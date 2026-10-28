#!/usr/bin/env python3
"""Build the directly convertible Paper E Word package from the canonical TeX."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
from pathlib import Path
from typing import Any

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.shared import Inches, Pt


HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[2]
SOURCE_ROOT = (
    REPO_ROOT
    / "research"
    / "adaptive_mechanism_20261027_v1"
    / "paper_e_formal_build"
)
TEX = SOURCE_ROOT / "paper_e_sncs.tex"
BIB = SOURCE_ROOT / "references.bib"
FIGURES = SOURCE_ROOT / "figures"
DATE = "2026-10-27"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def unescape_latex(value: str) -> str:
    replacements = {
        r"\_": "_",
        r"\%": "%",
        r"\&": "&",
        r"\#": "#",
        r"\{": "{",
        r"\}": "}",
        r"\textemdash": "—",
        r"\textendash": "–",
        r"``": "“",
        r"''": "”",
        r"\@": "@",
    }
    for old, new in replacements.items():
        value = value.replace(old, new)
    return value


def inline_latex(value: str) -> str:
    value = unescape_latex(value)
    value = re.sub(
        r"\\cite\{([^}]*)\}",
        lambda match: "[" + ",".join(item.strip() for item in match.group(1).split(",")) + "]",
        value,
    )
    value = re.sub(r"\\ref\{fig:(\d+)\}", r"Figure \1", value)
    value = re.sub(r"\\emph\{([^{}]*)\}", r"*\1*", value)
    value = re.sub(r"\\textit\{([^{}]*)\}", r"*\1*", value)
    value = re.sub(r"\\textbf\{([^{}]*)\}", r"**\1**", value)
    value = re.sub(r"\\texttt\{([^{}]*)\}", r"`\1`", value)
    value = value.replace(r"\noindent", "")
    value = value.replace(r"\medskip", "")
    value = value.replace(r"\centering", "")
    value = value.replace(r"\small", "")
    value = re.sub(r"\\setlength\{[^}]+\}\{[^}]+\}", "", value)
    value = re.sub(r"\\hyphenation\{[^}]+\}", "", value)
    value = re.sub(r"\\setlength\{\\emergencystretch\}\{[^}]+\}", "", value)
    return value.strip()


def parse_field(bib: str, key: str) -> str:
    match = re.search(rf"(?<![A-Za-z]){re.escape(key)}\s*=", bib, flags=re.IGNORECASE)
    if not match:
        return ""
    position = match.end()
    while position < len(bib) and bib[position].isspace():
        position += 1
    if position >= len(bib):
        return ""
    if bib[position] == "{":
        depth = 1
        cursor = position + 1
        start = cursor
        while cursor < len(bib) and depth:
            if bib[cursor] == "\\":
                cursor += 2
                continue
            if bib[cursor] == "{":
                depth += 1
            elif bib[cursor] == "}":
                depth -= 1
            cursor += 1
        return bib[start : cursor - 1].strip()
    if bib[position] == '"':
        cursor = position + 1
        start = cursor
        while cursor < len(bib):
            if bib[cursor] == "\\":
                cursor += 2
                continue
            if bib[cursor] == '"':
                return bib[start:cursor].strip()
            cursor += 1
        return ""
    end = re.search(r"[,\r\n]", bib[position:])
    stop = position + end.start() if end else len(bib)
    return bib[position:stop].strip()


def parse_bib(text: str) -> dict[str, dict[str, str]]:
    entries: dict[str, dict[str, str]] = {}
    starts = list(re.finditer(r"^@(\w+)\s*\{\s*([^,\s]+)\s*,", text, flags=re.MULTILINE))
    for index, match in enumerate(starts):
        end = starts[index + 1].start() if index + 1 < len(starts) else len(text)
        body = text[match.start() : end]
        entry = {"entry_type": match.group(1).lower(), "key": match.group(2)}
        for field in (
            "author",
            "editor",
            "title",
            "booktitle",
            "journal",
            "year",
            "doi",
            "eprint",
            "archivePrefix",
            "howpublished",
            "note",
            "publisher",
            "volume",
            "number",
            "pages",
            "url",
        ):
            value = parse_field(body, field)
            if value:
                entry[field] = value
        entries[entry["key"]] = entry
    return entries


def clean_bibtex_value(value: str) -> str:
    value = value.replace(r"\'", "").replace(r"\-", "-")
    value = re.sub(r"\\url\{([^}]*)\}", r"\1", value)
    value = re.sub(r"[{}]", "", value)
    return re.sub(r"\s+", " ", value).strip()


def format_authors(value: str) -> str:
    people = [clean_bibtex_value(item) for item in re.split(r"\s+and\s+", value)]
    formatted: list[str] = []
    for person in people:
        if person.lower() in {"others", "et al."}:
            formatted.append("et al.")
            continue
        if ", " in person:
            surname, given = person.split(", ", 1)
            formatted.append(f"{surname}, {given}")
        else:
            parts = person.split()
            formatted.append(f"{parts[-1]}, {' '.join(parts[:-1])}" if len(parts) > 1 else person)
    if len(formatted) == 1:
        return formatted[0]
    if len(formatted) == 2:
        return f"{formatted[0]} & {formatted[1]}"
    return ", ".join(formatted[:-1]) + f", & {formatted[-1]}"


def citation_order(tex: str) -> list[str]:
    ordered: list[str] = []
    for match in re.finditer(r"\\cite\{([^}]*)\}", tex):
        for key in match.group(1).split(","):
            key = key.strip()
            if key and key not in ordered:
                ordered.append(key)
    return ordered


def format_reference(index: int, entry: dict[str, str]) -> str:
    author = format_authors(entry.get("author") or entry.get("editor") or "Unknown")
    title = clean_bibtex_value(entry.get("title", ""))
    year = clean_bibtex_value(entry.get("year", ""))
    parts = [f"{author}. *{title}.*"]
    if entry.get("booktitle"):
        parts.append(f"In *{clean_bibtex_value(entry['booktitle'])}*")
    elif entry.get("journal"):
        parts.append(f"*{clean_bibtex_value(entry['journal'])}*")
    elif entry.get("publisher"):
        parts.append(clean_bibtex_value(entry["publisher"]))
    if year:
        parts.append(year + ".")
    if entry.get("doi"):
        parts.append(f"https://doi.org/{clean_bibtex_value(entry['doi'])}.")
    elif entry.get("eprint"):
        archive = clean_bibtex_value(entry.get("archivePrefix", "arXiv"))
        parts.append(f"{archive}:{clean_bibtex_value(entry['eprint'])}.")
    elif entry.get("url"):
        parts.append(clean_bibtex_value(entry["url"]) + ".")
    elif entry.get("howpublished"):
        parts.append(clean_bibtex_value(entry["howpublished"]) + ".")
    if entry.get("note") and "Accessed" not in entry["note"]:
        parts.append(clean_bibtex_value(entry["note"]) + ".")
    return f"[{index}] " + " ".join(parts)


def parse_tex_blocks(tex: str) -> list[tuple[str, str]]:
    start = tex.index(r"\begin{document}") + len(r"\begin{document}")
    end = tex.rindex(r"\end{document}")
    body = tex[start:end]
    block_re = re.compile(
        r"(\\begin\{(?:abstract|figure|table|enumerate)\}.*?\\end\{(?:abstract|figure|table|enumerate)\})",
        re.DOTALL,
    )
    blocks: list[tuple[str, str]] = []
    position = 0
    for match in block_re.finditer(body):
        if match.start() > position:
            blocks.append(("text", body[position : match.start()]))
        blocks.append(("block", match.group(1)))
        position = match.end()
    if position < len(body):
        blocks.append(("text", body[position:]))
    return blocks


def render_figure(block: str) -> str:
    path_match = re.search(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]*)\}", block)
    caption_match = re.search(r"\\caption\{([^}]*)\}", block, re.DOTALL)
    label_match = re.search(r"\\label\{([^}]*)\}", block)
    path = path_match.group(1) if path_match else ""
    caption = inline_latex(caption_match.group(1)) if caption_match else "Figure"
    number_match = re.search(r"fig:(\d+)", label_match.group(1)) if label_match else None
    number = number_match.group(1) if number_match else ""
    return f"![Figure {number}. {caption}]({path})\n"


def render_table(block: str) -> str:
    begin_match = re.search(r"\\begin\{tabular\}", block)
    if not begin_match:
        return ""
    cursor = begin_match.end()
    while cursor < len(block) and block[cursor].isspace():
        cursor += 1
    if cursor >= len(block) or block[cursor] != "{":
        return ""
    depth = 1
    cursor += 1
    while cursor < len(block) and depth:
        if block[cursor] == "\\":
            cursor += 2
            continue
        if block[cursor] == "{":
            depth += 1
        elif block[cursor] == "}":
            depth -= 1
        cursor += 1
    body_start = cursor
    end_match = re.search(r"\\end\{tabular\}", block[body_start:])
    if not end_match:
        return ""
    body = block[body_start : body_start + end_match.start()]
    caption_match = re.search(r"\\caption\{([^}]*)\}", block, re.DOTALL)
    caption = inline_latex(caption_match.group(1)) if caption_match else ""
    latex_rows = [row.strip().removesuffix(r"\\").strip() for row in body.splitlines() if row.strip()]
    rows: list[list[str]] = []
    for row in latex_rows:
        if not row or re.fullmatch(
            r"(?:\\hline|\\toprule|\\midrule|\\bottomrule|\\rule\{[^}]+\}\{[^}]+\})+",
            row,
        ):
            continue
        cells = [inline_latex(cell.strip()) for cell in row.split("&")]
        if cells:
            rows.append(cells)
    if not rows:
        return ""
    width = max(len(row) for row in rows)
    rows = [row + [""] * (width - len(row)) for row in rows]
    lines: list[str] = []
    if caption:
        lines.extend([f"**Table. {caption}**", ""])
    lines.append("| " + " | ".join(rows[0]) + " |")
    lines.append("|" + "|".join(["---"] * width) + "|")
    for row in rows[1:]:
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines) + "\n"


def render_abstract(block: str) -> str:
    inner = re.sub(r"^\\begin\{abstract\}|\\end\{abstract\}$", "", block.strip())
    paragraphs = [part.strip() for part in inner.split(r"\medskip") if part.strip()]
    lines = ["## Abstract", ""]
    for paragraph in paragraphs:
        lines.append(inline_latex(paragraph))
        lines.append("")
    return "\n".join(lines)


def render_enumerate(block: str) -> str:
    inner = re.sub(r"^\\begin\{enumerate\}|\\end\{enumerate\}$", "", block.strip())
    items = re.findall(r"\\item\s+(.*?)(?=\\item\s+|\\end\{enumerate\})", inner, re.DOTALL)
    return "\n".join(f"{index}. {inline_latex(item)}" for index, item in enumerate(items, start=1)) + "\n"


def render_text(text: str) -> str:
    output: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("%"):
            continue
        heading = re.match(r"\\(section|subsection|subsubsection)\{(.*)\}", line)
        if heading:
            level = {"section": 2, "subsection": 3, "subsubsection": 4}[heading.group(1)]
            output.append("#" * level + " " + inline_latex(heading.group(2)))
            output.append("")
            continue
        if line in {
            r"\maketitle",
            r"\date{}",
            r"\bibliographystyle{elsarticle-harv}",
            r"\bibliography{references}",
        }:
            continue
        if re.fullmatch(r"\\(?:title|author)\{.*\}", line):
            continue
        output.append(inline_latex(line))
    return "\n".join(output)


def convert_manuscript(tex: str) -> str:
    title_match = re.search(r"\\title\{(.*)\}", tex)
    author_match = re.search(r"\\author\{([^}]*)\}", tex, re.DOTALL)
    title = inline_latex(title_match.group(1)) if title_match else "Untitled"
    authors = inline_latex(author_match.group(1)).replace(r"\\", "<br>") if author_match else "TBD_OWNER"
    front = [
        "---",
        f"title: {json.dumps(title, ensure_ascii=False)}",
        "author:",
        f"  - {json.dumps(authors, ensure_ascii=False)}",
        "date: \"\"",
        "lang: en-US",
        "---",
        "",
    ]
    body: list[str] = []
    for kind, block in parse_tex_blocks(tex):
        if kind == "block":
            if block.startswith(r"\begin{abstract}"):
                body.append(render_abstract(block))
                body.append(
                    "**Keywords:** evaluation validity; staged evaluation; "
                    "evidence ranking; score sensitivity; reproducibility"
                )
                body.append("")
            elif block.startswith(r"\begin{figure}"):
                body.append(render_figure(block))
            elif block.startswith(r"\begin{table}"):
                body.append(render_table(block))
            elif block.startswith(r"\begin{enumerate}"):
                body.append(render_enumerate(block))
            body.append("")
        else:
            body.append(render_text(block))
    body.append("## References")
    return "\n".join(front + body).rstrip() + "\n"


def build_reference_doc(path: Path) -> None:
    document = Document()
    section = document.sections[0]
    section.top_margin = Inches(1)
    section.bottom_margin = Inches(1)
    section.left_margin = Inches(1)
    section.right_margin = Inches(1)
    styles = document.styles
    body = styles["Normal"]
    body.font.name = "Times New Roman"
    body.font.size = Pt(10)
    body._element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
    body.paragraph_format.line_spacing = 1.15
    body.paragraph_format.space_after = Pt(5)
    for style_name, size in (("Title", 16), ("Heading 1", 14), ("Heading 2", 12), ("Heading 3", 11)):
        style = styles[style_name]
        style.font.name = "Times New Roman"
        style.font.size = Pt(size)
        style.font.bold = True
        style._element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
    title = document.add_paragraph(style="Title")
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title.add_run("Paper E reference style — 10 pt Times New Roman")
    document.add_paragraph(
        "This document supplies Pandoc reference styles only; it is not the manuscript body."
    )
    document.save(path)


def write_csl(path: Path) -> None:
    style = {
        "id": "numeric-bracket",
        "title": "Numeric Bracket",
        "category": ["generic-base"],
        "citation-format": "numeric",
        "updated": "2026-10-27",
        "locale": "en",
        "macro-author": {
            "names": [
                {
                    "name": "author",
                    "delimiter": ", ",
                    "and": "text",
                    "et-al-min": 7,
                    "et-al-use-first": 6,
                }
            ]
        },
        "macro-title": {"text": {"variable": "title", "font-style": "italic"}},
        "macro-date": {"date": [{"variable": "issued", "form": "text", "date-parts": ["year"]}]},
        "macro-container": {"text": {"variable": "container-title", "font-style": "italic"}},
        "macro-identifier": {
            "choose": [
                {
                    "if": {"variable": "DOI"},
                    "then": {"text": {"prefix": "https://doi.org/", "variable": "DOI"}},
                    "else": [
                        {
                            "if": {"variable": "URL"},
                            "then": {"text": {"variable": "URL"}},
                        },
                        {
                            "if": {"variable": "archive"},
                            "then": {
                                "text": [
                                    {"term": "archive", "suffix": ":"},
                                    {"variable": "archive_location"},
                                ]
                            },
                        },
                    ],
                }
            ]
        },
        "citation": {
            "layout": {
                "prefix": "[",
                "suffix": "]",
                "delimiter": ", ",
                "group": [{"text": {"variable": "citation-number"}}],
            }
        },
        "bibliography": {
            "second-field-align": "flush",
            "layout": {
                "entry": {
                    "group": [
                        {"text": {"variable": "citation-number", "suffix": "."}},
                        {"macro": "macro-author", "suffix": "."},
                        {"macro": "macro-title", "suffix": "."},
                        {"macro": "macro-container", "suffix": "."},
                        {"macro": "macro-date", "suffix": "."},
                        {"macro": "macro-identifier", "prefix": " "},
                    ]
                }
            },
        },
    }
    path.write_text(json.dumps(style, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def check_package(paths: dict[str, Path], tex: str, markdown: str, bib_entries: dict[str, str]) -> dict[str, Any]:
    cited = citation_order(tex)
    md_cited = sorted(set(re.findall(r"\[(\d+(?:,\d+)*)\]", markdown)))
    abstract_match = re.search(r"## Abstract(.*?)(?=\n## )", markdown, re.DOTALL)
    abstract = abstract_match.group(1) if abstract_match else ""
    abstract_words = re.findall(r"[A-Za-z0-9][A-Za-z0-9'-]*", abstract)
    keyword_line = next(
        (line for line in markdown.splitlines() if line.startswith("**Keywords:**")),
        "",
    )
    keywords = [
        item.strip()
        for item in keyword_line.removeprefix("**Keywords:**").split(";")
        if item.strip()
    ]
    checks = {
        "source_identity": {
            "pass": subprocess_git_head_blob(TEX) == subprocess_git_blob(TEX),
            "tex_sha256": sha256(TEX),
            "head_blob": subprocess_git_head_blob(TEX),
            "working_blob": subprocess_git_blob(TEX),
        },
        "structured_abstract": {
            "pass": all(marker in abstract for marker in ("Purpose.", "Methods.", "Results.", "Conclusion.")),
            "word_count": len(abstract_words),
            "word_range_150_250": 150 <= len(abstract_words) <= 250,
        },
        "keywords": {
            "pass": 4 <= len(keywords) <= 6,
            "count": len(keywords),
            "keywords": keywords,
        },
        "citations": {
            "pass": len(cited) == 24,
            "unique_numeric_citations": len(cited),
            "keys": cited,
        },
        "bibliography": {
            "pass": len(bib_entries) == 24 and set(cited) == set(bib_entries),
            "entries": len(bib_entries),
            "missing": sorted(set(cited) - set(bib_entries)),
            "uncited": sorted(set(bib_entries) - set(cited)),
        },
        "figures": {
            "pass": len(re.findall(r"!\[Figure [123]\.", markdown)) == 3,
            "count": len(re.findall(r"!\[Figure [123]\.", markdown)),
        },
        "tables": {
            "pass": len(re.findall(r"^\|(?:---\|)+$", markdown, re.MULTILINE)) >= 3,
            "caption_count": len(re.findall(r"^\*\*Table(?:\.| \d)", markdown, re.MULTILINE)),
            "editable_markdown_tables": len(re.findall(r"^\|(?:---\|)+$", markdown, re.MULTILINE)),
        },
        "owner_placeholders": {
            "pass": markdown.count("TBD_OWNER") >= 4,
            "count": markdown.count("TBD_OWNER"),
        },
        "declarations": {
            "pass": all(
                marker in markdown
                for marker in (
                    "## Declarations",
                    "Funding:",
                    "Conflicts of interest:",
                    "Patent status and inventors:",
                    "Artifact license and",
                    "Submission channel, dates, fees",
                )
            )
        },
        "data_availability": {"pass": "## Data Availability" in markdown},
        "two_case_boundary": {
            "pass": "Case 1" in markdown and "Case 2" in markdown,
            "excludes_p1_p2": not re.search(r"\bP[12]\b", markdown),
        },
        "raw_bibtex_absent": {"pass": not re.search(r"^@\w+\{", markdown, re.MULTILINE)},
        "files": {name: {"exists": path.is_file(), "sha256": sha256(path)} for name, path in paths.items()},
    }
    if not all(item.get("pass", True) for item in checks.values() if isinstance(item, dict) and "pass" in item):
        failures = [name for name, item in checks.items() if isinstance(item, dict) and item.get("pass") is False]
        raise SystemExit("word_source_check_failed:" + ",".join(failures))
    return checks


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check-json", type=Path, required=True)
    parser.add_argument("--manifest-json", type=Path, required=True)
    args = parser.parse_args()
    if not TEX.is_file() or not BIB.is_file():
        raise SystemExit("canonical_paper_e_source_missing")
    for directory in (HERE, HERE / "figures"):
        directory.mkdir(parents=True, exist_ok=True)
    tex = TEX.read_text(encoding="utf-8")
    bib = BIB.read_text(encoding="utf-8")
    entries = parse_bib(bib)
    order = citation_order(tex)
    markdown = convert_manuscript(tex)
    reference_lines = ["# Formatted Reference List", "", f"Count: {len(order)}", ""]
    body_reference_lines: list[str] = []
    for index, key in enumerate(order, start=1):
        if key not in entries:
            raise SystemExit(f"missing_bibliography_entry:{key}")
        reference = format_reference(index, entries[key])
        reference_lines.extend([reference, ""])
        body_reference_lines.extend([reference, ""])
    if any(entry.get("author", "").startswith("Unknown") for entry in entries.values()):
        raise SystemExit("bibliography_author_missing")
    markdown = markdown.rstrip() + "\n\n" + "\n".join(body_reference_lines).rstrip() + "\n"
    (HERE / "paper_e_word.md").write_text(markdown, encoding="utf-8")
    (HERE / "REFERENCE_LIST.md").write_text("\n".join(reference_lines).rstrip() + "\n", encoding="utf-8")
    shutil.copy2(BIB, HERE / "references.bib")
    for figure in sorted(FIGURES.iterdir()):
        if figure.is_file():
            shutil.copy2(figure, HERE / "figures" / figure.name)
    write_csl(HERE / "numeric-bracket.csl")
    build_reference_doc(HERE / "reference_style.docx")
    paths = {
        "paper_e_word.md": HERE / "paper_e_word.md",
        "reference_list": HERE / "REFERENCE_LIST.md",
        "references.bib": HERE / "references.bib",
        "numeric-bracket.csl": HERE / "numeric-bracket.csl",
        "reference_style.docx": HERE / "reference_style.docx",
    }
    checks = check_package(paths, tex, markdown, entries)
    receipt = {
        "schema": "paper_e_word_source_check_v1",
        "status": "PASS",
        "date": DATE,
        "sole_content_source": {
            "path": str(TEX.relative_to(REPO_ROOT)),
            "git_blob": subprocess_git_blob(TEX),
            "sha256": sha256(TEX),
        },
        "checks": checks,
        "claim_boundary": (
            "Source-package validation only; no Windows Pandoc conversion, DOCX visual acceptance, "
            "C acceptance, submission or publication claim."
        ),
    }
    args.check_json.parent.mkdir(parents=True, exist_ok=True)
    args.check_json.write_text(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    manifest = {
        "schema": "paper_e_word_conversion_manifest_v1",
        "status": "READY_FOR_D_PANDOC_3_2_1",
        "date": DATE,
        "canonical_source": str(TEX.relative_to(REPO_ROOT)),
        "canonical_source_sha256": sha256(TEX),
        "output": "paper_e.docx",
        "expected_reference_docx": "reference_style.docx",
        "body_style": "10 pt Times New Roman when supported by reference_style.docx",
        "files": {
            path.name: {"bytes": path.stat().st_size, "sha256": sha256(path)}
            for path in sorted(HERE.glob("*"))
            if path.is_file() and path.name not in {"CONVERSION_MANIFEST.json", "SOURCE_CHECK_RECEIPT.json"}
        },
        "figure_files": {
            path.name: {"bytes": path.stat().st_size, "sha256": sha256(path)}
            for path in sorted((HERE / "figures").glob("*"))
            if path.is_file()
        },
    }
    args.manifest_json.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": "PASS", "abstract_words": checks["structured_abstract"]["word_count"], "references": len(order)}, sort_keys=True))
    return 0


def subprocess_git_blob(path: Path) -> str:
    import subprocess

    result = subprocess.run(
        ["git", "hash-object", str(path)],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def subprocess_git_head_blob(path: Path) -> str:
    import subprocess

    relative = path.relative_to(REPO_ROOT).as_posix()
    result = subprocess.run(
        ["git", "rev-parse", f"HEAD:{relative}"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


if __name__ == "__main__":
    raise SystemExit(main())
