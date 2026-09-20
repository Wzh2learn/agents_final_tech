# 批 #8-A Skill 瘦身与合并 — 只读盘点 + 合并方案（待用户确认，未改任何 skill）

> 状态: 方案稿（2026-09-21, Loop D 主线）**本件只做盘点与方案, 未动 skills/ 里任何文件**
> 工具: skill-merger（`scan_skills.py`）+ skill-map（`skill-map.py`）; **全部在 GB10 上跑**
> 基线: `38a329d` | 扫描根: `~/wzh/projects/agents_final_tech/skills`

## 0 盘点口径与两处必须先说清的发现

### 0.1 数字对账: 「114」是安装项而不是 skill 数

| 口径 | 值 | 说明 |
|---|---|---|
| 仓库 `skills/` 目录数（真实 skill 数） | **108** | `find skills -maxdepth 2 -name SKILL.md` = 108; 顶层目录 108 |
| `A_SKILLS` 项数 | **93** | Loop A 分发表 |
| `C_SKILLS` 项数 | **21** | Loop C 分发表 |
| `sync_skills --check` 自报总数 | **114** | = 93 + 21, 即**安装项数** |
| 两表交集 | **6** | `agent-prompt-contracts` / `evaluator-calibration` / `jinrong-docs-sync` / `m2-rag-playbook` / `paper-review-check` / `verify-before-done` |

⇒ **114 不是 skill 数，是 93+21 的安装项数；盘点基数 = 108 个目录**。两表都与磁盘严格对得上（列而未在盘 = 0、在盘而未列 = 0），所以「114 vs 108」不是漂移，是两个口径。

### 0.2 skill-map 报 129 个的原因（不是多出来 21 个 skill）

skill-map 在 `skills/` 下扫到 **129** 个 `SKILL.md`，其中 **21 个是 `scientific-toolkit-skill/references/scientific-skills/*` 里的内嵌子 skill**（astropy / matlab / pandas 等）。这些子 skill **不在 `A_SKILLS`/`C_SKILLS` 分发表内**，也不是独立目录，是 `scientific-toolkit-skill` 自带的参考资源。⇒ skill-map 的「129」对本次合并不直接可用；**合并基数以 108 目录为准**。

同时 skill-map 报了 **1 个 `duplicate-install`**：`pdf`（`skills/pdf/` 与 `scientific-toolkit-skill/references/scientific-skills/pdf/`）—— 这正是 08-29 裁定表已裁定过的「pdf 双份」（仓库版为准），处置 = 保持现状，**不在本次合并范围**。

## 1 保护清单（用户指定，本次不合并、不改名、不移动）

| skill | Loop | 行数 | 为何保护 |
|---|---|---|---|
| `graph-loop-rules` | A | 26 | 本仓红线唯一入口, 每个 agent 任务开头读 |
| `agent-prompt-contracts` | A/C | 69 | 已验证 prompt 契约库 + 治理规则; A/C 双列 |
| `jinrong-docs-sync` | A/C | 45 | 文档四层治理 + INDEX 单一入口; A/C 双列 |
| `m1-gap-triage` | A | 68 | 嘉合 playbook 固化的 M1 分诊主路径 |
| `m2-rag-playbook` | A/C | 58 | M2 RAG 失败模式手册; A/C 双列 |
| `repo-audit` | C | 205 | C 线核心治理审计循环 |
| `audit-cycle` | C | 160 | 证据纪律层, repo-audit 与 verify-before-done 都调用它 |

另 3 件虽未点名但本次也**不动**：`experiment-autopsy`（被 exp-lifecycle / code-pathology / repo-audit / COMMANDER_PLAYBOOK 四处引用，入向 12）、`systematic-debugging`（283L 完整版，08-29 已裁定不合并）、`neat-freak`（A_SKILLS 内唯一收尾管道）。
## 2 建议合并的簇

分两档：**A 档 = 职责真重叠，建议直接执行**；**B 档 = 可合并但会触及既有裁定或守卫，需用户单独拍板**。

### C1 → `research-writing-skill`（A 档）

- **成员**: `research-writing-skill` / `paper-writing-zh`
- **合并理由**: 同一职责重叠。两件都是「写/改学术论文正文」；research-writing-skill (72L, 中文优先, 含章节导向 + 改写规则 + 源材料分层) 是 paper-writing-zh (24L 通用简短版) 的超集 —— 后者的四条 Checks（贡献/证据/术语/局限）已被前者覆盖。
- **资源处理**: 零资源文件冲突。把 paper-writing-zh 的 Checks 四条作为一节并入（已有同名节，合并去重）。
- **风险**: 低。paper-writing-zh 在 `SKILL_ROUTING.md` 论文线与 `AGENTS.md` 注册表各 1 行。
- **计数**: 目录 −1；A 项 93→92。

### C2 → `experiment-analysis`（A 档）

- **成员**: `experiment-analysis` / `experiment-observer`
- **合并理由**: 同一工作面且高度互补。analysis (132L) = 实验结果归因五步框架；observer (112L) = 从日志周期巡检、指标解读、健康度判断。合并后从「周期看盘」到「归因结论」是一条连续路径，现在分两件反而会让 agent 只装其一。
- **资源处理**: 两件均无资源文件（零冲突）。observer 的日志命令与指标读法作为「在线监测」子节并入，保留原命令原文。
- **风险**: 低-中。observer 的描述偏 recsys 特定（HR/NDCG/proto cos），合并后 description 需同时覆盖两类触发词。
- **计数**: 目录 −1；A 项 92→91。

### C3 → `commit-and-pr-hygiene`（A 档）

