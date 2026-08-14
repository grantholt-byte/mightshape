import {
  cleanText,
  digestExternal,
  isoNow,
  MAX_WORKSHOP_CONTRIBUTIONS,
  retentionDate,
  workshopId,
  type ContributionInput,
  type ControlInput,
  type DelegateInput,
  type StartWorkshopInput,
  type TeamChannelBinding,
  type TeamWorkshopSession,
  type WorkshopContribution,
  type WorkshopHistoryEvent,
  type WorkshopParticipant,
  type WorkshopPresentation,
} from "./contracts.js";
import { exerciseDefinition } from "./exercises.js";

export class WorkshopError extends Error {
  constructor(
    message: string,
    readonly code: string,
    options?: ErrorOptions,
    readonly text_fallback?: string,
  ) {
    super(message, options);
    this.name = "WorkshopError";
  }
}

function nextNumberedId(prefix: string, records: Array<{ id: string }>): string {
  let highest = 0;
  const pattern = new RegExp(`^${prefix}-(\\d+)$`);
  for (const item of records) {
    const match = pattern.exec(item.id);
    if (match?.[1]) highest = Math.max(highest, Number(match[1]));
  }
  return `${prefix}-${String(highest + 1).padStart(3, "0")}`;
}

function clone<T>(value: T): T {
  return structuredClone(value);
}

function event(
  session: TeamWorkshopSession,
  action: string,
  at: string,
  actor: string | null,
  details: Record<string, unknown> = {},
): WorkshopHistoryEvent {
  return {
    version: session.step_version,
    at,
    action,
    actor_participant_id: actor,
    details,
  };
}

function advance(
  session: TeamWorkshopSession,
  action: string,
  at: string,
  actor: string | null,
  details: Record<string, unknown> = {},
): TeamWorkshopSession {
  session.step_version += 1;
  session.updated_at = at;
  session.history.push(event(session, action, at, actor, details));
  return session;
}

function participantFor(binding: TeamChannelBinding, actorRef: string): string | undefined {
  return binding.participant_refs[digestExternal(actorRef)];
}

function requireController(
  session: TeamWorkshopSession,
  binding: TeamChannelBinding,
  actorRef: string,
): string {
  const participantId = participantFor(binding, actorRef);
  if (!participantId || !session.controller_participant_ids.includes(participantId)) {
    throw new WorkshopError(
      "Only the initiator or a delegated facilitator can advance this exercise.",
      "CONTROL_FORBIDDEN",
    );
  }
  return participantId;
}

function ensureNewEvent(binding: TeamChannelBinding, eventId: string): string {
  const normalized = cleanText(eventId, 500);
  if (!normalized) throw new WorkshopError("event_id is required", "INVALID_EVENT");
  const digest = digestExternal(normalized);
  if (binding.processed_event_digests.includes(digest)) {
    throw new WorkshopError("This interaction was already processed.", "DUPLICATE_EVENT");
  }
  return digest;
}

function markEvent(binding: TeamChannelBinding, digest: string, at: string): TeamChannelBinding {
  const next = clone(binding);
  next.processed_event_digests.push(digest);
  // Digests are private, fixed-size, and retained until the workshop expires so
  // an old platform retry can never become a new mutation merely due to age.
  next.binding_version += 1;
  next.updated_at = at;
  return next;
}

function activeParticipant(session: TeamWorkshopSession, participantId: string): WorkshopParticipant {
  const participant = session.participants.find((item) => item.id === participantId);
  if (!participant || participant.status === "LEFT") {
    throw new WorkshopError("The participant is not active in this exercise.", "PARTICIPANT_INACTIVE");
  }
  return participant;
}

function ensureMatchingSession(
  session: TeamWorkshopSession,
  binding: TeamChannelBinding,
  sessionId: string,
): void {
  if (session.id !== sessionId || binding.session_id !== sessionId) {
    throw new WorkshopError("Workshop session and binding do not match.", "SESSION_MISMATCH");
  }
}

