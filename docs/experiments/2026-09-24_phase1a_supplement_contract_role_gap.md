# Phase 1a 数据补充合同的角色缺口：报告写「八角色」，机器合同要九角色（实测 fail-closed）

> 状态: 活跃 | 更新: 2026-09-24 | 取代/被取代: 不取代 `DATA_NO_GO` 报告；**指出其 “Executable supplement contract” 一节需要 append-only 更正**（本件不改该报告一个字节）
> 用途: 数据补充是解锁整条主线的**唯一外部依赖**。本件实测「数据 owner 严格照 `DATA_NO_GO` 报告交付」会发生什么，以免对方白跑一轮。
> 边界: 全程只读。**未改 `DATA_NO_GO` 报告、未改预注册件、未改 `phase1a_data_contract.py`**；未解 `DATA_NO_GO`；未批准任何数值；未填任何 `UNSET`；未启动 Phase 1a/2。更正措辞只是**建议**，需用户授权后才落。

## 1 为什么查这件

`docs/experiments/2026-09-23_phase1a_data_no_go.md` 的 “Executable supplement contract” 是**数据 owner 唯一会读的人工规格**。上一轮已实测预注册件 §7 收据与机器合同不相容（见 `2026-09-24_phase1a_s7_receipt_contract_gap.md`：原样 18 个错误码、填满仍 14 个）。本件用同一方法查另一份人工规格：**照报告交付，机器合同收不收？**

## 2 方法

- 驱动**真实校验器** `research/phase1a_data_contract.py::validate_package`，不重实现判据；合成包由 `tests/test_phase1a_data_contract.py::package` fixture 构建。
- 角色清单与 `analysis_plan` 必需键**全部由脚本从文件机械推导**，不用人工誊写的清单：`REQUIRED_ROLES` 直接从模块读；必需键由正则抽取校验块内 `analysis.get("...")` 与 `"..." in analysis`，**并补上经循环变量读取的三键**（`for key in ("significance_level","target_power","risk_limit")`，:920-921），再减去「出现即失败」的遗留歧义键（`alpha`/`power`/`noninferiority_margin` 单数，:910）。
- 报告侧的角色名同样用正则从 “Executable supplement contract” 一节抽取，与 `REQUIRED_ROLES` 求交，避免主观判断「算不算提到」。
- `analysis_plan` 行的散文覆盖判定：对每个「我认为散文描述了这个键」的映射，**脚本断言该短语确实出现在行内**，映射不成立即抛错。

## 3 发现一：报告写「八角色」，合同要九角色（已实测 fail-closed）

报告原文：“**The eight required roles are:**”，其表格列出 `source_tables` / `schema` / `injection_map` / `label_ledger` / `licence_record` / `confidence_manifest` / `analysis_plan` / `parser_contract_receipt` = **8 个**。

代码 `REQUIRED_ROLES`（:29-39）= **9 个**，多出的一个是 **`learnability_feature_ledger`**。机械比对结果：

```text
code REQUIRED_ROLES                    : 9
roles named in supplement contract     : 8
REQUIRED BY CODE BUT ABSENT FROM REPORT: ['learnability_feature_ledger']
named in report but not required       : []
```

**实测后果**（把该角色从原本有效的合成包中移除，其余 8 角色与全部哈希绑定保持不变）：

```text
BASELINE (9 roles)      -> READY_FOR_INDEPENDENT_ACCEPTANCE, 7 门全 PASS
交付报告所列 8 角色      -> DATA_NO_GO
  artifact_integrity    -> FAIL
    {"code": "missing_required_role", "role": "learnability_feature_ledger"}
    {"code": "missing_or_mismatched_binding"}
  其余 6 门              -> PASS
meta = {'phase': 'precheck', 'endpoint_calls': 0, 'socket_attempts': 0,
        'contract_version': 'phase1a-data-package-v2'}
```

⇒ **数据 owner 严格照报告交付，到货即 `DATA_NO_GO`**，且失败落在 `artifact_integrity` 门，与数据质量无关，纯属规格漏项。

### 3.1 已排除的替代解释（重要，避免误报缺陷）

一个自然的辩解是：`learnability_feature_ledger` 也许由 Phase 1a **自己生成**，所以不该出现在「owner 需交付」的清单里。实测排除：

- `research/phase1a_learnability_baselines.py` 只 **import** `FEATURE_FIELDS` 与 `FEATURE_LEDGER_VERSION`（:27-28、:36-37），其 `_load_feature_ledger()`（:538 起）做的是 `path.read_bytes()` + 逐字节 `bytes`/`sha256` 校验 + 绑定缺失即 `raise`，是**消费者不是生产者**。
- 全仓 `.py` 搜索 `FEATURE_LEDGER_VERSION|learnability_feature_ledger`，命中仅三类文件：`phase1a_data_contract.py`（要求并校验它）、`phase1a_learnability_baselines.py`（读取它）、两个测试文件（合成 fixture）。**仓内不存在任何生成器。**

⇒ 它是**必须由外部提供**的输入件，报告的八角色清单确实漏项。

