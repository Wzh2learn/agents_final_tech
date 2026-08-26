# 论文资产映射表 v1（2026-08-26, 只映射不补缺口）

状态: 活跃 | 更新: 2026-08-26 | 取代/被取代: 无
口径: 论文单元 ↔ 仓库资产（脚本/工件/skill）↔ 状态 ↔ 缺口动作。甲方数据零进入论文工件（红线）。

## 评估线（论文 B 章 1 benchmark + 专利检查点树）

| 论文单元 | 仓库资产 | 状态 | 缺口动作 |
|---|---|---|---|
| 混合三层 harness 第一层（确定性检查） | scripts/run_eval.sh + m1_scenario1_regression.py + m2_eval_{deterministic,number_faithfulness,judge}.py | 数据在位（08-26 重跑 16/16 + NF 0/9 + judge 4.94-5.0） | 无 |
| 第二层: 检查点树聚合（GTA-2 Algorithm 1） | config/eval_checkpoint_trees.json + scripts/eval_checkpoint_aggregate.py + 2026-08-18_checkpoint_protocol_v0.md / 2026-08-19_eval_protocol_v1.md | 数据在位（v1 交付; F-J1 后 None 安全） | 无 |
| 判别力测试床（缺陷场景判别数据） | scripts/eval_checkpoint_discrimination.py + logs/graph/eval/checkpoint_discrimination_report.{json,md}（08-19）+ K3 注入器 95 表（49a4ec2） | 占位→部分在位: 首份判别报告在位; 95 表联跑未跑 | **错峰联跑 K3 注入样本集（列名/别名/类型/结构四类缺陷）**, 与导师口径不混同（专利 §5.3.3 注记） |
| evidence card + judge k A/B 一致性 | scripts/eval_evidence_cards.py + evidence_cards.json + judge_consistency_report.json + evaluator-calibration skill | 数据在位 | 无 |
| 第三层: 按需 agent 深挖（v1 新增, 对标 HarnessEval Route+Verify） | 设计在 2026-08-19_eval_protocol_v1.md; B4 日志/opencode 轨迹为审计源 | **缺口**: 未实现 | v1 任务卡（依赖判别力数据, §8 倒排 #2→#3） |
| 评测成本-判别力 Pareto 曲线（核心实验） | 无现成工件 | **缺口** | 三层触发子集实验设计入论文 B 实验章 |
| related work 锚点 | 2026-08-18_harnesseval_alignment.md + FORCE-Bench/GTA-2 精读（2026-08-18_hbkeyan_close_read/）+ 专利 §2 背景引用 | 数据在位（"引入范式"口径已定） | NLPCC 2026 workshop 核实仍挂起 |

## 改进线（论文章 3 路由 + 延迟治理）

| 论文单元 | 仓库资产 | 状态 | 缺口动作 |
|---|---|---|---|
| step 数主导项证据 + 减 step 菜单 | 2026-08-22_l2_sidecar_context_measurement.md(+json) / 2026-08-25_e3_step_duration_diagnosis.md / 2026-08-22_step_reduction_menu.md / 2026-08-24_t1_step_reduction_ab.md | 数据在位（T1 还原; E2 复测 steps p50=4 坐实未污染） | 组合拳（瘦身+M4）立主线, 本周冻结让路论文（08-26 圈定） |
| thinking 档位裁定矩阵（L1） | 2026-08-22_l1_matrix_runbook.md / 2026-08-23_l1_thinking_matrix.md + logs/graph/eval/l1_judge_{medium,xhigh}.json | 数据在位（off 现状生产数据 + 两腿补跑） | 解读框架 = L2 主导项结论, 已注记 |
| 小模型矩阵 Pareto（路由实验数据） | 2026-08-18_small_model_matrix_design.md / c1c2 / c3 + research/ 探针工件 | 占位: C1/C2 NO-GO, C3 复测在位, C4 待错峰 | C4 视觉准备错峰; 数据齐后路由章可用 |
| 记忆感知路由形式化（max E[Q] s.t. E[C]≤b） | docs/33 §4 清单 | **缺口**: 未实测 | 与覆盖度 c 状态变量联测（实验 2/M3） |

