# WP-2 F-5 / F-10 闭环复查 — Loop C（round 3）

> task: `tatqa-wp2-f5c-20261014` | 审计者: GB10 Loop C（独立上下文）| 日期: 2026-10-14 | 总体判定: **CONDITIONAL**（F-5/F-10 关闭本体均成立；唯一缺口 = F5 执行报告一句无产物断言 → S0d 轮补档/撤回）
>
> 落盘说明: Loop C 写入通道再度被其沙箱拒绝（同前两轮的误判）；本文件正文区为运行日志 `~/wzh/loop_runs/tatqa-wp2-f5c-20261014/c.log` 第 2 行起的逐字节转录（`tail -n +2`，20843 bytes，未改一字）。
>
> Loop D 应裁摘要（非审计内容）: F-5 三数与逐 role-origin 独立复算全部一致（哈希序严格单调、替换建议位序正确）；F-10 由分支差分证明严格性界恰为 `wrong_period`→`wrong`；唯一 CONDITIONAL 来源为 `F5_EXECUTION_REPORT.md` L23 的 "24-case" 断言无产物 → 已派 S0d 轮（实证矩阵产物 + 原句撤回）；另两条低危建议入 S7 清单。

## 审计正文（逐字节转录，20843 bytes）
写盘被沙箱拒绝（`Write` 未授权 —— 与前两轮同一误判）。按任务卡规定，完整报告置于下文，供转录落盘为 `docs/research/WP2_F5F10_LOOP_C_AUDIT_v1.md`。

---

# WP-2 F-5 / F-10 闭环复查（round 3）— Loop C 审计报告 v1

> task: `tatqa-wp2-f5c-20261014` | date: 2026-10-14 | loop: C (round 3)
> 范围: **只复查** F-5 资格决策与 F-10 修复的关闭质量。未重做全量审计、未跑 S4+、未改任何被审对象与历史文件。
> 红线遵守: 只读；零模型、零网络、零凭证；未 commit、未 push。被审对象与历史文件均未触碰。

## 0. 总体判定 — **CONDITIONAL**

F-5 与 F-10 两项**关闭本体均成立**，经独立复算与手推演双重印证：

- F-5 的 352/36/316 三数、22 role-origin 逐项核验、唯一 shortfall 归属、`null=identity` 显式落录、`currency` fail-closed 口径、`gold_delta_source_unit` 数值性，**全部独立复算一致**。
- F-10 的新分支位置/守卫正确，严格性改动被哈希链证明**只含 `wrong_period`→`wrong`**，fixture 期望值经手推演双向确认。

判定为 CONDITIONAL 而非 PASS 的唯一原因：**执行报告中一条证据性断言无任何产物支撑**（§2.4）。不影响修复正确性，但影响本轮"关闭质量"的证据链完整性，须补档或撤回后方可宣告收口。

| 复查点 | 判定 | 一句话 |
|---|---|---|
| 1. F-5 资格 | **PASS** | 三数与逐 role-origin 全部独立复算一致，shortfall 归属与替换建议边界正确 |
| 2. F-10 修复 | **CONDITIONAL** | 修复本体与严格性界**已证实**；"24-case strictness matrix"断言无产物支撑 |
| 3. 边界 | **PASS** | 语义面未触碰、item freeze 仍 S7、S0/S0B 哈希钉住、零模型属实（附 1 条潜伏告警） |
| 4. 文档（INDEX 两行） | **PASS** | `git diff` 恰 2 insert；描述与实际产物逐项一致 |

---

## 1. F-5 资格决策 — **PASS**

### 1.1 三数独立复算（不复用被审代码）

用 `grep`/`paste`/`uniq` 直接读 `candidate_items_v2.json` 原始字节重新计数（**未 import `check_pilot_eligibility.py`**）：

| 量 | 独立复算 | 收据/决策文档 | 一致 |
|---|---:|---:|:--:|
| total | 352 | 352 | ✓ |
| excluded generic `currency` | 36 | 36 | ✓ |
| eligible | 316 | 316 | ✓ |
| eligible `null` | 312 | 312 | ✓ |
| eligible `%` | 2 | 2 | ✓ |
| eligible `million` | 2 | 2 | ✓ |
| eligible `absent` | 0 | 0 | ✓ |

`source_unit` 原始分布（全量 352）: `null=312, "currency"=36, "million"=2, "%=2"`，求和 352，分割完备。无 `absent`；352 个 `"source_unit"` 键 ↔ 352 题，无嵌套重复键。

