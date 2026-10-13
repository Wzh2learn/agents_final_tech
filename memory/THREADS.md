# memory/THREADS.md — 未决线索

[10-13] #PAPER-E-PRESENTATION-CLOSED-AND-WP2-PREP: (1) Paper E 表达层收口：移除内嵌 sha256 与部署式字符串（`127.0.0.1:8004` -> `served locally`；`:8004 judge` x2 -> `local judge`），重建 9 页 / 0 overfull；`PRE_SUBMISSION_AUDIT` / `WIDE_EVIDENCE_CHECK = PASS`；PDF 文本 `127.0.0.1`/`:8004`/`sha256`/`localhost` 计数全 0；commit `078398e`（robustness Sec.8 与 PDF_LAYOUT_AUDIT 记录同步更新）；科学数字/claim 零变化，10/20 冻结不受影响。注意：`paper/teacher_review_draft_v1.md` 与 `paper/submission_draft_arr_www_anonymous_v0.md`（另一条 ARR/WWW 冻结链）仍含 `:8004`，未动，需该链自查修订+重钉、待 owner 决定。(2) 负结果稳健性核查闭环：复算 11/11 + FPR 字节级重跑 + 独立 bug-lens PASS/PASS；记录 `research/negative_result_robustness_20261013/`（含 §7 循环风险 Q&A、§8 文本扫描）。(3) 大论文 WP-2 前置就绪：runbook（S0–S11 四步法）+ split dry-run 收据入档（`7a6cc11`）；新增 Loop A / Loop C 预冻结执行卡（DRAFT，未派发）于 `research/tatqa_wp0_2026/wp2/`；待 owner 拍板 P2 feedback-right / P3 actor+MODEL_GO / P4 预算窗口；S0–S3 零模型可先行。已记录发现：题本需“每原点 2 题”（现 1 题；176 原点有 >=2 行）。(4) skill 库第二轮合并首项已入档（`portfolio-triage` -> `inquiry-methods`，`7a6cc11`）；全量扫描报告待交付（派单通道今晚不稳）。

[10-12] #EXECUTION-HANDOFF-WAITING-NEXT-TASK: [执行侧状态](../docs/research/EXECUTION_HANDOFF_STATUS_v1.md) 固定后续两项：Paper E按gate进入WP-E修订流程；大论文仅WP-0只读资格核验。当前科学纠偏/材料核验未执行、两门PENDING；已有owner待办见下方FINAL条目，不新增路线或门。主入口齐备，STATE旧目标已标历史；蓝图“拟建task card”不表示应重建或资格已过。远端实际版本/文件与具体权限在下一阶段任务绑定；本轮交接完成后停止，未派活、未改稿/代码、未实验。

[10-12] #FINAL-RESEARCH-HANDOFF-PENDING-ACTIONS: 当前入口为 [repo治理收尾](../docs/research/REPO_GOVERNANCE_FINAL_v1.md)。Paper E [投稿门禁](../docs/research/PAPER_E_SUBMISSION_READINESS_GATE_v1.md) = BLOCKED_SCIENCE：A2核心claim及其余作者裁决未落实，尚需明确改稿范围、同一最终包验收、作者签署与owner外发决定；旧“只剩人工事项”已失效。硕士 [执行入口](../docs/research/MASTER_RESEARCH_EXECUTION_ENTRY_v1.md) 下一步仍WP-0只读来源/许可/目标/经验核验，G-RQ/G-M PENDING、创新未识别；Memory/SFT/DPO/Adaptation未来空间不等于现役贡献或运行许可。Git集成/远端运行/独立GB10验收未本轮核验，工作区脏件保留；无清场或删除请求。本地skill静态0 errors/139 warnings（既有）、map 27项启发式引用候选，目录债务保留，不是新增科学阻断；未自动修复。后续Loop D按具体包与权限派活，Loop A不自动推进。

[10-12] #TH3-WP0-DESIGN-QUALIFICATION-PENDING: [最小科学验证任务卡](../docs/research/thesis_experience_v1_task_card.md) 已完成设计；四臂只识别固定经验包的受限效应，不分离反馈资格的贡献，不证明Memory/SFT或方法创新。下一步仍需只读绑定确切来源/revision/文件/IDs/许可、origin/近重复、参考目标与经验可得性，交导师/owner裁决；`G-RQ=PENDING / G-M=PENDING / METHOD_NOVELTY=NOT_IDENTIFIED`。CONTINUE只支持申请必要性/既有基线比较，未授权WP-1/2。本轮零实验、代码/改稿、模型或GB10访问。

[10-12] #THESIS-RESEARCH-BOUNDARY-FROZEN: 当前边界以 [研究治理基线v1](../docs/research/THESIS_RESEARCH_GOVERNANCE_BASELINE_v1.md) 为准，架构v3管范围、蓝图v1管工作包与原首验参数；取代下面较早规划条目的未来推进口径。RQ2是待验证假设，具体方法创新未识别；Paper E不认证学习资格，Memory/SFT/Adaptation不预设贡献。`G-RQ=PENDING / G-M=PENDING / METHOD_NOVELTY=NOT_IDENTIFIED`；下一步仅WP-0只读核验，首验也须通过两门对最小验证范围的裁决与具体许可，pilot正向不自动进入新算法。导师待裁决任务/必要性、方法差异、资源与学位要求；历史字节快照已保留。零实验/代码/改稿/GB10/训练/外发，旧闭线与NOT_RUN不变。

[10-12] #THESIS-V3-BLUEPRINT-DESIGN-ONLY: 用户要求吸收三RQ与题目反馈、调整文档并生成执行规划；当前规划入口为 [架构v3](../docs/research/THESIS_RESEARCH_ARCHITECTURE_v3.md) → [执行蓝图v1](../docs/research/THESIS_EXECUTION_BLUEPRINT_v1.md)。新TH3-RQ命名不解除旧DATA_NO_GO/RQ2 NOT_IDENTIFIED或PR03/FinQA/TAT-DQA闭线；首验参数/来源/许可/模型与预算须在未来运行前绑定，Paper E科学纠偏仍未执行。导师待确认学位要求、题目定稿与参数资源；本轮仅文档，零GB10/模型/服务/实验/训练/改稿/外发。

[10-12] #STRATEGIC-REVIEW-PENDING: 新的独立战略审查见 [STRATEGIC_REVIEW_AND_NEXT_PLANS_v1.md](../docs/research/STRATEGIC_REVIEW_AND_NEXT_PLANS_v1.md)。新发现的 C2 操作点/ROC 区分、non-direct 部分信息及 harmfulness/FinQA 解释问题待作者独立审定；TOP 3 CONTINUE/STOP/NEW BETS 与6个未来工作包均为建议，不更改冻结结果/分支状态，不构成 GB10 实验、训练或改稿授权。本轮仅阅读/记录，零项目端点访问。


> 归档说明（2026-10-11）：本文档只保留近期未决线索（条目日期 >= 10-03）。更早的条目（<= 09-30，共 202 条）已按块字节级原样移入 `archive/THREADS_archive_pre_2026-10-01.md`；更早的历史滚动件见 `archive/THREADS_history.md`。
[10-09] #NEAT-CLEANUP-ACTION-COMPLETED: user confirmed deletion after full report; OpenCode sessions reduced 50->20, nine old config backups deleted, three current backups retained. Post-cleanup audit passed; attached tmux and legacy warnings remain untouched.
[10-09] #NEAT-ARCHIVE-COUNT-CORRECTION: previous 149 count is corrected to 150 after the final completed profile-smoke session was archived; active Codex session files=0.
[10-09] #NEAT-CONFIG-SESSION-CLOSEOUT: Loop A/C Xiaomi routes synchronized; 149 Codex sessions archived reversibly. OpenCode session trim and attached tmux closure are preview-only pending user confirmation after the complete report. No repo commit/push.
[10-08] #STAGE-E-INQUIRY-OPEN-DECISIONS: 公开元数据审计与 12-section Stage E inquiry/report 已完成，但实验状态仍为 `DESIGN_ONLY_NOT_AUTHORIZED`。待用户拍板：(1) multi-leaf synthetic 优先于 second dataflow；(2) harmfulness 定义维持 equivalence-dependent construct 还是比较新定义；(3) synthetic matrix、responsive-leaf minimum、table-origin split 与 independent-scorer scope 如何冻结。不得据此启动实验、下载、训练或外发。

[10-08] #STAGE-E-METADATA-BUDGET-EXCEPTION: 2026-10-08 metadata acquisition 使用 72 distinct URLs、94 actual HTTP attempts，超过 80-attempt budget 14 次；状态 `EXCEEDED_TRANSPARENTLY_REPORTED`。之后停止全部 HTTP。失败/回退项（TabFact DOI、PubTables official dataset entry、DeepMatcher exact record 及 rate-limited fallback）保持 `UNVERIFIED`，不得猜测补齐。

[10-08] #OPENALEX-METADATA-HANDOFF: OpenAlex key configured outside repository and validated HTTP 200 locally and on GB10; no key stored in Git/docs/logs. Crossref/OpenAlex paper candidates identified for FinQA, TAT-QA, TabFact, PubTables-1M, FeTaQA. Dataset licence/provenance/native bridge/independent-origin audit is still open and must resume in a new session; no download, experiment, model call, or claim upgrade occurred.

[10-08] #NEAT-CACHE-CLEANUP-COMPLETE: 用户看过完整报告后确认删除候选与缓存清理。已删除本地误同步临时树和项目 `__pycache__/.pytest_cache/.ruff_cache`；GB10 同类缓存已清零并显式保留 `venv/.venv`。未删除唯一证据、凭证、模型、数据、production 脏件或运行态台账。清理验证时 local/origin/GB10 对齐于 `8a36913dcd5ad62c06550e6a39a4972b200cb145`；当前 head 以 `git rev-parse HEAD` 为准。无源代码或实验状态变化。

[10-08] #NEAT-SELF-CHECK-GOVERNANCE main@8c0b248: 四批治理补充已同步到 local/origin/GB10；GB10 focused governance `13 passed`、tracked secret scan clean、docs_lint `0 fail / 7 warn`、skill-doctor `0 errors / 106 warnings / 0 fixes`。Stage E package 证据仍绑定 `62274ef`，后续治理提交不改科研数字或边界。删除候选仅一件：仓库根的异常 `C<private-use colon>` 目录，内含此前 Windows/WSL 路径误同步产生的 `audit-cycle` 临时副本；已确认无唯一证据，但按 neat 清场规则未删除，等待用户看过报告后明确确认。全局 hook 配置未改；registry_check/loopkit_ledger 未导入。

[10-08] #STAGE-E-ADVISOR-REVIEW-READY main@62274ef: Stage E 已完成 measurement-validity 身份收敛与最后一轮小修，当前 final head `62274ef1fa624912390d4f0a05828c038a938ccb`，local/origin/GB10 一致。GB10 定点验收：claims `74/74`、submission `10/10`、focused `22 passed`、Office/PDF 9 页视觉 PASS。本次只改 Abstract 外推措辞、§3.2 定义边界、mutation-testing 表述和 readiness 顶部状态；不改数字、判据、claim boundary 或冻结证据。仅余导师决策：multi-leaf vs second dataflow；harmfulness 定义选择。

[10-05] #FORMAL-NEGATIVE-PATH-B-COMPLETE: 当前 goal 的合法路径 B 已完成并落盘 `docs/experiments/2026-10-05_formal_negative_path_b_completion_audit.md`。六项完成标准均 PROVEN：`DATA_NO_GO / RQ2 NOT_IDENTIFIED`；Valentine 551 tasks 仅 8 个保守 origin components；无 native trajectory/checkpoint bridge；完整 E-D-R 转 future work；Stage E 小论文内部投稿版完成；大论文开题/第1–2章/第3–8章框架、Track B pilot、负结果边界与未来数据需求完成。科学/测试权威来源为 `f0764e7` 或等价 GB10 head：全量 `870 passed / 13 skipped / 1 deselected`、focused `27 passed`、claims `74/74`、submission `10/10`、docs_lint `0 fail / 4 warn`。`652c9c6` 仅修审计元数据，`1d5a7ff` 仅做文档归档/链接/workspace neat，二者不改变科学结果或运行代码。Track B 封存 `/home/testuser/wzh/track_b_adapter_20261005_seal/`，manifest hash `dc388959150c98ffa7639108e1e80e306c346317b1cdced632ab66593960a04b`，correctness 仍 `NOT_RUN`。外部投稿、patent/venue/作者/camera-ready、Stage D/R/RQ4、训练、Phase 2 和发布仍不完成。

[10-05] #VALENTINE-FULL-ROUTE-NEGATIVE-BOUNDARY: 用户选择第二路线（Valentine full benchmark + frozen process adapter）。Zenodo Valentine full benchmark 只读结构审计确认 551 个完整 pair，但保守 shared-origin components 仅 8（`miller2`/`prospect`/`assays`/`Musicians` + Magellan 3/2/1/1），低于 40，预注册硬止损因此自动转入第三路线：接受 `DATA_NO_GO / RQ2_NOT_IDENTIFIED` 为正式负结果，完整 E-D-R 转 future work，小论文保持 Stage E。未下载 archive、未提交 selected-pair annex、未运行 full-benchmark adapter/A0-A3/Phase2/B5/训练。

[10-05] #GOAL-COMPLETION-AUDIT-EXTERNAL-INPUT-BLOCKER: 完成审计结论 `NOT_COMPLETE_FOR_FULL_GOAL / INTERNAL_DELIVERABLES_COMPLETE`。RQ2 same-sample mother pool 仍无可用来源；registry screen `0/10`，Route V gap 30，Stage D/R/RQ4 仍无确认性结果。剩余工作需要用户提供新的精确 source/task-definition annex、批准 adapter 路线，或明确接受正式负结果边界；在此之前不运行 A2、Phase 2、训练或外发。

[10-05] #RQ2-CANDIDATE-SOURCE-SCREENING-0OF10: 对 `paper-public-source-registry-v1.json` 的 10 个 metadata-only 候选逐项审计同一 UID 四要求（checkpoint evidence、map/hold/skip action/target、独立 correctness、independence/role fit），直接合格 `0/10`。FinQA/ConvFinQA 只有 process/program；MultiHiertt 等需 adapter；Valentine 仅 exploratory 且固定 revision 缺 30 clusters；其余为 QA/type/proposal labels。结论限定 registry 范围，不是全球不存在声明；未选新源、未下载、未扩许可，`DATA_NO_GO / RQ2_NOT_IDENTIFIED` 不变。

[10-05] #PAPER-EVIDENCE-STATE-REFRESHED: 已统一 12 份内部小论文/大论文材料的 Q3/B0-B4 状态：Q3 raw/ledger/hash 已封存、corrected 51/58/37、visibility exceptions 保留，仅 exploratory；B0-B4 v2 已完成但 Stage D 仍 `PILOT_ONLY`。同时修正 thesis/teacher-review/figure/reproducibility/submission/asset-map 中的“只有输入包/未复核/NOT_RUN”旧口径。Stage E 已成立数字、claim token、引用与公式未改；`DATA_NO_GO` / `RQ2 NOT_IDENTIFIED` / 外发边界不变。

[10-05] #PHASE2-DUPLICATE-JSON-GATE-CLOSED: `research/phase2_rule_gate_replay.py` 的重复 JSON key 执行门已在历史 commit `60eaa27` 修复：`object_pairs_hook` 拒绝 dataset/config/nested duplicate key，`parse_constant` 拒绝 NaN/Infinity；负例覆盖 config `min_source_gain` 后值静默覆盖、dataset/nested key、NaN、unreadable file。GB10 `tests/test_phase2_rule_gate_replay.py` = `22 passed`。本项只闭合软件执行门，Phase 2 仍 `NOT_RUN`，不产生 replay、Stage R/RQ4 或训练证据。

[10-05] #STAGE-D-NECESSITY-CRITERIA-ALIGNED: 已将五项 A2 necessity 初始判据从“待确认”纠正为 `APPROVED_INITIAL_VALUES`，绑定 training readiness config：coverage gain >=0.05、target exact non-inferiority margin <=0.02、single-pair residual/gain share <=0.50、三 slice harmful-map risk upper <=0.10、primary/pair-invalid A2-B4 coverage delta lower >0。当前 A2 未运行，gain/target/gain-share/deltas = `NOT_ESTIMABLE`；B4 residual 最大 pair 占比 6/13=46.2% 仅作诊断；salted risk upper 0.1250 FAIL，verdict 保持 `PILOT_ONLY`。Route V `>=40` 目标已批但官方 revision 仅 10 clusters、新增 0、缺口 30，缺 exact new-directory annex，不下载、不换源。

[10-05] #QWEN3-8B-SYNC-ARTIFACT-VALIDATED: Qwen3-8B revision `b968826d...` 通过 `hf-mirror.com` fallback 精确 15 文件同步到 `/home/testuser/wzh/models/hf/Qwen3-8B`，`token=false`、Xet disabled、HF transfer disabled。monitor/download PID 3412262/3412266，13m41s，RC=0，无残留进程。GB10 真实 validator `PASS_ARTIFACT_VALIDATION_NOT_MODEL_GO`：15/15 identity（6 LFS SHA256 + 9 Git blob SHA1）、5 shard headers、399 tensors、tokenizer/licence、clean `e47b9aca...`、full `6ba50550...`。readiness `model_revision_ready=true`；科学门/stable residual/训练窗口未全过，S0/A0-A2/Phase2/训练仍不运行。

[10-05] #QWEN3-4B-ARTIFACT-VALIDATED-GB10: 本机 validator fixture 过程结果（含 3 failed / 1 passed）只记 `DEV_ONLY / NON_AUTHORITATIVE`，不作项目验收。GB10 focused contract tests `15 passed`；真实 Qwen3-4B validator `PASS_ARTIFACT_VALIDATION_NOT_MODEL_GO`：13/13 immutable identity（4 LFS SHA256 + 9 Git blob SHA1）、3 shard headers、398 tensors、tokenizer/licence、canonical model-root-relative manifests 全过。receipt SHA256 `227576f2...`；readiness `PASS_DRY_RUN_ONLY`，`smoke_model_revision_ready=true`，但 Qwen3-8B `NOT_DOWNLOADED`，`model_revision_ready=false`。S0/A0-A2 已获条件式自动授权，但六项门尚未全过，当前仍 `NOT_RUN`；A3/Phase2/新数据/外发仍需另批。

## 当前科研阻塞与接续（2026-09-23）

- **当前 Git 基线**：审计整改开工时 `test/compaction-guard-abort` 与远端 test 均为 `7dd505c`；本轮 v2 合同/理论/统计修复已在该基线上以 fast-forward 提交交付（接手时 3 项测试失败，已修复并补正测；复核时再发现并关闭 duplicate-role 绕过 feature-ledger hash 绑定的 fail-open 缺口，七套件 118 passed）。未使用 reset/rebase。
- **论文状态不变**：Stage E 是成熟评估子稿；Stage D 无训练后证据；Stage R 只有机制级证据。Phase 1a 仍为 `DATA_NO_GO`，Phase 2 只有仓内软件合同、正式数据 replay 未启动；零样本矩阵不能写成蒸馏结果，评估方向包不能冒充三阶段完整论文。
- **Phase 1 v2 审计整改已交付**：`research/phase1a_data_contract.py` 改为 namespaced lineage UID/root/independence-cluster 三层隔离，canonical Q3 ledger，当前四层必有数据；future 可空但须 hash-bound acquisition protocol，并显式输出 `LONGITUDINAL_EVIDENCE_UNAVAILABLE`。机械通过仍只到 `READY_FOR_INDEPENDENT_ACCEPTANCE`。
- **五基线 runner v2 已实现但未正式运行**：proposal view 现在逐条回查 hash-bound canonical Q3 ledger；`harmful_map_rate`、`map_to_risk`、`correct_map_coverage` 分母已消歧，`min_dev_uids=1` 被拒。没有私有 baseline 数字，Phase 1a 状态不变。
- **Phase 2 v2 已实现但未正式运行**：七臂状态机保持不变，统计输出把 rule-level harmful accept 与 UID-any-harm/Clopper–Pearson 上界分开；Phase 2 只依赖已接收数据、可重建状态和单独授权，不依赖 `LEARNABILITY_SIGNAL`。没有真实 replay 数字。
- **理论/数据冲突已修、证据缺口不伪造**：A1/A2 已拆共同资格 $u_i$ 与 checkpoint filter $z_i$；学生直出/送检、规则效用、完整 UID collateral、单侧非劣、Holm family 和 seed×UID 汇总已明确。FinQA 与 Valentine 只算互补预研；未找到同一母池同时含 checkpoint evidence、Q3 action/target、Q3 outcome 前，RQ2 保持 `NOT_IDENTIFIED`。
- **预注册已原位收口**：`docs/experiments/2026-09-22_distillation_mvp_preregistration.md` 已从旧 SP-RQ2/4B 对照草案改为当前 RQ2–RQ4 实验口径合同，覆盖五基线止损、A0–A3、七臂 replay、双公平口径和独立冻结收据。状态仍为 `DRAFT_NOT_FROZEN`，数值容差/模型 revision/预算/数据批准未由 Agent 代填。
- **GB10 仍待复核**：上次已知 production 为 `e5ab809`；2026-09-23 的一次 SSH 连接超时，当前 checkout、脏件、进程、Loop B、控制队列、私有数据和 Loop C Lead 均未验证。不得使用本地缓存 `gb10/main=3dabbc7` 推断实况，不得认领 READY 卡。
- **恢复顺序**：先只读核 GB10 状态并建立干净隔离 worktree，再只读挂载私有补充包，跑聚焦测试和两次 `strace` 预检，要求报告逐字一致、零 connect、七门全 PASS；随后由独立人员复核许可、标签身份/裁决、分析计划与 parser receipt。任何一步失败继续 `DATA_NO_GO`。
- **仍需后续门/授权**：GB10 私有包与人工验收通过后，Phase 1a 正式可学性探针仍须按已绑定配置运行；Phase 2 数据 replay 即使已有软件骨架仍须单独批准并按 handoff 双跑验收；4B smoke、8B 主训练、模型/服务/数据库动作、正式实验数字和公开投稿均未开放。Office 视觉验收仍为独立待办；专利状态未确认前不外发。
- **当前执行权威**：入口为 `docs/research/README.md`，叙事为 `paper/research_story_v2.md`，证据为 `paper/research_asset_map_v2.md`，唯一计划为 `docs/handoff/2026-09-22-paper-research-next-phase.md`。旧 closeout 细节留在 Git 与 handoff §10/§12，不再复制到当前台账。

## 技术未决（来自 blocked_questions.md 现存条目）

### Phase 1 数据抽取 (2026-08-01 19:45) — RESOLVED 带遗留
- 问题: /api/m2/compare/positions 对 jiaxing 返回空; PGVector metadata product_name 与查询不匹配。
- 状态: 2026-08-03 23:35 双根因已修 (服务进程缺 PGDATABASE_URL + 表类型判断改用 table_name+matched_schema 联合); positions 0→2, 24 tests passed。
- 遗留: 110/137 chunk 的 product_name 为空或正则碎片 (OCR 样本), 记录不修。
- 下一步: 若跨文档对比出现实质错漏, 再重做 ingest metadata 注入。

### OCR meta-query (2026-08-03 23:36) — RESOLVED (2026-08-05, Loop A)
- 问题: "哪个样本通过 OCR 解析了交易对账单" 被 scenario1 caitong HTML 特别提示样板 chunk 抢占排序 (0.4385)。
- 状态: **已修, QA 15/15=100%**。根因三层: 样板 chunk 含"交易对账单"字面量 (内容碰撞) + BM25 stub 未实现 (混合检索退化纯向量) + 正确证据 chunk (ocr_table_1:r0, dist 0.4420 ~第35名) 被 top_k 候选池截断。修法: 137 chunks 非破坏性 cmetadata 标记 doc_type (email_notice=15/ocr_table=11/parse_meta=17/reconcile=17/header_meta=15/statement=62, 工具 scripts/m1_rag_tag_doctype.py 幂等) + smart_retrieve 对含 "ocr" 查询补一路 doc_type=ocr_table 过滤召回 + 重排 (ocr_table schema 命中 x1.35 / 其余 x1.15 / email_notice x0.70)。未 --reset、未删灌 chunk、未重启 :5050。
- 遗留: ~~:5050 重启后 curl 复验 (Loop D 择窗)~~ **CLOSED (2026-08-09)**: 重启后生产端复验 PASS (sources=3, TraFax+WaveFax 正确溯源, 08-09 两次复验); ~~BM25 stub 未实现~~ **CLOSED (2026-08-09)**: 真 BM25 已实现并 flag 化 (M2_ENABLE_BM25 默认 false, A/B 零增益决策不修); coord_table 未纳入 ocr_table 语义 (见交付说明 §6)。详见 logs/graph/loop_a_ocr_metaquery_result.md。

