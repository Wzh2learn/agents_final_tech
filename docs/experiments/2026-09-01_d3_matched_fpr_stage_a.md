---
status: 阶段 A 交付（零端点）
date: 2026-09-01
card: docs/experiments/2026-09-01_d3_matched_specificity_card.md
card_id: TASK-20260901-D3
artifact: logs/graph/eval/d3_matched_fpr_stage_a.json
script: research/paper_d3_matched_fpr_stage_a.py
phase: A_zero_endpoint
endpoint_calls: 0
---

# D3 阶段 A：matched-FPR 公平比较 + 嵌入定标诊断 + 阈值稀释救援

> 派发: Loop A 重派（首次派发 22:4x 中止 = 改期 #1, 中间产物已清除, 工件谱系单一）
> 执行窗口: 2026-09-01 23:5x → 09-02 00:00（跨零点, 如实记）; 计时 33.6s
> 口径: 卡原文 E-1..E-4 + **加编 S-1..S-8**（S-5 覆盖原 E-2 措辞）; 统计引 Phase C 草案 §2/§3
> 零端点自证: `ports_touched=[]` / `model_calls=0` / socket 拦截 0 次 / 冻结件 sha 前后相等
> （A1 本地 bge-m3 CPU 推理属自证口径, 非网络端点, D2-B 先例; 护栏在模型装载之前安装）

## 0 一页结论

四条结论全部由冻结工件**确定性映射**得出, 无事后解释:

1. **无可定标空间 → 卡 §4 pivot 已执行**。对比型协议分数在 2382 张可用 clean 表上**恒为 0**
   （未注入表按定义无差）⇒ `FPR(θ)=0 ∀θ>0` 两协议同时成立; 两条绝对通道实测亦不可定标
   （Ch-1 生产 schema 覆盖恒 0 = 域不相交; Ch-2 自身撞车率 AUC=0.248 **反判别**）。
   故按卡面 pivot 报「零误报观测 + 检出率原始比较 + 效度注记」, **不硬造阈值**。
2. **匹配假阳率下两协议检出率差 = 0, 且是恒等而非"未检出差异"**。prune 后 `parse` 树只有
   一个随输入变化的叶子 ⇒ 层位降幅 ≡ (3/8)·扁平 drop10, 是严格正仿射像 ⇒ 两协议共用同一条
   ROC。实测: 秩相关 1.0、斜率最大偏离 4×10⁻⁸（1e-6 量化抖动）、2000 次**逐 replicate 重定标**
   的表簇 bootstrap 中非零差 replicate 数 = 0, 差 CI = [0, 0]。
   ⇒ **W2 的 0.7895 vs 0.2105 差距 100% 来自阈值摆放（ΔH ≥ 0.2 vs ≥ 0.5333）, 不是协议判别力差异。**

> [09-04 更正注记 | 用户裁定, 只增不改, 不溯及]: 上节散文与本节所引工件结论「斜率最大偏离 4×10⁻⁸」系误誊——以结构字段 `slope_max_abs_deviation_from_0.375 = 9e-08` 为准（= 斜率偏离集 {9e-8, 7e-8, 0, 4e-8} 的 max; 4e-8 仅为单点 0.37500004 的偏离）。误差源 = research/paper_d3_matched_fpr_stage_a.py:1228 散文模板; 工件 logs/graph/eval/d3_matched_fpr_stage_a.json 冻结, 零回改; 台账见 THREADS #D3-ARTIFACT-PROSE-CONTRADICTION-NOTE。
3. **嵌入臂定标诊断 = E-1 态 (b) → 引用方式 = 降为敏感性分析**。且**同串对污染假设不成立、方向
   相反**: 剔除 74 条 cos≡1.0 的 `standard==synonym` 对后 p05 由 0.5439 **降至** 0.5323, margin
   由 −0.13278 恶化至 −0.14433; 上移 p10/p15 可收回 −0.10640/−0.08192（改善但始终不过零）。
   弱门控成因是短表头域正负控真实重叠, 不是自配对污染。
