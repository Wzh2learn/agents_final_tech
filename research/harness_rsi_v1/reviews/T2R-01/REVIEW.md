# T2R-01 独立评审 — T2 harness_rsi_v1 评价底座

**评审者**：Loop C 独立质量审计层（GB10）· BR 强评审名额：**本卡 1 次，已使用**
**被审产物**：`research/harness_rsi_v1/runs/T2/20261014T145327Z_9a02a34a/`（52 件）
**评审性质**：只读独立复算 + 实跑评价器 + 反证尝试。registry/state 未写，未进入 T3。

---

## 1. 范围

在卡片 `T2.md` 的 A1/A2/A3/A-common 与 `evaluation/reliability_spec.md`、`evaluation/human_review_protocol.md`、`contracts/{protocol,authority_map,execution_policy,budget_profiles,schemas}` 约束下，独立复算 T2 run 的全部可核声明，并实跑评价器以检验辨别力、fail-closed 与退化门。排除：C/S 方向、封存集访问、正式实验、部署、生产/数据库/模型探针、任何 git 写。

---

## 2. 逐项结果

### 2.1 工件清单与哈希

| 项 | 结果 | 证据 |
|---|---|---|
| run 目录恰 52 件 | **PASS** | 首次递归枚举返回 52（`.run_id`、`TASK_PROMPT.md`、`artifacts_manifest.json`、`evaluator_spec.json`、`events.jsonl`、`qualification.json`、`receipt.json`、`sealed_access_proposal.json`、`summary.md` + `qualification_cases/t1/`×16 + `evaluator/`×3 + `fixtures/`×18 + `fixtures/artifacts/`×6） |
| manifest 51 条逐条 SHA-256/字节实算 | **PASS 51/51** | 自写 Python 逐条重算；0 处哈希失配、0 处字节失配；`self_hash_excluded=true`，`artifacts_manifest.json` 自不含；无缺项、无多项 |

**评审侧污染披露（非 Loop A 责任）**：本次评审曾 `cd` 进入 run 目录，OMC 工具钩子随后在该目录下生成 `.omc/state/sessions/ec852aef-…/{pre-tool-advisory-throttle,last-tool-error-state}.json`（mtime 23:37/23:38，晚于 run 交付物 23:30 及本次首次 52 件枚举）。此 2 件系本评审会话工具副作用，**不属于 T2 交付物，未进入 manifest，也未改动任何既有文件**。收口者如需清理应单独授权。

### 2.2 receipt 绑定与冻结

| 项 | 结果 | 证据 |
|---|---|---|
| `input_bindings` 10 条逐条实算 | **PASS 10/10** | 9 条 `git_blob_id` 经**两条独立路径**复算一致：(a) 由文件字节自算 git blob SHA-1（`sha1("blob <len>\0"+bytes)`）；(b) 解析 `.git/index`（3423 条目）取登记 blob SHA。二者与声明值全部 MATCH，无缺失。1 条 `sha256_file`（TASK_PROMPT.md = `6d591b2a…`）亦一致 |
| 卡片 7 输入 + T1 v3 receipt + T1I-03 + TASK_PROMPT | **PASS** | 覆盖齐备；角色标注正确（`card_input`×7 / `t1_accepted_run_dependency` / `t1_independent_review_dependency` / `dispatch_traceability`） |
| `protocol_freeze_check` | **PASS** | `contracts/protocol.json:107` `freeze_sha256` = `282f52133a682e927c82b771fa103c27da34db7acbd8a12d2921f42a6d0bf36b` = `dispatch_expected`；`match: true` 属实 |
| 三轴三值 | **PASS** | `DELIVERED / UNREVIEWED / NOT_ENABLED`，与 `evaluator_spec.status=UNREVIEWED`、`qualification.status=PASSED_LOCAL_UNREVIEWED` 自洽 |
| 无伪造 ACCEPTED / freeze | **PASS** | 全 run 文本扫描：仅出现「T1I-03 已 ACCEPTED」这一**依赖事实**（TASK_PROMPT、receipt 的 `verified_proposal` 字段）；`summary.md` 明确把「Loop C 独立 ACCEPTED」列入 UNRESOLVED；`evaluator_spec` 自带反越权声明 `no formal experiment authority and no scientific PASS`。无自授 ACCEPTED、无 PROMOTED、无 SEALED_QUALIF、无 SCIENTIFIC_PASS |
| usage 零编排调用 | **PASS（executor 层）** | `events.jsonl` USAGE_RECORDED 与 receipt.usage 一致（cheap 0 / strong 0 / orchestrated 0 / network 0 / model 0 / production 0 / db 0）；评价器全链路为本地确定性 Python + 本地只读 git 子进程。**反证扫描未发现 executor 发起端点调用**。但见 ADVISORY-A5（同窗口并存后台守护进程） |

