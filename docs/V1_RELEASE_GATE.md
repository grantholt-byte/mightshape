# V1 release gate

This gate was fixed before inspecting the current release-candidate benchmark results. It
separates product quality, comparative outcome evidence, resource diagnostics, and marketplace
administration so a favorable result in one category cannot hide a failure in another.

## Product gate

All deterministic checks must pass from a clean, exact source freeze:

- unit, adversarial behavioral, platform-mapping, schema, state/history, Council independence,
  Humanity, Inquiry, visual, and interview-app tests;
- bundled OpenAI authoring checks plus locally enforceable directory rules;
- strict Claude plugin and marketplace validation;
- byte-identical shared core and all ten Human Models across adapters;
- deterministic archives, secret scan, dependency audit, and clean install/invocation checks;
- no unresolved high-severity defect in evidence provenance, consent, sealed independence,
  project history, or Build Gate override.

## Comparative outcome gate

The primary intended-use comparison is deliberate Design Council invocation on treatment turn one
in a persisted multi-turn trajectory study against the frozen competent Design Thinking prompt on
every control turn. It must be bound to a clean commit, complete exactly as planned, have more
trajectory wins than losses, and return
`MEANINGFUL_TREATMENT_BENEFIT_ESTABLISHED`: the case-bootstrap interval's lower bound must clear
the preregistered 3-point minimum important uplift.

The machine-enforced policy is
[`evals/benchmark/v1-trajectory-gate-policy.json`](../evals/benchmark/v1-trajectory-gate-policy.json).
It fixes the exact five neutral trajectory IDs and canonical corpus hash, four-turn shape,
persisted mode, competent-prompt control, explicit first-turn treatment invocation, two candidate
repeats, two blind judge repetitions, seed `20260813`, at least 10,000 bootstrap samples, 2-point
tie margin, 3-point minimum important uplift, `gpt-5.6-sol`/medium candidate, and
`gpt-5.6-terra`/medium judge. Run:

```sh
make verify-v1-trajectory-gate RUN_DIR=evals/results/trajectory/<run-id>
```

The verifier exits zero only after independently reconstructing the run from raw artifacts. The
two product-specific Council and Inquiry trajectories remain separate conformance fixtures and
cannot enter the primary comparative efficacy corpus.

The demanding explicitly invoked one-shot comparison against the same competent prompt is secondary. It must not
establish a meaningful control advantage, must preserve direct execution on low-ambiguity work,
and must be inspected case by case for regressions hidden by an aggregate. A positive one-shot
result is desirable; the product's distinctive longitudinal value must not be inferred from it.

Implicit availability is a separate routing/discoverability estimand. It must pass positive and
negative activation cases, but it does not replace the deliberate-use capability comparison.

The raw-prompt comparison remains a sanity check, not the main claim. All model judgments are
subjective measurement aids. Public claims that Design Council improves real team or product
outcomes require held-out prompts and independent blind human raters; model results alone support
an engineering release decision, not that broader claim.

Native Claude performance must be measured within Claude before making a Claude-specific efficacy
claim. Shared files and contract parity establish package parity, not model behavior parity.

## Resource gate

Outcome quality is primary. Token ratio, absolute incremental tokens, latency, visible words, and
loaded-reference profiles are reported separately. The 1.5× token ratio remains an optimization
target, not a veto of a demonstrated quality benefit.

Before release, inspect every high-cost/no-gain case and remove repetition, duplicate resource
loads, ceremonial headers, and unnecessary panels. Do not remove competing frames, conceptual
distance, dissent, provenance, or a decision-changing experiment branch merely to hit a token
target. Re-run comparative quality after any material compression.

## Release and publication boundary

Only after the product and comparative outcome gates pass should the canonical version move from
the beta line to `1.0.0`, packages be rebuilt, and an immutable V1 tag be created. Marketplace
submission remains a separate manual act. Verified publisher identity, hosted legal/support URLs,
availability selections, policy attestations, public-repository choice, portal upload/review, and
the final Publish action cannot be manufactured by repository automation.

If a gate fails, keep the beta version, diagnose the measured weakness, make a bounded change, and
run a new frozen comparison. Never relabel an inconclusive result as success because the files are
complete or the treatment used more tokens.
