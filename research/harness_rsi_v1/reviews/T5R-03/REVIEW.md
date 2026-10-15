# T5R-03 — Loop C 独立评审：harness_rsi_v1 T5 v3 返工（第三轮）

- Reviewer：Loop C（独立质量审计层，GB10）
- 被审对象：`research/harness_rsi_v1/runs/T5/20261014T233742Z_cb132ce7/`（46 文件，已提交 `ebd2710a1078bbfe637528fb69013c24f208b002`）
- 前史：T5 v1 → T5R-01 REJECTED（2 blocking）；T5 v2 → T5R-02 REJECTED（1 blocking + 4 advisory）；v3 = 本轮返工对象
- **裁决：REJECTED（1 blocking）**。T5R-02 的 replay-stability blocking **实质已闭合并被独立复现**；剩余缺陷窄、局部、廉价可修，但直接命中 A-common 与前两轮确立的「头条主张须可从交付态复现」标准。

---

## 1. 摘要

v3 在真正的工程难点上做对了。T5R-02 的 blocking（replay 不稳定）已闭合，我用交付入口独立复现：四轮各 23/23、归一化结果逐项一致、两树重放前后不变、**并且我用自建的全量 sha256/bytes/mode/mtime_ns 扫描独立证明交付树 46 文件零写入**。run 内确无 prepare 路径，所有写路径都指向外部 root。NEW-1/2/3/4 四条 advisory 全部折叠，且我逐条对抗复验通过。T5R-01 的执行位修复（`watcher.sh` 100755）在工作树、`.git/index`、HEAD 树三处均保持。

阻断点是另一个问题，且是 T5R-01 同类缺陷的复发：**`artifacts_manifest.json` 为 4 个脚本声明 `mode: "100755"`，但交付字节（工作树、`.git/index`、HEAD 树三者一致）都是非可执行位**。manifest 自称 `hash_domain = sha256_file_bytes_plus_mode`，于是 45 条里 **41 条实算一致、4 条在 `mode` 字段失配**。后果是 README 指定的唯一无前置入口 `scratch/verify_replay.py` 对交付态返回 **rc=3**，而包内三份证据（`scratch/replay/replay_summary.json`、`scratch/self_check_result.json`、`events.jsonl`）都断言 manifest 45/45、`passed: true` —— 这一头条主张无法从交付态复现。

按 T5R-01/T5R-02 一致标准判定为 blocking。这不是完整性指控：交付快照记录作者当时 4 个文件确为 100755，作者当时的 45/45 很可能属实；缺陷是证据耐久性/交付自证性（mode 位在 commit 前后丢失），正是 T5R-02 用过的同一措辞。

---

## 2. 独立复算：计数 / 哈希 / 模式

| 项 | 结果 |
|---|---|
| 交付文件总数 | 46（manifest 45 条 + 不自哈希的 `artifacts_manifest.json`）— 一致 |
| manifest 条目数 / `artifact_count` | 45 / 45 — 一致 |
| 逐条 SHA-256 + bytes 实算 | **45/45 字节与哈希全部一致**（0 字节失配） |
| 逐条 mode 实算 | **41/45 一致，4 条失配** ← 阻断源 |
| `missing_on_disk` / `extra_on_disk` | [] / [] |
| `required_executables` | `["recipe_fixtures/dispatch/watcher.sh"]` — 该文件确为 100755，处置正确 |

mode 失配 4 条（声明 vs 实测）：

| 相对路径 | manifest 声明 | 工作树 | `.git/index` | HEAD 树(`ebd2710`) |
|---|---|---|---|---|
| `run_probes.py` | 100755 | 100664 | 100644 | 100644 |
| `scratch/adversarial_checks.py` | 100755 | 100664 | 100644 | 100644 |
| `scratch/self_check.py` | 100755 | 100664 | 100644 | 100644 |
| `scratch/verify_replay.py` | 100755 | 100664 | 100644 | 100644 |
| `recipe_fixtures/dispatch/watcher.sh` | 100755 | **100755** | **100755** | **100755** |

其余 41 条分组核对：11 条声明 100644 全部实测 100644（0 漂移）；29 条声明 100664 全部实测 100664（0 漂移）。**仅这 4 个执行位失配。**

关键判定：HEAD 树（`tree 82e1f718…` → run dir `824ae0dd…`）中 `run_probes.py` 为 `100644`。**该不一致是被提交进 `ebd2710` 的，不是脏工作树。** 被审对象即是该提交态，故包在自身 `hash_domain` 下不自证。

