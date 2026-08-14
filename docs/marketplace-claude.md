# Claude Code marketplace publication

Verified against current official Claude Code documentation on 2026-08-13.

## Self-hosted marketplace

This repository is a valid marketplace root through `.claude-plugin/marketplace.json`. It
points at `dist/claude/design-council`, a self-contained generated plugin. Before sharing:

```bash
make validate-claude
```

Repository-local development install (`local` scope):

```bash
claude plugin marketplace add /absolute/path/to/design-council --scope local
claude plugin install design-council@design-council --scope local
```

After the owner grants private-repository collaborator access and the collaborator accepts
the invitation, verify authentication and the exact release tag before adding the hosted
marketplace in Claude's cross-project `user` scope. Use these commands only when the preflight
resolves the immutable tag:

```bash
gh auth status
# If the preceding command reports that you are not logged in:
gh auth login --git-protocol https
gh auth setup-git
git ls-remote --exit-code https://github.com/grantholt-byte/design-council.git \
  refs/tags/v1.0.0
CLAUDE_CODE_PLUGIN_PREFER_HTTPS=1 \
  claude plugin marketplace add grantholt-byte/design-council@v1.0.0 --scope user
claude plugin install design-council@design-council --scope user
```

`gh auth status` must show the invited GitHub account, and `ls-remote` must succeed. Stop and
resolve authentication, invitation, or tag availability if it does not.

Git-backed relative plugin sources are supported because Claude clones the entire
marketplace. A direct URL to only `marketplace.json` would not resolve this relative source.

## Plugin directory submission

Independent publishers can submit either a public GitHub repository or a ZIP through the current
[Claude.ai plugin submission form](https://claude.ai/settings/plugins/submit) or
[Console plugin submission form](https://platform.claude.com/plugins/submit). Anthropic describes
the resulting directory as community-driven and surfaces it in Claude Code through the built-in
`claude-plugins-official` marketplace. That marketplace name does **not** mean every listing is
created, endorsed, or deeply reviewed by Anthropic.

Submissions receive basic automated review. Only listings that undergo Anthropic's additional
quality and safety review receive an **Anthropic Verified** badge, and the submission route gives
no guarantee that a community plugin will receive that badge. The dependable publisher-controlled
route therefore remains this GitHub-hosted marketplace even after directory submission.

Before submitting, either make the repository/distribution mirror public for the GitHub-backed
route or prepare the accepted final ZIP. Run `claude plugin validate`, and confirm the stable
release, license, security/privacy documentation, README, tests, and publisher rights. Accepted
GitHub-backed listings are mirrored into the directory and later source updates are screened
automatically; review timing varies. No submission has been made.

## Version and updates

The plugin manifest and marketplace entry both target `1.0.0`. Claude Code treats an explicit
version as the update boundary, so every release must bump `VERSION` and regenerate both
packages. `check_cross_platform_drift.py` rejects version mismatch.

The marketplace plugin's primary explicit invocation is `/design-council:design-think`.
Claude plugin skills are always namespaced. Exact `/design-think` requires a separate
explicit-only delegating skill outside the plugin namespace and is not the marketplace invocation.
Install or safely remove that optional alias with `scripts/install_claude_alias.py`; it contains no
duplicate methodology and fails closed if a user modifies it. Legacy
`/design-council:design-council` remains available for compatibility.

For a repository-local development install, rebuild and use the normal marketplace/plugin
update flow:

```bash
make build-claude
claude plugin marketplace update design-council
claude plugin update design-council@design-council --scope local
```

For a hosted `user`-scope install pinned to `@v1.0.0`, normal update commands cannot
move the marketplace to a different immutable tag. When a later release is announced, set the
variable below to that exact tag and re-create the installed marketplace boundary:

```bash
DC_DESIGN_COUNCIL_TAG='REPLACE_WITH_ANNOUNCED_TAG'
claude plugin uninstall design-council@design-council --scope user
claude plugin marketplace remove design-council --scope user
git ls-remote --exit-code https://github.com/grantholt-byte/design-council.git \
  "refs/tags/${DC_DESIGN_COUNCIL_TAG}"
CLAUDE_CODE_PLUGIN_PREFER_HTTPS=1 \
  claude plugin marketplace add \
  "grantholt-byte/design-council@${DC_DESIGN_COUNCIL_TAG}" --scope user
claude plugin install design-council@design-council --scope user
```

The fixed model-backed V1 gate passed in run `20260814T002300Z` from clean beta.8 source commit
`afddbf4ee4b2c7555f8e390d92edd843427ea31c`: 100/100 calls, 97.50 versus 88.125,
+9.375 points, 95% CI [4.625, 14.625], 4 wins, 1 tie, and 0 losses. Raw verification passed
45/45 and exported-bundle verification passed 44/44. Verify `v1.0.0` and a fresh collaborator
install as operational checks; never substitute a moving branch. No directory submission or
publication has occurred.

## Reviewer trust

The package contains the primary `design-think` skill, a legacy compatibility skill, and
one read-only sealed-round Agent. It contains no MCP
server, package dependencies, marketplace payment logic, participant recruitment, or
required hook. The core may write explicit project state and perform user-requested coding;
network research uses the host's normal tools. The optional interview app is source-repo
infrastructure, not a Claude plugin component.

Primary sources: [Create plugins](https://code.claude.com/docs/en/plugins),
[Plugin reference](https://code.claude.com/docs/en/plugins-reference),
[Create marketplaces](https://code.claude.com/docs/en/plugin-marketplaces), and
[Discover plugins](https://code.claude.com/docs/en/discover-plugins), plus
[Submit a plugin](https://claude.com/docs/plugins/submit). The reviewed directory
also applies Anthropic's [Software Directory Policy](https://support.claude.com/en/articles/13145358-anthropic-software-directory-policy)
and [Software Directory Terms](https://support.claude.com/en/articles/13145338-anthropic-software-directory-terms).

The prefilled fields and remaining owner actions are consolidated in
[`SUBMISSION_DOSSIER.md`](SUBMISSION_DOSSIER.md).
