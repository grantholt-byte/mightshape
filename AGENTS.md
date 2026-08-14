# MightShape development guidance

This repository ships a Codex-native human-centered design product. Preserve these priorities in order:

1. methodological rigor without ritual;
2. explicit evidence provenance;
3. deep, bounded Human Models;
4. sealed Council independence before social influence;
5. useful conceptual divergence and minority preservation;
6. outcome quality and decision-relevant learning;
7. low-friction, native Codex interaction;
8. progressive disclosure without sacrificing substantive quality;
9. cross-platform parity from one canonical source;
10. optional, method-safe participant facilitation;
11. visual creativity without provenance loss.
12. team-channel collaboration without ambient message surveillance.

Development rules:

- Keep `skills/mightshape/SKILL.md` focused on routing, invariants, transitions, and resource selection. Put detailed methodology in directly linked references.
- Treat `skills/mightshape/` as the canonical product core. Never hand-edit `dist/openai/` or `dist/claude/`; regenerate both with `scripts/build_packages.py`.
- Keep platform adapters mechanical. A Claude- or OpenAI-specific instruction may change invocation mechanics, never Human Models, evidence policy, methods, state, or Council protocols.
- Do not claim third-party authorship of Intake, Inquiry Lab, sealed rounds, Reality Check, Build Gate, Design Debt, Evidence Debt, or Assumption Burn-down.
- Do not describe the five design thinking modes as a mandatory linear process.
- Never convert Council or synthetic output into human evidence.
- Never label illustrative/demo records as human interviews or observations. Public examples must name their real source and visibly state their limits.
- Keep participation optional and non-blocking. A novice facilitator explains only the immediate purpose and mindset, gives a method-safe example, and asks one bounded prompt; protected ideation must not receive a target-domain seed.
- Keep Slack, Discord, and Teams as thin adapters over one portable team-workshop contract. Collect input through explicit actions, dialogs, or direct mentions; do not request channel-wide message access merely for convenience.
- Treat teammate workshop contributions as `USER_PROVIDED`, never `HUMAN_INTERVIEW`. Keep platform identifiers and OAuth credentials outside portable project exports.
- Show inspectable method artifacts and transformations, never hidden chain-of-thought, private worker reasoning, or raw tool logs.
- Route bounded, reversible technical spikes directly when the metric and timebox are already explicit; do not spend MightShape tokens where plain execution is the better fit.
- Keep study definition, participant sourcing, interviewing, evidence ingestion, and synthesis separable; Exchange must remain a replaceable provider boundary.
- Never send a private InternalStudy to a participant. Produce and approve a minimized ExternalStudyPacket, and keep project-owner and participant consent independent.
- Do not make the core depend on hooks, Sites, Codex memories, an MCP server, or third-party infrastructure.
- Do not implement or imply working Exchange recruitment, verification, credits, payments, reputation, or legal screening in V1.
- Preserve schema versions and record supersession instead of deleting meaningful state history.
- Prefer Python's standard library for deterministic tooling.
- Use `apply_patch` for source edits. Do not edit generated `interview-app/dist` output.
- Run `python3 -m unittest discover -s tests -v`, the package validator, skill validator, plugin validator, schema checks, and behavioral contract evals after substantive changes.
- Run `make release-check` before a release; platform package drift is a release blocker.
- Treat plugin-versus-baseline outcome effectiveness as primary. Report incremental token/latency use and marginal quality gain separately as resource diagnostics; a configured token target must never veto an established quality benefit. Never call the result monetary ROI or cost-effective without a defensible utility/cost model.
- Compare against both raw prompting and a frozen competent Design Thinking prompt. Use persisted multi-turn trajectories to test reframing, history, evidence updates, conceptual breadth, experiment information gain, and backward iteration; do not infer those longitudinal benefits from a one-shot response.
- Build and test `interview-app` separately; never claim a public URL unless Sites returned one.
- Do not copy or closely paraphrase third-party source text, exercise scripts, examples, worksheets, card layouts, or visual assets. Keep lineage precise and avoid any implication of affiliation, certification, or endorsement.
- Runtime skills, prompts, steps, manifests, generated package copy, screenshots, and visual assets must not use third-party institutional names as product positioning. Maintainer-only factual citations belong in `docs/THIRD_PARTY_SOURCES.md` and must not be copied into distribution packages.
