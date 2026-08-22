# L1 thinking 档位裁定矩阵报告 (medium / xhigh)

- 任务卡: docs/experiments/2026-08-22_l1_matrix_runbook.md (TASK-20260823-01)
- 执行窗口: 2026-08-22 23:30 - 2026-08-23 00:53（用户批准提前, 原 08-23 晚）
- 端点: http://127.0.0.1:8006/v1/chat/completions 直连（qwen38-27b-fp8, 非 DSpark 回滚栈, GMEM 0.30 观察期）
- 题库: tests/fixtures/m2_eval_questions.json（16 确定性题, 冻结只读）+ NF 9 题 + judge 四维抽样（:8004 35B, rubric v_k1）
- off 列: 不重跑, 引 08-22 eval 与 B4 历史数据（口径注记: off 现状已有生产数据）

## 一、结论一句话

**NO-GO**: 两腿均不构成"准路默认降档候选"。thinking 开启无延迟收益（单步直连 p50 56-58s, 远高于 off 现状）; medium 质量降（13/16 + NF 1/9 + judge 4.67 < 4.9）; xhigh 质量持平线（16/16 + NF 0/9）但 judge 4.875 略低于 4.9 闸门、且低于 off 基线 5.0。08-19 "xhigh 起步"批复由数据正式作废。**准路默认维持 thinking=OFF**; thinking 档位定位为质量维度（xhigh 可作用户可选"深度"档）; 延迟根治第一梯队仍为减 step（M4）+ L2 瘦身。

## 二、三方对照表

| 指标 | off（历史基线） | medium | xhigh |
|---|---|---|---|
| 口径来源 | 08-22 eval 经 :5050 + B4 | 本窗直连 :8006 | 本窗直连 :8006 |
| 确定性 16 题 | 16/16 | 13/16 * | 16/16 |
| NF 9 题（未落地数） | 0/9 | 1/9 | 0/9 |
| judge faithfulness | 5.0 | 4.62 | 4.81 |
| judge numeric_correctness | 5.0 | 4.69 | 4.69 |
| judge citation_quality | 5.0 | 4.69 | 5.0 |
| judge refusal_appropriateness | 5.0 | 4.69 | 5.0 |
| judge 四维均分 | 5.0 | 4.67 | 4.875 |
| wall_ms p50 / p95 | direct 46-50s（:5050 口径） | 55855 / 121943 | 57729 / 137149 |
| reasoning 字符 p50 / p95 | 0 | 524 / 961 | 574 / 1418 |
| completion_tokens p50 | — | 435 | 450 |

\* medium 13/16 构成: 2 例 markdown 转义判分假象（q02/q07, 答案实质正确, 掩码 `****` 被渲染为 `\*\*\*\*`, contains_keyword 字面匹配过敏）+ 1 例 adv_multiturn 180s/turn 超时（§四）。即便剔除两例假象, medium 仍因 NF 1/9 + judge 4.67 不过闸门。

## 三、窗口事件: 测量盲区与 runner 补丁（方法论记录）

1. 首冒烟两腿 `reasoning_tokens` 恒 0 → 按 runbook 中止条款停腿（未带假设硬跑）。
2. 诊断: 注入本身有效——原始 A/B 直发（难度题）: xhigh reasoning 2571 字符 > medium 1529 字符; 顶层 reasoning_effort 与 chat_template_kwargs 注入行为一致（2571 == 2571）。
3. 根因: 本 vLLM build（v0.27.1-gb10.1）不产 `usage.completion_tokens_details`（实测 details=None）, runner 只读该字段 → 恒 0; reasoning 文本实际在 `message.reasoning` 字段。
4. 补丁: `scripts/run_matrix_candidate.py` ask_candidate 加 fallback——details 缺省时以 `len(reasoning)`（字符数）估算并注明口径（runbook 口径注记预告的退化场景, 非新口径）。报告新增 `reasoning_chars` / `reasoning_caliber` 字段。
5. 冒烟复跑 PASS: medium 606 字符 / xhigh 517 字符（q01 简单题, 档位差小为题目特性; 档位区分度已由难度题 A/B 实证）。

## 四、异常与假象台账

