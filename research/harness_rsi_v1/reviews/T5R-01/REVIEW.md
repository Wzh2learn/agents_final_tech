# T5R-01 独立评审报告 — harness_rsi_v1 T5「R 两个对象接口」

- **review_id**: T5R-01 | **task_id**: T5 | **被审 run**: `research/harness_rsi_v1/runs/T5/20261014T195445Z_60c8e213/`（提交 `7f0bb9a0c`）
- **reviewer**: Loop C 独立质量审计层（GB10）| **runtime**: Linux 6.17.0-1018-nvidia / Python 3.12
- **评审性质**: 只读独立评审。不修改仓库与被审包、不 git 写、不联网、不调模型/生产/数据库、不进入 T6。仅出提案。

---

## 1. 范围与方法

**范围**：T5 run 全部 34 个交付文件 + 依赖事实（T4 v2 run、`reviews/T4R-01/`）+ 契约（`cards/T5.md`、`contracts/*`、`evaluation/reliability_spec.md`、`docs/governance/FORMAL_EXPERIMENT_PREFLIGHT_V1.md`）。

**方法**：
1. **独立复算，不采信声明** — 计数、SHA-256、字节、git blob 身份全部由我现算；哈希用三方交叉：字节派生 git blob SHA-1（`sha1("blob <len>\0"+bytes)`）／手工解析 `.git/index`（v2 索引、3775 条目、处理 8 字节对齐填充）／`git rev-parse HEAD:<path>`。
2. **实弹复跑** — 用交付的 `run_probes.py` + `caller_validator.py` 在我自己的 scratch 重跑；再用自建逐例 harness（不早退）跑完全部 17 用例；再自构造 **20 个新对抗用例**。
3. **反证优先** — 假定声明为假，专攻"实现-测试同错""为过而过的负例""宽松放行的正例"。
4. **只写仓库外** — `/home/testuser/wzh/loop_runs/t5r01_recheck_a/`（详见 §8 披露）。

**判级词汇**：依 `FORMAL_EXPERIMENT_PREFLIGHT_V1.md`，一切 PASS 带级别+范围；不使用裸 PASS；不声称 `END_TO_END_PREFLIGHT_PASS` / `FORMAL_RUN_PASS`。

---

## 2. 逐项复算结果

### 2.1 计数与哈希 — PASS(CONTRACT)，范围：run 包字节与 manifest 等价

| 检查 | 命令/方法 | 结果 | 退出码 |
|---|---|---|---|
| run 文件数 | `python3` rglob 计数 | 交付 **34**；评审时磁盘 35（+2 见 §8） | 0 |
| manifest 条目 | `artifacts_manifest.json` 解析 | 33 条，`self_hash_policy` 自排除 | 0 |
| 逐条 SHA-256+bytes | 独立实算 vs 声明 | **33/33 全等**，0 失配 | 0 |
| 无遗漏/多余 | 集合差 | `in_manifest_not_disk=[]`；`in_disk_not_manifest` 仅 `artifacts_manifest.json`（自排除，合规） | 0 |
| 重复 relative_path | set 比较 | 无重复 | 0 |
| worktree ≡ HEAD | 字节→blob SHA-1 vs `git rev-parse` | **34/34 全等** | 0 |

结论：包内字节完整、manifest 诚实、无伪造签署。

### 2.2 input_bindings 与依赖 — PASS(CONTRACT)，范围：tracked 身份绑定

17 条绑定全部三方一致（declared = bytes-derived = `.git/index` = `git rev-parse`），含 `sha256_file`（4 条）亦全等：

- 卡片 6 输入：`protocol.json` `c57937c8…`、`authority_map.json` `46acca7e…`、`execution_policy.md` `e0569763…`、`budget_profiles.json` `64634474…`、`schemas.json` `07731a30…`、`reliability_spec.md` `fd2c1fdf…`
- `cards/T5.md` `082ff999…`；`FORMAL_EXPERIMENT_PREFLIGHT_V1.md` `6d23e8d9…`
- T4 v2：`receipt.json` `14278b2a…` / sha256 `e9d4aa29…`、`baseline.json` `3ea99e45…` / `41ff78e4…`、`baseline_recipe.json` `ebe9231a…` / `65bc9332…`
- T4R-01：`ACCEPTANCE_PROPOSAL.json` `6bcb7812…`、`review_receipt.json` `caebf7f1…`
- 身份件：T3 `runner.py` `3708a4e6…`、T3 `receipt.json` `a5f98d0d…`、T2 `evaluate.py` `3d296b0b…`、T2 `receipt.json` `891955a6…`

**3/3 登记操作目标**（`c5045e95…` / `9f421f69…` / `7a3c9d1d…`）、**6/6 contract_sources**、**3/3 probe_definitions 契约源** 全部三方一致。

**freeze 一致**：`282f52133a682e927c82b771fa103c27da34db7acbd8a12d2921f42a6d0bf36b` 在 `protocol.json.freeze_sha256`、`recipe_interfaces.json`、`receipt.json`、两个 call 夹具、`caller_validator.py` 常量共 **6 处全等**。

