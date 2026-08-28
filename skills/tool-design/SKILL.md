---
name: tool-design
description: Agent 工具设计 - 设计高质量的 Agent 可调用工具
user-invocable: true
allowed-tools:
  - Read
  - Grep
version: 1.0.0
---

# Agent 工具设计

## 用途

帮助设计高质量的 Agent 可调用工具，确保工具易用、可靠、安全。

## 如何触发

```
帮我设计一个文件搜索工具给 Agent 使用
```

## 工具设计原则

| 原则 | 说明 |
|------|------|
| 单一职责 | 一个工具只做一件事 |
| 参数清晰 | 参数名和描述要明确 |
| 错误友好 | 返回有意义的错误信息 |
| 幂等安全 | 相同输入产生相同结果 |

## 工具定义模板

```python
from pydantic import BaseModel, Field

class SearchFilesInput(BaseModel):
    """搜索文件工具的输入参数"""
    pattern: str = Field(
        description="搜索模式，支持 glob 语法，如 '*.py'"
    )
    directory: str = Field(
        default=".",
        description="搜索目录，默认当前目录"
    )
    max_results: int = Field(
        default=10,
        description="最大返回数量"
    )

def search_files(input: SearchFilesInput) -> list[str]:
    """
    搜索匹配模式的文件

    Returns:
        匹配的文件路径列表
    """
    # 实现逻辑
    pass
```

## 工具描述最佳实践

```json
{
  "name": "search_files",
  "description": "在指定目录中搜索匹配模式的文件。支持 glob 语法。",
  "parameters": {
    "pattern": "搜索模式，如 '*.py' 匹配所有 Python 文件",
    "directory": "搜索目录路径，默认当前目录",
    "max_results": "最大返回数量，默认 10"
  }
}
```

## 常见工具类型

1. **读取类**: 获取信息，无副作用
2. **写入类**: 修改状态，需要确认
3. **执行类**: 运行命令，需要权限控制
4. **查询类**: 搜索检索，需要限制结果数量

## 注意事项

- 工具描述要让 LLM 能理解何时使用
- 参数验证要严格，防止注入攻击
- 敏感操作需要用户确认
- 记录工具调用日志便于调试
