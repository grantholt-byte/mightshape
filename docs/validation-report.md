# V1 private-beta validation report

**Validation date:** 2026-08-13

**Release candidate:** `v0.9.0-beta.5`

**Scope:** private collaborator distribution only; no public deployment or marketplace submission.

This report records observed checks without upgrading model judgments or synthetic exercises into
human evidence. Raw authenticated run artifacts remain locally ignored because they can contain
machine paths and generated study content. Redacted, portable evidence is committed under
[`evals/evidence/`](../evals/evidence/).

> **Current status:** beta.5 deterministic validation and both current platform validators
> pass. Model-backed benchmark reruns, immutable tag creation, and fresh collaborator-install
> tests remain pending. Pre-beta.5 model evidence below is retained as the current comparison
> boundary and is not silently promoted to evidence about this release candidate.

## Latest completed deterministic product and package checks

| Check | Observed result |
|---|---|
| Python unit suite | **PASS — 186 tests** |
| Behavioral contracts | **PASS — 114 cases**, including 60 adversarial cases and 51 invariant families |
| Adapter mapping | **PASS — 114 shared cases per adapter** |
| OpenAI package | **PASS** with official plugin and skill validators |
| Claude package | **PASS** with the current strict plugin validator used by `make release-check` |
| Shared-core drift | **PASS — 105 shared files**, including 10 byte-identical Council Human Models |
| Package contract | **PASS** for manifests, skill metadata, 35 schemas, 21 deterministic scripts, methods, templates, and optional-infrastructure boundaries |
| OpenAI starter prompts | **PASS — 3**, within the current runtime limit |
| Duplicate-file safety | **PASS** — clean builds preserve user-owned conflict copies locally; they remain untracked and are excluded from release archives and checksums |
| Credential scan | **PASS — no candidate secrets detected** |

Primary commands:

```sh
python3 -m unittest discover -s tests -v
python3 evals/run_contracts.py
python3 evals/run_platform_contracts.py
make validate-openai
make validate-claude
make check-cross-platform-drift
make release-check
```

## Adaptive facilitator and participation

- `OBSERVE`, `COLLABORATE`, and `FACILITATED_TURN_BY_TURN` are portable project-state
  modes presented as **Watch · Collaborate · One prompt at a time**.
- `NOVICE_ASSISTED` is the default for an opting-in user without evident fluency. At a method
  boundary it explains the immediate purpose and mindset, provides one method-safe example,
  and asks exactly one bounded prompt. Protected independent ideation receives only an
  answer-shape or distant-domain example, never a target-domain solution seed.
- Pace, explanation, skip, pause, undo-as-supersede, hand-back, exit, and resume are persisted.
  User contributions retain stable IDs and `USER_PROVIDED` provenance.
- Runtime tests enforce one-open-prompt state, prompt-linked contributions and adaptations,
  novice scaffolding before light-touch behavior, conservative compound-prompt rejection,
  and sealed-round input holding.
- A fresh model-backed novice brainstorm honored the named exercise, used a distant-domain
  example, and asked one prompt. Its semantic judge passed all eight criteria. Reapplying the
  corrected deterministic corpus to the saved response also passed; the earlier stored
  deterministic failure was caused by the now-fixed narrow regex, not the response.

The general invariant model-eval runner is a local authenticated harness and is not described as
clean-context proof: unlike the paired A/B runner, it can inherit host runtime configuration.

## Visual Workbench and visible process

- Affinity and process maps render deterministically as source JSON, self-contained HTML,
  accessible SVG, Markdown fallback, and an immutable hashed manifest.
- Visuals use sticky paper, tape, folded corners, colorful neighborhoods, actor lanes, handoffs,
  and restrained doodles while keeping provenance in text. Rendering tests cover escaping,
  no remote assets/scripts, accessible fallback, source retention, and non-overwrite behavior.
- Both shipped examples now derive solely from explicit benchmark-prompt inputs. All supplied
  notes are `USER_PROVIDED`; missing recovery behavior is `UNKNOWN`. The visible `P-*` labels
  are explicitly illustrative prompt identifiers—not verified people, interviews, or observed
  behavior. No fictional study or transcript IDs remain.
- Corrected affinity and process graphics were rendered in Chrome, inspected visually, and
  regenerated for the README/package gallery.
- `VISIBLE` and `WORKSHOP` views expose stable inputs, named transformations, output IDs,
  material changes, and the next move without exposing hidden chain-of-thought, raw logs, or
  partial sealed responses.