export function createWorkshop(input: StartWorkshopInput): {
  session: TeamWorkshopSession;
  binding: TeamChannelBinding;
} {
  const challenge = cleanText(input.challenge, 2_000);
  if (!challenge) throw new WorkshopError("A design challenge is required.", "CHALLENGE_REQUIRED");
  const actorRef = cleanText(input.actor_ref, 500);
  if (!actorRef) throw new WorkshopError("An initiating participant is required.", "ACTOR_REQUIRED");
  const workspaceRef = cleanText(input.workspace_ref, 500);
  const channelRef = cleanText(input.channel_ref, 500);
  const eventId = cleanText(input.event_id, 500);
  if (!workspaceRef || !channelRef) throw new WorkshopError("A workspace and channel are required.", "SCOPE_REQUIRED");
  if (!eventId) throw new WorkshopError("event_id is required", "INVALID_EVENT");
  const definition = exerciseDefinition(input.exercise);
  const now = isoNow(input.now);
  const id = workshopId([input.platform, workspaceRef, channelRef, eventId].join("\0"));
  const initiator: WorkshopParticipant = {
    id: "TP-001",
    role: "INITIATOR",
    status: "ACTIVE",
    joined_at: now,
  };
  const session: TeamWorkshopSession = {
    schema_version: "1.0.0",
    id,
    exercise: input.exercise,
    starting_point: input.starting_point ?? "UNSURE",
    challenge,
    visibility: input.visibility ?? definition.default_visibility,
    status: "COLLECTING",
    facilitator_level: input.facilitator_level ?? "NOVICE_ASSISTED",
    initiator_participant_id: initiator.id,
    controller_participant_ids: [initiator.id],
    participants: [initiator],
    prompts: [
      {
        id: "UP-001",
        purpose: definition.purpose,
        mindset: definition.mindset,
        prompt: definition.prompt,
        status: "OPEN",
        opened_at: now,
        closed_at: null,
      },
    ],
    contributions: [],
    artifacts: [],
    contribution_set_frozen_at: null,
    step_version: 1,
    created_at: now,
    updated_at: now,
    retention_expires_at: retentionDate(now, input.retention_days ?? 30),
    history: [],
  };
  session.history.push(
    event(session, "WORKSHOP_STARTED", now, initiator.id, {
      exercise: input.exercise,
      visibility: session.visibility,
      starting_point: session.starting_point,
      provenance: "USER_PROVIDED",
    }),
  );
  const binding: TeamChannelBinding = {
    schema_version: "1.0.0",
    session_id: id,
    binding_version: 1,
    platform: input.platform,
    workspace_ref: workspaceRef,
    channel_ref: channelRef,
    conversation_ref: cleanText(input.conversation_ref ?? "", 500) || null,
    root_message_ref: cleanText(input.root_message_ref ?? "", 500) || null,
    participant_refs: { [digestExternal(actorRef)]: initiator.id },
    processed_event_digests: [digestExternal(eventId)],
    outbound_deliveries: [],
    created_at: now,
    updated_at: now,
  };
  return { session, binding };
}

export function bindConversation(
  binding: TeamChannelBinding,
  conversationRef: string,
  rootMessageRef: string,
  nowValue?: string,
): TeamChannelBinding {
  const conversation = cleanText(conversationRef, 500);
  const root = cleanText(rootMessageRef, 500);
  if (!conversation || !root) {
    throw new WorkshopError("conversation and root message references are required", "BINDING_REQUIRED");
  }
  const next = clone(binding);
  next.conversation_ref = conversation;
  next.root_message_ref = root;
  next.binding_version += 1;
  next.updated_at = isoNow(nowValue);
  return next;
}