### 2.3 T1 依赖与嵌套证据

| 项 | 结果 | 证据 |
|---|---|---|
| T1 adapter 映射忠实性（Loop C 指定必审） | **PASS 16/16** | 逐条比对 `incidents.jsonl` 16 条源记录 vs 16 个 case bundle：`incident_id`、`expected_category`、`failure_family`、`artifact_level`、`case_kind.control_class` 全部一致；断言语义与源记录 `title`/`observed_fact` 相符（如 INC-06「(scores, input_ids) vs 实际 (input_ids, scores)」→ `CALL_ARGUMENT_ORDER_ERROR`；INC-09「manifest 未回钉」→ `MANIFEST_NOT_REPINNED`；INC-14「token 不可计量」→ `USAGE_METERING_UNRESOLVED`）。CTRL-01/02 映射到同族 legal 断言亦正确 |
| 嵌套证据哈希漂移披露准确性 | **PASS** | 独立重算 T1 全部 **33** 条 `source_refs` 的 canonical blob id：恰 **2** 条漂移，即 `T1-INC-08 → reviews/T1R-01/LOOP_C_RAW_STDOUT.log`（`62d8f5fd…`→`06d0b90f…`）与 `T1-INC-10 → reviews/T1R-02/REVIEW.md`（`cadcc0e7…`→`05e59c70…`）。与 `receipt.unresolved[0]`、`events.jsonl:5` 的「count:2，INC-08 与 INC-10 各一处」**完全吻合**；且 T2 bundle 确未复述这两条漂移引用，改绑未变的 T1 receipt/review 工件——披露属实、处置合理 |

### 2.4 A1 / A2 / A3 / A-common

