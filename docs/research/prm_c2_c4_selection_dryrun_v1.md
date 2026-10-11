# PRM800K C2/C4 Selection Dry-Run v1

> Status: `VALIDATED_NON_TRAINING` | Training runs: `0` | Scope: non-commercial academic non-training reference contract

## 1. Arms

| Arm | Rule | Eligible rows | Selected rows |
|---|---|---:|---:|
| C2-reference | official grading.grader.grade_answer terminal correctness == True | 2762 | 659 |
| C4-reference primary | every selected-path step rating is observed and strictly positive | 602 | 451 |
| C4-reference sensitivity | at least one observed selected-path rating and all observed ratings are non-negative | 2524 | 2494 |

Data licence remains `LICENCE_PENDING`; repository code licence is MIT.

## 2. Overlap and disagreement

- C2 and strict C4 overlap: `397`
- C2 only: `262`
- C4 only: `54`
- Neither: `2049`
- Terminal correct but selected process contains a negative: `1`
- Terminal incorrect but partial process is locally all-positive: `1336`
- Terminal incorrect but complete process is all-positive: `54`
- Terminal incorrect but known process has no negative: `1851`

`FACT`: both requested disagreement directions exist in the released phase2-test payload. Process labels therefore contain information not reducible to terminal correctness for this reference contract.

## 3. Problem groups and matching

- Derived problem groups: `458`
- Groups with C2: `296`
- Groups with strict C4: `232`
- Groups with both: `217`
- Deterministically matched pairs: `407`
- Unmatched C2 / C4: `252` / `44`
- Step-count absolute difference: `{'mean': 0.9828009828009828, 'median': 0.0, 'max_abs': 21.0}`
- Process-character absolute difference: `{'mean': 95.93857493857494, 'median': 0.0, 'max_abs': 1950.0}`
- Whitespace-token absolute difference: `{'mean': 18.41031941031941, 'median': 0.0, 'max_abs': 357.0}`
- Native token count: `NOT_AVAILABLE`
- Token matching: `PROXY_ONLY_FEASIBLE_NOT_NATIVE_TOKEN_MATCHED`

## 4. Missing labels and leakage

- Rows with any missing selected rating: `2160`
- Rows without any selected rating: `238`
- Complete selected-rating rows: `602`
- Strict positive rows lost only because labels are missing/partial: `1438`
- Leakage audit: `LOW_FOR_DRYRUN; training split/leakage gates remain open`

## 5. Boundary

This dry-run validates dataset -> arm selection -> problem/token-proxy matching -> accounting only. It does not train, reproduce the PRM800K paper result, establish C4 superiority, or authorize formal Stage D training.

PRM_C2_C4_REFERENCE_STATUS: VALIDATED_NON_TRAINING
