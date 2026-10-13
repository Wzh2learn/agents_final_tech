# WP-2 S0d 补档复查 — Loop C（round 4）

> task: `tatqa-wp2-f5d-c-20261014` | 审计者: GB10 Loop C（独立上下文）| 日期: 2026-10-14 | 总体判定: **PASS**（S0d 证据缺口闭合）
>
> 落盘说明: Loop C 写入通道再度被其沙箱拒绝；本文件正文区为运行日志 `~/wzh/loop_runs/tatqa-wp2-f5d-c-20261014/c.log` 第 2 行起的逐字节转录（`tail -n +2`，26669 bytes，未改一字）。
>
> Loop D 应裁摘要（非审计内容）: 16 例矩阵 16/16 手推演吻合；临时 pre-F-10 重建哈希与四处历史钉值逐字节相同（`b3c7b363…`）；撤回闭环成立；未覆写项全 PASS。O-2（撤回件未登 INDEX）已随本批补登；O-1 与 S7 遗留项入台账。

## 审计正文（逐字节转录，26669 bytes）
写入 `docs/research/WP2_F5D_LOOP_C_AUDIT_v1.md` 被沙箱拒绝（与 round-3 同一情形）。按任务卡规定，**全文转录如下**。

---

# WP-2 S0d 补档复查 — Loop C（round 4）审计卡

> task: `tatqa-wp2-f5d-c-20261014` | 审计者: GB10 Loop C（独立上下文）| 日期: 2026-10-14 | 总体判定: **PASS**
>
> 范围: **只查** S0d 两件产物 —— `research/tatqa_wp0_2026/wp1/S0C_STRICTNESS_MATRIX_RECEIPT.json`、`docs/research/F10_STRICTNESS_MATRIX_ADDENDUM_v1.md`（对照 `research/tatqa_wp0_2026/wp2/S0D_EXECUTION_REPORT.md`）。不重做全量审计、不跑 S4+、不改被审对象。
>
> 红线遵守: 只读；零模型、零网络、零凭证；未 commit、未 push；被审对象与历史文件字节未动（哈希对照见 §3）。

## 0. 总体判定 — **PASS**

S0d 两件产物的**内容与证据链成立**：16 例矩阵逐条 pre/post 归因经本轮独立手推演 16/16 吻合；变更集合恰为 5 条 `wrong_period`→`wrong`、`correct*` 翻转 0；原 "24-case" 断言已按原句逐字撤回并改引可核验产物；被保护文件未被覆写。三条观察（§6）与七项未验证面（§5）不构成判负，均为低成本移交项。

| # | 复查点 | 判定 | 一句话 |
|---|---|---|---|
| 1 | 矩阵收据内部一致 | **PASS** | 覆盖声明 16/16 穷举属实；逐条归因手推演全吻合；变更集恰为 `wrong_period`→`wrong`；`correct*` 翻转 = 0 |
| 2 | 撤回闭环 | **PASS** | 原句逐字撤回、改引矩阵产物 + round-3 §2.2；无夸大、无新悬空断言 |
| 3 | 未覆写 | **PASS** | S0/S0B/S0C 收据对 round-3 在案钉值 3/3 一致；F5 报告内容与时间序一致；builder 设计上拒绝覆写 |
| 4 | 力所能及手推演 | **PASS** | 超配额完成：16/16 例全推演，含 2 例详证 |

---

## 1. 矩阵收据内部一致 — **PASS**

### 1.1 用例集覆盖声明 vs 实际条目

收据 `case_construction.cardinality` 声明 `2 x 2 x 2 x 2 = 16; no target case count was assumed`。实测：

- `cases` 实际条目 = **16**，`summary.case_count` = 16，二者一致；
- 四维笛卡尔积（`periods_order` × `delta_source_correct` × `delta_target_correct` × `unit_correct`）**16 个组合逐一命中、无缺漏、无重复**；
- `period_form_counts`: `equivalent_form = 8` / `direct_form = 8`，与 `role` 字段（`full_equivalent_form_branch_space` / `direct_form_control`）逐条对应；
- `case_id` 命名与 `input_flags` 逐条相符；`answer` JSON 字段与 `wrong_value_rule`（错值 `delta_source=2.0`、`delta_target=2000`；错单位 `thousand`）逐条相符；`answer` 文本为 `sort_keys` + 紧凑分隔符的规范化序列化，逐条可复现。

