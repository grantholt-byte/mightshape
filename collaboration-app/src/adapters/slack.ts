import { resolve } from "node:path";
import { pathToFileURL } from "node:url";
import { App, LogLevel, type Logger } from "@slack/bolt";
import type { KnownBlock, ModalView } from "@slack/types";
import type { WebClient } from "@slack/web-api";
import {
  EXERCISES,
  STARTING_POINTS,
  type Exercise,
  type OutboundDeliveryKind,
  type StartingPoint,
  type TeamWorkshopSession,
  type Visibility,
} from "../core/contracts.js";
import { EXERCISE_DEFINITIONS } from "../core/exercises.js";
import { facilitatorFromEnvironment } from "../core/facilitator.js";
import { WorkshopService } from "../core/service.js";
import { workshopPresentation, WorkshopError } from "../core/session.js";
import { FileWorkshopStore } from "../core/store.js";
import type { WorkshopRecord } from "../core/store.js";
import { chunkText, type RenderedWorkshopVisual } from "../core/visual.js";

const SETUP_CALLBACK = "dc_setup_workshop";
const CONTRIBUTE_CALLBACK = "dc_submit_contribution";
const CONTRIBUTE_ACTION = "dc_contribute";
const PASS_ACTION = "dc_pass";
const FREEZE_ACTION = "dc_freeze";
const RETRY_ACTION = "dc_retry_synthesis";
const CLOSE_ACTION = "dc_close";
const DELETE_ACTION = "dc_delete";

interface SetupMetadata {
  team_id: string;
  channel_id: string;
  initial_challenge: string;
}

interface ContributionMetadata {
  session_id: string;
  team_id: string;
  channel_id: string;
  root_message_ref: string;
}

interface SlackStateValue {
  value?: string;
  selected_option?: { value?: string };
}

type SlackViewState = Record<string, Record<string, SlackStateValue>>;

export interface SlackFileClient {
  files: {
    getUploadURLExternal(args: {
      filename: string;
      length: number;
      alt_text: string;
    }): Promise<{ ok?: boolean; file_id?: string; upload_url?: string; error?: string }>;
    completeUploadExternal(args: {
      files: [{ id: string; title: string }];
      channel_id: string;
      thread_ts: string;
      initial_comment: string;
    }): Promise<{ ok?: boolean; error?: string }>;
  };
}

export interface SlackUploadResult {
  file_id: string;
  upload_url_origin: string;
}

function requiredEnv(name: string): string {
  const value = process.env[name]?.trim();
  if (!value) throw new Error(`${name} is required.`);
  return value;
}

function plain(text: string, max = 3_000) {
  return { type: "plain_text" as const, text: text.slice(0, max), emoji: true };
}

function encodeMetadata(value: SetupMetadata | ContributionMetadata): string {
  return JSON.stringify(value);
}

function parseMetadata<T extends SetupMetadata | ContributionMetadata>(value: string): T {
  const parsed = JSON.parse(value) as unknown;
  if (!parsed || typeof parsed !== "object") throw new Error("Slack modal metadata is invalid.");
  return parsed as T;
}

function selectedValue(state: SlackViewState, block: string, action: string): string {
  return state[block]?.[action]?.selected_option?.value?.trim() ?? "";
}

function inputValue(state: SlackViewState, block: string, action: string): string {
  return state[block]?.[action]?.value?.trim() ?? "";
}

function isExercise(value: string): value is Exercise {
  return (EXERCISES as readonly string[]).includes(value);
}

function isStartingPoint(value: string): value is StartingPoint {
  return (STARTING_POINTS as readonly string[]).includes(value);
}

function isVisibility(value: string): value is Visibility {
  return value === "OPEN" || value === "SEALED";
}

function eventKey(prefix: string, ...parts: Array<string | undefined>): string {
  return ["slack", prefix, ...parts.filter((part): part is string => Boolean(part))].join(":");
}

function actionValue(action: unknown): string {
  if (!action || typeof action !== "object" || !("value" in action)) return "";
  const value = (action as { value?: unknown }).value;
  return typeof value === "string" ? value : "";
}

function actionTimestamp(action: unknown): string | undefined {
  if (!action || typeof action !== "object" || !("action_ts" in action)) return undefined;
  const value = (action as { action_ts?: unknown }).action_ts;
  return typeof value === "string" ? value : undefined;
}

function triggerId(body: unknown): string {
  if (!body || typeof body !== "object" || !("trigger_id" in body)) return "";
  const value = (body as { trigger_id?: unknown }).trigger_id;
  return typeof value === "string" ? value : "";
}

function rootMessageRef(body: unknown): string {
  if (!body || typeof body !== "object") return "";
  const record = body as {
    container?: { message_ts?: unknown; thread_ts?: unknown };
    message?: { ts?: unknown; thread_ts?: unknown };
  };
  for (const value of [
    record.container?.thread_ts,
    record.container?.message_ts,
    record.message?.thread_ts,
    record.message?.ts,
  ]) {
    if (typeof value === "string" && value.trim()) return value.trim();
  }
  return "";
}

function errorMessage(error: unknown): string {
  if (error instanceof WorkshopError) return error.message;
  return "MightShape could not complete that action. The exercise state is preserved; please try again.";
}

function assertSlackChannel(record: WorkshopRecord, teamId: string | undefined, channelId: string | undefined): void {
  if (
    record.binding.platform !== "SLACK" ||
    !teamId ||
    !channelId ||
    record.binding.workspace_ref !== teamId ||
    record.binding.channel_ref !== channelId
  ) {
    throw new WorkshopError(
      "Use this control in the Slack workspace and channel where the exercise started.",
      "SCOPE_MISMATCH",
    );
  }
}

function assertSlackScope(
  record: WorkshopRecord,
  teamId: string | undefined,
  channelId: string | undefined,
  rootRef: string,
): void {
  assertSlackChannel(record, teamId, channelId);
  if (!rootRef || !record.binding.root_message_ref || record.binding.root_message_ref !== rootRef) {
    throw new WorkshopError(
      "Use this control on the original MightShape workshop root message.",
      "SCOPE_MISMATCH",
    );
  }
}

