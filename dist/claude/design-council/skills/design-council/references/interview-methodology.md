# Interview methodology and coach

## Story-first interviewing

Prefer reconstructed events over preferences:

- “Tell me about the last time…”
- “What happened next?”
- “Where did you look first?”
- “What did you do when that did not work?”
- “Who else became involved?”
- “Can you walk me through what you saw and did?”
- “You said X, but the sequence suggests Y—help me understand that.”

Follow concrete nouns, time markers, emotional shifts, workarounds, and contradictions. Use silence. Ask one question at a time. Do not exhaust a topic list mechanically when a story reveals a better follow-up.

## Adaptive interviewer state

Maintain:

```yaml
research_goal: string
topics_to_cover: []
covered_topics: []
emerging_threads: []
adaptive_follow_up_priorities: []
solution_blackout: true
concept_reveal_reason: null
stop_conditions: []
privacy_configuration: {}
```

After each answer, update coverage and choose the highest-learning follow-up. Cover required topics naturally before stopping. Stop on participant request, distress, duration, explicit study condition, or adequate coverage.

## Solution Blackout and Concept Reveal

Under `SOLUTION BLACKOUT`, do not disclose, describe, or imply the proposed intervention in introductions, questions, examples, or response options. Study current behavior, environment, goals, breakdowns, and workarounds.

Switch to `CONCEPT REVEAL` only when concept/prototype testing is the declared research goal or exploratory coverage is complete and disclosure is justified. Record when and why the switch occurred so pre- and post-reveal evidence cannot be conflated.

## Interview Coach detectors

- **Leading:** implies a desired answer (“Wouldn't AI make this easier?”).
- **Compound:** asks multiple things at once (“How do you plan and how does your partner react?”).
- **Hypothetical preference:** asks what someone would do rather than what happened.
- **Solution biased:** embeds an artifact or mechanism before the current problem is understood.
- **Excessively abstract:** invites general philosophy without concrete events (“How do you feel about coordination?”).

Coach without blocking:

```text
△ LEADING QUESTION
This embeds the preferred answer.
Try: “Tell me about the last time this part became difficult.”
```

Use `detect_leading_questions.py` for consistent flags. Let the researcher continue if they choose.

## Human interview disclosure

Before data collection put literal participant-facing language at the top of the script stating the AI identity, purpose, approximate duration, collected information, reviewer audience, recording and quotation policy, skip/stop rights, and applicable contact/deletion path. Never leave these as placeholders or researcher-only notes. Get affirmative consent. Default to `P-###`; avoid name/email unless necessary.

## Analysis cautions

Do not infer prevalence, demographic causality, or market size from a small qualitative sample. Preserve negative cases. Separate the participant's words from interviewer interpretation and later design implication. Note leading prompts, concept contamination, and missing contexts as limitations.
