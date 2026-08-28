---
name: webapp-testing
description: Web 应用测试 - 帮助编写和运行 Web 应用的各类测试
user-invocable: true
allowed-tools:
  - Read
  - Bash
  - Write
  - Grep
version: 1.0.0
---

# Web 应用测试

## 用途

帮助编写和运行 Web 应用的各类测试，包括单元测试、集成测试、API 测试和端到端测试。

## 如何触发

```
帮我为 @src/auth/login.py 编写单元测试
```

或者：

```
运行测试并分析失败原因
```

## 测试类型

| 类型 | 范围 | 工具 | 速度 |
|------|------|------|------|
| 单元测试 | 单个函数/类 | pytest | 快 |
| 集成测试 | 多个模块协作 | pytest | 中 |
| API 测试 | HTTP 接口 | pytest + httpx | 中 |
| E2E 测试 | 完整用户流程 | Playwright | 慢 |

## 测试模板

### 单元测试 (pytest)

```python
import pytest
from src.auth.login import verify_password

class TestVerifyPassword:
    def test_correct_password(self):
        assert verify_password("hash123", "password") == True

    def test_wrong_password(self):
        assert verify_password("hash123", "wrong") == False

    def test_empty_password(self):
        with pytest.raises(ValueError):
            verify_password("hash123", "")
```

### API 测试 (FastAPI)

```python
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

def test_login_success():
    response = client.post("/api/auth/login", json={
        "username": "test",
        "password": "password"
    })
    assert response.status_code == 200
    assert "access_token" in response.json()
```

## 常用命令

```bash
# 运行所有测试
pytest

# 运行特定文件
pytest tests/test_auth.py

# 显示覆盖率
pytest --cov=src --cov-report=html

# 只运行失败的测试
pytest --lf
```

## 测试最佳实践

1. **命名清晰**: `test_login_with_wrong_password_returns_401`
2. **单一职责**: 每个测试只验证一件事
3. **独立性**: 测试之间不应相互依赖
4. **使用 Fixture**: 复用测试数据和设置
5. **Mock 外部依赖**: 数据库、API、文件系统

## 注意事项

- 测试覆盖率目标：80% 以上
- 优先测试核心业务逻辑
- 边界条件和异常情况要覆盖
- 测试代码也要保持整洁
