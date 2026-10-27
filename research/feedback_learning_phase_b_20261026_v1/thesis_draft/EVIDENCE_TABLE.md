# C1—C3 Evidence Table

日期：2026-10-26
规则：`已验证 / 开发观察 / 未验证` 是证据身份标签，不是贡献等级。

| 点 | 证据标签 | 当前事实 | 分母与单位 | 可支持结论 | 不能支持 | 主证据路径 | 2027-10 前下一缺失证据 |
|---|---|---|---|---|---|---|---|
| C1 | 已验证 | 96/118 visible；OCR-like 0/13，跨 11 source-table clusters，五个阈值均不可见 | injection 为观察单位；family/cluster 必须分开报告 | visibility 随 family 改变；aggregate 会掩盖边界 | 自然失败率、harmfulness、false-negative rate | `paper/saner_rene_manuscript_v1.md` | 自然缺陷分母和独立 harmfulness labels |
| C1 | 已验证 | flat/hierarchical 在 single-responsive-leaf 下同秩；斜率约 0.375 | 当前冻结 score construction | 原始 protocol gap 不能当 ranking-quality gap | 层级与 flat 一般等价 | `paper/saner_rene_manuscript_v1.md` | 多 responsive leaves、不同权重/构造下的前瞻检验 |
| C1 | 已验证 | 2,382 clean records 的 support 均为 `{0}` | usable `(table_uid,column)` rows | 当前 clean-only procedure 不能选唯一 operating point | matched-FPR 普遍不可用 | `paper/saner_rene_manuscript_v1.md` | 非退化 clean support 与冻结 operating-point 协议 |
| C1 | 已验证 | 216 injections / 72 clusters 的 stage separation=1.000；direct-only codebook 也为 1.000，non-direct=0.3333 | cluster 为预测/重采样单位 | 结果来自显式 stage-aligned instrumentation | hierarchy 自动定位或自然泛化 | `paper/saner_rene_manuscript_v1.md` | 未 instrumented、因果对齐的第二数据流 |
| C1 | 已验证 | FinQA V=89/89、D=0/89、O=0/89 | 89 rows / 30 clusters | measurement-object mismatch boundary | 协议盲、检测能力或迁移规律 | `paper/saner_rene_manuscript_v1.md` | 重算下游结果字段的对齐 FinQA 执行 |
| C1 | 已验证 | FinRank absolute random accuracy 变化 1.084/1.029 点，但 hardness gap 只变约 0.359/0.343 点且方向稳定 | 1,185 records；TF-IDF/BM25 pairs | score sensitivity 与 decision stability 分离 | neural/generative 或其他 benchmark | `research/research_direction_sprint_20261020_v1/execution_v1/PAPER_E_EXTERNAL_AUDIT.md` | neural baselines 与第二个真实 ranking implementation |
| C1 | 开发观察 | post-hoc `text_sha1` 复现 442 occurrences / 305 records；33 gold loss、2 all-gold loss | canonical text identity；v2 post-hoc | author-disclosed identity 可确定性重现 | 完全冻结确认或 benchmark failure | `research/research_direction_sprint_20261020_v1/execution_v1/PAPER_E_EXTERNAL_AUDIT.md` | 冻结 canonical identity 的前瞻独立应用 |
| C1 | 已验证的负边界 | in-record/pair 精确复现；global 最多漂 0.19，metadata 最多漂 0.16，第二环境最多漂 0.47 | metric points；当前两个环境 | reproduction envelope 必须写明 | 唯一漂移原因、raw-precision exactness | `research/research_direction_sprint_20261020_v1/execution_v1/PAPER_E_EXTERNAL_AUDIT.md` | 原始 score matrices + 完整锁定平台/依赖 |
| C2 | 开发观察 | neutral retry 56/72 correct；localization 49/72（0 W2C、7 C2W）；execution 40/72（0 W2C、16 C2W） | 72 frozen outputs，24 families ×3 variants | 当前一跳反馈修订未超过 neutral | feedback learning 整体无效 | `research/feedback_delivery_continuation_20261025_v1/SAME_CANDIDATE_FEEDBACK_A_FINAL.json` | 稳定输出契约下的 source-isolated correction qualification |
| C2 | 开发观察 | localization feedback 有 3/72 false alarms、12/72 insufficient | frozen initial candidate + actual visible feedback | feedback-quality diagnostic 的开发边界 | teacher/gold、训练监督 | `research/feedback_delivery_continuation_20261025_v1/SAME_CANDIDATE_FEEDBACK_A_FINAL.json` | 教师/确定性 verifier 独立验证的 corrections |
| C2 | 开发观察 | oracle 有 3 W2C，但 54 C2W 且使用隐藏 correctness/discrepancy | 72 outputs；non-deployable diagnostic | 存在有限纠错能力，但反馈不可部署 | E 可训练或优于 R | `research/feedback_delivery_continuation_20261025_v1/FINAL_STAGE_INDEPENDENT_REVIEW.md` | 可见反馈、可执行 patch、source-isolated E 数据 |
| C2 | 真实训练开发结果 | 加载 parent 后激活 child；R/E 各训练 128 steps；39/256 纠正呈现、217/256 no-op/未决 | 36 unique trajectories /12 families；2 child-only runs | 当前实现不满足 ordinary-parent continuation | 所有反馈学习或局部编辑均无效 | `research/feedback_learning_phase_b_20261026_v1/b2/B2_TRAINING_RECEIPT_R.json` | 新来源确认已被停止门阻断 |
| C2 | 有界接口修复后开发结果 | set-binding match：N 72.2%、R 69.4%、E 0%；R/E strict 0/36、embedded 36/36 | 12 families；R/E 72 次新生成，复用首轮 N | E 实现失败；R 仅未观察到增益 | 反馈学习普遍无效或 R 已被因果否定 | `research/feedback_learning_phase_b_20261026_v1/b2b/B2B_DEVELOPMENT_ANALYSIS.json` | 按停止规则不进入确认 |
| C2 | 失败机制 | E 36/36 patch 非法、36/36 interface-UNKNOWN、5 个 originally-correct family damage；R 25 set-binding match/7 wrong/4 UNKNOWN | 72 B2B generations；全部达到 max-token | 当前失败包含 schema/hash/重复输出/截断混杂 | E 仅因模型能力弱而失败 | `research/feedback_learning_phase_b_20261026_v1/b2b/B2B_FAILURES.json` | 若重启需新监督与稳定合同，不复用旧确认 |
| 候选筛查 | 无模型资格结果 | TAT-QA text-only：top-3 378/389，top-5 与 top-3+邻域 385/389，top-10 389/389；覆盖指标非成本指标 | 389 个自然开发问题 | 固定检索/邻域/扩展已解释主要证据获取余量 | 证据获取问题不存在 | `research/decision_residual_pivot_20261026_v1/D_TATQA_TEXT_SCREEN.json` | 未曝光自然来源与越过强基线的残差 |
| 候选资格复核 | 无模型结果 | P1：4 个真实模型错误 + 1 个 reference defect，gold-free policy 修复 4/4；P2：507 table-text，top-3 potential 452、top-5 486、always-expand 506，top-3 成本 66.8% 但 gap 10.65pp | P1 24 ordinary originals；P2 507 questions | 当前强基线后无合格 challenger | 证据使用/取证成本问题不存在 | `research/natural_error_evidence_cost_20261026_v1/STAGE_RETURN.md` | 新自然来源或能越过冻结答案—风险—成本门的 challenger |
| C3 | 开发观察 | original 60 correct/12 wrong；retry 62/10；localization 59/13 | 复用 24-family ×3 variants | retry 是当前最强简单交付基线 | 新 family 泛化 | `research/feedback_delivery_continuation_20261025_v1/DELIVERY_CONFIRMATION_C_V1.json` | 真正 disjoint new-family frozen panel |
| C3 | 开发观察 | semantic gate 32/6/34 abstain，coverage 52.8%；bounded repair 33/6/33，coverage 54.2% | 72 outputs | gate 用 abstention 减少 accepted-wrong | 风险下降带来净行动效用 | `research/feedback_delivery_continuation_20261025_v1/DELIVERY_CONFIRMATION_C_V1.json` | matched risk-coverage + action utility |
| C3 | 开发观察 | original 41,997 tokens/51.99s；retry 52,223/94.42s；localization 64,326/173.91s | 本地单次运行，每条件 72 attempts | 当前运行成本边界 | 稳定吞吐、生产成本或 policy 边际成本 | `research/feedback_delivery_continuation_20261025_v1/DELIVERY_CONFIRMATION_C_V1.json` | 重复运行、GPU/tool/wall cost 与边际 deployment cost |
| C3 | 未验证 | 独立面板上的非 abstention 风险降低、跨来源覆盖和稳定成本优势 | 尚无 | 无 | 已建立交付创新或第三个独立贡献 | `docs/governance/audit/loop_d_control_review/PHASE_A_RETURN.md` | 预注册 disjoint panel、有限行动和独立审计 |
| Publication/proxy A | 开发观察 | P1 numeric 23/24、完整 semantic 13/24、可观察单位 14/24、单位 UNKNOWN 10/24，1 条方向冲突 `UNRESOLVED`；P2 preflight 后 12-item 三臂 ACCEPT 为 top-3 2/12、top-5 3/12、all 3/12，错误交付风险 0.833/0.750/0.750；合计 40 calls、2,609 output tokens、33,207 input tokens | frozen 24 originals；12-item exposed development panel；36 primary + 4 bounded retries | 修正 P1 数值/语义身份；报告同一开发面板的真实答案、风险和成本差异 | 2-point noninferiority、generalization、上/下界；Paper E 已接收/发表/学校认定 | `research/publication_proxy_calibration_20261026_v1/A_REMEDIATION_RETURN.md`、`raw/runs/primary/P2_CALIBRATION_RESULTS.json`、`paper_e_sncs/paper_e_sncs.tex` | 独立自然面板、approved TeX build、Owner 身份/投稿授权 |
| D预算更正 | 合规主样本+执行事故 | 第一批40次为36主调用+4重试；第二批40次为科学载荷相同但物理耗时不同的确定性复跑。实际80/48 attempts、66,414 input、5,218 output；科学估计只从第一批raw零模型派生 | 12-item exposed development panel；两批raw均保留 | 修正“无新增调用”和40-call总账；停止all-context，top-5保留为开发候选 | 把第二批当独立确认/复现证据，或称预算合规 | `research/publication_proxy_calibration_20261026_v1/D_BUDGET_INCIDENT_AND_CORRECTED_ACCOUNTING.md`、`raw/runs/compliant_primary/P2_CALIBRATION_RESULTS.json` | 新预算、新冻结面板和独立确认 |
| 全部 | 未验证 | 2027 年 10 月的确切评审日期 | Owner identity action | 目标窗口仅为 October 2027 | 具体日期或 10 月 31 日 | `research/feedback_learning_phase_b_20261026_v1/B1_A_PAPER_AND_THESIS_TASK.md` | Owner 提供准确日期 |


