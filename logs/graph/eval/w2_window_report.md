# W2 窗口汇报: :8004 合并窗（E1.5 Full-Judge + E1.6 多 seed + T4 PSO 严谨对照）

> 任务卡: docs/experiments/2026-08-30_w2_window_card_8004.md（TASK-20260830-04, risk medium, 预批: W1 绿态当晚开）
> 执行: Loop A | 收口: 2026-08-30 | :8004 真实调用: **122 / 200**（E1.5 120 单元 + 1 证据变更重判 + 1 中断占用）
> 端点自证: socket 层护栏, E1.5 `ports_touched=[8004]`；E1.6/T4 各自 `ports_touched=[]`（零调用段）
> 复算命令: `paper_w2_e15_full_judge.py --dry-run` / 同名全量（缓存命中零新增）/ `paper_w2_e16_injector_seeds.py` / `paper_w2_t4_pso_fair.py` / `paper_w2_assemble.py`
> 复算验证: E1.6+T4+装配连续双跑 `payload_sha256` 一致（`11674624…d807f`）；E1.5 全量重跑 120/120 缓存命中且 call_counter 不增（122→122）  
> 摘要修正: 首 commit 后抽验发现 `payload_sha256` 在最后一次 payload 改动之前计算, 审阅方按文件复算必然不匹配; 已改为收口后计算并新增 `digest_self_consistency` 门, 摘要由 `fe492e14…0ba7` 变为 `11674624…d807f`（详见 §9）

## 1 执行结果（三段各一行）

| 段 | 结果 | 关键数字 |
|---|---|---|
| E1.5 Full-Judge 基线（12 叶 × 10 状态） | **PASS**（未 BLOCKED） | 120/120 单元格式合格 0 失败；判分均值分离度 1.3053 vs 映射 1.2526；检出 3/9 两口径同为 M1/M8/M9；一致性 max\|Δ\|=0.5（边界） |
| E1.6 injector 三 seed 臂 B（零调用） | **PASS** | seed42 与冻结工件**字节一致**（三文件 sha 全等）；E1.2_flat = 0.7895 / 0.7835 / 0.7556 全落预测带 [0.70,0.85]；合并 0.7766 CI [0.727, 0.8227] |
| T4 PSO 五组对照 + minimax + 预算梯度（零调用） | **PASS 但触发 C3 降级条款** | 冻结复现门 abs_err=**0.0** 且权重逐维全等；PSO 1.432574 = greedy 1.432574（114.2× 评估次数）；minimax worst 0.3571 ≥ 预测 0.208 |

段间不互锁规则未被触发（三段一次通过, 无改期, 无 BLOCKED 段）。

## 2 工件路径

- `logs/graph/eval/t4_pso_fair_comparison.json` — 本窗唯一终 artifact（卡 §1 要求）, `payload_sha256=11674624219f63b672043116ed4079b98e911e58221d46fbae96920cd66d807f`, gates 全 PASS（含 `digest_self_consistency`）
- 分节中间件（可复算, 不入 payload 摘要范围）: `_w2_e15_section.json` / `_w2_e16_section.json` / `_w2_t4_section.json`
- 预算账本 `logs/graph/eval/w2_e15_call_ledger.json`（122 条 notes, 逐次可溯源）
- 裁判原始缓存 `logs/graph/eval/w2_e15_judge_cache.jsonl`（本地留存不入库, 其 sha256 入工件 `judge_cache_sha256`）
- 本汇报 `logs/graph/eval/w2_window_report.md`
- 脚本: `research/paper_w2_e15_full_judge.py` / `research/paper_w2_e16_injector_seeds.py` / `research/paper_w2_t4_pso_fair.py` / `research/paper_w2_assemble.py`

## 3 数字摘要

### 3.1 卡 §5 验收证据表（实测值已填）

| 声明 | 验证命令/位置 | 实测值 |
|---|---|---|
| 预算 ≤200 | `payload.call_counter` | **122**（ceiling 200, 余 78） |
| 端点仅 :8004 | `payload.endpoint_assert` | `ports_touched=[8004]`, `violations=[]`, `only_allowed_endpoint=true`；E1.6/T4 `model_calls=0` |
| C3 五组对照 | `payload.t4.separation_table` | equal 1.2563 / expert 1.2560 / random30 1.2604 / greedy 1.4326 / **PSO 1.4326**（主口径 pso_era） |
| E1.6 三 seed CI | `payload.e1_6` | 0.7895 [0.6947,0.8737] / 0.7835 [0.701,0.866] / 0.7556 [0.6667,0.8444]；合并 0.7766 [0.727,0.8227] |
| 一致性差异注记 | `payload.e1_5.endpoint_consistency_note` | faithfulness Δ=**0.5**、citation Δ=0.0、refusal Δ=0.0 → 预测 \|Δ\|≤0.5/维 **HOLDS（恰在边界）** |

