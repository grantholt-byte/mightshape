# Empathize mode

## Goal

Understand people's actual contexts, behaviors, stories, workarounds, relationships, and meanings before reducing them to a problem statement. Empathy is disciplined inquiry, not imagining what a demographic would think.

## Entry signals

- unfamiliar role, environment, or workflow;
- proposed solution with thin human grounding;
- contradictions between stated needs and observed behavior;
- consequential behavior/adoption assumptions;
- missing stakeholders or local context;
- synthetic hypothesis that requires human reality checking.

## Choose the smallest useful method set

- Begin with `Beginner's Mindset` and `What? How? Why?` when assumptions are embedded in observations.
- Use `Interview Preparation` and `Interview for Empathy` for stories and behavior reconstruction.
- Use `Contextual Inquiry` or `Observation` when workflow, tools, sequence, interruption, and workarounds matter.
- Use `Immersion` for first-person exposure to constraints, while explicitly rejecting equivalence with another person's lived experience.
- Use `Extreme Users` to expose amplified needs and adaptations; do not generalize prevalence.
- Use `Journey Mapping` for sequences, channels, emotions, handoffs, and breakdowns.
- Use `Stakeholder Mapping` for power, relationships, dependencies, beneficiaries, and burden.
- Use `Story Share and Capture` to make evidence inspectable across a team.
- Use `Analogous Experiences` to investigate mechanisms in distant settings.
- Use `Assumption Mapping` to prioritize what to learn.
- Open Inquiry Lab when direct access is limited, domain grounding is needed, or synthetic-to-human sequencing will improve research.

Run `select_methods.py --mode EMPATHIZE ...` for consistent narrowing.

If the user opts into process reconstruction, assumption mapping, or journey work, follow `participatory-workshops.md`. Use an adaptive facilitator and one bounded prompt at a time: one actual step/handoff, one unknown transition, or one assumption placement. Preserve each contribution as `USER_PROVIDED`; it describes what the user supplied and does not become observed human behavior.

For an evidence-linked workflow or journey, use `render_visual.py` to create a `PROCESS_MAP` when sequence, ownership, breakdowns, or unknown branches are materially easier to inspect spatially. Preserve provenance at every step and mark assumed or missing transitions explicitly. Always provide the Markdown fallback; do not invent a complete path to make the picture tidy.

## Research plan

Specify:

```yaml
decision_to_inform: string
learning_questions: []
participants_or_contexts: []
variation_dimensions: []
methods: []
solution_blackout: true
data_to_collect: []
consent_and_privacy: {}
analysis_plan: string
stop_condition: string
known_limits: []
```

Prefer actual human context when a material decision depends on behavior. Synthetic inquiry can improve questions and reveal hypotheses; it cannot replace human evidence.

## Capture

Keep observations, direct quotes, researcher interpretations, and design implications separate. Note sequence, environment, tools, interruptions, handoffs, workarounds, emotional peaks, contradictions, and negative cases. Record participant IDs and traceable excerpts only under the consent policy.

## Exit criteria

Move toward Define when there is enough situated material to identify patterns and tensions without inventing them. “Enough” is proportional to the decision; it is not a fixed participant count. Carry local variation and unanswered questions forward.
