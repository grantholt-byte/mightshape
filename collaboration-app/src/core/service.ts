import { rm } from "node:fs/promises";
import { resolve, sep } from "node:path";
import type {
  ContributionInput,
  ControlInput,
  DelegateInput,
  OutboundDeliveryKind,
  OutboundDeliveryReceipt,
  OutboundDeliveryStatus,
  Platform,
  StartWorkshopInput,
  TeamChannelBinding,
  TeamWorkshopSession,
} from "./contracts.js";
import { cleanText, digestExternal, isoNow } from "./contracts.js";
import type { FacilitatorProvider } from "./facilitator.js";
import {
  buildFrozenSourceFallback,
  buildWorkshopTextFallback,
  loadWorkshopVisual,
  renderWorkshopVisual,
  type RenderedWorkshopVisual,
} from "./visual.js";
import {
  addContribution,
  beginAuthorizedSynthesis,
  bindConversation,
  closeWorkshop,
  createWorkshop,
  delegateFacilitator,
  freezeWorkshop,
  markReview,
  markSynthesisFailed,
  markSynthesizing,
  passWorkshop,
  pauseWorkshop,
  resumeWorkshop,
  WorkshopError,
} from "./session.js";
import type { WorkshopRecord, WorkshopStore } from "./store.js";

export interface ClaimOutboundDeliveryInput {
  id: string;
  kind: OutboundDeliveryKind;
  conversation_ref: string;
  root_message_ref: string | null;
  artifact_id: string | null;
}

const BINDING_CAS_ATTEMPTS = 20;
const DELIVERY_CLAIM_LEASE_MS = 60_000;

export class WorkshopService {
  constructor(
    private readonly store: WorkshopStore,
    private readonly facilitator: FacilitatorProvider,
    private readonly dataRoot = resolve(process.env.DC_TEAM_DATA_DIR ?? ".data"),
  ) {}

  async start(input: StartWorkshopInput): Promise<WorkshopRecord> {
    const record = createWorkshop(input);
    try {
      await this.store.create(record);
      return record;
    } catch (error) {
      if (!(error instanceof WorkshopError) || error.code !== "SESSION_EXISTS") throw error;
      const existing = await this.store.get(record.session.id);
      const startDigest = digestExternal(cleanText(input.event_id, 500));
      if (
        existing &&
        existing.binding.platform === record.binding.platform &&
        existing.binding.workspace_ref === record.binding.workspace_ref &&
        existing.binding.channel_ref === record.binding.channel_ref &&
        existing.binding.processed_event_digests.includes(startDigest)
      ) {
        return existing;
      }
      throw error;
    }
  }

  async get(sessionId: string): Promise<WorkshopRecord> {
    const record = await this.store.get(sessionId);
    if (!record) throw new WorkshopError("Workshop session was not found.", "SESSION_NOT_FOUND");
    return record;
  }

  async bindRoot(
    sessionId: string,
    conversationRef: string,
    rootMessageRef: string,
    now?: string,
  ): Promise<WorkshopRecord> {
    const record = await this.get(sessionId);
    if (record.binding.conversation_ref || record.binding.root_message_ref) {
      if (
        record.binding.conversation_ref === cleanText(conversationRef, 500) &&
        record.binding.root_message_ref === cleanText(rootMessageRef, 500)
      ) {
        return record;
      }
      throw new WorkshopError(
        "This workshop is already bound to a different platform thread.",
        "BINDING_CONFLICT",
      );
    }
    const next = {
      session: record.session,
      binding: bindConversation(record.binding, conversationRef, rootMessageRef, now),
    };
    return this.store.saveBinding(next.binding, record.binding.binding_version);
  }

