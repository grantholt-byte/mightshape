#!/usr/bin/env python3
"""Score a Point of View with the documented 30-point facilitation heuristic."""

from __future__ import annotations

import argparse
import json
import re
import sys
from typing import Any

from dc_core import DesignCouncilError, json_output, load_json


DIMENSIONS = ("human_centered", "evidence_grounded", "specific", "insightful", "generative", "solution_independent")
SOLUTION_TERMS = {
    "app", "application", "platform", "dashboard", "chatbot", "assistant", "ai", "calendar",
    "notification", "feature", "website", "portal", "tool", "software", "algorithm", "automation",
}
VAGUE_USERS = {"user", "users", "people", "everyone", "customer", "customers", "stakeholder", "stakeholders"}
GENERIC_INSIGHTS = {"busy", "easy", "easier", "convenient", "better", "frustrated", "need help", "want simplicity"}


def solution_terms(text: str) -> list[str]:
    words = set(re.findall(r"[a-z][a-z-]+", text.lower()))
    return sorted(words & SOLUTION_TERMS)


def _clamp(value: int) -> int:
    return max(0, min(5, value))


def score_pov(pov: dict[str, Any]) -> dict[str, Any]:
    user = str(pov.get("user", "")).strip()
    need = str(pov.get("need", "")).strip()
    insight = str(pov.get("insight", "")).strip()
    evidence_ids = pov.get("evidence_ids", [])
    if not user or not need or not insight:
        raise DesignCouncilError("POV requires non-empty user, need, and insight fields")
    if not isinstance(evidence_ids, list):
        raise DesignCouncilError("evidence_ids must be an array")

    need_contamination = solution_terms(need)
    all_contamination = solution_terms(f"{need} {insight}")
    user_words = user.lower().split()
    human_centered = 2 if user.lower() in VAGUE_USERS else 4
    if len(user_words) >= 4:
        human_centered += 1
    evidence_grounded = _clamp(1 + min(4, len(set(str(item) for item in evidence_ids))))
    specificity = 2
    if len(user_words) >= 3:
        specificity += 1
    if len(need.split()) >= 6:
        specificity += 1
    if any(token in insight.lower() for token in ("when", "because", "while", "but", "rather than", "turning", "even though")):
        specificity += 1
    specificity = _clamp(specificity)
    insight_lower = insight.lower()
    insightful = 1
    if len(insight.split()) >= 10:
        insightful += 1
    if any(token in insight_lower for token in ("because", "but", "tension", "tradeoff", "rather than", "even when", "turns", "reveals")):
        insightful += 2
    if not any(phrase in insight_lower for phrase in GENERIC_INSIGHTS):
        insightful += 1
    insightful = _clamp(insightful)
    generative = 2
    if len(need.split()) >= 5:
        generative += 1
    if any(token in insight_lower for token in ("because", "tension", "tradeoff", "rather than", "without")):
        generative += 1
    if not need_contamination:
        generative += 1
    generative = _clamp(generative)
    solution_independent = _clamp(5 - min(5, len(all_contamination) * 2) - (2 if need_contamination else 0))

    scores = {
        "human_centered": human_centered,
        "evidence_grounded": evidence_grounded,
        "specific": specificity,
        "insightful": insightful,
        "generative": generative,
        "solution_independent": solution_independent,
    }
    total = sum(scores.values())
    interpretation = "STRONG_FRAME" if total >= 26 else "PROMISING" if total >= 21 else "FRAGILE" if total >= 15 else "REFRAME"
    cautions = []
    if need_contamination:
        cautions.append(f"Need may contain a hidden solution: {', '.join(need_contamination)}")
    if not evidence_ids:
        cautions.append("No traceable evidence IDs; confidence would not repair this grounding gap")
    if user.lower() in VAGUE_USERS:
        cautions.append("User is generic; specify a situated person or group")
    if insightful <= 2:
        cautions.append("Insight reads as an observation or generality rather than a revealing mechanism")
    return {
        "heuristic": "POV_0_TO_30_V1",
        "scores": scores,
        "total": total,
        "maximum": 30,
        "interpretation": interpretation,
        "solution_contamination": {"detected": bool(need_contamination), "terms": need_contamination},
        "cautions": cautions,
        "advisory": "This is facilitation guidance, not a scientific measure.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Score a Design Council POV")
    parser.add_argument("input", nargs="?", help="POV JSON file; stdin when omitted")
    args = parser.parse_args()
    try:
        value = load_json(args.input) if args.input else json.load(sys.stdin)
        if not isinstance(value, dict):
            raise DesignCouncilError("input must be a JSON object")
        json_output(score_pov(value))
    except (DesignCouncilError, json.JSONDecodeError) as exc:
        print(f"Design Council error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
