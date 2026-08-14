# Install on OpenAI / Codex

Verified against `codex-cli 0.146.1` and current official documentation on 2026-08-13.
ChatGPT desktop/Codex, ChatGPT Work,
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

## Invoke Design Council

OpenAI surfaces use skill invocation, not an arbitrary plugin-defined slash command:

- Codex: invoke `$design-think`, or open `/skills` and select **Design Think**.
- ChatGPT: invoke `@design-think`.
- Natural-language activation remains available on both surfaces.

An exact `/design-think` slash command cannot be registered by a packaged OpenAI plugin.
Deprecated custom prompts would appear under `/prompts:<name>`, not `/design-think`, and are
not shipped. Legacy `$design-council` remains available for compatibility.

## Test from the local development marketplace

The root `.agents/plugins/marketplace.json` points to the generated package. This path-based
marketplace is for repository-local development; the GitHub source below is the shareable
collaborator install.

```bash
codex plugin marketplace add /absolute/path/to/design-council --json
codex plugin list --available --json
codex plugin add design-council@design-council --json
codex plugin list --json
```

Start a new Codex context and invoke `$design-think` (or choose **Design Think** through
`/skills`), then test an implicit prompt such as “Challenge this product idea before we build
it.” The desktop app may require restart or plugin refresh after a local package changes
because installed plugins are loaded from the plugin cache, not the source directory.

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

For a collaborator who has access to the private repository, after the owner confirms the
immutable `v1.0.0` tag has been created and pushed:

```bash
gh auth status
# If the preceding command reports that you are not logged in:
gh auth login --git-protocol https
gh auth setup-git
git ls-remote --exit-code https://github.com/grantholt-byte/design-council.git \
  refs/tags/v1.0.0
codex plugin marketplace add grantholt-byte/design-council --ref v1.0.0 --json
codex plugin list --marketplace design-council --available --json
codex plugin add design-council@design-council --json
codex plugin list --json
```

The repository owner must add the installer as a collaborator, and the collaborator must
accept the invitation. `gh auth status` must show that account, while `ls-remote` proves both
private-repository access and availability of the exact `v1.0.0` tag. Do not continue
if either check fails. This installs from the immutable release tag rather than the moving
`main` branch.

To move to a later immutable release tag, remove the installed plugin and marketplace, then
repeat the commands above with the new `--ref`. `marketplace upgrade` refreshes a moving
branch; it does not change a marketplace pinned to an older tag.

## Troubleshooting

- Confirm `codex --version` and use current CLI documentation.
- Run `codex plugin marketplace list --json` and confirm the resolved root.
- Run `codex plugin list --available --json` and inspect marketplace/load errors.
- Rebuild before installing; the marketplace targets `dist/`, not canonical source.
- If the skill does not trigger implicitly, verify the plugin is enabled and test explicit
  `$design-think` invocation or `/skills` selection in a new context. In ChatGPT, test
  `@design-think` instead.
- Do not type `/design-think` in Codex expecting a plugin command; arbitrary plugin slash
  aliases are not part of the current OpenAI packaging contract.
- Hooks are optional and trust-gated. Declining the hook must not disable the skill.

The fixed model-backed V1 gate passed in run `20260814T002300Z` from clean beta.8 source commit
`afddbf4ee4b2c7555f8e390d92edd843427ea31c`: 100/100 calls, 97.50 versus 88.125,
+9.375 points, 95% CI [4.625, 14.625], 4 wins, 1 tie, and 0 losses. The raw verifier passed
45/45 checks and the exported verifier passed 44/44. Treat the GitHub commands as usable only when
the documented `git ls-remote --exit-code` preflight resolves `refs/tags/v1.0.0`; record remote
install evidence separately from the immutable source snapshot.
