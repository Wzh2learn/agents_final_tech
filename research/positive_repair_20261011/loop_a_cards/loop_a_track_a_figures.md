# Loop A Assignment — Track A: SANER Figure 1/2/3 Source Binding

ROLE: Loop A / GB10 execution. Track A (SANER manuscript consolidation). This task binds the three SANER figures to frozen source artifacts and materializes renderable files. It does NOT touch the manuscript body.

Read first (binding):
- paper/saner_rene_manuscript_scope_lock_v1.md  (figure definitions; allowed/forbidden caption language)
- research/stage_e_multileaf_20261010/loop_d_inputs/stage_e_version_b_figure_spec_v1.md  (spec v1, all three figures)
- paper/figure_plan_v1.md (existing figure ledger; do not modify)
- docs/research/figures_multileaf/ (Fig-3 candidate assets + manifest)
- logs/graph/eval/t2_visibility_sensitivity.json and logs/graph/eval/checkpoint_discrimination_tables_v2.json (Fig-2 frozen sources)
Project dir: /home/testuser/wzh/projects/agents_final_tech
Work dir (create if absent; do not touch other folders): docs/research/figures_saner/

DELIVERABLES (deterministic; zero model calls):
1) fig1_measurement_chain.svg — the five-node measurement chain exactly per spec (NIST motivation -> staged failure -> checkpoint visibility -> protocol detection -> outcome/harm); no decorative illustration; each node names a measurement construct; distinguish visibility/detection/harm by shape or border, not unsupported color semantics.
2) fig2_family_visibility_matrix.svg + .png — rows: the six defect families; columns: gamma 0.2,0.3,0.5,0.7,0.9; cell = visibility rate at that threshold; annotate injection counts; add the separate textual note "0/13 OCR-like injections were visible across 11 table clusters". EVERY cell number must be verified against the frozen JSON (record the field paths used); dump fig2_source.csv for traceability. Caption boundary: visibility matrix, NOT harmfulness matrix.
3) fig3_localization_ablation.svg + .png — bind the existing candidate (figures_multileaf/fig_multileaf_localization_ablation.*) and verify its numbers against multileaf_signature_ablation.json (full 1.0000 / direct 1.0000 / non-direct 0.3333; baselines majority 0.1667 / chance 0.3333). Required caption text exactly per spec; forbidden caption language enforced.
4) figure_source_binding_manifest.json — for each figure: source artifact paths + sha256, exact JSON field paths of every number, renderer script hashes, output hashes, and the caption texts.
5) receipt.json — inputs(+hashes), outputs(+hashes), start/end UTC, model_calls=0, verification notes, unverified items, deviations.

FORBIDDEN: inventing numbers; editing frozen artifacts or the manuscript; model/judge calls; commit/push; touching other figure folders.
STOP: required source missing or unverifiable -> FIGURE_DATA_MISSING; hash mismatch -> HASH_MISMATCH; else complete.
END: final message = status + manifest path + one-line summary.