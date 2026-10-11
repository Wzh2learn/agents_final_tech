# PR-03 v3 Result and Closeout v1

> date: 2026-10-11 | experiment: PR-EXP-03 (v3) | role: INTERVENTION_REPAIR | prereg sha256: 4c632300a588e2b20d05a66ee0d5b104490313959c8c12a14c94bf316f658445
> pipeline: implementation -> EXECUTION_PREFLIGHT -> (Loop C pre-result audit) -> formal run -> (Loop C post-result audit)

## 1. Preflight
`EXECUTION_PREFLIGHT_PASS` (10/10). Receipt: research/positive_repair_20261011/runs_local_mirror/PR-EXP-03-v3/execution_preflight_receipt.json. (Note: the preflight's check 9 was function-level, which did not catch the frozen implementation's runtime shadowing bug; see 3.1.)

## 2. Formal run: gate PASS; effect measurement entered; frozen pipeline completed only at the point-estimate level
- Generator: p1_run1.jsonl and p1_run2.jsonl are byte-size identical to the round-1 files (2,735,095 bytes); the generator is unchanged.
- Gate (v3 non-degeneracy): PASS (oracle fires on P1; A0/A1 structural false positives 0; differs from field-hit on P1).
- Coverage: new oracle 1973/2431 = 0.8116; standalone field-hit 0/2431; v1 alias 0/2431; delta = 0.8116 (coverage-bootstrap CI lower 0.7960 > 0).
- A0 false positives 0; A1 false positives 0; A3 (M-carrier) fires 72/72.
- Diagnosability (mixed population): stage macro-F1 new 0.2243 vs alias 0.0048 (delta +0.2194); family macro-F1 new 0.0048 vs alias 0.2000 (delta -0.1952). diag_delta = min = **-0.1952**.
- Frozen outcome rule (point estimates): diag_delta < -0.02 -> **NEGATIVE**.

## 3. Defects found in the frozen (v2) implementation lineage
3.1 Non-executable as delivered. The frozen v2 file (research/positive_repair_20261011/runs/PR-EXP-03/experiment.py, sha256 d75afca6...) contains `a1_table = a1_table(row["baseline"], uid)` at line 480, a variable-shadowing bug that makes `evaluate` raise UnboundLocalError. v3 renames the local to `a1_tbl` (pure implementation repair, no semantics change).
3.2 Diagnostic bootstrap computationally infeasible. `predict_loco` is O(groups^2) (one leave-one-group-out pass per group; ~2500 singleton groups). `diag_bootstrap` runs it 2 x 10,000 times per metric, i.e. tens of thousands of O(groups^2) passes; the run exceeded 30 minutes at 100% CPU and was stopped. The round-1 recovery receipt recorded runtime_seconds = 275, which is not attainable by this code, so the round-1 metrics.json is NOT attributable to the delivered frozen implementation (a provenance mismatch).
3.3 Degenerate baseline. `field_hit` compares a table's header tokens against the set of those same tokens, so it returns 1.0 for every non-empty header (constant probe = 1.0). The standalone field-hit response is therefore 0 on every case, and the headline coverage delta of 0.81 is measured against a detector that never fires.
3.4 A3 arm blocks POSITIVE. `a3_fp = sum(new) over the 72 M carriers = 72`, but the frozen POSITIVE rule requires a3_fp == 0. As written, POSITIVE cannot be reached.

## 4. Interpretation
- The repair is NOT supported. The structural oracle improves stage identification (+0.22) but regresses family diagnosability (-0.195), so the combined primary metric (min of the two deltas) is negative; the frozen rule returns NEGATIVE.
- The headline coverage delta is not a genuine repair effect: the population is defined as order-changing topology transpositions, the oracle is an order-sensitive signature (near-definitional), and the comparison baseline is degenerate.

## 5. Verdict
- Loop D self-audit (see caveat in 7): PR-03 v3 = **NEGATIVE**; genuine intervention repair NOT supported. Recommendation: do NOT add PR-03 to the SANER manuscript.
- The frozen formal pipeline could not be completed end to end (3.1, 3.2). PR-03 did ENTER effect measurement (gate PASS; primaries computed), so this is not a NOT_EVALUABLE_FINAL stop under the narrow schema/gate/provenance/undefined-domain trigger; the branch is instead concluded as NEGATIVE.

## 6. Registry disposition
- PR-EXP-03 (round 1): INVALID gate provenance / scientific NOT_EVALUABLE (unchanged).
- PR-EXP-03 v3: result_class = NEGATIVE; effect = diag_delta -0.1952 (point estimate); cost = 0 model/judge/network calls; genuine_repair_positive = false; manuscript_role = decline-cite.
- No synthesis gate contribution (0 genuine repair positives).

## 7. Caveats
- Independence: the Loop C pre-result audit could not be delivered by a fresh-context agent this session (the subagent harness returned no task to the spawned auditor), so sections 3-5 are a Loop D SELF-AUDIT, not an independent Loop C verdict. A true Loop C pass is still required to certify.
- The outcome is a point-estimate determination required by the frozen rule; the 10,000-replicate diagnostic bootstrap CI was not produced (3.2).