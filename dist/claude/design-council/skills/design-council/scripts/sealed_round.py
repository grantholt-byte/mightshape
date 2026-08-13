#!/usr/bin/env python3
"""Prepare, isolate, freeze, and anonymize consequential Council rounds.

No response enters another member's prompt. Files are staged only after isolated
passes finish, and anonymous kernels are unavailable until the complete set is
validated and frozen.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import copy
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from dc_core import DesignCouncilError, REFERENCE_ROOT, SCHEMA_ROOT, dump_json_atomic, json_output, load_json, now_utc, schema_validation


MEMBERS = [
    "maya-chen", "leo-martinez", "priya-rao", "marcus-brooks", "elena-rossi",
    "theo-bennett", "samira-okafor", "jack-sullivan", "mei-tanaka", "rafael-alvarez",
]
MEMBER_NAMES = {
    "maya-chen": "Maya Chen", "leo-martinez": "Leo Martinez", "priya-rao": "Priya Rao",
    "marcus-brooks": "Marcus Brooks", "elena-rossi": "Elena Rossi", "theo-bennett": "Theo Bennett",
    "samira-okafor": "Samira Okafor", "jack-sullivan": "Jack Sullivan", "mei-tanaka": "Mei Tanaka",
    "rafael-alvarez": "Rafael Alvarez",
}
REQUIRED_PACKET = {"round_id", "task", "challenge", "known_evidence", "assumptions", "unknowns", "constraints"}
SIGNATURE_REWRITES = [
    (re.compile(r"what happens when this goes wrong at 5:30 on a Friday\??", re.I), "How does failure unfold under pressure?"),
    (re.compile(r"what(?:'s| is) the crudest thing we can build today[^?]*\??", re.I), "What minimum experiment could reveal whether this works?"),
    (re.compile(r"are we observing behavior[^?]*\??", re.I), "Does the evidence reflect behavior or prompted agreement?"),
    (re.compile(r"who has to do the extra work[^?]*\??", re.I), "Where does incomplete information create hidden work?"),
    (re.compile(r"before we decide what it does[^?]*\??", re.I), "What experience quality matters?"),
    (re.compile(r"what would have to be false[^?]*\??", re.I), "Which falsifiable premise could collapse this concept?"),
    (re.compile(r"whose problem gets solved[^?]*\??", re.I), "How are benefit and burden distributed?"),
    (re.compile(r"what are they doing today[^?]*\??", re.I), "Which current behavior would have to change?"),
    (re.compile(r"which part of this actually needs intelligence\??", re.I), "Where, if anywhere, is computational intelligence necessary?"),
    (re.compile(r"delete the app\.?", re.I), "Remove the current solution form."),
    (re.compile(r"how would a theme park solve this\??", re.I), "Transfer the mechanism from a distant analogous setting."),
    (re.compile(r"what(?:'s| is) the ridiculous version[^?]*\??", re.I), "Use an extreme version to expose a hidden truth."),
]


def _canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _hash_value(value: Any) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _profile_for_sealed_round(member_id: str) -> str:
    path = REFERENCE_ROOT / f"council-{member_id}.md"
    text = path.read_text(encoding="utf-8")
    # Social relationship history may enrich open discussion but cannot enter Round A.
    heading = re.search(r"^## Council relationships[^\n]*\n", text, re.M | re.I)
    if not heading:
        return text
    before = text[: heading.start()].rstrip()
    tail = text[heading.end():].strip()
    if "project memory" in heading.group(0).lower() or "design behavior" in heading.group(0).lower():
        paragraphs = re.split(r"\n\s*\n", tail)
        keep_from = next((index for index, paragraph in enumerate(paragraphs) if paragraph.startswith("Record ") or paragraph.startswith("In divergence") or paragraph.startswith("Project memory")), len(paragraphs))
        retained = "\n\n".join(paragraphs[keep_from:]).strip()
        if retained:
            return before + "\n\n## Sealed-round design and project-memory behavior\n\n" + retained + "\n"
    return before + "\n"


def _prompt_payload(packet: dict[str, Any], member_id: str, memory: dict[str, Any] | None) -> dict[str, Any]:
    response_contract = copy.deepcopy(load_json(SCHEMA_ROOT / "council-response.schema.json"))
    response_contract["properties"]["member_id"] = {"type": "string", "const": member_id}
    return {
        "protocol": "DESIGN_COUNCIL_ROUND_A_SEALED_V1",
        "member_id": member_id,
        "instructions": [
            "Respond as this persistent fictional human, using conclusion-level reasoning rather than hidden chain-of-thought.",
            "Use only the common packet, this one identity model, and this member's own supplied project memory.",
            "Lead with what this person would notice first; do not open with a generic facilitator verdict or a balanced summary that any member could have written.",
            "Be naturally selective rather than mechanically comprehensive: two to four strong ideas are usually enough, and you need not cover every territory.",
            "Let the full life model influence attention, analogy, risk, and language without dumping biography, repeating a signature question, or relying on the occupation label.",
            "Preserve an interpretation, discomfort, or possibility this person would retain even if other competent people might disagree; do not manufacture disagreement when the packet genuinely supports the same conclusion.",
            "Do not mention, infer, cite, praise, rebut, or predict another Council member or any sibling response.",
            "No social relationship history is available. Do not claim direct user or research evidence.",
            "Respect knowledge boundaries; say what is intuition, unknown, or outside expertise.",
            "Return only JSON conforming to council-response.schema.json.",
        ],
        "common_packet": packet,
        "identity_model": _profile_for_sealed_round(member_id),
        "own_project_memory": memory or {},
        "response_contract": response_contract,
    }


def _assert_members(members: list[str]) -> None:
    if not members:
        raise DesignCouncilError("at least one Council member is required")
    if len(members) != len(set(members)):
        raise DesignCouncilError("selected members must be unique")
    unknown = sorted(set(members) - set(MEMBERS))
    if unknown:
        raise DesignCouncilError(f"unknown Council member(s): {', '.join(unknown)}")


def prepare_round(round_dir: str | Path, packet: dict[str, Any], members: list[str], member_memory: dict[str, Any] | None = None) -> dict[str, Any]:
    target = Path(round_dir).resolve()
    _assert_members(members)
    if not isinstance(packet, dict):
        raise DesignCouncilError("common packet must be an object")
    if member_memory is not None and not isinstance(member_memory, dict):
        raise DesignCouncilError("member_memory must be an object keyed by member ID")
    missing = REQUIRED_PACKET - packet.keys()
    if missing:
        raise DesignCouncilError(f"common packet missing: {', '.join(sorted(missing))}")
    round_id = str(packet.get("round_id", ""))
    if not re.fullmatch(r"CR-[0-9]{3,}", round_id):
        raise DesignCouncilError("round_id must match CR-###")
    if target.exists():
        raise DesignCouncilError(f"round directory already exists; never overwrite a prepared round: {target}")
    (target / "prompts").mkdir(parents=True)
    (target / "staged").mkdir()
    packet_path = target / "common-packet.json"
    dump_json_atomic(packet_path, packet)
    os.chmod(packet_path, 0o444)
    prompt_hashes: dict[str, str] = {}
    for member_id in members:
        payload = _prompt_payload(packet, member_id, (member_memory or {}).get(member_id))
        prompt_path = target / "prompts" / f"{member_id}.json"
        dump_json_atomic(prompt_path, payload)
        os.chmod(prompt_path, 0o444)
        prompt_hashes[member_id] = _hash_file(prompt_path)
    manifest = {
        "protocol_version": "1.0.0",
        "round_id": round_id,
        "status": "PREPARED",
        "selected_members": members,
        "prepared_at": now_utc(),
        "packet_hash": _hash_file(packet_path),
        "prompt_hashes": prompt_hashes,
        "response_hashes": {},
        "frozen_at": None,
        "response_set_hash": None,
        "anonymized_at": None,
    }
    dump_json_atomic(target / "manifest.json", manifest)
    return manifest


def _load_verified(round_dir: str | Path, expected_status: set[str] | None = None) -> tuple[Path, dict[str, Any]]:
    target = Path(round_dir).resolve()
    manifest = load_json(target / "manifest.json")
    if expected_status and manifest.get("status") not in expected_status:
        raise DesignCouncilError(f"round status is {manifest.get('status')}; expected {', '.join(sorted(expected_status))}")
    if _hash_file(target / "common-packet.json") != manifest.get("packet_hash"):
        raise DesignCouncilError("common packet changed after prepare; abandon this round and create a new ID")
    for member_id, digest in manifest.get("prompt_hashes", {}).items():
        if _hash_file(target / "prompts" / f"{member_id}.json") != digest:
            raise DesignCouncilError(f"sealed prompt changed for {member_id}; abandon this round")
    return target, manifest


def validate_response(response: dict[str, Any], round_id: str, member_id: str, siblings: list[str]) -> dict[str, Any]:
    result = schema_validation(response, "council-response.schema.json")
    errors = list(result["errors"])
    if response.get("round_id") != round_id:
        errors.append(f"round_id must be {round_id}")
    if response.get("member_id") != member_id:
        errors.append(f"member_id must be {member_id}")
    serialized = json.dumps(response, ensure_ascii=False)
    referenced = []
    for sibling in siblings:
        full = MEMBER_NAMES[sibling]
        first, last = full.split()
        stable_reference = re.search(rf"(?<![a-z])(?:{re.escape(sibling)}|{re.escape(full)})(?![a-z])", serialized, re.I)
        natural_name = re.search(rf"\b(?:{re.escape(first)}|{re.escape(last)})\b", serialized, re.I)
        if stable_reference or natural_name:
            referenced.append(sibling)
    if referenced:
        errors.append("pre-freeze sibling reference(s): " + ", ".join(sorted(referenced)))
    if re.search(r"\b(?:sibling response|response[-_ ]?[0-9]+|earlier response|previous response)\b", serialized, re.I):
        errors.append("response refers to another or earlier response before freeze")
    return {"valid": not errors, "errors": errors, "referenced_siblings": sorted(referenced)}


def stage_response(round_dir: str | Path, response: dict[str, Any]) -> dict[str, Any]:
    target, manifest = _load_verified(round_dir, {"PREPARED", "STAGED"})
    member_id = str(response.get("member_id", ""))
    if member_id not in manifest["selected_members"]:
        raise DesignCouncilError(f"response member {member_id!r} is not selected")
    validation = validate_response(response, manifest["round_id"], member_id, [item for item in manifest["selected_members"] if item != member_id])
    if not validation["valid"]:
        raise DesignCouncilError(f"invalid sealed response for {member_id}: " + "; ".join(validation["errors"]))
    destination = target / "staged" / f"{member_id}.json"
    if destination.exists():
        raise DesignCouncilError(f"response already staged for {member_id}; corrections require a new round ID")
    dump_json_atomic(destination, response)
    manifest["status"] = "STAGED"
    dump_json_atomic(target / "manifest.json", manifest)
    return {"member_id": member_id, "response_hash": _hash_file(destination), "status": "STAGED"}


def _plain_prompt(payload: dict[str, Any]) -> str:
    return (
        "Complete this sealed Design Council Round A pass. You have no sibling output. "
        "Do not use tools or inspect the filesystem. Return only the required JSON.\n\n"
        + json.dumps(payload, indent=2, ensure_ascii=False)
    )


def _run_one(prompt_path: Path, model: str, reasoning_effort: str, timeout: int) -> dict[str, Any]:
    payload = load_json(prompt_path)
    with tempfile.TemporaryDirectory(prefix="dc-sealed-pass-") as directory:
        isolated = Path(directory)
        schema_path = isolated / "response.schema.json"
        dump_json_atomic(schema_path, payload["response_contract"])
        output_path = isolated / "response.json"
        codex_home = isolated / "codex-home"
        codex_home.mkdir()
        source_codex_home = Path(
            os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))
        ).expanduser()
        source_auth = source_codex_home / "auth.json"
        if source_auth.is_file():
            destination_auth = codex_home / "auth.json"
            shutil.copy2(source_auth, destination_auth)
            destination_auth.chmod(0o600)
        environment = os.environ.copy()
        environment["CODEX_HOME"] = str(codex_home)
        command = [
            "codex", "exec", "--ephemeral", "--skip-git-repo-check", "--ignore-user-config", "--ignore-rules",
            "--sandbox", "read-only", "-C", str(isolated), "--output-schema", str(schema_path),
            "--output-last-message", str(output_path), "-m", model,
            "-c", f'model_reasoning_effort="{reasoning_effort}"', "-",
        ]
        completed = subprocess.run(
            command,
            input=_plain_prompt(payload),
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
            env=environment,
        )
        # An optional client may fail during shutdown after Codex has already
        # written the complete structured answer. Prefer that auditable file;
        # complete-set validation below still binds it to this member/round.
        if output_path.is_file():
            try:
                return load_json(output_path)
            except DesignCouncilError:
                pass
        if completed.returncode != 0:
            detail = completed.stderr.strip() or completed.stdout.strip() or "unknown codex exec failure"
            raise DesignCouncilError(f"isolated pass failed for {payload['member_id']}: {detail[-800:]}")
        try:
            return load_json(output_path)
        except DesignCouncilError as exc:
            raise DesignCouncilError(f"isolated pass returned invalid JSON for {payload['member_id']}: {exc}") from exc


def run_round(round_dir: str | Path, model: str = "gpt-5.6-sol", reasoning_effort: str = "high", parallel: int = 4, timeout: int = 600) -> dict[str, Any]:
    target, manifest = _load_verified(round_dir, {"PREPARED"})
    if any((target / "staged").glob("*.json")):
        raise DesignCouncilError("run requires an unstaged prepared round; do not mix manual and model responses")
    members = manifest["selected_members"]
    responses: list[dict[str, Any]] = []
    # Results remain in memory until every independent pass finishes. No response
    # file exists for a later batch to discover.
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, min(parallel, len(members)))) as pool:
        futures = {pool.submit(_run_one, target / "prompts" / f"{member}.json", model, reasoning_effort, timeout): member for member in members}
        for future in concurrent.futures.as_completed(futures):
            member = futures[future]
            try:
                responses.append(future.result())
            except Exception as exc:
                raise DesignCouncilError(f"sealed round aborted before staging ({member}): {exc}") from exc
    # Validate the complete in-memory set before staging any result.
    by_member = {str(item.get("member_id")): item for item in responses}
    if set(by_member) != set(members) or len(responses) != len(members):
        raise DesignCouncilError("isolated passes did not return exactly one response per selected member")
    for member in members:
        validation = validate_response(by_member[member], manifest["round_id"], member, [item for item in members if item != member])
        if not validation["valid"]:
            raise DesignCouncilError(f"sealed response invalid for {member}: " + "; ".join(validation["errors"]))
    staged = [stage_response(target, by_member[member]) for member in members]
    return {"round_id": manifest["round_id"], "model": model, "reasoning_effort": reasoning_effort, "responses": staged}


def freeze_round(round_dir: str | Path) -> dict[str, Any]:
    target, manifest = _load_verified(round_dir, {"PREPARED", "STAGED"})
    members = manifest["selected_members"]
    staged_paths = {path.stem: path for path in (target / "staged").glob("*.json")}
    if set(staged_paths) != set(members):
        missing = sorted(set(members) - set(staged_paths))
        extra = sorted(set(staged_paths) - set(members))
        raise DesignCouncilError(f"cannot freeze incomplete set; missing={missing}, extra={extra}")
    responses = []
    response_hashes = {}
    for member in sorted(members):
        response = load_json(staged_paths[member])
        validation = validate_response(response, manifest["round_id"], member, [item for item in members if item != member])
        if not validation["valid"]:
            raise DesignCouncilError(f"cannot freeze {member}: " + "; ".join(validation["errors"]))
        responses.append(response)
        response_hashes[member] = _hash_value(response)
    frozen = target / "frozen"
    if frozen.exists():
        raise DesignCouncilError("frozen output already exists and is immutable")
    frozen.mkdir()
    response_set = {"round_id": manifest["round_id"], "responses": responses}
    dump_json_atomic(frozen / "responses.json", response_set)
    os.chmod(frozen / "responses.json", 0o444)
    manifest["status"] = "FROZEN"
    manifest["response_hashes"] = response_hashes
    manifest["response_set_hash"] = _hash_value(response_set)
    manifest["frozen_at"] = now_utc()
    dump_json_atomic(target / "manifest.json", manifest)
    return manifest


def _sanitize_anonymous(value: Any) -> Any:
    if isinstance(value, list):
        return [_sanitize_anonymous(item) for item in value]
    if isinstance(value, dict):
        return {key: _sanitize_anonymous(item) for key, item in value.items()}
    if not isinstance(value, str):
        return value
    sanitized = value
    for member_id, full_name in MEMBER_NAMES.items():
        first, last = full_name.split()
        sanitized = re.sub(rf"(?<![a-z])(?:{re.escape(member_id)}|{re.escape(full_name)})(?![a-z])", "the contributor", sanitized, flags=re.I)
        sanitized = re.sub(rf"\b(?:{re.escape(first)}|{re.escape(last)})\b", "the contributor", sanitized, flags=re.I)
    for pattern, replacement in SIGNATURE_REWRITES:
        sanitized = pattern.sub(replacement, sanitized)
    return sanitized


def anonymize_round(round_dir: str | Path) -> dict[str, Any]:
    target, manifest = _load_verified(round_dir, {"FROZEN", "ANONYMIZED"})
    response_set = load_json(target / "frozen" / "responses.json")
    if _hash_value(response_set) != manifest.get("response_set_hash"):
        raise DesignCouncilError("frozen response set hash mismatch")
    destination = target / "anonymous" / "kernels.json"
    if destination.exists():
        return load_json(destination)
    kernels = []
    for index, response in enumerate(response_set["responses"], 1):
        # Do not expose author, lens, profile, or catchphrase. The audit hash is
        # intentionally one-way and can be matched only through the manifest.
        kernels.append({
            "kernel_id": f"KERNEL-{index:03d}",
            "position": _sanitize_anonymous(response["position"]),
            "ideas": _sanitize_anonymous(response["ideas"]),
            "concerns": _sanitize_anonymous(response["concerns"]),
            "questions": _sanitize_anonymous(response["questions"]),
            "source_response_hash": manifest["response_hashes"][response["member_id"]],
            "instruction": "Find the strongest kernel. Extend rather than judge. Combine it with something from your worldview. Produce a mutation the original author probably would not.",
        })
    anonymous = {"round_id": manifest["round_id"], "authorship_removed": True, "kernels": kernels, "created_at": now_utc()}
    destination.parent.mkdir()
    dump_json_atomic(destination, anonymous)
    os.chmod(destination, 0o444)
    manifest["status"] = "ANONYMIZED"
    manifest["anonymized_at"] = anonymous["created_at"]
    dump_json_atomic(target / "manifest.json", manifest)
    return anonymous


def main() -> int:
    parser = argparse.ArgumentParser(description="Manage sealed Design Council Round A generation")
    commands = parser.add_subparsers(dest="command", required=True)
    prepare = commands.add_parser("prepare")
    prepare.add_argument("--round-dir", required=True)
    prepare.add_argument("--packet", required=True)
    prepare.add_argument("--members", required=True, help="Comma-separated member IDs")
    prepare.add_argument("--member-memory")
    stage = commands.add_parser("stage")
    stage.add_argument("--round-dir", required=True)
    stage.add_argument("--response", required=True)
    run = commands.add_parser("run")
    run.add_argument("--round-dir", required=True)
    run.add_argument("--model", default="gpt-5.6-sol")
    run.add_argument("--reasoning-effort", default="high")
    run.add_argument("--parallel", type=int, default=4)
    run.add_argument("--timeout", type=int, default=600)
    freeze = commands.add_parser("freeze")
    freeze.add_argument("--round-dir", required=True)
    anonymize = commands.add_parser("anonymize")
    anonymize.add_argument("--round-dir", required=True)
    status = commands.add_parser("status")
    status.add_argument("--round-dir", required=True)
    args = parser.parse_args()
    try:
        if args.command == "prepare":
            packet = load_json(args.packet)
            memory = load_json(args.member_memory) if args.member_memory else None
            result = prepare_round(args.round_dir, packet, [item.strip() for item in args.members.split(",") if item.strip()], memory)
        elif args.command == "stage":
            result = stage_response(args.round_dir, load_json(args.response))
        elif args.command == "run":
            result = run_round(args.round_dir, args.model, args.reasoning_effort, args.parallel, args.timeout)
        elif args.command == "freeze":
            result = freeze_round(args.round_dir)
        elif args.command == "anonymize":
            result = anonymize_round(args.round_dir)
        else:
            _, result = _load_verified(args.round_dir)
        json_output(result)
    except (DesignCouncilError, subprocess.TimeoutExpired) as exc:
        print(f"Design Council error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
