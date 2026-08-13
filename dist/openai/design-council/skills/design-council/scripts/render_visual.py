#!/usr/bin/env python3
"""Render evidence-safe visual workshop artifacts without external dependencies."""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import os
import re
import sys
import tempfile
import textwrap
import webbrowser
from collections import Counter
from pathlib import Path
from typing import Any

from dc_core import DesignCouncilError, json_output, load_json


ARTIFACT_TYPES = {"AFFINITY_MAP", "PROCESS_MAP"}
MODES = {"INTAKE", "EMPATHIZE", "DEFINE", "IDEATE", "PROTOTYPE", "TEST"}
ROOT_KEYS = {
    "schema_version", "id", "artifact_type", "title", "summary", "summary_provenance",
    "summary_record_ids", "mode", "cycle", "limitations", "data",
}
NOTE_KEYS = {"id", "text", "provenance", "source_ids"}
CLUSTER_KEYS = {"id", "label", "description", "interpretation_provenance", "record_ids", "notes"}
AFFINITY_DATA_KEYS = {"clusters", "outliers"}
LANE_KEYS = {"id", "label"}
STEP_KEYS = {"id", "label", "detail", "lane_id", "provenance", "source_ids"}
TRANSITION_KEYS = {"id", "from_step_id", "to_step_id", "label", "provenance", "source_ids"}
PROCESS_DATA_KEYS = {"lanes", "steps", "transitions"}
PROVENANCE = {
    "OBSERVED_HUMAN_BEHAVIOR",
    "HUMAN_INTERVIEW",
    "USER_PROVIDED",
    "AUTHORITATIVE_RESEARCH",
    "RESEARCH_SUPPORTED_INFERENCE",
    "SYNTHETIC_USER",
    "SYNTHETIC_PRACTITIONER",
    "SYNTHETIC_EXPERT",
    "DESIGN_COUNCIL",
    "ASSUMPTION",
    "UNKNOWN",
}
TRACE_REQUIRED = {
    "OBSERVED_HUMAN_BEHAVIOR",
    "HUMAN_INTERVIEW",
    "AUTHORITATIVE_RESEARCH",
    "RESEARCH_SUPPORTED_INFERENCE",
    "SYNTHETIC_USER",
    "SYNTHETIC_PRACTITIONER",
    "SYNTHETIC_EXPERT",
}
PROVENANCE_STYLE = {
    "OBSERVED_HUMAN_BEHAVIOR": ("●", "Observed human behavior", "#0B63CE", "#E9F2FF"),
    "HUMAN_INTERVIEW": ("●", "Human interview", "#0B63CE", "#E9F2FF"),
    "USER_PROVIDED": ("◆", "User provided", "#35566F", "#EAF1F5"),
    "AUTHORITATIVE_RESEARCH": ("●", "Authoritative research", "#087F5B", "#E8F8F1"),
    "RESEARCH_SUPPORTED_INFERENCE": ("◐", "Research-supported inference", "#946200", "#FFF5D6"),
    "SYNTHETIC_USER": ("◇", "Synthetic user", "#7655C7", "#F2EDFF"),
    "SYNTHETIC_PRACTITIONER": ("◇", "Synthetic practitioner", "#7655C7", "#F2EDFF"),
    "SYNTHETIC_EXPERT": ("◇", "Synthetic expert", "#7655C7", "#F2EDFF"),
    "DESIGN_COUNCIL": ("◇", "Design Council", "#6457FF", "#EFEDFF"),
    "ASSUMPTION": ("△", "Assumption", "#B35200", "#FFF0E3"),
    "UNKNOWN": ("?", "Unknown", "#5F6872", "#F0F2F4"),
}

# The paper colors are intentionally independent of evidence provenance. They
# create the feel of a mixed sticky-note wall without implying that a color is
# an evidence-strength score. Provenance remains printed and separately accented.
STICKY_PALETTE = (
    ("#FFF19A", "#E8D365"),  # sun
    ("#FFD1C7", "#EAA99A"),  # coral
    ("#CFF4D8", "#9DD8AE"),  # mint
    ("#CDEBFF", "#9BCBE9"),  # sky
    ("#E5D8FF", "#BFAAE9"),  # lilac
    ("#FFE0A8", "#EDBC70"),  # apricot
)
ZONE_PALETTE = (
    ("#FFF7C7", "#E8C94E"),
    ("#FFE7E1", "#EF9B87"),
    ("#E3F8E9", "#87CF9D"),
    ("#E2F3FF", "#87C7EA"),
    ("#EFE7FF", "#BBA4E9"),
)


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise DesignCouncilError(message)


def _require_keys(value: dict[str, Any], allowed: set[str], location: str) -> None:
    extras = sorted(set(value) - allowed)
    _require(not extras, f"{location} contains unsupported properties: {', '.join(extras)}")


def _require_text(value: Any, location: str, maximum: int, *, allow_empty: bool = False) -> None:
    _require(isinstance(value, str), f"{location} must be a string")
    if not allow_empty:
        _require(bool(value.strip()), f"{location} is required")
    _require(len(value) <= maximum, f"{location} exceeds maximum length {maximum}")


def _require_local_id(value: Any, location: str) -> None:
    _require(
        isinstance(value, str) and re.fullmatch(r"[A-Za-z][A-Za-z0-9._-]*", value) is not None,
        f"{location} must match ^[A-Za-z][A-Za-z0-9._-]*$",
    )


def _records(artifact: dict[str, Any]) -> list[dict[str, Any]]:
    data = artifact.get("data", {})
    if artifact.get("artifact_type") == "AFFINITY_MAP":
        notes = [note for cluster in data.get("clusters", []) for note in cluster.get("notes", [])]
        return notes + list(data.get("outliers", []))
    return list(data.get("steps", [])) + list(data.get("transitions", []))


def _validate_record(record: Any, location: str, identifiers: set[str]) -> None:
    _require(isinstance(record, dict), f"{location} must be an object")
    identifier = record.get("id")
    _require_local_id(identifier, f"{location}.id")
    _require(identifier not in identifiers, f"duplicate artifact-local id: {identifier}")
    identifiers.add(identifier)
    provenance = record.get("provenance")
    _require(provenance in PROVENANCE, f"{location}.provenance must be an Evidence Firewall value")
    source_ids = record.get("source_ids")
    _require(
        isinstance(source_ids, list) and all(isinstance(value, str) and value.strip() for value in source_ids),
        f"{location}.source_ids must be a string array",
    )
    _require(len(source_ids) == len(set(source_ids)), f"{location}.source_ids contains duplicates")
    if provenance in TRACE_REQUIRED:
        _require(bool(source_ids), f"{location} uses {provenance} but has no source_ids")


