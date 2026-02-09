# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

JinRongAgents is a financial business assistant system built with LangChain + LangGraph + FastAPI. It provides intelligent Q&A, document processing, and knowledge base management for accounting rules.

**Tech Stack**: Python 3.11, FastAPI, LangChain 1.0+, LangGraph, PostgreSQL + PGVector, SiliconFlow API (DeepSeek-V3.2)

## Build/Run/Test Commands

```bash
# Activate virtual environment (Windows)
venv\Scripts\activate.bat

# Start the application
python src/main.py -m http -p 5000

# Run tests
python tests/test_core_service.py
pytest tests/ -v

# Lint
isort src/ tests/
pylint src/ --disable=import-error

# Database initialization
python scripts/init_pgvector_db.py
python scripts/init_collaboration_db.py
```

## Architecture

```
src/
├── web/          # Presentation layer - FastAPI routes + WebSocket
│   ├── app.py    # Main Flask app (legacy)
│   ├── routers/  # API route modules (chat, knowledge, collaboration)
│   └── templates/
├── biz/          # Business logic layer - Services
│   ├── agent_service.py   # Chat execution, session management
│   └── rag_service.py     # Smart retrieval, reranking, ingestion
├── agents/       # Agent layer - LangGraph ReAct agent
│   └── agent.py           # Master router with 17 tools
├── tools/        # Tool layer - Agent-callable tools
│   ├── rag_tools.py       # smart_retrieve, batch_retrieve
│   ├── qa_agent.py        # Knowledge base Q&A
│   ├── document_processor.py  # Rule extraction
│   ├── vector_store.py    # PGVector wrapper
│   ├── bm25_retriever.py  # Full-text search
│   ├── hybrid_retriever.py    # Combined search
│   ├── reranker_tool.py   # Result reranking
│   └── question_classifier.py # Query type classification
├── storage/      # Data access layer - ACL pattern
│   ├── provider.py        # Storage provider (schema validation)
│   ├── database/          # SQLAlchemy models, document manager
│   ├── memory/            # LangGraph checkpointer
│   └── s3/                # Object storage
└── utils/        # Utilities
    ├── config_loader.py   # Centralized config
    └── cache.py           # In-memory caching
```

## Key Data Flows

**Chat Request**:
```
User → FastAPI route → AgentService → LangGraph Agent → Tools → Storage → Response
```

**RAG Retrieval** (in `rag_service.py`):
```
Query → Question Classification (7 types) → Strategy Selection →
Vector/BM25/Hybrid Search → Rerank → Results
```

Question types: `concept`, `process`, `compare`, `factual`, `rule`, `troubleshooting`, `general`

## Configuration

**Primary config**: `config/app_config.json` - Database, vector store, LLM, RAG strategies

**Required environment variables** (`.env`):
- `SILICONFLOW_API_KEY` - LLM/Embedding API
- `PGDATABASE_URL` - PostgreSQL connection string
- `JWT_SECRET_KEY` - Auth token signing
- `CORS_ORIGINS` - Allowed origins (comma-separated)

## Code Conventions

**Imports**: Use relative imports for internal modules, absolute for third-party:
```python
from ..tools.vector_store import get_vector_store  # internal
from langchain.tools import tool  # third-party
```

**Service pattern**: Use singleton getters:
```python
def get_rag_service() -> RAGService:
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service
```

**Tools**: Use `@tool` decorator with clear docstrings (Agent reads these):
```python
@tool
def my_tool(query: str, top_k: int = 5) -> str:
    """Tool description for the Agent."""
    ...
```

**Error handling**: Catch specific exceptions, use `logger = logging.getLogger(__name__)`

**Async**: Use `async/await` for I/O operations, `AsyncGenerator` for streaming

## Adding New Features

**New API endpoint**: Add route in `src/web/routers/`, business logic in `src/biz/`

**New Agent tool**:
1. Create in `src/tools/` with `@tool` decorator
2. Register in `src/agents/agent.py` tools list

**New retrieval strategy**: Implement in `src/tools/`, integrate in `rag_service.py`, update `question_classifier.py`

## Frontend Notes

- Config in `src/web/static/config.js` - use `APP_CONFIG.*` instead of hardcoding
- Use `apiCall()` wrapper instead of raw `fetch`
- WebSocket port configurable via `APP_CONFIG.WS_PORT`
