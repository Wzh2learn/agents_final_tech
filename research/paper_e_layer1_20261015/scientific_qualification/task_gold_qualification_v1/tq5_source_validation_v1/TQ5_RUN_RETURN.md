# TQ5_RUN_RETURN

> run_id: `20261017T072340Z_5d8942bd` | panel: `TQ-5` | status: `COMPLETED`
> execution: GB10 `Qwen3.6-35B-A3B-Q4_K_M.gguf` at `http://127.0.0.1:8004`
> execution snapshot: `execution_v1/recovery_v1/SNAPSHOT_MANIFEST.json`, sha256 `a9c1c79eb3666f7d15be115d2d84ccf760b7c7b7a96150a29051a251b3e49a38`
> boundary: table-disjoint developmental panel; `scientific_gold_validity = NOT_ESTABLISHED`; no confirmatory claim

## 1. Execution and budget

- One authorized run only; `resumed=false`. The entrypoint verified 8/8 snapshot files before run and analysis.
- Requests: 36/36 planned steps completed; 36/40 allowed attempts; infrastructure retries 0/4.
- Tokens: 44,867 settled (TQ-5 cap 400,000). Chain totals after this run: 72 reserve / 72 settle / 85,072 tokens (caps 80 / 800,000). TQ-4 and TQ-5 quotas were not transferred.
- Timing: first request 2026-10-17 15:23:54 Asia/Shanghai; last response 15:27:10; duration 196 seconds. Start was within 09:00-18:30 and duration was below 90 minutes.
- Request parameters, model identity, material pins before/after, and HTTP status checks passed. Non-generation auxiliary operations: 72.
- The run manifest covers 83 run files and embeds 8 execution-snapshot hashes. Local and GB10 run bytes match the manifest.

## 2. Task-level results

The `frozen score` is the pre-frozen numeric scorer result. It is not a human semantic-gold label.

| task | layer | actor answer | frozen score | evidence | B | C | diagnostic disposition |
|---|---|---:|---|---|---|---|---|
| T01 | difference | `(2.4)pts.` | NO_MATCH | legal | accept | accept | `UNSCORABLE_FOR_PROVEN_ERROR`: accounting parentheses denote `-2.4`; the frozen parser normalizes the display as `+2.4`. |
| T02 | difference | `394` | MATCH | legal | accept | accept | Supported match under the frozen reference. |
| T03 | difference | `540` | MATCH | legal | accept | accept | Supported match under the frozen reference. |
| T04 | difference | `-7,614` | MATCH | legal | accept | accept | Supported match under the frozen reference. |
| T05 | ratio | `1,400` | MATCH | legal | accept | accept | Supported match under the frozen reference. |
| T06 | ratio | `7.87%` | MATCH | legal | accept | invalid | C returned prose plus an embedded JSON object; strict parsing failed. No decision is extracted. |
| T07 | ratio | `0.002` | NO_MATCH | illegal | abstain | invalid | `UNSCORABLE`: the question asks for total sales, but the reference divides by an affiliate-sales row. The actor notes say the denominator is absent while the final number is internally inconsistent; one cell citation is out of bounds. |
| T08 | ratio | `154.7 million` | NO_MATCH | legal | alarm | accept | Reference uncertainty remains. Under the frozen reference, `321.7/0.64=502.66` million share-years; the actor uses 154.7 million shares outstanding in 2020. B reports a period/scope contradiction; C accepts. |
| T09 | percentage change | `8.54%` | MATCH | legal | accept | accept | Supported match under the frozen reference. |
| T10 | percentage change | `3%` | NO_MATCH | legal | accept | invalid | `UNSCORABLE_FOR_PROVEN_ERROR`: 3% rounds the derived 2.81%, while the question specifies no output precision. C output was truncated before valid JSON. |
| T11 | percentage change | `-32.57%` | MATCH | legal | accept | accept | Supported match under the frozen reference. |
| T12 | percentage change | `5.7%` | NO_MATCH | legal | accept | accept | `UNSCORABLE_FOR_PROVEN_ERROR`: 5.7% rounds the derived 5.67%, while the question specifies no output precision. |

## 3. Aggregates and fixed dimensions

| layer | frozen MATCH | evidence legal | B accept / alarm / abstain / invalid | C accept / alarm / abstain / invalid |
|---|---:|---:|---|---|
| difference (T01-T04) | 3/4 | 4/4 | 4 / 0 / 0 / 0 | 4 / 0 / 0 / 0 |
| ratio (T05-T08) | 2/4 | 3/4 | 2 / 1 / 1 / 0 | 2 / 0 / 0 / 2 |
| percentage change (T09-T12) | 2/4 | 4/4 | 4 / 0 / 0 / 0 | 3 / 0 / 0 / 1 |
| total | 7/12 | 11/12 | 10 / 1 / 1 / 0 | 9 / 0 / 0 / 3 |

- Answer/reference matching: 7/12 MATCH and 5/12 NO_MATCH under the frozen numeric rule.
- Evidence-location legality: 11/12 legal; T07 has one `cell_out_of_bounds`.
- Citation support: `NOT_ASSESSED`. No separately adjudicated support label exists.
- Checker decisions: B 12/12 valid; C 9/12 valid and 3/12 `invalid` for JSON parse failure.
- Full-run output validity is 33/36. HTTP success is 36/36 and must not be conflated with output validity.
- Pairing unit is the task. TQ-5 has no repeated-stimulus pairs; this section is not applicable rather than zero observed disagreements.

## 4. Failures and interpretation boundaries

- C-T06 and C-T07 emitted long prose with no strict top-level JSON object; C-T10 reached `finish_reason=length` at 2,048 completion tokens. All remain `invalid`; prose is not converted into decisions and no retry was made.
- T01 exposes a scorer-format limitation, not a demonstrated reference or actor failure.
- T07 exposes a source-reference semantic problem. The pre-run checks established field equality, arithmetic reproducibility, and operand locatability, but not independent human semantic gold.
- T08 retains `reference uncertainty`; neither B nor C resolves the scope question by itself.
- T10/T12 expose a precision-policy mismatch between the frozen tolerance and unqualified natural-language answers. They remain NO_MATCH in the frozen analysis but `UNSCORABLE` as proven model errors.
- The panel is table-disjoint only. It is not report-level independent, not proven unseen during model training, and not a header-drift experiment.
- TQ-4 and TQ-5 are separate developmental panels and are never pooled into a single sample size or error rate.

## 5. Corrections and evidence

- The first analyzer output reused the TQ-4 label for `part1.summary.label`. `reviews/TQ5_RESULTS_CORRECTED_v1.json` changes only that label and adds source-hash/correction metadata. Raw responses, scores, decisions, and manifests are unchanged.
- `reviews/TQ5_POST_RUN_RECOMPUTE_v1.json` recomputes manifest, snapshot, RUN_META, ledger, budget, scoring, legality, decisions, prompt isolation, and the label correction. This is a focused Loop D recomputation, not an independent-review claim.
- `scientific_gold_validity` remains `NOT_ESTABLISHED`; `NO_PROMOTION` is recommended for empirical Paper E claims.
