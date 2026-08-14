# Publishing checklist

Nothing in this file authorizes publication. Check items only with inspectable evidence.

## Shared product

- [x] Repository metadata names Grant Holt as the intended publisher; final platform identity verification remains manual.
- [x] MIT retained for V1; reconfirm the licensing/trademark strategy before public publication.
- [x] `VERSION` and `CHANGELOG.md` are final and synchronized.
- [x] README, privacy, security, terms, attribution, public support route, and private vulnerability
  route reviewed.
- [ ] Owner confirms the public publisher name, launch regions, and repository visibility in
  `docs/SUBMISSION_DOSSIER.md`; owner separately decides on optional skills-only trust URLs and
  requires deployment-specific support/privacy/terms before promoting hosted interviews.
- [x] Logo/icon and repository demo assets reviewed; no Stanford marks or endorsement.
- [x] `make release-check` passes in the release working tree; repeat from the final clean commit.
- [x] Humanity, independence, Inquiry, process, and adversarial evals pass.
- [x] Optional participation tests pass for Watch, Collaborate, and One prompt at a time,
  including non-blocking default behavior, durable `USER_PROVIDED` contributions, and
  sealed-round input holding.
- [x] Novice-assisted, guided, and light-touch facilitator behavior passes; novice mode
  explains the immediate purpose/mindset, gives one relevant example, and asks one bounded prompt.
- [x] Visual Workbench accessibility, provenance, immutability, and browser-optional checks pass.
- [x] Whimsical sticky-note/process-map rendering is visually inspected for readability,
  visible outliers, text fallback parity, and decoration that does not imply evidence strength.
- [x] Controlled plugin-versus-baseline benchmark reviewed for both quality and token/latency overhead.
- [x] The preregistered engineering criteria in `docs/V1_RELEASE_GATE.md` pass on a clean,
  commit-bound source freeze; inconclusive evidence is not relabeled as efficacy.
- [x] Benchmark report is complete and reproducible; any effectiveness statement reflects
  realized pairs, uncertainty, important-value thresholds, and authored/model-judge limitations.
- [x] Cross-platform drift/parity check passes with ten identical Human Models.
- [x] Model-backed family-scheduler, ED-nurse, Council-humanity, and routing evals pass within their documented claim boundaries.
- [x] No secrets, transcripts, real participant quotes, or confidential project data ship.
- [x] Public GitHub source contains the MIT license, passed a tracked-history credential-pattern
  scan, supports anonymous pinned installs, and has private vulnerability reporting enabled.
- [x] Privacy copy explains visible workshop output, local participation records,
  undo-as-supersession, visual exports, and opt-in benchmark model calls.
- [x] Python and Site dependency/security audits reviewed.
- [x] Optional interview Site browser flow and consent/delete behavior pass in the deterministic/rendered suite; D1 lifecycle remains environment-gated.

## OpenAI / Codex

- [x] `.codex-plugin/plugin.json` passes bundled authoring validation.
- [x] Skill metadata passes bundled authoring validation.
- [ ] Final bundle passes the current live OpenAI portal validator.
- [x] Local marketplace add/install/list/remove tested in a clean context.
- [x] Explicit and implicit invocation plus inappropriate-trigger avoidance tested in a clean
  Codex context.
- [ ] Publisher identity verified; Apps Management write access confirmed.
- [ ] Owner decides whether to add the optional skills-only website/support/privacy/terms URLs;
  any hosted service has reviewed deployment-specific pages before it is promoted.
- [ ] Repository architecture notes are not submitted as if they were reviewed production
  privacy terms or service terms.
- [x] Five positive and three negative reviewer cases prepared with prompts, observable behavior,
  result shape or fallback, and reproducibility information; the current general submission guide
  requires them for this skills-only submission.
- [x] Current submission path and requirements rechecked against the live official OpenAI docs;
  authenticated portal access remains an external account step.
- [x] Skills-only submission reviewed; no unnecessary MCP server or unsupported screenshot is bundled.
- [x] V1 gate passed before any public submission; no beta trial/demo listing was submitted merely
  to reserve placement.
- [x] Prepared listing contains no digital-service pricing, Exchange-credit promotion, subscription
  plans, upgrade pitch, or checkout link.
- [x] Approval and final Publish are treated as separate manual actions in the release documentation.

## Claude Code

- [x] `dist/claude/design-council/.claude-plugin/plugin.json` passes through
  `claude plugin validate dist/claude/design-council --strict`.
- [x] Root marketplace passes `claude plugin validate . --strict`.
- [x] `--plugin-dir` sideload/package loading tested in an isolated configuration.
- [x] Local marketplace add/install/details/update/uninstall/remove lifecycle tested.
- [ ] Native Claude explicit, implicit, sealed Agent, and negative-routing model behavior remains
  unclaimed because the available Claude OAuth session expired; shared contracts and package
  parity pass.
- [x] Immutable `v1.0.0` tag and pinned GitHub install verified for
  `grantholt-byte/design-council`.
- [x] Claude distribution selected: public GitHub repository with plugin path
  `dist/claude/design-council`. Current directory submission does not accept closed-source or ZIP
  submissions.
- [x] Community directory form, public-repository, validation, and safety-review requirements
  rechecked against current official documentation; approved third-party plugins enter
  `claude-community`, not the separately curated `claude-plugins-official` marketplace.
- [ ] Anthropic Software Directory Policy and Terms reviewed and accepted by the authorized
  publisher; rights and privacy representations are accurate.
- [x] Public copy distinguishes a community directory listing from the separate Anthropic Verified badge.

## Release artifacts

- [x] `dist/design-council-openai-1.0.0.zip` inspected; archive integrity, version, and numbered-duplicate exclusion pass.
- [x] `dist/design-council-claude-1.0.0.zip` inspected; archive integrity, version, and numbered-duplicate exclusion pass.
- [x] Archive hashes are recorded in `dist/SHA256SUMS`; recheck from the final clean commit.
- [x] Owner authorized free public marketplace submission on 2026-08-13; portal/form submission,
  review approval, and final catalog publication are recorded as separate external states.
