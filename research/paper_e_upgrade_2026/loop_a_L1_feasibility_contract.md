# Loop A task contract - pe-l1-feas

ACK FIRST LINE: your first reply must begin with `ACK pe-l1-feas: Loop A executor, Layer-1 feasibility probe`, then start work.

## Role
You are **Loop A (executor)** on the GB10 repo. You run a single bounded, read-only-over-frozen-artifacts feasibility probe. You are **not** Loop D; do not re-plan the project, do not spawn sub-agents, do not touch the manuscript.

## Goal
Answer ONE question, with evidence: **can an independent task-level ground truth be constructed for header-perturbation cases in the frozen Stage E corpus, WITHOUT using the audited checkpoint/matcher outputs?**

This is the advisor-mandated "Layer 1" feasibility step for the Paper E upgrade. Do not run Layer 2/3. Do not change any experiment.

## Authorized scope
- READ everything under the repo (read-only).
- WRITE only inside a fresh run dir: `research/paper_e_upgrade_2026/runs/L1/<UTCstamp>_<uuid8>/` (create it; if the id exists pick a new one).
- Tools allowed: `bash`, `python3` (stdlib only), `git show/log/diff` (read-only, NO commit/push/config).

## Forbidden
- NO model / judge / API / network / training / GPU calls. Zero.
- NO git commit / push / checkout / reset / config.
- NO editing any existing file (manuscript, claim matrix, scope lock, frozen results, this contract).
- NO changing any frozen number (95 / 118 / 96 / 0-13 / 1.0 / 0.3333 / 0.1667 / V-D-O ...).
- NO reopening Route B / FinQA binding / PR-03 / synthesis / automatic selector.
- Do not let a checker define correctness. The task-level verdict must come from the **table content + task definition**, not from the checkpoint matchers or judges.

## Inputs to locate (read-only; verify each exists with ls/test, record sha256)
- Frozen corpus / injections: `docs/experiments/2026-08-18_drift_injection_v0.md`, `docs/research/stage_e_118_quantification_v1.md`, `docs/research/stage_e_zero_event_uncertainty_note_v1.md`
- Injector: `scripts/research/drift_inject.py`
- Frozen evaluator definition: `paper/method_theory_materials_v1.md`; Stage E multileaf results `research/stage_e_multileaf_20261010/results/multileaf_formal_results.json`
- If a canonical per-injection record (table_id, family, perturbation, checkpoint response) exists, use it; if only the generator + docs exist, reconstruct the case list deterministically from them and say so.

## Procedure (bash-first; evidence before assertion)
1. Locate + hash the frozen artifacts above; print the exact commands you ran.
2. Deterministically select 12-16 dev probe cases spanning all 6 families. MUST include the OCR-like family (the 0/13 boundary) and at least one arithmetic/numeric family. State a reproducible selection rule (e.g. sort by (family, table_id, injection_id), take first k per family) - do NOT cherry-pick to make a story.
3. For each case write BOTH:
   - `task_question`: the concrete task whose answer the perturbation could change (e.g. "does the mapped schema still recover cell (row,col) for query X?", "does the period/unit inferred from the header stay correct?"), and
   - `independent_verdict` in {TASK_CHANGING_ERROR, LEGITIMATE_CHANGE, INSUFFICIENT_EVIDENCE}, decided from table content + task definition ONLY.
4. Use INSUFFICIENT_EVIDENCE whenever the boundary needs a human decision you cannot ground. Do not guess to inflate a category.
5. Attest per case `used_checker_output: false` (if you ever peeked at a matcher/judge label, set true and say where).
6. Overall `constructible` in {YES, NO, PARTIAL} + one-paragraph justification.

## Deliverables (write ONLY in the run dir)
- `L1_feasibility.json`: top-level keys task_id, execution_status (DELIVERED|FAILED|STOPPED), constructible (YES|NO|PARTIAL), selection_rule, cases[] (each: case_id, family, table_id, perturbation, task_question, independent_verdict, evidence[], used_checker_output, ambiguity_note), counts{TASK_CHANGING_ERROR,LEGITIMATE_CHANGE,INSUFFICIENT_EVIDENCE}, criterion_dependence_attestation, input_hashes{}, unresolved[].
- `L1_feasibility_report.md`: prose - what you found, where independent gold is solid vs ambiguous, whether Layer 2 is worth attempting.
- `receipt.json`: commands run, files hashed, counts, zero-call attestation, write scope.

## Stopping conditions
Stop and record (do not improvise a fix) if: an input drifts or a hash is missing; you would need to write outside the run dir; you would need a model/network call; or you cannot construct independent gold without reading checker outputs. Report honestly as constructible NO/PARTIAL.

## Final reply format
End with a plain-text block: RESULT: <constructible> / RUN_DIR: <abs path> / COUNTS: <n,n,n> / ZERO_CALLS: yes / NEEDS_LOOP_C: yes.
