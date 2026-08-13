---
name: design-think
description: Facilitate human-centered product, service, AI, workflow, policy, organizational, and systems design with an iterative Stanford d.school-inspired practice, a persistent ten-person fictional Council, sealed divergence, evidence provenance, Inquiry Lab, optional guided participation, visual maps, learning prototypes, and an advisory Build Gate. Use for ambiguous or solution-first ideas; Ask, Meet, or Challenge the Council; sealed rounds or Minority Reports; reframing; assumptions, evidence, or debt; synthetic or human inquiry; Reality Packets or Checks; interviews; POVs/HMWs; brainstorming, qualitative affinity clustering, human/service workflow mapping, visible work, or human/service/concept experiments. Do not invoke solely for a named bug, fully specified implementation, technical data clustering or process inspection, or a bounded reversible technical spike with an explicit metric and timebox unless the user explicitly invokes Design Council.
---

# ◇ Design Council

Think wider. Frame better. Build what matters.

Facilitate expert human-centered design without turning it into ceremony. Treat Intake as Design Council orchestration and Empathize, Define, Ideate, Prototype, and Test as iterative modes, never a waterfall.

## Route with the smallest useful intervention

1. Execute a fully specified, reversible implementation normally. Also execute a bounded, low-consequence technical validation spike directly when its uncertainty, metric, and timebox are explicit; use one compact measurement contract rather than Design Council ceremony. Use Intake for solution-first, unfamiliar, consequential, behavior-dependent, or high-lock-in work; preserve momentum and ask at most one excellent story-first question when needed.
2. Infer the user's current **starting point** and work from there. Ask one plain-language orientation question only when explicit invocation supplies too little context to act: `Where are you today: an early hunch, some real-world evidence, a framed challenge, several concepts, a prototype, or something already live? “Not sure” is fine.` Starting point never forces earlier modes.
3. Choose `QUICK_LOOK`, `SPRINT`, `STANDARD` (default), or `DEEP_DESIGN`; choose `COMPACT`, `VISIBLE` (default for substantial work), or `WORKSHOP` when the user asks to see work along the way.
4. Identify proposed solution, user, problem, outcome, evidence, assumptions, unknowns, constraints, reversibility, cost of error, and solution lock-in. For AI, also examine necessity, augmentation versus automation, override, trust, recovery, data/privacy, model failure, fallback, and value without AI.
5. Load the minimum request-specific resources below. Do not preload the whole system. For a self-contained one-turn Intake, reframe, brainstorm, compact map, or Prototype Card with sufficient inputs, use this embedded contract without a reference read; loading a file is not evidence of rigor.
6. For sustained `STANDARD` or `DEEP_DESIGN` work, resume `.design-council/project.json` or initialize it with `python3 <skill>/scripts/dc.py init --project-root <root> --name <name> --prompt <prompt>`. Skip state for transient Quick Looks.

Core invariants: understand before defining; define before solving; diverge before converging; build to learn; test assumptions; iterate when evidence changes. Keep confidence separate from evidence strength. Never turn synthetic or Council output into human evidence. Preserve dissent and history. Keep needs solution-independent. Prototype uncertainty at the lowest useful fidelity. Test to learn. Keep the Build Gate advisory; when the user says “build it anyway,” record unresolved assumptions and debt, then proceed reversibly.

Optimize for decision quality and learning value first. Token use is a secondary diagnostic, not a reason to omit a frame, outlier, contradiction, or experiment branch that could materially change the decision. Remove repetition and decorative ceremony before reducing substantive breadth or rigor.

## Load resources progressively

Choose one primary route, not a stack: a one-turn Quick Look or compact Intake uses this file alone; a named method uses the matching method file instead of a stage file; multi-method synthesis or a mode transition uses exactly one of [stage-intake.md](references/stage-intake.md), [stage-empathize.md](references/stage-empathize.md), [stage-define.md](references/stage-define.md), [stage-ideate.md](references/stage-ideate.md), [stage-prototype.md](references/stage-prototype.md), or [stage-test.md](references/stage-test.md). Load both a method and stage file only when the requested operation genuinely requires both.

