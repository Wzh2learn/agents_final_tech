#!/usr/bin/env python3
"""Build an IJCNN 2027 submission draft: IEEE-style two columns, full-width figures.

IJCNN 2027 requires double column, single spaced, 10 pt Times Roman, Letter,
PDF only, no page numbers, **double-blind**, and it allows 6 pages plus up to
four extra pages at $100 each.  Word cannot float a figure across columns, so
each figure is placed in its own one-column section, which is the Word
equivalent of a `figure*` float.

The content is the same production source as the internal draft; only the
author block (anonymised), the page geometry and the figure placement change.

Usage:
    python build_ijcnn_draft.py --src paper_e_revision_v4.md --out paper_e_ijcnn2027_submission.docx
"""

from __future__ import annotations

import argparse
import copy
import subprocess
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt

HERE = Path(__file__).resolve().parent
PANDOC = "D:/pandocLatex2word/pandoc.exe"


def anonymise(src: Path, dst: Path) -> None:
    text = src.read_text(encoding="utf-8")
    import re as _re
    pattern = _re.compile(
        r"Author names: TBD_OWNER\s*\n\s*Affiliations: TBD_OWNER\s*\n"
        r"\s*Corresponding author and contact: TBD_OWNER\n")
    text, n = pattern.subn("Anonymous Authors\n", text)
    if n != 1:
        raise SystemExit(f"author block not found ({n} matches)")
    # double-blind: point at the anonymised marker
    text = text.replace("**Author names, affiliations and corresponding details:** TBD_OWNER.",
                        "**Author names, affiliations and corresponding details:** withheld for double-blind review.")
    dst.write_text(text, encoding="utf-8", newline="\n")


def set_cols(sect_pr, num: int, space_twips: int = 360) -> None:
    """Set the column count, keeping the CT_SectPr child order valid.

    ``w:cols`` must precede ``w:docGrid``; appending it at the end makes the
    section invalid and LibreOffice silently falls back to one column.
    """
    cols = sect_pr.find(qn("w:cols"))
    if cols is None:
        cols = OxmlElement("w:cols")
        anchor = None
        for tag in ("w:formProt", "w:vAlign", "w:noEndnote", "w:titlePg",
                    "w:textDirection", "w:bidi", "w:rtlGutter", "w:docGrid",
                    "w:printerSettings", "w:sectPrChange"):
            anchor = sect_pr.find(qn(tag))
            if anchor is not None:
                break
        if anchor is not None:
            anchor.addprevious(cols)
        else:
            sect_pr.append(cols)
    cols.set(qn("w:num"), str(num))
    cols.set(qn("w:space"), str(space_twips))
    cols.set(qn("w:equalWidth"), "1")


def geometry(doc: Document) -> None:
    for sec in doc.sections:
        sec.page_width = Inches(8.5)
        sec.page_height = Inches(11)
        sec.left_margin = Inches(0.62)
        sec.right_margin = Inches(0.62)
        sec.top_margin = Inches(0.75)
        sec.bottom_margin = Inches(1.0)
        set_cols(sec._sectPr, 2)


def style_body(doc: Document) -> None:
    for name in ("Normal", "Body Text", "First Paragraph", "Compact"):
        try:
            st = doc.styles[name]
        except KeyError:
            continue
        st.font.name = "Times New Roman"
        st.font.size = Pt(10)
        pf = st.paragraph_format
        pf.space_before = Pt(0)
        pf.space_after = Pt(0)
        pf.line_spacing = 1.0


def full_width_figures(doc: Document) -> int:
    """Wrap every drawing paragraph (plus its caption) in a one-column section."""
    body = doc.element.body
    paras = list(doc.paragraphs)
    wrapped = 0
    for i, para in enumerate(paras):
        if not para._p.findall(".//" + qn("w:drawing")):
            continue
        caption = paras[i + 1] if i + 1 < len(paras) else None
        base = copy.deepcopy(doc.sections[0]._sectPr)

        before = OxmlElement("w:p")
        pPr = OxmlElement("w:pPr")
        s1 = copy.deepcopy(base)
        # a sectPr stores the properties of the section it *ends*, so the break
        # before a figure must close a two-column text section
        set_cols(s1, 2)
        cont = OxmlElement("w:type")
        cont.set(qn("w:val"), "continuous")
        s1.insert(0, cont)
        pPr.append(s1)
        before.append(pPr)
        para._p.addprevious(before)

        after = OxmlElement("w:p")
        pPr2 = OxmlElement("w:pPr")
        s2 = copy.deepcopy(base)
        # and the break after it closes the one-column figure section
        set_cols(s2, 1)
        cont2 = OxmlElement("w:type")
        cont2.set(qn("w:val"), "continuous")
        s2.insert(0, cont2)
        pPr2.append(s2)
        after.append(pPr2)
        (caption._p if caption is not None else para._p).addnext(after)

        for p in (para, caption):
            if p is None:
                continue
            for run in p.runs:
                run.font.name = "Times New Roman"
                run.font.size = Pt(8)
        para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        wrapped += 1
    return wrapped


def widen_images(doc: Document, width_in: float) -> None:
    for shape in doc.inline_shapes:
        ratio = shape.height / shape.width if shape.width else 0.5
        shape.width = Inches(width_in)
        shape.height = Inches(width_in * ratio)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default="paper_e_revision_v4.md")
    ap.add_argument("--out", default="paper_e_ijcnn2027_submission.docx")
    args = ap.parse_args()
    src, out = HERE / args.src, HERE / args.out
    sub_md = HERE / "paper_e_ijcnn2027_submission.md"
    anonymise(src, sub_md)

    cmd = [PANDOC, str(sub_md), "--from=markdown+pipe_tables+tex_math_dollars",
           "--resource-path=.", f"--reference-doc={HERE/'reference_style.docx'}",
           "-o", str(out)]
    res = subprocess.run(cmd, cwd=HERE, capture_output=True, text=True)
    if res.returncode != 0:
        raise SystemExit(f"pandoc failed: {res.stderr[:400]}")

    doc = Document(str(out))
    geometry(doc)
    style_body(doc)
    widen_images(doc, 7.1)
    n = full_width_figures(doc)
    doc.save(str(out))
    print(f"built {out.name}: {n} figures wrapped full width")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
