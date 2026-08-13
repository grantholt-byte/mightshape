#!/usr/bin/env python3
"""Validate generated distributions with bundled authoring and platform tooling."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import struct
import sys
import zipfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OPENAI = ROOT / "dist/openai/design-council"
CLAUDE = ROOT / "dist/claude/design-council"
OPENAI_VALIDATOR = Path.home() / ".codex/skills/.system/plugin-creator/scripts/validate_plugin.py"
SKILL_VALIDATOR = Path.home() / ".codex/skills/.system/skill-creator/scripts/quick_validate.py"
PLATFORMS = ("openai", "claude")
SEMVER_RE = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?"
    r"(?:\+([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?$"
)
PLUGIN_NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def skill_name(path: Path) -> str | None:
    """Read the simple ``name`` field from a skill's YAML frontmatter."""

    match = re.search(r"(?m)^name:\s*([^\n#]+)", path.read_text(encoding="utf-8"))
    return match.group(1).strip().strip('"\'') if match else None


def is_semver(value: object) -> bool:
    """Return whether value is a SemVer 2.0.0 release or prerelease string."""
    match = SEMVER_RE.fullmatch(str(value))
    if not match:
        return False
    prerelease = match.group(4)
    if prerelease:
        for identifier in prerelease.split("."):
            if identifier.isdigit() and len(identifier) > 1 and identifier.startswith("0"):
                return False
    return True


def run(command: list[str], cwd: Path = ROOT) -> dict[str, Any]:
    completed = subprocess.run(command, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)
    return {"command": command, "returncode": completed.returncode, "output": completed.stdout.strip()}


def png_dimensions(path: Path) -> tuple[int, int] | None:
    """Return PNG dimensions without adding an image-library dependency."""

    try:
        header = path.read_bytes()[:24]
    except OSError:
        return None
    if len(header) != 24 or header[:8] != b"\x89PNG\r\n\x1a\n" or header[12:16] != b"IHDR":
        return None
    return struct.unpack(">II", header[16:24])


def validate_square_portal_asset(root: Path, value: object, label: str) -> list[str]:
    """Apply the current public-directory size rules to a manifest image."""

    if not isinstance(value, str) or not value.startswith("./"):
        return [f"OpenAI {label} must be a plugin-relative path beginning with ./"]
    asset = root / value[2:]
    if asset.suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp"}:
        return [f"OpenAI {label} uses an unsupported directory image format: {value}"]
    try:
        asset_size = asset.stat().st_size
    except OSError:
        return [f"OpenAI {label} does not exist: {value}"]
    if asset_size > 5 * 1024 * 1024:
        return [f"OpenAI {label} exceeds the 5 MiB portal limit: {value}"]
    dimensions = png_dimensions(asset)
    if dimensions is None:
        return [f"OpenAI {label} must resolve to a readable PNG: {value}"]
    width, height = dimensions
    if width != height or not 48 <= width <= 4096:
        return [
            f"OpenAI {label} must be square and 48–4096 px; "
            f"{value} is {width}x{height}"
        ]
    return []


def _channel(value: int) -> float:
    normalized = value / 255
    return normalized / 12.92 if normalized <= 0.04045 else ((normalized + 0.055) / 1.055) ** 2.4


def contrast_against_white(value: object) -> float | None:
    """Return WCAG-style contrast against white for a six-digit hex color."""

    if not isinstance(value, str) or re.fullmatch(r"#[0-9A-Fa-f]{6}", value) is None:
        return None
    red, green, blue = (int(value[index : index + 2], 16) for index in (1, 3, 5))
    luminance = 0.2126 * _channel(red) + 0.7152 * _channel(green) + 0.0722 * _channel(blue)
    return 1.05 / (luminance + 0.05)


def validate_openai_archive() -> list[str]:
    """Check current portal archive limits that local tooling can enforce."""

    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    archive_path = ROOT / f"dist/design-council-openai-{version}.zip"
    if not archive_path.is_file():
        return [f"OpenAI release archive is missing: {archive_path.name}"]
    if archive_path.stat().st_size > 100 * 1024 * 1024:
        return ["OpenAI release archive exceeds 100 MiB compressed"]
    errors: list[str] = []
    with zipfile.ZipFile(archive_path) as archive:
        entries = archive.infolist()
        if len(entries) > 5000:
            errors.append("OpenAI release archive exceeds 5,000 entries")
        if sum(item.file_size for item in entries) > 512 * 1024 * 1024:
            errors.append("OpenAI release archive exceeds 512 MiB extracted")
        roots: set[str] = set()
        for item in entries:
            parts = Path(item.filename).parts
            if not parts or any(part in {"", ".", ".."} for part in parts):
                errors.append(f"OpenAI archive contains an unsafe path: {item.filename}")
                continue
            roots.add(parts[0])
            if len(parts) > 20:
                errors.append(f"OpenAI archive path exceeds 20 segments: {item.filename}")
        if roots != {"design-council"}:
            errors.append(f"OpenAI archive must contain exactly one plugin root; found {sorted(roots)}")
    return errors


