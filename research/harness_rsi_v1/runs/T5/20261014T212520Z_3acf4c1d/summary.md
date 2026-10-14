# T5 v2 返工

- Run：`20261014T212520Z_3acf4c1d`；仅修复 T5R-01 的 2 个 blocking 并折叠 6 个 advisory，未进入 T6。
- BLOCKING-1：`recipe_fixtures/dispatch/watcher.sh` 交付模式 `100755`；manifest 逐件记 mode 并列 `required_executables`。fresh-delivery 先对副本全件 `chmod -x`，再按 manifest 恢复 32 件模式；P01 与全量矩阵均通过。
- 探针：fresh PASS_1 与 current-tree PASS_2 各 21/21，合计 42/42；每轮 `ACCEPT=4 / REJECT=17`，归一化结果逐项一致。
- BLOCKING-2：摘要接受要求声明哈希 == 运行时实测哈希 == 调用方可信记录中的外部 pin；无 pin → `FC_ARTIFACT_NOT_PINNED`，错 pin → `FC_PIN_MISMATCH`，正确 pin → 接受。校验器不防调用方故意递假 pin，该威胁边界已显式声明。
- Advisory：ADV-1/2/3/4/5/6 均有可复核工件；T4 仅消费 `baseline.cases[]`；操作显式固定 `cwd`；边界扫描包含 gitignored 文件。
- 本包仅给 `CONTRACT_PASS`（范围：本 run 的接口、字节/模式、调用方拒绝、G1、本地只读探针与写入边界）；不是科学 PASS、正式实验资格、`END_TO_END_PREFLIGHT_PASS` 或 `FORMAL_RUN_PASS`。独立验收 `UNREVIEWED`，启用 `NOT_ENABLED`。

<!-- SUMMARY-GUARD
artifact: research/harness_rsi_v1/runs/T5/20261014T212520Z_3acf4c1d/receipt.json
sha256: 3afcba34d426a9695adf46793522fd9d2baebccfb691cede9832213dbc427573
claims:
  usage.final_acceptance_caller_processes = 42
  self_check.overall = CONTRACT_PASS
END-SUMMARY-GUARD -->
