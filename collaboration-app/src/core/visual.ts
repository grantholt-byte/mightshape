import { createHash } from "node:crypto";
import { access, mkdir, readFile, writeFile, chmod } from "node:fs/promises";
import { dirname, resolve, sep } from "node:path";
import { fileURLToPath } from "node:url";
import { spawn } from "node:child_process";
import sharp from "sharp";
import { cleanText, type Platform, type TeamWorkshopSession, type WorkshopArtifactRef } from "./contracts.js";
import type { VisualArtifact, WorkshopSynthesis } from "./facilitator.js";
import { WorkshopError } from "./session.js";

export interface RenderedWorkshopVisual {
  artifact: VisualArtifact;
  png: Buffer;
  png_path: string;
  png_sha256: string;
  alt_text: string;
  /** Bounded portable/card summary; never contains raw platform identifiers. */
  text_summary: string;
  /** Complete source-linked channel alternative, delivered in platform-safe chunks. */
  text_fallback: string;
  artifact_ref: WorkshopArtifactRef;
}

interface StoredWorkshopVisual {
  schema_version: "1.0.0";
  artifact_id: string;
  artifact_type: "AFFINITY_MAP" | "PROCESS_MAP";
  png_filename: string;
  png_sha256: string;
  alt_text: string;
  text_summary: string;
  text_fallback: string;
}

const MAX_PORTABLE_TEXT_SUMMARY = 5_000;

/** Split an accessible fallback without dropping content or depending on a platform SDK. */
export function chunkText(value: string, maxLength: number): string[] {
  if (!Number.isInteger(maxLength) || maxLength < 200) throw new Error("maxLength must be at least 200 characters.");
  const chunks: string[] = [];
  let remaining = value.trim();
  while (remaining.length > maxLength) {
    let boundary = remaining.lastIndexOf("\n\n", maxLength);
    if (boundary < Math.floor(maxLength / 2)) boundary = maxLength;
    chunks.push(remaining.slice(0, boundary).trimEnd());
    remaining = remaining.slice(boundary).trimStart();
  }
  if (remaining) chunks.push(remaining);
  return chunks;
}

function repositoryRoot(): string {
  // Prefer the current name while retaining the former environment variable as
  // a migration-only fallback for already deployed services.
  const configured = process.env.MIGHTSHAPE_REPO_ROOT ?? process.env.HUNCHGARDEN_REPO_ROOT;
  if (configured) return resolve(configured);
  const current = dirname(fileURLToPath(import.meta.url));
  return resolve(current, "../../../..");
}

async function visualRenderer(root: string): Promise<string> {
  const candidates = [
    resolve(root, "skills/mightshape/scripts/render_visual.py"),
    resolve(root, "skills/hunchgarden/scripts/render_visual.py"),
  ];
  for (const candidate of candidates) {
    try {
      await access(candidate);
      return candidate;
    } catch (error) {
      if ((error as NodeJS.ErrnoException).code !== "ENOENT") throw error;
    }
  }
  throw new Error("The canonical workshop visual renderer could not be located.");
}

async function run(command: string, args: string[], cwd: string): Promise<{ stdout: string; stderr: string }> {
  return new Promise((accept, reject) => {
    const child = spawn(command, args, { cwd, stdio: ["ignore", "pipe", "pipe"] });
    const stdout: Buffer[] = [];
    const stderr: Buffer[] = [];
    child.stdout.on("data", (chunk: Buffer) => stdout.push(chunk));
    child.stderr.on("data", (chunk: Buffer) => stderr.push(chunk));
    child.on("error", reject);
    child.on("close", (code) => {
      const output = Buffer.concat(stdout).toString("utf8");
      const error = Buffer.concat(stderr).toString("utf8");
      if (code === 0) accept({ stdout: output, stderr: error });
      else reject(new Error(`Visual renderer failed (${code}): ${error || output}`));
    });
  });
}

function platformLimit(platform: Platform): { width: number; height: number; bytes: number } {
  // Teams bot activities have a much smaller practical message budget than a
  // normal file upload. Keep raw PNG bytes below 48 KB so base64 plus card JSON
  // remains comfortably below the documented ~100 KB activity limit.
  if (platform === "TEAMS") return { width: 900, height: 900, bytes: 48_000 };
  if (platform === "DISCORD") return { width: 1_600, height: 1_600, bytes: 9_500_000 };
  return { width: 1_600, height: 1_600, bytes: 5_000_000 };
}

