#!/usr/bin/env python3
"""Run an opt-in, name-blind Council recognition/confusion evaluation.

Ten independent model calls each receive the same neutral challenge and one
canonical Council profile. Their conclusion-level responses are screened for
direct identity, role, and biography leakage, frozen as an anonymous set, and
only then shown to a separate evaluator. The evaluator must assign all ten
identities exactly once.

This measures model-based traceability to the source profiles used for
generation. It is not human ground truth, a claim about human recognizability,
or evidence that the fictional people are real.
"""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import random
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from typing import Any, Iterable, Sequence

try:
    from run_ab_benchmark import (
        allocate_opaque_cell,
        find_user_skill_files,
        prepare_codex_home,
        run_codex_json,
    )
except ModuleNotFoundError:  # Imported as evals.run_council_recognition.
    from evals.run_ab_benchmark import (
        allocate_opaque_cell,
        find_user_skill_files,
        prepare_codex_home,
        run_codex_json,
    )


EVAL_ROOT = Path(__file__).resolve().parent
REPO_ROOT = EVAL_ROOT.parent
REFERENCE_ROOT = REPO_ROOT / "skills" / "design-council" / "references"
CHALLENGE_PATH = EVAL_ROOT / "benchmark" / "council-recognition-challenge.json"
RESPONSE_SCHEMA = EVAL_ROOT / "schema" / "council-recognition-response.schema.json"
JUDGE_SCHEMA = EVAL_ROOT / "schema" / "council-recognition-judge.schema.json"
RESULTS_ROOT = EVAL_ROOT / "results" / "council-recognition"

MEMBER_SPECS: tuple[tuple[str, str], ...] = (
    ("maya-chen", "Maya Chen"),
    ("leo-martinez", "Leo Martinez"),
    ("priya-rao", "Priya Rao"),
    ("marcus-brooks", "Marcus Brooks"),
    ("elena-rossi", "Elena Rossi"),
    ("theo-bennett", "Theo Bennett"),
    ("samira-okafor", "Samira Okafor"),
    ("jack-sullivan", "Jack Sullivan"),
    ("mei-tanaka", "Mei Tanaka"),
    ("rafael-alvarez", "Rafael Alvarez"),
)
IDENTITIES = tuple(name for _slug, name in MEMBER_SPECS)

GENERATOR_INSTRUCTION = """You are generating one sealed, conclusion-level response for a
Council identity-recognition evaluation. Use only the common packet and the one canonical Human
Model below. Let the complete Human Model shape attention, judgment, values, uncertainty, and
natural language. Do not imitate a generic role viewpoint.

The response will be evaluated without its name or profile label. It must not reveal or hint at
the identity through a name, job or professional title, age, place, education, ethnicity,
nationality, family relationship, named personal event, career episode, Council relationship,
or signature calibration sentence. Do not say "as a ...", narrate biography, cite your field,
or use specialized occupational jargon merely as an identity marker. Do not quote the profile.
Distinctiveness must come from reasoning priorities, values, analogy habits, risk posture,
question style, sentence shape, and a natural knowledge boundary.

Return conclusions, hypotheses, questions, and a recommended move only. Do not expose hidden
chain-of-thought. Do not use tools, inspect files, mention this evaluation, or claim human
evidence. Keep the `response` between 70 and 180 words and return only JSON matching the schema.
"""

JUDGE_INSTRUCTION = """Act as a blinded identity-recognition evaluator. You receive ten frozen,
anonymous conclusion-level artifacts from fictional Design Council Human Models and ten anonymous
behavioral reference cards projected from the canonical profiles. Names, roles, signature samples,
and obvious biography have been withheld from both artifact text and reference cards. Neither the
artifact-to-source mapping nor the profile-card-to-identity mapping is provided.

Assign every artifact to exactly one profile card and use every profile card exactly once. Base matches
on observable attention patterns, values, reasoning and analogy habits, risk posture, question
style, communication fingerprint, contradictions, and knowledge boundaries. Do not reward a
generic competent design answer. Do not use tools or inspect files. Provide only short observable
cue labels, never hidden chain-of-thought. Return only JSON matching the supplied schema.

This is a model-based profile-traceability exercise. Your assignments are not human ground truth
and do not establish that human readers would recognize these fictional identities. The controller
maps profile-card IDs to source-profile names only after your response is complete.
"""

