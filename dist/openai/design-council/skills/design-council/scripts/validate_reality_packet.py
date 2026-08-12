#!/usr/bin/env python3
"""Validate Reality Packet shape, traceability, and grounding sufficiency."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from dc_core import DesignCouncilError, json_output, load_json, schema_validation


THRESHOLDS = {
    "FAST": {"sources": 1, "facts": 2, "workflows": 1, "key_detail": 1},
    "RESEARCHED": {"sources": 3, "facts": 5, "workflows": 2, "key_detail": 1},
    "DEEP": {"sources": 5, "facts": 10, "workflows": 3, "key_detail": 2},
}
KEY_FIELDS = (
    "responsibilities", "working_environment", "decision_rights", "terminology", "tools_and_systems",
    "dependencies", "organizational_relationships", "incentives", "constraints", "performance_pressures",
    "failure_modes", "workarounds", "common_variations", "cultural_context", "unresolved_questions", "local_variation",
)


def validate_reality_packet(packet: dict[str, Any], consequential: bool = False) -> dict[str, Any]:
    if not isinstance(packet, dict):
        raise DesignCouncilError("Reality Packet must be a JSON object")
    schema = schema_validation(packet, "reality-packet.schema.json")
    errors = list(schema["errors"])
    warnings: list[str] = []
    grounding = str(packet.get("grounding_level", "FAST")).upper()
    threshold = THRESHOLDS.get(grounding, THRESHOLDS["FAST"])
    sources = packet.get("sources", []) if isinstance(packet.get("sources"), list) else []
    facts = packet.get("supported_facts", []) if isinstance(packet.get("supported_facts"), list) else []
    source_ids = {item.get("id") for item in sources if isinstance(item, dict)}
    duplicate_ids = len(source_ids) != len(sources)
    if duplicate_ids:
        errors.append("sources: source IDs must be unique")
    for index, fact in enumerate(facts):
        for source_id in fact.get("source_ids", []) if isinstance(fact, dict) else []:
            if source_id not in source_ids:
                errors.append(f"supported_facts.{index}: unknown source ID {source_id}")
    for index, inference in enumerate(packet.get("research_supported_inferences", [])):
        for source_id in inference.get("based_on", []) if isinstance(inference, dict) else []:
            if source_id not in source_ids:
                errors.append(f"research_supported_inferences.{index}: unknown source ID {source_id}")
    normalized_claims = [str(item.get("claim", "")).strip().lower() for item in facts if isinstance(item, dict)]
    if len(normalized_claims) != len(set(normalized_claims)):
        warnings.append("Duplicate supported claims do not create independent grounding")
    if len(sources) < threshold["sources"]:
        errors.append(f"{grounding} grounding requires at least {threshold['sources']} source(s); found {len(sources)}")
    if len(facts) < threshold["facts"]:
        errors.append(f"{grounding} grounding requires at least {threshold['facts']} traceable fact(s); found {len(facts)}")
    if len(packet.get("workflows", [])) < threshold["workflows"]:
        errors.append(f"{grounding} grounding requires at least {threshold['workflows']} workflow detail(s)")
    for field in KEY_FIELDS:
        if len(packet.get(field, [])) < threshold["key_detail"]:
            errors.append(f"{field}: insufficient detail for {grounding} grounding")
    regulations = packet.get("regulations", [])
    if not regulations and packet.get("regulations_not_applicable") is not True:
        warnings.append("Regulations are empty without regulations_not_applicable=true; verify rather than assume none apply")
    authority = {item.get("authority_type") for item in sources if isinstance(item, dict)}
    authoritative_count = sum(1 for item in sources if item.get("authority_type") in {"primary", "official", "peer_reviewed", "professional_authority"})
    if grounding in {"RESEARCHED", "DEEP"} and authoritative_count < max(2, threshold["sources"] - 1):
        errors.append(f"{grounding} grounding requires multiple primary or authoritative sources")
    if len({item.get("publisher") for item in sources if isinstance(item, dict)}) < min(2, len(sources)) and len(sources) > 1:
        warnings.append("Most sources share one publisher; inspect source independence")
    if consequential and grounding == "FAST":
        errors.append("FAST grounding is insufficient for a consequential synthetic participant")
    if consequential and not packet.get("local_variation"):
        errors.append("Consequential grounding must identify local variation rather than imply universal practice")
    if not packet.get("unresolved_questions"):
        warnings.append("No unresolved questions are recorded; this may indicate false completeness")
    valid = not errors
    return {
        "valid": valid,
        "valid_for_persona": valid and (not consequential or grounding in {"RESEARCHED", "DEEP"}),
        "grounding_level": grounding,
        "consequential": consequential,
        "schema_validator": schema["validator"],
        "counts": {"sources": len(sources), "authoritative_sources": authoritative_count, "supported_facts": len(facts), "workflows": len(packet.get("workflows", []))},
        "errors": errors,
        "warnings": warnings,
        "unknowns_preserved": len(packet.get("unresolved_questions", [])),
        "local_variation_preserved": bool(packet.get("local_variation")),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a Design Council Reality Packet")
    parser.add_argument("input", nargs="?", help="Reality Packet JSON; stdin when omitted")
    parser.add_argument("--consequential", action="store_true")
    args = parser.parse_args()
    try:
        packet = load_json(args.input) if args.input else json.load(sys.stdin)
        result = validate_reality_packet(packet, args.consequential)
        json_output(result)
        return 0 if result["valid"] else 1
    except (DesignCouncilError, json.JSONDecodeError) as exc:
        print(f"Design Council error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
