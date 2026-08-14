#!/usr/bin/env python3
"""Optional, read-only context hint for a resumed MightShape project."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any


def _read_input() -> dict[str, Any]:
    try:
        raw = sys.stdin.read()
        value = json.loads(raw) if raw.strip() else {}
        return value if isinstance(value, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def _state_path(payload: dict[str, Any]) -> Path:
    raw_cwd = payload.get("cwd") or os.getcwd()
    return Path(str(raw_cwd)).resolve() / ".design-council" / "project.json"


def main() -> int:
    target = _state_path(_read_input())
    if not target.is_file():
        return 0
    try:
        state = json.loads(target.read_text(encoding="utf-8"))
        if not isinstance(state, dict):
            return 0
        project = state.get("project", {})
        journey = state.get("journey", {})
        gate = state.get("build_gate", {})
        open_assumptions = [
            item.get("id")
            for item in state.get("assumptions", [])
            if item.get("status") in {"OPEN_HIGH_RISK", "OPEN_LOW_RISK", "TESTING"}
        ]
        context = (
            "A versioned MightShape project exists at .design-council/project.json. "
            f"Project: {project.get('name', 'unnamed')}; revision {state.get('revision', '?')}; "
            f"mode {journey.get('current_mode', 'UNKNOWN')}; cycle {journey.get('cycle', '?')}; "
            f"Build Gate {gate.get('status', 'NOT_ASSESSED')}; "
            f"open/testing assumptions: {', '.join(filter(None, open_assumptions)) or 'none'}. "
            "Treat that file and its revision snapshots as canonical; load the design-think skill before mutating it."
        )
        print(
            json.dumps(
                {
                    "hookSpecificOutput": {
                        "hookEventName": "SessionStart",
                        "additionalContext": context,
                    }
                }
            )
        )
    except (OSError, json.JSONDecodeError, TypeError):
        # A convenience hook must never block the core skill.
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
