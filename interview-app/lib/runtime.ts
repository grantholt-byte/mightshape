import { env } from "cloudflare:workers";

export type DesignCouncilEnv = {
  DB: D1Database;
  OPENAI_API_KEY?: string;
  OPENAI_MODEL?: string;
  INTERVIEW_AI_MODE?: string;
  RESEARCHER_ALLOWED_USER_IDS?: string;
  RESEARCHER_ALLOWED_EMAILS?: string;
  RESEARCHER_API_KEY?: string;
  RESEARCHER_ALLOW_ANY_AUTHENTICATED?: string;
};

export function runtimeEnv(): DesignCouncilEnv {
  return env as unknown as DesignCouncilEnv;
}
