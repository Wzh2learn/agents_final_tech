# 小论文内部送审验收结论（方向校准版 v2）

> 结论日期：2026-09-22
> 判定：**评估子稿可作为导师讨论材料，但不应再被称为完整小论文；不可对外投稿或公开。**

## 送审范围

- 主稿：`paper/teacher_review_draft_v1.docx`
- 可追踪文本：`paper/teacher_review_draft_v1.md`
- 中文说明：`paper/teacher_review_note_v2.md`
- 三阶段总叙事：`paper/research_story_v2.md`
- 三阶段方向 Word：`paper/research_story_v2.docx`
- 总架构图：`paper/figures/fig_evaluate_distill_evolve_v1.svg`
- 主张清单：`paper/claim_manifest_v1.json`
- 机械验收结果：`paper/acceptance_report_v1.json`

## 审稿式检查

| 维度 | 结论 | 依据或剩余边界 |
|---|---|---|
| 评估子稿故事 | 通过 | 问题、方法、结果和限制均围绕“评测协议能否看见缺陷”展开 |
| 用户原始三阶段方向 | 未闭环 | 蒸馏尚无训练结果；规则进化只有机制与受限收益证据 |
| Claim–Evidence 结构 | 静态通过 | 5 条主张、73 项章节/措辞/路径/证据检查；不替代原始数字复算或科研有效性审计 |
| 实验诚实性 | 通过 | matched-FPR 等价、PSO null、门控无显著收益均保留 |
| 表述边界 | 通过 | 不再主张已证明额外定位收益；第二数据流/第二 scorer 明示缺失 |
| 老师阅读形态 | 通过 | Word 结构完整；两份 DOCX 已于 2026-10-03 完成 Office 排版/分页视觉验收并 PASS |
| 对外公开 | 阻塞 | 专利状态尚未由用户确认；作者、单位和目标会议模板未填写 |

## 2026-09-22 阅读核对回执

- 逐段核对英文评估稿、中文说明、总叙事和本判定；推荐阅读顺序：中文说明 → 总叙事 → 英文评估稿，先理解目标与现有证据的区别。
- 已修正文 §5.1 的反向表述：OCR 为 **0/13 可见、13/13 被吸收**；旧静态门只认裸数字，现已改为方向性句子并加负控测试。
- 已按 T1 源码/工件纠正 Table 1 的检测信号，移除从完整树误套的“2 roots / 12 leaves”；补清 96 个可见与 112 个 mapping 文本变化、20 张表与13个单注入不是同一计数。
- 已解释校准 0.5 是历史维均分的 control 汇总差异，不是单 cell 或原始答案的跨 judge 一致率；规则效应补为 15 张碰撞表上的平均配对 ACC 差 0.05（5 个百分点），95% 区间 [0, 0.1056]，仍无显著收益主张。
- 英文稿与方向稿 DOCX 均离线重生成，全文段落/表格与对应 Markdown 比对通过。**本机没有 LibreOffice/soffice，Office 视觉核对未完成**；不声称分页、缺字或表格溢出已验，需在有 Office 的环境打开两份 DOCX 后再确认可发送版本。
- 本地 P1 审计不放行训练：动作 SFT/风险预筛为 DATA_NO_GO，DPO 为仅保留审计素材的 PILOT_ONLY；两者都不是训练许可，详细依据见资产账本 §3.1。

## 已确认与待确认

已确认：三阶段主线、4B 仅训练链 smoke、8B 主学生、小模型不替代确定性门，以及成熟评估稿保底。本地审计已交付；后续实验等待用户批准。

导师/用户仍需确认：主指标和非劣/安全容差、训练窗口及资源预算、专利申请状态与权利要求覆盖。DPO 仅在独立偏好数据门通过时执行，不预设 60 对单向偏好足够。

## 2026-09-22 下一轮计划（历史记录）

本地数据审计和内容核对已交付；当时计划由服务器接手剩余测试、两份 DOCX 的 Office 视觉核对。该 Office 项已于 2026-10-03 关闭；Phase 1a/2、数据补充及训练仍按后续明确授权推进，不因本地缺件判另一服务器资产失败。

24–48 小时内部方向包使用成熟评估稿与当前三阶段说明，不等训练；实验完成后的统一初稿另过证据门。数据不足、简单基线已足够、非劣或安全门失败时按现有计划拆稿，不临时改门救结果。

## 2026-10-03 状态附记

本附记更新上文 2026-09-22 的阶段性判断：两份 DOCX 的 Office 视觉验收已完成并 PASS；当前 claim manifest 为 5 条主张，GB10 `validate_paper_claims` 为 PASS / 74 checks，专用验收测试为 9 passed。G-A、G-B、G-C 不批，G-D 只批准 `target_table.csv` 表头作 canonical 参考，G-E 接受 `DATA_NO_GO` / RQ2 `NOT_IDENTIFIED`；V2-3 已关闭。146 列 Q3 review 已完成并封存 corrected ledger `51/58/37`，但 visibility exceptions 保留，只能作为 exploratory evidence，不能作为 Stage D、RQ2 或训练证据。

当前唯一执行计划仍为 `docs/handoff/2026-09-22-paper-research-next-phase.md`；本附记只更新状态，不另立平行计划。

## 2026-10-07 narrative revision and independent-evidence backlog

The Stage E manuscript now leads with the counterintuitive result `Visibility Is Not Detection`: hierarchical checkpoints decompose evidence but do not improve matched-FPR discrimination in the current instantiation. The abstract, introduction, method framing, result heading, limitations structure, and conclusion were synchronized without changing any measured value or claim boundary.

Future evidence required before making broader or stronger claims:

1. **Second dataflow:** a corpus with a real table layer, UID-disjoint split roles, and controlled perturbations must reproduce the visibility profile without changing the frozen criteria.
2. **Independent second scorer:** a scorer independent of the current semantic-judge endpoint must reproduce the frozen leaf-state cells; the stopped step-level route does not satisfy this clause.
3. **Multi-leaf responsiveness:** localization claims require more than one scored leaf to vary with the injected input; otherwise localization remains unestablished.
4. **External scenarios:** later work may test financial audit, compliance review, enterprise table processing, and other long-horizon document workflows. Each scenario must define its own observability and harmfulness criteria before results are compared.
5. **Claim upgrade discipline:** none of these future items may be reported as current Stage E evidence until the artifact, split, scorer independence, and review receipts are complete.

These are future independent-evidence requirements, not missing paragraphs to be filled with planned results.
