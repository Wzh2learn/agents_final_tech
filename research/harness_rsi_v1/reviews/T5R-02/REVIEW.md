# T5R-02 独立评审报告 — harness_rsi_v1 T5 v2 返工（重派 B）

- **review_id**: T5R-02 | **task_id**: T5 | **被审 run**: `research/harness_rsi_v1/runs/T5/20261014T212520Z_3acf4c1d/`（提交 `e0d2523`）
- **reviewer**: Loop C 独立质量审计层（GB10）| **runtime**: Linux 6.17.0-1018-nvidia / Python 3.12
- **评审性质**: 只读独立评审。不修改仓库与被审包、不 git 写、不联网、不调模型/生产/数据库、不进入 T6。仅出提案；registry/state 由收口者更新。
- **测量时刻**: UTC 2026-10-14T22:56Z 前后（tick 龄 59.25 min）

---

## 0. 判定摘要

**判定：REJECTED（1 项 BLOCKING）**。

T5R-01 的两个 blocking **均已实质修复并经我独立复现证实**（执行位已随包交付、外部 pin 三重相等成立且能拒自洽伪造摘要）。但**头号交付主张仍不可从交付态复现**：交付包自身的探针入口跑不出 21/21，唯一回放路径会**原地覆盖一件哈希绑定的原始记录**，与包自身 `FP-RAW-RECORD-INTEGRITY` 声明直接冲突。该缺陷与 T5R-01 BLOCKING-1 **同族同类、同一受损主张**，故按同一标准取 REJECTED；修法便宜、局部、不需扩权。

---

## 1. 范围与方法

**范围**：T5 v2 全部 46 个交付文件 + 依赖事实（T4 v2 适配器、`reviews/T4R-01/`）+ 契约（`cards/T5.md`、`contracts/*`、`evaluation/reliability_spec.md`、`docs/governance/FORMAL_EXPERIMENT_PREFLIGHT_V1.md`）+ T5R-01 全文判定链。

**方法**：
1. **独立复算，不采信声明** — 计数、SHA-256、字节、mode、git blob 身份全部现算。身份用三方交叉：字节派生 git blob SHA-1（`sha1("blob <len>\0"+bytes)`）／手工解析 `.git/index`（v2、3827 条目、8 字节对齐填充、mode 取第 7 个 uint32）／`git rev-parse`/`git ls-tree`。
2. **实弹复跑** — ①T5R-01 原 P01 命令链逐字重跑；②交付态直接跑交付 `run_probes.py`；③在**仓库外副本**上跑交付 `fresh_delivery_check.py` 两轮；④自构造 **15 个新对抗探针（Y01–Y15）** + **1 个注册表替换探针（Z01）**。
3. **反证优先** — 假定声明为假，专攻"实现-测试同错""为过而过的负例""回放自证性""宽读法边界"。
4. **只写仓库外** — `/home/testuser/wzh/loop_runs/t5r02b_recheck_a/`（详见 §8）。

**判级词汇**：依 `FORMAL_EXPERIMENT_PREFLIGHT_V1.md`，一切 PASS 带级别+范围；不使用裸 PASS；不声称 `END_TO_END_PREFLIGHT_PASS` / `FORMAL_RUN_PASS`。

---

## 2. 逐项复算结果

### 2.1 计数 / 哈希 / 模式 — PASS(CONTRACT)，范围：run 包字节与 manifest 等价

| 检查 | 方法 | 结果 | rc |
|---|---|---|---|
| run 文件数 | rglob | **46** | 0 |
| manifest 条目 | 解析 | **45**（`self_hash_policy` 自排除）+ `artifact_count=45` | 0 |
| 逐条 SHA-256+bytes+mode | 独立实算 vs 声明 | **45/45 全等，0 失配** | 0 |
| 无遗漏/多余 | 集合差 | `in_manifest_not_disk=[]`；`in_disk_not_manifest=['artifacts_manifest.json']`（自排除，合规） | 0 |
| 重复 relative_path / symlink | set + 遍历 | 无重复；**symlinks=[]** | 0 |
| worktree ≡ HEAD ≡ index | 字节→blob SHA-1 / `.git/index` 解析 / `git rev-parse` | **46/46 三方全等**；mode **46/46 一致** | 0 |
| 执行位 | X_OK + mode | 磁盘执行件**仅** `recipe_fixtures/dispatch/watcher.sh`；`required_executables` 声明 1 条且为 `100755` | 0 |

`hash_domain=sha256_file_bytes_plus_mode`，45 条全部带 `mode` 字段（`100644`×44 + `100755`×1）—— ADVISORY-1 口径已补。

### 2.2 绑定身份与依赖 — PASS(CONTRACT)，范围：tracked 身份绑定

