# 科研主线与论文验收入口

> 状态: 活跃 | 更新: 2026-09-22 | 取代/被取代: 不取代受保护路线文档；作为当前执行与验收入口

本文只回答三个问题：小论文在证明什么、大论文如何承接、下一项工作怎样验收。历史实验过程仍保留在 `docs/experiments/`，不在这里重复。

## 1. 权威顺序

出现冲突时，按下列顺序判断：

1. 用户在 2026-09-22 明确恢复的小论文三阶段方向：大模型流程评估、小模型蒸馏、自学习规则进化；当前落盘为 `paper/research_story_v2.md`。
2. `docs/34_专利_小论文_大论文协同研究路线.md`：上一轮为降低拒稿风险形成的“评估单线”裁定及公开边界（受保护，只读）；其中专利边界继续有效，论文范围由本次用户校准更新。
3. `docs/experiments/2026-08-30_phase_a_autopsy_and_claim_set_v2.md`：评估子稿的冻结主张与降级口径。
4. `logs/graph/eval/` 与 `docs/experiments/`：数字、预注册、审计和复现证据。
5. 早期路线、任务卡和旧稿：只用于追溯，不能覆盖以上现行结论。

## 2. 统一科研主线

### 2.1 会议小论文：评估—蒸馏—规则进化

当前目标故事见 `paper/research_story_v2.md`：流程评估产生可信 checkpoint 信号，可信轨迹用于小模型蒸馏，小模型或大模型提出的规则候选经验证门控后进入可回滚规则记忆，并重新进入同一评估协议。

| 阶段 | 论文责任 | 当前资产 | 成熟度 |
|---|---|---|---|
| E 大模型流程评估 | 提供可信训练/验收信号 | 95 表、118 注入、检查点树、可见性与协议审计 | 已闭环 |
| D 小模型蒸馏 | 把过程能力迁移到 4B/8B 学生 | 零样本矩阵、文献、60 条 DPO 对 | 未训练，当前最大缺口 |
| R 自学习规则进化 | 把稳定经验固化为可审计规则 | gain–collateral 门、碰撞/对抗实验、bandit/DPO 工件 | 机制级，功效待补 |

`paper/teacher_review_draft_v1.md/.docx` 只覆盖 E 阶段，现定位为成熟证据子稿或分拆投稿备选，不再代表完整小论文。

### 2.2 评估子稿：已完成的证据底座

暂定题目：*Discriminability-Aware Evaluation of Long-Horizon Document AI Pipelines via Hierarchical Checkpoints and Defect Visibility Analysis*。

唯一主问题：最终答案正确时，长流程系统的中间缺陷是否仍可能被静默吸收，以及评测协议本身能否发现这种缺陷？

| 研究问题 | 稿件责任 | 当前证据 | 当前结论边界 |
|---|---|---|---|
| SP-RQ1：缺陷在哪一层可见、在哪一层被吸收？ | 主贡献 | 95 表、118 注入、阈值网格和可见性谱 | 只主张受测文档管线；字符扰动危害性依赖等价类定义 |
| SP-RQ2：分层检查点带来什么？ | 主贡献 | 端到端、扁平、层级协议与 matched-FPR 对照 | 当前只证实证据分解；不主张检出率更高，额外定位收益仍待多 leaf 变化场景验证 |
| SP-RQ3：结论是否依赖协议、匹配器和评分口径？ | 严谨性贡献 | 跨匹配器、匹配竞争、judge 校准、种子与敏感性分析 | 第二数据流和第二 scorer 尚未闭合，不外推为普遍定律 |
| SP-RQ4：评测发现能否反馈系统改进？ | 半页机制案例 | VGRM 门拒、规则固化与回归记录 | 不主张 VGRM 显著净收益；PSO 仅报告 null/负面结果 |

小论文明确不承担：VGRM 显著效果、PSO 优越性、严格“盲锥”理论、RL/DPO/bandit 扩展、任意长流程系统的普遍外推。

