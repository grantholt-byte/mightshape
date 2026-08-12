# ◇ Inquiry Lab

Use the visible `◇ INQUIRY LAB` heading when entering this subsystem so the user can tell which research contract now governs the work.

## Purpose

Understand people before designing for them. Inquiry Lab spans Empathize and Test and supports eight routes:

1. `SYNTHETIC_USER`
2. `SYNTHETIC_PRACTITIONER`
3. `SYNTHETIC_EXPERT`
4. `AI_FACILITATED_HUMAN_INTERVIEW`
5. `HUMAN_LED_FIELDWORK_KIT`
6. `MIXED_INQUIRY`
7. `ANALOGOUS_INQUIRY`
8. `SYNTHETIC_TO_HUMAN_REALITY_CHECK`

Synthetic inquiry generates hypotheses, useful language, possible friction, potential needs, failure modes, and better research questions. It is not human research.

## Participant-source boundary

Choose participant sourcing independently from the study, interview, evidence-ingestion, and synthesis layers:

- `SYNTHETIC`: functional research-grounded simulation;
- `BRING_YOUR_OWN`: functional researcher-supplied participants through a link or fieldwork kit;
- `EXCHANGE`: typed future provider that returns `NOT_CONFIGURED`, `UNAVAILABLE`, or `FUTURE_FEATURE` in V1 without disrupting the other routes.

Before anything is shared with an external human, keep the rich `InternalStudy` private and produce a minimized `ExternalStudyPacket`. Read [exchange-readiness.md](exchange-readiness.md), apply Disclosure Guard, and preserve separate project-owner and participant consent. Default early Empathize work to `LEVEL_0_PROBLEM_ONLY` plus `SOLUTION BLACKOUT` unless the research question justifies disclosure.

## Reality Packet first

Never begin a consequential professional simulation with shallow roleplay. Research current primary and authoritative sources, then create:

```yaml
id: RP-###
grounding_level: FAST | RESEARCHED | DEEP
role: string
scope_and_locale: string
responsibilities: []
working_environment: []
workflows: []
decision_rights: []
terminology: []
tools_and_systems: []
dependencies: []
organizational_relationships: []
incentives: []
constraints: []
regulations: []
performance_pressures: []
failure_modes: []
workarounds: []
common_variations: []
cultural_context: []
supported_facts:
  - claim: string
    source_ids: []
research_supported_inferences: []
unresolved_questions: []
local_variation: []
sources:
  - id: SRC-###
    title: string
    publisher: string
    url: string
    accessed: date
```

Use `FAST` only for low-consequence exploration and label thin grounding. Use `RESEARCHED` by default. Use `DEEP` for niche, technical, regulated, consequential, or highly local roles. Run `validate_reality_packet.py`; an insufficient packet blocks consequential persona construction but not a transparent draft research plan.

## Construct the participant

Load `human-model.md`. Create a full but proportionate life model and partition every detail:

- `DOMAIN_GROUNDING`: linked to Reality Packet facts.
- `REASONABLE_INFERENCE`: plausible, qualified, not observed.
- `CONSTRUCTED_CONTINUITY`: incidental fiction for conversational continuity.
- `UNKNOWN`: outside grounding or legitimate knowledge.

Do not make protected characteristics do explanatory work without evidence. Vary participants on behaviorally meaningful dimensions. A synthetic person must refuse population estimates, unsupported local rules, confidential knowledge, and facts outside their expertise.

Assign an opaque study participant ID such as `SP-001`. Never reuse the name, biography, relationships, or memory of Maya, Leo, Priya, Marcus, Elena, Theo, Samira, Jack, Mei, or Rafael: Council identities and study participants are separate systems. For a consequential interview, expose a compact Human Model card with life context, professional reality, current pressures, cognition, communication, contradiction, and knowledge boundaries before the transcript.

## Participant types

- **User:** experiences the problem or service; do not grant professional system knowledge by default.
- **Practitioner:** performs the work; ground process, tools, constraints, handoffs, and local variation.
- **Expert:** understands broader systems; distinguish general knowledge from site-specific practice and lived frontline reality.

## Independent synthetic study

1. Define variation dimensions relevant to behavior.
2. Generate participants independently from the same packet plus distinct dimension values.
3. Interview each under the same guide and adaptive protocol without sibling transcripts.
4. Freeze all transcripts before synthesis.
5. Run `compare_participants.py`.
6. If language, positions, sequences, or needs converge suspiciously, issue `SYNTHETIC CONVERGENCE WARNING` and inspect weak differentiation, leading questions, overconstrained grounding, or model convergence.
7. Synthesize as synthetic signals only.

## AI-facilitated human interview

Create a study with `create_study.py`. Select a participant source with `participant_sources.py`. Establish disclosure and affirmative consent before substantive questions. Keep participant IDs anonymous by default. Use adaptive story-first interviewing and Solution Blackout. Store transcript references and consent version. Honor stop and deletion paths. A project owner's future research-contribution opt-in never grants participant consent.

For a shareable link, load `hosted-interviews.md`. If Sites is unavailable, provide the fieldwork kit and validated companion without claiming deployment.

## Human-led fieldwork kit

Return:

- decision and learning goals;
- participant/context rationale and meaningful variation;
- recruitment and consent language;
- short flexible guide with story-first prompts;
- observation/capture sheet separating fact from interpretation;
- Solution Blackout and optional Concept Reveal plan;
- interviewer bias and safety notes;
- analysis method and stop condition.

## Mixed inquiry

Use synthetic work before humans to learn vocabulary, surface possible sequences, stress-test questions, and identify variation. Then conduct human inquiry. Compare findings explicitly; do not blend them into one sample.

## Analogous inquiry

Identify a transferable mechanism, not merely an interesting industry. Research the analogous role/environment before creating a synthetic expert. Record the analogy, shared mechanism, important difference, and what would need human testing. Analogous findings are inspiration/hypothesis, never proof.

## ◇ Reality Check

```yaml
id: RC-###
synthetic_hypothesis_id: E-###
expected_pattern: string
human_evidence_needed: []
strategy: []
human_evidence_ids: []
comparison: string
outcome: supported | contradicted | transformed | inconclusive
frame_before: string
frame_after: string
assumptions_changed: []
next_mode: EMPATHIZE | DEFINE | IDEATE | PROTOTYPE | TEST
```

Never force support/contradiction into a binary when evidence transforms the mechanism. A synthetic expectation about frequent schedule change may become a human-supported insight about discovering changes; record the transformation and supersede the old frame. With no human evidence, use `inconclusive`, keep the current frame provisional, and show the future update rule rather than implying that Reality Check already changed the frame. When later `HUMAN_INTERVIEW` or `OBSERVED_HUMAN_BEHAVIOR` evidence differs, cite those IDs, classify the comparison, supersede the provisional frame, and preserve both frames in history.

## Inquiry synthesis

Generate patterns, tensions, contradictions, candidate needs, potential insights, unanswered questions, challenged assumptions, limitations, and follow-up research. Display human, research, inference, and synthetic layers separately. Run the evidence checker before writing a new POV.