function fallbackText(session: TeamWorkshopSession): string {
  const presentation = workshopPresentation(session);
  return [presentation.headline, presentation.body, presentation.prompt].filter(Boolean).join("\n\n");
}

function startingRootBlocks(challenge: string): KnownBlock[] {
  return [
    { type: "header", text: plain("◇ MightShape · starting exercise", 150) },
    { type: "section", text: plain(`Challenge\n${challenge}`) },
    {
      type: "context",
      elements: [{ type: "mrkdwn", text: "Controls will appear after the workshop is safely bound to this channel." }],
    },
  ];
}

function rootActions(session: TeamWorkshopSession): KnownBlock[] {
  const elements: Array<{
    type: "button";
    action_id: string;
    text: ReturnType<typeof plain>;
    value: string;
    style?: "primary" | "danger";
    confirm?: {
      title: ReturnType<typeof plain>;
      text: ReturnType<typeof plain>;
      confirm: ReturnType<typeof plain>;
      deny: ReturnType<typeof plain>;
    };
  }> = [];
  if (session.status === "COLLECTING") {
    elements.push({
      type: "button",
      action_id: CONTRIBUTE_ACTION,
      text: plain("Add my input", 75),
      value: session.id,
      style: "primary",
    });
    elements.push({
      type: "button",
      action_id: PASS_ACTION,
      text: plain("Pass this prompt", 75),
      value: session.id,
    });
    elements.push({
      type: "button",
      action_id: FREEZE_ACTION,
      text: plain("Freeze & synthesize", 75),
      value: session.id,
      confirm: {
        title: plain("Freeze this round?", 100),
        text: plain("New contributions will stop and sealed inputs will be revealed.", 300),
        confirm: plain("Freeze", 30),
        deny: plain("Keep collecting", 30),
      },
    });
  }
  if (
    session.status === "FROZEN" &&
    session.history.at(-1)?.action === "SYNTHESIS_FAILED" &&
    session.history.at(-1)?.details.retryable === true
  ) {
    elements.push({
      type: "button",
      action_id: RETRY_ACTION,
      text: plain("Retry synthesis", 75),
      value: session.id,
      style: "primary",
    });
  }
  if (session.status === "REVIEW" || session.status === "COMPLETED") {
    elements.push({
      type: "button",
      action_id: RETRY_ACTION,
      text: plain("Retry delivery", 75),
      value: session.id,
    });
  }
  if (session.status !== "CLOSED") {
    elements.push({
      type: "button",
      action_id: CLOSE_ACTION,
      text: plain("Close", 75),
      value: session.id,
      style: "danger",
      confirm: {
        title: plain("Close this exercise?", 100),
        text: plain("This stops participation. Saved workshop history is retained until its retention date.", 300),
        confirm: plain("Close", 30),
        deny: plain("Cancel", 30),
      },
    });
  }
  elements.push({
    type: "button",
    action_id: DELETE_ACTION,
    text: plain("Delete workshop data", 75),
    value: session.id,
    style: "danger",
    confirm: {
      title: plain("Delete workshop data?", 100),
      text: plain("The app will attempt to remove recorded bot posts/files, then local state. Failed remote cleanup remains retryable and is reported truthfully.", 300),
      confirm: plain("Delete", 30),
      deny: plain("Cancel", 30),
    },
  });
  return elements.length ? [{ type: "actions", block_id: `dc_controls_${session.step_version}`, elements }] : [];
}

export function workshopRootBlocks(session: TeamWorkshopSession): KnownBlock[] {
  const definition = EXERCISE_DEFINITIONS[session.exercise];
  const visibility = session.visibility === "SEALED" ? "SEALED · independent inputs" : "OPEN · shared inputs";
  const status = session.status.replaceAll("_", " ");
  const contributionWord = session.contributions.length === 1 ? "contribution" : "contributions";
  const blocks: KnownBlock[] = [
    { type: "header", text: plain(`◇ MightShape · ${definition.label}`, 150) },
    { type: "section", text: plain(`Challenge\n${session.challenge}`) },
    {
      type: "section",
      fields: [
        plain(`Purpose\n${definition.purpose}`, 2_000),
        plain(`Round\n${visibility}\n${status} · ${session.contributions.length} ${contributionWord}`, 2_000),
      ],
    },
  ];
  const openPrompt = session.prompts.find((item) => item.status === "OPEN");
  if (openPrompt) {
    blocks.push(
      { type: "section", text: plain(`Facilitator mindset\n${openPrompt.mindset}`) },
      { type: "section", text: plain(`Your move\n${openPrompt.prompt}`) },
    );
  }
  blocks.push({
    type: "context",
    elements: [
      {
        type: "mrkdwn",
        text: `Inputs are \`USER_PROVIDED\` design material—not human research. The app does not read channel history. Initiators can use *Delete workshop data* or \`/design-think delete ${session.id}\`; remote cleanup is best effort and any failure is retained for retry.`,
      },
    ],
  });
  blocks.push(...rootActions(session));
  return blocks;
}

