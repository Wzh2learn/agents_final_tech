# 三阶段科研资产地图 v2

> 状态：当前索引 | 更新：2026-09-22 | 范围：论文相关仓内资产与已知仓外证据

## 1. 阅读顺序

1. `paper/research_story_v2.md`：统一故事、RQ、主张边界和最小闭环。
2. `paper/teacher_review_note_v2.md`：给导师的方向校准说明。
3. 本文件：按 Evaluate–Distill–Evolve 查找素材。
4. `docs/research/README.md`：验收门和当前执行入口。

## 2. Stage E — 大模型流程评估

| 类型 | 资产 | 用途 | 状态 |
|---|---|---|---|
| 路线 | `docs/experiments/2026-08-29_long_horizon_eval_paper_blueprint.md` | 评估论文结构与实验问题 | 可用 |
| 方法 | `config/eval_checkpoint_trees.json` | 两棵检查点树定义 | 可用 |
| 方法 | `scripts/eval_checkpoint_aggregate.py` | 递归聚合实现 | 可用 |
| 方法核对 | `docs/experiments/2026-09-20_algorithm1_lines_vs_impl.md` | 算法行与实现对位 | 可用 |
| 主实验 | `logs/graph/eval/checkpoint_discrimination_tables_v2.json` | 95 表、118 注入、可见性 | 可用 |
| 对照 | `logs/graph/eval/t1_eval_baseline_comparison.json` | 端到端/扁平/层级协议 | 可用 |
| 稳健性 | `logs/graph/eval/t2_visibility_sensitivity.json` | 阈值敏感性 | 可用 |
| 匹配器 | `logs/graph/eval/d2_cross_matcher_det.json` | 跨匹配器结果 | 可用 |
| 统计 | `logs/graph/eval/d3_matched_fpr_stage_a.json` | matched-FPR bootstrap | 可用 |
| 稿件 | `paper/teacher_review_draft_v1.md/.docx` | Stage E 成熟英文子稿 | 已验收，不代表完整三阶段论文 |

## 3. Stage D — 小模型蒸馏

| 类型 | 资产 | 用途 | 状态 |
|---|---|---|---|
| 模型矩阵设计 | `docs/experiments/2026-08-18_small_model_matrix_design.md` | 4B/8B/14B/27B 与质量—成本协议 | 可用 |
| 模型矩阵结果 | `docs/experiments/2026-08-19_small_model_matrix_c1c2.md` | 14B、8B 训练前基线 | 报告可用；逐题 JSON 在 GB10 gitignored 路径 |
| 模型矩阵结果 | `docs/experiments/2026-08-21_small_model_matrix_c3.md` | 4B 训练前基线 | 报告可用；逐题 JSON 在 GB10 gitignored 路径 |
| 文献 | `docs/experiments/2026-09-20_kd_literature_candidates.md` | KD、agent distillation、多教师路线 | 18 条候选已核；venue 仍按文档边界 |
| 训练数据设计 | `docs/experiments/2026-08-28_dpo_pairs_v0_design.md` | 门控事件转偏好对 | 可用 |
| 训练数据 | `logs/graph/eval/dpo_pairs_v0.json` | 60 条偏好对，覆盖率 62.5% | 可用，但尚未训练 |
| 生成器 | `research/dpo_pairs_v0.py` | 可复现偏好对生成 | 可用 |
| 学生训练 | 尚无 | SFT/DPO/过程蒸馏 | **关键缺口** |
| 训练后评估 | 尚无 | 未见缺陷家族、质量—成本与回归 | **关键缺口** |

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

## 6. 清理裁定

- 保留评估子稿，不复制其正文到三阶段总叙事。
- 不把模型矩阵、DPO 偏好对或训练钩子表述为已完成蒸馏。
- 不把 bandit 奖励无分辨力包装成学习门有效。
- 不修改 `docs/33*`、`docs/34*`；新口径通过当前入口和决策日志覆盖。
- 不再新增按日期命名的临时路线稿；后续更新本地图和 `research_story_v2.md`。