| 断言 | 结果 | 证据 |
|---|---|---|
| **A1** 三退化策略均不可满足推广规则 | **PASS**（独立重算） | 见 §3.3。按冻结预期分布 15 缺陷 / 8 合法 / 11 待审（=34）独立代入双条件硬门：ALL_BLOCK 检出 15/15 但误拦 8/8 → 败；ALL_ALLOW 放行 8/8 但漏检 15/15 → 败；ALL_REVIEW_REQUIRED 拦 0/15 且误送审 8/8 → 败。三者均**不能同时**满足「缺陷检出 ∧ 合法对照不误拦」，与 `reliability_spec §6.4`「把所有案例送审也不是成功」一致 |
| **A2** 缺字段/错绑定/空集明确失败；层级不混用 | **PASS** | 三者各有显式专属夹具：`call_boundary_failclosed`→`FC_MISSING_REQUIRED_FIELD`、`evidence_identity_failclosed`→`FC_HASH_BINDING_MISMATCH`、`completeness_budget_failclosed`→`FC_EMPTY_EVIDENCE_SET`，均 exit 3。层级：`DIRECTIONS={"R"}` 硬编码，`direction:"C"` → `FC_INVALID_ENUM_VALUE` exit 3，输出恒为 `direction:"R"`，无任何跨轴聚合字段 |
| **A3** 候选不可写判分代码与标签 | **PASS** | `verify_hash()` 对候选工件**只做哈希**（`sha256_file` / `git_blob_id`），从不解析内容；`content_read_policy` 声明 `hash_only_no_candidate_scoring_code_or_labels_read` 并在每条结果回写。`candidate_writable_paths` 必须**恰等于**候选工件路径（多/少/异均 `FC_CANDIDATE_OWNERSHIP_VIOLATION`）。关键反证：`measurement_object_failcoded` 用候选自写标签 **`SELF_AUTHORED_PASS_LABEL`** → 被拒 `FC_UNKNOWN_ASSERTION_SIGNATURE` exit 3；证据 `provenance="candidate_self_attested"` → 被拒 `FC_CANDIDATE_OWNERSHIP_VIOLATION`。标签确不可由候选写入判分 |
| **A3** 封存隔离 + 权限测试证据 | **PASS（以「不主张」方式满足）** | `sealed_access_proposal.json`：`status=PROPOSAL_ONLY_NOT_IMPLEMENTED`、`qualification_claim=NO_SEALED_ACCESS_QUALIFICATION_CLAIM`；PT-01…PT-06 六项权限测试均有需求+证据要求；`unresolved` 明列「无身份隔离/ACL 实现」「无封存集」「PT-01…06 未执行」。**未主张封存资格通过**——符合卡片「未实现实际隔离则不声称封存资格通过」 |
| **A-common** JSON 解析/必需字段/allowlist/哈希/写入边界/未知项 | **PASS** | 39 个 JSON 全可解析；必需字段缺失走 `FC_MISSING_REQUIRED_FIELD`；路径越界/绝对路径/`..` 均 `FC_PATH_OUTSIDE_ALLOWLIST`；声明哈希全实算一致（§2.1/2.2）；executor 写入限于 run 目录（§2.5）；未知项在 `self_check.unknowns_explicit` + `evaluator_spec.unverified` + `sealed_access_proposal.unresolved` 三处显式列出 |

### 2.5 写入边界与反证

- **写入边界**：按 mtime 扫描 run 窗口（22:50–23:35）全仓 63 件变更，**52 件在 run 目录内 = 交付物全集**；目录外 11 件，经归属判定**均非 executor 所写**：
  - `runs/T2/_dispatch/loop_a_prompt_t2.md` @22:52:25 = run_id 时刻 22:53:27 前 **62 秒**，与 receipt 声明「existed 62 seconds before this run」**精确吻合**，且未被修改；
  - 其余 10 件（`logs/graph/{loop_b.log,pytest_loopb.txt,canary_latest.txt,eval/m2_canary_report.json,b4_ask_log.jsonl,docs_lint_report.json,verify-report.json}`、`logs/{app.log,m1_service.log}`、`.pytest_cache/…`）属**长驻 Loop B 校验守护进程**（`loop_b.log` 8.4MB/117k 行，可溯至 2026-07-29，尾行 `Sleeping 1800s until next check…`）与本地 M1 服务，见 ADVISORY-A5。
- **`issues_found_and_fixed` 如实性**：**PASS**。三项与 `events.jsonl` 逐条对应且算术自洽——SMOKE_1 `26/34` → 修复「PASS 未覆盖 NOT_EVALUATED」→ 34/34（34−26=8 = 恰好 8 个合法对照，与「synthetic legal controls 误送审」的描述吻合）；`fail_closed_codes` 曾用对象花括号 → 改数组；`/tmp/t2_final_qualification.json` 短暂生成后即删（`OUT_OF_RUN_TEMP_REVERTED`）。无夸大、无遗漏。
- **隐藏偏向（全 BLOCK / 全 ALLOW / 全送审）**：**无**。实际决策分布 ALLOW 8 / BLOCK 15 / REVIEW 11，三类齐备非退化；且独立反证确认 `expected_category` **不参与判定**——把 inc-01 的 `expected_category` 改为 `ALLOW_WITHIN_SCOPE` 后决策仍为 `BLOCK`（`decision_from_statuses` 只读三维状态）。
- **exit-code 契约一致性**：与 README、`evaluator_spec.exit_codes` 一致（0 正常 / 2 用法错 / 3 fail-closed），实测吻合——**但存在一处例外，见 ADVISORY-A1**。
- **越界/联网/模型痕迹**：executor 侧无。全 run 无外部 URL、无 socket、无客户端库导入；`evaluate.py` 仅 `subprocess` 调本地 `git ls-files`/`git rev-parse`（只读）。

