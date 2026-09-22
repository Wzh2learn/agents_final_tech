# Claude Code Project Guide

> 状态: 活跃（Loop C 薄指针） | 更新: 2026-09-22 | 取代/被取代: 无

Claude Code must follow the repository-wide instructions in [`../AGENTS.md`](../AGENTS.md). Current implementation status is maintained in [`../memory/STATE.md`](../memory/STATE.md); do not duplicate either source here.

## Required Reading

Before changing code, read:

1. `../README.md`
2. `../memory/STATE.md` (current snapshot; HANDOFF.md is frozen history)
3. `17_Graph_Engineering_多层Loop设计.md`
4. `21_基础设施盘点与gap解决规划.md`
5. `INDEX.md` (doc map)

## Project-Specific Notes

- The application is FastAPI-based. Do not introduce Flask response patterns into new routes.
- Keep Web routes in `src/web/routers/`, business logic in `src/biz/`, reusable tools in `src/tools/`, and the OpenCode adapter in `src/mcp_server/`.
- The existing `RAGService` and PostgreSQL/PGVector data are the single knowledge backend.
- The first MCP version is read-only. Write, delete, re-index, OCR, and evaluation operations require an explicit reviewed task.
- `opencode.json` points to a GB10-local OpenAI-compatible endpoint; credentials and machine-specific overrides must remain outside Git.

Use Python 3.12. Because this repository uses a `src/` layout, set `PYTHONPATH=src` when running tests directly.
