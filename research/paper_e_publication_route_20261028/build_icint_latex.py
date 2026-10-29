#!/usr/bin/env python3
"""Generate an anonymized IEEEtran draft from the maintained Markdown source."""
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "paper_e_icint_draft.md"
OUTPUT = ROOT / "icint_latex" / "main.tex"
PANDOC = "D:/pandocLatex2word/pandoc.exe"


def latex(text):
    return subprocess.run([PANDOC, "--from=markdown+raw_tex", "--to=latex"],
                          input=text, text=True, encoding="utf-8", capture_output=True,
                          check=True).stdout.strip()


def main():
    source = SOURCE.read_text(encoding="utf-8")
    source = source.split("---", 2)[2].strip()
    abstract, remainder = source.split("\n\n", 1)
    keywords, body = remainder.split("\n\n", 1)
    assert abstract.startswith("**Abstract—** ") and keywords.startswith("**Index Terms—** ")
    abstract = abstract.removeprefix("**Abstract—** ")
    keywords = keywords.removeprefix("**Index Terms—** ")
    body, refs = body.split("# References", 1)
    body = re.sub(r"(?m)^# [IVX]+\. ", "# ", body)
    table = ("| Original operating point | Flat | Hierarchical |\n"
             "| --- | ---: | ---: |\n"
             "| Source tables | 75/95 | 20/95 |\n"
             "| Header injections | 85/118 | 13/118 |")
    if body.count(table) != 1:
        raise ValueError("Expected detection table not found exactly once")
    raw_table = r"""```{=latex}
\begin{table}[t]
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
```"""
    body = body.replace(table, raw_table)
    body = re.sub(r"\[(\d+)\]", lambda m: r"\cite{r" + m.group(1) + "}", body)
    items = re.findall(r"(?ms)^\[(\d+)\]\s*(.*?)(?=^\[\d+\]|\Z)", refs)
    if [n for n, _ in items] != [str(n) for n in range(1, 10)]:
        raise ValueError("Unexpected reference numbering")
    references = "\n".join(r"\bibitem{r" + n + "} " + latex(item) for n, item in items)
    document = (r"\documentclass[conference]{IEEEtran}" + "\n" +
                r"\usepackage[T1]{fontenc}" + "\n" + r"\usepackage{cite}" + "\n" +
                r"\usepackage{url}" + "\n" + r"\begin{document}" + "\n" +
                r"\title{From Scores to Supported Claims: Measurement Audits of Document and Retrieval Evaluation}" + "\n" +
                r"\author{}" + "\n" + r"\maketitle" + "\n" +
                r"\begin{abstract}" + "\n" + latex(abstract) + "\n" + r"\end{abstract}" + "\n" +
                r"\begin{IEEEkeywords}" + "\n" + latex(keywords) + "\n" + r"\end{IEEEkeywords}" + "\n" +
                latex(body) + "\n" + r"\begin{thebibliography}{9}" + "\n" + references + "\n" +
                r"\end{thebibliography}" + "\n" + r"\end{document}" + "\n")
    with OUTPUT.open("w", encoding="utf-8", newline="\n") as output:
        output.write(document)
    print("Wrote", OUTPUT)


if __name__ == "__main__":
    main()
