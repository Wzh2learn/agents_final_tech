# 三阶段科研资产地图 v2

> 状态：当前索引 | 更新：2026-09-22 | 范围：论文相关仓内资产与已知仓外证据

## 1. 账本职责与阅读顺序

先完成 `AGENTS.md` 的规则/记忆必读，再按 `docs/research/README.md` → `paper/research_story_v2.md` → 本账本 → `docs/handoff/2026-09-22-paper-research-next-phase.md` 阅读。入口 §1 管权威冲突，叙事管故事，本账本管证据与缺口，执行计划管下一张任务卡；数字以原始工件为准，不按文档新旧投票。

`paper/teacher_review_note_v2.md` 是当前导师说明；`paper/research_story_v2.docx` 已由当前 Markdown 和同步后的三阶段表离线重生成，结构/口径测试通过，Office 视觉未验；它不覆盖 Markdown。24–48 小时方向包使用成熟评估稿 + 当前故事，不等待统一论文实验完成。

### 1.1 “有资产”与“可在本机执行”分开登记

本账本中的“可用”仅指所列代码/报告/工件可作为相应证据或复用素材，不表示本机输入齐备、服务存活或获得执行许可。全仓依赖图见 `docs/architecture/codebase_map.md`；`scripts/catalog.toml` 不覆盖根 `research/`，不能据它漏掉科研代码。

| 输入/资产 | 仓内可核验 | 依赖及本轮边界 |
|---|---|---|
| `logs/graph/eval/` 已有 JSON | 既有统计、分母、hash 与 provenance 引用 | 复算不等于重做实验或完成 Phase 1 标签审计 |
| `research/vgmc_exp1.py` 的 fewshot/记忆纯逻辑 | 合成 fix/meas fixture 与 mock 请求合同 | `load_corpus()` 需要 `data/research/drift_v0/output/`；完整新 replay 不在本地跑 |
| `research/dpo_pairs_v0.py` | 从已有 checkpoint 构造偏好的代码与现有结果 | 60 对偏好单向；不可据脚本存在宣称训练数据过门 |
| 源表、逐题输出、模型权重与训练环境 | 仅仓内引用、代码所需路径与既有报告 | 用户说明在另一台服务器，本轮未核验；不下载、搬运或重建，不据本地缺件判失败 |
| 文稿与派生器 | Markdown、SVG、临时 DOCX 的离线结构检查 | 不能代替 Office 视觉验收、导师认可或公开许可 |

本地只分析既有事实和验证代码合同；生成新论文数字的可学性实验、规则 replay、训练与终评均按 `docs/governance/2026-09-07_execution_plane_boundary.md` 在 GB10 获批执行。未来若输入仍不可核验，明确暂停对应步骤，不伪造结果；这不是本轮环境治理任务。

## 2. Stage E — 大模型流程评估

| 类型 | 资产 | 用途 | 状态 |
|---|---|---|---|
| 路线 | `docs/experiments/2026-08-29_long_horizon_eval_paper_blueprint.md` | 评估论文结构与实验问题 | 历史过程稿；只作评估素材，不再控制三阶段方向 |
| 方法 | `config/eval_checkpoint_trees.json` | 两棵检查点树定义 | 可用 |
| 方法 | `scripts/eval_checkpoint_aggregate.py` | 递归聚合实现 | 可用 |
| 方法核对 | `docs/experiments/2026-09-20_algorithm1_lines_vs_impl.md` | 算法行与实现对位 | 可用 |
| 主实验 | `logs/graph/eval/checkpoint_discrimination_tables_v2.json` | 95 表、118 注入、可见性 | 可用 |
| 对照 | `logs/graph/eval/t1_eval_baseline_comparison.json` | 端到端/扁平/层级协议 | 可用 |
| 稳健性 | `logs/graph/eval/t2_visibility_sensitivity.json` | 阈值敏感性 | 可用 |
| 匹配器 | `logs/graph/eval/d2_cross_matcher_det.json` | 跨匹配器结果 | 可用 |
| 统计 | `logs/graph/eval/d3_matched_fpr_stage_a.json` | matched-FPR bootstrap | 可用 |
| 稿件 | `paper/teacher_review_draft_v1.md` / `paper/teacher_review_draft_v1.docx` | Stage E 成熟英文子稿 | 已验收，不代表完整三阶段论文 |

## 3. Stage D — 小模型蒸馏

| 类型 | 资产 | 用途 | 状态 |
|---|---|---|---|
| 模型矩阵设计 | `docs/experiments/2026-08-18_small_model_matrix_design.md` | 4B/8B/14B/27B 与质量—成本协议 | 可用 |
| 模型矩阵结果 | `docs/experiments/2026-08-19_small_model_matrix_c1c2.md` | 14B、8B 训练前基线 | 报告可用；逐题 JSON 在 GB10 gitignored 路径 |
| 模型矩阵结果 | `docs/experiments/2026-08-21_small_model_matrix_c3.md` | 4B 训练前基线 | 报告可用；逐题 JSON 在 GB10 gitignored 路径 |
| 文献 | `docs/experiments/2026-09-20_kd_literature_candidates.md` | KD、agent distillation、多教师路线 | 18 条候选已核；venue 仍按文档边界 |
| 训练数据设计 | `docs/experiments/2026-08-28_dpo_pairs_v0_design.md` | 门控事件转偏好对 | 可用 |
| 候选事件 | `logs/graph/eval/vgmc*_checkpoint.json`（16 件） | 494 条有 gain/collateral 的 gated 事件，48 uid / 94 uid-col / 139 uid-col-target | accepted 292 / rejected 202；16 组相反标签、41 列多 target，待审计 |
| 训练数据 | `logs/graph/eval/dpo_pairs_v0.json` | 60 对、36 uid、60 uid-col；全部 skip 优于 map_to | 无 Type-B、gate_fooled=9；偏好单向，不是 DATA_GO |
| 生成器 | `research/dpo_pairs_v0.py` | 可复现偏好对生成 | 不重跑在线建议器；优先复用而非另起重复构建器 |
| 学生训练 | 尚无 | 8B 动作策略/规则候选 SFT，DPO 条件实验；4B 仅 smoke | **needs-evidence**；不得称完整过程推理蒸馏 |
| 训练后评估 | 尚无 | 四层隔离、未见缺陷家族、质量—成本与回归 | **needs-evidence**；先离线强基线再申请训练 |

