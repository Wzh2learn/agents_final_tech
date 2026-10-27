#!/usr/bin/env python3
"""Apply deterministic Word table and author-layout fixes after Pandoc."""

from __future__ import annotations

import sys
from pathlib import Path

from docx import Document
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt


ROOT = Path(__file__).resolve().parent
DOCX = ROOT / "paper_e.docx"


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


def set_table_borders(table) -> None:
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
        node.set(qn("w:sz"), "4")
        node.set(qn("w:space"), "0")
        node.set(qn("w:color"), "D9D9D9")


def split_author_paragraph(doc: Document) -> None:
    for paragraph in doc.paragraphs:
        if paragraph.text.startswith("Author names:"):
            paragraph.clear()
            paragraph.add_run("Author names: TBD_OWNER")
            paragraph.add_run().add_break()
            paragraph.add_run("Affiliations: TBD_OWNER")
            paragraph.add_run().add_break()
            paragraph.add_run("Corresponding author and contact: TBD_OWNER")
            return


def polish_tables(doc: Document) -> None:
    for table in doc.tables:
        try:
            table.style = "Table Grid"
        except KeyError:
            pass
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        table.autofit = False
        set_table_borders(table)
        column_count = len(table.columns)
        column_width = Inches(6.5 / max(column_count, 1))
        for column in table.columns:
            column.width = column_width
        for row in table.rows:
            for index, cell in enumerate(row.cells):
                cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
                set_cell_margins(cell)
                cell.width = column_width
                for paragraph in cell.paragraphs:
                    paragraph.style = "Normal"
                    paragraph.paragraph_format.space_after = Pt(2)
                    for run in paragraph.runs:
                        run.font.name = "Times New Roman"
                        run._element.get_or_add_rPr().rFonts.set(qn("w:ascii"), "Times New Roman")
                        run._element.get_or_add_rPr().rFonts.set(qn("w:hAnsi"), "Times New Roman")
                        run.font.size = Pt(9)


def main() -> int:
    doc = Document(DOCX)
    split_author_paragraph(doc)
    polish_tables(doc)
    doc.save(DOCX)
    print(DOCX)
    return 0


if __name__ == "__main__":
    sys.exit(main())
