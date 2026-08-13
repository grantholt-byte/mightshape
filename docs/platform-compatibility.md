# Platform reconciliation for V1

Researched and tested through 2026-08-13 with `codex-cli 0.146.1` and current primary platform documentation.

## Packaging and activation

- V1 is a skills-first plugin: `.codex-plugin/plugin.json` distributes the canonical
  `skills/design-council/` core whose metadata exposes `design-think`, a thin
  `skills/design-council-legacy/` beta-compatibility alias, and the optional hook. This is the
  documented minimal package shape.
- The canonical `SKILL.md` is the router/constitution; details live in references, schemas,
  scripts, and reusable assets. The short entry skill delegates to that same constitution—it
  is not a second product or methodology. Codex initially exposes skill metadata and loads
  instructions when explicitly invoked with `$design-think`, selected through `/skills`, or
  implicitly matched. ChatGPT uses `@design-think`. This is the documented
  progressive-disclosure model.
- `agents/openai.yaml` supplies UI metadata and invocation policy. It is not a custom Council-agent definition.
- Codex custom agent roles live in user/project configuration rather than the documented plugin bundle. V1 therefore treats Council members as Human Models loaded into independent subagent tasks, which is portable across supported Codex clients.

OpenAI plugins cannot register arbitrary slash commands, so `/design-think` is not presented as
a Codex or ChatGPT invocation. Deprecated local custom prompts would appear under
`/prompts:design-think`, are not plugin-distributed, and are not shipped. Legacy
`$design-council` remains available throughout this beta. Claude Code 2.1.216 or later can use
the requested `/design-think` only when the skill is installed standalone; marketplace plugins
must use `/design-council:design-think`, with `/design-council:design-council` retained for beta
compatibility.

Primary docs: [plugin architecture](https://developers.openai.com/plugins/concepts/plugins),
[build plugins](https://developers.openai.com/plugins/build/plugins),
[build skills](https://learn.chatgpt.com/docs/build-skills),
[developer commands](https://learn.chatgpt.com/docs/developer-commands?surface=cli),
[deprecated custom prompts](https://learn.chatgpt.com/docs/custom-prompts), and
[Codex subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents).

## Epistemic independence

Codex supports parallel subagent workflows, but the platform does not document a domain-specific “sealed Council” or “freeze response set” primitive. The skill enforces the invariant operationally:

1. minimal/fresh subagent context where available;
2. one immutable common packet plus one Human Model and that member's own project memory;
3. no sibling response in Round A;
4. wait for all responses;
5. validate and hash the frozen set;
6. anonymize only after freeze.

`sealed_round.py` supplies independent ephemeral `codex exec` passes as a fallback. If neither path exists, the product reports `FACILITATOR_ONLY`; it never labels contaminated serial roleplay as sealed.

## Visual artifacts and process visibility

The shared core generates offline source JSON, self-contained HTML, accessible SVG, Markdown,
and an immutable manifest for affinity and process maps. Browser rendering is an optional
presentation capability, not a methodology dependency:

- interactive ChatGPT/desktop surfaces may preview or open generated HTML where the relevant
  artifact/browser capability is available;
- Codex CLI and IDE flows report local clickable paths and retain the Markdown fallback rather
  than assuming a graphical preview;
- Claude Code skills can generate self-contained HTML and open it in a local browser when one is
  available, while headless sessions use the returned file path.

The skill therefore does not depend on an OpenAI-only UI, a Claude-only output style, an MCP UI,
or remote assets. `VISIBLE` and `WORKSHOP` views expose conclusion-level inputs, artifacts,
transformations, and decision boundaries. They never expose private chain-of-thought, raw tool
logs, or pre-freeze Council content. The shared renderer supplies the same playful sticky-note,
tape, cluster-neighborhood, visible-outlier, and process-lane language on both platforms;
printed IDs/provenance and text fallbacks keep decoration from carrying evidence meaning.

Primary docs: [OpenAI visualizations](https://learn.chatgpt.com/docs/visualizations),
[OpenAI artifact viewer](https://learn.chatgpt.com/docs/artifacts-viewer),
[OpenAI Browser](https://learn.chatgpt.com/docs/browser),
[Claude Code skills](https://code.claude.com/docs/en/skills), and
[Claude Desktop](https://code.claude.com/docs/en/desktop).

## Optional user participation

Codex and Claude both support the same conversational participation contract without a custom
UI: **Watch · Collaborate · One prompt at a time**. Internally these map to `OBSERVE`,
`COLLABORATE`, and `FACILITATED_TURN_BY_TURN`; facilitator support maps to
`NOVICE_ASSISTED`, `GUIDED`, or `LIGHT_TOUCH`. Watching continues without a blocking answer.
One-prompt mode waits for exactly one contribution or control action before advancing, while
collaborative mode lets the user add, move, rename, challenge, or extend material as the
facilitator continues bounded work.

Both adapters use the same project-state records and evidence labels. User contributions are
`USER_PROVIDED`, never human research. Pause, resume, skip, guidance changes, supersession,
hand-back, and exit are portable. During a sealed round, both adapters hold new user input
until freeze rather than changing only unfinished first-round packets. Platform differences
affect invocation syntax and worker mechanics, not facilitation behavior.

## Durable state and hooks

- `.design-council/project.json` plus immutable revision snapshots are canonical. This keeps state readable, inspectable, and portable without a server or undocumented memory contract.
- Codex memories are not used as canonical project state.
- `hooks/hooks.json` is an optional, read-only SessionStart convenience. Plugin hooks require user trust and can be unavailable or disabled, so the skill never depends on it.

Primary docs: [Codex hooks](https://learn.chatgpt.com/docs/hooks) and [Codex configuration](https://learn.chatgpt.com/docs/config-file/config-reference).

## Behavioral evals

OpenAI's current plugin/skill documentation does not define a packaged behavioral-eval service. Claude Code `2.1.229` exposes a `plugin eval` command, but the authenticated account used for this build reported that capability as early-access gated. V1 therefore keeps one vendor-neutral corpus, maps it to both adapters, and ships deterministic unit/contract tests plus an opt-in model-backed harness using authenticated, ephemeral `codex exec` calls and JSON output contracts. This exercises product behavior without requiring an MCP server or custom agent framework; native Claude model invocation remains an additional release check when the publisher account has access and valid authentication.

`evals/run_ab_benchmark.py` adds a separate controlled effectiveness comparison. Its primary arms
receive the identical raw prompt in fresh temporary workspaces and fresh `CODEX_HOME` directories;
only the treatment arm receives the plugin. It counterbalances order and blind A/B labels, keeps
rubrics out of candidate prompts, records candidate usage and latency independently of judge cost,
and reports paired uncertainty and realized-run completeness instead of turning a small smoke run
into an efficacy claim. Quality direction and value assessment remain separate, so token savings
cannot masquerade as quality improvement and verbosity cannot masquerade as value.
`codex exec --ephemeral --json` supplies structured per-turn usage. Claude's documented skill
evaluation guidance likewise recommends fresh with/without-skill baselines and blind comparison;
a native Claude benchmark remains pending until a Claude runtime and authentication are available.

Primary docs: [Codex non-interactive mode](https://learn.chatgpt.com/docs/non-interactive-mode)
and [Claude skill evaluation](https://code.claude.com/docs/en/skills).

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
