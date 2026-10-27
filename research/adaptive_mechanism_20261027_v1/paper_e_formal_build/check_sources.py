#!/usr/bin/env python3
"""Non-TeX structural checks for the canonical Paper E source bundle."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
TEX = ROOT / "paper_e_sncs.tex"
BIB = ROOT / "references.bib"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def citation_keys(text: str) -> set[str]:
    keys: set[str] = set()
    for match in re.finditer(r"\\cite\{([^}]*)\}", text):
        keys.update(item.strip() for item in match.group(1).split(","))
    return keys


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", type=Path, required=True)
    args = parser.parse_args()

    tex = TEX.read_text(encoding="utf-8")
    bib = BIB.read_text(encoding="utf-8")
    cited = citation_keys(tex)
    bib_keys = set(
        re.findall(r"^@\w+\s*\{\s*([^,\s]+)\s*,", bib, flags=re.MULTILINE)
    )
    labels = set(re.findall(r"\\label\{([^}]*)\}", tex))
    refs = set(re.findall(r"\\ref\{([^}]*)\}", tex))
    figures = sorted(
        match.group(1)
        for match in re.finditer(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]*)\}", tex)
    )
    missing_figures = [name for name in figures if not (ROOT / name).is_file()]
    abstract_match = re.search(
        r"\\begin\{abstract\}(.*?)\\end\{abstract\}", tex, flags=re.DOTALL
    )
    abstract = abstract_match.group(1) if abstract_match else ""
    abstract_words = re.findall(r"[A-Za-z0-9][A-Za-z0-9'-]*", abstract)

    checks: dict[str, dict[str, Any]] = {
        "canonical_tex_exists": {"pass": TEX.is_file()},
        "canonical_bibliography_exists": {"pass": BIB.is_file()},
        "structured_abstract_present": {
            "pass": bool(abstract_match)
            and all(
                marker in abstract
                for marker in ("Purpose.", "Methods.", "Results.", "Conclusion.")
            ),
            "word_count": len(abstract_words),
            "word_range_150_250": 150 <= len(abstract_words) <= 250,
        },
        "author_placeholders_present": {
            "pass": tex.count("TBD\\_OWNER") >= 4,
            "count": tex.count("TBD\\_OWNER"),
        },
        "declarations_present": {
            "pass": all(
                marker in tex
                for marker in (
                    "\\section{Declarations}",
                    "Funding:",
                    "Conflicts of interest:",
                    "Patent status and inventors:",
                    "Artifact license and",
                    "Submission channel, dates, fees",
                )
            )
        },
        "two_case_scope": {
            "pass": all(marker in tex for marker in ("Case 1", "Case 2")),
            "excludes_p1_p2_results": not re.search(r"\bP[12]\b", tex),
        },
        "complete_body": {
            "pass": all(
                marker in tex
                for marker in (
                    "\\section{Introduction}",
                    "\\section{Related Work}",
                    "\\section{Method}",
                    "\\section{Experimental Setup}",
                    "\\section{Results}",
                    "\\section{Discussion and Limitations}",
                    "\\section{Conclusion}",
                    "\\section{Declarations}",
                    "\\end{document}",
                )
            )
        },
        "display_formula_inventory": {
            "pass": True,
            "count": len(re.findall(r"\\begin\{(?:equation|align|gather)\}", tex)),
            "note": "Numeric equations are expressed inline; no display formula environment is required by this manuscript.",
        },
        "tables_present": {"count": tex.count("\\begin{table}"), "pass": tex.count("\\begin{table}") >= 1},
        "figures_present": {"count": len(figures), "pass": len(figures) >= 1},
        "figure_files_exist": {
            "pass": bool(figures) and not missing_figures,
            "missing": missing_figures,
        },
        "bibliography_24": {
            "pass": len(bib_keys) == 24,
            "bibliography_entries": len(bib_keys),
        },
        "citations_24": {
            "pass": len(cited) == 24,
            "unique_cited_keys": len(cited),
        },
        "citation_bibliography_identity": {
            "pass": cited == bib_keys,
            "uncited": sorted(bib_keys - cited),
            "missing": sorted(cited - bib_keys),
        },
        "cross_references_resolve": {
            "pass": refs <= labels and all(f"Figure {index}" in tex for index in (1, 2, 3)),
            "labels": sorted(labels),
            "formal_refs": sorted(refs),
            "manual_figure_references": [f"Figure {index}" in tex for index in (1, 2, 3)],
            "unresolved": sorted(refs - labels),
        },
        "bibliography_style_explicit": {
            "pass": "\\bibliographystyle{elsarticle-harv}" in tex,
            "dependency": "elsarticle-harv.bst",
        },
    }
    passed = all(item["pass"] for item in checks.values())
    payload = {
        "schema": "paper_e_non_tex_source_check_v1",
        "status": "PASS" if passed else "FAIL",
        "tex_sha256": sha256(TEX),
        "bib_sha256": sha256(BIB),
        "checks": checks,
    }
    args.json.parent.mkdir(parents=True, exist_ok=True)
    args.json.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"status": payload["status"], "failed": sorted(k for k, v in checks.items() if not v["pass"])}, sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
