# C3 Return: Scorer, Derivation And Output-Contract Corrections

Status: `COMPLETE_WITH_B0_V4_DEVELOPMENT_OBSERVATION`

C3 preserved all B0 V1/V2/V3 raw and results. It did not collect history, run
a pilot, change the model or schema, raise `max_tokens`, retry, or repair raw
output.

## Corrections

1. Literal `%` is now accepted as a percent unit. Red and green receipts are
   `C3_UNIT_RED.json` and `C3_UNIT_GREEN.json`.
2. Tool consistency no longer searches arbitrary number pairs. Ordinary facts
   require literal returned evidence. ESD_006 derived values require explicit
   reference-V3 target atoms, operand atoms, operators and formulas, with the
   operand values present in the returned evidence. Red and green receipts are
   `C3_DERIVATION_RED.json` and `C3_DERIVATION_GREEN.json`.
3. Plan and consume prompts explicitly require minified JSON, no whitespace
   outside string values, no pretty-printing, indentation, Markdown fences or
   commentary. The model/schema/generation parameters remain unchanged.
4. The estimand is explicitly
   `COMPLETE_CANDIDATE_SELECTION_AND_CONSUMPTION`: it is not active evidence
   acquisition and not a V2 experiment reproduction.

Reference V3 changes only derivation checks. Required answer scope is unchanged
from reference V2, and reference V1 is preserved.

C3 FIX1 bundle:

```text
7bb3564cc8a30bac8d81f158232d68c8e3fbdf59247edbc5cd963c47deb893e7
```

Complete fixture: `21/21`.

## Scores Kept Separate

| Version | Score | Interpretation |
|---|---:|---|
| B0 V3 original frozen | 4/7 | Preserved original result |
| B0 V3 post-hoc unit fix | 5/7 | Only ESD_004 recovered from literal `%` scorer bug |
| B0 V3 post-hoc full checker V3 | 5/7 | Explicit derivation checker; no outcome change |
| B0 V4 formal development | 5/7 | Final C3 observation |

The post-hoc files are diagnostics and do not overwrite the original V3 score.
ESD_006 remains `UNKNOWN` and non-success in every corrected view.

## B0 V4

| Layer | Result |
|---|---:|
| Plan contains a minimal sufficient set | 7/7 |
| Consume cites a sufficient set | 6/7 |
| Answer reference match | 5/7 |
| HTTP/raw/tool-chain failures | 0 |
| Model output-format failure | 1 |
| Semantic non-success | 1 |

Successful tasks: ESD_001, ESD_002, ESD_003, ESD_004, ESD_010.

- ESD_006: sufficient `cand_005`, but actor returned `UNKNOWN`. This is a real
  non-success and cannot be converted by scoring.
- ESD_012: the minified instruction was present in the request, but the actor
  still pretty-printed and hit `finish_reason=length` at
  `completion_tokens=256`; the JSON remained truncated. The raw is preserved
  and not repaired.

The ESD_001 question/reference pair asks which two components were largest and
second largest; reference V3 also requires their numeric values. This is
reported as a question-reference ambiguity limitation and is not changed in
C3.

## Accounting

| Run | Requests | Accounting tokens |
|---|---:|---:|
| B0 V1 | 14 | 19,034 |
| B0 V2 | 14 | 46,830 |
| B0 V3 | 14 | 196,038 |
| B0 V4 | 14 | 196,748 |
| Total | 56/192 | 458,650/2,000,000 |

All 56 records are settled. Judge, training, production Memory, history, and
pilot counts are zero.

## Scientific Readout

With complete candidate visibility, evidence selection is no longer the main
gap: B0 V4 reaches plan sufficiency `7/7`. The remaining observed headroom is
consumption and output behavior: one sufficient-evidence abstention and one
structured-output truncation at the fixed token budget.

This does not support historical-experience claims. Before any history or
mechanism study on this panel, resolve or redesign the output serialization
budget and decide whether the ESD_001 numeric requirement matches the intended
question. The current FULL_VISIBLE estimand is limited to complete-candidate
selection/consumption.

## Evidence

- C3 specification: `C3_CORRECTION_SPEC.md`
- Unit red/green: `C3_UNIT_RED.json`, `C3_UNIT_GREEN.json`
- Derivation red/green: `C3_DERIVATION_RED.json`,
  `C3_DERIVATION_GREEN.json`
- V3 post-hoc: `results/B0_V3_EQUAL_VISIBILITY/B0_RESULT_POSTHOC_SCORER_V2.json`,
  `results/B0_V3_EQUAL_VISIBILITY/B0_RESULT_POSTHOC_SCORER_V3.json`
- V4 raw/result: `raw/B0_V4_MINIFIED_JSON/`,
  `results/B0_V4_MINIFIED_JSON/B0_RESULT.json`
- Machine verification: `C3_VERIFICATION.json`
- Shared ledger: `../execution_v1/RESEARCH_GENERATION_LEDGER.json`
