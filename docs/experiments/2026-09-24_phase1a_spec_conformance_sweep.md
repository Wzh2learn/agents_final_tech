# Phase 1a/2 人工规格 vs 机器合同：完整一致性扫描（19 项，15 符 / 3 已有偏差 / 1 新发现）

> 状态: 活跃 | 更新: 2026-09-24 | 取代/被取代: 不取代任何既有报告；为前三件缺口件补上**完整边界**，使「文档更正批」可被一次性界定范围
> 用途: 前三件（§7 收据 schema、补充合同角色数、执行手册命令）是**逐个撞见**的偏差。本件把同一类检查**做完**：对人工规格里每一条机器可核验的主张逐条比对代码，给出「符合 / 偏差」的完整清单，并顺带查出一处**新的、此前无人记录的 fail-open 路径**。
> 边界: 全程只读。未改任何文档或代码一个字节；未改冻结判据；未解 `DATA_NO_GO`；未启动 Phase 1a/2；未批准任何数值；未读任何私有数据。

## 1 为什么要「扫完」而不是继续逐个撞

上一轮我建议把三处偏差合并成**一个文档更正批**。但那建议有个前提我没验：**偏差总数未知**。若只把已撞见的三处交给用户授权，很可能授权后仍有遗漏，导致同一批权威件被反复触碰。本件因此把扫描做完，让该批的范围**闭合可数**。

## 2 方法

- 两侧都**机械提取**，不用人工誊写清单：代码侧直接从模块读常量（`REQUIRED_ROLES`、`MANIFEST_ROW_FIELDS`、`LABEL_FIELDS`、`FEATURE_FIELDS`、`REQUIRED_USES`、`PARTITIONS`、`_new_gates()`、`L.BASELINES`、`L.CASE_FIELDS`、`L.CONFIG_FIELDS`、`L.MANUAL_REVIEW_FIELDS`、`L.POLICY_FIELDS`、`P.ARMS`、`P.ALLOWED_LAYERS`）；文档侧用正则从指定小节抽取字段名与计数词。
- 「某处不存在某检查」这类**否定结论**一律用**出现次数为 0** 的机械证明，不靠「我读了没看到」。
- 退出码、门数等以**源码实际返回语句**为准（如 `return 0 if report["status"] == READY else 2`）。

## 3 一致性总表（19 项）

### 3.1 符合（15 项）——这些**不要改**

| # | 人工规格主张 | 出处 | 代码事实 | 判定 |
|---|---|---|---|---|
| 1 | manifest lineage row 严格含 8 字段 | `paper/dataset_protocol_v1.md` §6.1 (:120-131) | `MANIFEST_ROW_FIELDS` = 8，逐名相同 | **符合** |
| 2 | label ledger 每行严格含 8 字段 | 同上 §6.2 (:139-151) | `LABEL_FIELDS` = 8，逐名相同 | **符合** |
| 3 | JSONL view 只接受 10 个字段 | `DATA_NO_GO` 报告 learnability 节 | `L.CASE_FIELDS` = 10，**集合完全相同** | **符合** |
| 4 | 「all seven mechanical gates」 | `DATA_NO_GO` 报告 acceptance 节 | `_new_gates()` = 7 门 | **符合** |
| 5 | `DATA_NO_GO` exit 2 / `READY…` exit 0 | 同上 (:68 附近) | `return 0 if report["status"] == READY else 2` | **符合** |
| 6 | 五臂 `always_skip`/`deterministic_matcher`/`lexical_fuzzy`/`confidence_only`/`simple_classifier` | 同上 | `L.BASELINES` = 5，逐名相同 | **符合** |
| 7 | 只有四个决策 | 同上 | 四者**均被实际产出**：`PILOT_ONLY` :980、`LEARNABILITY_SIGNAL` :1003、`SIMPLE_SUFFICIENT` :1010、`NO_CLEAR_SIGNAL` :1019 | **符合** |
| 8 | licence 需四项 permitted uses | 同上 补充合同表 | `REQUIRED_USES` = `{training, tuning, evaluation, rule_acceptance}` | **符合** |
| 9 | 须绑定 5 个 partition，前四个非空 | 同上 | `PARTITIONS` = 5、`REQUIRED_PARTITIONS` = 4 | **符合** |
| 10 | 三个独立人工复核身份 | 同上 | `L.MANUAL_REVIEW_FIELDS` = 3，语义逐一对应 | **符合** |
| 11 | 预注册 config 固定 lexical threshold / confidence policy / classifier / bootstrap / decision policy | 同上 | `L.CONFIG_FIELDS` = 6（上述 5 + `contract_version`） | **符合** |
| 12 | `confidence_manifest` 的 `missing_policy=unmeasurable` | 同上 补充合同表 | :889-890 `if confidence.get("missing_policy") != "unmeasurable"` → `invalid_missing_policy` | **符合** |
| 13 | Phase 2 七臂 | 计划 §Phase 2 (:277) | `P.ARMS` = 7，逐一对应 | **符合** |
| 14 | Phase 2 输入只接受 `proposal_train` 与 `gate_validation` | 计划 §Phase 2 (:285) | `P.ALLOWED_LAYERS` = `{proposal_train, gate_validation}`；越界即 :149 `forbidden or unknown data layer` | **符合** |
| 15 | Phase 2 候选**只能含** id/source uid/synonym/target/confidence，预存 `gain`/`collateral`/`accepted`/`split` **都会失败** | 计划 §Phase 2 (:285) | `_exact_keys(raw, {"candidate_id","source_uid","synonym","target","confidence"}, …)` **:176-181** | **符合** |

