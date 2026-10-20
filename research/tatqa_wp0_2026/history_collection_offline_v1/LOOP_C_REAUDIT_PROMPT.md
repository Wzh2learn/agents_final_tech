# Loop C focused re-audit: D1-D12 repairs and collection gate

Task id: `history-offline-audit-20261017-r2`
Role: Loop C independent reviewer.
Mode: read-only focused re-audit.

Do not modify reviewed files, old WP-2 artifacts, frozen material, or raw data. Do not commit, push, call a scientific model, start a collection, run a pilot, train, or write memory. This is an independent software/qualification review, not human semantic gold.

## Prior verdict

Read `LOOP_C_EXPOSURE_AND_SOFTWARE_AUDIT.md`. Its verdict was `CONDITIONAL` with D1-D9 repair items and D10-D12 observations.

## Current package

Re-read the current versions of:

- `EXPOSURE_AND_SPLIT_AUDIT.json`
- `SOURCE_CLUSTERS.json`
- `SPLIT_PROPOSAL.json`
- `PRE_COLLECTION_HASH_BUNDLE_DRAFT.json`
- `OFFLINE_RETURN.md`
- `tests/TEST_RECEIPT.json`
- `tests/TEST_RECEIPT_GB10.json`
- all `*.py` implementation files
- `tests/test_offline_v1.py`

## Focused checks

1. D1: Unicode minus handling accepts `−`, `–`, `—`, and fullwidth minus for numeric parsing; verify the corrected 1,149 tasks / 177 eligible clusters / 165 pending future clusters / 12 history clusters.
2. D2: invalid plans return `TOOL_ERROR` through `run_offline_episode` and do not raise.
3. D3: the 12 history clusters are explicitly materialized and are the same 12 model/diagnostic-exposed excluded-future clusters.
4. D4: the non-structural exposure freeze register is 233 UIDs with a canonical hash.
5. D5: both test receipts pin the test file hash.
6. D6: the GB10 receipt is host-labelled and records host/platform/Python.
7. D7: all association thresholds, including paragraph-reuse/table-divergence, are centralized and disclosed.
8. D8: `CRASH` and `COMPLETE` are mutually exclusive; terminal markers cannot be rewritten.
9. D9: non-positive/non-integer/bool token reservations are rejected.
10. D10: return text does not overstate the 2,246 structural-only UIDs as contract tasks; zero structural tasks is explicit.
11. D11: literal model-exposure UIDs have provenance comments.
12. D12: updated outputs and first audit report are traceable.
13. Verify split proposal is deterministic and disjoint: future 8, development 2, history 12, reserve 155.
14. Verify hash bundle remains `NOT_READY_FOR_COLLECTION` and correctly lists unresolved online/runtime/window gates.
15. Confirm no model/endpoint/judge/training/service/collection/pilot side effects.

## Output

Return `ACCEPTED`, `CONDITIONAL`, or `REJECTED`.

If write access is available, write:

`research/tatqa_wp0_2026/history_collection_offline_v1/LOOP_C_REAUDIT.md`

If write access is denied, return the full report in the task output for Loop D to transcribe.

Report:

- prior finding-by-finding closure;
- fresh commands and counts;
- any remaining discrepancy with file/line or JSON path;
- software qualification boundary;
- future-task qualification boundary;
- whether the next collection request is sufficiently prepared for owner review;
- unresolved items and decision handoff to Loop D.
