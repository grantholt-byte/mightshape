# Install on OpenAI / Codex

Verified against `codex-cli 0.146.1` and current official documentation on 2026-08-13.
ChatGPT desktop/Codex, ChatGPT Work,
CLI, and other supported surfaces may expose different installation UI; public plugins use
the universal directory shared by ChatGPT and Codex.

## Build and validate

```bash
cd /absolute/path/to/mightshape
make build-openai
make validate-openai
```

The installable package is `dist/openai/mightshape/` and the deterministic archive is
`dist/mightshape-openai-1.0.1.zip`.

## Invoke MightShape

OpenAI surfaces use skill invocation, not an arbitrary plugin-defined slash command:

- Codex: invoke `$design-think`, or open `/skills` and select **Design Think**.
- ChatGPT: invoke `@design-think`.
- Natural-language activation remains available on both surfaces.

An exact `/design-think` slash command cannot be registered by a packaged OpenAI plugin.
Deprecated custom prompts would appear under `/prompts:<name>`, not `/design-think`, and are
not shipped.

## Test from the local development marketplace

The root `.agents/plugins/marketplace.json` points to the generated package. This path-based
marketplace is for repository-local development; the GitHub source below is the shareable
public install.

```bash
codex plugin marketplace add /absolute/path/to/mightshape --json
codex plugin list --available --json
codex plugin add mightshape@mightshape --json
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
codex plugin remove mightshape@mightshape --json
codex plugin add mightshape@mightshape --json
```

For a Git-backed marketplace, refresh its snapshot first:

```bash
codex plugin marketplace upgrade mightshape --json
```

## Uninstall and remove the test marketplace

```bash
codex plugin remove mightshape@mightshape --json
codex plugin marketplace remove mightshape --json
```

Removing the plugin does not erase `.design-council/` project files. Remove project state
only through a deliberate project-data retention decision.

## GitHub marketplace source

Use the public `grantholt-byte/mightshape` repository and immutable release tag. Prove that the
exact tag resolves before sharing it:

```bash
git ls-remote --exit-code https://github.com/grantholt-byte/mightshape.git \
  refs/tags/v1.0.1
codex plugin marketplace add grantholt-byte/mightshape --ref v1.0.1 --json
codex plugin list --marketplace mightshape --available --json
codex plugin add mightshape@mightshape --json
codex plugin list --json
```

`ls-remote` proves availability of the exact `v1.0.1` tag. Do not continue if it fails. This
installs from the immutable release tag rather than the moving `main` branch.

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

The pre-rebrand core passed the fixed model-backed V1 gate in run `20260814T002300Z` from clean
beta.8 source commit
`afddbf4ee4b2c7555f8e390d92edd843427ea31c`: 100/100 calls, 97.50 versus 88.125,
+9.375 points, 95% CI [4.625, 14.625], 4 wins, 1 tie, and 0 losses. The raw verifier passed
45/45 checks and the exported verifier passed 44/44. Treat the GitHub commands as usable only when
the documented `git ls-remote --exit-code` preflight resolves `refs/tags/v1.0.1`; record
renamed-package remote-install evidence separately from the earlier core evidence.
