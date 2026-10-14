# Loop C 独立评审 — harness_rsi_v1 **T1** 事故案例整理包（T1R-01）

- Reviewer: Loop C 独立质量审计（Claude Code，GB10 = `promaxgb10-0b48`，Linux 6.17.0-1018-nvidia aarch64，Python 3.12.3）
- 被审对象: `research/harness_rsi_v1/runs/T1/20261014T132249Z_99f3bc6b/`（7 件）
- 范围: 只读独立复算 + **逐条事实核对 16 例**；不写仓库、不 git 写、不联网、不调模型端点/生产/数据库、不进入 T2。registry/state 不由我写。
- 仓库 HEAD（实测）: `87027f084f2a3664d9cb7c1eebae3ebf8f51338c`

---

## 0. 结论摘要

**提案：REJECTED**（仅提案；registry/state 由收口者写）。

包的**完整性与结构层全部独立复算成立**：7 件产物字节/SHA-256 逐件命中 manifest、run 目录恰 7 件、manifest 不自哈希、9/9 输入绑定实算一致、16 例字段齐、无双重归属、无封存标记、24/24/24 明确标为构建计划、B0 零调用、写入边界干净。

但本卡的**首要职责是「可追溯缺陷」案例事实核对**，而事实追溯层在 **16 例中 5 例不成立**，另有 **2 处 source_ref 哈希失配**（直接违反 A-common「声明哈希实算一致」）：

1. **T1-INC-11 引用完全错误归因**——所述 harness 投递缺口为真，但记录在 `research/tatqa_wp0_2026/wp2/LOOP_C_S4C_QUAL_AUDIT_v1.md`；被引的 `reviews/T1R-01/REVIEW.md` 对该事实 **0 命中**。
2. **T1-INC-12 / T1-INC-13 / T1-CTRL-01 为 ledger-only 引用**——事实为真，真源分别是 `research/positive_repair_20261011/{POSITIVE_REPAIR_REGISTRY_v1.json, ROUND1_CLOSEOUT_v1.md}` 与 `docs/research/stage_e_matched_fpr_reanalysis_v1.md`，而被引的 STATE/THREADS/INDEX 不含任何被断言的关键串。
3. **`memory/THREADS.md` 的 source_ref sha256 失配**——声明 `0653ff3d…`，本工作树与 `git cat-file blob HEAD:` **均为 `39ba8d56…`**；声明值等于 `authority_map.local_snapshot_raw_sha256_historical`（显式标注为历史域）。
4. **T1-INC-13 丢掉「第一轮」限定**，而其被引的 STATE.md 反而记录 PR-03 **v3** `effect measurement entered` = `NEGATIVE`。

**未发现任何编造**：我逐条独立取证到的底层事实全部为真。缺陷集中在**证据指针与身份钉定**，恰是本包自己列为失败族的「证据身份」——以带错误证据指针的案例去检验评价器能否抓证据身份缺陷，会形成循环性污染。修复为机械动作（改指真源、重算哈希、收窄措辞），不需 owner 实体裁决，故 **REJECTED** 而非 `PENDING_HUMAN_REVIEW`。

---

## 1. 逐项复算结果（命令 / 退出码 / 实测）