结论：小模型矩阵回答“现成模型能做到什么”，蒸馏实验回答“评估筛选的教师知识能否被迁移”。两者不能混用。

## 4. Stage R — 自学习规则进化

| 类型 | 资产 | 用途 | 状态 |
|---|---|---|---|
| 原始规划 | `docs/30_科研线规划.md` | VGMC/VGRM 早期单线设计 | 历史素材，受现行口径约束 |
| 方法稿 | `docs/experiments/2026-08-29_vgrm_method_chapter_draft_v0.md` | 门控算法、命题、碰撞机制 | 可用，需按最新证据收窄 |
| 核心实现 | `research/vgmc_exp1.py` | gated/ungated 规则固化 | 可用 |
| 对抗与碰撞 | `research/vgmc_adv_judge.py`、`research/vgmc_collision_corpus.py`、`research/vgmc_collision_expand.py` | 有害建议和碰撞暴露 | 可用 |
| 主工件 | `logs/graph/eval/vgmc_exp1_results.json` | 固化率、学习曲线、holdout | 可用；主效应不强 |
| 强机制证据 | `logs/graph/eval/vgmc_adv_curve.json` | 对抗候选拒绝 | 7/7 拒绝，机制证据 |
| 碰撞证据 | `logs/graph/eval/vgmc_collision_curve.json` | 门控与无门控差异 | 有方向性差异，不能替代功效分析 |
| 基线 | `logs/graph/eval/vgmc_baseline_curve.json` | few-shot/Mem0/AWM 式对照 | 与 no-gate 不可分，保留 null |
| 学习门 | `logs/graph/eval/bandit_gate_v0_eval.json`、`logs/graph/eval/bandit_prospective_eval.json` | 阈值 bandit | 奖励无分辨力，需重设计 |

## 5. 总体路线与图

| 资产 | 角色 | 注意事项 |
|---|---|---|
| `docs/33_导师指导吸收_科研三线升级.md` | “评估 + 改进 + 自学习”原始总纲 | 受保护，只读 |
| `docs/34_专利_小论文_大论文协同研究路线.md` | 2026-08-29 的评估单线收敛与专利边界 | 论文范围已被 2026-09-22 用户校准；公开边界继续有效；受保护，只读 |
| `paper/figures/fig_evaluate_distill_evolve_v1.svg` | 三阶段 Figure 1 | 实线/虚线同时编码成熟度，不只靠颜色 |
| `paper/thesis_manuscript_scaffold_v1.md` | 大论文章节与创新点 | 已恢复蒸馏独立章节 |

## 6. 主张—证据—缺口账本

| 当前叙事 RQ | 已成立与限制 | 下一证据门 / 责任角色 |
|---|---|---|
| RQ1 / Stage E | 95 表、118 注入与可见性/协议审计；不主张层级检出率更高或跨系统普适 | 成熟评估保底稿；第二数据流/scorer 为后续条件工作 / 论文 Agent |
| RQ2 / Stage D | 仅零样本矩阵与动作事件；本节 §3 统计由原始 JSON 复算，分母/hash 见执行计划 §1.2 | Phase 1 数据四层隔离、Phase 1a 可学性、Phase 4 A1/A2 自然量及 matched 双口径；DPO 为 RQ2 条件消融 / 数据与实验 Agent |
| RQ3 / Stage R | 现有拒绝与碰撞是机制证据，净收益/长期回滚仍 needs-evidence | Phase 2 七类共享流且状态独立的门基线、Phase 5 冻结快照评测 / 规则实验 Agent |
| RQ4 / 闭环 | needs-evidence，不把 E 与 R 分别存在写成闭环有效 | Phase 5 sealed test/future replay + Phase 6 合稿门 / 实验与论文 Agent |

当前第一个任务是执行计划 §10；数据不足时扩充独立公开源表/uid、正确 map_to、hold 和双向偏好，按 uid 做功效/MDE，不复制事件。`PILOT_ONLY` 或简单规则已足够即走评估保底，详细判据只维护在执行计划。

## 7. 清理裁定

- 保留评估子稿，不复制其正文到三阶段总叙事；内部稿、评估蓝图、旧骨架和审稿记录只作历史/素材，不再竞争当前方向。
- 不把模型矩阵、DPO 偏好对或训练钩子表述为已完成蒸馏；14B 既有异常尚未归因。
- 不把 bandit 奖励无分辨力包装成学习门有效。
- 不修改 `docs/33*`、`docs/34*`；入口仅覆盖旧论文范围/排期，不覆盖专利公开限制或已执行实验真值。
- 不再新增临时路线稿/claim 矩阵；叙事更新 `research_story_v2.md`，资产更新本账本，执行更新现有 handoff。
- 历史文件不删；大规模移动、删除、改名须用户另行确认。
