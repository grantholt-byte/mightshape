# Exchange-ready human research boundary

## V1 boundary

Design Council Core provides intelligence. A future Design Council Exchange may provide access to relevant lived experience. V1 builds the provider doorway and information-safety boundary; it does **not** build a participant marketplace, recruitment operation, payments, research-credit balances, identity or credential verification, public profiles, reputation scores, direct messaging, NDAs, legal conflict screening, or remote telemetry.

The reserved future product name is **◇ DESIGN COUNCIL EXCHANGE**. Its intended promise is: “Real people. Relevant experience. Only the context they need.” Do not surface marketing copy in ordinary facilitation.

## Separation of responsibilities

Keep five concerns separate:

```text
InternalStudy
    ↓
ParticipantSource
    ↓
interview/session
    ↓
Evidence Firewall ingestion
    ↓
inquiry synthesis
```

`InternalStudy` defines the learning goal, private context, session type, exposure policy, conflicts, and consent boundary. `ParticipantSource` chooses where participants come from. The interviewing layer should not change because sourcing changes. Evidence ingestion assigns provenance from what actually happened: a completed real-person session is `HUMAN_INTERVIEW`; a simulation remains the applicable `SYNTHETIC_*` class. Synthesis consumes provenance-aware evidence rather than provider internals.

The machine contracts are `internal-study.schema.json`, `participant-source.schema.json`, `external-study-packet.schema.json`, and `participant_sources.py`.

## Participant sources

- `SYNTHETIC` is functional in V1. Build a Reality Packet, create deep participants, interview independently, and retain synthetic provenance.
- `BRING_YOUR_OWN` is functional where a shareable link or researcher-led fieldwork is available. The researcher recruits their participants; Design Council supplies the approved external packet, consent surface, interview, and human-evidence ingestion.
- `EXCHANGE` is a future provider. In V1 its methods return `NOT_CONFIGURED`, `UNAVAILABLE`, or `FUTURE_FEATURE` with no side effect. Never invent recruitment progress or a participant pool.

The future provider contract reserves these operations:

```text
create_recruitment_request()
estimate_participant_pool()
match_participants()
invite_participants()
track_participation()
return_completed_sessions()
```

A later backend can implement those methods, emit completed human sessions into the existing Evidence Firewall, and leave study definition, interview state, and synthesis unchanged.

## Research session types

Use one of:

- `HUMAN_PULSE`: a very short lived-experience question or session;
- `QUALITATIVE_INTERVIEW`: adaptive, story-first behavior reconstruction;
- `PROTOTYPE_TEST`: interaction with a concept or artifact;
- `CONCEPT_REACTION`: neutral later-stage concept exposure;
- `EXPERT_REVIEW`: practitioner or domain-system scrutiny;
- `CO_CREATION`: higher-disclosure collaborative generation.

Early Empathize work normally favors `HUMAN_PULSE` or `QUALITATIVE_INTERVIEW` because they can bring in reality with little project exposure.

## Information minimization invariant

**A participant receives only the information necessary to answer the research question well.**

Share the problem before the solution. Share the experience before the IP. Reveal only what the research requires. If the question can be answered without the proposed solution, keep `SOLUTION_BLACKOUT` on. If a prototype can be tested without sponsor identity, remove sponsor identity.

### Project exposure levels

- `LEVEL_0_PROBLEM_ONLY`: share lived-experience context only. Prefer with `SOLUTION_BLACKOUT = ON` for early Empathize inquiry.
- `LEVEL_1_ABSTRACTED_CONCEPT`: share a generalized concept with unnecessary proprietary detail removed.
- `LEVEL_2_PROTOTYPE_BLIND`: expose only what a participant needs to perform the prototype task; omit sponsor, strategy, roadmap, architecture, and proprietary rationale.
- `LEVEL_3_CONFIDENTIAL`: reserve for future higher-disclosure controls. V1 can store the intent but does not implement confidentiality agreements, eligibility verification, or legal controls.

Solution Blackout and exposure are related but distinct. Exposure limits the full packet; Blackout controls whether the solution is revealed at the current interview phase. Concept Reveal is explicit and occurs only when the method requires it.

## Internal study versus external packet

Never send an `InternalStudy` to a participant. It may contain the full challenge, proposed solution, sponsor context, hypotheses, assumptions, and strategic rationale.

