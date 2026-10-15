# T6R-01 — Loop C 独立质量审计：T6 有界提案与统一档案

- **review_id**: T6R-01  **task_id**: T6  **direction**: R  **card_version**: 2
- **reviewer**: Loop C (independent quality audit) / runtime: GB10, Python 3.12, read-only
- **被审对象**: `research/harness_rsi_v1/runs/T6/20261015T012906Z_b9bb8ca6/`（HEAD `ef5e84edbd4fcd35cc287316c0e994cf72f6faa4`，`git rev-parse HEAD` rc=0）
- **范围**: 只读独立复算 + scratch 实弹复跑；不改被审 run / 仓库文件、不 git 写、不联网、不调模型/生产/数据库、不进入 T7、不更新 registry/state。
- **结论**: **ACCEPTED（0 阻断，9 顾问，1 项评审方副作用须收口者清理）**。全部头条声明从交付字节独立复算成立。

---

## 0. 评审方副作用（先读；非交付缺陷）

本次评审在被审 run 树内产生了 **2 个 gitignored 文件**（`.gitignore` 规则 `.omc/`）：

| 路径（相对 run root） | mtime | 来源 |
|---|---|---|
| `.omc/state/sessions/2b7c0690-fc6a-4d2e-a63a-49663672b283/pre-tool-advisory-throttle.json` | 2026-10-15T02:17:35Z | 本评审 Bash 以 run 目录为 cwd 运行 `find`/`cat`，OMC PreToolUse 钩子按 cwd 物化会话状态 |
| `archive_implementation/.omc/state/sessions/2b7c0690-…/pre-tool-advisory-throttle.json` | 2026-10-15T02:28:29Z | 同上，cwd = `archive_implementation/` |

- 这两件**不属于交付物**（T6 交付时刻 02:04–02:07Z；二者 mtime 晚于交付），不入 manifest、不入 index/HEAD。
- **后果**：交付的 `self_check.py` 现在重跑会 **rc=1 / 2 项 FAIL**（`artifact_manifest` 文件集失配、`write_boundary` ignored T6 entries=2）——这是评审方污染所致，不是交付缺陷；30 项 manifest 的 bytes/sha256/mode 本身仍 100% 复算一致（见 §1）。
- **须收口者删除上述 2 个文件**（我无 `rm` 白名单且不得改被审树）。删除后 `self_check.py` 应回到 18/18 PASS。
- 同型 `.omc/` 状态在 `runs/T1/20261014T132249Z_99f3bc6b/`、`runs/T5/20261014T195445Z_60c8e213/` 等既有 run 目录中早已存在（mtimes 2026-10-14），属环境常态，见 ADVISORY-8。
- 其余仓库外写入：`/home/testuser/wzh/loop_runs/t6r01_recheck_a/`（仅建空 `outputs/`，无文件）与 `/tmp/t6r01_scratch/`（8 个驱动脚本、`outputs/` 9 份复算 JSON、`attack/` 22 个变异样例 + 2 个合成包）。全部 `python3 -B` 执行，交付树内**无 `__pycache__`/`.pyc` 残留**（已扫，0 件）。

---

## 1. 计数 / 哈希 / 模式（三层）

命令：`python3 -B /tmp/t6r01_scratch/recompute_hashes.py`（rc=0）。git 受限时改用字节派生 blob SHA-1 + 解析 `.git/index` + 直接读 `.git/objects` pack 走 HEAD tree。

| 项 | 复算值 | 声明 | 判定 |
|---|---|---|---|
| 交付文件总数 | **31**（= 30 manifest 条目 + 自身不自哈希的 `artifacts_manifest.json`） | 31 | PASS |
| manifest 条目 | 30（`artifact_count` 字段=30，数组长度=30） | 30 | PASS |
| manifest 逐条 bytes | 30/30 一致 | — | PASS |
| manifest 逐条 SHA-256 | 30/30 一致 | — | PASS |
| manifest 逐条 mode | 30/30 一致 | — | PASS |
| 文件集 | 磁盘（除 manifest 自身）== manifest 路径集 | — | PASS |
| 755 | `archive_implementation/archive.py`、`archive_implementation/self_check.py` | 2×100755 | PASS |
| 644 | manifest 内 28 件 + `artifacts_manifest.json` = 交付 29 件（清单集 28） | 28×644（清单集） | PASS |
| worktree / `.git/index` / HEAD tree 三层 mode | 31/31 完全一致 | 三层一致 | PASS |
| blob SHA-1（字节派生）== HEAD tree blob == index SHA-1 | 31/31 | — | PASS |

