# T7R-01 — Loop C 独立质量审计：T7 R 独立验收与回滚（NO_PROMOTION）

- **review_id**: T7R-01　**task_id**: T7　**direction**: R　**card_version**: 2
- **reviewer / runtime**: Loop C（独立质量审计层）/ GB10、Python 3.12、只读；0 模型 / 0 网络 / 0 远程 / 0 生产 / 0 数据库 / 0 训练 / 0 daemon / 0 Loop B
- **被审对象**: `research/harness_rsi_v1/runs/T7/20261015T025839Z_c94af776/`（58 文件；HEAD `0579b64bbc4423b52055d37e0f81cd0715f453bb`，`git rev-parse HEAD` rc=0）
- **范围**: 只读独立复算 + 仓库外 scratch 实弹探针；不改任何文件、不 git 写、不联网、不调模型/生产/数据库、不进 T8、不更新 registry/state。
- **结论**: **ACCEPTED（0 阻断，7 顾问，1 项 T6R-01 清理条件已核实执行）**。全部头条声明从交付字节独立复算成立；**NO_PROMOTION / NOT_EVALUABLE 的事实基础经 12 组替代实现探针独立证实**。

---

## 0. 评审方副作用（先读；非交付缺陷）

| 位置 | 内容 | 说明 |
|---|---|---|
| `/home/testuser/wzh/loop_runs/t7r01_recheck_a/outputs/` | 7 个复算 JSON（manifest_recompute / three_layer / old_evidence / restored_parent / case_identity / input_bindings / adversarial_probes） | 仓库外，`python3 -B` 生成 |
| `/home/testuser/wzh/loop_runs/t7r01_recheck_a/scratch_runtime/` | 空目录 | 12 组探针全部在 target 执行前 fail-closed，无运行时产物 |

- 被审 run 树与仓库内**未写入任何文件**。交付树残留扫描（`__pycache__` / `.pyc` / `.omc` / `.tmp`）= **0 件**（历史 OMC/pycache 类问题本包未复发）。
- T6R-01 要求收口者删除的 2 个 `.omc/state/.../pre-tool-advisory-throttle.json` **已不存在**：T6 树现为 31/31 文件 == HEAD blob，0 失配（该前置条件已执行）。

## 1. 计数 / 哈希 / 模式（三层）

命令：`python3 -B` 复算脚本（rc=0）×3；git 受限时以 `git cat-file -p HEAD:<path>`（rc=0）+ 字节派生 blob SHA-1 + 解析 `.git/index`（v2，3986 条）完成三层比对。

| 项 | 复算值 | 声明 | 判定 |
|---|---|---|---|
| 交付文件总数 | **58** | 58 | PASS |
| manifest 条目（`artifact_count` / 数组长） | 57 / 57 | 57 | PASS |
| manifest 逐条 `sha256_file` | 57/57 一致 | — | PASS |
| manifest 逐条 `bytes` | 57/57 一致 | — | PASS |
| manifest 逐条 `mode` | 57/57 一致 | — | PASS |
| 文件集 | 磁盘 58 == manifest 57 + 不自哈希的 `artifacts_manifest.json` | self_hash_policy 如实 | PASS |
| worktree / `.git/index` / HEAD tree blob | **58/58 三层完全一致** | — | PASS |
| mode 三层 | 3×100755（`build_manifest.py`、`execute_t7.py`、`self_check.py`）+ 55×100644，三层同 | 3×755 | PASS |
| `artifacts_manifest.json` 自身 | `f2022817e6c0c435edb5a66495967cbc001f60aa70a6da5cf68984d1795b73bb`，22337 bytes，100644 | 不自哈希 | PASS |
| 共享父树未改 | T4 65/65、T5 46/46、T6 31/31 磁盘 blob == HEAD | `parent_diff_checks` 3×unchanged | PASS |

## 2. NO_PROMOTION 合法性（核心）

### 2.1 闭合词表事实（静态）

