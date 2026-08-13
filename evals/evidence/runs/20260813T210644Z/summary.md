# Design Council paired A/B benchmark

**Primary outcome effectiveness:** `DIRECTIONAL_BENEFIT_NOT_YET_ESTABLISHED_AS_MEANINGFUL`
**Quality direction:** `TREATMENT_BETTER`
**Token-budget descriptor:** `ABOVE_CONFIGURED_BUDGET`
**Outcome/resource quadrant:** `QUALITY_GAIN_FOR_TOKEN_PREMIUM`

This report compares identical raw prompts under two isolated conditions: the treatment workspace contains the frozen repository-local Design Council skill; the control does not load Design Council and receives the frozen prompt-only Design Thinking instruction. Candidate generation order and blind A/B presentation order are counterbalanced.

## Result

| Measure | Treatment | Control | Comparison |
|---|---:|---:|---:|
| Blind quality (0–100) | 95.54 | 92.98 | 2.56 points (2.8%) |
| Mean generation tokens | 23,406 | 15,371 | Δ 8,035 (1.52×) |
| Mean wall time | 45.00s | 36.96s | 1.22× |
| Mean visible response words | 648 | 654 | 0.99× |

Paired case-level quality uplift 95% bootstrap CI: **[0.42, 4.82]**. 
Paired standardized effect (dz): **0.61**. 
Case wins/ties/losses: **7/2/3**.
Blind treatment/control/tie judge votes: **37/11/0**.

## Incremental value purchased

Design Council bought **2.56 blind-quality points** for **8,035 additional generation tokens per case run**. That is **0.32 quality points per 1k additional tokens**, or **3,139 additional tokens per quality point**.

Quality-uplift interval expressed over the fixed observed token premium: **[0.05, 0.60] quality points per 1k additional tokens**. This is not a joint cost-effectiveness confidence interval.

Measured quadrant: `QUALITY_GAIN_FOR_TOKEN_PREMIUM`. Case win rate: **58.3%**; net case wins: **4**. Relative quality uplift / relative token premium: **0.05**.

This is a measured outcome/resource profile, not monetary ROI. It does not assign business value to a quality point or assume account-specific token pricing.

## User-value construct profile

These overlapping case groups expose the capabilities the plugin is intended to add. They are diagnostic group means, not independent psychometric subscales.

| Construct | Cases | Treatment | Control | Δ quality | W/T/L |
|---|---:|---:|---:|---:|---:|
| Right-problem framing | 6 | 94.29 | 93.10 | 1.19 | 3/1/2 |
| Structured divergence and synthesis | 6 | 95.00 | 95.24 | -0.24 | 2/1/3 |
| Evidence discipline | 9 | 94.92 | 93.33 | 1.59 | 5/1/3 |
| Learning-oriented experiments and iteration | 8 | 95.54 | 93.66 | 1.88 | 5/1/2 |
| Appropriate scope and momentum | 2 | 97.14 | 88.57 | 8.57 | 2/0/0 |

Constructs overlap by design and are diagnostic group means, not independent subscales. Their mapping must be frozen before a confirmatory run; mappings added after a run are post-hoc.

## Blind judge dimension profile

| Dimension | Treatment | Control | Δ |
|---|---:|---:|---:|
| Problem Understanding | 99.58 | 98.75 | 0.83 |
| Methodological Rigor | 98.33 | 88.33 | 10.00 |
| Breadth And Nonobviousness | 95.42 | 92.50 | 2.92 |
| Evidence Calibration | 97.50 | 93.75 | 3.75 |
| Actionability | 96.25 | 98.33 | -2.08 |
| Task Fit And Clarity | 97.92 | 95.00 | 2.92 |
| Communication Efficiency | 83.75 | 84.17 | -0.42 |

### Generation-cost anatomy

| Mean per successful, resource-complete candidate call | Treatment | Control | Absolute Δ (T−C) |
|---|---:|---:|---:|
| Total tokens | 23,406 | 15,371 | 8,035 |
| Input tokens | 21,972 | 14,355 | 7,616 |
| └ cached input | 12,960 | 10,112 | 2,848 |
| └ uncached input | 9,012 | 4,243 | 4,768 |
| Output tokens | 1,434 | 1,016 | 418 |
| └ reasoning output | 447 | 132 | 315 |
| Visible response words | 648 | 654 | -6 |
| Completed observable items | 2.21 | 1.08 | 1.12 |
| Completed tool calls | 0.21 | 0.00 | 0.21 |
| └ command executions | 0.21 | 0.00 | 0.21 |
| Assistant messages | 2.00 | 1.04 | 0.96 |

Tool-call counts are observable completed runtime events, not hidden reasoning. Input-token cost includes the model context accumulated across those interaction rounds.

## Outcome effectiveness test

Design Council is directionally better, but the interval still overlaps the preregistered practical-importance threshold.

