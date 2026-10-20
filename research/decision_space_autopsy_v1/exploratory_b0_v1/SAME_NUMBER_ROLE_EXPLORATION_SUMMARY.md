# Same-Number Role Exploration Summary

> Evidence summary only. Current research entry: `docs/research/README.md`.

Status: `COMPLETE_NO_UNIQUE_HISTORY_EFFECT / STOP_CURRENT_CANDIDATE`

This is the single result summary for the exploratory same-number/same-delta
role-binding work. Detailed raw requests, immutable responses, ledgers and
qualification records remain evidence and are not duplicated here.

## Result

| stage | result | interpretation |
|---|---|---|
| B0, 12 matched tasks | 6/12 success | Role binding had measurable headroom. |
| R, strong role rule | 8/12 success; 9/12 role decisions | A static rule explains part of the gain. |
| C, general context | 7/12 success | Extra domain context was weaker and sometimes disrupted plans. |
| Task-matched history collection | 6 tasks / 24 requests | Four first attempts recovered after plan/tool failure; no wrong-role correction. |
| H, corrected-history presentation | 6/6 on the six-task future panel | H improved plan/tool reliability and task examples. |
| K, ordinary solved examples | 6/6 on the same panel | K matched every final H decision, so ordinary few-shot content explains the observed H gain. |
| Final visible-role history collection | 5 complete tasks / 20 model requests | 5/5 first-attempt success; 0 corrections; 0 role-decision changes. |

## Why the history mechanism is not identified

1. The first collection mostly produced `PLAN_OR_TOOL_ERROR -> UNKNOWN` and then
   interface recovery. It did not show a wrong-role decision corrected by
   role-specific feedback.
2. H and K expose the same task mapping after history metadata is removed:
   `requested role != candidate role -> WRONG_ROLE`.
3. The final collection produced no failed role decisions at all. There is no
   real post-feedback action change to learn from.
4. One nominal wrong-role task was unscorable because visible row/period/unit
   roles were identical and only hidden row indices differed. It was excluded
   by deterministic qualification.

## Mechanism status

The negative-only episodic-memory proposal is `NOT_IDENTIFIABLE_WITH_REAL_HISTORY`
for the current pool. A future study would require at least two visible,
determinable wrong-role failures across two source clusters, each with:

- a real first role decision;
- successful plan/tool trace;
- independent role-specific feedback;
- a later real attempt with a recorded action change.

Generic calculator failures and ordinary solved examples cannot substitute for
that evidence.

## Accounting

- B0: 48 requests / 29,207 tokens.
- R and C: 48 requests / 32,314 tokens.
- First history and H/K comparison: 64 requests / 67,130 tokens.
- Final role-history collection: 21 requests / 13,942 tokens, including one
  connection-refused request record with zero model tokens.
- Current cumulative ledger: **313/316 requests** and
  **324,086/2,750,000 accounting tokens**.
- Training, judge, pilot and production-memory writes: **0**.

## Evidence

- `ROLE_HISTORY_COLLECTION_RETURN.md` and `ROLE_HISTORY_COLLECTION_LEDGER_V1.json`
  contain the final collection receipt and ledger.
- `FAILURE_HISTORY_QUALIFICATION_AUDIT.md` contains the failure-history gate.
- `SAME_NUMBER_ROLE_B0_LEDGER.json`, `SAME_NUMBER_ROLE_ARM_LEDGER.json` and
  `SAME_NUMBER_ROLE_HISTORY_H_K_LEDGER.json` preserve the earlier accounting.
- Archived comparison records:
  `docs/archive/2026-10-19_SAME_NUMBER_ROLE_ARM_COMPARISON.md` and
  `docs/archive/2026-10-19_SAME_NUMBER_ROLE_HISTORY_H_K_COMPARISON.md`.

## Decision

Stop the current experience-reuse candidate. This is a bounded negative result
for the fixed model, prompts, tool contract and visible role panel. It is not
evidence that historical experience is universally ineffective.
