# 🚀 Vibe Coding 跨项目迁移包（终极合并版）

> 目的：把在 AlgoQuest3 中验证过的 **Vibe Coding 方法论 + Windsurf Rules + Workflows + Prompt 模板 + 工程化 Checklists** 打包成一份可复制文件，迁移到任意新项目。

---

## 0) TL;DR（最小可用套件）

- **先贴 Rules**：把下文 `2) .windsurfrules 模板` 复制到新项目 `.windsurfrules`
- **再加 Workflows**：把下文 `3) Workflows 模板` 生成到 `.windsurf/workflows/`
- **最后用 Prompt 启动**：用 `4) Kill Prompts` 的模板启动对话
- **每次改动都跑验证**：`npm run lint` + `npm run build`（或项目对应命令）

---

## 1) Vibe Coding 核心技能（合并版：基础 + 深度）

### 1.1 Intent-Driven（意图驱动，而不是代码驱动）
- **用“契约/行为”描述需求**，不要用“改哪几行”描述需求。
  - 例：
    - 不佳："给函数加个参数"
    - 更佳："把 XHS 数据流从 UI 直读改为 Query 接口，保证向后兼容并为 RAG 预留扩展点"

### 1.2 Context-First（上下文先行）
- **先让 AI 建立数据流心智模型**：入口在哪里、状态中心在哪里、真理来源在哪里。
- **只读必要文件**：优先 `README/ARCHITECTURE/SOP` + 入口文件 + 状态管理 + 类型定义。
- **锚点引用（Anchored Citations）**：要求 AI 用 `path#Lx-Ly`（或 IDE 的可点击引用）来描述结论，减少“凭空猜”。

### 1.3 PRP Blueprint（先蓝图后实现）
- 复杂需求必须先产出 PRP：
  - Goal & Success Criteria
  - Non-Goals
  - Design / Steps（按顺序）
  - Docs 更新计划
  - Validation Loop（命令 + 手测回归点）
- 你确认“Start”后才允许动代码。

### 1.4 Atomic Edits（原子化修改）
- 一次只做一个闭环：
  - 数据结构/类型 → 状态层/Service → UI → 集成点 → 文档/验证
- 每个闭环结束立即跑验证并总结。

### 1.5 Robustness Injection（鲁棒性/防御性编程）
- I/O 入口（API、localStorage、文件导入）必须：
  - 校验 schema（guard）
  - `try/catch` + 错误日志
  - 降级/回退路径（fallback）
- 迁移（migration）必须先写：
  - **检测旧数据** → **copy-on-first-login** → **不立即删除旧数据（安全）**

### 1.6 Anti-Corruption Layer（防腐层：防止 AI 把业务改烂）
- 任何“跨模块共享数据/逻辑”先抽象成中间层：
  - 例：XHS Vault：统一 ingest/query/buildContext，让 Arena/Kanban/UI 只消费接口。
- 目标：未来加 RAG/向量检索时，只改中间层，不改业务 UI。

### 1.7 Validation Loop（验证驱动）
- 不靠“感觉”，靠命令输出：
  - Lint → Build →（必要时）Targeted API Hit / UI Smoke
- 出错时：先读完整 trace（不要盲目重试）。

---

## 2) `.windsurfrules` 模板（可直接复制到新项目）

> 说明：这是合并后的“架构师模式”规则，兼容 TS/React/Vite/Vercel 这类前端项目，也可按语言替换验证命令。

```markdown
# [Project Name] - Architect Mode Rules

## 0) Rule Priority
- 项目文档优先：README.md / ARCHITECTURE.md / SOP.md（若存在）
- 模块内规则优先于全局规则（例如 services/*、api/*、context/*）

## 1) Context-First Workflow
- 修改前：先读最近的项目文档（README/ARCHITECTURE/SOP）
- 不要全仓扫描：只打开与本次修改相关的入口文件/状态中心/类型定义/被触达的 UI
- 需要定位时：优先 grep/搜索，再精准 read

## 2) Engineering Guardrails
- 禁止硬编码 secrets：必须走 .env / env vars
- 关键状态必须集中管理：优先 Context/Service，不要把核心逻辑堆在 UI 组件
- TypeScript：避免 any；类型定义集中在 types.ts（或对应文件）

## 3) Anti-Corruption Layer
- 跨模块共享的数据/逻辑必须通过“中间层 API”对外暴露（ingest/query/buildContext）
- 新增能力优先设计成可替换实现（为 RAG/向量检索预留接口）

## 4) Interaction Loop
- 复杂需求先输出 PRP 蓝图；用户确认后再动代码
- 使用 todo_list 跟踪进度：一个 in_progress，其余 pending/completed
- 每个里程碑给出简要 check 总结（改了什么/怎么验证）

## 5) Validation Loop (Every Change)
- 最低要求：运行 lint
- UI/构建相关：再运行 build
- API 改动：至少 hit 一次关键 endpoint 或做最小 mock

## 6) Windows / PowerShell
- 不要在命令里写 cd；用 cwd
- 给出 PowerShell 环境变量示例（如 $env:KEY = "..."）
```

