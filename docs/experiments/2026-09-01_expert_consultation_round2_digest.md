# 专家咨询第 2 轮意见沉淀（增量咨询包 #1 → 回复）

> 性质: 外部专家意见蒸馏件（侧线整理 2026-09-01）| 输入 = 增量咨询包 #1（D1/D2 证据全景 + D3 草案 + D4 问题）
> 权限: 意见为建议, 裁定权在用户; 判据冻结纪律不变; 本件不改动任何已冻结文本
> 落地规则: §2-§5 每条附落点映射（§6）; 预注册参数须在看 D3/D4 结果前冻结（§7 清单）
> 原文: 全文在用户侧附件, 本件为结构化沉淀, 英文成稿句逐字保留

## 1. 核心判断（专家原意）

论文主线在 D1/D2 后**更稳了**: D2 的 τ 门失败不是 R3 的失败, 而是把 R3 从
"某个 matcher 有盲区" 推进为 "**可见性本身是 evaluator-context dependent 的**"。
关键写作纪律: **确定性打分基的变化（D2-A）与未充分定标的嵌入变化（D2-B）必须分开写**。
专家定位句: 既有工作主要研究 evaluation metric × phenomenon 的敏感性; 我们的增量 =
长流程 pipeline 中 **defect × intermediate transformation × scoring representation**
如何共同决定 visibility 与 silent absorption。

## 2. 已定决策（论文地位划分, 直接执行）

| 结果 | 论文地位 | 能说什么 |
|---|---|---|
| 贪心→匈牙利零翻转 | R3 主结果 | allocation rule 不是当前 profile variation 的来源 |
| 绝对→归一化编辑距离改变谱 | R3 主结果 | visibility 对 scoring representation 敏感 |
| τ_min=0.7333<0.8 | 必须正文报告 | 预注册"跨 matcher 排序稳定"失败, 主动写 |
| OCR 13/13 全配置不可见 | 很强的 anchor finding | 存在跨已测试配置持续的 blind family |
| 嵌入盲集 {ocr}→{ocr,prefix}→{ocr,prefix,unit} | sensitivity | 探索臂中的观察, 不升级主张 |
| 嵌入 τ=0.276/−0.298 | sensitivity | embedding scoring 可显著重塑 profile |
| "打分基越强盲区越大" | **禁止表述** | 无单调性支持 + 嵌入定标有混杂 |

R3 精化句（在冻结语义内吸收 D2 证据, 可直接入正文）:
> Defect visibility is jointly determined by mutant observability and the intermediate
> transformations through which the defect propagates, including the scoring
> representation used by the matching layer.

## 3. 可直接入论文的英文段（逐字保留）

主结果段:
> Defect visibility is not invariant to the scoring representation of the matching
> layer. Holding assignment fixed, replacing absolute edit-distance scoring with
> length-normalized scoring altered the type-level visibility profile, whereas
> switching from greedy to Hungarian assignment produced no flips. This isolates
> the observed variation to the scoring axis rather than the allocation axis.

预注册失败主动披露句:
> Accordingly, the pre-registered cross-matcher rank-stability criterion was not met
> (tau_min = 0.7333 < 0.8); we therefore do not claim that the complete visibility
> ranking is matcher-invariant.

OCR anchor 句:
> Nevertheless, OCR-similar perturbations remained invisible in all 13/13 cases across
> every tested scoring basis and threshold setting, making them the only defect family
> whose blind status persisted throughout the full configuration sweep.

D2-B 句（最后一句是防过度主张的关键）:
> An exploratory embedding-based scoring arm produced substantially different
> visibility profiles and enlarged the observed blind set in our tested configurations.
> Because positive and negative controls were not yet cleanly separated under this
> scorer, we treat this result as evidence of representation sensitivity rather than
> as evidence of monotonic blind-set expansion.

禁用句（任何场合）: "richer representations enlarge blind regions";
"semantic matching systematically produces more blindness"。

