# PILOT_PREP_RETURN

> Status: `FUTURE_TASKS_16_OF_16_QUALIFIED / PILOT_PROTOCOL_READY / AWAITING_REAL_EXPERIENCE`

## Full 16-task audit

Six chronological inversions were found and corrected:

- F01/F02: 2019 is late, 2018 is early; references became `2` and `15`.
- F13/F14: April 1, 2018 is late, March 31, 2018 is early; references became `-496` and `3124`.
- F11/F12: the original task used the wrong 2019 column.

F11/F12 source-table repair:

- The same rows contain both `Actual Fiscal 2019 (constant currency) (3) $` and `... %`.
- The original generator selected the percentage column while declaring currency.
- The corrected tasks use the unambiguous same-table 2019 dollar column:
  - F11 Adjusted EBITDA: `1,092 - 1,007 = 85`.
  - F12 Revenue: `2,294 - 2,147 = 147`.
- Original task IDs, source items, source UID, cluster and row identity are unchanged.

No reserve task was introduced and no task meaning was invented.

## Pilot preparation

- Future tasks: **16/16 qualified**.
- R/C content: frozen without answers or solved examples.
- U/E contract: same format/order, two experiences per task, 2048-token cap, no future answers, no success-based selection.
- Request order: 16 tasks x 5 arms x 2 stages = **160 unique slots**.
- Arms are balanced at 32 requests each: B0/R/C/U/E.
- Budget: 160 requests, 1.7M tokens, retry 0, concurrency 1.

## Remaining condition

Pilot can proceed only after the scheduled collection produces a qualified real-experience pool and explainable U/E distinction. If U/E contexts become identical, pilot must stop.

This is `READY_FOR_PILOT_BUNDLE_AFTER_COLLECTION`, not authorization to run pilot before experience qualification.
