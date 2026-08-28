---
name: vibe-coding-refinement
description: Vibe Coding 代码精炼器 - 通过迭代方式逐步优化 AI 生成的代码
user-invocable: true
allowed-tools:
  - Read
  - Edit
  - Bash
  - Glob
skills:
  - vibe-coding-principles
  - vibe-coding-quality-gate
version: 1.0.0
---

# Vibe Coding 代码精炼器

## 用途

针对"AI 首次生成的代码"，按迭代方式逐步优化：
- 可读性
- 性能
- 安全性
- 可测试性

遵循"生成 → 检查 → 精炼"的短循环，一次解决 1-2 个问题，逐步打磨代码质量。

## 如何触发

你可以这样对我说：

```
帮我精炼一下刚才生成的代码
```

或者：

```
对 @src/utils/data_processor.py 进行性能优化
```

## 精炼循环（推荐用法）

### 第一步：只找问题，不修改

```
用户：先帮我分析一下这段代码有哪些可以改进的地方，
     按优先级排序，但先不要修改。

AI：[输出问题清单，按优先级排序]
```

**为什么这样做？**
- 避免一次性改动过多导致混乱
- 让你有机会选择优先解决哪些问题
- 便于理解每个问题的影响范围

### 第二步：选择 1-2 个问题进行修改

```
用户：好的，我们先解决第 1 和第 2 个问题（性能优化）。

AI：[只针对这两个问题进行修改]
```

**为什么这样做？**
- 每次迭代都有明确的改进目标
- 便于验证改进效果
- 降低引入新 bug 的风险

### 第三步：运行测试验证

```
用户：运行单元测试，确保功能正常。

AI：[运行测试，报告结果]
```

**为什么这样做？**
- 确保优化没有破坏原有功能
- 及时发现问题
- 建立信心

### 第四步：重复循环

```
用户：测试通过了，继续解决第 3 个问题（可读性）。

AI：[继续精炼]
```

## 精炼维度

### 1. 可读性（Readability）
- 变量命名是否清晰
- 函数是否过长（建议 < 50 行）
- 逻辑是否清晰（避免深层嵌套）
- 注释是否必要且准确

### 2. 性能（Performance）
- 算法复杂度是否合理
- 是否有不必要的重复计算
- 数据结构选择是否合适
- 是否有明显的性能瓶颈

### 3. 安全性（Security）
- 输入验证是否充分
- 是否有注入风险
- 敏感信息是否安全处理
- 错误信息是否泄露细节

### 4. 可测试性（Testability）
- 函数是否职责单一
- 依赖是否可以 mock
- 是否有副作用
- 边界条件是否考虑

## 前后对比示例

### 示例 1：性能优化（O(n²) → O(n)）

#### ❌ 优化前
```python
def find_duplicates(items):
    """查找列表中的重复项"""
    duplicates = []
    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            if items[i] == items[j] and items[i] not in duplicates:
                duplicates.append(items[i])
    return duplicates
```

**问题**：
- 时间复杂度 O(n²)，数据量大时性能差
- 使用 `in` 检查列表，又增加了复杂度

#### ✅ 优化后
```python
def find_duplicates(items):
    """查找列表中的重复项"""
    seen = set()
    duplicates = set()

    for item in items:
        if item in seen:
            duplicates.add(item)
        else:
            seen.add(item)

    return list(duplicates)
```

**改进**：
- 时间复杂度降低到 O(n)
- 使用 set 提高查找效率
- 代码更简洁清晰

### 示例 2：可读性优化

#### ❌ 优化前
```python
def p(d):
    r = []
    for k, v in d.items():
        if v > 0:
            r.append(k)
    return r
```

**问题**：
- 变量名不清晰（d, r, k, v）
- 函数名不明确（p）
- 缺少文档字符串

#### ✅ 优化后
```python
def get_positive_keys(data_dict):
    """
    获取字典中值为正数的所有键

    Args:
        data_dict: 包含数值的字典

    Returns:
        值为正数的键列表
    """
    positive_keys = []
    for key, value in data_dict.items():
        if value > 0:
            positive_keys.append(key)
    return positive_keys
```

**改进**：
- 变量名清晰表达含义
- 函数名描述功能
- 添加文档字符串

### 示例 3：安全性优化

#### ❌ 优化前
```python
def execute_query(user_input):
    """执行用户查询"""
    query = f"SELECT * FROM users WHERE name = '{user_input}'"
    return db.execute(query)
```

**问题**：
- SQL 注入风险
- 直接拼接用户输入

#### ✅ 优化后
```python
def execute_query(user_input):
    """
    执行用户查询（使用参数化查询防止 SQL 注入）

    Args:
        user_input: 用户输入的查询条件

    Returns:
        查询结果
    """
    # 使用参数化查询
    query = "SELECT * FROM users WHERE name = ?"
    return db.execute(query, (user_input,))
```

**改进**：
- 使用参数化查询防止 SQL 注入
- 添加安全说明

## 精炼策略

### 首次生成：快速实现核心功能
- 重点：功能正确性
- 不追求完美
- 快速验证想法

### 第一轮精炼：可读性和代码风格
- 优化命名
- 简化逻辑
- 添加必要注释
- 符合代码规范

### 第二轮精炼：性能优化
- 识别性能瓶颈
- 优化算法复杂度
- 改进数据结构
- 减少不必要的计算

### 第三轮精炼：安全加固和边界情况
- 添加输入验证
- 处理异常情况
- 考虑边界条件
- 安全审查

### 第四轮精炼：可测试性
- 拆分复杂函数
- 减少副作用
- 依赖注入
- 添加单元测试

## 与其他技能的配合

### 与 quality-gate 配合
```
1. AI 生成代码
2. 运行 quality-gate（快速发现问题）
3. 使用 refinement 逐步优化
4. 再次运行 quality-gate（验证改进）
```

### 与 code-review 配合
```
1. 完成多轮 refinement
2. 运行 code-review（深度审查）
3. 根据审查意见再次 refinement
4. 最终提交
```

## 遵循的原则

本技能严格遵循 Vibe Coding 的核心原则：

1. **迭代优化**：短循环，逐步改进
2. **质量前移**：每轮迭代后都验证
3. **分层设计**：按维度分层优化

## 注意事项

- 不要追求一次性完美，允许多轮迭代
- 每次只解决 1-2 个问题，避免改动过多
- 每轮迭代后都要运行测试
- 优先解决高优先级问题（安全 > 性能 > 可读性）
- 保持代码的向后兼容性

## 快速参考

**精炼循环**：找问题 → 选 1-2 个 → 修改 → 测试 → 重复

**精炼维度**：可读性、性能、安全性、可测试性

**触发命令**：`帮我精炼一下刚才生成的代码`

**配合技能**：quality-gate（快速检查）、code-review（深度审查）
