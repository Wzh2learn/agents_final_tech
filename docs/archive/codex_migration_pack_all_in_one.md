

---

# FILE: README_Codex_使用说明.md

# Codex 迁移启动包使用说明

## 1. 使用目标

这个启动包用于帮助 Codex 快速理解 AIModel-UDF Explorer Platform 项目的背景、阶段目标、技术架构、任务边界和近期开发重点。

建议把本目录中的文件放到项目仓库根目录：

```text
project-root/
├── AGENTS.md
├── README_Codex_使用说明.md
├── docs/
│   ├── 00_Codex_启动提示词.md
│   ├── 01_项目背景与目标.md
│   ├── 02_阶段计划与分工.md
│   ├── 03_技术架构与模块设计.md
│   ├── 04_服务器与模型部署计划.md
│   ├── 05_开发任务清单.md
│   └── 06_Remote_SSH_开发流程.md
└── scripts/
    └── README_scripts.md
```

## 2. 推荐使用方式

### 第一步：把文件加入仓库

```bash
git checkout -b codex-migration
mkdir -p docs scripts
# 将本启动包中的 AGENTS.md、docs/、scripts/ 放入仓库
git add AGENTS.md README_Codex_使用说明.md docs scripts
git commit -m "docs: add codex migration context"
```

### 第二步：让 Codex 先读上下文

把 `docs/00_Codex_启动提示词.md` 中的提示词复制给 Codex。

### 第三步：让 Codex 分阶段工作

先让 Codex 做以下任务：

1. 阅读 `AGENTS.md` 和 `docs/`；
2. 输出它对项目目标、模块、当前阶段的理解；
3. 检查现有代码仓库结构；
4. 提出最小改造计划；
5. 分小步实现，不要一次性重构整个项目。

### 第四步：Remote SSH 开发机接入

开发机 SSH 已配置后，可以通过 VS Code Remote SSH 打开远程目录，在远程终端运行 Codex CLI 或手动执行 Codex 生成的命令。

注意：

- 不要把服务器密码、IP、token、API key 写入仓库；
- 所有密钥放入 `.env`，并只提交 `.env.example`；
- 服务器部署脚本先生成模板，实际执行前人工确认；
- 模型部署和 CUDA 环境调整需要谨慎执行，避免破坏现有环境。

## 3. 当前第一阶段原则

第一阶段目标不是完整生产级系统，而是完成：

1. 本地模型服务可调用；
2. M1 文档规则抽取最小闭环；
3. M2 规则知识库问答最小闭环；
4. 前端页面和评测 Harness 初版；
5. 模型部署、RAG、规则抽取、结构化输出的实验记录。

---

# FILE: AGENTS.md

# AGENTS.md

## Project Name

AIModel-UDF Explorer Platform

## Project Goal

Build a lightweight experimental platform for business rule document parsing, structured rule extraction, RAG-based rule QA, local LLM deployment, and evaluation harness.

The first stage focuses on M1 and M2:

- M1: business rule document parsing and structured rule extraction.
- M2: business rule knowledge base and role-aware RAG QA.

The platform should support demo, experiment, and iterative optimization. It should prioritize runnable workflows, clean interfaces, measurable experiments, and modular architecture.

## Important Context

The project is developed in a lab environment with access to GPU servers. A local development machine can be accessed via VS Code Remote SSH. The team plans to test local LLMs under 30B parameters or quantized 30B-level models, expose them through an OpenAI-compatible API, and use them for document parsing, rule extraction, RAG QA, and structured output tasks.

The project should keep both local model APIs and cloud model APIs configurable.

## Core Principles

1. Keep the system modular and easy to iterate.
2. Prefer FastAPI for backend APIs.
3. Use Pydantic schemas for structured business rule representation.
4. Use LangChain / LangGraph only where they simplify workflow orchestration.
5. Keep model provider configurable through environment variables.
6. Support local OpenAI-compatible endpoints from vLLM, SGLang, or llama.cpp.
7. Do not hardcode secrets, passwords, tokens, server IPs, or local absolute paths.
8. Add logs and evaluation outputs for every LLM workflow.
9. Keep frontend simple and demo-oriented in the first stage.
10. Prefer small, reviewable changes.
11. Avoid over-engineering production-level features before M1/M2 baseline is runnable.
12. Add clear run commands and update documentation after code changes.

## Current Milestones

### Milestone 1: Repository and backend scaffold

- Create or align FastAPI backend structure.
- Add health check API.
- Add config loading from `.env`.
- Add model provider configuration.
- Add Pydantic schemas.
- Add basic tests.

### Milestone 2: Local model service integration

- Add OpenAI-compatible model client.
- Support vLLM endpoint.
- Support SGLang endpoint if needed.
- Support llama.cpp endpoint if needed.
- Support cloud model fallback.
- Add model connectivity test API.
- Add model benchmark script.

### Milestone 3: RAG baseline

- Implement document upload.
- Implement document parsing.
- Implement text splitting.
- Implement vector storage.
- Implement retrieval.
- Implement rule QA with source citations.