Create a separate `ExternalStudyPacket` through Disclosure Guard. The packet is allow-listed and contains only participant purpose/context, topics, duration, AI disclosure, stop notice, optional approved prototype reference, exposure/Blackout state, consent version, and traceability IDs. Store the original unchanged. A disclosure finding names the field path and category but does not reproduce the detected sensitive value.

An external packet begins as `DRAFT` or `REQUIRES_USER_DECISION`; a human must approve it for external use. Disclosure Guard must never auto-destroy or rewrite private project state.

## ◇ Disclosure Guard

Run `disclosure_guard.py` before material is prepared for any external human participant. It detects field- and pattern-level signals including sponsor/company identity, project codenames, pricing, solution disclosure, source code and architecture, commercial strategy, customer identifiers, confidential terminology, competitor references, document metadata, personal identifiers, and secrets.

It recommends one of:

- `REMOVE`: unnecessary and unsafe for the research packet;
- `GENERALIZE`: retain the research mechanism without proprietary detail;
- `RETAIN`: directly necessary for the participant interaction;
- `REQUIRES_USER_DECISION`: ambiguous or higher-disclosure material, omitted from the safe draft pending a decision.

The helper produces a sanitized external representation and `IP_EXPOSURE_ASSESSMENT` across sponsor identity, solution, technical IP, commercial strategy, competitor inference, and participant conflict. `LOW`, `MODERATE`, or `HIGH` is facilitation guidance—not a confidentiality guarantee or legal opinion. Caller-designated sensitive terms improve detection; deterministic scanning cannot discover every trade secret or infer every sponsor clue.

## Conflict and participant privacy readiness

`conflict-policy.schema.json` stores `NONE`, `STANDARD`, or `STRICT` research-matching exclusions for companies, industries, roles, and relationships. These are future matching controls, not legal conflict screening.

Participant profiles keep three views separate:

- `PRIVATE_PROFILE`: identity/contact/verification references controlled by the future provider;
- `MATCHING_PROFILE`: experience signals and study-fit attributes;
- `RESEARCHER_VISIBLE_PROFILE`: participant ID and only study-relevant experience context.

Matching emphasizes lived or professional experience, workflow exposure, decision responsibility, environment, frequency, recency, technology use, and relevant constraints. Sensitive attributes are not defaults; when methodologically necessary they require recorded justification, handling controls, and participant consent. Verification states are `SELF_REPORTED`, `VERIFIED`, `PROFESSIONALLY_VERIFIED`, and `CREDENTIAL_VERIFIED`. V1 performs no verification and must not label someone verified without real evidence.

## Consent boundaries

Project-owner consent and participant consent are independent. A project owner opting into future methodological learning never grants permission to contribute participant content. Human transcripts, quotations, identities, or uploaded material remain excluded unless the participant's own applicable consent explicitly permits the use.

The optional `LearningSignal` is opt-in, aggregate, and structurally excludes raw project content, conversations, source code, company names, transcripts, quotations, and participant identities. The optional demand-signal event interface contains only a fixed event name and timestamp. V1 implements no remote collection or analytics transport.

## Future research credits and quality

`EXCHANGE_CREDITS` are ordinary future platform research credits, never cryptocurrency. The V1 ledger schema is deliberately inert: no balances, entries, pricing, payments, compensation, or purchases are executed. Future internal participant-quality signals may cover completion reliability, specificity, thoughtful participation, instruction adherence, session quality, and verified expertise; do not build public or gamified reputation scores.

## Three-ring future model

```text
RING 1 — PRIVATE DESIGN COUNCIL
Standing synthetic Council; private to the user's design process.

RING 2 — DESIGN COUNCIL EXCHANGE
Future abstracted human research with low project exposure.

RING 3 — VERIFIED CONFIDENTIAL NETWORK
Future verified practitioners/experts under stronger controls.
```

Real humans supply stories, behavior, workflow reality, and prototype reactions. The Evidence Firewall brings that reality into the private Design Council. Proprietary ideation does not need to be outsourced to strangers.

## Extension acceptance condition

A future Exchange adapter should be able to accept the existing internal study plus approved external packet, match five qualified participants using experience/conflict contracts, return completed sessions, debit future research credits, and ingest those sessions as `HUMAN_INTERVIEW` evidence. Implementing that adapter should not require changes to Inquiry Lab interviewing, evidence provenance, or synthesis. Only the Exchange provider, persistence/operations, verification, compensation, and stronger Ring 3 controls remain deferred.
