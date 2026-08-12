#!/usr/bin/env python3
"""Provenance-safe deterministic collation for already interpreted findings.

This script never claims to semantically interpret raw interviews. It checks and
organizes traceable finding records so facilitator synthesis cannot silently blend
human, research, inference, and synthetic layers.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from typing import Any

from dc_core import DesignCouncilError, json_output, load_json, schema_validation


HUMAN = {"OBSERVED_HUMAN_BEHAVIOR", "HUMAN_INTERVIEW"}
SYNTHETIC = {"SYNTHETIC_USER", "SYNTHETIC_PRACTITIONER", "SYNTHETIC_EXPERT"}
RESEARCH = {"AUTHORITATIVE_RESEARCH"}
INFERENCE = {"RESEARCH_SUPPORTED_INFERENCE", "DESIGN_COUNCIL"}
LAYERS = {
    "human_supported": HUMAN,
    "authoritative_research": RESEARCH,
    "inference": INFERENCE,
    "synthetic_signals": SYNTHETIC,
    "unknown": {"UNKNOWN"},
}
GENERALIZATION = re.compile(r"\b(all|always|everyone|most people|the majority|[0-9]+\s*%|universally)\b", re.I)


def synthesize_inquiry(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        findings = value.get("findings", [])
        transcripts = value.get("transcripts", [])
    elif isinstance(value, list):
        findings, transcripts = value, []
    else:
        raise DesignCouncilError("input must be a findings array or object")
    if not isinstance(findings, list):
        raise DesignCouncilError("findings must be an array")
    errors = []
    warnings = []
    layers: dict[str, list[dict[str, Any]]] = {name: [] for name in LAYERS}
    by_type: dict[str, list[str]] = {name: [] for name in ("pattern", "tension", "contradiction", "need_candidate", "insight_candidate", "unknown", "research_question")}
    ids: set[str] = set()
    records: dict[str, dict[str, Any]] = {}
    for index, finding in enumerate(findings):
        label = str(finding.get("id", f"index:{index}")) if isinstance(finding, dict) else f"index:{index}"
        if not isinstance(finding, dict):
            errors.append(f"{label}: finding must be an object")
            continue
        validation = schema_validation(finding, "research-finding.schema.json")
        errors.extend(f"{label}: {message}" for message in validation["errors"])
        if label in ids:
            errors.append(f"{label}: duplicate finding ID")
        ids.add(label)
        records[label] = finding
        provenance = finding.get("provenance")
        layer = next((name for name, values in LAYERS.items() if provenance in values), None)
        if layer:
            layers[layer].append(finding)
        else:
            errors.append(f"{label}: unsupported provenance {provenance}")
        finding_type = finding.get("finding_type")
        if finding_type in by_type:
            by_type[finding_type].append(label)
        if provenance in SYNTHETIC | {"DESIGN_COUNCIL", "UNKNOWN"} and finding.get("evidence_strength") != 0:
            errors.append(f"{label}: {provenance} must use evidence_strength 0")
        if provenance == "RESEARCH_SUPPORTED_INFERENCE" and finding.get("evidence_strength", 0) > 2:
            errors.append(f"{label}: inference strength cannot exceed 2")
        if any("CONSTRUCTED_CONTINUITY" in str(ref).upper() for ref in finding.get("source_refs", [])):
            errors.append(f"{label}: constructed continuity cannot become research evidence")
        if provenance in HUMAN and GENERALIZATION.search(str(finding.get("statement", ""))):
            warnings.append(f"{label}: qualitative finding appears overgeneralized")
    contradiction_links = []
    seen_links: set[tuple[str, str]] = set()
    for finding_id, finding in records.items():
        for target in finding.get("contradicts", []):
            if target not in records:
                warnings.append(f"{finding_id}: contradiction target {target} is not in this synthesis set")
                continue
            pair = tuple(sorted((finding_id, target)))
            if pair not in seen_links:
                seen_links.add(pair)
                contradiction_links.append({"left": finding_id, "right": target})
    reality_check_candidates = []
    for link in contradiction_links:
        left, right = records[link["left"]], records[link["right"]]
        if ({left.get("provenance"), right.get("provenance")} & SYNTHETIC) and ({left.get("provenance"), right.get("provenance")} & HUMAN):
            reality_check_candidates.append({
                "synthetic_finding": link["left"] if left.get("provenance") in SYNTHETIC else link["right"],
                "human_finding": link["left"] if left.get("provenance") in HUMAN else link["right"],
                "recommended_outcomes": ["contradicted", "transformed", "inconclusive"],
            })
    transcript_inventory = Counter()
    for transcript in transcripts if isinstance(transcripts, list) else []:
        if isinstance(transcript, dict):
            transcript_inventory[str(transcript.get("provenance", "UNKNOWN"))] += 1
    limitations = [
        "Findings are scoped to their source records and contexts; counts are not population prevalence.",
        "Synthetic participants remain synthetic after repetition or agreement.",
        "This deterministic tool organizes supplied interpretations; it does not infer themes from raw transcript text.",
    ]
    if layers["synthetic_signals"] and not layers["human_supported"]:
        limitations.append("No human-supported finding is present; use outputs as hypotheses and research questions.")
    return {
        "valid": not errors,
        "layers": layers,
        "finding_type_index": by_type,
        "contradictions": contradiction_links,
        "reality_check_candidates": reality_check_candidates,
        "unanswered_questions": [item["statement"] for item in findings if isinstance(item, dict) and item.get("finding_type") in {"unknown", "research_question"}],
        "transcript_inventory": dict(transcript_inventory),
        "errors": errors,
        "warnings": warnings,
        "limitations": limitations,
        "next_move": "Run a Reality Check" if reality_check_candidates else "Review contradictions and source scope before creating POVs",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Collate Inquiry findings without mixing provenance")
    parser.add_argument("input", nargs="?", help="JSON file; stdin when omitted")
    args = parser.parse_args()
    try:
        value = load_json(args.input) if args.input else json.load(sys.stdin)
        result = synthesize_inquiry(value)
        json_output(result)
        return 0 if result["valid"] else 1
    except (DesignCouncilError, json.JSONDecodeError) as exc:
        print(f"Design Council error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
