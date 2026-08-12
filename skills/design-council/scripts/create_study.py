#!/usr/bin/env python3
"""Create a consent-forward Inquiry Lab study record."""

from __future__ import annotations

import argparse
import json
import secrets
import sys
from typing import Any

from dc_core import DesignCouncilError, json_output, load_json, now_utc, schema_validation


STUDY_TYPES = {"SYNTHETIC", "HUMAN", "MIXED", "ANALOGOUS", "REALITY_CHECK"}
PII_TERMS = {"name", "email", "phone", "address", "date of birth", "dob", "social security", "ssn"}


def create_study(spec: dict[str, Any], issue_public_token: bool = False) -> dict[str, Any]:
    if not isinstance(spec, dict):
        raise DesignCouncilError("study specification must be an object")
    title = str(spec.get("title", "")).strip()
    goal = str(spec.get("research_goal", "")).strip()
    topics = spec.get("topics_to_cover", [])
    if not title or not goal or not isinstance(topics, list) or not topics:
        raise DesignCouncilError("title, research_goal, and at least one topics_to_cover item are required")
    study_type = str(spec.get("study_type", "HUMAN")).upper()
    if study_type not in STUDY_TYPES:
        raise DesignCouncilError(f"study_type must be one of {sorted(STUDY_TYPES)}")
    duration = int(spec.get("duration_minutes", 10))
    if not 1 <= duration <= 180:
        raise DesignCouncilError("duration_minutes must be between 1 and 180")
    solution_blackout = bool(spec.get("solution_blackout", True))
    privacy = dict(spec.get("privacy_configuration", {}))
    privacy.setdefault("participant_identifiers", "P-### only")
    privacy.setdefault("collect_names", False)
    privacy.setdefault("collect_emails", False)
    privacy.setdefault("minimize_pii", True)
    privacy.setdefault("deletion_path", "Participant may stop; researcher can delete transcript by participant ID")
    data_collected = spec.get("data_collected", ["consent status", "anonymous participant ID", "text transcript", "interview state"])
    if not isinstance(data_collected, list):
        raise DesignCouncilError("data_collected must be an array")
    consent_spec = dict(spec.get("consent", {}))
    consent = {
        "version": str(consent_spec.get("version", "1.0")),
        "ai_disclosure": str(consent_spec.get("ai_disclosure", "The interviewer is AI, not a human researcher.")),
        "purpose": str(consent_spec.get("purpose", goal)),
        "duration_minutes": duration,
        "data_collected": [str(item) for item in data_collected],
        "reviewers": str(consent_spec.get("reviewers", spec.get("reviewers", "The named design research team"))),
        "deidentified_quotes": bool(consent_spec.get("deidentified_quotes", False)),
        "may_stop": True,
        "retention": str(consent_spec.get("retention", spec.get("retention", "Defined by the study owner before activation"))),
        "contact": str(consent_spec.get("contact", spec.get("contact", "Study owner contact shown on the participant page"))),
    }
    if "ai" not in consent["ai_disclosure"].lower():
        raise DesignCouncilError("consent.ai_disclosure must explicitly say the interviewer is AI")
    timestamp = now_utc()
    public_token = spec.get("public_token")
    if issue_public_token and not public_token:
        public_token = secrets.token_urlsafe(24)
    study = {
        "id": str(spec.get("id", "STUDY-001")),
        "title": title,
        "study_type": study_type,
        "research_goal": goal,
        "topics_to_cover": [str(item) for item in topics],
        "covered_topics": [],
        "emerging_threads": [],
        "adaptive_follow_up_priorities": [str(item) for item in spec.get("adaptive_follow_up_priorities", topics[:2])],
        "solution_blackout": solution_blackout,
        "concept_reveal": dict(spec.get("concept_reveal", {"enabled": False, "condition": "After behavior reconstruction and only when methodologically justified"})),
        "stop_conditions": [str(item) for item in spec.get("stop_conditions", ["participant asks to stop", "participant withdraws", "topics covered and no productive thread remains", f"approximately {duration} minutes elapsed"])],
        "privacy_configuration": privacy,
        "consent": consent,
        "participant_id_prefix": "P-",
        "public_token": public_token,
        "status": str(spec.get("status", "draft")).lower(),
        "created_at": str(spec.get("created_at", timestamp)),
        "updated_at": str(spec.get("updated_at", timestamp)),
    }
    validation = schema_validation(study, "inquiry-study.schema.json")
    if not validation["valid"]:
        raise DesignCouncilError("Study failed validation: " + "; ".join(validation["errors"]))
    return study


def study_warnings(study: dict[str, Any]) -> list[str]:
    warnings = []
    collected = " ".join(study["consent"]["data_collected"]).lower()
    unnecessary = sorted(term for term in PII_TERMS if term in collected)
    if unnecessary:
        warnings.append("Study declares potential PII collection; justify and minimize: " + ", ".join(unnecessary))
    if study["privacy_configuration"].get("collect_names") or study["privacy_configuration"].get("collect_emails"):
        warnings.append("Direct identifiers are enabled; document why anonymous P-### identifiers are insufficient")
    if study["status"] in {"ready", "active"} and "defined by" in study["consent"]["retention"].lower():
        warnings.append("Set a concrete retention period before activating the study")
    if study["public_token"] and study["status"] == "draft":
        warnings.append("A bearer token exists for a draft; do not present it as a deployed interview link")
    if study["status"] in {"ready", "active"} and "study owner contact" in study["consent"]["contact"].lower():
        warnings.append("Set a real participant contact before activating the study")
    return warnings


def main() -> int:
    parser = argparse.ArgumentParser(description="Create an Inquiry Lab study")
    parser.add_argument("input", nargs="?", help="Study specification JSON; stdin when omitted")
    parser.add_argument("--issue-public-token", action="store_true", help="Create an opaque bearer token, not a deployment URL")
    args = parser.parse_args()
    try:
        spec = load_json(args.input) if args.input else json.load(sys.stdin)
        study = create_study(spec, args.issue_public_token)
        json_output({"study": study, "warnings": study_warnings(study), "deployment_url": None, "note": "A token is not a hosted link; publish the optional Site explicitly."})
    except (DesignCouncilError, json.JSONDecodeError, ValueError) as exc:
        print(f"Design Council error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
