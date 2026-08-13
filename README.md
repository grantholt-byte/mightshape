# ◇ Design Council

**Think wider. Frame better. Build what matters.**

Design Council is one human-centered design product packaged for OpenAI Codex/ChatGPT and Claude Code. It helps a team keep the energy of “let’s build it” while determining whether the proposed solution addresses the right human problem.

It is more than a prompt pack:

- an adaptive **Empathize ⇄ Define ⇄ Ideate ⇄ Prototype ⇄ Test** engine, with a lightweight Intake layer;
- ten persistent fictional collaborators with complete lives, bounded expertise, contradictions, recognizable voices, and project memory;
- sealed independent generation before cross-pollination, challenge, Minority Report, and synthesis;
- an Inquiry Lab for Reality Packets, research-grounded synthetic people, story-first interviews, real Bring-Your-Own participant studies, and synthetic-to-human Reality Checks;
- strict evidence provenance, revisioned project state, Assumption Burn-down, Design Debt, Evidence Debt, and an advisory Build Gate;
- optional participatory exercises with an adaptive AI facilitator for people who do not already know Design Thinking; and
- a portable, playful Visual Workbench for evidence-linked affinity walls and process maps, plus an inspectable workshop trace that shows real method outputs as they develop.

The core works without a hosted service, custom MCP server, external database, or required hook.

## The journey

```text
                         ◇ DESIGN COUNCIL
                              INTAKE
                                │
        EMPATHIZE ⇄ DEFINE ⇄ IDEATE ⇄ PROTOTYPE ⇄ TEST
             ▲          ▲        ▲          ▲          │
             └──────────┴────────┴──────────┴──────────┘
                                │
                          ◆ BUILD GATE
```

Testing can send a project backward. That is learning, not failure. Straightforward requests such as “implement the toggle in issue.md” route directly to implementation instead of forcing a workshop.

## Signature behavior

**The Council.** Maya, Leo, Priya, Marcus, Elena, Theo, Samira, Jack, Mei, and Rafael are shared byte-for-byte across both platform packages. Consequential rounds use a common packet, isolated first responses, a frozen set, anonymous cross-pollination, forced mutation, convergent challenge, a named **◇ MINORITY REPORT**, and synthesis that never invents consensus.

**Inquiry Lab.** Consequential synthetic inquiry starts with authoritative research and a Reality Packet—not “pretend you are a nurse.” Synthetic participants separate domain grounding, reasonable inference, constructed continuity, and unknowns. They can say “I don’t know,” and their output never becomes human evidence.

**Evidence Firewall.** Every meaningful claim retains provenance such as `HUMAN_INTERVIEW`, `AUTHORITATIVE_RESEARCH`, `SYNTHETIC_PRACTITIONER`, `DESIGN_COUNCIL`, `ASSUMPTION`, or `UNKNOWN`. Confidence and evidence strength are stored separately.

**Participatory exercises.** At a useful exercise boundary, Design Council offers a compact, non-blocking choice: **Watch · Collaborate · One prompt at a time**. Watching remains the default, so work continues if the user does not choose. A joining user can contribute ideas, sort notes, reconstruct a process, map assumptions, shape POVs/HMWs, or design a prototype/test. The facilitator defaults to **novice-assisted** support unless fluency is evident, with **guided** and **light-touch** levels available at any time. It explains the immediate purpose and mindset, gives one method-safe example, and asks one bounded question—not a lecture or giant questionnaire. Before independent ideation, that example uses only an answer shape or distant domain so it does not seed the user's first idea.

**Open Studio.** Substantial sessions show conclusion-level checkpoints, working cards, idea batches, groupings, mutations, exceptions, and outliers at meaningful boundaries. In `WORKSHOP`, each material boundary is inspectable as `INPUTS → TRANSFORMATION → OUTPUT → WHAT CHANGED → NEXT`. Compact mode keeps routine work lean. The trace exposes method artifacts and decisions—not private chain-of-thought, raw logs, or partial sealed responses.