4. **11 例阈值稀释在零端点下全部可救援（并集 11/11）**: θ 再定标 5 例 + 表级聚合 8 例（重叠 2）。
   嵌入臂的「8 例 HI→E」**不是救援**——那 8 例在嵌入件下 marginal_dH 全为 0.0, 变的是等价类标签
   （把有害改判为无害）, 属标签损失; 与 (3) 的 (b) 判定一致。

**元结论（给 Loop D）**: 本语料 + 本冻结树无法区分扁平与分层。要产生真实协议差异, 层位树需要
**第二个随输入变化的叶子**; `parse.reconcile` 型恒等式证据可在 TAT-DQA 数值列上确定性计算
（零端点）——已登记 `memory/THREADS.md`, 本窗不动冻结树。

## 1 前提证伪（P1–P5）

| 前提 | 结果 | 关键读数 |
|---|---|---|
| P1 clean controls 可枚举 | ✅ | 宇宙 2479 表 − 注入 95 表 = n_clean **2384**; 可用 **2382**（2 张无可用 canonical）; E-2 落 **top 分支**（两档都做） |
| P2 两协议可自冻结工件复现 | ✅ | 脚本可导入 + G-1 推导门全 true（含从**本窗重算分数**复现 W2 seed42 的 85/13/75/20） |
| P3 D2 嵌入定标块在位 | ✅ | 阈值 0.5439 / margin −0.13278 / 正控 286（同串对 **74** 自 schema 复算一致） |
| P4 阶段 A 零端点 | ✅ | 见 §7 自证四件套 |
| P5 统计口径依据在案 | ✅ | `docs/experiments/2026-08-31_phase_c_stats_plan_draft.md` §2/§3 在位（09-01 修订版） |

## 2 G-1 冻结输入复现（推导门, 失配即停报）

全部 true, 逐项: `d1_counts` 85/7/26/118/95 · `d1_hi_by_mechanism` 15/11 ·
`d1_secondary_counts`（anchor 85 / absorbed_strict 22 / undetected 33 / absorbed∧detected 0 /
keyset_identical 19）· `d2a_flips_0` + `d2a_tau_b_min`{1.0, 0.733333, 1.0}（τ 门 0.8 未过 = D2 判 b,
本窗只复现不重判）· `d2b_dilution_mech`{greedy_emb 31/7, hung_emb 29/4} ·
`d2b_calibration`{0.5439, −0.13278, 286, 286} · `w2_seed42_counts`{E1.2 75/0.7895, E1.3 20/0.2105,
E1.1 95, inj 0.7203/0.1102} · `affine_slope_0.375` ·
**`frozen_counts_reproduced_from_recomputed_scores`**: 本窗独立重算的两协议分数在冻结锚下给出
注入级 85 / 13、表级 75 / 20, 与 W2 冻结工件逐字相等 ⇒ 口径未漂移。

A1 另有独立自证: 本地重编码的**正/负控分布与 D2-B 冻结件逐值相等**（<1e-6）, 且 p05 重算
= 0.5439 = 存储阈值 ⇒ 后续「剔除同串对」是在同一口径上做差, 不是换模型。

## 3 A1 嵌入定标诊断（E-1 三态）

正控 286 = schema (standard, synonym) 对, 其中 74 条 `standard==synonym`（占 25.87%, cos≡1.0 全在
上沿）; 负控 286 跨字段对（`NEG_SAMPLE_MOD=7` 确定性抽样, 不引入 RNG）。剔除同串对（n=212）重定标:

| 候选分位 | 阈值 | margin(p_q pos − p95 neg) | 负控 p75<阈值 | margin>0 | 负控越阈率 | 正控留存率 |
|---|---|---|---|---|---|---|
| p05（原规则） | 0.5323 | −0.144333 | ✗ | ✗ | 0.3776 | 0.9481 |
| p10 | 0.5703 | −0.106396 | ✓ | ✗ | 0.2063 | 0.8962 |
| p15 | 0.5947 | −0.081916 | ✓ | ✗ | 0.1259 | 0.8491 |