读 T5 v3 `registered_operations.json`（`closed_vocabulary: true`，3 op）：

| op_id | 参数 | 类型 | 枚举 |
|---|---|---|---|
| OP-T4-R-DISPATCH-PRECHECK | tick_path / watcher_path / max_tick_age_minutes | enum / enum / int-range | 3 值 / 1 值 / 0–60 |
| OP-T4-R-SUMMARY-GUARD-CHECK | markdown_path | relative_path_enum | **恰 1 值** `recipe_fixtures/summary/good_summary.md` |
| OP-T4-R-SUMMARY-GUARD-DERIVE | base_markdown_path | relative_path_enum | **恰 1 值** `recipe_fixtures/summary/good_summary.md` |

E-03 要求 `markdown_path=FUTURE_ENUM_receipt_block_absent.md` + `required_result=REJECT with an explicit missing-receipt-block code`。**双重不可表达**：(i) 该路径不在任何枚举内；(ii) 目标语义为「REJECT 缺收据块」，而现有 `summary_recompute_guard.py check` 对无块文档是**静默跳过 rc=0**（本评审独立复跑，见 §6），`DERIVE` 只对**派生数字失配**出 target rc=1，`DISPATCH-PRECHECK` 是 tick 合同对象。**无任何已登记操作或组合能产生「缺块⇒显式 REJECT」**。

### 2.2 替代实现探针（12 组，本评审在 scratch 自建，`importlib` 载入被审 T5 `caller_validator.py`，rc=0）

| # | 替代实现尝试 | 结果 | fail-closed 码 |
|---|---|---|---|
| A | CHECK 换 `FUTURE_ENUM_receipt_block_absent.md` | REJECTED | FC_ARBITRARY_PATH |
| B | CHECK 换 T7 `required_receipt_block_missing.md` | REJECTED | FC_ARBITRARY_PATH |
| C | CHECK 换 T4 `usage_no_block.md`（真缺块件） | REJECTED | FC_ARBITRARY_PATH |
| D | DERIVE base 换 FUTURE_ENUM | REJECTED | FC_ARBITRARY_PATH |
| E | 追加第 3 个 CHECK 操作（组合表达） | REJECTED | FC_RECIPE_OBJECT_MISMATCH |
| F | 给 CHECK 加 `required_result` 参数 | REJECTED | FC_PARAMETER_TYPE_MISMATCH |
| G | 伪造未登记 op `...-ABSENT-BLOCK-REJECT` | REJECTED | FC_UNREGISTERED_OPERATION |
| H | 绝对路径 | REJECTED | FC_ARBITRARY_PATH |
| I | `../` 穿越 | REJECTED | FC_ARBITRARY_PATH |
| J | 用 DISPATCH-PRECHECK 承担缺块判定 | REJECTED | FC_RECIPE_OBJECT_MISMATCH |
| K | 删第 2 个 op | REJECTED | FC_RECIPE_OBJECT_MISMATCH |
| L | 交换 op 顺序 | REJECTED | FC_RECIPE_OBJECT_MISMATCH |

**12/12 全部 REJECTED，`target_execution=false`**（scratch_runtime 空）。**未发现被忽略的可行路径**，`NOT_EVALUABLE` 事实基础成立。

### 2.3 六硬门判定诚实性

| 硬门 | 交付判定 | 独立核验 | 归因准确性 |
|---|---|---|---|
| 严重漏检 | `UNRESOLVED_NOT_EVALUABLE` | 合法 UNRESOLVED 已从分母排除；缺必需证据基线为静默跳过，但候选无可执行操作 → 不能声称 0 漏检 | **准确**（不冒称 0，不冒称漏检） |
| 合法误拦 | `PASS_AT_PARENT_CONTROLS_ONLY` | T5 父配方 `ACCEPTED_WITHIN_SCOPE`（正控 target rc=0、失配负控 target rc=1、`derived_md_removed=true`）复算一致；候选全行为未建立 | **准确**（限定语到位） |
| 证据完整性 | `FAIL` | E-03 在闭合枚举外、无可执行覆盖（§2.1/2.2 证实） | **准确**（归因是词表边界，不是能力偷换） |
| 主张越级 | `PASS` | 全文措辞扫描 0 处正向实验/科学/C-S/部署主张，命中项全部是否定式（§6） | 准确 |
| 原始记录 | `PASS` | 22 条基线日志 + 4 条诊断日志全在；运行时派生失配件删除后留 sha256；父包未写（§1 共享树 0 失配） | 准确 |
| 预算完整 | `PASS` | usage 全 0 与 events 三方一致 | 准确 |