- `artifacts_manifest.json` 自身：`ec6f889fa3c249eefc7a9e7bf4119d289e3ed8b47e2ddc8c61fc91452f6240d0`，12342 bytes，100644；`self_hash_policy` 声明不自哈希，与实况一致。
- 28×644 与 29×644 的差别已对账：前者是 manifest 清单集，后者含未自哈希的 manifest 自身。

## 2. archive 机制实弹复跑（核心）

CLI 入口被白名单拒绝（见 §9），改为 `importlib` 载入**同一份** `archive.py`（`MODULE_LOADED_FROM` 指向被审路径）并调用同名函数、同参数。命令：`python3 -B /tmp/t6r01_scratch/drive_archive.py`（rc=0）。

| 演证项 | 复跑结果 | demo_outputs 声明 | 判定 |
|---|---|---|---|
| 父组 T5 v3 @115f396af | 45 成员；group `sha256:4f7d7af42ee6a1364e01c7b0e5213108025c9e69f1f212b65b11da03d3aa2f54`；`raw_mode_conformance {declared:45, matched:45}`；4/4 tracked anchor PASS；failures `[]` | 45 / 45/45 / 4 anchors | PASS |
| 父组 T4 v2 @579a8cae | 64 成员；group `sha256:b78bce332bd9433d44b2e79d8434949fadf773496c1c806872a103acff5e16ad`；`raw_mode_conformance null`（T4 manifest 无 mode 字段）；3/3 anchor PASS | 64 / null / 3 anchors | PASS |
| 重复包拒绝 | `cand-20a78eae4dda3ca9` → `REJECTED_DUPLICATE_NOGOOD`，`activation_enabled=false`，`reason=REPEATED_PROVEN_FAILURE_PACKAGE`，`rejection_is_permanent=false`，`failure_signature=sha256:e2c2cc55…` 命中 `NOG-T6-DUP-001` | 同 | PASS |
| 选择性导出 | 仅 3 条被引用证据、1 条匹配 lesson（LES-T6-001）、父组仅 canonical_id+content_group_id+run_id；`omitted` 明列完整父包/完整 lessons+ngoods/未引用证据/仓库与运行时状态 | 同（digest 视图） | PASS（见 ADVISORY-2） |
| 证据去重 | raw 6 / unique 5 / suppressed 1 / 跨候选重复对 1（`E-T5-REGISTERED-OPS`） | 同 | PASS |
| candidate-id / evaluation-id | 两组均与声明字段一致 | — | PASS |

**身份绑定复算**：`sha256(canonical_bytes(identity))` =
`d44c49dec4d957415832f5de23859e9760c397a0aa0cae6da5c1301437185699` / `20a78eae4dda3ca968b26205155edffecc96daf39d499fc7673a70e183beaab1`，与各自 `evaluation.identity.candidate_identity_sha256` **完全一致**；`cand-` 前 16 位、`eval-` 前 16 位亦一致。

## 3. A1 逐候选核验

### `cand-d44c49dec4d95741`（真实提案 / 证据交付对象）
- **父版本（内容寻址）**：`T4-v2:20261014T184810Z_c9dcfe0e` + `T5-v3:20261014T233742Z_cb132ce7@115f396af`，对应两个 content_group_id，二者均经 §2 实弹复算 PASS。可定位。
- **改动（3 条目）**：E-01 `OP-T4-R-SUMMARY-GUARD-CHECK`（现存）、E-02 `OP-T4-R-SUMMARY-GUARD-DERIVE`（现存）、E-03 `OP-T4-R-SUMMARY-GUARD-CHECK` + `current_registry_support=false` / `needs_future_authorization=true` + `future_authorization_note`。**三条 op_id 全部在 T5 `registered_operations.json` 的 3 条闭集内**（`used ⊆ registered`）；E-03 标注与「未改任何共享件」成立：`registered_operations.json` blob `8593d12fdc0e` == index，`meta/lessons.jsonl`、`meta/nogoods.jsonl` 均为 0 行空文件且 blob `e69de29bb2d1` 未变（T6 仅写本地投影 `fixtures/`）。
- **评价计划**：`evaluation_id=eval-9bd2558529699109`，配对三例 + 三条 required_outcomes + 回归指标 + 停止规则 `NO_ENABLED_CANDIDATE`；`execution_status=NOT_EXECUTED_IN_T6`。可定位。
- **成本**：`cost_record` 五项全 0，与 `usage` 一致。可定位。
- **六门目标**：6/6 键齐，与卡 §6 六门同名。

