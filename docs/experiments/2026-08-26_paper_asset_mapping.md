# 论文资产映射表 v1.1（2026-08-27 状态刷新, 只映射不补缺口）

状态: 活跃 | 更新: 2026-08-27（Gap1/2/5 closed 刷新 + 噪声体制新 Gap; 骨架 §8 漂移①闭环） | 取代/被取代: 无
口径: 论文单元 ↔ 仓库资产（脚本/工件/skill）↔ 状态 ↔ 缺口动作。甲方数据零进入论文工件（红线）。

## 评估线（论文 B 章 1 benchmark + 专利检查点树）

| 论文单元 | 仓库资产 | 状态 | 缺口动作 |
|---|---|---|---|
| 混合三层 harness 第一层（确定性检查） | scripts/run_eval.sh + m1_scenario1_regression.py + m2_eval_{deterministic,number_faithfulness,judge}.py | 数据在位（08-26 重跑 16/16 + NF 0/9 + judge 4.94-5.0） | 无 |
| 第二层: 检查点树聚合（GTA-2 Algorithm 1） | config/eval_checkpoint_trees.json + scripts/eval_checkpoint_aggregate.py + 2026-08-18_checkpoint_protocol_v0.md / 2026-08-19_eval_protocol_v1.md | 数据在位（v1 交付; F-J1 后 None 安全） | 无 |
| 判别力测试床（缺陷场景判别数据） | scripts/eval_checkpoint_discrimination.py + checkpoint_discrimination_report.{json,md}（08-19 树臂 + 08-26 新鲜重跑）+ K3 注入器 95 表（49a4ec2）+ **checkpoint_discrimination_tables_v2.json（85KB 主工件）+ 报告 v2** | **closed@34c93ab**（08-26 联跑: 表级 75/95, 注入级 96/118, 六类判别谱, OCR 形近 13/13 盲区） | 下游 = 小 B 盲锥章骨架（2026-08-27）+ C4 视觉臂（待批） |
| evidence card + judge k A/B 一致性 | scripts/eval_evidence_cards.py + evidence_cards.json + judge_consistency_report.json + evaluator-calibration skill | 数据在位 | 无 |
| 第三层: 按需 agent 深挖（v1 新增, 对标 HarnessEval Route+Verify） | 设计在 2026-08-19_eval_protocol_v1.md; B4 日志/opencode 轨迹为审计源 | **缺口**: 未实现 | v1 任务卡（依赖判别力数据, §8 倒排 #2→#3） |
| 评测成本-判别力 Pareto 曲线（核心实验） | 无现成工件 | **缺口** | 三层触发子集实验设计入论文 B 实验章 |
| related work 锚点 | 2026-08-18_harnesseval_alignment.md + FORCE-Bench/GTA-2 精读（2026-08-18_hbkeyan_close_read/）+ 专利 §2 背景引用 | 数据在位（"引入范式"口径已定） | NLPCC 2026 workshop 核实仍挂起 |

## 改进线（论文章 3 路由 + 延迟治理）

| 论文单元 | 仓库资产 | 状态 | 缺口动作 |
|---|---|---|---|
| step 数主导项证据 + 减 step 菜单 | 2026-08-22_l2_sidecar_context_measurement.md(+json) / 2026-08-25_e3_step_duration_diagnosis.md / 2026-08-22_step_reduction_menu.md / 2026-08-24_t1_step_reduction_ab.md | 数据在位（T1 还原; E2 复测 steps p50=4 坐实未污染） | 组合拳（瘦身+M4）立主线, 本周冻结让路论文（08-26 圈定） |
| thinking 档位裁定矩阵（L1） | 2026-08-22_l1_matrix_runbook.md / 2026-08-23_l1_thinking_matrix.md + l1_{medium,xhigh}_report/nf/judge.json + **2026-08-27_l1_matrix_analysis.md（分布级提纯）** | 数据在位（off 现状生产数据 + 两腿补跑 + 分析稿） | **章 3 供数在案**: 档位=质量维度路由轴（延迟中性/+21.5% thinking token/质量单调）; agent 路档位效应未测（挂起） |
| 小模型矩阵 Pareto（路由实验数据） | 2026-08-18_small_model_matrix_design.md / c1c2 / c3 + research/ 探针工件 + **2026-08-26_c4_visual_prep.md** | 占位: C1/C2 NO-GO, C3 复测在位, **C4 准备完成待探针窗批** | C4 探针窗口待批（准备文档在位, 零下载坐实） |
| 记忆感知路由形式化（max E[Q] s.t. E[C]≤b） | docs/33 §4 清单 | **缺口**: 未实测 | 与覆盖度 c 状态变量联测（实验 2/M3） |

