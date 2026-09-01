# Phase C 统计预案草稿（供 Phase C 冻结, 2026-08-31）

> 状态: 草稿（P1-1, 主线程零端点起草; 冻结权在 Phase C 预注册 + 用户）| 装载: statistical-analysis / eval-harness 参照
> 修订（09-01, 专家第 2 轮意见 + 用户指令; 草案未全量冻结, 修订合法不溯及）: primary 推断改 paired table-cluster bootstrap（replicate 内重做定标）+ 检验结构三组预设对比 + D3 口径对齐（S-1..S-8, 见 D3 卡加编）。
> 依据: 用户 08-31 裁定（表级聚类口径; 118 注入不得按 iid 引 CI）+ Phase A findings（F-A5 饱和轴教训: 不为救判据造数据）

## 1. 数据结构的统计事实

- 注入嵌套于表: 118 注入落在 95 表（seed42; 其余 seed 97/90）, 每表 0-3 注入 → 注入间不独立（同表共享解析/匹配上下文）。
- 可见性判定是表级协议输出在注入上的投影 → 同表注入判定相关。
- 缺陷类型（6 类）与强度（γ 网格）是构造因子 → 按 fixed effect 处理, 不作随机抽样推断。
- 多种子（42/20260831/20260832）是注入过程的重复 → 种子间可作重复测量, 种子内不可再当独立重复。

## 2. 口径（预注册候选, Phase C 冻结）

1. **表级聚类推断**: 一切检出率/可见率的 CI 与检验以表为 cluster——cluster bootstrap（重抽表, 表内注入整组带走）或 cluster-robust SE; 禁止按 118 注入 iid 引 CI。
   **修订（09-01）**: primary 推断定为 **paired table-cluster bootstrap**（所有协议评同一组表 = 天然配对）; 每个 replicate: 按表重采样 → 保留该表全部 mutations → **重做阈值定标** → 重算各协议 → 算协议差（不得固定原 threshold, 否则定标不确定度未入推断）。
2. **类型效应**: 六类缺陷率为 fixed effect; 类型间比较 = 配对结构（同表内跨类型共享上下文）→ 用表内配对检验（McNemar 族/条件逻辑回归）, 不用独立两比例检验。
3. **多重比较**: 六类 pairwise 共 15 对 → Holm 校正（预注册主口径）; 探索性比较单独标注未校正。
4. **阈值网格**: γ∈{0.2,...,0.9} 为同一协议族在相同证据上的重复测量 → 按重复测量处理（不独立的 5 个"实验"）; 谱的结论以"排序稳定性 + 极差机制"表述（②a 冻结口径）, 不按 5 次独立检验汇报。
5. **种子**: 报告种子间变异（3 seed 范围 0.0339 在案）; 合并推断仅在种子间同质时给出（预注册同质判据 = 各种子率落入合并 CI）。
6. **检验结构（09-01 修订）**: primary = protocol × defect type 全局/异质性检验; 预设机制对比三组 = OCR vs 非 OCR / 静默吸收 vs 阈值稀释 / 等价 vs 有害（仅作 validity audit, 不作 detection 比较）; 六类两两 15 对入 supplement（Holm 合法但稀释论文）。

## 3. matched-FPR 比较方案（D3 输入, 草案）

问题: 分层 vs 扁平的检出率直接比较有阈值/灵敏度不可比风险 → 需同假阳率（matched-specificity）下的比较。
1. clean controls: 无注入表（每 seed 的未注入表; 或构造零注入对照集）上分别跑扁平与分层协议 → 各自的"误报谱"。
2. 阈值校准（09-01 修订）: 共同假阳预算 = max TPR(θ) s.t. FPR(θ) ≤ α; 不强迫插值精确相等（离散分值 + 量化地板做不到）。主 α=0.05（clean n 不足/5% 档不稳 → 按预结果分支规则切 0.10, 不得按对谁有利挑选）; 报告实际达到 FPR + CI; 附固定 α 网格 {0.05, 0.10} 敏感性。定标/评估分离 = 5 折表簇交叉拟合（表为最小 split 单元, 同表 clean 与全部 mutation 同 fold）; 定标只用 clean controls, 禁混扰动样本（tuning leakage）。
3. 比较（09-01 修订）: 匹配 FPR 档内比较注入检出率（paired table-cluster bootstrap CI + 配对检验）; **检出分母 = H∪HI = 111 非等价有害注入, E=7 排除**（三行分列: Equivalent 7 excluded / Harmful-observable / Harmful-currently-invisible）; **定位双指标同报**: conditional P(correct location|detected) + end-to-end P(detected ∧ correctly localized|harmful); **成本轴主指标** = model calls / tokens / cost per harmful detected / cost per correctly localized harmful, latency 次要。
4. 零/低端点分割: 阈值校准与确定性协议部分零端点; 若需 judge 重打分 → 白天窗 + 预算硬门 + 端点条件照 08-31 资源裁定。
5. 预注册要求: 冻结前先做零端点可行性证伪（clean controls 数量够不够支撑目标 FPR 档的估计精度）, 不够 → 降档或改报点估计 + 区间, 不硬套渐近公式。

## 4. 红线

- 判据冻结: 本预案一经 Phase C 冻结不溯及; 调整 = 更正注记 + 报用户。
- 不得为救判据造数据/换定义（F-A5 教训在案）。