冻结参照 = 阈值 0.5439 / margin −0.13278 / 负控 p75 0.556794。
E-1 三态映射: (a) 需 ∃q 使 margin>0 **且** 负控 p75<阈值 → 不成立; margin 较冻结值有改善
（最优 −0.081916 > −0.13278）→ 落 **(b)** ⇒ `embedding_citation_decision = 降为敏感性分析`。

## 4 A2 clean controls 与 FPR 定标表

**枚举（结构事实, 与结果值无关）**: 2479 / 95 / 2384 / 可用 2382 / 无 canonical 2。
**clean 面板命中率**: distinct = {1.0}, 2382/2382 全等于 1 ⇒ 自证 canonical 由表头自身导出,
未注入表无差可测 ⇒ 对比型分数支撑集 = {0.0}, 非零观测数 **0（两协议相同）**。

**定标表（加编 S-5: θ 在各协议自身分数支撑上取 max TPR s.t. FPR ≤ α, 不插值）**:

| 层级 | 有害分母 | α | θ*(扁平) | θ*(层位) | 折算 ΔH 门 | 实际 FPR | TPR 扁平 | TPR 层位 | 差 |
|---|---|---|---|---|---|---|---|---|---|
| 注入级（主, S-2） | 111 | 0.05 | 1.428571 | 0.535714 | 两协议均 0.142857 | 0/2382 | 0.810811 | 0.810811 | **0** |
| 注入级 | 111 | 0.10 | 1.428571 | 0.535714 | 同上 | 0/2382 | 0.810811 | 0.810811 | **0** |
| 表级（次） | 88 | 0.05/0.10 | 1.666667 | 0.625 | 均 0.166667 | 0/2382 | 0.886364 | 0.886364 | **0** |

两档 α 选出同一工作点 —— 假阳预算在此通道**不构成约束**（FPR≡0）, 故 S-5 的自动降档规则不会被
触发; 这是结构事实, 非挑选结果。零误报观测 = 0/2382, 精确 CI [0, **0.001547**]。

**两条绝对通道（观察记录, 不新增判据）**: Ch-1 生产 schema 绝对覆盖在全部 2476 张可用表上恒 0
（TAT-DQA 英文表头 × 对账单中文字段 schema 域不相交）⇒ AUC 0.5 无信号; Ch-2 自身 canonical 未认领率
clean 上确有谱（非零率 0.863, 支撑 0..0.83）但有害表 AUC = **0.248411 < 0.5** 方向相反（注入把重复列
改互异列, 反而降低未认领数）⇒ 作检测统计量不成立。

**5 折表簇交叉拟合（加编 S-1/S-8 ②, 无 RNG: sorted(uid) index % 5; clean 表与注入表 uid 天然不相交）**:

| fold | 定标 clean | 评估表 | 评估有害注入 | θ*(扁平) | TPR 扁平 | TPR 层位 | 差 |
|---|---|---|---|---|---|---|---|
| 0 | 1899 | 12 | 14 | 1.666667 | 0.714286 | 0.714286 | 0 |
| 1 | 1907 | 19 | 24 | 1.666667 | 0.916667 | 0.916667 | 0 |
| 2 | 1910 | 21 | 29 | 1.428571 | 0.793103 | 0.793103 | 0 |
| 3 | 1904 | 15 | 20 | 2.0 | 0.8 | 0.8 | 0 |
| 4 | 1908 | 21 | 24 | 1.666667 | 0.791667 | 0.791667 | 0 |

θ* 逐折不同 ⇒ 定标确实**每折重做**（非固定阈值）; 五折差全为 0, 与 §0 结论 2 一致。

