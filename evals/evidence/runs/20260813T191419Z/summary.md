# Design Council longitudinal A/B benchmark

**Effectiveness verdict:** `TREATMENT_ADVANTAGE_DETECTED_BELOW_IMPORTANCE_THRESHOLD`

Blind trajectory quality: 98.333333 treatment vs 94.166667 control (+4.166666 points).
Cases: 2 wins / 1 ties / 0 losses.
Control comparator: `design-thinking-prompt`.
Estimand: within-model quality uplift from Design Council skill availability over a no-skill trajectory receiving the frozen Design Thinking prompt on every user turn.

The effectiveness verdict is based on outcome quality. Resource use is reported separately and does not veto quality improvement.

## Longitudinal dimensions

- frame_adaptation: 100.0 vs 98.333333 (delta +1.666667)
- history_preservation: 98.333333 vs 93.333333 (delta +5.0)
- assumption_updates: 98.333333 vs 96.666667 (delta +1.666666)
- conceptual_divergence: 95.0 vs 95.0 (delta +0.0)
- experiment_information_gain: 98.333333 vs 85.0 (delta +13.333333)
- backward_iteration: 100.0 vs 98.333333 (delta +1.666667)
- momentum_and_task_fit: 96.666667 vs 95.0 (delta +1.666667)
- evidence_calibration_and_provenance: 100.0 vs 91.666667 (delta +8.333333)

## Resource diagnostics

- Treatment/control generation-token ratio: 1.643486
- Treatment/control wall-time ratio: 1.24261
- Judge usage is benchmark overhead and excluded from arm resource totals.

## Reproducibility

- Run: `20260813T191419Z`
- Session mode: `persisted`
- Control mode: `design-thinking-prompt`
- Frozen prompt-only instruction SHA-256: `ad1b7fee598bafda3095c38fcb068686ecf369506cbeca85e7ddadeb715a40f8`
- Candidate: `gpt-5.6-sol` / `medium`
- Judge: `gpt-5.6-terra` / `medium`
- Design Council version: `0.9.0-beta.5`
- Git commit: `7bba36d2d4713bf1d697618eafad5d022f9a76ce`; dirty: `False`; status available: `True`
- Corpus SHA-256: `9c8c35fa408f78244aeedd1e07dd1afbf9687cd7803a23154fcbf60f7f17dc8e`
- Skill SHA-256: `4ab0b6e074b74865f5e4fc7331eea0f0fba483fff9b9bd9269c66199a4fd2a31`
- All planned candidate trajectories and blind judgments completed before reporting.
- Persisted mode resumes an explicit verified thread ID; it never uses `--last`.
- Raw stdout, stderr, event streams, environment variables, and credentials are not saved.

## Interpretation limits

- Blind model judgments are subjective measurement aids, not ground truth.
- The three product-authored trajectories are a small exploratory corpus, not confirmatory efficacy evidence.
- The corpus uses explicit fictional benchmark evidence; it does not establish real user outcomes.
- This measures assistant-trajectory quality, not shipped-product or longitudinal team performance.
- Native Claude effectiveness requires a separate within-Claude run.
