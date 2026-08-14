# Design Council behavioral evals

This suite treats V1's product invariants as executable contracts. The JSONL
corpus is intentionally adversarial: passing only happy-path prompts is not
sufficient.

Exchange-readiness cases verify disclosure minimization, Disclosure Guard,
internal/external packet separation, provider independence, graceful Exchange
unavailability, conflict-policy retention, consent independence, content-free
learning signals, provenance, and bounded IP-exposure guidance.

## Deterministic contract run

From the repository root:

```sh
python3 -m unittest discover -s tests -v
python3 evals/run_contracts.py
python3 evals/run_platform_contracts.py
```

These commands are standard-library-only. If `jsonschema` is installed, the
runner additionally performs full Draft 2020-12 schema validation; otherwise it
uses an explicit structural validator and reports that mode.

## Optional model-backed run

Model calls are opt-in so normal CI never needs network or Codex credentials:

```sh
DC_RUN_MODEL_EVALS=1 python3 evals/run_model_evals.py --family routing --limit 3
DC_RUN_MODEL_EVALS=1 python3 evals/run_model_evals.py --case acceptance.family_scheduler --judge
```

The runner creates a fresh temporary project for every case, exposes the local
skill through `.agents/skills/design-council`, invokes `codex exec --ephemeral`,
and writes results beneath `evals/results/`. Response-only cases use a read-only
sandbox. Declared mutation cases use a disposable workspace-write sandbox and
must leave a deterministically valid versioned state, visual artifact, or
prepared/frozen Council set as applicable; narration alone does not pass.
`--judge` adds a separate structured-output evaluation pass using
`schema/model-result.schema.json` and explicitly evaluates `state_effect` using
the deterministic workspace observation. Without the opt-in
environment variable, or when the Codex CLI is unavailable, it exits cleanly
with a visible `SKIP`; use `--require-model` when skipping should fail CI.

Use `--dry-run` to inspect selected prompts without a model call. Use
`--responses-dir PATH` to apply deterministic regex checks to previously saved
`<case-id>.md` responses without network access. Saved-response mode reports
mutation cases as `SKIP` because it has no workspace to inspect; it never treats
response text as proof that required state or artifacts exist.

## All-ten name-blind Council recognition

`run_council_recognition.py` is a focused Humanity Eval for a narrower question:
can a blinded model match independently generated Council artifacts back to the
canonical behavioral profiles that produced them? It does **not** establish that
human readers recognize the fictional people, and source-profile labels are not
human ground truth.

The harness gives all ten generators the same neutral challenge in fresh,
read-only, ephemeral Codex cells. Each receives exactly one canonical profile
with relationship/project-memory contamination removed and sees no sibling
output. A deterministic screen rejects candidate artifacts containing Council
names, explicit roles, ages, places, first-person biography, known signature
questions, or copied profile/sample phrases. Only after all ten artifacts pass
does the harness freeze and hash the anonymous set.

The blind evaluator sees those frozen artifacts plus randomized anonymous
behavioral reference cards projected from the canonical profiles. The cards
omit names, roles, signature samples, and obvious biography. It must complete a
one-to-one assignment. The controller reveals neither artifact-to-source nor
profile-card-to-name mappings until after judging, then reports source-profile
accuracy and a 10% random-permutation baseline with an exact fixed-point tail
reference. That tail is descriptive, not a human-study p-value.

Inspect the plan and hashes without model calls:

```sh
python3 evals/run_council_recognition.py --dry-run
```

Run one complete panel (ten sealed generators plus one blind evaluator):

```sh
DC_RUN_COUNCIL_RECOGNITION=1 python3 evals/run_council_recognition.py \
  --require-model \
  --model gpt-5.6-sol \
  --effort medium \
  --judge-model gpt-5.6-terra \
  --judge-effort medium \
  --seed 20260813
```

