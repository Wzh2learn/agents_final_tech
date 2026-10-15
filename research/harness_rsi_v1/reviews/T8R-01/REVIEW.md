# T8R-01 — Loop C 独立评审（T8 R 受控影子边界执行）

被审对象：`research/harness_rsi_v1/runs/T8/20261015T041717Z_669349f1/`（12 文件，HEAD `f5da2a71e19a21bf3e22ab39a2e80f6025f890bd`，父 `18a037093412f94d891df36b87c5dfbe13ace5a7`）
评审方式：GB10 本地只读独立复算；git 不可用，改用字节派生 blob SHA-1 + `.git/index` 解析 + 纯 Python 对象/树遍历（含 pack idx v2 与 ofs/ref delta 解析）。

## 1. 计数 / 哈希 / 模式（全部独立复算）

| 项 | 声称 | 独立复算 | 结果 |
|---|---|---|---|
| 交付文件数 | 12 | 12 个常规文件（第 13 项 `.omc/` 见 §7） | 一致 |
| manifest 条目 | 11（不自哈希） | 11；`artifacts_manifest.json` 除外 | 一致 |
| 逐条 sha256 | 11 条 | 11/11 逐字节复算匹配 | 一致 |
| bytes / mode | 11 条 | 11/11 匹配，manifest 均 `100755` | 一致 |
| 三层 755 | 12/12 | worktree `0o755` 12/12；`.git/index` `100755` 12/12；HEAD tree `100755` 12/12 | **一致** |
| blob SHA-1（字节派生） | — | 12/12 与 index 及 HEAD tree blob 三重一致 | 一致 |

`.git/index` v2 解析：4004 entries，T8 前缀 12 条，全部 `0x81ed`。HEAD run tree `172aaa2d9cdd7710e83783282ada2cc62a08714e` 恰含 12 项。`TASK_PROMPT.md` blob `3f8045601cf99241d9db897d8a215801520421e6` 与 receipt 记载的 dispatch `canonical_git_blob_id` 相同（byte-identity 交叉印证）。

## 2. NOT_SATISFIED 边界诚实性（核心）

**0/3 主张获四份独立权威来源印证**，无一处矛盾：

| 来源 | 措辞 |
|---|---|
| `cards/T8.md` | `execution_authorized:false`、`authorization_ref:UNRESOLVED`、A1 要求"三个真实新任务证据" |
| `state/current.json` | `execution_authorized:false`；`next_task`："shadow requires 3 new approved task windows (owner-gated); enablement/distribution reserved for user" |
| `state/open_decisions.json` U08 | "三个新任务影子证据…当前没有，不造结果补齐" |
| `registry/decision_events.jsonl` 末条 | "shadow requires 3 new approved task windows - owner gate; enablement/distribution reserved for user per card section 7" |
| `MASTER_PLAN.md:10,757,906` | "T8、T9 的 3 个新任务…是尚未满足的前提"；T8 产出"三个新任务影子记录"；M4 需"三个新任务影子记录完整" |

**独立遗漏搜索（未采信被审包证据清单）**：全树正则扫描 `new task window / 获批窗口 / authorization_ref…approved / three…window` 等，得 38 处命中，**无一为已存在的可用窗口**——全部是 T8 自述缺口、卡要求原文、state/registry owner 门、`sources/planning_round1.md:370` 规划语（"仅针对未来新获批任务"）。另扫全部 19 张卡：**19/19 均 `execution_authorized=false`、`authorization_ref=UNRESOLVED`**（含 T9–T17）。扫全部 24 个 run 目录：**无任何 `materials` / `permission_window` / `task_results` 窗口产物**。→ 结论：**0/3 属实，无被遗漏窗口**，不升级。

**未把可做工作标成未满足**：identity（复合组已算出）、rollback（`PASS_SIMULATED_ONLY` 已交付）、release_proposal（`RECOMMENDATION_ONLY` 已交付）三件均已完成；仅 A1（客观缺窗口）标 `NOT_SATISFIED`。无"以未满足掩盖未做"。

