# 决策 5 的三处「规格冲突」按全仓证据权重定性 —— 含对本会话此前一处结论的更正

> 状态: 活跃 | 更新: 2026-09-24 | 取代/被取代: **更正** `2026-09-24_phase1a_s7_receipt_contract_gap.md` §3.3 对 `H3a` 命名冲突的定性（该处把两侧写成「两份权威件各执一名、无从判断谁对」；本件用全仓证据权重证明**一侧是孤立离群值**）
> 用途: 把决策 5 从「三处需要用户在两个权威之间做判断的冲突」降级为「一处解释选择 + 一处范围决定 + 一处纯命名对齐」。三项都给出全仓证据权重，**不代用户裁定**。
> 边界: 全程只读。未改任何代码、文档或判据一个字节；未改冻结判据/阈值/oracle；未解 `DATA_NO_GO`；未启动 Phase 1a/2。

## 1 方法与一处必须声明的口径

`git grep` 全仓（HEAD）后，**先剔除本会话自己产出的引用**再计权重——否则这几轮写的证据件与台账会把两侧计数同时抬高，形成自证。剔除范围：`docs/experiments/2026-09-24_*.md`（本会话 7 件）、`logs/graph/dispatch_log.md`、`memory/THREADS.md`。剩下的才算**独立证据**。

## 2 冲突三（`H3a` 命名）：孤立离群值是**合同侧**，不是 §7 侧 —— 更正此前定性

### 2.1 独立证据计数

| 名称 | 独立出现处 | 位置 |
|---|---|---|
| **`uid_any_harm` 系**（含 `H3a_uid_any_harm` 与指标名 `uid_any_harm_*`） | **6 处文档 + 3 个代码/测试文件** | 预注册件 §2 `:28`（H3a 假设陈述）· §6.2 `:109`（指标定义）· §6.3 `:117`（Holm 家族）· §7 `:149`（收据 JSON）· 计划件 §Phase 2 `:279`（指标）· `paper/method_theory_materials_v1.md:295`（理论件）· **`research/phase2_rule_gate_replay.py:392-399`（实际产出指标）** · **`research/paper_result_views.py:76-81`（Table 2 / Figure 4 接口消费）** · **`tests/test_phase2_rule_gate_replay.py:214-236`（断言这些名字）** |
| **`H3a_cluster_any_harm`** | **仅 4 处 / 2 个文件** | `research/phase1a_data_contract.py:106`（`REQUIRED_HOLM_FAMILIES`）· 同文件 `:950`（`one_sided_p_value_methods`）· `tests/test_phase1a_data_contract.py:202` 与 `:212`（夹具；其中 `:197` 直接引用 `contract.REQUIRED_HOLM_FAMILIES`，故属**回声**而非独立第二来源） |

⇒ **离群值是 Phase 1a 数据合同里的那一个常量**，不是 §7。整个科学层（预注册件四处 + 计划件 + 理论件）与**已实现的 Phase 2 指标管线及其测试**都统一用 `uid_any_harm`；只有 Phase 1a 合同的两处常量（及其夹具回声）用 `cluster_any_harm`。

### 2.2 两者语义相同，故这是**纯命名**问题，不是判据问题

合同自己强制 `cluster_unit` **严格等于** `lineage_uid`（`phase1a_data_contract.py:918`）。既然聚类单元被钉死为 lineage UID，「cluster」与「UID」在本合同语境下**指同一个单位** ⇒ `H3a_cluster_any_harm` 与 `H3a_uid_any_harm` 描述**同一个统计量**（任一有害接受事件，按 UID 聚合，单侧 Clopper–Pearson 上界 + `exact_mcnemar`）。

**这一点很关键**：把合同常量对齐到 `H3a_uid_any_harm` 属**命名对齐**，不改任何阈值、oracle、统计量、家族结构或判定逻辑 ⇒ 与「改冻结判据」不是一类事。但它确实改的是 `REQUIRED_HOLM_FAMILIES`（`:99-109`）与 `one_sided_p_value_methods` 的键（`:946-953`），且 `REQUIRED_MDE_CONTRASTS`（`:110-114`）由前者**派生**，故三处会联动；**仍须用户显式授权 + 修者不自验 + 补正反例**，本件不实施。

### 2.3 对本会话此前定性的更正（如实记）

