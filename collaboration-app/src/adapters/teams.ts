import { pathToFileURL } from "node:url";
import { resolve } from "node:path";
import {
  MessageActivityInput,
  type IAdaptiveCardActionInvokeActivity,
  type IMessageActivity,
  type ITaskFetchInvokeActivity,
  type ITaskSubmitInvokeActivity,
} from "@microsoft/teams.api";
import { App } from "@microsoft/teams.apps";
import {
  AdaptiveCard,
  ExecuteAction,
  Image,
  OpenDialogData,
  SubmitAction,
  SubmitData,
  TextBlock,
  TextInput,
  type IAdaptiveCard,
} from "@microsoft/teams.cards";
import {
  EXERCISES,
  type ControlInput,
  type Exercise,
  type OutboundDeliveryKind,
  type TeamWorkshopSession,
} from "../core/contracts.js";
import type { WorkshopRecord } from "../core/store.js";
import { facilitatorFromEnvironment } from "../core/facilitator.js";
import { chunkText, type RenderedWorkshopVisual } from "../core/visual.js";
import { WorkshopService } from "../core/service.js";
import { WorkshopError, workshopPresentation } from "../core/session.js";
import { FileWorkshopStore } from "../core/store.js";

const MAX_CARD_IMAGE_BYTES = 48_000;
const MAX_BOT_ACTIVITY_BYTES = 80_000;
const SESSION_ID = /^TW-[A-F0-9-]{36}$/;

const EXERCISE_ALIASES: Record<string, Exercise> = {
  brainstorm: "BRAINSTORMING",
  brainstorming: "BRAINSTORMING",
  brainwrite: "BRAINWRITING",
  brainwriting: "BRAINWRITING",
  affinity: "AFFINITY_CLUSTERING",
  cluster: "AFFINITY_CLUSTERING",
  process: "PROCESS_RECONSTRUCTION",
  journey: "PROCESS_RECONSTRUCTION",
  assumptions: "ASSUMPTION_MAPPING",
  assumption: "ASSUMPTION_MAPPING",
  pov: "POV_HMW",
  hmw: "POV_HMW",
  prototype: "PROTOTYPE_DESIGN",
  test: "TEST_DESIGN",
};

export interface TeamsInvocation {
  workspace_id: string;
  channel_id: string;
  conversation_id: string;
  root_message_id: string;
  actor_id: string;
  event_id: string;
}

export interface TeamsOutboundPort {
  reply(conversationId: string, rootMessageId: string, message: MessageActivityInput | string): Promise<{ id: string }>;
  deleteActivity(conversationId: string, messageId: string): Promise<void>;
}

export type TeamsCommand =
  | { action: "START"; exercise: Exercise; challenge: string }
  | { action: "ADD"; session_id: string; content: string }
  | { action: "PASS"; session_id: string }
  | { action: "FREEZE"; session_id: string }
  | { action: "CLOSE"; session_id: string }
  | { action: "DELETE"; session_id: string }
  | { action: "HELP" }
  | { action: "UNKNOWN" };

export type TeamsCommandResult =
  | { action: "STARTED"; session: TeamWorkshopSession }
  | { action: "CONTRIBUTED"; session: TeamWorkshopSession; contribution_id: string }
  | { action: "PASSED"; session: TeamWorkshopSession }
  | { action: "FROZEN"; session: TeamWorkshopSession }
  | { action: "CLOSED"; session: TeamWorkshopSession }
  | { action: "DELETE_REQUESTED"; session: TeamWorkshopSession }
  | { action: "HELP"; text: string }
  | { action: "UNKNOWN"; text: string };

export function parseTeamsCommand(value: string): TeamsCommand {
  const text = value.replaceAll("\u00a0", " ").replace(/\s+/g, " ").trim();
  if (!text || /^help\b/i.test(text)) return { action: "HELP" };

  const start = /^start(?:\s+([a-z-]+))?(?:\s*[|:]\s*|\s+)(.+)$/i.exec(text);
  if (start?.[2]) {
    const candidate = (start[1] ?? "").toLowerCase();
    const aliased = EXERCISE_ALIASES[candidate];
    if (aliased) {
      return { action: "START", exercise: aliased, challenge: start[2].trim() };
    }
    const challenge = [start[1], start[2]].filter(Boolean).join(" ").trim();
    return { action: "START", exercise: "BRAINSTORMING", challenge };
  }

  const add = /^add\s+(TW-[A-F0-9-]{36})\s+(.+)$/i.exec(text);
  if (add?.[1] && add[2]) {
    return { action: "ADD", session_id: add[1].toUpperCase(), content: add[2].trim() };
  }
  const control = /^(pass|freeze|close|delete)\s+(TW-[A-F0-9-]{36})$/i.exec(text);
  if (control?.[1] && control[2]) {
    const action = control[1].toLowerCase();
    return {
      action: action === "pass" ? "PASS" : action === "freeze" ? "FREEZE" : action === "delete" ? "DELETE" : "CLOSE",
      session_id: control[2].toUpperCase(),
    };
  }
  return { action: "UNKNOWN" };
}