- **input_bindings 22/22** 字节派生 blob SHA-1 全等；含 `sha256_file` 的 5 条 SHA-256 亦全等。
- **登记操作目标 3/3**（`c5045e95…`/`9f421f69…`/`7a3c9d1d…`）、**contract_sources 6/6**、**probe_definitions 契约源 3/3** 全部字节派生一致。
- **freeze 常量 6 处全等** `282f52133a682e927c82b771fa103c27da34db7acbd8a12d2921f42a6d0bf36b`：`protocol.json` / `recipe_interfaces` / `receipt` / 两个 call 夹具 / `caller_validator.py` 常量。
- **T4R-01 依赖**：`decision=ACCEPTED`、`blocking_items=[]`、`review_receipt.verdict=ACCEPTED`。✔
- **T4 真案级消费**：`build_v2_receipt.py` L57 `Counter(case["case_result"] for case in baseline["cases"])`；禁读字段仅出现在禁止性措辞中，**`.py` 消费=0**。我独立从 `cases[].case_result` 重算 = `detected 6 / missed 2 / not_applicable 2 / unverified 6`，与声明一致。✔

### 2.3 核心 A — BLOCKING-1 复现验证

#### (a) 执行位交付 — **PASS(CONTRACT)**，范围：交付态 mode 三方一致

```
/usr/bin/bash <T4>/adapters/dispatch_precheck_adapter.sh \
  --watcher <RUN>/recipe_fixtures/dispatch/watcher.sh \
  --tick-marker <RUN>/recipe_fixtures/dispatch/tick_valid.json --max-tick-age-min 0
→ rc 0
→ PASS bash -n; mode=-rwxr-xr-x sha256=fb99eae951f1… bytes=27
→ 结论: 双实证齐备 (输入合同通过), 可派发
```

- T5R-01 的 P01 阻断命令链**逐字重跑 = rc 0**（v1 为 rc 1 `FAIL F-0907-1`）。执行位是 v1 唯一阻断因素，现已消除。
- 模式三方：worktree `0o755`（X_OK）；`.git/index` `0o100755`（`git ls-files -s` 与我手工解析 index 的 mode 字段双证）；`git ls-tree HEAD` **`100755`**。`core.fileMode=true`。
- 字节未变：`fb99eae951f1adc14d1a4a9a186c21930db2786b3208c94c7d9af382bd1048e5` / 27 B，与 `tick_valid.json.watcher_sha256` 声明一致。

#### (b) fresh-delivery 是否真从交付态重建 — **PASS(COMPONENT)**，范围：副本上 mode 重置+恢复

我在**仓库外副本**重跑交付 `fresh_delivery_check.py` 两轮（R1/R2，rc=0）：

| 项 | R1 | R2 |
|---|---|---|
| `all_files_chmod_x_removed` | True（全件 0o644） | True |
| `required_executables` 恢复 | `100755` + `x_bit=True` | 同 |
| probe_count / all_passed | 21 / True | 21 / True |
| ACCEPT / REJECT | **4 / 17** | **4 / 17** |
| 归一化结果 | 与 R2 **逐项一致** | 与 R1 一致 |
| fail_closed_code 失配 | **0** | 0 |
| REJECT 时 `target_execution_performed` | 全 False | 全 False |
| REJECT 时 `operation_result_count` | 全 0 | 全 0 |

ACCEPT 4 例 = `P01-PRECHECK-VALID` / `P09-PRECHECK-BOUNDED-TICK-AGE-60` / `E01-DELIVERY-VALID` / `X06C-…`，各执行 **2** 个真实只读操作。合计 42 caller 进程、16 次操作调用 —— 与 receipt `usage` 声明**逐项吻合**（我独立计数亦为 42/16）。

**对抗质检：是否还有"合同要求可执行"元素被漏标？** 读目标工具合同源（`scripts/graph/dispatch_precheck.sh` 的 `F-0907-1` 仅约束 watcher 执行位）。三个登记目标是 `.sh` 但由注册表固定 `/usr/bin/bash` 解释器调用，**调用方不可执行它们**，故不属于"合同要求可执行"面，未漏标。包内唯一执行位合同要素即 `watcher.sh`，已记入 `required_executables`。

#### (c) 但：**头号主张仍不可从交付态复现 — BLOCKING**（见 §7）

### 2.4 核心 B — BLOCKING-2 复现验证

实现（`caller_validator.py` L213–222、L245–260）：交付 recipe 要求 `caller_context.expected_artifact_sha256` 存在 → 键集恰为 `{context, expected_artifact_sha256}` → pin 须 64 位小写 hex → `package_sha256` 绑定真实包字节 → `summary_sha256 == sha256(summary_text)` → **`actual_summary_sha256 == expected_pin`**，全部在任何目标执行之前。

我自构造 **15 个全新探针**（均不在 `probe_definitions.json` 内）：