Target resolution 独立复算: `identity_unit=312, percent_identity=2, scale_identity=2`，与收据 `target_unit_resolution.counts` 一致。

### 1.2 `gold_delta_source_unit` 数值校验

| 检查 | 结果 |
|---|---|
| 出现次数 | 352 / 352（每题恰一次） |
| `null` | 0 |
| `true` / `false` | 0 / 0 |
| 字符串形态 | 0 |
| 指数记法（`e`/`E`，可能溢出为 `inf`） | 0 |

→ 全部为有限 JSON 数值。收据 `checks.all_gold_delta_source_unit_values_numeric = true` 属实。
"字段名陷阱"语义（别名 `gold_delta_value_in_source_unit`，**只作数值、绝不作单位串解析**）在决策文档 §2.5–2.6 与收据 `rules.gold_delta_source_unit` 两处显式记录，且 `check_pilot_eligibility.py` 只用 `source_unit` 做单位分类、`validate_gold_source_delta` 只验数值 —— 口径一致，无误用。

### 1.3 逐 role-origin 核验

22 个 role origin 来自 `SPLIT_RERUN_RECEIPT.json`（`status=PASS_BYTE_IDENTICAL`、`comparison.byte_identical=true`、`role_assignments_identical=true`），pilot 8 + pilot_reserve 8 + development 2 + history 4 = 22，互不重叠。

独立复算（原始 items 按 `origin_id` 归并）：

- 每个 origin 恰 2 题（352 题 / 176 origin，`origin_id` 计数 352，最大重复 2）。
- 36 道 `currency` 题分布于 **恰 18 个 origin**，且**这 18 个 origin 全部两题皆为 `currency`**（各自 2/2）→ 18 个 origin 均归零合格题。
- 22 个 role origin 与这 18 个 origin 的交集 = **恰 1 个**: `tatqa_dace18a6-701f-49d4-a16d-078e5b62fc94`
  - 其角色 = `pilot_reserve`（`SPLIT_RERUN_RECEIPT.json` L37）✓
  - `candidate_count=2, eligible_count=0` ✓ 与收据 `shortfall_rows` 逐字段一致
- 其余 21 个 role origin 各保 2 题合格 → `origins_with_at_least_2_eligible = 21`，`shortfall_count = 1` ✓

与决策文档 §3 表述逐句相符（"21 retain at least two eligible candidates"、"The 36 excluded items belong to 18 origins"、"loses both candidates"）。

### 1.4 角色未改 / 仅给替换建议

- 收据 `role_assignments_changed = false`、`silent_role_change = false`；`decision_boundary.role_assignments_changed = false`。
- 22 行 role 表逐行与独立复算的 (role, origin_id, candidate_count, eligible_count, excluded_currency_count) **零不符**。
- 替换建议仅 3 条（rank 23/24/25），`basis` 明文 "no role is changed"；决策文档 §4 声明应用须另授 freeze 动作。
- 分割侧一手印证: `SPLIT_RERUN_RECEIPT.json` 仍 `DRAFT_NOT_FROZEN`，未被改写。

**rank 23+ 独立复核**（`sha256(seed:origin_id)`，seed=`wp2-split-dryrun-20261013`）：

| # | origin | hash 前 8 位 |
|---|---|---|
| 1–8 (pilot) | 008eaf4e … 8edfdb1c | `0336fed3` → `12534fe8` |
| 9–16 (reserve) | 3e4f4b3e … **dace18a6** | `13f57448` → `28dda4b1` |
| 17–18 (dev) | 4565ded8, e8877535 | `28f339f4`, `2a343070` |
| 19–22 (history) | b2c8ac7d … 99a3fe4e | `2b521e87` → `300e1f82` |
| 建议 rank 23 | **cb626a5c** | `327686d5` |
| 建议 rank 24 | 989a6b20 | `37fa6a30` |
| 建议 rank 25 | 8e0e12f7 | `384c69da` |

22 个 role origin 的哈希**在 ROLE_ORDER 中严格单调递增**（`0336…`→`300e…`），证明 role 集合正是按该 outcome-blind 哈希序选取；三条建议哈希 `3276 < 37fa < 384c` 严格递增且**全部大于全部 22 个 role 哈希**，与 rank 23/24/25 相邻次序一致（22→23 位间距 `0x268` ≈ 0.94% 哈希空间，与 n=182 相邻次序统计期望 1/183 ≈ 0.55% 同量级）。三条建议 origin 均未被分配、各 2 题合格（`null=2`），与收据一致。

