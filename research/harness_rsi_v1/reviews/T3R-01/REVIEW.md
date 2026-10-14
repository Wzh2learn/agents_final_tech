# T3R-01 — Loop C 独立评审：harness_rsi_v1 T3 可信执行与计数

- **评审对象**：`research/harness_rsi_v1/runs/T3/20261014T161814Z_245b86ab/`
- **评审者**：Loop C 独立质量审计层（GB10，hostname `promaxgb10-0b48`，Python 3.12.3，aarch64）
- **本卡 Loop C 名额**：1 次（已消耗）
- **写入**：仅 stdout。未修改任何被审文件、未做 git 写、未联网、未调模型/生产/数据库、未进入 T4。
- **判定**：**ACCEPTED**（0 BLOCKING / 8 ADVISORY）

---

## 1. 范围与方法

只读审阅 T3 run 包 + `cards/T3.md` + 5 个 contracts + T2/T2R-01 依赖。方法为**独立复算 + 反证**，不接受 run 自述结论：

1. 计数与哈希全量重算（不用包内任何声明值作为输入）。
2. 输入绑定用**三种独立方法**交叉验证。
3. 在仓库外新 scratch **实跑资格脚本两遍**，自派 pass-id，比对声明哈希。
4. 用对抗探针构造包内未覆盖的输入面，检验拒绝面是否真实成立。
5. 静态审计 runner 调用图，找声明与实现域的偏差。
6. 反伪造扫描 + 写入边界 mtime 扫描。

**证据分级**：`FACT` = 本会话实测/实算；`INFERENCE` = 由事实推断；`UNVERIFIED` = 本会话无法验证。

---

## 2. 逐项结果

### 2.1 run 目录计数与 manifest — FACT

| 命令 | 结果 |
|---|---|
| `find <run> -type f \| wc -l`（复审起始） | **234** ✔ |
| `git ls-tree -r --name-only HEAD -- <run>/` | **234** ✔（第三方独立源） |
| manifest `artifact_count` / 实际条目 | 233 / 233 ✔ |
| 逐条 SHA-256 + 字节实算 | **233/233 全一致，0 mismatch** ✔ |
| `self_hash_excluded` | `true`；manifest 自身不在条目内 ✔ |
| 磁盘遗漏 / 多余 | 在清单 scope 内 **0 遗漏 0 多余** ✔ |

233 条目 + manifest 本体 = 234，与磁盘起始计数、git 跟踪数三方吻合。

### 2.2 input_bindings 8 条 — FACT（三法互证）

`git` 在本会话**未被拒**（与派发预告不符，如实记录）。故采用三法：

- **法 A**：字节派生 git blob SHA-1（`blob %d\0`+内容，python3）— 7 条 git_blob 域全中
- **法 B**：解析 `.git/index`（DIRC v2，3663 条目完整解析）— 7 条全中
- **法 C**：run 自述的 `git rev-parse HEAD:<path>` 实跑 — 7 条 exit 0 且全中

| role | declared | 三法 | 结论 |
|---|---|---|---|
| card_input_protocol | `c57937c8…6bf` | A=B=C | PASS |
| card_input_authority_map | `46acca7e…fed` | A=B=C | PASS |
| card_input_execution_policy | `e0569763…28d` | A=B=C | PASS |
| card_input_budget_profiles | `64634474…30e` | A=B=C | PASS |
| card_input_schemas | `07731a30…899` | A=B=C | PASS |
| t2_accepted_run_dependency | `891955a6…596` | A=B=C | PASS |
| t2_independent_review_dependency | `ec21e3ed…f59` | A=B=C | PASS |
| dispatch_traceability (`TASK_PROMPT.md`) | sha256 `3a5ba884…09a` | sha256 实算 = declared | PASS |

**protocol_freeze_check**：`protocol.json` 的 `/freeze_sha256` = `282f52133a682e927c82b771fa103c27da34db7acbd8a12d2921f42a6d0bf36b`，与 receipt 声明、派发预期**三方一致**。

### 2.3 实跑资格（核心）— FACT

```
python3 .../runner/run_qualification.py --pass-id LOOPC_A --output <scratchA>/result.json --scratch-root <scratchA>/scratch
python3 .../runner/run_qualification.py --pass-id LOOPC_B --output <scratchB>/result.json --scratch-root <scratchB>/scratch
```

