#!/usr/bin/env python3
"""Render a compact recovery summary from canonical project state."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from dc_core import DesignCouncilError, json_output, project_file
from project_state import load_project


def summarize_state(state: dict[str, Any]) -> str:
    project = state.get("project", {})
    journey = state.get("journey", {})
    challenge = state.get("challenge", {})
    assumptions = state.get("assumptions", [])
    open_high = [item.get("id") for item in assumptions if item.get("status") == "OPEN_HIGH_RISK"]
    testing = [item.get("id") for item in assumptions if item.get("status") == "TESTING"]
    gate = state.get("build_gate", {})
    minority = state.get("minority_reports", [])
    evidence = state.get("evidence", [])
    human = len({item.get("participant_id") for item in evidence if item.get("provenance") in {"HUMAN_INTERVIEW", "OBSERVED_HUMAN_BEHAVIOR"} and item.get("participant_id")})
    frame = challenge.get("current_problem_frame") or "Not yet framed"
    next_move = "Clarify the smallest decisive unknown"
    if open_high:
        next_move = f"Test the highest-risk open assumption ({open_high[0]})"
    elif testing:
        next_move = f"Complete and interpret the active test ({testing[0]})"
    elif gate.get("status") in {"READY", "READY_WITH_KNOWN_RISK"}:
        next_move = "Proceed within the Build Gate's documented risk boundary"
    lines = [
        f"◇ DESIGN COUNCIL / {project.get('name', 'Untitled project')}",
        f"Mode {journey.get('current_mode', 'UNKNOWN')} · Cycle {journey.get('cycle', '?')} · Revision {state.get('revision', '?')}",
        f"Frame: {frame}",
        f"Evidence: {len(evidence)} records · {human} human participant(s)",
        f"Assumptions: {len(open_high)} open/high · {len(testing)} testing",
        f"◆ Build Gate: {gate.get('status', 'NOT_ASSESSED')}",
        f"Minority Reports preserved: {len(minority)}",
        f"↳ Next move: {next_move}",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Summarize Design Council project state")
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--hook", action="store_true", help="Emit SessionStart additional context JSON")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    try:
        target = project_file(args.project_root)
        if not target.exists():
            if args.hook:
                json_output({"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": ""}})
                return 0
            raise DesignCouncilError(f"No Design Council state at {target}")
        state = load_project(args.project_root)
        summary = summarize_state(state)
        if args.hook:
            json_output({"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": summary}})
        elif args.json:
            json_output({"summary": summary, "revision": state.get("revision")})
        else:
            print(summary)
    except DesignCouncilError as exc:
        print(f"Design Council error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
