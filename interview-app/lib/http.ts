import { authorizeResearcher, bearerToken } from "./security.mjs";

export function json(data: unknown, init: ResponseInit = {}) {
  const headers = new Headers(init.headers);
  headers.set("Cache-Control", "no-store");
  headers.set("Content-Type", "application/json; charset=utf-8");
  return new Response(JSON.stringify(data), { ...init, headers });
}

export async function readJson(request: Request) {
  const contentType = request.headers.get("content-type") ?? "";
  if (!contentType.toLowerCase().startsWith("application/json")) {
    throw new HttpError(415, "Requests must use application/json.");
  }
  try {
    return (await request.json()) as unknown;
  } catch {
    throw new HttpError(400, "Request body must be valid JSON.");
  }
}

export function participantCredential(request: Request) {
  const token = bearerToken(request);
  if (!token) throw new HttpError(401, "Participant session credential required.");
  return token;
}

export async function requireResearcher(request: Request) {
  const { runtimeEnv } = await import("./runtime");
  const config = runtimeEnv();
  const auth = await authorizeResearcher(request, {
    researcherApiKey: config.RESEARCHER_API_KEY,
    allowedUserIds: config.RESEARCHER_ALLOWED_USER_IDS,
    allowedEmails: config.RESEARCHER_ALLOWED_EMAILS,
    allowAnyAuthenticated: config.RESEARCHER_ALLOW_ANY_AUTHENTICATED,
  });
  if (!auth.ok) {
    throw new HttpError(
      auth.reason === "NOT_ALLOWED" ? 403 : 401,
      auth.reason === "NOT_ALLOWED"
        ? "This researcher account is not allowed for this Site."
        : "Researcher authentication required.",
    );
  }
  return auth;
}

export class HttpError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

export function routeError(error: unknown) {
  if (error instanceof HttpError) {
    return json({ error: error.message }, { status: error.status });
  }
  const message = error instanceof Error ? error.message : "Unexpected error";
  if (message.includes("no such table")) {
    return json(
      { error: "The interview database migration has not been applied." },
      { status: 503 },
    );
  }
  console.error("MightShape interview route failed", error);
  return json({ error: "The interview service is temporarily unavailable." }, { status: 500 });
}
