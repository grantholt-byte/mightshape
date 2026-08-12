import { getD1 } from "@/db";
import {
  CONSENT_VERSION,
  firstQuestion,
  initialInterviewState,
  participantCode,
} from "./interview.mjs";
import { isValidPublicToken, randomToken, sha256 } from "./security.mjs";

export type StudyRow = {
  id: string;
  publicTokenHash: string;
  title: string;
  purpose: string;
  researchGoal: string;
  durationMinutes: number;
  topicsJson: string;
  interviewMode: "SOLUTION_BLACKOUT" | "CONCEPT_REVEAL";
  conceptDescription: string | null;
  dataCollected: string;
  reviewerDescription: string;
  deidentifiedQuotesAllowed: number;
  retentionDays: number;
  maxTurns: number;
  maxParticipants: number;
  nextParticipantNumber: number;
  status: string;
  createdBy: string;
  createdAt: string;
  updatedAt: string;
  expiresAt: string;
};

export type ParticipantRow = {
  id: string;
  studyId: string;
  participantNumber: number;
  sessionTokenHash: string;
  status: "ACTIVE" | "STOPPED" | "COMPLETED";
  consentVersion: string;
  consentedAt: string;
  stateJson: string;
  processing: number;
  createdAt: string;
  updatedAt: string;
  completedAt: string | null;
};

export type MessageRow = {
  id: string;
  participantId: string;
  role: "USER" | "ASSISTANT";
  content: string;
  provenance: "HUMAN_INTERVIEW" | "AI_FACILITATOR" | "PARTICIPANT_ACTION";
  redacted: number;
  createdAt: string;
};

const STUDY_SELECT = `
  id,
  public_token_hash AS publicTokenHash,
  title,
  purpose,
  research_goal AS researchGoal,
  duration_minutes AS durationMinutes,
  topics_json AS topicsJson,
  interview_mode AS interviewMode,
  concept_description AS conceptDescription,
  data_collected AS dataCollected,
  reviewer_description AS reviewerDescription,
  deidentified_quotes_allowed AS deidentifiedQuotesAllowed,
  retention_days AS retentionDays,
  max_turns AS maxTurns,
  max_participants AS maxParticipants,
  next_participant_number AS nextParticipantNumber,
  status,
  created_by AS createdBy,
  created_at AS createdAt,
  updated_at AS updatedAt,
  expires_at AS expiresAt
`;

const PARTICIPANT_SELECT = `
  id,
  study_id AS studyId,
  participant_number AS participantNumber,
  session_token_hash AS sessionTokenHash,
  status,
  consent_version AS consentVersion,
  consented_at AS consentedAt,
  state_json AS stateJson,
  processing,
  created_at AS createdAt,
  updated_at AS updatedAt,
  completed_at AS completedAt
`;

export async function createStudy(
  input: {
    title: string;
    purpose: string;
    researchGoal: string;
    topics: string[];
    interviewMode: string;
    conceptDescription: string | null;
    dataCollected: string;
    reviewerDescription: string;
    deidentifiedQuotesAllowed: boolean;
    retentionDays: number;
    maxTurns: number;
    maxParticipants: number;
    durationMinutes: number;
  },
  createdBy: string,
) {
  const db = getD1();
  const id = crypto.randomUUID();
  const publicToken = randomToken();
  const publicTokenHash = await sha256(publicToken);
  const expiresAt = new Date(
    Date.now() + input.retentionDays * 24 * 60 * 60 * 1_000,
  ).toISOString();
  await db.batch([
    db.prepare(
      `INSERT INTO studies (
        id, public_token_hash, title, purpose, research_goal, duration_minutes,
        topics_json, interview_mode, concept_description, data_collected,
        reviewer_description, deidentified_quotes_allowed, retention_days,
        max_turns, max_participants, status, created_by, expires_at
      ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'ACTIVE', ?, ?)`,
    ).bind(
      id,
      publicTokenHash,
      input.title,
      input.purpose,
      input.researchGoal,
      input.durationMinutes,
      JSON.stringify(input.topics),
      input.interviewMode,
      input.conceptDescription,
      input.dataCollected,
      input.reviewerDescription,
      input.deidentifiedQuotesAllowed ? 1 : 0,
      input.retentionDays,
      input.maxTurns,
      input.maxParticipants,
      createdBy,
      expiresAt,
    ),
    db
      .prepare(
        "INSERT INTO study_events (id, study_id, type, detail_json) VALUES (?, ?, 'STUDY_CREATED', ?)",
      )
      .bind(
        crypto.randomUUID(),
        id,
        JSON.stringify({ interviewMode: input.interviewMode }),
      ),
  ]);
  return { id, publicToken, expiresAt };
}