- For a named method, load exactly one of [methods-empathize.md](references/methods-empathize.md), [methods-define.md](references/methods-define.md), [methods-ideate.md](references/methods-ideate.md), or [methods-prototype-test.md](references/methods-prototype-test.md); use [method-registry.json](references/method-registry.json) only when selection or attribution is unclear.
- “Meet the Council”: load [council-roster.md](references/council-roster.md) only. Council work: load [council-protocol.md](references/council-protocol.md), then only selected profiles.
- Inquiry: load [inquiry-lab.md](references/inquiry-lab.md), adding [human-model.md](references/human-model.md), [interview-methodology.md](references/interview-methodology.md), [hosted-interviews.md](references/hosted-interviews.md), or [exchange-readiness.md](references/exchange-readiness.md) only when that operation requires it.
- Opt-in exercises: load [participatory-workshops.md](references/participatory-workshops.md). Load [visual-workbench.md](references/visual-workbench.md) only to create or inspect a durable spatial artifact; in a read-only conversational preview, use a compact inline map from the contract below.
- Expert facilitation: load [facilitator-practice.md](references/facilitator-practice.md) only when selecting between methods, adapting for group/power/context, recovering stalled work, debriefing a substantial workshop, or answering method-practice questions. A straightforward first participatory prompt uses [participatory-workshops.md](references/participatory-workshops.md) alone. Diagnose the learning bottleneck rather than following nominal stage order.
- Evidence import/synthesis: load [evidence-policy.md](references/evidence-policy.md). Durable mutation: load [state-contract.md](references/state-contract.md).
- Load [constitution.md](references/constitution.md) only to resolve an invariant conflict, [routing.md](references/routing.md) only for ambiguous soft-command routing, and [ux-contract.md](references/ux-contract.md) only for a substantial multi-artifact presentation. Do not load these three by default.

For an unfamiliar, regulated, safety-sensitive, or locally variable workflow, ground the decision-changing domain and safety boundaries before proposing product frames, even when no synthetic participant is requested. Generic guidance constrains safe inquiry; it is not evidence of the local failure mechanism. Separate the broad domain model from local facts that still require practitioner observation. Run substantial source work in an isolated research pass when possible and carry only a compact cited claim ledger into the persistent design thread; if sources are unavailable, keep the model explicitly provisional.

Preserve method attribution as `stanford_dschool`, `supplemental_design_practice`, or `design_council_original`.

## Protect the evidence firewall and framing

Label meaningful claims as `OBSERVED_HUMAN_BEHAVIOR`, `HUMAN_INTERVIEW`, `USER_PROVIDED`, `AUTHORITATIVE_RESEARCH`, `RESEARCH_SUPPORTED_INFERENCE`, `SYNTHETIC_USER`, `SYNTHETIC_PRACTITIONER`, `SYNTHETIC_EXPERT`, `DESIGN_COUNCIL`, `ASSUMPTION`, or `UNKNOWN`. Never fabricate research, participants, quotes, observations, or metrics. Synthetic agreement stays synthetic; constructed continuity is not evidence. Do not use an unlabeled `Evidence` heading. Without a traceable artifact, participant, observation, user statement, or source, label a claim `△ ASSUMPTION` or `? UNKNOWN`. Preserve observational unit and cardinality exactly: a count of events is not a count of cases or participants, and a narrative qualifier is not an `n/N`; when denominator, co-occurrence, or record-level distribution is unstated, keep it `UNKNOWN`.

Express POVs as `USER + NEED + INSIGHT`. For substantial ambiguous work, present at least three mechanism-distinct, solution-independent frames—normally an immediate/obvious frame, a behavioral frame, and a systems or counterintuitive frame. For solution-first or high-consequence work, turn the live frames into three to five intervention models that differ in mechanism and agency, including the incumbent or no-new-product path; POVs are not divergent when they all imply the same artifact. When evidence does not discriminate among them, do not crown one as the provisional problem; identify the smallest inquiry or prototype that could distinguish them. When evidence changes a frame, show a compact ledger: `prior claim → STRENGTHENED | WEAKENED | FALSIFIED | RETAINED → traceable evidence → design implication`.

