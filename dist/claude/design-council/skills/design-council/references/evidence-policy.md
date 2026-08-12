# Evidence Firewall

## Contents

1. Provenance vocabulary
2. Claim contract
3. Strength and confidence
4. Promotion rules
5. Synthesis rules
6. Debt

## Provenance vocabulary

| Provenance | Meaning | Direct human evidence? |
|---|---|---:|
| `OBSERVED_HUMAN_BEHAVIOR` | Recorded behavior observed in context | Yes, situated |
| `HUMAN_INTERVIEW` | Statement or reconstructed story from a real consenting participant | Yes, self-report |
| `USER_PROVIDED` | Claim supplied by the current user; truth not independently verified | No unless source is attached |
| `AUTHORITATIVE_RESEARCH` | Traceable primary/official/authoritative external source | External evidence |
| `RESEARCH_SUPPORTED_INFERENCE` | Interpretation derived from cited evidence | No; inference |
| `SYNTHETIC_USER` | Simulated person experiencing a problem/service | No |
| `SYNTHETIC_PRACTITIONER` | Simulated person doing the work | No |
| `SYNTHETIC_EXPERT` | Simulated broad domain/system expert | No |
| `DESIGN_COUNCIL` | Council hypothesis, critique, idea, or interpretation | No |
| `ASSUMPTION` | Belief currently treated as uncertain | No |
| `UNKNOWN` | Material question without support | No |

Research facts inside a Reality Packet remain `AUTHORITATIVE_RESEARCH`; a synthetic persona's statements derived from them remain synthetic in a transcript. Link the grounding source rather than changing transcript provenance.

## Claim contract

Every stored claim uses at least:

```json
{
  "id": "E-001",
  "claim": "Families may resist automatic rescheduling.",
  "provenance": "SYNTHETIC_USER",
  "confidence": 0.84,
  "evidence_strength": 0,
  "status": "unvalidated",
  "source_refs": ["SP-002:T-004"],
  "scope": "hypothesis, not prevalence"
}
```

For human evidence, include study ID, participant ID, transcript or observation reference, date, and a de-identified excerpt only when consent permits. Never invent a quotation. For authoritative research, store title, publisher/author, URL, publication date if known, accessed date, and the exact claim supported.

## Strength and confidence

`confidence` expresses how plausible the claim currently seems, from 0 to 1. `evidence_strength` is a facilitation heuristic from 0 to 5 reflecting directness, traceability, relevance, and triangulation. Neither is certainty or population validity.

Hard rules:

- Synthetic, Council, assumption, and unknown items have evidence strength `0` for real-world claims.
- Research-supported inference may not exceed `2`.
- User-provided claims default to `0` until a source is attached and reclassified.
- A single interview can be strong evidence of that person's experience but weak evidence of prevalence.
- Repetition from the same model, source, or study does not create independent corroboration.
- High confidence never upgrades provenance.

## Promotion rules

Never edit a provenance label to make a claim appear stronger. Add a new evidence record and link it with `tests`, `supports`, `contradicts`, or `transforms`.

Examples:

- A synthetic hypothesis `E-014` tested by interview excerpt `E-031` stays synthetic; `E-031` is a separate `HUMAN_INTERVIEW` record.
- A user's claim remains `USER_PROVIDED` until the cited original source is read; then create an `AUTHORITATIVE_RESEARCH` record.
- A Council interpretation of three observations remains `DESIGN_COUNCIL` or `RESEARCH_SUPPORTED_INFERENCE`, with links to the observations.
- Constructed continuity in a persona is never exported to the evidence ledger.

## Synthesis rules

1. Group evidence by provenance before looking for patterns.
2. Preserve contradictions and negative cases.
3. State the sample and context; do not convert “3 of 5 interviewees” into a market percentage.
4. Separate observation, interpretation, and implication.
5. State whether a pattern is human-supported, research-supported, synthetic, inferred, assumed, or unknown.
6. Check source independence. Multiple summaries of one source count as one source.
7. When synthetic and human findings disagree, create a Reality Check; treat the disagreement as useful learning.
8. Do not quote a synthetic participant in a layout that could be mistaken for a real participant. Mark the card and every excerpt.

## Design Debt and Evidence Debt

`DESIGN_DEBT` records implementation on unresolved user/problem assumptions. `EVIDENCE_DEBT` records consequential decisions relying mostly on inference, synthetic signals, or absent human evidence.

Debt is a communication device. It does not prohibit building and should not become a game score. Each debt item names the decision, unresolved claim, consequence, mitigation, owner if known, and review trigger.

Use `check_evidence.py` before Build Gate review, interview synthesis, and any claim that changes from synthetic expectation to human finding.
