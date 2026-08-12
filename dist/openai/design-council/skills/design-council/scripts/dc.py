#!/usr/bin/env python3
"""Command-line interface for Design Council project state."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from dc_core import DesignCouncilError, json_output
from project_state import (
    PROVENANCE,
    add_assumption,
    add_evidence,
    initialize_project,
    load_project,
    record_council_memory,
    record_gate_override,
    set_mode,
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
