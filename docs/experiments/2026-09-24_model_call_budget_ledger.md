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

- label_ledger 装配器审计三轮（qwen3.8-max, 各 1 turn）: 0.3195 (PASS_WITH_NOTES) + 0.1895 (REJECT, F1 残口) + 0.1522 (PASS_WITH_NOTES, F1 关闭确认); 落盘 docs/experiments/2026-09-24_loopc_audit_label_assembler*.md 三件。
- 累计更新: 主仓会话 45 turns / $5.0332; 加 canary 3、分支 5、被 kill 上限 38 ⇒ ≤91 < 200。
- 合同 bindings 守卫审计（qwen3.8-max, 1 turn, $0.1098）: PASS_WITH_NOTES; 落盘 docs/experiments/2026-09-24_loopc_audit_contract_bindings_guard.md。累计主仓 47 turns / $5.1430；含 canary 3、分支 5、被 kill 上限 38 ⇒ ≤93 < 200。

## 7 回写（2026-09-25）

- 双模型独立审稿 v2（对象 = 稿件 §6 新增两段与 claim SP-C5，即上次 ACCEPT 之后的增量）：
  canary 2 turns（qwen3.8-max → `QWEN_OK`、deepseek-v4-pro → `DS_OK`）+ 审稿 2 turns（各 1 turn，
  bare 模式不报 cost）。同一 packet（61 097 B，sha256 `ef6ddc7a…`），两会话并发、互不可见、不 resume、
  不带工具，GB10 PID 3812664 / 3812665，均正常退出无 stderr。输出逐字落盘
  `docs/experiments/2026-09-25_loopc_review_teacher_review_v2_qwen3.8-max.md` 与
  `…_deepseek-v4-pro.md`，差异对照表 `…_loopc_review_v2_divergence_table.md`。
  判定均为 REVISE，且独立收敛到同一条 Blocking（"under any proportional assignment" 全称量化被自引 artifact 反驳）。
- 09-25 其余各波（SPLIT 分层仪器、语料 v1、检测器 v1/v2、论文 §6 增补与 manifest SP-C5）均为零模型调用。
- 累计更新：主仓会话 49 turns；加分支 5、canary 5、被 kill 上限 38 ⇒ **≤97 < 200**，未触顶、未 top-up。- 确认性复核（第 3 轮，修订后的 §6 与 SP-C5）：canary 0（沿用同日已验证路由）+ 复核 2 turns
  （qwen3.8-max PID 3828335、deepseek-v4-pro PID 3828336，各 1 turn，bare 模式不报 cost，无 stderr）。
  packet 25 937 B，sha256 `801193769790242aa69cb0d3558e84adad3d98716865ddb51246a71c5fc46fc4`。
  两模型判定均 **ACCEPT**；落盘 `docs/experiments/2026-09-25_loopc_confirm_review_v2_{qwen3.8-max,deepseek-v4-pro}.md`。
- 累计更新：主仓会话 51 turns；加分支 5、canary 5、被 kill 上限 38 ⇒ **≤99 < 200**，未触顶、未 top-up。- 大论文三件边界同步批的独立审计（qwen3.8-max，1 turn，bare 模式不报 cost，PID 3851836，约 21 分钟，
  stderr 空）：packet 103 376 B，sha256 `e6f718bbf1fd810fff8d51eb3b0abfce2459c9ab3a3c3c75cb89f343ac239d86`；
  判定 **PASS_WITH_NOTES**（1 MEDIUM + 5 LOW），落盘
  `docs/experiments/2026-09-25_loopc_audit_thesis_boundary_sync.md`。
- 累计更新：主仓会话 52 turns；加分支 5、canary 5、被 kill 上限 38 ⇒ **≤100 < 200**，未触顶、未 top-up。- 窄范围放行确认（第 5 轮，双模型）：2 turns（qwen3.8-max PID 3890701、deepseek-v4-pro PID 3890703，
  各 1 turn，bare 模式不报 cost，均正常退出 stderr 空）。packet 20 014 B，sha256
  `bf086dff371053e8a207f08d1db9fd62678d4d0630c54c353622cf2a6cc5783d`；审计 head `12e5e398…`。
  两模型判定均 **ACCEPT**，四条放行条件全部满足；落盘
  `docs/experiments/2026-09-25_loopc_confirm_review_v2_round5_{qwen3.8-max,deepseek-v4-pro}.md`。
