# Loop C final focused re-audit: N1/N2 closure

Task id: `history-offline-audit-20261017-r3`
Role: Loop C independent reviewer.
Mode: read-only focused re-audit of the two residual findings from `LOOP_C_REAUDIT.md`.

Do not modify files, call models/services, collect data, train, or authorize the online collection. AI review is not human semantic gold.

## Scope

Verify only:

1. **N-2 accounting sign convention**
   - `parse_numeric("−1.25")`, `parse_numeric("–1.25")`, `parse_numeric("—1.25")`, `parse_numeric("(−1.25)")`, `parse_numeric("(-1.25)")`, and `parse_numeric("(1.25)")`.
   - Placeholder-only dash forms remain `None`.
   - No `(−N)` double-inversion remains.
   - Tests cover the corrected behavior.

2. **N-1 provenance citations**
   - `MODEL_EXPOSURE_PROVENANCE` accurately distinguishes TQ-4/TQ-5 selected tasks, Q02-Q04 content mapping, and WP2 opaque-ID prompt exposure.
   - No claim says raw UIDs appeared directly in TQ-4 artifacts when only deterministic content mapping established the link.
   - The provenance map is included in `EXPOSURE_AND_SPLIT_AUDIT.json`.

3. **Final package consistency**
   - Local and GB10 11/11 receipts pin implementation and test hashes.
   - `EXPOSURE_AND_SPLIT_AUDIT.json`, `SOURCE_CLUSTERS.json`, `SPLIT_PROPOSAL.json`, and `PRE_COLLECTION_HASH_BUNDLE_DRAFT.json` hashes are mutually consistent.
   - `PRE_COLLECTION_HASH_BUNDLE_DRAFT.json` records the sign/provenance fixes and remains `NOT_READY_FOR_COLLECTION`.
   - Online collection, pilot, training, source switching, and public release remain unauthorized.

## Output

Return `ACCEPTED`, `CONDITIONAL`, or `REJECTED`.

If write access is available, write:

`research/tatqa_wp0_2026/history_collection_offline_v1/LOOP_C_REAUDIT3.md`

If write access is denied, return the complete report in the task output for Loop D to transcribe.

The report must identify each N1/N2 item as closed or unresolved, list any new discrepancy, and state whether the owner-facing collection request package is ready for review without overstating scientific or online readiness.
