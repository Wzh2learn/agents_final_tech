# V4 科学解释裁决 v1

> 状态：`LOOP_D_RULING_READ_ONLY`
> 日期：2026-10-15
> 对象：`research/paper_e_layer1_20261015/v4/` 的 v4 结果、契约、runner 与 post-result audit
> 范围：只做科学解释与 claim boundary；不修改 v1-v4 任何产物，不重跑，不启动 Layer-2。

## 0. 裁决摘要

v4 通过的是一个**工程契约**：规则可执行、标签可复现、检查读取顺序干净、held-out 标签没有被 checker 污染。  
v4 没有证明的是：E/H/U 就是真实任务语义的合法性、有害性与不可判定性 gold。

因此：

- `GOLD_ESTABLISHED_ON_HELDOUT` 只能读作：“在冻结的列局部词法绑定契约下，独立 binding gold 可构造。”
- 不能读作：“我们已经建立了真实任务 gold。”
- `co_miss` / `co_alarm` 只能读作：对冻结代理标签与 `visible_frozen` 的描述性条件率。
- 不能读作：标准 FNR/FPR，或多个 checker 的共同盲点。
- 下一步的关键问题是测量设计，不是继续降低 U 率，也不是继续修改 runner。

## 1. 三个不同层次的真值

| 层次 | 内容 | 可以证明什么 | 不能证明什么 |
|---|---|---|---|
| 来源列真值 | injection map 的 `{uid, col, original, injected}` | 某来源列的表头被改成了什么 | 改动后真实任务答案是否改变 |
| 绑定预测 | 冻结规则（norm + Levenshtein + guard）把注入表头绑到哪一列 | 规则在词法层面是否仍绑定到目标列 | 绑定到目标列是否等于任务语义仍合法 |
| 真实任务正确性 | 固定任务、参考答案、证据单元、容许变化、错误判定 | 扰动是否真的改变任务答案或引用关系 | 不能由绑定规则自洽推出 |

v4 的 E/H/U 属于第二层。第三层尚未定义，也尚未标注。

## 2. U 率的含义

`u_rate_heldout = n(U among held-out 59) / 59` 只度量**规则可判定比例**：

- 它说明冻结规则在 59 个 held-out case 里，有 12 个无法给出唯一绑定（9 个 tie，3 个 target collision）。
- 它不说明这些 U 在真实任务里是否合法、是否错误，也不说明“gold 有效”。
- 不能通过把 U 改名、放宽 tie、修改 norm 或追加审计轮次来把 U 率当作 gold 有效性证据。

## 3. `visible_frozen` 的精确含义

代码定义（`research/paper_t2_visibility_sensitivity.py`）：

```
absorbed_full = target_c is not None and map_full_for_abs.get(target_c) == e["injected"]
visible_frozen = not absorbed_full
```

含义：在全注入表的 matcher 输出中，来源目标 canonical 字段是否被映射为注入后的字符串。  
`visible_frozen = true` 表示被审 matcher **没有吸收**该注入表头；`false` 表示它吸收了。

这不是任务级报警规则。v4 没有“看到什么信号就报警/接受/弃权”的显式决策定义。  
因此：

- 不能把 `visible` 写成 checker 报警。
- 不能把 `blind` 自动写成系统失败。
- 不能把 `visible_frozen` 的差异直接解释成任务语义差异。

## 4. 历史 co_miss / co_alarm 数字与中性解释

保留原有数字与公式，不改写：

- visible: E=19, H=17, U=12 (n=48)
- blind: E=10, H=1, U=0 (n=11)
- `co_miss_rate = n(blind,H)/n(blind) = 1/11 = 0.09090909090909091`
- `co_alarm_rate = n(visible,E)/n(visible) = 19/48 = 0.3958333333333333`

中性解释：

- 它描述的是“在冻结代理标签下，checker 的 `visible_frozen` 状态与 E/H/U 的条件交叉率”。
- 不是标准 FNR/FPR，因为没有真实任务 gold，也没有独立漏检定义。
- 不是“共享路径导致共同盲点”的证据；v4 只有一个 checker 状态，没有路径共享证明。
- blind 行里 10/11 是 legal variation、1/11 是 harmful，只能作为描述性观察，不能外推总体。

