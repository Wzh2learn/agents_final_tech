#!/usr/bin/env python3
"""Preprocess Outlook .msg files for the M1 statement pipeline.

Extracts from each .msg:
  - subject / body (plain text, saved as <stem>_body.txt)
  - attachments (saved under <out-dir>/attachments/, classified by type)
  - URLs found in the body (recorded only, NEVER auto-downloaded)

Outputs <out-dir>/manifest.json with a per-msg summary. The manifest and
extracted files may contain sensitive client data: keep them out of git
(same policy as ~/wzh/m1_samples).

Usage:
  python scripts/preprocess_msg.py --input-dir /path/to/msgs --out-dir /path/to/out

Classification (drives downstream routing):
  pdf   -> M1 parser directly (OCR fallback handled by the parser)
  image -> OCR path (vision-8004; PaddleOCR SIGSEGV on ARM64, do not use)
  other -> recorded as skipped, human decides
CID inline images are saved via attachment.save() like any other attachment.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

try:
    import extract_msg
except ImportError:
    sys.exit("extract_msg not installed: pip install extract-msg")

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp", ".gif", ".webp"}
URL_RE = re.compile(r"https?://[^\s<>\"'\u3000\uff09\uff08]+")


def classify(name: str) -> str:
    ext = Path(name).suffix.lower()
    if ext == ".pdf":
        return "pdf"
    if ext in IMAGE_EXTS:
        return "image"
    return "other"


def safe_name(name: str) -> str:
    """Keep CJK but remove path separators and control chars."""
    return re.sub(r"[\x00-\x1f/\\]", "_", name or "unnamed").strip() or "unnamed"


def process_msg(path: Path, out_dir: Path, att_dir: Path) -> dict:
    msg = extract_msg.Message(str(path))
    try:
        subject = (msg.subject or "").strip()
        body = msg.body or ""
        # HTML bodies: extract_msg exposes html; keep raw for the HTML email parser
        html = msg.html
        if html and isinstance(html, bytes):
            html = html.decode("utf-8", errors="replace")

        stem = safe_name(path.stem)
        body_path = out_dir / f"{stem}_body.txt"
        body_path.write_text(body, encoding="utf-8")

        urls = sorted(set(URL_RE.findall(body)))

        attachments = []
        for att in msg.attachments:
            name = safe_name(att.long_filename or att.short_filename or "attachment")
            dest = att_dir / f"{stem}_{name}"
            kind = classify(name)
            entry = {
                "filename": name,
                "saved_as": str(dest.relative_to(out_dir)),
                "kind": kind,
                "cid": getattr(att, "cid", None) or None,
                "route": {"pdf": "m1-parser", "image": "ocr-vision-8004",
                          "other": "skipped-record"}[kind],
            }
            try:
                att.save(str(dest))
                entry["bytes"] = dest.stat().st_size
            except Exception as e:  # noqa: BLE001 - record and continue
                entry["error"] = str(e)[:200]
            attachments.append(entry)

        kinds = {a["kind"] for a in attachments if "error" not in a}
        return {
            "msg_file": path.name,
            "subject": subject,
            "body_file": str(body_path.relative_to(out_dir)),
            "body_chars": len(body),
            "has_html_body": bool(html),
            "urls": urls,
            "url_note": "recorded only - human confirms before any download",
            "attachments": attachments,
            "needs_ocr_hint": bool(kinds) and kinds <= {"image"},
        }
    finally:
        msg.close()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input-dir", required=True, help="directory containing .msg files")
    ap.add_argument("--out-dir", required=True, help="output directory (attachments + manifest)")
    args = ap.parse_args()

    in_dir = Path(args.input_dir).expanduser()
    out_dir = Path(args.out_dir).expanduser()
    att_dir = out_dir / "attachments"
    att_dir.mkdir(parents=True, exist_ok=True)

    msgs = sorted(in_dir.glob("*.msg"))
    if not msgs:
        print(f"no .msg files under {in_dir}", file=sys.stderr)
        return 1

    manifest = {"input_dir": str(in_dir), "count": len(msgs), "items": []}
    for p in msgs:
        print(f"[preprocess_msg] {p.name}", file=sys.stderr)
        try:
            manifest["items"].append(process_msg(p, out_dir, att_dir))
        except Exception as e:  # noqa: BLE001
            manifest["items"].append({"msg_file": p.name, "error": str(e)[:200]})

    mpath = out_dir / "manifest.json"
    mpath.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    n_att = sum(len(i.get("attachments", [])) for i in manifest["items"])
    n_url = sum(len(i.get("urls", [])) for i in manifest["items"])
    print(f"[preprocess_msg] {len(msgs)} msgs, {n_att} attachments, {n_url} urls recorded")
    print(f"[preprocess_msg] manifest: {mpath}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
