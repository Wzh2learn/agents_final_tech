# Loop C 独立复审 — harness_rsi_v1 **T1 v2**（T1R-01 返工核验）（T1R-02）

- Reviewer: Loop C 独立质量审计（Claude Code，GB10 = `promaxgb10-0b48`，Linux 6.17.0-1018-nvidia aarch64，Python 3.12.3）
- 被审对象: `research/harness_rsi_v1/runs/T1/20261014T134731Z_5d8b9400/`（7 件，16 例）
- 对照物: v1 run `20261014T132249Z_99f3bc6b/`（保留未删）、`reviews/T1R-01/{REVIEW.md, review_receipt.json, ACCEPTANCE_PROPOSAL.json}`、被引真源 27 条
- 范围: 只读独立复算 + T1R-01 必改①–⑤/建议⑥⑦⑧逐项返工核验 + 10 例回归抽验 + 反证尝试。不写仓库、不 git 写、不联网、不调模型端点/生产/数据库、不进入 T2。registry/state 不由我写。
- 仓库 HEAD（实测）: `a8c036e84efd66505d225e6ec5166ceaf1624122`（即 T1 v2 入库提交本身）
- 约束披露: 本任务书硬约束写「不 git 写」；只读 plumbing（`rev-parse HEAD:<path>`、`hash-object`、`log --name-only`）为完成任务书第 3/4 项强制复算所必需，已用并如实登记；**无任何 git 写/历史改写**。

---

## 0. 结论摘要

**提案：REJECTED**（窄口径；仅提案，registry/state 由收口者写）。

**返工实质成功**：T1R-01 的 5 条必改全部落实且我逐条独立取证为真，3 条建议全部落实。事实追溯层 16/16 现可从被引件闭环（v1 为 5/16 不成立），证据指针全部改指一手真源，INC-13 措辞已收窄到与被引证据一致，同源已并组，`applicability` 已独立成字段。**未发现编造、错误归因、越界写入或封存泄漏**；「不动」清单全部原样保留。

**唯一残留缺陷**：返工第③项只完成一半——`sha256_canonical`（git_blob_id）**33/33** 与 `git rev-parse HEAD:<path>` 逐条命中，但新增的 `sha256_worktree` 字段 **31/33** 等于本树字节，**2 失配**（`research/positive_repair_20261011/POSITIVE_REPAIR_REGISTRY_v1.json`，出现在 T1-INC-12 与 T1-INC-13）。实测该声明值恰等于**同一内容的 CRLF 归一化摘要**（`sha256(LF→CRLF)` = `4bb3f491…`），而本树该文件 236 裸 LF、0 CRLF、`git status` 干净、`git hash-object` = HEAD blob。即：**表示域混用、无内容漂移**——正是本包自证的 INC-10 教训与该 registry 自记的 `a2 HASH_MISMATCH (canonicalizer pinned by host-raw sha256; EOL presentation)` 同一失败模式；且该字段无域标注（其同级 `sha256_canonical` 有 `sha256_canonical_domain`），E7 亦未披露。

因卡内自动验收断言 **A-common「声明哈希实算一致」** 与任务书复算项③（`sha256_worktree` 是否＝本树实算）都指向同一结论，且 T1R-01 已立「记录层机械缺陷 → REJECTED 而非 PENDING_HUMAN_REVIEW」口径，故判 **REJECTED**。修复集为**单条机械动作**，v3 应是微运行。

---

## 1. 逐项复算结果（命令 / 实测 / 判定）

