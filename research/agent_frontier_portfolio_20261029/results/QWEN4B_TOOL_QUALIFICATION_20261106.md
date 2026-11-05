# Qwen3-4B and 8B OpenCode tool qualification — 2026-11-06

**4B decision: PARTIAL_TOOL_INTERFACE_PASS_SEMANTIC_TASK_FAIL.** The model issued native OpenCode read, write and bash calls in a network-isolated task, but did not write the required numerical result. The subsequent 8B check completed the file and verification actions but hit the request cap before a final response. This is one fixture-level integration probe, not a measurement of general agent task capability or a learning-method comparison.

## Setup

- GB10 GGUF: `/home/testuser/wzh/models/gguf/qwen3-4b/Qwen3-4B-Q4_K_M.gguf`; SHA-256 `7485fe6f11af29433bc51cab58009521f205840f5b4ae3a32fa7f92e8534fdf5`. OpenCode SHA-256 `915ca1cd9eb5a7b3e15bd89dc71c38cf0caa9a02d13c5371422675b4b370bffb`; llama-server SHA-256 `037e02419e78256ed4227af31fc0b2602ff04c670fb7ad4fa2429fafb03bd55d`.
- Separate loopback service `127.0.0.1:18104`; health returned `ok`. The second episode used `-c 32768 -n 4096 -np 1 --no-context-shift --jinja`, alias `qwen3-4b-qual`. Initial episode used output 8192 and automatic parallel slots. The research service was started independently; existing endpoints were not restarted.
- Actor: `python:3.12-slim` container with `--network none`, read-only image, restricted capabilities, writable task workspace and a UDS relay allowing only the dedicated chat/model routes. Task prompt names the fixture but does not contain its values; the expected result is checked outside the agent. The sandbox is specific to this probe, not a general security certification.
- Private evidence: `/home/testuser/wzh/research_evidence/agent_learning_20261030/qwen4b_qualification_20261106/`, including both harnesses, original raw events, receipts and separate server logs. The fixture is the same in both episodes; the second is an engineering retry, not an independent sample.

## Results

| Episode | Calls | Actual outcome | Boundary |
| --- | --- | --- | --- |
| 01 | 1 forwarded POST; next request denied | Read succeeded. A bash call failed with a missing parenthesis; no result file. | The 45,000-byte cumulative request-body guard rejected the next POST before forwarding. This is an infrastructure limit and prevents judging whether the model would have recovered. Agent exit 1. |
| 02 | 2 forwarded POSTs | Read, bash and write were invoked. Agent exit 0; final prose stated the correct sum, 175, but `result.txt` contained shell code rather than the number. Independent byte-exact check failed. | Its bash check selected only negative lines, then matched an empty pattern, so exit 0 did not validate the result. The agent incorrectly treated that check as confirming success. The exact raw command, fixture, result, checker and JSON receipt remain private. |

Second-episode harness hash: `8342550914d4fd1e649134b1875409029f749ceb8e22c78b8f63ad6326e07803`; episode-01 raw SHA-256 `8f7c4581ddd6f74d724e2e22335cac274e9471801906f674a84172bda799c7a1`; episode-02 raw SHA-256 `4f609334453f59e1df2a6b6c56475107c4746dfe9ba092309115f70053dc2ea2`.

## Budget and next use

Actual OpenCode usage by POST: `(input 5101, output 1578, cache read 0)`, `(5101, 756, 0)`, `(458, 660, 5496)`. Sum of reported totals is **19,150 tokens**, including 5,496 cached-input tokens; generation output is 2,994. There were 3 forwarded POSTs overall, with no training. Do not add cache read a second time. The first episode's denied request was not forwarded. Two health GETs targeted only the dedicated service and are separate from model-generation accounting. The second proxy enforced at most three POSTs and a 300,000-byte cumulative request body; service context was 32,768 with context shift disabled and output capped at 4,096.