### Milestone 4: M1 rule extraction

- Implement rule extraction service.
- Define RuleSource, BusinessRule, UDFFieldRule, DocumentExtractResult.
- Validate LLM outputs with Pydantic.
- Add human review placeholder API.
- Save extraction results for evaluation.

### Milestone 5: M2 rule QA

- Implement role-aware RAG QA.
- Add role prompt templates.
- Return source documents and chunks.
- Add conversation history support if existing infrastructure allows.
- Add basic answer evaluation.

### Milestone 6: Evaluation Harness

- Add test case management.
- Add batch evaluation script.
- Record latency, source hit rate, JSON validity, Pydantic validation pass rate, and manual review status.
- Export experiment results.

## Suggested Repository Structure

```text
backend/
  app/
    main.py
    api/
    core/
    models/
    services/
    rag/
    schemas/
    agents/
    evaluation/
    observability/
  tests/

frontend/
  ...

docs/
  00_Codex_启动提示词.md
  01_项目背景与目标.md
  02_阶段计划与分工.md
  03_技术架构与模块设计.md
  04_服务器与模型部署计划.md
  05_开发任务清单.md
  06_Remote_SSH_开发流程.md

scripts/
  check_gpu.sh
  setup_env.sh
  start_vllm.sh
  start_sglang.sh
  start_llamacpp.sh
  benchmark_model.py

experiments/
  datasets/
  results/
  templates/
```

## Tech Stack

Backend:

- Python
- FastAPI
- Pydantic
- LangChain
- LangGraph
- Chroma / FAISS / Milvus / Qdrant as needed
- OpenAI-compatible local model API
- Optional cloud model API fallback

Frontend:

- React / Next.js / Vite
- Keep pages simple and demo-oriented

Model serving:

- vLLM as primary option
- SGLang as optional comparison
- llama.cpp as optional quantized model runtime

Evaluation:

- Batch test cases
- Source hit rate
- JSON validity
- Pydantic validation pass rate
- Latency
- Manual review result

## Do Not Do

- Do not commit secrets.
- Do not commit server passwords.
- Do not hardcode server IP.
- Do not hardcode API keys.
- Do not build a full production permission system in the first stage.
- Do not implement full multi-tenant architecture in the first stage.
- Do not implement M3 before M1/M2 baseline is runnable.
- Do not assume 30B models can run efficiently before benchmarking.
- Do not make destructive server environment changes without explicit confirmation.
- Do not run system-level installation commands unless the user explicitly approves.

## Output Expectations

For every coding task:

1. Explain changed files.
2. Add or update tests when possible.
3. Provide commands to run.
4. Update documentation if APIs or scripts change.
5. Keep changes small and reviewable.
6. Mention any assumptions.
7. Ask before destructive operations.

---

# FILE: docs/00_Codex_启动提示词.md

# Codex 启动提示词

请复制下面这段内容给 Codex。

---

你现在接手的是 `AIModel-UDF Explorer Platform` 项目。

请先阅读：

1. `AGENTS.md`
2. `docs/01_项目背景与目标.md`
3. `docs/02_阶段计划与分工.md`
4. `docs/03_技术架构与模块设计.md`
5. `docs/04_服务器与模型部署计划.md`
6. `docs/05_开发任务清单.md`
7. `docs/06_Remote_SSH_开发流程.md`

然后再开始检查代码。

## 项目目标

本项目要建设一个轻量级 AIModel-UDF Explorer Platform，用于业务规则文档解析、结构化规则抽取、RAG 规则问答、本地模型部署、模型效果评测和实验记录。

当前阶段聚焦 M1 和 M2：

- M1：业务规则文档解析与结构化规则抽取；
- M2：业务规则知识库与角色化 RAG 问答。

项目需要优先完成可运行 Demo、可复用模块、可评测实验链路，不要一开始做复杂生产级系统。

## 当前开发环境设想

项目会在远程 Linux 开发机上通过 VS Code Remote SSH 开发。后续会在 GPU 服务器上部署本地模型服务，优先调研 vLLM，也可以保留 SGLang 和 llama.cpp 作为对比方案。

本地模型需要通过 OpenAI-compatible API 提供服务，后端通过统一 ModelClient 调用。

## 你的第一轮任务

请先完成以下事情，不要直接大规模改代码：

1. 阅读项目文档；
2. 检查当前仓库结构；
3. 输出你对项目目标、模块边界和当前阶段任务的理解；
4. 识别当前仓库已经具备的能力；
5. 识别缺失模块；
6. 给出最小改造计划；
7. 把任务拆成 5–8 个小 PR/小提交级别的步骤；
8. 等我确认后再开始改代码。

## 第一阶段优先任务

优先级从高到低：

1. 后端 FastAPI 基础结构；
2. Pydantic 规则 Schema；
3. 本地模型 OpenAI-compatible API 调用层；
4. 文档上传、解析、切分、入库；
5. RAG 问答接口；
6. M1 规则抽取接口；
7. M2 角色化规则问答；
8. 评测 Harness；
9. 模型 benchmark 脚本；
10. 简单前端页面或 API mock。

