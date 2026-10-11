# PRM800K Reference Track Audit v1

> 状态: `PRM_REFERENCE_READY` | 更新: 2026-10-10 | 取代/被取代: 补齐 official grader、missing-label、problem grouping、split 与 licence-policy qualification；只用于非商业学术 reference track，不作为本研究 novelty

## 1. Identity and licence

| Item | Status | Evidence |
|---|---|---|
| Paper | `PAPER VERIFIED` | *Let's Verify Step by Step*, arXiv `2305.20050` |
| Official repo | `REPO VERIFIED` | `https://github.com/openai/prm800k`, commit `7ecc794703b2877f63226f2477a49b34f9b25163` |
| Code licence | `REPO VERIFIED` | root MIT |
| Dataset licence | `LICENCE_PENDING` | no separate dataset licence is established by the root MIT file |
| Academic inspection/use | `AUTHORIZED` | non-commercial academic metadata/schema/small-sample/reference-contract validation |
| Redistribution / final-result training | `NOT AUTHORIZED` | waits for data-licence and formal protocol gates |

`FACT`: code licence and dataset licence are recorded separately. `LICENCE_PENDING` does not stop local non-commercial research, adapter work, preprocessing or smoke.

## 2. Released splits

Official LFS payload status:

| Split | Payload status | SHA-256 / LFS OID |
|---|---|---|
| `phase1_test.jsonl` | `DATA VERIFIED`, 106 rows | `f4b3bc5b...727d` |
| `phase2_test.jsonl` | `DATA VERIFIED`, 2,762 rows | `6b172efa...aaad` |
| `phase1_train.jsonl` | `LFS_POINTER_ONLY` | `e9da6a73...e34d` |
| `phase2_train.jsonl` | `LFS_POINTER_ONLY` | `1110237f...1089` |
| `math_splits/train.jsonl` | `LFS_POINTER_ONLY` | `90d96dae...8076` |
| `math_splits/test.jsonl` | `LFS_POINTER_ONLY` | `35dc4108...6132` |

`FACT`: README documents a nonstandard split: training expands MATH train with 4,500 MATH test problems; evaluation holds out 500 random MATH test problems. The exact train payload bodies are not locally downloaded and remain `NOT VERIFIED` at record level.

## 3. Actual schemas

Phase 2 test top fields: `labeler`, `timestamp`, `generation`, `is_quality_control_question`, `is_initial_screening_question`, `question`, `label`.

Phase 1 test additionally has a reduced question schema: `problem`, `ground_truth_answer`; it does not expose the phase-2 pre-generated solution fields.

Phase 2 question fields:

```text
problem
ground_truth_solution
ground_truth_answer
pre_generated_steps
pre_generated_answer
pre_generated_verifier_score
```

Label fields:

```text
steps
total_time
finish_reason
```

Step fields:

```text
completions
human_completion
chosen_completion
```

Completion fields:

```text
text
rating
flagged
```

`DATA VERIFIED`: selected-path rating counts in phase2 test are `-1=31`, `0=1224`, `+1=15226`. `238/2762` rows have no selected rating; `1922/2762` have at least one missing selected step rating alongside at least one observed rating. Missing ratings are excluded from selected-path denominators and never imputed.

## 4. Grouping and label semantics

- No native problem ID or problem-family field is present in the inspected schema.
- A reproducible grouping key can be derived as SHA-256 of `question.problem`.
- Phase2 test contains 458 unique problem-text hashes; every group is duplicated, with at most 8 rows per problem text.
- `rating=-1`: incorrect step; `0`: no progress but not incorrect; `+1`: good step.
- `flagged`: labeler uncertainty/unknown.
- `chosen_completion=null` denotes the human-completion path where applicable.
- `finish_reason` is `found_error`, `solution`, `bad_problem` or `give_up`.

`VALUE`: the derived problem hash is suitable for grouped splits and leakage control, but it must be labelled derived rather than native provenance.

## 5. Terminal correctness qualification

Official `grading.grader.grade_answer` was run on all 2,762 phase2-test rows after installing `pylatexenc` in an isolated external vendor directory.

| Method | Correct | Incorrect |
|---|---:|---:|
| official `grade_answer` | 659 | 2103 |
| `normalize_answer` string-equality subset | 606 | 2156 |

`FACT`: official grader and normalization subset disagree on 53 rows. The official grader is therefore the C2 terminal oracle for the reference contract; the earlier 606 count remains a subset diagnostic only.

## 6. C2/C4 reference contract

| Arm | Selection |
|---|---|
| C2-reference | terminal answer correctness from official `grade_answer` |
| C4-reference | human selected-path step labels, e.g. no negative rating or all-positive path |
| Matching | derived problem hash, solution length, answer-token count and frozen split |
| Missing labels | exclude from C4 and report the denominator; never fill |
| Primary comparison | C4-reference minus C2-reference under matched problem/origin and token budgets |
| Forbidden claim | PRM800K result is our novelty, or this audit proves C4 superiority |

## 7. Gate

`PRM_REFERENCE_READY`

This gate covers process-versus-outcome experimental-contract validation, data matching, token accounting, split/group logic and static reference smoke. It does not authorize training. A later training decision still needs the dataset-licence record, frozen student/optimizer/seed budget and formal approval.
