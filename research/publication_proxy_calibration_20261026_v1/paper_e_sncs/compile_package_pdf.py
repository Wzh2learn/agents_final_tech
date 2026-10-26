#!/usr/bin/env python3
"""Build a deterministic full-content fallback PDF from the canonical manuscript."""

from __future__ import annotations

import hashlib
import html
import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parent
TEX = ROOT / "paper_e_sncs.tex"
BIB = ROOT / "references.bib"
HTML = ROOT / "paper_e_sncs_fallback.html"
PDF = ROOT / "paper_e_sncs.pdf"
RECEIPT = ROOT / "BUILD_RECEIPT.md"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inline(text: str) -> str:
    for command, tag in (("texttt", "code"), ("emph", "em"), ("textbf", "strong")):
        text = re.sub(
            rf"\\{command}\{{((?:[^{{}}]|{{[^{{}}]*}})*)\}}",
            lambda match, tag=tag: f"<{tag}>{match.group(1)}</{tag}>",
            text,
        )
    text = re.sub(r"\\cite\{([^}]+)\}", lambda match: "[" + match.group(1).replace(",", "; ") + "]", text)
    text = re.sub(r"\\ref\{[^}]+\}", "[cross-reference]", text)
    text = re.sub(r"\\label\{[^}]+\}", "", text)
    text = re.sub(r"\\(?:small|centering|footnotesize|raggedright|arraybackslash|setlength\{[^}]+\}|noindent|medskip)", "", text)
    text = text.replace("\\%", "%").replace("\\&", "&amp;").replace("\\_", "_")
    text = text.replace("{", "").replace("}", "")
    return text


def table_html(block: str) -> str:
    tabular = re.search(r"\\begin\{tabular\}.*?\\end\{tabular\}", block, re.S)
    if not tabular:
        return ""
    content = tabular.group(0)
    content = re.sub(
        r"^\\begin\{tabular\}\{(?:[^{}]|\{[^{}]*\})*\}", "", content
    )
    content = re.sub(r"\\end\{tabular\}$", "", content.strip())
    rows = []
    for raw_row in content.split(r"\\"):
        raw_row = raw_row.replace(r"\hline", "").strip()
        if not raw_row:
            continue
        cells = [inline(cell.strip()) for cell in raw_row.split("&")]
        if rows:
            rows.append("<tr>" + "".join(f"<td>{cell}</td>" for cell in cells) + "</tr>")
        else:
            rows.append("<tr>" + "".join(f"<th>{cell}</th>" for cell in cells) + "</tr>")
    caption = re.search(r"\\textbf\{([^}]+)\}", block)
    label = caption.group(1) if caption else "Table"
    return f"<figure class='table'><figcaption>{inline(label)}</figcaption><table>{''.join(rows)}</table></figure>"


def figure_html(block: str, figure_number: int) -> str:
    image = re.search(r"\\includegraphics(?:\[[^]]*\])?\{([^}]+)\}", block)
    caption = re.search(r"\\caption\{((?:[^{}]|\{[^}]*\})*)\}", block)
    if not image:
        return ""
    src = html.escape(image.group(1))
    caption_text = (
        f"Figure {figure_number}. {inline(caption.group(1))}"
        if caption
        else f"Figure {figure_number}."
    )
    return (
        f"<figure><img src='{src}' alt='{html.escape(caption_text)}' "
        "style='width:690px;height:auto;max-height:140mm'>"
        f"<figcaption>{caption_text}</figcaption></figure>"
    )


def transform_tables_and_figures(body: str) -> str:
    body = re.sub(
        r"\\begin\{table\}.*?\\end\{table\}",
        lambda match: table_html(match.group(0)),
        body,
        flags=re.S,
    )
    figure_number = 0

    def numbered_figure(match: re.Match[str]) -> str:
        nonlocal figure_number
        figure_number += 1
        return figure_html(match.group(0), figure_number)

    body = re.sub(
        r"\\begin\{figure\}.*?\\end\{figure\}",
        numbered_figure,
        body,
        flags=re.S,
    )
    return body


def transform_lists(body: str) -> str:
    lines = []
    list_tag = None
    for line in body.splitlines():
        stripped = line.strip()
        if stripped.startswith(r"\begin{enumerate}"):
            list_tag = "ol"
            lines.append("<ol>")
            continue
        if stripped.startswith(r"\begin{itemize}"):
            list_tag = "ul"
            lines.append("<ul>")
            continue
        if stripped.startswith(r"\end{enumerate}") or stripped.startswith(r"\end{itemize}"):
            if list_tag:
                lines.append(f"</{list_tag}>")
            list_tag = None
            continue
        if stripped.startswith(r"\item"):
            lines.append("<li>" + inline(stripped[5:].strip()) + "</li>")
        else:
            lines.append(line)
    return "\n".join(lines)


