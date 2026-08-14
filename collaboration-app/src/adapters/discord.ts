import { createServer, type IncomingMessage, type ServerResponse } from "node:http";
import { createHash } from "node:crypto";
import { resolve } from "node:path";
import { pathToFileURL } from "node:url";
import {
  ButtonStyleTypes,
  InteractionResponseFlags,
  InteractionResponseType,
  InteractionType,
  MessageComponentTypes,
  TextStyleTypes,
  verifyKey,
} from "discord-interactions";
import type {
  Exercise,
  OutboundDeliveryKind,
  StartingPoint,
  TeamChannelBinding,
  Visibility,
} from "../core/contracts.js";
import {
  MockFacilitatorProvider,
  OpenAIFacilitatorProvider,
} from "../core/facilitator.js";
import { WorkshopService } from "../core/service.js";
import { workshopPresentation, WorkshopError } from "../core/session.js";
import { FileWorkshopStore } from "../core/store.js";
import type { WorkshopRecord } from "../core/store.js";
import { chunkText, type RenderedWorkshopVisual } from "../core/visual.js";

const DISCORD_API = "https://discord.com/api/v10";
const MAX_REQUEST_BYTES = 1_000_000;
const MESSAGE_LIMIT = 1_900;
const ACK_DEADLINE_MS = 2_500;
const LEDGER_TTL_MS = 15 * 60_000;
const SIGNATURE_MAX_AGE_MS = 5 * 60_000;

type JsonObject = Record<string, unknown>;

interface DiscordCommandOption {
  name: string;
  type: number;
  value?: string;
  options?: DiscordCommandOption[];
}

interface DiscordComponentValue {
  custom_id?: string;
  value?: string;
  components?: DiscordComponentValue[];
  component?: DiscordComponentValue;
}

export interface DiscordInteraction {
  id: string;
  application_id: string;
  token: string;
  type: number;
  guild_id?: string;
  channel_id?: string;
  member?: { user?: { id?: string } };
  user?: { id?: string };
  message?: { id?: string; channel_id?: string };
  data?: {
    name?: string;
    custom_id?: string;
    options?: DiscordCommandOption[];
    components?: DiscordComponentValue[];
  };
}

export interface DiscordInteractionResponse {
  type: number;
  data?: JsonObject;
}

export interface DiscordRouteResult {
  response: DiscordInteractionResponse;
  /** Run only after the HTTP acknowledgement has been flushed to Discord. */
  afterResponse?: () => Promise<void>;
}

interface DiscordMessage {
  id: string;
  channel_id: string;
}

interface DiscordThread {
  id: string;
}

export interface DiscordApiPort {
  editOriginal(interaction: DiscordInteraction, payload: JsonObject): Promise<DiscordMessage>;
  createThread(channelId: string, messageId: string, name: string): Promise<DiscordThread | null>;
  sendMessage(channelId: string, payload: JsonObject): Promise<DiscordMessage>;
  uploadVisual(
    channelId: string,
    visual: Pick<RenderedWorkshopVisual, "png" | "alt_text" | "text_summary" | "artifact_ref">,
  ): Promise<DiscordMessage>;
  deleteMessage(channelId: string, messageId: string): Promise<void>;
}

export interface WorkshopPort {
  start(input: Parameters<WorkshopService["start"]>[0]): ReturnType<WorkshopService["start"]>;
  get(sessionId: string): ReturnType<WorkshopService["get"]>;
  bindRoot(
    sessionId: string,
    conversationRef: string,
    rootMessageRef: string,
    now?: string,
  ): ReturnType<WorkshopService["bindRoot"]>;
  contribute(input: Parameters<WorkshopService["contribute"]>[0]): ReturnType<WorkshopService["contribute"]>;
  pass(input: Parameters<WorkshopService["pass"]>[0]): ReturnType<WorkshopService["pass"]>;
  freeze(input: Parameters<WorkshopService["freeze"]>[0]): ReturnType<WorkshopService["freeze"]>;
  synthesize(sessionId: string, platform: "DISCORD"): ReturnType<WorkshopService["synthesize"]>;
  retrySynthesis(
    input: Parameters<WorkshopService["retrySynthesis"]>[0],
    platform: "DISCORD",
  ): ReturnType<WorkshopService["retrySynthesis"]>;
  assertController(sessionId: string, actorRef: string): ReturnType<WorkshopService["assertController"]>;
  claimOutboundDelivery(
    sessionId: string,
    input: Parameters<WorkshopService["claimOutboundDelivery"]>[1],
  ): ReturnType<WorkshopService["claimOutboundDelivery"]>;
  completeOutboundDelivery(
    sessionId: string,
    id: string,
    result: Parameters<WorkshopService["completeOutboundDelivery"]>[2],
  ): ReturnType<WorkshopService["completeOutboundDelivery"]>;
  failOutboundDelivery(
    sessionId: string,
    id: string,
    errorCode: string,
  ): ReturnType<WorkshopService["failOutboundDelivery"]>;
  markOutboundCleanup(
    sessionId: string,
    id: string,
    status: "DELETE_PENDING" | "DELETED" | "DELETE_FAILED",
    errorCode?: string | null,
  ): ReturnType<WorkshopService["markOutboundCleanup"]>;
  loadLatestVisual(input: Parameters<WorkshopService["loadLatestVisual"]>[0]): ReturnType<WorkshopService["loadLatestVisual"]>;
  close(input: Parameters<WorkshopService["close"]>[0]): ReturnType<WorkshopService["close"]>;
  delete(sessionId: string, actorRef: string): ReturnType<WorkshopService["delete"]>;
  privateBinding(sessionId: string): ReturnType<WorkshopService["privateBinding"]>;
}

function suppressMentions(): JsonObject {
  return { parse: [], replied_user: false };
}

function safeContent(...parts: Array<string | null | undefined>): string {
  return parts.filter((part): part is string => Boolean(part)).join("\n").slice(0, MESSAGE_LIMIT);
}

function deliveryNonce(id: string): string {
  return createHash("sha256").update(id).digest("hex").slice(0, 24);
}

