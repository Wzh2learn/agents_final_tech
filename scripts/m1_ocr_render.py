#!/usr/bin/env python3
"""M1 OCR 兜底 · Phase 0/1 准备：把纯图样本渲染/抽取为 /tmp PNG。

纯准备步骤：无模型、无网络。用项目 venv 运行（含 PyMuPDF + python-docx）。
样本只通过绝对路径 ~/wzh/m1_samples 读取，绝不复制进项目；产物只写 /tmp。
输出 manifest.json 供 scripts/m1_ocr_fallback.py（wzh_vision 环境）消费。

判定「纯图」：
  - PDF：所有页 get_text 为空；逐页渲染为 PNG（PyMuPDF，长边封顶 max-edge）。
  - DOCX：无段落文本且无表格，但 word/media 有图片；抽取内嵌图片 blob 存 PNG。

用法:
    ./venv/bin/python scripts/m1_ocr_render.py [--samples-dir DIR] [--out-dir /tmp/m1_ocr] [--max-edge 2048]
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

try:
    import fitz  # PyMuPDF
except Exception:  # pragma: no cover
    fitz = None

try:
    import docx  # python-docx
except Exception:  # pragma: no cover
    docx = None

try:
    from PIL import Image
except Exception:  # pragma: no cover
    Image = None

DEFAULT_SAMPLES_DIR = os.path.expanduser("~/wzh/m1_samples")
DEFAULT_OUT_DIR = "/tmp/m1_ocr"


def _cap_size(img: "Image.Image", max_edge: int) -> "Image.Image":
    """等比缩放使长边 <= max_edge（PIL 缺失或无需缩放时原样返回）。"""
    if Image is None:
        return img
    w, h = img.size
    longest = max(w, h)
    if longest <= max_edge:
        return img
    scale = max_edge / float(longest)
    return img.resize((max(1, int(w * scale)), max(1, int(h * scale))), Image.LANCZOS)


def render_pdf(pdf_path: Path, out_dir: Path, max_edge: int) -> list[dict]:
    """渲染 image-only PDF 的每一页为 PNG，返回 manifest 条目。"""
    entries: list[dict] = []
    doc = fitz.open(str(pdf_path))
    text_chars = sum(len(page.get_text().strip()) for page in doc)
    if text_chars > 0:
        return entries  # 非纯图，跳过
    stem = pdf_path.stem
    for pno in range(doc.page_count):
        page = doc[pno]
        rect = page.rect
        longest = max(rect.width, rect.height)
        zoom = min(max_edge / longest, 4.0) if longest > 0 else 1.0
        pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False)
        png = out_dir / f"{stem}__p{pno}.png"
        pix.save(str(png))
        entries.append({
            "sample": stem,
            "source": pdf_path.name,
            "kind": "pdf_page",
            "unit": f"p{pno}",
            "png": str(png),
            "png_basename": png.name,
            "width": pix.width,
            "height": pix.height,
            "render_zoom": round(zoom, 4),
        })
    return entries


def extract_docx(docx_path: Path, out_dir: Path, max_edge: int) -> list[dict]:
    """抽取 image-only DOCX 的内嵌图片 blob 为 PNG，返回 manifest 条目。"""
    entries: list[dict] = []
    if docx is None:
        return entries
    d = docx.Document(str(docx_path))
    para_text = "\n".join(p.text.strip() for p in d.paragraphs if p.text.strip())
    if para_text or d.tables:
        return entries  # 非纯图，跳过
    stem = docx_path.stem
    # 通过 package parts 读内嵌媒体（python-docx 官方 part 接口）
    pkg = d.part.package
    idx = 0
    for part in pkg.iter_parts():
        name = str(part.partname)
        if "/media/" not in name:
            continue
        ext = os.path.splitext(name)[1].lower()
        if ext not in {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff", ".webp", ".gif"}:
            continue
        idx += 1
        blob = part.blob
        if Image is not None:
            import io
            img = Image.open(io.BytesIO(blob)).convert("RGB")
            img = _cap_size(img, max_edge)
            png = out_dir / f"{stem}__img{idx}.png"
            img.save(str(png))
            w, h = img.size
        else:  # pragma: no cover
            png = out_dir / f"{stem}__img{idx}{ext}"
            png.write_bytes(blob)
            w = h = -1
        entries.append({
            "sample": stem,
            "source": docx_path.name,
            "kind": "docx_image",
            "unit": f"img{idx}",
            "png": str(png),
            "png_basename": png.name,
            "width": w,
            "height": h,
            "media_part": name,
        })
    return entries


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="渲染纯图 M1 样本为 /tmp PNG（无模型）")
    ap.add_argument("--samples-dir", default=DEFAULT_SAMPLES_DIR)
    ap.add_argument("--out-dir", default=DEFAULT_OUT_DIR)
    ap.add_argument("--max-edge", type=int, default=2048)
    args = ap.parse_args(argv)

    if fitz is None:
        print("ERROR: PyMuPDF(fitz) unavailable in this interpreter", file=sys.stderr)
        return 2
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    samples = Path(args.samples_dir)

    entries: list[dict] = []
    scanned: list[dict] = []
    for path in sorted(samples.iterdir()):
        ext = path.suffix.lower()
        if ext == ".pdf":
            before = len(entries)
            entries += render_pdf(path, out_dir, args.max_edge)
            scanned.append({"file": path.name, "image_only": len(entries) > before,
                            "units": len(entries) - before})
        elif ext == ".docx":
            before = len(entries)
            entries += extract_docx(path, out_dir, args.max_edge)
            scanned.append({"file": path.name, "image_only": len(entries) > before,
                            "units": len(entries) - before})

    manifest = {
        "samples_dir": str(samples),
        "out_dir": str(out_dir),
        "max_edge": args.max_edge,
        "scanned": scanned,
        "images": entries,
    }
    manifest_path = out_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"libs: fitz={fitz is not None} docx={docx is not None} PIL={Image is not None}")
    print(f"scanned {len(scanned)} pdf/docx samples:")
    for s in scanned:
        flag = "IMAGE-ONLY" if s["image_only"] else "has-text"
        print(f"  - {s['file']:36} {flag:10} units={s['units']}")
    print(f"rendered {len(entries)} images -> {out_dir}")
    for e in entries:
        print(f"  - {e['png_basename']:40} {e['width']}x{e['height']}")
    print(f"manifest: {manifest_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
