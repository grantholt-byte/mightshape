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
`dist/design-council-openai-0.9.0-beta.6.zip` after the beta.6 build completes.

## Invoke Design Council

OpenAI surfaces use skill invocation, not an arbitrary plugin-defined slash command:

- Codex: invoke `$design-think`, or open `/skills` and select **Design Think**.
- ChatGPT: invoke `@design-think`.
- Natural-language activation remains available on both surfaces.

An exact `/design-think` slash command cannot be registered by a packaged OpenAI plugin.
Deprecated custom prompts would appear under `/prompts:<name>`, not `/design-think`, and are
not shipped. Legacy `$design-council` remains available throughout this beta.

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

For a collaborator who has access to the private beta repository:

```bash
gh auth status
# If the preceding command reports that you are not logged in:
gh auth login --git-protocol https
gh auth setup-git
git ls-remote --exit-code https://github.com/grantholt-byte/design-council.git \
  refs/tags/v0.9.0-beta.6
codex plugin marketplace add grantholt-byte/design-council --ref v0.9.0-beta.6 --json
codex plugin list --marketplace design-council --available --json
codex plugin add design-council@design-council --json
codex plugin list --json
```

The repository owner must add the installer as a collaborator, and the collaborator must
accept the invitation. `gh auth status` must show that account, while `ls-remote` proves both
private-repository access and availability of the exact `v0.9.0-beta.6` tag. Do not continue
if either check fails. This installs from the immutable beta tag rather than the moving
`main` branch.

To move to a later immutable beta tag, remove the installed plugin and marketplace, then
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

The beta.6 package and deterministic validators pass. Model-backed benchmark reruns, the immutable
tag, and the pinned-tag clean install remain pending. Do not share the beta.6 GitHub commands as
validated before the owner confirms those remaining steps.
