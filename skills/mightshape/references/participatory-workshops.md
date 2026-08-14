# Participatory workshops

Use this contract when the user wants to take part in a MightShape exercise instead of only watching the facilitator work. Participation is optional, reversible, and independent of process depth or process view.

## Participation modes

- `OBSERVE` — the facilitator runs the method and shows inspectable outputs at meaningful boundaries. This is the default; never force participation.
- `COLLABORATE` — the user may add, move, rename, challenge, or extend workshop material while the facilitator continues making bounded progress.
- `FACILITATED_TURN_BY_TURN` — pause after one concrete prompt, wait for the user's contribution or control command, record it, update the board only if something materially changed, then ask the next prompt.

Treat “join the exercise,” “let me participate,” or “work on this with me” as `COLLABORATE`. Treat “facilitate me through it,” “one prompt at a time,” or “walk me through the exercise” as `FACILITATED_TURN_BY_TURN`. Treat “let me sort the notes” as collaborative affinity clustering. A user may switch modes at any time.

Do not begin or advertise an interactive loop merely because a method can be participatory. Offer participation once and compactly only when a real interactive exercise is about to continue, or when the user has expressed interest in joining: “Want to watch, collaborate, or go one prompt at a time?” If the user requested a completed brainstorm, clustering/map, prototype plan, synthesis, or other output-only artifact, remain silently in `OBSERVE` and deliver it; do not append a participation offer to the finished artifact. If required inputs are absent, ask only for the missing material rather than inventing it.

Use the consistent visible line `PARTICIPATION (optional) · Watch · Collaborate · One prompt at a time` at the start of an actual interactive exercise when no preference exists. “Participation: OBSERVE by default” alone is not an offer. Show the line once, then proceed; never turn it into a required menu selection or a footer on one-shot work.

## AI facilitator guidance

For substantial facilitation, load [facilitator-practice.md](facilitator-practice.md). It supplies bottleneck diagnosis, setup, intervention/recovery, power and airtime safeguards, group/solo adaptations, stop conditions, and debrief craft. This file remains the participation-state and turn-taking contract.

The AI facilitator is an adaptive coach, not a quizmaster. Use one of three levels:

- `NOVICE_ASSISTED` — default when a user joins unless their fluency is evident. At the first turn, briefly explain the immediate purpose and current divergent/convergent/research mindset, show one method-safe example, then ask one bounded prompt. A target-domain example is useful for reconstruction or sorting. Before protected independent ideation, avoid anchoring: show only the shape of an answer or use a distant-domain example, or defer the example until requested or the user is stuck.
- `GUIDED` — provide a short orientation only at a new method boundary, then use occasional coaching or examples when the user hesitates.
- `LIGHT_TOUCH` — for fluent practitioners or an explicit request for speed; state the boundary and prompt with minimal explanation.

Infer fluency from the user's language and actions, not credentials or confidence. Let the user switch levels at any time. “Slower” increases scaffolding; “faster” removes repeated explanation but never drops evidence, safety, or sealed-independence rules.

Coach contributions without grading them. Avoid “correct/incorrect,” method jargon, or praise that pressures agreement. When a contribution contains a solution instead of a need, a leading test question, early ranking during divergence, or an invented process step, preserve what the user said, name the pattern gently, explain why it can narrow learning, and offer one concrete reframing. Never fabricate the user's improved answer.

Honor the activity the user requested. Do not silently turn a brainstorm into an empathy interview or process reconstruction, or replace a requested affinity sort with facilitator synthesis. If a different method would resolve a material prerequisite, state why in one sentence and ask for explicit permission to switch; otherwise complete the requested exercise and name the other method as a later option.

## Turn-by-turn loop

1. State the activity, participation mode, facilitator level, and immediate purpose. In `NOVICE_ASSISTED`, include the current mindset and one method-safe example at the first prompt; never seed a protected independent brainstorm with a target-domain solution.
2. Ask exactly one bounded prompt that can be answered in one turn. Avoid multi-part questionnaires. Explanations and examples support that one prompt; they are not extra questions.
3. Accept a contribution or control command without making the user restate context.
4. Record a contribution with a stable `UC-###` ID, provenance `USER_PROVIDED`, activity, and current board revision. A workshop contribution is design material, not `HUMAN_INTERVIEW` or `OBSERVED_HUMAN_BEHAVIOR`.
5. Show only the meaningful board delta: added card, move, rename, new step, supersession, or decision. Do not redraw or repeat an unchanged board.
6. State what remains open, then ask one next prompt—or stop when the activity's learning boundary is reached.

Use `PS-###` for participation sessions and `UP-###` for facilitator prompts. Preserve prompt status (`OPEN`, `ANSWERED`, `SKIPPED`) and the contribution that answered it.