export const TEAMS_HELP = [
  "◇ MightShape for Teams",
  "Mention the app in a standard team channel; it never passively reads the channel.",
  "Start: `@MightShape start affinity | Map the handoffs in customer onboarding`",
  "Contribute: use **Add my input** on the workshop card. This is required for sealed exercises.",
  "Pass: use **Pass this prompt** or `@MightShape pass TW-…`; no response is invented for you.",
  "Open-session fallback: `@MightShape add TW-… one atomic note`",
  "Initiator controls: `@MightShape freeze TW-…` or `@MightShape close TW-…`",
  "Delete: use **Delete workshop data** or `@MightShape delete TW-…`; remote bot-post cleanup is best effort and partial failures remain retryable.",
  "Team inputs are USER_PROVIDED design material—not HUMAN_INTERVIEW evidence.",
].join("\n");

/** Thin Teams mapping around the platform-neutral WorkshopService. */
export class TeamsWorkshopAdapter {
  constructor(readonly service: WorkshopService) {}

  async assertBound(sessionId: string, invocation: TeamsInvocation): Promise<void> {
    const record = await this.service.get(sessionId);
    const binding = record.binding;
    const baseConversation = invocation.conversation_id.split(";")[0];
    if (
      binding.platform !== "TEAMS" ||
      binding.workspace_ref !== invocation.workspace_id ||
      binding.channel_ref !== invocation.channel_id ||
      binding.conversation_ref?.split(";")[0] !== baseConversation ||
      binding.root_message_ref !== invocation.root_message_id
    ) {
      throw new WorkshopError(
        "This workshop action must be completed in its original Teams channel thread.",
        "CONTEXT_MISMATCH",
      );
    }
  }

  async handle(command: TeamsCommand, invocation: TeamsInvocation): Promise<TeamsCommandResult> {
    if (command.action === "HELP") return { action: "HELP", text: TEAMS_HELP };
    if (command.action === "UNKNOWN") {
      return { action: "UNKNOWN", text: `I couldn't match that command.\n\n${TEAMS_HELP}` };
    }
    if (command.action === "START") {
      const record = await this.service.start({
        platform: "TEAMS",
        workspace_ref: invocation.workspace_id,
        channel_ref: invocation.channel_id,
        conversation_ref: invocation.conversation_id,
        root_message_ref: invocation.root_message_id,
        actor_ref: invocation.actor_id,
        event_id: invocation.event_id,
        exercise: command.exercise,
        challenge: command.challenge,
      });
      return { action: "STARTED", session: record.session };
    }
    if (!SESSION_ID.test(command.session_id)) throw new WorkshopError("Invalid session ID.", "INVALID_SESSION_ID");
    await this.assertBound(command.session_id, invocation);
    if (command.action === "ADD") {
      const existing = await this.service.get(command.session_id);
      if (existing.session.visibility === "SEALED") {
        throw new WorkshopError(
          "Sealed input must use the private Add my input dialog so it is not exposed in the channel.",
          "SEALED_INPUT_REQUIRES_DIALOG",
        );
      }
      const result = await this.service.contribute({
        session_id: command.session_id,
        actor_ref: invocation.actor_id,
        event_id: invocation.event_id,
        content: command.content,
      });
      return {
        action: "CONTRIBUTED",
        session: result.session,
        contribution_id: result.contribution.id,
      };
    }
    if (command.action === "PASS") {
      const record = await this.service.pass({
        session_id: command.session_id,
        actor_ref: invocation.actor_id,
        event_id: invocation.event_id,
      });
      return { action: "PASSED", session: record.session };
    }
    if (command.action === "FREEZE") {
      const record = await this.service.freeze({
        session_id: command.session_id,
        actor_ref: invocation.actor_id,
        event_id: invocation.event_id,
      });
      return { action: "FROZEN", session: record.session };
    }
    if (command.action === "DELETE") {
      const record = await this.service.assertController(command.session_id, invocation.actor_id);
      return { action: "DELETE_REQUESTED", session: record.session };
    }
    const record = await this.service.close({
      session_id: command.session_id,
      actor_ref: invocation.actor_id,
      event_id: invocation.event_id,
    });
    return { action: "CLOSED", session: record.session };
  }

  async contributeFromDialog(
    sessionId: string,
    content: string,
    invocation: TeamsInvocation,
  ): Promise<{ session: TeamWorkshopSession; contribution_id: string }> {
    await this.assertBound(sessionId, invocation);
    const result = await this.service.contribute({
      session_id: sessionId,
      actor_ref: invocation.actor_id,
      event_id: invocation.event_id,
      content,
    });
    return { session: result.session, contribution_id: result.contribution.id };
  }
}

function actionData(action: string, sessionId: string): SubmitData {
  return new SubmitData(action, { session_id: sessionId });
}

