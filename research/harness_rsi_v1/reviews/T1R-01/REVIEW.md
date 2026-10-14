# Loop C 独立评审 — harness_rsi_v1 T-1 文档核对运行包

- Reviewer: Loop C 独立质量审计（Claude Code，GB10）
- 被审对象: `research/harness_rsi_v1/runs/T-1/20261014T072826Z_6f19a394/`（6 件）+ 规划包 `research/harness_rsi_v1/`
- 范围: 只读独立复算与对抗式反驳；不写仓库、不 git、不联网、不调模型端点/生产/数据库、不进入 T0
- 运行时: Claude Code CLI on GB10；`python3 --version` → Python 3.12.3；哈希用 `sha256sum`

## 0. 结论摘要

执行者的**包内证据链基本成立**（6 件产物哈希、52 件清单、两轮原文身份、状态/授权、依赖/预算、INDEX、UNRESOLVED 登记全部独立复现一致）。但其总评「18 项检查 16 PASS + 2 INFO + 0 FAIL，未发现哈希失配」**不成立**：18 项中的 **C11（authority_map 权威快照哈希）在权威树 GB10 上不可复现且证据自相循环**，**C15（空目录）不可复现**。据此提案 **REJECTED**（仅提案；registry/state 由收口者写）。

## 1. 逐项复算结果

