# Stage E 118-Injection Quantification v1

Status: recomputed from frozen JSON only. No frozen value is replaced or reinterpreted.

## 1. Input integrity and anchors

| Input | SHA256 |
|---|---|
| `logs/graph/eval/t2_visibility_sensitivity.json` | `eff82b0b7abbb8edcb8aef24a921806a760624fc84b57b3c2e54331394f99ea5` |
| `logs/graph/eval/t1_eval_baseline_comparison.json` | `6993512c7e7fa9e6b4a90a6602d5107d62e55c1fcba066c3d43a18f444b63c87` |
| `logs/graph/eval/d1_mutant_validity_audit.json` | `ef1d46ed9ca1ae3832f35d2796b3a51be34c912897d68b40d73c9413d8651a2b` |
| `logs/graph/eval/d3_matched_fpr_stage_a.json` | `3318ac178a0c3317ce18d69663b942e289c2668f4b604082606a549172f2ab10` |

`FACT`: deterministic checks reproduce `95` tables, `118` injections, `96/118` visible, `0/13` OCR-like visible, `112/118`, `85/118`, `13/118`, matched-FPR `90` versus `90`, difference CI `[0,0]`, and harmful denominator `111`.

## 2. Overall visibility

| Statistic | Count | Rate |
|---|---:|---:|
| Visible | 96/118 | 81.36% |
| Blind | 22/118 | 18.64% |
| Macro family visibility | — | 76.83% |
| Table-cluster bootstrap 95% interval for micro visibility | — | `[72.88%, 88.50%]` |

`FACT`: the macro rate is the unweighted mean of six family rates and is not a second estimate of the same micro quantity.

## 3. Family profile

| Family | Visible/Total | Visibility | Blind |
|---|---:|---:|---:|
| alias variant | 43/47 | 91.49% | 4 |
| date variant | 15/17 | 88.24% | 2 |
| mixed language | 20/20 | 100.00% | 0 |
| OCR-like | 0/13 | 0.00% | 13 |
| prefix noise | 13/16 | 81.25% | 3 |
| unit suffix | 5/5 | 100.00% | 0 |

`FACT`: OCR-like is a predefined negative-observability control: every case is blind under the frozen absorption rule and every gamma in the grid.

### OCR-like grouped uncertainty

`FACT`: OCR-like is `0/13` across 11 table-UID clusters. The table-cluster bootstrap is degenerate at `[0,0]` because every resampled cluster has zero visible OCR cases; that interval describes this frozen construction and is not a population upper bound.

`FACT`: as a sensitivity reference only, the exact binomial 95% interval is `[0,24.71%]` if the 13 injections were independent. They are not guaranteed independent.

`VALUE`: the conservative grouped report is `0/13 visible; 0/11 table clusters contain a visible OCR case; exact cluster-event 95% sensitivity interval [0,28.49%]`. State that transfer to a new corpus or lineage is `UNVERIFIED`.

## 4. Visibility × frozen-threshold detection

Cells are `visible_detected`, `visible_undetected`, `blind_detected`, and `blind_undetected`.

| Protocol | VD | VU | BD | BU | `P(D|V)` | `P(D|B)` | `P(V|D)` | Blindness among misses |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| End-to-end | 90 | 6 | 22 | 0 | 93.75% | 100.00% | 80.36% | 0.00% |
| Flat | 85 | 11 | 0 | 22 | 88.54% | 0.00% | 100.00% | 66.67% |
| Hierarchical expert | 13 | 83 | 0 | 22 | 13.54% | 0.00% | 100.00% | 20.95% |

`FACT`: the end-to-end predicate detects all 22 checkpoint-blind cases because it observes final mapping-text change, not the same checkpoint signal. `INFERENCE`: this is construct divergence, not evidence that end-to-end detection repairs checkpoint blindness.

Table-cluster bootstrap intervals:

- `P(D|V)`: end-to-end `[86.27%,100%]`, flat `[80.00%,96.10%]`, hierarchical `[6.93%,21.11%]`.
- `P(D|B)`: end-to-end `[100%,100%]`, flat `[0%,0%]`, hierarchical `[0%,0%]`.
- `P(V|D)`: end-to-end `[71.30%,87.88%]`, flat/hierarchical `[100%,100%]`.
- blindness among misses: end-to-end `[0%,0%]`, flat `[50.00%,86.21%]`, hierarchical `[12.96%,30.21%]`.

## 5. Matched-FPR stress test

`FACT`: at `alpha=0.05`, clean-calibrated thresholds are `theta_flat_drop10=1.428571` and `theta_layered_root_drop=0.535714`.

| Axis | Flat | Hierarchical | Difference |
|---|---:|---:|---:|
| Matched-FPR detections on `H∪HI=111` | 90 | 90 | `[0,0]` CI |
| Frozen-threshold context | 85 | 13 | threshold-placement difference |

`FACT`: 2,000 paired table-cluster bootstrap replicates use seed `20260830` and 88 clusters; no replicate has a nonzero matched-FPR difference.

`INFERENCE`: raw `85` versus `13` reflects operating-point placement on an affinely related single-responsive-leaf score; it does not establish general hierarchical inferiority.

`VALUE`: the matched-FPR null is the defensible protocol conclusion for this corpus; the raw gap is retained as a sensitivity result rather than a superiority claim.

## 6. Operational harmfulness cells

| Operational class | Visible | Blind | Total |
|---|---:|---:|---:|
| `H` | 85 | 0 | 85 |
| `HI` | 11 | 15 | 26 |
| `E` | 0 | 7 | 7 |

`FACT`: these are descriptive operational-label cells, not independent semantic labels. Classification uses detection/equivalence paths in part.

`UNVERIFIED`: semantic harmfulness-conditional blindness is not identifiable. The semantic-boundary analysis uses one judge on 28 cases and has no calls for mixed-language or unit-suffix families.

## 7. Reproduction

`FACT`: source data, formulas, seed, input hashes, and output hashes are in [`source_data_receipt.json`](../../research/stage_e_stage_d_20261009/source_data_receipt.json).
