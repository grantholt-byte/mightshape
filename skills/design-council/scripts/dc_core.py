#!/usr/bin/env python3
"""Shared, dependency-light utilities for Design Council scripts."""

from __future__ import annotations

import json
import math
import os
import re
import tempfile
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import unquote, urlsplit


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


_SCHEMA_TYPES = {"array", "boolean", "integer", "null", "number", "object", "string"}
_SCHEMA_FORMATS = {"date", "date-time", "uri"}
_SCHEMA_ANNOTATIONS = {
    "$comment",
    "$id",
    "$schema",
    "default",
    "deprecated",
    "description",
    "examples",
    "readOnly",
    "title",
    "writeOnly",
}
_SCHEMA_KEYWORDS = _SCHEMA_ANNOTATIONS | {
    "$defs",
    "$ref",
    "additionalProperties",
    "allOf",
    "anyOf",
    "const",
    "dependentRequired",
    "dependentSchemas",
    "else",
    "enum",
    "exclusiveMaximum",
    "exclusiveMinimum",
    "format",
    "if",
    "items",
    "maxItems",
    "maxLength",
    "maxProperties",
    "maximum",
    "minItems",
    "minLength",
    "minProperties",
    "minimum",
    "not",
    "oneOf",
    "pattern",
    "patternProperties",
    "properties",
    "required",
    "then",
    "type",
    "uniqueItems",
}


def _schema_location(parts: tuple[str | int, ...]) -> str:
    return ".".join(str(part) for part in parts) or "$"


def _schema_error(parts: tuple[str | int, ...], message: str) -> DesignCouncilError:
    return DesignCouncilError(f"Unsupported or invalid JSON Schema at {_schema_location(parts)}: {message}")