export function workshopCard(session: TeamWorkshopSession): IAdaptiveCard {
  const view = workshopPresentation(session);
  const status = `${view.phase} · ${view.participant_count} participant${view.participant_count === 1 ? "" : "s"} · ${view.contribution_count} contribution${view.contribution_count === 1 ? "" : "s"}`;
  const card = new AdaptiveCard(
    new TextBlock(view.headline, {
      size: "Large",
      weight: "Bolder",
      color: "Accent",
      wrap: true,
      style: "heading",
    }),
    new TextBlock(status, { size: "Small", isSubtle: true, wrap: true }),
    new TextBlock(view.body, { wrap: true }),
    new TextBlock(view.prompt ?? "This exercise is no longer collecting input.", {
      weight: "Bolder",
      wrap: true,
      spacing: "Medium",
    }),
    new TextBlock(`Session: ${session.id}`, { size: "Small", isSubtle: true, wrap: true }),
    new TextBlock(
      `Local workshop state is stored until ${session.retention_expires_at.slice(0, 10)}. Channel posts follow Teams retention unless the initiator deletes workshop data; remote cleanup is best effort and any failure remains retryable.`,
      { size: "Small", isSubtle: true, wrap: true },
    ),
  )
    .withVersion("1.5")
    .withFallbackText(`${view.headline}\n${view.body}\n${view.prompt ?? ""}\nSession: ${session.id}`);

  if (session.status === "COLLECTING") {
    card.withActions(
      new SubmitAction()
        .withTitle("Add my input")
        .withData(new OpenDialogData("dc_contribute", { session_id: session.id })),
      new ExecuteAction()
        .withTitle("Pass this prompt")
        .withVerb("dc_pass")
        .withData(actionData("dc_pass", session.id)),
      new ExecuteAction()
        .withTitle("Freeze & synthesize")
        .withVerb("dc_freeze")
        .withData(actionData("dc_freeze", session.id)),
      new ExecuteAction()
        .withTitle("Close")
        .withVerb("dc_close")
        .withData(actionData("dc_close", session.id)),
      new ExecuteAction()
        .withTitle("Delete workshop data")
        .withVerb("dc_delete")
        .withData(actionData("dc_delete", session.id)),
    );
  }
  return card;
}

export function contributionDialogCard(session: TeamWorkshopSession): IAdaptiveCard {
  const prompt = session.prompts.find((item) => item.status === "OPEN")?.prompt ?? "Add one contribution.";
  return new AdaptiveCard(
    new TextBlock("◇ Add your input", {
      size: "Large",
      weight: "Bolder",
      color: "Accent",
      style: "heading",
    }),
    new TextBlock(prompt, { wrap: true }),
    new TextBlock(
      session.visibility === "SEALED"
        ? "Your text is submitted privately and is not revealed until the initiator freezes the set."
        : "Your text will be shared in the workshop thread after submission.",
      { wrap: true, size: "Small", isSubtle: true },
    ),
    new TextInput({
      id: "contribution",
      label: "Your contribution",
      isRequired: true,
      errorMessage: "Add a contribution before submitting.",
      isMultiline: true,
      maxLength: 2_000,
      placeholder: "One atomic idea, observation, assumption, step, or question…",
    }),
  )
    .withActions(
      new SubmitAction()
        .withTitle("Contribute")
        .withData(new SubmitData("dc_contribute", { session_id: session.id })),
    )
    .withVersion("1.5")
    .withFallbackText(`Add one contribution to ${session.id}.`);
}

export function visualCard(visual: RenderedWorkshopVisual): IAdaptiveCard {
  if (visual.png.byteLength > MAX_CARD_IMAGE_BYTES) {
    throw new Error(`Teams visual exceeds ${MAX_CARD_IMAGE_BYTES} bytes.`);
  }
  const imageUrl = `data:image/png;base64,${visual.png.toString("base64")}`;
  return new AdaptiveCard(
    new TextBlock(`◇ ${visual.artifact.title}`, {
      size: "Large",
      weight: "Bolder",
      color: "Accent",
      wrap: true,
      style: "heading",
    }),
    new Image(imageUrl, {
      altText: visual.alt_text,
      size: "Stretch",
    }),
    new TextBlock(visual.artifact.summary, { wrap: true, spacing: "Medium" }),
    new TextBlock("The complete source-linked text alternative follows in the workshop thread.", {
      wrap: true,
      size: "Small",
      isSubtle: true,
    }),
    new TextBlock(
      "Provenance: participant notes are USER_PROVIDED; labels and synthesis are DESIGN_COUNCIL. This workshop is not human research evidence.",
      { wrap: true, size: "Small", isSubtle: true },
    ),
  )
    .withVersion("1.5")
    .withFallbackText(`${visual.alt_text}\n\n${visual.text_summary}`);
}

export function aiCardMessage(card: IAdaptiveCard, fallbackText: string): MessageActivityInput {
  const message = new MessageActivityInput(fallbackText)
    .addCard("adaptive", card)
    .addAiGenerated();
  const bytes = Buffer.byteLength(JSON.stringify(message), "utf8");
  if (bytes > MAX_BOT_ACTIVITY_BYTES) {
    throw new Error(`Teams activity exceeds the ${MAX_BOT_ACTIVITY_BYTES}-byte safe delivery budget.`);
  }
  return message;
}