| 项 | LOOPC_A | LOOPC_B | 声明 | 判定 |
|---|---|---|---|---|
| exit code | 0 | 0 | 0 | PASS |
| stderr | **空**（0 字节） | **空**（0 字节） | — | PASS |
| 检查数 | **32/32** | **32/32** | 32/32 | PASS |
| `normalized_result_sha256` | `0a596362…3ed2` | `0a596362…3ed2` | `0a596362…3ed2` | **PASS（等于声明）** |
| 两遍一致 | ✔ checks 逐条全等 | | | PASS |

对 `normalized` 元组**独立重算**哈希（不信任脚本自写字段）：两遍均得 `0a5963625b637945eaf91610ea3505b7f9b94f4ae2039b265cd149dde8163ed2`，与声明值**逐字节相等**。与 Loop A 存档 `qualification_pass_1_final.json` / `pass_2_final.json` 的 checks **逐条全等**。

**14 次 mock transport 分项重算**（扫 `PASS_1_FINAL` + `PASS_2_FINAL` 全部 14 个 `run_summary.json`）：

| 分项 | 每轮 | 两轮实算 | 声明 | 判定 |
|---|---|---|---|---|
| failed | 1 | **2** | 2 | PASS |
| timeout | 1 | **2** | 2 | PASS |
| manual_retry | 1 | **2** | 2 | PASS |
| success | 3 | **6** | 6 | PASS |
| crash | 1 | **2** | 2 | PASS |
| **合计 transport_calls** | 7 | **14** | 14 | PASS |

### 2.4 A1 / A2 / A3 / A-common 逐条 + 拒绝面 — FACT

全部在**我方 scratch 复现**，非复述：

- **A1 duplicate_id**：exit **2**（精确值，非仅 nonzero）、sentinel 字节不变、**无** `run_summary.json`/`run_state.json` — PASS
- **A1 crash**：exit 4、`request.json`+`crash.json` 保留、`INCOMPLETE`、`crashed_requests=1` — PASS
- **A1 overwrite**：`preexisting.txt` 不变、**无** `request.json`、`overwrite_rejection.json` 存在、`overwrite_rejections=1` — PASS
- **A2 budget 无旁路**：cap=0 → exit 5、`transport_calls=0`、`model_extra_requests=0`、`budget_rejection.json` 保留、无 attempts/ — PASS。**边界正确**：cap=1 跑 2 次 transport → 仅 1 次放行、第 2 次 `budget_rejections=1`、exit 5，无 off-by-one。
- **A2 monotonic_counts**：f/t/mr/s = 1/1/1/1、`model_extra_requests=4`、`manual_retries=2`、`count_history.jsonl` 14 条增量**逐条 `after>=before` 且按计数器单调** — PASS
- **A2 policy_denied**：5 类 `file_path/network/sealed/production/database` **各拒一次**，`denial_reason` 分别为 `path_outside_run_allowlist` / `network_denied` / `sealed_access_denied` / `production_access_denied` / `database_access_denied`，证据 5 份，`transport_calls=0` — PASS
- **A2 split_accounting**：`model_extra_requests` 与 `execution_chat_usage` 分字段，后者 `UNRESOLVED`（非 0）— PASS
- **A2 persist_before_call**：`request.json` 独占创建；事件序 `request_persisted → transport_called → transport_result`；`request_persisted_before_transport=true` — PASS
- **A3 LOCAL 标注**：7 个产物（runner.py / run_qualification.py / README / permission_matrix / runner_qualification / summary / receipt）**均含 LOCAL**，**均不声称** GB10 权威绑定与 OS 级隔离；正向声明扫描（"GB10 verified/bound"、`os_sandbox: true`、"seccomp enforced" 等）**零命中** — PASS
- **A-common**：JSON 145 + JSONL 49 全可解析；py 全可 `ast.parse`；manifest 完备；哈希一致；写入边界干净；未知项显式列出 — PASS

**对抗探针**：

