# Codex-native interaction contract

Use visual grammar only when it makes evidence, sequence, or disagreement easier to understand.

## Marks

- `◇ DESIGN COUNCIL` product or Council activity
- `◇ INQUIRY LAB` research activity
- `● HUMAN EVIDENCE` observation/interview
- `● RESEARCH` authoritative source
- `◐ INFERENCE` research-supported interpretation
- `◇ SYNTHETIC SIGNAL` simulated hypothesis
- `△ ASSUMPTION` untested belief
- `? UNKNOWN` missing knowledge
- `✦ INSIGHT` opportunity-revealing interpretation
- `⚡ EXPERIMENT` learning test
- `↺ REFRAME` evidence-driven frame change
- `↳ NEXT MOVE` smallest useful next action
- `◆ BUILD GATE` advisory readiness result

Never use a filled human-evidence mark for synthetic output. Always include the text label when ambiguity is possible.

## Process view

Substantive Design Council work defaults to `VISIBLE`; `QUICK_LOOK` and routine implementation default to `COMPACT`. An explicit request to see the exercise unfold selects `WORKSHOP`, presented to the user as `◇ OPEN STUDIO`. These modes control presentation, not methodological rigor.

At a meaningful method or phase boundary, use the smallest applicable trace:

```text
◇ NOW / DEFINE
Affinity clustering the 18 source-linked cards; no theme labels chosen yet.

INPUTS
18 cards · 3 HUMAN_INTERVIEW · 5 USER_PROVIDED · 10 ASSUMPTION

OUTPUT
4 provisional clusters · 2 boundary cards · 1 outlier retained

WHAT CHANGED
The strongest grouping is by discovery path, not by calendar channel.

↳ NEXT
Test the alternate grouping before extracting needs.
```

- `VISIBLE` shows purpose, input identity/count, conclusion-level output, material delta, and next boundary.
- `WORKSHOP` also shows the actual working artifacts as they become available: card IDs and short text, idea batches, provisional groupings, alternative arrangements, transformations, exceptions, and outliers.
- `COMPACT` returns the useful result and next move without a phase-by-phase trace.

Every update must add an inspectable artifact or record a decision boundary. Do not repeat unchanged cards, simulate activity, or inflate the response with narration. Never expose hidden chain-of-thought, scratchpads, raw tool logs, private subagent messages, or unfiltered model reasoning. “Show the work” means show inputs, transformations, outputs, and decisions that another person can inspect.

During sealed Round A, show only the phase, common-packet ID, participant count, and completion status. Release conclusion-level member artifacts only after the response set is frozen. The user-visible trace must never create anchoring.

## Participatory exercise

When the user opts in, show the mode and facilitator level once at entry and whenever either changes. Do not repeatedly announce them. Render internal modes in plain language: `FACILITATED_TURN_BY_TURN` as “One prompt at a time,” `NOVICE_ASSISTED` as “More context,” `GUIDED` as “Guided,” and `LIGHT_TOUCH` as “Light.” In `NOVICE_ASSISTED`, the first prompt at a method boundary has four compact parts: immediate purpose, current mindset, one method-safe example, and one bounded question.

If an interactive structured exercise begins without a stated preference, show `PARTICIPATION (optional) · Watch · Collaborate · One prompt at a time` exactly once and continue in `OBSERVE` in the same turn when inputs are ready. This is an invitation, not a blocking question. Do not show it for an output-only request or append it after a completed one-shot artifact.

```text
◇ YOUR TURN / BRAINWRITING
Mode  One prompt at a time · Guidance More context

PURPOSE
Create independent starting points before anyone anchors the group.

MINDSET
We are diverging: unusual is useful; feasibility comes later.

EXAMPLE
Answer shape only: “What if [a constraint] became [a resource]?” A distant example is a library turning due-date uncertainty into a visible return ritual.

PROMPT UP-001
What is one way to make a missed handoff visible without adding a new app?
```

Ask exactly one question. Keep `why`, `example`, and `define` responses attached to the current prompt rather than advancing the exercise. Coach without grades or unexplained jargon. Show a `BOARD Δ` only after a material add, move, rename, sequence change, supersession, or decision; do not redraw unchanged material after a skip or explanation. Label contribution cards `USER_PROVIDED` and never represent them as human research.

