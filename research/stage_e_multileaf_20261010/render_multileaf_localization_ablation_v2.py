#!/usr/bin/env python3
"""Render Figure 3 only from the frozen multileaf ablation artifact."""
from __future__ import annotations

import hashlib
import json
import textwrap
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[2]
ABLATION = ROOT / "research/stage_e_multileaf_20261010/results/multileaf_signature_ablation.json"
FIGURE_DIR = ROOT / "docs/research/figures_multileaf"
PNG = FIGURE_DIR / "fig_multileaf_localization_ablation.png"
SVG = FIGURE_DIR / "fig_multileaf_localization_ablation.svg"
MANIFEST = FIGURE_DIR / "manifest.json"
FONT_REGULAR = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

FULL_COLOR = "#38678f"
DIRECT_COLOR = "#3d968f"
NON_DIRECT_COLOR = "#db7b4a"
BASELINE_COLOR = "#adb6c4"
TEXT_COLOR = "#172033"
MUTED_COLOR = "#66748d"
GRID_COLOR = "#dce7f5"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _balanced_classes(full: dict[str, Any]) -> list[str]:
    confusion = full["confusion"]
    classes = [name for name in confusion if name != "__TIE__"]
    supports = {name: sum(confusion[name].values()) for name in classes}
    if len(classes) != 3 or len(set(supports.values())) != 1:
        raise RuntimeError(
            f"FIGURE_REPAIR_INPUT_MISSING: expected three balanced classes, got {supports}"
        )
    return classes


def _close(left: float, right: float) -> bool:
    return abs(left - right) < 1e-12


def load_values() -> dict[str, Any]:
    payload = json.loads(ABLATION.read_text(encoding="utf-8"))
    feature_sets = payload["feature_sets"]
    full = feature_sets["full_vector"]
    direct = feature_sets["direct_target_codebook"]
    non_direct = feature_sets["non_direct_leaves_only"]
    classes = _balanced_classes(full)

    chance_top1 = 1.0 / len(classes)
    uniform_macro_f1 = 1.0 / len(classes)
    majority_macro_f1 = 1.0 / (2.0 * len(classes))
    values = {
        "full_macro_f1": float(full["macro_f1"]),
        "full_top1": float(full["top1_accuracy"]),
        "direct_macro_f1": float(direct["macro_f1"]),
        "direct_top1": float(direct["top1_accuracy"]),
        "non_direct_macro_f1": float(non_direct["macro_f1"]),
        "non_direct_top1": float(non_direct["top1_accuracy"]),
        "chance_top1": chance_top1,
        "uniform_macro_f1": uniform_macro_f1,
        "majority_macro_f1": majority_macro_f1,
    }
    required_equalities = (
        _close(values["full_macro_f1"], 1.0),
        _close(values["full_top1"], 1.0),
        _close(values["direct_macro_f1"], 1.0),
        _close(values["direct_top1"], 1.0),
        _close(values["non_direct_macro_f1"], uniform_macro_f1),
        _close(values["non_direct_top1"], chance_top1),
    )
    if not all(required_equalities):
        raise RuntimeError(
            f"FIGURE_REPAIR_INPUT_MISSING: frozen values do not satisfy required identities: {values}"
        )
    return values


@dataclass
class Scene:
    width: int
    height: int
    image: Image.Image
    draw: ImageDraw.ImageDraw
    svg_elements: list[str]

    @classmethod
    def create(cls) -> "Scene":
        image = Image.new("RGB", (1600, 900), "white")
        draw = ImageDraw.Draw(image)
        return cls(1600, 900, image, draw, [])

    @staticmethod
    def _font(size: int, bold: bool) -> ImageFont.FreeTypeFont:
        return ImageFont.truetype(FONT_BOLD if bold else FONT_REGULAR, size=size)

    def line(self, x1: int, y1: int, x2: int, y2: int, fill: str, width: int = 1) -> None:
        self.draw.line((x1, y1, x2, y2), fill=fill, width=width)
        self.svg_elements.append(
            f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{fill}" stroke-width="{width}"/>'
        )

    def text(
        self,
        x: int,
        y: int,
        text: str,
        size: int,
        fill: str = TEXT_COLOR,
        *,
        bold: bool = False,
        anchor: str = "la",
        spacing: int = 8,
    ) -> None:
        font = self._font(size, bold)
        self.draw.multiline_text(
            (x, y),
            text,
            font=font,
            fill=fill,
            anchor=anchor,
            spacing=spacing,
            align="center" if anchor.startswith("m") else "left",
        )
        svg_anchor = "middle" if anchor.startswith("m") else "start"
        if anchor.startswith("r"):
            svg_anchor = "end"
        line_height = size + spacing
        for index, line_text in enumerate(text.splitlines() or [""]):
            baseline = y + size + index * line_height
            weight = "700" if bold else "400"
            self.svg_elements.append(
                f'<text x="{x}" y="{baseline}" fill="{fill}" font-family="DejaVu Sans" '
                f'font-size="{size}" font-weight="{weight}" text-anchor="{svg_anchor}">'
                f"{escape(line_text)}</text>"
            )

    def rounded_rect(
        self,
        box: tuple[int, int, int, int],
        fill: str,
        outline: str,
        width: int = 2,
        radius: int = 8,
    ) -> None:
        self.draw.rounded_rectangle(
            box, radius=radius, fill=fill, outline=outline, width=width
        )
        x1, y1, x2, y2 = box
        self.svg_elements.append(
            f'<rect x="{x1}" y="{y1}" width="{x2 - x1}" height="{y2 - y1}" rx="{radius}" '
            f'fill="{fill}" stroke="{outline}" stroke-width="{width}"/>'
        )

    def save(self, png_path: Path, svg_path: Path) -> None:
        self.image.save(png_path, format="PNG", optimize=True)
        elements = "\n  ".join(self.svg_elements)
        svg = (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.width}" height="{self.height}" '
            f'viewBox="0 0 {self.width} {self.height}">\n'
            f'  <rect width="{self.width}" height="{self.height}" fill="#ffffff"/>\n'
            f"  {elements}\n"
            "</svg>\n"
        )
        svg_path.write_text(svg, encoding="utf-8", newline="\n")