export function addContribution(
  current: TeamWorkshopSession,
  currentBinding: TeamChannelBinding,
  input: ContributionInput,
): { session: TeamWorkshopSession; binding: TeamChannelBinding; contribution: WorkshopContribution } {
  ensureMatchingSession(current, currentBinding, input.session_id);
  if (current.status !== "COLLECTING") {
    throw new WorkshopError("This exercise is not accepting contributions.", "NOT_COLLECTING");
  }
  if (current.contributions.length >= MAX_WORKSHOP_CONTRIBUTIONS) {
    throw new WorkshopError(
      `This exercise has reached its ${MAX_WORKSHOP_CONTRIBUTIONS}-contribution limit. Freeze this round before starting another.`,
      "CONTRIBUTION_LIMIT",
    );
  }
  const content = cleanText(input.content, 2_000);
  if (!content) throw new WorkshopError("A contribution cannot be empty.", "CONTENT_REQUIRED");
  const now = isoNow(input.now);
  const eventDigest = ensureNewEvent(currentBinding, input.event_id);
  const session = clone(current);
  let binding = clone(currentBinding);
  const actorRef = cleanText(input.actor_ref, 500);
  if (!actorRef) throw new WorkshopError("A contributing participant is required.", "ACTOR_REQUIRED");
  const actorDigest = digestExternal(actorRef);
  let participantId = binding.participant_refs[actorDigest];
  if (!participantId) {
    participantId = nextNumberedId("TP", session.participants);
    session.participants.push({
      id: participantId,
      role: "CONTRIBUTOR",
      status: "ACTIVE",
      joined_at: now,
    });
    binding.participant_refs[actorDigest] = participantId;
  }
  const participant = activeParticipant(session, participantId);
  if (participant.status === "PASSED") participant.status = "ACTIVE";
  const definition = exerciseDefinition(session.exercise);
  const contribution: WorkshopContribution = {
    id: nextNumberedId("UC", session.contributions),
    participant_id: participantId,
    kind: input.kind ?? definition.contribution_kind,
    content,
    provenance: "USER_PROVIDED",
    status: "ACTIVE",
    submitted_at: now,
    revealed_at: session.visibility === "OPEN" ? now : null,
  };
  session.contributions.push(contribution);
  advance(session, "CONTRIBUTION_ADDED", now, participantId, {
    contribution_id: contribution.id,
    provenance: contribution.provenance,
    visibility: session.visibility,
  });
  binding = markEvent(binding, eventDigest, now);
  return { session, binding, contribution };
}

export function freezeWorkshop(
  current: TeamWorkshopSession,
  currentBinding: TeamChannelBinding,
  input: ControlInput,
): { session: TeamWorkshopSession; binding: TeamChannelBinding } {
  ensureMatchingSession(current, currentBinding, input.session_id);
  if (current.status !== "COLLECTING") {
    throw new WorkshopError("Only a collecting exercise can be frozen.", "INVALID_TRANSITION");
  }
  if (current.contributions.length === 0) {
    throw new WorkshopError("At least one contribution is required before freeze.", "EMPTY_SET");
  }
  const now = isoNow(input.now);
  const eventDigest = ensureNewEvent(currentBinding, input.event_id);
  const session = clone(current);
  const actor = requireController(session, currentBinding, input.actor_ref);
  session.status = "FROZEN";
  session.contribution_set_frozen_at = now;
  for (const contribution of session.contributions) {
    if (contribution.status === "ACTIVE" && contribution.revealed_at === null) {
      contribution.revealed_at = now;
    }
  }
  for (const prompt of session.prompts) {
    if (prompt.status === "OPEN") {
      prompt.status = "CLOSED";
      prompt.closed_at = now;
    }
  }
  advance(session, "CONTRIBUTION_SET_FROZEN", now, actor, {
    contribution_count: session.contributions.filter((item) => item.status === "ACTIVE").length,
  });
  return { session, binding: markEvent(currentBinding, eventDigest, now) };
}

export function pauseWorkshop(
  current: TeamWorkshopSession,
  currentBinding: TeamChannelBinding,
  input: ControlInput,
): { session: TeamWorkshopSession; binding: TeamChannelBinding } {
  ensureMatchingSession(current, currentBinding, input.session_id);
  if (current.status !== "COLLECTING") {
    throw new WorkshopError("Only a collecting exercise can be paused.", "INVALID_TRANSITION");
  }
  const now = isoNow(input.now);
  const eventDigest = ensureNewEvent(currentBinding, input.event_id);
  const session = clone(current);
  const actor = requireController(session, currentBinding, input.actor_ref);
  session.status = "PAUSED";
  advance(session, "WORKSHOP_PAUSED", now, actor);
  return { session, binding: markEvent(currentBinding, eventDigest, now) };
}

