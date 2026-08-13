---
name: design-think
description: Invoke the installed Design Council Claude Code plugin with the exact /design-think command. Use only when the user explicitly invokes /design-think; do not invoke this alias automatically.
disable-model-invocation: true
allowed-tools:
  - Skill(design-council:design-think)
  - Skill(design-council:design-think *)
---

# Design Council command alias

Immediately invoke the installed plugin skill `design-council:design-think` and pass
`$ARGUMENTS` through unchanged. Preserve the user's current conversational context when no
arguments follow the command.

Do not reproduce or summarize the Design Council methodology in this alias. The namespaced plugin
skill is the single source of runtime instructions, references, scripts, Human Models, project
memory, and sealed-round behavior.

If `design-council:design-think` is unavailable, stop and explain that the Design Council plugin
must be installed and enabled. Do not silently substitute a partial standalone implementation.
