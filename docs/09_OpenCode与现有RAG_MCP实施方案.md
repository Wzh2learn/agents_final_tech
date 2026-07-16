# OpenCode 与现有 RAG MCP 实施方案

## 1. 方案结论

M1/M2 主线采用“OpenCode + JinRongAgents RAG MCP + GB10 本地模型服务”。

- OpenCode 负责主 Agent、子 Agent、模型路由和工具调用。
- 现有 `RAGService`、PGVector、BM25、知识库接口和页面继续作为唯一知识底座。
- GB10 上的生成、OCR/VLM、Embedding 和 Reranker 继续独立部署。
- MCP 只做薄适配，不复制文档、不新建第二套向量库、不改变现有页面的数据来源。

Knowledge RAG 仅可用于 1 至 2 天的 MCP 兼容性验证。RAGFlow 暂不进入主线；只有现有复杂 PDF 解析和知识库管理能力经评测确认不足时，才单独立项评估。

## 2. 总体架构

```text
现有页面 / OpenCode
        |
        +-- 主协调 Agent
        |     +-- M1 文档处理 Agent
        |     +-- M2 问答 Agent
        |     +-- 校验 Agent
        |
        +-- JinRongAgents MCP Adapter
                    |
                    +-- RAGService / PGVector / BM25 / Traceability
                    +-- 现有 FastAPI 与知识库页面

GB10 OpenAI-compatible Model Services
        +-- Qwen3-14B：日常抽取和回答主力
        +-- Qwen3.6-35B-A3B：困难样例复核与质量上限
        +-- PaddleOCR-VL / Qwen3-VL：文档解析
        +-- BGE-M3 / Qwen3-Embedding：召回
        +-- Qwen3/BGE Reranker：重排序
```

## 3. MCP 工具边界

第一版只提供稳定、可审计的任务级工具：

| 工具 | 用途 | 默认权限 |
| --- | --- | --- |
| `knowledge_search` | 混合检索并返回证据片段、分数和来源 | allow |
| `knowledge_get_source` | 获取指定文档或片段的完整来源 | allow |
| `knowledge_list_collections` | 查询可用知识库 | allow |
| `m1_parse_document` | 调用 OCR/VLM 解析指定文档 | ask |
| `m1_extract_rules` | 生成并校验结构化规则 | ask |
| `evaluation_run` | 执行固定 M1/M2 评测集 | ask |

文档写入、删除、重新索引等操作不在首版自动授权范围内。MCP 返回结构使用现有业务 ID 和来源字段，避免 Agent 自行拼接数据库查询。

## 4. M1/M2 Agent 设计

M1 顺序执行“文档解析 -> 规则抽取 -> Pydantic 校验 -> 失败复核 -> 人工确认”。PaddleOCR-VL 为默认解析模型，Qwen3-VL 处理复杂版式，Qwen3-14B 负责抽取，35B 仅复核失败或低置信样例。

M2 顺序执行“查询分析 -> 混合召回 -> Rerank -> 有证据回答/无证据拒答 -> 来源校验”。召回和重排是确定性工具，不单独设置自治 LLM Agent。

不同 Agent 可以配置不同模型，但 GB10 一次尽量只常驻一个生成模型。第一版采用一个 14B 主服务加按需专项模型，避免为了形式上的多 Agent 同时加载多个大模型。

## 5. 分阶段实施

### 阶段 A：MCP 最小闭环

1. 新建独立 MCP 入口，复用 `RAGService`。
2. 实现三个只读知识工具及单元测试。
3. 在 OpenCode 中配置现有 OpenAI-compatible 模型和本地 MCP。
4. 使用 10 份文档、20 个问题连续验证工具发现、调用、来源返回和错误处理。

### 阶段 B：M2 基线

1. 将已验证的本地 Embedding/Reranker 接入现有 RAG 链路。
2. 固定 Recall@5、来源命中率、拒答率和延迟评测。
3. 复用现有知识库与聊天页面展示结果。

### 阶段 C：M1 工作流

1. 接入 OCR/VLM 路由与结构化规则 Schema。
2. 增加 Pydantic 校验、失败重试和人工审核状态。
3. 测量 JSON 合法率、字段 F1、人工修正率及 OCR 误差传递。

### 阶段 D：多 Agent 与交接

单 Agent 工具闭环稳定后，再拆分主协调、M1、M2 和校验 Agent。角色 B 负责模型、数据、任务工具和数字结果；协作同学负责复杂 Agent 编排、企业接口、权限、会话状态和生产化集成。

## 6. 第一阶段验收

- OpenCode 能识别并稳定调用 JinRongAgents MCP。
- MCP 不创建第二套知识库或向量索引。
- M2 返回文档名、片段、业务 ID 和可核验来源。
- M1 输出通过统一 JSON Schema/Pydantic 校验。
- 连续执行 20 个测试任务无进程崩溃、无明显工具调用漂移。
- 所有模型、Prompt、检索参数和原始结果均可复现。

## 7. 当前项目配置

项目根目录 `opencode.json` 已配置 GB10 上的 Qwen3-14B OpenAI-compatible
服务和 `jinrong-rag` 本地 MCP。启动 OpenCode 前需在开发机终端提供：

```bash
export PGDATABASE_URL='postgresql://USER:PASSWORD@127.0.0.1:15432/vector_db'
export JINRONG_MCP_PYTHON="$HOME/miniconda3/envs/wzh_vllm/bin/python"
```

协议级检查命令：

```bash
python scripts/smoke_test_mcp_server.py
opencode mcp list
```

配置中首批建立 `m2-qa`、`m1-extraction` 和 `evidence-verifier` 三个逻辑
子 Agent。它们暂时共用 14B 主模型，待单 Agent 工具闭环和任务评测稳定后，
再根据数字结果决定是否为困难样例切换 35B。
