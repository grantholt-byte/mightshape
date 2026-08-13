# Visual Workbench

Use a visual artifact when spatial relationships make an exercise materially easier to inspect. The visual is a derived facilitation view, not a new source of evidence.

V1 supports two portable artifact types:

- `AFFINITY_MAP`: evidence or idea notes grouped into emergent clusters, with outliers preserved in their own visible column;
- `PROCESS_MAP`: evidence-linked steps arranged by actor or system lane, with explicit transitions, branches, gaps, and breakdowns.

## Studio character

The workbench should feel like an active innovation studio, not a corporate reporting dashboard. Affinity records render as tactile sticky notes with mixed paper colors, folded corners, tape, soft shadows, and small deterministic variations. Clusters form colorful dashed neighborhoods; outliers receive their own conspicuous exception zone. Process maps use the same paper language inside lightly drawn actor lanes, with lively handoff paths and sparing doodles. The result may be playful, warm, and a little imperfect while remaining calm enough to inspect.

This is Design Council's own visual language. Do not imitate another company's logo, wordmark, branded typeface, or exact trade dress. Never assign epistemic meaning to paper color, rotation, doodles, or position. Provenance color is only an accent and is always reinforced by a printed mark, label, record ID, and source IDs. Accessibility and evidentiary honesty outrank decoration.

Use `visual-artifact.schema.json` as the input contract and `render_visual.py` to create synchronized outputs:

- normalized source JSON so the exact visual can be reproduced;
- a self-contained HTML workbench with an embedded accessible SVG and complete text fallback;
- a standalone SVG for viewing or embedding;
- Markdown for environments where graphics are unavailable;
- a JSON manifest with the canonical input SHA-256, file names, provenance mix, source IDs, record count, and warnings.

The renderer uses only the Python standard library. It makes no network request, loads no remote font or script, and opens the HTML in the local browser only when `--open` is explicitly supplied. Default output is `.design-council/artifacts/<artifact-id>/`. These files are derived views; canonical evidence and project history remain in project state.

## Render contract

Every note, process step, and transition carries:

- a stable artifact-local ID;
- one Evidence Firewall provenance;
- source IDs where the provenance claims an observed, researched, inferred, or synthetic basis.

The root `summary` and every affinity cluster label/description are synthesis, not raw evidence. Mark them `DESIGN_COUNCIL` and provide `summary_record_ids` or cluster `record_ids` that identify the exact rendered records being interpreted. The renderer rejects summaries that cite missing records and clusters that cite notes outside their own group. Display the facilitator-interpretation label and cited record IDs in the graphical and text views.

Human, authoritative-research, research-supported-inference, and synthetic records without source IDs fail validation. `ASSUMPTION`, `UNKNOWN`, `DESIGN_COUNCIL`, and `USER_PROVIDED` may be source-less, but their weaker status stays visible.

Color never carries meaning alone. The map prints the provenance label and source IDs on each card. The HTML includes a complete text version. User-provided strings are escaped before HTML or SVG rendering.

Do not:

- make invented notes look like observed human evidence;
- hide an outlier to make the cluster wall tidy;
- draw a fictional happy path without marking assumptions and unknowns;
- treat line thickness, card position, cluster size, or visual polish as confidence;
- infer prevalence from the number of notes in a qualitative sample;
- alter canonical project records while rendering an export.

## Affinity map procedure

1. Lock the input set with every record's ID, provenance, and original wording, plus the record count, provenance mix, and known exclusions. If the complete stable-ID deck is already visible in the prompt or immediately preceding context, acknowledge it as locked without echoing it; otherwise display it once. A count-only summary cannot replace a deck that has not yet been shown.
2. Render a first arrangement without naming clusters in advance. The locked deck must be available before any provisional cluster label; the arrangement can refer to its IDs rather than repeating its wording.
3. Test at least one alternate arrangement when the grouping changes a material conclusion.
4. Name clusters after grouping. Keep source IDs on every note.
5. Preserve genuinely unclustered notes in the visually distinct `OUTLIERS — KEEP VISIBLE` column. Keep a contradiction or counterexample beside the theme it qualifies when that relationship is defensible; contradiction alone does not make a record an outlier.
6. State what the clustering suggests, what it does not establish, and which records resist the pattern.
7. Name one concrete next analytical or research move that would test the most consequential interpretation.