async function pngWithinLimit(svg: Buffer, platform: Platform): Promise<Buffer> {
  const limit = platformLimit(platform);
  const widths = platform === "TEAMS" ? [limit.width, 768, 640, 512, 420] : [limit.width, 1_280, 1_024];
  for (const width of widths) {
    const pipeline = sharp(svg, { density: 144 })
      .resize({ width, height: limit.height, fit: "inside", withoutEnlargement: true });
    const png = await (platform === "TEAMS"
      ? pipeline.png({ compressionLevel: 9, adaptiveFiltering: true, palette: true, colours: 128, quality: 90 })
      : pipeline.png({ compressionLevel: 9, adaptiveFiltering: true, palette: false }))
      .toBuffer();
    if (png.byteLength <= limit.bytes) return png;
  }
  throw new Error(`Rendered ${platform} visual exceeds ${limit.bytes} bytes after bounded resizing.`);
}

function visualAlt(session: TeamWorkshopSession, synthesis: WorkshopSynthesis): string {
  const records = session.contributions.filter((item) => item.status === "ACTIVE").length;
  const type = synthesis.artifact.artifact_type === "PROCESS_MAP" ? "process map" : "sticky-note affinity map";
  const outlier = synthesis.outlier_worth_saving ? " A preserved outlier is described in the text summary." : "";
  return `${type} for ${session.exercise.toLowerCase().replaceAll("_", " ")} with ${records} USER_PROVIDED contribution${records === 1 ? "" : "s"}. ${synthesis.artifact.summary}${outlier}`.slice(0, 1_000);
}

export function buildFrozenSourceFallback(session: TeamWorkshopSession, reason: string): string {
  const sourceLines = session.contributions
    .filter((item) => item.status === "ACTIVE")
    .map((item) => `${item.id} · USER_PROVIDED\n${item.content}`);
  return [
    "◇ MIGHTSHAPE · TEXT FALLBACK",
    reason,
    "Evidence boundary: teammate input is USER_PROVIDED design material, not human-research evidence.",
    "SOURCE SET",
    sourceLines.join("\n\n") || "No active contributions.",
  ].join("\n\n");
}

function artifactStructure(synthesis: WorkshopSynthesis): string[] {
  const data = synthesis.artifact.data;
  if (synthesis.artifact.artifact_type === "AFFINITY_MAP") {
    const clusters = Array.isArray(data.clusters) ? data.clusters : [];
    const outliers = Array.isArray(data.outliers) ? data.outliers : [];
    const lines = clusters.map((raw) => {
      const cluster = raw as { label?: unknown; description?: unknown; record_ids?: unknown };
      const ids = Array.isArray(cluster.record_ids) ? cluster.record_ids.join(", ") : "";
      return `Cluster · ${String(cluster.label ?? "Unlabeled")} [${ids}]\n${String(cluster.description ?? "")}`;
    });
    for (const raw of outliers) {
      const note = raw as { id?: unknown; text?: unknown };
      lines.push(`Outlier · ${String(note.id ?? "UNKNOWN")}\n${String(note.text ?? "")}`);
    }
    return lines;
  }
  const lanes = Array.isArray(data.lanes) ? data.lanes : [];
  const steps = Array.isArray(data.steps) ? data.steps : [];
  const transitions = Array.isArray(data.transitions) ? data.transitions : [];
  return [
    ...lanes.map((raw) => {
      const lane = raw as { id?: unknown; label?: unknown };
      return `Lane · ${String(lane.id ?? "UNKNOWN")} · ${String(lane.label ?? "")}`;
    }),
    ...steps.map((raw) => {
      const step = raw as { id?: unknown; lane_id?: unknown; label?: unknown; detail?: unknown };
      return `Step · ${String(step.id ?? "UNKNOWN")} · lane ${String(step.lane_id ?? "UNKNOWN")} · ${String(step.label ?? "")}\n${String(step.detail ?? "")}`;
    }),
    ...transitions.map((raw) => {
      const transition = raw as {
        id?: unknown;
        from_step_id?: unknown;
        to_step_id?: unknown;
        label?: unknown;
        provenance?: unknown;
        source_ids?: unknown;
      };
      const ids = Array.isArray(transition.source_ids) ? transition.source_ids.join(", ") : "";
      return `Transition · ${String(transition.id ?? "UNKNOWN")} · ${String(transition.from_step_id ?? "?")} → ${String(transition.to_step_id ?? "?")} · ${String(transition.provenance ?? "UNKNOWN")} [${ids}]\n${String(transition.label ?? "")}`;
    }),
  ];
}

