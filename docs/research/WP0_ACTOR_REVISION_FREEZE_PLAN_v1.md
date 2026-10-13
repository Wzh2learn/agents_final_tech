# WP-0 Actor Revision Freeze Plan v1 (DRAFT)

> date: 2026-10-13 | author: Loop D | status: `PLAN_ONLY - NOTHING EXECUTED` | no model load, no sampling, no training.
> parents: [task card](thesis_experience_v1_task_card.md) Sec.3.2/3.4, [blueprint](THESIS_EXECUTION_BLUEPRINT_v1.md), [qualification appendix](WP0_TATQA_QUALIFICATION_APPENDIX_v1.md) Sec.4-5.

## 1. Purpose

Define how to freeze exactly one actor revision, its generation settings, and its tool interface before any pilot (WP-2), so that the E-arm effect is attributable to the experience package and not to model drift. Producing the freeze receipt is reversible bookkeeping; it does NOT authorise a run. `MODEL_GO` remains PENDING.

## 2. Candidate actors (already validated as artifacts; none is MODEL_GO)

| Candidate | Revision | Licence | GB10 receipt | Role in older record |
|---|---|---|---|---|
| Qwen3-8B | `b968826d9c46dd6066d109eabc6255188de91218` | apache-2.0 | `docs/datasets/2026-10-05_qwen3_8b_artifact_validation_receipt_v1.json` (+sync receipt) | main_student_candidate |
| Qwen3-4B | `1cfa9a7208912126459214e8b04321603b3df60c` | apache-2.0 | `docs/datasets/2026-10-05_qwen3_4b_artifact_validation_receipt_v1.json` | S0_smoke_only |

Both receipts predate this route and are explicitly NOT `MODEL_GO`. Advisor decision required: which one becomes the frozen actor (or an alternative).

## 3. Freeze package (to produce at approval time; read-only checks only)

1. **Revision record**: model id + immutable revision + tokenizer manifest hash + file-manifest hashes re-verified on GB10 (`sha256sum` of shard files; compare against the recorded `lfs_sha256`/`git_blob_sha1` lists in `docs/datasets/2026-10-05_qwen_model_metadata_v1.json`).
2. **Generation settings (proposed defaults to freeze)**: temperature 0; single-shot decoding; max output 512 tokens; input cap 4096; experience block cap 600 tokens; no third round of automatic repair (per card Sec.3.4).
3. **Tool interface hash**: adapter + checker versions (once WP-1 exists) + tool contract (`calc(expression) -> number`).
4. **Environment receipt**: python/torch/runtime versions on the executing host; GPU/CPU identity.
5. **`ACTOR_FREEZE_RECEIPT.json`** + sha256; referenced by the prereg. After this point, any change to any field invalidates the freeze and requires a new receipt (change control; no silent updates).

## 4. Sequence (all rows reversible; none executed yet)

| Step | Action | Precondition |
|---|---|---|
| F1 | Advisor picks the actor + approves `MODEL_GO` for this route | advisor decision |
| F2 | Re-verify artifact hashes on GB10 (read-only) | F1 |
| F3 | Record settings + tool/environment hashes | F1 |
| F4 | Assemble + hash the freeze receipt; attach to prereg draft | F2-F3 |
| F5 | Prereg + C pre-result audit; only then any model call can be proposed | F4 + owner window/budget |

## 5. Risks

- Revision drift (mirror re-downloads) - mitigated by immutable revision + receipt re-check at F2 and at pilot start.
- Setting leakage: any per-item setting change is a protocol violation; the adapter must reject it.
- Receipt provenance: older receipts are historical; F2 must recompute, not re-cite blindly.
