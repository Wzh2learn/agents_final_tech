# Stage D training readiness report（2026-10-05）

> Status: `PREPARED_NOT_AUTHORIZED / DRY_RUN_ONLY`
> Machine config: [`docs/datasets/2026-10-05_stage_d_training_readiness_config_v1.json`](../datasets/2026-10-05_stage_d_training_readiness_config_v1.json)
> Validation: [`docs/datasets/2026-10-05_stage_d_training_readiness_validation_v1.json`](../datasets/2026-10-05_stage_d_training_readiness_validation_v1.json)

## 1. Environment snapshot

| Item | GB10 read-only result |
|---|---|
| GPU | NVIDIA GB10, driver `580.159.03` |
| CUDA | available, 1 device |
| Torch / Accelerate | `2.13.0+cu130` / `1.14.0` |
| Unified memory | available `29,999 MB`; GPU memory fields report `N/A` |
| Disk | 2.6 TB available, 24% used; inode 2% used |
| Heavy services | vLLM / llama server / OpenCode sidecar already resident |
| Missing packages | `peft`, `trl`, `deepspeed` |

No model was imported or loaded. The readiness validator is pure configuration/contract code.

## 2. Arms

| Arm | Purpose | Status |
|---|---|---|
| A0 | Qwen3-8B zero-shot reference | `PREPARED_NOT_RUN` |
| A1 | Qwen3-8B unfiltered QLoRA SFT | `PREPARED_NOT_RUN` |
| A2 | Qwen3-8B checkpoint-filtered QLoRA SFT | `PREPARED_NOT_RUN` |
| A3 | A2 + conditional DPO | `CONDITIONAL_NOT_RUN` |
| S0 | Qwen3-4B training-chain smoke only | `PREPARED_NOT_RUN` |

A1/A2 share model, tokenizer, template, sequence length, epochs, batch, accumulation, learning rate, and seeds `[42,43,44]`. A2 differs only by the frozen checkpoint-filter rule. A3 requires bidirectional preference data and independent adjudication.

## 3. Checkpoint/filter and recovery

- A1 uses every accepted proposal-train row.
- A2 includes only rows with a final record/batch-record action event, no invalid source reference on that sample, canonical target or non-map action, reasoning/transformation evidence, and no post-record revoke before finalization.
- A2 never reads gold, source gold, final correctness, gain/collateral, gate decisions, or model predictions as filter inputs.
- A2 must repeat with the whole DSNY pair excluded as sensitivity.
- Save every epoch and the best development checkpoint under the harmful-map risk limit.
- Resume only from the latest verified checkpoint; preserve failed outputs and reconcile all new processes.

## 4. Resource and monitoring contract

Start gates require disk free at least 20% and 50 GB, inode below 80%, available memory at least 25 GB for 4B smoke or 45 GB for 8B arms, used memory below 85%, GPU utilization below 80%, and exactly one heavy task.

Stop immediately at disk below 15%/30 GB, inode at or above 90%, available memory below 10 GB, used memory above 85%, GPU utilization above 90%, a second heavy task, OOM, or output/log limit breach.

Every run must record PID, start time, heartbeat every 5 minutes, log/checkpoint paths, GPU utilization, available memory, disk free, loss/NaN scan, call count, and process reconciliation.

## 5. Planning estimates

These are **planning estimates only**, not measurements:

| Run class | Estimated GPU time | Peak unified memory | Disk |
|---|---:|---:|---:|
| S0 4B smoke | 5–15 min | 12–20 GB | 1–2 GB |
| A1/A2 per seed | 20–60 min | 20–32 GB | 2–4 GB |
| A1/A2, 3 seeds each | 2–6 GPU-hours | — | 12–24 GB |
| A3 per seed, conditional | 15–45 min | 22–34 GB | 2–4 GB |
| A3, 3 seeds | 0.75–2.25 GPU-hours | — | 6–12 GB |

Total after smoke: `2.75–8.25` estimated local GPU-hours. External API calls and external API cost are both `0`. These ranges require a pilot to replace with measurements.

## 6. Launch blockers

The validator result is `PASS_DRY_RUN_ONLY`, but training execution remains blocked by:

1. exact model/tokenizer revision and licence approval;
2. missing `peft`, `trl`, `deepspeed` or an approved alternative implementation;
3. SOURCE/LABEL/SPLIT/POWER/BASELINE gates;
4. Stage D necessity showing a stable residual;
5. explicit MODEL_GO/TRAINING_GO with budget, window, output paths, and stop conditions.

No A0/A1/A2/A3, 4B smoke, Phase 2, model dispatch, download, or external release is authorized.
