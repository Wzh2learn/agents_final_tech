# Loop A Assignment - TAT-QA WP-1c (final bounded fix; NO MODEL CALLS)

CARD: research/tatqa_wp0_2026/wp1/loop_a_prompt_fix2.md | dispatched 2026-10-13 by Loop D after the Loop C audit (`tatqa-wp1-audit-20261013`, CONDITIONAL).
ROLE: Loop A / GB10. Final bounded completion of WP-1 per spec revision 1.2. Nothing else. Model calls = 0.

CONTEXT (read first; binding):
- `docs/research/WP0_TATQA_ADAPTER_CHECKER_CONTRACT_v1.md` Sec.5 (revision 1.2) supersedes 1.1(b),(d), extends the taxonomy, and weakens nothing.
- Audit findings to fix: (i) needle `1300.0` vs canonical `1300` (positive-control-proven latent false-negative); (ii) the `wrong` outcome class and `regressed` semantics are undeclared; (iii) safety booleans are self-attested rather than derived; (iv) FIXTURE_RECEIPT is unpinned / canonical path unclear; (v) byte-determinism coverage was one item x one arm.
- Existing run-1/run-2 artifacts remain; extend, do not delete. Pinned inputs unchanged; re-verify hashes/counts first (same as run 2).

TASK (bounded, per revision 1.2):
F1. Hidden-gold answer-value needle: canonical plain-decimal form (strip trailing zeros; no exponent) for `delta_source`/`delta_target`; search BOTH canonical and exact `str()` forms where they differ; the fixture-design precondition (d) uses the same needle set. Never weaken.
F2. Positive control (mandatory): a self-test that injects each needle into a synthetic projection and asserts the guard fires (at minimum the `1300`/`1300.0` pair and one negative value); a silent guard fails the obligation.
F3. Byte-determinism obligation: EVERY fixture x ALL four arms (B/E/C/S).
F4. Outcome vocabulary: align to the eight classes including `wrong`; `regressed` = B-correct becoming non-correct other than `refused`/`unknown`; extend `_check_taxonomy` to exercise the new `wrong` class; document in `implementation_contract.md`.
F5. Receipts: label every safety boolean `derived` or `attested: true`; derive `scoring_inputs_all_synthetic` (record item ids at every `score_item` call site in `run_fixtures.py` and assert all are synthetic); add the `fixture_receipt` hash to `WP1_RECEIPT.artifact_hashes`; state the canonical FIXTURE_RECEIPT path (`data/...`) and that the repo mirror is byte-identical.
F6. `PREREG_DRAFT_SKELETON.md`: outcomes list = eight classes; add PENDING items: protocol pin, item/split freeze, actor freeze, `target_unit` assignment (identity-only today); add `spec_revision: 1.2`; refresh hash pins.
F7. Receipts add `spec_revision: "1.2"`; deviations may cite resolution notes (e.g., the `wrong` class blessed by rev 1.2).
F8. Re-run the full suite; on PASS write `PREFLIGHT_RECEIPT.json`, `data/research/tatqa_wp0_2026/wp1/FIXTURE_RECEIPT.json`, `WP1_RECEIPT.json` (run id `tatqa-wp1c-20261013`); update `implementation_contract.md` addendum + rehash.

SAME constraints, write paths, and forbidden list as run 2. STOP conditions unchanged: fail-closed; never adjust a test to pass.
END: final message = status + receipt paths + one-line summary.
