# Codex 启动提示词

请把下面这段内容粘贴到开发机的 Codex CLI。

---

你现在接手的是 `JinRongAgents` 仓库中的 M1/M2 本地模型与 Agent 接入工作。

请先完整阅读：

1. `AGENTS.md`
2. `HANDOFF.md`
3. `docs/AGENTS.md`
4. `docs/05_开发任务清单.md`
5. `docs/12_阶段收尾与对外汇报.md`
6. `docs/09_OpenCode与现有RAG_MCP实施方案.md`
7. `docs/10_OpenCode开发机运行说明.md`

然后检查 Git 状态、Conda 环境、PostgreSQL/PGVector、Qwen3-14B 服务、
OpenCode 和 `jinrong-rag` MCP，不要先改代码。

## 项目目标

本项目在现有 JinRongAgents 系统上扩展 M1/M2 模型实验与 Agent 接入能力，用于业务规则文档解析、结构化规则抽取、RAG 规则问答、本地模型部署、模型效果评测和实验记录。

当前阶段聚焦 M1 和 M2：

- M1：业务规则文档解析与结构化规则抽取；
- M2：业务规则知识库与角色化 RAG 问答。

项目需要优先完成可运行 Demo、可复用模块、可评测实验链路，不要一开始做复杂生产级系统。

## 当前开发环境设想

项目会在远程 Linux 开发机上通过 VS Code Remote SSH 开发。后续会在 GPU 服务器上部署本地模型服务，优先调研 vLLM，也可以保留 SGLang 和 llama.cpp 作为对比方案。

本地模型需要通过 OpenAI-compatible API 提供服务，后端通过统一 ModelClient 调用。

## 你的当前任务

1. 核验开发机上 PostgreSQL/PGVector、14B 16K 服务、OpenCode 与 MCP；
2. 确认已完成的 20/20 只读 MCP/OpenCode 稳定性验收，不重复无必要运行；
3. 取得负责人批准的 M2 标签—来源映射和人工答案质量标注；
4. 使用已有 20 条合成脱敏夹具和评测器建立正式 M2 基线；
5. 建立 M1 OCR/规则抽取数值基线后，再单变量比较检索与重排方案。

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

先报告已完成、待完成、当前服务状态和本轮第一项任务，然后直接完成可以安全
完成的工作。不要自动修改 CUDA、驱动、系统网络，不要覆盖未提交改动或远端
stash。
