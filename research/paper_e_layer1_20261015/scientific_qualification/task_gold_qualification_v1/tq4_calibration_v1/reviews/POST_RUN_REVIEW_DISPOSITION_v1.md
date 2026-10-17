# TQ-4 post-run review disposition v1

Date: 2026-10-17 Asia/Shanghai. Scope: close the eight notes in `POST_RUN_REVIEW_v1.md` without changing the original run, raw responses, ledger, manifest, frozen material, or `TQ4_RUN_RETURN.md`.

| Note | Disposition |
|---|---|
| N-1 config provenance | OPEN_PROVENANCE_GAP. The run-time config was not preserved. Its mtime lies inside the run window, so the earlier statement that `scoring_dir` was added only after the run is retracted as unsupported. No synthetic old config or `RUN_META` correction is created. TQ-5 uses a hash-enforced pre-run snapshot. |
| N-2 parse-fail display | FIXED_IN_NEW_ANALYZER. A parse failure now renders as `invalid`; `ledger_state=done` is retained separately and is never presented as a model decision. |
| N-3 denominators | CORRECTED_IN_ERRATA. Full-run valid output is 35/36. B valid decisions are 15/16: Part 1 4/4 and Part 2 11/12. HTTP success is not output validity. |
| N-4 point-check count | CORRECTED_IN_ERRATA. The pre-run record is 14/14, including `material_pin_check_full`. |
| N-5 timing | CORRECTED_IN_ERRATA. First request is 16:29:02 Asia/Shanghai and elapsed time is 194 seconds by first-request/last-response accounting. |
| N-6 mirror receipt | RETRACTED_HISTORICAL_CLAIM. The original report lacked a dual-end receipt. A later receipt may establish the current mirror state but cannot prove the historical wording. |
| N-7 N1 wording | CONSTRAINED_INTERPRETATION. Evidence supports only semantic disagreement between reference matching and checker verification. It does not establish that the reference is wrong or that the actor is absolutely correct. C's decision is `alarm`, while empty `contradiction_points` and accepting language at the end of its reason are retained as internal inconsistency. |
| N-8 field naming | DEFERRED_NO_CODE_CHANGE. `tokens_unsettled` remains unchanged in the old receipt; the current settled amount is reported explicitly in new documents. |

Q03-C3/C4 keep their original frozen construction labels and original results. Because the arithmetic direction is semantically ambiguous, they do not count as confirmed shared misses. Semantic qualification for those negative examples is NOT_ESTABLISHED.
