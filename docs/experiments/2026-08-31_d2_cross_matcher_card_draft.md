---
id: TASK-20260831-D2-DRAFT
risk: medium
window: daytime（D1 收口 + autopsy 后, 按序派发; 今晚不派）
status: 草案（待 D1 底表冻结后定稿）
premises:
  - id: P1
    claim: "D1 三分类底表冻结在位（d1_mutant_validity_audit.json + SUMMARY-GUARD 收据）"
    falsify: "工件存在 + 收据复核过"
  - id: P2
    claim: "确定性匹配器三件在库: greedy（research/pso/ 匹配路径）/ Hungarian（research/paper_t6_matching_competition.py）/ 归一化变体（本卡实现, 编辑距离归一化打分）"
    falsify: "文件在位 + 归一化变体单测"
  - id: P3
    claim: "嵌入匹配器资产: GB10 本地嵌入权重可用（候选: 既有 bge 权重）; 不可用则本卡降级为三确定性件并如实记账"
    falsify: "ls 权重路径 + 加载冒烟（零模型服务调用, 本地加载）"
  - id: P4
    claim: "预算账: 确定性三件零端点; 嵌入匹配器 = 本地嵌入计算（95 表头 × 候选字段, 一次性, 无 LLM 调用）; 如需任何 :8004/:8006 调用 → 卡内硬计数器 + 白天错峰 + 超支即停报用户"
    falsify: "运行时调用计数器断言"
acceptance:
  - "≥2 种匹配器（含 1 非贪心）下重算可见性谱: 六类判别率 + 谱排序稳定性 + 全盲类型是否存续"
  - "与主匹配器谱的差异表（类型级 + 注入级）; R3 降级判据对照: 谱形显著改变 → 主张改'盲区位置匹配器相关, 谱结构匹配器无关'"
  - "嵌入匹配器端点与预算入报告（本地加载 = 零端点声明 或 调用计数）"
  - "工件落 logs/graph/eval/d2_cross_matcher_*.json + SUMMARY-GUARD 收据"
rollback: "git revert; 冻结件只读"
redlines:
  - ":8006 如需使用: 仅预注册窗口卡内 + 白天错峰 + 硬预算门 + canary 异常即停记账窗内不归因 + 窗外恢复零触碰（08-31 资源裁定五条件）"
  - "J7 端点鲁棒性窗不随本卡自动开启"
  - "判据冻结: R3 降级表述预注册在案, 执行后不溯及"
skills:
  - "graph-loop-rules（红线常备）"
  - "verify-before-done"
  - "executing-plans"
  - "systematic-debugging"
---

# 任务卡 D2（草案）: 跨匹配器验证

> 派发载体: Loop A（GB10）| 序列: D1 收口 autopsy 后 | 白天窗执行
> 判据引用: Claim Set v2 R3 降级表述（D2 为其证伪通道）+ 蓝图 C1 成功标准（设计稿引用纪律照旧）

## 1. 目标

验证可见性谱对匹配器选择的稳健性: 确定性三件（归一化 / 现有 greedy / Hungarian）+ 嵌入匹配器（端点与预算入卡）, 输出谱形对比与 R3 判据对照。

## 2. 设计要点

1. 匹配器接口统一: header → canonical field 分配 + 打分; 贪心与 Hungarian 用既有实现, 归一化变体 = 编辑距离/长度归一化打分（低成本, 本卡实现）。
2. 嵌入匹配器: 表头与候选字段嵌入相似度最大分配; 资产 = GB10 本地权重（前提 P3 证伪; 不可用 → 降级三件并记账, 不静默跳过）。
3. 谱重算: 每匹配器 × 六类 × γ 网格（主口径 γ=0.2 + 全网格排序稳定性）; 注入级差异表（哪些注入的可见性随匹配器翻转）。
4. R3 判据对照: 全盲类型（ocr_similar）是否在所有匹配器下存续; 谱排序 Kendall τ 报告。

## 3. 窗口与预算

- 确定性三件 + 嵌入本地加载: 可零端点; 如需模型服务端点, 按 P4 条件与 08-31 资源裁定。
- canary 异常即停 + 记账, 窗内不归因。

## 4. 汇报格式

照模板四项 + 派发证据; findings 先行。