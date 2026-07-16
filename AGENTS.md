# Repository Guidelines

## Project Structure & Module Organization

Application code lives in `src/` and follows a layered design: `web/` contains FastAPI routes, templates, and static assets; `biz/` holds application services; `agents/` defines LangGraph workflows; `tools/` implements retrieval and document utilities; `storage/` contains database, memory, and object-storage adapters; and `auth/` handles JWT authentication. Put automated tests in `tests/`, operational utilities in `scripts/`, configuration templates in `config/`, and design or deployment notes in `docs/`. Model manifests belong in `models/`; model weights and generated data must stay outside Git.

## Build, Test, and Development Commands

Create a Python 3.11 environment, then install dependencies:

```bash
pip install -r requirements.txt
python scripts/verify_config.py
python src/main.py -m http -p 5000
```

The service is available at `http://localhost:5000`; FastAPI documentation is at `/docs`. Start the local PostgreSQL/PGVector container before database-backed work. Run `python scripts/init_pgvector_db.py` when initializing a new database.

## Coding Style & Naming Conventions

Follow PEP 8 with four-space indentation. Use type annotations and concise docstrings for public functions. Name functions and variables `snake_case`, classes `PascalCase`, and constants `UPPER_CASE`. Keep imports ordered as standard library, third-party packages, then project modules. Route handlers belong in `src/web/routers/`; business logic should remain in `src/biz/` rather than handlers. Use `isort src tests` and `pylint src --disable=import-error` for local checks.

## Testing Guidelines

Tests use `pytest`, `pytest-asyncio`, and `pytest-mock`. Name files `test_*.py` and tests `test_<behavior>`. Run:

```bash
pytest tests/ -v
pytest tests/ --cov=src --cov-report=html
```

Add focused unit tests for service changes and integration tests for API, storage, or retrieval behavior. Do not require live cloud credentials in ordinary test runs.

## Commit & Pull Request Guidelines

History uses short imperative subjects and conventional prefixes such as `feat:`, `fix:`, `docs:`, and `chore:`. Keep each commit scoped to one concern. Pull requests should explain the behavior change, list verification commands, link relevant issues, and include screenshots for UI changes. Call out database migrations, configuration changes, and remaining risks.

## Security & Configuration Tips

Never commit `.env`, API keys, passwords, server IPs, model weights, logs, or local databases. Use environment variables for secrets. Do not modify `config/` or perform destructive server/environment operations without explicit coordination.
