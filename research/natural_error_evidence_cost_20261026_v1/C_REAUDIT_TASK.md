# Loop C Task: Corrected Candidate Qualification Re-Audit

Task ID: `natural-error-cost-reaudit-c-20261026`

Goal ID: `NATURAL_ERROR_EVIDENCE_COST_20261026`

Role: C independent audit. File ownership:

- `research/natural_error_evidence_cost_20261026_v1/audits/C_REAUDIT.md`
- `research/natural_error_evidence_cost_20261026_v1/audits/TASK_RESULT_C_REAUDIT.json`

Audit `a_remediate/` against frozen raw and the prior `a_prepare/` identity.
Independently execute `P2_RECOVERY_RECOMPUTE.py` or reimplement its checks;
do not accept aggregate numbers without row-level reproduction.

Verify:

1. P1 now separates 4 natural model errors from 1 reference defect and uses
   one deployable gold-free rule policy with `4/5` overall / `4/4` genuine
   error replay. Scoring identity is explicit.
2. P2 source-requirement, scale-source, semantic-potential, ranking, neighbor,
   stop-rule and character-volume calculations are reproducible from the
   pinned 507-question source without gold leakage into action selection.
3. The answer-matching rule and pre-registration receipt were frozen before
   any generation; no generation occurred in remediation.
4. The frontiers and margin/budget screen are correct at row level. Determine
   whether a restricted challenger passes both conditions.
5. Exposure/source clusters and selected examples remain accurate.
6. No model, judge, training, production or confirmation call occurred.

Return `ACCEPTED`, `CONDITIONAL` or `REJECTED`, exact blockers and a primary
recommendation for D. Do not modify A artifacts. Final response must be
compact JSON.
