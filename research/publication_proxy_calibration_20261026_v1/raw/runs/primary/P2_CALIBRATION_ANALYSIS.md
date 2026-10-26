# P2 Three-Arm Calibration

This is a 12-item exposed development-panel comparison after a passing hash-bound runner→adapter→model→parser→scorer preflight. It is not a generalization, noninferiority, upper-bound or lower-bound study.

| Arm | Accept | Pending | Reject | Unknown | Error delivery | Input tokens | Output tokens | Context chars (mean) | Wall s |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| table_top3 | 2 | 0 | 10 | 1 | 0.833 | 8863 | 778 | 1710.1 | 46.91 |
| table_top5 | 3 | 0 | 9 | 1 | 0.750 | 9780 | 778 | 2040.0 | 46.45 |
| table_all | 3 | 0 | 9 | 2 | 0.750 | 11384 | 786 | 2630.2 | 47.69 |

Measured generation calls: 40; generation tokens: 2609; training calls/tokens: 0/0; cached tokens and cash/subscription cost: UNKNOWN.

Raw responses and paired item differences are under `raw/runs/primary/`. Old 507-row proxy counts and visible-character measurements remain separate from measured model tokens.

Disposition separates proxy/reference defects, retrieval omissions, actor errors, parser failures, semantic pending adjudication, and the measured cost/risk tradeoff.