function ephemeral(content: string): DiscordInteractionResponse {
  return {
    type: InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE,
    data: {
      content: safeContent(content),
      flags: InteractionResponseFlags.EPHEMERAL,
      allowed_mentions: suppressMentions(),
    },
  };
}

function deferred(ephemeralResponse: boolean): DiscordInteractionResponse {
  return {
    type: InteractionResponseType.DEFERRED_CHANNEL_MESSAGE_WITH_SOURCE,
    data: ephemeralResponse ? { flags: InteractionResponseFlags.EPHEMERAL } : {},
  };
}

function actionRow(components: JsonObject[]): JsonObject {
  return { type: MessageComponentTypes.ACTION_ROW, components };
}

function button(label: string, customId: string, style = ButtonStyleTypes.SECONDARY, disabled = false): JsonObject {
  return {
    type: MessageComponentTypes.BUTTON,
    label,
    custom_id: customId,
    style,
    disabled,
  };
}

function modal(
  customId: string,
  title: string,
  fields: Array<{
    id: string;
    label: string;
    style: TextStyleTypes;
    placeholder: string;
    maxLength: number;
  }>,
): DiscordInteractionResponse {
  return {
    type: InteractionResponseType.MODAL,
    data: {
      custom_id: customId,
      title,
      components: fields.map((field) => ({
        type: MessageComponentTypes.LABEL,
        label: field.label,
        component: {
            type: MessageComponentTypes.INPUT_TEXT,
            custom_id: field.id,
            style: field.style,
            placeholder: field.placeholder,
            min_length: 1,
            max_length: field.maxLength,
            required: true,
        },
      })),
    },
  };
}

function actorId(interaction: DiscordInteraction): string {
  const user = interaction.member?.user?.id ?? interaction.user?.id;
  if (!user) throw new WorkshopError("Discord did not provide a participant ID.", "ACTOR_REQUIRED");
  return `discord:${interaction.guild_id ?? "direct"}:${user}`;
}

function interactionScope(interaction: DiscordInteraction): { workspace: string; channel: string } {
  if (!interaction.guild_id || !interaction.channel_id) {
    throw new WorkshopError(
      "MightShape team exercises must be started in a server text channel.",
      "GUILD_CHANNEL_REQUIRED",
    );
  }
  return { workspace: interaction.guild_id, channel: interaction.channel_id };
}

function commandSelection(interaction: DiscordInteraction): {
  subcommand: string;
  options: Record<string, string>;
} {
  const subcommand = interaction.data?.options?.find((item) => item.type === 1);
  if (!subcommand) return { subcommand: "", options: {} };
  const options: Record<string, string> = {};
  for (const option of subcommand.options ?? []) {
    if (typeof option.value === "string") options[option.name] = option.value;
  }
  return { subcommand: subcommand.name, options };
}

function modalValues(interaction: DiscordInteraction): Record<string, string> {
  const result: Record<string, string> = {};
  const visit = (component: DiscordComponentValue): void => {
    if (component.custom_id && typeof component.value === "string") {
      result[component.custom_id] = component.value;
    }
    if (component.component) visit(component.component);
    for (const child of component.components ?? []) visit(child);
  };
  for (const component of interaction.data?.components ?? []) visit(component);
  return result;
}

function parseAction(value: string): { action: string; values: string[] } {
  const [prefix, action, ...values] = value.split("|");
  return prefix === "dc" && action ? { action, values } : { action: "", values: [] };
}

function setupId(exercise: Exercise, visibility: Visibility | "AUTO", startingPoint: StartingPoint): string {
  return `dc|setup|${exercise}|${visibility}|${startingPoint}`;
}

function contributionModal(sessionId: string): DiscordInteractionResponse {
  return modal(
    `dc|contribute|${sessionId}`,
    "Add to MightShape",
    [
      {
        id: "contribution",
        label: "Your contribution",
        style: TextStyleTypes.PARAGRAPH,
        placeholder: "One idea, observation, step, assumption, or question…",
        maxLength: 1_500,
      },
    ],
  );
}

function setupModal(exercise: Exercise, visibility: Visibility | "AUTO", startingPoint: StartingPoint): DiscordInteractionResponse {
  return modal(
    setupId(exercise, visibility, startingPoint),
    "Start a MightShape exercise",
    [
      {
        id: "challenge",
        label: "Design challenge",
        style: TextStyleTypes.PARAGRAPH,
        placeholder: "What are we trying to understand, frame, create, or test?",
        maxLength: 1_500,
      },
    ],
  );
}

function controls(record: WorkshopRecord): JsonObject[] {
  const { session } = record;
  const collecting = session.status === "COLLECTING";
  const canPass = session.status === "COLLECTING" || session.status === "PAUSED";
  const retryable =
    session.status === "FROZEN" &&
    session.history.at(-1)?.action === "SYNTHESIS_FAILED" &&
    session.history.at(-1)?.details.retryable === true;
  const deliveryRetryable =
    session.status === "REVIEW" &&
    record.binding.outbound_deliveries.some((receipt) =>
      ["FAILED", "UNKNOWN", "CLAIMED"].includes(receipt.status),
    );
  return [
    actionRow([
      button("Add my input", `dc|add|${session.id}`, ButtonStyleTypes.PRIMARY, !collecting),
      button("Pass", `dc|pass|${session.id}`, ButtonStyleTypes.SECONDARY, !canPass),
      button("Status", `dc|status|${session.id}`),
      button(
        retryable ? "Retry synthesis" : deliveryRetryable ? "Retry delivery" : "Freeze + create map",
        `dc|${retryable || deliveryRetryable ? "retry" : "freeze"}|${session.id}`,
        ButtonStyleTypes.SUCCESS,
        !(collecting || retryable || deliveryRetryable),
      ),
      button("Close", `dc|close|${session.id}`, ButtonStyleTypes.DANGER, session.status === "CLOSED"),
    ]),
    actionRow([
      button("Delete workshop data", `dc|delete|${session.id}`, ButtonStyleTypes.DANGER),
    ]),
  ];
}

