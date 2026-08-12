import { createParticipant, findStudyByPublicToken } from "@/lib/repository";
import { HttpError, json, readJson, routeError } from "@/lib/http";
import { CONSENT_VERSION } from "@/lib/interview.mjs";

export async function POST(
  request: Request,
  context: { params: Promise<{ token: string }> },
) {
  try {
    const body = (await readJson(request)) as {
      consent?: boolean;
      consentVersion?: string;
    };
    if (body.consent !== true || body.consentVersion !== CONSENT_VERSION) {
      throw new HttpError(400, "Current explicit consent is required to begin.");
    }
    const { token } = await context.params;
    const study = await findStudyByPublicToken(token);
    if (!study) throw new HttpError(404, "Study not found or no longer open.");
    const participant = await createParticipant(study);
    return json(
      {
        participantCode: participant.participantCode,
        sessionToken: participant.sessionToken,
        status: "ACTIVE",
        messages: [
          {
            role: "ASSISTANT",
            content: participant.opening,
            provenance: "AI_FACILITATOR",
          },
        ],
      },
      { status: 201 },
    );
  } catch (error) {
    if (error instanceof Error && error.message === "STUDY_CAPACITY_REACHED") {
      return json({ error: "This study is no longer accepting participants." }, { status: 409 });
    }
    return routeError(error);
  }
}