| 新用例 | 攻击面 | 实测 | code | 判定 |
|---|---|---|---|---|
| **Y01 伪造 text + 自洽伪造 hash + 真 pin** | **伪造者会算自己哈希**（判别性反例） | **REJECT** | `FC_PIN_MISMATCH` | **拒 ✔ 关键** |
| Y02 pin 类型=int | pin 形态 | REJECT | `FC_ARTIFACT_NOT_PINNED` | fail-closed ✔ |
| Y03 pin="" | pin 形态 | REJECT | `FC_ARTIFACT_NOT_PINNED` | ✔ |
| Y04 pin 非 hex×64 | pin 形态 | REJECT | `FC_ARTIFACT_NOT_PINNED` | ✔ |
| Y05 pin 大写 hex | 严格性 | REJECT | `FC_ARTIFACT_NOT_PINNED` | ✔ |
| **Y06 宽读法：text+hash+pin 全伪造且自洽** | 已声明威胁边界 | **ACCEPT** | — | 见 §7/dissent |
| Y07 删 pin 键（真摘要） | 缺 pin | REJECT | `FC_ARTIFACT_NOT_PINNED` | ✔ |
| Y08 caller_context 加键 | 键集封闭 | REJECT | `FC_RECIPE_OBJECT_MISMATCH` | ✔ |
| Y09 改 text 未改 hash | 自洽失败 | REJECT | `FC_FORGED_SUMMARY_MISMATCH` | ✔ |
| Y10 pin 类型=list | pin 形态 | REJECT | `FC_ARTIFACT_NOT_PINNED` | ✔ |
| Y11 summary_text 类型=int | 类型 | REJECT | `FC_FORGED_SUMMARY_MISMATCH` | ✔ |
| Y12 summary_sha256=null | 类型 | REJECT | `FC_FORGED_SUMMARY_MISMATCH` | ✔ |
| **Y13 正例**：真摘要+真 pin | 正例真实性 | **ACCEPT** | — | 执行 2 真操作 ✔ |
| Y14 pin=null 显式 | pin 形态 | REJECT | `FC_ARTIFACT_NOT_PINNED` | ✔ |
| Y15 空摘要+匹配 pin | 内容充分性 | ACCEPT | — | 身份绑定不裁内容（见 ADV-NEW-3） |

**Y01 是判别性证据**：v1 的 E06 只测"忘记重算哈希"，v2 的 X06B 用全零 pin；两者都未证明"伪造者正确重算自身哈希时仍被拒"。Y01 用**真 pin**（真摘要哈希）+ 自洽伪造，得 `FC_PIN_MISMATCH` 且 `target_execution_performed=false` —— 外部 pin 确实能在伪造者自洽时阻断。**A2 的"伪造摘要不能通过"在已裁决口径下成立**。

**威胁边界声明**：三处显式声明且措辞与实现一致 —
- `recipe_interfaces.json` L286：“…`caller_context.expected_artifact_sha256` sourced outside the producer (caller-owned manifest, registry, or upstream receipt chain)… The validator does not protect against a caller that deliberately supplies a false pin; that identity source is outside this producer-controlled package and must be trusted by the caller.”
- `recipe_fixtures/README.md` L7 同义中文声明。
- `receipt.unresolved[0]` 同义声明。

**宽读法边界实测（Y06）**：`summary_text` + `summary_sha256` + `expected_artifact_sha256` 三者同时伪造且相互自洽 → `ACCEPTED_WITHIN_SCOPE`、`target_execution_performed=true`、执行 2 个真实操作。这**正是**已声明的"不防调用方自递假 pin"非保证，且交付探针集已把它显式编码为 `X06C-SELF-CONSISTENT-FORGED-CORRECT-PIN`、`expected=ACCEPT`。与 Loop D 裁决（"接受须绑定生产者控制之外的外部 pin；威胁边界须显式声明"）**一致**，故记为**边界事实**，不计为缺陷。残余设计局限见 **dissent**。

**所有拒绝均 `target_execution_performed=false`、`operation_results=[]`** —— 接口错误确在目标执行前被调用方发现。

### 2.5 A1 / A2 / A3 / A-common 逐条

