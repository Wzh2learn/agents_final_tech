#!/usr/bin/env python3
"""Render the SANER figure bundle from frozen local artifacts only."""
from __future__ import annotations

import csv
import hashlib
import json
import math
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape

from PIL import Image, ImageDraw, ImageFont, PngImagePlugin


ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "docs/research/figures_saner"
T2_PATH = ROOT / "logs/graph/eval/t2_visibility_sensitivity.json"
CHECKPOINT_PATH = ROOT / "logs/graph/eval/checkpoint_discrimination_tables_v2.json"
ABLATION_PATH = ROOT / "research/stage_e_multileaf_20261010/results/multileaf_signature_ablation.json"
SPEC_PATH = ROOT / "research/stage_e_multileaf_20261010/loop_d_inputs/stage_e_version_b_figure_spec_v1.md"
SCOPE_PATH = ROOT / "paper/saner_rene_manuscript_scope_lock_v1.md"
PLAN_PATH = ROOT / "paper/figure_plan_v1.md"
CANDIDATE_MANIFEST_PATH = ROOT / "docs/research/figures_multileaf/manifest.json"
CANDIDATE_SVG_PATH = ROOT / "docs/research/figures_multileaf/fig_multileaf_localization_ablation.svg"
CANDIDATE_PNG_PATH = ROOT / "docs/research/figures_multileaf/fig_multileaf_localization_ablation.png"
CANDIDATE_RENDERER_PATH = ROOT / "research/stage_e_multileaf_20261010/render_multileaf_localization_ablation_v2.py"
CANDIDATE_REPAIR_RECEIPT_PATH = ROOT / "research/stage_e_multileaf_20261010/stage_e_evidence_strengthening_repair_receipt.json"

FIG1_PATH = OUT / "fig1_measurement_chain.svg"
FIG2_SVG_PATH = OUT / "fig2_family_visibility_matrix.svg"
FIG2_PNG_PATH = OUT / "fig2_family_visibility_matrix.png"
FIG2_CSV_PATH = OUT / "fig2_source.csv"
FIG3_SVG_PATH = OUT / "fig3_localization_ablation.svg"
FIG3_PNG_PATH = OUT / "fig3_localization_ablation.png"
MANIFEST_PATH = OUT / "figure_source_binding_manifest.json"

FONT_REGULAR = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
TEXT = "#172033"
MUTED = "#59677a"
GRID = "#cdd5df"

FIG1_CAPTION = "NIST motivates measurement effectiveness, not this paper's blind-spot framework."
FIG2_CAPTION = (
    "Figure 2. Defect family × checkpoint visibility. This is a visibility matrix, "
    "not a harmfulness matrix; cell values are visibility rates and annotations are "
    "visible/injection counts."
)
FIG2_OCR_NOTE = "0/13 OCR-like injections were visible across 11 table clusters"
FIG3_CAPTION = (
    "Full and direct-codebook localization are perfect on the explicitly instrumented "
    "M/R/N observation surface. When directly targeted checkpoints are removed, top-1 "
    "falls to chance. The result reflects stage-aligned instrumentation, not emergent "
    "localization from the remaining hierarchy."
)
FIG3_FORBIDDEN = (
    "hierarchy localizes failures",
    "natural failures are localized",
    "distributed downstream evidence is sufficient",
)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def close(left: float, right: float) -> bool:
    return math.isclose(left, right, rel_tol=0.0, abs_tol=1e-12)