### 3.2 已记录的偏差（3 项，见前三件）

| # | 偏差 | 证据件 |
|---|---|---|
| 16 | 报告写「eight required roles」，`REQUIRED_ROLES` 要 **9**（漏 `learnability_feature_ledger`）；照报告交付实测 `DATA_NO_GO` | `2026-09-24_phase1a_supplement_contract_role_gap.md` |
| 17 | 报告 `analysis_plan` 行：18 个必需键中**逐字命名 3、仅散文 10、完全缺失 5**；§7 收据与合同 10 个必需键不相交，填满仍 14 个 schema 级错误 | 同件 + `2026-09-24_phase1a_s7_receipt_contract_gap.md` |
| 18 | 执行手册解释器/环境变量错误：10 行命令 **6 行实测即败**（5×rc=127 `.venv` 不存在、1×rc=1 裸 `python3` 无 pytest） | `2026-09-24_phase1a_phase2_runbook_command_defects.md` |

### 3.3 新发现（1 项）：两份工件各存一份「最低 UID 阈值」，**彼此无任何一致性约束**

| # | 问题 | 判定 |
|---|---|---|
| 19 | `analysis_plan.minimum_uid_by_action` / `minimum_uid_by_role_family`（数据合同侧）与 `decision_policy.min_dev_uids_by_action` / `min_dev_uids_by_family` / `min_dev_uids`（可学性 config 侧）是**同一语义量的两份副本**，键名不同、分属两份工件，**无相等性校验、无交叉引用** | **新发现，需裁定** |

## 4 第 19 项的机械证明与后果（本件最重要的部分）

### 4.1 两侧各自做什么

**数据合同侧只做形状检查，不做任何决策**：

```text
:956  minimums = analysis.get("minimum_uid_by_role_family")
:961  _fail(gates, "analysis_plan", "invalid_minimum_uid_by_role_family")   # 仅要求 dict 非空、值 int>=2
:962  action_minimums = analysis.get("minimum_uid_by_action")
:968  _fail(gates, "analysis_plan", "invalid_minimum_uid_by_action")        # 仅要求键集恰为 {map_to,skip,hold}、值 int>=2
```

**可学性 config 侧才是真正驱动决策的那一份**：

```text
:243-244  min_dev_uids 必须为 int 且 >= 2
:245-247  min_dev_uids_by_action 必须定义 skip / hold / map_to
:250      min_dev_uids_by_family
:944-945  action_minimums = policy["min_dev_uids_by_action"]
          family_minimums = policy["min_dev_uids_by_family"]
:949      total < int(policy["min_dev_uids"])  -> 记入 shortfalls
:956-977  逐 action / 逐 family 比对 observed vs required -> shortfalls
:978-984  if shortfalls: return {"status": "PILOT_ONLY",
                                 "reason": "insufficient_or_unregistered_dev_uid_support",
                                 "training_authorized": False}
```