**结论**：未预设 24，实际穷举 16，声明与条目自洽。

### 1.2 逐条 pre/post 归因

以 `checker_v2.py`（SHA-256 `aeedf62b…d048`，见 §3）判定序为基准，**16 例全部独立手推演**（不跑代码），结果与收据 `pre_outcome` / `post_outcome` / `transition` / `changed` **逐字段吻合，0 处偏差**。详见 §4。

### 1.3 变更集合与 correct-class 安全性

| 项 | 收据声明 | 本轮复算 | 判定 |
|---|---:|---:|---|
| `case_count` | 16 | 16 | ✓ |
| `changed_count` | 5 | 5 | ✓ |
| `unchanged_count` | 11 | 11 | ✓ |
| `transition_counts` | `{"wrong_period->wrong": 5}` | 同 | ✓ |
| `non_allowed_transition_count` | 0 | 0 | ✓ |
| `correct_class_flip_count` | 0 | 0 | ✓ |

- **变更集合逐条为 `wrong_period`→`wrong`**：5 条变更全部落在 equivalent-form 侧，无任何其他迁移类型，无反向翻转。
- **`correct*` 翻转 = 0**：`checker.py:43` 定义 `CORRECT_OUTCOMES = {"correct", "correct_other_form"}`。矩阵中属 correct 类的恰有 2 例（`equivalent_form_…_target_correct_unit_correct` = `correct_other_form`；`direct_form_…_target_correct_unit_correct` = `correct`），二者 pre == post、`changed = false`，故按收据自定义的翻转判定（"changed case whose pre or post outcome belongs to CORRECT_OUTCOMES"）计 0 正确。该定义在收据内显式给出，与实现一致。
- 构建器 `build_s0c_strictness_matrix.py:192-196` 有 fail-closed 断言：迁移类型集合必须恰为 `{"wrong_period->wrong"}`、翻转列表必须为空，否则抛错即停 —— 与补档 §3 "任何其他变更类型或 `correct*` 翻转都会使构建器失败即停" 相符。

### 1.4 输入/输出 sha256 与重跑说明

**输入哈希（3/3 与盘上实测一致）**：

| 收据 `inputs` 键 | 声明值（前 16 位） | 本轮 `sha256sum` 实测 | 判定 |
|---|---|---|---|
| `builder_sha256` | `9bf5af883a52c8d7…` | `9bf5af883a52c8d7…` | ✓ |
| `base_checker_dependency_sha256` | `c919845b051a7cfb…` | `c919845b051a7cfb…` | ✓ |
| `post_checker_v2_sha256` | `aeedf62b7d44a142…` | `aeedf62b7d44a142…` | ✓ |

**`temporary_pre_f10_source_sha256` = `b3c7b36363386ab6…194ca3` —— 超出预期的一手闭合**：该值与 F-10 之前**真实历史文件** `checker_v2.py` 的在案钉值**逐字节相同**：

| 在案来源 | 值 |
|---|---|
| `S0B_FIX_RECEIPT.json` L129 / L1766（S0B 后 `checker_v2.py`） | `b3c7b36363386ab6a9d0be21775bd174d7a19db0e6b534347b0a2269d1194ca3` |
| `S0C_FIX_RECEIPT.json` L1812（F-10 前 `checker_v2.py`） | 同上 |
| `s0_run_fixtures_v2.py` L37（`PRE_FIX_SHA256` 钉校验） | 同上 |
| `S0B_EXECUTION_REPORT.md` L65 | 同上 |
| **本收据 `temporary_pre_f10_source_sha256`** | **同上** |

即：**"从现行 `checker_v2.py` 精确删除唯一 F-10 branch C 块" 的临时重建，字节级等于真实的 pre-F-10 源文件**。故 pre 臂不是近似重建，而是历史原件的等价复现；pre/post 差分严格只含 F-10 一处改动。本轮另证实 branch C 多行块在 `checker_v2.py` 中**唯一**（L48–52；另两处 `return {"outcome": "wrong"}` 为 L33/L73 的单行回退，不匹配该块），与构建器 `require(post_source.count(F10_BRANCH_C_SOURCE) == 1)` 一致。