export function setupWorkshopModal(metadata: SetupMetadata): ModalView {
  const exerciseOptions = EXERCISES.map((exercise) => ({
    text: plain(EXERCISE_DEFINITIONS[exercise].label, 75),
    value: exercise,
  }));
  const startingOptions: Array<{ value: StartingPoint; label: string }> = [
    { value: "EARLY_HUNCH", label: "Early hunch" },
    { value: "GROUNDED_EXPLORATION", label: "Grounded exploration" },
    { value: "FRAMED_CHALLENGE", label: "Framed challenge" },
    { value: "CONCEPT", label: "Established concept" },
    { value: "PROTOTYPE", label: "Prototype" },
    { value: "LIVE", label: "Live product or service" },
    { value: "UNSURE", label: "Not sure yet" },
  ];
  const challengeElement: {
    type: "plain_text_input";
    action_id: string;
    multiline: boolean;
    max_length: number;
    placeholder: ReturnType<typeof plain>;
    initial_value?: string;
  } = {
    type: "plain_text_input",
    action_id: "challenge",
    multiline: true,
    max_length: 2_000,
    placeholder: plain("What are we trying to understand, frame, create, or test?", 150),
  };
  if (metadata.initial_challenge) challengeElement.initial_value = metadata.initial_challenge.slice(0, 2_000);
  return {
    type: "modal",
    callback_id: SETUP_CALLBACK,
    private_metadata: encodeMetadata(metadata),
    title: plain("MightShape", 24),
    submit: plain("Start exercise", 24),
    close: plain("Cancel", 24),
    blocks: [
      {
        type: "section",
        text: {
          type: "mrkdwn",
          text: "One channel member starts the exercise. The AI facilitator explains the immediate purpose, then teammates contribute through a modal.",
        },
      },
      {
        type: "input",
        block_id: "challenge_block",
        label: plain("Design challenge", 2_000),
        element: challengeElement,
      },
      {
        type: "input",
        block_id: "exercise_block",
        label: plain("Exercise", 2_000),
        element: {
          type: "static_select",
          action_id: "exercise",
          initial_option: exerciseOptions[0]!,
          options: exerciseOptions,
        },
      },
      {
        type: "input",
        block_id: "starting_block",
        label: plain("Where is the idea now?", 2_000),
        element: {
          type: "static_select",
          action_id: "starting_point",
          initial_option: { text: plain("Not sure yet", 75), value: "UNSURE" },
          options: startingOptions.map((option) => ({ text: plain(option.label, 75), value: option.value })),
        },
      },
      {
        type: "input",
        block_id: "visibility_block",
        label: plain("Contribution visibility", 2_000),
        hint: plain("Sealed protects independent thinking until the initiator freezes the round.", 2_000),
        element: {
          type: "static_select",
          action_id: "visibility",
          initial_option: { text: plain("Use the exercise default", 75), value: "DEFAULT" },
          options: [
            { text: plain("Use the exercise default", 75), value: "DEFAULT" },
            { text: plain("Sealed until freeze", 75), value: "SEALED" },
            { text: plain("Open in the thread", 75), value: "OPEN" },
          ],
        },
      },
    ],
  };
}

export function contributionModal(
  session: TeamWorkshopSession,
  teamId = "",
  channelId = "",
  rootRef = session.id,
): ModalView {
  const definition = EXERCISE_DEFINITIONS[session.exercise];
  return {
    type: "modal",
    callback_id: CONTRIBUTE_CALLBACK,
    private_metadata: encodeMetadata({
      session_id: session.id,
      team_id: teamId,
      channel_id: channelId,
      root_message_ref: rootRef,
    }),
    title: plain("Add your input", 24),
    submit: plain("Contribute", 24),
    close: plain("Pass", 24),
    blocks: [
      { type: "section", text: plain(definition.purpose) },
      { type: "section", text: plain(`Mindset\n${definition.mindset}`) },
      {
        type: "input",
        block_id: "contribution_block",
        label: plain(definition.prompt, 2_000),
        element: {
          type: "plain_text_input",
          action_id: "contribution",
          multiline: true,
          max_length: 2_000,
          placeholder: plain("One atomic note is enough. You can contribute again.", 150),
        },
      },
    ],
  };
}

async function postEphemeral(
  client: WebClient,
  channel: string,
  user: string,
  text: string,
): Promise<void> {
  await client.chat.postEphemeral({ channel, user, text, parse: "none", link_names: false });
}

async function updateRoot(client: WebClient, session: TeamWorkshopSession, channel: string, root: string): Promise<void> {
  await client.chat.update({
    channel,
    ts: root,
    text: fallbackText(session),
    blocks: workshopRootBlocks(session),
    parse: "none",
    link_names: false,
  });
}

function revealMessages(session: TeamWorkshopSession): Array<{ text: string; blocks: KnownBlock[] }> {
  const visible = session.contributions.filter((item) => item.status === "ACTIVE");
  const groups: typeof visible[] = [];
  for (let index = 0; index < visible.length; index += 20) groups.push(visible.slice(index, index + 20));
  return groups.map((group, groupIndex) => {
    const heading = groupIndex === 0 ? "Frozen contribution set" : `Frozen contribution set · continued ${groupIndex + 1}`;
    const blocks: KnownBlock[] = [{ type: "header", text: plain(heading, 150) }];
    for (const contribution of group) {
      blocks.push({
        type: "section",
        text: plain(`${contribution.id} · USER_PROVIDED\n${contribution.content}`),
      });
    }
    const text = [heading, ...group.map((item) => `${item.id} · USER_PROVIDED\n${item.content}`)].join("\n\n");
    return { text, blocks };
  });
}

async function uploadBytes(
  uploadUrl: string,
  png: Buffer,
  fetchImpl: typeof fetch,
  attempts = 3,
): Promise<void> {
  let lastError: Error | null = null;
  for (let attempt = 1; attempt <= attempts; attempt += 1) {
    try {
      const response = await fetchImpl(uploadUrl, {
        method: "POST",
        headers: { "Content-Type": "application/octet-stream" },
        body: new Uint8Array(png),
      });
      if (response.ok) return;
      lastError = new Error(`Slack external file upload returned ${response.status}.`);
      if (response.status < 500 && response.status !== 429) break;
    } catch (error) {
      lastError = error instanceof Error ? error : new Error("Slack external file upload failed.");
    }
    if (attempt < attempts) await new Promise((accept) => setTimeout(accept, 150 * attempt));
  }
  throw lastError ?? new Error("Slack external file upload failed.");
}

/**
 * Upload a rendered PNG using Slack's current three-step external upload flow.
 * This intentionally never calls the retired files.upload method.
 */