---

## 3) Workflows 模板（建议放到 `.windsurf/workflows/`）

### 3.1 `prp.md`（需求蓝图流）
**用途**：把自然语言需求转成可执行蓝图。

**步骤**：
1. 产出 PRP：Goal / Non-Goals / Context / Blueprint / Risks / Validation
2. 询问用户是否按蓝图执行
3. 用户确认后开始改代码

### 3.2 `bugfix.md`（根因修复流）
1. 收集完整错误（终端 trace / log / 截图）
2. 定位 root cause（先读源码，不猜）
3. 最小修复 + 必要的防护（guard/log）
4. 回归验证（lint/build/targeted）

### 3.3 `rag-ready-feature.md`（RAG-ready 功能流）
1. **Define Interface**：types.ts 定义核心模型与查询参数
2. **Service/Context**：实现 ingest/query/buildContext
3. **UI**：绑定 query + 操作入口（import/export/search/filter）
4. **Integrations**：业务模块只调用 buildContext / query，不直接读原始数据
5. **Docs + Validation**

### 3.4 `storage-migration.md`（存储迁移流）
1. 设计新旧 key（含 userId 前缀）
2. Provider 初始化：先读新 key；为空则检测旧 key
3. copy-on-first-login：把旧数据复制到新 key
4. 不立即删除旧数据（安全）；可加 migrated flag

---

## 4) Kill Prompts（高复用提示词模板）

### 4.1 接手新项目（快速建立心智模型）
> 你先阅读 @README.md（若无就阅读入口文件和 package/requirements），然后给我：
> 1) 项目数据流向图（state / storage / api / ui）
> 2) “真理来源”在哪里（类型定义/状态中心/后端入口）
> 3) 我这次需求会影响哪些文件（最小集合）

### 4.2 大型重构（先 PRP 再执行）
> 我要做一个可能破坏性的修改。请先输出 PRP 蓝图：
> - Goal & Success Criteria
> - Non-Goals
> - Blueprint（按顺序）
> - Backward Compatibility / Migration
> - Docs Update Plan
> - Validation Loop
> 在我回复“Start”前，不要写任何代码。

### 4.3 排查部署/lint/build 报错（禁止猜测）
> 不要猜。先读取完整终端输出并指出：
> - 根因是什么（哪个文件/哪个规则/哪个依赖）
> - 最小修复方案
> - 修复后要跑哪些命令验证

### 4.4 让 AI 变得“可控”（减少幻觉）
> 你必须：
> - 只在读过相关文件后给结论
> - 用路径锚点引用你的依据
> - 不确定就明确说不确定，并提出下一步要读哪些文件/跑哪些命令

---

## 5) 工程化 Checklists（可直接复用）

### 5.1 变更前
- [ ] 明确 Goal / Non-Goals
- [ ] 找到状态中心（Context/Store）与入口文件
- [ ] 确认持久化策略（localStorage/db）及是否需要迁移

### 5.2 变更中
- [ ] 每个闭环结束跑 lint
- [ ] UI/构建相关再跑 build
- [ ] 必要时加 guard + fallback

### 5.3 变更后
- [ ] 更新 README/ARCHITECTURE/SOP（至少 README）
- [ ] 写回归点：哪些页面必须点一遍

---

## 6) 常见坑位与建议（来自本项目实战）

### 6.1 ESLint / globals
- 现代前端用到 `Blob/URL/window/localStorage` 等时，确保 ESLint globals 覆盖到位。
- 推荐用 ESLint Flat Config + `globals` 包统一管理。

### 6.2 多账号 + localStorage
- **必须用 userId 前缀隔离**（否则账号串数据）。
- 切换账号后要确保 Provider 重新初始化（可通过重载或 key 变更触发）。

### 6.3 迁移策略
- “拷贝优先，不急着删”是最安全策略。
- 迁移要可重复执行且幂等（dedup/guards）。

---

## 7) 你可以直接复制的文件清单（建议落地到新项目）

- `.windsurfrules`（贴 `2)` 模板）
- `.windsurf/workflows/prp.md`
- `.windsurf/workflows/bugfix.md`
- `.windsurf/workflows/rag-ready-feature.md`
- `.windsurf/workflows/storage-migration.md`
- `ARCHITECTURE.md`（若缺失，让 AI 先补一份最小版）
- `SOP.md`（写操作路径/排错流程）

---

## ✅ End

如果你要我进一步把 `3) Workflows 模板` 直接生成成多个 `.md` 文件放进 `.windsurf/workflows/`，也可以继续说一声（我会按这个合并版自动落地成文件）。
