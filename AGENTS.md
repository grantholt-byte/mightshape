# Design Council development guidance

This repository ships a Codex-native human-centered design product. Preserve these priorities in order:

1. methodological rigor without ritual;
2. explicit evidence provenance;
3. deep, bounded Human Models;
4. sealed Council independence before social influence;
5. useful conceptual divergence and minority preservation;
6. low-friction, native Codex interaction;
7. progressive disclosure and token efficiency.
8. cross-platform parity from one canonical source.

Development rules:

- Keep `skills/design-council/SKILL.md` focused on routing, invariants, transitions, and resource selection. Put detailed methodology in directly linked references.
- Treat `skills/design-council/` as the canonical product core. Never hand-edit `dist/openai/` or `dist/claude/`; regenerate both with `scripts/build_packages.py`.
- Keep platform adapters mechanical. A Claude- or OpenAI-specific instruction may change invocation mechanics, never Human Models, evidence policy, methods, state, or Council protocols.
- Do not claim that Intake, Inquiry Lab, sealed rounds, Reality Check, Build Gate, Design Debt, Evidence Debt, or Assumption Burn-down are Stanford methods.
- Do not describe the five d.school modes as a mandatory linear process.
- Never convert Council or synthetic output into human evidence.
- Keep study definition, participant sourcing, interviewing, evidence ingestion, and synthesis separable; Exchange must remain a replaceable provider boundary.
- Never send a private InternalStudy to a participant. Produce and approve a minimized ExternalStudyPacket, and keep project-owner and participant consent independent.
- Do not make the core depend on hooks, Sites, Codex memories, an MCP server, or third-party infrastructure.
- Do not implement or imply working Exchange recruitment, verification, credits, payments, reputation, or legal screening in V1.
- Preserve schema versions and record supersession instead of deleting meaningful state history.
- Prefer Python's standard library for deterministic tooling.
- Use `apply_patch` for source edits. Do not edit generated `interview-app/dist` output.
- Run `python3 -m unittest discover -s tests -v`, the package validator, skill validator, plugin validator, schema checks, and behavioral contract evals after substantive changes.
- Run `make release-check` before a release; platform package drift is a release blocker.
- Build and test `interview-app` separately; never claim a public URL unless Sites returned one.
- Do not copy substantial source text or Stanford visual assets. Keep attribution precise and avoid any implication of endorsement.
