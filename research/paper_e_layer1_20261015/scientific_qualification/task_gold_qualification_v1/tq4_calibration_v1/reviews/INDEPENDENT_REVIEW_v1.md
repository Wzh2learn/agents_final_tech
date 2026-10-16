# TQ-4 独立复核 v1（聚焦：评分器修复 / 旧结果解释 / 新面板设计）

> 2026-10-16｜复核方：原委派独立复核代理 `loopc_tq4_review`（fresh context；非包作者）｜只读独立复算，零模型调用
> 基线：`tq4_calibration_v1/`（commit `4b64d9c`；复核时点本地 = origin/main）
> 机器记录：`INDEPENDENT_REVIEW_RECOMPUTE_v1.json`；复算脚本：`INDEPENDENT_REVIEW_RECOMPUTE_v1.py`

## 0. 交付说明（供编排层归档时并入 `REVIEW_STATUS_v1.md`）

- 本件为**延迟交付**。原委派任务简报与往返消息因 harness **消息投递故障**丢失，复核代理未收到任务简报；
  编排层据此记录了"委派失败"，并以其对抗式自审作为暂代（已正确标注为非独立）。
- 复核代理实际在线可用：本件由该代理对冻结件**独立复算**后产出（全部检查为本次实跑，不引用任何既有自审结论；
  逐项结果见复算记录 JSON）。
- 同类佐证：同批最小探针 `loopc_tq4_mini` 实际已完成任务并返回正确载荷
  （`PROBE_COUNTS={"items":12,"v1_match":12,"v2_match":12,"changed":0}`），其完成消息亦未被编排层接收。
  证据支持"消息投递（双向）故障"而非"代理不可执行"的故障定性。
- 编排层收尾建议（5 项）：① 更新 `REVIEW_STATUS_v1.md` 中 attempt-1 的结果记录；② 回填 `TQ4_PACKAGE_RETURN.md` §6；
  ③ 更新 `README.md` 的 reviews/ 行；④ 重跑 `tq4_finalize.py`（将本件 3 个文件纳入清单）；⑤ commit。

## 1. 结论摘要

| 范围 | 结论 | 依据（本次实跑） |
|---|---|---|
| A 评分器修复（v2 语义 + 回归套件） | **PASS** | 独立重跑回归 18/18；8 处 v1→v2 状态翻转逐项复现（R1a/R1b/R2/R3/R4/R5）；记录内两模块 sha256 与磁盘一致 |
| B 旧结果解释（12 条重评分 + 两句纠正） | **PASS** | 独立重评分：12/12 两版均 MATCH、0 变更；v2 合法性视图 12/12 非法（22 处 kind_invalid）；§3/§4 纠正在证据上成立 |
| C 人工候选面板（12 份冻结） | **PASS** | 矩阵与顺序精确（3 题 x 4 条件）；合法性独立重算 12/12 与标签一致；输入/候选文件哈希复核一致；错答构造符合规范 |
| D 自然任务面板（N1-N4 冻结） | **PASS** | S1-S4 各一；语料与文件哈希重算一致；表体拼接/表头替换/输入与语料逐元素一致；unit_kind 与容差规则符合规范；参考答案自检 4/4 MATCH |
| E 运行卡 v2 与授权项 v2 | **PASS** | 规模 36=12+24、重试<=4、上限 40、单并发；C 标签逐字在场；G1-G5 与"不得复用 TQ-3 授权"在场 |
| F 完整性（清单/提交态） | **PASS** | 根 MANIFEST 46/46、面板 26/26 逐项哈希一致；无缺件；runs/ 与 __pycache__ 正确排除（另有本件 3 个新文件待编排层注册，见 §3F） |

无阻断性问题；非阻断注记 1 条（§4）。

## 2. 复核方法

- 只读：所有检查在**不改动冻结树**的前提下重执行（Python 字节码写入禁用；模块仅从原路径导入）。
- 独立重执行：A/B/C/D 的全部判定均为本次重新计算（评分器实跑、合法性重算、哈希重算、语料重比、
  数据集记录抽查），并与冻结记录逐项对照（含行级对照）；不采用"引用既有结论"的捷径。
- 复算口径与本包既有脚本同源（避免口径漂移）：回归 fixture 与 runner 同源；重评分映射沿用
  `Q10=ratio; Q03/Q04/Q12=plain`；合法性使用 `check_evidence_legality`（机械层）。

## 3. 逐项结果

### A 评分器修复

- 回归：18/18 通过；`v1_v2_status_differences=8`，与冻结 `regression_results.json` 的 counts 完全一致；
  翻转覆盖 case：`R1a-percent-false-reject`、`R1b-percent-false-accept`、`R2-multi-number-cherry-pick`、
  `R3-list-no-substring`、`R4-no-guessing-numeric`、`R5-date-parse`。
