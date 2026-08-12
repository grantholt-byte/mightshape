import { createStudy } from "@/lib/repository";
import {
  HttpError,
  json,
  readJson,
  requireResearcher,
  routeError,
} from "@/lib/http";
import { validateStudyInput } from "@/lib/validation.mjs";

export async function POST(request: Request) {
  try {
    const researcher = await requireResearcher(request);
    const validation = validateStudyInput(await readJson(request));
    if (!validation.ok) {
      throw new HttpError(400, validation.errors.join("; "));
    }
    const created = await createStudy(validation.value, String(researcher.identity));
    return json(
      {
        studyId: created.id,
        participantPath: `/s/${created.publicToken}`,
        publicToken: created.publicToken,
        expiresAt: created.expiresAt,
        note: "The public token is shown once and stored only as a hash. Save the participant link now.",
      },
      { status: 201 },
    );
  } catch (error) {
    return routeError(error);
  }
}
