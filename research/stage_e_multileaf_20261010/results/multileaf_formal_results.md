# Stage E Multi-Leaf Formal Results v1

> Status: `POSITIVE` | Generated: 2026-10-10T01:02:44+08:00 | Pre-result freeze verified before output creation

## 1-2. Contracts and retained units

| Stage | Contract | Clusters | Injections |
|---|---|---:|---:|
| M | PASS | 24 | 72 |
| R | PASS | 24 | 72 |
| N | PASS | 24 | 72 |

Leakage audit: `PASS`.

## 3. Per-stage visibility profiles

| Stage | Direct leaf | Direct visibility | Any response | Responsive leaves |
|---|---|---:|---:|---:|
| M | parse.field.hit_rate | 1.0000 | 1.0000 | 2 |
| R | qa.retrieval.source_required | 1.0000 | 1.0000 | 1 |
| N | parse.reconcile.equations | 1.0000 | 1.0000 | 1 |

## 4-5. Responsive leaves and signatures

Global responsive leaves: `['parse.field.hit_rate', 'parse.reconcile.equations', 'parse.table.regression', 'qa.retrieval.source_required']`.

- M: [0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0] x72
- R: [0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0] x72
- N: [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0] x72

## 6-10. Primary localization results

- LOCO macro-F1: `1.000000`
- Top-1 accuracy: `1.000000`
- Majority baseline: top-1 `0.333333`, macro-F1 `0.166667`
- Permutation p-value: macro-F1 `9.999e-05`, top-1 `9.999e-05`
- Cluster bootstrap 95% CI: macro-F1 `[1.0, 1.0]`, top-1 `[1.0, 1.0]`

## 11. Confusion matrix

| True / Pred | M | R | N | __TIE__ |
|---|---|---|---|---|
| M | 72 | 0 | 0 | 0 |
| R | 0 | 72 | 0 | 0 |
| N | 0 | 0 | 72 | 0 |

Ties are serialized as `__TIE__` and always scored incorrect.

## 12. Leakage audit

{"expected_stage_matches": true, "m_n_uid_disjoint": true, "one_stage_per_cluster": true, "sample_ids_unique": true, "three_repeated_injections_per_cluster": true}

## 13-14. Flat/hierarchy secondary structure

- Flat/hierarchical Pearson correlation: `0.931305`
- Spearman ranking correlation: `0.866025`
- Linear affine fit: `h = 1.409091 f + -0.075758`, R2 `0.867329`, max residual `0.265152`
- Flat score support: `[0.833333, 1.666667]`
- Hierarchical score support: `[0.833333, 1.363636, 2.272727]`
- AUROC flat/hierarchical: `1.000000` / `1.000000`
- Clean-only matched operating point: `NOT_IDENTIFIABLE_CLEAN_SUPPORT_ZERO`
- Single-leaf affine degeneracy broken: `True`

## 15-16. Claim boundary

Allowed: `Checkpoint evidence contains stage-localizing information under the frozen M/R/N controlled injections.`

Forbidden: `The hierarchy localizes failures.`

MULTILEAF_RESULT_STATUS: POSITIVE
