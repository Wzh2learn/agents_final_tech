# Loop A Task: B1 Narrow Set-Binding Remediation

Task ID: `phaseb-b1-remediation2-a-20261026`

Goal ID: `FEEDBACK_LEARNING_PHASE_B_20261026`

Role: A-EXP. Modify only A-owned B1 outputs and code. Do not train or issue
model calls.

Close the remaining C-1 findings by narrowing the qualified mechanism to one
visible set-binding family:

1. Split every eligible correction into `set_binding_component` and
   `direction_component`. The R/E training target and E patch may contain only
   set-binding operations. Operator and subtraction-order direction are frozen
   to the O candidate or marked `UNRESOLVED`; never infer them from gold.
2. Register `VISIBLE_SET_BINDING_REBINDING` as one mechanism with two observed
   subtypes (`ROW_ROLE_MISBINDING`, `ROW_AND_PERIOD_ROLE_MISBINDING`) and record
   source-family counts separately from trajectory counts. Do not claim two
   independent mechanisms.
3. Add the pre-registered correct-preservation direction:
   preserve all unchanged references, operator, order and unit; E must not
   damage an originally correct family. Unit and direction components are not
   training targets.
4. Rebuild trajectories, manifest, patch contract, receipts, tests and
   `B2_DEVELOPMENT_PANEL_DRAFT.json`. Keep exposed-development identity and
   reference-derived supervision naming.
5. Write `B1_REMEDIATION2_RESULT_A.json` and preserve old raw/score versions.

Final response: compact JSON with `status`, `conditions`, `outputs`, `tests`,
`panel`, `scope`, `next_gate`.