function stringValue(value: unknown): string {
  return typeof value === "string" ? value.trim() : "";
}

function normalizedInvocation(activity: IMessageActivity): TeamsInvocation {
  const workspace = activity.channelData?.tenant?.id ?? activity.conversation.tenantId ?? "";
  const channel = activity.channelData?.channel?.id ?? "";
  const root = activity.replyToId ?? activity.id;
  if (!workspace || !channel || !activity.conversation.id || !root || !activity.from.id || !activity.id) {
    throw new WorkshopError("This command must be used in a standard Teams channel.", "UNSUPPORTED_CONTEXT");
  }
  if (activity.channelData?.channel?.type && activity.channelData.channel.type !== "standard") {
    throw new WorkshopError("MightShape 1.0.1 supports standard Teams channels only.", "UNSUPPORTED_CHANNEL_TYPE");
  }
  return {
    workspace_id: workspace,
    channel_id: channel,
    conversation_id: activity.conversation.id.split(";")[0] ?? activity.conversation.id,
    root_message_id: root,
    actor_id: activity.from.id,
    event_id: activity.id,
  };
}

function invokeActor(activity: ITaskFetchInvokeActivity | ITaskSubmitInvokeActivity | IAdaptiveCardActionInvokeActivity): string {
  const id = activity.from.id;
  if (!id) throw new WorkshopError("A Teams participant identity is required.", "ACTOR_REQUIRED");
  return id;
}

function normalizedInvokeInvocation(
  activity: ITaskFetchInvokeActivity | ITaskSubmitInvokeActivity | IAdaptiveCardActionInvokeActivity,
): TeamsInvocation {
  const workspace = activity.channelData?.tenant?.id ?? activity.conversation.tenantId ?? "";
  const channel = activity.channelData?.channel?.id ?? "";
  const root = activity.replyToId ?? activity.id;
  if (!workspace || !channel || !activity.conversation.id || !root || !activity.id) {
    throw new WorkshopError("This action must originate in the workshop's Teams channel.", "UNSUPPORTED_CONTEXT");
  }
  if (activity.channelData?.channel?.type && activity.channelData.channel.type !== "standard") {
    throw new WorkshopError("MightShape 1.0.1 supports standard Teams channels only.", "UNSUPPORTED_CHANNEL_TYPE");
  }
  return {
    workspace_id: workspace,
    channel_id: channel,
    conversation_id: activity.conversation.id.split(";")[0] ?? activity.conversation.id,
    root_message_id: root,
    actor_id: invokeActor(activity),
    event_id: activity.id,
  };
}

function sessionIdFrom(value: unknown): string {
  const id = stringValue((value as Record<string, unknown> | undefined)?.session_id).toUpperCase();
  if (!SESSION_ID.test(id)) throw new WorkshopError("A valid workshop session is required.", "INVALID_SESSION_ID");
  return id;
}

function errorText(error: unknown): string {
  if (error instanceof WorkshopError) return error.message;
  return "The workshop action could not be completed. Try again or ask the initiator to check the session.";
}

function adaptiveActionMessage(value: string): {
  statusCode: 200;
  type: "application/vnd.microsoft.activity.message";
  value: string;
} {
  return { statusCode: 200, type: "application/vnd.microsoft.activity.message", value };
}

function teamsOutboundPort(app: App): TeamsOutboundPort {
  return {
    reply: async (conversationId, rootMessageId, message) => {
      const sent = await app.reply(conversationId, rootMessageId, message);
      if (!sent?.id) throw new Error("Teams did not return an activity ID for the bot reply.");
      return { id: String(sent.id) };
    },
    deleteActivity: (conversationId, messageId) => app.api.conversations.deleteActivity(conversationId, messageId),
  };
}

async function postToBoundThread(
  port: TeamsOutboundPort,
  service: WorkshopService,
  sessionId: string,
  id: string,
  kind: OutboundDeliveryKind,
  message: MessageActivityInput | string,
  artifactId: string | null = null,
): Promise<boolean> {
  const record = await service.get(sessionId);
  const conversation = record.binding.conversation_ref;
  const root = record.binding.root_message_ref;
  if (!conversation || !root) throw new Error("Teams workshop thread binding is incomplete.");
  const claim = await service.claimOutboundDelivery(sessionId, {
    id,
    kind,
    conversation_ref: conversation,
    root_message_ref: root,
    artifact_id: artifactId,
  });
  if (!claim.claimed) return claim.receipt.status === "POSTED";
  try {
    const sent = await port.reply(conversation, root, message);
    await service.completeOutboundDelivery(sessionId, id, { message_ref: sent.id });
    return true;
  } catch {
    await service.failOutboundDelivery(sessionId, id, "TEAMS_REPLY_FAILED").catch(() => undefined);
    return false;
  }
}

