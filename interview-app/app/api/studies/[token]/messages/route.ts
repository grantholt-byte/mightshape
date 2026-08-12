import {
  acquireParticipant,
  findParticipantSession,
  findStudyByPublicToken,
  listMessages,
  releaseParticipant,
  safeJson,
  saveInterviewTurn,
} from "@/lib/repository";
import {
  HttpError,
  json,
  participantCredential,
  readJson,
  routeError,
} from "@/lib/http";
import {
  applyTurnToState,
  cleanText,
  parseStringList,
  participantCode,
  redactLikelyPii,
  SKIP_ACTION_TEXT,
  SKIP_DISPLAY_TEXT,
} from "@/lib/interview.mjs";
import { generateInterviewTurn } from "@/lib/openai.mjs";
import { runtimeEnv } from "@/lib/runtime";
import { sha256 } from "@/lib/security.mjs";

export async function POST(
  request: Request,
  context: { params: Promise<{ token: string }> },
) {
  let lockedParticipantId: string | null = null;
  let saved = false;
  try {
    const body = (await readJson(request)) as { message?: unknown; action?: unknown };
    if (body.action !== undefined && body.action !== "SKIP") {
      throw new HttpError(400, "Unknown participant action.");
    }
    const isSkip = body.action === "SKIP";
    const rawText = isSkip ? SKIP_ACTION_TEXT : cleanText(body.message, 4_000);
    if (!rawText) throw new HttpError(400, "A response is required.");

    const { token } = await context.params;
    const study = await findStudyByPublicToken(token);
    if (!study) throw new HttpError(404, "Study not found or no longer open.");
    const participant = await findParticipantSession(
      study.id,
      participantCredential(request),
    );
    if (!participant) throw new HttpError(401, "Participant session not found.");
    if (participant.status !== "ACTIVE") {
      throw new HttpError(409, "This interview has already ended.");
    }
    if (!(await acquireParticipant(participant.id))) {
      throw new HttpError(409, "A response is already being processed.");
    }
    lockedParticipantId = participant.id;

    const redaction = isSkip
      ? { text: SKIP_ACTION_TEXT, redacted: false }
      : redactLikelyPii(rawText);
    const state = safeJson<Record<string, unknown>>(participant.stateJson, {});
    const messages = await listMessages(participant.id);
    const promptMessages = [
      ...messages.map((message) => ({
        role: message.role,
        content:
          message.provenance === "PARTICIPANT_ACTION"
            ? SKIP_ACTION_TEXT
            : message.content,
      })),
      { role: "USER", content: redaction.text },
    ];
    const config = runtimeEnv();
    let turn;
    try {
      turn = await generateInterviewTurn(
        {
          study,
          state,
          messages: promptMessages,
          participantCode: participantCode(participant.participantNumber),
          participantText: redaction.text,
          participantAction: isSkip ? "SKIP" : null,
        },
        {
          mode: config.INTERVIEW_AI_MODE || "openai",
          apiKey: config.OPENAI_API_KEY,
          model: config.OPENAI_MODEL || "gpt-5.6-sol",
          safetyIdentifier: `dc_${(await sha256(participant.id)).slice(0, 24)}`,
        },
      );
    } catch (error) {
      console.error("AI interviewer generation failed", error);
      throw new HttpError(
        503,
        "The AI interviewer could not respond just now. Your response was not stored; please try again.",
      );
    }

    if (isSkip) {
      turn.coveredTopics = parseStringList(state.coveredTopics);
    }
    const nextState: Record<string, unknown> = applyTurnToState(state, turn);
    if (isSkip) {
      nextState.skippedQuestions = Number(state.skippedQuestions ?? 0) + 1;
    }
    const maxTurns = Number(
      (state.stopConditions as { maxTurns?: number } | undefined)?.maxTurns ??
        study.maxTurns,
    );
    if (Number(nextState.turnCount) >= maxTurns && !turn.shouldStop) {
      turn.shouldStop = true;
      turn.closingReason = "MAX_TURNS";
      turn.reply =
        "Thank you for sharing that. We’ve reached the planned end of this interview. Your responses are recorded under your participant ID, and you can delete them from this page.";
      nextState.lastClosingReason = "MAX_TURNS";
    }

    const committed = await saveInterviewTurn({
      participant,
      participantText: isSkip ? SKIP_DISPLAY_TEXT : redaction.text,
      participantRedacted: redaction.redacted,
      participantProvenance: isSkip ? "PARTICIPANT_ACTION" : "HUMAN_INTERVIEW",
      assistantText: turn.reply,
      nextState,
      shouldStop: turn.shouldStop,
    });
    saved = true;
    if (!committed) {
      return json({
        status: "STOPPED",
        discarded: true,
        message:
          "The interview ended before this response was saved. No late response was added.",
      });
    }
    return json({
      participantMessage: {
        role: "USER",
        content: isSkip ? SKIP_DISPLAY_TEXT : redaction.text,
        provenance: isSkip ? "PARTICIPANT_ACTION" : "HUMAN_INTERVIEW",
        redacted: redaction.redacted,
      },
      assistantMessage: {
        role: "ASSISTANT",
        content: turn.reply,
        provenance: "AI_FACILITATOR",
      },
      status: turn.shouldStop ? "COMPLETED" : "ACTIVE",
      closingReason: turn.closingReason,
      interviewMode: study.interviewMode,
      conceptDescription:
        study.interviewMode === "CONCEPT_REVEAL"
          ? study.conceptDescription
          : null,
      progress: { turnCount: nextState.turnCount, maxTurns },
    });
  } catch (error) {
    return routeError(error);
  } finally {
    if (lockedParticipantId && !saved) {
      await releaseParticipant(lockedParticipantId).catch((error) =>
        console.error("Failed to release participant interview lock", error),
      );
    }
  }
}
