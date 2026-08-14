import assert from "node:assert/strict";
import { mkdtemp, readFile, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";
import type { App } from "@slack/bolt";
import type { WebClient } from "@slack/web-api";
import {
  cleanupSlackWorkshop,
  contributionModal,
  registerSlackHandlers,
  retryAndPublishSlack,
  setupWorkshopModal,
  uploadSlackPng,
  workshopRootBlocks,
} from "../src/adapters/slack.js";
import { createWorkshop } from "../src/core/session.js";
import { MockFacilitatorProvider } from "../src/core/facilitator.js";
import type { FacilitatorProvider } from "../src/core/facilitator.js";
import { WorkshopService } from "../src/core/service.js";
import { MemoryWorkshopStore } from "../src/core/store.js";
import type { RenderedWorkshopVisual } from "../src/core/visual.js";

test("Slack manifest uses Socket Mode and least-privilege interaction scopes", async () => {
  const manifest = await readFile("manifests/slack/manifest.yaml", "utf8");
  assert.match(manifest, /name: MightShape/);
  assert.doesNotMatch(manifest, /Hunchgarden|Design Council/);
  assert.match(manifest, /command: \/design-think/);
  assert.match(manifest, /socket_mode_enabled: true/);
  assert.match(manifest, /- commands\n/);
  assert.match(manifest, /- chat:write\n/);
  assert.match(manifest, /- files:write\n/);
  assert.doesNotMatch(manifest, /(?:channels|groups|im|mpim):history/);
  assert.doesNotMatch(manifest, /chat:write\.public/);
  assert.doesNotMatch(manifest, /event_subscriptions/);
});

test("setup modal explains the exercise and supports stage plus sealed or open input", () => {
  const modal = setupWorkshopModal({
    team_id: "T-1",
    channel_id: "C-1",
    initial_challenge: "Improve handoffs without assuming an app.",
  });
  assert.equal(modal.callback_id, "dc_setup_workshop");
  assert.equal(modal.blocks.length, 5);
  assert.match(JSON.stringify(modal), /Where is the idea now/);
  assert.match(JSON.stringify(modal), /Sealed until freeze/);
  assert.match(JSON.stringify(modal), /Improve handoffs without assuming an app/);
});

test("root card protects a sealed round and only exposes explicit controls", () => {
  const { session } = createWorkshop({
    platform: "SLACK",
    workspace_ref: "T-1",
    channel_ref: "C-1",
    actor_ref: "U-INITIATOR",
    challenge: "Reduce uncertainty during service handoffs.",
    exercise: "BRAINWRITING",
    visibility: "SEALED",
    event_id: "EV-START",
    now: "2026-08-14T12:00:00.000Z",
  });
  const encoded = JSON.stringify(workshopRootBlocks(session));
  assert.match(encoded, /SEALED · independent inputs/);
  assert.match(encoded, /dc_contribute/);
  assert.match(encoded, /dc_pass/);
  assert.match(encoded, /dc_freeze/);
  assert.match(encoded, /dc_close/);
  assert.match(encoded, /dc_delete/);
  assert.match(encoded, /\/design-think delete TW-/);
  assert.match(encoded, /does not read channel history/);
  assert.doesNotMatch(encoded, /U-INITIATOR/);
  assert.equal(contributionModal(session).callback_id, "dc_submit_contribution");
});

test("PNG upload uses Slack's external upload APIs with alt text and a thread destination", async () => {
  const calls: string[] = [];
  let uploaded = Buffer.alloc(0);
  const client = {
    files: {
      async getUploadURLExternal(args: { alt_text: string; length: number }) {
        calls.push(`ticket:${args.length}:${args.alt_text}`);
        return { ok: true, file_id: "F-1", upload_url: "https://files.slack.test/upload/once" };
      },
      async completeUploadExternal(args: { channel_id: string; thread_ts: string; files: [{ id: string }] }) {
        calls.push(`complete:${args.channel_id}:${args.thread_ts}:${args.files[0].id}`);
        return { ok: true };
      },
    },
  };
  const visual: RenderedWorkshopVisual = {
    artifact: {
      schema_version: "1.0.0",
      id: "VA-TEST",
      artifact_type: "AFFINITY_MAP",
      title: "Whimsical team affinity wall",
      summary: "Three source-linked notes in two provisional clusters.",
      summary_provenance: "DESIGN_COUNCIL",
      summary_record_ids: ["UC-001", "UC-002", "UC-003"],
      limitations: ["USER_PROVIDED workshop material, not human evidence."],
      data: {},
    },
    png: Buffer.from([137, 80, 78, 71]),
    png_path: "/private/not-shared.png",
    png_sha256: "abc",
    alt_text: "Sticky-note affinity map with three USER_PROVIDED contributions.",
    text_summary: "Text alternative",
    text_fallback: "Complete source-linked text alternative",
    artifact_ref: {
      artifact_id: "VA-TEST",
      artifact_type: "AFFINITY_MAP",
      source_contribution_ids: ["UC-001", "UC-002", "UC-003"],
      png_sha256: "abc",
      alt_text: "Sticky-note affinity map with three USER_PROVIDED contributions.",
      text_summary: "Text alternative",
      recorded_at: "2026-08-14T12:00:00.000Z",
    },
  };
  const result = await uploadSlackPng(
    client,
    visual,
    "C-1",
    "1755172800.000001",
    async (_url, init) => {
      calls.push("bytes");
      uploaded = Buffer.from(init?.body as Uint8Array);
      return new Response(null, { status: 200 });
    },
  );
  assert.deepEqual(uploaded, visual.png);
  assert.deepEqual(calls, [
    `ticket:4:${visual.alt_text}`,
    "bytes",
    "complete:C-1:1755172800.000001:F-1",
  ]);
  assert.equal(result.file_id, "F-1");
  assert.equal(result.upload_url_origin, "https://files.slack.test");
  assert.equal("upload" in client.files, false, "the retired files.upload method must not exist");
});

test("external byte delivery retries a transient upload without allocating duplicate Slack files", async () => {
  let tickets = 0;
  let uploads = 0;
  let completions = 0;
  const client = {
    files: {
      async getUploadURLExternal() {
        tickets += 1;
        return { ok: true, file_id: "F-RETRY", upload_url: "https://files.slack.test/upload/retry" };
      },
      async completeUploadExternal() {
        completions += 1;
        return { ok: true };
      },
    },
  };
  const visual = {
    artifact: {
      schema_version: "1.0.0",
      id: "VA-RETRY",
      artifact_type: "PROCESS_MAP",
      title: "Process map",
      summary: "A process map.",
      summary_provenance: "DESIGN_COUNCIL",
      summary_record_ids: ["UC-001"],
      limitations: [],
      data: {},
    },
    png: Buffer.from([1, 2, 3]),
    png_path: "/private/retry.png",
    png_sha256: "retry",
    alt_text: "A source-linked process map.",
    text_summary: "A source-linked process map.",
    text_fallback: "Complete source-linked process-map alternative.",
    artifact_ref: {
      artifact_id: "VA-RETRY",
      artifact_type: "PROCESS_MAP",
      source_contribution_ids: ["UC-001"],
      png_sha256: "retry",
      alt_text: "A source-linked process map.",
      text_summary: "A source-linked process map.",
      recorded_at: "2026-08-14T12:00:00.000Z",
    },
  } satisfies RenderedWorkshopVisual;
  await uploadSlackPng(client, visual, "C-1", "1.2", async () => {
    uploads += 1;
    return new Response(null, { status: uploads === 1 ? 503 : 200 });
  });
  assert.equal(tickets, 1);
  assert.equal(uploads, 2);
  assert.equal(completions, 1);
});

test("slash command acknowledges before opening the setup modal", async () => {
  const order: string[] = [];
  type Listener = (args: Record<string, unknown>) => Promise<void>;
  const commands = new Map<string, Listener>();
  const fakeApp = {
    command(name: string, listener: Listener) {
      commands.set(name, listener);
    },
    view() {},
    action() {},
  };
  registerSlackHandlers(fakeApp as unknown as App, {} as WorkshopService);
  const command = commands.get("/design-think");
  assert.ok(command);
  await command({
    command: {
      trigger_id: "TRIGGER-1",
      team_id: "T-1",
      channel_id: "C-1",
      user_id: "U-1",
      text: "A bounded challenge",
    },
    ack: async () => {
      order.push("ack");
    },
    client: {
      views: {
        open: async () => {
          order.push("open");
        },
      },
      chat: { postEphemeral: async () => undefined },
    } as unknown as WebClient,
    logger: { error: () => undefined },
  });
  assert.deepEqual(order, ["ack", "open"]);
});

test("setup and sealed contribution flow stays on one bound thread without message-history reads", async () => {
  type Listener = (args: Record<string, unknown>) => Promise<void>;
  const commands = new Map<string, Listener>();
  const views = new Map<string, Listener>();
  const actions = new Map<string, Listener>();
  const fakeApp = {
    command(name: string, listener: Listener) {
      commands.set(name, listener);
    },
    view(name: string, listener: Listener) {
      views.set(name, listener);
    },
    action(name: string, listener: Listener) {
      actions.set(name, listener);
    },
  };
  const store = new MemoryWorkshopStore();
  const service = new WorkshopService(store, new MockFacilitatorProvider());
  registerSlackHandlers(fakeApp as unknown as App, service);
  assert.equal(commands.size, 1);
  assert.equal(actions.size, 6);
  const eventOrder: string[] = [];
  let rootPosts = 0;
  let openContributionPosts = 0;
  let ephemeralReceipts = 0;
  const client = {
    chat: {
      postMessage: async (args: { thread_ts?: string }) => {
        if (args.thread_ts) openContributionPosts += 1;
        else rootPosts += 1;
        return { ok: true, ts: "1755172800.000001" };
      },
      postEphemeral: async () => {
        ephemeralReceipts += 1;
        return { ok: true };
      },
      update: async () => ({ ok: true }),
    },
  } as unknown as WebClient;
  const setup = views.get("dc_setup_workshop");
  assert.ok(setup);
  await setup({
    ack: async () => {
      eventOrder.push("setup-ack");
    },
    body: { user: { id: "U-INITIATOR" } },
    view: {
      id: "V-SETUP",
      private_metadata: JSON.stringify({ team_id: "T-1", channel_id: "C-1", initial_challenge: "" }),
      state: {
        values: {
          challenge_block: { challenge: { value: "Improve the handoff." } },
          exercise_block: { exercise: { selected_option: { value: "BRAINWRITING" } } },
          starting_block: { starting_point: { selected_option: { value: "EARLY_HUNCH" } } },
          visibility_block: { visibility: { selected_option: { value: "SEALED" } } },
        },
      },
    },
    client,
    logger: { error: () => undefined },
  });
  assert.equal(eventOrder[0], "setup-ack");
  assert.equal(rootPosts, 1);
  const record = await store.findByConversation("SLACK", "T-1", "C-1", "C-1");
  assert.ok(record);
  assert.equal(record.binding.root_message_ref, "1755172800.000001");

  const contribute = views.get("dc_submit_contribution");
  assert.ok(contribute);
  await contribute({
    ack: async () => {
      eventOrder.push("contribution-ack");
    },
    body: { team: { id: "T-1" }, user: { id: "U-TEAMMATE" } },
    view: {
      id: "V-CONTRIBUTION",
      private_metadata: JSON.stringify({
        session_id: record.session.id,
        team_id: "T-1",
        channel_id: "C-1",
        root_message_ref: "1755172800.000001",
      }),
      state: { values: { contribution_block: { contribution: { value: "Handoffs break at ownership changes." } } } },
    },
    client,
    logger: { error: () => undefined },
  });
  const updated = await service.get(record.session.id);
  assert.equal(eventOrder[1], "contribution-ack");
  assert.equal(updated.session.contributions.length, 1);
  assert.equal(updated.session.contributions[0]?.provenance, "USER_PROVIDED");
  assert.equal(updated.session.contributions[0]?.revealed_at, null);
  assert.equal(openContributionPosts, 0);
  assert.equal(ephemeralReceipts, 2, "the starter and sealed contributor each receive a private receipt");
});

test("replayed setup submission reuses one recorded Slack root", async () => {
  type Listener = (args: Record<string, unknown>) => Promise<void>;
  const views = new Map<string, Listener>();
  const fakeApp = {
    command() {},
    view(name: string, listener: Listener) { views.set(name, listener); },
    action() {},
  };
  const store = new MemoryWorkshopStore();
  const service = new WorkshopService(store, new MockFacilitatorProvider());
  registerSlackHandlers(fakeApp as unknown as App, service);
  let rootPosts = 0;
  const client = {
    chat: {
      postMessage: async () => ({ ok: true, ts: `ROOT-${++rootPosts}` }),
      postEphemeral: async () => ({ ok: true }),
      update: async () => ({ ok: true }),
    },
  } as unknown as WebClient;
  const args = {
    ack: async () => undefined,
    body: { user: { id: "U-OWNER" } },
    view: {
      id: "V-IDEMPOTENT-SETUP",
      private_metadata: JSON.stringify({ team_id: "T-1", channel_id: "C-1", initial_challenge: "" }),
      state: { values: {
        challenge_block: { challenge: { value: "Reduce handoff ambiguity." } },
        exercise_block: { exercise: { selected_option: { value: "BRAINWRITING" } } },
        starting_block: { starting_point: { selected_option: { value: "EARLY_HUNCH" } } },
        visibility_block: { visibility: { selected_option: { value: "SEALED" } } },
      } },
    },
    client,
    logger: { error: () => undefined },
  };
  const setup = views.get("dc_setup_workshop");
  assert.ok(setup);
  await setup(args);
  await setup(args);
  assert.equal(rootPosts, 1);
  // Stable workshop IDs are derived from the replayed setup event; conversation lookup
  // verifies the single portable/private record without coupling this test to the ID hash.
  const storeRecord = await store.findByConversation("SLACK", "T-1", "C-1", "C-1");
  assert.ok(storeRecord);
  assert.equal(storeRecord.binding.root_message_ref, "ROOT-1");
  assert.equal(storeRecord.binding.outbound_deliveries.filter((item) => item.id === "slack:root").length, 1);
  assert.equal(storeRecord.binding.outbound_deliveries[0]?.status, "POSTED");
});

test("Slack controls reject a forged action outside the bound root thread", async () => {
  type Listener = (args: Record<string, unknown>) => Promise<void>;
  const actions = new Map<string, Listener>();
  const fakeApp = {
    command() {},
    view() {},
    action(name: string, listener: Listener) { actions.set(name, listener); },
  };
  const service = new WorkshopService(new MemoryWorkshopStore(), new MockFacilitatorProvider());
  const started = await service.start({
    platform: "SLACK", workspace_ref: "T-1", channel_ref: "C-1", actor_ref: "OWNER",
    challenge: "Protect this workshop scope.", exercise: "BRAINWRITING", event_id: "START-SCOPE",
  });
  await service.bindRoot(started.session.id, "C-1", "ROOT-BOUND");
  registerSlackHandlers(fakeApp as unknown as App, service);
  let opened = 0;
  let warned = 0;
  await actions.get("dc_contribute")!({
    ack: async () => undefined,
    body: {
      team: { id: "T-1" }, channel: { id: "C-1" }, user: { id: "U-2" },
      container: { message_ts: "ROOT-FORGED" }, trigger_id: "TRIGGER-1",
    },
    action: { value: started.session.id },
    client: {
      views: { open: async () => { opened += 1; } },
      chat: { postEphemeral: async () => { warned += 1; } },
    } as unknown as WebClient,
    logger: { error: () => undefined },
  });
  assert.equal(opened, 0);
  assert.equal(warned, 1);
  assert.equal((await service.get(started.session.id)).session.contributions.length, 0);
});

test("review delivery retry reuses the immutable artifact without another facilitator call", async (t) => {
  const dataRoot = await mkdtemp(join(tmpdir(), "mightshape-slack-retry-"));
  t.after(async () => rm(dataRoot, { recursive: true, force: true }));
  let syntheses = 0;
  const base = new MockFacilitatorProvider();
  const facilitator: FacilitatorProvider = {
    async synthesize(session) {
      syntheses += 1;
      return base.synthesize(session);
    },
  };
  const service = new WorkshopService(new MemoryWorkshopStore(), facilitator, dataRoot);
  const started = await service.start({
    platform: "SLACK", workspace_ref: "T-1", channel_ref: "C-1", actor_ref: "OWNER",
    challenge: "Find a cheap coordination experiment.", exercise: "BRAINWRITING", event_id: "START-RETRY",
  });
  await service.bindRoot(started.session.id, "C-1", "ROOT-1");
  await service.contribute({
    session_id: started.session.id, actor_ref: "U-2", content: "Try a single shared intake address.", event_id: "NOTE-1",
  });
  await service.freeze({ session_id: started.session.id, actor_ref: "OWNER", event_id: "FREEZE-1" });
  const first = await service.synthesize(started.session.id, "SLACK");
  assert.equal(syntheses, 1);
  const client = {
    chat: {
      update: async () => ({ ok: true }),
      postMessage: async () => ({ ok: true, ts: `MSG-${Math.random()}` }),
    },
    files: {
      getUploadURLExternal: async () => ({ ok: true, file_id: "FILE-1", upload_url: "https://files.slack.test/upload" }),
      completeUploadExternal: async () => ({ ok: true }),
    },
  } as unknown as WebClient;
  await retryAndPublishSlack({
    service,
    client,
    session_id: started.session.id,
    actor_ref: "OWNER",
    event_id: "DELIVERY-RETRY-1",
    fetch_impl: async () => new Response(null, { status: 200 }),
  });
  assert.equal(syntheses, 1);
  assert.equal((await service.get(started.session.id)).session.artifacts.at(-1)?.artifact_id, first.visual.artifact_ref.artifact_id);
});

test("partial Slack cleanup retains retryable receipts and deletes the root last", async () => {
  const store = new MemoryWorkshopStore();
  const service = new WorkshopService(store, new MockFacilitatorProvider());
  const started = await service.start({
    platform: "SLACK", workspace_ref: "T-1", channel_ref: "C-1", actor_ref: "OWNER",
    challenge: "Delete safely.", exercise: "BRAINWRITING", event_id: "START-DELETE",
  });
  await service.bindRoot(started.session.id, "C-1", "ROOT-1");
  await service.claimOutboundDelivery(started.session.id, {
    id: "slack:root", kind: "ROOT", conversation_ref: "C-1", root_message_ref: "ROOT-1", artifact_id: null,
  });
  await service.completeOutboundDelivery(started.session.id, "slack:root", { message_ref: "ROOT-1", root_message_ref: "ROOT-1" });
  await service.claimOutboundDelivery(started.session.id, {
    id: "slack:child", kind: "SOURCE_SET", conversation_ref: "C-1", root_message_ref: "ROOT-1", artifact_id: null,
  });
  await service.completeOutboundDelivery(started.session.id, "slack:child", { message_ref: "CHILD-1" });
  let failChild = true;
  const deleted: string[] = [];
  const client = {
    chat: {
      delete: async ({ ts }: { ts: string }) => {
        deleted.push(ts);
        if (ts === "CHILD-1" && failChild) return { ok: false, error: "ratelimited" };
        return { ok: true };
      },
    },
    files: { delete: async () => ({ ok: true }) },
  } as unknown as WebClient;
  const partial = await cleanupSlackWorkshop({ service, client, session_id: started.session.id, actor_ref: "OWNER" });
  assert.equal(partial.complete, false);
  assert.deepEqual(deleted, ["CHILD-1"], "the root remains visible while a child cleanup is unresolved");
  const retained = await service.get(started.session.id);
  assert.equal(retained.binding.outbound_deliveries.find((item) => item.id === "slack:child")?.status, "DELETE_FAILED");
  assert.equal(retained.binding.outbound_deliveries.find((item) => item.id === "slack:root")?.status, "POSTED");

  failChild = false;
  const complete = await cleanupSlackWorkshop({ service, client, session_id: started.session.id, actor_ref: "OWNER" });
  assert.equal(complete.complete, true);
  assert.deepEqual(deleted, ["CHILD-1", "CHILD-1", "ROOT-1"]);
  await assert.rejects(service.get(started.session.id), /not found/i);
});