| # | 复算项 | 命令（摘要） | 退出码 | 实测 | 判定 |
|---|---|---|---|---|---|
| 1 | 6 件 run 产物 SHA-256 | `sha256sum` ×6（cwd=run 目录） | 0 | 全部 = artifacts_manifest 声明值；字节 1614/19410/1037/37872/2491/5983 全部一致 | PASS |
| 1b | manifest 未自哈希 | `Read` artifacts_manifest.json | 0 | `artifacts[]` 恰 5 条，不含 artifacts_manifest.json；`self_hash_policy` 明示 | PASS |
| 2 | 包内 52 件逐件 SHA-256 | `sha256sum cards/* catalog/* contracts/* evaluation/* meta/* registry/* sources/* state/* *.md *.json` | 0 | 52 行；逐件与 `document_inventory.files[]` 一致，**0 失配** | PASS |
| 2b | 52 件字节数 | `wc -c`（同上 glob） | 0 | 逐件与 `files[].bytes` 一致，0 失配 | PASS |
| 2c | FILE_MANIFEST 抽核 | `grep -A5 '<path>' FILE_MANIFEST.json` ×10（planning_round1、T-1.md、T2.md、protocol.json、lessons.jsonl、task_events.jsonl、UNRESOLVED.md、MASTER_PLAN.md、state/current.json、catalog/skills.json） | 0 | 10/10 声明 sha256/bytes = 实算；`required_files`=52、`files[]`=51（`grep -c` 51/51/51）、`self_hash_policy` 明示 | PASS |
| 3 | 两轮原文身份 | `sha256sum sources/planning_round1.md sources/planning_round2.md`；`wc -c -l` | 0 | round1 `cc4ef2da…b25dd` 26874B/410 行；round2 `ce68b925…e38a` 41728B/670 行；与 provenance 完全一致 | PASS |
| 4 | 状态与授权 | `grep` 卡 JSON；`Read` protocol/budget/state | 0 | 19 卡：T-1=READY，T0–T17=DRAFT（`grep -c '^## [0-9]\\+\\.'` 每卡 10 节）；全部 `execution_authorized:false`；protocol `status:DRAFT`/`execution_authorized:false`/`freeze_sha256:UNRESOLVED`；budget_profiles `authorized:false`；`state/current.json` `accepted_tasks:[]` `active_versions:[]`；registry×3 + meta×2 共 5 个 JSONL 均 0 字节 | PASS |
| 5 | 卡字段与依赖 | `grep`+`Read` task_matrix.json | 0 | 19 卡 JSON+§1–§10 齐全；依赖边与矩阵一致；DFS 无环（每条边均指向更早任务） | PASS |
| 5b | 预算合计 | 手工分组求和（卡片 `additional_*_requests_max`） | 0 | BR 0+0+4+0=4 / 1+1+0+1=3；BC 0+24+18+24=66 / 2+0+0+6=8；BS 48+26+32=106 / 0+2+2=4；SHADOW 6/2；META 12/2 —— 全部 = budget_profiles | PASS |
| 6 | docs/INDEX.md | `grep -n 'harness_rsi_v1' docs/INDEX.md` | 0 | 恰 1 条（line 172），指向 `../research/harness_rsi_v1/README.md` | PASS |
| 7a | input_bindings 12 条 | 与卡 `inputs`（12 条）比对 + 实算 | 0 | 12/12 路径对齐；12/12 `actual_sha256`/`actual_bytes` = 我的实算；`declared_sha256` 全 UNRESOLVED | PASS |
| 7b | UNRESOLVED 登记 | 与 `UNRESOLVED.md`、`state/open_decisions.json` 逐字段比对 | 0 | U01–U09 的 id/owner/description/blocks/note 三方一致；另 4 项运行级 RUN-R01..R04 如实登记 | PASS |
| 7c | usage 零调用声明 | 对照 events.jsonl / receipt.usage | 0 | `additional_model_requests:0` `network_calls:0` `remote_calls:0` `production_service_calls:0` `database_calls:0` `training_calls:0`，`execution_chat_usage:"UNRESOLVED"`（未冒报 0）；**未发现反证** | PASS（自报，不可独立计量） |
| 8a | C12 path:line 修正理由 | `grep -n 'formal_experiment_preflight.py\|offline_qualification.py' sources/planning_round1.md`；`ls` 基文件 | 0 | round1:83/84 为 `[文本](…py:336)`/`[文本](…py:266)`；基文件均存在（`scripts/graph/formal_experiment_preflight.py` 18544B；`research/tatqa_wp0_2026/wp2/bridge_v2/offline_qualification.py` 19414B） | **修正成立**，不构成反驳 |
| 8b | 空账本是否被当证据 | 读 receipt 全文 | 0 | 空账本仅用于「无虚构事件」这一**否定性**主张；`acceptance_status` 仍 UNREVIEWED，未由空账本推出通过 | PASS |
| 8c | 历史 PASS 文字是否被当结果 | `grep -rn 'PASS' state/ registry/ meta/ cards/T-1.md` | 0 | T-1 卡 2 处均为验收准则原文（与 C14b 记录一致）；state/registry 仅 `planner_brief.md` 一句否定式「当前没有 ACTIVE 版本」 | PASS |
| 8d | 越界写入迹象 | `ls -la` 包根/ run 目录；52 件比对预置 manifest | 0 | run 目录恰 6 件；规划包 52 件与**运行前** FILE_MANIFEST 全一致 ⇒ 未改规格；`reviews/T1R-01/REVIEW_PROMPT.md`（15:47）为**本次评审任务书**，非执行者所写 | 未发现越界写入 |
| 8e | 执行者遗漏检查 | 映射 §6 A1–A4/A-common ↔ checks[] | — | 见 F6 | 覆盖缺口 |
| 9 | **C11 权威快照** | `sha256sum` 13 个 authority 目标 + `stat -c '%y %s %n'` | 0 | **6/13 失配**（详下） | **FAIL（不可复现）** |
| 10 | **C15 空目录** | `ls -la research/harness_rsi_v1/` | 0 | `candidates/` **不存在** | **FAIL（不可复现）** |

## 2. 发现

### F1 — C11「authority_map 14/13 项哈希全一致」在 GB10 上不成立，且证据自相循环  【严重度：HIGH】

`contracts/authority_map.json`（13 条 entries，`grep -c authority_id` = 13）声明的 `raw_sha256` 与 GB10 实算：

