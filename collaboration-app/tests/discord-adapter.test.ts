import assert from "node:assert/strict";
import { generateKeyPairSync, sign } from "node:crypto";
import { mkdtemp, readFile, rm } from "node:fs/promises";
import type { AddressInfo } from "node:net";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";
import test from "node:test";
import {
  InteractionResponseFlags,
  InteractionResponseType,
  InteractionType,
} from "discord-interactions";
import {
  DiscordAdapter,
  DiscordInteractionLedger,
  DiscordRestApi,
  createDiscordHttpServer,
  type DiscordApiPort,
  type DiscordInteraction,
} from "../src/adapters/discord.js";
import { MockFacilitatorProvider, type FacilitatorProvider } from "../src/core/facilitator.js";
import { WorkshopService } from "../src/core/service.js";
import { MemoryWorkshopStore } from "../src/core/store.js";
import { DESIGN_THINK_COMMAND, registerDiscordCommand } from "../scripts/register-discord.js";

class FakeDiscordApi implements DiscordApiPort {
  edits: Array<{ interaction: DiscordInteraction; payload: Record<string, unknown> }> = [];
  messages: Array<{ channel: string; payload: Record<string, unknown> }> = [];
  uploads: Array<{ channel: string; bytes: number; alt: string }> = [];
  deletes: Array<{ channel: string; message: string }> = [];
  failUploadCount = 0;
  failDeleteRefs = new Set<string>();
  makeThread = true;

  async editOriginal(interaction: DiscordInteraction, payload: Record<string, unknown>) {
    this.edits.push({ interaction, payload });
    return { id: "ROOT-1", channel_id: interaction.channel_id ?? "CHANNEL-1" };
  }

  async createThread(_channelId: string, _messageId: string, _name: string) {
    return this.makeThread ? { id: "THREAD-1" } : null;
  }

  async sendMessage(channelId: string, payload: Record<string, unknown>) {
    this.messages.push({ channel: channelId, payload });
    return { id: `MSG-${this.messages.length}`, channel_id: channelId };
  }

  async uploadVisual(
    channelId: string,
    visual: { png: Buffer; alt_text: string },
  ) {
    if (this.failUploadCount > 0) {
      this.failUploadCount -= 1;
      throw new Error("simulated Discord upload failure");
    }
    this.uploads.push({ channel: channelId, bytes: visual.png.byteLength, alt: visual.alt_text });
    return { id: `UPLOAD-${this.uploads.length}`, channel_id: channelId };
  }

  async deleteMessage(channelId: string, messageId: string) {
    this.deletes.push({ channel: channelId, message: messageId });
    if (this.failDeleteRefs.has(messageId)) throw new Error("simulated Discord delete failure");
  }
}

function command(id: string, subcommand: string, options: Record<string, string> = {}): DiscordInteraction {
  return {
    id,
    application_id: "APP-1",
    token: `TOKEN-${id}`,
    type: InteractionType.APPLICATION_COMMAND,
    guild_id: "GUILD-1",
    channel_id: "CHANNEL-1",
    member: { user: { id: "USER-1" } },
    data: {
      name: "design-think",
      options: [
        {
          type: 1,
          name: subcommand,
          options: Object.entries(options).map(([name, value]) => ({ type: 3, name, value })),
        },
      ],
    },
  };
}

function modalSubmit(
  id: string,
  customId: string,
  field: string,
  value: string,
  user = "USER-1",
  channel = "CHANNEL-1",
): DiscordInteraction {
  return {
    id,
    application_id: "APP-1",
    token: `TOKEN-${id}`,
    type: InteractionType.MODAL_SUBMIT,
    guild_id: "GUILD-1",
    channel_id: channel,
    member: { user: { id: user } },
    data: {
      custom_id: customId,
      components: [{ component: { custom_id: field, value } }],
    },
  };
}

