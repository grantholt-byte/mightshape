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
`dist/design-council-claude-1.0.0.zip`.

## Invoke Design Council

Marketplace and `--plugin-dir` installs use Claude's mandatory plugin namespace:

```text
/design-council:design-think
```

Natural-language activation also remains available. Exact `/design-think` is possible only
through a separately installed delegating skill outside the plugin namespace; a marketplace
plugin cannot register that unnamespaced command itself. Legacy
`/design-council:design-council` remains available for compatibility.

### Optional exact `/design-think` command

Claude namespaces every skill shipped by a plugin. If the shorter spelling matters, keep the
plugin installed and add the shipped explicit-only alias from the same pinned source checkout:

```bash
cd /absolute/path/to/design-council
python3 scripts/install_claude_alias.py --scope user
```

Then invoke:

```text
/design-think
```

The alias contains no duplicate methodology. It passes arguments to
`/design-council:design-think`, so the installed plugin remains the source of Human Models,
references, scripts, project memory, and sealed-round behavior. The installer is idempotent and
refuses to overwrite an existing personal skill unless the user reviews it and explicitly adds
`--force`. Use `--scope project --project-root /absolute/project/path` instead for a shared
project skill. Because the alias is explicit-only, it does not compete with the plugin's natural
language activation. It relies on Claude's Skill tool to delegate: if that tool is denied, a
higher-priority `design-think` skill shadows it, or the plugin is disabled, use the native
`/design-council:design-think` command instead.

Remove only an unmodified copy installed from this checkout with:

```bash
python3 scripts/install_claude_alias.py --scope user --uninstall
```

For project scope, add `--scope project --project-root /absolute/project/path`. The uninstaller
fails closed if the skill has changed and preserves every sibling file; review a modified alias
before removing it manually.

## One-session sideload test

```bash
claude --plugin-dir /absolute/path/to/design-council/dist/claude/design-council
```

Invoke `/design-council:design-think` or ask “Meet the Council.” Sideloading does not create a
persistent installed record.

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
interactive session. Test `/design-council:design-think`, implicit activation, and the
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

For a collaborator who has accepted access to the private repository, use `user` scope so
Design Council is available across that collaborator's projects after the owner confirms the
immutable `v1.0.0` tag has been created and pushed:

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

The repository owner must add the installer as a collaborator, and the collaborator must
accept the invitation. `gh auth status` must show that account, while `ls-remote` proves both
private-repository access and availability of the exact `v1.0.0` tag. Do not continue
if either check fails. Claude Code otherwise prefers SSH for GitHub shorthand, so the
environment setting above avoids requiring an SSH key. The `local`-scope commands above
remain the repository-specific, no-network development path.

### Move a hosted install to a later release tag

A GitHub marketplace added with `@v1.0.0` is pinned to that immutable ref. A normal
marketplace or plugin update does not move it to another tag. Set the variable below to the
exact later release tag announced by the owner, then remove and re-add the hosted `user`-scope
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

The fixed model-backed V1 gate passed in run `20260814T002300Z` from clean beta.8 source commit
`afddbf4ee4b2c7555f8e390d92edd843427ea31c`: 100/100 calls, 97.50 versus 88.125,
+9.375 points, 95% CI [4.625, 14.625], 4 wins, 1 tie, and 0 losses. The raw verifier passed
45/45 checks and the exported verifier passed 44/44. Use the hosted GitHub commands only when the
documented `git ls-remote --exit-code` preflight resolves `refs/tags/v1.0.0`; always use that
immutable tag rather than a moving branch, and record remote install evidence separately.

## Troubleshooting

- Run `claude --version`; update if `plugin` commands are unavailable.
- Use `/design-council:design-think` for every plugin or marketplace install. Exact
  `/design-think` requires the optional explicit-only alias above and still delegates to the
  installed plugin.
- Validate both the plugin directory and marketplace root with `--strict`.
- Inspect `/plugin` → Errors or `claude plugin details` for component load failures.
- Rebuild `dist/`; do not edit generated package files.
- Third-party marketplaces may be blocked by managed `strictKnownMarketplaces` policy.
- The Claude package intentionally omits the optional OpenAI hook and never invokes
  `sealed_round.py run`; it uses fresh Claude Agent contexts instead.