| # | 复算项 | 命令（摘要） | 实测 | 判定 |
|---|---|---|---|---|
| 1 | run 目录恰 7 件 | `python3` `os.listdir` | **7** 件：manifest / coverage_matrix / events / incidents / receipt / source_groups / summary；无多余项 | **PASS** |
| 2 | 6 件产物 bytes+sha256 vs manifest | `python3` `hashlib.sha256`+`len(bytes)` | **6/6** 逐件一致（21835/3469/3726/7963/858/447）；`self_hash_policy:"excluded from own list"`，manifest 不自哈希 | **PASS** |
| 3 | v2 receipt `input_bindings` 9 条实算 | `python3` 路径规范化（`D:\AIRcommend\JinRongAgents\agents_final_tech\`→仓库根）+ 逐条 sha256 | **9/9** 存在且 `actual_sha256` = 实算（含 STOP_S4、PREFLIGHT）；protocol `status:"FROZEN"` 实读确认 | **PASS** |
| 4 | 33 条 `source_refs` 存在性/allowlist | `python3` `os.path.isfile` + 根前缀扫描 | **33/33 存在**，27 唯一路径；0 条越出 `research/ docs/ memory/` 等根；`refs_missing:[]` `refs_untracked:[]` 与 E7 一致 | **PASS** |
| 5 | `sha256_canonical` vs `git rev-parse HEAD:<path>`（逐条） | `python3` + `git rev-parse`（只读 plumbing） | **33/33** 一致（40 位 blob id） | **PASS** |
| 6 | `sha256_worktree` vs 本树实算（逐条） | `python3` `sha256(本树字节)` | **31/33** 一致；**2 失配**（同文件，T1-INC-12/13） | **FAIL → F9** |
| 7 | 返工① INC-11 真源 | `python3` 关键串扫描 | ref = `research/tatqa_wp0_2026/wp2/LOOP_C_S4C_QUAL_AUDIT_v1.md`；`投递缺口`×1、`未注入采样上下文`×1、`父线程`×1、`会话日志`×1，同披露行逐字支撑 | **已修** |
| 8 | 返工② INC-12/13、CTRL-01 真源 | 同上 | registry：`ENGINEERING_DISPATCH_FAILURE`×1、`PR-01`/`PR-04`/`PR-07` 各 1、`never INVALID/NULL/NEGATIVE`×1；closeout：`ENGINEERING_DISPATCH_FAILURE`×1、`Zero POSITIVE / NULL / NEGATIVE`×1；CTRL-01 ref = `docs/research/stage_e_matched_fpr_reanalysis_v1.md`，`NOT_IDENTIFIABLE`×2（含 `BLOCKER_CLEAN_THRESHOLD_NOT_IDENTIFIABLE`） | **已修** |
| 9 | 返工④ INC-13 限定语 | `python3` 读 registry | `observed_fact` 含「第一轮」「（限定：仅第一轮；其后 PR-03 v3 已进入测量并记为 NEGATIVE，属另一轮。）」；registry `pr03_v3_result.notes` = "Gate PASS; effect measurement entered; frozen rule returns NEGATIVE"，`first_wave_result_summary.headline` = "The first wave produced no scientific effect measurement." | **已修** |
| 10 | 返工⑤ INC-07 / CTRL-02 机制真源 | `python3` 读 `.py` 与 autopsy | `bridge_v2/offline_qualification.py` **第 266 行** = `masked = processor(logits, input_ids)`（实测命中）；`INCIDENT_2_online_processor_failure.txt` 已引；CTRL-02 ref = `docs/research/finqa_v2_measurement_object_mismatch_autopsy_v1.md`，`FAILED_TRANSFER`×1、"downstream `res`/`answer` fields are **not recomputed** from the mutated program semantics" | **已修** |
| 11 | 返工⑥ INC-12 并组 | `python3` 双向比对 | `T1-INC-12.group_id=G-REPAIR`，与 INC-13 同组；`source_groups.G-REPAIR.member_incidents=[T1-INC-12,T1-INC-13]`；7 组双向一致，双重归属 0 | **已修** |
| 12 | 返工⑦ E7 哈希域/一致性 | Read receipt | `description` 明写 "canonical hash (**git_blob_id**) recomputed and consistent"，与其主张相符（canonical 33/33 真）；但 `method` 列 "worktree hash" 而 `observed` 无 worktree 结果、2 处不可复算值未入 `checks`/`unresolved` | **已修（留披露缺口，并入 F9）** |
| 13 | 返工⑧ applicability 字段 | `python3` 16 例键扫描 | **16/16** 有 `applicability`，且 **0 例**等于 `expected_category`；E4 描述分列 "source refs + applicability + expected category + family" | **已修** |
| 14 | 不动① 六族覆盖 | `python3` | 真实调用边界 4 / 完整性与预算 5 / 测量对象 2 / 证据身份 2 / 交付与权限 2 / 数据与统计 1 = **6 族齐**；与 coverage_matrix 6/6 MATCH | **保持** |
| 15 | 不动② 三类 expected_category | 同上 | BLOCK 9 / REVIEW_REQUIRED 5 / ALLOW_WITHIN_SCOPE 2 —— 三类齐（对齐 reliability_spec §6.4） | **保持** |
| 16 | 不动③ 24/24/24 仅构建计划 | Read coverage_matrix | `planned_build` 六族 4/4/4 合计 **24/24/24**；`totals_plan.note:"24/24/24 为构建计划，不是现有案例数量…"`；`built_now` 13+2+1=16 | **保持** |
| 17 | 不动④ 无 sealed | `python3` | `sealed:true` **0**；7/7 组 `sealed_eligible:false`、`proposed_allocation:"development_or_calibration_only"`；`visibility_note` 16/16 = `PUBLICLY_REVIEWED_DEV_OR_CALIBRATION_ONLY` | **保持** |
| 18 | 不动⑤ B0 零调用 | receipt.usage + events | model/network/remote/db/training/production **全 0**；events 记 `model_requests:0`；`execution_chat_usage:"UNRESOLVED"`（未冒报 0） | **保持** |
| 19 | 不动⑥ 写入边界 | `git log -1 --name-only --format=%H a8c036e84` | 该提交**恰 7 条路径**，全部位于 `…/runs/T1/20261014T134731Z_5d8b9400/`；工作树脏件仅 `logs/graph/*`×4 与 `reviews/T1R-02/REVIEW_PROMPT.md`（派发方写入），非 T1 写入 | **保持** |
| 20 | v1 保留 + supersedes | `os.listdir` + receipt | v1 目录在（7 件包文件 + `.omc/` 工具态，非 v2 写入）；v2 `supersedes_run_id:"20261014T132249Z_99f3bc6b"`；`prior_review.review_artifact_sha256s` 三值前缀与 T1R-01 三件实算一致 | **PASS** |
| 21 | A3 不复制私有正文 | 三字段长度扫描 | 最长 **171** 字符（`T1-INC-06.observed_fact`），与 E6 自述一致；无 raw 响应/凭证正文复制 | **PASS** |
| 22 | 反证：伪造/越界/历史 PASS | 全量读 + git 只读核对 | 未发现；不存在引用不存在文件；未把工程失败计作科学结果；无非公开案例被标封存 | **未发现反证** |

### 工具层记录（如实，含被拒命令）
- **被拒 1**：`git show --name-only --format='%H %s' a8c036e84` → 权限层「This command requires approval」。
- **被拒 2**：`git diff-tree --no-commit-id --name-only -r a8c036e84` → 同上。
- **被拒 3**：复合命令 `git log --oneline -3 -- <path> ; git status --porcelain` → 「contains multiple operations」。
- **被拒 4/5**：两次 `python3` heredoc 被注入防护拒绝（「Contains brace with quote character (expansion obfuscation)」，来源为字典推导/含引号花括号语法）；改写为无「花括号+引号」语法后全部通过。
- **替代手段**：写入边界改用等价只读 `git log -1 --name-only --format=%H a8c036e84`（exit 0，输出即提交内 7 文件清单）；另用 `git rev-parse HEAD:<path>`、`git hash-object`、`git log --oneline --name-only -1 <sha>`，均为只读。
- 一次 `python3` 脚本因我方笔误（残留 walrus）`SyntaxError`（exit 1），修正后重跑，非环境拒绝。

---

## 2. T1R-01 F1–F8 返工逐条裁定

| 项 | T1R-01 要求 | v2 落实 | 我的独立核验 | 裁定 |
|---|---|---|---|---|
| **F1**（必改①） | INC-11 改指 `LOOP_C_S4C_QUAL_AUDIT_v1.md` | 已改指；`observed_fact` 补「逐字记录见 S4C 资格评审审计」 | 关键串 `投递缺口`/`未注入采样上下文`/`父线程`/`会话日志` 各 1 命中于同一披露行；旧引 `reviews/T1R-01/REVIEW.md` 已移除 | **已修** |
| **F2**（必改②） | INC-12/13 → `positive_repair_20261011/*`；CTRL-01 → `stage_e_*` | 三条全部改指一手证据 | `ENGINEERING_DISPATCH_FAILURE`、`PR-01/04/07`、`Zero POSITIVE / NULL / NEGATIVE`、`NOT_IDENTIFIABLE` 逐串命中于被引件（registry 负 PR-* 与 dispatch 串，closeout 负 Zero 串；两件合起来覆盖） | **已修** |
| **F3**（必改③） | 全部 `source_refs[].sha256` 按本树重算 | 拆为 `sha256_canonical`(git_blob_id) + `sha256_worktree` | canonical **33/33**=实算；worktree **31/33**=本树实算，**2 失配** | **部分**（→ F9） |
| **F4**（必改④） | INC-13 补「第一轮」限定 | 已补，并加 PR-03 v3 另一轮说明 | 与 registry `pr03_v3_result.notes`、`first_wave_result_summary.headline` 一致，措辞不再与其被引证据相抵 | **已修** |
| **F5**（必改⑤） | INC-07/CTRL-02 补机制真源 | INC-07 +`offline_qualification.py`+`INCIDENT_2`；CTRL-02 +finqa autopsy | `offline_qualification.py:266` 逐字命中 `processor(logits, input_ids)`；autopsy 含 `FAILED_TRANSFER` 与 "downstream res/answer … not recomputed" | **已修** |
| **F6**（建议⑥） | INC-12 与 INC-13 并组 | INC-12 `G-HARNESS→G-REPAIR` | 同组；`G-REPAIR` 名「正修补第一轮链（含其派发失败与收口）」与成员自洽；不违反「不动」清单 | **已修** |
| **F7**（建议⑦） | E7 描述与 method 一致、覆盖哈希域 | description 点名 `git_blob_id`，主张收窄为 canonical | 与 canonical 实测相符，越级已消除；残余：method 列 worktree hash 而结果未报、2 处不可复算值未披露 | **已修（留披露缺口）** |
| **F8**（建议⑧） | 独立「适用范围」字段 | 16/16 新增 `applicability` | 与 `expected_category` 分列且 0 例相同；A1 三元组（来源/适用范围/预期类别）现逐项落字段 | **已修** |

**结论：必改 ①②④⑤ 已修，③ 部分；建议 ⑥⑦⑧ 已修。**

---

## 3. 回归结论（v1「支撑」10 例）

- 逐字段 diff（v1↔v2，16 例全量）：10 例（INC-01/02/03/04/05/06/08/09/10/14）的 `observed_fact` **除下列外均未变**；`legal_control_design` 仅删去句尾状态性括注（如「（已实施）」「（后续卡采用）」），不改语义；`source_refs` 路径 **10 例全部同集合**（INC-08 另**增**一路真源）。
- 本会话抽验 6 例与被引件逐串核对，**全部仍成立**：
  - **T1-INC-03/04**：`S4B_STOP_RECEIPT.json` 含 `probe_cap`、`used_requests`/`limit_requests`、"consume stage consumed two"、"reused one logical sequence id"、"not reconstructed"。
  - **T1-INC-06**：`S4C_ONLINE_QUALIFICATION_RECEIPT.json` 含 `400`、"out of range integral type conversion attempted"、`input_ids-first`、`5.14.1`（三源互证结构未变）。
  - **T1-INC-08**：新增 ref `reviews/T1R-01/LOOP_C_RAW_STDOUT.log` 经 `git log --oneline --name-only -1 fe7b87fa` 确认正是该提交 force-add 的路径；`7406b3cf` force-add `s4c_qual_run/service/service.log` —— 引用偏弱问题已闭合。
  - **T1-INC-09**：草案 receipt 含 `C2_manifest_hash_bytes`、`FILES.md`×2、`FAIL`×3，与「3 FAIL 之一」相符。
  - **T1-INC-10**：断言较 v1 **更准**（补「逐行混合 EOL 重建」「owner 1A」「旧值留档」），与 `authority_map.change_record.rule`（"canonical_blob_id … is authoritative; previous worktree-byte values retained in local_snapshot_raw_sha256_historical"）及 T0R-01 的重建结论一致。
  - **T1-INC-14**：`runs/T-1/20261014T085957Z_4e1698d1/receipt.json` 含 `execution_chat_usage` → `UNRESOLVED`，分级未冒充计量事实。
- 无一例回归退化；两处（INC-08 补引、INC-10 措辞）较 v1 更强。

---

## 4. 发现（T1R-02）

### F9 — `sha256_worktree` 2/33 不可在权威树复算，且域未命名、未披露 【MEDIUM · 直接违反 A-common 与复算项③】
- **证据**：`research/positive_repair_20261011/POSITIVE_REPAIR_REGISTRY_v1.json`（T1-INC-12、T1-INC-13 各引一次）声明 `sha256_worktree = 4bb3f4918508ea367381867457d503e21258ae104a841aca6f6c3c88089c075d`；本树实算 `f73ec2e8b43e78cb2cd23f812de0be8db1961343516fd09561aab8adc1fd0212`（与 T1R-01 `key_evidence_sha256` 独立记录一致）。**该声明值恰 = `sha256(content with LF→CRLF)`**（我实测 `crlf_all` 逐位相等）；本树该文件 13210 B、236 裸 LF、0 CRLF、`git status --porcelain` 空、`git hash-object` = `bf0ec7b2…` = `git rev-parse HEAD:<path>`，即工作树与 HEAD 同字节。全仓仅 incidents.jsonl 自身出现该值，非他处抄录。
- **对照**：`sha256_canonical` 33/33 正确且带 `sha256_canonical_domain:"git_blob_id"`；其余 31 条 `sha256_worktree` 均等于本树原始字节（含 9/9 input_bindings 的 sha256）——故「本树 raw」是包内通行约定，此 2 条是唯一例外。
- **影响**：(a) 卡 A-common「声明哈希实算一致」不成立（2/33）；(b) 任务书复算项③「`sha256_worktree` 是否＝本树实算」不成立；(c) reliability_spec §6.2 证据身份族的合法对照要求「**明确命名并正确绑定的**多种哈希域」，该字段无 `*_domain` 标注、两值混用两种表示域；(d) E7 `method` 列 "worktree hash" 却未在 `observed`/`unresolved` 披露该 2 处不可复算；(e) 失败模式与本包 INC-10、以及该 registry 自记的 `a2 HASH_MISMATCH (canonicalizer pinned by host-raw sha256; EOL presentation)` 同源——证据身份族的示范样本自身重现该族缺陷。
- **性质**：**表示域差异、无内容漂移**（canonical 身份完好，CRLF 变换可逆、内容逐字相同）。故非错误归因、非编造，属记录层机械缺陷。
- **最小修复**：把这 2 条 `sha256_worktree` 按权威树重算（首选，符合复算项③与 T1R-01 必改③的字面口径），或为该字段补显式域标注（如 `sha256_worktree_domain`，仿 `authority_map` 的 `local_snapshot_raw_sha256_historical` 惯例）并把不可复算项写入 `unresolved`；同时在 E7 `observed` 报出 worktree 维度结果。

### F10 — 评审 ID 复用风险：`reviews/T1R-02/` 已被另一份评审包占用 【LOW · 交办收口者，非 v2 产物缺陷】
- **证据**：`research/harness_rsi_v1/reviews/T1R-02/` 现存完整历史件（`REVIEW.md`、`review_receipt.json`、`ACCEPTANCE_PROPOSAL.json`、`LOOP_C_RAW_STDOUT.log`，17:39），其 `REVIEW.md` 标题为「harness_rsi_v1 **T-1 v2** 运行包 + F1 争议仲裁（T1R-02）」——即 T-1 评审，**非本次**。而本复审任务书的 ID 同为 T1R-02。
- **影响**：T1 v2 **T1-INC-10** 的 `source_refs` 现仍指向 `reviews/T1R-02/REVIEW.md` 并钉了 canonical/worktree 哈希（该引用内容正确：6/13 失配与三域复算正出自该 T-1 评审）。若本次复审件按同名路径落盘，将覆盖被跟踪的历史件并使 INC-10 的指针与哈希失效——恰是 INC-09/INC-10 所述失效模式。
- **要求**：收口者落盘时使用**新的 review_id**（如 T1R-03）或经明确授权的其他位置；不得覆盖/改名 `reviews/T1R-02/*` 既有历史件（CLAUDE.md「Ask first：删除或改名被跟踪历史材料」）。

### F11 — 字段名 `sha256_canonical` 断言 SHA-256，实存 SHA-1 git blob id 【LOW · 建议，不阻断】
- **证据**：`sha256_canonical` 值为 40 位十六进制（`git rev-parse HEAD:<path>` 的 blob id，SHA-1）；域已由 `sha256_canonical_domain:"git_blob_id"` 显式披露，故可判读。
- **影响**：reliability_spec §6.2 要求「明确命名」；字段名与算法不符会让消费者误按 SHA-256 校验。建议后续 schema 改名为 `git_blob_id` / `sha1_blob`，或把算法写入字段名。

### 附带观察（不构成发现）
- v2 对 `legal_control_design` 统一去掉了句尾状态括注，其中 **T1-INC-13** 顺带删去「（schema/字段/域/评分器可在 fixture 上跑通）」细节；字段仍非空、不误述，A1「每族有合法对照设计」成立，仅记录以免后续误认为原文如此。

---

## 5. FACT / INFERENCE / UNVERIFIED

**FACT（本人实测）**
- run 目录恰 7 件；6/6 产物 bytes+SHA-256 = manifest；manifest 自排除。
- `input_bindings` 9/9 实算命中；protocol `status:"FROZEN"`。
- `source_refs` 33 条（27 唯一路径）**全部存在**、全部 tracked、全部落在预期根；`sha256_canonical` **33/33** = `git rev-parse HEAD:<path>`；`sha256_worktree` **31/33** = 本树字节，2 失配且声明值 = 同内容 CRLF 归一化摘要。
- 16 例必需字段齐（含 `applicability`，16/16 与 `expected_category` 不同）；`sealed` 全 false；双重归属 0；组双向一致 7/7；六族齐；三类 `expected_category` 齐；24/24/24 显式标为构建计划；最长描述 171 字符。
- 返工①②④⑤⑥⑦⑧ 的被引件关键串逐条命中（含 `offline_qualification.py:266` 逐字、registry `pr03_v3_result.notes`、finqa autopsy "not recomputed"、fe7b87fa/7406b3cf 两个 force-add 提交的实际路径）。
- v1 run 包保留未删；v2 `supersedes_run_id` 已记；v2 `prior_review` 三哈希前缀 = T1R-01 三件实算。
- 提交 `a8c036e84` 恰含 7 条路径，全部位于 v2 run 目录；无越界写入。
- v1 判「支撑」10 例在 v2 的断言未退化，抽验 6 例逐串仍成立。
- `reviews/T1R-02/` 现存 T-1 评审包（历史件），被 T1-INC-10 引用并钉哈希。

**INFERENCE（推断）**
- F9 成因最可能是：`sha256_worktree` 的 2 条取自含 CRLF 的作者侧副本或经 EOL 归一化后计算，而非本树 raw 字节。依据：声明值与 `sha256(LF→CRLF)` 逐位相等；其余 31 条与 9/9 input_bindings 均按本树 raw 命中；全仓无第二处记录该值。备选解释（执行者整树在 D: 侧作业）与其余 31 条按 Linux 树命中相冲突。
- F9 的严重度应低于 v1-F3：彼时唯一哈希字段（身份）失配 2/31；今身份域 33/33 正确且域已命名，仅次要快照字段混用表示域。但因 A-common 与复算项③明文且口径已由 T1R-01 必改③定死，仍判未通过。

**UNVERIFIED（本次无法验证）**
- 执行者自报 usage（model/network/remote/db/training/production = 0）无独立计量通道，只能做「无反证」检验（已做，未发现相反证据）；`execution_chat_token_usage` 双方均 `UNRESOLVED`，未冒报 0。
- D:/AIRcommend 作者侧树当时的实际字节（不在本机、禁联网）；故 `sha256_worktree` 若解释为「作者侧快照」则无法证伪——但该解释本身与字段无域标注、与其余 31 条按本树命中相矛盾，且复算项③已规定以本树为准。
- 任何模型端点 / 生产服务 / 数据库行为（约束内零调用；本地文档检查不代表 GB10 运行验证）。
- 27 条被引证据未逐行背对背全读；INC-01/02/05/14 采抽证（关键字段/提交对象/收据字段），其余按上文关键串逐条核对。
- 24/24/24 构建计划可行性、封存集构建（T2 范围，本评审不进入）。
- 「同源」判定标准未在卡内形式化；F6 的并组依据 ROUND1_CLOSEOUT 同文并列，收口者可复裁。

---

## 6. 判定与理由

**提案：REJECTED**（窄口径；仅提案）

理由：

1. **必改③只完成一半**：T1R-01 明文要求「全部 `source_refs[].sha256` **按本树重算**」，任务书复算项③同样要求「`sha256_worktree` 是否＝本树实算」。实测 2/33 不等于本树，且其值为 EOL 归一化摘要——不是本树字节。
2. **直接违反卡内自动验收断言 A-common「声明哈希实算一致」**：33 条声明的 worktree 哈希中 2 条无法用本树复算。T1R-01 已把「声明哈希失配」列为使提案定为 REJECTED 而非 PENDING 的决定性因素；同口径应保持一致。
3. **违反本包自证失败族的合法对照**：reliability_spec §6.2 证据身份族要求「明确命名并正确绑定的多种哈希域」；`sha256_worktree` 无域标注、混用两种表示域，且未在 E7/`unresolved` 披露。以自身存在证据身份缺陷的案例去标定「证据完整率 100%」「原始记录完整性 0」两道硬门，会形成轻度循环失真（比 v1 弱，但同构）。
4. **不 `PENDING_HUMAN_REVIEW` 的理由**：全部残余问题位于记录层（2 个摘要值、字段命名、E7 披露），不触及科学结论、冻结结论或授权边界；两条可选修法（按本树重算 / 补域标注并披露）都是机械动作，无需 owner 实体裁决。按 T0R-01 已立「记录层缺陷不升级人类门」口径，应 REJECTED。**唯一需要 owner/收口者另行处置的是 F10 落盘位置**，那属交接事项，不构成对 v2 产物的实体否决。
5. **不 `ACCEPTED` 的理由**：若接受，等于承认「A-common 对次要哈希字段不适用」——这是一条会外溢到后续所有 T 卡的口径松动，而口径本身已由 T1R-01 必改③写死。且 v2 修复成本极低（2 个摘要或 1 个域标注 + 1 处披露），不应以松动硬门换取一次省事。
6. **必须保留的正面结论**：T1R-01 的 5 必改 + 3 建议**全部落实**（③除 2 个 worktree 值外），事实追溯层 16/16 闭环，无编造、无错误归因、无过度陈述、无越界写入、无封存泄漏，「不动」清单原样成立。**包的骨架与事实层已达标，返工集只剩 F9 一条。**

**交办条件（供收口者执行）**
- **必改（1 条）**：修 F9 —— 将 `POSITIVE_REPAIR_REGISTRY_v1.json` 的 2 处 `sha256_worktree` 按权威树重算（或为该字段补显式域标注并把不可复算项写入 `unresolved`），同时在 E7 `observed` 报出 worktree 维度结果。
- **建议**：F11 字段改名（去掉误导性 `sha256_` 前缀）；可顺带补记 T1-INC-13 `legal_control_design` 的 fixture 细节。
- **交办收口者（非返工项）**：F10 —— 本复审件以**新 review_id** 落盘，勿覆盖 `reviews/T1R-02/*` 历史件（T1-INC-10 正引用其一）。
- **不动**：六族覆盖、三类 `expected_category`、24/24/24 构建计划标注、无封存标记、B0 申报、写入边界、以及本节所列全部已核实的返工成果——v3 微运行不得改动。