def validate_artifact(artifact: Any) -> dict[str, Any]:
    """Perform the complete dependency-free semantic validation used by the CLI."""

    _require(isinstance(artifact, dict), "visual artifact root must be an object")
    _require_keys(artifact, ROOT_KEYS, "root")
    _require(artifact.get("schema_version") == "1.0.0", "schema_version must be 1.0.0")
    identifier = artifact.get("id")
    _require(
        isinstance(identifier, str) and re.fullmatch(r"VA-[A-Z0-9][A-Z0-9-]*", identifier) is not None,
        "id must match VA-[A-Z0-9-]+",
    )
    artifact_type = artifact.get("artifact_type")
    _require(artifact_type in ARTIFACT_TYPES, f"artifact_type must be one of {sorted(ARTIFACT_TYPES)}")
    _require_text(artifact.get("title"), "title", 200)
    _require_text(artifact.get("summary"), "summary", 1000)
    _require(artifact.get("summary_provenance") == "DESIGN_COUNCIL", "summary_provenance must be DESIGN_COUNCIL")
    summary_record_ids = artifact.get("summary_record_ids")
    _require(
        isinstance(summary_record_ids, list)
        and bool(summary_record_ids)
        and all(isinstance(value, str) and value.strip() for value in summary_record_ids),
        "summary_record_ids must be a non-empty string array",
    )
    _require(len(summary_record_ids) == len(set(summary_record_ids)), "summary_record_ids contains duplicates")
    if "mode" in artifact:
        _require(artifact["mode"] in MODES, f"mode must be one of {sorted(MODES)}")
    if "cycle" in artifact:
        _require(
            isinstance(artifact["cycle"], int) and not isinstance(artifact["cycle"], bool) and artifact["cycle"] >= 1,
            "cycle must be an integer greater than or equal to 1",
        )
    limitations = artifact.get("limitations")
    _require(
        isinstance(limitations, list)
        and all(isinstance(value, str) and value.strip() and len(value) <= 500 for value in limitations),
        "limitations must be a string array",
    )
    _require(len(limitations) == len(set(limitations)), "limitations contains duplicates")
    data = artifact.get("data")
    _require(isinstance(data, dict), "data must be an object")
    identifiers: set[str] = set()

    if artifact_type == "AFFINITY_MAP":
        _require_keys(data, AFFINITY_DATA_KEYS, "data")
        clusters = data.get("clusters")
        outliers = data.get("outliers")
        _require(isinstance(clusters, list) and bool(clusters), "AFFINITY_MAP requires at least one cluster")
        _require(isinstance(outliers, list), "AFFINITY_MAP data.outliers must be an array")
        cluster_ids: set[str] = set()
        for cluster_index, cluster in enumerate(clusters):
            location = f"data.clusters[{cluster_index}]"
            _require(isinstance(cluster, dict), f"{location} must be an object")
            _require_keys(cluster, CLUSTER_KEYS, location)
            cluster_id = cluster.get("id")
            _require_local_id(cluster_id, f"{location}.id")
            _require(cluster_id not in cluster_ids, f"duplicate cluster id: {cluster_id}")
            cluster_ids.add(cluster_id)
            _require_text(cluster.get("label"), f"{location}.label", 160)
            if "description" in cluster:
                _require_text(cluster["description"], f"{location}.description", 500, allow_empty=True)
            notes = cluster.get("notes")
            _require(isinstance(notes, list) and bool(notes), f"{location}.notes must be a non-empty array")
            cluster_note_ids: set[str] = set()
            for note_index, note in enumerate(notes):
                note_location = f"{location}.notes[{note_index}]"
                _require(isinstance(note, dict), f"{note_location} must be an object")
                _require_keys(note, NOTE_KEYS, note_location)
                _require_text(note.get("text"), f"{note_location}.text", 1000)
                _validate_record(note, note_location, identifiers)
                cluster_note_ids.add(note["id"])
            _require(
                cluster.get("interpretation_provenance") == "DESIGN_COUNCIL",
                f"{location}.interpretation_provenance must be DESIGN_COUNCIL",
            )
            record_ids = cluster.get("record_ids")
            _require(
                isinstance(record_ids, list)
                and bool(record_ids)
                and all(isinstance(value, str) and value.strip() for value in record_ids),
                f"{location}.record_ids must be a non-empty string array",
            )
            _require(len(record_ids) == len(set(record_ids)), f"{location}.record_ids contains duplicates")
            unknown_cluster_refs = sorted(set(record_ids) - cluster_note_ids)
            _require(
                not unknown_cluster_refs,
                f"{location}.record_ids references records outside this cluster: {', '.join(unknown_cluster_refs)}",
            )
            missing_cluster_refs = sorted(cluster_note_ids - set(record_ids))
            _require(
                not missing_cluster_refs,
                f"{location}.record_ids must include every clustered note: {', '.join(missing_cluster_refs)}",
            )
        for note_index, note in enumerate(outliers):
            note_location = f"data.outliers[{note_index}]"
            _require(isinstance(note, dict), f"{note_location} must be an object")
            _require_keys(note, NOTE_KEYS, note_location)
            _require_text(note.get("text"), f"{note_location}.text", 1000)
            _validate_record(note, note_location, identifiers)
    else:
        _require_keys(data, PROCESS_DATA_KEYS, "data")
        lanes = data.get("lanes")
        steps = data.get("steps")
        transitions = data.get("transitions")
        _require(isinstance(lanes, list) and bool(lanes), "PROCESS_MAP requires at least one lane")
        _require(isinstance(steps, list) and bool(steps), "PROCESS_MAP requires at least one step")
        _require(isinstance(transitions, list), "PROCESS_MAP data.transitions must be an array")
        lane_ids: set[str] = set()
        for lane_index, lane in enumerate(lanes):
            location = f"data.lanes[{lane_index}]"
            _require(isinstance(lane, dict), f"{location} must be an object")
            _require_keys(lane, LANE_KEYS, location)
            lane_id = lane.get("id")
            _require_local_id(lane_id, f"{location}.id")
            _require(lane_id not in lane_ids, f"duplicate lane id: {lane_id}")
            lane_ids.add(lane_id)
            _require_text(lane.get("label"), f"{location}.label", 160)
        step_ids: set[str] = set()
        for step_index, step in enumerate(steps):
            location = f"data.steps[{step_index}]"
            _require(isinstance(step, dict), f"{location} must be an object")
            _require_keys(step, STEP_KEYS, location)
            _require_text(step.get("label"), f"{location}.label", 160)
            _require_text(step.get("detail"), f"{location}.detail", 1000)
            _require(isinstance(step.get("lane_id"), str) and bool(step["lane_id"]), f"{location}.lane_id is required")
            _require(step.get("lane_id") in lane_ids, f"{location}.lane_id references an unknown lane")
            _validate_record(step, location, identifiers)
            step_ids.add(step["id"])
        for transition_index, transition in enumerate(transitions):
            location = f"data.transitions[{transition_index}]"
            _require(isinstance(transition, dict), f"{location} must be an object")
            _require_keys(transition, TRANSITION_KEYS, location)
            _validate_record(transition, location, identifiers)
            _require(isinstance(transition.get("from_step_id"), str) and bool(transition["from_step_id"]), f"{location}.from_step_id is required")
            _require(isinstance(transition.get("to_step_id"), str) and bool(transition["to_step_id"]), f"{location}.to_step_id is required")
            _require(transition.get("from_step_id") in step_ids, f"{location}.from_step_id references an unknown step")
            _require(transition.get("to_step_id") in step_ids, f"{location}.to_step_id references an unknown step")
            _require(transition["from_step_id"] != transition["to_step_id"], f"{location} cannot connect a step to itself")
            _require_text(transition.get("label"), f"{location}.label", 160, allow_empty=True)

    unknown_summary_refs = sorted(set(summary_record_ids) - identifiers)
    _require(
        not unknown_summary_refs,
        f"summary_record_ids references unknown artifact records: {', '.join(unknown_summary_refs)}",
    )

    records = _records(artifact)
    provenance_counts = Counter(record["provenance"] for record in records)
    source_ids = sorted({source for record in records for source in record["source_ids"]})
    warnings = []
    if not limitations:
        warnings.append("NO_LIMITATIONS_RECORDED")
    if not source_ids:
        warnings.append("NO_TRACEABLE_SOURCE_IDS")
    return {
        "valid": True,
        "artifact_type": artifact_type,
        "record_count": len(records),
        "provenance_counts": dict(sorted(provenance_counts.items())),
        "source_ids": source_ids,
        "warnings": warnings,
    }


