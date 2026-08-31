# D1 Autopsy 决策记录（2026-08-31, D2 开窗前置件）

> 性质: experiment-autopsy（D1 工件 285a93d 收口后主线程尸检, 零端点）| 装载: experiment-autopsy / decision-record
> 工件: logs/graph/eval/d1_mutant_validity_audit.json（payload_sha256 d7d0e0e0…, 抽验 7/7 在案）
> 纪律: 成功也要问为什么; findings 先行; 决策记录只增不改

## 0. Findings 先行

1. **HI=26 不是铁板一块**: 机制二分 = 静默吸收 15 + 阈值稀释 11（工件 hi_by_mechanism）。阈值稀释类在锚点 γ0.2 下有残余信号未过阈 → 与"结构性不可见"性质不同, 是 D3 matched-FPR 阈值校准的天然救援通道。论文必须分开表述。
2. **盲区宽于 OCR**: 类型内非等价吸收存在——alias 7 / date 5 / mixed_lang 1（按类型吸收率 14.9% / 29.4% / 5.0%）; OCR 是唯一全盲类型（0/13）, 不是唯一被吸收类型。R1 谱报告需要"类型内吸收分解"维度, 否则低估盲区广度。
3. **失明 vs 鲁棒（专家第一风险）完整答案**: 7 等价吸收 = 鲁棒（归一化, 行为不变）; 26 有害吸收 = 失明; 85 检出 = 协议正常工作。三数之和 = 118 全谱闭合。
4. **MU 机制实锤**: M7 carriers=[] + derived_label_only=[qa.numeric.number_grounding]（moved=0）——缺陷只落派生标签, item 级证据零移动。8 个 MO 突变体全部有 primary item 移动（2-16 条）。"有效突变体"的操作化定义由此成立。
5. **等价类阈值无关性**: G3 全网格零违反——等价判定（吸收 + 语义等价类）与 γ 无关, 定义可移植（D4 的 TAT-DQA 等价类定义可直接套模板）。
6. **预注册全中（P1-P6 全 true）的反思**: 85/7/26 是从冻结工件推导的——这是"推导一致性门"不是"经验预测"。未来窗口预注册须区分两类: 推导门（工件间一致性）与经验预测（真会被数据反驳的）。本条为流程教训, 非结果问题。
7. **G6 闸修复盘**: 首版自证混淆"代码在位"与"路径被调用"→ AST 作用域收敛 + 出站封死自证（改期 1 次, 纪律内）。后续零端点卡的设计稿应直接写明自证口径, 避免返工。

## 1. 决策记录（DR-*)

- **DR-1（采纳, 入 T7）**: R1 可见性谱表述精化 = 类型谱 + 类型内吸收分解 + 机制二分（静默吸收 15 / 阈值稀释 11）; "OCR 全盲"表述保留但补"非唯一吸收类型"。
- **DR-2（输入 Phase C 冻结）**: 有效突变体定义 = 缺陷须在 ≥1 承载叶移动 ≥1 条 primary item 证据（D1 九突变体验证: MO 8 全满足, M7 不满足 = canonical MU 案例, 原样保留不替代）。
- **DR-3（入 D2 卡）**: D2 验收加 per-injection 迁移矩阵——33 吸收注入（E7+HI26）× 每匹配器的状态保持/翻转, 不止报率。
- **DR-4（入未来 D4 卡）**: TAT-DQA 预注册必须自带等价类定义（套用 D1 模板: 吸收 + 设计语义等价类 + 标准字段集不变）, 不得事后补定义。
- **DR-5（输入 Phase C）**: 阈值稀释 11 例为"可救援"先验进 D3 matched-FPR 设计; 不作新主张, 统计口径以 Phase C 冻结为准。

## 2. 对 D2 的直接含义（明日开窗输入）

- 编辑距离族（贪心/归一化/Hungarian）共享打分管道 → 预测谱结构稳定（τ≥0.8, OCR 全盲存续）; 嵌入匹配器 = 新打分基, 结果不论方向都回答"盲区位置是否匹配器相关"（R3 判据通道）。
- 等价 7 在编辑距离族下预测保持吸收-等价; 翻转 = 发现（该匹配器不认同价归一化）, 逐条报告不判失败。
- 零端点自证口径直接沿用 D1（AST 作用域 + ports 自证 + 冻结件只读 sha 核对）。

## 3. 治理/环境注记

- GB10 codex 后端: 昨夜模型目录刷新错误（schema 不匹配）+ 今晨探针（PROBE_OK）无复现; rmcp 遥测退出错误无害。探针证据与 canary 快照（qa_canary PASS / overall PASS / "Loop A may continue"）入 D2 开窗前置记账。
- v4 venue 标签（ICSME/COLM）arXiv 元数据无据 → 入 Phase B DBLP 实查队列（用户 08-31 更正注记）。

## 4. 数字收据（SUMMARY-GUARD, 重读复算）

<!-- SUMMARY-GUARD
artifact: logs/graph/eval/d1_mutant_validity_audit.json
sha256: 7e2ee0eb072ab0626af1e41d4586a73e3d8ffa7642ec31171428e6f43bfde767
sha256_lf: ef1d46ed9ca1ae3832f35d2796b3a51be34c912897d68b40d73c9413d8651a2b
claims:
  payload.counts.H = 85
  payload.counts.E = 7
  payload.counts.HI = 26
  gates.all_pass = true
END-SUMMARY-GUARD -->
