# Claude Code Project Guide

> 状态: 活跃（Loop C 阅读指引，薄指针，以根 AGENTS.md 为准; 09-11 指针目标已逐个核验 = **9/9 存在**（承 A19 引用校验姿势, 只核不改）） | 更新: 2026-09-11（09-11 neat 批（决策 22）**刷元数据 + 指针核验**: 正文零改动。本件共 10 处路径型引用、去重后 **9 个唯一目标全部存在**（含 `../AGENTS.md`、`README.md`、`memory/STATE.md` 等）⇒ 与 08-23 审计复核所记「指针仍有效」一致; 前序 2026-08-23（08-23 审计复核: 指针仍有效, Loop C 配属以根 AGENTS.md 注册表为准） 保留作轨迹） | 取代/被取代: 无

Claude Code must follow the repository-wide instructions in [`../AGENTS.md`](../AGENTS.md). The detailed Agent architecture and implementation status are maintained in [`AGENTS.md`](../AGENTS.md); do not duplicate or override those facts here.

## Required Reading

Before changing code, read:

1. `README.md`
2. `memory/STATE.md` (current snapshot; HANDOFF.md is frozen history)
3. `docs/17_Graph_Engineering_多层Loop设计.md`
4. `docs/21_基础设施盘点与gap解决规划.md`
5. `docs/INDEX.md` (doc map)

## Project-Specific Notes

- The application is FastAPI-based. Do not introduce Flask response patterns into new routes.
- Keep Web routes in `src/web/routers/`, business logic in `src/biz/`, reusable tools in `src/tools/`, and the OpenCode adapter in `src/mcp_server/`.
- The existing `RAGService` and PostgreSQL/PGVector data are the single knowledge backend.
- The first MCP version is read-only. Write, delete, re-index, OCR, and evaluation operations require an explicit reviewed task.
- `opencode.json` points to a GB10-local OpenAI-compatible endpoint; credentials and machine-specific overrides must remain outside Git.

Use Python 3.12. Because this repository uses a `src/` layout, set `PYTHONPATH=src` when running tests directly.