function workshopCard(record: WorkshopRecord): JsonObject {
  const view = workshopPresentation(record.session);
  return {
    content: safeContent(
      view.headline,
      view.body,
      view.prompt ? `\n**Your move**\n${view.prompt}` : null,
      `\nSession: \`${record.session.id}\` · ${view.participant_count} participant(s) · ${view.contribution_count} contribution(s)`,
    ),
    components: controls(record),
    allowed_mentions: suppressMentions(),
  };
}

function rootTeaser(record: WorkshopRecord, threadId?: string): JsonObject {
  return {
    content: safeContent(
      `◇ **MightShape · team exercise started**`,
      `**${record.session.exercise.toLowerCase().replaceAll("_", " ")}**`,
      record.session.challenge,
      threadId ? `Continue together in <#${threadId}>.` : "Use the controls below to participate.",
      "The facilitator is AI. Team inputs are USER_PROVIDED design material—not human-research evidence.",
      `Session: \`${record.session.id}\` · recovery: \`/design-think status\` or \`/design-think retry\` in the workshop thread.`,
      `Local workshop state is stored until ${record.session.retention_expires_at.slice(0, 10)}. Channel posts follow Discord retention unless the initiator uses Delete workshop data; remote cleanup is best effort and any failure remains retryable.`,
    ),
    components: [],
    allowed_mentions: suppressMentions(),
  };
}

function statusText(record: WorkshopRecord): string {
  const view = workshopPresentation(record.session);
  return safeContent(
    `${view.headline} · ${view.phase}`,
    `${view.participant_count} participant(s) · ${view.contribution_count} contribution(s) · ${view.visibility.toLowerCase()} input`,
    view.prompt ? `Current prompt: ${view.prompt}` : null,
    `Session: \`${view.session_id}\``,
  );
}

function threadName(record: WorkshopRecord): string {
  const exercise = record.session.exercise.toLowerCase().replaceAll("_", " ");
  return `MightShape · ${exercise}`.slice(0, 100);
}

function errorText(error: unknown): string {
  if (error instanceof WorkshopError) return `△ ${error.message}`;
  return "△ MightShape could not complete that action. The exercise is unchanged where possible; try again or ask the initiator to check the service.";
}

function assertScope(binding: TeamChannelBinding, interaction: DiscordInteraction): void {
  const scope = interactionScope(interaction);
  const boundChannel = binding.conversation_ref ?? binding.channel_ref;
  if (binding.platform !== "DISCORD" || binding.workspace_ref !== scope.workspace || boundChannel !== scope.channel) {
    throw new WorkshopError("Use this control in the exact Discord thread where the exercise started.", "SCOPE_MISMATCH");
  }
  if (interaction.type === InteractionType.MESSAGE_COMPONENT) {
    const messageId = interaction.message?.id;
    const ownsControl = binding.outbound_deliveries.some(
      (receipt) =>
        (receipt.kind === "CONTROL" || receipt.kind === "ROOT") &&
        receipt.status === "POSTED" &&
        receipt.conversation_ref === boundChannel &&
        receipt.message_ref === messageId,
    );
    if (!messageId || !ownsControl) {
      throw new WorkshopError("This control is not attached to a recorded MightShape workshop message.", "SCOPE_MISMATCH");
    }
  }
}

/**
 * Bounded process-local replay protection. The portable session store independently
 * hashes mutating interaction IDs; multi-instance hosting should replace this with
 * a shared receipt store before horizontal scaling.
 */
export class DiscordInteractionLedger {
  private readonly receipts = new Map<string, {
    at: number;
    response: DiscordInteractionResponse | null;
    ready: Promise<DiscordInteractionResponse>;
    resolve: (response: DiscordInteractionResponse) => void;
  }>();

  reserve(interactionId: string, now = Date.now()): boolean {
    this.prune(now);
    if (this.receipts.has(interactionId)) return false;
    let resolveReady: (response: DiscordInteractionResponse) => void = () => undefined;
    const ready = new Promise<DiscordInteractionResponse>((accept) => {
      resolveReady = accept;
    });
    this.receipts.set(interactionId, { at: now, response: null, ready, resolve: resolveReady });
    return true;
  }

  complete(interactionId: string, response: DiscordInteractionResponse): void {
    const receipt = this.receipts.get(interactionId);
    if (!receipt || receipt.response) return;
    receipt.response = structuredClone(response);
    receipt.resolve(structuredClone(response));
  }

  async wait(interactionId: string): Promise<DiscordInteractionResponse | null> {
    const receipt = this.receipts.get(interactionId);
    return receipt ? structuredClone(await receipt.ready) : null;
  }

  claim(interactionId: string, response: DiscordInteractionResponse, now = Date.now()): boolean {
    if (!this.reserve(interactionId, now)) return false;
    this.complete(interactionId, response);
    return true;
  }

  replay(interactionId: string): DiscordInteractionResponse | null {
    const receipt = this.receipts.get(interactionId);
    return receipt?.response ? structuredClone(receipt.response) : null;
  }

  private prune(now: number): void {
    for (const [id, receipt] of this.receipts) {
      if (now - receipt.at > LEDGER_TTL_MS) this.receipts.delete(id);
    }
  }
}

export class DiscordRestApi implements DiscordApiPort {
  constructor(
    private readonly botToken: string,
    private readonly fetchImpl: typeof fetch = fetch,
  ) {}

  private async json(path: string, init: RequestInit, botAuth: boolean): Promise<JsonObject> {
    const headers = new Headers(init.headers);
    if (botAuth) headers.set("Authorization", `Bot ${this.botToken}`);
    headers.set("User-Agent", "MightShape/1.0.1 (+https://github.com/grantholt-byte/mightshape)");
    const response = await this.fetchImpl(`${DISCORD_API}${path}`, { ...init, headers });
    if (!response.ok) throw new Error(`Discord API request failed (${response.status}).`);
    return (await response.json()) as JsonObject;
  }

