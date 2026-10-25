# Loop A Task: B2B Output-Budget Repair And Correct Paired Analysis

Task ID: `phaseb-b2b-output-repair-a-20261026`

Goal ID: `FEEDBACK_LEARNING_PHASE_B_20261026`

Role: A-EXP. File ownership:
`research/feedback_learning_phase_b_20261026_v1/b2b/`.

Read `B2B_D_OUTPUT_BUDGET_REPAIR_DECISION.md` and the frozen B2 protocol,
training receipts and first-run raw/logs. Use the same trained R/E adapters and
the same 12-family development panel. Do not retrain. Do not inspect or create
confirmation outputs.

Implement the bounded 72-attempt R/E regeneration with `max_new_tokens=384` and
contract-only output. Keep the visible task and information identical; only
the output-format instruction may be tightened. Preserve raw generation text,
token counts, finish reasons and failures. Use the row-level source-family
paired estimand defined in the D decision; keep all-three-variants-correct
paired completion separate.
Report syntax, patch legality, `SET_BINDING_SET_ACCURACY`, O transitions,
delivery and cost. Keep semantic-tool failures separate from candidate
semantics.

Required outputs under `b2b/`:

- `B2B_PROTOCOL_FROZEN.json`
- `B2B_GENERATION_RAW.jsonl`
- `B2B_GENERATION_RECEIPT.json`
- `B2B_DEVELOPMENT_ANALYSIS.json`
- `B2B_FAILURES.json`
- `TASK_RESULT_A_B2B.json`

Stop before generation if the parent/child adapter hashes do not match the B2
receipts, the panel hash changes, any confirmation artifact is read, or the
72/180,000 repair budget cannot be enforced. The final response must be compact
JSON and must not claim feedback-derived learning, answer correctness or
new-source confirmation.
