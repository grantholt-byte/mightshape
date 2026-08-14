#!/usr/bin/env python3
"""Compare independently interviewed participants and flag synthetic convergence."""

from __future__ import annotations

import argparse
import itertools
import json
import re
import sys
from typing import Any

from dc_core import DesignCouncilError, json_output, load_json


STOP = {"the", "and", "that", "this", "with", "from", "have", "would", "there", "they", "them", "about", "because", "when", "what", "then", "just", "into", "your", "their", "were", "been", "could", "should"}


def _participant_text(transcript: dict[str, Any]) -> str:
    messages = transcript.get("messages", [])
    if isinstance(messages, list):
        parts = [str(item.get("text", "")) for item in messages if isinstance(item, dict) and item.get("role") == "participant"]
        if parts:
            return " ".join(parts)
    return str(transcript.get("response", transcript.get("text", "")))


def _features(text: str) -> set[str]:
    words = [word for word in re.findall(r"[a-z][a-z0-9'-]{2,}", text.lower()) if word not in STOP]
    unigrams = set(words)
    bigrams = {f"{left} {right}" for left, right in zip(words, words[1:])}
    return unigrams | bigrams


def _jaccard(left: set[str], right: set[str]) -> float:
    return len(left & right) / len(left | right) if left or right else 0.0


def compare_participants(value: Any, threshold: float = 0.62) -> dict[str, Any]:
    if not 0 < threshold <= 1:
        raise DesignCouncilError("threshold must be greater than 0 and at most 1")
    if isinstance(value, dict):
        transcripts = value.get("transcripts", value.get("participants", []))
        persona_records = value.get("personas", [])
    elif isinstance(value, list):
        transcripts, persona_records = value, []
    else:
        raise DesignCouncilError("input must be a transcript array or object containing transcripts")
    if not isinstance(transcripts, list) or len(transcripts) < 2:
        raise DesignCouncilError("at least two independently collected transcripts are required")
    identifiers: list[str] = []
    texts: dict[str, str] = {}
    provenances: dict[str, str] = {}
    independence_violations = []
    for index, transcript in enumerate(transcripts, 1):
        if not isinstance(transcript, dict):
            raise DesignCouncilError(f"transcript {index} must be an object")
        identifier = str(transcript.get("participant_id", transcript.get("id", f"P-{index:03d}")))
        if identifier in texts:
            raise DesignCouncilError(f"duplicate participant identifier: {identifier}")
        identifiers.append(identifier)
        texts[identifier] = _participant_text(transcript)
        provenances[identifier] = str(transcript.get("provenance", transcript.get("participant_type", "UNKNOWN")))
    empty = [identifier for identifier, content in texts.items() if not content.strip()]
    if empty:
        raise DesignCouncilError("participant response text is empty for: " + ", ".join(empty))
    for identifier, content in texts.items():
        siblings = [other for other in identifiers if other != identifier and re.search(rf"\b{re.escape(other)}\b", content, re.I)]
        if siblings:
            independence_violations.append({"participant_id": identifier, "references": siblings, "message": "Participant response references a sibling identifier before synthesis"})
    pairwise = []
    scores = []
    high_pairs = 0
    for left, right in itertools.combinations(identifiers, 2):
        score = _jaccard(_features(texts[left]), _features(texts[right]))
        scores.append(score)
        exact = bool(texts[left].strip()) and re.sub(r"\s+", " ", texts[left].strip().lower()) == re.sub(r"\s+", " ", texts[right].strip().lower())
        suspicious = score >= threshold or exact
        high_pairs += int(suspicious)
        pairwise.append({"participants": [left, right], "similarity": round(score, 3), "exact_duplicate": exact, "suspicious": suspicious})
    average = sum(scores) / len(scores) if scores else 0.0
    all_synthetic = all(item.startswith("SYNTHETIC_") for item in provenances.values())
    variation_sets = []
    for persona in persona_records if isinstance(persona_records, list) else []:
        if isinstance(persona, dict):
            variation_sets.append(persona.get("variation_dimensions", {}))
    weak_variation = bool(variation_sets) and (any(len(item) < 2 for item in variation_sets) or len({json.dumps(item, sort_keys=True) for item in variation_sets}) < len(variation_sets))
    suspicious = all_synthetic and (high_pairs >= max(1, len(pairwise) // 2) or average >= threshold * 0.85)
    causes = []
    if suspicious:
        causes.extend(["weak persona differentiation", "interviewer leading", "shared grounding overconstraint", "model convergence"])
    if weak_variation:
        causes.insert(0, "variation dimensions are missing, duplicated, or behaviorally thin")
    if independence_violations:
        causes.insert(0, "participant independence may have been breached")
    return {
        "participant_count": len(identifiers),
        "provenance": provenances,
        "pairwise": pairwise,
        "average_similarity": round(average, 3),
        "threshold": threshold,
        "independence_violations": independence_violations,
        "independence_passes": not independence_violations,
        "variation_warning": weak_variation,
        "warning": "SYNTHETIC_CONVERGENCE_WARNING" if suspicious else None,
        "possible_causes": list(dict.fromkeys(causes)),
        "interpretation": "Agreement remains synthetic and is not evidence of prevalence or human behavior." if all_synthetic else "Do not merge human and synthetic samples; compare provenance layers separately.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Detect suspicious convergence across participant interviews")
    parser.add_argument("input", nargs="?", help="JSON file; stdin when omitted")
    parser.add_argument("--threshold", type=float, default=0.62)
    args = parser.parse_args()
    try:
        value = load_json(args.input) if args.input else json.load(sys.stdin)
        json_output(compare_participants(value, args.threshold))
    except (DesignCouncilError, json.JSONDecodeError) as exc:
        print(f"MightShape error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