- **成员**: `changelog-from-diff` / `clean-commits` / `pr-from-diff`
- **合并理由**: 同一交付物的三个面。三件都是「把改动整理成审阅者能快速读的产出」（发行说明 / commit message / PR body），各 12-13 行，引用面同构（AGENTS + sync + using-loopkit），且实际工作中总是同一流程里连续用。
- **资源处理**: 零资源文件。三节合一 ≈ 35 行。
- **风险**: 低。三件仅被 AGENTS / sync_skills / using-loopkit / SKILL_ROUTING 引用，无第三方依赖。
- **计数**: 目录 −2；A 项 91→89。

### C4 → `code-simplification`（A 档）

- **成员**: `simplify` / `reduce-nesting` / `kill-dead-code`
- **合并理由**: 同一动作的三个切面：都是「把现有代码变小 / 变清楚」的重构类指导（去抽象 / 去嵌套 / 删死代码），各 11-12 行，命中同一触发场景（重构前、清理时）。
- **资源处理**: 零资源文件。三节合一 ≈ 32 行。
- **风险**: 中。`simplify` 字面在 27 个文件出现，但绝大多数是 scientific-toolkit 内嵌参考里的普通词汇而非 skill 名引用；**实际需改的只有 4 处**（AGENTS / sync_skills / SKILL_ROUTING / codebase-map）。执行前会逐个核实。
- **计数**: 目录 −2；A 项 89→87。

### C5 → `git-history-ops`（A 档）

- **成员**: `bisect-regression` / `revert-surgical` / `rebase-safely`
- **合并理由**: 同一域（对 git 历史的操作）的三个动作：定位坏 commit (bisect) / 精准回退一个改动 (revert) / 重写历史前的安全操作 (rebase)。各 12 行，三者常在一次排查中连续使用，合并后「历史出了问题该怎么办」有单一入口。
- **资源处理**: 零资源文件。三节合一 ≈ 34 行；**各动作保留独立小节**（三者触发场景确有区别）。
- **风险**: 中。`bisect-regression` 在 `scripts/graph/loop_a_exec_constraints.md:123` 被列为 A 派发件，合并后需同步该行。
- **计数**: 目录 −2；A 项 87→85。

### C6 → `db-schema-change`（A 档）

- **成员**: `schema-diff` / `migration-writer`
- **合并理由**: 同一工作流的前后两步：先对比两个 schema 状态定风险（schema-diff），再写可回退的迁移（migration-writer）。各 11-12 行，同一会话内必然先后发生。
- **资源处理**: 零资源文件。两节合一 ≈ 24 行。
- **风险**: 低。两件仅被 AGENTS / sync / using-loopkit / SKILL_ROUTING 引用；且本仓当前无迁移工作流，该簇适用面本就窄。
- **计数**: 目录 −1；A 项 85→84。

### C7 → `frontend-quality`（A 档）

- **成员**: `design-system` / `a11y-pass` / `loading-empty-error-states`
- **合并理由**: 同一交付物(UI)的三个质量面：视觉意图（design-system）/ 无障碍（a11y-pass）/ 四态覆盖（loading-empty-error-states）。各 12-13 行，同一次界面开发中同时适用，现在分三件会让 agent 只装其一。
- **资源处理**: 零资源文件。三节合一 ≈ 38 行；三个面各保留一节。
- **风险**: 中。`design-system` 被 figma 系 6 件引用（figma-use 及其 references / figma-implement-design / figma）。**执行前必须逐处核实那些引用是「技术共享名词」还是「skill 名引用」**，只改后者。
- **计数**: 目录 −2；A 项 84→82。

### C8 → `testing-practices`（A 档）

- **成员**: `write-failing-test-first` / `coverage-gaps` / `contract-test` / `flaky-hunter`
- **合并理由**: 同一工作面（测试）的四个实践：先写失败测试 / 找覆盖空白 / 契约测试 / 查间歇失败。各 12-13 行，同一开发环节（写代码→补测试→修问题）。
- **资源处理**: 零资源文件。四节合一 ≈ 48 行。
- **风险**: 中-高。四者触发场景恰好有区别（TDD / 覆盖率 / 契约 / 稳定性），合并后 description **必须逐类写清四类触发词**，否则会从「四件各专一件」变成「一件四头不靠」。`write-failing-test-first` 在 loop_a_exec_constraints:120 有独立行。
- **计数**: 目录 −3；A 项 82→79。

### C9 → `web-deploy`（A 档）

- **成员**: `cloudflare-deploy` / `vercel-deploy`
- **合并理由**: 同一任务（把 web 应用发到托管平台）的两个平台实现。两件已由 08-29 裁定表标为「个人通用，不主动装载」，合并后仍不主动装载。
- **资源处理**: 合并后保留两个子目录：`references/cloudflare/`（309 个资源文件）与 `references/vercel/`（3 个），按来源前缀归位。
- **风险**: 中。**本簇资源迁移量最大**（cloudflare 309 个文件）。因两件本就不主动装载，**建议标为可选项「延后」**，与其他簇不同批。
- **计数**: 目录 −1；A 项 79→78。

### C10 → `codebase-review`（A 档）