**未验证面（明示）**: 沙箱禁止逐行批量哈希（`python`/`jq`/`xargs`/`awk system()`/`for` 变量均被挡），**未能枚举全部 182 个 origin 哈希**去独立证明"恰 22 个排在 cb626a5c 之前"这一**整数 rank 值**。该值由被审代码 `enumerate(ranked, start=1)` 从清单直接算出（读码确认计数含已分配/不合格 origin，逻辑正确），且上述次序不等式已独立成立。残余风险仅在"收据非由该代码生成"，而 §1.6 哈希钉定与 stdout 逐字吻合使该可能极低。

### 1.5 `null=identity` 显式记录、`currency` fail-closed 口径

- **`null=identity` 显式落录**（非依赖 checker 静默行为）:
  - `rules.source_unit_null_or_absent` 明文: "explicit identity at dimensionless unit; receipt does not rely on silent checker behavior"。
  - 312 条 `null` 题**逐题**写入 `target_unit_resolution.items`，抽查确认 `resolution_class="identity_unit" / resolved_target_unit="unit" / result_unit_semantics="unit"`。
  - `%` 题 → `percent_identity / percent / percentage_points` ✓；`million` 题 → `scale_identity / million / million` ✓（Option A 恒等）。
- **`currency` fail-closed 与 owner 授权口径一致**:
  - 授权口径见 `WP2_TARGET_UNIT_RULES_DRAFT_v1.md`: "Currency is not converted unless both currency and denomination are explicit; **a generic `currency` label is insufficient**"；"currency identity is allowed only for the same explicit currency and denomination"；"The decision sets **fail-closed generic-currency exclusion** and explicit null/absent source-unit identity; item freeze remains S7"。
  - 决策文档 §2.1 表述为"excluded fail-closed from the pilot candidate set"，收据 `rules.generic_currency = "exclude fail-closed"`。
  - 与 Loop C round-1 的 F-5 基线（"按 S2 草案自身 fail-closed 规则，这批题不得进入 pilot 题本"）同一口径 —— **一致，无扩大、无缩小**。排除仅限 **generic** 标签，未涉具体币种/面额题。

### 1.6 哈希与收据完整性

`F5_EXECUTION_REPORT.md` 记录的 **10 个产物哈希 + 3 个输入哈希，逐个 `sha256sum` 与盘上比对，13/13 全部吻合**：

| 文件 | 声明 | 实测 | |
|---|---|---|:--:|
| `check_pilot_eligibility.py` | `614fad85…` | `614fad85…` | ✓ |
| `PILOT_ELIGIBILITY_RECEIPT.json` | `7cda8d71…` | `7cda8d71…` | ✓ |
| `WP2_F5_ELIGIBILITY_DECISION_v1.md` | `f45718a3…` | `f45718a3…` | ✓ |
| `WP2_TARGET_UNIT_RULES_DRAFT_v1.md` | `ee665e9d…` | `ee665e9d…` | ✓ |
| `checker_v2.py` | `aeedf62b…` | `aeedf62b…` | ✓ |
| `s0c_equivalent_form_fixtures_v2.json` | `58e17ac5…` | `58e17ac5…` | ✓ |
| `s0_run_fixtures_v2.py` | `2f5460de…` | `2f5460de…` | ✓ |
| `S0C_FIX_RECEIPT.json` | `a6b88817…` | `a6b88817…` | ✓ |
| `S0_FIX_RECEIPT.json` | `1085cde7…` | `1085cde7…` | ✓ |
| `S0B_FIX_RECEIPT.json` | `b759a5e7…` | `b759a5e7…` | ✓ |
| `candidate_items_v2.json`（输入） | `5f61f2a4…` | `5f61f2a4…` | ✓ |
| `origin_manifest.json`（输入） | `3718e6fe…` | `3718e6fe…` | ✓ |
| `SPLIT_RERUN_RECEIPT.json`（输入） | `771f2096…` | `771f2096…` | ✓ |

收据内嵌输入哈希与实测一致；`determinism.timestamp_free=true`、canonical JSON 声明与代码 `json.dumps(..., indent=2, sort_keys=True)+"\n"` 实现一致。代码 stdout 模板与执行报告所记两行逐字吻合。