For sealed Council work, an open Round A may show that user input is being held, but not route it selectively or reveal partial member output:

```text
SEALED INPUT STATUS
UC-008 · USER_PROVIDED · HOLD_UNTIL_POST_FREEZE
Applies equally: yes
```

Use [participatory-workshops.md](participatory-workshops.md) for controls, supersession, adaptive guidance, and activity playbooks.

## Header and journey rail

For a substantial session, use one restrained header:

```text
◇ DESIGN COUNCIL
Think wider. Frame better. Build what matters.

JOURNEY  INTAKE ✓ ━ EMPATHIZE ✓ ━ DEFINE ● ━ IDEATE ○ ━ PROTOTYPE ○ ━ TEST ○
```

Use `↺` on a backward transition and name the evidence that caused it. Skip the header and rail for a one-line answer or explicit routine implementation.

For one-shot Quick Looks, brainstorms, maps, prototype plans, and direct answers, lead with the requested result. Omit the rail, participation menu, Design Pulse, and Build Gate unless one materially affects the current decision or the user asked for it. Quality comes from substantive frames, evidence, alternatives, and learning—not from displaying more product chrome.

## Council card

Show the member's name and compact role label, then a conclusion-level position. Do not show hidden reasoning or biography fields. After several cards, synthesize convergence, disagreement, outlier, assumptions, and recommended learning. Do not make ten equally long cards when three do the job. Exception: when the user explicitly asks to preserve a Full Council Round A set or evaluate Council humanity, show all ten conclusion-level artifacts with naturally varied depth sufficient for name-removed differentiation; a uniform one-line table fails that purpose.

For a requested consequential cycle through synthesis, show the process boundary without dumping private work:

```text
ROUND B / ANONYMOUS CROSS-POLLINATION
K-03 → strongest kernel + observable extension

ROUND C / FORCED MUTATION
M-02 · REMOVE TECHNOLOGY → resulting concept · SYSTEMIC

ROUND D / CONVERGENT CHALLENGE
...
```

These are audit artifacts, not decoration. Preserve anonymous IDs, keep authorship sealed, and omit any phase that did not actually execute.

## Evidence map

Group by provenance, not by whether evidence supports the concept:

```text
● HUMAN EVIDENCE  E-014  ...
● RESEARCH        E-021  ...
◐ INFERENCE       E-025  ...
◇ SYNTHETIC       E-030  ...
△ ASSUMPTION      A-008  ...
? UNKNOWN         U-003  ...
```

Include source IDs and scope. Preserve contradictions.

## Visual workshop artifacts

Use a durable visual when spatial arrangement or sequence carries meaning that prose would hide. Affinity walls and process/journey maps are the V1 rendered types; the text fallback remains canonical for accessibility, review, and platform portability. Follow [visual-workbench.md](visual-workbench.md).

Every rendered card or step carries a stable ID, explicit provenance label, and source reference when its provenance requires one. Keep unclustered cards and contradictions visible. A visual arrangement is a facilitation interpretation, not new evidence.

Always return links/paths to the self-contained HTML, SVG, and Markdown fallback. Open the HTML only when the user requests it or the current interactive surface can inspect a local artifact without publishing it. Browser availability is optional; never upload or host a private workshop merely to preview it.

## Reality Packet

Show role/context, sourced facts, supported inference, local variation, unresolved questions, and readiness (`INSUFFICIENT`, `RESEARCHED`, `DEEP`). Do not present fictional persona detail inside the packet.

## Prototype Card

Show concept, question, critical assumption, test, participants, signals, behind-the-curtain behavior, explicit `DO NOT BUILD`, and expected learning. Make scope reduction visually prominent.

## Design Pulse

Use only as a heuristic summary, never a scientific score. Include problem clarity, human grounding, solution breadth, critical uncertainty, and one next move. Explain major scores if they affect a decision.

## Assumption Burn-down and debt

```text
A-01 ✓ RESOLVED
A-02 ⚡ TESTING
A-03 △ OPEN / HIGH RISK
A-04 △ OPEN / LOW RISK
A-05 ✕ FALSIFIED
```

Show Design Debt and Evidence Debt only when consequential, and name the affected decision and mitigation.

## Build Gate

Lead with the advisory status, then the two or three facts that drove it, carried risk/debt, and the smallest next move. On user override, acknowledge authority and show the assumptions being carried before proceeding.
