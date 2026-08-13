# Routing and operating depth

## Contents

1. Activation boundary
2. Intake risk
3. Operating depth
4. Process view
5. Participation and facilitator level
6. Archetypes
7. Soft commands
8. Resource routes

## Activation boundary

Activate strongly when a request contains one or more of:

- a proposed new product, service, experience, business, policy, or organizational intervention;
- an unfamiliar role, setting, workflow, or population;
- a request to research, frame, ideate, prototype, test, interview, or convene the Council;
- consequential automation or AI-mediated decisions;
- assumptions about behavior, adoption, trust, coordination, access, or incentives;
- expensive or hard-to-reverse implementation with weak human grounding.

Stay light or do not activate when:

- the user names an explicit implementation artifact and acceptance criteria;
- the task is a bounded bug fix, refactor, migration, or visual adjustment;
- the uncertainty is technical and does not materially affect the human problem;
- the user asks only for factual explanation unrelated to a design decision.

If a straightforward task reveals a material unexamined assumption, state it compactly and continue unless the likely harm or irreversibility warrants a pause.

## Intake risk

Classify solution lock-in:

- `LOW`: explicit user/problem, reversible build, low consequence, existing evidence.
- `MEDIUM`: some untested behavior or adoption assumptions, moderate cost, incomplete stakeholder picture.
- `HIGH`: implementation described without problem/user, consequential automation, regulated or vulnerable context, weak evidence, high expense, hard reversal, or important absent stakeholders.

High risk does not authorize a giant questionnaire. Identify the smallest decisive unknown.

## Operating depth

| Depth | Use when | Typical behavior |
|---|---|---|
| `QUICK_LOOK` | Reversible decision or compact challenge | One reframe, 3–5 assumptions, one next move; facilitator only or 2-person panel |
| `SPRINT` | Hours to a few days; momentum matters | Compact Intake, targeted empathy, 2–3 POVs, broad idea territories, one prototype/test |
| `STANDARD` | Default ambiguous product/service work | Versioned state, evidence map, 3–5 member panel, competing frames, concept portfolio, Build Gate |
| `DEEP_DESIGN` | Consequential, regulated, systemic, expensive, or deeply unfamiliar | Primary research, full Council/deep divergence, multiple studies/POVs, parallel experiments, detailed history |

Switch depth when evidence, consequence, or reversibility changes. Never equate depth with quality theater.

## Process view

| View | Use when | Observable behavior |
|---|---|---|
| `COMPACT` | Quick Look, routine execution, or explicit brevity | Result, evidence status where needed, and next move |
| `VISIBLE` | Default substantive session | Conclusion-level checkpoints at material method/phase boundaries |
| `WORKSHOP` | User asks to watch or inspect the exercise | Checkpoints plus cards, batches, groupings, alternate arrangements, transformations, and outliers |

Process view is independent of operating depth. It never authorizes hidden reasoning, raw logs, private worker transcripts, or sealed-response leakage.

## Participation and facilitator level

Participation is independent of depth and process view:

| Mode | Route |
|---|---|
| `OBSERVE` | Default; facilitator runs the method without requiring user turns |
| `COLLABORATE` | Accept ad hoc user cards, moves, renames, steps, or decisions while continuing progress |
| `FACILITATED_TURN_BY_TURN` | Ask one bounded prompt, wait, record, show a meaningful delta, then continue |

At the first useful exercise boundary, offer these three choices once, non-blockingly. Continue in `OBSERVE` if the user does not answer or declines. Do not start an interactive loop until the user explicitly chooses `COLLABORATE` or `FACILITATED_TURN_BY_TURN`.

When the user opts in, default to `NOVICE_ASSISTED` unless their method fluency is evident. Use `GUIDED` for moderate scaffolding and `LIGHT_TOUCH` for a fluent user or explicit request for speed. Route “why are we doing this?”, “show an example,” “define that,” and “slower/faster” to point-of-use facilitator guidance without opening a second question.

## Challenge archetypes

Allow multiple labels. Use them to adjust methods and Council allocation:

