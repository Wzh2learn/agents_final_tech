# Build Receipt

- Editable manuscript: `paper_e_sncs.tex`
- Bibliography: `references.bib`
- Figures and sources: `figures/`
- Compiled package PDF: `paper_e_sncs.pdf`
- Build command: `python3 compile_package_pdf.py` — exit status 0
- TeX attempt: `/tmp/tectonic/tectonic paper_e_sncs.tex` — exit status 126 (`Exec format error`; downloaded x86-64 binary on aarch64 host)
- The package PDF is a deterministic local reportlab rendering of the editable manuscript text because no compatible TeX engine is installed. The editable LaTeX remains the canonical source for owner TeX/Overleaf compilation.
