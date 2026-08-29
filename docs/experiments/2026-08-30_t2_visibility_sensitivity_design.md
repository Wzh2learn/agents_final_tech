# T2 缺陷可见性敏感性设计稿（Phase 2 E2.1-E2.3, 零端点）

> 状态: 预注册（执行前） | 创建: 2026-08-30 00:xx | 任务卡: docs/superpowers/plans/2026-08-29-long-horizon-evaluation-paper.md T2
> 红线: 甲方数据零进入; :5050 零重启; 生产配置零改; 专利终态件只读; 对外零发送; 冻结节点零改动
> 范围注记: 成功标准中"第二数据流方向一致"一维属 T3（阻塞等裁定）, 不在本卡; 本卡验证前两维（γ 网格 + 等价变异校正）

## 1 对应主张与判据（蓝图 §1 原样引用, 判据冻结）

对应主张 C1: 「仅看最终答案无法区分"缺陷被检出"与"被中间层静默吸收"」。

- 成功标准（预注册）: 「OCR 形近全盲与类型不均匀在 γ∈{0.3,0.5,0.7,0.9} 网格内成立、经等价变异校正后存续、第二数据流方向一致」
- 失败后降级表述（预注册）: 「第二数据流不复现: 主张收窄为"金融表头匹配层观察到结构性盲区"，不推广到任意长流程管线」

## 2 输入工件（全部既有）

| 工件 | 角色 |
|---|---|
| data/research/drift_v0/output/{injected_tables,injection_map}.json + sample_injected_tables.json（GB10） | 95 表 / 118 注入确定性语料 |
| logs/graph/eval/checkpoint_discrimination_tables_v2.json | 冻结判别基线（75/95, 逐注入 absorbed/visible/tier） |
| scripts/m1_statement_parser.py map_headers | 被测匹配层（只读导入, 零改动） |

## 3 操作化定义

### 3.1 E2.1 γ 阈值网格

- 单注入边际降幅: 对每条注入 i, 构造单注入表头（original 表头仅第 col_i 列替换为 injected_i, 其余列保持 original）, ΔH_i = H(orig) − H(单注入)（H = 命中 canonical 数 / n_canonical）。
- 判可见: visible_γ(i) ⟺ ΔH_i ≥ γ; γ ∈ {0.2, 0.3, 0.5, 0.7, 0.9}（0.2 = 冻结判据 2.0/10 的锚点, 与网格点同列报告; 网格四点为判据引用值）。
- 表级配套: detected_γ(t) ⟺ drop10_t ≥ 10γ（全注入表头, 与冻结工件同口径）。
- 注: 冻结基线（08-26 工件）为全注入并表 + drop10≥2.0 + 注入级吸收判据, 原样保留为锚, 本实验是敏感性重判, 不覆写。

### 3.2 E2.2 等价变异标记

- 定义（预注册）: 等价变异 ⟺ 注入后全表映射与原始完全一致（mapping_inj == mapping_orig, 行为等价）且注入类型属语义等价类 {alias_variant, mixed_lang, prefix_noise}（词库内真别名/混写/装饰, 语义保持）。
- 语义缺陷类 {ocr_similar（形近损坏）, date_variant（日期语义改变）, unit_suffix（单位信息添加）} 即使行为被吸收也不等价——它们是静默吸收本体, 不剔除。
- 校正: 等价变异从可见性分母剔除, 逐类型重算 visibility_rate（校正后）, 报告主结论（ocr_similar 全盲 + 类型不均匀）是否改变。
- 注: 冻结工件 locality_clean = 95/95, 故 absorbed ⟺ 映射完全一致, 定义可机械执行。

### 3.3 E2.3 强度梯度（每类 2 档）

强度轴 = 扰动与原件的匹配层距离; 构造全部确定性（由冻结注入映射派生, 无新随机源）:

| 类型 | W 档（弱化） | S 档（标准 = 冻结 v0 注入） |
|---|---|---|
| alias_variant / mixed_lang / unit_suffix / date_variant / prefix_noise | original + "(" + injected + ")"——保留原件子串的括号追加式（归一化后含原件, 预期落入包含匹配档） | 冻结 v0 注入原样 |
| ocr_similar | 不适用（S 档已处于编辑距离 1 吸收边界, 无更弱档）; 改设 S' 强化档 | S = 冻结（距离 1）; S' = 在 S 的首个替换位点邻接重复一字符（距离 2, 超出匹配器 ≤1 兜底） |

机制预测锚: 匹配器吸收区 = 精确 ∪ 归一化包含 ∪ 编辑距离≤1; W 档落在吸收区内, S'（ocr）落在区外。

## 4 预注册预测与验证门

1. 复现门 G1: S 档（冻结注入）重算 = 冻结工件逐表逐注入一致（75/95, by_type 六类计数, 误差 0）。
2. E2.1: ocr_similar 在全部 γ 点可见率 = 0（全盲稳定）; 类型不均匀（六类可见率极差）在全部 γ 点 ≥ 0.5。γ=0.9 时允许多数类型可见率大幅下降（ΔH 多为 1/n_canonical 量级）, 但排序不均匀性须存续。
3. E2.2: 预期等价变异 ≈7 条（alias 吸收 4 + prefix 吸收 3 + mixed 吸收 0, 以实算为准）; 校正后 ocr_similar 全盲不变、类型不均匀存续; 若校正月均改变主结论, 如实报告并触发判据评估。
4. E2.3: 单调性预测——可见率 W ≤ S（五类）, ocr_similar S(0%) ≤ S'（预测 S' ≥ 10/13, 机制 = 编辑距离兜底 ≤1 被击穿）; 违反单调的个例逐条列出归因, 不静默。
5. 确定性门: 全部构造同输入双跑字节一致（沿用注入器确定性契约口径）。

## 5 工件命名与复算

- 执行脚本: research/paper_t2_visibility_sensitivity.py（纯规则零端点, 运行时断言无网络调用）
- 输出工件: logs/graph/eval/t2_visibility_sensitivity.json（γ×类型矩阵 + 等价清单 + 强度梯度逐注入明细 + payload sha256）
- 复算命令: `PYTHONPATH=src python research/paper_t2_visibility_sensitivity.py`（GB10）

## 6 红线自查（设计期）

- 甲方数据零进入: TAT-QA 公开底座 + 合成注入 ✓
- 零端点: 纯规则重算 ✓
- 冻结件只读: 08-26 冻结工件为锚, 只读对账不覆写 ✓
- 判据冻结: §1 引文不溯及; T3 维度显式划界不冒充 ✓