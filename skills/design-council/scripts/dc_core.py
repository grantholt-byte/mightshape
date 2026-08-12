#!/usr/bin/env python3
"""Shared, dependency-light utilities for Design Council scripts."""

from __future__ import annotations

import json
import os
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


SCHEMA_VERSION = "1.0.0"
SKILL_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_ROOT = SKILL_ROOT / "schemas"
REFERENCE_ROOT = SKILL_ROOT / "references"


class DesignCouncilError(RuntimeError):
    """Raised for user-actionable Design Council contract failures."""


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def load_json(path: str | Path) -> Any:
    target = Path(path)
    try:
        with target.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except FileNotFoundError as exc:
        raise DesignCouncilError(f"File not found: {target}") from exc
    except json.JSONDecodeError as exc:
        raise DesignCouncilError(f"Invalid JSON in {target}: line {exc.lineno}, column {exc.colno}: {exc.msg}") from exc


def dump_json_atomic(path: str | Path, value: Any) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temp_name = tempfile.mkstemp(prefix=f".{target.name}.", suffix=".tmp", dir=target.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(value, handle, indent=2, ensure_ascii=False, sort_keys=False)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, target)
    except Exception:
        try:
            os.unlink(temp_name)
        except FileNotFoundError:
            pass
        raise


def project_dir(project_root: str | Path) -> Path:
    return Path(project_root).resolve() / ".design-council"


def project_file(project_root: str | Path) -> Path:
    return project_dir(project_root) / "project.json"


def next_id(prefix: str, records: Iterable[dict[str, Any]], width: int = 3) -> str:
    pattern = re.compile(rf"^{re.escape(prefix)}-(\d+)$")
    highest = 0
    for record in records:
        match = pattern.match(str(record.get("id", "")))
        if match:
            highest = max(highest, int(match.group(1)))
    return f"{prefix}-{highest + 1:0{width}d}"


def json_output(value: Any) -> None:
    print(json.dumps(value, indent=2, ensure_ascii=False, sort_keys=False))


def schema_validation(instance: Any, schema_name: str) -> dict[str, Any]:
    """Validate with jsonschema when installed; retain a useful basic fallback."""

    schema_path = SCHEMA_ROOT / schema_name
    schema = load_json(schema_path)
    try:
        import jsonschema  # type: ignore
    except ImportError:
        errors: list[str] = []
        if not isinstance(instance, dict):
            errors.append("root must be an object")
        for required in schema.get("required", []):
            if isinstance(instance, dict) and required not in instance:
                errors.append(f"missing required field: {required}")
        return {"valid": not errors, "errors": errors, "validator": "basic-fallback"}

    # Every schema has a stable HTTPS `$id` for interchange, while runtime
    # validation must remain offline. Preload both the canonical IDs and local
    # file URIs so a relative `$ref` can never trigger remote retrieval.
    schema_store: dict[str, Any] = {}
    for candidate in SCHEMA_ROOT.glob("*.json"):
        document = load_json(candidate)
        schema_store[candidate.resolve().as_uri()] = document
        schema_store[candidate.name] = document
        if isinstance(document, dict) and isinstance(document.get("$id"), str):
            schema_store[document["$id"]] = document
    validator_cls = jsonschema.validators.validator_for(schema)
    validator_cls.check_schema(schema)
    try:
        from referencing import Registry, Resource  # type: ignore

        registry = Registry()
        for uri, document in schema_store.items():
            if "://" not in uri:
                continue
            registry = registry.with_resource(uri, Resource.from_contents(document))
        validator = validator_cls(
            schema,
            registry=registry,
            format_checker=jsonschema.FormatChecker(),
        )
    except (ImportError, TypeError):
        # Compatibility with older jsonschema releases.
        resolver = jsonschema.RefResolver(
            base_uri=schema_path.parent.resolve().as_uri() + "/",
            referrer=schema,
            store=schema_store,
        )
        validator = validator_cls(
            schema,
            resolver=resolver,
            format_checker=jsonschema.FormatChecker(),
        )
    errors = []
    for error in sorted(validator.iter_errors(instance), key=lambda item: list(item.absolute_path)):
        location = ".".join(str(part) for part in error.absolute_path) or "$"
        errors.append(f"{location}: {error.message}")
    return {"valid": not errors, "errors": errors, "validator": validator_cls.__name__}
