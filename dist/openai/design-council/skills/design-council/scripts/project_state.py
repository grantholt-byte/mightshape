#!/usr/bin/env python3
"""Versioned, human-readable project state for Design Council."""

from __future__ import annotations

import copy
import uuid
from pathlib import Path
from typing import Any

from dc_core import (
    SCHEMA_VERSION,
    DesignCouncilError,
    dump_json_atomic,
    load_json,
    next_id,
    now_utc,
    project_dir,
    project_file,
    schema_validation,
)


MEMBER_IDS = [
    "maya-chen",
    "leo-martinez",
    "priya-rao",
    "marcus-brooks",
    "elena-rossi",
    "theo-bennett",
    "samira-okafor",
    "jack-sullivan",
    "mei-tanaka",
    "rafael-alvarez",
]

PROVENANCE = {
    "OBSERVED_HUMAN_BEHAVIOR",
    "HUMAN_INTERVIEW",
    "USER_PROVIDED",
    "AUTHORITATIVE_RESEARCH",
    "RESEARCH_SUPPORTED_INFERENCE",
    "SYNTHETIC_USER",
    "SYNTHETIC_PRACTITIONER",
    "SYNTHETIC_EXPERT",
    "DESIGN_COUNCIL",
    "ASSUMPTION",
    "UNKNOWN",
}

ZERO_STRENGTH_PROVENANCE = {
    "USER_PROVIDED",
    "SYNTHETIC_USER",
    "SYNTHETIC_PRACTITIONER",
    "SYNTHETIC_EXPERT",
    "DESIGN_COUNCIL",
    "ASSUMPTION",
    "UNKNOWN",
}


def empty_member_memory() -> dict[str, list[dict[str, Any]]]:
    return {
        "positions": [],
        "changes_of_mind": [],
        "ideas_supported": [],
        "ideas_opposed": [],
        "unresolved_questions": [],
        "surprises": [],
        "important_evidence": [],
    }


def new_project_state(
    name: str,
    prompt: str,
    proposed_solution: str | None = None,
    project_id: str | None = None,
) -> dict[str, Any]:
    timestamp = now_utc()
    resolved_id = project_id or f"DC-{uuid.uuid4().hex[:10].upper()}"
    return {
        "schema_version": SCHEMA_VERSION,
        "revision": 1,
        "project": {"id": resolved_id, "name": name, "created": timestamp, "updated": timestamp},
        "challenge": {
            "original_prompt": prompt,
            "proposed_solution": proposed_solution,
            "current_problem_frame": None,
            "desired_outcome": None,
        },
        "classification": {
            "archetypes": [],
            "complexity": "UNKNOWN",
            "reversibility": "UNKNOWN",
            "consequence_of_error": "UNKNOWN",
            "solution_lock_in_risk": "UNKNOWN",
            "operating_depth": "STANDARD",
        },
        "journey": {"current_mode": "INTAKE", "cycle": 1, "completed_modes": [], "transitions": []},
        "stakeholders": [],
        "evidence": [],
        "assumptions": [],
        "unknowns": [],
        "observations": [],
        "needs": [],
        "insights": [],
        "povs": [],
        "hmw_questions": [],
        "ideas": [],
        "concept_clusters": [],
        "outliers": [],
        "selected_concepts": [],
        "prototypes": [],
        "experiments": [],
        "inquiry_studies": [],
        "reality_packets": [],
        "synthetic_personas": [],
        "participants": [],
        "reality_checks": [],
        "decisions": [],
        "minority_reports": [],
        "design_debt": [],
        "evidence_debt": [],
        "build_gate": {
            "status": "NOT_ASSESSED",
            "assessed_at": None,
            "heuristics": {},
            "reasons": [],
            "unresolved_assumptions": [],
            "override": {"active": False, "recorded_at": None, "note": None},
        },
        "council_memory": {member: empty_member_memory() for member in MEMBER_IDS},
        "history": [
            {
                "revision": 1,
                "at": timestamp,
                "action": "PROJECT_INITIALIZED",
                "details": {"original_prompt_preserved": True},
            }
        ],
    }


