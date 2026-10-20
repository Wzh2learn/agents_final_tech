# Implementation Delta

The revision 3 source split is fixed. The 19 WP2-designated clusters remain conservatively isolated and their real exposure nature is not reopened.

| new artifact | reused or changed contract | delta boundary |
|---|---|---|
| `build_task_manifest.py` | consumes pinned `candidate_items_v2.json` and `SPLIT_PROPOSAL.json` | selects 32 tasks by deterministic rank after contract/reference validity; never orders by gold, answer, score, or model result |
| `execution_core.py` | reuses signed-difference, accounting parentheses, calculator, and independent-reference semantics | adds explicit unit-source precedence, strict JSON schemas, boolean rejection, LF JSON, bounded immutable raw capture, and worst-case budget reserve/settle |
| `collection_runner.py` | new isolated online runner | wraps plan -> real calculator -> consume; authorization and bundle gates run before adapter construction; no request is issued by preflight or this readiness task |
| `PROMPT_PLAN.json`, `PROMPT_CONSUME.json`, `OUTPUT_SCHEMAS.json` | frozen constrained-task protocol | exact JSON output, explicit nulls for UNKNOWN/REFUSE, no retry, no hidden reference or UID in actor context |
| `RUNTIME_IDENTITY_SNAPSHOT.json` | reuses TQ model pin and service props as read-only identity sources | non-generative hash snapshot only; tokenizer is bound by the GGUF artifact hash |
| `TASK_REFERENCE_MANIFEST.json`, `EXECUTION_PLAN.json` | fixed revision 3 cluster placement | 12 history tasks x 2 attempts, 3 qualification fixtures x 1 attempt, 54 request slots |
| `tests/test_execution_v1.py` | new contract and integration tests | fixture adapter is non-generative and explicitly separate from scientific model calls |

No old WP-2 runner, TQ artifact, frozen score, raw dataset, or prior review is modified.
