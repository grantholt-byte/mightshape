const PUBLIC_TOKEN_PATTERN = /^[A-Za-z0-9_-]{43}$/;

/** @param {number} byteLength */
export function randomToken(byteLength = 32) {
  const bytes = new Uint8Array(byteLength);
  crypto.getRandomValues(bytes);
  let binary = "";
  for (const byte of bytes) binary += String.fromCharCode(byte);
  return btoa(binary).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/g, "");
}

/** @param {string} token */
export function isValidPublicToken(token) {
  return PUBLIC_TOKEN_PATTERN.test(token);
}

/** @param {string} value */
export async function sha256(value) {
  const digest = await crypto.subtle.digest(
    "SHA-256",
    new TextEncoder().encode(value),
  );
  return [...new Uint8Array(digest)]
    .map((byte) => byte.toString(16).padStart(2, "0"))
    .join("");
}

/** @param {Request} request */
export function bearerToken(request) {
  const header = request.headers.get("authorization") ?? "";
  const match = /^Bearer\s+(.+)$/i.exec(header);
  return match?.[1]?.trim() ?? "";
}

/**
 * Researcher access is deny-by-default. It accepts either a configured
 * high-entropy server key (for seed tooling) or Sites-injected identity that
 * passes an explicit user/email allowlist.
 * @param {Request} request
 * @param {{researcherApiKey?:string, allowedUserIds?:string, allowedEmails?:string, allowAnyAuthenticated?:string|boolean}} config
 */
export async function authorizeResearcher(request, config = {}) {
  const suppliedKey = bearerToken(request);
  if (
    config.researcherApiKey &&
    suppliedKey &&
    (await constantTimeEqual(suppliedKey, config.researcherApiKey))
  ) {
    return { ok: true, identity: "api-key", method: "API_KEY" };
  }

  const userId = request.headers.get("oai-authenticated-user-id") ?? "";
  const email = (request.headers.get("oai-authenticated-user-email") ?? "").toLowerCase();
  if (!userId || !email) return { ok: false, reason: "AUTHENTICATION_REQUIRED" };

  const allowedIds = csvSet(config.allowedUserIds);
  const allowedEmails = csvSet(config.allowedEmails, true);
  const allowAny =
    config.allowAnyAuthenticated === true ||
    String(config.allowAnyAuthenticated).toLowerCase() === "true";
  if (!allowAny && !allowedIds.has(userId) && !allowedEmails.has(email)) {
    return { ok: false, reason: "NOT_ALLOWED" };
  }
  return { ok: true, identity: userId, method: "SITES_IDENTITY" };
}

/** @param {string} left @param {string} right */
async function constantTimeEqual(left, right) {
  const [a, b] = await Promise.all([sha256(left), sha256(right)]);
  let difference = 0;
  for (let index = 0; index < a.length; index += 1) {
    difference |= a.charCodeAt(index) ^ b.charCodeAt(index);
  }
  return difference === 0;
}

function csvSet(value, lowercase = false) {
  return new Set(
    String(value ?? "")
      .split(",")
      .map((entry) => entry.trim())
      .filter(Boolean)
      .map((entry) => (lowercase ? entry.toLowerCase() : entry)),
  );
}