def _xml(value: Any) -> str:
    return html.escape(str(value), quote=True)


def _markdown(value: Any) -> str:
    # Treat all supplied values as prose, never as Markdown. Collapsing line
    # breaks prevents a value from opening a new block; escaping Markdown
    # control punctuation prevents links, images, headings, lists, and HTML.
    normalized = re.sub(r"\s+", " ", str(value)).strip()
    normalized = normalized.replace("\\", "\\\\").replace("&", "&amp;").replace("<", "&lt;")
    return re.sub(r"([`*_{}\[\]()#+\-.!|>])", r"\\\1", normalized)


def _table(value: Any) -> str:
    return _markdown(value)


def _lines(value: Any, width: int, maximum: int = 5) -> list[str]:
    lines = textwrap.wrap(str(value), width=width, break_long_words=False, break_on_hyphens=False) or [""]
    if len(lines) > maximum:
        lines = lines[:maximum]
        lines[-1] = (lines[-1][:-1] + "…") if len(lines[-1]) >= width else (lines[-1] + "…")
    return lines


def _text_block(x: float, y: float, value: Any, width: int, css_class: str, line_height: int = 18, maximum: int = 5) -> tuple[str, int]:
    lines = _lines(value, width, maximum)
    tspans = [f'<tspan x="{x}" dy="{0 if index == 0 else line_height}">{_xml(line)}</tspan>' for index, line in enumerate(lines)]
    return f'<text x="{x}" y="{y}" class="{css_class}">' + "".join(tspans) + "</text>", len(lines)


def _source_label(record: dict[str, Any]) -> str:
    return ", ".join(record["source_ids"]) if record["source_ids"] else "No source ID"


def _provenance_label(provenance: str) -> str:
    mark, label, _, _ = PROVENANCE_STYLE[provenance]
    return f"{mark} {label}"


def _interpretation_label(provenance: str, record_ids: list[str]) -> str:
    return f"◇ Facilitator interpretation · {_provenance_label(provenance)} · based on {', '.join(record_ids)}"


def _stable_variant(identifier: str, modulo: int) -> int:
    """Return a deterministic visual variant without Python's salted hash()."""

    digest = hashlib.sha256(identifier.encode("utf-8")).digest()
    return int.from_bytes(digest[:4], "big") % modulo


def _svg_shell(artifact: dict[str, Any], width: int, height: int, body: str, description: str) -> str:
    summary_svg, summary_lines = _text_block(24, 86, artifact["summary"], 96, "summary-text", 18, 2)
    interpretation_y = 91 + summary_lines * 18
    interpretation_svg, _ = _text_block(
        24,
        interpretation_y,
        _interpretation_label(artifact["summary_provenance"], artifact["summary_record_ids"]),
        116,
        "meta",
        13,
        2,
    )
    return f'''<svg xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="visual-title visual-desc" viewBox="0 0 {width} {height}" width="{width}" height="{height}">
  <title id="visual-title">{_xml(artifact["title"])}</title>
  <desc id="visual-desc">{_xml(description)}</desc>
  <metadata>Design Council {_xml(artifact["artifact_type"])} {_xml(artifact["id"])}. Derived facilitation view; provenance remains attached to every record.</metadata>
  <defs>
    <filter id="paper-shadow" x="-20%" y="-20%" width="150%" height="160%">
      <feDropShadow dx="1.5" dy="5" stdDeviation="4" flood-color="#3F355F" flood-opacity="0.18"/>
    </filter>
    <filter id="soft-shadow" x="-20%" y="-20%" width="150%" height="160%">
      <feDropShadow dx="1" dy="3" stdDeviation="3" flood-color="#4A4165" flood-opacity="0.12"/>
    </filter>
  </defs>
  <style>
    text {{ font-family: ui-rounded, "Trebuchet MS", ui-sans-serif, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; fill: #17212B; }}
    .title {{ font-size: 25px; font-weight: 800; letter-spacing: 0; }}
    .subtitle {{ font-size: 13px; fill: #56606B; }}
    .summary-text {{ font-size: 13px; font-weight: 650; fill: #313B47; }}
    .cluster {{ font-size: 16px; font-weight: 700; }}
    .note-id {{ font-size: 11px; font-weight: 800; letter-spacing: .35px; }}
    .note-text {{ font-size: 13px; font-weight: 650; }}
    .meta {{ font-size: 10px; fill: #4B5662; }}
    .lane {{ font-size: 14px; font-weight: 800; }}
    .transition {{ font-size: 10px; fill: #4B5662; paint-order: stroke; stroke: #FFFFFF; stroke-width: 4px; }}
  </style>
  <rect x="0" y="0" width="{width}" height="{height}" fill="#FFFDF5"/>
  <g fill="#6457FF" opacity="0.11" aria-hidden="true">
    <circle cx="14" cy="164" r="1.2"/><circle cx="36" cy="164" r="1.2"/><circle cx="58" cy="164" r="1.2"/>
    <circle cx="14" cy="186" r="1.2"/><circle cx="36" cy="186" r="1.2"/><circle cx="58" cy="186" r="1.2"/>
  </g>
  <path d="M 24 142 C 95 135, 165 151, 238 141 S 370 135, 430 143" fill="none" stroke="#FF8C73" stroke-width="4" stroke-linecap="round" opacity="0.72"/>
  <path d="M {width - 94} 26 l 7 12 14 2 -10 10 3 14 -13 -7 -13 7 3 -14 -10 -10 14 -2 z" fill="#FFF19A" stroke="#DDAF24" stroke-width="1.4"/>
  <text x="24" y="36" class="title">{_xml(artifact["title"])}</text>
  <text x="24" y="58" class="subtitle">{_xml(artifact["id"])} · {_xml(artifact["artifact_type"])} · derived view, not new evidence</text>
  {summary_svg}
  {interpretation_svg}
{body}
</svg>
'''


