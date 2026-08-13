# Changelog

All notable changes use [Semantic Versioning](https://semver.org/).

## [0.9.0-beta.5] — 2026-08-13

### Added

- Added `design-think` as the short, shared skill entry point while retaining the canonical
  Design Council product identity and existing invocation names for compatibility.
- Documented each host's native explicit form: `/design-think` on Claude Code 2.1.216 or
  later, `$design-think` (or `/skills`) in Codex, and `@design-think` in ChatGPT.

### Changed

- Claude documentation now also records the collision-safe namespaced form
  `/design-council:design-think`.
- OpenAI documentation now states plainly that packaged plugins cannot register arbitrary
  slash commands and that Design Council does not ship deprecated custom prompts.
- Longitudinal benchmark manifests now bind results to the Design Council version, Git commit,
  and dirty state so an efficacy run can be traced to an exact source freeze.

### Fixed

- Clean package builds now preserve user-owned conflict-copy files and directories under
  generated package folders while excluding them from archives and checksum metadata.

### Breaking Changes

- None. Legacy `$design-council` and `/design-council:design-council` invocation remain
  available throughout this beta.

## [0.9.0-beta.4] — 2026-08-13

### Fixed

- Longitudinal benchmark aggregation now refuses to report a complete design or efficacy
  verdict unless every planned candidate trajectory and blind judgment is present exactly
  once with the expected identity and repetition, and each saved judgment payload validates.
- Blind quality is recomputed from validated judge payloads; forged or missing cached quality
  fields cannot influence a result.
- Incomplete and quota-failed longitudinal runs now render a safe `INCOMPLETE` report instead
  of crashing or claiming that all trajectories completed.

### Security

- Preserved immutable beta tags: the benchmark hardening ships as a new beta rather than
  rewriting the already shared `v0.9.0-beta.3` tag.

### Breaking Changes

- None.

## [0.9.0-beta.3] — 2026-08-13

### Added

- Open Studio process views (`COMPACT`, `VISIBLE`, and `WORKSHOP`) with inspectable
  checkpoints, working cards, alternate groupings, mutations, exceptions, and outliers.
- A dependency-free Visual Workbench for evidence-linked affinity maps and process maps,
  emitted as reproducible source JSON, self-contained HTML, accessible SVG, Markdown,
  and an immutable manifest.
- Portable visual-artifact records in project state without embedding rendered HTML/SVG.
- Optional participatory exercises with `OBSERVE`, `COLLABORATE`, and
  `FACILITATED_TURN_BY_TURN` modes, presented as Watch, Collaborate, or One prompt at a time.
- Adaptive facilitator levels (`NOVICE_ASSISTED`, `GUIDED`, and `LIGHT_TOUCH`) with
  progressive explanation, one bounded prompt, user controls, and durable contribution ledgers.
- An opt-in, isolated plugin-versus-baseline benchmark with blind paired judging, token
  and latency accounting, uncertainty estimates, incremental outcome value per additional
  token, per-case value quadrants, straightforward-task routing checks, a frozen competent
  Design Thinking prompt-only comparator, blind judge dimension profiles, and overlapping
  user-value construct scorecards.
- A blind human paired-rating schema and protocol for subjective next-decision quality,
  right-problem framing, conceptual breadth, informative experiments, evidence-driven
  iteration, momentum, and multi-turn trajectory review.
- An opt-in persisted-session trajectory benchmark comparing the skill with either plain Codex
  or the frozen competent Design Thinking prompt across four-turn evidence-change journeys. It
  scores reframing, history, assumption updates, divergence, evidence provenance, experiment
  information gain, backward iteration, and momentum while reporting resource use separately.
- Visual, visibility, participation, sealed-round, benchmark-isolation, and cross-platform
  parity tests.

### Changed

- Substantial sessions now show conclusion-level method outputs as they develop while
  keeping routine implementation compact.
- Affinity clustering and process/journey mapping route to visual artifacts when spatial
  structure materially improves comprehension.
- Visual artifacts now use a warm innovation-studio language: tactile sticky notes, tape,
  folded corners, colorful cluster neighborhoods, playful lanes, and visible outliers,
  while retaining accessible text and provenance labels.
- Joining users receive novice-assisted facilitation by default unless their Design Thinking
  fluency is evident; watching remains non-blocking and participation can be paused,
  handed back, or exited at any time.
- Package builds exclude accidental operating-system duplicate files matching `* 2.*`.
- Bounded, reversible technical spikes with explicit metrics and timeboxes now route to
  direct execution unless Design Council is explicitly requested; design-heavy learning
  prototypes retain the full facilitation contract.
- Comparative effectiveness is now the primary A/B verdict. Token and latency use remain
  visible optimization/resource descriptors but cannot negate an established outcome-quality
  benefit.
- One-shot outputs now remove participation menus and product ceremony unless decision-relevant,
  retain at least three mechanism-distinct frames when ambiguity remains, preserve conditional
  pivots, and reject arbitrary or internally inconsistent prototype thresholds.

### Security

- Visual exports escape untrusted text, contain no remote assets/scripts/telemetry, retain
  evidence provenance, and open a local browser only by explicit request.
- Benchmark runs use fresh workspaces and homes, auth-only credential copying, read-only
  sandboxes, ephemeral sessions, and no inherited user plugins or ambient service keys.
- Participatory workshop contributions retain `USER_PROVIDED` provenance, undo uses
  supersession rather than deletion, and in-flight sealed Council packets cannot be changed
  selectively by new user input.
- Marketplace visual examples use only supplied benchmark inputs labeled `USER_PROVIDED`;
  illustrative `P-*` identifiers are explicitly not represented as participants or interviews.

### Breaking Changes

- None. Existing project-state files remain valid; visual and participation fields are additive.

## [0.9.0-beta.2] — 2026-08-12

### Fixed

- Documented authenticated private-repository preflight for Codex installs.
- Forced HTTPS for Claude Code marketplace installs when GitHub SSH keys are unavailable.
- Clarified immutable-tag update behavior and private-beta access requirements.

## [0.9.0-beta.1] — 2026-08-12

### Added

- Adaptive Intake plus iterative Empathize, Define, Ideate, Prototype, and Test modes.
- Ten deep, persistent Council Human Models and sealed independent-round protocol.
- Inquiry Lab, Reality Packets, synthetic epistemic layers, live BYO interviews,
  Solution Blackout, Reality Check, and optional ChatGPT Sites companion.
- Evidence Firewall, versioned project memory, Minority Report, Build Gate,
  Assumption Burn-down, Design Debt, and Evidence Debt.
- Exchange-ready participant-source, disclosure, conflict, privacy, and exposure boundaries.
- Generated OpenAI and Claude Code packages from one canonical core.
- Deterministic utilities, JSON Schemas, unit tests, behavioral evals, and release checks.

### Changed

- Intake and method routing were refined after adversarial and model-backed tests.
- Hosted interview UX was refined against consent and active-session visual references.
- Acceptance synthesis now exposes a sealed-round receipt and competing POVs without revealing private reasoning.
- Consequential full-cycle output now exposes anonymous cross-pollination and forced-mutation ledgers before convergence.
- Synthetic Inquiry demonstrations now expose a compact bounded Human Model and keep study identities separate from the standing Council.

### Fixed

- Aligned user-provided and synthetic evidence strength with the canonical firewall.
- Corrected template discovery, schema reference resolution, and eval-fixture injection.
- Hardened sealed-round freezing, sibling-reference rejection, and anonymization.
- Prevented unlabeled general model knowledge from appearing as evidence.
- Made Inquiry Lab entry and inconclusive Reality Check update rules explicit after strict model-judge failures.
- Prevented a completed Council cycle from collapsing post-freeze divergence into an unauditable synthesis claim.
- Prevented an in-flight AI interview response from being persisted after a
  participant's concurrent stop request.
- Preserved participant transcript roles in Responses API input instead of
  interpolating participant-controlled text into developer-priority instructions.
- Kept internal visual-generation reference assets out of public plugin archives.

### Security

- Added AI disclosure, explicit consent, participant stop/delete controls, PII
  minimization, opaque link tokens, server-only model keys, and `store: false` model calls.
- Added Disclosure Guard and external-packet minimization without destructive rewriting.

### Breaking Changes

- None. This is the first private-beta release candidate.
