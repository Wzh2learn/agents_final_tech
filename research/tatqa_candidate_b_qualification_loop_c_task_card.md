# Candidate B Independent Review - Loop C

Task ID: `tatqa-candidate-b-qualification-c-20261019`

Role: Loop C independent scientific and software review

Status: `REVIEW_REQUESTED`

## Review object

Loop A task `tatqa-candidate-b-qualification-a-20261019` reported:

`CANDIDATE_B_QUALIFIED_OFFLINE`

with 8 development clusters, 8 future-validation clusters, 32 deterministic-reference tasks, 0 human-adjudication items and 0 online requests.

## Evidence whitelist

- `research/tatqa_candidate_b_qualification_loop_a_task_card.md`
- `research/tatqa_candidate_b_qualification_v1/SOURCE_EXPOSURE_QUALIFICATION.json`
- `research/tatqa_candidate_b_qualification_v1/CANDIDATE_B_TASKS_DRAFT.json`
- `research/tatqa_candidate_b_qualification_v1/HIDDEN_REFERENCE_MANIFEST.json`
- `research/tatqa_candidate_b_qualification_v1/candidate_b_reference_checker_v1.py`
- `research/tatqa_candidate_b_qualification_v1/tests/test_candidate_b_reference_checker_v1.py`
- `research/tatqa_candidate_b_qualification_v1/QUALIFICATION_SUMMARY.json`
- `research/tatqa_candidate_b_qualification_v1/LOOP_A_RETURN.md`
- `research/tatqa_candidate_b_qualification_v1/candidate_b_qualification_receipt.json`
- the reused source/cluster/exposure artifacts named by `SOURCE_EXPOSURE_QUALIFICATION.json`
- `research/paper_e_contribution_reassessment_v1/REUSE_TASK_REDESIGN.md`
- `docs/archive/2026-10-19_NEXT_DEVELOPMENT_RUN_CARD_DRAFT.md`

Do not inspect non-whitelisted model outputs or modify files.

## Required checks

1. Verify raw source hashes and all reused evidence hashes.
2. Independently reconcile source-cluster counts and development/future overlap.
3. Verify the selection rule is label-blind, source-structure-only and does not use model errors or expected headroom.
4. Verify 8+8 clusters and 16+16 tasks exactly.
5. Verify actor-facing tasks expose no hidden coordinates, references or source-cluster IDs.
6. Recompute all 32 hidden references from frozen source coordinates.
7. Inspect reference checker and tests for silent defaults, denominator shrinkage and semantic over-claiming.
8. Determine whether zero `REQUIRES_HUMAN_SEMANTIC_ADJUDICATION` is justified or merely an AI labeling shortcut.
9. Verify no online/model/judge/training/service calls occurred.
10. Decide whether `CANDIDATE_B_QUALIFIED_OFFLINE` is correct and whether any condition remains before a future online run.

## Output contract

Return exactly one JSON object with no Markdown fences:

{
  "review_identity": "LOOP_C_TATQA_CANDIDATE_B_INDEPENDENT_REVIEW_NOT_HUMAN_GOLD",
  "verdict": "ACCEPTED | CONDITIONAL | REJECTED",
  "disposition": "QUALIFIED_OFFLINE | CONDITIONAL | STOP",
  "checks": ["actual command and result"],
  "blocking_findings": [{"id": "B1", "finding": "...", "impact": "...", "required_fix": "..."}],
  "non_blocking_findings": [{"id": "N1", "finding": "..."}],
  "cluster_counts": {"development": 0, "future": 0, "overlap": 0},
  "task_counts": {"development": 0, "future": 0, "reference_valid": 0, "human_adjudication_required": 0},
  "residual_disagreements": ["..."],
  "unverified_or_excluded": ["..."]
}

This is AI independent review only, not human semantic gold, blind review, advisor signature or online authorization.
