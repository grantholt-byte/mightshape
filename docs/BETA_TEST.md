# Design Council beta evaluator guide

Use a tagged prerelease such as `0.9.0-beta.1` if testing occurs before the owner accepts
the production release. Do not call an unvalidated package `1.0.0` in public.

## Setup

1. Give 5–10 evaluators the tagged repository/archive and the platform-specific install doc.
2. Ask them to install without a live walkthrough and record friction verbatim.
3. Use a fresh, non-confidential project. Do not include real participant data.
4. Run at least one ambiguous product idea, one straightforward code task, one Council
   round, and one Inquiry Lab request.

## Tasks

- “I have an excellent idea for an AI family scheduler. Let's build it.”
- “Meet the Council, then run Challenge Me on this idea.”
- “We are designing for an unfamiliar practitioner. Research the role first.”
- “Show evidence, assumptions, Design Debt, Evidence Debt, and the Build Gate.”
- “Implement the explicit dark-mode issue in this repository.”

## Questions

- How hard was installation and first invocation?
- Could you explain Design Council to another person after two minutes?
- Did Council members feel like distinct humans or renamed viewpoints? Which blurred?
- Did the process preserve momentum, or did it feel obstructive? Where?
- Was Inquiry Lab's synthetic-versus-human distinction unmistakable?
- Could you tell confidence from evidence strength?
- Was the visual grammar attractive and readable without becoming noisy?
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
platform-parity issues. Fix and rerun the relevant acceptance case before release.
