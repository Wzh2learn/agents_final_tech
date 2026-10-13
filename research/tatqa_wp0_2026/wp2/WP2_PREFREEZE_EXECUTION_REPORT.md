# WP-2 Pre-Freeze Execution Report

> task: `tatqa-wp2-prefreeze-20261013` | date: 2026-10-13 | loop: A
> authorization: owner “wp-2 可以去做后续要做的”; executed under WP2 runbook §4 pending-decision stop policy
> boundary: S0-S3 plus S10 only; zero model calls, zero endpoint calls, zero judge calls, zero training, zero external network

## 1. Status

| Step | Status | Result |
|---|---|---|
| S0 software fix | `PASS` | Rev 1.3 append-only correction; seven existing obligations plus three unit-gate and five numeric-rendering dedicated cases PASS |
| S1 item expansion | `DRAFT_NOT_FROZEN` | 352 items / 176 eligible origins; exactly 2 items per eligible origin; all 22 draft role origins have >=2 items |
| S2 target-unit rules | `PENDING_OWNER_ADVISOR_DECISION` | Options, recommended default, five examples, and both residual fixes documented; no rule frozen |
| S3 split replay | `PASS_BYTE_IDENTICAL` | Seed and 22 role assignments exactly match the tracked dry-run receipt; old receipt not overwritten |
| S10 analysis skeleton | `PASS` | Pure-stdlib origin-level paired comparisons and cost aggregation; four synthetic fixture tests PASS |

No S4+ action occurred. No experience collection, actor selection, model/judge call, training, pilot, result read, or scientific ruling was performed.

## 2. S0 pre-freeze software correction

The implementation is additive:

- `checker_v2.py` requires `normalize_unit(answer.unit) == gold.target_unit` for both `correct` and `correct_other_form`; equivalent forms with a wrong unit become `wrong_unit`.
- `leak_guard_v2.py` generates canonical, exact, grouped, scientific, and zero-padded forms where applicable.
- `s0_run_fixtures_v2.py` runs the complete existing fixture pipeline against v2 without writing historical receipts, then runs two dedicated synthetic fixture files.
- Contract revision 1.3 is recorded in a new append file because the card forbids modifying historical material.

Command and output:

```text
PYTHONPATH=src python3 research/tatqa_wp0_2026/wp1/s0_run_fixtures_v2.py
S0_FIXTURES_PASS obligations=7 unit_gate_cases=3 numeric_rendering_cases=5
receipt=research/tatqa_wp0_2026/wp1/S0_FIX_RECEIPT.json
```

Historical preservation:

| Historical artifact | Pre-task SHA-256 | Current SHA-256 |
|---|---|---|
| `wp1/checker.py` | `c919845b051a7cfbebfdc782ba4c9dcbd99cac8b950b46f8bd908fcdc2cb12f1` | unchanged |
| `wp1/run_fixtures.py` | `215bae90a01bf8e34dc0adcc8a1f5e7a22f2c4ed29e05f3b307e1556d92dca07` | unchanged |
| `wp1/fixtures/synthetic_fixtures.json` | `acbe79d9c0c1123dcfcc4cbc764cd0bcc6a6359fad4530c814d546497f036a85` | unchanged |
| `wp1/WP1_RECEIPT.json` | `a06cf566243743cd77246d0748375460a45c172454de597f424faec827bc059b` | unchanged |
| `wp1/FIXTURE_RECEIPT.json` | `f862cc0accf37a5e9fff50469d782d21355cb3a96d46314472edd12753531903` | unchanged |
| `wp1/run_logs/tatqa-wp1c-20261013.log` | `67a86b0ee820f25352907a9d9b88856cd393bfa57fc1ad277bc5e9d3af231b46` | unchanged |

## 3. S1 candidate item expansion

`build_items_v2.py` reads the pinned origin manifest and raw TAT-QA train/dev records, selects the first two usable numeric period deltas for each eligible origin, and performs two in-memory builds before writing. The v1 candidate list and origin manifest were not changed.

Command and output:

