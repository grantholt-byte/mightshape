import assert from "node:assert/strict";
import test from "node:test";
import {
  MockFacilitatorProvider,
  OpenAIFacilitatorProvider,
  validateWorkshopSynthesis,
} from "../src/core/facilitator.js";
import { addContribution, createWorkshop, freezeWorkshop } from "../src/core/session.js";

function frozenSession() {
  const created = createWorkshop({
    platform: "SLACK",
    workspace_ref: "T1",
    channel_ref: "C1",
    actor_ref: "U1",
    challenge: "How might a team preserve context without adding ceremony?",
    exercise: "BRAINWRITING",
    event_id: "START",
    now: "2026-08-14T12:00:00Z",
  });
  const first = addContribution(created.session, created.binding, {
    session_id: created.session.id,
    actor_ref: "U2",
    content: "Let the receiver write the handoff summary.",
    event_id: "NOTE-1",
    now: "2026-08-14T12:01:00Z",
  });
  const second = addContribution(first.session, first.binding, {
    session_id: created.session.id,
    actor_ref: "U3",
    content: "Carry the unresolved question with the work item.",
    event_id: "NOTE-2",
    now: "2026-08-14T12:02:00Z",
  });
  return freezeWorkshop(second.session, second.binding, {
    session_id: created.session.id,
    actor_ref: "U1",
    event_id: "FREEZE",
    now: "2026-08-14T12:03:00Z",
  }).session;
}

function outputFor(session: ReturnType<typeof frozenSession>, artifactId: string, provenance = "USER_PROVIDED") {
  const notes = session.contributions.map((item) => ({
    id: item.id,
    text: item.content,
    provenance,
    source_ids: [item.id],
  }));
  return {
    artifact: {
      schema_version: "1.0.0",
      id: artifactId,
      artifact_type: "AFFINITY_MAP",
      title: "Handoff ideas",
      summary: "Two distinct mechanisms preserve context at the transfer boundary.",
      summary_provenance: "DESIGN_COUNCIL",
      summary_record_ids: session.contributions.map((item) => item.id),
      mode: "IDEATE",
      cycle: 1,
      limitations: [
        "These USER_PROVIDED workshop inputs are not human interview or observed-behavior evidence.",
      ],
      data: {
        clusters: [
          {
            id: "CLUSTER-HANDOFF",
            label: "Move context into the transfer",
            description: "The receiver and work item each become carriers of unresolved context.",
            interpretation_provenance: "DESIGN_COUNCIL",
            record_ids: notes.map((item) => item.id),
            notes,
          },
        ],
        outliers: [],
      },
    },
    synthesis: "The source set contains two complementary handoff mechanisms.",
    tensions: ["Receiver effort versus sender control"],
    outlier_worth_saving: null,
    next_move: "Role-play both handoffs and watch where context is lost.",
  };
}

function fakeFetch(
  session: ReturnType<typeof frozenSession>,
  mutate?: (output: ReturnType<typeof outputFor>) => void,
): { fetchImpl: typeof fetch; requests: Array<Record<string, unknown>> } {
  const requests: Array<Record<string, unknown>> = [];
  const fetchImpl = async (_input: string | URL | Request, init?: RequestInit) => {
    const request = JSON.parse(String(init?.body)) as Record<string, unknown>;
    requests.push(request);
    const instructions = String(request.instructions);
    const artifactId = /artifact id must be (VA-[A-Z0-9-]+)/.exec(instructions)?.[1];
    assert.ok(artifactId);
    const output = outputFor(session, artifactId);
    mutate?.(output);
    return new Response(
      JSON.stringify({
        status: "completed",
        output: [{ type: "message", content: [{ type: "output_text", text: JSON.stringify(output) }] }],
      }),
      { status: 200, headers: { "content-type": "application/json" } },
    );
  };
  return { fetchImpl: fetchImpl as typeof fetch, requests };
}

test("OpenAI facilitation uses strict non-stored output and validates a source-locked result", async () => {
  const session = frozenSession();
  const fake = fakeFetch(session);
  const provider = new OpenAIFacilitatorProvider({ apiKey: "test-only", fetchImpl: fake.fetchImpl });
  const result = await provider.synthesize(session);
  assert.equal(result.artifact.artifact_type, "AFFINITY_MAP");
  assert.deepEqual(result.artifact.summary_record_ids, ["UC-001", "UC-002"]);
  assert.equal(fake.requests.length, 1);
  assert.equal(fake.requests[0]?.store, false);
  assert.equal(fake.requests[0]?.model, "gpt-5.6-sol");
  const text = fake.requests[0]?.text as Record<string, unknown>;
  const format = text.format as Record<string, unknown>;
  assert.equal(format.type, "json_schema");
  assert.equal(format.strict, true);
});

