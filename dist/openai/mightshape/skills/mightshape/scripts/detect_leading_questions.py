#!/usr/bin/env python3
"""Non-blocking Interview Coach for weak or contaminating questions."""

from __future__ import annotations

import argparse
import json
import re
import sys
from typing import Any

from dc_core import DesignCouncilError, json_output, load_json


PATTERNS: list[tuple[str, re.Pattern[str], str]] = [
    ("LEADING", re.compile(r"\b(wouldn['’]?t|don['’]?t you|surely|obviously|clearly|isn['’]?t it|agree that)\b", re.I), "It embeds or rewards a preferred answer."),
    ("HYPOTHETICAL_PREFERENCE", re.compile(r"\b(would you|will you|do you think you would|wouldn['’]?t you)\b", re.I), "Future preference is a weak proxy for behavior."),
    ("SOLUTION_BIASED", re.compile(r"\b(ai|app|platform|dashboard|assistant|automation|feature|prototype|our solution|this solution)\b", re.I), "It introduces a solution before current behavior is understood."),
    ("EXCESSIVE_ABSTRACTION", re.compile(r"\b(generally|typically|in general|usually|overall|people like you|most people|ideal)\b", re.I), "Abstract summaries hide sequence, context, and exceptions."),
]


def stronger_alternative(question: str, flags: list[str]) -> str:
    lower = question.lower()
    if "why" in lower and not any(flag in flags for flag in ("SOLUTION_BIASED", "HYPOTHETICAL_PREFERENCE")):
        return "Tell me about the last time that happened. What happened next?"
    if "SOLUTION_BIASED" in flags or "HYPOTHETICAL_PREFERENCE" in flags or "LEADING" in flags:
        return "Tell me about the last time this part became difficult. What did you do next?"
    if "COMPOUND" in flags:
        return "Ask the first part alone, then follow the participant's story before asking another question."
    return "Can you walk me through the most recent time this happened, starting at the first trigger?"


def coach_question(question: str, solution_blackout: bool = False) -> dict[str, Any]:
    question = question.strip()
    if not question:
        raise DesignCouncilError("question must not be empty")
    findings = []
    flags = []
    for name, pattern, explanation in PATTERNS:
        if pattern.search(question):
            flags.append(name)
            findings.append({"type": name, "explanation": explanation})
    interrogatives = len(re.findall(r"\?", question))
    conjunctions = len(re.findall(r"\b(and|or|plus|as well as)\b", question, re.I))
    clauses = len(re.findall(r"\b(what|how|why|when|where|who|would|could|did|do)\b", question, re.I))
    if interrogatives > 1 or (conjunctions >= 1 and clauses >= 2):
        flags.append("COMPOUND")
        findings.append({"type": "COMPOUND", "explanation": "It asks for multiple judgments or stories at once."})
    if solution_blackout and "SOLUTION_BIASED" in flags:
        flags.append("SOLUTION_BLACKOUT_BREACH")
        findings.append({"type": "SOLUTION_BLACKOUT_BREACH", "explanation": "The named exploratory mode prohibits unnecessary concept priming."})
    # Deduplicate while retaining inspection order.
    flags = list(dict.fromkeys(flags))
    findings = list({item["type"]: item for item in findings}.values())
    return {
        "question": question,
        "coach_status": "SUGGEST_REVISION" if flags else "CLEAR",
        "flags": flags,
        "findings": findings,
        "suggested_alternative": stronger_alternative(question, flags) if flags else None,
        "solution_blackout": solution_blackout,
        "blocking": False,
        "note": "Interview Coach advises but never prevents the researcher from continuing.",
    }


def coach_input(value: Any, solution_blackout: bool = False) -> dict[str, Any]:
    if isinstance(value, str):
        questions = [value]
    elif isinstance(value, list):
        questions = [str(item) for item in value]
    elif isinstance(value, dict):
        raw = value.get("questions", value.get("question"))
        solution_blackout = bool(value.get("solution_blackout", solution_blackout))
        questions = [str(item) for item in raw] if isinstance(raw, list) else [str(raw)] if raw is not None else []
    else:
        raise DesignCouncilError("input must be a question, array, or object")
    if not questions:
        raise DesignCouncilError("no questions supplied")
    coached = [coach_question(item, solution_blackout) for item in questions]
    return {
        "results": coached,
        "counts": {flag: sum(flag in item["flags"] for item in coached) for flag in sorted({f for item in coached for f in item["flags"]})},
        "blocking": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Coach interview questions without blocking them")
    parser.add_argument("input", nargs="?", help="JSON file; use --question or stdin when omitted")
    parser.add_argument("--question", action="append", default=[])
    parser.add_argument("--solution-blackout", action="store_true")
    args = parser.parse_args()
    try:
        if args.question:
            value: Any = args.question
        elif args.input:
            value = load_json(args.input)
        else:
            value = json.load(sys.stdin)
        json_output(coach_input(value, args.solution_blackout))
    except (DesignCouncilError, json.JSONDecodeError) as exc:
        print(f"MightShape error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