export function resumeWorkshop(
  current: TeamWorkshopSession,
  currentBinding: TeamChannelBinding,
  input: ControlInput,
): { session: TeamWorkshopSession; binding: TeamChannelBinding } {
  ensureMatchingSession(current, currentBinding, input.session_id);
  if (current.status !== "PAUSED") {
    throw new WorkshopError("Only a paused exercise can resume collecting.", "INVALID_TRANSITION");
  }
  const now = isoNow(input.now);
  const eventDigest = ensureNewEvent(currentBinding, input.event_id);
  const session = clone(current);
  const actor = requireController(session, currentBinding, input.actor_ref);
  session.status = "COLLECTING";
  advance(session, "WORKSHOP_RESUMED", now, actor);
  return { session, binding: markEvent(currentBinding, eventDigest, now) };
}

export function passWorkshop(
  current: TeamWorkshopSession,
  currentBinding: TeamChannelBinding,
  input: ControlInput,
): { session: TeamWorkshopSession; binding: TeamChannelBinding } {
  ensureMatchingSession(current, currentBinding, input.session_id);
  if (!(["COLLECTING", "PAUSED"] as const).includes(current.status as "COLLECTING" | "PAUSED")) {
    throw new WorkshopError("Passing is only available while an exercise is collecting or paused.", "INVALID_TRANSITION");
  }
  const actorRef = cleanText(input.actor_ref, 500);
  if (!actorRef) throw new WorkshopError("A participant is required.", "ACTOR_REQUIRED");
  const now = isoNow(input.now);
  const eventDigest = ensureNewEvent(currentBinding, input.event_id);
  const session = clone(current);
  let binding = clone(currentBinding);
  const actorDigest = digestExternal(actorRef);
  let participantId = binding.participant_refs[actorDigest];
  if (!participantId) {
    participantId = nextNumberedId("TP", session.participants);
    session.participants.push({
      id: participantId,
      role: "CONTRIBUTOR",
      status: "PASSED",
      joined_at: now,
    });
    binding.participant_refs[actorDigest] = participantId;
  } else {
    const participant = activeParticipant(session, participantId);
    participant.status = "PASSED";
  }
  advance(session, "PARTICIPANT_PASSED", now, participantId);
  binding = markEvent(binding, eventDigest, now);
  return { session, binding };
}

export function delegateFacilitator(
  current: TeamWorkshopSession,
  currentBinding: TeamChannelBinding,
  input: DelegateInput,
): { session: TeamWorkshopSession; binding: TeamChannelBinding } {
  ensureMatchingSession(current, currentBinding, input.session_id);
  if (["COMPLETED", "CLOSED"].includes(current.status)) {
    throw new WorkshopError("A completed or closed workshop cannot change facilitators.", "INVALID_TRANSITION");
  }
  const now = isoNow(input.now);
  const eventDigest = ensureNewEvent(currentBinding, input.event_id);
  const session = clone(current);
  const actor = requireController(session, currentBinding, input.actor_ref);
  const targetRef = cleanText(input.target_actor_ref, 500);
  if (!targetRef) throw new WorkshopError("A target participant is required.", "TARGET_REQUIRED");
  const targetId = participantFor(currentBinding, targetRef);
  if (!targetId) {
    throw new WorkshopError(
      "The delegated facilitator must first opt in by contributing or passing.",
      "TARGET_NOT_PARTICIPATING",
    );
  }
  const target = activeParticipant(session, targetId);
  target.status = "ACTIVE";
  if (target.role === "CONTRIBUTOR") target.role = "FACILITATOR";
  if (!session.controller_participant_ids.includes(targetId)) {
    session.controller_participant_ids.push(targetId);
  }
  advance(session, "FACILITATOR_DELEGATED", now, actor, { target_participant_id: targetId });
  return { session, binding: markEvent(currentBinding, eventDigest, now) };
}

export function markSynthesizing(
  current: TeamWorkshopSession,
  nowValue?: string,
  actor: string | null = null,
): TeamWorkshopSession {
  if (current.status !== "FROZEN") {
    throw new WorkshopError("Only a frozen exercise can begin synthesis.", "INVALID_TRANSITION");
  }
  const now = isoNow(nowValue);
  const session = clone(current);
  session.status = "SYNTHESIZING";
  return advance(session, "SYNTHESIS_STARTED", now, actor);
}

