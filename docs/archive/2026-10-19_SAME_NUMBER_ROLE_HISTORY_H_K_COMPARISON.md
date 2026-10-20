# Same-Number Role History/H/K Comparison

Status: `EXPLORATORY_COMPARISON_COMPLETE_NO_UNIQUE_HISTORY_EFFECT`

## Source isolation

- History collection: 6 tasks from development clusters `cluster_0402`, `cluster_1582`, `cluster_2174`.
- Evaluation: 6 tasks from exploratory future clusters `cluster_1604`, `cluster_1792`, `cluster_2442`.
- No source cluster is shared between history and evaluation.

## History collection

- 6 task-matched role-binding histories, two planned attempts each.
- 24 requests, 16,064 tokens.
- Four first attempts were corrected on attempt 2.
- The history contains actual plan/tool/consume outputs and deterministic feedback; no future evaluation output entered the pool.

## Same future panel

| arm | success | non-success | decision match | interpretation |
|---|---:|---:|---:|---|
| B0 | 5/6 | 1 | 5/6 | baseline headroom |
| R | 4/6 | 2 | 6/6 | role rule fixes decisions but leaves plan/tool failures |
| C | 3/6 | 3 | 3/6 | generic context is weaker |
| H | 6/6 | 0 | 6/6 | corrected history examples |
| K | 6/6 | 0 | 6/6 | ordinary solved examples without history/feedback metadata |

H and K produce the same decision on all six tasks. One plan expression differs, but the final role decision and outcome are identical.

## Mechanism conclusion

`FACT`: H improves over B0/R/C on this small future panel.

`FACT`: K, an ordinary solved-example control with history and feedback removed, reaches the same 6/6 result.

`INFERENCE`: the observed H gain is explained by few-shot task demonstrations or shared task structure, not uniquely by real historical experience or correction feedback.

`DECISION`: do not claim an experience-specific mechanism from this run. Preserve the result as a negative boundary for the current experience-presentation design.

## Accounting

- New requests: 64 (24 history + 8 R residual + 8 C residual + 12 H + 12 K).
- New accounting tokens: 67,130.
- Cumulative: 292/292 requests and 310,144/2,450,000 tokens.
- No training, judge, pilot or production-memory calls.

## Next gate

The role-binding task remains useful for studying evidence decisions, but the current H presentation does not isolate a real-history effect. A future study would need either:

1. a new experience representation whose information is unavailable in ordinary solved examples, with K and random/no-guidance controls; or
2. a different task where historical correction changes an action that solved examples cannot prescribe.

No further model run is authorized under the current budget.
