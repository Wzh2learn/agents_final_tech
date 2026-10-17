# Loop D 中断恢复交接 — 2026-10-17

核查人：总规划师 AI；依据本地文件、Git 状态、GB10 只读文件/账本/进程检查。本轮未调用模型、未运行实验、未修改实现或旧结果。

## 结论与已完成事项

- 中断的是 Loop D 对话，不是尚在进行的 TQ-4 实验。TQ-4 已完成，禁止重新生成。
- TQ-4 run_id=`20261016T082849Z_430d927a`；36 attempts、0 retries、40205 tokens。首请求北京时间2026-10-16 16:29:02，末响应16:32:16，194秒。
- 2026-10-17本次本地核查：TQ-4冻结材料49/49、TQ-5冻结材料49/49、TQ-4运行清单84/84哈希一致。该检查不冒称完整科学复核。
- TQ-4运行独立复核已落盘：reviews/POST_RUN_REVIEW_v1.md，结论无阻断、有8条注记。无需继续等待或再次委派相同复核。
- TQ-5预运行独立复核已落盘：../tq5_source_validation_v1/reviews/TQ5_PRE_RUN_REVIEW_v1.md，结论NO_SUBSTANTIVE_BLOCKER。确认12张表与已登记221项排除并集无重合；仅支持table-disjoint开发性表述。
- TQ-5规格v2在输出前修正百分比公式编码识别，独立复核已确认不是根据结果选题或降低参考检查标准。本次认可继续使用已冻结v2，不退回v1或重建面板。

## 实际中断点和运行状态

- S1实现完成；S2 TQ-4运行完成；S3独立复核完成但注记/状态未收口；S4 TQ-5面板与预检完成，尚未运行；S5仅有草稿。
- GB10实际检查：TQ-5 runs/仅.gitignore，无run目录或RECEIPT；chain_master_ledger只有TQ-4的36 reserve/36 settle。未发现匹配chain_runner/tq4_runner/tq5_runner的运行进程。
- 本地与GB10 Git HEAD均为1c7a94a系列提交；这只说明提交点一致，不代表最新工作区已同步。大量新增执行代码、两份复核及closeout未提交；保留全部现场。
- GB10缺少以下本地文件：tq4/reviews/POST_RUN_REVIEW_v1.md、tq5/reviews/TQ5_PRE_RUN_REVIEW_v1.md、tq4/closeout/CHAIN_RETURN.md。本地已经存在，不能等远端自动出现。
- CHAIN_RETURN.md中“复核在途”“最终MD待达”过时；它是草稿，不是当前状态的最高依据。

## 接手时必须先读

本地项目根：`D:/AIRcommend/JinRongAgents/agents_final_tech`。
以下相对路径以 `research/paper_e_layer1_20261015/scientific_qualification/task_gold_qualification_v1/` 为基准：

1. `tq4_calibration_v1/run_card_v2/OWNER_DELEGATED_AUTHORIZATION_20261016_v1.md`（仍有效的G1–G5及S1–S5授权）。
2. `tq4_calibration_v1/reviews/POST_RUN_REVIEW_v1.md`（已完成的运行复核及注记）。
3. `tq5_source_validation_v1/reviews/TQ5_PRE_RUN_REVIEW_v1.md`（已完成的运行前复核）。
4. `tq4_calibration_v1/execution_v1/TQ4_RUN_RETURN.md`（旧报告，部分措辞需勘误）。
5. `tq5_source_validation_v1/TQ5_PANEL_SPEC_v2.md`。
6. `tq5_source_validation_v1/execution_v1/chain_config_tq5.json`。
7. `tq4_calibration_v1/closeout/CHAIN_RETURN.md`（待更新的交付骨架）。

必要时从两份复核链接读取重算JSON，不再全量研究历史对话。新对话应在当前工作目录继续；不要只clone origin或新建干净worktree来替代未提交现场，不使用reset/clean，不覆盖其他任务脏文件。

## 已授权且必须完成的下一步