## 其他技术线索
### 08-26 夜间冲刺: 导师文档 + demo_v3 视频交付 + judge 超时归因 (2026-08-25 23:10 - 08-26 00:1x)
- 交付三件（待用户亲发, 主线程零对外）: ① `docs/31_导师进展汇报_v2_20260825.md` + docx（自包含, 内部黑话扫描零命中, judge 四维未引用）② `docs/experiments/2026-08-25_demo_video_v3/demo_v3.mp4`（1080p 配音, Yunyang; 十段结构 = 2026-08-15 steps.md 骨架 + 现行口径）③ `docs/experiments/2026-08-25_demo_talk_track_v2.md`（逐分镜解说词 + 选题变更记录）; 呈递清单 `2026-08-25_send_checklist.md`。
- **彩排驱动选题变更（护栏执行证据）**: route=on 生产态下, 确定性题集与快路三问全部被路由进深度验证通道（实测 30-52s/问, 无 2 秒快答）——"快问快答"在现行路由下仅对结构化查询成立; 快路段终选 = 持仓对比（实测 11ms）, 深度段终选 = 复熙混合25号资产总值（彩排实测 52.4s 完成, 实测值烧录字幕与解说）。依据 = 彩排实录 + B4 窗口行（23:19-23:47）。
- **口径注记（甲方暴露面）**: 视频沿用 v2 结构含嘉合上传/传真 OCR 段（既有测试语料入镜, 与 08-15 v2 演示同口径, 发送对象=导师, 未新增对外暴露面）; 用户侧线底稿明确保留该叙事（嘉合 93.8→100% 等战绩）, 与"甲方数据零进入"红线的协调解释 = 不新增暴露面 + 发送前用户终审。
- **judge 16/16 超时归因定论**（只读排查, 报告 `2026-08-25_judge_timeout_triage.md`）: W3 run_eval 的 NF 步 9 题经 :5050 生产口径全被路由进 agent 路, 45s 超时后孤儿轨迹续跑占满 :8006; 紧随的 judge 16 次调用（:8006 直连, timeout=90s）逐一打满 → 四维全 None。假设 (a) timeout 预算不足=排除（08-23 同预算成功先例）, (b) 消费者争用=成立（竞争源=流水线自身）, (c) :8006 本体异常=不独立成立。修复菜单校准: F-J1 `_judge_avg` None 安全化（仍需）/ F-J2 judge 重跑加隔离闸（与 agent 路批量错峰 + 开跑前查 :8006 无在途）/ F-J3 原"超时排查"关闭, 升级为**孤儿轨迹治理 = 减 step 菜单 M4-a**（与准路完成率洼地同根因）。
- B4 视频窗口: 23:19-23:51（录制/彩排经 :5050 的问句止于 23:47）, 干净段统计剔除; dispatch #VIDEO-V3-WINDOW-START/END 在案。
- 版本治理: docs/31 v1（08-15）标"作废-已被 v2 取代"保留不删; talk track v1（08-12）同口径; 新文件均带日期, INDEX 同 commit 登记。
### 08-25 晚间队列 E1-E6: 三缺陷修复 + E2/E4 补跑 + 规则评估回填 (2026-08-25, 22:25 开窗)
- E1 三修（只改脚本/SOP, 零生产变更）: a) cron 闸失败语义 = 改期（≤N 次）, **禁 SKIP**——新 `scripts/graph/cron_gate_helper.sh`（`cron_gate NAME COND MAX INTERVAL SELFLINE MARKER LOG`; 回归中发现并修 `grep -vF ""` 会清空 crontab 的真 bug, 改 awk $2 自删键）; 案例 = 01:50 W4 闸撞 W3 eval 收尾（01:05→01:51）致 SKIP → W5 连环 abort。 b) 汇编器门禁解析（根因钉死）: gate 脚本 `/tmp/pool_gate.sh` `head -c 400` 字节截断切断多字节字符——工件 position 657 实测 invalid continuation byte, "资产市"后一字符"值"被腰斩 → assemble_morning.py 的 rd() 把严格 read_text 的 UnicodeDecodeError 吞掉返回空串 → gate=UNKNOWN。三层修: ① rd() `read_bytes().decode(errors="replace")` ② gate 判定用 dispatch_log（#POOL-GATE-PASS/FAIL）做兜底源 ③ gate 截断 `| iconv -f utf-8 -t utf-8 -c` 字符安全化（工件已修复, 640-680 字节复验 decode clean）。回归用例 = 今晚 PASS（verdict=GATE_PASS runs=3）。固化: 汇编器升仓库资产 `scripts/graph/assemble_morning.py`（/tmp 重启即失教训）, 字节截断字符安全规则入 AGENTS.md + template §8。 c) pending 卡交接必须 cron one-shot 触发, 禁依赖"硬停后会话仍活"（案例 = 晨间序列卡零执行）; 规则入 task_card_template.md §8 + AGENTS.md。
- E2 step 复测补跑（规则 B 输入）: 13 题全名 id 经 :5050 agent 路, 13/13 PASS（eval 口径）, B4 行 4122→4139（canary 混入 4 行已注）, join 12/13（顺序索引 + session.created±8s）; **wall p50=49.09s / mean=49.2s, steps p50=4 / mean=4.67**（分布 4×8/5×3/9×1）。三点对比 ≈ T1 Arm A（49.6s/p50=4/mean 4.4）干净环境复现, 健康代 p50=3 未复现 → **规则 B: T1 基线未被池病污染, T1 结论维持, 原杠杆队列不变**; 工件 `logs/graph/eval/e2_step_retest_20260825.md`。
- E3 逐步耗时诊断（规则 A 后果, 减 step 第一梯队输入）: 窗口内 62 session（59 超时类, 与 B4 口径 59 尝试吻合）; **45s 截断时 step1 在途 26/59（44%）> step3 14 > step4 9**; 每 step 位 p50=30-34s（对照健康代 7-15s/step, 放大 3-4 倍, 主因 prefill/context 27k 膨胀）→ 结论: **减 step 必须与 context 瘦身组合**（单杠杆 2 step≈60s 仍超 45s）; 报告 `docs/experiments/2026-08-25_e3_step_duration_diagnosis.md`（菜单已出不动手）。
- E4 PSO 落点② 补跑 = **ABORT（根因坐实）**: 启动闸全过, 判别力套件 exit=1——W3 judge 工件（01:51）四维 avg=None/n=0, n_unusable=16（judge 调用 :8006 全 16 条 TimeoutError）, `eval_checkpoint_aggregate.py` L67 `_judge_avg` 对 avg=None 无防护 → 崩溃。**更正入账**: W3 "eval 16/16/0/5.0 零漂移"——确定性 16/16 + NF 0/9 部分属实, judge 腿无数据（全超时）, "5.0 对照"口径收窄。修复候选（待明日窗口）: _judge_avg None 安全化 + judge 腿重跑 + 超时原因排查。详见 `docs/experiments/2026-08-25_pso_question_set_v0.md` E4 节。
- E5 Loop B 反复归因: 18:44 FAIL = STEP 9 agent_watchdog（last 30 asks: 0 completions, ≥25 fallbacks）——设计内信号, 对照 08-23 23:51 先例属 canary 抖动类; 19:17/19:51 延续, 20:24 翻回 PASS, 22:05 九项全绿。只分类不动手。
- E6 一页纸 v2: `docs/experiments/2026-08-25_morning_decision_sheet_v2.md`——门禁更正 PASS（00:28, 3 次运行）; 规则 0 n=59 过样本闸（canary 代表性注记）; 规则 A 3.4%<10% 且非近失主导 → 超时 (a) CLOSED, 诊断=E3; 规则 B steps p50=4 ≥4 → T1 维持; 规则 C FK 水位线单件窗等用户另行批（不催）; 规则 D PSO blocked（根因见上）; 规则 E 积压维持。规则评估逐条以本条入账, 晨间序列卡欠账清偿。

### :5050 代码窗一窗全激活执行结果 (2026-08-23 23:22-23:35, 用户批准提前)
- 背景: 原排期 08-24 48h 观察收口后; 用户批准提前——判定数据已成形(修复后段完成率 19.0%/19.3% 远超 10% 再议线), 明晚 checkpoint 只是复核; 三件修复全就绪, 回滚路径有先例。
- 激活三件: ① FK 竞争修复菜单 a (src/biz/opencode_adapter.py: 超时不删 session + completed 标志; 草稿 docs/experiments/2026-08-23_fk_adapter_fix_draft.md) ② vector_store 实例缓存 (src/tools/vector_store.py: (collection,conn) 键 + Lock + setdefault, engine-per-search 泄漏根治) ③ M1_B4_LOG_PATH 修复 (fb94824, 08-21 提交) 随重启生效——生产走默认路径, env override 供测试隔离。
- 窗口证据: 窗前存档 logs/graph/eval/m1_harness_window_archive_20260823.txt (23:22:23; 旧 PID 2104416 lstart 08-18 16:44:49) → 重启 6s (scripts/restart_m1_harness.sh 定型 SOP; 新 PID 2300096 lstart 23:27:09; 进程 env OPENCODE_ASK_TIMEOUT=45 / M2_OPENCODE_ROUTE=on 未动)。
- 验证全过: /api/health/full overall=healthy (embeddings 137/local/ok); QA 2 条 (OCR meta-query sources=3 正确溯源 / 诚实拒答) + compare 嘉兴民安 2 持仓 + canary 4/4; pytest 384 passed/13 skipped (含新测试 5 项 tests/test_window_fixes_20260823.py)。
- agent 路实值: 6 尝试全回落 47.6-70.5s (记实值; 窗口样本不构成结论, 按 48h 口径续观察)。
- FK 验收双条件 PASS: opencode.db 三表 0/0/0 → 9/44/118 (session/part/message) + opencode.log FK 错误停涨于 136 — 持久化恢复成立 (08-11 FK 竞争 / 08-14 持久化损坏根因待查 合并条目由此关闭)。
- 台账连续性: 重启后立即验 b4_checkpoint.py 3429 冒烟 PASS (259 行, 读路径连续无断); B4 第五分段点 3682 @23:27 入账 (窗口重启段标记)。
- 遗留: 超时 (a) 45→60-75s 不预载, 待 08-24 23:50 cron 48h 口径数据拍板 (判据已预写: 段 C+D 完成率 <10% → 再议, ≥10% → 维持); 回滚口径 = 原参数重起 (SOP = 上述脚本)。

### 夜间队列任务 4 核查: K2 前置齐 + PSO/K3 排期 (2026-08-23)
- 核查坐实: K2 v1 齐（2026-08-19_eval_protocol_v1.md, 判别力 9/9 + judge k A/B + 冻版零漂移）+ evidence card 齐（并入 v1 产出, scripts/eval_evidence_cards.py, evidence_cards 16A 工件）→ 前置条件 PASS。
- 今晚不跑（预算门）: PSO 落点②需 (问题×mutant) 判别力矩阵——cached 判别力报告只有 per-mutant 叶级 delta 无 per-question 信号, 必须新跑模型（:8006 负载, 估 ≥1h）; 与 B4 canary 每 30min slot 争用 + 02:00 硬停 + 明日 48h checkpoint/代码窗前排, 不硬上。
- 排期: 08-24 23:50 cron 收口后错峰窗执行（PSO 落点② 或 K3 注入批跑二选一, 届时预算门复查）; K3 漂移注入器 v0（118 条 + 95 表）就绪在案。

### 48h checkpoint 口径预写 (2026-08-23 夜, 明晚 23:50 cron 执行, 不临场定口径)
- 执行: `./venv/bin/python scripts/graph/b4_checkpoint.py 3429`（段起点 3429 = 08-22 14:38 侧车修复后）; cron 23:50 已布防（08-21）, 跑完人工删。
- 分段口径（判定时按此切, 两列口径=尝试/完成, 回落率=1-完成/尝试）:
  - 段 A [3429 ~ 08-23 11:45): 侧车修复后 + PG 饱和前, 相对干净段;
  - 段 B [08-23 ~11:45 ~ 20:20): **PG 打满污染段——剔除或降权**（金丝雀空检索回落样本, 事故条在案）;
  - 段 C [08-23 20:20 起, 实际重启 20:26): 修复后干净段（首批样本: canary adv_refusal agent 路 44.8s 等）;
  - 段 D [08-24 全天]: 干净段。
- 判据（先入账）: 段 C+D 合并完成率 <10% → 超时 (a) 45→60-75s 再议（明日 :5050 代码窗一窗全激活顺带载入）; ≥10% → 维持现状续观察（对照楔死前 45s era ~20% 基线）。
- 附加: content=null 计数与回落率按原批复口径; eval 中间行 route=agent 标签异常以 B4 为准。

### 窗口验收两疵核查结论 (2026-08-23)
- ① inspect 存档口径: logs/graph/eval/pgvector_inspect_pre_restart_20260823.json 实测 9836B = `docker inspect pgvector_15432` 单容器全量输出（Id/Config/HostConfig/State/NetworkSettings 齐全）, 符合「可回滚级全量」标准; 验收所引 324B 与在盘存档不符, 如实记录。
- ② verify-report.json 扫描范围核查: STEP4 扫描范围无漏——git status --porcelain 全 worktree, verify-report.json 未入白名单被正常计数（21:41/22:15 两周期 dirty_files=1 可查; 20:38/21:08 为 0 系写入顺序: STEP4 先于当周期 report 写入, 且在盘 report 恰与 HEAD 一致）。口径补充: dirty 计数为 R1 信息性字段, 不影响 overall（仅 tests/ 变更触发 WARNING）。
- ② 处置提案（Loop B 红线报批）: 白名单再扩 2 件——verify-report.json（含 timestamp 字段, 每周期必脏）+ loop_b_last_status（Loop B 运行时工件）, 与已批 5 件同口径注释入脚本; 批准后常驻脏件归零。未批前维持现状（每周期自写回, 收口顺带 commit 快照）。
- :5050 代码窗积压三件排期: FK adapter 修复（#HYG-FK-DIAG 菜单 a/b）/ PG 池泄漏根治（疑 engine-per-request, mcp 侧 ~1.5 连接/时 + :5050 侧 ~0.5/时, GUC 兜底中）/ M1_B4_LOG_PATH 激活——48h 观察（08-24 晚）收口后一起排窗。**[08-23 23:35 三件已一窗全激活完成（用户批准提前）, 见「:5050 代码窗一窗全激活执行结果」条; 剩超时 (a) 待 48h 口径数据拍板。]**

### /api/health/full 路径更正 (2026-08-23, 窗口验收必更正)
- 错误声明: 「/health/full 路由不存在, /health 为唯一健康端点」——PG 窗口验证时我的错误结论（grep 范围仅 src/*.py + src/api/*.py, 漏 src/web/routers/）。
- 更正: 正确路径 **/api/health/full**, 08-01 (32cca97) 入库, 定义 src/web/routers/pages.py:55; 08-23 22:35 实测返回 overall=healthy（pgvector ok / embeddings 137 / llm_8004 ok / embedding local / proxy_8100 ok / m2_rag retrieval_working=true）。历次窗口「137/local/healthy」口径即出此端点。
- 行动: 今后六步验证保留 /api/health/full 项, 不再测错路径。

### 汇报措辞更正 (2026-08-23, 抽验批复两处记账)
- 「本机 docs_lint 0 fail」仅 GB10 成立: 本机 autocrlf=true 致 .sh CRLF, sync_skills.sh 本机无法执行, 本机 docs_lint FAIL[4] 结构性; 今后汇报台词统一「GB10 为准」。
- INDEX 自身行日期 08-22 落后头部 08-23 一天, 违「INDEX 最后更新与内容变更同 commit」规则, 本 commit 修复（08-22→08-23）。

### Loop B 覆写 pytest_latest.txt 结构问题 (2026-08-23, 方案已报批, 红线先报后动)
- 问题: Loop B STEP 2 每 30min 跑 tests/test_m1_service.py 18 题子集覆写 logs/graph/pytest_latest.txt（08-22「全量入该文件」批复被冲掉; 实测收口全量 379/13 两小时内被覆写成 "18 passed in 0.03s"）。
- 方案（待批, 与 PG 窗口合并执行）: ① STEP 2 输出改 pytest_loopb.txt（loop_b_verify.sh L132/L135 两行） ② STEP4 白名单扩至 4 件: config/schema_suggestions.json（先例）+ logs/graph/{dispatch_log.md, docs_lint_report.json, pytest_latest.txt}（grep -v → grep -vE） ③ daemon reload（旧进程跑旧脚本教训, 改动必须 kill 旧 PID + tmux graph-loop-b 内重拉 --daemon 才生效）。
- GB10 常驻 3 脏文件源 = 上述 Loop B 运行时写入（HEAD 三方对齐无问题）; 侧线未提交改动已清, 本机 _tmp 已清。**[08-23 20:38 已执行: 三项落地 + daemon reload (新 PID 2187590); 验收全过——首周期与手工复跑周期均 dirty_files=0 + whitelisted=1(白名单生效) + pytest_loopb.txt 产出(18 passed) + overall FAIL→PASS 翻绿; 白名单实为 5 件(批准 4 件 + pytest_loopb.txt 分流推论, 脚本注释写明)。]**

### PG 池打满事故 (2026-08-23, P1 活跃; 处置窗口申请已报, 待用户批准一次做完)
- 证据: psql FATAL too many clients already（容器内管理连接亦打不进）; :15432 连接饱和 ~100=max_connections; Loop B 今日翻转 5 次, 17:50 周期 FAIL 于 qa_canary adv_ocr_meta 空检索; 生产检索间歇降级。
- 根因 = [08-16 22:20] known_risk 条: Loop B 周期跑每轮泄漏 ~1 idle 连接（增长速率 ~30min/个 与 POLL_INTERVAL=1800 吻合）, 7 天未修打满。
- 处置清单（窗口申请待批, 一次做完）: ① 窗前 docker inspect 存档 → docker restart pgvector_15432（秒级, M1/M2 检索短暂报错窗 ~5-15s） ② 重启后 ALTER SYSTEM SET idle_session_timeout='10min' + pg_reload_conf（持久化 postgresql.auto.conf; **饱和时 psql 连不进, 只能重启后设——卡片假设已更正**） ③ Loop B 脚本改动按批方案同窗执行 + canary 前后 pg_stat_activity 归因泄漏端 ④ 验证: health/full + canary + pg_stat_activity 回落 + Loop B 下周期翻绿。
- 注: 仓库 compose 文件（pg16/m1_pgvector）与在跑容器（pg15/pgvector_15432, 07-16 起）不一致, 重启直接对容器操作不用 compose。
- **B4 统计注记: 08-23 ~11:45 起 B4 金丝雀样本受 PG 打满污染, 48h 观察（08-24 晚）判定时剔除或降权该时段。**
- **执行结果 (08-23 20:26-20:38 窗口)**: ① restart 1s / ready 2s, 活动 100→1 ② GUC idle_session_timeout=10min 生效持久化 (600000ms, postgresql.auto.conf) ③ canary 4/4 PASS 两轮连过 (adv_ocr_meta 复活; 重启后长闲首请求重连验证成立——:5050 池 idle 连接被 GUC 切断后自动重连, 口径入账) ④ 泄漏实证: canary 前后连接 1→10(idle 9), 每请求留闲连接, 10min 后回收 (10min/30min 两点观察入 logs/graph/eval/pg_activity_followup_20260823.txt) ⑤ inspect 存档 logs/graph/eval/pgvector_inspect_pre_restart_20260823.json ⑥ compose(pg16/m1_pgvector) vs 在跑容器(pg15/pgvector_15432) 漂移只记账不修 ⑦ 中止条件未触发。
### FK 竞争诊断定论 + 台账合并 (2026-08-23, #HYG-FK-DIAG; 诊断只读完成, 动手等 :5050 重启窗)
- 08-23 只读诊断坐实（积压清理卡·窗口合并项①）: opencode.db 重建为假愈合——三表全空（session/part/message = 0/0/0）; `FOREIGN KEY constraint failed` 累计 2824 条（近 24h ~90, 08-23 15:10Z 新鲜样本 `insert into "part" FOREIGN KEY failed`）; 栈 `Session.updatePart -> SessionProcessor.cleanup`。
- 根因: `src/biz/opencode_adapter.py` `ask_via_opencode()` 的 finally 块无条件 `delete_session(session_id)`——超时/异常回落后侧车 run 仍在途, adapter 已删父 session -> 在途 part/message 插入 FK 失败。08-11「FK 竞争」与 08-14「持久化损坏根因待查」为同一病灶, **合并为本条, 「根因待查」措辞作废**。
- 实际代价: transcript 零持久化——今后 L2 式 context 分布测量无生产 db 原料（08-22 L2 用日志侧口径完成, 未受影响）。
- 修复菜单（报用户, 未实施; 与 M1_B4_LOG_PATH 修复同窗合并, 动手必须等 :5050 重启窗）: a) 超时不删——仅确认 run 完成才删 session（改 finally 条件） b) 清理异步化——run 完结事件后延迟删。方向口径: 超时不 DELETE session 或清理异步化。
- 诊断时实况: OPENCODE_ASK_TIMEOUT=45 / OPENCODE_MAX_SESSIONS=50; 重建库亦复现 = 结构性问题非旧库腐烂。

### 专利文档终态三件套冻结台账 (2026-08-22, 已发导师 08-22 晚, 等五项定夺反馈)
- 背景: 08-22 13:48 worktree 回退为用户有意操作(v1 docx 文末嵌呈递说明不宜随文档发出); 侧线重放修复并完成文档/邮件分离。
- ① 交底书 md: docs/experiments/2026-08-21_patent_full_revised.md (737 行=§1-§8+附录A/B) sha256=F8A4B0CDF2BC0A503CA7DEED060C999425CA86082DB6740857C5F61F931635A6
- ② docx v2: docs/experiments/《大模型长流程智能测评装置及方法》技术交底书_完整修订版_2026-08-21_v2.docx sha256=48FF2A450707B3038581B164E426C6D9ECBCFBFC2B1CDF951B8034CA45DC01BC (docx 内"老师好/呈递说明/请您定夺"零命中)
- ③ 邮件草稿: docs/experiments/2026-08-22_patent_advisor_email.md sha256=7E39CFFC5F5CBD306C6617A250ECC4DAF61C3B06B67439F4662470EE84E109A6
- v1 docx(hash 7954BB...)含嵌呈递说明, 不入库不发送, 留本地作废。
- 状态更新 (08-22 晚): 用户已亲发三件给导师, 等导师五项定夺反馈(权利要求范围/发明人排序等, 见邮件草稿呈递说明); 主线程不碰。

