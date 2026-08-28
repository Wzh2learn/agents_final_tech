# DPO 偏好对 v0 配对口径设计稿（台账 #1 样本薄缺口的首填补）

> 状态: 设计稿（口径预注册, 生成照稿机械执行） | 更新: 2026-08-28 | 依据: 2026-08-27_bandit_gate_v0_design.md §1（DPO 阶段轨迹级偏好对=0 → 需"门控救回/未救回"成对轨迹）
> 红线: 全合成语料甲方零进入; 本稿只生成对不训练; 种子预注册 20260828

## 1 目的与单位

为后续偏好学习（DPO 或奖励模型）生成首批 (prompt, chosen, rejected) 偏好对。
配对单位 = **(uid, col) 建议事件**（表 × 列粒度, 与建议流最小决策单元一致）。
prompt 上下文 = 该表表头 + 该列询问语境（建议器所见信息的可重构描述, 不含数据行——与建议器 prompt 的差异注记在案）。

## 2 来源（预注册）

- 噪声 L3（vgmc_noise_L3_checkpoint.json, 两臂 sugg_log; force 0.5 seed 20260827）
- 碰撞 C1（vgmc_collision_C1_checkpoint.json, 两臂 sugg_log; 同 force 种子 + 碰撞语料）
- **synthetic 标记利用**: force 注入的合成错误建议带 synthetic 印记（经建议流后处理）, 提供机制级硬负例（目标确知错误）

## 3 正/负例定义（预注册）

- **正例（chosen 候选）** = 门控接受的 map_to 事件（reason=gated_pass）
- **负例（rejected 候选）** 三源:
  - N1 门控拦截（reason=gated_fail）: 门判据（gain<τ 或 collateral<−ε）认定的坏映射
  - N2 合成垃圾: synthetic 事件（无论哪臂接受, 目标确知错误）
  - N3 无门控直固的 synthetic（ungated 吞下的垃圾）= N2 子集, 标臂源

## 4 配对规则（机械, 三类）

- **Type A（跨臂对, 同体制）**: 同一体制内, 同一 (uid,col) 在 gated 流被拦截（N1）且该列在 gated 流无其他接受事件 → 对 = (chosen=skip, rejected=map_to(被拦目标))。语义: 门控的"拒绝"本身是偏好信号（不映射优于错映射）。
- **Type B（跨体制对）**: 同一 (uid, col) 在 L3 与 C1 的 gated 流中一边接受目标 X、另一边拦截 → 对 = (chosen=接受侧动作, rejected=拦截侧动作)；两侧动作均为 map_to 且目标不同时才生成（同目标无信息）。注记: 跨体制 prompt 上下文不完全相同（C1 含移植列）, 标签列注明。
- **Type C（synthetic 锚定对）**: synthetic 事件单独成对——被门拦 → (chosen=skip, rejected=map_to(合成目标)); 被门放行（gated_pass 且 synthetic, "门被骗"子集）→ 翻转对 (chosen=skip, rejected=map_to(合成目标)) 并标 gate_fooled 旗（硬负例中的硬负例）。
- 去重: 同 (uid, col, chosen, rejected) 只留一条, 来源合并记入 sources 数组。

## 5 预注册预期（生成前冻结）

- Type A 量级 ≈ 两体制 gated_fail 合计（L3 26 + C1 50 ≈ 76 上下）
- Type C ⊆ (N1∪N2 的 synthetic 部分); gate_fooled 子集预期非空（L3 gated_pass 27 含合成通过）
- 覆盖率 = 参与 ≥1 对的 (uid,col) / 两来源 (uid,col) 并集, 预期 40-70%（受"同列无接受事件"约束）
- 全部对可溯源到 sugg_log 行（每对带 regime/arm/round 指针）

## 6 工件与回滚

- 产出: logs/graph/eval/dpo_pairs_v0.json（pairs + summary: 对数/by_type/覆盖率/来源分布）
- 生成器: research/dpo_pairs_v0.py（种子 20260828, 零端点, 重跑逐字节一致）
- 回滚: 工件独立, 删除即净; 不触训练基建