- Minimum important quality uplift: `3.00` points
- Complete realized design: `True` (24/24 complete pairs)
- Exact release-quality record/usage integrity: `True`

The primary effectiveness verdict uses outcome quality and practical importance only. It does not use token cost.

## Resource profile

The observed token premium exceeded at least one configured resource budget.

- Configured maximum treatment/control token ratio: `1.50`
- Configured maximum absolute token overhead: `n/a`

This is a resource descriptor, not an outcome-value veto or monetary ROI.

## Descriptive efficiency diagnostic

Treatment/control quality points per 1k total generation tokens: `4.33` / `6.18` (ratio `0.70`). This ratio is not causal, is not price-adjusted, and does not determine outcome effectiveness.

## Per-case results

| Case | Treatment | Control | Δ quality | Δ tokens | Token ratio | Marginal yield | Result |
|---|---:|---:|---:|---:|---:|---:|---|
| Ambiguous AI family scheduler | 90.00 | 92.14 | -2.14 | 4,755 | 1.33× | -0.45 | LOSS |
| Consequential automated career advice | 96.43 | 99.29 | -2.86 | 4,428 | 1.30× | -0.65 | LOSS |
| Unfamiliar emergency nursing workflow | 95.00 | 94.29 | 0.71 | 15,488 | 2.05× | 0.05 | TIE |
| Municipal extreme-heat preparedness | 95.71 | 93.57 | 2.14 | -5,434 | 0.78× | n/a | WIN |
| Visual affinity clustering | 94.29 | 96.43 | -2.14 | 4,732 | 1.33× | -0.45 | LOSS |
| Cross-channel clinic rescheduling map | 97.14 | 90.00 | 7.14 | 4,500 | 1.30× | 1.59 | WIN |
| Conceptually wide service ideation | 97.86 | 98.57 | -0.71 | 5,351 | 1.36× | -0.13 | TIE |
| Prototype a coordination behavior | 97.14 | 95.00 | 2.14 | 14,253 | 1.98× | 0.15 | WIN |
| Exploratory interview without solution priming | 92.86 | 87.86 | 5.00 | 24,208 | 2.64× | 0.21 | WIN |
| Reframe after contradictory evidence | 95.71 | 91.43 | 4.29 | 14,536 | 2.03× | 0.29 | WIN |
| Straightforward specified implementation | 95.71 | 85.71 | 10.00 | 5,033 | 1.36× | 1.99 | WIN |
| Cheap coded technical experiment | 98.57 | 91.43 | 7.14 | 4,568 | 1.32× | 1.56 | WIN |

## Interpretation warnings

- The host runtime emitted bundled plugin/MCP diagnostics despite the fresh Codex homes. No project or user plugins were copied, but built-in runtime capabilities remain a shared environmental boundary.
- More than 20% of multiply judged pairs changed winner across counterbalanced presentations; inspect judge stability.
- Quality per 1k tokens is a descriptive heuristic only. It is never used to infer causality or determine outcome effectiveness.
- Judge blinding conceals arm allocation, but candidate wording may reveal Design Council terminology; this is not guaranteed content blinding.
- The bundled corpus and rubrics were authored with the product; confirm release claims on held-out external prompts and preferably independent human judges.

## Reproducibility

- Run ID: `20260813T210644Z`
- Candidate runtime / model / effort: `codex` / `gpt-5.6-sol` / `medium`
- Judge model / effort: `gpt-5.6-terra` / `medium`
- Seed: `20260813`
- Cases × repeats: `12 × 2`
- Blind judgments per pair: `2`
- Prompt corpus SHA-256: `afb507b2d2e22eb384a239ca4aaed03e0c9f35e88538c10d327b395c1dab9a29`
- Control mode: `design-thinking-prompt`
- Treatment invocation: `explicit`
- Design Council version: `0.9.0-beta.6`
- Canonical skill tree SHA-256: `e29ddf931204cdf560fd03b300dd04d478422f67ae3aba6e2d976b61313cc975` (108 files)
- Benchmark runner SHA-256: `42d022a44ec9ea8b49b3689f9b2a3df38c414257f75ae2202293c75d1df54739`
- Judge schema SHA-256: `e159ffaad62281672b57e81051a535cc4b4799697a6ceee507fd01bcd2eff66e`
- Git commit: `f88cb2ec3ee0f4bba3a2428e12572b58c7093bcd`; dirty: `False`
- Codex CLI: `codex-cli 0.146.1`
- Claude CLI: `n/a`
- Python: `CPython 3.11.3`
- Platform: `macOS-15.7.7-x86_64-i386-64bit`
- Bootstrap resamples whole cases, not repeated generations, to avoid pseudo-replication.
- Judge tokens are reported as benchmark overhead and excluded from each arm's generation cost.

Inspect `generations.jsonl`, `judgments.jsonl`, `blinded-pairs.jsonl`, and the saved responses before making a release claim.