### 2026-10-26事后复核附注（不回写上表历史计数）

| 对象 | 本次可支持 | 尚不能支持 | 证据 |
|---|---|---|---|
| P1 | 四条错误的可见规则解释；五项错误子集重放 | 统一actor已交付、19条原对无破坏、一般问题残差0 | docs/governance/audit/loop_d_control_review/NATURAL_COST_POST_RETURN_REVIEW.md |
| P2 | 507行算术/hash及启发式分类可复现；两个人工审计反例可复现 | 506条独立完整语义参考、potential为真实答案上界、已测实际成本无收益 | 同目录JSON与natural_cost_post_return_audit.py；自然数值边界5条只是待审标记 |

### 2026-10-27接续更正

| 对象 | 本次可支持 | 尚不能支持 | 证据 |
|---|---|---|---|
| P1 | 统一公共actor与全24题回归已交付；numeric 23/24、semantic 13/24、unit 14/24、4修复/0破坏 | 一般证据使用问题已关闭，或规则actor是学习方法贡献 | `research/publication_proxy_calibration_20261026_v1/p1_rule_execution/full_24_regression.json` |
| P2 | 第一批40次真实三臂结果：2/3/3 ACCEPT；all被top-5弱支配；9/12三臂均失败 | 2点非劣、泛化、全上下文理论上界、代理potential与真实准确率同构 | `research/publication_proxy_calibration_20261026_v1/raw/runs/compliant_primary/P2_CALIBRATION_RESULTS.json` |
| Paper E | 完整两案例期刊派生稿、15页fallback PDF、24/24引用 | 精确TeX-engine构建已验证、投稿/录用/学校认定 | `research/publication_proxy_calibration_20261026_v1/D_INTEGRATION_RETURN.md` |

