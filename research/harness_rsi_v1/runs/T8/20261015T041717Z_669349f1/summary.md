# T8 — R 受控影子边界执行摘要

- **影子状态**：`NOT_SATISFIED_NO_THREE_TASK_WINDOWS`，逐任务 0/3 执行；三张结果表均为空并标 `NOT_EXECUTED_MISSING_APPROVED_WINDOW`。依据是 T8 卡 `execution_authorized=false`、当前派发明确“无三个新获批任务窗口”、owner note 与 MASTER_PLAN 均把三任务窗口列为未满足前提。
- **身份绑定**：R 复合组 `sha256:e16cde27ff239da0c7b76f35272e0950e1cb9f0878d464b0ae6629e88d4c4f86`；T5 v3 @`115f396` 45/45、T6 @`ef5e84e` 30 成员、T7 @`0579b64` 57 成员，三棵被绑定路径在对应 commit 下均未漂移。T5 父组复算 PASS，T6/T7 候选 SHA-256 与各自 ACCEPTED 评审记录一致。
- **安装/装载边界**：均 `NOT_ESTABLISHED_NOT_INFERRED_FROM_REPOSITORY`；仓库存在不证明已安装或已装载。
- **回滚**：`PASS_SIMULATED_ONLY`；逻辑 base→shadow→base 恢复后复合/组件哈希一致，11 件旧证据的 SHA-256、字节、模式与 git blob 均零改。实际部署回滚因从未启用而未验证。
- **建议**：`release_proposal.json` 仅建议在获得三个新获批任务窗口后启动影子；启用与精确分发继续由用户按 §7 裁决。本包未启用、未分发、未改 skills 或全局配置。
- **预算**：SHADOW 额外便宜 `0/6`、强模型 `0/2`；网络/远程/生产/数据库/训练/daemon/Loop B/自动重试均 0；执行对话 token 为 `UNRESOLVED`。
- **自检**：A1 如实 `NOT_SATISFIED`；A2 身份/验收一致 `PASS`；A3 旧证据零改与零越权请求 `PASS`；A-common 与 G1 以最终只读复算为准；三轴 `DELIVERED / UNREVIEWED / NOT_ENABLED`。

阻断/owner 门：① 三个新获批任务窗口与时间均缺；② 启用与精确分发待用户 §7 裁决。不得进入 T9。

<!-- SUMMARY-GUARD
artifact: research/harness_rsi_v1/runs/T8/20261015T041717Z_669349f1/shadow_comparison.json
sha256: adbfcb90adb2b10b60e455f187369c5897752da7bd70735584e2d9057949c871
claims:
  shadow_status = NOT_SATISFIED_NO_THREE_TASK_WINDOWS
  authorization_scope_check.authorized_new_task_window_count = 0
  authorization_scope_check.required_new_task_window_count = 3
  usage.additional_cheap_requests = 0
  usage.additional_strong_requests = 0
END-SUMMARY-GUARD -->