export async function uploadSlackPng(
  client: SlackFileClient,
  visual: RenderedWorkshopVisual,
  channel: string,
  threadTs: string,
  fetchImpl: typeof fetch = fetch,
): Promise<SlackUploadResult> {
  const filename = `${visual.artifact.artifact_type.toLowerCase().replaceAll("_", "-")}-${visual.artifact.id.toLowerCase()}.png`;
  const ticket = await client.files.getUploadURLExternal({
    filename,
    length: visual.png.byteLength,
    alt_text: visual.alt_text.slice(0, 2_000),
  });
  if (!ticket.ok || !ticket.file_id || !ticket.upload_url) {
    throw new Error(`Slack did not issue an external upload URL${ticket.error ? `: ${ticket.error}` : "."}`);
  }
  await uploadBytes(ticket.upload_url, visual.png, fetchImpl);
  const completed = await client.files.completeUploadExternal({
    files: [{ id: ticket.file_id, title: visual.artifact.title.slice(0, 255) }],
    channel_id: channel,
    thread_ts: threadTs,
    initial_comment: "◇ MightShape visual · source-linked workshop artifact. A text alternative follows.",
  });
  if (!completed.ok) {
    throw new Error(`Slack did not complete the external upload${completed.error ? `: ${completed.error}` : "."}`);
  }
  return { file_id: ticket.file_id, upload_url_origin: new URL(ticket.upload_url).origin };
}

async function postFallbackText(
  client: WebClient,
  channel: string,
  threadTs: string,
  value: string,
): Promise<void> {
  for (const [index, text] of chunkText(value, 35_000).entries()) {
    await client.chat.postMessage({
      channel,
      thread_ts: threadTs,
      text: index === 0 ? text : `MightShape text alternative · continued ${index + 1}\n\n${text}`,
      mrkdwn: false,
      link_names: false,
      unfurl_links: false,
      unfurl_media: false,
    });
  }
}

type SlackPostArguments = Parameters<WebClient["chat"]["postMessage"]>[0];

async function postRecordedSlackMessage(input: {
  service: WorkshopService;
  client: WebClient;
  record: WorkshopRecord;
  id: string;
  kind: OutboundDeliveryKind;
  args: SlackPostArguments;
  artifact_id?: string | null;
}): Promise<boolean> {
  const claim = await input.service.claimOutboundDelivery(input.record.session.id, {
    id: input.id,
    kind: input.kind,
    conversation_ref: input.record.binding.channel_ref,
    root_message_ref: input.record.binding.root_message_ref,
    artifact_id: input.artifact_id ?? null,
  });
  if (!claim.claimed) return claim.receipt.status === "POSTED";
  try {
    const posted = await input.client.chat.postMessage(input.args);
    if (posted.ok === false || !posted.ts) throw new Error("Slack did not return a posted message timestamp.");
    await input.service.completeOutboundDelivery(input.record.session.id, input.id, {
      message_ref: posted.ts,
    });
    return true;
  } catch {
    await input.service.failOutboundDelivery(input.record.session.id, input.id, "SLACK_MESSAGE_FAILED").catch(() => undefined);
    return false;
  }
}

async function postRecordedTextAlternative(
  service: WorkshopService,
  client: WebClient,
  record: WorkshopRecord,
  visual: RenderedWorkshopVisual,
): Promise<number> {
  const value = `MightShape visual · text alternative\n${visual.artifact.title}\n\n${visual.text_fallback}`;
  let failures = 0;
  for (const [index, text] of chunkText(value, 35_000).entries()) {
    const delivered = await postRecordedSlackMessage({
      service,
      client,
      record,
      id: `slack:${visual.artifact_ref.artifact_id}:text:${index}`,
      kind: "TEXT_FALLBACK",
      artifact_id: visual.artifact_ref.artifact_id,
      args: {
        channel: record.binding.channel_ref,
        thread_ts: record.binding.root_message_ref!,
        text: index === 0 ? text : `MightShape text alternative · continued ${index + 1}\n\n${text}`,
        mrkdwn: false,
        link_names: false,
        unfurl_links: false,
        unfurl_media: false,
      },
    });
    if (!delivered) failures += 1;
  }
  return failures;
}

async function uploadRecordedSlackVisual(input: {
  service: WorkshopService;
  client: WebClient;
  record: WorkshopRecord;
  visual: RenderedWorkshopVisual;
  fetch_impl?: typeof fetch;
}): Promise<number> {
  const id = `slack:${input.visual.artifact_ref.artifact_id}:visual`;
  const claim = await input.service.claimOutboundDelivery(input.record.session.id, {
    id,
    kind: "VISUAL",
    conversation_ref: input.record.binding.channel_ref,
    root_message_ref: input.record.binding.root_message_ref,
    artifact_id: input.visual.artifact_ref.artifact_id,
  });
  if (!claim.claimed) return claim.receipt.status === "POSTED" ? 0 : 1;
  try {
    const uploaded = await uploadSlackPng(
      input.client,
      input.visual,
      input.record.binding.channel_ref,
      input.record.binding.root_message_ref!,
      input.fetch_impl ?? fetch,
    );
    await input.service.completeOutboundDelivery(input.record.session.id, id, {
      file_ref: uploaded.file_id,
    });
    return 0;
  } catch {
    await input.service.failOutboundDelivery(input.record.session.id, id, "SLACK_VISUAL_FAILED").catch(() => undefined);
    return 1;
  }
}

async function deliverSlackVisual(input: {
  service: WorkshopService;
  client: WebClient;
  record: WorkshopRecord;
  visual: RenderedWorkshopVisual;
  fetch_impl?: typeof fetch;
}): Promise<number> {
  const textFailures = await postRecordedTextAlternative(input.service, input.client, input.record, input.visual);
  const imageFailures = await uploadRecordedSlackVisual(input);
  return textFailures + imageFailures;
}

