---
name: design-think
description: Invoke the installed MightShape Claude Code plugin with the exact /design-think command. Use only when the user explicitly invokes /design-think; do not invoke this alias automatically.
disable-model-invocation: true
allowed-tools:
  - Skill(mightshape:design-think)
  - Skill(mightshape:design-think *)
---

# MightShape command alias

Immediately invoke the installed plugin skill `mightshape:design-think` and pass
`$ARGUMENTS` through unchanged. Preserve the user's current conversational context when no
arguments follow the command.

Do not reproduce or summarize the MightShape methodology in this alias. The namespaced plugin
skill is the single source of runtime instructions, references, scripts, Human Models, project
memory, and sealed-round behavior.

If `mightshape:design-think` is unavailable, stop and explain that the MightShape plugin
must be installed and enabled. Do not silently substitute a partial standalone implementation.