Use `--repeats 2` or more for independent complete panels; each repeat adds 11
model calls. Incomplete or leakage-contaminated panels suppress accuracy and
confusion claims. Results are stored under
`evals/results/council-recognition/<timestamp>/`, including exact prompts,
models, efforts, source/profile/projection hashes, frozen-set hashes, call
metadata, judgments, manifest, accuracy, and the confusion matrix. Run this
from a clean commit for release evidence; the manifest records commit and dirty
status. Normal CI remains offline.

The clean beta.6 run `20260813T212210Z` completed all 11 calls with zero leakage findings and
10/10 correct source-profile assignments under the forced one-to-one mapping. That is narrow
model-based traceability on one neutral challenge, not human recognition or cross-context proof.
It used 182,930 total candidate-plus-evaluator tokens and ran against clean commit `f88cb2e`.
The frozen content-safe run is in
[`evidence/council-recognition/20260813T212210Z`](evidence/council-recognition/20260813T212210Z/summary.md).

## Paired plugin-versus-baseline benchmark

`run_ab_benchmark.py` measures whether Design Council produces a practically meaningful
outcome-quality improvement under either deliberate invocation or implicit availability. Token and latency
use are reported separately as resource descriptors; they do not veto a demonstrated
quality benefit. This is distinct from the invariant corpus above: it estimates
comparative effectiveness instead of asking only whether a Design Council response
satisfies its own contract.

The primary comparison is paired and controlled:

- both arms receive the identical raw user request, neutral wrapper, model,
  reasoning effort, word cap, sandbox, and fresh workspace;
- the treatment workspace contains the repository-local Design Council skill; in explicit mode its
  raw request is preceded only by the native skill invocation;
  the control workspace contains no skill;
- candidate working directories use opaque random cell names that do not reveal
  treatment/control allocation; the skill's presence is the only arm-specific
  workspace difference;
- generation order is randomized and counterbalanced;
- A/B candidate labels are blind and counterbalanced for the judge;
- task rubrics never enter either candidate prompt;
- `codex exec --ephemeral --json --ignore-user-config --ignore-rules` supplies
  structured input, cached-input, output, and reasoning token usage; wall time is
  measured around each process and visible response words are counted;
- bootstrap intervals resample whole cases, while repeated model generations are
averaged within case to avoid pseudo-replication.

A directional quality conclusion is allowed only when the *realized* run is
complete: at least 12 selected cases, every requested generation repeat for
every case, successful treatment and control generations for every planned
pair, and every requested valid counterbalanced judgment for every pair. A
partially successful run can still be inspected, but it remains
`INCONCLUSIVE` even when its partial-sample confidence interval excludes zero.
Aggregation independently binds every generation and judgment to the frozen
plan, validates the normalized usage and payload contracts, and recomputes
quality totals and winner mappings from the structured judge payload. Missing,
duplicate, unexpected, mismatched, or forged cached records therefore fail the
release-quality completeness flag without preventing partial diagnostics. The
report shows treatment, control, and absolute treatment-minus-control values
for total/input/cached/output/reasoning tokens, response words, and observable
tool activity.

The judge is blind to arm allocation, not guaranteed blind to product identity:
a treatment response may name Design Council or use recognizable terminology.
The judge is instructed not to reward those cues. For a publication-quality
claim, add held-out prompts not written by the product team and independent
human raters who do not know which response came from which condition.

The shared response word cap is outcome-neutral: it prevents output length from
becoming the intervention while allowing either arm to use the available space.
The communication-efficiency rubric also penalizes unnecessary ceremony rather
than rewarding verbosity.

Inspect the study without spending model calls:

```sh
python3 evals/run_ab_benchmark.py --dry-run
```

Run an inexpensive smoke comparison:

```sh
python3 evals/run_ab_benchmark.py \
  --case family_scheduler \
  --case dark_mode \
  --run-model
```

Run the recommended exploratory study with two generation pairs per case and
two counterbalanced blind judgments per pair:

```sh
DC_RUN_AB_BENCHMARK=1 python3 evals/run_ab_benchmark.py \
  --repeats 2 \
  --judge-repetitions 2 \
  --minimum-important-uplift 3 \
  --max-token-ratio 1.5 \
  --seed 20260813
```

Run the more demanding prompt-engineering comparison with the same corpus:

```sh
DC_RUN_AB_BENCHMARK=1 python3 evals/run_ab_benchmark.py \
  --repeats 2 \
  --judge-repetitions 2 \
  --control-mode design-thinking-prompt \
  --treatment-invocation explicit \
  --judge-model gpt-5.6-terra \
  --seed 20260813
```

That comparator has no plugin, state, Human Models, protocols, or modular references. It receives
one frozen, competent Design Thinking instruction in addition to the same raw prompt. This tests
whether Design Council adds value beyond a one-shot prompt, not only beyond an unassisted session.

The completed pre-tag beta3 candidate-snapshot run (`20260813T160656Z`) did **not** establish that incremental
single-turn benefit: Design Council scored **93.57** versus **95.12** for the prompt-only control
(difference **-1.55**, 95% case-bootstrap CI **[-4.64, 1.79]**; 3 wins, 2 ties, 7 losses).
Generation-token use was **2.15×** control. The quality verdict is `INCONCLUSIVE`; token use is
reported separately and is not the reason for that verdict. This result must be read alongside,
not blended with, the separate raw-prompt comparison, where Design Council established a
meaningful benefit. Redacted evidence is committed in
[`ab-benchmark-strong-prompt-beta3.json`](evidence/ab-benchmark-strong-prompt-beta3.json) and
[`ab-benchmark-beta3.json`](evidence/ab-benchmark-beta3.json).

The clean post-refinement beta.6 rerun (`20260813T210644Z`) completed all 24 generation pairs and
48 blind judgments. Design Council scored **95.54** versus **92.98**: **+2.56 points**, 95%
case-bootstrap CI **[0.42, 4.82]**, with 7 wins, 2 ties, and 3 losses. Generation-token use was
**1.523×** control, down from 2.15× in the beta3 strong-comparator run. The correct verdict is
`DIRECTIONAL_BENEFIT_NOT_YET_ESTABLISHED_AS_MEANINGFUL`, because the interval does not clear the
preregistered +3-point practical threshold. Complete content-safe artifacts and hashes are in
[`evidence/runs/20260813T210644Z`](evidence/runs/20260813T210644Z).

The strong-prompt result makes the next validation step explicit: use held-out prompts and blind
human raters, and measure scripted multi-turn trajectories where persistent framing, evidence
integration, structured divergence, experiment information gain, and backward iteration can
actually occur. Do not generalize either Codex result to Claude.

This default 12-case, two-repeat design makes 96 model calls: 48 candidate
generations plus 48 blind judgments. Use a different judge model through
`--judge-model` when available to reduce same-model self-preference. The runner
warns when the sample is small, the paired 95% bootstrap interval crosses zero,
candidate and judge models are the same, a pair fails, or counterbalanced judge
orientations are unstable. A confidence interval that crosses zero is reported
as `INCONCLUSIVE`, not as a win.

### Outcome effectiveness versus resource use

The runner deliberately reports two separate assessments:

- `primary_effectiveness_assessment`: whether a complete paired study establishes a
  practically meaningful outcome benefit over the selected no-plugin control;
- `resource_efficiency_assessment`: whether generation-token use falls within the
  configured optimization budget.

The defaults preregister a minimum important uplift of **3 points on the 0–100
blind-quality scale** and a maximum treatment/control generation-token ratio of
**1.5×**. Three points is approximately one score-level improvement on one of
the seven equally weighted dimensions; 1.5× marks a selected optimization target.
These are product decision settings, not scientific constants. The primary
effectiveness verdict depends only on quality direction and the minimum-important
uplift. Exceeding a token target is reported as `ABOVE_CONFIGURED_BUDGET`; it never
turns an established outcome benefit into “no value.” `--max-token-overhead` can
add an absolute per-case-run resource target.