## 编码要求

1. 不要写入真实服务器 IP、用户名、密码、token、API key；
2. 所有配置通过 `.env` 读取；
3. 提交 `.env.example`，不要提交 `.env`；
4. 每个模块都要有清楚的接口和示例；
5. 优先小步提交；
6. 每次改动后说明运行方式；
7. 涉及服务器安装、CUDA、驱动、系统环境改动时必须先询问；
8. 不要做破坏性操作；
9. 不要过度设计；
10. 第一阶段先把 M1/M2 跑通。

## 请现在开始

请输出：

1. 你对项目的理解；
2. 你建议的目录结构；
3. 你建议的第一轮改动；
4. 你需要我确认的问题；
5. 你准备执行的第一步。

---

# FILE: docs/01_项目背景与目标.md

# 01 项目背景与目标

## 1. 项目背景

本项目围绕托管业务中的规则理解、文档解析、知识问答和流程辅助场景展开，建设一个可演示、可实验、可持续优化的 AIModel-UDF Explorer Platform。

平台服务于业务文档处理、规则知识组织、规则问答、结构化规则抽取、本地模型部署和实验评测等工作。第一阶段重点围绕 M1 和 M2 两类能力展开。

## 2. 核心场景

### M1：业务规则文档解析与统一数据格式抽取

M1 关注从多源业务材料中抽取规则、字段、条件、动作和来源，形成可校验、可展示、可复用的结构化结果。

输入可能包括：

- 产品文档；
- 业务规则文档；
- PDF；
- Word；
- Excel；
- 邮件附件；
- 代码片段；
- SQL 片段；
- 业务流程说明。

输出包括：

- 规则列表；
- 字段列表；
- 条件与动作；
- 来源引用；
- 置信度；
- 人工审核状态；
- Pydantic 校验结果。

### M2：业务规则知识库与角色化 RAG 问答

M2 关注把业务文档构建为规则知识库，并支持不同角色基于知识库问答。

典型能力包括：

- 文档上传；
- 文档切分；
- 向量入库；
- 规则问答；
- 来源追溯；
- 角色化回答；
- 历史记录；
- 回答质量评估。

## 3. 平台目标

### 3.1 功能验证目标

完成业务文档解析、规则抽取、规则知识库问答、来源追溯、人工审核、前端展示等核心能力，形成可演示的业务闭环。

### 3.2 技术验证目标

完成本地模型部署、推理框架调研、RAG 检索链路、Prompt 上下文构建、Pydantic 规则结构化、Agent 流程编排和评估模块，验证技术方案在真实业务材料上的可行性。

### 3.3 方法优化目标

在功能开发过程中积累模型能力、上下文构建、规则抽取、RAG 检索、结构化输出和人工审核等实验数据，为后续模型优化和系统改进提供依据。

## 4. 第一阶段边界

第一阶段优先完成：

1. 本地模型服务可调用；
2. 文档上传、解析、切分、入库；
3. M1 规则抽取最小闭环；
4. M2 RAG 问答最小闭环；
5. Pydantic 规则 Schema；
6. 前端基础页面；
7. 评测 Harness 初版；
8. 模型部署和 RAG 实验记录。

第一阶段暂不展开：

1. 完整生产级权限系统；
2. 完整多租户体系；
3. 完整 M3 业务流程自动化；
4. 金融级审计体系；
5. 全量模型微调平台；
6. 复杂工作流编排平台；
7. 私有化交付完整运维体系。

---

# FILE: docs/02_阶段计划与分工.md

# 02 阶段计划与分工

## 1. 总体周期

整体按 6–8 周推进。第一阶段重点完成 M1/M2 闭环，并同步开展本地模型部署、模型能力测试和 RAG 实验记录。

## 2. 阶段计划

### 第 1 周：项目启动、环境摸底与基础链路搭建

目标：

1. 明确两人分工；
2. 确认服务器账号、GPU、CUDA、系统环境；
3. 搭建代码仓库；
4. 确定第一批测试文档；
5. 完成前后端 API 初稿；
6. 跑通一个本地模型 API；
7. 前端搭建基础页面框架。

交付物：

- 项目任务清单；
- 技术架构草图；
- 服务器环境摸底记录；
- 本地模型 API 初步可用；
- 前后端 API 初稿。

### 第 2 周：本地模型服务与 RAG 基线

目标：

1. 跑通 vLLM 服务；
2. 跑通 7B/14B 模型；
3. 完成 OpenAI-compatible API 调用；
4. 完成文档上传、切分、入库 baseline；
5. 前端完成文档上传和知识库页面初版；
6. 记录模型调用速度和显存占用。

交付物：

- vLLM 模型服务；
- RAG 入库 baseline；
- 文档上传页面初版；
- 模型调用测试记录。

### 第 3 周：M2 规则问答闭环

目标：