`2026-09-24_phase1a_s7_receipt_contract_gap.md` §3.3 与 §5 写的是「两份权威件对同一个确认性假设取了不同名字」「改合同常量 = 触碰冻结判据，改预注册件 = 改 `DRAFT_NOT_FROZEN` 合同，两条路都不是 Loop D 能自行选的」，并把两侧呈现为**对等**选项。

**该定性偏颇，本件更正**：当时只比对了「§7 vs 合同」两个点，未做全仓权重扫描，因而漏掉了预注册件自己的 §2/§6.2/§6.3、计划件 §Phase 2、理论件，以及**已落地的 Phase 2 指标名与测试**。补齐后证据是**一边倒**的。更正不改变「须用户授权」的结论，但**改变了建议方向**：不是「二选一的对等抉择」，而是「合同侧常量为孤立离群值，建议向 `uid_any_harm` 对齐；若反向对齐则需同时改 6 处文档 + 3 个代码/测试文件，代价与风险都大得多」。

## 3 冲突二（`threshold_selection`）：不是同一条断言，且 §6.3 的规则**全仓零实现**

### 3.1 两个 token 编码的是不同层面的事

| 来源 | 值 | 编码的内容 |
|---|---|---|
| 合同 `:940` + 夹具 `:195` | `proposal_dev_only` | **范围**：阈值只在 proposal/dev 上选（对应 §6.3 `:118` 末句「gate/sealed 不参与阈值选择」） |
| 预注册件 §7 `:144` | `proposal_dev_max_coverage_under_risk_then_macro_f1_then_conservative` | **范围 + 规则 + 两级并列决胜**：proposal_dev / 风险不高于 ρ_max 时覆盖最大 / 并列先取 macro-F1 高者 / 再取更保守阈值 |

§7 的长串**逐段对应** §6.3 `:118` 的规则原文，是规则的忠实编码；合同的短串**只编码范围**。⇒ **两者不是互相矛盾的同一断言，而是宽窄不同的两条断言**，合同那条**弱于**预注册那条。

### 3.2 §6.3 的选择规则在代码里**没有任何实现**（机械证明）

```text
git grep -i -E <pattern> HEAD，只计 .py 命中：
  max_coverage_under_risk   py-hits = 0
  max_coverage              py-hits = 0
  then_macro_f1             py-hits = 0
  conservative              py-hits = 6  -> 全部无关：
      research/paper_d3_stage_b_closeout.py:168（一处 "conservative parser" 注释）
      skills/office-academic-skill/.../inventory.py:481/507/580（PPT 字号默认值）
```

⇒ 「风险不高于 ρ_max 时覆盖最大、并列先取 macro-F1、再取更保守阈值」这条**预注册规则目前不由任何代码执行或校验**。合同只校验「范围 = `proposal_dev_only`」这一个 token。

**这不必然是缺陷**：规则可能本就打算由 Phase 1a 执行者（人工或尚未编写的选阈脚本）在 dev 上应用，合同只负责记录「选阈发生在正确的层」。但它意味着一个**须由用户明确的范围决定**：

- 选项 A：**不要求机器强制**。则 §7 那个长 token 无处安放（合同字段只接受 `proposal_dev_only`），应把「规则」与「范围」拆成两个字段，规则字段仅作记录、由人工复核。
- 选项 B：**要求机器强制**。则需新增选阈实现 + 校验，属新功能与新判据面，工作量与授权都更大。

本件不选，只把两条路的代价写清。

## 4 冲突一（`status`）：证据支持「两份工件」，而非「token 写错」

| 值 | 独立出现处 |
|---|---|
| `FROZEN_BY_HUMAN` | **仅 1 处**：预注册件 §7 `:127` |
| `"approved"` | 合同 `:912`（`if analysis.get("status") != "approved"`）+ 夹具 `:182` |

两者描述的是**不同工件的不同生命周期状态**：一份「人工冻结收据」的状态自然是 `FROZEN_BY_HUMAN`；一份「已批准的分析计划」的状态自然是 `approved`。这不是笔误，而是**两类文档各自的状态词表**。

与上一轮实测合并看——§7 缺 `analysis_plan` 的 **10 个必需键**、且填满全部 `UNSET` 后仍剩 **14 个 schema 级错误**——**三条独立证据同向指向决策 5 = 两份工件**：

1. 键集在 10 个必需键上完全不相交（上轮实测）；
2. `status` 词表分属两种生命周期（本节）；
3. `threshold_selection` 宽窄不同、编码不同层面的断言（§3.1）。