def basic_openai_validate() -> list[str]:
    errors: list[str] = []
    manifest_path = OPENAI / ".codex-plugin/plugin.json"
    marketplace_path = ROOT / ".agents/plugins/marketplace.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        marketplace = json.loads(marketplace_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"OpenAI JSON load failed: {exc}"]
    if manifest.get("name") != "design-council":
        errors.append("OpenAI plugin name must be design-council")
    if not isinstance(manifest.get("name"), str) or len(manifest["name"]) > 64 or not PLUGIN_NAME_RE.fullmatch(manifest["name"]):
        errors.append("OpenAI plugin name must be <=64 lowercase ASCII letters/digits/hyphens")
    if not is_semver(manifest.get("version", "")):
        errors.append("OpenAI plugin version must be valid SemVer (for example 1.0.0 or 0.9.0-beta.1)")
    if len(str(manifest.get("version", ""))) > 64:
        errors.append("OpenAI plugin version must be <=64 characters")
    if not (OPENAI / "skills/design-council/SKILL.md").is_file():
        errors.append("OpenAI skill is missing")
    elif skill_name(OPENAI / "skills/design-council/SKILL.md") != "design-think":
        errors.append("OpenAI primary skill must expose the design-think invocation")
    if not (OPENAI / "skills/design-council-legacy/SKILL.md").is_file():
        errors.append("OpenAI legacy invocation alias is missing")
    elif skill_name(OPENAI / "skills/design-council-legacy/SKILL.md") != "design-council":
        errors.append("OpenAI legacy alias must preserve the design-council invocation")
    if marketplace.get("name") != "design-council":
        errors.append("OpenAI marketplace name must be design-council")
    plugins = marketplace.get("plugins", [])
    if len(plugins) != 1 or plugins[0].get("name") != "design-council":
        errors.append("OpenAI marketplace must expose exactly Design Council")
    interface = manifest.get("interface", {})
    if not isinstance(interface, dict):
        errors.append("OpenAI interface metadata must be an object")
        return errors
    text_limits = {
        "displayName": 30,
        "shortDescription": 30,
        "longDescription": 4000,
    }
    for field, limit in text_limits.items():
        value = interface.get(field)
        if not isinstance(value, str) or not value.strip() or len(value) > limit:
            errors.append(f"OpenAI interface.{field} must contain 1–{limit} characters")
    developer = interface.get("developerName")
    if not isinstance(developer, str) or not developer.strip() or len(developer) > 80:
        errors.append("OpenAI interface.developerName must contain 1–80 characters")
    if not isinstance(interface.get("category"), str) or not interface["category"].strip():
        errors.append("OpenAI interface.category is required")
    capabilities = interface.get("capabilities")
    if not isinstance(capabilities, list) or not 1 <= len(capabilities) <= 20:
        errors.append("OpenAI interface.capabilities must contain 1–20 items")
    elif any(not isinstance(item, str) or not item.strip() or len(item) > 120 for item in capabilities):
        errors.append("Every OpenAI capability must contain 1–120 characters")
    prompts = interface.get("defaultPrompt")
    if not isinstance(prompts, list) or not 1 <= len(prompts) <= 3:
        errors.append("OpenAI interface.defaultPrompt must contain 1–3 prompts")
    elif any(not isinstance(prompt, str) or not prompt.strip() or len(prompt) > 128 for prompt in prompts):
        errors.append("Every OpenAI default prompt must contain 1–128 characters")
    elif len(set(prompts)) != len(prompts):
        errors.append("OpenAI default prompts must be unique")
    for field in ("composerIcon", "logo"):
        errors.extend(validate_square_portal_asset(OPENAI, interface.get(field), f"interface.{field}"))
    contrast = contrast_against_white(interface.get("brandColor"))
    if contrast is None or contrast < 2:
        errors.append("OpenAI interface.brandColor must be #RRGGBB with at least 2:1 contrast on white")
    for forbidden in ("mcpServers", "apps"):
        if forbidden in manifest:
            errors.append(f"OpenAI skills-only package must not declare {forbidden}")
    if "screenshots" in interface:
        errors.append("OpenAI skills-only package without custom UI must not declare screenshots")
    skill_metadata = OPENAI / "skills/design-council/agents/openai.yaml"
    if skill_metadata.is_file():
        metadata_text = skill_metadata.read_text(encoding="utf-8")
        icon_match = re.search(r'(?m)^\s*icon_large:\s*["\']?([^"\'\n]+)', metadata_text)
        if icon_match:
            skill_asset = OPENAI / "skills/design-council" / icon_match.group(1).strip()
            dimensions = png_dimensions(skill_asset.resolve())
            if dimensions is None or dimensions[0] != dimensions[1] or not 48 <= dimensions[0] <= 4096:
                errors.append("OpenAI skill icon_large must resolve to a square 48–4096 px PNG")
    errors.extend(validate_openai_archive())
    return errors