⇒ **`PILOT_ONLY` 由 config 侧那份阈值决定，与 `analysis_plan` 里被批准并绑定 hash 的那份无关。**

### 4.2 「无交叉校验」的机械证明（出现次数为 0）

```text
可学性 runner 中：
  "minimum_uid_by_action"      出现 0 次
  "minimum_uid_by_role_family" 出现 0 次
  "analysis_plan"              出现 1 次 —— 且该处 (:99) 只是 PRECHECK_GATES 的门名列表，不读其内容
数据合同中：
  "min_dev_uids"               出现 0 次
  "min_dev_uids_by_action"     出现 0 次
  "min_dev_uids_by_family"     出现 0 次
  "decision_policy"            出现 0 次
```

runner 对 precheck 报告的校验只有三条（:277-291）：`status == READY_FOR_INDEPENDENT_ACCEPTANCE`、门集合恰为 `PRECHECK_GATES`、无失败门。**它从不读取 `analysis_plan` 的任何数值。**

接收回执确实绑定三份哈希（:307-309 `package_manifest_sha256` / `precheck_report_sha256` / `preregistered_config_sha256`）⇒ **两份工件各自都被 hash 绑定、各自都需批准，但没有任何一处要求这两份阈值相等。**

### 4.3 后果：预注册的功效下限存在一条 fail-open 路径

预注册件 §6.3 要求「`minimum_uid_by_role_family` 与 MDE 必须在揭封前由人批准并绑定 hash」。该要求对 `analysis_plan` **确实已满足**。但**真正生效**的是另一份工件里的另一个键，且无相等约束。于是：

- 人可以批准 `analysis_plan.minimum_uid_by_action = {map_to: 50, skip: 50, hold: 50}` 并绑定 hash；
- 同时 config 写 `min_dev_uids_by_action = {map_to: 2, skip: 2, hold: 2}`（**满足 :245-247 的全部校验**）；
- 探针在 dev 只有 2 个 UID/动作时**不会**返回 `PILOT_ONLY`，而可能返回 `LEARNABILITY_SIGNAL`。

⇒ **被批准的功效下限在「本该执行它的那一步」被静默绕过。** 两份工件都通过了各自的门，没有任何一处会报错。这与姊妹件里「`minimum_uid_by_action >= 2` 是健全性下限而非功效下限」是同一个风险的**两个独立入口**：那一处是「值填小了合同也放行」，这一处是「值填对了也不生效」。

同时它直接影响 `2026-09-24_phase1a_power_mde_sensitivity_grid.md` 的可用性：该件算出的 K（δ=0.02 时 39..343）是用户要批准进 `analysis_plan` 的值；**除非 config 侧同名阈值被设为同样的数，否则批准不产生任何强制力。**

### 4.4 三条可选处置（均属判据面，须用户显式授权，本件不代判）

1. **加交叉一致性校验**（推荐方向）：让可学性 runner 在读取 precheck 报告时，一并读取 `analysis_plan` 的两个 minimum 键并断言与 config 侧相等，不等即 fail-closed。改动面小（runner 已在校验 precheck 报告），但**改了守卫逻辑** ⇒ 须授权 + 修者不自验 + 补一对正反例（相等时通过、不等时必须失败）。
2. **只补文档**：在两份文档里明写「config 侧三个 `min_dev_uids*` 必须与 `analysis_plan` 侧两个 `minimum_uid_*` 取同值，且由人工在批准时逐项核对」。**零代码改动**，但把一致性责任留给人，仍可能静默失配。
3. **合并为单一信源**：让 config 不再自带这三个键，改由 runner 从已验收的 `analysis_plan` 读取。**最彻底**，但改动面最大，且会改变 config 的字段集（`L.CONFIG_FIELDS`/`POLICY_FIELDS`）与既有测试。

## 5 一处必须如实报告的「差点误报」

第 15 项（Phase 2 候选字段泄漏守卫）**一度看起来是缺失的**：按被禁字段名 grep（`gain`/`collateral`/`accepted`/`split`）在候选校验区**零命中**，据此很容易得出「文档承诺的泄漏守卫未实现」的结论。

