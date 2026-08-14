# Marketplace submission dossier

**Checked against official platform documentation:** 2026-08-13
**Current release line:** `1.0.0`
**Publication state:** no submission has been made and nothing in this dossier authorizes one.

This is the owner handoff for a future “go” decision. Technical metadata is prefilled. The
remaining items require the owner because they establish legal identity, availability,
repository visibility or distribution form, and—where a hosted service is offered—public policy
and support. Do not invent those values or substitute repository notes for reviewed deployment
policies.

## Readiness snapshot

| Area | Prepared | Still required before submission |
|---|---|---|
| Shared product | Cross-platform package source, README, MIT license, tests, release automation, passed V1 efficacy gate, `1.0.0` source freeze | Immutable `v1.0.0` tag, fresh pinned installs, owner license/trademark confirmation |
| OpenAI | Skills-only package, listing copy, icon, three starter prompts, optional reviewer cases, authoring validation | Verified publisher, Apps Management write access, regions, portal validation, fresh pinned install; public trust URLs are recommended but optional for skills-only |
| Claude | Plugin manifest, self-hosted marketplace, namespaced invocation, install docs, strict package validation | Immutable tag, fresh pinned install, owner-selected public repository/self-hosted route or final ZIP submission, authorized submission, directory-policy acceptance |
| Hosted interview service | Deployable optional source and architecture/privacy notes | Deployment owner, production policies, support/security contacts, retention/processors, deployment review |

OpenAI requires a stable, responsive, complete plugin and rejects trial or demo submissions.
Design Council passed its fixed internal V1 gate in run `20260814T002300Z`: 100/100 calls,
97.50 versus 88.125, +9.375 points, 95% CI [4.625, 14.625], 4 wins, 1 tie, and 0 losses.
Candidate tokens were 1.320392× control and wall time was 1.244173×; raw verification passed
45/45 and exported-bundle verification passed 44/44.
This is not a claim that OpenAI requires that gate or a particular semantic-version string.

## Owner decisions that cannot be prefilled

Record these once, immediately before the release freeze:

| Field | Current state | Owner action |
|---|---|---|
| Public publisher | Intended: **Grant Holt** | Confirm the exact verified OpenAI individual/business identity and authority to accept both platforms' terms |
| Claude distribution form | Private `grantholt-byte/design-council` | Choose a public repository/self-hosted marketplace for direct installs or a final ZIP for the current directory-submission form |
| Website | **NOT SET** | Optional for the skills-only listing; recommended for product trust and required before presenting a hosted service as available |
| Support | **NOT SET** | Optional for the skills-only listing; recommended as a monitored public route and required for a supported hosted service |
| Privacy policy | `docs/privacy.md` is architecture guidance only | Optional for skills-only Core; publish a reviewed deployment-specific policy before collecting data through a hosted service |
| Terms | `docs/terms.md` is a publication placeholder only | Optional for skills-only Core; publish reviewed terms before offering a hosted service or paid entitlement |
| Security contact | Interim private-owner route | Enable a monitored private vulnerability channel/address and define an acknowledgment window |
| Availability | **NOT SET** | Select only regions where support and legal terms are ready |
| License/trademark | MIT release; no trademark policy | Confirm MIT for public distribution and decide whether the Design Council name needs a trademark policy |
| Hosted interview listing scope | Optional app is not bundled in either plugin | Decide whether public copy describes only local/BYO preparation or links to an actually deployed service |

## OpenAI / Codex submission packet

### Prefilled listing

- Submission type: **Skills only**
- Name: **Design Council**
- Short description: **Frame better before building**
- Long description: use `interface.longDescription` from `.codex-plugin/plugin.json`
- Category: **Productivity**
- Logo: square `assets/icon.png`
- Publisher: **Grant Holt**, subject to exact Platform identity verification
- Authentication: none
- MCP server: none
- Plugin UI: none; omit directory screenshots for this skills-only listing
- Starter prompts: the three `interface.defaultPrompt` entries in `.codex-plugin/plugin.json`
- Review cases: `docs/submission-openai-test-cases.md`

Suggested initial release notes:

> Initial public release of Design Council, a skills-only human-centered design workflow for
> ChatGPT and Codex. It includes adaptive Intake, ten persistent Council members, sealed
> divergence and Minority Report, evidence provenance, Inquiry Lab guidance, participatory
> workshops, visual artifact generation, portable project state, prototype-to-learn, and an
> advisory Build Gate. It requires no Design Council account, MCP server, or hosted service.

Recheck that every sentence describes the final package before pasting it into the portal.

### Manual portal sequence

1. Pass the clean, commit-bound V1 release gate and build the final skills bundle.
2. In the publishing OpenAI organization, verify the selected individual/business identity and
   **Apps Management: Write** permission. Organization owners receive this permission by default;
   other submitters need it granted.
