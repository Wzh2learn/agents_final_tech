# T5 v3 返工

- Run：`20261014T233742Z_cb132ce7`；只修复 T5R-02 的 replay-stability blocking 并折叠 NEW-1..4，不进入 T6。
- 无前置重放：README 入口对交付态运行 current-tree 两轮与 fresh-delivery 两轮，均为 23/23，归一化结果逐项一致；交付树和复制树重放前后 SHA-256/bytes/mode/mtime_ns 不变，manifest 45/45。
- 时间稳定性：P01 使用 `max_tick_age_minutes=0`；P09 的 60 分钟界在外部 runtime 临时目录生成。交付 tick 不改写，run 内不存在 prepare 路径。
- `run_probes.py` 收集全部 23 例后统一判定；对抗首败场景 rc=3 且 23 条记录完整。
- NEW-1：interfaces/operations 内嵌 SHA-256，目标按 git blob 身份复核，scope 为 delivered, identity-verified registry；NEW-3 异源 pin 文件；NEW-4 缩进规整。
- 本包仅给 `CONTRACT_PASS`（范围：当前 run 包字节、调用边界、无前置重放证据、G1 与 B0 写入边界）；不是科学 PASS、正式实验资格、`END_TO_END_PREFLIGHT_PASS` 或 `FORMAL_RUN_PASS`。独立验收 `UNREVIEWED`，启用 `NOT_ENABLED`。

<!-- SUMMARY-GUARD
artifact: research/harness_rsi_v1/runs/T5/20261014T233742Z_cb132ce7/receipt.json
sha256: 285c808d1cb65c0c93f7534866e3f9550d11333a28b73d42d7bd39dea0e53a90
claims:
  usage.final_acceptance_caller_processes = 92
  self_check.overall = CONTRACT_PASS
END-SUMMARY-GUARD -->
