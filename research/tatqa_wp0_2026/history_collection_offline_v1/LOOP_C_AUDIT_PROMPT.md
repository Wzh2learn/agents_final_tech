# Loop C independent offline audit: exposure, source clusters, and tool chain

Task id: `history-offline-audit-20261017`
Role: Loop C independent reviewer.
Mode: read-only offline audit.

Do not modify reviewed files, old WP-2 artifacts, frozen material, or raw data. Do not commit, push, call a model/service/database, start a collection, run a pilot, train, or write memory. AI review is not human semantic gold.

## Scope

Review the new package under:

`research/tatqa_wp0_2026/history_collection_offline_v1/`

Required inputs:

- `EXPOSURE_AND_SPLIT_AUDIT.json`
- `SOURCE_CLUSTERS.json`
- `OFFLINE_RETURN.md`
- `offline_core.py`
- `source_cluster_builder.py`
- `exposure_classifier.py`
- `collection_chain.py`
- `raw_capture.py`
- `build_exposure_and_split_audit.py`
- `fixtures/synthetic_offline_cases.json`
- `tests/test_offline_v1.py`
- `tests/TEST_RECEIPT.json`

Source and evidence inputs:

- `data/research/tatqa_raw_2026/tatqa_dataset_train.json`
- `data/research/tatqa_raw_2026/tatqa_dataset_dev.json`
- `data/research/tatqa_wp0_2026/candidate_items_v2.json`
- task-root coordinator and TQ evidence files referenced by `build_exposure_and_split_audit.py`.

## Audit questions

1. Does the exposure implementation distinguish:
   - structural scan only;
   - program-generated task/reference pending review;
   - method development or diagnostic use;
   - model/feedback exposure;
   - unknown exposure?
2. Does the code avoid treating TQ-5 exclusion-list membership as model exposure by itself?
3. Are the 2,479 records, 2,443 clusters, 176 eligible clusters, 1,099 contract tasks, 164 pending future clusters and 12 reserved history clusters reproducible from the recorded inputs and code?
4. Does source association preserve separate edge reasons and conservatively merge table-reuse/paragraph-divergence conflicts?
5. Does normalization preserve minus signs, decimal points, digits and punctuation, with exact-only handling for empty/short text?
6. Are thresholds fixed in code and not tuned after results?
7. Does the plan -> actual calculator -> consume chain avoid gold correction and preserve tool errors?
8. Does the independent reference checker distinguish `REFERENCE_RECOMPUTED` from `REFERENCE_UNSCORABLE`?
9. Do raw capture and budget controls prevent overwrite, preserve crash state, and stop at hard caps?
10. Do local and GB10 test receipts support the software claim without weakening assertions?
11. Does the package avoid model, endpoint, judge, training, service, collection and pilot side effects?

## Required checks

- Read the actual implementation and artifacts; do not trust `OFFLINE_RETURN.md` alone.
- Recompute key counts where authorized and locally possible.
- Run only the existing offline tests if needed. Do not create new scientific requests.
- Check source file hashes and output consistency.
- Report every discrepancy with file/line or JSON path.
- Keep `FACT / INFERENCE / VALUE / UNVERIFIED` separate.

## Output

Return one verdict:

- `ACCEPTED`: bounded offline package is internally supported;
- `CONDITIONAL`: specific evidence remains missing;
- `REJECTED`: blocking defect or unsupported claim exists.

If write access is available, write:

`research/tatqa_wp0_2026/history_collection_offline_v1/LOOP_C_EXPOSURE_AND_SOFTWARE_AUDIT.md`

If write access is denied, return the complete report in the task output for Loop D to transcribe.

The report must include:

- scope and excluded actions;
- commands/checks run;
- count verification;
- exposure-layer verification;
- source-cluster verification;
- tool-chain and raw-capture verification;
- test/receipt verification;
- findings and exact locations;
- unresolved items;
- verdict and decision handoff to Loop D.