实际读源码后发现守卫**存在且严格**：`_exact_keys(raw, {"candidate_id","source_uid","synonym","target","confidence"}, …)` 位于 **:176-181**，只是该调用**跨多行**、字段集写在单独一行，故按名字 grep 抓不到。

⇒ 教训已入账：**否定结论不能只靠关键词 grep**。本件因此把所有否定结论改为「机械抽取集合后比对」或「出现次数为 0 且已人工读过相关区块」两种口径，第 15 项即属后者的反面教材。若无这一步，本件会多出一条**假缺陷**并误导更正批。

## 6 更正批的闭合范围（据本件可一次性界定）

扫描已闭合 ⇒ 建议的**单一文档更正批**范围如下，共 **4 项**，其中 3 项纯文档、1 项需先裁定处置方向：

| 项 | 目标文件 | 动作 | 是否需裁定 |
|---|---|---|---|
| A | `docs/experiments/2026-09-23_phase1a_data_no_go.md` | 末尾**追加**更正段：必需角色 9 而非 8 + `learnability_feature_ledger` 九条约束 + `analysis_plan` 的 18 个逐字键名与 5 处精确 token | 否（纯更正） |
| B | 同上 | 同段内追加：命令块解释器与环境变量更正（`.venv`→`venv`、worktree 内用绝对路径、pytest 不用裸 `python3`、删 `PYTHONPATH=src`、`PYTHONPATH=.` 只留给 `paper_result_views.py`），并注明 rc=2 属正确行为勿改 | 否（纯更正） |
| C | `docs/archive/2026-10-20_entry_consolidation/2026-09-22-paper-research-next-phase.md` §Phase 2 命令块 | 同 B 的解释器更正 | 需授权：该件是 `LC-RESEARCH-001` 的 `owned_paths` |
| D | 第 19 项 fail-open 路径 | 先在 §4.4 三条处置中择一，再落地 | **需裁定** |

§7 收据与 `analysis_plan` 是「一份还是两份」（决策 5）与 `H3a_uid_any_harm` vs `H3a_cluster_any_harm` 的命名权威，仍须先裁，A 项的措辞依赖其结果 ⇒ 建议 A 与决策 5 同批处理。

## 7 复现与取证

| 文件（GB10 `/tmp`，仓外，不 commit） | sha256 |
|---|---|
| `dump_consts.py` | `7c58e9a0ececf15e7f4e9ed814ed11a2e23f152d51286159b2e77435346332bb` |
| `dump_consts2.py` | `a7c00cc22db45b7499c5b68c1b1ac1e918e25b6fd02a786a3db024a906c58c48` |
| `dump_consts3.py` | `85912b7ea69a1ea151362dc7eb69e160562284a1d2f99fe421e603e89f7595d6` |
| `dump_consts4.py` | `fc4999e8759efe9178cd42d2d3fdf6def8850b5ce606e9872dbb0bf0a10ca6b7` |
| `crosscheck.py` | `afcbb24c8a775baff82430110ec06696c712323337e45c658dc020415fe45915` |

全部为**静态读取与集合比对**：零端点、零模型调用、零 canary、零 judge、零起 run、零私有数据读取；未运行任何实验，未生成任何数值结果。`/tmp` 非持久，故全部常量值、行号与出现次数已逐字抄入本件。

## 8 红线自查

未改任何文档或代码一个字节 · 未改冻结判据/阈值/oracle/冻结 hash · 未解 `DATA_NO_GO` · 未启动 Phase 1a/2 · 未批准任何数值、未填任何 `UNSET` · 未授权训练或端点 · 未派发任何 Loop A/B/C 卡 · 未与 `LC-RESEARCH-001` 的 `owned_paths` 冲突（正因如此 C 项列为待授权而非自行改）· 未动 `docs/33`、`docs/34` · 未 pull production（仍 `e5ab809` + 5 脏件）· 未重启 daemon `1816933` 与 `:5050` `1868428` · 未改 crontab · 四件用户资产零触碰 · 逐路径 add、无 `-A`/`--amend`/`--no-verify`。
