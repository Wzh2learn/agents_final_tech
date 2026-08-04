# 2026-07-10 Tabular Foundation Model Smoke Test

## Environment

```text
conda environment: wzh_tabular
Python: 3.11.15
PyTorch: 2.13.0+cu130
CUDA: 13.0
GPU: NVIDIA GB10, capability 12.1
TabPFN: 8.0.8
TabFM: 1.0.1 (editable official repository checkout)
```

TabFM source is checked out at `~/wzh/research/tabfm`. Classification and
regression checkpoints are stored under
`~/wzh/models/hf/tabfm-1.0.0-pytorch` and occupy about 13 GB combined.

## Shared Smoke Dataset

Both models used the same eight synthetic training rows and three test rows.
Features were `age`, `debt_ratio`, and `consecutive_overdue_months`. This data
is desensitized and only validates the execution chain.

## Results

| Model | Device | Load/inference result | Elapsed |
| --- | --- | --- | --- |
| TabPFN v2 | CUDA | Completed; predictions and probabilities returned | 4.824 s |
| TabFM 1.0.0 PyTorch | CUDA | Loaded local classification weights; predictions and probabilities returned | 0.696 s |

The elapsed values are single warm-up runs and are not benchmark-quality
latency measurements. Neither model's predictions should be interpreted as an
accuracy result because the training set has only eight rows.

## Commands

```bash
cd ~/wzh/projects/agents_final_tech
~/miniconda3/bin/conda run --no-capture-output -n wzh_tabular \
  python scripts/smoke_test_tabular_model.py \
  --model tabpfn --device cuda --model-version v2

~/miniconda3/bin/conda run --no-capture-output -n wzh_tabular \
  python scripts/smoke_test_tabular_model.py \
  --model tabfm --device cuda
```

## Remaining Work

1. Build a labeled M1-derived table dataset with train/validation/test splits.
2. Compare TabFM, TabPFN, XGBoost, and LightGBM using accuracy, F1, calibration,
   latency, and peak memory.
3. Accept the gated TabPFN v3 terms only when the v3 comparison is scheduled.
4. Record repeated runs and confidence intervals before drawing conclusions.