## 自学习线（论文 A 章 2 VGMC + 专利权利要求 10）

| 论文单元 | 仓库资产 | 状态 | 缺口动作 |
|---|---|---|---|
| schema 自学习闭环原型（命中率上升×LLM 介入衰减主图） | config/schema_suggestions.json（25+ 条门控记录）+ m1_accuracy_eval.py + 回归门禁 | 占位: 闭环在产, 学习曲线未绘 | **VGMC 实验 1 门控闭环跑批（论文 A 主图, §8 #3）** |
| 固化门形式化（ΔH≥τ_acc 且基线无退化） | docs/33 §4 + m1_scenario1_regression.py 门禁逻辑 | **缺口**: τ/ε 未测 | 实验 1 内标定 |
| 专利权利要求 10（评测驱动自学习闭环, 双锚定"确定性规则工件+回归验证门"） | 专利修订版 §3.2.8 + 映射建议闭环工程件 | 数据在位（工程实证） | 冻结等导师反馈, 不碰 |
| PSO 落点①（权重搜索, 专利 §5.3 供数） | research/pso/pso_weight_search.py + 2026-08-21_pso_weight_search_v0.md（分离度 1.2560→1.4326, 5 轮收敛, 已回填专利正文） | 数据在位 | 无 |
| PSO 落点②（最小判别题集, 专利 §5.3 供数） | research/pso/pso_question_set_search.py + pso_question_set_v0.json（08-26 首批: bank19/7mutant/B=4 最小全保持）+ 2026-08-25_pso_question_set_v0.md | 部分在位: 首批落盘 | 第二批 = 判别力套件新鲜重跑后复算（规则 D 裁定续跑） |

## 大论文四点 ↔ 资产总览

| 章 | 单元 | 资产锚点 | 状态 |
|---|---|---|---|
| 1 | 金融文档智能体分层 benchmark | 评估线全行 + 专利实施例五（§5.5 四层检查点树实例, 全抽象化） | 骨架在位, Pareto 缺 |
| 2 | VGMC 验证门控记忆固化 | 自学习线 + docs/30 §2/§4 + M0 文献（RecMem/CAIS/Q-Evolve/STATE-Bench 待精读核实） | 主图缺（实验 1） |
| 3 | 记忆感知路由与小模型分工 | 改进线小模型矩阵 + 路由形式化 | 数据半在位 |
| 4 | PSO 驱动测评优化 | PSO ①② + 专利 §3.2.6/§5.3 | ①在位②半在位 |

## Gap Top5（按启动序加权）

1. **K3 95 表判别力联跑**（评估线核心数据, 同时是 PSO ②第二批前提; 注入器就绪, 只差错峰窗）
2. **VGMC 实验 1 门控闭环跑批**（论文 A 主图, 自学习线唯一缺主图的单元）
3. **K2 v1 第三层 agent 深挖实现**（评估线差异化第二条, 设计在位代码缺）
4. **小模型矩阵 C4 + 路由 Pareto**（章 3 数据, 错峰纪律下缓）
5. **固化门 τ/ε 标定 + 学习曲线收敛条件**（章 2 形式化, 随实验 1 同批）

## 论文第一启动单元建议

**K2 v1 判别力联跑（gap 1）**: 资产全在位（v1 协议 + 注入器 95 表 + evaluator-calibration + judge 一致性先例）,
零代码缺口只差错峰窗; 产出同时喂论文 B 判别力曲线与 PSO ②第二批（§8 倒排"2 是 5 的前提"）,
一跑两得, 且与本周冻结令无冲突（纯推理实验错峰, 不开窗）。次选 = VGMC 实验 1（需 :8006 空闲窗更长, 排其后）。
