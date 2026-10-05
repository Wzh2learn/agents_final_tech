# SUMMARY: Stage D readiness and model synchronization

> Status: current summary | Updated: 2026-10-05 | Execution state: prepared, not authorized for formal training

## Current answer

Stage D necessity remains `PILOT_ONLY`. B4 is risk-admissible in the primary and pair-invalid slices, but the salted split remains unstable. A dedicated student is therefore not yet justified.

The approved initial A2 criteria are now explicit: coverage gain over B4 `>=0.05`, target exact non-inferiority margin `<=0.02`, maximum single-pair residual/gain share `<=0.50`, harmful-map risk upper `<=0.10` in all three slices, and positive A2-B4 coverage-delta lower bounds in primary and pair-invalid. A2 is not run, so gain, target non-inferiority, gain concentration and coverage deltas are `NOT_ESTIMABLE`; the salted risk upper bound is `0.1250` and fails.

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



## Formal negative closure context

The current goal is `COMPLETE_FOR_FORMAL_NEGATIVE_PATH_B`. The formal scientific boundary is `DATA_NO_GO / RQ2 NOT_IDENTIFIED`: Valentine's 551 tasks provide only 8 conservative origin components, the archive has no native trajectory/checkpoint bridge, and full Evaluate-Distill-Evolve validation is future work. Track B is a within-origin exploratory pilot sealed at `/home/testuser/wzh/track_b_adapter_20261005_seal/` with manifest hash `dc388959150c98ffa7639108e1e80e306c346317b1cdced632ab66593960a04b`; it is not RQ2, Stage D, Stage R or RQ4.

The formal small-paper route is the mature Stage E internal submission version. External submission, patent/venue/authorship/camera-ready, Stage D/R/RQ4, training, Phase 2 and external release remain incomplete. Scientific/test evidence comes from `f0764e714d21408a1a848ee0f327a22294eda73a` or an equivalent GB10 head; `652c9c6` is metadata-only and `1d5a7ff` is documentation/workspace neat.

## Boundary

Both model artifacts are validated, but this is not MODEL_GO. No model load, S0, A0-A3, Phase 2, or training has started. The user has conditionally authorized automatic S0/A0-A2 only after all scientific/safety gates and stable Stage D residual pass; current gates do not pass. `DATA_NO_GO`, `RQ2 NOT_IDENTIFIED`, and Stage D `PILOT_ONLY` remain active. Route V still has a 30-cluster acquisition gap against the 40-cluster target.