## Council independence and persistence

- A real four-member Round A run used fresh auth-only Codex homes and identical common packets.
  All outputs completed before freeze; the response set was hashed/read-only before anonymous
  cross-pollination. The four responses showed different reasoning, attention, and language.
- Deterministic tests cover sibling-reference rejection, frozen-set immutability, authorship
  removal, no Round-A streaming, minority preservation, project-memory supersession, and
  per-member evidence-driven changes of mind.
- Council conclusion artifacts never claim hidden chain-of-thought or human evidence.

## Plugin-versus-baseline effectiveness

### Raw-prompt baseline

The frozen pre-refinement beta3 skill-tree snapshot used for this run was compared with no skill
using identical raw prompts, model, effort, word cap, read-only permissions, and fresh auth-only
Codex homes. Arm order and blind
candidate labels were counterbalanced; all candidate generation completed before judging.
The design realized 12 cases × 2 generation pairs × 2 blind judgments (24/24 complete pairs).

| Measure | Design Council | Baseline | Difference |
|---|---:|---:|---:|
| Blind model-judge quality | 95.60 | 86.31 | **+9.29 points** |
| Mean generation tokens | 32,393 | 17,647 | **+14,746; 1.84×** |
| Mean wall time | 46.62s | 34.27s | **1.36×** |
| Mean visible words | 638 | 646 | **0.99×** |

- Quality uplift 95% case-bootstrap interval: **[6.07, 12.74]**; paired dz: **1.53**.
- Case results: **11 wins, 1 tie, 0 losses**; blind votes: **42 treatment, 6 control**.
- Primary effectiveness: **`MEANINGFUL_BENEFIT_ESTABLISHED`**. The entire quality interval
  clears the preregistered 3-point minimum-important-difference threshold; token use is not
  part of this outcome verdict.
- A post-hoc capability profile found positive group means for right-problem framing
  (**+10.71**), structured divergence/synthesis (**+9.17**), evidence discipline (**+9.68**),
  learning-oriented experiments/iteration (**+8.04**), and appropriate scope (**+10.00**).
  The strongest blind dimension gains were evidence calibration (**+20.42**), methodological
  rigor (**+14.58**), and breadth/non-obviousness (**+9.58**). These groupings must be
  preregistered in a confirmatory rerun.
- Marginal outcome yield: **0.63 blind-quality points per 1,000 additional generation tokens**
  (uplift interval divided by the fixed observed premium: **0.41–0.86**); inverse yield:
  **1,588 additional tokens per quality point**.
- Configured maximum token ratio: 1.50×. The observed 1.84× ratio is
  **`ABOVE_CONFIGURED_BUDGET`**. This is an optimization/resource descriptor, not an
  outcome-value veto or a claim about monetary cost-effectiveness.
- The routing correction removed the prior technical-spike regression: parser-spike became a
  tie (+1.43 quality) at **1.01× tokens** with no skill load. Design-heavy tasks still carry
  substantial method-loading cost.

Exact redacted raw-baseline measurements, hashes, per-case results, and limitations are in
[`ab-benchmark-beta3.json`](../evals/evidence/ab-benchmark-beta3.json).

### Competent prompt-only baseline

The same 12-case, 24-pair, 48-blind-judgment design was repeated with a more demanding control.
That arm had no plugin, state, Human Models, protocols, or modular references, but it received one
frozen competent Design Thinking instruction before the identical raw user prompt.

| Measure | Design Council | Prompt-only control | Difference |
|---|---:|---:|---:|
| Blind model-judge quality | 93.57 | 95.12 | **-1.55 points** |
| Mean generation tokens | 35,168 | 16,353 | **+18,815; 2.15×** |
| Mean wall time | 46.79s | 36.18s | **1.29×** |
| Mean visible words | 651 | 653 | **1.00×** |

- Quality-difference 95% case-bootstrap interval: **[-4.64, 1.79]**; paired dz: **-0.26**.
- Case results: **3 wins, 2 ties, 7 losses**; blind votes: **21 treatment, 27 control**.
- Primary effectiveness: **`INCONCLUSIVE`**. The interval crosses zero, so the run establishes
  neither a Design Council advantage nor a reliable prompt-only advantage.
