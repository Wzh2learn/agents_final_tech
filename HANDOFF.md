# Development Handoff

## Snapshot — 2026-08-01 (8h delivery loop complete)

### 8h Delivery Loop: Runnable -> Deliverable

All 6 phases complete. System now has: client demo doc (docs/19), deployment
guide (docs/20), Docker Compose, multi-turn M2 chat, 98+ tests, 11 demo
screenshots. M1 100% parse rate, M2 15/15 RAG QA + multi-turn sessions.
Git aligned at c0eb55e. Loop B continuous PASS. See docs/18 section 17.

### Latest: M2 RAG QA API + Harness Tools (2026-07-31 evening)

M2 RAG QA endpoint live at :5050/api/m2/ask (1021ms response). QA suite
expanded to 15 queries, 100% correct (13 answerable + 2 documented gaps).
Qwen harness tools CLI (web_search, code_interpreter, web_extractor) integrated
into Loop A/C workflows. Loop C R7 ACCEPTED (4th consecutive). Loop B PASS
covering HEAD. Git aligned at 538fb08.

### 8h Autonomous Loop Summary (2026-07-30 night → 2026-07-31 morning)

Graph Engineering four-layer loop ran overnight: 8 Loop A tasks, 6 Loop C
audits, Loop B continuous PASS. M1 parse rate went from 20% to **100%** on all
5 real client samples. M1→M2 RAG closed loop verified (3/3 QA correct). OCR
parallelized 200s→74s. Reconcile disposition field added. 15 git commits.
Loop C reached 3x consecutive ACCEPTED, audit frequency reduced to 12h.
72B model evaluated and rejected (degenerate on structured extraction).
PaddleOCR-VL still broken (transformers compat); vision-8004 fallback handles
all OCR. See `docs/18_overnight_loopD_neat_closeout.md` for full report.

**Current state**: Loop B daemon running (30min cycle, all PASS). Loop A
standby. Loop C 12h frequency. :5050 M1 harness healthy (workers=2). :8004
and :8005 model services healthy. Git aligned at fe5d662 (local = remote =
GitHub).

### Previous snapshot — 2026-07-28

Start with the approved joint-data plan: [docs/13_M1_M2联合数据闭环计划.md](docs/13_M1_M2联合数据闭环计划.md), then read [docs/12_阶段收尾与对外汇报.md](docs/12_阶段收尾与对外汇报.md).

The existing Web application and `RAGService` remain the sole source of truth
for documents, collections, retrieval, and traceability.  The OpenCode path is
a thin, read-only MCP adapter; do not create another vector store or bypass
`RAGService` with direct database queries.

## Completed and verified

- The read-only MCP surface is implemented: `knowledge_search`,
  `knowledge_list_collections`, and `knowledge_get_source`.
- The OpenCode provider and logical M1/M2/verifier agent definitions are
  configured. They are configuration, not a completed multi-agent workflow.
- Qwen3-14B is the validated local generation-service path for OpenCode/MCP.
  This is historical service validation, not evidence that a service is running
  now.
- Formal read-only OpenCode/MCP stability verification completed: **20/20
  passed**. The inherited process-descriptor lifecycle bug was fixed.
- Focused tests for MCP contract, stability runner, and M2 fixture/evaluator:
  **19 passed, 6 deprecation warnings**.
- A 20-case synthetic/sanitized M2 fixture and evaluator are committed.
- The first public validation baseline is complete on TAT-DQA official converted JSON:
  20 documents, 627 parsed blocks, and 100 questions were run through the existing
  `RAGService` with local Qwen3-Embedding-0.6B and Qwen3-14B. Document Recall@5 is
  0.81, evidence-block Recall@5 is 0.50, evidence MRR is 0.4132, answer exact match
  is 0.24, correct evidence citation rate is 0.48, and mean end-to-end latency is
  3.079 seconds. This is an M2 parsed-input upper bound, not an M1/PDF result.
- A separate read-only Vision MCP implementation exposes `vision_ocr_extract` through an
  isolated vision interpreter. It restricts images to configured roots and model selection to
  server-side keys; it does not change `jinrong-rag`, databases, or documents. This implementation
  is not an OCR quality baseline or proof that an inference service is running. Discovery-only
  protocol smoke passed on 2026-07-21; the required real call is blocked because the documented
  public Chinese newspaper demo image is absent from the available filesystem. No OCR text or
  fabricated resource result is recorded.
- A separate read-only Tabular MCP implementation exposes `tabular_classify` through an MCP
  interpreter that never imports tabular model packages at startup and an isolated tabular child
  interpreter. Protocol discovery and desensitized synthetic TabPFN v2 and TabFM chain calls were
  verified on 2026-07-21 (success; each used 8 training rows, 3 prediction rows, and 3×2 output;
  0.912 and 0.616 seconds respectively); this validates the controlled invocation path, not
  business accuracy or formal M1/M2 metrics.
