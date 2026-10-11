# FinQA v2 Formal Experiment Task Card

- Task ID: `finqa-v2-formal-experiment-pending-user-20261010`
- Status: `SECOND_FLOW_READY_FOR_EXECUTION_NOT_EXECUTED`
- Execution authorized: `false`
- Window: zero-endpoint, non-training
- Evidence class: formal second-flow experiment after user scheduling
- Freeze namespace: `research/finqa_v2_20261010/`

## Frozen Research Question

Does the visibility-detection separation transfer to a different reasoning-oriented dataflow under an independently implemented observation scorer?

## Gate Receipt

| Gate | Status |
|---|---|
| `SOURCE_GO` | `PASS` |
| `ID_GO` | `PASS` |
| `JOIN_GO` | `PASS` |
| `SPLIT_GO` | `PASS` |
| `SCORER_GO` | `PASS` |
| `PREREG_GO` | `PASS` |

Loop C independently executed `19 passed` and reproduced split, counts, hashes and scorer independence. No mismatch was reported.

## Frozen Population

- Candidate injections: `216`
- Retained paired injections: `215`
- Excluded before split: `1` ambiguous N join
- Independent report clusters: `72`
- Train: `81 samples / 27 groups`
- Calibration: `45 samples / 15 groups`
- Evaluation: `89 samples / 30 groups`
- Stage retention: E `72`, P `72`, N `71`

## Immutable Inputs

Use only artifacts hash-bound in:

- `finqa_v2_frozen_sample_manifest.json`
- `finqa_v2_split_manifest.json`
- `finqa_v2_paired_artifact_manifest.json`
- `finqa_v2_scorer_binding_manifest.json`
- `finqa_v2_preresult_freeze_receipt.json`

Do not change sample IDs, split roles, joins, mutation operations, scorer code, observation features or thresholds.

## Measurement Contract

- Visibility: paired clean/mutant checkpoint observation response under the frozen independent scorer.
- Detection: the frozen protocol decision on the same paired artifacts.
- Outcome: terminal answer/result correctness reported separately from visibility and detection.
- Harmfulness: do not report unless an equivalence-dependent harmfulness contract is separately frozen.
- Scorer measurement object remains `paired_checkpoint_observation_reproduction`.
- `semantic_correctness_claim = false`.

## Primary Analysis

Test construct transfer, not hierarchy superiority:

1. Report visibility counts/rates with explicit denominators.
2. Report protocol detection counts/rates with explicit denominators.
3. Report the visibility-by-detection table.
4. Report `P(D=1 | V=1)` and `P(D=1 | V=0)` separately.
5. Report terminal outcome correctness separately.
6. Use report cluster as the independent unit and preserve the frozen train/calibration/evaluation roles.
7. Calibration may set any already-frozen operating point; evaluation remains sealed until final scoring.

Primary claim allowed only if the visibility and detection constructs remain empirically distinguishable on the held-out evaluation role.

## Required Controls

- Repeat all source/hash checks before execution.
- Verify zero pre-existing formal outputs.
- Use calibration only for frozen operating-point selection.
- Do not inspect evaluation results while selecting thresholds or exclusions.
- Preserve missing/unevaluable cases in explicit denominators.
- Report all null/adverse results unchanged.
- Keep multi-leaf claims outside this experiment.

## Hash-Field Guard

Two distinct hash contracts currently share the name `artifact_sha256`:

1. raw stored-pair manifest binding;
2. normalized scorer payload self-hash.

At execution time, store them under distinct names such as `manifest_artifact_sha256` and `scorer_payload_sha256`. Do not overwrite either frozen value. Any mismatch fails closed.

## Outputs

- exact command/environment receipt;
- frozen-input hash verification;
- per-sample visibility, detection and outcome rows;
- cluster-level accounting;
- visibility-by-detection table;
- conditional detection rates;
- missing/unevaluable accounting;
- uncertainty using the frozen analysis plan;
- claim-boundary report.

## Stop Conditions

- any frozen hash mismatch;
- any split/group leakage;
- any scorer dependency or label leakage;
- any attempt to alter thresholds after evaluation access;
- any formal output found before execution;
- any result requiring semantic-correctness or hierarchy-localization language.

## Forbidden Claims

- hierarchy beats flat;
- hierarchy localizes failures;
- the independent scorer is semantically better;
- FinQA validates natural-failure localization;
- Stage E multi-leaf results transfer automatically.

## Execution Boundary

This task card is generated only. Do not run it until separately scheduled and explicitly authorized.