1. 完成规则知识库问答；
2. 支持角色化 Prompt；
3. 支持来源返回；
4. 支持历史记录；
5. 前端完成规则问答页面；
6. 建立第一版问答测试集。

交付物：

- M2 规则问答 Demo；
- 角色化问答 Prompt 模板；
- 来源追溯结果展示；
- 第一版问答测试集。

### 第 4 周：M1 规则抽取与 Pydantic 结构化

目标：

1. 完成产品文档规则抽取；
2. 设计 Pydantic 规则 Schema；
3. 完成抽取结果校验；
4. 前端展示规则抽取结果；
5. 支持人工审核入口；
6. 记录抽取结果和人工修正结果。

交付物：

- RuleSource / BusinessRule / UDFFieldRule 等 Schema；
- M1 文档规则抽取 Demo；
- 规则抽取结果展示页面；
- 人工审核页面初版。

### 第 5 周：Agent 流程与评测 Harness

目标：

1. 使用 LangGraph 搭建轻量流程；
2. 完成 Router Node；
3. 完成 Rule Extraction Node；
4. 完成 Rule QA Node；
5. 完成 Evaluation Node；
6. 搭建评测 Harness；
7. 批量测试不同模型在 M1/M2 上的效果。

交付物：

- M1/M2 LangGraph 流程；
- 评测 Harness 初版；
- 规则抽取准确率初步统计；
- RAG 问答来源命中率统计。

### 第 6 周：前后端联调与模型对比

目标：

1. 完成前后端联调；
2. 接入本地模型和云模型切换；
3. 对比 8B/14B/30B 模型效果；
4. 对比 vLLM 和备选推理框架；
5. 完成第一版 Demo 流程；
6. 形成第一版实验记录。

交付物：

- 可演示系统；
- 模型对比实验表；
- 前后端联调记录；
- Demo 演示脚本。

### 第 7 周：上下文构建与规则抽取优化

目标：

1. 测试不同切分策略；
2. 测试不同上下文长度；
3. 测试不同 Prompt 模板；
4. 测试不同量化精度；
5. 优化 Pydantic 结构化输出；
6. 梳理可继续深入的技术方向。

交付物：

- RAG 实验记录；
- 上下文构建实验记录；
- 规则抽取优化记录；
- 模型部署实验记录；
- 技术方向调研清单。

### 第 8 周：阶段验收与后续方案

目标：

1. 完成阶段演示；
2. 整理平台使用文档；
3. 整理模型与 RAG 实验结果；
4. 明确后续是否扩展 M3；
5. 明确后续重点优化方向。

交付物：

- AIModel-UDF Explorer Platform 阶段 Demo；
- 技术路线文档；
- 实验结果汇总；
- 后续优化方向建议。

## 3. 团队分工

### 3.1 角色 A：前端页面与评测 Harness

主要负责：

1. 平台前端页面；
2. 文档上传页面；
3. 知识库管理页面；
4. 规则问答页面；
5. 规则抽取结果展示页面；
6. 人工审核页面；
7. 模型评测页面；
8. 测试样例管理；
9. 评测 Harness 设计；
10. 评测结果可视化；
11. 前后端 API 联调；
12. Demo 演示流程整理。

评测 Harness 需要支持：

1. 管理测试文档；
2. 管理标准问题集；
3. 管理规则抽取标注样例；
4. 批量调用不同模型；
5. 批量记录回答结果；
6. 展示来源命中、格式合法、人工评分等指标；
7. 导出实验结果。

### 3.2 角色 B：模型调研、模型部署与模型侧辅助开发

主要负责：

1. 候选模型调研；
2. 本地模型部署；
3. vLLM / SGLang / llama.cpp 推理框架对比；
4. 模型量化方案测试；
5. 模型微调方案调研；
6. LoRA / QLoRA 可行性验证；
7. 规则抽取 Prompt 调优；
8. 结构化输出能力测试；
9. 模型服务 API 封装；
10. 模型调用性能记录；
11. 本地模型和云模型效果对比；
12. 模型侧实验报告整理。

### 3.3 共同协作内容

1. 明确第一批业务文档和测试样例；
2. 定义前后端接口；
3. 设计 Pydantic 规则 Schema；
4. 设计 M1/M2 Demo 流程；
5. 设计实验指标；
6. 整理阶段汇报材料；
7. 讨论后续可优化的技术方向。

---

# FILE: docs/03_技术架构与模块设计.md

# 03 技术架构与模块设计

## 1. 总体架构

平台建议采用以下结构：

```text
前端页面
  ↓
API 服务层
  ↓
LLM 业务逻辑层
  ↓
RAG 知识库层
  ↓
Pydantic 规则结构层
  ↓
本地模型服务层
  ↓
评测 Harness 与日志观测层
```

## 2. 前端页面层

前端页面主要包括：

1. 首页 Dashboard；
2. 文档管理；
3. M1 规则解析；
4. M2 规则问答；
5. 规则抽取结果展示；
6. 人工审核；
7. 模型选择；
8. 模型评测；
9. 实验结果展示。

第一阶段重点是让流程清楚，不追求复杂交互。

