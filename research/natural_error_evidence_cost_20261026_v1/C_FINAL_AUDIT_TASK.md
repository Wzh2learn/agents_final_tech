# Loop C Task: Final Candidate And Closeout Audit

Task ID: `natural-error-cost-final-audit-c-20261026`

Goal ID: `NATURAL_ERROR_EVIDENCE_COST_20261026`

Role: C independent audit. File ownership:

- `research/natural_error_evidence_cost_20261026_v1/audits/C_FINAL_AUDIT.md`
- `research/natural_error_evidence_cost_20261026_v1/audits/TASK_RESULT_C_FINAL.json`

Audit `a_closeout/` against frozen raw and prior A/C identities. Independently
replay the final recovery program and answer matcher.

Verify R1-R5 closure:

1. The stale `5/5` and `229/507` claims are superseded without modifying
   `a_prepare/`.
2. The final matcher implements all declared normalization and passes the new
   self-tests. Rule and prereg receipt hashes are frozen in the correct order.
3. The prereg metric accurately describes the offline proxy and the future
   model metric separately.
4. Aggregate counts are runtime-derived and row-level results remain
   reproducible.
5. P1 example transcription has distinct visible rows and matching schemas.
6. No model, judge, training, production or confirmation call is attributable
   to this task. Disclose the independent Loop B canary separately.

Return `ACCEPTED`, `CONDITIONAL` or `REJECTED` and the final candidate
disposition. Do not modify A artifacts. Final response must be compact JSON.
