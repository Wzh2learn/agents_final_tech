# Zero-Training and Zero-Generation Evidence

## Historical A attempt retained

The following statement is preserved for the superseded pre-remediation A
attempt and must not be used as current P2 accounting:

- P2 generation calls: 0
- P2 generation tokens: 0
- P2 training calls: 0
- P2 generation stop reason: failed formal preflight at runner→adapter→scorer dry run
- P1 regression calls: 0 model calls; deterministic local actor only
- A token ledger: no model output generated; input/cache/output/reasoning token categories are therefore `NOT_APPLICABLE_NO_CALL`

## Remediation accounting

- P2 formal preflight: pass before scientific generation.
- P2 scientific generation calls after preflight: 40 = 36 primary + 4 bounded retries.
- P2 output tokens: 2,609; measured non-padding input tokens: 33,207.
- P2 training calls/tokens: 0/0.
- A harness input/cache/output/reasoning tokens: `UNKNOWN`.
- Claude/subscription/cash fees: `UNKNOWN`.
- The prior failed scoring attempt is preserved under
  `raw/runs/failed_attempt_20261026/`; it contains no scientific conclusion.
