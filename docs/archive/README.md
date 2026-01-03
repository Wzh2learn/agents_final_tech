# 归档文档说明

本目录包含项目开发过程中的历史文档，这些文档记录了项目的开发历程和阶段性成果。

## 📚 文档列表

### 开发计划与报告

| 文档 | 说明 | 归档日期 |
|------|------|----------|
| `DEVELOPMENT_PLAN.md` | 项目开发计划（已完成功能的清单） | 2025-01-03 |
| `FINAL_REPORT.md` | 最终测试报告（~92% 完成度） | 2025-01-03 |
| `PROJECT_SUMMARY.md` | 项目总结（Dify 迁移 + RAG 功能） | 2025-01-03 |

### 功能总结

| 文档 | 说明 | 归档日期 |
|------|------|----------|
| `NEW_FEATURES_SUMMARY.md` | 优先级 2 和 3 功能完成总结（知识库管理 + 高级 RAG） | 2025-01-03 |
| `OPTIMIZATION_SUMMARY.md` | 短期优化功能总结（真实数据库、持久化存储、缓存） | 2025-01-03 |

### 指南文档

| 文档 | 说明 | 归档日期 |
|------|------|----------|
| `GUIDE_DOCUMENT_TESTING.md` | 文档解析测试指南 | 2025-01-02 |
| `GUIDE_KNOWLEDGE_MIGRATION.md` | Dify 知识库迁移方案 | 2025-01-02 |

### 临时和流程文档

| 文档 | 说明 | 归档日期 |
|------|------|----------|
| `NEW_SSH_KEY.md` | SSH 密钥更新记录 | 2025-01-03 |
| `DOCUMENT_REORGANIZATION_REPORT.md` | 文档整理报告（v1） | 2025-01-03 |
| `SSH_SETUP_GUIDE.md` | SSH 配置指南（旧版） | 2025-01-03 |

### 快速开始与 RAG 指南（已合并）

| 文档 | 说明 | 归档日期 | 合并到 |
|------|------|----------|--------|
| `QUICK_START.md` | 快速开始指南 | 2025-01-03 | README.md |
| `RAG_API_GUIDE.md` | RAG API 方案使用指南 | 2025-01-03 | docs/RAG_GUIDE.md |
| `RAG_USAGE_GUIDE.md` | RAG 功能使用指南 | 2025-01-02 | docs/RAG_GUIDE.md |

---

## 📋 文档整理说明

### 整理时间
2025年1月3日

### 整理目的
- 精简项目文档，提高可读性
- 保留历史记录，方便查阅
- 合并重复内容，避免信息分散

### 整理结果
- **整理前（第1次）**：13 个文档分散在多个位置
- **整理后（第1次）**：3 个核心文档 + 10 个归档文档，精简率 77%
- **整理后（第2次）**：5 个核心文档 + 14 个归档文档，精简率 74%

### 核心文档（最新）

1. **README.md** - 项目主文档
   - 包含项目介绍、快速开始、功能特性、技术架构、文档导航

2. **docs/INDEX.md** - 文档导航索引
   - 快速查找所需文档

3. **docs/CONFIGURATION.md** - 配置说明文档
   - 详细的配置项说明
   - 环境变量配置指南

4. **docs/DEPLOYMENT_GUIDE.md** - 部署和协作指南
   - Git 使用指南
   - 部署到生产环境
   - 日常开发流程

5. **docs/RAG_GUIDE.md** - RAG 完整指南
   - RAG 功能使用指南
   - API 文档
   - 使用示例

6. **docs/PROJECT_HEALTH_CHECK.md** - 健康检查报告
   - 项目健康度评估
   - 测试结果
   - 改进建议

---

## 🔍 查阅历史文档的建议

### 如果您想了解：

- **项目开发计划** → 查看 `DEVELOPMENT_PLAN.md`
- **功能完成情况** → 查看 `FINAL_REPORT.md` 或 `PROJECT_SUMMARY.md`
- **新增功能的详细实现** → 查看 `NEW_FEATURES_SUMMARY.md`
- **优化功能的详细实现** → 查看 `OPTIMIZATION_SUMMARY.md`
- **文档测试方法** → 查看 `GUIDE_DOCUMENT_TESTING.md`
- **Dify 知识库迁移方案** → 查看 `GUIDE_KNOWLEDGE_MIGRATION.md`
- **原始的快速开始步骤** → 查看 `QUICK_START.md`
- **原始的 RAG API 指南** → 查看 `RAG_API_GUIDE.md`
- **原始的 RAG 使用指南** → 查看 `RAG_USAGE_GUIDE.md`

---

## ⚠️ 注意事项

1. **归档文档仅供参考**：这些文档记录了开发过程，可能与当前实现有差异
2. **优先使用核心文档**：日常使用请参考 README.md、CONFIGURATION.md 和 RAG_GUIDE.md
3. **内容已合并**：归档文档中的有用信息已经合并到核心文档中
4. **历史记录**：保留这些文档可以追溯项目的发展历程

---

## 📝 更新日志

### 2025-01-03（第2次整理）
- 创建 docs/INDEX.md 文档导航索引
- 创建 docs/README.md 文档目录入口
- 新增归档：NEW_SSH_KEY.md, DOCUMENT_REORGANIZATION_REPORT.md, SSH_SETUP_GUIDE.md
- 优化 README.md，添加文档导航
- 新增 docs/PROJECT_HEALTH_CHECK.md 健康检查报告
- 归档文档总数：14 个

### 2025-01-03（第1次整理）
- 创建归档目录
- 移动 10 个历史文档到归档目录
- 合并 QUICK_START.md 到 README.md
- 合并 RAG_API_GUIDE.md 和 RAG_USAGE_GUIDE.md 到 RAG_GUIDE.md
- 创建本说明文档
