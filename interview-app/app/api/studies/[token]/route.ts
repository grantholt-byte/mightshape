import { json, routeError } from "@/lib/http";
import { bearerToken, isValidPublicToken } from "@/lib/security.mjs";
import { publicStudyView } from "@/lib/validation.mjs";

export async function GET(
  request: Request,
  context: { params: Promise<{ token: string }> },
) {
  try {
    const { token } = await context.params;
    if (!isValidPublicToken(token)) {
      return json({ error: "Study not found or no longer open." }, { status: 404 });
    }
    const { findParticipantSession, findStudyByPublicToken } = await import(
      "@/lib/repository"
    );
    let study = await findStudyByPublicToken(token);
    if (!study) {
      const sessionToken = bearerToken(request);
      const inactiveStudy = sessionToken
        ? await findStudyByPublicToken(token, { includeInactive: true })
        : null;
      if (
        inactiveStudy &&
        (await findParticipantSession(inactiveStudy.id, sessionToken))
      ) {
        study = inactiveStudy;
      }
    }
    if (!study) return json({ error: "Study not found or no longer open." }, { status: 404 });
    return json({ study: publicStudyView(study) });
  } catch (error) {
    return routeError(error);
  }
}
