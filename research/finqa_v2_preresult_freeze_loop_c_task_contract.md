# Task Contract: FinQA v2 Pre-Result Freeze - Loop C

- Task ID: `finqa-v2-preresult-freeze-c-20261010`
- Role: Loop C / GB10 fresh-context independent audit
- Risk: medium
- Window: zero-endpoint, non-training
- Evidence classes: PRIMARY freeze validity; SECONDARY split/join/leakage; ENGINEERING tests/scorer; NEGATIVE blockers

## Frozen Research Question

Does the visibility-detection separation transfer to a different reasoning-oriented dataflow under an independently implemented observation scorer?

Do not substitute hierarchy-versus-flat superiority, localization superiority, semantic scorer superiority or natural-failure localization.

## Independence Order

1. Read the Loop D contract, frozen source manifests and raw FinQA artifacts.
2. Independently recompute IDs, group counts, split disjointness, hashes and leakage checks.
3. Inspect resolver/scorer source before reading Loop A conclusions.
4. Execute the explicitly authorized offline focused tests.
5. Only then read `FINQA_V2_EXECUTION_FREEZE_PACKET` and compare claims with first-hand evidence.
6. Declare any prior-conclusion ingestion.

## Inputs

- This Loop C contract.
- Frozen FinQA candidate manifest and causal join audit.
- Exact FinQA source/paired artifacts referenced by the freeze namespace.
- `research/finqa_v2_20261010/` outputs produced by Loop A.
- numeric canonicalization, resolver and independent scorer source/tests.
- relevant Git HEAD/diff/environment snapshot.

## Allowed Actions

1. Read-only inspect all freeze inputs/outputs and independently recompute SHA-256 hashes.
2. Independently verify exact sample IDs, report-cluster groups, stage counts and train/calibration/evaluation assignment.
3. Recompute group disjointness and check for duplicate normalized source/record identities crossing roles.
4. Inspect causal join provenance and verify selection uses no outcome/label/result fields.
5. Inspect scorer imports, call graph, input schema and decision predicate.
6. Execute the existing 11 focused tests exactly:
   - `tests/test_finqa_evidence_argument_resolver_v2.py`
   - `tests/test_finqa_independent_observation_scorer_v2.py`
   - `tests/test_finqa_numeric_token_canonicalization_v2.py`
7. Execute any new freeze-specific tests needed to verify split determinism, leakage fail-closed behavior and artifact binding.
8. Verify the freeze receipt predates any formal evaluator outputs and that no formal outputs were generated.
9. Return `PASS`, `CONDITIONAL`, or `FAIL` with exactly one primary blocker if not PASS.

The user explicitly authorizes these offline test commands on GB10. No model/API/database access is authorized.

## Required Checks

### Split

- exact IDs and counts match the manifest;
- all records in one origin/source component share one role;
- no cross-role duplicate source/record identity;
- deterministic assignment reproduces from the frozen seed/rule;
- no outcome/result/visibility/detection fields were read.

### Join

- exact clean/mutant artifacts are hash-bound;
- the E1 evidence-to-argument resolver uses the shared token identity;
- retained cases are unique and fail closed when evidence is absent/ambiguous;
- lexical provenance is not overstated as native pipeline provenance.

### Scorer

- measurement object is exactly `paired_checkpoint_observation_reproduction`;
- `semantic_correctness_claim = false`;
- no shared FinQA fault adapter or Stage E aggregation import/call;
- labels and outcomes are absent from scoring;
- deterministic/hash-bound behavior is tested.

### Leakage and Timing

- split/selection/scoring cannot access evaluation outcomes;
- no threshold or predictor selection uses evaluation results;
- no formal evaluator output exists before freeze;
- timestamp and hash ordering are recorded without relying only on mutable file mtimes.

## Forbidden Actions

- Modify Loop A code, manifests, receipts, frozen evidence or paper text.
- Run formal FinQA, PRM or model training.
- Use model/API/database calls.
- Repair failures inside the audit.
- Infer unexecuted tests as passing.
- Treat observation reproduction as semantic correctness.
- Expand into unrelated repository review.

## Output

Prefer `docs/experiments/2026-10-10_loop_c_finqa_v2_preresult_freeze_audit.md`; if report writing is permission-denied, return the complete report verbatim in the task log.

The report must contain:

- independence declaration;
- exact sample/group counts by stage and role;
- split/leakage verdicts;
- join verdict;
- scorer independence verdict;
- executed test commands and results, or `TEST_EXECUTION_BLOCKED`;
- freeze-before-output timing verdict;
- gate-by-gate independent recommendation;
- `VERDICT: PASS | CONDITIONAL | FAIL`;
- exactly one primary blocker if not PASS;
- strongest remaining scientific risks.

## Stop Conditions

- `FROZEN_ARTIFACT_CORRUPTION`: any frozen hash mismatch.
- `SPLIT_LEAKAGE`: any cross-role origin/source duplicate or outcome access.
- `SCORER_NOT_INDEPENDENT`: shared generator/aggregation dependency or label access.
- `TEST_EXECUTION_BLOCKED`: the 11 tests cannot actually be executed.
- `PRERESULT_FREEZE_VIOLATION`: formal output predates freeze or exists during this task.
- `IDENTITY_MISMATCH`: selection/resolver/audit numeric identities differ.

## Success Exit

Independent checks and test execution support `PASS`, or the report precisely identifies the single blocker preventing it. The audit then stops and returns to Loop D.
