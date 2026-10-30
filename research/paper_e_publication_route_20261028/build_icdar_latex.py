#!/usr/bin/env python3
"""Generate an ICDAR-format exploratory backup from the ICINT working source.

This version is a template feasibility draft, not a separate submission or
an already adapted document-analysis contribution.
"""
from pathlib import Path
import re

from build_icint_latex import FINRANK_LATEX, FINRANK_TABLE, latex

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "paper_e_icint_draft.md"
OUTPUT = ROOT / "icdar_latex" / "main.tex"


def main():
    source = SOURCE.read_text(encoding="utf-8").split("---", 2)[2].strip()
    abstract, rest = source.split("\n\n", 1)
    keywords, body = rest.split("\n\n", 1)
    abstract = abstract.removeprefix("**Abstract—** ")
    keywords = keywords.removeprefix("**Index Terms—** ").rstrip(".")
    body, refs = body.split("# References", 1)
    body = re.sub(r"(?m)^# [IVX]+\. ", "# ", body)
    table = ("| Original operating point | Flat | Hierarchical |\n"
             "| --- | ---: | ---: |\n"
             "| Source tables | 75/95 | 20/95 |\n"
             "| Header injections | 85/118 | 13/118 |")
    if body.count(table) != 1:
        raise ValueError("Expected detection table not found exactly once")
    body = body.replace(table, r"""```{=latex}
\begin{table}[htbp]
\caption{Original seed-42 operating-point detection; table and injection counts are different units.}
\label{tab:original-detection}
\centering
\begin{tabular}{lrr}
\hline
Unit & Flat & Hierarchical \\
\hline
Source tables & 75/95 & 20/95 \\
Header injections & 85/118 & 13/118 \\
\hline
\end{tabular}
\end{table}
```""")
    if body.count(FINRANK_TABLE) != 1:
        raise ValueError("Expected FinRank table not found exactly once")
    body = body.replace(FINRANK_TABLE, FINRANK_LATEX)
    body = re.sub(r"\[(\d+)\]", lambda m: r"\cite{r" + m.group(1) + "}", body)
    items = re.findall(r"(?ms)^\[(\d+)\]\s*(.*?)(?=^\[\d+\]|\Z)", refs)
    if [n for n, _ in items] != [str(n) for n in range(1, 10)]:
        raise ValueError("Unexpected reference numbering")
    references = "\n".join(r"\bibitem{r" + n + "} " + latex(item) for n, item in items)
    document = (r"\documentclass[runningheads]{llncs}" + "\n" +
                r"\usepackage[T1]{fontenc}" + "\n" + r"\usepackage{url}" + "\n" +
                r"\begin{document}" + "\n" + r"\emergencystretch=2em" + "\n" +
                r"\title{From Scores to Supported Claims: Measurement Audits of Document and Retrieval Evaluation}" + "\n" +
                r"\titlerunning{Measurement Audits of Document and Retrieval Evaluation}" + "\n" +
                r"\author{Anonymous Authors}" + "\n" + r"\institute{}" + "\n" +
                r"\maketitle" + "\n" + r"\begin{abstract}" + "\n" + latex(abstract) + "\n" +
                r"\keywords{" + latex(keywords) + "}\n" + r"\end{abstract}" + "\n" +
                latex(body) + "\n" + r"\begin{thebibliography}{9}" + "\n" + references + "\n" +
                r"\end{thebibliography}" + "\n" + r"\end{document}" + "\n")
    with OUTPUT.open("w", encoding="utf-8", newline="\n") as output:
        output.write(document)
    print("Wrote", OUTPUT)


if __name__ == "__main__":
    main()