## 4. D3 matched-FPR 协议: 6 条设计约束（总体通过, 补约束后才可冻结）

1. **clean controls 定标是对的**, 不得混入扰动样本（否则 threshold 知道 positive
   分布, 再用同批比 TPR = tuning leakage）。
2. **定标与评估分离**: 5-fold cluster cross-fitting, 表为最小 split 单元; 同一张表的
   clean 版与全部 mutation 必须在同一 fold; 绝不许一张表 clean 在定标、mutation 在测试。
3. **matched-FPR 改为共同假阳预算**: 定义 max TPR(θ) s.t. FPR(θ) ≤ α, 不强迫插值
   精确相等（离散分值 + 量化地板做不到）。primary α=0.05（若 clean n 不足、5% 档
   不稳定可改 0.10, 但必须在看 D3 mutant 结果前冻结, 不得按对谁有利选）; 同时报告
   实际达到的 FPR 与 CI; 附少量固定 α 网格作敏感性。
4. **检出分母重定义**: D3 detection denominator = H∪HI = 111 个非等价有害注入;
   E=7 不算 evaluator miss（否则又把鲁棒与盲区混回一起）。表格三行分列:
   Equivalent 7 (excluded) / Harmful-observable / Harmful-currently-invisible。
5. **localization 报两个指标**: conditional P(correct location | detected) **与**
   end-to-end P(detected ∧ correctly localized | harmful)。禁止只报前者
   （20/95 检出且 20/20 定位对 → "100%" 误导, 端到端仍是 20/95）。
6. **成本指标排序**: 主 = model calls / tokens / cost per harmful detected /
   cost per correctly localized harmful; latency 降次要（易被负载/缓存/批处理污染,
   调用数与 token 机械可复算）。

统计修正（覆盖现草案）:
- primary 推断改 **paired table-cluster bootstrap**（所有协议评同组表 = 天然配对）;
  每个 bootstrap replicate: 按表重采样 → 保留该表全部 mutations → **重做 threshold
  定标** → 重算各协议 → 算协议差（不得固定原 threshold, 否则定标不确定度未入）。
- 检验结构: primary = protocol × defect type 异质性/全局检验; 预设机制对比 =
  OCR vs 非 OCR / 静默吸收 vs 阈值稀释 / 等价 vs 有害（仅作 validity audit 不作
  detection 比较）; 其余 15 对两两放 supplement（Holm 合法但稀释论文）。

## 5. D4 重设计（替代原"单个 Spearman 过线"方案）

**R4 拆分**: R4a configuration transfer = D2 已答（按预注册秩稳定判据, 部分失败）;
R4b dataset/pipeline transfer = D4 新测（冻结 evaluator 配置下, visibility 结构
跨数据流是否保存）。

**三个指标**（均在看结果前冻结）:
- Metric A 谱形状: Kendall τ_b（6 类型有 ties, 优于 Spearman）, 预注册 τ_b ≥ 0.6
  为 strong ordinal preservation 点估计门; K=6 小, 不以 τ 的 CI 作唯一生死门。
- Metric B 幅度迁移: macro type-level MAE（不按注入数加权, 防大类淹没小类）,
  预注册 MAE ≤ 0.15 为较强迁移（= minimum practically important difference,
  冻结前按各类型 n 与分值分辨率做一次功效/分辨率检查）; 报 cluster-bootstrap CI。
- Metric C blind-anchor persistence: OCR 为锚, 不要求 target 0/13（n 不同, 太脆）;
  预注册 V_OCR_target ≤ 0.20 为 near-blind 持续; 报 ΔV_OCR + CI; 另报
  source blind family 是否在 target 翻为 high-visibility（V_target > 0.50 =
  mechanism reversal, 显式报告）。

