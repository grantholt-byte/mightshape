# V1 validation report

**Validation date:** 2026-08-13

**Release:** `1.0.0`

**Scope:** private collaborator distribution only; no public deployment or marketplace submission.

This report records observed checks without upgrading model judgments or synthetic exercises into
human evidence. Raw runtime streams remain locally ignored. Content-safe audit bundles preserve
the frozen manifest, assistant outputs, blinded pairs, structured judgments, summaries, and hashes
under [`evals/evidence/`](../evals/evidence/), without environment variables or credentials.

> **Current status:** the unchanged preregistered V1 trajectory gate passed from clean beta.8
> source commit `afddbf4ee4b2c7555f8e390d92edd843427ea31c` as run `20260814T002300Z`.
> All 100 planned calls completed; Design Council scored 97.50 versus 88.125, a +9.375-point
> advantage (95% case-bootstrap CI [4.625, 14.625]; 4 wins, 1 tie, 0 losses). The raw verifier
> passed 45/45 checks and the content-safe exported bundle passed 44/44. This satisfies the fixed
> V1 efficacy gate. Earlier beta evidence remains historical and is not silently promoted.

## Latest completed deterministic product and package checks

| Check | Observed result |
|---|---|
| Python unit suite | **PASS — 274 tests** |
| Behavioral contracts | **PASS — 132 cases**, including 74 adversarial cases and 52 invariant families |
| Adapter mapping | **PASS — 132 shared cases per adapter** |
| OpenAI package | **PASS** with bundled plugin/skill authoring validators and local portal-rule checks; portal upload validation remains manual |
| Claude package | **PASS** with the current strict plugin validator used by `make release-check` |
| Shared-core drift | **PASS — 106 shared files**, including 10 byte-identical Council Human Models |
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

### Focused all-ten recognition run

A clean beta.6 run generated ten isolated, name-screened Council artifacts from the same neutral
challenge and froze the complete set before one blind evaluator received anonymous behavioral
reference cards. All **11/11 model calls** completed, the leakage screen found **0/10** violations,
and the evaluator made **10/10 correct source-profile assignments** under a forced one-to-one
mapping. The descriptive random-permutation expectation is 10% accuracy; the exact probability of
all ten matches under that reference process is `2.76e-7`.

This is evidence that the artifacts were traceable to the ten canonical fictional profiles on one
neutral challenge. It is **not** human recognition evidence, a human-study p-value, cross-context
identity consistency, or human ground truth. Candidates used `gpt-5.6-sol` at medium effort and
the evaluator used `gpt-5.6-terra` at medium effort on clean commit `f88cb2e`; the run consumed
**182,930 total tokens** and took **92.32 seconds** end to end. The reproducible harness and its
narrow claim boundary are documented in [`evals/README.md`](../evals/README.md); the frozen
prompts, screened artifacts, source assignments, judgment, call metadata, and manifest are in the
[`20260813T212210Z evidence bundle`](../evals/evidence/council-recognition/20260813T212210Z/summary.md),
with a complete `SHA256SUMS` ledger for the retained files.

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

### Post-refinement beta.6 one-shot comparator

The same complete 12-case design was rerun from clean commit `f88cb2e` after the efficacy,
facilitation, routing, and proportionality refinements. Design Council scored **95.54** versus
**92.98** for the frozen competent prompt-only control: **+2.56 points**, with 95% case-bootstrap
CI **[0.42, 4.82]**, 7 wins, 2 ties, and 3 losses. Blind votes were 37 treatment to 11 control.

Generation-token use fell from the beta3 2.15× ratio to **1.523×** control: 23,406 versus 15,371
mean tokens per case run. Visible length was slightly lower than control (648 versus 654 words),
so the premium came from loaded context, reasoning, and a small number of tool-backed artifacts,
not longer prose. The configured 1.50× optimization target was narrowly missed; that remains a
resource diagnostic rather than an outcome veto.

The honest verdict is
`DIRECTIONAL_BENEFIT_NOT_YET_ESTABLISHED_AS_MEANINGFUL`: the point estimate is positive, but the
interval does not clear the preregistered +3-point practical threshold. The run therefore does
not establish meaningful one-shot benefit, but it also does not establish a meaningful control
advantage—the secondary V1 gate condition is satisfied. Diagnostic gains were strongest in
methodological rigor (+10.00), evidence calibration (+3.75), and appropriate scope (+8.57);
actionability (-2.08) and structured divergence/synthesis (-0.24) remain refinement targets.
More than 20% of multiply judged pairs changed winner across counterbalanced presentations, so
small per-case differences must not be overinterpreted.

