import vinext from "vinext";
import { defineConfig, loadEnv } from "vite";
import hostingConfig from "./.openai/hosting.json" with { type: "json" };
import { sites } from "./build/sites-vite-plugin.ts";

const SITE_CREATOR_PLACEHOLDER_DATABASE_ID =
  "00000000-0000-4000-8000-000000000000";

const { d1, r2 } = hostingConfig;

// macOS Seatbelt blocks FSEvents, so Codex previews need polling for HMR.
const isCodexSeatbeltSandbox = process.env.CODEX_SANDBOX === "seatbelt";

const localRuntimeVariableNames = [
  "OPENAI_API_KEY",
  "OPENAI_MODEL",
  "INTERVIEW_AI_MODE",
  "RESEARCHER_ALLOWED_USER_IDS",
  "RESEARCHER_ALLOWED_EMAILS",
  "RESEARCHER_API_KEY",
  "RESEARCHER_ALLOW_ANY_AUTHENTICATED",
] as const;

function localBindingConfig(runtimeVariables: Record<string, string>) {
  return {
    main: "./worker/index.ts",
    compatibility_flags: ["nodejs_compat"],
    vars: runtimeVariables,
    d1_databases: d1
      ? [
          {
            binding: d1,
            database_name: "design-council-interviews",
            database_id: SITE_CREATOR_PLACEHOLDER_DATABASE_ID,
          },
        ]
      : [],
    r2_buckets: r2
      ? [
          {
            binding: r2,
            bucket_name: "design-council-interviews",
          },
        ]
      : [],
  };
}

export default defineConfig(async ({ command, mode }) => {
  // Keep Wrangler and Miniflare state project-local. These are non-secret tool
  // settings; application environment belongs in ignored `.env*` files.
  process.env.WRANGLER_WRITE_LOGS ??= "false";
  process.env.WRANGLER_LOG_PATH ??= ".wrangler/logs";
  process.env.MINIFLARE_REGISTRY_PATH ??= ".wrangler/registry";

  // Wrangler snapshots its log path while the Cloudflare plugin is imported.
  const { cloudflare } = await import("@cloudflare/vite-plugin");
  const fileEnvironment = loadEnv(mode, process.cwd(), "");
  const localRuntimeVariables = Object.fromEntries(
    localRuntimeVariableNames.flatMap((name) => {
      const value = process.env[name] ?? fileEnvironment[name];
      return value ? [[name, value]] : [];
    }),
  );

  return {
    server: isCodexSeatbeltSandbox
      ? { watch: { useFsEvents: false, usePolling: true } }
      : undefined,
    plugins: [
      vinext(),
      sites(),
      cloudflare({
        viteEnvironment: { name: "rsc", childEnvironments: ["ssr"] },
        // Never bake local secrets into a production bundle. Sites injects
        // hosted values at runtime; local values exist only in dev workers.
        config: localBindingConfig(
          command === "serve" ? localRuntimeVariables : {},
        ),
      }),
    ],
  };
});
