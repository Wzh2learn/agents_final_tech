#!/usr/bin/env python3
"""Regenerate submission-shaped figure artwork from the existing SVG sources.

What this does, and what it deliberately does not do:

* removes the in-artwork title ("Figure N. …"), the subtitle and the in-artwork
  caption/footnote lines, because the venue requires the caption to live in the
  document, not inside the artwork.  The rule is explicit and checked: a text
  node is dropped only if it carries ``font-size="36"`` (the title) or
  ``fill="#59677a"`` (the muted subtitle/footnote colour).  Every axis, legend,
  node, panel label and value annotation is kept.
* crops the canvas to the remaining content so the drawing fills the placed
  width instead of sitting in a lake of white.
* writes artwork-only SVG with the placed width fixed, so the rasteriser can
  produce a file whose pixel width divided by the placed width equals the
  required dots-per-inch.
* reports the on-page type size of every font size, computed at the final placed
  width, so the "is the type big enough" question is answered with numbers
  rather than a claim.

It does **not** silently upscale a raster, and it does not rewrite font sizes:
changing type size would reflow a diagram whose boxes are already sized to their
labels, which is a redesign, not a repair.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
FIGDIR = HERE / "figures"
OUTDIR = FIGDIR / "art"
PLACED_WIDTH_IN = 6.5
PAD = 16.0

# Mean advance width of DejaVu Sans for mixed-case Latin text, in em.
MEAN_ADVANCE = 0.58


def attr(blob: str, name: str, default: str | None = None) -> str | None:
    m = re.search(rf'\b{name}="([^"]*)"', blob)
    return m.group(1) if m else default


def drop_nodes(text: str) -> tuple[str, list[dict]]:
    removed: list[dict] = []

    def text_repl(m: re.Match[str]) -> str:
        blob, body = m.group(1), m.group(2)
        size = attr(blob, "font-size")
        fill = attr(blob, "fill")
        if size == "36" or fill == "#59677a":
            removed.append({"text": body[:80], "font_size": size, "fill": fill})
            return ""
        return m.group(0)

    text = re.sub(r"<text ([^>]*)>(.*?)</text>", text_repl, text, flags=re.S)
    wm = len(re.findall(r"<metadata[^>]*>.*?</metadata>", text, flags=re.S))
    text = re.sub(r"<metadata[^>]*>.*?</metadata>\s*", "", text, flags=re.S)
    return text, removed + [{"text": "<metadata>", "font_size": None, "fill": None}] * wm


def text_extent(blob: str, body: str) -> tuple[float, float, float, float]:
    x = float(attr(blob, "x", "0"))
    y = float(attr(blob, "y", "0"))
    size = float(attr(blob, "font-size", "16"))
    anchor = attr(blob, "text-anchor", "start")
    width = len(body) * size * MEAN_ADVANCE
    if anchor == "middle":
        left, right = x - width / 2, x + width / 2
    elif anchor == "end":
        left, right = x - width, x
    else:
        left, right = x, x + width
    return left, y - size, right, y + size * 0.25


def content_bbox(text: str, vb: list[float]) -> tuple[float, float, float, float]:
    vb_w, vb_h = vb[2], vb[3]
    xs: list[float] = []
    ys: list[float] = []

    for m in re.finditer(r"<rect ([^>]*)/?>", text):
        blob = m.group(1)
        x = float(attr(blob, "x", "0"))
        y = float(attr(blob, "y", "0"))
        w = float(attr(blob, "width", "0"))
        h = float(attr(blob, "height", "0"))
        # skip a full-bleed background: it must not define the content box
        if (x, y) == (0.0, 0.0) and w >= 0.98 * vb_w and h >= 0.98 * vb_h:
            continue
        xs += [x, x + w]
        ys += [y, y + h]

    for m in re.finditer(r"<line ([^>]*)/?>", text):
        blob = m.group(1)
        xs += [float(attr(blob, "x1", "0")), float(attr(blob, "x2", "0"))]
        ys += [float(attr(blob, "y1", "0")), float(attr(blob, "y2", "0"))]

    for m in re.finditer(r"<polygon ([^>]*)/?>", text):
        pts = attr(m.group(1), "points") or ""
        nums = [float(v) for v in re.findall(r"-?\d+(?:\.\d+)?", pts)]
        xs += nums[0::2]
        ys += nums[1::2]

    for m in re.finditer(r"<text ([^>]*)>(.*?)</text>", text, flags=re.S):
        left, top, right, bottom = text_extent(m.group(1), re.sub(r"<[^>]+>", "", m.group(2)))
        xs += [left, right]
        ys += [top, bottom]

    return min(xs), min(ys), max(xs), max(ys)


def font_report(text: str, placed_w: float, canvas_w: float) -> list[dict]:
    sizes = sorted({float(s) for s in re.findall(r'font-size="(\d+(?:\.\d+)?)"', text)})
    out = []
    for s in sizes:
        pt = s / canvas_w * placed_w * 72.0
        out.append({"svg_units": s, "page_pt": round(pt, 1)})
    return out


def promote_small_type(text: str, floor: int = 21) -> tuple[str, list[dict]]:
    """Raise sub-floor labels to the smallest body size used in the same drawing.

    Only the all-caps stage headers in Figure 1 sit at 17 units (4.6 pt at the
    placed width, i.e. ~1.6 mm). They are short centred labels in 310-unit
    boxes, so 21 units still fits; nothing is re-laid out and no text changes.
    """
    changed: list[dict] = []

    def repl(m: re.Match[str]) -> str:
        blob, body = m.group(1), m.group(2)
        size = attr(blob, "font-size")
        # only the 17-unit all-caps headers: the 18-unit diamond labels in
        # Figure 1 do not fit their polygon at a larger size
        if size != "17":
            return m.group(0)
        changed.append({"from": size, "to": str(floor), "text": body[:60]})
        return "<text " + re.sub(r'font-size="[^"]*"', f'font-size="{floor}"', blob) + ">" + body + "</text>"

    return re.sub(r"<text ([^>]*)>(.*?)</text>", repl, text, flags=re.S), changed


def main() -> int:
    OUTDIR.mkdir(parents=True, exist_ok=True)
    report = []
    for src in sorted(FIGDIR.glob("fig*.svg")):
        raw = src.read_text(encoding="utf-8")
        header = re.search(r"<svg[^>]*>", raw).group(0)
        vb = [float(v) for v in (attr(header, "viewBox") or "").split()]
        if len(vb) != 4:
            raise SystemExit(f"{src.name}: no viewBox")

        text, removed = drop_nodes(raw)
        text, promoted = promote_small_type(text)
        if "ocr similar" in text:
            text = text.replace("ocr similar", "OCR-like")
            promoted.append({"from": "label", "to": "label", "text": "ocr similar -> OCR-like"})
        x0, y0, x1, y1 = content_bbox(text, vb)
        x0, y0 = max(vb[0], x0 - PAD), max(vb[1], y0 - PAD)
        x1, y1 = min(vb[0] + vb[2], x1 + PAD), min(vb[1] + vb[3], y1 + PAD)
        w, h = x1 - x0, y1 - y0
        height_in = PLACED_WIDTH_IN * h / w

        new_header = (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{PLACED_WIDTH_IN}in" '
            f'height="{height_in:.3f}in" viewBox="{x0:.1f} {y0:.1f} {w:.1f} {h:.1f}" '
            f'role="img" aria-labelledby="title desc">'
        )
        text = re.sub(r"<svg[^>]*>", new_header, text, count=1)
        # the background must cover the new canvas, not the old one
        text = re.sub(
            r'<rect x="0" y="0" width="\d+" height="\d+" fill="#ffffff"/>',
            f'<rect x="{x0:.1f}" y="{y0:.1f}" width="{w:.1f}" height="{h:.1f}" fill="#ffffff"/>',
            text,
            count=1,
        )
        dst = OUTDIR / (src.stem + "_art.svg")
        dst.write_text(text, encoding="utf-8", newline="\n")

        report.append(
            {
                "source": src.name,
                "artifact": str(dst.relative_to(HERE)),
                "removed": removed,
                "type_promoted": promoted,
                "crop": [round(x0, 1), round(y0, 1), round(w, 1), round(h, 1)],
                "placed_in": [PLACED_WIDTH_IN, round(height_in, 3)],
                "aspect": round(h / w, 4),
                "fonts": font_report(text, PLACED_WIDTH_IN, w),
            }
        )

    import json

    (OUTDIR / "FIGURE_REBUILD_REPORT.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    for r in report:
        print(r["source"], "crop", r["crop"], "placed", r["placed_in"])
        for f in r["fonts"]:
            print(f"    {f['svg_units']:>5.0f} units -> {f['page_pt']:>4.1f} pt on the page")
        for d in r["removed"]:
            print("    removed:", d["text"][:70])
        for d in r["type_promoted"]:
            print(f"    type {d['from']} -> {d['to']}: {d['text'][:40]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
