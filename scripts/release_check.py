#!/usr/bin/env python3
"""One-command, side-effect-local release check for both platform packages."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
BRAND = json.loads((ROOT / "brand.json").read_text(encoding="utf-8"))
PRODUCT_SLUG = BRAND["product"]["slug"]


def run(name: str, command: list[str], cwd: Path = ROOT) -> dict[str, Any]:
    completed = subprocess.run(command, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)
    return {"name": name, "command": command, "returncode": completed.returncode, "output": completed.stdout.strip()}


def secret_scan() -> dict[str, Any]:
    patterns = {
        "OpenAI key": re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
        "Anthropic key": re.compile(r"sk-ant-[A-Za-z0-9_-]{20,}"),
        "GitHub token": re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}"),
        "Private key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    }
    # Generated distributions are rebuilt from the scanned canonical sources,
    # and this workspace may contain user-owned numbered conflict copies. Skip
    # both so the release gate remains bounded and never treats stale backups as
    # publication inputs.
    ignored = {".git", "node_modules", ".next", ".wrangler", "results", "dist"}
    duplicate_copy = re.compile(r" \d+(?:$|(?=\.))")
    findings = []
    for path in ROOT.rglob("*"):
        if (
            not path.is_file()
            or any(part in ignored for part in path.parts)
            or any(duplicate_copy.search(part) for part in path.parts)
        ):
            continue
        if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".zip", ".woff", ".woff2"}:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for name, pattern in patterns.items():
            if pattern.search(text):
                findings.append({"type": name, "path": str(path.relative_to(ROOT))})
    return {"name": "credential pattern scan", "returncode": 1 if findings else 0, "findings": findings, "output": f"{len(findings)} credential-like pattern(s)"}


def main() -> int:
    python = sys.executable
    checks = [
        run("build packages", [python, "scripts/build_packages.py", "--clean"]),
        run("runtime third-party branding boundary", [python, "scripts/check_runtime_branding.py"]),
        run("cross-platform drift", [python, "scripts/check_cross_platform_drift.py"]),
        run("package validators", [python, "scripts/validate_packages.py", "--require-claude"]),
        run("current product identity", [python, "scripts/check_brand_identity.py"]),
        run("repository package contract", [python, f"skills/{PRODUCT_SLUG}/scripts/validate_package.py", "."]),
        run("unit tests", [python, "-m", "unittest", "discover", "-s", "tests", "-v"]),
        run("behavioral contracts", [python, "evals/run_contracts.py"]),
        run("platform eval contracts", [python, "evals/run_platform_contracts.py"]),
        run("interview app full tests", ["npm", "run", "test:full"], ROOT / "interview-app"),
        run("interview app lint", ["npm", "run", "lint"], ROOT / "interview-app"),
        run("interview app typecheck", ["npm", "run", "typecheck"], ROOT / "interview-app"),
        run("interview app production build", ["npm", "run", "build"], ROOT / "interview-app"),
        run("interview app production dependency audit", ["npm", "audit", "--omit=dev"], ROOT / "interview-app"),
        run("collaboration service typecheck", ["npm", "run", "typecheck"], ROOT / "collaboration-app"),
        run("collaboration service tests", ["npm", "test"], ROOT / "collaboration-app"),
        run("collaboration service production dependency audit", ["npm", "audit", "--omit=dev"], ROOT / "collaboration-app"),
        secret_scan(),
    ]
    failures = [item for item in checks if item["returncode"] != 0]
    result = {
        "valid": not failures,
        "version": (ROOT / "VERSION").read_text(encoding="utf-8").strip(),
        "checks": [{"name": item["name"], "passed": item["returncode"] == 0, "output": item.get("output", "")[-2000:]} for item in checks],
        "failures": [item["name"] for item in failures],
        "note": "Model-backed acceptance evals, official clean-context marketplace installs, and live Slack/Discord/Teams workspace installs are recorded separately because they require authenticated platform runtimes.",
    }
    print(json.dumps(result, indent=2))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
