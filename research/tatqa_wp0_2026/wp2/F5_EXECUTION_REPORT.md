# F-5 / F-10 Execution Report

> task: `tatqa-wp2-f5-20261013` | date: 2026-10-14 | loop: A
> authorization: owner default closure, authorized 2026-10-13 night
> boundary: pilot eligibility and S0C checker fix only; zero model, endpoint, judge, training, and external-network calls

## 1. Status

| Deliverable | Status | Result |
|---|---|---|
| F-5 eligibility rule and receipt | `PASS_WITH_RESERVE_REPLACEMENT_RECOMMENDATION` | 352 candidates -> 316 eligible; 36 generic-currency items excluded |
| 22 role-origin verification | `PASS_WITH_ONE_EXCEPTION` | 21/22 retain two eligible items; one reserve origin falls to zero |
| Reserve replacement guidance | `AVAILABLE` | rank 23 is the first eligible unassigned origin; no role was changed |
| F-10 attribution fix | `CLOSED` | dedicated equivalent-form fixture changes only `wrong_period` -> `wrong` |
| S0 full fixture rerun | `PASS` | 7 obligations + 3 unit-gate + 1 direct-form + 1 equivalent-form + 5 numeric-rendering cases |
| Historical receipt preservation | `PASS` | S0 and S0B SHA-256 values are pinned and byte-unchanged |
| Documentation lint | `PASS` | 0 failures and 14 unrelated existing warnings |

Eligibility totals are `total=352`, `excluded_currency=36`, and `eligible=316`. The eligible source-unit distribution is `null=312`, `%=2`, `million=2`; absent source-unit keys count zero. Target resolution counts are `identity_unit=312`, `percent_identity=2`, and `scale_identity=2`.

The only shortfall is reserve origin `tatqa_dace18a6-701f-49d4-a16d-078e5b62fc94`: both candidates are generic currency. The first replacement recommendation under the unchanged rank rule is `tatqa_cb626a5c-7b30-46ef-b0a7-971bc2196678` at rank 23, with two eligible candidates. This recommendation is not applied.

F-10 uses the case `equivalent_form_valid_periods_wrong_delta_valid_unit`: periods `[2024, 2025]` are legal equivalent form, both delta values are wrong, and `unit` is correct. The pre-fix observation is `wrong_period`; the fixed outcome is `wrong`. An additional 24-case strictness matrix found five changed classifications, all `wrong_period` -> `wrong`; no case flipped to a correct class.

## 2. Files and SHA-256

| File | SHA-256 |
|---|---|
| `research/tatqa_wp0_2026/wp2/check_pilot_eligibility.py` | `614fad85e7528146ee487c92ffa80e22b32d4144d9cd1634a802b183814bd71e` |
| `research/tatqa_wp0_2026/wp2/PILOT_ELIGIBILITY_RECEIPT.json` | `7cda8d71f3ea46fe1d44271534f47aae4b35fef949d16a99ac509f68bd7c7068` |
| `docs/research/WP2_F5_ELIGIBILITY_DECISION_v1.md` | `f45718a3295f4c77cf4c2576104727a9630332a0f8c94a6680bebbd38bbd5d34` |
| `docs/research/WP2_TARGET_UNIT_RULES_DRAFT_v1.md` | `ee665e9df0cdb21e21834afa30196821238398d9fd2f75a7b25f07a6632db8fc` |
| `research/tatqa_wp0_2026/wp1/checker_v2.py` | `aeedf62b7d44a1422ee631783c3daa47be8a3e7e8811462a23ad3c520ce4d048` |
| `research/tatqa_wp0_2026/wp1/fixtures/s0c_equivalent_form_fixtures_v2.json` | `58e17ac50713aa8892222041d073e2bbd8a5b704bf312eef6d6fc622d1d5e51d` |
| `research/tatqa_wp0_2026/wp1/s0_run_fixtures_v2.py` | `2f5460de68218c6b0a8aaf6fede245ba752ff7d0d825ccaf9000669f9d603686` |
| `research/tatqa_wp0_2026/wp1/S0C_FIX_RECEIPT.json` | `a6b888177557d70d9d03da7bc36d2b2ab94747970ba93b02d37c87032ce3264f` |
| `research/tatqa_wp0_2026/wp1/S0_FIX_RECEIPT.json` | `1085cde79b3085eaa6963799c6c4018937c070149dbc5e619bb4cf0d39561c50` |
| `research/tatqa_wp0_2026/wp1/S0B_FIX_RECEIPT.json` | `b759a5e74b1d58c2500380f2301f5988c67bdb284e5453cdacab524236eb2c17` |
| `docs/INDEX.md` | `03d5ea456b7d1f2682c68abf346d55406b4a6311cd8a24517be7be6f9f73a1c5` |

This report does not embed its own SHA-256 because embedding would make the value self-referential. Its final file hash is reported outside the file in the task handoff.

Input hashes are independently pinned inside the eligibility receipt:

| Input | SHA-256 |
|---|---|
| `data/research/tatqa_wp0_2026/candidate_items_v2.json` | `5f61f2a476c220f4ed4c159030490c6dfaabcea9778820abc89d3bed859738aa` |
| `data/research/tatqa_wp0_2026/origin_manifest.json` | `3718e6fef4d52bec0c1c29b47ba9ab60e298754b9e8527835d09c9d223d70cea` |
| `research/tatqa_wp0_2026/wp2/SPLIT_RERUN_RECEIPT.json` | `771f209634c8a2fb4e71734ac6a14e161260de624506dd1f9a8065fbaeafc668` |

## 3. Commands and evidence

1. Eligibility generation, run twice with byte comparison:

   `PYTHONPATH=src python3 research/tatqa_wp0_2026/wp2/check_pilot_eligibility.py`

   Both runs returned `PILOT_ELIGIBILITY_RECEIPT_PASS ... total=352 excluded_currency=36 eligible=316 role_origins=22 role_shortfalls=1`. `cmp` passed; final receipt SHA-256 is `7cda8d71f3ea46fe1d44271534f47aae4b35fef949d16a99ac509f68bd7c7068`.

2. S0/S0B/S0C preservation and full S0 fixture runner, run twice:

   `PYTHONPATH=src python3 research/tatqa_wp0_2026/wp1/s0_run_fixtures_v2.py`

   Both runs returned:

   `S0_FIXTURES_PASS obligations=7 unit_gate_cases=3 direct_form_cases=1 equivalent_form_cases=1 numeric_rendering_cases=5`

   The two S0C receipts were byte-identical. Before and after hashes for S0 and S0B were unchanged.

3. Python compilation:

   `PYTHONPATH=src python3 -m py_compile research/tatqa_wp0_2026/wp1/checker_v2.py research/tatqa_wp0_2026/wp1/s0_run_fixtures_v2.py research/tatqa_wp0_2026/wp2/check_pilot_eligibility.py`

4. Documentation lint:

   `python3 scripts/docs_lint.py --json /tmp/docs_lint_report.json`

   Result: `PASS (0 fail / 14 warn)`. The warnings concern unrelated pre-existing documents or registry entries.

## 4. Left open

- The split remains DRAFT and unchanged. The reserve replacement is a recommendation only; applying it requires a separately authorized split or freeze action.
- The 18 origins excluded by generic currency are not assigned replacements.
- Option A identity remains the default for `thousand`, `million`, and `billion`; no Option B scale assignment was created.
- `gold_delta_source_unit` remains a frozen JSON name with documented numeric semantic alias; it is never parsed as a unit.
- Item freeze remains S7. No S4+, actor, pilot, training, or runtime action occurred.
- No git add, commit, push, or other git operation was performed.
