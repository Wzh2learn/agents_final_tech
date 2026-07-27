# Repository Guidelines

## Project Structure

`src/` uses a layered FastAPI architecture: `web/` contains routes, templates, and static assets; `biz/` owns application services; `agents/` contains the in-app LangGraph agent; `tools/` implements retrieval and document functions; `storage/` manages PostgreSQL/PGVector, memory, and files. Read-only OpenCode adapters live in `src/mcp_server/`, `src/vision_mcp_server/`, and `src/tabular_mcp_server/`. Put tests in `tests/`, operational and experiment commands in `scripts/`, model manifests in `models/`, and plans/results in `docs/`.

Read `HANDOFF.md` and `docs/13_M1_M2联合数据闭环计划.md` for the current GB10 state,
approved public dataset, split policy, and immediate work before starting a new Codex CLI session.

## Current Architecture Boundary

The existing Web application and `RAGService` remain the source of truth for documents, collections, retrieval, and traceability. `opencode.json` connects the GB10 OpenAI-compatible Qwen3-14B service to three isolated local MCP servers. The implemented surface is read-only:

- `knowledge_search`
- `knowledge_list_collections`
- `knowledge_get_source`
- `vision_ocr_extract`
- `tabular_classify`

Qwen3-14B has been service-validated on this path, and the formal read-only
20-call OpenCode/MCP stability run passed. This does not imply a service is
currently running. Formal M2 business metrics remain blocked on an
owner-approved label-to-source mapping and human annotations. Vision and
tabular protocol/synthetic chain checks have passed, but M1 OCR quality,
tabular business metrics, and full multi-agent orchestration remain unfinished.
Do not create a second vector store or bypass `RAGService` with ad hoc database
queries.

As of 2026-07-27, the local worktree also contains an **unverified M1 display
draft** (`m1_service.py`, `routers/m1.py`, and `templates/m1.html`). It is a
deterministic text baseline for explaining the planned M1 -> M2 handoff, not a
GB10 OCR/VLM experiment or a persistent production API. Finish its static
assets and focused tests locally before synchronizing it to GB10; retain this
distinction in code, docs, and teacher-facing material.

## Development Commands

Use Python 3.11 and install `requirements.txt`. On Windows:

```powershell
.\venv\Scripts\python.exe scripts\verify_config.py
.\venv\Scripts\python.exe src\main.py -m http -p 5000
$env:PYTHONPATH="src"; .\venv\Scripts\python.exe -m pytest tests -v
```

On the GB10 Linux machine, provide the required local environment variables
without recording their values, then initialize and test the MCP path with:

```bash
python scripts/init_knowledge_backend.py
python scripts/smoke_test_mcp_server.py
opencode mcp list
```

## Style and Testing

Follow PEP 8, four-space indentation, type annotations, and `snake_case`/`PascalCase` naming. Keep route handlers thin and business logic in `src/biz/`. Tests use `pytest`; name files `test_*.py` and add focused coverage for service, retrieval, MCP contract, and API changes. Commands requiring live PostgreSQL, GB10 models, or cloud credentials must be identified as integration tests.

## Changes and Security

Use short, imperative commits scoped to one concern. PRs should state behavior, verification commands, configuration impact, and screenshots for UI changes. Never commit `.env`, credentials, server addresses, model weights, generated datasets, logs, or local databases. Preserve the read-only MCP boundary unless a reviewed task explicitly introduces a write operation.