export async function findStudyByPublicToken(
  publicToken: string,
  options: { includeInactive?: boolean } = {},
) {
  if (!isValidPublicToken(publicToken)) return null;
  const tokenHash = await sha256(publicToken);
  const activeClause = options.includeInactive
    ? ""
    : "AND status = 'ACTIVE' AND datetime(expires_at) > CURRENT_TIMESTAMP";
  return getD1()
    .prepare(
      `SELECT ${STUDY_SELECT} FROM studies WHERE public_token_hash = ? ${activeClause} LIMIT 1`,
    )
    .bind(tokenHash)
    .first<StudyRow>();
}

export async function findStudyById(id: string) {
  return getD1()
    .prepare(`SELECT ${STUDY_SELECT} FROM studies WHERE id = ? LIMIT 1`)
    .bind(id)
    .first<StudyRow>();
}

export async function createParticipant(study: StudyRow) {
  const db = getD1();
  const allocation = await db
    .prepare(
      `UPDATE studies
       SET next_participant_number = next_participant_number + 1,
           updated_at = CURRENT_TIMESTAMP
       WHERE id = ?
         AND status = 'ACTIVE'
         AND datetime(expires_at) > CURRENT_TIMESTAMP
         AND next_participant_number <= max_participants
       RETURNING next_participant_number - 1 AS participantNumber`,
    )
    .bind(study.id)
    .first<{ participantNumber: number }>();
  if (!allocation) throw new Error("STUDY_CAPACITY_REACHED");

  const id = crypto.randomUUID();
  const sessionToken = randomToken();
  const sessionTokenHash = await sha256(sessionToken);
  const consentedAt = new Date().toISOString();
  const state = initialInterviewState(study);
  const opening = firstQuestion(study);
  await db.batch([
    db
      .prepare(
        `INSERT INTO participants (
          id, study_id, participant_number, session_token_hash, status,
          consent_version, consented_at, state_json
        ) VALUES (?, ?, ?, ?, 'ACTIVE', ?, ?, ?)`,
      )
      .bind(
        id,
        study.id,
        allocation.participantNumber,
        sessionTokenHash,
        CONSENT_VERSION,
        consentedAt,
        JSON.stringify(state),
      ),
    db
      .prepare(
        `INSERT INTO messages (
          id, participant_id, role, content, provenance, redacted
        ) VALUES (?, ?, 'ASSISTANT', ?, 'AI_FACILITATOR', 0)`,
      )
      .bind(crypto.randomUUID(), id, opening),
  ]);
  return {
    participantId: id,
    participantCode: participantCode(allocation.participantNumber),
    sessionToken,
    consentedAt,
    state,
    opening,
  };
}

export async function findParticipantSession(
  studyId: string,
  sessionToken: string,
) {
  if (!isValidPublicToken(sessionToken)) return null;
  const tokenHash = await sha256(sessionToken);
  return getD1()
    .prepare(
      `SELECT ${PARTICIPANT_SELECT}
       FROM participants
       WHERE study_id = ? AND session_token_hash = ?
       LIMIT 1`,
    )
    .bind(studyId, tokenHash)
    .first<ParticipantRow>();
}

export async function listMessages(participantId: string) {
  const result = await getD1()
    .prepare(
      `SELECT
        id, participant_id AS participantId, role, content, provenance,
        redacted, created_at AS createdAt
       FROM messages
       WHERE participant_id = ?
       ORDER BY created_at ASC, rowid ASC`,
    )
    .bind(participantId)
    .all<MessageRow>();
  return result.results;
}

