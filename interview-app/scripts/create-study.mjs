#!/usr/bin/env node

const baseUrl = (process.argv[2] || process.env.DESIGN_COUNCIL_SITE_URL || "http://localhost:3000").replace(/\/$/, "");
const apiKey = process.env.RESEARCHER_API_KEY;

if (!apiKey) {
  console.error("Set RESEARCHER_API_KEY before creating a study.");
  process.exitCode = 1;
} else {
  const study = {
    title: process.env.STUDY_TITLE || "Understanding family coordination",
    purpose:
      process.env.STUDY_PURPOSE ||
      "We are learning how families currently notice, communicate, and resolve changes to shared commitments.",
    researchGoal:
      process.env.STUDY_RESEARCH_GOAL ||
      "Reconstruct recent coordination breakdowns, including information sources, handoffs, workarounds, emotional consequences, and who carries the invisible work.",
    topics: parseTopics(
      process.env.STUDY_TOPICS ||
        "a recent schedule change|how the change was discovered|the steps taken to resolve it|workarounds and invisible coordination",
    ),
    interviewMode:
      process.env.STUDY_INTERVIEW_MODE === "CONCEPT_REVEAL"
        ? "CONCEPT_REVEAL"
        : "SOLUTION_BLACKOUT",
    conceptDescription: process.env.STUDY_CONCEPT || null,
    durationMinutes: Number(process.env.STUDY_DURATION_MINUTES || 10),
    retentionDays: Number(process.env.STUDY_RETENTION_DAYS || 30),
    maxParticipants: Number(process.env.STUDY_MAX_PARTICIPANTS || 30),
    maxTurns: Number(process.env.STUDY_MAX_TURNS || 12),
    dataCollected:
      "Your conversation, consent time, and anonymous participant ID. Likely email addresses and phone numbers are removed before storage.",
    reviewerDescription: process.env.STUDY_REVIEWERS || "The Design Council project research team.",
    deidentifiedQuotesAllowed:
      String(process.env.STUDY_ALLOW_QUOTES).toLowerCase() === "true",
  };

  const response = await fetch(`${baseUrl}/api/researcher/studies`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${apiKey}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(study),
  });
  const payload = await response.json();
  if (!response.ok) {
    console.error(payload.error || `Study creation failed (${response.status}).`);
    process.exitCode = 1;
  } else {
    console.log(`Study created: ${payload.studyId}`);
    console.log(`Participant link: ${baseUrl}${payload.participantPath}`);
    console.log(`Expires: ${payload.expiresAt}`);
    console.log("Save this link now. The server retains only a hash of its public token.");
  }
}

function parseTopics(value) {
  return value
    .split("|")
    .map((topic) => topic.trim())
    .filter(Boolean);
}