  private async updateBinding(
    sessionId: string,
    mutate: (binding: TeamChannelBinding) => void,
  ): Promise<WorkshopRecord> {
    for (let attempt = 0; attempt < BINDING_CAS_ATTEMPTS; attempt += 1) {
      const current = await this.get(sessionId);
      const binding = structuredClone(current.binding);
      mutate(binding);
      binding.binding_version = current.binding.binding_version + 1;
      binding.updated_at = isoNow();
      try {
        return await this.store.saveBinding(binding, current.binding.binding_version);
      } catch (error) {
        if (!(error instanceof WorkshopError) || error.code !== "VERSION_CONFLICT") throw error;
      }
    }
    throw new WorkshopError(
      "Private delivery state changed too frequently; retry this operation.",
      "VERSION_CONFLICT",
    );
  }

  async claimOutboundDelivery(
    sessionId: string,
    input: ClaimOutboundDeliveryInput,
  ): Promise<{ claimed: boolean; record: WorkshopRecord; receipt: OutboundDeliveryReceipt }> {
    const id = cleanText(input.id, 500);
    const conversation = cleanText(input.conversation_ref, 500);
    const root = cleanText(input.root_message_ref ?? "", 500) || null;
    const artifact = cleanText(input.artifact_id ?? "", 100) || null;
    if (!id || !conversation) {
      throw new WorkshopError("A delivery ID and conversation are required.", "INVALID_DELIVERY");
    }
    for (let attempt = 0; attempt < BINDING_CAS_ATTEMPTS; attempt += 1) {
      const current = await this.get(sessionId);
      const existing = current.binding.outbound_deliveries.find((item) => item.id === id);
      const claimExpired = existing?.status === "CLAIMED" &&
        Date.now() - new Date(existing.updated_at).valueOf() >= DELIVERY_CLAIM_LEASE_MS;
      if (existing && !(existing.status === "FAILED" || existing.status === "UNKNOWN" || claimExpired)) {
        return { claimed: false, record: current, receipt: structuredClone(existing) };
      }
      const now = isoNow();
      const binding = structuredClone(current.binding);
      let receipt = binding.outbound_deliveries.find((item) => item.id === id);
      if (receipt) {
        if (
          receipt.kind !== input.kind ||
          receipt.conversation_ref !== conversation ||
          receipt.artifact_id !== artifact ||
          (receipt.root_message_ref && root && receipt.root_message_ref !== root)
        ) {
          throw new WorkshopError("A delivery key was reused for a different platform effect.", "DELIVERY_KEY_CONFLICT");
        }
        receipt.status = "CLAIMED";
        receipt.root_message_ref ??= root;
        receipt.delivery_attempts += 1;
        receipt.updated_at = now;
        receipt.last_error_code = null;
      } else {
        receipt = {
          id,
          kind: input.kind,
          conversation_ref: conversation,
          root_message_ref: root,
          message_ref: null,
          file_ref: null,
          artifact_id: artifact,
          status: "CLAIMED",
          posted_at: null,
          updated_at: now,
          delivery_attempts: 1,
          delete_attempts: 0,
          last_error_code: null,
        };
        binding.outbound_deliveries.push(receipt);
      }
      binding.binding_version = current.binding.binding_version + 1;
      binding.updated_at = now;
      try {
        const record = await this.store.saveBinding(binding, current.binding.binding_version);
        const saved = record.binding.outbound_deliveries.find((item) => item.id === id)!;
        return { claimed: true, record, receipt: structuredClone(saved) };
      } catch (error) {
        if (!(error instanceof WorkshopError) || error.code !== "VERSION_CONFLICT") throw error;
      }
    }
    throw new WorkshopError("Delivery claim could not be serialized.", "VERSION_CONFLICT");
  }