| 断言 | 判定 | 级别 | 范围 |
|---|---|---|---|
| **A1** 一 recipe 一对象；不能任意 shell | **PASS** | CONTRACT | 两 recipe `only_object:true`、`object_id` 互斥、各自 `explicitly_not_responsible_for` 列明排除面；P02/P03/P08/E02/E03/E09 六例 + 我的 Y08/Y11 等边界负例均在目标执行前被拒；argv 形状按 `op_id` 硬编码、解释器固定 `/usr/bin/bash`、参数为封闭枚举。**范围限定**：以"调用方使用交付的、身份正确的 registry/interfaces"为前提，见 ADV-NEW-1。不含科学测量、C/S 评分、正式资格、推广。 |
| **A2** 接口错误调用方可见；伪造摘要不能通过 | **PASS** | CONTRACT | 前半：17/17 负例码精确 + Y01–Y15 中 11 个负例码精确、均 `target_execution_performed=false`。后半：Y01 判别性反例被 `FC_PIN_MISMATCH` 阻断；无 pin/错 pin/形态非法 pin 全部 fail-closed。**按 Loop D 裁决口径**（外部 pin + 显式威胁边界）成立；宽读法 Y06 属已声明非保证。 |
| **A3** 不改 C/S 评分、旧实验组件、冻结件 | **PASS** | CONTRACT | 22 条 tracked 绑定 + 3 目标 + 9 契约源字节派生全等；我的探针前后 manifest 45/45 仍全等、run 文件集 46 不变、无 `.omc`/`__pycache__`/`.pytest_cache` 污染、`/tmp` 无残留。`git status` 脏项全部在 run 之外且 pre-existing（见 §8）。`registered_operations` 声明 `repository_write_forbidden`/`git_index_mutation_forbidden`。 |
| **A-common** JSON/必需字段/路径/哈希/越界/未知项 | **PASS** | CONTRACT | 全部 JSON 解析成功；`strict_object` 拒重复字段、`reject_constant` 拒 NaN/Infinity；路径仅 run-root 下封闭枚举且 `resolve()` 防逃逸；manifest 45/45 哈希+字节+mode 实算一致；`unresolved` 显式列 6 项。**附注**：回放路径与"原始记录只读"声明冲突，单列 BLOCKING（§7），不并入本条。 |

**级别纪律**：receipt 16 条 checks 全部带 `verification_level`（`CONTRACT_PASS`/`COMPONENT_PASS`），**无裸 PASS**；`summary.md` 明写"不是科学 PASS、正式实验资格、`END_TO_END_PREFLIGHT_PASS` 或 `FORMAL_RUN_PASS`"。全包扫描 END_TO_END/FORMAL_RUN 令牌**仅出现在词表与显式否定句**中。✔

---

## 3. Advisory 闭合核验（A1–A6 逐条）

| 前轮 | 状态 | 我的独立证据 |
|---|---|---|
| **ADV-1** manifest 记 mode | **闭合** | `hash_domain=sha256_file_bytes_plus_mode`；45/45 条带 `mode`；`required_executables=[recipe_fixtures/dispatch/watcher.sh]`；我实算 45/45 mode 全等 |
| **ADV-2** 有界 tick 正例 | **实质闭合，但交付形态引发新阻断** | P01(30) 与 P09(60) 在记录轮与我复跑轮均 ACCEPT，可行使值集已非 `{0}`；但见 §7 |
| **ADV-3** 固定 cwd | **闭合** | 3/3 目标 `required_cwd=/home/testuser/wzh/projects/agents_final_tech`；validator 检查并传 `cwd=REPOSITORY_ROOT`；两轮均从 `/tmp` 执行 |
| **ADV-4** 修复记录工件 | **闭合** | 7 条修复、12 条证据路径**全部存在且非空**（最小 318 B）；`attempt1_failure.json`(605B)/`attempt2_failure.json`(603B) 独立成件 |
| **ADV-5** 措辞/禁读派生字段 | **闭合** | `combination_results`/`failure_family_profiles` **仅**现于 `receipt.json`+`recipe_interfaces.json` 禁止性措辞；`.py` 消费=0；`build_v2_receipt.py` 真案级取 `cases[]`；我独立重算 6/2/2/6 一致 |
| **ADV-6** gitignored 路径扫描 | **闭合** | `boundary_scan.json`：`scan_scope="full repository walk including hidden and gitignored files since run start"`、`repo_files_scanned=74348`、`gitignored_touched`(9)、`unexpected_touched`(10，全在 `logs/`+`.pytest_cache/`，并在 `unresolved[5]` 如实披露)；manifest 覆盖 run 内 gitignored 的 `.log`；我自做文件集枚举 46 = 45+self |

---

## 4. 回归核验 — PASS(CONTRACT)