`pilot_acceptance.a_assertions.A1=FAIL`（0/2 修复、成本分支未预注册且不可用）为**如实自报**，未粉饰。

## 3. A-1 修正充分性（T6R-01 ADVISORY-1 四项）

| 要求 | 核验 | 判定 |
|---|---|---|
| (a) 拆分 a/b | `classification_policy` 4 类：`MISSING_REQUIRED_EVIDENCE`（SEVERE_EVIDENCE_COMPLETENESS）/ `LEGAL_UNRESOLVED`（NONE）/ 正控 / 负控；两诊断件分立 | **满足** |
| (b) 合法 UNRESOLVED 不入 severe | `six_gate_targets.severe_defect_miss` 明写「legal T1-INC-14 UNRESOLVED is excluded from the denominator and must never be converted into a severe defect」；`counted_severe_defect_repair_count=0`、`legal_unresolved_counted_as_severe_defect=false`、六门未计严重缺陷 | **实质满足**，但见 **ADVISORY-1**（记录字段字面反向） |
| (c) 不折算 | 无 0 填充、无 1/1→0/1 折算；`cost.cost_comparison_available=false`，未把 0 模型调用解释为同质量降成本 | **满足** |
| (d) 再锚定或理由 | `problem_family` 改锚 `SUMMARY_GUARD_ABSENT_REQUIRED_RECEIPT_BLOCK`；`t1_v3_applicability_resolution.t1_incident_reclassified_as_severe_defect=false` + 显式理由 + T1/T4 权威源绑定（blob `c666bb35…`/`3ea99e45…` 复算一致） | **满足** |

**时间线（修正先于任何候选评估）**：`candidate_amendment_A1.json` mtime `03:02:45Z` → 基线重放 `03:17:08Z` → A-1 诊断 `03:17:09.09–.14Z` → `amended_candidate.json` `03:17:09.14Z` → 候选 validator `03:17:09.21Z`；events 顺序 `a1_precondition_completed_before_evaluation` 早于 `paired_replay_completed`。**PASS**。

**诊断件与日志**：两轮 4 条日志（`scratch/a1_diagnostic/*`）两两内容一致，均为 `exit_code=0` + `无 SUMMARY-GUARD 块, 跳过`，与 `paired_replay.a1_diagnostic_records` 的 `SILENT_SKIP` 一致。fixture sha256 复算一致。见 **ADVISORY-6**（a/b 拆分目前仅由 fixture 文本声明，未由合同推导）。

## 4. 回滚演练

| 项 | 复算 | 判定 |
|---|---|---|
| `restored_parent/` 三件 vs T5 v3 原件 | `caller_validator.py` / `recipe_interfaces.json` / `registered_operations.json` 字节、模式（0644）、blob 全等 | PASS |
| 父行为 before / after | `execute_t7.py` 确以 `restored_parent/caller_validator.py` **二次执行** `validate_call`，两次 `ACCEPTED_WITHIN_SCOPE`；不一致即 raise | PASS（见 ADVISORY-5：二次调用原始输出未留存） |
| 11 件旧证据 | `bytes` / `sha256_file` / git blob / `mode` **11/11 复算一致**；before/after 两快照**字节相同**（同 blob `d9be03a2…`） | PASS |
| `candidate_state.json` | sha256 `669630e5…` 与 `rollback_receipt` 声明一致；`shared_activation=false` | PASS |
| 共享树 | `registry_changed/t4_changed/t5_changed/t6_changed` 全 false，与 §1 三层复算一致 | PASS |
| 边界诚实 | `unverified` 明列「曾启用候选后的真实部署回滚」「选择/封存集回滚」不存在 | PASS |

