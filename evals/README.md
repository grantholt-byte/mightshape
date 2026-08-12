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

The runner creates a temporary project, exposes the local skill through
`.agents/skills/design-council`, invokes `codex exec --ephemeral`, and writes
results beneath `evals/results/`. `--judge` adds a separate structured-output
evaluation pass using `schema/model-result.schema.json`. Without the opt-in
environment variable, or when the Codex CLI is unavailable, it exits cleanly
with a visible `SKIP`; use `--require-model` when skipping should fail CI.

Use `--dry-run` to inspect selected prompts without a model call. Use
`--responses-dir PATH` to apply deterministic regex checks to previously saved
`<case-id>.md` responses without network access.

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
invocation (`$design-council` or `/design-council:design-council`); implicit and
avoid-routing prompts remain byte-for-byte unchanged. The platform directories
do not copy cases or fixtures.

Run both mappings, or one adapter, without model calls:

```sh
make platform-evals
python3 evals/run_platform_contracts.py --platform openai
python3 evals/run_platform_contracts.py --platform claude --json
```

This is a deterministic adapter/parity gate. It does not claim the behavioral
cases passed a live model; authenticated platform runs remain a separate release
check.
