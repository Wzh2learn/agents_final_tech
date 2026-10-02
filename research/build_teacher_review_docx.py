#!/usr/bin/env python3
"""Build the teacher-review DOCX from the clean Markdown manuscript.

This is a deterministic, offline formatter. It does not call models, services,
databases, or the network.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Inches, Pt, RGBColor


REPO = Path(__file__).resolve().parents[1]
SOURCE = REPO / "paper" / "teacher_review_draft_v1.md"
OUTPUT = REPO / "paper" / "teacher_review_draft_v1.docx"
MATH_GREEK = {
    "alpha": "α", "beta": "β", "gamma": "γ", "Gamma": "Γ", "delta": "δ", "Delta": "Δ",
    "epsilon": "ε", "varepsilon": "ε", "eta": "η", "theta": "θ", "Theta": "Θ", "iota": "ι",
    "kappa": "κ", "lambda": "λ", "mu": "μ", "nu": "ν", "xi": "ξ", "pi": "π", "rho": "ρ",
    "sigma": "σ", "tau": "τ", "phi": "φ", "chi": "χ", "psi": "ψ", "omega": "ω", "zeta": "ζ",
}
MATH_SYMBOLS = {
    "sum": "Σ", "prod": "∏", "int": "∫", "in": "∈", "notin": "∉", "le": "≤", "leq": "≤",
    "ge": "≥", "geq": "≥", "times": "×", "cdot": "·", "pm": "±", "mp": "∓",
    "approx": "≈", "neq": "≠", "ne": "≠", "to": "→", "rightarrow": "→", "leftarrow": "←",
    "mid": "|", "infty": "∞", "partial": "∂",
}
MATH_SPACING = (("\\,", " "), ("\\;", " "), ("\\:", " "), ("\\!", ""), ("\\ ", " "), ("\\quad", "  "))


def _matching_brace(text: str, open_index: int) -> int:
    """Index of the brace matching the one at `open_index`, or -1 when unbalanced."""
    depth = 0
    for position in range(open_index, len(text)):
        if text[position] == "{":
            depth += 1
        elif text[position] == "}":
            depth -= 1
            if depth == 0:
                return position
    return -1


def render_math(text: str) -> str:
    """Translate the LaTeX constructs this manuscript uses into Unicode.

    python-docx cannot typeset LaTeX, so passing formula source through verbatim puts
    backslashes and command names in front of a reader. Only the constructs present in the
    manuscript are translated; any unrecognised command is left untouched, so a new
    construct degrades into visible source instead of being silently mistranslated.
    """
    out = text

    # \frac{num}{den} -> (num)/(den); brace-matched so a denominator that itself contains
    # `_{...}` is captured whole rather than truncated at the inner brace.
    for _ in range(8):
        match = re.search(r"\\frac\{", out)
        if not match:
            break
        open_num = match.end() - 1
        close_num = _matching_brace(out, open_num)
        if close_num < 0 or close_num + 1 >= len(out) or out[close_num + 1] != "{":
            break
        close_den = _matching_brace(out, close_num + 1)
        if close_den < 0:
            break
        out = (
            out[: match.start()]
            + "(" + out[open_num + 1:close_num] + ")/(" + out[close_num + 2:close_den] + ")"
            + out[close_den + 1:]
        )

    for name in ("sum", "prod", "int"):
        out = re.sub(
            r"\\" + name + r"_\{([^{}]*)\}",
            lambda m, symbol=MATH_SYMBOLS[name]: symbol + "_{" + m.group(1) + "}",
            out,
        )
        out = re.sub(r"\\" + name + r"(?![A-Za-z])", MATH_SYMBOLS[name], out)

    for source, target in (("\\{", "{"), ("\\}", "}"), ("\\%", "%"), ("\\_", "_"),
                           ("\\&", "&"), ("\\#", "#")):
        out = out.replace(source, target)
    for source, target in MATH_SPACING:
        out = out.replace(source, target)
    for table in (MATH_GREEK, MATH_SYMBOLS):
        for name in sorted(table, key=len, reverse=True):
            out = re.sub(r"\\" + name + r"(?![A-Za-z])", table[name], out)
    return re.sub(r"[ \t]{2,}", " ", out).strip()


def prevent_row_split(table) -> None:
    """Keep each row on one page.

    A row that breaks across a page boundary leaves a continuation fragment whose leading
    cells are empty, which reads as a malformed table. Word and LibreOffice both honour
    the `w:cantSplit` row property.
    """
    for row in table.rows:
        row._tr.get_or_add_trPr().append(OxmlElement("w:cantSplit"))



def add_runs(paragraph, text: str) -> None:
    position = 0
    pattern = re.compile(r"(\*\*[^*]+\*\*|`[^`]+`|\*[^*]+\*)")
    for match in pattern.finditer(text):
        if match.start() > position:
            paragraph.add_run(text[position : match.start()])
        token = match.group(0)
        run = paragraph.add_run(token.strip("*`"))
        if token.startswith("**"):
            run.bold = True
        elif token.startswith("`"):
            run.font.name = "Consolas"
        else:
            run.italic = True
        position = match.end()
    if position < len(text):
        paragraph.add_run(text[position:])


def add_page_number(section) -> None:
    paragraph = section.footer.paragraphs[0]
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = paragraph.add_run()
    begin = OxmlElement("w:fldChar")
    begin.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = "PAGE"
    end = OxmlElement("w:fldChar")
    end.set(qn("w:fldCharType"), "end")
    run._r.extend([begin, instr, end])


def style_document(document: Document) -> None:
    section = document.sections[0]
    section.top_margin = Cm(2.0)
    section.bottom_margin = Cm(2.0)
    section.left_margin = Cm(2.2)
    section.right_margin = Cm(2.2)
    add_page_number(section)

    normal = document.styles["Normal"]
    normal.font.name = "Times New Roman"
    normal.font.size = Pt(10.5)
    normal.paragraph_format.space_after = Pt(4)
    normal.paragraph_format.line_spacing = 1.08
    for name, size in (("Title", 18), ("Heading 1", 14), ("Heading 2", 12)):
        style = document.styles[name]
        style.font.name = "Arial"
        style.font.size = Pt(size)
        style.font.color.rgb = RGBColor(0x17, 0x21, 0x2B)


def add_markdown_table(document: Document, rows: list[list[str]]) -> None:
    table = document.add_table(rows=len(rows), cols=max(map(len, rows)))
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    for row_index, row in enumerate(rows):
        for column_index, value in enumerate(row):
            cell = table.cell(row_index, column_index)
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            paragraph = cell.paragraphs[0]
            add_runs(paragraph, value)
            if row_index == 0:
                for run in paragraph.runs:
                    run.bold = True
            for run in paragraph.runs:
                run.font.size = Pt(8.5)
    prevent_row_split(table)


def add_three_stage_table(document: Document) -> None:
    table = document.add_table(rows=4, cols=3)
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    entries = (
        (
            "E · Evaluate",
            "D · Distill",
            "R · Evolve rules",
        ),
        (
            "Contracts + judges\nCheckpoint forest\nVisibility audit",
            "Filter action events\n8B rule-candidate policy\n4B: training smoke only",
            "candidate proposal/prescreen\nfinal deterministic gate\n"
            "gate-validation not sealed test",
        ),
        (
            "Output: qualified traces and defect labels",
            "Target: action policy\nQuality–cost comparison",
            "Target: rule memory + rollback\nIndependent validation pending",
        ),
        (
            "Established evidence",
            "TRAINING RESULT MISSING",
            "MECHANISM EVIDENCE ONLY",
        ),
    )
    for row_index, row in enumerate(entries):
        for column_index, value in enumerate(row):
            cell = table.cell(row_index, column_index)
            cell.text = value
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            for paragraph in cell.paragraphs:
                paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
                for run in paragraph.runs:
                    run.font.size = Pt(8.5)
                    if row_index in (0, 3):
                        run.bold = True
    prevent_row_split(table)
    feedback = document.add_paragraph(
        "Target loop: accepted rules update the workflow and return to the same evaluation protocol."
    )
    feedback.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for run in feedback.runs:
        run.italic = True
        run.font.size = Pt(9)


def build(source: Path = SOURCE, output: Path = OUTPUT) -> Path:
    document = Document()
    style_document(document)
    lines = source.read_text(encoding="utf-8").splitlines()
    index = 0
    in_formula = False

    while index < len(lines):
        line = lines[index]
        stripped = line.strip()

        if index == 0 and line.startswith("# "):
            title = document.add_paragraph(style="Title")
            title.alignment = WD_ALIGN_PARAGRAPH.CENTER
            add_runs(title, line[2:])
            if source.name.startswith("teacher_review_draft"):
                author = document.add_paragraph("Author: ____________________")
                author.alignment = WD_ALIGN_PARAGRAPH.CENTER
            index += 1
            continue

        if stripped == "\\[":
            in_formula = True
            index += 1
            continue
        if stripped == "\\]":
            in_formula = False
            index += 1
            continue
        if in_formula:
            paragraph = document.add_paragraph()
            paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run = paragraph.add_run(render_math(stripped))
            run.font.name = "Cambria Math"
            run.italic = True
            index += 1
            continue

        if line.startswith("|") and index + 1 < len(lines) and re.match(r"^\|[\s\-:|]+\|$", lines[index + 1]):
            rows: list[list[str]] = []
            while index < len(lines) and lines[index].startswith("|"):
                rows.append([part.strip() for part in lines[index].strip("|").split("|")])
                index += 1
            rows.pop(1)
            add_markdown_table(document, rows)
            continue

        image_match = re.match(r"^!\[([^]]+)\]\(([^)]+)\)$", stripped)
        if image_match:
            caption, relative = image_match.groups()
            image_path = (source.parent / relative).resolve()
            if image_path.suffix.lower() == ".png" and image_path.is_file():
                paragraph = document.add_paragraph()
                paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
                paragraph.add_run().add_picture(str(image_path), width=Inches(6.2))
            elif image_path.name == "fig_checkpoint_trees_v2.svg" and image_path.is_file():
                # python-docx cannot rasterize SVG. Preserve the complete structure
                # as a compact native Word table instead of emitting a blank figure.
                table = document.add_table(rows=2, cols=2)
                table.style = "Table Grid"
                table.alignment = WD_TABLE_ALIGNMENT.CENTER
                entries = (
                    (
                        "Parsing tree",
                        "document → read OK*, throughput\n"
                        "table → structure\nfield → field hit\nreconcile → equations",
                    ),
                    (
                        "Question-answering tree",
                        "retrieval → source*\nfaithfulness → judge\n"
                        "numeric → exact*, grounding*\ncitation → judge\n"
                        "refusal → judge, contract*",
                    ),
                )
                for column, (heading, body) in enumerate(entries):
                    head_cell = table.cell(0, column)
                    head_cell.text = heading
                    body_cell = table.cell(1, column)
                    body_cell.text = body
                    for run in head_cell.paragraphs[0].runs:
                        run.bold = True
                    for cell in (head_cell, body_cell):
                        cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
                prevent_row_split(table)
            elif image_path.name == "fig_evaluate_distill_evolve_v1.svg" and image_path.is_file():
                add_three_stage_table(document)
            caption_paragraph = document.add_paragraph(caption)
            caption_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
            for run in caption_paragraph.runs:
                run.italic = True
                run.font.size = Pt(9)
            index += 1
            continue

        heading = re.match(r"^(#{2,3}) (.+)$", line)
        if heading:
            level = 1 if len(heading.group(1)) == 2 else 2
            document.add_heading(heading.group(2), level=level)
            index += 1
            continue

        if stripped.startswith("> "):
            paragraph = document.add_paragraph()
            paragraph.paragraph_format.left_indent = Cm(0.5)
            add_runs(paragraph, stripped[2:])
            for run in paragraph.runs:
                run.italic = True
                run.font.color.rgb = RGBColor(0x66, 0x66, 0x66)
            index += 1
            continue

        if re.match(r"^\d+\. ", stripped):
            paragraph = document.add_paragraph(style="List Number")
            add_runs(paragraph, re.sub(r"^\d+\. ", "", stripped))
            index += 1
            continue
        if stripped.startswith("- "):
            paragraph = document.add_paragraph(style="List Bullet")
            add_runs(paragraph, stripped[2:])
            index += 1
            continue

        if stripped:
            paragraph = document.add_paragraph()
            add_runs(paragraph, stripped)
        index += 1

    # Preserve an explicit internal-review watermark in document properties.
    document.core_properties.title = source.read_text(encoding="utf-8").splitlines()[0][2:]
    document.core_properties.subject = (
        "Internal teacher-review manuscript; patent release gate pending confirmation"
    )
    try:
        source_label = source.relative_to(REPO).as_posix()
    except ValueError:
        source_label = source.as_posix()
    document.core_properties.comments = f"Generated offline from {source_label}"
    output.parent.mkdir(parents=True, exist_ok=True)
    document.save(output)
    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=SOURCE)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    source = args.source if args.source.is_absolute() else REPO / args.source
    output = args.output if args.output.is_absolute() else REPO / args.output
    print(build(source, output))
