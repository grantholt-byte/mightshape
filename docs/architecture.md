# Architecture: one product, two adapters

## Source of truth

Design Council has one canonical product core under `skills/design-council/`:

- `references/`: constitution, ten Human Models, Council protocols, Inquiry Lab,
  stage/method guidance, UX, evidence, and source notes;
- `schemas/`: portable records for project state, inquiry, evidence, and Exchange readiness;
- `scripts/`: deterministic facilitation, validation, state, and sealed-round helpers;
- `assets/templates/`: reusable project artifacts;
- `SKILL.md`: the shared routing constitution and OpenAI entry point.

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

`scripts/build_packages.py` creates both self-contained packages. The Claude package
copies the exact shared directories and exact canonical `SKILL.md`, then appends only
Claude-specific invocation, Agent, Sites, and hook mechanics. It does not fork Human
Models or methodology. `scripts/check_cross_platform_drift.py` hashes every shared file,
checks all signature invariants, confirms ten identical Human Models, and synchronizes
versions.

## Platform differences

| Concern | OpenAI / Codex | Claude Code |
|---|---|---|
| Manifest | `.codex-plugin/plugin.json` | `.claude-plugin/plugin.json` |
| Explicit invocation | `$design-council` | `/design-council:design-council` |
| Independent workers | Native Codex subagents; isolated `codex exec` fallback | Fresh Agent workers via `design-council:sealed-member` |
| Optional state recovery | Trust-gated SessionStart hook | Skill reads canonical state on activation |
| Hosted companion | ChatGPT Sites-compatible | Can develop the app; cannot claim a Sites deploy |

These differences affect mechanics only. Council identities, evidence provenance,
methods, memory, Minority Report, Inquiry Lab, debt, and Build Gate are byte-identical.

## Portable state

Both adapters read `.design-council/project.json` and the same revision snapshots. The
schema contains no OpenAI-, Codex-, Claude-, or Anthropic-specific fields. Platform
metadata should be optional and namespaced if a future adapter truly needs it; core
evidence, frames, experiments, and Council memories remain portable.

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
