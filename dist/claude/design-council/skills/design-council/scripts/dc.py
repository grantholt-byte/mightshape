#!/usr/bin/env python3
"""Command-line interface for Design Council project state."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from dc_core import DesignCouncilError, json_output
from project_state import (
    ADAPTATION_SOURCES,
    FACILITATOR_LEVELS,
    PARTICIPATION_ACTIVITIES,
    PARTICIPATION_KINDS,
    PARTICIPATION_MODES,
    PROVENANCE,
    add_assumption,
    add_evidence,
    add_participation_contribution,
    initialize_project,
    load_project,
    open_participation_prompt,
    participation_action,
    record_council_memory,
    record_gate_override,
    record_participation_guidance,
    record_visual_artifact,
    set_facilitator_level,
    set_mode,
    set_participation_mode,
    set_process_view,
    start_participation,
    validate_state,
)
from score_build_gate import assess_build_gate, apply_gate_assessment
from session_summary import summarize_state


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description="Design Council state and facilitation utilities")
    commands = root.add_subparsers(dest="command", required=True)

    init = commands.add_parser("init", help="Initialize versioned project state")
    init.add_argument("--project-root", default=".")
    init.add_argument("--name", required=True)
    init.add_argument("--prompt", required=True)
    init.add_argument("--proposed-solution")
    init.add_argument("--project-id")

    validate = commands.add_parser("validate", help="Validate project state")
    validate.add_argument("--project-root", default=".")

    show = commands.add_parser("show", help="Show a compact state summary")
    show.add_argument("--project-root", default=".")
    show.add_argument("--json", action="store_true")

    evidence = commands.add_parser("add-evidence", help="Add a provenance-safe evidence item")
    evidence.add_argument("--project-root", default=".")
    evidence.add_argument("--claim", required=True)
    evidence.add_argument("--provenance", choices=sorted(PROVENANCE), required=True)
    evidence.add_argument("--confidence", type=float, required=True)
    evidence.add_argument("--strength", type=int, required=True)
    evidence.add_argument("--source-ref", action="append", default=[])
    evidence.add_argument("--scope")
    evidence.add_argument("--study-id")
    evidence.add_argument("--participant-id")
    evidence.add_argument("--excerpt")
    evidence.add_argument("--consent-allows-quote", action="store_true")

    assumption = commands.add_parser("add-assumption", help="Add an assumption to burn down")
    assumption.add_argument("--project-root", default=".")
    assumption.add_argument("--statement", required=True)
    assumption.add_argument("--risk", choices=["LOW", "MEDIUM", "HIGH"], required=True)
    assumption.add_argument("--importance", choices=["LOW", "MEDIUM", "HIGH"], required=True)
    assumption.add_argument("--status")

    mode = commands.add_parser("mode", help="Record a design-mode transition")
    mode.add_argument("--project-root", default=".")
    mode.add_argument("--to", required=True)
    mode.add_argument("--reason", required=True)
    mode.add_argument("--evidence-id", action="append", default=[])

    memory = commands.add_parser("memory", help="Record one Council member's project memory")
    memory.add_argument("--project-root", default=".")
    memory.add_argument("--member", required=True)
    memory.add_argument("--kind", required=True)
    memory.add_argument("--statement", required=True)
    memory.add_argument("--confidence", type=float)
    memory.add_argument("--evidence-id", action="append", default=[])
    memory.add_argument("--changed-because", action="append", default=[])

    gate = commands.add_parser("gate", help="Assess the advisory Build Gate")
    gate.add_argument("--project-root", default=".")
    gate.add_argument("--apply", action="store_true")

    override = commands.add_parser("override", help="Record 'build it anyway' without erasing risk")
    override.add_argument("--project-root", default=".")
    override.add_argument("--note", required=True)

    view = commands.add_parser("view", help="Set COMPACT, VISIBLE, or WORKSHOP process presentation")
    view.add_argument("--project-root", default=".")
    view.add_argument("--mode", choices=["COMPACT", "VISIBLE", "WORKSHOP"], required=True)

    artifact = commands.add_parser("record-artifact", help="Record a rendered visual manifest in project history")
    artifact.add_argument("--project-root", default=".")
    artifact.add_argument("--manifest", required=True)

    participate_start = commands.add_parser("participate-start", help="Start an optional participatory exercise")
    participate_start.add_argument("--project-root", default=".")
    participate_start.add_argument("--mode", choices=sorted(PARTICIPATION_MODES), default="OBSERVE")
    participate_start.add_argument("--activity", choices=sorted(PARTICIPATION_ACTIVITIES), required=True)
    participate_start.add_argument("--facilitator-level", choices=sorted(FACILITATOR_LEVELS), default="NOVICE_ASSISTED")
    participate_start.add_argument("--round-id")
    participate_start.add_argument("--sealed-phase", choices=["NONE", "PRE_ROUND", "ROUND_A_OPEN", "POST_FREEZE"], default="NONE")

    participate_mode = commands.add_parser("participate-mode", help="Change participation or facilitator mode")
    participate_mode.add_argument("--project-root", default=".")
    participate_mode.add_argument("--session-id", required=True)
    mode_choice = participate_mode.add_mutually_exclusive_group(required=True)
    mode_choice.add_argument("--mode", choices=sorted(PARTICIPATION_MODES))
    mode_choice.add_argument("--facilitator-level", choices=sorted(FACILITATOR_LEVELS))
    participate_mode.add_argument("--change-reason", help="Why facilitator support is changing")
    participate_mode.add_argument(
        "--change-source", choices=sorted(ADAPTATION_SOURCES), default="USER_REQUEST"
    )

    participate_prompt = commands.add_parser("participate-prompt", help="Open one bounded participation prompt")
    participate_prompt.add_argument("--project-root", default=".")
    participate_prompt.add_argument("--session-id", required=True)
    participate_prompt.add_argument("--prompt", required=True)
    participate_prompt.add_argument("--purpose")
    participate_prompt.add_argument("--mindset")
    participate_prompt.add_argument("--example")

    participate_add = commands.add_parser("participate-add", help="Record a USER_PROVIDED workshop contribution")
    participate_add.add_argument("--project-root", default=".")
    participate_add.add_argument("--session-id", required=True)
    participate_add.add_argument("--kind", choices=sorted(PARTICIPATION_KINDS), required=True)
    participate_add.add_argument("--content", required=True)
    participate_add.add_argument("--board-change")
    participate_add.add_argument("--sealed-disposition", choices=["NONE", "COMMON_PACKET_NEXT_ROUND", "HOLD_UNTIL_POST_FREEZE"])

    participate_guide = commands.add_parser("participate-guide", help="Record point-of-use facilitator guidance")
    participate_guide.add_argument("--project-root", default=".")
    participate_guide.add_argument("--session-id", required=True)
    participate_guide.add_argument("--request", choices=["WHY", "EXAMPLE", "DEFINE", "SLOWER", "FASTER", "COACHING"], required=True)
    participate_guide.add_argument("--response", required=True)
    participate_guide.add_argument("--term")
    participate_guide.add_argument("--adaptation-reason", help="Why SLOWER or FASTER is appropriate")
    participate_guide.add_argument(
        "--adaptation-source", choices=sorted(ADAPTATION_SOURCES), default="USER_REQUEST"
    )

    participate_control = commands.add_parser("participate-action", help="Skip, pause, resume, supersede, hand back, exit, or complete")
    participate_control.add_argument("--project-root", default=".")
    participate_control.add_argument("--session-id", required=True)
    participate_control.add_argument("--action", choices=["SKIP", "PAUSE", "RESUME", "UNDO", "HAND_BACK", "EXIT", "COMPLETE"], required=True)
    participate_control.add_argument("--contribution-id")
    participate_control.add_argument("--replacement")
    return root


def run(args: argparse.Namespace) -> dict | str:
    project_root = Path(args.project_root)
    if args.command == "init":
        return initialize_project(project_root, args.name, args.prompt, args.proposed_solution, args.project_id)
    if args.command == "validate":
        return validate_state(load_project(project_root))
    if args.command == "show":
        state = load_project(project_root)
        return state if args.json else summarize_state(state)
    if args.command == "add-evidence":
        return add_evidence(
            project_root,
            args.claim,
            args.provenance,
            args.confidence,
            args.strength,
            args.source_ref,
            args.scope,
            args.study_id,
            args.participant_id,
            args.excerpt,
            True if args.consent_allows_quote else None,
        )
    if args.command == "add-assumption":
        return add_assumption(project_root, args.statement, args.risk, args.importance, args.status)
    if args.command == "mode":
        return set_mode(project_root, args.to, args.reason, args.evidence_id)
    if args.command == "memory":
        return record_council_memory(
            project_root,
            args.member,
            args.kind,
            args.statement,
            args.confidence,
            args.evidence_id,
            args.changed_because,
        )
    if args.command == "gate":
        state = load_project(project_root)
        assessment = assess_build_gate(state)
        if args.apply:
            return apply_gate_assessment(project_root, assessment)
        return assessment
    if args.command == "override":
        return record_gate_override(project_root, args.note)
    if args.command == "view":
        return set_process_view(project_root, args.mode)
    if args.command == "record-artifact":
        return record_visual_artifact(project_root, args.manifest)
    if args.command == "participate-start":
        return start_participation(
            project_root,
            args.mode,
            args.activity,
            args.facilitator_level,
            args.round_id,
            args.sealed_phase,
        )
    if args.command == "participate-mode":
        if args.mode:
            return set_participation_mode(project_root, args.session_id, args.mode)
        return set_facilitator_level(
            project_root,
            args.session_id,
            args.facilitator_level,
            args.change_reason,
            args.change_source,
        )
    if args.command == "participate-prompt":
        return open_participation_prompt(
            project_root,
            args.session_id,
            args.prompt,
            args.purpose,
            args.mindset,
            args.example,
        )
    if args.command == "participate-add":
        return add_participation_contribution(
            project_root,
            args.session_id,
            args.kind,
            args.content,
            args.board_change,
            args.sealed_disposition,
        )
    if args.command == "participate-guide":
        return record_participation_guidance(
            project_root,
            args.session_id,
            args.request,
            args.response,
            args.term,
            args.adaptation_reason,
            args.adaptation_source,
        )
    if args.command == "participate-action":
        return participation_action(
            project_root,
            args.session_id,
            args.action,
            args.contribution_id,
            args.replacement,
        )
    raise DesignCouncilError(f"Unsupported command: {args.command}")


def main() -> int:
    args = parser().parse_args()
    try:
        result = run(args)
    except DesignCouncilError as exc:
        print(f"Design Council error: {exc}", file=sys.stderr)
        return 2
    if isinstance(result, str):
        print(result)
    else:
        json_output(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