  async completeOutboundDelivery(
    sessionId: string,
    idValue: string,
    result: { message_ref?: string | null; file_ref?: string | null; root_message_ref?: string | null },
  ): Promise<WorkshopRecord> {
    const id = cleanText(idValue, 500);
    const message = cleanText(result.message_ref ?? "", 500) || null;
    const file = cleanText(result.file_ref ?? "", 500) || null;
    const root = cleanText(result.root_message_ref ?? "", 500) || null;
    return this.updateBinding(sessionId, (binding) => {
      const receipt = binding.outbound_deliveries.find((item) => item.id === id);
      if (!receipt) throw new WorkshopError("Delivery receipt was not found.", "DELIVERY_NOT_FOUND");
      if (receipt.status === "POSTED") {
        if (
          (message && receipt.message_ref !== message) ||
          (file && receipt.file_ref !== file) ||
          (root && receipt.root_message_ref !== root)
        ) {
          throw new WorkshopError("Completed delivery receipt references changed.", "DELIVERY_KEY_CONFLICT");
        }
        return;
      }
      if (!(message || file)) {
        throw new WorkshopError("A completed delivery requires a remote message or file reference.", "INVALID_DELIVERY");
      }
      receipt.message_ref = message;
      receipt.file_ref = file;
      receipt.root_message_ref ??= root;
      receipt.status = "POSTED";
      receipt.posted_at = isoNow();
      receipt.updated_at = receipt.posted_at;
      receipt.last_error_code = null;
    });
  }

  async failOutboundDelivery(sessionId: string, idValue: string, errorCodeValue: string): Promise<WorkshopRecord> {
    const id = cleanText(idValue, 500);
    const errorCode = cleanText(errorCodeValue, 100) || "DELIVERY_FAILED";
    return this.updateBinding(sessionId, (binding) => {
      const receipt = binding.outbound_deliveries.find((item) => item.id === id);
      if (!receipt) throw new WorkshopError("Delivery receipt was not found.", "DELIVERY_NOT_FOUND");
      if (receipt.status === "POSTED" || receipt.status === "DELETED") return;
      receipt.status = "FAILED";
      receipt.last_error_code = errorCode;
      receipt.updated_at = isoNow();
    });
  }

  async markOutboundCleanup(
    sessionId: string,
    idValue: string,
    status: Extract<OutboundDeliveryStatus, "DELETE_PENDING" | "DELETED" | "DELETE_FAILED">,
    errorCodeValue?: string | null,
  ): Promise<WorkshopRecord> {
    const id = cleanText(idValue, 500);
    const errorCode = cleanText(errorCodeValue ?? "", 100) || null;
    return this.updateBinding(sessionId, (binding) => {
      const receipt = binding.outbound_deliveries.find((item) => item.id === id);
      if (!receipt) throw new WorkshopError("Delivery receipt was not found.", "DELIVERY_NOT_FOUND");
      if (receipt.status === "DELETED" && status === "DELETED") return;
      if (status === "DELETE_PENDING") receipt.delete_attempts += 1;
      receipt.status = status;
      receipt.last_error_code = status === "DELETE_FAILED" ? errorCode ?? "REMOTE_DELETE_FAILED" : null;
      receipt.updated_at = isoNow();
    });
  }

  /** Recover an immutable REVIEW artifact for delivery retry without re-synthesis. */
  async loadLatestVisual(input: ControlInput): Promise<{
    record: WorkshopRecord;
    visual: RenderedWorkshopVisual;
  }> {
    const digest = digestExternal(cleanText(input.event_id, 500));
    for (let attempt = 0; attempt < BINDING_CAS_ATTEMPTS; attempt += 1) {
      const current = await this.assertController(input.session_id, input.actor_ref);
      if (!(current.session.status === "REVIEW" || current.session.status === "COMPLETED")) {
        throw new WorkshopError("Delivery-only retry requires an existing reviewed artifact.", "INVALID_TRANSITION");
      }
      try {
        const claimed = await this.store.claimEvent(
          input.session_id,
          digest,
          current.binding.binding_version,
          input.now,
        );
        if (!claimed.claimed) {
          throw new WorkshopError("This delivery retry was already processed.", "DUPLICATE_EVENT");
        }
        return {
          record: claimed.record,
          visual: await loadWorkshopVisual(claimed.record.session, this.dataRoot),
        };
      } catch (error) {
        if (error instanceof WorkshopError && error.code === "VERSION_CONFLICT") continue;
        throw error;
      }
    }
    throw new WorkshopError("Delivery retry could not be serialized.", "VERSION_CONFLICT");
  }