| 探针 | 期望 | 实测 | 判定 |
|---|---|---|---|
| 路径穿越 `../`（policy_probe） | 拒 | 2 条 policy_rejection | PASS |
| 未知 action type | fail-closed | exit 4 + `unexpected_crash.json`（`ValueError`） | PASS |
| 未知 policy category | 拒 | `kernel_seccomp` → policy_rejection，无 crash | PASS |
| 非法 run_id（5 变体，含 `../../../etc/passwd`、大写 hex） | exit 6 | 全部 exit 6 | PASS |
| runner.py 网络导入 | 无 | imports 仅 `__future__/argparse/json/re/sys/pathlib/typing`；`urlopen/socket/requests/http/subprocess/eval/exec/pickle/__import__` **全零命中** | PASS |
| 资格脚本真跑 runner | subprocess | `subprocess.run` + `sys.executable` 调 `runner.py`，**非** import 自证；checks 读 returncode + 磁盘证据 | PASS |
| **`attempt_id` 带 `../`** | **拒** | **逃出 run 目录，写入 `request.json`+`response.json`，exit 0** | **FAIL → A1** |
| **`preseed_attempts` 带 `../`** | **拒** | **逃出 run 目录，写入 `preexisting.txt`，exit 0** | **FAIL → A1** |

### 2.5 披露一致性 — FACT

- **`issues_found_and_fixed` 两处修复**与留存证据**精确吻合**：
  - 修复 1（`attempts/` 父目录）：`qualification_work/PASS_1` 的 4 个 transport 类 case 均留有 `unexpected_crash.json`，错误文本为 `FileNotFoundError: .../attempts/attempt-0001`，且**无** `attempts/` 目录 — 逐字证实。
  - 修复 2（`run_state` 独占写）：`qualification_work/PASS_1_RETRY` 的 `attempts/` 已生成、`unexpected_crash` **0 个**、`run_summary` 已写出，7 个 case 全部 exit 6 — 与"错误在 try 块外抛出到 main 的 OSError 处理器"完全一致。
  - 失败历史未删除（PASS_1 / PASS_1_RETRY 完整留存）— 符合"历史记录不删"。
- **`_dispatch/loop_a_prompt_t3.md` "早 58 秒、未被修改"**：mtime `2026-10-15 00:17:16 +0800` vs `TASK_PROMPT.md` `00:18:14` → **Δ=57.5s ≈ 58s** ✔；文件早于 run 窗口起点，内容为派发原文 — 属实。
- **`execution_policy.json` vs `.md`**：contracts 目录**仅有** `execution_policy.md`，无 `.json`；派发原文确写 `contracts/{...execution_policy...}.json`；run 按卡列路径绑定 `.md` 并披露 — **属实**。

### 2.6 写入边界与零调用 — FACT

mtime 全仓扫描（run 窗口 `00:18:09–00:45:25 +0800`）：

- 窗口内文件 **234** 个，**全部**在 run 目录内；**窗外 0 个** — 写入边界干净。
- `git status --porcelain --untracked-files=all` 仅 4 条 `logs/graph` 预存脏件，与会话起始快照一致 — 未新增越界写入。
- `events.jsonl` 13 条事件、receipt.usage 的零 network/model/production/db/training/remote 声明 — **无任何相反证据**（runner 无网络能力，静态审计零命中）。
- **无伪造**：正则扫描全包，`ACCEPTED` 仅出现在**引用 T2R-01 依赖事实**处；无 `PROMOTED`/`SCIENTIFIC_PASS`/`GB10_VERIFIED`/`ACTIVATED`。三轴 **`DELIVERED / UNREVIEWED / NOT_ENABLED`** 正确。

### 2.7 包自检重算 — FACT

按 receipt.checks 20/20 的方法重算关键面：JSON/JSONL 全解析 **PASS**、manifest 完备性 **PASS**、二轮一致性 **PASS**、LOCAL 标注 **PASS**、allowlist/isolation 免责 **PASS**、写入边界 **PASS**。包自检结论与我方独立结果一致。

---

## 3. 反自证分析（防"只输出预设 PASS"）

**结论：资格脚本不是自证循环，判定可信。** 依据：

