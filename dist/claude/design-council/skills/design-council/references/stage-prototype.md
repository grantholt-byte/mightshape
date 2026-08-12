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

## Ethics

Do not deceive participants about consequential decisions, data use, or risk. Wizard-of-Oz and fake-door tests require appropriate disclosure/debriefing. Avoid collecting data merely because the prototype can.

## Exit

Move to Test when the artifact is just faithful enough. Return to Ideate if prototyping exposes a narrow concept set; Define if the learning question cannot be stated without solution language; Empathize if contextual assumptions dominate.
