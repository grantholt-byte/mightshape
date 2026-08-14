#!/usr/bin/env python3
"""Controlled Claude Code candidate runtime for MightShape A/B studies."""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import time
from typing import Any, Mapping, Sequence


AUTH_KEYS = ("ANTHROPIC_API_KEY", "CLAUDE_CODE_OAUTH_TOKEN")
BASE_ENV_KEYS = {
    "HOME",
    "PATH",
    "SHELL",
    "TMPDIR",
    "LANG",
    "LC_ALL",
    "SSL_CERT_FILE",
    "SSL_CERT_DIR",
    "HTTP_PROXY",
    "HTTPS_PROXY",
    "ALL_PROXY",
    "NO_PROXY",
    "http_proxy",
    "https_proxy",
    "all_proxy",
    "no_proxy",
}


class ClaudeRuntimeError(RuntimeError):
    """Raised when a Claude candidate cell is invalid or incomparable."""


def explicit_auth_key(source: Mapping[str, str]) -> str | None:
    """Return the one explicitly supplied Claude credential name, never its value."""

    present = [name for name in AUTH_KEYS if source.get(name)]
    if len(present) > 1:
        raise ClaudeRuntimeError(
            "supply exactly one of ANTHROPIC_API_KEY or CLAUDE_CODE_OAUTH_TOKEN"
        )
    return present[0] if present else None


def isolated_claude_environment(
    source: Mapping[str, str],
    config_dir: Path,
) -> dict[str, str]:
    """Build a minimal environment with one explicit auth credential."""

    credential = explicit_auth_key(source)
    environment = {
        key: value for key, value in source.items() if key in BASE_ENV_KEYS and value
    }
    if credential:
        environment[credential] = source[credential]
    environment.update(
        {
            "CLAUDE_CONFIG_DIR": str(config_dir),
            "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1",
            "CLAUDE_CODE_DISABLE_OFFICIAL_MARKETPLACE_AUTOINSTALL": "1",
            "DISABLE_TELEMETRY": "1",
            "NO_COLOR": "1",
        }
    )
    return environment


def build_claude_command(
    *,
    binary: str,
    prompt: str,
    model: str,
    effort: str,
    max_turns: int,
    max_budget_usd: float,
    plugin_dir: Path | None = None,
) -> list[str]:
    """Return a deterministic headless command; plugin_dir is the sole arm delta."""

    if max_turns < 1 or max_budget_usd <= 0:
        raise ClaudeRuntimeError("max_turns and max_budget_usd must be positive")
    command = [
        binary,
        "-p",
        prompt,
        "--output-format",
        "stream-json",
        "--verbose",
        "--no-session-persistence",
        "--setting-sources",
        "local",
        "--permission-mode",
        "dontAsk",
        "--tools",
        "Read,Skill,Task",
        "--allowedTools",
        "Read,Skill,Task",
        "--model",
        model,
        "--effort",
        effort,
        "--max-turns",
        str(max_turns),
        "--max-budget-usd",
        str(max_budget_usd),
    ]
    if plugin_dir is not None:
        command.extend(["--plugin-dir", str(plugin_dir)])
    return command


def parse_claude_stream(stdout: str) -> dict[str, Any]:
    """Parse stream-json without double-counting cache or thinking tokens."""

    events: list[dict[str, Any]] = []
    warnings: list[str] = []
    for line_number, raw in enumerate(stdout.splitlines(), 1):
        if not raw.strip():
            continue
        try:
            value = json.loads(raw)
        except json.JSONDecodeError:
            warnings.append(f"line {line_number}: invalid JSON")
            continue
        if isinstance(value, dict):
            events.append(value)
        else:
            warnings.append(f"line {line_number}: event is not an object")
    init_events = [event for event in events if event.get("type") == "system" and event.get("subtype") == "init"]
    result_events = [event for event in events if event.get("type") == "result"]
    init = init_events[-1] if init_events else None
    result = result_events[-1] if result_events else None
    if len(init_events) != 1:
        warnings.append(f"expected one init event; observed {len(init_events)}")
    if len(result_events) != 1:
        warnings.append(f"expected one result event; observed {len(result_events)}")
    usage_source = result.get("usage") if isinstance(result, dict) else None
    usage_source = usage_source if isinstance(usage_source, dict) else {}
    input_tokens = int(usage_source.get("input_tokens", 0) or 0)
    cache_creation = int(usage_source.get("cache_creation_input_tokens", 0) or 0)
    cache_read = int(usage_source.get("cache_read_input_tokens", 0) or 0)
    output_tokens = int(usage_source.get("output_tokens", 0) or 0)
    normalized_input = input_tokens + cache_creation + cache_read
    usage = {
        "input_tokens": normalized_input,
        "cached_input_tokens": cache_read,
        "uncached_input_tokens": input_tokens + cache_creation,
        "cache_creation_input_tokens": cache_creation,
        "cache_read_input_tokens": cache_read,
        "output_tokens": output_tokens,
        "reasoning_output_tokens": 0,
        "total_tokens": normalized_input + output_tokens,
    }
    response = str(result.get("result", "")) if isinstance(result, dict) else ""
    status = "OK"
    if not isinstance(result, dict) or result.get("is_error") is True or not response.strip():
        status = "ERROR"
    tool_calls = 0
    assistant_messages = 0
    for event in events:
        if event.get("type") != "assistant":
            continue
        assistant_messages += 1
        message = event.get("message")
        contents = message.get("content") if isinstance(message, dict) else None
        if isinstance(contents, list):
            tool_calls += sum(
                isinstance(item, dict) and item.get("type") == "tool_use"
                for item in contents
            )
    return {
        "status": status,
        "response": response,
        "usage": usage,
        "init": init,
        "result": result,
        "events": events,
        "warnings": warnings,
        "activity": {
            "tool_calls": tool_calls,
            "command_executions": 0,
            "agent_messages": assistant_messages,
        },
    }