## 4 发现二：漏掉的不只是「一个名字」，而是一整套未记录的规格

`learnability_feature_ledger` 在合同里有一组**强约束**，报告一字未提（行号均指 `phase1a_data_contract.py`）：

| 约束 | 代码位置 | 失败码 |
|---|---|---|
| 顶层键集**恰好**为 `contract_version` / `source_tables_sha256` / `schema_sha256` / `confidence_manifest_sha256` / `rows` | :665-673 | `invalid_feature_ledger_fields` |
| `contract_version` 恰好等于 `phase1a-feature-ledger-v1` | :24、:674-675 | `invalid_feature_ledger_version` |
| 三个 sha256 必须**分别等于**同包内 `source_tables` / `schema` / `confidence_manifest` 三个角色件的实际哈希（跨角色绑定） | :690-699 | `feature_ledger_source_hash_mismatch` |
| `rows` 必须是非空 list | :700-703 | `invalid_feature_ledger_rows` |
| 每行键集**恰好**等于 `FEATURE_FIELDS` = `sample_id`/`uid`/`observed_header`/`canonical_fields`/`candidate_target`/`confidence`/`family` | :82-90、:709-711 | `invalid_feature_ledger_row` |
| `canonical_fields` 非空、元素为非空字符串且**互不重复**；`candidate_target` 若非 null 必须**属于** `canonical_fields` | :714、:725-729、:736 | `invalid_feature_ledger_row` |
| `confidence` 只能是 `null` 或 `low`/`medium`/`high` | :730-734、:736 | `invalid_feature_ledger_row` |
| 每行 `sample_id` 必须落在 **proposal_train 层**，且 `uid` 必须与该样本登记的 uid 一致 | :704-708、:739-740 | `feature_ledger_identity_mismatch` |
| 行集合必须**恰好覆盖** proposal_train 层全部样本（不多不少） | :741-742 | `feature_ledger_proposal_coverage_mismatch` |

⇒ 即使 owner 猜到要多加一个角色，也**无法从报告推出**上面任何一条；尤其「三个跨角色哈希必须自洽」与「必须恰好覆盖 proposal_train 层」两条，只能读代码才知道。

## 5 发现三：报告的 `analysis_plan` 行同样欠规格（18 个必需键只逐字命名 3 个）

机械推导得校验器对 `analysis_plan` 的**必需键 = 18**（正则抽取 15 + 循环变量 3；另 3 个遗留歧义键为「出现即失败」，不计入必需）。报告 `analysis_plan` 行的覆盖情况：

```text
逐字命名 (3): cluster_unit, risk_limit, significance_level
仅散文描述 (10): approved_by<-“Approved owner”   approved_at<-“owner/time”
                target_power<-“target power”    noninferiority_margins<-“non-inferiority margin”
                holm_families<-“frozen Holm family”
                seed_uid_aggregation<-“seed×UID aggregation”
                threshold_selection<-“threshold-selection rule”
                minimum_uid_by_role_family<-“每角色×家族最低 UID”
                mde_by_confirmatory_contrast<-“每个确认性对比的 MDE”
                layer_manifest_sha256<-“exact layer-manifest hash”
完全缺失 (5): primary_metrics, one_sided_p_value_methods, holm_adjustment,
              minimum_uid_by_action, status
合计 3 + 10 + 5 = 18
```

上表 10 条散文映射**逐条经脚本断言短语确实在该行内出现**，不是目视判断。

**散文无法传达的精确 token 要求**（这几条最容易被 owner 写错）:

- `status` 必须恰好等于 `approved`（:912）；报告只写 “Approved owner/time”，给不出这个字面量。
- `threshold_selection` 必须恰好等于 `proposal_dev_only`（:940）；报告只写 “threshold-selection rule”。
- `minimum_uid_by_action` 的键集必须**恰好**为 `{map_to, skip, hold}` 且值为 `int >= 2`（:962-968）；报告**完全没提**这个按动作的下限（只提了按角色×家族的）。
- `one_sided_p_value_methods` 必须是**恰好 5 键**的字典且值逐字匹配（:946-953）；报告完全没提。
- `holm_adjustment` 必须恰好等于 `step_down_adjusted_p_and_simultaneous_one_sided_ci`（:954）；报告完全没提。

## 6 综合判断：同一件事存在三份互不相容的规格

| 规格来源 | 角色数 | `analysis_plan` 字段 | 照它交付的结果 |
|---|---|---|---|
| `DATA_NO_GO` 报告 “Executable supplement contract” | **8**（漏 `learnability_feature_ledger`） | 18 个必需键中逐字命名 3、散文 10、缺失 5 | **实测 `DATA_NO_GO`**：`missing_required_role` + `missing_or_mismatched_binding` |
| 预注册件 §7 冻结收据 | 不涉及 | 24 键、平铺 `delta_*`，与合同 10 个必需键完全不相交 | **实测 `DATA_NO_GO`**：原样 18 个错误码；填满仍 14 个（见姊妹件） |
| `research/phase1a_data_contract.py` | **9** | **18** 个必需键 + 多处精确 token | 唯一权威；`READY_FOR_INDEPENDENT_ACCEPTANCE` |

