import { randomUUID } from "node:crypto";
import { chmod, mkdir, readFile, readdir, rename, rm, unlink, writeFile } from "node:fs/promises";
import { join, resolve } from "node:path";
import { isoNow, type Platform, type TeamChannelBinding, type TeamWorkshopSession } from "./contracts.js";
import { WorkshopError } from "./session.js";

export interface WorkshopRecord {
  session: TeamWorkshopSession;
  binding: TeamChannelBinding;
}

export interface EventClaimResult {
  claimed: boolean;
  record: WorkshopRecord;
}

export interface WorkshopStore {
  create(record: WorkshopRecord): Promise<void>;
  get(sessionId: string): Promise<WorkshopRecord | null>;
  save(
    record: WorkshopRecord,
    expectedVersion: number,
    expectedBindingVersion: number,
    eventClaimDigest?: string,
  ): Promise<void>;
  saveBinding(binding: TeamChannelBinding, expectedBindingVersion: number): Promise<WorkshopRecord>;
  claimEvent(
    sessionId: string,
    eventDigest: string,
    expectedBindingVersion: number,
    now?: string,
  ): Promise<EventClaimResult>;
  findByConversation(
    platform: Platform,
    workspaceRef: string,
    channelRef: string,
    conversationRef: string,
  ): Promise<WorkshopRecord | null>;
  listExpired(before?: string): Promise<string[]>;
  delete(sessionId: string): Promise<boolean>;
}

function clone<T>(value: T): T {
  return structuredClone(value);
}

function normalizeBinding(binding: TeamChannelBinding): TeamChannelBinding {
  const legacy = binding as TeamChannelBinding & {
    binding_version?: unknown;
    outbound_deliveries?: TeamChannelBinding["outbound_deliveries"];
  };
  const bindingVersion =
    Number.isInteger(legacy.binding_version) && Number(legacy.binding_version) >= 1
      ? Number(legacy.binding_version)
      : 1;
  return {
    ...clone(binding),
    binding_version: bindingVersion,
    processed_event_digests: [...new Set(binding.processed_event_digests)],
    outbound_deliveries: structuredClone(legacy.outbound_deliveries ?? []),
  };
}

function normalizeRecord(record: WorkshopRecord): WorkshopRecord {
  return { session: clone(record.session), binding: normalizeBinding(record.binding) };
}

function assertRecordMatch(record: WorkshopRecord): void {
  if (record.session.id !== record.binding.session_id) {
    throw new WorkshopError("Workshop session and binding do not match.", "SESSION_MISMATCH");
  }
}

function assertDigest(value: string): void {
  if (!/^[a-f0-9]{64}$/.test(value)) {
    throw new WorkshopError("Event claim must be a SHA-256 digest.", "INVALID_EVENT_CLAIM");
  }
}

function assertReplacement(
  existing: WorkshopRecord,
  incoming: WorkshopRecord,
  expectedVersion: number,
  expectedBindingVersion: number,
  eventClaimDigest?: string,
): void {
  assertRecordMatch(incoming);
  if (eventClaimDigest) {
    assertDigest(eventClaimDigest);
    if (existing.binding.processed_event_digests.includes(eventClaimDigest)) {
      throw new WorkshopError("This interaction was already processed.", "DUPLICATE_EVENT");
    }
    if (!incoming.binding.processed_event_digests.includes(eventClaimDigest)) {
      throw new WorkshopError("Saved state does not contain its event claim.", "INVALID_EVENT_CLAIM");
    }
  }
  if (existing.session.step_version !== expectedVersion) {
    throw new WorkshopError("Workshop changed before this action completed.", "VERSION_CONFLICT");
  }
  if (existing.binding.binding_version !== expectedBindingVersion) {
    throw new WorkshopError("Private workshop binding changed before this action completed.", "VERSION_CONFLICT");
  }
  if (
    incoming.binding.binding_version !== expectedBindingVersion &&
    incoming.binding.binding_version !== expectedBindingVersion + 1
  ) {
    throw new WorkshopError("Private workshop binding version did not advance correctly.", "INVALID_BINDING_VERSION");
  }
  if (
    incoming.binding.binding_version === expectedBindingVersion &&
    JSON.stringify(incoming.binding) !== JSON.stringify(existing.binding)
  ) {
    throw new WorkshopError("Private workshop binding changed without a version advance.", "INVALID_BINDING_VERSION");
  }
}