**Visual Workbench.** Affinity clustering and process/journey mapping can produce reproducible source JSON, accessible self-contained HTML and SVG, and a Markdown fallback under `.design-council/artifacts/`. Affinity walls use tactile sticky-note paper, tape, folded corners, colorful cluster neighborhoods, and a visible outlier zone; process maps use playful actor lanes, handoffs, and sparing doodles. The style is warm and whimsical without using decoration as evidence. The same artifacts work across Codex and Claude; a graphical browser is helpful but never required.

**Build Gate.** The advisory result is `READY`, `READY_WITH_KNOWN_RISK`, `TEST_FIRST`, or `REFRAME_FIRST`. “Build it anyway” always remains available; unresolved assumptions are recorded and the implementation stays reversible where practical.

## A compact example

> “I have an excellent idea for an AI app that automatically coordinates family schedules. Let’s build it.”

Design Council preserves momentum, then distinguishes a proposed solution from evidence. A representative journey exposes assumptions about who coordinates, where commitments originate, whether automation is welcome, and whether scheduling or information capture is the real problem. A sealed panel develops competing behavioral and systems frames, preserves the outlier “remove automatic scheduling; surface conflicts,” and proposes a manual coordination-inbox experiment before accounts, calendar integrations, AI extraction, or a production database. The likely initial gate is `TEST_FIRST`, not “never build.”

No interview, observation, or experiment is presented as completed unless it actually occurred.

### Tested output gallery

The first four repository demo images are composed from live acceptance-session outputs dated 2026-08-12. The two Visual Workbench examples use supplied benchmark prompts, not collected interviews; their `P-*` labels are prompt identifiers and remain `USER_PROVIDED`, not verified participants or human evidence.

| Design journey | Sealed Council + Minority Report |
|---|---|
| ![Design Council journey with Intake assumptions and next move](assets/screenshots/01-design-journey.png) | ![Three independent Council perspectives, sealed receipt, and Minority Report](assets/screenshots/02-sealed-council.png) |
| Inquiry Lab Reality Packet | Prototype + Build Gate |
| ![Inquiry Lab Reality Packet separating authoritative research, inference, and missing human evidence](assets/screenshots/03-inquiry-lab.png) | ![Low-fidelity Prototype Card and advisory TEST_FIRST Build Gate](assets/screenshots/04-build-gate.png) |
| Visual affinity wall | Evidence-linked process map |
| ![Illustrative affinity map preserving user-provided source IDs, a counterexample, and an outlier](assets/screenshots/05-affinity-map.png) | ![Illustrative swimlane process map marking supplied transitions and an unknown recovery path](assets/screenshots/06-process-map.png) |

The last two images are rendered directly by the shipped Visual Workbench from the
versioned example JSON under `skills/design-council/assets/examples/`.

## Install the private beta

The beta repository is private. The owner must add the installer as a repository
collaborator, and the collaborator must accept the invitation. On a fresh machine, verify
GitHub CLI authentication and access to the exact immutable beta tag first:

```bash
gh auth status
# If the preceding command reports that you are not logged in:
gh auth login --git-protocol https
gh auth setup-git
git ls-remote --exit-code https://github.com/grantholt-byte/design-council.git \
  refs/tags/v0.9.0-beta.3
```

Do not continue if `ls-remote` fails: the invitation may still need to be accepted, the
GitHub account may be wrong, or the `v0.9.0-beta.3` tag may not be available yet.

### OpenAI / Codex

```bash
codex plugin marketplace add grantholt-byte/design-council --ref v0.9.0-beta.3 --json
codex plugin add design-council@design-council --json
```

Start a fresh context and say `$design-council`, “Meet the Council,” or another natural request. See [OpenAI installation](docs/installation-openai.md) for update, uninstall, clean-context tests, and troubleshooting.

### Claude Code

```bash
CLAUDE_CODE_PLUGIN_PREFER_HTTPS=1 \
  claude plugin marketplace add grantholt-byte/design-council@v0.9.0-beta.3 --scope user
claude plugin install design-council@design-council --scope user
```