def _names(value: Any) -> set[str]:
    if not isinstance(value, list):
        return set()
    names: set[str] = set()
    for item in value:
        if isinstance(item, dict):
            candidate = item.get("name") or item.get("id") or item.get("path")
            names.add(str(candidate) if candidate is not None else json.dumps(item, sort_keys=True))
        else:
            names.add(str(item))
    return names


def validate_arm_init(control: dict[str, Any], treatment: dict[str, Any]) -> list[str]:
    """Return fairness errors; only MightShape may differ between init surfaces."""

    errors: list[str] = []
    if not control or not treatment:
        return ["both arms require a Claude init event"]
    for field in ("model", "tools"):
        if control.get(field) != treatment.get(field):
            errors.append(f"{field} differs between arms")
    control_plugins = _names(control.get("plugins"))
    treatment_plugins = _names(treatment.get("plugins"))
    if control_plugins:
        errors.append("control unexpectedly loaded a plugin")
    if not any("mightshape" in name for name in treatment_plugins):
        errors.append("treatment did not load MightShape")
    if any("mightshape" not in name for name in treatment_plugins - control_plugins):
        errors.append("treatment loaded an unexpected plugin")
    control_skills = _names(control.get("skills"))
    treatment_skills = _names(treatment.get("skills"))
    added_skills = treatment_skills - control_skills
    removed_skills = control_skills - treatment_skills
    if removed_skills or any("mightshape" not in name for name in added_skills):
        errors.append("bundled skill surfaces differ beyond MightShape")
    control_agents = _names(control.get("agents"))
    treatment_agents = _names(treatment.get("agents"))
    added_agents = treatment_agents - control_agents
    removed_agents = control_agents - treatment_agents
    if removed_agents or any("sealed-member" not in name for name in added_agents):
        errors.append("agent surfaces differ beyond the sealed member")
    plugin_errors = treatment.get("plugin_errors") or treatment.get("pluginErrors")
    if plugin_errors:
        errors.append("treatment reported plugin load errors")
    return errors


def run_claude_stream(
    *,
    command: Sequence[str],
    cwd: Path,
    environment: Mapping[str, str],
    timeout_seconds: int,
) -> dict[str, Any]:
    """Execute one controlled Claude cell and return runner-compatible fields."""

    started = time.perf_counter()
    try:
        completed = subprocess.run(
            list(command),
            cwd=cwd,
            env=dict(environment),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout_seconds,
            check=False,
        )
        timed_out = False
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout if isinstance(exc.stdout, str) else ""
        stderr = exc.stderr if isinstance(exc.stderr, str) else ""
        completed = None
        timed_out = True
    elapsed = time.perf_counter() - started
    if completed is not None:
        stdout = completed.stdout
        stderr = completed.stderr
        returncode = completed.returncode
    else:
        returncode = 124
    parsed = parse_claude_stream(stdout)
    if timed_out or returncode != 0:
        parsed["status"] = "ERROR"
    parsed.update(
        {
            "returncode": returncode,
            "timed_out": timed_out,
            "wall_time_seconds": round(elapsed, 6),
            "stdout": stdout,
            "stderr": stderr,
            "event_count": len(parsed["events"]),
        }
    )
    return parsed
