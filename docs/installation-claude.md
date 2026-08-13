# Install on Claude Code

The Claude distribution is generated from the same canonical core as OpenAI. Current Claude
Code plugin syntax is documented at [Create plugins](https://code.claude.com/docs/en/plugins)
and [Plugin marketplaces](https://code.claude.com/docs/en/plugin-marketplaces).

## Build and validate

```bash
cd /absolute/path/to/design-council
make build-claude
make validate-claude
```

`validate-claude` uses an installed `claude` executable when present and falls
back to the current official `@anthropic-ai/claude-code` package through `npx`.
Set `DC_CLAUDE_CLI` to an explicit executable path in controlled build
environments.

The installable package is `dist/claude/design-council/` and the deterministic archive is
`dist/design-council-claude-0.9.0-beta.3.zip`.

## One-session sideload test

```bash
claude --plugin-dir /absolute/path/to/design-council/dist/claude/design-council
```

Invoke `/design-council:design-council` or ask “Meet the Council.” Sideloading does not
create a persistent installed record.

## Test the local development marketplace

The root `.claude-plugin/marketplace.json` points to the generated Claude package.
Use `local` scope for this repository-specific development installation:

```bash
claude plugin marketplace add /absolute/path/to/design-council --scope local
claude plugin install design-council@design-council --scope local
claude plugin list --json
claude plugin details design-council@design-council
```

If installation reports that activation needs a reload, run `/reload-plugins` in an
interactive session. Test `/design-council:design-council`, implicit activation, and the
`design-council:sealed-member` Agent in a fresh project.

## Update a local development install

```bash
make build-claude
claude plugin marketplace update design-council
claude plugin update design-council@design-council --scope local
```

Every release must bump the canonical `VERSION`, Claude manifest, and marketplace version;
the build and drift checks enforce synchronization.

## Remove a local development install

```bash
claude plugin uninstall design-council@design-council --scope local
claude plugin marketplace remove design-council --scope local
```

Plugin removal does not delete `.design-council/` project state unless the user separately
chooses to remove that project data.

## GitHub-hosted marketplace

For a collaborator who has accepted access to the private beta repository, use `user`
scope so Design Council is available across that collaborator's projects:

```bash
gh auth status
# If the preceding command reports that you are not logged in:
gh auth login --git-protocol https
gh auth setup-git
git ls-remote --exit-code https://github.com/grantholt-byte/design-council.git \
  refs/tags/v0.9.0-beta.3
CLAUDE_CODE_PLUGIN_PREFER_HTTPS=1 \
  claude plugin marketplace add grantholt-byte/design-council@v0.9.0-beta.3 --scope user
claude plugin install design-council@design-council --scope user
```

The repository owner must add the installer as a collaborator, and the collaborator must
accept the invitation. `gh auth status` must show that account, while `ls-remote` proves both
private-repository access and availability of the exact `v0.9.0-beta.3` tag. Do not continue
if either check fails. Claude Code otherwise prefers SSH for GitHub shorthand, so the
environment setting above avoids requiring an SSH key. The `local`-scope commands above
remain the repository-specific, no-network development path.

### Move a hosted install to a later beta tag

A GitHub marketplace added with `@v0.9.0-beta.3` is pinned to that immutable ref. A normal
marketplace or plugin update does not move it to another tag. Set the variable below to the
exact later beta tag announced by the owner, then remove and re-add the hosted `user`-scope
installation:

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

The current beta is `v0.9.0-beta.3`; do not change the installed tag until the owner announces
and pushes a later one.

## Troubleshooting

- Run `claude --version`; update Claude Code if `plugin` commands are unavailable.
- Validate both the plugin directory and marketplace root with `--strict`.
- Inspect `/plugin` → Errors or `claude plugin details` for component load failures.
- Rebuild `dist/`; do not edit generated package files.
- Third-party marketplaces may be blocked by managed `strictKnownMarketplaces` policy.
- The Claude package intentionally omits the optional OpenAI hook and never invokes
  `sealed_round.py run`; it uses fresh Claude Agent contexts instead.
