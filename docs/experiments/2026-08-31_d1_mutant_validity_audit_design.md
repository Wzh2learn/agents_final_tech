# D1 突变体有效性审计 · 预注册设计稿（零端点）

> 卡号: TASK-20260831-01 | 风险: 低（零端点, 冻结工件只读）| 执行者: Loop A（GB10）; 主线程拟卡与抽验
> 依据: Paper Claim Set v2（R3 可见性边界机制 + 有效突变体定义缺口）+ 侧线移交资产（e2_2_equivalence_correction 存量）+ 用户 08-31 裁定（三分类升格; M7 原样保留不替代）

## 1. 判据引用（蓝图 §1 原样, 判据冻结不溯及）

蓝图 C1 主张: 「仅看最终答案无法区分"缺陷被检出"与"被中间层静默吸收"」。
成功标准（原样）: 「OCR 形近全盲与类型不均匀在 γ∈{0.3,0.5,0.7,0.9} 网格内成立、经等价变异校正后存续、第二数据流方向一致」。
降级表述（原样）: 「第二数据流不复现: 主张收窄为"金融表头匹配层观察到结构性盲区"，不推广到任意长流程管线」。
本设计稿承担 C1 证据链的"注入有效性/可观测性"基础层: 118 注入 + 9 检查点突变体的三分类审计, 为 D2/D3/D4 提供"哪些扰动是有效缺陷"的冻结底表。

## 2. 定义（三分类, 冻结）

对 118 表头漂移注入, 每注入恰好一类:
- **H 有害-可见（harmful_visible）**: 协议在锚点阈值 γ=0.2 检出该注入（t2 工件可见性判定）。
- **E 等价（equivalent）**: 被吸收 且 类型 ∈ {alias_variant, mixed_lang, prefix_noise} 且 映射标准字段集与原表一致（= T2 冻结定义, e2_2_equivalence_correction; 语义 = 吸收后标准字段集不变, 系统行为无实质变化 → 鲁棒, 非盲区）。
- **HI 有害-不可见（harmful_invisible）**: 被吸收且不满足 E（缺陷按设计意图成立——注入破坏语义而协议未察觉 → 盲区实例）。

对 9 检查点突变体, 每突变体恰好一类:
- **MO 可观测-有害（observable_harmful）**: 缺陷在 item 级证据层有承载字段（契约叶可读或 judge 叶可见证据片段）, 判别协议原则上可检出。
- **MU 不可观测（unobservable）**: 缺陷只落在预聚合量, item 级证据无承载 → 对 item 级判分结构性不可见。

## 3. 预注册预测（冻结, 执行后不溯及）

- P1（等价集复现）: D1 从原始注入映射独立重推的等价集 == T2 冻结 equivalent_list（7 uid: alias 4 + prefix_noise 3, mixed_lang 0）。集合差 ≠ ∅ → BLOCKED 报主线程, 不静默重分类。
- P2（γ=0.2 三分类计数）: H=85 / E=7 / HI=26, 总和 118。（推导: t2 corrected visibility γ0.2 逐类可见 36/12/19/0/13/5=85; 吸收 33; 33−7=26。）
- P3（等价 ⇒ 全网格不可见）: 7 个等价注入在全部 γ 网格 {0.2,0.3,0.5,0.7,0.9} 均不可见（吸收 ⇒ 映射回原字段 ⇒ 无失配信号）。任一 γ 可见 → 矛盾上报（不静默处置）。
- P4（突变体分类）: MU = {M7_nf_fail_3}（1 个）; MO = 其余 8 个。每个 MO 必须给出 item 级证据承载字段（证据路径列）; 无法给出 → 该突变体改判并逐条说明（不允许批量静默改判）。
- P5（OCR 有害论证数据）: 13 个 ocr_similar 注入全部 ∈ HI; 工件附 ≥3 条示例三元组（original header / injected header / 映射目标不变）供论证骨架引用。
- P6（零端点自证）: ports_touched = [], model_calls = 0, 预算计数器恒 0。

## 4. 动作序（Loop A）

0. 前提一分钟证伪（见任务卡 P1-P4）+ 冻结工件在位与摘要核对。
1. 读原始件: data/research/drift_v0/output/injection_map.json + injected_tables.json（冻结只读）+ logs/graph/eval/t2_visibility_sensitivity.json + checkpoint_discrimination_report.json + W2 工件（突变体证据路径）。
2. 实现 scripts/graph/../research/paper_d1_mutant_validity_audit.py: 从原始注入映射 + 协议判定独立重推每注入的 visible/absorbed/keyset 状态（不复用 t2 的聚合计数, 只允许用其做对账门）, 按 §2 规则分类; 突变体按 §2 证据路径规则分类。
3. 门: G1 等价集 == T2 冻结 7 uid（P1）; G2 γ0.2 计数 85/7/26（P2）; G3 等价全网格不可见（P3）; G4 突变体分类 == 预注册 + 证据路径全在（P4）; G5 OCR 13 全 HI + 示例三元组在位（P5）; G6 零端点自证（P6）; G7 digest_self_consistency（工件回读复算, W2 配方）。
4. 工件: logs/graph/eval/d1_mutant_validity_audit.json（payload: 118 注入逐条三分类表 + 9 突变体分类表 + 计数 + 门 + prereg_predicates + inputs_sha256 + OCR 示例三元组 + M7 保留声明）+ 报告 docs/experiments/2026-08-31_d1_audit_report.md（含 SUMMARY-GUARD 收据, 用 scripts/graph/hooks/summary_recompute_guard.py gen 生成）。
5. commit（逐路径 add, 禁 git add -A / amend）+ 汇报。

## 5. OCR 形近为何按设计口径属有害（论证骨架, 供报告引用）

1. 设计意图: ocr_similar 注入模拟 OCR 误读——表头文本被形近串替换, 语义身份被破坏（注入头 ≠ 原头, 字面不同）。
2. 吸收行为: 文本匹配层在编辑距离容差内把受损表头映射回原标准字段 → 下游一切如常, 损害无任何信号 → 不可见（13/13 全盲, t2 工件）。
3. 与等价类的边界: 等价类（alias/mixed_lang/prefix_noise 中被吸收者）的注入变体按设计是同一概念的合法写法——吸收 = 归一化, 标准字段集与系统行为不变 → 鲁棒; ocr_similar 的注入变体不是合法写法而是误读产物, 吸收 = 把破坏静默合法化 → 有害。判据 = 设计意图（该类型被注入就是为了制造应当被察觉的破坏）, 已在设计稿冻结, 重分类须用户裁定。
4. 专家风险（失明 vs 鲁棒）的答案: 等价吸收 = 鲁棒（7 例）; OCR 吸收 = 有害且不可见（13 例）; 其余吸收 = 有害性待类型化讨论（HI 兜底 + 工件标注类型明细）。

## 6. 红线与纪律

- 零端点（本卡任何步骤不建立任何模型调用连接）; 冻结工件只读; M7 原始数据原样保留, 零重设计替代（J2 附加条件）; 甲方标识零进入; 判据冻结不溯及; 段闸失败改期 ≤2 禁静默跳过。