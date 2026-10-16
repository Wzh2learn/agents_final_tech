# Loop D Adversarial Self-Review v1 (NOT independent)

> Substitute for the failed independent delegation (see REVIEW_STATUS_v1.md). Machine record:
> `LOOP_D_ADVERSARIAL_SELF_REVIEW_v1.json` (16/16 checks pass, issues: none).

## Scope and checks (falsify-claims pass)

A. Scorer fixes
- Re-ran `scorer_v2/regression/tq4_regression_run.py` live: 18/18 pass; verified exactly 8 v1-vs-v2 status flips
  covering percent false-reject/false-accept (R1a/R1b), multi-number cherry-pick (R2), list superset/subset/reorder
  (R3), and no-guessing (R4/R5). Correct samples unchanged.

B. Old-output rescore
- Verified all 12 rescore rows against the raw run files (answers byte-consistent); counts = 12/12 MATCH both
  versions, changed = 0; v2 legality view recomputed: 12 illegal, 22 kind_invalid (1 entry x 2 Q02 items + 2 entries x 10).

C. Candidate freeze
- 12 candidates; candidates_file sha256 matches the log; matrix exactly 3 tasks x {correct, incorrect} x {legal, illegal};
  legality RE-COMPUTED with a fresh call for all 12 and matches labels; incorrect-answer constructions match the spec
  (Q03-C3 = -14054; Q02-C3 = two-item subset; Q04-C3 = 3).

D. Natural freeze
- N1-N4 = one per stratum S1-S4; inputs byte-match the frozen corpora (original vs tatqa_tables; perturbed vs
  injected_tables); scoring unit_kind follows the frozen '% rule' (N1/N3 percent; N2/N4 plain); selection-log corpus
  hashes recomputed and match disk.

E. Run card v2
- Budget arithmetic 12+24=36, retries <= 4, cap 40 present; C label verbatim "同模型、独立上下文、可见候选答案";
  authorization items state no reuse of the TQ-3 authorization.

## Limitations

- This is a self-review by the package author (Loop D); it is deliberately recorded as NON-INDEPENDENT.
- The independence item remains OPEN; no content change was made or needed as a result of these checks.