- **成员**: `codebase-map` / `review-codebase`
- **合并理由**: 同一目的（让人看懂 / 评估一个仓库）的两种输出：结构图谱（codebase-map, 311L）与架构健康评审（review-codebase, 383L）。两者都是全仓层面的只读产出，合并后作为两模式。
- **资源处理**: 零资源文件冲突。保留「结构图谱」与「健康评审」两模式。
- **风险**: 中。两件**分属不同 Loop**（map=A, review=C）⇒ 合并后新件必须同时进 A 与 C，**安装项数不降**（目录 −1 但 A+C 各 −1/+1）。另 `review-codebase` 是 C 线核心件，合并后需确保 C 线仍拥有架构审计能力。
- **计数**: 目录 −1；**A/C 安装项不降**（本簇是唯一不降安装项的）。
—— A 档小计：**10 簇，目录 −16**；A 安装项 93→**78**（脚本实算；其中 C10 净 0）；C 安装项 21→**21**（C10 一进一出）。

### C11 → `paper-audit`（B 档）

- **成员**: `paper-review-check` / `paper-polish-and-audit`
- **合并理由**: 同一对象（论文）的相邻阶段：draft 期逻辑审查 vs 投稿前终审。两件常连续使用，合并后作为「过程审查」与「投稿门」两模式。
- **资源处理**: 零资源文件。两节合一 ≈ 87 行。
- **风险**: **高 — 本簇推翻既有裁定**。`docs/SKILL_ROUTING.md:29` 裁定表已逐字裁定这两件「**分工并存**（过程审查用前者, 投稿终审用后者）」。合并 = 推翻该行。**必须用户显式同意才能做**，否则保持现状。
- **计数**: 目录 −1；A 项 −1；C 项不变。

### C12 → `progress-reading-protocol`（B 档）

- **成员**: `progress-reading-protocol` / `broken-window-check`
- **合并理由**: 后者已是前者的第 6 步。progress-reading-protocol 的固定 6 步序列末步就是「smoke-test 上个功能」，而 broken-window-check 正是该步的展开（「看起来交付了实际没交付」）。
- **资源处理**: 零资源文件。两节合一 ≈ 104 行。
- **风险**: 中。`broken-window-check` 在 08-29 裁定表被列入前端线主装；合并后需同步 `SKILL_ROUTING.md` 前端线。两件均强调「会话开头」，合并无语义损失。
- **计数**: 目录 −1；A 项 −1。

### C13 → `eval-harness`（B 档）

- **成员**: `eval-harness` / `evaluator-calibration`
- **合并理由**: 同一基建（LLM-as-judge 循环）的两件：eval-harness 建评分循环，evaluator-calibration 校准评分者人格。calibration 的「避免审阅者宽松漂移」本就是 harness 的一个必备环节。
- **资源处理**: 零资源文件。两节合一 ≈ 124 行。
- **风险**: 中。`evaluator-calibration` 是 **A/C 双列**件；合并后仍需 A+C 双列。
- **计数**: 目录 −1；A 项 −1；C 项不变。

### C14 →（无新名；从 A_SKILLS 摘除）（B 档）

- **成员**: `verification-before-completion`
- **处置理由**: 该件已于 **2026-08-25 标 DEPRECATED** 并由 `verify-before-done` 取代（这是退役而非合并），但 **至今仍在 `A_SKILLS` 分发列表内** —— 即每个 Loop A 环境仍装一件废件。
- **资源处理**: 目录按治理规则 4 保留（只标记不删除）；**动作 = 从 `A_SKILLS` 摘除该行 + prune 安装区残留**。
- **风险**: **高 — 必须与 docs_lint 同步**。`docs_lint` 的 `[5]` 是双向对账：摘除后会立刻报「注册表已登记但 A_SKILLS 未分发」⇒ FAIL ⇒ **Loop B HALT**。正确修法 = 决策 51 授权的**三步同一 commit**：(i) `[5]` 跳过用途列含 DEPRECATED 的行 + 从 `A_SKILLS` 摘除 + prune。**本条与 A19 脚本级批合并**，不单独执行。
- **计数**: 目录不变（108）；但 **A 安装项 −1**。

### C15 → `dispatching-parallel-agents`（B 档）

- **成员**: `dispatching-parallel-agents` / `subagent-fanout`
- **合并理由**: 同一能力（并行子代理）的两种表述：通用概览（167L）vs 精确 fanout 实践（13L）。fanout 的「worker 报告是声明不是证据，编排者必须验证后再合成」正是并行分发的核心风险管理，应合为一。
- **资源处理**: 零资源文件。两节合一 ≈ 180 行。
- **风险**: **高 — 本簇推翻既有裁定**。`docs/SKILL_ROUTING.md:31` 已逐字裁定 dispatching-parallel-agents / subagent-driven-development / subagent-fanout「三者粒度不同，暂不合并」，并写明「skill-merger 可后续评估」。**本次正是那个后续评估，结论建议合并 2 件（不动 subagent-driven-development）。需用户拍板。**
- **计数**: 目录 −1；A 项 −1；C 项不变。

—— B 档小计：**4 合并簇 + C14，目录 −4**（C15 对 A 净 0）；A 安装项 **−3**（C11/C12/C13 各 −1，C15 净 0）；C 安装项不变。另 C14 单独把 A 再 −1。其中 **C11 / C15 推翻 08-29 裁定表已明确的两行**，C14 需与 docs_lint 同步。

## 3 建议保留（不合并）

下列规模足够、或触发边界已清晰、或合并后会超 500 行难维护 —— **建议保持独立**：

