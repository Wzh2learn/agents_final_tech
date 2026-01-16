# AGENTS.md - Development Guidelines for AI Agents

This file provides guidelines for AI coding agents working on this repository.

## Build/Lint/Test Commands

### Environment Setup
```bash
# Activate virtual environment (Windows)
cd D:\AIRcommend\JinRongAgents\agents_final_tech
venv\Scripts\activate.bat

# Install dependencies
pip install -r requirements.txt
```

### Running the Application
```bash
# Using main.py with HTTP server on port 5000
python src/main.py -m http -p 5000
```

### Running Tests
```bash
# Run the async test script
python tests/test_core_service.py
```

### Linting and Formatting
```bash
# Sort imports
isort src/ tests/

# Lint with pylint
pylint src/ --disable=import-error

# Verify imports work
python -c "from src.main import app; print('Import OK')"
```

## Code Style Guidelines

### Import Conventions
Use **relative imports** for internal modules, **absolute imports** for third-party libraries:
```python
# Internal modules (relative)
from ..tools.vector_store import get_vector_store
from ..storage.provider import get_storage_provider

# Third-party libraries (absolute)
from langchain.tools import tool
from flask import Flask
from typing import List, Dict, Optional, Any
```

### Formatting
- No unnecessary comments unless explaining complex logic
- Use blank lines to separate logical sections within functions
- Keep lines under 120 characters
- Use consistent indentation (4 spaces)

### Type Annotations
Use Python's `typing` module for type hints:
```python
from typing import List, Dict, Optional, Any, AsyncGenerator

def smart_retrieve(query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """Smart retrieval with type annotations."""
    ...

async def stream_chat(self, message: str, conversation_id: str) -> AsyncGenerator[Dict[str, Any], None]:
    ...
```

### Naming Conventions
- **Files/Functions/Variables**: `snake_case`
- **Classes**: `PascalCase`
- **Constants**: `UPPER_SNAKE_CASE`
- **Private methods**: `_leading_underscore`

### Error Handling
Catch specific exceptions first, use logging, return user-friendly errors:
```python
try:
    result = process()
except ValueError as e:
    logger.error(f"参数错误: {e}")
    return {"error": "invalid_parameter"}
except Exception as e:
    logger.exception(f"未预期错误: {e}")
    return {"error": "internal_error"}
```

### Logging
Use `logging.getLogger(__name__)` for module-level loggers:
```python
import logging

logger = logging.getLogger(__name__)
```

### Project Architecture
```
src/
├── web/          # 表示层 - Flask API + WebSocket
├── biz/          # 业务逻辑层 - Service层
├── agents/       # Agent层 - LangGraph Agent
├── tools/        # 工具层 - Agent可用工具
├── storage/      # 数据访问层 - DB/S3/Cache
└── utils/        # 工具函数
```

### Service Pattern
Use singleton getters for services:
```python
def get_rag_service() -> RAGService:
    """Get RAG service singleton."""
    ...

def get_agent_service() -> AgentService:
    """Get Agent service singleton."""
    ...
```

### Async Operations
Use `async/await` for I/O-bound operations:
```python
async def stream_chat(self, message: str, conversation_id: str) -> AsyncGenerator[Dict[str, Any], None]:
    """Stream chat responses asynchronously."""
    async for chunk in agent.stream(message):
        yield chunk
```

### API Response Format
Return consistent JSON responses:
```python
return jsonify({
    "status": "success",
    "data": {...},
    "message": "操作成功"
})
```