For a text-only fallback, show a not-yet-visible locked deck once, then show the arrangement with record IDs rather than repeating each card's full wording. The stable IDs keep the transformation auditable without making the user read the same note twice. A graphical artifact may repeat the wording on moved sticky notes because spatial inspection is the purpose of that view.

The deterministic renderer displays a supplied arrangement; it does not claim that lexical or model-generated grouping is semantic truth. Use `cluster_ideas.py` only as a facilitation aid, then inspect the grouping.

## Process map procedure

1. Define the event boundary and whose process is being represented.
2. Use lanes for meaningfully different actors or systems, not decorative categories.
3. Link each step and transition to its provenance and sources.
4. Show handoffs, branches, loops, missing information, recovery, and workarounds when present.
5. Label unsupported steps `ASSUMPTION` or `UNKNOWN` instead of completing the flow from imagination.
6. End with breakdowns, uncertainties, and the observation or interview that would test them.

## User-visible workshop trace

For substantial brainstorming, synthesis, clustering, or process mapping, use process view `VISIBLE` by default and `WORKSHOP` (shown as `◇ OPEN STUDIO`) when the user wants the fuller exercise. Show meaningful work products at actual phase boundaries; do not narrate private chain-of-thought or stream internal token-by-token reasoning.

Use compact checkpoints such as:

```text
◇ WORKSHOP TRACE · 01 / INPUTS LOCKED
18 records · 6 HUMAN_INTERVIEW · 4 USER_PROVIDED · 8 ASSUMPTION
? Missing: night-shift handoff and exception recovery

◇ WORKSHOP TRACE · 02 / FIRST ARRANGEMENT
4 provisional clusters · 3 outliers retained
Changed since last view: none — first visible arrangement

◇ WORKSHOP TRACE · 03 / ALTERNATE ARRANGEMENT
E-014 moved from “speed” to “unclear ownership.”
Why at the conclusion level: the incident describes a handoff failure, not elapsed time.

◇ WORKSHOP TRACE · 04 / ARTIFACT READY
AFFINITY_MAP VA-003 · HTML + SVG + Markdown
△ Limitation: one participant contributes 7 of 18 notes.
↳ Next move: observe the disputed handoff in context.
```

Allowed visible material includes input IDs/counts, method selected, provisional artifacts, changed groupings, preserved contradictions, conclusion-level rationales, files created, checks run, and the next boundary. Hidden reasoning, private scratch work, and claims about steps that did not run remain excluded.

At each material boundary, preserve the explicit order `INPUTS → TRANSFORMATION → OUTPUT → WHAT CHANGED → NEXT`. Name the method or constraint in `TRANSFORMATION` and cite input/output IDs. A journey rail alone is status, not an inspectable workshop trace.

During a sealed Council round, progress visibility must not break independence. Before freeze, show only operational status such as the common-packet ID and completed-response count. Reveal no member position, idea, or identifying wording. After freeze, the existing Sealed Receipt and anonymous phase ledgers make the work observable.

Avoid performative verbosity. Do not repeat an unchanged wall after every prompt. Show a checkpoint when a user-visible artifact, evidence status, grouping, frame, decision, or next move actually changes. `QUICK_LOOK` may remain compact; `WORKSHOP` can add a complete input ledger and artifact manifest when the user requests it.

## CLI

```bash
python3 <skill>/scripts/render_visual.py artifact.json \
  --project-root /path/to/project
```

To open the local HTML workbench after rendering:

```bash
python3 <skill>/scripts/render_visual.py artifact.json \
  --project-root /path/to/project \
  --open
```

The command treats rendered artifacts as immutable and refuses to overwrite an existing ID. After the complete artifact set is written, it makes the files read-only where the host supports that mode. The manifest records SHA-256 hashes for the normalized source, HTML, SVG, and Markdown outputs. Use a new `VA-` ID for a changed arrangement so the earlier visual remains auditable. It returns a JSON result containing the artifact type, source/visual/manifest paths, input hash, provenance mix, source count, and whether a browser was opened.

For a sustained journey, record the generated manifest without embedding the full HTML/SVG in project state:

```bash
python3 <skill>/scripts/dc.py record-artifact \
  --project-root /path/to/project \
  --manifest /path/to/project/.design-council/artifacts/VA-003/manifest.json
```
