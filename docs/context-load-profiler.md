# Static context-load profiler

Use `scripts/profile_context.py` to compare the file footprint of MightShape's
progressive-disclosure routes without running a model:

```bash
python3 scripts/profile_context.py
python3 scripts/profile_context.py --profile quick-look --profile inquiry-lab
python3 scripts/profile_context.py --profile quick-look --json
```

The built-in profiles are Quick Look; a straightforward participatory first prompt; an expert
facilitated workshop; Inquiry Lab route selection; a representative five-member sealed panel;
and a durable visual affinity artifact. Every profile includes the active `SKILL.md`, then only
the resources required by that route. The panel is a stable diagnostic sample, not a prescribed
allocation; a real panel must retain every selected member's complete profile and sealed
independence.

Bytes are exact on-disk UTF-8 bytes. Words are matches of the script's fixed Unicode word
expression. `heuristic_token_estimate` is `ceil(UTF-8 bytes / 4)`: a rough comparison aid, not a
model tokenizer or an exact input/billing-token count. The script makes no model or network call
and excludes user prompts, runtime wrappers, tools, outputs, caching, and provider-specific
tokenization.

Gross, unique-content, and redundant totals are reported separately. Repeated resolved paths and
different files with byte-identical content are named explicitly. To audit a suspected reload,
append it to one profile:

```bash
python3 scripts/profile_context.py --profile quick-look \
  --extra-load skills/mightshape/SKILL.md
```

Use the result to remove accidental reloads and unjustified route stacking. It is a resource
diagnostic, never a quality gate: do not trim evidence provenance, competing frames, dissent,
selected Human Models, or decision-changing experiment branches to satisfy the heuristic.
