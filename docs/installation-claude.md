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
`dist/design-council-claude-0.9.0-beta.2.zip`.

## One-session sideload test

```bash
claude --plugin-dir /absolute/path/to/design-council/dist/claude/design-council
```

Invoke `/design-council:design-council` or ask “Meet the Council.” Sideloading does not
create a persistent installed record.

## Test the local marketplace

The root `.claude-plugin/marketplace.json` points to the generated Claude package.

```bash
claude plugin marketplace add /absolute/path/to/design-council --scope local
claude plugin install design-council@design-council --scope local
claude plugin list --json
claude plugin details design-council@design-council
```

If installation reports that activation needs a reload, run `/reload-plugins` in an
interactive session. Test `/design-council:design-council`, implicit activation, and the
`design-council:sealed-member` Agent in a fresh project.

## Update

```bash
make build-claude
claude plugin marketplace update design-council
claude plugin update design-council@design-council --scope local
```

Every release must bump the canonical `VERSION`, Claude manifest, and marketplace version;
the build and drift checks enforce synchronization.

## Uninstall

```bash
claude plugin uninstall design-council@design-council --scope local
claude plugin marketplace remove design-council --scope local
```

Plugin removal does not delete `.design-council/` project state unless the user separately
chooses to remove that project data.

## GitHub-hosted marketplace

For a collaborator who has access to the private beta repository:

```bash
gh auth setup-git
CLAUDE_CODE_PLUGIN_PREFER_HTTPS=1 \
  claude plugin marketplace add grantholt-byte/design-council@v0.9.0-beta.2
claude plugin install design-council@design-council
```

GitHub authentication must grant the collaborator read access. Claude Code otherwise
prefers SSH for GitHub shorthand, so the environment setting above avoids requiring an SSH
key. The local commands above remain the no-network development path.

## Troubleshooting

- Run `claude --version`; update Claude Code if `plugin` commands are unavailable.
- Validate both the plugin directory and marketplace root with `--strict`.
- Inspect `/plugin` → Errors or `claude plugin details` for component load failures.
- Rebuild `dist/`; do not edit generated package files.
- Third-party marketplaces may be blocked by managed `strictKnownMarketplaces` policy.
- The Claude package intentionally omits the optional OpenAI hook and never invokes
  `sealed_round.py run`; it uses fresh Claude Agent contexts instead.