| 项 | 结果 |
|---|---|
| 原 15 负例 `fail_closed_code` 精确 | **15/15 逐字保留且实测精确**（我复跑 0 失配）；P01/E01 正例保留 |
| 四类交付字段分离 | **精确**：两 recipe `delivery_fields` 键 = {qualification, audit, execution, scientific, overall_pass_field_forbidden}；各 `*_mixed_in` 全 false；`overall_pass_field_forbidden=true`；`scientific.claim_must_be=null`；qualification status_field 分别为 `preflight_eligibility`/`delivery_eligibility`（按对象分离） |
| frozen_protections 不减少 | **7/7**，两 recipe 各引全部 7 项，与 v1 同数、同 ID、同 reliability_spec §6.3 语义；仅声明不评分 |
| TASK_PROMPT 逐字 | **逐字节一致**：5288 B / `0007a76a7e17b9e1d0030003d5f7e7000f98ec0f3882229e06698a009a5a7305`，与 `runs/T5/_dispatch/loop_a_prompt_t5_v2.md` 全等；且 ≠ v1 派发（6689 B） |
| G1 每个 `.md` rc=0 | **4/4 rc=0**（`TASK_PROMPT.md`/`recipe_fixtures/README.md`/`recipe_fixtures/summary/good_summary.md`/`summary.md`） |
| 无裸 PASS / 无越级 | 8 处候选全为假阳性（禁令措辞"单字段总体 PASS"、`PASS_1/2` 轮次、`E07-…-OVERALL-PASS` 用例名）；越级令牌仅在词表/否定句 |
| usage 零声明与探针计数自洽 | `final_acceptance_caller_processes=42`、`registered_operation_invocations=16`、`g1_markdown_checks=4`、`runtime_derive_negative_controls=2`、`fresh_delivery_helper_attempts=4`、`manual_repair_fixes=2`、`automatic_retries=0`；外部 11 项全 0；`execution_chat_usage=UNRESOLVED`（非 0）。**我的独立两轮同为 42 进程 / 16 操作** |
| 三轴状态 | `DELIVERED` / `UNREVIEWED` / `NOT_ENABLED` ✔ |

---

## 5. 对抗面

| 项目 | 结果 |
|---|---|
| fresh-delivery 是否真从交付态重建 | **是**：copytree → 全件 `chmod 0o644` → 仅按 manifest `mode` 逐件恢复 → 探针。`all_files_chmod_x_removed=True`、watcher 恢复 `100755`+X_OK。**但**其后必跑 `prepare_runtime_fixtures.py` 改 tick（见 §7） |
| `scratch/reproduction/` 两条 v1 复现件对照 | **成立**：`v1_p01_delivery_probe.jsonl` → `P01 actual=REJECT code=FC_OPERATION_TARGET_FAILURE`（`wrapper=1 target=1`）；`v1_x06_forge.jsonl` → `caller_exit_code=0`、`fail_closed_code=null` 且 `operation_results` 非空（即 v1 伪造摘要被接受）。两者与 T5R-01 判定链一致 ✔ |
| 写入边界（含 gitignore 视野） | 边界扫描含 gitignored（见 ADV-6）；我方复核：探针前后 manifest 45/45 全等、run 文件集 46 不变、无污染目录、`/tmp` 无 `t4-v2*`/`summary-mismatch*` 残留。`git status --porcelain -uall` 36 行**全部在被审 run 之外**且与会话起始快照一致（`logs/graph/*` 4 处既有改动 + 未跟踪 T4 v1 目录 `20261014T174628Z_2cc25c92/` 32 件），非本次写入 |
| **Z01 注册表替换** | **穿透**：把 `registered_operations.json` 的 `OP-T4-R-SUMMARY-GUARD-CHECK` 目标路径换成我方诱饵脚本 → validator **执行了诱饵**（marker 落盘 `Z01 ARBITRARY TARGET EXECUTED`）并返回 `ACCEPTED_WITHIN_SCOPE`/`target_execution_performed=true`。另：registry 逐操作声明 `target.git_blob_id`，但 `execute_operation` **从不核验目标文件身份**。→ ADV-NEW-1 |

---

## 6. FACT / INFERENCE / UNVERIFIED

**FACT（我亲手实算或实跑证实）**
- 46 交付文件；manifest 45 条 SHA-256+bytes+mode **45/45 全等**；worktree ≡ HEAD ≡ index **46/46 字节与 mode 全等**；`core.fileMode=true`；HEAD/index/worktree 三处 `watcher.sh` 均 `100755`。
- T5R-01 原 P01 命令链重跑 **rc=0**（v1 rc=1）；`mode=-rwxr-xr-x`、`sha256=fb99eae9…`、27 B。
- 交付态直接跑交付 `run_probes.py` → **P01 = REJECT / `FC_OPERATION_TARGET_FAILURE`，rc=3，仅 1 条记录**（tick 龄 59.25 min，`valid_precheck_call.json` 用 `max_tick_age_minutes=30`）。
- 仓库外副本上 `fresh_delivery_check.py` 两轮 **21/21 ×2**，ACCEPT=4/REJECT=17，归一化逐项一致，fail_closed_code 失配 0；**两轮后副本 manifest 失配 = `['recipe_fixtures/dispatch/tick_valid.json']`**。
- `prepare_runtime_fixtures.py` **原地写** `recipe_fixtures/dispatch/tick_valid.json` 的 `observed_at`；`scratch/current_tree/runtime_fixture_prepare.log` 留有对**被审 run 自身**该路径的写入记录（`observed_at=2026-10-14T21:56:53Z`）。
- `recipe_interfaces.json` 声明 `max_tick_age_minutes: 0`，`valid_precheck_call.json` 实用 `30`。
- 22/22 绑定、3/3 目标、6/6+3/3 契约源、6 处 freeze 常量全等；T4R-01 `decision=ACCEPTED`、0 blocking。
- `baseline.cases[]` 16 行独立重算 = 6/2/2/6；禁读派生字段 `.py` 消费 = 0。
- 我的 Y01 判别性反例被 `FC_PIN_MISMATCH` 阻断；Y02–Y05/Y07–Y12/Y14 共 11 例 fail-closed 码精确；Y06（三者全伪造自洽）被接受并执行目标；Y13 正例被接受并执行 2 真操作；Y15 空摘要+匹配 pin 被接受。
- Z01：替换 registry 目标路径 → 诱饵脚本被执行，validator 返回 ACCEPT。
- 15 个 v1 负例码逐字保留；G1 4/4 rc=0；TASK_PROMPT 与 v2 派发逐字节一致；usage 42/16/4 与我独立计数一致；16 条 checks 全带级别、无越级。
- 交付 4 份 probe 结果（fresh/current × attempt3/最终）自洽：均为 21 行、21 passed、ACCEPT=4/REJECT=17、同 4 个 ACCEPT 用例。

