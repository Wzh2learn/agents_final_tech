# SkillsBench prefix-cache: first paired agent pilot

2026-10-29. Status: single-task, one-run-per-arm exploratory development, not official BenchFlow, not a held-out confirmation, not evidence of a new skill-selection method.

## What was run

Public SkillsBench v1.1 task `llm-prefix-cache-replay` uses the original 2,000-request trace, config and task statement, Qwen3.6-35B-A3B via OpenCode 1.18.3, no external network and no access to oracle/verifier during agent execution. Both arms have the same 8 POST, 450,000 total request bytes, 300-second wall clock and 4,096 output tokens/step ceilings; no-skill has no skill text and all-skill has both upstream skill files (not an equal-information comparison). Both prompts tell the agent to inspect two trace rows and process the full trace programmatically. No verifier output is fed to the agent. After execution, a separate isolated container runs original verifier assertions under pytest 9.0.1, not official BenchFlow/pytest 8.4.1; task and source qualification are in `../agent_frontier_portfolio_20261029/SKILLSBENCH_SOURCE_QUALIFICATION_AND_PLAN.md`.

| Arm | Actual result | Elapsed | Model POSTs | Event tokens incl cache |
|---|---|---:|---:|---:|
| no skill | no report; verifier 10 fixture setup errors (single missing file), exit 1 | 75.566 s | 3 | 21,339 |
| two original skills | produced report; verifier 10 passed, exit 0 | 58.213 s | 6 | 67,759 |

The no-skill final step terminates with reason `length` and 4,096 output tokens; OpenCode process exit 0 does not mean task success. The skill arm used roughly 3.18 times as many event tokens, with twice as many POSTs, within the same ceilings. This run establishes task- and harness-specific feasibility and a promising paired development signal; it cannot establish a population effect, equal-information advantage, skill generality, or skill selection under environment change. One task and one sample per condition do not resolve sampling variation. Original task, trace and verifier are unchanged; upstream oracle had separately passed the verifier. These are test assertions, not independent task families.

## Environment correction and prior failed runs

The two previous matched trials had a harness bug: bind mount directory belonged to host UID/GID 1001 with mode 775; container uid 0 had `--cap-drop ALL` and thus no DAC bypass, so output creation was denied. This was confirmed in both raw traces (`Permission denied` on `/root/report.json`). A no-model isolated container probe verified that mode 0777 on a newly created synthetic task-only output directory resolves the issue while the root filesystem is read-only, network none, and the verifier/oracle remain unmounted. It does not change the raw tasks or verifier. Older trials are retained; do not count them as skill outcomes.

Six recorded receipts (including older cap/timeout probes) have known sum 349,167 event tokens including cached input; the first timed-out attempt includes an unfinished POST whose backend use is UNKNOWN, so actual total may be higher. The latest two completed runs are 89,098 known tokens and 9 HTTP requests. No training, paid API, or production write. A previously created setup-only folder lacks a receipt; do not assume its request count from file presence alone. Preserve previous failed attempts in accounting.

## Evidence

GB10 private evidence root: `/home/testuser/wzh/research_evidence/agent_skill_method_20261029/`.

- no-skill `llm-prefix-cache-replay__no_skill__241657/receipt.json`, SHA-256 `8f6e50a1fd600154d519c3b6ceef4611bef2d4c0e6b203d46f70c6eebcad3deb`; raw SHA in receipt `6fbdcaa7335210b186b2747cb2f588ef76254d61ac43e8cbecd7a09c60303e16`.
- all-skill `llm-prefix-cache-replay__all_skill__243805/receipt.json`, SHA-256 `34912a15941a14955057643f3de8b10c8465f6fb514f46b0556f3caf538a58e8`; raw SHA `9de736b18153b08d33a7433739d33196c18a4378f7cf831339340be1c0a65cb1`; `work/report.json` SHA `6362432aa9e93c86b896c938560dafabbd2ef68f19958fc96bc1a8512517e457`.
- [`run_skill_episode_writable.py`](run_skill_episode_writable.py) SHA-256 on GB10 `a72812474de2104e5918e45d7f79558bd3aa97653a58a3012aeefb43a196f332`. Raw episodes and public task inputs remain on GB10, not in project Git.

## Next meaningful experiment

Use additional independently qualified public tasks, repeat runs with locked budget, include no-skill/fixed skill/equal-information documentation and same-budget retries, and inspect response truncation. The existing static task is not a naturally observed skill invalidation, and Skill-V already studies applicability: any dynamic-selection claim requires a tested changing environment, stronger baselines and independent source families.