---

## 3. 三项实跑证据

### 3.1 实跑资格评价器（两轮）

```
python3 research/harness_rsi_v1/runs/T2/20261014T145327Z_9a02a34a/evaluator/run_qualification.py --pass-id LOOPC_RECHECK_1
  → RUNNER_EXIT 0，STDERR 空，matched 34/34，failures 0
python3 ... --pass-id LOOPC_RECHECK_2
  → RUNNER_EXIT 0，matched 34/34，failures 0
```

18 合成夹具（每族各 BLOCK / ALLOW / fail-closed，**六族全覆盖**）+ 16 T1 v3 bundle。exit code 每轮 28×0 + 6×3。六个 fail-closed 夹具分别命中 6 个不同 FC 码（每族一个）。`qualification.json` 内部 68 条 `passes` 记录（34×2）`expected==actual` 且 `matched=True` 全真；重算的 `family_coverage`（完整 8 / 调用 7 / 交付 5 / 证据 5 / 测量 5 / 数据 4）与 `expected_distribution`（8/15/11）与声明**逐字相等**。

### 3.2 评价器决策与退出码抽查

```
call_boundary_block.json          EXIT=0  decision=BLOCK               dims={execution_integrity:FAIL,…}
call_boundary_allow.json          EXIT=0  decision=ALLOW_WITHIN_SCOPE  dims={PASS,PASS,PASS}
call_boundary_failclosed.json     EXIT=3  decision=REVIEW_REQUIRED     fc=FC_MISSING_REQUIRED_FIELD
delivery_permissions_failclosed   EXIT=3  decision=REVIEW_REQUIRED     fc=FC_CANDIDATE_OWNERSHIP_VIOLATION
t1/ctrl-01.json                   EXIT=0  decision=ALLOW_WITHIN_SCOPE  ev=2
t1/inc-07.json                    EXIT=0  decision=REVIEW_REQUIRED     ev=2
t1/inc-10.json                    EXIT=0  decision=REVIEW_REQUIRED     ev=2
```

BLOCK / ALLOW / REVIEW 三值与 exit 0 / fail-closed exit 3 均符合 README 与 `evaluator_spec.exit_codes` 声明。

### 3.3 退化策略独立重算 + 对抗探针（30 次）

**退化门独立重算**（不采信 `qualification.json` 自述，按 `promotion_rule.requires_simultaneously` 从冻结预期分布重新代入）：

| 策略 | 缺陷检出 | 合法对照 | 同时满足？ | 判定 |
|---|---|---|---|---|
| ALL_BLOCK | 15/15 ✓ | 误拦 8/8 ✗ | 否 | 硬门失败 |
| ALL_ALLOW | 漏检 15/15 ✗ | 放行 8/8 ✓ | 否 | 硬门失败 |
| ALL_REVIEW_REQUIRED | 拦 0/15 ✗ | 误送审 8/8 ✗ | 否 | 硬门失败 |

**结论：三个退化策略确实均不满足推广规则**（FACT，重算成立）。

**对抗探针**（经 `--case /dev/stdin` 喂入变异 bundle，全程无文件写入）：