async function postTeamsTextFallback(
  port: TeamsOutboundPort,
  service: WorkshopService,
  sessionId: string,
  value: string,
  idPrefix: string,
  artifactId: string | null,
): Promise<number> {
  let failures = 0;
  for (const [index, text] of chunkText(value, 7_000).entries()) {
    const delivered = await postToBoundThread(
      port,
      service,
      sessionId,
      `${idPrefix}:text:${index}`,
      "TEXT_FALLBACK",
      `${index === 0 ? "◇ MightShape · accessible text alternative" : `◇ Text alternative · continued ${index + 1}`}\n\n${text}`,
      artifactId,
    );
    if (!delivered) failures += 1;
  }
  return failures;
}

function retrySynthesisCard(sessionId: string, message: string): IAdaptiveCard {
  return new AdaptiveCard(
    new TextBlock("△ Synthesis did not complete", {
      size: "Large",
      weight: "Bolder",
      color: "Attention",
      wrap: true,
      style: "heading",
    }),
    new TextBlock(message, { wrap: true }),
    new TextBlock("The frozen source set is intact. Only the initiator or a delegated facilitator can retry.", {
      wrap: true,
      size: "Small",
      isSubtle: true,
    }),
  )
    .withActions(
      new ExecuteAction()
        .withTitle("Retry synthesis")
        .withVerb("dc_retry")
        .withData(actionData("dc_retry", sessionId)),
      new ExecuteAction()
        .withTitle("Delete workshop data")
        .withVerb("dc_delete")
        .withData(actionData("dc_delete", sessionId)),
    )
    .withVersion("1.5")
    .withFallbackText(`${message}\nThe frozen source set is intact. Retry is available to the facilitator.`);
}

async function sendTeamsRecorded(
  service: WorkshopService,
  record: WorkshopRecord,
  id: string,
  kind: OutboundDeliveryKind,
  producer: () => Promise<{ id: string }>,
): Promise<boolean> {
  const conversation = record.binding.conversation_ref;
  const root = record.binding.root_message_ref;
  if (!conversation || !root) throw new Error("Teams workshop thread binding is incomplete.");
  const claim = await service.claimOutboundDelivery(record.session.id, {
    id,
    kind,
    conversation_ref: conversation,
    root_message_ref: root,
    artifact_id: null,
  });
  if (!claim.claimed) return claim.receipt.status === "POSTED";
  try {
    const sent = await producer();
    await service.completeOutboundDelivery(record.session.id, id, { message_ref: sent.id });
    return true;
  } catch {
    await service.failOutboundDelivery(record.session.id, id, "TEAMS_REPLY_FAILED").catch(() => undefined);
    return false;
  }
}

export async function cleanupTeamsWorkshop(
  port: TeamsOutboundPort,
  service: WorkshopService,
  sessionId: string,
  actorRef: string,
): Promise<{ complete: boolean; failed: number; tracked: number }> {
  const current = await service.assertController(sessionId, actorRef);
  const receipts = current.binding.outbound_deliveries.filter((receipt) => receipt.status !== "DELETED");
  let failed = 0;
  const deletedResources = new Set<string>();
  for (const receipt of receipts) {
    if (!receipt.message_ref) {
      failed += 1;
      await service.markOutboundCleanup(
        sessionId,
        receipt.id,
        "DELETE_FAILED",
        "REMOTE_REFERENCE_UNAVAILABLE",
      );
      continue;
    }
    const key = `${receipt.conversation_ref}\0${receipt.message_ref}`;
    await service.markOutboundCleanup(sessionId, receipt.id, "DELETE_PENDING");
    try {
      if (!deletedResources.has(key)) {
        await port.deleteActivity(receipt.conversation_ref, receipt.message_ref);
        deletedResources.add(key);
      }
      await service.markOutboundCleanup(sessionId, receipt.id, "DELETED");
    } catch {
      failed += 1;
      await service.markOutboundCleanup(sessionId, receipt.id, "DELETE_FAILED", "TEAMS_DELETE_FAILED");
    }
  }
  if (failed > 0) return { complete: false, failed, tracked: receipts.length };
  await service.delete(sessionId, actorRef);
  return { complete: true, failed: 0, tracked: receipts.length };
}

function reviewCard(sessionId: string, message: string, retryDelivery: boolean): IAdaptiveCard {
  const card = new AdaptiveCard(
    new TextBlock("◆ MightShape · Review", {
      size: "Large",
      weight: "Bolder",
      color: retryDelivery ? "Attention" : "Good",
      wrap: true,
      style: "heading",
    }),
    new TextBlock(message, { wrap: true }),
    new TextBlock(
      retryDelivery
        ? "Retry delivery reuses the recorded artifact and never reruns synthesis."
        : "The source-linked PNG and complete text alternative were delivered.",
      { wrap: true, size: "Small", isSubtle: true },
    ),
  );
  const actions: ExecuteAction[] = [];
  if (retryDelivery) {
    actions.push(
      new ExecuteAction()
        .withTitle("Retry delivery")
        .withVerb("dc_retry")
        .withData(actionData("dc_retry", sessionId)),
    );
  }
  actions.push(
    new ExecuteAction()
      .withTitle("Delete workshop data")
      .withVerb("dc_delete")
      .withData(actionData("dc_delete", sessionId)),
  );
  return card.withActions(...actions).withVersion("1.5").withFallbackText(message);
}