1. **断言来自实测非常量**：32 条 check 的 `condition` 全部取自 `subprocess.run` 的 `returncode`、磁盘文件 `exists()`、`read_json` 解析出的计数器与事件序列。逐行扫描 `run_qualification.py`，**无** `check(..., True, ...)` 硬编码真值。
2. **实现与测试确为同一作者，但非同源自证**：runner 与 qualification 同包产出，存在"测试与实现同源"的固有局限。但测试观测的是**外部可验信号**（进程退出码、磁盘落盘、计数器序列），而非 runner 的自述字段。故同源性降低了独立性，但**未**使断言沦为常量。
3. **资格覆盖面不足以证明全部声明** —— 这是本次的核心发现：32 条 check **从未触碰** `attempt_id`/`preseed_attempts` 路径穿越面。因此 "32/32 PASS" **不能**推出 permission_matrix 的 allowlist 声明成立。见 A1/A2。
4. **`run_summary` 中 `count_monotonic`/`network_used`/`mock_transport_only` 为硬编码常量**，非派生。所幸资格脚本另行独立验证了 `count_history` 单调性，且网络零能力由静态审计独立证实，故结论仍成立（记 A4）。
5. **allowlist 声明 vs `ensure_path_allowed` 实现域**（任务指定重点）：`ensure_path_allowed` 全包**仅 1 个调用点**（`runner.py:147`，仅服务 `policy_probe` 的 `file_path` 类）。其余写入路径中，`attempts_dir / attempt_id`（L176/201/269/304）与 `run_dir/"attempts"/preseed`（L320/321）**均绕过该检查**。permission_matrix 声称 "resolved-path containment check **before any runner read or write**" —— **该表述为假**。见 A1。

---

## 4. BLOCKING 发现

**无。**

## 5. ADVISORY 发现

### A1 — `attempt_id` / `preseed_attempts` 逃出 run 目录写入，证伪 permission_matrix 的包含性声明
- **类别**：security / correctness｜**严重度**：**highest**
- **证据**（FACT，本会话实测）：fixture `attempt_id="../../escape_attempt"` → 在 `<workspace>/escape_attempt/` 落 `request.json`+`response.json`，run 目录内 `attempts/` **为空**，exit 0，无 policy_rejection。`preseed_attempts=["../../escape_preseed"]` → 在 `<workspace>/escape_preseed/` 落 `preexisting.txt`，exit 0。而 `policy_probe` 的 `../` 探测**被正确拒绝**。静态审计：`ensure_path_allowed` 仅 1 个调用点（L147）。
- **影响**：`permission_matrix.json` 的 `check_method`（"before any runner read or write"）与 `run_write_path`（"attempt request/response files **additionally** require exclusive create mode"）含**不成立的包含性主张**。A2 的"非法路径被拒"在**已声明的 policy_probe 机制上成立**，但**覆盖不到**这两个 fixture 派生字段。
- **建议**：对 `attempt_id`/`preseed` 拒绝路径分隔符与 `..`，或统一走 `ensure_path_allowed`；补 1 个穿越 fixture。
- **为何不阻断**：写入方由**操作者自供 fixture** 驱动，与运行者同信任域，T3 范围内无不可信输入入口；包在 7 个产物中一致声明 `POLICY_ONLY`/`os_sandbox=false`/"实际隔离未实现/未声称"，且卡 §4 明示"目录分开不当隔离证明"；失败面**不产生错误判定、不刷分、不泄封存**；`activation_status=NOT_ENABLED`，T4 未进入；正常 fixture 下 run 全部 234 文件均在 allowlist 内。
- **升级条件**：若收口者把 permission_matrix 字面包含性表述（"any runner read or write"）当作硬验收门，则升为 BLOCKING；**最小重审范围** = 该处路径规范化补丁 + 1 个穿越 fixture 的实跑证据，其余 32 条资格与 233 条 manifest 不需重审。

### A2 — 32 条资格未覆盖穿越面与预算中段边界，"32/32" 不足以背书 allowlist 声明
- **类别**：test-coverage｜**严重度**：medium
- **证据**（FACT）：`run_qualification.py` 的 `case_specs` 7 例 + duplicate 例均使用包内静态 fixture；无任何含 `..` 的 `attempt_id`/`preseed` 用例。`budget_bypass.json` 第 2 个 action 因首个即抛 `BudgetExhaustedError` 而**从未执行**，故 cap>1 的中段截断未被固定（我方独立实测 cap=1×2 行为正确）。
- **影响**：资格分数不能外推到未测面；A1 因此得以通过自检。
- **建议**：补穿越 fixture、cap=1 双请求 fixture、未知 action type、非法 run_id 各 1 例，纳入 32 条。

### A3 — `strong_requests` 预算轴仅携带、不设限
- **类别**：spec-fidelity｜**严重度**：medium
- **证据**（FACT）：`runner.py:67-68` 仅 `int(profile.get("cheap_requests", 0))` 进入 `budget_cap`；`strong_requests` 全文**无任何检查点**。卡 §8 要求"共享 profile 总额与单卡上限取更严格者"、"额外强模型请求上限 0"。
- **影响**：强模型请求轴无预算闸；当前 mock 仅单轴 transport，故未触发，但声明的双轴约束未完整实现。
- **建议**：为 `strong_requests` 独立计数与闸，或在 permission_matrix/README 明示"本 runner 仅执行 cheap 轴"。

