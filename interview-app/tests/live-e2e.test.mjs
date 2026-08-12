import assert from "node:assert/strict";
import test from "node:test";

const baseUrl = process.env.E2E_BASE_URL?.replace(/\/$/, "");
const researcherKey = process.env.RESEARCHER_API_KEY;

test(
  "D1-backed live interview lifecycle",
  { skip: !baseUrl || !researcherKey },
  async () => {
    const researcherHeaders = {
      Authorization: `Bearer ${researcherKey}`,
      "Content-Type": "application/json",
    };
    const created = await api("/api/researcher/studies", {
      method: "POST",
      headers: researcherHeaders,
      body: JSON.stringify({
        title: "E2E family coordination",
        purpose:
          "Understand how families experience and resolve recent coordination changes.",
        researchGoal:
          "Reconstruct actual behavior, breakdowns, handoffs, and workarounds without revealing a proposed solution.",
        topics: [
          "a recent schedule change",
          "how it was discovered",
          "what happened next",
        ],
        interviewMode: "SOLUTION_BLACKOUT",
        conceptDescription: "A hidden automatic family scheduling assistant.",
        durationMinutes: 8,
        maxTurns: 4,
        maxParticipants: 5,
        retentionDays: 7,
      }),
    });
    assert.equal(created.response.status, 201);
    assert.match(created.payload.participantPath, /^\/s\/[A-Za-z0-9_-]{43}$/);
    const studyId = created.payload.studyId;
    const publicPath = created.payload.participantPath.replace("/s/", "/api/studies/");

    try {
      const publicStudy = await api(publicPath);
      assert.equal(publicStudy.response.status, 200);
      assert.equal(publicStudy.payload.study.interviewMode, "SOLUTION_BLACKOUT");
      assert.equal(publicStudy.payload.study.conceptDescription, null);

      const rejectedConsent = await api(`${publicPath}/participants`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ consent: false, consentVersion: "outdated" }),
      });
      assert.equal(rejectedConsent.response.status, 400);

      const consented = await api(`${publicPath}/participants`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          consent: true,
          consentVersion: publicStudy.payload.study.consentVersion,
        }),
      });
      assert.equal(consented.response.status, 201);
      assert.equal(consented.payload.participantCode, "P-001");
      assert.match(consented.payload.messages[0].content, /last specific time/i);
      const participantHeaders = {
        Authorization: `Bearer ${consented.payload.sessionToken}`,
        "Content-Type": "application/json",
      };

      const turn = await api(`${publicPath}/messages`, {
        method: "POST",
        headers: participantHeaders,
        body: JSON.stringify({
          message:
            "The change arrived late by text. I emailed person@example.com and called 212-555-0198, then used a spreadsheet workaround.",
        }),
      });
      assert.equal(turn.response.status, 200);
      assert.equal(turn.payload.participantMessage.redacted, true);
      assert.doesNotMatch(turn.payload.participantMessage.content, /example\.com|555-0198/);
      assert.equal(turn.payload.participantMessage.provenance, "HUMAN_INTERVIEW");
      assert.equal(turn.payload.assistantMessage.provenance, "AI_FACILITATOR");
      assert.match(turn.payload.assistantMessage.content, /What happened next/i);

      const secondParticipant = await api(`${publicPath}/participants`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          consent: true,
          consentVersion: publicStudy.payload.study.consentVersion,
        }),
      });
      assert.equal(secondParticipant.response.status, 201);
      assert.equal(secondParticipant.payload.participantCode, "P-002");
      const secondParticipantHeaders = {
        Authorization: `Bearer ${secondParticipant.payload.sessionToken}`,
        "Content-Type": "application/json",
      };
      const secondSession = await api(`${publicPath}/session`, {
        headers: secondParticipantHeaders,
      });
      assert.equal(secondSession.payload.messages.length, 1);
      assert.doesNotMatch(
        secondSession.payload.messages[0].content,
        /person@example\.com|spreadsheet workaround/,
      );

      const skipped = await api(`${publicPath}/messages`, {
        method: "POST",
        headers: secondParticipantHeaders,
        body: JSON.stringify({ action: "SKIP" }),
      });
      assert.equal(skipped.response.status, 200);
      assert.equal(skipped.payload.participantMessage.content, "Question skipped.");
      assert.equal(skipped.payload.participantMessage.provenance, "PARTICIPANT_ACTION");
      assert.match(skipped.payload.assistantMessage.content, /Let's move on/i);

      const revealed = await api(`/api/researcher/studies/${studyId}`, {
        method: "PATCH",
        headers: researcherHeaders,
        body: JSON.stringify({
          action: "reveal_concept",
          conceptDescription: "A shared inbox that surfaces schedule conflicts.",
        }),
      });
      assert.equal(revealed.response.status, 200);
      const revealedPublicStudy = await api(publicPath);
      assert.equal(revealedPublicStudy.payload.study.interviewMode, "CONCEPT_REVEAL");
      assert.equal(
        revealedPublicStudy.payload.study.conceptDescription,
        "A shared inbox that surfaces schedule conflicts.",
      );

      const conceptTurn = await api(`${publicPath}/messages`, {
        method: "POST",
        headers: participantHeaders,
        body: JSON.stringify({
          message: "The workaround helped, but I still found the conflict late.",
        }),
      });
      assert.equal(conceptTurn.response.status, 200);
      assert.equal(conceptTurn.payload.interviewMode, "CONCEPT_REVEAL");
      assert.equal(
        conceptTurn.payload.conceptDescription,
        "A shared inbox that surfaces schedule conflicts.",
      );
      assert.match(conceptTurn.payload.assistantMessage.content, /what do you think this concept would do/i);

      const stopped = await api(`${publicPath}/stop`, {
        method: "POST",
        headers: participantHeaders,
      });
      assert.equal(stopped.response.status, 200);
      assert.equal(stopped.payload.status, "STOPPED");

      const closed = await api(`/api/researcher/studies/${studyId}`, {
        method: "PATCH",
        headers: researcherHeaders,
        body: JSON.stringify({ action: "close" }),
      });
      assert.equal(closed.response.status, 200);
      assert.equal(closed.payload.closed, true);
      const closedPublicStudy = await api(publicPath);
      assert.equal(closedPublicStudy.response.status, 404);
      const existingParticipantView = await api(publicPath, {
        headers: participantHeaders,
      });
      assert.equal(existingParticipantView.response.status, 200);
      assert.equal(
        existingParticipantView.payload.study.interviewMode,
        "CONCEPT_REVEAL",
      );

      const exported = await api(`/api/researcher/studies/${studyId}`, {
        headers: researcherHeaders,
      });
      assert.equal(exported.response.status, 200);
      assert.equal(exported.payload.evidenceProvenance, "HUMAN_INTERVIEW");
      assert.match(exported.payload.qualitativeScopeWarning, /Do not infer prevalence/);
      assert.equal(exported.payload.participants.length, 2);
      assert.equal(exported.payload.participants[0].messages[1].provenance, "HUMAN_INTERVIEW");
      assert.equal(exported.payload.participants[1].messages.length, 3);
      assert.equal(
        exported.payload.participants[1].messages[1].provenance,
        "PARTICIPANT_ACTION",
      );

      const deletedParticipant = await api(`${publicPath}/session`, {
        method: "DELETE",
        headers: participantHeaders,
      });
      assert.equal(deletedParticipant.response.status, 200);
      assert.equal(deletedParticipant.payload.deleted, true);
      const afterDeletion = await api(`/api/researcher/studies/${studyId}`, {
        headers: researcherHeaders,
      });
      assert.equal(afterDeletion.payload.participants.length, 1);
      assert.equal(afterDeletion.payload.deletionReceipts.length, 1);
      assert.equal(afterDeletion.payload.deletionReceipts[0].participantCode, "P-001");

      const deletedSecondParticipant = await api(`${publicPath}/session`, {
        method: "DELETE",
        headers: secondParticipantHeaders,
      });
      assert.equal(deletedSecondParticipant.response.status, 200);
      const afterBothDeletions = await api(`/api/researcher/studies/${studyId}`, {
        headers: researcherHeaders,
      });
      assert.equal(afterBothDeletions.payload.participants.length, 0);
      assert.equal(afterBothDeletions.payload.deletionReceipts.length, 2);
    } finally {
      const removed = await api(`/api/researcher/studies/${studyId}`, {
        method: "DELETE",
        headers: researcherHeaders,
      });
      assert.equal(removed.response.status, 200);
    }
  },
);

async function api(path, init = {}) {
  const response = await fetch(`${baseUrl}${path}`, init);
  const payload = await response.json();
  return { response, payload };
}