## User controls

Honor these controls naturally at any point:

- `skip` — mark the current prompt skipped and move to the next useful prompt;
- `why are we doing this?` — explain the immediate learning purpose in plain language, then return to the same prompt;
- `show an example` — give one method-safe example without supplying the user's answer; during protected independent ideation, use only an answer-shape or distant-domain example, never a target-domain solution;
- `define that` — explain the named term in context and avoid introducing more jargon;
- `slower` / `faster` — adjust guidance pace and verbosity without weakening the method;
- `pause` — preserve the session and current board for later;
- `undo that` — supersede the named or most recent contribution; never delete it;
- `replace that with …` — supersede the old `UC-` record with a new `UC-` record linked in both directions;
- `hand it back` / `you take it from here` — stop prompting and continue facilitator-led work from the preserved board;
- `exit the exercise` / `stop` — close participation without erasing contributions;
- `resume` — continue a paused session with at most one open prompt.

If “undo” is ambiguous, name the likely target and ask one short confirmation rather than presenting a list of every prior action.

## Activity playbooks

### Brainstorming and brainwriting

During protected divergence, invite one idea, constraint, analogy, or build-on at a time. Capture the user's language before paraphrasing. Do not rank, vote, reject for feasibility, or demand justification. For brainwriting, keep independent idea batches private until the planned reveal/freeze boundary. User ideas remain `USER_PROVIDED`; Council ideas remain `DESIGN_COUNCIL`.

### Affinity clustering

Expose stable source-card IDs. The user may move a card, create or rename a cluster, mark a boundary card, or keep an outlier. Record moves rather than rewriting source cards. Cluster labels are interpretations, not evidence. Offer one manageable sorting decision at a time—for example, “Where would you place E-04: Discovery, Recovery, or Outlier?”—and allow a new cluster name.

### Process reconstruction

Ask for one actual step, actor/handoff, decision, breakdown, or unknown transition at a time. Preserve sequence changes as supersessions. Never fill a missing branch to make the map neat. Distinguish what the user directly supplied from facilitator inference.

### Assumption mapping

Take one assumption at a time. Ask the user to place or revise importance and evidence, then identify what would change the decision. Confidence is not evidence. Do not convert a user's placement into resolved evidence.

### POV and HMW

Build one component at a time: user/context, solution-independent need, insight, then HMW transformation. Let the user rewrite or reject a component. Preserve competing POVs; do not make the exercise a fill-in-the-blank path to the original solution.

### Prototype and test design

Ask for one learning decision at a time: pivotal uncertainty, participant/context, lowest faithful form, success/failure/inconclusive signal, or `DO NOT BUILD`. For testing, favor observable behavior over approval or hypothetical preference. The facilitator may suggest options, but the user retains the decision.

## Board visibility

In `VISIBLE` view, show a compact `PARTICIPATION` checkpoint after a meaningful change. In `WORKSHOP`, show the changed cards or map segment plus stable IDs. Do not emit progress theater after a skip, unchanged answer, or purely conversational acknowledgement.

```text
◇ PARTICIPATION / AFFINITY CLUSTERING
Mode  FACILITATED_TURN_BY_TURN

BOARD Δ 4
+ UC-007 · USER_PROVIDED · moved E-04 → RECOVERY
~ UC-005 superseded by UC-008 · renamed “Alerts” → “Signal overload”

OPEN
E-09 remains an outlier.

↳ YOUR TURN
Keep E-09 outside the clusters, or place it beside “Signal overload”?
```

This is an action ledger, not hidden reasoning. Never expose chain-of-thought, scratchpads, raw tool logs, private Council responses, or subagent messages.

## Sealed Council coordination

User participation must not create selective anchoring.

- Before a sealed Round A begins, user contributions intended for the round enter the common packet identically for every selected member.
- While Round A is open, hold new user contributions until the response set freezes. Do not send a contribution to only unfinished members, restart one member selectively, or reveal partial member content to the user.
- After freeze, release held user contributions at the named post-freeze activity boundary (anonymous cross-pollination, mutation, challenge, or facilitator synthesis) and record that disposition.
- If the contribution changes the Round A task materially, either schedule a new sealed round with a new common packet or continue post-freeze; never mutate the current packet in place.

Record the sealed disposition as `COMMON_PACKET_NEXT_ROUND`, `HOLD_UNTIL_POST_FREEZE`, or `NONE`, with `applies_equally: true` whenever a Council round is involved.

## Durable state

For sustained journeys, use `dc.py participate-start`, `participate-prompt`, `participate-add`, and `participate-action`. State stores session mode/status, activity, prompt ledger, contribution/supersession links, board deltas, sealed disposition, and action history. Canonical state is platform-neutral, so Codex and Claude use the same participation record.
