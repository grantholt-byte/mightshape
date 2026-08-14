# OpenAI marketplace and universal directory

Verified from current official OpenAI plugin and skill documentation on 2026-08-13.

## Distribution paths

1. **Local/repository marketplace:** `.agents/plugins/marketplace.json` for authoring,
   private use, and installation testing. Add with `codex plugin marketplace add`.
2. **Git marketplace:** host the marketplace in Git and add it by GitHub shorthand, Git URL,
   or SSH URL. This is independent distribution; it is not the universal directory.
3. **Workspace publishing:** a workspace admin can publish a local plugin to selected
   workspace roles from ChatGPT Plugins. This stays inside the workspace.
4. **Universal public directory:** submit through the
   [OpenAI plugin submission portal](https://platform.openai.com/plugins). An approved
   plugin must then be explicitly published before it is discoverable across supported
   ChatGPT and Codex surfaces.

There is a real public submission path; no submission has been made by this build.

## Current prerequisites

- OpenAI Platform organization role with **Apps Management: Write**. Organization owners have
  it by default; otherwise the owner must verify or grant it in the publishing organization.
- Verified individual or business identity matching the public publisher.
- Final skills-only bundle for Design Council Core.
- Production listing: name, subtitle, long description, logo, category, website, support,
  privacy-policy, and terms URLs.
- At least five positive and three negative behavioral cases with expected behavior.
- Country/region availability, release notes, and policy attestations.

Design Council is skills-only. The optional interview Site is not an MCP server bundled into
the plugin. Do not add an unnecessary MCP server merely to alter the submission type.

## Current commerce boundary

The current directory policy permits plugin commerce only for physical goods. Design Council
must not sell or promote hosted interviews, digital subscriptions, Exchange credits, or an
indirect freemium upgrade inside the OpenAI plugin. A future adapter may recognize an existing
paid entitlement and may explain an unavailable entitlement within policy. It may link to a
neutral informational plan page, but it must not display plans, promote an upgrade, start
checkout, or link directly to a transaction. Recheck the
[current commerce policy](https://developers.openai.com/plugins/app-guidelines#commerce-and-monetization)
before submission; the free core remains complete without a paid service.

## Prepared metadata

- Display name: **Design Council**
- Tagline: **Think wider. Frame better. Build what matters.**
- Subtitle: **Frame better before building**
- Category: Productivity
- Version: `0.9.0-beta.8` (release candidate; validation must pass before tagging)
- Directory logo/composer icon: square `assets/icon.png` (the wide `assets/logo.png` wordmark
  remains documentation-only)
- Starter prompts: three in `.codex-plugin/plugin.json`
- Test material: `evals/cases/` and `docs/submission-openai-test-cases.md`

The manifest intentionally omits fabricated website, repository, support, privacy-policy,
and terms URLs. The owner must host reviewed pages and add their public HTTPS URLs before
submission. The repository's `docs/privacy.md` and `docs/terms.md` are architecture/publication
notes, not substitutes for the required publisher-specific public policies.
The local release check enforces known portal image and text limits; the submission portal
remains the authoritative validator.

## Validation and installation test

```bash
make validate-openai
python3 ~/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py dist/openai/design-council
python3 ~/.codex/skills/.system/skill-creator/scripts/quick_validate.py dist/openai/design-council/skills/design-council
codex plugin marketplace add /absolute/path/to/design-council --json
codex plugin add design-council@design-council --json
codex plugin list --json
```

The first Python command is Codex's bundled authoring validator, not a substitute for portal
validation. Then run explicit, implicit, negative-routing, Council, Inquiry, and state-persistence tests
in a new context. Clean-up commands are in `docs/installation-openai.md`.

The explicit invocation surface is platform-native: `$design-think` in Codex (or selection
through `/skills`) and `@design-think` in ChatGPT. Current OpenAI plugin packaging does not
allow Design Council to register an arbitrary `/design-think` slash command. Deprecated local
custom prompts would invoke as `/prompts:design-think`, are not plugin-distributed, and are not
shipped. Legacy `$design-council` remains available for beta compatibility.

## Submission checklist

1. Confirm license and publisher/repository identity.
2. Host website, support, reviewed privacy, and terms pages on matching HTTPS domains.
3. Run `make release-check` plus model-backed acceptance evals.
4. Build the final package and inspect archive contents/secrets.
5. Open the portal, select **Skills only**, upload the final skill bundle, and complete the
   verified publisher/listing fields.
6. Enter at least five positive and three negative test cases.
7. Submit for review; respond to actual portal validation/review findings.
8. After approval, publish deliberately. Approval alone does not publish.

Do not submit the beta merely to reserve a listing. OpenAI's guidelines require a stable,
responsive, complete product and reject trial or demo plugins. The repository's move from a beta
version to `1.0.0` is governed by `docs/V1_RELEASE_GATE.md`; this is a Design Council release
decision, not a claim that OpenAI mandates a particular semantic-version string.

The official guidelines say screenshots are optional for plugins with UI and should not be
submitted for plugins without UI. Design Council ships repository demo images for reviewers
and beta users, but its skills-only directory submission should omit UI screenshots unless
OpenAI confirms the optional interview experience qualifies for that listing.

Primary sources: [Package plugins](https://developers.openai.com/plugins/build/plugins),
[Submit plugins](https://developers.openai.com/plugins/deploy/submission), and
[Plugin guidelines](https://developers.openai.com/plugins/app-guidelines),
[Build skills](https://learn.chatgpt.com/docs/build-skills),
[developer commands](https://learn.chatgpt.com/docs/developer-commands?surface=cli), and
[deprecated custom prompts](https://learn.chatgpt.com/docs/custom-prompts).

Beta.8 deterministic package validation and the model-backed release-gate rerun must pass before
tagging; clean pinned-tag installation then remains required. This document describes the prepared route; it does not
claim those remaining gates have passed.
The prefilled fields and remaining owner actions are consolidated in
[`SUBMISSION_DOSSIER.md`](SUBMISSION_DOSSIER.md).