- The plugin improved methodological rigor (**+3.33**) and appropriate scope (**+4.29** across
  that two-case construct), but trailed on breadth/non-obviousness (**-8.75**) and the structured
  divergence/synthesis construct (**-4.64**). These are diagnostic group means, not validated
  independent scales.
- The **2.15×** token ratio is **`ABOVE_CONFIGURED_BUDGET`**, but token use is secondary: it
  does not determine the outcome verdict and cannot turn an inconclusive quality result into a
  claim of benefit or harm.

The honest beta conclusion is therefore two-part: Design Council established value over raw
prompting on this internal corpus, but did **not** establish incremental single-turn value over a
competent Design Thinking prompt. The latter result identifies concrete refinement targets around
conceptual breadth, evidence calibration, and ceremony. It also makes longitudinal evaluation
essential because a single response cannot measure persistent project memory, structured
participation, or evidence-driven change across cycles.

Both comparisons are exploratory internal Codex evidence, not monetary ROI or a public efficacy
claim. The corpus and rubrics were product-authored; judges were models; terminology can weaken
content blinding; and the strong-comparator treatment was a frozen snapshot from a dirty beta3
working tree. Held-out external prompts, independent human judges, scripted multi-turn outcome
studies, and new frozen reruns after refinements remain required. The Claude headless isolation
boundary was structurally verified, but this host had no authenticated Claude runtime, so no
Claude behavioral efficacy claim is made. Exact strong-comparator evidence is in
[`ab-benchmark-strong-prompt-beta3.json`](../evals/evidence/ab-benchmark-strong-prompt-beta3.json).

### Longitudinal value harness

A new persisted-session paired harness now tests the value proposition that a one-shot comparison
cannot: remembering an earlier frame, using new constraints, changing direction when supplied
evidence contradicts the initial solution, preserving a minority interpretation, and choosing a
test with high decision value. Its default comparator has no plugin and receives the exact frozen
competent Design Thinking instruction on every turn. The eight blind dimensions include evidence
calibration/provenance as well as framing, history, assumptions, divergence, experiment information
gain, backward iteration, and momentum.

Deterministic validation passed for the three four-turn trajectories, exact prompt parity,
treatment-only skill presence, auth-only isolation, explicit UUID session resume, arm/label
counterbalancing, frozen hashes, schema enforcement, and quality-first verdict logic. A meaningful
benefit requires a complete realized design and a case-bootstrap interval clearing the configured
minimum important uplift; token/latency diagnostics remain separate.

Failure-path tests also require every planned candidate trajectory and blind judgment exactly once,
validate saved judge payloads, recompute quality from those payloads, reject forged derived scores,
and render quota/interrupted runs as `INCOMPLETE` without a completion claim.

The live 60-call exploratory run has not yet completed, so no longitudinal outcome is claimed.
The runner now records the exact Design Council version, Git commit, dirty state, frozen content
hashes, and runtime configuration. It will run from a clean source-freeze commit, followed by the
single-turn strong comparator, held-out trajectories, and blind human ratings. Until then, the
pre-refinement single-turn strong-prompt result remains the current honest incremental-value
boundary.

## Interview companion and Exchange boundary

- Interview companion deterministic/rendered suite: **16 passed, 1 environment-gated skip**.
- Lint, TypeScript checking, production build, and `npm audit --omit=dev` pass with
  **0 production vulnerabilities**.
- Full development audit continues to report 6 upstream build/development advisories
  (4 moderate, 2 high); these are not production runtime dependencies and remain a beta caveat.
- No Site was deployed and no public interview URL was created.
- `SYNTHETIC` and `BRING_YOUR_OWN` participant sources function. `EXCHANGE` remains a
  side-effect-free future provider returning a structured unavailable state. Recruitment,
  matching, verification, credits/payments, reputation, legal screening, and NDAs are deferred.

## Marketplace and distribution readiness

OpenAI and Claude packages are generated from one canonical core at
`dist/openai/design-council` and `dist/claude/design-council`; deterministic beta archives and
SHA-256 checksums live under `dist/`. Installation, update, uninstall, private-repository auth,
and current public-publication paths are documented separately.

The `v0.9.0-beta.5` tag and fresh pinned-tag collaborator installs must occur only after its
pending benchmark review. Existing beta tags remain immutable. Nothing has been
submitted, approved, or published to either marketplace. Public publication remains gated on
owner-controlled publisher identity, public policy/support URLs, independent evaluation, a fresh
release audit, and each platform's current review/catalog process.
