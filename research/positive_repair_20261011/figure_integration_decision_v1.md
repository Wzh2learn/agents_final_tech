# Manuscript Figure Integration Decision v1

> date: 2026-10-11 | Loop D (manuscript assembly) | authority: paper/saner_rene_manuscript_scope_lock_v1.md (Figure Definitions) + docs/research/stage_e_version_b_figure_spec_v1.md (FIGURE_SPEC_LOOP_C_REPAIRED) | NO scientific change

## Decision
The manuscript carries exactly three numbered figures, the SANER Version-B core set, per the frozen scope-lock figure definitions:
- Figure 1 - measurement chain (motivation).
- Figure 2 - defect family x checkpoint visibility (matrix).
- Figure 3 - multi-leaf localization and ablation.

## Edits applied to paper/saner_rene_manuscript_v1.md
- Figure 1 inserted in Section 1 (Introduction), immediately after the three-construct paragraph. Caption states the chain and that NIST motivates measurement effectiveness, not this paper's blind-spot framework (scope-lock caption boundary).
- Figure 2 replaces the previous visibility-spectrum embed in Section 5.1. Caption carries the scope-lock / figure-spec boundary: this is a visibility matrix, not a harmfulness matrix, with the OCR-like 0/13 across 11 clusters note.
- Figure 3 inserted in Section 5.5. Caption is the Loop C-repaired required caption, including the metric-specific identities (non-direct top-1 = chance 0.3333; non-direct macro-F1 = uniform-class baseline 0.3333, above the plotted majority baseline 0.1667) and the stage-aligned instrumentation, not emergent localization clause. All three forbidden phrases remain absent.
- Retired the previous two-checkpoint-trees embed (Section 3.1) to hold the 3-figure budget. Section 3.1 prose (the checkpoint-forest description) is UNCHANGED; only the picture was removed. Restore only if the owner elects a 4-figure paper.

## Hash binding (embed targets match the frozen manifest outputs)
- docs/research/figures_saner/fig1_measurement_chain.svg -> sha256 95fff20876ec9fc721866308cdfdcdce1fcff55668c3e38b4c9f0c67fb02d506
- docs/research/figures_saner/fig2_family_visibility_matrix.png -> sha256 f0281da58e456402b54783c5041de98044360244c9cfcd5f5a552c54185dff5d
- docs/research/figures_saner/fig3_localization_ablation.png -> sha256 1e3d9709451807f938ad91e25472892c23df045669efcdfe00a0899d10ae2c64
All three recompute exactly against research/positive_repair_20261011/track_a_figures_mirror/figure_source_binding_manifest.json.

## NIST reference (bundled into this pass)
- Section 1 now cites [NIST AI 100-1, 2023] and drops the internal process sentence that said the citation was deferred to the final reference pass.
- Reference added to the References list: National Institute of Standards and Technology, AI Risk Management Framework (AI RMF 1.0), NIST AI 100-1, January 2023, https://doi.org/10.6028/NIST.AI.100-1. Motivation-only per docs/research/nist_measurement_validity_ledger_v2.md; NIST does not certify the metrics.

## Open residual (Loop A materialization, non-blocking for text)
- Fig-3 in-figure status/identity labels are not rendered (residual F10/R8). The identities are carried in the caption text. A Loop A re-render of fig3_localization_ablation with per-bar status labels would change the output hash and therefore requires re-running verify_saner_figures.py and re-binding figure_source_binding_manifest.json. Deferred to the owner/Loop A; not a text blocker.