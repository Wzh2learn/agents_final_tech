# 检查点树评测协议 v0 — 首个分层评分报告 + 口径对照

> 状态: 活跃 | 更新: 2026-08-18 | 类型: K2 科研探索产出（只读形式化, 不改基线/既有 eval 脚本）
> 依据: K1 SOP `docs/experiments/2026-08-18_hbkeyan_close_read/gta2_checkpoint_tree_sop.md` §3/§4 + Algorithm 1
> 输入工件: `logs/graph/eval/` 活工件（2026-08-16 产, gitignored）| 基线: `docs/experiments/2026-08-08_eval_baseline.md`

## 1 交付物与运行方式

- 树定义: `config/eval_checkpoint_trees.json`（meta 自描述: 口径/版本/阈值; 20 叶子; weight∈{1,2,3}）
- 聚合脚本: `scripts/eval_checkpoint_aggregate.py`（Algorithm 1 自底向上; 兄弟归一化加权平均; 叶子从工件实测值确定性映射 0-10; 缺工件显式降级 missing_score, 不静默给 0）
- 运行（演示日安全, 纯确定性计算, 不调用 :5050/:8004/:8006）:
  `python3 scripts/eval_checkpoint_aggregate.py`
- 输出: `logs/graph/eval/checkpoint_aggregate_report.{json,md}`（gitignored 工件目录）; 本报告为可追溯的快照, 数字与 json 报告一致

## 2 首个分层评分结果

| 树 | Root Score (0-10) | 叶子数 | k=5 root/leaf SR | k=7 root/leaf SR | k=8 root/leaf SR | STABLE |
|---|---|---|---|---|---|---|
| parse (M1 解析树) | 10.0 | 5 | 1.0 / 1.0 | 1.0 / 1.0 | 1.0 / 1.0 | True |
| qa (QA 树) | 10.0 | 7 | 1.0 / 1.0 | 1.0 / 1.0 | 1.0 / 1.0 | True |

- STABLE 判据（K2 定, 供报告用）: ≥90% 叶子 ≥7 且无 hinge 叶子 ≤7 → parse 5/5, qa 7/7, min_leaf=10.0, hinge_ok=True
- 注: Root SR 在 k=5/7/8 全 1.0, 因为两棵子树 Root 都是 10.0（三档阈值无区分度）; 区分度依赖真实退化样本, K5/K6 建议引入构造缺陷样本验证判别力

### 2.1 叶子级得分（与基线逐条对照, 见 §3）

- parse: `parse.doc.ok` 10 / `parse.doc.throughput` 10 / `parse.table.regression` 10 / `parse.field.hit_rate` 10 / `parse.reconcile.equations` 10
- qa: `qa.retrieval.source_required` 10 / `qa.faithfulness.judge` 10 / `qa.numeric.exact` 10 / `qa.numeric.number_grounding` 10 / `qa.citation.judge` 10 / `qa.refusal.judge` 10 / `qa.refusal.deterministic` 10

## 3 口径对照（叶子级数字 vs 2026-08-08 基线文档）

| 基线条目 | 基线值 | 本协议映射 | 结果 | 结论 |
|---|---|---|---|---|
| M2 确定性检验 16/16 | 16/16 PASS | 每个契约 check 通过率 | n=16, all_pass 逐题 True | **对上** |
| AI judge 四维均分 | faithfulness 5.0 / numeric 5.0 / citation 5.0 / refusal 5.0 | judge 0-5 ×2 → 叶 10.0 | 四叶全 10.0 | **对上** |
| M1 scenario1 回归 15/15 | quick: 12 PASS + 3 OCR skip (基线 100/100; TraFax [50,81.8,100]; WaveFax 100; guojin 90 等) | 表级/字段级叶 | 12 源全 PASS; 15 表级条目全过; 3 OCR 源本次未跑（SKIP(quick)） | **对上**（quick 口径一致; OCR 源按基线 eval_summary 的 quick=True 口径不参与） |
| M2 数值忠实度 0/9 fail | 09-09 基线: NF 未在基线文档, eval_summary 2026-08-16: 0/9 条未落地 | NF 通过率 9/9 → 叶 10.0 | n=9, n_fail=0 | **对上** (与 eval_summary.md 一致; 基线文档未覆盖此条目, 属补充而非漂移) |
| judge 一致性 | judge_consistency_report: 3 runs, drift_any=False | 未作为独立叶子（归入各 judge 维叶） | 3 runs 全 5 分 per-dim | 一致性支持四维叶 10.0, 无独立计数节点 |

**漂移清单**: 无（本次所有叶子/树的数字与基线文档逐条对上）。

**口径边界（如实记录, 非漂移）**:
1. OCR 三源（华泰紫金/TraFax/WaveFax）本次 quick 门禁 SKIP, 不进叶子; 全量门禁才计（基线的 15/15 是含 OCR 的全量历史值, 本报告为 quick 工件快照）
2. 勾稽级 `parse.reconcile.equations` = 10 derived（K1 SOP §3.1 引用工程期 reconcile ALL PASS; 现有工件不产 reconcile 明细, 已注明 derived 而非直接测量）
3. 拒答/引用等 k=9 边界设计: K2 采用"k=9 表示区分 borderline(9) 与稳健通过(10)"的判读, 阈值敏感性 K5/K6 再定
4. 本协议是 GTA-2 的形式化落地（K2 只新增）, 不是 :5050/:8004 的直接测量; 演示日禁跑约束下, 所有数字来自 2026-08-16 活工件（timestamp 已记录于报告 json）

## 4 与 GTA-2 三类 SR 的对应

| GTA-2 指标 | 本项目实现 |
|---|---|
| Root SR | 每树子树 Root 超阈值比例（k 参数化, 报告 5/7/8 三档） |
| Leaf SR | 每树叶子超阈值比例（同上三档） |
| Tool SR | 未做工具调用场景; 对应替代 = 工件级调用成功（m1_regression run_completed / judge 报告存在性）已并入文档级叶 |

## 5 局限与后续

- 阈值 k=5/7/8 区分度不足（当前全绿）; K5 建议用判别力/敏感度目标做阈值与权重搜索（用构造缺陷样本）
- 缺工件降级路径已实现并有测试覆盖（missing_score 默认 5, hinge 0）; 现网四工件齐全, degraded=[] 如实记录
- 基线文件与既有 eval 脚本零改动（本次仅新增 config/scripts/docs/tests 四类文件）

