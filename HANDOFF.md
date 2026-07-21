# Development Handoff

## Snapshot — 2026-07-21

Start with the current external briefing: [docs/12_阶段收尾与对外汇报.md](docs/12_阶段收尾与对外汇报.md).

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
- OpenCode lists all three MCP servers as connected. A 2026-07-21 non-interactive
  `tabular-researcher` attempt was stopped after more than three minutes because Qwen3-14B had
  not started the tabular child process. The model API remained healthy and no process was left
  behind. Therefore OpenCode-to-subagent automatic tool selection is not yet end-to-end verified.

## Current execution state and next work

At the 2026-07-21 closeout, no evaluator or Codex execution task was active.
The local generation listener and PostgreSQL/PGVector container were still
running as reusable infrastructure. Runtime state can change independently of
Git, so verify it before any integration command; do not restart a model merely
to inspect documentation.

1. Obtain an owner-approved local mapping from synthetic M2 labels to stable
   source labels, plus human answer-quality annotations.
2. Run the existing M2 evaluator only after that approval; report Recall@5,
   source-hit/refusal metrics, latency, and human review. Until then, **formal
   M2 business metrics are blocked**.
3. Build an approved M1 OCR/rule-extraction dataset and complete its first
   numeric baseline. As of 2026-07-21, no M1 numeric baseline exists. The Vision MCP is only a
   controlled OCR invocation boundary and must be integration-verified separately.
4. After single-agent M1/M2 evidence loops are measured, hand the frozen API,
   datasets, and results to the engineering teammate for orchestration,
   permissions, state, and integration.
5. Treat tabular protocol discovery and synthetic chain validation as operational checks only.
   Formal business metrics require an approved tabular dataset, evaluation protocol, and human
   review; none are available as of 2026-07-21.

Do not start LoRA/QLoRA, new model downloads, or full multi-agent orchestration
before the approved datasets and reproducible baselines exist.

## Guardrails

- Read `AGENTS.md`, `docs/AGENTS.md`, and this file before changing work.
- Keep model weights, environments, credentials, runtime logs, source mappings,
  and private business samples outside Git.
- Use the documented environment variables locally; never place their values in
  docs, commits, terminal captures, or reports.
- Preserve the read-only MCP boundary unless a reviewed task explicitly changes
  it.
