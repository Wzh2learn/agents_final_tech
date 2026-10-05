"""Rendering-contract tests for the teacher-review DOCX builder.

These cover two defects found in the 2026-09-25 Office visual pass: display formulas were
emitted as raw LaTeX, and a table row could break across a page boundary mid-cell.
"""
from __future__ import annotations

import time

from docx import Document

from research.build_teacher_review_docx import SOURCE, add_markdown_table, build, render_math

FORMULA_S = r"S(n)=\sum_{c\in C(n)} \frac{w(c)}{\sum_{j\in C(n)}w(j)}S(c)."
FORMULA_G = r"\Gamma=\{0.2,0.3,0.5,0.7,0.9\}."


def test_render_math_translates_the_manuscript_formulas():
    assert render_math(FORMULA_S) == "S(n)=\u03a3_{c\u2208 C(n)} (w(c))/(\u03a3_{j\u2208 C(n)}w(j))S(c)."
    assert render_math(FORMULA_G) == "\u0393={0.2,0.3,0.5,0.7,0.9}."


def test_render_math_leaves_unknown_commands_visible():
    # An unrecognised command must survive so a new construct cannot be silently mangled.
    assert render_math(r"\foobar{x}") == r"\foobar{x}"
    assert render_math(r"\alpha \le \beta") == "\u03b1 \u2264 \u03b2"


def test_markdown_table_rows_cannot_split_across_pages():
    document = Document()
    add_markdown_table(document, [["A", "B"], ["1", "2"], ["3", "4"]])
    table = document.tables[0]
    assert len(table.rows) == 3
    for row in table.rows:
        assert "cantSplit" in row._tr.xml


def test_built_docx_has_no_raw_latex_and_keeps_the_formulas(tmp_path):
    output = build(source=SOURCE, output=tmp_path / "rendered.docx")
    paragraphs = [paragraph.text for paragraph in Document(output).paragraphs]
    assert render_math(FORMULA_S) in paragraphs
    assert render_math(FORMULA_G) in paragraphs
    joined = "\n".join(paragraphs)
    for leftover in ("\\sum", "\\frac", "\\Gamma", "\\in"):
        assert leftover not in joined


def test_built_docx_is_byte_deterministic(tmp_path):
    first = build(source=SOURCE, output=tmp_path / "first.docx")
    time.sleep(1.1)
    second = build(source=SOURCE, output=tmp_path / "second.docx")

    assert first.read_bytes() == second.read_bytes()