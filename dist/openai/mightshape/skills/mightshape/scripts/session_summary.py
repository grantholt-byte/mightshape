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
    visual_artifacts = state.get("visual_artifacts", [])
    participation = state.get("participation_sessions", [])
    active_participation = next(
        (item for item in reversed(participation) if item.get("status") in {"ACTIVE", "PAUSED"}),
        None,
    )
    open_prompt = next(
        (
            item
            for item in reversed(active_participation.get("prompts", []))
            if item.get("status") == "OPEN"
        ),
        None,
    ) if active_participation else None
    process_view = state.get("classification", {}).get("process_view", "VISIBLE")
    human = len({item.get("participant_id") for item in evidence if item.get("provenance") in {"HUMAN_INTERVIEW", "OBSERVED_HUMAN_BEHAVIOR"} and item.get("participant_id")})
    frame = challenge.get("current_problem_frame") or "Not yet framed"
    next_move = "Clarify the smallest decisive unknown"
    if open_high:
        next_move = f"Test the highest-risk open assumption ({open_high[0]})"
    elif testing:
        next_move = f"Complete and interpret the active test ({testing[0]})"
    elif gate.get("status") in {"READY", "READY_WITH_KNOWN_RISK"}:
        next_move = "Proceed within the Build Gate's documented risk boundary"
    if active_participation:
        activity = str(active_participation.get("activity", "exercise")).replace("_", " ").title()
        if open_prompt:
            next_move = f"Resume {activity} at {open_prompt.get('id')}: {open_prompt.get('prompt')}"
        else:
            next_move = f"Resume {activity} from board revision {active_participation.get('board_revision', 0)}"
    mode_labels = {
        "OBSERVE": "Watch",
        "COLLABORATE": "Collaborate",
        "FACILITATED_TURN_BY_TURN": "One prompt at a time",
    }
    guidance_labels = {
        "NOVICE_ASSISTED": "More context",
        "GUIDED": "Guided",
        "LIGHT_TOUCH": "Light",
    }
    mode_line = (
        f"Mode {journey.get('current_mode', 'UNKNOWN')} · Cycle {journey.get('cycle', '?')} · "
        f"Revision {state.get('revision', '?')} · View {process_view}"
    )
    if journey.get("starting_point") and journey.get("starting_point") != "UNSURE":
        mode_line = (
            f"Starting point {journey['starting_point']} "
            f"({journey.get('starting_point_basis', 'INFERRED').lower()}) · {mode_line}"
        )
    lines = [
        f"◇ MIGHTSHAPE / {project.get('name', 'Untitled project')}",
        mode_line,
        *(
            [f"Current decision: {journey['current_decision']}"]
            if journey.get("current_decision")
            else []
        ),
        f"Frame: {frame}",
        f"Evidence: {len(evidence)} records · {human} human participant(s)",
        f"Assumptions: {len(open_high)} open/high · {len(testing)} testing",
        f"◆ Build Gate: {gate.get('status', 'NOT_ASSESSED')}",
        f"Minority Reports preserved: {len(minority)}",
        f"Visual artifacts: {len(visual_artifacts)}",
        "Participation: "
        + (
            f"{active_participation.get('id')} · {active_participation.get('status')} · "
            f"{str(active_participation.get('activity', 'exercise')).replace('_', ' ').title()} · "
            f"Mode {mode_labels.get(active_participation.get('mode'), active_participation.get('mode'))} · "
            f"Guidance {guidance_labels.get(active_participation.get('facilitator_level'), active_participation.get('facilitator_level'))} · "
            f"Pace {active_participation.get('guidance_state', {}).get('pace', 'STANDARD').title()} · "
            f"Board r{active_participation.get('board_revision', 0)}"
            if active_participation
            else "none active"
        ),
        *(
            [f"Open prompt {open_prompt.get('id')}: {open_prompt.get('prompt')}"]
            if open_prompt
            else []
        ),
        f"↳ Next move: {next_move}",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Summarize MightShape project state")
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
            raise DesignCouncilError(f"No MightShape state at {target}")
        state = load_project(args.project_root)
        summary = summarize_state(state)
        if args.hook:
            json_output({"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": summary}})
        elif args.json:
            json_output({"summary": summary, "revision": state.get("revision")})
        else:
            print(summary)
    except DesignCouncilError as exc:
        print(f"MightShape error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
