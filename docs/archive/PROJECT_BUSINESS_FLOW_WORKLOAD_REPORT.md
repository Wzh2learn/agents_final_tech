# 建账规则助手系统业务流程与工作量评估（汇报版）

更新时间：2026-03-04  
适用项目：`JinRongAgents`

## 1. 项目目标与范围

本系统面向“金融估值/建账规则”场景，核心目标是：
- 把分散的业务文档沉淀为可检索的多知识库。
- 在对话中实现“检索增强回答 + 来源溯源 + 下一步建议”。
- 支持协作会话与知识库持续维护（CRUD + 在线分段编辑）。

当前系统采用 ACL 分层架构（Web / Biz / Tools / Storage），并已具备可运行的 Web 端、RAG 检索链路、协作会话、最小评估测试。

## 2. 端到端业务流程（文字版）

### 2.1 知识入库流程（Knowledge Ingestion）

1. 用户在 `/knowledge` 创建知识库（collection）。
2. 用户上传文档并指定 `collection_name`。
3. 后端执行文档解析与父子分段（hierarchical chunking）。
4. 分段写入 PGVector，并更新文档元数据与统计信息。
5. 前端刷新概览卡片、文档列表、分段详情。

结果：知识按库隔离，可用于后续检索与问答。

### 2.2 问答流程（RAG QA）

1. 用户在 `/chat` 提问并携带当前会话上下文。
2. Agent 进入“问题分析 -> 检索 -> 生成”主链路。
3. `smart_retrieve` 执行向量/BM25/混合召回与可选 rerank。
4. 模型生成回答，后端附带 `sources`（来源片段）。
5. 前端渲染回答、来源卡片、下一步建议问题。

结果：回答与知识库绑定，具备可解释性和可追溯性。

### 2.3 溯源与回退流程（Traceability Fallback）

1. 若 Agent 未返回 trace，后端自动触发 `smart_retrieve` 回填来源。
2. 若检索仍为空，继续走本地兜底片段回退，保证 `sources` 字段结构可用。
3. 前端统一渲染来源（正常/兜底路径一致）。

结果：降低“回答无来源”的概率，提升可审计性。

### 2.4 协作会话流程（Collaboration）

1. 创建会话（私有/协作）。
2. 会话内发送消息并持久化历史。
3. 支持角色切换与会话管理（列表/重命名/删除）。

结果：满足多人协同与连续上下文需求。

### 2.5 运维与评估流程（Ops & Eval）

1. 使用 Docker 启动 `pgvector_15432`（`15432 -> 5432`）。
2. 初始化数据库脚本检查扩展与向量链路。
3. 运行非思考模式验证脚本（`scripts/test_non_thinking_mode.py`）。
4. 运行最小化检索评估测试（`test_minimal_retrieval_eval.py`）。
5. 通过配置控制 rerank、默认检索策略、代理继承行为。

结果：可重复部署、可最小验证、可配置演进。

## 3. 系统模块清单（按分层）

| 层级 | 模块 | 主要职责 | 关键文件 |
|---|---|---|---|
| Web 层 | Chat API | 对话请求、来源回填、建议问题 | `src/web/routers/chat.py` |
| Web 层 | Knowledge API | 知识库/文档 CRUD、上传、设置 | `src/web/routers/knowledge.py` |
| Web 层 | Collaboration API | 会话与消息管理 | `src/web/routers/collaboration.py` |
| Web 层 | 前端页面 | `/knowledge` `/chat` 交互渲染 | `src/web/static/knowledge.js`, `src/web/static/script.js` |
| Biz 层 | AgentService | 会话编排、Agent 调用、记忆协同 | `src/biz/agent_service.py` |
| Biz 层 | RAGService | 多检索策略、rerank、回退链路 | `src/biz/rag_service.py` |
| Tools 层 | 检索工具集 | 向量/BM25/Hybrid/Rerank | `src/tools/vector_store.py`, `src/tools/bm25_retriever.py`, `src/tools/reranker_tool.py` |
| Tools 层 | 文档处理集 | 解析、父子分段、规则抽取 | `src/tools/document_loader.py`, `src/tools/document_hierarchy.py` |
| Storage 层 | 数据持久化 | PGVector、协作消息、缓存 | `src/storage/database/*`, `src/storage/collaboration/*` |
| Config & Ops | 配置与启动 | 配置中心、部署与脚本 | `config/app_config.json`, `run.bat`, `README.md` |
| Quality | 测试与评估 | 最小检索评估、集成测试 | `tests/test_minimal_retrieval_eval.py`, `tests/test_web_integration.py` |

## 4. 工作量估算（后续迭代）

估算口径：1 名熟悉项目的全栈工程师，人日（PD）。

| 模块包 | 主要工作 | 估算（PD） | 优先级 |
|---|---|---:|---|
| M1 稳定性治理 | API 连接稳定性、超时/重试、日志与错误分级 | 3-5 | P0 |
| M2 知识库能力完善 | 知识库/文档 CRUD 打磨、批量操作、回收站策略 | 6-9 | P0 |
| M3 RAG 质量提升 | 检索策略参数化、rerank 评测、召回-准确率权衡 | 8-12 | P1 |
| M4 前端体验升级 | 交互一致性、可视化优化、移动端适配 | 6-10 | P1 |
| M5 测试体系建设 | API 自动化、回归集、最小确定性评估扩展 | 6-8 | P1 |
| M6 文档与交付 | README/部署手册、实验记录、答辩材料整理 | 3-4 | P2 |

总计：**32-48 人日**（约 6-10 周，取决于并行人数与返工比例）。

## 5. 分阶段里程碑建议

### 阶段 A（第 1-2 周，P0）
- 完成 M1 + M2：先保证“稳定可用 + 数据可维护”。
- 验收标准：对话成功率、来源可用率、CRUD 闭环可用。

### 阶段 B（第 3-6 周，P1）
- 完成 M3 + M4 + M5：提升回答质量、UI 体验和自动化验证能力。
- 验收标准：检索质量指标达标、核心页面走查通过、回归测试可一键执行。

### 阶段 C（第 7-8 周，P2）
- 完成 M6：沉淀部署文档、实验结论、论文/汇报材料。
- 验收标准：新成员可按文档独立部署与复现实验结果。

## 6. 建议对外汇报的量化指标

- 知识库侧：库数量、文档数、分段数、入库成功率。
- 检索侧：Top-K 召回率、来源非空率、平均响应时延。
- 问答侧：可追溯回答占比、人工评审通过率。
- 工程侧：关键接口测试通过率、回归时长、部署成功率。

## 7. 当前风险与应对

- 外部 API 网络波动/代理干扰。  
  应对：默认 `OPENAI_TRUST_ENV=false`，并保留可配置开关。
- 历史数据质量不一致（命名、元数据缺损）。  
  应对：增加入库校验与后台修复脚本。
- 前端需求迭代频繁。  
  应对：明确“信息架构优先”，避免反复重构页面结构。

---

如用于答辩，可将本文件作为“项目实施与工作量依据”附件，配合 `/knowledge` 与 `/chat` 的实际截图展示效果。
