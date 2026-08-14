# MightShape 1.0.1 validation report

**Release candidate validated:** 2026-08-14

**Product version:** `1.0.1`

**Stable invocation:** `design-think`

## Outcome

The final local release gate passed **18/18 checks** after the MightShape rebrand and the
Slack, Discord, and Microsoft Teams collaboration merge.

| Boundary | Result |
|---|---|
| OpenAI plugin authoring validator | Pass |
| OpenAI and Claude skill validators | Pass |
| Claude plugin validator, package and marketplace, strict mode | Pass |
| Shared-core drift | Pass: 109 shared files and all ten Human Models identical |
| Product-identity boundary | Pass: 387 source files and 236 archive entries checked |
| Third-party runtime-material boundary | Pass: 687 files/archive entries checked |
| Repository contract | Pass: 10/10 checks, 37 schemas, 21 deterministic scripts, ten Human Models |
| Python unit suite | Pass: 284/284 |
| Shared behavioral contracts | Pass: 137/137, including 76 adversarial cases |
| Cross-platform behavioral mapping | Pass: 137 OpenAI + 137 Claude mappings |
| Interview companion | Pass: 16 tests; one D1 integration test correctly environment-gated |
| Interview lint, typecheck, production build | Pass |
| Collaboration companion | Pass: typecheck and 63/63 Slack/Discord/Teams tests |
| Production dependency audits | Pass: zero known vulnerabilities in either companion |
| Credential-pattern scan | Pass: zero findings in canonical release sources |

The opt-in model-backed V1 outcome gate was completed before the rebrand on the shared
methodological core (`20260814T002300Z`): 100/100 planned model calls, treatment 97.50 versus
control 88.125, a **+9.375-point** difference with 95% CI **[4.625, 14.625]**, four wins, one
tie, and no losses. Candidate generation used 1.320392× control tokens. This is bounded
internal comparative evidence, not a guarantee of performance on every project.

## Release artifacts

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| `mightshape-openai-1.0.1.zip` | 2,000,696 | `2f4018cfd0a3c1772814746a1f0340ade9a3d017e1eb0297acd52dcf33f0272b` |
| `mightshape-claude-1.0.1.zip` | 1,999,620 | `36503e9d9d9149a3ccad83851df7b9dccd92027327c92b29835ca4f6a13caf2c` |

The archives are deterministic, contain one `mightshape/` root, and exclude local numbered
conflict copies. `dist/SHA256SUMS` is the canonical checksum file.

## Public-source installation preflight

The public GitHub repository at `grantholt-byte/mightshape` was tested from exact commit
`dae745ef1e73daf17fbfee6fcfe2219d4d4a79fc` before the final tag was attached.

- Codex Git marketplace add, plugin install, and plugin list passed; the installed cache reported
  `mightshape@mightshape` version `1.0.1`. An isolated ephemeral turn explicitly loaded the
  installed `design-think` skill and correctly identified MightShape's solution-first routing.
- Claude Code cloned the public repository over HTTPS from a temporary release-candidate ref;
  local-scope marketplace add, plugin install, and plugin list passed with
  `mightshape@mightshape` version `1.0.1`.
- A native Claude model turn could not run because the machine's existing OAuth session had
  expired and could not refresh. The failure occurred before any model tokens or plugin behavior;
  it does not invalidate the package/install checks and is not presented as a native behavior pass.

After release, annotated tag `v1.0.1` was independently verified to resolve to final commit
`7f4d8b517f32c407126fcc906328499ca920c3c3`. A second fresh Claude Code local-scope marketplace
install cloned the public repository at that exact tag and installed `mightshape@mightshape`
version `1.0.1` successfully. The public GitHub release exposes both validated package archives
and `SHA256SUMS`, and unauthenticated downloads matched the recorded hashes.

## Collaboration scope

The release includes an optional, separately hosted companion with Slack, Discord, and
Microsoft Teams adapters. Deterministic transport, concurrency, idempotency, sealed-response,
retention, deletion, visual-output, and provenance behavior passed locally. Installing the
Codex or Claude plugin does **not** deploy these bots.

Live workspace acceptance remains operator work because it requires owner-created platform
applications, credentials, workspace/tenant consent, and a deployed endpoint. The bundled
persistence model is single-process; horizontal production deployment requires a transactional
shared store. These limits do not affect the local Codex/Claude skill packages.

## Claim boundary

- The runtime and release packages contain independently authored human-centered design
  instructions and original visuals; the release boundary contains no restricted institutional
  names, branded course materials, or third-party worksheets.
- Legacy `.design-council`, `DESIGN_COUNCIL`, schema IDs, and action identifiers remain only as
  portable data contracts. Narrow former-package fallbacks remain solely for migration.
- The owner selected MightShape after a preliminary knockout screen. This report does not claim
  comprehensive trademark clearance or legal advice.
- Marketplace submission, review approval, publication, and optional chat-platform deployment
  are separate external states and must be reported separately.
