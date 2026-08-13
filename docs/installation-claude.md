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
`dist/design-council-claude-0.9.0-beta.5.zip` after the beta.5 build completes.

## Invoke Design Council

Claude Code 2.1.216 or later supports the short skill command:

```text
/design-think
```

If another installed skill has the same short name, use the collision-safe namespaced form
`/design-council:design-think`. Natural-language activation also remains available. Legacy
`/design-council:design-council` remains available throughout this beta.

## One-session sideload test

```bash
claude --plugin-dir /absolute/path/to/design-council/dist/claude/design-council
```

Invoke `/design-think` or ask “Meet the Council.” Use `/design-council:design-think` if the
short name collides. Sideloading does not create a persistent installed record.

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
interactive session. Test `/design-think`, the collision-safe
`/design-council:design-think`, implicit activation, and the `design-council:sealed-member`
Agent in a fresh project.

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
  refs/tags/v0.9.0-beta.5
CLAUDE_CODE_PLUGIN_PREFER_HTTPS=1 \
  claude plugin marketplace add grantholt-byte/design-council@v0.9.0-beta.5 --scope user
claude plugin install design-council@design-council --scope user
```

The repository owner must add the installer as a collaborator, and the collaborator must
accept the invitation. `gh auth status` must show that account, while `ls-remote` proves both
private-repository access and availability of the exact `v0.9.0-beta.5` tag. Do not continue
if either check fails. Claude Code otherwise prefers SSH for GitHub shorthand, so the
environment setting above avoids requiring an SSH key. The `local`-scope commands above
remain the repository-specific, no-network development path.

### Move a hosted install to a later beta tag

A GitHub marketplace added with `@v0.9.0-beta.5` is pinned to that immutable ref. A normal
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

The beta.5 package, validator, benchmark reruns, immutable tag, and fresh collaborator install
are pending until the repository release gate finishes. Do not use the beta.5 GitHub commands
until the owner confirms that `v0.9.0-beta.5` has been pushed. After that confirmation,
`v0.9.0-beta.5` is the pinned beta; do not substitute a moving branch.

## Troubleshooting

- Run `claude --version`; update to Claude Code 2.1.216 or later for the unnamespaced
  `/design-think` form, and update if `plugin` commands are unavailable.
- If `/design-think` is ambiguous, use `/design-council:design-think`.
- Validate both the plugin directory and marketplace root with `--strict`.
- Inspect `/plugin` → Errors or `claude plugin details` for component load failures.
- Rebuild `dist/`; do not edit generated package files.
- Third-party marketplaces may be blocked by managed `strictKnownMarketplaces` policy.
- The Claude package intentionally omits the optional OpenAI hook and never invokes
  `sealed_round.py run`; it uses fresh Claude Agent contexts instead.
