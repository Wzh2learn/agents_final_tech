#!/usr/bin/env python3
"""Regenerate docs/23_甲方阶段汇报_发送版.docx (self-contained, images embedded).

Markdown subset handled: # / ## headings, pipe tables, ![img](rel), - bullets,
> blockquote, **bold** and `code` inline. Run after any docs/23 content change.
"""
import os
import re

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt, RGBColor

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "docs", "23_甲方阶段汇报.md")
OUT = os.path.join(ROOT, "docs", "23_甲方阶段汇报_发送版.docx")


def add_md_runs(par, text: str) -> None:
    pos = 0
    for m in re.finditer(r"(\*\*[^*]+\*\*|`[^`]+`)", text):
        if m.start() > pos:
            par.add_run(text[pos:m.start()])
        tok = m.group(0)
        if tok.startswith("**"):
            par.add_run(tok[2:-2]).bold = True
        else:
            par.add_run(tok[1:-1]).font.name = "Consolas"
        pos = m.end()
    if pos < len(text):
        par.add_run(text[pos:])


COVER_TITLE = "AI 金融对账单智能解析与问答系统"
COVER_SUB = "阶段汇报"


def add_cover(doc: Document) -> None:
    for _ in range(6):
        doc.add_paragraph()
    t = doc.add_paragraph()
    t.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = t.add_run(COVER_TITLE)
    r.bold = True
    r.font.size = Pt(26)
    s = doc.add_paragraph()
    s.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = s.add_run(COVER_SUB)
    r.font.size = Pt(16)
    r.font.color.rgb = RGBColor(0x40, 0x40, 0x40)
    d = doc.add_paragraph()
    d.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = d.add_run("2026 年 8 月")
    r.font.size = Pt(12)
    r.font.color.rgb = RGBColor(0x70, 0x70, 0x70)
    doc.add_page_break()


def main() -> None:
    doc = Document()
    doc.styles["Normal"].font.name = "Microsoft YaHei"
    doc.styles["Normal"].font.size = Pt(10.5)

    lines = open(SRC, encoding="utf-8").read().split("\n")
    i = 0
    # 封面独立成页; md 首行 H1 与封面标题重复, 跳过
    if lines and lines[0].startswith("# "):
        lines = lines[1:]
    add_cover(doc)
    while i < len(lines):
        ln = lines[i]
        stripped = ln.strip()
        # pipe table
        if ln.startswith("|") and i + 1 < len(lines) and re.match(r"^\|[\s\-:|]+\|\s*$", lines[i + 1]):
            rows = []
            while i < len(lines) and lines[i].startswith("|"):
                rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")])
                i += 1
            rows.pop(1)  # separator
            ncols = max(len(r) for r in rows)
            t = doc.add_table(rows=len(rows), cols=ncols)
            t.style = "Table Grid"
            for ri, row in enumerate(rows):
                for ci in range(ncols):
                    p = t.cell(ri, ci).paragraphs[0]
                    add_md_runs(p, row[ci] if ci < len(row) else "")
                    if ri == 0:
                        for run in p.runs:
                            run.bold = True
            continue
        m = re.match(r"^(#{1,3}) (.+)$", ln)
        if m:
            h = doc.add_heading("", level=len(m.group(1)))
            add_md_runs(h, m.group(2))
            i += 1
            continue
        m = re.match(r"^!\[([^\]]*)\]\(([^)]+)\)", stripped)
        if m:
            alt, path = m.groups()
            full = os.path.join(ROOT, "docs", path)
            if os.path.exists(full):
                p = doc.add_paragraph()
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                p.add_run().add_picture(full, width=Inches(6.0))
                cap = doc.add_paragraph()
                cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
                r = cap.add_run(alt)
                r.italic = True
                r.font.size = Pt(9)
            else:
                doc.add_paragraph(f"[缺图: {path}]")
            i += 1
            continue
        if stripped.startswith("- "):
            add_md_runs(doc.add_paragraph(style="List Bullet"), stripped[2:])
            i += 1
            continue
        if stripped.startswith("> "):
            p = doc.add_paragraph()
            add_md_runs(p, stripped[2:])
            for run in p.runs:
                run.font.size = Pt(9)
                run.font.color.rgb = RGBColor(0x60, 0x60, 0x60)
            i += 1
            continue
        if stripped:
            add_md_runs(doc.add_paragraph(), stripped)
        i += 1

    doc.save(OUT)
    print("saved:", OUT)


if __name__ == "__main__":
    main()
