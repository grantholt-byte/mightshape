import assert from "node:assert/strict";
import test from "node:test";

async function worker() {
  const workerUrl = new URL("../dist/server/index.js", import.meta.url);
  workerUrl.searchParams.set("test", `${process.pid}-${Date.now()}-${Math.random()}`);
  return (await import(workerUrl.href)).default;
}

async function request(path) {
  const builtWorker = await worker();
  return builtWorker.fetch(
    new Request(`http://localhost${path}`, { headers: { accept: "text/html" } }),
    {
      ASSETS: { fetch: async () => new Response("Not found", { status: 404 }) },
    },
    { waitUntil() {}, passThroughOnException() {} },
  );
}

test("server-renders the finished MightShape companion", async () => {
  const response = await request("/");
  assert.equal(response.status, 200);
  assert.match(response.headers.get("content-type") ?? "", /^text\/html\b/i);
  assert.equal(response.headers.get("referrer-policy"), "no-referrer");
  assert.match(response.headers.get("content-security-policy") ?? "", /connect-src 'self'/);
  const html = await response.text();
  assert.match(html, /<title>MightShape Research<\/title>/i);
  assert.match(html, /A more human interview, facilitated by AI\./);
  assert.match(html, /SOLUTION BLACKOUT/);
  assert.match(html, /Participant privacy/);
  assert.doesNotMatch(html, /Your site is taking shape|codex-preview|react-loading-skeleton/);
});

test("privacy route is concrete and participant-facing", async () => {
  const response = await request("/privacy");
  assert.equal(response.status, 200);
  const html = await response.text();
  assert.match(html, /Research without unnecessary identity/);
  assert.match(html, /delete their transcript/i);
  assert.match(html, /automated redaction is limited/i);
});

test("study routes are non-indexable and never cached", async () => {
  const response = await request(`/s/${"a".repeat(43)}`);
  assert.equal(response.status, 200);
  assert.equal(response.headers.get("cache-control"), "no-store");
  assert.equal(response.headers.get("x-robots-tag"), "noindex, nofollow, noarchive");
  const html = await response.text();
  assert.match(html, /Opening the research study/);
  assert.match(html, /noindex/);
});

test("invalid public tokens fail without touching persistence", async () => {
  const response = await request("/api/studies/guessable");
  assert.equal(response.status, 404);
  assert.equal(response.headers.get("cache-control"), "no-store");
  assert.deepEqual(await response.json(), {
    error: "Study not found or no longer open.",
  });
});