function claimedBinding(
  binding: TeamChannelBinding,
  eventDigest: string,
  now?: string,
): TeamChannelBinding {
  const next = clone(binding);
  next.processed_event_digests.push(eventDigest);
  next.binding_version += 1;
  next.updated_at = isoNow(now);
  return next;
}

export class MemoryWorkshopStore implements WorkshopStore {
  private readonly records = new Map<string, WorkshopRecord>();

  async create(record: WorkshopRecord): Promise<void> {
    if (this.records.has(record.session.id)) {
      throw new WorkshopError("Workshop session already exists.", "SESSION_EXISTS");
    }
    const normalized = normalizeRecord(record);
    assertRecordMatch(normalized);
    this.records.set(record.session.id, normalized);
  }

  async get(sessionId: string): Promise<WorkshopRecord | null> {
    const record = this.records.get(sessionId);
    return record ? clone(record) : null;
  }

  async save(
    record: WorkshopRecord,
    expectedVersion: number,
    expectedBindingVersion: number,
    eventClaimDigest?: string,
  ): Promise<void> {
    const existing = this.records.get(record.session.id);
    if (!existing) throw new WorkshopError("Workshop session was not found.", "SESSION_NOT_FOUND");
    const normalized = normalizeRecord(record);
    assertReplacement(existing, normalized, expectedVersion, expectedBindingVersion, eventClaimDigest);
    this.records.set(record.session.id, normalized);
  }

  async saveBinding(binding: TeamChannelBinding, expectedBindingVersion: number): Promise<WorkshopRecord> {
    const existing = this.records.get(binding.session_id);
    if (!existing) throw new WorkshopError("Workshop session was not found.", "SESSION_NOT_FOUND");
    const normalized = normalizeBinding(binding);
    assertReplacement(
      existing,
      { session: existing.session, binding: normalized },
      existing.session.step_version,
      expectedBindingVersion,
    );
    const record = { session: existing.session, binding: normalized };
    this.records.set(binding.session_id, clone(record));
    return clone(record);
  }

  async claimEvent(
    sessionId: string,
    eventDigest: string,
    expectedBindingVersion: number,
    now?: string,
  ): Promise<EventClaimResult> {
    assertDigest(eventDigest);
    const existing = this.records.get(sessionId);
    if (!existing) throw new WorkshopError("Workshop session was not found.", "SESSION_NOT_FOUND");
    if (existing.binding.processed_event_digests.includes(eventDigest)) {
      return { claimed: false, record: clone(existing) };
    }
    if (existing.binding.binding_version !== expectedBindingVersion) {
      throw new WorkshopError("Private workshop binding changed before this action completed.", "VERSION_CONFLICT");
    }
    const record = {
      session: existing.session,
      binding: claimedBinding(existing.binding, eventDigest, now),
    };
    this.records.set(sessionId, clone(record));
    return { claimed: true, record: clone(record) };
  }

  async findByConversation(
    platform: Platform,
    workspaceRef: string,
    channelRef: string,
    conversationRef: string,
  ): Promise<WorkshopRecord | null> {
    for (const record of this.records.values()) {
      const binding = record.binding;
      if (
        binding.platform === platform &&
        binding.workspace_ref === workspaceRef &&
        binding.channel_ref === channelRef &&
        binding.conversation_ref === conversationRef
      ) {
        return clone(record);
      }
    }
    return null;
  }

  async delete(sessionId: string): Promise<boolean> {
    return this.records.delete(sessionId);
  }

  async listExpired(before?: string): Promise<string[]> {
    const cutoff = isoNow(before);
    return [...this.records.values()]
      .filter((record) => record.session.retention_expires_at <= cutoff)
      .map((record) => record.session.id)
      .sort();
  }
}