## 3. API 服务层

API 层建议使用 FastAPI。

核心接口包括：

1. `GET /api/health`：健康检查；
2. `GET /api/models/list`：模型列表；
3. `POST /api/models/test`：模型连通性测试；
4. `POST /api/documents/upload`：文档上传；
5. `POST /api/documents/ingest`：文档解析、切分、入库；
6. `POST /api/rag/query`：RAG 问答；
7. `POST /api/rules/extract`：规则抽取；
8. `POST /api/rules/review`：人工审核结果提交；
9. `POST /api/evaluation/run`：批量评测；
10. `GET /api/evaluation/results`：评测结果查询。

LangServe 可作为后续标准化封装方案，在核心链路稳定后再引入。

## 4. LLM 业务逻辑层

LLM 业务逻辑层负责：

1. 场景识别；
2. 用户意图识别；
3. Prompt 上下文构建；
4. 文档解析调度；
5. 规则抽取；
6. RAG 检索问答；
7. 结构化输出；
8. 人工审核流转；
9. Agent 流程编排；
10. 结果评估。

第一阶段建议采用 LangChain + LangGraph 的轻量流程编排。不要过度构建复杂自治 Agent。

## 5. RAG 知识库层

RAG 知识库层负责：

1. 文档切分；
2. 元数据管理；
3. 向量入库；
4. BM25 检索；
5. Hybrid 检索；
6. Rerank；
7. 来源追溯；
8. 多版本规则管理。

第一阶段可先支持：

1. 普通切分；
2. Markdown 结构切分；
3. 向量检索；
4. 来源返回。

后续补充：

1. Hybrid 检索；
2. Rerank；
3. 父子分段；
4. 上下文压缩；
5. 长上下文对比实验。

## 6. Pydantic 规则结构层

Pydantic 用于描述关键规则和统一数据格式。

建议设计：

### RuleSource

描述规则来源：

- document_id；
- document_name；
- chunk_id；
- page_no；
- section_title；
- quote；
- version。

### BusinessRule

描述通用业务规则：

- rule_id；
- rule_name；
- scenario；
- condition；
- action；
- constraints；
- source；
- confidence；
- status。

### UDFFieldRule

描述统一数据格式字段：

- field_name；
- field_type；
- required；
- aliases；
- validation_rule；
- example；
- source。

### DocumentExtractResult

描述文档抽取结果：

- document_id；
- rules；
- fields；
- warnings；
- confidence；
- validation_errors；
- need_human_review。

### RuleReviewResult

描述人工审核结果：

- rule_id；
- reviewer；
- status；
- comments；
- corrected_rule；
- reviewed_at。

### EvalResult

描述评估结果：

- task_id；
- model_name；
- score；
- latency_ms；
- source_hit；
- json_valid；
- pydantic_valid；
- risk_level；
- reasons。

## 7. Agent 流程设计

第一阶段使用轻量状态机。

建议节点：

1. Router Node：判断 M1/M2；
2. Document Parser Node：解析文档；
3. Rule Extraction Node：抽取规则；
4. RAG Retrieval Node：检索知识库；
5. Rule QA Node：生成角色化问答；
6. Pydantic Validation Node：校验结构化结果；
7. Human Review Node：生成人工审核记录；
8. Evaluation Node：评估结果；
9. Trace Node：记录日志和来源。

建议状态结构：

```json
{
  "task_id": "",
  "scenario": "m1_rule_extraction",
  "user_input": "",
  "document_ids": [],
  "role": "",
  "retrieved_docs": [],
  "extracted_rules": [],
  "validated_result": {},
  "answer": "",
  "eval_result": {},
  "trace_id": ""
}
```

## 8. 日志与观测

第一阶段先做本地日志和评测结果记录。

需要记录：

1. 用户请求；
2. 场景；
3. 模型名称；
4. Prompt 摘要；
5. 检索结果；
6. 输出结果；
7. 来源信息；
8. 结构化校验结果；
9. 评估指标；
10. 错误信息；
11. 耗时。

Langfuse 可以作为后续接入方向，用于 LLM trace、prompt 管理、评分和成本统计。

---

# FILE: docs/04_服务器与模型部署计划.md

# 04 服务器与模型部署计划

## 1. 目标

在实验室开发机或 GPU 服务器上部署 30B 以内或 30B 左右可量化运行的本地模型，通过 OpenAI-compatible API 提供统一调用接口，支撑 M1 规则抽取、M2 RAG 问答、评测 Harness 和后续模型实验。

## 2. Remote SSH 开发方式

当前推荐开发方式：

1. 使用 VS Code Remote SSH 连接开发机；
2. 在远程开发机上 clone 项目仓库；
3. 在远程终端运行后端、前端和模型服务；
4. 通过 GitHub 同步代码；
5. 通过 `.env` 配置模型服务地址和 API key；
6. 由 Codex 辅助生成代码、脚本和实验工具。

注意：

- 不要把服务器密码写入仓库；
- 不要把 IP 写入仓库；
- 不要提交 `.env`；
- 只提交 `.env.example`；
- 系统级安装命令执行前需要人工确认。

