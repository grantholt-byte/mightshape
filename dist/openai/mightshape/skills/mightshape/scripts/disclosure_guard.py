#!/usr/bin/env python3
"""Create a minimized participant-facing packet from a private study.

Disclosure Guard is deliberately conservative. It never edits the supplied
study, never reproduces detected sensitive values in its findings, and never
claims legal/confidentiality protection. Ambiguous material is omitted from the
external packet until a user makes an explicit decision.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from dc_core import DesignCouncilError, json_output, load_json, now_utc, schema_validation


EXPOSURE_LEVELS = {
    "LEVEL_0_PROBLEM_ONLY",
    "LEVEL_1_ABSTRACTED_CONCEPT",
    "LEVEL_2_PROTOTYPE_BLIND",
    "LEVEL_3_CONFIDENTIAL",
}
DISCLAIMER = (
    "Disclosure Guard reduces unnecessary information exposure; it does not "
    "guarantee confidentiality, legal protection, conflict screening, or NDA coverage."
)

REMOVE_KEYS: dict[str, tuple[str, str]] = {
    "companyname": ("SPONSOR_IDENTITY", "Sponsor identity is unnecessary unless the research question requires it."),
    "sponsorname": ("SPONSOR_IDENTITY", "Sponsor identity is unnecessary unless the research question requires it."),
    "sponsoridentity": ("SPONSOR_IDENTITY", "Sponsor identity is unnecessary unless the research question requires it."),
    "projectcodename": ("PROJECT_CODENAME", "Internal codenames should not enter participant-facing material."),
    "productcodename": ("PROJECT_CODENAME", "Internal codenames should not enter participant-facing material."),
    "unreleasedproductname": ("PROJECT_CODENAME", "Unreleased product names should not enter participant-facing material."),
    "pricing": ("PRICING", "Internal pricing is unnecessary for this external packet."),
    "pricingassumption": ("PRICING", "Internal pricing assumptions are unnecessary for this external packet."),
    "commercialstrategy": ("BUSINESS_STRATEGY", "Commercial strategy should remain in the private study."),
    "businessstrategy": ("BUSINESS_STRATEGY", "Business strategy should remain in the private study."),
    "productroadmap": ("BUSINESS_STRATEGY", "The product roadmap should remain in the private study."),
    "strategicrationale": ("BUSINESS_STRATEGY", "Strategic rationale should remain in the private study."),
    "sourcecode": ("TECHNICAL_IP", "Source code is not participant-facing research context."),
    "customeridentifiers": ("CUSTOMER_IDENTITY", "Customer-identifying data is not required for this research packet."),
    "customerdata": ("CUSTOMER_IDENTITY", "Customer data is not required for this research packet."),
    "email": ("PERSONAL_DATA", "Direct personal identifiers are excluded by default."),
    "phone": ("PERSONAL_DATA", "Direct personal identifiers are excluded by default."),
    "fullname": ("PERSONAL_DATA", "Direct personal identifiers are excluded by default."),
    "address": ("PERSONAL_DATA", "Direct personal identifiers are excluded by default."),
    "apikey": ("SECRET", "Secrets must never enter participant-facing material."),
    "accesstoken": ("SECRET", "Secrets must never enter participant-facing material."),
    "secret": ("SECRET", "Secrets must never enter participant-facing material."),
    "documentmetadata": ("DOCUMENT_METADATA", "Document metadata can reveal internal identity or systems."),
    "filepath": ("DOCUMENT_METADATA", "File paths can reveal internal identity or systems."),
    "author": ("DOCUMENT_METADATA", "Document authorship is unnecessary for this research packet."),
}

GENERALIZE_KEYS: dict[str, tuple[str, str, str]] = {
    "architecture": ("TECHNICAL_IP", "Technical architecture is more specific than the research requires.", "[technical mechanism generalized]"),
    "internalarchitecture": ("TECHNICAL_IP", "Internal architecture is more specific than the research requires.", "[technical mechanism generalized]"),
    "proprietaryarchitecture": ("TECHNICAL_IP", "Proprietary architecture is more specific than the research requires.", "[technical mechanism generalized]"),
    "implementationdetails": ("TECHNICAL_IP", "Implementation details are more specific than the research requires.", "[implementation generalized]"),
    "technicalmechanism": ("TECHNICAL_IP", "Technical mechanism detail is more specific than the research requires.", "[technical mechanism generalized]"),
}

DECISION_KEYS: dict[str, tuple[str, str]] = {
    "competitors": ("COMPETITOR_REFERENCE", "Competitor references may reveal sponsor identity or strategy."),
    "competitorreferences": ("COMPETITOR_REFERENCE", "Competitor references may reveal sponsor identity or strategy."),
    "confidentialnotes": ("CONFIDENTIAL_TERMINOLOGY", "Confidential notes require an explicit disclosure decision."),
    "internalterminology": ("CONFIDENTIAL_TERMINOLOGY", "Internal terminology may identify the sponsor or project."),
    "proprietaryrationale": ("BUSINESS_STRATEGY", "Proprietary rationale requires an explicit disclosure decision."),
}

SOLUTION_KEYS = {"proposedsolution", "solution", "concept", "productdescription"}
RETAIN_KEYS = {
    "purpose", "researchpurpose", "context", "participantcontext", "topics", "topicstocover",
    "durationminutes", "aiinterviewerdisclosure", "stopnotice", "prototypereference", "question", "questions",
}

EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
SECRET_RE = re.compile(r"\b(?:sk-[A-Za-z0-9_-]{16,}|(?:api|access)[_-]?key\s*[:=]\s*\S+)", re.IGNORECASE)
PRICE_RE = re.compile(r"(?:[$€£]\s?\d|\b\d+(?:\.\d+)?\s?(?:USD|EUR|GBP)\b)", re.IGNORECASE)


@dataclass(frozen=True)
class Finding:
    path: str
    category: str
    recommendation: str
    reason: str

    def as_dict(self) -> dict[str, str]:
        return {
            "path": self.path,
            "category": self.category,
            "recommendation": self.recommendation,
            "reason": self.reason,
        }


_REMOVED = object()


def _normalized_key(key: str) -> str:
    return re.sub(r"[^a-z0-9]", "", key.lower())


def _canonical_hash(value: Any) -> str:
    try:
        payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise DesignCouncilError(f"study must contain JSON-compatible values: {exc}") from exc
    return hashlib.sha256(payload).hexdigest()


def _solution_action(exposure_level: str) -> tuple[str, str, str | None]:
    if exposure_level == "LEVEL_0_PROBLEM_ONLY":
        return "REMOVE", "SOLUTION BLACKOUT removes the proposed solution from problem-only inquiry.", None
    if exposure_level == "LEVEL_1_ABSTRACTED_CONCEPT":
        return "GENERALIZE", "Only an abstracted concept is appropriate at this exposure level.", "[concept abstracted for research]"
    if exposure_level == "LEVEL_2_PROTOTYPE_BLIND":
        return "GENERALIZE", "Expose only the interaction needed for the prototype task.", "[prototype behavior only]"
    return "REQUIRES_USER_DECISION", "Higher-disclosure context requires explicit controls and a user decision.", None


def _classify_leaf(
    key: str,
    value: Any,
    exposure_level: str,
    sensitive_terms: tuple[str, ...],
) -> tuple[str, str, str, Any | None]:
    normalized = _normalized_key(key)
    if normalized in REMOVE_KEYS:
        category, reason = REMOVE_KEYS[normalized]
        return category, "REMOVE", reason, None
    if normalized in GENERALIZE_KEYS:
        category, reason, replacement = GENERALIZE_KEYS[normalized]
        return category, "GENERALIZE", reason, replacement
    if normalized in DECISION_KEYS:
        category, reason = DECISION_KEYS[normalized]
        return category, "REQUIRES_USER_DECISION", reason, None
    if normalized in SOLUTION_KEYS:
        action, reason, replacement = _solution_action(exposure_level)
        return "SOLUTION", action, reason, replacement
    if normalized == "prototypereference" and exposure_level in {"LEVEL_0_PROBLEM_ONLY", "LEVEL_1_ABSTRACTED_CONCEPT"}:
        return "SOLUTION", "REMOVE", "A prototype is unnecessary at this exposure level.", None
    if isinstance(value, str):
        folded = value.casefold()
        if any(term.casefold() in folded for term in sensitive_terms):
            return "CONFIDENTIAL_TERMINOLOGY", "REMOVE", "A caller-designated sensitive term was detected.", None
        if SECRET_RE.search(value):
            return "SECRET", "REMOVE", "A token or secret-like value was detected.", None
        if EMAIL_RE.search(value):
            return "PERSONAL_DATA", "REMOVE", "An email address was detected and is unnecessary by default.", None
        if PRICE_RE.search(value):
            return "PRICING", "REMOVE", "A price or commercial amount was detected.", None
    if normalized in RETAIN_KEYS:
        return "RESEARCH_NECESSARY", "RETAIN", "This field can directly support the stated research interaction.", value
    return "CONFIDENTIAL_TERMINOLOGY", "REQUIRES_USER_DECISION", "This unrecognized field is not on the external-study allow list.", None


def _sanitize(
    value: Any,
    *,
    path: str,
    key: str,
    exposure_level: str,
    sensitive_terms: tuple[str, ...],
    findings: list[Finding],
    inherited: tuple[str, str, str, Any | None] | None = None,
) -> Any:
    rule = inherited or _classify_leaf(key, value, exposure_level, sensitive_terms)
    category, recommendation, reason, replacement = rule

    # Apply non-retain decisions to a sensitive container as a whole. This
    # avoids leaking a structured architecture/source-code object one innocent-
    # looking child at a time. The synthetic root container is only a carrier.
    if path != "external_candidate" and isinstance(value, (dict, list)) and recommendation != "RETAIN":
        findings.append(Finding(path, category, recommendation, reason))
        if recommendation in {"REMOVE", "REQUIRES_USER_DECISION"}:
            return _REMOVED
        return replacement

    if isinstance(value, dict):
        cleaned: dict[str, Any] = {}
        for child_key, child_value in value.items():
            child_path = f"{path}.{child_key}" if path else child_key
            child = _sanitize(
                child_value,
                path=child_path,
                key=child_key,
                exposure_level=exposure_level,
                sensitive_terms=sensitive_terms,
                findings=findings,
            )
            if child is not _REMOVED:
                cleaned[child_key] = child
        return cleaned

    if isinstance(value, list):
        cleaned_items = []
        for index, item in enumerate(value):
            child = _sanitize(
                item,
                path=f"{path}[{index}]",
                key=key,
                exposure_level=exposure_level,
                sensitive_terms=sensitive_terms,
                findings=findings,
                inherited=rule,
            )
            if child is not _REMOVED:
                cleaned_items.append(child)
        return cleaned_items

    findings.append(Finding(path, category, recommendation, reason))
    if recommendation in {"REMOVE", "REQUIRES_USER_DECISION"}:
        return _REMOVED
    if recommendation == "GENERALIZE":
        return replacement
    return copy.deepcopy(value)


def _scan_private_context(
    value: Any,
    *,
    path: str,
    exposure_level: str,
    sensitive_terms: tuple[str, ...],
    findings: list[Finding],
) -> None:
    """Identify private fields without copying any private value into output."""
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}" if path else key
            normalized = _normalized_key(key)
            if normalized in SOLUTION_KEYS:
                action, reason, _ = _solution_action(exposure_level)
                findings.append(Finding(child_path, "SOLUTION", action, reason))
            elif normalized in REMOVE_KEYS:
                category, reason = REMOVE_KEYS[normalized]
                findings.append(Finding(child_path, category, "REMOVE", reason))
            elif normalized in GENERALIZE_KEYS:
                category, reason, _ = GENERALIZE_KEYS[normalized]
                findings.append(Finding(child_path, category, "GENERALIZE", reason))
            elif normalized in DECISION_KEYS:
                category, reason = DECISION_KEYS[normalized]
                findings.append(Finding(child_path, category, "REQUIRES_USER_DECISION", reason))
            _scan_private_context(
                child,
                path=child_path,
                exposure_level=exposure_level,
                sensitive_terms=sensitive_terms,
                findings=findings,
            )
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _scan_private_context(
                child,
                path=f"{path}[{index}]",
                exposure_level=exposure_level,
                sensitive_terms=sensitive_terms,
                findings=findings,
            )
    elif isinstance(value, str):
        folded = value.casefold()
        if any(term.casefold() in folded for term in sensitive_terms):
            findings.append(Finding(path, "CONFIDENTIAL_TERMINOLOGY", "REMOVE", "A caller-designated sensitive term was detected."))
        elif SECRET_RE.search(value):
            findings.append(Finding(path, "SECRET", "REMOVE", "A token or secret-like value was detected."))
        elif EMAIL_RE.search(value):
            findings.append(Finding(path, "PERSONAL_DATA", "REMOVE", "An email address was detected and is unnecessary by default."))
        elif PRICE_RE.search(value):
            findings.append(Finding(path, "PRICING", "REMOVE", "A price or commercial amount was detected."))


def _deduplicate_findings(findings: list[Finding]) -> list[Finding]:
    seen: set[tuple[str, str, str]] = set()
    result: list[Finding] = []
    for item in findings:
        identity = (item.path, item.category, item.recommendation)
        if identity not in seen:
            seen.add(identity)
            result.append(item)
    return result


def _risk_assessment(findings: list[Finding], conflict_enabled: bool) -> dict[str, Any]:
    def residual(category: str) -> str:
        action_rank = {"REMOVE": 0, "GENERALIZE": 1, "REQUIRES_USER_DECISION": 2, "RETAIN": 3}
        level_for_rank = ("NONE", "LOW", "MODERATE", "HIGH")
        relevant = [action_rank[item.recommendation] for item in findings if item.category == category]
        return level_for_rank[max(relevant)] if relevant else "NONE"

    dimensions = {
        "sponsor_identity_exposure": residual("SPONSOR_IDENTITY"),
        "solution_exposure": residual("SOLUTION"),
        "technical_ip_exposure": residual("TECHNICAL_IP"),
        "commercial_strategy_exposure": max(
            (residual("BUSINESS_STRATEGY"), residual("PRICING")),
            key=lambda level: ("NONE", "LOW", "MODERATE", "HIGH").index(level),
        ),
        "competitor_inference_risk": residual("COMPETITOR_REFERENCE"),
        "participant_conflict_risk": "MODERATE" if conflict_enabled else "NONE",
    }
    rank = {"NONE": 0, "LOW": 1, "MODERATE": 2, "HIGH": 3}
    highest = max(rank[value] for value in dimensions.values())
    overall = "HIGH" if highest == 3 else "MODERATE" if highest == 2 else "LOW"
    return {
        **dimensions,
        "overall": overall,
        "legal_guarantee": False,
        "disclaimer": DISCLAIMER,
    }


def _safe_finding_path(path: str, sensitive_terms: tuple[str, ...]) -> str:
    safe = path
    for term in sensitive_terms:
        safe = re.sub(re.escape(term), "[sensitive-field]", safe, flags=re.IGNORECASE)
    safe = EMAIL_RE.sub("[email-field]", safe)
    safe = SECRET_RE.sub("[secret-field]", safe)
    safe = PRICE_RE.sub("[commercial-field]", safe)
    return safe


def build_external_packet(
    internal_study: dict[str, Any],
    *,
    review_id: str = "DR-001",
    packet_id: str = "ESP-001",
    extra_sensitive_terms: tuple[str, ...] = (),
) -> dict[str, Any]:
    """Return a review and sanitized packet without modifying ``internal_study``."""
    if not isinstance(internal_study, dict):
        raise DesignCouncilError("internal study must be a JSON object")
    original = copy.deepcopy(internal_study)
    original_hash = _canonical_hash(original)
    study_id = str(internal_study.get("id", ""))
    if not re.fullmatch(r"STUDY-[0-9]{3,}", study_id):
        raise DesignCouncilError("internal study id must use STUDY-###")

    exposure = internal_study.get("project_exposure", {})
    exposure_level = str(exposure.get("level", "LEVEL_0_PROBLEM_ONLY"))
    if exposure_level not in EXPOSURE_LEVELS:
        raise DesignCouncilError("unsupported project exposure level")
    source = str(internal_study.get("participant_source", {}).get("provider", "BRING_YOUR_OWN"))
    if source not in {"SYNTHETIC", "BRING_YOUR_OWN", "EXCHANGE"}:
        raise DesignCouncilError("unsupported participant source")
    session_type = str(internal_study.get("research_session", {}).get("type", "QUALITATIVE_INTERVIEW"))
    solution_blackout = bool(exposure.get("solution_blackout", exposure_level == "LEVEL_0_PROBLEM_ONLY"))
    if exposure_level == "LEVEL_0_PROBLEM_ONLY":
        solution_blackout = True

    sensitive_terms = tuple(
        term for term in [*internal_study.get("sensitive_terms", []), *extra_sensitive_terms]
        if isinstance(term, str) and len(term) >= 2
    )
    candidate = copy.deepcopy(internal_study.get("external_candidate", {}))
    if not isinstance(candidate, dict):
        raise DesignCouncilError("external_candidate must be an object")
    candidate.setdefault("purpose", internal_study.get("research_goal", "Understand the current experience."))
    candidate.setdefault("context", "We are studying how people currently experience this situation.")
    candidate.setdefault("topics", internal_study.get("topics_to_cover", ["current experience"]))
    candidate.setdefault("duration_minutes", internal_study.get("research_session", {}).get("duration_minutes", 10))
    candidate.setdefault("ai_interviewer_disclosure", "I am an AI interviewer helping a design team learn from your experience.")
    candidate.setdefault("stop_notice", "You may stop the interview at any time.")

    findings: list[Finding] = []
    sanitized = _sanitize(
        candidate,
        path="external_candidate",
        key="external_candidate",
        exposure_level=exposure_level,
        sensitive_terms=sensitive_terms,
        findings=findings,
    )
    if sanitized is _REMOVED or not isinstance(sanitized, dict):
        sanitized = {}
    _scan_private_context(
        internal_study.get("internal_context", {}),
        path="internal_context",
        exposure_level=exposure_level,
        sensitive_terms=sensitive_terms,
        findings=findings,
    )
    findings = _deduplicate_findings(findings)

    def safe_string(key: str, fallback: str) -> str:
        value = sanitized.get(key)
        return value if isinstance(value, str) and value.strip() else fallback

    raw_topics = sanitized.get("topics", sanitized.get("topics_to_cover", []))
    topics = [item for item in raw_topics if isinstance(item, str) and item.strip()] if isinstance(raw_topics, list) else []
    if not topics:
        topics = ["current behavior and recent experiences"]
    duration = sanitized.get("duration_minutes", 10)
    if not isinstance(duration, int) or isinstance(duration, bool) or not 1 <= duration <= 240:
        duration = 10
    prototype_reference = sanitized.get("prototype_reference")
    if exposure_level == "LEVEL_0_PROBLEM_ONLY":
        prototype_reference = None

    requires_decision = any(item.recommendation == "REQUIRES_USER_DECISION" for item in findings)
    omitted = sorted({
        item.category for item in findings
        if item.recommendation in {"REMOVE", "REQUIRES_USER_DECISION"}
    })
    packet = {
        "id": packet_id,
        "internal_study_id": study_id,
        "generated_at": now_utc(),
        "participant_source": source,
        "research_session_type": session_type,
        "project_exposure_level": exposure_level,
        "solution_blackout": solution_blackout,
        "participant_facing": {
            "purpose": safe_string("purpose", "Understand the current experience."),
            "context": safe_string("context", "We are studying how people currently experience this situation."),
            "topics": topics,
            "duration_minutes": duration,
            "prototype_reference": prototype_reference if isinstance(prototype_reference, str) else None,
            "ai_interviewer_disclosure": safe_string("ai_interviewer_disclosure", "I am an AI interviewer helping a design team learn from your experience."),
            "stop_notice": safe_string("stop_notice", "You may stop the interview at any time."),
        },
        "disclosure_review_id": review_id,
        "omitted_categories": omitted,
        "approval_status": "REQUIRES_USER_DECISION" if requires_decision else "DRAFT",
        "consent_version": str(internal_study.get("consent_boundary", {}).get("participant_consent_version") or "consent-v1"),
    }
    conflict_enabled = bool(internal_study.get("conflict_policy", {}).get("enabled", False))
    assessment = _risk_assessment(findings, conflict_enabled)
    review = {
        "id": review_id,
        "study_id": study_id,
        "reviewed_at": now_utc(),
        "exposure_level": exposure_level,
        "original_sha256": original_hash,
        "original_mutated": False,
        "findings": [
            {**item.as_dict(), "path": _safe_finding_path(item.path, sensitive_terms)}
            for item in findings
        ],
        "sanitized_packet_id": packet_id,
        "ip_exposure_assessment": assessment,
        "requires_user_decision": requires_decision,
        "disclaimer": DISCLAIMER,
    }

    if _canonical_hash(internal_study) != original_hash:
        raise DesignCouncilError("internal study changed during disclosure review")
    for document, schema_name in (
        (packet, "external-study-packet.schema.json"),
        (assessment, "ip-exposure-assessment.schema.json"),
        (review, "disclosure-review.schema.json"),
    ):
        validation = schema_validation(document, schema_name)
        if not validation["valid"]:
            raise DesignCouncilError(f"{schema_name} validation failed: " + "; ".join(validation["errors"]))
    return {"review": review, "external_study_packet": packet}


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a minimized external study packet")
    parser.add_argument("input", type=Path, help="private InternalStudy JSON")
    parser.add_argument("--review-id", default="DR-001")
    parser.add_argument("--packet-id", default="ESP-001")
    parser.add_argument("--sensitive-term", action="append", default=[])
    args = parser.parse_args()
    try:
        result = build_external_packet(
            load_json(args.input),
            review_id=args.review_id,
            packet_id=args.packet_id,
            extra_sensitive_terms=tuple(args.sensitive_term),
        )
        json_output(result)
        return 0
    except DesignCouncilError as exc:
        parser.error(str(exc))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
