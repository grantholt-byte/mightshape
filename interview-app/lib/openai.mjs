import {
  buildInterviewerInput,
  buildInterviewerPrompt,
  mockInterviewTurn,
  normalizeModelTurn,
} from "./interview.mjs";

export const DEFAULT_OPENAI_MODEL = "gpt-5.6-sol";

export const INTERVIEW_TURN_SCHEMA = Object.freeze({
  type: "object",
  additionalProperties: false,
  required: [
    "reply",
    "covered_topics",
    "emerging_threads",
    "follow_up_priorities",
    "should_stop",
    "closing_reason",
  ],
  properties: {
    reply: { type: "string" },
    covered_topics: { type: "array", items: { type: "string" } },
    emerging_threads: { type: "array", items: { type: "string" } },
    follow_up_priorities: { type: "array", items: { type: "string" } },
    should_stop: { type: "boolean" },
    closing_reason: { type: ["string", "null"] },
  },
});

/**
 * @param {{study: Record<string, unknown>, state: Record<string, unknown>, messages: Array<{role:string,content:string}>, participantCode:string, participantText:string, participantAction?:string|null}} input
 * @param {{mode?:string, apiKey?:string, model?:string, safetyIdentifier?:string, fetchImpl?:typeof fetch, timeoutMs?:number}} config
 */
export async function generateInterviewTurn(input, config = {}) {
  const mode = config.mode ?? "openai";
  if (mode === "mock") return mockInterviewTurn(input);
  if (mode !== "openai") throw new Error(`Unsupported interview AI mode: ${mode}`);
  if (!config.apiKey) {
    throw new Error(
      "The live interviewer is not configured. Set OPENAI_API_KEY or use INTERVIEW_AI_MODE=mock for local validation.",
    );
  }

  const fetchImpl = config.fetchImpl ?? fetch;
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), config.timeoutMs ?? 30_000);
  const body = {
    model: config.model || DEFAULT_OPENAI_MODEL,
    store: false,
    safety_identifier: config.safetyIdentifier,
    reasoning: { effort: "low" },
    instructions: buildInterviewerPrompt(input),
    input: buildInterviewerInput(input.messages),
    max_output_tokens: 700,
    text: {
      verbosity: "low",
      format: {
        type: "json_schema",
        name: "design_council_interview_turn",
        strict: true,
        schema: INTERVIEW_TURN_SCHEMA,
      },
    },
  };

  try {
    const response = await fetchImpl("https://api.openai.com/v1/responses", {
      method: "POST",
      headers: {
        Authorization: `Bearer ${config.apiKey}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
      signal: controller.signal,
    });
    if (!response.ok) {
      const requestId = response.headers.get("x-request-id");
      throw new Error(
        `OpenAI Responses request failed (${response.status})${requestId ? ` [${requestId}]` : ""}.`,
      );
    }
    const payload = await response.json();
    const outputText = extractOutputText(payload);
    if (!outputText) throw new Error("OpenAI returned no interview text.");
    return normalizeModelTurn(JSON.parse(outputText), input.study);
  } finally {
    clearTimeout(timer);
  }
}

/** @param {unknown} payload */
export function extractOutputText(payload) {
  if (!payload || typeof payload !== "object") return "";
  const record = /** @type {Record<string, unknown>} */ (payload);
  if (typeof record.output_text === "string") return record.output_text;
  if (!Array.isArray(record.output)) return "";
  for (const item of record.output) {
    if (!item || typeof item !== "object") continue;
    const content = /** @type {Record<string, unknown>} */ (item).content;
    if (!Array.isArray(content)) continue;
    for (const part of content) {
      if (part && typeof part === "object") {
        const text = /** @type {Record<string, unknown>} */ (part).text;
        if (typeof text === "string") return text;
      }
    }
  }
  return "";
}
