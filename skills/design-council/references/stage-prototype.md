# Prototype mode

## Core principle

Prototype the uncertainty, not the product.

A prototype is an instrument for learning. Fidelity is justified only by the question it must answer.

## Prototype Card contract

```yaml
id: PROTO-###
concept: string
hypothesis: string
critical_assumption: A-###
question: string
prototype_type: enum
minimum_fidelity: string
participants_or_context: []
success_signal: string
failure_signal: string
what_not_to_build: []
expected_learning: string
evidence_needed: []
stop_condition: string
```

Make signals behavioral and interpretable. “Users like it” is rarely enough. Include ambiguous outcomes and what would make the test inconclusive.

Keep participant counts and signal denominators consistent. Use a quantitative threshold only when it comes from supplied evidence, a baseline, or an explicit risk tolerance; otherwise identify it as a proposed heuristic to calibrate. For each plausible outcome, state the conditional next move (`if supported`, `if weakened/falsified`, `if inconclusive`) and which competing problem frame it strengthens or weakens.

When a new hard constraint changes time, access, privacy, staffing, or integration, supersede every incompatible earlier scope item before designing the next test. Translate the constraint into feasible capacity; do not carry forward an earlier participant count, case count, duration, or infrastructure plan by inertia.

Do not let convergence erase the alternatives the experiment must discriminate. Before choosing
the final test, list the incumbent and live mechanism alternatives. Use the same realistic trigger
or disruption across the smallest comparison that could change the build decision. If one mechanism
is tested alone, state why a comparison adds no decision value and what result would reopen the
alternatives.

For shared-work and coordination concepts, distinguish accountable ownership from contribution.
Include cases for legitimate parallel work, stale ownership or status, failed transfer recovery,
false duplicate warnings, and complete work falsely blocked as incomplete. A mechanism that prevents
all parallel action or blocks valid work has not solved coordination.

## Choose the cheapest faithful form

- paper prototype for comprehension, sequence, and navigation;
- storyboard for context and emotional/temporal logic;
- roleplay or service rehearsal for handoffs, scripts, and social dynamics;
- clickable mock for interaction concepts without backend reality;
- fake door or landing page for attention/commitment signals, with ethical disclosure;
- concierge/manual workflow for demand and service value;
- Wizard of Oz for perceived automation before automation exists;
- spreadsheet/email/SMS simulation for information and workflow mechanisms;
- coded spike for technical uncertainty or when code is cheaper than simulation;
- physical mock for ergonomics, scale, placement, or use environment;
- technical proof for capability only—not desirability.

Codex should happily build a rapid coded experiment when it is the lowest useful fidelity. Avoid account systems, production databases, generalized frameworks, polished design systems, and automation that do not affect the learning question.

## Fidelity audit

For each component ask: “If this were rougher or manual, would the participant respond differently in a way that invalidates the learning?” If no, reduce it.

Explicitly list `DO NOT BUILD`. This prevents implementation enthusiasm from consuming the experiment.

Run a proportionality pass before presenting the plan. Remove every participant, day, task,
artifact, feature, or facilitator operation that does not increase discrimination, ecological
validity, safety, or decision value. Preserve a matched comparator and decisive branch even when
they cost more than a simpler confirmation test.

For opted-in prototype design, use `participatory-workshops.md` and choose one learning decision per turn: uncertainty, lowest faithful form, participant/context, signal, or excluded scope. The facilitator may give a concrete domain example, but must not invent the user's choice.

## Ethics

Do not deceive participants about consequential decisions, data use, or risk. Wizard-of-Oz and fake-door tests require appropriate disclosure/debriefing. Avoid collecting data merely because the prototype can.

## Exit

Move to Test when the artifact is just faithful enough. Return to Ideate if prototyping exposes a narrow concept set; Define if the learning question cannot be stated without solution language; Empathize if contextual assumptions dominate.