**效度注记（pivot 强制附带）**: 零误报是**构造性**结论而非测量力结论。真实漂移监控的参照物是
上一期表头, clean 面板会出现非零差（换表头/加列/改序）, 那是本语料没有的通道 —— 故此读数
**不可外推为"生产假阳率 = 0"**。要使其可测需要 (i) 同期真实未注入面板, 或 (ii) 与客户 schema
同域的 clean 语料（启用 Ch-1）, 或 (iii) 层位树补第二变化叶。

## 5 A3 阈值稀释救援通道（E-4 + 加编 S-6）

子组出身如实记: **post-D1 hypothesis, prospectively preregistered for D3**（非自始预注册）。
11 例逐例（uid 只留 8 位别名, 零甲方标识）:

| uid_alias | col | type | 单注入 drop10 | 表级合并 drop10 | θ 再定标 | 表级聚合 | 嵌入件 | 机制 |
|---|---|---|---|---|---|---|---|---|
| 24ff90f9 | 2 | alias_variant | 0.0 | 2.5 | ✗ | ✓ | flip→E | 表级聚合（被同表注入摊薄） |
| 24ff90f9 | 4 | alias_variant | 0.0 | 2.5 | ✗ | ✓ | flip→E | 表级聚合 |
| 32cfcadb | 2 | alias_variant | 0.0 | 3.333333 | ✗ | ✓ | flip→E | 表级聚合 |
| 32cfcadb | 4 | alias_variant | 0.0 | 3.333333 | ✗ | ✓ | flip→E | 表级聚合 |
| 567a03c7 | 0 | date_variant | 1.428571 | 2.857143 | ✓ | ✓ | keep→HI | 两通道皆可 |
| 567a03c7 | 2 | date_variant | 1.428571 | 2.857143 | ✓ | ✓ | keep→HI | 两通道皆可 |
| 68b8d514 | 5 | date_variant | 1.666667 | 1.666667 | ✓ | ✗ | keep→HI | θ 再定标（本为正, 低于冻结锚 0.2） |
| 97176853 | 2 | alias_variant | 0.0 | 3.333333 | ✗ | ✓ | flip→E | 表级聚合 |
| 97176853 | 4 | alias_variant | 0.0 | 3.333333 | ✗ | ✓ | flip→E | 表级聚合 |
| e11338f6 | 4 | alias_variant | 1.666667 | 1.666667 | ✓ | ✗ | flip→E | θ 再定标 |
| ea031e89 | 0 | mixed_lang | 1.666667 | 1.666667 | ✓ | ✗ | flip→E | θ 再定标 |

θ 再定标 **5**（最小正分数 1.428571）· 表级聚合 **8** · 双通道重叠 **2** · **并集 11/11** ·
仍未救援 **0**。表级聚合只 flag 表**不归位列**（`localization_attributable=false` 的 6 例）——
救援收益与定位成本同报, 不只报有利面。
D2-B 先验「嵌入基下 8 例 HI(dilution)→E」逐例复核**为真**, 但语义是标签损失不是检出（见 §0 结论 4）。

## 6 A4 matched-FPR 比较（确定性部分）

**分母（加编 S-2 三行分列）**: Equivalent 7 = excluded（不算 evaluator miss）·
Harmful-observable（分数>0）**90 / 111 = 0.810811** · Harmful-currently-invisible（分数=0）
**21 / 111 = 0.189189**（absorption_silent 15 + threshold_dilution 6）。

**匹配工作点（α=0.05, 注入级）**: θ*=1.428571（ΔH ≥ 0.142857）· 实际 FPR 0/2382
CI [0, 0.001547] · TPR 扁平 = TPR 层位 = 90/111 = 0.810811, 精确二项 CI [0.725461, 0.878907]。

**协议差**: 点估计 **0.0**; paired table-cluster bootstrap（88 簇, N=2000, seed 20260830,
**每 replicate 重做定标**）→ 差均值 0.0, 差 CI [0, 0], 非零 replicate **0/2000**。
恒等性证据: 斜率集 {0.37499991…0.37500004}（代数严格值 3/8）· Spearman ρ = 1.0 ·
118/118 例零-非零指示一致。⇒ E-3 如实报 **null**（不造数据救轴, F-A5 教训）。

