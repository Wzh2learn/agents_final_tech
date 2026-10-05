# Research story DOCX refresh and Office check（2026-10-05）

> Status: `PASS_INTERNAL_DERIVED_DOCX_REFRESH`
> Scope: `paper/research_story_v2.md` -> `paper/research_story_v2.docx`
> Boundary: internal research material only; patent/public-release gate remains closed

## 1. Why the derived DOCX changed

The Route V full-benchmark structural decision moved full Evaluate-Distill-Evolve validation to future work and retained the Stage E fallback. The authoritative Markdown was updated first, then the derived Word narrative was regenerated so the two representations remain synchronized.

## 2. Deterministic generation

Generator:

```text
research/build_teacher_review_docx.py
```

Command run on GB10:

```text
python research/build_teacher_review_docx.py \
  --source paper/research_story_v2.md \
  --output /tmp/research_story_det_a.docx
```

The source was paired with `paper/figures/fig_evaluate_distill_evolve_v1.svg`, which the generator renders as a native three-stage Word table. The generator now normalizes DOCX ZIP timestamps; two GB10 reruns were byte-identical with SHA-256 `5a506de6723a3364a06315c35581554406a4dce34e1efc90ec8a8ed498e8ef30`.

Hashes:

- Markdown: `48c8768970e9529e44a490abccd2e02492466be7b4adf0b948da65cde67ccb5a`
- DOCX: `5a506de6723a3364a06315c35581554406a4dce34e1efc90ec8a8ed498e8ef30`
- Rendered QA PDF: `34f713fe69ae810751581e75ec04cc83b3f601e21b49906b7d1816c384b1a9bd`

## 3. Quality checks

- `unzip -t`: all DOCX package members OK.
- DOCX XML contains the new Route V decision and the expected boundary terms.
- LibreOffice headless PDF conversion: `rc=0`.
- PDF page count: 4, unchanged from the prior accepted story rendering.
- PDF text extraction contains the complete Route V decision.
- Page 4 raster inspection: no overflow, overlap, missing characters, or clipped paragraphs.
- The mature Stage E teacher-review DOCX was not regenerated or modified.

## 4. Interpretation

This refresh updates only the internal three-stage narrative and its derived Word display. It does not alter Stage E paper results, claim tokens, experimental numbers, `DATA_NO_GO`, `RQ2 NOT_IDENTIFIED`, or the external-release prohibition.