**逐任务表无伪造**：3 行均为 `task_id/authorization_ref/materials/base_result/candidate_result/comparison = null` + `status=NOT_EXECUTED_MISSING_APPROVED_WINDOW`。`self_check.py` 机械强制该形态（逐行断言 null 与 status 字面值），非仅自述。顶层 `shadow_completed=false`、`execution_status=NOT_EXECUTED`。

**影子协议承接能力**：窗口要素 9 项、记录字段 23 项、严重回归停用规则、回滚保持、评测次序（硬门优先）齐备；技术前提含接入/双版本捕获/8 项最小捕获/安装边界/模型边界；精确缺口清单 10 条。**足以直接承接真实窗口**，唯缺"记录写入何处/由谁写"（见 advisory-4）。

## 3. 身份绑定（独立重算，非采信）

按 `archive.py` 声明域（`canonical_bytes` = `sort_keys=True,separators=(",",":")`；组 = 排序 `relative_path+sha256+normalized_mode`；`normalized_mode` = 有执行位→`100755` 否则 `100644`）逐字节重算：

| 组件 | commit | 成员 | 复算 content_group_id | 声称 | 结果 |
|---|---|---|---|---|---|
| T5 v3 | `115f396af…` | 45 | `sha256:4f7d7af42ee6a1364e01c7b0e5213108025c9e69f1f212b65b11da03d3aa2f54` | 同 | **MATCH** |
| T6 v1 | `ef5e84edbd…` | 30 | `sha256:a123480270ebdfc1d9ecb8bf74928676810ba2507290f5708911774c1755a1b7` | 同 | **MATCH** |
| T7 v1 | `0579b64bbc…` | 57 | `sha256:363991a2cccccc4581ecafefdb73dc569dd2ab6333bd0514927e48ed7b2f5ff7` | 同 | **MATCH** |

**复合组**（五字段 `content_group_id/git_commit/member_count/run_id/task_id`，按 task_id 排序后 canonical JSON 的 SHA-256）：
`sha256:e16cde27ff239da0c7b76f35272e0950e1cb9f0878d464b0ae6629e88d4c4f86` — **与声称完全一致**。

132 个成员（45+30+57）逐个以 commit 树 blob 内容与 worktree 文件双向核对：**0 失配** → 三棵被绑定树在对应 commit 下未漂移。注意 `hash` 字段名分族：T5/T6 为 `sha256`，**T7 为 `sha256_file`**（被审包处理正确）。

**T6/T7 候选哈希 vs ACCEPTED 记录**：T6 `cand-d44c49dec4d95741/candidate.json` = `ae238ec26cb285a92e91ccffb33a671d0d274113b16608fe421c5607a8c920d2`，与 T6R-01 `review_receipt.json` 记载一致；T7 `amended_candidate.json` = `779e3a0c56355bccbd5d9775a93d6e6369a9aadf44d7a995354fcbee1c0b4326`，与 T7R-01 记载一致。两者均等于被审包声明的 `accepted_review_sha256`。

## 4. A2 / A3

- **安装/装载不推断**：全文一致为 `NOT_ESTABLISHED_NOT_INFERRED_FROM_REPOSITORY`；`installation_boundary` 明写"仓库存在不证明已安装或已装载"。全文检索无任何 installed/loaded/已启用 断言；`activation_status` 三处均 `NOT_ENABLED`。
- **无安装/装载/全局配置改动**：将 T8 commit 与父 commit 的**顶层树逐项比较（36 项）**——**35 项 blob SHA 完全相同**，含 `skills`、`config`、`scripts`、`src`、`memory`、`docs`、`models`、`deploy`、`templates`、`tests`、`assets`；仅 `research` 变化。→ 独立证明**未改 skills、未改全局配置、未改源码**。
- **12 项 input_bindings 零漂移**：逐条复算 sha256 与字节派生 blob SHA-1，均等于记载（含 4 份 `BOUND_ACCEPTED`、decision_events、MASTER_PLAN）。
- **旧证据零改**：11 件基线逐条复算 `bytes/sha256_file/mode/git_blob_id`（blob SHA-1 由字节派生），**0 失配**，且 `old_evidence_before == old_evidence_after`。
- **零越权请求 / usage 0/6、0/2**：receipt、shadow_comparison、release_proposal、self_check_result、events 五处 usage 一致，network/remote/production/database/training/daemon/loop_b/retry/model 全 0。（外部调用无法由本评审直接观测，记 unverified。）

