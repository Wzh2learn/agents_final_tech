# Task Contract: FinQA v2 Pre-Result Freeze - Loop A

- Task ID: `finqa-v2-preresult-freeze-a-20261010`
- Role: Loop A / GB10 primary execution
- Risk: medium
- Window: zero-endpoint, non-training
- Evidence classes: PRIMARY freeze identity; SECONDARY split/join; ENGINEERING scorer/tests; NEGATIVE blockers

## Frozen Research Question

Does the visibility-detection separation transfer to a different reasoning-oriented dataflow under an independently implemented observation scorer?

This question must not be changed to hierarchy-versus-flat superiority, localization superiority, semantic scorer superiority, or natural-failure localization.

## Premises

| ID | Premise | One-minute falsification |
|---|---|---|
| P1 | The frozen FinQA candidate manifest contains exactly 216 candidate injections in 72 report clusters, 24 clusters per E/P/N stage. | Count IDs/groups directly from `finqa_v2_candidate_sample_manifest.json`. |
| P2 | A deterministic group-disjoint train/calibration/evaluation assignment can be made without outcome or evaluator-output access. | Inspect the assignment input fields and search the assignment code for outcome/result fields. |
| P3 | The independent scorer can bind to exact clean/mutant artifacts without importing the shared fault adapter or Stage E aggregation. | Static import/function-call inspection plus focused tests. |
| P4 | Numeric-token identity can be unified across selection, resolver and causal-join paths without editing frozen evidence. | Run canonicalization tests and scoped identity search. |

Any falsified premise stops the task with an explicit blocker.

## Inputs

- `research/stage_e_multileaf_20261010/finqa_v2_candidate_sample_manifest.json`
- `research/stage_e_multileaf_20261010/finqa_v2_causal_join_audit.json`
- `research/finqa_numeric_token_canonicalization_v2.py`
- `research/finqa_evidence_argument_resolver_v2.py`
- `research/finqa_independent_observation_scorer_v2.py`
- `research/stage_e_multileaf_20261010/audit_finqa_v2_causal_join.py`
- `research/stage_e_multileaf_20261010/audit_finqa_v2_overlap_feasibility.py`
- existing FinQA source records and paired clean/mutant construction inputs already present on GB10
- focused tests under `tests/`
- current repair receipt and gate reconciliation artifacts

## Allowed Actions

1. Verify source identities, candidate IDs and existing hashes.
2. Create a new FinQA v2 freeze namespace under `research/finqa_v2_20261010/`; do not overwrite prior gate or audit artifacts.
3. Freeze exact clean/mutant sample IDs, source-record IDs, report-cluster IDs, stage keys and artifact hashes.
4. Freeze deterministic split roles and the origin/group-disjoint rule using no outcomes, labels, evaluator outputs or post-result information.
5. Bind the causal E1 resolver to exact paired artifacts and record unique/ambiguous/unresolved join status.
6. Bind the independent scorer to those exact artifacts and freeze its code, tests, decision predicate and measurement object.
7. Reconcile every live FinQA numeric-token identity path to one shared canonicalization function, preferably in a new versioned namespace while preserving old artifacts.
8. Add focused tests for split determinism, group disjointness, leakage fail-closed behavior, artifact binding and token identity.
9. Run the existing 11 focused tests and any new freeze tests; record exact commands, stdout/stderr, exit codes and hashes.
10. Create `FINQA_V2_EXECUTION_FREEZE_PACKET` and a machine-readable receipt before any formal evaluator output is materialized.
11. Record HEAD, relevant diff hash, Python/dependency versions and all input/output SHA-256 values.

## Frozen Split Contract

- Roles: `train`, `calibration`, `evaluation`.
- Primary group: `report_cluster_id`.
- Group closure: union records sharing exact normalized source identity, source hash, or duplicate record identity. All members of a connected component receive one role.
- Stage keys remain exactly `E`, `P`, `N`.
- Stage target allocation: 40% train, 20% calibration, 40% evaluation by independent groups.
- If 24 singleton groups remain per stage, exact quotas are 9 train / 5 calibration / 10 evaluation groups per stage, totaling 27 / 15 / 30 groups and 81 / 45 / 90 injections when each group has three injections.
- Deterministic ordering key: `SHA256("finqa-v2-split-v1|20261016|<stage>|<canonical_group_id>")`.
- If connected components alter the quotas, use a deterministic largest-remainder/greedy allocation minimizing stage-by-role deviation, freeze the resulting exact counts, and record every deviation.
- Any cross-stage connected component triggers `SPLIT_GROUP_COLLISION`; do not force a split.
- Assignment code must not read outcome, correctness, harmfulness, evaluator result, visibility result or detection result fields.
- Calibration may select operating thresholds only within the calibration role. Evaluation remains untouched until a later explicitly authorized formal run.