```
A_baseline_inc01                        EXIT=0 BLOCK            （对照）
B_expected_flipped→ALLOW  决策仍 BLOCK  EXIT=0 BLOCK            （证明答案不泄漏进判定）
C 缺证据字段              EXIT=3 FC_MISSING_REQUIRED_FIELD
D 空证据集                EXIT=3 FC_EMPTY_EVIDENCE_SET
E direction="C"           EXIT=3 FC_INVALID_ENUM_VALUE
F hash_domain="crc32"     EXIT=3 FC_UNSUPPORTED_HASH_DOMAIN
G 断言跨族                EXIT=3 FC_SIGNATURE_FAMILY_MISMATCH
H writable_paths 扩写     EXIT=3 FC_CANDIDATE_OWNERSHIP_VIOLATION
I 哈希错绑                EXIT=3 FC_HASH_BINDING_MISMATCH
J 非法 expected 枚举      EXIT=3 FC_INVALID_ENUM_VALUE
K 伪造 source.origin      EXIT=3 FC_INVALID_ENUM_VALUE
L provenance=候选自证     EXIT=3 FC_CANDIDATE_OWNERSHIP_VIOLATION
M 绝对路径 /etc/passwd    EXIT=3 FC_PATH_OUTSIDE_ALLOWLIST
N 非法 JSON 文本          EXIT=3 FC_INPUT_NOT_JSON_OBJECT
S–AC  12 类型混淆         EXIT=3 均正确 fail-closed
O/P/Q/R/Q2 非对象 JSON    EXIT=1 崩溃  ← 见 ADVISORY-A1
```

fail-closed 网络总体健壮（30 探针中 29 行为正确）；唯一破口见下。

---

## 4. 发现

### BLOCKING（必须修复后重审）

**无。** 三项验收断言 A1/A2/A3 与 A-common 经独立复算全部成立；无伪造、无越界、无隐藏偏向、无答案泄漏。

### ADVISORY（不影响验收，可收口层登记）

**A1（最高优先级）非对象 JSON 输入崩溃而非 fail-closed — 声明契约与实现不符**

- **证据**：`--case /dev/stdin` 喂入合法 JSON 但顶层非对象（`[1,2,3]`、`"hello"`、`42`、`true`、`null`）时，`evaluate.py` 抛未捕获 `AttributeError: 'list'/'str'/'int'/'bool'/'NoneType' object has no attribute 'get'`，**exit 1，不写出任何结果记录**。而 `evaluator_spec.json` 的 `fail_closed_codes` 明列 `FC_INPUT_NOT_JSON_OBJECT`，`decision_rule.fail_closed` 声明「Invalid… input returns REVIEW_REQUIRED… and exit code 3」，README 亦同。
- **根因**：`evaluate_bundle()` 的 `except FailClosed` 处理器**自己崩溃**。第 386 行 `bundle.get("bundle_id", …)` 有 `isinstance(bundle, dict)` 守卫，但**第 397 行** `"expected_category_for_qualification_only": bundle.get("expected_category", "UNRESOLVED")` **没有守卫**。判定逻辑本身正确（第 321–322 行已正确抛出 `FC_INPUT_NOT_JSON_OBJECT`），是报错回写路径缺一处防御。
- **为何不升为 BLOCKING**：失败模式**响亮**（exit 1 + traceback，无静默通过、无错误判决）；`run_qualification.py` 会将其判为 `INVALID_OUTPUT` 且计为 mismatch → 该轮 runner exit 1，**不可能被用来刷分或放行缺陷**；34/34 资格集全部为对象，不受影响；三项验收断言无一被违反。
- **升级条件（请收口者裁决）**：若 owner 将「每一个声明的 `fail_closed_code` 必须对其声明输入类可达且返回 exit 3」视为 A2 的硬门，则本项**升为 BLOCKING**，仅需复审这一行修复。
- **建议**：在第 397 行同处加 `isinstance(bundle, dict)` 守卫（或在 `evaluate_bundle` 入口先归一化），并补一条 `FC_INPUT_NOT_JSON_OBJECT` 夹具（非对象 JSON）以钉住回归。

**A2 退化门表为手工声明，非执行门计算**
`degenerate_strategies[].hard_gate_pass` 与 `promotion_rule` 在 `qualification.json` 中为静态文本；全 run 无任何 `.py` 计算它们（grep 仅命中 `receipt.json`/`qualification.json`）。算术经本评审独立重算**正确**，但读者可能误读为已执行门。建议加一个 ~20 行脚本从 `case_results` 推导该表，使 3.3 的重算可复现。

