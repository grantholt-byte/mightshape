#!/usr/bin/env python3
"""Validate the Design Council JSONL behavioral-eval corpus.

This runner intentionally has no required third-party dependencies. When
``jsonschema`` is available it performs full schema validation; otherwise the
same core contract is checked explicitly.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Iterable


EVAL_ROOT = Path(__file__).resolve().parent
CASES_ROOT = EVAL_ROOT / "cases"
FIXTURES_ROOT = EVAL_ROOT / "fixtures"
CASE_SCHEMA_PATH = EVAL_ROOT / "schema" / "case.schema.json"
COVERAGE_PATH = EVAL_ROOT / "required_coverage.json"

FAMILIES = {
    "routing",
    "design_process",
    "council_humanity",
    "council_independence",
    "inquiry",
    "acceptance",
}
INVOCATIONS = {"explicit", "implicit", "avoid"}


class ContractFailure(RuntimeError):
    """Raised when a corpus-level contract is not satisfied."""


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ContractFailure(
            f"{path}: invalid JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}"
        ) from exc


def iter_cases(cases_root: Path = CASES_ROOT) -> Iterable[tuple[Path, int, dict[str, Any]]]:
    paths = sorted(cases_root.glob("*.jsonl"))
    if not paths:
        raise ContractFailure(f"No JSONL case files found beneath {cases_root}")
    for path in paths:
        for line_number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if not raw.strip():
                continue
            try:
                value = json.loads(raw)
            except json.JSONDecodeError as exc:
                raise ContractFailure(
                    f"{path}:{line_number}: invalid JSON: {exc.msg} at column {exc.colno}"
                ) from exc
            if not isinstance(value, dict):
                raise ContractFailure(f"{path}:{line_number}: case must be an object")
            yield path, line_number, value


def load_cases(cases_root: Path = CASES_ROOT) -> list[dict[str, Any]]:
    return [case for _, _, case in iter_cases(cases_root)]


def _basic_validate(case: dict[str, Any], location: str) -> list[str]:
    errors: list[str] = []
    required = {
        "id",
        "family",
        "title",
        "prompt",
        "invocation",
        "adversarial",
        "expected",
        "invariants",
        "automated",
        "tags",
    }
    missing = sorted(required.difference(case))
    if missing:
        errors.append(f"{location}: missing fields: {', '.join(missing)}")
        return errors
    if not isinstance(case["id"], str) or not re.fullmatch(r"[a-z][a-z0-9_]*\.[a-z0-9_]+", case["id"]):
        errors.append(f"{location}: malformed id {case['id']!r}")
    if case["family"] not in FAMILIES:
        errors.append(f"{location}: unknown family {case['family']!r}")
    if case["invocation"] not in INVOCATIONS:
        errors.append(f"{location}: unknown invocation {case['invocation']!r}")
    if not isinstance(case["adversarial"], bool):
        errors.append(f"{location}: adversarial must be boolean")
    if not isinstance(case["prompt"], str) or len(case["prompt"].strip()) < 8:
        errors.append(f"{location}: prompt is too short")
    expected = case["expected"]
    if not isinstance(expected, dict) or not expected.get("must_demonstrate"):
        errors.append(f"{location}: expected.must_demonstrate must be a non-empty array")
    for array_field in ("invariants", "tags"):
        values = case[array_field]
        if not isinstance(values, list) or not values or not all(isinstance(item, str) for item in values):
            errors.append(f"{location}: {array_field} must be a non-empty string array")
        elif len(values) != len(set(values)):
            errors.append(f"{location}: {array_field} contains duplicates")
    automated = case["automated"]
    if not isinstance(automated, dict):
        errors.append(f"{location}: automated must be an object")
    else:
        for regex_group in ("must_match", "must_not_match"):
            patterns = automated.get(regex_group)
            if not isinstance(patterns, list) or not all(isinstance(item, str) for item in patterns):
                errors.append(f"{location}: automated.{regex_group} must be a string array")
                continue
            for pattern in patterns:
                try:
                    re.compile(pattern)
                except re.error as exc:
                    errors.append(f"{location}: invalid regex {pattern!r}: {exc}")
    return errors


def _jsonschema_validator() -> tuple[Any | None, str]:
    schema = load_json(CASE_SCHEMA_PATH)
    try:
        import jsonschema  # type: ignore
    except ImportError:
        return None, "basic-stdlib"
    validator_cls = jsonschema.validators.validator_for(schema)
    validator_cls.check_schema(schema)
    return validator_cls(schema), validator_cls.__name__


def validate_corpus(cases_root: Path = CASES_ROOT) -> dict[str, Any]:
    coverage = load_json(COVERAGE_PATH)
    validator, validator_name = _jsonschema_validator()
    errors: list[str] = []
    warnings: list[str] = []
    cases: list[dict[str, Any]] = []
    seen_ids: dict[str, str] = {}

    for path, line_number, case in iter_cases(cases_root):
        location = f"{path.relative_to(EVAL_ROOT)}:{line_number}"
        cases.append(case)
        errors.extend(_basic_validate(case, location))
        case_id = case.get("id")
        if isinstance(case_id, str):
            if case_id in seen_ids:
                errors.append(f"{location}: duplicate id {case_id!r}; first seen at {seen_ids[case_id]}")
            else:
                seen_ids[case_id] = location
        if validator is not None:
            for error in sorted(validator.iter_errors(case), key=lambda item: list(item.absolute_path)):
                field = ".".join(str(part) for part in error.absolute_path) or "$"
                errors.append(f"{location}:{field}: {error.message}")
        family = case.get("family")
        if isinstance(case_id, str) and isinstance(family, str) and not case_id.startswith(f"{family}."):
            errors.append(f"{location}: id prefix does not match family {family!r}")
        body = json.dumps(case, ensure_ascii=False).lower()
        for marker in coverage["forbidden_placeholder_markers"]:
            if marker.lower() in body:
                errors.append(f"{location}: placeholder marker {marker!r} is forbidden")

    counts = Counter(case.get("family") for case in cases)
    for family, minimum in coverage["minimum_cases_by_family"].items():
        if counts[family] < minimum:
            errors.append(f"family {family!r} has {counts[family]} cases; requires at least {minimum}")

    invariant_counts = Counter(
        invariant
        for case in cases
        for invariant in case.get("invariants", [])
        if isinstance(invariant, str)
    )
    allowed_invariants = set(coverage["required_invariants"])
    missing_invariants = sorted(allowed_invariants.difference(invariant_counts))
    if missing_invariants:
        errors.append("missing required invariant coverage: " + ", ".join(missing_invariants))
    unknown_invariants = sorted(set(invariant_counts).difference(allowed_invariants))
    if unknown_invariants:
        errors.append(
            "unknown invariant keys (update required_coverage.json deliberately): "
            + ", ".join(unknown_invariants)
        )

    missing_acceptance = sorted(set(coverage["required_acceptance_ids"]).difference(seen_ids))
    if missing_acceptance:
        errors.append("missing acceptance cases: " + ", ".join(missing_acceptance))

    adversarial_count = sum(bool(case.get("adversarial")) for case in cases)
    if cases and adversarial_count / len(cases) < 0.35:
        errors.append(
            f"only {adversarial_count}/{len(cases)} cases are adversarial; corpus requires at least 35%"
        )
    avoid_count = sum(case.get("invocation") == "avoid" for case in cases)
    if avoid_count < 3:
        errors.append("at least three inappropriate-trigger avoidance cases are required")

    acceptance_contracts = sorted(FIXTURES_ROOT.glob("*.contract.json"))
    if len(acceptance_contracts) < 2:
        errors.append("family scheduler and ED nurse acceptance contracts are required")
    for contract_path in acceptance_contracts:
        contract = load_json(contract_path)
        if not isinstance(contract, dict) or not contract.get("fixture_id"):
            errors.append(f"{contract_path}: fixture_id is required")
        if not contract.get("required_sequence"):
            errors.append(f"{contract_path}: required_sequence is required")

    if validator is None:
        warnings.append("jsonschema not installed; used explicit standard-library validation")

    return {
        "valid": not errors,
        "validator": validator_name,
        "case_count": len(cases),
        "family_counts": dict(sorted((str(key), value) for key, value in counts.items())),
        "adversarial_count": adversarial_count,
        "avoid_trigger_count": avoid_count,
        "invariant_count": len(invariant_counts),
        "invariant_coverage": dict(sorted(invariant_counts.items())),
        "errors": errors,
        "warnings": warnings,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    parser.add_argument("--cases-root", type=Path, default=CASES_ROOT)
    args = parser.parse_args(argv)
    result = validate_corpus(args.cases_root)
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        status = "PASS" if result["valid"] else "FAIL"
        print(f"{status}: {result['case_count']} cases ({result['adversarial_count']} adversarial)")
        print("Families: " + ", ".join(f"{key}={value}" for key, value in result["family_counts"].items()))
        print(f"Validator: {result['validator']}; invariant families covered: {result['invariant_count']}")
        for warning in result["warnings"]:
            print(f"WARNING: {warning}")
        for error in result["errors"]:
            print(f"ERROR: {error}")
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    sys.exit(main())
