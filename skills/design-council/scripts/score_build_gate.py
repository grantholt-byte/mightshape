#!/usr/bin/env python3
"""Advisory, reversibility-aware Build Gate scoring."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from dc_core import DesignCouncilError, json_output, load_json, now_utc


def _score_problem(state: dict[str, Any]) -> int:
    score = 0
    challenge = state.get("challenge", {})
    if challenge.get("current_problem_frame"):
        score += 5
    active_povs = [pov for pov in state.get("povs", []) if pov.get("status") == "active"]
    if active_povs:
        best = max((pov.get("heuristic_score") or 0 for pov in active_povs), default=0)
        score += 3 if best >= 21 else 2
    if challenge.get("desired_outcome"):
        score += 2
    return min(10, score)


def assess_build_gate(state: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(state, dict):
        raise DesignCouncilError("project state must be an object")
    classification = state.get("classification", {})
    consequence = classification.get("consequence_of_error", "UNKNOWN")
    reversibility = classification.get("reversibility", "UNKNOWN")
    evidence = state.get("evidence", [])
    human = [item for item in evidence if item.get("provenance") in {"HUMAN_INTERVIEW", "OBSERVED_HUMAN_BEHAVIOR"}]
    authoritative = [item for item in evidence if item.get("provenance") == "AUTHORITATIVE_RESEARCH"]
    synthetic = [item for item in evidence if str(item.get("provenance", "")).startswith("SYNTHETIC_")]
    active_povs = [item for item in state.get("povs", []) if item.get("status") == "active"]
    territories = {item.get("territory") for item in state.get("ideas", []) if item.get("status", "active") != "retired"}
    open_high = [item for item in state.get("assumptions", []) if item.get("status") == "OPEN_HIGH_RISK"]
    testing = [item for item in state.get("assumptions", []) if item.get("status") == "TESTING"]
    completed_experiments = [item for item in state.get("experiments", []) if item.get("hypothesis_status") in {"supported", "weakened", "falsified", "inconclusive"}]
    prototypes = state.get("prototypes", [])
    reality_checks = state.get("reality_checks", [])
    contradictions = [item for item in reality_checks if item.get("outcome") in {"contradicted", "transformed"}]

    problem = _score_problem(state)
    human_grounding = min(10, len({item.get("participant_id") for item in human if item.get("participant_id")}) * 2 + sum(min(3, int(item.get("evidence_strength", 0))) for item in human))
    evidence_quality = min(10, sum(min(2, int(item.get("evidence_strength", 0))) for item in evidence) + min(2, len(authoritative)))
    pov_quality = min(10, round(max((item.get("heuristic_score") or 0 for item in active_povs), default=0) / 3))
    solution_diversity = min(10, len(territories) * 2)
    assumption_learning = min(10, len(completed_experiments) * 3 + len([item for item in state.get("assumptions", []) if item.get("status") in {"RESOLVED", "FALSIFIED"}]) * 2)
    prototype_learning = min(10, len(prototypes) + len(completed_experiments) * 3)
    heuristics = {
        "problem_clarity": problem,
        "human_grounding": human_grounding,
        "evidence_quality": evidence_quality,
        "pov_quality": pov_quality,
        "solution_diversity": solution_diversity,
        "assumption_learning": assumption_learning,
        "prototype_test_learning": prototype_learning,
        "open_high_risk_assumptions": len(open_high),
        "synthetic_human_contradictions": len(contradictions),
        "reversibility": reversibility,
        "consequence_of_error": consequence,
    }
    reasons: list[str] = []
    high_stakes = consequence == "HIGH" or reversibility == "DIFFICULT"
    easy_learning_build = consequence == "LOW" and reversibility == "EASY"
    frame_absent = not state.get("challenge", {}).get("current_problem_frame") and not active_povs
    pivotal_untested = bool(open_high) and not completed_experiments

    if frame_absent and not easy_learning_build:
        status = "REFRAME_FIRST"
        reasons.append("No current problem frame or active POV is recorded.")
    elif problem < 4 and high_stakes:
        status = "REFRAME_FIRST"
        reasons.append("The problem frame is too fragile for a consequential or difficult-to-reverse build.")
    elif pivotal_untested or (high_stakes and human_grounding == 0):
        status = "TEST_FIRST"
        if pivotal_untested:
            reasons.append("At least one open high-risk assumption has no completed experiment.")
        if high_stakes and human_grounding == 0:
            reasons.append("High-consequence or difficult-to-reverse work has no direct human grounding.")
    elif problem >= 7 and (not open_high) and (prototype_learning >= 3 or easy_learning_build) and (human_grounding > 0 or not high_stakes):
        status = "READY"
        reasons.append("The frame and pivotal learning are proportionate to the build's reversibility and consequence.")
    else:
        status = "READY_WITH_KNOWN_RISK" if easy_learning_build or (problem >= 5 and not high_stakes) else "TEST_FIRST"
        reasons.append("Proceed only with the visible uncertainties and a reversible implementation boundary." if status == "READY_WITH_KNOWN_RISK" else "One focused experiment can reduce a material uncertainty before production investment.")

    if synthetic and not human:
        reasons.append("Synthetic signals are present without human evidence; this is Evidence Debt, not proof.")
    if contradictions:
        reasons.append("Synthetic-to-human contradiction or transformation requires the current frame to reflect the Reality Check.")
    if len(territories) < 3 and state.get("ideas"):
        reasons.append("The active solution set covers fewer than three conceptual territories.")
    if testing:
        reasons.append("Some assumptions are still under test; preserve their status rather than implying resolution.")
    return {
        "status": status,
        "assessed_at": now_utc(),
        "heuristics": heuristics,
        "reasons": reasons,
        "unresolved_assumptions": [item.get("id") for item in open_high],
        "risk_formula": "uncertainty × cost_of_being_wrong × irreversibility",
        "advisory": True,
        "override_available": True,
        "note": "A user may say 'build it anyway'; record Design/Evidence Debt and proceed reversibly.",
    }


def apply_gate_assessment(project_root: str | Path, assessment: dict[str, Any]) -> dict[str, Any]:
    from project_state import commit_project, load_project

    required = {"status", "assessed_at", "heuristics", "reasons", "unresolved_assumptions"}
    if not required <= assessment.keys():
        raise DesignCouncilError(f"assessment missing: {', '.join(sorted(required - assessment.keys()))}")
    if assessment["status"] not in {"READY", "READY_WITH_KNOWN_RISK", "TEST_FIRST", "REFRAME_FIRST"}:
        raise DesignCouncilError("invalid Build Gate status")
    state = load_project(project_root)
    existing_override = state.get("build_gate", {}).get("override", {"active": False, "recorded_at": None, "note": None})
    state["build_gate"] = {
        "status": assessment["status"],
        "assessed_at": assessment["assessed_at"],
        "heuristics": assessment["heuristics"],
        "reasons": assessment["reasons"],
        "unresolved_assumptions": assessment["unresolved_assumptions"],
        "override": existing_override,
    }
    return commit_project(project_root, state, "BUILD_GATE_ASSESSED", {"status": assessment["status"]})


def main() -> int:
    parser = argparse.ArgumentParser(description="Assess the advisory Design Council Build Gate")
    parser.add_argument("input", nargs="?", help="Project state JSON file; stdin when omitted")
    args = parser.parse_args()
    try:
        state = load_json(args.input) if args.input else json.load(sys.stdin)
        json_output(assess_build_gate(state))
    except (DesignCouncilError, json.JSONDecodeError) as exc:
        print(f"Design Council error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
