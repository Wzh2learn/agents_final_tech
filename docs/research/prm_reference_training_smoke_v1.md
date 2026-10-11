# PRM800K Reference Training Smoke v1

> Status: `PIPELINE_CLOSED_REFERENCE_TRAINING_SMOKE_NOT_PAPER_RESULT` | Scope: one seed, two tiny matched arms, two optimizer steps; no scientific performance comparison and no formal Stage D training

## 1. Authorization and boundary

The overnight research authorization permits a small reference training smoke after the non-training C2/C4 dry-run confirmed real terminal/process disagreement. This run is explicitly:

```text
REFERENCE_TRAINING_SMOKE
NOT_PAPER_RESULT
NOT_FORMAL_STAGE_D_TRAINING
```

It does not lift `DATA_GO`, `MODEL_GO`, `TRAINING_GO`, licence, power, or multi-seed gates.

## 2. Environment root cause and repair

First attempt failed before training because Qwen3-4B's RoPE operation dispatched to Triton, and Triton's `backends/nvidia/driver.c` could not compile:

```text
fatal error: Python.h: No such file or directory
```

Evidence:

- `libcuda.so.1` and CUDA headers were present.
- system `python3-dev` was not installed;
- manual compilation reproduced the exact `Python.h` failure;
- Python 3.12 development headers were downloaded as Ubuntu packages and unpacked under:
  `/home/testuser/wzh/env_overlays/python312-dev-ubuntu017/root`;
- adding both `root/usr/include/python3.12` and `root/usr/include` to `CPATH` made the exact Triton C extension compile.

No sample, label, loss, step count, learning rate or evaluation rule was changed between the failed and successful attempts. The failed directory is preserved as:

`research/prm_reference_training_smoke_20261010_failed_triton_python_h/`

## 3. Frozen smoke configuration

| Item | Value |
|---|---|
| Source | PRM800K `phase2_test.jsonl`, SHA-256 `6b172efa...aaad` |
| C2 arm | official terminal-correct row in each matched problem group |
| C4 arm | complete, strictly all-positive selected human process-label row in the same problem group |
| Train groups | 8 distinct problem hashes |
| Held-out groups | 4 distinct problem hashes |
| Model | local Qwen3-4B |
| Method | LoRA SFT, `q_proj/v_proj`, r=8, alpha=16 |
| Seed | `20261013` |
| Optimizer steps | 2 per arm |
| Batch | 1 |
| Sequence cap | 256 tokens |
| External calls | 0 |
| Hyperparameter search | 0 |

The train and held-out problem groups are disjoint.

## 4. Chain result

| Chain stage | C2 | C4 |
|---|---|---|
| Dataset load | PASS | PASS |
| Selection | PASS | PASS |
| Training | PASS, 2 steps | PASS, 2 steps |
| Checkpoint | PASS | PASS |
| Held-out evaluation | PASS | PASS |
| Generation smoke | 2 rows | 2 rows |

| Arm | Train loss | Held-out LM loss | Runtime | Adapter |
|---|---:|---:|---:|---|
| C2 | 1.100282 | 1.399844 | 3.24 s | `C2/final_adapter` |
| C4 | 1.098687 | 1.401571 | 1.16 s | `C4/final_adapter` |

`VALUE`: these loss values only establish that finite loss was produced and evaluated. Eight training examples, four held-out examples, different selected solution texts, two steps and one seed cannot support C2/C4 superiority or non-inferiority.

## 5. What is now known

`ENGINEERING`:

- PRM data can be partitioned into terminal-process matched groups.
- C2 and C4 selections can be materialized into SFT examples.
- Qwen3-4B LoRA training, checkpoint saving and held-out evaluation run end to end on GB10 after the Python-header repair.
- The local smoke path can now be used to validate a future formal pilot proposal.

`NOT ESTABLISHED`:

- C4 improves student performance over C2.
- The tiny loss difference is meaningful.
- Dataset/model licences permit publication or large-scale training.
- The selected 8/4 groups are representative or adequately powered.
- The smoke validates semantic process supervision; C4 here uses human process labels from PRM800K.

## 6. Required before a formal pilot proposal

1. dataset licence decision;
2. predeclared train/dev/gate/sealed problem-group split;
3. native token-count matching, not whitespace/character proxies;
4. a powered sample-size plan and primary metric;
5. a fixed student model/optimizer/token/seed budget;
6. an independent evaluation set and safety/risk metrics;
7. a formal `MODEL_GO` and `TRAINING_GO` application.

`DECIDE NEXT LOOP: STOP_BRANCH` for training. Additional tiny runs would not answer a new scientific question; proceed to formal proposal only after the seven gates above.