⇒ **两份人工规格都无法让机器合同通过。** 代码是唯一权威规格，但它对数据 owner 不可见（且按纪律 owner 只拿到报告）。**这是当前主线上最便宜的一处修复**：不动代码、不动判据，只需给报告补一段 append-only 更正，就能避免一整轮外部交付白跑。

## 7 建议的 append-only 更正（**本件未落，需用户授权**）

`docs/INDEX.md` :66 记 `experiments/` 为「只追加证据集」，且 `DATA_NO_GO` 报告是**权威门槛报告**，故本件**不改它一个字节**，只把建议措辞列在这里等授权：

1. 在 “Executable supplement contract” 一节**末尾追加**更正段（不改动既有正文与 `DATA_NO_GO` 结论），内容至少包含：
   - 必需角色是 **9** 个而非 8 个，补列 `learnability_feature_ledger`，并注明「八角色」为原报告笔误、以本段为准；
   - §4 表格的全部 9 条约束（顶层 5 键、版本 token `phase1a-feature-ledger-v1`、三个跨角色 sha256、`rows` 非空、行键集恰为 `FEATURE_FIELDS` 7 键、`canonical_fields` 去重且 `candidate_target` 必属其中、`confidence` 词表、`sample_id` 必在 proposal_train 层且 uid 一致、行集合恰好覆盖该层）；
   - `analysis_plan` 的 **18 个必需键的逐字键名**与 §5 列出的 5 处精确 token/键集要求；
   - 一句显式声明：机器合同 `research/phase1a_data_contract.py` 为唯一权威规格，本段是其可读镜像，冲突时以代码为准。
2. 同一更正段应交叉指向 §7 收据口径缺口件，说明 §7 收据与 `analysis_plan` 是**两份不同工件**还是同一份仍待裁定（决策 5），在裁定前不要照 §7 的字段集构造 `analysis_plan`。
3. 建议同时补一个**只读自检脚本**（可入 `scripts/research/`），让 owner 在交付前对自备包跑一次 `validate_package` 并只回传聚合失败码，避免到货才发现规格不符。此为新增可执行文件，属独立批，需另批并跑全量 pytest。

## 8 本件不做的事

未改 `DATA_NO_GO` 报告、预注册件、`phase1a_data_contract.py` 或任何代码；未改冻结判据/阈值/oracle/冻结 hash；未解 `DATA_NO_GO`（本件实测结果反而是 `DATA_NO_GO`）；未启动 Phase 1a/2；未批准任何数值、未填任何 `UNSET`；未新增任何生成器或脚本入仓；未授权训练或模型端点；未动 `docs/33`、`docs/34`。

## 9 复现与取证

```bash
ssh jinrong-dev
cd ~/wzh/projects/agents_final_tech_accept_ac009e3
~/wzh/projects/agents_final_tech/venv/bin/python /tmp/cmp_supplement_contract.py "$PWD"
~/wzh/projects/agents_final_tech/venv/bin/python /tmp/p1a_supplement_gap_probe.py "$PWD"
~/wzh/projects/agents_final_tech/venv/bin/python /tmp/p1a_row_classify.py "$PWD"
```

| 文件（GB10 `/tmp`，仓外，不 commit） | sha256 |
|---|---|
| `cmp_supplement_contract.py` | `7c0c0a0eb8aaf3890a63b538d3ac0af94832bacdd1caa9e4b23960c77dc8340f` |
| `p1a_supplement_gap_probe.py` | `c991c26df139dbebe6061c23d2fcc5ce547315e01b3db1172c5359972263c1b9` |
| `p1a_supplement_contract_gap.json` | `b82c02545d5253cbbb71a5c965d7dcf481fb7814072880bcf27c0f297239ad4d` |
| `p1a_row_classify.py` | `501f0b9e8d4d001885953211f2b70bfb0b43d22a75f1efc07b6b9613fd44b755` |
| `p1a_analysis_plan_row_classification.json` | `f1833fb49a3ef06ba733f14787a0b5c743781d2a8815197baa021b7f89b9b125` |

纯 stdlib，**零第三方依赖、零端点、零模型调用、零私有数据读取**（合成 fixture 而已）；两次校验器 `meta` 均 `endpoint_calls 0 / socket_attempts 0`，由 `offline_guard()` 记录而非自我申报。脚本内含 `assert`，映射或计数不成立即抛错而非静默出数。`/tmp` 非持久，故全部关键数字与失败码已逐字抄入本件。

## 10 红线自查

未改任何权威规格文件一个字节 · 未解 `DATA_NO_GO` · 未改冻结判据 · 未批准任何数值 · 未填任何 `UNSET` · 未启动 Phase 1a/2 · 未授权训练或端点 · 零模型调用 · 未派发任何 Loop A/B/C 卡 · 未 pull production（仍 `e5ab809` + 5 脏件）· 未重启 daemon `1816933` 与 `:5050` `1868428` · 未改 crontab · 未动 `docs/33`、`docs/34` · 四件用户资产零触碰 · 逐路径 add、无 `-A`/`--amend`/`--no-verify`。
