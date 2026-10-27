#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

for tool in pdflatex bibtex; do
  if ! command -v "$tool" >/dev/null 2>&1; then
    echo "BUILD_BLOCKED: required TeX tool not found: $tool" >&2
    exit 127
  fi
done

if kpsewhich elsarticle-harv.bst >/dev/null 2>&1; then
  style_file="$(kpsewhich elsarticle-harv.bst)"
else
  echo "BUILD_BLOCKED: explicit bibliography-style dependency missing: elsarticle-harv.bst" >&2
  exit 2
fi

echo "TeX engine: $(command -v pdflatex)"
pdflatex -interaction=nonstopmode -halt-on-error paper_e_sncs.tex
bibtex paper_e_sncs
pdflatex -interaction=nonstopmode -halt-on-error paper_e_sncs.tex
pdflatex -interaction=nonstopmode -halt-on-error paper_e_sncs.tex

echo "Bibliography style: ${style_file}"
echo "Formal PDF: $(pwd)/paper_e_sncs.pdf"