`quality points per 1k tokens` remains a descriptive diagnostic only. It is not
price-adjusted, has no shared causal utility scale, and is never used to decide
outcome effectiveness.

The report also exposes an incremental value profile so the product question is
visible rather than buried in separate quality and cost tables:

- outcome gain: blind-quality uplift, interval, case wins, and net wins;
- resource premium: additional generation tokens and wall time;
- marginal quality yield: blind-quality points gained per 1,000 additional
  generation tokens;
- inverse yield: additional tokens spent per blind-quality point gained;
- a per-case quality/cost quadrant and marginal yield.

These retain their measured units. They are not monetary ROI: the harness does
not invent a dollar value for a rubric point or assume account-specific cached
and uncached token prices. Use the effectiveness assessment to decide whether the
product adds outcome value. Use the resource profile and per-case marginal yield
to improve routing—especially to find tasks where the skill adds cost without
adding outcome value.

The report also aggregates the blind judge's seven dimensions and a frozen set of
overlapping user-value constructs: right-problem framing, structured divergence and
synthesis, evidence discipline, learning-oriented experiments/iteration, and appropriate
scope. Construct mappings are diagnostic rather than psychometric subscales. The mapping
in a completed beta3 raw-baseline run was added post-hoc and is labeled accordingly;
future confirmatory runs freeze its hash before generation.

`--treatment-invocation explicit` makes deliberate use the primary paired treatment. Optional
`--explicit-diagnostic` adds an explicitly invoked Design Council arm when the primary treatment
is implicit so routing failure can be diagnosed. The diagnostic is intentionally excluded from
the primary paired uplift, which measures implicit skill availability against no skill with
identical prompts.

### Persisted multi-turn trajectory benchmark

`run_trajectory_benchmark.py` measures the plugin's intended longitudinal value rather than
inferring it from one response. Each arm receives the same four raw user turns: a solution-first
request, a practical constraint, contradictory supplied evidence, and a request to revise the
frame and next test. By default the no-skill arm also receives the same frozen competent Design
Thinking instruction on every turn, making the comparison deliberately demanding. With
`--treatment-invocation explicit-first-turn`, the treatment receives `$design-think` only on turn
one and then continues through the persisted session; this is the primary deliberate-use estimand.
Implicit skill availability remains a separate routing diagnostic.

The judge scores frame adaptation, history preservation, assumption updates, conceptual
divergence, evidence calibration/provenance, experiment information gain, backward iteration,
and momentum/task fit. Candidate sessions persist and resume by explicit verified thread ID;
all trajectories finish before blind counterbalanced judging begins. Outcome effectiveness is
primary. Token and latency use remain separate resource diagnostics and cannot veto a quality
benefit. A benefit claim requires the complete realized design and a case-bootstrap interval that
clears the configured minimum important uplift.

Inspect the frozen plan without model calls:

```sh
make trajectory-benchmark-dry-run
```

Run the exploratory persisted-session comparison:

```sh
python3 evals/run_trajectory_benchmark.py \
  --run-model \
  --require-model \
  --session-mode persisted \
  --control-mode design-thinking-prompt \
  --treatment-invocation explicit-first-turn \
  --repeats 2 \
  --judge-repetitions 2 \
  --model gpt-5.6-sol \
  --effort medium \
  --judge-model gpt-5.6-terra \
  --judge-effort medium \
  --bootstrap-samples 10000 \
  --timeout 900
```

The primary efficacy corpus contains exactly five neutral intended-use trajectories. At two
repeats and two judge repetitions, the frozen V1 design makes 80 candidate-turn calls and 20
blind judgments (100 calls total). Council independence/change-of-mind and Inquiry Lab
synthetic-to-human Reality Check journeys remain in
[`product-conformance-trajectories.jsonl`](benchmark/product-conformance-trajectories.jsonl),
where they test proprietary product behavior without making the comparative corpus favor the
plugin's named mechanisms.

