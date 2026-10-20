# Authorized Run Implementation Plan

Status: `READY_TO_BIND_AND_WAIT_FOR_FIXED_WINDOW`

| step | deliverable | status |
|---|---|---|
| 1 | Preserve baseline bundle and changed baseline artifacts | DONE |
| 2 | Add per-request window gate and partial-result expiry behavior | DONE |
| 3 | Add fixture-first qualification gate and zero-history failure behavior | DONE |
| 4 | Update execution order, tests, receipts, change record, and new bundle | DONE |
| 5 | Targeted Loop C re-audit of only the two increments | DONE |
| 6 | Bind one authorization file to the new bundle | READY |
| 7 | Execute the single fixed-window run and write `COLLECTION_RETURN.md` | PENDING_FIXED_WINDOW |
