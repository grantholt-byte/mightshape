
## Claude Code adapter rules

These platform rules override only runtime mechanics; the product constitution
and methodology above remain unchanged.

- Marketplace and `--plugin-dir` installs invoke the primary skill as
  `/design-council:design-think`. Claude plugin skills are always namespaced.
  The exact `/design-think` spelling is available through the optional
  explicit-only delegating alias outside the plugin namespace, which asks Claude to invoke the installed
  `design-council:design-think` skill; it is not a native plugin alias. If Skill
  invocation is denied or the plugin is unavailable, fail visibly rather than
  substituting a partial workflow. Legacy `/design-council:design-council` remains available
  as a V1 compatibility alias. Natural-language auto-discovery remains available
  through the skill description.
- For consequential Round A work, spawn separate fresh-context Agent workers,
  preferably with the plugin agent `design-council:sealed-member`. Give every
  worker the same immutable packet, exactly one Council profile, and only that
  member's project memory. Launch independent workers in parallel when the
  runtime permits; never pass an earlier response to a later worker.
- Wait for the complete response set. Use `sealed_round.py stage`, `freeze`,
  and `anonymize` to validate and freeze supplied responses when useful.
  `sealed_round.py run` is an OpenAI/Codex CLI fallback and must not be invoked
  by the Claude adapter. If Agent workers are unavailable, use
  `FACILITATOR_ONLY` and say the sealed round is deferred.
- ChatGPT Sites is the first-party host used by the optional interview
  companion. Claude Code can develop and inspect `interview-app/`, but cannot
  itself claim a Sites deployment. Never invent an interview URL.
- The optional OpenAI SessionStart hook is not shipped in the Claude package.
  Recover canonical state by reading `.design-council/project.json` when the
  skill activates.

Do not translate these mechanical differences into different Council people,
evidence rules, methodology, or user-facing terminology.
