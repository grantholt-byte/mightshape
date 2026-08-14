# Marketplace submission dossier

**Checked against official platform documentation:** 2026-08-13

**Release:** `1.0.0` at immutable tag `v1.0.0`

**Owner authorization:** public submission approved on 2026-08-13
**Commercial status:** free; no paid tier, credits, advertising, checkout, or upgrade path

This dossier is the factual submission handoff. Authorization to submit does not authorize the
agent to invent a legal identity, contact email, availability region, or policy attestation. A
draft, a submission under review, approval, and publication are separate states and must be
reported separately.

## Readiness snapshot

| Area | Completed | Remaining external step |
|---|---|---|
| Shared product | V1 gate, 13/13 release checks, MIT license, immutable tag, archive hashes, clean pinned installs, cross-platform parity | Make the reviewed source public for Claude directory submission |
| OpenAI | Skills-only package, manifest, listing copy, icon, three prompts, required 5 positive/3 negative cases, local validation and clean-context routing tests | Portal draft, verified publisher/permission, availability, attestations, upload scan, Submit for Review |
| Claude | Plugin/marketplace manifests, strict validation, install lifecycle, GitHub tag install, listing copy | Public GitHub source, authorized contact and legal acceptance, directory form submission |
| Hosted interview app | Optional deployable source and deterministic tests | Not part of either marketplace submission and not represented as an operated service |

The fixed internal V1 efficacy gate passed in run `20260814T002300Z`: 100/100 model calls,
97.50 versus 88.125, +9.375 points, 95% CI [4.625, 14.625], 4 wins, 1 tie, and 0 losses.
Candidate tokens were 1.320392× control and wall time was 1.244173×. This is an internal
comparative result, not a platform requirement or a claim of universal effectiveness.

## Values that must come from the authorized account holder

| Field | Prepared state | Required action |
|---|---|---|
| OpenAI developer identity | Intended publisher: **Grant Holt** | Select the matching verified individual or business identity in the publishing organization |
| OpenAI permission | Not observable outside the signed-in portal | Confirm **Apps Management: Write** in the selected organization |
| OpenAI availability | Not selected | Choose only supported countries/regions for which the listing and support posture are accurate |
| OpenAI attestations | Not accepted | Review and accept in the portal after every field and scan is accurate |
| Claude contact email | Not stored in the repository | Enter a monitored address controlled by the publisher |
| Claude legal acceptance | Not accepted | Authorized representative reviews and accepts the Software Directory Terms and Policy |
| Public trust URLs | No deployment-specific policy site | Optional for the OpenAI skills-only validator and optional in the current Claude form; do not misrepresent repository architecture notes as operated-service policies |

## OpenAI / Codex submission packet

### Listing

- Submission type: **Skills only**
- Name: **Design Council**
- Short description: **Frame better before building**
- Long description: `interface.longDescription` in `.codex-plugin/plugin.json`
- Category: **Productivity**
- Developer: **Grant Holt**, subject to exact Platform identity selection
- Logo: `assets/icon.png`
- Authentication: none
- MCP server: none
- Plugin UI: none; omit screenshots
- Starter prompts: the three `interface.defaultPrompt` entries in `.codex-plugin/plugin.json`
- Required reviewer cases: `docs/submission-openai-test-cases.md`
- Website/support/privacy/terms URLs: optional under the current skills-only final-validator rule;
  the general guide recommends public trust URLs. Leave blank rather than fabricate them if the
  live form permits.

### Initial release notes

> Initial public release of Design Council, a free skills-only human-centered design workflow for
> ChatGPT and Codex. It includes adaptive Intake, ten persistent fictional Council members, sealed
> divergence and Minority Report, evidence provenance, Inquiry Lab guidance, participatory
> workshops, visual artifact generation, portable project state, prototype-to-learn, and an
> advisory Build Gate. It requires no Design Council account, MCP server, or hosted service.

### Current OpenAI sequence

1. Open `https://platform.openai.com/plugins` in the publishing organization.
2. Confirm Apps Management write access and select the verified developer identity.
3. Create **Skills only** and upload the exact validated V1 bundle.
4. Enter the listing, three starter prompts, five positive cases, and three negative cases.
5. Select accurate availability and wait for all skill safety/security scans.
6. The authorized publisher reviews the release notes and policy attestations, then selects
   **Submit for Review**.
