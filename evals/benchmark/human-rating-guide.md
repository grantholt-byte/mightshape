# Blind human outcome-rating guide

Use this protocol to measure the subjective value the product is intended to create. It complements
model judging; it does not replace controlled generation or provenance checks.

## Comparison conditions

Within each platform, generate candidates from the same starting material, model class, effort,
permissions, and timebox:

1. plain session with the raw user prompt;
2. plain session plus the frozen prompt-only Design Thinking instruction recorded by
   `run_ab_benchmark.py --control-mode design-thinking-prompt`;
3. Design Council available, with the same raw user prompt.

Do not compare absolute Codex and Claude scores. Estimate each platform's within-platform uplift.
Use held-out prompts written by people who did not author the plugin or its current rubric. Include
ambiguous product decisions, service/system challenges, research synthesis, divergent ideation,
prototype-to-learn decisions, contradictory evidence, and clear direct-execution controls.

## Blind quality rating

Randomize and label paired artifacts A/B. Remove platform/plugin names and superficial headers where
doing so does not remove substantive content. A rater first answers:

- Which response is more likely to improve the team's **next decision**?
- Which better challenges a proposed solution and helps find the **right problem**?
- Which creates **meaningfully different possibilities**, rather than feature variants?
- Which better distinguishes evidence, inference, assumptions, synthetic signals, and unknowns?
- Which proposes the more **informative, reversible experiment**?
- After contradictory evidence, which updates the frame and preserves useful history?
- Which preserves momentum without imposing unnecessary process?
- Which would the rater choose to continue working with?

Record the result with `human-paired-rating.schema.json`. Reveal token usage and latency only after
the quality rating is locked. This prevents cost expectations from contaminating the outcome judgment.

## Multi-turn trajectory

For longitudinal cases, give both arms the same fixed sequence:

1. a solution-first request;
2. a user constraint or contribution;
3. contradictory interview/observation/experiment evidence with explicit provenance;
4. a request to revise the frame and choose the next test.

Rate frame change, history preservation, assumption updates, conceptual breadth, experiment learning
leverage, backward iteration, and momentum. Never let one arm choose evidence that the other arm does
not receive. A scripted evidence injection tests adaptation rather than research luck.

## Claims boundary

Report win/tie/loss counts, preference proportions, rater agreement, and uncertainty. Keep resource use
as a separate profile. Do not infer shipped-product outcomes, actual human behavior, or long-term team
performance from response ratings. Native Claude efficacy requires a native Claude run; package parity
does not establish behavioral parity.