def validate_state(state: dict[str, Any]) -> dict[str, Any]:
    result = schema_validation(state, "project-state.schema.json")
    history = state.get("history", []) if isinstance(state, dict) else []
    if isinstance(state, dict) and history:
        if history[-1].get("revision") != state.get("revision"):
            result["errors"].append("history last revision does not match project revision")
    if isinstance(state, dict) and state.get("schema_version") != SCHEMA_VERSION:
        result["errors"].append(
            f"unsupported schema_version {state.get('schema_version')!r}; expected {SCHEMA_VERSION}"
        )
    result["valid"] = not result["errors"]
    return result


def initialize_project(
    project_root: str | Path,
    name: str,
    prompt: str,
    proposed_solution: str | None = None,
    project_id: str | None = None,
) -> dict[str, Any]:
    root = project_dir(project_root)
    target = project_file(project_root)
    if target.exists():
        raise DesignCouncilError(f"Project state already exists: {target}. Resume it instead of overwriting history.")
    state = new_project_state(name, prompt, proposed_solution, project_id)
    validation = validate_state(state)
    if not validation["valid"]:
        raise DesignCouncilError("Generated state failed validation: " + "; ".join(validation["errors"]))
    (root / "history").mkdir(parents=True, exist_ok=True)
    (root / "council-rounds").mkdir(parents=True, exist_ok=True)
    (root / "inquiry").mkdir(parents=True, exist_ok=True)
    (root / "exports").mkdir(parents=True, exist_ok=True)
    dump_json_atomic(target, state)
    dump_json_atomic(root / "history" / "rev-000001.json", state)
    return state


def load_project(project_root: str | Path) -> dict[str, Any]:
    value = load_json(project_file(project_root))
    if not isinstance(value, dict):
        raise DesignCouncilError("Project state root must be an object")
    return value


def commit_project(
    project_root: str | Path,
    state: dict[str, Any],
    action: str,
    details: dict[str, Any],
    expected_revision: int | None = None,
) -> dict[str, Any]:
    target = project_file(project_root)
    current = load_project(project_root)
    current_revision = int(current.get("revision", 0))
    source_revision = int(state.get("revision", 0))
    if expected_revision is not None and current_revision != expected_revision:
        raise DesignCouncilError(f"Revision conflict: expected {expected_revision}, found {current_revision}")
    if source_revision != current_revision:
        raise DesignCouncilError(
            f"Refusing stale write: state revision {source_revision}, canonical revision {current_revision}"
        )
    updated = copy.deepcopy(state)
    revision = current_revision + 1
    timestamp = now_utc()
    updated["revision"] = revision
    updated["project"]["updated"] = timestamp
    updated["history"].append({"revision": revision, "at": timestamp, "action": action, "details": details})
    validation = validate_state(updated)
    if not validation["valid"]:
        raise DesignCouncilError("State mutation failed validation: " + "; ".join(validation["errors"]))
    snapshot = project_dir(project_root) / "history" / f"rev-{revision:06d}.json"
    if snapshot.exists():
        raise DesignCouncilError(f"History snapshot already exists; refusing overwrite: {snapshot}")
    dump_json_atomic(target, updated)
    dump_json_atomic(snapshot, updated)
    return updated


