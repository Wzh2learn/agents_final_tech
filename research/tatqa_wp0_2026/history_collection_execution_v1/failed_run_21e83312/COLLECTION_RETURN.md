# COLLECTION_RETURN

> Status: `TWO_FIXTURE_GATES_FAILED / HISTORY_REQUESTS=0 / PILOT_NOT_RUN`

## Experience chains

- Complete trustworthy history chains: **0 / 12**.
- History requests: **0**.
- First-result / follow-up pairs: **0**.
- Qualified U/E experience: **none**.

## Two authorized runs

| run | requests | fixture result | history requests |
|---|---:|---|---:|
| `AUTH-20261018-1700-CST-54REQ-5a389f0e` | 6 | interface qualification failed | 0 |
| `AUTH-20261018-1925-CST-54REQ-21e83312` | 6 | retry-fix qualification failed | 0 |

The first run was preserved under `failed_run_5a389f0e/`. The second run used new bundle `21e83312...` and new raw root. No retry was made after either fixture gate.

## Qualification evidence

Across both runs, all 12 fixture responses showed:

- top-level `timings`;
- message-level `reasoning_content`;
- empty `content`;
- `finish_reason=length`;
- exactly 256 completion tokens consumed by reasoning.

The retry fix correctly accepted metadata and still rejected empty content. `/no_think` did not suppress reasoning on the fixed Qwen3.6/llama-server chain. Therefore tool execution, known-answer matching and answer/tool consumption remained unqualified.

Raw integrity for the second run: 6 request files, 6 response files, 6 COMPLETE markers, 0 CRASH markers, 0 request-response mismatches.

## Outcome measures

| measure | history | fixtures |
|---|---:|---:|
| answer/reference match | not attempted | not evaluable |
| calculator execution success | not attempted | 0/6 across two runs |
| operation satisfies task | not attempted | not evaluable |
| final answer consumes tool result | not attempted | 0/6 across two runs |

These are interface/output qualification failures, not model arithmetic errors and not evidence about experience learning.

## Consumption and identity

- Total requests: **12**.
- Conservative accounting tokens: **122,880**.
- Server-reported raw usage: **6,452 tokens** total.
- Raw/result evidence wall time: **52.50 seconds** across two runs.
- `max_tokens=256` unchanged in both runs.
- Final retry bundle: `21e83312bbb82e1a11ad3b7f3aef5e2a30574e30977e62d6ad0e61cb2fe71a3b`.
- Task/reference manifest remained `5be130d7d6c3514862ad44149ec61b95ba68c8d83178e259aa7da90904633db6`.
- No service restart, model change, parameter increase, retry, sample top-up, raw-root reset or second concurrent instance occurred.

## Pilot disposition

**Pilot not eligible and not run.**

There is no qualified history pool, so U/E cannot be formed from real experience without inventing evidence or weakening the frozen qualification rule. The 160-request pilot, training, memory write-back, source switch and public release remain unauthorized.

Final decision: **pause with a boundary result**. A future collection would require a new authorization and a model/runtime-level reasoning suppression that is verified before the next fixture gate. `/no_think` is empirically insufficient on this fixed chain.
