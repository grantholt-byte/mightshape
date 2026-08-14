import { readFile, mkdir, rename, writeFile, unlink } from "node:fs/promises";
import { existsSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import sharp from "sharp";

const GUID = /^[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}$/i;
const SEMVER = /^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$/;

export interface TeamsPackageOptions {
  appId: string;
  version: string;
  outputPath: string;
}

export interface TeamsPackageResult {
  output_path: string;
  manifest: Record<string, unknown>;
  files: Array<{ name: string; bytes: number }>;
}

interface ZipEntry {
  name: string;
  data: Buffer;
}

function appRoot(): string {
  const current = dirname(fileURLToPath(import.meta.url));
  const candidates = [
    resolve(current, ".."),
    resolve(current, "../.."),
    resolve(process.cwd()),
    resolve(process.cwd(), "collaboration-app"),
  ];
  const located = candidates.find((candidate) =>
    existsSync(resolve(candidate, "manifests", "teams", "manifest.template.json")),
  );
  if (!located) throw new Error("Could not locate the collaboration-app package root.");
  return located;
}

function repositoryRoot(): string {
  return resolve(appRoot(), "..");
}

function crc32(buffer: Buffer): number {
  let crc = 0xffffffff;
  for (const byte of buffer) {
    crc ^= byte;
    for (let bit = 0; bit < 8; bit += 1) {
      crc = (crc >>> 1) ^ (0xedb88320 & -(crc & 1));
    }
  }
  return (crc ^ 0xffffffff) >>> 0;
}

/** Small dependency-free ZIP writer; Teams packages contain only three stored files. */
export function zipEntries(entries: ZipEntry[]): Buffer {
  const localParts: Buffer[] = [];
  const centralParts: Buffer[] = [];
  let offset = 0;
  for (const entry of entries) {
    const name = Buffer.from(entry.name, "utf8");
    const checksum = crc32(entry.data);
    const local = Buffer.alloc(30);
    local.writeUInt32LE(0x04034b50, 0);
    local.writeUInt16LE(20, 4);
    local.writeUInt16LE(0, 6);
    local.writeUInt16LE(0, 8);
    local.writeUInt16LE(0, 10);
    local.writeUInt16LE(0x21, 12);
    local.writeUInt32LE(checksum, 14);
    local.writeUInt32LE(entry.data.byteLength, 18);
    local.writeUInt32LE(entry.data.byteLength, 22);
    local.writeUInt16LE(name.byteLength, 26);
    local.writeUInt16LE(0, 28);
    localParts.push(local, name, entry.data);

    const central = Buffer.alloc(46);
    central.writeUInt32LE(0x02014b50, 0);
    central.writeUInt16LE(20, 4);
    central.writeUInt16LE(20, 6);
    central.writeUInt16LE(0, 8);
    central.writeUInt16LE(0, 10);
    central.writeUInt16LE(0, 12);
    central.writeUInt16LE(0x21, 14);
    central.writeUInt32LE(checksum, 16);
    central.writeUInt32LE(entry.data.byteLength, 20);
    central.writeUInt32LE(entry.data.byteLength, 24);
    central.writeUInt16LE(name.byteLength, 28);
    central.writeUInt16LE(0, 30);
    central.writeUInt16LE(0, 32);
    central.writeUInt16LE(0, 34);
    central.writeUInt16LE(0, 36);
    central.writeUInt32LE(0, 38);
    central.writeUInt32LE(offset, 42);
    centralParts.push(central, name);
    offset += local.byteLength + name.byteLength + entry.data.byteLength;
  }
  const localData = Buffer.concat(localParts);
  const centralData = Buffer.concat(centralParts);
  const end = Buffer.alloc(22);
  end.writeUInt32LE(0x06054b50, 0);
  end.writeUInt16LE(0, 4);
  end.writeUInt16LE(0, 6);
  end.writeUInt16LE(entries.length, 8);
  end.writeUInt16LE(entries.length, 10);
  end.writeUInt32LE(centralData.byteLength, 12);
  end.writeUInt32LE(localData.byteLength, 16);
  end.writeUInt16LE(0, 20);
  return Buffer.concat([localData, centralData, end]);
}

function validateManifest(manifest: Record<string, unknown>, appId: string, version: string): void {
  if (manifest.manifestVersion !== "1.29") throw new Error("Teams manifestVersion must be 1.29.");
  if (manifest.id !== appId || manifest.version !== version) throw new Error("Manifest substitution failed.");
  const bots = manifest.bots;
  if (!Array.isArray(bots) || bots.length !== 1) throw new Error("Teams package must declare one bot.");
  const bot = bots[0] as Record<string, unknown>;
  if (bot.botId !== appId) throw new Error("Bot ID must match the Teams app ID.");
  if (JSON.stringify(bot.scopes) !== JSON.stringify(["team"])) {
    throw new Error("The MightShape Teams adapter must remain limited to team channels.");
  }
  for (const forbidden of ["permissions", "authorization", "validDomains", "webApplicationInfo"]) {
    if (forbidden in manifest) throw new Error(`Least-privilege manifest must not declare ${forbidden}.`);
  }
  const serialized = JSON.stringify(manifest);
  if (serialized.includes("ChannelMessage.Read") || serialized.includes("TeamSettings")) {
    throw new Error("The Teams adapter must not request RSC or Graph channel-reading access.");
  }
}

async function packageEntries(appId: string, version: string): Promise<{ manifest: Record<string, unknown>; entries: ZipEntry[] }> {
  if (!GUID.test(appId)) throw new Error("--app-id must be a valid non-placeholder GUID.");
  if (!SEMVER.test(version)) throw new Error("--version must be semantic versioning compatible.");
  const templatePath = resolve(appRoot(), "manifests", "teams", "manifest.template.json");
  const template = await readFile(templatePath, "utf8");
  const rendered = template
    .replaceAll("${{TEAMS_APP_ID}}", appId)
    .replaceAll("${{MIGHTSHAPE_VERSION}}", version);
  const manifest = JSON.parse(rendered) as Record<string, unknown>;
  validateManifest(manifest, appId, version);

  const color = await sharp(resolve(repositoryRoot(), "assets", "icon.png"))
    .resize(192, 192, { fit: "cover" })
    .png({ compressionLevel: 9 })
    .toBuffer();
  const outlineSvg = Buffer.from(`
    <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 32 32">
      <g fill="none" stroke="#fff" stroke-width="1.6" stroke-linecap="round" opacity=".7">
        <path d="M16 3.6 22.3 5.7 26.2 11.1 26.2 16.9 22.3 22.3 16 24.4 9.7 22.3 5.8 16.9 5.8 11.1 9.7 5.7Z"/>
        <path d="M16 10.4c3.2 0 5.6 2.3 5.6 5.6 0 3.4-2.4 5.7-5.6 5.7s-5.6-2.3-5.6-5.7c0-3.3 2.4-5.6 5.6-5.6Z"/>
      </g>
      <g fill="#fff">
        <circle cx="16" cy="3.6" r="1.55"/><circle cx="22.3" cy="5.7" r="1.55"/>
        <circle cx="26.2" cy="11.1" r="1.55"/><circle cx="26.2" cy="16.9" r="1.55"/>
        <circle cx="22.3" cy="22.3" r="1.55"/><circle cx="16" cy="24.4" r="1.55"/>
        <circle cx="9.7" cy="22.3" r="1.55"/><circle cx="5.8" cy="16.9" r="1.55"/>
        <circle cx="5.8" cy="11.1" r="1.55"/><circle cx="9.7" cy="5.7" r="1.55"/>
      </g>
    </svg>
  `);
  const outline = await sharp(outlineSvg).resize(32, 32).png({ compressionLevel: 9 }).toBuffer();
  return {
    manifest,
    entries: [
      { name: "manifest.json", data: Buffer.from(`${JSON.stringify(manifest, null, 2)}\n`, "utf8") },
      { name: "color.png", data: color },
      { name: "outline.png", data: outline },
    ],
  };
}

export async function buildTeamsPackage(options: TeamsPackageOptions): Promise<TeamsPackageResult> {
  const { manifest, entries } = await packageEntries(options.appId, options.version);
  const output = resolve(options.outputPath);
  await mkdir(dirname(output), { recursive: true });
  const temporary = `${output}.${process.pid}.${Date.now()}.tmp`;
  try {
    await writeFile(temporary, zipEntries(entries), { flag: "wx", mode: 0o600 });
    await rename(temporary, output);
  } catch (error) {
    await unlink(temporary).catch(() => undefined);
    throw error;
  }
  return {
    output_path: output,
    manifest,
    files: entries.map((entry) => ({ name: entry.name, bytes: entry.data.byteLength })),
  };
}

function argument(name: string): string | undefined {
  const index = process.argv.indexOf(name);
  return index >= 0 ? process.argv[index + 1] : undefined;
}

async function main(): Promise<void> {
  const packageJson = JSON.parse(await readFile(resolve(appRoot(), "package.json"), "utf8")) as { version: string };
  const appId = argument("--app-id") ?? process.env.TEAMS_APP_ID ?? "";
  const version = argument("--version") ?? packageJson.version;
  const output = argument("--output") ?? resolve(repositoryRoot(), "dist", "teams", `mightshape-teams-${version}.zip`);
  const result = await buildTeamsPackage({ appId, version, outputPath: output });
  process.stdout.write(`${JSON.stringify(result, null, 2)}\n`);
}

const entry = process.argv[1];
if (entry && import.meta.url === pathToFileURL(entry).href) {
  main().catch((error) => {
    process.stderr.write(`Teams package build failed: ${error instanceof Error ? error.message : String(error)}\n`);
    process.exitCode = 1;
  });
}