## 5. dev / heldout 表 UID 重叠独立复核

独立复核结果（本次重新计算，不引用总规划师数字）：

- v1 dev：59 rows，54 unique table UIDs
- v4 held-out：59 rows，50 unique table UIDs
- 两侧 UID 交集：**9 个**
- held-out 中落在重叠表上的 rows：11
- dev 中落在重叠表上的 rows：9
- held-out 每表 rows 最大值：3
- held-out 中 >1 rows 的表：8 个

重叠 UID：

```
32cfcadb-add0-4cc1-9956-41ac073477c4
3c609073-6a48-4961-84cd-de68a59fd66c
425ee1c7-fb82-4853-994a-9876c414fbd5
5fe2c49e-5b1a-479a-8df7-f9a50e5d7609
68b8d514-802c-4ebc-a754-db4a3db7f9fd
abba843f-be4e-4905-8bab-19942dbfedef
b6fa85a0-a203-4ed3-8c4d-6c1b5a8b08c1
bf4ac2c0-98c9-481c-ba0c-c6728b3b3540
ed76bf6b-4d46-42b2-88ff-b2205470c8af
```

含义：v4 的 held-out split 是 **injection-level split**，不是 table-disjoint split。  
因此不能把 v4 held-out 称为“表级未见测试”，也不能用它支持跨表泛化或总体率。未来确认集必须按 table / source document 隔离。

## 6. 已有事实 / 代理指标 / 待验证主张

| 项 | 状态 | 说明 |
|---|---|---|
| 59/59 held-out 标签可独立重算 | `FACT` | 工程复现性成立，audit 0 mismatch |
| checker 读取在 label freeze 之后 | `FACT` | 读取顺序与哈希链成立 |
| `visible_frozen` = matcher 未吸收 | `FACT` | 精确定义见第 3 节 |
| dev/heldout 9 个表 UID 重叠 | `FACT` | injection-level split，非 table-disjoint |
| E/H/U 是任务语义 gold | `UNVERIFIED` | 未定义真实任务、参考答案与容许变化 |
| visible = 任务报警 | `WRONG` | 无显式报警规则；visible 只是 matcher 行为 |
| co_miss/co_alarm 是 FNR/FPR | `WRONG` | 只是代理条件率，不是独立任务 gold 下的漏检/误报 |
| 存在多个 checker 的共同盲点 | `UNVERIFIED` | v4 没有多 checker 路径共享实验 |
| 0-13 OCR-like 边界与 v4 一致 | `UNVERIFIED` | v4 是 header binding，不是 OCR 面板复算 |
| 论文可以升级为真实任务测量结论 | `NOT_YET` | 需先建立 task-level reference gold |

## 7. 允许进入稿件的表述

允许：

- “Under the frozen column-local lexical binding contract, all 59 held-out labels were independently reproducible, and the rule left 12/59 cases undecidable.”
- “In this controlled split, `visible_frozen` denotes whether the audited matcher absorbed the injected header; it is not by itself a task-level alert.”
- “Against the frozen lexical proxy labels, checker-invisible cases were mostly legal variations (10/11), with one harmful case; checker-visible cases included 19/48 legal variations.”
- “The dev/held-out split is injection-level and has 9 overlapping table UIDs; it cannot support table-level or population generalization.”

禁止：

- “We established a task-level gold.”
- “The checker has a harmful blind spot.”
- “co_miss/co_alarm are FNR/FPR.”
- “Multiple checkers share a common blind spot.”
- “The result shows document-AI/OCR blindness.”
- “The held-out set is an unseen table-level test set.”
- “The rule is correct because it is self-consistent.”

## 8. 不覆盖的历史事实

本裁决不覆盖、不重估：

- v1 的 `GOLD_NOT_ESTABLISHED`
- v2/v3 的 `STOPPED_BY_GOVERNANCE`
- v4 的 verdict、标签、hash、契约、manifest、lock、audit
- Paper E 的 claim matrix、scope lock、冻结数字与 manuscript

## 9. 结论

当前 v4 的正确科学位置是：**测量仪器的工程可行性证据**，不是任务语义有效性证据。  
要进入 Layer-2，必须先完成 task-level reference gold 的可操作定义与人工资格核验；否则只能保留为论文的测量方法警示与工程可复现附录。
