# user + Commander Agent 协作手册 v1

> **用途**：user（人类决策者）的协作姿势备忘录，防止遗忘。
> **创建**：2026-06-26
> **角色定位**：user 是人类决策者；**Commander Agent 是 AI 角色**，负责接收 user 的思考并派活给子 Agent；子 Agent = 研究/写作/代码/苏格拉底
> **综合来源**：协议 §1.6 + §4 + 朋友给的"30秒冷启动"方案 + 实战教训（助手虚报事件）
> **配套规则**：`AGENT_COLLABORATION_PROTOCOL_v1.0.md`（权威规则）
> **生命周期**：每次开新会话前先读本文件 §1，每周一读 §3，遇分叉读 §4

---

## §0 一句话定位

**你不是从苏格拉底入手，是从 SESSION_HANDOFF.md §0.1 入手。**
**苏格拉底是你的学习陪练，不是管理入口。**
**Commander Agent 模式（INSTRUCTION 派活 + handoff 闭环回收）才是你的管理入口。**

## §0.5 四层角色 + 三通道工作模式（2026-06-26 创建，2026-06-28 升级为四层+三通道）

### 四层角色

| 层 | 角色 | 本体 | 职责 |
|----|------|------|------|
| L1 | **你（user）** | 人类决策者 | 思考/拍板/实时干预子 Agent session/最终决策 |
| L2 | **Commander Agent** | AI 会话角色 | 接收你的思考 → 写 INSTRUCTION 派活 → 闭环核对 → 关键信息回流 → INSTRUCTION 清理（项目级） |
| **L2.5** | **代码 Agent（代码域指挥）** | AI 会话角色 | **在自己域内对 local machine/remote-server/数据助手有派活/闭环/回流/清理权**；代码域小板自决；项目级决策上报 L2（详见协议 §3.3/§3.6） |
| L3 | **子 Agent** | 研究/写作/苏格拉底/**local agent/remote-server助手/数据助手** | 各自专项执行 |

> **L2.5 边界**：代码 Agent 的派活权仅限 code/ 域内（实验/数据/代码改动/助手调度）；项目级（paper SSOT/跨 Agent /红线/投稿）仍归 L2 Commander Agent。

### 三通道工作模式

你有三条通道同时存在，**不冲突**：

**通道 A：项目级持久派活通道（user → Commander Agent → 研究/写作/苏格拉底 Agent）**
- 你在Commander Agent 会话里口述思考
- Commander Agent 把它落盘为 `session/INSTRUCTION_*.md` 或 DECISION 或 SESSION_HANDOFF §0.1 更新
- 子 Agent 下一会话读到就执行
- **特点**：跨会话持久、可追溯、可清理（§6.5）

**通道 A'：代码域持久派活通道（user → 代码 Agent → local machine/remote-server/数据助手，2026-06-28 新增）**
- 你在代码 Agent 会话里口述代码域思考（实验/数据/代码改动/助手调度）
- 代码 Agent 把它落盘为 `docs/INSTRUCTION_Code Agent→{助手}_*.md`（物理隔离项目级）
- 助手下一会话读到就执行
- **特点**：跨会话持久、代码 Agent 自管清理（不占Commander Agent INSTRUCTION 堆积）、user 不再当助手传话筒
- **触发场景**：你发现自己在直接和 Local Agent 派活

**通道 B：实时干预通道（user ↔ 任何 session）**
- 你直接在任何子 Agent 会话窗口发 prompt
- 追问/纠偏/调整范围/临时改参数
- **特点**：本会话内有效、不跨会话、不落盘

### 通道 B 的回写规则（关键，按层级路由）

session 内的临时指令**有项目级影响**时，必须由对应层级回写到持久文件，否则下次会话丢：

| session 内说的话 | 影响层级 | 回写责任方 | 回写到哪 |
|-----------------|---------|----------|---------|
| "prototype 维度改 128 试试" | 代码域（临时参数） | 不需回写 | — |
| "这个消融先不做了，改跑 C7" | 代码域（任务范围） | 代码 Agent | `docs/INSTRUCTION_*.md` + `SESSION_HANDOFF_CodeAgent.md` §M/§P/§D |
| "D11 用 Cyclic 触发，T_c=14" | 代码域（设计决策） | 代码 Agent | `SESSION_HANDOFF_CodeAgent.md` §M/§P/§D + 必要时上报Commander Agent |
| "实验结果显示 memory 无效" | **项目级**（颠覆 SSOT） | 代码 Agent **上报** → Commander Agent | `SESSION_HANDOFF.md` §0.1 + DECISION_*.md |
| "这块写法按 current paper version修正" | **项目级**（红线变更） | Commander Agent | `SESSION_HANDOFF.md` §4 红线段 |

**操作建议**：session 结束前，让子 Agent 自检"本次会话有没有项目级变更"，有则触发对应层级回写（代码域→代码 Agent / 项目级→Commander Agent）。

---

## §1 会话开场白（最重要，复制粘贴）

### 1.1 给任何 Agent 开新会话时的第一句话

不管你开的是代码 Agent / 研究 Agent / 写作 Agent / 苏格拉底 Agent，**第一句话永远是这段**（直接复制粘贴）：

```
请先读取以下三个文件，然后按规则执行：

1. session/AGENT_COLLABORATION_PROTOCOL_v1.0.md
2. MEMORY_INDEX.md
3. session/SESSION_HANDOFF.md

读完后用 3 句话告诉我：
  ① 你理解的当前项目状态（一句话）
  ② 你的职责边界（能做什么/不能做什么）
  ③ 你建议本次会话从哪里接续

然后等我的 INSTRUCTION 再动手。
```

**为什么这段话有效**（30 秒冷启动原理）：
- Agent 每次新会话是冷启动无记忆
- 三件套读完 = 知道全局 + 知道自己是谁 + 知道规则
- "等 INSTRUCTION 再动手" 防止 Agent 自作主张乱改

**⚠️ 大文件硬规则（2026-07-13 第二十二轮新增，治 handoff 截断）**：
`SESSION_HANDOFF.md`(~97KB)/`SESSION_HANDOFF_CodeAgent.md`(~141KB) 已超 harness Read 预览上限（仅给 ~2KB），**严禁整文件 Read——会截断致 Agent 拿到残缺上下文**。正确读法：
1. 先 `grep -n '^## ' <file>` 看顶部「📑 目录与针对性阅读指南」的章节行号表
2. 按行号 Read 区间（冷启动只读前两条章节：主 handoff = §0.1 最新状态 + §0 文档体系导航）
3. 其余章节按需 grep 行号后针对性 Read
4. 闭环记录段（按日期 append-only 历史）仅追溯时读，最新状态以 §0.1 为准
行号会随后续编辑漂移，用前必须 `grep -n '^## '` 校准。本规则对任何 >50KB 的项目文档通用。

### 1.2 给 Local Agent 子助手）的开场白

子助手不是独立 Agent，是代码 Agent（L2.5 代码域指挥）的辅助。开场白多读两份文件（2026-06-28 升级）：

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

**关键变化（2026-06-28）**：
- Local Agent
- INSTRUCTION 文件在 `docs/INSTRUCTION_Code Agent→{助手}_*.md`（不在 `session/`）
- 助手闭环记录归位 `SESSION_HANDOFF_CodeAgent.md` 对应章节（§M/§P/§D）的"派活记录"子段
- remote-server 助手 2026-06-28 正式恢复（原"已退下"作废）

**🌐 远程 session 启动 checklist（2026-07-13 第二十二轮新增，治"远程没 skill"卡死）**：
代码 Agent / remote-server 助手等跑在**远程 session**，本地 local machine 装的 skill（loopkit 等）远程看不到。开场白后追加三步自检：
1. **git pull**——拿最新（含 `paper/.claude/skills/` 进 git 的 skill + handoff TOC + 路径修复）
2. **验 skill 可用**——试调 `/kill-dead-code` 等斜杠命令；可用则用
3. **不可用则降级**——skill 本质是方法论 prompt 不是工具，INSTRUCTION 已内联方法论（grep 全仓证无引用 + 查 flag 门控 + 删 + 跑 suite 验零行为变化），用普通 `grep/read/edit` 等价执行，**不等、不卡、不报错中止**
关键：远程 session 只信 git 里的项目级 `paper/.claude/skills/`，不信本地 local machine 的 `~/.claude/skills/`。skill 进 git 是远程同步的唯一通道。

---

## §2 派活模板（INSTRUCTION §4.1）

### 2.1 文件命名

`session/INSTRUCTION_Commander Agent→{目标Agent}_{主题}_{YYYY-MM-DD}.md`

### 2.2 模板（直接填）

```markdown
# Commander Agent → {目标Agent}：{主题}
> 日期：YYYY-MM-DD | 性质：P0/P1 | 前置文件：①②

## 背景（为什么做、服务于什么目标）

## 任务清单
| # | 目标 | 具体动作 | 产出位置 | 红线 |
|---|------|---------|---------|------|
| 1 | ... | ... | ... | 不能改 SSOT / 不能虚报完成 |

## 评估维度（如涉及评估）

## 回报要求
- 精确到行号 + 命令 + 磁盘证据（diff 片段 / grep 输出）
- 完成后在个人 handoff 末尾追加 `## YYYY-MM-DD 闭环记录`（§4.2 格式）
- 不接受"全部完成"汇总陈述，必须逐项 `[x]/[ ]` 勾选
```

### 2.3 指令简洁原则（2026-06-26 新增，详见协议 §4.1）

INSTRUCTION 是**方向性指导**，不是详细 SOP。Agent 模型能力够强，能自主补全实施细节。

- ✅ 写：目标 / 前置文件 / 红线 / 产出位置 / 回报格式 / 评估维度
- ❌ 不写：具体步骤 / 参数值 / 实施细节 / 预期数字 / 时间估算
- 判断标准：删掉一条指令后 Agent 仍能基于目标 + 前置文件 + 红线自主完成 → 这条就是冗余
- 例外：红线、SSOT 引用、产出位置必须精确

### 2.4 派活前必做

触发 `task-analysis` skill：先分析任务类型（研究/写作/代码/协调），再决定派给哪个 Agent。

---

## §3 周节奏（你的日常管理循环）

| 时机 | 动作 | 时长 | 工具 |
|------|------|------|------|
| **每次开新会话前** | 快读 SESSION_HANDOFF §0.1 + 目标 Agent handoff 闭环记录段 | 2 min | 直接 Read |
| **每周一** | 深度扫 4 个 handoff 全文 + `cross_agent_lessons.md` + 根目录项目级 INSTRUCTION 堆积（`session/INSTRUCTION_*`）+ 代码域 INSTRUCTION 堆积（`docs/INSTRUCTION_Code Agent→*`，由代码 Agent 自管，Commander Agent 只看不清理） | 15 min | Read + ls |
| **每次派活** | task-analysis 分析 → 写 INSTRUCTION → 粘贴 §1 开场白给目标 Agent | 10 min | task-analysis skill |
| **每次接汇报** | `grep '\[ \]'` 核对勾选状态（防虚报） | 1 min | 终端 grep |
| **遇到分叉** | 用 DECISION 模板让各 Agent 出独立分析，你拍板 | 按需 | §4.4 模板 |
| **子 Agent 会话结束** | 让子 Agent 自己触发 `neat-freak`（文档同步）+ `memory-cleanup`（如涉及记忆） | 2 min | skill 触发词，跟着会话走非日历 |
| **学习/复习** | 喊"苏格拉底"，会话结束按 §5 三件套沉淀 | 按需 | socrates skill |

### 3.1 朋友给的"每日循环"（更轻量，日常用这个）

```
1. 读 SESSION_HANDOFF.md §0.1（30秒掌握全局）
2. 各 Agent handoff 扫 ⚠️风险 + 闭环记录（2分钟）
3. 注入思考 → 通过Commander Agent 写 INSTRUCTION 派发
4. Agent 会话首句：粘贴 §1 开场白
5. 做完 → Agent 更新 handoff + 触发 neat-freak 自检 → 你扫一眼闭环记录
```

---

## §4 进度查阅 SSOT 表（想知道什么去哪看）

不需要逐个打开 Agent 问进度——SSOT 体系已经解决：

| 想知道什么 | 去哪看 | 粒度 |
|-----------|--------|------|
| 全局状态 | `SESSION_HANDOFF.md` §0.1 | 一段话 |
| 代码/实验进度 | `SESSION_HANDOFF_CodeAgent.md` §M（local machine）/§P（remote-server，2026-06-28 恢复）/§D（数据） | 当前任务 + checkpoint |
| 写作进度 | `SESSION_HANDOFF_WritingAgent.md` | 哪节改了/等什么 |
| 研究进度 | `SESSION_HANDOFF_ResearchAgent.md` | 精读几篇/ACTION 产出 |
| 跨 Agent 踩坑 | `cross_agent_lessons.md` | 5 分钟扫完 |
| 协作规则 | `AGENT_COLLABORATION_PROTOCOL_v1.0.md` | 全文 360 行 |
| paper SSOT | `paper_drafts/main_paper.md` | current version |

**核心原则**：先读 SSOT 再问 Agent。Agent 的时间是用来干活的，不是来回答"你进度怎样"的。

---

## §5 决策模板（DECISION §4.4）

遇到多方分歧 / 跨 Agent 协调 / 项目级范围调整时用：

```
session/DECISION_{主题}_{YYYY-MM-DD}.md
```

模板见 `AGENT_COLLABORATION_PROTOCOL_v1.0.md` §4.4。已试用一次：`DECISION_4篇聚焦ThePaper_2026-06-26.md`。

---

## §6 接汇报的防虚报核对（实战教训）

**背景**：2026-06-26 助手汇报"P0/P1/P2 全✅"，grep 后发现 P1 剩 2 项 `[ ]`、P2 剩 4 项 `[ ]` 未做。

**核对动作**（每次接"全部完成"汇报必做）：

```bash
# 在被汇报的文件目录下
grep -n '\[ \]' <文件>
# 有输出 = 有未完成项，要求助手补做或说明未做原因
```

**红线**：不接受"全部完成""已验证通过"等汇总性陈述。只认 `[x]` 勾选 + 磁盘证据（diff/grep/commit hash）。

## §6.5 INSTRUCTION 清理（防文档堆积）

**问题**：INSTRUCTION 是临时派活文档，每次派活都新增一份，不清理会越攒越多变成噪音。

**清理责任**（2026-06-28 升级，按层级路由）：

| INSTRUCTION 类别 | 位置 | 清理责任方 |
|-----------------|------|----------|
| 项目级（`INSTRUCTION_Commander Agent→*_*.md`） | `session/` 根目录 | Commander Agent |
| 代码域（`INSTRUCTION_Code Agent→*_*.md`） | `docs/` | **代码 Agent**（不在助手，不在Commander Agent） |

Commander Agent 只负责项目级 INSTRUCTION 清理。代码域 INSTRUCTION 由代码 Agent 自管，归档到 `docs/archive/{YYYY-MM}/`。Commander Agent 周一巡检时**只看不清理**代码域 INSTRUCTION，发现堆积超 30 天未闭环时提醒代码 Agent。

**清理时机**（跟着闭环走，非日历定时）：

| 时机 | 动作 |
|------|------|
| 子 Agent 完成汇报 + 闭环记录落盘后 | Commander Agent 顺手扫一次根目录 INSTRUCTION |
| 触发 neat-freak 巡检时 | 一并扫 |
| 每月末 neat-freak 巡检 | 必扫 |

**归档条件**（必须同时满足三条）：

1. INSTRUCTION 中所有任务项都已 `[x]` 闭环
2. 关键信息（决策/红线/任务范围变更）已回流到 `SESSION_HANDOFF.md` §0.1 或 `DECISION_*.md`
3. 超过 14 天无新动作

**归档动作**：

```bash
mkdir -p session/archive/$(date +%Y-%m)
mv session/INSTRUCTION_*.md session/archive/$(date +%Y-%m)/
```

**强制归档**：超过 30 天仍未闭环且无活跃会话引用 → 强制归档 + 在 `cross_agent_lessons.md` 追加"未闭环原因"。

**红线**：
- ❌ 不得在关键信息回流前归档
- ❌ 不得 rm，只 mv
- ❌ 不得归档任务项未全 `[x]` 的 INSTRUCTION（除非走强制归档并记录原因）

**扫描命令**（Commander Agent 自检）：

```bash
# 看根目录还有多少 INSTRUCTION
ls session/INSTRUCTION_*.md 2>/dev/null | wc -l

# 看哪些有未完成任务项
for f in session/INSTRUCTION_*.md; do
  echo "=== $f ==="
  grep -c '\[ \]' "$f" 2>/dev/null
done

# 看哪些超过 14 天没改过
find session/ -name 'INSTRUCTION_*.md' -mtime +14 2>/dev/null
```

---

## §7 苏格拉底 Agent 的正确用法

| 场景 | 用苏格拉底 | 用Commander Agent 模式 |
|------|----------|-----------------|
| "我想搞懂 the paper 的 Write Gate 梯度路径" | ✅ | |
| "帮我 review 一下 v9+ 故事线" | ✅ | |
| "会议前快速复习 contribution" | ✅ | |
| "我要派代码 Agent 跑实验" | | ✅ |
| "研究 Agent 精读完了，下一步怎么分配" | | ✅ |
| "B/D/E 论文要不要重启" | | ✅ |

**苏格拉底会话结束**：自动按 `SESSION_HANDOFF_LearningAgent.md` §5 三件套沉淀（未决议题/纠错记录/学习锚点），下次接续。

---

## §8 多 Agent 并行协作

想让多个 Agent 同时干活时：

1. 写多份 INSTRUCTION（一份 per Agent）
2. 同时开多个会话窗口，各自粘贴 §1 开场白
3. 各 Agent 独立执行，完成后更新各自 handoff
4. 你定期扫 handoff 闭环记录，发现卡点就介入

**跨 Agent 数据流转**：协议 §0.6 流转矩阵已定义。Agent 之间**不直接通信**，通过磁盘文件异步传递：
- 研究 → 写作：ACTION 文件
- 代码 → 写作：`SHARED_RESULTS.md`
- 指挥 → 全体：INSTRUCTION + SESSION_HANDOFF §0.1

---

## §9 Skill 清单（全部已安装，2026-06-26 验证）

| 类别 | Skill | 触发词 | 用途 |
|------|-------|--------|------|
| 🎓 学习 | socrates | 苏格拉底/学习/精读 | the paper 学习陪练 |
| 🎓 学习 | dream-engine | 做梦/灵感/idea | 研究 idea 发散 |
| 🎓 学习 | experiment-autopsy | 实验尸检/复盘 | 实验因果分析 |
| 🎓 学习 | research-driven-design | 训练策略/loss 设计 | 研究↔代码桥梁 |
| 🎓 学习 | research-paper-pipeline | 写论文/顶会/精读 | 写作+研究共用 |
| 🔧 协同 | handoff | 交接/转接/总结 | 跨 Agent 接力 |
| 🔧 协同 | neat-freak | 整理一下/同步/收尾 | 文档巡检 |
| 🔧 协同 | memory-cleanup | 清理记忆/记忆太乱 | 记忆巡检 |
| 🔧 协同 | task-analysis | 任务分解/派活分析 | 派活前分析 |
| 🔧 协同 | auto-cr | 代码评审/CR | 提交前自检 |

**安装位置**：`~/.claude/skills/`（local machine 本地）。全部 SKILL.md 验证通过。

---

## §10 给所有 Agent "重新按规则做事"的指令

**答案**：不需要单独通知某个 Agent——Agent 每次新会话冷启动，下次开会话时第一句粘贴 §1 开场白即可让任何 Agent 30 秒内按规则做事。

**如果你想批量通知**（不是必须）：在 `SESSION_HANDOFF.md` §0.1 主线段加一行：

```
> 2026-06-26 更新：协同规则 v1.0 已落地，所有 Agent 新会话首句必须读三件套（协议+MEMORY_INDEX+主HANDOFF），按 §1.1 开场白执行。
```

这样任何 Agent 下次读 §0.1 时自动看到。

---

## §11 你的思考注入通道（按层级路由，2026-06-28 升级）

| 通道 | 影响层级 | 适用场景 | 操作 |
|------|---------|---------|------|
| **直接改 SSOT** | 项目级 | 你的判断是项目级共识 | 写进 `SESSION_HANDOFF.md` §0.1 主线段 |
| **派项目级 INSTRUCTION** | 项目级 | 你的思考是研究/写作/苏格拉底任务 | 写 `session/INSTRUCTION_Commander Agent→*_*.md` |
| **派代码域 INSTRUCTION** | 代码域 | 你的思考是实验/数据/代码改动/助手调度 | 在代码 Agent 会话口述 → 代码 Agent 写 `docs/INSTRUCTION_Code Agent→*_*.md` |
| **触发 DECISION** | 项目级 | 你的思考是分叉决策 | 让各 Agent 出独立分析，你拍板落盘 `DECISION_*.md` |

---

## §12 红线（你不能踩）

1. **不直接改 the paper 正文**——那是写作 Agent 的活，你只通过 INSTRUCTION/ACTION 派活
2. **不直接改实验代码**——那是代码 Agent 的活
3. **不绕过 SSOT**——你的判断必须落盘到指定文件，不能口头传达
4. **不接"全部完成"汇总陈述**——必 grep `[ ]` 核对（§6）
5. **不让 Agent 之间直接通信**——通过磁盘文件异步传递（§8）

---

*v1 · 2026-06-26 · 综合 AGENT_COLLABORATION_PROTOCOL_v1.0 + 朋友"30秒冷启动"方案 + 实战教训*
