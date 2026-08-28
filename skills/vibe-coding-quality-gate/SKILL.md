---
name: vibe-coding-quality-gate
description: Vibe Coding 质量闸门 - 在代码生成后立即进行快速质量检查
user-invocable: true
allowed-tools:
  - Read
  - Grep
  - Bash
  - Glob
skills:
  - vibe-coding-principles
version: 1.0.0
---

# Vibe Coding 质量闸门

## 用途

在"AI 已经写完一段代码/一个模块"之后，自动或手动进行快速质量检查，包括：
- 代码风格
- 安全性
- 性能
- 可测试性

这是一个**快速、可自动化的 baseline 检查**，与深度代码审查（code-review）互补。

## 如何触发

你可以这样对我说：

```
对刚才生成的代码运行 quality-gate 检查
```

或者：

```
检查 @src/auth/login.py 的代码质量
```

## 检查维度

### 1. 代码风格（Style）
- 命名规范（变量、函数、类名）
- 代码格式（缩进、空行、行长度）
- 注释质量（是否有必要的注释）
- 代码复杂度（函数长度、嵌套层级）

### 2. 安全性（Security）
- SQL 注入风险
- XSS 攻击风险
- 敏感信息泄露（硬编码密码、API key）
- 不安全的依赖库
- 输入验证缺失

### 3. 性能（Performance）
- 明显的性能问题（N+1 查询、不必要的循环）
- 资源泄露（未关闭的文件、连接）
- 不必要的重复计算
- 低效的数据结构选择

### 4. 可测试性（Testability）
- 函数是否过于复杂（难以测试）
- 是否有硬编码的依赖（难以 mock）
- 是否有副作用（难以隔离测试）
- 边界条件是否考虑

## 配置文件示例

你可以在项目根目录创建 `.qualitygate.yml` 来自定义检查规则：

```yaml
# .qualitygate.yml
style:
  max_function_length: 50  # 函数最大行数
  max_complexity: 10       # 最大圈复杂度
  naming_convention:
    functions: snake_case
    classes: PascalCase
    constants: UPPER_CASE

security:
  check_sql_injection: true
  check_xss: true
  check_hardcoded_secrets: true
  forbidden_patterns:
    - "eval("
    - "exec("
    - "os.system("

performance:
  check_n_plus_one: true
  check_resource_leaks: true
  max_loop_nesting: 3

testability:
  require_docstrings: true
  max_function_params: 5
  avoid_global_state: true
```

## 质量检查报告示例

```markdown
# 质量检查报告

**文件**: src/auth/login.py
**检查时间**: 2026-01-15 10:30:00
**总体评分**: B (75/100)

## 检查结果

### ✅ 通过项 (3)
- 代码格式符合 PEP 8 规范
- 无明显的 SQL 注入风险
- 函数长度合理（平均 25 行）

### ⚠️ 警告项 (2)
1. **性能警告**: `get_user_posts` 函数存在 N+1 查询问题
   - 位置: 第 45-52 行
   - 建议: 使用 JOIN 或预加载优化

2. **可测试性警告**: `send_login_email` 函数直接调用外部 SMTP 服务
   - 位置: 第 78 行
   - 建议: 通过依赖注入传入邮件服务，便于测试时 mock

### ❌ 错误项 (1)
1. **安全错误**: 发现硬编码的 API 密钥
   - 位置: 第 12 行 `API_KEY = "sk-1234567890"`
   - 严重程度: 高
   - 建议: 使用环境变量或密钥管理服务

## 详细建议

### 优先修复（高优先级）
1. 移除硬编码的 API 密钥，改用环境变量
   ```python
   # 修改前
   API_KEY = "sk-1234567890"

   # 修改后
   import os
   API_KEY = os.getenv("API_KEY")
   ```

### 建议优化（中优先级）
2. 优化 N+1 查询问题
   ```python
   # 修改前
   for user in users:
       user.posts = db.query(Post).filter(Post.user_id == user.id).all()

   # 修改后
   users = db.query(User).options(joinedload(User.posts)).all()
   ```

3. 改进可测试性
   ```python
   # 修改前
   def send_login_email(user_email):
       smtp.send(user_email, "Login notification")

   # 修改后
   def send_login_email(user_email, email_service=None):
       service = email_service or default_email_service
       service.send(user_email, "Login notification")
   ```

## 下一步行动

1. 立即修复安全错误（硬编码密钥）
2. 运行单元测试确保功能正常
3. 考虑进行深度代码审查（使用 code-review 技能）
```

## 与 code-review 的配合

### quality-gate（质量闸门）
- **目的**: 快速、自动化的 baseline 检查
- **时机**: 代码生成后立即执行
- **范围**: 常见问题、明显缺陷
- **速度**: 快速（几秒钟）
- **适用**: 每次代码生成后

### code-review（代码审查）
- **目的**: 深度、全面的代码审查
- **时机**: 功能完成后、提交前
- **范围**: 架构设计、业务逻辑、边界情况
- **速度**: 较慢（几分钟）
- **适用**: 重要功能、复杂逻辑

### 推荐工作流

```
1. AI 生成代码
   ↓
2. 运行 quality-gate（快速检查）
   ↓
3. 修复明显问题
   ↓
4. 运行单元测试
   ↓
5. 运行 code-review（深度审查）
   ↓
6. 最终优化
   ↓
7. 提交代码
```

## 自动化集成

你可以将 quality-gate 集成到开发流程中：

### Git Pre-commit Hook
```bash
#!/bin/bash
# .git/hooks/pre-commit

echo "Running quality gate checks..."
claude-code run quality-gate --files $(git diff --cached --name-only)

if [ $? -ne 0 ]; then
    echo "Quality gate failed. Please fix the issues before committing."
    exit 1
fi
```

### CI/CD Pipeline
```yaml
# .github/workflows/quality-check.yml
name: Quality Gate

on: [push, pull_request]

jobs:
  quality-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run Quality Gate
        run: |
          claude-code run quality-gate --all
```

## 遵循的原则

本技能严格遵循 Vibe Coding 的核心原则：

1. **质量前移**：在代码生成后立即检查，而不是等到上线后
2. **迭代优化**：快速发现问题，逐步改进
3. **分层设计**：quality-gate 做快速检查，code-review 做深度审查

## 注意事项

- quality-gate 不能替代人工代码审查，只是第一道防线
- 检查规则可以根据项目需求自定义
- 不要过度追求完美，重点关注高优先级问题
- 自动化检查可能有误报，需要人工判断

## 快速参考

**检查命令**：`对刚才生成的代码运行 quality-gate 检查`

**检查维度**：风格、安全、性能、可测试性

**配置文件**：`.qualitygate.yml`

**与 code-review 的区别**：快速 baseline 检查 vs 深度全面审查
