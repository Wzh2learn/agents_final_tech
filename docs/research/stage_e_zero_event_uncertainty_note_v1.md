# Stage E Zero-Event Uncertainty Note v1

> 状态: 活跃 | 更新: 2026-10-09 | 取代/被取代: 规范 OCR `0/13` 的 estimand 与区间表述

## 1. Final wording

> `0/13 OCR-like injections were visible across 11 table clusters.`

## 2. Two estimands

1. **Injection-level descriptive visibility**: `0/13`. Under an independent-injection reference assumption, the two-sided 95% Clopper-Pearson interval is `[0,24.71%]`, with upper bound `1-0.025^(1/13)`.
2. **Table-cluster event rate**: `0/11 tables contained any visible OCR case`. The two-sided 95% exact binomial interval for this cluster-event estimand is `[0,28.49%]`, with upper bound `1-0.025^(1/11)`.

`FACT`: the latter is not a clustered confidence interval for the injection-level rate. It is a separate table-level estimand and a conservative sensitivity bound.

## 3. Cluster bootstrap

`FACT`: a table-cluster bootstrap resampling the 11 OCR-bearing table clusters always returns zero visible events, hence `[0,0]`.

`VALUE`: `[0,0]` is a degenerate empirical bootstrap result and must not be presented as inferential population uncertainty.

## 4. Beta-binomial restriction

`VALUE`: do not use a beta-binomial interval for these all-zero data unless a defensible prior and identifiable overdispersion parameter are supplied independently. Current data do not identify both parameters.

## 5. Recommended main-text report

Report raw `0/13`, the 11-cluster count, and the two estimands separately. For uncertainty, lead with the table-cluster event sensitivity interval `[0,28.49%]`, retain `[0,24.71%]` only as an independence-reference interval, and state transfer is `UNVERIFIED`.
