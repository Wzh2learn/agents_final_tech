"""Render the advisor brief from its tracked Markdown source using ReportLab."""

from html import escape
from pathlib import Path
import re

from reportlab import rl_config
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
SOURCE = HERE / "ADVISOR_BRIEF_20261102.md"
OUTPUT = REPO / "output" / "pdf" / "advisor_brief_20261102.pdf"
FONT = Path("C:/Windows/Fonts/Deng.ttf")


def markup(value):
    """Preserve simple bold and public hyperlinks from the Markdown source."""
    value = escape(value)
    value = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", value)
    return re.sub(
        r"\[([^\]]+)\]\((https?://[^)]+)\)",
        r'<link href="\2" color="#174a75">\1</link>',
        value,
    )


def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("AdvisorCJK", 8)
    canvas.setFillColor(colors.HexColor("#5b6672"))
    canvas.drawString(18 * mm, 12 * mm, "硕士论文方向与小论文进展 · 2026-11-03")
    canvas.drawRightString(A4[0] - 18 * mm, 12 * mm, str(doc.page))
    canvas.restoreState()


def main():
    if not FONT.is_file():
        raise FileNotFoundError(f"A Chinese font is required: {FONT}")
    pdfmetrics.registerFont(TTFont("AdvisorCJK", str(FONT)))
    rl_config.canvas_basefontname = "AdvisorCJK"
    pdfmetrics.registerFontFamily(
        "AdvisorCJK", normal="AdvisorCJK", bold="AdvisorCJK",
        italic="AdvisorCJK", boldItalic="AdvisorCJK"
    )
    title = ParagraphStyle(
        "title", fontName="AdvisorCJK", fontSize=17, leading=24,
        alignment=TA_CENTER, textColor=colors.HexColor("#193b5b"),
        spaceAfter=9, wordWrap="CJK", keepWithNext=True,
    )
    heading = ParagraphStyle(
        "heading", fontName="AdvisorCJK", fontSize=12, leading=18,
        textColor=colors.HexColor("#193b5b"), spaceBefore=10,
        spaceAfter=5, wordWrap="CJK", keepWithNext=True,
    )
    body = ParagraphStyle(
        "body", fontName="AdvisorCJK", fontSize=9.4, leading=15.3,
        textColor=colors.HexColor("#202830"), spaceAfter=6.5,
        wordWrap="CJK", splitLongWords=True,
    )
    bullet = ParagraphStyle("bullet", parent=body, leftIndent=11, firstLineIndent=-8)
    story = []
    for line in SOURCE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith("# "):
            story.append(Paragraph(markup(line[2:]), title))
        elif line.startswith("## "):
            story.append(Paragraph(markup(line[3:]), heading))
        elif line.startswith("- "):
            story.append(Paragraph("- " + markup(line[2:]), bullet))
        elif re.match(r"^\d+\. ", line):
            story.append(Paragraph(markup(line), bullet))
        else:
            story.append(Paragraph(markup(line), body))
    story.append(Spacer(1, 1 * mm))
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    document = SimpleDocTemplate(
        str(OUTPUT), pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm,
        topMargin=16 * mm, bottomMargin=19 * mm,
        title="硕士论文方向与小论文进展",
        author="",
    )
    document.build(story, onFirstPage=footer, onLaterPages=footer)
    print(OUTPUT)


if __name__ == "__main__":
    main()
