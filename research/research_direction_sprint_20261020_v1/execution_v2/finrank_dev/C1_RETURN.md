# C1 Return: FinRank Tool Contract And Development Baseline

Status: `COMPLETE_WITH_DEVELOPMENT_OBSERVATION`

Scope: seven retained AI-assisted development tasks only. This is not
statistical confirmation, independent human gold, or an experience-learning
result.

## Contract Qualification

- Frozen actor inputs and evaluation references are separate:
  `TASKS_ACTOR_V1.json` and `REFERENCES_V1.json`.
- The actor sees the complete `plan`, `evidence_lookup`, and `consume` schemas,
  visible source fields, and the actual returned evidence. It does not receive
  reference answers, minimal sufficient sets, adjudication notes, or hidden
  passage IDs.
- `plan` accepts only current-task candidate IDs and no history actions in B0.
- `evidence_lookup` preserves request order and visible fields, and rejects
  empty/out-of-range, cross-task, unknown, duplicate, and extra-key arguments.
- `consume` can cite only returned IDs. Strict validation does not accept
  `{"plan": ...}` or `{"consume": ...}` wrappers.
- Offline fixtures pass `15/15`, including same-form/different-content-period,
  ESD_010 sufficient-subset, no-leakage, and wrapper positive/negative cases.
- Non-generative runtime qualification passed. Generation uses the pinned
  Qwen3.6-35B-A3B-Q4_K_M artifact, `enable_thinking=false`,
  `max_tokens=256`, and `127.0.0.1:18004` only as a transport override.

Frozen B0-fix bundle:

```text
be910bc82200466c5218912943ff5b896da5c734ecefe5f8bdd9acc36e7d08ca
```

## Generation Accounting

| Run | Requests | Accounting tokens | Status |
|---|---:|---:|---|
| B0 V1 | 14 | 19,034 | All outputs wrapped despite the schema; retained as engineering failure |
| B0 V2 engineering fix | 14 | 46,830 | Complete, no engineering/schema/tool errors |
| Total | 28 | 65,864 | Shared ledger `28/192`, `65,864/2,000,000` |

All 28 responses have request/response pairs and immutable raw capture.
Retries, judge calls, training calls, and production Memory writes are zero.
The deterministic strong-rule baseline used zero generation requests.

## Development Results

B0 V2 strict result: `1/7` success. All six non-successes are semantic rather
than engineering failures.

| Task | B0 plan contains a minimal sufficient set | Consume sufficient | Frozen answer match | Main observed issue |
|---|---|---|---|---|
| ESD_001 | yes | yes | no | Correct evidence selected, but facts omit 12,471 and 5,050 |
| ESD_002 | no | no | no | Selected `cand_005`; missed content-period evidence `cand_001` |
| ESD_003 | no | no | no | Selected `cand_001,cand_006`; missed `cand_007` |
| ESD_004 | no | no | no | Selected `cand_001,cand_003`; missed `cand_005` |
| ESD_006 | yes | yes | no | Returned the requested 20,541 and 11.97%; checker additionally required both input rows |
| ESD_010 | yes | yes | yes | Both requested liabilities matched and were tool-consistent |
| ESD_012 | no | no | no | Missed `cand_001`; method was right, but the trend fact was unsupported and 2.42/3.33/4.12 were absent |

The frozen answer checker is intentionally preserved. For ESD_006, a
post-hoc question-scope observation is that the model answered the two values
asked by the question while the checker required revenue and cost operands as
additional atoms. This is a scoring-contract limitation, not evidence that the
model missed the requested output.

The deterministic visible-rule baseline selected a sufficient set for `7/7`
at the plan layer. Its extractive consume stage cited a sufficient set for
`6/7` and achieved `0/7` strict answer matches, so it is informative for
selection but weak as an answer baseline.

## Interpretation

The runnable tool contract is now qualified. The current panel has headroom in
answer fact formation and in multi-evidence acquisition. It does not yet show
that historical experience is the right remedy.

There is also an access asymmetry that must be fixed before treating B0 versus
the strong rule as a clean method comparison: B0 plan sees question scope and
candidate metadata before lookup, while the deterministic rule scores candidate
text directly. The rule's `7/7` selection result therefore is not a
same-information upper bound for B0.

Recommended next development step: freeze equal plan-time candidate visibility,
remove the ESD_006 over-required answer atoms in a new reference version, and
rerun only the smallest baseline needed to distinguish evidence acquisition
from answer consumption. Do not collect history until a residual decision
space remains after those two corrections.

## Evidence Locations

- Contract and runner: `finrank_contract.py`, `run_b0.py`
- Fixtures: `FIXTURE_RECEIPT.json`, `FIXTURE_RECEIPT_V1_FAILED.json`,
  `FIXTURE_RECEIPT_V2_FAILED.json`
- B0 V1: `results/b0_v1/B0_RESULT.json`, `raw/B0_V1/`
- B0 V2: `results/B0_V2_ENGINEERING_FIX/B0_RESULT.json`,
  `raw/B0_V2_ENGINEERING_FIX/`
- Strong rule: `results/STRONG_RULE_RESULT.json`
- Verification: `C1_VERIFICATION.json`
- Shared accounting:
  `../execution_v1/RESEARCH_GENERATION_LEDGER.json`
