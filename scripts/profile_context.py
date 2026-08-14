#!/usr/bin/env python3
"""Measure static MightShape context-load profiles without calling a model.

The token figure is deliberately a rough, tokenizer-free planning heuristic. Exact
model input and billing usage remain the responsibility of authenticated runtime
measurements.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence


ROOT = Path(__file__).resolve().parents[1]
WORD_PATTERN = re.compile(r"\b\w+(?:[\N{RIGHT SINGLE QUOTATION MARK}'-]\w+)*\b", re.UNICODE)
HEURISTIC_BYTES_PER_TOKEN = 4


class ProfileError(ValueError):
    """Raised when a requested static context resource cannot be measured."""


@dataclass(frozen=True)
class LoadSpec:
    """One planned file load and the reason it preserves route quality."""

    path: str
    reason: str


@dataclass(frozen=True)
class ProfileSpec:
    """A stable, realistic progressive-disclosure resource set."""

    identifier: str
    label: str
    description: str
    loads: tuple[LoadSpec, ...]


BASE_SKILL = LoadSpec(
    "skills/mightshape/SKILL.md",
    "activated routing contract and embedded one-turn method safeguards",
)


PROFILES = (
    ProfileSpec(
        "quick-look",
        "Quick Look",
        "Self-contained one-turn reframe or compact Intake; no reference read.",
        (BASE_SKILL,),
    ),
    ProfileSpec(
        "participatory-first-prompt",
        "Straightforward participatory first prompt",
        "One bounded novice-assisted prompt with participation state and safety intact.",
        (
            BASE_SKILL,
            LoadSpec(
                "skills/mightshape/references/participatory-workshops.md",
                "participation modes, one-prompt loop, controls, and sealed-input rule",
            ),
        ),
    ),
    ProfileSpec(
        "expert-facilitated-workshop",
        "Expert facilitated workshop",
        "Substantive opted-in workshop requiring adaptation, recovery, or debrief craft.",
        (
            BASE_SKILL,
            LoadSpec(
                "skills/mightshape/references/participatory-workshops.md",
                "participation state, turn-taking, contribution, and control contract",
            ),
            LoadSpec(
                "skills/mightshape/references/facilitator-practice.md",
                "expert bottleneck diagnosis, group adaptation, interventions, and debrief",
            ),
        ),
    ),
    ProfileSpec(
        "inquiry-lab",
        "Inquiry Lab",
        "Inquiry route selection before an operation requires an optional specialist file.",
        (
            BASE_SKILL,
            LoadSpec(
                "skills/mightshape/references/inquiry-lab.md",
                "inquiry routes, epistemic boundaries, and synthetic-to-human sequencing",
            ),
        ),
    ),
    ProfileSpec(
        "sealed-panel",
        "Sealed panel",
        "Static resource set for a representative five-member consequential panel.",
        (
            BASE_SKILL,
            LoadSpec(
                "skills/mightshape/references/council-protocol.md",
                "sealed generation, freeze, anonymous mutation, challenge, and synthesis",
            ),
            LoadSpec(
                "skills/mightshape/references/council-mei-tanaka.md",
                "selected member's complete bounded Human Model",
            ),
            LoadSpec(
                "skills/mightshape/references/council-maya-chen.md",
                "selected member's complete bounded Human Model",
            ),
            LoadSpec(
                "skills/mightshape/references/council-priya-rao.md",
                "selected member's complete bounded Human Model",
            ),
            LoadSpec(
                "skills/mightshape/references/council-jack-sullivan.md",
                "selected member's complete bounded Human Model",
            ),
            LoadSpec(
                "skills/mightshape/references/council-rafael-alvarez.md",
                "selected member's complete bounded Human Model",
            ),
        ),
    ),
    ProfileSpec(
        "visual-affinity",
        "Visual affinity",
        "Durable, provenance-preserving affinity artifact in a writable workspace.",
        (
            BASE_SKILL,
            LoadSpec(
                "skills/mightshape/references/visual-workbench.md",
                "durable spatial artifact contract, provenance, accessibility, and export",
            ),
        ),
    ),
)
PROFILE_BY_ID = {profile.identifier: profile for profile in PROFILES}


def heuristic_token_estimate(byte_count: int) -> int:
    """Return the documented byte-ratio heuristic, never a tokenizer result."""

    if byte_count < 0:
        raise ProfileError("byte count cannot be negative")
    return math.ceil(byte_count / HEURISTIC_BYTES_PER_TOKEN)


def word_count(text: str) -> int:
    """Count Unicode word-like spans with one stable, documented expression."""

    return len(WORD_PATTERN.findall(text))


def _relative_resource(root: Path, value: str) -> tuple[Path, str]:
    root = root.resolve()
    candidate = Path(value)
    resolved = candidate.resolve() if candidate.is_absolute() else (root / candidate).resolve()
    try:
        relative = resolved.relative_to(root).as_posix()
    except ValueError as exc:
        raise ProfileError(f"resource is outside profile root: {value}") from exc
    if not resolved.is_file():
        raise ProfileError(f"context resource is not a file: {relative}")
    return resolved, relative


def _metrics(data: bytes, path: str) -> dict[str, object]:
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ProfileError(f"context resource is not UTF-8 text: {path}") from exc
    byte_count = len(data)
    return {
        "bytes": byte_count,
        "words": word_count(text),
        "heuristic_token_estimate": heuristic_token_estimate(byte_count),
    }


def _total_metrics(byte_count: int, words: int) -> dict[str, int]:
    """Measure a whole byte/word total with one application of the heuristic."""

    return {
        "bytes": byte_count,
        "words": words,
        "heuristic_token_estimate": heuristic_token_estimate(byte_count),
    }


def profile_loads(root: Path, profile: ProfileSpec) -> dict[str, object]:
    """Measure a profile and identify repeated paths or byte-identical content."""

    load_results: list[dict[str, object]] = []
    redundancies: list[dict[str, object]] = []
    first_path_event: dict[str, int] = {}
    first_digest_event: dict[str, tuple[int, str]] = {}
    gross_bytes = 0
    gross_words = 0
    unique_bytes = 0
    unique_words = 0

    for order, load in enumerate(profile.loads, start=1):
        resource, relative = _relative_resource(root, load.path)
        data = resource.read_bytes()
        digest = hashlib.sha256(data).hexdigest()
        metrics = _metrics(data, relative)
        gross_bytes += int(metrics["bytes"])
        gross_words += int(metrics["words"])

        redundancy: dict[str, object] | None = None
        if relative in first_path_event:
            first_order = first_path_event[relative]
            redundancy = {
                "kind": "repeated_path",
                "load_order": order,
                "path": relative,
                "duplicates_load_order": first_order,
                "duplicates_path": relative,
            }
        elif digest in first_digest_event:
            first_order, first_path = first_digest_event[digest]
            redundancy = {
                "kind": "identical_content",
                "load_order": order,
                "path": relative,
                "duplicates_load_order": first_order,
                "duplicates_path": first_path,
            }

        if redundancy is None:
            unique_bytes += int(metrics["bytes"])
            unique_words += int(metrics["words"])
            first_digest_event[digest] = (order, relative)
        else:
            redundancies.append(redundancy)

        first_path_event.setdefault(relative, order)
        load_results.append(
            {
                "order": order,
                "path": relative,
                "reason": load.reason,
                "sha256": digest,
                **metrics,
                "redundancy": redundancy,
            }
        )

    gross = _total_metrics(gross_bytes, gross_words)
    unique = _total_metrics(unique_bytes, unique_words)
    redundant = _total_metrics(gross_bytes - unique_bytes, gross_words - unique_words)
    return {
        "id": profile.identifier,
        "label": profile.label,
        "description": profile.description,
        "loads": load_results,
        "totals": {
            "load_events": len(load_results),
            "distinct_paths": len(first_path_event),
            "unique_content_blobs": len(first_digest_event),
            "redundant_load_events": len(redundancies),
            "gross": gross,
            "unique_content": unique,
            "redundant": redundant,
        },
        "redundancies": redundancies,
    }


def build_report(root: Path, profiles: Sequence[ProfileSpec]) -> dict[str, object]:
    """Build a deterministic, timestamp-free report for the requested profiles."""

    return {
        "schema_version": "1.0",
        "measurement": {
            "bytes": "exact on-disk UTF-8 byte count",
            "words": "Unicode word-like spans matched by the profiler's fixed expression",
            "heuristic_token_estimate": (
                "ceil(UTF-8 bytes / 4); rough comparative planning estimate only"
            ),
            "limitations": (
                "No model or tokenizer is called. Estimates are not exact model-input or "
                "billing-token counts and exclude prompts, runtime wrappers, tools, outputs, "
                "caching, and provider-specific tokenization."
            ),
        },
        "profiles": [profile_loads(root, profile) for profile in profiles],
    }


def render_text(report: dict[str, object]) -> str:
    """Render a stable human-readable report with explicit heuristic labeling."""

    measurement = report["measurement"]
    assert isinstance(measurement, dict)
    lines = [
        "STATIC CONTEXT-LOAD PROFILE (no model calls)",
        f"Bytes: {measurement['bytes']}.",
        f"Words: {measurement['words']}.",
        f"HEURISTIC token estimate: {measurement['heuristic_token_estimate']}.",
        f"Limit: {measurement['limitations']}",
    ]
    profiles = report["profiles"]
    assert isinstance(profiles, list)
    for profile in profiles:
        assert isinstance(profile, dict)
        lines.extend(("", f"{profile['label']} [{profile['id']}]", str(profile["description"])))
        loads = profile["loads"]
        assert isinstance(loads, list)
        for load in loads:
            assert isinstance(load, dict)
            marker = " REDUNDANT" if load["redundancy"] is not None else ""
            lines.append(
                f"  {int(load['order']):>2}. {load['path']} | "
                f"{int(load['bytes']):,} bytes | {int(load['words']):,} words | "
                f"~{int(load['heuristic_token_estimate']):,} heuristic tokens{marker}"
            )
            lines.append(f"      {load['reason']}")

        totals = profile["totals"]
        assert isinstance(totals, dict)
        for label, key in (
            ("Gross", "gross"),
            ("Unique content", "unique_content"),
            ("Redundant", "redundant"),
        ):
            values = totals[key]
            assert isinstance(values, dict)
            lines.append(
                f"  {label}: {int(values['bytes']):,} bytes | "
                f"{int(values['words']):,} words | "
                f"~{int(values['heuristic_token_estimate']):,} heuristic tokens"
            )

        redundancies = profile["redundancies"]
        assert isinstance(redundancies, list)
        if redundancies:
            lines.append("  Duplicate/redundant loads:")
            for item in redundancies:
                assert isinstance(item, dict)
                lines.append(
                    f"    - #{item['load_order']} {item['path']} ({item['kind']}) "
                    f"duplicates #{item['duplicates_load_order']} {item['duplicates_path']}"
                )
        else:
            lines.append("  Duplicate/redundant loads: none")
    return "\n".join(lines) + "\n"


def _parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Measure deterministic bytes/words and a clearly labeled static token heuristic "
            "for MightShape's progressive-disclosure routes."
        )
    )
    parser.add_argument(
        "--profile",
        action="append",
        choices=tuple(PROFILE_BY_ID),
        help="profile to report; repeat for several (default: all)",
    )
    parser.add_argument(
        "--extra-load",
        action="append",
        default=[],
        metavar="REPO_RELATIVE_PATH",
        help="append a load to one selected profile, useful for finding accidental duplicates",
    )
    parser.add_argument("--json", action="store_true", help="emit stable JSON instead of text")
    parser.add_argument(
        "--root",
        type=Path,
        default=ROOT,
        help="repository/package root containing the profile resources",
    )
    args = parser.parse_args(argv)
    if args.extra_load and (not args.profile or len(args.profile) != 1):
        parser.error("--extra-load requires exactly one --profile")
    return args


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    selected = list(PROFILES) if not args.profile else [PROFILE_BY_ID[item] for item in args.profile]
    if args.extra_load:
        current = selected[0]
        extras = tuple(LoadSpec(path, "CLI-supplied load for redundancy analysis") for path in args.extra_load)
        selected[0] = ProfileSpec(
            current.identifier,
            current.label,
            current.description,
            current.loads + extras,
        )
    try:
        report = build_report(args.root, selected)
    except (OSError, ProfileError) as exc:
        print(f"profile_context: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(render_text(report), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
