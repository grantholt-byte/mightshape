# Contributing

Thank you for improving Design Council. Preserve the product before adding surface area.

1. Read `AGENTS.md`, `skills/design-council/SKILL.md`, and the reference you plan to change.
2. Keep methodology, Human Models, evidence rules, schemas, and eval fixtures in the
   canonical source under `skills/design-council/`. Do not hand-edit generated `dist/` files.
3. Keep platform mechanics in `platforms/` or packaging scripts. A platform adapter may
   change invocation mechanics, never the Council's identities or epistemic rules.
4. Add an adversarial test for behavior changes and a unit test for deterministic changes.
5. Run `make release-check`. For Claude packaging, also run the current official
   `claude plugin validate ... --strict` command.
6. Update `CHANGELOG.md` for user-visible or security-relevant changes.

Method contributions must name their actual lineage. Do not claim Stanford authorship
without a primary Stanford source. Do not add participant quotes, transcripts, or project
material to fixtures unless they are explicitly synthetic and safe to publish.

Changes should be small enough to review. Explain the product invariant affected, the
evidence for the change, and how you tested cross-platform parity.