.git 无 CLI，按任务要求替代口径：字节派生 git blob SHA-1（`sha1("blob <len>\0" + bytes)`）+ 直接解析 `.git/index` 二进制（DIRC v2，3880 entries，按路径字节定位 entry 头读 mode）+ 直接解压 `.git/objects` 走 HEAD commit→tree 递归。`watcher.sh` 派生 blob id `742e13d6…` 与 index 记录、HEAD tree 记录三者一致。

---

## 3. replay-stability 核心（T5R-02 blocking 闭合验证）

**交付入口 `scratch/verify_replay.py --run-root <v3> --work-root <外部新路径>` → rc=3。**

拆解（我的 work-root：`/home/testuser/wzh/loop_runs/t5r03_recheck_a/work_replay_1`，运行前确认不存在，位于交付树外）：

| 断言 | 声称 | 我的实测 | 判定 |
|---|---|---|---|
| `prerequisites` | NONE | `NONE` | ✅ |
| 四轮完整矩阵 | 23/23 ×4 | PASS_1/PASS_2 × 两树，各 `record_count=23`、`passed=23`、`exit_code=0`、accepted=5/rejected=18 | ✅ |
| 归一化结果四轮一致 | true | `normalized_outcomes_identical_across_four_rounds: true` | ✅ |
| 两树重放前后不变 | true | `tree_unchanged: true`（两树） | ✅ |
| manifest 45/45 | 45/45 | current_tree **before/after 均 4 failures**；fresh_delivery 45/45 | ❌ |
| 总 `passed` | true | **false** | ❌ |

**独立二次验证（不经 verify_replay，直接用交付 CLI `run_probes.py` 跑交付树两遍）**：两遍各 23 条、逐项一致、rc=0。运行前后对交付树做全量 `sha256 + bytes + mode + mtime_ns` 扫描：**46 文件，ADDED=[]、REMOVED=[]、CHANGED_COUNT=0 → 零写入实证。**

**P01 / P09 时间语义核对**：
- `recipe_fixtures/valid_precheck_call.json` 的 `max_tick_age_minutes` 确为 **0**，与 recipe 声明一致。
- 目标工具 `scripts/graph/dispatch_precheck.sh` 的实现：`nonnegative_integer` 文档「0 = 不限年龄」，判定式为 `if args.max_tick_age_min > 0 and age_seconds > args.max_tick_age_min * 60`。**0 = 不施加上限**，但 `if age_seconds < 0: raise "observed_at 是未来时间"` 仍生效。
- 交付 tick `observed_at = 2026-10-14T21:56:53Z`（过去时刻）。过去时刻永远不触发未来拒绝，且 0 不做年龄上界 → **P01 严格时间可重放**。这是 v2 阻断的真正修复点，我确认其成立。
- P09 每次由 `runtime_tick()` 以 `datetime.now(UTC)` 生成新 tick，写入 `tempfile.TemporaryDirectory(dir=output.parent)`，而 `output.parent` 被 `run_probes.py` 强制在交付树外（`if output == run_root or run_root in output.parents: SystemExit`），配合 60 分钟界 → 稳定。
- **run 内无任何 prepare/改写路径**：全量扫描 `run_probes.py` / `caller_validator.py` / `scratch/*.py` 的写调用，目标只落在 `runtime_root`、`--output`、`work_root`、`mktemp`；`v2` 的 `prepare_runtime_fixtures.py` 已不存在；交付夹具 `dispatch/tick_valid.json` 未被改写（我的零写入扫描佐证）。
- `verify_replay.py` 对 work-root 的两道拒绝实测：已存在 → `refuse to overwrite replay work root` rc=1；树内路径 → `work root must be outside the delivered run tree` rc=1。两者均未向交付树写入任何字节。

**结论：T5R-02 BLOCKING-1 的实质缺陷（陈旧 tick + 就地改写 manifest 绑定夹具）确已闭合，且我独立复现。** 唯一未复现的是 manifest 计数主张本身（见 §5）。

---

## 4. NEW-1 信任边界对抗（自构造攻击）

**(a) 替换 `registered_operations.json`（副本）目标路径 + 内容 → 必须 `FC_INPUT_IDENTITY_MISMATCH` 且目标零执行**
- 复制 registry 到 scratch，把 `OP-T4-R-DISPATCH-PRECHECK` 的 `target.path` 指向外部 decoy（执行即 `touch` marker）。
- 结果：`rc=1`，`FC_INPUT_IDENTITY_MISMATCH`，detail `operations bytes do not match the embedded SHA-256 pin`，`target_execution_performed=false`，`operation_results=[]`，**marker 不存在（decoy 零执行）**。✅

