# Project state contract

## Canonical location

Store sustained journey state under the project being designed:

```text
.design-council/
├── project.json
├── history/
│   ├── rev-000001.json
│   └── rev-000002.json
├── council-rounds/
├── inquiry/
│   ├── internal-studies/
│   ├── external-packets/
│   └── disclosure-reviews/
└── exports/
```

`project.json` is canonical. Each mutation increments `revision`, writes atomically, appends a history event, and saves a complete revision snapshot. Never edit an older snapshot. Keep secrets and direct identifiers out of state.

## Main domains

Track:

- challenge, original prompt, original proposed solution, current problem frame, desired outcome;
- archetypes, operating depth, complexity, reversibility, cost/consequence of error;
- current mode, cycle, completed modes, and backward transitions;
- stakeholders, evidence, assumptions, unknowns, observations, needs, insights;
- POV history and supersession, HMW prompts, ideas, clusters, outliers, selected concept portfolio;
- prototypes, experiments, inquiry studies, Reality Packets, synthetic personas, participant IDs, Reality Checks;
- participant-source selections, private internal studies, minimized external packets, disclosure reviews, exposure levels, and conflict-policy references;
- decisions, Minority Reports, Build Gate, Design Debt, Evidence Debt;
- each Council member's project memory;
- append-only history explaining why material state changed.

## Identity and IDs

Use stable prefixes: `E-` evidence, `A-` assumption, `N-` need, `I-` insight, `POV-`, `HMW-`, `IDEA-`, `PROTO-`, `EXP-`, `STUDY-`, `RP-`, `SP-`, `P-`, `RC-`, `DEC-`, `MR-`, `DD-`, `ED-`, `CR-` Council round.

Never recycle an ID. Participant IDs default to `P-001`; do not require names or email.

Keep internal studies, sanitized external packets, and disclosure reviews as distinct versioned records under `inquiry/`. Never replace a private study with its redacted packet. Never store future Exchange identity-verification material in researcher-visible project state.

## Historical integrity

Supersede rather than overwrite:

```json
{
  "id": "POV-001",
  "status": "superseded",
  "superseded_by": "POV-004",
  "changed_because": ["EXP-003", "E-041"],
  "superseded_at": "..."
}
```

Falsified assumptions remain visible. A changed Council belief retains both positions. Removed concepts become `retired`, with a reason; outliers are never silently deleted.

## Assumption Burn-down

Allowed assumption states:

- `RESOLVED`
- `TESTING`
- `OPEN_HIGH_RISK`
- `OPEN_LOW_RISK`
- `FALSIFIED`

Every resolved or falsified state links evidence or an experiment. Do not resolve an assumption from Council agreement or synthetic repetition.

## Optional state hook

The bundled SessionStart hook emits a compact summary only when `.design-council/project.json` is present. It is trust-gated and may be disabled. Always read canonical state directly before consequential work.