**T4R-01 依赖事实**：`decision=ACCEPTED`；`blocking_items=[]`（0）；`review_receipt.verdict=ACCEPTED`。✔

> 注：receipt 对 `execution_policy.md` 已如实披露派发原文写作 `execution_policy.json` 的措辞差异。披露诚实（FACT）。

### 2.3 核心 — 接口闭合与调用方校验（实弹）

#### (a) 交付探针复跑 — **未能复现 17/17**

```
python3 run_probes.py --run-root <RUN> --definitions recipe_fixtures/probe_definitions.json \
        --output <reviewer_scratch>/reviewer_probe_pass_1.jsonl --round-id PASS_1   → exit 3
python3 run_probes.py ... --round-id PASS_2                                        → exit 3
```
`run_probes.py` 在首个失败即 `return 3`，两轮均止于 P01，仅 1 行记录。

改用自建逐例 harness（不早退，同一 `caller_validator.py`，同一 `--run-root`）复跑全部 17 例：

| 用例 | 期望 | 实测 | fail_closed_code | 判定 |
|---|---|---|---|---|
| **P01-PRECHECK-VALID** | ACCEPT | **REJECT** | `FC_OPERATION_TARGET_FAILURE` | **失败** |
| P02 unregistered-op | REJECT | REJECT | `FC_UNREGISTERED_OPERATION` | ✔ |
| P03 shell-injection | REJECT | REJECT | `FC_SHELL_OR_COMMAND_INJECTION` | ✔ |
| P04 range 61 | REJECT | REJECT | `FC_PARAMETER_OUT_OF_RANGE` | ✔ |
| P05 type "2" | REJECT | REJECT | `FC_PARAMETER_TYPE_MISMATCH` | ✔ |
| P06 missing-field | REJECT | REJECT | `FC_MISSING_REQUIRED_FIELD` | ✔ |
| P07 wrong-hash | REJECT | REJECT | `FC_HASH_BINDING_MISMATCH` | ✔ |
| P08 arbitrary-path | REJECT | REJECT | `FC_ARBITRARY_PATH` | ✔ |
| **E01-DELIVERY-VALID** | ACCEPT | **ACCEPT** | — | ✔ |
| E02 unregistered-op | REJECT | REJECT | `FC_UNREGISTERED_OPERATION` | ✔ |
| E03 shell-injection | REJECT | REJECT | `FC_SHELL_OR_COMMAND_INJECTION` | ✔ |
| E04 missing-scientific | REJECT | REJECT | `FC_MISSING_REQUIRED_FIELD` | ✔ |
| E05 wrong-package-hash | REJECT | REJECT | `FC_HASH_BINDING_MISMATCH` | ✔ |
| E06 forged-summary | REJECT | REJECT | `FC_FORGED_SUMMARY_MISMATCH` | ✔ |
| E07 single-overall-pass | REJECT | REJECT | `FC_SINGLE_OVERALL_PASS_FORBIDDEN` | ✔ |
| E08 parameter-type | REJECT | REJECT | `FC_PARAMETER_TYPE_MISMATCH` | ✔ |
| E09 arbitrary-path | REJECT | REJECT | `FC_ARBITRARY_PATH` | ✔ |

**实测 16/17**。15 个负例 **全部以与探针定义逐字一致的 fail_closed_code 被拒**；E01 接受。唯一失败为 P01 → 见 **BLOCKING-1**。

#### (b) 独立对抗探针（自构造 20 个，全部**新**构造、不在 `probe_definitions.json` 内）