## 3. 服务器环境摸底

需要检查：

```bash
nvidia-smi
uname -a
df -h
free -h
python3 --version
nvcc --version || true
docker --version || true
```

需要记录：

1. GPU 型号；
2. 显存大小；
3. CUDA 版本；
4. 驱动版本；
5. 系统版本；
6. Python 版本；
7. 磁盘空间；
8. 内存；
9. Docker 是否可用；
10. 网络访问能力。

## 4. 推理框架选择

### 4.1 vLLM

定位：主力推理服务框架。

适用场景：

1. 本地模型服务化；
2. 多用户并发调用；
3. OpenAI-compatible API；
4. 长上下文 RAG；
5. 模型吞吐测试；
6. 后续服务化部署。

优先级：高。

### 4.2 SGLang

定位：结构化生成和复杂调用流程的对比框架。

适用场景：

1. JSON 结构化输出；
2. 多轮 Agent 调用；
3. 多请求并发；
4. 复杂 Prompt 程序；
5. 与 vLLM 做性能对比。

优先级：中。

### 4.3 llama.cpp

定位：轻量量化模型推理框架。

适用场景：

1. GGUF 模型；
2. Q4/Q5/Q8 量化；
3. 低资源本地推理；
4. 边缘部署可行性测试；
5. 轻量模型测试。

优先级：中。

## 5. 候选文本模型

候选模型需要符合本地硬件条件，优先选择 30B 以内或 30B 左右可量化运行的模型。

### 第一梯队：通用文本与规则理解模型

1. Qwen3-8B  
   用途：快速 baseline、低成本部署、Prompt 调试。

2. Qwen3-14B  
   用途：第一阶段主力候选模型，兼顾效果和部署成本。

3. Qwen3-30B-A3B  
   用途：30B 级 MoE 模型可行性测试。

4. Qwen3-32B  
   用途：30B 级强基线，适合规则理解、结构化抽取和 RAG 问答测试。硬件压力较大时优先使用量化版本。

5. DeepSeek-R1-Distill-Qwen-14B / 32B  
   用途：测试推理型模型在复杂规则理解、条件判断、流程解释中的表现。

### 第二梯队：小模型与轻量部署模型

1. MiniCPM 系列  
   用途：测试小模型在业务规则问答、轻量部署和端侧推理中的表现。

2. MiniCPM-V 系列  
   用途：测试图文混合文档、截图、扫描件、表格图片理解能力。

3. 3B 级小模型  
   用途：测试小模型在 Agent、工具调用、规则问答中的能力边界。

4. Qwen3-4B / Qwen3-1.7B  
   用途：作为轻量 baseline，用于速度、成本和小模型微调实验。

### 第三梯队：国产生态模型

1. GLM 系列  
   用途：结合智谱生态，测试中文规则理解和结构化输出。

2. ERNIE / 文心相关开源模型  
   用途：测试中文文档理解、OCR 后文本理解、业务规则问答。

3. Baichuan / InternLM / Yi 等模型  
   用途：作为补充对比，观察不同国产模型在中文业务规则场景中的差异。

## 6. 文档解析与 OCR 模型

业务规则文档可能包含 PDF、扫描件、图片、表格、印章、公式、复杂排版，因此需要单独调研 OCR 与文档解析模型。

候选方向：

1. PaddleOCR / PP-OCR；
2. PaddleOCR-VL；
3. GLM-OCR；
4. MiniCPM-V；
5. Qwen-VL / Qwen3-VL。

第一阶段优先级：

1. 可编辑文本类文档：直接解析文本；
2. PDF 文档：先尝试文本抽取，再补 OCR；
3. 扫描件/图片：使用 OCR 或多模态模型；
4. 表格类文档：结合 Excel 解析和 OCR 表格识别；
5. 复杂版式文档：纳入后续专项测试。

## 7. Embedding 与 Rerank 模型

候选方向：

1. BGE-M3；
2. bge-reranker 系列；
3. Qwen Embedding 系列；
4. Jina Embeddings / Jina Reranker。

实验指标：

1. Top-K 命中率；
2. 来源命中率；
3. Rerank 后正确片段排序；
4. 问答可追溯率；
5. 响应延迟。

## 8. 模型服务配置

`.env.example` 建议包含：

```env
MODEL_PROVIDER=local
LOCAL_MODEL_BASE_URL=http://127.0.0.1:8000/v1
LOCAL_MODEL_API_KEY=dummy
LOCAL_MODEL_NAME=qwen3-14b
CLOUD_MODEL_BASE_URL=
CLOUD_MODEL_API_KEY=
CLOUD_MODEL_NAME=
EMBEDDING_MODEL_NAME=
RERANK_MODEL_NAME=
VECTOR_DB_PATH=./data/vector_db
```

## 9. Benchmark 指标

每个模型需要记录：