- OpenCode lists all three MCP servers as connected. The dedicated `tabular-runner` primary agent
  was verified end to end on 2026-07-21: it selected `tabular_classify`, supplied valid typed arrays,
  and completed the sanitized TabPFN chain in about 26 seconds overall (1.013 seconds inference).
  The earlier apparent three-minute hang was SSH waiting on inherited output descriptors. Automatic
  delegation from a coordinator to the `tabular-researcher` subagent remains unverified.

## Current execution state and next work

At the 2026-07-21 closeout, no evaluator or Codex execution task was active.
The local generation listener and PostgreSQL/PGVector container were still
running as reusable infrastructure. Runtime state can change independently of
Git, so verify it before any integration command; do not restart a model merely
to inspect documentation.

### Local M1 display draft (not yet verified)

### M1 display workbench (complete, verified 2026-07-28)

The M1 display workbench is complete and verified on both Windows and Linux
aarch64 (GB10). Files: `src/biz/m1_service.py`, `src/web/routers/m1.py`,
`src/web/templates/m1.html`, `src/web/static/m1.css`, `src/web/static/m1.js`,
`tests/test_m1_service.py` (18 tests passing). The preamble bug was fixed
(paragraphs before the first rule heading are no longer emitted as rules).
Flow: source text -> structured rule candidates -> Pydantic validation ->
non-persistent human-review decision -> M2 handoff payload. It remains a
deterministic text-rule baseline, not an OCR/VLM result.

### GB10 Codex CLI configuration (complete, verified 2026-07-28)

Codex CLI 0.145.0 configured with Token Plan:
- Default: `qwen3.8-max-preview` (direct Responses API, xhigh)
- Chat-only models (`glm-5.2`, `deepseek-v4-pro`) via `responses2chat_proxy.py` on `:8100`
- Model switch: `bash ~/switch_codex_model.sh <model|use-case>`
- tmux launcher: `bash ~/start_codex_tmux.sh`
- Sandbox bypass required: `--dangerously-bypass-approvals-and-sandbox`
- neat-freak skill v3.0.0 installed at `~/.codex/skills/neat-freak/`

### Overnight experiments (launched 2026-07-28)

Four autonomous experiment rounds completed via Codex CLI on GB10:

**Round 1 (completed):**
- Retrieval ablation: vector/BM25/hybrid weights make no difference on 627-block set;
  top_k is the only effective variable (10 -> 0.85 Doc R@5, 3 -> 0.77 down). LLM rerank timeout.
  Output: `docs/experiments/2026-07-28_retrieval_ablation.md`
- M1 baseline: deterministic Chinese regex produces 0 rules on English TAT-DQA (expected);
  OCR not a bottleneck (99.9% char overlap on digital PDFs).
  Output: `docs/experiments/2026-07-28_m1_baseline.md`

**Round 2 (completed):**
- Cross-encoder rerank (bge-reranker-v2-m3): G strategy (top_k=10 -> rerank -> 5) is optimal:
  Doc R@5 0.85, EM 0.28 (+17% over baseline), rerank latency 0.06-0.13s/q.
  Output: `docs/experiments/2026-07-28_rerank_experiment.md`
- M1 LLM extraction prototype: Qwen3-14B zero-shot structured extraction works on
  English financial docs (4/5 company names, 18 metrics from QuickLogic 10-K).
  Output: `docs/experiments/2026-07-28_m1_llm_extraction.md`

**Round 3 (in progress):**
- `codex-integrate`: Integrate G strategy into default config + chunking granularity ablation
- `codex-m1-batch`: Full 274-doc dev split LLM batch extraction

## Current best metrics (TAT-DQA validation, 20 docs, 100 questions)

| Metric | Baseline | Best (G strategy) |
|--------|----------|-------------------|
| Doc Recall@5 | 0.81 | **0.85** |
| Evidence Recall@5 | 0.50 | 0.50 (bottleneck) |
| Evidence MRR | 0.4132 | 0.4098 |
| Answer EM | 0.24 | **0.28** |
| Citation Rate | 0.48 | 0.48 |
| Latency | 3.5s | 3.55s |

## Key findings and next steps

1. Evidence block recall 0.50 is the main bottleneck; chunking granularity experiment running
2. G strategy (top_k=10 + bge-reranker-v2-m3 -> top-5) recommended as new default
3. M1 LLM extraction is viable for English docs; deterministic regex only for Chinese rules
4. bge-reranker-v2-m3 rerank adds negligible latency (0.06-0.13s vs LLM >600s)

