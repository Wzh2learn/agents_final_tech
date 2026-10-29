# Paper E: controlled Agent evidence on two public-source task families

Date 2026-10-29. Status `NATURAL_SOURCE_DEVELOPMENT` — four real OpenCode/Qwen runs on previously exposed sources, with a **historical** execution result; not a new benchmark, an independent generalization experiment, prospective preregistration, or evidence of a new Agent method.

## Research question

What interpretation changes when an evaluator records evidence beyond a final score? We separately inspect (i) final Agent verdict/choice; (ii) the files actually exposed by completed read-tool events; and (iii) a fixed non-LLM reference. Recording a read is not proof the model used the information, and adding a trace is not itself a new evaluator.

## Four actual isolated Agent runs

The same `gb10/qwen3.6-35b-a3b` provider name and OpenCode 1.18.3 were requested for all four; the running server's exact weight hash was not independently verified in this stage. Each run used the previously qualified `--network none`, read-only Docker and local-only Unix-socket relay, with no host home or hidden reference mounted. Two POSTs to the local model endpoint were recorded for each run; each final answer and raw tool event is retained at the private evidence path below. Read metadata records `truncated=false` for all eight completed reads. This is not a production application test.

| Case | Agent final only | Completed read trace | Fixed comparison / interpretation |
|---|---|---|---|
| NtripBrowser historical BASE candidate | `VERDICT: INVALID` | `/task/module.py` | Historical local test receipt: 7/7 pass. Independent direct-import/call AST contract: INVALID. A behavior-only pass therefore does not establish the migration contract. |
| NtripBrowser historical PROSE candidate | `VERDICT: VALID` | `/task/module.py` | Historical local test receipt: 7/7 pass. Same direct-import/call AST contract: VALID. The test-only score cannot distinguish the two cases under the historical test suite. |
| SciFact query 13 | `CHOICE: A` | query + A + B | Selected A is **UNJUDGED** in official qrels; BM25 also chooses A. B is recorded positive. No independent negative annotation is available for A. |
| SciFact query 36 | `CHOICE: B` | query + A + B | Selected B is **UNJUDGED** in official qrels; BM25 also chooses B. A is recorded positive. No independent negative annotation is available for B. |

The two migration inputs are the BASE/PROSE generated candidates from a previously studied real public repository change, not two independent repositories and not newly generated candidates. Both historical 7/7 results are retained receipts, **not rerun** here. The AST baseline and requested Agent predicate check direct `cchardet` import plus `cchardet.detect` call and absence of the old direct import/call. The AST baseline classifies 2/2 correctly under that narrow contract; the Agent also matches 2/2. This shows no Agent gain over that cheap baseline, does not check aliasing, result consumption, semantic equivalence or a new production deployment, and is not a general failure rate.

SciFact cases were deliberately selected from existing test queries where BM25 top-1 is unjudged and a labelled positive also appears in its top-100, so the selection is post-hoc and not representative. An incomplete qrels file makes either chosen A/B `UNJUDGED`, **not an established error**; conventional closed-world zero treatment is a measurement convention, not an independent relevance verdict. The labelled alternative is positive under qrels, but agent choice of an unjudged candidate does not demonstrate the candidate is irrelevant. A maximum of 6,000 characters per document was configured; the four source texts were 2,379, 2,414, 1,687, and 1,789 characters, so none hit that cap. Task-level correctness remains unresolved until a qualified independent assessment. The outputs are decisions about a fixed two-document subset, not a head-to-head reproducible full-ranking benchmark.

## Three observation layers and limits

| Evidence available | What it supports | What it cannot support |
|---|---|---|
| Final response / historical 7/7 score | Agent emitted a verdict or A/B. Both historical migration candidates pass the selected behavioral tests. | No automatic inference that a model read, used or checked a source; a test pass does not by itself prove the target dependency was migrated. |
| Completed read events | Which actor-visible files and portions the harness actually returned; here all required files returned without read-tool truncation. | No independent proof that content was understood, final reasoning used it, reference is valid, or an unjudged document is irrelevant. |
| Historical tests + independent AST / qrels | Distinguish target migration under the specified direct-call contract; classify the known qrels status as positive or unjudged. | Static pattern is not general semantic equivalence; historical tests do not cover network behavior; missing qrels labels are not negative labels. |

## Cost and failure accounting