**INFERENCE（我的推断，标注依据）**
- 该缺陷**非伪造证据**：留存探针输出真实、字节完整、`attempt1/attempt2` 失败工件独立成件、`unresolved` 如实披露回放需重新生成 tick。主张在**作出之时**应为真（tick 龄≈0 时 30/60 均可过）；缺陷是**证据耐久性/自证性**，非真实性。
- 属 T5R-01 BLOCKING-1 **同族残留**而非新目标：同一受损主张（"21/21×2 / 42/42" vs "17/17×2"）、同一失败签名（`run_probes.py` 首败即 `return 3`、止于 P01）、同一标准（交付态不可独立复现）。依据：T5R-01 §3 BLOCKING-1 影响段原文。
- 该矛盾是**设计选择**而非不可避免：卡内已有可回放稳定值（`max_tick_age_minutes=0`，且 `recipe_interfaces` 本就如此声明）；P09 单独即可证有界龄。故非"有界 tick 必然时变"所迫。

**UNVERIFIED（我无法验证，如实列出）**
- GB10 权威运行时、生产服务、数据库、模型端点、daemon、Loop B —— 一律未触碰、未验证。
- 执行对话 token 用量 —— `UNRESOLVED`（我这侧同为 UNRESOLVED，不填 0）。
- 未来 Loop D 对真实 run 包的调用、真实证据交付、密封案例集 —— 未验证（包内亦自陈）。
- pin 在真实部署中的**外部来源**（caller-owned manifest/registry/upstream receipt chain）—— 交付夹具把 pin 与 `summary_text` 同文件并置且 `pin == summary_sha256`，故测试证据只证明**机制**，未证明**来源独立性**。
- `logs/`、`.pytest_cache/` 变更的确切写入者与时刻 —— 非本次评审写入，无审计日志可证。
- Z01 场景在真实 Loop D 部署中被触发的可能性 —— 取决于 registry 交付链是否受控，未验证。

---

## 7. BLOCKING

### BLOCKING-1（本轮唯一条目）— 头号交付主张仍不可从交付态复现：有界 tick 夹具时变 + 回放原地覆盖哈希绑定原始记录

**事实链（逐条可复现）**：
1. 交付态直接跑交付入口：
   ```
   python3 <RUN>/run_probes.py --run-root <RUN> \
     --definitions <RUN>/recipe_fixtures/probe_definitions.json \
     --output <reviewer_scratch>/asdelivered_passA.jsonl --round-id PASS_1
   → rc 3；仅 1 条记录：P01-PRECHECK-VALID expected=ACCEPT actual=REJECT
     fail_closed_code=FC_OPERATION_TARGET_FAILURE
   ```
2. 成因：`recipe_fixtures/valid_precheck_call.json` 用 `max_tick_age_minutes: 30`；`recipe_fixtures/dispatch/tick_valid.json.observed_at` 为固定过去时刻 `2026-10-14T21:56:53Z`（实测龄 59.25 min）。同链 `--max-tick-age-min 30` → rc 1 `FAIL 收据过期: age=59.25min > 30min`；`--max-tick-age-min 0` 与 `60` → rc 0。
3. 唯一 21/21 路径需先跑 `scratch/prepare_runtime_fixtures.py`，它 **`tick_path.write_text(...)` 原地覆盖** `recipe_fixtures/dispatch/tick_valid.json` —— 一件 manifest 记录、SHA-256 绑定的原始记录。`scratch/current_tree/runtime_fixture_prepare.log` 正是对**被审 run 自身**该路径的写入记录。
4. 后果：包**不能同时** manifest 自洽与可回放。我在副本上实证：回放后 `COPY_manifest_mismatches_after_run = ['recipe_fixtures/dispatch/tick_valid.json']`。
5. 与包自身声明直接冲突：
   - `recipe_interfaces.json` `FP-RAW-RECORD-INTEGRITY`：「Existing run files are **read-only**; runtime-derived mismatch text is **never persisted over a matching fixture**.」
   - `artifacts_manifest.hash_domain = sha256_file_bytes_plus_mode` —— 回放使该件 mode/bytes 域自证失效。