export async function deliverTeamsVisual(
  port: TeamsOutboundPort,
  service: WorkshopService,
  record: WorkshopRecord,
  visual: RenderedWorkshopVisual,
): Promise<number> {
  const sessionId = record.session.id;
  const artifactId = visual.artifact_ref.artifact_id;
  const prefix = `teams:${artifactId}`;
  let failures = 0;
  const visualPosted = await postToBoundThread(
    port,
    service,
    sessionId,
    `${prefix}:visual`,
    "VISUAL",
    aiCardMessage(
      visualCard(visual),
      `${visual.alt_text}\nThe complete source-linked text alternative follows in the workshop thread.`,
    ),
    artifactId,
  );
  if (!visualPosted) {
    failures += 1;
    const notice = await postToBoundThread(
      port,
      service,
      sessionId,
      `${prefix}:visual-failure-notice`,
      "STATUS",
      "△ The PNG could not be posted. The complete text alternative follows; the generated artifact remains available for delivery retry without rerunning synthesis.",
      artifactId,
    );
    if (!notice) failures += 1;
  }
  failures += await postTeamsTextFallback(
    port,
    service,
    sessionId,
    visual.text_fallback,
    prefix,
    artifactId,
  );
  const reviewPosted = await postToBoundThread(
    port,
    service,
    sessionId,
    `${prefix}:review-control:${failures > 0 ? "partial" : "complete"}`,
    "CONTROL",
    aiCardMessage(
      reviewCard(
        sessionId,
        visualPosted
          ? "PNG and complete text alternative posted."
          : "Complete text alternative posted; PNG delivery remains retryable.",
        !visualPosted || failures > 0,
      ),
      visualPosted
        ? "Review: PNG and complete text alternative posted."
        : "Review: text alternative posted; PNG delivery remains retryable without rerunning synthesis.",
    ),
    artifactId,
  );
  if (!reviewPosted) failures += 1;
  return failures;
}

function scheduleSynthesis(
  app: App,
  service: WorkshopService,
  sessionId: string,
  retryInput?: ControlInput,
  deliveryOnly = false,
): void {
  const port = teamsOutboundPort(app);
  setImmediate(() => {
    void (async () => {
      try {
        try {
          await postToBoundThread(
            port,
            service,
            sessionId,
            `teams:${deliveryOnly ? "delivery" : "synthesis"}:${retryInput?.event_id ?? "initial"}:progress`,
            "PROGRESS",
            aiCardMessage(
              new AdaptiveCard(
                new TextBlock(
                  deliveryOnly
                    ? "◇ MightShape is retrying delivery of the recorded artifact…"
                    : "◇ MightShape is synthesizing the frozen set…",
                  {
                  weight: "Bolder",
                  wrap: true,
                  },
                ),
                new TextBlock(deliveryOnly
                  ? "The source set, synthesis, and visual remain unchanged."
                  : "The team can keep working while the source-linked visual is rendered.", {
                  wrap: true,
                  size: "Small",
                }),
              ).withVersion("1.5"),
              deliveryOnly
                ? "MightShape is retrying delivery of the existing artifact without rerunning synthesis."
                : "MightShape is synthesizing the frozen contribution set.",
            ),
          );
        } catch {
          // A progress-message failure must not discard an authorized frozen set.
        }
        const loaded = deliveryOnly
          ? await service.loadLatestVisual(retryInput!)
          : retryInput
            ? await service.retrySynthesis(retryInput, "TEAMS")
            : await service.synthesize(sessionId, "TEAMS");
        await deliverTeamsVisual(port, service, loaded.record, loaded.visual);
      } catch (error) {
        try {
          if (error instanceof WorkshopError && error.text_fallback) {
            const record = await service.get(sessionId);
            await postTeamsTextFallback(
              port,
              service,
              sessionId,
              error.text_fallback,
              `teams:failure:${record.session.step_version}`,
              null,
            );
          }
          await postToBoundThread(
            port,
            service,
            sessionId,
            `teams:failure:${(await service.get(sessionId)).session.step_version}:control`,
            "CONTROL",
            aiCardMessage(
              deliveryOnly
                ? reviewCard(
                    sessionId,
                    `Delivery retry did not complete: ${errorText(error)} The recorded artifact remains available.`,
                    true,
                  )
                : retrySynthesisCard(sessionId, errorText(error)),
              deliveryOnly
                ? `Delivery retry did not complete: ${errorText(error)} The recorded artifact remains available; synthesis was not rerun.`
                : `Synthesis did not complete: ${errorText(error)} The frozen contributions remain in project state.`,
            ),
          );
        } catch {
          // The platform SDK logger will retain the original handler failure; do not leak identifiers.
        }
      }
    })();
  });
}