async function deliverFrozenSlackCheckpoints(
  service: WorkshopService,
  client: WebClient,
  record: WorkshopRecord,
): Promise<number> {
  let failures = 0;
  if (record.session.visibility === "OPEN") {
    for (const contribution of record.session.contributions.filter((item) => item.status === "ACTIVE")) {
      const delivered = await postRecordedSlackMessage({
        service,
        client,
        record,
        id: `slack:contribution:${contribution.id}`,
        kind: "SOURCE_SET",
        args: {
          channel: record.binding.channel_ref,
          thread_ts: record.binding.root_message_ref!,
          text: `${contribution.id} · USER_PROVIDED\n${contribution.content}`,
          blocks: [{ type: "section", text: plain(`${contribution.id} · USER_PROVIDED\n${contribution.content}`) }],
          mrkdwn: false,
          link_names: false,
        },
      });
      if (!delivered) failures += 1;
    }
  } else {
    for (const [index, message] of revealMessages(record.session).entries()) {
      const delivered = await postRecordedSlackMessage({
        service,
        client,
        record,
        id: `slack:frozen-source:${index}`,
        kind: "SOURCE_SET",
        args: {
          channel: record.binding.channel_ref,
          thread_ts: record.binding.root_message_ref!,
          text: message.text,
          blocks: message.blocks,
          mrkdwn: false,
          link_names: false,
        },
      });
      if (!delivered) failures += 1;
    }
  }
  const progress = await postRecordedSlackMessage({
    service,
    client,
    record,
    id: "slack:synthesis-checkpoint",
    kind: "PROGRESS",
    args: {
      channel: record.binding.channel_ref,
      thread_ts: record.binding.root_message_ref!,
      text: "The contribution set is frozen. The disclosed AI facilitator preserves source links and outliers during synthesis.",
      mrkdwn: false,
      link_names: false,
    },
  });
  if (!progress) failures += 1;
  return failures;
}

export async function freezeAndPublishSlack(input: {
  service: WorkshopService;
  client: WebClient;
  session_id: string;
  actor_ref: string;
  event_id: string;
  logger?: Pick<Logger, "error">;
  fetch_impl?: typeof fetch;
}): Promise<void> {
  const frozen = await input.service.freeze({
    session_id: input.session_id,
    actor_ref: input.actor_ref,
    event_id: input.event_id,
  });
  const channel = frozen.binding.channel_ref;
  const root = frozen.binding.root_message_ref;
  if (!root) throw new Error("The Slack workshop has no root message binding.");
  let failures = 0;
  try {
    await updateRoot(input.client, frozen.session, channel, root);
  } catch {
    failures += 1;
  }
  failures += await deliverFrozenSlackCheckpoints(input.service, input.client, frozen);
  const result = await input.service.synthesize(input.session_id, "SLACK");
  try {
    await updateRoot(input.client, result.record.session, channel, root);
  } catch {
    failures += 1;
  }
  failures += await deliverSlackVisual({
    service: input.service,
    client: input.client,
    record: result.record,
    visual: result.visual,
    ...(input.fetch_impl ? { fetch_impl: input.fetch_impl } : {}),
  });
  if (failures > 0) {
    throw new WorkshopError(
      `Synthesis completed, but ${failures} Slack delivery item(s) remain retryable. The existing artifact will be reused.`,
      "DELIVERY_PARTIAL",
    );
  }
}

export async function retryAndPublishSlack(input: {
  service: WorkshopService;
  client: WebClient;
  session_id: string;
  actor_ref: string;
  event_id: string;
  fetch_impl?: typeof fetch;
}): Promise<void> {
  const current = await input.service.assertController(input.session_id, input.actor_ref);
  const retryInput = {
    session_id: input.session_id,
    actor_ref: input.actor_ref,
    event_id: input.event_id,
  };
  const result = current.session.status === "REVIEW" || current.session.status === "COMPLETED"
    ? await input.service.loadLatestVisual(retryInput)
    : await input.service.retrySynthesis(retryInput, "SLACK");
  const channel = result.record.binding.channel_ref;
  const root = result.record.binding.root_message_ref;
  if (!root) throw new Error("The Slack workshop has no root message binding.");
  let failures = 0;
  try {
    await updateRoot(input.client, result.record.session, channel, root);
  } catch {
    failures += 1;
  }
  failures += await deliverFrozenSlackCheckpoints(input.service, input.client, result.record);
  failures += await deliverSlackVisual({
    service: input.service,
    client: input.client,
    record: result.record,
    visual: result.visual,
    ...(input.fetch_impl ? { fetch_impl: input.fetch_impl } : {}),
  });
  if (failures > 0) {
    throw new WorkshopError(
      `Delivery remains partial (${failures} Slack item(s)). The existing artifact and receipts are retained; synthesis was not rerun.`,
      "DELIVERY_PARTIAL",
    );
  }
}

export interface SlackCleanupResult {
  complete: boolean;
  deleted_remote_items: number;
  failed_items: number;
  local_deleted: boolean;
}

async function ensureSlackRoot(
  service: WorkshopService,
  client: WebClient,
  record: WorkshopRecord,
): Promise<WorkshopRecord> {
  const knownRoot = record.binding.root_message_ref;
  const claim = await service.claimOutboundDelivery(record.session.id, {
    id: "slack:root",
    kind: "ROOT",
    conversation_ref: record.binding.channel_ref,
    root_message_ref: knownRoot,
    artifact_id: null,
  });
  if (knownRoot) {
    if (claim.receipt.status !== "POSTED") {
      await service.completeOutboundDelivery(record.session.id, "slack:root", {
        message_ref: knownRoot,
        root_message_ref: knownRoot,
      });
    }
    return service.get(record.session.id);
  }
  if (!claim.claimed) {
    if (claim.receipt.status === "POSTED" && claim.receipt.message_ref) {
      return service.bindRoot(
        record.session.id,
        record.binding.channel_ref,
        claim.receipt.message_ref,
      );
    }
    throw new WorkshopError(
      "This exercise is already being started. Its root message will appear shortly.",
      "DELIVERY_IN_PROGRESS",
    );
  }
  try {
    const posted = await client.chat.postMessage({
      channel: record.binding.channel_ref,
      text: `MightShape is starting an exercise for: ${record.session.challenge}`,
      blocks: startingRootBlocks(record.session.challenge),
      mrkdwn: false,
      link_names: false,
    });
    if (posted.ok === false || !posted.ts) throw new Error("Slack did not return a root message timestamp.");
    await service.completeOutboundDelivery(record.session.id, "slack:root", {
      message_ref: posted.ts,
      root_message_ref: posted.ts,
    });
    return service.bindRoot(record.session.id, record.binding.channel_ref, posted.ts);
  } catch (error) {
    await service.failOutboundDelivery(record.session.id, "slack:root", "SLACK_ROOT_FAILED").catch(() => undefined);
    throw error;
  }
}

