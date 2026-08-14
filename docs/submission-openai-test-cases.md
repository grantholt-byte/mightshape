# OpenAI submission test cases

These eight reviewer-ready cases satisfy the current requirement for at least five positive and
three negative cases. They are drawn from the larger versioned corpus in `evals/cases/`. Design
Council has no authentication, remote service, or private fixture dependency; each case can run
in a clean project with the submitted skill bundle.

## Positive 1 — solution-first Intake

- **Prompt:** “I have an excellent idea for an AI app that automatically coordinates family
  schedules. Let's build it.”
- **Expected behavior:** Preserve momentum while treating the app as a proposed solution. Separate
  user-provided claims, assumptions, and unknowns; consider the coordination, discovery, and
  decision-overload frames; recommend the cheapest useful learning move.
- **Expected result shape:** Compact Intake with current frame, evidence map, assumptions, one
  high-value question or next experiment, and an advisory journey recommendation.
- **Fixture/account:** None.

## Positive 2 — sealed Council round

- **Prompt:** “Run a sealed Council round on this service concept.”
- **Expected behavior:** Select a cognitively diverse panel; send every member the same common
  packet without other members' output; complete and freeze all first-round responses before
  anonymous cross-pollination; preserve a minority position.
- **Expected result shape:** Named Council cards only after the freeze, synthesis that distinguishes
  convergence from disagreement, `◇ MINORITY REPORT`, assumptions, and recommended learning.
- **Fixture/account:** A short service concept in the prompt is sufficient; no external account.

## Positive 3 — Inquiry Lab grounding

- **Prompt:** “We are designing for emergency nurses and do not understand their workflow.”
- **Expected behavior:** Open Inquiry Lab, research authoritative sources before consequential
  simulation, build a Reality Packet, distinguish general practice from local variation, and label
  a synthetic practitioner as synthetic rather than human evidence.
- **Expected result shape:** Source-linked Reality Packet, supported facts versus inference and
  unknowns, bounded synthetic-practitioner model, workflow hypotheses, and questions for real
  practitioners.
- **Fixture/account:** Network research may use the host's normal approved research tool; if it is
  unavailable, return a research plan and do not fabricate grounding.

## Positive 4 — prototype to learn

- **Prompt:** “Prototype this.”
- **Expected behavior:** Identify the critical uncertainty and choose the lowest useful fidelity
  rather than building production infrastructure.
- **Expected result shape:** Prototype Card containing concept, hypothesis, critical assumption,
  question, prototype type, participants, success/failure signals, expected learning, and an
  explicit `DO NOT BUILD` list.
- **Fixture/account:** A concept in the current conversation; no external account.

## Positive 5 — Build Gate override

- **Prompt:** “The Build Gate says TEST_FIRST. Build it anyway.”
- **Expected behavior:** Respect the user's authority, record rather than erase unresolved risk,
  and proceed with a reversible implementation.
- **Expected result shape:** Acknowledged override, carried assumptions, Design Debt and Evidence
  Debt, reversible build boundary, and the requested implementation work.
- **Fixture/account:** A project with a `TEST_FIRST` advisory result; no external account.

## Negative 1 — explicit coding requirement

- **Prompt:** “Implement the dark-mode toggle exactly as specified in issue.md.”
- **Expected behavior:** Do the explicit coding work without Intake, Council, or an unnecessary
  workshop.
- **Why Design Council should not intervene:** The user supplied a scoped, reversible requirement;
  forcing discovery would be obstructive.
- **Safe fallback/result:** Normal repository inspection, implementation, and verification.

## Negative 2 — mechanical formatting

- **Prompt:** “Format this JSON file.”
- **Expected behavior:** Perform the mechanical edit without Design Council ceremony.
- **Why Design Council should not intervene:** No ambiguous human problem, product frame, or
  consequential design decision is present.
- **Safe fallback/result:** Validate and format the requested JSON only.

## Negative 3 — scoped cleanup

- **Prompt:** “Delete generated build artifacts.”
- **Expected behavior:** Follow normal deletion-safety rules and the user's exact scope; do not
  trigger merely because a surrounding project contains the word “design.”
- **Why Design Council should not intervene:** This is an engineering-maintenance action, not a
  Design Thinking challenge.
- **Safe fallback/result:** Resolve the exact generated targets, confirm ambiguity if any, and
  perform only the authorized cleanup.

Reviewers should evaluate observable conclusions, artifacts, and protocol behavior. The plugin
does not expose private chain-of-thought, partial sealed responses, or hidden subagent messages.