7. Approval does not publish. After approval, the owner deliberately selects **Publish**.

OpenAI's current commerce policy is also compatible with the owner decision: Design Council makes
no commercial offer and contains no pricing, credits, paid entitlement, advertising, upgrade link,
or checkout.

## Claude Code submission packet

### Public source and listing

- Repository: `https://github.com/grantholt-byte/design-council`
- Path within repository: `dist/claude/design-council`
- Plugin name: **Design Council**
- Description: **Human-centered Design Thinking with a deeply modeled ten-person Council,
  evidence-safe inquiry, participatory workshops, and visual design artifacts.**
- Supported platform: **Claude Code**
- License: **MIT** (set explicitly; do not rely on the form's default)
- Manifest: `dist/claude/design-council/.claude-plugin/plugin.json`
- Explicit invocation: `/design-council:design-think`
- Self-hosted install: `design-council@design-council`
- Contact email: publisher must enter a real monitored address in the form

### Three reviewer examples

1. “Challenge this product idea before we build it, then identify the cheapest useful experiment.”
2. “Open Inquiry Lab, research this unfamiliar role, and build a Reality Packet before any
   synthetic interview.”
3. “Run a sealed Council round and preserve the Minority Report before synthesis.”

### Current Claude sequence

1. Make the submitted GitHub repository public. The current directory does not accept closed-source
   repositories or ZIP uploads.
2. Re-run `claude plugin validate dist/claude/design-council --strict` against the submitted commit.
3. Use the [Console form](https://platform.claude.com/plugins/submit) as a Developer, Admin, or
   Owner, or the [Claude.ai form](https://claude.ai/admin-settings/directory/submissions/plugins/new)
   from an eligible Team/Enterprise organization with directory-management access.
4. Enter the repository URL and path above, listing fields, three examples, Claude Code support,
   MIT license, and the authorized contact email.
5. The authorized publisher reviews and accepts the Software Directory Terms and Policy, then
   submits for review.

Approved third-party plugins enter Anthropic's `claude-community` marketplace and are pinned to a
reviewed commit. `claude-plugins-official` is a separately curated marketplace with no public
application process. There is no documented second publisher “Publish” click for community
approval; the public catalog syncs after approval and later GitHub updates are mirrored and
screened. An **Anthropic Verified** badge is a separate discretionary review and is not promised.

After community approval, the documented install path is:

```bash
claude plugin marketplace add anthropics/claude-plugins-community
claude plugin install design-council@claude-community
```

Until then, the publisher-controlled GitHub marketplace remains installable with:

```bash
CLAUDE_CODE_PLUGIN_PREFER_HTTPS=1 \
  claude plugin marketplace add grantholt-byte/design-council@v1.0.0 --scope user
claude plugin install design-council@design-council --scope user
```

## Submission status record

Update this table only from portal receipts or catalog visibility:

| Surface | State | Receipt |
|---|---|---|
| OpenAI | Authorized; portal state not yet recorded | — |
| Claude community | Authorized; form state not yet recorded | — |
| GitHub source | Private until the publication operation is completed | `v1.0.0` → `e3152c7a41c2afcb22ecd5009ddd051bfb69722e` |

## Primary references

- OpenAI: [submit plugins](https://developers.openai.com/plugins/deploy/submission),
  [submission errors](https://developers.openai.com/plugins/deploy/submission-errors#final-directory-submission),
  and [plugin guidelines](https://developers.openai.com/plugins/app-guidelines)
- Anthropic: [submit a plugin](https://claude.com/docs/plugins/submit),
  [community marketplace](https://code.claude.com/docs/en/plugins#submit-your-plugin-to-the-community-marketplace),
  [Software Directory Policy](https://support.claude.com/en/articles/13145358-anthropic-software-directory-policy),
  and [Software Directory Terms](https://support.claude.com/en/articles/13145338-anthropic-software-directory-terms)

Platform rules can change. Recheck primary sources immediately before each submission or update.
