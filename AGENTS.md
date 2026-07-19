# Repository Guidelines

## Project Structure

`src/` uses a layered FastAPI architecture: `web/` contains routes, templates, and static assets; `biz/` owns application services; `agents/` contains the in-app LangGraph agent; `tools/` implements retrieval and document functions; `storage/` manages PostgreSQL/PGVector, memory, and files. The read-only OpenCode adapter is in `src/mcp_server/`. Put tests in `tests/`, operational and experiment commands in `scripts/`, model manifests in `models/`, and plans/results in `docs/`.

Read `HANDOFF.md` for the current GB10 state and immediate work before starting
a new Codex CLI session.

## Current Architecture Boundary

The existing Web application and `RAGService` remain the source of truth for documents, collections, retrieval, and traceability. `opencode.json` connects the GB10 OpenAI-compatible Qwen3-14B service to the local `jinrong-rag` MCP server. The implemented MCP surface is currently read-only:

- `knowledge_search`
- `knowledge_list_collections`
- `knowledge_get_source`

Qwen3-14B has been service-validated on this path, and the formal read-only
20-call OpenCode/MCP stability run passed. This does not imply a service is
currently running. Formal M2 business metrics remain blocked on an
owner-approved label-to-source mapping and human annotations; M1 OCR/rule-tool
metrics and full multi-agent orchestration remain planned work. Do not create a
second vector store or bypass `RAGService` with ad hoc database queries.

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
