# BUILD_README - Paper E internal review bundle

> Purpose: compile the current Paper E review PDF with no local dependencies.
> All figure paths are bundle-local; there are no absolute paths. The
> `saner_rene_*` filenames are historical identifiers, not a current venue
> decision.

## Status
Compiled and verified on 2026-10-21 after the G1 statistical-unit revision.
Build method actually used: portable
tectonic 0.15.0 (user-space, single file). Command
`tectonic saner_rene_manuscript_v1.tex` produced
`saner_rene_manuscript_v1.pdf` (10 pages, 0 overfull boxes, 7 underfull-box
warnings). All 10 rendered pages were inspected for clipping and overlap.

This is an internal review bundle, not a venue-ready upload. If ICAART is
selected, convert to the live SCITEPRESS/ICAART template and rules. If IEEE
Access is selected, convert to the official IEEE Access Word or LaTeX
template and submit both source and matching PDF. The current IEEEtran source
must not be represented as either final venue format.

## Files
- `saner_rene_manuscript_v1.tex` - main file. IEEEtran conference format, double-anonymous (author block = "Anonymous Submission").
- `saner_rene_references.bib` - 21 cited and verified entries; consumed via `\bibliography{saner_rene_references}`.
- `fig1_measurement_chain.pdf` - vector re-render of the bound Figure 1 SVG (no Inkscape/svg package needed).
- `fig1_measurement_chain.png` - raster fallback for Figure 1.
- `fig2_family_visibility_matrix.png` - bound Figure 2 raster.
- `fig3_localization_ablation.png` - bound Figure 3 raster.
- `saner_rene_manuscript_v1.pdf` - the compiled review PDF (10 pages).

## How to compile on Overleaf
1. Upload every file in this directory to an Overleaf project (all at the project root).
2. Set the main file to `saner_rene_manuscript_v1.tex`.
3. Compiler: pdfLaTeX. Recompile from scratch once so the bibliography resolves.
4. `IEEEtran.cls` is provided by Overleaf; no extra style file is needed.

## Notes for the owner
- Figure 1 is included as `fig1_measurement_chain.pdf` via `\includegraphics`. The authoritative bound asset remains the SVG `docs/research/figures_saner/fig1_measurement_chain.svg`; the PDF here is a faithful vector re-render of that SVG.
- Figures 2 and 3 are the bound PNGs, hash-pinned in `docs/research/figures_saner/figure_source_binding_manifest.json`.
- Before submission: replace "Anonymous Submission" with the frozen author list (H1) and wire the Data Availability statement to a real anonymized repository link.
- Current build is 10 pages total and fits the preserved ICAART full-paper
  snapshot and the IEEE Access readability recommendation. Final page budgets
  must be rechecked against the selected live venue.
- The Acknowledgements section contains a proposed AI-use disclosure. Owner
  confirmation and venue-specific wording are still required before external
  submission.

## Rebuild from source
1. `python paper/_md2tex.py` (from the repo root) - regenerate the root .tex from `paper/saner_rene_manuscript_v1.md`.
2. `python paper/_to_bundle_tex.py` (from the repo root) - derive this bundle's self-contained .tex (bundle-local figure paths; fig1 as vector PDF).
3. `tectonic saner_rene_manuscript_v1.tex` (in this directory), or upload the bundle to Overleaf and compile with pdfLaTeX.

## Toolchain bootstrap (PDF build)
The PDF was built with a portable, user-space tectonic binary (no system TeX install):
- version: `tectonic 0.15.0`
- source: https://github.com/tectonic-typesetting/tectonic/releases/download/tectonic%400.15.0/tectonic-0.15.0-x86_64-pc-windows-msvc.zip
- local path used: `D:\AIRcommend\_tools\tectonic\tectonic.exe` (OUTSIDE the repository)
- sha256 (binary): 6760c6368d3219c687eb1811e55379af9526fbd97e97fa954968267f5241deb9
- sha256 (zip): 1d6bb76f049c8a3774f6e9d66e4b04e1a8c3dcb37527b6b41b7e894328e7bf29
- command: `tectonic saner_rene_manuscript_v1.tex` in this directory (runs bibtex internally; the first run downloads the TeX bundle).

On a fresh machine either download the same release and verify the hash above, or compile on Overleaf (`ieeetran` is provided there). A system TeX installation is NOT required and was deliberately avoided.
