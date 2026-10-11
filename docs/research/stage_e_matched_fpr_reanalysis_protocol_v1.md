# Stage E Clean-Only Matched-FPR Reanalysis Protocol v1

> 状态: 活跃 | 更新: 2026-10-09 | 取代/被取代: 不覆盖 D3；建立独立 clean-only namespace

## 1. Claims

- **CLAIM A, structural**: under the current single-responsive-leaf construction, hierarchical score is a positive affine transform of flat score. Ranking and ROC equivalence follow.
- **CLAIM B, empirical**: a clean-only calibrated matched-FPR TPR difference. This requires a positive threshold identifiable from clean scores alone.

## 2. Contract

1. Cluster = table UID.
2. Deterministic fold = sorted table UID index modulo five.
3. Calibration fold uses clean-table scores only.
4. Evaluation fold contains held-out injected/harmful rows.
5. H/HI outcomes and evaluation TPR are prohibited from threshold selection.
6. The same target-FPR rule is used for flat and hierarchical.
7. Every bootstrap or cross-fit replicate redoes calibration.
8. Report ranking equivalence, ROC equivalence and matched-FPR TPR difference separately.
9. Namespace is `stage_e_matched_fpr_reanalysis_v1`.

## 3. Identification rule

For each fold, select the smallest positive threshold maximizing TPR subject to `FPR<=alpha` using calibration scores only. If calibration has no positive support, the target-FPR threshold is `UNIDENTIFIED`; do not choose a threshold by held-out TPR.

## 4. Required outputs

- clean score support and positive counts;
- per-fold calibration/evaluation counts;
- threshold-identification status;
- affine slope/rank/ROC checks;
- fixed positive-threshold sensitivity grid, explicitly not matched-FPR calibration;
- exact blocker if threshold identification fails.
