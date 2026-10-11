# PR-01 Semantic-Null Qualification v1 (Track P recovery, item G)

> date: 2026-10-11 | Loop D analysis over the frozen first-run artifacts | NO harmful TPR computed | no new experiment
> underlying first-run record unchanged: PR-EXP-01 = NOT_EVALUABLE (Phase 0 fail-closed)

## Question (owner-fixed)
Does there exist a set of transformations satisfying ALL of: (1) canonical task truth unchanged; (2) scored observation surface non-identity; (3) no dependence on harmful outcomes; (4) separable calibration/held-out null partition; (5) an independent semantic-preservation contract?

## Evidence used (first-run artifacts, read-only)
- `runs_local_mirror/PR-EXP-01/generator_summary.json`: 37,900 candidate applications -> 9,566 admitted; 15,995 rejected for task-truth mismatch; 12,339 candidates identity-at-rule; counts close exactly (9,566 + 15,995 + 12,339 = 37,900).
- `runs_local_mirror/PR-EXP-01/receipt.json` / `phase0_qualification.json`: harmful_side_read=false; AST generator-independence passes; admitted recomputed == observed == 9,566; panel_exact_complete_match=true; status FAIL with unverifiable_identity=true.
- `runs_local_mirror/PR-EXP-01/check_null_panel.py` source (read this round).

## Root-cause finding (this analysis; FACT + INFERENCE)
`FACT`: the checker's verdict aggregation is defective. In `check_null_panel.py`, every candidate rejected by the admission rule is appended to a list named `failures` (`kind: truth_mismatch`), and then `unverifiable_identity = bool(failures) or not ast_check.passes`, and `status = PASS iff ast AND not failures AND ...`. Therefore the 15,995 legitimate candidate-level rejections force `status=FAIL` / `unverifiable_identity=true`, even though (a) the checker independently recomputed the admitted set, (b) the recomputed set exactly equals the generator panel (`panel_exact_complete_match=true`), and (c) the AST independence check passed. `INFERENCE`: the semantic-preservation verification actually RAN and matched; only the verdict bookkeeping conflated "candidate rejected by the rule" with "admitted candidate whose identity could not be verified". The induced class (NOT_EVALUABLE) was fail-closed but triggered by this defect, not by a real identity failure.

## Five-condition answer
| Condition | Answer | Basis |
|---|---|---|
| (1) canonical task truth unchanged | YES | admitted edits require downstream task-truth hash identity (`task_truth_sha256 == source_task_truth_sha256`); rejected candidates are exactly those violating it |
| (2) scored observation surface non-identity | YES | admitted edits require raw header digest difference (`scored_surface_nonidentity: true`) |
| (3) no dependence on harmful outcomes | YES | harmful_side_read=false; generator/checker read only clean source tables + frozen exclusion map |
| (4) separable calibration/held-out null partition | YES (to be enumerated in v3) | inherited 5-fold table-UID rule (sorted(uid) index mod 5) gives disjoint folds; v3 must enumerate fold-level counts explicitly |
| (5) independent semantic-preservation contract | YES-with-defect | separate checker file + AST independence PASS + independent recompute with exact panel match; the verdict-aggregation defect must be fixed and re-confirmed |

## Qualification verdict
`PR-01_QUALIFICATION = YES_REQUIRES_CHECKER_FIX` (NOT `NOT_EVALUABLE_FINAL`).
The transformation class EXISTS and was independently recomputed; the prior stop was an engineering defect in the checker's verdict semantics.

## Required fix before any v3 execution (Loop A implementation-contract items; NO definition relaxation)
1. Separate `rejected_candidates` (candidate-level exclusions by the admission rule) from `verification_failures` (admitted candidates that fail verification). Only the latter may set `unverifiable_identity`/FAIL.
2. Keep the semantic-preservation definition and the raw-nonidentity + truth-hash-identity rule EXACTLY as frozen; no relaxation for clean support.
3. Add a pre-freeze schema-conformance assertion for every pinned field name; keep the checker independent (no generator import; AST check).
4. Re-run the qualification under the v3 prereg; require `EXECUTION_PREFLIGHT_PASS` before scoring; then the owner-ordered path applies (v3 prereg -> Loop C pre-result audit -> execute).