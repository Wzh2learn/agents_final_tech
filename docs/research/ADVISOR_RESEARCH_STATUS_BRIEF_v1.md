# 导师研究状态简报（2026-10-13）

> 用途：供导师快速了解当前两项主线的真实状态与待决问题。本简报不含任何新 claim；所有数字与冻结证据一致，未授权任何不可逆动作（注册/投稿/发布均待确认）。

## 1. Paper E 当前状态

- 论文（T1）：*Visibility Is Not Detection: Auditing Observation Boundaries in Staged Document-Intelligence Evaluation*，SANER RENE: NegativeResult 形态的测量有效性审查。
- 状态：**冻结版已完成并通过全链路审计**——9 页（含附录≤10 页，参考文献≈1 页）、0 overfull、引用 21/21、双匿名合规、机器审计 `PRE_SUBMISSION_AUDIT = PASS`。
- **独立复核已交付**（经设计旁路通道执行）：v2 CONDITIONAL → 9 项残项全部修复 → v3：条目落实与 claim 边界均 PASS；一处单字图注问题已按审计方裁定修复并双端机器复验。记录：`docs/research/LOOP_C_INDEPENDENT_AUDIT_A1A7_v1.md`。
- 科学边界（冻结）：visibility ≠ detection ≠ harmfulness 三构念分离；单响应叶结构等价（正仿射/秩一致）；clean 面板退化使部署工作点未确定；多叶显式插桩构造内可分离签名（无 hierarchy 增量）；FinQA 为 measurement-object mismatch 失败迁移。**不声称**通用盲点、层级定位、自动选择器或长程经验结论。

## 2. 投稿选择建议

- **首选：SANER 2027 RENE: NegativeResult**（当前默认）。契合度最高（负结果+可复现性定位），格式与匿名要求已按官方页面核验；时间：摘要注册 10/19 AoE、全文 10/23 AoE（距今约 6 天）。
- 备选（若需要换窗）：**ICST 2027 Research** 移植成本 LOW-MEDIUM（oracle/可诊断性叙事几乎原生适配）；**CAIN 2027 Research** 需要中等重构（AI 工程框架 + 新 related-work 层）。移植成本估算见 `VENUE_PORTABILITY_NOTE_v1.md`，未做任何改稿。
- 建议：若本周内可确认署名与注册授权，维持 SANER RENE 投出；否则按备选计划排期，paper 冻结版可直接复用或低成本移植。

## 3. 大论文候选路线（TAT-QA WP-0）

- 最小研究问题：固定模型、工具与预算下，来自其他来源（origin）的相关真实执行经验，是否改善新来源两期表格计算任务的答案正确率与执行一致性。
- WP-0 **A1–A6 全部完成**：许可核验（MIT + CC BY 4.0）；raw 数据获取（2479 条记录，sha256 回执）；origin 构建 182 个（远高于 8 个需求）；候选 items 60 条（60 origins）；任务适配/检查器契约；资格附录。
- 门裁决建议：**G-RQ = QUALIFIED_CONDITIONAL**（材料侧已就绪；还差 feedback-right、actor revision、预算窗口三个绑定）；**G-M = HOLD**（尚未发现方法必要性，`METHOD_NOVELTY = NOT_IDENTIFIED`）。
- 可逆准备工作已完成（四份草案）：feedback-right 合约草案、actor revision 冻结方案（候选 Qwen3-8B / 4B，已有 GB10 验证回执但均非 MODEL_GO）、评测协议、Loop A 执行包（仅薄实现+fixture，无模型调用）。
- 下一步（需批准后才执行）：WP-1 薄执行器 + fixture 校验（**不训练、不调模型**）；通过后才有 WP-2 最小 pilot 申请。

## 4. 风险与需导师决策的问题

1. **venue 最终拍板**：SANER RENE vs ICST/CAIN（影响投稿时间线与叙事）。
2. **署名**：第一作者王中华已确定；共同作者顺序与通讯作者需确认（SANER 要求录用后署名不可变更，建议 10/23 前锁定）。
3. **注册/投稿授权**：abstract registration（10/19 AoE）与 full submission（10/23 AoE）均为不可逆外发动作，需明确同意。
4. **WP-0 三个绑定**：feedback-right（历史上允许展示哪些反馈/修正）、actor revision 冻结（选 Qwen3-8B 还是 4B，及 MODEL_GO）、预算/窗口（蓝图上限：300 次请求、0 judge）。
5. 其他已关闭项：专利问题（无，导师已同意投稿）；artifact 暂不公开（只备匿名包）。
6. 风险提示：SANER RENE 评审强调"负结果必须来自无效应而非方法学不足"，当前稿件已按此收窄；若换 venue，需要按移植说明重排 framing（不改数据）。

## 5. 参考入口

- 投稿执行交接：`docs/research/SUBMISSION_EXECUTION_HANDOFF_v1.md`
- 投稿清单与冻结护栏：`docs/research/SUBMISSION_READY_CHECKLIST_v1.md`、`PROJECT_FINAL_STATE_BEFORE_SUBMISSION.md`
- 独立审计记录：`docs/research/LOOP_C_INDEPENDENT_AUDIT_A1A7_v1.md`
- WP-0 资格附录：`docs/research/WP0_TATQA_QUALIFICATION_APPENDIX_v1.md`；四份准备草案见 `docs/research/WP0_*` 与 `WP0_TATQA_*` 系列

**等导师确认后，才进入不可逆执行（注册/投稿/发布）或 WP-1 实施授权。**
