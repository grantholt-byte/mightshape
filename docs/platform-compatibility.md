# Platform reconciliation for V1

Researched and tested 2026-08-12 with `codex-cli 0.146.1` and the current OpenAI documentation.

## Packaging and activation

- V1 is a skills-first plugin: `.codex-plugin/plugin.json` distributes `skills/design-council/` and its optional hook. This is the documented minimal package shape.
- `SKILL.md` is the router/constitution; details live in references, schemas, scripts, and reusable assets. Codex initially exposes only skill metadata and loads the instructions when explicitly invoked with `$design-council` or implicitly matched. This is the documented progressive-disclosure model.
- `agents/openai.yaml` supplies UI metadata and invocation policy. It is not a custom Council-agent definition.
- Codex custom agent roles live in user/project configuration rather than the documented plugin bundle. V1 therefore treats Council members as Human Models loaded into independent subagent tasks, which is portable across supported Codex clients.

Primary docs: [plugin architecture](https://developers.openai.com/plugins/concepts/plugins), [build plugins](https://developers.openai.com/plugins/build/plugins), [build skills](https://developers.openai.com/plugins/build/skills), and [Codex subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents).

## Epistemic independence

Codex supports parallel subagent workflows, but the platform does not document a domain-specific “sealed Council” or “freeze response set” primitive. The skill enforces the invariant operationally:

1. minimal/fresh subagent context where available;
2. one immutable common packet plus one Human Model and that member's own project memory;
3. no sibling response in Round A;
4. wait for all responses;
5. validate and hash the frozen set;
6. anonymize only after freeze.

`sealed_round.py` supplies independent ephemeral `codex exec` passes as a fallback. If neither path exists, the product reports `FACILITATOR_ONLY`; it never labels contaminated serial roleplay as sealed.

## Durable state and hooks

- `.design-council/project.json` plus immutable revision snapshots are canonical. This keeps state readable, inspectable, and portable without a server or undocumented memory contract.
- Codex memories are not used as canonical project state.
- `hooks/hooks.json` is an optional, read-only SessionStart convenience. Plugin hooks require user trust and can be unavailable or disabled, so the skill never depends on it.

Primary docs: [Codex hooks](https://learn.chatgpt.com/docs/hooks) and [Codex configuration](https://learn.chatgpt.com/docs/config-file/config-reference).

## Behavioral evals

OpenAI's current plugin/skill documentation does not define a packaged behavioral-eval service. Claude Code `2.1.229` exposes a `plugin eval` command, but the authenticated account used for this build reported that capability as early-access gated. V1 therefore keeps one vendor-neutral corpus, maps it to both adapters, and ships deterministic unit/contract tests plus an opt-in model-backed harness using authenticated, ephemeral `codex exec` calls and JSON output contracts. This exercises product behavior without requiring an MCP server or custom agent framework; native Claude model invocation remains an additional release check when the publisher account has access and valid authentication.

## Shareable interviews

[ChatGPT Sites](https://learn.chatgpt.com/docs/sites) is the current first-party hosted-experience path, so `interview-app/` is a Sites-compatible companion:

- D1 stores structured studies, anonymous participants, consent records, and transcripts.
- R2 is intentionally unused because V1 does not need file uploads.
- OpenAI Responses API calls remain server-side and set `store: false`.
- The core skill can prepare interview guides/studies without hosting.

Sites is in public beta. Availability, public sharing, limits, and analytics depend on plan, region, and workspace settings; there is no standalone Codex CLI/IDE Sites management surface. Every deployed URL is production. New Sites are restricted until sharing is changed, and public publishing may require workspace approval. V1 therefore never invents or promises a link: an operator must inspect, save, deploy, and explicitly choose the audience through Sites.

Sites currently does not support data or inference residency and must not be used for protected health information, payment-card data, financial transactions, or interviews targeting children below the applicable age of digital consent. The companion minimizes PII and includes consent, stop, deletion, retention, and reviewer disclosures; deployment owners remain responsible for applicable law and study governance.

## Intentionally absent

- No MCP server: the core product needs instructions, local scripts, file state, browser research, and native subagents—not a new remote tool boundary.
- No custom agent framework, vector database, authentication stack, or administration dashboard.
- No deployment performed by the build: Sites publishing is an external, production-changing action and depends on the user's account/workspace.