## 自学习线（论文 A 章 2 VGMC + 专利权利要求 10）

| 论文单元 | 仓库资产 | 状态 | 缺口动作 |
|---|---|---|---|
| schema 自学习闭环原型（命中率上升×LLM 介入衰减主图） | config/schema_suggestions.json（25+ 条门控记录）+ m1_accuracy_eval.py + 回归门禁 + **research/vgmc_exp1.py + vgmc_exp1_results.json（两臂 4 轮全流水）** | **实验 1 closed@ce85736**（null result 如实入账: 可靠体制两臂终值同 0.589048, ε 维不活跃; 主图叙事改"门控价值曲线", 骨架 §5） | **噪声体制实验（台账 #12）= 决定性后续**, 设计稿 2026-08-27 夜产出, 窗口待批 |
| 固化门形式化（ΔH≥τ_acc 且基线无退化） | docs/33 §4 + m1_scenario1_regression.py 门禁逻辑 + **实验 1 网格重放（6 格）** | **closed 同批@ce85736**: τ 敏感阶 0.1→0.2, ε 维不活跃（零有害建议） | bandit 学习门（台账 #10）设计稿在案 |
| 专利权利要求 10（评测驱动自学习闭环, 双锚定"确定性规则工件+回归验证门"） | 专利修订版 §3.2.8 + 映射建议闭环工程件 | 数据在位（工程实证） | 冻结等导师反馈, 不碰 |
| PSO 落点①（权重搜索, 专利 §5.3 供数） | research/pso/pso_weight_search.py + 2026-08-21_pso_weight_search_v0.md（分离度 1.2560→1.4326, 5 轮收敛, 已回填专利正文） | 数据在位 | 无 |
| PSO 落点②（最小判别题集, 专利 §5.3 供数） | research/pso/pso_question_set_search.py（--disc/--out 参数化）+ pso_question_set_v0.json（首批）+ **pso_question_set_v0_batch2.json（第二批）** + 2026-08-25_pso_question_set_v0.md | **数据在位@34c93ab**: 第二批复算零漂移（B=4 两批稳定, keep_rate/子集/信号排名逐项一致） | 无 |

## 大论文四点 ↔ 资产总览

| 章 | 单元 | 资产锚点 | 状态 |
|---|---|---|---|
| 1 | 金融文档智能体分层 benchmark | 评估线全行 + 专利实施例五（§5.5 四层检查点树实例, 全抽象化） | 骨架在位, Pareto 缺 |
| 2 | VGMC 验证门控记忆固化 | 自学习线 + docs/30 §2/§4 + M0 文献（RecMem/CAIS/Q-Evolve/STATE-Bench 待精读核实） | 主图口径更正@骨架 v2.2: 门控价值曲线（左端点=实验 1 在位, 右端点=噪声体制 #12 待跑） |
| 3 | 记忆感知路由与小模型分工 | 改进线小模型矩阵 + 路由形式化 | 数据半在位 |
| 4 | PSO 驱动测评优化 | PSO ①② + 专利 §3.2.6/§5.3 | ①在位②半在位 |

## Gap Top5（2026-08-27 刷新）

1. ~~K3 95 表判别力联跑~~ **closed@34c93ab**（报告 v2 + 85KB 主工件在位）
2. ~~VGMC 实验 1 门控闭环跑批~~ **closed@ce85736**（null result 如实入账; 决定性后续 = 下条）
3. **噪声体制实验**（骨架台账 #12, 小 A 决定性实验: 门控价值曲线右端点）——设计稿 2026-08-27 夜产出, 窗口待批
4. **K2 v1 第三层 agent 深挖实现**（评估线差异化第二条, 设计在位代码缺）
5. **小模型矩阵 C4 探针 + 路由 Pareto**（章 3 数据; C4 准备完成待窗批）
6. ~~固化门 τ/ε 标定~~ **closed 同批@ce85736**（网格 6 格重放在案）

## 论文第一启动单元建议（2026-08-27 更新）

Top5 缺口 1/2/5 已闭（34c93ab / ce85736 同批）, **第一启动单元指向台账 #12 噪声体制实验**
（设计稿 = 2026-08-27 夜间卡 T1 产出: 2026-08-27_noise_regime_exp_design.md, 预注册完毕, 执行待错峰窗口批）。
其余排队 = C4 探针（准备在位）/ 次模消融 ρ（复用流水零额外 LLM）/ bandit 门 v0（样本审计结论在案）。