## Join Contract

- Freeze the exact clean and mutant artifact for every retained ID.
- The causal join must use the shared numeric-token canonicalization identity.
- A retained causal sample requires one unique evidence-to-argument join and a deterministic removal/replacement response under the frozen resolver.
- Ambiguous/unresolved cases are excluded before split assignment and counted explicitly.
- Preserve provenance: source file, byte offset or stable locator when available, record ID, report cluster, evidence ID/text hash, argument token, canonical token and resolver version.
- Outcome fields and gold answer fields must be absent from resolver selection and split assignment.
- Do not claim native pipeline provenance from a lexical join.

## Scorer Contract

- Measurement object: `paired_checkpoint_observation_reproduction`.
- `semantic_correctness_claim = false`.
- No import or call to the shared FinQA fault adapter, old FinQA step scorer, or Stage E aggregation.
- Label-blind: no gold answer, terminal correctness, harmfulness or stage label may enter scoring.
- Deterministic and hash-bound to exact paired artifacts, scorer source, predicate version and freeze manifest.
- Existing five features remain the observation surface unless an existing frozen contract requires otherwise.
- The scorer must fail closed on missing/ambiguous fields and report unevaluable denominators.
- Formal evaluator outputs must not be generated during this task.

## Required Outputs

1. `research/finqa_v2_20261010/FINQA_V2_EXECUTION_FREEZE_PACKET.md`
2. `research/finqa_v2_20261010/finqa_v2_execution_freeze_packet.json`
3. `research/finqa_v2_20261010/finqa_v2_frozen_sample_manifest.json`
4. `research/finqa_v2_20261010/finqa_v2_split_manifest.json`
5. `research/finqa_v2_20261010/finqa_v2_paired_artifact_manifest.json`
6. `research/finqa_v2_20261010/finqa_v2_scorer_binding_manifest.json`
7. `research/finqa_v2_20261010/finqa_v2_preresult_freeze_receipt.json`
8. exact test logs and a scoped source/diff/environment snapshot

The packet must report exact retained sample/group counts by stage and role, exclusions, join statuses, scorer independence, leakage checks and all six gate recommendations.

## Stop Conditions

- `INPUT_MISSING`: any required frozen source/artifact is absent.
- `SPLIT_GROUP_COLLISION`: one origin/source component crosses stages or cannot be assigned without leakage.
- `JOIN_NOT_IDENTIFIABLE`: exact paired artifacts or unique causal joins cannot be frozen.
- `TOKEN_IDENTITY_UNRECONCILED`: any live FinQA selection/resolution/audit path still uses a different numeric identity.
- `SCORER_NOT_INDEPENDENT`: any shared mutation/Stage E aggregation dependency or label leakage remains.
- `PRERESULT_FREEZE_VIOLATION`: any formal evaluator output predates the freeze receipt.
- `TEST_VALIDATION_FAILED`: any focused test fails.
- `OUT_OF_SCOPE`: closure would require formal FinQA execution, model calls, training, paper edits or frozen-evidence modification.

## Forbidden Actions

- Run formal FinQA v2 evaluator outputs or second-flow experiments.
- Run PRM, Agent Distillation or any model training.
- Modify frozen candidate/audit/result JSON or old D3 artifacts.
- Change sample IDs, mutation semantics, thresholds or expected checkpoints after viewing results.
- Search for a predictor/threshold that improves the existing multi-leaf result.
- Claim semantic correctness, hierarchy superiority or natural-failure localization.
- Commit, push, release data or redistribute artifacts.

## Success Exit

`FINQA_V2_EXECUTION_FREEZE_PACKET` is hash-complete, all permitted focused tests pass, all six gate recommendations are evidenced, and no formal output exists. The task then stops for Loop C independent review.
