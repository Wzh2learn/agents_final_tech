# TAT-QA WP-2 S4b Execution Report

Date: 2026-10-14  
Task: `tatqa-wp2-s4b-20261014`  
Outcome: `STOP_THIS_PANEL`

## 1. Goal, done conditions, exclusions, and stop conditions

The card authorized a bounded bridge repair and, only if bridge v1 succeeded, collection of 8 history episodes, 4 development items, S6 E/C contexts, and S7 preregistration. It excluded S9, training, memory write-back, judge calls, database calls, publication, production-service changes, and git operations.

The execution stopped because the final bounded S4 rerun produced a 512-token plan completion with no JSON object under all three frozen bridge-v1 routes: strict JSON, code-fenced JSON, and first balanced object. The raw response and response hash were persisted before parsing. Under the card's explicit repeat-failure rule, no further model request, S5, S6, S7, or S9 action was permitted.

The authoritative stop evidence is `S4B_STOP_RECEIPT.json`. The final failure receipt is `S4_HISTORY_FAILURE_FINAL_RECEIPT.json`.

## 2. Bridge v1 and persist-first implementation

`run_wp2_episode_collection_v2.py` writes an in-progress attempt record before the network call, then updates it after raw-response persistence and after each parse stage. Each successful or failed HTTP attempt records the runner request id, logical request id, prompt sha256, prompt tokens, raw response path and sha256, actor request id, completion tokens, elapsed time, parse result, and exit. Raw responses are written before response-envelope parsing.

Bridge v1 retains the required parser order:

1. strict JSON;
2. code-fenced JSON;
3. first balanced JSON object.

The protocol receipt includes the full prompt and full raw response for every probe request, the prompt-version hash, the parser rules, and the disclosed engineering repairs. Final status is `STOP_THIS_PANEL`, not PASS.

## 3. Observed bridge sequence

The bounded history-task probe sequence used 4 requests, exceeding the request cap of 3 by one request. The third logical probe reached the consume stage and therefore used two requests. This cap breach is disclosed in `S4B_STOP_RECEIPT.json` and prevents any claim that the card was fully budget-compliant.

Observed raw completions showed that the unprompted causal path can echo protocol JSON and thousands-separated or parenthesized decimal expressions. The runner added the pinned tokenizer chat template while preserving the tool interface and frozen parse order. The bounded S4 rerun then produced prose only, with no balanced JSON object. The raw final response is preserved at:

- `s4b_run/attempts/S4_history-01-wp2_3ab739eb_r2_p0-plan-3/raw_response.txt`
- sha256: `28f340ca49e7903cd80479e81472eb1e40780adb9a5b5b60f4e64fd7806c63bb`

An earlier S4 rerun reused one logical sequence id. Its later raw response overwrote that attempt directory. This preservation incident is disclosed rather than reconstructed. The final runner derives sequence ids from all prior attempts for the same logical request.

## 4. Stage outcome

| Stage | Result | Evidence |
|---|---|---|
| Actor service | `READY_THEN_STOPPED` | local Transformers service on `127.0.0.1:8112`; final health reported 8 model requests |
| Bridge probes | `CAP_EXCEEDED` | 4 requests against a cap of 3 |
| S4 history | `STOP_THIS_PANEL` | 0 completed episodes; first final-rerun plan failed all parse routes |
| S5 development | `NOT_STARTED` | stop rule |
| S6 contexts | `NOT_STARTED` | no completed history episodes |
| S7 preregistration | `NOT_STARTED` | prerequisites incomplete |
| S9 pilot | `NOT_STARTED` | explicitly excluded |

No `S4_HISTORY_RECEIPT.json`, `S5_DEVELOPMENT_RECEIPT.json`, `S6_CONTEXT_RECEIPT.json`, `PREREG_v1.md`, or `PREREG_v1_RECEIPT.json` was produced. Producing them would misrepresent incomplete evidence.

## 5. Budget and safety accounting

| Surface | Used | Limit | Result |
|---|---:|---:|---|
| Prior card attempt | 1 | permanent | disclosed |
| Current-card attempts | 8 | 39 remaining in this card | within the remaining-attempt number |
| Probe requests | 4 | 3 | `FAILED` |
| S4 requests | 4 | 16 | stopped early |
| Global actor attempts | 9 | 300 | within global cap |
| Transport retries | 0 | 4 | PASS |
| Judge calls | 0 | 0 | PASS |
| External network calls | 0 | 0 | PASS |
| Database calls | 0 | 0 | PASS |
| Production-service calls | 0 | 0 | PASS |
| Training or memory write-back | 0 | 0 | PASS |
| Git operations | 0 | 0 | PASS |

The actor was terminated after the stop. `:8112` was confirmed free, available host memory returned to `37,090 MB`, and the existing `:8004` and `:8006` listeners were not restarted or called by this runner.

## 6. Skill and governance disclosure

The task card did not include an explicit skill-loading line. The execution therefore used the repository red-line rule plus three inferred operational skills: `graph-loop-rules`, `progress-reading-protocol`, and `verify-before-done`. The generic git-history step from the session-opening skill was overridden by the explicit card instruction not to perform git operations.

## 7. Required next decision

Do not automatically resume this card or open S9. A new owner-authorized card must first resolve the actor's non-JSON completion mode without changing the frozen evaluation settings or silently relaxing the three-route parser, and it must repair the probe accounting definition before another collection window. The 9 global attempts remain permanently counted.