**A3 冻结断言词表 29 条中 7 条未被资格集覆盖**
未覆盖者全为 defect 类：`AUDIT_SOURCE_MISSING`、`DENOMINATOR_DRIFT`、`PARTIAL_PASS_ELEVATED`、`RAW_NORMALIZED_MIXED`、`SILENT_EXCLUSION`、`STALE_RECEIPT_CURRENT_CODE`、`STOP_IGNORED`。代码路径经审阅正确，但无夹具钉住。建议补入后续选择集。

**A4 `promotion_rule` 为 `reliability_spec §6.3` 的简化形**
仅含「缺陷检出 ∧ 合法不误拦」两条硬门，未含 §6.3 的「选择集上至少修复两个原先漏检案例、无新增回归」「只让一个候选访问封存集一次」「同等质量下成本更低」。对 A1 用途足够，但**不得被下游当作完整推广规则**。建议加一行限定语。

**A5 同窗口后台活动未披露（审计可见性）**
run 窗口内（23:17–23:20）存在**非 executor** 的模型/端点活动：Loop B 守护进程（1800s 周期）执行 pytest 并发起 M2 canary 至 `http://127.0.0.1:5050/api/m2/ask`（`m2_canary_report.json` timestamp `2026-10-14 23:20:05`），M1 服务同期写日志。归属判定明确（`loop_b.log` 可溯至 2026-07-29、含自身睡眠周期；`events.jsonl` 全程无调用），故 **executor 的零调用声明成立**；但「zero orchestrated calls」不应被读作「run 期间环境零模型调用」。建议在 receipt.usage 或 WRITE_BOUNDARY 增一句并存守护进程披露。

**A6 case bundle 自身无完整性保护**
`expected_category` 与 `assertions` 由 bundle 提供，评价器无法验真（无签名/MAC）；所有权为声明式。已缓解：allowlist + provenance 白名单 + 已证 `expected_category` 不参与判定。封存化前建议引入 bundle 签名或由 custodian 独立持有。

**A7 4/10 fail_closed 码缺专属夹具**
`FC_INVALID_ENUM_VALUE`、`FC_UNSUPPORTED_HASH_DOMAIN`、`FC_SIGNATURE_FAMILY_MISMATCH`、`FC_INPUT_NOT_JSON_OBJECT` 未被 18 夹具钉住。前三者经本次对抗探针证实确被执行；第四者即 A1。建议补夹具固化。

---

## 5. FACT / INFERENCE / UNVERIFIED

**FACT（本评审一手实测）**
- run 目录 52 件；manifest 51/51 SHA-256 与字节实算一致，自不含。
- 10 条 `input_bindings` 双路径复算全 MATCH；协议 freeze 值三方一致。
- 两轮独立实跑 `run_qualification.py` 均 34/34、exit 0、无 stderr。
- 三决策值与 exit 0/3 契约实测成立（A1 例外除外）。
- 三个退化策略经独立代入**均不满足**双条件推广规则。
- T1 adapter 16/16 映射忠实；33 条嵌套 `source_refs` 中恰 2 条漂移，与披露一致。
- `issues_found_and_fixed` 三项与 events.jsonl 自洽（26/34→34/34 与 8 合法对照算术吻合）。
- 非对象 JSON 输入崩溃 exit 1（5 类型），根因为 `evaluate.py:397` 缺守卫。
- `SELF_AUTHORED_PASS_LABEL` 被拒；`expected_category` 翻转不改变决策。

**INFERENCE（有据推断，非实测）**
- 23:17–23:20 的日志/canary 归属 Loop B 守护进程与 M1 服务，非 T2 executor（据 `loop_b.log` 长期周期、文件命名 `pytest_loopb`、`events.jsonl` 无调用记录）。归属链强但非 executor 亲笔声明。
- A1 的业务影响评为「响亮失败、不可用于刷分」，系基于 `run_qualification.py` 将其计为 mismatch 的代码路径推演，非实测一次完整 runner 失败轮。
- `.omc/state` 2 件为本评审工具副作用（据 mtime 晚于交付物且位于我 `cd` 之后）。