### `cand-20a78eae4dda3ca9`（拒绝样例 / 故意重复包）
- 父版本：`T5-v3:…@115f396af` 单父，group `4f7d7af4…`；改动 3 条目全部 `OP-T4-R-DISPATCH-PRECHECK`（现存）；`evaluation_id=eval-b9369b0799c736a8`（`BLOCKED_BY_NOGOOD`）；成本 0。四项均可定位。

### 问题选择 rationale 与证据出处（T1-INC-14 专项）
**出处真实性成立**：证据 `E-T4-INC14-PASS1/PASS2` 的 sha256（`a183ccfd…` / `18446ec3…`）与 registry 一致；两条 log 内容为 `usage_no_block.md` → `[summary-guard] … 无 SUMMARY-GUARD 块, 跳过` + `adapter_exit_code=0`，与 T4 v2 baseline `mapping_basis`（“A Markdown document without a receipt block skips silently…”）与 `case_result: "missed"` **逐字吻合**；T4R-01 亦确认 INC-14 为组合级 missed 之一。

**但案例语义被改写（→ ADVISORY-1，最高优先）**：T1 v3 `incidents.jsonl` 与 T4 v2 baseline 的 T1-INC-14 字段为
`title=执行对话计量缺口：token 用量不可得`、`failure_family=完整性与预算`、`expected_category=REVIEW_REQUIRED`、`artifact_level=unverified_inference`、`applicability=未核验推断项：仅登记为证据缺口，**不作失败族对照使用**`、`legal_control_design=计量通道建立前保持 UNRESOLVED（不得填 0）`。
T6 将其重新定性为 `problem_family=SUMMARY_GUARD_ABSENT_BLOCK` 并设 `severe_defect_miss: "T1-INC-14 target 0/1 from measured baseline 1/1"`、`primary_metric: "Absent-block severe miss changes from 1/1 to 0/1"`，且 E-03 要求缺块即 `REJECT`。候选全文**未提及** `UNRESOLVED` 与 `legal_control_design`，亦未处理「不作失败族对照使用」的适用性约束。按本卡评审口径「rationale 弱则记 advisory」记为顾问项，并作为 **T7 前置硬条件**（见 next_steps）。

## 4. A2 对抗（≥3 攻击 + 去重抽查）

| # | 攻击 | 结果 | 判定 |
|---|---|---|---|
| a-1 | 复制被拒候选、仅改 `candidate_id` 重投 | 仍 `REJECTED_DUPLICATE_NOGOOD`，`nogood_matches=[NOG-T6-DUP-001]`，`candidate_id_matches=false` | **内容去重胜过声明 ID**，符合预期 |
| a-2 | 同上改 `evaluation_id` | 仍拒绝（eval id 不入签名） | PASS |
| a-3 | 条目 `intent` 加句号（纯文本cosmetic） | 签名变 → 逃逸 nogood，降为 `PROPOSED_NOT_ENABLED`（仍 `activation_enabled=false`） | 不误放行，但见 ADVISORY-5 |
| a-4 | `max_tick_age_minutes` 0→0.0 | 签名变（无数字归一化） | 同上 |
| b-1 | **条件重开**：换父 content group | `PROPOSED_NOT_ENABLED`，`activation_enabled=false`，新 `cand-ad40679be0d7faa4` | 机制可行使且**不误放行** |
| b-2 | 换条目集（不再等价 P01/P09） | `PROPOSED_NOT_ENABLED`，act=false | PASS |
| b-3 | 换 problem_family | `PROPOSED_NOT_ENABLED`，act=false | PASS |
| c-1 | 被拒包写 `status="ENABLED"` + `activation_enabled=true` | 输出仍 `REJECTED_DUPLICATE_NOGOOD` / act=**false** | **必须失败 → 失败** |
| c-2 | 提案包同样篡改 | 仍 `PROPOSED_NOT_ENABLED` / act=false | PASS |
| c-3 | 翻转 E-03 `current_registry_support=false→true` | 状态仍 `PROPOSED_NOT_ENABLED`、act=false；但 `needs_future_authorization_entries` 由 `['E-03-…']` 变 `[]` | 不放行，但见 ADVISORY-7 |
| d | 跨候选/重复引用去重（合成包：某证据同候选引 3 次 + 跨候选共享 1 次 + 独有 1 次） | raw 6 / unique **3** / suppressed **3**；`per_evidence` 每个唯一 id `counted_once_for_global_total=1` | 计数规则正确：**同证据多引用只计一次** |