**(b) 替换目标文件本身（scratch 副本 + 改字节）→ 执行前按 `git_blob_id` 复核被拒**
- 导入交付 `caller_validator.py` 的 `execute_operation`，构造 registry entry：`target.path` 指向 scratch 改字节副本（blob id `552e2372…`），`target.git_blob_id` 仍为真目标的 `c5045e95…`。
- 结果：抛 `FC_OPERATION_TARGET_IDENTITY_MISMATCH`，detail `… target bytes do not match registered git_blob_id`，**decoy marker 不存在 = 执行前被拒**。对照组（真目标 + 正确 blob id）正常 `wrapper=0/target=0`。✅
- 披露：层 2 的**端到端**验证需要改写仓库内 T4 adapter 字节，越出评审者写入边界，故以交付函数直接调用验证；层 1 的端到端组合由 (a) 与 Z01 覆盖。

**内嵌 pin 常量与交付文件实测比对**（全部精确一致）：
- `INTERFACES_SHA256` `52d5ec1e…` = `recipe_interfaces.json` 实测 ✅
- `OPERATIONS_SHA256` `2cc368b6…` = `registered_operations.json` 实测 ✅
- `PROTOCOL_FREEZE` `282f5213…` 与 receipt/协议一致 ✅
- `RUN_ID` = 目录名 ✅
- 三个登记目标 `git_blob_id` 全部与字节派生值一致（`c5045e95…` / `9f421f69…` / `7a3c9d1d…`）✅

**scope 措辞**：`registered_operations.json.path_policy.target_rule` 明确「verifies each target's bytes against target.git_blob_id before execution」；`registered_operations.json.scope`、`README.md`、receipt 均声明范围为 "against the delivered, identity-verified registry"。措辞与实现相符。✅

---

## 5. 前两轮闭合回归

| 项 | 结果 |
|---|---|
| `watcher.sh` 交付 100755 | 工作树 / `.git/index` / HEAD 树 **三处均 100755** ✅（T5R-01 P01 链保持） |
| X06A 无 pin | REJECT `FC_ARTIFACT_NOT_PINNED` ✅ |
| X06B 错 pin | REJECT `FC_PIN_MISMATCH` ✅ |
| X06C 全伪造+自洽正确 pin | ACCEPT（按 T5R-02 dissent-1 裁定边界）✅ |
| Z01 registry 替换 | REJECT `FC_INPUT_IDENTITY_MISMATCH`，decoy 零执行 ✅ |
| E10 异源 pin 正例 | ACCEPT，`pin_source=external_summary_pin.txt` ✅ |
| 15 原负例码精确 | **15/15 expected == actual 逐条精确**（P02–P08、E02–E09）✅ |
| 四类分离 | 两 recipe 均 qualification/audit/execution/scientific，`overall_pass_field_forbidden: true`；E07 → `FC_SINGLE_OVERALL_PASS_FORBIDDEN` ✅ |
| frozen_protections | **7/7** 全在且全 FROZEN；`FP-RAW-RECORD-INTEGRITY` 本轮无就地改写，未被违反 ✅ |
| TASK_PROMPT 逐字节 | 与 `runs/T5/_dispatch/loop_a_prompt_t5_v3.md` **字节全等**（4368 bytes，sha256 `dd77d244…`）✅ |
| G1 每个 `.md` rc=0 | 我用 `summary_recompute_guard.py check` 独立跑 **5/5 rc=0** ✅ |
| 无裸 PASS / 无越级 | 正文无越级断言；`self_check_result.json` 的 `"status":"PASS"` 均挂在具名 `check_id` 下；overall 仅 `CONTRACT_PASS`，未冒称科学/正式 ✅ |
| usage 零声明与 92 自洽 | `final_acceptance_caller_processes=92` = 4 轮 × 23，与我的复现一致；其余 11 项调用计数 0；`execution_chat_usage="UNRESOLVED"`（未伪零）✅ |
| SUMMARY-GUARD 绑定 | `receipt.json` 实测 sha256 `285c808d…` 与 summary/repair_record 声明一致 ✅ |
| 写入边界 | run 内 Python 无任何指向交付树的写路径；`.git/*` 变更属 `ebd2710` 提交本身 |

---

## 6. 新对抗探针（5 负 + 2 正，全部自构造）

