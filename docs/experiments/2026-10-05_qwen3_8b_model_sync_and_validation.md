# Qwen3-8B mirror sync and artifact validation (2026-10-05)

> Status: `PASS_ARTIFACT_VALIDATION_NOT_MODEL_GO`
> Provenance: `hf-mirror.com` third-party fallback after official Hugging Face network block
> Model load: not started

## Download contract

- repository: `Qwen/Qwen3-8B`
- revision: `b968826d9c46dd6066d109eabc6255188de91218`
- endpoint: `https://hf-mirror.com`
- `token_sent=false`
- `HF_HUB_DISABLE_XET=1`
- `HF_HUB_ENABLE_HF_TRANSFER=0`
- target: `/home/testuser/wzh/models/hf/Qwen3-8B`
- exact allowlist: 15 metadata-listed files
- download duration: 13m41s
- download PID: `3412266`
- monitor PID: `3412262`
- exit code: `0`
- process cleanup: PASS; no download/monitor process remained

Operational logs and manifests are under `/home/testuser/wzh/model_sync_logs/qwen3_8b_hfmirror_noxet_b968826d_20261005.*`.

## Artifact validation

GB10 real validator result:

- 15/15 immutable identities: 6 LFS SHA-256 and 9 Git blob SHA-1;
- 5 safetensors shards present and headers parsed;
- 399 `weight_map` entries exactly covered 81 + 114 + 111 + 92 + 1 tensors;
- model index metadata total size `16,381,470,720`;
- `qwen3` / `Qwen3ForCausalLM` config parsed;
- `Qwen2Tokenizer` parsed;
- tokenizer revision equals model revision;
- Apache License 2.0 verified;
- canonical model-root-relative clean manifest: 15 entries, `e47b9aca03bbdb25886318a0f1bea76e13303f2971c21ecb8e0ffe69029172bb`;
- canonical model-root-relative full manifest: 48 entries, `6ba50550273e1b8573d0189ab1bebaac43bc173dcb5b464aade2c1f13895ebca`.

Receipts:

- sync receipt: `docs/datasets/2026-10-05_qwen3_8b_sync_receipt_v1.json`, SHA-256 `684dfb9b6d9d91f92776ac771b975f560674a6234336ec9ebd12fce0d3d7a322`;
- artifact receipt: `docs/datasets/2026-10-05_qwen3_8b_artifact_validation_receipt_v1.json`, SHA-256 `8c35a447d911caafb80a4f26526199b38658952cb7294ec5087600dd73c0aca8`.

## Readiness boundary

GB10 readiness reports `smoke_model_revision_ready=true`, `student_model_revision_ready=true`, and `model_revision_ready=true`. This means both immutable model/tokenizer artifacts are validated only.

Training remains `BLOCKED` because SOURCE/LABEL/SPLIT/POWER/BASELINE/SAFETY, stable Stage D residual, A2-vs-B4 criteria, and the frozen execution window are not all satisfied. No S0, A0, A1, A2, A3, Phase 2, model load, or training has started. `DATA_NO_GO`, `RQ2 NOT_IDENTIFIED`, and Stage D `PILOT_ONLY` remain unchanged.