function slackErrorCode(error: unknown): string {
  if (!error || typeof error !== "object") return "SLACK_DELETE_FAILED";
  const data = (error as { data?: { error?: unknown }; code?: unknown }).data;
  if (typeof data?.error === "string") return data.error;
  const code = (error as { code?: unknown }).code;
  return typeof code === "string" ? code : "SLACK_DELETE_FAILED";
}

function alreadyAbsent(code: string): boolean {
  return ["message_not_found", "file_not_found", "already_deleted"].includes(code);
}

/** Best-effort remote cleanup. Local state is removed only after every receipt is resolved. */
export async function cleanupSlackWorkshop(input: {
  service: WorkshopService;
  client: WebClient;
  session_id: string;
  actor_ref: string;
}): Promise<SlackCleanupResult> {
  let record = await input.service.assertController(input.session_id, input.actor_ref);
  const channel = record.binding.channel_ref;
  const root = record.binding.root_message_ref;
  if (!root) throw new WorkshopError("The Slack workshop has no root message binding.", "BINDING_REQUIRED");

  let rootReceipt = record.binding.outbound_deliveries.find((item) => item.id === "slack:root");
  if (!rootReceipt) {
    const claim = await input.service.claimOutboundDelivery(input.session_id, {
      id: "slack:root",
      kind: "ROOT",
      conversation_ref: channel,
      root_message_ref: root,
      artifact_id: null,
    });
    rootReceipt = claim.receipt;
  }
  if (rootReceipt.status !== "POSTED" && rootReceipt.status !== "DELETED") {
    record = await input.service.completeOutboundDelivery(input.session_id, "slack:root", {
      message_ref: root,
      root_message_ref: root,
    });
  } else {
    record = await input.service.get(input.session_id);
  }

  let deletedRemote = 0;
  let failures = 0;
  const deleted = new Set<string>();
  const receipts = record.binding.outbound_deliveries
    .filter((item) => item.status !== "DELETED")
    .sort((left, right) => Number(left.kind === "ROOT") - Number(right.kind === "ROOT"));

  const deleteReceipt = async (receipt: (typeof receipts)[number]): Promise<boolean> => {
    if (!receipt.message_ref && !receipt.file_ref) {
      await input.service.markOutboundCleanup(
        input.session_id,
        receipt.id,
        "DELETE_FAILED",
        "REMOTE_REFERENCE_UNAVAILABLE",
      );
      return false;
    }
    await input.service.markOutboundCleanup(input.session_id, receipt.id, "DELETE_PENDING");
    try {
      if (receipt.file_ref) {
        const key = `file:${receipt.file_ref}`;
        if (!deleted.has(key)) {
          const response = await input.client.files.delete({ file: receipt.file_ref });
          if (response.ok === false && !alreadyAbsent(String(response.error ?? ""))) {
            throw new Error(String(response.error ?? "SLACK_FILE_DELETE_FAILED"));
          }
          deleted.add(key);
          deletedRemote += 1;
        }
      }
      if (receipt.message_ref) {
        const key = `message:${receipt.conversation_ref}:${receipt.message_ref}`;
        if (!deleted.has(key)) {
          const response = await input.client.chat.delete({
            channel: receipt.conversation_ref,
            ts: receipt.message_ref,
          });
          if (response.ok === false && !alreadyAbsent(String(response.error ?? ""))) {
            throw new Error(String(response.error ?? "SLACK_MESSAGE_DELETE_FAILED"));
          }
          deleted.add(key);
          deletedRemote += 1;
        }
      }
      await input.service.markOutboundCleanup(input.session_id, receipt.id, "DELETED");
      return true;
    } catch (error) {
      const code = slackErrorCode(error);
      if (alreadyAbsent(code)) {
        await input.service.markOutboundCleanup(input.session_id, receipt.id, "DELETED");
        return true;
      }
      await input.service.markOutboundCleanup(input.session_id, receipt.id, "DELETE_FAILED", code);
      return false;
    }
  };

  for (const receipt of receipts.filter((item) => item.kind !== "ROOT")) {
    if (!(await deleteReceipt(receipt))) failures += 1;
  }
  // Keep the root and its visible retry/delete controls until every child item
  // is confirmed gone or already absent.
  if (failures === 0) {
    for (const receipt of receipts.filter((item) => item.kind === "ROOT")) {
      if (!(await deleteReceipt(receipt))) failures += 1;
    }
  }
  if (failures > 0) {
    return {
      complete: false,
      deleted_remote_items: deletedRemote,
      failed_items: failures,
      local_deleted: false,
    };
  }
  const localDeleted = await input.service.delete(input.session_id, input.actor_ref);
  return {
    complete: true,
    deleted_remote_items: deletedRemote,
    failed_items: 0,
    local_deleted: localDeleted,
  };
}

