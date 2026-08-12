import {
  closeStudy,
  deleteStudy,
  exportStudy,
  findStudyById,
  revealStudyConcept,
} from "@/lib/repository";
import {
  HttpError,
  json,
  readJson,
  requireResearcher,
  routeError,
} from "@/lib/http";
import { cleanText } from "@/lib/interview.mjs";

async function resolveOwnedStudy(request: Request, id: string) {
  const researcher = await requireResearcher(request);
  const study = await findStudyById(id);
  if (!study) throw new HttpError(404, "Study not found.");
  if (researcher.method !== "API_KEY" && study.createdBy !== researcher.identity) {
    throw new HttpError(403, "This study belongs to another researcher.");
  }
  return study;
}

export async function GET(
  request: Request,
  context: { params: Promise<{ id: string }> },
) {
  try {
    const { id } = await context.params;
    return json(await exportStudy(await resolveOwnedStudy(request, id)));
  } catch (error) {
    return routeError(error);
  }
}

export async function PATCH(
  request: Request,
  context: { params: Promise<{ id: string }> },
) {
  try {
    const { id } = await context.params;
    const study = await resolveOwnedStudy(request, id);
    const body = (await readJson(request)) as {
      action?: string;
      conceptDescription?: unknown;
    };
    if (body.action === "close") {
      return json({ closed: await closeStudy(study.id) });
    }
    if (body.action === "reveal_concept") {
      const concept = cleanText(body.conceptDescription, 1_600);
      if (!concept) throw new HttpError(400, "conceptDescription is required.");
      const revealed = await revealStudyConcept(study, concept);
      if (!revealed) {
        throw new HttpError(409, "This study is already in CONCEPT_REVEAL mode.");
      }
      return json({ interviewMode: "CONCEPT_REVEAL" });
    }
    throw new HttpError(400, "Unsupported study action.");
  } catch (error) {
    return routeError(error);
  }
}

export async function DELETE(
  request: Request,
  context: { params: Promise<{ id: string }> },
) {
  try {
    const { id } = await context.params;
    const study = await resolveOwnedStudy(request, id);
    await deleteStudy(study.id);
    return json({ deleted: true });
  } catch (error) {
    return routeError(error);
  }
}
