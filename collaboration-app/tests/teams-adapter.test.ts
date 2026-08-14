import assert from "node:assert/strict";
import { mkdtemp, readFile, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";
import test from "node:test";
import sharp from "sharp";
import {
  TeamsWorkshopAdapter,
  aiCardMessage,
  contributionDialogCard,
  cleanupTeamsWorkshop,
  deliverTeamsVisual,
  parseTeamsCommand,
  visualCard,
  workshopCard,
  type TeamsInvocation,
  type TeamsOutboundPort,
} from "../src/adapters/teams.js";
import { MockFacilitatorProvider, type FacilitatorProvider } from "../src/core/facilitator.js";
import { WorkshopService } from "../src/core/service.js";
import { WorkshopError } from "../src/core/session.js";
import { MemoryWorkshopStore } from "../src/core/store.js";
import type { RenderedWorkshopVisual } from "../src/core/visual.js";
import { buildTeamsPackage } from "../scripts/build-teams-package.js";

function invocation(actor = "TEAMS-USER-1", event = "TEAMS-EVENT-1"): TeamsInvocation {
  return {
    workspace_id: "TENANT-1",
    channel_id: "CHANNEL-1",
    conversation_id: "19:channel@thread.tacv2",
    root_message_id: "1755172800000",
    actor_id: actor,
    event_id: event,
  };
}

class FakeTeamsOutboundPort implements TeamsOutboundPort {
  replies: Array<{ conversation: string; root: string; message: unknown; id: string }> = [];
  deletions: Array<{ conversation: string; message: string }> = [];
  failVisualCount = 0;
  failDeleteRefs = new Set<string>();

  async reply(
    conversationId: string,
    rootMessageId: string,
    message: Parameters<TeamsOutboundPort["reply"]>[2],
  ) {
    if (this.failVisualCount > 0 && JSON.stringify(message).includes("data:image/png;base64")) {
      this.failVisualCount -= 1;
      throw new Error("simulated Teams visual failure");
    }
    const id = `TEAMS-MSG-${this.replies.length + 1}`;
    this.replies.push({ conversation: conversationId, root: rootMessageId, message, id });
    return { id };
  }

  async deleteActivity(conversationId: string, messageId: string) {
    this.deletions.push({ conversation: conversationId, message: messageId });
    if (this.failDeleteRefs.has(messageId)) throw new Error("simulated Teams deletion failure");
  }
}

function storedZipFiles(zip: Buffer): Map<string, Buffer> {
  const files = new Map<string, Buffer>();
  let offset = 0;
  while (offset + 4 <= zip.byteLength && zip.readUInt32LE(offset) === 0x04034b50) {
    const compressed = zip.readUInt32LE(offset + 18);
    const nameLength = zip.readUInt16LE(offset + 26);
    const extraLength = zip.readUInt16LE(offset + 28);
    const nameStart = offset + 30;
    const dataStart = nameStart + nameLength + extraLength;
    const name = zip.subarray(nameStart, nameStart + nameLength).toString("utf8");
    files.set(name, zip.subarray(dataStart, dataStart + compressed));
    offset = dataStart + compressed;
  }
  return files;
}

test("Teams command parser supports mention-first starts and bounded controls", () => {
  assert.deepEqual(
    parseTeamsCommand("start affinity | Map the actual onboarding handoffs"),
    {
      action: "START",
      exercise: "AFFINITY_CLUSTERING",
      challenge: "Map the actual onboarding handoffs",
    },
  );
  assert.deepEqual(parseTeamsCommand("start How might we reduce handoff ambiguity?"), {
    action: "START",
    exercise: "BRAINSTORMING",
    challenge: "How might we reduce handoff ambiguity?",
  });
  const sessionId = "TW-AAAAAAAA-BBBB-4CCC-8DDD-EEEEEEEEEEEE";
  assert.deepEqual(parseTeamsCommand(`add ${sessionId} One atomic note`), {
    action: "ADD",
    session_id: sessionId,
    content: "One atomic note",
  });
  assert.deepEqual(parseTeamsCommand(`freeze ${sessionId}`), { action: "FREEZE", session_id: sessionId });
  assert.deepEqual(parseTeamsCommand(`pass ${sessionId}`), { action: "PASS", session_id: sessionId });
  assert.deepEqual(parseTeamsCommand(`close ${sessionId}`), { action: "CLOSE", session_id: sessionId });
  assert.deepEqual(parseTeamsCommand(`delete ${sessionId}`), { action: "DELETE", session_id: sessionId });
});

test("a Teams participant can pass without fabricating a contribution", async () => {
  const service = new WorkshopService(new MemoryWorkshopStore(), new MockFacilitatorProvider());
  const adapter = new TeamsWorkshopAdapter(service);
  const started = await adapter.handle(
    { action: "START", exercise: "BRAINWRITING", challenge: "Create independent handoff ideas." },
    invocation(),
  );
  assert.equal(started.action, "STARTED");
  if (started.action !== "STARTED") assert.fail("workshop did not start");

  const result = await adapter.handle(
    { action: "PASS", session_id: started.session.id },
    invocation("TEAMS-USER-2", "TEAMS-PASS-1"),
  );
  assert.equal(result.action, "PASSED");
  if (result.action !== "PASSED") assert.fail("pass was not recorded");
  assert.equal(result.session.contributions.length, 0);
  assert.equal(result.session.participants.find((participant) => participant.id === "TP-002")?.status, "PASSED");
});

test("one Teams member starts a thread-bound workshop without platform IDs entering portable state", async () => {
  const service = new WorkshopService(new MemoryWorkshopStore(), new MockFacilitatorProvider());
  const adapter = new TeamsWorkshopAdapter(service);
  const result = await adapter.handle(
    parseTeamsCommand("start brainwriting | Reimagine the project handoff"),
    invocation(),
  );
  assert.equal(result.action, "STARTED");
  if (result.action !== "STARTED") assert.fail("workshop did not start");
  assert.equal(result.session.visibility, "SEALED");
  assert.equal(result.session.initiator_participant_id, "TP-001");
  const binding = await service.privateBinding(result.session.id);
  assert.equal(binding.platform, "TEAMS");
  assert.equal(binding.workspace_ref, "TENANT-1");
  assert.equal(binding.channel_ref, "CHANNEL-1");
  assert.equal(binding.conversation_ref, "19:channel@thread.tacv2");
  assert.equal(binding.root_message_ref, "1755172800000");
  assert.doesNotMatch(JSON.stringify(await service.exportPortable(result.session.id)), /TEAMS-USER|TENANT-1|CHANNEL-1/);
});

test("private dialog participation stays USER_PROVIDED and sealed until initiator freeze", async () => {
  const service = new WorkshopService(new MemoryWorkshopStore(), new MockFacilitatorProvider());
  const adapter = new TeamsWorkshopAdapter(service);
  const started = await adapter.handle(
    { action: "START", exercise: "BRAINWRITING", challenge: "Create non-obvious handoff mechanisms." },
    invocation(),
  );
  assert.equal(started.action, "STARTED");
  if (started.action !== "STARTED") assert.fail("workshop did not start");
  const sessionId = started.session.id;

  await assert.rejects(
    adapter.handle(
      { action: "ADD", session_id: sessionId, content: "This would leak in a channel mention." },
      invocation("TEAMS-USER-2", "LEAK-ATTEMPT"),
    ),
    (error: unknown) => error instanceof WorkshopError && error.code === "SEALED_INPUT_REQUIRES_DIALOG",
  );

  await adapter.contributeFromDialog(
    sessionId,
    "Let the receiver rewrite the handoff in their own words.",
    invocation("TEAMS-USER-2", "DIALOG-SUBMIT-1"),
  );
  const contributed = await service.get(sessionId);
  assert.equal(contributed.session.participants.length, 2);
  assert.equal(contributed.session.contributions[0]?.provenance, "USER_PROVIDED");
  assert.equal(contributed.session.contributions[0]?.revealed_at, null);

  await assert.rejects(
    adapter.handle({ action: "FREEZE", session_id: sessionId }, invocation("TEAMS-USER-2", "FREEZE-BAD")),
    (error: unknown) => error instanceof WorkshopError && error.code === "CONTROL_FORBIDDEN",
  );
  const frozen = await adapter.handle(
    { action: "FREEZE", session_id: sessionId },
    invocation("TEAMS-USER-1", "FREEZE-GOOD"),
  );
  assert.equal(frozen.action, "FROZEN");
  if (frozen.action !== "FROZEN") assert.fail("workshop did not freeze");
  assert.ok(frozen.session.contributions.every((item) => item.revealed_at !== null));
});

test("session IDs cannot be replayed from a different tenant, channel, or conversation", async () => {
  const service = new WorkshopService(new MemoryWorkshopStore(), new MockFacilitatorProvider());
  const adapter = new TeamsWorkshopAdapter(service);
  const started = await adapter.handle(
    { action: "START", exercise: "PROCESS_RECONSTRUCTION", challenge: "Map the current flow." },
    invocation(),
  );
  assert.equal(started.action, "STARTED");
  if (started.action !== "STARTED") assert.fail("workshop did not start");
  await assert.rejects(
    adapter.contributeFromDialog(
      started.session.id,
      "A cross-channel injection",
      { ...invocation("ATTACKER", "CROSS-CHANNEL"), channel_id: "CHANNEL-2" },
    ),
    (error: unknown) => error instanceof WorkshopError && error.code === "CONTEXT_MISMATCH",
  );
  await assert.rejects(
    adapter.contributeFromDialog(
      started.session.id,
      "A same-channel but different-thread injection",
      { ...invocation("ATTACKER", "CROSS-THREAD"), root_message_id: "DIFFERENT-ROOT" },
    ),
    (error: unknown) => error instanceof WorkshopError && error.code === "CONTEXT_MISMATCH",
  );
  assert.equal((await service.get(started.session.id)).session.contributions.length, 0);
});

test("Teams cards make opt-in, control, provenance, accessibility, and AI disclosure inspectable", async () => {
  const service = new WorkshopService(new MemoryWorkshopStore(), new MockFacilitatorProvider());
  const started = await service.start({
    platform: "TEAMS",
    workspace_ref: "TENANT-1",
    channel_ref: "CHANNEL-1",
    actor_ref: "TEAMS-USER-1",
    challenge: "Map the missing context in a handoff.",
    exercise: "BRAINWRITING",
    event_id: "START-CARD",
  });
  const root = JSON.stringify(workshopCard(started.session));
  assert.match(root, /Add my input/);
  assert.match(root, /Freeze & synthesize/);
  assert.match(root, /USER_PROVIDED/);
  assert.match(root, /not human research evidence/i);
  assert.match(root, /Delete workshop data/);
  assert.match(root, /best effort/i);

  const dialog = JSON.stringify(contributionDialogCard(started.session));
  assert.match(dialog, /submitted privately/);
  assert.match(dialog, /Your contribution/);
  assert.match(dialog, /isRequired/);
  assert.doesNotMatch(dialog, /TEAMS-USER-1/);

  const visual: RenderedWorkshopVisual = {
    artifact: {
      schema_version: "1.0.0",
      id: "VA-TEAMS",
      artifact_type: "AFFINITY_MAP",
      title: "Whimsical team affinity wall",
      summary: "Two source-linked notes remain visible.",
      summary_provenance: "DESIGN_COUNCIL",
      summary_record_ids: ["UC-001", "UC-002"],
      limitations: ["USER_PROVIDED workshop material, not human evidence."],
      data: {},
    },
    png: Buffer.from([137, 80, 78, 71]),
    png_path: "/private/not-shared.png",
    png_sha256: "abc",
    alt_text: "Sticky-note affinity map with two USER_PROVIDED contributions.",
    text_summary: "Two notes form one provisional cluster. Next move: test the boundary.",
    text_fallback: "UC-001 · USER_PROVIDED\nFirst source note.\n\nUC-002 · USER_PROVIDED\nSecond source note.",
    artifact_ref: {
      artifact_id: "VA-TEAMS",
      artifact_type: "AFFINITY_MAP",
      source_contribution_ids: ["UC-001", "UC-002"],
      png_sha256: "abc",
      alt_text: "Sticky-note affinity map with two USER_PROVIDED contributions.",
      text_summary: "Two notes form one provisional cluster. Next move: test the boundary.",
      recorded_at: "2026-08-14T12:00:00.000Z",
    },
  };
  const rendered = visualCard(visual);
  const encoded = JSON.stringify(rendered);
  assert.match(encoded, /data:image\/png;base64/);
  assert.match(encoded, /Sticky-note affinity map/);
  assert.match(encoded, /Provenance/);
  assert.match(encoded, /text summary|Two notes form/i);
  assert.match(JSON.stringify(aiCardMessage(rendered, visual.text_summary)), /AIGeneratedContent/);
});

test("Teams visual delivery stays inside the safe activity budget at declared field limits", () => {
  const visual: RenderedWorkshopVisual = {
    artifact: {
      schema_version: "1.0.0",
      id: "VA-TEAMS-LIMIT",
      artifact_type: "AFFINITY_MAP",
      title: "T".repeat(200),
      summary: "S".repeat(1_000),
      summary_provenance: "DESIGN_COUNCIL",
      summary_record_ids: ["UC-001"],
      limitations: ["USER_PROVIDED workshop material, not human evidence."],
      data: {},
    },
    png: Buffer.alloc(47_999, 0xff),
    png_path: "/private/bounded.png",
    png_sha256: "bounded",
    alt_text: "A".repeat(1_000),
    text_summary: "M".repeat(5_000),
    text_fallback: `COMPLETE-SOURCE-SENTINEL\n${"full source wording ".repeat(5_000)}`,
    artifact_ref: {
      artifact_id: "VA-TEAMS-LIMIT",
      artifact_type: "AFFINITY_MAP",
      source_contribution_ids: ["UC-001"],
      png_sha256: "bounded",
      alt_text: "A".repeat(1_000),
      text_summary: "M".repeat(5_000),
      recorded_at: "2026-08-14T12:00:00.000Z",
    },
  };
  const message = aiCardMessage(
    visualCard(visual),
    `${visual.alt_text}\nThe complete source-linked text alternative follows in the workshop thread.`,
  );
  const encoded = JSON.stringify(message);
  assert.ok(Buffer.byteLength(encoded, "utf8") <= 80_000);
  assert.doesNotMatch(encoded, /COMPLETE-SOURCE-SENTINEL/);
});

test("Teams rejects a raw PNG that would overflow the bounded inline-card budget", () => {
  const visual = {
    artifact: {
      schema_version: "1.0.0",
      id: "VA-TEAMS-TOO-LARGE",
      artifact_type: "AFFINITY_MAP",
      title: "Bounded visual",
      summary: "Summary",
      summary_provenance: "DESIGN_COUNCIL",
      summary_record_ids: ["UC-001"],
      limitations: [],
      data: {},
    },
    png: Buffer.alloc(48_001),
    png_path: "/private/too-large.png",
    png_sha256: "too-large",
    alt_text: "Source-linked visual",
    text_summary: "UC-001",
    text_fallback: "UC-001 · USER_PROVIDED\nComplete source wording.",
    artifact_ref: {
      artifact_id: "VA-TEAMS-TOO-LARGE",
      artifact_type: "AFFINITY_MAP",
      source_contribution_ids: ["UC-001"],
      png_sha256: "too-large",
      alt_text: "Source-linked visual",
      text_summary: "UC-001",
      recorded_at: "2026-08-14T12:00:00.000Z",
    },
  } satisfies RenderedWorkshopVisual;
  assert.throws(() => visualCard(visual), /exceeds 48000 bytes/);
});

test("Teams delivery retry in REVIEW reuses the immutable visual, avoids duplicate text, and never re-synthesizes", async (context) => {
  const dataRoot = await mkdtemp(join(tmpdir(), "mightshape-teams-delivery-"));
  context.after(async () => rm(dataRoot, { recursive: true, force: true }));
  const delegate = new MockFacilitatorProvider();
  let synthesisCalls = 0;
  const facilitator: FacilitatorProvider = {
    async synthesize(session) {
      synthesisCalls += 1;
      return delegate.synthesize(session);
    },
  };
  const service = new WorkshopService(new MemoryWorkshopStore(), facilitator, dataRoot);
  const started = await service.start({
    platform: "TEAMS",
    workspace_ref: "TENANT-1",
    channel_ref: "CHANNEL-1",
    conversation_ref: "19:channel@thread.tacv2",
    root_message_ref: "1755172800000",
    actor_ref: "TEAMS-USER-1",
    challenge: "Keep a retry from changing the team's synthesis.",
    exercise: "BRAINWRITING",
    event_id: "TEAMS-DELIVERY-START",
  });
  await service.contribute({
    session_id: started.session.id,
    actor_ref: "TEAMS-USER-2",
    content: "Preserve this complete source sentence across every retry.",
    event_id: "TEAMS-DELIVERY-CONTRIBUTION",
  });
  await service.freeze({
    session_id: started.session.id,
    actor_ref: "TEAMS-USER-1",
    event_id: "TEAMS-DELIVERY-FREEZE",
  });
  const synthesized = await service.synthesize(started.session.id, "TEAMS");
  const port = new FakeTeamsOutboundPort();
  port.failVisualCount = 1;
  const initialFailures = await deliverTeamsVisual(port, service, synthesized.record, synthesized.visual);
  assert.ok(initialFailures > 0);
  assert.equal(synthesisCalls, 1);
  const sourceTextPosts = port.replies.filter((item) => JSON.stringify(item.message).includes("complete source sentence")).length;

  const loaded = await service.loadLatestVisual({
    session_id: started.session.id,
    actor_ref: "TEAMS-USER-1",
    event_id: "TEAMS-DELIVERY-RETRY",
  });
  const retryFailures = await deliverTeamsVisual(port, service, loaded.record, loaded.visual);
  assert.equal(retryFailures, 0);
  assert.equal(synthesisCalls, 1, "delivery retry must not call the facilitator again");
  assert.equal(
    port.replies.filter((item) => JSON.stringify(item.message).includes("complete source sentence")).length,
    sourceTextPosts,
    "already-posted text fallback chunks must not be duplicated",
  );
  assert.equal(
    (await service.privateBinding(started.session.id)).outbound_deliveries.find((item) => item.kind === "VISUAL")?.status,
    "POSTED",
  );
});

test("Teams partial remote cleanup retains local state and retryable receipts until all deletions succeed", async () => {
  const service = new WorkshopService(new MemoryWorkshopStore(), new MockFacilitatorProvider());
  const started = await service.start({
    platform: "TEAMS",
    workspace_ref: "TENANT-1",
    channel_ref: "CHANNEL-1",
    conversation_ref: "19:channel@thread.tacv2",
    root_message_ref: "1755172800000",
    actor_ref: "TEAMS-USER-1",
    challenge: "Delete recorded bot output without overstating platform guarantees.",
    exercise: "AFFINITY_CLUSTERING",
    event_id: "TEAMS-CLEANUP-START",
  });
  const claim = await service.claimOutboundDelivery(started.session.id, {
    id: "teams:control:initial",
    kind: "CONTROL",
    conversation_ref: "19:channel@thread.tacv2",
    root_message_ref: "1755172800000",
    artifact_id: null,
  });
  assert.equal(claim.claimed, true);
  await service.completeOutboundDelivery(started.session.id, claim.receipt.id, { message_ref: "TEAMS-MSG-1" });
  const port = new FakeTeamsOutboundPort();
  port.failDeleteRefs.add("TEAMS-MSG-1");
  const partial = await cleanupTeamsWorkshop(port, service, started.session.id, "TEAMS-USER-1");
  assert.deepEqual(partial, { complete: false, failed: 1, tracked: 1 });
  assert.equal((await service.privateBinding(started.session.id)).outbound_deliveries[0]?.status, "DELETE_FAILED");

  port.failDeleteRefs.clear();
  const completed = await cleanupTeamsWorkshop(port, service, started.session.id, "TEAMS-USER-1");
  assert.deepEqual(completed, { complete: true, failed: 0, tracked: 1 });
  await assert.rejects(service.get(started.session.id), /not found/i);
});

test("Teams manifest is 1.29, team-only, and requests no Graph, RSC, or channel-history access", async () => {
  const manifest = await readFile(resolve("manifests/teams/manifest.template.json"), "utf8");
  assert.match(manifest, /"manifestVersion": "1\.29"/);
  const parsed = JSON.parse(manifest) as Record<string, unknown>;
  assert.deepEqual(parsed.name, { short: "MightShape", full: "MightShape Collaborative Workshops" });
  assert.doesNotMatch(manifest, /Hunchgarden|Design Council/);
  const bots = parsed.bots as Array<Record<string, unknown>>;
  assert.deepEqual(bots[0]?.scopes, ["team"]);
  assert.equal(parsed.defaultInstallScope, "team");
  assert.equal("permissions" in parsed, false);
  assert.equal("authorization" in parsed, false);
  assert.equal("validDomains" in parsed, false);
  assert.doesNotMatch(manifest, /ChannelMessage\.Read|TeamSettings|webApplicationInfo|supportsChannelFeatures/);
});

test("Teams package builder emits a root manifest and compliant PNG icons without secrets", async (context) => {
  const root = await mkdtemp(join(tmpdir(), "dc-teams-package-"));
  context.after(async () => rm(root, { recursive: true, force: true }));
  const output = join(root, "mightshape-teams.zip");
  const appId = "aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee";
  const result = await buildTeamsPackage({ appId, version: "1.0.1", outputPath: output });
  const files = storedZipFiles(await readFile(output));
  assert.deepEqual([...files.keys()], ["manifest.json", "color.png", "outline.png"]);
  const manifest = JSON.parse(files.get("manifest.json")!.toString("utf8"));
  assert.equal(manifest.id, appId);
  assert.equal(manifest.bots[0].botId, appId);
  assert.equal(manifest.version, "1.0.1");
  assert.deepEqual(manifest.name, { short: "MightShape", full: "MightShape Collaborative Workshops" });
  assert.equal(JSON.stringify(manifest).includes("SECRET"), false);
  const color = await sharp(files.get("color.png")!).metadata();
  const outline = await sharp(files.get("outline.png")!).metadata();
  assert.deepEqual([color.width, color.height], [192, 192]);
  assert.deepEqual([outline.width, outline.height], [32, 32]);
  assert.equal(outline.hasAlpha, true);
  assert.deepEqual(result.files.map((item) => item.name), ["manifest.json", "color.png", "outline.png"]);
});
