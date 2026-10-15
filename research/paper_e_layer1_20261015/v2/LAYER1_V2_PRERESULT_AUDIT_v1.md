[loop-c] start 2026-10-15T09:18:47Z
The write to `research/paper_e_layer1_20261015/v2/LAYER1_V2_PRERESULT_AUDIT_v1.md` is blocked pending your permission — that is the only write this task needs, and it's the one file the mandate authorizes. Please approve it (or re-run with write access) and I'll commit the file. Full audit content is drafted and ready; findings below.

## Evidence re-derived (not taken on trust)

- `LAYER1_ANALYSIS_PLAN_v1.md` hash `a275e55a…` **equals** the `plan_sha256` frozen inside `LAYER1_RESULTS_v1.json` → v1 plan bytes unchanged since the run.
- `case_rows` = 59, **all** `split: "dev"`; `label_counts` 12E/12H/35U = 59. The held-out block is 59 bare identifier strings with **no label field**.
- U-reason tally: 32 `source_header_empty_after_norm` + 3 `nearest_neighbour_tie`, no duplicates, no missing reasons. v2 §1's claim ("35/59 U, of which 32 from the table-wide empty-header rule") is **exact**.
- `v2/` contains only the plan + this audit prompt — **no v2 results/receipt exists**. No held-out label has been computed.

## Verdicts

| # | Item | Verdict |
|---|---|---|
| 1 | v1 preserved; `GOLD_NOT_ESTABLISHED` not rewritten/suppressed | **PASS** |
| 2 | Rule change isolated to empty-header handling | **PASS** |
| 3 | Sample genuinely held-out | **PASS** |
| 4 | Gates pre-stated, none derived from held-out outcomes | **CONDITIONAL** |
| 5 | No silent `U` relabelling; every `U` reason explicit | **CONDITIONAL** |
| 6 | No premature population/OCR/blind-spot/Layer-2 claim | **PASS** |

**VERDICT: CONDITIONAL**

## Conditions to clear before any held-out label exists

- **A — gate arity:** §4 says "`LAYER2_GO` if **all three** hold" then lists **four** conditions.
- **B — non-exhaustive decision function:** `u_rate_heldout <= 0.30` with n(H)=5 is simultaneously `GOLD_ESTABLISHED` and, via "Otherwise", `LAYER1_V2_NO_GO`. Undefined at freeze time becomes discretionary after labels exist.
- **C — loophole:** §6's do-not-tune list names `norm(.)`, split, tie policy, gates — and **omits the empty-header/candidate-set rule**, the one mechanism v2 introduces. Post-hoc tuning of it converts `U` without invalidating the run.
- **D — missing stop:** v1's RULE_AMBIGUOUS / undecidable-non-`U` stop is not carried into v2 §6.
- **E — hashes:** §6 says "any input hash mismatch → stop" but never pins the two expected digests from v1 §8.
- **F — reason codes:** v2 `U` codes are not enumerated in closed form (a target-empty case has no assigned code), so v2 counts would be uncomparable with v1.
- **G — constant provenance:** the `>= 8` floors are unexplained; the dev counterfactual already existed when the gates were written.

## Red flags checked

- Dev counterfactual cited as a v2 result — **not found** (explicitly fenced as "design input only", and its numbers match v1 results exactly).
- Threshold/rule chosen after seeing held-out labels — **not found at audit time** (no held-out labels exist); residual exposure only via the dev counterfactual, hence G.
- Missing stop / zero-call discipline — zero-call discipline **present** and receipt-enforced; stop gaps listed as C, D, E plus a missing `INPUT_MISSING`.
- Wording letting v2 replace v1 — **not found**; "Relation to v1" keeps v1 standing, outputs scoped to `v2/`.

None of A–G is evidence of post-hoc fitting — they are specification gaps that turn into discretionary choices the moment labels are read. Each fix is a clarification that must be hashed and re-frozen before the run; it does not reopen v1.