1. 开场重新查看本地/GB10 runs、主账本及匹配进程，防止本交接之后已有执行者启动。若出现新请求，以最新账本为准，不能沿用本文件的零TQ-5快照。
2. 保存本地已有产物，定向同步缺少的复核/交接材料；依据现有规则提交代码、授权和摘要。原始run输出/数据/日志不推Git，采用文件镜像。不可覆盖他人改动。
3. 收口S3注记，另存勘误/新分析版本：
   - B有效决策15/16（Part1 4/4、Part2 11/12）；35/36是全run合法输出数。请求HTTP成功不等于输出有效。
   - 矩阵中解析失败必须显示invalid，不把ledger_state=done当作模型决策。
   - 点检记录为14项；首请求和时长采用16:29:02/194秒口径。
   - N1只支持“参考匹配与核验存在语义分歧”；不能凭模型报警判定参考错或actor绝对正确。C字段alarm，但contradiction_points为空、理由尾部有接受措辞，单列内部不一致，不替它补造一致理由。
   - Q03人工负例的运算方向存在歧义，保留原构造标签与原结果，在解释层标语义资格未成立；不能以它统计已证实的共同漏检。不得在看结果后换题补跑。
4. TQ-5启动前加固运行快照：保存实际使用的config、runner、评分器、模板、分析器及其哈希，纳入新run manifest；执行和分析均从该不可变快照读，防止边运行边改配置。
   - TQ-4 config哈希已无法由当前文件复现。旧稿称“运行后修改”，但复核记录mtime落在运行窗口内；不能继续无证据断言只在运行后改了scoring_dir。
   - 如没有真正的旧快照，保留缺口；用已有raw/prompts/ledger证明已发生的实际行为，不生成假旧配置或改RUN_META hash消除差异，不重跑TQ-4。
   - 快照/invalid展示修复在新文件或execution_v1/recovery_v1/完成，保留原实现。只对新增变更做定点检查及必要聚焦复核，不重做全套科研规划或整个旧复核。
5. 既有TQ-5预检加上述定点检查无阻断后，按现有授权直接启动唯一一次TQ-5。旧runner CLI确有--config、--root、--plan、--check-pins、--run、--resume；正式执行须使用完成快照加固后的入口。GB10 root覆盖必须为Linux绝对路径，不能将配置里的Windows root用于GB10。
6. 完成TQ-5离线评分、结果分析和聚焦复核，记录table-disjoint/开发性边界。更新CHAIN_RETURN.md，交付CONTRIBUTION_RULING.md及PAPER_E_ADDENDUM_DRAFT.md；保持冻结稿、旧参考与旧实验不变。

## 剩余预算和时间（不需重新向owner申请）

- 现有授权至2026-10-19 20:00，北京时间；只在09:00–18:30启动，单次≤90分钟且20:00前停止。
- TQ-4已消耗36请求/40205 token，实验已结束。未用的4次不能转给TQ-5。
- TQ-5仍允许36计划请求、最多4次基础设施重试、总请求≤40、token≤400000；模型、参数、单并发及USD0新增付费实验API边界按授权原文。
- 总链≤80请求/800000 token不等于TQ-5可用44请求或759795 token；两级上限同时约束。沿用原主账本，不新建空总账。
- 如果TQ-5还未启动，2026-10-17/18/19可依授权选择白天新窗口；这不是跨窗口恢复旧run。若发现TQ-5此前已经发过请求，先按原授权的续跑和停止规则处理，不能再当首次启动。

## 尚未成立的科研结论

- TQ-4已出现模型核验分歧、引用报警、格式失败与候选方向歧义；它们不证明C优于B或存在普遍共同盲点。
- 引用定位合法性不等于引用支持性；后者仍NOT_ASSESSED。C看不到候选引用，不评其支持性。
- TQ-5预检中的参考字段一致/算术复算/数字可定位不是独立人工语义gold；运行后仍要保留reference uncertainty和UNSCORABLE，不强行将每一项异常当模型错误。
- 结束后允许NO_PROMOTION。目标是完整、可解释的实际证据，不为了差异或漂亮表格追加第三轮。

## 完成条件

新Loop D完成S3收口、唯一一次允许的S4运行（或有证据的NOT_RUN/PARTIAL）和S5三项交付，并报告真实同步范围、预算、复核范围及全部偏差。除实质停止条件外，在现有授权内连续推进；不要再等待已经落盘的两份复核。