def _affinity_note(note: dict[str, Any], x: int, y: int, width: int, outlier: bool = False) -> tuple[str, int]:
    text_lines = _lines(note["text"], 31, 6)
    source_lines = _lines(_source_label(note), 34, 2)
    height = max(184, 92 + len(text_lines) * 17 + len(source_lines) * 14)
    _, _, accent, _ = PROVENANCE_STYLE[note["provenance"]]
    fill, fold = STICKY_PALETTE[_stable_variant(note["id"], len(STICKY_PALETTE))]
    center_x = x + width / 2
    paper_x = x + 7
    paper_width = width - 14
    paper_right = paper_x + paper_width
    dash = ' stroke-dasharray="7 5"' if outlier else ""
    text_svg, _ = _text_block(paper_x + 16, y + 72, note["text"], 29, "note-text", 17, 6)
    source_svg, _ = _text_block(paper_x + 16, y + height - 18 - (len(source_lines) - 1) * 14, _source_label(note), 31, "meta", 14, 2)
    outlier_mark = (
        f'<path d="M {paper_x + 10} {y + 18} q 8 -10 16 0 q 8 10 16 0" fill="none" stroke="#B35200" stroke-width="2.4" stroke-linecap="round"/>'
        if outlier else ""
    )
    block = f'''  <g class="sticky-note" data-note="{_xml(note["id"])}">
    <rect x="{paper_x}" y="{y}" width="{paper_width}" height="{height}" rx="2" fill="{fill}" stroke="{accent}" stroke-width="1.5" filter="url(#paper-shadow)"{dash}/>
    <polygon class="dog-ear" points="{paper_right - 24},{y} {paper_right},{y} {paper_right},{y + 24}" fill="{fold}" stroke="{accent}" stroke-width="0.7"/>
    <rect class="tape" x="{center_x - 28}" y="{y - 7}" width="56" height="17" rx="2" fill="#FFFDF2" stroke="#D8CDA8" stroke-width="0.7" opacity="0.78"/>
    <circle cx="{paper_x + 15}" cy="{y + 26}" r="5" fill="{accent}"/>
    <text x="{paper_x + 27}" y="{y + 29}" class="note-id">{_xml(note["id"])}</text>
    <text x="{paper_x + 16}" y="{y + 49}" class="meta">{_xml(_provenance_label(note["provenance"]))}</text>
    <path d="M {paper_x + 16} {y + 57} q 30 4 62 0 t 64 0" fill="none" stroke="{accent}" stroke-width="1.3" stroke-linecap="round" opacity="0.46"/>
    {outlier_mark}
    {text_svg}
    <path d="M {paper_x + 16} {y + height - 42} q 42 -3 84 0 t 84 0" fill="none" stroke="#4B5662" stroke-width="1" stroke-dasharray="2 5" opacity="0.38"/>
    {source_svg}
  </g>'''
    return block, height


def _render_affinity_svg(artifact: dict[str, Any]) -> str:
    clusters = artifact["data"]["clusters"]
    outliers = artifact["data"]["outliers"]
    columns: list[tuple[str, str, list[dict[str, Any]], bool]] = [
        (cluster["id"], cluster["label"], cluster["notes"], False) for cluster in clusters
    ]
    if outliers:
        columns.append(("OUTLIERS", "OUTLIERS — KEEP VISIBLE", outliers, True))
    column_width = 276
    gap = 24
    margin = 24
    header_y = 170
    note_y = 347
    widths = margin * 2 + len(columns) * column_width + max(0, len(columns) - 1) * gap
    rendered_columns: list[str] = []
    maximum_bottom = 220
    for column_index, (column_id, label, notes, is_outlier) in enumerate(columns):
        x = margin + column_index * (column_width + gap)
        zone_fill, zone_stroke = (("#FFF0E0", "#D97706") if is_outlier else ZONE_PALETTE[column_index % len(ZONE_PALETTE)])
        note_metrics = []
        y_cursor = note_y
        for note in notes:
            text_lines = _lines(note["text"], 31, 6)
            source_lines = _lines(_source_label(note), 34, 2)
            note_height = max(184, 92 + len(text_lines) * 17 + len(source_lines) * 14)
            note_metrics.append((note, y_cursor, note_height))
            y_cursor += note_height + 22
        zone_height = max(330, y_cursor - header_y + 4)
        rendered_columns.append(
            f'  <rect class="cluster-zone" x="{x - 7}" y="{header_y - 13}" width="{column_width + 14}" height="{zone_height}" rx="28" fill="{zone_fill}" fill-opacity="0.58" stroke="{zone_stroke}" stroke-width="2" stroke-dasharray="9 8"/>'
        )
        rendered_columns.append(
            f'  <path d="M {x + 18} {header_y - 1} q 42 -14 84 0 t 84 0 t 66 0" fill="none" stroke="{zone_stroke}" stroke-width="3" stroke-linecap="round" opacity="0.58"/>'
        )
        rendered_columns.append(
            f'  <rect x="{x + 8}" y="{header_y + 5}" width="{column_width - 16}" height="151" rx="16" fill="#FFFFFF" stroke="{zone_stroke}" filter="url(#soft-shadow)"/>'
        )
        rendered_columns.append(
            f'  <rect x="{x + column_width / 2 - 31}" y="{header_y - 4}" width="62" height="17" rx="3" fill="#FFF7D4" stroke="#D9C988" opacity="0.84"/>'
        )
        rendered_columns.append(f'  <text x="{x + 21}" y="{header_y + 29}" class="meta">{_xml(column_id)} · {len(notes)} record(s)</text>')
        label_svg, _ = _text_block(x + 21, header_y + 55, label, 22, "cluster", 17, 2)
        rendered_columns.append(label_svg)
        if not is_outlier:
            cluster = clusters[column_index]
            description = cluster.get("description", "")
            if description:
                description_svg, _ = _text_block(x + 21, header_y + 90, description, 38, "meta", 13, 2)
                rendered_columns.append(description_svg)
            interpretation_svg, _ = _text_block(
                x + 21,
                header_y + 128,
                _interpretation_label(cluster["interpretation_provenance"], cluster["record_ids"]),
                38,
                "meta",
                13,
                2,
            )
            rendered_columns.append(interpretation_svg)
        else:
            outlier_ids = [note["id"] for note in notes]
            interpretation_svg, _ = _text_block(
                x + 21,
                header_y + 128,
                "Exception set · supplied records · " + ", ".join(outlier_ids),
                38,
                "meta",
                13,
                2,
            )
            rendered_columns.append(interpretation_svg)
        for note, y, _ in note_metrics:
            note_svg, height = _affinity_note(note, x, y, column_width, is_outlier)
            rendered_columns.append(note_svg)
        doodle_x = x + column_width - 30
        doodle_y = header_y + zone_height - 24
        rendered_columns.append(
            f'  <path d="M {doodle_x - 17} {doodle_y} q 8 -12 16 0 q 8 12 16 0" fill="none" stroke="{zone_stroke}" stroke-width="2.4" stroke-linecap="round" opacity="0.7"/>'
        )
        maximum_bottom = max(maximum_bottom, header_y + zone_height)
    width = max(920, widths)
    height = max(500, maximum_bottom + 24)
    description = f"Affinity map with {len(clusters)} clusters and {len(outliers)} preserved outliers. Every note shows provenance and source IDs."
    return _svg_shell(artifact, width, height, "\n".join(rendered_columns), description)