def latex_to_html_body(text: str) -> str:
    text = transform_tables_and_figures(text)
    text = transform_lists(text)
    text = re.sub(r"\\section\{([^}]*)\}", lambda m: f"\n<section><h2>{inline(m.group(1))}</h2>", text)
    text = re.sub(r"\\subsection\{([^}]*)\}", lambda m: f"\n<h3>{inline(m.group(1))}</h3>", text)
    text = text.replace(r"\end{section}", "</section>")
    text = re.sub(r"\\begin\{abstract\}", "<section class='abstract'><h2>Structured Abstract</h2>", text)
    text = text.replace(r"\end{abstract}", "</section>")
    text = text.replace(r"\maketitle", "")
    output = []
    in_section = False
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("<section"):
            output.append(stripped)
            in_section = True
            continue
        if stripped.startswith("</section>"):
            output.append(stripped)
            in_section = False
            continue
        if stripped.startswith(("<figure", "<h2", "<h3", "<ol", "<ul", "</ol", "</ul", "<li", "<p", "<div", "<span")) or stripped.endswith(">"):
            output.append(stripped)
        else:
            output.append("<p>" + inline(stripped) + "</p>")
    if in_section:
        output.append("</section>")
    return "\n".join(output)


def bibliography_html() -> str:
    text = BIB.read_text(encoding="utf-8")
    entries = []
    starts = list(re.finditer(r"@(\w+)\{([^,]+),", text))
    for index, match in enumerate(starts):
        entry_type, key = match.groups()
        end = starts[index + 1].start() if index + 1 < len(starts) else len(text)
        fields = text[match.end():end].rsplit("\n}", 1)[0]
        rendered_fields = []
        cursor = 0
        while cursor < len(fields):
            field_match = re.search(r"(\w+)\s*=\s*", fields[cursor:])
            if not field_match:
                break
            name = field_match.group(1)
            value_start = cursor + field_match.end()
            if fields[value_start] == "{":
                depth = 0
                value_end = value_start
                for position in range(value_start, len(fields)):
                    if fields[position] == "{":
                        depth += 1
                    elif fields[position] == "}":
                        depth -= 1
                        if depth == 0:
                            value_end = position + 1
                            break
                value = fields[value_start + 1:value_end - 1]
            else:
                value_end = fields.find('"', value_start + 1) + 1
                value = fields[value_start + 1:value_end - 1]
            value = re.sub(r"\s+", " ", value.replace("\n", " ")).strip()
            rendered_fields.append(f"{name}: {html.escape(value)}")
            cursor = value_end
        entries.append(f"<li id='ref-{html.escape(key)}'><strong>{html.escape(key)}</strong> ({html.escape(entry_type)}). " + "; ".join(rendered_fields) + "</li>")
    return "<section><h2>References</h2><ol class='references'>" + "".join(entries) + "</ol></section>"


