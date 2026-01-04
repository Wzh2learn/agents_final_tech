# 📖 项目文档

欢迎来到建账规则助手系统的文档中心。本系统已从 Dify 迁移至基于 LangChain + LangGraph 的自研架构。

---

## 📖 快速导航

### 🆕 新手入门

1. **[部署指南 (DEPLOYMENT.md)](DEPLOYMENT.md)** - 从零开始部署项目：环境配置、数据库初始化、启动服务
2. **[开发者指南 (DEVELOPER_GUIDE.md)](DEVELOPER_GUIDE.md)** - 项目架构、开发规范、添加新功能、测试指南
3. **[API 参考 (API_REFERENCE.md)](API_REFERENCE.md)** - 完整的 REST API 接口文档

### 🛠️ 开发参考

1. **[工具使用说明 (../TOOLS_USAGE.md)](../TOOLS_USAGE.md)** - 所有工具的用途、调用路径、使用示例

### 📦 历史归档

1. **[归档目录](./archive/)** - 迁移过程中的原始记录、旧版设计、VibeCoding指南、架构审查报告、优化实施报告

---

## 📚 文档目录树

```
docs/
├── README.md              # 本文档（导航中心）
├── DEVELOPER_GUIDE.md     # 开发者指南
├── API_REFERENCE.md       # API 参考文档
├── DEPLOYMENT.md          # 部署指南
└── archive/               # 历史记录归档
    ├── VibeCoding_Migration_Kit_Merged.md
    └── [其他历史文档]
```

---

**最后更新**: 2026-01-05

---

## 🆕 最新更新 (2026-01-05)

### 架构优化与前端增强
- ✅ 统一API错误处理封装 (apiCall + showToast)
- ✅ WebSocket自动重连机制 (指数退避策略)
- ✅ 配置外部化 (新增config.js)
- ✅ 完善会话管理API (CRUD + 历史消息)
- ✅ 为关键函数添加JSDoc注释
- ✅ 代码质量提升：错误处理覆盖率95%，代码注释率40%

### 代码清理
- ✅ 删除废弃的collaboration和rag_config独立页面（已集成到chat和knowledge）
- ✅ 清理临时行动记录文档
- ✅ 归档架构审查和优化实施报告

详见：[归档文档 - 优化实施报告](./archive/OPTIMIZATION_IMPLEMENTATION_REPORT.md)