  async contribute(input: ContributionInput): Promise<ReturnType<typeof addContribution>> {
    const current = await this.get(input.session_id);
    const result = addContribution(current.session, current.binding, input);
    await this.store.save(
      { session: result.session, binding: result.binding },
      current.session.step_version,
      current.binding.binding_version,
      digestExternal(cleanText(input.event_id, 500)),
    );
    return result;
  }

  async freeze(input: ControlInput): Promise<WorkshopRecord> {
    const current = await this.get(input.session_id);
    const result = freezeWorkshop(current.session, current.binding, input);
    await this.store.save(
      result,
      current.session.step_version,
      current.binding.binding_version,
      digestExternal(cleanText(input.event_id, 500)),
    );
    return result;
  }

  async pause(input: ControlInput): Promise<WorkshopRecord> {
    const current = await this.get(input.session_id);
    const result = pauseWorkshop(current.session, current.binding, input);
    await this.store.save(
      result,
      current.session.step_version,
      current.binding.binding_version,
      digestExternal(cleanText(input.event_id, 500)),
    );
    return result;
  }

  async resume(input: ControlInput): Promise<WorkshopRecord> {
    const current = await this.get(input.session_id);
    const result = resumeWorkshop(current.session, current.binding, input);
    await this.store.save(
      result,
      current.session.step_version,
      current.binding.binding_version,
      digestExternal(cleanText(input.event_id, 500)),
    );
    return result;
  }

  async pass(input: ControlInput): Promise<WorkshopRecord> {
    const current = await this.get(input.session_id);
    const result = passWorkshop(current.session, current.binding, input);
    await this.store.save(
      result,
      current.session.step_version,
      current.binding.binding_version,
      digestExternal(cleanText(input.event_id, 500)),
    );
    return result;
  }

  async delegate(input: DelegateInput): Promise<WorkshopRecord> {
    const current = await this.get(input.session_id);
    const result = delegateFacilitator(current.session, current.binding, input);
    await this.store.save(
      result,
      current.session.step_version,
      current.binding.binding_version,
      digestExternal(cleanText(input.event_id, 500)),
    );
    return result;
  }

  async synthesize(sessionId: string, platform: Platform): Promise<{
    record: WorkshopRecord;
    visual: RenderedWorkshopVisual;
  }> {
    const frozen = await this.get(sessionId);
    const synthesizing = markSynthesizing(frozen.session);
    await this.store.save(
      { session: synthesizing, binding: frozen.binding },
      frozen.session.step_version,
      frozen.binding.binding_version,
    );
    return this.performSynthesis(synthesizing, frozen.binding, platform);
  }

  /** Controller-authorized retry after a provider or rendering failure restored the set to FROZEN. */
  async retrySynthesis(input: ControlInput, platform: Platform): Promise<{
    record: WorkshopRecord;
    visual: RenderedWorkshopVisual;
  }> {
    const frozen = await this.get(input.session_id);
    const authorized = beginAuthorizedSynthesis(frozen.session, frozen.binding, input);
    await this.store.save(
      authorized,
      frozen.session.step_version,
      frozen.binding.binding_version,
      digestExternal(cleanText(input.event_id, 500)),
    );
    return this.performSynthesis(authorized.session, authorized.binding, platform);
  }

