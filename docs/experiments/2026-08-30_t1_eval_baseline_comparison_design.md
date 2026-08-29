# T1 评测基线对照设计稿（Phase 1 E1.1-E1.4, 零端点）

> 状态: 预注册（执行前） | 创建: 2026-08-30 00:xx | 任务卡: docs/superpowers/plans/2026-08-29-long-horizon-evaluation-paper.md T1
> 红线: 甲方数据零进入; :5050 零重启; 生产配置零改; 专利终态件只读; 对外零发送; 冻结节点零改动
> 执行范围: 本轮仅 E1.1-E1.4（用户绿灯 2026-08-30）; E1.5（Full Judge, :8004）/ E1.6（3 seeds 全量）不在本轮, 另行排窗

## 1 对应主张与判据（蓝图 §1 原样引用, 判据冻结）

对应主张 C2: 「分层检查点树可定位长流程缺陷，优于扁平端到端分数」。

- 成功标准（预注册）: 「分层评测缺陷检出以不高于 end-to-end/flat 的成本不低于其检出，且 ≥3 seeds CI 可算」
- 失败后降级表述（预注册）: 「检出率无优势: 改"分层评测以相当成本提供等效判别力并给出缺陷定位"，不主张优越」

口径注记: 本轮零端点重算覆盖成功标准中"检出/成本"两维; "≥3 seeds CI 可算"一维由表级 bootstrap CI（单种子确定性重抽样 2000 次）部分承担, 完整多种子属 E1.6, 不在本轮, 如实注记不视为本卡判据达成。

## 2 输入工件（全部既有, 零新评测）

| 工件 | 角色 |
|---|---|
| logs/graph/eval/checkpoint_discrimination_report.json | 臂 A: 9 mutant × 12 活叶 delta + root_scores + control.live_leaves |
| config/eval_checkpoint_trees.json | 专家权重与树结构（兄弟归一化, hinge, missing_score） |
| logs/graph/eval/pso_weight_search_v0.json | PSO 最优权重（GB10 在盘, 随本轮入库） |
| logs/graph/eval/checkpoint_discrimination_tables_v2.json | 臂 B: 95 表 / 118 注入判别结果（冻结基线 75/95） |
| data/research/drift_v0/{output,injection_map,sample}（GB10） | 臂 B 重算底座（确定性注入语料） |
| scripts/eval_checkpoint_aggregate.py | Algorithm 1 参考实现（聚合同构性校验） |

## 3 操作化定义

### 3.1 臂 A（检查点树 mutant 臂, 12 活叶）

叶分装配沿用 PSO v0 口径（variant=all_leaves_missing_score）: Z = control.live_leaves（12 叶全 10.0）; D = 9 mutant, 叶分 = 基线叶分 + 报告 delta, 未涉叶按树配置 missing_score 补位。聚合 = Algorithm 1（兄弟归一化自底向上）。

| 协议 | 定义 |
|---|---|
| E1.1 end-to-end only | 只用单一终局标量: 两树根分按根权重（3:3）加权均值; 检出判据 = 终局分降幅 ≥ τ=2.0; 无叶级定位信息 |
| E1.2 flat weighted | Algorithm 1 但全部内部节点权重置 1（均匀, 无层级优先）; 检出同 τ |
| E1.3 hierarchical expert | 树配置专家权重原样; 检出同 τ（= 冻结协议） |
| E1.4 hierarchical + PSO | pso_weight_search_v0.json 最优权重; 检出同 τ |

指标（每协议）: 逐 mutant 根分降幅、均值分离度、最差 mutant 分离度、检出数（降幅 ≥ τ）、定位能力（能否归因到目标叶: E1.1 无, 其余有）、成本代理（需打分的叶数: E1.1=2 根, 其余=12 叶; 模型调用全 0）。

### 3.2 臂 B（95 表头漂移臂）

底座 = drift_v0 语料经 map_headers 纯规则重算（与 k2_table_discrimination_v2.py 同流）。每表双头（original/injected）× canonical 集（原件表头自含 schema）。

| 协议 | 定义 |
|---|---|
| E1.1 end-to-end only | 只比较终局输出: 检出 ⟺ mapping_inj ≠ mapping_orig（终局映射任何变化）; 无定位 |
| E1.2 flat weighted | S = H = 命中 canonical 数 / n_canonical（逐字段均匀均值）; 检出 ⟺ ΔH ≥ 0.2（= 冻结 τ 对齐叶片量纲） |
| E1.3 hierarchical expert | parse 树实例化: doc.ok（表可解析, 恒过）/ table.regression（表头行在位, 恒过）/ field.hit_rate（H×10）; reconcile 与 throughput 在本臂 N/A, 按 missing 排除并注记; 专家权重 + hinge; 检出 ⟺ 根分降幅 ≥ 2.0 |
| E1.4 hierarchical + PSO | 不适用: PSO 权重定义在臂 A 的 11 维内部节点空间, 与臂 B 实例化树结构不同构, 不迁移; 臂 B 该行如实标 N/A 并引用臂 A PSO 结果 |

指标（每协议）: 按类型检出率（注入级 + 表级）、正常-缺陷分离度（均值 Δ 分）、最坏类型检出率、定位率（检出注入中正确归因到目标列的比例: E1.1=0, E1.2/E1.3=字段级归因）、成本（模型调用 0; 确定性检查项计数）、表级检出率 bootstrap 95% CI（2000 次重抽样, seed=20260830）。

## 4 预注册预测与验证门

1. 复现门 G1: E1.3 臂 A 重算逐 mutant root_scores 与冻结报告误差 <0.01（对账 PSO v0 同款验证门）。
2. 复现门 G2: E1.3 臂 B 表级判别 = 75/95 逐表一致（与 checkpoint_discrimination_tables_v2.json properties.discrimination 对账）。
3. 复现门 G3: E1.4 臂 A 均值分离度 = 1.4326、最差（M7）= 0.093（与 2026-08-21_pso_weight_search_v0.md §4 对账, 误差 <0.01）。
4. 探索性预测 P1（不作假设承诺, 如实报告）: 臂 A 均值分离度排序预期 PSO ≥ expert; flat 与 expert 的差距方向不预判。
5. 探索性预测 P2: 臂 B 上 E1.1 检出率 ≥ E1.2/E1.3（任何映射变化即检出, 阈值最松）但定位率 = 0; 分层协议以定位能力换取阈值纪律。
6. 判据评估: 若 E1.3 相对 E1.1/E1.2 在检出维度无优势, 触发 §1 降级表述（本卡只产证据, 表述切换在写作卡）。

## 5 工件命名与复算

- 执行脚本: research/paper_t1_eval_baselines.py（纯 stdlib + 仓内脚本导入, 零端点, 运行时断言无任何网络调用）
- 输出工件: logs/graph/eval/t1_eval_baseline_comparison.json（含全部逐 mutant/逐表中间量 + payload sha256 + 脚本路径 + 种子）
- 复算命令: `PYTHONPATH=src python research/paper_t1_eval_baselines.py`（GB10; 臂 B 底座在 GB10）
- 数字溯源: 执行记录中每个数字标注工件内 JSON 路径

## 6 红线自查（设计期）

- 甲方数据零进入: 底座 = TAT-QA 公开语料 + 合成注入 ✓
- 零端点: 纯离线重算, 脚本内断言无网络调用 ✓
- 冻结件只读: 对账工件只读不改; 新工件新文件名, 不覆写冻结基线 ✓
- 判据冻结: §1 引文执行后不溯及改写; 任何调整以更正注记覆盖 ✓