# Deterministic exclusion screen. These terms are identifiers, explicit job
# labels, and conspicuous biographical details; they are not the subtle cues the
# evaluation is intended to measure.
ROLE_LEAK_RE = re.compile(
    r"\b(?:emergency nurse|nurse|healthcare operations|mechanical engineer|behavioral scientist|"
    r"measurement researcher|laundromat(?:s)?|small[- ]business operator|service operator|"
    r"experience designer|industrial designer|investigative journalist|journalist|reporter|"
    r"community organizer|public[- ]service designer|sales operator|software engineer|"
    r"data architect|technical architect|systems engineer|theat(?:er|re) director|"
    r"installation artist|improviser)\b",
    re.IGNORECASE,
)
PLACE_LEAK_RE = re.compile(
    r"\b(?:Saint Paul|Minnesota|Tucson|Providence|Rhode Island|Somerville|Massachusetts|Pune|"
    r"Calgary|Baltimore|Dayton|Chicago|Turin|Philadelphia|Syracuse|Minneapolis|Milwaukee|"
    r"Enugu|Seattle|Sacramento|Nagoya|El Paso)\b",
    re.IGNORECASE,
)
BIOGRAPHY_LEAK_RE = re.compile(
    r"\b(?:I|we)\s+(?:grew up|used to work|worked as|studied|live in|am an?|was an?)\b|"
    r"\bI(?:'ve| have)?\s+(?:seen|learned|found|watched|managed|led|built|designed|reported|sold|worked)\b|"
    r"\bmy\s+(?:mother|father|parent|daughter|son|partner|spouse|childhood|family|career)\b|"
    r"\b(?:in|from)\s+my\s+(?:work|career|profession|field|childhood)\b",
    re.IGNORECASE,
)
AGE_LEAK_RE = re.compile(
    r"\b(?:at|age[d]?)\s+(?:39|40|41|42|44|46|47|52)\b|"
    r"\b(?:39|40|41|42|44|46|47|52)(?:\s+years?\s+old|-year-old)\b",
    re.IGNORECASE,
)
SIGNATURE_QUESTION_RE = re.compile(
    r"(?:what happens when this goes wrong|crudest thing we can build today|"
    r"observing behavior or simply agreement|who has to do the extra work|"
    r"what should this experience feel like|what would have to be false|"
    r"whose problem gets solved.*whose work gets moved|"
    r"what are they doing today.*asking them to stop|"
    r"which part of this actually needs intelligence|delete the app.*what happens|"
    r"how would a theme park solve this|ridiculous version that reveals something true)",
    re.IGNORECASE,
)


class RecognitionError(RuntimeError):
    """Raised for invalid configuration or an incomplete sealed evaluation."""


