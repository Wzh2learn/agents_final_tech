# Stage D training readiness report（2026-10-05）

> Status: `PREPARED_NOT_AUTHORIZED / DRY_RUN_ONLY`
> Authority: GB10 only; local synthetic tests are `DEV_ONLY / NON_AUTHORITATIVE`
> Current-state rule: section 9 supersedes stale status text in the historical dry-run sections below.
> Machine config: [`docs/datasets/2026-10-05_stage_d_training_readiness_config_v1.json`](../datasets/2026-10-05_stage_d_training_readiness_config_v1.json)
> Validation: [`docs/datasets/2026-10-05_stage_d_training_readiness_validation_v1.json`](../datasets/2026-10-05_stage_d_training_readiness_validation_v1.json)
> Qwen3-4B receipt: [`docs/datasets/2026-10-05_qwen3_4b_artifact_validation_receipt_v1.json`](../datasets/2026-10-05_qwen3_4b_artifact_validation_receipt_v1.json)

## 1. GB10 authority and evidence level

Local fixture runs observed during validator development, including the intermediate `3 failed / 1 passed` state, are development diagnostics only. They are not Qwen artifact validation, readiness acceptance, project pytest results, scientific evidence, or Goal-state evidence.

The accepted evidence in this report was generated on GB10:

- focused contract tests: `15 passed`;
- Qwen3-4B real artifact validator: `PASS_ARTIFACT_VALIDATION_NOT_MODEL_GO`;
- readiness validator: `PASS_DRY_RUN_ONLY`;
- import/config/tokenizer smoke: PASS without loading model weights.

No `AutoModel` or training model was loaded.

## 2. Environment and safety dry-run

| Item | GB10 read-only result | Gate |
|---|---|---|
| Disk | 3.6T total, 826G used, 2.6T available, 24% used | PASS |
| Inode | 2% used | PASS |
| Memory | 121Gi total, 30Gi available, 90Gi used | PASS for 4B smoke |
| GPU utilization | 0%; unified-memory fields report `N/A` | PASS |
| Resident services | production vLLM and llama-server remain running | no restart, no overlap action |
| S0 heavy-task window | not opened | `NOT_RUN` |

The measured values satisfy the numeric 4B smoke start gates. This is a dry-run snapshot only and does not itself grant MODEL_GO, TRAINING_GO, or S0 execution.

## 3. Qwen3-4B artifact validation

Immutable revision: `1cfa9a7208912126459214e8b04321603b3df60c`.

- 13 top-level files validated by size and immutable identity;
- 4 LFS files matched `lfs_sha256`; 9 non-LFS files matched Git blob SHA-1;
- 3 safetensors shard headers parsed without loading tensors;
- 398 `weight_map` entries exactly covered 174 + 219 + 5 tensors across 3 shards;
- `config.json` parsed as `qwen3` / `Qwen3ForCausalLM`;
- `tokenizer_config.json` parsed as `Qwen2Tokenizer`;
- tokenizer revision is bound to the same immutable model revision;
- Apache License 2.0 text verified.

Canonical model-root-relative sorted manifests:

- clean, 13 entries: `3d1c26944d87b4f8429cb66ca40fa5fd190fc9adf8bd58e07f625b3471891101`;
- full cache, 42 entries: `3584ef3de9e6c4fd5d8fab458c7265531bf4b24d7644e5bd1a555377011d7b91`.

Manifest paths are model-root-relative POSIX paths. Absolute paths and `..` are rejected. The older absolute-path download manifests remain provenance-only with aggregate hashes `28860ec...` and `fdba6de...`.

GB10 receipt SHA-256: `227576f2b90a0b7c22a77af0de60f5f3d8bc0d9bd158af59b70b463bc574cf5d`.

## 4. Import/config/tokenizer smoke

GB10 package imports passed:

- `torch 2.13.0+cu130`
- `transformers 5.14.1`
- `accelerate 1.14.0`
- `peft 0.21.2`
- `trl 1.14.1`
- `datasets 5.0.1`

`pip check` passed. GB10 config/tokenizer-only loading reported `model_type=qwen3`, `tokenizer_class=Qwen2Tokenizer`, and tokenizer vocabulary size `151669`. Model weights were not loaded.

## 5. Readiness result

GB10 readiness validator output:

- `status=PASS_DRY_RUN_ONLY`;
- `smoke_model_revision_ready=true`;
- `student_model_revision_ready=false`;
- `model_revision_ready=false`;
- `missing_dependencies=[]`;
- `deepspeed=intentionally_not_installed_single_device_qlora`;
- `stage_d_necessity_threshold_status=APPROVED_INITIAL_VALUES`;
- `training_execution_authorized=false`;
- `training_status=NOT_RUN`;
- `phase2_status=NOT_RUN`;
- `data_go=false`;
- `paper_result=false`.

`model_revision_ready=false` because Qwen3-8B is still `NOT_DOWNLOADED`; Qwen3-4B success does not substitute for the main student artifact.

## 6. Frozen initial Stage D necessity criteria

These user-approved values are design starting points and cannot be changed after results are visible:

- A2 absolute correct-map coverage gain over B4: at least `0.05`;
- target exact non-inferiority margin: at most `0.02`;
- maximum single-pair contribution to residual/gain: at most `0.50`;
- primary, pair-invalid, and salted slices must all have harmful-map risk upper bound `<= 0.10`;
- A2-B4 coverage delta lower bound must be `> 0` in primary and pair-invalid slices.

Current evidence verdict remains `PILOT_ONLY`; no A2 residual exists yet.

## 7. Conditional execution authorization

The user has conditionally authorized automatic S0 and A0/A1/A2 execution only after all six conditions pass:

1. Qwen3-4B and Qwen3-8B artifact, tokenizer, licence, and manifests validate on GB10;
2. SOURCE/LABEL/SPLIT/POWER/BASELINE/MODEL/SAFETY all pass;
3. Stage D necessity changes from `PILOT_ONLY` to a stable residual;
4. A2 satisfies the preregistered risk, coverage, and target-exact criteria relative to B4;
5. training budget, output root, execution window, and stop conditions are frozen;
6. execution is GB10-only, isolated-output, and one heavy task at a time.

A3 DPO, Phase 2, new data/licence, formal submission, arXiv, code release, and external release still require separate authorization. If any gate fails, the result remains `SIMPLE_SUFFICIENT`, `NO_CLEAR_SIGNAL`, `PILOT_ONLY`, or `DATA_NO_GO`; training must not mask data or power insufficiency.

## 8. Execution boundary

No S0, A0, A1, A2, A3, Phase 2, B5 installation/run, model dispatch, new download, or external release has started. Qwen3-8B remains `NOT_DOWNLOADED`.

`DATA_NO_GO`, `RQ2 NOT_IDENTIFIED`, and Stage D `PILOT_ONLY` remain unchanged. Model artifact validation is not MODEL_GO and is not a scientific result.
