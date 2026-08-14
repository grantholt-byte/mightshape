# Publishing checklist

Nothing in this file authorizes publication. Check items only with inspectable evidence.

## Shared product

- [x] Repository metadata names Grant Holt as the intended publisher; final platform identity verification remains manual.
- [ ] Qualified counsel clears the “MightShape” product name for the intended goods, services,
  platforms, and launch regions; preliminary screening is not legal clearance. See
  `docs/BRAND_CLEARANCE.md`.
- [x] MIT retained for independently authored V1 material; no third-party source expression is
  represented as MIT-licensed.
- [x] `VERSION` and `CHANGELOG.md` are synchronized for `1.0.1`.
- [ ] README, privacy, security, terms, attribution, public support route, and private vulnerability
  route reviewed against the renamed repository and collaboration deployment.
- [ ] Owner confirms the public publisher name, launch regions, and repository visibility in
  `docs/SUBMISSION_DOSSIER.md`; owner separately decides on optional skills-only trust URLs and
  requires deployment-specific support/privacy/terms before promoting hosted interviews.
- [x] Runtime package and marketplace branding check passes with no third-party institutional positioning, source artwork, or implied endorsement.
- [ ] `make release-check` passes after the collaboration lifecycle merge and from the final clean
  commit.
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
- [ ] Renamed public GitHub source contains the MIT license, passes a tracked-history
  credential-pattern scan, supports anonymous pinned installs, and has private vulnerability
  reporting enabled.
- [x] Privacy copy explains visible workshop output, local participation records,
  undo-as-supersession, visual exports, and opt-in benchmark model calls.
- [x] Python and Site dependency/security audits reviewed.
- [x] Optional interview Site browser flow and consent/delete behavior pass in the deterministic/rendered suite; D1 lifecycle remains environment-gated.

## OpenAI / Codex

- [x] MightShape beta `.codex-plugin/plugin.json` passes bundled authoring validation after the
  collaboration merge; repeat on the final stable artifact.
- [x] MightShape beta skill metadata passes bundled authoring validation after the collaboration
  merge; repeat on the final stable artifact.
- [ ] Final bundle passes the current live OpenAI portal validator.
- [ ] Renamed local marketplace add/install/list/remove tested in a clean context.
- [ ] Renamed explicit and implicit invocation plus inappropriate-trigger avoidance tested in a
  clean Codex context.
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
- [x] The pre-rebrand V1 core gate passed; MightShape remains beta until its new release gates pass
  and is not submitted merely to reserve placement.
- [x] Prepared listing contains no digital-service pricing, Exchange-credit promotion, subscription
  plans, upgrade pitch, or checkout link.
- [x] Approval and final Publish are treated as separate manual actions in the release documentation.

## Claude Code

- [x] MightShape beta `dist/claude/mightshape/.claude-plugin/plugin.json` passes through
  `claude plugin validate dist/claude/mightshape --strict` after the collaboration merge; repeat
  on the final stable artifact.
- [x] MightShape beta root marketplace passes `claude plugin validate . --strict`; repeat on the
  final stable artifact.
- [ ] Renamed `--plugin-dir` sideload/package loading tested in an isolated configuration.
- [ ] Renamed local marketplace add/install/details/update/uninstall/remove lifecycle tested.
- [ ] Native Claude explicit, implicit, sealed Agent, and negative-routing model behavior remains
  unclaimed because the available Claude OAuth session expired; shared contracts and package
  parity pass.
- [ ] Immutable `v1.0.1` (and later stable `v1.1.0`) tag plus pinned GitHub install verified
  for `grantholt-byte/mightshape`.
- [ ] Claude distribution selected: publish the renamed GitHub repository with plugin path
  `dist/claude/mightshape`. Current directory submission does not accept closed-source or ZIP
  submissions.
- [x] Community directory form, public-repository, validation, and safety-review requirements
  rechecked against current official documentation; approved submissions surface in
  `claude-plugins-official`, while Anthropic Verified remains an additional review badge.
- [ ] Anthropic Software Directory Policy and Terms reviewed and accepted by the authorized
  publisher; rights and privacy representations are accurate.
- [x] Public copy distinguishes a community directory listing from the separate Anthropic Verified badge.

## Release artifacts

- [x] Current `dist/mightshape-openai-1.0.1.zip` inspected; archive integrity, version, and
  numbered-duplicate exclusion pass.
- [x] Current `dist/mightshape-claude-1.0.1.zip` inspected; archive integrity, version, and
  numbered-duplicate exclusion pass.
- [x] Current beta archive hashes are recorded in `dist/SHA256SUMS`; regenerate from the clean
  release commit.
- [x] Owner requested the renamed free release; MightShape submission, review approval, catalog
  publication, and former-listing retirement remain separate manual states.

## Optional team-channel companion

- [ ] Repeat `make release-check` from the final clean `1.0.1` commit.
- [x] Shared workshop engine, portable/private state split, explicit opt-in, Pass, sealed freeze,
  `USER_PROVIDED` provenance, retention deletion, and visual fallback tests pass.
- [x] Slack manifest requests only `commands`, `chat:write`, and `files:write`; Socket Mode and the
  current external file-upload flow are covered without channel-history scopes.
- [x] Discord interactions are signature/staleness checked, mention-safe, require no Gateway or
  Message Content intent, and upload an accessible inline PNG.
- [x] Teams manifest targets schema 1.29, standard team channels, and no Graph/RSC history access;
  current SDK and Adaptive Card behavior are covered structurally.
- [ ] Complete one real private-workspace Slack install, one Discord test-guild install, and one
  Teams tenant sideload with operator-owned credentials; record screenshots and redacted receipts.
- [ ] Publish an operator-specific privacy notice, retention schedule, support path, and terms
  before inviting coworkers outside a controlled beta.
- [ ] Replace the single-process store and process-local receipt ledger before horizontal scaling.
- [ ] Configure managed secrets, encrypted persistence, scheduled `npm run purge-expired`, backups,
  and monitoring that excludes participant content.
- [ ] Treat Slack/Discord/Teams marketplace review as independent external work; do not imply that
  OpenAI or Claude plugin publication approves these hosted transports.