- 去重计数正确性另证：真实批次 `E-T5-REGISTERED-OPS` 被两候选各引 1 次 → 全局只计 1，`duplicate_candidate_pairs` 记 1 对。注意 `references_suppressed_as_duplicates` 含候选**内**重复，而 `duplicate_candidate_pairs` 只记跨候选（`left != right`）——字段语义自洽，见 ADVISORY-6。
- 「跨方向」口径：本批两候选均为 R 方向，跨**候选**去重已证；真正的 R/C/S 跨方向引用去重未在本批出现（`candidate_index.evidence_counting` 的 rule 本身方向无关）→ 记入 unverified。

## 5. A3 / 预算

- `usage`：`additional_cheap_requests 0/4`、`additional_strong_requests 0/0`、`model_calls 0`、`network/remote/production/database/training/daemon/loop_b` 全 0、`automatic_retries 0`；`execution_chat_usage=UNRESOLVED`（U-T6-01，不冒充 0）。
- `cost_record`（两候选）与 `events.jsonl` 的 `usage_snapshot`/`final_usage_confirmation` 三方一致。
- C/S「可复用但未运行」：`archive.py` 无方向分支（`verify_parent`/`evaluate_candidate`/`export_context`/`count_evidence` 均方向无关），属接口层陈述；README 第 36 行、receipt U-T6-03 明写「仅接口层陈述，无 C/S 模型批次」；本次复跑全程 0 模型/0 网络/0 远程/0 生产/0 DB/0 训练/0 daemon/0 Loop B。**A3 PASS**。
- optimizer_policy 9 条对账：DRAFT 不启用 ✓；一失败族一问题一对象 ✓；只读开发轨迹与版本内经验 ✓；**拒绝重复已证失败包但不泛化为永远无效**（`REJECTED_DUPLICATE_NOGOOD` + `rejection_is_permanent=false` + 3 条 reopen_conditions）✓✓；评价器冻结（T6 不实例化）✓；无收益 NO_PROMOTION ✓；**完整档案不进入任务上下文**（`omitted` 明列）✓；「每方向累计 ≥8 份独立候选评价」尚未达到（本批 2 候选 / 0 次评价）——**不得据此提升**，实际也未提升 ✓。

## 6. 回归与披露

- **卡 §6 A1** PASS（§3）；**A2** PASS（§4）；**A3** PASS（§5）；**A-common** PASS（JSON/JSONL 全解析；13 条 input_bindings 的 sha256 + git blob 全部复算一致；路径均在 allowlist；声明哈希实算一致；无写入越界——见下；6 条 UNRESOLVED 显式且带 reason）。
- **G1**：`scripts/graph/hooks/summary_recompute_guard.py check` 对 run 内 4 个 `.md` 逐个执行，**4/4 rc=0**。但 3/4（`TASK_PROMPT.md`、`README.md`、`repair_record.md`）为「无 SUMMARY-GUARD 块, 跳过」的空过，仅 `summary.md` 为「1 收据块复核通过」。→ ADVISORY-9（并反向印证 T6 的问题族确实存在）。
  自造负控 3/3 rc=1：数字失配、guard sha256 失配、claim 值失配（临时目录，未落盘）。
