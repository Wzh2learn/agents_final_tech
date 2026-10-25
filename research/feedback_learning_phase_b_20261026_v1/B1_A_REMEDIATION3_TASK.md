# Loop A Task: B1 Disclosure and Estimand Remediation

Task ID: `phaseb-b1-remediation3-a-20261026`

Goal ID: `FEEDBACK_LEARNING_PHASE_B_20261026`

Role: A-EXP. Modify only A-owned B1 outputs. Close H1/H2 without training or
model calls.

1. Disclose in `B1_REPORT.md` and `B1_SUPERVISION_MANIFEST.json` that the
   materialized set-binding targets for `NAT_train_bdeeb701_c6f0281e` and
   `NAT_train_b74eaf04_caa15292` are sign-reversed relative to the frozen
   reference target and do not execute to the reference answer. Include the
   per-family target forms and counts.
2. State the sole qualified estimand as `SET_BINDING_SET_ACCURACY`: correct
   visible cell set with operator, order and unit preserved. It is not answer
   correctness and must never score against the reference answer.
3. Restate `OPERAND_ORDER_SIGN_REVERSAL`: set difference can yield an eligible
   set-binding component; order-only difference has no training target and is
   `UNRESOLVED`. The phrase "between A and B" alone is not the discriminator.
4. Refresh hashes and receipts. Preserve old raw and score versions.

Write `B1_REMEDIATION3_RESULT_A.json`. Final response: compact JSON with
`status`, `disclosure`, `estimand`, `outputs`, `tests`, `next_gate`.