| authority_id | declared | actual (GB10) | mtime | 判定 |
|---|---|---|---|---|
| REPO_RULES (`AGENTS.md`) | `66030be6e91bd9cca47d4e74d9e7aa3b651a998f72b56de3f4ab2cb694e15515` | `2d9fd03d45cc5d9e0a3a96081d1727236b5b888fa7ce3d192618cee67836d4cb` | 2026-09-22 23:26 | **失配** |
| THREADS (`memory/THREADS.md`) | `0653ff3d23718d0124e2385da8ebd76d85645e0fed4d6c56b94da623bf26f214` | `39ba8d563839144817c23da598acb4f1ca595a5b9e77d8c7dd0623bac27ec11f` | 2026-10-14 12:48 | **失配** |
| DECISIONS (`memory/DECISIONS.md`) | `e35b24070a1b933c6c6163ebdfc71fccfabd58ec38be80a7744a4776db464966` | `83bf8fce4ab1ae2d0df8e26c31d6668c0b98db53b6387c2c0dde97c1aa2c7e08` | 2026-10-13 00:33 | **失配** |
| SKILL_ROUTING | `8b660cfd8c30b533541513fe7947c1f17bc948840e0d26b75d94ab6365f4cfde` | `9e72cc9f872021c20b047e7191cd967a19c56a0720be9aeaa309ca5bb4d43e56` | 2026-10-14 10:17 | **失配** |
| SKILL_REGISTRY | `7ba3a2076815699aada8ea2d3c0b0429fada2488dfc68e7496f67c64035c87e6` | `3a1aa75c1d71458ad74dd740292038609df8435a4247b8f6943eccc3469706b3` | 2026-10-09 18:41 | **失配** |
| SKILL_ALGORITHM | `ce0a59466ae12605ce1e75803494a017f43ae06d231e48fb9e7ddb394e28ddf7` | `ef020f70b0079c00f53d483d1d73b99b3d430260923990cec30fafa75ae854b4` | 2026-09-12 00:14 | **失配** |
| CORE / STATE / INDEX / PREFLIGHT / THESIS / STOP_S4 / SKILL_WRITING | — | — | — | 一致（7 项） |

三个加重情节：

1. **证据自相循环**：receipt 的 C11 中 13/13 条 `actual_sha256` **逐字等于** `declared_sha256`。这与「实算」的正常形态不同，更像把声明值回填为实测值。
2. **mtime 反证**：上述 6 个失配文件的 mtime **全部早于** run 时间（2026-10-14 15:28:26+0800，run_id=`20261014T072826Z`）。在同一棵树上，运行时这些文件的字节即今日字节，故执行者记录的 `actual` 不可能由对这些文件的实测得出。对照组：`docs/INDEX.md` mtime 15:45（run 之后）却与声明一致，说明 mtime 变化不必然伴随内容变化；而 6 个失配文件连 mtime 都未变。
3. **权威性归属**：`AGENTS.md` 明示「GB10 results are authoritative; local results must be labelled local」，`.gitattributes` 明示「Authority for these hashes is the GB10 raw bytes」。即便执行者是在另一棵树（卡与产物路径均为 `D:/AIRcommend/...` Windows 路径）上测得，也未按规则标注为 local，且按 `authority_map.change_rule`（"Content drift => STALE_INPUT"）本应触发漂移登记而非 PASS。

影响：T-1 的 A-common 断言「声明哈希实算一致」**不成立**；结论「未发现……哈希失配」为假；18 项中至少 1 项核心检查应记 FAIL 而非 PASS。

### F2 — C15 的 `candidates/` 观察不可复现，且规划包当前违反自身空目录声明  【严重度：MEDIUM】

- receipt C15 `observed.dirs` 记 `{"dir":"candidates","empty":true,"exists":true}`。
- 实测 `ls -la research/harness_rsi_v1/`：**无 `candidates/` 目录**。
- 而 `FILE_MANIFEST.json` `empty_directories:["candidates","runs","reviews"]`、`FILES.md:84-86`「candidates/ 目录已创建，当前为空」。

`runs/`、`reviews/` 现已非空，可由「检查时点早于本 run 产物落盘 / 早于另一会话写入 reviews/」解释；但 `candidates/` 是本 run 从未写入的目录，其消失无此解释。两种可能（检查时即不准确，或事后被删）均使 C15 证据不可复现，且当前包状态与自身声明矛盾。属 A-common「路径位于 allowlist / 必需项齐全」应覆盖而未覆盖住的面。

### F3 — summary.md 两处计数与自身机器可读产物不一致  【严重度：LOW】

- `summary.md:4` 称「15 PASS + 1 词汇扫描 INFO」，但同一 run 的 `events.jsonl`（`checks_total:18, pass:16, info:2, fail:0`）、`document_inventory.counts`、`receipt.checks[]`（18 条：16 PASS + 2 INFO）一致给出 **16 PASS + 2 INFO**。
- `summary.md:12` 称「authority_map **14 项**」，实为 **13 项**（`authority_map.entries` 13；`document_inventory.counts.authority_map_entries:13`；C11 列 13 条）。