Invoke `/design-council:design-council` or use natural language. See [Claude installation](docs/installation-claude.md) for sideloading, update, uninstall, and troubleshooting.

The hosted collaborator install uses Claude's `user` scope so it remains available across
projects. Repository contributors testing a locally built package should instead clone the
tag, run `python3 scripts/build_packages.py --clean`, and use the documented `local`-scope
marketplace commands. Updating a hosted install to a later pinned tag requires uninstalling
the plugin, removing the old marketplace, adding the new tag, and reinstalling; a normal
marketplace update does not change the pinned Git ref.

Generated packages and deterministic archives appear under `dist/`. Do not edit generated packages; `skills/design-council/` is the canonical product core.

## Try it

- “Challenge this idea before we build it.”
- “Run a sealed Council round.”
- “Give me the Minority Report.”
- “Open Inquiry Lab and research this role first.”
- “Create six different synthetic practitioners and interview them independently.”
- “Prepare a human interview in Solution Blackout.”
- “Reality-check this synthetic finding.”
- “Workshop mode: show the brainstorming artifacts as we go.”
- “I’m new to this. Facilitate the exercise one prompt at a time.”
- “Let me collaborate on the brainstorm, then hand it back to you.”
- “Let me sort the notes. Explain only what I need for each move.”
- “Cluster these evidence cards as post-it notes and make an affinity-map visual.”
- “Turn this handoff into an evidence-linked process map.”
- “Turn these findings into competing POVs.”
- “Prototype the riskiest assumption.”
- “Show Design Debt and Evidence Debt.”
- “Check the Build Gate.”
- “Build it anyway.”

Operating depth can switch at any time: `QUICK LOOK`, `SPRINT`, `STANDARD`, or `DEEP DESIGN`.

## Project memory

Sustained projects use a portable, human-readable `.design-council/project.json` record and revision snapshots:

```bash
python3 skills/design-council/scripts/dc.py init \
  --project-root /path/to/project \
  --name "Family coordination" \
  --prompt "Build an AI family scheduler"
```

Frames are superseded rather than erased. Evidence, assumptions, experiments, decisions, Minority Reports, and each member’s prior positions and changes of mind remain traceable across cycles and platforms. Sustained participatory exercises also retain the selected participation/facilitator modes, one-open-prompt ledger, `USER_PROVIDED` contribution IDs, meaningful board changes, pauses, hand-backs, and supersessions.

Switch the visible process view for a sustained project without changing the method:

```bash
python3 skills/design-council/scripts/dc.py view --project-root /path/to/project --mode WORKSHOP
```

## Human interviews and Exchange readiness

`interview-app/` is an optional ChatGPT Sites-compatible text interview experience with explicit AI disclosure, consent, opaque participant IDs, Solution Blackout, adaptive follow-up, stop/delete controls, D1 persistence, and server-only model calls with `store: false`.

Inquiry Lab separates study definition, participant sourcing, interviewing, evidence ingestion, and synthesis. `SYNTHETIC` and `BRING_YOUR_OWN` are functional. The future `◇ DESIGN COUNCIL EXCHANGE` provider returns a structured unavailable status; V1 intentionally includes no recruitment, verification, credits, payments, reputation, or marketplace backend. Exposure levels, Disclosure Guard, minimized external packets, conflict settings, and participant-profile separation make that future provider attachable without rewriting the design engine.

## Architecture and release checks

```text
canonical core
   ├── OpenAI adapter → dist/openai/design-council
   └── Claude adapter → dist/claude/design-council
```

The build copies canonical Human Models, policies, methods, scripts, schemas, and templates into both packages. A hash-based drift check rejects platform divergence.

```bash
python3 -m pip install -r requirements-dev.txt
make build-openai                 # build only the Codex package
make build-claude                 # build only the Claude Code package
make validate-openai              # OpenAI manifest + skill validation
make validate-claude              # Claude strict plugin validation
make check-cross-platform-drift   # rebuild both and prove shared-core parity
make platform-evals               # map the shared corpus to both adapters
make release-check
```