  async editOriginal(interaction: DiscordInteraction, payload: JsonObject): Promise<DiscordMessage> {
    return (await this.json(
      `/webhooks/${encodeURIComponent(interaction.application_id)}/${encodeURIComponent(interaction.token)}/messages/@original`,
      {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ...payload, allowed_mentions: suppressMentions() }),
      },
      false,
    )) as unknown as DiscordMessage;
  }

  async createThread(channelId: string, messageId: string, name: string): Promise<DiscordThread | null> {
    const response = await this.fetchImpl(
      `${DISCORD_API}/channels/${encodeURIComponent(channelId)}/messages/${encodeURIComponent(messageId)}/threads`,
      {
        method: "POST",
        headers: {
          Authorization: `Bot ${this.botToken}`,
          "Content-Type": "application/json",
          "User-Agent": "MightShape/1.0.1 (+https://github.com/grantholt-byte/mightshape)",
        },
        body: JSON.stringify({ name, auto_archive_duration: 1_440 }),
      },
    );
    // Threads are an enhancement. Unsupported channel types or missing thread
    // permission fall back to a channel-scoped workshop without losing the session.
    if (!response.ok) return null;
    return (await response.json()) as DiscordThread;
  }

  async sendMessage(channelId: string, payload: JsonObject): Promise<DiscordMessage> {
    return (await this.json(
      `/channels/${encodeURIComponent(channelId)}/messages`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ...payload, allowed_mentions: suppressMentions() }),
      },
      true,
    )) as unknown as DiscordMessage;
  }

  async uploadVisual(
    channelId: string,
    visual: Pick<RenderedWorkshopVisual, "png" | "alt_text" | "text_summary" | "artifact_ref">,
  ): Promise<DiscordMessage> {
    const filename = `${visual.artifact_ref.artifact_id.toLowerCase()}.png`;
    const payload = {
      content: safeContent(
        "◇ **MightShape · visual synthesis**",
        `Artifact: ${visual.artifact_ref.artifact_id}. The complete accessible source set and synthesis follow as text messages.`,
        "Every sticky note or process step remains source-linked to USER_PROVIDED input. AI-created grouping and labels are DESIGN_COUNCIL interpretation.",
      ),
      attachments: [{ id: 0, filename, description: visual.alt_text.slice(0, 1_024) }],
      nonce: deliveryNonce(`visual:${visual.artifact_ref.artifact_id}`),
      enforce_nonce: true,
      allowed_mentions: suppressMentions(),
    };
    const form = new FormData();
    form.append("payload_json", JSON.stringify(payload));
    form.append("files[0]", new Blob([Uint8Array.from(visual.png)], { type: "image/png" }), filename);
    return (await this.json(
      `/channels/${encodeURIComponent(channelId)}/messages`,
      { method: "POST", body: form },
      true,
    )) as unknown as DiscordMessage;
  }

  async deleteMessage(channelId: string, messageId: string): Promise<void> {
    const response = await this.fetchImpl(
      `${DISCORD_API}/channels/${encodeURIComponent(channelId)}/messages/${encodeURIComponent(messageId)}`,
      {
        method: "DELETE",
        headers: {
          Authorization: `Bot ${this.botToken}`,
          "User-Agent": "MightShape/1.0.1 (+https://github.com/grantholt-byte/mightshape)",
        },
      },
    );
    if (!response.ok && response.status !== 404) {
      throw new Error(`Discord message deletion failed (${response.status}).`);
    }
  }
}

export class DiscordAdapter {
  constructor(
    private readonly workshops: WorkshopPort,
    private readonly api: DiscordApiPort,
    private readonly ledger = new DiscordInteractionLedger(),
  ) {}

  async route(interaction: DiscordInteraction): Promise<DiscordRouteResult> {
    const replay = this.ledger.replay(interaction.id);
    if (replay) return { response: replay };
    if (!this.ledger.reserve(interaction.id)) {
      const pending = await this.ledger.wait(interaction.id);
      return {
        response: pending ?? ephemeral("This Discord interaction is already being processed."),
      };
    }

    let result: DiscordRouteResult;
    if (interaction.type === InteractionType.PING) {
      result = { response: { type: InteractionResponseType.PONG } };
    } else if (interaction.type === InteractionType.APPLICATION_COMMAND) {
      result = this.command(interaction);
    } else if (interaction.type === InteractionType.MESSAGE_COMPONENT) {
      const parsed = parseAction(interaction.data?.custom_id ?? "");
      const sessionId = parsed.values[0];
      if (!sessionId) {
        result = { response: ephemeral("This MightShape control is invalid.") };
      } else {
        try {
          await this.scopedBinding(interaction, sessionId);
          result = this.component(interaction);
        } catch (error) {
          result = { response: ephemeral(errorText(error)) };
        }
      }
    } else if (interaction.type === InteractionType.MODAL_SUBMIT) {
      result = this.modalSubmit(interaction);
    } else {
      result = { response: ephemeral("That Discord interaction is not supported by MightShape.") };
    }

    this.ledger.complete(interaction.id, result.response);
    return result;
  }

  private command(interaction: DiscordInteraction): DiscordRouteResult {
    if (interaction.data?.name !== "design-think") {
      return { response: ephemeral("Unknown command. Use `/design-think start`.") };
    }
    const { subcommand, options } = commandSelection(interaction);
    if (subcommand === "start") {
      const exercise = (options.exercise ?? "BRAINSTORMING") as Exercise;
      const visibility = (options.visibility ?? "AUTO") as Visibility | "AUTO";
      const startingPoint = (options["starting-point"] ?? "UNSURE") as StartingPoint;
      return { response: setupModal(exercise, visibility, startingPoint) };
    }
    if (subcommand === "status" && options.session) {
      const response = deferred(true);
      return { response, afterResponse: () => this.status(interaction, options.session!) };
    }
    if (subcommand === "retry" && options.session) {
      const response = deferred(true);
      return { response, afterResponse: () => this.retry(interaction, options.session!) };
    }
    if (subcommand === "delete" && options.session) {
      const response = deferred(true);
      return { response, afterResponse: () => this.delete(interaction, options.session!) };
    }
    return { response: ephemeral("Choose `start`, `status`, `retry`, or `delete` and provide the requested fields.") };
  }

