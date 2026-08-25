#!/usr/bin/env python3
"""Regenerate docs/31_导师进展汇报_v2_20260825.docx (self-contained, images embedded).

Audience switch: --audience advisor (default, strips internal appendices A/B) | full.

Same markdown subset as build_doc23_docx.py + fenced code blocks.
Does NOT touch the client-version builder (build_doc23_docx.py).
"""
import argparse
import os
import re

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt, RGBColor

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "docs", "31_导师进展汇报_v2_20260825.md")
OUT = os.path.join(ROOT, "docs", "31_导师进展汇报_v2_20260825.docx")

COVER_TITLE = "AI 金融对账单智能解析与问答系统"
COVER_DATE = "2026 年 8 月 25 日"


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


def add_cover(doc: Document, sub: str) -> None:
    for _ in range(6):
        doc.add_paragraph()
    t = doc.add_paragraph()
    t.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = t.add_run(COVER_TITLE)
    r.bold = True
    r.font.size = Pt(26)
    s = doc.add_paragraph()
    s.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = s.add_run(sub)
    r.font.size = Pt(16)
    r.font.color.rgb = RGBColor(0x40, 0x40, 0x40)
    d = doc.add_paragraph()
    d.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = d.add_run(COVER_DATE)
    r.font.size = Pt(12)
    r.font.color.rgb = RGBColor(0x70, 0x70, 0x70)
    for _ in range(4):
        doc.add_paragraph()
    for text in ("呈报对象：指导老师", "汇报方：金融对账单智能解析与问答项目组"):
        ln = doc.add_paragraph()
        ln.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = ln.add_run(text)
        r.font.size = Pt(12)
    doc.add_page_break()


def add_page_numbers(doc: Document) -> None:
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    footer = doc.sections[0].footer
    p = footer.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run()
    el = OxmlElement("w:fldChar")
    el.set(qn("w:fldCharType"), "begin")
    run._r.append(el)
    it = OxmlElement("w:instrText")
    it.set(qn("xml:space"), "preserve")
    it.text = "PAGE"
    run._r.append(it)
    el = OxmlElement("w:fldChar")
    el.set(qn("w:fldCharType"), "end")
    run._r.append(el)


def main() -> None:
    ap = argparse.ArgumentParser(description="docs/31 导师汇报 docx 生成器")
    ap.add_argument("--audience", choices=["advisor", "full"], default="advisor",
                    help="advisor=发送版(裁掉内部附录 A/B, 默认); full=内部全量")
    ap.add_argument("--out", default=None, help="输出路径覆盖")
    args = ap.parse_args()

    doc = Document()
    doc.styles["Normal"].font.name = "Microsoft YaHei"
    doc.styles["Normal"].font.size = Pt(10.5)

    lines = open(SRC, encoding="utf-8").read().split("\n")
    # 跳过状态头与首行 H1（封面已含标题）
    while lines and (lines[0].startswith("状态:") or lines[0].startswith("# ")):
        lines = lines[1:]
    if args.audience == "advisor":
        # 受众分离: 附录 A(取回命令)/B(隧道速查)为内部操作卡, 不进发送版
        cut = [i for i, l in enumerate(lines) if l.startswith("## 附录 A")]
        if cut:
            lines = lines[:cut[0]]
    i = 0
    in_fence = False
    add_cover(doc, "科研进展汇报（导师版）" if args.audience == "advisor" else "科研进展汇报（导师预审版·内部全量）")
    while i < len(lines):
        ln = lines[i]
        stripped = ln.strip()
        if stripped.startswith("```"):
            in_fence = not in_fence
            i += 1
            continue
        if in_fence:
            p = doc.add_paragraph()
            p.paragraph_format.left_indent = Pt(14)
            r = p.add_run(ln if ln else " ")
            r.font.name = "Consolas"
            r.font.size = Pt(8.5)
            i += 1
            continue
        # pipe table
        if ln.startswith("|") and i + 1 < len(lines) and re.match(r"^\|[\s\-:|]+\|\s*$", lines[i + 1]):
            rows = []
            while i < len(lines) and lines[i].startswith("|"):
                rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")])
                i += 1
            rows.pop(1)
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
                p.add_run().add_picture(full, width=Inches(6.3))
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
            bp = doc.add_paragraph()
            bp.paragraph_format.left_indent = Pt(14)
            bp.add_run("•  ")
            add_md_runs(bp, stripped[2:])
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

    add_page_numbers(doc)
    out = args.out or OUT
    doc.save(out)
    print("saved:", out)


if __name__ == "__main__":
    main()