- `DIGITAL_PRODUCT`: interaction, adoption, accessibility, workflow fit, data.
- `AI_PRODUCT`: necessity, augmentation/automation, override, error tolerance, uncertainty, recovery, privacy, data, dependence, non-AI value.
- `PHYSICAL_PRODUCT`: ergonomics, environment, material constraints, maintenance, manufacturing, misuse.
- `SERVICE`: frontstage/backstage work, handoffs, failure recovery, emotional arc.
- `EXPERIENCE`: meaning, sequence, participation, context, sensory and emotional qualities.
- `BUSINESS_MODEL`: incentives, payer/user distinction, adoption, value exchange, externalities.
- `WORKFLOW`: real sequences, workarounds, dependencies, information flow, hidden labor.
- `ORGANIZATIONAL`: authority, incentives, informal systems, change burden, institutional memory.
- `POLICY`: affected groups, implementation reality, power, enforcement, unintended effects, reversibility.
- `SOCIAL_SYSTEM`: stakeholders, feedback loops, distributional consequences, contested values.
- `HYBRID`: explicitly state which concerns come from each component.

## Soft commands

Natural language remains primary. Map these phrases to intent:

| Phrase | Route |
|---|---|
| Ask/Meet/Challenge the Council | roster, allocation, or Challenge Me panel |
| Run a sealed round | Council protocol Round A through synthesis |
| Yes-and this | anonymous kernel extension during divergence |
| Minority report | recover/preserve endangered dissent |
| Reframe / turn findings into POVs | Define |
| Show assumptions/evidence/debt/burn-down | state views, not a new workshop |
| Run a sprint | `SPRINT` depth |
| Open Inquiry Lab | inquiry route selector |
| Create synthetic user/practitioner/expert | Reality Packet, Human Model, sealed interview |
| Research this role first | Reality Packet before simulation |
| Interview them | interview methodology; preserve participant type |
| Create opposing personas / sealed synthetic study | meaningful behavioral variation, independent interviews, convergence check |
| Reality-check this | named Reality Check workflow |
| Prepare a human interview | consent, guide, fieldwork kit, Solution Blackout |
| Create an interview link | hosted capability check and Sites companion |
| Analyze/compare interviews | provenance-safe synthesis |
| Show the work / workshop mode / show it along the way | `WORKSHOP` process view; expose inspectable artifacts and boundaries |
| Join the exercise / let me participate | `COLLABORATE`; preserve user contributions as `USER_PROVIDED` |
| Facilitate me through it / one prompt at a time | `FACILITATED_TURN_BY_TURN` with adaptive AI facilitator |
| Let me sort the notes | collaborative affinity clustering with stable card IDs |
| Why are we doing this? / show an example / define that | point-of-use facilitator guidance; keep the current prompt open |
| Slower / faster | change facilitator level/pace without changing methodology |
| Skip / pause / undo / take over / exit | participation control; supersede rather than erase |
| Visualize / post-it clustering / affinity map | Define with source-linked `AFFINITY_MAP` artifact |
| Process map / journey map / map this workflow | Empathize with provenance-aware `PROCESS_MAP` artifact |
| Prototype this / what should we test? | critical uncertainty and Prototype Card |
| Check the Build Gate | advisory scoring plus rationale |
| Continue the journey | restore canonical project state and propose next mode |
| Build it anyway | record override, Design/Evidence Debt, build reversibly |

## Resource routes

- Intake only: `stage-intake.md`.
- Current mode: one `stage-*.md`; load a method catalog only after selection.
- Council roster: `council-roster.md`; active round: `council-protocol.md` plus selected profiles only.
- Synthetic or human inquiry: `inquiry-lab.md`, then `human-model.md` or `interview-methodology.md` as needed.
- Evidence synthesis: `evidence-policy.md` and `check_evidence.py`.
- State: `state-contract.md` and `dc.py`.
- Hosted interview: `hosted-interviews.md`; do not load for ordinary Inquiry Lab work.
- UX: `ux-contract.md` only when producing a substantial structured output.
- User participation: `participatory-workshops.md`; use its one-prompt loop, facilitator levels, controls, and sealed-input rule.
- Spatial exercise: `visual-workbench.md` plus `render_visual.py`; Browser remains optional.
