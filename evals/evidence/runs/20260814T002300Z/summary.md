# Design Council longitudinal A/B benchmark

**Effectiveness verdict:** `MEANINGFUL_TREATMENT_BENEFIT_ESTABLISHED`

Blind trajectory quality: 97.5 treatment vs 88.125 control (+9.375 points).
Cases: 4 wins / 1 ties / 0 losses.
Control comparator: `design-thinking-prompt`.
Treatment invocation: `explicit-first-turn`.
Estimand: within-model quality uplift from deliberate Design Council invocation on turn one over a no-skill trajectory receiving the frozen Design Thinking prompt on every user turn.

The effectiveness verdict is based on outcome quality. Resource use is reported separately and does not veto quality improvement.

## Longitudinal dimensions

- frame_adaptation: 98.0 vs 94.0 (delta +4.0)
- history_preservation: 98.0 vs 86.0 (delta +12.0)
- assumption_updates: 100.0 vs 90.0 (delta +10.0)
- conceptual_divergence: 99.0 vs 87.0 (delta +12.0)
- experiment_information_gain: 94.0 vs 78.0 (delta +16.0)
- backward_iteration: 98.0 vs 94.0 (delta +4.0)
- momentum_and_task_fit: 93.0 vs 95.0 (delta -2.0)
- evidence_calibration_and_provenance: 100.0 vs 81.0 (delta +19.0)

## Resource diagnostics

- Treatment/control generation-token ratio: 1.320392
- Treatment/control wall-time ratio: 1.244173
- Judge usage is benchmark overhead and excluded from arm resource totals.

## Reproducibility

- Run: `20260814T002300Z`
- Session mode: `persisted`
- Control mode: `design-thinking-prompt`
- Treatment invocation: `explicit-first-turn`
- Frozen prompt-only instruction SHA-256: `ad1b7fee598bafda3095c38fcb068686ecf369506cbeca85e7ddadeb715a40f8`
- Candidate: `gpt-5.6-sol` / `medium`
- Judge: `gpt-5.6-terra` / `medium`
- Design Council version: `0.9.0-beta.8`
- Git commit: `afddbf4ee4b2c7555f8e390d92edd843427ea31c`; dirty: `False`; status available: `True`
- Corpus SHA-256: `8c8fbe4f6a1e10baa92f267b2570e06e4009a754ddefad96b29112565aab75fd`
- Skill SHA-256: `c6572607c6dca6a94393305660c6c9c5bb919fb5ee5c48602241cdf11934c23b`
- All planned candidate trajectories and blind judgments completed before reporting.
- Persisted mode resumes an explicit verified thread ID; it never uses `--last`.
- Raw stdout, stderr, event streams, environment variables, and credentials are not saved.

## Interpretation limits

- Blind model judgments are subjective measurement aids, not ground truth.
- The 5 product-authored trajectories are a small exploratory corpus, not confirmatory efficacy evidence.
- The corpus uses explicit fictional benchmark evidence; it does not establish real user outcomes.
- This measures assistant-trajectory quality, not shipped-product or longitudinal team performance.
- Native Claude effectiveness requires a separate within-Claude run.
