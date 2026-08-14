import assert from "node:assert/strict";
import { access, mkdtemp, readFile, stat, unlink, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";
import {
  MockFacilitatorProvider,
  SYNTHESIS_SCHEMA,
  type FacilitatorProvider,
} from "../src/core/facilitator.js";
import {
  addContribution,
  bindConversation,
  createWorkshop,
  delegateFacilitator,
  freezeWorkshop,
  passWorkshop,
  pauseWorkshop,
  resumeWorkshop,
  WorkshopError,
  workshopPresentation,
} from "../src/core/session.js";
import { digestExternal } from "../src/core/contracts.js";
import { WorkshopService } from "../src/core/service.js";
import { FileWorkshopStore, MemoryWorkshopStore } from "../src/core/store.js";
import { buildWorkshopTextFallback, buildWorkshopTextSummary, loadWorkshopVisual } from "../src/core/visual.js";

const NOW = "2026-08-14T12:00:00.000Z";

function start(overrides: Record<string, unknown> = {}) {
  return createWorkshop({
    platform: "SLACK",
    workspace_ref: "T-WORKSPACE",
    channel_ref: "C-CHANNEL",
    actor_ref: "U-INITIATOR",
    challenge: "How might a distributed team make handoffs less fragile?",
    exercise: "BRAINSTORMING",
    event_id: "EV-START",
    now: NOW,
    ...overrides,
  });
}

test("one member can start a novice-assisted protected brainstorm", () => {
  const { session, binding } = start();
  assert.match(session.id, /^TW-[A-F0-9-]{36}$/);
  assert.equal(session.visibility, "SEALED");
  assert.equal(session.facilitator_level, "NOVICE_ASSISTED");
  assert.equal(session.participants.length, 1);
  assert.equal(session.participants[0]?.role, "INITIATOR");
  assert.equal(session.prompts.length, 1);
  assert.match(session.prompts[0]?.prompt ?? "", /one idea/i);
  const presentation = workshopPresentation(session);
  assert.match(presentation.headline, /MightShape/);
  assert.doesNotMatch(presentation.headline, /Hunchgarden|Design Council/);
  assert.equal(Object.keys(binding.participant_refs).length, 1);
  assert.doesNotMatch(JSON.stringify(session), /U-INITIATOR|T-WORKSPACE|C-CHANNEL/);
});

test("real teammates are pseudonymous and their input remains USER_PROVIDED", () => {
  const created = start();
  const first = addContribution(created.session, created.binding, {
    session_id: created.session.id,
    actor_ref: "U-TEAMMATE-A",
    content: "Make the receiver explicitly accept the handoff.",
    event_id: "EV-A",
    now: "2026-08-14T12:01:00Z",
  });
  const second = addContribution(first.session, first.binding, {
    session_id: created.session.id,
    actor_ref: "U-TEAMMATE-B",
    content: "Remove the handoff and keep one accountable owner.",
    event_id: "EV-B",
    now: "2026-08-14T12:02:00Z",
  });
  assert.deepEqual(
    second.session.contributions.map((item) => item.provenance),
    ["USER_PROVIDED", "USER_PROVIDED"],
  );
  assert.deepEqual(
    second.session.contributions.map((item) => item.participant_id),
    ["TP-002", "TP-003"],
  );
  assert.ok(second.session.contributions.every((item) => item.revealed_at === null));
  assert.doesNotMatch(JSON.stringify(second.session), /U-TEAMMATE/);
  assert.ok(second.session.contributions.every((item) => !("source_event_digest" in item)));
});

test("participants can pass, and controllers can pause, resume, and delegate without ambient capture", () => {
  const created = start();
  const passed = passWorkshop(created.session, created.binding, {
    session_id: created.session.id,
    actor_ref: "U-FACILITATOR",
    event_id: "EV-PASS",
    now: "2026-08-14T12:00:30Z",
  });
  assert.equal(passed.session.participants[1]?.status, "PASSED");
  assert.equal(passed.session.contributions.length, 0);
  const delegated = delegateFacilitator(passed.session, passed.binding, {
    session_id: created.session.id,
    actor_ref: "U-INITIATOR",
    target_actor_ref: "U-FACILITATOR",
    event_id: "EV-DELEGATE",
    now: "2026-08-14T12:00:40Z",
  });
  assert.equal(delegated.session.participants[1]?.role, "FACILITATOR");
  assert.equal(delegated.session.participants[1]?.status, "ACTIVE");
  const paused = pauseWorkshop(delegated.session, delegated.binding, {
    session_id: created.session.id,
    actor_ref: "U-FACILITATOR",
    event_id: "EV-PAUSE",
    now: "2026-08-14T12:00:50Z",
  });
  assert.equal(paused.session.status, "PAUSED");
  assert.throws(
    () =>
      addContribution(paused.session, paused.binding, {
        session_id: created.session.id,
        actor_ref: "U-OTHER",
        content: "This must wait until resume.",
        event_id: "EV-WHILE-PAUSED",
      }),
    (error: unknown) => error instanceof WorkshopError && error.code === "NOT_COLLECTING",
  );
  const resumed = resumeWorkshop(paused.session, paused.binding, {
    session_id: created.session.id,
    actor_ref: "U-FACILITATOR",
    event_id: "EV-RESUME",
    now: "2026-08-14T12:01:00Z",
  });
  assert.equal(resumed.session.status, "COLLECTING");
});

test("sealed contributions reveal together only after an authorized freeze", () => {
  const created = start();
  const contributed = addContribution(created.session, created.binding, {
    session_id: created.session.id,
    actor_ref: "U-TEAMMATE",
    content: "Show the handoff as a temporary shared object.",
    event_id: "EV-C",
    now: "2026-08-14T12:03:00Z",
  });
  assert.throws(
    () =>
      freezeWorkshop(contributed.session, contributed.binding, {
        session_id: created.session.id,
        actor_ref: "U-TEAMMATE",
        event_id: "EV-FREEZE-BAD",
        now: "2026-08-14T12:04:00Z",
      }),
    (error: unknown) => error instanceof WorkshopError && error.code === "CONTROL_FORBIDDEN",
  );
  const frozen = freezeWorkshop(contributed.session, contributed.binding, {
    session_id: created.session.id,
    actor_ref: "U-INITIATOR",
    event_id: "EV-FREEZE",
    now: "2026-08-14T12:05:00Z",
  });
  assert.equal(frozen.session.status, "FROZEN");
  assert.equal(frozen.session.contribution_set_frozen_at, "2026-08-14T12:05:00.000Z");
  assert.ok(frozen.session.contributions.every((item) => item.revealed_at === frozen.session.contribution_set_frozen_at));
});

test("open co-creation reveals only explicitly submitted material", () => {
  const created = start({ exercise: "PROCESS_RECONSTRUCTION", visibility: "OPEN" });
  const contributed = addContribution(created.session, created.binding, {
    session_id: created.session.id,
    actor_ref: "U-TEAMMATE",
    content: "The requester sends a direct message after the ticket stalls.",
    event_id: "EV-STEP",
    now: "2026-08-14T12:06:00Z",
  });
  assert.equal(contributed.contribution.kind, "PROCESS_STEP");
  assert.equal(contributed.contribution.revealed_at, "2026-08-14T12:06:00.000Z");
  assert.match(workshopPresentation(contributed.session).body, /visible to people in this channel/i);
});

test("replayed platform interaction IDs cannot duplicate contributions", () => {
  const created = start();
  const first = addContribution(created.session, created.binding, {
    session_id: created.session.id,
    actor_ref: "U-A",
    content: "One idea",
    event_id: "EV-REPLAY",
    now: "2026-08-14T12:07:00Z",
  });
  assert.throws(
    () =>
      addContribution(first.session, first.binding, {
        session_id: created.session.id,
        actor_ref: "U-A",
        content: "Duplicated idea",
        event_id: "EV-REPLAY",
        now: "2026-08-14T12:08:00Z",
      }),
    (error: unknown) => error instanceof WorkshopError && error.code === "DUPLICATE_EVENT",
  );
  assert.equal(first.session.contributions.length, 1);
});

test("optimistic persistence permits exactly one simultaneous phase transition", async () => {
  const store = new MemoryWorkshopStore();
  const created = start();
  await store.create(created);
  const snapshotA = await store.get(created.session.id);
  const snapshotB = await store.get(created.session.id);
  assert.ok(snapshotA && snapshotB);
  const a = addContribution(snapshotA.session, snapshotA.binding, {
    session_id: created.session.id,
    actor_ref: "U-A",
    content: "A",
    event_id: "EV-A1",
    now: "2026-08-14T12:09:00Z",
  });
  const b = addContribution(snapshotB.session, snapshotB.binding, {
    session_id: created.session.id,
    actor_ref: "U-B",
    content: "B",
    event_id: "EV-B1",
    now: "2026-08-14T12:09:01Z",
  });
  await store.save(
    { session: a.session, binding: a.binding },
    snapshotA.session.step_version,
    snapshotA.binding.binding_version,
  );
  await assert.rejects(
    store.save(
      { session: b.session, binding: b.binding },
      snapshotB.session.step_version,
      snapshotB.binding.binding_version,
    ),
    (error: unknown) => error instanceof WorkshopError && error.code === "VERSION_CONFLICT",
  );
});

test("file store physically separates owner-only portable and private generations", async () => {
  const root = await mkdtemp(join(tmpdir(), "dc-team-store-"));
  const store = new FileWorkshopStore(root);
  const service = new WorkshopService(store, new MockFacilitatorProvider(), root);
  const created = await service.start({
    platform: "DISCORD",
    workspace_ref: "GUILD-SECRET",
    channel_ref: "CHANNEL-SECRET",
    actor_ref: "USER-SECRET",
    challenge: "Explore reliable transitions",
    exercise: "ASSUMPTION_MAPPING",
    event_id: "INTERACTION-SECRET",
    now: NOW,
  });
  const commitPath = join(root, "commits", `${created.session.id}.json`);
  const pointer = JSON.parse(await readFile(commitPath, "utf8")) as { generation: string };
  const portablePath = join(root, "portable", created.session.id, `${pointer.generation}.json`);
  const privatePath = join(root, "private", created.session.id, `${pointer.generation}.json`);
  assert.equal((await stat(commitPath)).mode & 0o077, 0);
  assert.equal((await stat(portablePath)).mode & 0o077, 0);
  assert.equal((await stat(privatePath)).mode & 0o077, 0);
  const portableRaw = await readFile(portablePath, "utf8");
  const privateRaw = await readFile(privatePath, "utf8");
  assert.doesNotMatch(portableRaw, /GUILD-SECRET|CHANNEL-SECRET|USER-SECRET|INTERACTION-SECRET/);
  assert.match(privateRaw, /GUILD-SECRET/);
  await assert.rejects(access(join(root, `${created.session.id}.json`)));
  const portable = await service.exportPortable(created.session.id);
  assert.doesNotMatch(JSON.stringify(portable), /GUILD-SECRET|CHANNEL-SECRET|USER-SECRET|INTERACTION-SECRET/);
});

test("file store migrates a legacy combined record and normalizes its private version", async () => {
  const root = await mkdtemp(join(tmpdir(), "dc-team-legacy-store-"));
  const created = start();
  const { binding_version: _legacyBindingVersion, ...legacyBinding } = created.binding;
  const legacy = { session: created.session, binding: legacyBinding };
  const legacyPath = join(root, `${legacy.session.id}.json`);
  await writeFile(legacyPath, `${JSON.stringify(legacy)}\n`, { mode: 0o600 });

  const store = new FileWorkshopStore(root);
  const recovered = await store.get(legacy.session.id);
  assert.ok(recovered);
  assert.equal(recovered.binding.binding_version, 1);
  assert.equal(recovered.binding.workspace_ref, "T-WORKSPACE");
  await assert.rejects(access(legacyPath));
  assert.ok(JSON.parse(await readFile(join(root, "commits", `${legacy.session.id}.json`), "utf8")));
});

test("file store recovers a complete split generation when the commit pointer is lost", async () => {
  const root = await mkdtemp(join(tmpdir(), "dc-team-generation-recovery-"));
  const created = start();
  const store = new FileWorkshopStore(root);
  await store.create(created);
  const commitPath = join(root, "commits", `${created.session.id}.json`);
  await unlink(commitPath);

  const restarted = new FileWorkshopStore(root);
  const recovered = await restarted.get(created.session.id);
  assert.equal(recovered?.session.id, created.session.id);
  assert.equal(recovered?.binding.workspace_ref, "T-WORKSPACE");
  assert.ok(JSON.parse(await readFile(commitPath, "utf8")));
});

test("private binding optimistic version prevents two root bindings from overwriting each other", async () => {
  const store = new MemoryWorkshopStore();
  const created = start();
  await store.create(created);
  const snapshotA = await store.get(created.session.id);
  const snapshotB = await store.get(created.session.id);
  assert.ok(snapshotA && snapshotB);
  const bindingA = bindConversation(snapshotA.binding, "THREAD-A", "ROOT-A");
  const bindingB = bindConversation(snapshotB.binding, "THREAD-B", "ROOT-B");
  await store.saveBinding(bindingA, snapshotA.binding.binding_version);
  await assert.rejects(
    store.saveBinding(bindingB, snapshotB.binding.binding_version),
    (error: unknown) => error instanceof WorkshopError && error.code === "VERSION_CONFLICT",
  );
  assert.equal((await store.get(created.session.id))?.binding.root_message_ref, "ROOT-A");
});

test("durable event claims never expire and concurrent replay claims exactly once", async () => {
  const store = new MemoryWorkshopStore();
  const created = start();
  await store.create(created);
  let current = await store.get(created.session.id);
  assert.ok(current);
  const firstDigest = digestExternal("EVENT-0001");
  for (let index = 1; index <= 2_101; index += 1) {
    const claimed = await store.claimEvent(
      created.session.id,
      digestExternal(`EVENT-${String(index).padStart(4, "0")}`),
      current.binding.binding_version,
    );
    assert.equal(claimed.claimed, true);
    current = claimed.record;
  }
  assert.equal(current.binding.processed_event_digests.length, 2_102);
  const replay = await store.claimEvent(
    created.session.id,
    firstDigest,
    current.binding.binding_version,
  );
  assert.equal(replay.claimed, false);
  assert.equal(replay.record.binding.processed_event_digests.length, 2_102);

  const sharedVersion = replay.record.binding.binding_version;
  const simultaneousDigest = digestExternal("SIMULTANEOUS-DELIVERY");
  const results = await Promise.all([
    store.claimEvent(created.session.id, simultaneousDigest, sharedVersion),
    store.claimEvent(created.session.id, simultaneousDigest, sharedVersion),
  ]);
  assert.deepEqual(results.map((result) => result.claimed).sort(), [false, true]);
});

test("event claims survive a file-store restart", async () => {
  const root = await mkdtemp(join(tmpdir(), "dc-team-claim-restart-"));
  const created = start();
  const firstStore = new FileWorkshopStore(root);
  await firstStore.create(created);
  const digest = digestExternal("DELIVERY-CLAIM-1");
  const claimed = await firstStore.claimEvent(
    created.session.id,
    digest,
    created.binding.binding_version,
  );
  assert.equal(claimed.claimed, true);

  const restarted = new FileWorkshopStore(root);
  const replay = await restarted.claimEvent(
    created.session.id,
    digest,
    claimed.record.binding.binding_version,
  );
  assert.equal(replay.claimed, false);
  assert.ok(replay.record.binding.processed_event_digests.includes(digest));
});

test("concurrent redelivery is classified as DUPLICATE_EVENT rather than a generic conflict", async () => {
  const store = new MemoryWorkshopStore();
  const service = new WorkshopService(store, new MockFacilitatorProvider());
  const created = await service.start({
    platform: "SLACK",
    workspace_ref: "T-CONCURRENT",
    channel_ref: "C-CONCURRENT",
    actor_ref: "U-OWNER",
    challenge: "Process a redelivered contribution exactly once.",
    exercise: "BRAINWRITING",
    event_id: "START-CONCURRENT",
    now: NOW,
  });
  const input = {
    session_id: created.session.id,
    actor_ref: "U-MEMBER",
    content: "One contribution from one platform event.",
    event_id: "SAME-PLATFORM-EVENT",
  };
  const settled = await Promise.allSettled([service.contribute(input), service.contribute(input)]);
  assert.equal(settled.filter((result) => result.status === "fulfilled").length, 1);
  const rejected = settled.find((result) => result.status === "rejected");
  assert.ok(rejected?.status === "rejected");
  assert.ok(rejected.reason instanceof WorkshopError);
  assert.equal(rejected.reason.code, "DUPLICATE_EVENT");
  assert.equal((await service.get(created.session.id)).session.contributions.length, 1);
});

test("a redelivered start event is durably idempotent across service restarts", async () => {
  const root = await mkdtemp(join(tmpdir(), "dc-team-start-replay-"));
  const input = {
    platform: "SLACK" as const,
    workspace_ref: "T-REPLAY",
    channel_ref: "C-REPLAY",
    actor_ref: "U-STARTER",
    challenge: "Avoid duplicate workshop roots after a platform retry.",
    exercise: "BRAINWRITING" as const,
    event_id: "PLATFORM-START-EVENT-1",
    now: NOW,
  };
  const firstService = new WorkshopService(
    new FileWorkshopStore(join(root, "sessions")),
    new MockFacilitatorProvider(),
    root,
  );
  const first = await firstService.start(input);
  const restartedService = new WorkshopService(
    new FileWorkshopStore(join(root, "sessions")),
    new MockFacilitatorProvider(),
    root,
  );
  const replay = await restartedService.start(input);
  assert.equal(replay.session.id, first.session.id);
  assert.equal(replay.session.history.filter((event) => event.action === "WORKSHOP_STARTED").length, 1);
});

test("offline synthesis produces an honest inline PNG and accessible fallback", async () => {
  const root = await mkdtemp(join(tmpdir(), "dc-team-visual-"));
  const service = new WorkshopService(new MemoryWorkshopStore(), new MockFacilitatorProvider(), root);
  const created = await service.start({
    platform: "SLACK",
    workspace_ref: "T1",
    channel_ref: "C1",
    actor_ref: "U1",
    challenge: "How might teams preserve context across handoffs?",
    exercise: "BRAINWRITING",
    event_id: "E1",
    now: NOW,
  });
  await service.contribute({
    session_id: created.session.id,
    actor_ref: "U2",
    content: "Make the unresolved question travel with the work.",
    event_id: "E2",
    now: "2026-08-14T12:01:00Z",
  });
  await service.contribute({
    session_id: created.session.id,
    actor_ref: "U3",
    content: "Use a short receiver-authored summary.",
    event_id: "E3",
    now: "2026-08-14T12:02:00Z",
  });
  await service.freeze({
    session_id: created.session.id,
    actor_ref: "U1",
    event_id: "E4",
    now: "2026-08-14T12:03:00Z",
  });
  const result = await service.synthesize(created.session.id, "SLACK");
  assert.equal(result.record.session.status, "REVIEW");
  assert.equal(result.visual.png.subarray(0, 8).toString("hex"), "89504e470d0a1a0a");
  assert.ok(result.visual.png.byteLength < 5_000_000);
  assert.match(result.visual.alt_text, /USER_PROVIDED/);
  assert.match(result.visual.text_summary, /does not claim semantic clustering/i);
  assert.equal(result.visual.artifact_ref.source_contribution_ids.length, 2);
  await service.delete(created.session.id, "U1");
  await assert.rejects(access(result.visual.png_path));
});

test("a near-limit contribution survives portable state, synthesis, rendering, and full text fallback", async () => {
  const root = await mkdtemp(join(tmpdir(), "dc-team-long-contribution-"));
  const service = new WorkshopService(new MemoryWorkshopStore(), new MockFacilitatorProvider(), root);
  const created = await service.start({
    platform: "SLACK",
    workspace_ref: "T-LONG",
    channel_ref: "C-LONG",
    actor_ref: "U-OWNER",
    challenge: "Preserve source wording without overflowing delivery payloads.",
    exercise: "BRAINWRITING",
    event_id: "LONG-START",
    now: NOW,
  });
  const content = "A participant supplied this long source record. ".padEnd(1_950, "x");
  await service.contribute({
    session_id: created.session.id,
    actor_ref: "U-CONTRIBUTOR",
    content,
    event_id: "LONG-NOTE",
  });
  assert.equal((await service.get(created.session.id)).session.contributions[0]?.content, content);
  await service.freeze({
    session_id: created.session.id,
    actor_ref: "U-OWNER",
    event_id: "LONG-FREEZE",
  });
  const result = await service.synthesize(created.session.id, "SLACK");
  assert.equal(result.record.session.contributions[0]?.content, content);
  assert.ok(JSON.stringify(result.visual.artifact.data).includes(content));
  assert.ok(result.visual.text_fallback.includes(`UC-001 · USER_PROVIDED\n${content}`));
  assert.ok(result.visual.text_summary.length <= 5_000);
  const recovered = await loadWorkshopVisual(result.record.session, root);
  assert.deepEqual(recovered.png, result.visual.png);
  assert.equal(recovered.text_fallback, result.visual.text_fallback);
  assert.equal(recovered.artifact_ref.artifact_id, result.visual.artifact_ref.artifact_id);
  await service.delete(created.session.id, "U-OWNER");
});

test("bounded visual summary identifies every source while the complete fallback retains all wording", async () => {
  let record = start({ exercise: "PROCESS_RECONSTRUCTION", visibility: "OPEN" });
  const expected = new Map<string, string>();
  for (let index = 1; index <= 100; index += 1) {
    const content = `Source contribution ${String(index).padStart(3, "0")} · ${"detail ".repeat(20)}`.trim();
    record = addContribution(record.session, record.binding, {
      session_id: record.session.id,
      actor_ref: `U-${index}`,
      content,
      event_id: `EV-SOURCE-${index}`,
      now: `2026-08-14T12:${String(Math.floor(index / 60)).padStart(2, "0")}:${String(index % 60).padStart(2, "0")}Z`,
    });
    expected.set(`UC-${String(index).padStart(3, "0")}`, content);
  }
  const synthesis = await new MockFacilitatorProvider().synthesize(record.session);
  synthesis.artifact.title = "T".repeat(200);
  synthesis.artifact.limitations = Array.from({ length: 20 }, (_, index) =>
    `Limitation ${index + 1} ${"detail ".repeat(140)}`.trim(),
  );
  synthesis.synthesis = "S".repeat(2_000);
  synthesis.tensions = Array.from({ length: 8 }, () => "T".repeat(500));
  synthesis.outlier_worth_saving = "O".repeat(1_000);
  synthesis.next_move = "N".repeat(1_000);
  const summary = buildWorkshopTextSummary(record.session, synthesis);
  const fallback = buildWorkshopTextFallback(record.session, synthesis);
  assert.ok(summary.length <= 5_000);
  for (const [id, content] of expected) {
    assert.match(summary, new RegExp(`\\b${id}\\b`));
    assert.ok(fallback.includes(`${id} · USER_PROVIDED\n${content}`));
  }
  assert.equal(record.session.contributions.length, 100);
  assert.throws(
    () =>
      addContribution(record.session, record.binding, {
        session_id: record.session.id,
        actor_ref: "U-101",
        content: "This must start a new bounded round.",
        event_id: "EV-SOURCE-101",
      }),
    (error: unknown) => error instanceof WorkshopError && error.code === "CONTRIBUTION_LIMIT",
  );
});

test("retention cleanup removes expired portable and private state", async () => {
  const store = new MemoryWorkshopStore();
  const service = new WorkshopService(store, new MockFacilitatorProvider());
  const expired = await service.start({
    platform: "DISCORD",
    workspace_ref: "G1",
    channel_ref: "C1",
    actor_ref: "U1",
    challenge: "Retire old workshop state.",
    exercise: "POV_HMW",
    event_id: "START-OLD",
    now: "2026-08-01T00:00:00Z",
    retention_days: 1,
  });
  const active = await service.start({
    platform: "DISCORD",
    workspace_ref: "G1",
    channel_ref: "C2",
    actor_ref: "U2",
    challenge: "Keep current workshop state.",
    exercise: "POV_HMW",
    event_id: "START-NEW",
    now: "2026-08-14T00:00:00Z",
    retention_days: 30,
  });
  assert.deepEqual(await service.purgeExpired("2026-08-14T12:00:00Z"), [expired.session.id]);
  await assert.rejects(service.get(expired.session.id), /not found/i);
  assert.equal((await service.get(active.session.id)).session.id, active.session.id);
});

test("failed facilitation restores the immutable frozen set for a safe retry", async () => {
  const store = new MemoryWorkshopStore();
  const root = await mkdtemp(join(tmpdir(), "dc-team-retry-"));
  const failing: FacilitatorProvider = {
    async synthesize() {
      throw new Error("provider unavailable");
    },
  };
  const service = new WorkshopService(store, failing, root);
  const created = await service.start({
    platform: "TEAMS",
    workspace_ref: "TENANT",
    channel_ref: "CHANNEL",
    actor_ref: "OWNER",
    challenge: "Make incident handoffs learnable.",
    exercise: "ASSUMPTION_MAPPING",
    event_id: "START",
    now: NOW,
  });
  await service.contribute({
    session_id: created.session.id,
    actor_ref: "MEMBER",
    content: "The receiver knows which uncertainty matters.",
    event_id: "NOTE",
  });
  await service.freeze({ session_id: created.session.id, actor_ref: "OWNER", event_id: "FREEZE" });
  await assert.rejects(
    service.synthesize(created.session.id, "TEAMS"),
    (error: unknown) => error instanceof WorkshopError && error.code === "FACILITATION_FAILED",
  );
  const restored = await service.get(created.session.id);
  assert.equal(restored.session.status, "FROZEN");
  assert.equal(restored.session.contributions.length, 1);
  assert.match(restored.session.history.at(-1)?.action ?? "", /SYNTHESIS_FAILED/);
  assert.deepEqual(restored.session.history.at(-1)?.details, {
    failure_code: "FACILITATION_FAILED",
    retryable: true,
  });
  const retryService = new WorkshopService(store, new MockFacilitatorProvider(), root);
  await assert.rejects(
    retryService.retrySynthesis(
      { session_id: created.session.id, actor_ref: "MEMBER", event_id: "RETRY-BAD" },
      "TEAMS",
    ),
    (error: unknown) => error instanceof WorkshopError && error.code === "CONTROL_FORBIDDEN",
  );
  const retried = await retryService.retrySynthesis(
    { session_id: created.session.id, actor_ref: "OWNER", event_id: "RETRY-GOOD" },
    "TEAMS",
  );
  assert.equal(retried.record.session.status, "REVIEW");
  assert.match(retried.visual.text_summary, /frozen and visible/i);
});

test("the OpenAI structured-output schema closes every object and requires every property", () => {
  const visit = (node: unknown, location = "root") => {
    if (!node || typeof node !== "object") return;
    const record = node as Record<string, unknown>;
    if (record.type === "object") {
      assert.equal(record.additionalProperties, false, `${location} must reject undeclared properties`);
      const properties = (record.properties ?? {}) as Record<string, unknown>;
      assert.deepEqual(
        [...((record.required ?? []) as string[])].sort(),
        Object.keys(properties).sort(),
        `${location} must require every declared property`,
      );
    }
    for (const [key, child] of Object.entries(record)) {
      if (Array.isArray(child)) child.forEach((item, index) => visit(item, `${location}.${key}[${index}]`));
      else visit(child, `${location}.${key}`);
    }
  };
  visit(SYNTHESIS_SCHEMA);
});