### 3.2 E1.5 判分 vs 确定性映射：逐 mutant 分离度（v2 口径, 根分落点）

| mutant | 判分 sep | 映射 sep | 判分根分降幅 | 映射根分降幅 | 判读 |
|---|---|---|---|---|---|
| M1_m1_rows_fail | 1.8523 | 2.6428 | 3.7045 | 5.2855 | 闸门软化（F_W2_3） |
| M2_exact_numeric_fail | 0.6250 | 0.6250 | 1.2500 | 1.2500 | 完全一致 |
| M3_source_required_fail | 0.8333 | 0.8333 | 1.6667 | 1.6667 | 完全一致 |
| M4_refusal_expected_fail | 0.5556 | 0.5556 | 1.1111 | 1.1111 | 完全一致 |
| M5_judge_faithfulness_degrade | 0.6250 | 0.7350 | 1.2500 | 1.4700 | 整数化取整损失 |
| M6_judge_citation_degrade | 0.5000 | 0.5833 | 1.0000 | 1.1667 | 整数化取整损失 |
| M7_nf_fail_3 | **0.0000** | 0.2083 | 0.0000 | 0.4167 | 缺陷在 item 层不可见（F_W2_1） |
| M8_judge_artifact_missing | 2.0972 | 1.1656 | 4.1944 | 2.3311 | 裁判对空证据悲观（F_W2_2） |
| M9_m1_all_rows_fail | 4.6591 | 3.9248 | 9.3182 | 7.8497 | 灾难态判分更敏感 |

均值 1.3053（判分）vs 1.2526（映射）；检出集两口径相同（3/9 = M1/M8/M9, 根分落点 TAU=2.0）。
四契约类突变（M2/M3/M4 + 部分 M5/M6）判分与映射**逐位相同**, 差异集中在三处机制（F_W2_1/2/3）。

### 3.3 T4 主口径（pso_era, 08-19 矩阵）五组对照

| 组 | 均值分离度 | 最差 mutant 分离度 | 评估次数 | 备注 |
|---|---|---|---|---|
| equal | 1.256268 | 0.166665 | 1 | 无先验 |
| expert | 1.255968 | **0.208331** | 1 | 人工先验（复现冻结 1.2560） |
| random(30) | 1.260413 (std 0.05296) | 0.069444（30 组里最差） | 30 | 16/30 优于 expert, 单点最好 1.3670 |
| greedy | **1.432574** | 0.092591 | **67** | 坐标上升, 与 PSO 同最优点 |
| PSO(5 seeds) | **1.432574** (std 0.0, CI 零宽) | 0.092591 | 7650 | G 门 abs_err=0.0, 权重与冻结逐维全等 |
| PSO-minimax(5 seeds) | 1.256050 | **0.357140** | 7650 | 最差维 +0.2645 / 均值 −0.1765 |

- 次口径 v2(08-26) 排序完全一致: expert 1.252634 / equal 1.253601 / random30 1.257812 / greedy=PSO 1.428129 / minimax worst 0.357139。
- 题集预算梯度 25/50/75/100%（B=5/10/14/19）: keep_rate 恒 1.0 → **饱和**, 判据"单调不降"平凡成立但无区分力；适应度序列 0.031579/0.036842/0.031579/0.031579 非单调（B=10 反而更差, 搜索噪声）。
- Pareto（mean × worst 双轴）: 非支配点 7 个, **去重后只有 2 个不同点** (1.4326, 0.0926)〔PSO/greedy〕与 (1.3344, 0.3571)〔minimax seed777〕; expert/equal 两点均被 minimax 解支配。

### 3.4 E1.6 三 seed 判别率分布

| seed | 注入表数 | 注入数 | E1.2_flat 表级 | 95% CI | E1.1 | E1.3 |
|---|---|---|---|---|---|---|
| 42（冻结） | 95 | 118 | 0.7895 | [0.6947, 0.8737] | 1.0 | 0.2105 |
| 20260831 | 97 | 121 | 0.7835 | [0.7010, 0.8660] | 1.0 | 0.1855 |
| 20260832 | 90 | 108 | 0.7556 | [0.6667, 0.8444] | 1.0 | 0.2000 |
| 合并（282 表） | — | — | 0.7766 | [0.7270, 0.8227] | 1.0 | 0.1915 |

三 seed 极差 0.0339, CI 高度重叠 → 臂 B 判别率对注入种子稳健。E1.1 恒 1.0 / E1.3 恒 ~0.19-0.21 同样稳定。

## 4 红线自查