**三档 verdict**（不二元化）:
- Strong transfer: τ_b ≥ 0.6 且 MAE ≤ 0.15 且 blind anchor 保持 near-blind;
- Partial / context-dependent transfer: 部分满足（排序存值漂移 / OCR 存余类重排 /
  幅度近而秩变）——与 meta-evaluation 叙事天然契合;
- No evidence of transfer / structural shift: τ ≤ 0 / MAE 明显超 margin / 锚大幅反转。
  措辞写 "no evidence of profile transfer under the preregistered criteria",
  不写 "transfer is impossible"。

**等价类模板关键修正（直接推翻现 DR-4 措辞, 须改卡）**:
"吸收"不得进入等价定义, 否则循环（没发现→被吸收→判等价→不算没发现）,
是严重方法学攻击点。正确顺序:
- Step 1（运行被测 matcher/evaluator **之前**冻结）: 依据独立 oracle 定义
  E(m)=1 当且仅当: mutation 属预定义语义等价算子; 独立规范真值映射不变;
  下游目标语义不变。
- Step 2（之后）: 观察并记录 detected / absorbed / propagated / localized。
  **absorption 是 outcome, 不是 equivalence criterion。**
- 另: 某算子在 source 有害 ≠ target 每实例必然有害; 按 **instance-level**
  ground truth 冻结 E/H, 不按 mutation type 一刀切（与 mutation testing 的
  equivalent-mutant validity 同源）。
- 侧线注: D1 现行分类以设计语义类（算子级）+ 字段集一致性为据, 与此修正方向
  相容, 但 D4 新语料必须按 Step1/2 顺序执行; D1 分类建议按同一标准复核一遍。

**D4 双条件（不增模型调用, 预算允许强烈建议）**:
- D4-A source-frozen operating point: D3 在 source 定的 threshold 原样带过去 →
  测协议能否真正 transport（最强外部效度）;
- D4-B target-local calibration: target 上仅用 clean controls 重新定标再评 →
  测去除 base-rate/score-scale shift 后 profile 是否仍迁移。
- 解释表: A 成 B 成 = 强迁移; A 败 B 成 = 定标偏移; A 败 B 败 = 结构性偏移;
  A 成 B 败 = 异常, 优先审计。

## 6. 落点映射（谁在哪个阶段执行）

| 意见 | 落点 | 责任 |
|---|---|---|
| §2 地位划分 + §3 英文句 | T7 写作口径（入 Claim Set v2 适用注记） | 主线程, T7 |
| §4 六约束 + 统计修正 | D3 卡定稿的前置修改（冻结前） | 主线程, D3 卡 |
| §5 三指标/三档/双条件 | D4 卡重拟（替代原方案） | 主线程, D4 卡 |
| §5 等价类 Step1/2 修正 | DR-4 模板改写 + D1 分类复核 | 主线程, 决策记录更正 |
| §7 文献线（四组检索词） | Phase B 续（paper-lookup → v4 增簇/子簇） | 主线程, Phase B |
| §8 风险 1-4 | D3/D4 卡内条款 + R4 问句改写 | 主线程, 卡 + Claim Set 注记 |

## 7. 待冻结参数清单（看 D3/D4 结果前冻结, 不得事后挑）

1. D3 primary α: 0.05（默认）或 0.10（仅当 clean 定标样本明显不稳, 先看功效再定）;
2. D3 fold 结构: 5-fold table-cluster cross-fitting（表为单元）;
3. D3 检验结构: primary 全局 + 三组预设对比, 15 对入 supplement;
4. D4 τ_b 门 0.6 / MAE margin 0.15 / OCR anchor 0.20 / reversal 0.50（冻结前
   做功效与分辨率检查）;
5. D4 等价 oracle 与 instance-level E/H 标签一次性冻结;
6. D4 单窗执行, 见到 target 结果后禁止: 调 threshold / 改等价 / 改分类 / 换
   matcher / 换指标（失败 = 如实形成 context-dependence 结果, 不修到成功）。

## 8. 文献补线: 指标对表示层鲁棒性（R3 理论坐标, 非边缘）

