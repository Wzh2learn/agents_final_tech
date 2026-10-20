# AUTHORIZED_BOUNDED_SINGLE_COLLECTION Goal

Apply exactly two bounded execution fixes to the existing `history_collection_execution_v1` package, obtain one targeted Loop C re-audit, bind one authorization to the new bundle, and execute exactly one 54-request history collection in the fixed 2026-10-19 20:00–21:30 Asia/Shanghai window.

## Done when

1. Every request is preceded by an active-window check with enough remaining time for the fixed request timeout; expiry stops new requests and persists partial evidence.
2. The three qualification fixtures execute first as six requests. If interface/schema/tool/reference qualification fails, history request count is zero. If they pass, at most 48 history requests follow and the total remains 54.
3. `TASK_REFERENCE_MANIFEST.json` is byte-identical to baseline `5be130d7...`; task/reference/model/generation/prompt/source/sampling identity is unchanged and `max_tokens` remains 256.
4. Baseline bundle `0d13f556...` and its changed artifacts are preserved separately; a change record and manifest comparison prove the allowed delta.
5. Targeted Loop C checks only window-boundary partial persistence, fixture gating/counts, and manifest identity.
6. Local and GB10 tests pass and a new bundle is generated; the old hash is never relabeled as the new bundle.
7. One authorization file binds the new bundle, exact UTC/Asia-Shanghai window, 54/600000/0/1 budget, and the architect authorization reference without fabricating signatures.
8. At window start the existing bound local service is identity-checked without starting/restarting it, then one run executes. `COLLECTION_RETURN.md` reports trustworthy chains, paired attempts, separate reference/tool/consumption outcomes, incomplete paths, costs, bundle, and run identity.

## Never touch

- Task/reference manifest contents, model artifact, tokenizer/chat template, generation parameters including `max_tokens=256`, prompt text, source split, selected tasks, or sampling counts.
- Old WP-2, TQ-4/TQ-5, Paper E, frozen results, raw datasets, memory, unrelated dirty files, or prior reviews.
- No pilot, training, memory write-back, source switch, public release, service start/restart/switch, retry, sample top-up, or cross-window resume.

## Stop if

- Fixture qualification fails; history requests must remain zero.
- The window expires; save partial results and do not send another request.
- Identity drift, hidden-reference leakage, raw loss/overwrite, or request-response correspondence failure occurs.
- Any task/reference manifest byte changes.
- The targeted review leaves a blocker or the two-hour repair/review limit is reached.