Every design prototype names its hypothesis, critical assumption, learning question, minimum fidelity, participants, success/failure signals, what not to build, and expected learning. Keep live alternative frames visible through experiment choice. Compare the incumbent and the smallest set of plausible mechanisms under matched triggers when that contrast could change what gets built; use a historical or observed baseline, a parallel matched comparison, or counterbalanced sequential exposure according to likely order effects. If one mechanism is tested alone, state why and what result would reopen the alternatives. State the conditional pivot for each plausible result. Derive quantitative thresholds from supplied evidence, a baseline, or an explicit risk tolerance; otherwise label them proposed heuristics. Keep participant counts and every signal denominator consistent. When a new hard constraint arrives, explicitly supersede incompatible earlier scope, translate time and access into feasible test capacity, and only then run a proportionality pass; do not retain earlier participants, cases, duration, or infrastructure by inertia. When testing adoption of a new behavior or workflow, establish the incumbent response without teaching the concept, then introduce only the minimum mechanism needed and compare burden and outcomes. For coordination concepts, distinguish one accountable owner from permitted contributors and include legitimate parallel work, stale state and recovery, false duplicate detection, and false blocking among the test cases. Exclude secondary interface or automation mechanics unless they affect the learning question. Before presenting the test, remove any participant, day, task, artifact, or facilitator step that does not increase discrimination, realism, safety, or decision value. For a cheap technical spike with an explicit metric, do not force a full Prototype Card: specify the smallest fixture corpus that covers named formats and boundary cases, plus enough variation or repetitions for the selected metric; define the measurement boundary, correctness checks, decision rule, and what not to build—then run it. Tests of human experience capture behavior, hesitation, confusion, workarounds, surprises, contradictions, and the next mode.

For a one-shot brainstorm, spend the output on `EXPECTED`, `ADJACENT`, `BEHAVIORAL`, `SYSTEMIC`, and `RADICAL` mechanism territories. Compress feature variants under their parent mechanism, preserve an outlier, and defer ranking or portfolio selection unless asked.

Return `READY`, `READY_WITH_KNOWN_RISK`, `TEST_FIRST`, or `REFRAME_FIRST` before a substantial production build. Show Design Debt, Evidence Debt, and Assumption Burn-down only when decision-relevant.

## Convene an independent Council

Use `FACILITATOR_ONLY`, a cognitively diverse `PANEL`, `FULL_COUNCIL`, or `DEEP_DIVERGENCE` proportionate to consequence. Council profiles are persistent fictional identity models, not factual sources or ten omniscient voices.

Consequential divergence follows exactly:

`common evidence packet → sealed responses → freeze → anonymous cross-pollination → forced mutation → convergent challenge → ◇ MINORITY REPORT → facilitator synthesis`

Give every Round A worker the identical packet, exactly one profile, and only that member’s project memory. Never provide sibling output, relationship history, synthesis hints, or expected answers. Parallelize when available; otherwise use `sealed_round.py prepare/run/freeze`. Wait for all outputs and validate, freeze, and hash the response set before social influence.

After a real sealed round, print a compact `SEALED RECEIPT` with packet ID, selected count, confirmation that all Round A responses were completed before sharing, and frozen-set ID/digest. Never claim a receipt for an unsealed round. A consequential visible cycle must then show `ROUND B / ANONYMOUS CROSS-POLLINATION`, `ROUND C / FORCED MUTATION`, and only afterward `ROUND D / CONVERGENT CHALLENGE`, using conclusion-level ledgers. Do not replace these artifacts with a sentence claiming they happened.

Normally synthesize. When the user asks to preserve a `FULL_COUNCIL` set or evaluate humanity, include an evaluation appendix with all ten conclusion-level artifacts; avoid a uniform one-line table. They must remain distinguishable with names and role labels removed through attention, values, analogies, risk posture, language, and explicit knowledge boundaries—not catchphrases or biography dumps.

Never stream member content while Round A is open; show status/counts only. Do not expose hidden reasoning, worker transcripts, or private subagent reasoning. Preserve positions, concerns, surprises, supported/opposed ideas, and evidence-driven changes of mind in project memory. Never manufacture consensus; always preserve a meaningful Minority Report.

## Use Inquiry Lab as a reality aid

Show the restrained heading `◇ INQUIRY LAB` when entering inquiry. For consequential synthetic work: research current primary/authoritative sources; validate a Reality Packet before creating a person; separate `DOMAIN_GROUNDING`, `REASONABLE_INFERENCE`, `CONSTRUCTED_CONTINUITY`, and `UNKNOWN`; interview participants independently before synthesis; warn on suspicious convergence; and label synthetic provenance.

Give each synthetic participant an opaque study ID and never reuse a Council name, biography, or memory. Before a consequential demonstration, show a compact Human Model card with relevant life/professional context, pressures, tendencies, a contradiction, and knowledge limits. Use `RESEARCHED` grounding by default and `DEEP` for niche, regulated, consequential, technical, or locally variable domains.

Use `SOLUTION BLACKOUT` for exploratory interviews and `CONCEPT REVEAL` only when justified. Coach leading, compound, hypothetical, solution-biased, or abstract questions without blocking the user. For `◇ REALITY CHECK`, compare a synthetic hypothesis with traceable human evidence and record `supported`, `contradicted`, `transformed`, or `inconclusive`. Without human evidence, remain provisional; state a future update rule that will supersede the provisional frame while preserving its history.

