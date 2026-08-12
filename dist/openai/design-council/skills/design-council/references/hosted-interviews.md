# Optional hosted human interviews

## Current platform fit

ChatGPT Sites is the current first-party OpenAI hosted surface for a shareable participant experience. It is distinct from plugin/MCP UI, which renders inside ChatGPT and is not a standalone public interview link. Sites is public beta; availability and public sharing vary by plan, region, workspace policy, and admin permissions. There is no standalone Sites deployment manager in Codex CLI or the IDE.

Core Inquiry Lab must always be able to prepare an interview guide, consent copy, fieldwork kit, and local study without Sites.

## Create-an-interview-link route

1. Confirm the study has a research goal, topics, approximate duration, data plan, reviewer audience, quotation policy, stop condition, and contact/rights path.
2. Apply Solution Blackout unless concept disclosure is methodologically justified.
3. Set a project exposure level; prefer `LEVEL_0_PROBLEM_ONLY` for early empathy work.
4. Run Disclosure Guard and approve a separate `ExternalStudyPacket`; never send private `InternalStudy` content directly.
5. Minimize fields; use `P-###` rather than names/emails by default.
6. Check whether the current runtime exposes Sites creation/version/deployment tools and whether the account/workspace permits the required access level.
7. If unavailable, return the validated companion source and a truthful Sites handoff. Never invent a URL or imply it is live.
8. If available, create or reuse a Site, save a version, inspect it, then deploy privately by default. Obtain explicit user approval before shared/public access.
9. Open the resulting URL as a participant and verify disclosure, consent, stop, transcript, and intended audience.

Every deployed Sites URL is production. A saved version is the review boundary.

## Companion architecture

`interview-app/` uses the installed Sites starter and Cloudflare-compatible ESM output:

- D1 stores studies, consent receipt/version, participant IDs, messages, topic coverage, Solution Blackout/Concept Reveal status, completion/stop/deletion state.
- R2 is unused.
- A high-entropy study token identifies the anonymous participant route.
- OpenAI Responses API calls happen server-side; the API key is a Sites secret, never client code or `.openai/hosting.json`.
- Requests use `store: false`; D1 is the application's canonical transcript store.
- A deterministic local mock allows tests without credentials.
- Researcher access must enforce authorization server-side. Sign in with ChatGPT establishes identity, not authorization or workspace membership; use an explicit allowlist or ownership check.

## Participant disclosure

Before collection, clearly show:

- the interviewer is AI;
- research purpose and approximate duration;
- information collected and who may review it;
- whether de-identified quotations may be used;
- the ability to stop;
- a contact/rights route and retention/deletion summary appropriate to the deployment.

Do not imply the AI is a human researcher. Do not begin substantive questions before affirmative consent.

The project owner's consent to any future Design Council methodological-learning program is separate and never authorizes participant transcript or quotation use.

## Safety and data constraints

Sites currently lacks data and inference residency. Do not use the companion for protected health information, payment-card data, under-age participants, or work whose obligations the platform cannot meet. The deployer is responsible for applicable privacy/data-protection law, notice, consent where required, minimization, security, retention/deletion, and rights handling.

Default to anonymous public participation only when public sharing is explicitly approved and appropriate. New Sites begin owner/admin-only. Enterprise public publishing is off by default unless enabled by an admin.

## Official references

- [ChatGPT Sites](https://learn.chatgpt.com/docs/sites)
- [Sites availability and limits](https://help.openai.com/en/articles/20001339)
- [Workspace Sites controls](https://help.openai.com/en/articles/20001338)
- [Sites data responsibilities](https://help.openai.com/en/articles/20001340)
- [Responses API](https://developers.openai.com/api/docs/guides/migrate-to-responses)
- [OpenAI API data controls](https://developers.openai.com/api/docs/guides/your-data)
