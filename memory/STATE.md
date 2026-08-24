# memory/STATE.md
更新: 2026-08-24 03:15（夜间自主 loop 第二阶段收口: T0 MCP 重载闭环 / T1 减 step A/B 判定还原 / T2 Loop B STEP 10 上线 / T3 backlog 首波 / T4 14B 异常复测定论）

## 模式
守护模式。等拍板: ① 甲方首轮反馈（B4 时钟 08-12 启动）② 专利件导师五项定夺反馈（三件已发导师 08-22 晚）③ 超时 (a) 45→60-75s——等 08-24 23:50 cron 48h checkpoint 数据（判据预写: 段 C+D 完成率 <10% → 再议, ≥10% → 维持）④ 五项用户决策备忘录 D1-D5 圈选（docs/experiments/2026-08-23_user_decision_memos.md）⑤ M4 减 step 下一杠杆（T1 已证 top_k 变体无效; 菜单剩 M3 终答瘦身 / M1 playbook 预注入 / 结构性减 step 3→2）
本轮已关闭: T0 泄漏修复闭环（MCP 重载 + pg 贴底零增长 + 持久化复验）/ T1 减 step 第一杠杆 A/B（判定=还原）/ T2 Loop B STEP 10 pg_pool_guard 上线（演练+四周期验证）/ T3 backlog 首波（docs_lint 头部三件套 + runner 盘点入库）/ T4 14B>8B 异常复测（可复现定论）
**48h 观察期（至 08-24 晚）**: 判定挂起（08-24 22:25 用户指令）——段 D 塌方归因已闭环（红旗 1+2 同根: 池×GUC 化学反应, 见下）, 段 D 数据被污染, 超时 (a) 待修复后干净段数据再拍; 23:50 cron 照跑收原始数据; 段起点 3429, 02:08 checkpoint 累计 337 尝试/51 完成/回落率 84.9%, 今日 218/4=1.8%（塌方值, 污染段）
**红旗 1+2 归因闭环（08-24 22:37, 报告 2026-08-24_segment_d_q06_attribution.md）**: 实例缓存长驻池 × GUC idle_session_timeout 10min × 无 pre_ping × smart_retrieve 吞异常 × 兜底冒充检索; 证据 = IdleSessionTimeout 216 条逐周期对上 + 双窗复现 + MCP 池同病; 修复菜单 F1 pre_ping+recycle / F2 异常不吞 待批（需 :5050 窗）; 次生: 僵尸 run 超时不 abort（F4 另卡）

## Git
- HEAD: 1196ee9（08-24 夜间 loop 第二阶段收口, 本回填 commit 后终态）; 上轮 9445f06; 三方对齐 GB10=GitHub=本机
- 本轮资产: Loop B STEP 10 pg_pool_guard + write_report 11 参 + status.sh PG/db 两行 / docs_lint [2b] 头部三件套 WARN 检查 / T1 减 step A/B 报告（判定还原）/ T4 14B 复测报告（可复现定论）/ T0 MCP 重载存档 / dispatch 8 行

## T1 减 step 第一杠杆 A/B（判定=还原, 01:42）
- 选杠 M2-top_k 变体（top_k 5→8 + follow-up 收紧）; 报告 docs/experiments/2026-08-24_t1_step_reduction_ab.md
- Arm A 13/13 p50=49.6s steps p50=4 mean=4.4（全量日志重提, 更正 00:48 缓冲假象）; Arm B 13/13 p50=48.9s（Δ−0.7s 噪声）steps p50=4 mean=4.85 且诱导 evidence-verifier 子代理; 质量门禁 14/16（2 FAIL 直连路瞬态抖动, 复测 2/2 非回归）
- 结论: 45s 超时审查为第一障碍, prompt 层微调在延迟维度无法显形; keep 判据未达 → 还原（sha 逐字一致 + 冒烟 q06 PASS）
- 后续: 第一梯队 = 结构性减 step（M4 3→2）+ 超时口径决策（48h 数据）; top_k↑诱导子代理入观察指标

## T4 14B>8B 异常复测（定论=可复现, 03:09）
- 14B 07-10 snapshot 双档与 C1 逐题一致: off 11/16（富熙系亚秒拒答）/ xhigh 14/16（q08+adv_ocr_meta）; 归因=权重/量化批次/模板行为 > 参数量; NO-GO 维持; 唯一未排除变量=新权重
- 报告 docs/experiments/2026-08-24_t4_14b_anomaly_retest.md; :8007 探针用毕即停（30G→33G 归位）

## Loop B（STEP 10 已上线）
- STEP 10 pg_pool_guard（warn>80/fail>95, flag LOOP_B_PG_POOL 默认 1）: 阈值演练 00:52 FAIL 触发正确; 真实周期 00:56/01:00/01:32/02:06 connections 9/9/9/8 全 OK
- daemon 唯一新脚本（2385039 起, 双旧进程更正坐实）; STEP 9 02:06 OK = canary 真实 agent 完成 1 条（02:03:30, 43.4s 预算内, fell_back=false）
- 周期实录: 01:00/01:32 overall=FAIL（STEP 9 设计内信号, 当时段 0 完成）; 02:06 overall=PASS

## B4（分段, 两列口径 尝试/完成 写全名）
- 侧车修复后段（段起点 3429, 08-22 14:38:33）: 累计 **337 尝试 / 51 完成**, 回落率 84.9%, p50=48.8s（02:08 checkpoint）
- 今夜 T1 分段: A 段 行 3698 @00:36 / B 段 行 3728 @01:04 / 质量门禁段 行 3741 @01:21 / 还原点 行 3761 @01:42; 段内全回落（审查效应）, 02:03 canary 1 条真实完成
- 明晚 23:50 cron 按预写口径判定（段 B 污染降权）

## 服务
- :5050 UP（PID 2300096, 08-23 23:27:09; route=on, timeout=45, embeddings=137; 今夜零重启）; :8004 A3B UP（M1 热路径锁定）; :8006 非 DSpark 生产 UP（GMEM 0.30, 观察期配置不动）; :8008 UP; :8007 空闲（T4 用毕已停）; :8005 DOWN（退位断言）; :15432 PG UP（GUC 10min, 连接贴底 8-14 零增长）
- opencode 侧车 PID 2418792 UP（01:42 T1 还原重启起; 序列 1189803→00:32 kill, 2357848→01:04 Arm B 注入重启, 2418792=还原后）; MCP 三子进程随侧车重生载修复
- Loop B 30min 周期 PASS@02:06（canary 4/4 / STEP 9 OK / STEP 10 OK）; kiosk 正式关闭（08-22）

## 质量基线
- eval 08-22: M1 PASS / 确定性 16/16 / NF 0/9 / judge 5.0
- L1 矩阵 08-23: medium/xhigh 两腿 NO-GO, 准路默认维持 thinking=OFF
- pytest: **384 passed / 13 skipped**（08-24 03:12 收口全量, logs/graph/pytest_latest.txt; Loop B 子集已分流 pytest_loopb.txt）
- docs_lint: PASS（GB10 为准, 本机 autocrlf 结构性 FAIL 不采信）

## 专利三件（已发导师 08-22 晚, 等导师五项定夺反馈; 主线程不碰）
- md 737 行 hash F8A4B0…61F931635A6 / docx v2 hash 48FF2A…45DC01BC（入 git）/ 邮件草稿 hash 7E39CF…E84E109A6（INDEX 登记）; v1 7954BB… 留本地不入库
