# TQ-3 旧输出重评分报告 v1（v2 评分器）

> 日期 2026-10-16；只读重算（12 条已保存 actor 输出），未重跑任何模型；TQ-3 原始运行报告与材料未覆盖（本文件为新增修订件）。
> 数据：`rescoring/rescore_results.json`（逐条 v1/v2 状态 + v2 合法性视图）。

## 1. 方法

- 12 条输入：`runs/20261016T051556Z_af4c2db6/raw/0001..0012_actor_*.json` 的 `parse.result`。
- v1 = `tools/tq3_scoring_entry.py`（冻结）；v2 = `scorer_v2/tq4_scoring_entry.py`。
- 模式映射（仅重评分用）：列表题 `span_containment_normalized -> list_full_match`；数值题新增 `unit_kind`（Q10=ratio；Q03/Q04/Q12=plain）；日期题不变。
- 未修改任何旧文件；未新增模型调用。

## 2. 结果：新旧状态差异 = 0

- 12/12：v1 MATCH -> v2 MATCH（无变化）。
- 含义：这 12 条输出在更严格的 v2 规则下仍然成立（单数字、完整列表、明确日期均未触发缺陷路径）。

## 3. 解释纠正 1：不能把"12/12 MATCH"称为"答案完整正确"

- v1 存在三类已实证缺陷（百分数按数值大小、多数字任取、列表子串命中）；回归套件显示 8 处 v1↔v2 状态翻转
  （`scorer_v2/regression/regression_results.json`）——即同样的 lenient 规则在其他输入上会失准。
- 因此"12/12 MATCH"只能说明：本样本未触发缺陷路径，且在 v2 规则下同样成立；
  MATCH 是"与冻结参考在既定评分规则下一致"的判定，不是人工 gold，也不等于"完整正确"。
- 旧措辞"答案 MATCH 即完整正确"废弃；替换为："在 v2 评分规则下与冻结参考一致/不一致"。

## 4. 解释纠正 2：不能把 5 个 A 报警称为"假警报"

- v2 合法性视图：12/12 旧输出的 evidence **全部 schema 非法**（缺少 `kind` 字段），共 22 处 `kind_invalid`；
  旧协议下不存在"合法 evidence"样本。
- 因此"五个报警均是假警报"不成立，应为：
  (a) 当时协议未定义索引基/类型，报警与否取决于未冻结的假设（0 基），本身不可裁定；
  (b) 以 v2 协议看，全部 12 份（含 7 份当时"通过"的）证据都是 schema 非法——旧 A 层的 accept/alarm 划分是未定义协议下的伪区分；
  (c) 5 个报警仍不构成语义错误的证据（与答案正确性无关），但也不应被"假警报"一词洗白。
- 替换表述："5 个报警是未定义协议下的不可裁定项；v2 协议下全部 12 份证据为 schema 非法。"

## 5. 回归证据（支持第 3/4 节的实测）

- 18/18 检查通过；8 处 v1↔v2 状态翻转，覆盖：R1 百分数（false reject + false accept）、R2 多数字 cherry-pick、
  R3 列表（superset/subset/reorder）、R4/R5 解析失败不猜测；正确样例保持不变。

## 6. 边界

- 本报告只重解释，不改变 canonical 运行记录（RECEIPT/RESULTS/SUMMARY 原样）；不重开 TQ-3 分支；不把 v2 结论称为 gold。
- 旧材料（TQ-3 全部文件）保持只读。