3. Decide whether to include optional website, support, privacy, and terms URLs for the skills-only
   listing. Do not use the current architecture notes as production legal pages, and require
   deployment-specific pages before promoting any hosted capability.
4. Open the [plugin portal](https://platform.openai.com/plugins), create **Skills only**, upload
   the final bundle, and paste the prefilled listing, prompts, release notes, and review cases.
5. Select supported regions and complete attestations only after verifying every statement.
6. Submit for review. Resolve portal findings against the submitted commit.
7. Approval does not publish the plugin. Return to the owner for a separate explicit publish
   decision after approval.

### Commerce constraint

Keep the OpenAI plugin's complete core free. Current policy permits plugin commerce only for
physical goods. Do not display digital-service plans, promote hosted-study subscriptions or
Exchange credits, initiate checkout, or link directly to an upgrade transaction. An existing
entitlement may be recognized; an unavailable entitlement may be explained and linked only to a
neutral informational page within current policy. Recheck this rule on submission day.

## Claude Code submission packet

### Prepared distribution

- Self-hosted marketplace: `.claude-plugin/marketplace.json`
- Generated plugin: `dist/claude/design-council`
- Manifest: `dist/claude/design-council/.claude-plugin/plugin.json`
- Marketplace install: `design-council@design-council`
- Explicit skill invocation: `/design-council:design-think`
- License: MIT, subject to owner confirmation for public distribution
- Dependencies: none in the distributed Claude plugin

Once the final repository/tag or a public distribution mirror is available, users can add the
self-hosted marketplace with:

```bash
CLAUDE_CODE_PLUGIN_PREFER_HTTPS=1 \
  claude plugin marketplace add grantholt-byte/design-council@v1.0.0 --scope user
claude plugin install design-council@design-council --scope user
```

`1.0.0` is the current private release. Use the hosted install command only after
`git ls-remote --exit-code` resolves `refs/tags/v1.0.0`; never substitute a moving branch.

### Community review sequence

1. Choose either a public repository/distribution mirror for self-hosted installation or a final
   ZIP accepted by the current directory-submission form. Verify that the selected artifact
   contains the complete installable package and documentation.
2. Run `claude plugin validate dist/claude/design-council --strict` and
   `claude plugin validate . --strict` on that exact commit, then perform a clean install.
3. Review and accept Anthropic's Software Directory Policy and Software Directory Terms as an
   authorized publisher. Confirm all rights, privacy, and support statements are accurate.
4. Submit the public GitHub repository or final ZIP through the
   [Claude.ai form](https://claude.ai/settings/plugins/submit) or
   [Claude Console form](https://platform.claude.com/plugins/submit).
5. Anthropic runs automated validation and safety review before a community listing is added to
   the directory surfaced in Claude Code as `claude-plugins-official`. GitHub-backed updates are
   mirrored and screened automatically after publication.

Directory submission does not imply that Anthropic created or endorsed the plugin. A separate
**Anthropic Verified** badge requires additional quality and safety review, and Anthropic gives no
guarantee that a community plugin will receive it. Keep the GitHub-hosted Design Council
marketplace as the publisher-controlled distribution path regardless of directory outcome.

## Final “go” sequence

When the owner later says to prepare the actual submission:

1. verify the completed V1 gate receipts and final release checks against the exact source;
2. confirm `1.0.0` metadata and regenerate both packages;
3. obtain the owner fields above and insert only verified URLs/identity data;
4. run the complete release, security, package, clean-install, and documentation checks;
5. create the immutable release tag and archive hashes, then complete fresh pinned installs;
6. prepare both platform drafts from this dossier;
7. show the owner the exact final listing, attestations, availability, and commit before any
   external submission; and
8. never convert review approval into publication without a separate explicit instruction.

## Primary references

- OpenAI: [package plugins](https://developers.openai.com/plugins/build/plugins),
  [submit plugins](https://developers.openai.com/plugins/deploy/submission),
  [plugin guidelines and commerce](https://developers.openai.com/plugins/app-guidelines), and
  [App Developer Terms](https://openai.com/policies/developer-apps-terms/)
- Anthropic: [create plugins](https://code.claude.com/docs/en/plugins),
  [plugin marketplaces](https://code.claude.com/docs/en/plugin-marketplaces),
  [plugin reference](https://code.claude.com/docs/en/plugins-reference),
  [submit plugins](https://claude.com/docs/plugins/submit),
  [Software Directory Policy](https://support.claude.com/en/articles/13145358-anthropic-software-directory-policy),
  and [Software Directory Terms](https://support.claude.com/en/articles/13145338-anthropic-software-directory-terms)

Platform rules can change. Recheck all primary sources on the day of submission.