def add_evidence(
    project_root: str | Path,
    claim: str,
    provenance: str,
    confidence: float,
    evidence_strength: int,
    source_refs: list[str] | None = None,
    scope: str | None = None,
    study_id: str | None = None,
    participant_id: str | None = None,
    excerpt: str | None = None,
    consent_allows_quote: bool | None = None,
) -> dict[str, Any]:
    if provenance not in PROVENANCE:
        raise DesignCouncilError(f"Unknown provenance: {provenance}")
    if not 0 <= confidence <= 1:
        raise DesignCouncilError("confidence must be between 0 and 1")
    if not 0 <= evidence_strength <= 5:
        raise DesignCouncilError("evidence_strength must be an integer from 0 to 5")
    if provenance in ZERO_STRENGTH_PROVENANCE and evidence_strength != 0:
        raise DesignCouncilError(f"{provenance} must use evidence_strength 0 for real-world claims")
    if provenance == "RESEARCH_SUPPORTED_INFERENCE" and evidence_strength > 2:
        raise DesignCouncilError("RESEARCH_SUPPORTED_INFERENCE may not exceed evidence_strength 2")
    if provenance in {"HUMAN_INTERVIEW", "OBSERVED_HUMAN_BEHAVIOR"} and not participant_id:
        raise DesignCouncilError(f"{provenance} requires participant_id")
    if provenance == "HUMAN_INTERVIEW" and not study_id:
        raise DesignCouncilError("HUMAN_INTERVIEW requires study_id and a transcript source reference")
    if excerpt and consent_allows_quote is not True and provenance in {"HUMAN_INTERVIEW", "OBSERVED_HUMAN_BEHAVIOR"}:
        raise DesignCouncilError("A human excerpt requires consent_allows_quote=true")
    refs = source_refs or []
    if provenance in {"HUMAN_INTERVIEW", "OBSERVED_HUMAN_BEHAVIOR", "AUTHORITATIVE_RESEARCH"} and not refs:
        raise DesignCouncilError(f"{provenance} requires at least one source reference")
    state = load_project(project_root)
    item = {
        "id": next_id("E", state["evidence"]),
        "claim": claim,
        "provenance": provenance,
        "confidence": confidence,
        "evidence_strength": evidence_strength,
        "status": "active" if provenance not in {"ASSUMPTION", "UNKNOWN"} else "unvalidated",
        "source_refs": refs,
        "scope": scope,
        "study_id": study_id,
        "participant_id": participant_id,
        "excerpt": excerpt,
        "consent_allows_quote": consent_allows_quote,
        "created_at": now_utc(),
        "relations": [],
    }
    state["evidence"].append(item)
    return commit_project(project_root, state, "EVIDENCE_ADDED", {"evidence_id": item["id"]})


def add_assumption(
    project_root: str | Path,
    statement: str,
    risk: str,
    importance: str,
    status: str | None = None,
) -> dict[str, Any]:
    risk = risk.upper()
    importance = importance.upper()
    if risk not in {"LOW", "MEDIUM", "HIGH"} or importance not in {"LOW", "MEDIUM", "HIGH"}:
        raise DesignCouncilError("risk and importance must be LOW, MEDIUM, or HIGH")
    resolved_status = status or ("OPEN_HIGH_RISK" if risk == "HIGH" else "OPEN_LOW_RISK")
    if resolved_status not in {"RESOLVED", "TESTING", "OPEN_HIGH_RISK", "OPEN_LOW_RISK", "FALSIFIED"}:
        raise DesignCouncilError(f"Invalid assumption status: {resolved_status}")
    state = load_project(project_root)
    timestamp = now_utc()
    item = {
        "id": next_id("A", state["assumptions"]),
        "statement": statement,
        "status": resolved_status,
        "risk": risk,
        "importance": importance,
        "evidence_ids": [],
        "experiment_ids": [],
        "owner": None,
        "created_at": timestamp,
        "updated_at": timestamp,
        "resolution_note": None,
    }
    state["assumptions"].append(item)
    return commit_project(project_root, state, "ASSUMPTION_ADDED", {"assumption_id": item["id"]})


