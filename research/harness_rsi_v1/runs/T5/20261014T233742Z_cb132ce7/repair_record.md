# T5 v3 修复记录

- Run：`20261014T233742Z_cb132ce7`。本包只执行 T5R-02 指定返工；不进入 T6，不做 git 写入，不修改其他任务文件。
- BLOCKING：交付 P01 改用 `max_tick_age_minutes=0`，与 recipe 声明一致；P09 的有界 tick 在外部临时 runtime 根生成。删除 run 内 prepare 路径，README 以无前置、交付树只读的 `scratch/verify_replay.py` 为唯一入口。
- BLOCKING：`run_probes.py` 收集全部 23 个用例后统一返回；失败路径由对抗检查实测 rc=3 且仍保留末例记录。
- NEW-1：validator 内嵌 interfaces/operations SHA-256，注册目标按 git blob 字节身份在执行前复算；scope 限定为 delivered, identity-verified registry。
- NEW-2：全矩阵失败行为有独立证据。
- NEW-3：新增异源 pin 文件与 E10 探针；同时声明摘要内容充分性不在 validator 范围。该夹具只证明文件级来源分离。
- NEW-4：JSON error_surface 缩进已规整。评审 dissent-2 未实施，仅保留为后续可选项。

<!-- SUMMARY-GUARD
artifact: research/harness_rsi_v1/runs/T5/20261014T233742Z_cb132ce7/receipt.json
sha256: 285c808d1cb65c0c93f7534866e3f9550d11333a28b73d42d7bd39dea0e53a90
claims:
  usage.final_acceptance_caller_processes = 92
  self_check.overall = CONTRACT_PASS
END-SUMMARY-GUARD -->
