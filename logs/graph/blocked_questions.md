# blocked_questions.md（夜间队列歧义/缺前置登记, 2026-08-25 建）

> 规则: 歧义/缺前置 → 登记一行（时点/问题/缺什么/跳项去向）, 不停车; 白天判定一页纸时统一过目。

（今夜暂无 — 截至 00:50 各 W 前置齐备）

[2026-10-10 17:37] FinQA v2 minimal binding-v2 rerun 缺什么：仓库与已检索会话日志中没有任务 `finqa-v2-binding-audit-c-20261010` 的独立完整报告，也没有可验证的 `SCORER_BINDING_GO = PASS` 结论；跳项去向：执行步骤 4-10 全部停止，未创建 `results_binding_v2_rerun/`、未调用 scorer、未计算 V/D/O/estimands/bootstrap；补齐要求：提供独立 Loop C 报告或按 `research/finqa_v2_binding_audit_loop_c_task_contract.md` 完成审计后再重验。

[2026-10-10 17:53] 已解除：`docs/experiments/2026-10-10_loop_c_finqa_v2_binding_v2_audit.md` 已给出 `SCORER_BINDING_GO = PASS` 与 `VERDICT: PASS`；新门在 scorer 执行前重验通过，正式执行随后按冻结规则以 `BINDING_TRACE_MISMATCH` 的 89/89 失败停为 `FORMAL_RUN_INVALID`，不构成原缺报告问题。