The complete content-safe evidence bundle—including frozen manifests, assistant outputs, blinded
pairs, judgments, summaries, and hashes—is stored at
[`evals/evidence/runs/20260813T210644Z`](../evals/evidence/runs/20260813T210644Z).

### Longitudinal value harness

A new persisted-session paired harness now tests the value proposition that a one-shot comparison
cannot: remembering an earlier frame, using new constraints, changing direction when supplied
evidence contradicts the initial solution, preserving a minority interpretation, and choosing a
test with high decision value. Its default comparator has no plugin and receives the exact frozen
competent Design Thinking instruction on every turn. The eight blind dimensions include evidence
calibration/provenance as well as framing, history, assumptions, divergence, experiment information
gain, backward iteration, and momentum.

Deterministic validation passed for the five neutral comparative trajectories plus two separate
product-conformance trajectories, exact prompt parity,
treatment-only skill presence, auth-only isolation, explicit UUID session resume, arm/label
counterbalancing, frozen hashes, schema enforcement, and quality-first verdict logic. A meaningful
benefit requires a complete realized design and a case-bootstrap interval clearing the configured
minimum important uplift; token/latency diagnostics remain separate.

Failure-path tests also require every planned candidate trajectory and blind judgment exactly once,
validate saved judge payloads, recompute quality from those payloads, reject forged derived scores,
and render quota/interrupted runs as `INCOMPLETE` without a completion claim.

The clean 60-call beta.5 exploratory run completed every planned candidate turn and blind
judgment at commit `7bba36d`: Design Council scored **98.33** versus **94.17**, a **+4.17-point**
directional advantage with 95% case-bootstrap CI **[0.625, 6.875]** and 2 wins, 1 tie, 0 losses.
Generation-token use was **1.643×** control. The interval lower bound did not clear the
preregistered +3-point minimum, so the honest verdict is
`TREATMENT_ADVANTAGE_DETECTED_BELOW_IMPORTANCE_THRESHOLD`, not V1 efficacy success. Full
assistant trajectories, blinded pairs, judgments, summaries, hashes, and frozen-commit metadata
are committed under
[`evals/evidence/runs/20260813T191419Z`](../evals/evidence/runs/20260813T191419Z).

The first fully preregistered five-trajectory attempt then ran from exact clean beta.6 commit
`f88cb2e`. All **20/20 candidate arms** and **20/20 blind judgments** completed without failures,
retries, skips, or timeouts. Design Council scored **96.875** versus **91.375**, a **+5.5-point**
advantage with 4 wins, 0 ties, and 1 loss. Candidate tokens were **2,559,903** versus **1,605,139**
(**1.594817×**); visible treatment output was only modestly longer, so input/context dominated the
premium. The 10,000-sample case-bootstrap interval was **[0.25, 11.625]**. Because its lower bound
did not clear +3, the verdict remained
`TREATMENT_ADVANTAGE_DETECTED_BELOW_IMPORTANCE_THRESHOLD`; the shipped content-safe bundle
reproduces an independent verifier failure of **42/44** when exported-bundle mode is explicitly
allowed (the two failed checks are the verdict and interval threshold). Default raw-run mode also
fails the expected missing-snapshot check. No V1 receipt was created. The complete immutable evidence is in
[`evals/evidence/runs/20260813T210617Z`](../evals/evidence/runs/20260813T210617Z).

Four trajectories won; the clinic handoff case lost **−3.125**. Forensics showed a precise,
generalizable defect rather than failure to reframe: one repeat converted duplicated-task events
into unsupported walkthrough ratios, carried obsolete scope after hard constraints, and omitted
legitimate parallel work and false-blocking counterexamples. Beta.7 now preserves observational
units/cardinality, explicitly supersedes incompatible scope, distinguishes accountable ownership
from contribution, tracks evidence-driven frame changes, and keeps generic authority separate from
local causal evidence. In a local authenticated regression run, five focused live model responses
passed independent semantic judgment and their saved responses passed corrected deterministic
matchers. Those gitignored artifacts are a development diagnostic, not shipped release evidence.
The unchanged primary gate then reran from a new clean beta.7 commit as described below.

### Preregistered beta.7 trajectory gate

The unchanged five-trajectory gate ran from clean beta.7 commit `893867f7d` as
`20260813T225549Z`. All **100/100 planned calls** completed: 80 persisted candidate-turn calls and
20 blind judgments, with no failures, retries, skips, timeouts, or malformed records. Design
Council scored **97.0** versus **93.125** for the competent Design Thinking prompt control, a
**+3.875-point** difference with **4 wins, 0 ties, and 1 loss**. The 10,000-sample case-bootstrap
interval was **[0.25, 6.75]**. Candidate-token use was **1.546573×** control and wall time was
**1.306717×** control; both remain resource diagnostics rather than outcome gates.

