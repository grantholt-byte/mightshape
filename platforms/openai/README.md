# OpenAI adapter

The repository-root `.codex-plugin/plugin.json`, `hooks/`, and
`skills/mightshape/SKILL.md` are the OpenAI adapter sources. The canonical
methodology, Human Models, Inquiry Lab, schemas, deterministic helpers, and
templates live below `skills/mightshape/` and are copied unchanged into
both platform packages.

Run `python3 scripts/build_packages.py --clean` to materialize the installable
OpenAI package at `dist/openai/mightshape/`.