1. DATA-2 is complete and verified: `docs/datasets/tat-dqa-joint-v1-manifest.json` fixes 100
   public documents and 500 public question IDs at seed `20260722`, with 60/20/20 document
   splits, required answer-type coverage, no document leakage, and preserved official boundaries
   (`train -> train`, `dev -> validation`, `test_gold -> test`). Focused verification is 9/9.
   DATA-1 is complete: all seven official files match 1,514,773,595 cataloged bytes,
   all four JSON files parse, and all three ZIP CRC checks pass. A 516,964,298-byte
   interrupted train archive was completed through the Range-validated resumable downloader.
2. Commit only scripts, tests, the public-ID manifest, data card, and sanitized aggregate checks.
   PDFs, converted JSON, rendered pages, indexes, logs, and raw outputs remain under
   `~/wzh/datasets/tat-dqa/` or another approved external data root.
3. The official converted JSON -> existing knowledge base -> M2 validation upper bound is frozen.
   Next compare vector/BM25/hybrid/rerank as single variables, then compare traditional PDF
   extraction and Vision MCP/OCR on the same manifest.
4. Report M1, retrieval, answer, end-to-end, Agent, latency, and resource metrics without mixing
   protocol smoke results with business quality.
5. Freeze the untuned baseline before preparing SFT/DPO from the training split and real baseline
   failures. Only after the single-agent joint loop is measured should automatic multi-agent
   delegation be attempted.
6. Treat tabular protocol discovery and synthetic chain validation as operational checks only.
   Formal business metrics require an approved tabular dataset, evaluation protocol, and human
   review; none are available as of 2026-07-21.
7. Complete the local M1 display draft before touching GB10: finish the static assets, correct
   preamble handling, add service/API tests, start the local FastAPI app, and capture a browser
   check. Only then commit and let the development machine pull the same revision for an
   integration check.

Do not start LoRA/QLoRA, unrelated model/dataset downloads, or full multi-agent orchestration
before `joint-v1` and its reproducible untuned baseline exist.

## Guardrails

- Read `AGENTS.md`, `docs/AGENTS.md`, and this file before changing work.
- Keep model weights, environments, credentials, runtime logs, source mappings,
  and private business samples outside Git.
- Use the documented environment variables locally; never place their values in
  docs, commits, terminal captures, or reports.
- Preserve the read-only MCP boundary unless a reviewed task explicitly changes
  it.
## Real counterparty-statement business alignment (2026-07-28)

The actual client M1 task is **counterparty-statement / report parsing + header
synonym mapping**, not free-text rule extraction: each broker/fund uses different
column headers, and M1 must parse the table, map source headers to standard fields
via a synonym table (e.g. product name <-> fund name / account name / full name /
security abbreviation), extract header-region key/value pairs, and emit standardized
records for M2 data-analysis QA. Real samples + `m1_table_schema.json` live in
`~/wzh/m1_samples/` on GB10 (outside the repo, never committed; reports desensitized).

Prior M1 work is retained and remapped, not discarded:
- Contract layer (`m1_service.py` schema / pipeline stages / M2 payload) -> validation layer.
- Display layer (`m1.html`/`m1.css`/`m1.js` four-panel workbench, review buttons, M2 payload
  copy/download) -> reuse as the statement-parsing workbench (data model ExtractedRule ->
  StatementRecord; interaction paradigm unchanged).
- LLM fallback (`m1_llm_extract_prototype.py`, zero-shot, /no_think) -> fallback for unmapped /
  headerless / complex tables and cross-validation.
- Multi-agent skeleton already in `opencode.json` (m1-extraction / m2-qa /
  evidence-verifier / tabular-researcher with permissions) -> the multi-agent verification
  backbone, now activatable in principle (config + samples + engine present), but OpenCode multi-agent automatic delegation has NOT been verified end-to-end as of 2026-07-28; treat as 'ready to activate', not 'verified'.

Adopted architecture (layered parse): deterministic synonym mapping first pass -> LLM fallback
second pass -> arithmetic-reconciliation + evidence verification third pass (financial
statements give hard check constraints: detail market-value sum == total amount, currency
consistency, date format) -> data-analysis QA over the standardized table (m2-qa / Tabular
MCP) -> orchestration and final answer by the GB10 default model.

Remote GB10 loops 2026-07-28 night: `codex-integrate` done (G strategy integrated, commit
98bc82e), `codex-m1-batch` DONE but only 190/274 (hit 60-min budget wall; the report title 'full dev split' is misleading), company-name extraction 47.9% non-null (JSON-valid 100% != entity-usable). NOTE: TAT-DQA retrieval best EM 0.28 is retrieval-side and unrelated to counterparty-statement M1; do not conflate, `codex-m1-real` finalizing the real
statement-parser prototype + header mapping.
## Strategic pivot + TAT-DQA freeze (2026-07-28, user-confirmed)

