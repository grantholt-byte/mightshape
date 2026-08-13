# Design Council beta evaluator guide

The current private beta is tagged `v0.9.0-beta.4`. Do not call it `1.0.0` or represent it
as a public marketplace release.

## Setup

1. Give 5–10 evaluators the tagged repository/archive and the platform-specific install doc.
2. Ask them to install without a live walkthrough and record friction verbatim.
3. Use a fresh, non-confidential project. Do not include real participant data.
4. Run at least one ambiguous product idea, one straightforward code task, one Council
   round, one Inquiry Lab request, and one optional participatory exercise.

## Tasks

- “I have an excellent idea for an AI family scheduler. Let's build it.”
- “Meet the Council, then run Challenge Me on this idea.”
- “We are designing for an unfamiliar practitioner. Research the role first.”
- “Show evidence, assumptions, Design Debt, Evidence Debt, and the Build Gate.”
- “Workshop mode: show the brainstorming work as it develops, then preserve one outlier.”
- “I’m new to Design Thinking. Facilitate an assumption-mapping exercise one prompt at a
  time.” After the first prompt, try “Why are we doing this?”, “Show an example,” “Slower,”
  “Skip,” and “You take it from here.”
- “Let me collaborate on this affinity sort.” Move or rename one card, then ask to undo it.
- Start a structured exercise but do not answer the optional Watch/Collaborate/One-prompt
  choice. Confirm that useful facilitator-led work continues instead of blocking.
- “Cluster these source-linked notes into an affinity map and give me a visual artifact.”
- “Turn this multi-person handoff into a process map; mark missing transitions as unknown.”
- “Implement the explicit dark-mode issue in this repository.”

## Questions

- How hard was installation and first invocation?
- Could you explain Design Council to another person after two minutes?
- Did Council members feel like distinct humans or renamed viewpoints? Which blurred?
- Did the process preserve momentum, or did it feel obstructive? Where?
- Was Inquiry Lab's synthetic-versus-human distinction unmistakable?
- Could you tell confidence from evidence strength?
- Was the visual grammar attractive and readable without becoming noisy?
- Did the sticky notes, tape, cluster neighborhoods, outlier area, and process-map lanes feel
  playful and inviting rather than corporate? Did any decoration interfere with meaning?
- Did the visual artifact make a relationship easier to understand than the text fallback?
- Did the visible checkpoints help you inspect the method, or did any feel like token-burning narration?
- In compact mode, did Design Council avoid unnecessary workshop overhead?
- Was participation clearly optional, and did ignoring the offer allow work to continue?
- In one-prompt mode, did the facilitator explain only the immediate purpose and mindset,
  give one useful example, and ask exactly one manageable question?
- Could you switch between novice-assisted, guided, and light-touch support without losing
  evidence labels, sealed independence, or your prior contributions?
- Were your contributions preserved in your language and marked `USER_PROVIDED`, rather
  than being presented as human research or silently rewritten?
- Would you use it again? For what kind of decision?
- When did it trigger but should not have?
- When did it fail to trigger?
- Did OpenAI and Claude behavior differ in methodology or identity?

## Evidence to collect

Collect installation outcome, platform/version, anonymous task ID, evaluator ratings, and
redacted observations. Do not collect raw projects, code, model conversations, interview
transcripts, participant quotes, company names, or product ideas by default. Obtain separate
consent for any material beyond the beta evaluation itself.

Record defects as routing, humanity, independence, inquiry, provenance, UX, packaging, or
platform-parity issues. Record participation defects separately when the facilitator lectures,
asks multiple questions at once, blocks on the optional choice, invents a user answer, or leaks
new input into only part of an in-flight sealed round. Fix and rerun the relevant acceptance
case before release.

## Release-team effectiveness check

Beta feedback is not a substitute for the controlled plugin-versus-baseline benchmark. The
release team—not every evaluator—should run the documented paired harness with identical raw
prompts/model settings, isolated workspaces, counterbalanced order, and blind labels. Review
quality change together with candidate tokens and latency, including low-ambiguity routing
cases. Inspect the reported quality points gained per 1,000 additional generation tokens and
the per-case value quadrants. Outcome effectiveness is primary; exceeding the configured token
target is a resource-optimization finding, not a veto of a demonstrated quality benefit. Run both
the raw-prompt baseline and the frozen competent Design Thinking prompt-only comparator. Do not
treat a longer response, a single smoke pair, or model-judge agreement as proof of effectiveness.
See `evals/README.md`; do not use confidential project prompts.

For the subjective value that response rubrics only approximate, use the blind protocol in
`evals/benchmark/human-rating-guide.md`. Have independent raters choose which anonymized output
better improves the next decision, challenges the initial solution, expands the possibility space,
proposes the more informative experiment, changes direction when evidence changes, and preserves
momentum. Lock those ratings before revealing tokens or latency. Include scripted multi-turn
trajectories and record ratings against `evals/schema/human-paired-rating.schema.json`.
