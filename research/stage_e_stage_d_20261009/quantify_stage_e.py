#!/usr/bin/env python3
"""Recompute Stage E derived observability statistics from frozen JSON only."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import random
import struct
import zlib
from collections import defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
SEED = 20260830
N_BOOT = 2000

INPUTS = {
    "checkpoint_discrimination_tables_v2": "logs/graph/eval/checkpoint_discrimination_tables_v2.json",
    "t2_visibility_sensitivity": "logs/graph/eval/t2_visibility_sensitivity.json",
    "d1_mutant_validity_audit": "logs/graph/eval/d1_mutant_validity_audit.json",
    "t1_eval_baseline_comparison": "logs/graph/eval/t1_eval_baseline_comparison.json",
    "d3_matched_fpr_stage_a": "logs/graph/eval/d3_matched_fpr_stage_a.json",
    "d2_cross_matcher_det": "logs/graph/eval/d2_cross_matcher_det.json",
    "t4_pso_fair_comparison": "logs/graph/eval/t4_pso_fair_comparison.json",
}

FAMILY_ORDER = [
    "alias_variant",
    "date_variant",
    "mixed_lang",
    "ocr_similar",
    "prefix_noise",
    "unit_suffix",
]

PROTOCOLS = {
    "end_to_end": ("E1.1_detected", "E1.1_end_to_end"),
    "flat": ("E1.2_detected", "E1.2_flat"),
    "hierarchical_expert": ("E1.3_detected", "E1.3_hier_expert"),
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load(relative: str) -> Any:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )


def ratio(numerator: int, denominator: int) -> float | None:
    return None if denominator == 0 else numerator / denominator


def percentile(sorted_values: list[float], q: float) -> float:
    if not sorted_values:
        raise ValueError("empty percentile")
    position = (len(sorted_values) - 1) * q
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return sorted_values[lower]
    weight = position - lower
    return sorted_values[lower] * (1 - weight) + sorted_values[upper] * weight


def ci95(values: list[float]) -> list[float] | None:
    if not values:
        return None
    ordered = sorted(values)
    return [percentile(ordered, 0.025), percentile(ordered, 0.975)]


def cluster_bootstrap(records: list[dict[str, Any]]) -> dict[str, Any]:
    by_table: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        by_table[record["uid"]].append(record)
    table_ids = sorted(by_table)
    rng = random.Random(SEED)
    metrics: dict[str, list[float]] = defaultdict(list)
    for _ in range(N_BOOT):
        sampled = [table_ids[rng.randrange(len(table_ids))] for _ in range(len(table_ids))]
        rows = [record for uid in sampled for record in by_table[uid]]
        visibility_num = sum(int(r["visible"]) for r in rows)
        visibility_den = len(rows)
        metrics["visibility_rate"].append(visibility_num / visibility_den)
        for protocol in PROTOCOLS:
            visible = [r for r in rows if r["visible"]]
            blind = [r for r in rows if not r["visible"]]
            detected = [r for r in rows if r[protocol]]
            undetected = [r for r in rows if not r[protocol]]
            values = {
                f"{protocol}:p_detect_given_visible": ratio(
                    sum(int(r[protocol]) for r in visible), len(visible)
                ),
                f"{protocol}:p_detect_given_blind": ratio(
                    sum(int(r[protocol]) for r in blind), len(blind)
                ),
                f"{protocol}:p_visible_given_detect": ratio(
                    sum(int(r["visible"]) for r in detected), len(detected)
                ),
                f"{protocol}:blindness_among_undetected": ratio(
                    sum(not r["visible"] for r in undetected), len(undetected)
                ),
            }
            for name, value in values.items():
                if value is not None:
                    metrics[name].append(value)
    return {
        "method": "table-cluster nonparametric bootstrap; retain all injections per sampled table",
        "seed": SEED,
        "n_boot": N_BOOT,
        "n_clusters": len(table_ids),
        "ci_level": 0.95,
        "intervals": {name: ci95(values) for name, values in sorted(metrics.items())},
        "replicates_with_defined_value": {name: len(values) for name, values in sorted(metrics.items())},
    }


def png_chunk(kind: bytes, data: bytes) -> bytes:
    return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)


class Canvas:
    def __init__(self, width: int = 1200, height: int = 760) -> None:
        self.width = width
        self.height = height
        self.ops: list[str] = []

    def line(self, x1: int, y1: int, x2: int, y2: int, color: str, width: int = 2) -> None:
        self.ops.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="{width}"/>')

    def text(self, x: int, y: int, value: str, color: str = "#111827", size: int = 18, anchor: str = "start") -> None:
        escaped = value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        self.ops.append(
            f'<text x="{x}" y="{y}" fill="{color}" font-family="sans-serif" font-size="{size}" text-anchor="{anchor}">{escaped}</text>'
        )

    def circle(self, x: int, y: int, radius: int, color: str) -> None:
        self.ops.append(f'<circle cx="{x}" cy="{y}" r="{radius}" fill="{color}"/>')

    def svg(self) -> str:
        body = "\n".join(self.ops)
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.width}" height="{self.height}" '
            f'viewBox="0 0 {self.width} {self.height}">\n'
            f'<rect width="{self.width}" height="{self.height}" fill="#ffffff"/>\n{body}\n</svg>\n'
        )


def simple_png(canvas: Canvas) -> bytes:
    # Deterministic software rasterization for the few primitives used above.
    pixels = bytearray(b"\xff" * (canvas.width * canvas.height * 3))

    def put(x: int, y: int, rgb: tuple[int, int, int]) -> None:
        if 0 <= x < canvas.width and 0 <= y < canvas.height:
            offset = (y * canvas.width + x) * 3
            pixels[offset:offset + 3] = bytes(rgb)

    def color(value: str) -> tuple[int, int, int]:
        value = value.lstrip("#")
        if len(value) == 3:
            value = "".join(ch * 2 for ch in value)
        return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))  # type: ignore[return-value]

    def segment(x1: int, y1: int, x2: int, y2: int, rgb: tuple[int, int, int], width: int) -> None:
        steps = max(abs(x2 - x1), abs(y2 - y1), 1)
        for step in range(steps + 1):
            x = round(x1 + (x2 - x1) * step / steps)
            y = round(y1 + (y2 - y1) * step / steps)
            for dy in range(-(width // 2), width // 2 + 1):
                for dx in range(-(width // 2), width // 2 + 1):
                    put(x + dx, y + dy, rgb)

    # Rasterize structural lines; points are represented by line joins. Text remains SVG-only.
    import re

    for match in re.finditer(
        r'<line x1="(-?\d+)" y1="(-?\d+)" x2="(-?\d+)" y2="(-?\d+)" stroke="([^"]+)" stroke-width="(\d+)"/>',
        "\n".join(canvas.ops),
    ):
        x1, y1, x2, y2 = map(int, match.group(1, 2, 3, 4))
        segment(x1, y1, x2, y2, color(match.group(5)), int(match.group(6)))
    for match in re.finditer(
        r'<circle cx="(-?\d+)" cy="(-?\d+)" r="(\d+)" fill="([^"]+)"/>', "\n".join(canvas.ops)
    ):
        cx, cy, radius = map(int, match.group(1, 2, 3))
        rgb = color(match.group(4))
        for y in range(cy - radius, cy + radius + 1):
            for x in range(cx - radius, cx + radius + 1):
                if (x - cx) ** 2 + (y - cy) ** 2 <= radius ** 2:
                    put(x, y, rgb)
    raw = b"".join(b"\x00" + pixels[y * canvas.width * 3:(y + 1) * canvas.width * 3] for y in range(canvas.height))
    header = struct.pack(">IIBBBBB", canvas.width, canvas.height, 8, 2, 0, 0, 0)
    return b"\x89PNG\r\n\x1a\n" + png_chunk(b"IHDR", header) + png_chunk(b"IDAT", zlib.compress(raw, 9)) + png_chunk(b"IEND", b"")


def render_line_chart(
    path_prefix: Path,
    title: str,
    x_labels: list[str],
    series: list[tuple[str, list[float], str]],
    y_label: str,
) -> None:
    canvas = Canvas()
    left, right, top, bottom = 130, 1100, 100, 640
    canvas.text(600, 45, title, size=25, anchor="middle")
    canvas.text(42, 390, y_label, size=18, anchor="middle")
    canvas.line(left, top, left, bottom, "#374151", 3)
    canvas.line(left, bottom, right, bottom, "#374151", 3)
    for tick in range(6):
        value = tick / 5
        y = round(bottom - value * (bottom - top))
        canvas.line(left - 7, y, right, y, "#e5e7eb", 1)
        canvas.text(left - 18, y + 6, f"{value:.1f}", size=16, anchor="end")
    for index, label in enumerate(x_labels):
        x = round(left + index * (right - left) / max(1, len(x_labels) - 1))
        canvas.line(x, top, x, bottom, "#f3f4f6", 1)
        canvas.text(x, bottom + 38, label, size=17, anchor="middle")
    for name, values, color in series:
        points = []
        for index, value in enumerate(values):
            x = round(left + index * (right - left) / max(1, len(values) - 1))
            y = round(bottom - value * (bottom - top))
            points.append((x, y))
        for start, end in zip(points, points[1:]):
            canvas.line(start[0], start[1], end[0], end[1], color, 4)
        for point in points:
            canvas.circle(point[0], point[1], 7, color)
    legend_x = 760
    for index, (name, _, color) in enumerate(series):
        y = 555 + index * 26
        canvas.line(legend_x, y, legend_x + 35, y, color, 5)
        canvas.text(legend_x + 48, y + 6, name, size=16)
    svg_path = path_prefix.with_suffix(".svg")
    png_path = path_prefix.with_suffix(".png")
    svg_path.write_text(canvas.svg(), encoding="utf-8")
    png_path.write_bytes(simple_png(canvas))


def main() -> None:
    input_hashes = {name: sha256(ROOT / relative) for name, relative in INPUTS.items()}
    t2 = load(INPUTS["t2_visibility_sensitivity"])
    t1 = load(INPUTS["t1_eval_baseline_comparison"])
    d1 = load(INPUTS["d1_mutant_validity_audit"])
    d3 = load(INPUTS["d3_matched_fpr_stage_a"])

    t2_records = t2["injections"]
    t1_records = t1["arm_b"]["injections"]
    d1_records = d1["payload"]["injections"]
    key = lambda row: (row["uid"], row["col"])
    t1_by_key = {key(row): row for row in t1_records}
    d1_by_key = {key(row): row for row in d1_records}
    if len(t2_records) != 118 or len(t1_by_key) != 118 or len(d1_by_key) != 118:
        raise AssertionError("frozen injection cardinality mismatch")

    records: list[dict[str, Any]] = []
    for t2_row in t2_records:
        k = key(t2_row)
        t1_row = t1_by_key[k]
        d1_row = d1_by_key[k]
        if t1_row["type"] != t2_row["type"] or d1_row["type"] != t2_row["type"]:
            raise AssertionError(f"family mismatch at {k}")
        record = {
            "uid": t2_row["uid"],
            "col": t2_row["col"],
            "type": t2_row["type"],
            "visible": bool(t2_row["visible_frozen"]),
            "operational_class": d1_row["class"],
            "equivalent": bool(d1_row["equivalent"]),
            "visible_by_gamma": t2_row["visible_by_gamma"],
        }
        for protocol, (field, _) in PROTOCOLS.items():
            record[protocol] = bool(t1_row[field])
        records.append(record)

    n = len(records)
    visible = sum(r["visible"] for r in records)
    family_counts: dict[str, dict[str, int]] = {}
    for family in FAMILY_ORDER:
        rows = [r for r in records if r["type"] == family]
        family_visible = sum(r["visible"] for r in rows)
        family_counts[family] = {
            "n": len(rows),
            "visible": family_visible,
            "blind": len(rows) - family_visible,
            "visibility_rate": family_visible / len(rows),
            "blindness_rate": (len(rows) - family_visible) / len(rows),
        }
    macro_visibility = sum(v["visibility_rate"] for v in family_counts.values()) / len(family_counts)

    protocol_cells: dict[str, Any] = {}
    for protocol in PROTOCOLS:
        visible_detected = sum(r["visible"] and r[protocol] for r in records)
        visible_undetected = sum(r["visible"] and not r[protocol] for r in records)
        blind_detected = sum(not r["visible"] and r[protocol] for r in records)
        blind_undetected = sum(not r["visible"] and not r[protocol] for r in records)
        detected = visible_detected + blind_detected
        undetected = visible_undetected + blind_undetected
        protocol_cells[protocol] = {
            "cells": {
                "visible_detected": visible_detected,
                "visible_undetected": visible_undetected,
                "blind_detected": blind_detected,
                "blind_undetected": blind_undetected,
            },
            "conditional_rates": {
                "p_detect_given_visible": ratio(visible_detected, visible_detected + visible_undetected),
                "p_detect_given_blind": ratio(blind_detected, blind_detected + blind_undetected),
                "p_visible_given_detect": ratio(visible_detected, detected),
                "blindness_among_undetected": ratio(blind_undetected, undetected),
            },
            "margins": {"detected": detected, "undetected": undetected},
        }
    operational_cells: dict[str, Any] = {}
    for cls in ["H", "HI", "E"]:
        rows = [r for r in records if r["operational_class"] == cls]
        operational_cells[cls] = {
            "n": len(rows),
            "visible": sum(r["visible"] for r in rows),
            "blind": sum(not r["visible"] for r in rows),
        }

    threshold_rows: list[dict[str, Any]] = []
    gammas = [str(x) for x in t2["meta"]["gammas"]]
    for gamma in gammas:
        row: dict[str, Any] = {
            "gamma": float(gamma),
            "visible_injections": sum(r["visible_by_gamma"][gamma] for r in records),
            "blind_injections": sum(not r["visible_by_gamma"][gamma] for r in records),
            "detected_tables": sum(t["detected_by_gamma"][gamma] for t in t2["tables"]),
        }
        for family in FAMILY_ORDER:
            rows = [r for r in records if r["type"] == family]
            row[f"{family}_visible"] = sum(r["visible_by_gamma"][gamma] for r in rows)
            row[f"{family}_n"] = len(rows)
        threshold_rows.append(row)

    with (OUT / "threshold_visibility_source.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(threshold_rows[0]))
        writer.writeheader()
        writer.writerows(threshold_rows)

    visibility_detection_rows: list[dict[str, Any]] = []
    for protocol in PROTOCOLS:
        cells = protocol_cells[protocol]["cells"]
        visibility_detection_rows.append({"protocol": protocol, **cells})
    with (OUT / "visibility_detection_source.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(visibility_detection_rows[0]))
        writer.writeheader()
        writer.writerows(visibility_detection_rows)

    bootstrap = cluster_bootstrap(records)
    matched = d3["payload"]["a4_matched_fpr"]
    frozen_protocols = t1["arm_b"]["protocols"]
    anchors = {
        "tables": len(t2["tables"]),
        "injections": len(records),
        "visible_micro": visible,
        "blind_micro": n - visible,
        "ocr_visible": family_counts["ocr_similar"]["visible"],
        "ocr_total": family_counts["ocr_similar"]["n"],
        "end_to_end_detected": frozen_protocols["E1.1_end_to_end"]["injections_detected"],
        "flat_detected": frozen_protocols["E1.2_flat"]["injections_detected"],
        "hierarchical_detected": frozen_protocols["E1.3_hier_expert"]["injections_detected"],
        "matched_flat_detected": matched["operating_point_matched_alpha"]["det_flat"],
        "matched_layered_detected": matched["operating_point_matched_alpha"]["det_layered"],
        "matched_difference_ci95": matched["matched_fpr_difference"]["bootstrap"]["difference_ci95"],
        "harmful_denominator": matched["denominator_S2"]["harmful_H_union_HI"],
        "operational_classes": d1["payload"]["counts"],
    }
    expected = {
        "tables": 95,
        "injections": 118,
        "visible_micro": 96,
        "blind_micro": 22,
        "ocr_visible": 0,
        "ocr_total": 13,
        "end_to_end_detected": 112,
        "flat_detected": 85,
        "hierarchical_detected": 13,
        "matched_flat_detected": 90,
        "matched_layered_detected": 90,
        "matched_difference_ci95": [0, 0],
        "harmful_denominator": 111,
    }
    checks = {name: anchors[name] == value for name, value in expected.items()}
    if not all(checks.values()):
        raise AssertionError(f"anchor mismatch: {checks}")

    summary = {
        "evidence_labels": {
            "FACT": "recomputed directly from named frozen JSON fields",
            "INFERENCE": "interpretation bounded by the frozen construct and denominators",
            "VALUE": "priority or normative choice",
            "UNVERIFIED": "not identifiable from current labels or source metadata",
        },
        "denominators": {
            "tables": 95,
            "injections": 118,
            "harmful_operational_H_union_HI": 111,
            "equivalent_operational_E": 7,
            "warning": "95 tables, 118 injections and 111 operational harmful injections are distinct denominators, not one partition",
        },
        "visibility": {
            "definition": "visible_frozen in T2; absorption-based checkpoint visibility, not the gamma-dependent score predicate",
            "micro": {"visible": visible, "blind": n - visible, "rate": visible / n, "blindness_rate": (n - visible) / n},
            "macro_family_rate": macro_visibility,
            "by_family": family_counts,
        },
        "threshold_gamma": threshold_rows,
        "visibility_by_detection": protocol_cells,
        "operational_class_visibility_cells": operational_cells,
        "operational_class_identifiability": {
            "status": "UNVERIFIED",
            "reason": "H/HI/E labels are partly defined through detection/equivalence paths; semantic harmfulness-conditional blindness is not independently identifiable",
        },
        "cluster_bootstrap": bootstrap,
        "frozen_anchors": anchors,
        "anchor_checks": checks,
        "endpoint_counts": {
            "model_calls": 0,
            "judge_calls": 0,
            "gpu_training_calls": 0,
            "database_calls": 0,
            "production_service_calls": 0,
            "package_install_calls": 0,
            "paid_api_calls": 0,
        },
    }
    write_json(OUT / "analysis_summary.json", summary)

    x_labels = [f"{float(g):.1f}" for g in gammas]
    threshold_series = [("Overall", [r["visible_injections"] / n for r in threshold_rows], "#111827")]
    colors = ["#2563eb", "#7c3aed", "#059669", "#dc2626", "#d97706", "#0891b2"]
    for family, color in zip(FAMILY_ORDER, colors):
        threshold_series.append(
            (family, [r[f"{family}_visible"] / r[f"{family}_n"] for r in threshold_rows], color)
        )
    render_line_chart(
        OUT / "threshold_visibility",
        "Threshold-conditioned visibility by family",
        x_labels,
        threshold_series,
        "Visibility rate",
    )

    detection_series = []
    for protocol, color in zip(PROTOCOLS, ["#2563eb", "#dc2626", "#7c3aed"]):
        cells = protocol_cells[protocol]["cells"]
        visible = cells["visible_detected"] + cells["visible_undetected"]
        blind = cells["blind_detected"] + cells["blind_undetected"]
        detection_series.append(
            (protocol, [ratio(cells["visible_detected"], visible) or 0, ratio(cells["blind_detected"], blind) or 0], color)
        )
    render_line_chart(
        OUT / "visibility_detection",
        "Detection conditional on frozen checkpoint visibility",
        ["Visible (96)", "Blind (22)"],
        detection_series,
        "P(detect)",
    )

    outputs = [
        "analysis_summary.json",
        "threshold_visibility_source.csv",
        "visibility_detection_source.csv",
        "threshold_visibility.png",
        "threshold_visibility.svg",
        "visibility_detection.png",
        "visibility_detection.svg",
    ]
    receipt = {
        "script": str(Path(__file__).resolve().relative_to(ROOT)),
        "script_sha256": sha256(Path(__file__).resolve()),
        "inputs": {name: {"path": relative, "sha256": input_hashes[name]} for name, relative in INPUTS.items()},
        "formulas": {
            "micro_visibility": "sum(visible_frozen) / 118",
            "micro_blindness": "(118 - sum(visible_frozen)) / 118",
            "macro_family_visibility": "mean(family_visible / family_n) over the six frozen families",
            "p_detect_given_visible": "count(visible AND detected) / count(visible)",
            "p_detect_given_blind": "count(blind AND detected) / count(blind)",
            "p_visible_given_detect": "count(visible AND detected) / count(detected)",
            "blindness_among_undetected": "count(blind AND undetected) / count(undetected)",
            "threshold_visibility": "count(visible_by_gamma[gamma]) / family_or_overall denominator",
        },
        "join_keys": ["uid", "col"],
        "bootstrap": {"seed": SEED, "n_boot": N_BOOT, "cluster": "table uid"},
        "outputs": {name: {"sha256": sha256(OUT / name), "bytes": (OUT / name).stat().st_size} for name in outputs},
        "endpoint_counts": summary["endpoint_counts"],
        "negative_results": [
            "No matplotlib dependency was used; PNG/SVG are rendered by the checked standard-library script.",
            "Semantic harmfulness-conditional blindness remains UNVERIFIED because operational labels are not an independent semantic oracle.",
        ],
    }
    write_json(OUT / "source_data_receipt.json", receipt)
    print(json.dumps({"status": "PASS", "outputs": outputs + ["source_data_receipt.json"], "anchors": anchors}, ensure_ascii=False))


if __name__ == "__main__":
    main()