| 簇 | 成员 | 理由 |
|---|---|---|
| 治理与审计 | `repo-audit` / `audit-cycle` / `differential-review` / `spec-to-code-compliance` / `review-codebase`（合并后） | 205-383L 的完整工作流，各自触发边界已在 description 里互相指向（audit-cycle 已写明「不用于例行 code review」） |
| 安全系列 | `owasp-review` / `sql-review` / `authz-check` / `input-validation` / `secret-scan` / `security-best-practices` / `security-threat-model` / `db-schema-change`（合并后） | 08-29 裁定表已明确「分工并存」；分别覆盖 diff 审查 / SQL 正确性 / 授权 / 边界输入 / 密钥 / 语言特定最佳实践 / 威胁建模，互不替代 |
| 子代理与计划 | `subagent-driven-development` / `executing-plans` / `writing-plans` / `spec-first` / `sprint-contract` | 五件是不同层次（规格 / 计划编写 / 计划执行 / 子代理精内核执行 / 契约议定），且 subagent-driven-development 已 503L |
| 实验与运维 | `experiment-autopsy` / `offline-eval-playbook` / `harness-stripping` / `data-sync` / `gpu-env` / `train-monitor` | autopsy 入向引用 12 处（保护）；offline-eval-playbook 与 analysis 是「离线评测」与「实验归因」两个不同阶段；data-sync/gpu-env/train-monitor 是工程运维操作 |
| 工程实践（单件） | `systematic-debugging` / `testing-practices`（合并后） | systematic-debugging 283L 完整版，08-29 已裁定不合并 |
| 项目专属与 meta | `graph-loop-rules` / `agent-prompt-contracts` / `jinrong-docs-sync` / `m1-gap-triage` / `m2-rag-playbook` / `neat-freak` / `exp-lifecycle` / `dream-engine` / `socrates` / `recsys-toolkit` / `skill-doctor` / `skill-map` / `skill-merger` / `skill-hook-trigger` / `skills-best-practices` | 各自唯一职责；meta 层四件已有明确分工（doctor 体检 / map 引用图 / merger 合并 / hook 触发） |
| 前端与外部工具 | `figma` 系 6 件 / `playwright` / `playwright-interactive` / `frontend-quality`（合并后）/ `jupyter-notebook` / `pdf` / `pdf-ingestion` | figma 6 件共 22 条内部依赖，已是一个密集子系统；playwright-interactive 693L；pdf 双件已裁定合一（仓库版为准） |
| 学术写作与工具 | `research-writing-skill`（合并后）/ `algorithm-description` / `office-academic-skill` / `literature-review` / `citation-management` / `scientific-toolkit-skill`（1 顶 21 子） | 各自产出物不同（正文 / 伪代码 / Word-PPT / 综述 / 引文 / 科学计算） |

## 4 建议拆分 / 建议废弃

| 建议 | 对象 | 理由 |
|---|---|---|
| **建议废弃（从分发摘除，目录保留）** | `verification-before-completion` | 已于 2026-08-25 标 DEPRECATED 并被 `verify-before-done` 取代；**当前仍在 A_SKILLS 里被主动分发** ⇒ 每个 Loop A 环境多装一件废件。见 C14。 |
| **建议废弃（待确认）** | `scientific-toolkit-skill` 内嵌的 21 个子 skill | 它们不在分发表内、也不是独立目录，**不属「合并集」范围**；但 skill-map 会把它们计进来导致数字混淆。建议：不动它们，**但以后引用 skill-map 数字时必须声明口径**。 |
| **建议不拆分** | 全部 | 本次盘点未发现「单件职责过宽需拆」的候选；唯一接近的是 `playwright-interactive`（693L）与 `subagent-driven-development`（503L），但两者都是**单一流程的完整描述**，拆开会产生新的触发冲突 |

## 5 预期结果（已用脚本对 A/C 两表逐项重算，非手算）

| 项 | 现状 | A 档 10 簇后 | A 档 + C14 摘除 | A+B 全批 | A+B 全批 + C14 |
|---|---|---|---|---|---|
| 仓库 skills 目录数 | 108 | 92 | 92 | **88** | **88** |
| `A_SKILLS` 项数 | 93 | 78 | **77** | 75 | **74** |
| `C_SKILLS` 项数 | 21 | 21 | 21 | **21** | **21** |
| 两表合计（= `sync --check` 总数） | 114 | 99 | **98** | 96 | **95** |
| 两表交集 | 6 | 7 | 7 | **8** | 8 |

**逐簇的 A/C 增减（脚本实算）**：

| 新名 | A 增减 | C 增减 |
|---|---|---|
| `research-writing-skill` | −1 | 0 |
| `experiment-analysis` | −1 | 0 |
| `commit-and-pr-hygiene` | −2 | 0 |
| `code-simplification` | −2 | 0 |
| `git-history-ops` | −2 | 0 |
| `db-schema-change` | −1 | 0 |
| `frontend-quality` | −2 | 0 |
| `testing-practices` | −3 | 0 |
| `web-deploy` | −1 | 0 |
| `codebase-review` | 0 | 0 |
| `paper-audit` | −1 | 0 |
| `progress-reading-protocol` | −1 | 0 |
| `eval-harness` | −1 | 0 |
| `dispatching-parallel-agents` | 0 | 0 |

→ 目标「114 降到 90 左右」**需 A+B 全批执行才接近（95-96）**；只做 A 档到 98-99。两者都在合理区间，且 A 档零触及既有裁定。

**两处交叉 Loop 簇的说明**（这是交集从 6 升到 8 的原因）：`codebase-review`（C10, map=A + review=C）与 `dispatching-parallel-agents`（C15, dispatching=A + fanout=C）合并后**新名同时进入 A 与 C**，故该两簇对两表都是净 0，但交集 +2。

## 6 执行方案（待确认，本批未执行）