def set_mode(
    project_root: str | Path,
    new_mode: str,
    reason: str,
    evidence_ids: list[str] | None = None,
) -> dict[str, Any]:
    modes = ["INTAKE", "EMPATHIZE", "DEFINE", "IDEATE", "PROTOTYPE", "TEST", "BUILD"]
    new_mode = new_mode.upper()
    if new_mode not in modes:
        raise DesignCouncilError(f"Invalid mode: {new_mode}")
    state = load_project(project_root)
    old_mode = state["journey"]["current_mode"]
    if old_mode == new_mode:
        raise DesignCouncilError(f"Already in mode {new_mode}")
    backward = modes.index(new_mode) < modes.index(old_mode)
    if backward:
        state["journey"]["cycle"] += 1
    if old_mode not in state["journey"]["completed_modes"]:
        state["journey"]["completed_modes"].append(old_mode)
    transition = {
        "from": old_mode,
        "to": new_mode,
        "at": now_utc(),
        "reason": reason,
        "evidence_ids": evidence_ids or [],
        "direction": "BACKWARD_LEARNING" if backward else "FORWARD",
    }
    state["journey"]["current_mode"] = new_mode
    state["journey"]["transitions"].append(transition)
    return commit_project(project_root, state, "MODE_CHANGED", transition)


def record_council_memory(
    project_root: str | Path,
    member_id: str,
    kind: str,
    statement: str,
    confidence: float | None = None,
    evidence_ids: list[str] | None = None,
    changed_because: list[str] | None = None,
) -> dict[str, Any]:
    if member_id not in MEMBER_IDS:
        raise DesignCouncilError(f"Unknown Council member: {member_id}")
    allowed_kinds = set(empty_member_memory())
    if kind not in allowed_kinds:
        raise DesignCouncilError(f"Invalid memory kind {kind}; choose from {sorted(allowed_kinds)}")
    if confidence is not None and not 0 <= confidence <= 1:
        raise DesignCouncilError("confidence must be between 0 and 1")
    state = load_project(project_root)
    entry: dict[str, Any] = {
        "cycle": state["journey"]["cycle"],
        "statement": statement,
        "evidence_ids": evidence_ids or [],
        "recorded_at": now_utc(),
    }
    if confidence is not None:
        entry["confidence"] = confidence
    if changed_because:
        entry["changed_because"] = changed_because
    if kind == "changes_of_mind" and not changed_because:
        raise DesignCouncilError("changes_of_mind requires changed_because evidence or experiment IDs")
    state["council_memory"][member_id][kind].append(entry)
    return commit_project(
        project_root,
        state,
        "COUNCIL_MEMORY_RECORDED",
        {"member_id": member_id, "kind": kind},
    )


def record_gate_override(project_root: str | Path, note: str) -> dict[str, Any]:
    state = load_project(project_root)
    timestamp = now_utc()
    state["build_gate"]["override"] = {"active": True, "recorded_at": timestamp, "note": note}
    open_high = [item for item in state["assumptions"] if item["status"] == "OPEN_HIGH_RISK"]
    existing_claims = {item["unresolved_claim"] for item in state["design_debt"]}
    for assumption in open_high:
        if assumption["statement"] in existing_claims:
            continue
        state["design_debt"].append(
            {
                "id": next_id("DD", state["design_debt"]),
                "decision": "Proceed after Build Gate override",
                "unresolved_claim": assumption["statement"],
                "consequence": "Implementation may encode an unvalidated user/problem assumption.",
                "mitigation": "Keep the implementation reversible and review after relevant evidence arrives.",
                "review_trigger": f"Evidence or experiment resolving {assumption['id']}",
                "status": "accepted",
                "created_at": timestamp,
            }
        )
    if not any(item["provenance"] in {"HUMAN_INTERVIEW", "OBSERVED_HUMAN_BEHAVIOR"} for item in state["evidence"]):
        if not any(item["unresolved_claim"] == "Human grounding is absent" for item in state["evidence_debt"]):
            state["evidence_debt"].append(
                {
                    "id": next_id("ED", state["evidence_debt"]),
                    "decision": "Proceed after Build Gate override",
                    "unresolved_claim": "Human grounding is absent",
                    "consequence": "Consequential design choices may rely on inference or synthetic signals.",
                    "mitigation": "Schedule a Reality Check or human test at the earliest useful point.",
                    "review_trigger": "First relevant human interview or observation",
                    "status": "accepted",
                    "created_at": timestamp,
                }
            )
    return commit_project(project_root, state, "BUILD_GATE_OVERRIDDEN", {"note": note})