  private component(interaction: DiscordInteraction): DiscordRouteResult {
    const parsed = parseAction(interaction.data?.custom_id ?? "");
    const sessionId = parsed.values[0];
    if (!sessionId) return { response: ephemeral("This MightShape control is invalid.") };
    if (parsed.action === "add") return { response: contributionModal(sessionId) };
    if (parsed.action === "pass") {
      return { response: deferred(true), afterResponse: () => this.pass(interaction, sessionId) };
    }
    if (parsed.action === "status") {
      return { response: deferred(true), afterResponse: () => this.status(interaction, sessionId) };
    }
    if (parsed.action === "freeze") {
      return { response: deferred(true), afterResponse: () => this.freeze(interaction, sessionId) };
    }
    if (parsed.action === "retry") {
      return { response: deferred(true), afterResponse: () => this.retry(interaction, sessionId) };
    }
    if (parsed.action === "close") {
      return { response: deferred(true), afterResponse: () => this.close(interaction, sessionId) };
    }
    if (parsed.action === "delete") {
      return { response: deferred(true), afterResponse: () => this.delete(interaction, sessionId) };
    }
    return { response: ephemeral("This MightShape control is no longer supported.") };
  }

  private modalSubmit(interaction: DiscordInteraction): DiscordRouteResult {
    const parsed = parseAction(interaction.data?.custom_id ?? "");
    if (parsed.action === "setup") {
      // A public deferred response becomes the workshop root and can own a thread.
      return { response: deferred(false), afterResponse: () => this.start(interaction, parsed.values) };
    }
    if (parsed.action === "contribute" && parsed.values[0]) {
      return {
        response: deferred(true),
        afterResponse: () => this.contribute(interaction, parsed.values[0]!),
      };
    }
    return { response: ephemeral("This MightShape form is invalid or expired.") };
  }

  private async scopedBinding(interaction: DiscordInteraction, sessionId: string): Promise<TeamChannelBinding> {
    const binding = await this.workshops.privateBinding(sessionId);
    assertScope(binding, interaction);
    return binding;
  }

  private async start(interaction: DiscordInteraction, values: string[]): Promise<void> {
    try {
      const scope = interactionScope(interaction);
      const form = modalValues(interaction);
      const exercise = (values[0] ?? "BRAINSTORMING") as Exercise;
      const selectedVisibility = (values[1] ?? "AUTO") as Visibility | "AUTO";
      const startingPoint = (values[2] ?? "UNSURE") as StartingPoint;
      const record = await this.workshops.start({
        platform: "DISCORD",
        workspace_ref: scope.workspace,
        channel_ref: scope.channel,
        actor_ref: actorId(interaction),
        challenge: form.challenge ?? "",
        exercise,
        starting_point: startingPoint,
        ...(selectedVisibility === "AUTO" ? {} : { visibility: selectedVisibility }),
        facilitator_level: "NOVICE_ASSISTED",
        event_id: `discord:${interaction.id}`,
        retention_days: Number(process.env.DC_RETENTION_DAYS ?? "30"),
      });
      const root = await this.api.editOriginal(interaction, rootTeaser(record));
      const thread = await this.api.createThread(scope.channel, root.id, threadName(record));
      const conversation = thread?.id ?? scope.channel;
      const bound = await this.workshops.bindRoot(record.session.id, conversation, root.id);
      await this.recordKnownDelivery(bound, {
        id: "discord:root",
        kind: "ROOT",
        conversation_ref: scope.channel,
        root_message_ref: root.id,
        artifact_id: null,
      }, root.id);
      if (thread) {
        await this.api.editOriginal(interaction, rootTeaser(bound, thread.id));
        await this.postRecordedMessage(
          bound,
          "discord:control:initial",
          "CONTROL",
          workshopCard(bound),
        );
      } else {
        await this.api.editOriginal(interaction, workshopCard(bound));
      }
    } catch (error) {
      await this.api.editOriginal(interaction, {
        content: errorText(error),
        components: [],
        allowed_mentions: suppressMentions(),
      });
    }
  }

  private async contribute(interaction: DiscordInteraction, sessionId: string): Promise<void> {
    try {
      const binding = await this.scopedBinding(interaction, sessionId);
      const content = modalValues(interaction).contribution ?? "";
      const result = await this.workshops.contribute({
        session_id: sessionId,
        actor_ref: actorId(interaction),
        content,
        event_id: `discord:${interaction.id}`,
      });
      await this.api.editOriginal(interaction, {
        content: `✓ Input captured as ${result.contribution.id} · USER_PROVIDED${result.session.visibility === "SEALED" ? " · sealed until freeze" : ""}.`,
        components: [],
        allowed_mentions: suppressMentions(),
      });
      if (result.session.visibility === "OPEN") {
        await this.postRecordedMessage({ session: result.session, binding }, `discord:${interaction.id}:source`, "SOURCE_SET", {
          content: safeContent(
            `◇ **Team input · ${result.contribution.id}**`,
            `> ${result.contribution.content.replaceAll("\n", "\n> ")}`,
            "Provenance: USER_PROVIDED",
          ),
          allowed_mentions: suppressMentions(),
        });
      } else {
        await this.postRecordedMessage({ session: result.session, binding }, `discord:${interaction.id}:status`, "STATUS", {
          content: `◇ A sealed contribution was added. ${result.session.contributions.length} input(s) are now held independently; content stays hidden until freeze.`,
          allowed_mentions: suppressMentions(),
        });
      }
    } catch (error) {
      await this.api.editOriginal(interaction, {
        content: errorText(error),
        components: [],
        allowed_mentions: suppressMentions(),
      });
    }
  }

