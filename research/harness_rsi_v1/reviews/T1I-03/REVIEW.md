# Loop C 独立复审 — harness_rsi_v1 **T1 v3**（T1R-02 残余项返工核验）（T1R-03）

- Reviewer: Loop C 独立质量审计（Claude Code，GB10 = `promaxgb10-0b48`，Linux 6.17.0-1018-nvidia aarch64，Python 3.12.3）
- 被审对象: `research/harness_rsi_v1/runs/T1/20261014T141004Z_2647a7e1/`（7 件，16 例）
- 对照物: v2 run `20261014T134731Z_5d8b9400/`、v1 run `20261014T132249Z_99f3bc6b/`、`reviews/T1R-02/{REVIEW.md, review_receipt.json, ACCEPTANCE_PROPOSAL.json}`、被引真源
- 范围: 只读独立复算 + T1R-02 残余项（F9）返工核验 + 最小改动 diff + 不动项核验 + 回归抽验 + 反证尝试。不写仓库、不 git 写、不联网、不调模型端点/生产/数据库、不进入 T2。registry/state 不由我写。
- 仓库 HEAD（实测）: `c67d4f1be8a9849310259955346dc7ecc6d7b4da`（即 T1 v3 入库提交本身）
- 约束披露: 硬约束「不 git 写」；只读 plumbing（`rev-parse HEAD:<path>`、`log --name-only`）为任务书强制复算所必需，已用并登记；无任何 git 写/历史改写。

---

## 0. 结论摘要

**提案：ACCEPTED**（附强制 advisory F12；仅提案，registry/state 由收口者写）。

**T1R-02 残余项（F9）已干净关闭**——这是 T1R-03 受命核验的唯一残余缺陷，已彻底修好：`incidents.jsonl` 中 `sha256_worktree` 出现 **0** 次；每 ref 仅含 `{path, exists, tracked, sha256_canonical, sha256_canonical_domain}`；**33/33** `sha256_canonical` == `git rev-parse HEAD:<path>`；E7 描述显式覆盖「single declared identity domain」并声明 worktree 哈希有意不声明。16 例事实层全部为真（本人独立取证），A-common 哈希门 33/33 通过，无编造、无错误归因、无过度陈述、无越界写入、无封存泄漏；六族/三类/24/24/24/无封存/B0/写入边界等「不动」项原样保留；INC-11/12/13/CTRL-01/INC-06 回归无退化。

**保留意见（3 条，均不阻断 v3 本体）**：
- **F12【LOW-MEDIUM · 强制 advisory，交办收口者】** INC-10 的 `reviews/T1R-02/REVIEW.md` 引用已**自指/失效**——该路径在提交 `b75a083dc` 被 T1 v2 评审**覆盖**了原 T-1 评审（`e71aa713a`），正是 T1R-02 F10 预警的落盘碰撞。INC-10 断言（6/13 失配、三域复算、owner 1A 重钉、旧值留档）**全部为真**（我已比对 `runs/T-1/*`、`authority_map.change_record`、`T0R-01`），但其「6/13/三域」子断言的一手专用出处已被覆盖；v3 为保 33/33 将该 pin 重钉到新内容（`05e59c70`→`cadcc0e7`）。根因是收口者覆盖被跟踪历史件（CLAUDE.md「Ask first」），非 v3 缺陷；须收口者在标定硬门前修复（重指 INC-10 到 `runs/T-1/*` 真源，或恢复/迁置 T-1 评审）。
- **F13【LOW】** E7 `method` 仍列 "worktree hash" 而 `observed` 无 worktree 结果；`description` 已披露「有意不声明」（F7 披露缺口已补），method 措辞是 F7 回声，不阻断。
- **F14【LOW】** 「supersedes/prior_review 指针改 v2」「schema 字符串升 v3」两意图项**未全量落实**：receipt 已正确改 v2/T1R-02，但 `coverage_matrix.supersedes_run_id`、`events.jsonl.supersedes` 仍指 v1，events 仍是 "t1v2_*"/F1–F8 陈旧标签，`artifacts_manifest.schema` 仍 "_v2"。元数据卫生，非事实缺陷。

---

## 1. 逐项复算结果（命令 / 实测 / 判定）