| 新用例 | 攻击面 | 实测 | code | 结果 |
|---|---|---|---|---|
| X01 新造未登记 `OP-T5-R-ARBITRARY-EVAL` | 注册表封闭性 | REJECT | `FC_UNREGISTERED_OPERATION` | 拒 ✔ |
| X02 反引号 `` watcher.sh`id` `` | shell 注入变体 | REJECT | `FC_SHELL_OR_COMMAND_INJECTION` | 拒 ✔ |
| X03 换行注入 `tick.json\n/bin/true` | shell 注入变体 | REJECT | `FC_SHELL_OR_COMMAND_INJECTION` | 拒 ✔ |
| X04 自由命令参数 `command="rm -rf /"` | 任意 shell 入口 | REJECT | `FC_PARAMETER_TYPE_MISMATCH` | 拒 ✔ |
| X05 篡改 `package_sha256`（格式合法） | 哈希绑定 | REJECT | `FC_HASH_BINDING_MISMATCH` | 拒 ✔ |
| **X06 自洽伪造摘要**（text 与正确 hash 同时伪造） | **伪造摘要** | **ACCEPT** | — | **穿透 ✘** |
| X07 caller_context 与 recipe 不符 | 对象边界 | REJECT | `FC_RECIPE_OBJECT_MISMATCH` | 拒 ✔ |
| X08 `recipe_fixtures/../../T4/x.json` | 路径穿越 | REJECT | `FC_ARBITRARY_PATH` | 拒 ✔ |
| X09 `max_tick_age_minutes=true` | 类型严格性 | REJECT | `FC_PARAMETER_TYPE_MISMATCH` | 拒 ✔ |
| X10 删除第二个 operation | 操作序完整性 | REJECT | `FC_RECIPE_OBJECT_MISMATCH` | 拒 ✔ |
| X11 偷运 `scientific.claim` | 四类分离 | REJECT | `FC_SINGLE_OVERALL_PASS_FORBIDDEN` | 拒 ✔ |
| X12 audit 类混入 `scientific_status` | 四类分离 | REJECT | `FC_SINGLE_OVERALL_PASS_FORBIDDEN` | 拒 ✔ |
| **X13 新合法正例**（交付 recipe 重序列化） | 正例接受 | **ACCEPT** | — | **接受 ✔** |
| X14 precheck `max_tick_age_minutes=60` | 边界值 | REJECT | `FC_OPERATION_TARGET_FAILURE` | 见 ADVISORY-2 |
| X15 跨 recipe 注入已登记操作 | 操作/对象错配 | REJECT | `FC_RECIPE_OBJECT_MISMATCH` | 拒 ✔ |
| X16 op_id 与参数形状不匹配 | 参数耦合 | REJECT | `FC_RECIPE_OBJECT_MISMATCH` | 拒 ✔ |
| X17 参数键集加宽 `extra_argv=--staged` | 自由 argv | REJECT | `FC_PARAMETER_TYPE_MISMATCH` | 拒 ✔ |
| X18 重复 JSON 字段 | 严格解析 | REJECT | `FC_INPUT_NOT_JSON_OBJECT` | 拒 ✔ |
| X19 非对象 JSON `[1,2,3]` | 严格解析 | REJECT | `FC_INPUT_NOT_JSON_OBJECT` | 拒 ✔ |
| X20 非法常量 `NaN` | 严格解析 | REJECT | `FC_INPUT_NOT_JSON_OBJECT` | 拒 ✔ |

**≥1 新合法正例被接受（X13）** ✔；**≥3 新负例被拒** ✔（实测 18 拒）。但 **X06 穿透** → **BLOCKING-2**。

**所有拒绝均 `target_execution_performed=false`、`operation_results=[]`** — 接口错误确在目标执行前被调用方发现。

#### (c) "不能执行任意 shell" — PASS(COMPONENT)，范围：registry 封闭词表 + 调用方 argv 构造

- `caller_validator.execute_operation` 用 **列表 argv、`shell=False`、解释器硬编码 `/usr/bin/bash`**；argv 形状按 `op_id` 固定，仅注入**已解析**的枚举路径（`Path`）与 `int`。调用方无法选择/改写解释器、argv 前缀、环境或目标。
- 操作目标非空且**仅 3 个**：`OP-T4-R-DISPATCH-PRECHECK` / `OP-T4-R-SUMMARY-GUARD-CHECK` / `OP-T4-R-SUMMARY-GUARD-DERIVE`。
- `registered_operations.json` 抽查 **3/3 含**：`allowed_parameters`（`relative_path_enum` 封闭枚举 + `integer_range` 0..60 + `required` + `shell_forbidden:true`）、`forbidden_parameter_forms`、`side_effect_class: READ_ONLY`、`verification_level: COMPONENT_PASS` + `scope` + `unverified`。另有 `global_constraints` 13 项禁止声明与 `excluded_operations` 5 条排除项（含 `loop_b_verify.sh`、`governance_drift_scan.py`、`generate_repository_receipt.py`、生产端点）。
- 实证：X04（自由命令）、X17（`extra_argv`）、X02/X03（shell 元字符）全拒。

#### (d) G1 与派生对照 — PASS(COMPONENT)，范围：本 run 内 Markdown

```
python3 scripts/graph/hooks/summary_recompute_guard.py check <path>    （逐个 .md）
```
| 文件 | rc | 守卫输出 |
|---|---|---|
| `TASK_PROMPT.md` | **0** | 无 SUMMARY-GUARD 块, 跳过 |
| `recipe_fixtures/README.md` | **0** | 无 SUMMARY-GUARD 块, 跳过 |
| `recipe_fixtures/summary/good_summary.md` | **0** | 1 收据块复核通过 |
| `summary.md` | **0** | 无 SUMMARY-GUARD 块, 跳过 |

**4/4 rc=0** ✔（与 receipt `G1_MARKDOWN_GUARD` 一致）。