export async function acquireParticipant(participantId: string) {
  const result = await getD1()
    .prepare(
      `UPDATE participants
       SET processing = 1, updated_at = CURRENT_TIMESTAMP
       WHERE id = ? AND status = 'ACTIVE'
         AND (
           processing = 0 OR
           datetime(updated_at) <= datetime(CURRENT_TIMESTAMP, '-2 minutes')
         )`,
    )
    .bind(participantId)
    .run();
  return Number(result.meta.changes ?? 0) === 1;
}

export async function releaseParticipant(participantId: string) {
  await getD1()
    .prepare(
      `UPDATE participants
       SET processing = 0, updated_at = CURRENT_TIMESTAMP
       WHERE id = ?`,
    )
    .bind(participantId)
    .run();
}

export async function saveInterviewTurn(input: {
  participant: ParticipantRow;
  participantText: string;
  participantRedacted: boolean;
  participantProvenance?: "HUMAN_INTERVIEW" | "PARTICIPANT_ACTION";
  assistantText: string;
  nextState: Record<string, unknown>;
  shouldStop: boolean;
}) {
  const db = getD1();
  const nextStatus = input.shouldStop ? "COMPLETED" : "ACTIVE";
  const results = await db.batch([
    db
      .prepare(
        `INSERT INTO messages (
          id, participant_id, role, content, provenance, redacted
        )
        SELECT ?, ?, 'USER', ?, ?, ?
        WHERE EXISTS (
          SELECT 1 FROM participants
          WHERE id = ? AND status = 'ACTIVE' AND processing = 1
        )`,
      )
      .bind(
        crypto.randomUUID(),
        input.participant.id,
        input.participantText,
        input.participantProvenance ?? "HUMAN_INTERVIEW",
        input.participantRedacted ? 1 : 0,
        input.participant.id,
      ),
    db
      .prepare(
        `INSERT INTO messages (
          id, participant_id, role, content, provenance, redacted
        )
        SELECT ?, ?, 'ASSISTANT', ?, 'AI_FACILITATOR', 0
        WHERE EXISTS (
          SELECT 1 FROM participants
          WHERE id = ? AND status = 'ACTIVE' AND processing = 1
        )`,
      )
      .bind(
        crypto.randomUUID(),
        input.participant.id,
        input.assistantText,
        input.participant.id,
      ),
    db
      .prepare(
        `UPDATE participants
         SET state_json = ?,
             status = ?,
             processing = 0,
             completed_at = CASE
               WHEN ? = 'COMPLETED' THEN CURRENT_TIMESTAMP
               ELSE completed_at
             END,
             updated_at = CURRENT_TIMESTAMP
         WHERE id = ? AND status = 'ACTIVE' AND processing = 1`,
      )
      .bind(
        JSON.stringify(input.nextState),
        nextStatus,
        nextStatus,
        input.participant.id,
      ),
  ]);
  // D1 batches execute as a transaction. A concurrent stop that commits first
  // makes every conditional statement a no-op, so a late model response cannot
  // be persisted after the participant has ended the interview.
  return Number(results[2]?.meta.changes ?? 0) === 1;
}

export async function stopParticipant(participantId: string) {
  const result = await getD1()
    .prepare(
      `UPDATE participants
       SET status = 'STOPPED', processing = 0, completed_at = CURRENT_TIMESTAMP,
           updated_at = CURRENT_TIMESTAMP
       WHERE id = ? AND status = 'ACTIVE'`,
    )
    .bind(participantId)
    .run();
  return Number(result.meta.changes ?? 0) === 1;
}

export async function deleteParticipant(
  participant: ParticipantRow,
  reason = "PARTICIPANT_REQUEST",
) {
  const db = getD1();
  await db.batch([
    db
      .prepare(
        `INSERT INTO deletion_receipts (
          id, study_id, participant_code, reason
        ) VALUES (?, ?, ?, ?)`,
      )
      .bind(
        crypto.randomUUID(),
        participant.studyId,
        participantCode(participant.participantNumber),
        reason,
      ),
    db.prepare("DELETE FROM participants WHERE id = ?").bind(participant.id),
  ]);
}

