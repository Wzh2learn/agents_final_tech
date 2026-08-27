# K2/小 B 章草稿核对清单（侧线预备, 机械对账用）

> 状态: 待主线程草稿落地 | 更新: 2026-08-27 | 取代/被取代: 无
> 用途: 主线程 K2 章草稿 v0 落地后, 侧线按 differential-review 口径机械对账——数字逐行比本表, 不一致即审查发现, 不凭印象。

## A. 预期数字（逐条带工件源）

| # | 声明 | 值 | 工件源（logs/graph/eval/） |
|---|---|---|---|
| A1 | 表级 MS（主口径） | 75/95 = 78.95%, CI95[70.53, 86.32] | k2_ms_bc_analysis.json → mutation_score.table_level_primary（seed=20260827, n_boot=2000） |
| A2 | 注入级 MS（仅参考） | 96/118 = 81.36%, CI95[74.58, 88.14] | 同上 → injection_level |
| A3 | 配对差 别名型−列名型 | +0.492 [0.2386, 0.6471] 显著 | 同上 → paired_bootstrap_type_diffs |
| A4 | 配对差 别名型−类型型 | +0.0312 [−0.1266, 0.0612] 不显著 | 同上 |
| A5 | 配对差 列名型−类型型 | −0.4608 [−0.6745, −0.2751] 显著 | 同上 |
| A6 | BC(δ=1) 盲区质量 | 22/118 = 0.1864 | 同上 → blind_cone_bc_delta1 |
| A7 | ocr_similar 盲率 | 13/13 = 1.0（锥尖, tier1 全吸收） | 同上 → by_type.ocr_similar |
| A8 | 六类可见性 | alias .9149(43/47) / date .8824(15/17) / mixed 1.0(20/20) / ocr 0(0/13) / prefix .8125(13/16) / unit 1.0(5/5) | checkpoint_discrimination_tables_v2.json → by_type |
| A9 | match_tiers 吸收机制 | alias tier0=43/tier2=4; ocr tier1=13（编辑距离≤1 全吸收）; prefix tier0=13/tier1=1/tier2=2; date tier0=14/tier2=3 | 同上 → by_type.*.match_tiers |
| A10 | crosswalk 四型 | 别名型{alias,mixed} 63/67=.9403 / 列名型{ocr,prefix} 13/29=.4483 / 类型型{unit,date} 20/22=.9091 / 结构型 [] 缺口注记 | 同上 → patent_crosswalk |
| A11 | 三性质 | 判别 75/95 / 局部性 95/95 零违规 / 零漂移 95/95 / crosscheck_mismatch=0 | 同上 → properties |
| A12 | QA 小臂 | 12 条 :8004（9 忠实 / 0 自动改写 / 3 列错位） | 报告 v2 → qa_arm + THREADS #K2-DISC-WINDOW |

## B. 结构断言

- 五节齐全: 问题定义 → 盲锥测度（命题 2）→ 注入分类学与 crosswalk → K2 v2 实证 → 局限与 C4 衔接
- 图引用 fig1-fig5 齐全（figures_k2/）, caption 语义与盲锥骨架图清单一致
- §5.3.3 口径注记原样: 95 表 ≠ 9 类预构造场景
- 结构型缺口诚实注记（结构型 [], 后续版本补结构扰动）
- BC 真实分布侧显式注记"待公开语料或合成渲染（接 C4）, 甲方真实 OCR 红线禁入"

## C. 禁词与红线

- judge 四维分数 / 5.0 / unusable（01:51 工件已作废, 永久禁引）
- 甲方真实数据与真实 OCR 样本（零进入）
- 未定义缩写首现（BC/MS/δ/tier 等须先定义后使用）
- 正文避免内部运维标记（端口号 / B4 / canary / sidecar）: 论文面向文本以角色名替代, 实验文档本体可保留

## D. 对账方法

1. A 表逐行: 在草稿中检索对应数字, 命中且上下文语义一致 = PASS; 缺失或不一致 = 发现, 入审查报告
2. B 节逐条勾选; C 节全文扫描（含正则: 端口号 \d{4} 四位数串、judge、5\.0、unusable）
3. 报告落 docs/experiments/（differential-review skill 体例）, 发现分级（数字错误=HIGH, 口径缺失=MEDIUM, 措辞=LOW）