⇒ 建议按「两份工件」裁定：§7 保持为**人工冻结收据**（记批准人/时间/各 hash/各 δ），另建 `analysis_plan.json` 作为**包内角色件**（18 个必需键，字段清单可由合同 `:909-977` 机械导出，见 `2026-09-24_phase1a_supplement_contract_role_gap.md` §5）。**裁定权仍在用户**，本件只给证据权重。

## 5 三项的净结果：决策 5 的可裁定面已收窄

| 原表述（本会话上一轮） | 本件按全仓证据权重后的表述 | 尚需用户做什么 |
|---|---|---|
| `H3a` 命名：两份权威件各执一名，对等抉择 | **合同侧常量为孤立离群值**（4 处 / 2 文件，其中 2 处是夹具回声）；科学层 6 处 + 实现与测试统一用 `uid_any_harm`；且因 `cluster_unit == lineage_uid`，两名**语义相同** | 授权一次**纯命名对齐**（合同 `:106`/`:950` 及其夹具），不改任何判据；仍须修者不自验 + 正反例 |
| `threshold_selection`：两边都写了值但不是同一个 | 两者是**宽窄不同的两条断言**，合同那条弱于预注册；且 §6.3 规则**全仓零实现** | 在「不机器强制（拆成范围 + 规则两字段）」与「机器强制（新增实现与判据面）」之间择一 |
| `status`：token 冲突 | 两个词表分属**两类工件的生命周期**，是「两份工件」的**证据**而非缺陷 | 确认决策 5 = 两份工件（三条独立证据同向） |

## 6 建议并入既有「文档更正批」

该批目前含 6 项（角色数 8→9、命令块解释器、计划件 §Phase 2、`minimum_uid` fail-open 处置、`DATA_NO_GO` 报告复核注记、`schema` 候选裁定）。本件新增 3 项，建议同批处理以免多次触碰同一批权威件：

7. **`H3a` 命名对齐**（合同侧，纯命名，须授权 + 修者不自验 + 正反例）；
8. **`threshold_selection` 的范围决定**（A/B 二择，见 §3.2）；
9. **决策 5 确认为两份工件后**，给预注册件 §7 追加 append-only 注记，写明「§7 为人工冻结收据，`analysis_plan.json` 为另一工件，其 18 个必需键以合同 `:909-977` 为准」。

## 7 复现

```bash
# 权重扫描（剔除本会话自产引用后再计数）
git grep -n -E 'H3a_cluster_any_harm|H3a_uid_any_harm' HEAD
git grep -n -i -E 'uid.any.harm' HEAD
git grep -n -E 'proposal_dev_only|proposal_dev_max_coverage_under_risk' HEAD
git grep -n -E 'FROZEN_BY_HUMAN' HEAD
git grep -n -i -E 'max_coverage_under_risk|max_coverage|then_macro_f1' HEAD -- '*.py'
```

判读要点：计数时**必须剔除** `docs/experiments/2026-09-24_*.md`、`logs/graph/dispatch_log.md`、`memory/THREADS.md`，否则本会话自产引用会同时抬高两侧、形成自证；另需识别**夹具回声**（`tests/test_phase1a_data_contract.py:197` 直接引用 `contract.REQUIRED_HOLM_FAMILIES`，不构成独立第二来源）。

## 8 红线自查

- 未改任何代码、文档或判据一个字节；§2.2 的命名对齐、§3.2 的两条选项、§6 的三项**一律未实施**。
- 未改冻结判据/阈值/oracle/冻结 hash；未解 `DATA_NO_GO`；未启动 Phase 1a/2；未批准任何数值、未填任何 `UNSET`；未授权训练或端点。
- 零端点、零模型调用、零 canary、零 judge、零起 run；本件全部证据来自 `git grep` 静态检索，未运行任何测试或实验。
- **本件更正了自己上一轮的一处偏颇定性（§2.3），未回改原件**——原件 §3.3/§5 文字保持原样作为轨迹，更正只在本件与台账登记（append-only 纪律）。
- 未动 `docs/33`、`docs/34`；未 pull production（仍 `e5ab809` + 5 脏件）；未重启 daemon `1816933` 与 `:5050` `1868428`；未改 crontab；未重置 Loop B；四件用户资产零触碰；逐路径 add、无 `-A`/`--amend`/`--no-verify`。
