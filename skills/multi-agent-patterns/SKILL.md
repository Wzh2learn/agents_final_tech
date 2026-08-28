---
name: multi-agent-patterns
description: 多 Agent 架构模式 - 设计和实现多 Agent 协作系统的最佳实践
user-invocable: true
allowed-tools:
  - Read
  - Grep
  - Glob
version: 1.0.0
---

# 多 Agent 架构模式

## 用途

帮助设计和实现多 Agent 协作系统，提供常见架构模式和最佳实践。

## 如何触发

```
帮我设计一个多 Agent 系统来处理客服工单
```

## 常见架构模式

### 1. 路由模式 (Router)

```
用户请求 → 路由 Agent → 专业 Agent A/B/C → 响应
```

**适用场景**: 不同类型任务需要不同专业能力

### 2. 管道模式 (Pipeline)

```
输入 → Agent A → Agent B → Agent C → 输出
```

**适用场景**: 任务需要多步骤顺序处理

### 3. 监督模式 (Supervisor)

```
监督 Agent
    ↓
Worker Agent 1/2/3
    ↓
汇总结果
```

**适用场景**: 需要协调多个 Agent 并行工作

### 4. 辩论模式 (Debate)

```
Agent A ←→ Agent B
    ↓
裁判 Agent → 最终决策
```

**适用场景**: 需要多角度分析和验证

## 设计要点

| 要点 | 说明 |
|------|------|
| 职责单一 | 每个 Agent 只负责一类任务 |
| 接口清晰 | Agent 间通信格式标准化 |
| 容错处理 | 单个 Agent 失败不影响整体 |
| 可观测性 | 记录每个 Agent 的输入输出 |

## 示例：客服系统

```
用户消息
    ↓
意图识别 Agent → 分类: 咨询/投诉/退款
    ↓
路由到专业 Agent
    ↓
知识检索 Agent (RAG)
    ↓
回复生成 Agent
    ↓
质量检查 Agent
    ↓
最终回复
```

## 注意事项

- 避免 Agent 间循环依赖
- 设置合理的超时和重试机制
- 监控 Agent 调用链路和耗时
- 考虑成本（每个 Agent 调用都有开销）
