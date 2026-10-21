# Research Entry

Status: `CURRENT_SINGLE_ENTRY`
Updated: 2026-10-20

This file is the only current research entry. `docs/INDEX.md` navigates to it;
`memory/STATE.md` carries the short current-state summary; detailed reports are
evidence, not competing entry points.

## Current Rulings

- Paper E: `NARROW_AND_CONTINUE` as a bounded two-case measurement audit.
- FinRank history/H: `STOP_ON_CURRENT_PANEL`. The corrected baseline leaves one
  sufficient-evidence abstention and one serialization failure at outcome
  level. Plan recall is derived at `7/7`, but plan precision is `5/7`; no
  executed task-matched correction histories exist.
- MA-CERD current interpretation, corrected 2026-10-21: the existing resource
  baseline is `resource_ids` membership localization, not dependency-edge
  propagation. `TOOL_FIRST_WITH_SELECTIVE_ESCALATION` is a development
  hypothesis. Handling `0.012` is complete-set exact matching; admissibility
  and actual action selection are separate targets. See
  [`CORRECTIONS_20261021.md`](../../research/ma_cerd_independent_v1/CORRECTIONS_20261021.md).
- Shared research ledger: `747/747` requests and `1,564,176/2,000,000`
  accounting tokens, recomputed from all 747 request records. The ledger has
  746 `OK` records and one retained `FAILED/request_already_exists` event with
  conservative 10,240-token accounting. Judge, training, paid research API and
  production Memory writes are zero. The old ledger remains unchanged at
  `313/316` requests and `324,086/2,750,000` tokens.
- Current merged return:
  [`MERGED_GOAL_RETURN.md`](../../research/research_direction_sprint_20261020_v1/execution_v2/MERGED_GOAL_RETURN.md).
- Independent review:
  [`INDEPENDENT_SCIENCE_REVIEW.md`](../../research/research_direction_sprint_20261020_v1/execution_v2/INDEPENDENT_SCIENCE_REVIEW.md).
- GB10 authoritative Loop A/C evidence:
  [`GB10_LOOP_A_RETURN.md`](../../research/research_direction_sprint_20261020_v1/execution_v2/GB10_LOOP_A_RETURN.md),
  [`GB10_LOOP_A_VERIFICATION.json`](../../research/research_direction_sprint_20261020_v1/execution_v2/GB10_LOOP_A_VERIFICATION.json),
  and
  [`GB10_LOOP_C_REVIEW.md`](../../research/research_direction_sprint_20261020_v1/execution_v2/GB10_LOOP_C_REVIEW.md).
- Research calls follow the owner-adopted Goal and its shared budget; this
  navigation page does not create additional funds or execution claims.
- `PAPER_E_EXTERNAL_AUDIT_AND_EXPERIENCE_SCOPE_V1` completed with two
  conditional rulings: Paper E continues as a bounded two-case audit after the
  FinRank provenance correction. The subsequent owner-requested AI semantic
  review retains 13 development references, requires revision/review for 9,
  and excludes 2; human confirmation remains false. The next engineering step
  is tool-contract implementation, not blanket human adjudication of all 24.
  This update does not open online execution or independent validation. See
  [`GOAL_RETURN.md`](../../research/research_direction_sprint_20261020_v1/execution_v1/GOAL_RETURN.md).
- Latest reference review and continuation Goal:
  [`ADJUDICATION_AND_NEXT_GOAL.md`](../../research/research_direction_sprint_20261020_v1/execution_v1/ai_semantic_adjudication_v1/ADJUDICATION_AND_NEXT_GOAL.md),
  with machine-readable per-task evidence in
  [`ADJUDICATION.json`](../../research/research_direction_sprint_20261020_v1/execution_v1/ai_semantic_adjudication_v1/ADJUDICATION.json).
- Latest owner instruction expands exploratory autonomy beyond that candidate:
  [`OPEN_RESEARCH_CHARTER.md`](../../research/research_direction_sprint_20261020_v1/OPEN_RESEARCH_CHARTER.md).
  Loop D may select, prototype, probe and change exploratory directions within
  the existing shared budget; seven-task baseline completion is not a gate for
  all discovery. Proposed mechanisms and new literature are not results.

## MA-CERD Independent Probe

- Source and offline baselines:
  [`RESEARCH_RETURN.md`](../../research/ma_cerd_independent_v1/RESEARCH_RETURN.md)
- Transparent adjudicator and resource-membership baseline:
  [`ADJUDICATOR_RETURN.md`](../../research/ma_cerd_independent_v1/ADJUDICATOR_RETURN.md)
