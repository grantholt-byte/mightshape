#!/usr/bin/env python3
"""Versioned, human-readable project state for Design Council."""

from __future__ import annotations

import copy
import hashlib
import json
import re
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

PROCESS_VIEWS = {"COMPACT", "VISIBLE", "WORKSHOP"}
PARTICIPATION_MODES = {"OBSERVE", "COLLABORATE", "FACILITATED_TURN_BY_TURN"}
FACILITATOR_LEVELS = {"NOVICE_ASSISTED", "GUIDED", "LIGHT_TOUCH"}
ADAPTATION_SOURCES = {"USER_REQUEST", "FACILITATOR_INFERENCE", "SYSTEM_POLICY"}
PARTICIPATION_ACTIVITIES = {
    "BRAINSTORMING",
    "BRAINWRITING",
    "AFFINITY_CLUSTERING",
    "PROCESS_RECONSTRUCTION",
    "ASSUMPTION_MAPPING",
    "POV_HMW",
    "PROTOTYPE_DESIGN",
    "TEST_DESIGN",
}
PARTICIPATION_KINDS = {
    "IDEA",
    "NOTE",
    "SORT_MOVE",
    "CLUSTER_RENAME",
    "PROCESS_STEP",
    "ASSUMPTION",
    "POV_COMPONENT",
    "HMW",
    "PROTOTYPE_DECISION",
    "TEST_DECISION",
}
SEALED_PHASES = {"NONE", "PRE_ROUND", "ROUND_A_OPEN", "POST_FREEZE"}
SEALED_DISPOSITIONS = {"NONE", "COMMON_PACKET_NEXT_ROUND", "HOLD_UNTIL_POST_FREEZE"}


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
            "process_view": "VISIBLE",
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
        "visual_artifacts": [],
        "participation_sessions": [],
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
    if isinstance(state, dict):
        for session in state.get("participation_sessions", []):
            prompts = session.get("prompts", []) if isinstance(session, dict) else []
            prompt_by_id = {
                prompt.get("id"): prompt
                for prompt in prompts
                if isinstance(prompt, dict) and isinstance(prompt.get("id"), str)
            }
            adaptations = session.get("adaptations", []) if isinstance(session, dict) else []
            adaptation_by_id = {
                adaptation.get("id"): adaptation
                for adaptation in adaptations
                if isinstance(adaptation, dict) and isinstance(adaptation.get("id"), str)
            }
            last_adaptation_id = session.get("guidance_state", {}).get("last_adaptation_id")
            if last_adaptation_id is not None and last_adaptation_id not in adaptation_by_id:
                result["errors"].append(
                    f"participation session {session.get('id', '?')} guidance state references an unknown adaptation"
                )
            if sum(prompt.get("status") == "OPEN" for prompt in prompts if isinstance(prompt, dict)) > 1:
                result["errors"].append(
                    f"participation session {session.get('id', '?')} has more than one open prompt"
                )
            for contribution in session.get("contributions", []):
                if not isinstance(contribution, dict):
                    continue
                prompt_id = contribution.get("prompt_id")
                if session.get("mode") == "FACILITATED_TURN_BY_TURN" and prompt_id not in prompt_by_id:
                    result["errors"].append(
                        f"participation session {session.get('id', '?')} turn-by-turn contribution "
                        f"{contribution.get('id', '?')} must reference its participation prompt"
                    )
            for checkpoint in session.get("guidance_checkpoints", []):
                if not isinstance(checkpoint, dict):
                    continue
                if checkpoint.get("prompt_id") not in prompt_by_id:
                    result["errors"].append(
                        f"participation session {session.get('id', '?')} guidance checkpoint "
                        f"{checkpoint.get('id', '?')} must reference its participation prompt"
                    )
                adaptation_id = checkpoint.get("adaptation_id")
                if checkpoint.get("request") in {"SLOWER", "FASTER"} and adaptation_id not in adaptation_by_id:
                    result["errors"].append(
                        f"participation session {session.get('id', '?')} pace guidance checkpoint "
                        f"{checkpoint.get('id', '?')} must reference its adaptation record"
                    )
            for adaptation in adaptations:
                if not isinstance(adaptation, dict):
                    continue
                prompt_id = adaptation.get("prompt_id")
                if prompt_id is not None and prompt_id not in prompt_by_id:
                    result["errors"].append(
                        f"participation session {session.get('id', '?')} adaptation "
                        f"{adaptation.get('id', '?')} references an unknown prompt"
                    )
                allowed_values = (
                    {"SLOWER", "STANDARD", "FASTER"}
                    if adaptation.get("dimension") == "PACE"
                    else FACILITATOR_LEVELS
                )
                if adaptation.get("from") not in allowed_values or adaptation.get("to") not in allowed_values:
                    result["errors"].append(
                        f"participation session {session.get('id', '?')} adaptation "
                        f"{adaptation.get('id', '?')} mixes pace and facilitator-level values"
                    )
            coordination = session.get("sealed_coordination", {}) if isinstance(session, dict) else {}
            if coordination.get("phase") == "ROUND_A_OPEN" and coordination.get("default_disposition") != "HOLD_UNTIL_POST_FREEZE":
                result["errors"].append(
                    f"participation session {session.get('id', '?')} must hold Round A contributions until freeze"
                )
            if coordination.get("round_id") and coordination.get("applies_equally") is not True:
                result["errors"].append(
                    f"participation session {session.get('id', '?')} must apply Council input equally"
                )
            prompts = session.get("prompts", []) if isinstance(session, dict) else []
            if session.get("facilitator_level") == "NOVICE_ASSISTED" and prompts:
                first = prompts[0]
                if not all(first.get(field) for field in ("purpose", "mindset", "example")):
                    result["errors"].append(
                        f"participation session {session.get('id', '?')} must onboard a novice at the first prompt"
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
    (root / "participation").mkdir(parents=True, exist_ok=True)
    (root / "artifacts").mkdir(parents=True, exist_ok=True)
    (root / "exports").mkdir(parents=True, exist_ok=True)
    dump_json_atomic(target, state)
    dump_json_atomic(root / "history" / "rev-000001.json", state)
    return state


def load_project(project_root: str | Path) -> dict[str, Any]:
    value = load_json(project_file(project_root))
    if not isinstance(value, dict):
        raise DesignCouncilError("Project state root must be an object")
    return value


def set_process_view(project_root: str | Path, process_view: str) -> dict[str, Any]:
    """Persist the user's presentation preference without changing methodology."""

    normalized = process_view.upper()
    if normalized not in PROCESS_VIEWS:
        raise DesignCouncilError(f"Unknown process view: {process_view}")
    state = load_project(project_root)
    previous = state.get("classification", {}).get("process_view", "VISIBLE")
    state["classification"]["process_view"] = normalized
    return commit_project(
        project_root,
        state,
        "PROCESS_VIEW_CHANGED",
        {"from": previous, "to": normalized},
    )


def _participation_session(state: dict[str, Any], session_id: str) -> dict[str, Any]:
    for session in state.get("participation_sessions", []):
        if session.get("id") == session_id:
            return session
    raise DesignCouncilError(f"Unknown participation session: {session_id}")


def _all_participation_records(state: dict[str, Any], field: str) -> list[dict[str, Any]]:
    return [
        record
        for session in state.get("participation_sessions", [])
        for record in session.get(field, [])
        if isinstance(record, dict)
    ]


def _open_participation_prompts(session: dict[str, Any]) -> list[dict[str, Any]]:
    return [prompt for prompt in session["prompts"] if prompt.get("status") == "OPEN"]


def _close_open_prompt(session: dict[str, Any], status: str, answered_by: str | None = None) -> str | None:
    open_prompts = _open_participation_prompts(session)
    if not open_prompts:
        return None
    if len(open_prompts) > 1:
        raise DesignCouncilError("participation session has more than one open prompt")
    prompt = open_prompts[0]
    prompt["status"] = status
    prompt["closed_at"] = now_utc()
    prompt["answered_by"] = answered_by
    return str(prompt["id"])


_SECOND_PROMPT_CUE = re.compile(
    r"\b(?:and|then|also)\s+(?:what|why|how|where|when|who|which|"
    r"tell|name|describe|choose|rank|list|explain|identify|compare|add|move|map|write)\b",
    re.IGNORECASE,
)
_NEW_PROMPT_CUE = re.compile(
    r"(?:;|\n)\s*(?:(?:and|then|also)\s+)?(?:what|why|how|where|when|who|which|"
    r"tell|name|describe|choose|rank|list|explain|identify|compare|add|move|map|write)\b",
    re.IGNORECASE,
)


def _is_obviously_compound_prompt(prompt: str) -> bool:
    """Reject only surface-obvious multi-part asks; nuanced language remains facilitator judgment."""

    normalized = prompt.strip()
    if normalized.count("?") > 1:
        return True
    if len(re.findall(r"(?m)^\s*(?:[-*]|\d+[.)])\s+", normalized)) > 1:
        return True
    return bool(_SECOND_PROMPT_CUE.search(normalized) or _NEW_PROMPT_CUE.search(normalized))


def _record_participation_adaptation(
    state: dict[str, Any],
    session: dict[str, Any],
    dimension: str,
    previous: str,
    current: str,
    reason: str,
    source: str,
    prompt_id: str | None,
    timestamp: str,
) -> str:
    normalized_source = source.upper()
    if normalized_source not in ADAPTATION_SOURCES:
        raise DesignCouncilError(f"Unknown participation adaptation source: {source}")
    if not reason.strip():
        raise DesignCouncilError("participation adaptation reason cannot be empty")
    adaptation_id = next_id("UA", _all_participation_records(state, "adaptations"))
    session.setdefault("adaptations", []).append(
        {
            "id": adaptation_id,
            "dimension": dimension,
            "from": previous,
            "to": current,
            "reason": reason.strip(),
            "source": normalized_source,
            "prompt_id": prompt_id,
            "created_at": timestamp,
        }
    )
    session["guidance_state"]["last_adaptation_id"] = adaptation_id
    return adaptation_id


def start_participation(
    project_root: str | Path,
    mode: str,
    activity: str,
    facilitator_level: str = "NOVICE_ASSISTED",
    round_id: str | None = None,
    sealed_phase: str = "NONE",
) -> dict[str, Any]:
    """Start an optional, platform-neutral participatory workshop."""

    normalized_mode = mode.upper()
    normalized_activity = activity.upper()
    normalized_facilitator = facilitator_level.upper()
    normalized_phase = sealed_phase.upper()
    if normalized_mode not in PARTICIPATION_MODES:
        raise DesignCouncilError(f"Unknown participation mode: {mode}")
    if normalized_activity not in PARTICIPATION_ACTIVITIES:
        raise DesignCouncilError(f"Unknown participation activity: {activity}")
    if normalized_facilitator not in FACILITATOR_LEVELS:
        raise DesignCouncilError(f"Unknown facilitator level: {facilitator_level}")
    if normalized_phase not in SEALED_PHASES:
        raise DesignCouncilError(f"Unknown sealed phase: {sealed_phase}")
    if normalized_phase != "NONE" and not round_id:
        raise DesignCouncilError("a sealed Council phase requires round_id")
    if round_id and re.fullmatch(r"CR-[A-Z0-9-]+", round_id) is None:
        raise DesignCouncilError("round_id must use the CR- prefix")
    state = load_project(project_root)
    active = [
        session["id"]
        for session in state.get("participation_sessions", [])
        if session.get("status") in {"ACTIVE", "PAUSED"}
    ]
    if active:
        raise DesignCouncilError(
            f"Participation session {active[-1]} is still active or paused; resume, hand back, or exit it first"
        )
    timestamp = now_utc()
    if normalized_phase == "PRE_ROUND":
        default_disposition = "COMMON_PACKET_NEXT_ROUND"
    elif normalized_phase == "ROUND_A_OPEN":
        default_disposition = "HOLD_UNTIL_POST_FREEZE"
    else:
        default_disposition = "NONE"
    session = {
        "id": next_id("PS", state.get("participation_sessions", [])),
        "mode": normalized_mode,
        "facilitator_level": normalized_facilitator,
        "activity": normalized_activity,
        "status": "ACTIVE",
        "created_at": timestamp,
        "updated_at": timestamp,
        "prompts": [],
        "contributions": [],
        "board_revision": 0,
        "board_changes": [],
        "sealed_coordination": {
            "round_id": round_id,
            "phase": normalized_phase,
            "default_disposition": default_disposition,
            "applies_equally": bool(round_id),
        },
        "guidance_state": {
            "purpose_explained": False,
            "mindset_explained": False,
            "example_shown": False,
            "pace": "STANDARD",
            "last_coaching": None,
            "last_adaptation_id": None,
        },
        "guidance_checkpoints": [],
        "adaptations": [],
        "actions": [
            {
                "action": "START",
                "at": timestamp,
                "details": {"mode": normalized_mode, "facilitator_level": normalized_facilitator},
            }
        ],
    }
    state.setdefault("participation_sessions", []).append(session)
    return commit_project(
        project_root,
        state,
        "PARTICIPATION_STARTED",
        {
            "session_id": session["id"],
            "mode": normalized_mode,
            "facilitator_level": normalized_facilitator,
            "activity": normalized_activity,
        },
    )


def set_participation_mode(
    project_root: str | Path,
    session_id: str,
    mode: str,
) -> dict[str, Any]:
    normalized = mode.upper()
    if normalized not in PARTICIPATION_MODES:
        raise DesignCouncilError(f"Unknown participation mode: {mode}")
    state = load_project(project_root)
    session = _participation_session(state, session_id)
    if session["status"] not in {"ACTIVE", "PAUSED"}:
        raise DesignCouncilError(f"Participation session {session_id} is closed")
    previous = session["mode"]
    if previous == normalized:
        raise DesignCouncilError(f"Participation session is already in {normalized}")
    if normalized == "OBSERVE":
        _close_open_prompt(session, "SKIPPED")
    timestamp = now_utc()
    session["mode"] = normalized
    session["updated_at"] = timestamp
    session["actions"].append(
        {"action": "MODE_CHANGED", "at": timestamp, "details": {"from": previous, "to": normalized}}
    )
    return commit_project(
        project_root,
        state,
        "PARTICIPATION_MODE_CHANGED",
        {"session_id": session_id, "from": previous, "to": normalized},
    )


def set_facilitator_level(
    project_root: str | Path,
    session_id: str,
    facilitator_level: str,
    reason: str | None = None,
    source: str = "USER_REQUEST",
) -> dict[str, Any]:
    normalized = facilitator_level.upper()
    if normalized not in FACILITATOR_LEVELS:
        raise DesignCouncilError(f"Unknown facilitator level: {facilitator_level}")
    state = load_project(project_root)
    session = _participation_session(state, session_id)
    if session["status"] not in {"ACTIVE", "PAUSED"}:
        raise DesignCouncilError(f"Participation session {session_id} is closed")
    previous = session["facilitator_level"]
    if previous == normalized:
        raise DesignCouncilError(f"Facilitator is already using {normalized}")
    if session["guidance_state"].get("pace") == "SLOWER" and normalized == "LIGHT_TOUCH":
        raise DesignCouncilError("SLOWER pace requires GUIDED or NOVICE_ASSISTED scaffolding, not LIGHT_TOUCH")
    open_prompts = _open_participation_prompts(session)
    if len(open_prompts) > 1:
        raise DesignCouncilError("participation session has more than one open prompt")
    timestamp = now_utc()
    resolved_reason = reason.strip() if reason and reason.strip() else f"Explicit change from {previous} to {normalized}."
    adaptation_id = _record_participation_adaptation(
        state,
        session,
        "FACILITATOR_LEVEL",
        previous,
        normalized,
        resolved_reason,
        source,
        str(open_prompts[0]["id"]) if open_prompts else None,
        timestamp,
    )
    session["facilitator_level"] = normalized
    session["updated_at"] = timestamp
    session["actions"].append(
        {
            "action": "FACILITATOR_LEVEL_CHANGED",
            "at": timestamp,
            "details": {
                "from": previous,
                "to": normalized,
                "adaptation_id": adaptation_id,
                "reason": resolved_reason,
                "source": source.upper(),
            },
        }
    )
    return commit_project(
        project_root,
        state,
        "PARTICIPATION_FACILITATOR_LEVEL_CHANGED",
        {
            "session_id": session_id,
            "from": previous,
            "to": normalized,
            "adaptation_id": adaptation_id,
            "reason": resolved_reason,
            "source": source.upper(),
        },
    )


def open_participation_prompt(
    project_root: str | Path,
    session_id: str,
    prompt: str,
    purpose: str | None = None,
    mindset: str | None = None,
    example: str | None = None,
) -> dict[str, Any]:
    if not prompt.strip():
        raise DesignCouncilError("participation prompt cannot be empty")
    if _is_obviously_compound_prompt(prompt):
        raise DesignCouncilError("participation prompt is obviously compound; ask one bounded question at a time")
    state = load_project(project_root)
    session = _participation_session(state, session_id)
    if session["status"] != "ACTIVE":
        raise DesignCouncilError(f"Participation session {session_id} is not active")
    if session["mode"] == "OBSERVE":
        raise DesignCouncilError("OBSERVE mode cannot open a user prompt; switch participation mode first")
    if any(item.get("status") == "OPEN" for item in session["prompts"]):
        raise DesignCouncilError("answer, skip, pause, or close the current prompt before opening another")
    if session["facilitator_level"] == "NOVICE_ASSISTED" and not session["prompts"]:
        if not all(value and value.strip() for value in (purpose, mindset, example)):
            raise DesignCouncilError(
                "the first NOVICE_ASSISTED prompt requires a brief purpose, mindset, and concrete example"
            )
    pace = session["guidance_state"].get("pace", "STANDARD")
    if pace == "SLOWER":
        if session["facilitator_level"] == "LIGHT_TOUCH":
            raise DesignCouncilError("SLOWER pace requires GUIDED or NOVICE_ASSISTED scaffolding, not LIGHT_TOUCH")
        if not all(value and value.strip() for value in (purpose, mindset)):
            raise DesignCouncilError("the next prompt at SLOWER pace requires brief purpose and mindset scaffolding")
    timestamp = now_utc()
    item = {
        "id": next_id("UP", _all_participation_records(state, "prompts")),
        "purpose": purpose.strip() if purpose and purpose.strip() else None,
        "mindset": mindset.strip() if mindset and mindset.strip() else None,
        "example": example.strip() if example and example.strip() else None,
        "prompt": prompt.strip(),
        "guidance_level": session["facilitator_level"],
        "pace": pace,
        "status": "OPEN",
        "created_at": timestamp,
        "closed_at": None,
        "answered_by": None,
    }
    session["prompts"].append(item)
    if item["purpose"]:
        session["guidance_state"]["purpose_explained"] = True
    if item["mindset"]:
        session["guidance_state"]["mindset_explained"] = True
    if item["example"]:
        session["guidance_state"]["example_shown"] = True
    session["updated_at"] = timestamp
    session["actions"].append(
        {"action": "PROMPT_OPENED", "at": timestamp, "details": {"prompt_id": item["id"]}}
    )
    return commit_project(
        project_root,
        state,
        "PARTICIPATION_PROMPT_OPENED",
        {"session_id": session_id, "prompt_id": item["id"]},
    )


def add_participation_contribution(
    project_root: str | Path,
    session_id: str,
    kind: str,
    content: str,
    board_change_summary: str | None = None,
    sealed_disposition: str | None = None,
) -> dict[str, Any]:
    normalized_kind = kind.upper()
    if normalized_kind not in PARTICIPATION_KINDS:
        raise DesignCouncilError(f"Unknown participation contribution kind: {kind}")
    if not content.strip():
        raise DesignCouncilError("participation contribution cannot be empty")
    state = load_project(project_root)
    session = _participation_session(state, session_id)
    if session["status"] != "ACTIVE":
        raise DesignCouncilError(f"Participation session {session_id} is not active")
    if session["mode"] == "OBSERVE":
        raise DesignCouncilError("OBSERVE mode does not accept contributions; switch participation mode first")
    open_prompts = _open_participation_prompts(session)
    if len(open_prompts) > 1:
        raise DesignCouncilError("participation session has more than one open prompt")
    if session["mode"] == "FACILITATED_TURN_BY_TURN" and len(open_prompts) != 1:
        raise DesignCouncilError(
            "FACILITATED_TURN_BY_TURN contributions require exactly one open participation prompt"
        )
    linked_prompt_id = str(open_prompts[0]["id"]) if open_prompts else None
    coordination = session["sealed_coordination"]
    disposition = (sealed_disposition or coordination["default_disposition"]).upper()
    if disposition not in SEALED_DISPOSITIONS:
        raise DesignCouncilError(f"Unknown sealed disposition: {disposition}")
    if coordination["phase"] == "ROUND_A_OPEN" and disposition != "HOLD_UNTIL_POST_FREEZE":
        raise DesignCouncilError("new user input during sealed Round A must be held until post-freeze")
    if coordination["phase"] == "PRE_ROUND" and disposition != "COMMON_PACKET_NEXT_ROUND":
        raise DesignCouncilError("pre-round user input must enter the next common packet equally")
    if disposition != "NONE" and not coordination["round_id"]:
        raise DesignCouncilError("a Council sealed disposition requires a round_id")
    timestamp = now_utc()
    contribution_id = next_id("UC", _all_participation_records(state, "contributions"))
    board_revision = session["board_revision"]
    if board_change_summary:
        board_revision += 1
    item = {
        "id": contribution_id,
        "kind": normalized_kind,
        "content": content.strip(),
        "provenance": "USER_PROVIDED",
        "status": "ACTIVE",
        "supersedes": None,
        "superseded_by": None,
        "board_revision": board_revision,
        "sealed_disposition": disposition,
        "prompt_id": linked_prompt_id,
        "created_at": timestamp,
    }
    session["contributions"].append(item)
    prompt_id = _close_open_prompt(session, "ANSWERED", contribution_id)
    if prompt_id != linked_prompt_id:
        raise DesignCouncilError("participation contribution lost its prompt linkage")
    if board_change_summary:
        session["board_revision"] = board_revision
        session["board_changes"].append(
            {
                "revision": board_revision,
                "summary": board_change_summary.strip(),
                "contribution_ids": [contribution_id],
                "created_at": timestamp,
            }
        )
    session["updated_at"] = timestamp
    session["actions"].append(
        {
            "action": "CONTRIBUTION_ADDED",
            "at": timestamp,
            "details": {"contribution_id": contribution_id, "prompt_id": prompt_id},
        }
    )
    return commit_project(
        project_root,
        state,
        "PARTICIPATION_CONTRIBUTION_ADDED",
        {"session_id": session_id, "contribution_id": contribution_id, "provenance": "USER_PROVIDED"},
    )


def record_participation_guidance(
    project_root: str | Path,
    session_id: str,
    request: str,
    response: str,
    term: str | None = None,
    adaptation_reason: str | None = None,
    adaptation_source: str = "USER_REQUEST",
) -> dict[str, Any]:
    """Record progressive, point-of-use facilitator help without inventing user input."""

    normalized = request.upper()
    if normalized not in {"WHY", "EXAMPLE", "DEFINE", "SLOWER", "FASTER", "COACHING"}:
        raise DesignCouncilError(f"Unknown participation guidance request: {request}")
    if not response.strip():
        raise DesignCouncilError("participation guidance response cannot be empty")
    if normalized == "DEFINE" and not (term and term.strip()):
        raise DesignCouncilError("DEFINE guidance requires the term being explained")
    state = load_project(project_root)
    session = _participation_session(state, session_id)
    if session["status"] not in {"ACTIVE", "PAUSED"}:
        raise DesignCouncilError(f"Participation session {session_id} is closed")
    open_prompts = _open_participation_prompts(session)
    if len(open_prompts) != 1:
        raise DesignCouncilError("participation guidance requires exactly one open participation prompt")
    prompt_id = str(open_prompts[0]["id"])
    timestamp = now_utc()
    adaptation_id: str | None = None
    if normalized in {"SLOWER", "FASTER"}:
        previous_pace = session["guidance_state"].get("pace", "STANDARD")
        next_pace = normalized
        if previous_pace == next_pace:
            raise DesignCouncilError(f"Participation pace is already {next_pace}")
        resolved_reason = (
            adaptation_reason.strip()
            if adaptation_reason and adaptation_reason.strip()
            else response.strip()
        )
        adaptation_id = _record_participation_adaptation(
            state,
            session,
            "PACE",
            previous_pace,
            next_pace,
            resolved_reason,
            adaptation_source,
            prompt_id,
            timestamp,
        )
    item = {
        "id": next_id("UG", _all_participation_records(state, "guidance_checkpoints")),
        "prompt_id": prompt_id,
        "request": normalized,
        "term": term.strip() if term and term.strip() else None,
        "response": response.strip(),
        "adaptation_id": adaptation_id,
        "created_at": timestamp,
    }
    session["guidance_checkpoints"].append(item)
    if normalized == "WHY":
        session["guidance_state"]["purpose_explained"] = True
    elif normalized == "EXAMPLE":
        session["guidance_state"]["example_shown"] = True
    elif normalized == "SLOWER":
        session["guidance_state"]["pace"] = "SLOWER"
    elif normalized == "FASTER":
        session["guidance_state"]["pace"] = "FASTER"
    elif normalized == "COACHING":
        session["guidance_state"]["last_coaching"] = response.strip()
    session["updated_at"] = timestamp
    session["actions"].append(
        {
            "action": "GUIDANCE",
            "at": timestamp,
            "details": {
                "guidance_id": item["id"],
                "prompt_id": prompt_id,
                "request": normalized,
                "adaptation_id": adaptation_id,
            },
        }
    )
    return commit_project(
        project_root,
        state,
        "PARTICIPATION_GUIDANCE_RECORDED",
        {
            "session_id": session_id,
            "guidance_id": item["id"],
            "prompt_id": prompt_id,
            "request": normalized,
            "adaptation_id": adaptation_id,
        },
    )


def participation_action(
    project_root: str | Path,
    session_id: str,
    action: str,
    contribution_id: str | None = None,
    replacement: str | None = None,
) -> dict[str, Any]:
    normalized = action.upper().replace("-", "_")
    allowed = {"SKIP", "PAUSE", "RESUME", "UNDO", "HAND_BACK", "EXIT", "COMPLETE"}
    if normalized not in allowed:
        raise DesignCouncilError(f"Unknown participation action: {action}")
    state = load_project(project_root)
    session = _participation_session(state, session_id)
    timestamp = now_utc()
    details: dict[str, Any] = {}
    action_record = normalized
    if normalized == "SKIP":
        if session["status"] != "ACTIVE":
            raise DesignCouncilError("only an active participation session can skip a prompt")
        prompt_id = _close_open_prompt(session, "SKIPPED")
        if not prompt_id:
            raise DesignCouncilError("there is no open participation prompt to skip")
        details = {"prompt_id": prompt_id}
    elif normalized == "PAUSE":
        if session["status"] != "ACTIVE":
            raise DesignCouncilError("only an active participation session can pause")
        session["status"] = "PAUSED"
    elif normalized == "RESUME":
        if session["status"] != "PAUSED":
            raise DesignCouncilError("only a paused participation session can resume")
        session["status"] = "ACTIVE"
    elif normalized == "UNDO":
        if session["status"] not in {"ACTIVE", "PAUSED"}:
            raise DesignCouncilError("a closed participation session cannot be revised")
        active_contributions = [item for item in session["contributions"] if item["status"] == "ACTIVE"]
        if contribution_id:
            target = next((item for item in active_contributions if item["id"] == contribution_id), None)
        else:
            target = active_contributions[-1] if active_contributions else None
        if target is None:
            raise DesignCouncilError("no matching active contribution can be superseded")
        target["status"] = "SUPERSEDED"
        session["board_revision"] += 1
        related_ids = [target["id"]]
        replacement_id: str | None = None
        if replacement and replacement.strip():
            replacement_id = next_id("UC", _all_participation_records(state, "contributions"))
            replacement_item = {
                "id": replacement_id,
                "kind": target["kind"],
                "content": replacement.strip(),
                "provenance": "USER_PROVIDED",
                "status": "ACTIVE",
                "supersedes": target["id"],
                "superseded_by": None,
                "board_revision": session["board_revision"],
                "sealed_disposition": target["sealed_disposition"],
                "prompt_id": target.get("prompt_id"),
                "created_at": timestamp,
            }
            target["superseded_by"] = replacement_id
            session["contributions"].append(replacement_item)
            related_ids.append(replacement_id)
        session["board_changes"].append(
            {
                "revision": session["board_revision"],
                "summary": f"Superseded {target['id']}" + (f" with {replacement_id}" if replacement_id else ""),
                "contribution_ids": related_ids,
                "created_at": timestamp,
            }
        )
        action_record = "UNDO_SUPERSEDE"
        details = {"contribution_id": target["id"], "replacement_id": replacement_id}
    else:
        if session["status"] not in {"ACTIVE", "PAUSED"}:
            raise DesignCouncilError(f"Participation session {session_id} is already closed")
        _close_open_prompt(session, "SKIPPED")
        session["status"] = {
            "HAND_BACK": "HANDED_BACK",
            "EXIT": "EXITED",
            "COMPLETE": "COMPLETED",
        }[normalized]
    session["updated_at"] = timestamp
    session["actions"].append({"action": action_record, "at": timestamp, "details": details})
    return commit_project(
        project_root,
        state,
        f"PARTICIPATION_{action_record}",
        {"session_id": session_id, **details},
    )


def record_visual_artifact(project_root: str | Path, manifest_path: str | Path) -> dict[str, Any]:
    """Attach a renderer manifest to project history without embedding the visual."""

    root = Path(project_root).resolve()
    path = Path(manifest_path).resolve()
    try:
        portable_path = path.relative_to(root)
    except ValueError as exc:
        raise DesignCouncilError("visual artifact manifest must be inside the project root") from exc
    manifest = load_json(path)
    if not isinstance(manifest, dict):
        raise DesignCouncilError("visual artifact manifest must be an object")
    required = {
        "schema_version",
        "artifact_id",
        "artifact_type",
        "input_sha256",
        "record_count",
        "provenance_counts",
        "source_ids",
        "files",
        "file_sha256",
    }
    missing = sorted(required - set(manifest))
    if missing:
        raise DesignCouncilError("visual artifact manifest is missing: " + ", ".join(missing))
    if manifest["schema_version"] != "1.0.0":
        raise DesignCouncilError("visual artifact manifest has an unsupported schema_version")
    if not isinstance(manifest["artifact_id"], str) or re.fullmatch(r"VA-[A-Z0-9][A-Z0-9-]*", manifest["artifact_id"]) is None:
        raise DesignCouncilError("visual artifact manifest has an invalid artifact_id")
    if manifest["artifact_type"] not in {"AFFINITY_MAP", "PROCESS_MAP"}:
        raise DesignCouncilError("visual artifact manifest has an invalid artifact_type")
    if not isinstance(manifest["input_sha256"], str) or re.fullmatch(r"[a-f0-9]{64}", manifest["input_sha256"]) is None:
        raise DesignCouncilError("visual artifact manifest has an invalid input_sha256")
    if not isinstance(manifest["record_count"], int) or isinstance(manifest["record_count"], bool) or manifest["record_count"] < 0:
        raise DesignCouncilError("visual artifact manifest has an invalid record_count")
    if not isinstance(manifest["provenance_counts"], dict) or any(
        not isinstance(key, str)
        or not isinstance(value, int)
        or isinstance(value, bool)
        or value < 0
        for key, value in manifest["provenance_counts"].items()
    ):
        raise DesignCouncilError("visual artifact manifest has invalid provenance_counts")
    if sum(manifest["provenance_counts"].values()) != manifest["record_count"]:
        raise DesignCouncilError("visual artifact manifest provenance_counts do not match record_count")
    if not isinstance(manifest["source_ids"], list) or any(
        not isinstance(value, str) or not value.strip() for value in manifest["source_ids"]
    ):
        raise DesignCouncilError("visual artifact manifest has invalid source_ids")
    if len(manifest["source_ids"]) != len(set(manifest["source_ids"])):
        raise DesignCouncilError("visual artifact manifest source_ids contains duplicates")
    required_files = {"source", "html", "svg", "markdown"}
    if not isinstance(manifest["files"], dict) or set(manifest["files"]) != required_files or any(
        not isinstance(value, str) or Path(value).name != value for value in manifest["files"].values()
    ):
        raise DesignCouncilError("visual artifact manifest must name local source, html, svg, and markdown files")
    if not isinstance(manifest["file_sha256"], dict) or set(manifest["file_sha256"]) != required_files or any(
        not isinstance(value, str) or re.fullmatch(r"[a-f0-9]{64}", value) is None
        for value in manifest["file_sha256"].values()
    ):
        raise DesignCouncilError("visual artifact manifest has invalid file_sha256 values")
    expected_parent = root / ".design-council" / "artifacts" / manifest["artifact_id"]
    if path.parent != expected_parent:
        raise DesignCouncilError("visual artifact manifest must be stored under its matching VA- artifact directory")
    referenced_files: dict[str, Path] = {}
    for key, filename in manifest["files"].items():
        referenced = (path.parent / filename).resolve()
        try:
            referenced.relative_to(root)
        except ValueError as exc:
            raise DesignCouncilError("visual artifact file resolves outside the project root") from exc
        if not referenced.is_file():
            raise DesignCouncilError(f"visual artifact file is missing: {filename}")
        actual_hash = hashlib.sha256(referenced.read_bytes()).hexdigest()
        if actual_hash != manifest["file_sha256"][key]:
            raise DesignCouncilError(f"visual artifact file hash mismatch: {filename}")
        referenced_files[key] = referenced
    source = load_json(referenced_files["source"])
    if not isinstance(source, dict):
        raise DesignCouncilError("visual artifact source must be an object")
    source_hash = hashlib.sha256(
        json.dumps(source, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()
    if source_hash != manifest["input_sha256"]:
        raise DesignCouncilError("visual artifact source does not match input_sha256")
    try:
        from render_visual import validate_artifact  # local script module; no platform dependency

        source_validation = validate_artifact(source)
    except ImportError as exc:
        raise DesignCouncilError("visual artifact validator is unavailable") from exc
    for source_key, manifest_key in (
        ("artifact_type", "artifact_type"),
        ("record_count", "record_count"),
        ("provenance_counts", "provenance_counts"),
        ("source_ids", "source_ids"),
    ):
        actual = source.get("artifact_type") if source_key == "artifact_type" else source_validation[source_key]
        if actual != manifest[manifest_key]:
            raise DesignCouncilError(f"visual artifact manifest {manifest_key} does not match source")
    if source.get("id") != manifest["artifact_id"]:
        raise DesignCouncilError("visual artifact manifest artifact_id does not match source")
    state = load_project(project_root)
    if any(item.get("artifact_id") == manifest["artifact_id"] for item in state.get("visual_artifacts", [])):
        raise DesignCouncilError(f"visual artifact is already recorded: {manifest['artifact_id']}")
    record = {
        "artifact_id": manifest["artifact_id"],
        "artifact_type": manifest["artifact_type"],
        "input_sha256": manifest["input_sha256"],
        "record_count": manifest["record_count"],
        "provenance_counts": manifest["provenance_counts"],
        "source_ids": manifest["source_ids"],
        "manifest_path": portable_path.as_posix(),
        "files": manifest["files"],
        "file_sha256": manifest["file_sha256"],
        "recorded_at": now_utc(),
    }
    state.setdefault("visual_artifacts", []).append(record)
    return commit_project(
        project_root,
        state,
        "VISUAL_ARTIFACT_RECORDED",
        {"artifact_id": record["artifact_id"], "artifact_type": record["artifact_type"], "input_sha256": record["input_sha256"]},
    )


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