The clean, three-trajectory implicit-routing beta.5 run (`20260813T191419Z`) completed every
planned turn and judgment: **98.33** treatment versus **94.17** competent-prompt control,
**+4.17 points**, 95% case-bootstrap CI **[0.625, 6.875]**, with 2 wins, 1 tie, and 0 losses.
Generation-token ratio was **1.643×**. Its verdict is
`TREATMENT_ADVANTAGE_DETECTED_BELOW_IMPORTANCE_THRESHOLD`: the direction was positive, but the
lower interval bound did not clear the preregistered +3-point V1 threshold. Complete assistant
trajectories, blinded pairs, judgments, summaries, hashes, and frozen-commit metadata are retained
in [`evidence/runs/20260813T191419Z`](evidence/runs/20260813T191419Z); raw process streams and
credentials are excluded.

The first fully preregistered five-trajectory, explicitly invoked attempt ran from clean beta.6
commit `f88cb2e` as `20260813T210617Z`. All 20 candidate arms and 20 blind judgments completed
without retry, skip, timeout, or malformed output. Design Council scored **96.875** versus
**91.375**, a **+5.5-point** advantage with 4 wins, 0 ties, and 1 loss. The 10,000-sample
case-bootstrap interval was **[0.25, 11.625]** and the candidate-token ratio was **1.594817×**.
The shipped content-safe bundle reproduces an independent verifier result of **42/44** when
exported-bundle mode is explicitly allowed. The two failed checks are the interval threshold and
the required meaningful-benefit verdict; default raw-run mode additionally reports the expected
missing raw intervention snapshot. The release gate therefore correctly failed because the
interval's lower bound did not clear +3 and the verdict remained
`TREATMENT_ADVANTAGE_DETECTED_BELOW_IMPORTANCE_THRESHOLD`. Its content-safe artifacts are in
[`evidence/runs/20260813T210617Z`](evidence/runs/20260813T210617Z); no passing
`v1-trajectory-gate.json` exists.

The unchanged preregistered gate then reran from clean beta.7 commit `893867f7d` as
`20260813T225549Z`. All **100/100 planned calls** completed: 80 persisted candidate-turn calls and
20 blind judgments, with no failures, retries, skips, timeouts, or malformed records. Design
Council scored **97.0** versus **93.125** for the competent prompt control, a **+3.875-point**
difference with **4 wins, 0 ties, and 1 loss**. The 10,000-sample case-bootstrap interval was
**[0.25, 6.75]**. Candidate-token use was **1.546573×** control and wall time was **1.306717×**
control; neither resource measure changes the outcome verdict.

The raw-run verifier reproduced **43/45 checks**. Its two failures were the required
meaningful-benefit verdict and the interval threshold. Because the interval's lower bound did not
clear the fixed +3 minimum-important uplift, the result remains
`TREATMENT_ADVANTAGE_DETECTED_BELOW_IMPORTANCE_THRESHOLD` and the V1 release gate failed. The
content-safe artifacts and checksums are in
[`evidence/runs/20260813T225549Z`](evidence/runs/20260813T225549Z). This positive but insufficient
result must not be described as a passing efficacy receipt. The committed content-safe export
reproduces **42/44** with `--allow-exported-bundle`; it has the same two decision failures and omits
the raw-only intervention-snapshot check by design.

The beta.7 clinic correction held in that primary rerun: clinic handoff improved from the previous
**−3.125** loss to a **+5.0** win. The remaining loss was the live-product trajectory at
**−3.125**. Diagnosis isolated an outcome-versus-intervention-locus defect: the treatment converged
on making the product the coordination destination instead of preserving a discriminating fork
among destination, bridge to an existing venue, and incumbent or private workflows. It also used
the one available event for a role declaration instead of reciprocal downstream behavior.

