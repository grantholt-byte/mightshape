#!/usr/bin/env python3
"""Repository-level MightShape release validator.

This complements, rather than replaces, the official plugin and skill validators.
It checks product invariants that generic package validation cannot know.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

from dc_core import DesignCouncilError, json_output, load_json


COUNCIL_IDS = [
    "maya-chen", "leo-martinez", "priya-rao", "marcus-brooks", "elena-rossi",
    "theo-bennett", "samira-okafor", "jack-sullivan", "mei-tanaka", "rafael-alvarez",
]
EXPECTED_SCRIPTS = {
    "dc.py", "dc_core.py", "project_state.py", "select_methods.py", "cluster_ideas.py", "score_pov.py",
    "score_build_gate.py", "check_evidence.py", "allocate_council.py", "session_summary.py", "create_study.py",
    "create_persona.py", "validate_reality_packet.py", "detect_leading_questions.py", "compare_participants.py",
    "synthesize_inquiry.py", "validate_package.py", "sealed_round.py",
    "participant_sources.py", "disclosure_guard.py",
    "render_visual.py",
}
EXPECTED_SCHEMAS = {
    "project-state.schema.json", "evidence.schema.json", "assumption.schema.json", "insight.schema.json",
    "pov.schema.json", "idea.schema.json", "prototype.schema.json", "experiment.schema.json",
    "council-response.schema.json", "human-model.schema.json", "inquiry-study.schema.json",
    "reality-packet.schema.json", "synthetic-persona.schema.json", "interview-guide.schema.json",
    "participant.schema.json", "transcript.schema.json", "research-finding.schema.json", "reality-check.schema.json",
    "participant-source.schema.json", "internal-study.schema.json", "external-study-packet.schema.json",
    "project-exposure.schema.json", "disclosure-review.schema.json", "conflict-policy.schema.json",
    "experience-signal.schema.json", "participant-profile.schema.json", "participant-verification-status.schema.json",
    "research-session-type.schema.json", "exchange-recruitment-request.schema.json",
    "exchange-credit-ledger.schema.json", "learning-signal.schema.json",
    "ip-exposure-assessment.schema.json", "demand-signal-event.schema.json",
    "visual-artifact.schema.json",
    "participation-session.schema.json",
    "team-channel-binding.schema.json",
    "team-workshop-session.schema.json",
}
EXPECTED_TEMPLATES = {
    "design-brief.md", "research-plan.md", "interview-guide.md", "reality-packet.md", "pov-card.md",
    "hmw-card.md", "prototype-card.md", "experiment-card.md", "decision-record.md",
}
SOURCE_FAMILIES = {"public_design_practice", "supplemental_design_practice", "mightshape_original"}
SEMVER_RE = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?"
    r"(?:\+([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?$"
)


def _is_semver(value: object) -> bool:
    match = SEMVER_RE.fullmatch(str(value))
    if not match:
        return False
    prerelease = match.group(4)
    if prerelease:
        for identifier in prerelease.split("."):
            if identifier.isdigit() and len(identifier) > 1 and identifier.startswith("0"):
                return False
    return True


def _check(condition: bool, code: str, message: str, errors: list[dict[str, str]]) -> None:
    if not condition:
        errors.append({"code": code, "message": message})


def validate_package(root: str | Path) -> dict[str, Any]:
    root = Path(root).resolve()
    errors: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []
    checks: list[dict[str, Any]] = []

    def report(name: str, before: int, details: Any = None) -> None:
        checks.append({"name": name, "passes": len(errors) == before, "details": details})

    before = len(errors)
    for relative in (".codex-plugin/plugin.json", "README.md", "LICENSE", "AGENTS.md", "skills/mightshape/SKILL.md"):
        _check((root / relative).is_file(), "MISSING_FILE", relative, errors)
    report("required repository files", before)

    before = len(errors)
    manifest_path = root / ".codex-plugin" / "plugin.json"
    if manifest_path.exists():
        try:
            manifest = load_json(manifest_path)
            _check(manifest.get("name") == "mightshape", "MANIFEST_NAME", "plugin name must be mightshape", errors)
            _check(
                _is_semver(manifest.get("version", "")),
                "MANIFEST_VERSION",
                "plugin version must be valid SemVer (for example 1.0.0 or 0.9.0-beta.1)",
                errors,
            )
            skill_path = root / str(manifest.get("skills", "")).lstrip("./")
            _check(skill_path.is_dir(), "MANIFEST_SKILLS", "manifest skills path does not exist", errors)
            interface = manifest.get("interface", {})
            for key in ("composerIcon", "logo"):
                value = interface.get(key)
                _check(bool(value) and (root / str(value).lstrip("./")).is_file(), "MANIFEST_ASSET", f"interface.{key} target is missing", errors)
            _check(interface.get("brandColor") == "#6457FF", "BRAND_COLOR", "expected MightShape brand color #6457FF", errors)
        except DesignCouncilError as exc:
            errors.append({"code": "MANIFEST_JSON", "message": str(exc)})
    report("plugin manifest", before)

    skill_root = root / "skills" / "mightshape"
    before = len(errors)
    skill_path = skill_root / "SKILL.md"
    if skill_path.exists():
        skill = skill_path.read_text(encoding="utf-8")
        _check(skill.startswith("---\n"), "SKILL_FRONTMATTER", "SKILL.md needs YAML frontmatter", errors)
        _check("name: design-think" in skill, "SKILL_NAME", "primary skill name must be design-think", errors)
        _check("description:" in skill.split("---", 2)[1], "SKILL_DESCRIPTION", "skill description is missing", errors)
        _check(len(skill.splitlines()) <= 500, "SKILL_TOO_LONG", "SKILL.md exceeds 500 lines; preserve progressive disclosure", errors)
        linked = re.findall(r"\]\((references/[^)#]+)\)", skill)
        for relative in linked:
            _check((skill_root / relative).is_file(), "BROKEN_SKILL_LINK", relative, errors)
        for invariant in ("sealed", "SOLUTION BLACKOUT", "Build Gate", "evidence firewall", "Minority Report"):
            _check(invariant.lower() in skill.lower(), "SKILL_INVARIANT", f"SKILL.md does not route {invariant}", errors)
    report("skill metadata and progressive disclosure", before)

    before = len(errors)
    schema_root = skill_root / "schemas"
    found_schemas = {path.name for path in schema_root.glob("*.json")}
    for missing in sorted(EXPECTED_SCHEMAS - found_schemas):
        errors.append({"code": "MISSING_SCHEMA", "message": missing})
    for path in sorted(schema_root.glob("*.json")):
        try:
            schema = load_json(path)
            try:
                import jsonschema  # type: ignore
                jsonschema.validators.validator_for(schema).check_schema(schema)
            except ImportError:
                if schema.get("type") != "object":
                    warnings.append({"code": "SCHEMA_BASIC_ONLY", "message": f"jsonschema unavailable; minimally checked {path.name}"})
        except Exception as exc:
            errors.append({"code": "INVALID_SCHEMA", "message": f"{path.name}: {exc}"})
    report("JSON Schemas", before, {"count": len(found_schemas)})

    before = len(errors)
    script_root = skill_root / "scripts"
    found_scripts = {path.name for path in script_root.glob("*.py")}
    for missing in sorted(EXPECTED_SCRIPTS - found_scripts):
        errors.append({"code": "MISSING_SCRIPT", "message": missing})
    for path in sorted(script_root.glob("*.py")):
        try:
            compile(path.read_text(encoding="utf-8"), str(path), "exec")
        except SyntaxError as exc:
            errors.append({"code": "PYTHON_SYNTAX", "message": f"{path.name}:{exc.lineno}: {exc.msg}"})
    report("deterministic scripts", before, {"count": len(found_scripts)})

    before = len(errors)
    reference_root = skill_root / "references"
    _check(
        (reference_root / "participatory-workshops.md").is_file(),
        "MISSING_REFERENCE",
        "participatory-workshops.md",
        errors,
    )
    for member_id in COUNCIL_IDS:
        path = reference_root / f"council-{member_id}.md"
        _check(path.is_file(), "MISSING_PROFILE", member_id, errors)
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        normalized_text = text.lower().replace("-", " ")
        word_count = len(re.findall(r"\b[\w'-]+\b", text))
        _check(word_count >= 900, "SHALLOW_PROFILE", f"{member_id} has only {word_count} words", errors)
        for concept in ("Present life", "Professional reality", "Worldview", "Communication", "Contradiction", "Knowledge bound", "project memory"):
            _check(concept.lower() in normalized_text, "PROFILE_SECTION", f"{member_id} lacks {concept}", errors)
        _check("I don't know" in text or "I don’t know" in text, "KNOWLEDGE_BOUNDARY", f"{member_id} lacks an explicit 'I don't know' behavior", errors)
    report("ten deep Human Models", before, {"count": len(list(reference_root.glob("council-*.md"))) - 2})

    before = len(errors)
    registry_path = reference_root / "method-registry.json"
    if registry_path.exists():
        try:
            registry = load_json(registry_path)
            methods = registry.get("methods", [])
            ids = [item.get("id") for item in methods]
            _check(len(methods) >= 60, "METHOD_COVERAGE", f"registry contains only {len(methods)} methods", errors)
            _check(len(ids) == len(set(ids)), "METHOD_IDS", "method IDs must be unique", errors)
            families = {item.get("source_family") for item in methods}
            _check(families <= SOURCE_FAMILIES, "SOURCE_FAMILY", f"unknown source families: {sorted(families - SOURCE_FAMILIES)}", errors)
            _check(SOURCE_FAMILIES <= families, "SOURCE_FAMILY_COVERAGE", "all three source families must be represented", errors)
            for item in methods:
                for field in ("id", "name", "modes", "purpose", "use_when", "avoid_when", "requires", "outputs", "council", "effort", "source_family"):
                    _check(field in item, "METHOD_FIELD", f"{item.get('id', '?')} missing {field}", errors)
        except DesignCouncilError as exc:
            errors.append({"code": "METHOD_REGISTRY_JSON", "message": str(exc)})
    else:
        errors.append({"code": "MISSING_METHOD_REGISTRY", "message": str(registry_path)})
    report("method registry and attribution", before)

    before = len(errors)
    template_root = skill_root / "assets" / "templates"
    found_templates = {path.name for path in template_root.glob("*.md")} if template_root.exists() else set()
    for missing in sorted(EXPECTED_TEMPLATES - found_templates):
        errors.append({"code": "MISSING_TEMPLATE", "message": missing})
    report("facilitation templates", before, {"count": len(found_templates)})

    before = len(errors)
    app = root / "interview-app"
    for relative in ("package.json", ".openai/hosting.json", "README.md"):
        _check((app / relative).is_file(), "INTERVIEW_APP", f"optional hosted companion missing {relative}", errors)
    if (app / "package.json").exists():
        try:
            package = load_json(app / "package.json")
            _check(bool(package.get("scripts", {}).get("test")), "INTERVIEW_TEST", "interview app has no test script", errors)
            _check(bool(package.get("scripts", {}).get("build")), "INTERVIEW_BUILD", "interview app has no build script", errors)
        except DesignCouncilError as exc:
            errors.append({"code": "INTERVIEW_PACKAGE_JSON", "message": str(exc)})
    report("optional hosted interview companion", before)

    before = len(errors)
    _check((root / "evals" / "cases").is_dir(), "EVALS", "behavioral eval cases directory is missing", errors)
    _check((root / "tests").is_dir(), "TESTS", "unit tests directory is missing", errors)
    report("test and eval harness", before)

    return {
        "valid": not errors,
        "package_root": str(root),
        "checks": checks,
        "errors": errors,
        "warnings": warnings,
        "summary": {"checks": len(checks), "passed": sum(item["passes"] for item in checks), "failed": sum(not item["passes"] for item in checks), "errors": len(errors), "warnings": len(warnings)},
        "note": (
            "Also run Codex's bundled plugin/skill authoring validators and the current "
            "OpenAI submission-portal validator before release."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate the complete MightShape package")
    parser.add_argument("root", nargs="?", default=".")
    args = parser.parse_args()
    try:
        result = validate_package(args.root)
        json_output(result)
        return 0 if result["valid"] else 1
    except DesignCouncilError as exc:
        print(f"MightShape error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
