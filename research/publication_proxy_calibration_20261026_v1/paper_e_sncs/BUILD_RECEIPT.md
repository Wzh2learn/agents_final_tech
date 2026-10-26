# Build Receipt

- Canonical source: `paper_e_sncs.tex`
- Bibliography source: `references.bib`
- TeX engine result: no compatible aarch64 TeX engine is installed locally.
- Delivered PDF engine: PyMuPDF `1.27.2.3` Story full-content fallback; this is **not** a TeX-engine compilation.
- Determinism controls: fixed A4 geometry, fixed metadata timestamps, empty PDF trailer ID, garbage/deflate/clean save, local figures and local bibliography.
- PDF: `paper_e_sncs.pdf`; pages `15`; extracted text `6879` whitespace-delimited tokens and `51326` bytes.
- Canonical source scope: 150-250 word structured abstract, complete Introduction through Declarations, exactly two counted cases, and 24 bibliography entries.
- Structured abstract count: 195 words; citation census: `24` cited and `24` bibliography entries, with no orphan or missing keys.
- PDF SHA256: `f042958061bc1118e76f58b6a3504f5125f4161b82ebca28decc7548f3bf048c`
- TeX SHA256: `f1993042d344d97e7a47fe6cda1065ca3bfc42d7720565c492c8c6dfef173734`
- BibTeX SHA256: `f606916544375f0ce3be8ca602476b2f69a5aef3e633e443716a3face007df06`
- Fallback HTML SHA256: `2e6a0e00cedf0f5fc49b01b642808da276713dfa88d1e2073d9a3b762e785d53`
- Figure source count: `3`; measurement-chain use count: 1; visibility-figure use count: 1.
- D approved-tool command: `pdflatex paper_e_sncs.tex && bibtex paper_e_sncs && pdflatex paper_e_sncs.tex && pdflatex paper_e_sncs.tex`
- Local fallback command: `python3 compile_package_pdf.py`