**输出哈希**：`cases_payload_sha256` / `summary_payload_sha256` / `matrix_payload_sha256` **未独立重算**（见 §5.1），仅确认三值互不相同、格式合法、且与收据正文同源。

**重跑说明自洽性**：

- 收据 `rerun = {comparison_runs: 2, byte_identical: true, comparison_scope: "complete deterministic receipt payload"}` 与 `S0D_EXECUTION_REPORT.md` §4 的三步（run1 / run2 + cmp / 对落盘收据 fresh rerun + cmp）**口径一致**（收据计的是两两比较，报告另记一次对落盘件复跑，非矛盾）。
- **确定性机制经源码证实**：生成器无时间戳/随机源；字典按插入序、`sort_keys=True` 排序输出；`period_form_counts` 用 `sorted(period_forms)`、`transition_counts` 用 `sorted(set(...))`；外层 `PYTHONHASHSEED=0` 不影响结果。故 byte-identical 主张**结构上可信**。
- 落盘收据格式与 `canonical_json_bytes`（2 空格缩进 + `sort_keys` + 末尾换行）**相符**：顶层键、`cases[i]`、`input_flags`、`inputs`、`outputs`、`summary` 各层键均字母序；`wc -l` = 403 / `wc -c` = 13992，末字节为 `}\n`。
- 生成器 `require(not args.output.exists())` **拒绝覆写输出**，故盘上收据只能由一次性写入（或临时路径落位）产生，不可能被"重跑覆盖"—— 这与 §3 的未覆写结论互证。

### 1.5 观察（非判负）

- **O-1｜`withdrawn_claim` 引文不完整**：收据 `original_claim_disposition.withdrawn_claim` 为
  `"An additional 24-case strictness matrix found five changed classifications, all wrong_period -> wrong."`，
  而 `F5_EXECUTION_REPORT.md` L23 原句尾部还有 `"; no case flipped to a correct class."`。收据引文截断了后半句（并去掉了反引号）。撤回的实质范围不受影响（补档 §1 以**完整原句**为准），且被截断的部分恰好是新矩阵同样支持的 0-flip 事实；但"withdrawn_claim" 作为引文字段宜逐字完整，建议下轮补正或加注"摘引"。

---

## 2. 撤回闭环 — **PASS**

### 2.1 原句撤回（逐字核对）

补档 §1 引用块与 `F5_EXECUTION_REPORT.md` L23 原句**逐字符一致**（含反引号与分号）：

> An additional 24-case strictness matrix found five changed classifications, all `wrong_period` -> `wrong`; no case flipped to a correct class.

并明示：**"24-case" 不再作为事实引用**；撤回理由（scratch 未落盘、无生成器、无逐例结果、无重跑收据 → 不可复现、不可独立核验）成立 —— 与 round-3 §2.4 的缺口描述一致。

**尤值肯定的认识论处置**：补档明确拒绝用新矩阵的 5 条变更"追认"原 scratch 结果（"不能视为对原 scratch 结果的追认"），`S0D_EXECUTION_REPORT.md` §5 亦同（"5 的数量不能追溯性地证明原 scratch 的 24-case 产物存在"）。无夸大。

### 2.2 改引目标（两者均已核验）

| 改引目标 | 补档定位 | 哈希声明 | 本轮实测 | 内容核对 |
|---|---|---|---|---|
| 矩阵产物（builder + 收据） | §2 | 收据 `b88c7e1c…f115b` | `b88c7e1c…f115b` ✓ | 16 例 + 逐例归因，见 §1 |
| Loop C round-3 §2.2 | §4 | `bfe367cb…b420b` | `bfe367cb…b420b` ✓ | 见下 |

补档 §4 对 round-3 §2.2 的五点转述，逐条与 `WP2_F5F10_LOOP_C_AUDIT_v1.md` §2.2 原文相符：

1. "分支 A 与直接形单位门在 F-10 之前已存在" ← §2.2 哈希链（S0B 前/后 + `PRE_FIX_SHA256` 同值 → F-10 编辑起点即 S0B 终态）；
2. "branch C 仅拦截等价形中未满足既有 A/B 条件的答案" ← §2.1 判定序表（C 位于 A/B 之后、D 之前）；
3. "可达变化仅为 `wrong_period` → `wrong`" ← §2.2 穷举差分表；
4. "无 `correct*` 翻转、无反向翻转" ← §2.2 结论句；
5. "非等价形（含直接形控制）逐支未变" ← §2.2 末段。