def _render_process_svg(artifact: dict[str, Any]) -> str:
    data = artifact["data"]
    lanes = data["lanes"]
    steps = data["steps"]
    lane_index = {lane["id"]: index for index, lane in enumerate(lanes)}
    card_width = 216
    card_height = 190
    left = 204
    top = 170
    x_gap = 330
    lane_height = 250
    width = max(960, left + len(steps) * x_gap + 30)
    height = max(440, top + len(lanes) * lane_height + 34)
    positions = {
        step["id"]: (left + index * x_gap, top + lane_index[step["lane_id"]] * lane_height + 28)
        for index, step in enumerate(steps)
    }
    body: list[str] = []
    for index, lane in enumerate(lanes):
        y = top + index * lane_height
        fill, lane_stroke = ZONE_PALETTE[index % len(ZONE_PALETTE)]
        body.append(f'  <rect class="process-lane" x="18" y="{y}" width="{width - 36}" height="{lane_height - 10}" rx="26" fill="{fill}" fill-opacity="0.48" stroke="{lane_stroke}" stroke-width="1.7" stroke-dasharray="10 8"/>')
        body.append(f'  <circle cx="54" cy="{y + 45}" r="24" fill="#FFFFFF" stroke="{lane_stroke}" stroke-width="2" filter="url(#soft-shadow)"/>')
        body.append(f'  <text x="54" y="{y + 51}" text-anchor="middle" class="lane">{index + 1}</text>')
        lane_svg, _ = _text_block(34, y + 92, lane["label"], 16, "lane", 17, 3)
        body.append(lane_svg)
        body.append(f'  <text x="34" y="{y + 152}" class="meta">{_xml(lane["id"])}</text>')
        body.append(f'  <path d="M 34 {y + 171} q 24 -8 48 0 t 48 0" fill="none" stroke="{lane_stroke}" stroke-width="2.5" stroke-linecap="round" opacity="0.65"/>')
    for transition in data["transitions"]:
        source_x, source_y = positions[transition["from_step_id"]]
        target_x, target_y = positions[transition["to_step_id"]]
        x1, y1 = source_x + card_width, source_y + card_height / 2
        x2, y2 = target_x, target_y + card_height / 2
        segments: list[str]
        if x2 > x1:
            control = (x1 + x2) / 2
            vertical_y = min(y1, y2)
            vertical_height = max(4, abs(y2 - y1))
            segments = [
                f'<rect x="{x1}" y="{y1 - 2}" width="{control - x1 + 2}" height="4" rx="2"/>',
                f'<rect x="{control - 2}" y="{vertical_y}" width="4" height="{vertical_height}" rx="2"/>',
                f'<rect x="{control}" y="{y2 - 2}" width="{max(1, x2 - 12 - control)}" height="4" rx="2"/>',
            ]
            label_x, label_y = control, min(y1, y2) + abs(y2 - y1) / 2 - 8
        else:
            arch_y = min(y1, y2) - 54
            segments = [
                f'<rect x="{x1}" y="{y1 - 2}" width="42" height="4" rx="2"/>',
                f'<rect x="{x1 + 40}" y="{arch_y}" width="4" height="{max(4, y1 - arch_y)}" rx="2"/>',
                f'<rect x="{x2 - 42}" y="{arch_y}" width="{max(4, x1 - x2 + 84)}" height="4" rx="2"/>',
                f'<rect x="{x2 - 44}" y="{arch_y}" width="4" height="{max(4, y2 - arch_y)}" rx="2"/>',
                f'<rect x="{x2 - 42}" y="{y2 - 2}" width="30" height="4" rx="2"/>',
            ]
            label_x, label_y = (x1 + x2) / 2, arch_y - 6
        body.append(
            f'  <g class="flow-echo" aria-hidden="true" fill="#DCD6FF">'
            + "".join(segment.replace('height="4"', 'height="10"').replace('width="4"', 'width="10"') for segment in segments)
            + "</g>"
        )
        body.append(
            f'  <g class="flow-path" data-transition="{_xml(transition["id"])}" fill="#6457FF">'
            + "".join(segments)
            + "</g>"
        )
        body.append(
            f'  <polygon points="{x2 - 12},{y2 - 7} {x2},{y2} {x2 - 12},{y2 + 7}" fill="#6457FF"/>'
        )
        visible_label = transition["label"] or "transition"
        label_width = min(210, max(92, len(visible_label) * 6.4))
        body.append(f'  <rect x="{label_x - label_width / 2}" y="{label_y - 15}" width="{label_width}" height="35" rx="12" fill="#FFFFFF" stroke="#C8C0FF" filter="url(#soft-shadow)"/>')
        body.append(f'  <text x="{label_x}" y="{label_y}" text-anchor="middle" class="transition">{_xml(visible_label)}</text>')
        body.append(
            f'  <text x="{label_x}" y="{label_y + 14}" text-anchor="middle" class="transition">'
            f'{_xml(transition["id"])} · {_xml(_provenance_label(transition["provenance"]))} · {_xml(_source_label(transition))}</text>'
        )
    for step in steps:
        x, y = positions[step["id"]]
        _, _, accent, _ = PROVENANCE_STYLE[step["provenance"]]
        fill, fold = STICKY_PALETTE[_stable_variant(step["id"], len(STICKY_PALETTE))]
        center_x = x + card_width / 2
        label_svg, _ = _text_block(x + 14, y + 70, step["label"], 23, "note-text", 16, 2)
        detail_svg, _ = _text_block(x + 14, y + 116, step["detail"], 29, "meta", 14, 3)
        source_svg, _ = _text_block(x + 14, y + 170, _source_label(step), 31, "meta", 13, 2)
        body.extend([
            f'  <g class="process-card" data-step="{_xml(step["id"])}">',
            f'  <rect x="{x}" y="{y}" width="{card_width}" height="{card_height}" rx="3" fill="{fill}" stroke="{accent}" stroke-width="1.5" filter="url(#paper-shadow)"/>',
            f'  <polygon class="dog-ear" points="{x + card_width - 24},{y} {x + card_width},{y} {x + card_width},{y + 24}" fill="{fold}" stroke="{accent}" stroke-width="0.7"/>',
            f'  <rect class="tape" x="{center_x - 25}" y="{y - 7}" width="50" height="16" rx="2" fill="#FFFDF2" stroke="#D8CDA8" stroke-width="0.7" opacity="0.78"/>',
            f'  <circle cx="{x + 16}" cy="{y + 23}" r="5" fill="{accent}"/>',
            f'  <text x="{x + 29}" y="{y + 26}" class="note-id">{_xml(step["id"])}</text>',
            f'  <text x="{x + 14}" y="{y + 43}" class="meta">{_xml(_provenance_label(step["provenance"]))}</text>',
            f'  <path d="M {x + 14} {y + 53} q 36 4 72 0 t 72 0" fill="none" stroke="{accent}" stroke-width="1.3" stroke-linecap="round" opacity="0.46"/>',
            label_svg,
            detail_svg,
            f'  <path d="M {x + 14} {y + 151} q 42 -3 84 0 t 84 0" fill="none" stroke="#4B5662" stroke-width="1" stroke-dasharray="2 5" opacity="0.38"/>',
            source_svg,
            '  </g>',
        ])
    body.append(f'  <path d="M {width - 134} {height - 44} q 14 -20 28 0 q 14 20 28 0 q 14 -20 28 0" fill="none" stroke="#FF8C73" stroke-width="3" stroke-linecap="round" opacity="0.72"/>')
    description = f"Process map with {len(lanes)} lanes, {len(steps)} steps, and {len(data['transitions'])} evidence-linked transitions."
    return _svg_shell(artifact, width, height, "\n".join(body), description)