**未验证面（明示）**: `output_sha256`（payload 自哈希 `d42e11eb…`）**未重算** —— 沙箱禁止 `python`/`jq`/`sed`/`awk gsub`，无法在不落盘前提下重建 canonical 序列化。同理**未复跑**字节级重生成（跑生成脚本会覆写被审收据，属红线，刻意不跑）。

---

## 2. F-10 修复 — **CONDITIONAL**

### 2.1 新分支位置与守卫 — 正确

`checker_v2.score_prepared` 判定序：

| 序 | 守卫 | 归因 | 来源 |
|---|---|---|---|
| A | `periods==[early,late]` ∧ `delta_source==-gold.delta_source` ∧ `unit!=gold.target_unit` | `wrong_unit` | **S0B** 单位门 |
| B | `periods==[early,late]` ∧ `delta_source==-gold.delta_source` ∧ `delta_target==-gold.delta_target` | `correct_other_form` | 原有 |
| **C** | **`periods==[early,late]`** | **`wrong`** | **F-10（本轮）** |
| D | `periods!=[late,early]` | `wrong_period` | 原有 |
| E–H | 直接形源/目标/单位 | `wrong_unit`/`correct`/`wrong` | E 含 S0B 门 |

分支 C 位于 A/B **之后**、D **之前** —— 位置正确：既不遮蔽等价形的正确归因（B）与单位门（A），又能在 D 之前拦下"等价形合法期间但数值错误"的错归因。守卫精确匹配等价形（期间集合合法、早→晚顺序），无过宽匹配。

### 2.2 严格性只允许 `wrong_period`→`wrong` — **已证实**

关键在隔离 F-10 改动与更早的 S0B 单位门。哈希链一手闭合：

```
S0B_FIX_RECEIPT.json before.checker_v2.py = 642c5d9c…   (S0B 前)
S0B_FIX_RECEIPT.json after.checker_v2.py  = b3c7b363…   (S0B 后)
s0_run_fixtures_v2.py PRE_FIX_SHA256      = b3c7b363…   (F-10 前)  ← 同值
现盘 checker_v2.py                        = aeedf62b…   (F-10 后)
```

→ **F-10 的编辑起点正是 S0B 终态**，故分支 A 与直接形单位门在 F-10 之前已存在。分支 A 归属 S0B 亦由其专属 3 例 fixture 独立佐证（`s0_unit_gate_fixtures_v2.json`: `equivalent_form_same_scale_wrong_unit`、`thousand_to_unit_equivalent_form_wrong_unit`、`thousand_to_unit_equivalent_form_valid_unit`，覆盖 A 与 B 两侧）。

据此对等价形（`periods==[early,late]`，`early!=late`）穷举差分：

| `delta_source` vs `-Gds` | `delta_target` vs `-Gdt` | `unit` vs `Gtu` | F-10 前 | F-10 后 | 变化 | 归属 |
|---|---|---|---|---|---|---|
| == | == | == | `correct_other_form` | `correct_other_form` | 无 | — |
| == | == | ≠ | `wrong_unit`(A) | `wrong_unit`(A) | 无 | — |
| == | ≠ | == | `wrong_period` | **`wrong`**(C) | **`wrong_period`→`wrong`** | **F-10** |
| == | ≠ | ≠ | `wrong_unit`(A) | `wrong_unit`(A) | 无 | — |
| ≠ | 任意 | 任意 | `wrong_period` | **`wrong`**(C) | **`wrong_period`→`wrong`** | **F-10** |

非等价形分支（含直接形与 D）**逐支未变**。→ **F-10 严格性差分恰为 `wrong_period`→`wrong`，无任何 `correct*` 类翻转、无反向翻转。** 收据三处 `strictness: "wrong_period_to_wrong_only"` 与此一致。

### 2.3 fixture 期望与手推演复核

fixture `equivalent_form_valid_periods_wrong_delta_valid_unit`：`observed_pre_fix_outcome="wrong_period"`、`expected_outcome="wrong"`；runner 双重断言，实跑 `actual="wrong"`、`pass=true`。

**手推演（独立、不跑代码）**：

- 表 `["Revenue","2.5","1.2"]`，`period_late{col:1,label:"2025"}`、`period_early{col:2,label:"2024"}` → `late=2.5, early=1.2`
- `delta_source = 2.5−1.2 = 1.3`；`source_unit="thousand"→target_unit="unit"`，`conversion_factor = 10^(3−0) = 1000` → `delta_target = 1300`；`gold.target_unit = "unit"`
- 答案 `{"row":"Revenue","periods":["2024","2025"],"delta_source":-1.0,"delta_target":-1000,"unit":"unit"}`：
  - row `"Revenue"` 相符 → 不走 row 门
  - A: `delta_source(-1.0) == -1.3`? **否** → 不触发
  - B: 同上 **否** → 不触发
  - **C: `periods == ["2024","2025"] == [early,late]` → 返回 `wrong`** ✓ 与 `expected_outcome` 相符
  - F-10 前（无 C）: `periods != ["2025","2024"]` 成立 → 返回 `wrong_period` ✓ 与 `observed_pre_fix_outcome` 相符

