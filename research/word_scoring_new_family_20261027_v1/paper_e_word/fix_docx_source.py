#!/usr/bin/env python3
"""Make the Pandoc Word source structurally convertible without changing claims."""

from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "paper_e_word.md"
BIB = ROOT / "references.bib"
OUTPUT = ROOT / "paper_e_word_fixed.md"


def citation_order() -> dict[str, int]:
    text = BIB.read_text(encoding="utf-8")
    keys = re.findall(r"(?m)^@\w+\{([^,\s]+)\s*,", text)
    return {key: index for index, key in enumerate(keys, start=1)}


def normalize_structure(lines: list[str]) -> list[str]:
    out: list[str] = []
    for index, line in enumerate(lines):
        is_heading = bool(re.match(r"^#{1,6}\s", line))
        is_table_row = line.startswith("|")
        previous = out[-1] if out else ""
        previous_is_table = previous.startswith("|")
        if is_heading and previous and previous != "":
            out.append("")
        if is_table_row and not previous_is_table and previous and previous != "":
            out.append("")
        out.append(line)
        if is_heading:
            nxt = lines[index + 1] if index + 1 < len(lines) else ""
            if nxt and not nxt.startswith("#"):
                out.append("")
        if is_table_row:
            nxt = lines[index + 1] if index + 1 < len(lines) else ""
            if nxt and not nxt.startswith("|"):
                out.append("")
    return out


def replace_citations(text: str, order: dict[str, int]) -> str:
    pattern = re.compile(r"\[([A-Za-z][A-Za-z0-9_]+(?:,[A-Za-z][A-Za-z0-9_]+)*)\]")

    def repl(match: re.Match[str]) -> str:
        keys = [item.strip() for item in match.group(1).split(",")]
        numbers = [str(order[key]) for key in keys if key in order]
        return "[" + ",".join(numbers) + "]" if len(numbers) == len(keys) else match.group(0)

    return pattern.sub(repl, text)


def convert_latex_lists(text: str) -> str:
    text = text.replace(r"\begin{itemize}", "").replace(r"\end{itemize}", "")
    text = re.sub(r"^\s*\\item\s+", "- ", text, flags=re.MULTILINE)
    return text


def main() -> int:
    text = SOURCE.read_text(encoding="utf-8")
    start = text.find("---\n")
    end = text.find("\n---\n", start + 4)
    if start == 0 and end > 0:
        body = text[end + 5 :].lstrip("\n")
        text = (
            "---\n"
            "title: \"Visibility Is Not Detection: Auditing Measurement Boundaries "
            "in Staged and Evidence-Ranking Evaluation\"\n"
            "author: []\n"
            "date: \"\"\n"
            "lang: en-US\n"
            "---\n\n"
            "Author names: TBD_OWNER  \n"
            "Affiliations: TBD_OWNER  \n"
            "Corresponding author and contact: TBD_OWNER\n\n"
            + body
        )
    text = convert_latex_lists(text)
    text = text.replace(
        "\\[\nS(n)=\\sum_{c\\in C(n)} \\frac{w(c)}{\\sum_{j\\in C(n)}w(j)}S(c).\n\\]",
        "S(n) = sum over child nodes c in C(n) of "
        "[w(c) / sum of w(j) for j in C(n)] x S(c).",
    )
    text = text.replace(
        "\\[\n\\Gamma={0.2,0.3,0.5,0.7,0.9}.\n\\]",
        "Gamma = {0.2, 0.3, 0.5, 0.7, 0.9}.",
    )
    text = replace_citations(text, citation_order())
    text = "\n".join(normalize_structure(text.splitlines())) + "\n"
    OUTPUT.write_text(text, encoding="utf-8")
    print(OUTPUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
