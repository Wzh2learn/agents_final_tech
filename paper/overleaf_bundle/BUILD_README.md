# BUILD_README - SANER 2027 RENE self-contained Overleaf bundle

> Purpose: compile the submission PDF on Overleaf with no local dependencies. All figure paths are bundle-local; there are no absolute paths.

## Files
- `saner_rene_manuscript_v1.tex` - main file. IEEEtran conference format, double-anonymous (author block = "Anonymous Submission").
- `saner_rene_references.bib` - 21 verified entries; consumed via `\bibliography{saner_rene_references}`.
- `fig1_measurement_chain.pdf` - vector re-render of the bound Figure 1 SVG (no Inkscape/svg package needed).
- `fig1_measurement_chain.png` - raster fallback for Figure 1.
- `fig2_family_visibility_matrix.png` - bound Figure 2 raster.
- `fig3_localization_ablation.png` - bound Figure 3 raster.

## How to compile
1. Upload every file in this directory to an Overleaf project (all at the project root).
2. Set the main file to `saner_rene_manuscript_v1.tex`.
3. Compiler: pdfLaTeX. Run once, then run BibTeX (or use the "Recompile from scratch" button) so the bibliography resolves.
4. `IEEEtran.cls` is provided by Overleaf; no extra style file is needed.

## Notes for the owner
- Figure 1 is included as `fig1_measurement_chain.pdf` via `\includegraphics`. The authoritative bound asset remains the SVG `docs/research/figures_saner/fig1_measurement_chain.svg`; the PDF here is a faithful vector re-render (rects/text/lines/polygons) of that SVG.
- Figures 2 and 3 are the bound PNGs, hash-pinned in the repository manifest `docs/research/figures_saner/figure_source_binding_manifest.json`.
- Before submission: replace "Anonymous Submission" with the frozen author list (H1) and wire the Data Availability statement to a real anonymized repository link.
- Target page budget (RENE): at most 10 pages including figures and appendices, plus up to 2 references-only pages.
- This bundle was NOT compiled locally (no TeX engine in the build environment); the first compile should be checked for overfull boxes and float placement.