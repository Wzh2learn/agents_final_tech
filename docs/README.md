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
2. **[重构蓝图 (../REFACTOR_PRP_BLUEPRINT.md)](../REFACTOR_PRP_BLUEPRINT.md)** - 最新的架构调研和重构方案

### 📦 历史归档

1. **[归档目录](./archive/)** - 迁移过程中的原始记录、旧版设计、VibeCoding指南

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

**最后更新**: 2026-01-04

---

## 🆕 最新更新 (2026-01-04)

- ✅ 新增主页导航界面，统一入口访问四大功能
- ✅ 实现父子分段模式，支持两级文档分割
- ✅ 增强答案溯源，支持精确位置标注和引用高亮
- ✅ 实现结构化规则解读，支持规则字典模式输出
- ✅ 完善文档体系，新增工具使用说明和重构蓝图
