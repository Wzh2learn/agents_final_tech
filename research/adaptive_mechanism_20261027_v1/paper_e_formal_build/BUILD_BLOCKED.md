# Paper E Formal Build Blocked

Status: `BUILD_BLOCKED`

Date: 2026-10-27, Asia/Shanghai

## Search boundary

Only already-installed executables on `PATH` and conventional local installation roots were checked. No package installation, GitHub download, Windows-sandbox workaround, external build service, or fallback-PDF substitution was attempted.

## Observed tool errors

The required executables were absent:

```text
MISSING pdflatex
MISSING latex
MISSING lualatex
MISSING xelatex
MISSING tectonic
MISSING latexmk
MISSING bibtex
MISSING biber
MISSING tex
MISSING luaotfload
```

Running `bash build_paper_e.sh` fails before compilation with:

```text
BUILD_BLOCKED: required TeX tool not found: pdflatex
```

No formal PDF, TeX log, bibliography `.bbl`, engine version, or PDF page count exists for this attempt. The pre-existing 15-page fallback remains a non-TeX review artifact and is not reported as a formal build.

## Directly buildable bundle

- Canonical manuscript: `paper_e_sncs.tex`
- Bibliography source: `references.bib`
- Figures: `figures/fig1_measurement_chain.png`, `figures/fig2_family_visibility_matrix.png`, `figures/fig3_localization_ablation.png`
- Exact command: `bash build_paper_e.sh`
- Explicit bibliography-style dependency: `elsarticle-harv.bst`
- Non-TeX source check: `python3 check_sources.py --json SOURCE_CHECK_RECEIPT.json`

The build script retains complete `pdflatex` and BibTeX logs and refuses to substitute the fallback PDF as a formal compilation.
