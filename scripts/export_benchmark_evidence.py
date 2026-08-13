#!/usr/bin/env python3
"""Export an auditable, content-safe benchmark bundle for version control.

The benchmark runners keep full local artifacts under ignored result directories.
This exporter retains the frozen manifest, assistant outputs, blinded comparisons,
structured judgments, summaries, and hashes while removing raw process streams.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.verify_v1_trajectory_gate import (  # noqa: E402
    V1TrajectoryGateError,
    require_v1_trajectory_gate,
)


DEFAULT_DESTINATION = ROOT / "evals" / "evidence" / "runs"
RUN_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
REQUIRED_FILES = (
    "manifest.json",
    "generations.jsonl",
    "judgments.jsonl",
    "blinded-pairs.jsonl",
    "summary.json",
    "summary.md",
)
PRIVATE_KEYS = {"stdout", "stderr", "events", "environment", "credentials"}


class EvidenceExportError(ValueError):
    """Raised when a run cannot be exported without weakening traceability."""


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise EvidenceExportError(f"invalid JSON file: {path}") from exc


def _read_jsonl(path: Path) -> list[Any]:
    records: list[Any] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError) as exc:
        raise EvidenceExportError(f"invalid JSONL file: {path}") from exc
    for number, raw in enumerate(lines, start=1):
        if not raw.strip():
            continue
        try:
            records.append(json.loads(raw))
        except json.JSONDecodeError as exc:
            raise EvidenceExportError(f"invalid JSONL at {path}:{number}") from exc
    return records


def strip_private_process_fields(value: Any) -> Any:
    """Recursively remove process-level fields that are not evaluation evidence."""

    if isinstance(value, dict):
        return {
            key: strip_private_process_fields(child)
            for key, child in value.items()
            if key.lower() not in PRIVATE_KEYS
        }
    if isinstance(value, list):
        return [strip_private_process_fields(child) for child in value]
    return value


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode(
        "utf-8"
    )


def _jsonl_bytes(records: Iterable[Any]) -> bytes:
    return "".join(
        json.dumps(record, sort_keys=True, ensure_ascii=False, separators=(",", ":")) + "\n"
        for record in records
    ).encode("utf-8")


def detect_kind(manifest: dict[str, Any]) -> str:
    if "planned_candidate_turn_calls" in manifest:
        return "trajectory"
    if "planned_generation_calls" in manifest:
        return "one_shot_ab"
    raise EvidenceExportError("manifest does not identify a supported benchmark kind")


def validate_complete_summary(kind: str, summary: dict[str, Any]) -> None:
    if kind == "trajectory":
        completion = summary.get("completion")
        if not isinstance(completion, dict):
            raise EvidenceExportError("trajectory summary has no completion record")
        if completion.get("realized_design_complete") is not True:
            raise EvidenceExportError(
                "only a complete realized benchmark design can be exported"
            )
        if completion.get("judgment_plan_complete") is not True:
            raise EvidenceExportError("trajectory judgment plan is incomplete")
        return

    realized = summary.get("realized_design")
    if not isinstance(realized, dict):
        raise EvidenceExportError("one-shot summary has no realized-design record")
    required_flags = (
        "minimum_design_met",
        "all_planned_pairs_usable",
        "plan_shape_complete",
        "requested_repeats_realized",
        "requested_judgments_realized",
    )
    if any(realized.get(flag) is not True for flag in required_flags):
        raise EvidenceExportError(
            "only a complete realized benchmark design can be exported"
        )
    planned = summary.get("planned_pairs")
    complete = summary.get("complete_pairs")
    if not isinstance(planned, int) or isinstance(planned, bool) or planned <= 0:
        raise EvidenceExportError("one-shot summary has an invalid planned-pair count")
    if complete != planned:
        raise EvidenceExportError("one-shot benchmark pair plan is incomplete")


def build_bundle(
    run_dir: Path, *, require_v1_gate: bool = False
) -> tuple[str, dict[str, bytes]]:
    run_dir = run_dir.resolve()
    if not run_dir.is_dir():
        raise EvidenceExportError(f"run directory does not exist: {run_dir}")
    for name in REQUIRED_FILES:
        if not (run_dir / name).is_file():
            raise EvidenceExportError(f"run is missing required artifact: {name}")

    manifest = _read_json(run_dir / "manifest.json")
    summary = _read_json(run_dir / "summary.json")
    if not isinstance(manifest, dict) or not isinstance(summary, dict):
        raise EvidenceExportError("manifest and summary must be JSON objects")
    run_id = manifest.get("run_id")
    if not isinstance(run_id, str) or not RUN_ID_PATTERN.fullmatch(run_id):
        raise EvidenceExportError("manifest run_id is invalid")
    if run_dir.name != run_id:
        raise EvidenceExportError("run directory name and manifest run_id differ")
    kind = detect_kind(manifest)
    validate_complete_summary(kind, summary)
    gate_report: dict[str, Any] | None = None
    if require_v1_gate:
        if kind != "trajectory":
            raise EvidenceExportError(
                "the V1 trajectory gate applies only to trajectory benchmark runs"
            )
        try:
            gate_report = require_v1_trajectory_gate(run_dir, require_snapshot=True)
        except V1TrajectoryGateError as exc:
            raise EvidenceExportError(str(exc)) from exc

    source_hashes = {
        name: sha256_bytes((run_dir / name).read_bytes()) for name in REQUIRED_FILES
    }
    files: dict[str, bytes] = {
        "manifest.json": _json_bytes(strip_private_process_fields(manifest)),
        "summary.json": _json_bytes(strip_private_process_fields(summary)),
        "summary.md": (run_dir / "summary.md").read_bytes(),
        "generations.jsonl": _jsonl_bytes(
            strip_private_process_fields(record)
            for record in _read_jsonl(run_dir / "generations.jsonl")
        ),
        "judgments.jsonl": _jsonl_bytes(
            strip_private_process_fields(record)
            for record in _read_jsonl(run_dir / "judgments.jsonl")
        ),
        "blinded-pairs.jsonl": _jsonl_bytes(
            strip_private_process_fields(record)
            for record in _read_jsonl(run_dir / "blinded-pairs.jsonl")
        ),
    }
    evidence_manifest = {
        "schema_version": "1.0.0",
        "run_id": run_id,
        "benchmark_kind": kind,
        "complete_realized_design": True,
        "v1_trajectory_gate": (
            {
                "verified": True,
                "policy_id": gate_report["policy_id"],
                "policy_sha256": gate_report["policy_sha256"],
                "source_commit": gate_report["source_commit"],
            }
            if gate_report is not None
            else {"verified": False, "reason": "not requested"}
        ),
        "retained": [
            "frozen run manifest",
            "assistant generations and turn-level usage",
            "blinded candidate pairs",
            "structured blind judgments",
            "machine-readable and human-readable summaries",
        ],
        "excluded": [
            "raw stdout and stderr",
            "runtime event streams",
            "environment variables and credentials",
            "copied intervention tree; use the clean Git commit and recorded tree hash",
        ],
        "source_artifact_sha256": source_hashes,
    }
    if gate_report is not None:
        files["v1-trajectory-gate.json"] = _json_bytes(gate_report)
    files["evidence-manifest.json"] = _json_bytes(evidence_manifest)
    checksums = "".join(
        f"{sha256_bytes(data)}  {name}\n" for name, data in sorted(files.items())
    ).encode("utf-8")
    files["SHA256SUMS"] = checksums
    return run_id, files


def write_bundle(destination_root: Path, run_id: str, files: dict[str, bytes]) -> Path:
    destination = destination_root.resolve() / run_id
    if destination.exists():
        raise EvidenceExportError(f"evidence destination already exists: {destination}")
    destination.mkdir(parents=True)
    for name, data in files.items():
        (destination / name).write_bytes(data)
    return destination


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_dir", type=Path)
    parser.add_argument("--destination-root", type=Path, default=DEFAULT_DESTINATION)
    parser.add_argument(
        "--require-v1-gate",
        action="store_true",
        help="fail unless the raw trajectory run passes the committed V1 release policy",
    )
    args = parser.parse_args(argv)
    try:
        run_id, files = build_bundle(
            args.run_dir, require_v1_gate=args.require_v1_gate
        )
        destination = write_bundle(args.destination_root, run_id, files)
    except EvidenceExportError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(destination)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