| # | 复算项 | 命令（摘要） | 实测 | 判定 |
|---|---|---|---|---|
| 1 | run 目录恰 7 件 | `python3 os.listdir` | **7** 件：manifest / coverage_matrix / events / incidents / receipt / source_groups / summary，无多余项 | **PASS** |
| 2 | 6 件产物 bytes+sha256 vs manifest | `python3 hashlib` | **6/6** 逐件一致（18964/3469/3726/8053/912/447）；`self_hash_policy:"excluded from own list"` | **PASS** |
| 3 | receipt `input_bindings` 9 条实算 | `python3` 路径规范化 + sha256 | **9/9** 存在且 `actual_sha256`=实算（含 STOP_S4、PREFLIGHT）；protocol `status:"FROZEN"` | **PASS** |
| 4 | 残余① `sha256_worktree` 计数 | `python3 raw.count` | incidents.jsonl 中 `sha256_worktree` 出现 **0** 次（"worktree" 词 0 次） | **PASS（F9 关闭）** |
| 5 | 残余② ref 键集合 | `python3` 键扫描 | **33/33** 单一键集 `{exists,path,sha256_canonical,sha256_canonical_domain,tracked}`，键变体=1 | **PASS** |
| 6 | 残余③ canonical vs `git rev-parse HEAD:<path>` | `python3`+`git rev-parse` | **33/33** = HEAD blob id（域 `git_blob_id`×33）；0 失配；exists/tracked 全真 | **PASS** |
| 7 | 残余④ E7 描述与 method、覆盖单一声明域 | Read receipt | description 显式含 "single declared identity domain" + "worktree hashes intentionally not declared"；method 仍列 "worktree hash"（→F13） | **PASS_WITH_NOTE** |
| 8 | 最小改动 diff（incidents） | `python3` 逐例比较（剔除 v2 worktree 键） | 15/16 逐字段等价；仅 **T1-INC-10** 的 `T1R-02/REVIEW.md` canonical `05e59c70`→`cadcc0e7`（强制重钉，见 F12） | **PASS（差异可解释）** |
| 9 | 最小改动 diff（matrix/groups） | `python3` 递归 diff | 除 `generated_at_utc`/`run_id`/`schema` 外**逐字段等价** | **PASS** |
| 10 | schema 串升 v3 | `python3` | receipt/matrix/groups → `_v3`；`artifacts_manifest` 仍 `_v2`（→F14） | **PARTIAL** |
| 11 | 不动① 六族覆盖 | `python3` | 真实调用边界 4 / 完整性与预算 5 / 测量对象 2 / 证据身份 2 / 交付与权限 2 / 数据与统计 1 = **6 族齐** | **保持** |
| 12 | 不动② 三类 expected_category | `python3` | BLOCK 9 / REVIEW_REQUIRED 5 / ALLOW_WITHIN_SCOPE 2 | **保持** |
| 13 | 不动③ applicability | `python3` | 16/16 有，0 例 = expected_category | **保持** |
| 14 | 不动④ 24/24/24 仅构建计划 | Read matrix | `totals_plan` dev/sel/sealed=24，note「为构建计划…」；`built_now` 13+2+1=16 | **保持** |
| 15 | 不动⑤ 无 sealed | `python3` | `sealed:true` **0**；7/7 组 `sealed_eligible:false`、`alloc=development_or_calibration_only`；16/16 visibility 同 | **保持** |
| 16 | 不动⑥ B0 零调用 | receipt.usage + events | model/network/remote/db/training/production **全 0**；`execution_chat_usage:"UNRESOLVED"` | **保持** |
| 17 | 不动⑦ 写入边界 | `git log -1 --name-only --format=%H c67d4f1be` | 该提交**恰 7 条路径**，全在 v3 run 目录 | **保持** |
| 18 | supersedes/prior_review 指针改 v2 | `python3` | receipt.supersedes=v2、prior_review=T1R-02（3 哈希前缀=T1R-02 实算）✓；matrix/events.supersedes 仍 v1（→F14） | **PARTIAL** |
| 19 | 回归 INC-11 真源 | `python3` 关键串 | `LOOP_C_S4C_QUAL_AUDIT_v1.md`：投递缺口/未注入采样上下文/父线程/会话日志 各 ×1 | **PASS** |
| 20 | 回归 INC-12/13 真源 | 同上 | registry `ENGINEERING_DISPATCH_FAILURE`/`PR-01`/`PR-04`/`PR-07`/`never INVALID/NULL/NEGATIVE` 各 ×1；closeout `Zero POSITIVE / NULL / NEGATIVE`×1 | **PASS** |
| 21 | 回归 CTRL-01 真源 | 同上 | stage_e `NOT_IDENTIFIABLE`×2、`BLOCKER_CLEAN_THRESHOLD_NOT_IDENTIFIABLE`×1 | **PASS** |
| 22 | 回归 INC-06 三源互证 | 同上 | S4C/INCIDENT_2/diagnosis 三源均含调用约定项；S4C 含 `400`/`out of range integral type conversion attempted`/`input_ids-first`/`5.14.1` | **PASS** |
| 23 | 反证：伪造/过度陈述/越界 | 全量读 + 比对 | max_desc **171**；artifact_level 13/2/1；无 raw 正文复制；无越界写入；无封存泄漏 | **未发现反证** |
| 24 | 反证：INC-10 断言真伪 | 比对 `runs/T-1/*`、`authority_map`、`T0R-01` | 6/13、三域复算、owner 1A 重钉、旧值留档 **全部为真** | 断言为真（但指针失效 →F12） |