1. 模型名称；
2. 推理框架；
3. 量化方式；
4. 显存占用；
5. 首 token 延迟；
6. 平均生成速度；
7. 并发 1/2/4/8 响应情况；
8. 最大上下文长度；
9. JSON 输出稳定性；
10. 规则抽取准确率；
11. RAG 问答质量；
12. 部署稳定性。

---

# FILE: docs/05_开发任务清单.md

# 05 开发任务清单

## 1. 当前优先级

优先级排序：

1. 服务器环境摸底；
2. 本地模型服务跑通；
3. 后端基础框架；
4. Pydantic 规则 Schema；
5. 文档上传、解析、切分、入库；
6. M2 RAG 问答；
7. M1 规则抽取；
8. 前端基础页面；
9. 评测 Harness；
10. 模型 benchmark；
11. 上下文构建与规则抽取优化。

## 2. 后端基础任务

### Task B1：FastAPI 基础框架

要求：

1. 新增 `/api/health`；
2. 新增配置读取；
3. 新增统一错误处理；
4. 新增日志；
5. 新增基础测试。

验收：

- `pytest` 可运行；
- `GET /api/health` 返回正常；
- `.env.example` 可用于配置。

### Task B2：模型客户端

要求：

1. 支持 OpenAI-compatible API；
2. 支持本地 vLLM；
3. 支持 llama.cpp；
4. 支持云模型 fallback；
5. 支持模型连通性测试。

接口：

- `GET /api/models/list`
- `POST /api/models/test`

验收：

- 可以配置不同模型 endpoint；
- 不硬编码 key；
- 失败时返回清晰错误。

### Task B3：Pydantic 规则 Schema

要求实现：

1. RuleSource；
2. BusinessRule；
3. UDFFieldRule；
4. DocumentExtractResult；
5. RuleReviewResult；
6. EvalResult。

验收：

- 可导出 JSON Schema；
- 有示例 JSON；
- 有基础单元测试。

## 3. RAG 任务

### Task R1：文档上传

要求：

1. 支持 docx/pdf/txt/md/xlsx；
2. 保存文件元信息；
3. 返回 document_id；
4. 记录上传日志。

### Task R2：文档解析与切分

要求：

1. 可编辑文本直接抽取；
2. PDF 先文本抽取；
3. Excel 保留 sheet 和行列信息；
4. chunk 带 metadata；
5. 支持 chunk_id、document_id、section_title、page_no。

### Task R3：向量入库与检索

要求：

1. 支持 embedding；
2. 支持向量检索；
3. 返回来源 chunk；
4. 预留 BM25、Hybrid、Rerank。

### Task R4：M2 规则问答

要求：

1. 输入用户问题；
2. 输入角色；
3. 检索相关规则片段；
4. 组装 Prompt；
5. 返回答案；
6. 返回来源；
7. 记录日志；
8. 生成评估结果。

## 4. M1 规则抽取任务

### Task M1-1：规则抽取 Prompt

要求：

1. 从文档 chunk 中抽取规则；
2. 输出 JSON；
3. 包含规则名称、条件、动作、来源；
4. 不确定时标记 need_human_review。

### Task M1-2：Pydantic 校验

要求：

1. LLM 输出必须经过 Pydantic 校验；
2. 校验失败需要保存错误；
3. 支持人工审核修正。

### Task M1-3：规则审核接口

接口：

- `POST /api/rules/review`
- `GET /api/rules/{rule_id}`
- `GET /api/documents/{document_id}/rules`

## 5. 前端与 Harness 任务

### Task F1：首页 Dashboard

展示：

1. 文档数量；
2. 规则数量；
3. 测试任务数量；
4. 模型服务状态；
5. 最近实验结果。

### Task F2：文档管理页面

功能：

1. 上传文档；
2. 查看文档列表；
3. 查看解析状态；
4. 触发入库；
5. 查看 chunk。

### Task F3：规则问答页面

功能：

1. 选择知识库；
2. 选择角色；
3. 输入问题；
4. 展示答案；
5. 展示来源；
6. 展示模型信息。

### Task F4：规则抽取页面

功能：

1. 选择文档；
2. 触发规则抽取；
3. 展示抽取结果；
4. 展示 Pydantic 校验结果；
5. 支持人工审核。

### Task F5：评测 Harness 页面

功能：

1. 管理测试集；
2. 选择模型；
3. 批量运行；
4. 展示指标；
5. 导出结果。

## 6. 实验任务

### Task E1：模型部署实验

记录：

1. 模型名称；
2. 推理框架；
3. 量化方式；
4. 显存；
5. 延迟；
6. tokens/s；
7. 并发能力。

### Task E2：规则抽取实验

记录：

1. JSON 合法率；
2. Pydantic 校验通过率；
3. 人工审核修改率；
4. 来源引用完整率；
5. 不同模型对比。

### Task E3：RAG 问答实验

记录：

1. Top-K 命中率；
2. 来源命中率；
3. 答案可追溯率；
4. 幻觉率；
5. 响应延迟；
6. token 消耗。

## 7. 技术方向调研任务

从项目中的实际问题出发，后续可调研：

