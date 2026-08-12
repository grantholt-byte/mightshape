# V1 validation report

**Validation date:** 2026-08-12  
**Scope:** repository state before publication; no deployment or marketplace
submission was performed.

This report records observed checks only. A portable summary is committed at
[`evals/evidence/model-backed-summary.json`](../evals/evidence/model-backed-summary.json).
Raw model/session logs live under the locally ignored `evals/results/`
directory; rerun commands are in [`evals/README.md`](../evals/README.md).

## Deterministic product and package checks

| Check | Observed result |
|---|---|
| Python unit suite | **PASS — 74 tests** |
| Behavioral contract corpus | **PASS — 100 cases**, including 53 adversarial cases and 46 invariant families |
| Adapter mapping | **PASS — 100 shared cases per adapter**; native explicit invocation is `$design-council` on OpenAI and `/design-council:design-council` on Claude Code |
| OpenAI package | **PASS** with the official plugin validator and official skill validator |
| Claude package | **PASS** with strict Claude plugin validation for both the generated plugin and root marketplace |
| Shared-core drift | **PASS — 98 shared files**, including 10 byte-identical Council Human Models |
| Package contract | **PASS** for manifests, skill metadata, schemas, scripts, methods, templates, and optional interview companion boundaries |

Primary commands were:

```sh
python3 -m unittest discover -s tests -v
python3 evals/run_contracts.py
python3 evals/run_platform_contracts.py
make validate-openai
make validate-claude
make check-cross-platform-drift
make release-check
```

## Runtime behavior

- **OpenAI clean-context install:** explicit invocation introduced all ten
  fictional members while preserving the evidence disclaimer; implicit
  invocation refused to invent evidence for an AI career-decider; the negative
  routing case proceeded toward the specified dark-mode implementation without
  Design Council ceremony. Recorded outputs:
  `evals/results/openai-clean-explicit.md`,
  `evals/results/openai-clean-implicit.md`, and
  `evals/results/openai-clean-negative.md`.
- **Family-scheduler acceptance:** strict model-backed judging **PASS** across
  all criteria. Recorded run: `evals/results/20260812T214720Z/`.
- **Emergency-nurse Inquiry Lab acceptance:** strict model-backed judging
  **PASS** across all criteria. Recorded run:
  `evals/results/20260812T220041Z/`.
- **Council-humanity acceptance:** strict model-backed judging **PASS** across
  all criteria: ten differentiated attention patterns, sealed independent
  Round A, post-freeze anonymous extension and forced mutation, later
  convergence, preserved dissent, knowledge boundaries, and structured
  project-memory-ready output. Recorded run:
  `evals/results/20260812T222324Z/`.
- **Claude Code:** strict validation plus clean structural marketplace
  add/install/list/details/update/uninstall checks succeeded, including skill
  and sealed-member component discovery. Native model invocation was attempted
  but **blocked by an expired OAuth session**; the recorded result is
  `evals/results/claude-installed-explicit.json`. No Claude behavioral pass is
  claimed.

## Interview companion

- Full deterministic/rendered suite: **16 passed, 1 environment-gated skip**.
- A separate configured D1-backed live lifecycle run: **1 passed**.
- Concurrent stop versus model completion is linearized in one D1 batch: a stop
  that commits first prevents both late messages and the late state update.
  The route reports the discarded turn instead of presenting it as saved.
- Browser-rendered participant surfaces were inspected at
  [`consent.png`](../interview-app/tests/screenshots/consent.png) and
  [`active.png`](../interview-app/tests/screenshots/active.png).
- Lint, TypeScript checking, and production build passed.
- `npm audit --omit=dev`: **0 production vulnerabilities**.
- Full development audit: **6 upstream build/development advisories**
  (4 moderate, 2 high). They are not production runtime dependencies, but must
  be rechecked as the Sites/Vinext toolchain updates.

No Site was deployed and no public interview URL was created.

## Exchange-readiness boundary

`SYNTHETIC` and `BRING_YOUR_OWN` participant sources are functional.
`EXCHANGE` is a side-effect-free future provider returning a structured
unavailable state. V1 validates the participant-source seam, internal versus
external study packets, Disclosure Guard, exposure levels, conflict settings,
participant-profile separation, evidence provenance, consent independence, and
content-free learning signals. Recruitment, matching operations, verification,
credits/payments, reputation, legal conflict screening, NDAs, and remote
telemetry remain intentionally unimplemented.

## Release boundary

The repository was not deployed, pushed, submitted, approved, or published to
OpenAI, Anthropic, GitHub, ChatGPT Sites, or any marketplace. Publication still
requires the owner-controlled identity, license, repository, public policy URLs,
authenticated platform checks, and approval steps in the
[`publishing checklist`](PUBLISHING_CHECKLIST.md).
