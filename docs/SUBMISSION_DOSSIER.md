# Marketplace submission dossier

**Checked against official platform documentation:** 2026-08-14

**Prepared release:** `1.0.1`

**Owner authorization:** public submission approved on 2026-08-13
**Commercial status:** free; no paid tier, credits, advertising, checkout, or upgrade path

This dossier is the factual submission handoff. Authorization to submit does not authorize the
agent to invent a legal identity, contact email, availability region, or policy attestation. A
draft, a submission under review, approval, and publication are separate states and must be
reported separately.

## Readiness snapshot

| Area | Completed | Remaining external step |
|---|---|---|
| Shared product | Canonical rebrand, beta packages, MIT license, archive hashes, shared core, preserved legacy state contracts, and a green 18-check local beta gate | Repeat from a final clean commit; obtain name clearance; publish and verify an immutable renamed tag; complete live channel installs |
| OpenAI | Skills-only package, manifest, listing copy, icon, three prompts, required 5 positive/3 negative cases, and local validation | Submit MightShape as a new identity after clearance; verify publisher/permission, availability, attestations, upload scan, and clean pinned install |
| Claude | Plugin/marketplace manifests, strict local validation, and listing copy | Publish the renamed GitHub source/tag, verify a fresh hosted install, accept directory terms, and submit the new namespace |
| Hosted interview app | Optional deployable source and deterministic tests | Not part of either marketplace submission and not represented as an operated service |

The pre-rebrand core passed the fixed internal V1 efficacy gate in run `20260814T002300Z`: 100/100 model calls,
97.50 versus 88.125, +9.375 points, 95% CI [4.625, 14.625], 4 wins, 1 tie, and 0 losses.
Candidate tokens were 1.320392× control and wall time was 1.244173×. This is an internal
comparative result, not a platform requirement or a claim of universal effectiveness.

## Values that must come from the authorized account holder

| Field | Prepared state | Required action |
|---|---|---|
| Product-name clearance | Open; preliminary exact-name screening is not legal clearance | Qualified trademark counsel reviews intended goods, regions, marks, classes, and relevant records before the project claims clearance |
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
- Name: **MightShape**
- Short description: **Shape the right thing**
- Long description: `interface.longDescription` in `.codex-plugin/plugin.json`
- Category: **Productivity**
- Developer: **Grant Holt**, subject to exact Platform identity selection
- Logo: `assets/icon.png`
- Authentication: none
- MCP server: none
- Plugin UI: none; omit screenshots
- Starter prompts: the three `interface.defaultPrompt` entries in `.codex-plugin/plugin.json`
- Required reviewer cases: `docs/submission-openai-test-cases.md`
- Website: `https://github.com/grantholt-byte/mightshape`
- Support: `https://github.com/grantholt-byte/mightshape/issues`
- Privacy/terms URLs: optional under the current skills-only final-validator rule. Leave them blank
  rather than represent architecture notes as operated-service policies if the live form permits.

### Initial release notes

> Initial public release of MightShape, a free skills-only human-centered design workflow for
> ChatGPT and Codex. It includes adaptive Intake, ten persistent fictional Council members, sealed
> divergence and Minority Report, evidence provenance, Inquiry Lab guidance, participatory
> workshops, visual artifact generation, portable project state, prototype-to-learn, and an
> advisory Build Gate. It requires no MightShape account, MCP server, or hosted service.

### Current OpenAI sequence

1. Open `https://platform.openai.com/plugins` in the publishing organization.
2. Confirm Apps Management write access and select the verified developer identity.
3. Create a new **Skills only** plugin named **MightShape** and upload the exact validated beta
   bundle. Do not submit it as a normal update to the former-name listing: OpenAI's update validator
   requires the package name to match the existing plugin identity.
4. Enter the listing, three starter prompts, five positive cases, and three negative cases.
5. Select accurate availability and wait for all skill safety/security scans.
6. The authorized publisher reviews the release notes and policy attestations, then selects
   **Submit for Review**.
