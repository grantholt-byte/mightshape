from __future__ import annotations

import json
import os
from pathlib import Path
import tempfile
import unittest

from evals.claude_runtime import (
    ClaudeRuntimeError,
    build_claude_command,
    explicit_auth_key,
    isolated_claude_environment,
    parse_claude_stream,
    validate_arm_init,
)


class ClaudeBenchmarkRuntimeTests(unittest.TestCase):
    def test_command_arm_delta_is_only_plugin_dir(self) -> None:
        common = dict(
            binary="claude",
            prompt="decide",
            model="claude-sonnet-test",
            effort="medium",
            max_turns=12,
            max_budget_usd=5,
        )
        control = build_claude_command(**common)
        treatment = build_claude_command(**common, plugin_dir=Path("/tmp/plugin"))
        self.assertEqual(treatment[:-2], control)
        self.assertEqual(treatment[-2:], ["--plugin-dir", "/tmp/plugin"])
        self.assertIn("local", control)
        self.assertNotIn("--bare", control)

    def test_environment_keeps_one_auth_secret_without_logging_it(self) -> None:
        source = {
            "PATH": "/bin",
            "HOME": "/home/test",
            "ANTHROPIC_API_KEY": "secret",
            "OPENAI_API_KEY": "drop-me",
            "AWS_SECRET_ACCESS_KEY": "drop-me-too",
        }
        with tempfile.TemporaryDirectory() as name:
            environment = isolated_claude_environment(source, Path(name))
        self.assertEqual(environment["ANTHROPIC_API_KEY"], "secret")
        self.assertNotIn("OPENAI_API_KEY", environment)
        self.assertNotIn("AWS_SECRET_ACCESS_KEY", environment)
        self.assertEqual(environment["DISABLE_TELEMETRY"], "1")
        self.assertEqual(explicit_auth_key(source), "ANTHROPIC_API_KEY")

    def test_environment_rejects_ambiguous_auth(self) -> None:
        with self.assertRaises(ClaudeRuntimeError):
            explicit_auth_key({"ANTHROPIC_API_KEY": "x", "CLAUDE_CODE_OAUTH_TOKEN": "y"})

    def test_stream_parser_counts_usage_once_and_detects_error(self) -> None:
        init = {"type": "system", "subtype": "init", "model": "m", "tools": ["Read"], "skills": [], "agents": [], "plugins": []}
        result = {
            "type": "result",
            "is_error": False,
            "result": "Answer",
            "usage": {
                "input_tokens": 10,
                "cache_creation_input_tokens": 20,
                "cache_read_input_tokens": 30,
                "output_tokens": 4,
            },
        }
        parsed = parse_claude_stream("\n".join(json.dumps(item) for item in (init, result)))
        self.assertEqual(parsed["status"], "OK")
        self.assertEqual(parsed["usage"]["total_tokens"], 64)
        result["is_error"] = True
        self.assertEqual(
            parse_claude_stream("\n".join(json.dumps(item) for item in (init, result)))["status"],
            "ERROR",
        )

    def test_init_parity_allows_only_design_council(self) -> None:
        control = {
            "model": "claude-sonnet-test",
            "tools": ["Task", "Read", "Skill"],
            "plugins": [],
            "skills": ["verify", "debug"],
            "agents": ["claude", "Explore"],
        }
        treatment = {
            **control,
            "plugins": [{"name": "design-council", "version": "beta"}],
            "skills": ["verify", "debug", "design-council:design-council"],
            "agents": ["claude", "Explore", "design-council:sealed-member"],
        }
        self.assertEqual(validate_arm_init(control, treatment), [])
        treatment["tools"] = ["Read"]
        self.assertIn("tools differs between arms", validate_arm_init(control, treatment))


if __name__ == "__main__":
    unittest.main()