**交叉印证强度**：round-3 §2.2 的静态分支差分表（5 行）与本轮 16 例实跑矩阵**互相吻合** —— 差分表预测的变化恰好是 `ds≠−Gds` 的 4 例 + `ds==−Gds ∧ dt≠−Gdt ∧ unit==Gtu` 的 1 例 = 5 例，与实跑 `changed_count = 5` 同值同界。静态证明与逐例实证双向一致。

### 2.3 无夸大、无新悬空断言

逐条核对补档全文断言：

| 断言 | 核对 | 判定 |
|---|---|---|
| "从现行 `checker_v2.py` 精确删除唯一 F-10 branch C 块；未修改生产路径中的 `checker_v2.py`" | builder 源码 + `checker_v2.py` mtime/哈希未变 | ✓ |
| `N = 2 × 2 × 2 × 2 = 16`（未预设总数） | 16 组合穷举核实 | ✓ |
| 16/5/11/5/0/0/0 结果表 | 与收据逐项一致（§1.3） | ✓ |
| "任何其他变更类型或 `correct*` 翻转都会使构建器失败即停" | builder `require` 两处 | ✓ |
| §5 两条 S7 建议 | 与 round-3 §6 待办 #2 / #3 逐条对应；明示"不是本轮代码修复" | ✓ |
| §6 owner 授权出处（`loop_a_prompt_f5.md` L13–16 + 2026-10-13 夜授权） | 哈希 `0b7f126b…290a4` ✓ 实测一致；L15 原文含"唯一允许的类别变化是 `wrong_period` → `wrong`，任何用例不得翻成 correct"；L4 含"owner 已授权（2026-10-13 夜）按 Loop D 默认闭环执行" | ✓ |
| "本轮 S0d 是对该授权范围内的未落盘证据补档，不扩大 S4+ 范围" | 无 S4+ 产物 | ✓ |
| §7 红线遵守（未覆写、未改 checker、零模型、未 git 操作） | §3；`git status` 显示全部产物仍为 `??` 未跟踪 → 无 add/commit 独立佐证 | ✓ |

补档未新增任何无产物支撑的实证断言。

### 2.4 观察（非判负）

- **O-2｜撤回的可发现性未闭合**：`F5_EXECUTION_REPORT.md` L23 原句仍以原文形式留在原报告中（按红线不得覆写，处置正确），撤回仅存在于新文件 `F10_STRICTNESS_MATRIX_ADDENDUM_v1.md`。但该补档**未登记进 `docs/INDEX.md`**（grep 无命中），亦未见于 `memory/THREADS.md` / `memory/STATE.md` / `logs/graph/dispatch_log.md`。从文档目录入口阅读的读者会看到 INDEX L67–68（F-5 资格 / F-10 checker 收口）而**没有指向撤回件的线索**。按 `jinrong-docs-sync` 单一入口治理建议下轮补登 INDEX 与台账。
  与 round-3 §4 的先例一致（该轮对 `WP2_TARGET_UNIT_RULES_DRAFT_v1.md` 等 3 件未进 INDEX 明确"故不判负…建议下轮补登"），故本轮同样不判负；但本轮涉及的是**撤回件**，可发现性优先级高于一般附属文档。
- **O-3｜两件被引文件的落盘时间在 S0d 写作窗口内**：`WP2_F5F10_LOOP_C_AUDIT_v1.md`（mtime `01:29:19.496`）与 `loop_a_prompt_f5.md`（mtime `01:29:19.970`）落在 builder（`01:29:13.986`）与收据（`01:29:51.186`）之间；同目录其余 12 件历史产物 mtime 各自与所属轮次相符（23:04–00:36），无此现象。
  **成因已自证**：round-3 文件头部自述"Loop C 写入通道再度被其沙箱拒绝…本文件正文区为运行日志 `~/wzh/loop_runs/tatqa-wp2-f5c-20261014/c.log` 第 2 行起的逐字节转录（`tail -n +2`，20843 bytes，未改一字）" —— 即该件系**事后转录落盘**，故 mtime 落在使用它的 S0d 轮窗口内。`loop_a_prompt_f5.md` 同批落位，性质应同为转录/落盘。
  **故**：补档 §7 "本轮只新增文件" **成立**（新增 6 件、覆写 0 件）；但对这两件的哈希钉定证明的是**落盘完整性**，而非独立成文 —— 其独立性来源是 round-3 运行日志本身。本轮未越界读取该日志（工作目录外），转录保真度列入 §5.5。
  **另注**：owner 授权的**存在性**另有 pre-S0d 一手旁证 —— `F5_EXECUTION_REPORT.md` L4（mtime `00:36:45`）载 `authorization: owner default closure, authorized 2026-10-13 night`，早于 S0d 窗口，故不受本观察影响。

