# Council independence and deliberation protocol

## Contents

1. Select operating level
2. Assemble the common packet
3. Round A: sealed generation
4. Freeze
5. Round B: anonymous cross-pollination
6. Round C: forced mutation
7. Round D: convergent challenge
8. Round E: Minority Report
9. Round F: synthesis and memory
10. Runtime fallback

## 1. Select operating level

- `FACILITATOR_ONLY`: no simulated member; routine facilitation.
- `PANEL`: 3–5 members selected for relevant expertise and cognitive diversity.
- `FULL_COUNCIL`: all ten for consequential, cross-system decisions.
- `DEEP_DIVERGENCE`: full Council plus multiple independent prompts or mutation passes.

Use `allocate_council.py`; do not summon ten voices as decoration.

## 2. Assemble one immutable common packet

```yaml
round_id: CR-###
task: string
challenge: string
current_problem_frame: string | null
current_pov: string | null
known_evidence:
  - id: E-###
    claim: string
    provenance: enum
    strength: 0..5
assumptions: []
unknowns: []
constraints: []
operating_depth: enum
cycle: integer
```

Exclude facilitator preference, expected answer, relationship history, sibling responses, and prior synthesis. Include a member's own project memory separately and only when relevant.

## 3. Round A — sealed generation

Load exactly one profile:

`council-maya-chen.md`, `council-leo-martinez.md`, `council-priya-rao.md`, `council-marcus-brooks.md`, `council-elena-rossi.md`, `council-theo-bennett.md`, `council-samira-okafor.md`, `council-jack-sullivan.md`, `council-mei-tanaka.md`, or `council-rafael-alvarez.md`.

Require structured, conclusion-level output:

```json
{
  "round_id": "CR-001",
  "member_id": "maya-chen",
  "position": "...",
  "ideas": [{"idea": "...", "territory": "..."}],
  "concerns": ["..."],
  "questions": ["..."],
  "unknowns": ["..."],
  "surprise": "...",
  "knowledge_boundary": "...",
  "confidence": 0.0
}
```

No member may cite, praise, rebut, extend, or predict another member in Round A. No generic “as the X expert” preamble. The output should reveal the person's attention, values, history, and language without biography dumping.

## 4. Freeze

Wait for all selected responses. Validate member IDs, round IDs, required fields, and absence of sibling references. Serialize in stable member-ID order and calculate SHA-256. Write `manifest.json` with packet hash, response hashes, selected members, timestamps, and status `FROZEN`. Never edit frozen files; append a corrected round if one is invalid.

In the user-facing synthesis, include a compact `SEALED RECEIPT`: common-packet ID, selected/completed count, confirmation that every Round A response completed before sharing, and frozen-set ID or digest prefix. This reports process facts, not private reasoning. Never manufacture a receipt for serial roleplay, an incomplete round, or facilitator-only output.

## 5. Round B — anonymous cross-pollination

Remove names, occupations, catchphrases, and member IDs. Give each participant a different anonymous kernel after freeze:

> Find the strongest kernel. Extend rather than judge. Combine it with something from your worldview. Produce a mutation the original author probably would not.

Store the source response hash for audit but do not expose authorship to the mutator.

For a requested end-to-end Council cycle, preserve a compact user-visible ledger after the sealed receipt. Show anonymous kernel IDs, the strongest retained kernel, and the conclusion-level extension. Do not reveal either author or mutator, and do not substitute a narrative assertion that the round happened.

## 6. Round C — forced mutation

Use at least one transformation not already represented: invert, remove technology, automate completely, make fully human, scale 10×, serve one person, remove money, remove time, make asynchronous, make physical, make invisible, change beneficiary, change environment, turn constraint into a feature, serve an extreme user, or transfer an analogy.

For substantial ideation verify territory coverage: `EXPECTED`, `ADJACENT`, `BEHAVIORAL`, `SYSTEMIC`, `RADICAL`. A list of adjacent app features fails divergence.

For a requested end-to-end Council cycle, show a compact mutation ledger before convergence: anonymous concept ID, named transformation, resulting concept, and territory. Include enough entries to demonstrate conceptual distance rather than merely listing mutation names. Never describe an unexecuted mutation as completed.

## 7. Round D — convergent challenge

Only now evaluate desirability, feasibility, viability, accessibility, adoption, system effects, evidence, assumptions, and reversibility. Temporary roles may include Assumption Hunter, Failure Forecaster, or Excluded User Advocate. These roles do not replace identity.

Make the boundary observable with the heading `ROUND D / CONVERGENT CHALLENGE` when the user requested the complete cycle. Cross-pollination and forced-mutation artifacts must appear before it.

Preserve a concept portfolio instead of one winner: `LIKELY_BET`, `DELIGHT_BET`, `SYSTEM_BET`, `CHEAP_TEST`, `LONG_SHOT`.

## 8. Round E — ◇ Minority Report

Ask: “Which idea, objection, or interpretation is in danger of disappearing merely because few people currently support it?”

Record:

- the position in its strongest form;
- why it remains plausible;
- what evidence would resolve it;
- the consequence of ignoring it;
- whether a cheap test can preserve optionality.

Do not manufacture dissent when none exists. “No material minority position” is valid if explained.

## 9. Round F — synthesis and memory

Report only supported group-level conclusions:

- `STRONG_CONVERGENCE`
- `PARTIAL_CONVERGENCE`
- `MEANINGFUL_DISAGREEMENT`
- `OUTLIER_WORTH_SAVING`
- `ASSUMPTIONS`
- `UNKNOWN`
- `RECOMMENDED_LEARNING`

Convergence means overlapping reasoning, not a vote. Preserve confidence differences and the Minority Report.

For ordinary work, summarize member artifacts compactly. If the user explicitly requests preserved Round A artifacts, a Full Council humanity test, or anonymous differentiation review, append all selected conclusion-level artifacts with enough substance to show distinct attention, values, analogies or risk posture, and knowledge boundaries. A uniform table of one-line abstractions is insufficient for a humanity evaluation. Vary natural length and form; do not reveal hidden reasoning, profile fields, canned catchphrases, or résumé exposition.

Update each member's project memory with positions, supported/opposed ideas, unresolved concerns, surprises, important evidence, and changes of mind. A change requires prior/new belief, confidence, evidence IDs, and explanation. Majority agreement alone is not evidence.

## 10. Runtime fallback

Preferred: fresh-context subagents, one profile and one common packet each. With limited slots, batch them; the parent must not alter later prompts based on earlier responses.

Fallback: use `sealed_round.py`:

1. `prepare` writes immutable per-member prompt packets and a manifest.
2. `run` invokes independent ephemeral Codex passes, concurrently when configured, and stages results outside other prompts.
3. `freeze` validates and hashes all results atomically.
4. `anonymize` creates cross-pollination kernels only after `FROZEN`.

If neither subagents nor isolated CLI passes are available, run one facilitator-only response and say the Council round is deferred. Do not falsely label sequential context-contaminated roleplay as sealed.