**UNVERIFIED（本次无法/不予验证）**
- **git CLI 全部被拒**（见 §6），故 `git rev-parse HEAD:<path>` 的**命令行**等价性未验；改用字节自算 blob SHA-1 + `.git/index` 解析双路径替代，结论一致。
- `git show --name-only 5756984` 与 `git status --porcelain` **被拒**，commit 级写入边界改由 mtime 扫描 + 归属推断替代；未验证 5756984 提交的文件清单。
- 封存隔离、PT-01…PT-06、C/S 方向、人工一致率、生产运行时、真实缺陷率——均未验证（与产物自述一致）。
- 执行对话 token 用量：UNRESOLVED。
- 合成夹具仅证明已知签名辨别力，不构成真实缺陷率估计（与 `evaluator_spec.unverified` 一致）。

---

## 6. 被拒命令如实记录

| 命令 | 结果 |
|---|---|
| `git -C <repo> log --oneline -8` | **拒绝**（requires approval） |
| `git -C <repo> show --name-only 5756984` | **拒绝**（requires approval） |
| `git -C <repo> status --porcelain --untracked-files=all` | **拒绝**（requires approval） |
| `git -C <repo> rev-parse HEAD` | **拒绝**（requires approval） |
| `git -C <repo> rev-parse HEAD:research/harness_rsi_v1/contracts/protocol.json` | **拒绝**（requires approval） |
| `… run_qualification.py > /tmp/loopc_q1.json` | **拒绝**（harness 禁止写 `/tmp`；改用 subprocess 捕获 stdout，无文件写入） |

未发起任何联网、模型端点、生产或数据库调用。`evaluate.py` 内部对本地 `git` 子进程的只读调用（`git ls-files --error-unmatch`、`git rev-parse HEAD:<path>`）随评价器执行发生，属本地只读哈希解析，非网络/服务/数据库。

---

## 7. 对 T2 的判定与理由

**判定：ACCEPTED**（工程资格层；不授予正式实验权限，不含科学 PASS，不含封存资格）

**理由**：
1. 三项验收断言**全部经独立复算成立**——三退化策略确不可满足推广规则（重算非采信）；缺字段/错绑定/空集显式失败且 R/C/S 不混用；候选不可写判分代码与标签（`SELF_AUTHORED_PASS_LABEL` 实证被拒），封存以「提案 + 明确未实现 + 无资格主张」正确处置。
2. **可核声明全部对得上**：51/51 清单哈希、10/10 绑定（双路径）、freeze 三方一致、两轮 34/34 复现、决策分布非退化、`expected_category` 不泄漏进判定。
3. **Loop C 指定必审的 T1 adapter 经逐条比对忠实**（16/16），嵌套哈希漂移披露**精确**（2 处，命名与计数全中）。
4. **无伪造**：无自授 ACCEPTED，`evaluator_spec` 自带反越权声明，`summary.md` 把 Loop C 验收正确列为 UNRESOLVED。
5. 唯一实质缺陷（A1）位于**未部署工件的边缘输入路径**，失败**响亮**（exit 1，runner 计为 mismatch），**不产生错误判决、不产生静默通过、不可用于刷分**，且不触及任一验收断言——故不构成「必须修复后重审」。
6. 先例一致：T1I-03 对同类工程工件以 ACCEPTED 结案并在 `dissent` 留档次优处置；本评审同构处理。

**保留意见（dissent）**：次优处置为 `PENDING_HUMAN_REVIEW`，理由是 A1 构成 `evaluator_spec` 声明的 `FC_INPUT_NOT_JSON_OBJECT` 未对「合法 JSON 非对象」类完整落地，在以 fail-closed 为核心价值主张的底座中属契约完整度缺口。本评审选择 ACCEPTED，因为该缺口响亮失败、不可被利用、且不触验收断言；但若 owner 采「声明的每个 fail_closed 码须对声明输入类可达」为硬门，则应立即改判 BLOCKING 并仅复审该一行修复。此裁量权归 owner / 收口者。

**下一步建议**：修复 A1（一行守卫 + 一条夹具）；A2–A7 登记收口层；本卡不自动进入 T3。