export function beginAuthorizedSynthesis(
  current: TeamWorkshopSession,
  currentBinding: TeamChannelBinding,
  input: ControlInput,
): { session: TeamWorkshopSession; binding: TeamChannelBinding } {
  ensureMatchingSession(current, currentBinding, input.session_id);
  const now = isoNow(input.now);
  const eventDigest = ensureNewEvent(currentBinding, input.event_id);
  const actor = requireController(current, currentBinding, input.actor_ref);
  return {
    session: markSynthesizing(current, now, actor),
    binding: markEvent(currentBinding, eventDigest, now),
  };
}

export function markReview(
  current: TeamWorkshopSession,
  artifact: TeamWorkshopSession["artifacts"][number],
  nowValue?: string,
): TeamWorkshopSession {
  if (current.status !== "SYNTHESIZING") {
    throw new WorkshopError("Only a synthesizing exercise can publish an artifact.", "INVALID_TRANSITION");
  }
  const now = isoNow(nowValue);
  const session = clone(current);
  session.artifacts.push(artifact);
  session.status = "REVIEW";
  return advance(session, "ARTIFACT_PUBLISHED", now, null, {
    artifact_id: artifact.artifact_id,
    artifact_type: artifact.artifact_type,
  });
}

export function markSynthesisFailed(
  current: TeamWorkshopSession,
  failureCode: "FACILITATION_FAILED" | "RENDER_FAILED",
  nowValue?: string,
): TeamWorkshopSession {
  if (current.status !== "SYNTHESIZING") {
    throw new WorkshopError("Only a synthesizing exercise can record synthesis failure.", "INVALID_TRANSITION");
  }
  const now = isoNow(nowValue);
  const session = clone(current);
  session.status = "FROZEN";
  return advance(session, "SYNTHESIS_FAILED", now, null, { failure_code: failureCode, retryable: true });
}

export function closeWorkshop(
  current: TeamWorkshopSession,
  currentBinding: TeamChannelBinding,
  input: ControlInput,
): { session: TeamWorkshopSession; binding: TeamChannelBinding } {
  ensureMatchingSession(current, currentBinding, input.session_id);
  if (current.status === "CLOSED") {
    throw new WorkshopError("This workshop is already closed.", "INVALID_TRANSITION");
  }
  const now = isoNow(input.now);
  const eventDigest = ensureNewEvent(currentBinding, input.event_id);
  const session = clone(current);
  const actor = requireController(session, currentBinding, input.actor_ref);
  session.status = "CLOSED";
  for (const prompt of session.prompts) {
    if (prompt.status === "OPEN") {
      prompt.status = "CLOSED";
      prompt.closed_at = now;
    }
  }
  advance(session, "WORKSHOP_CLOSED", now, actor);
  return { session, binding: markEvent(currentBinding, eventDigest, now) };
}

export function workshopPresentation(session: TeamWorkshopSession): WorkshopPresentation {
  const definition = exerciseDefinition(session.exercise);
  const activeParticipants = session.participants.filter((item) => item.status === "ACTIVE").length;
  const activeContributions = session.contributions.filter((item) => item.status === "ACTIVE").length;
  const visibilityLine =
    session.visibility === "SEALED" && session.status === "COLLECTING"
      ? "Submissions are sealed. Only the count is visible until the initiator freezes the set."
      : "Contributions are visible to people in this channel thread.";
  return {
    session_id: session.id,
    phase: session.status,
    headline: `◇ MightShape · ${definition.label}`,
    body: [
      `Challenge: ${session.challenge}`,
      `Purpose: ${definition.purpose}`,
      visibilityLine,
      "Inputs are processed by an AI facilitator and stored as USER_PROVIDED design material—not human research evidence.",
      `Retention: ${session.retention_expires_at.slice(0, 10)}. Do not submit secrets or material inappropriate for this channel.`,
    ].join("\n"),
    prompt:
      session.prompts.find((item) => item.status === "OPEN")?.prompt ?? null,
    participant_count: activeParticipants,
    contribution_count: activeContributions,
    visibility: session.visibility,
  };
}