**对照: 冻结阈值轴（仅作背景, 非匹配比较）** —— 扁平 ΔH≥0.2 → 85/111 = 0.765766;
层位 ΔH≥0.53333 → 13/111 = 0.117117; 差 0.648649, bootstrap CI [0.536364, 0.756763]
（2000/2000 非零）。此差异**全部来自阈值摆放**; 表级同口径 75 vs 20 已由 G-1 从本窗重算分数复现。

**定位双指标（加编 S-3 同报, 不单报条件式）**:

| 工作点 | 检出 | P(correct loc \| detected) containment | P(exact \| detected) | end-to-end | end-to-end exact | 平均归位列数 |
|---|---|---|---|---|---|---|
| θ*（匹配, α=0.05） | 90 | 1.0 | 1.0 | **0.810811** | 0.810811 | 1.0 |
| 冻结扁平锚 0.2 | 85 | 1.0 | 1.0 | 0.765766 | 0.765766 | 1.0 |
| 冻结层位锚 0.5333 | 13 | 1.0 | 1.0 | 0.117117 | 0.117117 | 1.0 |

口径坦白: 单注入扰动下映射变化必然锚在被扰列, containment 近乎恒 1（信息量低）; 本语料 exact
亦恒 1 且平均归位列数 1.0 ⇒ **零误归位** ⇒ 定位轴在此通道无判别信息, 差异全在检出轴。
两协议定位集相同（同一证据叶）, 层位无额外定位能力。

**成本轴（加编 S-4, latency 按卡降为次要, 本窗不报）**: 两臂 model calls **0** / tokens **0** ⇒
cost per harmful detected = 0, cost per correctly localized harmful = 0。规则算力:
`map_headers` 7549 次（整窗累计, 两臂共用同一批结果）, 层位额外 `aggregate` 4764 次纯算术。
⇒ 成本轴在阶段 A 同样无法区分两协议, 真分岔在阶段 B judge 臂。

**检验结构（加编 S-7）**: primary protocol×type 全局 = 统计量恒 0（**degenerate_identically_zero**,
6 类型无变异可分）; 三组预设对比在匹配轴上两臂计数相同 ——
c1 OCR 13 例: 扁平 0 / 层位 0（**全盲, 与 D1 一致**）vs 非 OCR 98 例: 90/90;
c2 静默吸收 15 例: 0/0 vs 阈值稀释 11 例: 5/5;
c3 等价 7 例: 0/0 vs 有害 111 例: 90/90 ⇒ **匹配工作点未把已知等价变异误判为漂移**（轴效度旁证）。
类型两两 15 对在匹配轴同为恒 0, 不入正文（`type_level_rates` 已全量入工件）。

## 7 门禁与红线自查

- **G-1 冻结输入复现**: ✅ 全 true（§2）
- **G-2 零端点自证（阶段 A）**: ✅ `ports_touched=[]` · `model_calls=0` · socket 拦截尝试 0 次 ·
  AST 作用域检索本窗脚本零使用命中（1 处散文中提及 `:8004` 属路由说明, 单列 `prose_port_mentions_not_usage`,
  不计为使用）· 9 件冻结输入 sha 前后相等（D1 / D2-A / D2-B / W2-E1.6 / drift 三件 / 树 / schema）
- **G-3 端点窗条件**: N/A（阶段 A 不开端点窗）
- 判据冻结: R1–R4 / D1–D2 / W2 旧判据**零改动**; Ch-1/Ch-2 为观察记录, 不落新判据;
  冻结树未动（第二叶只登记 THREADS）