6. 内部不一致：`recipe_interfaces.json` 声明 `max_tick_age_minutes: 0`（可回放稳定），交付正例夹具却用 `30`（不稳定）——**稳定值在手却未用于 P01**。
7. 披露不对称：`receipt.unresolved` 记「must be regenerated before later replay」，`FRESH_DELIVERY_SIMULATION.scope` 亦含「regenerate bounded tick timestamp」——诚实；但 `summary.md` 与提交信息平铺「各 21/21，合计 42/42」「fresh-delivery 42/42」，且 `recipe_fixtures/README.md` **完全未写回放前置步骤**。独立复放者按自然入口会命中 v1 同一失败签名。

**影响**：`receipt.checks.FINAL_PROBE_MATRIX`「42/42 cases passed」与提交信息「fresh-delivery 42/42」在**交付态下不成立**（实测首例即败、rc=3）。该 claim 是 T5 v2 的头号交付主张，无法从交付物独立复现 —— 与 T5R-01 BLOCKING-1 的影响段**逐句同构**。

**加重情节**：`run_probes.py` 仍「首败即 `return 3`」，故回放失败只产出 1 条记录而非全矩阵，v1/v2 两次诊断均受此拖累。

**非指控伪造**：留存证据真实、计数自洽（我独立复算 42/16 一致）、修复披露诚实；主张在作出之时应为真。属**可复现性/证据耐久性**缺陷。

**修复（局部、便宜、不需扩权/不需动冻结件）**：
- (a) 让交付正例可回放稳定：P01 的 `max_tick_age_minutes` 取 **0**（与 `recipe_interfaces` 一致），P09 单独承担有界龄（30/60）正例；**或**
- (b) 把 tick 生成移到**非 manifest 路径**（运行时写入独立 runtime 目录、调用指向它），使回放永不作废任何 manifest 哈希；
- (c) 在 `recipe_fixtures/README.md` 明写回放入口与前置；
- (d) 统一 `recipe_interfaces` 与夹具的 `max_tick_age_minutes`；
- (e) 建议 `run_probes.py` 收集完全部用例再返回非零，使失败也产出全矩阵。

---

## 8. ADVISORY（本轮新增）

**ADVISORY-NEW-1**（类别 trust-boundary / security）：`caller_validator` **不认证自身 `--interfaces` / `--operations` 输入**，且 `execute_operation` **不核验目标文件身份**（registry 已声明 `target.git_blob_id` 却从不比对）。实证 Z01：替换 registry 目标路径 → 任意脚本被执行并返回 ACCEPT。`registered_operations.path_policy.target_rule`「callers cannot replace a target, interpreter, argv prefix or environment」**对"调用"成立、对"替换 registry/改目标文件"不成立**，措辞强于实现。
　**升级条件**：若任何后续部署把 registry/interfaces 交由被审方或不可信方提供，或卡 A1 需在该威胁下成立 → 升级 BLOCKING。**建议**：validator 内固定 registry/interfaces 的 SHA-256 常量（同 `PROTOCOL_FREEZE` 做法），并在执行前核验 `target.git_blob_id`；同时把 A1 范围显式写成"以交付且身份正确的 registry 为前提"。

**ADVISORY-NEW-2**（类别 evidence-completeness）：`run_probes.py` 首败即 `return 3`，失败时仅产 1 条记录。v1、v2 两轮诊断均被此放大。建议收集完全部用例后统一返回非零。

**ADVISORY-NEW-3**（类别 fixture-design / informational）：`valid_delivery_call.json` 把 pin 与 `summary_text` **同文件并置**且 `pin == summary_sha256`，故测试仅证机制、未证 pin 来源独立性；另 Y15 显示**空 `summary_text` + 匹配 pin 即被接受**——身份绑定不裁内容充分性，属设计口径，但建议在 caller_contract 写明"不裁摘要内容质量"。

**ADVISORY-NEW-4**（类别 artifact-polish / informational）：`recipe_interfaces.json` `error_surface` 数组第 319–322 行（新增四个 `FC_*`）缩进漂移，JSON 可解析但格式与上下文不一致。建议规整。

---

## 9. dissent（如实记录，供收口者/owner 复核）

