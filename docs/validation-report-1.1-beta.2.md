# Hunchgarden 1.1.0-beta.2 validation receipt

**Validation date:** 2026-08-14

**Release state:** prepared local beta; not tagged, pushed, submitted, or published

**Working tree:** in-progress release tree; repeat from the final clean commit

## Result

`python3 scripts/release_check.py` passed all 18 checks with no failures.

| Boundary | Result |
|---|---|
| OpenAI package and skill authoring validators | Pass |
| Claude package and marketplace strict validators | Pass |
| Hunchgarden identity guard | Pass; 387 source files and 236 archive entries |
| Third-party runtime branding guard | Pass; 687 files and 258 archive entries |
| Cross-platform drift | Pass; 109 shared files and 10 identical Human Models |
| Repository package contract | Pass; 10/10 checks |
| Python unit tests | Pass; 284 |
| Shared behavioral contracts | Pass; 137, including 76 adversarial |
| Platform behavioral mapping | Pass; 137 OpenAI and 137 Claude mappings |
| Interview companion | Pass; 16 tests, 1 environment-gated D1 skip; lint, typecheck, and production build pass |
| Collaboration service | Pass; typecheck and 63 Slack/Discord/Teams/core tests |
| Production dependency audits | Pass; zero reported vulnerabilities in interview and collaboration apps |
| Credential-pattern scan | Pass; zero findings |

The generated artifacts are:

- `dist/openai/hunchgarden/`
- `dist/claude/hunchgarden/`
- `dist/hunchgarden-openai-1.1.0-beta.2.zip`
- `dist/hunchgarden-claude-1.1.0-beta.2.zip`

`dist/SHA256SUMS` records the current deterministic archive hashes.

## Collaboration guarantees exercised

- physically separate portable workshop state and private platform bindings;
- legacy combined-record migration and crash recovery;
- durable full-retention event claims and optimistic concurrency;
- exact workspace/channel/thread/control binding;
- sealed contribution freeze before reveal;
- immutable delivery-only retry without another synthesis call;
- durable outbound receipts and controller-only best-effort remote deletion;
- retryable local state after partial remote cleanup;
- bounded source-linked PNGs, accessible text fallbacks, and Teams payload limits;
- no ambient channel-history permission or ingestion.

## External gates not represented as passed

- No real Slack workspace, Discord test guild, or Teams tenant was available for credentialed
  install and end-to-end delivery evidence.
- No renamed GitHub repository or immutable `v1.1.0-beta.2` tag has been published, so fresh pinned
  Codex and Claude installs are not yet proven.
- No Hunchgarden OpenAI or Anthropic marketplace submission has been made.
- Hunchgarden has preliminary knockout-search results only. Qualified trademark review across the
  intended regions and services remains required before public relaunch.
- The Teams transport retains a narrow accept-before-durable-claim edge; eliminating it requires a
  transactional ingress queue or equivalent production receipt boundary.
- Scheduled expiry removes local records and artifacts only. Remote channel output requires a live
  controller deletion flow.

This receipt proves the local implementation and package gates stated above. It does not prove
platform approval, legal clearance, production-scale operations, or live third-party delivery.
