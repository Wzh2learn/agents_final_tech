"""Build the anonymous IEEE review PDF from the maintained Markdown paper."""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile


ROOT = Path(__file__).resolve().parent
MANUSCRIPT = ROOT.parent / "IJCNN_MANUSCRIPT.md"
FIGURES = {
    "method": (
        "Three interventions on executed program states. Stage A allocates counterexamples before and after recovery. "
        "Stage B labels distinct local states using one fixed-input teacher trajectory per source. "
        "Stage C intervenes on scale with the arithmetic program fixed.",
        True,
    ),
    "finqa_budget": (
        "FinQA budget curves on development, forward and confirmation panels. The top row counts selected tasks "
        "and the bottom counts their teacher tokens. Random is the expectation from the shared pool.",
        True,
    ),
    "recovery_harm": (
        "Recovered and harmed answers for DEV64 local correction, TAT-QA development disclosure and the adaptive "
        "128- and 160-table scale extension on the reused 64-case TAT-QA cohort. Each panel states its baseline. "
        "Parentheses give final correct counts.",
        True,
    ),
}
TABLE_FORMATS = {
    "1": ("lrr", False),
    "2": ("lrrrrrrrrr", True),
    "3": ("lrrr", False),
    "4": ("lrrrr", False),
}
TABLE = re.compile(r"(?m)^\*\*Table (\d+)\. ([^\n]+)\*\*\n\n((?:\|[^\n]+\|\n?)+)")
CITATION = re.compile(r"\[([1-9]\d*(?:,\s*[1-9]\d*)*)\]")


def latex(source, *, shift_heading=False):
    command = ["pandoc", "--from=markdown", "--to=latex", "--wrap=none"]
    if shift_heading:
        command.append("--shift-heading-level-by=-1")
    return subprocess.run(
        command,
        input=source, text=True, encoding="utf-8", capture_output=True, check=True,
    ).stdout.strip()


def one_table(match):
    number, caption, markdown_rows = match.groups()
    columns, wide = TABLE_FORMATS[number]
    rows = [[cell.strip() for cell in line.strip("|").split("|")] for line in markdown_rows.splitlines()]
    if not all(len(row) == len(columns) for row in rows):
        raise ValueError(f"Unexpected number of columns in Table {number}")

    def row_tex(row):
        parts = [re.sub(r"\*\*(.*?)\*\*", r"\\textbf{\1}", cell) for cell in row]
        return " & ".join(parts) + r" \\"

    environment = "table*" if wide else "table"
    return "\n\n" + "\n".join([
        rf"\begin{{{environment}}}[!t]",
        r"\centering",
        rf"\caption{{{caption}}}",
        rf"\label{{tab:{number}}}",
        rf"\begin{{tabular}}{{@{{}}{columns}@{{}}}}",
        r"\toprule", row_tex(rows[0]), r"\midrule",
        *(row_tex(row) for row in rows[2:]),
        r"\bottomrule",
        r"\end{tabular}",
        rf"\end{{{environment}}}",
    ]) + "\n\n"


def one_figure(match):
    name = match.group(1)
    caption, wide = FIGURES[name]
    if not (ROOT / "figures" / f"{name}.pdf").is_file():
        raise FileNotFoundError(f"Missing figure asset: figures/{name}.pdf")
    env = "figure*" if wide else "figure"
    width = r"\textwidth" if wide else r"\columnwidth"
    return "\n".join([
        rf"\begin{{{env}}}[!t]",
        r"\centering",
        rf"\includegraphics[width={width}]{{figures/{name}.pdf}}",
        rf"\caption{{{caption}}}",
        rf"\label{{fig:{name}}}",
        rf"\end{{{env}}}",
    ])


def citations(match):
    keys = ",".join(f"r{item.strip()}" for item in match.group(1).split(","))
    return rf"\cite{{{keys}}}"


