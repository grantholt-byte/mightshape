#!/usr/bin/env python3
"""Small, inspectable idea clustering that preserves outliers and territories."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from typing import Any

from dc_core import DesignCouncilError, json_output, load_json


STOP = {"the", "a", "an", "and", "or", "of", "to", "for", "with", "without", "in", "on", "by", "is", "be", "that", "this", "it", "from", "as", "at", "we", "user", "users", "make", "use"}
TERRITORIES = {"EXPECTED", "ADJACENT", "BEHAVIORAL", "SYSTEMIC", "RADICAL"}


def tokens(text: str) -> set[str]:
    return {word for word in re.findall(r"[a-z][a-z0-9-]{2,}", text.lower()) if word not in STOP}


def similarity(a: set[str], b: set[str]) -> float:
    if not (a or b):
        return 0.0
    overlap = len(a & b)
    jaccard = overlap / len(a | b)
    overlap_coefficient = overlap / min(len(a), len(b)) if a and b else 0.0
    return max(jaccard, 0.75 * overlap_coefficient)


def _normalize(ideas: Any) -> list[dict[str, Any]]:
    if isinstance(ideas, dict):
        ideas = ideas.get("ideas", [])
    if not isinstance(ideas, list) or not ideas:
        raise DesignCouncilError("input requires a non-empty ideas array")
    output = []
    for index, item in enumerate(ideas, 1):
        if isinstance(item, str):
            record = {"id": f"IDEA-{index:03d}", "statement": item, "territory": "ADJACENT"}
        elif isinstance(item, dict):
            record = dict(item)
            record.setdefault("id", f"IDEA-{index:03d}")
            record.setdefault("statement", record.get("idea", ""))
            record.setdefault("territory", "ADJACENT")
        else:
            raise DesignCouncilError(f"idea {index} must be a string or object")
        if not str(record["statement"]).strip():
            raise DesignCouncilError(f"idea {record['id']} has no statement")
        record["territory"] = str(record["territory"]).upper()
        if record["territory"] not in TERRITORIES:
            raise DesignCouncilError(f"idea {record['id']} has invalid territory {record['territory']}")
        output.append(record)
    return output


def cluster_ideas(ideas: Any, threshold: float = 0.28, minimum_cluster_size: int = 2) -> dict[str, Any]:
    if not 0 <= threshold <= 1:
        raise DesignCouncilError("threshold must be between 0 and 1")
    normalized = _normalize(ideas)
    token_sets = [tokens(str(item["statement"])) for item in normalized]
    parent = list(range(len(normalized)))

    def find(index: int) -> int:
        while parent[index] != index:
            parent[index] = parent[parent[index]]
            index = parent[index]
        return index

    def union(left: int, right: int) -> None:
        left_root, right_root = find(left), find(right)
        if left_root != right_root:
            parent[right_root] = left_root

    for left in range(len(normalized)):
        for right in range(left + 1, len(normalized)):
            lexical = similarity(token_sets[left], token_sets[right])
            mechanism_match = normalized[left].get("mechanism") and normalized[left].get("mechanism") == normalized[right].get("mechanism")
            if lexical >= threshold or mechanism_match:
                union(left, right)

    groups: dict[int, list[int]] = {}
    for index in range(len(normalized)):
        groups.setdefault(find(index), []).append(index)
    clusters = []
    outliers = []
    cluster_number = 0
    for indexes in sorted(groups.values(), key=lambda values: min(values)):
        if len(indexes) < minimum_cluster_size:
            outliers.extend(normalized[index] for index in indexes)
            continue
        cluster_number += 1
        common = Counter(word for index in indexes for word in token_sets[index])
        label_words = [word for word, _ in common.most_common(3)]
        clusters.append({
            "id": f"CLUSTER-{cluster_number:03d}",
            "label": " / ".join(label_words).title() if label_words else f"Concept territory {cluster_number}",
            "idea_ids": [normalized[index]["id"] for index in indexes],
            "territories": sorted({normalized[index]["territory"] for index in indexes}),
            "representative": normalized[indexes[0]]["statement"],
        })
    for item in outliers:
        item["is_outlier"] = True
    represented = {item["territory"] for item in normalized}
    missing = sorted(TERRITORIES - represented)
    return {
        "clusters": clusters,
        "outliers": outliers,
        "territory_coverage": {
            "represented": sorted(represented),
            "missing": missing,
            "passes_substantial_divergence": not missing,
        },
        "input_count": len(normalized),
        "clustered_count": sum(len(cluster["idea_ids"]) for cluster in clusters),
        "outlier_count": len(outliers),
        "warning": "IDEATION_TERRITORY_GAP" if missing else None,
        "note": "Outliers are preserved; lexical grouping is a facilitation aid, not semantic truth.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Cluster ideas without discarding outliers")
    parser.add_argument("input", nargs="?", help="JSON file; stdin when omitted")
    parser.add_argument("--threshold", type=float, default=0.28)
    parser.add_argument("--minimum-cluster-size", type=int, default=2)
    args = parser.parse_args()
    try:
        value = load_json(args.input) if args.input else json.load(sys.stdin)
        json_output(cluster_ideas(value, args.threshold, args.minimum_cluster_size))
    except (DesignCouncilError, json.JSONDecodeError) as exc:
        print(f"Design Council error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
