# TAT-QA WP-2 S4-S7 Execution Report

> task: `tatqa-wp2-s4s7-20261014` | date: 2026-10-14 | loop: A
> final status: `BLOCKED_BRIDGE_FAILURE`
> boundary: S4-S7 only; no S9; zero judge, training, write-back, database, external-network, or production-service calls

## 1. Outcome

The card stopped at the first S4 plan-stage actor response. The runner made one counted actor request attempt, then failed when the returned plan text could not be decoded as JSON (`Expecting value: line 1 column 1 (char 0)`). No tool calculation, consume-stage request, episode completion, or feedback context construction occurred. Under the card's stop rule, S5-S7 were not started.

The authoritative failure receipt is [`S4_HISTORY_FAILED_ATTEMPT_RECEIPT.json`](S4_HISTORY_FAILED_ATTEMPT_RECEIPT.json). It counts the service-reported request and discloses that the first runner version did not persist the response text, request id, token usage, or elapsed time before raising. Those fields are left null rather than reconstructed or fabricated.

## 2. Completed before the stop

| Step | Status | Evidence |
|---|---|---|
| F2 artifact verification | `PASS` | [`ACTOR_ARTIFACT_VERIFICATION_RECEIPT.json`](ACTOR_ARTIFACT_VERIFICATION_RECEIPT.json), SHA-256 `f74363bda60816a5da6a47504c11e6dd9f9063e3c6dc5a870ddbc027e2f38b35` |
| F3 actor/tool/environment record | `PASS_WITH_SERVICE_PATH_DISCLOSED` | startup receipt in `/tmp/tatqa-wp2-actor-20261014/STARTUP_RECEIPT.json`, SHA-256 `455fda13c19ace6239b346f67347e444a0b0d478a48b911f121562507f7e6d74` |
| P2 feedback-right v1 | `IN_FORCE` | [`WP0_TATQA_FEEDBACK_RIGHT_CONTRACT_v1.md`](../../../docs/research/WP0_TATQA_FEEDBACK_RIGHT_CONTRACT_v1.md), SHA-256 `c597be967a04a93f36d696614c0a1d78ef61f5afe68cf1c0f23b6fec6e9799db` |
| Actor call path | `READY_THEN_STOPPED` | local Transformers greedy-completion server on `127.0.0.1:8112`; process stopped and port released |
| S4 | `BLOCKED_AT_EPISODE_1_PLAN` | one actor request attempt; zero completed episodes |
| S5 | `NOT_STARTED` | card stop rule |
| S6 | `NOT_STARTED` | no real completed episodes |
| S7 | `NOT_STARTED` | incomplete prerequisites and stop rule |
| S9 | `NOT_STARTED` | explicitly excluded from this card |

## 3. Actor revision and verification

- Actor: Qwen3-8B `b968826d9c46dd6066d109eabc6255188de91218`, licence `apache-2.0`.
- All 15 top-level model files were rehashed on the execution host. Five safetensor shard SHA-256 values, six LFS SHA-256 identities, nine git-blob identities, all file sizes, and all validation-receipt content hashes matched.
- Current software pins were recomputed from disk: `checker_v2.py` `aeedf62b…d048`, `adapter.py` `dbb5b55b…2477`, `provenance.py` `75c3de…4cc3`.
- Frozen settings were temperature `0`, greedy single-shot decoding, max output `512`, input cap `4096`, experience cap `600`, and no automatic third-round repair.

## 4. Call path and failed startup evidence

No compatible Qwen3-8B actor service was already listening. The existing `:8004` model, `:8006` vLLM service, and other production services were not called or restarted.

The first local vLLM container invocation rejected the unsupported `--disable-log-requests` argument before model loading. A second vLLM invocation reached engine initialization but failed with `CUDA error: out of memory`; it exited without serving or producing a model response. The service was then started through the frozen local Transformers runtime using the exact command recorded in `/tmp/tatqa-wp2-actor-20261014/start_transformers_command.txt`.

The Transformers service loaded the pinned model from the read-only model root, exposed only `127.0.0.1:8112`, and returned a READY health response. Host memory before loading was `38,055 MB available`; after loading it was `20,541 MB available`, with host used memory below the 85% stop threshold. After the S4 bridge failure, the service was terminated; `:8112` was confirmed free and available memory returned to `37,062 MB`.

## 5. Budget and safety accounting

| Surface | Used | Limit | Result |
|---|---:|---:|---|
| Actor request attempts | 1 | 40 in this card / 300 globally | within budget; stopped for bridge failure |
| Transport retries | 0 | 4 | PASS |
| Judge calls | 0 | 0 | PASS |
| External network calls | 0 | 0 | PASS |
| Database calls | 0 | 0 | PASS |
| Training or memory write-back | 0 | 0 | PASS |
| Pilot/S9 calls | 0 | not authorised here | PASS |

## 6. Why no S6 or S7 receipt was produced

S6 requires real executed history episodes. S7 requires complete item/split, actor, feedback, context, budget, analysis, pilot-order, and software freezes. Because S4 did not complete one episode, producing E/C blocks or a `PREREG_v1` freeze would misrepresent the evidence and was prohibited by the card.

## 7. Required next decision

Do not resume this card automatically. A new bounded card must first define and freeze the runner's plan/consume bridge, persist every request attempt immediately (including response hash, request id, tokens, exit, and elapsed time), and decide whether the non-JSON response is a canary stop requiring a new actor-service protocol. The one consumed attempt remains permanently counted against the global budget.