def create_tex():
    source = MANUSCRIPT.read_text(encoding="utf-8")
    title = latex(source.splitlines()[0].removeprefix("# "))
    _, abstract = source.split("\n## Abstract\n", 1)
    abstract, keywords = abstract.split("\n## Index Terms\n", 1)
    keywords, body = keywords.split("\n## Introduction\n", 1)
    body, references = body.split("\n## References\n", 1)
    references, _ = references.split("\n## Writing provenance\n", 1)
    body = "## Introduction\n" + body
    body = re.sub(r"(?m)^(### )[A-Z]\. ", r"\1", body)
    body = body.replace("## Acknowledgment\n", "\\section*{Acknowledgment}\n")
    body = TABLE.sub(one_table, body)
    pattern = r"(?m)^!\[[^\n]+\]\(ijcnn_ieee/figures/([a-z_]+)\.png\)$"
    if sorted(re.findall(pattern, body)) != sorted(FIGURES):
        raise ValueError("Expected exactly one image for each manuscript figure")
    body = re.sub(pattern, one_figure, body)
    references = re.findall(r"(?m)^\[(\d+)\]\s+(.+)$", references)
    known_keys = {number for number, _ in references}
    body = CITATION.sub(lambda match: citations(match) if
                        set(re.split(r",\s*", match.group(1))) <= known_keys else match.group(0), body)
    cited = {key.removeprefix("r") for item in re.findall(r"\\cite\{([^{}]+)\}", body) for key in item.split(",")}
    if cited != known_keys:
        raise ValueError("Cited identifiers and bibliography entries must match")
    bib = "\n".join(rf"\bibitem{{r{number}}} " + latex(item) for number, item in references)
    return "\n".join((
        r"\documentclass[10pt,letterpaper,conference]{IEEEtran}",
        r"\usepackage[T1]{fontenc}",
        r"\usepackage{amsmath,amssymb,booktabs,graphicx,cite,url}",
        r"\usepackage[hidelinks]{hyperref}",
        rf"\hypersetup{{pdfauthor={{Anonymous Authors}},pdftitle={{{title}}}}}",
        r"\begin{document}",
        rf"\title{{{title}}}",
        r"\author{\IEEEauthorblockN{Anonymous Authors}}",
        r"\maketitle",
        r"\begin{abstract}", latex(abstract), r"\end{abstract}",
        r"\begin{IEEEkeywords}", latex(keywords), r"\end{IEEEkeywords}",
        latex(body, shift_heading=True),
        r"\begin{thebibliography}{99}", bib, r"\end{thebibliography}",
        r"\end{document}",
        "",
    ))


def compile_pdf(engine, class_file):
    with tempfile.TemporaryDirectory(prefix="ijcnn-ieee-") as folder:
        work = Path(folder)
        shutil.copy2(ROOT / "main.tex", work / "main.tex")
        if (ROOT / "figures").exists():
            shutil.copytree(ROOT / "figures", work / "figures")
        if class_file:
            shutil.copy2(class_file, work / "IEEEtran.cls")
        command = [engine, "--keep-logs", "main.tex"]
        result = subprocess.run(command, cwd=work)
        log = work / "main.log"
        if log.exists():
            for line in log.read_text(encoding="utf-8", errors="replace").splitlines():
                if "Overfull" in line or "undefined" in line or "Output written" in line:
                    print(line)
        result.check_returncode()
        shutil.copy2(work / "main.pdf", ROOT / "main.pdf")


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--tectonic", default=os.environ.get("TECTONIC"))
    cli.add_argument("--ieee-class", type=Path, help="Optional path to the unmodified official IEEEtran.cls")
    args = cli.parse_args()
    tex = create_tex()
    with (ROOT / "main.tex").open("w", encoding="utf-8", newline="\n") as stream:
        stream.write(tex)
    if args.tectonic:
        compile_pdf(args.tectonic, args.ieee_class)


if __name__ == "__main__":
    main()
