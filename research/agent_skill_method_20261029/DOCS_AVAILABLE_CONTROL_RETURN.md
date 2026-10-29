# Optional same-content documentation control

2026-10-29. Post-hoc, same public SkillsBench task, one Agent episode. The decision to add this control followed the earlier results; it is not a pre-registered or independent-source study. Raw outputs and prior reports remain unchanged.

## Comparison contract

The no-skill and forced all-skill arms in [OUTPUT8192_PAIRED_RETURN.md](OUTPUT8192_PAIRED_RETURN.md) and the new `docs_available` arm use the same task statement SHA-256 `51b34b97291d07c10a0632781102e9cc4a4c9e9b8cf09b31ee93a1b5ab7f549d`, config `bf4f44ffb65803b2e0ffe998c144abc6b67418dc7cf1fdcefddd17a3056402b3`, and unmodified trace `9e81b386f0d8cea16d376b041d7a7e8fed5ba65b53e989444c76cef408442c2a`. Configured output cap 8,192, 8 POSTs, 450,000 request bytes and 300-second ceilings are the same. The same isolated no-network container and post-episode original verifier assertions under pytest 9.0.1 are used; verifier and oracle are never mounted in the Agent container. These are adapted executions, not official BenchFlow runs.

The all-skill arm was explicitly told to read both upstream skill files before solving. In docs_available, those exact two files were accessible, and their paths were presented as **optional reference files**, not required initial instructions. The no-skill arm did not have those files. Thus all-skill and docs_available have the same documents available, but prompts and exposure order differ; this is neither equal prompt nor equal realized cost. The two files' SHA-256 values are `28ced940ec272cc01cf06519912077492d948b10e08a933acba12dd9907220cf` and `353a7215727695b01e48ea69e63ed92c0b32174534a6bda38cee9b91382e5963` in both arms. In the docs_available raw trace, two `read` tool events for both references completed successfully. Glob attempts before them failed; then the Agent explicitly read each file.

| Arm, run | Verifier result | Agent/process result | POSTs | Known event tokens incl cache | Elapsed incl verifier |
| --- | --- | --- | ---: | ---: | ---: |
| no skill `258386` | 1 passed, 9 failed on one generated report | exit 1; sixth POST timed out with no completed usage | 6 | 42,085 + UNKNOWN | 239.464 s |
| forced skill `263034` | 10 passed | exit 0 | 6 | 67,243 | 57.852 s |
| optional docs `267991` | 6 passed, 4 failed on one generated report | exit 1; attempted next request was rejected at the 8-POST limit | 8 | 95,958 | 104.127 s |

All checks within a row assess **one task outcome**, not independent tasks. Optional docs failures include wrong total hit tokens, overall hit rate, resident block count and a sample hit; the report exists. The `skills_prompted` receipt field lists paths and does not distinguish forced from optional wording; actual wording is in [`run_skill_episode_docs8192.py`](run_skill_episode_docs8192.py), and reading must be checked against raw tool events, not inferred from that field. The HTTP proxy cap denial is not a model response; docs_available could have behaved differently with a higher budget. No-skill had an incomplete last request; it could have repaired its output. There is no evidence of dynamic skill selection or causal effects beyond the explicit one-sample observations.

## Cost, evidence and next steps

This new batch records 205,286 completed-step tokens including cache, plus UNKNOWN consumption for the no-skill timed-out final request; prior six-episode batch records 349,167 known plus the earlier unfinished request UNKNOWN. Combined known event total 554,453 tokens, with at least two unresolved POST usages. Token totals are event accounting, not verified backend billing; no training, paid API, or production writes were used.

GB10 evidence root `/home/testuser/wzh/research_evidence/agent_skill_method_20261029/` contains:

- `llm-prefix-cache-replay__no_skill__258386/`, receipt SHA `af70e1af34121cb5c0045a78984c276cdc79e5d5965579ad0d482e515d54fbd8`, raw SHA `f2c8a3433a895c5703be80ad2c50eef5289ec25e70396d4a02b4040c7d5b40c8`.
- `llm-prefix-cache-replay__all_skill__263034/`, receipt SHA `be83fcb6ea598934d7d99adffbf7e6f5ba948ad976940fa0cd0fd473e24b3b61`, raw SHA `d958631d0b4c3851c35c390e789cab137e3ad566387d2f6bec594444c7b67821`.
- `llm-prefix-cache-replay__docs_available__267991/`, receipt SHA `0d4b8a7e9518503e76ed4d25ae6e76abba74b3ec80d6e2361305d5ba80e9546d`, raw SHA `b1f3239ea7fa7833fdf92541bd974ff592aaca9c87be873e270a8d50d09e061d`.
- Driver [`run_skill_episode_output8192.py`](run_skill_episode_output8192.py) SHA `4111a0be97845740769722e2e596871d51c7693d14d2372d7f6931b4d06e7afb`; docs driver SHA `800609ec7d346185169436cdd27a6e9bdbdeb471578210048f354fe564a5917e`. Driver source preserves the exact common instruction and forced-vs-optional reference wording.

All three receipts are copied locally, and raw events, logs, outputs, and task inputs remain on GB10; no older evidence was overwritten. Next compare repeats and a second source family with sufficiently independent task/oracle, equal total budgets and a predeclared usable-document baseline; investigate tool/timeout failures as separate outcomes. Do not infer a new skill method from these development observations.