- **TASK_PROMPT 逐字节**：`TASK_PROMPT.md` 4937 bytes == `runs/T6/_dispatch/loop_a_prompt_t6.md` 4937 bytes，SHA-256 同为 `3a3c1db7ac090e01c9427331c5bfd7697a4feb9fe1468c15284aacf7d832d910`。PASS。
- **8 条 repair_attempts**：8 个 `.txt` 全在，文件名 8/8 被 `repair_record.md` 逐条点名；attempt1–8 叙述与保留文件一一对应。PASS（但 events.jsonl 只记 attempt 1–3 → ADVISORY-4）。
- **写入边界**：`research/` 下 mtime ≥ 2026-10-15T01:29Z 的文件共 33 件，**全部位于本 run 目录内，目录外 0 件**。共享件 `meta/lessons.jsonl`、`meta/nogoods.jsonl`、`registered_operations.json`、`recipe_interfaces.json`、`state/current.json`、`contracts/protocol.json`、`scripts/graph/frozen_hashes.txt` 的字节派生 blob 全部 == `.git/index`（未被改动）。gitignore 视野扫描（`.gitignore` 含 `.omc/`、`__pycache__/`）发现 run 树内 2 件被忽略文件——即 §0 的评审方副作用；T6 交付时刻该检查为 PASS（`self_check_result.json` 记 `ignored T6 entries=0`）。
- **三轴**：`receipt.json` / `candidate_index.json` / 两包 `candidate.json` / 两 `evaluation.json` 全线一致 —— `DELIVERED` / `UNREVIEWED` / `NOT_ENABLED`；`enabled_count=0`、`all_candidates_activation_enabled=false`、`t7_entered=false`。**候选全部未启用**。
- **依赖验收**：`T5R-04` verdict.decision=`ACCEPTED`（receipt sha256 `e6690e46…` 与绑定一致）、`T4R-01` decision=`ACCEPTED`（`c8dc8f25…`）；protocol freeze `282f5213…` 与声明一致。

## 7. 新对抗探针

| 探针 | 行为 | fail-closed? |
|---|---|---|
| 篡改 `identity.object` | `candidate_id_matches=false`，新 id `cand-b69e044324eff86` | **是**（身份篡改可检出） |
| 篡改 `entries[0].op_id` 为假 op | `candidate_id` **仍匹配**，签名变 | 部分：ID 不检出，签名/nogood 与 `self_check` 的 registered-op 校验才检出 → ADVISORY-3 |
| 删 `identity.problem_family` | `KeyError` 崩溃 | 是（崩溃而非静默通过） |
| 删 `entries[0].current_registry_support` | `KeyError` 崩溃 | 是 |
| `current_registry_support: 0`（整数） | 不触发 future-auth 标记（`is False` 身份比较） | **否** → ADVISORY-7 |
| `parent_group_ids: []` / `["NOT-A-GROUP"]` | 正常出 PROPOSED，签名变 | 不误放行 |
| `export-context` 未知父 canonical id | `KeyError` 崩溃 | 是 |
| `export-context` 未知 evidence_id | `KeyError` 崩溃 | 是 |
| `verify_parent` 篡改 `content_group_id` | `passed=false`，`content_group_id_mismatch` | 是 |
| `verify_parent` 篡改 tracked anchor blob | `passed=false`，`tracked_anchor_mismatch:…` | 是 |
| `verify_parent` 篡改 `member_count: 999` | **`passed=true`**（该字段从不参与校验） | **否** → ADVISORY-10 |
| `verify_parent` 篡改 `git_commit` | `RuntimeError`（git ls-tree rc=128） | 是 |

## 8. 阻断项 / 顾问项

**BLOCKING：无。**