The first episode shows real native read integration; the second shows all three tool interfaces working, not correct completion. Further work should distinguish tool availability from correct tool use and independent verification; no model-quality generalization follows from this single fixture. Preserve both episodes and account for the retry when comparing future configurations.

The dedicated 4B research server, PID `3172436`, was stopped by its owner after the probe to free port 18104 for the separately authorized 8B check. Its `server_episode02.log` SHA-256 at the handoff was `1717b58612b10256f1ae770bcedb53de95220f4b74a5074e8122cdd935ae2c02`. Existing services were left alone.

## 8B follow-up on the same fixture

**Decision: TOOL_AND_FILE_CHECK_PASSED; FINAL_RESPONSE_BLOCKED_BY_POST_CAP.** `/home/testuser/wzh/models/gguf/qwen3-8b/Qwen3-8B-Q4_K_M.gguf` SHA-256 `d98cdcbd03e17ce47681435b5150e34c1417f50b5c0019dd560e4882c5745785`; its model-metadata template used Jinja with thinking enabled. The dedicated endpoint used context 16,384, output 4,096, one slot and disabled context shift. Its harness hash is `6b2f6b1628657f7c2ad72729a26d2931b5b316b5490e5d9fd00c53adff169a40`; the same isolated task prompt and fixture were used, with a four-POST and 500,000-byte cumulative body guard.

Read, write and bash executed. The agent first wrote `42` and made an invalid `cmp` call; on the next turn a numeric check printed failure. It then wrote `175\n` and reran the check, which printed success. The separately executed byte-exact checker agrees: fixture SHA-256 `37e5257c40b186e60730f2fa36a806d735e7ad2bd40199b7eb2ec111da7a71f0`; result SHA-256 `f0448ca7d8645d6c1d4902a2c058a37abfc44f1de59ab54163c80faaf72f6a4c`. The agent's shell check prints a failure message but does not itself use a nonzero failure exit, so the independent checker remains necessary.

The next request after four completed POSTs was denied by the guard; agent exit was 1 and no final response was observed. The tool/file subtasks passed, but this is not a complete successful agent episode. The raw SHA-256 is `bedd713687ef90d570751b374a4a2ecbd710172d3c0dcd93839f4935b8079e95`; the private evidence is under `episode_8b_01/`. The 8B run used 25,650 reported total tokens, including 18,871 cached input and 1,527 generated output. Both models together used **44,800 total reported tokens** and seven forwarded POSTs; cache is already included. There were three separate health GETs to the dedicated service and two proxy-denied requests across the episodes; no `/v1/models` GET appears in the episode receipts. These are interface qualification runs with different contexts and recovery histories, not evidence of a learning mechanism or a controlled model ranking.

At closeout the dedicated 8B service remained on `127.0.0.1:18104`, PID `3177513`, with `--alias qwen3-8b-qual -c 16384 -n 4096 -np 1 --no-context-shift --jinja -ngl 999`. `server_8b.log` SHA-256 at the check was `db11f9701cbe8826c8d071cb2c8dda0bc299483bb0a2bc8f788131c18638e9b1` (the log can change). To stop only this service, recheck PID and argv first, then `kill -TERM 3177513`.

Coordinator verification independently recomputed all receipt/raw bindings and usage: 24,367 cached input + 15,912 uncached input + 4,521 output = 44,800 reported tokens. It also recomputed the sum from the fixture and checked the actual 8B result bytes, including its newline; no new model call was used. A 27-file review packet (12,965 bytes) is mirrored at `D:/Documents/Loop_D_assets/agent_learning_20261106/qwen_small_model_qualification_20261106.tar.gz` and GB10 private `evidence_packets_20261106/qwen_small_model_qualification/`; SHA-256 `d97feb62291e96a6d574c0a5a0eafef2e8a36fed47a01f4a35e55ae8de1cb409`. It excludes active server logs and model weights; complete original evidence remains at the private root.
