---
name: generate-commit
description: 智能提交信息生成器 - 根据代码变更自动生成规范的 Git 提交信息
user-invocable: true
allowed-tools:
  - Bash
  - Read
  - Grep
version: 1.0.0
---

# 智能提交信息生成器

## 用途

根据代码变更自动生成规范的 Git 提交信息，遵循 Conventional Commits 规范。

## 如何触发

```
/commit
```

或者：

```
帮我生成提交信息
```

## 提交信息格式

遵循 Conventional Commits 规范：

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Type 类型

| 类型 | 说明 |
|------|------|
| feat | 新功能 |
| fix | Bug 修复 |
| docs | 文档更新 |
| style | 代码格式（不影响功能） |
| refactor | 重构（不是新功能也不是修复） |
| perf | 性能优化 |
| test | 测试相关 |
| chore | 构建/工具相关 |

### Scope 范围

可选，表示影响的模块，如：
- `auth` - 认证模块
- `api` - API 接口
- `db` - 数据库
- `ui` - 用户界面

## 工作流程

1. **分析变更**：读取 `git diff --staged` 或 `git diff`
2. **识别类型**：根据变更内容判断提交类型
3. **生成信息**：生成符合规范的提交信息
4. **确认提交**：让你确认后执行提交

## 示例

### 输入

```bash
git diff --staged
# 显示修改了 src/auth/login.py，添加了登录失败次数限制
```

### 输出

```
feat(auth): 添加登录失败次数限制

- 登录失败 5 次后锁定账号 15 分钟
- 添加 login_attempts 字段记录失败次数
- 添加 locked_until 字段记录锁定时间

Co-Authored-By: Claude <noreply@anthropic.com>
```

## 最佳实践

### Subject 主题行

- 使用祈使句（"添加"而不是"添加了"）
- 不超过 50 个字符
- 首字母小写（英文）
- 不加句号

### Body 正文

- 解释"做了什么"和"为什么"
- 每行不超过 72 个字符
- 使用列表说明多个变更

### Footer 页脚

- 关联 Issue：`Closes #123`
- 破坏性变更：`BREAKING CHANGE: xxx`
- 协作者：`Co-Authored-By: xxx`

## 配置

可以在项目中创建 `.commitrc.yml` 自定义规则：

```yaml
# .commitrc.yml
types:
  - feat
  - fix
  - docs
  - refactor

scopes:
  - auth
  - api
  - db
  - ui

rules:
  subject_max_length: 50
  body_max_line_length: 72
  require_scope: false
  require_body: true
```

## 注意事项

- 确保已暂存要提交的文件（`git add`）
- 一次提交只做一件事
- 提交信息要清晰描述变更内容
- 不要提交敏感信息（密码、密钥等）
