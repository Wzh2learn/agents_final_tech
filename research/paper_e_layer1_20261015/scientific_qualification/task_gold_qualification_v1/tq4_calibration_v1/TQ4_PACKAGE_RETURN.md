# TQ4_PACKAGE_RETURN - TQ-4 校准执行包（离线准备完成）

> 2026-10-16｜Loop D（AI）｜本轮**零模型调用**（仅离线计算 + 一次独立复核委派）
> 对应裁决：D1 修订批准（协议修复 + 可失败样本）；D2 独立复核并入本轮（见 §6）；D3 暂缓大规模人工标注
> 状态：`PREPARED_AWAITING_AUTHORIZATION_V2`——未运行；TQ-3 单次授权已被消耗，不得复用

## 1. 交付物索引

| 组件 | 位置 | 内容/证据 |
|---|---|---|
| 评分器修复 | `scorer_v2/tq4_scoring_entry.py` + `SCORER_FIX_NOTES.md` | 百分数仅按显式单位；多数字不可任取；列表要求全集相等；不可解析不猜测 |
| 修复回归证据 | `scorer_v2/regression/` | 18/18 通过；**8 处 v1→v2 状态翻转**（含百分数 false-reject/false-accept、多数字 cherry-pick、列表 superset/subset/reorder、解析失败不猜测） |
| 旧输出重评分 | `rescoring/` | 12/12 v1=MATCH→v2=MATCH（0 变化）；v2 合法性视图：全部 12 份 schema 非法（22 处 kind_invalid） |
| 解释纠正 | `rescoring/TQ3_RESCORE_REPORT_v1.md` §3/§4 | 纠正"MATCH 即完整正确""5 个报警均是假警报"两句过强表述 |
| 证据协议 v2 | `evidence_protocol/EVIDENCE_PROTOCOL_v2.md` | cell/paragraph 类型；0 基坐标；段落用输入 uid；合法性与支持性分开记录 |
| 冻结面板 Part 1 | `panel_v2/natural/` + `NATURAL_SELECTION_SPEC_v1.md` | 4 个新自然任务 N1-N4（S1-S4 各一；选择顺序=哈希序+结构校验；输出前冻结；含 SELECTION_LOG 全轨迹） |
| 冻结面板 Part 2 | `panel_v2/candidates/` + `CANDIDATE_BUILD_SPEC_v1.md` | 3 题 x {对/错} x {引用合法/非法} = 12 份人工候选；合法性验证 12/12 通过 |
| 运行卡 v2 | `run_card_v2/` | 36 请求（12+24）、重试<=4、上限 40、单并发；两部分分开记账；C=同模型、独立上下文、可见候选答案 |
| 授权项 v2 | `run_card_v2/AUTHORIZATION_ITEMS_v2.md` | G1-G5 待签；明确不复用 TQ-3 授权 |
| 独立复核 | `reviews/INDEPENDENT_REVIEW_v1.md` | 聚焦复核（评分器修复 / 旧结果解释 / 新面板设计）——见 §6 |

## 2. 调用预算（下一轮，待授权）

- Part 1：4 x (actor+B+C) = 12；Part 2：12 x (B+C) = 24；合计 36；基础设施重试 <= 4；总上限 40；单并发；超时 120s/请求。
- 模型提案：沿用 GB10 `Qwen3.6-35B-A3B-Q4_K_M.gguf @127.0.0.1:8004`（运行前重新核对身份；漂移即停）。
- token 上限提案 400,000；费用 USD 0（本地）；窗口=**新窗口**（09:00-18:30 启动、<=90 分钟、20:00 前停）。

## 3. 与裁决的逐项对应

- "百分数按显式单位转换" -> §1 评分器修复第 1 条（回归 R1a/R1b）；
- "数值题不允许任取" -> 第 2 条（回归 R2：`UNSCORABLE_MULTIPLE_NUMBERS`）；
- "列表题不得局部子串命中" -> 第 3 条（回归 R3：superset/subset -> NO_MATCH）；
- "无法唯一解析 -> INVALID/UNSCORABLE" -> 第 4 条（回归 R4/R5）；
- "三反例+正确样例入回归" -> `scorer_v2/regression/tq4_regression_cases.json`（18 检查全通过）；
- "新版 evidence：cell/paragraph、0 基、输入 uid、合法性/支持性分开" -> `EVIDENCE_PROTOCOL_v2.md`（+ 运行卡 §5）；
- "旧输出重评分，不重跑、不覆盖" -> `rescoring/`（原报告未动，仅新增重评分件）；
- "四新自然任务（纳排+顺序冻结）" -> `NATURAL_SELECTION_SPEC_v1.md` + `SELECTION_LOG.json`；
- "3 题 x 4 候选，只跑 B/C，分开记账" -> `CANDIDATE_BUILD_SPEC_v1.md` + `RUN_CARD_v2.md`；
- "不强行标注 Q06/Q08/Q09" -> 两处规范均未引用其语义；保持隔离状态。

## 4. 冻结声明

- 所有面板材料在本轮冻结（各带哈希日志）；此后不因任何 B/C 分歧修改、替换或调题。
- 旧 TQ-3 材料全程只读；本包不改动任何旧文件。

## 5. 剩余人工/授权步骤（唯一）

1. owner/总规划师签署 `AUTHORIZATION_ITEMS_v2.md`（G1-G5 + 窗口日期）；
2. 授权后：实现 runner 增量（<=1 天）-> 点检 -> 单窗口执行 36 请求 -> 产出 `runs/<run_id>/` 与 `TQ4_RUN_RETURN.md`。

## 6. 独立复核（已完成 - 延迟交付）

- 独立复核件已交付：`reviews/INDEPENDENT_REVIEW_v1.md`（+ `INDEPENDENT_REVIEW_RECOMPUTE_v1.json` / `.py`），
  由委派的 fresh-context 复核代理产出；结论 **A-F 全部 PASS**、无阻断问题、1 条非阻断注记 N-1
  （bool 作为 int 的坐标加固，供未来版本）。
- 延迟原因更正：委派并非"代理卡死"，而是 harness **消息投递（双向）故障**——任务简报与完成回执丢失；
  同批最小探针亦实际完成（载荷正确）而回执未达。详见 `reviews/REVIEW_STATUS_v1.md`（已按时间线更正）。
- 历史替代件 `LOOP_D_ADVERSARIAL_SELF_REVIEW_v1.md/.json`（标注非独立）保留为过程记录，已被独立复核覆盖。
