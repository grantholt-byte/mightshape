# Marketplace submission dossier

**Checked against official platform documentation:** 2026-08-13
**Current release line:** `0.9.0-beta.6`
**Publication state:** no submission has been made and nothing in this dossier authorizes one.

This is the owner handoff for a future “go” decision. Technical metadata is prefilled. The
remaining items require the owner because they establish legal identity, public policy, support,
availability, or repository visibility. Do not invent those values or substitute repository
notes for reviewed public policies.

## Readiness snapshot

| Area | Prepared | Still required before submission |
|---|---|---|
| Shared product | Cross-platform package source, README, MIT license, tests, release automation | V1 efficacy/release gates, final `1.0.0` freeze, owner license/trademark confirmation |
| OpenAI | Skills-only package, listing copy, icon, three starter prompts, five positive and three negative cases | Verified publisher, Apps Management write access, public website/support/privacy/terms URLs, regions, portal validation |
| Claude | Plugin manifest, self-hosted marketplace, namespaced invocation, install docs | Public repository for community review, final strict validation, authorized submission, directory-policy acceptance |
| Hosted interview service | Deployable optional source and architecture/privacy notes | Deployment owner, production policies, support/security contacts, retention/processors, deployment review |

OpenAI requires a stable, responsive, complete plugin and rejects trial or demo submissions.
Design Council therefore remains beta until `docs/V1_RELEASE_GATE.md` passes. This is not a claim
that OpenAI requires a particular semantic-version string.

## Owner decisions that cannot be prefilled

Record these once, immediately before the release freeze:

| Field | Current state | Owner action |
|---|---|---|
| Public publisher | Intended: **Grant Holt** | Confirm the exact verified OpenAI individual/business identity and authority to accept both platforms' terms |
| Public repository | Private `grantholt-byte/design-council` | Choose when to make it public for Claude community review, or create a separate public distribution repository |
| Website | **NOT SET** | Supply a public HTTPS homepage matching the publisher |
| Support | **NOT SET** | Supply a public HTTPS support URL backed by a monitored channel |
| Privacy policy | `docs/privacy.md` is architecture guidance only | Publish a reviewed, deployment-specific HTTPS policy with controller identity, data categories/purposes, recipients, retention, controls, and contact |
| Terms | `docs/terms.md` is a publication placeholder only | Publish reviewed HTTPS terms matching the actual local plugin and any hosted service |
| Security contact | Interim private-owner route | Enable a monitored private vulnerability channel/address and define an acknowledgment window |
| Availability | **NOT SET** | Select only regions where support and legal terms are ready |
| License/trademark | MIT beta; no trademark policy | Confirm MIT for public V1 and decide whether the Design Council name needs a trademark policy |
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
3. Host and review the website, support, privacy, and terms URLs. Do not use the current
   architecture notes as production legal pages.
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
- License: MIT, subject to owner confirmation for public V1
- Dependencies: none in the distributed Claude plugin

Once the final repository/tag is public, users can add the self-hosted marketplace with:

```bash
claude plugin marketplace add grantholt-byte/design-council@v1.0.0 --scope user
claude plugin install design-council@design-council --scope user
```

Treat `v1.0.0` above as a future release target, not an existing tag.

### Community review sequence

1. Make the final repository or a distribution mirror public and verify that the referenced
   commit contains the complete installable package and documentation.
2. Run `claude plugin validate dist/claude/design-council --strict` and
   `claude plugin validate . --strict` on that exact commit, then perform a clean install.
3. Review and accept Anthropic's Software Directory Policy and Software Directory Terms as an
   authorized publisher. Confirm all rights, privacy, and support statements are accurate.
4. Submit through the [Claude Console form](https://platform.claude.com/plugins/submit). A
   Team/Enterprise organization with directory-management access may instead use the Claude.ai
   admin submission form documented by Anthropic.
5. Anthropic runs automated validation and safety review, pins accepted entries to a commit SHA,
   and publishes them on its catalog schedule. The current Claude Code creation guide describes
   third-party submissions as entering `anthropics/claude-plugins-community` under marketplace
   name `claude-community`. A separate Anthropic submission page describes the reviewed directory
   as surfaced under `claude-plugins-official`, with community versus Anthropic Verified status.

Those official pages currently use inconsistent catalog labels. Submission therefore establishes
eligibility for review—not guaranteed placement in a named catalog, official status, or Anthropic
Verified status. Claude Code's creation guide separately says Anthropic chooses the curated
official marketplace at its discretion and provides no application process. Keep the GitHub-hosted
Design Council marketplace as the publisher-controlled distribution path regardless of directory
review outcome.

## Final “go” sequence

When the owner later says to prepare the actual submission:

1. verify all V1 gates against one clean commit;
2. replace beta metadata with the approved stable version and regenerate both packages;
3. obtain the owner fields above and insert only verified URLs/identity data;
4. run the complete release, security, package, clean-install, and documentation checks;
5. create the immutable release tag and archive hashes;
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
  [Software Directory Policy](https://support.claude.com/en/articles/13145358-anthropic-software-directory-policy),
  and [Software Directory Terms](https://support.claude.com/en/articles/13145338-anthropic-software-directory-terms)

Platform rules can change. Recheck all primary sources on the day of submission.