@dataclass(frozen=True)
class MemberProfile:
    slug: str
    name: str
    path: Path
    source_text: str
    sealed_text: str
    judge_text: str
    source_sha256: str
    sealed_sha256: str
    judge_sha256: str


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def command_text(command: Sequence[str], cwd: Path | None = None) -> str | None:
    try:
        completed = subprocess.run(
            list(command),
            cwd=cwd,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            check=False,
            timeout=20,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    output = completed.stdout.strip()
    return output if completed.returncode == 0 and output else None


def git_state() -> dict[str, Any]:
    commit = command_text(["git", "rev-parse", "HEAD"], cwd=REPO_ROOT)
    try:
        completed = subprocess.run(
            ["git", "status", "--porcelain=v1", "--untracked-files=all"],
            cwd=REPO_ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            check=False,
            timeout=20,
        )
    except (OSError, subprocess.TimeoutExpired):
        return {"commit": commit, "dirty": None, "status_available": False}
    return {
        "commit": commit,
        "dirty": bool(completed.stdout.strip()) if completed.returncode == 0 else None,
        "status_available": completed.returncode == 0,
    }


def load_challenge(path: Path = CHALLENGE_PATH) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise RecognitionError(f"challenge file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise RecognitionError(f"invalid challenge JSON: {exc.msg}") from exc
    required = {"schema_version", "id", "title", "challenge", "task", "evidence_status"}
    if not isinstance(value, dict) or not required.issubset(value):
        raise RecognitionError("challenge is missing required fields")
    if value["schema_version"] != "1.0.0":
        raise RecognitionError("unsupported challenge schema_version")
    if not all(isinstance(value[key], str) and value[key].strip() for key in ("id", "title", "challenge", "task")):
        raise RecognitionError("challenge text fields must be non-empty strings")
    evidence = value["evidence_status"]
    if not isinstance(evidence, list) or not evidence or not all(isinstance(item, str) and item.strip() for item in evidence):
        raise RecognitionError("evidence_status must be a non-empty string array")
    return value


def sealed_profile_projection(source: str, own_name: str) -> str:
    """Project a canonical profile into a sealed, relationship-free packet."""

    kept: list[str] = []
    skipping = False
    for line in source.splitlines():
        if line.startswith("## "):
            heading = line[3:].strip().lower()
            skipping = heading.startswith("council relationships") or heading.startswith("project-memory behavior")
        if not skipping:
            kept.append(line)
    projected = "\n".join(kept).strip() + "\n"
    own_parts = set(own_name.split())
    for _slug, other_name in MEMBER_SPECS:
        if other_name == own_name:
            continue
        for token in (other_name, *other_name.split()):
            if token in own_parts:
                continue
            projected = re.sub(rf"\b{re.escape(token)}\b", "[another Council member]", projected)
    return projected


def judge_profile_projection(source: str) -> str:
    """Return a name/role/biography-free behavioral card for the blind judge."""

    allowed = False
    skip_samples = False
    selected: list[str] = []
    for line in source.splitlines():
        if line.startswith("## "):
            heading = line[3:].strip().lower()
            allowed = heading.startswith(("worldview", "cognitive and emotional", "communication fingerprint"))
            skip_samples = False
            if allowed:
                selected.append(f"## {heading.title()}")
            continue
        if line.startswith("### ") or "unlabeled voice samples" in line.lower():
            skip_samples = True
            continue
        if allowed and not skip_samples and not line.lstrip().startswith(">"):
            selected.append(line)
    projected = "\n".join(selected)
    for _slug, name in MEMBER_SPECS:
        for token in (name, *name.split()):
            projected = re.sub(rf"\b{re.escape(token)}\b", "[identity withheld]", projected)
    # Remove whole prose lines containing an explicit role, location, age, or
    # close-family fact. The remaining material describes cognition, values,
    # affect, and communication without an occupational/biographical shortcut.
    safe_lines: list[str] = []
    family = re.compile(r"\b(?:mother|father|daughter|son|partner|spouse|childhood|grew up|career)\b", re.IGNORECASE)
    for line in projected.splitlines():
        if line.startswith("## ") or not line.strip():
            safe_lines.append(line)
            continue
        if ROLE_LEAK_RE.search(line) or PLACE_LEAK_RE.search(line) or AGE_LEAK_RE.search(line) or family.search(line):
            continue
        safe_lines.append(line)
    result = "\n".join(safe_lines).strip() + "\n"
    if len(_normalized_words(result)) < 100:
        raise RecognitionError("judge profile projection became too small")
    return result


def load_profiles(reference_root: Path = REFERENCE_ROOT) -> list[MemberProfile]:
    profiles: list[MemberProfile] = []
    for slug, name in MEMBER_SPECS:
        path = reference_root / f"council-{slug}.md"
        if not path.is_file():
            raise RecognitionError(f"canonical profile not found: {path}")
        source = path.read_text(encoding="utf-8")
        if not source.startswith(f"# {name} "):
            raise RecognitionError(f"canonical profile heading does not match {name}: {path}")
        sealed = sealed_profile_projection(source, name)
        judge_text = judge_profile_projection(source)
        profiles.append(
            MemberProfile(
                slug=slug,
                name=name,
                path=path,
                source_text=source,
                sealed_text=sealed,
                judge_text=judge_text,
                source_sha256=sha256_file(path),
                sealed_sha256=sha256_text(sealed),
                judge_sha256=sha256_text(judge_text),
            )
        )
    return profiles


def common_packet(challenge: dict[str, Any]) -> dict[str, Any]:
    return {
        "challenge_id": challenge["id"],
        "challenge": challenge["challenge"],
        "task": challenge["task"],
        "evidence_status": challenge["evidence_status"],
    }


def candidate_prompt(profile: MemberProfile, challenge: dict[str, Any]) -> str:
    return (
        f"{GENERATOR_INSTRUCTION}\n\n"
        "COMMON PACKET (identical for all ten sealed calls):\n"
        f"{json.dumps(common_packet(challenge), indent=2, ensure_ascii=False)}\n\n"
        "ONE CANONICAL HUMAN MODEL (relationship/project-memory sections removed for sealing):\n"
        f"{profile.sealed_text}"
    )


def judge_prompt(
    challenge: dict[str, Any],
    artifacts: Sequence[dict[str, str]],
    profile_cards: Sequence[dict[str, str]],
) -> str:
    artifact_block = "\n\n".join(
        f"### {item['artifact_id']}\n{item['response']}" for item in artifacts
    )
    profile_block = "\n\n".join(
        f"### {card['profile_id']}\n{card['behavioral_reference']}" for card in profile_cards
    )
    return (
        f"{JUDGE_INSTRUCTION}\n\n"
        "COMMON PACKET:\n"
        f"{json.dumps(common_packet(challenge), indent=2, ensure_ascii=False)}\n\n"
        "FROZEN ANONYMOUS ARTIFACTS:\n"
        f"{artifact_block}\n\n"
        "ANONYMOUS CANONICAL BEHAVIORAL REFERENCE CARDS (order carries no mapping):\n"
        f"{profile_block}"
    )


def _normalized_words(text: str) -> list[str]:
    return re.findall(r"[a-z0-9']+", text.lower())


def _copied_profile_phrase(text: str, profiles: Sequence[MemberProfile], n: int = 10) -> str | None:
    words = _normalized_words(text)
    if len(words) < n:
        return None
    source_ngrams: set[tuple[str, ...]] = set()
    for profile in profiles:
        source_words = _normalized_words(profile.source_text)
        source_ngrams.update(tuple(source_words[index : index + n]) for index in range(len(source_words) - n + 1))
    for index in range(len(words) - n + 1):
        phrase = tuple(words[index : index + n])
        if phrase in source_ngrams:
            return " ".join(phrase)
    return None


def _signature_sample_phrases(profile: MemberProfile, n: int = 6) -> set[tuple[str, ...]]:
    """Extract n-grams only from canonical unlabeled voice/calibration samples."""

    in_samples = False
    phrases: set[tuple[str, ...]] = set()
    for line in profile.source_text.splitlines():
        lowered = line.lower()
        if "unlabeled calibration samples" in lowered or "unlabeled voice samples" in lowered:
            in_samples = True
            continue
        if in_samples and line.startswith("## "):
            break
        if not in_samples:
            continue
        words = _normalized_words(line)
        phrases.update(tuple(words[index : index + n]) for index in range(len(words) - n + 1))
    return phrases


def _copied_signature_phrase(text: str, profiles: Sequence[MemberProfile], n: int = 6) -> str | None:
    words = _normalized_words(text)
    if len(words) < n:
        return None
    signature_ngrams: set[tuple[str, ...]] = set()
    for profile in profiles:
        signature_ngrams.update(_signature_sample_phrases(profile, n=n))
    for index in range(len(words) - n + 1):
        phrase = tuple(words[index : index + n])
        if phrase in signature_ngrams:
            return " ".join(phrase)
    return None


def leakage_findings(text: str, profiles: Sequence[MemberProfile]) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    for _slug, name in MEMBER_SPECS:
        for token in (name, *name.split()):
            match = re.search(rf"\b{re.escape(token)}\b", text, flags=re.IGNORECASE)
            if match:
                findings.append({"type": "council_identifier", "match": match.group(0)})
    for label, pattern in (
        ("explicit_role", ROLE_LEAK_RE),
        ("place_or_origin", PLACE_LEAK_RE),
        ("biography_statement", BIOGRAPHY_LEAK_RE),
        ("age", AGE_LEAK_RE),
        ("signature_question", SIGNATURE_QUESTION_RE),
    ):
        match = pattern.search(text)
        if match:
            findings.append({"type": label, "match": match.group(0)})
    copied = _copied_profile_phrase(text, profiles)
    if copied:
        findings.append({"type": "copied_profile_phrase", "match": copied})
    signature = _copied_signature_phrase(text, profiles)
    if signature:
        findings.append({"type": "signature_sample_phrase", "match": signature})
    # Preserve order but do not repeat the same detector result.
    unique: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for finding in findings:
        key = (finding["type"], finding["match"].lower())
        if key not in seen:
            seen.add(key)
            unique.append(finding)
    return unique


def parse_candidate_response(raw: str, profiles: Sequence[MemberProfile]) -> dict[str, Any]:
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RecognitionError(f"candidate response is not JSON: {exc.msg}") from exc
    if not isinstance(payload, dict) or set(payload) != {"response"}:
        raise RecognitionError("candidate response must contain only `response`")
    response = payload["response"]
    if not isinstance(response, str) or not response.strip():
        raise RecognitionError("candidate `response` must be a non-empty string")
    words = len(response.split())
    if words < 70 or words > 180:
        raise RecognitionError(f"candidate response has {words} words; expected 70..180")
    findings = leakage_findings(response, profiles)
    if findings:
        compact = ", ".join(f"{item['type']}={item['match']!r}" for item in findings)
        raise RecognitionError(f"candidate response failed leakage screen: {compact}")
    return {"response": response, "word_count": words, "leakage_findings": []}


def parse_judgment(
    raw: str,
    artifact_ids: Iterable[str],
    profile_ids: Iterable[str] | None = None,
) -> dict[str, Any]:
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RecognitionError(f"judge response is not JSON: {exc.msg}") from exc
    if not isinstance(payload, dict) or set(payload) != {"assignments", "overall_notes"}:
        raise RecognitionError("judge response must contain assignments and overall_notes")
    assignments = payload["assignments"]
    if not isinstance(assignments, list) or len(assignments) != len(IDENTITIES):
        raise RecognitionError("judge must return exactly ten assignments")
    expected_artifacts = set(artifact_ids)
    seen_artifacts: set[str] = set()
    expected_profiles = set(profile_ids or (f"P-01-{index:02d}" for index in range(1, 11)))
    seen_profiles: set[str] = set()
    for item in assignments:
        if not isinstance(item, dict) or set(item) != {
            "artifact_id",
            "assigned_profile_id",
            "confidence",
            "observable_cues",
        }:
            raise RecognitionError("each assignment has an invalid shape")
        artifact_id = item["artifact_id"]
        profile_id = item["assigned_profile_id"]
        confidence = item["confidence"]
        cues = item["observable_cues"]
        if artifact_id not in expected_artifacts or artifact_id in seen_artifacts:
            raise RecognitionError(f"unknown or duplicate artifact assignment: {artifact_id!r}")
        if profile_id not in expected_profiles or profile_id in seen_profiles:
            raise RecognitionError(f"unknown or duplicate profile-card assignment: {profile_id!r}")
        if isinstance(confidence, bool) or not isinstance(confidence, (int, float)) or not 0 <= confidence <= 1:
            raise RecognitionError("assignment confidence must be between 0 and 1")
        if not isinstance(cues, list) or not 1 <= len(cues) <= 4 or not all(isinstance(cue, str) and cue.strip() for cue in cues):
            raise RecognitionError("observable_cues must contain one to four strings")
        seen_artifacts.add(artifact_id)
        seen_profiles.add(profile_id)
    if seen_artifacts != expected_artifacts or seen_profiles != expected_profiles:
        raise RecognitionError("judge assignments must be one-to-one and complete")
    if not isinstance(payload["overall_notes"], str) or not payload["overall_notes"].strip():
        raise RecognitionError("overall_notes must be a non-empty string")
    return payload


def derangements(n: int) -> int:
    if n < 0:
        raise ValueError("n must be non-negative")
    if n == 0:
        return 1
    if n == 1:
        return 0
    before, current = 1, 0
    for value in range(2, n + 1):
        before, current = current, (value - 1) * (current + before)
    return current


def fixed_point_counts(n: int = 10) -> list[int]:
    return [math.comb(n, fixed) * derangements(n - fixed) for fixed in range(n + 1)]


def chance_tail_probability(observed_correct: int, repeats: int, n: int = 10) -> float:
    if repeats < 1:
        raise ValueError("repeats must be positive")
    if observed_correct < 0 or observed_correct > repeats * n:
        raise ValueError("observed_correct is outside the possible range")
    distribution = fixed_point_counts(n)
    aggregate = [1]
    for _ in range(repeats):
        combined = [0] * (len(aggregate) + n)
        for left_index, left_count in enumerate(aggregate):
            for fixed, count in enumerate(distribution):
                combined[left_index + fixed] += left_count * count
        aggregate = combined
    numerator = sum(aggregate[observed_correct:])
    denominator = math.factorial(n) ** repeats
    return numerator / denominator


def empty_confusion_matrix() -> dict[str, dict[str, int]]:
    return {actual: {predicted: 0 for predicted in IDENTITIES} for actual in IDENTITIES}


def score_assignments(
    source_by_artifact: dict[str, str],
    identity_by_profile_id: dict[str, str],
    judgment: dict[str, Any],
) -> dict[str, Any]:
    matrix = empty_confusion_matrix()
    correct = 0
    rows: list[dict[str, Any]] = []
    for assignment in judgment["assignments"]:
        artifact_id = assignment["artifact_id"]
        source = source_by_artifact[artifact_id]
        predicted = identity_by_profile_id[assignment["assigned_profile_id"]]
        is_correct = source == predicted
        correct += int(is_correct)
        matrix[source][predicted] += 1
        rows.append(
            {
                "artifact_id": artifact_id,
                "source_profile": source,
                "assigned_profile_id": assignment["assigned_profile_id"],
                "assigned_identity": predicted,
                "correct": is_correct,
                "confidence": assignment["confidence"],
                "observable_cues": assignment["observable_cues"],
            }
        )
    return {"correct": correct, "total": len(rows), "assignments": rows, "confusion_matrix": matrix}


def merge_confusion_matrices(matrices: Sequence[dict[str, dict[str, int]]]) -> dict[str, dict[str, int]]:
    merged = empty_confusion_matrix()
    for matrix in matrices:
        for actual in IDENTITIES:
            for predicted in IDENTITIES:
                merged[actual][predicted] += matrix[actual][predicted]
    return merged


def result_run_dir(root: Path = RESULTS_ROOT) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    base = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    candidate = root / base
    suffix = 1
    while candidate.exists():
        candidate = root / f"{base}-{suffix}"
        suffix += 1
    candidate.mkdir()
    return candidate


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def render_summary(summary: dict[str, Any]) -> str:
    lines = [
        "# Council name-blind recognition result",
        "",
        f"Status: **{summary['status']}**",
        "",
        "> This is model-based traceability to the canonical fictional source profiles. It is not human ground truth and does not establish human recognizability.",
        "",
    ]
    if summary["status"] != "COMPLETE":
        lines.extend([f"Reason: {summary.get('error', 'incomplete run')}", ""])
        return "\n".join(lines)
    lines.extend(
        [
            f"Source-profile assignment accuracy: **{summary['accuracy']:.1%}** "
            f"({summary['correct_assignments']}/{summary['total_assignments']})",
            f"Forced-permutation chance baseline: **{summary['chance_baseline']['expected_accuracy']:.1%}**",
            "",
            "## Confusion matrix",
            "",
            "Rows are source profiles used for generation; columns are evaluator assignments.",
            "",
            "| Source \\ Assigned | " + " | ".join(IDENTITIES) + " |",
            "|---|" + "---:|" * len(IDENTITIES),
        ]
    )
    matrix = summary["confusion_matrix"]
    for actual in IDENTITIES:
        lines.append(f"| {actual} | " + " | ".join(str(matrix[actual][predicted]) for predicted in IDENTITIES) + " |")
    lines.extend(
        [
            "",
            "The random-permutation tail probability is a descriptive chance reference for this constrained assignment task, not a human-study p-value.",
            "",
        ]
    )
    return "\n".join(lines)


def build_summary(
    completed_scores: Sequence[dict[str, Any]],
    planned_repeats: int,
    run_error: str | None,
) -> dict[str, Any]:
    """Build a directional result only for a fully realized sealed design."""

    complete = run_error is None and len(completed_scores) == planned_repeats
    scope = "model-based traceability to canonical fictional Council source profiles; not human ground truth"
    if not complete:
        return {
            "schema_version": "1.0.0",
            "status": "INCOMPLETE",
            "study_scope": scope,
            "error": run_error or "not all planned repeats completed",
            "completed_repeats": len(completed_scores),
            "planned_repeats": planned_repeats,
            "correct_assignments": None,
            "total_assignments": None,
            "accuracy": None,
            "confusion_matrix": None,
            "chance_baseline": {
                "expected_accuracy": 0.1,
                "note": "No observed accuracy is reported for an incomplete sealed design.",
            },
        }

    correct = sum(int(score["correct"]) for score in completed_scores)
    total = sum(int(score["total"]) for score in completed_scores)
    return {
        "schema_version": "1.0.0",
        "status": "COMPLETE",
        "study_scope": scope,
        "correct_assignments": correct,
        "total_assignments": total,
        "accuracy": correct / total,
        "confusion_matrix": merge_confusion_matrices([score["confusion_matrix"] for score in completed_scores]),
        "chance_baseline": {
            "assignment_constraint": "one-to-one permutation within each ten-artifact repeat",
            "expected_accuracy": 0.1,
            "expected_correct_per_repeat": 1.0,
            "observed_correct": correct,
            "random_permutation_tail_probability_at_least_observed": chance_tail_probability(correct, planned_repeats),
            "interpretation": "descriptive random-permutation reference only; not a human-study p-value",
        },
        "limitations": [
            "Candidates and evaluator are models, not human raters.",
            "Source labels identify which fictional profile generated an artifact; they are not human ground truth.",
            "A one-to-one assignment constraint changes the chance distribution and can propagate one mistaken match.",
            "One neutral challenge does not establish identity consistency across contexts.",
            "Candidate and evaluator model-family effects may influence the result.",
        ],
    }


def call_metadata(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": result["status"],
        "returncode": result["returncode"],
        "timed_out": result["timed_out"],
        "wall_time_seconds": result["wall_time_seconds"],
        "usage": result["usage"],
        "event_count": result["event_count"],
        "activity": result["activity"],
        "warnings": result["warnings"],
        "stdout_sha256": sha256_text(result["stdout"]),
        "stderr_sha256": sha256_text(result["stderr"]),
    }


def dry_run_payload(
    profiles: Sequence[MemberProfile],
    challenge: dict[str, Any],
    args: argparse.Namespace,
) -> dict[str, Any]:
    return {
        "status": "DRY_RUN",
        "model_calls_made": 0,
        "planned_model_calls": args.repeats * 11,
        "planned_sealed_sets": args.repeats,
        "candidate_model": args.model,
        "candidate_effort": args.effort,
        "judge_model": args.judge_model,
        "judge_effort": args.judge_effort,
        "challenge_id": challenge["id"],
        "challenge_sha256": sha256_file(CHALLENGE_PATH),
        "generator_instruction_sha256": sha256_text(GENERATOR_INSTRUCTION),
        "judge_instruction_sha256": sha256_text(JUDGE_INSTRUCTION),
        "candidate_prompts": [
            {
                "source_profile": profile.name,
                "prompt_sha256": sha256_text(candidate_prompt(profile, challenge)),
                "canonical_profile_sha256": profile.source_sha256,
                "sealed_profile_sha256": profile.sealed_sha256,
                "judge_projection_sha256": profile.judge_sha256,
            }
            for profile in profiles
        ],
        "note": "Judge prompts depend on frozen generated artifacts and are recorded exactly in live runs.",
    }


def run_live(
    args: argparse.Namespace,
    codex: str,
    profiles: Sequence[MemberProfile],
    challenge: dict[str, Any],
) -> tuple[Path, dict[str, Any]]:
    source_codex_home = Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))).expanduser()
    if not source_codex_home.joinpath("auth.json").is_file():
        raise RecognitionError(f"no saved Codex auth file at {source_codex_home / 'auth.json'}")

    run_dir = result_run_dir(args.results_dir)
    rng = random.Random(args.seed)
    started_at = utc_now()
    generation_records: list[dict[str, Any]] = []
    repeat_records: list[dict[str, Any]] = []
    run_error: str | None = None

    with tempfile.TemporaryDirectory(prefix="design-council-recognition-") as temp_name:
        temp_root = Path(temp_name)
        for repeat in range(1, args.repeats + 1):
            call_order = list(profiles)
            rng.shuffle(call_order)

            def generate(profile: MemberProfile) -> dict[str, Any]:
                cell_root = allocate_opaque_cell(temp_root)
                workdir = cell_root / "workspace"
                workdir.mkdir()
                (workdir / "AGENTS.md").write_text(
                    "This is an isolated read-only response cell. Do not use tools, inspect files, or read parent directories.\n",
                    encoding="utf-8",
                )
                codex_home = prepare_codex_home(cell_root / "codex-home", source_codex_home)
                output_path = cell_root / "response.json"
                prompt = candidate_prompt(profile, challenge)
                result = run_codex_json(
                    codex=codex,
                    workdir=workdir,
                    codex_home=codex_home,
                    prompt=prompt,
                    response_path=output_path,
                    model=args.model,
                    effort=args.effort,
                    timeout_seconds=args.timeout,
                    output_schema=RESPONSE_SCHEMA,
                )
                record: dict[str, Any] = {
                    "repeat": repeat,
                    "source_profile": profile.name,
                    "source_slug": profile.slug,
                    "prompt": prompt,
                    "prompt_sha256": sha256_text(prompt),
                    "raw_response": result["response"],
                    "response_sha256": sha256_text(result["response"]),
                    "call": call_metadata(result),
                }
                if result["status"] != "OK":
                    record["validation_error"] = f"candidate call exited {result['returncode']}"
                elif result["activity"].get("tool_calls", 0):
                    record["validation_error"] = "candidate used tools in a sealed response cell"
                else:
                    try:
                        record["parsed"] = parse_candidate_response(result["response"], profiles)
                    except RecognitionError as exc:
                        record["validation_error"] = str(exc)
                return record

            records_by_name: dict[str, dict[str, Any]] = {}
            with ThreadPoolExecutor(max_workers=min(args.workers, len(profiles))) as executor:
                futures = {executor.submit(generate, profile): profile.name for profile in call_order}
                for future in as_completed(futures):
                    records_by_name[futures[future]] = future.result()
            records = [records_by_name[profile.name] for profile in profiles]
            generation_records.extend(records)
            invalid = [record for record in records if "validation_error" in record]
            if invalid:
                run_error = "sealed generation incomplete: " + "; ".join(
                    f"{record['source_profile']}: {record['validation_error']}" for record in invalid
                )
                break

            alias_profiles = list(profiles)
            rng.shuffle(alias_profiles)
            source_by_artifact: dict[str, str] = {}
            artifacts: list[dict[str, str]] = []
            for position, profile in enumerate(alias_profiles, 1):
                artifact_id = f"A-{repeat:02d}-{position:02d}"
                source_by_artifact[artifact_id] = profile.name
                record = records_by_name[profile.name]
                artifacts.append({"artifact_id": artifact_id, "response": record["parsed"]["response"]})
            freeze_payload = {
                "repeat": repeat,
                "artifact_count": len(artifacts),
                "artifacts": artifacts,
            }
            freeze_digest = sha256_text(stable_json(freeze_payload))

            reference_order = list(profiles)
            rng.shuffle(reference_order)
            identity_by_profile_id: dict[str, str] = {}
            profile_cards: list[dict[str, str]] = []
            for position, profile in enumerate(reference_order, 1):
                profile_id = f"P-{repeat:02d}-{position:02d}"
                identity_by_profile_id[profile_id] = profile.name
                profile_cards.append({"profile_id": profile_id, "behavioral_reference": profile.judge_text})
            blinded_prompt = judge_prompt(challenge, artifacts, profile_cards)
            judge_root = allocate_opaque_cell(temp_root)
            judge_workdir = judge_root / "workspace"
            judge_workdir.mkdir()
            (judge_workdir / "AGENTS.md").write_text(
                "This is an isolated read-only blind-evaluation cell. Do not use tools, inspect files, or read parent directories.\n",
                encoding="utf-8",
            )
            judge_home = prepare_codex_home(judge_root / "codex-home", source_codex_home)
            judge_output = judge_root / "judgment.json"
            judge_result = run_codex_json(
                codex=codex,
                workdir=judge_workdir,
                codex_home=judge_home,
                prompt=blinded_prompt,
                response_path=judge_output,
                model=args.judge_model,
                effort=args.judge_effort,
                timeout_seconds=args.timeout,
                output_schema=JUDGE_SCHEMA,
            )
            if judge_result["status"] != "OK":
                run_error = f"blind evaluator call exited {judge_result['returncode']}"
                judgment: dict[str, Any] | None = None
            elif judge_result["activity"].get("tool_calls", 0):
                run_error = "blind evaluator used tools"
                judgment = None
            else:
                try:
                    judgment = parse_judgment(
                        judge_result["response"],
                        source_by_artifact,
                        identity_by_profile_id,
                    )
                except RecognitionError as exc:
                    run_error = str(exc)
                    judgment = None

            repeat_record: dict[str, Any] = {
                "repeat": repeat,
                "freeze": {
                    "sha256": freeze_digest,
                    "artifact_count": len(artifacts),
                    "all_generation_calls_completed_before_judge": True,
                    "artifacts": artifacts,
                },
                "source_by_artifact": source_by_artifact,
                "identity_by_profile_id": identity_by_profile_id,
                "profile_card_order": [card["profile_id"] for card in profile_cards],
                "judge_prompt": blinded_prompt,
                "judge_prompt_sha256": sha256_text(blinded_prompt),
                "judge_raw_response": judge_result["response"],
                "judge_response_sha256": sha256_text(judge_result["response"]),
                "judge_call": call_metadata(judge_result),
                "judgment": judgment,
            }
            if judgment is not None:
                repeat_record["score"] = score_assignments(
                    source_by_artifact,
                    identity_by_profile_id,
                    judgment,
                )
            repeat_records.append(repeat_record)
            if run_error:
                break

    for record in generation_records:
        repeat_label = f"repeat-{record['repeat']:02d}"
        prompt_path = run_dir / "prompts" / "generation" / repeat_label / f"{record['source_slug']}.txt"
        prompt_path.parent.mkdir(parents=True, exist_ok=True)
        prompt_path.write_text(record.pop("prompt"), encoding="utf-8")
        raw_path = run_dir / "responses" / "generation" / repeat_label / f"{record['source_slug']}.json"
        raw_path.parent.mkdir(parents=True, exist_ok=True)
        raw_path.write_text(record.pop("raw_response"), encoding="utf-8")
        write_json(run_dir / "calls" / "generation" / repeat_label / f"{record['source_slug']}.json", record)

    for record in repeat_records:
        repeat_label = f"repeat-{record['repeat']:02d}"
        judge_prompt_path = run_dir / "prompts" / "judge" / f"{repeat_label}.txt"
        judge_prompt_path.parent.mkdir(parents=True, exist_ok=True)
        judge_prompt_path.write_text(record.pop("judge_prompt"), encoding="utf-8")
        judge_response_path = run_dir / "responses" / "judge" / f"{repeat_label}.json"
        judge_response_path.parent.mkdir(parents=True, exist_ok=True)
        judge_response_path.write_text(record.pop("judge_raw_response"), encoding="utf-8")
        write_json(run_dir / "sealed-sets" / f"{repeat_label}.json", record["freeze"])
        write_json(
            run_dir / "source-profile-assignments" / f"{repeat_label}.json",
            {
                "written_after_blind_evaluator_completed": True,
                "source_by_artifact": record["source_by_artifact"],
                "identity_by_profile_id": record["identity_by_profile_id"],
            },
        )
        write_json(run_dir / "judgments" / f"{repeat_label}.json", record)

    completed_scores = [record["score"] for record in repeat_records if "score" in record]
    summary = build_summary(completed_scores, args.repeats, run_error)
    if summary["status"] == "COMPLETE":
        summary["repeats"] = [
            {"repeat": record["repeat"], "correct": record["score"]["correct"], "total": record["score"]["total"]}
            for record in repeat_records
        ]

    profile_manifest = [
        {
            "identity": profile.name,
            "path": str(profile.path.relative_to(REPO_ROOT)),
            "canonical_sha256": profile.source_sha256,
            "sealed_projection_sha256": profile.sealed_sha256,
            "judge_projection_sha256": profile.judge_sha256,
        }
        for profile in profiles
    ]
    manifest = {
        "schema_version": "1.0.0",
        "run_id": run_dir.name,
        "created_at": started_at,
        "completed_at": utc_now(),
        "status": summary["status"],
        "design_council_version": (REPO_ROOT / "VERSION").read_text(encoding="utf-8").strip(),
        "candidate_model": args.model,
        "candidate_effort": args.effort,
        "judge_model": args.judge_model,
        "judge_effort": args.judge_effort,
        "repeats": args.repeats,
        "seed": args.seed,
        "workers": args.workers,
        "timeout_seconds": args.timeout,
        "planned_model_calls": args.repeats * 11,
        "completed_generation_calls": len(generation_records),
        "completed_judge_calls": len(repeat_records),
        "execution_controls": {
            "one_fresh_ephemeral_process_and_workspace_per_candidate": True,
            "identical_common_packet": True,
            "no_sibling_output_in_candidate_prompt": True,
            "all_ten_validated_before_freeze": True,
            "judge_started_only_after_freeze": True,
            "one_to_one_assignment": True,
            "tool_use_invalidates_call": True,
            "source_mapping_withheld_from_judge_prompt": True,
        },
        "source_hashes": {
            "runner_sha256": sha256_file(Path(__file__).resolve()),
            "challenge_sha256": sha256_file(CHALLENGE_PATH),
            "candidate_schema_sha256": sha256_file(RESPONSE_SCHEMA),
            "judge_schema_sha256": sha256_file(JUDGE_SCHEMA),
            "generator_instruction_sha256": sha256_text(GENERATOR_INSTRUCTION),
            "judge_instruction_sha256": sha256_text(JUDGE_INSTRUCTION),
            "profiles": profile_manifest,
        },
        "exact_prompt_locations": {
            "generation": "prompts/generation/",
            "judge": "prompts/judge/",
        },
        "runtime": {
            "codex_version": command_text([codex, "--version"]),
            "python_version": platform.python_version(),
            "python_implementation": platform.python_implementation(),
            "platform": platform.platform(),
        },
        "git": git_state(),
        "claim_boundary": "Results compare generated artifacts with their fictional source-profile labels. They are not human ground truth or human evidence.",
    }
    write_json(run_dir / "manifest.json", manifest)
    write_json(run_dir / "summary.json", summary)
    (run_dir / "summary.md").write_text(render_summary(summary), encoding="utf-8")
    return run_dir, summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-model", action="store_true", help="opt in to live Codex model calls")
    parser.add_argument("--require-model", action="store_true", help="treat an unavailable live run as failure")
    parser.add_argument("--dry-run", action="store_true", help="print the frozen plan and prompt hashes without model calls")
    parser.add_argument("--model", default="gpt-5.6-sol")
    parser.add_argument("--effort", default="medium")
    parser.add_argument("--judge-model", default="gpt-5.6-terra")
    parser.add_argument("--judge-effort", default="medium")
    parser.add_argument("--repeats", type=int, default=1, help="independent complete ten-member panels")
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--seed", type=int, default=20260813)
    parser.add_argument("--timeout", type=int, default=900)
    parser.add_argument("--codex", default="codex")
    parser.add_argument("--results-dir", type=Path, default=RESULTS_ROOT)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.repeats < 1 or args.repeats > 20:
        parser.error("--repeats must be between 1 and 20")
    if args.workers < 1 or args.workers > 10:
        parser.error("--workers must be between 1 and 10")
    if args.timeout < 1:
        parser.error("--timeout must be positive")
    if args.dry_run and args.run_model:
        parser.error("--dry-run and --run-model are mutually exclusive")

    try:
        profiles = load_profiles()
        challenge = load_challenge()
    except RecognitionError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    if args.dry_run:
        print(json.dumps(dry_run_payload(profiles, challenge, args), indent=2, sort_keys=True))
        return 0

    enabled = args.run_model or os.environ.get("DC_RUN_COUNCIL_RECOGNITION") == "1"
    if not enabled:
        print(
            f"SKIP: Council recognition is opt-in and would make {args.repeats * 11} model calls; "
            "pass --run-model or set DC_RUN_COUNCIL_RECOGNITION=1"
        )
        return 1 if args.require_model else 0
    codex = shutil.which(args.codex)
    if codex is None and Path(args.codex).is_file():
        codex = str(Path(args.codex).resolve())
    if codex is None:
        print("SKIP: Codex CLI is unavailable", file=sys.stderr)
        return 1 if args.require_model else 0
    missing = [path for path in (RESPONSE_SCHEMA, JUDGE_SCHEMA) if not path.is_file()]
    if missing:
        print(f"ERROR: required schema is missing: {missing[0]}", file=sys.stderr)
        return 2
    user_skills = find_user_skill_files()
    if user_skills:
        print(
            "ERROR: user-scoped skills under ~/.agents/skills could contaminate isolated calls; "
            f"detected {len(user_skills)} skill(s)",
            file=sys.stderr,
        )
        return 2
    try:
        run_dir, summary = run_live(args, codex, profiles, challenge)
    except RecognitionError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(f"Council recognition {summary['status']}: {run_dir}")
    if summary["status"] == "COMPLETE":
        print(
            f"Source-profile assignment accuracy {summary['accuracy']:.1%}; "
            f"chance baseline {summary['chance_baseline']['expected_accuracy']:.1%}."
        )
        print("This is model-based fictional-profile traceability, not human ground truth.")
        return 0
    print(summary["error"], file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