The release gate builds both packages, requires current OpenAI and Claude
validators, checks shared-core drift, runs deterministic and adversarial tests,
runs the interview app's full suite plus lint/typecheck/build and production
dependency audit, and scans for credential patterns. Authenticated model-backed
acceptance runs and clean marketplace installs are documented separately because
they exercise external platform runtimes.

The opt-in paired benchmark compares matched model settings in isolated with-plugin and
without-plugin contexts. It counterbalances arm order and blind labels, then reports outcome
quality separately from token and latency use; judge tokens remain separate from candidate cost.

Two frozen pre-refinement beta3 comparisons answer different questions:

- Against an unassisted raw-prompt session, Design Council improved blind model-judge quality by
  **9.29 points** (95% case-bootstrap CI **6.07–12.74**; 11 wins, 1 tie), meeting the
  preregistered 3-point meaningful-benefit threshold. It used **1.84×** the generation tokens.
- Against a competent frozen one-shot Design Thinking prompt, Design Council scored **93.57**
  versus **95.12** for the prompt-only control: **-1.55 points**, 95% CI **[-4.64, 1.79]**,
  3 wins, 2 ties, 7 losses. The result is **`INCONCLUSIVE`** and used **2.15×** the tokens.
  This run therefore does not establish incremental single-turn value beyond careful prompt
  engineering.

Token use is an optimization target, not an outcome-value veto; the stronger comparator's
quality result would remain inconclusive regardless of token ratio. These are exploratory
internal Codex studies, not native Claude evidence, monetary ROI, or a universal efficacy claim.
Longitudinal trajectories, held-out external prompts, and blind human review are the next tests
for the plugin's intended advantages in persistent reframing, structured divergence, and rapid
evidence-driven iteration. See the [raw-prompt evidence](evals/evidence/ab-benchmark-beta3.json),
[strong-prompt evidence](evals/evidence/ab-benchmark-strong-prompt-beta3.json), and
[eval guide](evals/README.md).

See the [validation report](docs/validation-report.md), [architecture](docs/architecture.md), [publishing checklist](docs/PUBLISHING_CHECKLIST.md), [beta guide](docs/BETA_TEST.md), [OpenAI marketplace path](docs/marketplace-openai.md), and [Claude marketplace path](docs/marketplace-claude.md).

## Privacy and trust

Project state is local by default, but the selected AI platform still processes prompts, files, and tool results under its own terms. External research uses configured host tools. The optional interview app stores study/consent/transcript data in its configured deployment. Disclosure Guard reduces accidental exposure but is not a confidentiality, legal, or DLP guarantee. There is no telemetry or remote research-contribution collector in V1.

Read [privacy](docs/privacy.md) and [security](SECURITY.md) before sharing studies or deploying the interview app.

## Methodology and independence

Design Council uses a human-centered methodology inspired primarily by publicly available Stanford d.school Design Thinking materials. It is an independent product and is not affiliated with or endorsed by Stanford University or the d.school. Supplemental practices and Design Council-original mechanisms are labeled separately in the machine-readable method registry; no Stanford marks or substantial copied source text are included.

See [methodology](docs/methodology.md) and the canonical [source notes](skills/design-council/references/source-notes.md).

## Contributing, security, and license

Read [CONTRIBUTING.md](CONTRIBUTING.md), [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md), and [SECURITY.md](SECURITY.md). The code is licensed under MIT, which keeps installation and collaboration simple while allowing separately operated proprietary hosted services. See [the licensing decision](docs/licensing.md).

## Release status

Version `0.9.0-beta.3` is the synchronized private beta. The tagged GitHub repository is private and has not been published to either marketplace. Public release still requires publisher identity, public support/privacy/terms URLs where applicable, a fresh release audit, and the platforms’ current review or catalog steps.