  private async status(interaction: DiscordInteraction, sessionId: string): Promise<void> {
    try {
      await this.scopedBinding(interaction, sessionId);
      const record = await this.workshops.get(sessionId);
      await this.api.editOriginal(interaction, {
        content: statusText(record),
        components: [],
        allowed_mentions: suppressMentions(),
      });
    } catch (error) {
      await this.api.editOriginal(interaction, {
        content: errorText(error),
        components: [],
        allowed_mentions: suppressMentions(),
      });
    }
  }

  private async pass(interaction: DiscordInteraction, sessionId: string): Promise<void> {
    try {
      const binding = await this.scopedBinding(interaction, sessionId);
      const record = await this.workshops.pass({
        session_id: sessionId,
        actor_ref: actorId(interaction),
        event_id: `discord:${interaction.id}`,
      });
      await this.api.editOriginal(interaction, {
        content: "✓ Pass recorded. Participation is optional; you can still add input later while the exercise is collecting.",
        components: [],
        allowed_mentions: suppressMentions(),
      });
      await this.postRecordedMessage(record, `discord:${interaction.id}:status`, "STATUS", {
        content: `◇ A teammate passed this prompt. ${record.session.contributions.length} contribution(s) are currently captured; no response was fabricated for them.`,
        allowed_mentions: suppressMentions(),
      });
    } catch (error) {
      await this.api.editOriginal(interaction, {
        content: errorText(error),
        components: [],
        allowed_mentions: suppressMentions(),
      });
    }
  }

  private async freeze(interaction: DiscordInteraction, sessionId: string): Promise<void> {
    try {
      const binding = await this.scopedBinding(interaction, sessionId);
      const frozen = await this.workshops.freeze({
        session_id: sessionId,
        actor_ref: actorId(interaction),
        event_id: `discord:${interaction.id}`,
      });
      await this.api.editOriginal(interaction, {
        content: `✓ ${frozen.session.contributions.length} contribution(s) frozen. The AI facilitator is creating a source-linked visual…`,
        components: [],
        allowed_mentions: suppressMentions(),
      });
      await this.postRecordedMessage(frozen, `discord:${interaction.id}:progress`, "PROGRESS", {
        content: "◇ **Freeze** · independent input is now visible to the facilitator. Synthesis has started; contradictions and outliers will remain inspectable.",
        allowed_mentions: suppressMentions(),
      });
      await this.completeSynthesis(
        interaction,
        sessionId,
        binding,
        () => this.workshops.synthesize(sessionId, "DISCORD"),
      );
    } catch (error) {
      await this.api.editOriginal(interaction, {
        content: errorText(error),
        components: [],
        allowed_mentions: suppressMentions(),
      });
    }
  }

  private async retry(interaction: DiscordInteraction, sessionId: string): Promise<void> {
    try {
      const binding = await this.scopedBinding(interaction, sessionId);
      const current = await this.workshops.get(sessionId);
      if (current.session.status === "REVIEW") {
        await this.api.editOriginal(interaction, {
          content: "✓ Authorized delivery retry received. The existing synthesis and visual are unchanged…",
          components: [],
          allowed_mentions: suppressMentions(),
        });
        const loaded = await this.workshops.loadLatestVisual({
          session_id: sessionId,
          actor_ref: actorId(interaction),
          event_id: `discord:${interaction.id}`,
        });
        const failures = await this.deliverVisual(loaded.record, loaded.visual);
        await this.api.editOriginal(interaction, {
          content: failures === 0
            ? "✓ Existing visual and complete text alternative delivered; synthesis was not rerun."
            : `△ Delivery remains partial (${failures} item(s) failed). The existing artifact and retry receipts were retained; synthesis was not rerun.`,
          components: [],
          allowed_mentions: suppressMentions(),
        });
        return;
      }
      await this.api.editOriginal(interaction, {
        content: "✓ Authorized retry received. The frozen set is unchanged while synthesis runs again…",
        components: [],
        allowed_mentions: suppressMentions(),
      });
      await this.completeSynthesis(
        interaction,
        sessionId,
        binding,
        () => this.workshops.retrySynthesis(
          {
            session_id: sessionId,
            actor_ref: actorId(interaction),
            event_id: `discord:${interaction.id}`,
          },
          "DISCORD",
        ),
      );
    } catch (error) {
      await this.api.editOriginal(interaction, {
        content: errorText(error),
        components: [],
        allowed_mentions: suppressMentions(),
      });
    }
  }

  private async recordKnownDelivery(
    record: WorkshopRecord,
    input: Parameters<WorkshopPort["claimOutboundDelivery"]>[1],
    messageRef: string,
  ): Promise<boolean> {
    const claimed = await this.workshops.claimOutboundDelivery(record.session.id, input);
    if (!claimed.claimed) return claimed.receipt.status === "POSTED";
    try {
      await this.workshops.completeOutboundDelivery(record.session.id, input.id, { message_ref: messageRef });
      return true;
    } catch (error) {
      await this.workshops.failOutboundDelivery(record.session.id, input.id, "RECEIPT_WRITE_FAILED").catch(() => undefined);
      throw error;
    }
  }

  private async postRecordedMessage(
    record: WorkshopRecord,
    id: string,
    kind: OutboundDeliveryKind,
    payload: JsonObject,
    artifactId: string | null = null,
  ): Promise<boolean> {
    const conversation = record.binding.conversation_ref ?? record.binding.channel_ref;
    const claim = await this.workshops.claimOutboundDelivery(record.session.id, {
      id,
      kind,
      conversation_ref: conversation,
      root_message_ref: record.binding.root_message_ref,
      artifact_id: artifactId,
    });
    if (!claim.claimed) return claim.receipt.status === "POSTED";
    try {
      const message = await this.api.sendMessage(conversation, {
        ...payload,
        nonce: deliveryNonce(id),
        enforce_nonce: true,
      });
      await this.workshops.completeOutboundDelivery(record.session.id, id, { message_ref: message.id });
      return true;
    } catch (error) {
      await this.workshops.failOutboundDelivery(record.session.id, id, "DISCORD_MESSAGE_FAILED").catch(() => undefined);
      return false;
    }
  }