### 2.3 研究生大论文：展开三阶段并验证长期闭环

| 创新点 | 核心问题 | 与小论文关系 | 独立验收条件 | 成熟度 |
|---|---|---|---|---|
| TH-I1 判别力感知的分层评测 | 如何以可控成本获得可诊断证据？ | 小论文 SP-RQ2/RQ3 是主体证据 | 强基线、多种子、不确定性、成本口径、第二类长流程 | 中高 |
| TH-I2 缺陷可见性与静默吸收 | 哪些缺陷为何不可见？ | 小论文 SP-RQ1 是主体证据 | 等价类、强度梯度、匹配器边界和跨数据流复现 | 中高 |
| TH-I3 评估引导的小模型过程蒸馏 | 如何将可靠过程能力迁移到低成本学生？ | 小论文 D 阶段 | 4B/8B、SFT/DPO、未见家族 holdout、质量—成本 Pareto | 低，最高优先 |
| TH-I4 验证门控的规则自学习 | 如何安全固化并回滚？ | 小论文 R 阶段 | no-gate/gain-only/collateral-only/confidence/holdout/rollback 强基线，功效分析 | 中 |

大论文不是把小论文拉长。TH-I1/TH-I2 复用评估底座，TH-I3 扩展多学生/多教师和泛化，TH-I4 扩展长期安全性与学习门。视觉补盲仅作 TH-I2 的条件性实验。

## 3. 论文导向验收体系

任何新测试、脚本或实验必须先绑定一个 `SP-RQ*` 或 `TH-I*`。不能回答论文问题的“全链路通过”只算工程健康检查，不算科研验收。

| 门 | 必须回答 | 通过证据 | 失败时处理 |
|---|---|---|---|
| G0 主张门 | 要支持或证伪哪条主张？ | 冻结 claim、成功/失败判据、禁止修改项 | 无 claim ID 不执行 |
| G1 构念门 | 注入真代表缺陷吗？指标真测到目标吗？ | 等价类审计、正负控、匹配器/评分口径说明 | 降级为边界或无效 mutant，不换标签救结果 |
| G2 数据门 | split、样本、分母和污染边界可靠吗？ | 公开数据卡、固定 hash、无甲方数据、表级聚类口径 | 批次无效，不进入论文 |
| G3 对照与统计门 | 结果能排除简单解释吗？ | 强基线、消融、多种子、CI/效应量、成本 | 收窄主张或保留 null |
| G4 复现门 | 独立环境能重建数字吗？ | 固定命令、环境、种子、输出 hash、数字到工件映射 | 不得写入正文结论 |
| G5 稿件一致性门 | 文字、表图和工件是否同口径？ | claim-evidence 表、术语/分母/数值扫描、独立审稿 0 blocking | 只修稿，不用新实验掩盖矛盾 |
| G6 外部效度门 | 结论能推广到哪里？ | 第二数据流、第二 scorer 或明确限制 | 使用预注册降级表述 |
| G7 公开门 | 可以投稿或公开吗？ | 专利申请状态及权利要求覆盖由用户确认 | 未确认前不外发、不上传 arXiv、不公开核心代码 |

### 验收结果只有四种

- `PASS`：预注册判据满足，可以支持指定 claim。
- `PARTIAL`：只支持收窄后的 claim，必须同时写限制。
- `NULL`：没有预期增益，但实验有效；保留为科研结果。
- `INVALID`：构念、数据、执行或证据链失败；不能进入论文。

“服务启动成功”“pytest 全绿”不能单独得到以上任何科研结论。

## 4. 当前就绪度

### 小论文

- T1/T2/T6 实验与 T7 回填已完成；Algorithm 1 已入稿并有实现对位表。
- 2026-09-21 双模型独立审稿均判定 `REVISE`；随后已完成口径、hinge、算法编号、门控披露等 P0 文本修订。
- 评估子稿已完成干净稿、Related Work、claim—number—artifact 机械验收。
- 完整三阶段小论文的最高价值缺口是蒸馏 MVP；第二数据流/第二 scorer 次于该缺口。
- 完整三阶段稿尚未达到投稿就绪；即使科研验收通过，专利公开状态仍是独立外发硬门。

