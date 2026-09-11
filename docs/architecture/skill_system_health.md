# Skill 体系体检报告 (2026-08-04, Phase 1)

> 补注 (2026-08-05): 本报告扫描时仓库 skills/ 为 10 个；2026-08-04 新增第 11 个 jinrong-docs-sync（Phase 4 自定义 skill，已注册进 AGENTS.md Skill 武库），未经本轮 doctor/map 扫描。

工具: skill-doctor + skill-map (均 uv run; Windows 需 PYTHONUTF8=1 规避 GBK 解码崩溃 — skill-map 的已知平台 bug)。
扫描根: 本机 `C:\Users\王中华\.codex\skills` (Loop D 工作区) + 仓库 `skills/` (source of truth)。

## 总量

- 本地安装区: 35 个 active skill (17 社区 + 系统/插件贡献)
- 仓库 skills/: 10 个 active skill (Phase 0 入库)
- skill-map 合计去重后 63 条目 (含两处安装的重复计数)

## skill-doctor 结果

| 时点 | error | warning |
|---|---|---|
| 初检 | 47 | 32 |
| --fix-safe 后 (20 处修复) | 27 | 32 |

**已修复 (20)**: 缺失的 `agents/openai.yaml` 由 fix-safe 创建 (含仓库 skills/ 内 7 个: executing-plans / receiving-code-review / requesting-code-review / review-codebase / subagent-driven-development / systematic-debugging / verification-before-completion)。

**手工补齐 (3, 仓库 skills/)**: differential-review / spec-to-code-compliance 补 `policy.allow_implicit_invocation: true`; security-best-practices 补 `false` (其描述要求仅显式触发)。仓库 source of truth 现无 doctor error。

**剩余 27 error (全部在本机安装区, 不阻塞)**:
- 19 × OPENAI_POLICY_MISSING: 既有 yaml 缺 policy 布尔值 (fix-safe 不代写值, 需逐个按 skill 语义判定, 列入后续 neat)
- 4 × RESOURCE_LINK_MISSING: 文档链接失效
- 4 × FRONTMATTER_MISSING: algorithm-description 等个人 skill 无 frontmatter (非社区包, 不处理)

**32 warning (advisory, 不自动修)**: FRONTMATTER_FIELD_ORDER (字段顺序) 与 COMPLETION_EVIDENCE_MISSING (缺完成判据) — 社区 skill 原文风格, 记录不改。

## skill-map 结果

**重复安装 (10, 均为设计使然)**: Phase 0 的 10 个 skill 同时存在于本机 `~/.codex/skills` 与仓库 `skills/`。仓库是 source of truth, 本机是 Loop D 工作副本, 远端经 sync_skills.sh 分发 — 不视为缺陷。

**依赖关系 (全部已解析)**: figma 家族内部互链 (figma-use / figma-generate-* / figma-implement-design / figma-code-connect-components), playwright-interactive → playwright。金融项目链路 (review/debug/verify 系) 无外部依赖。

**未解析引用**: 全部为文档占位符误报 (skill-name / cdn-cgi / 50-100 等), 无需处理。

## 结论