  private async postTextFallback(
    record: WorkshopRecord,
    value: string,
    idPrefix: string,
    artifactId: string | null,
  ): Promise<number> {
    let failures = 0;
    for (const [index, text] of chunkText(value, 1_750).entries()) {
      const delivered = await this.postRecordedMessage(record, `${idPrefix}:text:${index}`, "TEXT_FALLBACK", {
        content: safeContent(
          index === 0
            ? "◇ **MightShape · accessible text alternative**"
            : `◇ **Text alternative · continued ${index + 1}**`,
          text,
        ),
        allowed_mentions: suppressMentions(),
      }, artifactId);
      if (!delivered) failures += 1;
    }
    return failures;
  }

  private async deliverVisual(record: WorkshopRecord, visual: RenderedWorkshopVisual): Promise<number> {
    const channel = record.binding.conversation_ref ?? record.binding.channel_ref;
    const artifactId = visual.artifact_ref.artifact_id;
    const prefix = `discord:${artifactId}`;
    let failures = 0;
    const imageClaim = await this.workshops.claimOutboundDelivery(record.session.id, {
      id: `${prefix}:visual`,
      kind: "VISUAL",
      conversation_ref: channel,
      root_message_ref: record.binding.root_message_ref,
      artifact_id: artifactId,
    });
    let imagePosted = imageClaim.receipt.status === "POSTED";
    if (imageClaim.claimed) {
      try {
        const message = await this.api.uploadVisual(channel, visual);
        await this.workshops.completeOutboundDelivery(record.session.id, imageClaim.receipt.id, {
          message_ref: message.id,
          file_ref: message.id,
        });
        imagePosted = true;
      } catch {
        await this.workshops.failOutboundDelivery(record.session.id, imageClaim.receipt.id, "DISCORD_VISUAL_FAILED").catch(() => undefined);
        failures += 1;
      }
    } else if (!imagePosted) {
      failures += 1;
    }

    if (!imagePosted) {
      const notice = await this.postRecordedMessage(
        record,
        `${prefix}:visual-failure-notice`,
        "STATUS",
        {
          content: "△ The PNG could not be posted. The complete text alternative follows; the generated artifact remains available for delivery retry without rerunning synthesis.",
          allowed_mentions: suppressMentions(),
        },
        artifactId,
      );
      if (!notice) failures += 1;
    }
    failures += await this.postTextFallback(record, visual.text_fallback, prefix, artifactId);
    const refreshed = await this.workshops.get(record.session.id);
    const review = await this.postRecordedMessage(
      refreshed,
      `${prefix}:review-control:${failures > 0 ? "partial" : "complete"}`,
      "CONTROL",
      {
        content: safeContent(
          `◆ **Review** · ${refreshed.session.artifacts.length} visual artifact(s) recorded`,
          imagePosted
            ? "PNG and complete text alternative posted."
            : "Complete text alternative posted; PNG delivery remains retryable without rerunning synthesis.",
        ),
        components: controls(refreshed),
        allowed_mentions: suppressMentions(),
      },
      artifactId,
    );
    if (!review) failures += 1;
    return failures;
  }

  private async completeSynthesis(
    interaction: DiscordInteraction,
    sessionId: string,
    binding: TeamChannelBinding,
    operation: () => ReturnType<WorkshopPort["synthesize"]>,
  ): Promise<void> {
    try {
      const { record, visual } = await operation();
      const failures = await this.deliverVisual(record, visual);
      await this.api.editOriginal(interaction, {
        content: failures === 0
          ? "✓ Visual and accessible text alternative posted in the workshop thread."
          : `△ Synthesis completed, but delivery is partial (${failures} item(s) failed). Use Retry delivery; synthesis will not run again.`,
        components: [],
        allowed_mentions: suppressMentions(),
      });
    } catch (error) {
      if (error instanceof WorkshopError && error.text_fallback) {
        const record = await this.workshops.get(sessionId).catch(() => null);
        if (record) await this.postTextFallback(record, error.text_fallback, `discord:failure:${record.session.step_version}`, null);
      }
      const record = await this.workshops.get(sessionId).catch(() => null);
      if (record) {
        await this.postRecordedMessage(record, `discord:failure:${record.session.step_version}:control`, "CONTROL", {
          content: safeContent(
            "△ **Synthesis did not complete**",
            errorText(error),
            "The frozen source set is intact. The initiator can use Retry synthesis.",
          ),
          components: controls(record),
          allowed_mentions: suppressMentions(),
        });
      }
      await this.api.editOriginal(interaction, {
        content: errorText(error),
        components: [],
        allowed_mentions: suppressMentions(),
      });
    }
  }

  private async close(interaction: DiscordInteraction, sessionId: string): Promise<void> {
    try {
      const binding = await this.scopedBinding(interaction, sessionId);
      const record = await this.workshops.close({
        session_id: sessionId,
        actor_ref: actorId(interaction),
        event_id: `discord:${interaction.id}`,
      });
      await this.postRecordedMessage(record, `discord:${interaction.id}:status`, "STATUS", {
        content: `◇ **Workshop closed** · ${record.session.contributions.length} USER_PROVIDED contribution(s) remain in the versioned exercise record until its retention date.`,
        allowed_mentions: suppressMentions(),
      });
      await this.api.editOriginal(interaction, {
        content: "✓ Exercise closed. Only the initiator or a delegated facilitator can close a workshop.",
        components: [],
        allowed_mentions: suppressMentions(),
      });
    } catch (error) {
      await this.api.editOriginal(interaction, {
        content: errorText(error),
        components: [],
        allowed_mentions: suppressMentions(),
      });
    }
  }