### 大论文

- TH-I1/TH-I2 已有较完整的小论文证据底座。
- TH-I3 只有训练前矩阵、文献和偏好对，尚无蒸馏结果。
- TH-I4 有机制与探索性证据，强门控基线和功效分析尚未闭合。

## 5. 论文验收基线 v1

目标不是新跑模型，而是把现有科研资产变成可审计、可投稿、可继续扩展的基线。

当前已建立第一版仓内资产：

1. `paper/teacher_review_draft_v1.md`：独立的干净老师审阅稿；原内部稿继续作为证据底稿。
2. `paper/claim_manifest_v1.json`：每条 claim 对应稿件数字、证据、适用范围和降级边界。
3. `research/validate_paper_claims.py`：静态检查章节、证据路径、关键数字和内部注记泄漏。
4. `paper/teacher_review_draft_v1.docx`：老师可直接打开的 Word 审阅版，由 Markdown 离线生成。
5. `paper/teacher_review_readiness_v2.md`：方向校准后的内部送审判定、阻塞项与导师审阅问题。
6. `paper/thesis_manuscript_scaffold_v1.md`：大论文章节、创新点、小论文继承与新增证据边界。
7. `paper/research_story_v2.md`：三阶段统一故事、证据成熟度和最小蒸馏/规则实验闭环。
8. `paper/figures/fig_evaluate_distill_evolve_v1.svg`：三阶段总架构图。
9. `paper/research_story_v2.docx`：可直接交导师讨论的三阶段方向说明。
10. `paper/research_asset_map_v2.md`：评估、蒸馏、规则进化的代码、实验、稿件和缺口索引。
11. `docs/experiments/2026-09-22_distillation_mvp_preregistration.md`：下一项蒸馏实验的 RQ、四臂对照、split、防泄漏和判定规则。

运行：

```bash
python3 research/validate_paper_claims.py
PYTHONPATH=. python3 -m pytest tests/test_paper_claim_acceptance.py -q
.venv/bin/python research/build_teacher_review_docx.py
```

评估子稿已通过 G5。完整三阶段稿下一门是蒸馏 MVP；通过后再决定外部效度优先补第二数据流还是第二 scorer。

本批不包含：生产探测、模型调用、TAT-DQA 解冻、D4 执行、专利公开状态判断或对外发送。

## 6. 常用入口

- 当前内部稿：`paper/draft_v0_s1_s2_s6.md`
- 老师审阅稿：`paper/teacher_review_draft_v1.md`
- 老师审阅 Word：`paper/teacher_review_draft_v1.docx`
- 方向校准说明：`paper/teacher_review_note_v2.md`
- 内部送审验收：`paper/teacher_review_readiness_v2.md`
- 三阶段总叙事：`paper/research_story_v2.md`
- 三阶段方向 Word：`paper/research_story_v2.docx`
- 三阶段架构图：`paper/figures/fig_evaluate_distill_evolve_v1.svg`
- 三阶段资产地图：`paper/research_asset_map_v2.md`
- 大论文稿件骨架：`paper/thesis_manuscript_scaffold_v1.md`
- Claim manifest：`paper/claim_manifest_v1.json`
- 小论文蓝图：`docs/experiments/2026-08-29_long_horizon_eval_paper_blueprint.md`
- 冻结 Claim Set v2：`docs/experiments/2026-08-30_phase_a_autopsy_and_claim_set_v2.md`
- 最新双模型审稿：`docs/experiments/2026-09-21_loopc_review_diff_table.md`
- Algorithm 1 对位：`docs/experiments/2026-09-20_algorithm1_lines_vs_impl.md`
- 大论文旧骨架（仅作素材）：`docs/experiments/2026-08-26_thesis_narrative_skeleton.md`
- 专利与论文协同路线：`docs/34_专利_小论文_大论文协同研究路线.md`