---

## 3. 未覆写 — **PASS**

### 3.1 受保护文件哈希对照

| 文件 | 本轮实测 | 在案基线 | 基线来源（**pre-S0d**） | 判定 |
|---|---|---|---|---|
| `S0_FIX_RECEIPT.json` | `1085cde79b30…1c50` | `1085cde7…` | round-3 审计 §1 表 L134（逐个 `sha256sum` 比对，13/13 吻合） | **未动** |
| `S0B_FIX_RECEIPT.json` | `b759a5e74b1d…2c17` | `b759a5e7…` | round-3 审计 §1 表 L135 | **未动** |
| `S0C_FIX_RECEIPT.json` | `a6b888177557…264f` | `a6b88817…` | round-3 审计 §1 表 L133 | **未动** |
| `F5_EXECUTION_REPORT.md` | `c26f42224601…8c5f` | 见下 | 无 pre-S0d 全文钉值 | **未动**（证据链见 §3.2） |

三份收据的基线取自 round-3 审计（其正文先于 S0d 轮），故为**独立于 S0d 的第三方钉值**，非被审对象自述。另有双重钉：`s0_run_fixtures_v2.py:45,48` 内置 `PINNED_RECEIPT_SHA256`，runner 写 S0C 前后各校验一次、只写 `S0C_FIX_RECEIPT.json`。

### 3.2 `F5_EXECUTION_REPORT.md` 未动的证据

无 pre-S0d 全文哈希钉值（该件按其 §2 自述"不嵌入自身 SHA-256"），改以四路旁证：

1. **内容未被抹除**：L23 的 "24-case" 原句**仍在原处**（本轮 rg 命中）。若 S0d 覆写该件，最可能的动作是删除该句 —— 实际未删，与"以新文件撤回、不改历史件"的处置一致；
2. **mtime 早于 S0d 窗口**：`2026-10-14 00:36:45`，而 S0d 产物窗口为 `01:29:13`–`01:32:18`；
3. **自钉哈希仍全部吻合**：该件 §2 所列 10 件产物 + 3 件输入哈希，round-3 曾逐个 `sha256sum` 比对得 13/13 吻合；本轮再抽 3 件（S0/S0B/S0C）复测一致，`checker_v2.py` = `aeedf62b…` 亦与其 L33 声明一致；
4. **S0d 侧的声明与实测一致**：`S0D_EXECUTION_REPORT.md` §3 钉其 `c26f4222…8c5f`，与本轮实测相符。

### 3.3 其他被保护面

| 检查 | 结果 |
|---|---|
| 现行 `checker_v2.py` 是否被改 | 否 —— 哈希 `aeedf62b…` 与 F5 报告 L33、round-3 §2.2 的"F-10 后"值一致；mtime `00:26:29` 早于 S0d 窗口 |
| builder 是否会覆写既有产物 | 否 —— `require(not args.output.exists())` 拒绝写已存在输出；对 `checker_v2.py` / `checker.py` 仅 `read_text` |
| 临时 pre 文件是否清理 | 是 —— `finally: temporary_path.unlink()` + `require(not temporary_path.exists())`；写入系统临时目录，不落仓 |
| git 操作 | 无 —— 全部 S0d 产物在 `git status` 中为 `??` 未跟踪，未 add/commit/push |
| 其他历史件（`WP0_TATQA_ADAPTER_CHECKER_CONTRACT…`、`WP1_PREFREEZE_*`、`WP2_PREFREEZE_*`、`WP2_TARGET_UNIT_RULES_DRAFT`、`WP2_F5_ELIGIBILITY_DECISION`、`S0B_EXECUTION_REPORT`、`WP2_PREFREEZE_EXECUTION_REPORT` 等 12 件） | mtime 各自与所属轮次相符（23:04–00:28），无 S0d 窗口写入 |