1. Pydantic 约束结构化抽取；
2. RAG 上下文构建优化；
3. 本地模型与量化模型能力边界；
4. OCR 与文档解析专项优化；
5. Agent 流程与评估；
6. 人工审核反馈闭环；
7. LoRA / QLoRA 在规则抽取任务中的效果。

---

# FILE: docs/06_Remote_SSH_开发流程.md

# 06 Remote SSH 开发流程

## 1. 目标

使用 VS Code Remote SSH 连接 Linux 开发机，在远程环境中进行项目开发、模型部署、后端服务运行和实验测试。

## 2. 安全原则

1. 不要把服务器密码写入仓库；
2. 不要把服务器 IP 写入仓库；
3. 不要提交 `.env`；
4. 不要提交 API key；
5. 不要在文档中记录真实 token；
6. 不要让 Codex 执行破坏性系统命令，除非人工确认；
7. 所有服务器环境修改先记录，再执行。

## 3. 推荐目录

远程开发机建议目录：

```bash
mkdir -p ~/projects
cd ~/projects
git clone <REPO_URL> aimodel-udf-explorer
cd aimodel-udf-explorer
```

## 4. Python 环境

建议使用 venv 或 conda。

venv 示例：

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt
```

conda 示例：

```bash
conda create -n aimodel-udf python=3.11 -y
conda activate aimodel-udf
pip install -U pip
pip install -r requirements.txt
```

## 5. 环境变量

创建 `.env`：

```bash
cp .env.example .env
```

`.env` 仅保存在服务器本地，不提交 Git。

## 6. 服务器摸底命令

```bash
nvidia-smi
uname -a
df -h
free -h
python3 --version
nvcc --version || true
docker --version || true
```

建议把输出保存到：

```text
experiments/results/server_env_check.md
```

注意：不要把敏感 IP、用户名、内网路径写入公开仓库。

## 7. 本地模型服务启动方式

### vLLM 示例

```bash
export MODEL_NAME=<model_name_or_path>
python -m vllm.entrypoints.openai.api_server \
  --model "$MODEL_NAME" \
  --host 0.0.0.0 \
  --port 8000
```

### llama.cpp 示例

```bash
export GGUF_MODEL_PATH=<path_to_model.gguf>
./llama-server \
  -m "$GGUF_MODEL_PATH" \
  --host 0.0.0.0 \
  --port 8001
```

具体命令需要根据服务器实际环境调整。

## 8. 后端启动

示例：

```bash
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
```

## 9. 前端启动

示例：

```bash
cd frontend
npm install
npm run dev
```

## 10. Codex 使用方式

### 方式一：在本地 VS Code 使用 Codex

适合：

1. 改代码；
2. 生成文档；
3. 生成接口；
4. 写测试；
5. 写脚本。

### 方式二：Remote SSH 后在远程终端使用 Codex CLI

适合：

1. 检查服务器环境；
2. 调试 Python 依赖；
3. 运行模型服务；
4. 执行 benchmark；
5. 修复远程环境相关问题。

使用原则：

1. 先让 Codex 读 `AGENTS.md`；
2. 每次只给一个明确任务；
3. 执行系统级命令前人工确认；
4. 不要让 Codex 自动修改 CUDA、驱动或系统包；
5. 对每次改动要求说明 changed files、run commands、test results。

## 11. Git 工作流

建议：

```bash
git checkout -b feat/backend-scaffold
# 修改代码
git add .
git commit -m "feat: add backend scaffold"
git push origin feat/backend-scaffold
```

每个任务尽量一个小分支。

## 12. 调试记录

建议把实验结果放到：

```text
experiments/results/
```

文件命名：

```text
YYYYMMDD_model_benchmark.md
YYYYMMDD_rag_eval.md
YYYYMMDD_rule_extraction_eval.md
```

---

# FILE: scripts/README_scripts.md

# scripts 目录说明

建议后续由 Codex 生成以下脚本。

## 1. check_gpu.sh

用途：

- 检查 GPU、CUDA、驱动、内存、磁盘、Python、Docker。

## 2. setup_env.sh

用途：

- 创建 Python 环境；
- 安装基础依赖；
- 不建议自动安装 CUDA/驱动。

## 3. start_vllm.sh

用途：

- 启动 vLLM OpenAI-compatible API；
- 模型名从环境变量读取。

## 4. start_sglang.sh

用途：

- 启动 SGLang 服务；
- 用于后续对比。

## 5. start_llamacpp.sh

用途：

- 启动 llama.cpp server；
- GGUF 模型路径从环境变量读取。

## 6. benchmark_model.py

用途：

- 调用 OpenAI-compatible API；
- 记录首 token 延迟、总耗时、tokens/s、错误信息。

## 7. run_rag_eval.py

用途：

- 批量运行 RAG 问答测试集；
- 输出来源命中率、回答可追溯率、延迟。

## 8. run_rule_extract_eval.py

用途：

- 批量运行规则抽取测试；
- 输出 JSON 合法率、Pydantic 校验通过率、人工审核修改率。