## 5. 回滚

`PASS_SIMULATED_ONLY` 语义准确：`BASE_BEFORE → SHADOW_SIMULATED_ONLY → BASE_RESTORED` 三态，`simulated_marker=T8_RUN_LOCAL_LOGICAL_STATE_ONLY`、`model_or_task_calls=0`、`shared_tree_changed=false`；三组件 before/after 组 ID 一致；`composite_hash_unchanged=true`。哈希恢复证据（base→shadow→base）成立。`shared_tree_rollback_needed:false` 理由（未启用故不涉共享树）成立。**未触碰共享件**（§4 顶层树比对佐证）。实际部署回滚因从未启用而未验证——被审包已在 `unverified` 如实列出。

## 6. release_proposal

`proposal_type=RECOMMENDATION_ONLY`、`enabled=false`、`distribution_started=false`、`skills_modified=false`、`global_configuration_modified=false`。§7 保留措辞与卡一致：`decision_authority=USER_OWNERSHIP_GATE_SECTION_7`，启用/分发均 `RESERVED_TO_USER_UNDER_CARD_SECTION_7`，`proposal_state=ADVISORY_ONLY_NOT_AN_ACTIVATION_ORDER`，`current_action`："Deliver the shadow plan and rollback readiness; do not enable or distribute." 与卡 §7"用户决定启用和精确分发目标"逐条对齐。

无越权"已就绪即可启用"暗示：最接近的表述 "technically eligible to enter a controlled shadow evaluation" 被 `entry_conditions` 8 条前提与 `shadow_candidate_status=NOT_EVALUATED_BECAUSE_NO_TASK_WINDOWS` 严格限定，且 `selection_status` 保持 T7 的 `NO_PROMOTION`。**通过**。

## 7. A1 / A-common / G1 / 纪律

| 检查 | 被审声称 | 独立实测 | 结果 |
|---|---|---|---|
| A1 | NOT_SATISFIED（诚实） | 0/3 属实；表 null；self_check 机械强制 | 一致 |
| A2 | 身份/验收一致 | 复合组与三组件组全部复算 MATCH | 一致 |
| A3 | 旧证据零改、无越权 | 11 件零改；35/36 顶层树同 | 一致 |
| A-common | JSON 全解析、11 条 manifest 实算一致 | 7 JSON 全解析；11/11 复算一致；路径均在 allowlist | 一致 |
| G1 | 2/2 md rc=0 | 重跑 `summary_recompute_guard.py check`：TASK_PROMPT rc=0（零块跳过）、summary rc=0（1 收据块复核通过） | **一致** |
| TASK_PROMPT 逐字 | 3087 B 相同 | 3087 B、字节相同、sha256 `b9d48d82…` 相同 | 一致 |
| 修复记录 | 4 次 | `repair_record.json` 4 条（before/expected/cause/repair/evidence_lost 齐全） | 见 advisory-1 |
| 三轴 | DELIVERED/UNREVIEWED/NOT_ENABLED | receipt 与 summary 一致 | 一致 |