| 红线 | 结论 | 证据 |
|---|---|---|
| 端点仅 :8004, :8006/:8008/:5050 零触碰 | **PASS** | E1.5 `ports_touched=[8004]`；E1.6/T4 独立 zero-guard `ports_touched=[]`；护栏禁代理（`ProxyHandler({})`）防 :8100 劫持 |
| 预算 ≤200 硬计数器, 不静默超支 | **PASS** | 账本悲观占用 + 超限抛错；122 条 note 可溯源；重跑缓存命中不增计数 |
| judge 不见注入 ground truth | **PASS** | dry-run 120/120 单元零残留（甲方标识 + `mutated_field`/状态 id 全清单）；prompt 不含状态标识断言；`overall`/`avg`/占比等预聚合量全屏蔽 |
| 甲方标识零进入 | **PASS** | 位置别名（row_NN/item_NN/org_NN）构造期生成 + `redact` 二道闸 + 终工件全 JSON 字符串零命中（`client_identifier_zero_entered=true`） |
| 冻结工件只读 / 活工件只读 | **PASS** | mutants 只作用于 `/tmp/w2_e15_scratch` 副本；冻结 md5 五件全 OK；`git status` 显示活工件 0 改动 |
| 禁 `git add -A` / 禁 amend | **PASS** | 逐路径 `git add -f`；不 amend 任何既有 commit |
| TAT-DQA 不投入 / opencode.json 不动 | **PASS** | 未触碰；臂 B 复用既有 drift_v0 公开数据注入器（属已批准的评测协议资产, 非新开 TAT-DQA 实验线） |

## 5 预注册判据对账（卡 §2.2, 冻结于执行前）

| 判据 | 预测 | 实测 | 裁定 |
|---|---|---|---|
| C2 ≥3 seeds CI 可算 | 三 seed 各自可算 | 三 seed CI + 合并 CI 全部可算且非退化 | **PASS** |
| C3 PSO 优于四组对照 | 优于 equal/expert/random/greedy | 优于前三组, **与 greedy 完全打平** | **PARTIAL → 降级条款** |
| C3 最坏维度如实报告 | 如实 | PSO worst 0.0926 < expert worst 0.2083（均值增益以最差维退化为代价） | **已如实报告** |
| E1.5 一致性 \|Δ\|≤0.5/维 | 校准预期 | max 0.5（faithfulness） | **HOLDS（边界, 见 F_W2_4）** |
| T4 PSO ≥ expert 且复现 1.4326±0.01 | 1.4326 | 1.432574, abs_err 0.0 | **PASS** |
| T4 random30 < PSO | 成立 | 1.2604 < 1.4326 | **PASS** |
| T4 minimax worst ≥ 0.208 | ≥0.208 | 0.3571 | **PASS** |
| T4 预算梯度单调不降 | 单调 | keep_rate 恒 1.0（饱和） | **PASS 但不可用** |
| E1.6 三 seed ∈ [0.70,0.85] | 带内 | 0.7895/0.7835/0.7556 | **PASS** |

## 6 发现与局限（编号入工件 `payload.findings`）

- **F_W2_1 突变体保真度**: M7 在判分口径分离度恰为 0。机制 = NF 工件 9 条里 8 条 `number_claims=0`, `mut_nf_fail(3)` 只把前 3 条（零数值主张）的 `pass` 置 False 并写聚合 `n_fail=3`；本窗按证据等价设计对裁判屏蔽 `n_fail`, 于是缺陷在 item 层不可观测。**结论: 该 mutant 的差异不能归因裁判能力**, 两口径在根分落点上也都不检出（<TAU）。
- **F_W2_2 缺失证据的评分政策**: 确定性口径对缺工件给中性 5 分, 裁判对空证据给 0/0/5（"无法验证即最低分"）→ Full-Judge 对 M8 敏感度翻倍（2.0972 vs 1.1656）。属**政策选择**（悲观 vs 中性）而非优劣。
- **F_W2_3 硬闸门 vs 部分分**: `parse.doc.ok` 确定性路由是 `overall_status_binary`（2 条 FAIL 即归零）, 裁判按失败占比给 7 分 → M1 分离度被软化（1.8523 vs 2.6428）; 反向 M9 更敏感（4.6591 vs 3.9248）。契约语义不可与 Full-Judge 互换。
- **F_W2_4 分辨率下限**: 0-10 整数叶分下 1 单位 = 0-5 维尺度 0.5, 恰等于一致性判据容差；faithfulness 真值 9.875 无法整数表达（裁判给 9）。判据在该量纲下无区分力, 需放宽容差或改连续叶分（明日一页纸判定项）。
- **F_W2_5 greedy 平价 + 成本反转**: 权重搜索上 PSO 相对坐标上升无判别力增益且贵 114 倍评估；离散 {1,2,3}^11 目标面最优点高度退化（5 seed std=0, CI 零宽）。→ C3 必须按降级口径陈述（自动搜索价值 = 省专家调参, 非判别力上限）。
- **F_W2_6 种子稳健性**: 臂 B 判别率三 seed 极差 0.0339, CI 重叠 → 变异主要来自表样本而非注入种子。
- 另注: 本窗 E1.5 的 3 个 judge 叶为"裁判评逐条判定"（工件层证据）, 非"裁判评原始答案"；端点一致性注记度量的是 :8004 聚合器能否复现历史四维均分, 不等于 :8004/:8006 逐条判定一致率。此限定已写入工件 `endpoint_consistency_note.caveat`。

