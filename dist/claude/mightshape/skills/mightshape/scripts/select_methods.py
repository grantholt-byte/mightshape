#!/usr/bin/env python3
"""Deterministically narrow the MightShape method registry.

The router is deliberately modest: it ranks plausible methods and explains why;
it does not replace facilitator judgment or claim that a score is scientific.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from dc_core import DesignCouncilError, REFERENCE_ROOT, json_output, load_json


VALID_MODES = {"INTAKE", "EMPATHIZE", "DEFINE", "IDEATE", "PROTOTYPE", "TEST"}
VALID_ARCHETYPES = {
    "DIGITAL_PRODUCT", "AI_PRODUCT", "PHYSICAL_PRODUCT", "SERVICE", "EXPERIENCE",
    "BUSINESS_MODEL", "WORKFLOW", "ORGANIZATIONAL", "POLICY", "SOCIAL_SYSTEM", "HYBRID",
}
EFFORT_MINUTES = {"low": 20, "medium": 75, "high": 180}

ARCHETYPE_SIGNALS = {
    "DIGITAL_PRODUCT": {"usability-test", "clickable-mock", "journey-mapping", "observation"},
    "AI_PRODUCT": {"assumption-mapping", "inquiry-lab", "wizard-of-oz", "human-only", "technical-proof"},
    "PHYSICAL_PRODUCT": {"observation", "immersion", "physical-mock", "extreme-users", "prototype-to-learn"},
    "SERVICE": {"journey-mapping", "stakeholder-mapping", "roleplay", "concierge", "experience-prototype"},
    "EXPERIENCE": {"journey-mapping", "storyboard", "roleplay", "experience-prototype"},
    "BUSINESS_MODEL": {"stakeholder-mapping", "assumption-mapping", "fake-door", "concept-selection"},
    "WORKFLOW": {"contextual-inquiry", "observation", "journey-mapping", "manual-workflow", "spreadsheet-simulation"},
    "ORGANIZATIONAL": {"stakeholder-mapping", "contextual-inquiry", "tension-finding", "powers-of-ten"},
    "POLICY": {"stakeholder-mapping", "extreme-users", "tension-finding", "alternative-frames", "reality-check"},
    "SOCIAL_SYSTEM": {"stakeholder-mapping", "powers-of-ten", "alternative-frames", "analogous-experiences"},
    "HYBRID": {"stakeholder-mapping", "assumption-mapping", "alternative-frames", "prototype-to-learn"},
}

UNCERTAINTY_SIGNALS = {
    "people": {"interview-for-empathy", "observation", "contextual-inquiry", "inquiry-lab"},
    "behavior": {"observation", "interview-for-empathy", "assumption-test", "wizard-of-oz"},
    "problem": {"need-finding", "insight-generation", "alternative-frames", "point-of-view"},
    "solution": {"how-might-we", "brainwriting", "analogy-storm", "concept-selection"},
    "desirability": {"storyboard", "concierge", "assumption-test", "comparative-prototype-test"},
    "feasibility": {"coded-spike", "physical-mock", "technical-proof", "prototype-to-learn"},
    "viability": {"fake-door", "concierge", "assumption-test", "stakeholder-mapping"},
    "adoption": {"interview-for-empathy", "observation", "fake-door", "manual-workflow"},
    "system": {"stakeholder-mapping", "powers-of-ten", "analogous-experiences", "alternative-frames"},
    "evidence": {"research-planning", "inquiry-lab", "assumption-mapping", "reality-check"},
}


def _normalize_request(request: dict[str, Any]) -> dict[str, Any]:
    mode = str(request.get("current_mode", "")).upper()
    if mode not in VALID_MODES:
        raise DesignCouncilError(f"current_mode must be one of {sorted(VALID_MODES)}")
    raw_archetypes = request.get("challenge_archetype", request.get("challenge_archetypes", []))
    if isinstance(raw_archetypes, str):
        archetypes = [raw_archetypes.upper()]
    elif isinstance(raw_archetypes, list):
        archetypes = [str(value).upper() for value in raw_archetypes]
    else:
        raise DesignCouncilError("challenge_archetype must be a string or array")
    unknown_archetypes = sorted(set(archetypes) - VALID_ARCHETYPES)
    if unknown_archetypes:
        raise DesignCouncilError(f"unknown challenge archetype(s): {', '.join(unknown_archetypes)}")
    evidence = str(request.get("evidence_level", "LOW")).upper()
    if evidence not in {"NONE", "LOW", "MEDIUM", "HIGH"}:
        raise DesignCouncilError("evidence_level must be NONE, LOW, MEDIUM, or HIGH")
    try:
        minutes = int(request.get("time_available", request.get("time_available_minutes", 120)))
    except (TypeError, ValueError) as exc:
        raise DesignCouncilError("time_available must be an integer number of minutes") from exc
    if minutes < 5:
        raise DesignCouncilError("time_available must be at least 5 minutes")
    uncertainty = str(request.get("uncertainty_type", "evidence")).lower().replace("_", " ")
    return {
        **request,
        "current_mode": mode,
        "challenge_archetypes": archetypes,
        "evidence_level": evidence,
        "time_available_minutes": minutes,
        "uncertainty_type": uncertainty,
        "council_requested": bool(request.get("council_requested", False)),
    }


def select_methods(request: dict[str, Any], registry: dict[str, Any] | None = None) -> dict[str, Any]:
    req = _normalize_request(request)
    registry = registry or load_json(REFERENCE_ROOT / "method-registry.json")
    methods = registry.get("methods")
    if not isinstance(methods, list):
        raise DesignCouncilError("method registry has no methods array")

    uncertainty_words = set(req["uncertainty_type"].split())
    uncertainty_ids: set[str] = set()
    for key, identifiers in UNCERTAINTY_SIGNALS.items():
        if key in uncertainty_words or key in req["uncertainty_type"]:
            uncertainty_ids |= identifiers
    archetype_ids = set().union(*(ARCHETYPE_SIGNALS.get(item, set()) for item in req["challenge_archetypes"]))

    ranked: list[tuple[int, dict[str, Any], list[str]]] = []
    avoided: list[dict[str, str]] = []
    for method in methods:
        if req["current_mode"] not in method.get("modes", []):
            continue
        reasons = [f"supports {req['current_mode'].title()} mode"]
        score = 10
        method_id = method.get("id", "")
        if method_id in archetype_ids:
            score += 4
            reasons.append("fits the challenge archetype")
        if method_id in uncertainty_ids:
            score += 5
            reasons.append(f"targets {req['uncertainty_type']} uncertainty")
        if req["evidence_level"] in {"NONE", "LOW"} and method_id in {
            "research-planning", "inquiry-lab", "interview-for-empathy", "observation",
            "assumption-mapping", "need-finding", "insight-generation",
        }:
            score += 4
            reasons.append("addresses weak grounding")
        if req["council_requested"] and method.get("council") == "recommended":
            score += 2
            reasons.append("benefits from a cognitively diverse panel")
        effort = str(method.get("effort", "medium")).lower()
        minimum = EFFORT_MINUTES.get(effort, 75)
        if req["time_available_minutes"] < minimum:
            avoided.append({
                "method": method.get("name", method_id),
                "why": f"Typical {effort} effort exceeds the {req['time_available_minutes']}-minute window",
            })
            continue
        if req["time_available_minutes"] >= minimum * 2:
            score += 1
        ranked.append((score, method, reasons))

    ranked.sort(key=lambda item: (-item[0], EFFORT_MINUTES.get(str(item[1].get("effort", "medium")), 75), item[1].get("id", "")))
    capacity = 1 if req["time_available_minutes"] < 30 else 2 if req["time_available_minutes"] < 90 else 3
    recommended = []
    optional = []
    for index, (_, method, reasons) in enumerate(ranked[: capacity + 3]):
        result = {
            "id": method["id"],
            "method": method["name"],
            "why": "; ".join(reasons),
            "expected_learning": method["purpose"],
            "outputs": method.get("outputs", []),
            "source_family": method.get("source_family"),
            "reference": method.get("reference"),
        }
        (recommended if index < capacity else optional).append(result)

    if not recommended:
        fallback = next((m for m in methods if req["current_mode"] in m.get("modes", [])), None)
        if fallback:
            recommended.append({
                "id": fallback["id"], "method": fallback["name"],
                "why": "Smallest registry method available for this mode; compress facilitation to the timebox",
                "expected_learning": fallback["purpose"], "outputs": fallback.get("outputs", []),
                "source_family": fallback.get("source_family"), "reference": fallback.get("reference"),
            })
    return {
        "router_version": "1.0.0",
        "input": req,
        "recommended": recommended,
        "optional": optional,
        "avoid": avoided[:4],
        "advisory": "Method ranking is facilitation guidance, not evidence or a mandatory sequence.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Select relevant MightShape methods")
    parser.add_argument("input", nargs="?", help="JSON request file; stdin when omitted")
    parser.add_argument("--registry", default=str(REFERENCE_ROOT / "method-registry.json"))
    args = parser.parse_args()
    try:
        request = load_json(args.input) if args.input else json.load(sys.stdin)
        if not isinstance(request, dict):
            raise DesignCouncilError("input must be a JSON object")
        json_output(select_methods(request, load_json(args.registry)))
    except (DesignCouncilError, json.JSONDecodeError) as exc:
        print(f"MightShape error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