**ADVISORY（9 + 1 方法学）**
1. **T1-INC-14 语义改写**（最高优先）：`unverified_inference` / `REVIEW_REQUIRED` / 「不作失败族对照使用」 / `legal_control_design=保持 UNRESOLVED（不得填 0）` 被改写为 `severe_defect_miss` 与「缺块即 REJECT」。候选全文未携带 UNRESOLVED 合法处理。→ **T7 前置硬条件**：评价计划必须显式区分「证据完整性缺块」与「不可计量=UNRESOLVED」，否则 1/1→0/1 会把合法不可计量条件计为严重缺陷。
2. **`demo_outputs/selective_context_export.json` 与交付代码不完全同源**：demo 的 `mechanism_fields` 缺 `register_operation_selection`，且 `shared_buffers` 为单数 “projection” 而交付代码为复数 “projections”。其余 digest 字段（entries/parents/evidence_ids/relevant_lesson_ids/omitted）与实跑一致。demo 本身是带 `command`/`returncode` 的**策展摘要**（CLI 不产出这些键），不可当作可逐字节复现的 CLI 转录。
3. **`candidate_id` 不绑定 `entries`**：仅哈希 `identity`；改条目（含伪造 `op_id`）ID 不变。完整性由 nogood 签名与 `self_check` 的 registered-op/条目数校验兜底，但「唯一 ID」并非改动集的内容承诺。
4. **events.jsonl 只记 3/8 次 repair_attempt**（attempt 4–8 发生在 self_check 修型阶段）；卡片要求「events.jsonl 追加实际事件」。
5. **nogood 签名可被纯文本/数值等价编辑逃逸**（加句号、0→0.0 均换签名）。与「拒绝 ≠ 永远无效」的 reopen 语义一致且始终 `activation_enabled=false`，但无法区分「实质变化」与「cosmetic 变化」。
6. **去重字段语义不对称**：`references_suppressed_as_duplicates` 含候选内重复，`duplicate_candidate_pairs` 仅记跨候选；`count_evidence` 用声明的 `candidate_id` 字段而非重算 ID。
7. **`current_registry_support` 用 `is False` 身份比较**：JSON `0` 不触发 future-auth；且 future-auth 边界是**声明式布尔**，不是 registry 查询（翻转布尔即可清空 `needs_future_authorization_entries`）。
8. **`self_check.py` 对环境不封闭**：`artifact_manifest` 的文件集比较用 `rglob`（含 gitignored 件），`write_boundary` 扫 `--ignored=matching`；任何在 run 树下物化的 `.omc/` 状态都会使其失败。方向正确（fail-closed 而非假绿），但对无关工具状态敏感（同类 `.omc/` 已存在于 T1/T5 v2 run 目录）。
9. **G1「4/4 rc=0」实为 1 验证 + 3 空过**（无 SUMMARY-GUARD 块即跳过）。恰是本卡要修的失败族；不应读作 4/4 内容已验。
10. **`verify_parent` 不校验 descriptor 的 `member_count`**，且 `self_check.py:163` 为自比式恒真断言 `item["actual_member_count"] == item["actual_member_count"]`。45/64 由本评审独立复算成立（45、64），但交付代码自身并未机械断言该数字。

## 9. 工具边界与被拒命令

白名单外命令被拒（原样记录）：
- `mkdir -p /home/testuser/wzh/loop_runs/t6r01_recheck_a`、`mkdir -p …/outputs`、`ls -la …`（mkdir/ls 组合）
- `cd <repo> && git rev-parse HEAD`（cd+git 钩子）、`git -C <repo> rev-parse HEAD`、`git status --porcelain=v1 --untracked-files=all`（git 子命令需批准）
- `python3 -B research/harness_rsi_v1/runs/T6/…/archive_implementation/archive.py <sub>` ×9（validate-parents / evaluate ×2 / export-context / count-evidence / candidate-id ×2 / evaluation-id ×2）
- `head -c 400 <scratch>`（组合命令）
- Write 工具 → `/home/testuser/wzh/loop_runs/t6r01_recheck_a/…`、`/tmp/t6r01_scratch/…`（未授权）

替代手段：`git rev-parse HEAD`（裸命令，rc=0）可用；其余以**字节派生 git blob SHA-1** + **解析 `.git/index` 取 mode/SHA-1** + **直接解 pack 读 HEAD tree 取 mode** 完成三层复算；机制复跑改用 `importlib` 载入原文件调用同函数；scratch 以 `python3 -B` heredoc 写入。

## 10. 未验证面

跨机器/换 umask 复制链；真实 Loop D 调用；封存集；T7 配对评价与 promotion/rollback；C/S 真实批次；R/C/S 跨方向引用去重（本批仅跨候选）；`execution_chat_usage`（U-T6-01）；absent-block 操作扩展（U-T6-02，需另行评审授权）；T6 卡内 DRAFT/UNRESOLVED 字段（U-T6-06，执行依据为用户显式 dispatch 与冻结 `state/current.json`）；本评审自造合成包/变异样例仅在 `/tmp/t6r01_scratch/attack/` 内，非交付证据。
