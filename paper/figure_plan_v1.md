# 图表框架 v1（小论文基线 + 三阶段稿空槽位）

> 状态: 框架件（2026-09-24, Loop D）| 不含任何新数字；已存在图件只登记不重画；空槽位**明确为空**
> 纪律: 空槽位在对应门通过前**只允许**画坐标轴、图例与「awaiting gate」水印；任何预画数据点视为伪造。
> 回填一律单独成批、自带验收与独立复核，并回指 `paper/teacher_review_finalization_v1.md` 的 BF 槽位。

## 1 已存在且在小论文基线内的图件

| id | 文件 | 展示内容 | 数字来源 artifact | 状态 |
|---|---|---|---|---|
| FIG-SP-1 | `docs/experiments/figures_paper/fig_checkpoint_trees_v2.svg` | 两棵检查点树、leaf 与打分器分工（契约 / 裁判不混用） | `logs/graph/eval/checkpoint_discrimination_tables_v2.json` | 已存在、已入稿 |
| FIG-SP-2 | `docs/experiments/figures_paper/fig_visibility_spectrum.png` | 按缺陷家族的可见性谱与 absorbed 计数 | 同上 + `logs/graph/eval/t2_visibility_sensitivity.json` | 已存在、已入稿；柱底 `absorbed=N` 标注偏紧已记录于视觉验收件 §5，单独批修 |
| FIG-ST-1 | `paper/figures/fig_evaluate_distill_evolve_v1.svg` | 三阶段总架构与当前角色 / 边界 | `paper/research_story_v2.md` | 已存在（DOCX 以原生表格承载矢量图） |
| FIG-ST-2 | `paper/figures/fig_rule_gate_replay_v1.svg` | 七臂规则门 replay 与数据防火墙 | `research/phase2_rule_gate_replay.py` 的设计合同 | 已存在 |

## 2 三阶段稿的空槽位（门通过前不画数据）

| slot | 计划图 | 类型 | 将展示什么 | 数字来源（回填时才存在） | 前置门 | 当前 |
|---|---|---|---|---|---|---|
| FIG-D-1 | 质量—成本 Pareto（学生 vs 教师代理） | scatter | 8B 主学生在质量—成本平面上的位置与教师参照 | 未来 run 的 artifact，经 `research/paper_result_views.py` 且独立审查后 | SOURCE_GO→MODEL_GO 全过 + 独立验收（= BF-1） | 空框 |
| FIG-D-2 | 动作策略转移 / 混淆矩阵（map_to / skip / hold） | heatmap | 学生动作分布与教师动作的条件分布 | 同 FIG-D-1 | 同 BF-1 | 空框 |
| FIG-R-1 | 七臂 gain–collateral 曲线 + 独立 gate delta | line | 各臂规则状态演化与独立门增量 | `research/phase2_rule_gate_replay.py` 的独立验收输出 | Phase 2 + 功效分析 + 独立 gate-validation（= BF-2） | 空框 |
| FIG-R-2 | 规则版本化回滚曲线 | line | 固化增量在回滚事件下的质量 / 风险轨迹 | 同 FIG-R-1 | 同 BF-2 | 空框 |
| FIG-L-1 | future replay 纵向对照 | line | 获取协议哈希绑定后的跨时间 replay 对照 | 协议 + 获取时间 + 分层规则 | 协议存在即可启动（= BF-4） | 空框；允许 `LONGITUDINAL_EVIDENCE_UNAVAILABLE` |
| FIG-Q3-1 | 146 列双审动作一致性与分歧剖面 | stacked bar / matrix | R1/R2 的 `map_to / skip / hold` 计数、动作一致/分歧和裁决占比 | 将来封存的 R1/R2/ADJ 输出与 `phase1a_label_ledger_assemble.py` meta | token 状态确认 + 明确授权 + 三载体复核完成 | 空框；`NOT_RUN` |
| TAB-Q3-1 | Q3 复核一致性与目标匹配表 | table | raw action agreement、Cohen’s kappa、`map_to` target exact agreement、adjudication rate | 同 FIG-Q3-1 | 同 FIG-Q3-1 | 空表；`NOT_RUN` |

## 3 与正文的挂钩

- 小论文 §5 使用 FIG-SP-1 / FIG-SP-2；其 DOCX 视觉验收见
  `docs/experiments/2026-09-24_docx_office_visual_acceptance.md`。
- 开题 §5.1 的总体路线对应 FIG-ST-1；第 2 章 §2.12 的分类总表给出各簇与图件的对应关系。
- 大论文第 5 / 6 章为 FIG-D-* / FIG-R-* 预留图位；第 4 章为 FIG-L-1 预留图位；
  章节—图位映射以 `paper/thesis_manuscript_scaffold_v1.md` 为准，本件不重复维护章节号。

## 4 不主张

- 本件不主张任何空槽位已有数据；不主张 FIG-D-* / FIG-R-* 的形状或趋势；
- 不把 FIG-ST-2 的机制示意读作效果证据（机制级成立、功效未闭合的口径不变）。
- FIG-Q3-1 / TAB-Q3-1 只允许展示 exploratory 复核的一致性与标签形状；不得用它们支撑 Stage D、RQ2、`DATA_GO`、gate/sealed 或训练结论。