---

## 4. 手推演（力所能及）— **PASS**（超配额：16/16）

配额为 1–2 例；实际对**全部 16 例**做了 pre/post 归因手推演（不跑代码），与收据**逐字段 0 偏差**。基准：`checker_v2.score_prepared` 判定序（`checker_v2.py:24-73`）。

**Gold（由 `make_base_item` + builder 断言 + 表值推得）**：表 `["Revenue","2.5","1.2"]`，`late=2025: 2.5`、`early=2024: 1.2` → `delta_source = 2.5−1.2 = 1.3`；`source_unit="thousand"`→`target_unit="unit"`（×1000）→ `delta_target = 1300`；`gold.target_unit = "unit"`。故等价形（`periods=[early,late]`）的正确取负为 `(-1.3, -1300)`，直接形（`periods=[late,early]`）为 `(1.3, 1300)`。

**判定序**（pre = 删除 branch C）：

| 序 | 守卫 | 归因 | pre 是否含 |
|---|---|---|---|
| A | `periods==[early,late]` ∧ `ds==−Gds` ∧ `unit≠Gtu` | `wrong_unit` | 含 |
| B | `periods==[early,late]` ∧ `ds==−Gds` ∧ `dt==−Gdt` | `correct_other_form` | 含 |
| **C** | **`periods==[early,late]`** | **`wrong`** | **不含（F-10）** |
| D | `periods≠[late,early]` | `wrong_period` | 含 |
| E | `ds==Gds` ∧ `dt≠Gdt` | `wrong_unit` | 含 |
| F | `ds==Gds` ∧ `dt==Gdt` ∧ `unit≠Gtu` | `wrong_unit` | 含 |
| G | `ds==Gds` ∧ `dt==Gdt` ∧ `unit==Gtu` | `correct` | 含 |
| — | 其余 | `wrong` | 含 |

### 详证例 1（变更例）：`equivalent_form_source_correct_target_wrong_unit_correct`

答案 `{"row":"Revenue","periods":["2024","2025"],"delta_source":"-1.3","delta_target":"2000","unit":"unit"}`

- row `"Revenue"` 相符 → 不走 row 门；
- A: `periods` ✓、`ds(-1.3) == −Gds(−1.3)` ✓、`unit("unit") ≠ Gtu("unit")`？**否** → 不触发；
- B: `dt(2000) == −Gdt(−1300)`？**否** → 不触发；
- **C（post）: `periods == ["2024","2025"] == [early,late]` → `wrong`** ✓ 与 `post_outcome` 相符；
- **pre（无 C）**: 落到 D，`periods ≠ ["2025","2024"]` 成立 → `wrong_period` ✓ 与 `pre_outcome` 相符。

→ `changed = true`，`transition = wrong_period->wrong` ✓ 与收据一致。此例正是 F-5 fixture 形态（等价形、期间合法、双 delta 错、单位对）在矩阵中的对应格。

### 详证例 2（未变例，验分支 A 先于 C）：`equivalent_form_source_correct_target_wrong_unit_wrong`

答案 `{"row":"Revenue","periods":["2024","2025"],"delta_source":"-1.3","delta_target":"2000","unit":"thousand"}`

- A: `periods` ✓、`ds == −1.3` ✓、`unit("thousand") ≠ Gtu("unit")` ✓ → **`wrong_unit`**（A 在 pre/post 两侧均存在）；
- 因被 A 捕获，**永不达 C** → pre = post = `wrong_unit`，`changed = false` ✓ 与收据一致。

此例证明 branch C 未遮蔽既有单位门归因 —— 与 round-3 §2.2 差分表 `== / ≠ / ≠` 行相符。

### 控制例（直接形）：`direct_form_source_correct_target_wrong_unit_correct`

答案 `{"periods":["2025","2024"],"delta_source":"1.3","delta_target":"2000","unit":"unit"}`