interface CommitPointer {
  schema_version: "1.0.0";
  session_id: string;
  generation: string;
}

const SESSION_ID = /^TW-[A-F0-9-]{36}$/;
const GENERATION = /^\d{13}-[a-f0-9-]{36}$/;

/**
 * Crash-safe, single-process store. Portable session and private adapter
 * binding are physically separate. A tiny atomic commit pointer selects a
 * complete generation, so a crash cannot expose only one half of a write.
 * Production multi-instance deployments should provide a transactional store.
 */
export class FileWorkshopStore implements WorkshopStore {
  private readonly root: string;
  private readonly locks = new Map<string, Promise<void>>();

  constructor(root: string) {
    this.root = resolve(root);
  }

  private assertSessionId(sessionId: string): void {
    if (!SESSION_ID.test(sessionId)) {
      throw new WorkshopError("Invalid workshop session ID.", "INVALID_SESSION_ID");
    }
  }

  private legacyPath(sessionId: string): string {
    this.assertSessionId(sessionId);
    return join(this.root, `${sessionId}.json`);
  }

  private commitPath(sessionId: string): string {
    this.assertSessionId(sessionId);
    return join(this.root, "commits", `${sessionId}.json`);
  }

  private generationPath(kind: "portable" | "private", sessionId: string, generation: string): string {
    this.assertSessionId(sessionId);
    if (!GENERATION.test(generation)) {
      throw new WorkshopError("Invalid workshop store generation.", "INVALID_STORE_GENERATION");
    }
    return join(this.root, kind, sessionId, `${generation}.json`);
  }

  private async locked<T>(sessionId: string, operation: () => Promise<T>): Promise<T> {
    const prior = this.locks.get(sessionId) ?? Promise.resolve();
    let release: () => void = () => undefined;
    const current = new Promise<void>((resolveLock) => {
      release = resolveLock;
    });
    const tail = prior.then(() => current);
    this.locks.set(sessionId, tail);
    await prior;
    try {
      return await operation();
    } finally {
      release();
      if (this.locks.get(sessionId) === tail) this.locks.delete(sessionId);
    }
  }

  private async readJson<T>(path: string): Promise<T | null> {
    try {
      return JSON.parse(await readFile(path, "utf8")) as T;
    } catch (error) {
      if ((error as NodeJS.ErrnoException).code === "ENOENT") return null;
      throw error;
    }
  }

  private async writeJson(path: string, value: unknown): Promise<void> {
    const directory = resolve(path, "..");
    await mkdir(directory, { recursive: true, mode: 0o700 });
    const temporary = `${path}.${process.pid}.${randomUUID()}.tmp`;
    await writeFile(temporary, `${JSON.stringify(value, null, 2)}\n`, {
      encoding: "utf8",
      mode: 0o600,
      flag: "wx",
    });
    await rename(temporary, path);
    await chmod(path, 0o600);
  }

  private async readGeneration(sessionId: string, generation: string): Promise<WorkshopRecord | null> {
    const session = await this.readJson<TeamWorkshopSession>(
      this.generationPath("portable", sessionId, generation),
    );
    const binding = await this.readJson<TeamChannelBinding>(
      this.generationPath("private", sessionId, generation),
    );
    if (!session || !binding) return null;
    const record = normalizeRecord({ session, binding });
    assertRecordMatch(record);
    if (record.session.id !== sessionId) {
      throw new WorkshopError("Committed workshop ID does not match its path.", "SESSION_MISMATCH");
    }
    return record;
  }

  private async generationNames(kind: "portable" | "private", sessionId: string): Promise<string[]> {
    try {
      return (await readdir(join(this.root, kind, sessionId)))
        .filter((name) => GENERATION.test(name.slice(0, -5)) && name.endsWith(".json"))
        .map((name) => name.slice(0, -5));
    } catch (error) {
      if ((error as NodeJS.ErrnoException).code === "ENOENT") return [];
      throw error;
    }
  }

