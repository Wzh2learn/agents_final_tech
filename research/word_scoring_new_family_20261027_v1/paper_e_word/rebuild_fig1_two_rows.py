#!/usr/bin/env python3
"""Redraw Figure 1 as a two-row, numbered flow so the reading order is explicit.

The previous artwork was a single row of five 310-unit boxes.  At the placed
width that forced 5.7 pt labels, and the fifth node was a diamond whose inner
text overflowed the outline.  This generator rebuilds the same five stages with
the same wording as a 3 + 2 layout:

* larger relative type (the canvas is ~40% narrower for the same content),
* numbered steps and a elbow arrow so the reading order does not depend on
  guessing,
* the outcome node is a rounded box rather than a diamond, because a diamond
  cannot hold three lines at any legible size.

Nothing is added to or removed from the argument: the labels are the ones from
the previous figure.
"""

from __future__ import annotations

import json
from pathlib import Path

OUT = Path(__file__).resolve().parent / "figures" / "art"
W, H = 1460, 700
BOX_W, BOX_H = 430, 200
R = 14

STAGES = [
    ("1", "MOTIVATION", ["Measurement-effectiveness", "motivation", "NIST / long-horizon service"]),
    ("2", "CONTROLLED FAILURE", ["Controlled failure state", "Staged pipeline", "perturbation"]),
    ("3", "VISIBILITY", ["Checkpoint visibility", "Did any instrument", "observe the failure?"]),
    ("4", "DETECTION", ["Protocol detection", "Did the decision rule", "use that observation?"]),
    ("5", "OUTCOME / HARM", ["Outcome / harm", "Consequence under", "stated contract?"]),
]

ROW1_Y, ROW2_Y = 70, 400
ROW1_X = [40, 515, 990]
ROW2_X = [278, 753]

HEAD = 26
BODY = 24
NUM = 26


def box(x: int, y: int, step: str, title: str, lines: list[str], accent: bool) -> str:
    fill = "#f3f7fb" if not accent else "#fdf6ec"
    stroke = "#172033" if not accent else "#8a5a1e"
    out = [
        f'<rect x="{x}" y="{y}" width="{BOX_W}" height="{BOX_H}" rx="{R}" ry="{R}" '
        f'fill="{fill}" stroke="{stroke}" stroke-width="3"/>',
        f'<circle cx="{x+30}" cy="{y+30}" r="17" fill="{stroke}"/>',
        f'<text x="{x+30}" y="{y+39}" fill="#ffffff" font-family="DejaVu Sans" '
        f'font-size="{NUM}" font-weight="700" text-anchor="middle">{step}</text>',
        f'<text x="{x+58}" y="{y+39}" fill="{stroke}" font-family="DejaVu Sans" '
        f'font-size="{HEAD}" font-weight="700" text-anchor="start">{title}</text>',
    ]
    for i, line in enumerate(lines):
        out.append(
            f'<text x="{x+BOX_W/2:.0f}" y="{y+92+i*34}" fill="#172033" '
            f'font-family="DejaVu Sans" font-size="{BODY}" text-anchor="middle">{line}</text>'
        )
    return "\n".join(out)


def arrow(x1: int, y1: int, x2: int, y2: int) -> str:
    return (f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#172033" '
            f'stroke-width="3" marker-end="url(#a)"/>')


def main() -> int:
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="6.5in" '
        f'height="{6.5*H/W:.3f}in" viewBox="0 0 {W} {H}" role="img" '
        f'aria-labelledby="title desc">',
        "<title>Measurement chain</title>",
        "<desc>Five numbered stages in two rows: motivation, controlled failure, "
        "visibility, detection, outcome and harm.</desc>",
        "<defs><marker id=\"a\" viewBox=\"0 0 10 10\" refX=\"9\" refY=\"5\" "
        "markerWidth=\"6\" markerHeight=\"6\" orient=\"auto-start-reverse\">"
        "<path d=\"M 0 0 L 10 5 L 0 10 z\" fill=\"#172033\"/></marker></defs>",
        f'<rect x="0" y="0" width="{W}" height="{H}" fill="#ffffff"/>',
    ]
    ys = [ROW1_Y, ROW1_Y, ROW1_Y, ROW2_Y, ROW2_Y]
    xs = ROW1_X + ROW2_X
    for (step, title, lines), x, y in zip(STAGES, xs, ys):
        parts.append(box(x, y, step, title, lines, accent=(step == "5")))

    # 1 -> 2 -> 3 across the top row
    for i in range(2):
        parts.append(arrow(ROW1_X[i] + BOX_W + 6, ROW1_Y + BOX_H // 2 - 30,
                           ROW1_X[i + 1] - 6, ROW1_Y + BOX_H // 2 - 30))
    # 3 -> 4: down the right edge, then left into the second row
    x3r = ROW1_X[2] + BOX_W // 2
    x4c = ROW2_X[0] + BOX_W // 2
    parts.append(f'<polyline points="{x3r},{ROW1_Y+BOX_H+4} {x3r},{ROW2_Y-60} '
                 f'{x4c},{ROW2_Y-60} {x4c},{ROW2_Y-8}" fill="none" stroke="#172033" '
                 f'stroke-width="3" marker-end="url(#a)"/>')
    parts.append(f'<text x="{x4c+14}" y="{ROW2_Y-68}" fill="#59677a" '
                 f'font-family="DejaVu Sans" font-size="20">continues</text>')
    # 4 -> 5
    parts.append(arrow(ROW2_X[0] + BOX_W + 6, ROW2_Y + BOX_H // 2 - 30,
                       ROW2_X[1] - 6, ROW2_Y + BOX_H // 2 - 30))
    parts.append("</svg>")

    OUT.mkdir(parents=True, exist_ok=True)
    svg = "\n".join(parts) + "\n"
    (OUT / "fig1_measurement_chain_art.svg").write_text(svg, encoding="utf-8", newline="\n")

    # type size on the page, at the two widths this paper can use
    for placed in (6.5, 7.16, 3.5):
        print(f"placed {placed} in -> body {BODY/W*placed*72:.1f} pt, "
              f"title {HEAD/W*placed*72:.1f} pt")
    (OUT / "FIG1_RELAYOUT.json").write_text(json.dumps({
        "canvas": [W, H], "boxes": {"w": BOX_W, "h": BOX_H, "radius": R},
        "font_units": {"title": HEAD, "body": BODY, "step": NUM},
        "page_pt_at_placed_width": {str(p): round(BODY / W * p * 72, 1) for p in (3.5, 6.5, 7.16)},
        "change": "single row + diamond -> two rows (3+2) + numbered rounded boxes",
        "labels": [t[1] for t in STAGES],
    }, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