- 模块哈希：冻结记录内 v1/v2 sha256 与磁盘文件逐一一致（v2 即 `scorer_v2/tq4_scoring_entry.py`）。
- 语义抽查（本次新增探针）：`5%` + plain -> `UNSCORABLE_PERCENT_MARKER_ON_PLAIN_UNIT`；
  多数字回答 -> `UNSCORABLE_MULTIPLE_NUMBERS`；列表 superset -> `NO_MATCH`；列表 reorder -> `MATCH`。
  行为与 `SCORER_FIX_NOTES.md` 一致。

### B 旧结果解释

- 独立重评分：12 条旧 actor 输出（run `20261016T051556Z_af4c2db6`），v1 与 v2 全部 MATCH（changed=0），
  与冻结 `rescore_results.json` 行级一致。
- v2 合法性视图：12/12 非法，22 处 `kind_invalid`（计数复核一致）。
- 两句解释纠正的复核结论：`MATCH != 完整正确`（有 8 处 v1/v2 翻转 + 三类已实证缺陷支撑）与
  `5 个报警 != 假警报`（旧协议未定义索引基，v2 视图下全部证据 schema 非法）均在证据上成立，无过度更正；
  边界表述（不视为 gold、不改 canonical 记录、只重解释）恰当。

### C 人工候选面板

- 12 份、矩阵精确（Q02/Q03/Q04 x {correct,incorrect} x {legal,illegal}）；顺序 C1..C4 与规范一致。
- 合法性重算：12/12 与标签一致（legal 组合法；illegal 组为越界 cell / 未知 paragraph uid）。
- 哈希：`inputs/Q02|Q03|Q04.json` 与 `CANDIDATES_LOG.input_hashes` 一致；
  `candidates_v1.json` 与 log 记录的 sha256 一致。
- 错答构造复核：Q02-C3 = 两项子集；Q03-C3 = -14054；Q04-C3 = 3。与 `CANDIDATE_BUILD_SPEC_v1.md` 一致。

### D 自然任务面板

- 每个 stratum（S1-S4）恰一题（N1-N4，各带 original/perturbed/reference/scoring）。
- `SELECTION_LOG.json` 的 `corpus_hashes`（5 个语料文件）与 `files`（每题目 4 个文件）重算全部一致。
- 拼接标准独立重比：4 题全部满足 `source[uid][0][col] == original_header`、
  `injected[uid][0][col] == injected_header`、其余行完全一致；`N*_original/_perturbed` 输入表与语料逐元素一致。
- 数据集记录抽查：4 题在 train/dev 记录中的 uid、问题 uid、答案存在且数值化均成立。
- 规则复核：`unit_kind`（N1/N3=percent；N2/N4=plain）与"'%' 在 derivation 中"规则一致；
  `abs_tolerance = 0.5 x 10^-d`（d=参考答案规范串小数位）4/4 一致；参考答案用 scoring 文件打分自检 4/4 MATCH。

### E 运行卡与授权项

- `RUN_CARD_v2.md`：计划 36=12+24、基础设施重试 <= 4、总上限 40、单并发；
  C 标签逐字 "同模型、独立上下文、可见候选答案"。
- `AUTHORIZATION_ITEMS_v2.md`：G1-G5 全在场；明确"不得复用 TQ-3 单次授权"；预算/窗口/环境字段齐备。

### F 完整性

- 根 MANIFEST：46/46 条目哈希与字节数一致；`manifest_self_excluded=true`；`runs/` 仅 `.gitignore` 入册；
  无 `__pycache__`。面板 MANIFEST：26/26 一致。清单与磁盘集合相等（无遗漏）。
- 盘上另有本次复核交付的 3 个文件（本件、复算 JSON、复算脚本）尚未注册清单 —— 属预期的待编排动作，
  由收尾建议第 ④ 步覆盖。
- 复核时点提交 `4b64d9c`（本地 = origin/main）。

## 4. 非阻断注记（1 条，供未来版本参考；不要求修改本冻结版本）

- **N-1（加固，低优先）**：`check_evidence_legality` 对 cell 坐标使用 `isinstance(x, int)`；
  Python 中 `bool` 是 `int` 子类，实测 `{"table_row": true, "table_col": 0}` 会被当作行 1 通过边界检查。
  本包全部证据均由机械构造或人工冻结产生、无此形态，不影响任何现有结论；若未来接入自由形式的外部输出，
  建议改为 `type(x) is int`（或显式排除 bool）并随新版本发布。

## 5. 边界与声明

- 本复核为只读独立复算：无模型调用、无网络、未修改任何冻结件（含面板、评分器、清单、旧材料）。
- 本件不改变 canonical 记录、不签发 gold、不构成对 TQ-4 运行结果的任何预判。
- "独立"指复核方非包作者且检查为独立重执行；复核方在撰写前可访问包内状态文件（含自审记录），
  但本件所有结论均有本次实跑证据支撑（见复算记录 JSON）。