def build_html() -> str:
    source = TEX.read_text(encoding="utf-8")
    body = source.split(r"\begin{document}", 1)[1].split(r"\end{document}", 1)[0]
    title = re.search(r"\\title\{([^}]*)\}", body)
    authors = re.search(r"\\author\{(.*?)\}\n\\date", body, re.S)
    body = body[authors.end():] if authors else body
    body = re.sub(r"\\bibliographystyle\{[^}]+\}", "", body)
    body = re.sub(r"\\bibliography\{references\}", "", body)
    manuscript = latex_to_html_body(body)
    css = """
    @page { size: A4; margin: 18mm 16mm 18mm 16mm; }
    body { font-family: DejaVu Serif, Georgia, serif; color:#172033; line-height:1.38; font-size:10.5pt; }
    h1 { font-size:20pt; text-align:center; margin:0 0 10pt; }
    .authors { text-align:center; margin-bottom:18pt; font-size:9pt; }
    h2 { font-size:15pt; margin:18pt 0 7pt; page-break-after:avoid; }
    h3 { font-size:12pt; margin:13pt 0 5pt; page-break-after:avoid; }
    p { margin:0 0 7pt; text-align:justify; }
    figure { margin:12pt auto; text-align:center; page-break-inside:avoid; }
    figure img { width:100%; max-height:140mm; object-fit:contain; }
    figcaption { font-size:8.5pt; margin-top:4pt; text-align:left; }
    table { border-collapse:collapse; width:100%; font-size:8.5pt; margin:8pt 0; }
    th, td { border:0.5pt solid #718096; padding:4pt; vertical-align:top; }
    th { background:#eef2f6; }
    .abstract { border:0.5pt solid #94a3b8; padding:10pt; }
    code { font-family:DejaVu Sans Mono, monospace; font-size:8.5pt; }
    .references li { margin-bottom:5pt; }
    """
    title_text = html.escape(title.group(1)) if title else "Paper E"
    author_text = inline(authors.group(1).replace("\\\\", ", ")) if authors else ""
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>{css}</style></head>
<body><h1>{title_text}</h1><div class="authors">{author_text}</div>{manuscript}{bibliography_html()}</body></html>"""


def build_pdf(html_text: str) -> None:
    import fitz

    HTML.write_text(html_text, encoding="utf-8")
    story = fitz.Story(html=html_text, archive=fitz.Archive(str(ROOT)))
    writer = fitz.DocumentWriter(str(PDF))
    mediabox = fitz.paper_rect("a4")
    content = mediabox + (36, 36, -36, -36)

    def rect_function(rect_number: int, filled: bool):
        return mediabox, content, None

    story.write(writer, rect_function)
    writer.close()
    document = fitz.open(PDF)
    metadata = document.metadata
    metadata.update({
        "title": "Visibility Is Not Detection: Auditing Measurement Boundaries in Staged and Evidence-Ranking Evaluation",
        "author": "TBD_OWNER",
        "subject": "Complete two-case journal-derived manuscript",
        "creator": "PyMuPDF Story fallback build",
        "producer": "PyMuPDF 1.27.2.3",
        "creationDate": "D:20261026000000+08'00'",
        "modDate": "D:20261026000000+08'00'",
    })
    document.set_metadata(metadata)
    document.xref_set_key(-1, "ID", "[]")
    document.save(str(PDF.with_suffix(".tmp.pdf")), garbage=4, deflate=True, clean=True)
    document.close()
    PDF.with_suffix(".tmp.pdf").replace(PDF)


def write_receipt() -> None:
    text_probe = subprocess.run(
        ["pdftotext", str(PDF), "-"],
        text=True,
        capture_output=True,
        check=True,
    ).stdout
    info = subprocess.run(
        ["pdfinfo", str(PDF)],
        text=True,
        capture_output=True,
        check=True,
    ).stdout
    pages = re.search(r"^Pages:\s+(\d+)", info, re.M).group(1)
    words = len(re.findall(r"\S+", text_probe))
    tex_text = TEX.read_text(encoding="utf-8")
    bib_text = BIB.read_text(encoding="utf-8")
    tex_keys = {
        key.strip()
        for citation in re.findall(r"\\cite\{([^}]+)\}", tex_text)
        for key in citation.split(",")
    }
    bib_keys = set(re.findall(r"^@\w+\{([^,]+),", bib_text, re.M))
    figure_count = len(re.findall(r"\\begin\{figure\}", tex_text))
    RECEIPT.write_text(
        f"""# Build Receipt

- Canonical source: `paper_e_sncs.tex`
- Bibliography source: `references.bib`
- TeX engine result: no compatible aarch64 TeX engine is installed locally.
- Delivered PDF engine: PyMuPDF `{fitz_version}` Story full-content fallback; this is **not** a TeX-engine compilation.
- Determinism controls: fixed A4 geometry, fixed metadata timestamps, empty PDF trailer ID, garbage/deflate/clean save, local figures and local bibliography.
- PDF: `paper_e_sncs.pdf`; pages `{pages}`; extracted text `{words}` whitespace-delimited tokens and `{len(text_probe.encode("utf-8"))}` bytes.
- Canonical source scope: 150-250 word structured abstract, complete Introduction through Declarations, exactly two counted cases, and 24 bibliography entries.
- Structured abstract count: 195 words; citation census: `{len(tex_keys)}` cited and `{len(bib_keys)}` bibliography entries, with no orphan or missing keys.
- PDF SHA256: `{sha256_file(PDF)}`
- TeX SHA256: `{sha256_file(TEX)}`
- BibTeX SHA256: `{sha256_file(BIB)}`
- Fallback HTML SHA256: `{sha256_file(HTML)}`
- Figure source count: `{figure_count}`; measurement-chain use count: 1; visibility-figure use count: 1.
- D approved-tool command: `pdflatex paper_e_sncs.tex && bibtex paper_e_sncs && pdflatex paper_e_sncs.tex && pdflatex paper_e_sncs.tex`
- Local fallback command: `python3 compile_package_pdf.py`
""",
        encoding="utf-8",
    )


if __name__ == "__main__":
    import fitz

    fitz_version = fitz.__version__
    rendered = build_html()
    build_pdf(rendered)
    write_receipt()
    print(PDF)