1. **q02_minan_positions / q07_boshi_fund_code（medium 腿）**: 答案实质正确, 掩码值在 markdown 表格中渲染为 `\*\*\*\*` → 判分器字面匹配失败。判分器 markdown 转义容忍 = 已知后续项（不改变本轮裁定）。
2. **adv_multiturn（medium 腿）**: 180s/turn 超时（[candidate error]）; 同题 xhigh 腿 PASS（58.6s）。超时与档位无关, 疑受当窗争用/题目方差影响; 多轮 + thinking 的超时口径留档。
3. **NF medium adv_june_cross_period**: 答案含无根据数字 '07'（跨期诱导陷阱命中）→ NF 1/9; xhigh 同题 0/9 通过。**思考档位对跨期诱导抗性有实际作用**（本矩阵唯一正向质量信号）。
4. NF 脚本 rc=1 = "存在失败"退出码（报告已正常写入）, 非基建故障; 两腿 NF 报告均在位。

## 五、争用注记（不掩饰）

窗口期间 Loop B 金丝雀照常（30min 周期, Loop B 00:41:07 周期 PASS）。两腿 p95 离群（medium 121.9s adv_cross_doc / xhigh 137.1s q02）与 reasoning 长度正相关（548-1418 字符）→ 主因长思考; 金丝雀争用叠加不能排除但无独立证据。

## 六、go/no-go 裁定（引 runbook 判据）

判据: 质量不降（16/16, NF 0/9, judge ≥4.9）且延迟实质下降 → 候选; 质量降 → 数据入账, 准路维持现状, 重心转减 step 第一梯队。

- medium: 质量降（13/16, NF 1/9, judge 4.67）→ **NO-GO**
- xhigh: 通过率/NF 持平但 judge 4.875 < 4.9 闸门, 且无延迟收益（p50 57.7s ≫ off 直连 46-50s / 快路 1.3-2s）→ **NO-GO**
- 裁定: 准路默认维持 thinking=OFF（现状不动）; xhigh 记账为用户可选"深度"档菜单项（优势: citation/refusal 5.0 + 跨期诱导抗性; 代价: 单步 p50 ~58s）。

## 七、下游数据输入

1. **08-19 "xhigh 起步"批复**: 前提失效 → 本矩阵复测后正式作废（THREADS 更正条目同步）。
2. **N3 agent 超时抬升（45→60-75s）拍板输入**: off 单步 46-50s, xhigh 单步 p50 57.7s / p95 137s。抬超时到 60-75s 可容纳 off 多步轨迹, 但容纳不了 xhigh p95; 超时抬升与档位升级不应捆绑。
3. **延迟期望算术（实测拼接, 不外推）**: 准路端到端 ≈ step 数 × 单步 wall。off 3 步 ≈ 140-150s ≫ 45s 预算 → 减 step（3→2, M4 菜单）+ L2 瘦身是唯一进预算路径; 若未来启用 xhigh 深度档, 预算需按单步 ~58s 重算。

## 八、还原验证（runbook 验收清单, 全过）

| 声明 | 验证 | 实测 |
|---|---|---|
| 生产配置未动（还原第一项） | sha256sum 两份 opencode 配置窗前窗末 | 一致（8cb44e40… / 4e901f9e…）✅ |
| :5050 未受影响 | health/full 窗前窗末 | healthy / 137 / local 一致 ✅ |
| git status 无配置类 diff | git status --porcelain | 仅 docs/scripts/台账类 ✅ |
| 侧车状态 | :4096 窗前窗末 | 200 / 200 ✅ |
| 窗口起点侧车状态行（P7） | 快照 | 侧车 :4096=200; B4 段 3429 口径 65 尝试/11 完成, 回落率 83.1%（全超时回落）✅ |

## 九、执行耗时与工件

23:30:36 快照+首冒烟 → （诊断+补丁）→ 23:52 冒烟复跑 PASS → 00:13:26 medium 腿（21.4min）→ 00:30:20 xhigh 腿（16.9min）→ 00:42:16 NF medium（11.9min）→ 00:50:35 NF xhigh（8.3min）→ 00:51:45 judge medium（1.2min）→ 00:52:55 judge xhigh → 00:52:56 还原验证。总耗时 ≈ 1h 22min（含诊断补丁）。

工件（logs/graph/eval/）: l1_medium_report.json / l1_xhigh_report.json / l1_nf_medium.json / l1_nf_xhigh.json / l1_judge_medium.json / l1_judge_xhigh.json / l1_smoke_medium.json / l1_smoke_xhigh.json / l1_window_snapshot.txt
