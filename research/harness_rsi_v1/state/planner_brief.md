# 规划者入口

状态：协议已由 owner 签署冻结（freeze_sha256 `282f52133a682e927c82b771fa103c27da34db7acbd8a12d2921f42a6d0bf36b`，2026-10-14）；T-1(v2) 与 T0 已验收；R 线（至 M1）获授权；C/S 线未授权。
下一步：T1（可靠性事故案例整理，B0、零模型调用）。
落地注记：评审包与 T0/T-1 运行包均未被改动；记录层小瑕疵已在 registry 的 closer_note 事件中说明。authority_map 已按 1A 以 canonical blob id 重钉（旧值存 local_snapshot_raw_sha256_historical）。

[2026-10-14] T1 已验收（T1R-03 ACCEPTED；v3 run 20261014T141004Z_2647a7e1）。评审 ID 命名冲突已修复：T-1 评审恢复至 reviews/T1R-01、T1R-02；事故案例任务评审迁移至 reviews/T1I-01..03。下一步：T2（独立评价底座）。

[2026-10-15] T2 已验收（T2R-01 ACCEPTED，零阻断；advisory A 系列已在 registry 登记）。评价器 34/34×2、三退化策略全失败硬门、6 fail-closed；Loop A 自检 PASS。下一步：T3（可信执行与计数）。
