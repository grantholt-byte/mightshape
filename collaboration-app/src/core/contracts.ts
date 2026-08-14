import { createHash, randomUUID } from "node:crypto";

export const PLATFORMS = ["SLACK", "DISCORD", "TEAMS"] as const;
export type Platform = (typeof PLATFORMS)[number];

export const EXERCISES = [
  "BRAINSTORMING",
  "BRAINWRITING",
  "AFFINITY_CLUSTERING",
  "PROCESS_RECONSTRUCTION",
  "ASSUMPTION_MAPPING",
  "POV_HMW",
  "PROTOTYPE_DESIGN",
  "TEST_DESIGN",
] as const;
export type Exercise = (typeof EXERCISES)[number];

/**
 * A bounded frozen set keeps model, renderer, and platform delivery costs
 * predictable without truncating any contribution that the workshop accepts.
 */
export const MAX_WORKSHOP_CONTRIBUTIONS = 100;

export const STARTING_POINTS = [
  "EARLY_HUNCH",
  "GROUNDED_EXPLORATION",
  "FRAMED_CHALLENGE",
  "CONCEPT",
  "PROTOTYPE",
  "LIVE",
  "UNSURE",
] as const;
export type StartingPoint = (typeof STARTING_POINTS)[number];

export type Visibility = "OPEN" | "SEALED";
export type WorkshopStatus =
  | "COLLECTING"
  | "PAUSED"
  | "FROZEN"
  | "SYNTHESIZING"
  | "REVIEW"
  | "COMPLETED"
  | "CLOSED";

export type ParticipantRole = "INITIATOR" | "FACILITATOR" | "CONTRIBUTOR";
export type ParticipantStatus = "ACTIVE" | "PASSED" | "LEFT";

export interface WorkshopParticipant {
  id: string;
  role: ParticipantRole;
  status: ParticipantStatus;
  joined_at: string;
}

export interface WorkshopContribution {
  id: string;
  participant_id: string;
  kind:
    | "IDEA"
    | "NOTE"
    | "SORT_MOVE"
    | "PROCESS_STEP"
    | "ASSUMPTION"
    | "POV_COMPONENT"
    | "HMW"
    | "PROTOTYPE_DECISION"
    | "TEST_DECISION";
  content: string;
  provenance: "USER_PROVIDED";
  status: "ACTIVE" | "SUPERSEDED";
  submitted_at: string;
  revealed_at: string | null;
}

export interface FacilitatorPrompt {
  id: string;
  purpose: string;
  mindset: string;
  prompt: string;
  status: "OPEN" | "CLOSED";
  opened_at: string;
  closed_at: string | null;
}

export interface WorkshopArtifactRef {
  artifact_id: string;
  artifact_type: "AFFINITY_MAP" | "PROCESS_MAP";
  source_contribution_ids: string[];
  png_sha256: string;
  alt_text: string;
  text_summary: string;
  recorded_at: string;
}

export interface WorkshopHistoryEvent {
  version: number;
  at: string;
  action: string;
  actor_participant_id: string | null;
  details: Record<string, unknown>;
}

export type OutboundDeliveryKind =
  | "ROOT"
  | "PROGRESS"
  | "SOURCE_SET"
  | "VISUAL"
  | "TEXT_FALLBACK"
  | "CONTROL"
  | "STATUS";

export type OutboundDeliveryStatus =
  | "CLAIMED"
  | "POSTED"
  | "FAILED"
  | "DELETE_PENDING"
  | "DELETED"
  | "DELETE_FAILED"
  | "UNKNOWN";

/** Private receipt for one logical platform side effect. */
export interface OutboundDeliveryReceipt {
  id: string;
  kind: OutboundDeliveryKind;
  conversation_ref: string;
  root_message_ref: string | null;
  message_ref: string | null;
  file_ref: string | null;
  artifact_id: string | null;
  status: OutboundDeliveryStatus;
  posted_at: string | null;
  updated_at: string;
  delivery_attempts: number;
  delete_attempts: number;
  last_error_code: string | null;
}