def _is_nonnegative_integer(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _is_json_number(value: Any) -> bool:
    if isinstance(value, bool):
        return False
    if isinstance(value, int):
        return True
    return isinstance(value, float) and math.isfinite(value)


def _check_schema_contract(schema: Any, parts: tuple[str | int, ...] = ()) -> None:
    """Reject malformed or unsupported schema features before validating data.

    Design Council intentionally owns a small Draft 2020-12 subset. Rejecting
    unknown validation keywords prevents a future schema edit from silently
    weakening the dependency-free runtime.
    """

    if isinstance(schema, bool):
        return
    if not isinstance(schema, dict):
        raise _schema_error(parts, "a schema must be an object or boolean")
    unknown = sorted(set(schema) - _SCHEMA_KEYWORDS)
    if unknown:
        raise _schema_error(parts, "unsupported keyword(s): " + ", ".join(unknown))

    for key in ("$schema", "$id", "$ref", "$comment", "title", "description", "format"):
        if key in schema and not isinstance(schema[key], str):
            raise _schema_error(parts + (key,), "must be a string")
    if "format" in schema and schema["format"] not in _SCHEMA_FORMATS:
        raise _schema_error(parts + ("format",), f"unsupported format {schema['format']!r}")

    if "type" in schema:
        declared = schema["type"]
        values = [declared] if isinstance(declared, str) else declared
        if (
            not isinstance(values, list)
            or not values
            or any(not isinstance(item, str) or item not in _SCHEMA_TYPES for item in values)
            or len(values) != len(set(values))
        ):
            raise _schema_error(parts + ("type",), "must name one or more unique supported types")
    if "enum" in schema and (not isinstance(schema["enum"], list) or not schema["enum"]):
        raise _schema_error(parts + ("enum",), "must be a non-empty array")

    for key in ("required",):
        if key in schema:
            value = schema[key]
            if (
                not isinstance(value, list)
                or any(not isinstance(item, str) for item in value)
                or len(value) != len(set(value))
            ):
                raise _schema_error(parts + (key,), "must be an array of unique strings")
    for key in ("minItems", "maxItems", "minLength", "maxLength", "minProperties", "maxProperties"):
        if key in schema and not _is_nonnegative_integer(schema[key]):
            raise _schema_error(parts + (key,), "must be a non-negative integer")
    for minimum_key, maximum_key in (
        ("minItems", "maxItems"),
        ("minLength", "maxLength"),
        ("minProperties", "maxProperties"),
    ):
        if minimum_key in schema and maximum_key in schema and schema[minimum_key] > schema[maximum_key]:
            raise _schema_error(parts, f"{minimum_key} cannot exceed {maximum_key}")
    for key in ("minimum", "maximum", "exclusiveMinimum", "exclusiveMaximum"):
        if key in schema and not _is_json_number(schema[key]):
            raise _schema_error(parts + (key,), "must be a finite number")
    if "pattern" in schema:
        if not isinstance(schema["pattern"], str):
            raise _schema_error(parts + ("pattern",), "must be a string")
        try:
            re.compile(schema["pattern"])
        except re.error as exc:
            raise _schema_error(parts + ("pattern",), f"invalid regular expression: {exc}") from exc
    if "uniqueItems" in schema and not isinstance(schema["uniqueItems"], bool):
        raise _schema_error(parts + ("uniqueItems",), "must be boolean")

    for key in ("$defs", "properties", "patternProperties", "dependentSchemas"):
        if key not in schema:
            continue
        mapping = schema[key]
        if not isinstance(mapping, dict) or any(not isinstance(name, str) for name in mapping):
            raise _schema_error(parts + (key,), "must be an object of schemas")
        if key == "patternProperties":
            for pattern in mapping:
                try:
                    re.compile(pattern)
                except re.error as exc:
                    raise _schema_error(parts + (key, pattern), f"invalid regular expression: {exc}") from exc
        for name, child in mapping.items():
            _check_schema_contract(child, parts + (key, name))

    if "dependentRequired" in schema:
        dependencies = schema["dependentRequired"]
        if not isinstance(dependencies, dict):
            raise _schema_error(parts + ("dependentRequired",), "must be an object")
        for name, required in dependencies.items():
            if (
                not isinstance(name, str)
                or not isinstance(required, list)
                or any(not isinstance(item, str) for item in required)
                or len(required) != len(set(required))
            ):
                raise _schema_error(
                    parts + ("dependentRequired", str(name)),
                    "must be an array of unique strings",
                )

    for key in ("additionalProperties", "items", "not", "if", "then", "else"):
        if key in schema:
            _check_schema_contract(schema[key], parts + (key,))
    for key in ("allOf", "anyOf", "oneOf"):
        if key not in schema:
            continue
        branches = schema[key]
        if not isinstance(branches, list) or not branches:
            raise _schema_error(parts + (key,), "must be a non-empty array of schemas")
        for index, child in enumerate(branches):
            _check_schema_contract(child, parts + (key, index))


def _json_equal(left: Any, right: Any) -> bool:
    """JSON-aware equality: booleans are not numbers, while 1 equals 1.0."""

    if _is_json_number(left) and _is_json_number(right):
        return left == right
    if type(left) is not type(right):
        return False
    if isinstance(left, dict):
        return left.keys() == right.keys() and all(
            _json_equal(left[key], right[key]) for key in left
        )
    if isinstance(left, list):
        return len(left) == len(right) and all(
            _json_equal(left_item, right_item)
            for left_item, right_item in zip(left, right)
        )
    return left == right


def _matches_type(instance: Any, expected: str) -> bool:
    if expected == "null":
        return instance is None
    if expected == "boolean":
        return isinstance(instance, bool)
    if expected == "object":
        return isinstance(instance, dict)
    if expected == "array":
        return isinstance(instance, list)
    if expected == "string":
        return isinstance(instance, str)
    if expected == "number":
        return _is_json_number(instance)
    if expected == "integer":
        if isinstance(instance, int) and not isinstance(instance, bool):
            return True
        return isinstance(instance, float) and math.isfinite(instance) and instance.is_integer()
    return False


_RFC3339_DATE_TIME = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$"
)
_URI_SCHEME = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*$")


def _valid_format(value: str, format_name: str) -> bool:
    try:
        if format_name == "date":
            return date.fromisoformat(value).isoformat() == value
        if format_name == "date-time":
            if _RFC3339_DATE_TIME.fullmatch(value) is None:
                return False
            datetime.fromisoformat(value[:-1] + "+00:00" if value.endswith("Z") else value)
            return True
        if format_name == "uri":
            if any(character.isspace() or ord(character) < 0x20 for character in value):
                return False
            parsed = urlsplit(value)
            return bool(parsed.scheme and _URI_SCHEME.fullmatch(parsed.scheme))
    except (TypeError, ValueError):
        return False
    return False