function component(id: string, customId: string, user: string): DiscordInteraction {
  return {
    id,
    application_id: "APP-1",
    token: `TOKEN-${id}`,
    type: InteractionType.MESSAGE_COMPONENT,
    guild_id: "GUILD-1",
    channel_id: "THREAD-1",
    member: { user: { id: user } },
    message: { id: "MSG-1", channel_id: "THREAD-1" },
    data: { custom_id: customId },
  };
}

function modalCustomId(response: { data?: Record<string, unknown> }): string {
  const customId = response.data?.custom_id;
  if (typeof customId !== "string") assert.fail("modal custom_id is missing");
  return customId;
}

function content(payload: Record<string, unknown>): string {
  return typeof payload.content === "string" ? payload.content : "";
}

async function startedWorkshop(
  dataRoot = resolve(".test-data"),
  facilitator: FacilitatorProvider = new MockFacilitatorProvider(),
) {
  const store = new MemoryWorkshopStore();
  const service = new WorkshopService(store, facilitator, dataRoot);
  const api = new FakeDiscordApi();
  const adapter = new DiscordAdapter(service, api);
  const startCommand = await adapter.route(
    command("COMMAND-START", "start", {
      exercise: "BRAINSTORMING",
      visibility: "SEALED",
      "starting-point": "EARLY_HUNCH",
    }),
  );
  assert.equal(startCommand.response.type, InteractionResponseType.MODAL);
  const modalComponents = startCommand.response.data?.components as Array<{ type?: number }>;
  assert.equal(modalComponents[0]?.type, 18, "new Discord modals should wrap inputs in Label components");
  const submit = modalSubmit(
    "MODAL-START",
    modalCustomId(startCommand.response),
    "challenge",
    "How might our team reduce handoff confusion?",
  );
  const accepted = await adapter.route(submit);
  assert.equal(accepted.response.type, InteractionResponseType.DEFERRED_CHANNEL_MESSAGE_WITH_SOURCE);
  assert.equal(accepted.response.data?.flags, undefined, "workshop root must be public and threadable");
  assert.ok(accepted.afterResponse);
  await accepted.afterResponse();
  const card = api.messages.find((message) => message.channel === "THREAD-1");
  assert.ok(card, "a thread-scoped card should be posted when Discord permits a thread");
  const sessionId = /Session: `([^`]+)`/.exec(content(card.payload))?.[1];
  assert.match(sessionId ?? "", /^TW-[A-F0-9-]{36}$/);
  return { adapter, api, service, sessionId: sessionId! };
}

test("Discord command manifest matches registration code and requests no Message Content intent", async () => {
  const manifest = JSON.parse(
    await readFile(resolve("manifests/discord/application-command.json"), "utf8"),
  );
  assert.deepEqual(manifest, DESIGN_THINK_COMMAND);
  const install = JSON.parse(await readFile(resolve("manifests/discord/install.json"), "utf8"));
  assert.equal(install.application_name, "MightShape");
  assert.match(DESIGN_THINK_COMMAND.description, /MightShape/);
  assert.doesNotMatch(JSON.stringify({ manifest, install }), /Hunchgarden|Design Council/);
  assert.deepEqual(install.gateway_intents, []);
  assert.equal(install.message_content_intent, false);
  assert.deepEqual(install.oauth2_scopes, ["applications.commands", "bot"]);
  assert.deepEqual(
    DESIGN_THINK_COMMAND.options.map((option) => option.name),
    ["start", "status", "delete", "retry"],
  );
});

test("guild test registration strips global-only Discord command context fields", async (context) => {
  const prior = {
    application: process.env.DISCORD_APPLICATION_ID,
    token: process.env.DISCORD_BOT_TOKEN,
    guild: process.env.DISCORD_TEST_GUILD_ID,
  };
  context.after(() => {
    if (prior.application === undefined) delete process.env.DISCORD_APPLICATION_ID;
    else process.env.DISCORD_APPLICATION_ID = prior.application;
    if (prior.token === undefined) delete process.env.DISCORD_BOT_TOKEN;
    else process.env.DISCORD_BOT_TOKEN = prior.token;
    if (prior.guild === undefined) delete process.env.DISCORD_TEST_GUILD_ID;
    else process.env.DISCORD_TEST_GUILD_ID = prior.guild;
  });
  process.env.DISCORD_APPLICATION_ID = "123";
  process.env.DISCORD_BOT_TOKEN = "secret-test-token";
  process.env.DISCORD_TEST_GUILD_ID = "456";
  let body: Record<string, unknown> | undefined;
  const registered = await registerDiscordCommand(async (url, init) => {
    assert.match(String(url), /applications\/123\/guilds\/456\/commands$/);
    body = JSON.parse(String(init?.body));
    return new Response(JSON.stringify({ id: "789", name: "design-think" }), {
      status: 200,
      headers: { "Content-Type": "application/json" },
    });
  });
  assert.equal(registered.scope, "guild");
  assert.equal(body?.integration_types, undefined);
  assert.equal(body?.contexts, undefined);
  assert.equal(body?.name, "design-think");
});

test("/design-think start opens a setup modal and binds the public workshop to a thread", async () => {
  const { service, api, sessionId } = await startedWorkshop();
  const record = await service.get(sessionId);
  assert.equal(record.binding.platform, "DISCORD");
  assert.equal(record.binding.channel_ref, "CHANNEL-1");
  assert.equal(record.binding.conversation_ref, "THREAD-1");
  assert.equal(record.session.starting_point, "EARLY_HUNCH");
  assert.equal(record.session.visibility, "SEALED");
  assert.match(content(api.edits.at(-1)!.payload), /Continue together in <#THREAD-1>/);
  assert.deepEqual(api.edits.at(-1)!.payload.allowed_mentions, { parse: [], replied_user: false });
});

test("per-user modal contributions remain USER_PROVIDED and sealed until freeze", async () => {
  const { adapter, api, service, sessionId } = await startedWorkshop();
  const add = await adapter.route(component("BUTTON-ADD", `dc|add|${sessionId}`, "USER-2"));
  assert.equal(add.response.type, InteractionResponseType.MODAL);
  const submit = modalSubmit(
    "MODAL-CONTRIBUTION",
    modalCustomId(add.response),
    "contribution",
    "Make the next owner explicit at every handoff.",
    "USER-2",
    "THREAD-1",
  );
  const accepted = await adapter.route(submit);
  assert.equal(accepted.response.type, InteractionResponseType.DEFERRED_CHANNEL_MESSAGE_WITH_SOURCE);
  assert.equal(accepted.response.data?.flags, InteractionResponseFlags.EPHEMERAL);
  await accepted.afterResponse!();

  const record = await service.get(sessionId);
  assert.equal(record.session.participants.length, 2);
  assert.equal(record.session.contributions.length, 1);
  assert.equal(record.session.contributions[0]?.provenance, "USER_PROVIDED");
  assert.equal(record.session.contributions[0]?.revealed_at, null);
  assert.ok(
    api.messages.some((message) => content(message.payload).includes("sealed contribution")),
    "sealed progress should reveal the count but not the contribution text",
  );
  assert.ok(
    !api.messages.some((message) => content(message.payload).includes("Make the next owner")),
    "sealed content must not leak into the thread",
  );
});

test("interaction replay is acknowledged without scheduling the mutation twice", async () => {
  const { adapter, sessionId } = await startedWorkshop();
  const input = modalSubmit(
    "REPLAYED-MODAL",
    `dc|contribute|${sessionId}`,
    "contribution",
    "A single input",
    "USER-2",
    "THREAD-1",
  );
  const first = await adapter.route(input);
  const second = await adapter.route(input);
  assert.ok(first.afterResponse);
  assert.equal(second.afterResponse, undefined);
  assert.deepEqual(second.response, first.response);
});

test("concurrent duplicate Discord controls schedule at most one side effect", async () => {
  const { adapter, sessionId } = await startedWorkshop();
  const input = component("CONCURRENT-PASS", `dc|pass|${sessionId}`, "USER-2");
  const [first, second] = await Promise.all([adapter.route(input), adapter.route(structuredClone(input))]);
  assert.equal([first.afterResponse, second.afterResponse].filter(Boolean).length, 1);
  assert.deepEqual(first.response, second.response);
  await (first.afterResponse ?? second.afterResponse)!();
});

test("a teammate can pass without the facilitator fabricating a contribution", async () => {
  const { adapter, api, service, sessionId } = await startedWorkshop();
  const pass = await adapter.route(component("PASS-BUTTON", `dc|pass|${sessionId}`, "USER-2"));
  assert.equal(pass.response.type, InteractionResponseType.DEFERRED_CHANNEL_MESSAGE_WITH_SOURCE);
  await pass.afterResponse!();
  const record = await service.get(sessionId);
  assert.equal(record.session.contributions.length, 0);
  assert.equal(record.session.participants.find((participant) => participant.id === "TP-002")?.status, "PASSED");
  assert.match(content(api.edits.at(-1)!.payload), /Participation is optional/);
  assert.ok(api.messages.some((message) => content(message.payload).includes("no response was fabricated")));
});

test("only the initiator can freeze or close the exercise", async () => {
  const { adapter, api, service, sessionId } = await startedWorkshop();
  const contribution = await adapter.route(
    modalSubmit(
      "CONTRIB-FOR-CONTROL",
      `dc|contribute|${sessionId}`,
      "contribution",
      "A useful note",
      "USER-2",
      "THREAD-1",
    ),
  );
  await contribution.afterResponse!();
  const freeze = await adapter.route(component("FREEZE-BY-CONTRIBUTOR", `dc|freeze|${sessionId}`, "USER-2"));
  assert.equal(freeze.response.type, InteractionResponseType.DEFERRED_CHANNEL_MESSAGE_WITH_SOURCE);
  await freeze.afterResponse!();
  assert.match(content(api.edits.at(-1)!.payload), /Only the initiator or a delegated facilitator/);
  assert.equal((await service.get(sessionId)).session.status, "COLLECTING");

  const close = await adapter.route(component("CLOSE-BY-INITIATOR", `dc|close|${sessionId}`, "USER-1"));
  await close.afterResponse!();
  assert.equal((await service.get(sessionId)).session.status, "CLOSED");
});

test("Discord controls are rejected outside the exact bound thread or from an unrecorded message", async () => {
  const { adapter, service, sessionId } = await startedWorkshop();
  const wrongThread = component("WRONG-THREAD", `dc|freeze|${sessionId}`, "USER-1");
  wrongThread.channel_id = "CHANNEL-1";
  wrongThread.message = { id: "MSG-1", channel_id: "CHANNEL-1" };
  const wrongThreadResult = await adapter.route(wrongThread);
  assert.equal(wrongThreadResult.afterResponse, undefined);
  assert.equal(wrongThreadResult.response.data?.flags, InteractionResponseFlags.EPHEMERAL);
  assert.equal((await service.get(sessionId)).session.status, "COLLECTING");

  const forged = component("FORGED-CONTROL", `dc|freeze|${sessionId}`, "USER-1");
  forged.message = { id: "UNRECORDED-MESSAGE", channel_id: "THREAD-1" };
  const forgedResult = await adapter.route(forged);
  assert.equal(forgedResult.afterResponse, undefined);
  assert.equal(forgedResult.response.data?.flags, InteractionResponseFlags.EPHEMERAL);
  assert.equal((await service.get(sessionId)).session.status, "COLLECTING");
});

test("authorized freeze renders and posts an inline workshop PNG in the bound thread", async (context) => {
  const dataRoot = await mkdtemp(join(tmpdir(), "mightshape-discord-"));
  context.after(() => rm(dataRoot, { recursive: true, force: true }));
  const { adapter, api, service, sessionId } = await startedWorkshop(dataRoot);
  const contribution = await adapter.route(
    modalSubmit(
      "CONTRIB-FOR-VISUAL",
      `dc|contribute|${sessionId}`,
      "contribution",
      "Make ownership visible at the handoff.",
      "USER-2",
      "THREAD-1",
    ),
  );
  await contribution.afterResponse!();
  const freeze = await adapter.route(component("FREEZE-BY-INITIATOR", `dc|freeze|${sessionId}`, "USER-1"));
  await freeze.afterResponse!();
  assert.equal((await service.get(sessionId)).session.status, "REVIEW");
  assert.equal(api.uploads.length, 1);
  assert.equal(api.uploads[0]?.channel, "THREAD-1");
  assert.ok((api.uploads[0]?.bytes ?? 0) > 1_000);
  assert.match(api.uploads[0]?.alt ?? "", /sticky-note affinity map/i);
  assert.ok(api.messages.some((message) => content(message.payload).includes("Review")));
});

test("Discord delivery retry in REVIEW reuses the immutable visual and never re-synthesizes", async (context) => {
  const dataRoot = await mkdtemp(join(tmpdir(), "mightshape-discord-delivery-retry-"));
  context.after(() => rm(dataRoot, { recursive: true, force: true }));
  const delegate = new MockFacilitatorProvider();
  let synthesisCalls = 0;
  const facilitator: FacilitatorProvider = {
    async synthesize(session) {
      synthesisCalls += 1;
      return delegate.synthesize(session);
    },
  };
  const { adapter, api, service, sessionId } = await startedWorkshop(dataRoot, facilitator);
  const contribution = await adapter.route(
    modalSubmit(
      "CONTRIB-FOR-DELIVERY-RETRY",
      `dc|contribute|${sessionId}`,
      "contribution",
      "Keep the complete source wording stable across delivery retry.",
      "USER-2",
      "THREAD-1",
    ),
  );
  await contribution.afterResponse!();
  api.failUploadCount = 1;
  const freeze = await adapter.route(component("FREEZE-FOR-DELIVERY-RETRY", `dc|freeze|${sessionId}`, "USER-1"));
  await freeze.afterResponse!();
  assert.equal((await service.get(sessionId)).session.status, "REVIEW");
  assert.equal(synthesisCalls, 1);
  const sourceTextPosts = api.messages.filter((item) => content(item.payload).includes("complete source wording")).length;

  const retry = await adapter.route(component("RETRY-DELIVERY", `dc|retry|${sessionId}`, "USER-1"));
  await retry.afterResponse!();
  assert.equal(synthesisCalls, 1, "delivery retry must not call the facilitator again");
  assert.equal(api.uploads.length, 1);
  assert.equal(
    api.messages.filter((item) => content(item.payload).includes("complete source wording")).length,
    sourceTextPosts,
    "already-posted text chunks must not be duplicated",
  );
  const receipts = (await service.privateBinding(sessionId)).outbound_deliveries;
  assert.equal(receipts.find((item) => item.kind === "VISUAL")?.status, "POSTED");
});

test("Discord partial remote deletion retains retryable receipts and local state until cleanup succeeds", async () => {
  const { adapter, api, service, sessionId } = await startedWorkshop();
  api.failDeleteRefs.add("ROOT-1");
  const first = await adapter.route(component("DELETE-PARTIAL", `dc|delete|${sessionId}`, "USER-1"));
  await first.afterResponse!();
  const retained = await service.get(sessionId);
  assert.ok(retained.binding.outbound_deliveries.some((item) => item.status === "DELETE_FAILED"));
  assert.match(content(api.edits.at(-1)!.payload), /Partial cleanup/);

  api.failDeleteRefs.clear();
  const retryCommand = command("DELETE-RETRY", "delete", { session: sessionId });
  retryCommand.channel_id = "THREAD-1";
  const second = await adapter.route(retryCommand);
  await second.afterResponse!();
  await assert.rejects(service.get(sessionId), /not found/i);
  assert.match(content(api.edits.at(-1)!.payload), /cleanup completed/i);
});

test("Discord PNG upload is multipart, inline-previewable, accessible, and mention-safe", async () => {
  let request: RequestInit | undefined;
  const api = new DiscordRestApi("BOT-TOKEN", async (_url, init) => {
    request = init;
    return new Response(JSON.stringify({ id: "IMAGE-1", channel_id: "THREAD-1" }), {
      status: 200,
      headers: { "Content-Type": "application/json" },
    });
  });
  await api.uploadVisual("THREAD-1", {
    png: Buffer.from([137, 80, 78, 71]),
    alt_text: "A whimsical sticky-note affinity map with three source-linked clusters.",
    text_summary: "Three clusters; one contradiction; one outlier.\nNext move: test the handoff assumption.",
    artifact_ref: {
      artifact_id: "VA-123456789ABC",
      artifact_type: "AFFINITY_MAP",
      source_contribution_ids: ["UC-001"],
      png_sha256: "abc",
      alt_text: "A whimsical sticky-note affinity map with three source-linked clusters.",
      text_summary: "summary",
      recorded_at: "2026-08-14T12:00:00.000Z",
    },
  });
  assert.equal(request?.method, "POST");
  assert.ok(request?.body instanceof FormData);
  const payload = JSON.parse(String((request.body as FormData).get("payload_json")));
  assert.deepEqual(payload.allowed_mentions, { parse: [], replied_user: false });
  assert.equal(payload.enforce_nonce, true);
  assert.match(payload.nonce, /^[a-f0-9]{24}$/);
  assert.equal(payload.attachments[0].description, "A whimsical sticky-note affinity map with three source-linked clusters.");
  assert.ok((request.body as FormData).get("files[0]") instanceof Blob);
});

test("process-local interaction ledger returns exact acknowledgements for Discord retries", () => {
  const ledger = new DiscordInteractionLedger();
  const response = { type: InteractionResponseType.PONG };
  assert.equal(ledger.claim("I-1", response, 1_000), true);
  assert.equal(ledger.claim("I-1", response, 1_001), false);
  assert.deepEqual(ledger.replay("I-1"), response);
});

test("HTTP endpoint rejects unsigned requests and answers a signed Discord ping", async (context) => {
  const { privateKey, publicKey } = generateKeyPairSync("ed25519");
  const publicDer = publicKey.export({ format: "der", type: "spki" });
  const publicHex = publicDer.subarray(publicDer.byteLength - 32).toString("hex");
  const service = new WorkshopService(
    new MemoryWorkshopStore(),
    new MockFacilitatorProvider(),
    resolve(".test-data"),
  );
  const server = createDiscordHttpServer(new DiscordAdapter(service, new FakeDiscordApi()), publicHex);
  await new Promise<void>((accept, reject) => {
    server.once("error", reject);
    server.listen(0, "127.0.0.1", accept);
  });
  context.after(() => new Promise<void>((accept) => server.close(() => accept())));
  const address = server.address() as AddressInfo;
  const endpoint = `http://127.0.0.1:${address.port}/interactions`;
  const unsigned = await fetch(endpoint, { method: "POST", body: "{}" });
  assert.equal(unsigned.status, 401);

  const staleBody = Buffer.from(
    JSON.stringify({ id: "PING-STALE", application_id: "APP-1", token: "PING", type: InteractionType.PING }),
  );
  const staleTimestamp = String(Math.floor((Date.now() - 10 * 60_000) / 1_000));
  const staleSignature = sign(
    null,
    Buffer.concat([Buffer.from(staleTimestamp), staleBody]),
    privateKey,
  ).toString("hex");
  const stale = await fetch(endpoint, {
    method: "POST",
    headers: {
      "X-Signature-Ed25519": staleSignature,
      "X-Signature-Timestamp": staleTimestamp,
    },
    body: staleBody,
  });
  assert.equal(stale.status, 401);

  const body = Buffer.from(
    JSON.stringify({ id: "PING-1", application_id: "APP-1", token: "PING", type: InteractionType.PING }),
  );
  const timestamp = String(Math.floor(Date.now() / 1_000));
  const signature = sign(null, Buffer.concat([Buffer.from(timestamp), body]), privateKey).toString("hex");
  const ping = await fetch(endpoint, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Signature-Ed25519": signature,
      "X-Signature-Timestamp": timestamp,
    },
    body,
  });
  assert.equal(ping.status, 200);
  assert.deepEqual(await ping.json(), { type: InteractionResponseType.PONG });
});