test("runtime evidence validation rejects a model response that relabels team input", async () => {
  const session = frozenSession();
  const fake = fakeFetch(session, (output) => {
    output.artifact.data.clusters[0]!.notes[0]!.provenance = "HUMAN_INTERVIEW";
  });
  const provider = new OpenAIFacilitatorProvider({ apiKey: "test-only", fetchImpl: fake.fetchImpl });
  await assert.rejects(provider.synthesize(session), /provenance must remain USER_PROVIDED/);
});

function frozenProcessSession() {
  const created = createWorkshop({
    platform: "TEAMS",
    workspace_ref: "TENANT-1",
    channel_ref: "CHANNEL-1",
    actor_ref: "OWNER",
    challenge: "Reconstruct the actual handoff.",
    exercise: "PROCESS_RECONSTRUCTION",
    event_id: "PROCESS-START",
    now: "2026-08-14T12:00:00Z",
  });
  const first = addContribution(created.session, created.binding, {
    session_id: created.session.id,
    actor_ref: "U2",
    content: "The sender writes the unresolved question beside the work item.",
    event_id: "PROCESS-1",
  });
  const second = addContribution(first.session, first.binding, {
    session_id: created.session.id,
    actor_ref: "U3",
    content: "The receiver restates what they believe must happen next.",
    event_id: "PROCESS-2",
  });
  return freezeWorkshop(second.session, second.binding, {
    session_id: created.session.id,
    actor_ref: "OWNER",
    event_id: "PROCESS-FREEZE",
  }).session;
}

function processOutput(session: ReturnType<typeof frozenProcessSession>) {
  return {
    artifact: {
      schema_version: "1.0.0" as const,
      id: "VA-PROCESS-TEST",
      artifact_type: "PROCESS_MAP" as const,
      title: "Handoff reconstruction",
      summary: "Two supplied steps with one unvalidated ordering assumption.",
      summary_provenance: "DESIGN_COUNCIL" as const,
      summary_record_ids: session.contributions.map((item) => item.id),
      mode: "DEFINE" as const,
      cycle: 1,
      limitations: ["USER_PROVIDED workshop material is not human interview evidence."],
      data: {
        lanes: [{ id: "LANE-UNKNOWN", label: "Actor not established" }],
        steps: session.contributions.map((item) => ({
          id: item.id,
          label: item.content.slice(0, 160),
          detail: item.content,
          lane_id: "LANE-UNKNOWN",
          provenance: "USER_PROVIDED",
          source_ids: [item.id],
        })),
        transitions: [
          {
            id: "FLOW-001",
            from_step_id: "UC-001",
            to_step_id: "UC-002",
            label: "possible sequence",
            provenance: "ASSUMPTION",
            source_ids: ["UC-001", "UC-002"],
          },
        ],
      },
    },
    synthesis: "The order remains an assumption.",
    tensions: [],
    outlier_worth_saving: null,
    next_move: "Ask the team to reconstruct one recent handoff chronologically.",
  };
}

test("team process maps keep verbatim step labels and inferred transitions out of USER_PROVIDED provenance", () => {
  const session = frozenProcessSession();
  const valid = processOutput(session);
  assert.equal(validateWorkshopSynthesis(valid, session, "VA-PROCESS-TEST").artifact.artifact_type, "PROCESS_MAP");

  const relabeled = structuredClone(valid);
  relabeled.artifact.data.steps[0]!.label = "AI shorthand for the first step";
  assert.throws(
    () => validateWorkshopSynthesis(relabeled, session, "VA-PROCESS-TEST"),
    /deterministic verbatim prefix/,
  );

  const unsupportedTransition = structuredClone(valid);
  unsupportedTransition.artifact.data.transitions[0]!.provenance = "USER_PROVIDED" as "ASSUMPTION";
  unsupportedTransition.artifact.data.transitions[0]!.source_ids = [];
  assert.throws(
    () => validateWorkshopSynthesis(unsupportedTransition, session, "VA-PROCESS-TEST"),
    /must remain ASSUMPTION or UNKNOWN/,
  );
});

test("offline process mode emits an honest PROCESS_MAP without invented transitions", async () => {
  const session = frozenProcessSession();
  const result = await new MockFacilitatorProvider().synthesize(session);
  assert.equal(result.artifact.artifact_type, "PROCESS_MAP");
  assert.deepEqual(result.artifact.data.transitions, []);
  assert.match(result.artifact.limitations.join(" "), /does not infer actors, order, transitions/i);
});
