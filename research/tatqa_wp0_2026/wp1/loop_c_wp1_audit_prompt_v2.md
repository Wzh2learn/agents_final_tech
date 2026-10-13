# Loop C focused re-audit (v2, read-only) - WP-1c after spec revision 1.2

You are **Loop C**: an independent reviewer. READ-ONLY: do not modify files, commit, push, or call services. Verify from the artifacts themselves; do not trust summaries. If `python3` execution is denied by your permission gate, replicate statically with `grep`/`jq`/`sha256sum` and say so.

Repo root: `wzh/projects/agents_final_tech`

## Context
A first audit (`tatqa-wp1-audit-20261013`) returned CONDITIONAL and prescribed fixes. Run 3 (`tatqa-wp1c-20261013`) applied them under spec revision 1.2 (`docs/research/WP0_TATQA_ADAPTER_CHECKER_CONTRACT_v1.md` Sec.5). Verify the fixes and check for regressions.

## Checks (give file:line or hash evidence)
F1. Leak-guard needle: canonical plain-decimal form + dual-form search for `delta_source`/`delta_target`; confirm a `1300` leak would now be caught (positive-control evidence); the fixture-design precondition uses the same needle set.
F2. `hidden_gold_positive_control` obligation present and PASSing with the mandated cases (`1300`, `1300.0`, `-55`).
F3. Byte-determinism across every fixture and all four arms (expect 28 checks).
F4. Taxonomy: eight classes (incl. `wrong`) declared in spec and prereg skeleton; `wrong` exercised in the taxonomy check; `regressed` semantics; deviations note present.
F5. Receipts: `fixture_receipt` hash pinned in `WP1_RECEIPT.artifact_hashes` and recomputes; safety booleans labelled `derived` or `attested: true`; `scoring_inputs_all_synthetic` derived; canonical (`data/...`) and mirror (`research/...`) fixture receipts byte-identical.
F6. Prereg skeleton: eight-class outcomes list; PENDING items (protocol pin, item/split freeze, actor freeze, `target_unit` assignment); `spec_revision: 1.2`; hash pins refreshed.
F7. Regression of prior passes: all artifact hashes recompute; pinned inputs 60 items / 182 origins; scope checks (no model/network/services; writes confined; candidate items not scored; no commit/push by Loop A).
Note (environment fact, verify or correct): the suite uses `zip(..., strict=False)` (Python >= 3.10); the declared runtime is Python 3.12 and GB10 runs 3.12. State whether this is consistent with the contract.

## Output (stdout only)
Per item: verdict + evidence. Then exactly:
`LOOP_C_WP1_REAUDIT_ITEMS_VERDICT = PASS | CONDITIONAL | FAIL`
`LOOP_C_WP1_REAUDIT_SPEC_VERDICT = PASS | CONDITIONAL | FAIL`
`LOOP_C_WP1_REAUDIT_SCOPE_VERDICT = PASS | CONDITIONAL | FAIL`
`LOOP_C_WP1_REAUDIT_INDEPENDENT_VERDICT = PASS | CONDITIONAL | FAIL`
and one closing line naming the weakest remaining point.
