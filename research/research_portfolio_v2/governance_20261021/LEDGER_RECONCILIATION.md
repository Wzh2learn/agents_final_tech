# Generation usage reconciliation

Date: 2026-10-21, Asia/Shanghai. Evidence identity:
`POST_HOC_ACCOUNTING_RECONCILIATION_NOT_NEW_MODEL_EXPERIMENT`.

The current portfolio contains **101 recorded generation request/response
pairs across eight generation batches**, plus one aggregate event for a
zero-request execution replay. Its corrected current consumption is
**101 / 2,048 attempts and 57,987 / 10,000,000 tokens**. The frozen event
values sum to 57,222 tokens; two explicit post-hoc adjustments add 765 tokens.
The original 747- and 313-attempt historical ledgers remain separate.

## Findings

| Batch | Generation pairs | Frozen event tokens | Raw usage tokens | Adjustment |
|---|---:|---:|---:|---:|
| Qualification V1 canary | 1 | 0 | 84 | +84 |
| Qualification V2 | 24 | 2,514 | 2,514 | 0 |
| Query scout V1 | 3 | 1,955 | 1,955 | 0 |
| Query scout V2 | 6 | 3,243 | 3,924 | +681 |
| CodeUpdateArena adapter V1 | 16 | 9,986 | 9,986 | 0 |
| CodeUpdateArena new-family confirmation | 16 | 10,995 | 10,995 | 0 |
| VersiCode observability | 32 | 15,917 | 15,917 | 0 |
| NtripBrowser behavioral case | 3 | 12,612 | 12,612 | 0 |
| Total | 101 | 57,222 | 57,987 | +765 |

1. The failed qualification canary returned **51 prompt + 33 completion = 84
   tokens**. The preserved qualification runner validated the output contract
   before extracting usage. Validation failed, so its frozen ledger recorded
   zero despite a saved response with usage.
2. Query scout V2's sixth response (`benign_change/2`) returned **601 prompt +
   80 completion = 681 tokens**. `parse_decision` rejected the illegal query
   before usage settlement. Its frozen event recorded the first five
   responses only, although all six generation calls were counted.

The first finding was a known early-canary omission; scanning all 101 saved
responses identified the second. Both share a settlement-order defect:
generation cost must be settled at the transport boundary even if subsequent
parsing, output validation or tool validation fails. A future runner should
settle usage before these validations and conservatively account transport
failures. This finding does not authorize rewriting frozen runner versions.

## Preservation and current accounting

The original per-run ledgers, results, raw responses, source runners, scores
and scientific rulings are unchanged. The current
[`COST_AND_CANDIDATES.json`](../COST_AND_CANDIDATES.json) retains the original
event values and adds `post_hoc_adjustments`; its `new_budget` reflects their
sum. The applicable formula is:

```text
current_tokens = sum(events.accounting_tokens)
               + sum(post_hoc_adjustments.accounting_tokens_delta)
57,987         = 57,222 + 84 + 681
```

Attempt and recorded generation POST counts remain 101. The ledger's
`physical_http_calls` means generation POST calls, excluding the four
model-identity GETs reported in the frozen Goal return. The saved generation
pairs do not constitute an independent packet/network trace; this audit
neither establishes the absence of unrecorded traffic nor reissues requests.

The pre-reconciliation current aggregate had SHA-256
`e657af2d473ab8ad14ef5b5302eb7a862e8ecdeb30ba8f993ff038f917b635cc`.
Historical reports containing 57,222 remain checkpoint receipts. Current
entry points should cite the corrected aggregate rather than silently editing
those reports.

## Reproduction and negative controls

Run from the Git root with the applicable Python environment:

```text
python research/research_portfolio_v2/governance_20261021/reconcile_ledger.py --negative-controls
```

[`reconcile_ledger.py`](reconcile_ledger.py) reads all 101 request/response
pairs, validates each usage decomposition, each batch count, the two
adjustment hashes and the current aggregate. It also verifies the frozen
input SHA-256 set recorded in
[`LEDGER_RECONCILIATION.json`](LEDGER_RECONCILIATION.json). It exits nonzero
on missing files, missing/nonpositive usage, count mismatch, an unrecognized
new event, changed frozen inputs, inconsistent adjustments or current totals.

Six in-memory negative controls must be rejected: decrement the aggregate by
one token; omit each of the two failed responses; zero each failed response's
usage; remove all adjustments. They never modify actual evidence files.
Three additional CLI checks used an isolated temporary evidence copy: a
one-token aggregate error and removal of either failed response each returned
exit code 1. The untouched actual tree then passed again. Temporary test
copies were removed; no frozen source file was changed.
This is a bounded reconciliation of the explicitly mapped 101-generation
snapshot; a later batch requires extending the audit rather than implicitly
passing through unexamined events.

Local standard-library verification uses Python 3.11.9 and is not Python 3.12
project-suite or GB10 runtime acceptance. The script itself makes zero model
or network calls. Root may repeat the same deterministic audit on GB10 after
the files are synchronized.
