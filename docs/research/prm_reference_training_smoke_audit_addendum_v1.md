# PRM Reference Training Smoke Audit Addendum v1

> Status: `PIPELINE_CLOSED_WITH_LOOP_C_CONDITIONS` | Fresh-audit verdict: `CONDITIONAL` | No retraining and no change to original smoke metrics

## 1. Independent audit outcome

The fresh-context Loop C audit accepted the non-paper/non-formal boundary, disjoint train/eval problem groups, parameter consistency, absence of hidden epochs/hyperparameter search and chain closure. It conditionally required receipt and disclosure corrections.

Raw audit: [`../experiments/2026-10-10_loop_c_prm_smoke_audit.md`](../experiments/2026-10-10_loop_c_prm_smoke_audit.md).

## 2. Material arm-overlap disclosure

The two smoke arms are not disjoint treatments:

| Item | Shared / total |
|---|---:|
| train rows | 7 / 8 |
| held-out rows | 2 / 4 |
| generation-smoke outputs | byte-identical across arms |

The two optimizer steps consumed only 2 of the 8 training rows per arm (`epoch=0.25`, batch size 1). The first step is bit-identical across arms; only the second step sees a differing row.

Consequently, the train-loss difference is:

```text
(1.468546986579895 - 1.4653573036193848) / 2
= 0.0015948414802551
```

This is exactly half of one step's loss difference on one differing example. It is not an effect size.

The held-out loss difference has the opposite sign: C4 is higher than C2 by `0.0017263889312744`. This is also not an effect size because two held-out rows are shared and `completion_only_loss=False` includes identical prompt tokens.

## 3. Field-semantics correction

`smoke_config.json` field `selection.matched_pairs_available=12` means the number of matched pairs selected for the 8-train/4-eval smoke, not the 407 matched pairs in the full non-training dry-run.

Future scripts must use `matched_pairs_selected_for_smoke`. The original config is preserved unchanged as the historical run receipt.

## 4. Environment and code receipt

| Item | Value |
|---|---|
| Python | 3.12.3 |
| Torch | 2.13.0+cu130 |
| Transformers | 5.14.1 |
| TRL | 1.14.1 |
| PEFT | 0.21.2 |
| Accelerate | 1.14.0 |
| Device | NVIDIA GB10 |
| Runner SHA-256 | `900f17df4bff7d28f95ef0bdb4fc5dbae699006226dfc49bbf9f50a44c2691c7` |
| Config SHA-256 | `7db152e87209126c9dc681ce6dd8cfb9246b6b64ead8d28c93d021566a9165b5` |
| Metrics SHA-256 | `0d234d0d6d94ec0ac2dd4fddaba21339fd6b46ada620f6a4461f249214efcbb6` |

The failed-run directory preserves the byte-identical config and an empty `C2/`, proving death occurred before any checkpoint output. The original traceback was not written to disk. The root cause remains supported by the manual `Python.h` compile reproduction, but the exact failed traceback is `NOT PRESERVED`.

## 5. Chain-field evidence caveat

The original `smoke_metrics.json` writes `dataset=PASS` and `selection=PASS` as literals. Independent audit recomputed those facts from config hashes and disjoint row/problem IDs; `checkpoint=PASS` is additionally based on directory presence plus adapter/trainer files. Future validators must derive chain fields from checks rather than write constants.

## 6. Final interpretation

`ENGINEERING`: the dataset -> selection -> LoRA training -> checkpoint -> held-out evaluation chain is operational on GB10 after the local Python-header repair.

`NOT ESTABLISHED`: C2/C4 performance difference, effect size, pilot power, representative sampling, or paper evidence.

`DECISION`: retain `REFERENCE_TRAINING_SMOKE / NOT_PAPER_RESULT`; no further tiny training run is scientifically useful.
