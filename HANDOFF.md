# Development Handoff

## Snapshot — 2026-07-19

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

## Current stopped/idle state and next work

No runtime state is assumed after this documentation closeout. Check services
and Git state before any integration command; do not start a model merely to
inspect documentation.

1. Obtain an owner-approved local mapping from synthetic M2 labels to stable
   source labels, plus human answer-quality annotations.
2. Run the existing M2 evaluator only after that approval; report Recall@5,
   source-hit/refusal metrics, latency, and human review. Until then, **formal
   M2 business metrics are blocked**.
3. Build an approved M1 OCR/rule-extraction dataset and complete its first
   numeric baseline. As of 2026-07-19, no M1 numeric baseline exists.
4. After single-agent M1/M2 evidence loops are measured, hand the frozen API,
   datasets, and results to the engineering teammate for orchestration,
   permissions, state, and integration.

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