### A4 — `run_summary` 的 `count_monotonic`/`network_used`/`mock_transport_only` 为硬编码常量；`previous_counters` 为死字段
- **类别**：evidence-reproducibility｜**严重度**：low
- **证据**（FACT）：`runner.py:299/380/384/386` 为字面量；`previous_counters` 仅初始化后 1 次出现（赋值），从不读取。
- **影响**：读者可能误认为 `count_monotonic` 为算出值。结论本身成立（资格独立复算 `count_history`；网络零能力由导入审计独立证实）。
- **建议**：由 `count_history` 派生该字段；删除死字段。

### A5 — `duplicate_id` 断言弱于自述：`exit_nonzero` 而非 `exit == 2`；未断言 stderr 为空
- **类别**：test-coverage / assertion-strength｜**严重度**：low
- **证据**（FACT）：`run_qualification.py:123` 为 `duplicate.returncode != 0`；receipt/check 文字称 "exit 2"。我方独立实测 **exit=2**、stderr 空 —— **行为正确，断言偏弱**。
- **建议**：改为精确 `== 2`，并加 stderr 空断言。

### A6 — 三处错误分类/闸门边界问题（行为 fail-closed，语义不齐）
- **类别**：correctness / error-taxonomy｜**严重度**：low
- **证据**（FACT，本会话实测）：
  1. `overwrite_probe` **不经** `check_budget`：cap=0 时仍写出 `request.json`，且 `budget_rejections=0`（未记预算拒绝）。
  2. `preseed_attempts` 重复 → `FileExistsError` 在 try 块**外**抛出，exit 6，**无 `run_summary`**，`run_state` 永留 `RUNNING`。
  3. transport 内重复 `attempt_id` → `OverwriteRejectedError` 落入通用 `except`，exit 4 + `unexpected_crash.json`（而非结构化 overwrite 拒绝）。实质保护成立：旧证据保留、`overwrite_rejections=1`。
- **影响**：计数与拒绝语义略不对齐；(2) 留下悬挂 `RUNNING` 态。
- **建议**：`overwrite_probe` 也过预算闸并记拒绝；preseed 循环移入 try 并给结构化拒绝；`OverwriteRejectedError` 单独分类。

### A7 — `model_extra_requests` 字段名跨账本重名
- **类别**：auditability｜**严重度**：low
- **证据**（FACT）：`receipt.usage.model_extra_requests = 0`（B0 真实模型额外请求），而 mock runner 内部同名计数器两轮合计 **14**。已由 `mock_transport_requests_across_two_formal_qualification_rounds: 14` 与 `events.jsonl` 的 `model_extra_requests_in_mock_qualification: 14` 分开披露。
- **建议**：将 usage 字段改名为 `model_extra_requests_real` 以免误读。

### A8 — 审阅侧在被审 run 目录内产生 1 个仓库内文件（本评审自身副作用）
- **类别**：reviewer-hygiene / disclosure｜**严重度**：low（**归属：T3R-01 审阅者，非 Loop A**）
- **证据**（FACT）：`.omc/state/sessions/2f6dad8a-0f18-4838-bd29-2aaf3c38d9c2/pre-tool-advisory-throttle.json`，mtime `2026-10-15 01:03:03 +0800`（run 窗口 00:18–00:43 **之后**，我的会话进行中），内容为 OMC pre-tool 钩子节流状态，含本会话收到的钩子文案。成因：我执行 `cd <run目录> && find` 时 shell CWD 落入 run 目录，OMC 钩子向 CWD 写 `.omc/`。发现后已将 CWD 移至仓库根。
- **影响**：run 目录磁盘现为 **235** 文件 = 234（原始，与 `git ls-tree` 一致）+ 1（本文件）。该文件被 `.gitignore` 的 `.omc/` 规则忽略，**不进 manifest、不进 git**，故不影响 233/234 的完整性重算与写入边界结论。
- **建议**：收口层可删除该 `.omc` 目录（我无 `rm` 权限且不得改动被审包，故保留并披露）。**请勿据此追责 Loop A。**

---

## 6. FACT / INFERENCE / UNVERIFIED 分离