**结论**: fixture 声明的 pre-fix 与 post-fix 两个期望值**均被手推演独立证实**。归因正确 —— 期间为合法等价形、单位正确、双 delta 皆错，错误在数值而非期间，`wrong` 优于 `wrong_period`。

### 2.4 证据缺口 — **必须补档或撤回**（CONDITIONAL 之由来）

`F5_EXECUTION_REPORT.md` L23 断言：

> "An additional **24-case strictness matrix** found **five changed classifications**, all `wrong_period` -> `wrong`; no case flipped to a correct class."

**全仓检索无任何产物承载该证据**：

- `S0C_FIX_RECEIPT.json` 的 `equivalent_form_fixtures.case_count = 1`，无 24 例矩阵、无"five changed"计数；
- `fixtures/` 下无 strictness-matrix 文件（仅 4 个 fixture：3/1/1/5 例）；
- `s0_run_fixtures_v2.py` 无矩阵生成或计数逻辑；
- `docs/research/` 无相关记录；该句是"24"在 F-5/F-10 产物中的**唯一**出现。

该 24 例矩阵**不可复现、不可核验**。注意这不影响 §2.2 结论 —— 后者由哈希链 + 穷举差分**独立**成立；但执行报告中一条**实证性断言悬空**，在"只认一手证据"的审计纪律下必须处理。

**处置建议（择一，需 owner 拍板）**:
1. 补档：把 24 例矩阵的 case 列表、变更计数与生成方式作为产物落盘并钉哈希；或
2. 撤回：将该句删除或改写为"严格性界由分支差分证明"，避免无据实证。

### 2.5 告警（不影响判定，建议随下轮加固）

`checker_v2.score_prepared` 分支 C 守卫为 `periods == [early, late]`，而 `recompute_gold`/`prepare_item` **未校验** `period_late` 与 `period_early` 的列/标签互异。若某题 `early_period == late_period`，则 `[early,late] == [late,early]`，分支 C 将先于直接形路径返回 `wrong`，使本应 `correct` 的答案被判 `wrong` —— **严格性会越出 `wrong_period`→`wrong`**。

**当前数据不可达**（已独立验证）：352 题的 704 个 period label 中，`uniq` 折叠后仅 4 组相邻重复，涉及 `"2018"`/`"2019"`/`"2021-2022"` 三值；对三值逐一按 (late,early) 配对检索，**同题等值配对 0 例**（4 组重复全落在跨题边界，如 L23694 `period_early` ↔ L23750 下一题 `period_late`）。故本轮数据面无实际影响。

建议 S7 前在 `prepare_item`/`recompute_gold` 增加 `late_col != early_col` 且 `late_label != early_label` 的 fail-closed 断言。属**新建议**，非本轮失败项。

---

## 3. 边界 — **PASS**

| 检查项 | 证据 | 结果 |
|---|---|:--:|
| `normalize_unit`/`UNIT_ALIASES` 未改 | 二者定义于 `checker.py`；实测 `c919845b…`，与 Loop C round-2 所钉一致。`checker_v2.py` 以 `checker_v1.normalize_unit = …` **引用再导出、无覆写**；`recompute_gold`/`prepare_item`（单位语义所在）同样原样再导出 | ✓ |
| `checker.py` 一手印证 | git 跟踪且不在 `git status` 改动列表中 | ✓ |
| item freeze 仍 S7 | 收据 `decision_boundary.item_freeze="S7"`；决策文档 §1/§5；`left_open` 第 3 条 | ✓ |
| S0/S0B 收据哈希钉住 | 实测 `1085cde7…` / `b759a5e7…`，与 `PINNED_RECEIPT_SHA256` **双钉**一致；runner 写 S0C 前后各校验一次，只写 `S0C_FIX_RECEIPT.json`、不覆写 S0/S0B | ✓ |
| 零模型/端点/裁判/外网 | 四份被审脚本 grep `requests/httpx/openai/urllib/socket/http(s)://urlopen/api_key/anthropic/OPENAI` **零命中**；S0C `cost` 全 0；收据 `decision_boundary` 四项全 0 | ✓ |
| 未越界动作 | 未跑 S4+、未冻结、未训练、未改 split、未 commit/push | ✓ |