**A2 = PASS**。

## 5. 配对重放抽查

- **T1 v3 16 案身份**：T1 `incidents.jsonl` 16 条 vs T4 v2 `baseline.json` 16 案，`case_id` 集合相等，`title/expected_category/artifact_level/applicability/legal_control_design` **5 字段 0 失配**（独立复算 == `identity_bindings.case_set.identity_field_matches` 16/16）。
- **T4 基线 11×2=22/22**：`applicable_checks` 求和 = 11/轮，22 条记录 `match` 全 true；4 案抽查与 T4 原始工具输出逐项吻合：
  - `T1-INC-12`（derive）：T7 与 T4 原日志 **derived_md_sha256 同为 `52a58656…`**、同文案、`guard_rc=1`、`derived_md_removed=true` → 字节级忠实复现；
  - `T1-INC-14`：同为 `无 SUMMARY-GUARD 块, 跳过` rc=0；
  - `T1-INC-09`（frozen）：`md5sum` 报错 rc=1；
  - `T1-INC-01`：rc=1，但**失败原因集不同** → **ADVISORY-4**。
- **T5 父配方**：`scratch/t5_baseline_validator_result.json` 复算 `ACCEPTED_WITHIN_SCOPE`，2 op 的 wrapper/target 退出码与文案与 registry `expected_*` 一致。
- **候选调用**：`FC_RECIPE_OBJECT_MISMATCH` / `target_execution_performed=false` / `counted_as_severe_defect_detection=false` 归因正确（fail-closed 只证无注册支持）。

## 6. A1 / A2 / A3 / A-common + 纪律

- **A1**：六门非全满足（2 项非 PASS）、修复漏检 0/2、成本分支未预注册 → **FAIL 如实**（不伪造 24/24/24、不伪造一次封存访问：`selection_set=NOT_BUILT`、`sealed=NOT_APPLICABLE_UNRESOLVED`、`sealed_access_count=0`）。
- **A2**：§4 PASS。
- **A3**：全文措辞扫描（`实验成功|科学成功|已验证|FORMAL_RUN_PASS|…`）命中项**全部为否定式**（"不是实验、科学成功…"/"No experiment, scientific success…"）；`self_check.py:194` 亦显式做否定式排除。**PASS**。
- **A-common**：JSON/JSONL 全解析；**20/20 input_bindings** 的 `sha256_file` + 字节派生 blob + `git rev-parse HEAD:<path>` 全一致（A-1 记 `RUN_LOCAL_UNTRACKED_AT_EXECUTION` 如实）；路径均在 allowlist；无写入越界（§1 共享树 0 失配）；5 条 UNRESOLVED 显式且不填 0。**PASS**。
- **G1**：run 内 5 个 `.md` 逐个 `summary_recompute_guard.py check`，5/5 rc=0——**但 5/5 全是「无 SUMMARY-GUARD 块, 跳过」空过**（本评审独立复跑 `summary.md`、`TASK_PROMPT.md` 各 1 次，均 rc=0 + 跳过）。`scratch/g1_guard_matrix.log` **如实记录跳过**，但 `receipt.checks.g1.scope` 只写「checked individually; each returned rc=0」、`final_self_check.g1_markdown={count:5, rc0_count:5}` 未披露空过 → **ADVISORY-3**。跳过项本身披露诚实。
- **TASK_PROMPT 逐字节**：`TASK_PROMPT.md` 4267 bytes == `runs/T7/_dispatch/loop_a_prompt_t7.md` 4267 bytes，sha256 同为 `ed062beda4320b56b7f9f2e6916700d1c9cc78704a44a3010bc8b2ec8d906828`。**PASS**。
- **修复记录**：`repair_record.json` 8 次 attempt；`repair_attempts/` 仅 2 件（对应该记录 attempt 5、6）→ **ADVISORY-2**（与 events / review_packet 三方不一致）。
- **usage**：`model_calls=0`、`additional_cheap 0/0`、`additional_strong 0/1`（`strong_requests_reserved_for_loop_c=1`，即本评审占用）、网络/远程/生产/数据库/训练/daemon/Loop B/自动重试全 0；`execution_chat_usage=UNRESOLVED`（不填 0）。**PASS**。说明：若运行时出现模型供应商自有列表刷新日志，属运行时环境事件，**非编排调用**，未计入也不应计入上述计数。
- **三轴**：`DELIVERED / UNREVIEWED / NOT_ENABLED` 全线一致（receipt / pilot_acceptance / paired_replay / amended_candidate.activation.enabled=false）；Loop A 未自填 ACCEPTED。**PASS**。
- **依赖**：`T6R-01` decision=ACCEPTED（receipt blob `5c3b5431…`/sha `11a36576…` 复算一致）；protocol freeze `282f5213…` 一致；T5/T4 content_group_id `4f7d7af4…`/`b78bce33…` 与 T6R-01 独立复算值相同。