A bounded beta.8 candidate correction now requires that strategic fork and its explicit decision
boundary, rejects experiments whose plausible results cannot distinguish the competing loci, and
spends scarce instrumentation on consequential downstream behavior rather than clicks or
self-declared roles. One targeted local model regression passed semantic judgment, and its saved
response passed the corrected deterministic matcher. This gitignored diagnostic is **unshipped**, was
not run from a frozen beta.8 release candidate, and is **not release evidence**. It does not replace
another unchanged preregistered gate run.

Verify a newly completed raw run against the committed fail-closed V1 policy, then export it:

```sh
make verify-v1-trajectory-gate RUN_DIR=evals/results/trajectory/<run-id>
python3 scripts/export_benchmark_evidence.py \
  --require-v1-gate evals/results/trajectory/<run-id>
```

The verifier reconstructs the exact neutral corpus/hash, pair and judge plans, all four turns,
prompt delivery, persisted sessions, usage, blinded transcripts, aggregation, and source freeze.
It rejects dirty/null commits, replay runs, reduced repetitions or bootstrap counts, wrong models,
missing usage, incomplete records, forged summaries, and a non-meaningful verdict. Its policy is
[`v1-trajectory-gate-policy.json`](benchmark/v1-trajectory-gate-policy.json). The exporter is
immutable and writes checksummed artifacts beneath `evals/evidence/runs/<run-id>`; with
`--require-v1-gate` it includes the signed-by-hash gate report.

The beta.6 attempt isolated one stochastic clinic regression rather than a framing failure: an
event count became an unsupported case ratio, hard constraints did not fully retire earlier pilot
scope, and legitimate shared work and false blocking were under-tested. Beta.7 adds general
invariants and adversarial cases for those behaviors, scopes authoritative research to decision-
changing boundaries, and records only privacy-safe completed runtime item-type counts so future
context spikes are diagnosable. The clean beta.7 rerun above confirmed the clinic correction but
failed the fixed V1 gate after exposing the live-product outcome-locus defect. Beta.8 addresses only
that bounded defect; the comparison policy, corpus, threshold, and verifier remain unchanged.
Held-out trajectories and independent human review remain necessary before making a public efficacy
claim.

Use [`human-rating-guide.md`](benchmark/human-rating-guide.md) and
[`human-paired-rating.schema.json`](schema/human-paired-rating.schema.json) for blind human review.
The human protocol locks quality ratings before revealing resource use and can compare raw/plain,
frozen-prompt, and plugin conditions.

### Claude comparison status

The committed result is a native Codex comparison and must not be generalized to Claude Code.
The same within-platform design is feasible through Claude's documented headless mode: both arms
retain identical vendor-bundled skills and tools, while the treatment alone adds a frozen package
through `--plugin-dir`. Use a fresh empty working directory and `CLAUDE_CONFIG_DIR`,
`--setting-sources local`, `--no-session-persistence`, a pinned model, and
`--output-format stream-json --verbose`; verify from the init event that the only treatment delta
is Design Council and that there are no plugin errors. Compare Claude arms only—raw token counts
and client-estimated cost are not directly comparable across vendors.

