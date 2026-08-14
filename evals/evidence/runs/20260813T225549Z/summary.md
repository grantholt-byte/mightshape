# Design Council longitudinal A/B benchmark

**Effectiveness verdict:** `TREATMENT_ADVANTAGE_DETECTED_BELOW_IMPORTANCE_THRESHOLD`

Blind trajectory quality: 97.0 treatment vs 93.125 control (+3.875 points).
Cases: 4 wins / 0 ties / 1 losses.
Control comparator: `design-thinking-prompt`.
Treatment invocation: `explicit-first-turn`.
Estimand: within-model quality uplift from deliberate Design Council invocation on turn one over a no-skill trajectory receiving the frozen Design Thinking prompt on every user turn.

The effectiveness verdict is based on outcome quality. Resource use is reported separately and does not veto quality improvement.

## Longitudinal dimensions

- frame_adaptation: 96.0 vs 99.0 (delta -3.0)
- history_preservation: 100.0 vs 87.0 (delta +13.0)
- assumption_updates: 100.0 vs 94.0 (delta +6.0)
- conceptual_divergence: 94.0 vs 91.0 (delta +3.0)
- experiment_information_gain: 94.0 vs 90.0 (delta +4.0)
- backward_iteration: 98.0 vs 99.0 (delta -1.0)
- momentum_and_task_fit: 94.0 vs 99.0 (delta -5.0)
- evidence_calibration_and_provenance: 100.0 vs 86.0 (delta +14.0)

## Resource diagnostics

- Treatment/control generation-token ratio: 1.546573
- Treatment/control wall-time ratio: 1.306717
- Judge usage is benchmark overhead and excluded from arm resource totals.

## Reproducibility

- Run: `20260813T225549Z`
- Session mode: `persisted`
- Control mode: `design-thinking-prompt`
- Treatment invocation: `explicit-first-turn`
- Frozen prompt-only instruction SHA-256: `ad1b7fee598bafda3095c38fcb068686ecf369506cbeca85e7ddadeb715a40f8`
- Candidate: `gpt-5.6-sol` / `medium`
- Judge: `gpt-5.6-terra` / `medium`
- Design Council version: `0.9.0-beta.7`
- Git commit: `893867f7d233483e1c8cc58c16ca2def59ca0161`; dirty: `False`; status available: `True`
- Corpus SHA-256: `8c8fbe4f6a1e10baa92f267b2570e06e4009a754ddefad96b29112565aab75fd`
- Skill SHA-256: `64db3803a559fe31d5fd125267ef5bdb0e18b8e15af1ddc0c974d8087708c171`
- All planned candidate trajectories and blind judgments completed before reporting.
- Persisted mode resumes an explicit verified thread ID; it never uses `--last`.
- Raw stdout, stderr, event streams, environment variables, and credentials are not saved.

## Interpretation limits

- Blind model judgments are subjective measurement aids, not ground truth.
- The 5 product-authored trajectories are a small exploratory corpus, not confirmatory efficacy evidence.
- The corpus uses explicit fictional benchmark evidence; it does not establish real user outcomes.
- This measures assistant-trajectory quality, not shipped-product or longitudinal team performance.
- Native Claude effectiveness requires a separate within-Claude run.
