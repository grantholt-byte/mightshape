#!/usr/bin/env python3
"""Reanalyze a completed paired run without making model calls or overwriting it."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

from run_ab_benchmark import (
    BenchmarkError,
    OUTCOME_CONSTRUCTS_PATH,
    aggregate_results,
    file_digest,
    load_cases,
    load_outcome_constructs,
    render_summary,
    select_cases,
)


def read_jsonl(path: Path) -> list[dict]:
    records: list[dict] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise BenchmarkError(f"{path}:{line_number}: expected an object")
        records.append(value)
    return records


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_dir", type=Path)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args(argv)
    run_dir = args.run_dir.resolve()
    required = ["manifest.json", "generations.jsonl", "judgments.jsonl", "summary.json"]
    missing = [name for name in required if not (run_dir / name).is_file()]
    if missing:
        print("ERROR: missing run files: " + ", ".join(missing), file=sys.stderr)
        return 2
    output_json = run_dir / "summary.reanalysis.json"
    output_md = run_dir / "summary.reanalysis.md"
    if not args.force and (output_json.exists() or output_md.exists()):
        print("ERROR: reanalysis outputs already exist; pass --force to replace them", file=sys.stderr)
        return 2

    manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
    all_cases = load_cases()
    selected = select_cases(all_cases, manifest.get("case_ids", []), None)
    constructs = load_outcome_constructs(all_cases)
    summary = aggregate_results(
        cases=selected,
        pair_plan=manifest["pair_plan"],
        generations=read_jsonl(run_dir / "generations.jsonl"),
        judgments=read_jsonl(run_dir / "judgments.jsonl"),
        bootstrap_samples=int(manifest["bootstrap_samples"]),
        seed=int(manifest["seed"]),
        tie_margin=float(manifest["tie_margin_points"]),
        repeats=int(manifest["repeats"]),
        judge_repetitions=int(manifest["judge_repetitions"]),
        candidate_model=str(manifest["candidate_model"]),
        judge_model=str(manifest["judge_model"]),
        word_cap=int(manifest["word_cap"]),
        minimum_important_uplift=float(
            manifest["preregistered_value_thresholds"]["minimum_important_quality_uplift_points"]
        ),
        max_token_ratio=manifest["preregistered_value_thresholds"].get("maximum_token_ratio"),
        max_token_overhead=manifest["preregistered_value_thresholds"].get("maximum_token_overhead"),
        outcome_constructs=constructs,
        reproducibility=manifest.get("reproducibility"),
    )
    summary["reanalysis"] = {
        "status": "POST_HOC_REPORTING_UPDATE",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source_run_id": manifest.get("run_id"),
        "source_summary_sha256": file_digest(run_dir / "summary.json"),
        "source_runner_sha256": manifest.get("reproducibility", {}).get("runner_sha256"),
        "outcome_construct_registry_sha256": file_digest(OUTCOME_CONSTRUCTS_PATH),
        "note": (
            "Candidate responses, blind judgments, preregistered minimum quality uplift, and token "
            "measurements are unchanged. Effectiveness/resource separation and construct grouping "
            "were added after the run and are labeled post-hoc."
        ),
    }
    render_config = dict(manifest)
    render_config.setdefault("control_mode", "plain")
    output_json.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    output_md.write_text(render_summary(summary, render_config), encoding="utf-8")
    print(f"JSON: {output_json}")
    print(f"Markdown: {output_md}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