- 累计更新：主仓会话 56 turns；加分支 5、canary 5、被 kill 上限 38 ⇒ **≤104 < 200**，未触顶、未 top-up。- 全链路独立审计（第 6 轮，qwen3.8-max，1 turn，bare 模式不报 cost，GB10 PID 3903468，约 12 分钟，stderr 空）：
  packet 178 438 B，sha256 `826905f8050845b11c5d644a564354ebdab1fc0b22f6e764191e8311e2de15e9`，
  审计基线 head `e357e11`。判定 **PASS_WITH_NOTES**（无 HIGH；2 MEDIUM + 6 LOW），并给出引用门判定
  「小论文 §6 对 0.0298 / 0.2233 的引用可以保留」。落盘
  `docs/experiments/2026-09-25_loopc_audit_step_checkpoint_chain.md`。
  派发偏差如实记录：首次以 `-p "$(cat packet)"` 传参触发 `nohup: 参数列表过长` 立即退出（stderr 74 B、无输出），
  改 stdin 重定向后成功；先用小 prompt 验证 stdin 通路（STDIN_OK）再派发，未换模型、未缩减 packet。
- 累计更新：主仓会话 57 turns；加分支 5、canary 5、被 kill 上限 38 ⇒ **≤105 < 200**，未触顶、未 top-up。
## 8 回写（2026-10-11，Track P round 1）

- Loop C fresh-context 设计挑战（Track P 候选集，1 turn，rc=0）：2026-10-11T05:36:45Z → 05:42:24Z（约 5m40s）；路由 = Loop C 默认（launcher 任务 `positive-repair-challenge-c-20261011`，无 override）；packet 12,094 B，sha256 `93151e01…`；输出落档 `research/positive_repair_20261011/loop_c_challenge_result_raw.log`（18,806 B，sha256 `3ea95284…`）。
- 台账说明：本件自 2026-09-25 后未逐次回写（09-26..10-10 期间调用记录在各 receipt/审计件头部）；本次仅登记本轮调用。登记口径：主仓会话 +1 turn ⇒ 58；canary 5、分支 5、被 kill 上限 38 不变 ⇒ 上限口径 ≤106 < 200，未触顶、未 top-up。
## 9 回写（2026-10-11，Track P round 2：prereg 修订 + 双轮审计）

- prereg audit v1（4 份 prereg；packet 16,152 B sha256 `82d68ec3…`）：1 turn，rc=0，约 12m20s；输出 `research/positive_repair_20261011/loop_c_prereg_audit_result_raw.log`（21,933 B，sha256 `5b8333f6…`）；判定 CONDITIONAL×4。
- prereg re-audit（v2 修订版；packet 27,078 B sha256 `18205b14…`）：1 turn，rc=0，约 31m38s；输出 `research/positive_repair_20261011/loop_c_prereg_audit_recheck_result_raw.log`（5,527 B，sha256 `a437792b…`；首段捕获缺失已记录）；判定 PASS×4。
- 累计更新：主仓口径 +2 turns ⇒ 60；canary 5、分支 5、被 kill 上限 38 不变 ⇒ ≤108 < 200，未触顶、未 top-up。
- 备注：本轮另有 Codex 协作子代理会话（3 mining + 1 qualification）与 4 个 Loop A、1 个 Track A 执行任务；执行任务按完成时各自 num_turns 登记（另见 round_receipt_v2.json）。
- addendum（2026-10-11 16:1x）：Loop A 基建层两轮 fail-closed（a1 INPUT_MISSING×4、a2 HASH_MISMATCH×4）与 r3 重派详见 `round_receipt_v3_dispatch_amendment.json` / `round_receipt_v4_hashfix.json`；Loop A 执行任务不计入本台账历史口径（各自运行时路由记账）。

## 10 回写（2026-10-11，Track P round 1 closeout：四个 post-result audit + Track A reviewer audit）

- PR-EXP-01/03/04/07 post-result audits（Loop C，fresh context，packet-only）：各 1 turn，rc=0；packet 80,705 / 60,715 / 79,021 / 37,864 B；输出 `research/positive_repair_20261011/loop_c_postaudit0{1,3,4,7}_result_raw.log`（14,224 / 17,723 / 15,379 / 19,444 B）。
- Track A reviewer-attack claim audit（Loop C）：1 turn，rc=0；packet 66,802 B；输出 `track_a_reviewer_attack_audit_result_raw.log`（34,915 B）。
- 累计更新：主仓口径 +5 turns ⇒ 65；canary 5、分支 5、被 kill 上限 38 不变 ⇒ ≤113 < 200，未触顶、未 top-up。（Loop A 执行任务另计：a1×4 + a2×4 基建失败已隔离；r3×4 各 ≥1 turn，见 round_receipt_v2/v3/v4 与 registry。）