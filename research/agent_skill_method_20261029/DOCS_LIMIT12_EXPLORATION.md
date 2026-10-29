# Optional documentation: higher request-limit exploratory run

2026-10-29; one post-hoc episode; source/task unchanged; not a repeatability or causal estimate. Earlier 8-request study is retained in [DOCS_AVAILABLE_CONTROL_RETURN.md](DOCS_AVAILABLE_CONTROL_RETURN.md).

To investigate whether an optional-document Agent can eventually produce a passing output, we ran a new independent generation on the same SkillsBench `llm-prefix-cache-replay` with the same optional access to the two upstream skill files, same OpenCode/Qwen, public input, isolation, configured 8,192 output ceiling, 300-second process timeout, and post-agent isolated verifier. The script differs only by increasing the request-count cap from 8 to 12; the 450,000 cumulative POST-body-byte limit remains. This is not a continuation from the earlier trace, uses a fresh generation and is not a controlled intervention on the exact earlier Agent state.

## Observed result

- The Agent read both optional skill files successfully and produced `/root/report.json`.
- The separate original verifier assertions returned **10 passed** under the adapted pytest 9.0.1 environment. The report SHA-256 `6362432aa9e93c86b896c938560dafabbd2ef68f19958fc96bc1a8512517e457` matches the earlier forced-skill run's output file; this does not imply the generated programs are identical. The verifier checks one task; 10 tests are not independent samples. This is not an official BenchFlow execution.
- The OpenCode process exited **1** after the proxy rejected its attempted tenth POST; nine POSTs were forwarded, totaling **434,285 request-body bytes**. The proxy recorded `DENIED_OR_LIMIT` without the rejected request's `Content-Length`, so exceeding the unchanged 450,000-byte cap is plausible but a missing length or another proxy condition cannot be excluded. The exact reason remains unresolved; it did not exhaust the 12-request cap. The output passed despite the process not finishing cleanly; distinguish task-artifact validation from Agent completion.
- Nine completed `step_finish` events total **115,150 known event tokens including cache**. Wall time including verifier was **211.242 s**. No extra missing step usage was observed in this run; backend billing remains independently unverified. No training, paid API or production write.

The earlier optional-doc run had 6 passing/4 failing tests, whereas this new sample passes the same tests. Because it is a separate stochastic run and both request-count and realised trajectory differ, the difference does **not** establish that added requests caused improvement. It also does not establish a population-level method effect or prove an episode-level skill switching benefit.

## Sources and accounting

GB10 evidence `/home/testuser/wzh/research_evidence/agent_skill_method_20261029/llm-prefix-cache-replay__docs_available__278343/` contains `raw.jsonl` SHA-256 `95b4035368f6209fb0292c3a269546e7fca92ca9aea481668f78963df8f00d66`, `receipt.json` SHA-256 `4f176700a222eb65f63bdcf0c67dc583542a10a76ceca533d041afb767986229`, `verifier.txt`, public inputs and `report.json`. The trace SHA-256 is `9e81b386f0d8cea16d376b041d7a7e8fed5ba65b53e989444c76cef408442c2a`. [`run_skill_episode_docs8192_limit12.py`](run_skill_episode_docs8192_limit12.py) SHA-256 `2aed077f100a70634afd0371f2cb170f8cb95c4e86dca4ffd9ce43a583935d4e`. It removes no prior data; a copy of the summary receipt is stored locally.

Prior six-receipt phase: 349,167 known event tokens plus at least one unfinished POST UNKNOWN. Following three-arm 8-request phase: 205,286 known plus another unfinished POST UNKNOWN. This new episode adds 115,150 known; all ten receipts total **669,603 known event tokens** plus at least two prior unfinished POST usages UNKNOWN. These include cached input and are not a verified billed amount.
