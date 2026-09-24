# 模型调用预算台账（2026-09-24 汇总，D3 硬上限 <200）

> 状态: 台账件（2026-09-24, Loop D）| 口径: 以会话 turns 作为模型调用代理计数（packet 会话每会话 1 turn；
> 带工具会话按 num_turns）；canary 按次计；被 kill 会话 turns 未终局、记上限不记实测。
> 所有成本取自已落盘审计/复审件头部的 self-reported cost（主仓件）或分支件头部（注明）。

## 1 主仓已落盘会话（9 个 packet 会话 + 1 个带工具会话）

| 会话 | 模型 | turns | cost USD | 落盘件 |
|---|---|---|---|---|
| 初审 qwen | qwen3.8-max | 1 | 0.9051 | docs/experiments/2026-09-24_loopc_review_teacher_review_qwen3.8-max.md |
| 初审 dspro | deepseek-v4-pro | 1 | 0.2682 | docs/experiments/2026-09-24_loopc_review_teacher_review_deepseek-v4-pro.md |
| 复审 qwen | qwen3.8-max | 1 | 0.2287 | docs/experiments/2026-09-24_loopc_rereview_teacher_review_qwen3.8-max.md |
| 复审 dspro | deepseek-v4-pro | 1 | 0.1129 | docs/experiments/2026-09-24_loopc_rereview_teacher_review_deepseek-v4-pro.md |
| confidence 草案审计 | qwen3.8-max | 1 | 0.1550 | docs/experiments/2026-09-24_loopc_audit_confidence_manifest_draft.md |
| schema 审计（REJECT） | qwen3.8-max | 1 | 0.1248 | docs/experiments/2026-09-24_loopc_audit_schema_role_reject.md |
| schema 复审 | qwen3.8-max | 1 | 0.1068 | docs/experiments/2026-09-24_loopc_audit_schema_role_reaudit.md |
| analysis_plan 审计 | qwen3.8-max | 1 | 0.1815 | docs/experiments/2026-09-24_loopc_audit_analysis_plan_template.md |
| 两运行器审计 | qwen3.8-max | 1 | 0.3153 | docs/experiments/2026-09-24_loopc_audit_phase1a_runners.md |
| ONLINE 卡报告（带工具） | qwen3.8-max | 31 | 1.7857 | GB10 分支 gb10/lc-research-20260924 reports/LC-RESEARCH-001-ONLINE.md 头部 |

主仓小计：**40 turns / $4.1840**。

## 2 canary（3 次）

| canary | 模型 | 结果 | request_id |
|---|---|---|---|
| 1 | mimo-v2.6-flash | FAIL HTTP 400 Model not exist | d904c6d9-d91c-4bd2-83cc-b022810425ed |
| 2 | mimo-v2.6-pro | FAIL HTTP 400 Model not exist | 711a3af0-ba21-414c-bf9a-de85b4d4afcc |
| 3 | qwen3.8-max | PASS（stdout DS_OK） | 未记录（成功 canary 无 request_id 留痕） |

## 3 分支落盘会话（成本记于分支件头部）

GB10 分支 gb10/lc-research-20260924：OFFLINE 报告审计 1 turn、ONLINE 报告 1 turn（$0.3117）、
ONLINE 审计 1 turn；GB10 分支 gb10/loop-c-lead-20260923：GOV 审计 1 turn、GOV 复审 1 turn。
小计 5 turns（其中 $0.3117 已知，其余见分支件头部）。

## 4 被 kill 会话（无终局计数）

audit2 与 review_qwen2（首轮带工具、error_max_turns 前被 kill）：turns 未终局，上限分别 20 / 18；
streams 留 /tmp/lc_audit2.stream 与 /tmp/lc_review_qwen2.stream 备查。按上限计 ≤38。

## 5 上限核对

已计 turns = 40（主仓）+ 5（分支）+ 3（canary）= 48；加被 kill 上限 38 ⇒ **≤86 < 200**，未触顶、未 top-up。
后续每次派发须在对应审计/报告件头部记录 turns 与 cost，并回写本件。

## 6 回写（2026-09-24 晚）

- 确认性复审（camera-pass a0f4d3d vs ACCEPTed 4de4741）: qwen3.8-max, 1 turn, $0.1880, 落盘 docs/experiments/2026-09-24_loopc_confirm_review_camera_pass.md; 判定 ACCEPT, 两 minor 关闭, 零数字/保护结果/主张范围漂移。
- 累计更新: 主仓会话 41 turns / $4.3720; 加 canary 3 与分支 5 turns 及被 kill 上限 38 ⇒ ≤87 < 200。