## 7 复盘: 喂给了什么

- **S4/S5 正文表**: §3.2 判分 vs 映射逐 mutant 表（9 行 × 4 列 + 三机制归因）；§3.3 五组对照表（含 worst 列与评估次数列）→ 支撑 C3 降级条款的改写。
- **Pareto 图数据**: 工件 `per_caliber.*.pareto.points/front`, 双轴 (mean, worst)；去重 2 点 + 13 总点, 可直接出图（含 expert/equal 被支配的事实）。
- **明日《判定一页纸》判定项**:
  1. F_W2_4 量纲: 叶分是否改连续值 / 一致性容差是否放宽到 >1 单位（影响 E1.5 结论强度）；
  2. F_W2_1 突变体: M7 是否重设计为"在有数值主张的条目注入 ungrounded"（否则数值忠实度维的 Full-Judge 结论不可下）；
  3. C3 降级条款是否采纳（PSO→"省专家调参"叙事）, 以及是否补 greedy 作论文标准对照组；
  4. 题集预算梯度饱和: 是否换判据轴（最小叶支撑题数 / 类型覆盖）或扩题库使梯度可辨；
  5. E1.5 是否追加"裁判评原始答案"的第二形态（需另批预算, 本窗 78 次余量不足以跑 16 题 × 4 维）。
- **未做/留档**: `--stability` 复采未启用（预算余量充足, 但本窗结论不依赖复采）；cache 不入库仅记 sha。

## 8 交班

- Loop B 在本窗执行期间因我 4 个在制未跟踪脚本判 `git_alignment=FAIL`（dirty 6 > 白名单 5）, 其余 8 项检查（frozen/pytest/api_anchors/qa_canary/docs_lint/model_topology/watchdog/pg_pool）全 PASS；本 commit 入库后 dirty 归零, 下一 30min 周期应自动翻回 PASS。
- 冻结件五件 md5 全 OK, 未触发 REQUEST_UNFREEZE。
- 预算账本与缓存留在本地（`logs/` gitignored, 仅 artifact/report 逐路径 `-f` 入库）。

## 9 收口清单扫描结果（2026-08-29 制度化条款）

- `scripts/graph/governance_drift_scan.py`: **15 hits, registered 0**（与开窗基线同值, 本窗零新增漂移候选）
- `scripts/docs_lint.py`: **PASS（0 fail / 0 warn）**
- `venv/bin/python -m pytest -q`: **402 passed / 13 skipped**（与 W1 收口基线同, 本窗零回归）
- 冻结节点 md5 复核: 五件全 OK（`tests/test_m1_service.py` / `m1_table_schema.json` / 三件基线资产）
- CJK 字节检查: 本汇报与 STATE/INDEX 编辑 U+FFFD 零残留
- **摘要计算次序缺陷（本窗抽验发现并已修复, 记入台账）**: `paper_w2_assemble.py` 原先在
  `redline_self_check.client_identifier_zero_entered` 写入**之前**计算 `payload_sha256`,
  导致首个 commit 的存储摘要覆盖的是"写入前的 payload"——审阅方按文件复算必然不匹配。
  修复 = ① 摘要移到 payload 全部改动完成之后；② 新增永久门 `digest_self_consistency`
  （回读已写文件并对**存储的** payload 重新哈希）, 使同类缺陷下次收口即红。
  双跑摘要一致（`11674624…d807f`）, 独立文件复算 = True。研究数字（122 调用 / 三段结果 / 判据裁定）零改动,
  仅 provenance 字段与摘要值变化。
- **Hook Escalation Ladder 计数**: 这是"**声明的哈希/扫描与存储工件不符**"第 **2** 次
  （第 1 次 = W1 `SCAN_MANIFEST` glob 漏扫, 见 STATE.md W1 治理教训）。第 3 次即上机械强制;
  本窗已以 `digest_self_consistency` 门预先机械化, 建议把"终工件摘要必须回读复算"提炼进
  `scripts/graph/hooks/` 通用件而非留在单脚本。