1. **备份**：整簇复制到仓外 `D:\AIRcommend\JinRongAgents\skills-backup\<YYYYMMDD-HHMMSS>/`，**不入 commit**；备份失败即中止。
2. **逐簇合并**：融合 description（覆盖全部成员触发场景、去重消歧）→ 按逻辑重组正文（不简单拼接）→ 资源文件同名者加**来源前缀**并更新正文引用。
3. **新件自检**：`name` 合规、description 含「做什么 + 何时用」、SKILL.md ≤ 500 行（超则下沉 `references/`）、无悬挂引用。
4. **更新四处清单**：`scripts/graph/sync_skills.sh` 的 A/C 表 · `AGENTS.md` 配属注册表 · `docs/SKILL_ROUTING.md` 五线主装 · `scripts/graph/loop_a_exec_constraints.md`（派发路径现役件）—— **只改技能名与路由映射，不改治理原则**。
5. **下游引用扫描**：改名前列出全部引用位点，逐处判定是「skill 名引用」还是「技术名词」；**只改前者**。
6. **一致性守卫父子**：`A_SKILLS ∪ C_SKILLS == skills/ 目录集`（当前两边各 108）。**执行后必须重新相等**，否则 `docs_lint [5]` 报 FAIL。
7. **三层守卫同步**：`verification-before-completion` 若摘除，**必须与 docs_lint `[5]` 修法同 commit**（决策 51 三步）。
8. **GB10 权威复核**：skill-doctor errors = 0 · `sync_skills --check` PASS · `docs_lint` exit 0 / 0 fail / **1 warn 保持** · 若改 shell 则 `bash -n` · 若改可执行逻辑则跑相关测试。
9. **两个 commit**：commit 1 = 本方案与盘点报告；commit 2 = 实际合并与分发更新。

## 7 需用户拍板的点

1. **A 档 10 簇是否直接执行**（零触及既有裁定，但仍是不可逆的合并）。
2. **C9（web-deploy）是否本批做**：309 个资源文件迁移量最大，且两件不主动装载 ⇒ 建议延后。
3. **C10（codebase-review）如何处理双 Loop**：合并后不降安装项，需确认是否仍值得合。
4. **C11（paper-audit）是否推翻 08-29 的「分工并存」裁定**。
5. **C15（dispatching-parallel-agents）是否推翻 08-29 的「暂不合并」裁定**。
6. **C14 与 A19 脚本级批合并**的时点（需 docs_lint `[5]` 同步）。
7. **B 档是否只做 C12/C13**（不推翻裁定的那两个），把 C11/C15 置为「保持现状」。

## 8 本批做了什么 / 没做什么

- **做了**：GB10 上跑 skill-merger `scan_skills.py` 与 skill-map；完成 108 目录的全量清点；按**语义簇**（非名字相似度）分出 15 簇；给出每簇的合并理由 / 资源方案 / 风险 / 计数影响；清点侧线引用爆炸半径。
- **没做（明确）**：**未修改 skills/ 下任何文件**；未改 `sync_skills.sh` / `AGENTS.md` / `SKILL_ROUTING.md`；未删任何目录；未外发；未动论文与 `docs/33` / `docs/34`；未动实验工件。
- **执行纪律**：全部扫描与校验在 GB10 上跑；本机只做文本编辑与 git。
## 附录 A 全量清单（108 个目录）

> 口径: Loop 列取自 `A_SKILLS` / `C_SKILLS`; 行数 = SKILL.md 物理行; 资源 = scripts/references/assets 下文件数。

