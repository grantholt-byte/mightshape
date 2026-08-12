#!/usr/bin/env python3
"""Assemble a synthetic participant only from a validated Reality Packet."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from dc_core import DesignCouncilError, json_output, load_json, now_utc, schema_validation
from validate_reality_packet import validate_reality_packet


TYPES = {"SYNTHETIC_USER", "SYNTHETIC_PRACTITIONER", "SYNTHETIC_EXPERT"}


def create_persona(spec: dict[str, Any], consequential: bool = True) -> dict[str, Any]:
    if not isinstance(spec, dict):
        raise DesignCouncilError("persona specification must be an object")
    packet = spec.get("reality_packet")
    if not isinstance(packet, dict):
        raise DesignCouncilError("create_persona requires the complete reality_packet object")
    packet_result = validate_reality_packet(packet, consequential=consequential)
    if not packet_result["valid_for_persona"]:
        raise DesignCouncilError("Reality Packet is insufficient: " + "; ".join(packet_result["errors"]))
    participant_type = str(spec.get("participant_type", "")).upper()
    if participant_type not in TYPES:
        raise DesignCouncilError(f"participant_type must be one of {sorted(TYPES)}")
    human_model = spec.get("human_model")
    if not isinstance(human_model, dict):
        raise DesignCouncilError("A full human_model is required; this script will not generate a shallow role stereotype")
    model_validation = schema_validation(human_model, "human-model.schema.json")
    if not model_validation["valid"]:
        raise DesignCouncilError("Human Model is invalid: " + "; ".join(model_validation["errors"]))
    variations = spec.get("variation_dimensions", {})
    if not isinstance(variations, dict) or len(variations) < 2:
        raise DesignCouncilError("variation_dimensions requires at least two behaviorally meaningful dimensions")
    superficial = {"race", "ethnicity", "gender", "name", "age"}
    if set(str(key).lower() for key in variations) <= superficial:
        raise DesignCouncilError("variation must include behaviorally meaningful dimensions, not demographics alone")

    facts = packet.get("supported_facts", [])
    layers = spec.get("epistemic_layers", {})
    domain_grounding = layers.get("DOMAIN_GROUNDING") if isinstance(layers, dict) else None
    if domain_grounding is None:
        domain_grounding = [{"detail": item["claim"], "source_ids": item["source_ids"]} for item in facts]
    if not isinstance(domain_grounding, list) or not domain_grounding:
        raise DesignCouncilError("DOMAIN_GROUNDING must contain traceable details")
    valid_source_ids = {item["id"] for item in packet.get("sources", [])}
    for index, detail in enumerate(domain_grounding):
        if not isinstance(detail, dict) or not str(detail.get("detail", "")).strip():
            raise DesignCouncilError(f"DOMAIN_GROUNDING item {index} requires a detail")
        source_ids = detail.get("source_ids", [])
        if not isinstance(source_ids, list) or not source_ids:
            raise DesignCouncilError(f"DOMAIN_GROUNDING item {index} requires source_ids")
        unknown_sources = sorted(set(source_ids) - valid_source_ids)
        if unknown_sources:
            raise DesignCouncilError(f"DOMAIN_GROUNDING item {index} references unknown source(s): {', '.join(unknown_sources)}")
    inference = layers.get("REASONABLE_INFERENCE", packet.get("research_supported_inferences", [])) if isinstance(layers, dict) else packet.get("research_supported_inferences", [])
    inference = [item.get("claim", "") if isinstance(item, dict) else str(item) for item in inference]
    continuity = spec.get("constructed_continuity", layers.get("CONSTRUCTED_CONTINUITY", []) if isinstance(layers, dict) else [])
    unknowns = layers.get("UNKNOWN", packet.get("unresolved_questions", [])) if isinstance(layers, dict) else packet.get("unresolved_questions", [])
    if not isinstance(continuity, list):
        raise DesignCouncilError("constructed_continuity must be an array")
    supplied_limitations = spec.get("limitations", [])
    if not isinstance(supplied_limitations, list) or not all(isinstance(item, str) for item in supplied_limitations):
        raise DesignCouncilError("limitations must be an array of strings")
    limitations = list(dict.fromkeys(supplied_limitations + [
        "Cannot infer prevalence or population statistics from simulated experience.",
        "Cannot know site-specific practice beyond the Reality Packet.",
        "Must label intuition and defer outside the modeled knowledge boundary.",
        "Constructed continuity is fictional and must never be promoted to evidence.",
    ]))
    persona = {
        "id": spec.get("id", "SP-001"),
        "participant_type": participant_type,
        "provenance": participant_type,
        "reality_packet_id": packet["id"],
        "variation_dimensions": variations,
        "human_model": human_model,
        "epistemic_layers": {
            "DOMAIN_GROUNDING": domain_grounding,
            "REASONABLE_INFERENCE": inference,
            "CONSTRUCTED_CONTINUITY": [str(item) for item in continuity],
            "UNKNOWN": [str(item) for item in unknowns],
        },
        "limitations": limitations,
        "created_at": spec.get("created_at", now_utc()),
    }
    validation = schema_validation(persona, "synthetic-persona.schema.json")
    if not validation["valid"]:
        raise DesignCouncilError("Synthetic persona failed validation: " + "; ".join(validation["errors"]))
    return persona


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a research-grounded synthetic participant")
    parser.add_argument("input", nargs="?", help="Persona specification JSON; stdin when omitted")
    parser.add_argument("--low-consequence", action="store_true", help="Allow valid FAST grounding")
    args = parser.parse_args()
    try:
        spec = load_json(args.input) if args.input else json.load(sys.stdin)
        json_output(create_persona(spec, consequential=not args.low_consequence))
    except (DesignCouncilError, json.JSONDecodeError) as exc:
        print(f"Design Council error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
