#!/usr/bin/env python3
"""Audit evidence records against the Evidence Firewall."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from typing import Any

from dc_core import DesignCouncilError, json_output, load_json, schema_validation


PROVENANCE = {
    "OBSERVED_HUMAN_BEHAVIOR", "HUMAN_INTERVIEW", "USER_PROVIDED", "AUTHORITATIVE_RESEARCH",
    "RESEARCH_SUPPORTED_INFERENCE", "SYNTHETIC_USER", "SYNTHETIC_PRACTITIONER", "SYNTHETIC_EXPERT",
    "DESIGN_COUNCIL", "ASSUMPTION", "UNKNOWN",
}
ZERO_STRENGTH = {"USER_PROVIDED", "SYNTHETIC_USER", "SYNTHETIC_PRACTITIONER", "SYNTHETIC_EXPERT", "DESIGN_COUNCIL", "ASSUMPTION", "UNKNOWN"}
HUMAN = {"OBSERVED_HUMAN_BEHAVIOR", "HUMAN_INTERVIEW"}
GENERALIZATION = re.compile(r"\b(all|always|everyone|nobody|most|the majority|[0-9]+\s*%|nationally|universally)\b", re.I)


def audit_evidence(value: Any) -> dict[str, Any]:
    if isinstance(value, dict) and "evidence" in value:
        records = value["evidence"]
    elif isinstance(value, list):
        records = value
    elif isinstance(value, dict):
        records = [value]
    else:
        raise DesignCouncilError("input must be an evidence record, array, or project state")
    if not isinstance(records, list):
        raise DesignCouncilError("evidence must be an array")
    errors: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []
    ids: set[str] = set()
    provenance_counts: Counter[str] = Counter()
    source_usage: Counter[str] = Counter()
    human_participants: set[str] = set()
    for index, record in enumerate(records):
        label = str(record.get("id", f"index:{index}")) if isinstance(record, dict) else f"index:{index}"
        if not isinstance(record, dict):
            errors.append({"record": label, "code": "NOT_OBJECT", "message": "Evidence record must be an object"})
            continue
        validation = schema_validation(record, "evidence.schema.json")
        for message in validation["errors"]:
            errors.append({"record": label, "code": "SCHEMA", "message": message})
        if label in ids:
            errors.append({"record": label, "code": "DUPLICATE_ID", "message": "Evidence IDs must be unique"})
        ids.add(label)
        provenance = str(record.get("provenance", ""))
        provenance_counts[provenance] += 1
        strength = record.get("evidence_strength")
        if provenance not in PROVENANCE:
            errors.append({"record": label, "code": "UNKNOWN_PROVENANCE", "message": provenance})
        if provenance in ZERO_STRENGTH and strength != 0:
            errors.append({"record": label, "code": "UNSUPPORTED_PROMOTION", "message": f"{provenance} must have evidence_strength 0 for real-world claims"})
        if provenance == "RESEARCH_SUPPORTED_INFERENCE" and isinstance(strength, int) and strength > 2:
            errors.append({"record": label, "code": "INFERENCE_OVERSTRENGTH", "message": "Research-supported inference cannot exceed strength 2"})
        refs = record.get("source_refs") or []
        source_usage.update(str(ref) for ref in refs)
        if provenance in HUMAN | {"AUTHORITATIVE_RESEARCH"} and not refs:
            errors.append({"record": label, "code": "MISSING_SOURCE", "message": f"{provenance} requires traceable source_refs"})
        if provenance in HUMAN:
            participant_id = record.get("participant_id")
            if not participant_id:
                errors.append({"record": label, "code": "MISSING_PARTICIPANT", "message": "Human evidence requires a participant ID"})
            else:
                human_participants.add(str(participant_id))
            if record.get("excerpt") and record.get("consent_allows_quote") is not True:
                errors.append({"record": label, "code": "QUOTE_WITHOUT_CONSENT", "message": "Human excerpt requires consent_allows_quote=true"})
            if GENERALIZATION.search(str(record.get("claim", ""))):
                warnings.append({"record": label, "code": "QUALITATIVE_OVERGENERALIZATION", "message": "A situated qualitative record appears to make a population-wide claim"})
        if provenance.startswith("SYNTHETIC_") and record.get("participant_id") and str(record.get("participant_id")).startswith("P-"):
            warnings.append({"record": label, "code": "AMBIGUOUS_PARTICIPANT_REF", "message": "Keep synthetic persona/transcript references visibly synthetic"})
        if provenance.startswith("SYNTHETIC_") and GENERALIZATION.search(str(record.get("claim", ""))):
            warnings.append({"record": label, "code": "SYNTHETIC_GENERALIZATION", "message": "A synthetic signal cannot support a population-wide claim"})
        if any("CONSTRUCTED_CONTINUITY" in str(ref).upper() for ref in refs):
            errors.append({"record": label, "code": "CONSTRUCTED_CONTINUITY_PROMOTION", "message": "Constructed persona continuity cannot become evidence"})

    non_human_count = len(records) - sum(provenance_counts[item] for item in HUMAN)
    debts = []
    if records and not human_participants:
        debts.append({"type": "EVIDENCE_DEBT", "claim": "No direct human evidence is present", "mitigation": "Use a Reality Check or appropriately scoped human inquiry when behavior materially affects the decision."})
    if records and sum(provenance_counts[item] for item in ZERO_STRENGTH) > len(records) / 2:
        debts.append({"type": "EVIDENCE_DEBT", "claim": "Most records are user claims, assumptions, Council output, unknowns, or synthetic signals", "mitigation": "Do not block reversible learning builds; expose this debt at consequential decisions."})
    repeated_sources = {source: count for source, count in source_usage.items() if count > 1}
    if repeated_sources:
        warnings.append({"record": "set", "code": "SOURCE_INDEPENDENCE", "message": "Repeated source references do not create independent corroboration: " + ", ".join(sorted(repeated_sources))})
    return {
        "valid": not errors,
        "record_count": len(records),
        "provenance_counts": dict(sorted(provenance_counts.items())),
        "direct_human_participant_count": len(human_participants),
        "repeated_source_refs": repeated_sources,
        "errors": errors,
        "warnings": warnings,
        "evidence_debt": debts,
        "firewall": "PASS" if not errors else "FAIL",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit Design Council evidence provenance")
    parser.add_argument("input", nargs="?", help="JSON file; stdin when omitted")
    args = parser.parse_args()
    try:
        value = load_json(args.input) if args.input else json.load(sys.stdin)
        result = audit_evidence(value)
        json_output(result)
        return 0 if result["valid"] else 1
    except (DesignCouncilError, json.JSONDecodeError) as exc:
        print(f"Design Council error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
