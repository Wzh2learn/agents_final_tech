# Development Handoff

## Snapshot — 2026-07-22

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

1. Implement DATA-1 and DATA-2 from the task list: download and validate the CC BY 4.0 TAT-DQA
   package outside Git, then create the deterministic `joint-v1` subset with 100 documents,
   at most 500 questions, document-level 60/20/20 splits, and seed `20260722`.
2. Commit only scripts, tests, the public-ID manifest, data card, and sanitized aggregate checks.
   PDFs, converted JSON, rendered pages, indexes, logs, and raw outputs remain under
   `~/wzh/datasets/tat-dqa/` or another approved external data root.
3. Run the official converted JSON -> existing knowledge base -> M2 path first to establish an
   upper bound. Then compare traditional PDF extraction and Vision MCP/OCR on the same manifest.
4. Report M1, retrieval, answer, end-to-end, Agent, latency, and resource metrics without mixing
   protocol smoke results with business quality.
5. Freeze the untuned baseline before preparing SFT/DPO from the training split and real baseline
   failures. Only after the single-agent joint loop is measured should automatic multi-agent
   delegation be attempted.
6. Treat tabular protocol discovery and synthetic chain validation as operational checks only.
   Formal business metrics require an approved tabular dataset, evaluation protocol, and human
   review; none are available as of 2026-07-21.

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