本次审计自身亦零模型、零网络、零凭证；仅用只读文本工具与 `sha256sum`/`git` 只读命令。**刻意不执行** `check_pilot_eligibility.py` 与 `s0_run_fixtures_v2.py`（二者都会覆写被审收据，属红线）。

---

## 4. 文档（`docs/INDEX.md` 新增两行）— **PASS**

`git diff --stat docs/INDEX.md` = `1 file changed, 2 insertions(+)`，无删除 —— **恰为两行新增**。

| 行 | 链接 | 描述要点 | 核对 |
|---|---|---|---|
| WP-2 F-5 资格闭环 | `research/WP2_F5_ELIGIBILITY_DECISION_v1.md` | 352→316、36 fail-closed、22 origins 逐项、1 reserve shortfall 仅建议不改角色、item freeze 仍 S7 | 五点**全部**与 §1 复算一致 ✓ |
| WP-2 F-10 checker 收口 | `../research/tatqa_wp0_2026/wp1/S0C_FIX_RECEIPT.json` | 等价形合法期间+错值+正确单位 `wrong_period`→`wrong`；S0/S0B 哈希钉住且不覆盖 | 与 §2/§3 一致 ✓ |

两链接目标均存在；描述无夸大（未把"24-case matrix"写入 INDEX）。

**备注（非失败项）**: 另产 `WP2_TARGET_UNIT_RULES_DRAFT_v1.md`、`F5_EXECUTION_REPORT.md`、`PILOT_ELIGIBILITY_RECEIPT.json` 未进 INDEX。任务卡只要求核对"新增两行"，故不判负；按 `jinrong-docs-sync` 单一入口治理建议下轮补登。

---

## 5. 未验证面（汇总明示）

1. `PILOT_ELIGIBILITY_RECEIPT.json` 的 `output_sha256` 自哈希（`d42e11eb…`）**未重算** —— 沙箱禁止 `python`/`jq`/`sed`/`awk`，无法重建 canonical 序列化。
2. 收据**字节级重生成未复跑** —— 跑生成脚本会覆写被审收据，属红线；仅由哈希钉定 + stdout 逐字吻合 + 输入哈希一致间接支撑。
3. **rank 23 的整数位次未独立枚举**（182 origin 全量哈希被沙箱挡）；次序不等式已证，位次值为代码推导。
4. `docs_lint.py` 的 `PASS (0 fail / 14 warn)` **未复跑**（需 python）。
5. "24-case strictness matrix" **无法验证** —— 无产物存在（§2.4）。
6. F-5 所称 owner 授权"2026-10-13 夜默认 Loop D 闭环"的**原始授权记录未一手读取**；本轮以 `WP2_TARGET_UNIT_RULES_DRAFT_v1.md` 规则文本 + Loop C round-1/2 审计所载口径为一致性基准，三者自洽。

---

## 6. 结论与待办

**判定: CONDITIONAL。** F-5 与 F-10 的**关闭本体成立**（独立复算 + 手推演 + 哈希链三重印证），边界干净、文档两行属实。放行前须处置一项证据缺口：

| # | 事项 | 严重度 | 处置 |
|---|---|---|---|
| 1 | `F5_EXECUTION_REPORT.md` L23 "24-case strictness matrix / five changed classifications" 无任何产物支撑 | **中** | 补档并钉哈希，或撤回该句（需 owner 拍板） |
| 2 | `run_equivalent_form_fixtures` 的 `observed_pre_fix_outcome` 为 fixture 自声明字段，runner 只断言其等于 `"wrong_period"`，**并不回跑 pre-fix 代码** | 低 | 该声明经本轮手推演证实为真；建议 runner 携带 pre-fix 实跑路径，使证据链自足 |
| 3 | `early_period == late_period` 无守卫（潜在 `correct`→`wrong` 越界） | 低（当前数据 0 例） | 建议 S7 前加 fail-closed 断言 |

在第 1 项闭合前，本报告**不宣告** F-5/F-10 轮闭环完成，亦不授权任何 S4+ 动作。item freeze 仍为 S7；split 仍 `DRAFT_NOT_FROZEN`；三条 reserve 替换建议仍为**建议**，应用须另授 freeze 动作。
