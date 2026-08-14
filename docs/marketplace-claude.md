# Claude Code marketplace publication

Verified against current official Claude Code documentation on 2026-08-14.

Owner authorization to prepare the renamed release is distinct from repository publication,
directory submission, review approval, and catalog visibility; none of those MightShape states is
claimed by this document.

## Self-hosted marketplace

This repository is a valid marketplace root through `.claude-plugin/marketplace.json`. It
points at `dist/claude/mightshape`, a self-contained generated plugin. Before sharing:

```bash
make validate-claude
```

Repository-local development install (`local` scope):

```bash
claude plugin marketplace add /absolute/path/to/mightshape --scope local
claude plugin install mightshape@mightshape --scope local
```

For a private collaborator or, after publication, any GitHub user, verify authentication when
needed and the exact release tag before adding the hosted marketplace in Claude's cross-project
`user` scope. The intended renamed repository/tag is not yet published; use these commands only
when the preflight resolves the immutable tag:

```bash
gh auth status
# If the preceding command reports that you are not logged in:
gh auth login --git-protocol https
gh auth setup-git
git ls-remote --exit-code https://github.com/grantholt-byte/mightshape.git \
  refs/tags/v1.0.1
CLAUDE_CODE_PLUGIN_PREFER_HTTPS=1 \
  claude plugin marketplace add grantholt-byte/mightshape@v1.0.1 --scope user
claude plugin install mightshape@mightshape --scope user
```

For a private repository, `gh auth status` must show an authorized GitHub account. Once the
repository is public, authentication is optional, but `ls-remote` must still prove the immutable
tag is available.

Git-backed relative plugin sources are supported because Claude clones the entire
marketplace. A direct URL to only `marketplace.json` would not resolve this relative source.

## Plugin directory submission

Independent publishers submit a **public GitHub repository** through the current
[Claude.ai plugin submission form](https://claude.ai/admin-settings/directory/submissions/plugins/new)
or [Console plugin submission form](https://platform.claude.com/plugins/submit). Closed-source
repositories are not accepted, and the current form has no ZIP-upload route. Use repository
`https://github.com/grantholt-byte/mightshape` with path
`dist/claude/mightshape`.

Approved community submissions appear in the Claude directory surfaced as
`claude-plugins-official`. **Anthropic Verified** is a separate additional review badge; community
submission does not guarantee that badge. Later source updates are mirrored from the submitted
public GitHub repository and automatically screened.

Before submitting, make the repository public, run `claude plugin validate`, and confirm the stable
release, license, security/privacy documentation, README, tests, and publisher rights. The live
form requires the repository URL, plugin name, description, examples, at least one supported
platform, a contact email, and acceptance of the directory terms. Later source updates are mirrored
and screened automatically; review timing varies. Owner authorization was recorded on 2026-08-13;
record the actual form receipt separately.

After directory approval, install with:

```bash
claude plugin install mightshape@claude-plugins-official --scope user
```

In an interactive Claude Code session, `/plugin install mightshape@claude-plugins-official` is the
equivalent directory flow.

## Version and updates

The plugin manifest and marketplace entry both target `1.0.1`. Claude Code treats an explicit
version as the update boundary, so every release must bump `VERSION` and regenerate both
packages. `check_cross_platform_drift.py` rejects version mismatch.

The marketplace plugin's primary explicit invocation is `/mightshape:design-think`.
Claude plugin skills are always namespaced. Exact `/design-think` requires a separate
explicit-only delegating skill outside the plugin namespace and is not the marketplace invocation.
Install or safely remove that optional alias with `scripts/install_claude_alias.py`; it contains no
duplicate methodology and fails closed if a user modifies it.

For a repository-local development install, rebuild and use the normal marketplace/plugin
update flow:

```bash
make build-claude
claude plugin marketplace update mightshape
claude plugin update mightshape@mightshape --scope local
```

For a hosted `user`-scope install pinned to `@v1.0.1`, normal update commands cannot
move the marketplace to a different immutable tag. When a later release is announced, set the
variable below to that exact tag and re-create the installed marketplace boundary:

```bash
MIGHTSHAPE_RELEASE_TAG='REPLACE_WITH_ANNOUNCED_TAG'
claude plugin uninstall mightshape@mightshape --scope user
claude plugin marketplace remove mightshape --scope user
git ls-remote --exit-code https://github.com/grantholt-byte/mightshape.git \
  "refs/tags/${MIGHTSHAPE_RELEASE_TAG}"
CLAUDE_CODE_PLUGIN_PREFER_HTTPS=1 \
  claude plugin marketplace add \
  "grantholt-byte/mightshape@${MIGHTSHAPE_RELEASE_TAG}" --scope user
claude plugin install mightshape@mightshape --scope user
```

The pre-rebrand core passed the fixed model-backed V1 gate in run `20260814T002300Z` from clean
beta.8 source commit
`afddbf4ee4b2c7555f8e390d92edd843427ea31c`: 100/100 calls, 97.50 versus 88.125,
+9.375 points, 95% CI [4.625, 14.625], 4 wins, 1 tie, and 0 losses. Raw verification passed
45/45 and exported-bundle verification passed 44/44. Those results do not establish the renamed
package's remote installation. Verify an immutable `v1.0.1` tag and a fresh GitHub-backed
install before sharing; never substitute a moving branch. Authorization, form submission,
approval, and catalog visibility remain distinct states.

## Reviewer trust

The package contains the primary `design-think` skill and one read-only sealed-round Agent. It contains no MCP
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
