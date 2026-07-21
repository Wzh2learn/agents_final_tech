# Agent Development Guide

## Source of Truth

All coding agents must read the root `AGENTS.md` first. For product scope and current plans, use:

1. `01_项目背景与目标.md`
2. `02_阶段计划与分工.md`
3. `03_技术架构与模块设计.md`
4. `05_开发任务清单.md`
5. `09_OpenCode与现有RAG_MCP实施方案.md`

Historical reviews under `archive/` are reference material, not current implementation instructions.

## Two Agent Surfaces

The repository contains two related but distinct agent paths:

- `src/agents/agent.py`: the existing LangGraph agent used by the FastAPI application.
- `opencode.json`: OpenCode orchestration using the GB10 local model and the
  isolated knowledge, vision, and tabular MCP servers under `src/`.

Do not merge these paths casually. The knowledge MCP must reuse `RAGService`
and existing business identifiers so the Web UI, API, and OpenCode see the
same knowledge base. Vision and tabular MCPs remain isolated model-invocation
boundaries and must not access or mutate that knowledge store.

## Implemented vs Planned

Implemented:

- OpenCode provider for `gb10/qwen3-14b`;
- local stdio MCP startup script;
- read-only search, collection listing, and source retrieval tools;
- isolated `vision_ocr_extract` and `tabular_classify` MCP tools with bounded,
  server-controlled model invocation;
- MCP unit tests and protocol smoke test;
- logical `m2-qa`, `m1-extraction`, `evidence-verifier`, and
  `tabular-researcher` subagent definitions, plus the direct CLI
  `tabular-runner` primary agent;
- formal read-only OpenCode/MCP stability verification: 20/20 passed, with the
  inherited process-descriptor lifecycle issue fixed.
- desensitized synthetic TabPFN v2 and TabFM MCP calls; these verify the
  invocation path, not business accuracy.

Planned:

- formal M2 business evaluation (blocked on an owner-approved synthetic-label
  to stable-source mapping and human annotations);
- approved M1 OCR/rule dataset, real OCR baseline, and Pydantic extraction
  validation;
- evaluation MCP tools and full coordinator workflow;
- production permissions, state management, and enterprise integration.

Qwen3-14B is a service-validated generation path, not a claim of current
runtime. Agent definitions are configuration, not proof that the complete
workflow is implemented.

## Working Rules

- Keep MCP tools task-level, typed, traceable, and read-only by default.
- Access data through `RAGService`, `DocumentManager`, or stable APIs.
- Preserve `document_id`, chunk metadata, collection, score, and source fields.
- Put model experiments under `scripts/` and results under `docs/experiments/`.
- Keep GB10 model weights and Conda environments outside the repository.
- Mark commands needing PostgreSQL, external APIs, or GPU services as integration steps.

## Verification

```bash
PYTHONPATH=src pytest tests/test_mcp_server.py -v
python scripts/smoke_test_mcp_server.py
opencode mcp list
```

The latter two commands require `PGDATABASE_URL`; the smoke test also requires the dependencies installed in `JINRONG_MCP_PYTHON`.