  private async recoverGeneration(sessionId: string): Promise<WorkshopRecord | null> {
    const portable = new Set(await this.generationNames("portable", sessionId));
    const common = (await this.generationNames("private", sessionId))
      .filter((generation) => portable.has(generation))
      .sort()
      .reverse();
    for (const generation of common) {
      try {
        const record = await this.readGeneration(sessionId, generation);
        if (!record) continue;
        await this.writeJson(this.commitPath(sessionId), {
          schema_version: "1.0.0",
          session_id: sessionId,
          generation,
        } satisfies CommitPointer);
        return record;
      } catch (error) {
        if (error instanceof SyntaxError) continue;
        throw error;
      }
    }
    return null;
  }

  private async readCommitted(sessionId: string): Promise<WorkshopRecord | null> {
    const pointer = await this.readJson<CommitPointer>(this.commitPath(sessionId));
    if (pointer) {
      if (
        pointer.schema_version !== "1.0.0" ||
        pointer.session_id !== sessionId ||
        !GENERATION.test(pointer.generation)
      ) {
        throw new WorkshopError("Workshop commit pointer is invalid.", "INVALID_STORE_COMMIT");
      }
      const record = await this.readGeneration(sessionId, pointer.generation);
      if (record) return record;
    }
    return this.recoverGeneration(sessionId);
  }

  private async readLegacy(sessionId: string): Promise<WorkshopRecord | null> {
    const record = await this.readJson<WorkshopRecord>(this.legacyPath(sessionId));
    if (!record) return null;
    const normalized = normalizeRecord(record);
    assertRecordMatch(normalized);
    return normalized;
  }

  private async readAndMigrate(sessionId: string): Promise<WorkshopRecord | null> {
    const committed = await this.readCommitted(sessionId);
    if (committed) return committed;
    const legacy = await this.readLegacy(sessionId);
    if (!legacy) return null;
    await this.write(legacy);
    await unlink(this.legacyPath(sessionId)).catch((error: NodeJS.ErrnoException) => {
      if (error.code !== "ENOENT") throw error;
    });
    return legacy;
  }

  private async cleanupGenerations(sessionId: string, current: string): Promise<void> {
    for (const kind of ["portable", "private"] as const) {
      for (const generation of await this.generationNames(kind, sessionId)) {
        if (generation !== current) {
          await unlink(this.generationPath(kind, sessionId, generation)).catch(() => undefined);
        }
      }
    }
  }

  private async write(record: WorkshopRecord): Promise<void> {
    const normalized = normalizeRecord(record);
    assertRecordMatch(normalized);
    const generation = `${String(Date.now()).padStart(13, "0")}-${randomUUID()}`;
    await this.writeJson(
      this.generationPath("portable", normalized.session.id, generation),
      normalized.session,
    );
    await this.writeJson(
      this.generationPath("private", normalized.session.id, generation),
      normalized.binding,
    );
    await this.writeJson(this.commitPath(normalized.session.id), {
      schema_version: "1.0.0",
      session_id: normalized.session.id,
      generation,
    } satisfies CommitPointer);
    await this.cleanupGenerations(normalized.session.id, generation);
  }

  async create(record: WorkshopRecord): Promise<void> {
    await this.locked(record.session.id, async () => {
      if (await this.readAndMigrate(record.session.id)) {
        throw new WorkshopError("Workshop session already exists.", "SESSION_EXISTS");
      }
      await this.write(record);
    });
  }

  async get(sessionId: string): Promise<WorkshopRecord | null> {
    return this.locked(sessionId, () => this.readAndMigrate(sessionId));
  }

  async save(
    record: WorkshopRecord,
    expectedVersion: number,
    expectedBindingVersion: number,
    eventClaimDigest?: string,
  ): Promise<void> {
    await this.locked(record.session.id, async () => {
      const existing = await this.readAndMigrate(record.session.id);
      if (!existing) throw new WorkshopError("Workshop session was not found.", "SESSION_NOT_FOUND");
      const normalized = normalizeRecord(record);
      assertReplacement(existing, normalized, expectedVersion, expectedBindingVersion, eventClaimDigest);
      await this.write(normalized);
    });
  }

