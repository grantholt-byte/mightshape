# Publishing checklist

Nothing in this file authorizes publication. Check items only with inspectable evidence.

## Shared product

- [ ] Product owner confirms public publisher/repository identity.
- [x] MIT retained for the private beta; reconfirm the licensing strategy before public publication.
- [ ] `VERSION` and `CHANGELOG.md` are final and synchronized.
- [ ] README, privacy, security, terms, attribution, and support routes reviewed.
- [ ] Logo/icon and repository demo assets reviewed; no Stanford marks or endorsement.
- [ ] `make release-check` passes from a clean checkout.
- [ ] Humanity, independence, Inquiry, process, and adversarial evals pass.
- [ ] Optional participation tests pass for Watch, Collaborate, and One prompt at a time,
  including non-blocking default behavior, durable `USER_PROVIDED` contributions, and
  sealed-round input holding.
- [ ] Novice-assisted, guided, and light-touch facilitator behavior passes; novice mode
  explains the immediate purpose/mindset, gives one relevant example, and asks one bounded prompt.
- [ ] Visual Workbench accessibility, provenance, immutability, and browser-optional checks pass.
- [ ] Whimsical sticky-note/process-map rendering is visually inspected for readability,
  visible outliers, text fallback parity, and decoration that does not imply evidence strength.
- [ ] Controlled plugin-versus-baseline benchmark reviewed for both quality and token/latency overhead.
- [ ] Benchmark report is complete and reproducible; any effectiveness statement reflects
  realized pairs, uncertainty, important-value thresholds, and authored/model-judge limitations.
- [ ] Cross-platform drift/parity check passes with ten identical Human Models.
- [ ] Model-backed family-scheduler, ED-nurse, Council-humanity, and routing evals pass.
- [ ] No secrets, transcripts, real participant quotes, or confidential project data ship.
- [ ] Privacy copy explains visible workshop output, local participation records,
  undo-as-supersession, visual exports, and opt-in benchmark model calls.
- [ ] Python and Site dependency/security audits reviewed.
- [ ] Optional interview Site browser flow and consent/delete behavior pass.

## OpenAI / Codex

- [ ] `.codex-plugin/plugin.json` passes the current official validator.
- [ ] Skill metadata passes the current official validator.
- [ ] Local marketplace add/install/list/remove tested in a clean context.
- [ ] Explicit and implicit invocation plus inappropriate-trigger avoidance tested.
- [ ] Publisher identity verified; Apps Management write access confirmed.
- [ ] Public website, support, privacy-policy, and terms HTTPS URLs exist and match publisher.
- [ ] Five positive and three negative portal cases prepared.
- [ ] Current submission path rechecked at the OpenAI plugin portal.
- [ ] Skills-only submission reviewed; no unnecessary MCP server or unsupported screenshot.
- [ ] Approval and final Publish are treated as separate manual actions.

## Claude Code

- [ ] `dist/claude/design-council/.claude-plugin/plugin.json` passes through
  `claude plugin validate dist/claude/design-council --strict`.
- [ ] Root marketplace passes `claude plugin validate . --strict`.
- [ ] `--plugin-dir` sideload tested in a clean project.
- [ ] Local marketplace add/install/details/update/uninstall/remove tested.
- [ ] Explicit, implicit, sealed Agent, and negative-routing behavior tested.
- [ ] Public GitHub repository and release tag exist; `<owner>/<repo>` docs updated.
- [ ] Community-catalog form, validation, and safety-review requirements rechecked.
- [ ] Public copy distinguishes `claude-community` from curated official marketplace.

## Release artifacts

- [ ] `dist/design-council-openai-<version>.zip` inspected.
- [ ] `dist/design-council-claude-<version>.zip` inspected.
- [ ] Archive hashes recorded in release notes.
- [x] Owner explicitly approved the private-beta channel and colleague audience.