def basic_claude_validate() -> list[str]:
    errors: list[str] = []
    manifest_path = CLAUDE / ".claude-plugin/plugin.json"
    marketplace_path = ROOT / ".claude-plugin/marketplace.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        marketplace = json.loads(marketplace_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"Claude JSON load failed: {exc}"]
    if manifest.get("name") != "design-council":
        errors.append("Claude plugin name must be design-council")
    if not is_semver(manifest.get("version", "")):
        errors.append("Claude plugin version must be valid SemVer (for example 1.0.0 or 0.9.0-beta.1)")
    if not (CLAUDE / "skills/design-council/SKILL.md").is_file():
        errors.append("Claude skill is missing")
    elif skill_name(CLAUDE / "skills/design-council/SKILL.md") != "design-think":
        errors.append(
            "Claude primary skill must expose design-think as the namespaced "
            "/design-council:design-think command"
        )
    if not (CLAUDE / "skills/design-council-legacy/SKILL.md").is_file():
        errors.append("Claude legacy invocation alias is missing")
    elif skill_name(CLAUDE / "skills/design-council-legacy/SKILL.md") != "design-council":
        errors.append("Claude legacy alias must preserve the design-council command")
    if not (CLAUDE / "agents/sealed-member.md").is_file():
        errors.append("Claude sealed-member agent is missing")
    plugins = marketplace.get("plugins", [])
    if len(plugins) != 1 or plugins[0].get("name") != "design-council":
        errors.append("Claude marketplace must expose exactly Design Council")
    if plugins and plugins[0].get("source") != "./dist/claude/design-council":
        errors.append("Claude marketplace source must stay inside the repository root")
    return errors


def validate(require_claude: bool = False, platform: str = "all") -> dict[str, Any]:
    results: list[dict[str, Any]] = []
    errors: list[str] = []
    warnings: list[str] = []
    selected = PLATFORMS if platform == "all" else (platform,)
    missing = [name for name in selected if not (OPENAI if name == "openai" else CLAUDE).exists()]
    if missing:
        errors.append(
            "generated packages are missing for "
            + ", ".join(missing)
            + "; run scripts/build_packages.py --platform <platform>"
        )
        return {"valid": False, "results": results, "errors": errors, "warnings": warnings}

    if "openai" in selected:
        errors.extend(basic_openai_validate())
        if OPENAI_VALIDATOR.is_file():
            results.append(run([sys.executable, str(OPENAI_VALIDATOR), str(OPENAI)]))
        else:
            errors.append(f"bundled OpenAI authoring validator unavailable: {OPENAI_VALIDATOR}")
        if SKILL_VALIDATOR.is_file():
            results.append(run([sys.executable, str(SKILL_VALIDATOR), str(OPENAI / "skills/design-council")]))
            results.append(run([sys.executable, str(SKILL_VALIDATOR), str(OPENAI / "skills/design-council-legacy")]))
        else:
            errors.append(f"skill validator unavailable: {SKILL_VALIDATOR}")

    if "claude" in selected:
        errors.extend(basic_claude_validate())
        if SKILL_VALIDATOR.is_file():
            results.append(run([sys.executable, str(SKILL_VALIDATOR), str(CLAUDE / "skills/design-council")]))
            results.append(run([sys.executable, str(SKILL_VALIDATOR), str(CLAUDE / "skills/design-council-legacy")]))
        else:
            errors.append(f"skill validator unavailable: {SKILL_VALIDATOR}")
        configured_claude = os.environ.get("DC_CLAUDE_CLI")
        claude = configured_claude or shutil.which("claude")
        if claude:
            claude_command = [claude]
        elif require_claude and shutil.which("npx"):
            claude_command = [shutil.which("npx") or "npx", "--yes", "@anthropic-ai/claude-code@latest"]
        else:
            claude_command = []
        if claude_command:
            results.append(run(claude_command + ["plugin", "validate", str(CLAUDE), "--strict"]))
            results.append(run(claude_command + ["plugin", "validate", str(ROOT), "--strict"]))
        elif require_claude:
            errors.append("official Claude CLI is required but neither `claude` nor `npx` is available")
        else:
            warnings.append(
                "Claude CLI unavailable; run `claude plugin validate "
                "dist/claude/design-council --strict` before publication"
            )

    for item in results:
        if item["returncode"] != 0:
            errors.append(f"command failed ({item['returncode']}): {' '.join(item['command'])}\n{item['output']}")
    return {
        "valid": not errors,
        "platforms": list(selected),
        "results": results,
        "errors": errors,
        "warnings": warnings,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--require-claude", action="store_true")
    parser.add_argument("--platform", choices=("all",) + PLATFORMS, default="all")
    args = parser.parse_args()
    result = validate(args.require_claude, args.platform)
    print(json.dumps(result, indent=2))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