7. Approval does not publish. After approval, the owner deliberately selects **Publish**.

OpenAI's current commerce policy is also compatible with the owner decision: MightShape makes
no commercial offer and contains no pricing, credits, paid entitlement, advertising, upgrade link,
or checkout.

## Claude Code submission packet

### Public source and listing

- Repository: `https://github.com/grantholt-byte/mightshape`
- Path within repository: `dist/claude/mightshape`
- Plugin name: **MightShape**
- Description: **Human-centered Design Thinking with a deeply modeled ten-person Council,
  evidence-safe inquiry, participatory workshops, and visual design artifacts.**
- Supported platform: **Claude Code**
- License: **MIT** (set explicitly; do not rely on the form's default)
- Manifest: `dist/claude/mightshape/.claude-plugin/plugin.json`
- Explicit invocation: `/mightshape:design-think`
- Self-hosted install: `mightshape@mightshape`
- Contact email: publisher must enter a real monitored address in the form

### Three reviewer examples

1. “Challenge this product idea before we build it, then identify the cheapest useful experiment.”
2. “Open Inquiry Lab, research this unfamiliar role, and build a Reality Packet before any
   synthetic interview.”
3. “Run a sealed Council round and preserve the Minority Report before synthesis.”

### Current Claude sequence

1. Make the submitted GitHub repository public. The current directory does not accept closed-source
   repositories or ZIP uploads.
2. Re-run `claude plugin validate dist/claude/mightshape --strict` against the submitted commit.
3. Use the [Console form](https://platform.claude.com/plugins/submit) as a Developer, Admin, or
   Owner, or the [Claude.ai form](https://claude.ai/admin-settings/directory/submissions/plugins/new)
   from an eligible Team/Enterprise organization with directory-management access.
4. Enter the repository URL and path above, listing fields, three examples, Claude Code support,
   MIT license, and the authorized contact email.
5. The authorized publisher reviews and accepts the Software Directory Terms and Policy, then
   submits for review.

Approved community submissions appear in the directory surfaced as `claude-plugins-official`.
There is no documented second publisher “Publish” click after approval; later GitHub updates are
mirrored and screened. An **Anthropic Verified** badge is a separate additional review and is not
promised.

After directory approval, the documented install path is:

```bash
claude plugin install mightshape@claude-plugins-official --scope user
```

Until then, the publisher-controlled GitHub marketplace remains installable with:

```bash
CLAUDE_CODE_PLUGIN_PREFER_HTTPS=1 \
  claude plugin marketplace add grantholt-byte/mightshape@v1.0.1 --scope user
claude plugin install mightshape@mightshape --scope user
```

## Submission status record

Update this table only from portal receipts or catalog visibility:

| Surface | State | Receipt |
|---|---|---|
| OpenAI MightShape | Not submitted; new identity required | — |
| Claude MightShape | Not submitted | — |
| GitHub MightShape source | Intended repository not yet published/tagged | — |
| Former OpenAI listing | Published under the former name; migration/delisting is a manual owner action | Existing portal record |

## Primary references

- OpenAI: [submit plugins](https://developers.openai.com/plugins/deploy/submission),
  [submission errors](https://developers.openai.com/plugins/deploy/submission-errors#final-directory-submission),
  and [plugin guidelines](https://developers.openai.com/plugins/app-guidelines)
- Anthropic: [submit a plugin](https://claude.com/docs/plugins/submit),
  [community marketplace](https://code.claude.com/docs/en/plugins#submit-your-plugin-to-the-community-marketplace),
  [Software Directory Policy](https://support.claude.com/en/articles/13145358-anthropic-software-directory-policy),
  and [Software Directory Terms](https://support.claude.com/en/articles/13145338-anthropic-software-directory-terms)

Platform rules can change. Recheck primary sources immediately before each submission or update.
