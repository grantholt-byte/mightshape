import {
  findParticipantSession,
  findStudyByPublicToken,
  stopParticipant,
} from "@/lib/repository";
import {
  HttpError,
  json,
  participantCredential,
  routeError,
} from "@/lib/http";

export async function POST(
  request: Request,
  context: { params: Promise<{ token: string }> },
) {
  try {
    const { token } = await context.params;
    const study = await findStudyByPublicToken(token, { includeInactive: true });
    if (!study) throw new HttpError(404, "Study not found.");
    const participant = await findParticipantSession(
      study.id,
      participantCredential(request),
    );
    if (!participant) throw new HttpError(401, "Participant session not found.");
    await stopParticipant(participant.id);
    return json({
      status: "STOPPED",
      message:
        "The interview is stopped. Your existing responses remain stored until you delete them or the research team deletes the study under its retention process.",
    });
  } catch (error) {
    return routeError(error);
  }
}
