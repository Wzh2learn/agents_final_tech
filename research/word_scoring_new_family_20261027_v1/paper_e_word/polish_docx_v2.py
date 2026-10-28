#!/usr/bin/env python3
"""Deterministic Word post-processing for the Paper E revision.

Same interoperability fixes as ``polish_docx.py`` (table grid, borders,
explicit widths, cell margins, Times New Roman cells), plus:

* every table caption and figure caption paragraph gets the ``Caption``
  style with explicit 9 pt black type, so captions are document text and not
  image alt text;
* table rows are marked non-splittable and the header row repeats.

Usage:
    python polish_docx_v2.py --docx paper_e_revision_v2.docx
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from docx import Document
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

CAPTION_RE = re.compile(r"^((?:Table|Figure)\s+\d+\.)\s*(.*)$", re.S)


def set_cell_margins(cell, top=90, start=100, bottom=90, end=100) -> None:
    tc = cell._tc
    tc_pr = tc.get_or_add_tcPr()
    tc_mar = tc_pr.first_child_found_in("w:tcMar")
    if tc_mar is None:
        tc_mar = OxmlElement("w:tcMar")
        tc_pr.append(tc_mar)
    for edge, value in (("top", top), ("start", start), ("bottom", bottom), ("end", end)):
        node = tc_mar.find(qn(f"w:{edge}"))
        if node is None:
            node = OxmlElement(f"w:{edge}")
            tc_mar.append(node)
        node.set(qn("w:w"), str(value))
        node.set(qn("w:type"), "dxa")


def set_table_borders(table, color="BFBFBF", size=4) -> None:
    tbl_pr = table._tbl.tblPr
    borders = tbl_pr.first_child_found_in("w:tblBorders")
    if borders is None:
        borders = OxmlElement("w:tblBorders")
        tbl_pr.append(borders)
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        tag = qn(f"w:{edge}")
        node = borders.find(tag)
        if node is None:
            node = OxmlElement(f"w:{edge}")
            borders.append(node)
        node.set(qn("w:val"), "single")
        node.set(qn("w:sz"), str(size))
        node.set(qn("w:space"), "0")
        node.set(qn("w:color"), color)


def repeat_header_and_keep_rows(table) -> None:
    for index, row in enumerate(table.rows):
        tr_pr = row._tr.get_or_add_trPr()
        if tr_pr.find(qn("w:cantSplit")) is None:
            tr_pr.append(OxmlElement("w:cantSplit"))
        if index == 0 and tr_pr.find(qn("w:tblHeader")) is None:
            tr_pr.append(OxmlElement("w:tblHeader"))


def split_author_paragraph(doc: Document) -> bool:
    for paragraph in doc.paragraphs:
        if paragraph.text.startswith("Author names:"):
            paragraph.clear()
            paragraph.add_run("Author names: TBD_OWNER")
            paragraph.add_run().add_break()
            paragraph.add_run("Affiliations: TBD_OWNER")
            paragraph.add_run().add_break()
            paragraph.add_run("Corresponding author and contact: TBD_OWNER")
            return True
    return False


def polish_tables(doc: Document) -> int:
    for table in doc.tables:
        try:
            table.style = "Table Grid"
        except KeyError:
            pass
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        table.autofit = False
        set_table_borders(table)
        repeat_header_and_keep_rows(table)
        column_count = len(table.columns)
        column_width = Inches(6.5 / max(column_count, 1))
        for column in table.columns:
            column.width = column_width
        for row_index, row in enumerate(table.rows):
            for cell in row.cells:
                cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
                set_cell_margins(cell)
                cell.width = column_width
                for paragraph in cell.paragraphs:
                    paragraph.style = "Normal"
                    paragraph.paragraph_format.space_after = Pt(2)
                    paragraph.paragraph_format.space_before = Pt(0)
                    paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT
                    for run in paragraph.runs:
                        run.font.name = "Times New Roman"
                        rfonts = run._element.get_or_add_rPr().rFonts
                        rfonts.set(qn("w:ascii"), "Times New Roman")
                        rfonts.set(qn("w:hAnsi"), "Times New Roman")
                        run.font.size = Pt(9)
                        if row_index == 0:
                            run.font.bold = True
    return len(doc.tables)


def polish_captions(doc: Document) -> int:
    """Give every caption a real paragraph, bold label + regular body text.

    ``reference_style.docx`` defines ``Caption`` as bold, which turns a
    three-line figure caption into a wall of bold.  Only the ``Table N.`` /
    ``Figure N.`` label keeps the bold weight, which is the usual journal
    convention.
    """
    count = 0
    for paragraph in doc.paragraphs:
        text = paragraph.text.strip()
        match = CAPTION_RE.match(text)
        if not match:
            continue
        label, rest = match.group(1), match.group(2)
        paragraph.clear()
        try:
            paragraph.style = "Caption"
        except KeyError:
            pass
        label_run = paragraph.add_run(label + (" " if rest else ""))
        label_run.font.bold = True
        if rest:
            body_run = paragraph.add_run(rest)
            body_run.font.bold = False
        paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT
        paragraph.paragraph_format.space_before = Pt(6)
        paragraph.paragraph_format.space_after = Pt(4)
        paragraph.paragraph_format.keep_with_next = True
        for run in paragraph.runs:
            run.font.name = "Times New Roman"
            rfonts = run._element.get_or_add_rPr().rFonts
            rfonts.set(qn("w:ascii"), "Times New Roman")
            rfonts.set(qn("w:hAnsi"), "Times New Roman")
            run.font.size = Pt(9)
            run.font.italic = False
            run.font.color.rgb = RGBColor(0, 0, 0)
        count += 1
    return count


def normalise_unknown_styles(doc: Document) -> dict:
    """Drop paragraph-style references that the reference document does not define.

    Pandoc emits ``w:pStyle w:val="Compact"`` for tight-list paragraphs, but
    ``reference_style.docx`` has no ``Compact`` style.  LibreOffice 24.2 then
    discards the whole paragraph properties block, which silently removes the
    list numbering (``w:numPr``) and the bullets.  Removing the dangling
    reference falls back to the document default and keeps numbering intact.
    """
    defined = {style.style_id for style in doc.styles if style.style_id}
    removed: dict[str, int] = {}
    for paragraph in doc.element.body.iter(qn("w:p")):
        ppr = paragraph.find(qn("w:pPr"))
        if ppr is None:
            continue
        pstyle = ppr.find(qn("w:pStyle"))
        if pstyle is None:
            continue
        value = pstyle.get(qn("w:val"))
        if value and value not in defined:
            ppr.remove(pstyle)
            removed[value] = removed.get(value, 0) + 1
    return {"undefined_style_references_removed": removed, "defined_styles": len(defined)}


REFERENCE_RE = re.compile(r"^\[\d+\]\s")


def compact_reference_list(doc: Document) -> int:
    """Set the reference list tight single-spaced.

    Pandoc emits one paragraph per entry with the body paragraph spacing,
    which pushes the last three entries onto a near-empty final page.
    """
    in_refs = False
    count = 0
    for paragraph in doc.paragraphs:
        text = paragraph.text.strip()
        if paragraph.style.name.startswith("Heading") and text.lower() == "references":
            in_refs = True
            continue
        if in_refs and paragraph.style.name.startswith("Heading"):
            in_refs = False
        if in_refs and REFERENCE_RE.match(text):
            fmt = paragraph.paragraph_format
            fmt.space_before = Pt(0)
            fmt.space_after = Pt(0)
            fmt.line_spacing = 1.0
            count += 1
    return count


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--docx", required=True)
    args = ap.parse_args()

    path = Path(args.docx)
    if not path.is_absolute():
        path = Path(__file__).resolve().parent / path
    doc = Document(str(path))
    styles = normalise_unknown_styles(doc)
    author_fixed = split_author_paragraph(doc)
    tables = polish_tables(doc)
    captions = polish_captions(doc)
    refs = compact_reference_list(doc)
    doc.save(str(path))
    print(
        f"polished {path.name}: tables={tables} captions={captions} "
        f"author_block_split={author_fixed} refs={refs} "
        f"removed_styles={styles['undefined_style_references_removed']}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