```text
PYTHONPATH=src python3 research/tatqa_wp0_2026/wp2/build_items_v2.py
byte_identical=true
candidate_items_v2_sha256=5f61f2a476c220f4ed4c159030490c6dfaabcea9778820abc89d3bed859738aa
origins_total=182
origins_with_ge2_usable_rows=176
candidate_items=352
distinct_item_origins=176
role_origins_checked=22
role_origins_with_ge2_items=22
items_per_origin_distribution={"2": 176}
```

The output remains `DRAFT_NOT_FROZEN`. Source-unit resolution is deliberately not frozen: 312 items have null source unit, 36 currency, 2 percent, and 2 million. This is disclosed in the S2 draft and is not treated as execution readiness.

## 4. S2 target-unit rule draft

`WP2_TARGET_UNIT_RULES_DRAFT_v1.md` records:

1. conservative identity, scale-authorized conversion, and broad conversion options;
2. recommended identity default plus frozen powers-of-ten conversions;
3. percent-to-percent and explicit-currency treatment;
4. five examples;
5. `gold_delta_source_unit` as a value-name trap;
6. absent `target_unit` as identity only after normalization and explicit future recording.

Status is `PENDING_OWNER_ADVISOR_DECISION`; no item field or scientific rule was frozen.

## 5. S3 split replay

The replay independently reconstructs the tracked dry-run payload and compares bytes without calling or overwriting the historical script output.

Command and output:

```text
PYTHONPATH=src python3 research/tatqa_wp0_2026/wp2/split_rerun_v1.py
SPLIT_RERUN_BYTE_IDENTICAL origins=182 roles=22
receipt=research/tatqa_wp0_2026/wp2/SPLIT_RERUN_RECEIPT.json
```

Tracked receipt SHA-256 and replay payload SHA-256 are both `4a95fff77d77ea86a492736864149a6013a94b031115cbaf0539f3bb3457f356`.

## 6. S10 analysis skeleton

`analyze_wp2.py` is pure stdlib and accepts synthetic or later-frozen JSON. It validates episode keys, keeps UNKNOWN first-class, aggregates per-arm outcomes and costs, and emits explicit origin differences for `E-B`, `E-C`, `E-S`, and `C-B`. Bootstrap settings are deterministic and fully reported.

Commands and output:

```text
PYTHONPATH=src python3 research/tatqa_wp0_2026/wp2/test_analyze_wp2.py -v
Ran 4 tests in 0.002s
OK

PYTHONPATH=src python3 research/tatqa_wp0_2026/wp2/analyze_wp2.py \
  --input research/tatqa_wp0_2026/wp2/fixtures/synthetic_wp2_analysis.json \
  --output /tmp/wp2_analysis_fixture_output_20261013.json \
  --bootstrap-replicates 200 \
  --seed synthetic-cli
WP2_ANALYSIS_SKELETON_PASS records=16 origins=2 comparisons=4
```

Only the synthetic fixture was used. The CLI output remained outside the repository.

## 7. Additional verification

```text
python3 -m py_compile <all seven new Python files>
PY_COMPILE_PASS

python3 scripts/docs_lint.py --json /tmp/wp2_prefreeze_docs_lint_20261013.json
docs_lint: PASS (0 fail / 14 warn)
```

The 14 documentation warnings are existing debt outside this card; the report is at `/tmp/wp2_prefreeze_docs_lint_20261013.json`.

## 8. Artifact hashes

