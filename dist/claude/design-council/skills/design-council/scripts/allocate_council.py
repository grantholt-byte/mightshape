#!/usr/bin/env python3
"""Allocate Council members for relevance *and* cognitive diversity."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from dc_core import DesignCouncilError, json_output, load_json


MEMBERS: dict[str, dict[str, Any]] = {
    "maya-chen": {"name": "Maya Chen", "lens": "Human Reality", "group": "human", "tags": {"burden", "safety", "accessibility", "care", "recovery", "workflow"}},
    "leo-martinez": {"name": "Leo Martinez", "lens": "Maker", "group": "making", "tags": {"prototype", "physical", "mechanism", "experiment", "feasibility", "repair"}},
    "priya-rao": {"name": "Priya Rao", "lens": "Behavioral Skeptic", "group": "evidence", "tags": {"behavior", "evidence", "incentives", "experiment", "bias", "adoption"}},
    "marcus-brooks": {"name": "Marcus Brooks", "lens": "Operator", "group": "operations", "tags": {"operations", "labor", "service", "viability", "margin", "workflow", "adoption"}},
    "elena-rossi": {"name": "Elena Rossi", "lens": "Experience Designer", "group": "experience", "tags": {"experience", "emotion", "usability", "physical", "meaning", "coherence"}},
    "theo-bennett": {"name": "Theo Bennett", "lens": "Investigative Skeptic", "group": "accountability", "tags": {"institutions", "accountability", "assumption", "incentives", "policy", "risk"}},
    "samira-okafor": {"name": "Samira Okafor", "lens": "Systems Advocate", "group": "systems", "tags": {"systems", "equity", "power", "policy", "stakeholders", "accessibility", "burden"}},
    "jack-sullivan": {"name": "Jack Sullivan", "lens": "Adoption Realist", "group": "adoption", "tags": {"adoption", "sales", "switching", "business", "value", "language", "incentives"}},
    "mei-tanaka": {"name": "Mei Tanaka", "lens": "Systems Engineer", "group": "technical", "tags": {"ai", "technical", "data", "reliability", "automation", "privacy", "workflow"}},
    "rafael-alvarez": {"name": "Rafael Alvarez", "lens": "Possibility Engine", "group": "possibility", "tags": {"divergence", "analogy", "inversion", "radical", "experience", "possibility"}},
}

ARCHETYPE_TAGS = {
    "DIGITAL_PRODUCT": {"usability", "technical", "adoption", "accessibility", "data"},
    "AI_PRODUCT": {"ai", "automation", "data", "behavior", "safety", "adoption", "divergence"},
    "PHYSICAL_PRODUCT": {"physical", "mechanism", "safety", "experience", "repair"},
    "SERVICE": {"service", "operations", "experience", "burden", "adoption"},
    "EXPERIENCE": {"experience", "emotion", "meaning", "behavior", "possibility"},
    "BUSINESS_MODEL": {"business", "value", "margin", "adoption", "incentives"},
    "WORKFLOW": {"workflow", "operations", "burden", "technical", "behavior"},
    "ORGANIZATIONAL": {"institutions", "operations", "power", "incentives", "workflow"},
    "POLICY": {"policy", "power", "equity", "institutions", "risk"},
    "SOCIAL_SYSTEM": {"systems", "stakeholders", "power", "equity", "incentives"},
    "HYBRID": {"systems", "stakeholders", "technical", "experience", "operations"},
}

LEVEL_SIZE = {"FACILITATOR_ONLY": 0, "PANEL": 5, "FULL_COUNCIL": 10, "DEEP_DIVERGENCE": 10}


def _normalize_request(request: dict[str, Any]) -> tuple[str, int, list[str], set[str]]:
    level = str(request.get("operating_level", request.get("level", "PANEL"))).upper()
    if level not in LEVEL_SIZE:
        raise DesignCouncilError(f"operating_level must be one of {sorted(LEVEL_SIZE)}")
    raw_archetypes = request.get("archetypes", request.get("challenge_archetype", []))
    raw_archetypes = [raw_archetypes] if isinstance(raw_archetypes, str) else raw_archetypes
    if not isinstance(raw_archetypes, list):
        raise DesignCouncilError("archetypes must be a string or array")
    archetypes = [str(item).upper() for item in raw_archetypes]
    unknown = sorted(set(archetypes) - set(ARCHETYPE_TAGS))
    if unknown:
        raise DesignCouncilError(f"unknown archetype(s): {', '.join(unknown)}")
    default_size = LEVEL_SIZE[level]
    try:
        size = int(request.get("panel_size", default_size))
    except (TypeError, ValueError) as exc:
        raise DesignCouncilError("panel_size must be an integer") from exc
    if level in {"FULL_COUNCIL", "DEEP_DIVERGENCE"}:
        size = 10
    if level == "FACILITATOR_ONLY":
        size = 0
    if not 0 <= size <= 10:
        raise DesignCouncilError("panel_size must be between 0 and 10")
    text = " ".join(str(request.get(key, "")) for key in ("task", "challenge", "uncertainty_type")).lower()
    signals = {token for token in set().union(*(ARCHETYPE_TAGS[item] for item in archetypes)) if token}
    for token in {tag for member in MEMBERS.values() for tag in member["tags"]}:
        if token in text:
            signals.add(token)
    return level, size, archetypes, signals


def allocate_council(request: dict[str, Any]) -> dict[str, Any]:
    level, size, archetypes, signals = _normalize_request(request)
    if not size:
        return {
            "operating_level": "FACILITATOR_ONLY", "selected": [], "cognitive_groups": [],
            "why": "No simulated member is needed for this bounded facilitation task.",
            "sealed_round_required": False,
        }
    text = " ".join(str(request.get(key, "")) for key in ("task", "challenge")).lower()
    challenge_me = "challenge me" in text or bool(request.get("challenge_me"))
    if challenge_me and size >= 5:
        priority = ["theo-bennett", "priya-rao", "samira-okafor", "marcus-brooks", "rafael-alvarez"]
    elif "AI_PRODUCT" in archetypes and size >= 5:
        # Explicitly span technical, human, behavioral, adoption, and possibility lenses.
        priority = ["mei-tanaka", "maya-chen", "priya-rao", "jack-sullivan", "rafael-alvarez"]
    else:
        priority = []

    scored = []
    for member_id, member in MEMBERS.items():
        overlap = sorted(signals & member["tags"])
        score = len(overlap) * 3
        if member_id in priority:
            score += 20 - priority.index(member_id)
        if not signals:
            score += 1
        scored.append((score, member_id, overlap))
    scored.sort(key=lambda item: (-item[0], item[1]))

    selected_ids: list[str] = []
    used_groups: set[str] = set()
    for member_id in priority:
        if len(selected_ids) < size and member_id not in selected_ids:
            selected_ids.append(member_id)
            used_groups.add(MEMBERS[member_id]["group"])
    # First pass favors unrepresented cognitive groups, second fills by relevance.
    for _, member_id, _ in scored:
        if len(selected_ids) >= size:
            break
        group = MEMBERS[member_id]["group"]
        if member_id not in selected_ids and group not in used_groups:
            selected_ids.append(member_id)
            used_groups.add(group)
    for _, member_id, _ in scored:
        if len(selected_ids) >= size:
            break
        if member_id not in selected_ids:
            selected_ids.append(member_id)

    rank = {member_id: (score, overlap) for score, member_id, overlap in scored}
    selected = []
    for member_id in selected_ids:
        member = MEMBERS[member_id]
        score, overlap = rank[member_id]
        selected.append({
            "member_id": member_id,
            "name": member["name"],
            "lens": member["lens"],
            "cognitive_group": member["group"],
            "relevance_signals": overlap,
            "why": f"Adds {member['lens'].lower()} reasoning" + (f" for {', '.join(overlap)}" if overlap else " to preserve cognitive range"),
        })
    return {
        "operating_level": level,
        "selected": selected,
        "cognitive_groups": [item["cognitive_group"] for item in selected],
        "relevant_signals": sorted(signals),
        "diversity_check": {
            "distinct_groups": len({item["cognitive_group"] for item in selected}),
            "panel_size": len(selected),
            "passes": len({item["cognitive_group"] for item in selected}) == len(selected),
        },
        "sealed_round_required": len(selected) > 1,
        "note": "Expertise informed selection; no single domain was allowed to crowd out cognitive diversity.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Allocate a cognitively diverse Design Council")
    parser.add_argument("input", nargs="?", help="JSON request file; stdin when omitted")
    args = parser.parse_args()
    try:
        request = load_json(args.input) if args.input else json.load(sys.stdin)
        if not isinstance(request, dict):
            raise DesignCouncilError("input must be a JSON object")
        json_output(allocate_council(request))
    except (DesignCouncilError, json.JSONDecodeError, ValueError) as exc:
        print(f"Design Council error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
