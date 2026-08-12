import {
  deleteParticipant,
  findParticipantSession,
  findStudyByPublicToken,
  listMessages,
  safeJson,
} from "@/lib/repository";
import {
  HttpError,
  json,
  participantCredential,
  routeError,
} from "@/lib/http";
import { participantCode } from "@/lib/interview.mjs";

async function resolveSession(request: Request, token: string) {
  const study = await findStudyByPublicToken(token, { includeInactive: true });
  if (!study) throw new HttpError(404, "Study not found.");
  const participant = await findParticipantSession(
    study.id,
    participantCredential(request),
  );
  if (!participant) throw new HttpError(401, "Participant session not found.");
  return { study, participant };
}

export async function GET(
  request: Request,
  context: { params: Promise<{ token: string }> },
) {
  try {
    const { token } = await context.params;
    const { participant } = await resolveSession(request, token);
    const state = safeJson<Record<string, unknown>>(participant.stateJson, {});
    return json({
      participantCode: participantCode(participant.participantNumber),
      status: participant.status,
      progress: {
        turnCount: Number(state.turnCount ?? 0),
        maxTurns: Number(
          (state.stopConditions as { maxTurns?: number } | undefined)?.maxTurns ?? 14,
        ),
      },
      messages: (await listMessages(participant.id)).map((message) => ({
        role: message.role,
        content: message.content,
        provenance: message.provenance,
        redacted: Boolean(message.redacted),
        createdAt: message.createdAt,
      })),
    });
  } catch (error) {
    return routeError(error);
  }
}

export async function DELETE(
  request: Request,
  context: { params: Promise<{ token: string }> },
) {
  try {
    const { token } = await context.params;
    const { participant } = await resolveSession(request, token);
    await deleteParticipant(participant);
    return json({ deleted: true });
  } catch (error) {
    return routeError(error);
  }
}
