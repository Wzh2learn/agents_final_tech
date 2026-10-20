# Same-Number Role Qualification Return

Status: `QUALIFICATION_FIXED_NO_MODEL_REQUEST`

## Root cause

`build_same_number_role_tasks.py` selected the first collision case using only a
row-label difference. In `cluster_1582`, this selected a pair whose actor-visible
row label and period were identical and whose only distinction was hidden
`row_index` 4 versus 9. The generated hidden reference nevertheless marked that
pair `WRONG_ROLE`.

## Fix

- Compare actor-visible `row_label`, period fields, unit and scale using a
  conservative canonical text key.
- Qualify `WRONG_ROLE` only when at least one visible role field differs.
- Mark hidden-coordinate-only differences `UNSCORABLE_FOR_REFERENCE`; do not put
  them in model tasks.
- Keep positive controls and all source/raw/frozen artifacts unchanged.
- Record qualification status and visible/hidden difference fields in new
  versioned output.

## Deterministic requalification

Input frozen package:

`../SAME_NUMBER_ROLE_TASKS_DRAFT.json`

Output:

- `artifact_v2/SAME_NUMBER_ROLE_TASKS_QUALIFICATION_V2.json`
- `artifact_v2/SAME_NUMBER_ROLE_QUALIFICATION_REPORT_V2.json`

Counts from the frozen package:

- 12 negative candidate pairs checked;
- 11 `QUALIFIED_VISIBLE_ROLE_DIFFERENCE`;
- 1 `UNSCORABLE_FOR_REFERENCE` (`NR_development_1582_N2`);
- 22 complete matched tasks retained after removing the invalid pair;
- 0 model requests issued.

The corrected generator will skip the row-index-only case and select the
period-difference case in the same cluster when the raw TAT-QA files are
available. The raw files are not present in this workspace, so no raw-backed
package was regenerated.

## Regression

Command:

```text
python -m unittest discover -s qualification_v2/tests -p 'test_*.py' -v
```

Result: 6 tests passed, including row-index-only rejection, visible row/period/
unit qualification, candidate selection, and `make_task` metadata.
