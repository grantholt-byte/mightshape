#!/usr/bin/env python3
"""Validate both generated distributions with local and official tooling."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OPENAI = ROOT / "dist/openai/design-council"
CLAUDE = ROOT / "dist/claude/design-council"
OPENAI_VALIDATOR = Path.home() / ".codex/skills/.system/plugin-creator/scripts/validate_plugin.py"
SKILL_VALIDATOR = Path.home() / ".codex/skills/.system/skill-creator/scripts/quick_validate.py"
PLATFORMS = ("openai", "claude")


def run(command: list[str], cwd: Path = ROOT) -> dict[str, Any]:
    completed = subprocess.run(command, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)
    return {"command": command, "returncode": completed.returncode, "output": completed.stdout.strip()}


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
    if not str(manifest.get("version", "")).count(".") == 2:
        errors.append("OpenAI plugin version must be semantic x.y.z")
    if not (OPENAI / "skills/design-council/SKILL.md").is_file():
        errors.append("OpenAI skill is missing")
    if marketplace.get("name") != "design-council":
        errors.append("OpenAI marketplace name must be design-council")
    plugins = marketplace.get("plugins", [])
    if len(plugins) != 1 or plugins[0].get("name") != "design-council":
        errors.append("OpenAI marketplace must expose exactly Design Council")
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
    if not str(manifest.get("version", "")).count(".") == 2:
        errors.append("Claude plugin version must be semantic x.y.z")
    if not (CLAUDE / "skills/design-council/SKILL.md").is_file():
        errors.append("Claude skill is missing")
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
            errors.append(f"official OpenAI validator unavailable: {OPENAI_VALIDATOR}")
        if SKILL_VALIDATOR.is_file():
            results.append(run([sys.executable, str(SKILL_VALIDATOR), str(OPENAI / "skills/design-council")]))
        else:
            errors.append(f"skill validator unavailable: {SKILL_VALIDATOR}")

    if "claude" in selected:
        errors.extend(basic_claude_validate())
        if SKILL_VALIDATOR.is_file():
            results.append(run([sys.executable, str(SKILL_VALIDATOR), str(CLAUDE / "skills/design-council")]))
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