| # | skill | description 摘要 | Loop | 行数 | 资源 | 是否重复 | 是否可合并 | 建议处置 |
|---|---|---|---|---|---|---|---|---|
| 1 | `a11y-pass` | Catch the accessibility failures that ship in almost every AI-built UI. Use af | A | 13 | 0 | 否 | 是 → `frontend-quality` | **合并**(A档) |
| 2 | `agent-prompt-contracts` | JinRongAgents 已验证的 4 条 agent prompt 契约 (verbatim 首查 / FORMAT_HINT / bash 先行 /  | A/C | 69 | 0 | 否 | 否 | **保护** |
| 3 | `agent-rules` | Use when creating or updating AGENTS.md files, .github/copilot-instructions.md | A | 87 | 152 | 否 | 否 | 保留 |
| 4 | `algorithm-description` | Use when converting source code, formulas, or implementation notes into paper- | A | 23 | 0 | 否 | 否 | 保留 |
| 5 | `audit-cycle` | >- | C | 160 | 0 | 否 | 否 | **保护** |
| 6 | `authz-check` | Verify that an endpoint checks ownership, not just authentication. Use on any  | A | 12 | 0 | 否 | 否 | 保留 |
| 7 | `bisect-regression` | Find the exact commit that introduced a bug. Use when something worked before  | A | 12 | 0 | 否 | 是 → `git-history-ops` | **合并**(A档) |
| 8 | `broken-window-check` | Before picking new work, smoke-test the last "completed" feature. If it's brok | A | 55 | 0 | 否 | 是 → `progress-reading-protocol` | **合并**(B档) |
| 9 | `changelog-from-diff` | Turn a set of commits or a diff into a clean, user-facing changelog entry. Use | A | 13 | 0 | 否 | 是 → `commit-and-pr-hygiene` | **合并**(A档) |
| 10 | `clean-commits` | Turn messy WIP into clean, atomic commits with messages that explain why. Use  | A | 12 | 0 | 否 | 是 → `commit-and-pr-hygiene` | **合并**(A档) |
| 11 | `cloudflare-deploy` | Deploy applications and infrastructure to Cloudflare using Workers, Pages, and | A | 224 | 309 | 否 | 是 → `web-deploy` | **合并**(A档) |
| 12 | `code-cleanup-helper` | 兩模式工具 — Mode A 掃 codebase / SKILL.md / prompt 找重複/命名/模組/過長 4 類技術債；Mode B 跑 rep | A | 368 | 0 | 否 | 否 | 保留 |
| 13 | `code-pathology` | / | A | 416 | 0 | 否 | 否 | 保留 |
| 14 | `codebase-map` | Generate a structural overview and dependency diagram of the codebase. Use whe | A | 311 | 0 | 否 | 是 → `codebase-review` | **合并**(A档) |
| 15 | `context-budget` | Keep the agent's context lean so accuracy doesn't collapse. Use on long sessio | A | 12 | 0 | 否 | 否 | 保留 |
| 16 | `contract-test` | Test the boundary between two systems by the contract, not the implementation. | A | 12 | 0 | 否 | 是 → `testing-practices` | **合并**(A档) |
| 17 | `coverage-gaps` | Find the untested code paths that actually matter, not just the coverage perce | A | 12 | 0 | 否 | 是 → `testing-practices` | **合并**(A档) |
| 18 | `data-sync` | Download data or model checkpoints from object storage to local training serve | A | 58 | 0 | 否 | 否 | 保留 |
| 19 | `decision-record` | Capture an architectural decision so the next session (or engineer) knows WHY. | A | 13 | 0 | 否 | 否 | 保留 |
| 20 | `dependency-audit` | Decide whether to add, keep, or remove a dependency. Use before adding any pac | A | 13 | 0 | 否 | 否 | 保留 |
| 21 | `design-system` | Make frontend output look intentional, not AI-generated. Use for any UI work — | A | 13 | 0 | 否 | 是 → `frontend-quality` | **合并**(A档) |
| 22 | `differential-review` | > | C | 228 | 1 | 否 | 否 | 保留 |
| 23 | `dispatching-parallel-agents` | Use when facing 2+ independent tasks that can be worked on without shared stat | A | 167 | 0 | 否 | 是 → `dispatching-parallel-agents` | **合并**(B档) |
| 24 | `dream-engine` | / | A | 194 | 23 | 否 | 否 | 保留 |
| 25 | `eval-harness` | Build a repeatable eval loop that grades agent output with an LLM judge, so pr | A | 72 | 0 | 否 | 是 → `eval-harness` | **合并**(B档) |
| 26 | `evaluator-calibration` | Calibrate a reviewer persona with few-shot rubric examples so skepticism stays | A/C | 52 | 0 | 否 | 是 → `eval-harness` | **合并**(B档) |
| 27 | `executing-plans` | Use when you have a written implementation plan to execute in a separate sessi | A | 64 | 0 | 否 | 否 | 保留 |
| 28 | `exp-lifecycle` | >- | A | 107 | 0 | 否 | 否 | 保留 |
| 29 | `experiment-analysis` | / | A | 132 | 0 | 否 | 是 → `experiment-analysis` | **合并**(A档) |
| 30 | `experiment-autopsy` | / | A | 101 | 0 | 否 | 否 | **保护** |
| 31 | `experiment-observer` | 自动检查实验日志，提取关键指标（HR/NDCG/sHR/proto cos/ort_loss/group 诊断/τ 退火）、趋势分析和健康度判断。当用户需要 | A | 112 | 0 | 否 | 是 → `experiment-analysis` | **合并**(A档) |
| 32 | `feature-list-json` | Enumerate every end-to-end feature as strict JSON entries with passes:false, e | C | 81 | 0 | 否 | 否 | 保留 |
| 33 | `figma` | Use the Figma MCP server to fetch design context, screenshots, variables, and  | A | 42 | 5 | 否 | 否 | 保留 |
| 34 | `figma-code-connect-components` | Connects Figma design components to code components using Code Connect mapping | A | 349 | 5 | 否 | 否 | 保留 |
| 35 | `figma-generate-design` | Use this skill alongside figma-use when the task involves translating an appli | A | 341 | 3 | 否 | 否 | 保留 |
| 36 | `figma-generate-library` | Build or update a professional-grade design system in Figma from a codebase. U | A | 314 | 19 | 否 | 否 | 保留 |
| 37 | `figma-implement-design` | Translates Figma designs into production-ready application code with 1:1 visua | A | 258 | 3 | 否 | 否 | 保留 |
| 38 | `figma-use` | **MANDATORY prerequisite** — you MUST invoke this skill BEFORE every `use_figm | A | 233 | 25 | 否 | 否 | 保留 |
| 39 | `flaky-hunter` | Diagnose and fix tests that pass sometimes and fail other times. Use when CI i | A | 13 | 0 | 否 | 是 → `testing-practices` | **合并**(A档) |
| 40 | `gpu-env` | Activate GPU training environment, check GPU/driver status, verify torch/accel | A | 60 | 0 | 否 | 否 | 保留 |
| 41 | `graph-loop-rules` | JinRongAgents Graph Loop 红线与运行约束。OpenCode agent 在本仓库执行任何任务（解析、审计、问答、代码修改）前必须遵守 | A | 26 | 0 | 否 | 否 | **保护** |
| 42 | `harness-stripping` | Systematically remove one harness component at a time and measure impact, kill | A | 66 | 0 | 否 | 否 | 保留 |
| 43 | `init-script-contract` | Author idempotent init.sh under 120s plus sibling test.sh, stop.sh, reset.sh,  | A | 66 | 0 | 否 | 否 | 保留 |
| 44 | `input-validation` | Validate and constrain untrusted input at the boundary. Use on any handler tha | A | 13 | 0 | 否 | 否 | 保留 |
| 45 | `jinrong-docs-sync` | JinRongAgents 项目文档四层结构（活文档/当前/实验/归档）治理与 docs/INDEX.md 单一入口维护。新增文档、归档文档、neat 收尾 | A/C | 45 | 0 | 否 | 否 | **保护** |
| 46 | `jupyter-notebook` | Use when the user asks to create, scaffold, or edit Jupyter notebooks (`.ipynb | A | 107 | 9 | 否 | 否 | 保留 |
| 47 | `kill-dead-code` | Find and remove unreachable/unused code safely. Use during cleanup or before a | A | 11 | 0 | 否 | 是 → `code-simplification` | **合并**(A档) |
| 48 | `loading-empty-error-states` | Design the three states every data UI forgets. Use for any component that fetc | A | 12 | 0 | 否 | 是 → `frontend-quality` | **合并**(A档) |
| 49 | `m1-gap-triage` | M1 解析失败分诊（0 表 / unmapped 过高）：嘉合 playbook 固化的"读原文诊断 → 补 synonyms → 重跑 → 报 delta | A | 68 | 0 | 否 | 否 | **保护** |
| 50 | `m2-rag-playbook` | M2 RAG 问答失败模式手册（检索为空/数值缺失/多轮追问/脱敏掩码/跨文档聚合的对策与验证）。m2-qa agent 或任何经 jinrong-rag  | A/C | 58 | 0 | 否 | 否 | **保护** |
| 51 | `migration-writer` | Write safe, reversible database migrations for this repo's conventions. Use fo | A | 12 | 0 | 否 | 是 → `db-schema-change` | **合并**(A档) |
| 52 | `neat-freak` | >- | A | 221 | 5 | 否 | 否 | **保护** |
| 53 | `office-academic-skill` | Chinese-first academic Word and PowerPoint workflow for paper reading reports, | A | 122 | 121 | 否 | 否 | 保留 |
| 54 | `offline-eval-playbook` | / | A | 109 | 0 | 否 | 否 | 保留 |
| 55 | `organize-logs` | / | A | 121 | 0 | 否 | 否 | 保留 |
| 56 | `owasp-review` | Security-review a diff against the OWASP Top 10. Use before merging anything t | C | 15 | 0 | 否 | 否 | 保留 |
| 57 | `paper-polish-and-audit` | / | A | 64 | 0 | 否 | 是 → `paper-audit` | **合并**(B档) |
| 58 | `paper-review-check` | Use when checking a paper, thesis chapter, LaTeX draft, experiment report, or  | A/C | 23 | 0 | 否 | 是 → `paper-audit` | **合并**(B档) |
| 59 | `paper-writing-zh` | Use when writing, rewriting, or polishing Chinese or English academic papers,  | A | 24 | 0 | 否 | 是 → `research-writing-skill` | **合并**(A档) |
| 60 | `pdf` | Use when tasks involve reading, creating, or reviewing PDF files where renderi | A | 67 | 1 | 是(pdf 双份) | 否 | 保留 |
| 61 | `pdf-ingestion` | Get a PDF into the model without blowing the context window or losing structur | A | 59 | 0 | 否 | 否 | 保留 |
| 62 | `planner-spec-expand` | Expand a 1-4 sentence product brief into a full spec with a design language, a | A | 49 | 0 | 否 | 否 | 保留 |
| 63 | `playwright` | Use when the task requires automating a real browser from the terminal (naviga | A | 147 | 5 | 否 | 否 | 保留 |
| 64 | `playwright-interactive` | Persistent browser and Electron interaction through `js_repl` for fast iterati | A | 693 | 2 | 否 | 否 | 保留 |
| 65 | `pr-from-diff` | Write a PR description a reviewer can approve fast. Use when opening any pull  | A | 13 | 0 | 否 | 是 → `commit-and-pr-hygiene` | **合并**(A档) |
| 66 | `progress-reading-protocol` | Run the fixed 6-step session-opening sequence — pwd, read progress, git log, c | A | 49 | 0 | 否 | 是 → `progress-reading-protocol` | **合并**(B档) |
| 67 | `prompt-caching` | Cache the parts of the prompt that don't change so a long-running loop stops p | A | 55 | 0 | 否 | 否 | 保留 |
| 68 | `readme-audit` | Check whether a README actually lets a stranger run the project. Use on any re | C | 14 | 0 | 否 | 否 | 保留 |
| 69 | `rebase-safely` | Rebase, squash, or rewrite history without losing work or breaking shared bran | A | 12 | 0 | 否 | 是 → `git-history-ops` | **合并**(A档) |
| 70 | `receiving-code-review` | Use when receiving code review feedback, before implementing suggestions, espe | C | 205 | 0 | 否 | 否 | 保留 |
| 71 | `recsys-toolkit` | / | A | 189 | 0 | 否 | 否 | 保留 |
| 72 | `reduce-nesting` | Flatten deeply nested conditionals into readable, early-return code. Use on an | A | 12 | 0 | 否 | 是 → `code-simplification` | **合并**(A档) |
| 73 | `repo-audit` | / | C | 205 | 0 | 否 | 否 | **保护** |
| 74 | `requesting-code-review` | Use when completing tasks, implementing major features, or before merging to v | C | 95 | 0 | 否 | 否 | 保留 |
| 75 | `research-driven-design` | / | A | 296 | 0 | 否 | 否 | 保留 |
| 76 | `research-writing-skill` | Chinese-first research paper writing, revision, polishing, section drafting, r | A | 72 | 19 | 否 | 是 → `research-writing-skill` | **合并**(A档) |
| 77 | `revert-surgical` | Undo a bad change without nuking unrelated work. Use when a specific commit or | A | 12 | 0 | 否 | 是 → `git-history-ops` | **合并**(A档) |
| 78 | `review-codebase` | Optional focus area to review (e.g., "API layer", "tests", "auth system"). Def | C | 383 | 0 | 否 | 是 → `codebase-review` | **合并**(A档) |
| 79 | `schema-diff` | Compare two schema states and surface the risky changes. Use before applying m | A | 11 | 0 | 否 | 是 → `db-schema-change` | **合并**(A档) |
| 80 | `scientific-toolkit-skill` | Research computing toolkit for optoelectronic information science and engineer | A | 89 | 241 | 否 | 否 | 保留 |
| 81 | `secret-scan` | Catch hardcoded secrets, keys, and tokens before they get committed. Use befor | A | 12 | 0 | 否 | 否 | 保留 |
| 82 | `security-best-practices` | Perform language and framework specific security best-practice reviews and sug | C | 86 | 10 | 否 | 否 | 保留 |
| 83 | `security-threat-model` | Repository-grounded threat modeling that enumerates trust boundaries, assets,  | A | 81 | 2 | 否 | 否 | 保留 |
| 84 | `self-eval-bias` | Detect and interrupt the pattern where an agent confidently praises work it ju | C | 46 | 0 | 否 | 否 | 保留 |
| 85 | `shift-notes` | Write and read the between-session handoff file so a fresh agent with no memor | A | 73 | 0 | 否 | 否 | 保留 |
| 86 | `simplify` | Reduce a change to the minimum that solves the problem. Use when code is over- | A | 12 | 0 | 否 | 是 → `code-simplification` | **合并**(A档) |
| 87 | `skill-doctor` | (no description) | A | 79 | 2 | 否 | 否 | 保留 |
| 88 | `skill-hook-trigger` | 用 Hook 机制为 Skill 加确定性触发提示。当用户抱怨「skill 老是不触发/该用的时候没用上」、想「用 hook 保证 skill 触发」「给  | A | 89 | 3 | 否 | 否 | 保留 |
| 89 | `skill-map` | (no description) | A | 85 | 2 | 否 | 否 | 保留 |
| 90 | `skill-merger` | 分析并合并功能重叠的 Skill。当用户觉得 skill 太多太杂、想整理/精简/瘦身 skill 库、发现多个 skill 职责重复、说「合并重复的 sk | A | 92 | 1 | 否 | 否 | 保留 |
| 91 | `skills-best-practices` | Authors and structures professional-grade agent skills following the agentskil | A | 56 | 3 | 否 | 否 | 保留 |
| 92 | `socrates` | Socratic learning coach for any technical paper or complex topic. Use when the | A | 50 | 0 | 否 | 否 | 保留 |
| 93 | `spec-first` | Write the goal spec on disk before the agent acts, so it can't drift. Use befo | A | 13 | 0 | 否 | 否 | 保留 |
| 94 | `spec-to-code-compliance` | Verifies code implements exactly what documentation specifies for blockchain a | C | 357 | 1 | 否 | 否 | 保留 |
| 95 | `sprint-contract` | Negotiate a pre-code contract between generator and evaluator personas that de | A | 73 | 0 | 否 | 否 | 保留 |
| 96 | `sql-review` | Review SQL and ORM queries for correctness, safety, and performance before the | C | 13 | 0 | 否 | 否 | 保留 |
| 97 | `structured-output` | Get JSON out of the model reliably. Prefer tool_use with a schema over prompte | A | 54 | 0 | 否 | 否 | 保留 |
| 98 | `subagent-driven-development` | Use when executing implementation plans with independent tasks in the current  | A | 503 | 3 | 否 | 否 | 保留 |
| 99 | `subagent-fanout` | Parallelize independent sub-jobs across fresh-context subagents instead of one | C | 13 | 0 | 否 | 是 → `dispatching-parallel-agents` | **合并**(B档) |
| 100 | `systematic-debugging` | Use when encountering any bug, test failure, or unexpected behavior, before pr | A | 283 | 0 | 否 | 否 | **保护** |
| 101 | `tool-restraint` | Don't over-equip an agent with tools/MCP servers. More tools = more ways to fa | A | 12 | 0 | 否 | 否 | 保留 |
| 102 | `train-monitor` | Monitor running training jobs — check GPU utilization, training progress, loss | A | 94 | 0 | 否 | 否 | 保留 |
| 103 | `using-loopkit` | Use when starting any conversation in a loopkit-enabled project - establishes  | C | 76 | 0 | 否 | 否 | 保留 |
| 104 | `vercel-deploy` | Deploy applications and websites to Vercel. Use when the user requests deploym | A | 77 | 3 | 否 | 是 → `web-deploy` | **合并**(A档) |
| 105 | `verification-before-completion` | Use when about to claim work is complete, fixed, or passing, before committing | A | 122 | 0 | 否 | 否(退役) | **废弃**(摘除分发) |
| 106 | `verify-before-done` | / | A/C | 73 | 0 | 否 | 否 | 保留 |
| 107 | `write-failing-test-first` | Before fixing any bug, write a test that reproduces it and watch it fail. Use  | A | 13 | 0 | 否 | 是 → `testing-practices` | **合并**(A档) |
| 108 | `writing-plans` | Use when you have a spec or requirements for a multi-step task, before touchin | A | 168 | 0 | 否 | 否 | 保留 |

合计: 108 目录 = 保护 10 + 合并成员 34 + 废弃 1 + 保留 63