def _used_provenance(artifact: dict[str, Any]) -> list[str]:
    return sorted({record["provenance"] for record in _records(artifact)})


def _html_fallback(artifact: dict[str, Any]) -> str:
    data = artifact["data"]
    sections: list[str] = []
    if artifact["artifact_type"] == "AFFINITY_MAP":
        for cluster in data["clusters"]:
            notes = "".join(
                f'<li><strong>{_xml(note["id"])}</strong> — {_xml(note["text"])} '
                f'<span class="record-meta">{_xml(_provenance_label(note["provenance"]))}; sources: {_xml(_source_label(note))}</span></li>'
                for note in cluster["notes"]
            )
            description = f'<p>{_xml(cluster["description"])}</p>' if cluster.get("description") else ""
            interpretation = _interpretation_label(cluster["interpretation_provenance"], cluster["record_ids"])
            sections.append(
                f'<section><h3>{_xml(cluster["label"])}</h3>{description}'
                f'<p class="interpretation">{_xml(interpretation)}</p><ul>{notes}</ul></section>'
            )
        if data["outliers"]:
            notes = "".join(
                f'<li><strong>{_xml(note["id"])}</strong> — {_xml(note["text"])} '
                f'<span class="record-meta">{_xml(_provenance_label(note["provenance"]))}; sources: {_xml(_source_label(note))}</span></li>'
                for note in data["outliers"]
            )
            sections.append(f'<section><h3>Outliers — keep visible</h3><ul>{notes}</ul></section>')
    else:
        lane_names = {lane["id"]: lane["label"] for lane in data["lanes"]}
        rows = "".join(
            f'<tr><td>{_xml(step["id"])}</td><td>{_xml(lane_names[step["lane_id"]])}</td><td>{_xml(step["label"])}</td>'
            f'<td>{_xml(step["detail"])}</td><td>{_xml(_provenance_label(step["provenance"]))}</td><td>{_xml(_source_label(step))}</td></tr>'
            for step in data["steps"]
        )
        transitions = "".join(
            f'<li><strong>{_xml(item["from_step_id"])} → {_xml(item["to_step_id"])}</strong> — {_xml(item["label"] or "unlabeled transition")} '
            f'<span class="record-meta">{_xml(_provenance_label(item["provenance"]))}; sources: {_xml(_source_label(item))}</span></li>'
            for item in data["transitions"]
        )
        sections.append(
            '<section><h3>Steps</h3><div class="table-scroll"><table><thead><tr><th>ID</th><th>Lane</th><th>Step</th><th>Detail</th><th>Provenance</th><th>Sources</th></tr></thead>'
            f'<tbody>{rows}</tbody></table></div></section><section><h3>Transitions</h3><ul>{transitions or "<li>None recorded.</li>"}</ul></section>'
        )
    return "".join(sections)


