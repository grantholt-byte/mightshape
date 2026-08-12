import { spawn } from "node:child_process";
import { mkdir, mkdtemp, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";

const baseUrl = (process.env.E2E_BASE_URL ?? "http://localhost:4173").replace(/\/$/, "");
const researcherKey = process.env.RESEARCHER_API_KEY;
const chromePath =
  process.env.CHROME_PATH ??
  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
const outputDirectory = resolve("tests/screenshots");

async function main() {
  if (!researcherKey) {
    throw new Error("RESEARCHER_API_KEY is required to create the screenshot fixture study.");
  }

  await mkdir(outputDirectory, { recursive: true });
  const profileDirectory = await mkdtemp(join(tmpdir(), "design-council-chrome-"));
  let browser;
  let studyId;

  try {
  const created = await api("/api/researcher/studies", {
    method: "POST",
    headers: researcherHeaders(),
    body: JSON.stringify({
      title: "Everyday coordination study",
      purpose:
        "Help a design team understand how people notice, communicate, and resolve changes to shared plans.",
      researchGoal:
        "Reconstruct recent coordination breakdowns, workarounds, handoffs, and felt consequences.",
      topics: [
        "a recent change to a shared plan",
        "how the change was discovered",
        "what happened next",
      ],
      interviewMode: "SOLUTION_BLACKOUT",
      conceptDescription: "A proposed coordination assistant that remains hidden during exploration.",
      durationMinutes: 8,
      retentionDays: 7,
      maxTurns: 8,
      maxParticipants: 3,
      dataCollected: "Your text responses, anonymous participant ID, and interview timestamps.",
      reviewerDescription: "The Design Council project research team.",
      deidentifiedQuotesAllowed: true,
    }),
  });
  studyId = created.studyId;
  const participantPath = created.participantPath;
  const publicApiPath = participantPath.replace("/s/", "/api/studies/");
  const token = participantPath.split("/").at(-1);

  browser = await launchChrome(chromePath, profileDirectory);
  const page = await createPage(browser.port);
  await page.send("Page.enable");
  await page.send("Runtime.enable");
  await setViewport(page, 1440, 1280);
  await navigate(page, `${baseUrl}${participantPath}`, ".consent-card");
  await settle(page);
  await capture(page, join(outputDirectory, "consent.png"));

  const publicStudy = await api(publicApiPath);
  const participant = await api(`${publicApiPath}/participants`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      consent: true,
      consentVersion: publicStudy.study.consentVersion,
    }),
  });
  await api(`${publicApiPath}/messages`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${participant.sessionToken}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      message:
        "Last Thursday the plan changed in a group text while I was working. I updated my calendar, then learned my partner had not seen the message, so I called them and we rearranged pickup manually.",
    }),
  });

  await navigate(page, `${baseUrl}/privacy`, "main");
  await page.send("Runtime.evaluate", {
    expression: `sessionStorage.setItem(${JSON.stringify(`dc-interview:${token}`)}, ${JSON.stringify(participant.sessionToken)})`,
  });
  await setViewport(page, 1440, 1000);
  await navigate(page, `${baseUrl}${participantPath}`, ".conversation-shell");
  await settle(page);
  await capture(page, join(outputDirectory, "active.png"));
  page.close();

  process.stdout.write(
    `Rendered screenshots:\n- ${join(outputDirectory, "consent.png")}\n- ${join(outputDirectory, "active.png")}\n`,
  );
  } finally {
    if (studyId) {
      await api(`/api/researcher/studies/${studyId}`, {
        method: "DELETE",
        headers: researcherHeaders(),
      }).catch(() => undefined);
    }
    if (browser) await stopBrowser(browser.process);
    await rm(profileDirectory, {
      recursive: true,
      force: true,
      maxRetries: 8,
      retryDelay: 125,
    });
  }
}

function researcherHeaders() {
  return {
    Authorization: `Bearer ${researcherKey}`,
    "Content-Type": "application/json",
  };
}

async function api(path, init = {}) {
  const response = await fetch(`${baseUrl}${path}`, init);
  const text = await response.text();
  const payload = text ? JSON.parse(text) : {};
  if (!response.ok) {
    throw new Error(`${init.method ?? "GET"} ${path} failed (${response.status}): ${payload.error ?? text}`);
  }
  return payload;
}