export function buildWorkshopTextFallback(
  session: TeamWorkshopSession,
  synthesis: WorkshopSynthesis,
): string {
  const source = buildFrozenSourceFallback(session, "The source set is frozen.");
  const tensions = synthesis.tensions.length ? synthesis.tensions.map((item) => `- ${item}`).join("\n") : "- None recorded";
  const outlier = synthesis.outlier_worth_saving ?? "None recorded";
  const limitations = synthesis.artifact.limitations.map((item) => `- ${item}`).join("\n");
  return [
    source,
    `VISUAL STRUCTURE · ${synthesis.artifact.artifact_type}`,
    artifactStructure(synthesis).join("\n\n") || "No visual structure was returned.",
    "MIGHTSHAPE SYNTHESIS",
    synthesis.synthesis,
    `TENSIONS\n${tensions}`,
    `OUTLIER WORTH SAVING\n${outlier}`,
    `LIMITATIONS\n${limitations}`,
    `NEXT MOVE\n${synthesis.next_move}`,
  ].join("\n\n");
}

function clipped(value: string, maximum: number): string {
  const normalized = cleanText(value, maximum + 1);
  return normalized.length <= maximum ? normalized : `${normalized.slice(0, Math.max(0, maximum - 1)).trimEnd()}…`;
}

/**
 * Portable/card summaries are intentionally bounded. The complete contribution
 * wording remains in session state and buildWorkshopTextFallback(), while this
 * compact form still names every source record and preserves the decision-facing
 * synthesis, limitations, outlier, and next move.
 */
export function buildWorkshopTextSummary(
  session: TeamWorkshopSession,
  synthesis: WorkshopSynthesis,
): string {
  const ids = session.contributions
    .filter((item) => item.status === "ACTIVE")
    .map((item) => item.id);
  const tensions = synthesis.tensions.length ? synthesis.tensions.join(" | ") : "None recorded";
  const limitations = synthesis.artifact.limitations.length
    ? synthesis.artifact.limitations.join(" | ")
    : "None recorded";
  const result = [
    "◇ MIGHTSHAPE · ACCESSIBLE VISUAL SUMMARY",
    `ARTIFACT · ${synthesis.artifact.id} · ${synthesis.artifact.artifact_type}\n${clipped(synthesis.artifact.title, 200)}`,
    `SOURCE CONTRIBUTION IDS (${ids.length})\n${ids.join(", ")}`,
    "Evidence boundary: every source ID is USER_PROVIDED design material, not human-research evidence. Full source wording remains in the workshop record and complete channel fallback.",
    `SYNTHESIS · DESIGN_COUNCIL\n${clipped(synthesis.synthesis, 900)}`,
    `TENSIONS\n${clipped(tensions, 550)}`,
    `OUTLIER WORTH SAVING\n${clipped(synthesis.outlier_worth_saving ?? "None recorded", 350)}`,
    `LIMITATIONS\n${clipped(limitations, 500)}`,
    `NEXT MOVE\n${clipped(synthesis.next_move, 500)}`,
  ].join("\n\n");
  if (result.length > MAX_PORTABLE_TEXT_SUMMARY) {
    throw new Error(
      `Portable workshop summary exceeds ${MAX_PORTABLE_TEXT_SUMMARY} characters; reduce the contribution set before delivery.`,
    );
  }
  return result;
}