export interface TeamWorkshopSession {
  schema_version: "1.0.0";
  id: string;
  exercise: Exercise;
  starting_point: StartingPoint;
  challenge: string;
  visibility: Visibility;
  status: WorkshopStatus;
  facilitator_level: "NOVICE_ASSISTED" | "GUIDED" | "LIGHT_TOUCH";
  initiator_participant_id: string;
  controller_participant_ids: string[];
  participants: WorkshopParticipant[];
  prompts: FacilitatorPrompt[];
  contributions: WorkshopContribution[];
  artifacts: WorkshopArtifactRef[];
  contribution_set_frozen_at: string | null;
  step_version: number;
  created_at: string;
  updated_at: string;
  retention_expires_at: string;
  history: WorkshopHistoryEvent[];
}

/** Private adapter binding. Raw platform identifiers never enter portable exports. */
export interface TeamChannelBinding {
  schema_version: "1.0.0";
  session_id: string;
  /** Private-store optimistic version; independent from the portable design step. */
  binding_version: number;
  platform: Platform;
  workspace_ref: string;
  channel_ref: string;
  conversation_ref: string | null;
  root_message_ref: string | null;
  participant_refs: Record<string, string>;
  processed_event_digests: string[];
  outbound_deliveries: OutboundDeliveryReceipt[];
  created_at: string;
  updated_at: string;
}

export interface StartWorkshopInput {
  platform: Platform;
  workspace_ref: string;
  channel_ref: string;
  conversation_ref?: string | null;
  root_message_ref?: string | null;
  actor_ref: string;
  challenge: string;
  exercise: Exercise;
  starting_point?: StartingPoint;
  visibility?: Visibility;
  facilitator_level?: "NOVICE_ASSISTED" | "GUIDED" | "LIGHT_TOUCH";
  event_id: string;
  now?: string;
  retention_days?: number;
}

export interface ContributionInput {
  session_id: string;
  actor_ref: string;
  content: string;
  kind?: WorkshopContribution["kind"];
  event_id: string;
  now?: string;
}

export interface ControlInput {
  session_id: string;
  actor_ref: string;
  event_id: string;
  now?: string;
}

export interface DelegateInput extends ControlInput {
  target_actor_ref: string;
}

export interface WorkshopPresentation {
  session_id: string;
  phase: WorkshopStatus;
  headline: string;
  body: string;
  prompt: string | null;
  participant_count: number;
  contribution_count: number;
  visibility: Visibility;
}

export function cleanText(value: unknown, maxLength = 2_000): string {
  if (typeof value !== "string") return "";
  return value.replaceAll("\0", "").replace(/\s+/g, " ").trim().slice(0, maxLength);
}

export function digestExternal(value: string): string {
  return createHash("sha256").update(value).digest("hex");
}

export function workshopId(seed?: string): string {
  if (!seed) return `TW-${randomUUID().toUpperCase()}`;
  const value = createHash("sha256").update(seed).digest("hex").slice(0, 32).toUpperCase();
  return `TW-${value.slice(0, 8)}-${value.slice(8, 12)}-${value.slice(12, 16)}-${value.slice(16, 20)}-${value.slice(20)}`;
}

export function artifactId(): string {
  return `VA-${randomUUID().replaceAll("-", "").slice(0, 12).toUpperCase()}`;
}

export function isoNow(value?: string): string {
  if (!value) return new Date().toISOString();
  const parsed = new Date(value);
  if (Number.isNaN(parsed.valueOf())) throw new Error("now must be an ISO-8601 timestamp");
  return parsed.toISOString();
}

export function retentionDate(now: string, days = 30): string {
  if (!Number.isInteger(days) || days < 1 || days > 365) {
    throw new Error("retention_days must be between 1 and 365");
  }
  const result = new Date(now);
  result.setUTCDate(result.getUTCDate() + days);
  return result.toISOString();
}