User-confirmed strategic pivot: the four TAT-DQA rounds are a **general-methodology
v0**; the priority now is to build the **client counterparty-statement M1** well first,
and return to the more general methodology only in a later research phase. Therefore
TAT-DQA retrieval / ablation / llm-batch experiments are **FROZEN** (paused, not
deleted; numbers retained as a research baseline). Stop opening new TAT-DQA loops;
spend remote Codex loops on counterparty M1. (Distinct from the older "frozen M2
parsed-JSON upper bound", which is a frozen number, not a paused activity.)

Re-ranked asset priority: m1-statement (parse + header mapping + reconciliation) =
live client mainline; m1_service contract layer / m1 display workbench / LLM fallback
= mainline components; TAT-DQA four rounds = frozen reserve. The integrated G
retrieval strategy (TAT-DQA EM 0.28) is the live M2 retrieval default but orthogonal
to client M1 -- report separately.

Client M1 north-star metrics: column-alignment coverage, mismatch rate
(reconciliation-falsifiable), unknown-header cold-start -- NOT TAT-DQA EM/Recall.
LLM role in M1 repositioned to "suggest mappings / fill synonyms for unknown headers"
+ hard-case fallback (the 47.9% company-name figure is a 3000-char truncation design
flaw, not a model verdict), with its own eval. Multi-agent auto-delegation remains a
to-verify subtask inside the mainline (config+samples+engine present, never verified
end-to-end; do not claim verified).

Remote loop terminal state 2026-07-28: all three committed (281089b integrate /
d42787f m1-real / dcfa161 m1-batch) and rebased onto the doc-correction commit; three
empty tmux sessions (codex-integrate / codex-m1-batch / codex-m1-real) remain harmless;
llama-server :8004, responses2chat proxy :8100 and FastAPI :5000 are reusable infra,
left running. coding-jinrong tmux is the user's own session, untouched.


## Overnight experiment results (2026-07-29 morning check)

All four client-M1 loops completed via autonomous supervisor chain:

- **A (schema+reconcile)**: headline hit rate 52.4%->66.7%; boshi KV 0->2; reconciliation
  caught silent mismatches (持仓数量<-在途数量 now visible unmapped). commit b2c6ea7.
- **B (OCR fallback)**: 0/7 real samples (PaddleOCR-VL ~14-18 char/s too slow for full-page
  on GB10); synthetic self-check 7/7 proves pipeline works. Not a mapper defect.
  commit 484f607.
- **C (LLM header mapping)**: 32 unknown columns, 15 pass reconciliation gate, unmapped
  39->23; counterfactual self-test proves gate is not rubber-stamp; rows=0 tables are
  blind spot requiring human review. commit e83fb23.
- **D (multi-agent delegation)**: single-hop verified correct (matches direct parser);
  auto-delegation unreliable (neutral prompt -> direct tool call); two-hop BLOCKED
  (verifier reads 215KB JSON > 16K context). commit 917e7c5.

**Qoder CLI recon**: isolated install OK, protocol compatible with :8004/:8100,
but BLOCKED-auth (needs Qoder account PAT). commit 2d018a8.
See docs/16 for migration plan; docs/experiments/2026-07-29_qoder_recon.md for full report.

**Git reconciled**: local = remote = GitHub = 2d018a8 (2026-07-29 08:30 CST).


## Client supplementary requirements (2026-07-29)

From client screenshot and verbal feedback:

1. **KV table as first-class table type**: The client system treats "表头信息"
   (header info) as a standalone table with layout type `kv` (key-value), not just
   a side-car `header_meta_fields` dict. It has its own table name ("表头信息"),
   layout selector ("键值(kv)"), header-region keywords, and field synonym list
   (same fields as grid tables: 产品名称/管理人/对账日期/券商/托管行/合计金额/单位净值).
   Our schema should model this as a table entry with `layout: "kv"` rather than
   a separate `header_meta_fields` section.

2. **No-table-name fields**: Client asks "没表名的也可以想想怎么单独处理" — fields
   like "风险等级到期时间" that appear in documents without belonging to any named
   table. These need a fallback: either a catch-all "unattributed" table, or a
   document-level field extraction pass that runs after table detection.

3. **Expanded synonyms** (from updated screenshot): 对账日期 now includes
   对账期间/打印日期/起止日期/开始日期/结束日期; 合计金额 now includes
   总资产/净资产/资产市值/参考市值; 产品名称 now includes 姓名/客户姓名;
   单位净值 now includes 份额净值.

These are schema-level improvements for the next M1 iteration (after the current
compact-summary loop completes). Not blocking the current loop.
