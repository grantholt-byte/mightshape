import { cleanText, INTERVIEW_MODES, parseStringList } from "./interview.mjs";

/** @param {unknown} payload */
export function validateStudyInput(payload) {
  const input = payload && typeof payload === "object" ? payload : {};
  const title = cleanText(input.title, 120);
  const purpose = cleanText(input.purpose, 800);
  const researchGoal = cleanText(input.researchGoal, 1_600);
  const topics = parseStringList(input.topics).slice(0, 12);
  const interviewMode =
    input.interviewMode === INTERVIEW_MODES.reveal
      ? INTERVIEW_MODES.reveal
      : INTERVIEW_MODES.blackout;
  const conceptDescription = cleanText(input.conceptDescription, 1_600) || null;
  const errors = [];
  if (title.length < 3) errors.push("title must contain at least 3 characters");
  if (purpose.length < 20) errors.push("purpose must explain the study to participants");
  if (researchGoal.length < 20) errors.push("researchGoal must guide the interviewer");
  if (topics.length === 0) errors.push("at least one interview topic is required");
  if (interviewMode === INTERVIEW_MODES.reveal && !conceptDescription) {
    errors.push("conceptDescription is required for CONCEPT_REVEAL");
  }

  return {
    ok: errors.length === 0,
    errors,
    value: {
      title,
      purpose,
      researchGoal,
      topics,
      interviewMode,
      conceptDescription,
      durationMinutes: integerInRange(input.durationMinutes, 3, 60, 10),
      maxTurns: integerInRange(input.maxTurns, 3, 30, 14),
      maxParticipants: integerInRange(input.maxParticipants, 1, 5_000, 100),
      retentionDays: integerInRange(input.retentionDays, 1, 365, 30),
      dataCollected:
        cleanText(input.dataCollected, 500) ||
        "Your conversation, consent time, and anonymous participant ID. Likely email addresses and phone numbers are removed before storage.",
      reviewerDescription:
        cleanText(input.reviewerDescription, 300) ||
        "The research team that created this study.",
      deidentifiedQuotesAllowed: Boolean(input.deidentifiedQuotesAllowed),
    },
  };
}

/** @param {Record<string, unknown>} study */
export function publicStudyView(study) {
  const reveal = study.interviewMode === INTERVIEW_MODES.reveal;
  return {
    title: study.title,
    purpose: study.purpose,
    durationMinutes: study.durationMinutes,
    interviewMode: study.interviewMode,
    conceptDescription: reveal ? study.conceptDescription : null,
    dataCollected: study.dataCollected,
    reviewerDescription: study.reviewerDescription,
    deidentifiedQuotesAllowed: Boolean(study.deidentifiedQuotesAllowed),
    retentionDays: study.retentionDays,
    consentVersion: "design-council-live-interview-v1",
  };
}

function integerInRange(value, minimum, maximum, fallback) {
  const number = Number(value);
  if (!Number.isInteger(number)) return fallback;
  return Math.min(maximum, Math.max(minimum, number));
}
