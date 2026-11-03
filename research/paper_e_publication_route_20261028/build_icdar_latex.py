#!/usr/bin/env python3
"""Generate an ICDAR-format exploratory backup from the ICINT working source.

This version is a template feasibility draft, not a separate submission or
an already adapted document-analysis contribution.
"""
import argparse
from pathlib import Path
import re

from build_icint_latex import (
    DETECTION_LATEX, DETECTION_TABLE, FINRANK_LATEX, FINRANK_TABLE,
    INTERPRETATION_LATEX, INTERPRETATION_TABLE, latex,
)

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "paper_e_icint_draft.md"
OUTPUT = ROOT / "icdar_latex" / "main.tex"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=SOURCE)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    source_text = args.source.read_text(encoding="utf-8")
    frontmatter, source = source_text.split("---", 2)[1:]
    title_match = re.search(r'(?m)^title:\s*"([^"]+)"\s*$', frontmatter)
    if title_match is None:
        raise ValueError("Missing quoted manuscript title")
    title = title_match.group(1)
    source = source.strip()
    abstract, rest = source.split("\n\n", 1)
    keywords, body = rest.split("\n\n", 1)
    abstract = abstract.removeprefix("**Abstract—** ")
    keywords = keywords.removeprefix("**Index Terms—** ").rstrip(".")
    body, refs = body.split("# References", 1)
    body = re.sub(r"(?m)^# [IVX]+\. ", "# ", body)
    if body.count("# Acknowledgment\n") != 1:
        raise ValueError("Expected one acknowledgment")
    body = body.replace("# Acknowledgment\n", "```{=latex}\n\\section*{Acknowledgment}\n```\n")
    if body.count(INTERPRETATION_TABLE) != 1:
        raise ValueError("Expected interpretation table not found exactly once")
    body = body.replace(INTERPRETATION_TABLE, INTERPRETATION_LATEX)
    if body.count(DETECTION_TABLE) != 1:
        raise ValueError("Expected detection table not found exactly once")
    body = body.replace(DETECTION_TABLE, DETECTION_LATEX)
    if body.count(FINRANK_TABLE) != 1:
        raise ValueError("Expected FinRank table not found exactly once")
    finrank = FINRANK_LATEX.replace(r"\begin{tabular}{llrrr}",
                                  "\\setlength{\\tabcolsep}{6pt}\n" + r"\begin{tabular}{llrrr}")
    body = body.replace(FINRANK_TABLE, finrank)
    body = re.sub(r"\[(\d+)\]", lambda m: r"\cite{r" + m.group(1) + "}", body)
    items = re.findall(r"(?ms)^\[(\d+)\]\s*(.*?)(?=^\[\d+\]|\Z)", refs)
    if not items or [n for n, _ in items] != [str(n) for n in range(1, len(items) + 1)]:
        raise ValueError("Unexpected reference numbering")
    references = "\n".join(r"\bibitem{r" + n + "} " + latex(item) for n, item in items)
    document = (r"\documentclass[runningheads]{llncs}" + "\n" +
                r"\usepackage[T1]{fontenc}" + "\n" + r"\usepackage{url}" + "\n" + r"\usepackage{array}" + "\n" +
                r"\begin{document}" + "\n" + r"\emergencystretch=2em" + "\n" +
                r"\title{" + latex(title) + "}\n" +
                r"\titlerunning{Measurement Audits of Document and Retrieval Evaluation}" + "\n" +
                r"\author{Anonymous Authors}" + "\n" + r"\institute{}" + "\n" +
                r"\maketitle" + "\n" + r"\begin{abstract}" + "\n" + latex(abstract) + "\n" +
                r"\keywords{" + latex(keywords) + "}\n" + r"\end{abstract}" + "\n" +
                latex(body) + "\n" + r"\begin{thebibliography}{" + str(len(items)) + "}\n" + references + "\n" +
                r"\end{thebibliography}" + "\n" + r"\end{document}" + "\n")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="\n") as output:
        output.write(document)
    print("Wrote", args.output)


if __name__ == "__main__":
    main()