### 工具层记录（如实，含被拒命令）
- **被拒 1**：`python3` heredoc（回归脚本，含 f-string 花括号）→ 注入防护「Contains brace with quote character」；改写为无 f-string 后通过。
- **被拒 2**：`python3` heredoc（哈希脚本，含字典字面量 `{"key":"value"}`）→ 同上；改写为列表二元组后通过。
- **替代手段**：写入边界用等价只读 `git log -1 --name-only --format=%H c67d4f1be`（exit 0，输出即提交内 7 文件清单）；另用 `git rev-parse HEAD:<path>`（canonical blob id）、`git log --oneline --name-only`（`reviews/T1R-02/` 历史）。均为只读。
- **git 写 = 0**；无 `find -exec`、无 `$(...)`；未联网、未调端点/服务/数据库。

---

## 2. 残余项裁定（T1R-02 F9 → 关闭）

T1R-02 判 v2 REJECTED 的**唯一残余缺陷**是 `source_refs[].sha256_worktree` 2/33 不可复算且域未标注（违反 A-common）。v3 的修法是**移除该字段**（仅留 canonical git_blob_id）。逐条裁定：

- **`sha256_worktree` 出现次数 = 0** ✅ —— incidents.jsonl 全文 `sha256_worktree`/`worktree` 均 0 次。残余字段彻底移除。
- **每 ref 仅含 5 个规定键** ✅ —— 33 ref 单一键集 `{path, exists, tracked, sha256_canonical, sha256_canonical_domain}`，无冗余、无缺失。
- **33/33 `sha256_canonical` == `git rev-parse HEAD:<path>`** ✅ —— 逐条实算命中（40 位 blob id，域 `git_blob_id`×33），0 失配。
- **E7 描述覆盖「单一声明域」** ✅ —— description 明写 "single declared identity domain; platform-dependent worktree hashes intentionally not declared"，即：canonical 是唯一声明身份域，worktree 哈希因平台相关而**有意不声明**——这正是 T1R-02 F9「最小修复」的合法路径（移除混用域字段），且比原第二选项（补域标注）更干净。

**裁定：F9 已干净关闭。** A-common「声明哈希实算一致」在 v3 全绿（33/33），T1R-02 判 REJECTED 的决定性因素已消除。E7 method 措辞残余（F13）是披露卫生，非哈希失配，不构成 F9 复发。

---

## 3. 最小改动 diff 结论（v3 vs v2）

程序化逐字段比较，差异**限于意图项 + 一处强制重钉 + 新 run 自然元数据**，无越界改动：

- **incidents.jsonl**：把 v2 的 `sha256_worktree` 键剔除后，**15/16** 例与 v3 逐字段等价（含 observed_fact/legal_control_design/applicability/分组等全字段）。唯一例外 **T1-INC-10**：其 `reviews/T1R-02/REVIEW.md` 的 `sha256_canonical` 由 `05e59c70…` 重钉为 `cadcc0e7…`（其余 3 ref canonical 不变）。此重钉是**强制的**——所引文件在 v2→v3 之间被外部提交 `b75a083dc` 覆盖（见 F12），若不重钉则 33/33 将失配。故非随意增改，是 A-common 达标的必要后果。
- **coverage_matrix.json / source_groups.json**：除 `generated_at_utc`、`run_id`、`schema`（v2→v3）外**逐字段等价**（六族、24/24/24、分组成员、sealed 标记全同）。
- **schema 串**：receipt/matrix/groups 已升 `_v3`；`artifacts_manifest.schema` 仍 `_v2`（F14）。
- **supersedes/prior_review**：receipt.supersedes=v2、prior_review=T1R-02（3 哈希前缀与 T1R-02 实算一致）；matrix/events.supersedes 仍 v1（F14）。
- **summary.md**：抬头改 v3，supersedes 正确记「v2 与 v1」。