- A/B/C 均要求 `periods==[early,late]` → 一律不触发；
- D: `periods == [late,early]` → 不触发；
- E: `ds(1.3)==Gds` ✓、`dt(2000)≠Gdt` ✓ → `wrong_unit`（两侧同）→ `changed = false` ✓。

### 16 例汇总（本轮推演值 = 收据值，16/16 一致）

| # | case_id（简记） | pre | post | 变化 | 收据相符 |
|---|---|---|---|---|---|
| 1 | eq / src✗ tgt✗ unit✗ | `wrong_period` | `wrong` | **`wrong_period`→`wrong`** | ✓ |
| 2 | eq / src✗ tgt✗ unit✓ | `wrong_period` | `wrong` | **`wrong_period`→`wrong`** | ✓ |
| 3 | eq / src✗ tgt✓ unit✗ | `wrong_period` | `wrong` | **`wrong_period`→`wrong`** | ✓ |
| 4 | eq / src✗ tgt✓ unit✓ | `wrong_period` | `wrong` | **`wrong_period`→`wrong`** | ✓ |
| 5 | eq / src✓ tgt✗ unit✗ | `wrong_unit`(A) | `wrong_unit`(A) | 无 | ✓ |
| 6 | eq / src✓ tgt✗ unit✓ | `wrong_period` | `wrong` | **`wrong_period`→`wrong`** | ✓ |
| 7 | eq / src✓ tgt✓ unit✗ | `wrong_unit`(A) | `wrong_unit`(A) | 无 | ✓ |
| 8 | eq / src✓ tgt✓ unit✓ | `correct_other_form`(B) | `correct_other_form`(B) | 无 | ✓ |
| 9–12 | dir / src✗ ×{tgt,unit} | `wrong` | `wrong` | 无 | ✓ |
| 13–15 | dir / src✓ tgt✗ 或 tgt✓ unit✗ | `wrong_unit` | `wrong_unit` | 无 | ✓ |
| 16 | dir / src✓ tgt✓ unit✓ | `correct`(G) | `correct`(G) | 无 | ✓ |

变更 5 条（#1–4、#6）全为 `wrong_period`→`wrong`；correct 类两例（#8、#16）均未变；direct-form 8 例 0 变更。**与收据 `summary` 完全一致。**

**标签语义提示（非缺陷）**：`input_flags.unit_correct` 描述的是答案 `unit` 字段是否等于 `gold.target_unit`（构造维度），而结果标签 `wrong_unit` 是 checker 词表中的**归因类别**，其 E 分支表示"源对、目标错"（量纲/换算类误差）。故 #13–15 出现 `unit_correct: true` 却得 `wrong_unit` 并不矛盾；但对不读源码的读者是陷阱，建议后续收据加一行标签语义说明。

---

## 5. 未验证面（本轮明示）

1. **`cases_payload_sha256` / `summary_payload_sha256` / `matrix_payload_sha256` 未独立重算** —— 本沙箱禁止 `python`/`jq`/管道写文件，无法重建 `json.dumps(indent=2, sort_keys=True)` 的 canonical 序列化。三项输出哈希仅为收据自述。**缓解**：收据正文结构（§1.1–1.3）已逐条独立核对，正文被篡改而三个哈希仍自洽的窗口极窄。
2. **`item_template_sha256` 未重算** —— item 模板文本已在 builder 中核对，但其 canonical 哈希同 §5.1 原因未重算。
3. **`temporary_pre_f10_source_sha256` 未由本轮自行求哈希** —— 受 §5.1 同一限制；改以**跨件等值**佐证（= S0B/S0C/runner 在案的 pre-F-10 钉值 `b3c7b363…`，见 §1.4）。若该重建有误，其哈希几乎不可能与四件历史钉值相等。
4. **收据 byte-identical 重跑未复跑** —— 跑生成器属执行动作，且会写输出文件，超出本轮"只读"红线；改由确定性机制（§1.4）+ 落盘格式相符间接支撑。
5. **round-3 转录保真度未验** —— `~/wzh/loop_runs/tatqa-wp2-f5c-20261014/c.log` 在工作目录外，沙箱拒绝访问；"20843 bytes 逐字节转录、未改一字" 未一手核对。**缓解**：本轮对 §2.2 五点转述逐条比对原文相符，且严格性界由 §4 手推演独立成立，不依赖该件字节。
6. **`docs_lint.py` 的 `PASS (0 fail / 14 warn)` 未复跑** —— 需 python；`S0D_EXECUTION_REPORT.md` §4 的 lint 结论为自述。
7. **零模型/零网络/零数据库调用** 为执行轮自述（`S0D_EXECUTION_REPORT.md` §7 计数全 0），本轮无独立遥测可证；产物形态与"零调用"一致（无 run_log、无模型输出）。

