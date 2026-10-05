# MODEL_GO / TRAINING_GO application v1（2026-10-05）

> Status: `PENDING_USER_APPROVAL / NOT_AUTHORIZED`
> Scope: application only; no dependency install, model load, A0-A3 run, Phase 2, or training

## 1. Current gate matrix

| Gate | Status | Blocking fact |
|---|---|---|
| Stage D necessity | **FAIL** | `PILOT_ONLY`; stable residual and necessity are not established |
| SOURCE_GO | **FAIL** | no approved confirmatory source with sufficient independent same-sample clusters |
| LABEL_GO | **FAIL** | Q3 is exploratory with visibility exceptions |
| SPLIT_GO | **FAIL** | Valentine `proposal_train.dev=0`; gate/sealed role policy unapproved |
| POWER_GO | **FAIL** | no real variance/MDE/power receipt or approved UID/family minima |
| BASELINE_GO | **FAIL** | B4 is the comparator, but mandatory split risk is unstable |
| MODEL_GO | **PENDING** | exact model/tokenizer revision and weight licence are not approved |
| TRAINING_GO | **PENDING** | budget, window, output paths and explicit launch decision are not approved |
| SAFETY_GO | **READY_DESIGN_ONLY** | dry-run validator passes; runtime gate has not been executed |
| Dependencies | **FAIL** | `peft`, `trl`, `deepspeed` absent; no alternative implementation approved |

## 2. MODEL_GO fields requiring user decision

| Field | Proposed value | Approval |
|---|---|---|
| Main student family | Qwen3-8B | pending |
| Smoke-only family | Qwen3-4B | pending |
| Exact model revision | user-provided immutable SHA / model artifact hash | **required** |
| Exact tokenizer revision | must match the approved model/template pairing | **required** |
| Weight and tokenizer licence | verified licence artifact/hash | **required** |
| Runtime method | QLoRA SFT for A1/A2 | pending |
| DPO implementation | only after A2 and preference-data gate | conditional |
| Local cache/output identity | no public release; private GB10 only | pending |

## 3. TRAINING_GO fields requiring user decision

| Field | Proposed value | Approval |
|---|---|---|
| First executable arm | S0 4B chain smoke | pending |
| Later arms | A0, then A1/A2; A3 only conditionally | pending |
| Seeds | `[42,43,44]` | pending |
| Sequence length | S0 512; A1/A2/A3 1024 | pending |
| Epochs | S0 1; A1/A2 3 | pending |
| Learning rate / batch / accumulation | `1e-4 / 1 / 8` | pending |
| Output root | `/home/testuser/wzh/stage_d_runs` | pending |
| Per-run output / log limits | 5 GB / 500 MB | pending |
| Execution window | user-approved start/end time | **required** |
| Estimated local compute | 2.75–8.25 GPU-hours after smoke, estimate only | pending |
| External API/model calls | 0 | pending |

## 4. Runtime safety and recovery

- Start only when disk free >=20% and >=50 GB, inode <80%, used memory <85%, GPU utilization <80%, and exactly one heavy task.
- Require available memory >=25 GB for 4B smoke and >=45 GB for 8B arms.
- Stop on available memory <10 GB, used memory >85%, disk <15% or <30 GB, GPU utilization >90%, second heavy task, OOM, or output/log limit.
- Run in the isolated output root with PID, start time, 5-minute heartbeat, logs, checkpoints, GPU/memory/disk metrics, loss/NaN scan, call count and process reconciliation.
- Save every epoch and the best development checkpoint; resume only from a hash-verified latest checkpoint.
- Preserve failed outputs and require all newly created processes to exit before completion.

## 5. Launch order after approval

1. Install or approve exact training dependencies;
2. verify immutable model/tokenizer revisions and licences;
3. run S0 4B dry/smoke only if explicitly approved;
4. replace planning estimates with measured resource results;
5. re-run readiness and safety gates;
6. request a separate A0/A1/A2 execution window;
7. run A3 only if its preference-data gate passes.

## 6. Non-approval statement

This file is not MODEL_GO or TRAINING_GO. It does not lift `DATA_NO_GO`, `RQ2 NOT_IDENTIFIED`, B5 dormancy, Phase 2 closure, patent/publication restrictions, or any data-licensing boundary.

## 7. Model candidate audit result (2026-10-05)

Only local GGUF inference artifacts were found:

- Qwen3-4B Q4_K_M sha256 `7485fe6f11af29433bc51cab58009521f205840f5b4ae3a32fa7f92e8534fdf5`;
- Qwen3-8B Q4_K_M sha256 `d98cdcbd03e17ce47681435b5150e34c1417f50b5c0019dd560e4882c5745785`.

They are not HF QLoRA training checkpoints. Hugging Face metadata-only lookup timed out for both model families; immutable revision, tokenizer revision and licence evidence remain missing. See `docs/experiments/2026-10-05_qwen_model_candidate_metadata_audit.md`.