**内存派生坏摘要对照**（经 T4 既有派生适配器，不落盘失配 `.md`）：
```
/usr/bin/bash .../summary_guard_derive_check_adapter.sh <good_summary.md>
→ wrapper rc 0；guard_rc=1；derived_md_removed=true
→ FAIL 数字失配: request_count = 4 (收据声称 3)
```
包内文件集 35→35 不变；`/tmp/t4-v2-summary-mismatch*` 无残留；**包内无失配收据块 `.md`**（唯一带 SUMMARY-GUARD 块者声称 `request_count = 4`，与 `effect_artifact.json` 的 `request_count: 4` 及 sha256 `a358bc70…` 一致）。wrapper/target 退出码分列，规避 T4R-01 A2 字段混淆。✔

### 2.4 A1 / A2 / A3 / A-common 逐条

| 断言 | 判定 | 级别 | 范围 |
|---|---|---|---|
| **A1** 一个 recipe 一对象；不能任意 shell | **PASS** | CONTRACT | 两 recipe `only_object:true`、`object_id` 互斥，且各自 `explicitly_not_responsible_for` 明列排除面；P02/P03/P08/E02/E03/E09 + X01/X02/X03/X04/X08/X15/X16/X17 共 14 个边界负例在目标执行前被拒。**不含**科学测量、C/S 评分、正式资格、推广。 |
| **A2** 接口错误调用方可见；伪造摘要不能通过 | **FAIL** | CONTRACT | 前半成立（15/15 负例码精确、20 新对抗用例 19 拒且均 `target_execution_performed=false`）。**后半不成立**：X06 自洽伪造摘要被接受并执行目标操作 → **BLOCKING-2**。 |
| **A3** 不修改 C/S 评分、旧实验组件、冻结件 | **PASS** | CONTRACT | 17 条 tracked 绑定 + 3 条 op 目标哈希三方一致；worktree ≡ HEAD 34/34；`git status --porcelain` 无任何 `runs/T5/<run_id>/` 之外的本次写入（脏项仅既有 `logs/graph/`×4 与未提交 T4 v1 目录×32，均 pre-existing 且已披露）。`registered_operations` 声明 `repository_write_forbidden`/`git_index_mutation_forbidden`。 |
| **A-common** JSON/必需字段/路径/哈希/越界/未知项 | **PASS** | CONTRACT | 全部 JSON 解析成功；`strict_object` 拒重复字段、`reject_constant` 拒 NaN/Infinity（X18/X19/X20 实证）；路径仅 run-root 下封闭枚举且 `resolve()` 防 symlink 逃逸；manifest 33/33 哈希+字节实算一致；无写入越界；`unresolved` 显式列 7 项。 |

**级别纪律**：receipt 12 条 checks 全部带 `verification_level`（11×CONTRACT_PASS + 1×COMPONENT_PASS），**无裸 PASS**；`unresolved` 明写 "END_TO_END_PREFLIGHT_PASS and FORMAL_RUN_PASS are not claimed"。✔

### 2.5 T4 消费约束（T4R-01 A1）— PASS(CONTRACT)，范围：派生汇总字段排除

`grep` 全包（.py/.json/.md/.jsonl/.sh）对 `combination_results` / `failure_family_profiles`：

- **仅出现在禁止性声明中**：`recipe_interfaces.design_principle.baseline_consumption`、`receipt.input_bindings[].consumption_rule`（"Use .cases[] only; do not trust summary.combination_results or summary.failure_family_profiles."）、`events.jsonl` 第 4 条、`receipt.dependency_acceptance.T4.advisory_A1_applied`。
- **无任何代码读取这两个字段**。`scratch/self_check.py` 只验绑定哈希，根本不解析 `baseline.json` 内容。

**独立案级重算**（我自算，不采信声明）：`baseline.json.cases[]` 16 行，`cases[].case_result` 计数 → `detected=6, missed=2, not_applicable=2, unverified=6`，与 receipt/summary 宣称**完全一致**。

> **重要限定**：该数值与派生字段 `baseline.summary.case_results` **恰好相同**，故单凭数值无法区分读取来源。但我已从 `cases[].case_result` 独立复现同一计数，且包内无读取被禁字段的代码路径，故**实质合规**。另：TASK_PROMPT 措辞"以 case-level `case_results` 为准"字面指向 `summary.case_results`（实为派生字段），T5 正确解析为真案级 `cases[]` 并在 receipt 写明 `consumption_rule`。措辞精确化见 ADVISORY-5。

### 2.6 对抗面

