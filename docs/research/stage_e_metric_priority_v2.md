# Stage E Metric Priority v2

> 状态: 活跃 | 更新: 2026-10-09 | 取代/被取代: 收敛 `stage_e_observability_metrics_v1.md` 的 headline hierarchy；不修改 frozen results

## 1. Reporting hierarchy

| Level | Metric | Formula | Current value | Claim boundary |
|---|---|---|---:|---|
| PRIMARY | Per-family visibility profile | `VR_f = v_f/n_f` | alias `43/47`; date `15/17`; mixed `20/20`; OCR `0/13`; prefix `13/16`; unit `5/5` | Shows family-dependent observability |
| PRIMARY | Micro visibility | `VR = 96/118` | `0.8136` | Absorption-based checkpoint visibility on this corpus |
| PRIMARY | Worst-family visibility | `min_f VR_f` | `0/13` | Identifies the worst observed family; not a population minimum |
| PRIMARY | Visibility-conditioned protocol use | `P(D=1|V=1)` | E2E `90/96`; flat `85/96`; hierarchical `13/96` | Measures use of evidence under each protocol definition |
| SECONDARY | Blindness rate | `BR=22/118` | `0.1864` | Complement of micro VR |
| SECONDARY | Macro-family visibility | `(1/6)Σ_f VR_f` | `0.7683` | Equal-family summary |
| DIAGNOSTIC | Detection without selected-checkpoint visibility | `P(D=1|V=0)` | E2E `22/22`; flat `0/22`; hierarchical `0/22` | Explains other detection signals; never a protocol ranking |
| DIAGNOSTIC | Visibility × detection cells | `VD,VU,BD,BU` | E2E `90,6,22,0`; flat `85,11,0,22`; hierarchical `13,83,0,22` | Construct stress test |
| DIAGNOSTIC | Threshold visibility | `v_f(γ)/n_f` | five-point curve | Operating-point sensitivity only |
| FUTURE | Semantic HBR | `P(V=0|H_c=1)` | `NOT IDENTIFIED` | Requires frozen canonical/reader contracts and labels |
| FUTURE | Localization metrics | top-1/top-k/stage distance | `NOT YET DEFINED` | Requires multi-leaf experiment |

`VALUE`: do not create more headline metrics. The four primary quantities answer where observability fails, how much is visible overall, which family is worst, and whether a protocol uses visible evidence.

## 2. Operational formulas

For injection `i`, `V_i=visible_frozen`; for protocol `p`, `D_i^p` is its frozen detection predicate.

```text
VR = sum_i V_i / 118
BR = 1 - VR
VR_f = sum_{i in f} V_i / n_f
MacroVR = (1/6) sum_f VR_f
WorstVR = min_f VR_f
P(D=1|V=1) = VD/(VD+VU)
P(D=1|V=0) = BD/(BD+BU)
```

`FACT`: unit is injection; table UID is the clustering unit. The main descriptive interval uses 2,000 table-cluster bootstrap replicates with seed `20260830`.

`VALUE`: the convenience float in `analysis_summary.json` is not the authoritative micro rate; retain the exact fraction `96/118`.

## 3. Claim discipline

Allowed: report raw numerator/denominator, family profile, micro/macro distinction, operating point and cluster-aware descriptive uncertainty.

Forbidden: rank E2E/flat/hierarchical from `P(D=1|V=0)`; infer semantic harm from visibility; call `[0,0]` a population CI; add threshold-AUC without a separately justified estimand.