| 探针 | 构造 | 期望 | 实测 | 判定 |
|---|---|---|---|---|
| NEG1 陈旧 tick | `observed_at=2020-01-01T00:00:00Z` + `max_tick_age_minutes=30` | 拒 | `FC_OPERATION_TARGET_FAILURE`，target_execution=false | ✅ |
| NEG2 未来 tick | `observed_at=2030-01-01T00:00:00Z`，age=0 | 拒 | `FC_OPERATION_TARGET_FAILURE`，target_execution=false | ✅ |
| NEG3 runtime symlink 逃逸 | `runtime/tick_valid.json` → 指向 runtime root 外文件 | 拒 | `FC_ARBITRARY_PATH` `runtime path escapes runtime root` | ✅ |
| NEG4 pin 类型畸形 | `expected_artifact_sha256 = 123456`（整数） | 拒 | `FC_ARTIFACT_NOT_PINNED` | ✅ |
| NEG5 pin 类型畸形 | `expected_artifact_sha256 = null` | 拒 | `FC_ARTIFACT_NOT_PINNED` | ✅ |
| POS1 合法新调用 | 新鲜 runtime tick + `max_tick_age_minutes=30` | 受 | `ACCEPTED_WITHIN_SCOPE`，2 ops 执行 | ✅ |
| POS2 异源 pin 交付 | pin 读自 `external_summary_pin.txt` | 反 | `ACCEPTED_WITHIN_SCOPE` | ✅ |

**NEW-2 全矩阵独立复现**：翻转 P01 期望值后运行交付 `run_probes.py` → `rc=3`、**23 条记录全在**、首例 P01 失败、末例 `Z01-IDENTITY-VERIFIED-REGISTRY-SUBSTITUTION` 在场。与 `scratch/full_matrix_failure_evidence.json` 声称一致。✅

**NEW-3 / NEW-4**：`recipe_interfaces.json:289` `caller_contract.scope_boundary` 明确「Summary content sufficiency, quality, completeness and scientific interpretation are not judged」；`error_surface` 两处缩进一致；26 个 JSON 全部解析成功。✅

---

## 7. 披露核对与 supersedes 链条

`repair_record.md` 与 `v2_v3_diff.json` 的每条修复声明我都逐项对上实现与实测（P01=0、P09 外部 tick、无 prepare、全矩阵收集、双层身份、异源 pin、缩进、dissent-2 未实施并如实声明）。`receipt.supersedes.review_chain` 记录 T5R-01 REJECTED/2 blocking、T5R-02 REJECTED/1 blocking + 4 advisory —— 与两轮 `ACCEPTANCE_PROPOSAL.json` 实际内容一致。✅

**但披露面存在一处系统性不实**：`summary.md`、`repair_record.md`、`events.jsonl`(event 9)、`scratch/self_check_result.json`(`MANIFEST_45_OF_45` → `failures: []`)、`scratch/replay/replay_summary.json`(`passed: true` + manifest 0 failures)、`receipt.json`("manifest recompute 45/45") **六处**均断言 manifest 45/45，与交付态实算 41/45 不符。

---

## 8. 阻断项

**BLOCKING-1｜manifest mode 自证失效 4/45；无前置重放入口对交付态返回 rc=3；六处证据断言 45/45 不可复现**

事实链：
1. `artifacts_manifest.json` 为 4 个脚本声明 `mode:"100755"`，`hash_domain=sha256_file_bytes_plus_mode`。
2. 交付字节（工作树 100664 / `.git/index` 100644 / HEAD 树 100644）三者一致为**非可执行**；不一致已被提交进 `ebd2710`，非脏工作树。
3. 独立逐条实算：45 条中 41 条一致，4 条在 `mode` 字段失配；字节与 SHA-256 零失配。
4. 交付唯一无前置入口 `scratch/verify_replay.py` → **rc=3**，`current_tree.manifest_before/after.passed=false`，各 4 条 mode 失配，总 `passed=false`。
5. 包内六处断言 manifest 45/45 / `passed:true`（清单见 §7），无法从交付态复现。
6. 卡 A-common「声明哈希实算一致」在包自身 `hash_domain` 下**不成立**。
7. **同类复发**：T5R-01 BLOCKING-1 即执行位/mode 丢失致不可复现。v3 的 mode 纪律只覆盖了 `required_executables`（故 `watcher.sh` 三处幸存 100755），未覆盖 manifest 自身 mode 字段。