  private async performSynthesis(
    synthesizing: TeamWorkshopSession,
    binding: TeamChannelBinding,
    platform: Platform,
  ): Promise<{ record: WorkshopRecord; visual: RenderedWorkshopVisual }> {
    let synthesis;
    try {
      synthesis = await this.facilitator.synthesize(synthesizing);
    } catch (error) {
      await this.restoreFrozenAfterFailure(synthesizing, binding, "FACILITATION_FAILED");
      throw new WorkshopError(
        "AI facilitation failed. The frozen contribution set is intact and synthesis can be retried.",
        "FACILITATION_FAILED",
        { cause: error },
        buildFrozenSourceFallback(synthesizing, "AI facilitation did not complete; no synthesis claim is made."),
      );
    }
    let visual: RenderedWorkshopVisual;
    try {
      visual = await renderWorkshopVisual(synthesizing, synthesis, platform, this.dataRoot);
    } catch (error) {
      await this.restoreFrozenAfterFailure(synthesizing, binding, "RENDER_FAILED");
      throw new WorkshopError(
        "Visual rendering failed. The frozen contribution set is intact and synthesis can be retried; use the text fallback when available.",
        "RENDER_FAILED",
        { cause: error },
        buildWorkshopTextFallback(synthesizing, synthesis),
      );
    }
    const review = markReview(synthesizing, visual.artifact_ref);
    await this.store.save(
      { session: review, binding },
      synthesizing.step_version,
      binding.binding_version,
    );
    return { record: { session: review, binding }, visual };
  }

  private async restoreFrozenAfterFailure(
    synthesizing: TeamWorkshopSession,
    binding: TeamChannelBinding,
    failureCode: "FACILITATION_FAILED" | "RENDER_FAILED",
  ): Promise<void> {
    const failed = markSynthesisFailed(synthesizing, failureCode);
    try {
      await this.store.save(
        { session: failed, binding },
        synthesizing.step_version,
        binding.binding_version,
      );
    } catch (error) {
      throw new WorkshopError(
        "Synthesis failed and workshop state could not be restored automatically.",
        "SYNTHESIS_RECOVERY_FAILED",
        { cause: error },
      );
    }
  }

  async close(input: ControlInput): Promise<WorkshopRecord> {
    const current = await this.get(input.session_id);
    const result = closeWorkshop(current.session, current.binding, input);
    await this.store.save(
      result,
      current.session.step_version,
      current.binding.binding_version,
      digestExternal(cleanText(input.event_id, 500)),
    );
    return result;
  }

  /** Read-only controller preflight for adapters that must acknowledge before scheduling work. */
  async assertController(sessionId: string, actorRef: string): Promise<WorkshopRecord> {
    const current = await this.get(sessionId);
    const participantId = current.binding.participant_refs[digestExternal(actorRef)];
    if (!participantId || !current.session.controller_participant_ids.includes(participantId)) {
      throw new WorkshopError(
        "Only the initiator or a delegated facilitator can advance this exercise.",
        "CONTROL_FORBIDDEN",
      );
    }
    return current;
  }

  async delete(sessionId: string, actorRef: string): Promise<boolean> {
    await this.assertController(sessionId, actorRef);
    const deleted = await this.store.delete(sessionId);
    await this.removeArtifacts(sessionId);
    return deleted;
  }

  async purgeExpired(now?: string): Promise<string[]> {
    const expired = await this.store.listExpired(now);
    const deleted: string[] = [];
    for (const sessionId of expired) {
      if (await this.store.delete(sessionId)) deleted.push(sessionId);
      await this.removeArtifacts(sessionId);
    }
    return deleted;
  }

  private async removeArtifacts(sessionId: string): Promise<void> {
    if (!/^TW-[A-F0-9-]{36}$/.test(sessionId)) {
      throw new WorkshopError("Invalid workshop session ID.", "INVALID_SESSION_ID");
    }
    const artifactRoot = resolve(this.dataRoot, "artifacts");
    const target = resolve(artifactRoot, sessionId);
    if (!target.startsWith(`${artifactRoot}${sep}`)) {
      throw new WorkshopError("Workshop artifact path escaped the data root.", "INVALID_SESSION_ID");
    }
    await rm(target, { recursive: true, force: true });
  }

  /** Portable export intentionally omits workspace, channel, user, and event identifiers. */
  async exportPortable(sessionId: string): Promise<TeamWorkshopSession> {
    return structuredClone((await this.get(sessionId)).session);
  }

  async privateBinding(sessionId: string): Promise<TeamChannelBinding> {
    return structuredClone((await this.get(sessionId)).binding);
  }
}