class Canvas:
    def __init__(self, width: int, height: int, title: str, description: str) -> None:
        self.width = width
        self.height = height
        self.image = Image.new("RGB", (width, height), "white")
        self.draw = ImageDraw.Draw(self.image)
        self.parts = [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
            f'viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
            f"<title>{escape(title)}</title>",
            f"<desc>{escape(description)}</desc>",
            f'<rect x="0" y="0" width="{width}" height="{height}" fill="#ffffff"/>',
        ]

    @staticmethod
    def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
        return ImageFont.truetype(FONT_BOLD if bold else FONT_REGULAR, size=size)

    @staticmethod
    def wrap(text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
        lines: list[str] = []
        for paragraph in text.split("\n"):
            words = paragraph.split()
            if not words:
                lines.append("")
                continue
            current = words[0]
            for word in words[1:]:
                candidate = f"{current} {word}"
                if font.getlength(candidate) <= max_width:
                    current = candidate
                else:
                    lines.append(current)
                    current = word
            lines.append(current)
        return lines

    def rect(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        *,
        fill: str = "#ffffff",
        outline: str = TEXT,
        width_px: int = 3,
        radius: int = 0,
        dash: str | None = None,
    ) -> None:
        box = (x, y, x + width, y + height)
        pillow_fill = None if fill == "none" else fill
        if radius:
            self.draw.rounded_rectangle(
                box, radius=radius, fill=pillow_fill, outline=outline, width=width_px
            )
            radius_attr = f' rx="{radius}" ry="{radius}"'
        else:
            self.draw.rectangle(box, fill=pillow_fill, outline=outline, width=width_px)
            radius_attr = ""
        dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
        self.parts.append(
            f'<rect x="{x}" y="{y}" width="{width}" height="{height}" fill="{fill}" '
            f'stroke="{outline}" stroke-width="{width_px}"{radius_attr}{dash_attr}/>'
        )

    def polygon(
        self,
        points: list[tuple[int, int]],
        *,
        fill: str = "#ffffff",
        outline: str = TEXT,
        width_px: int = 3,
        dash: str | None = None,
    ) -> None:
        pillow_fill = None if fill == "none" else fill
        pillow_outline = None if outline == "none" else outline
        self.draw.polygon(points, fill=pillow_fill, outline=pillow_outline)
        if width_px > 1 and pillow_outline is not None:
            self.draw.line(
                [*points, points[0]], fill=pillow_outline, width=width_px, joint="curve"
            )
        point_text = " ".join(f"{x},{y}" for x, y in points)
        dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
        self.parts.append(
            f'<polygon points="{point_text}" fill="{fill}" stroke="{outline}" '
            f'stroke-width="{width_px}"{dash_attr}/>'
        )

    def line(
        self,
        x1: int,
        y1: int,
        x2: int,
        y2: int,
        *,
        color: str = TEXT,
        width_px: int = 3,
        dash: str | None = None,
    ) -> None:
        self.draw.line((x1, y1, x2, y2), fill=color, width=width_px)
        dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
        self.parts.append(
            f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" '
            f'stroke-width="{width_px}"{dash_attr}/>'
        )

    def text(
        self,
        x: int,
        y: int,
        text: str,
        size: int,
        *,
        color: str = TEXT,
        bold: bool = False,
        anchor: str = "mm",
        max_width: int | None = None,
        spacing: int = 7,
    ) -> list[str]:
        font = self.font(size, bold)
        lines = self.wrap(text, font, max_width) if max_width else text.splitlines()
        line_height = size + spacing
        block_height = max(line_height * len(lines) - spacing, size)
        if anchor[1] == "m":
            top = y - block_height // 2
        elif anchor[1] == "s":
            top = y - block_height
        else:
            top = y
        horizontal = anchor[0]
        for index, line_text in enumerate(lines):
            line_y = top + index * line_height
            self.draw.text((x, line_y), line_text, font=font, fill=color, anchor=f"{horizontal}a")
            svg_anchor = {"l": "start", "m": "middle", "r": "end"}[horizontal]
            baseline = line_y + size
            weight = "700" if bold else "400"
            self.parts.append(
                f'<text x="{x}" y="{baseline}" fill="{color}" font-family="DejaVu Sans" '
                f'font-size="{size}" font-weight="{weight}" text-anchor="{svg_anchor}" '
                f'xml:space="preserve">{escape(line_text)}</text>'
            )
        return lines

    def arrow(self, x1: int, y: int, x2: int, *, color: str = TEXT) -> None:
        self.line(x1, y, x2 - 14, y, color=color, width_px=4)
        self.polygon(
            [(x2 - 14, y - 10), (x2, y), (x2 - 14, y + 10)],
            fill=color,
            outline=color,
            width_px=1,
        )

    def metadata(self, element_id: str, text: str) -> None:
        self.parts.append(f'<metadata id="{element_id}">{escape(text)}</metadata>')

    def save(self, path: Path, png_metadata: dict[str, str] | None = None) -> None:
        self.parts.append("</svg>")
        path.with_suffix(".svg").write_text("\n".join(self.parts) + "\n", encoding="utf-8")
        if path.suffix.lower() == ".png" or png_metadata is not None:
            info = PngImagePlugin.PngInfo()
            for key, value in sorted((png_metadata or {}).items()):
                info.add_text(key, value)
            self.image.save(path, format="PNG", optimize=True, pnginfo=info)


def render_fig1() -> None:
    canvas = Canvas(
        1800,
        700,
        "Figure 1. Measurement chain",
        "Five-stage measurement chain separating motivation, controlled failure, visibility, detection, and harm.",
    )
    canvas.text(900, 48, "Figure 1. Measurement chain", 36, bold=True, anchor="mm")
    canvas.text(
        900,
        95,
        "Observability precedes detection and harm claims",
        22,
        color=MUTED,
        anchor="mm",
    )
    nodes = [
        ("MOTIVATION", "Measurement-effectiveness motivation\nNIST / long-horizon service", "rect"),
        ("CONTROLLED FAILURE", "Controlled failure state\nStaged pipeline perturbation", "rect"),
        ("VISIBILITY", "Checkpoint visibility\nDid any instrument observe the failure?", "round"),
        ("DETECTION", "Protocol detection\nDid the decision rule use that observation?", "octagon"),
        ("OUTCOME / HARM", "Outcome / harm\nConsequence under stated contract?", "diamond"),
    ]
    x_positions = [55, 400, 745, 1090, 1435]
    y, node_width, node_height = 180, 310, 245
    for index, ((tag, label, shape), x) in enumerate(zip(nodes, x_positions, strict=True)):
        fill = "#f8fafc" if index < 2 else "#ffffff"
        if shape == "rect":
            canvas.rect(x, y, node_width, node_height, fill=fill, width_px=3)
        elif shape == "round":
            canvas.rect(x, y, node_width, node_height, fill=fill, width_px=5, radius=30)
            canvas.rect(
                x + 12,
                y + 12,
                node_width - 24,
                node_height - 24,
                fill="none",
                outline=MUTED,
                width_px=2,
                radius=20,
                dash="7 6",
            )
        elif shape == "octagon":
            inset = 35
            outer = [
                (x + inset, y),
                (x + node_width - inset, y),
                (x + node_width, y + inset),
                (x + node_width, y + node_height - inset),
                (x + node_width - inset, y + node_height),
                (x + inset, y + node_height),
                (x, y + node_height - inset),
                (x, y + inset),
            ]
            inner_inset = 12
            inner = [
                (x + inset + inner_inset, y + inner_inset),
                (x + node_width - inset - inner_inset, y + inner_inset),
                (x + node_width - inner_inset, y + inset + inner_inset),
                (x + node_width - inner_inset, y + node_height - inset - inner_inset),
                (x + node_width - inset - inner_inset, y + node_height - inner_inset),
                (x + inset + inner_inset, y + node_height - inner_inset),
                (x + inner_inset, y + node_height - inset - inner_inset),
                (x + inner_inset, y + inset + inner_inset),
            ]
            canvas.polygon(outer, fill=fill, width_px=6)
            canvas.polygon(inner, fill="none", outline=MUTED, width_px=2)
        else:
            cx, cy = x + node_width // 2, y + node_height // 2
            outer = [
                (cx, y),
                (x + node_width, cy),
                (cx, y + node_height),
                (x, cy),
            ]
            canvas.polygon(outer, fill=fill, width_px=6)
        canvas.text(
            cx if shape == "diamond" else x + node_width // 2,
            y - 24 if shape == "diamond" else y + 48,
            tag,
            17,
            bold=True,
            anchor="mm",
        )
        canvas.text(
            cx if shape == "diamond" else x + node_width // 2,
            y + 145,
            label,
            18 if shape == "diamond" else 21,
            anchor="mm",
            max_width=240 if shape == "diamond" else node_width - 60,
            spacing=8,
        )
        if index < len(nodes) - 1:
            canvas.arrow(x + node_width, y + node_height // 2, x_positions[index + 1])
    canvas.text(
        900,
        635,
        FIG1_CAPTION,
        22,
        color=MUTED,
        anchor="mm",
        max_width=1700,
    )
    canvas.metadata("required-caption", FIG1_CAPTION)
    canvas.save(FIG1_PATH)


def fig2_bindings(
    t2: dict[str, Any],
    checkpoint: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    numeric: list[dict[str, Any]] = []
    gammas = t2["meta"]["gammas"]
    types = t2["meta"]["types"]
    for gamma_index, gamma in enumerate(gammas):
        gamma_key = f"{gamma:.1f}"
        numeric.append(
            {
                "display": f"{gamma:.1f}",
                "source": rel(T2_PATH),
                "field_path": f"$.meta.gammas[{gamma_index}]",
                "value": gamma,
            }
        )
        for family in types:
            cell = t2["e2_1_gamma_grid"][gamma_key]["by_type"][family]
            frozen = checkpoint["by_type"][family]
            if cell["n"] != frozen["n_injections"]:
                raise RuntimeError(f"HASH_MISMATCH: injection count mismatch for {gamma_key}/{family}")
            if abs(cell["visibility_rate"] - cell["visible"] / cell["n"]) > 0.0001:
                raise RuntimeError(f"FIGURE_DATA_MISSING: invalid visibility rate for {gamma_key}/{family}")
            rate_path = f'$.e2_1_gamma_grid["{gamma_key}"].by_type["{family}"].visibility_rate'
            visible_path = f'$.e2_1_gamma_grid["{gamma_key}"].by_type["{family}"].visible'
            n_path = f'$.e2_1_gamma_grid["{gamma_key}"].by_type["{family}"].n'
            n_cross_path = f'$.by_type["{family}"].n_injections'
            rows.append(
                {
                    "family": family,
                    "gamma": gamma,
                    "visibility_rate": f"{cell['visibility_rate']:.4f}",
                    "visible_count": cell["visible"],
                    "injection_count": cell["n"],
                    "visibility_rate_field_path": rate_path,
                    "visible_count_field_path": visible_path,
                    "injection_count_field_path": n_path,
                    "injection_count_crosscheck_path": n_cross_path,
                    "crosscheck_status": "PASS",
                }
            )
            for display, source, path, value in (
                (f"{cell['visibility_rate']:.4f}", rel(T2_PATH), rate_path, cell["visibility_rate"]),
                (str(cell["visible"]), rel(T2_PATH), visible_path, cell["visible"]),
                (str(cell["n"]), rel(T2_PATH), n_path, cell["n"]),
            ):
                numeric.append(
                    {
                        "display": display,
                        "source": source,
                        "field_path": path,
                        "value": value,
                    }
                )
    return rows, numeric


def render_fig2(t2: dict[str, Any], checkpoint: dict[str, Any]) -> list[dict[str, Any]]:
    rows, numeric = fig2_bindings(t2, checkpoint)
    with FIG2_CSV_PATH.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "family",
                "gamma",
                "visibility_rate",
                "visible_count",
                "injection_count",
                "visibility_rate_field_path",
                "visible_count_field_path",
                "injection_count_field_path",
                "injection_count_crosscheck_path",
                "crosscheck_status",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    canvas = Canvas(
        1800,
        1080,
        "Figure 2. Defect family × checkpoint visibility",
        "Visibility-rate matrix across six defect families and five gamma thresholds; annotations are visible and injection counts.",
    )
    canvas.text(900, 42, "Figure 2. Defect family × checkpoint visibility", 36, bold=True, anchor="mm")
    canvas.text(
        900,
        88,
        "Cell = visibility rate; annotation = visible / injections",
        22,
        color=MUTED,
        anchor="mm",
    )
    x0, label_width, grid_y = 55, 355, 155
    column_width, header_height, row_height = 270, 68, 112
    gammas = t2["meta"]["gammas"]
    types = t2["meta"]["types"]
    canvas.rect(x0, grid_y, label_width, header_height, fill="#eef2f6", width_px=2)
    canvas.text(
        x0 + label_width // 2,
        grid_y + header_height // 2,
        "Defect family",
        23,
        bold=True,
        anchor="mm",
    )
    for col, gamma in enumerate(gammas):
        x = x0 + label_width + col * column_width
        canvas.rect(x, grid_y, column_width, header_height, fill="#eef2f6", width_px=2)
        canvas.text(
            x + column_width // 2,
            grid_y + header_height // 2,
            f"gamma {gamma:.1f}",
            22,
            bold=True,
            anchor="mm",
        )
    row_by_key = {(row["family"], row["gamma"]): row for row in rows}
    for row_index, family in enumerate(types):
        y = grid_y + header_height + row_index * row_height
        canvas.rect(x0, y, label_width, row_height, fill="#f8fafc", width_px=2)
        canvas.text(
            x0 + label_width // 2,
            y + row_height // 2,
            family.replace("_", " "),
            23,
            bold=True,
            anchor="mm",
            max_width=label_width - 30,
        )
        for col, gamma in enumerate(gammas):
            row = row_by_key[(family, gamma)]
            rate = float(row["visibility_rate"])
            shade = round(245 - rate * 145)
            fill = f"#{shade:02x}{shade:02x}{shade:02x}"
            text_color = "#ffffff" if rate >= 0.68 else TEXT
            x = x0 + label_width + col * column_width
            canvas.rect(x, y, column_width, row_height, fill=fill, width_px=2)
            canvas.text(
                x + column_width // 2,
                y + 38,
                row["visibility_rate"],
                27,
                color=text_color,
                bold=True,
                anchor="mm",
            )
            canvas.text(
                x + column_width // 2,
                y + 77,
                f"{row['visible_count']} / {row['injection_count']}",
                21,
                color=text_color,
                anchor="mm",
            )
    note_y = grid_y + header_height + len(types) * row_height + 35
    canvas.rect(180, note_y, 1440, 74, fill="#f3f4f6", outline=MUTED, width_px=3, radius=18)
    canvas.text(900, note_y + 37, FIG2_OCR_NOTE, 25, bold=True, anchor="mm")
    canvas.text(
        900,
        note_y + 125,
        FIG2_CAPTION,
        18,
        color=MUTED,
        anchor="mm",
        max_width=1700,
        spacing=5,
    )
    canvas.metadata("required-caption", FIG2_CAPTION)
    canvas.metadata("ocr-note", FIG2_OCR_NOTE)
    canvas.save(
        FIG2_PNG_PATH,
        png_metadata={
            "saner_figure": "fig2_family_visibility_matrix",
            "t2_visibility_sensitivity_sha256": sha256_file(T2_PATH),
            "checkpoint_discrimination_tables_v2_sha256": sha256_file(CHECKPOINT_PATH),
            "renderer_sha256": sha256_file(Path(__file__)),
        },
    )
    canvas.parts[-1] = "</svg>"
    FIG2_SVG_PATH.write_text("\n".join(canvas.parts) + "\n", encoding="utf-8")

    for display, source, path, value in (
        ("0", rel(T2_PATH), '$.e2_1_gamma_grid["0.2"].by_type["ocr_similar"].visible', 0),
        ("13", rel(T2_PATH), '$.e2_1_gamma_grid["0.2"].by_type["ocr_similar"].n', 13),
        ("11", rel(CHECKPOINT_PATH), '$.by_type["ocr_similar"].n_tables', 11),
    ):
        numeric.append({"display": display, "source": source, "field_path": path, "value": value})
    return numeric


def ablation_values(ablation: dict[str, Any]) -> dict[str, Any]:
    feature_sets = ablation["feature_sets"]
    full = feature_sets["full_vector"]
    direct = feature_sets["direct_target_codebook"]
    non_direct = feature_sets["non_direct_leaves_only"]
    classes = [name for name in full["confusion"] if name != "__TIE__"]
    supports = {name: sum(full["confusion"][name].values()) for name in classes}
    if len(classes) != 3 or set(supports.values()) != {72}:
        raise RuntimeError("FIGURE_DATA_MISSING: expected three balanced frozen classes")
    values = {
        "full_macro_f1": float(full["macro_f1"]),
        "full_top1": float(full["top1_accuracy"]),
        "direct_macro_f1": float(direct["macro_f1"]),
        "direct_top1": float(direct["top1_accuracy"]),
        "non_direct_macro_f1": float(non_direct["macro_f1"]),
        "non_direct_top1": float(non_direct["top1_accuracy"]),
        "majority_macro_f1": 1.0 / (2.0 * len(classes)),
        "chance_top1": 1.0 / len(classes),
    }
    required = {
        "full_macro_f1": 1.0,
        "full_top1": 1.0,
        "direct_macro_f1": 1.0,
        "direct_top1": 1.0,
        "non_direct_macro_f1": 1.0 / 3.0,
        "non_direct_top1": 1.0 / 3.0,
        "majority_macro_f1": 1.0 / 6.0,
        "chance_top1": 1.0 / 3.0,
    }
    if any(not close(values[key], expected) for key, expected in required.items()):
        raise RuntimeError(f"FIGURE_DATA_MISSING: frozen ablation identities failed: {values}")
    return values


def verify_candidate(
    candidate_manifest: dict[str, Any],
    repair_receipt: dict[str, Any],
    ablation_values_by_key: dict[str, Any],
) -> list[str]:
    expected_svg = candidate_manifest["outputs"][CANDIDATE_SVG_PATH.name]["sha256"]
    expected_png = candidate_manifest["outputs"][CANDIDATE_PNG_PATH.name]["sha256"]
    if sha256_file(CANDIDATE_SVG_PATH) != expected_svg:
        raise RuntimeError("HASH_MISMATCH: candidate SVG hash")
    if sha256_file(CANDIDATE_PNG_PATH) != expected_png:
        raise RuntimeError("HASH_MISMATCH: candidate PNG hash")
    if repair_receipt["output_sha256"][rel(CANDIDATE_SVG_PATH)] != expected_svg:
        raise RuntimeError("HASH_MISMATCH: candidate SVG repair receipt")
    if repair_receipt["output_sha256"][rel(CANDIDATE_PNG_PATH)] != expected_png:
        raise RuntimeError("HASH_MISMATCH: candidate PNG repair receipt")
    if repair_receipt["output_sha256"][rel(CANDIDATE_RENDERER_PATH)] != sha256_file(CANDIDATE_RENDERER_PATH):
        raise RuntimeError("HASH_MISMATCH: candidate renderer receipt")
    svg_text = CANDIDATE_SVG_PATH.read_text(encoding="utf-8")
    for phrase in FIG3_FORBIDDEN:
        if phrase in svg_text.lower():
            raise RuntimeError(f"FIGURE_DATA_MISSING: forbidden candidate caption language: {phrase}")
    required_candidate_values = ("1.0000", "0.3333", "0.1667")
    for value in required_candidate_values:
        if value not in svg_text:
            raise RuntimeError(f"FIGURE_DATA_MISSING: candidate SVG missing {value}")
    expected_formatted = {
        f"{ablation_values_by_key[key]:.4f}"
        for key in (
            "full_macro_f1",
            "full_top1",
            "direct_macro_f1",
            "direct_top1",
            "non_direct_macro_f1",
            "non_direct_top1",
            "majority_macro_f1",
            "chance_top1",
        )
    }
    if not set(required_candidate_values) <= expected_formatted:
        raise RuntimeError("FIGURE_DATA_MISSING: candidate formatted value mismatch")
    return [
        "Figure 3 candidate SVG/PNG hashes match the candidate manifest and repair receipt.",
        "Figure 3 candidate renderer hash matches the repair receipt.",
        "Figure 3 candidate SVG contains all required formatted values and no forbidden caption phrase.",
    ]


def render_fig3(
    ablation: dict[str, Any],
    values: dict[str, Any],
    candidate_manifest: dict[str, Any],
    repair_receipt: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[str]]:
    candidate_notes = verify_candidate(candidate_manifest, repair_receipt, values)
    canvas = Canvas(
        1600,
        1000,
        "Figure 3. Multi-leaf localization and ablation",
        "Macro-F1 and top-1 ablation bars on the explicitly instrumented M/R/N observation surface.",
    )
    canvas.text(
        800,
        42,
        "Figure 3. Multi-leaf localization and ablation",
        36,
        bold=True,
        anchor="mm",
    )
    canvas.text(
        800,
        88,
        "Explicitly instrumented M/R/N observation surface",
        22,
        color=MUTED,
        anchor="mm",
    )
    panels = [
        (
            "Panel A · Macro-F1",
            125,
            [
                ("Full vector", "full_macro_f1", "$.feature_sets.full_vector.macro_f1"),
                ("Direct codebook", "direct_macro_f1", "$.feature_sets.direct_target_codebook.macro_f1"),
                ("Non-direct leaves", "non_direct_macro_f1", "$.feature_sets.non_direct_leaves_only.macro_f1"),
                (
                    "Majority baseline",
                    "majority_macro_f1",
                    "$.feature_sets.full_vector.confusion",
                ),
            ],
        ),
        (
            "Panel B · Top-1",
            510,
            [
                ("Full vector", "full_top1", "$.feature_sets.full_vector.top1_accuracy"),
                ("Direct codebook", "direct_top1", "$.feature_sets.direct_target_codebook.top1_accuracy"),
                ("Non-direct leaves", "non_direct_top1", "$.feature_sets.non_direct_leaves_only.top1_accuracy"),
                ("Chance baseline", "chance_top1", "$.signature_counts"),
            ],
        ),
    ]
    numeric: list[dict[str, Any]] = []
    for panel_title, panel_y, rows in panels:
        canvas.text(70, panel_y, panel_title, 27, bold=True, anchor="lm")
        bar_x, bar_width = 390, 930
        for row_index, (label, key, field_path) in enumerate(rows):
            y = panel_y + 58 + row_index * 74
            value = values[key]
            numeric.append(
                {
                    "display": f"{value:.4f}",
                    "source": rel(ABLATION_PATH),
                    "field_path": field_path,
                    "value": value,
                    "derivation": (
                        None
                        if key not in {"majority_macro_f1", "chance_top1"}
                        else {
                            "formula": "1/(2K)" if key == "majority_macro_f1" else "1/K",
                            "K": 3,
                            "basis_field_path": field_path,
                            "class_field_paths": (
                                [
                                    "$.feature_sets.full_vector.confusion.M",
                                    "$.feature_sets.full_vector.confusion.N",
                                    "$.feature_sets.full_vector.confusion.R",
                                ]
                                if key == "majority_macro_f1"
                                else ["$.signature_counts.M", "$.signature_counts.N", "$.signature_counts.R"]
                            ),
                        }
                    ),
                }
            )
            canvas.text(355, y + 22, label, 23, anchor="rm", max_width=310)
            canvas.rect(bar_x, y, bar_width, 44, fill="#f3f5f7", outline=GRID, width_px=2, radius=8)
            fill = "#365a6b" if row_index < 2 else "#9aabb4"
            canvas.rect(
                bar_x,
                y,
                max(6, round(bar_width * value)),
                44,
                fill=fill,
                outline="#365a6b" if row_index < 2 else "#71858f",
                width_px=2,
                radius=8,
            )
            canvas.text(1570, y + 22, f"{value:.4f}", 24, bold=True, anchor="rm")
    canvas.text(
        800,
        910,
        FIG3_CAPTION,
        20,
        color=MUTED,
        anchor="mm",
        max_width=1470,
        spacing=6,
    )
    canvas.metadata("required-caption", FIG3_CAPTION)
    canvas.save(
        FIG3_PNG_PATH,
        png_metadata={
            "saner_figure": "fig3_localization_ablation",
            "multileaf_signature_ablation_sha256": sha256_file(ABLATION_PATH),
            "candidate_svg_sha256": sha256_file(CANDIDATE_SVG_PATH),
            "candidate_png_sha256": sha256_file(CANDIDATE_PNG_PATH),
            "renderer_sha256": sha256_file(Path(__file__)),
        },
    )
    canvas.parts[-1] = "</svg>"
    FIG3_SVG_PATH.write_text("\n".join(canvas.parts) + "\n", encoding="utf-8")
    return numeric, candidate_notes


def source(path: Path, role: str) -> dict[str, str]:
    return {"path": rel(path), "sha256": sha256_file(path), "role": role}


def output(path: Path) -> dict[str, Any]:
    return {"path": rel(path), "sha256": sha256_file(path), "bytes": path.stat().st_size}


def write_manifest(
    fig1_caption: str,
    fig2_numeric: list[dict[str, Any]],
    fig3_numeric: list[dict[str, Any]],
    fig3_notes: list[str],
) -> None:
    renderer = source(Path(__file__), "deterministic renderer")
    fig1 = {
        "source_artifacts": [
            source(SCOPE_PATH, "frozen figure definition and caption boundary"),
            source(SPEC_PATH, "approved figure specification"),
            source(PLAN_PATH, "existing figure ledger (read-only reference)"),
        ],
        "numeric_bindings": [],
        "renderer_scripts": [renderer],
        "outputs": [output(FIG1_PATH)],
        "caption": fig1_caption,
    }
    fig2 = {
        "source_artifacts": [
            source(SCOPE_PATH, "frozen caption boundary"),
            source(SPEC_PATH, "approved matrix encoding"),
            source(PLAN_PATH, "existing figure ledger (read-only reference)"),
            source(T2_PATH, "threshold-specific visibility rates and counts"),
            source(CHECKPOINT_PATH, "frozen injection and OCR cluster counts"),
        ],
        "numeric_bindings": fig2_numeric,
        "renderer_scripts": [renderer],
        "outputs": [
            output(FIG2_SVG_PATH),
            output(FIG2_PNG_PATH),
            output(FIG2_CSV_PATH),
        ],
        "caption": FIG2_CAPTION,
        "ocr_note": FIG2_OCR_NOTE,
        "caption_boundary": "visibility matrix, not harmfulness matrix",
    }
    fig3 = {
        "source_artifacts": [
            source(SCOPE_PATH, "frozen caption boundary"),
            source(SPEC_PATH, "required caption and forbidden language"),
            source(PLAN_PATH, "existing figure ledger (read-only reference)"),
            source(ABLATION_PATH, "full, direct, non-direct, class-support derivation"),
            source(CANDIDATE_SVG_PATH, "existing candidate SVG"),
            source(CANDIDATE_PNG_PATH, "existing candidate PNG"),
            source(CANDIDATE_MANIFEST_PATH, "candidate output hash manifest"),
            source(CANDIDATE_RENDERER_PATH, "candidate renderer hash"),
            source(CANDIDATE_REPAIR_RECEIPT_PATH, "candidate hash-chain validation"),
        ],
        "numeric_bindings": fig3_numeric,
        "source_verification": fig3_notes,
        "renderer_scripts": [renderer, source(CANDIDATE_RENDERER_PATH, "candidate source renderer")],
        "outputs": [output(FIG3_SVG_PATH), output(FIG3_PNG_PATH)],
        "caption": FIG3_CAPTION,
        "forbidden_caption_language": list(FIG3_FORBIDDEN),
    }
    manifest = {
        "schema_version": 1,
        "namespace": "SANER_FIGURE_SOURCE_BINDING",
        "status": "COMPLETE",
        "model_calls": 0,
        "figures": {"fig1": fig1, "fig2": fig2, "fig3": fig3},
    }
    MANIFEST_PATH.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    t2 = read_json(T2_PATH)
    checkpoint = read_json(CHECKPOINT_PATH)
    ablation = read_json(ABLATION_PATH)
    candidate_manifest = read_json(CANDIDATE_MANIFEST_PATH)
    repair_receipt = read_json(CANDIDATE_REPAIR_RECEIPT_PATH)
    values = ablation_values(ablation)
    render_fig1()
    fig2_numeric = render_fig2(t2, checkpoint)
    fig3_numeric, fig3_notes = render_fig3(
        ablation, values, candidate_manifest, repair_receipt
    )
    write_manifest(FIG1_CAPTION, fig2_numeric, fig3_numeric, fig3_notes)
    print("SANER_FIGURES_RENDER_PASS")


if __name__ == "__main__":
    main()