影响：T5 v3 头条交付主张「manifest 45/45」与 `replay_summary.passed=true` 无法从交付字节独立复现。按 T5R-01「头条主张不可从交付态复现即 blocking」、T5R-02 同一标准一致适用 → blocking。

**非完整性指控**：`scratch/replay/current_tree_snapshot_before.json` 记录作者当时 4 个文件确为 100755，作者当时的 45/45 很可能属实。缺陷是证据耐久性 / 交付自证性（mode 位在入库环节丢失），与 T5R-02 对 v2 的措辞同源。未发现伪造或越权。

**廉价本地修法（不扩权、不重跑实验、不改冻结件）**：
- (a) 要么恢复 4 个脚本执行位，要么把 manifest 的 `mode` 改为实际交付值 —— 二者取一，使 manifest 在 `sha256_file_bytes_plus_mode` 下与交付字节严格相等。
- (b) 在最终交付字节**之后**重建 manifest，并对**该**交付态重跑 `verify_replay.py`，要求 rc=0 且四次 manifest 检查均 45/45。
- (c) 据实重发 `scratch/replay/replay_summary.json`、`scratch/self_check_result.json`、`events.jsonl`、`summary.md`、`repair_record.md`、`receipt.json`，使全部「45/45」表述等于复算值。
- (d) 建议把记录口径归一到 git 语义（100644/100755），避免 umask 漂移。

---

## 9. 建议项

- **ADV-1｜fresh-delivery 腿对 mode 漂移失明**：`verify_replay.py:restore_modes()` 在 manifest 校验前把复制树 mode 强制改写（`os.chmod 0o644` → 回填 manifest 值，实测 `mode_reset_and_restore_count=45`）。这使 fresh 腿在 mode 上永远「通过」——正是本次逃逸缺陷的同类盲区。且它是重放路径中的一步 mode 改写（仅作用于外部副本、已披露）。建议移除该函数或在改写前先校验。
- **ADV-2｜manifest 记录 umask 相关 mode**：11 条 100644 与 29 条 100664 混录，跨环境/换 umask 检出即会大面积失配。建议只记执行位。
- **ADV-3｜非 JSON 失败面**：`--runtime-root` 落在交付树内、或 `verify_replay.py --work-root` 越界/已存在时，均 `raise SystemExit(文本)`，无 JSON 结果对象；调用方只能落入 `MALFORMED_RESULT/FC_INTERNAL`，而非规范 `FC_*`。虽 fail-closed，但错误面不在契约内。
- **ADV-4｜gitignore 视野的外部写者**：作者窗口内 `logs/`（app.log、loop_b.log、docs_lint_report.json 等 13 个）有变更，但 T5 代码路径无任何指向该处的写口，应属 Loop B/应用等外部进程。沿 T5R-02 先例列为未验证，不归因于 T5。

---

## 10. 异议记录

- **dissent-A（X06C / 主动假 pin）**：维持 T5R-02 dissent-1 的裁定与处置——验证器只裁决身份绑定，不裁决摘要内容；「调用方主动提供假 pin」在信任边界之外，且该边界已在三处一致声明。我同意按边界事实记录而非缺陷。
- **dissent-B（更强构造未采用）**：T5R-02 dissent-2 提出的「把摘要校验绑定到已哈希绑定的 `delivery_payload.json` 之 `summary.text`」仍是严格更强的构造，v3 按指令未实施并如实披露。本轮不因未实施而扣分，继续作为后续可选设计。

---

## 11. 范围与未验证面

**本次声称的验证层级**：`CONTRACT_PASS` 级别的字节/模式/哈希实算、调用边界对抗、无前置重放独立复现、G1、B0 写入边界。

**明确不声称**：`END_TO_END_PREFLIGHT_PASS`、`FORMAL_RUN_PASS`、科学 PASS、正式实验资格、promotion/deployment。

**未验证**：GB10 生产服务、数据库、模型端点、daemon、Loop B；执行对话 token（UNRESOLVED）；未来 Loop D 对真实 run 包的调用与真实证据交接、封闭案例集；真实部署中异源 pin 的来源归属（夹具只证明文件级分离）；`logs/` 与 `.pytest_cache/` 变更的确切写者与时点；T5R-02 dissent-2 的更强构造。

**评审者副作用**：仅在仓库外 `/home/testuser/wzh/loop_runs/t5r03_recheck_a/` 建立 scratch 与 work-root；未在被审 run 或仓库内写入任何文件（已用全量 sha/mtime 扫描自证交付树零写入）；未调用模型端点、生产、数据库、Loop B；未做 git 写；未进入 T6。