### 2026-10-27自适应机制A补充（不改写上表历史计数）

| 对象 | 本次可支持 | 尚不能支持 | 证据 |
|---|---|---|---|
| Paper E formal build | canonical 两案例源与 24/24 bibliography 源检查通过；本机无 TeX 引擎，`BUILD_BLOCKED`；Owner/专利/artifact/投稿字段待定 | 精确 engine/version、PDF hash/page count、正式 bibliography 渲染、投稿或学校认定 | `research/adaptive_mechanism_20261027_v1/paper_e_formal_build/BUILD_BLOCKED.md`、`SOURCE_CHECK_RECEIPT.json` |
| Scoring V2 | 第一批 40 calls 的 36 个最终 attempt 零模型重评分；历史 2/3/3 保持可见；top3 `7R/4SF/1P`、top5 `8R/4SF`、all `7R/5SF`；输入差 917/1,604 | 人工 gold、预注册确认分、完整语义 oracle、C acceptance | `research/adaptive_mechanism_20261027_v1/scoring_v2/results/FIRST_BATCH_RESCORE_V2.json`、`SCORING_TEST_RECEIPT.json` |
| Error cards | 12 张证据卡：9 个旧共同 REJECT + 3 个非共同控制；标签来自 raw/可见上下文/评分层，不是模型自述 | 模型自我解释有效、人工标签共识或一般错误分布 | `research/adaptive_mechanism_20261027_v1/diagnostics/results/ERROR_CARDS.json` |
| Visible typed baseline | 36/36 零模型；`ACCEPT 31 / REASONABLE_UNKNOWN 5`；mean/count/percentage 可见 typed reduction 被解释；无未解释自然残差 | 模型准确率提升、方法增益、泛化或 new-source validation | `research/adaptive_mechanism_20261027_v1/diagnostics/results/VISIBLE_TYPED_BASELINE.json`、`DIAGNOSTIC_SUMMARY.json` |
| Persistent budget | 外部 hash-chained/fsynced ledger 初始化 SHA256 `ad0535…fdef`；7 项 fault injection 其中 attempt-37/token-cap 在 loader 前拒绝；真实 attempts/tokens/model loads=0 | GB10/生产稳定性、实际生成成本或真实模型预算使用 | `research/adaptive_mechanism_20261027_v1/persistent_budget/BUDGET_RECEIPT.json` |
| Diagnostic panel | 8 UID、三臂、提示词、输出合同、calculator、Qwen3-4B hash、解码和停止规则已冻结；强 baseline 解释或约束全部自然残差，故 `STOP_BEFORE_GENERATION` | 三臂方法增益、确认运行、新来源验证或 C acceptance | `research/adaptive_mechanism_20261027_v1/diagnostic_panel/DIAGNOSTIC_PANEL_PREREGISTRATION.json` |

| 自适应机制 C/D复核 | 零模型边界消融 | gold `answer_type` 基线 31/5；blank-type 12/19/5；question-only 31/5，且 5 个 UNKNOWN 均为可见段落缺失 | 12 UID × 3 arms，同一第一批 raw 和 scorer | 问题文本类型启发式可复现该面板残差收束 | 通用 answer-type 推断、跨来源方法收益；冻结面板生成结果 | `research/adaptive_mechanism_20261027_v1/d_integration/results/QUESTION_ONLY_ABLATION.json`、`audits/C_JOINT_AUDIT.md` | 新来源、answer-type-free 冻结面板 |

| 2026-10-27 条件收尾 | Word/Scoring V3/同源新表族 | 14页内部渲染；三类配对控制通过；D/T/M真实执行但512-token截断与臂完全共线 | 8 family ×3 arms，27 reservations，46,054 input+output | Scoring V3、同源曝光和持久预算可用 | 提交级Word完成、M有效/无效、机制增量 | `research/word_scoring_new_family_20261027_v1/D_CLOSEOUT_RETURN.md`、`audits/C_JOINT_AUDIT.md` | 修Paper E或新24-call高输出预算 |
