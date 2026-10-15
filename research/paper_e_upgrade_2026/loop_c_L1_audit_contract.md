# Loop C task contract - pe-l1-audit

ACK FIRST LINE: your first reply must begin with `ACK pe-l1-audit: Loop C independent auditor, Layer-1 probe`.

## Role
You are **Loop C (independent auditor)**. You are **read-only**. You do NOT modify Loop A outputs and you do NOT trust Loop A's prose or commit messages. Verify with your own commands.

## Goal
Independently audit the Layer-1 feasibility probe (`pe-l1-feas`). Answer: is the "independent task-level gold" real, or is it circular (the checker's opinion restated)? Is the 3-way triage defensible?

## Data source (whitelist - read these, do not wander the repo)
- Loop A run dir: `research/paper_e_upgrade_2026/runs/L1/<run_id>/` (L1_feasibility.json, L1_feasibility_report.md, receipt.json)
- The frozen artifacts Loop A cited (verify their hashes against the run's input_hashes): `docs/experiments/2026-08-18_drift_injection_v0.md`, `docs/research/stage_e_118_quantification_v1.md`, `scripts/research/drift_inject.py`, `paper/method_theory_materials_v1.md`.
- You may read the frozen manuscript only to check the frozen numbers are unchanged (do NOT edit it).

## Method (bash-first)
1. Re-hash the cited frozen artifacts yourself; compare to Loop A `input_hashes`. Any mismatch = FAIL.
2. Parse `L1_feasibility.json`; confirm the schema and that counts equal the case list.
3. Independently re-judge a subset of at least 6 cases (must include every family present, including OCR-like). You re-derive the task_question and the verdict from table content + task definition. You must NOT simply re-read Loop A's verdict before deciding.
4. Non-circularity check: did Loop A's verdict depend on any checkpoint/matcher/judge output? Look for `used_checker_output:true`, or evidence locators that point at checker outputs, or wording that restates a matcher label. Flag any.
5. Boundary check: are TASK_CHANGING_ERROR and LEGITIMATE_CHANGE separated by a *task-defined* criterion, or by an arbitrary one? Is INSUFFICIENT_EVIDENCE used honestly?
6. Confirm no frozen number changed (spot-check the manuscript's headline numbers are the frozen ones).

## Verdict
Return exactly one of PASS / CONDITIONAL / FAIL, with:
- strongest counter-argument to Loop A's `constructible` value,
- concrete list of any circular or unsupported cases,
- what would have to change to reach PASS.

## Forbidden
NO edits anywhere; NO git write; NO model/network/training calls; do not write outside your own review file. Write your review to `research/paper_e_upgrade_2026/reviews/pe-l1-audit/<run_id>_REVIEW.md` (create dirs as needed).

## Final reply format
End with: VERDICT: <PASS|CONDITIONAL|FAIL> / REVIEW_PATH: <abs path> / CIRCULAR_CASES: <n> / NUMBERS_UNCHANGED: yes|no.