export async function exportStudy(study: StudyRow) {
  const participantResult = await getD1()
    .prepare(
      `SELECT ${PARTICIPANT_SELECT}
       FROM participants WHERE study_id = ?
       ORDER BY participant_number ASC`,
    )
    .bind(study.id)
    .all<ParticipantRow>();
  const participants = [];
  for (const participant of participantResult.results) {
    participants.push({
      participantCode: participantCode(participant.participantNumber),
      status: participant.status,
      consentVersion: participant.consentVersion,
      consentedAt: participant.consentedAt,
      state: safeJson(participant.stateJson, {}),
      createdAt: participant.createdAt,
      completedAt: participant.completedAt,
      messages: (await listMessages(participant.id)).map((message) => ({
        role: message.role,
        content: message.content,
        provenance: message.provenance,
        redacted: Boolean(message.redacted),
        createdAt: message.createdAt,
      })),
    });
  }
  const receiptResult = await getD1()
    .prepare(
      `SELECT participant_code AS participantCode, reason, deleted_at AS deletedAt
       FROM deletion_receipts WHERE study_id = ? ORDER BY deleted_at ASC`,
    )
    .bind(study.id)
    .all();
  return {
    study: {
      id: study.id,
      title: study.title,
      purpose: study.purpose,
      researchGoal: study.researchGoal,
      topics: safeJson(study.topicsJson, []),
      interviewMode: study.interviewMode,
      conceptDescription: study.conceptDescription,
      status: study.status,
      createdAt: study.createdAt,
      expiresAt: study.expiresAt,
    },
    evidenceProvenance: "HUMAN_INTERVIEW",
    qualitativeScopeWarning:
      "These accounts describe this sample only. Do not infer prevalence or population-wide behavior from a small qualitative study.",
    participants,
    deletionReceipts: receiptResult.results,
  };
}

export async function revealStudyConcept(
  study: StudyRow,
  conceptDescription: string,
) {
  if (study.interviewMode !== "SOLUTION_BLACKOUT") return false;
  const result = await getD1()
    .prepare(
      `UPDATE studies
       SET interview_mode = 'CONCEPT_REVEAL', concept_description = ?,
           updated_at = CURRENT_TIMESTAMP
       WHERE id = ? AND interview_mode = 'SOLUTION_BLACKOUT'`,
    )
    .bind(conceptDescription, study.id)
    .run();
  if (Number(result.meta.changes ?? 0) === 1) {
    await recordStudyEvent(study.id, "CONCEPT_REVEALED", {
      disclosure: "Concept became available to subsequent interview turns.",
    });
    return true;
  }
  return false;
}

export async function closeStudy(studyId: string) {
  const result = await getD1()
    .prepare(
      `UPDATE studies SET status = 'CLOSED', updated_at = CURRENT_TIMESTAMP
       WHERE id = ? AND status = 'ACTIVE'`,
    )
    .bind(studyId)
    .run();
  return Number(result.meta.changes ?? 0) === 1;
}

export async function deleteStudy(studyId: string) {
  const db = getD1();
  await db.batch([
    db.prepare("DELETE FROM deletion_receipts WHERE study_id = ?").bind(studyId),
    db.prepare("DELETE FROM studies WHERE id = ?").bind(studyId),
  ]);
}

async function recordStudyEvent(
  studyId: string,
  type: string,
  detail: Record<string, unknown>,
) {
  await getD1()
    .prepare(
      "INSERT INTO study_events (id, study_id, type, detail_json) VALUES (?, ?, ?, ?)",
    )
    .bind(crypto.randomUUID(), studyId, type, JSON.stringify(detail))
    .run();
}

export function safeJson<T>(value: string, fallback: T): T {
  try {
    return JSON.parse(value) as T;
  } catch {
    return fallback;
  }
}
