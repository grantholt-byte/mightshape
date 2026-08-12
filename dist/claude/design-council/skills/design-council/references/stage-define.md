# Define mode

## Goal

Transform traceable evidence into competing human-centered frames without smuggling the proposed solution into the need.

Use this ladder:

`raw evidence → observations → patterns → needs → tensions → insights → competing POVs → HMW prompts`

Do not skip rungs merely because a compelling concept already exists.

## Synthesis sequence

1. **Prepare evidence.** Run `check_evidence.py`; separate human, research, inference, synthetic, Council, assumptions, and unknowns.
2. **Share and cluster.** Group records by meaningful similarity, not desired conclusion. Preserve unclustered observations and negative cases.
3. **Find patterns and tensions.** Look for repeated mechanisms, sequence breaks, workarounds, conflicting goals, say/do gaps, power differences, and context dependence.
4. **Extract needs.** Use verbs or capacities. A need should remain valid across several possible solutions.
5. **Generate insights.** Connect evidence to a non-obvious explanation or opportunity. State inferential status.
6. **Create competing frames.** At minimum consider obvious, behavioral, systems, and counterintuitive interpretations when evidence permits.
7. **Write POVs.** `USER + NEED + INSIGHT`; cite supporting evidence IDs and unknowns. For a substantial ambiguous journey, show at least two genuinely competing POVs before selecting a provisional frame, and label ungrounded Council frames `DESIGN_COUNCIL`.
8. **Generate HMWs.** Produce several transformations broad enough for alternatives and narrow enough for direction.

## Solution-contamination test

Ask:

- Does the need name an artifact, feature, channel, technology, or implementation?
- Would the need disappear if the proposed solution were forbidden?
- Does it describe what a person is trying to accomplish, feel, avoid, understand, or control?

Bad: “Parents need an AI calendar.”

Better: “Parents need confidence that commitments will not silently collide.”

## Insight test

An observation states what happened. A pattern states recurrence. An insight proposes a supported explanation that opens design possibility.

Weak: “Parents are busy.”

Stronger: “Coordination is not one planning task; commitments arrive through unrelated channels, so calendar maintenance becomes continuous reconciliation.”

Label the stronger statement `RESEARCH_SUPPORTED_INFERENCE` unless directly established.

## POV quality

Use `score_pov.py` as a facilitation heuristic across human-centered, evidence-grounded, specific, insightful, generative, and solution-independent dimensions. Maximum 30:

- 26–30 `STRONG_FRAME`
- 21–25 `PROMISING`
- 15–20 `FRAGILE`
- 0–14 `REFRAME`

Do not treat the score as scientific. A high score cannot repair weak evidence.

## HMW transformations

Generate direct, amplify, remove, invert, assumption-questioning, extreme-user, scale-up, scale-down, analogy, resource-constraint, impossible-ideal, and system-intervention variants as useful. Keep competing POVs visible; do not crown one prematurely.

## Exit and backward movement

Move to Ideate when at least one useful, solution-independent frame exists and the team needs breadth. Return to Empathize when clusters rely on inference, a key stakeholder is absent, contradictions cannot be explained, or the frame depends on a synthetic claim.