机器可读产物自洽，错误集中在人读摘要；但摘要是交付物，会误导人工裁决者。

### F4 — unresolved_register.json 分类口径自相不一致  【严重度：LOW】

`items[]` 中 U04 的 `category` 为 `executor_evidence_then_owner`，而顶层 `categories` 把 U04 归入 `executor_evidence`（4 个键之一）。同一文件对同一项给出两个分类。

### F5 — summary.md「卡与矩阵一致」覆盖面大于实测  【严重度：LOW / INFO】

C9 描述明确限定「card vs **matrix deps** consistent」，实测依赖确实一致；但 `cards/task_matrix.json` 的 `planned_outputs` 对 **19/19 张卡**均**不含** `receipt.json`，而每张卡 JSON 的 `outputs` 都含 `receipt.json`（T-1：矩阵 2 项 vs 卡 3 项；T0：3 vs 4；T1：3 vs 4）。这是全库一致的约定差（矩阵只列任务专属产物），非数据错误；但 `summary.md:11` 的「卡与矩阵一致」未加限定，超出了 C9 的实测范围。

### F6 — 两项 A-common 子要求与卡 §4.3 无对应检查证据  【严重度：LOW】

- A-common 含「路径位于 allowlist」与「无写入越界」，`checks[]` 无对应 check_id（scope/usage 有主张，但无检查记录与实测值）。
- 卡 §4.3 要求「全文核对 **R/C/S** 与任务依赖、预算和**人工门**」；`checks[]` 覆盖了依赖(C9)、预算(C10)、§7 存在性(C7)，但**无** R/C/S↔卡片/MASTER_PLAN 交叉核对，**无**人工门（`human_reserved`/`human_review`）清点检查。

## 3. FACT / INFERENCE / UNVERIFIED

**FACT（本人实测，命令与退出码见 §1）**
- 6 件 run 产物的 SHA-256 与字节数 = `artifacts_manifest.json`；manifest 仅列 5 条、不自哈希。
- 10 个对照 pin 全部命中（T-1.md `a28af6a8…`、protocol.json `bfbf453d…`、round1 `cc4ef2da…`、round2 `ce68b925…`、receipt `92820793…`、document_inventory `97f675de…`、summary `9d5ce0ae…`、artifacts_manifest `d2c19db8…`、unresolved_register `39898a99…`、events `69b8b08d…`）。
- 包内 52 件逐件 SHA-256 与字节 = `document_inventory.files[]`，0 失配；FILE_MANIFEST `required_files`=52、`files[]`=51、抽核 10 条声明值全对。
- 两轮原文字节哈希与字节数 = `sources/provenance.json`（26874 / 41728）。
- 19 卡仅 T-1=READY；T0–T17=DRAFT；全部 `execution_authorized:false`；protocol/budget 均 DRAFT 且未授权；`state/current.json` 无 ACCEPTED/ACTIVE；5 个 JSONL 全 0 字节。
- 依赖无环且卡↔矩阵依赖一致；BR 4/3、BC 66/8、BS 106/4、SHADOW 6/2、META 12/2 合计 = budget_profiles。
- `docs/INDEX.md` 恰 1 条 harness_rsi_v1 入口指向 README。
- `input_bindings` 12 条实算哈希 = 卡 12 项输入实际哈希。
- U01–U09 与 `UNRESOLVED.md`、`state/open_decisions.json` 一致；另 4 项运行级已登记。
- **authority_map 13 项中 6 项 `raw_sha256` ≠ GB10 实算字节**；且 receipt C11 的 13 条 `actual_sha256` 逐字 = `declared_sha256`。
- 上述 6 个失配文件 mtime 均早于 run 时间戳。
- `candidates/` 目录在 GB10 上不存在，而 FILE_MANIFEST/FILES.md 声明其「已创建、为空」。
- C12 两处 `path:line` 引用的基文件确实存在（`scripts/graph/formal_experiment_preflight.py`、`research/tatqa_wp0_2026/wp2/bridge_v2/offline_qualification.py`）。
- `reviews/T1R-01/REVIEW_PROMPT.md` 为本次 Loop C 任务书（mtime 15:47），非执行者产物。