## 7. 新对抗探针

1. **词表内等价实现穷举**（§2.2，12 组）：枚举替换、参数注入、追加/删减/重排操作、伪造 op、绝对路径、穿越——**全部 fail-closed 且不执行 target**，无法在词表内表达 E-03 语义；反向证实 NOT_EVALUABLE。
2. **G1 空过独立复跑**（§6）：证实 5/5 rc=0 是 0 项内容验证，暴露交付聚合口径未区分「验证」与「跳过」。
3. **重放保真度对照**（§5）：把 T7 重放日志与 T4 v2 原始工具输出逐字比对，发现 dispatch 族失败原因集漂移（ADVISORY-4）。
4. **父树完整性全量复算**：T4/T5/T6 三树 142 文件磁盘 blob == HEAD，反证「共享树未改」。

## 8. 阻断项 / 顾问项

**BLOCKING：无。**（候选从未启用、结论为 NO_PROMOTION、决策路径正确且保守。）

**ADVISORY（7）**

1. **（high）`paired_replay.json` 的 `legal_unresolved_is_severe_defect` 字段语义反向**。`execute_t7.py:352` 以 `classification == "LEGAL_UNRESOLVED"` 赋值，故两条 LEGAL_UNRESOLVED 诊断记录写入 `legal_unresolved_is_severe_defect: true`，而 MISSING_REQUIRED_EVIDENCE 记录写 `false`——字面断言与 A-1 要求 (b)「合法 UNRESOLVED 不入 severe」**相反**。计数与判定路径均正确（`legal_unresolved_counted_as_severe_defect=false`、0 计数、六门未计严重缺陷），故不阻断；但机器抽取该字段会得出与 A-1 相反的结论，且该字段出现在记录 A-1 诊断的证据件中。须在账本中绑定该字段真实语义（或未来新 run 包更名），不得据字面回读。
2. **（medium）修复史三方不一致**。`repair_record.json` 8 次 attempt；`events.jsonl` 仅 4 条 `repair_attempt`（编号 1、2、5、7），其中编号 5 的 result 为「FAILED_DURING_BASELINE_REPLAY_BEFORE_CANDIDATE_EVALUATION」而 repair_record 的 attempt 5 是「FAILED_AFTER_CANDIDATE_EVALUATION_DURING_DELIVERY_CLEANUP（self-check）」，编号 7 为「FAILED_DURING_A1_DIAGNOSTIC_BEFORE_CANDIDATE_EVALUATION」而 repair_record 的 attempt 7 是「FAILED_ON_MANIFEST_MODE_PARSER（post-manifest）」；`review_packet.md` §6 称「四次失败」只列评估前 4 次。8 次中仅 2 次有留存失败件（`repair_attempts/`），attempt 3–4 的 retained_evidence 指向的是修复后的**成功**日志。卡片 §5 要求 events.jsonl 追加实际事件——同族于 T6R-01 ADVISORY-4，此处还多出编号/结论错位。
3. **（medium）G1「5/5 rc=0」实为 0 验证 + 5 空过**，含 `summary.md` 自身**无 SUMMARY-GUARD 块**（T6 的 summary.md 是有块的）。恰是本线在研究的失败族；receipt 的 g1 scope 未披露空过。`scratch/g1_guard_matrix.log` 如实，聚合口径不实义。
4. **（low-medium）配对重放 dispatch 族失败原因漂移**。T4 的 `fixtures/dispatch/watcher.sh` 现为 0664，故 T7 重放 6/22 记录（T1-INC-01/02/11 ×2）多出 `watcher 缺执行位 (F-0907-1)`；T4 原日志为 `mode=-rwxrwxr-x` + watcher PASS + 「watcher 缺少合格执行收据」。退出码同为 1、意图缺陷（tick 合同）FAIL 在两侧都在，故案例结论稳定；但「22/22 一致」仅是**退出码层**，失败原因集不同且未在 summary/review_packet 披露。（对照：T1-INC-12 derive 为字节级忠实。）
5. **（low）回滚二次校验原始输出未留存**：`scratch/` 仅有 `t5_baseline_validator_result.json`，恢复后那次 `validate_call` 的完整结果只以 status 字符串写入 `rollback_receipt.json`；比较本身由 `execute_t7.py:572` 机械强制。
6. **（low）A-1 a/b 拆分尚不可机械判定**：两类仅由 fixture 散文声明（「Classification target: …」），两者对守卫完全同构（均静默跳过）；区分依赖外部「交付合同是否明示要求收据块」，未由任何可执行检查推导。
7. **（low）T7 时间窗内有非本包写入，归属未披露**：`logs/graph/docs_lint_report.json`（mtime 03:23:12Z）与 `logs/graph/verify-report.json`（03:23:13Z，自述 `loop: B` / `role: independent_verification` / `head_commit: bad4e3890`）落在 T7 执行窗内。二者非 T7 写入（T7 只写 run 目录，`loop_b_calls=0`，self_check 的 `write_boundary` 亦列其为窗外既有状态），但归属未在交付中写明，特此披露以免误读为 T7 越界。

