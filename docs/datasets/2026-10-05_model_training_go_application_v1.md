# MODEL_GO / TRAINING_GO application v1（2026-10-05）

> Status: `PENDING_USER_APPROVAL / NOT_AUTHORIZED`
> Scope: application only; no dependency install, model load, A0-A3 run, Phase 2, or training

## 1. Current gate matrix

Conditional authorization update: after all six user-specified conditions pass, S0 and A0/A1/A2 may proceed automatically without per-item confirmation. Both model artifacts are now validated, but the scientific gates fail or remain incomplete and Stage D is `PILOT_ONLY`; therefore no training arm is currently authorized.

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
| Dependencies | **READY_WITH_APPROVED_ALTERNATIVE** | `peft==0.21.2`, `trl==1.14.1`, `datasets==5.0.1` installed; `accelerate==1.14.0` approved for single-device QLoRA; `deepspeed` intentionally not installed |

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
## 8. Model sync status (2026-10-05)

Historical official-path status: before the approved mirror fallback, Qwen3-4B weight download was `MODEL_SYNC_BLOCKED` because `huggingface.co:443` was unreachable from GB10 and the local official path. The current artifact status is in section 9.

## 9. Model sync addendum (2026-10-05)

The official Hugging Face path remains blocked. Under the approved fallback, Qwen3-4B revision `1cfa9a7208912126459214e8b04321603b3df60c` was downloaded through `https://hf-mirror.com` with `token=false` and `HF_HUB_DISABLE_XET=1`.

The 13 top-level model files and all 3 safetensors shards are present at `/home/testuser/wzh/models/hf/Qwen3-4B`; model index validation reports 398 weight entries and all shards present. The clean model-file manifest is `28860ecbda224e8d9ead8ec91e68abd6488dc3e33f46a768d0f33368203e456c`, and the full cache manifest is `fdba6de9068e02663fcbc7aec02125fd310fed82692cf37360f2924b81b1842a`. Apache-2.0 licence and mirror `X-Repo-Commit` were verified. Qwen3-4B is now `READY_FOR_ARTIFACT_VALIDATION`; Qwen3-8B remains `NOT_DOWNLOADED`.

GB10 real validation subsequently passed: `PASS_ARTIFACT_VALIDATION_NOT_MODEL_GO`. The canonical model-root-relative manifests are clean `3d1c2694...` and full `3584ef3d...`; receipt SHA-256 is `227576f2...`. Readiness reports `smoke_model_revision_ready=true`, `student_model_revision_ready=false`, and `model_revision_ready=false`. Qwen3-8B remains `NOT_DOWNLOADED`.

Qwen3-8B subsequently passed GB10 real validation at revision `b968826d...`: 15/15 identities, 5 shard headers, 399 tensors, tokenizer/licence, clean `e47b9aca...`, and full `6ba50550...`. Readiness now reports `student_model_revision_ready=true` and `model_revision_ready=true`. This closes model artifact readiness only; scientific gates, stable residual, and training window remain blocking.

This addendum does not grant MODEL_GO, TRAINING_GO, S0, A0-A3, Phase 2 or training execution. It only closes the Qwen3-4B artifact acquisition path and records third-party mirror provenance.

The later conditional user authorization permits S0/A0-A2 automatically only after both models and every scientific/safety gate pass. It does not change the current blocked state or authorize A3, Phase 2, new data/licence, or external release.

The model downloads and artifact validations are complete, but no S0, A0, A1, A2, A3, Phase 2, model load, training, or external release has started.