| 项目 | 结果 |
|---|---|
| 交付字段四类分离 | **精确**：`delivery_fields` 键 = {qualification, audit, execution, scientific, overall_pass_field_forbidden}；两 recipe 各自 `status_field`/`allowed_values`/`required_fields` 独立，互不混入（`*_mixed_in:false`）；`overall_pass_field_forbidden:true`；`scientific.claim_must_be:null`。X11/X12 实证强制。 |
| 无单一总体 PASS | `overall_pass_field_forbidden:true` + E07/X11/X12 拒绝 ✔ |
| frozen_protections 覆盖 reliability_spec 硬门 | **7/7 全覆盖**：FP-CRITICAL-MISS-ZERO↔严重缺陷漏检=0；FP-FALSE-BLOCK-CEILING↔合法案例误拦不高于基线；FP-EVIDENCE-COVERAGE↔证据完整率=100%；FP-CLAIM-OVERRIDE-ZERO↔主张越级=0；FP-RAW-RECORD-INTEGRITY↔原始记录完整性=0；FP-BUDGET-INTEGRITY↔预算完整性=0；FP-COST-RECORD↔验证成本（耗时/调用量/token）完整记录。两 recipe 各引用全部 7 项，仅声明不评分 ✔ |
| 探针契约来源为真实调用方形态 | `recipe_interfaces.contract_sources` 6 项 + `probe_definitions.contract_sources` 3 项，**9/9 blob_id 三方复算一致**；README 明写来源（T4 `baseline_recipe.json` 真实 adapter argv、T3 runner 有界 CLI/fail-closed、T2 evaluator 输入契约）非实现者想象 ✔ |
| 修复记录多样件与披露一致 | 6 条修复；证据件多样：`probe_results_pass1_retry.jsonl` / `_final` / `_final2` / `_final3` / `artifacts_manifest_attempt1.json` + 0 字节 `probe_results_pass1.jsonl`（对应修复#1）。`manual_implementation_repair_runs=5` + `final_self_check_repairs=1` = 6 ✔（2 条仅叙述，见 ADVISORY-4） |
| usage 零声明与探针计数自洽 | 34 caller processes = 17×2 ✔；8 op invocations = 2 正例×2 操作×2 轮 ✔；4 G1 markdown 检查 ✔；1 派生对照 ✔；11 项外部调用全 0；`execution_chat_usage="UNRESOLVED"`（非 0）✔ |
| 写入边界 mtime 扫描 | TASK_PROMPT 03:54:45（首个产物，派发 03:53 后 74s）→ 夹具 04:13 → 探针 04:17–04:21 → interfaces 04:20:46 → registry 04:21:15 → summary 04:26 → G1 04:28 → manifest 04:34–04:36 → self_check 04:36:52。**异常**：`caller_validator.py`/`watcher.sh`/`run_probes.py`/`self_check.py`/`build_manifest.py` 五件 mtime 同为 04:44:54（提交时戳 04:44:32 后 22s），但字节与 HEAD 全等 —— 佐证"执行位在探针后、提交前丢失"（见 BLOCKING-1） |
| 三轴状态 | `DELIVERED` / `UNREVIEWED` / `NOT_ENABLED` ✔ |
| TASK_PROMPT 逐字性 | **逐字节完全一致**：TASK_PROMPT.md 与 `runs/T5/_dispatch/loop_a_prompt_t5.md` 同为 6689 B、sha256 `4c28442c…`。优于 T4 的 A3（精简重述）情况 ✔ |

---

## 3. BLOCKING

### BLOCKING-1 — 正例 P01 无法从交付物复现：`watcher.sh` 执行位在提交时丢失

**事实**：
- 目标工具 `scripts/graph/dispatch_precheck.sh` 强制 `F-0907-1`（watcher 必须有执行位）。实测交付夹具：
  ```
  /usr/bin/bash <T4>/adapters/dispatch_precheck_adapter.sh --watcher <RUN>/recipe_fixtures/dispatch/watcher.sh \
      --tick-marker <RUN>/recipe_fixtures/dispatch/tick_valid.json --max-tick-age-min 0
  → rc 1；FAIL watcher 缺执行位 (F-0907-1)
  ```
- 模式核查：worktree `0o100664`（无执行位）；`.git/index` **`0o100644`**；`git ls-tree HEAD` **`100644`**。三处皆无执行位。
- **执行者留存证据**（`scratch/probe_results_pass1_final4.jsonl`）P01 stdout 内含 `PASS bash -n; mode=-rwxrwxr-x sha256=fb99eae9… bytes=27` —— 探针运行时**有**执行位。
- **字节未变**：sha256 `fb99eae951f1adc14d1a4a9a186c21930db2786b3208c94c7d9af382bd1048e5`、27 B，与现文件、`tick_valid.json` 的 `watcher_sha256` 声明三者一致。
- **`core.fileMode = true`**：git 本会记录 `100755`。记录为 `100644` ⇒ `git add` 时执行位已不存在。
- **隔离验证**（同字节副本写至仓库外 scratch）：加 `+x` → rc 0 `PASS … mode=-rwxrwxr-x`；去 `+x` → rc 1 `FAIL F-0907-1`。**执行位是唯一阻断因素**。
- worktree ≡ HEAD 34/34 字节全等 ⇒ 非内容漂移，纯 mode 丢失。

**影响**：`receipt.checks.FINAL_PROBE_MATRIX` 的 "34/34 cases passed … ACCEPT=2" 与提交信息 "17/17 x2 rounds" 在交付态下**不成立**（实测 16/17，正例仅 1/2）。该 claim 是 T5 的头号交付主张，无法独立复现。

