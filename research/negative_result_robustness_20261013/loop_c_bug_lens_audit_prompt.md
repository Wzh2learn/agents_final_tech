# Loop C bug-lens audit (read-only) - Paper E negative results: bug or synthetic-data artifacts?

You are **Loop C**: independent, read-only. No edits, commits, pushes, or services. Verify from the artifacts themselves; do not trust summaries. If `python3` is denied by your gate, replicate statically with `grep`/`jq`/`sha256sum`/`cat` and say so.

Repo root: `wzh/projects/agents_final_tech`

## Context
The owner asked whether the three headline negative/boundary findings of Paper E could be artifacts of implementation bugs or synthetic-data problems. Loop D ran an independent recomputation (`research/negative_result_robustness_20261013/recompute_receipt.json`) that reproduces the frozen numbers, and a byte-identical re-run of the matched-FPR reanalysis script from frozen inputs. Your job: adversarially test the bug / synthetic-artifact hypotheses and the recomputation.

## Artifacts to audit
- `research/negative_result_robustness_20261013/recompute_receipt.json` + `recompute_negative_results.py`
- Frozen evidence: `logs/graph/eval/t2_visibility_sensitivity.json`, `checkpoint_discrimination_tables_v2.json`, `d2_cross_matcher_det.json`, `d3_matched_fpr_stage_a.json`; `research/stage_e_method_revision_20261009/matched_fpr_reanalysis.json`; `research/stage_e_multileaf_20261010/results/{multileaf_formal_results.json, multileaf_signature_ablation.json, multileaf_prediction_rows.jsonl, multileaf_run_receipt.json}`; `research/stage_e_multileaf_20261010/multileaf_preresult_freeze_manifest.json`
- Claim boundaries: `paper/saner_rene_manuscript_scope_lock_v1.md`, `docs/research/SANER_SCIENTIFIC_ADJUDICATION_v1.md` (A1-A7)

## Checks (test each bug hypothesis explicitly)
1. **OCR-like 0/13**: (a) no-op injections? (all 13 differ; token-level morphology: exactly one token, injected token lowercase, case-folded token Lev=1); (b) dead instrumentation? (other families register: 96/118 total; leaf responses exist); (c) masking mechanism vs bug: canonical mapping keys identical for 12/13 OCR cases, judge 13/13 equivalent (frozen autopsy evidence); is the manuscript claim scoped to "unobserved on the frozen scored surface" as written?
2. **Matched-FPR structural equivalence**: (a) construction artifact? (slope ~0.375 follows from the single-responsive-leaf construction; is the claim so scoped?); (b) byte-identical re-run of the reanalysis script from frozen inputs - state that evidence; (c) clean support {0} by construction - does the manuscript avoid a blanket non-identifiability claim (A2)?
3. **Multi-leaf**: (a) label leakage? (leakage_audit PASS fields; features = response vector only; spot-check prediction rows vs classifier code); (b) freeze-before-results ordering (manifest temporal_order; result_artifacts_absent_at_freeze); (c) recomputed LOCO numbers match stored (full/direct 1.0; non-direct 0.3333, tie 0.6667; any-response 0.0, tie 1.0); (d) "explicit instrumentation, not hierarchy" consistent with direct codebook = full?
4. **Synthetic-data framing**: corpus/injections are synthetic by design (stated); check no claim in the claim matrix C1-C3 or the abstract exceeds the synthetic scope.
5. Any suspected defect, inconsistency, or over/under-claim: report precisely (file:line), or state "none".

## Output
Per area: verdict ROBUST / CONDITIONAL / SUSPECT + evidence. Then exactly:
`LOOP_C_NEGRESULT_RECHECK_VERDICT = PASS | CONDITIONAL | FAIL`
`LOOP_C_NEGRESULT_BUG_LENS_VERDICT = PASS | CONDITIONAL | FAIL`
`LOOP_C_NEGRESULT_SYNTHETIC_SCOPE_VERDICT = PASS | CONDITIONAL | FAIL`
and one closing line naming the weakest remaining point.
