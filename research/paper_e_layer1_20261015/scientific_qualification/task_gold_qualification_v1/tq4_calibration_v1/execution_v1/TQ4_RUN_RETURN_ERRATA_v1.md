# TQ4_RUN_RETURN errata v1

This errata supplements `TQ4_RUN_RETURN.md`; it does not edit or replace the original report.

1. Validity denominator: the run produced 35/36 valid outputs. B had 15/16 valid decisions (Part 1 4/4; Part 2 11/12). The sentence "B valid decision denominator = 35" is retracted. HTTP request success does not imply valid model output.
2. Matrix display: B-Q04-C2 is `invalid` because JSON parsing failed. `ledger_state=done` records ledger completion only and is not a model decision.
3. Point checks: the pre-run record is 14/14, including `material_pin_check_full`.
4. Timing: first request 2026-10-16 16:29:02 Asia/Shanghai; last response 16:32:16; elapsed time 194 seconds. The run creation time 16:28:49 is not the first-request time.
5. N1: the evidence supports "semantic disagreement between reference matching and checker verification." It does not prove the official reference wrong or the actor absolutely correct. C's decision field is `alarm`, but `contradiction_points` is empty and its reason ends with accepting language; that internal inconsistency is reported without inventing a consistent rationale.
6. Q03-C3/C4: the frozen labels and results remain unchanged. The negative-example arithmetic direction is ambiguous, so semantic qualification is NOT_ESTABLISHED and these rows are not counted as confirmed shared misses.
7. TQ-4 config provenance: the run-time config snapshot is missing. The current file mtime falls inside the run window; no evidence supports the earlier claim that only `scoring_dir` changed after execution. The hash gap remains open and is not repaired retroactively.
8. Dual-end 84-file matching: the original report had no dedicated receipt. The claim is retracted as a historical assertion; current mirror verification, if recorded separately, is a later check.
