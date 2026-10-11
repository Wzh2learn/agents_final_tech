# Task Contract: Close FinQA v2 TEST_EXECUTION_BLOCKED - Loop C

- Task ID: `finqa-v2-test-execution-c-20261010`
- Role: Loop C / GB10 fresh-context independent execution audit
- Window: zero-endpoint, non-training
- Execution environment: isolated permissive session with Python/Bash allowed; Edit/Write/Web tools denied
- Evidence class: ENGINEERING independent verification

## Sole Objective

Close `TEST_EXECUTION_BLOCKED` without redesigning FinQA v2, modifying the freeze packet, or running a formal experiment.

## Frozen Research Question

Does the visibility-detection separation transfer to a different reasoning-oriented dataflow under an independently implemented observation scorer?

## Inputs

- Frozen artifacts under `research/finqa_v2_20261010/`.
- `finqa_v2_frozen_sample_manifest.json`
- `finqa_v2_split_manifest.json`
- `finqa_v2_paired_artifact_manifest.json`
- `finqa_v2_scorer_binding_manifest.json`
- `FINQA_V2_EXECUTION_FREEZE_PACKET.md`
- `finqa_v2_preresult_freeze_receipt.json`
- numeric canonicalization, resolver, scorer and freeze-test sources.
- The original Loop A execution logs only after independent commands have run.

## Independence Requirements

1. Do not import `build_finqa_v2_execution_freeze.py` for the independent split recomputation.
2. Do not use Loop A test logs as test results.
3. First execute tests and independent calculations, record outputs/hashes, then compare with A.
4. Read the same frozen artifacts but write no repository or freeze files.
5. Use fresh one-off Python logic for split/order-key/group checks.

## Required Independent Commands

Execute and record exact commands, exit codes, stdout/stderr and SHA-256 of captured output:

1. Existing 11 focused tests:
   `PYTHONPATH=src ./venv/bin/python -m pytest tests/test_finqa_numeric_token_canonicalization_v2.py tests/test_finqa_evidence_argument_resolver_v2.py tests/test_finqa_independent_observation_scorer_v2.py -q`
2. Eight freeze tests:
   `PYTHONPATH=src ./venv/bin/python -m pytest tests/test_finqa_v2_execution_freeze.py -q`
3. Combined 19 tests:
   `PYTHONPATH=src ./venv/bin/python -m pytest tests/test_finqa_numeric_token_canonicalization_v2.py tests/test_finqa_evidence_argument_resolver_v2.py tests/test_finqa_independent_observation_scorer_v2.py tests/test_finqa_v2_execution_freeze.py -q`

## Independent Recomputation

Use fresh one-off Python through Bash to verify:

- retained and excluded counts;
- total and per-stage group counts;
- train/calibration/evaluation sample and group counts;
- every sample maps to exactly one role;
- every `report_cluster_id` and source connected component maps to exactly one role;
- no duplicate source identity crosses roles;
- `order_key` exactly equals the frozen contract hash string and ordering reproduces role assignment;
- the one excluded ambiguous N case is excluded before split;
- no cross-stage connected component.

Do not import A's builder or reuse its functions.

## Independent Scorer Verification

Verify from source and manifests:

- exact scorer source hash and paired-artifact binding hashes;
- measurement object is paired checkpoint observation reproduction;
- no semantic correctness claim;
- no gold answer, terminal correctness, harmfulness or stage label input;
- no shared FinQA fault adapter import/call;
- no Stage E aggregation import/call;
- deterministic fail-closed behavior is covered by executed tests.

## Environment Record

Record:

- `pwd`
- Git HEAD
- Python executable and version
- pytest version
- relevant environment variables `PYTHONPATH`, `PYTHONHASHSEED`, `PYTHONDONTWRITEBYTECODE`, `TMPDIR`
- hashes of the four executed test/source files and frozen manifests.

## Comparison

After independent execution:

- Compare test counts/results with A's claim of `11 + 8 = 19 passed`.
- Compare counts, role allocation and hashes with the freeze packet.
- Report each item as `MATCH`, `MISMATCH`, or `NOT_COMPARABLE`.

## Output

Return the complete audit in the task output/log. Do not write repository files.

Required verdict:

- `PASS` if all 19 tests pass independently and every recomputation matches;
- `CONDITIONAL` if tests run but some non-primary check remains unverified;
- `FAIL` on any test failure, count mismatch, split leakage, hash mismatch, scorer dependency or label leakage.

If not PASS, report exactly one primary blocker.

## Forbidden Actions

- Modify A's implementation, freeze packet, manifests, receipts or frozen evidence.
- Run formal FinQA evaluator outputs, model calls, API/database calls or training.
- Redesign split, joins, mutation rules, scorer, thresholds or research question.
- Use A's test logs as execution evidence.
- Write or publish artifacts.

## Stop Conditions

- Any of the 19 tests fails.
- Any count/hash/order_key/group-disjointness mismatch is found.
- Scorer independence or label-blindness fails.
- Formal output exists before the freeze.
- Python execution is still denied.

## Success Exit

Independent commands and recomputations match A, `SPLIT_GO` and `SCORER_GO` can be promoted to PASS, and the task stops for Loop D gate judgment.