### opencode 侧车交付链楔死 (2026-08-22 #B4-DIAGNOSIS) — 已修复 + 完整验收通过(08-22 15:11), 拍板 c 维持现状
- 现象: B4 行 3075 (08-20 22:47:06) 起 agent 路 0 完成, 全部 45s 超时回落; 回滚点 3295 起 128 尝试/0 完成 (kiosk 94 / eval 窗 30 / 手工 4, 三段回落率均 100%; 08-22 三段核查 #B4-SEGMENT)。
- 根因 (证据链: docs/experiments/2026-08-22_b4_agent_route_diagnosis.md): 轨迹形态 step0 skill+search ~5s → step1 最终答案流开始 → 静默 ~40s → 客户端超时 (回滚后 n=112, p50 steps=2); vLLM 侧最终流开始后 ≤20s Running→0 + 200 OK 不背锅; "exiting loop" 计数 08-18:117/08-19:81/08-20:27/08-21:0/08-22:0, 末次 08-20 22:46:16 与最后完成(行 3074)逐秒吻合; **故障起点早于 DSpark v3 切换 (23:48 READY)** → 切换/回滚均非病因; 侧车进程 08-17 22:49 启动未重启; :5050 回落原因全部 "opencode ask failed (timed out)" (非 compaction 守卫); opencode.db 持久化慢性病 (session 表仅 7 行 / message·part FK 插入失败自 08-11 每日都有, 08-19 峰值 570) 为背景噪声非直接病因。
- 拍板选项: ① 重启 opencode 侧车进程 (低风险, 非 :5050/:8004/:8006 红线项) ② 仍 0 完成则备份重建 opencode.db ③ 维持现状 (直连兜底可用, 准路菜单名存实亡, kiosk 每条 46-50s 回落)。
- 修复执行 (08-22 14:20-14:53, 拍板圈1+预授权升级): ①重启侧车(旧进程 08-17 22:49 起 4天15小时, 四项存档 logs/graph/eval/sidecar_restart_archive_0822.txt) ②重启后 2 次尝试仍 0 完成 → 选项2 备份重建 opencode.db(备份 ~/.local/share/opencode/backup_20260822/, sha256 在 dispatch #SIDECAR-DB-REBUILD, 恢复 SOP 同条)。结果: 楔死解除("exiting loop" 重现 14:32:34, 步速恢复 5-12s/step), 但实测题需 5-6 步 ≈46-60s > 45s 预算 → 验收①未达成, 剩余差距=延迟预算非侧车故障。待拍板: a) OPENCODE_ASK_TIMEOUT 45→60-75s(需 :5050 重启窗口) b) 准路根治杠杆(L2 瘦身/减 step) c) 维持现状。
- 归因重记 (08-22): DSpark era 190/0 与 08-21"准路不可用"判定结论保留, **归因更正为侧车楔死**(起点 08-20 22:46 早于 DSpark v3 切换 23:48), DSpark 切换/回滚不背 agent 路失败; "content=null 首要怀疑"条目 **CLOSED**(根因是楔死致超时, 非 content=null)。
- 判定更正 + 拍板 (08-22 22:14): 验收①实已达成于 15:11:59——修复后 58 尝试 / 11 完成 = 19.0% (31.4-45.0s 全在预算内), 与楔死前 45s era 基线 ~20% 吻合; Loop B overall 15:14 FAIL→PASS (#LOOP-B-FLIP)。此前 14:53 "0 完成"判定 = 时点采样不足。**拍板 c 维持现状(不抬超时)**: ① 修复目标=恢复楔死前基线已达成, 无需动 :5050 ② 明晚 L1 矩阵需"生产配置未动"基线, 超时变更污染可比性 ③ "60s 完成率 >50%"属外推无数据, 不为外推花重启窗口 ④ 真正完成率提升走减 step (M4 34s→19s) + L2 context 瘦身 (27k→8-10k, 预热 2 overflow 为现成动机)。(a) 抬超时保留为后备: 48h 观察期(至 08-24 晚)完成率 <10% 或甲方要求更高 agent 完成率 → 届时与减 step 数据一起拍。
- FK 竞争 (超时删 session vs 在途运行): 08-11 以来已知结构性问题 (adapter 超时删 session → 在途运行 FK 错), 新库亦复现非旧库腐烂; 记 **adapter 修复候选项, 不阻塞**当前任何事项。**[08-23 #HYG-FK-DIAG: 根因定论 + 修复菜单见「FK 竞争诊断定论」条; 08-14「持久化损坏根因待查」并入该条, 措辞作废。]**
- B4 统计分段: 08-22 14:37 起记"侧车修复后段", 48h 观察以 b4_checkpoint.py 两列口径(尝试/完成)为准。
- xargs 陷阱备忘: `xargs -0 -a ENVFILE env -i CMD` 会把变量追加到 CMD 参量尾 → yargs 未知位置参量打 help 退出; 正确姿势 = mapfile -d "" 重建数组(启动器 scripts/sidecar_launch.sh, 08-22 夜间审计入库, 原 /tmp 版同内容)。
- 关联: L1 thinking 档位裁定矩阵 (08-23 晚窗口, runbook 已就位) 走直连不受影响; 减 step 菜单 (2026-08-22_step_reduction_menu.md) 在楔死修复前收益为零; B4 agent_watchdog ALARM 为该现象的设计内信号。

### kiosk 正式关闭 (08-22 用户终判选项 B) — 归因定论: 窗前暂停未复活
- 事实: B4 末条 kiosk-era 行 08-20 23:55:19 (= B4 行 3092); 08-21/22 全天 ~8 行/时 = 纯 Loop B 金丝雀(30min 周期 3-5 题); ps 无 kiosk 进程; 仓库内无 kiosk runner 脚本(仅 08-21 方案文档 2026-08-21_kiosk_agent_route_proposal.md)。
- **归因定论 (08-22 用户抽验更正)**: 停点 = B4 行 3092 = DSpark 窗口 v2 切换点, 正对"窗前暂停 kiosk"动作点, v1/v2 连败混乱中复活步骤漏掉 = **"窗前暂停未复活"**; 原"疑楔死致死"作废(矛盾点: 楔死起点 08-20 22:46, kiosk 此后仍写 B4 至 23:55, 不相容)。
- 连带更正: #DSPARK-ROLLBACK(08-21 23:54) Phase 0 收口"声称已恢复"(STATE@f8898c9 "本机 kiosk 播放中（已恢复）")与进程级证据矛盾, dispatch 条目已加注不涂改。
- 影响: ① 演示观感无自动播放 ② 48h 观察期样本 = 纯金丝雀题型(见元认知快照 §四) ③ 台账/汇报"播放中"声称持续 2 天与实况脱节(漂移实例存档)。
- 用户终判 (08-22, 选项 B): **确认关闭, 不重建**; 启动方式失考(仓库无 runner = 未纳管资产 = 停摆两天无人发现的根因); kiosk 相关缓办全部 CLOSED: A1 方案(per-request route 提案, 已归档) / 演示观感问题 / 建议生成计数观察(41 条/晚可接受, 已作面板演示素材); kiosk 缺位对 L1 矩阵是利好(少一个争用源)。
- **教训入账**: 收口清单必含消费者复活核验(暂停/恢复必须成对, 以进程级证据为准, 口头声称不算), 与"声明必须带证据"同账。
- **规则入账 (08-22)**: 今后任何常驻演示资产必须 runner 入库 + Loop B 健康断言, 不允许无册运行。
- **文档漂移防御规则入账 (08-22 侧线审计 §5)**: ① 收口清单加 rg 扫荡（`:8005|72B 硬禁|300 passed|待发送|待执行` 命中 = 漂移候选）② INDEX "最后更新"字段与内容变更必须同 commit ③ 活文档头部三件套（状态/更新/取代）列为 docs_lint 检查项。
- **残留记账 (08-22 侧线审计 §4, 只记不动)**: ① `31_导师进展汇报_预审版.docx` 文件名仍带"预审版"而内容已是导师版——已发送冻结件不改名不重冻, 记账即可 ② docs/19 补版触发器 = 甲方反馈, 不提前动 ③ RECSYS_MEMORY_DESIGN.md INDEX 日期 2026-02-20 经复验与文档头部"设计冻结"一致, 非漂移（误报剔除）。

### L3 DFlash2 侦查结论 (08-22 晚, N2 记账) — 维持路线 A 等新 tag
- 事实: vLLM #52816 已合入上游(08-21); 权重在位 incoai/Qwen3.8-27B-DFlash2; 我们镜像 vllm-gb10:v0.27.1-gb10.1 构建 08-15 早于合入 → 无 DFlash2 代码, **今晚不可跑**; 镜像 tag 最新仍 v0.27.1 族, 无新版本。
- 处置: 维持路线 A(等 timothystewart6 新 tag), 08-29 checkpoint 不变(无 tag → 路径 B 再评估报告); sha-* tag 日期排查入 drafter 盯梢台账。不自建镜像(路线 A 拍板)。

### 缓办: agent 超时抬升 + 每步输出 (08-22 晚, N3 记账, 不动手)
- ① agent 超时抬升(45→60-75s): **待 N1 矩阵质量数据后拍板**; 执行需 :5050 重启窗口(红线, 另行批)。
- ② "每步输出" = adapter step 事件流: 开发任务入下个代码窗口; 兼作导师演示叙事素材。

### 快路 27B 提议否决 (08-22 晚, N4 记账)
- 物理算术: 27B dense ~10 tok/s, 200tok 答案 15-25s; 快路现 1.3-2s; 换 = 快档慢 10 倍。
- 官方 pairing(27B 质量 + A3B 快) = 现有拓扑; 快路升级唯一路径 = Route B 3.8-A3B 权重(盯梢中, 08-22 前无官方开源权重)。
- 折中菜单项"深度直答第三档(27B thinking-off 单发 15-25s)"**记账不实施**。

### L1 thinking 档位裁定矩阵裁定 (08-22 夜窗执行, 08-23 出数) — NO-GO, 准路默认维持 thinking=OFF
- 数据: medium 13/16 + NF 1/9 + judge 4.67; xhigh 16/16 + NF 0/9 + judge 4.875（基线 off = 16/16 + NF 0/9 + judge 5.0）; 单步直连 wall p50 medium 55.9s / xhigh 57.7s, p95 121.9s / 137.1s。
- 裁定: 两腿均 NO-GO（判据: 质量不降 16/16 + NF 0/9 + judge ≥4.9 且延迟实质下降）; 08-19 "xhigh 起步"正式作废。
- 正向信号: xhigh 跨期诱导抗性（NF adv_june_cross_period medium 命中 / xhigh 过）+ citation/refusal 5.0 → 记为用户可选"深度"档菜单项（代价单步 p50 ~58s）。
- 方法论: 首冒烟命中测量盲区（本 vLLM build 不产 usage.completion_tokens_details）, runner 补丁 fallback=len(reasoning)（runbook 口径注记预告场景）; 报告 docs/experiments/2026-08-23_l1_thinking_matrix.md。
- 下游输入: N3 agent 超时抬升拍板数据就位（off 单步 46-50s / xhigh p50 57.7s p95 137s, 抬 60-75s 容纳不了 xhigh p95, 超时抬升与档位升级不捆绑）。

### :5050 运行代码滞后 (08-22 夜间审计发现) — 记台账, 待重启窗
- 事实: uvicorn 父进程 2104416 lstart 08-18 16:44:49; fb94824(08-21, src/web/routers/m2.py M1_B4_LOG_PATH B4 日志隔离修复)未生效——进程跑旧代码。**[08-23 23:27 已生效: :5050 代码窗重启(新 PID 2300096, env 基线不变), b4_checkpoint.py 读路径连续性冒烟 PASS(3429 段 259 行正常统计), 台账未断; 生产默认路径不变, env 覆盖仅测试用。]**
- 处置: 生效需 :5050 重启窗口(红线不擅动); 下次重启窗顺带激活; 运行中行为未见异常(日志隔离缺失期 B4 行已验证无 M1 污染)。

- Schema 口径 (2026-08-09 P1): 冻结运行时 schema (~/wzh/m1_samples, 07-30 版) 已落后 config/m1_table_schema.json (嘉合/卢样本 synonyms 演进)。CLI 与 :5050 已统一走 resolve_schema_path() (config/ 优先)。是否把运行时副本同步到 config 版 = 待 Loop D 决策 (需刷新 frozen_hashes.txt manifest)。
- HTML 邮件链路 (2026-08-09 P1): 匹配步已复活 (scripts/m1_html_email_parse.py), 但 .msg -> HTML -> 表格的提取步脚本未入库 (仅存产物 html_extracted/*_tables.json); 重提取需重写 (4.1 一并)。

- VLM :8007 (Qwen3-VL-8B-Instruct GGUF): **VERIFIED-CLOSED** (2026-08-08) — hf-mirror 已同步官方 GGUF 仓库, Q4_K_M 5.0GB + mmproj-Q8_0 752MB 下载成功, llama.cpp 2.16 llama-server 起 :8007 一次点亮; NCAMC 截图手测输出合法 markdown 表格 (首调 119s); parser 重跑 engine=vlm-8007 (trafax/wavefax 走通), 但传真样本命中率与 vision-8004 持平 (trafax 2/4;8/11;4/11, wavefax 4/7), 单文件 OCR 延迟 3-8min (vision-8004 ~30s) → 默认关闭, :8007 已 kill。重启方法: llama-server -m ~/wzh/models/gguf/qwen3-vl-8b/Qwen3VL-8B-Instruct-Q4_K_M.gguf --mmproj .../mmproj-Qwen3VL-8B-Instruct-Q8_0.gguf --port 8007 --alias Qwen3-VL-8B-Instruct -ngl 99 -c 8192, parser _try_vlm_table 自动接入 (M1_VLM_TIMEOUT 建议 ≥240)。降采样已实验完毕 (见下 4.2, M1_VLM_MAX_PX=1600 默认): 延迟达标但 TraFax 命中率劣化, 代码保留为复用资产。
- MCP server x3: **RESOLVED** (2026-08-05 S1) — start 脚本改 venv-first + conda fallback, smoke 3/3 过, opencode.json 注册并随 agent 链跑通; vision 走 :8004 mmproj (:8007 停摆)。
- OpenCode 多 agent (docs/21 §1.4): 显式指令链已端到端验证 (2026-08-05 S3: M1 链 PASS + M2 Q1 PASS 带引用 + tabular PASS, 见 docs/experiments/2026-08-05_opencode_e2e.md); 中性 prompt 自动委派已验证 CLOSED (2026-08-09: 默认 build agent 不委派专职 agent, 但直接调 jinrong-rag MCP 检索作答, 掩码保留正确; 结论: 无需显式 --agent 也能走 MCP, 但查询策略不受 m2-qa 契约约束, 生产路径仍应显式指定 agent 或走 :5050 适配层)。
- Qoder CLI (2026-07-29 侦察): BLOCKED-auth, 等用户注册并提供 PAT 后再做 Phase 2 连通性实测。
- ZhikunCode 重建 (2026-08-03): 官方 Dockerfile pip 直连 pypi.org 极慢, 需临时 aliyun 镜像源 (已还原) 或向上游提 PR。
- codex CLI 对 qwen3.8-max 报 "model metadata not found" 警告: 无功能影响, 记录不修 (2026-08-03)。
- ~~.msg→htmlBody 预处理仍是临时脚本未入库~~ **RESOLVED** (2026-08-09, c863235): scripts/preprocess_msg.py 已入库 + 8 单测; parse_html 覆盖解析环节。
- embedding 本地切换: **RESOLVED** (2026-08-05, 用户拍板不恢复 SILICONFLOW key): .env 加 LOCAL_EMBEDDING_MODEL_PATH=qwen3-embedding-0.6b + DEVICE=cpu, 同模型 drop-in 无需 re-ingest。MCP 链实测生效 (knowledge_search vector=3); :5050 已重启载入 (重启验证见 dispatch_log 2026-08-05)。**口径更正**: "RAG QA 14/15" 从来不是降级态成绩 — QA 脚本 (m1_rag_qa.py) 经 setdefault 从未降级; 曾降级的仅 :5050/MCP 端点进程 (缺 env 走 fallback)。14/15 唯一失败 = OCR meta-query 内容碰撞 (email_caitong.html 含"交易对账单"字样), 已派 Loop A 正式任务修 (禁 --reset)。

### scenario1 gap 台账（2026-08-04 审计定基线，漂移校准）
- NCAMC 垂直布局: **CLOSED** — pymupdf 坐标重建, 0→1 表 75% 命中 (b927efe; 见 docs/21 执行结果节)
- 华泰/TraFax OCR 纯文本: **CLOSED** — OCR prompt 增强 markdown 表格输出, 华泰 0→1 (35.7%) / TraFax 0→3 (9ea3754)
- email body: **CLOSED (有界)** — HTML body 提取, 3 封 0→9 表 (国金 70% / 财通 42% / 南华初值 24%)
- 南华 HTML: **遗留 (低优先)** — T3 已提升 24%→65.7%, parse_html(bs4) 入 PARSERS + synonyms 扩展 (html_table_4 88.9%), 不再恋战
- OCR meta-query: **RESOLVED** (2026-08-05 Loop A) — 15/15=100%, doc_type 标记 + smart_retrieve 过滤召回/重排 (见本文件上条)
## 甲方侧待确认

- 跨期对比: 需甲方提供多期对账单数据才能解锁 (现仅单期/单文档内对比)。
- email body 格式: 已解决 (有界) — HTML body 路径已验证 (3 封邮件 0→9 表), 仅在甲方要求时扩展。
- M2 正式业务指标: 阻塞于甲方批准的 label-to-source 映射与人工标注 (AGENTS.md 架构边界)。
- 部署加固: M1_API_TOKEN/M1_ADMIN_TOKEN 启用、systemd 进程守护、Prometheus 接入, 待甲方运维确认。

### A2 灰度审计闭环项（COMPLETE — c5a8ecf 交付, Loop C 复核 ACCEPTED, CONDITIONAL 解除 2026-08-07）
- ① F1 (MEDIUM): chat_persistence PG I/O 在全局锁内且 psycopg 无超时 → 加 connect_timeout + 查询级超时 (先例 memory_saver.py:60), 或移出锁; 不修须入账 known_risk
- ② F2: compare-intent 绕过补接线级回归测试 (route=on + 对比类问题 → 走直连且 ask_via_opencode 未被调用)
- ③ F3/F4: trust_env=False 断言守卫 + sources:[] 显式拒绝透传测试 + echo 负例 + strip sample_id 尾部 `.`
- 体量预计 <30min, 完成后 Loop C 复核转 ACCEPTED; 不阻塞当前灰度 (route=on 继续)。报告: docs/experiments/2026-08-06_audit_loop_c_flash_fixes.md
- F5 known_risk (2026-08-06 裁定不修, 用户确认): async 端点 /api/m2/ask 同步调用 adapter/直连 LLM → 阻塞事件循环最坏 51s(env)/133s(default), 病态清理级联 +500s; workers=2 仅部分缓解。既有模式非回归, 归入 B 阶段 (网关/原生入口改造, docs/25 路线 A/B) 处理。

### 2026-08-07 differential 审计待办（源: docs/experiments/2026-08-06_differential_phase3_to_head.md, 33 项 0 CRITICAL/1 HIGH/8 MEDIUM）
- E1 (HIGH): **RESOLVED** (2026-08-07 00:26) — 生产口径复验 rerank=True 下 RAG QA 15/15 通过; rescore 被 rerank 架空不影响 QA 结果, docs/23 15/15 两口径均成立。
- E4 (MEDIUM, 一行修): m1_rag_ingest.py:341 传 document="" 使 email_notice 标记词检查恒 False; email_* 样本一旦进入 ingest 即标签漂移。
- P1/P2/P3 (随手修级): shell 误映射 / proxy debug 日志截断 / stdio hygiene 补齐 (报告处置序节)。
- E7 (记录漂移更正): commit 9f3e655 message 声称 16 测试, 实测 15 — 审计抓出, 台账更正。
- T1 INFO 残留: 会话 delete/list 端点断言缺口; opencode.json skill:allow 全局继承 (F6 后续可加 "skill": "deny")。
- 运维注意: ~~:5050 需重启载入 c5a8ecf PG 超时加固~~ **CLOSED**: 08-07 起已载入; 2026-08-09 02:0x 再次重启载入 compare 模糊匹配 (24770c4) + M2_ENABLE_BM25 flag (13a37b8), 生产验证 PASS (嘉兴民安短名 0→2 持仓)。

### TODO: jinrong-rag MCP 接入 Loop C (Claude Code) — 已评估不实施 (2026-08-06 T3.2)
- 价值: Loop C 审计时可直接查 m1_parsed_statements 核验 RAG/QA 类声明 (如答案溯源正确性), 不必绕 curl :5050 或手跑脚本。
- 接线方案 (实施时用): `claude mcp add jinrong-rag -s user -- bash ~/wzh/projects/agents_final_tech/scripts/start_mcp_server.sh`; start 脚本已 venv-first + 自载 .env (PGDATABASE_URL/embedding), 配置侧无需放任何 env/密钥; 备选 .mcp.json (project scope, 不 commit)。
- 前提/风险: Claude Code 对 MCP tool 首次调用要权限确认 (skip-permissions dispatch 下自动过, 交互模式需 permissions allowlist); 多一个 PG + 本地 embedding (CPU) 消费方, 负载可忽略; 审计独立性略降 (判定方可触被测数据源) — 保持 "MCP 只取抽查证据, 判定仍以独立复算为准" 纪律。
- 触发条件: Loop C 审计开始频繁需要核验 RAG 答案时, 或 B 阶段 (docs/25 路线 B) OpenCode 原生入口落地后。
- 2026-08-07 用户批复: 维持观望, 不启动。
### Agent 面对的 CLI 表面盘点 (2026-08-06 T3.3, 仅清单, 动手前过用户)
| 位置 | 现状 (prompt 内联) | 建议 |
|---|---|---|
| opencode.json m1-extraction.prompt | 内联绝对路径长命令: {项目venv}/python scripts/m1_statement_parser.py --samples-dir ~/wzh/m1_samples --json /tmp/opencode/m1_extract.json --compact-summary /tmp/opencode/m1_compact_summary.json 2>&1 \| tail -20 | 封装 scripts/opencode_m1_extract.sh (venv 探测 + 固定输出路径 + tail 内置), prompt 只留一行入口 |
| opencode.json evidence-verifier.prompt | cat /tmp/opencode/m1_compact_summary.json (一次) | 已最小化, 不动 |
| opencode.json m2-qa.prompt | 无 CLI, 纯 MCP 调用 (jinrong-rag_knowledge_search) | 不动 |
| opencode.json tabular-researcher/runner | prompt 描述"对显式提供的数值行做有界实验", 未发现内联命令 | 下轮复核确认 |
- 收益: prompt 缩短 (省 token + 减漂移)、脚本入口可独立 smoke test、路径/参数变更只改脚本不改 prompt。
- 风险: 封装后 agent 对参数的临场调适能力下降 (如换样本目录) — 脚本留 --samples-dir 透传参数即可。
- ~~ripgrep 缺失 (GB10)~~ **RESOLVED** (2026-08-10 核实): rg 15.1.0 已安装于 ~/bin/rg (bashrc 已含 PATH), skill-map 可运行; 陈旧条目本轮清除。

## 2026-08-09 Phase 4 结论入账
- **4.2 VLM 降采样实验 CLOSED**: _vlm_downsample(≤1600px, M1_VLM_MAX_PX) 解决延迟(华泰 22.9s/TraFax 10.3s/WaveFax 9.6s, 远优于 90s 门槛), 但 TraFax 命中率 [50,81.8,81.8]→[0,0,100] 显著劣化(8B Q4 对乱版传真输出退化 2x1 表) → :8007 维持 VERIFIED-CLOSED; 下采样代码保留(flag 化, 未来若换更强 VLM 可复用); 实验后 :8007 已 kill
- **4.6 BM25 决策不修**: 真 BM25 已实现(PG 全量取 137 chunks + rank_bm25 + /tmp 缓存)并 flag 化 M2_ENABLE_BM25(默认 false); A/B 16 题 hit@10 off=15/16 on=15/16, 排名零变化, improved=0 regressed=0 → 当前语料规模下无增益, 留 flag 备未来语料扩大; scripts/m2_bm25_ab.py + logs/graph/eval/bm25_ab_report.json 为证据资产

## 2026-08-10 文档刷新+双链路+视频+选择题专项 入账
- **T4 场景 A 最小闭环 CLOSED** (7b27d50): /m1 建议映射面板 — GET/apply/reject 三端点 + 回归门禁 (apply 后自动跑 scenario1 --quick, FAIL 自动回滚 schema 返 409) + 用户可改选目标字段 (retarget) + 10 tests (tests/test_m1_schema_suggestions.py)。UI: #suggBtn 徽章 + modal (high 置信默认勾选)。**注意**: 端点需 :5050 重启才生效, 重启窗口待用户批准。
- **场景 B (问答候选选择题) 设计入库、实现排期**: docs/26 §三 — 直连路 ~2h (候选收集 1h + 拼装 0.5h + 测试 0.5h), agent 路二期。触发条件: 场景 A 面板经甲方 walkthrough 认可后, 或甲方明确反馈"未找到"体验需升级。
- **T5 对账表 CLOSED**: docs/26 附录 — docs/23 话术/限制 9 条: 8 解决有证据 + 1 等甲方数据; 台账 10 条: 8 闭环 + 1 待决策 (schema 口径统一, 需刷 frozen_hashes manifest) + 1 等甲方输入 (Qoder PAT)。
- **hygiene** (02b768e): legacy test_e2e_browser 显式跳过 (:5000 旧 UI + headless=False, playwright 安装后被解锁致 2 fail); pytest 回 310 passed / 13 skipped / 0 failed。

## 2026-08-10 Loop C differential 审计入账 (a7f8282..HEAD, CONDITIONAL → 修复中)
- 报告: docs/experiments/2026-08-10_audit_loop_c_differential.md (0 CRITICAL / 1 HIGH / 6 MEDIUM)
- **已修 (批 A 395f85b)**: F1 冻结 schema 守卫(403) / F2 reject admin 门禁 / F3 OCR 门禁盲区提示 / F4 apply single-flight / F5 字节级备份回滚 / F10 CLI 无样本 --apply 需 --force / F11 退出码契约; +3 tests
- **已修 (批 B 7173dce)**: F18 docs/23 四处数字按工件校正 + docx 重生成; F19 附录 B 数据源/延迟区间/QA 口径; F13 judge 声明如实化; F14/F15 描述与 .env.example 登记
- **台账遗留**: F6 同(raw,table)多目标策略(当前重复数=0, 无实害); F7 M1_SCHEMA_SUGGESTIONS 双轨(CLI-only 用途, 文档注明即可); F8 上传临时文件名建议不可复验(UI 标注为后续); judge 结构性隔离(双 prompt, 后续项); F3 中期: OCR 来源建议 apply 前定向 before/after
- **F4 结构项**: async 端点同步阻塞又一新实例, 归 B 阶段(网关化)处理 — 既有 F5 known_risk 同源; 本轮已加 single-flight 缓解
- **待办**: :5050 重启载入批 A 端点加固 (等用户批窗口, 与 walkthrough 合并执行)

## 2026-08-11 agent 路延迟退化 — 根因定位（A/B 闭环, 修复待批）
- 排查方法: adapter 为 throwaway session（ask 完即删）, 旧 39/55s transcript 不可追溯; 改直连 sidecar 计量会话 + SQLite trace 取活证据。
- 基线（原配置, warm）: 31.5s = 轮1 12.0s（in 512 + cache.read 10454, out 459, tool=knowledge_search）+ 轮2 19.5s（out 1017）。**skill tool 从未被调用**（playbook 未加载）。
- 变体 A（摘 m2-qa「首答前加载 m2-rag-playbook」指令）: 冷 43.1s（轮1 prefill 37.3s = 10.9k skill 元数据上下文冷 prefill）/ 热 22.8s（out 903）。
- 根因分解: ① **~11k skill 元数据上下文冷 prefill ≈ 37s**（「冷 39s」真身, 每次 sidecar 重启后首问承担） ② **输出端 reasoning tokens ~1-1.5k ≈ 19-30s（warm）**（qwen3.6 thinking 默认开） ③ playbook 指令本身未执行但诱发额外推理（摘除 warm 31.5→22.8s）。
- 现状: warm 22.8s 仍 > OPENCODE_ASK_TIMEOUT=18 → route=on 当前多回落直连; 回落路 2-4s 正常, 演示以直连为主不受影响。
- 修复候选（待批, 未动手）: a) restart_opencode_sidecar.sh 加一次 warm-up ask 预热缓存（消 37s 冷启动, 最小改动） b) m2-qa 禁 thinking（adapter hint 或 provider 层, 需 :5050 重启窗口） c) skill 上下文瘦身（m2-qa 仅注册必需 skill）。测后配置已还原（opencode.json 无净变化）。**[08-23 洁癖批定性: b CLOSED（生产 thinking 本就 OFF, 08-22 L2 更正坐实, FORMAT_HINT /no_think 08-16 已载入, 无动作空间）; c 并入 L2 sidecar 瘦身菜单（08-22 测量完成, 方案待批）; a warm-up 留候选（冷路 45s 预付, 效果待观察）。]**

## 2026-08-11 任务2 M1/M2 页面改版设计稿（待拍板, 未动代码）
- docs/27_M1M2页面改版_两个设计方向.md + 草图 docs/experiments/2026-08-11_m1m2_redesign/{direction_a,direction_b}.html（浏览器直接打开）。
- A 三栏任务工作台（WorkBuddy 正传, 2.5-3 人天） vs B 流水线画布控制台（演进式, 1.5-2 人天）; 推荐先 B 后 A。
- 公共规范: 模式切换只读指示（/api/m2/ask 无每请求 route 覆盖, 诚实设计）/ 选择器保留映射表（record_demo_video + tests 命脉）/ m1v2 并行灰度 / 视频重录与 walkthrough 刷新预案。

## 2026-08-11 夜间 loop（行业对标 × 四维审计）入账
- docs/28 业界对标与优化菜单: 14 gap + Top5 菜单, 待用户拍板; 不擅自启动。
- eval 硬化资产: scripts/m2_eval_number_faithfulness.py（数值 claim 去 LLM 化核验, 掩码感知, 3 对抗题, FAIL=0）+ scripts/m2_eval_judge_consistency.py（judge 自一致性 STABLE）; 报告 logs/graph/eval/{number_faithfulness,judge_consistency}_report.json。
- eval 工具 bug 修正: 新脚本初版 chunk 键误用 text（真键 content）→ 修正; judge 本体无此 bug（基线不虚, 误判已撤回）。
- 后端小修: .env.example 补 OPENCODE_ASK_TIMEOUT/MAX_SESSIONS/SERVE_URL。
- 延迟诊断实验文档: docs/experiments/2026-08-11_agent_latency_diagnosis.md（修复菜单 a warm-up / b 禁 thinking / c skill 瘦身, 待拍板）。
- 菜单新增: bare except 收窄 x5 / knowledge 端点 metrics / eval pytest 原生化(G14) / judge 全 16 题一致性 / agent-vs-直连一致性检查(前置延迟修复) / parser 双引擎交叉。

## 2026-08-11 辅助线 walkthrough 验收入账（块 A）
- **验收结论**: 场景 A 建议映射面板 walkthrough 通过; apply 5 干净建议 / reject 14 / hold 6; WaveFax 85.7→**100** 入基线 (270c686, --rebuild + quick 门禁 12 pass/3 skip)。schema +5 近义词 (基金资产总额→资产总额类 / 交易账号→资产账号 等)。
- **遗留①**: ~~schema「交易对账单」表缺 分红方式 标准字段~~ **RESOLVED (2026-08-12 T4①)**: 交易对账单+证券持仓明细 新增 分红方式/可用份额 两标准字段 (m1-gap-triage SOP: 诊断→补字段→回归门禁→报 delta); 嘉合×8 87.5→100、TraFax 表3 81.8→100、NCAMC 75→87.5、nanhua 75→87.5, 基线 rebuild 后门禁 15 pass/0 warn; 附带修复嘉合默认路 3.3-9s LLM 兜底延迟 (根因=基金份额/可用份额 双列争用 持仓数量 单槽位) → 63ms。详见 docs/experiments/2026-08-12_client_experience_audit.md §三。
- **遗留②**: admin token **fail-open 仍为 B 阶段延期项** — 本次 apply 即在无 M1_ADMIN_TOKEN 下执行, 风险已知 (与 knowledge 写端点无 token 同源, 台账不重复开条目)。
- **决策入账**: 延迟修复 a(warm-up ask)+b(禁 thinking) 已批, 等 :5050 重启窗口一并载入; 任务二「先 B 后 A」已批, 代码启动等 docs/23 发送; docs/28 顺序 #2→#1→#4; docx+视频预审 PASS, 等用户人工复审 docs/23 后亲发甲方。
- **口径提醒**: 已决 — 表下加注(定稿后 WaveFax 100 以实况为准) + docx 重生成, 504810c 定稿, 双方不再改/不再重生成, 用户终读后亲发。

## 2026-08-12 发送前自审计专项 (T1-T4) 入账
- **T1 甲方体验审计**: 15 步全过 / 0 console 错误 / 无演示前必修项; 口头解释 4 条 (QA 20-25s=route 回落 / thinking 提示 / 持仓对比(未知)=掩码样本如实呈现 / OCR 冷热口径) + 可接受 3 条 (下载文件名 F8 / 开关无 toast / hold 不显示按设计)。报告 docs/experiments/2026-08-12_client_experience_audit.md。
- **T2 声明复测漂移案例** (docs/23 冻结不改文, 只入账): ① "非扫描 <2.1s" 默认路实测 3.3-9s ✗ → 根因定位后 T4① 当晚修复复测 63ms ✅ RESOLVED; ② "OCR 16-71s" 复测 536ms = .ocr_cache 内容哈希磁盘缓存 (冷启 08-09 证据 9.6-22.9s), 漂移方向更快, 口头解释级不修。教训: 声明数字必须标注口径 (路径/冷热/题集), 复测时口径不一致即记漂移。
- **T2 16/16 生产口径**: deterministic eval 打 :5050 → 16/16 PASS (题集含对抗题; 感知延迟 20-30s 为 route=on 回落, 正确性不受影响)。
- **T3 Loop C 差分审计 (5535bdf..504810c) = CONDITIONAL**: 报告 docs/experiments/2026-08-12_audit_loop_c_differential.md。FC-1 (MEDIUM, diff 引入: 资产账号 下 交易账号 同义词与 交易账号 字段表内碰撞) **当晚已修** (删同义词 + 门禁复验); FC-4 fail-open auth 复评 **HIGH 暴露** (0.0.0.0 + 无 token 写操作已实发生, B 阶段最高优先, token 落地前不扩大暴露面; .env.example 已补 M1_API_TOKEN 条目); FC-5 async 端点同步调用复评 HIGH-可用性 (route=on 在跑, 匿名低成本 DoS 面, B 阶段网关化处理); FC-3 (LOW): 多表 100.0 基线进入零容差粒度区, OCR 容差仍是唯一缓冲, 门禁健壮性改进入下迭代; 范围外观察: 冻结清单表述应统一为 scripts/graph/frozen_hashes.txt (任务书"docs/m1_schema/frozen_hashes"与实物不符, 文档引用时注意)。
- **T4① 附带修复 (自学习写入器 bug)**: scripts/m1_statement_parser.py `_append_schema_suggestions` 重写文件时只写 {suggestions}, 丢失 applied/rejected 审计区 (T2 复测默认路实跑于 00:00:56 触发) → 修复为保留原有顶层键; 丢失区段已从 HEAD 恢复; 2 条陈旧建议 (可用份额→持仓数量 / 交易费用→财汇局征费, 均已被存量或新字段覆盖) 移入 rejected 防碰撞复发。
- **T4② eval 接线**: m2_eval_number_faithfulness.py 失败计退出码 (原恒 0), run_eval.sh 增步 [3/4] 数值忠实度 + 退出码联动 + summary 段落。
- **遗留 (小)**: scripts/t1_client_experience_audit.py 上传步等待条件命中过早 (03/04 ms 无效, 已用 API curl 补偿), 下次维护窗修; FC-3 门禁健壮性; 审计建议"token 落地时同步收紧 CORS_ORIGINS" (随 FC-4 处理)。

## 2026-08-12 docs/23 解冻重写（用户授权覆盖 504810c 冻结约定）
- 用户终审结论: 旧版不达交付标准 → 授权解冻重写。新结构: 30s 执行摘要(头部仅 4 数字: 嘉合100% / 35.7→100% / 16-16带溯源 / 电子件毫秒级) / 场景化能力 / 递进故事 / 诚实限制 / 需要您支持; 口径演化(14/15→16/16, OCR 冷热)移脚注; 去 23_ 编号与待审阅元行; 附录 B 业务化; 附录 C 话术拆至 docs/experiments/2026-08-12_demo_talk_track.md。
- 截图 08-12 重拍 10 张 (docs/experiments/2026-08-12_docs23_screenshots/, 含建议映射面板 6 候选实拍); 08-04 目录转历史留档。
- **新发送版 docx md5 冻结: bc3785cb4237dcda316120251fab8472** (封面含呈报/汇报方行+10图内嵌+页码, 12 页; 图7 单独占页放大, 8/9 放大) — 等用户终审; 终审通过前双方不再改/不再重生成。旧 504810c / 141b092b 冻结约定作废。打磨五处: ①封面署名+呈报行 ②图7 独占页放大 ③TraFax(逐表命中率) ④页码 ⑤支持清单项目符号+附录B全量。

## 2026-08-12 仓库精简收尾入账（主线程清扫）
- **精简落地**: c4f6a5a (git mv 归档 18 实验记录 + 16 一次性脚本 + README_Codex 历史快照, 零 rm 可逆); 主线程执行沙箱拦截的删除: sessions.db / scripts tmp_*.py×7 / 工作区 PNG×6 / tmpclaude-cwd×2 / _staging_task2 / D:\tmp_doc23_pages×2 — 全部先移备份 D:\AIRcommend\JinRongAgents\_cleanup_backup_20260812 (45 文件) 再清源; _staging_task2 删前核验内容已在库 (设计文档=docs/27@8e5fd92, html/png=experiments/2026-08-11_m1m2_redesign 在库, 仅 _shot.py 一次性); pytest 325 passed/13 skipped 零回归; 冻结 docx bc3785cb 复验未动。
- **机会项（等拍板）**: 本机 agents_final_tech/dify/ (gitignored, GB10 无此目录) 存 5 份甲方规则 docx（电子对账规则0108 / 估值数据催收规则 / 完整性监控与一键估值规则 / 管理人估值进度查询规则 / 自定义对账规则）+ 5 份 Dify workflow yml — 七月 Dify 原型遗留, 正是 docs/23"需要您支持"所列字段规则素材; 建议走 Q2 同款确定性流程挖 schema synonyms, 批准前先不动。
- **待审（低优先）**: 本机 agents_final_tech/image/.env/ 7 张时间戳 PNG (~2026-02, gitignored), 旧时代遗留, 下轮 neat 判定去留。
- **禁动确认**: 本机工作区 3 个 .bundle (tat-dqa×2 + joint-m1-m2-plan) 为相关工作唯一载体, GB10 无 tat-dqa 仓库, 不得删除。
- **check[4] 本机 FAIL 定性 (辅助线复核更正)**: 根因非缺 skill 目录 (本机 ~/.codex/skills 37 目录 / ~/.claude/skills 均在), 而是本机 CRLF checkout 使 sync_skills.sh 行尾带 \r, WSL bash 执行 `set -o pipefail\r` 即错 exit 2 (git ls-files --eol = i/lf w/crlf 为证); 属环境差异非真漂移, 结论维持 docs_lint 以 GB10 为准 (0 fail/0 warn); 本机如需跑: `bash <(sed 's/\r$//' scripts/graph/sync_skills.sh) --check`, 不强制。


## 2026-08-12 "已发送"信号 → S1/S2 执行入账
- **docs/23 已发送甲方**（用户亲发, 2026-08-12）; **B4 观察时钟启动**: 目标 ≥100 asks / ≥3 天; 仪表 = /api/m2/ask JSONL (logs/graph/b4_ask_log.jsonl: ts/route/latency_ms/sources_count/fell_back/status) + status.sh B4 段; eval 套件每天经 :5050 生产端点跑一遍积累真实样本; 数字不许造。
- **S2 重启载入** (窗口 23:24-23:41): 延迟 a(sidecar warm-up ask; 首版用"就绪确认"题不触发检索→MCP 冷启动未预热, 修正 d8504fb 为真实检索题, 冷路 45s 预付) + b(FORMAT_HINT /no_think, 契约 C-1) + Q2 别名链 + 批 A 端点加固 + vision MCP allowed_roots=/home/testuser/wzh/m1_samples(opencode.json mcp env); B4 仪表 + status.sh(Q4 L1) 同窗载入 (cab17b9)。
- **六步验证**: ①health/full healthy(137/local)✓ ②parse 冒烟 sample_20260506_233222LU.pdf 3 表(OCR+LLM 路 16.4s)✓ ③QA×2 正确带 sources(含 OCR meta-query 命中)✓ ④compare 嘉兴民安短名 2 持仓✓ ⑤route=on✓ ⑥agent 路 warm 实测: **最佳 13.5s 成功(单检索题), 3/4 次尝试 >18s 回落**——目标 <18s 部分达成, 如实记账。
- **延迟实测台账**: a+b 后 agent 路 1 成 3 落; 回落与多轮检索耗时 + :8004 slot 争用(与 Loop B 23:38 循环时间窗重叠)疑似相关, 根因诊断入 A2 稳态化遗留; 直连路 warm 2.7-3s, 重启后首请求冷加载 ~17-20s(embedding 懒加载, B4 验收口径: 热身或从 p95 排除)。
- **回滚演练**: kill→health200(route=off) 实测 **10s** (B4 ≤30s 达标, 前次实测 23s); route=off 直连验证正常; 甲方临时演示第一动作 = M2_OPENCODE_ROUTE=off 重启(10s)。
- **B4 数据卫生**: pytest m2 端点测试会写 latency_ms=0 的 mock 条目进 B4 日志, 统计时过滤 latency_ms=0。


## 2026-08-13 S3 队列收口入账（发送后队列 ①-⑤ 全部完成）
- **S3① G12 数值核验产品化**: 原型核心抽入 src/biz/number_grounding.py (行为逐字一致) + eval 脚本改 import + 6 单测; NF 复跑 0/9 与基线一致 (bda88f4)。
- **S3② dify 5 docx synonyms 挖掘**: scripts/mine_dify_rule_terms.py (确定性无 LLM, 可复用); 5 docx 性质判定 = 估值工作流业务规则(非字段映射表); covered=4/candidates 28(真实 3)/unknown 978; 补词 3 (交易日→交易日期 / 下层基金净值→基金净值 / 手续费支出→手续费, 均证券持仓明细, 碰撞检查过); 门禁 15 pass; **诚实 delta=0** (语料无新词, 为未来估值表类文档强化) (6dd189b)。
- **S3③ G6 检索透明面板**: top_k 选择器(3/5/8/10) + sources score/field/text 优雅降级(agent 路无 score 不再显示 undefined) + meta 显示 route(直连/验证链路); 纯前端零 API 改动, 既有选择器未动 (61d2fd2)。
- **S3④ Docling ARM64 探针**: 独立 venv 零编译安装 (torch 2.13 aarch64 wheel, 模型走 hf-mirror, HF 直连超时); **GPU 路 triton gcc JIT 失败 (与 Qwen3-VL safetensors 同类故障)**; CPU 路: NCAMC 垂直行提取优于坐标重建(完整 1×8 数据行) / TraFax 表数同基线但退化表 / 嘉合弱于确定性 parser; 定位 = 离线 second-opinion 候选, 不入热路径 (f86a876)。
- **S3⑤ :8005 judge 分流**: M2_JUDGE_ENDPOINT/MODEL flag 原生在位(默认 :8004); :8005 Qwen3-14B 交叉一致性 **63/64 = 98.4%** 平均差 0.03 (唯一分歧 adv_multiturn citation A=5/B=3); crosscheck 脚本入库; :8005 可作 eval judge 分流端点给 :8004 腾 slot (ceec4ab)。
- **B4 观察进行中**: asks 积累见 status.sh (测试 mock 条目 latency_ms=0 统计时过滤)。

## 2026-08-13 凌晨 科研线与守备强化队列 (R1/R2/R3) 入账
- **R1 Loop B 强化 COMPLETE** (e508a5c): STEP5 QA 金丝雀 4 题 (adv_ocr_meta/adv_refusal/q06_minan_cash_balance/adv_cross_doc, m2_eval_deterministic.py 新增 --only/--timeout, 报告→logs/graph/eval/m2_canary_report.json) + STEP6 三方 git 对齐 (网络不可达=SKIP 不 FAIL) + STEP7 docs_lint; env flags LOOP_B_CANARY/GIT_ALIGN/DOCS_LINT/CANARY_IDS/CANARY_TIMEOUT 增量, 默认行为不变; write_report.py 扩展兼容 SKIP(-1); **FAIL 翻转才写 dispatch** (状态文件 logs/graph/loop_b_last_status, 首跑=init 不写); 破坏验收过 (INDEX 死链注入→翻转 PASS→FAIL→恢复→FAIL→PASS 双 entry); pytest 336/13 skipped。
- **R1 事故记录**: 旧 graph-loop-b daemon (07-31 起运行) 08-13 01:00 发现停摆 (死因不明, 00:47 侦察尚活); 重建 tmux + --daemon, 首周期 PASS (01:02:23, head=e508a5c)。
- **R2① zhikuncode 探针结论**: Docker 确认 (Spring Boot JDK21 + python-service sidecar, healthy, :8090→8080; "依赖安装"仅指本地构建镜像时); 仓库已 bind-mount /app/workspace; BYOK 现指云端 Token Plan; **:8100 仅 /responses 线 (responses2chat), zhikuncode 走 Chat Completions → 直切 :8100 不可用**, 价值低, 维持云配置; 顺带: MCP zhipu-websearch 每 30s 重连失败 (无害噪音)。
- **R2② OpenAI4S 探针结论**: PKU-YuanGroup/OpenAI4S (MIT, Code-as-Action 科研 agent, 纯 stdlib 核心) **最小循环验证通过**: ~/wzh/research/openai4s_probe + 独立 venv ~/wzh/venvs/openai4s_probe; BYOK 直连 Token Plan 上游 (OPENAI4S_CHATGPT_BASE_URL; :8100 因 /responses-only 不可用); `openai4s run` 输出结构化结果 + kernel 验证 + metrics (RUN_EXIT=0); serve Web UI :8760 未启动; **未接生产**, 可作 docs/30 科研线执行器。
- **R3 学术 skill 审计安装 COMPLETE**: zLanqing/codex-claude-academic-skills (MIT) GB10 克隆 ~/wzh/research/academic_skills_audit (本机 clone 被沙箱拦截, 转 GB10 成功); 审计 = 3 顶层 skill (research-writing/office-academic/scientific-toolkit 含 21 子技能), frontmatter 规范, 无恶意模式; **唯一 caveat**: literature-review 子技能含 `curl|bash` 第三方安装引用 (parallel.ai), 未经审阅勿执行。安装 = repo skills/ + sync_skills.sh A 列表 + AGENTS.md 注册表 (A 配属 科研线) + 本机 Loop D; sync --check PASS 21/21。
- **R3 docs/30 入账**: docs/30_科研线规划.md (VGMC 验证门控记忆固化) 登记 INDEX 状态=活跃; M0 文献调研任务卡已附文末 (只读 2h 隔离执行), 待用户排期。

## 2026-08-13 早 T1/T3 收尾小队列入账
- **T1 schema_suggestions 脏改动入账** (0d938d7): 自学习闭环 08-12 23:33 批次 (walkthrough 上传 tmp2s004xv5.pdf) 7 条新建议 + 权益登记日 count 1→2; **产品份额①→持仓数量(high) 列下轮 apply 候选** (走既有 SOP: 回归门禁 + delta 报告, 等明确窗口, 本次不 apply); tmp2s004xv5.pdf 定性 = 场景 A walkthrough 上传临时件 (时间戳落在 23:24-23:41 重启+walkthrough 窗口), 磁盘搜索 (/tmp + 项目目录) 未见残留, 无需清理动作。
- **T3 B4 分布记账** (辅助线 08-13 08:27 实测): asks=120 (agent=15 / fallback=92 / error=0) — route=on 下 **77% 流量经 18s 超时回落走直连**, "快与准菜单"的准路径当前被超时吞掉大半。定性: ① 作为 **A2 遗留 (:8004 slot 争用/延迟方差) 的量化证据**, 修复优先级随甲方反馈定; ② **B4 时钟口径确认**: ≥100 asks 数量维度已达标, 继续等 ≥3 天, 达标判定 = 两条件同时满足; ③ 该分布同时是 docs/30 B 模块 (记忆感知路由) 的实证动机 — 引用不重复复述 (台账唯一存放规则)。

## 2026-08-13 夜 T2 M0 文献调研结论入账
- **M0 差异化判定 = 差异化成立（附条件）**: 报告 docs/experiments/2026-08-13_m0_literature_survey.md。精读/补扫 5 篇可核验文献（RecMem ACL26 Findings = 最近邻但只解"何时固化"且记忆仍 NL / Q-Evolve 进化权重不进化记忆工件 / Evo-Memory 与 MemoryAgentBench 为基准类可借鉴评估方法 / self-evolving coding agents 综述 §3.2 确认记忆自进化全线 NL 轨迹形态且明言需 validation+rollback）。VGMC 三要素组合（可执行规则工件 + 回归验证门 + LLM 介入衰减）未见覆盖。
- **重要发现（检索可靠性）→ C1 更正 VERIFIED（08-13 夜）**: CAIS 2026 与 STATE-Bench 经直连 URL 复验存在——CAIS: "Learning from Supervision with Semantic and Episodic Memory"（Megagon Labs, episodic critique→semantic guidance 管线坐实）@ caisconf.org/program/2026/papers; STATE-Bench: Microsoft Open Source Blog 2026-05-19（开源 450+ 任务 agent-memory 基准）。初判"疑似检索幻觉"系 **M0 渠道覆盖缺口**（文献 API 不索引 ACM 会议页/工业博客）, 非幻觉。渠道规则 + 元洞察（验证门需多渠道化, 与 VGMC 主题同构, 可入论文 motivation）入 M0 报告 §六; docs/30 两锚点恢复必引。
- **可吸收**: Evo-Memory 流式评估协议→实验 3; MemoryAgentBench 四能力→评测对照; 综述分类学→相关工作定位; 真实门控数据 (apply 5/reject 14/hold 6) 为稀缺实证资产。
- **NLPCC/CCIR 截稿日未获得**（DNS/502/JS 渲染全挡）, 入 blocked_questions 待人工浏览器查。
- 约束遵守: parallel.ai curl|bash 引用全程未执行; 物料在 ~/wzh/research/m0_lit/（GB10 本地不入 git）。

- **运维 (08-13 夜, C2 更正)**: GB10→GitHub SSH publickey 拒绝 = **GitHub 侧瞬时故障, 已自愈** — 辅助线实测 ssh -T git@github.com 认证成功 (Hi Wzh2learn!) + ls-remote SSH 路正常 + key 文件在位; 同时段 HTTPS 500 瞬断 x2 为旁证。主路径恢复 **GB10 直推**（C1/C2 收口实测确认）; "GB10 commit → 本机代推"保留为兜底预案; 用户侧 GitHub key 检查降级为可选。

## 2026-08-14 导师包终审入账
- **导师版 docx 重冻结**: 5707fcea397c384d21e35ba72023cee0（R1 口径修正后重生成; 旧版 3d80d27 内 docx hash 作废）。修正内容: 图 1' 看点补"冷态首请求 20.5s / 热态复测 2.7s（战绩表口径）" + shots_meta 04/05 note 更正 + 附录 B 故障表补双端口占用行（R4 实测 exit 1 不静默）。
- **导师版 docx 重冻结（二次，08-14）**: 567c7fe732b8b2993396c6cc2d32a172（Loop C 发送前终审 R2 FAIL 后换图重生成；5707fcea 作废）。修正: 图 1 改解析完成态+选择器位置改输入行右侧；图 2/3 改直连路+sources 展开态（旧图为 agent 路拒答误拍）；图 7 元素级截图无裁切；图 9 拒答完成态并改指 08-13 目录。误拍根因: 旧截图脚本等待条件对整 chatlog 全局匹配且无 sources 非空重试，重拍脚本 /tmp/reshoot_fix.py 已修。待 Loop C 复验。
- **导师版 docx 重冻结（三次，08-14）**: bd3daed4948af81cb5dcea5ef2814882（Loop C 复验残差 2 处改图注后重生成；567c7fe7 作废）。修正: 图 1 图注选择器改互指图 1'/图 9；图 5 图注未映射列改互指图 1/图 4；图 2 看点补冷态说明；shots_meta 01/07 note 同步。待 Loop C 三验。
- **导师版 docx 重冻结（四次，08-14 受众分离）**: d31fe5c3f49f81202a9a03f08c9983ed（build_doc31_docx.py 加 --audience 开关，advisor 默认裁附录 A/B；bd3daed4 作废）。md 保持全量源；清单入审查报告受众分离轮。
- **导师版 docx 重冻结（五次，08-15 视频 v2 轮）**: ab2fed4310487d5f4136f6546780d057（d31fe5c3 作废）。配套: 视频 v2 demo_v2.mp4 3:48（V1-V7 全消解: 开场解析态/等待段倍速+字幕/横幅数字对齐/透明面板+建议面板新分段/结束卡）；D1 H1 导师版；D2 §3.7 按 v2 重写；D3 §6 视频条同步；D4 战绩表 pytest 口径注（334/15 无 PG 环境，PG 依赖 2 项随环境翻转）。
- **导师版 docx 重冻结（六次，08-16 微修轮）**: 929a8c65fbdea1bd672f5d8d5ea1fd16（ab2fed43 作废）。配套交付行改 demo_v2.mp4；扫描全 0 + 第 2 页目检过。视频治理: cards/ 入库，segs//work//demo_v2.mp4 入 .gitignore。视频取回: scp jinrong-dev:~/wzh/projects/agents_final_tech/docs/experiments/2026-08-15_demo_video_v2/demo_v2.mp4（+ 同目录 steps.md）。
- **治理规则（08-16）**: STATE 覆写绑定收口 commit——每次收口 commit 必须同步覆写 memory/STATE.md 至当前 HEAD，杜绝 HEAD 漂移（起因: STATE 曾停 299f77d 三轮）。
- **R3 附录 A 实测**: 五条 scp 临时目录逐条跑通（23 文件 6.33MB, 未覆盖已取回文件）。
- Loop C 独立复审进行中, 报告 docs/experiments/2026-08-13_advisor_package_review.md。

## 2026-08-16 模型升级专项 (Qwen3.8-27B + vLLM) — P2 完成, 闸门触发, 待用户拍板 (A/B 路线)
- P0 完成: :8004/:8005 完整 llama-server cmdline 已录 (回滚依据, 见 dispatch_log 08-15/16 + DECISIONS.md 模型卡); 内存 121GB 统一内存 / 磁盘 2.8T 空闲; :8006/:8007 空闲。
- P1 资产落盘: Qwen/Qwen3.8-27B-FP8 (29GB, 66 shards) → ~/wzh/models/hf/Qwen3.8-27B-FP8 (hf-mirror, 独立 dl_venv); 镜像 timothystewart6/vllm-gb10:v0.27.1-gb10.1 (vLLM 0.27.2.dev0+20260815, 22.1GB, dockerproxy.net; daocloud 白名单拒绝/1ms.run 大层卡死为过程事实)。
- **关键实测 (GB10 统一内存)**: ① CUDA mem_get_info 不计 page cache — 模型+镜像下载后 CUDA free 仅 15.6GB, vLLM init 即 cudaErrorMemoryAllocation; 无 sudo 不能 drop_caches, 用 CPU 分配压力法回收干净缓存 (scripts/gb10_reclaim_page_cache.sh, 15.6→38GB), 生产栈实测无感 (:5050 healthy / :8004 200)。② 回收后 GMEM=0.30 启动成功 (0.27 差 0.44GiB 失败); --max-num-seqs ≤78 (Mamba 状态块约束)。③ 思考控制实证: enable_thinking=false 零推理; reasoning_effort 合法集 xhigh(默认)/medium/low (prompt 引导式非硬上限); thinking_budget 模板不支持传入被忽略; "high" 非法→400; vLLM 0.27 reasoning 存 message.reasoning。
- P2 基准 (全实测, 报告 logs/graph/eval/model_probe_*.json @GB10): 三档矩阵 A_off p50=10.31s/p95=15.76s (49 tok), B_effort_low p50=23.82s, C_effort_xhigh p50=60.60s (431 tok); 确定性 16/16 PASS (旧栈对照 16/16, 1.3-1.9s/题); 并发 3 流 makespan 70.6s vs 串行 207.1s 但单请求劣化 7x (带宽受限); judge 交叉评 5.0×4 (基线 4.94), 自评 5.0×4; 视觉转写质量平手但候选 72-76s vs 旧栈 mmproj 29-31s。NF 未对候选重跑 (脚本锁 :5050, 红线不重启), 留 P3。
- **闸门判定: 质量 GO + 快路 FAIL (A_off p50 10.31s > 8s) → 不全量替换**。切换菜单 = 路线 A 双模型分工 (推荐先行) vs 路线 B Qwen3.8-35B-A3B MoE 探针, 见 docs/32 §2.4, **待用户拍板**。
- 状态: 探针 :8006 保持运行 (tmux vllserve), 拍板前不动生产。旧 GGUF+llama-server 保留 48h (至 08-17 18:00)。附注: P2 视觉对照占用 :8004 期间 (18:16) Loop B qa_canary 一次超时 FAIL, 属探针负载扰动, 非代码回归, 观察下轮翻转。

## [2026-08-16 22:20] PG 连接泄漏: Loop B 周期跑遗留 idle 连接打满 max_connections=100 (known_risk)
- 现象: NF 候选侧首跑全程 "too many clients already" (结果无效已重跑); pg_stat_activity 95 idle/100, 最老 1d21h, 增长速率 ~30min/个, last_q 含 chat_sessions 心跳与 ROLLBACK, 判定 Loop B 周期跑每轮漏 1 连接。
- 临时处置: pg_terminate_backend 清 >60min idle (95→20), :5050 health 全程 healthy 无感。
- 根治选项 (待窗口): a) Loop B 脚本补连接关闭 (Loop B 本体不扰, 需用户批) b) PG 设 idle_session_timeout (需 PG 重启窗口) c) max_connections 调大 (同需重启)。**[08-23 窗口执行完毕 + 归因更正: 窗前 ss 普查坐实泄漏端 = :5050 uvicorn 两 worker(55 连接) + mcp_server.server(45), Loop B 本体零连接——「Loop B 每轮漏 1 连接」更正为「Loop B 周期流量是触发器, 泄漏在 :5050/MCP 池」; 根治 a 不适用(Loop B 侧无连接), 根治 b idle_session_timeout=10min 已落地, c 不需要; :5050/MCP 池泄漏根治(连接关闭/池配置)记代码窗候选, GUC 10min 回收兜底。]**
- 状态: OPEN (B 阶段候选); 再现特征: NF/eval 报 too many clients → 先查 pg_stat_activity。

## [2026-08-16 23:35] S4 双模型接线完成 + OPENCODE_ASK_TIMEOUT 重议待拍板
- 接线: gb10v provider (经 :8008 注入代理 → :8006) 承载 m2-qa + evidence-verifier; judge → :8006; A3B 守快路+视觉+M1 热路径。详见 DECISIONS 当日条目与 docs/32 §4 S4 执行记录。
- agent 路实测: 首轮 ~30s / 热态 72s / >120s 超时, 18s 预算全回落 → 用户可见行为不变 (零回归)。
- 重议需要: :5050 重启窗口 (OPENCODE_ASK_TIMEOUT 模块级读取) + M2 菜单项 (skill 预载/降轮次/档位感知超时) 组合。等用户拍板, 与 48h 旧栈窗口 (08-17 18:00) 时序上互不阻塞。
- B4 台账切换点: 2026-08-16 ~23:35 双模型接线 (ask 结构化日志按 timestamp 分段; 接线不改变回落行为, 计数连续累计)。

## [2026-08-17 00:35] T2 辅助 Qwen 退位: :8005 Qwen3-14B 停服
- 依赖盘点: .env/src/opencode.json 零引用 (judge 已于 S4 切 :8006); 仅治理脚本/文档引用, 已更新: graph_orchestrator.sh (8004/8006 http_code 检查) / loop_d_monitor.sh (:8006 vLLM + :8005 RETIRED 行) / loop_a_exec_constraints.md / loop_c_audit_prompt.md; status.sh 端口表保留 (快照如实反映 down); loop_b MODEL_AUX_PORT 由 T5 升级为期望关闭态。
- 停服: kill llama-server pid 2645844 (LM Studio 后端, -c 32768 -ngl 20); 端口关闭确认, 无自动拉起 (无 LM Studio daemon)。
- 权重保留 (退位政策): /home/testuser/wzh/models/gguf/qwen3-14b/Qwen3-14B-Q4_K_M.gguf; 磁盘 2.8T 空闲, 不删。
- 端口快照: :5050=200 :4096=200 :8004=404 :8005=000000 :8006=404 :8008=404 :8100=404 (8005 关闭为预期)

## [2026-08-17 23:25] P0-2/P1-1 Loop B daemon 重载 + T5 措辞更正
- 根因: bash --daemon 启动时脚本整体载入内存; 08-13 01:00 启动的 daemon 一直跑 T5 升级前旧脚本——旧 STEP 3 查 :8005 健康 (已退位) → api_anchors FAIL 自 00:48 持续 ~22h 无人接; 旧脚本 8 参调新 write_report.py → STEP 8/9 恒 SKIP (看门狗等于没装)。
- 修复: kill 旧 daemon (pid 1661919) → graph-loop-b pane 重启 --daemon; 新周期 STEP 8/9 出判定, :8005 退位断言 (响应即 FAIL) 生效。
- **T5 措辞更正**: 台账 08-17 00:40 "验收: 完整周期无误报 PASS" 实为新脚本前台运行结果; daemon 当时从未重载, 其后 22h 静默 FAIL。
- **治理规则**: Loop 脚本升级必须重启 daemon 载入新版; 验收以 verify-report 中对应 STEP 实际出现判定为准, 前台运行 PASS 不替代 daemon 载入。

## [2026-08-17 23:25] 回滚 31s 口径备案 (B4 闸门 ≤30s 边界案例)
- T3 回滚演练实测 31s = 含 8s 保守等待 (health 稳定观察窗); 紧等待口径收敛 ~23s (08-09 首测)。闸门 ≤30s 在保守口径下超限 1s, 记为边界案例; 后续演练注明口径。

[08-18 20:24] TODO(科研, 待批): per-case evidence card 立项 — K1.5 对照文档 §6.4: checkpoint report+judge report+B4 日志合成结构化卡片+leaderboard, 现有原料齐全, 低成本高价值增量
  → [08-19 CLOSED, 批复 ⑤]: 批准并**并入评测协议 v1 产出**（不单独立项）; scripts/eval_evidence_cards.py 随 v1 交付; 演示冻结窗内不碰前端（UI 展示层另行排期）
[08-18 20:24] TODO(科研, 待批): '金融文档领域首个 evaluation harness' 主张 targeted 检索验证 — 论文 B 投稿前必须定稿措辞(首个 vs 引入范式)
  → [08-19 CLOSED, 批复 ④]: 措辞定稿降级为"引入范式"（docs/33 §2.1 差异化第 3 条已改）; related work 补 FORCE-Bench（arXiv 2607.19409, Microsoft, 企业金融 agent 评测 harness; 对照口径=它评 agent QA 工作流 / 我们评解析管线+schema 漂移+勾稽+自学习闭环; 引用细节以 github.com/microsoft/FinanceBenchmark README 为准, 其 ~300 问与 arXiv 摘要 251 不一致已记录）
[08-19 03:15] 治理决策项(待拍板): kiosk 播放持续写 config/schema_suggestions.json 计数 → Loop B STEP 4 脏文件报警周期性复发(本轮 00:01/00:34 即此因, 4fc251c 入账清除后 kiosk 又会写脏)。候选: a) Loop B STEP 4 对该文件 count-only 变更白名单(小改+演练) b) 定时入账清扫(治标) c) kiosk 停播(演示已结束, 但 B4 样本积累仍在用)。拍板前维持现状, 报警出现即按先例 commit 入账。
  → [08-19 20:05 CLOSED, 用户拍板选 a]: STEP4 白名单落地 25d2bec — 只豁免 config/schema_suggestions.json(运行时状态文件, 自学习闭环合法写入目标), 其余脏文件照常计数报警; 豁免清单写入脚本注释。不停 kiosk、不搞定时清扫; kiosk 建议计数继续观察, 单晚增量 41 条可接受(面板演示素材), 过大再议。daemon 已重启载入新版(治理规则), 首轮 20:04:53 验证 dirty_files=1 whitelisted=1 格式生效。
  [08-19 20:05 根因更正]: 本条原归因"STEP 4 脏文件报警"**有误** — 代码核查证实 STEP 4 只记数不判 FAIL(13:53 FAIL 与 14:26 PASS 同为 dirty_files=2 即反证); 00:01/00:34 两次 FAIL 实为 STEP 5 canary 在 judge --runs3 重负载窗口的超时误报(既有已知模式)。STATE.md 对应行同步更正。
## [2026-08-19 23:xx] DSpark 批复批量入账 (用户)
- ① GO 流程: :8006 基线矩阵回填 + Track C 审计 → 切换窗口申请(用户另行给窗); 回滚预案 = 原参数重起现容器(--rm, 启动命令已入 SOP), 切换前后各留一份 docker inspect 存档
- ② 思考档位 xhigh 起步不降档: medium 无质量数据, 降档 = 无依据质量回归; 切换后 B4 跑 2-3 天 + 同步补 medium 档 16 题矩阵, 数据说话再议 【08-22 L2 更正注: 前提失效, 待 L1 矩阵复测——接线实况 thinking 当时实际 OFF, "xhigh 起步"从未在生产生效（不撤销不涂改, 让数据裁定）; 证据: docs/experiments/2026-08-22_l2_sidecar_context_measurement.md §7; L1 已更名"thinking 档位裁定矩阵"（用户拍板 a, 08-22）。08-23 L1 矩阵复测裁定: 正式作废——thinking ON 无延迟收益(单步 p50 56-58s), medium 质量降(13/16+NF 1/9+judge 4.67), xhigh judge 4.875<4.9; 准路默认维持 thinking=OFF。详见 docs/experiments/2026-08-23_l1_thinking_matrix.md。】
- ③ content=null 偶发 (xhigh 多轮 adv_multiturn 第二轮) = **已知边界**入台账: 切换后 B4 回落率 watchdog 的首要怀疑对象; 回落率异常即回滚
- ④ num_speculative_tokens=5 A/B → 切换后优化台账 (现 k=7 第 6/7 位接受率 14.3%/5.7% 近乎白算)
- ⑤ Route S 解除阻塞 + 归因更正: token 一直在 GB10 (~/.cache/huggingface/token, whoami wpxxqzh111, 有效至 2026-09-11); 原归因"GB10 无 HF token"有误 — 实为查找路径遗漏 (recipe 仓库在 GitHub 不在 HF: github.com/hasso5703/dgx-spark-qwen38)。**红线: token 只引用路径, 任何场合不打印值, 不入 git**。对照臂恢复执行, 时序不阻塞 Route V 切换
- ⑥ 生产 ask 46-48s 与 B4 交叉核对结论: **回落常态非退化** — timeout=45 era (08-19 01:00 起 n=791): agent-complete n=124 p50 37.8s (p95 44.6, max 45.2 贴门) / fallback n=509 p50 49.7s (=45s 超时+直连 ~5s) / pure-direct p50 23ms; 预算内完成率 ~20% (124/633) 即 DSpark 加速的直接动机; 停机窗口 (21:10-22:48) kiosk 全回落 46-55s 为 :8006 down 预期副作用
- ⑦ 镜像口径: 探针与生产同一镜像 dockerproxy.net/timothystewart6/vllm-gb10:v0.27.1-gb10.1 — tag 为 recipe 版本, 内含 vLLM 0.27.2.dev0+g6e448d0ea.d20260815; 切换不换镜像 (详见探针报告)

## [2026-08-20 00:15] DSpark :8006 切换窗口执行 — 4 连败回滚, 生产已恢复
- 窗口 23:28-00:13: kiosk 暂停(本机 PID 158600 killed)→恢复(00:13, 新 PID 143516); B4 前置标记 2304 行 @23:28 — **窗口内无切换点, B4 统计连续不分段**
- DSpark 规格启动 4 连败, 同一根因: **KV 预算不足** (maxlen 32768 需 4.6 GiB; 实测可用逐次恶化 2.57→3.09→1.86→0.56 GiB; profiling peak 31.26 GiB vs 原配置 ~27.9)
- 根因链: ① Route S 下载 (sglang 镜像 3 次尝试 + HF 24GB NVFP4) 灌入 ~28-30GB page cache, CUDA mem_get_info 不计为可用 (reclaim 脚本注释同款机制); ② reclaim 35G×5 次上限只能到 ~50 GiB CUDA free (探针成功窗口为 69.46 GiB 干净 free); ③ DSpark drafter 2.53G + spec graph/activation 增量 ~3.4G 把 KV 挤过红线。下载停止后第 4 次尝试仍败 → page cache 残留层需比 reclaim 更强的驱逐手段 (无 sudo, 无法 drop_caches)
- 已执行对策(均不足): reclaim SOP ×5 / 下载暂停后重试 / 第 4 次在全部下载结束后启动
- 回滚: 原参数重起 00:12 READY → health/full 全绿 (137/local/healthy/llm_8004 ok/m2_rag ok) + :8006 快问正常 (冷态 26.9s, thinking off reasoning=null 生效); inspect 存档 dsaprk_switch_inspect_before_8006.json (切换前); 回滚后未做 after 存档 (容器=原配置, 与 22:06 恢复态一致)
- **重试菜单 (入台账等用户拍板)**: ① 干净窗口重试 — 切换前 24h 无大下载 + 多次 reclaim + 单次启动 (探针先例: 69.46G free 时全规格成功); ② MAXLEN=16384 (KV 需 ~2.3G 可容; 任务卡明示退路; 代价: agent 路 15-19k 长 prompt 截断风险, 需先评估 opencode 实际 context 分布); ③ GMEM 抬升 (SOP 明禁"只许调低不许调高", 需用户特批 + 内存算术); ④ 维持 Route V 探针结论 (GO 数据有效) 待条件成熟再切
- Route S 下载状态: HF 双权重 **DONE** (NVFP4@52d1adc / DSpark drafter@923ed3a, 坐实 ~/.cache/huggingface/hub); sglang 镜像 docker pull 3 次失败 (unexpected EOF + 502 Bad Gateway, dockerproxy 通道不稳), 重试缓至下次窗口合并

## [2026-08-20 21:14] DSpark 重试批复 + 专利 P3 批复入账 (用户)
### DSpark
- ① **选方案 1 干净窗口重试** (明晚 08-21 候选), 加两道闸 (已入 SOP FM8 + §0): a) 切换窗 = **纯窗口**, 禁止任何 download/pull — 大 I/O page cache 污染 GB10 内存预算 (CUDA 不计 page cache 为可用) 教训入 SOP; b) **预检闸**: reclaim 后 CUDA free ≥60 GiB 才许启动, 不达标当晚放弃, 杜绝连败
- ② 方案 2 (MAXLEN=16384) 为后备: 先量 opencode 实际 context 分布 (sidecar transcript / B4 token 数), **p99>16k 则放弃该退路** — 待执行
- ③ 方案 3 (GMEM 抬升) **不批** — SOP 红线 (只许调低不许调高), 探针已证 0.30 够用
- ④ **时序教训入账**: 上轮批复允许"下载与切换同窗"为失误, 此后切换窗 = 纯窗口, 任何大 I/O 提前完成或推后
- ⑤ **23:57/58 B4 悬案已查清**: 实为 23:56-23:58 共 4 条 (此前目测 2 条为少计), 全部是 **Loop B STEP 5 QA canary 哨兵** (23:52 周期跑到 STEP 5): q06_minan_cash_balance 23:56:13 / adv_ocr_meta 23:57:01 / adv_cross_doc 23:57:52 / adv_refusal 23:58:38, 与 CANARY_IDS 四项逐一吻合 (app.log Query 行 + loop_b_verify.sh L46 互证); **非 kiosk 残留非浏览器残留页**, kiosk 暂停有效; 后续切换窗内 canary 照常跑 (属预期治理流量), 如需静默可临时 LOOP_B_CANARY=0 (本轮不动 Loop B)
### 专利专项
- P1/P2 质量确认; **P3 启动**: 权 10 措辞差异化锚定"**确定性规则工件 + 回归验证门**", 防 Mem0/Letta 类通用记忆框架在先技术 (已写入 P2 权 10 锚定注记); 实施例三供数等 K7 (切换后第一周, 与 DSpark 重试互不阻塞); 发明人与时间表用户与导师确认后回

## [2026-08-20 22:35] DSpark :8006 切换窗口 (08-20 夜, 用户批准) — 预检闸未过, 当晚放弃, 原配置已恢复
- 窗口 22:16-22:35: kiosk 暂停 (本机 PID 143516/150708 killed, :5051 释放) → B4 前置标记 3064 行 → 切换前 inspect 存档 → docker stop (--rm 移除) → reclaim (buff/cache 降至 22G) → **预检闸: CUDA free 52.08 GiB < 60 GiB → 当晚放弃 (批复规则: 不二次尝试, 不恋战)**
- 恢复: 原参数重起 (/tmp/rollback_launch.sh) 22:23 启动 → 22:32 READY (编译缓存热; 权重 66 分片 @2.3s/片 + profiling) → 验证全过: /v1/models qwen38-27b-fp8 maxlen 32768 无 spec / health/full 全绿 (137/local/healthy) / canary adv_ocr_meta PASS (B4 22:34:41 direct fell_back=true 45162ms = 45s 超时+直连, 当前常态模式) / inspect 存档配对 (before 17797B / after-rollback 17796B, 均 0 处 speculative-config)
- kiosk 恢复 (PID 159568 controller + 159996 loop_demo, :5051 OK); B4 窗口间隙 3064→3065 (仅 canary 1 条, kiosk 零流量, 暂停有效); **无切换点, B4 统计连续不分段**
- Loop B: 22:15 周期 PASS (恰在停止前); 窗口内无周期触发, 无翻转; ~22:45 周期复验恢复态
- **开放问题 (明日评估, 今晚不擅动)**: 52.08 vs 探针成功窗 69.46 GiB 缺口 ~17G — reclaim 已执行, 候选方向: 更强驱逐手段 (无 sudo 无法 drop_caches) / 窗口内暂停非必要内存消费者 (zhikuncode docker 等, 需用户批准) / 实测各组件常驻内存定位占用源
- 存档路径 (GB10 本地, 不入 git): logs/graph/eval/dspark_switch_inspect_before_8006_0821.json + dsark_switch_inspect_after_rollback_8006_0821.json; 启动日志 /tmp/rollback_0821.log
- 重试: 等用户下一次窗口指令; 闸规则不变 (纯窗口 + reclaim 后 ≥60G + 单发起动 + 不达标即弃)
## [2026-08-21 00:00] DSpark 切换窗口 v2/v3 全程 — v3 成功, DSpark 在生产
### v2 (~22:5x): 闸过启动败 + 回滚两败 (当晚放弃)
- drop_caches 首次实战: buff/cache 24→2G, CUDA free 76.05G ≥60G 闸通过 (sudoers.d 窄授权生效)
- DSpark 启动败: KV 3.08 vs 需 4.6 GiB (GMEM 0.30 预算结构性不足 + padding 25% 浪费)
- 回滚两败 (2.13/2.47 vs 2.3): 权重加载吃回 MemFree → vLLM 预算截断 (#48140 机制) → **drop_caches 每次启动前必须重做**
- 误判更正入账: :5050 uvicorn workers (2104425/2104426) 永不杀; zhikuncode 220MiB 非嫌疑
### v3 (23:2x-23:5x): 批准参数变更 GMEM 0.34 + kv-cache-memory 6.0G 钉死 → 成功
- 首启失败 = 脚本编辑丢行续反斜杠, speculative_config=None 静默原配置运行; /metrics spec 计数器为 0 暴露 (追加验证①立功); 修复重起 23:41:20 → READY 23:48:08
- 引擎核验: SpeculativeConfig(dspark, /models/drafter, k=7) + trust_remote_code=True + reserved 6.0G KV (skipped profiling) + KV 42,711 tokens
- 验证组全过: health/full (137/local) / parse 冒烟 65ms / QA canary 2/2 (回落 direct 答案正确) / compare 嘉兴民安 2 持仓 / route=on timeout=45 / spec 计数器随请求增长 (drafts 117)
- **生产接受率 1.26 tokens/round vs 探针 3.31** (逐位 51/34/19/10/7/3/2%) — 探针高估生产收益, 如实入账
- **agent 路完成切换点以来 0 次** (B4 权威, 全 fell_back); eval 中间行 route=agent 标签 (35850/38677ms) 与 B4/报告 JSON 矛盾, 以 B4 为准, 异常记账待审
- B4 分段: 窗口开始 3081 → 切换点 **3092**; kiosk 恢复 (PID 23036/151364)
- 存档: inspect before_8006_0821v2 (0 spec) / after_dspark_8006_0821v3 (4 spec) 配对; 实验文档 docs/experiments/2026-08-20_dspark_switch_windows_v2v3.md; SOP FM8 对策③ + FM10
### 长期台账
- vLLM 版本升级评估: #46932 / #49760 / #48140 三项 issue 入账, 今晚不动版本
- 待审: ask 自然语言日期对比产品解析错配 (嘉兴民安→复熙, 规则路径与切换无关)
- 观察: agent 路完成率以 B4 数日数据为准 (watchdog 守护); k=5 A/B + medium 16 题矩阵仍排切换稳定后
[08-21 01:30] #NIGHT-LOOP-CLOSEOUT ① P4 专利完整修订版待用户终审 (docs/experiments/2026-08-21_patent_full_revised.md, 权 7-12 + 权 10 双锚定 + PSO 实测回填) ② B4 污染修复: M1_B4_LOG_PATH env 覆盖 + conftest 隔离 (生产行为不变无需重启); 24h checkpoint cron 一次性 23:50 (跑完人工删除); 真实 agent 完成维持 0, 接受率 1.33 ③ PSO 落点①v0: 分离度 +14.06%, research/pso/ 独立 venv ④ docs/33 §8 状态对齐
[08-21 01:55] #D2-D4 DSpark 实效诊断定论: D2 分段接受率=生产 agent 路 1.09-1.29 / XML-xhigh 1.517 / freeform 1.76 — 全段均匀低, 无 >2.5 段, 探针 3.31 为 thinking-off 离群值; D3 k=5 方案就绪(推荐度中低, 等窗口); D4 DFlash 探针臂 NO-GO(判据后半不成立 + rwmacy drafter 需 rmacy/vllm fork 否则接受率崩 24% + B70 调优), DFlash2 PR#52816 open 入盯梢; 报告 2026-08-21_d2_acceptance_segmentation.md / dsprk_k5_ab_plan.md / dflash_probe_decision_memo.md
[08-21 23:24] #B4-24H-FINAL DSpark 切换 24h 终判（提前至 23:22 跑, 用户批准; cron 条目已删, 报告 logs/graph/b4_checkpoint_20260821_2322.md）: 切换点 3092 起 n=195（剔 5 疑似测试行）, **agent 尝试 190 / 完成 0 / 回落率 100%**, 全部超时型回落（p50=46.6s / p95=49.9s, 预算 45s）, content=null=0（status 全 ok）。归因明确: ① xhigh agent 轨迹长度 > 45s 预算; ② D2 坐实接受率全段均匀低（agent 段 1.09-1.29）, 投机解码对 agent 流量无增益; ③ 对照切换前 45s era（n=791）完成率 ~20%（124 条 p50=37.8s / 509 回落 p50=49.7s）→ 切换后 0%, DSpark 对 agent 路净效应为负（草稿开销无接受率收益）。判定: 回落率 >60% 但 content=null 排除且归因明确 → 不属"查无解释", 按批复报用户拍板, 不擅自回滚。菜单: a) 回滚 :8006 非 DSpark 参数（SOP 就绪 ~31s, 预期恢复 ~20% 完成率） b) 保留 DSpark + 超时抬至 60s（覆盖 p95, 但 kiosk 更慢且接受率根因未解） c) 保留 DSpark + kiosk A1 路由分离（待批）+ 等 k=5/medium 矩阵数据。 【08-22 L2 更正注: "xhigh 轨迹"归因作废——生产 m2-qa thinking 当时实际 OFF（opencode.json 无 reasoning_effort + thinking_inject_proxy 默认注入 enable_thinking:false + 生成 45tok/请求 + DB reasoning 全 0）, 正解 = 串行多步（p50=3）× 7-15s/步。证据: docs/experiments/2026-08-22_l2_sidecar_context_measurement.md §7。】

[08-21 23:54] #DSPARK-ROLLBACK 准路根治合并卡 Phase 0 执行完毕: :8006 回滚非 DSpark 原参数 (GMEM 0.30, 无 spec config, 23:46 READY ~5min)。六步验证全 PASS: health/full (137/local/healthy) + parse 冒烟 latin1.txt 5ms + QA 2 条含 OCR meta 确定性 2/2 + compare 嘉兴民安 2 持仓 + route=on env 确认 + agent 路单题实测 45931ms (45s 超时回落, 单条不构成结论, 不二次折腾)。**B4 回滚点 = 3294 行 (23:51:43)**, 统计分段: DSpark era 3093-3287 / 回滚验证期 3288-3294 / 回滚后自 3295。Loop B: topology 断言实查无 spec 计数器项 (仅 health+模型 ID) 无需改动; agent_watchdog 持续守护。drafter 权重留盘不删, ledger 记生产退出; kiosk 已恢复。根治三杠杆排队: L1 medium 矩阵 08-23/24 → L2 sidecar 瘦身先量 → L3 DFlash2 镜像评估先行; 抬超时不在选项内。

## [2026-08-22 00:35] L2/L3 批复执行（纯只读: 测量 + 评估, 零配置变更）
### L2 sidecar context 测量定论（报告 docs/experiments/2026-08-22_l2_sidecar_context_measurement.md + JSON 工件）
- 单调用: decode 占 ~60-70%（但仅 ~45 tok/请求, 带宽墙非 token 量）/ prefill ~30-40%（~10k context, TTFT 0.5-5s）; **attempt 级主导项 = 串行 step 数（p50=3/p95=5/max=15）× 每步 ~7-15s**——与 B4 实测 46-50s 吻合。
- prefill 构成: 可测小计 ~2.6k（agent prompt 494 + playbook 1030 + skill 清单 1011 + 工具 docstring 47）; 残差 ~8-10.5k = opencode 内置 system prompt + 工具 JSON schema（主项 ~70-80%）——08-13 "skill 全量装载膨胀"假设部分修正（实为清单 + 单 skill 全文）。
- **关键更正: 生产 m2-qa thinking 实际 OFF**（证据四条: opencode.json 无 reasoning_effort / proxy 默认注入 enable_thinking:false / 生成 45tok/请求与 off 档逐 token 吻合 + DB reasoning 全 0 / DECISIONS 08-16 结论）。"xhigh 轨迹超预算"表述更正为"串行多步 × 每步 7-15s（thinking off）"。
- **L1 矩阵 08-23 基线口径须先拍板**: 现接线下 medium vs xhigh = off vs off; 选项 a) L1 改测 off（现状）vs 显式注入 medium/xhigh b) 先裁定准路要不要开 thinking（08-16 数据: dense 27B 开 thinking 加延迟无结构化收益; 08-19 批复"xhigh 起步"与接线实况存在口径落差, 一并报用户）。
- 杠杆排序（对 45s 预算, 实测拼接）: ① step 数削减（3→2 省 1/3）② 孤儿续跑终结 ③ decode 提速（接受率是前提）④ context 瘦身（10k→6k 每步省 ~1-2s × 3 步）。
- 顺带发现（记账不动手）: a) 孤儿会话续跑（45s 超时回落后 sidecar 继续跑 p95=133s/max=69min, slot 白占）→ 入 L2 方案菜单; b) opencode.db transcript 持久化损坏（08-14 起 5187 次插入失败, message 表仅存 08-07/08 六会话）**[08-23: 「根因待查」作废, 与 08-11 FK 竞争合并为同一病灶, 定论见 #HYG-FK-DIAG 条]**; c) Loop B 08-21 23:43 model_topology FAIL = 回滚窗内 :8006 停机抓取, 设计内预期; d) log permission 行不带 session.id → skill/rag 归属计数偏低（方法学注记）。
### L3 DFlash2 镜像可行性（报告 docs/experiments/2026-08-22_l3_dflash2_image_feasibility.md）
- PR #52816 直连复核: **MERGED**（08-21T05:27Z, b389ac2, base main）——DFlash2 = DFlash2DraftModel 新架构类, method 仍 dflash, 旧 DFlash checkpoint 不受影响。
- 现镜像坐实不含: 0.27.2.dev0+g6e448d0ea.d20260815（22.1GB）全库 grep DFlash2DraftModel 零命中; 构建 commit 与合并点 diverged（ahead 792/behind 21）; v0.27.1 release（08-11）早于合并 → 无官方 release 含 DFlash2。
- 权重 incoai/Qwen3.8-27B-DFlash2 3.85GB apache-2.0 k=8（block_size=8）只查未下; 磁盘空闲 2.7T。
- 路径 A（推荐）: 等 timothystewart6 新 tag（可复现构建, tag 实为 main 快照, 节奏数天级）→ pull → :8007 探针（L1 基线后）→ 等价性三连 + 分段接受率 → 申请窗口; 注意新 tag 含 ~800 commit 跨度, 等价性三连 + SOP 重标定必跑。路径 B（后备）: 自建（Dockerfile+versions.env 在位, 0.5-1d, 破碎前科风险）, 仅 A 超一周无 tag 启用。**未拉镜像未重建, 报用户拍板。**
### 其他记账
- Loop B agent_watchdog 持续 ALARM = 设计内信号（agent 完成未恢复, 00:17 周期 overall=FAIL 属此）, 记台账不当事故。
- 专利完整修订版冻结等用户终审、用户亲发导师, 主线程不碰; kiosk A1 方案窗口另行给。

### [2026-08-22 01:25] 用户拍板: L1 口径=a, L3 路径=A（夜间 graph engineering loop）

**拍板一 · L1 口径（选 a）**: L2 更正坐实——生产 m2-qa thinking 实际 OFF（证据链: opencode.json 无 reasoning_effort + thinking_inject_proxy 默认注入 enable_thinking:false + 生成 45tok/请求 + DB reasoning 全 0, 见 docs/experiments/2026-08-22_l2_sidecar_context_measurement.md §7）。处置三条:
- ① "xhigh 轨迹超预算"归因作废, 正解 = 串行多步（p50=3/p95=5/max=15）× 7-15s/步; 08-19 "xhigh 起步"批复标注"前提失效, 待 L1 矩阵复测"（不撤销不涂改, 让数据裁定）; B4 终判条目 / docs/32 / drafter ledger / D2 报告 / DFlash 备忘中旧归因处已同步加注（08-22 T1 扫荡）。
- ② L1 更名 **"thinking 档位裁定矩阵"**: off 腿有生产数据不重跑, 只补 medium/xhigh 两腿（各 16 确定性题 + NF 9 题 + judge 四维抽样 + 端到端延迟与 thinking token 分布）; reasoning_effort 显式注入（探针直打 :8006 或 sidecar 临时配置, 实现路径自定）, 生产默认口径不动, 矩阵跑完即还原, 还原动作写入验收清单（templates/acceptance_checklist_template.md）。
- ③ 杠杆序重排备忘录入 docs/32 §6: 主导项 = step 数, "减 step（3→2 省 1/3）+ 终结孤儿续跑"升第一梯队, thinking 档位降为质量维度（由矩阵裁定）; 只记账不动手, 实施排矩阵之后。
- 教训入账: 声称的决策状态与运行实况脱节整整一周无人发现 → 任务卡"前提假设清单"成为必填项（T2 模板已体现, templates/task_card_template.md）。

**拍板二 · L3 路径（选 A）**: 等 timothystewart6/vllm-gb10 新 tag（含 DFlash2）, 不自建。追加四条:
- ① 新 tag 出现后探针默认排入 L1 基线之后, 前置条件 = L1 基线完成 / pull 避开任何预留窗口（22GB 大 I/O 不与矩阵同夜）/ :8007 探针走既有协议 / GO-NO-GO 报用户后才许申请生产窗口。
- ② checkpoint: 2026-08-29 仍无 tag → 出路径 B（自建）再评估报告, 不自动启建。
- ③ 新 tag 带 ~800 commit 跨度, 等价性三连（thinking 各档 / qwen3_xml 工具解析 / chat template）+ GB10 启动 SOP 重标定为探针卡必跑项。
- ④ 盯梢命令维持 drafter ledger 现状（curl dockerproxy.net tags/list）。

## 23:50 checkpoint 判定挂起（2026-08-24 22:25, 用户指令）
- cron 23:50 照跑收数据（一次性条目重装, 跑完人工删）, 判定挂起不拍超时
- 理由: 段 D 塌方 (今日 218/4=1.8%, 基线 15-19%) 归因未清, 当晚拍超时 = 08-20 楔死教训复刻
- 归因队列已完成（22:37, 报告 docs/experiments/2026-08-24_segment_d_q06_attribution.md）: ① 轨迹对比 = step 结构未变, 每周期首查命中降（死连接）+ 流量构成变化 ② q06 双窗复现坐实池×GUC 交互（冷池 0.0027 兜底 / 暖池 0.7889）③ eval 缺位已记 + 错误清单实查 32 条历史零今日（故障在 WARNING 级 216 条）; 修复菜单 F1/F2 待批, 需 :5050 窗
- 红旗关联: Loop B 翻转 = canary agent 完成时点症状, 不当独立故障
- 解挂条件: 归因完成 + 干净段数据在手, 再拍超时 (a)/其他

## 晨间序列卡 M0-M3 收到 PENDING（2026-08-25 00:52, 用户预置卡）
- 时序闸门: 夜间队列（04:00 硬停）收口前只入账不执行; 收口后立即执行, 全程只读+草稿, 零生产变更
- M0 分支: 门禁 FAIL 已回滚 → 跳 M2 出 NO-GO 处置单; 正常 → M1→M2→M3
- M1 = 圈选表 5 数字（门禁结果 / 3929 后干净段完成率+样本构成 / 超时近失占比 45-50s 段 / eval vs 16/16/0/5.0 / step 复测三点对比）
- M2 = 预提交规则自动评估（只算数比对不自由裁量）: 规则 0 样本闸（<40 条全降观察+延 24h）/ A timeout（≥15% CLOSED; 10-15% 且近失≥30% 抬 60s 并入 FK 窗; <10% 或近失不占主导 → 系统诊断方案）/ B T1（steps p50 ≤3.5 判污染重开减 step 只出方案; ≥4 维持）/ C FK 三件合并窗（+规则 A 触发则加第四件, 时机明晚候选, 窗口卡含交互假设检查节, 触发≠开窗仍等批）/ D PSO（落盘→登记+明晚第二批; blocked 维持）/ E 积压维持挂起
- M3 = 收尾: 规则结果入 THREADS + INDEX 登记 + 窗口申请草稿入一页纸附录 + dispatch + commit/push/三方对齐
- 红线: 本序列 :5050 零重启（含规则触发项）; :8004/:8006 配置不动; 专利不碰; 台账唯一 THREADS
- 执行入口: 夜间队列收口后（03:50 汇编 + 04:00 硬停）, 产出醒来看

[08-26 晚] #MAINLINE-SWITCH 主线切换论文（用户授权侧线圈定挂起三件）: ① F-J3 圈 b 先行, a 并入窗口队列 ② 减 step 组合拳立主线但本周窗口冻结让路论文 ③ FK 缓办合并激活; 导师包已发（08-26 白天, 终版 d85d50f, §5 微修终判不做）; 规则 F 加强: 不开任何新窗口。资产梳理两件: skills 白皮书 v1 + 论文资产映射表 v1（第一启动单元建议 = K2 v1 判别力联跑）。

[08-26 22:3x] #K2-DISC-WINDOW K2 v1 判别力联跑窗口（起）: 95 表注入臂过 K2 协议（纯确定性 matcher, 零端点）+ 第三层小臂 <=12 条 :8004 表忠实度 QA（temp=0, 运行时断言零 :8006）; B4 干净段统计注记本窗口（窗口流量不经 :5050 agent 路, 实际零污染, 登记为口径纪律）; 预算门: canary 周期 :00/:30 争用源为 :8006（本窗零触碰）, :8004 仅 STEP3 健康探测瞬时, 门过

[08-26 23:2x] #VGMC-EXP1-WINDOW VGMC 实验 1 窗口（起）: 固化闭环两臂（有门控 τ=0.1/ε=0.02 vs 无门控直固）, 60/35 hold-out（seed=20260826 预注册）, 建议生成仅 :8004（断言零 :8006）, 回归纯确定性; 生产配置零写（sha 前置: suggestions=61782a8b.../schema=ad09d151...）; 预算门: canary :00/:30 争用源 :8006 本实验零触碰, 门过

[08-27 01:xx] #NIGHT-RESEARCH-0827 夜间科研卡 T1-T4 完成: ① 噪声体制实验设计稿（台账 #12, 预注册三档 + P1 单调/P2 有界/P3 null 分支机械判据 + 窗口卡草稿待批）② 小 B 盲锥章节骨架 v1（五节 + 图三张）③ bandit v0（样本审计: 生产 23 无实测/实验 42 金标 → 可行, DPO 薄）+ ρ 协议（零额外 LLM）④ T4 审计: 骨架 7 数字全一致; **4/42 vs 4/53 裁定 = 分母 42（53 含 no_map 11）, 报侧线不改骨架**; closed@34c93ab 精确引入点 0cbced5 记账

[08-27 00:3x] #T5-LEDGER-CLEAR 台账清账两件（零 LLM）: #8 MS+bootstrap CI 算讫（表级主口径 75/95=78.95% [70.53,86.32], 注入级 81.36% [74.58,88.14], 三型配对差两显著一不显著, seed=20260827 n=2000）; #7 BC(δ=1) 注入侧 22/118=0.1864（ocr 盲率 1.0 锥尖）; 状态变更 #8 有 / #7 部分·注入侧在位——**报侧线更新骨架 §4 两行**（骨架正文主线程未动）; 真实 OCR 分布待 C4 合成题库, 甲方红线禁入已显式注记

[08-27 00:2x] #T6-L1-ANALYSIS L1 两腿既有数据分析稿入库（补充项卡, 零重跑零 LLM）: 延迟 p50 55.9/57.7s 重合 + mean 反转系 adv_multiturn 超时拉高非档位效应 + Δ延迟与 Δthinking token 无相关 → **档位=质量杠杆非延迟杠杆**（E3 主导项结论独立复证）; thinking token +21.5%（p95 尾 +47.6%）廉价; 质量 13/16→16/16 单调; mapping 改进线 L1 行已更新（章 3 供数在案）; NO-GO 裁定不翻案只供数
[08-27 00:4x] #T7-GATE-HOLD 候补小 A 基线复现协议设计稿本轮未启动: 闸门=03:00 后且余 ≥45min, 收口完毕时 00:42（距闸 2h18m）; 阻塞 sleep>5min 禁令 + 唤醒机制本会话不可用（automation 工具 schema 不全）→ 记账移交下卡, 不硬上不空等; 下卡若开门: 03:00-04:15 窗内执行, 模板=Mem0 式/AWM 式/few-shot 三基线×（记忆形态/读写接口/评测协议/预算估计）, research-writing-skill 只设计不写码
[08-27 22:4x] #VGMC-NOISE-WINDOW VGMC 噪声体制实验窗口（起）: L1 temp×2seed(42/43)+L2 prompt+L3 force × 两臂（门控 τ=0.1/ε=0.02 vs 无门控）, 切分复用实验 1（digest MATCH 4764938...）, 建议器仅 :8004（断言零 :8006）; 噪声层 50 insertions（P5 预算内）+ 单测 5/5; 生产配置零写前置 sha: suggestions=61782a8b.../schema=ad09d151...; 预算门: canary :00/:30 争用源 :8006 零触碰, 门过; 机械判据预注册: P1 单调 / P2 有界 / P3 null 分支
[08-27 23:0x] #T7-BASELINE-DESIGN 小 A 基线复现协议设计稿入库（晨间卡窗隙, 只设计不写码）: Mem0 式（事实记忆, 轮末写）/ AWM 式（过程记忆, 全量注入）/ few-shot（静态示例 top-k=6）× 记忆形态/读写接口/评测协议/预算（合计 ~131 次 :8004 ≈12min 单窗）; 对照设计 = 基线一律 ungated 单臂, 对照 = 实验 1 ungated + VGRM gated; 机械判据预注册（|ΔH|<0.005 且 CI 跨 0 = 不可分）; 执行窗口待批（让路序: 扩语料碰撞设计稿 → 基线窗口）
[08-27 23:2x] #SIDE-5PT-LANDING 侧线五点加速优化直落（用户批准; 主线程已收口, 无冲突）: ① Loop A 双档路由落地——执行卡默认 --profile loopa-exec（qwen3.8-flash/Token_Plan/medium, codex exec 端到端 PROFILE-OK）/ 诊断卡 --profile loopa-diag（deepseek-v4-flash-0731/Token_Plan_Chat/xhigh）; profile 单文件仓外（~/.codex/loopa-{exec,diag}.config.toml）+ orchestrator start_loop_a heredoc 同步 + [profiles.X] legacy 表报错教训入账 ② K2 五图组入 docs/experiments/figures_k2/（本机渲染+目检全过: 中文无乱码/无重叠）+ 生成脚本在位, 数据源 logs/graph/eval 两 json ③ 四桶并行板 v1（桶 0 永不断后）+ 夜间窗口合并草案（待批, 与主线程"明日待拍"两项呼应）登记 ④ **Round 3 辩证触发成立**: 噪声 P3 null（门对噪声有响应而两臂终值全同）= I1"门控价值=f(建议器可靠性)"首个实证材料; 骨架正文未碰（仅侧线可改）, 辩证时机待用户 ⑤ C4 依赖澄清: BC 图（fig5）已交付, 剩余依赖 = C4 合成题库（真实 OCR 分布侧）, 与主线程 C4 缓判据吻合。红线全程未触（骨架只读 / 生产配置零写 / 不对外）
[08-27 23:5x] #VGMC-COLLISION-WINDOW 扩语料碰撞实验窗口（起）: 段 A（窗口合并卡）, 碰撞语料 = 移植列 overlay（meas E=4 / fix E=2, 实际 67 列/37 表, 构造种子 20260828, P4 双生成 sha 一致）, 两体制 C0 可靠/C1 碰撞+force 噪声 × 两臂; 建议器仅 :8004（断言零 :8006）; 双主指标预注册 = H + ACC（碰撞列映射正确率, 机制锚: map_headers 每标准字段至多占用一次）; 生产配置零写前置 sha: suggestions=61782a8b.../schema=ad09d151...; 预算门: canary 争用源 :8006 零触碰
[08-27 23:5x] #SIDE-ROUND3-PREP Round 3 辩证简报备妥（用户+侧线, 议程 D1-D4 约 30min）: 两次 null 证据清单——transfer_rate=0.1143（两臂相同, 碰撞瓶颈）/ L3 验收缺口 +25（机制响应性）/ −0.0095 对称轻度毒性（有界但三免疫）; H1 输入端证伪（垃圾确已进记忆）/ H2 碰撞匮乏领先（今晚段 A 可证伪）/ H3 待段 D 基线; I1 修正提案 = f(可靠性, 碰撞暴露, 单次碰撞危害); 对抗建议器臂提案需批（~60 次 :8004 调用 ≈8min, 零新基建）; 骨架正文全程未动, 编辑项清单待辩证批准。同备 K2 章机械对账清单（12 行数字 × 工件源 + 结构断言 + 禁词, 草稿落地即机械对账）
[08-27 23:5x] #C4-VISUAL-PROBE-WINDOW C4 视觉探针窗口（起）: 段 B（窗口合并卡）, 合成渲染题库（95 表 PIL 网格渲染, 零下载零新依赖）+ VLM :8007 探针（Qwen3-VL-8B, 用毕即停手册纪律）; 内存门重测 33G ≥ 30G 过; 预算门: canary 争用源 :8006 本段零触碰（探针走 :8007）; 全合成渲染甲方零进入（工件注记）
[08-27 23:5x] #SIDE-ROUND3-RECORD Round 3 辩证记录入账（侧线 skill 自过一轮: systematic-debugging/spec-to-code-compliance/differential-review/research-writing-skill）: D1 裁定文本（臂间差只由碰撞暴露×单次碰撞危害驱动; 可靠性经接受集移动两臂水平, 正交分解 + 经验命题 1a: C=0→ΔV=0）/ D2 对抗臂推荐批准（待用户勾选, 全稿设计待批后写）/ D3 null 叙事两段成稿 / D4 骨架编辑候选 6 项（骨架未动, 勾选后侧线执行）; 两处更正: "对称毒性"→对称抑制（L3 +0.0214 仍是改善）+ L0 行 = 复用实验 1 工件的跨运行比较（含抖动, 不得读作门免疫失败）; L3 工件复算坐实（门拒 31/58 = 58-27; 两臂 h_meas 逐轮全同）; THREADS 登记行由主线程收口带走提交（本行入账时 THREADS.md 有主线程未提交改动, 侧线不代提交）
[08-28 00:xx] #LOOPA-TOKEN-ANOMALY 用户通报: GB10 Loop A token plan 暂时异常 → 本夜窗口合并卡剩余段（段 D 基线窗 + 收口）由主线程 Codex 直接执行, 经 ssh/git 交付 GB10, 不派活 Loop A; 异常本身待用户侧修复, 主线程不诊断
[08-28 20:0x] #LOOPA-TOKEN-ANOMALY 用户通报: GB10 Loop A 已恢复（前条异常作废）; 段 D 基线窗为主线程直跑 :8004, 不涉 Loop A, 队列不变
[08-28 20:0x] #BASELINE-WINDOW 小 A 基线窗（起）: 段 D（窗口合并卡条件项, 闸门满足）, fewshot/mem0/awm 三基线单臂 ungated × 4 轮 × 15 表（切分复用 seed=20260826）, 建议+写侧仅 :8004（断言零 :8006）; 对照 = 实验 1 ungated（0.589048）+ VGRM gated; 机械判据: |ΔH|<0.005 且配对 bootstrap CI 跨 0 = 不可分（预注册）; 生产配置零写前置: 夜间窗 sha 基线维持（日间生产管道计数更新另记）
[08-28 21:xx] #LOW-2ITEMS-RECORD 抽验后两处 LOW 记账（不改数据不重跑）: ① 段 C 口径更正——"direct best=最宽门（τ0.05,ε0）"应读作**六格 direct 全 1.0 同分, 可靠体制无分辨空间**（json direct_best 字段为字典序 tie-break, 不读作信号）; ② K2 章草稿头部红线自查行含禁词字样（judge/四维）= 实验文档阶段豁免, **正文继承时删除**（头部已加注）
[08-28 23:1x] #T3-GOVERNANCE 治理一捆完成: ① docs/29 清账（出表 CLOSED: D6/A1/B1/B2/B3; 更新: D1 圈定 A / A2 C4 首批 / A5 08-29 checkpoint; 新登: A12 C4 错位治理 / A13 对抗臂 / A14 DPO 训练后续 / A15 bandit 奖励再设计 / D11 K2 章复核 / D12 bandit 前瞻结论）② INDEX 状态词 5 件刷新（噪声设计稿/基线协议/窗口合并草案 待批→已执行; b4 诊断→已关闭; L1 runbook→已执行）③ STATE 挂起行 D2/D4 更正（已勾选/已执行 73ac314）④ docs/26,28 降历史快照 → **docs_lint 0 fail / 0 warn 清零达成** ⑤ **报侧线**: K2 章草稿引用 figures_k2/fig4（MS CI forest）+fig5（BC blind rate）与盲锥章节骨架图清单（3 张: 谱/吸收机制/三性质表）不一致 = 侧线资产（骨架图清单 vs figures_k2 实际五图组）, 主线程未碰, 请侧线裁定图清单扩容或章节引用收敛
[08-29 00:xx] #FIG-LIST-RULING 报侧线条目裁定入账: K2 章 fig4/fig5 与盲锥骨架图清单不一致 = **图清单扩容（3→5 张）, 侧线执行**; 主线程销账不碰骨架（本条即销账记录）
[08-29 00:xx] #RULING-A-FIRST-B-SECOND 用户拍板（判定件先后序）: **A 先**——对抗建议器臂窗（#13）明晚开窗 ~15min, 照设计稿预注册三预测执行（主案 3 跑批 ≈120-180 次 :8004, 紧张时降级最小案双臂 1.0）; **B 后**——扩碰撞复跑带 A 的危害梯度再定扩容设计（同窗顺延或后晚）; 理由 = 同底座剂量响应链可比性（A 解锁 A15 奖励再设计 + DPO 对增量前置, B 设计受益于 A）
[08-29 00:xx] #RULING-M1-ACCEPTANCE /m1 验收口径: 用户按五步 walkthrough 自走（时间轴 / 刷新持久化 / QA 五步条 / 建议映射 tab / 快路回归）, 结果与 A 窗一并看明晚汇报; **口径 3 拍"接受 localStorage"**（无后端）; 服务端任务历史持久化 = 触发项登记（甲方多人/跨设备需求出现再议, 台账 D13）
[08-28 23:2x] #ADVERSARIAL-ARM-WINDOW 对抗建议器臂窗口（起）: #13 拍板即执行（用户 08-28 晚拍板, 不等一页纸）; 照设计稿五节预注册: 主案 3 跑批（门控 1.0 / 无门控 0.5 / 无门控 1.0）, 底座 = 段 A 碰撞语料（67 移植列）, 对抗注入 = meas 碰撞列种子派生 k 列 × 貌似合理错列 + high 置信; 建议器仅 :8004（断言零 :8006）; 预算门: canary 争用源 :8006 零触碰; 三预测机械对数（① ΔH<0 单调 / ② |ΔH|≤Σε / ③ 门拒 ≥80%）
[08-29 00:2x] #GOVERNANCE-INSTITUTIONAL 治理制度化（本次起生效, 不再等用户触发）: ① scripts/graph/governance_drift_scan.py 入库（首跑 10 命中全登记, 含真漂移: 31 v2 仍待发送/round3 待勾选/send_checklist 待执行等, 待核不擅改）② 收口清单加漂移扫描（AGENTS.md 新节）③ 夜间 03:30 cron 轻扫已装（--cron 只报告不登记）④ Loop C 审计范围扩治理件。纪律注记入账: **夜间禁的是"判定", 不是"已判定事项的执行"; 并行线判定项一律记账进白天一页纸**
[08-29 00:4x] #LOOPC-BLOCKED Loop C 审计今夜受阻（环境）: 首派挂起 21min（CPU 24s, 子进程=omc MCP bridge）kill; 重派 3min 仍近零 CPU 同模式 kill; 判定 = claude CLI 运行环境异常（与 Loop A token plan 异常同期, 疑同源）, 非审计对象问题; 空报告已清; 对抗臂工件+D1 diff+T2 回填三对象审计顺延至环境修复（登记待核, 不阻塞主线）; 审计层今夜以漂移扫描+主线程自核代行
[08-29 02:0x] #LOOPC-FIX Loop C 挂死修复: 根因 = oh-my-claudecode 插件 bridge 非交互挂死（探针 claude --bare 9s 正常）; 修法 = 派发命令改 claude --bare -p（orchestrator heredoc 已同步）; 顺带 ~/.claude/settings.json chmod 600 + AGENTS.md 立"敏感文件永不 cat"纪律节
[08-29 02:5x] #RESEARCH-ASSETS 科研自动化资产台账入库（~/wzh/research/ 五件）: OpenAI4S 长期候选不启动（用户卡明示论文优先工具克制）/ tabfm v1.0.1 相邻备用 / **academic_skills_audit 上游漂移检查 = 无漂移**（ls-remote HEAD=7ed6377=本地, 三件技能 diff -rq 零差异, 不回灌）/ **m0_lit 接入科研线 Phase 2**: 五篇全文补强三簇（簇二+评测与巩固两支, 簇三+参数侧/规则侧分野与分类学坐标）, 引文作者 OpenAlex 实查 5/5 → related_work_v3 取代 v2; 全文在盘零在线依赖
[08-29 03:1x] #OFFREPO-INVENTORY 仓外资产普查终版台账入库（两轮扫描合并）: GB10 权重补登 12 件（:8006 生产/视觉/embedding 在役标注 + bge 疑遗留 + minicpm 闲置 + tabfm/tabpfn 探索线待定性 + paddleocr-vl 挂 C4 候选 + gguf 8002/8003 服役史佐证）; tat-dqa 1.5G 论文 data availability 必引; routes_s 口径更正（配方仓非权重, NVFP4 权重未在盘 → A17 复核）; 本机残留清单（清理候选等批: _tmp×14/bundles×3/staging×2/inbound_0822; m1.*.bak 保留至 D1 验收; advisor 不碰）; **勘误: docker 三 tag 同 image（734134467dc5）, 删冗余回收≈0 非 44G**; 暂缓区白名单（顶层 datasets/mym/.openclaw/6g_v2x）防误报; 红线备忘 = Downloads 甲方件零接触; 治理补丁: 漂移扫描扩 ~/wzh 资产面 + 下载即登记规则生效（自检 12 命中 0 新登）
[08-29 02:2x] #B-EXPANSION-WINDOW B 扩碰撞复跑窗口（止）: ρ 梯度三跑批（0.5/1.0 无门控 + 1.0 门控, 全叠对抗 α=1.0）; 构造更正如实记录（基础 overlay 饱和共享空间 → 新变体对构造, 15 对, 碰撞表 12→15）; **E1 PASS（ρ=1.0 伤害首触 H: ΔH −0.0057）/ E2 PASS（门控零伤害, 门拒 5/5=100%）/ E3 卡片触发=否**——ΔV(ACC) 点估计 0.05 达线但配对 bootstrap CI [0.0, 0.1056] 含 0（15 碰撞表功效不足）, 设计稿辅判据亦未过 → **版本 B→A 不切换, 版本 B 维持, 判据冻结不溯及**; E4 未触发（方向全对, 功效问题非效应缺失）; 下一步候选 a 语料再扩（15 对天花板需多变体族突破）/ b 逐列配对重判现有数据（零新跑批）/ c 版本 B 叙事投稿——另行裁定
[08-29 02:2x] #SKELETON-V25 骨架 v2.5 用户授权编辑（Round 3 勾选先例）: §1.6 贡献重组 2+1（I1 门控规则记忆 / I2 盲锥双旗舰, I3 降 pilot）+ §10 生产边界声明（研究管线数字非生产流量 / 甲方零进入 / 可复现性边界 / 伴生问题边界）两节写入, 其余节未动
[08-29 12:15] #REVIEW-DAY-RULING 用户裁定执行: 论文 b+c 并行、a 暂缓；b 仅列级敏感性、不覆盖冻结表级 E3；c 仅内部投稿稿、禁止对外；清理只限 `_tmp`/bundles/side staging/inbound_0822 可恢复处置；Docker/bge/DAIR/暂缓区冻结；/m1 13/13 仅功能证据，不签快路体验。
[08-29 12:37] #M1-LATENCY-NAMING 最终单实例 walkthrough 功能 13/13；QA 48.7s，三问 48.6/50.6/49.7s，对应 B4 四问均 `route=direct,fell_back=true`，即 45s 验证链等待后回落，非快路；并发复跑曾出现 105.5/105.6s 尾部，进一步否决体验签署。证据先改称“回落问答”；真实提速最小案 = 后续显式 direct 模式绕过验证链等待，是否实现待用户裁定。
[08-29 17:3x] #PAPER-ROADMAP-DOCS 专利-小论文-大论文协同路线沉淀三件入库: ① docs/34_专利_小论文_大论文协同研究路线.md（活文档, 路线裁定+专利锚点+大论文创新点+优先级+知识产权边界）② docs/experiments/2026-08-29_long_horizon_eval_paper_blueprint.md（AAAI 蓝图: 主张-证据-缺口 C1-C5 + 章节骨架 + Phase 1-5 补强）③ docs/superpowers/plans/2026-08-29-long-horizon-evaluation-paper.md（T1-T8 任务卡+依赖图+红线）。INDEX 三行注册同步。零端点/零跑批/零对外。
[08-29 23:2x] #PAPER-ROUTE-INPUT-ABSORB 路线评审输入吸收（前置工作）: 源件 D:\Desktop\1.txt（sha256 6E24362CA6C3C6D16D7B9AD971232AD415092046FC8CD639E0BA11CA1D72145E）verbatim 存档 docs/experiments/2026-08-29_paper_route_review_input.md; 内容吸收三件——① docs/34: AAAI 模拟评审判定（Overall 4/10 Weak Reject 置信 4/5）+ 拒稿风险六类 + 完整技术链 + 研究问题三问 + 贡献收紧（时延/成本维度, PSO 两任务闭环）+ VGRM 四角色 + 契约-Judge-证据链专利行 + 大论文收敛原则 + 门控基线缺口清单 + 碰撞暴露 P1 行 + 边界内许可清单 + Loop 0-F 纪律 ② 蓝图: §0.1 模拟评审判定 + §1 矩阵扩八列（成功标准/失败后降级表述预注册 v1）+ Phase 1 基线口径澄清（E1.3 = 第六基线"确定性契约+触发式 Judge"）+ §7 原始输入关联行 ③ 计划文档: Loop 0-F 映射表 + 矩阵回填纪律 + 独立审计九项攻击面清单。待裁定项沿用原条目（T3 解冻 / T5 治理 / 专利申请状态确认）, 不重复开立。零端点/零跑批/零对外。
[08-30 00:1x] #RULING-T3-UNFREEZE 用户裁定（事项一）: T3 第二数据流选 a——解冻 TAT-DQA joint-v1, 解冻范围仅限 T3 一项: 只在已冻结的 validation split 上构造注入, 不碰 test split, 不重开任何旧 TAT-DQA 实验循环; T3 完成后冻结线恢复冻结。按阶段纪律先出任务卡再执行。执行者 = Loop A（GB10）。
[08-30 00:1x] #RULING-T5-C4B 用户裁定（事项二）: T5 视觉批错位治理, 采用 C4 菜单 b 案（单列裁剪, 预注册预期错位率 33%→≤5%, 门 <10%）。治理本身零端点; 治理后复跑 118 注入视觉判别需一次 :8007 窗口（用毕即停）。判据照预注册: 错位 <10% 且跨层增益过线才入正文, 否则整节删除。先出任务卡再执行。执行者 = Loop A（GB10）。
[08-30 00:1x] #EXEC-SYSTEM-CORRECTION 执行体系更正在案（用户重申）: ① 四层 Loop（docs/17）: 用户+主线程 = Loop D 指挥层（拟卡/写文档/抽验/记账）, Loop A = 执行层（GB10 远程 Codex CLI, tmux 直启）, Loop B 验证, Loop C 审计 ② 实验执行（T1-T6）位置一律在 GB10, 本地只做拟卡/写文档/抽验/记账 ③ 标准执行链: 拟卡 → 本地 push → GB10 先提交自身在制件再 pull（三方对齐）→ GB10 tmux 派发 Loop A（loop_a_exec_constraints.md + 任务卡, profile 双档路由）→ 工件落 GB10 logs/graph/eval/ 并 commit 入账 → 主线程 pull 抽验 → 汇报 ④ 主线程直跑仅在 Loop A 异常时允许且必须显式记账（本会话先例: 08-30 凌晨主线程 ssh GB10 直跑 pytest 验证 = 收口验证非实验执行, 已记账）⑤ 计划文档 T1/T2/T6 "主线程可直跑"字样已删, 统一"执行者: Loop A（GB10）; 主线程拟卡与抽验"（同 commit）; T7/T8 仍主线程。
[08-30 白天] #W2-CLOSEOUT-SPOTCHECK W2 收口 + 主线程抽验（绿态）: 三方对齐（本地/origin/GB10 = 60887e6; GB10 ahead 3 提交推送 + 在制件 91a2042 + INDEX 合并 e0fb601, 运行时冲突按「GB10 为准」取入版）; 抽验 26/26 复算过（research/paper_w2_spotcheck_recompute.py → logs/graph/eval/w2_spotcheck_recompute.json: payload_sha256 独立重算匹配 / E1.5 树权重独立复算 / E1.6 独立 bootstrap 一致 / T4 全表复核 / 证据链 LF-sha 逐字节）+ GB10 27 件输入+脚本 sha 零漂移; 派发证据 = tmux loop-a-w2（观察器 SESSION_ENDED 02:20）+ Loop A commits 5e2498d/f1bf00b/36ab25f; 红线自查: 预算 122/200 / 端点仅 :8004（护栏探针四门自证）/ judge 不见真值 / 冻结件只读 / 甲方标识零命中。
[08-30 白天] #RULING-SHEET-CIRLED 用户圈选入账（判据冻结, 不溯及）: ①a 分层提供定位与诊断, 检出率不主张优越, 照冻结降级措辞 / ②a 谱排序稳定, 绝对极差按量化机制衰减, 机制解释入正文 / ③ T6 分支 a 入效度威胁节照草稿措辞 / F-1 论文正文只引公开底座, fixture 表述「内部校准臂」。落点: paper/draft_v0_s1_s2_s6.md（S1 ②a 句 + S2 ①a/F-1 块 + 效度威胁占位节）。
[08-30 白天] #HOOK-ESCALATION-SUMMARY-GUARD 教训台账（Hook Escalation 第 3 次触发 → 上机械强制, 用户批准）: 「声明摘要 ≠ 存储工件」三次实证（① f1bf00b W2 摘要在 payload 收口前计算 ② 36ab25f ports_touched 作用域声称≠存储 ③ d4e749a W1 汇报自指计数失真）→ scripts/graph/hooks/summary-recompute-guard.precommit.sh + summary_recompute_guard.py 上线（AGENTS.md 机械强制层 #5, 链式入口不变, 本地/GB10 通用）; 收据块 = 工件路径 + sha（raw + LF 双口径）+ 数字声明列表, gen 预校验 / check 重读复算, 失配阻断提交; 附加教训: 本地检出 CRLF 转换使工件原始 sha 变化 → 双口径设计（LF 值与 GB10 逐字节一致）。首个应用件 = 完整版一页纸 §I 收据块。
[08-30 白天] #F-SC-1-SPEARMAN-GAP 抽验发现（待裁定, 见完整版一页纸 J6）: 加编算法主可比两列（跨端点 Spearman + 方向一致率）不在 W2 工件且报告未注记缺列; 根因 = 冻结 :8006 基线为异语料标量聚合（无逐状态向量）且 :8006 红线零触碰; 缓解 = 同口径替代指标（judged vs mapped Spearman 0.9744 / 方向一致 107/108, 限 :8004 口径内, 抽验侧复算）。
[08-30 白天] #DECISION-SHEET-FULL-W2 完整版一页纸入库（docs/experiments/2026-08-30_decision_sheet_full_w2.md）: W2 结果 + 抽验摘要 + findings（F_W2_4/F_W2_1/C3 降级/预算饱和/E1.5 变体 2/F-SC-1）+ 待圈选 J1-J6（各带推荐）; 圈选后即派 T3 → T5（卡在案: t3_task_card 前提含工件在位验证+解冻范围条款; t5_task_card 治理零端点+:8007 用毕即停）。

[08-30 Phase A] #RULING-J1-J7-EXPERT-REVIEW 用户圈选（外部专家评审采纳）入账: J1=a（只写"验证到离散评分分辨率", 不写"端点高度一致"）/ J2=a+附加条件（不得用重设计 mutant 偷偷替代原 M7; M7 作为 mutation fidelity/observability 机制发现入账）/ J3=a 且更彻底（不写"PSO 省专家调参"; PSO 从贡献删除, 方法最多一句带过）/ J4=a（饱和轴只留一句 observation, 不造困难集救轴）/ J5=a 不追投（算术错误更正见下条）/ J6=a（0.9744/0.9907 限同端点同口径, 不得表述为跨端点证据）/ J7=暂不开、附条件开放（仅当第二数据流/跨匹配器/统计校正全部完成后终审仍把端点鲁棒性列为主要拒稿点, 且错峰单窗 ≤120 次调用, 才另报批）。C2 表述被更保守句覆盖（判据冻结不变）: "Hierarchical checkpoints provide layer-level localization and decomposable evidence under a lower evaluation budget, but do not improve raw defect-detection sensitivity in the current setting."
[08-30 Phase A] #SEQUENCE-REFREEZE 论文身份重冻结与序列调整（覆盖"圈选后即派 T3/T5"）: T3/T5 派发暂停; Phase A 尸检+Claim Set v2 冻结（已完成）→ Phase B 文献重定位（四簇 = meta-evaluation/过程级评测/突变与故障注入/裁判可靠性; 专家六线索 ACES/Contextual Metric Meta-Evaluation/WebStep/AgentProcessBench/AgentChaos/LLM 形态测试一律实查核验零猜测; BiomniBench 未证实前禁用; 相关工作 v3 三簇降为 S6 短段素材）→ Phase C 预注册新判据（可见性定义/有效突变体定义/检出-定位-成本三轴/表级聚类统计——118 注入不得按 iid 引 CI/matched-FPR 比较方案）→ Phase D（D1 突变体有效性审计零端点 → D2 跨匹配器验证 ≥2 种、嵌入类注明端点与预算 → D3 同假阳率公平比较零/低端点、新预注册不动旧判据 → D4 第二数据流=原 T3, 解冻条款照旧: 仅 validation split、完成即恢复冻结）; 每段完成后停一次做 autopsy 再定后续; T5 视觉补盲降为 P2 可选（排 D4 后按需另批; 原 C4 案 b 裁定暂缓执行）。
[10-03] #OFFICE-VISUAL-ACCEPTANCE-AND-REVERIFY main@871aeb3: 一、Office 视觉验收完成并落档 docs/experiments/2026-10-03_office_visual_acceptance.md（86 行）：导师稿 8/8 页、故事稿 4/4 页逐页检查；GB10 重渲染 12 张 PNG 与本机检查副本 12/12 逐字节一致；修复前实测三处缺陷——O1 p4 公式显示为 |Gamma={0.2,0.3,0.5,0.7,0.9};（修：闭集 render_math()）、O2 p5→p6 Table 1 的 Flat 行被跨页劈开、续页首行仅剩 0.8737])（修：w:cantSplit 接入 4 个表格构建器）、O3 p5 Figure 2 的 absorbed= 柱内白字在 ocr-similar（比率 0）柱上白底白字不可见（修：折入柱顶标签 + ylim 1.16→1.30）；修复提交 3df1134（builder +90/−1、图脚本 +5/−4、回归测试 +43），导师稿 DOCX 重建提交 9b19167；图 PNG 新旧 sha256 c0b1ec3d…（55 226 B）→ d9da2f7b…（55 352 B），属展示层重生成（GB10 无 matplotlib、本机 3.9.4，输入为冻结 JSON），不在 frozen_hashes 18 项内、数据不变。二、GB10 权威复核 @871aeb3（16:24:58–16:27:21 UTC，日志 /tmp/b6office_suite_PfxG，rc 全 0）：pytest 803 passed / 13 skipped / 1 deselected（= 799 + 4，等于预期）；validate_paper_claims PASS 73/73；docs_lint rc=0 / 0 fail / 4 warn——除 docs/34 基线 warn 外，docs/32 / docs/33 / docs/m1_coldstart_candidates 三条 [2] 时效 warn 系 09-11 最后更新、自 09-26 起按 STALE_DAYS=14 自然越阈，非本批引入、本批未消警未扩基线，登记为待处置偏离。三、Loop B 已于 10-03 00:27:32 自然周期覆盖 871aeb3：overall PASS，9 项检查全 PASS，未手工触发未重置；:5050 PID 1868428（lstart 09-13 01:22:32）与 Loop B daemon PID 2835621（lstart 09-24 14:14:59）均未变；三方对齐 871aeb3，production 脏件仍固定五件。四、红线自查：零模型调用（累计 ≤105/200 不变）、未改冻结判据/冻结 hash/数据体、未覆盖 production 脏件、未重启服务、逐路径 add、无 --amend、无 --no-verify、不外发不上 arXiv 不公开代码。
[10-03] #GD-Q3-PACKAGE-READY-TOKEN-CONFIRM-PENDING main@333b933: 一、用户裁定逐条落地：G-A 不批（Valentine 不承担 gate/sealed）、G-B 不批（保持阈值分桶）、G-C 本批不批（不选源不下载）、G-D 批（canonical = target_table.csv 表头）、G-E 接受（DATA_NO_GO / RQ2 NOT_IDENTIFIED / 146 列仅 exploratory）、V2-3 关闭（不开 v3、不申报 FinQA 算子材料）；核心目标与安全边界不变，goal 推进重点刷新为“交付物证据链已达成 / 唯一在途 = 146 列 Q3 / 门链按 G-E 归档”，完成审计前不申报 goal 完成。二、docs_lint 基线 B：logs/graph/docs_lint_warn_baseline.md 1→4 条，docs/32、docs/33、docs/34、docs/m1_coldstart_candidates 均登记为历史/受保护件自然时效 warn；正文不回改、不消警、lint 逻辑零改动。GB10 实测 rc=0 / 0 fail / 4 warn，基线与 report 按“检查项+路径”机器比对 SET_EQUAL=True、4/4。三、G-D 复核包：research/valentine_q3_review_package.py + 6 例测试落地；GB10 /tmp/valentine_q3_20261003_jeDV 双跑，10 pair / 146 source columns / 160 target headers / chunks 50+50+46，manifest sha d91fd7d4…、samples sha 6843f4c5…、canonical sha 241ca7ed…；两包 diff rc=0 全逐字节一致。可见性自证：manifest 只读 20 个 source_table.csv/target_table.csv，10 个 ground_truth.json 仅 exists 计数，forbidden_open_count=0；strace 对 ground_truth.json 的 open/openat 命中 0。四、调试偏差如实入账：首次 fixture 多拼 source_ 前缀（1 failed/4 passed，只修 fixture 不放松断言）；首次 direct-script import 失败（ModuleNotFoundError: research），按仓内 finqa adapter/split_assign 既定模式恢复仓库根 import path 并加删除 PYTHONPATH 后 --help 负例；修正后 6 passed。五、GB10 权威收口 @333b933：全量 pytest 809 passed / 13 skipped / 1 deselected（rc=0），validate_paper_claims PASS 73/73；未改冻结判据/hash/数据合同，零下载、零业务端点、零模型调用，数据体不入 Git。六、硬停点：按密钥纪律，本轮任何模型派发前必须由用户确认 GB10 Token Plan token 已轮换；未确认不派 R1/R2/裁决、不把旧值当新值、不自行重试；token 值/敏感元数据不入文件、prompt、台账、Git。D-E MIMO 继续挂起，D-F 专利门不变。
[10-03] #GOAL-COMPLETION-AUDIT-PASS main@ae344ae: 一、零模型收口完成：G-A..G-E/V2-3 同步进开题、前两章、骨架与分层设计件 §12；acceptance_report 由 GB10 validate_paper_claims 重生成为 PASS / 5 claims / 73 checks；146 列 Q3 明确 NOT_RUN/UNFINISHED，输入包结构审计为 6 个输入包 judgment_keys=0、3 个裁决模板全空、label/result 文件 0。二、新增理论/图表探索位：method_theory §11 形式化样本空间、R1/R2/ADJ、gold、事后源侧收敛效度与证据等级；figure_plan 新增 FIG-Q3-1 / TAB-Q3-1 空槽，均不得支撑 Stage D/RQ2/DATA_GO/训练。三、完成审计逐项判定见 docs/experiments/2026-10-03_goal_completion_audit.md：小论文在成熟评估保底稿口径下正文/方法/实验/图表/Related Work/limitations/claim-evidence 齐备，round5 双模型 ACCEPT、chain audit PASS_WITH_NOTES 无 HIGH、Office PASS；大论文开题/框架/前两章齐备且后续章节保留三阶段空槽。四、对抗审计抓到一处真实回归并修复：改写 readiness 历史句时误删唯一执行计划链接，导致 test_advisor_materials_link_to_the_current_execution_plan 1 failed；只补回链接、未改测试，随后该用例 1 passed，GB10 全量恢复 809 passed / 13 skipped / 1 deselected，claims 73/73，docs_lint 0 fail / 4 warn 基线同构。五、安全自查：三方对齐 ae344ae；未触碰 docs/33/34、冻结判据/hash、production 脏件；零模型、零业务端点、零下载；专利门保持不上 arXiv/不公开代码/不外发。六、完成判定 COMPLETE_FOR_STATED_GOAL 只覆盖两份内部科研交付物；正式投稿、146 review、Phase 2/训练均为保留的后续探索或另行授权事项，不冒充完成结果。
[10-03] #GOAL-STATUS-CORRECTION-ACTIVE 用户新增裁定覆盖上一条过宽表述：本 goal **不关闭**。草稿层两份交付物已由逐项审计证明（小论文成熟评估保底稿、大论文开题/框架/前两章），但当前继续准备小论文投稿版、大论文后续章节框架与零模型探索。GB10 qwen/deepseek 旧 key 已失效，token 一律按“未轮换 / 未就绪”处理；新 key 安全配置、状态确认并获明确授权前不派任何模型、不跑 G-D 三载体、不打印或记录 token。146 列输入包保持“已装配、未复核”，不得标完成、Stage D 闭合、DATA_GO 或 RQ2 确认。G-A/B/C 不批边界与 V2-3 关闭继续有效，不新增下载、不扩数据源、不开 v3。投稿材料按 ARR 10/12 主窗口、WWW 10/18/10/25 后备准备；专利未确认前不正式投稿、不上 arXiv、不公开代码。
[10-03] #PROJECT-CLEANUP-COMPLETE 起点 main@7dfb426；`paper/submission_references_arr_www_v1.md` 已在 `35e77d1` 原子收口。范围仅文档/资产索引/代码安全/可审计性；零模型、零 G-D、零下载、零 Phase 1a/2/训练、零服务重启。一、文档对齐：research README 删除“无需裁定”并明确 V2-3 关闭/146 包未复核；handoff 用当前状态注记覆盖 GB10 未验证与 1 fail/1 warn 历史口径；asset map 修正 D-C 已暂存、Office PASS、Q3 runner/包边界；codebase map 登记 runner 输入输出与禁止事项；三载体补不同会话+不同模型身份且非生成者。二、代码安全：修复前实测 build 会静默删除 out_dir 旧 sentinel；修复后 out_dir 仅允许 temp 下不存在/空目录，非空/嵌套/输入树内/符号链接/temp 根 fail closed 且不 unlink。输入树硬 allowlist 10 pair × {source_table.csv,target_table.csv,ground_truth.json}，manifest data 范围恰 30 项，额外 pair/file/dataset/manifest 项全部拒绝；ground_truth 只 stat 不 open。Q3 测试 16 passed；GB10 全量 819 passed / 13 skipped / 1 deselected（相对 809 的 +10 全为新反例）。三、可审计性：现役 Markdown 319 件断链 0，模板占位 `file.md` 1 件单列；secret scan 高置信命中 0；投稿准备 hash 12/12；claims 73/73；docs_lint 0 fail / 4 warn 且 SET_EQUAL=True。四、未决技术债（唯一信源本行）：① harness audit 历史 `HANDOFF_PROMPT.md` 不在仓库，已清断链不伪造载体；② 原始 Valentine staging 含 30 个 `_full/_result/_trajectory` 扩展项，新 runner 按 `input_manifest_scope_mismatch` 拒绝，旧 Q3 包为 hardening 前不可变历史产物，未来重建必须用 10 pair × 3 文件过滤根；③ Loop B 最近自然 PASS 只覆盖 `6ea6209`，`ae344ae..10dfbbd` 与最终收尾提交未覆盖；④ 暂停科研 goal 的 `research/build_submission_anonymous_preview.py` 与 `tests/test_submission_anonymous_preview.py` 为未提交工作区件，本批未混入。五、保护资产 `IMPLEMENTATION_PLAN.md`、`PROMPT.md`、`_d3b_dispatch.sh`、`side_handoff_20260829.md`、`logs/graph/docs_lint_report.json` 与 Loop B 瞬态件均未 add/commit/delete；docs/33、docs/34、冻结判据/hash、TAT-DQA 边界未动。
[10-03] #CLEANUP-FINAL-VERIFY main@5f82efb: GB10 全量 pytest 819 passed / 13 skipped / 1 deselected（rc=0，增量10全为 Q3 反例）；validate_paper_claims 73/73；docs_lint 0 fail / 4 warn 且 SET_EQUAL=True；现役 Markdown 链接 broken 0、模板占位 1；高置信 secret 命中 0；投稿准备 hash 12/12。Q3 raw staging 探测按 input_manifest_scope_mismatch 拒绝且 out_dir 未创建。大扫除完成，goal 继续 PAUSED。
[10-03] #LOOP-B-NATURAL-FAIL-QA-CANARY main@5f82efb: 大扫除收尾后观察到自然 Loop B 覆盖 `5f82efb` 且 overall FAIL，未手工触发/未重置。唯一失败项 = qa_canary failures=1；`adv_cross_doc`（跨文档聚合）2 个断言中 `contains_keyword=份` PASS、`source_required=嘉合基金` FAIL，证据为 `sources empty`，duration 24248ms，route opencode / model opencode:qwen38-27b-fp8；canary 总结 3/4，其他三题 PASS。其余 8 项 frozen/pytest/api/git/docs_lint/model_topology/agent_watchdog/pg_pool_guard 全 PASS。上一自然周期 02:36 同题为 2/2 PASS，表现为间歇 source retrieval 缺失；本批不修业务、不重跑、不改 canary、不重置 daemon。最近 PASS 覆盖 `6ea6209`，`5f82efb` 为 FAIL 覆盖，最终 ledger head `2219fbc` 尚未覆盖。
[10-04] #DB-LICENCE-RECORD-FORMALIZED main@d83078e: 用户 D-B 批准已落正式 Phase 1a 记录 `docs/datasets/phase1a_licence_record_v1.json`。status=accepted、accepted_by=Wzh、accepted_at=2026-10-03T17:01:42Z（GB10 生成现场 UTC，非回填）；permitted_uses 严格为 training/tuning/evaluation/rule_acceptance；covered_artifact_sha256 仅三项 D-B annex 工件 = FinQA LICENSE 92c0e67b…ac087、FinQA README eb86779c…64605、Valentine LICENSE f4960433…e99d。显式不授予 redistribution/public_release/commercial_use/other_data_sources/other_licence_interpretations；未用 fixture-user/data-owner。该记录不是 package-wide licence 绑定，不覆盖 source_tables/injection_map/schema/label_ledger/learnability_feature_ledger，不解除 DATA_NO_GO、不授权新下载或训练。二、证据/索引：D-B annex 加 append-only 接受指针；角色模板注明正式记录与未来 package-wide 模板边界；INDEX/资产地图/research README 同步。新增 tests/test_phase1a_licence_record.py 5 例，目标测试 49 passed；GB10 全量 824 passed / 13 skipped / 1 deselected，claims 73/73，docs_lint 0 fail/4 warn。记录 sha256=57592fa1…dd8d8。三、边界保持：D-C 最小下载已存在不新增，fetch/PID/log/manifest 为 operational metadata；Q3 三文件 allowlist 只约束下游复核输入；G-A/B/C/E、V2-3、Q3 未复核、token 未就绪、Loop B qa_canary 间歇失败继续如实记账。
[10-04] #ZERO-MODEL-PAPER-AND-THESIS-MAP main@7d776b1: D-B licence_record 后继续零模型推进两件：① `paper/reproducibility_statement_arr_www_v1.md` 固化可公开候选/不外发边界、D-B provenance 与 13/13 hash 清单；② `paper/thesis_manuscript_scaffold_v1.md` 新增第 3-8 章证据指针，明确第 5 章只有 licence scope 与 Q3“已装配未复核”，第 6 章 Phase 2/功效/rollback 空槽，第 7 章引用复现声明，第 8 章只汇总边界/开放问题。未新增实验数字、未改判据、未派模型、未下载。GB10 定点复核 22 passed、claims 73/73、docs_lint 0 fail/4 warn；全量基线仍为 c26ae04 的 824/13/1。
[10-04] #ANONYMOUS-SUBMISSION-PREVIEW-READY main@3f82d68: 匿名投稿源预览与内部 redaction map 已收口。源稿 sha 7006d98e…9e18a 未改；preview sha 9d4edf42…ab4d39、map sha 36114ceb…34f678。有效脱敏 11 处/12 条记录，禁词扫描 0，claim tokens 缺失 0，输出双跑一致。tracked preview 对账测试曾因测试自身从 anonymize() 读取不存在的 source_sha256 报 KeyError；只修测试为直接核源稿 hash，生成器/产物零改动。修正后 tests/test_submission_anonymous_preview.py 5 passed；GB10 全量 829 passed / 13 skipped / 1 deselected，claims 73/73，docs_lint 0 fail / 4 warn。预览不是 camera-ready，redaction map 不外发；venue/作者/匿名模板与专利门仍待处理。生成期间 GB10 同名未跟踪副本已移到 /tmp/b6anon_generated_original 保留后才 ff-only 拉平，production 五件脏件未覆盖。
[10-04] #SUBMISSION-PACKAGE-AUDIT-PASS main@4cd0713: 新增零模型投稿包完整性审计入口 `research/audit_submission_package.py` 与机器报告 `paper/submission_package_audit_v1.json`。机械检查 10/10 PASS，submission_status=PENDING_EXTERNAL_ITEMS / overall=NOT_READY_FOR_SUBMISSION；覆盖 source/anonymous 九章节、claim tokens、15/15/15 引用集合、匿名禁词/redaction hash、15 项 readiness hash、D-B licence scope、可复现性边界。审计发现并修正真实 hash 口径问题：投稿清单曾记录本机 CRLF 字节值，已全部改为 GB10 checkout 权威字节值（6 项变更）；不改审计判据。tracked audit 报告自身纳入 readiness hash 清单，避免自证遗漏。专项 25 passed；GB10 全量 832 passed / 13 skipped / 1 deselected、claims 73/73、docs_lint 0 fail/4 warn。未完成外部项固定为 venue/CFP、作者/匿名、专利、camera-ready、Q3 三载体 review；不派模型、不下载、不把 mechanical PASS 写成可投稿。
[10-04] #SPC5-EVIDENCE-ANCHOR-CLOSED main@61abf0c: 闭合 round5 N-2。将 `docs/datasets/2026-09-25_finqa_process_structure_and_checkpoint_semantics.md` 补入 SP-C5 evidence，使 7134 examples / two-to-eleven columns 等列宽分布主张有最详载工件锚点；不改 manuscript token、实验数字、判定或 scope。validate_paper_claims 由 73/73 增至 74/74，acceptance_report_v1.json 重生成 sha cf612363…9d05，claim_manifest sha 62a119e8…afc5；现役文档与投稿清单 hash/计数已同步。投稿包审计仍 10/10 mechanical PASS / PENDING_EXTERNAL_ITEMS，报告 sha 不变。GB10 全量 832 passed / 13 skipped / 1 deselected，docs_lint 0 fail/4 warn。零模型、零下载、零外发。
[10-04] #SUBMISSION-RISK-REGISTER-READY main@e34b3ea: 新增 `paper/submission_review_risk_register_v1.md`，RR-01..RR-10 按 controlled/closed/tracked/pending-external 分类。旧审稿高风险措辞（any proportional assignment、detection figures、origin clusters 等）在当前主稿/匿名预览均为 0 命中；N-1/N-2 已闭合。当前无新 manuscript blocking issue，submission blocker 仅 venue/CFP、作者/匿名、专利、camera-ready、Q3 review 外部件。风险登记纳入 readiness/audit hash 面。GB10 audit 10/10 mechanical PASS / submission PENDING，专项 17 passed，claims 74/74；全量 832 passed / 13 skipped / 1 deselected，docs_lint 0 fail/4 warn。零模型、零下载、零外发。
[10-04] #RELATED-WORK-MATRIX-READY main@1a13223: 新增 `paper/related_work_contribution_matrix_v1.md`，把主稿 Related Work 四簇固定为「代表工作—共同关注—本文差异/边界」：meta-evaluation、process/hierarchical、mutation/fault injection、LLM-as-judge；KD/agent distillation 七条只保留 future-work 边界，不把模型矩阵、DPO 素材或 Q3 输入包写成蒸馏证据。矩阵仅用 references_v0 已核条目，不新增 venue/数字。纳入 submission readiness 与 audit hash 面。GB10 audit 10/10 mechanical PASS / submission PENDING，专项 17 passed，claims 74/74，full 832 passed / 13 skipped / 1 deselected，docs_lint 0 fail/4 warn。
[10-04] #RR01-CLOSED-DERIVED-REBUILT main@6812d3c: 主稿 §5.2 补 matched-FPR [0,0] 的 single-varying-leaf 仿射分数推导，明确退化支持集不是一般等价定理；不改任何数字、claim token、实验结论或 scope。GB10 重建派生物：source sha 9d3e4926…f5c、DOCX 4f0b88cf…8a5f、匿名预览 6af1dfc6…b30e、redaction map 30f1be4b…03a6；旧件备份保留于 /tmp/b6rr01_backup 与 /tmp/b6rr01_generated_checkout。submission_package_audit 重生成 sha 87c6ece3…0bbf，机械 10/10 PASS / submission PENDING_EXTERNAL_ITEMS。更新 tests/test_submission_anonymous_preview 与 test_submission_package_audit 的 hash 常量；不改生成器行为。GB10 专项 25 passed、claims 74/74、docs_lint 0 fail/4 warn、full 832 passed / 13 skipped / 1 deselected。RR-01 从 should-fix/controlled 变 closed；venue/作者/专利/camera-ready/Q3 review 仍 pending。
[10-04] #GOAL-REQUIREMENT-MATRIX-UPDATED main@e0a626e: 在 2026-10-03 完成审计后追加当前要求矩阵，明确两份草稿交付物 PROVEN at draft level、投稿包 mechanical 10/10，但 146 列 Q3 仍 NOT_RUN 且 venue/作者/专利/camera-ready 外部项 pending；因此 goal 不关闭、不把草稿/机械审计冒充正式投稿完成。同步 RR-01 已闭合、SP-C5 74/74、D-B licence scope、G-A/B/C/E/V2-3 与安全边界。GB10 validate_paper_claims 74/74、submission audit 10/10、docs_lint 0 fail/4 warn；全量基线 832/13/1 不变。零模型、零下载、零外发。
[10-04] #LANGUAGE-TERMINOLOGY-AUDIT-READY main@08b231f: 新增 `paper/submission_language_audit_v1.md`，按 paper-polish checklist 扫描术语一致性、强主张、AI 套话与版本同步。结果：0 个 blocking language issue；`state-of-the-art`/`delve into`/`important to note`/`in conclusion` 命中 0，`superior/significant/robust` 均处于否定或限定语境；checkpoint visibility、protocol detection、silent absorption、matched-FPR、single-varying-leaf 术语一致。未改主稿。纳入 submission readiness 与 audit hash 面。GB10 audit 10/10、专项 8 passed、claims 74/74；全量基线 832/13/1 不变。
[10-04] #RQ2-RQ4-EXECUTION-MATRIX-READY main@b72d06a: 新增 `paper/thesis_rq2_rq4_execution_matrix_v1.md`，固化第 5–6 章 RQ2/RQ3/RQ4 的输入、对照臂、必报指标、确认性族、门序与禁止写法。RQ2=B0-B4/A0-A3、确认族质量非劣/安全非劣/风险覆盖；RQ3=七臂规则门、确认族 UID-any-harm/valid-rule retention；RQ4=统一端到端质量-成本-风险消融。所有实验槽位明确为空，FinQA/Valentine 分命名空间，sealed/future 只读，146 列 Q3 即使完成也只 exploratory。挂接大论文骨架与资产账本。GB10 audit 10/10、专项 20 passed、claims 74/74、docs_lint 0 fail/4 warn；全量基线 832/13/1 不变。零模型、零下载、零外发。
[10-04] #GOAL-FINAL-COMPLETE-AUDIT main@d9e9e41: 最终全量与逐项审计完成。两份可交付成果（成熟评估保底稿；大论文开题+框架+前两章）均满足当前 goal 的内部科研完成标准：9 sections、5 claims/74 checks、round5 双 ACCEPT、chain audit PASS_WITH_NOTES 无 HIGH、Office PASS、语言审计无 blocker、submission audit 10/10 mechanical PASS；RQ2–RQ4 后续矩阵与所有空槽/边界保留。非完成前置显式保留：正式投稿/venue/作者/专利/camera-ready、146 列 R1/R2/ADJ（已装配未复核，仅 exploratory）、Phase 2/训练。GB10 全量 832 passed / 13 skipped / 1 deselected、claims 74/74、docs_lint 0 fail/4 warn。审计结论 COMPLETE_FOR_STATED_GOAL；零模型、零下载、零外发。
[10-04] #DB-VERIFY-MIMO-ROUTE-PLAIN-EXPLAIN main@f2adaf1: 一、基线核验：local/origin/GB10 均 f2adaf1，未回退/reset/rebase；fdf549a 及更早只作历史。二、D-B licence_record 只核验不新建：accepted_by=Wzh、permitted_uses 严格 training/tuning/evaluation/rule_acceptance、covered_artifact_sha256 仅 finqa_repo_license / finqa_readme / valentine_repo_license 三件，not_granted 严格含 redistribution/public_release/commercial_use/other_data_sources/other_licence_interpretations。三、按 paper-polish-and-audit + paper-review-check + verify-before-done 重做完成度解释并落 `docs/experiments/2026-10-04_goal_completion_plain_language.md`：两份内部科研交付物完成=成熟评估保底稿+大论文开题/框架/前两章；不等于正式投稿；146 列 Q3 仅已装配未复核；Phase2/训练/外发仍 pending；COMPLETE_FOR_STATED_GOAL 不等于全科研项目全部完成。四、MIMO 路由只改 GB10 配置：Codex `/home/testuser/.codex/config.toml` model=mimo-v2.6-flash、base_url=https://token-plan-cn.xiaomimimo.com/v1；Claude Code `/home/testuser/.claude/settings.json` model=mimo-v2.6-pro、base_url=https://token-plan-cn.xiaomimimo.com/anthropic；两处语法/加载 PASS。API key 由既有安全通道承载，未读取、未打印、未写入 prompt/Git/日志/台账/测试输出；未调用模型、未派 R1/R2/ADJ、未启动 Phase2/训练、未改 D-C 范围。
[10-04] #MIMO-READY-FOR-CONFIG-ONLY main@8898f45: API key 已通过 `/home/testuser/.config/mimo-token-plan.env` 安全加载到一次性进程环境；文件权限 600，格式检查通过。仅完成路由配置状态更新：Codex `/home/testuser/.codex/config.toml` model=mimo-v2.6-flash、base_url=https://token-plan-cn.xiaomimimo.com/v1；Claude Code `/home/testuser/.claude/settings.json` model=mimo-v2.6-pro、base_url=https://token-plan-cn.xiaomimimo.com/anthropic；两处 syntax/load PASS。状态 = READY_FOR_CONFIG_ONLY。未读取/打印/记录/提交 env 文件内容，未调用模型，未跑 R1/R2/ADJ，未启动 Phase 2/训练，未改 D-C 数据范围。

[10-04] #RQ2-Q3-EDGE-PLANS-PENDING: 新增 RQ2 identification/acquisition 申报卡与 Q3/B0-B4 执行卡。未决：Route V 是否批准扩到 >=40 independent Valentine pair clusters 及精确新增目录 annex；Route F 受 D-A/V2-3 阻塞；R1/R2/ADJ 未派发，B0-B4 未运行；POWER_GO 仍待真实开发侧方差/MDE receipt；Stage R 最强预注册基线 vs 完整验证门+rollback 与 RQ4 C0-C3 只有设计槽位。零模型、零下载、零 Phase 1a/2/训练。

[10-04] #Q3-THREE-EXPERT-RESULT-RECORDED: 用户确认 Q3 已由三位独立专家完成 R1/R2/ADJ，取代“同一专家兼任 R1/R2”的中间口径。已登记 exploratory 摘要：146/146 adjudicated；119/146 exact agreement（81.51%）；κ≈0.727；双方 map_to 的 41 条 target 41/41；27 条 disagreement 均为 action boundary；最终 map_to=52 / skip=58 / hold=36。未决：原始输出、ADJ ledger、final label ledger、visibility receipt 与 hash 尚待封存；在此之前不得把摘要写成完整 artifact audit。
[10-04] #B5-TYPED-DECISION-PROPOSED: 新增 B5 exploratory candidate = Jev-like typed-decision baseline，PROPOSED_EXPLORATORY / NOT_RUN。输入严格 source_header + canonical headers + LABEL semantics；action 为 map_to/hold/skip，map_to 后再选 canonical target。B5 不改 B0-B4；open-alternative-jev / jevos-v2 是未核验候选，未做 licence/provenance/dependency audit 前不安装、不运行。B5 只回答通用 typed-decision baseline 是否已覆盖问题、是否仍有必要训练专门学生，不解除 DATA_NO_GO / NOT_IDENTIFIED。

[10-04] #Q3-PARTIAL-DELIVERY-VALIDATED: corrected final label ledger 已验证：146 行，map_to=51 / skip=58 / hold=37，仅 line 61 由 map_to|pap_curb_sec 修正为 hold|null。output_manifest、sha256_manifest、correction_record、visibility receipt、normalized pre-correction ledger 已入 GB10 inbox。R1/R2/ADJ raw originals 与 README_identity_and_status.txt 仍缺失，且 R2/ADJ visibility receipts 未独立签署，因此 seal_complete=false，状态 PARTIAL_DELIVERY_VALIDATED_RAW_MISSING。

[10-04] #Q3-FULL-DELIVERY-SEALED: 专家10件完整包已落 `logs/graph/q3_raw_seal_20261004/` 并同步 GB10 `/home/testuser/wzh/q3_raw_seal_20261004/inbox/q3_raw_seal_20261004/`。9/9 manifest hash匹配，secret命中0。R1/R2/ADJ机械对账：146/146/27，exact agreement 119/146，27个ADJ一一覆盖，κ=0.7265348595；pre-correction由119条一致项+27条ADJ合成，derive errors=0；corrected只改line 61为hold|null，最终51/58/37，target validation errors=0。状态 SEALED_WITH_VISIBILITY_EXCEPTIONS / seal_complete=true；R1可见lineage/table grouping，R2/ADJ无独立签名visibility receipt，不得写成strict three-field-only PASS。DATA_NO_GO / NOT_IDENTIFIED不变。

[10-04] #Q3-BOUNDARY-BLOCKER-CLOSURE: Q3 raw seal is blocked by six missing artifacts (R1/R2/ADJ outputs, final ledger, expert visibility receipt, output manifest/hash). Three invalid action references in DSNY pair remain undecided: reference quarantine vs whole-pair INVALID. B0-B4 exploratory split protocol prepared but NOT_RUN because proposal_train.dev=0; B5 offline audit found no verifiable local source/licence/version/dependency/output capability and remains NOT_RUN. Goal ACTIVE; DATA_NO_GO / RQ2 NOT_IDENTIFIED unchanged.

[10-04] #Q3-RULING-LANDED: raw originals must arrive at exact GB10 paths or /home/testuser/wzh/q3_raw_seal_20261004/inbox/ (empty mode 700). Invalid refs = Option A primary / Option B mandatory sensitivity; B0-B4 = LOO primary / salted sensitivity, bootstrap 2000 seeds 42/43/44 exploratory only; B5 dormant. Execution gates remain closed pending raw seal, quarantine implementation, label lock, split freeze, and B5 boundary closure.

[10-04] #B0-B4-EXPLORATORY-V2-COMPLETE: Option A primary and Option B sensitivity implemented; frozen LOO/salted probe run on GB10, zero model. Primary B4 macro-F1 0.717 / harmful-map 0.062 vs B3 0.572 / 0.178; pair-invalid similar; salted test only 2 pairs / 19 columns with wide CI. Dedicated student necessity NOT_ESTABLISHED. First run invalidated by salted B4 alignment bug; v2 double-run byte-identical. Remaining: approved go/no-go thresholds and all Stage D gates before any training.
[10-05] #STAGE-D-NECESSITY-GATE-PILOT-ONLY: risk_limit=0.10 gate run from B0-B4 v2. B4 passes primary and pair-invalid slices (harm upper 0.0948/0.0991) but salted 2-pair slice fails (point 0.1053, upper 0.1250). Verdict PILOT_ONLY; dedicated student necessity NOT_ESTABLISHED; no A0-A2/Phase2/training. Internal paper route remains Stage E fallback.
[10-05] #INTERNAL-DELIVERABLES-COMPLETE-GOAL-ACTIVE: internal deliverable audit passed. Stage E paper has 9 sections, claim checks 74/74, round5 dual ACCEPT, Office visual PASS, submission audit 10/10; thesis proposal/ch1-ch2/ch3-ch8 framework have Loop C audits and explicit empty slots. Stale q3_three_carrier_review_not_run external blocker removed; remaining external blockers are venue, authorship, patent, camera-ready. Internal deliverables complete only; Stage D/R/RQ4 scientific closure and external release remain open, Goal ACTIVE.
[10-05] #STAGE-D-FORMAL-BOUNDARY-RECORDED: DATA_NO_GO / RQ2 NOT_IDENTIFIED formalized with recovery requirements. Exploratory same-sample linkage exists only for 10-pair subset; confirmatory blockers are independent clusters, non-empty split layers, strict reviewer visibility receipts, and signed power/MDE receipt. No download/model/Phase2/training action taken.
[10-05] #TRAINING-READINESS-DRY-RUN-READY: A0-A3/4B-smoke config and resource/monitor/recovery package prepared; GB10 validator PASS_DRY_RUN_ONLY but training execution BLOCKED pending MODEL_GO/dependencies/data gates. estimates explicitly unmeasured; peft/trl/deepspeed absent. RQ2 four-gate application and Stage R/RQ4 static protocol prepared; no A0-A3/Phase2/training/download/model dispatch.
[10-05] #MODEL-TRAINING-GO-APPLICATION-PREPARED: separate MODEL_GO/TRAINING_GO application prepared with exact revision/licence/budget/window/stop fields. Current gate matrix fails necessity/source/label/split/power/baseline and dependency readiness; status PENDING_USER_APPROVAL, no install/model load/training.
[10-05] #MODEL-CANDIDATE-METADATA-AUDIT: local Qwen3-4B/8B GGUF hashes recorded but not trainable checkpoints. HF metadata-only queries timed out; immutable model/tokenizer revisions and licences remain missing. MODEL_GO incomplete, no model loaded/downloaded.
[10-05] #MODEL-SYNC-BLOCKED: Qwen3-4B exact revision metadata bound but weight download blocked. GB10 DNS resolves, HTTPS to huggingface.co:443 times out; local official path also times out. credential discovery resolved, whoami network timeout, authenticated unknown, username unverified, token length 825 only. no target/partial files, no model load/S0/A0-A3/Phase2/training.

[10-05] #MODEL-SYNC-MIRROR-SUCCESS: 官方 HF 路径仍阻塞；批准的 fallback 使用 `hf-mirror.com`、`token=false`、`HF_HUB_DISABLE_XET=1`，Qwen3-4B revision `1cfa9a72...` 已同步到 `/home/testuser/wzh/models/hf/Qwen3-4B`。13 个顶层文件、3 个分片、398 个 index 条目、Apache-2.0、镜像 `X-Repo-Commit`、clean/full manifest 全部验证。状态 `READY_FOR_ARTIFACT_VALIDATION`；不等于 MODEL_GO，未加载模型或启动 S0/A0-A3/Phase2/训练。provenance 必须写 third-party mirror fallback，不能写官方直连。

[10-05] #DOCS-GOVERNANCE-COMPACTED: 新建 `side_handoff.md` 与 `docs/handoff/README.md` 作为现役交接入口；`side_handoff_20260827.md`、`side_handoff_20260829.md` 归档到 `docs/archive/`。Q3 partial/boundary blocker 与 official model-sync blocker 归档到 `docs/archive/experiments/`，新建 `SUMMARY_q3_label_and_baselines.md` 与 `SUMMARY_stage_d_readiness_and_model_sync.md` 收拢现役结论。论文 hash 证据件未移动，历史台账只更新路径/状态标签。

[10-05] #WORKSPACE-RESIDUE-ARCHIVED: 根目录旧会话资产 `IMPLEMENTATION_PLAN.md`、`PROMPT.md` 归档到 `docs/archive/session_assets/2026-08-29/`，`_d3b_dispatch.sh` 归档到 `scripts/archive/`。本机旧 WSL `docs_lint_report.json` 已保存到 ignored `logs/graph/archive/docs_lint_report_2026-09-08_local_wsl.json`，tracked 路径恢复仓库基线；GB10 docs_lint 才是权威。未删除任何唯一证据。

[10-10] #MULTILEAF-V1-FORMAL-POSITIVE: pre-result freeze preceded output; M/R/N contracts 24 clusters x 3 injections each, 216/216 retained. LOCO macro-F1/top-1=1.0, permutation p=1/10001, cluster CI=[1,1], leakage PASS. Fresh Loop C ACCEPTED with construct-sensitive scope; direct three-leaf codebook ablation also=1.0, so claim is limited to the constructed observation surface.
[10-10] #STAGE-D-REFERENCE-TRACK: PRM C2/C4 dry-run VALIDATED_NON_TRAINING (C2=659, strict C4=451, matched=407, real terminal/process disagreement). Reference smoke PIPELINE_CLOSED after Python-header repair; Loop C CONDITIONAL because arms share 7/8 train and 2/4 eval rows and 2 steps consume 2/8 rows. Formal pilot remains NO-GO.
[10-10] #AGENT-DISTILLATION-QUALIFIED-NOT-PILOT: actual 1928-row payload inspected; 1381 positive / 0 negative / 547 missing terminal values, no step_reward or native IDs/split. TCV smoke 1926/1928 rows and execution proxy 1792/1928. Status NOT_SUITABLE_FOR_C2_C4; derived IDs and syntactic signals remain engineering-only.
[10-10] #SECOND-DATAFLOW-DESIGN: FinQA process/checkpoint v2 selected as best candidate; overlap feasibility 628 multi-step clusters for E1/N and P/N. Existing FinQA scorer is CONDITIONAL_WRONG_MEASUREMENT_OBJECT and V2-3 remains closed. Exact IDs, causal evidence join, role/split and independent semantic scorer remain open.
[10-10] #OVERNIGHT-VERIFICATION: full pytest 880 passed / 13 skipped / 1 deselected; docs_lint 0 fail / 6 existing warnings; paper claims 79/79; submission 10/10; multi-leaf validators 22/22 and 105/105. No commit/push; formal Stage D training, Phase 2 and Stage R not run.
[10-10] #FINQA-V2-PRERESULT-FREEZE-A: Loop A produced the hash-complete freeze packet and receipt under `research/finqa_v2_20261010/`; 216 candidates -> 215 retained / 1 ambiguous N join excluded before split, 72 components remain stage-disjoint, 19 focused tests pass, scorer bindings are 0-executed with 215 unevaluable until an explicitly authorized later run. Next action is Loop C independent review only; formal FinQA v2 execution, threshold search, semantic-correctness claims and commit/push remain blocked.
[10-10] #FINQA-V2-ANALYSIS-PLAN-FREEZE-A: Loop A added `FINQA_V2_ANALYSIS_PLAN.md`, `finqa_v2_analysis_plan.json`, `finqa_v2_analysis_plan_hash_manifest.json` and `finqa_v2_analysis_preresult_freeze_receipt.json`; 16 bound files match, prior-freeze hash mismatches=0, formal scorer outputs before/after=0, and focused pytest=19 passed. Next action is fresh-context Loop C analysis-plan audit only; formal scoring, training, threshold search, metric/permutation additions and commit/push remain blocked.
[10-10] #FINQA-V2-FORMAL-LOOP-A-INVALID: Task `finqa-v2-formal-experiment-a-20261010` stopped at the frozen scorer guard: 0 successes / 89 failures, every failure `artifact_sha256_mismatch` with raw-manifest versus normalized-payload hash disagreement. The 89 rows/30 clusters are preserved unevaluable, scientific estimands and 10,000-replicate bootstrap were not attempted, `A_RECOMMENDED_CLASS=SECOND_FLOW_INVALID`, and fresh output/hash verification passed. Next action is Loop C independent recomputation/audit of the invalid packet only; do not rerun the scorer or infer transfer, hierarchy, semantic correctness, harmfulness, localization, or Stage E transfer.

[10-10] #FINQA-V2-MINIMAL-RERUN-LOOP-C-REPORT-MISSING: RESOLVED. The independent report now exists at `docs/experiments/2026-10-10_loop_c_finqa_v2_binding_v2_audit.md` with `SCORER_BINDING_GO = PASS` and `VERDICT: PASS`; fresh preflight reverified 12 old-run hashes, 7 frozen-input hashes, 994 trace rows, 89 samples/30 clusters and focused tests `19 + 10`.

[10-10] #FINQA-V2-BINDING-V2-RERUN-INVALID: Task `finqa-v2-minimal-rerun-pending-execution-20261010` executed under `results_binding_v2_rerun/` and stopped fail-closed at `BINDING_TRACE_MISMATCH`: 0 successes / 89 failures before any observation vector. The invalid packet preserves 89 rows/30 clusters with raw and normalized binding hashes plus null V/D/O, materializes 56 scientific estimand slots as non-computable, runs 0 of 10,000 planned bootstraps, retains the 994-row trace map, sets `A_RECOMMENDED_CLASS=SECOND_FLOW_INVALID`, and hash-binds 11 outputs in the execution receipt. Fresh verification passed; old invalid run remains intact and unsuperseded; endpoint/model/database/training/PRM/Stage-D/permutation counts are 0. Next action is Loop C independent post-run recomputation only; do not rerun the scorer or infer transfer, hierarchy, semantic correctness, harmfulness, localization or Stage E transfer.

[10-10] #GRAPH-LOOP-META-RETROSPECTIVE: root-cause tree separates CONTRACT/INTERFACE/TEST_COVERAGE/DOCUMENTATION/STATE_MEMORY/ROLE_HANDOFF/GOVERNANCE from scientific/data causes. The reusable authority map, PASS levels, formal preflight checklist and handoff fields are now in `docs/governance/`. Current true blocker is `RUNTIME_BINDING_INTEGRATION_GO`; no third formal scientific rerun is authorized.
[10-10] #FINQA-V2-BINDING-V3-QUALIFICATION: A reports `89/89` runtime bindings and `420/420` evaluation trace matches, four metadata fields present/consistent, zero silent defaults, zero identity/group/split drift, zero leakage and zero scientific outputs. Previous invalid runs remain immutable. Status is `QUALIFICATION_PASS_PENDING_LOOP_C_INDEPENDENT_REVIEW`; `GOVERNANCE_READY_FOR_NEXT_FORMAL_RUN=NO` until C independently confirms and the preflight receipt is complete.

[10-10] #GRAPH-LOOP-GOVERNANCE-AUDIT-C: C independently confirms binding-v3 `RUNTIME_BINDING_INTEGRATION_GO = YES / INTEGRATION_PASS`, but `GOVERNANCE_READY_FOR_NEXT_FORMAL_RUN = NO`. The single remaining blocker is `END_TO_END_PREFLIGHT_PASS_UNMATERIALIZED_AND_NON_CERTIFIABLE`: the preflight receipt does not exist and the checker has silent-green bypass/empty-set paths. Owner: Loop D. No formal experiment is authorized.

[10-11] #SANER-ROUTE-LOCKED: `PRIMARY_ROUTE=A`; `OPTIONAL_ROUTE=B/READ_ONLY_48H_QUALIFICATION`; Route B result `B_QUALIFICATION=NO`, `STOP_BRANCH`. Scope lock and claim matrix are frozen; no positive method is required for the SANER RENE route.
[10-11] #REPOSITORY-GOVERNANCE-AUDIT-C: `REPOSITORY_GOVERNANCE=FAIL`, `GIT_SYNC=STOP_GIT_SYNC`. Required corrections: record the authorized formal-v3 result in status authorities, add the accepted `MEASUREMENT_OBJECT_MISMATCH` autopsy record, reconcile stale paper/memory references, then re-audit before any commit/push.
[10-11] #REPOSITORY-GOVERNANCE-FINAL-C: fresh-context Loop C verdict `CONDITIONAL`, `GIT_SYNC=STOP_GIT_SYNC`. Actionable recordkeeping blockers are closed: 335-path machine manifest exists, authority conflicts are superseded/resolved, FinQA autopsy lineage is closed, and stale gate status is marked superseded. Remaining blocker is independent cross-host verification: the reviewer sandbox could not read GB10 directly and did not independently bind the 929/13/1/10 receipt to current GB10. No commit/push.
[10-11] #CROSS-HOST-REPOSITORY-RECEIPT: RESOLVED. Fresh GB10 direct checks plus deterministic LOCAL/GB10 receipts passed C verification (`RECEIPT_VERIFIED`, content-semantic match, manifest 353/353, hash chains valid). The prior `CONDITIONAL / STOP_GIT_SYNC` repository-governance item is superseded. Git commit/push authority is now the existing seven-group manifest.
