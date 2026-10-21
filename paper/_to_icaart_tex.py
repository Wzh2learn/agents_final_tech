#!/usr/bin/env python3
"""Build the ICAART/SCITEPRESS submission TeX from the canonical manuscript."""

from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "paper" / "saner_rene_manuscript_v1.tex"
MARKDOWN = ROOT / "paper" / "saner_rene_manuscript_v1.md"
OUTPUT = ROOT / "paper" / "icaart_2027_submission_v1" / "manuscript.tex"


def inline_tex(value: str) -> str:
    code: list[str] = []

    def stash(match: re.Match[str]) -> str:
        code.append(match.group(1))
        return f"\x00{len(code) - 1}\x00"

    value = re.sub(r"`([^`]+)`", stash, value)
    value = value.replace("\\", r"\textbackslash{}")
    for source, target in (
        ("&", r"\&"),
        ("%", r"\%"),
        ("$", r"\$"),
        ("#", r"\#"),
        ("_", r"\_"),
        ("{", r"\{"),
        ("}", r"\}"),
        ("~", r"\textasciitilde{}"),
        ("^", r"\textasciicircum{}"),
    ):
        value = value.replace(source, target)
    value = re.sub(r"\*\*([^*]+)\*\*", r"\\textbf{\1}", value)
    value = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"\\emph{\1}", value)
    for index, item in enumerate(code):
        value = value.replace(f"\x00{index}\x00", r"\texttt{" + inline_tex(item) + "}")
    return value


def markdown_abstract() -> str:
    text = MARKDOWN.read_text(encoding="utf-8")
    abstract = text.split("## Abstract", 1)[1].split("## 1.", 1)[0].strip()
    return inline_tex(abstract)


def manuscript_body() -> str:
    source = SOURCE.read_text(encoding="utf-8")
    body = source.split(r"\maketitle", 1)[1].rsplit(r"\end{document}", 1)[0]
    body = re.sub(
        r"\\begin\{abstract\}.*?\\end\{abstract\}\s*",
        "",
        body,
        count=1,
        flags=re.DOTALL,
    )
    body = re.sub(
        r"^% NOTE: SVG-only asset[^\n]*\n",
        "",
        body,
        count=1,
        flags=re.MULTILINE,
    )
    body = body.replace(
        r"\includesvg[width=\columnwidth]{../docs/research/figures_saner/fig1_measurement_chain}",
        r"\includegraphics[width=\columnwidth]{figures/fig1_measurement_chain.pdf}",
    )
    body = body.replace(
        r"\includegraphics[width=\columnwidth]{../docs/research/figures_saner/fig2_family_visibility_matrix.png}",
        r"\includegraphics[width=\columnwidth]{figures/fig2_family_visibility_matrix.png}",
    )
    body = body.replace(
        r"\includegraphics[width=\columnwidth]{../docs/research/figures_saner/fig3_localization_ablation.png}",
        r"\includegraphics[width=\columnwidth]{figures/fig3_localization_ablation.png}",
    )
    body = body.replace(
        "\\bibliographystyle{IEEEtran}\n\\bibliography{saner_rene_references}",
        "\\begingroup\\scriptsize\\linespread{0.8}\\selectfont\n"
        "\\bibliographystyle{apalike}\n"
        "\\bibliography{saner_rene_references}\n\\endgroup",
    )
    body = body.replace(r"\begin{table}[t]", r"\begin{table}[htbp]")
    body = body.replace(r"\setlength{\tabcolsep}{3pt}", r"\setlength{\tabcolsep}{1pt}")
    body = body.replace("\\small\n\\setlength{\\tabcolsep}{1pt}", "\\scriptsize\n\\setlength{\\tabcolsep}{1pt}")
    body = re.sub(
        r"\\section\{([^{}]+)\}",
        lambda match: r"\section{\uppercase{" + match.group(1) + "}}",
        body,
    )
    if "../docs/" in body or r"\includesvg" in body:
        raise RuntimeError("unresolved repository figure path")
    return body.strip()


def main() -> int:
    markdown = MARKDOWN.read_text(encoding="utf-8")
    title = markdown.splitlines()[0][2:].strip()
    body = manuscript_body()
    document = rf"""% ICAART 2027 Regular Paper double-blind review build.
% Official SCITEPRESS template files are stored beside this source.
\documentclass[a4paper,twoside]{{article}}
\usepackage{{epsfig}}
\usepackage{{subcaption}}
\usepackage{{calc}}
\usepackage{{amssymb}}
\usepackage{{amstext}}
\usepackage{{amsmath}}
\usepackage{{amsthm}}
\usepackage{{pslatex}}
\usepackage{{apalike}}
\usepackage{{algorithm2e}}
\usepackage{{footmisc}}
\usepackage{{graphicx}}
\usepackage{{array}}
\usepackage{{url}}
\usepackage{{seqsplit}}
\usepackage{{hyperref}}
\usepackage{{SCITEPRESS}}

\begin{{document}}
\title{{{inline_tex(title)}}}
\author{{\authorname{{Anonymous Submission}}
\affiliation{{Double-blind review copy}}
\email{{}}
}}
\keywords{{Measurement Validity, Agent Evaluation, Benchmark Auditing, Reproducibility.}}
\abstract{{{markdown_abstract()}}}

\onecolumn \maketitle \normalsize \setcounter{{footnote}}{{0}} \vfill

{body}

\end{{document}}
"""
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(document)
    print(f"wrote {OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
