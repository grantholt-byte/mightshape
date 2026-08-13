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
the invitation, verify authentication and the exact beta tag before adding the hosted
marketplace in Claude's cross-project `user` scope:

```bash
gh auth status
# If the preceding command reports that you are not logged in:
gh auth login --git-protocol https
gh auth setup-git
git ls-remote --exit-code https://github.com/grantholt-byte/design-council.git \
  refs/tags/v0.9.0-beta.5
CLAUDE_CODE_PLUGIN_PREFER_HTTPS=1 \
  claude plugin marketplace add grantholt-byte/design-council@v0.9.0-beta.5 --scope user
claude plugin install design-council@design-council --scope user
```

`gh auth status` must show the invited GitHub account, and `ls-remote` must succeed. Stop and
resolve authentication, invitation, or tag availability if it does not.

Git-backed relative plugin sources are supported because Claude clones the entire
marketplace. A direct URL to only `marketplace.json` would not resolve this relative source.

## Community marketplace

Anthropic maintains `anthropics/claude-plugins-community`; users add it manually and install
approved entries from marketplace name `claude-community`. Independent publishers can use
the Claude.ai directory submission form (Team/Enterprise directory-management access) or
the Console plugin submission form. The pipeline runs `claude plugin validate`, automated
validation, and safety screening; approved plugins are pinned to a commit SHA and the public
catalog syncs on its schedule.

Prepare a public GitHub repository, stable release tag, license, security/privacy docs,
README, tests, and a clean strict validation result before submitting. No submission has
been made.

## Official curated marketplace

`claude-plugins-official` is a separate Anthropic-curated marketplace. The community form
does **not** put a plugin there. Current Anthropic documentation says there is no application
process for the curated official marketplace; Anthropic chooses entries at its discretion.
Do not promise or market official inclusion.

## Version and updates

The plugin manifest and marketplace entry both target `0.9.0-beta.5`. Claude Code treats an explicit
version as the update boundary, so every release must bump `VERSION` and regenerate both
packages. `check_cross_platform_drift.py` rejects version mismatch.

On Claude Code 2.1.216 or later, the primary explicit invocation is `/design-think`. If that
short name collides with another installed skill, use `/design-council:design-think`. Legacy
`/design-council:design-council` remains available throughout this beta.

For a repository-local development install, rebuild and use the normal marketplace/plugin
update flow:

```bash
make build-claude
claude plugin marketplace update design-council
claude plugin update design-council@design-council --scope local
```

For a hosted `user`-scope install pinned to `@v0.9.0-beta.5`, normal update commands cannot
move the marketplace to a different immutable tag. When a later beta is announced, set the
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

Beta.5 package validation, model-backed benchmark reruns, the immutable tag, and a fresh
collaborator install are pending. After the owner confirms the tag has been pushed, the pinned
beta is exactly `v0.9.0-beta.5`; do not substitute a moving branch.

## Reviewer trust

The package contains the primary `design-think` skill, a legacy beta compatibility skill, and
one read-only sealed-round Agent. It contains no MCP
server, package dependencies, marketplace payment logic, participant recruitment, or
required hook. The core may write explicit project state and perform user-requested coding;
network research uses the host's normal tools. The optional interview app is source-repo
infrastructure, not a Claude plugin component.

Primary sources: [Create plugins](https://code.claude.com/docs/en/plugins),
[Plugin reference](https://code.claude.com/docs/en/plugins-reference),
[Create marketplaces](https://code.claude.com/docs/en/plugin-marketplaces), and
[Discover plugins](https://code.claude.com/docs/en/discover-plugins).