四组检索词: ① contextual metric meta-evaluation / evaluation metric context
sensitivity / metric ranking instability across contexts; ② challenge-set
evaluation metric sensitivity / error-type sensitivity automatic evaluation
metrics / metric family phenomenon sensitivity; ③ representation sensitivity
evaluation metrics / embedding-based metric robustness / pretrained
representation choice evaluation metric / multilingual embedding evaluation
bias; ④ metric calibration under distribution shift / score calibration across
metric families / threshold calibration embedding similarity / evaluation
metric invariance / representation-induced evaluation bias / metric robustness
under scoring transformations。
锚点两篇: Contextual Metric Meta-Evaluation（arXiv 2503.19828, 已实查）;
ACES / Span-ACES（arXiv 2401.16313 同族, 已实查）。

## 9. 风险清单（专家点名）

1. **D2-B 盲集扩张可能是 calibration artifact**（当前第一风险）: 嵌入臂进正文前
   必须 matched operating point / matched false-match rate 定标; OCR 跨阈值恒盲
   受影响小, prefix/unit 扩张很可能受影响。（与侧线此前弱门控发现互证。）
2. **11 例阈值稀释是 post-D1 数据驱动子组**: 可研究, 但必须写明
   "post-D1 hypothesis, prospectively preregistered for D3", 不得伪装成
   自始预注册。
3. **D4 validation split 不得用成 development set**: 协议 + 等价 oracle +
   primary 阈值一次性冻结, 单窗执行; 失败如实写, 不修到成功（恰与 Contextual
   Meta-Evaluation 思想契合）。
4. **R4 问句改写**: 从 "Does the profile transfer?" 改为 "Which components of a
   visibility profile transfer across evaluation contexts, and which are
   context-specific?"——D2 已证 configuration transfer 不天然成立。

## 10. 金句候选（专家视为最有潜力升级 AAAI 主贡献的结论, 待 D3/D4 证据支持）

> Defect visibility is structured, but not universal: some blind mechanisms
> persist while the surrounding profile is evaluation-context dependent.

（即使 D4 失败, 论文仍得完整结果: 跨配置持续的 OCR anchor + profile 其余部分
显著受打分基与数据语境影响——这不是坏结果, 可能比"六类排序都稳定"更有研究价值。）

## 11. F5 补发核对记录（2026-09-04, Loop D）

用户 F5 补发（本沉淀件截断部分, 原文照发: §8 检索词 ③④ + §9 风险清单）与登记版（commit 790f67f, 196 行）逐条核对:

1. §8 ③④ 与 §9 四风险与登记版逐句一致; 用户原文编号 6-9 = 本件 §9 的 1-4（四风险一一对应; 编号系用户原文续编, 前段推定为 §8 四组检索词与两锚点, 本件原有编号不改, 以免破坏 D3 加编 S-6 等既有引用）。
2. 本件内三处编辑性互证括注非专家原文, 登记保留: 风险 1 尾「（与侧线此前弱门控发现互证。）」/ 风险 3 尾「（恰与 Contextual Meta-Evaluation 思想契合）」/ 风险 4 尾「——D2 已证 configuration transfer 不天然成立」。
3. 更正记账: THREADS #EXPERT-R2-ARRIVAL FINDING「沉淀件截断（164 行, §8 缺 ③④, §9 缺失）」不成立——登记版 196 行完整, 截断声明撤销销账（声明 ≠ 事实家族; 文件级核对由主线程完成）。
4. 风险 6-9 覆盖映射（均已在案）: 6(=1) → D3 阶段 B matched operating point + 加编 2 judge 防泄漏条款; 7(=2) → D3 加编 S-6 出身注记; 8(=3) → D4 卡一次性冻结条款（协议+等价 oracle+primary 阈值, 单窗执行, 失败如实写）; 9(=4) → Claim Set v2 R4 拆分注记。