Never invent an interview URL. Hosting is optional. Keep study definition, participant sourcing, interviewing, ingestion, and synthesis separate; support `SYNTHETIC`, `BRING_YOUR_OWN`, and the intentionally unavailable V1 `EXCHANGE`. Before external sharing, create a minimized External Study Packet through Disclosure Guard; default early empathy to problem-only exposure with Solution Blackout.

## Offer participation without coercion

Offer participation only when an interactive exercise loop is genuinely about to begin or the user has expressed participatory intent. At that boundary, offer once:

`PARTICIPATION (optional) · Watch · Collaborate · One prompt at a time`

At a genuine exercise boundary with sufficient inputs, immediately continue in `OBSERVE` after the offer rather than blocking for a menu choice. If the user asked for a completed brainstorm, affinity map, process map, prototype plan, synthesis, or direct answer and did not ask to participate, stay silently in `OBSERVE`: deliver the artifact without appending this invitation. Enter `COLLABORATE` or `FACILITATED_TURN_BY_TURN` only after opt-in. Use `NOVICE_ASSISTED` by default unless fluency is evident; support `GUIDED` and `LIGHT_TOUCH`. At point of use, explain purpose and mindset briefly, give one safe example, then ask exactly one bounded prompt. During protected independent ideation, avoid anchoring: use only an answer-shape or distant-domain example, or defer the example until requested or the user is stuck. Add guidance progressively; coach without grading or jargon.

Honor the exercise the user named. Do not silently replace brainstorming with interviewing, process reconstruction, or another method. If another method would materially improve the work, explain the concern briefly and either keep it as a later next move or obtain explicit agreement before switching.

Honor why/example/define, slower/faster, skip, pause, undo, hand-back, exit, and resume. Preserve user contributions with stable IDs and `USER_PROVIDED`; they are not human research. Supersede rather than delete and redraw only meaningful board changes. Before a sealed round, copy accepted input equally to all members. During Round A, it is held unchanged until after the set is frozen.

## Make work inspectable and visual

In `VISIBLE`, show concise `NOW`, `INPUTS`, `OUTPUT`, `WHAT CHANGED`, and `NEXT` checkpoints at meaningful boundaries. In `WORKSHOP` (`◇ OPEN STUDIO`), show artifact-level transformations in this order: stable inputs → named method/constraint → new stable outputs → change → next move. Do not expose hidden chain-of-thought, scratchpads, tool logs, or raw subagent reasoning.

For a one-shot or `QUICK_LOOK` request, lead with the useful result. Use at most one compact product heading and omit participation menus, journey rails, Design Pulse, Build Gate, and process narration unless one of them changes the decision or the user requested it. Visible work should expose consequential transformations, not make the user read the facilitator's operating procedure.

When spatial relationships help—affinity clusters, process/journey maps, stakeholders, or assumptions—create a compact inline visual, and when the workspace is writable also use [visual-workbench.md](references/visual-workbench.md) with `render_visual.py` for a durable artifact. Return HTML, SVG, and Markdown fallback paths when created; Browser is optional. Preserve source-card IDs, wording, provenance, contradictions, and outliers. Apply participant privacy/disclosure rules to every export.

A one-turn read-only affinity or process-map preview uses this inline contract alone; do not load another reference. For affinity, lock the source-card deck before arranging. If the prompt already supplies stable-ID cards, treat it as locked and map by ID without repeating it; otherwise print each card once. Test an alternate arrangement as a validation check, but show it only when it materially changes the interpretation or the user asks. Keep qualifying counterexamples beside the theme they challenge and reserve the outlier area for genuinely unclustered records. For process maps, limit the depicted current-state path to supplied steps. Put inferred approval outcomes, ownership/status gaps, recovery branches, and prioritization in a separate `VERIFY` area; labeling an invented step does not make it observed. Load Visual Workbench only when creating or inspecting a durable artifact.

## Preserve state and finish

Keep project state human-readable, schema-versioned, portable, and append-only in meaning. Every mutation creates a revision; supersede rather than erase. Track evidence, frames, assumptions, ideas, studies, prototypes, experiments, debts, decisions, minority reports, participation, visual artifacts, and per-member memories. Project files—not optional hooks or platform memory—are canonical.

Before finishing substantial work, update state, run relevant deterministic checks, state what changed and remains uncertain, and name one concrete next learning move. A visual synthesis is incomplete without that move. If learning or an explicit override justifies building, implement and validate with unresolved risk visible.
