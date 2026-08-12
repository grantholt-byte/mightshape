# OpenAI submission test cases

Use the current portal's exact form fields. These eight concise cases are drawn from the
larger versioned corpus in `evals/cases/`.

## Positive

1. **Solution-first Intake** — “I have an excellent idea for an AI app that automatically
   coordinates family schedules. Let's build it.” Expected: preserve momentum; treat the
   app as a proposed solution; label assumptions/unknowns; recommend a cheap learning path.
2. **Council** — “Run a sealed Council round on this service concept.” Expected: identical
   packet, independent workers, freeze before anonymous cross-pollination, Minority Report.
3. **Inquiry Lab** — “We are designing for emergency nurses and do not understand their
   workflow.” Expected: research and Reality Packet before synthetic practitioner; local
   variation; synthetic provenance; questions for real humans.
4. **Prototype** — “Prototype this.” Expected: identify critical uncertainty, lowest useful
   fidelity, success/failure signals, participants, and explicit `DO NOT BUILD` list.
5. **Build override** — “The Build Gate says TEST_FIRST. Build it anyway.” Expected: obey,
   preserve open assumptions, record Design/Evidence Debt, keep implementation reversible.

## Negative / inappropriate trigger

1. “Implement the dark-mode toggle exactly as specified in issue.md.” Expected: do the
   explicit coding work without a workshop.
2. “Format this JSON file.” Expected: no Council, Intake, or Inquiry ceremony.
3. “Delete generated build artifacts.” Expected: normal scoped engineering behavior;
   Design Council should not trigger solely because the word “design” appears elsewhere.

The submission evaluator should see only observable expected behavior. It should never be
asked to infer hidden chain-of-thought.
