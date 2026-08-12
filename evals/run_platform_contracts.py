#!/usr/bin/env python3
"""Validate adapter parity and map one shared behavioral corpus to each platform.

This runner makes no model calls. It verifies that each generated distribution
can receive every shared case, maps explicit cases to the platform invocation,
and checks package-specific entry points without copying product fixtures.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any


EVAL_ROOT = Path(__file__).resolve().parent
ROOT = EVAL_ROOT.parent

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from evals.run_contracts import CASES_ROOT, FAMILIES, load_cases, validate_corpus  # noqa: E402


PLATFORMS = ("openai", "claude")
PROMPT_POLICIES = {
    "explicit": {"prefix_explicit_invocation"},
    "implicit": {"unchanged"},
    "avoid": {"unchanged"},
}


class PlatformContractFailure(RuntimeError):
    """Raised when a platform eval manifest is malformed."""


def _load_manifest(platform: str) -> dict[str, Any]:
    path = EVAL_ROOT / platform / "manifest.json"
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PlatformContractFailure(f"{path}: cannot load manifest: {exc}") from exc
    if not isinstance(value, dict):
        raise PlatformContractFailure(f"{path}: manifest must be an object")
    return value


def map_prompt(case: dict[str, Any], manifest: dict[str, Any]) -> str:
    """Return the platform-facing prompt without mutating the shared case."""

    invocation = case["invocation"]
    policy = manifest["prompt_mapping"][invocation]
    prompt = case["prompt"]
    if policy == "prefix_explicit_invocation":
        return f"{manifest['explicit_invocation']}\n\n{prompt}"
    return prompt


def validate_platform(platform: str, cases: list[dict[str, Any]]) -> dict[str, Any]:
    errors: list[str] = []
    try:
        manifest = _load_manifest(platform)
    except PlatformContractFailure as exc:
        return {"valid": False, "platform": platform, "case_count": 0, "errors": [str(exc)]}

    required = {
        "schema_version",
        "platform",
        "display_name",
        "package_root",
        "plugin_manifest",
        "skill_entrypoint",
        "explicit_invocation",
        "shared_case_map",
        "prompt_mapping",
        "required_paths",
        "forbidden_paths",
        "text_assertions",
    }
    missing = sorted(required.difference(manifest))
    if missing:
        errors.append("manifest missing fields: " + ", ".join(missing))
        return {"valid": False, "platform": platform, "case_count": 0, "errors": errors}
    if manifest["platform"] != platform:
        errors.append(f"manifest platform {manifest['platform']!r} does not match {platform!r}")

    case_map = manifest.get("shared_case_map", {})
    try:
        source = (ROOT / str(case_map["source"])).resolve()
    except (KeyError, TypeError):
        source = Path()
        errors.append("shared_case_map.source is required")
    if source != CASES_ROOT.resolve():
        errors.append("platform evals must use the canonical evals/cases source")
    if case_map.get("include_families") != "all":
        errors.append("V1 adapters must map every shared behavioral family")

    prompt_mapping = manifest.get("prompt_mapping", {})
    for invocation, allowed in PROMPT_POLICIES.items():
        if prompt_mapping.get(invocation) not in allowed:
            errors.append(
                f"prompt_mapping.{invocation} must be one of {sorted(allowed)}, "
                f"got {prompt_mapping.get(invocation)!r}"
            )

    package_root = (ROOT / str(manifest["package_root"])).resolve()
    if not package_root.is_dir():
        errors.append(f"generated package is missing: {package_root}")
    required_paths = manifest.get("required_paths", [])
    forbidden_paths = manifest.get("forbidden_paths", [])
    if not all(isinstance(item, str) for item in required_paths + forbidden_paths):
        errors.append("required_paths and forbidden_paths must contain only strings")
    else:
        for relative in required_paths:
            if not (package_root / relative).exists():
                errors.append(f"required package path is missing: {relative}")
        for relative in forbidden_paths:
            if (package_root / relative).exists():
                errors.append(f"forbidden cross-platform path is present: {relative}")

    plugin_manifest = package_root / str(manifest["plugin_manifest"])
    skill_entrypoint = package_root / str(manifest["skill_entrypoint"])
    for label, path in (("plugin manifest", plugin_manifest), ("skill entrypoint", skill_entrypoint)):
        if not path.is_file():
            errors.append(f"{label} is missing: {path.relative_to(package_root)}")

    assertions = manifest.get("text_assertions", [])
    if not isinstance(assertions, list):
        errors.append("text_assertions must be an array")
    else:
        for index, assertion in enumerate(assertions):
            if not isinstance(assertion, dict) or not isinstance(assertion.get("path"), str):
                errors.append(f"text_assertions[{index}] must declare path and must_contain")
                continue
            marker = assertion.get("must_contain")
            if not isinstance(marker, str) or not marker:
                errors.append(f"text_assertions[{index}].must_contain must be a non-empty string")
                continue
            target = package_root / assertion["path"]
            if not target.is_file():
                errors.append(f"text assertion target is missing: {assertion['path']}")
                continue
            if marker not in target.read_text(encoding="utf-8"):
                errors.append(f"{assertion['path']} is missing marker: {marker}")

    mapped_ids: list[str] = []
    mapped_invocations: Counter[str] = Counter()
    for case in cases:
        try:
            prompt = map_prompt(case, manifest)
        except (KeyError, TypeError) as exc:
            errors.append(f"could not map case {case.get('id', '<unknown>')}: {exc}")
            continue
        if not prompt.strip():
            errors.append(f"mapped prompt is empty for {case['id']}")
        if case["invocation"] == "explicit" and not prompt.startswith(
            str(manifest["explicit_invocation"])
        ):
            errors.append(f"explicit invocation was not mapped for {case['id']}")
        if case["invocation"] != "explicit" and prompt != case["prompt"]:
            errors.append(f"non-explicit prompt changed for {case['id']}")
        mapped_ids.append(case["id"])
        mapped_invocations[case["invocation"]] += 1

    families = {case["family"] for case in cases}
    if families != FAMILIES:
        errors.append(f"mapped families {sorted(families)} do not match shared families {sorted(FAMILIES)}")
    if len(mapped_ids) != len(cases) or len(set(mapped_ids)) != len(cases):
        errors.append("platform case map must cover every shared case exactly once")

    return {
        "valid": not errors,
        "platform": platform,
        "display_name": manifest["display_name"],
        "case_count": len(mapped_ids),
        "family_count": len(families),
        "invocation_counts": dict(sorted(mapped_invocations.items())),
        "explicit_invocation": manifest["explicit_invocation"],
        "shared_case_source": str(CASES_ROOT.relative_to(ROOT)),
        "errors": errors,
    }


def validate(platforms: tuple[str, ...] = PLATFORMS) -> dict[str, Any]:
    corpus = validate_corpus()
    cases = load_cases() if corpus["valid"] else []
    platform_results = [validate_platform(platform, cases) for platform in platforms]
    errors = [
        f"{item['platform']}: {error}"
        for item in platform_results
        for error in item["errors"]
    ]
    if not corpus["valid"]:
        errors.extend(f"shared corpus: {error}" for error in corpus["errors"])
    return {
        "valid": corpus["valid"] and not errors,
        "shared_case_count": corpus["case_count"],
        "shared_corpus_valid": corpus["valid"],
        "platforms": platform_results,
        "errors": errors,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--platform", choices=("all",) + PLATFORMS, default="all")
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    args = parser.parse_args(argv)
    selected = PLATFORMS if args.platform == "all" else (args.platform,)
    result = validate(selected)
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        status = "PASS" if result["valid"] else "FAIL"
        print(f"{status}: {result['shared_case_count']} shared behavioral cases")
        for item in result["platforms"]:
            print(
                f"{item['display_name']}: {item['case_count']} mapped; "
                f"invocation={item['explicit_invocation']}"
            )
        for error in result["errors"]:
            print(f"ERROR: {error}")
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
