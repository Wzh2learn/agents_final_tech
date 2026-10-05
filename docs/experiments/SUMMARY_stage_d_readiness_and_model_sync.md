# SUMMARY: Stage D readiness and model synchronization

> Status: current summary | Updated: 2026-10-05 | Execution state: prepared, not authorized for formal training

## Current answer

Stage D necessity remains `PILOT_ONLY`. B4 is risk-admissible in the primary and pair-invalid slices, but the salted split remains unstable. A dedicated student is therefore not yet justified.

Training readiness is prepared for Qwen3-4B smoke and Qwen3-8B QLoRA arms. `peft`, `trl`, `datasets`, and `accelerate` are installed; `deepspeed` is intentionally omitted on the single-device path.

GB10 focused validator tests pass (`15 passed`). Qwen3-4B passed real artifact validation with 13/13 immutable identities, 3 valid safetensors shard headers, 398 covered tensor entries, tokenizer/licence parsing, and canonical model-root-relative manifests. The readiness dry-run reports `smoke_model_revision_ready=true`, `student_model_revision_ready=false`, and `model_revision_ready=false`; no model weights were loaded.

Both Qwen3-4B and Qwen3-8B exact-revision artifacts are present and validated on GB10 through the approved `hf-mirror.com` fallback with `token=false` and Xet disabled. Qwen3-8B passed 15/15 immutable identities, 5 shard headers, 399 tensor entries, tokenizer/licence, and canonical relative manifests. `model_revision_ready=true`; this is not MODEL_GO.

## Canonical evidence

| Topic | Canonical file |
|---|---|
| Stage D data boundary | `docs/experiments/2026-10-05_stage_d_data_no_go_boundary_and_requirements.md` |
| Necessity gate | `docs/experiments/2026-10-05_stage_d_necessity_gate.md` and `docs/experiments/2026-10-05_stage_d_necessity_residual_memo.md` |
| Training readiness | `docs/experiments/2026-10-05_stage_d_training_readiness_report.md` |
| Machine readiness config | `docs/datasets/2026-10-05_stage_d_training_readiness_config_v1.json` |
| Dependency decision | `docs/experiments/2026-10-05_training_dependency_audit.md` |
| Qwen immutable metadata | `docs/datasets/2026-10-05_qwen_model_metadata_v1.json` |
| Mirror sync and download contract | `docs/experiments/2026-10-05_model_sync_mirror_success.md` |
| GB10 Qwen3-4B artifact receipt | `docs/datasets/2026-10-05_qwen3_4b_artifact_validation_receipt_v1.json` |
| Qwen3-8B sync and validation | `docs/experiments/2026-10-05_qwen3_8b_model_sync_and_validation.md` |
| Qwen3-8B sync receipt | `docs/datasets/2026-10-05_qwen3_8b_sync_receipt_v1.json` |
| Qwen3-8B artifact receipt | `docs/datasets/2026-10-05_qwen3_8b_artifact_validation_receipt_v1.json` |
| MODEL_GO / TRAINING_GO request | `docs/datasets/2026-10-05_model_training_go_application_v1.md` |

## Historical chain

`docs/archive/experiments/2026-10-05_model_sync_blocked.md` records the official Hugging Face path failure before the mirror fallback succeeded. It is not the current acquisition state.

## Boundary

Both model artifacts are validated, but this is not MODEL_GO. No model load, S0, A0-A3, Phase 2, or training has started. The user has conditionally authorized automatic S0/A0-A2 only after all scientific/safety gates and stable Stage D residual pass; current gates do not pass. `DATA_NO_GO`, `RQ2 NOT_IDENTIFIED`, and Stage D `PILOT_ONLY` remain active. Route V still has a 30-cluster acquisition gap against the 40-cluster target.
