# TQ-4 Authorization Items v2 (AWAITING - independent authorization required)

> state: `AWAITING_SPECIFIC_AUTHORIZATION_V2`
> 本文件列出运行 TQ-4 所需的最小授权字段；**不得复用 TQ-3 单次授权**。
> 运行方：Loop D（可委派 Loop A 执行、Loop C 复核，均不新增模型实验预算）。

- G1 模型 pin：提案沿用 GB10 现役配置（Qwen3.6-35B-A3B-Q4_K_M.gguf @127.0.0.1:8004，参数同 TQ-3）；
  运行前重新核对文件哈希/模型 ID/model_path，漂移即停。需 owner/总规划师确认或另选。____
- G2 预算：36 计划请求 + 重试 <= 4 + 总上限 40；token 上限提案 400,000；费用上限 USD 0（本地）。____
- G3 窗口（新）：允许启动日期与时段（09:00-18:30）；单窗口 <= 90 分钟；20:00 前停止；单次运行。____
- G4 runner 实现授权：按 RUN_CARD_v2 第 8 节增量规格实现（预计 <= 1 天，不改核心 harness）。____
- G5 运行环境：GB10 执行；输出根 `tq4_calibration_v1/runs/<run_id>/`；两端镜像与哈希核对；runs/ 不入 git。____
- 附加确认：Part 1/Part 2 分开记账；C 标签"同模型、独立上下文、可见候选答案"；不按 B/C 分歧调题。____
