# Architecture: one product, two adapters

## Source of truth

Design Council has one canonical product core under `skills/design-council/`:

- `references/`: constitution, ten Human Models, Council protocols, Inquiry Lab,
  stage/method guidance, UX, evidence, and source notes;
- `schemas/`: portable records for project state, inquiry, evidence, and Exchange readiness;
- `scripts/`: deterministic facilitation, validation, state, and sealed-round helpers;
- `assets/templates/`: reusable project artifacts;
- `SKILL.md`: the shared routing constitution whose skill metadata exposes the primary
  `design-think` entry point.

`skills/design-council-legacy/` is the intentionally thin beta-compatibility adapter. It
delegates to the canonical constitution and does not duplicate Human Models, methodology,
state, or policy.

The repository layout predates the platform-adapter addendum, so the core remains in its
validated installable location rather than moving every file. That is an intentional
low-risk choice, not two products.

```text
canonical core + routing constitution
              │
       ┌──────┴──────┐
       │             │
OpenAI adapter   Claude adapter
manifest/hooks   manifest/Agent appendix
       │             │
dist/openai      dist/claude
```

`scripts/build_packages.py` creates both self-contained packages. Each package receives the
same canonical Design Council core (exposed as `design-think`) and thin legacy alias. The Claude
package then appends only Claude-specific invocation, Agent, Sites, and hook mechanics. It does
not fork Human Models or methodology. `scripts/check_cross-platform-drift.py` hashes every
shared file, checks all signature invariants, confirms ten identical Human Models, and
synchronizes versions.

## Platform differences

| Concern | OpenAI / Codex | Claude Code |
|---|---|---|
| Manifest | `.codex-plugin/plugin.json` | `.claude-plugin/plugin.json` |
| Primary explicit invocation | `$design-think` or `/skills`; ChatGPT uses `@design-think` | `/design-council:design-think` |
| Optional short form / beta compatibility | Legacy `$design-council` | Standalone skill only: `/design-think`; legacy plugin skill: `/design-council:design-council` |
| Independent workers | Native Codex subagents; isolated `codex exec` fallback | Fresh Agent workers via `design-council:sealed-member` |
| Optional state recovery | Trust-gated SessionStart hook | Skill reads canonical state on activation |
| Hosted companion | ChatGPT Sites-compatible | Can develop the app; cannot claim a Sites deploy |

These differences affect mechanics only. Council identities, evidence provenance,
methods, memory, Minority Report, Inquiry Lab, debt, and Build Gate are byte-identical.
OpenAI's plugin contract does not permit an arbitrary `/design-think` alias; deprecated
custom prompts would invoke under `/prompts:` and are intentionally not shipped.

## Portable state

Both adapters read `.design-council/project.json` and the same revision snapshots. The
schema contains no OpenAI-, Codex-, Claude-, or Anthropic-specific fields. Platform
metadata should be optional and namespaced if a future adapter truly needs it; core
evidence, frames, experiments, Council memories, and participation sessions remain portable.

## Participation and adaptive facilitation

Participation is a platform-neutral conversation/state boundary, not a vendor-specific form.
The user-facing choice is **Watch · Collaborate · One prompt at a time**, represented in state
as `OBSERVE`, `COLLABORATE`, or `FACILITATED_TURN_BY_TURN`. Watching is the non-blocking
default. A joining user starts at `NOVICE_ASSISTED` unless fluency is evident and may switch
to `GUIDED` or `LIGHT_TOUCH` at any time.

The facilitator exposes only the immediate purpose and mindset, one method-safe example, and one
bounded prompt. Stable `PS-`, `UP-`, and `UC-` records preserve sessions, prompts, and
`USER_PROVIDED` contributions. Board revisions record material moves, renames, additions, and
supersessions rather than redrawing an unchanged wall. Pause, resume, skip, undo-as-supersede,
hand-back, and exit are durable controls. Participation records are design-process material,
not human interviews or observed behavior.

Sealed independence remains upstream of interaction convenience. Input accepted before Round A
enters every member's common packet identically; new input received while the round is open is
held until freeze. Neither adapter may selectively update unfinished members.

## Visual workbench

Spatial workshop outputs are derived from a platform-neutral JSON contract by the
standard-library renderer in the canonical skill. It emits the same self-contained
HTML, SVG, and Markdown fallback on both adapters beneath
`.design-council/artifacts/<artifact-id>/`. No CDN, telemetry, browser extension,
custom MCP UI, or hosted service is required.

The renderer deliberately uses a warm, whimsical studio vocabulary—sticky-note paper,
tape, folded corners, soft shadows, colorful dashed cluster neighborhoods, playful actor
lanes, handoff paths, and sparing doodles. These decorations are deterministic presentation,
not epistemic encoding. Provenance always remains explicit in text, and accessible fallbacks
carry the same records and outliers.

Interactive desktop surfaces may open the local HTML. Headless CLI/IDE sessions
always return inspectable paths and retain the text fallback. Artifact manifests
carry input hashes, provenance labels, source references, and versioned paths;
platform preview state never enters canonical project state.

## Evaluation boundary

The paired A/B harness keeps outcome evaluation outside the product core. It runs
the same raw prompt and model settings in isolated clean workspaces, with the
repo-local skill absent for the baseline and present for treatment. Arm order and
blind labels are randomized. Candidate token usage and wall time are measured
separately from judge cost, and reports include paired quality change, uncertainty,
token overhead, and marginal blind-quality gain per 1,000 additional generation tokens
rather than treating verbosity as success. The marginal measure retains its units and is
not presented as monetary ROI. Important-value thresholds,
realized-run completeness, reproducibility metadata, and straightforward-task routing cases
prevent an incomplete or single-pair smoke run from becoming an efficacy claim. The harness
measures response quality for visual cases under read-only candidate sandboxes; writable
artifact integrity remains covered by separate end-to-end and deterministic tests.

## Exchange seam

Participant sourcing is separated from study definition, interviewing, evidence ingestion,
and synthesis. `SYNTHETIC` and `BRING_YOUR_OWN` work in V1; `EXCHANGE` implements a
structured unavailable provider contract. A future backend can accept an internal study,
receive a minimized external packet, recruit/match participants, return completed sessions,
and feed `HUMAN_INTERVIEW` evidence through the existing firewall without changing the
Design Thinking engine.

## Release flow

```text
canonical core
  → build both packages
  → hash/drift check
  → platform validators
  → unit + behavioral parity tests
  → interview-app tests/build
  → deterministic ZIP artifacts
```

Use `make build-openai` or `make build-claude` while iterating on one adapter.
`make validate-openai` and `make validate-claude` run the respective platform
validators; `make check-cross-platform-drift` rebuilds both packages before the
hash comparison. `make platform-evals` maps the single shared behavioral corpus
through both invocation adapters without copying fixtures or making model calls.
Run `make release-check` for the combined deterministic gate. Generated
directories are release artifacts; edit source files, not package copies.
The combined gate requires a current Claude validator (installed `claude`, or
the official package through `npx`) and runs the interview app's full tests,
lint, typecheck, production build, and production-dependency audit. Authenticated
model evals and clean marketplace installs remain separately evidenced runtime
checks.
