# Loop C Task: Candidate Qualification Pre-Audit

Task ID: `natural-error-cost-preaudit-c-20261026`

Goal ID: `NATURAL_ERROR_EVIDENCE_COST_20261026`

Role: C independent audit. File ownership:

- `research/natural_error_evidence_cost_20261026_v1/audits/C_PREAUDIT.md`
- `research/natural_error_evidence_cost_20261026_v1/audits/TASK_RESULT_C_PREAUDIT.json`

Read the current prompt, `D_STAGE_GATE.md`, frozen source/raw/references and
then A outputs. Independently recompute before accepting A labels.

Verify:

1. The five P1 candidates are natural original errors, not variants, and each
   has a complete semantic reference and legal deployment-visible decision
   space.
2. Reference/scoring defects, unobservable units and reasonable UNKNOWN are
   separated from model semantic errors.
3. Gold programs, reference row IDs, answers and hidden scales are absent from
   proposed actor inputs.
4. P2 has legally retrievable table/text evidence and a complete reference for
   the 507 table-text questions. Record-internal text-only retrieval is not
   mislabeled as report/corpus retrieval.
5. The proposed simple baselines are deployable under the same information and
   cost conditions. The answer-risk-cost non-inferiority margin and budget
   points are frozen before generation.
6. Exposure/source clusters and all selected development examples are
   correctly registered.
7. The 3-5 mechanism neighbors are materially differentiated.

Return `ACCEPTED`, `CONDITIONAL` or `REJECTED` for each candidate, identify
blocking fixes, and recommend one primary only as evidence for D. Do not
modify A artifacts. No model, judge, training, production or confirmation call.
Final response must be compact JSON.
