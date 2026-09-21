# Algorithm 1 逐行对位表（论文伪代码 ↔ eval_checkpoint_aggregate.py）

> 状态: 对位表（2026-09-20, Loop D 主线; 纯文本产出, **未改任何实现**）
> 用途: 支撑 `paper/draft_v0_s1_s2_s6.md` 的 S2 Algorithm 1；保证论文伪代码可由实现逐行复核
> 边界: **不修改现有实现**；本表只做「论文行 ↔ 代码行」的映射与差异说明
> 实现件: `scripts/eval_checkpoint_aggregate.py`（360 行, 本批未改动）; 树配置: `config/eval_checkpoint_trees.json`

## 1 伪代码行 ↔ 实现位点

| 伪代码行 | 含义 | 实现位点 | 备注 |
|---|---|---|---|
| 2 `if n has no children` | 叶子判定 | `aggregate_tree.dfs` 的 `if not children:` | 叶子 = 无 `children` 字段的节点 |
| 3 `v,c,note <- EVIDENCE(n)` | 取证据 | `_mapped_leaf_score` 顶部的 `art = artifacts.get(src, ...)` | 工件缺失 ⇒ 直接进第 4 行 |
| 4 `if v is undefined` | 缺失/不可用 | `if "__missing__" in art:` 与 `if val is None:` | 两条支路（工件缺 / judge 维不可用）合并为论文的一行 |
| 5 `return (m(n), degraded, note)` | 显式降级 | `return float(leaf.get("missing_score", 5.0)), {"degraded": True, "reason": ...}` | **不静默给 0**；`missing_score` 逐叶取自树配置 |
| 7 `judge_dim_0_5 -> 10*v/5` | judge 0-5 放大到 0-10 | `score = val * unit / 5.0`（`unit = 10.0`） | |
| 8 `else 10*v` | 比率/二值映射 | `score = val * 10.0`（`pass_rate_contract` / `nf_pass_rate` / `row_pass_rate` / `hit_rate_achievement`） | 二值叶走 `else` 分支的 `val*unit/10`（10 或 0） |
| 11 `C <- children(n)` | 取子节点 | `children = node.get("children", [])` | |
| 12 `W <- sum w(c)` | 兄弟归一化分母 | `w_sum = sum(w for _,_,w in scores)`; `w_sum = w_sum or 1.0` | 全零权重保护为 1.0 |
| 15 `S += (w(c)/W) * SCORENODE(c)` | 加权平均 | `agg = sum(s * (w / w_sum) for s,_,w in scores)` | 与原文 Algorithm 1 第 10-16 行同构 |
| 20 `(S(r),degraded,_) <- SCORENODE(r)` | 根分 | `dfs(tree)` 后 `tree["_score"]` | |
| 23 `root_sr(k)` | 子树根超阈值比例 | `root_ok / max(len(tree.get("children",[])),1)` | 分母 = **本树根的直接子节点数**（parse 4 / qa 5），实测量于 `checkpoint_aggregate_report.json` 的 `results.<tree>.sr.<k>.n_sr_subtrees`；旧 docstring :15 写的 "n_subtrees=2" 是**森林树数**，不是本分母 |
| 24 `leaf_sr(k)` | 叶子超阈值比例 | `leaf_ok / max(len(leaves),1)` | 分母 = 当前树叶子数（parse 5 / qa 7） |
| 26 `k_last` | 稳定性使用的阈值 | `for k in thresholds:` 循环内赋值 `stable = {...}` | **末次迭代生效**（默认 5,7,8 ⇒ k=8） |
| 27 `stable <- ... > k_last ... hinge >= 7` | 稳定性判据 | `leaf_ok >= 0.9*len(leaves) and all(leaf_scores.get(h,0) >= 7 ...)` | 叶子侧用 `>`，hinge 侧硬编码 `>= 7` |

## 2 hinge gate 行为（论文 S2 「硬门」措辞依据）

- `HINGE_ROUTES = {"overall_status_binary", "pass_rate_contract", "nf_pass_rate"}`（实现 `:149`）。
- hinge 叶子的作用：**唯一特化 = 参与稳定性判据的硬子检查**（`stable` 表达式右半）。**缺失分数不是 hinge 属性，而是按树配置**：parse 树 5 个叶全 `missing_score: 0`，qa 树 7 个叶全 `missing_score: 5`（含 4 个 hinge 叶中的 3 个）。
  - 实测（`config/eval_checkpoint_trees.json`）：hinge 集合（mapping ∈ `HINGE_ROUTES`）**实际命中 5 个叶** = `parse.doc.ok`(0) / `qa.retrieval.source_required`(5) / `qa.numeric.exact`(5) / `qa.numeric.number_grounding`(5) / `qa.refusal.deterministic`(5)；mapping 类型共 **3 种**（`overall_status_binary` / `pass_rate_contract` / `nf_pass_rate`）。
  - **纠正常见误读**：不存在「hinge 缺失统一给 0」；5 个 hinge 叶里只有 1 个是 0，反向也不成立（4 个**非** hinge 的 parse 叶也都是 0）。真实策略 = **按树分**（parse 全 0 / qa 全 5）。
- **注意（纠正常见误读）**：hinge **不会**把父节点「归零」——聚合仍是兄弟归一化加权平均，hinge 只通过「低分把该叶拉低」+ 「阻断 stable 判定」起作用。
  论文 S2 原句曾写 "hard hinge gates that zero a subtree on gate failure"，**与实现不符，已在 T7 修正**。
- 20 叶旧口径注记: 脚本 docstring **第 17 行**（不是 :16）写「STABLE = (18/20 叶子 >= 7) 且 (无 hinge 叶子 <= 7)」；现树 **12 叶**（parse 5 + qa 7），0.9 比例按 12 计算。
  **边界差异（新增登记）**：docstring 写 hinge 判据为「无 hinge 叶子 **<= 7**」，而实现是 `all(hinge >= 7)`（`:257`-`:259`）——两者在 **=7 边界相反**。本表只登记，**不改实现也不改 docstring**（均属另批授权）。

## 3 复算与差异自证（全部在 GB10 上跑）

- `venv/bin/python scripts/eval_checkpoint_aggregate.py --out -`：exit 0；`parse` root 10.0 / 5 叶、`qa` root 9.97 / 7 叶。
- 阈值排列实验（`--thresholds 7` / `5 7 8` / `8 7`）三组 `stable` 均为 True 且 `leaf_pass_count` 与 `n_leaves` 相同 ⇒ **本语料上末次阈值的选择不改变任何上报数字**，差异只在定义层面。
- `stable` 的叶侧比较用 `>`（非 `>= `），已在伪代码一行写明。
- **仓内存档说明**: `logs/graph/eval/checkpoint_aggregate_report.json` 是 **2026-08-18 旧档**（`qa` root = 10.0）；本表第 3 节复算出的 `qa` root 9.97 以**当前** `m2_judge_report.json`（faithfulness avg 4.94）为准。两者对不上是**取时点不同**，不是矛盾。

## 4 未决 / 不在本件范围

- 脚本 docstring 的「18/20」与「k=7」两处过时表述 **留待授权批次修正**；本批只写论文描述。
- 具体 `weight` 与 `missing_score` 逐叶取值以 `config/eval_checkpoint_trees.json` 为准，本表不复制，避免两处漂移。
