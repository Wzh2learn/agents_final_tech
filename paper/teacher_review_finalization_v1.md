# 小论文定稿基线与三阶段回填位 v1

> 状态: 定稿基线记录（2026-09-24, Loop D）| 密级: **仅限内部审阅**（`release_gate = patent_status_confirmation_required`）
> 本件不含任何新数字；所有数字一律回指已验收 artifact。用户裁定（2026-09-24）：小论文按评估保底稿推进定稿，
> 同时保留三阶段回填位；数据门后续通过再升级，**不无限等待**。

## 1 定稿基线（评估保底稿，送审候选）

基线 = commit `1627a54` 上的以下 8 件，彼此哈希互锁，缺一即不称定稿：

| 件 | 角色 |
|---|---|
| `paper/teacher_review_draft_v1.md` | 可追踪文本主稿（9 个必需章节齐备） |
| `paper/teacher_review_draft_v1.docx` | 送审形态；Office 视觉验收见 `docs/experiments/2026-09-24_docx_office_visual_acceptance.md` |
| `paper/teacher_review_note_v2.md` | 中文说明（推荐阅读顺序第一件） |
| `paper/research_story_v2.md` / `.docx` | 三阶段总叙事与方向 Word |
| `paper/figures/fig_evaluate_distill_evolve_v1.svg` 与 `docs/experiments/figures_paper/` 两张必需图件 | 图件 |
| `paper/claim_manifest_v1.json` | 4 条主张 + 10 个内部流程标记清单 + 专利门 |
| `paper/acceptance_report_v1.json` | 机械验收结果（`tests/test_paper_claim_acceptance.py` 7 passed） |
| `paper/teacher_review_readiness_v2.md` | 送审验收结论；其「视觉未验」一行已被视觉验收证据件关闭 |

基线**不含**三阶段结果：Stage D 无学生训练，Stage R 只有机制级证据。这两块在基线里只以边界与
否定性结果的形式出现，且**不允许**在升级前被改写为成果。

## 2 三阶段回填位（slots）

回填纪律：只允许**新增小节**或替换本表登记的显式占位句；**不得回改已验收段落的数字**；不得把目标
贡献写成已有结果；每次回填单独成批并自带验收与独立复核。

| slot | 落点 | 回填内容 | 前置门 | 数字来源（回填时才存在） | 当前状态 |
|---|---|---|---|---|---|
| BF-1 | 主稿 §5 新增小节「Distillation transfer」 | 8B 主学生的动作策略蒸馏结果与质量—成本对照 | SOURCE_GO → LABEL_GO → SPLIT_GO → POWER_GO → BASELINE_GO → MODEL_GO 全过 + 独立验收 | 未来 run 的 artifact，经 `research/paper_result_views.py` 且独立审查后才允许 `paper_result=true` | 空（目标） |
| BF-2 | 主稿 §5/§6 | 七臂规则门的功效与强基线对照、独立 gate-validation、版本回滚曲线 | Phase 2 replay + 功效分析 + 独立 gate-validation | `research/phase2_rule_gate_replay.py` 的独立验收输出 | 仅机制级（7/7 与 5/5 拒绝），功效空 |
| BF-3 | 主稿 §6 Discussion | 第二数据流 / 第二 scorer 的复现 | 相应实验完成 | 新 artifact | 明示未主张 |
| BF-4 | 主稿 §4 Setup | future replay 纵向证据 | 哈希绑定的获取协议 | 协议 + 获取时间 + 分层规则 | `LONGITUDINAL_EVIDENCE_UNAVAILABLE` 容忍 |

## 3 投稿前剩余阻塞（本件不解除，逐项有归属）

- **专利门**：`release_gate = patent_status_confirmation_required`，只有用户本人确认后才能外发；确认前不上 arXiv、不公开代码。
- **作者 / 单位 / 目标会议模板**：按专利门要求**留空**；venue 与 CFP 未经官方源核实一律不写入。
- **内部流程标记纪律**：继续由 `tests/test_paper_claim_acceptance.py` 机器检查，含反向负控用例。
- **Figure 2 的柱底标注偏紧**：属已提交位图图件内部细节，记录于视觉验收证据件 §5，单独成批处理。

## 4 升级与止损（不无限等待）

- 数据门打开且 BF-1/BF-2 的前置门逐门通过时，按 §2 顺序回填，评估保底稿升级为三阶段稿的一部分。
- 触发任一止损条件（数据仅 `PILOT_ONLY`、简单基线已足够、非劣或安全门失败、安全回归）时，**基线原样交付**，
  Stage D/R 转入大论文作为边界与后续工作；不为救结论改 split、阈值、家族或容差。
- 所有 null / adverse 结果（matched-FPR 仿射等价、PSO null、门控无显著收益）原样保留。