This host structurally verified that boundary with Claude Code 2.1.231, but no native Claude model
study was run because the CLI had no authenticated account, API key, or setup token. Follow the
official [headless](https://code.claude.com/docs/en/headless),
[CLI](https://code.claude.com/docs/en/cli-usage), and
[authentication](https://code.claude.com/docs/en/team) documentation before adding that result.

Each run writes beneath ignored `evals/results/ab/<timestamp>/`:

- `manifest.json`: immutable settings, case/order plans, prompt hashes;
- `generations.jsonl`: arm status, measured usage, timing, and artifact paths;
- `judgments.jsonl`: blind label maps and structured judge results;
- `blinded-pairs.jsonl`: review packet without treatment labels;
- `summary.json`: machine-readable paired statistics and warnings;
- `summary.md`: human-readable quality/cost report;
- `responses/`, `events/`, and `logs/`: auditable raw artifacts.

The manifest and summary also pin the canonical skill-tree hash (excluding
cache files and intentionally ignored `* 2.*` duplicates), runner hash, judge
schema hash, Design Council version, Git commit and dirty state, Codex CLI
version, Python runtime, and host platform. This lets later runs distinguish a
model change from a skill, runner, schema, or environment change.

Judge cost is reported separately and never charged to either product arm.
`quality points per 1k tokens` is explicitly heuristic: it is not a monetary
cost estimate and does not account for different cached-input pricing.

The candidate wrapper deliberately forbids file writes so both arms have equal,
read-only permissions. Therefore the benchmark's `affinity_cluster` and
`process_map` cases assess response quality, visual organization within the
response, and the quality of an offered artifact plan—not whether HTML/SVG files
were actually emitted. Artifact rendering, escaping, provenance, accessibility,
and browser-independent fallbacks are tested separately end to end in
`tests/test_visual_workbench.py`.

### Isolation boundary

Each invocation gets a fresh temporary `CODEX_HOME`. The runner copies only
`auth.json`, with mode `0600`, from the invoking user's Codex home so the fresh
process can authenticate. It does not read, print, persist in benchmark output,
or copy the credential into the result directory. It never copies user config,
plugins, skills, sessions, memories, logs, or marketplace state. In addition,
`--ignore-user-config` excludes `config.toml` while `--ignore-rules` excludes
user and project exec-policy rules. Credential-like ambient environment
variables are removed; the subprocess retains only basic process, locale,
temporary-directory, certificate, and proxy variables. Because Codex also
discovers personal skills beneath `$HOME/.agents/skills` independently of
`CODEX_HOME`, the runner refuses a live benchmark when that directory contains
skills. The candidate workspace itself contains only the common `AGENTS.md`;
the treatment adds `.agents/skills/design-council`. Candidate cells are opaque
random directories and contain neither `treatment` nor `control` in the
candidate-visible working-directory path.

A saved Codex login is therefore required; run `codex login` before a live
benchmark. API keys and unrelated service credentials from the ambient shell
are intentionally not forwarded.

This is strong process-level isolation, not a claim of hardware isolation. The
same account, service, CLI binary, model release, network, and host-level
environment remain shared. On the August 13, 2026 host smoke test, a bundled
runtime MCP attempted initialization and emitted the same authentication
diagnostic in both arms even though no user plugin/config was copied. The
runner flags this boundary and retains stderr for inspection. Provider-side
caching and nondeterminism may also affect results, which is why prompt order
is counterbalanced and token reports separate cached from uncached input. Never
commit raw event/log artifacts; they can contain machine paths or
model-generated study content even though the runner does not log credentials.

## Corpus contract

Every case declares:

- explicit, implicit, or intentionally avoided invocation;
- observable expected behavior, not private reasoning;
- the product invariants exercised;
- conservative regex checks for smoke detection;
- semantic criteria for a model judge or human reviewer.

Regex results are smoke signals, not a substitute for behavioral judgment.
Model-judge output is also evidence for inspection rather than a scientific
quality score.

## Cross-platform adapter contracts

`openai/manifest.json` and `claude/manifest.json` map the complete shared case
corpus in `cases/` to each generated package. Explicit cases receive the native
primary invocation (`$design-think` for Codex or `/design-council:design-think`
for the Claude plugin); implicit and avoid-routing prompts remain byte-for-byte
unchanged. ChatGPT uses `@design-think`. Exact Claude `/design-think` is only a
separately installed explicit-only delegating alias; the plugin itself remains namespaced.
Legacy `$design-council` and
`/design-council:design-council` remain beta compatibility checks rather than the
primary adapter mapping. The platform directories do not copy cases or fixtures.

Run both mappings, or one adapter, without model calls:

```sh
make platform-evals
python3 evals/run_platform_contracts.py --platform openai
python3 evals/run_platform_contracts.py --platform claude --json
```

This is a deterministic adapter/parity gate. It does not claim the behavioral
cases passed a live model; authenticated platform runs remain a separate release
check.
