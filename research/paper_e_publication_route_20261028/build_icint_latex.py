#!/usr/bin/env python3
"""Generate an anonymized IEEEtran draft from the maintained Markdown source."""
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "paper_e_icint_draft.md"
OUTPUT = ROOT / "icint_latex" / "main.tex"
PANDOC = "D:/pandocLatex2word/pandoc.exe"
INTERPRETATION_TABLE = ("| Case | Tempting interpretation | Supported interpretation after audit |\n"
                        "| --- | --- | --- |\n"
                        "| Document | Lower detection means weaker ranking | The reported rates differ, but rankings coincide in the single-leaf setting. |\n"
                        "| FinRank | Absolute score changes imply a changed comparison | The random-minus-hard gap stays positive under both inspected tie policies. |\n"
                        "| Retrieval | A higher mean establishes every system ordering | The paired test supports only some differences; unsupported pairs are not proven equal. |")
INTERPRETATION_LATEX = r"""```{=latex}
\begin{table}[htbp]
\caption{Interpretations qualified or retained by the three audits.}
\label{tab:interpretations}
\centering
\footnotesize
\renewcommand{\arraystretch}{1.12}
\begin{tabular}{@{}>{\raggedright\arraybackslash}p{.18\columnwidth}>{\raggedright\arraybackslash}p{.34\columnwidth}>{\raggedright\arraybackslash}p{.36\columnwidth}@{}}
\hline
Case & Tempting interpretation & Supported interpretation \\
\hline
Document & Lower detection means weaker ranking & Rates differ; ranks coincide in the single-leaf setting. \\
FinRank & Absolute score changes imply a changed comparison & The random-minus-hard gap stays positive under both inspected tie policies. \\
Retrieval & A higher mean establishes every system ordering & The paired test supports some differences; other pairs are not proven equal. \\
\hline
\end{tabular}
\end{table}
```"""
FINRANK_TABLE = ("| System | Tie policy | Hard (%) | Random (%) | Gap (pp) |\n"
                 "| --- | --- | ---: | ---: | ---: |\n"
                 "| TF-IDF | Positive | 77.756 | 91.935 | 14.179 |\n"
                 "| TF-IDF | Strict win | 77.030 | 90.850 | 13.821 |\n"
                 "| BM25 | Positive | 74.780 | 87.789 | 13.009 |\n"
                 "| BM25 | Strict win | 74.094 | 86.760 | 12.666 |")
FINRANK_LATEX = r"""```{=latex}
\begin{table}[htbp]
\caption{FinRank pairwise accuracy under two tie policies; gaps are computed before rounding.}
\label{tab:finrank}
\centering
\begin{tabular}{llrrr}
\hline
System & Policy & Hard (\%) & Random (\%) & Gap (pp) \\
\hline
TF-IDF & Positive & 77.756 & 91.935 & 14.179 \\
TF-IDF & Strict & 77.030 & 90.850 & 13.821 \\
BM25 & Positive & 74.780 & 87.789 & 13.009 \\
BM25 & Strict & 74.094 & 86.760 & 12.666 \\
\hline
\end{tabular}
\end{table}
```"""


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
    if body.count("# Acknowledgment\n") != 1:
        raise ValueError("Expected one acknowledgment")
    body = body.replace("# Acknowledgment\n", "```{=latex}\n\\section*{Acknowledgment}\n```\n")
    if body.count(INTERPRETATION_TABLE) != 1:
        raise ValueError("Expected interpretation table not found exactly once")
    body = body.replace(INTERPRETATION_TABLE, INTERPRETATION_LATEX)
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
    if body.count(FINRANK_TABLE) != 1:
        raise ValueError("Expected FinRank table not found exactly once")
    body = body.replace(FINRANK_TABLE, FINRANK_LATEX)
    body = re.sub(r"\[(\d+)\]", lambda m: r"\cite{r" + m.group(1) + "}", body)
    items = re.findall(r"(?ms)^\[(\d+)\]\s*(.*?)(?=^\[\d+\]|\Z)", refs)
    if not items or [n for n, _ in items] != [str(n) for n in range(1, len(items) + 1)]:
        raise ValueError("Unexpected reference numbering")
    references = "\n".join(r"\bibitem{r" + n + "} " + latex(item) for n, item in items)
    document = (r"\documentclass[conference]{IEEEtran}" + "\n" +
                r"\usepackage[T1]{fontenc}" + "\n" + r"\usepackage{cite}" + "\n" +
                r"\usepackage{url}" + "\n" + r"\usepackage{array}" + "\n" + r"\begin{document}" + "\n" +
                r"\title{From Scores to Supported Claims: Measurement Audits of Document and Retrieval Evaluation}" + "\n" +
                r"\author{}" + "\n" + r"\maketitle" + "\n" +
                r"\begin{abstract}" + "\n" + latex(abstract) + "\n" + r"\end{abstract}" + "\n" +
                r"\begin{IEEEkeywords}" + "\n" + latex(keywords) + "\n" + r"\end{IEEEkeywords}" + "\n" +
                latex(body) + "\n" + r"\begin{thebibliography}{" + str(len(items)) + "}\n" + references + "\n" +
                r"\end{thebibliography}" + "\n" + r"\end{document}" + "\n")
    with OUTPUT.open("w", encoding="utf-8", newline="\n") as output:
        output.write(document)
    print("Wrote", OUTPUT)


if __name__ == "__main__":
    main()
