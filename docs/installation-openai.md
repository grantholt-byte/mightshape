# Install on OpenAI / Codex

Verified against `codex-cli 0.146.1` on 2026-08-12. ChatGPT desktop/Codex, ChatGPT Work,
CLI, and other supported surfaces may expose different installation UI; public plugins use
the universal directory shared by ChatGPT and Codex.

## Build and validate

```bash
cd /absolute/path/to/design-council
make build-openai
make validate-openai
```

The installable package is `dist/openai/design-council/` and the deterministic archive is
`dist/design-council-openai-1.0.0.zip`.

## Test from the repository marketplace

The root `.agents/plugins/marketplace.json` points to the generated package.

```bash
codex plugin marketplace add /absolute/path/to/design-council --json
codex plugin list --available --json
codex plugin add design-council@design-council --json
codex plugin list --json
```

Start a new Codex context and invoke `$design-council`, then test an implicit prompt such as
“Challenge this product idea before we build it.” The desktop app may require restart or
plugin refresh after a local package changes because installed plugins are loaded from the
plugin cache, not the source directory.

## Update a local test install

Rebuild, remove the cached plugin, and install it again:

```bash
make build-openai
codex plugin remove design-council@design-council --json
codex plugin add design-council@design-council --json
```

For a Git-backed marketplace, refresh its snapshot first:

```bash
codex plugin marketplace upgrade design-council --json
```

## Uninstall and remove the test marketplace

```bash
codex plugin remove design-council@design-council --json
codex plugin marketplace remove design-council --json
```

Removing the plugin does not erase `.design-council/` project files. Remove project state
only through a deliberate project-data retention decision.

## GitHub marketplace source

After the owner publishes this repository and replaces `<owner>/<repo>`:

```bash
codex plugin marketplace add <owner>/<repo> --ref v1.0.0 --json
codex plugin add design-council@design-council --json
```

The GitHub command is documented but cannot be executed until an owner/repository and tag
exist. Do not publish just to satisfy this test.

## Troubleshooting

- Confirm `codex --version` and use current CLI documentation.
- Run `codex plugin marketplace list --json` and confirm the resolved root.
- Run `codex plugin list --available --json` and inspect marketplace/load errors.
- Rebuild before installing; the marketplace targets `dist/`, not canonical source.
- If the skill does not trigger implicitly, verify the plugin is enabled and test explicit
  `$design-council` invocation in a new context.
- Hooks are optional and trust-gated. Declining the hook must not disable the skill.