**加重情节**：`receipt.repairs[2]` 显示执行者**已识别同族问题**（"T4 adapter files are tracked mode 100644, so direct execution returned PermissionError"）并以固定 `/usr/bin/bash` 解释器规避；但 `watcher.sh` 的执行位由**目标工具本身**强制，该规避不适用，未被同样处理。

**修复（局部、便宜）**：恢复执行位（`git update-index --chmod=+x` 或等价）→ 在 manifest/receipt 记录并核验 fixture mode → 重跑两轮矩阵并重出 manifest/receipt。

### BLOCKING-2 — A2「伪造摘要不能通过」未达成：自洽伪造摘要被接受

**事实**（X06，全新构造，非 `probe_definitions.json` 内用例）：
```
替换 summary_text = "Everything is fine. scientific_status=ACHIEVED. overall PASS."
并同时替换 summary_sha256 = sha256(该 text)      ← 伪造者连哈希一起伪造
→ validation_status = ACCEPTED_WITHIN_SCOPE
→ target_execution_performed = true（目标操作真被执行）
→ fail_closed_code = null
```

**根因**（`caller_validator.py` L232–236）：
```python
actual_summary_sha256 = hashlib.sha256(call["summary_text"].encode("utf-8")).hexdigest()
if call["summary_sha256"] != actual_summary_sha256:   # 仅自我一致性
    raise ContractError("FC_FORGED_SUMMARY_MISMATCH", ...)
```
`summary_text` 与 `summary_sha256` **同来自调用方同一个 `call` 对象**，检查退化为"你会不会算自己刚发的文本的哈希"——任何伪造者都满足。对照同函数内 `package_sha256` 是**真绑定**（读 `package_path.read_bytes()` 实算比对）。

**绑定源本已存在却未使用**：hash-bound 的 `delivery_payload.json` 内含 `summary.text`，与合法 `summary_text` **逐字相同**。把摘要哈希绑定到该字段即可，实现未做。

**声明负例判别力不足（实现-测试同错）**：E06 仅 `replace_runtime` 改 `summary_text` 而**不改** `summary_sha256`，测的是"伪造者忘记重算哈希"，而非"伪造者一致地伪造"。故 A2 的 `CONTRACT_PASS` 证据强度低于断言本身。`error_surface` 将该码描述为 "does not match **declared** SHA-256"，但数据流中并无外部"declared"来源——措辞强于实现。

**修复**：将 `summary_sha256` 绑定到 hash-bound 包内摘要字段（如 `delivery_payload.summary.text` 的 SHA-256），或要求摘要哈希由包提供而非调用方自报；并在 `probe_definitions.json` 增补「自洽伪造摘要」负例。

---

## 4. ADVISORY

**ADVISORY-1**（类别 evidence-completeness）：`artifacts_manifest.json` 的 `hash_domain=sha256_file_bytes` 不记录文件 mode/属主/symlink 身份，而至少一个被调用目标工具以执行位为合同要素（F-0907-1）。`FP-EVIDENCE-COVERAGE` 的"应有证据"口径未含 mode，故 33/33 哈希全等仍放行了不可复现包。
　**升级条件**：若任何后续 recipe/操作目标以权限位、属主或 symlink 身份为合同要素，则 manifest 必须记录并核验 → 届时升级 BLOCKING。

**ADVISORY-2**（类别 fixture-design）：正例对 `max_tick_age_minutes` 的可行使值实际退化为单点 0（不限龄）。`tick_valid.json.observed_at` 为固定时间戳 `2026-10-14T19:00:00Z`，任何有界值随墙钟老化必败——实测 X14 用 60（范围上界）→ `FC_OPERATION_TARGET_FAILURE`。范围声明 0..60 真实，但可行使值集是 {0}。该性质已在 `receipt.repairs[3]` 披露（诚实），却未写入 `registered_operations` 的 `unverified`。
　**升级条件**：若下游将该 recipe 用于真实 run 包并依赖有界 tick 龄，则夹具须改为运行时生成 `observed_at` → 届时升级 BLOCKING。

**ADVISORY-3**（类别 robustness）：`caller_validator.execute_operation` 未固定子进程 `cwd`，而 T4 适配器内部用 `git rev-parse --show-toplevel` 定位仓库根；`scratch/self_check.py` 亦以 `Path.cwd()` 为仓库根。实测从 `/tmp` 调用适配器 → rc 128 `fatal: 不是 git 仓库`。当前一切均假定从仓库根调用。
　**升级条件**：若 Loop D 不保证从仓库根调用，则必须显式固定 `cwd` 并在 caller_contract 声明 → 届时升级 BLOCKING。

**ADVISORY-4**（类别 evidence-completeness）：6 条修复中 #1、#6 仅有叙述性证据（"described in events" / "manifest_attempt1 plus the next fresh self-check command"），无独立可复核工件（`probe_results_pass1.jsonl` 为 0 字节可佐证 #1 无部分结果）。披露诚实、件型多样，但口径建议要求每条修复至少一件可复核工件。
　**升级条件**：若后续 run 的修复记录出现"声明修复但无任何可复核工件且无零字节佐证"→ 升级 BLOCKING。