  private async delete(interaction: DiscordInteraction, sessionId: string): Promise<void> {
    try {
      await this.scopedBinding(interaction, sessionId);
      const current = await this.workshops.assertController(sessionId, actorId(interaction));
      const receipts = current.binding.outbound_deliveries.filter((receipt) => receipt.status !== "DELETED");
      let failures = 0;
      const deletedResources = new Set<string>();
      for (const receipt of receipts) {
        if (!receipt.message_ref) {
          failures += 1;
          await this.workshops.markOutboundCleanup(
            sessionId,
            receipt.id,
            "DELETE_FAILED",
            "REMOTE_REFERENCE_UNAVAILABLE",
          );
          continue;
        }
        const key = `${receipt.conversation_ref}\0${receipt.message_ref}`;
        await this.workshops.markOutboundCleanup(sessionId, receipt.id, "DELETE_PENDING");
        try {
          if (!deletedResources.has(key)) {
            await this.api.deleteMessage(receipt.conversation_ref, receipt.message_ref);
            deletedResources.add(key);
          }
          await this.workshops.markOutboundCleanup(sessionId, receipt.id, "DELETED");
        } catch {
          failures += 1;
          await this.workshops.markOutboundCleanup(
            sessionId,
            receipt.id,
            "DELETE_FAILED",
            "DISCORD_DELETE_FAILED",
          );
        }
      }
      if (failures > 0) {
        await this.api.editOriginal(interaction, {
          content: `△ Partial cleanup: ${failures} recorded Discord item(s) could not be confirmed deleted. Local session data and retryable receipts were retained. If delivery itself failed, retry delivery first; then run \`/design-think delete\` with this session ID in the workshop thread. Deletion is best effort, not a confidentiality guarantee.`,
          components: [],
          allowed_mentions: suppressMentions(),
        });
        return;
      }
      const deleted = await this.workshops.delete(sessionId, actorId(interaction));
      await this.api.editOriginal(interaction, {
        content: deleted
          ? receipts.length
            ? `✓ Best-effort Discord cleanup completed for ${receipts.length} recorded bot post(s); ${sessionId} and local generated artifacts were deleted.`
            : `✓ ${sessionId} and local generated artifacts were deleted. This older session had no recorded bot-post receipts, so remote cleanup could not be verified.`
          : "That session was already absent.",
        components: [],
        allowed_mentions: suppressMentions(),
      });
    } catch (error) {
      await this.api.editOriginal(interaction, {
        content: errorText(error),
        components: [],
        allowed_mentions: suppressMentions(),
      });
    }
  }
}

async function rawBody(request: IncomingMessage): Promise<Buffer> {
  const chunks: Buffer[] = [];
  let total = 0;
  for await (const chunk of request) {
    const buffer = Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk);
    total += buffer.byteLength;
    if (total > MAX_REQUEST_BYTES) throw new Error("Request body is too large.");
    chunks.push(buffer);
  }
  return Buffer.concat(chunks);
}

function json(response: ServerResponse, status: number, payload: unknown): void {
  response.statusCode = status;
  response.setHeader("Content-Type", "application/json; charset=utf-8");
  response.setHeader("Cache-Control", "no-store");
  response.end(JSON.stringify(payload));
}

export function createDiscordHttpServer(adapter: DiscordAdapter, publicKey: string) {
  return createServer(async (request, response) => {
    if (request.method === "GET" && request.url === "/healthz") {
      return json(response, 200, { ok: true, service: "mightshape-discord" });
    }
    if (request.method !== "POST" || request.url !== "/interactions") {
      return json(response, 404, { error: "not_found" });
    }
    const started = Date.now();
    try {
      const body = await rawBody(request);
      const signature = request.headers["x-signature-ed25519"];
      const timestamp = request.headers["x-signature-timestamp"];
      const signedAt = typeof timestamp === "string" ? Number(timestamp) * 1_000 : Number.NaN;
      if (
        typeof signature !== "string" ||
        typeof timestamp !== "string" ||
        !Number.isFinite(signedAt) ||
        Math.abs(Date.now() - signedAt) > SIGNATURE_MAX_AGE_MS ||
        !(await verifyKey(body, signature, timestamp, publicKey))
      ) {
        return json(response, 401, { error: "invalid_signature" });
      }
      const interaction = JSON.parse(body.toString("utf8")) as DiscordInteraction;
      const result = await adapter.route(interaction);
      if (Date.now() - started > ACK_DEADLINE_MS) {
        // Do not log payloads: they may contain private workshop material.
        console.warn("Discord interaction acknowledgement approached the 3-second deadline.");
      }
      json(response, 200, result.response);
      if (result.afterResponse) {
        setImmediate(() => {
          void result.afterResponse!().catch(() => {
            console.error("Discord post-acknowledgement task failed; interaction content was not logged.");
          });
        });
      }
    } catch {
      if (!response.headersSent) json(response, 400, { error: "invalid_request" });
    }
  });
}

function requiredEnv(name: string): string {
  const value = process.env[name]?.trim();
  if (!value) throw new Error(`${name} is required.`);
  return value;
}

export async function startDiscordApp(): Promise<void> {
  const publicKey = requiredEnv("DISCORD_PUBLIC_KEY");
  const botToken = requiredEnv("DISCORD_BOT_TOKEN");
  const dataRoot = resolve(process.env.DC_TEAM_DATA_DIR ?? ".data");
  const store = new FileWorkshopStore(resolve(dataRoot, "sessions"));
  const facilitator =
    process.env.DC_AI_MODE === "openai"
      ? new OpenAIFacilitatorProvider({
          apiKey: requiredEnv("OPENAI_API_KEY"),
          model: process.env.OPENAI_MODEL ?? "gpt-5.6-sol",
        })
      : new MockFacilitatorProvider();
  const workshops = new WorkshopService(store, facilitator, dataRoot);
  const adapter = new DiscordAdapter(workshops, new DiscordRestApi(botToken));
  const server = createDiscordHttpServer(adapter, publicKey);
  const port = Number(process.env.DISCORD_PORT ?? "3002");
  await new Promise<void>((accept, reject) => {
    server.once("error", reject);
    server.listen(port, () => accept());
  });
  console.log(`MightShape Discord adapter listening on :${port}/interactions`);
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  void startDiscordApp().catch((error: unknown) => {
    console.error(error instanceof Error ? error.message : "Discord adapter failed to start.");
    process.exitCode = 1;
  });
}
