# COLLECTION_RETURN

> Status: `FIXTURE_QUALIFICATION_FAILED / HISTORY_REQUESTS=0 / PILOT_NOT_RUN`
> Authorization: `AUTH-20261018-1700-CST-54REQ-5a389f0e`

## 1. Experience chains

- Complete trustworthy history experience chains: **0 / 12**.
- History requests: **0**.
- First-result / follow-up pairs: **0**.
- No history task was opened after the fixture gate failed.

## 2. Outcomes

| measure | history | qualification fixtures |
|---|---:|---:|
| answer/reference match | not attempted (0/0) | not evaluable (0/3) |
| calculator execution success | not attempted (0/0) | 0/3 |
| operation satisfies task | not attempted | not evaluable |
| final answer consumes tool result | not attempted (0/0) | 0/3 |

The fixture failures are interface qualification failures, not model-answer errors.

## 3. Failure evidence

All 3 fixture attempts sent plan and consume requests, producing 6 raw request/response pairs:

- `timings` is present at the response top level and `reasoning_content` is present in each message, while the strict interface schema allowed neither.
- More importantly, every `content` is empty, every `finish_reason` is `length`, and all 256 completion tokens were consumed by reasoning before a valid JSON object was produced.
- Therefore schema parsing, real tool execution, known-answer comparison, and answer/tool consumption could not qualify.
- Raw integrity: 6 request files, 6 response files, 6 COMPLETE markers, 0 CRASH markers, 0 missing request-response pairs.

## 4. Disposition

- Fixture trajectories disqualified: **3 / 3**.
- Incomplete raw request-response chains: **0**.
- U/E experience pool: **not established**.
- E/U distinguishable contexts: **none**.
- Pilot: **not run**. The conditional pilot gate failed before experience construction.

Machine-readable disposition:

```json
{
  "complete_history_chains": 0,
  "history_tasks_total": 12,
  "qualified_experience": [],
  "u_contexts": [],
  "e_contexts": [],
  "pilot_status": "NOT_RUN_FIXTURE_QUALIFICATION_FAILED"
}
```

## 5. Consumption and identity

- Requests: **6 / 54**.
- Conservative accounting tokens: **61,440 / 600,000** because each unparseable response settled its full 10,240-token reservation.
- Server-reported raw usage: 1,685 prompt + 1,536 completion = **3,221 tokens**.
- `max_tokens`: **256**, unchanged.
- Wall time across raw/result evidence: **26.31 seconds**.
- Final bundle SHA-256: `5a389f0ee0cdb6b1522fa4a291b8f95b413f59021b5ef0b8a5503d86b4f4b85c`.
- Authorization SHA-256: `6835199c639e6c60646f7aac70099efebac5baee83b63aeee7ed7ef120877259`.
- Raw root: `/home/testuser/wzh/collection_runs/AUTH-20261018-1700-CST-54REQ-5a389f0e`.

## 6. Pilot decision

**Not eligible to request or run the 160-request pilot.**

The run produced no qualified history experience, so the E/U distinction cannot be implemented without inventing or weakening the evidence-qualification rule. No tasks were added, no retry occurred, and no alternate raw root or service was used.

Next disposition: **pause and retain the boundary result**. Any future collection requires a new authorization and pre-run qualification of the actual response wrapper/output behavior while keeping the model and `max_tokens=256` unchanged. The remaining pilot, training, memory write-back, source switch, and public release remain unauthorized.