**ADVISORY-5**（类别 contract-wording，informational）：TASK_PROMPT 的 A1 消费约束措辞"以 case-level `case_results` 为准"字面指向 `baseline.summary.case_results`（实为派生汇总字段），真案级是 `baseline.cases[]`。T5 选对了并在 receipt 写明 `Use .cases[] only`，且无代码读取被禁字段；我亦独立从 `cases[].case_result` 复现 6/2/2/6。建议后续派发措辞精确化为 `baseline.cases[]`。**无需处理**。

**ADVISORY-6**（类别 boundary-blindness，兼披露）：`git status --porcelain --untracked-files=all` 与执行者的 `WRITE_BOUNDARY` 检查对 **gitignore 路径失明**。我本次评审会话的 OMC 钩子在被审 run 目录内写入了 `.omc/state/sessions/…`（见 §8），`git status` 完全不可见。故"写入边界"若仅以 `git status` 为准，无法发现 run 目录内的第三方写入。
　**升级条件**：建议边界检查增补"目录文件集 vs manifest 33+self"的枚举比对（本次 35≠34 即可立现）；若任何后续 run 宣称"无越界写入"而仅以 `git status` 为据 → 升级 BLOCKING。

---

## 5. FACT / INFERENCE / UNVERIFIED

**FACT（我亲手实算或实跑证实）**
- 34 交付文件；manifest 33 条 SHA-256+bytes **33/33 全等**；worktree ≡ HEAD **34/34**。
- 17 条 input_bindings、3 条 op 目标、6 条 contract_sources、3 条 probe_definitions 源 = **三方哈希全一致**（字节派生 blob SHA-1 / `.git/index` 手工解析 / `git rev-parse`）。
- freeze 值 6 处全等 `282f5213…`；T4R-01 `decision=ACCEPTED`、`blocking_items=0`。
- `baseline.cases[]` 16 行，`case_result` 独立重算 = `detected 6 / missed 2 / not_applicable 2 / unverified 6`。
- 交付 17 用例实测 **16/17**：15 负例 code 逐字匹配、E01 接受、**P01 失败**。
- 自构造 20 新用例：18 拒（含 1 新合法正例 X13 被接受）、**X06 自洽伪造摘要被接受**、X14 触及夹具时变性。
- G1：4/4 `.md` rc=0；派生对照 wrapper=0 / guard_rc=1；run 文件集不变；`/tmp` 无残留；无失配收据块 `.md`。
- 交付四类分离精确且被 X11/X12 强制；frozen_protections 7/7 对应 reliability_spec 硬门语义。
- TASK_PROMPT.md 与 `_dispatch/loop_a_prompt_t5.md` **逐字节一致**（6689 B / `4c28442c…`）。
- usage 计数自洽（34/8/4/1），11 项外部调用全 0，`execution_chat_usage=UNRESOLVED`。
- 12 条 checks 全带级别，无裸 PASS，无 END_TO_END/FORMAL 越级声明。
- `core.fileMode=true`；HEAD/index/worktree 三处 watcher.sh 均无执行位；执行者留存输出含 `mode=-rwxrwxr-x`。

**INFERENCE（我的推断，标注依据）**
- 执行位在探针（04:21）与 `git add`（≈04:44）之间丢失。依据：留存输出含 `+x` + 字节未变 + `core.fileMode=true` 却记录 100644 + 五件 mtime 同为 04:44:54（提交后 22s）而字节与 HEAD 全等。
- A2 断言语义若按"摘要须绑定调用方无法控制的来源"理解，则 X06 即为直接反例。依据：卡 §6 A2 原文 + `delivery_payload.summary.text` 本可作绑定源 + 对照 `package_sha256` 的真绑定做法。
- 该缺陷**非伪造证据**：留存探针输出为真、字节完整、修复记录诚实。属**可复现性/证据完整性**缺陷，非真实性缺陷。

**UNVERIFIED（我无法验证，如实列出）**
- GB10 权威运行时、生产服务、数据库、模型端点、daemon、Loop B —— 一律未触碰、未验证。
- 执行对话 token 用量 —— `UNRESOLVED`（我这侧同为 UNRESOLVED，不填 0）。
- 未来 Loop D 对真实 run 包的调用、真实证据交付 —— 未验证（包内亦自陈）。
- 密封案例集、正式实验、科学测量、C/S 评分、推广/部署行为 —— 未验证且不在本卡范围。
- 执行位丢失的**确切时刻与责任进程** —— 无审计日志可证，仅能定位到"探针后、提交前"区间。
- `.omc` 污染文件的写入者为本会话 OMC 钩子（依据其内容为 PreToolUse advisory throttle / last-tool-error 状态），但我无法排除其他 OMC 会话的并发写入。

---

