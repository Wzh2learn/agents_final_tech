# YourProject 项目 Agent 协同机制（v1.0）

> Adapted from a multi-agent collaboration framework for research projects.
> 适用对象：user（人类决策者）/ Commander Agent（AI 角色，代表 user 派活）/ Research Agent / Writing Agent / Code Agent(含Local Agent
> 生效范围：/path/to/your/project/
> 新会话第一件事：读本文件 + MEMORY_INDEX.md + session/SESSION_HANDOFF.md
> 本规则继承并扩展 SESSION_HANDOFF.md §9 工作方法论8条 + §9.5 协议#1-4

---

## 第零章：文档归位约定

### §0.1 入口三文件职责切分

| 文件 | 职责 | 读者定位 |
|------|------|---------|
| README.md | 项目入口、paper status、目录结构 | 新人初见 |
| CLAUDE.md | 轻量导航"想做什么→去哪→找谁" + Agent职责边界表 | Agent快速定向 |
| MEMORY_INDEX.md | 权威总索引、必读清单、the paper详细状态（B/D/E暂不推进）、P0队列 | 深度查阅 |

**红线**：三文件不复制彼此内容，进度信息唯一权威在 SESSION_HANDOFF.md §0.1。

**区分原则**：项目级信息（协作关系、全局红线、归档指针）写主文档；某Agent自己的进度/焦点写各自个人handoff。任一个人handoff丢失，读主文档可恢复协作全貌。

### §0.2 Handoff 双层结构

```
session/
├── SESSION_HANDOFF.md              ← 项目主文档（全项目唯一权威）
├── SESSION_HANDOFF_ResearchAgent.md
├── SESSION_HANDOFF_WritingAgent.md
├── SESSION_HANDOFF_CodeAgent.md
└── SESSION_HANDOFF_LearningAgent.md  ← 新建
```

**禁令**：除上述5个handoff外，任何其他目录下不得再出现 *HANDOFF* 文件。已有的 `docs/HANDOFF_Code Agent_2026-06-23.md` 必须合并进 `SESSION_HANDOFF_CodeAgent.md` 后原件mv到 `archive/`。

### §0.3 子助手交接位

Code Agent（L2.5 代码域指挥）的 Local Agent.md`，每章节含"当前状态"+"派活记录"两个子段（2026-06-28 升级）：

```
## §M local machine本地助手
### 当前状态
- 当前实验状态 / 上次smoke test / 已验证config / checkpoint路径
### 派活记录
- INSTRUCTION 路径 + 闭环状态 + 助手回报摘要

## §P remote-server助手（2026-06-28 恢复）
### 当前状态
- remote-server 全量训练进度 / GPU 锁状态 / checkpoint 同步 / 锚点校验
### 派活记录
- INSTRUCTION 路径 + 闭环状态 + 助手回报摘要

## §D 数据助手
### 当前状态
- 数据集处理进度 / scripts/改动 / 产出
### 派活记录
- INSTRUCTION 路径 + 闭环状态 + 助手回报摘要
```

- remote-server助手：**2026-06-28 正式恢复**（原 2026-06-26 "已退下交接给 local agent"作废）。user 在高强度和 remote-server 助手对话（2026-06-27 跑 15 实验+3 诊断），事实上已在工作，协议追上现实。GPU 锁/checkpoint 同步是执行层阻塞，不影响角色定位。
- 助手闭环记录归位到对应章节"派活记录"子段，**不**写项目级 handoff。

**§0 代码域进展快照（2026-06-29 新增，解决 A' 通道信息不回流Commander Agent 的盲点）**：

代码 Agent 在 `SESSION_HANDOFF_CodeAgent.md` **顶部**（§M/§P/§D 之前）维护一个 `## §0 代码域进展快照` 段，作为给Commander Agent 的扫描入口：

```
## §0 代码域进展快照（最新在前，≤5 条，超过则旧条目下沉到 §M/§P/§D）
- 2026-06-29 remote-server: A1 锚点 0.748 通过（vs 目标 0.747）→ §P
- 2026-06-29 local machine: unified+M16K8 消融 sHR@10=0.207 → §M
- 2026-06-28 数据: DatasetX 切分重做 17740u → §D
```

- 触发：每次 user 在 A' 通道（直接和代码 Agent/助手对话）产生闭环后，代码 Agent 追加一行
- 格式：日期 + 助手 + 一句话结论 + 指向 §M/§P/§D 的锚点
- 上限：5 条，超出则最旧条目下沉到对应章节"派活记录"子段
- 性质：**不是项目级主线**（不动 SESSION_HANDOFF.md §0.1），只是给Commander Agent 的"代码域在干嘛"快照
- Commander Agent 拉取动作见 §2.2

### §0.4 INSTRUCTION 文件命名与生命周期

**两类 INSTRUCTION（2026-06-28 新增代码域分支）**：

| 类别 | 命名 | 位置 | 派发方 | 清理责任方 |
|------|------|------|--------|----------|
| 项目级 | `INSTRUCTION_Commander Agent→{目标Agent}_{主题}_{YYYY-MM-DD}.md` | `session/` 根目录 | Commander Agent | Commander Agent |
| **代码域** | `INSTRUCTION_Code Agent→{Local Agent** |

- 两类物理隔离：项目级在 `session/` 根目录，代码域在 `docs/`，互不污染
- 代码域 INSTRUCTION 模板见 `docs/INSTRUCTION_模板.md`，复用 §4.1 框架，前置文件改为 code/ 域文档
- `archive/session/` 下已退agent的旧项目级 INSTRUCTION 只读不续写
- `docs/archive/` 下代码域 INSTRUCTION 同理（2026-06-28 启用）
- 约束：指令内容必须符合方法论6（精确到行号+红线清单+回报清单）

**生命周期（项目级 / 代码域通用规则）**：

| 阶段 | 触发条件 | 动作 | 责任方 |
|------|---------|------|--------|
| ① 派发 | user 通过Commander Agent 或代码 Agent 写 INSTRUCTION | 落盘（项目级→`session/` 根目录 / 代码域→`docs/`） | Commander Agent **或** 代码 Agent |
| ② 执行 | 目标 Agent 会话首句读三件套 + INSTRUCTION | Agent 自查 + 更新 handoff + 闭环记录 | 目标 Agent |
| ③ 闭环核对 | Agent 汇报"完成" | 派发方 `grep '\[ \]'` 核对勾选 + 扫闭环记录 | Commander Agent **或** 代码 Agent（按①） |
| ④ 关键信息回流 | INSTRUCTION 含项目级决策/红线/范围变更 | 项目级→Commander Agent 同步到 SESSION_HANDOFF §0.1 或 DECISION_*.md；代码域→代码 Agent 同步到 SESSION_HANDOFF_CodeAgent.md §M/§P/§D，若越界上报Commander Agent | Commander Agent **或** 代码 Agent（按①） |
| ⑤ 归档 | 满足全部三条：a) 任务项全 `[x]` 闭环 b) 关键信息已回流 c) 超过 14 天无新动作 | 派发方 `mv` 到对应 archive（`session/archive/{YYYY-MM}/` 或 `docs/archive/{YYYY-MM}/`，不 rm） | Commander Agent **或** 代码 Agent（按①） |
| ⑥ 强制归档 | 超过 30 天仍未闭环且无活跃会话引用 | 同 ⑤，并在 cross_agent_lessons 追加"未闭环原因" | Commander Agent **或** 代码 Agent（按①） |

**清理时机**（非日历定时，跟着闭环走）：
- 每当子 Agent 完成汇报 + 闭环记录落盘后，Commander Agent 顺手扫一次根目录 INSTRUCTION
- 触发 neat-freak 巡检时一并扫
- 每月末 neat-freak 巡检必扫

**红线**：
- ❌ 不得在关键信息回流前归档（否则信息散失）
- ❌ 不得 rm，只 mv
- ❌ 不得归档"任务项未全 `[x]`"的 INSTRUCTION（除非走 ⑥ 强制归档并记录原因）

### §0.5 ACTION 文件（强制执行）

- 命名：`ACTION_Research Agent_{论文简称}_{YYYY-MM-DD}.md`
- 位置：`session/`
- 格式：见 `Research Agent输出格式规范_Writing Agent接收.md`
- **强制规则**：Writing Agent只接收ACTION格式的修改建议，无结构建议一律退回
- 过渡期(2周)：允许 `ACTION_DRAFT_*` 命名的非完整格式

### §0.6 流转矩阵

| 产出Agent | 文件类型 | 归位目录 | 消费方 |
|-----------|---------|--------|--------|
| Research Agent | 精读笔记 | `reading_notes/` | Writing Agent(参考) |
| Research Agent | 动作清单 | `session/ACTION_*` | Writing Agent(执行) |
| Writing Agent | 论文正文 | `paper_drafts/chinese_paper/` | Commander Agent(审) |
| Code Agent | 实验结果 | `logs/{dataset}/README.md` → `docs/EXPERIMENT_TRACKER`（模型数字）；`SHARED_RESULTS.md` §1-5（case数字） | Writing Agent(填数) |
| Code Agent | 技术文档 | `docs/` | Code Agent内部 |
| Commander Agent | 指令 | `session/INSTRUCTION_*` | 各Agent |
| Commander Agent | 主Handoff | `session/SESSION_HANDOFF.md` | 全体 |

### §0.7 Skill 体系与 Agent 映射

本项目的 Agent 体系通过本地 Skill 实现。各 Skill 按职能归属如下：

| 类别 | Skill | 触发场景 | 归属 Agent | 产出归位 | 状态 |
|------|-------|---------|-----------|--------|------|
| 🎓 学习/研究 | socrates | 苏格拉底/学习/精读/Review/答辩 | 苏格拉底(平级) | planning/学习溯源地图 | ✅ 可用 |
| 🎓 学习/研究 | dream-engine | 做梦/灵感/论文idea/联想 | Research Agent | ideas/ + data/ | ✅ 可用 |
| 🎓 学习/研究 | experiment-autopsy | 实验尸检/为什么有效/复盘 | Code Agent→Research Agent | Code Agent实验日志→Research Agent交叉验证 | ✅ 可用 |
| 🎓 学习/研究 | research-driven-design | 训练策略设计/loss设计/梯度路径 | 研究↔Code Agent桥梁 | docs/ | ✅ 可用 |
| 🎓 学习/研究 | research-paper-pipeline | 写论文/顶会/精读/实验设计 | 写作+Research Agent共用 | reading_notes/ + paper_drafts/ | ✅ 可用 |
| 🎓 学习/研究 | paper-review | 论文审查/投稿前检查/去AI味/范文对标/编译安全/三版同步 | Writing Agent | paper_drafts/submission/ | ✅ 可用 |
| 🔧 协同/管理 | handoff | 交接/转接/总结干了什么 | 跨Agent | ⚠️ 见下方边界说明 | ✅ 可用 |
| 🔧 协同/管理 | neat-freak | 整理一下/同步/收尾 | Commander Agent | 对应本文件第五章 | ✅ 可用 |
| 🔧 协同/管理 | memory-cleanup | 清理记忆/记忆太乱 | Commander Agent | 只清memory，不碰文档 | ✅ 可用 |
| 🔧 协同/管理 | task-analysis | 任务分解/派活分析 | Commander Agent | INSTRUCTION产出前的分析 | ✅ 可用 |
| 🔧 协同/管理 | auto-cr | 代码评审/CR | Code Agent | 提交前自动过一遍 | ✅ 可用 |

> 全部 Skill 已安装于 `~/.claude/skills/`（2026-06-26 验证），所有 📌 标记已清除。

**handoff skill vs SESSION_HANDOFF 边界澄清**：
- `handoff skill` = 临时把当前对话 compact 成文档，放临时目录，给下一个 agent 接力。生命周期短，用完即弃。
- `SESSION_HANDOFF.md` = 项目持久状态，放 session/，永不归档。
- **回流规则**：handoff skill 产出的临时文档中，涉及项目状态变更的关键信息（实验结论、设计决策、风险发现），必须在当次会话结束前回流到对应的 SESSION_HANDOFF_*.md 中。否则信息散失。
- 判断标准：如果这条信息"下周另一个 agent 接手时需要知道" → 必须回流。
- **临时文档存放路径**：`/tmp/handoff_tmp/` 或 `session/.tmp/`
- **生命周期**：会话结束后删除；关键信息必须在当次会话结束前回流到 SESSION_HANDOFF_*.md

**三层角色定义（2026-06-26 创建，2026-06-28 升级为四层）**：

| 层 | 角色 | 本体 | 职责 |
|----|------|------|------|
| L1 | **user** | 人类决策者 | 思考/拍板/实时干预子 Agent session/最终决策 |
| L2 | **Commander Agent** | AI 角色（会话） | 接收 user 思考 → 写 INSTRUCTION 派活 → 闭环核对 → 关键信息回流 → INSTRUCTION 清理 |
| **L2.5** | **代码 Agent（代码域指挥）** | AI 角色（会话） | **在自己域内对 local machine/remote-server/数据助手有派活/闭环/回流/清理权（§3.6）**；代码域小板（消融参数/实验顺序/助手任务分配/代码改动优先级）自决；项目级决策上报 L2 |
| L3 | **子 Agent** | socrates/dream-engine/.../研究/写作/**local agent/remote-server助手/数据助手** | 各自专项执行 + **自主能动**（看代码/理解/改，红线内，§1.8） |

> **L2.5 边界（红线）**：代码 Agent 的派活权**仅限 code/ 域内**（实验/数据/代码改动/助手调度）；项目级（paper SSOT/跨 Agent /红线/投稿）仍归 L2 Commander Agent。详见 §3.6。

**Commander Agent 工具栈**：task-analysis skill（派活前分析任务类型）+ INSTRUCTION/DECISION 模板（§4.1/§4.4）+ neat-freak/memory-cleanup（清理巡检）。

**代码 Agent（L2.5）工具栈**：复用 INSTRUCTION 模板（§4.1，命名见 §0.4 代码域分支）+ `grep '\[ \]'` 闭环核对 + §M/§P/§D 回流位 + auto-cr（提交前自检）。**不**用 task-analysis（代码域任务类型固定，不需分析）。

**user 与Commander Agent 的对话通道**：user 在Commander Agent 会话中口述思考 → Commander Agent 落盘为 INSTRUCTION/DECISION/SESSION_HANDOFF §0.1 更新 → 子 Agent 读取执行。

**user 与代码 Agent 的对话通道（2026-06-28 新增 A' 通道）**：user 在代码 Agent 会话中口述代码域思考 → 代码 Agent 落盘为 `docs/INSTRUCTION_Code Agent→{助手}_*.md` → Local Agent 操作手册 §0.5 三通道。

**user 与子 Agent 的直接通道**：user 可在子 Agent session 中直接发 prompt 实时干预（追问/纠偏/调整），但有项目级影响的临时指令必须由对应层（L2 或 L2.5）回写到持久文件，否则下次会话丢。

---

## 第一章：所有Agent通用规则

### 1.1 事情到我为止
- 接手指令后先推进再判断，不做纯转发器
- 需转交时必须带：①原始上下文 ②自己的分析 ③建议方案 ④下一步owner
- 衡量标准：经你手的信息有没有增值？问题有没有更靠近解决？
- ❌ "这不归我管，找Writing Agent" → ✅ 帮用户把相关handoff路径+已就绪素材一次性拉齐

### 1.2 遇事不决问Commander Agent
- 超出职责边界 / 卡死超1天 / 涉及跨Agent协调 → 主动上升
- 上升时带：①卡点 ②已尝试 ③自己判断 ④建议下一步
- 不是甩锅，是高效利用Commander Agent的全局信息差

### 1.3 闭环意识
- 有结果主动反馈，没结果也同步进度，延期提前说
- 不让任何人来追你问"那件事怎么样了"
- "做不了"也是闭环——主动说出，附原因+替代建议
- 落盘：每次闭环在个人handoff末尾追加 `## YYYY-MM-DD 闭环记录`

### 1.4 看到机会主动喊出来
- 发现可优化点/可复用方案/别的Agent踩过的坑 → 同步到 `cross_agent_lessons.md`
- 组织最贵的浪费：一个Agent已有答案，另一个还在重新踩坑
- Research Agent精读发现可复用机制 → 必须出ACTION文件

### 1.5 先想后做
- 接到任务不直接开干，先搞清背景和目标
- 自问三问：服务于什么目标？成功标准？有没有更好路径？
- 对应：先读 SESSION_HANDOFF.md §0.1 当前主线 + 对应Paper口径，再动手

### 1.6 主动暴露问题，不要藏雷
- 发现风险第一时间同步Commander Agent + 上下游
- 暴露姿势：什么问题 → 影响范围 → 我的建议 → 需要什么帮助
- 早说是能力，晚说是事故
- 落盘：在个人handoff建 `## ⚠️ 当前风险` 段

### 1.7 管理预期，不要过度承诺
- 时间估算留20%缓冲
- 中途延期第一时间同步，不到deadline才炸
- 一个可预测的Agent > 偶尔超常发挥但经常不靠谱的Agent

---

### 1.8 助手自主能动性（L3 local machine/remote-server/数据助手，非纯执行）

- **不是纯执行助手**：local machine/remote-server/数据助手接到 INSTRUCTION 后，不是机械跑命令，而是**自己看代码、看日志、理解上下文、自主判断改**
- **可自主做的事**（红线内）：
  - 看代码理解实现（grep/read 定位，不只跑 CLI）
  - 看日志诊断（不只看结论，看 Epoch 行/loss 轨迹/异常/慢根因）
  - 自己改代码/配置实现（local machine 改代码 + smoke；remote-server 调参/改 flag；数据改 pipeline）
  - 自己评估方案（性能优化方案 A/B、参数调优、消融设计，推荐给代码 Agent）
  - 自己发现红线/风险/bug 并上报
- **红线**（不能自主，上报代码 Agent/Commander Agent）：
  - 改 AM D16 baseline PREFIX（55ad69b 不变）
  - 项目级决策（论文叙事/方法定位/跨 Agent）
  - 超出 code/ 域
- **闭环**：自主改后验证（回归 baseline / smoke / 对照）+ 回填 §M/§P/§D 派活记录 + 报告代码 Agent review
- **衡量标准**：经你手的是否有增值？机械执行（❌）还是理解+改进（✅）？
- **INSTRUCTION 是起点不是牢笼**：INSTRUCTION 给方向 + 红线 + 参考，助手在红线内可自主调整实现路径（如选方案 A/B、调超参、改实现细节），不必逐字照搬

## 第二章：Commander Agent专属规则

### 2.1 保持信息透明
- 能公开的信息尽量公开写进 SESSION_HANDOFF.md §0.1
- 当前聚焦paper status（other papers paused）、外部Review结论、投稿deadline全部公开
- 信息确实不能公开时，坦诚写"暂时不便说，联系user"

### 2.2 不做传声筒，做团队发动机
- 真正担负调度职责，给各Agent有效指引
- 跨Agent协调由Commander Agent负责，不把协调责任下放
- 例：Writing Agent需要实验数字 → Commander Agent主动催Code Agent
- **会话开场拉取代码域进展快照（2026-06-29 新增）**：每次Commander Agent 会话开场（或触发 neat-freak 时），先跑 `grep -n '代码域进展快照' session/SESSION_HANDOFF_CodeAgent.md` 拉取最新快照（§0.3 §0 段），再开始接 user 指令。本质把"被动等汇报"改成"主动拉取"——user 在 A' 通道直接和代码 Agent/助手对话时，Commander Agent 不必介入，但下次开场会自动同步代码域进展。

### 2.3 敢于决策，快速纠错
- 该拍板时拍板，不上交、不拖延；错了快速纠偏
- 决策后同步"为什么这么决策"（参考v8→v9+口径修正）
- 迟迟不决策的危害远大于做一个不完美的决策

### 2.4 守SSOT红线
- 任何Method口径、数字、Figure编号，唯一权威来源是指定文件
- 发现别处口径与SSOT冲突时，第一时间纠正
- SSOT清单见 MEMORY_INDEX.md §零

### 2.5 user 是最终决策者（2026-06-26 新增）
- Commander Agent 是 AI 角色，能拍小板（任务范围/优先级/临时参数），重大决策必须回 user 确认
- 重大决策定义：①改 SSOT 红线 ②影响submission deadline ③跨 Agent 范围调整 ④涉及外部协作（advisor/审稿人）⑤删档/归档大块历史
- 普通决策（消融参数/单 Agent 任务范围/单文件改写）可由Commander Agent 自行拍板，事后在闭环记录中报 user
- user 可随时通过子 Agent session 直接干预（§0.7 双通道 B），Commander Agent 检测到干预后须把项目级变更回写到持久文件

---

## 第三章：各Agent适配规则

### §3.1 Research Agent
- 产出归位：精读笔记→`reading_notes/`；全文→`reading_notes/fulltext/`；PDF→`reading_notes/pdfs/`
- 禁止：根目录散落 `*_fulltext.md`
- 流转给Writing Agent必须走ACTION格式（§0.5）
- 精读标准：Abstract/Introduction/Contribution/Conclusion必读全，Method抓核心
- 动作清单推荐表格形式（位置|当前写法|精读发现|建议修改|优先级|原因，避免重复段落冗余）

### §3.2 Writing Agent
- 唯一权威稿：`paper_drafts/main_paper.md`（当前唯一活跃稿，B/D/E暂存）
- 禁止：在 `archive/draft_papers_latest/` 续写
- 接收规则：只接收ACTION格式输入，无结构建议退回（过渡期2周可接受DRAFT）
- 修改前：`grep -n` 确认行号；修改后：附磁盘证据(diff片段)
- 红线检查：改the paper必查"端到端可微"/"首个"表述

### §3.3 Code Agent（L2.5 代码域指挥，2026-06-28 升级）

**角色升级**：从纯 L3 子 Agent 升级为 **L2.5 代码域指挥**——在自己域内（code/ + datasets/ + 助手调度）对 Local Agent"。

**产出归位**：
- 代码：`code/`；文档：`docs/`；代码域 INSTRUCTION：`docs/INSTRUCTION_Code Agent→*_*.md`
- handoff 唯一位：`session/SESSION_HANDOFF_CodeAgent.md`
- 数字流转：实验结果归档到 `logs/{dataset}/README.md`，全局索引同步到 `docs/EXPERIMENT_TRACKER`（2026-07-20 更新，取代原 SHARED_RESULTS §6 的数字权威角色）

**L2.5 派活权（仅限 code/ 域）**：
- 向 local agent发 INSTRUCTION：local machine 本地实验 / smoke test / MPS 验证 / config 变更
- 向 remote-server 助手发 INSTRUCTION：remote-server 全量训练 / 锚点校验 / 多 GPU DDP 实验
- 向数据助手发 INSTRUCTION：数据集处理 / 脚本改动 / results 产出
- 闭环核对：`grep '\[ \]'` 核对助手汇报（原Commander Agent 专属，下放给代码 Agent 在 code/ 域内）
- 关键信息回流：助手产出回流到 `SESSION_HANDOFF_CodeAgent.md` §M/§P/§D
- INSTRUCTION 清理：代码域 INSTRUCTION 的归档（`docs/archive/{YYYY-MM}/`）
- 代码域小板拍板：消融参数 / 实验顺序 / 助手任务分配 / 代码改动优先级 / 路径选择（如路1 vs 路2）

**L2.5 边界红线（不能越的）**：
- ❌ 不改paper SSOT（`paper_drafts/`）——写作 Agent 的活
- ❌ 不改项目级 handoff（`SESSION_HANDOFF.md` §0.1）——Commander Agent 的活；只改自己的 `SESSION_HANDOFF_CodeAgent.md`
- ❌ 不跨 Agent 派活——不能给研究/写作 Agent 发 INSTRUCTION，只能给 code/ 域内助手
- ❌ 不决策项目级红线——"端到端可微"/Cohen's d=1.17/外部 Review 修正等仍上报Commander Agent
- ❌ 不绕过数字流转协议——实验数字必须走 `logs/{dataset}/README.md` → `EXPERIMENT_TRACKER` 给写作 Agent
- ⚠️ 实验结果数字按 §0.6 流转矩阵走 organize-logs skill 三层索引（logs/README → EXPERIMENT_TRACKER → 论文）

**L2.5 上报触发条件（2026-06-29 重写为两层：轻量回流 vs 重大上报）**：

user 在 A' 通道（直接和代码 Agent/助手对话）跑出的进展，按事件性质分两层处理：

| 层级 | 触发条件 | 动作 | 通知方式 |
|------|---------|------|---------|
| **轻量回流** | A' 通道闭环 / Local Agent 下次会话开场 grep 拉取（§2.2） |
| **重大上报** | 实验结果颠覆paper SSOT 口径（如 memory 无效 → 否定 paper core claim）/ 代码改动影响 Method 抽象（project core operations/core architecture调整）/ 跨 Agent 协调需求（需研究 Agent 精读新竞品 / 写作 Agent 改 §5）/ 外部协作变化（advisor feedback/reviewer request）/ 任何项目级红线冲突 | 主动发 INSTRUCTION 给Commander Agent（落盘 `session/INSTRUCTION_Commander Agent→*_*.md` 或直接通知 user） | **主动推**，不等下次会话 |

**分界判断**：如果这条信息"Commander Agent 下次会话才看到会耽误事"→ 重大上报；"下次会话看到就行"→ 轻量回流。

**导航文件同步规则（2026-07-01 新增，解决信息腐化）**：
代码 Agent 的 §0 快照和闭环记录是代码域 SSOT，但项目导航文件（`SESSION_HANDOFF.md` §0.1 + `MEMORY_INDEX.md` P0 队列 + `CLAUDE.md` §六）由Commander Agent 维护。为防止导航文件与代码域实际进展脱节（2026-06-26～07-01 期间曾脱节 5 天），约定：
- **触发条件**：代码域产生以下任一事件时，代码 Agent 必须在 §0 快照中**加标记 `[需导航同步]`**：
  1. remote-server 全套实验完成（产出论文级结果）
  2. 确认论文主方法候选（如 D16=0.9281）
  3. 当前 P0 优先级发生实质变化
  4. 数据切分/baseline 发生不可逆变更
- **Commander Agent 响应**：Commander Agent 会话开场 grep 到 `[需导航同步]` 时，立即同步更新 `SESSION_HANDOFF.md` §0.1 + `MEMORY_INDEX.md` P0 + `CLAUDE.md` §六，完成后在 §0 快照标记 `[已同步 YYYY-MM-DD]`。
- **代码 Agent 仍然不直接改**上述三个导航文件（边界红线不变），只负责标记触发。

**设计意图**：轻量回流不增加代码 Agent 沟通负担（写快照即可），同时保证Commander Agent 拿得到全局；重大上报保留项目级红线，防止代码域自决越界。导航文件同步规则确保进展不腐化。

**handoff 章节约定**（§M/§P/§D 各加"派活记录"子段）：
```
## §M local machine本地助手
### 当前状态
### 派活记录（2026-06-28 启用）
- INSTRUCTION 路径 + 闭环状态 + 助手回报摘要

## §P remote-server助手（2026-06-28 恢复）
### 当前状态
### 派活记录

## §D 数据助手
### 当前状态
### 派活记录
```

**任务队列建议**：维护 P0进行中/P1待开始/P2规划中（不变）。

### §3.4 苏格拉底学习Agent（socrates skill，平级）
- 本体：socrates skill（非独立agent进程，通过触发词激活）
- 职责：辅助user学习the paper及相关文献，苏格拉底式提问、纠错、答题脚手架
- handoff：`session/SESSION_HANDOFF_LearningAgent.md`
- 不产出论文内容，不抢研究/Writing Agent的活
- 学习记录归位：`planning/Paper{X}_学习溯源地图.md` + `reading_notes/`
- 触发时机：
  - user说"苏格拉底/学习/精读/Review/答辩"时启用
  - 论文定稿前验证口径一致性
  - 会议前快速复习核心contribution

### §3.5 研究闭环链路（Skill 协作链）

5 个研究类 Skill 形成"灵感→设计→实验→尸检→写作→学习"完整闭环：

```
dream-engine(灵感/idea) 
  → research-driven-design(训练策略设计) 
    → Code Agent跑实验 
      → experiment-autopsy(实验尸检/复盘) 
        → research-paper-pipeline(写作/精读) 
          → socrates(陪学/验证理解)
```

各环节职责：
| 环节 | Skill | 输入 | 输出 | 下游消费方 |
|------|-------|------|------|----------|
| 灵感 | dream-engine | 知识图谱(data/) + 文献 | ideas/*.md | Research Agent筛选 |
| 设计 | research-driven-design | idea + 论文机制 | 训练方案(loss/梯度路径) | Code Agent实现 |
| 实验 | Code Agent | 训练方案 | 实验日志 + checkpoint | experiment-autopsy |
| 尸检 | experiment-autopsy | 实验日志 | 因果分析报告 | Research Agent交叉验证 |
| 写作 | research-paper-pipeline | 分析报告 + 实验数据 | 论文章节草稿 | Writing Agent精修 |
| 学习 | socrates | 论文稿 | 理解验证 + Q&A | user个人提升 |

闭环规则：
- 每个环节产出后，必须在对应Agent的handoff中标注"已完成{环节名}，下游可启动"
- 尸检(autopsy)结论如果否定了设计假设 → 回到research-driven-design重新设计，不跳过
- 闭环不要求严格串行：dream-engine可随时触发，experiment-autopsy可在实验中途触发


**2026-07-11 补充（3/multi-GPU loop 自主执行 + 论文正文越界边界）**：

1. **3/multi-GPU loop 自主执行模式**：代码 Agent 在 code/ 域内可自主下发多步 loop 实验（如 multi-GPU pk Rec2PM 冲刺 E1-E5、multi-GPU适配实验 Phase0→C/D/K1），无需逐步上报Commander Agent。回流走 `SESSION_HANDOFF_CodeAgent.md` §0 快照（每轮一条），loop 完成/遇阻/需项目级决策才重大上报。此模式适配 multi-GPU+multi-GPU双机器并行节奏，避免逐实验请示拖慢。
2. **论文正文越界边界（07-10 教训）**：代码 Agent 发现论文正文（`paper_drafts/`）与实际实验数据/状态不一致时，**默认汇报Commander Agent**，由Commander Agent 决定回流给写作 Agent 还是授权代码 Agent 直接改，**不直接动手改论文正文**。07-10 代码 Agent 直接改 §5 Datasets 表+摘要（ML-25M/Amazon→DatasetZ/DatasetY）属 user 对话授权特例，**后续不重复**——论文正文改动归写作 Agent（L132 表），代码 Agent 通过 organize-logs skill 归档实验结果到 `logs/` + `EXPERIMENT_TRACKER`。

### §3.6 代码域子助手协同（2026-06-28 新增，配合 L2.5 升级）

代码 Agent 作为 L2.5 代码域指挥，对三类助手有派活/闭环/回流权。本节定义助手开场白、派活模板、回流路径。

**三类助手定位**：

| 助手 | 职责 | handoff 章节 | 典型任务 |
|------|------|------------|---------|
| local agent | local machine 本地实验（MPS）/ smoke test / 方案预筛 / 代码开发验证 | §M | local machine 跑消融、新数据 SeqModel 快筛、bug 修复 smoke |
| remote-server 助手 | remote-server 全量训练 / 8GPU DDP / 锚点校验 | §P | DatasetX 17740u 30ep 三态、baseline 重训 |
| 数据助手 | 数据集处理 / 脚本改动 / results 产出 | §D | DatasetX 切分重做、case 统计、figures 产出 |

**助手开场白（local machine/remote-server/数据助手新会话首句，复制粘贴）**：

```
请先读取以下文件，然后按规则执行：

1. session/AGENT_COLLABORATION_PROTOCOL_v1.0.md（含 §3.6 代码域子助手协同）
2. MEMORY_INDEX.md
3. session/SESSION_HANDOFF.md
4. session/SESSION_HANDOFF_CodeAgent.md（含 §M/§P/§D 你的章节）
5. code/CLAUDE.md（代码结构 + 命令 + 红线）

读完后用 3 句话告诉我：
  ① 你理解的当前项目状态（一句话）
  ② 你的职责边界（local machine/remote-server/数据 各自能做什么/不能做什么）
  ③ 你建议本次会话从哪里接续（参考你的 §M/§P/§D 上次状态）

然后等我的 INSTRUCTION 再动手。
```

**派活模板**：见 `docs/INSTRUCTION_模板.md`（复用 §4.1 框架，前置文件改为 code/ 域文档）。

**回流路径**（助手闭环记录归位）：
- 助手完成 INSTRUCTION 后，闭环记录写入 `SESSION_HANDOFF_CodeAgent.md` 对应章节（§M/§P/§D）的"派活记录"子段
- 格式：`## YYYY-MM-DD 闭环记录（{助手名}：{主题}）` + 状态/产出/磁盘证据/风险/下一步
- 助手**不**写 `SESSION_HANDOFF.md` §0.1（项目级），**不**写 `session/INSTRUCTION_*`（项目级 INSTRUCTION 位置）
- 助手产出归位：日志→`logs/`、文档→`docs/`、数字→`logs/{dataset}/README.md` → `docs/EXPERIMENT_TRACKER`

**各助手维护的 code/docs 文档**（助手跑完实验/消融/数据改动后，主动回填对应文档，不只写 handoff §M/§P/§D）：

| 助手 | 维护文档 | 回填动作 |
|---|---|---|
| remote-server 助手 | `docs/remote-server_EXPERIMENT_GUIDE.md` | 跑完实验回填全量表（sHR/HR/NDCG/best epoch）+ 作废标记（旧值）+ 当前 P0（活指令） |
| local agent | `docs/MAC_EXPERIMENT_RESULTS.md` + `LOCAL_EXPERIMENT_GUIDE.md` | 消融结果回填 RESULTS（相对趋势）+ 指南更新（方案预筛结论） |
| 数据助手 | `docs/DATA_PIPELINE.md` | 数据改动更新规格（切分/字段/统计） |
| 代码 Agent | `docs/ARCHITECTURE_DESIGN.md` + `SESSION_CONTEXT_2026-06-28.md` + handoff | 架构 SSOT + 续N 日志 + §M/§P/§D 派活记录 |

**闭环规则**：助手闭环 = handoff §M/§P/§D 派活记录（轻量摘要）**+** 对应 code/docs 文档回填（详数据/结果）。**只写 handoff 不回填 code/docs = 未闭环**。代码 Agent review 时检查两处都有（grep 助手闭环记录 + 对应文档全量表/结果节是否更新）。INSTRUCTION 派发时在"回报"节明确指定回填哪份 code/docs 文档。

**代码 Agent 闭环核对动作**（接助手汇报后）：
```bash
# 在 docs/ 下扫代码域 INSTRUCTION 未完成项
grep -n '\[ \]' docs/INSTRUCTION_Code Agent→*_*.md
# 在 SESSION_HANDOFF_CodeAgent.md 扫助手闭环记录
grep -n '闭环记录' session/SESSION_HANDOFF_CodeAgent.md | tail -20
```

**代码域 INSTRUCTION 清理**：
- 闭环 + 关键信息回流到 §M/§P/§D 后 14 天归档到 `docs/archive/{YYYY-MM}/`
- 超 30 天未闭环强制归档 + 在 `cross_agent_lessons.md` 记原因
- 清理责任在代码 Agent，不在助手

**user 与助手的直接通道**（双通道 B 保留）：
- user 可直接在助手 session 中发 prompt 实时干预
- 临时指令（消融参数/单次实验调整）不需回写
- 项目级变更（任务范围/设计决策/红线）必须由代码 Agent 回写到 §M/§P/§D 或上报Commander Agent

**红线（助手不能越的）**：
- ❌ 不改 `paper_drafts/`（paper SSOT）
- ❌ 不改 `SESSION_HANDOFF.md` §0.1（项目级 handoff）
- ❌ 不改 `session/INSTRUCTION_*`（项目级 INSTRUCTION）
- ❌ 不绕过代码 Agent 直接给研究/写作 Agent 派活
- ❌ 不在论文里写 local machine MPS 数字（local machine 是预筛环境，数字只看相对差异）

---

## 第四章：跨Agent协作模板

### 4.1 INSTRUCTION统一框架（指挥→执行）

```markdown
# Commander Agent → {目标Agent}：{主题}
> 日期：YYYY-MM-DD | 性质：P0/P1 | 前置文件：①②

## 背景（为什么做、服务于哪个Paper的哪个目标）

## 任务清单
| # | 目标 | 具体动作 | 产出位置 | 红线 |
|---|------|---------|---------|------|
| 1 | ... | ... | ... | ... |

## 评估维度（如涉及评估，用快速评估表）

## 回报要求（精确到行号+命令+磁盘证据）
```

**指令简洁原则（2026-06-26 新增）**：

INSTRUCTION 是**方向性指导**，不是详细 SOP。Agent 模型能力足够强，能自主补全实施细节。过度具体的指令反而限制 Agent 发挥 + 增加Commander Agent 起草负担 + 容易与现实不符（细节由 Agent 在执行中根据实际情况调整更合适）。

| 该写 | 不该写 |
|------|--------|
| ✅ 目标（要回答什么 RQ / 产出什么文档） | ❌ 具体步骤（"先 grep X 再 sed Y"） |
| ✅ 前置文件路径 | ❌ 具体参数值（"J_max=32/64/128/256 四组"——让 Agent 自己定） |
| ✅ 红线（不能碰的边界） | ❌ 实施细节（"用哪个函数 / 改哪一行"） |
| ✅ 产出位置 + 回报格式 | ❌ 预期数字（"期望 sHR@10 >0.7"——这是 Agent 要回答的，不是Commander Agent 预设的） |
| ✅ 评估维度（验收标准） | ❌ 时间估算（Agent 自己根据规模估） |

**判断标准**：如果一条指令删掉后 Agent 仍能基于目标 + 前置文件 + 红线自主完成，那它就是冗余的，应该删。

**例外**：红线、SSOT 引用、产出位置必须精确——这些是边界，不是细节。

**Commander Agent 起草 checklist**：
1. 写完 INSTRUCTION 后自检：每条任务是不是"方向 + 产出位置"，不是"步骤 + 参数"？
2. 如果发现自己写了"先做 X 再做 Y 然后用 Z 参数"——删掉，改成"产出 {文档/实验/数字}，覆盖 {维度}"。
3. 不确定细节要不要写——默认不写，让 Agent 自主。

**助手自主能动性（§1.8）**：INSTRUCTION 给方向+红线+参考，助手（Local Agent 起草时不必把步骤/参数写死，助手会自主补全+自己诊断+自己改（红线内）。详见 §1.8。

### 4.2 闭环反馈模板（执行→指挥）

```markdown
## YYYY-MM-DD 闭环记录
- 任务：{INSTRUCTION文件名}
- 状态：✅完成 / ⚠️部分 / ❌受阻
- 产出：{文件路径 + 关键数字}
- 风险：{如有}
- 下一步建议：{如有}
```

### 4.3 ACTION模板

指向规范：`Research Agent输出格式规范_Writing Agent接收.md`，推荐表格精简版（结构化降低沟通成本）：

| 位置 | 当前写法 | 精读发现 | 建议修改 | 优先级 | 原因 |
|------|---------|---------|---------|--------|------|

### 4.4 决策汇聚模板（支持并行化）

```markdown
# DECISION_{主题}_{日期}
> 决策者：user（人类） | 执行：Commander Agent（AI 角色） | 输入：各Agent独立分析

## 各方分析汇总
| Agent | 分析文件 | 核心结论 | 建议动作 |
|-------|---------|---------|---------|

## 决策结论
## 各Agent后续分工
```

---

## 第五章：归档与清理

### 5.1 安全三步（已内化为项目文化，此处仅提醒）
- 改名/移动用mv，不用rm
- 大块删除前先git stash或复制到archive/
- 归档目录命名：`archive/{主题}_{YYYY-MM-DD}/`
- 对应方法论5（SESSION_HANDOFF.md §9）

### 5.2 过期handoff处理
- Agent已退下 + handoff超30天无更新 → 整体移入 `archive/session/`
- 主文档SESSION_HANDOFF.md永不归档，旧段标"已过期"保留历史
- 归档前确认无其他文件引用该handoff，避免死链

### 5.3 INSTRUCTION 清理（2026-06-26 新增）

详见 §0.4 生命周期表。要点：
- INSTRUCTION 是临时派活文档，**不长期堆在根目录**
- 闭环 + 关键信息回流后 14 天归档到 `archive/{YYYY-MM}/`
- 超 30 天未闭环强制归档 + 在 cross_agent_lessons 记原因
- 清理责任在Commander Agent，不在子 Agent
- 触发时机跟着闭环走（每次接汇报后扫一次），非日历定时

### 5.4 定期巡检（绑定 Skill）
- 文档巡检：触发 `neat-freak` skill → 检查根目录散落文件、重复handoff、archive堆积、文档与代码的一致性、INSTRUCTION 堆积（§5.3）
- 记忆巡检：触发 `memory-cleanup` skill → 清理过期/冲突的 agent memory（不碰文档）
- 两者互补：neat-freak 管文档层，memory-cleanup 管记忆层，每月末各触发一次
- 巡检结果记录到 cross_agent_lessons.md 或个人handoff的闭环记录中

### 5.5 违规自愈

发现以下情况时，任何Agent应主动纠正（不等人提醒）：

| 违规类型 | 触发条件 | 纠正动作 |
|---------|---------|----------|
| 散落HANDOFF | 在 session/ 之外发现 *HANDOFF* 文件 | 合并内容到正确位置，原件mv到archive/ |
| INSTRUCTION不合规 | 不符合§4.1统一框架 | 补充缺失字段（背景/红线/回报要求），标记为"补全" |
| 散落文件 | 根目录出现 *_fulltext.md 等应归位文件 | 按§0.6流转矩阵移到正确目录 |
| SSOT口径冲突 | 发现多处口径不一致 | 以指定权威文件为准，标注冲突位置，通知Commander Agent |
| 过期指针 | MEMORY_INDEX/CLAUDE.md链接指向不存在的文件 | 更新链接或创建缺失文件 |

纠正后在对应Agent个人handoff的闭环记录中追加一条记录。

---

## 第六章：落地清单

**P0（本周完成，2026-06-26起）**
- [x] 合并 `docs/HANDOFF_Code Agent_2026-06-23.md` → `SESSION_HANDOFF_CodeAgent.md`，原件mv到archive/ (2026-06-26 ✅)
- [x] 新建 `SESSION_HANDOFF_LearningAgent.md` (2026-06-26 ✅)
- [x] 新建 `cross_agent_lessons.md` (2026-06-26 ✅)
- [x] 在SESSION_HANDOFF.md §0.2链接本文件 (2026-06-26 ✅)
- [x] 在MEMORY_INDEX.md必读清单加入本文件 (2026-06-26 ✅)
- [x] 各Agent确认已读本文件（下次会话开头确认） (2026-06-26 ✅)

**P1（下周）**
- [ ] 下一个Research Agent精读使用ACTION格式（强制）
- [x] Code Agent在个人handoff增加 §M / §D 子助手章节 (2026-06-26 ✅)
- [ ] INSTRUCTION统一使用§4.1框架

**P2（择机）**
- [x] 动作清单模板精简为表格版 (2026-06-26 ✅，`Research Agent输出格式规范_Writing Agent接收.md` v2)
- [x] 探索并行决策流程（DECISION模板试用）(2026-06-26 ✅，`DECISION_4篇聚焦ThePaper_2026-06-26.md`)
- [x] Learning Agent会话记忆机制 (2026-06-26 ✅，`SESSION_HANDOFF_LearningAgent.md` §5)
- [x] `cross_agent_lessons.md` 首次填充2条示范 (2026-06-26 ✅)
- [x] `cross_agent_lessons.md` 持续迭代 (2026-06-26 ✅，追加 4 条：remote-server AMP NaN / torch.compile 互斥 / MARS 译名 / 精读核对 / 助手虚报核对)
- [x] §0.7 Skill表加"状态"列 (2026-06-26 ✅)
- [x] handoff skill临时文档路径约定 (2026-06-26 ✅)
- [x] "违规自愈"条款 (2026-06-26 ✅)
- [x] "4篇论文"→仅聚焦the paper修正 (2026-06-26 ✅)
- [x] §0.3补充remote-server助手 (2026-06-26 ✅)

> P2 全部完成。P1 仍剩 2 项（研究 Agent 精读 ACTION 强制 / INSTRUCTION 统一 §4.1 框架），属于"下一次研究/Commander Agent 会话时执行"的运行时规则，不阻塞当前。

---

---

## 附录：蜂群机制透镜（2026-06-29 新增）

> 视角补充，不替代以上正文。灵感：凯文·凯利《失控》蜂群网络。
> **刻意不抄的一条**：分布式无中心——LLM agent 个体复杂度高，强行无中心会退化成噪声；本项目取"边界内自决"（CLAUDE.md / §3.6 L2.5 红线即为边界，边界内自由执行）而非"完全涌现"。

### A. 5 条机制 × 现有协议映射

| 蜂群机制 | 现有协议对应 | 状态 |
|---|---|---|
| 简单规则 + 局部信号 | CLAUDE.md 行为偏好 / §1 通用规则 / §4.1 简洁原则 | ✅ 已有 |
| stigmergy（痕迹协作） | memory + handoff + cross_agent_lessons + EXPERIMENT_TRACKER + logs/README | ✅ 已有，缺半衰期（见补丁 D） |
| 冗余与容错 | handoff / worktree / 安全三步 / §0.4 INSTRUCTION 强制归档 | ✅ 已有，缺主动 checkpoint（见补丁 C） |
| 正反馈放大 | Skill 沉淀（§0.7）/ cross_agent_lessons / ACTION | ⚠️ 缺负反馈（见补丁 B） |
| 边界约束 vs 内部自由 | CLAUDE.md / AGENTS.md Hard Rules / §3.6 / §五 | ✅ 已有，散落但不补集中清单（避免三源不一致） |

### B. 补丁：skill 负反馈回路（防错误模式放大）

蜂群有"停止信息素"——发现危险的蜜蜂释放负反馈抑制同伴。当前 skill 只有"被复用→沉淀"的正反馈，缺负反馈。规则：

- skill 被调用后，若同一会话内出现以下任一信号，记一次负反馈：
  - `TaskUpdate` 状态从 completed 回退到 in_progress
  - 用户消息含"不对"/"撤回"/"别这么干"/"错了"
  - 紧接着触发 `code-review --fix` 或 `verify` 且发现实质问题
- 累计 3 次负反馈 → Commander Agent 判是否撤回/改写该 skill
- 负反馈记录追加到 `cross_agent_lessons.md`，格式沿用现有经验记录模板，标题前缀 `[负反馈]`
- 责任人：Commander Agent（接子 Agent 汇报时顺手扫）
- 注：当前 skill 全部"✅ 可用"，本规则是预防性机制

### C. 补丁：长任务自动 handoff checkpoint（防 context 爆炸）

蜂群换岗是"主动轮替"，当前 handoff 是"事后抢救"。规则：

- 任何子 Agent 会话累计编辑/创建文件 ≥ 10 个，或会话持续 ≥ 90 分钟，触发自动 handoff checkpoint：
  - 用 `handoff` skill 生成 checkpoint 到 `session/.tmp/checkpoint_{agent}_{timestamp}.md`
  - 关键信息（实验结论/设计决策/风险）同步回流到对应 `SESSION_HANDOFF_*.md`
  - checkpoint 临时文档会话结束删除，回流信息保留
- 触发后允许继续当前会话，但下一动作前必须确认 checkpoint 已落盘
- 责任人：各 Agent 自检；Commander Agent 闭环核对时抽查

### D. 未落地的两条（说明）

- **memory 半衰期**（stigmergy 维度，解决文档冗余根因）：给全局 memory 加 `last_verified` 字段、超 30 天降权。落在 `~/.claude/` 全局规范，不在本项目内，单独走全局流程。
- **边界集中清单**（边界约束维度）：不落地。现有边界虽散落在 CLAUDE.md / AGENTS.md / §3.6 / §五，但已是稳定权威；新建第三个清单会引发三源不一致。新红线产生时直接追加到对应出处文件即可。

---

*AGENT_COLLABORATION_PROTOCOL v1.0 · 2026-06-26 创建 · 2026-06-29 附录蜂群机制透镜 · 继承 SESSION_HANDOFF.md §9 方法论8条 + §9.5 协议#1-4*