export function registerSlackHandlers(app: App, service: WorkshopService): void {
  app.command("/design-think", async ({ command, ack, client, logger }) => {
    await ack();
    try {
      const deleteMatch = command.text.trim().match(/^delete\s+(TW-[A-F0-9-]{36})$/i);
      if (deleteMatch?.[1]) {
        const sessionId = deleteMatch[1].toUpperCase();
        const current = await service.get(sessionId);
        assertSlackChannel(current, command.team_id, command.channel_id);
        const outcome = await cleanupSlackWorkshop({
          service,
          client,
          session_id: sessionId,
          actor_ref: command.user_id,
        });
        await postEphemeral(
          client,
          command.channel_id,
          command.user_id,
          outcome.complete
            ? `Workshop ${sessionId} was deleted. Recorded bot posts/files and local state were removed.`
            : `Remote cleanup is incomplete for ${sessionId}: ${outcome.failed_items} item(s) remain retryable. Local workshop state was retained. Run \`/design-think delete ${sessionId}\` again.`,
        );
        return;
      }
      await client.views.open({
        trigger_id: command.trigger_id,
        view: setupWorkshopModal({
          team_id: command.team_id,
          channel_id: command.channel_id,
          initial_challenge: command.text.trim().slice(0, 2_000),
        }),
      });
    } catch (error) {
      logger.error(error);
      await postEphemeral(client, command.channel_id, command.user_id, errorMessage(error));
    }
  });

  app.view(SETUP_CALLBACK, async ({ ack, body, view, client, logger }) => {
    await ack();
    try {
      const metadata = parseMetadata<SetupMetadata>(view.private_metadata);
      const state = view.state.values as SlackViewState;
      const challenge = inputValue(state, "challenge_block", "challenge");
      const exerciseValue = selectedValue(state, "exercise_block", "exercise");
      const startingValue = selectedValue(state, "starting_block", "starting_point");
      const visibilityValue = selectedValue(state, "visibility_block", "visibility");
      if (!isExercise(exerciseValue) || !isStartingPoint(startingValue)) {
        throw new Error("Slack returned an unsupported workshop option.");
      }
      const visibility = isVisibility(visibilityValue) ? visibilityValue : undefined;
      const record = await service.start({
        platform: "SLACK",
        workspace_ref: metadata.team_id,
        channel_ref: metadata.channel_id,
        actor_ref: body.user.id,
        challenge,
        exercise: exerciseValue,
        starting_point: startingValue,
        ...(visibility ? { visibility } : {}),
        facilitator_level: "NOVICE_ASSISTED",
        event_id: eventKey("setup", view.id),
        retention_days: Number(process.env.DC_RETENTION_DAYS ?? "30"),
      });
      const bound = await ensureSlackRoot(service, client, record);
      if (!bound.binding.root_message_ref) throw new Error("Slack did not persist the root message timestamp.");
      await updateRoot(client, bound.session, metadata.channel_id, bound.binding.root_message_ref);
      await postEphemeral(
        client,
        metadata.channel_id,
        body.user.id,
        "Exercise started. Teammates can participate from the root message; keep discussion in its thread.",
      );
    } catch (error) {
      logger.error(error);
      const metadata = parseMetadata<SetupMetadata>(view.private_metadata);
      await postEphemeral(client, metadata.channel_id, body.user.id, errorMessage(error));
    }
  });

  app.action(CONTRIBUTE_ACTION, async ({ ack, body, action, client, logger }) => {
    await ack();
    const sessionId = actionValue(action);
    try {
      const record = await service.get(sessionId);
      assertSlackScope(record, body.team?.id, body.channel?.id, rootMessageRef(body));
      await client.views.open({
        trigger_id: triggerId(body),
        view: contributionModal(
          record.session,
          record.binding.workspace_ref,
          record.binding.channel_ref,
          record.binding.root_message_ref ?? "",
        ),
      });
    } catch (error) {
      logger.error(error);
      const channel = body.channel?.id;
      if (channel) await postEphemeral(client, channel, body.user.id, errorMessage(error));
    }
  });

  app.view(CONTRIBUTE_CALLBACK, async ({ ack, body, view, client, logger }) => {
    await ack();
    const metadata = parseMetadata<ContributionMetadata>(view.private_metadata);
    try {
      const current = await service.get(metadata.session_id);
      assertSlackScope(
        current,
        body.team?.id ?? metadata.team_id,
        metadata.channel_id,
        metadata.root_message_ref,
      );
      const content = inputValue(view.state.values as SlackViewState, "contribution_block", "contribution");
      const result = await service.contribute({
        session_id: metadata.session_id,
        actor_ref: body.user.id,
        content,
        event_id: eventKey("contribution", view.id),
      });
      const channel = result.binding.channel_ref;
      const root = result.binding.root_message_ref;
      if (!root) throw new Error("The Slack workshop has no root message binding.");
      if (result.session.visibility === "OPEN") {
        await postRecordedSlackMessage({
          service,
          client,
          record: result,
          id: `slack:contribution:${result.contribution.id}`,
          kind: "SOURCE_SET",
          args: {
            channel,
            thread_ts: root,
            text: `${result.contribution.id} · USER_PROVIDED\n${result.contribution.content}`,
            blocks: [
              {
                type: "section",
                text: plain(`${result.contribution.id} · USER_PROVIDED\n${result.contribution.content}`),
              },
            ],
            mrkdwn: false,
            link_names: false,
          },
        });
      } else {
        await postEphemeral(
          client,
          channel,
          body.user.id,
          `${result.contribution.id} received and sealed. Only the contribution count is shared until freeze.`,
        );
      }
      await updateRoot(client, result.session, channel, root);
    } catch (error) {
      logger.error(error);
      try {
        const record = await service.get(metadata.session_id);
        await postEphemeral(client, record.binding.channel_ref, body.user.id, errorMessage(error));
      } catch (nested) {
        logger.error(nested);
      }
    }
  });

  app.action(PASS_ACTION, async ({ ack, body, action, client, logger }) => {
    await ack();
    const sessionId = actionValue(action);
    try {
      const current = await service.get(sessionId);
      assertSlackScope(current, body.team?.id, body.channel?.id, rootMessageRef(body));
      const record = await service.pass({
        session_id: sessionId,
        actor_ref: body.user.id,
        event_id: eventKey("pass", actionTimestamp(action), triggerId(body)),
      });
      if (record.binding.root_message_ref) {
        await updateRoot(client, record.session, record.binding.channel_ref, record.binding.root_message_ref);
      }
      await postEphemeral(
        client,
        record.binding.channel_ref,
        body.user.id,
        "Pass recorded. The facilitator will not invent a response on your behalf.",
      );
    } catch (error) {
      logger.error(error);
      try {
        const record = await service.get(sessionId);
        if (record.binding.root_message_ref) {
          await updateRoot(client, record.session, record.binding.channel_ref, record.binding.root_message_ref);
        }
        await postEphemeral(client, record.binding.channel_ref, body.user.id, errorMessage(error));
      } catch (nested) {
        logger.error(nested);
      }
    }
  });

  app.action(FREEZE_ACTION, async ({ ack, body, action, client, logger }) => {
    await ack();
    const sessionId = actionValue(action);
    const eventId = eventKey("freeze", actionTimestamp(action), triggerId(body));
    void (async () => {
      const current = await service.get(sessionId);
      assertSlackScope(current, body.team?.id, body.channel?.id, rootMessageRef(body));
      await freezeAndPublishSlack({
        service,
        client,
        session_id: sessionId,
        actor_ref: body.user.id,
        event_id: eventId,
        logger,
      });
    })().catch(async (error: unknown) => {
      logger.error(error);
      try {
        const record = await service.get(sessionId);
        if (record.binding.root_message_ref) {
          await updateRoot(client, record.session, record.binding.channel_ref, record.binding.root_message_ref);
          if (error instanceof WorkshopError && error.text_fallback) {
            await postFallbackText(
              client,
              record.binding.channel_ref,
              record.binding.root_message_ref,
              error.text_fallback,
            );
          }
        }
        await postEphemeral(client, record.binding.channel_ref, body.user.id, errorMessage(error));
      } catch (nested) {
        logger.error(nested);
      }
    });
  });

  app.action(RETRY_ACTION, async ({ ack, body, action, client, logger }) => {
    await ack();
    const sessionId = actionValue(action);
    void (async () => {
      const current = await service.get(sessionId);
      assertSlackScope(current, body.team?.id, body.channel?.id, rootMessageRef(body));
      await retryAndPublishSlack({
        service,
        client,
        session_id: sessionId,
        actor_ref: body.user.id,
        event_id: eventKey("retry", actionTimestamp(action), triggerId(body)),
      });
    })().catch(async (error: unknown) => {
      logger.error(error);
      try {
        const record = await service.get(sessionId);
        if (record.binding.root_message_ref) {
          await updateRoot(client, record.session, record.binding.channel_ref, record.binding.root_message_ref);
          if (error instanceof WorkshopError && error.text_fallback) {
            await postFallbackText(
              client,
              record.binding.channel_ref,
              record.binding.root_message_ref,
              error.text_fallback,
            );
          }
        }
        await postEphemeral(client, record.binding.channel_ref, body.user.id, errorMessage(error));
      } catch (nested) {
        logger.error(nested);
      }
    });
  });

  app.action(CLOSE_ACTION, async ({ ack, body, action, client, logger }) => {
    await ack();
    const sessionId = actionValue(action);
    try {
      const current = await service.get(sessionId);
      assertSlackScope(current, body.team?.id, body.channel?.id, rootMessageRef(body));
      const record = await service.close({
        session_id: sessionId,
        actor_ref: body.user.id,
        event_id: eventKey("close", actionTimestamp(action), triggerId(body)),
      });
      if (record.binding.root_message_ref) {
        await updateRoot(client, record.session, record.binding.channel_ref, record.binding.root_message_ref);
      }
      await postEphemeral(client, record.binding.channel_ref, body.user.id, "Exercise closed.");
    } catch (error) {
      logger.error(error);
      try {
        const record = await service.get(sessionId);
        await postEphemeral(client, record.binding.channel_ref, body.user.id, errorMessage(error));
      } catch (nested) {
        logger.error(nested);
      }
    }
  });

  app.action(DELETE_ACTION, async ({ ack, body, action, client, logger }) => {
    await ack();
    const sessionId = actionValue(action);
    try {
      const current = await service.get(sessionId);
      assertSlackScope(current, body.team?.id, body.channel?.id, rootMessageRef(body));
      const channel = current.binding.channel_ref;
      const outcome = await cleanupSlackWorkshop({
        service,
        client,
        session_id: sessionId,
        actor_ref: body.user.id,
      });
      await postEphemeral(
        client,
        channel,
        body.user.id,
        outcome.complete
          ? "Workshop data was deleted. Recorded bot posts/files and local state were removed."
          : `Remote cleanup is incomplete: ${outcome.failed_items} item(s) remain retryable. Local workshop state was retained. Use \`/design-think delete ${sessionId}\` to retry.`,
      );
    } catch (error) {
      logger.error(error);
      try {
        const current = await service.get(sessionId);
        await postEphemeral(client, current.binding.channel_ref, body.user.id, errorMessage(error));
      } catch (nested) {
        logger.error(nested);
      }
    }
  });
}

export async function startSlackApp(): Promise<void> {
  const dataRoot = resolve(process.env.DC_TEAM_DATA_DIR ?? ".data");
  const app = new App({
    token: requiredEnv("SLACK_BOT_TOKEN"),
    appToken: requiredEnv("SLACK_APP_TOKEN"),
    socketMode: true,
    // Bolt DEBUG logs can include interaction payloads; keep participant text out of default logs.
    logLevel: LogLevel.INFO,
  });
  const service = new WorkshopService(
    new FileWorkshopStore(resolve(dataRoot, "sessions")),
    facilitatorFromEnvironment(),
    dataRoot,
  );
  registerSlackHandlers(app, service);
  await app.start();
  console.log("◇ MightShape Slack adapter connected in Socket Mode.");
}

const entry = process.argv[1];
if (entry && import.meta.url === pathToFileURL(resolve(entry)).href) {
  startSlackApp().catch((error: unknown) => {
    console.error(error instanceof Error ? error.message : error);
    process.exitCode = 1;
  });
}