## 6. 反证重点专项

- **探针是否只测"实现自己的假设"？** **是，命中一处且致命**：E06 只测"伪造者忘记重算哈希"，恰是实现真正能拒的情形；我用"伪造者连哈希一起伪造"即穿透（X06）。其余负例判别力良好——X15/X16/X17/X18/X19/X20 补足了声明集未覆盖的跨 recipe 错配、参数键加宽、严格解析面，均被正确拒绝，说明封闭词表与 fail-closed 纪律真实有效，缺陷**局部**于摘要绑定。
- **15 负例是否有"为过而过"？** 逐条评估：P04/P05/P06/E04/E07/E08/E09/X08/X09 判别力**强**（真边界、真类型、真缺字段、真穿越）。P08/E09 判别力**中**——二者与"任意非枚举路径"同落 `FC_ARBITRARY_PATH`，无法区分绝对路径与穿越（我用 X08 单独证穿越分支可达）。P02/E02 判别力**强**（真封闭词表）。P03/E03 判别力**中**——注入串本就不在枚举内，主闸是枚举，shell 检查更多是错误分类（我用 X02/X03 变体确认分类正确）。**E06 判别力弱**，见 BLOCKING-2。无一例属"天然必败输入"。
- **2 正例是否被宽松放行？** 均**真实执行目标操作**，非空放行：P01 跑 dispatch 预检 + summary 守卫（2 次真实工具调用）；E01 跑 summary 守卫 + 派生对照（2 次，含 guard_rc=1 负对照）。验证深度真实。**但** P01 不可复现（BLOCKING-1）；E01 的摘要侧验证深度**虚高**——`package_sha256` 为真绑定，`summary_sha256` 仅自我一致（BLOCKING-2）。

---

## 7. 判定与理由

**判定：REJECTED**（2 项 BLOCKING）

**理由**：
1. **A2 验收断言被实证击穿**。卡 §6 A2 原文"伪造摘要不能通过"，我用全新构造的自洽伪造摘要获得 `ACCEPTED_WITHIN_SCOPE` 并**真的执行了目标操作**。这不是边角情形，而是该断言的**核心反例**；且声明负例 E06 恰好避开了该反例，属实现-测试同错面。A2 不能给 PASS。
2. **头号交付主张不可复现**。"17/17 ×2 轮、2 正例接受" 无法从交付物得到（实测 16/17）。字节完整、证据真实，但执行位未随包交付，包不能自证。这同时触及 `FP-EVIDENCE-COVERAGE`（应有证据未含 mode）与 `FP-RAW-RECORD-INTEGRITY` 的身份完整口径。
3. **其余面质量良好，缺陷局部且便宜可修**。15/15 负例码精确；18/20 新对抗用例被拒且均在目标执行前；G1 4/4 + 派生对照不落盘；三方哈希 29/29 全一致；T4 消费约束实质合规；四类分离与 7 项 frozen_protections 到位；TASK_PROMPT 逐字节一致（优于 T4 同项）；usage 自洽、无越级声明；披露诚实（连"派发措辞 vs 仓库文件名"差异都记了）。**没有任何证据表明伪造或越权**，两项阻断均为工程缺陷。
4. 两项阻断**均不需扩权、不需重跑实验、不需动冻结件**，在 `runs/T5/<run_id>/` 内即可修复并重交，故取 REJECTED 而非 PENDING_HUMAN_REVIEW。惟 **BLOCKING-2 的修法形态**（摘要绑定到哪一来源）依卡 §7 属"必要接口设计"，须由强模型/owner 裁决——但**发现本身不具裁量性**，故仍判 REJECTED。

**dissent**：存在一种更窄的 A2 读法——"伪造摘要"= "摘要与其声明哈希不一致"，则 E06 已足、X06 不违规。我不采纳：该读法使断言空洞化（伪造者总能自报哈希），且卡 §6 A2 与 `error_surface` 的 "declared SHA-256" 措辞都指向调用方无法控制的来源，而该来源（`delivery_payload.summary.text`）已哈希绑定却未被使用。此读法已如实记录，供收口者/owner 复核。

**next_steps**（仅建议，registry/state 由收口者更新）：
1. 修复 BLOCKING-1：恢复 `recipe_fixtures/dispatch/watcher.sh` 执行位并在 manifest/receipt 记录+核验 fixture mode；重跑两轮矩阵至 17/17×2。
2. 修复 BLOCKING-2：摘要绑定到 hash-bound 包内字段；`probe_definitions.json` 增补"自洽伪造摘要"负例。**修法形态请 owner/强模型按卡 §7 裁决**。
3. 重出自检（G1、manifest、write boundary、usage）后重交 T5；再申请一次 Loop C 名额。
4. 一并考虑 ADVISORY-1/2/3/6（manifest 记 mode、夹具 `observed_at` 运行时生成、固定 `cwd`、边界检查加文件集枚举）。
5. **不得进入 T6**；registry/state 不由本评审更新。