**FACT（本会话实测/实算）**
- 计数 234 / manifest 233 全哈希与字节一致 / 无遗漏无多余；`git ls-tree` 独立得 234。
- 8 条 input_bindings 三法（字节派生 blob SHA-1、`.git/index`、`git rev-parse HEAD:`）全一致；TASK_PROMPT sha256 一致。
- protocol freeze `282f5213…` 三方一致。
- 两遍实跑各 32/32、exit 0、stderr 空、`normalized_result_sha256` **等于** `0a596362…3ed2`，且独立重算复现同一哈希。
- 14 次 mock transport 分项 2/2/2/6/2 与声明全等。
- A1/A2/A3/A-common 关键断言全部在自建 scratch 复现。
- 预算无旁路：`transport_calls` 全包唯一递增点 L253，`check_budget` L245 恒在其前；cap 边界正确。
- 路径穿越经 `attempt_id`/`preseed_attempts` 可逃出 run 目录（2 例实测）。
- 披露两处修复与 PASS_1 / PASS_1_RETRY 证据逐字吻合；`_dispatch` Δ57.5s；`execution_policy.md` 唯一存在。
- run 窗口 234 文件全在 run 目录内、窗外 0；三轴 `DELIVERED/UNREVIEWED/NOT_ENABLED`；无伪造验收字样。
- 该 run 已被提交于 `fafb27fb7`（Wzh2learn，2026-10-15 00:52:55 +0800），工作树与 HEAD 一致；我未做任何 git 写。

**INFERENCE（由事实推断）**
- `PASS_1` 的 `FileNotFoundError` 与 `PASS_1_RETRY` 的全 exit 6，分别对应自述的两处修复，时间序与因果链自洽。
- 资格脚本非"预设 PASS"：断言取自外部可验信号而非 runner 自述。
- A1 因资格未覆盖面（A2）而未被自检发现。

**UNVERIFIED（本会话无法验证）**
- OS 级隔离、namespaces、seccomp、capabilities、跨用户隔离 —— 未实现且未声称，无法验证，也未据以扣分。
- GB10 权威运行面绑定与正式 GB10 资格 —— 包内一致声明未执行；我方 hostname 为 `promaxgb10-0b48`，但**未**以硬件探针独立复核，故不对 T3 的 GB10 面作任何背书。
- 执行对话 token 用量 —— `UNRESOLVED`，不作 0。
- 封存根 —— `UNRESOLVED`，无封存访问。
- 生产/数据库/训练/网络/真实模型端点行为 —— 零调用，无从验证。
- `execution_policy.json` 命名分歧的**上游意图**（派发 vs 卡）—— 仅能证实差异属实，不能裁决孰对。

---

## 7. 判定与理由

### **ACCEPTED**（0 BLOCKING / 8 ADVISORY）

**理由**：
1. **全部声明的验收断言面已独立复现**：A1 三项（重复 ID 精确 exit 2 / 崩溃证据保留 / 覆写拒绝）、A2 五项（预算无旁路含 cap 边界、计数单调、五类拒绝各带证据、分账、写前落盘）、A3（LOCAL 一致、GB10 与 OS 隔离零声称）、A-common（解析、必需字段、allowlist、哈希、写入边界、未知显式）。
2. **核心计数与身份绑定达到三重独立验证**：234/233 计数由磁盘 + git + manifest 三方吻合；8 条绑定由三法吻合；两遍实跑哈希**等于**声明值且可独立重算复现 —— 包的可复现性主张成立。
3. **零外部调用经静态与动态双向证实**：runner 无网络能力（导入审计零命中），事件与 usage 声明无任何相反证据。
4. **披露诚实**：两处修复留有失败证据且历史未删；命名分歧、预存脏件、未验证面均如实列出；三轴未越权。
5. **A1 虽为真实的声明/实现落差，但未击穿任何验收断言的具名条件**，失败面不可用于刷分/出错误判定/泄封存，输入位于操作者信任域，包级 `POLICY_ONLY` 免责完整，且 `NOT_ENABLED`、T4 未进入。按 T2R-01 的校准纪律（"失败响亮、不改判定、不影响具名验收条件 → 附升级条件收口"）归入 ADVISORY **highest**，而非 BLOCKING。

**内部备选裁量已记录于 `dissent`**（runner-up = REJECTED），升级条件与最小重审范围已逐字给出，供收口层/人工裁决保留。

**本判定不授予**：正式实验权限、科学 PASS、封存访问资格、promotion、部署、GB10 权威绑定、OS 级隔离、T4 进入。registry/state 由收口者更新。