def _draw_panel(
    scene: Scene,
    x_left: int,
    x_right: int,
    title: str,
    values: list[float],
    annotations: list[str],
    x_labels: list[str],
    value_offsets: list[int],
) -> None:
    y_top = 255
    y_bottom = 570
    scene.text(x_left, 175, title, 30, bold=True)
    for tick in (0.0, 0.25, 0.5, 0.75, 1.0):
        y = round(y_bottom - tick * (y_bottom - y_top))
        scene.line(x_left, y, x_right, y, GRID_COLOR, 2)
        scene.text(x_left - 16, y - 10, f"{tick:.2f}", 17, MUTED_COLOR, anchor="ra")
    scene.line(x_left, y_top, x_left, y_bottom, TEXT_COLOR, 3)
    scene.line(x_left, y_bottom, x_right, y_bottom, TEXT_COLOR, 3)

    plot_width = x_right - x_left
    centers = [x_left + plot_width * (index + 1) // 5 for index in range(4)]
    colors = [FULL_COLOR, DIRECT_COLOR, NON_DIRECT_COLOR, BASELINE_COLOR]
    bar_width = 78
    for center, value, annotation, label, color, value_offset in zip(
        centers, values, annotations, x_labels, colors, value_offsets
    ):
        bar_top = round(y_bottom - value * (y_bottom - y_top))
        scene.rounded_rect(
            (center - bar_width // 2, bar_top, center + bar_width // 2, y_bottom),
            color,
            TEXT_COLOR,
            width=2,
            radius=8,
        )
        scene.text(center, bar_top + value_offset, annotation, 19, bold=True, anchor="ma")
        scene.text(center, y_bottom + 23, label, 18, anchor="ma", spacing=4)


def render(values: dict[str, Any]) -> None:
    scene = Scene.create()
    scene.text(
        80,
        55,
        "Figure 3. Multi-leaf localization and construct-sensitive ablation",
        38,
        bold=True,
    )
    scene.text(
        80,
        125,
        "Controlled, explicitly instrumented M/R/N surface; perfect full/direct bars are construct-sensitive",
        22,
        MUTED_COLOR,
    )
    _draw_panel(
        scene,
        155,
        745,
        "Panel A · Macro-F1",
        [
            values["full_macro_f1"],
            values["direct_macro_f1"],
            values["non_direct_macro_f1"],
            values["majority_macro_f1"],
        ],
        ["1.0000", "1.0000", "0.3333 = uniform", "0.1667"],
        ["Full\nvector", "Direct\ncodebook", "Non-direct\nleaves", "Majority\nbaseline"],
        [-33, -33, -33, -33],
    )
    _draw_panel(
        scene,
        915,
        1505,
        "Panel B · Top-1",
        [
            values["full_top1"],
            values["direct_top1"],
            values["non_direct_top1"],
            values["chance_top1"],
        ],
        ["1.0000", "1.0000", "0.3333 = chance", "0.3333"],
        ["Full\nvector", "Direct\ncodebook", "Non-direct\nleaves", "Chance\nbaseline"],
        [-33, -33, -60, -25],
    )

    scene.text(80, 675, "Required caption", 20, bold=True)
    caption = (
        "Perfect full-vector and direct-codebook bars are construct-sensitive on the explicitly instrumented "
        "controlled M/R/N observation surface. After directly targeted checkpoints are removed, non-direct "
        "top-1 equals chance (0.3333); non-direct macro-F1 equals the uniform-class macro-F1 baseline "
        "(0.3333) but remains above the plotted majority macro-F1 baseline (0.1667). The result reflects "
        "stage-aligned instrumentation, not emergent localization from the remaining hierarchy."
    )
    wrapped_caption = "\n".join(textwrap.wrap(caption, width=142))
    scene.text(80, 715, wrapped_caption, 21, spacing=9)
    scene.text(
        80,
        855,
        "Frozen source: multileaf_signature_ablation.json only; no tuning, derived scientific data, or experiment rerun.",
        17,
        MUTED_COLOR,
    )
    scene.save(PNG, SVG)


def update_manifest() -> dict[str, Any]:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    for path in (PNG, SVG):
        manifest["outputs"][path.name] = {
            "bytes": path.stat().st_size,
            "sha256": sha256_file(path),
        }
    MANIFEST.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return {
        PNG.name: manifest["outputs"][PNG.name],
        SVG.name: manifest["outputs"][SVG.name],
    }


def main() -> int:
    values = load_values()
    render(values)
    outputs = update_manifest()
    print(
        json.dumps(
            {
                "ablation_sha256": sha256_file(ABLATION),
                "outputs": outputs,
                "status": "FIGURE_3_REPAIRED_FROM_FROZEN_ABLATION",
                "values": values,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
