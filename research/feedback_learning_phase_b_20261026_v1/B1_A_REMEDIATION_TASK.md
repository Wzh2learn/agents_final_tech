# Loop A Task: B1 Remediation

Task ID: `phaseb-b1-remediation-a-20261026`

Goal ID: `FEEDBACK_LEARNING_PHASE_B_20261026`

Authority: commit `caa18102bdbbcfe99a889bcf82a125dcc20fdcca`, Git blob
`c7053b678ce4c67f38656f73932991632107b4fe`, GB10 LF SHA-256
`3ed5e1fc38c214c0620941903dcf5d4748ca9441edd651ecac2c78edac6db2d7`.

Role: A-EXP. Modify only A-owned B1 outputs and code. Close exactly the
conditions in `B1_D_REMEDIATION_GATE.md`; do not train or generate model
outputs.

Required updates:

- Error-type taxonomy with visible-evidence tests and correction operators.
- Unit corrections all `UNRESOLVED`; no unit edits in R/E or legal patches.
- Visible-only allowed units; reference-only edit instructions; R/E feedback
  content diff per trajectory.
- Structural target identity separated from semantic legal-equivalence
  acceptance.
- Proposed exact 12-family B2 development panel and its originally-correct
  family denominator from the 72 B1 trajectories.
- Refresh hashes/receipts and run deterministic tests.

Outputs:

- Updated B1 manifests, trajectories, patch contract/applier/tests and report.
- `B1_AUTHORITY_BINDING_CORRECTION.json`
- `B2_DEVELOPMENT_PANEL_DRAFT.json`
- `B1_REMEDIATION_RESULT_A.json`

Final response: compact JSON with `status`, `conditions`, `outputs`, `tests`,
`panel`, `risks`, `next_gate`.