The raw-run verifier reproduced **43/45 checks**. The two failures were exactly the required
meaningful-benefit verdict and the interval threshold: although the point estimate exceeded +3,
the interval's lower bound did not. The recorded verdict is
`TREATMENT_ADVANTAGE_DETECTED_BELOW_IMPORTANCE_THRESHOLD`. This fails the fixed V1
minimum-important-uplift gate, so it cannot support a V1 promotion. The complete content-safe,
checksummed evidence is in
[`evals/evidence/runs/20260813T225549Z`](../evals/evidence/runs/20260813T225549Z).
Running that deliberately content-safe export with `--allow-exported-bundle` reproduces **42/44**;
its same two failures are the verdict and interval threshold, while the raw-only snapshot check is
not part of exported-bundle mode.

The beta.7 clinic fix generalized in the primary rerun: clinic handoff changed from the previous
**−3.125** loss to a **+5.0** win. The remaining loss was the live-product trajectory at
**−3.125**. Forensics found that the treatment translated the desired outcome too directly into
making the product the coordination destination. It did not preserve the decision boundary among
becoming that destination, bridging into an accepted existing venue, and retaining incumbent or
private workflows; it also spent the one-event budget on a role declaration rather than downstream
reciprocal behavior.

The bounded beta.8 correction makes outcome and intervention locus separate decisions,
requires the destination/bridge/incumbent-or-private fork to survive until a discriminating test,
and allocates scarce instrumentation to consequential downstream behavior rather than clicks or
self-declared roles. One targeted local model regression for this new invariant passed semantic
judgment, and its saved response passed the corrected deterministic matcher. That gitignored run
remains a development diagnostic only and is not release evidence. The unchanged release gate was
then rerun from the frozen beta.8 source as documented below.

### Passing V1 trajectory gate

The unchanged five-trajectory gate ran from clean beta.8 source commit
`afddbf4ee4b2c7555f8e390d92edd843427ea31c` as `20260814T002300Z`. All **100/100 planned
calls** completed. Design Council scored **97.50** versus **88.125** for the competent Design
Thinking prompt control, a **+9.375-point** advantage with **4 wins, 1 tie, and 0 losses**. The
10,000-sample case-bootstrap interval was **[4.625, 14.625]**, entirely above the fixed +3-point
minimum-important-uplift threshold. Candidate-token use was **1.320392×** control and wall time
was **1.244173×** control; these remain resource diagnostics rather than outcome gates.

The fail-closed raw-run verifier passed **45/45 checks**. The immutable content-safe export passed
**44/44 checks** in exported-bundle mode. The run therefore satisfies the preregistered V1
efficacy gate without changing its comparator, corpus, policy, verifier, or threshold. The complete
checksummed evidence is in
[`evals/evidence/runs/20260814T002300Z`](../evals/evidence/runs/20260814T002300Z).
This internal Codex result supports the bounded claim tested by that corpus; held-out trajectories,
native Claude testing, and blind human ratings remain required before a broad public efficacy claim.

## Interview companion and Exchange boundary

- Interview companion deterministic/rendered suite: **16 passed, 1 environment-gated skip**.
- Lint, TypeScript checking, production build, and `npm audit --omit=dev` pass with
  **0 production vulnerabilities**.
- Full development audit continues to report 6 upstream build/development advisories
  (4 moderate, 2 high); these are not production runtime dependencies and remain a release caveat.
- No Site was deployed and no public interview URL was created.
- `SYNTHETIC` and `BRING_YOUR_OWN` participant sources function. `EXCHANGE` remains a
  side-effect-free future provider returning a structured unavailable state. Recruitment,
  matching, verification, credits/payments, reputation, legal screening, and NDAs are deferred.

## Marketplace and distribution readiness

OpenAI and Claude packages are generated from one canonical core at
`dist/openai/design-council` and `dist/claude/design-council`; deterministic release archives and
SHA-256 checksums live under `dist/`. Installation, update, uninstall, private-repository auth,
and current public-publication paths are documented separately.

The product is now version `1.0.0`, and the fixed V1 efficacy gate has passed. The immutable
`v1.0.0` tag and fresh pinned-tag collaborator installs are required operational checks: use the
pinned commands only when the documented tag preflight succeeds. Existing beta tags remain
immutable. Nothing has
been submitted, approved, or published to either marketplace. Public publication remains gated on
owner-controlled publisher identity, a fresh release audit, and each platform's current
review/catalog process. Public policy/support URLs are recommended trust assets for skills-only
Core and become deployment requirements before a hosted interview service is promoted. Broader
outcome claims—not publication of the bounded, accurately described Core—remain gated on held-out
trajectories, native Claude evidence, and independent human review.
