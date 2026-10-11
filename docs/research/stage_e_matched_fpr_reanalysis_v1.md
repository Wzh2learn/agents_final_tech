# Stage E Clean-Only Matched-FPR Reanalysis v1

> 状态: `BLOCKER_CLEAN_THRESHOLD_NOT_IDENTIFIABLE` | 更新: 2026-10-09 | 取代/被取代: 不修改旧 D3

## 1. Executed analysis

`FACT`: a derived-only script loaded the frozen D3/D1 inputs, recomputed clean scores and harmful score pairs, assigned five deterministic table-UID folds, and tested whether positive thresholds were identifiable from clean scores alone.

Evidence: [`matched_fpr_reanalysis.json`](../../research/stage_e_method_revision_20261009/matched_fpr_reanalysis.json).

## 2. Clean-only blocker

`FACT`: 2,382 usable clean rows have flat and layered contrastive support exactly `{0}`. Positive clean counts are `0` and `0` in every fold.

`INFERENCE`: any positive threshold yields observed clean FPR 0, but the clean data cannot select a unique threshold without maximizing harmful TPR. That would violate the clean-only contract.

`VALUE`: empirical clean-only matched-FPR TPR is therefore `NOT_IDENTIFIABLE`, not `90/111 versus 90/111`.

`FACT`: the current contrastive score is constructed from two identical hit-rate observations (`h_repeat = h`), so every unmodified clean row is zero by construction. No unmodified clean panel can provide positive support for this exact score definition.

`VALUE`: the real remedy is a revised score definition with nonzero clean support or a separately preregistered pseudo-injection/null-mutation panel. Do not relabel the current zero-support panel as a failed sample-size problem.

## 3. Structural result

`FACT`: 90 positive harmful score pairs have layered/flat slopes `0.3749999125` to `0.3750000375`, maximum deviation `8.75e-08`, and Spearman rank correlation `1.0`.

`INFERENCE`: CLAIM A remains supported. Flat and hierarchical rankings and ROC curves are equivalent in the current single-leaf construction.

## 4. Sensitivity result

Across a fixed affine threshold grid independent of harmful outcomes, flat and layered detected counts are identical in every fold and every grid point; difference is always zero.

`VALUE`: this is structural sensitivity evidence, not clean-only empirical matched-FPR evidence.

## 5. Old D3 disposition

- `CLAIM A`: retain as structural diagnosis.
- `CLAIM B`: downgrade to `SUPPORTING_SENSITIVITY_ONLY`.
- Old `90/111` and `θ*`: retain as historical/sensitivity evidence; do not call cleanly calibrated confirmatory results.
- Required missing evidence: a clean panel with nonzero contrastive score support under the same score definition.