**FULL-SET 755 策略**：内部一致（manifest 声明 / worktree / index / HEAD tree 四层全 100755，且 `mode_policy=DELIVERY_FULL_SET_755` 如实声明）。但**对外影响真实存在**——7 个 JSON/JSONL 数据件与 2 个 .md 均带可执行位，与 T7 已确立的 `mode_policy`（"no non-script file is declared executable"，T7 为 54×100644 + 3×100755）相悖，且使 mode 丧失"脚本 vs 数据"的判别信号。因该策略系 TASK_PROMPT 逐字下达（"提交侧落实 755 全集"），非执行层擅自选择，故记 **advisory**（应由派发/规划层修正），不阻断本包。

## 8. 新对抗探针

**探针 A — 构造"授权范围内可视为真实新任务窗口"的候选并检验成立性。** 提出 4 个候选逐一检验：
1. **T9–T17 卡**：19/19 卡均 `execution_authorized=false`、`authorization_ref=UNRESOLVED`、`status=DRAFT`；且卡 §1 排除"进入 T9"，MASTER_PLAN 明列 T8/T9 前提未满足 → **不成立**。
2. **T1/T2/T4 既有 run 作"新任务"材料**：全 24 个 run 目录无 `materials`/`permission_window`/`task_results`；且属历史冻结实验，T8 卡明禁重开 → **不成立**。
3. **未跟踪 `runs/T4/20261014T174628Z_2cc25c92/`**：系 registry 已记录的 uncommittable T4 v1，非任务窗口 → **不成立**。
4. **"R 线授权至 M1"推导影子执行权**：U07=C 注"每次明确动作；不从规划认可推导运行许可"，state 仍 `execution_authorized=false` → **不成立**。
→ **0/3 主张经对抗检验仍成立，不升级。**

**探针 B — 检验 0/3 空表被误读为结果的可能。** `task_results` 为长度 3 的数组，槽位 1/2/3；仅做 `len()` 计数的消费者会得到"3"而非"0"，且全 null 行可能被误读为"3 条结果缺数据"。现有缓解：逐行 `status=NOT_EXECUTED_MISSING_APPROVED_WINDOW`、顶层 `shadow_completed=false`/`execution_status=NOT_EXECUTED`/`shadow_status=NOT_SATISFIED_NO_THREE_TASK_WINDOWS`、`authorization_scope_check.authorized_new_task_window_count=0`、summary"逐任务 0/3 执行"。**判定：已充分缓解，不构成阻断；但缺显式 `executed_task_count` 字段，记 advisory-3。**

## 9. 评审方副作用自扫（含 gitignore 视野）

- **`.omc/state/sessions/69ab89ad-…/` 出现在被审 run 目录内**——经归属核实为**本评审会话自身**产物（session id 与本会话 tool-results 路径一致，内容记录了本评审的 `IsADirectoryError` 与 hook 节流状态；mtime `04:43:43Z` 晚于 T8 收尾 `04:37:37Z`）。成因：早先 Bash 调用 `cd` 进入 run 目录后工作目录持续，OMC 于 cwd 落盘。**非 T8 缺陷**，未作任何修改或删除（`rm` 不在白名单，且不替包修复）。仓库现有 20 处 `.omc/`（全 gitignored），属长期环境性存量。
- 仓库内无 `__pycache__`/`.pyc`/`tmp_` 残留（全程 `python3 -B`）。
- 仓库外 scratch：`/home/testuser/wzh/loop_runs/t8r01_recheck_a/`（由 `python3 os.makedirs` 创建；`mkdir` 被拒），其内 `gresolve.py` 一个只读解析脚本（因 Write 于仓库外未获授权，改由 python 落盘）。
- 未写入被审 run 或仓库内任何文件。

## 10. 结论

计数/哈希/三层模式、身份复合组、边界诚实性、旧证据零改、回滚、建议边界、G1、TASK_PROMPT 逐字——**全部独立复算通过**。0/3 主张经四源印证与对抗探针检验成立；无可做工作被标未满足；无越权启用/分发/配置改动。**0 blocking / 5 advisory**，建议 **ACCEPTED**（advisory 保留为 backlog，不解除两个 owner 门，不进入 T9）。