  async saveBinding(binding: TeamChannelBinding, expectedBindingVersion: number): Promise<WorkshopRecord> {
    return this.locked(binding.session_id, async () => {
      const existing = await this.readAndMigrate(binding.session_id);
      if (!existing) throw new WorkshopError("Workshop session was not found.", "SESSION_NOT_FOUND");
      const normalized = normalizeBinding(binding);
      const record = { session: existing.session, binding: normalized };
      assertReplacement(
        existing,
        record,
        existing.session.step_version,
        expectedBindingVersion,
      );
      await this.write(record);
      return clone(record);
    });
  }

  async claimEvent(
    sessionId: string,
    eventDigest: string,
    expectedBindingVersion: number,
    now?: string,
  ): Promise<EventClaimResult> {
    assertDigest(eventDigest);
    return this.locked(sessionId, async () => {
      const existing = await this.readAndMigrate(sessionId);
      if (!existing) throw new WorkshopError("Workshop session was not found.", "SESSION_NOT_FOUND");
      if (existing.binding.processed_event_digests.includes(eventDigest)) {
        return { claimed: false, record: clone(existing) };
      }
      if (existing.binding.binding_version !== expectedBindingVersion) {
        throw new WorkshopError("Private workshop binding changed before this action completed.", "VERSION_CONFLICT");
      }
      const record = {
        session: existing.session,
        binding: claimedBinding(existing.binding, eventDigest, now),
      };
      await this.write(record);
      return { claimed: true, record: clone(record) };
    });
  }

  private async sessionIds(): Promise<string[]> {
    const ids = new Set<string>();
    for (const directory of [join(this.root, "commits"), join(this.root, "portable")]) {
      try {
        for (const name of await readdir(directory)) {
          const candidate = name.endsWith(".json") ? name.slice(0, -5) : name;
          if (SESSION_ID.test(candidate)) ids.add(candidate);
        }
      } catch (error) {
        if ((error as NodeJS.ErrnoException).code !== "ENOENT") throw error;
      }
    }
    try {
      for (const name of await readdir(this.root)) {
        if (/^TW-[A-F0-9-]{36}\.json$/.test(name)) ids.add(name.slice(0, -5));
      }
    } catch (error) {
      if ((error as NodeJS.ErrnoException).code !== "ENOENT") throw error;
    }
    return [...ids].sort();
  }

  async findByConversation(
    platform: Platform,
    workspaceRef: string,
    channelRef: string,
    conversationRef: string,
  ): Promise<WorkshopRecord | null> {
    for (const sessionId of await this.sessionIds()) {
      const record = await this.get(sessionId);
      const binding = record?.binding;
      if (
        record &&
        binding?.platform === platform &&
        binding.workspace_ref === workspaceRef &&
        binding.channel_ref === channelRef &&
        binding.conversation_ref === conversationRef
      ) {
        return record;
      }
    }
    return null;
  }

  async delete(sessionId: string): Promise<boolean> {
    return this.locked(sessionId, async () => {
      const existed = Boolean(
        (await this.readCommitted(sessionId)) ?? (await this.readLegacy(sessionId)),
      );
      await Promise.all([
        rm(join(this.root, "portable", sessionId), { recursive: true, force: true }),
        rm(join(this.root, "private", sessionId), { recursive: true, force: true }),
        unlink(this.commitPath(sessionId)).catch(() => undefined),
        unlink(this.legacyPath(sessionId)).catch(() => undefined),
      ]);
      return existed;
    });
  }

  async listExpired(before?: string): Promise<string[]> {
    const cutoff = isoNow(before);
    const expired: string[] = [];
    for (const sessionId of await this.sessionIds()) {
      const record = await this.get(sessionId);
      if (record && record.session.retention_expires_at <= cutoff) expired.push(sessionId);
    }
    return expired;
  }
}