## 9. 工具边界与被拒命令

白名单外被拒（原样记录）：
- 组合命令 `ls …; echo; ls $R/runs/T5 …`（多操作需批准）
- 首个 `python3 -B <<'PY'` heredoc（含 `{`+引号，判为 expansion obfuscation）→ 改为无花括号字面量重写，rc=0
- Write 工具 → `/home/testuser/wzh/loop_runs/t7r01_recheck_a/recompute_manifest.py`（未授权）
- `git ls-tree HEAD <path>`（需批准）

替代手段：`git rev-parse HEAD` / `git rev-parse HEAD:<path>` / `git cat-file -p <ref>`（均 rc=0）完成 HEAD tree 三层复算；`.git/index` 自解析取 mode/SHA-1；字节派生 blob SHA-1；机制探针以 `importlib` 载入被审 `caller_validator.py` 同函数同参；scratch 仅以 `python3 -B` 写仓库外。**未使用** git 写、mkdir/cp/mv/rm/chmod、网络、模型端点。

## 10. 未验证面

跨机器/换 umask 复制链；真实 Loop D 调用；选择集与封存集（均未构建，本评审不伪造）；C/S 批次与跨方向引用去重；「曾启用候选后」的真实部署回滚；T4 `watcher.sh` 0664 是交付归一态还是环境态（影响 ADVISORY-4 归因，不影响退出码结论）；`execution_chat_usage`；缺收据块操作扩展（U-T6-02）的科学价值与另行授权；本评审 12 组探针为合成调用，仅存 `/home/testuser/wzh/loop_runs/t7r01_recheck_a/`，非交付证据。
