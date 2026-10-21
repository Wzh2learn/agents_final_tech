# G1 Injection-Seed Statistical Audit

Date: 2026-10-21, Asia/Shanghai

Status: `POST_HOC_REANALYSIS_COMPLETE`

Evidence identity: `POST_HOC_DETERMINISTIC_REANALYSIS_NOT_NEW_MODEL_EXPERIMENT`

## Question

The manuscript reports three injection-seed runs and pools them as
`219/282 = 0.7766`, with a percentile bootstrap interval
`[0.7270, 0.8227]` over 282 table-run units. The question is whether that
interval is aligned with the intended independent analysis unit.

## Estimands

1. **Table-run estimand:** the detection probability for a randomly selected
   injected `(source table UID, seed)` run under these three fixed seeds.
2. **Source-table estimand:** the expected detection rate for a source table,
   weighting each unique source-table UID equally and averaging the seeds in
   which that UID is injected.
3. **Seed-generalization estimand:** not reliably estimated here because only
   three injection seeds exist. Seed rates and leave-one-seed-out values are
   reported instead of a population-level seed interval.

## Reanalysis

The zero-network script `g1_recompute_seeds.py` reruns the unchanged injector
and `paper_t1_eval_baselines.run_arm_b` path on GB10. It preserves the seed-42
byte-identity gate and emits one row per source-table UID and seed.

- Seeds: `42`, `20260831`, `20260832`
- Injection ratio: `0.3`
- Table-run rows: `282`
- Detected flat table-runs: `219`
- Unique source-table UIDs: `119`
- UID overlap: 29 UIDs in one seed, 17 in two seeds, 73 in all three seeds
- Seed-42 injected-table, injection-map and determinism hashes match the frozen
  artifact byte-for-byte.

## Results

| Estimand | Flat detection | 95% uncertainty |
|---|---:|---:|
| Table-run point estimate | `219/282 = 0.7766` | historical naive bootstrap `[0.7270, 0.8227]` |
| UID-cluster bootstrap over table-run ratio | `0.7766` | `[0.7117, 0.8364]` |
| UID-equal source-table estimate | `0.7535` | `[0.6835, 0.8207]` |

Per-seed flat rates are `0.7895`, `0.7835`, and `0.7556`; their range is
`0.0339`. Leave-one-seed-out table-run rates are:

- omit seed 42: `144/187 = 0.7701`
- omit seed 20260831: `143/185 = 0.7730`
- omit seed 20260832: `151/192 = 0.7865`

## Ruling For Paper E

Keep `219/282 = 0.7766` as the descriptive **table-run** estimate. Replace the
current pooled interval in the main text with the source-table UID-cluster
interval `[0.7117, 0.8364]`, and retain the UID-equal sensitivity
`0.7535 [0.6835, 0.8207]` as a secondary analysis. The historical
`[0.7270, 0.8227]` may remain in a dated audit note as a naive table-run
interval, but it should not be presented as source-table uncertainty.

Suggested manuscript wording:

> Across three injection seeds, flat table-detection rates are 75/95 = 0.7895,
> 76/97 = 0.7835, and 68/90 = 0.7556. The denominator-weighted table-run
> estimate is 219/282 = 0.7766. Because these runs map to 119 unique source
> table UIDs, 73 of which occur in all three seeds, a source-table UID-cluster
> bootstrap gives a 95% interval of [0.7117, 0.8364]. Equal-weighting source
> table UIDs gives 0.7535 with interval [0.6835, 0.8207]. With only three
> injection seeds, we report the observed seed range and leave-one-seed-out
> sensitivity rather than a population-level seed interval.

## Interpretation Boundary

This is a post-hoc reanalysis of frozen deterministic artifacts. It does not
change any raw injection, checkpoint, judge or score result. It also does not
make the three seeds an independent random sample of future injection
distributions.
