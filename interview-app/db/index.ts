import { env } from "cloudflare:workers";
import { drizzle } from "drizzle-orm/d1";
import * as schema from "./schema";

export function getD1(): D1Database {
  const runtime = env as unknown as { DB?: D1Database };
  if (!runtime.DB) {
    throw new Error(
      "Cloudflare D1 binding `DB` is unavailable. Declare `DB` in .openai/hosting.json and apply the packaged migration.",
    );
  }
  return runtime.DB;
}

export function getDb() {
  return drizzle(getD1(), { schema });
}