---

## 6. 观察与移交项（均不判负）

| # | 事项 | 严重度 | 建议处置 |
|---|---|---|---|
| O-1 | 收据 `withdrawn_claim` 截断原句（缺 `; no case flipped to a correct class.`） | 低 | 下轮补正为逐字全文，或标注"摘引" |
| O-2 | 撤回件 `F10_STRICTNESS_MATRIX_ADDENDUM_v1.md` 未登记 `docs/INDEX.md` / 台账，撤回不可经目录发现 | **中**（可发现性） | 按 `jinrong-docs-sync` 补登 INDEX 一行（描述宜含"撤回 F5 执行报告 24-case 断言"），并在 `memory/THREADS.md` 记一项处置 |
| O-3 | 两件被引文件（round-3 审计、owner 卡）系 S0d 窗口内转录落盘；哈希钉定证落盘完整、不证独立成文 | 低（已自证成因） | 移交时注明独立性来源为 round-3 运行日志；若需一手闭合，可补验 `c.log` 转录保真度 |
| S7 遗留（补档 §5 已列） | `prepare_item`/`recompute_gold` 加 `late != early` fail-closed 断言；runner 携带 pre-fix 实跑路径 | 低（当前数据 0 例退化周期） | 与 round-3 §6 #2/#3 合并入 S7 清单，本轮不修 |
| 标签语义 | `unit_correct` 构造旗标 vs `wrong_unit` 归因类别易误读 | 低 | 收据加一行标签语义说明 |

**放行意见**：S0d 补档达到 round-3 §6 #1 要求的"补档并钉哈希 **或** 撤回该句"两条路径**均已满足**，且附有独立交叉证明。本报告**同意宣告 S0d 证据缺口闭合**，不因此阻塞后续轮次。O-2 为唯一建议尽快处置项（一行 INDEX + 一条台账），属文档治理，不影响证据成立。item freeze 仍为 S7；split 仍 `DRAFT_NOT_FROZEN`；本报告不授权任何 S4+ 动作。

---

## 7. 调用计数

| 类型 | 计数 |
|---|---:|
| model calls | 0 |
| endpoint calls | 0 |
| judge calls | 0 |
| network calls | 0 |
| database calls | 0 |
| service restarts/probes | 0 |

只读工具使用：`git status`、`ls`、`sha256sum`、`grep`、`sed -n`、`wc`、`tail`、`rg`、文件读取。未运行任何 Python/生成器/lint；未写入被审对象与历史文件；本报告因写入被沙箱拒绝而未落盘（按任务卡转录入答复）；未 git add/commit/push。

---

### 复查要点速览

- **最强证据**：收据的 `temporary_pre_f10_source_sha256` = `b3c7b363…`，与 S0B/S0C/runner 四处在案的 **pre-F-10 历史钉值逐字节相同** —— 临时重建等价于真实历史原件，pre/post 差分严格只含 F-10 一处。
- **超配额**：16/16 例手推演全吻合（配额只要求 1–2 例），变更集恰为 5 条 `wrong_period`→`wrong`，correct 类 2 例均未变。
- **撤回**：补档 §1 与 F5 L23 原句逐字符一致，且明确拒绝用新矩阵"追认"旧 scratch —— 认识论处置干净。
- **未覆写**：S0/S0B/S0C 对 round-3 第三方钉值 3/3 一致；F5 未动（四路旁证）；builder 设计上拒绝覆写输出；全部产物仍 `??` 未跟踪。
- **主要移交项（O-2，中）**：撤回件未进 `docs/INDEX.md`/台账，从目录入口看不到撤回 —— 建议补一行 INDEX + 一条 `THREADS.md`。
- **未验证面**：payload/item/pre-source 三个哈希未自行重算（沙箱禁 python/jq）、重跑未复跑、round-3 转录保真度未验、lint 未复跑。
