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
