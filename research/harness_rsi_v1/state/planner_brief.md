# 规划者入口

状态：协议已由 owner 签署冻结（freeze_sha256 `282f52133a682e927c82b771fa103c27da34db7acbd8a12d2921f42a6d0bf36b`，2026-10-14）；T-1(v2) 与 T0 已验收；R 线（至 M1）获授权；C/S 线未授权。
下一步：T1（可靠性事故案例整理，B0、零模型调用）。
落地注记：评审包与 T0/T-1 运行包均未被改动；记录层小瑕疵已在 registry 的 closer_note 事件中说明。authority_map 已按 1A 以 canonical blob id 重钉（旧值存 local_snapshot_raw_sha256_historical）。

[2026-10-14] T1 已验收（T1R-03 ACCEPTED；v3 run 20261014T141004Z_2647a7e1）。评审 ID 命名冲突已修复：T-1 评审恢复至 reviews/T1R-01、T1R-02；事故案例任务评审迁移至 reviews/T1I-01..03。下一步：T2（独立评价底座）。

[2026-10-15] T2 已验收（T2R-01 ACCEPTED，零阻断；advisory A 系列已在 registry 登记）。评价器 34/34×2、三退化策略全失败硬门、6 fail-closed；Loop A 自检 PASS。下一步：T3（可信执行与计数）。
[2026-10-15] T3 已验收（T3R-01 ACCEPTED，零阻断；advisory A1-A8 登记，A1 升级条件保留待 owner；审阅者 .omc 残留已按 A8 清理）。可信执行 runner：234 文件包、manifest 233/233 复算零失配、8/8 绑定三方法一致、两遍独立复跑 32/32 且归一化哈希与声明一致、14 次 mock 传输分项重算一致、零外部调用、LOCAL_DEV_HOST 标注。下一步：T4（R 适配器与基线）。
[2026-10-15] T4 已验收（T4R-01 ACCEPTED，零阻断；advisory A1-A3 登记）。v1 因「收据守卫 vs 故意失配夹具」不可提交 → v2 返工（守卫合规化 + 运行时派生失配），提交序列 v2=579a8ca、评审=50da8e0；守卫实弹全绿、11 组合×2 回放一致、画像 6/2/2/6、零外部调用。A1 消费约束：下游读 baseline 须以 case-level 为准。下一步：T5（R 两个对象接口）。
[2026-10-15] T5 首轮评审 T5R-01=REJECTED（2 blocking：执行位交付缺失使 17/17 主张不可复现；自洽伪造摘要 X06 穿透 A2；另 6 advisory）。Loop D 裁决：交付执行位 + manifest 记 mode + fresh-delivery 模拟；摘要接受须外部 pin（未 pin/不符即拒）。进入 T5 v2 返工，随后 T5R-02。
[2026-10-15] T5 第二轮评审 T5R-02=REJECTED（1 blocking：重放不稳定——陈旧 tick + 就地改写 manifest 绑定夹具，42/42 不可从交付字节复现；4 advisory；另有 attempt1 非合规废件）。修复方向：交付字节零写入重放 + 全矩阵收集 + registry/目标身份 pin。进入 T5 v3，随后 T5R-03。
[2026-10-15] T5 第三轮 T5R-03=REJECTED（1 blocking：4 个 manifest 声明 755 的模式未随交付落地→入口 rc=3；T5R-02 blocking 已被独立确认闭合；另 4 advisory）。Closer 修复：115f396 模式补丁（零内容变更）+ GB10 工作树 chmod 755 + 清理评审窗口遗留 pyc（未披露，已登记）；重放 rc=0、45/45 复现。进入 T5R-04 聚焦复评。
[2026-10-15] T5 已验收（T5R-04 ACCEPTED，零阻断；链条 v1→v3 三次 REJECTED + closer 模式修复 115f396 后聚焦复评通过；advisory A1-A4 登记；dissent X06C 边界记录）。两个 recipe 接口 + 23/23×4 无前置重放 + 外部 pin + 身份校验 registry。下一步：T6（有界提案与统一档案）。
