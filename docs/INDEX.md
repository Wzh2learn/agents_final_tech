# 📚 项目文档索引

欢迎来到建账规则助手系统的文档中心。本文档将帮助您快速找到所需的文档。

---

## 🎯 快速导航

### 🆕 新手入门

- [**README.md**](../README.md) - 项目总览和快速开始
- [**docs/CONFIGURATION.md**](./CONFIGURATION.md) - 配置说明
- [**docs/DEPLOYMENT_GUIDE.md**](./DEPLOYMENT_GUIDE.md) - 部署和协作指南

### 🛠️ 核心功能

- [**docs/RAG_GUIDE.md**](./RAG_GUIDE.md) - RAG 知识检索使用指南
- [**docs/PROJECT_HEALTH_CHECK.md**](./PROJECT_HEALTH_CHECK.md) - 项目健康检查报告

### 📦 历史文档

- [**docs/archive/**](./archive/) - 归档的历史文档

---

## 📖 文档详细说明

### 1. README.md

**位置**: 项目根目录

**内容**:
- 项目简介和功能特性
- 快速开始指南
- 技术架构说明
- 项目结构说明
- 核心功能使用
- 常见问题

**适用人群**: 所有用户

---

### 2. docs/CONFIGURATION.md

**位置**: `docs/CONFIGURATION.md`

**内容**:
- 配置文件说明
- 数据库配置
- Embedding 模型配置
- RAG 配置
- Web 服务配置
- 环境变量配置

**适用人群**: 开发者和运维人员

---

### 3. docs/DEPLOYMENT_GUIDE.md

**位置**: `docs/DEPLOYMENT_GUIDE.md`

**内容**:
- 方案一：推送到 GitHub
- 方案二：下载到本地修改
- 环境配置步骤
- 日常开发流程
- Git 最佳实践
- 常见问题解决

**适用人群**: 开发者和协作者

---

### 4. docs/RAG_GUIDE.md

**位置**: `docs/RAG_GUIDE.md`

**内容**:
- RAG 功能简介
- 问题类型分类
- 检索策略说明
- 高级功能使用
- API 接口说明
- 使用示例

**适用人群**: 开发者和高级用户

---

### 5. docs/PROJECT_HEALTH_CHECK.md

**位置**: `docs/PROJECT_HEALTH_CHECK.md`

**内容**:
- 项目健康度评估
- 依赖检查结果
- 代码检查结果
- 测试结果
- 改进建议

**适用人群**: 项目维护者和贡献者

---

## 📦 归档文档 (docs/archive/)

归档目录包含历史文档和临时文档，用于记录项目发展历程。

### 归档文档列表

- `README.md` - 归档文档索引
- `DEVELOPMENT_PLAN.md` - 项目开发计划
- `FINAL_REPORT.md` - 项目最终报告
- `GUIDE_DOCUMENT_TESTING.md` - 文档测试指南
- `GUIDE_KNOWLEDGE_MIGRATION.md` - 知识库迁移指南
- `NEW_FEATURES_SUMMARY.md` - 新功能总结
- `OPTIMIZATION_SUMMARY.md` - 优化总结
- `PROJECT_SUMMARY.md` - 项目总结
- `QUICK_START.md` - 快速开始（旧版）
- `RAG_API_GUIDE.md` - RAG API 指南（旧版）
- `RAG_USAGE_GUIDE.md` - RAG 使用指南（旧版）
- `NEW_SSH_KEY.md` - SSH 密钥更新记录
- `DOCUMENT_REORGANIZATION_REPORT.md` - 文档整理报告
- `SSH_SETUP_GUIDE.md` - SSH 配置指南（旧版）

---

## 🚀 根据需求选择文档

### 我想快速上手

1. 阅读 [README.md](../README.md) 了解项目
2. 运行 `./scripts/quick_start.sh` 启动服务
3. 访问 http://localhost:5000 使用系统

### 我想部署到生产环境

1. 阅读 [docs/DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md)
2. 配置 `.env` 文件
3. 运行 `./scripts/init_db.sh` 初始化数据库
4. 使用 `./scripts/quick_start.sh` 启动服务

### 我想配置 RAG 功能

1. 阅读 [docs/RAG_GUIDE.md](./RAG_GUIDE.md)
2. 编辑 `config/app_config.json` 中的 RAG 配置
3. 根据需要调整检索策略
4. 重启服务生效

### 我想参与开发

1. 阅读 [docs/DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md) 中的"日常开发流程"
2. 配置开发环境
3. 查看代码结构
4. 运行测试确保功能正常

### 我想了解项目状态

1. 阅读 [docs/PROJECT_HEALTH_CHECK.md](./PROJECT_HEALTH_CHECK.md)
2. 查看测试覆盖率
3. 了解已知问题和改进建议

---

## 📝 文档更新记录

| 日期 | 更新内容 |
|------|----------|
| 2025-01-03 | 创建文档索引，整理核心文档 |
| 2025-01-03 | 新增健康检查报告 |
| 2025-01-03 | 归档临时和历史文档 |
| 2025-01-03 | 新增部署和协作指南 |
| 2025-01-03 | 新增 RAG 完整指南 |

---

## 💡 文档贡献

如果您发现文档有错误或需要补充，欢迎：

1. 提交 Issue 描述问题
2. 提交 Pull Request 修改文档
3. 联系项目维护者

---

**最后更新**: 2025-01-03
