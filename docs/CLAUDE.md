# Claude Code Project Guide

Claude Code must follow the repository-wide instructions in [`../AGENTS.md`](../AGENTS.md). The detailed Agent architecture and implementation status are maintained in [`AGENTS.md`](AGENTS.md); do not duplicate or override those facts here.

## Required Reading

Before changing code, read:

1. `README.md`
2. `docs/02_阶段计划与分工.md`
3. `docs/05_开发任务清单.md`
4. `docs/09_OpenCode与现有RAG_MCP实施方案.md`

## Project-Specific Notes

- The application is FastAPI-based. Do not introduce Flask response patterns into new routes.
- Keep Web routes in `src/web/routers/`, business logic in `src/biz/`, reusable tools in `src/tools/`, and the OpenCode adapter in `src/mcp_server/`.
- The existing `RAGService` and PostgreSQL/PGVector data are the single knowledge backend.
- The first MCP version is read-only. Write, delete, re-index, OCR, and evaluation operations require an explicit reviewed task.
- `opencode.json` points to a GB10-local OpenAI-compatible endpoint; credentials and machine-specific overrides must remain outside Git.

Use Python 3.11. Because this repository uses a `src/` layout, set `PYTHONPATH=src` when running tests directly.
