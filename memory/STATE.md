# memory/STATE.md
更新: 2026-08-22 00:55（L2/L3 批复只读执行完毕, 收口三方对齐, 回守护模式）

## 模式
守护模式。本轮: L2 sidecar context 测量 + L3 DFlash2 镜像可行性（均纯只读, 零配置变更, 未拉镜像未重建）。
等拍板: ① **L1 基线口径**（生产 thinking 实际 OFF, 现接线 medium vs xhigh = off vs off; 08-23 跑前须裁定, 详见 THREADS 08-22 条）② **L3 路径选择**（A 等新 tag 推荐 / B 自建后备 / C 缓议）③ 甲方首轮反馈（B4 时钟 08-12 启动）④ 用户专利终审 + 导师时间表（专利件冻结, 用户亲发）⑤ kiosk A1 方案窗口
已关闭: D3 k=5 随 DSpark 退出作废; cron 24h 条目已删

## Git
- HEAD: 本收口 commit; 三方对齐 GB10=GitHub=本机
- 本轮资产: L2 报告 + JSON 工件 / L3 可行性备忘 / drafter ledger L3 复核节 / INDEX 两行 / THREADS/dispatch/STATE

## 本轮战绩
- **L2 定论**: 单调用 decode 60-70%（仅 ~45tok/请求, 带宽墙）/ prefill 30-40%（~10k, TTFT 0.5-5s）; attempt 级主导项 = 串行 step 数（p50=3/p95=5/max=15）× 每步 7-15s（与 B4 实测 46-50s 吻合）; prefill 主项 = opencode 内置 system prompt + 工具 schema（残差 8-10.5k 占 70-80%）
- **L2 关键更正**: 生产 m2-qa thinking 实际 OFF（证据四条）→ "xhigh 轨迹超预算"更正为"串行多步 × 每步 7-15s"; L1 矩阵基线口径须先拍板
- **L2 顺带记账**: 孤儿会话续跑（p95=133s, slot 白占）入 L2 方案菜单; opencode.db transcript 持久化损坏（08-14 起 5187 次插入失败）
- **L3 定论**: #52816 MERGED（08-21T05:27Z, b389ac2）但现镜像（0.27.2.dev0+g6e448d0ea.d20260815, 22.1GB, DFlash2DraftModel 全库零命中）与 v0.27.1 release（08-11）均不含; incoai 权重 3.85GB k=8 只查未下; 路径 A（等 timothystewart6 新 tag, 其 tag 实为 main 快照）推荐 / B（自建 0.5-1d）后备; 零动作报拍板

## 服务
- :5050 UP（route=on, timeout=45, embeddings=137, 不重启）; :8004 A3B UP（M1 热路径锁定）; :8006 非 DSpark 生产 UP（GMEM 0.30, 观察期配置不动）; :8008 UP; :8007 空闲; :8005 DOWN（退位断言）; :8100 UP; :15432 PG UP
- Loop B 30min 周期: 00:17 overall=FAIL = agent_watchdog ALARM（**设计内信号**, agent 完成未恢复前预期持续, 记台账不当事故）
- kiosk 播放中; B4: 回滚点 3294（08-21 23:51）, 现 3298; 分段: DSpark era 3093-3287 / 验证期 3288-3294 / 回滚后自 3295

## 质量基线
- eval: 确定性 16/16 + NF 0/9 + judge 四维 5.0
- pytest: 379 passed / 13 skipped（08-22 00:40 全量, 171s, logs/graph/pytest_latest.txt）
- docs_lint: GB10 为准

## 下一步
1. 08-23/24 错峰: L1 medium 矩阵——**前提 = 用户拍板基线口径**（off 现状 vs 显式注入 medium/xhigh; 08-16 数据 dense 27B 开 thinking 无结构化收益, 08-19 批复"xhigh 起步"与接线实况有口径落差）
2. L1 基线后: L3 探针（路径 A 批准 + 新 tag 就位时）→ :8007 等价性三连 + D2 口径分段接受率 → GO/NO-GO → 申请 :8006 窗口
3. L2 方案菜单（报批后动）: step 数削减 / 孤儿取消 / context 瘦身（残差 8-10k 为靶）
4. 盯梢: timothystewart6 新 tag（DFlash2）/ drafter v2 / incoai 权重镜像; 复核命令入 ledger
5. 缓办: 甲方反馈 → B4 分布分析; kiosk A1 窗口; C4 VL-8B; K3 批跑; NLPCC 核实