class _StdlibSchemaValidator:
    """Dependency-free validator for Design Council's owned schema subset."""

    def __init__(self, root_path: Path, root_schema: dict[str, Any] | bool):
        self.root_path = root_path.resolve()
        self.documents: dict[Path, Any] = {self.root_path: root_schema}
        self.checked_documents: set[Path] = set()

    def _load_document(self, path: Path) -> Any:
        resolved = path.resolve()
        try:
            resolved.relative_to(SCHEMA_ROOT.resolve())
        except ValueError as exc:
            raise DesignCouncilError(f"Schema reference leaves the schema directory: {path}") from exc
        if resolved not in self.documents:
            self.documents[resolved] = load_json(resolved)
        if resolved not in self.checked_documents:
            _check_schema_contract(self.documents[resolved], (resolved.name,))
            self.checked_documents.add(resolved)
        return self.documents[resolved]

    def _resolve_ref(self, reference: str, current_path: Path) -> tuple[Any, Path]:
        file_part, separator, fragment = reference.partition("#")
        if file_part:
            candidate = (current_path.parent / unquote(file_part)).resolve()
            document = self._load_document(candidate)
            resolved_path = candidate
        else:
            document = self._load_document(current_path)
            resolved_path = current_path
        if not separator or not fragment:
            return document, resolved_path
        decoded = unquote(fragment)
        if not decoded.startswith("/"):
            raise DesignCouncilError(f"Unsupported schema reference fragment: {reference}")
        target = document
        for raw_part in decoded[1:].split("/"):
            part = raw_part.replace("~1", "/").replace("~0", "~")
            if isinstance(target, dict) and part in target:
                target = target[part]
            elif isinstance(target, list) and part.isdigit() and int(part) < len(target):
                target = target[int(part)]
            else:
                raise DesignCouncilError(f"Unresolved schema reference: {reference}")
        if not isinstance(target, (dict, bool)):
            raise DesignCouncilError(f"Schema reference does not resolve to a schema: {reference}")
        return target, resolved_path

    def errors(self, instance: Any) -> list[str]:
        self._load_document(self.root_path)
        errors: list[str] = []
        self._validate(instance, self.documents[self.root_path], self.root_path, (), errors, 0)
        return errors

    def _branch_errors(
        self,
        instance: Any,
        schema: Any,
        current_path: Path,
        instance_path: tuple[str | int, ...],
        depth: int,
    ) -> list[str]:
        errors: list[str] = []
        self._validate(instance, schema, current_path, instance_path, errors, depth + 1)
        return errors

    def _validate(
        self,
        instance: Any,
        schema: Any,
        current_path: Path,
        instance_path: tuple[str | int, ...],
        errors: list[str],
        depth: int,
    ) -> None:
        if depth > 256:
            raise DesignCouncilError("Schema validation exceeded the safe reference depth")
        location = _schema_location(instance_path)
        if schema is True:
            return
        if schema is False:
            errors.append(f"{location}: value is forbidden by schema")
            return

        if "$ref" in schema:
            target, target_path = self._resolve_ref(schema["$ref"], current_path)
            self._validate(instance, target, target_path, instance_path, errors, depth + 1)

        for child in schema.get("allOf", []):
            self._validate(instance, child, current_path, instance_path, errors, depth + 1)
        if "anyOf" in schema:
            branch_results = [
                self._branch_errors(instance, child, current_path, instance_path, depth)
                for child in schema["anyOf"]
            ]
            if all(branch for branch in branch_results):
                errors.append(f"{location}: value does not match any allowed schema")
        if "oneOf" in schema:
            matches = sum(
                not self._branch_errors(instance, child, current_path, instance_path, depth)
                for child in schema["oneOf"]
            )
            if matches != 1:
                errors.append(f"{location}: value must match exactly one allowed schema (matched {matches})")
        if "not" in schema and not self._branch_errors(
            instance, schema["not"], current_path, instance_path, depth
        ):
            errors.append(f"{location}: value matches a forbidden schema")
        if "if" in schema:
            condition_matches = not self._branch_errors(
                instance, schema["if"], current_path, instance_path, depth
            )
            branch = schema.get("then") if condition_matches else schema.get("else")
            if branch is not None:
                self._validate(instance, branch, current_path, instance_path, errors, depth + 1)

        if "const" in schema and not _json_equal(instance, schema["const"]):
            errors.append(f"{location}: {instance!r} does not equal required constant {schema['const']!r}")
        if "enum" in schema and not any(_json_equal(instance, item) for item in schema["enum"]):
            errors.append(f"{location}: {instance!r} is not one of the allowed values")

        if "type" in schema:
            declared = schema["type"]
            expected = [declared] if isinstance(declared, str) else declared
            if not any(_matches_type(instance, item) for item in expected):
                errors.append(f"{location}: expected {' or '.join(expected)}")
                return

        if isinstance(instance, dict):
            required = schema.get("required", [])
            for name in required:
                if name not in instance:
                    errors.append(f"{location}: missing required property {name!r}")
            properties = schema.get("properties", {})
            pattern_properties = schema.get("patternProperties", {})
            matched: set[str] = set()
            for name, child in properties.items():
                if name in instance:
                    matched.add(name)
                    self._validate(
                        instance[name], child, current_path, instance_path + (name,), errors, depth + 1
                    )
            for pattern, child in pattern_properties.items():
                expression = re.compile(pattern)
                for name, value in instance.items():
                    if expression.search(name):
                        matched.add(name)
                        self._validate(
                            value, child, current_path, instance_path + (name,), errors, depth + 1
                        )
            additional = schema.get("additionalProperties", True)
            for name in sorted(instance.keys() - matched):
                if additional is False:
                    errors.append(f"{location}: additional property {name!r} is not allowed")
                elif isinstance(additional, dict) or isinstance(additional, bool):
                    if additional is not True:
                        self._validate(
                            instance[name],
                            additional,
                            current_path,
                            instance_path + (name,),
                            errors,
                            depth + 1,
                        )
            if "minProperties" in schema and len(instance) < schema["minProperties"]:
                errors.append(f"{location}: needs at least {schema['minProperties']} properties")
            if "maxProperties" in schema and len(instance) > schema["maxProperties"]:
                errors.append(f"{location}: allows at most {schema['maxProperties']} properties")
            for trigger, dependencies in schema.get("dependentRequired", {}).items():
                if trigger in instance:
                    for dependency in dependencies:
                        if dependency not in instance:
                            errors.append(
                                f"{location}: property {trigger!r} requires property {dependency!r}"
                            )
            for trigger, child in schema.get("dependentSchemas", {}).items():
                if trigger in instance:
                    self._validate(instance, child, current_path, instance_path, errors, depth + 1)

        if isinstance(instance, list):
            if "items" in schema:
                for index, item in enumerate(instance):
                    self._validate(
                        item,
                        schema["items"],
                        current_path,
                        instance_path + (index,),
                        errors,
                        depth + 1,
                    )
            if "minItems" in schema and len(instance) < schema["minItems"]:
                errors.append(f"{location}: needs at least {schema['minItems']} items")
            if "maxItems" in schema and len(instance) > schema["maxItems"]:
                errors.append(f"{location}: allows at most {schema['maxItems']} items")
            if schema.get("uniqueItems"):
                for index, item in enumerate(instance):
                    if any(_json_equal(item, earlier) for earlier in instance[:index]):
                        errors.append(f"{location}: item {index} duplicates an earlier item")
                        break

        if isinstance(instance, str):
            if "minLength" in schema and len(instance) < schema["minLength"]:
                errors.append(f"{location}: must contain at least {schema['minLength']} characters")
            if "maxLength" in schema and len(instance) > schema["maxLength"]:
                errors.append(f"{location}: must contain at most {schema['maxLength']} characters")
            if "pattern" in schema and re.search(schema["pattern"], instance) is None:
                errors.append(f"{location}: does not match required pattern {schema['pattern']!r}")
            if "format" in schema and not _valid_format(instance, schema["format"]):
                errors.append(f"{location}: is not a valid {schema['format']}")

        if _is_json_number(instance):
            if "minimum" in schema and instance < schema["minimum"]:
                errors.append(f"{location}: must be at least {schema['minimum']}")
            if "maximum" in schema and instance > schema["maximum"]:
                errors.append(f"{location}: must be at most {schema['maximum']}")
            if "exclusiveMinimum" in schema and instance <= schema["exclusiveMinimum"]:
                errors.append(f"{location}: must be greater than {schema['exclusiveMinimum']}")
            if "exclusiveMaximum" in schema and instance >= schema["exclusiveMaximum"]:
                errors.append(f"{location}: must be less than {schema['exclusiveMaximum']}")


def schema_validation(instance: Any, schema_name: str) -> dict[str, Any]:
    """Validate offline with Design Council's dependency-free schema subset."""

    schema_path = SCHEMA_ROOT / schema_name
    schema = load_json(schema_path)
    if not isinstance(schema, (dict, bool)):
        raise DesignCouncilError(f"Schema root must be an object or boolean: {schema_path}")
    validator = _StdlibSchemaValidator(schema_path, schema)
    errors = validator.errors(instance)
    return {"valid": not errors, "errors": errors, "validator": "design-council-stdlib-2020-12-subset"}