export async function renderWorkshopVisual(
  session: TeamWorkshopSession,
  synthesis: WorkshopSynthesis,
  platform: Platform,
  dataRoot: string,
): Promise<RenderedWorkshopVisual> {
  const root = repositoryRoot();
  const renderer = await visualRenderer(root);
  const artifactRoot = resolve(dataRoot, "artifacts", session.id, synthesis.artifact.id);
  await mkdir(artifactRoot, { recursive: true, mode: 0o700 });
  const inputPath = resolve(artifactRoot, "input.json");
  await writeFile(inputPath, `${JSON.stringify(synthesis.artifact, null, 2)}\n`, { mode: 0o600 });
  const outputRoot = resolve(artifactRoot, "workbench");
  await run(process.env.PYTHON_BIN ?? "python3", [renderer, inputPath, "--output-dir", outputRoot], root);
  const manifest = JSON.parse(await readFile(resolve(outputRoot, "manifest.json"), "utf8")) as {
    files: { svg: string };
  };
  const svg = await readFile(resolve(outputRoot, manifest.files.svg));
  const png = await pngWithinLimit(svg, platform);
  const pngPath = resolve(artifactRoot, `${synthesis.artifact.id.toLowerCase()}.png`);
  await writeFile(pngPath, png, { mode: 0o600 });
  await chmod(pngPath, 0o600);
  const pngSha = createHash("sha256").update(png).digest("hex");
  const alt = visualAlt(session, synthesis);
  const summary = buildWorkshopTextSummary(session, synthesis);
  const fallback = buildWorkshopTextFallback(session, synthesis);
  const stored: StoredWorkshopVisual = {
    schema_version: "1.0.0",
    artifact_id: synthesis.artifact.id,
    artifact_type: synthesis.artifact.artifact_type,
    png_filename: `${synthesis.artifact.id.toLowerCase()}.png`,
    png_sha256: pngSha,
    alt_text: alt,
    text_summary: summary,
    text_fallback: fallback,
  };
  await writeFile(resolve(artifactRoot, "delivery.json"), `${JSON.stringify(stored, null, 2)}\n`, {
    mode: 0o600,
  });
  const artifactRef: WorkshopArtifactRef = {
    artifact_id: synthesis.artifact.id,
    artifact_type: synthesis.artifact.artifact_type,
    source_contribution_ids: session.contributions
      .filter((item) => item.status === "ACTIVE")
      .map((item) => item.id),
    png_sha256: pngSha,
    alt_text: alt,
    text_summary: summary,
    recorded_at: new Date().toISOString(),
  };
  return {
    artifact: synthesis.artifact,
    png,
    png_path: pngPath,
    png_sha256: pngSha,
    alt_text: alt,
    text_summary: summary,
    text_fallback: fallback,
    artifact_ref: artifactRef,
  };
}

/**
 * Reload the immutable rendered artifact for delivery-only recovery. This never
 * calls a facilitator and verifies the persisted PNG against portable state.
 */
export async function loadWorkshopVisual(
  session: TeamWorkshopSession,
  dataRoot: string,
  artifactId?: string,
): Promise<RenderedWorkshopVisual> {
  const reference = artifactId
    ? session.artifacts.find((item) => item.artifact_id === artifactId)
    : session.artifacts.at(-1);
  if (!reference || !/^VA-[A-Z0-9][A-Z0-9-]*$/.test(reference.artifact_id)) {
    throw new WorkshopError("No recoverable workshop visual is recorded.", "ARTIFACT_NOT_FOUND");
  }
  const artifactsRoot = resolve(dataRoot, "artifacts");
  const artifactRoot = resolve(artifactsRoot, session.id, reference.artifact_id);
  if (!artifactRoot.startsWith(`${artifactsRoot}${sep}`)) {
    throw new WorkshopError("Workshop artifact path escaped the data root.", "INVALID_SESSION_ID");
  }
  try {
    const artifact = JSON.parse(await readFile(resolve(artifactRoot, "input.json"), "utf8")) as VisualArtifact;
    const stored = JSON.parse(await readFile(resolve(artifactRoot, "delivery.json"), "utf8")) as StoredWorkshopVisual;
    if (
      stored.schema_version !== "1.0.0" ||
      stored.artifact_id !== reference.artifact_id ||
      stored.artifact_type !== reference.artifact_type ||
      stored.png_sha256 !== reference.png_sha256 ||
      stored.alt_text !== reference.alt_text ||
      stored.text_summary !== reference.text_summary ||
      artifact.id !== reference.artifact_id ||
      artifact.artifact_type !== reference.artifact_type ||
      !/^[a-z0-9-]+\.png$/.test(stored.png_filename)
    ) {
      throw new Error("Persisted workshop visual metadata does not match portable state.");
    }
    const pngPath = resolve(artifactRoot, stored.png_filename);
    if (!pngPath.startsWith(`${artifactRoot}${sep}`)) throw new Error("Persisted PNG path is invalid.");
    const png = await readFile(pngPath);
    const actualSha = createHash("sha256").update(png).digest("hex");
    if (actualSha !== stored.png_sha256) throw new Error("Persisted workshop PNG failed integrity verification.");
    return {
      artifact,
      png,
      png_path: pngPath,
      png_sha256: actualSha,
      alt_text: stored.alt_text,
      text_summary: stored.text_summary,
      text_fallback: stored.text_fallback,
      artifact_ref: structuredClone(reference),
    };
  } catch (error) {
    if (error instanceof WorkshopError) throw error;
    throw new WorkshopError(
      "The recorded workshop visual could not be recovered. Local state was retained for inspection.",
      "ARTIFACT_RECOVERY_FAILED",
      { cause: error },
    );
  }
}
