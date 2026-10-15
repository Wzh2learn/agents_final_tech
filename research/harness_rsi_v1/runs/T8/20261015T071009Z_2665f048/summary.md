# T8 v2 影子执行摘要

- `shadow_status`: `NOT_EVALUABLE`
- 结论：三个旧流程均完成；三个 T5 v3 新流程均在目标分派前以 `FC_ARBITRARY_PATH` 拒绝，旧/新等价性为 0/3。
- 发布建议：`DO_NOT_RELEASE` / `HOLD`。
- 范围：只读本地影子执行；零模型、零网络；不构成 GB10 运行、生产、数据库、模型端点或科学资格声明。

## 三个窗口

| 窗口 | 旧流程 | 新流程 | 对比 |
|---|---|---|---|
| 1 TAT-QA 许可记录 | `COMPLETED_WITH_FINDINGS`：2244 bytes；license=true，permitted/covered/accepted=false | `NOT_EVALUABLE`：`FC_ARBITRARY_PATH`，未执行目标 | `parity=false` |
| 2 WP-1 合同哈希 | `PASS`：实算 SHA-256 与 sidecar 一致 | `NOT_EVALUABLE`：未进入哈希绑定评估 | `parity=false` |
| 3 状态一致性 | `PASS`：10/10 accepted task run 目录存在 | `NOT_EVALUABLE`：无任意 JSON 结构验证操作 | `parity=false` |

## 包件状态

- `rollback_receipt.json`: `PASS_READ_ONLY`
- `release_proposal.json`: `DO_NOT_RELEASE`
- G1: 所有本 run Markdown 必须通过 `scripts/graph/hooks/summary_recompute_guard.py check`
- usage: orchestrated model requests = 0；network = 0；automatic retries = 0
- `execution_chat_usage`: `UNRESOLVED`
- `UNRESOLVED`: T5 v3 对三个真实目标缺少登记操作，无法判定新流程正确性；独立验收未执行。

<!-- SUMMARY-GUARD
artifact: runs/T8/20261015T071009Z_2665f048/shadow_comparison.json
sha256: b8d1805f6ed467895008621282bfe573efa1f420154f378875b63d84c243b029
claims:
  counts.windows = 3
  counts.new_not_evaluable = 3
  promotion_eligible = false
  shadow_status = NOT_EVALUABLE
END-SUMMARY-GUARD -->