async function launchChrome(executable, userDataDirectory) {
  const process = spawn(
    executable,
    [
      "--headless",
      "--no-sandbox",
      "--disable-gpu",
      "--disable-background-networking",
      "--disable-component-update",
      "--disable-default-apps",
      "--disable-extensions",
      "--disable-sync",
      "--hide-scrollbars",
      "--mute-audio",
      "--no-first-run",
      "--no-default-browser-check",
      "--password-store=basic",
      "--use-mock-keychain",
      "--enable-automation",
      "--remote-debugging-address=127.0.0.1",
      "--remote-debugging-port=0",
      `--user-data-dir=${userDataDirectory}`,
      "about:blank",
    ],
    { stdio: ["ignore", "ignore", "pipe"] },
  );
  const browserWebSocketUrl = await new Promise((resolvePromise, reject) => {
    const timeout = setTimeout(() => reject(new Error("Chrome did not expose a debugging endpoint.")), 15_000);
    process.stderr.setEncoding("utf8");
    process.stderr.on("data", (chunk) => {
      const match = String(chunk).match(/DevTools listening on (ws:\/\/[^\s]+)/);
      if (match) {
        clearTimeout(timeout);
        resolvePromise(match[1]);
      }
    });
    process.once("exit", (code) => {
      clearTimeout(timeout);
      reject(new Error(`Chrome exited before startup (${code ?? "unknown"}).`));
    });
  });
  const port = Number(new URL(browserWebSocketUrl).port);
  return { process, port };
}

async function createPage(port) {
  const response = await fetch(`http://127.0.0.1:${port}/json/new?about:blank`, {
    method: "PUT",
  });
  if (!response.ok) throw new Error(`Could not create Chrome page (${response.status}).`);
  const target = await response.json();
  return new CdpPage(target.webSocketDebuggerUrl);
}

class CdpPage {
  constructor(url) {
    this.socket = new WebSocket(url);
    this.pending = new Map();
    this.nextId = 1;
    this.ready = new Promise((resolvePromise, reject) => {
      this.socket.addEventListener("open", resolvePromise, { once: true });
      this.socket.addEventListener("error", reject, { once: true });
    });
    this.socket.addEventListener("message", (event) => {
      const message = JSON.parse(String(event.data));
      if (!message.id) return;
      const pending = this.pending.get(message.id);
      if (!pending) return;
      this.pending.delete(message.id);
      if (message.error) pending.reject(new Error(message.error.message));
      else pending.resolve(message.result ?? {});
    });
  }

  async send(method, params = {}) {
    await this.ready;
    const id = this.nextId++;
    const result = new Promise((resolvePromise, reject) => {
      this.pending.set(id, { resolve: resolvePromise, reject });
    });
    this.socket.send(JSON.stringify({ id, method, params }));
    return result;
  }

  close() {
    this.socket.close();
  }
}

async function setViewport(page, width, height) {
  await page.send("Emulation.setDeviceMetricsOverride", {
    width,
    height,
    deviceScaleFactor: 1,
    mobile: false,
  });
}

async function navigate(page, url, selector) {
  await page.send("Page.navigate", { url });
  await waitFor(page, `document.readyState === "complete" && Boolean(document.querySelector(${JSON.stringify(selector)}))`);
}

async function settle(page) {
  await waitFor(page, `!document.fonts || document.fonts.status === "loaded"`);
  await new Promise((resolvePromise) => setTimeout(resolvePromise, 250));
}

async function waitFor(page, expression) {
  const deadline = Date.now() + 15_000;
  while (Date.now() < deadline) {
    const result = await page.send("Runtime.evaluate", {
      expression,
      returnByValue: true,
    });
    if (result.result?.value) return;
    await new Promise((resolvePromise) => setTimeout(resolvePromise, 150));
  }
  throw new Error(`Timed out waiting for rendered page: ${expression}`);
}

async function capture(page, path) {
  const screenshot = await page.send("Page.captureScreenshot", {
    format: "png",
    fromSurface: true,
    captureBeyondViewport: false,
  });
  await writeFile(path, Buffer.from(screenshot.data, "base64"));
}

async function stopBrowser(process) {
  if (process.exitCode !== null) return;
  const exited = new Promise((resolvePromise) => {
    process.once("exit", resolvePromise);
  });
  process.kill("SIGTERM");
  await Promise.race([
    exited,
    new Promise((resolvePromise) => setTimeout(resolvePromise, 5_000)),
  ]);
}

await main();