- Selective routing and error strata:
  [`SELECTIVE_ROUTING_RETURN.md`](../../research/ma_cerd_independent_v1/SELECTIVE_ROUTING_RETURN.md)
- Full uncertainty-queue model probe:
  [`UNCERTAINTY_ADJUDICATION_RETURN.md`](../../research/ma_cerd_independent_v1/UNCERTAINTY_ADJUDICATION_RETURN.md)
- Experiment autopsy and next-action ruling:
  [`EXPERIMENT_AUTOPSY.md`](../../research/ma_cerd_independent_v1/EXPERIMENT_AUTOPSY.md)

The full-release transparent summary is relation `0.881`, handling `0.839`,
impact F1 `0.676` and preserved F1 `0.648`; it is not a pure held-out result.
The original test summary is relation `0.830`, handling `0.835`, impact F1
`0.5856` and preserved F1 `0.5280`. On the 250-record uncertainty queue,
handling `0.012` is complete-set exact matching, while 241 admissible
`{defer}` subsets show that the original prompt did not make enumeration
requirements explicit. These observations motivate, but do not verify,
selective escalation.

## Paper E

- Claim/evidence matrix: `research/paper_e_contribution_reassessment_v1/PAPER_E_CLAIM_EVIDENCE.md`
- Preferred positioning: `research/paper_e_contribution_reassessment_v1/PAPER_E_POSITIONING_DRAFT.md`
- Nearest-work check: `research/paper_e_contribution_reassessment_v1/NEAREST_WORK_COMPARISON.md`
- Independent review: `research/paper_e_contribution_reassessment_v1/INDEPENDENT_REVIEW.md`
- Final reassessment record: `research/paper_e_contribution_reassessment_v1/GOAL_RETURN.md`
- Submission gate: `PAPER_E_SUBMISSION_READINESS_GATE_v1.md`

## Experience Reuse

- Decision-space diagnosis: `research/decision_space_autopsy_v1/DECISION_SPACE_AUTOPSY.md`
- Consolidated exploratory result: `research/decision_space_autopsy_v1/exploratory_b0_v1/SAME_NUMBER_ROLE_EXPLORATION_SUMMARY.md`
- Final history collection receipt: `research/decision_space_autopsy_v1/exploratory_b0_v1/ROLE_HISTORY_COLLECTION_RETURN.md`
- Failure-history qualification: `research/decision_space_autopsy_v1/exploratory_b0_v1/FAILURE_HISTORY_QUALIFICATION_AUDIT.md`
- Task-reference qualification: `research/decision_space_autopsy_v1/qualification_v2/QUALIFICATION_RETURN.md`
- Design rationale: `research/paper_e_contribution_reassessment_v1/REUSE_TASK_REDESIGN.md`

## Thesis Boundaries

- Governance baseline: `THESIS_RESEARCH_GOVERNANCE_BASELINE_v1.md`
- Current scope: `THESIS_RESEARCH_ARCHITECTURE_v3.md`
- Work-package blueprint: `THESIS_EXECUTION_BLUEPRINT_v1.md`
- TAT-QA source/contract evidence: `WP0_TATQA_PACKAGE_v1.md`,
  `WP0_TATQA_QUALIFICATION_APPENDIX_v1.md`,
  `WP0_TATQA_FEEDBACK_RIGHT_CONTRACT_v1.md`

## Evidence Policy

- Frozen raw responses, ledgers, manifests and independent checks remain in
  their research artifact directories.
- Per-experiment return files are point-in-time receipts. Aggregate request
  and token accounting comes from
  [`RESEARCH_GENERATION_LEDGER.json`](../../research/research_direction_sprint_20261020_v1/execution_v1/RESEARCH_GENERATION_LEDGER.json),
  recomputed from its 747 request records; its original top-level status string
  is historical and is not the current research disposition.
- Dated corrections supersede current explanatory wording but do not rewrite
  original reports or scores:
  [`CORRECTIONS_20261021.md`](../../research/ma_cerd_independent_v1/CORRECTIONS_20261021.md).
- Archived handoffs and superseded reports remain under `docs/archive/`.
- A result document may state its evidence boundary, but it must link here for
  current routing instead of claiming a second project entry.
- AI review is not human gold, blind review or advisor signature.

## Next Execution Step

Integrate unique evidence across local and GB10, select one canonical Paper E
manuscript, and run bounded adaptive-revalidation probes for action-loss
active checking and local revalidation. Distinguish authored DEV_ONLY
fixtures from model observations and new-family confirmation. Do not collect
FinRank history, reopen stopped panels, or strengthen Paper E beyond its
bounded two-case measurement-audit claim.