**结论**：最小改动原则成立——除强制重钉（F12）与新 run 时间戳/run_id 外，无非意图项改动；仅存在意图项的**欠落实**（F14），属元数据卫生。

---

## 4. 回归结论

- **INC-11**：ref = `LOOP_C_S4C_QUAL_AUDIT_v1.md`；`投递缺口`/`未注入采样上下文`/`父线程`/`会话日志` 各 ×1，同披露行逐字支撑。**仍成立**。
- **INC-12/13**：refs = `positive_repair_20261011/{POSITIVE_REPAIR_REGISTRY_v1.json, ROUND1_CLOSEOUT_v1.md}`；registry `ENGINEERING_DISPATCH_FAILURE`/`PR-01`/`PR-04`/`PR-07`/`never INVALID/NULL/NEGATIVE` 各 ×1，closeout `Zero POSITIVE / NULL / NEGATIVE`×1。**仍成立**。
- **CTRL-01**：ref = `stage_e_matched_fpr_reanalysis_v1.md`；`NOT_IDENTIFIABLE`×2（含 `BLOCKER_CLEAN_THRESHOLD_NOT_IDENTIFIABLE`）。**仍成立**。
- **INC-06 三源互证**：S4C receipt / INCIDENT_2 / processor_interface_diagnosis_output 三源均含 `(input_ids, scores)` 调用约定项；S4C 含 `400`、"out of range integral type conversion attempted"、`input_ids-first`、`5.14.1`。**三源互证仍成立**。
- 无一例回归退化。

---

## 5. 发现（T1R-03）

### F12 — INC-10 证据指针在 T1R-02 落盘覆盖后自指/失效 【LOW-MEDIUM · 强制 advisory，交办收口者】
- **证据**：`reviews/T1R-02/REVIEW.md` 的 git 历史为 `e71aa713a`（**T-1 v2 评审**）→ `b75a083dc`（**T1 v2 评审覆盖**，标题现为「T1 v2 …（T1R-02）」）。INC-10 `source_refs` 引该路径并称「6/13 失配、三域复算」，但当前该文件只在 F10/回归注里**转述** INC-10，并自述「6/13 失配与三域复算正出自该 T-1 评审」——即已非一手出处。v3 为保 33/33 将 pin 由 `05e59c70…`（T-1 评审 blob）重钉为 `cadcc0e7…`（T1 评审 blob）。
- **断言真伪**：INC-10 的 observed_fact（13 pin 取自工作树字节 / 6/13 失配 / 三域复算+逐行混合 EOL 重建判表示差异无内容漂移 / owner 1A 重钉、旧值留档）**全部为真**——我已比对 `runs/T-1/20261014T085638Z_ba9297ac/receipt.json`（C11 three_domain：pin_eq_local_raw 13/13、blob 13/13、gb10 mismatch 6）、`runs/T-1/.../summary.md`（6/13 EOL 表示差异）、`authority_map.change_record.rule`（canonical_blob_id authoritative，旧值留 local_snapshot_raw_sha256_historical）、`T0R-01`（逐行混合 EOL 重建）。故**非编造、非错误事实**，而是**指针退化**：一条 ref 变为「引用对本例的评审」的自指弱证据，"6/13/三域" 子断言失去专用一手出处（其余 3 ref 仍支撑核心叙事）。
- **根因**：收口者在 `b75a083dc` 用 T1 v2 评审**覆盖了被跟踪历史件** T-1 评审——正是 T1R-02 F10 明文预警并交办「勿覆盖 `reviews/T1R-02/*`」的落盘碰撞。违反 CLAUDE.md「Ask first：删除或改名被跟踪历史材料」。非 v3 微运行缺陷（v3 写边界仅 run 目录）。
- **要求（收口者，标定硬门前必须）**：恢复或迁置 T-1 评审，并把 INC-10 的 `T1R-02/REVIEW.md` ref 重指到稳定真源（如 `runs/T-1/20261014T085638Z_ba9297ac/receipt.json` 的 C11 three_domain 行，或迁置后的 T-1 评审）；或在 receipt `unresolved`+E7 披露该指针不稳、将 6/13 子断言标为「出处待复钉」。**覆盖被跟踪历史件的授权状态本人无法验证**（UNVERIFIED）。