| # | 复算项 | 命令（摘要） | 退出码 | 实测 | 判定 |
|---|---|---|---|---|---|
| 1 | run 目录恰 7 件 | `python3`：`os.listdir` | 0 | **7** 件，与任务书一致 | **PASS** |
| 2 | 6 件产物 bytes/sha256 vs manifest | `python3`：`hashlib.sha256` + `len(bytes)` | 0 | 6/6 逐件一致（15365/3303/3952/7122/948/364） | **PASS** |
| 2b | manifest 不自哈希 | `Read artifacts_manifest.json` | 0 | `artifacts[]` 恰 6 条，不含自身；`self_hash_policy:"excluded from own list"` | **PASS** |
| 3 | 卡 7 输入 + STOP_S4/PREFLIGHT 共 9 条 vs `receipt.input_bindings` | `python3`：路径规范化（`D:\AIRcommend\JinRongAgents\agents_final_tech\`→仓库根）+ 逐条实算 | 0 | **9/9 存在且 `actual_sha256` = 实算**，0 失配 | **PASS** |
| 4 | 31 条 `source_refs` 存在性 | `python3`：`os.path.isfile` | 0 | **31/31 存在**，与 E7 `refs_missing:[]` 一致 | **PASS** |
| 5 | 31 条 `source_refs[].sha256` 实算 | `python3`：逐条 `hashlib.sha256` | 0 | **29/31 一致；2 失配**（均 `memory/THREADS.md`） | **FAIL** |
| 6 | 16 例逐条事实核对 | 见 §2；`Read`/`python3` 读证据原文 | 0 | **10 支撑 / 4 不足 / 1 过度陈述 / 1 错误归因** | **FAIL** |
| 7 | A1 字段齐 | `python3`：12 必需键扫描 | 0 | 16/16 齐；`legal_control_design` 16/16 非空；6/6 族 `legal_control_design_present:true` | **PASS（1 处见 F8）** |
| 8 | A2 同源不跨组 / 无封存 | `python3`：`incidents.group_id` ↔ `source_groups.member_incidents` 双向比对 | 0 | 7 组逐组 MATCH；16 唯一 ID；**双重归属 0**；16/16 `sealed:false`；7/7 `sealed_eligible:false`；7/7 `proposed_allocation:"development_or_calibration_only"` | **PASS（1 处见 F6）** |
| 9 | A3 不复制私有正文 | `python3`：三字段长度扫描 | 0 | 最长 **171** 字符（`T1-INC-06.observed_fact`）；无 raw 响应/凭证正文复制 | **PASS** |
| 10 | A3 不重跑旧实验 / B0 | `receipt.usage` + 反证检索 | 0 | 自报 model/network/remote/db/training/production **全 0**；`events.jsonl` 记 `model_requests:0`；**未发现相反证据** | **PASS（自报，见未验证面）** |
| 11 | 24/24/24 标注 | `Read coverage_matrix.json` | 0 | `totals_plan.note:"24/24/24 为构建计划，不是现有案例数量…"`；`built_now` 13+2+1=16 | **PASS** |
| 12 | 写入边界 | `git show --name-only 87027f08` | 0 | 该提交**仅 7 件 run 产物**；工作树脏件为 `logs/graph/*`×4（会话开始即存在）与 `reviews/T1R-01/REVIEW_PROMPT.md`（派发方写入），均非 T1 写入 | **PASS** |
| 13 | 覆盖矩阵 ↔ 例族归属 | `python3`：6 族桶 vs `failure_family` | 0 | **6/6 MATCH**；六族齐（对齐 reliability_spec §6.2）；三类 `expected_category` 齐（对齐 §6.4 `BLOCK/REVIEW_REQUIRED/ALLOW_WITHIN_SCOPE`） | **PASS** |

---

## 2. 16 例事实核对表（核心）

结论列：**支撑** / **不足** / **过度陈述**。

| 例 | 断言要点 | 取证结果 | 结论 |
|---|---|---|---|
| **T1-INC-01** | 首次请求非 JSON 且未先持久化；按卡立即停止；1/300 计入 | `S4_HISTORY_FAILED_ATTEMPT_RECEIPT.json`：`failure_point:"plan_response_json_parse"`；`JSONDecodeError: Expecting value: line 1 column 1 (char 0)`；`response_text_status:"not persisted by the first runner version"`；`stop_rule:"immediate stop on bridge failure"`；`global_attempts_used:1` / `global_hard_cap:300` | **支撑** |
| **T1-INC-02** | 最终重跑 512-token 纯散文；三路解析全败；按同类重复失败停面板 | `S4_HISTORY_FAILURE_FINAL_RECEIPT.json`：`all JSON bridge parse routes failed: strict=…; fenced=unavailable_or_invalid; balanced_object=absent`；`same_family_repeat_rule:"A second same-family bridge failure ends this panel."`；`status:"STOP_THIS_PANEL"`。`S4B_STOP_RECEIPT` `raw_response_full.usage.completion_tokens:512` 且正文为散文。路由名 `first_balanced` 在 bridge_v2 代码中实存（37 处/8 文件），非遗词 | **支撑** |
| **T1-INC-03** | 探针用 4 次请求 vs 上限 3；consume 阶段一探针耗 2 次；如实披露 | `S4B_STOP_RECEIPT.probe_cap` = `{used_requests:4, limit_requests:3, logical_sequences:3, status:"FAILED"}`；`disclosure:"A probe that reached the consume stage consumed two requests; the request cap is therefore exceeded by one."` | **支撑** |
| **T1-INC-04** | 逻辑序列 id 复用致 raw 覆盖；如实披露、不重建 | `S4B_STOP_RECEIPT.raw_preservation.incident`：`"The pre-fix S4 rerun reused one logical sequence id, so its later raw response overwrote that attempt directory; the old raw response is disclosed as lost and is not reconstructed."` | **支撑** |
| **T1-INC-05** | 动态模块未注册 `sys.modules` → `AttributeError`；零传输；修复一次（runner v1.1） | `INCIDENT_1_runner_import_failure.txt`：`root_cause:… not registered in sys.modules …`；traceback 末行 `AttributeError: 'NoneType' object has no attribute '__dict__'`；`budget_impact: 0 requests attempted; 0 model responses`；`classification: ENGINEERING_INCOMPLETE (zero-transmission) -> one repair + retry allowed`；`repair (runner v1.1)` | **支撑** |
| **T1-INC-06** | 约定错配 `(scores,input_ids)` vs transformers 5.14.1 `(input_ids,scores)`；scores 被当 token id 送 decode；HTTP 400 | 三源互证：`S4C_ONLINE_QUALIFICATION_RECEIPT.probes[0]` = `http_status:400` + `error_message:"out of range integral type conversion attempted"`；`incidents[2].root_cause:"logits-processor call convention mismatch vs transformers 5.14.1 (input_ids-first)"`；`INCIDENT_2` 给出完整机制（`SchemaConstraintProcessor.__call__(self, logits, input_ids)` 反序 → 浮点当 token id → `OverflowError`）；`processor_interface_diagnosis_output.json` 独立复现（`transformers_version:"5.14.1"`，transformers 约定调用 `raised:true` 同错串，离线约定 `raised:false`） | **支撑（强）** |
| **T1-INC-07** | 离线 PASS 但在线未验证（`online GPU constrained decoding`）；离线 dry-run 复用组件自身约定 | 前半 **成立**：`BRIDGE_V2_RECEIPT.status:"OFFLINE_QUALIFICATION_PASS_WITH_ONLINE_UNVERIFIED"`；`unverified_surfaces` 首项即 `"online GPU constrained decoding"`。后半 **被引件不支持**（`BRIDGE_V2_RECEIPT` 对 `convention` **0 命中**）；事实本身为真——`bridge_v2/offline_qualification.py:266` 确为 `masked = processor(logits, input_ids)`（即组件自身 `(scores,input_ids)` 约定），但该文件与 `INCIDENT_2` 均未被引 | **不足** |
| **T1-INC-08** | `*.log` 规则致证据未入库；`7406b3c`/`fe7b87f` force-add 补入 | 两提交实存且确为 force-add：`7406b3cf…`(12:48:04) `chore(tatqa): force-add S4C actor service log (gitignored by default…)` → `s4c_qual_run/service/service.log`；`fe7b87fa…`(16:37:57) `chore(research): force-add T1R-01 Loop C raw stdout log (gitignored by default…)`。弱点：「Loop C 原始 stdout」一侧无任何 `source_refs`，commit 亦未作引用锚 | **支撑（引用偏弱）** |
| **T1-INC-09** | R1 修 FILES.md 后未回钉；v2 校验 C2 报字节/哈希失配（草案 3 FAIL 之一）；随后补钉通过 | 草案 `20261014T085638Z_ba9297ac/receipt.json`：`C2_manifest_hash_bytes = FAIL`，`observed:{bytes_mismatch:["FILES.md"], hash_mismatch:["FILES.md"]}`；草案恰 3 FAIL（C2/C12/C17）；`SUPERSEDED.md`：`"the draft also surfaced one true package slip (FILES.md manifest pin stale after R1 edits)"`、`"Its artifacts (3 FAIL checks recorded)"`；v2 `20261014T085957Z_4e1698d1` 同项 `C2 = PASS` | **支撑** |
| **T1-INC-10** | 13 项 pin 取自本地工作树字节；GB10 侧 6/13 失配；三域复算判为表示差异、无内容漂移；按 1A 以 canonical blob id 重钉 | 13 条权威条目实数=13。`T1R-02`：`pin==GB10 raw 7/13`（失配 6）。**`T0R-01` F4 以逐行混合 EOL 重建证伪 T1R-02 F7**：THREADS/DECISIONS/SKILL_ALGORITHM 三 pin 由「blob + 纯 EOL 变体」精确命中，`6/6 同时满足 replace(\r\n,\n)==对象 与 replace(\r,"")==对象`，故 owner「1A」（表示差异、无内容漂移）成立。`authority_map.change_record.rule`：`canonical_blob_id … is authoritative`，旧值留 `local_snapshot_raw_sha256_historical` | **支撑** |
| **T1-INC-11** | Loop C 线程任务文本未注入采样上下文（harness 投递缺口）；经父线程会话日志恢复；恢复前后均只读 | **被引件不支持**：`reviews/T1R-01/REVIEW.md`（17569B）对 `注入/投递/采样上下文/父线程/会话日志/任务文本/恢复/未收到` **全部 0 命中**（该文实为 T-1 文档核对评审，判定 REJECTED）。事实**为真**，逐字记录在 **`research/tatqa_wp0_2026/wp2/LOOP_C_S4C_QUAL_AUDIT_v1.md`** 披露行：`「本审计线程启动时任务消息未注入采样上下文（harness 投递缺口），任务原文经父线程会话日志恢复；恢复前后活动均为只读侦察，未触碰被审对象。」`（sha `60ff75dd…`，与 STATE/THREADS 所记 Loop C 审计 sha 一致） | **不足（错误归因）** |
| **T1-INC-12** | PR-EXP a1/a2 记为 `ENGINEERING_DISPATCH_FAILURE`；不得计入 INVALID/NULL/NEGATIVE | **被引件不支持**：`memory/STATE.md`/`memory/THREADS.md` 对 `ENGINEERING_DISPATCH_FAILURE`/`PR-EXP`/派发标签 **0 命中**（`a1`/`a2` 命中均为中文子串噪声）。事实**为真**，真源 `research/positive_repair_20261011/POSITIVE_REPAIR_REGISTRY_v1.json`：`engineering_dispatch_failures_2026-10-11.classification:"ENGINEERING_DISPATCH_FAILURE"`、`detail:"a1 INPUT_MISSING x4 …; a2 HASH_MISMATCH x4 …"`、`treatment:"EXCLUDED from scientific result classes; never INVALID/NULL/NEGATIVE"`；`ROUND1_CLOSEOUT_v1.md` §3 同证。**另**：`memory/THREADS.md` 的声明 sha256 失配（见 F3） | **不足** |
| **T1-INC-13** | PR-01/03/04/07 **均未进入有效 effect measurement**；POSITIVE/NULL/NEGATIVE 计数全 0 | **过度陈述 + 引用不足**。第一轮为真：`ROUND1_CLOSEOUT_v1.md` §6 `Zero POSITIVE / NULL / NEGATIVE`、headline `"The first wave produced no scientific effect measurement."`。但 (a) 被引 STATE/THREADS **不含** `PR-01`/`PR-04`/`PR-07`/`undefined-domain`；(b) 被引 `STATE.md` 反而记载 **`Track P CLOSED: PR-03 v3 = NEGATIVE (gate PASS, effect measurement entered; frozen rule returns NEGATIVE)`** —— `observed_fact` 未携带标题里的「第一轮」限定，按字面会被读成覆盖 PR-03 全部轮次，与其被引证据相抵 | **过度陈述** |
| **T1-CTRL-01** | clean-only 工作点不可识别时如实记 `NOT_IDENTIFIABLE` 而非宣布通过 | **被引件不支持**：`memory/STATE.md`/`docs/INDEX.md` 对 `NOT_IDENTIFIABLE`/`不可识别` **0 命中**。事实**为真**，真源 `docs/research/stage_e_matched_fpr_reanalysis_v1.md`：`状态: BLOCKER_CLEAN_THRESHOLD_NOT_IDENTIFIABLE`；`VALUE: empirical clean-only matched-FPR TPR is therefore NOT_IDENTIFIABLE, not 90/111 versus 90/111` | **不足** |
| **T1-CTRL-02** | FinQA 测量对象错位（干预源字段、下游未同步重算）如实定位为 failed transfer / measurement-object mismatch，而非宣称外部验证成功 | **部分支撑**：`STATE.md` 支持核心判读——`FinQA formal-v3 is SECOND_FLOW_MIXED; accepted interpretation is MEASUREMENT_OBJECT_MISMATCH, not protocol-blindness or transfer confirmation`。但 `"failed transfer"` 与机制细节（下游 `res`/`answer` 未按变异程序语义重算）**不在被引件**，真源 `docs/research/finqa_v2_measurement_object_mismatch_autopsy_v1.md`（`Evidence class: NEGATIVE / FAILED_TRANSFER`；`downstream res/answer fields are not recomputed from the mutated program semantics`）未被引 | **不足** |
| **T1-INC-14** | 多轮执行对话 token 无法计量，一律记 UNRESOLVED；登记为未核验项 | `runs/T-1/20261014T085957Z_4e1698d1/receipt.json` `usage.execution_chat_usage:"UNRESOLVED"`；`artifact_level:"unverified_inference"` + `expected_category:"REVIEW_REQUIRED"` 分级正确，未冒充计量事实 | **支撑** |

**汇总：支撑 10 / 不足 4 / 过度陈述 1 / 错误归因 1。**

### 过度陈述 / 错误归因 / 引用不足 清单

| 类型 | 案例 | 内容 |
|---|---|---|
| **错误归因** | T1-INC-11 | 事实逐字记录在 `LOOP_C_S4C_QUAL_AUDIT_v1.md`，被引 `reviews/T1R-01/REVIEW.md` 零支撑；且 `T1R-01` 目录 ID 正被本次评审复用，指向进一步失真 |
| **过度陈述** | T1-INC-13 | `observed_fact` 丢「第一轮」限定；被引 `STATE.md` 明载 PR-03 **v3** 已进入 effect measurement 且为 `NEGATIVE` |
| **引用不足（ledger-only）** | T1-INC-12, T1-INC-13, T1-CTRL-01 | 仅引 `memory/STATE.md`/`memory/THREADS.md`/`docs/INDEX.md` 状态台账；真源 `positive_repair_20261011/*`、`stage_e_matched_fpr_reanalysis_v1.md` 未引 |
| **引用不足（子句）** | T1-INC-07, T1-CTRL-02 | 主判读有支撑，机制子句（离线 dry-run 约定 / `failed transfer` + 下游未重算）落在未被引文件 |

---

## 3. 发现清单（T1R-01）

### F1 — T1-INC-11 证据指向错误归因 【HIGH】
- **证据**：`reviews/T1R-01/REVIEW.md` 关键词扫描 0 命中；真源 `research/tatqa_wp0_2026/wp2/LOOP_C_S4C_QUAL_AUDIT_v1.md` 披露行逐字相符（sha `60ff75dd…`）。
- **影响**：一例以「无审计来源」为题的案例，自身审计来源指错文件。T1R-01 目录现被本次评审复用，指向将持续失真。

### F2 — 三例 ledger-only 引用，真源未被引 【HIGH】
- **证据**：T1-INC-12/13、T1-CTRL-01 的 `source_refs` 全部落在 `memory/STATE.md`/`memory/THREADS.md`/`docs/INDEX.md`；被断言关键串（`ENGINEERING_DISPATCH_FAILURE`、`PR-01`、`PR-04`、`PR-07`、`NOT_IDENTIFIABLE`）在被引件内 **0 命中**，而在真源内逐字存在。
- **影响**：违反「保留来源、独立审计指针」的卡 §4.1；A1「每例有来源」在追溯意义上不成立。恰是本包自称的「证据身份」失败族。

### F3 — `memory/THREADS.md` source_ref sha256 失配，且取自显式历史域 【HIGH · 直接违反 A-common】
- **证据**：T1-INC-12/13 声明 `0653ff3d23718d0124e2385da8ebd76d85645e0fed4d6c56b94da623bf26f214`；本工作树实算 **`39ba8d563839144817c23da598acb4f1ca595a5b9e77d8c7dd0623bac27ec11f`**，`git cat-file blob HEAD:memory/THREADS.md` **同为 `39ba8d56…`**（blob==worktree，CRLF 计数 0，655 裸 LF）。声明值 = `authority_map` 条目 THREADS 的 **`local_snapshot_raw_sha256_historical`**（`T0R-01` §2.3(e) 已重建其为「653 CRLF + 行 1、2 裸 LF」的历史 D: 树表示）。同批 STATE/INDEX 两引用碰巧等于工作树，故未暴露。
- **反证自检**：已排除「运行后文件变动」——`memory/THREADS.md` 末次提交 `abc0a5de`(12:46:44+08) 早于 T1 run(13:22:49Z)，`git status` 干净；已排除统一 EOL 变换（LF/CRLF/strip 三态均非 `0653ff3d`）。其余 29/31 引用与 9/9 输入绑定均按本树实算命中，故「按本树哈希」是包内通行约定。
- **影响**：A-common「声明哈希实算一致」**不成立**（2/31）。且 `authority_map` 明示 `hash_authority:"canonical_blob_id"`，历史字段被当作现行身份使用——与本包 T1-INC-10 自述的教训正相反。

### F4 — T1-INC-13 过度陈述：丢「第一轮」限定 【MEDIUM】
- **证据**：标题载「正修补第一轮」，`observed_fact` 作「PR-01/03/04/07 均未进入有效 effect measurement」；被引 `STATE.md` 记 `PR-03 v3 = NEGATIVE (gate PASS, effect measurement entered…)`。
- **影响**：按字面读会与被引证据相抵；`expected_category=REVIEW_REQUIRED` 案例尤忌表述越级（reliability_spec §6.3 `claim_overreach=0`）。

### F5 — T1-INC-07 / T1-CTRL-02 机制子句引用不足 【MEDIUM】
- **证据**：INC-07「离线 dry-run 复用组件自身约定」真源 `offline_qualification.py:266`（`processor(logits, input_ids)`）/`INCIDENT_2`，均未引；CTRL-02「failed transfer」+ 下游 `res`/`answer` 未按变异语义重算，真源 `finqa_v2_measurement_object_mismatch_autopsy_v1.md` 未引。
- **影响**：主判读可用，但复核者无法从被引件闭环。

### F6 — A2 同源簇跨组：T1-INC-12 / T1-INC-13 【MEDIUM】
- **证据**：两例同出 `research/positive_repair_20261011/{POSITIVE_REPAIR_REGISTRY_v1.json, ROUND1_CLOSEOUT_v1.md}` 同一轮收口（§3 与 §6 同文并列）；却分属 `G-HARNESS` 与 `G-REPAIR`。而 `G-REPAIR` 自名为「**正修补第一轮链**」却独缺 INC-12。
- **影响**：卡 §4.3「按来源事故簇归组」与 A2「同源事故及改写不得跨组」在此不自洽。实务风险低（16 例全部 `development_or_calibration_only`、无封存），但分组声明本身不成立。

### F7 — receipt `E7` 主张越级 【LOW】
- **证据**：`E7_refs_verified.description` =「All source_refs verified against the working tree」，`method` =「existence check per ref」，`result:"INFO"`。存在性 31/31 成立，哈希维度未检且实有 2 处失配。
- **影响**：正是 reliability_spec §6.3「主张越级」定义的形态（把较低层级验证扩大为较高层级结论）。

### F8 — A1「适用范围」无专字段 【LOW】
- **证据**：16 例键集 = `{artifact_level, date, expected_category, failure_family, group_id, incident_id, legal_control_design, observed_fact, sealed, source_refs, title, visibility_note}`，无适用范围字段；`receipt.E4` 将「applicability」直接等同 `expected_category`。按 reliability_spec §6.4，`expected_category` 是评价**判定类别**（BLOCK/REVIEW_REQUIRED/ALLOW_WITHIN_SCOPE），与「适用范围」非同一概念。
- **影响**：信息可由 `failure_family`/`visibility_note`/`legal_control_design` 部分还原，但 A1 三元组未逐项落字段。

---

## 4. FACT / INFERENCE / UNVERIFIED

**FACT（本人实测）**
- 7 件产物 6/6 字节+SHA-256 = manifest；run 目录恰 7 件；manifest 自排除。
- `receipt.input_bindings` 9/9 实算逐位命中（含 STOP_S4、PREFLIGHT）。
- `source_refs` 31/31 存在；**29/31 哈希一致，2 失配**（`memory/THREADS.md`×2）。
- `memory/THREADS.md`：blob==worktree==`39ba8d56…`，0 CRLF；声明值 `0653ff3d…` = `authority_map.local_snapshot_raw_sha256_historical`。
- 16 例 12 必需键齐；`sealed:false` 16/16；双重归属 0；`incidents.group_id` ↔ `source_groups.member_incidents` 7/7 MATCH。
- 六族齐、三类 `expected_category` 齐；`legal_control_design_present` 6/6；`planned_build` 24/24/24 且显式标注为**构建计划**。
- 最长描述 171 字符；无 raw 响应/凭证正文复制。
- T1 提交 `87027f08` 仅写 7 件 run 产物。
- T1-INC-03/04/05/06/09 与 T1-INC-10 的被引证据逐字支持其断言（INC-06 三源互证，含 5.14.1 调用签名与 `OverflowError` 串）。
- T1-INC-11 真源为 `LOOP_C_S4C_QUAL_AUDIT_v1.md`（sha `60ff75dd…`）；T1-INC-12/13 真源为 `positive_repair_20261011/*`；T1-CTRL-01 真源为 `stage_e_matched_fpr_reanalysis_v1.md`。
- commits `7406b3cf`、`fe7b87fa` 存在且确为 `*.log` force-add。
- 草案 `20261014T085638Z_ba9297ac` 恰 3 FAIL，其 `C2_manifest_hash_bytes` FAIL 项即 `FILES.md` 字节+哈希双失配；v2 同项 PASS。

**INFERENCE（推断）**
- F3 的成因最可能是：对三条权威文档（STATE/THREADS/INDEX）的 `source_refs[].sha256` 取自 `authority_map.local_snapshot_raw_sha256_historical` 而非现场实算。依据：三值与该字段逐字相同；STATE/INDEX 与本树偶然一致故未暴露；其余 29 引用与 9 绑定均按本树实算，说明包内通行约定是「工作树 raw」。备选解释（执行者在 D: 树作业）与其余 29 条按 Linux 树命中相冲突。
- F2 的成因最可能是：对已复盘的历史事件，执行者引了状态台账而非一手证据文档（4 例全部集中在 STATE/THREADS/INDEX），呈系统性取材习惯而非单点笔误。
- INC-12/13 被拆到两个组，最可能是按**失败族**（交付与权限 / 完整性与预算）而非卡 §4.3 的**来源事故簇**归组，与 `G-REPAIR` 命名叠加后显形。

**UNVERIFIED（本次无法验证）**
- 执行者自报 usage 各项（model/network/remote/db/training/production = 0）无独立计量通道；只能做**无反证**检验（已做，未发现相反证据）。`execution_chat_usage` token 消耗执行者与本评审均记 `UNRESOLVED`，未冒报 0。
- D:/AIRcommend 树在钉定当时的实际字节与是否干净（不在本机、禁联网）——这正是 INC-10「来源」侧由 owner「2行」裁决关闭的问题；不影响 F3 的失配判定（失配是对**本树**而言）。
- 任何模型端点 / 生产服务 / 数据库行为（约束内零调用；本地文档检查不代表 GB10 运行验证）。
- 未逐行审读全部 31 条被引证据原文；T1-INC-01/02/08/14 采用抽证（关键字段/提交对象/收据字段）而非全文背对背。
- 24/24/24 构建计划的可行性未评估（属 T2 范围，本评审不进入）。
- 「同源事故」判定标准未在卡内形式化；F6 依据 ROUND1_CLOSEOUT 同文并列而判，收口者可按其对「同源」的定义复裁。

---

## 5. 判定与理由

**提案：REJECTED**

理由：

1. **直接违反卡内自动验收断言 A-common**：「声明哈希实算一致」在 `source_refs` 维度 **2/31 失配**（F3）。这是明文断言，不是风格偏好。
2. **卡的首要职责不成立**：T1 §4.1 要求「保留来源、时间、运行级别、失败族和独立审计指针」，§7 要求「独立评审案例事实与分组」。16 例中 **5 例**（INC-11/12/13、CTRL-01/02）的事实无法从其被引件闭环，其中 1 例指错文件、1 例措辞与其被引证据相抵（F1/F2/F4/F5）。
3. **不 ACCEPTED 的实质理由**：本包是 R 线的可靠性案例集，用途是检验评价器能否抓「证据身份 / 主张越级」类缺陷。若把带错误证据指针与错误哈希钉的案例收进开发集，等于用污染样本去标定「证据完整率=100%」「主张越级=0」两道硬门，形成循环性失真。
4. **不 `PENDING_HUMAN_REVIEW` 的理由**：五项发现全部位于**记录层**（指针指向、哈希取值、措辞限定、分组标签、收据措辞），无一触及科学结论、冻结结论或授权边界；修复是机械动作（改指真源、按本树重算、加「第一轮」限定、同源并组、收窄 E7 描述），不需 owner 实体裁决。把机械可修的记录缺陷升级为人类门，与 T0R-01 已确立的「记录层缺陷不升级」口径不一致。
5. **无编造、无越界、无封存泄漏**：我独立取证到的底层事实**全部为真**（含 INC-06 的调用约定机制、INC-03/04 的 probe_cap 与 raw 覆盖、INC-05 的零传输修复一次、INC-08 的两个 force-add 提交、INC-09 的 C2 失配后补钉、INC-10 的 6/13 表示差异判定）。16 例全部 `sealed:false` 且 `development_or_calibration_only`；未把工程失败计作科学结果（INC-12/13 的分级纪律正确）；未复制私有正文；B0 零调用、写入边界干净。**包的骨架值得保留，只需证据层返工。**

**交办条件（供收口者执行，非阻断项之外的最小返工集）**
- **必改**：① INC-11 改指 `LOOP_C_S4C_QUAL_AUDIT_v1.md`；② INC-12/13 改指 `positive_repair_20261011/{POSITIVE_REPAIR_REGISTRY_v1.json, ROUND1_CLOSEOUT_v1.md}`，CTRL-01 改指 `stage_e_matched_fpr_reanalysis_v1.md`；③ 全部 `source_refs[].sha256` 按本树重算（至少修 `memory/THREADS.md`）；④ INC-13 `observed_fact` 补「第一轮」限定；⑤ INC-07/CTRL-02 补引机制真源。
- **建议**：⑥ INC-12 与 INC-13 并入同组（或改 `G-REPAIR` 命名）；⑦ `E7` 描述改为与 method 一致；⑧ A1 增设独立「适用范围」字段，勿与 `expected_category` 混用。
- **不动**：六族覆盖、三类 `expected_category`、24/24/24 构建计划标注、无封存标记、B0 申报、写入边界——均已独立复算成立，返工时勿改。

===
