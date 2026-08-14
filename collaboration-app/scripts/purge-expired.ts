import { resolve } from "node:path";
import { pathToFileURL } from "node:url";
import { MockFacilitatorProvider } from "../src/core/facilitator.js";
import { WorkshopService } from "../src/core/service.js";
import { FileWorkshopStore } from "../src/core/store.js";

/**
 * Delete workshop records whose disclosed retention deadline has elapsed, plus
 * their generated artifacts. Run this from the deployment scheduler; it makes
 * no model or platform API calls and never prints participant content.
 */
export async function purgeExpired(dataRoot = resolve(process.env.DC_TEAM_DATA_DIR ?? ".data")): Promise<string[]> {
  const service = new WorkshopService(
    new FileWorkshopStore(resolve(dataRoot, "sessions")),
    new MockFacilitatorProvider(),
    dataRoot,
  );
  return service.purgeExpired();
}

if (process.argv[1] && import.meta.url === pathToFileURL(resolve(process.argv[1])).href) {
  purgeExpired()
    .then((deleted) => {
      process.stdout.write(`Purged ${deleted.length} expired MightShape workshop(s).\n`);
    })
    .catch((error: unknown) => {
      process.stderr.write(`Retention purge failed: ${error instanceof Error ? error.message : String(error)}\n`);
      process.exitCode = 1;
    });
}