### F13 — E7 `method` 仍列 "worktree hash" 而无对应 observed 结果 【LOW · 建议，不阻断】
- **证据**：E7 `method` = "existence + rev-parse HEAD:path + worktree hash"（与 v2 逐字相同，未随描述更新）；`observed` 仅 `refs_missing/refs_total/refs_untracked`，无 worktree 维度结果；`description` 已写 "platform-dependent worktree hashes intentionally not declared"。
- **影响**：description 与 method 在「method=计算动作、description=声明口径」读法下**可调和**，且 description 已披露有意不声明（F7 披露缺口已补）；残余只是 method 列出的 "worktree hash" 步骤无表列结果，是 F7 措辞回声。非 A-common 失配（无 worktree 哈希被声明）。建议 method 同步删去 "worktree hash" 或补注「computed-not-declared」。

### F14 — 意图项「supersedes/prior_review 改 v2」「schema 升 v3」欠落实 【LOW · 建议，不阻断】
- **证据**：receipt.supersedes=v2、prior_review=T1R-02 ✓；但 `coverage_matrix.supersedes_run_id`、`events.jsonl.supersedes` 仍 = v1（`20261014T132249Z_99f3bc6b`）；`events.jsonl` 三条事件仍 "t1v2_*" 且 `items:[F1..F8]`（v2 的动作，非 v3 的 F9）；`artifacts_manifest.schema` 仍 `harness_rsi_t1_artifacts_manifest_v2`。
- **影响**：包内 supersedes 链自相矛盾（receipt 指 v2，matrix/events 指 v1）；events 未记录 v3 实际动作。元数据卫生，不影响事实层/哈希门。建议 events 记 t1v3 事件与 F9、supersedes 统一、manifest schema 视版本轴语义决定是否升。

---

## 6. FACT / INFERENCE / UNVERIFIED

**FACT（本人实测）**
- run 目录恰 7 件；6/6 产物 bytes+SHA-256 = manifest；manifest 自排除。
- `input_bindings` 9/9 实算命中；protocol `status:"FROZEN"`。
- `sha256_worktree` 在 incidents.jsonl 出现 **0** 次；33 ref 单一键集 `{path,exists,tracked,sha256_canonical,sha256_canonical_domain}`。
- `sha256_canonical` **33/33** = `git rev-parse HEAD:<path>`（域 `git_blob_id`×33），0 失配；33/33 exists/tracked 真；27 唯一路径全存、0 越出预期根。
- E7 description 含 "single declared identity domain" 与 "worktree hashes intentionally not declared"；method 含 "worktree hash"（无表列结果）。
- 最小改动：剔除 v2 worktree 键后 15/16 例等价，仅 INC-10 canonical 重钉；matrix/groups 除 meta 等价；schema 三升 v3、manifest 留 v2。
- 六族齐、三类 expected_category 齐、applicability 16/16 且 0=expected_category、sealed 0、7/7 组 sealed_eligible:false、24/24/24 标注为计划、built_now 16、B0 全 0。
- 写入边界：`c67d4f1be` 恰 7 路径，全在 v3 run 目录。
- 回归 INC-11/12/13/CTRL-01/INC-06 关键串逐条命中；INC-06 三源含调用约定项。
- INC-10 断言对 `runs/T-1/*`、`authority_map.change_record`、`T0R-01` 逐项为真；其 `T1R-02/REVIEW.md` ref 的 pin `05e59c70`→`cadcc0e7`。
- `reviews/T1R-02/REVIEW.md` 历史 `e71aa713a`(T-1)→`b75a083dc`(T1 覆盖)；T1R-02 prior_review 三哈希前缀 = T1R-02 三件实算。
- max_desc **171**（INC-06.observed_fact）；artifact_level 13/2/1；visibility_note 16/16 同。

