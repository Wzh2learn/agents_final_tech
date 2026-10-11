ROLE: Loop C / GB10 independent re-audit of targeted repairs
RESEARCH QUESTION:
Did the targeted Loop A repair close the blocking Figure 3, gate-snapshot, and numeric-token-identity findings without changing frozen scientific evidence or overstating the remaining limitations?

INPUTS:
- /home/testuser/wzh/loop_runs/paper-evidence-strengthening-c-20261010/c.log as the original CONDITIONAL findings F2-F8
- /home/testuser/wzh/projects/agents_final_tech/research/stage_e_multileaf_20261010/stage_e_evidence_strengthening_repair_receipt.json
- /home/testuser/wzh/projects/agents_final_tech/research/stage_e_multileaf_20261010/stage_e_evidence_strengthening_repair_tests.log
- changed outputs listed in that receipt
- frozen ablation, causal-join audit and candidate-manifest hashes recorded in the receipt

ALLOWED ACTIONS:
- Read-only inspection of source and output artifacts.
- Independently recompute hashes, metric/baseline wording checks and status-matrix consistency.
- Run the three focused test files and deterministic validators if permission permits.
- Compare F2-F8 against the repair evidence.
- Return a fresh audit report in the task output; write `docs/experiments/2026-10-10_loop_c_evidence_strengthening_repair_audit.md` only if the environment permits.

FORBIDDEN ACTIONS:
- Modify any artifact, code, paper, contract, figure or receipt.
- Run M/R/N, formal FinQA, PRM training or any model call.
- Expand into unrelated repository review.
- Treat the observation-reproduction scorer as semantic process correctness.
- Invent an explanation for the 627-versus-594 PRM accounting gap.

OUTPUT:
- Independence declaration.
- Finding-by-finding verdict for F2-F8: CLOSED / PARTIAL / OPEN / NOT_YET_RESOLVED, with exact evidence.
- Verification of frozen hashes and the `11 passed / 0 failed` test claim, or a declared verification gap.
- `VERDICT: ACCEPTED`, `CONDITIONAL`, or `REJECTED`.
- Strongest remaining reviewer attacks.

STOP CONDITIONS:
- If frozen hashes changed, report `FROZEN_ARTIFACT_CORRUPTION` and reject.
- If Figure 3 still mixes metric-specific baselines, keep F2 open.
- If gate status remains ambiguous or `SCORER_GO` is absent from the canonical table, keep F3 open.
- If selection and causal token identity still differ, keep F4 open.
- If tests cannot be run, record `TEST_STATUS_NOT_INDEPENDENTLY_VERIFIED` rather than inferring pass.

EVIDENCE CLASS:
PRIMARY = F2 claim/metric boundary.
SECONDARY = F3 gate reconciliation.
ENGINEERING = F4 token identity and focused tests.
NEGATIVE = F6/F7/F8 residual limitations.
EXPLORATORY = reviewer-attack prioritization.