**dissent-1（宽读法边界的更严读法）**：Y06 / X06C（`summary_text`+`summary_sha256`+`expected_artifact_sha256` 三者同时伪造且自洽）被接受。存在一种更严的 A2 读法——「伪造摘要不能通过」应无条件成立，则 Y06 即为直接反例。我不采纳该读法为阻断：Loop D 裁决已明确「威胁边界（不防调用方自递假 pin）须显式声明」，而声明在 `recipe_interfaces.json:286`、`README.md:7`、`receipt.unresolved[0]` **三处显式存在且与实现一致**，交付探针集更把该情形显式编码为 `X06C` 且 `expected=ACCEPT`。故记为**已声明边界事实**。**但**边界实质是信任假设而非机制：pin 与摘要同在一个 `call` 对象内传递，「生产者控制之外」无法由 validator 验证。

**dissent-2（更优构造，已存在却未用）**：`recipe_fixtures/delivery_payload.json` 内含 `summary.text`，与合法 `summary_text` **逐字相同**，而该包已由 `package_sha256` 真绑定（读文件实算）。若把摘要校验绑定到**包内 `summary.text`**，则即使调用方递假 pin 也无法伪造（伪造须改包字节 → 触发 `FC_HASH_BINDING_MISMATCH`）。该构造**严格强于**裁决采纳的外部 pin 形态，且绑定源已在交付件中。Loop D 已裁决外部 pin 形态可接受，故不计缺陷；记此供 owner 在后续演进中考虑，或据此收窄 `unresolved` 的措辞边界。

---

## 10. 判定与理由

**判定：REJECTED（1 项 BLOCKING）**

**理由**：
1. **T5R-01 两项 blocking 均实质修复，且经判别性独立复现证实**。BLOCKING-1 的执行位已三方交付（worktree/index/HEAD `100755`），原阻断命令链 rc=0，fresh-delivery 真从交付态重建并恢复执行位；BLOCKING-2 的三重相等成立，我用「伪造者会算自身哈希」的判别性反例 Y01 被 `FC_PIN_MISMATCH` 阻断，六个 pin 形态破坏尝试全部 fail-closed，威胁边界三处显式声明。**A1/A2/A3/A-common 现均为 PASS(CONTRACT)**。
2. **但头号交付主张仍不可从交付态复现**，与 T5R-01 BLOCKING-1 同族同类、同一受损主张、同一失败签名（`run_probes.py` 首败即 rc=3、止于 P01）。T5R-01 已把「交付态下无法独立复现头号主张」定为 BLOCKING，本轮按**同一标准**判级，不因已修复两项而放宽。
3. **并触及包自身冻结保护声明**：回放唯一路径原地覆盖一件 SHA-256 绑定的原始记录，与 `FP-RAW-RECORD-INTEGRITY`「原始记录只读、不覆盖匹配夹具」及 `hash_domain=sha256_file_bytes_plus_mode` 自证口径直接冲突。这不是 UX 不便，而是**证据交付包的自证性破口**——恰是本卡主题（A2：伪造证据不能通过）。
4. **取 REJECTED 而非 PENDING_HUMAN_REVIEW**：修法不需扩权、不需重跑实验、不需动冻结件，在 `runs/T5/{run_id}/` 内即可完成，理由同 T5R-01 §7 第 4 条。
5. **其余面质量良好且有实质进步**：45/45 manifest（含 mode）全等、三方身份 46/46、22/22 绑定、6 处 freeze 一致；17 负例码精确、我 15 个新对抗探针中 11 个 fail-closed 码精确；G1 4/4；四类分离与 7 项 frozen_protections 到位且未减少；TASK_PROMPT 逐字节一致；usage 42/16/4 与我独立计数一致；6 个 advisory 全部闭合且工件可复核；`unresolved`/`attempt1/2` 失败工件/`unexpected_touched` 披露诚实。**无任何证据表明伪造或越权**；本轮阻断是工程与证据耐久性缺陷。

**next_steps**（仅建议；registry/state 由收口者更新）：
1. 修 BLOCKING-1（本轮）：P01 改 `max_tick_age_minutes=0`（与 `recipe_interfaces` 一致）或把 tick 生成移出 manifest 路径；`README.md` 补回放入口；统一 `max_tick_age_minutes`；建议 `run_probes.py` 不早退。
2. 重出自检（manifest、write boundary、G1、usage、两轮矩阵）后重交 T5；再申请一次 Loop C 名额。
3. 一并处理 ADV-NEW-1（registry/interfaces 身份固定 + 目标 `git_blob_id` 核验 + A1 范围显式化）——此项最值得在下一轮顺手完成。
4. 参考 dissent-2 考虑把摘要校验绑定到 hash-bound 包内 `summary.text`（更严构造），或据此收窄 `unresolved` 措辞。
5. **不得进入 T6**；registry/state 不由本评审更新。
