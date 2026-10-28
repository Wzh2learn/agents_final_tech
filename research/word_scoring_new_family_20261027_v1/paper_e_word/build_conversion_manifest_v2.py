#!/usr/bin/env python3
"""Build CONVERSION_MANIFEST_V2.json and D_PAGE_HASHES_V2.sha256.

Hashes text artifacts from their **raw Git blob bytes**, never from the
Windows working copy. This clone runs with ``core.autocrlf=true``, so the
working tree holds CRLF while the blob holds LF; a hash taken from the working
tree is a checkout-policy value, not an artifact identity. The working-tree
hash is recorded separately, and the pair is marked ``CRLF_CHECKOUT_ONLY``
when the two differ only by line endings.

Run after committing the artifacts you want to describe.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
BASE = "research/word_scoring_new_family_20261027_v1/paper_e_word/"


def blob(rel: str) -> tuple[str, bytes]:
    oid = subprocess.run(
        ["git", "rev-parse", f"HEAD:{rel}"], cwd=REPO, capture_output=True, text=True
    ).stdout.strip()
    if not oid:
        raise SystemExit(f"not in HEAD: {rel}")
    raw = subprocess.run(
        ["git", "cat-file", "blob", oid], cwd=REPO, capture_output=True
    ).stdout
    return oid, raw


def describe(rel: str) -> dict:
    oid, raw = blob(rel)
    rec = {
        "path": rel,
        "git_blob_oid": oid,
        "raw_blob_sha256": hashlib.sha256(raw).hexdigest(),
        "bytes": len(raw),
    }
    local = REPO / rel
    if local.is_file():
        wt = local.read_bytes()
        rec["worktree_sha256"] = hashlib.sha256(wt).hexdigest()
        if wt == raw:
            rec["worktree_vs_blob"] = "IDENTICAL"
        elif wt.replace(b"\r\n", b"\n") == raw:
            rec["worktree_vs_blob"] = "CRLF_CHECKOUT_ONLY"
        else:
            rec["worktree_vs_blob"] = "CONTENT_DIFFERS"
    return rec


def main() -> int:
    rev = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=REPO, capture_output=True, text=True
    ).stdout.strip()

    pages = sorted((HERE / "rendered_v2").glob("page-*.png"))
    if not pages:
        raise SystemExit("no rendered pages")

    # sha256sum-compatible, relative to this directory
    lines = []
    for p in pages:
        lines.append(f"{hashlib.sha256(p.read_bytes()).hexdigest()}  rendered_v2/{p.name}")
    pdf = HERE / "rendered_v2" / "paper_e_revision_v2.pdf"
    lines.append(f"{hashlib.sha256(pdf.read_bytes()).hexdigest()}  rendered_v2/{pdf.name}")
    # newline="" keeps LF so `sha256sum -c` works on a Windows checkout
    with (HERE / "D_PAGE_HASHES_V2.sha256").open("w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines) + "\n")

    text_files = [
        "paper_e_revision_v2.md",
        "build_revision_v2.py",
        "polish_docx_v2.py",
        "verify_revision_v2.py",
        "BUILD_COMMANDS_V2.md",
        "D_REVISION_NOTES_20261028.md",
        "SNCS_GUIDELINE_CHECK_20261028.md",
        "C_RESPONSE_AND_DISPOSITION_20261028.md",
    ]
    artifacts = {}
    for name in text_files:
        rel = BASE + name
        try:
            artifacts[name] = describe(rel)
        except SystemExit:
            artifacts[name] = {"path": rel, "status": "NOT_YET_COMMITTED"}

    binary = {}
    for name, ext in (
        ("paper_e_revision_v2.docx", None),
        ("rendered_v2/paper_e_revision_v2.pdf", None),
    ):
        rel = BASE + name
        try:
            binary[name] = describe(rel)
        except SystemExit:
            binary[name] = {"path": rel, "status": "NOT_YET_COMMITTED"}

    figures = {}
    for name in (
        "fig1_measurement_chain.png",
        "fig2_family_visibility_matrix.png",
        "fig3_localization_ablation.png",
    ):
        rel = BASE + "figures/" + name
        oid, raw = blob(rel)
        w, h = int.from_bytes(raw[16:20], "big"), int.from_bytes(raw[20:24], "big")
        figures[name] = {
            "git_blob_oid": oid,
            "raw_blob_sha256": hashlib.sha256(raw).hexdigest(),
            "pixels": f"{w}x{h}",
            "effective_dpi_at_6_5in": round(w / 6.5, 1),
            "png_pHYs_present": b"pHYs" in raw,
            "status": "BELOW_300_DPI_AND_CARRIES_IN_TITLE",
        }

    frozen = {}
    for name, rel in (
        ("paper_e_word.md", BASE + "paper_e_word.md"),
        ("references.bib", BASE + "references.bib"),
        ("reference_style.docx", BASE + "reference_style.docx"),
        (
            "canonical_tex",
            "research/adaptive_mechanism_20261027_v1/paper_e_formal_build/paper_e_sncs.tex",
        ),
    ):
        oid, raw = blob(rel)
        frozen[name] = {
            "path": rel,
            "git_blob_oid": oid,
            "raw_blob_sha256": hashlib.sha256(raw).hexdigest(),
            "modified": False,
        }

    manifest = {
        "schema": "paper_e_word_conversion_manifest_v2",
        "date": "2026-10-28",
        "bound_to_commit": rev,
        "bound_to_note": "Commit at build time. Only this manifest file differs between that commit and the one carrying it; every artifact hash above matches the blobs at that commit.",
        "status": "RENDERED_AND_PAGE_CHECKED_NOT_SUBMITTED",
        "hash_rule": (
            "raw_blob_sha256 is the identity value. worktree_sha256 is recorded "
            "separately because core.autocrlf=true makes the Windows checkout CRLF; "
            "a pair marked CRLF_CHECKOUT_ONLY differs only by line endings."
        ),
        "production_source": {
            "path": BASE + "paper_e_revision_v2.md",
            "role": "single editable body; DOCX and PDF derive from this file only",
        },
        "frozen_inputs": frozen,
        "artifacts": artifacts,
        "outputs": binary,
        "figures": figures,
        "tools": {
            "pandoc": "3.2.1 at D:/pandocLatex2word/pandoc.exe",
            "pandoc_from": "markdown+pipe_tables+tex_math_dollars",
            "libreoffice": "24.2.7.2 at /usr/bin/soffice on GB10, fresh -env:UserInstallation per render",
            "pdftoppm": "/usr/bin/pdftoppm -png -r 120",
            "python_docx": "python-docx in an isolated venv outside the repository",
        },
        "document_counts": {
            "tables": 4,
            "table_shapes": ["6x3", "3x3", "4x4", "7x5"],
            "figures": 3,
            "references": 24,
            "checklist_steps": 6,
            "contributions": 3,
            "abstract_part_labels": 4,
            "tbd_owner_placeholders": 10,
            "numbered_headings": 32,
            "pages": len(pages),
        },
        "open_venue_items": {
            "figure_resolution": "246-277 dpi at 6.5 in, no pHYs; venue asks >=300 dpi",
            "figure_in_artwork_titles": "all three PNGs draw their own title and subtitle",
            "declaration_placeholders": "Funding / Competing interests / Authors' contributions are TBD_OWNER",
        },
        "boundary": (
            "Internal Word-route revision acceptance after one fixed-snapshot C review. "
            "Not publisher formatting acceptance, not submission, not school recognition."
        ),
    }
    (HERE / "CONVERSION_MANIFEST_V2.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({"commit": rev, "pages": len(pages)}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