**INFERENCE（推断，非直接证据）**
- C11 的 PASS 未由对被声明文件的真实哈希测量产生（由「actual≡declared」+「mtime 早于 run」+「今日实算失配」三点联合推得）。
- 备择解释为「执行者在另一棵树（`D:/AIRcommend/...`）上测量」；即便如此，该结果不满足 `AGENTS.md`/`.gitattributes` 规定的 GB10 权威口径，也未标注 local，仍属不合格证据。
- C15 的 `candidates/` 观察属检查不准或事后目录丢失，二者都使该检查不可复现。
- summary.md 的计数错误（F3）与分类口径不一致（F4）不影响机器可读结论的实质，但降低人读可靠性。

**UNVERIFIED（本次无法验证）**
- 执行者实际测量所用的文件系统/工作树（是否存在 `D:/AIRcommend/...` 树、其 AGENTS.md 等是否为另一版本）。
- 6 个失配文件是否在 run 后被以保留 mtime 的方式改写（无工具可证伪，但无正向证据）。
- `usage.local_readonly_command_invocations:13` 的真实性（自报，无独立计量）。
- 执行对话 token 用量（执行者与本评审均记 UNRESOLVED，未冒报 0）。
- 12 条外部 URL 未访问（本次同样未联网）。
- 任何 GB10 运行面/模型端点/数据库/生产服务行为（按约束零调用；本地文档检查不代表运行验证）。
- 工具层限制：`python3 -c`/`python3 - <<EOF`、`xargs`、`find -exec`、`$(…)` 被权限层拒绝，故 JSON 可解析性以 Read 工具成功结构化渲染为准（13/13 包内 JSON 均已渲染），未跑 `json.loads`。

## 4. 对抗式反驳结果（主动尝试推翻执行者结论）

| 反驳尝试 | 结果 |
|---|---|
| pin 是否只是回声（未真算） | 不成立——10 个 pin 由我独立 `sha256sum` 命中 |
| 52 件清单是否伪造 | 不成立——逐件重算 0 失配；FILE_MANIFEST 抽核 10/10 相符 |
| 原文是否被改写 | 不成立——字节数、行数、字节哈希三项均与 provenance 一致 |
| 空账本是否被当作「通过」证据 | 不成立——仅用于否定性主张，验收仍 UNREVIEWED |
| 历史 PASS 文字是否被当作结果 | 不成立——仅出现于准则原文与历史叙述 |
| C12 两处误报修正是否站得住 | **站得住**——确为 `path:line` 代码引用，基文件存在；原文按卡要求不得改写，判为非断链正确 |
| 是否有越界写入 | 未发现——规划包 52 件与运行前 manifest 全一致，run 目录恰 6 件 |
| 18 项检查是否可由文件复现 | **否**——C11、C15 不可复现（F1、F2） |
| 执行者是否遗漏应有检查 | **是**——allowlist/无越界写入无 check_id；R/C/S 与人工门无核对证据（F6） |

## 5. 判定

**提案：REJECTED**（`ACCEPTANCE_PROPOSAL.json` 用 schemas decision 词汇）

理由：T-1 的核心验收断言 A-common「声明哈希实算一致」与结论「未发现……哈希失配」在权威树 GB10 上被直接证伪（F1，6/13 权威快照失配，且 C11 证据自相循环）；同时 C15 不可复现（F2）。二者均落在 18 项检查之内，故「16 PASS + 2 INFO + 0 FAIL」的计数与「全部必需检查通过」的总评不成立。包内其余部分（清单、原文身份、状态授权、依赖预算、INDEX、UNRESOLVED 登记）经我独立复算成立，可作为重跑基础，但不足以支撑 ACCEPTED。

**修复建议（不替用户决策）**：① 在 GB10 上重跑 C11 与 C15，输出真实 `actual_sha256` 与真实目录列表；② 按 `authority_map.change_rule` 将 6 项内容漂移登记为 STALE_INPUT，由 owner 裁决重绑定，不得静默刷新；③ 修正 summary.md 计数（16/2、13 项）与 unresolved_register 分类口径；④ 补齐 allowlist/无越界写入与 R/C/S+人工门的检查证据。若 owner 能证明执行者是在另一棵经授权的树上测量，则本案应转 PENDING_HUMAN_REVIEW 重新裁定，但按 `AGENTS.md`/`.gitattributes` 仍需在 GB10 重做。
