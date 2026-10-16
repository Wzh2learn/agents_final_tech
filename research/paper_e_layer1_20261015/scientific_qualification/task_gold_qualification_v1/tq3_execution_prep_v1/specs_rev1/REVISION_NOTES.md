# specs_rev1 - Revision Notes (vs measurement_contract_v2/cases)

> Date: 2026-10-16. Actor: Loop D (AI). v2 files are NOT overwritten.
> rev1 files are the execution authority for the 9 tasks; v2 remains the
> record of the previous revision.

## Changes in rev1

1. `question_uid` / `table_uid` filled from `coordinator/case_provenance.json`;
   both asserted against the raw TAT-QA records (`raw/tatqa_dataset_train.json`,
   `raw/tatqa_dataset_dev.json`) for all 9 cases - see `BUILD_RECEIPT.json`
   (`uid_verification`, 9/9).
2. Per-case table pins restored:
   - v2 stored `source_table_sha256` = sha256 of the drift-v0 corpus file
     `data/research/drift_v0/input/tatqa_tables.json` (3e7e0568...) and
     `perturbed_table_sha256` = sha256 of
     `data/research/drift_v0/output/injected_tables.json` (827092cf...) for
     ALL 9 specs (identical values across specs; corpus-level, not per-case).
     This is confirmed by `BUILD_RECEIPT.json` (`v2_pin_observations`).
   - rev1: `source_table_sha256` / `perturbed_table_sha256` are the per-case
     canonical hashes of the packet tables; the corpus-file hashes moved to
     `corpus_pins` with accurate labels.
   - Canonical serialization: `json.dumps(obj, ensure_ascii=False,
     sort_keys=True, separators=(',', ':')).encode('utf-8')`.
3. Added `raw` block: raw file name + raw file sha256 + record/question index.
4. Added `panel_plan`:
   - Q02/Q03/Q04/Q05/Q10/Q12: `dev_panel_dry_run_input` (`in_primary_metrics: true`).
   - Q06/Q08/Q09: `exploratory_ambiguity_side_case` (`in_primary_metrics: false`).

## Not changed (copied verbatim from v2)

`task_requirements` / `reference_paths` / `expression` / `expected` / `precision`
/ `semantic_assumptions` / `evidence_effect_ai` / `reference_status_ai` /
`status` / `isolation` / `limitations`.

## Quarantine unchanged

Q01/Q07/Q11 have no rev1 file; they remain in
`measurement_contract_v2/quarantine/` with the original questions/references.