def _render_html(artifact: dict[str, Any], svg: str) -> str:
    legend = "".join(
        f'<li><span class="swatch" style="background:{PROVENANCE_STYLE[value][2]}"></span>{_xml(_provenance_label(value))}</li>'
        for value in _used_provenance(artifact)
    )
    limitations = "".join(f"<li>{_xml(value)}</li>" for value in artifact["limitations"]) or "<li>None recorded; verify that this is intentional.</li>"
    mode = f'<span class="chip">{_xml(artifact["mode"])}</span>' if artifact.get("mode") else ""
    cycle = f'<span class="chip">Cycle {_xml(artifact["cycle"])}</span>' if artifact.get("cycle") else ""
    summary_interpretation = _interpretation_label(artifact["summary_provenance"], artifact["summary_record_ids"])
    return f'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; img-src data:">
  <title>{_xml(artifact["title"])}</title>
  <style>
    :root {{ color-scheme: light; font-family: ui-rounded, "Trebuchet MS", ui-sans-serif, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; color: #17212B; background: #FFF9EC; }}
    body {{ margin: 0; background: radial-gradient(circle at 10% 8%, #FFE7DE 0 7%, transparent 26%), radial-gradient(circle at 92% 14%, #E5DCFF 0 8%, transparent 27%), #FFF9EC; }}
    main {{ max-width: 1440px; margin: 0 auto; padding: 28px; }}
    header, .panel {{ background: rgba(255,255,255,.96); border: 1px solid #DDD6EE; border-radius: 22px; box-shadow: 0 10px 0 rgba(100,87,255,.045), 0 18px 45px rgba(55, 44, 90, .08); }}
    header {{ position: relative; overflow: hidden; padding: 29px 32px 27px; border-top: 7px solid #6457FF; background: linear-gradient(115deg, #FFFFFF 0 66%, #F3EEFF 66% 100%); }}
    header::before {{ content: ""; position: absolute; width: 170px; height: 170px; right: 42px; top: -112px; border: 18px solid #FFD454; border-radius: 50%; transform: rotate(-8deg); }}
    header::after {{ content: "✦"; position: absolute; right: 30px; bottom: 7px; color: #FF8066; font-size: 2.4rem; transform: rotate(12deg); }}
    header > * {{ position: relative; z-index: 1; }}
    h1 {{ margin: 0 0 8px; font-size: clamp(1.9rem, 4vw, 2.7rem); letter-spacing: -.035em; line-height: 1.02; }} h2 {{ margin-top: 0; }}
    .eyebrow {{ color: #6457FF; font-size: .78rem; font-weight: 800; letter-spacing: .08em; text-transform: uppercase; }}
    .summary {{ max-width: 78ch; color: #485462; line-height: 1.5; }} .chips {{ display: flex; gap: 8px; flex-wrap: wrap; margin-top: 14px; }}
    .chip {{ padding: 6px 11px; border: 1px solid #CFC7FF; border-radius: 999px; background: #EFEDFF; color: #4438C8; font-size: .78rem; font-weight: 800; transform: rotate(-.35deg); }}
    .chip:nth-child(even) {{ background: #FFF2B8; border-color: #EBD676; color: #6D5900; transform: rotate(.55deg); }}
    .notice {{ margin-top: 17px; padding: 11px 14px; border: 1px dashed #D5B33A; border-left: 5px solid #E7B824; border-radius: 4px 13px 13px 4px; background: #FFF7CC; color: #594700; transform: rotate(-.15deg); }}
    .interpretation {{ color: #51459E; font-size: .82rem; font-weight: 700; line-height: 1.4; }}
    .panel {{ margin-top: 22px; padding: 22px; }} .visual {{ overflow-x: auto; background: #FFFDF5; border: 2px dashed #CFC7FF; }} .visual svg {{ min-width: 900px; max-width: none; height: auto; display: block; }}
    .legend {{ display: flex; flex-wrap: wrap; gap: 10px 18px; padding: 0; list-style: none; }} .swatch {{ display: inline-block; width: 10px; height: 10px; border-radius: 3px; margin-right: 7px; }}
    .record-meta {{ color: #5A6470; font-size: .9em; }} li {{ margin: .45rem 0; line-height: 1.45; }}
    table {{ width: 100%; border-collapse: collapse; }} th, td {{ text-align: left; padding: 9px; border-bottom: 1px solid #E3E5EC; vertical-align: top; }} th {{ background: #F6F7FA; }} .table-scroll {{ overflow-x: auto; }}
    footer {{ color: #65707B; font-size: .82rem; margin: 24px 4px; }}
    @media (max-width: 700px) {{ main {{ padding: 14px; }} header, .panel {{ border-radius: 10px; }} }}
    @media print {{ body {{ background: #FFF; }} header, .panel {{ box-shadow: none; break-inside: avoid; }} }}
  </style>
</head>
<body>
<main>
  <header>
    <div class="eyebrow">◇ Design Council · Visual Workbench</div>
    <h1>{_xml(artifact["title"])}</h1>
    <p class="summary">{_xml(artifact["summary"])}</p>
    <p class="interpretation">{_xml(summary_interpretation)}</p>
    <div class="chips"><span class="chip">{_xml(artifact["id"])}</span><span class="chip">{_xml(artifact["artifact_type"])}</span>{mode}{cycle}</div>
    <div class="notice"><strong>Evidence note:</strong> this visual reorganizes supplied records. It does not create evidence or measure prevalence.</div>
  </header>
  <section class="panel visual" aria-label="Graphical workshop artifact">{svg}</section>
  <section class="panel" aria-labelledby="text-view-heading"><h2 id="text-view-heading">Complete text view</h2>{_html_fallback(artifact)}</section>
  <section class="panel"><h2>Provenance legend</h2><ul class="legend">{legend}</ul><h2>Limitations</h2><ul>{limitations}</ul></section>
  <footer>Generated locally by Design Council Visual Workbench. No remote assets, scripts, or analytics.</footer>
</main>
</body>
</html>
'''


def _render_markdown(artifact: dict[str, Any], svg_name: str) -> str:
    lines = [
        f'# ◇ {_markdown(artifact["title"])}',
        "",
        f'`{_markdown(artifact["id"])}` · `{_markdown(artifact["artifact_type"])}`',
        "",
        f'> {_markdown(artifact["summary"])}',
        "",
        f'> {_markdown(_interpretation_label(artifact["summary_provenance"], artifact["summary_record_ids"]))}',
        "",
        # svg_name is generated by artifact_stem() and contains only a local,
        # renderer-controlled filename. Never place supplied text in this target.
        f'![{_markdown(artifact["title"])}]({svg_name})',
        "",
        "> **Evidence note:** This visual reorganizes supplied records. It does not create evidence or measure prevalence.",
        "",
        "## Complete text view",
        "",
    ]
    data = artifact["data"]
    if artifact["artifact_type"] == "AFFINITY_MAP":
        for cluster in data["clusters"]:
            lines.extend([f'### {_markdown(cluster["label"])} · `{_markdown(cluster["id"])}`', ""])
            if cluster.get("description"):
                lines.extend([f'_{_markdown(cluster["description"])}_', ""])
            lines.extend(
                [
                    f'_{_markdown(_interpretation_label(cluster["interpretation_provenance"], cluster["record_ids"]))}_',
                    "",
                ]
            )
            for note in cluster["notes"]:
                lines.append(f'- **{_markdown(note["id"])}** — {_markdown(note["text"])}  ')
                lines.append(f'  {_markdown(_provenance_label(note["provenance"]))} · Sources: {_markdown(_source_label(note))}')
            lines.append("")
        if data["outliers"]:
            lines.extend(["### Outliers — keep visible", ""])
            for note in data["outliers"]:
                lines.append(f'- **{_markdown(note["id"])}** — {_markdown(note["text"])}  ')
                lines.append(f'  {_markdown(_provenance_label(note["provenance"]))} · Sources: {_markdown(_source_label(note))}')
            lines.append("")
    else:
        lane_names = {lane["id"]: lane["label"] for lane in data["lanes"]}
        lines.extend([
            "| ID | Lane | Step | Detail | Provenance | Sources |",
            "|---|---|---|---|---|---|",
        ])
        for step in data["steps"]:
            lines.append(
                f'| {_table(step["id"])} | {_table(lane_names[step["lane_id"]])} | {_table(step["label"])} | '
                f'{_table(step["detail"])} | {_table(_provenance_label(step["provenance"]))} | {_table(_source_label(step))} |'
            )
        lines.extend(["", "### Transitions", ""])
        if data["transitions"]:
            for item in data["transitions"]:
                lines.append(
                    f'- **{_markdown(item["from_step_id"])} → {_markdown(item["to_step_id"])}** — '
                    f'{_markdown(item["label"] or "unlabeled transition")}  '
                )
                lines.append(f'  {_markdown(_provenance_label(item["provenance"]))} · Sources: {_markdown(_source_label(item))}')
        else:
            lines.append("- None recorded.")
        lines.append("")
    lines.extend(["## Provenance legend", ""])
    for value in _used_provenance(artifact):
        lines.append(f'- `{value}` — {_markdown(_provenance_label(value))}')
    lines.extend(["", "## Limitations", ""])
    lines.extend(f"- {_markdown(value)}" for value in artifact["limitations"])
    if not artifact["limitations"]:
        lines.append("- None recorded; verify that this is intentional.")
    lines.extend(["", "_Generated locally by Design Council Visual Workbench._", ""])
    return "\n".join(lines)


def artifact_stem(artifact: dict[str, Any]) -> str:
    raw = f'{artifact["id"]}-{artifact["title"]}'.lower()
    return re.sub(r"[^a-z0-9]+", "-", raw).strip("-")[:96]


def render_artifact(artifact: dict[str, Any]) -> dict[str, Any]:
    validation = validate_artifact(artifact)
    stem = artifact_stem(artifact)
    source_json = json.dumps(artifact, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    input_sha256 = hashlib.sha256(source_json.encode("utf-8")).hexdigest()
    svg = _render_affinity_svg(artifact) if artifact["artifact_type"] == "AFFINITY_MAP" else _render_process_svg(artifact)
    return {
        "artifact_id": artifact["id"],
        "artifact_type": artifact["artifact_type"],
        "stem": stem,
        "source_json": json.dumps(artifact, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        "svg": svg,
        "html": _render_html(artifact, svg),
        "markdown": _render_markdown(artifact, f"{stem}.svg"),
        "record_count": validation["record_count"],
        "provenance_counts": validation["provenance_counts"],
        "source_ids": validation["source_ids"],
        "input_sha256": input_sha256,
        "warnings": validation["warnings"],
    }


def _write_atomic(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(value)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except Exception:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


def write_artifact(rendered: dict[str, Any], output_dir: str | Path) -> dict[str, str]:
    target = Path(output_dir).resolve()
    paths = {
        "source": target / "source.json",
        "html": target / f'{rendered["stem"]}.html',
        "svg": target / f'{rendered["stem"]}.svg',
        "markdown": target / f'{rendered["stem"]}.md',
        "manifest": target / "manifest.json",
    }
    existing = [path for path in paths.values() if path.exists()]
    if existing:
        raise DesignCouncilError(
            "Refusing to overwrite immutable visual artifact output; use a new VA- ID: "
            + ", ".join(str(path) for path in existing)
        )
    _write_atomic(paths["source"], rendered["source_json"])
    _write_atomic(paths["svg"], rendered["svg"])
    _write_atomic(paths["html"], rendered["html"])
    _write_atomic(paths["markdown"], rendered["markdown"])
    file_content = {
        "source": rendered["source_json"],
        "html": rendered["html"],
        "svg": rendered["svg"],
        "markdown": rendered["markdown"],
    }
    manifest = {
        "schema_version": "1.0.0",
        "artifact_id": rendered["artifact_id"],
        "artifact_type": rendered["artifact_type"],
        "input_sha256": rendered["input_sha256"],
        "record_count": rendered["record_count"],
        "provenance_counts": rendered["provenance_counts"],
        "source_ids": rendered["source_ids"],
        "files": {key: path.name for key, path in paths.items() if key != "manifest"},
        "file_sha256": {
            key: hashlib.sha256(value.encode("utf-8")).hexdigest()
            for key, value in sorted(file_content.items())
        },
        "warnings": rendered["warnings"],
        "note": "Derived visual only; canonical evidence and project history were not changed.",
    }
    _write_atomic(paths["manifest"], json.dumps(manifest, indent=2, ensure_ascii=False, sort_keys=True) + "\n")
    # Rendered views are historical snapshots. Make the completed set read-only
    # where the host supports POSIX mode bits; future arrangements use a new ID.
    for path in paths.values():
        try:
            path.chmod(0o444)
        except OSError:
            pass
    return {key: str(path) for key, path in paths.items()}


def open_artifact(path: str | Path) -> bool:
    return bool(webbrowser.open(Path(path).resolve().as_uri(), new=2))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", help="visual-artifact JSON file")
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--output-dir", help="default: <project>/.design-council/artifacts/<artifact-id>")
    parser.add_argument("--open", action="store_true", help="open the local HTML workbench after rendering")
    args = parser.parse_args()
    try:
        artifact = load_json(args.input)
        rendered = render_artifact(artifact)
        output_dir = (
            Path(args.output_dir)
            if args.output_dir
            else Path(args.project_root) / ".design-council" / "artifacts" / str(artifact["id"])
        )
        paths = write_artifact(rendered, output_dir)
        browser_opened = open_artifact(paths["html"]) if args.open else False
        json_output({
            "artifact_id": rendered["artifact_id"],
            "artifact_type": rendered["artifact_type"],
            "record_count": rendered["record_count"],
            "provenance_counts": rendered["provenance_counts"],
            "source_count": len(rendered["source_ids"]),
            "input_sha256": rendered["input_sha256"],
            "files": paths,
            "browser_opened": browser_opened,
            "warnings": rendered["warnings"],
            "note": "Derived visual only; canonical evidence and project history were not changed.",
        })
    except (DesignCouncilError, OSError) as exc:
        print(f"Design Council error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
