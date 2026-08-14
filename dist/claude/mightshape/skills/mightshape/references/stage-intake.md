# Intake — MightShape orchestration

Intake is MightShape's own orchestration layer, not one of the five design thinking modes. It preserves momentum while identifying whether the request needs facilitation, research, a prototype, or straightforward execution.

## Compact extraction

From the user's own words, draft rather than interrogate:

- **Proposed solution:** the artifact/intervention already imagined.
- **Implied user:** who experiences value, burden, or change.
- **Implied problem:** what the solution is assumed to address.
- **Desired outcome:** the human or system change, not delivery of the artifact.
- **Evidence:** with provenance; user claims remain `USER_PROVIDED`.
- **Assumptions:** what must be true for the proposal to work.
- **Unknowns:** what could materially change the frame or intervention.
- **Constraints:** time, money, policy, environment, access, capability.
- **Reversibility:** easy, moderate, or difficult to undo.
- **Cost of being wrong:** human, financial, operational, institutional, safety, or opportunity cost.
- **Solution lock-in:** `LOW`, `MEDIUM`, or `HIGH`, with reasons.

## Response pattern

1. Infer the starting point and current decision from the user's words when possible: `EARLY_HUNCH`, `GROUNDED_EXPLORATION`, `FRAMED_CHALLENGE`, `CONCEPT`, `PROTOTYPE`, `LIVE`, or `UNSURE`. Record whether it was `USER_DECLARED` or `INFERRED`; never confuse it with the current mode. For a sustained project, persist it with `python3 <skill>/scripts/dc.py orient --project-root <root> --starting-point <value> --basis <value> [--current-decision <decision>]`; omitting the decision preserves any existing focus.
2. Acknowledge the useful energy or intent without endorsing untested claims.
3. Recast a proposal as a candidate solution when relevant.
4. Show no more than five pivotal assumptions/unknowns.
5. Choose depth and the smallest next move from the current decision—not from a requirement to start at Empathize.
6. Ask at most one high-yield question when the answer would change the route. If explicit invocation supplies no usable context, ask which plain-language starting point best fits and include “not sure”; otherwise infer and proceed without a redundant question.

For a `LIVE` product or service, name the current strategic fork before proposing another surface.
Separate the outcome people need from the locus of the intervention: the product may need to become
the destination, bridge into an accepted venue, support a private/incumbent mode, or change a role or
process. Existing maturity and evidence narrow the inquiry; they do not make one locus inevitable.

Example high-yield question: “Tell me about the last real incident that made you want this—what happened, who was involved, and what did they do next?”

## Do not be obstructive

Proceed directly when requirements are explicit and risk is low. Do not validate universal/common-sense premises for ceremony. If the user explicitly wants brainstorming and supplies demand claims, label them `USER_PROVIDED`, honor protected divergence, and avoid turning the turn into a research lecture.

## AI-product Intake

Add these checks only when relevant:

- Is AI necessary, or can a rule, workflow, interface, or human service create the value?
- Is the goal augmentation, recommendation, delegation, or full automation?
- Who can override, appeal, recover, or understand uncertainty?
- What errors are tolerable; which are not?
- What data exists, who controls it, and how representative/reliable is it?
- What happens when the model is wrong, unavailable, or confidently ambiguous?
- Does the product create dependence or deskilling?
- What remains valuable when AI is removed?

## Transition

Starting point does not dictate transition. A live product may return to Empathize or Define; an early hunch may move directly to a low-fidelity Prototype when making is the cheapest inquiry.

- To `EMPATHIZE` when behavior, context, stakeholders, or workflow is insufficiently known.
- To `DEFINE` when grounded evidence exists but the frame is weak or contested.
- To `IDEATE` when a strong solution-independent POV exists and breadth is missing.
- To `PROTOTYPE` when a candidate concept exists and making is the cheapest inquiry.
- To `TEST` when a learning artifact already exists.
- To ordinary implementation when the request is explicit and no material design uncertainty remains.