This new stage: 4 physical OpenCode runs, 8 observed local model HTTP POSTs; event totals 8,628 / 8,453 / 7,053 / 6,920 = **31,054 tokens**. Non-cache input 9,480, cache-read input 20,367, output 1,207; these sum to 31,054. The wall times in order were 8.34 / 6.58 / 8.28 / 9.14 s. No independent GPU-seconds were measured. No judge, training, paid API, external contact or production-service write was used. Model metadata identifies the requested alias, not a fresh weight hash. The previous six-run isolation/qualification ledger, including two attempts with unknown backend usage, is separate and not reset.

## Evidence and reproduction

Evidence root `/home/testuser/wzh/research_evidence/paper_e_natural_agent_20261029/` contains `reference_hidden.json` (not mounted inside containers), frozen `task_prompts.json`, four actor-visible directories, four raw JSONL streams and receipts, `analysis.json` and full source hashes. Reference SHA-256 `06509b3d070f43782386583b7c4c1dc2d82a7fbd57cb6b51123428ca93438b75`. Each run's raw hash and usage appear in [analysis.json](analysis.json). `natural_agent_prepare.py` computes actor files and reference from existing protected assets; `natural_agent_run.py CASE` calls the model and should not be run for deterministic reanalysis; `natural_agent_analyze.py EVIDENCE_ROOT` recomputes output/trace classification offline. Exact source/candidate/QREL hashes are frozen in the reference. Full benchmark docs and raw events remain in GB10 evidence storage; verify dataset and code licenses before any redistribution.

## External research comparison and article placement

[AgentSuite / COBA (ICML 2026)](https://proceedings.mlr.press/v306/suh26a.html) already audits benchmark component interactions and compares with experts. [Chen, oracle-integrity audit, arXiv v2](https://arxiv.org/abs/2610.16067v2) already uses known-answer controls, actual benchmark correction and replay; [AgentRx](https://www.microsoft.com/en-us/research/blog/systematic-debugging-for-ai-agents-introducing-the-agentrx-framework/) already uses guarded executable constraints and trajectory evidence. Therefore neither separate score/trace/oracle reporting nor these two migration observations establish novel general Agent evaluation theory. The realistic contribution is a transparent, trace-linked **bounded illustration** complementary to Paper E's measurement-contract analysis, with the no-gain strong baseline and UNJUDGED limitations kept visible.

### Candidate paper paragraph — after independent review, not an already-integrated result

> As a development-only extension, we executed an OpenCode–Qwen agent in an isolated read-only environment on two previously generated candidates for one public dependency-migration task and on two selected SciFact two-document choices. Both migration candidates had passed the same seven historical tests, while a direct import/call contract classified one invalid and the other valid. The agent read the candidate code and gave the same classifications as that inexpensive static check; thus these examples do not establish an advantage of agentic inspection. On both retrieval examples the agent chose an unjudged passage, matching the BM25 top-ranked choice. The absence of a qrels judgment does not establish irrelevance, and a completed read event does not prove that the content was used. These controlled examples illustrate the distinct scopes of scores, traces and reference contracts rather than estimating their general efficacy.

Do not add this paragraph silently as a fourth independent case: before venue-specific revision, verify hidden reference and original execution receipts independently, confirm publisher/data licenses and manuscript page limits, and label the demonstrations as post-hoc and source-exposed.

## Next targeted experiment

1. Obtain a separate real migration family with pinned parent/gold and executable tests plus a frozen, falsifiable consumption/behavior reference. Include both realistic successful and failure variants, an alias-aware AST baseline, and verify that any deliberately generated variant is marked as such; use 8–12 independent case units across at least two repositories if qualification permits, not repeated rows treated as independent.
2. For retrieval use queries with **explicit positive and negative judgments** or add independent human expert adjudication, plus a noncircular source-availability reference. Freeze both a positive and negative matched candidate selection before model outputs; include all unjudged/abstaining/failed cases, never impute correctness. Compare same-model final-only, trace-enabled and deterministic strong baselines under matched costs.
3. Estimate an initial development budget of 20–40 physical agent runs and 150k–300k tokens depending on trace length; this is an estimate, not spent resources. First measure reference availability and use staged budget caps with raw event accounting. Decide inclusion in the short paper on both effect and presentation value; a negative result remains informative and must not be spun as positive.