- 甲方标识扫描: client token / id token 命中 **0**（token 表 verbatim 复用 D1 冻结件）
- git 纪律: 逐路径 add · 禁 `-A` · 禁 amend · J7 不开 · TAT-DQA 零触碰 · 对外零发送
- 段间不互锁: `--sections` 可单选（唯一硬依赖 = a4 需 a2 工作点）; 本次为四段全跑
- `all_pass = true`, `digest_self_consistency` 复算 = true, 计时 33.6s

**执行期发现并修复的实现缺陷（如实入账, 不改判据）**:
① 归位规则初版用「认领文本增删」判列, 字段整体掉线时被删文本已不在扰动后表头中 ⇒ 90 例全判误归位;
   改为位置级归位（canonical 认领变化 → 两次观测各自占用的列位置）。
② θ 选择循环把 raw TPR 与**已舍入**的 best TPR 比较, 23/29=0.7931034 舍入后 raw>rounded+1e-12 成立,
   使该折错误落到 1e-12 哨兵并显示 θ=0; 改为原值对原值比较。两处修复均只影响实现,
   冻结数字复现门（G-1）在修复前后皆 true。

## 8 阶段 B（另行派发, 端点窗白天错峰）需求清单

阶段 B 卡内**不新增判据**, 只执行本清单; `:8004` 主; 预算 ≤200 调用硬门（计数器入工件）;
3 例 canary 快照先行, 异常即停 + 记账; 完成后 `:8006` 恢复零触碰态。

| id | 内容 | 单元 | n | 调用/单元 | 为何确定性不足 |
|---|---|---|---|---|---|
| J-N1 | 21 例零信号有害注入的语义危害性复判 | injection | 21 | 1 | 确定性通道分数恒 0, 无可判读信号 |
| J-N2 | 7 例等价注入 validity audit | injection | 7 | 1 | 同上; 且为轴效度对照不可省略 |
| J-N3 | 层位第二证据叶落地后的 111 例定位复核 | injection | 0 | 0 | 阻塞于树结构变更需 Loop D 先批, 本窗零调用 |

估计合计 **28 调用**（预算内）。注: 阶段 A 的匹配-FPR 结论不依赖 judge; 本清单只回答
「零信号子组是否真有害」这一确定性无法回答的问题。

## 9 复现

```bash
venv/bin/python research/paper_d3_matched_fpr_stage_a.py            # 四段全跑, ~34s（工件 meta.elapsed_sec）
venv/bin/python research/paper_d3_matched_fpr_stage_a.py --sections a2   # 单段
venv/bin/python scripts/graph/hooks/summary_recompute_guard.py check docs/experiments/2026-09-01_d3_matched_fpr_stage_a.md
```

<!-- SUMMARY-GUARD
artifact: logs/graph/eval/d3_matched_fpr_stage_a.json
sha256: 3318ac178a0c3317ce18d69663b942e289c2668f4b604082606a549172f2ab10
claims:
  gates.all_pass = true
  meta.endpoint_calls = 0
  payload.zero_endpoint.model_calls = 0
  payload.g1_reproduction.checks.frozen_counts_reproduced_from_recomputed_scores = true
  payload.a1_embedding_calibration.e1_state = "b"
  payload.a1_embedding_calibration.embedding_citation_decision = "降为敏感性分析"
  payload.a2_clean_controls_fpr.enumeration.n_clean_usable = 2382
  payload.a2_clean_controls_fpr.contrastive_fpr_spectrum.flat_nonzero_observations = 0
  payload.a2_clean_controls_fpr.pivot.triggered = true
  payload.a4_matched_fpr.denominator_S2.harmful_H_union_HI = 111
  payload.a4_matched_fpr.operating_point_matched_alpha.tpr_flat = 0.810811
  payload.a4_matched_fpr.matched_fpr_difference.point = 0.0
  payload.a4_matched_fpr.matched_fpr_difference.bootstrap.difference_nonzero_replicates = 0
  payload.a3_dilution_rescue.union_deterministic.n = 11
  payload.judge_rescoring_needs.estimated_calls = 28
END-SUMMARY-GUARD -->