function scheduleThreadMessage(
  app: App,
  service: WorkshopService,
  sessionId: string,
  id: string,
  message: MessageActivityInput | string,
): void {
  const port = teamsOutboundPort(app);
  setImmediate(() => {
    void postToBoundThread(
      port,
      service,
      sessionId,
      id,
      "STATUS",
      message,
    ).catch(() => {
      // The participant still receives the private dialog confirmation; state is not lost.
    });
  });
}

export function createTeamsApp(service?: WorkshopService): App {
  const dataRoot = resolve(process.env.DC_TEAM_DATA_DIR ?? ".data");
  const workshopService = service ?? new WorkshopService(
    new FileWorkshopStore(resolve(dataRoot, "sessions")),
    facilitatorFromEnvironment(),
    dataRoot,
  );
  const adapter = new TeamsWorkshopAdapter(workshopService);
  const app = new App({
    activity: { mentions: { stripText: true } },
  });

  app.on("mention", async ({ activity, send }) => {
    try {
      if (activity.type !== "message") {
        throw new WorkshopError("MightShape commands must be sent as channel messages.", "UNSUPPORTED_CONTEXT");
      }
      const invocation = normalizedInvocation(activity);
      const result = await adapter.handle(parseTeamsCommand(activity.text), invocation);
      if (result.action === "STARTED") {
        await sendTeamsRecorded(
          workshopService,
          await workshopService.get(result.session.id),
          "teams:control:initial",
          "CONTROL",
          () => send(aiCardMessage(workshopCard(result.session), workshopPresentation(result.session).body)),
        );
      } else if (result.action === "CONTRIBUTED") {
        await sendTeamsRecorded(
          workshopService,
          await workshopService.get(result.session.id),
          `teams:${activity.id}:status`,
          "STATUS",
          () => send(
            `✓ ${result.contribution_id} captured as USER_PROVIDED design material. ` +
            `${result.session.contributions.length} contribution(s) are now in the exercise.`,
          ),
        );
      } else if (result.action === "PASSED") {
        await sendTeamsRecorded(
          workshopService,
          await workshopService.get(result.session.id),
          `teams:${activity.id}:status`,
          "STATUS",
          () => send("✓ Pass recorded. Participation is optional, and no response was invented for you."),
        );
      } else if (result.action === "FROZEN") {
        await sendTeamsRecorded(
          workshopService,
          await workshopService.get(result.session.id),
          `teams:${activity.id}:status`,
          "STATUS",
          () => send("✓ Contribution set frozen. AI synthesis has started asynchronously."),
        );
        scheduleSynthesis(app, workshopService, result.session.id);
      } else if (result.action === "CLOSED") {
        await sendTeamsRecorded(
          workshopService,
          await workshopService.get(result.session.id),
          `teams:${activity.id}:status`,
          "STATUS",
          () => send("✓ Workshop closed. Its versioned history remains available until the retention date."),
        );
      } else if (result.action === "DELETE_REQUESTED") {
        const cleanup = await cleanupTeamsWorkshop(
          teamsOutboundPort(app),
          workshopService,
          result.session.id,
          invocation.actor_id,
        );
        await send(
          cleanup.complete
            ? cleanup.tracked
              ? `✓ Best-effort cleanup completed for ${cleanup.tracked} recorded bot post(s); local workshop data was deleted.`
              : "✓ Local workshop data was deleted. This older session had no bot-post receipts, so remote cleanup could not be verified."
            : `△ Partial cleanup: ${cleanup.failed} recorded Teams item(s) could not be confirmed deleted. Local data and retryable receipts were retained. If delivery itself failed, retry delivery first; then use Delete workshop data again.`,
        );
      } else {
        await send(result.text);
      }
    } catch (error) {
      await send(`△ ${errorText(error)}`);
    }
  });

  app.on("dialog.open.dc_contribute", async ({ activity }) => {
    try {
      const sessionId = sessionIdFrom(activity.value.data);
      await adapter.assertBound(sessionId, normalizedInvokeInvocation(activity));
      const record = await workshopService.get(sessionId);
      if (record.binding.platform !== "TEAMS" || record.session.status !== "COLLECTING") {
        return { task: { type: "message", value: "This Teams exercise is not collecting input." } };
      }
      return {
        task: {
          type: "continue",
          value: {
            title: "Add to MightShape",
            height: "medium",
            width: "medium",
            card: {
              contentType: "application/vnd.microsoft.card.adaptive",
              content: contributionDialogCard(record.session),
            },
          },
        },
      };
    } catch (error) {
      return { task: { type: "message", value: errorText(error) } };
    }
  });

  app.on("dialog.submit.dc_contribute", async ({ activity }) => {
    try {
      const data = activity.value.data as Record<string, unknown> | undefined;
      const sessionId = sessionIdFrom(data);
      const result = await adapter.contributeFromDialog(
        sessionId,
        stringValue(data?.contribution),
        normalizedInvokeInvocation(activity),
      );
      const count = result.session.contributions.filter((item) => item.status === "ACTIVE").length;
      if (result.session.visibility === "SEALED") {
        scheduleThreadMessage(
          app,
          workshopService,
          sessionId,
          `teams:${activity.id}:status`,
          `✓ A sealed USER_PROVIDED contribution was received. ${count} contribution(s) are held.`,
        );
      } else {
        const contribution = result.session.contributions.find((item) => item.id === result.contribution_id);
        scheduleThreadMessage(
          app,
          workshopService,
          sessionId,
          `teams:${activity.id}:source`,
          `✓ ${result.contribution_id} · USER_PROVIDED\n${contribution?.content ?? "Contribution captured."}`,
        );
      }
      return { task: { type: "message", value: "Your contribution was added." } };
    } catch (error) {
      return { task: { type: "message", value: errorText(error) } };
    }
  });

  app.on("card.action.dc_freeze", async ({ activity }) => {
    try {
      const sessionId = sessionIdFrom(activity.value.action.data);
      await adapter.handle({ action: "FREEZE", session_id: sessionId }, normalizedInvokeInvocation(activity));
      scheduleSynthesis(app, workshopService, sessionId);
      return adaptiveActionMessage("Contribution set frozen. AI synthesis is running in the workshop thread.");
    } catch (error) {
      return adaptiveActionMessage(errorText(error));
    }
  });

  app.on("card.action.dc_pass", async ({ activity }) => {
    try {
      const sessionId = sessionIdFrom(activity.value.action.data);
      await adapter.handle({ action: "PASS", session_id: sessionId }, normalizedInvokeInvocation(activity));
      scheduleThreadMessage(
        app,
        workshopService,
        sessionId,
        `teams:${activity.id}:status`,
        "◇ A teammate passed this prompt. Participation is optional; no contribution was fabricated for them.",
      );
      return adaptiveActionMessage("Pass recorded. You may still contribute later while the exercise is collecting.");
    } catch (error) {
      return adaptiveActionMessage(errorText(error));
    }
  });

  app.on("card.action.dc_retry", async ({ activity }) => {
    try {
      const sessionId = sessionIdFrom(activity.value.action.data);
      const invocation = normalizedInvokeInvocation(activity);
      await adapter.assertBound(sessionId, invocation);
      const current = await workshopService.assertController(sessionId, invocation.actor_id);
      const deliveryOnly = current.session.status === "REVIEW";
      scheduleSynthesis(app, workshopService, sessionId, {
        session_id: sessionId,
        actor_ref: invocation.actor_id,
        event_id: invocation.event_id,
      }, deliveryOnly);
      return adaptiveActionMessage(
        deliveryOnly
          ? "Authorized delivery retry started. The recorded artifact is reused; synthesis will not run again."
          : "Authorized retry started. The frozen source set remains unchanged.",
      );
    } catch (error) {
      return adaptiveActionMessage(errorText(error));
    }
  });

  app.on("card.action.dc_close", async ({ activity }) => {
    try {
      const sessionId = sessionIdFrom(activity.value.action.data);
      await adapter.handle({ action: "CLOSE", session_id: sessionId }, normalizedInvokeInvocation(activity));
      scheduleThreadMessage(
        app,
        workshopService,
        sessionId,
        `teams:${activity.id}:status`,
        "✓ Workshop closed by its initiator.",
      );
      return adaptiveActionMessage("Workshop closed. Its versioned history is retained.");
    } catch (error) {
      return adaptiveActionMessage(errorText(error));
    }
  });

  app.on("card.action.dc_delete", async ({ activity }) => {
    try {
      const sessionId = sessionIdFrom(activity.value.action.data);
      const invocation = normalizedInvokeInvocation(activity);
      await adapter.assertBound(sessionId, invocation);
      const cleanup = await cleanupTeamsWorkshop(
        teamsOutboundPort(app),
        workshopService,
        sessionId,
        invocation.actor_id,
      );
      return adaptiveActionMessage(
        cleanup.complete
          ? cleanup.tracked
            ? `Best-effort cleanup completed for ${cleanup.tracked} recorded bot post(s); local workshop data was deleted.`
            : "Local workshop data was deleted. This older session had no recorded bot-post receipts, so remote cleanup could not be verified."
          : `Partial cleanup: ${cleanup.failed} recorded Teams item(s) could not be confirmed deleted. Local data and retryable receipts were retained. If delivery itself failed, retry delivery first; then use Delete workshop data again. Deletion is best effort, not a confidentiality guarantee.`,
      );
    } catch (error) {
      return adaptiveActionMessage(errorText(error));
    }
  });

  return app;
}

async function main(): Promise<void> {
  const app = createTeamsApp();
  const port = Number(process.env.TEAMS_PORT ?? process.env.PORT ?? "3978");
  if (!Number.isInteger(port) || port < 1 || port > 65_535) {
    throw new Error("TEAMS_PORT must be a valid TCP port.");
  }
  await app.start(port);
}

const entry = process.argv[1];
if (entry && import.meta.url === pathToFileURL(entry).href) {
  main().catch((error) => {
    process.stderr.write(`MightShape Teams adapter failed: ${error instanceof Error ? error.message : String(error)}\n`);
    process.exitCode = 1;
  });
}

export { EXERCISES };