| Artifact | SHA-256 |
|---|---|
| `docs/research/WP0_TATQA_ADAPTER_CHECKER_CONTRACT_v1_REV1_3_APPEND.md` | `9eb7dda3eae6952dd97c4c32da147a4a6d89e0a5e523c128d200f77c92501db2` |
| `docs/research/WP1_PREFREEZE_FIX_NOTE_v1.md` | `998b82190ea618912ddab61a15684e4a53ccc6421c2be3960d3fc025b70c5fe5` |
| `docs/research/WP2_TARGET_UNIT_RULES_DRAFT_v1.md` | `47feef85203bcf019bbf7c66b6a603fda8673b437d904fe5c3395f64e58387ac` |
| `research/tatqa_wp0_2026/wp1/checker_v2.py` | `642c5d9cc55c12c283bc8cc1f4122de0ac8158df737102edd85258b94256a57e` |
| `research/tatqa_wp0_2026/wp1/leak_guard_v2.py` | `da9e14df5b4308b76623d59378473013f8cbb364b1ce6da10156bb9f1e50edc9` |
| `research/tatqa_wp0_2026/wp1/s0_run_fixtures_v2.py` | `1821e319d15607043d79b4c086b49010fb622fdc4a05fa54048ffbba0ca2d534` |
| `research/tatqa_wp0_2026/wp1/fixtures/s0_unit_gate_fixtures_v2.json` | `812e537c95d51e7977073d671760a11eb305592690cd88795fd3f2f2ba0d44ae` |
| `research/tatqa_wp0_2026/wp1/fixtures/s0_numeric_rendering_fixtures_v2.json` | `836eee0471eec8a6b46a55f7810f1e0728e9a57b06092f0faa945a44a5f6fa9b` |
| `research/tatqa_wp0_2026/wp1/S0_FIX_RECEIPT.json` | `1085cde79b3085eaa6963799c6c4018937c070149dbc5e619bb4cf0d39561c50` |
| `research/tatqa_wp0_2026/wp2/build_items_v2.py` | `fe9bec5e3a83a2a47f472435d64257af960678b03a33f103ca1b2657d14e9e1e` |
| `research/tatqa_wp0_2026/wp2/ITEMS_V2_RECEIPT.json` | `1f33a64ac803459b4be6a21f92a7254fa4bb44ab549cdf57f776990bb1d33817` |
| `data/research/tatqa_wp0_2026/candidate_items_v2.json` | `5f61f2a476c220f4ed4c159030490c6dfaabcea9778820abc89d3bed859738aa` |
| `research/tatqa_wp0_2026/wp2/split_rerun_v1.py` | `63ec1db29d5147ec9616c13bd4af584ac58cc643dbdc435bb474057e9ca76ce7` |
| `research/tatqa_wp0_2026/wp2/SPLIT_RERUN_RECEIPT.json` | `771f209634c8a2fb4e71734ac6a14e161260de624506dd1f9a8065fbaeafc668` |
| `research/tatqa_wp0_2026/wp2/analyze_wp2.py` | `1217cbeea2d28334b4c17e6075c17f6d01c434d098f80c5eb3267a201b5232be` |
| `research/tatqa_wp0_2026/wp2/fixtures/synthetic_wp2_analysis.json` | `0f55b6479179d6d11c2fbebfab7e7431e61176d3d75447c18c020d134998e264` |
| `research/tatqa_wp0_2026/wp2/test_analyze_wp2.py` | `98549d746f873b51765d7a2d20be5d8b2c0762a18570639aef95fa443c3ac3c9` |

## 9. Left open

1. Owner/advisor must ratify the target-unit and source-unit resolution before item freeze; the 312 null and 36 generic-currency source labels are not execution-ready.
2. Candidate v2 remains DRAFT and must receive a later near-duplicate/isolation receipt before S7.
3. The analysis skeleton's bootstrap method and seed must be frozen with the actual episode schema before any real-data run.
4. Actor revision, feedback-right blanks, MODEL_GO, budget/window, and all S4+ gates remain pending.

## 10. Skill-load execution

- `graph-loop-rules`: repository red lines; the explicit “do not touch logs” instruction overrode its generic dispatch-log append rule.
- `testing-practices`: dedicated failing behavior was added before accepting each fix path; full fixture behavior is checked contract-first.
- `verify-before-done`: fresh commands, full outputs, artifact-hash recheck, and compile checks were run before completion.
- `executing-plans`: the S0/S1/S2/S3/S10 boundary and stop conditions were kept sequential and explicit.

No unused fifth skill was loaded.

## 11. Workspace discipline

No `git add`, commit, push, log edit, credential read, production probe, or network action was performed. Existing unrelated dirty files under `logs/` were not reverted or modified by this task.
