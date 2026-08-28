---
name: memory-systems
description: Agent 记忆系统 - 设计和实现 Agent 的短期/长期记忆机制
user-invocable: true
allowed-tools:
  - Read
  - Grep
version: 1.0.0
---

# Agent 记忆系统

## 用途

帮助设计和实现 Agent 的记忆机制，包括短期记忆、长期记忆和工作记忆。

## 如何触发

```
帮我设计一个 Agent 记忆系统
```

## 记忆类型

| 类型 | 存储 | 生命周期 | 用途 |
|------|------|----------|------|
| 短期记忆 | 内存 | 单次对话 | 上下文保持 |
| 工作记忆 | 内存 | 单次任务 | 中间状态 |
| 长期记忆 | 数据库 | 持久化 | 知识积累 |
| 情景记忆 | 向量库 | 持久化 | 经验检索 |

## 实现方案

### 短期记忆（对话历史）

```python
class ConversationMemory:
    def __init__(self, max_turns=20):
        self.messages = []
        self.max_turns = max_turns

    def add(self, role, content):
        self.messages.append({"role": role, "content": content})
        # 滑动窗口
        if len(self.messages) > self.max_turns * 2:
            self.messages = self.messages[-self.max_turns * 2:]
```

### 长期记忆（向量检索）

```python
class LongTermMemory:
    def __init__(self, vector_store):
        self.store = vector_store

    def remember(self, content, metadata):
        embedding = get_embedding(content)
        self.store.add(embedding, content, metadata)

    def recall(self, query, top_k=5):
        return self.store.search(query, top_k)
```

## 设计要点

1. **容量管理**: 设置合理的记忆上限
2. **相关性**: 只保留与任务相关的信息
3. **时效性**: 旧记忆逐渐衰减或归档
4. **检索效率**: 使用向量索引加速检索

## 注意事项

- 避免记忆过载导致上下文超限
- 敏感信息需要脱敏或加密
- 定期清理过期记忆
- 考虑记忆的一致性和准确性