- Phase 0 注册的 10 个 skill: metadata 健康 (仓库侧 error=0), 双端 harness 可见性已验证
- 治理动作: 每次 neat 收尾跑一次 doctor + map (AGENTS.md 治理规则 #2); 本机安装区 19 个 POLICY 缺失项列入低优清单
- 已知工具问题: skill-map 在 Windows GBK locale 崩溃, 需 PYTHONUTF8=1 (可向作者反馈)

---

## 09-11 复检（决策 22 任务 2; 第二轮, 只诊断零修复）

> 性质: 本节为 `AGENTS.md` 治理规则 2（`:388`「skill-doctor / skill-map 定期体检（每次 neat 收尾时）」）的**第二轮执行记录**; 08-04 首轮原文逐字保留作轨迹, 不回改。
> 姿势: **只跑诊断模式, 未使用 `--fix` / `--fix-safe` 或任何自动修复开关**——机械自证 = 三份 JSON 报告的 `fixes = []` 且 `fix_errors = 0`。本批**不动任何 skill 文件**（仓库 `skills/` 与两个安装区逐件字节未动）; findings 只入账, 修复归 **A19**, 而 A19 须等 A4/A5 验收通过后另批派发 Loop A。
> 环境: Windows / 宿主 Python 3.9.10 / PyYAML 6.0.2; 工具以 `python scripts/<tool>.py` 直跑（未经 `uv run`）。**skill-map 仍需 `PYTHONUTF8=1`** 规避 GBK 解码崩溃, 报错链与本报告 `:5`、`:44` 所记 08-04 的**同一平台 bug 逐字相同**（`UnicodeDecodeError: 'gbk' codec can't decode byte 0x94` → 子进程 reader 线程失败 → `result.stdout` 为 `None` → `AttributeError: 'NoneType' object has no attribute 'splitlines'`, 位置 `skill-map.py:298`）⇒ **该 bug 34 天未修, 且库内未见上游反馈记录**。
> 扫描根: 仓库 `skills/`（source of truth）+ `~/.codex/skills`（Loop A）+ `~/.claude/skills`（Loop C）三根合一轮; 另对仓库派发路径文件（`scripts/`·`templates/`·`docs/`·`memory/`）单独扫一轮交叉引用。

### 执行时点与逾期口径（**更正开工卡前提**, 只增不改）

开工卡称「全库检索确认从未真正运行过（唯一命中是 THREADS `:201` 于 08-10 记的一句『skill-map 可运行』, 属能力确认不是运行记录）」。**git 历史与该前提不符, 故本批不把「从未运行过」写进台账**, 实测如下:

| 时点 | commit | 事实 |
|---|---|---|
| 2026-08-03 23:25:54 | `e86ff07` | 治理规则 2 与配属注册表入 `AGENTS.md`（**规则立**） |
| 2026-08-03 23:31:36 | `d33b4fa` | "Phase 1 panorama - codebase map, **skill health report**, metadata fixes" ⇒ **本报告即其产物**, 同批为约 10 件 skill 补 `agents/openai.yaml` |
| 2026-08-07 23:49:08 | `74bc181` | "skills: **skill-doctor --fix-safe** 补齐 4 个自定义 skill 的 agents/openai.yaml + security-best-practices policy 修正 (0 error)" |
| 2026-08-07 23:49:44 | `8de1318` | "skills: 补齐 agent-prompt-contracts/graph-loop-rules/jinrong-docs-sync/m1-gap-triage 的 agents/openai.yaml (**skill-doctor fix-safe**)" |
| 2026-08-08 00:06:54 | `02f793d` | "docs: 二轮治理收口 — 盘点文档 **skill-map 口径更正** + rg 缺失记账 THREADS" ⇒ skill-map 曾运行, 其输出进入 `docs/experiments/2026-08-07_full_system_inventory.md` |
| 2026-08-10 | THREADS `:201` | 「rg 15.1.0 已安装, **skill-map 可运行**」= 能力确认（开工卡所引那一条, 定性正确, 但**不是唯一命中**） |
| 2026-08-29 00:19:25 | `7a65bea` | skill-doctor / skill-map **自身**入库并登记进配属注册表 `:365`-`:366`; 同批入库科研三件（见 F-1） |

**⇒ 准确口径**: 本批**不是**「规则立后首次执行」, 而是 **① 2026-08-08 之后的首次执行（间隔 34 天）② `7a65bea`（08-29）把两个工具自身入库并登记进配属注册表、以及 `docs/SKILL_ROUTING.md` 立法（08-29）之后的首次执行**。**逾期仍成立**（治理规则 2 要求「每次 neat 收尾时」跑, 而期间 08-29 skills 入库批与 09-06 / 09-07 的 neat 类收口均未见运行记录）, 但**起点是 08-08 而非「从未」**; 逾期时长 = **34 天**, 不是「约一个月」的规则立后起算（若按规则立日 08-03 起算则为 39 天, 两个口径都给, 由用户择一入台账措辞）。

### 总量对照（08-04 → 09-11）

| 项 | 08-04 首轮 | 09-11 复检 | 说明 |
|---|---|---|---|
| 仓库 `skills/` 顶层目录 | 10（+1 未扫） | **71** | **92 个 SKILL.md**（含捆绑包内子 skill） |
| `~/.codex/skills`（Loop A） | 35 active | **57 目录 / 56 件有 SKILL.md**（另 1 = `.system`） | **83 个 SKILL.md** |
| `~/.claude/skills`（Loop C） | 未单列 | **27 目录** | 三层分发的第二个靶 |
| skill-doctor 仓库根 | 两根合并报 47 error / 32 warn（初检）→ 27 / 32（fix-safe 后） | **50 error / 83 warn = 133 findings, 29 fixable** | 口径不同: 08-04 两根本合并, 本批逐根分报 |
| skill-doctor `~/.codex` | 同上（合并） | **37 error / 54 warn = 91 findings, 14 fixable** | |
| skill-doctor `~/.claude` | 未单列 | **20 error / 41 warn = 61 findings, 18 fixable** | |
| skill-map | 63 条目（去重后） | **202 skills / 91 duplicates / 103 edges / 59 unresolved** | 三根扫描; 仓库派发路径单独一轮 = 110 skills / 13 duplicates / 73 edges / 43 unresolved |

**「71 vs 57 不是漂移」（承开工卡要求入账; 08-04 报告 `:34` 已有同一结论的先例）**: 仓库 `skills/` = **source of truth**, 经 `scripts/graph/sync_skills.sh` 分往**两个靶**（Loop A 的 `~/.codex/skills` 与 Loop C 的 `~/.claude/skills`）, 且各靶只取自己 A 表 / C 表所列子集 ⇒ **两个安装区各自小于源是设计使然, 不是缺件**。同理 **92 vs 83 个 SKILL.md 不可直减比较**: `scientific-toolkit-skill` 一类是**捆绑包**（内含十余个子 skill, 各自带 SKILL.md）。一致性由 `docs_lint` 的 `[4]`（`sync_skills.sh --check`）与 `[5]` 机械判定, **该两项在 GB10 均为 0 fail**（09-11 实测 GB10 `docs_lint` = PASS / 0 fail / 8 warn, 8 条全为 `[2]` 时效类）。skill-map 报的 **91 条 duplicates 同理 = 设计使然**（08-04 报告 `:34` 已定性「均为设计使然…不视为缺陷」）。

### findings 分类（三份报告逐类, 原始 code 不加工）

| code | severity | 仓库 `skills/` | `~/.codex` | `~/.claude` | fixable |
|---|---|---|---|---|---|
| `COMPLETION_EVIDENCE_MISSING` | warning | 51 | 37 | 23 | 否（advisory, 永不自动修） |
| `FRONTMATTER_FIELD_ORDER` | warning | 32 | 17 | 18 | 否（advisory） |
| `OPENAI_METADATA_MISSING` | error | 29 | 14 | 18 | **是**（`--fix-safe` 可建 `agents/openai.yaml`; **本批未用**） |
| `OPENAI_POLICY_MISSING` | error | 16 | 19 | 0 | 否（fix-safe 不代写布尔值, 需逐个按 skill 语义判定） |
| `FRONTMATTER_MISSING` | error | 4 | 4 | 1 | 否 |
| `RESOURCE_LINK_MISSING` | error | 1 | 0 | 1 | 否 |

skill-map 侧: **edges 103 条**（skill↔skill 依赖; figma 家族内部互链与 `playwright-interactive → playwright` 承 08-04 结论不变; **指向弃用件 `verification-before-completion` 的边 = 0**）; **unresolved 59 条逐条核过 = 全部假阳**, 两类: ① 占位词（`cdn-cgi` 10 / `skill-name` 5 / `turn-credentials` 4 / `50-100` 3 / `api-v2`·`attack-detected`·`customer-id`·`kebab-name`·`my-bucket`·`new-page`·`new-path`·`old-page`·`problematic-path` 各 2 / `skill-name-here` 1）② **`paper-writing` 18 条 = 目录名误判**（真身是 `research-writing-skill/references/paper-writing/` 这个**参考目录**, 非 skill 引用）。**与 08-04 报告 `:38`「全部为文档占位符误报」同结论。**仓库派发路径单独一轮的 11 条仓库侧 unresolved 亦全为假阳（`compatible-mode`·`parse-file`·`install-plugin`·`kill-dead-code`·`proxy-health`·`responses-only`·`schema-suggestions` = CLI 子命令与 API 模式名, 非 skill）。

### F-1（HIGH, 影响论文线; **根因与 08-04 的定性相反**）— 4 件 skill 带 UTF-8 BOM, 而 `FRONTMATTER_MISSING` 是假阳

skill-doctor 报 `FRONTMATTER_MISSING` 的 4 件 = `algorithm-description` / `paper-review-check` / `paper-writing-zh` / `skills-best-practices`。**逐件字节层实测**: 四件的 frontmatter **都存在且闭合**（`---` … `---`, `name:` 与 `description:` 齐备）, 真正的问题是 **`---` 之前有 UTF-8 BOM `EF BB BF`** ⇒ skill-doctor 未以 `utf-8-sig` 解码, `startswith('---')` 于是失败, **误报为「缺 frontmatter」**。**故本轮 4 条 `FRONTMATTER_MISSING` error 全部是工具假阳, 真缺陷是 BOM。**

- **机械对照（双向排他）**: `~/.codex/skills` 下 56 件有 SKILL.md 的 skill 中, **带 BOM 的恰好是这 4 件**; 而这 4 件**恰好也是**唯一 4 件「已安装但不出现在 Codex 实际可装载 skill 清单里」的件。**反证已做**: 同批（`7a65bea`, 08-29）入库的 `neat-freak` / `code-cleanup-helper` / `skill-doctor` / `skill-map` **无 BOM 且均可装载**; 其余未出现在清单里的名字（`repo-audit` / `readme-audit` / `webapp-testing` / `code-review` / `generate-commit` / `memory-systems` / `multi-agent-patterns`）经实测**根本未安装进 `~/.codex/skills`**（属 Loop C 靶或仅存于仓库）⇒ 其缺席由「未安装」解释, 不构成反例。**故「BOM ⇔ 不可装载」在受检集合上双向成立**; 装载器源码未读, 该因果为**强相关推断而非源码证明**, 如实标注。
- **扩散面**: 仓库 `skills/` 的 92 个 SKILL.md 中**恰好 4 个带 BOM**（即这 4 件, 全在顶层, 捆绑包内 0 件）; 经 `sync_skills.sh` 扩散为 `~/.codex` 4 件 + `~/.claude` 1 件（`paper-review-check`, 因 C 表 `:19` 亦列该件）。**源在仓库 ⇒ 修一处即可, 但修 = 改 skill 文件, 本批禁做。**
- **为什么是 HIGH**: 这 4 件不是边角料——`AGENTS.md` 配属注册表把**四件全部登记给 Loop A（Codex CLI）**: `:347` `paper-review-check`（科研线: 投稿前攻击面自查/对抗审查, 审稿人视角五问）/ `:361` `paper-writing-zh`（中英文学术写作纪律）/ `:362` `algorithm-description`（代码→论文算法描述, **G(τ,ε) 方法节用**）/ `:384` `skills-best-practices`（治理线: 自定义 skill 规范, **治理规则 3 的依据件**）; `docs/SKILL_ROUTING.md`（立法件）`:10` 更把其中三件列为**论文线主装**, `:29` 裁定 `paper-review-check` 与 `paper-polish-and-audit` **分工并存**（过程审查用前者）, `:41` 钩链矩阵把 `paper-review-check` 列为 **Loop C 论文件审计派单**件。
- **与论文线的直接撞击**: 决策 21=D 之后论文线的下一站是 **T7**, 而 T7 两个 blocking 占位之一 = **Algorithm 1 伪代码未入稿**——`algorithm-description` 正是注册表为该用途指定的件（「伪代码/复杂度/变量对位」）, **它装不上**。另一件 `paper-review-check` 在库内有**已使用记录**（draft 内「审稿人视角五问注记（paper-review-check 一轮, 2026-08-30 夜, Loop D 自审）」）⇒ 08-30 那次很可能是**以文档方式读取**而非由装载器装载, 与「BOM 件不可装载」并不矛盾。
- **08-04 的定性已失效（本条最重要的部分）**: 08-04 报告 `:28` 把同类 4 条判为「`algorithm-description` 等**个人 skill** 无 frontmatter（**非社区包, 不处理**）」。当时它们确实只在个人安装区。但 **`7a65bea`（08-29）把三件科研 skill 入库为仓库 source of truth、列入 `sync_skills.sh` A 表 `:18`、登记进 `AGENTS.md` 配属注册表、并写进 `SKILL_ROUTING.md` 论文线主装**（`skills-best-practices` 于同日 `8899cff` 入库, 亦在 A 表 `:18`）⇒ **「个人 skill 故不处理」的前提在 08-29 当天即失效, 但无人复检**, 至本批已 **13 天**。**教训**: 一次「不处理」的裁定是**绑定当时归属状态**的; 归属变更（个人件 → 仓库件 → 注册表登记 → 立法件主装）必须触发复检, 否则旧裁定会变成静默债务。

### F-2（LOW-MEDIUM）— `repo-audit` 的资源引用指向不存在的文件

`skills/repo-audit/SKILL.md:116` 引用 `scripts/env_gpu-cluster.sh`, **该文件不存在**（仓库与 `~/.claude` 两份副本同一处失效; `~/.codex` 未安装该件故无第三份）。

**是否触发开工卡「停等点 4 的高危项」= 本批判定不触发**, 理由三条: ① `repo-audit` 在 `AGENTS.md:341` 登记给 **Loop C**, 且实测**未安装进 `~/.codex/skills`** ⇒ 不在 Loop A / 主线程的任何装载路径上 ② 本批与两个代理交付批均未装载它 ③ 失效点是该 skill **Mode B（repo audit）内部的一个 helper 引用**, 不是派发入口。**故按 finding 入账, 归 A19, 不停批、不自修。**（若用户判定应视为高危, 本批已停在只入账状态, 未做任何修复动作。）

### F-3（LOW）— 弃用件引用: A19 第 1 项复核成立, 且范围比台账所记更窄

- 全库扫描**带 DEPRECATED 标记的 skill 只有 1 件** = `verification-before-completion`（`SKILL.md:6`: 「DEPRECATED (2026-08-26): 本 skill 已被 `verify-before-done` 取代…按治理规则 4 只标记不删除, 目录保留审计痕迹」）。`figma-generate-design` 的命中是假阳（其正文含「Remove deprecated sections」字样）。
- **派发路径引用共 4 处, 其中 3 处正确、1 处是缺陷**: `docs/SKILL_ROUTING.md:28`（冗余裁决表**正确**记为「已废」）✓ / `AGENTS.md:311`（注册表行**正确**标注 DEPRECATED）✓ / `AGENTS.md:329`（`verify-before-done` 行**正确**记「取代 verification-before-completion」）✓ / **`scripts/graph/loop_a_exec_constraints.md:118` = 缺陷** —— 该件是**派发给 Loop A 的现役约束件**, 其 skill 触发表仍把 `verification-before-completion` 列为应装件且**未提 `verify-before-done`** ⇒ **A19 第 1 项成立, 且是该族唯一活体缺陷**。
- **方法论附注（对 A19 的扫描域有约束力）**: skill-map 的 edges 中指向该弃用件的边 = **0**, 因为该引用住在**仓库文件**而非 skill 文件里 ⇒ **只跑 skill-map（扫描根 = 三个 skill 目录）扫不到它**, 必须把仓库派发路径文件（`scripts/graph/*.md`·`templates/*.md`·`docs/SKILL_ROUTING.md`·`AGENTS.md`）一并纳入扫描域。本批即因此另跑一轮, 才机械坐实该条。
- **附带一处日期不一致（只记不改）**: 弃用标记在 `SKILL.md:6` 写 **2026-08-26**, 而 `AGENTS.md:311` 写 **DEPRECATED 2026-08-25** ⇒ 差 1 天, 属 metadata 一致性缺口, 归 A19。

### 本轮结论与不修清单

- **零修复自证**: 未使用 `--fix` / `--fix-safe`（三份 JSON `fixes = []`、`fix_errors = 0`）; 未改任何 skill 文件; 未改 `sync_skills.sh`; 未改 `AGENTS.md` 与 `docs/SKILL_ROUTING.md`（后者是立法件, 修改需用户批）。
- **未动 `~/.codex` 任何文件**（决策 15=A 仍生效）: 两个工具的运行只读, JSON 输出落**仓外临时目录**并已清理, 未在 `~/.codex` 下产生任何文件。
- **修复归属**: F-1 / F-2 / F-3 全部归 **A19**（须等 A4/A5 验收通过后另批派发 Loop A）。**F-1 建议提级**——它影响的是决策 21=D 之后论文线的第一站（T7 的 Algorithm 1 占位）; 是否把「给 4 件去 BOM」从 A19 中拆出提前做, **属用户裁定, 主线程不自行提前**。
- **与 08-04 首轮的连续性**: 首轮所列「本机安装区 19 个 POLICY 缺失项列入低优清单」在本轮为 `~/.codex` **19 条 `OPENAI_POLICY_MISSING`** ⇒ **数量逐字未变, 34 天零处置**, 该低优清单仍未消化（本轮不提升其优先级, 只记事实）。
