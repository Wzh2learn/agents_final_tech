# D Correction: Generation-Cap Incident And Compliant Primary

Date checked: 2026-10-27, Asia/Shanghai
Experiment execution date: 2026-10-26, Asia/Shanghai
Scope: accounting and scientific-identity correction only. No model call was
made by this correction.

## Finding

A's remediation return states that the second `--mode calibrate` performed no
additional generation. That statement is not supported by the launcher log or
the two raw ledgers.

Evidence:

1. Log item 51 ran
   `python -m ...raw.runner --mode calibrate`, loaded Qwen3-4B, generated 40
   attempts and then failed in post-generation semantic scoring. The immutable
   raw is
   `raw/runs/failed_attempt_20261026/P2_GENERATIONS.partial_40.jsonl`,
   SHA256 `fca487c420409a389059aefe169562ca28f58246df0b6157b6c51b7258132488`.
2. Log item 89 ran the same `--mode calibrate` command again. Its output again
   contains the model-weight loading sequence and it produced
   `raw/runs/primary/P2_GENERATIONS.jsonl`, SHA256
   `03f714dd0c8946e82e4e3b9fa7f74efb9911ac59236ec164929ac5e9afa38450`.
3. The two batches have the same 40 call IDs and the same scientific payload
   fields, but every batch wall-time field is a new physical measurement.
   Deterministic decoding explains identical responses; it does not make a
   second model invocation free.
4. Log item 95 is the later zero-generation rescore of the already-existing
   primary ledger. A's "no additional generation" statement is true only for
   item 95, not item 89.

## Corrected Accounting

| Category | Correct value |
|---|---:|
| First physical batch | 40 calls |
| Second physical batch | 40 calls |
| Actual physical generation calls | **80** |
| Hard call cap | 48 |
| Call-cap breach | **32 calls** |
| Compliant primary calls | 40 |
| Quarantined deterministic replay calls | 40 |
| First-batch input/output tokens | 33,207 / 2,609 |
| Second-batch input/output tokens | 33,207 / 2,609 |
| Actual total input/output tokens | **66,414 / 5,218** |
| Training calls/tokens | 0 / 0 |

The 240,000-token ceiling was not reached under either input-plus-output or
output-only accounting. The attempt ceiling was nevertheless breached and
cannot be repaired by deterministic replay or by relabelling the second batch
as scoring.

## Scientific Disposition

The first 40 calls remain a valid bounded development sample because they were
generated before the cap was exhausted: 36 primary calls plus four
preregistered bounded retries. They are retained byte-for-byte.

The second 40 calls are quarantined as a prohibited deterministic replay and
are excluded from the compliant scientific estimate. `D_RESCORE_FIRST_BATCH.py`
performs a zero-model post-hoc score transfer from the second annotated ledger
only after verifying that every original scientific payload field matches the
first batch by call ID. The derived result is written under
`raw/runs/compliant_primary/`; its raw source hash is the first-batch hash.

Consequences:

- Report arm results only from `raw/runs/compliant_primary/`.
- Report actual physical attempts as 80/48 and preserve both raw ledgers.
- Do not call the second batch independent replication, confirmation or extra
  evidence.
- Do not rewrite `A_REMEDIATION_RETURN.md`; it remains historical A output.
- Any later confirmation requires a new explicit budget and a new frozen
  sample. The over-cap batch cannot be converted into confirmation.