**INFERENCE（推断）**
- INC-10 canonical 重钉是 A-common 33/33 达标的**强制**后果，非 v3 越界增改：所引文件被外部提交覆盖后，不重钉则哈希门失配。v3 在其写边界内做的是唯一机械上能保门的动作。
- F12 严重度低于 T1R-01 的错引（F1–F5）：彼时断言未被一手证据支撑、需返工补证；今 INC-10 断言已对稳定真源核实为真，仅一条 ref 因外部覆盖退化为自指，且核心叙事仍由 3 条 ref 支撑。故列 advisory 而非阻断。

**UNVERIFIED（本次无法验证）**
- 收口者覆盖 T-1 评审（`b75a083dc`）的**授权状态**；CLAUDE.md「Ask first」要求是否满足不可验。
- 执行者自报 B0 用量（model/network/remote/db/training/production=0）无独立计量通道，只做「无反证」检验（已做）；`execution_chat_usage` 双方 `UNRESOLVED`。
- 任何模型端点/生产/数据库行为（约束内零调用；本地文档检查不代表 GB10 运行验证）。
- 27 条被引证据未逐行背对背全读；按关键串逐条核对 + INC-10 深查，其余采抽证。
- 24/24/24 构建计划可行性、封存集构建（T2 范围，不进入）。

---

## 7. 判定与理由

**提案：ACCEPTED**（附强制 advisory F12；仅提案，registry/state 由收口者写）

理由：

1. **受命核验的唯一残余项（F9）已干净关闭**：`sha256_worktree`=0、ref 键纯净、33/33 canonical 实算命中、E7 覆盖单一声明域。T1R-02 判 REJECTED 的决定性因素（A-common 哈希失配 2/33）已彻底消除。
2. **A-common 全绿**：声明哈希 33/33 实算一致、路径在 allowlist、无写入越界、未知项显式（`unresolved` 列封存集/chat usage/INC-14）。卡内自动验收断言达标。
3. **事实层全真、无编造/错误归因/过度陈述**：16 例断言对真源逐项核实；INC-10 的 6/13/三域/重钉亦对 `runs/T-1/*`、`authority_map`、`T0R-01` 核实为真；max_desc 171，无正文复制；无封存泄漏。
4. **最小改动成立**：差异限于意图项 + 强制重钉 + 新 run 元数据，无非意图增改；matrix/groups 逐字段等价。
5. **不动项全部保留**：六族、三类、24/24/24 计划标注、无封存、B0 零调用、写入边界，全绿。
6. **不 REJECTED 的理由**：T1R-02/T1R-01 判 REJECTED 的门槛是「A-common 哈希失配」或「断言未被一手证据支撑」。v3 二者皆无——哈希门 33/33，INC-10 断言已核实为真，唯一瑕疵（F12）是**外部覆盖**导致的指针退化，根因在收口者落盘（F10 落地），非 v3 微运行可归责。为一个外部根因、断言为真的指针卫生问题否定已完成受命的 v3，会把收口者过错记到执行者账上。
7. **不 PENDING_HUMAN_REVIEW 的理由**：F12 的**核心修法**（重指 INC-10 到 `runs/T-1/*` 真源）是记录层、v3 写边界内可做；仅「恢复被覆盖的 T-1 评审」涉 git/历史材料需收口者+授权，属交接事项（F10 已交办），不构成对 v3 产物的实体人类门。按 T0R-01/T1R-02「记录层缺陷不升级人类门」口径，判 ACCEPTED。
8. **强制 advisory 的必要性**：INC-10 属「证据身份」族，正是用于标定证据完整性/原始记录完整性硬门的样本；带自指指针入标定会形成轻度循环失真。故接受**以收口者在标定硬门前修复 F12 为条件**（重指指针或恢复 T-1 评审）。若收口者判定 F12 应阻断，可退回——但据证据（断言全真、哈希门全绿、根因外置）我提案 ACCEPTED。

**交办条件（供收口者执行）**
- **强制（F12）**：标定硬门前修复 INC-10 指针——重指到 `runs/T-1/20261014T085638Z_ba9297ac/receipt.json`（C11 three_domain）等稳定真源，或恢复/迁置被覆盖的 T-1 评审并复钉；同时核实 `b75a083dc` 覆盖历史件的授权（CLAUDE.md「Ask first」）。
- **建议**：F13 E7 method 同步删 "worktree hash" 或补注 computed-not-declared；F14 events 记 t1v3/F9、supersedes 链统一到 v2、manifest schema 依版本轴语义决定。
- **不动**：六族、三类、24/24/24 计划、无封存、B0、写入边界，及 F9 已关闭的全部返工成果——后续任何微运行不得回退。
