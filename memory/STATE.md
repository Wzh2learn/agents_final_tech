# memory/STATE.md
更新: 2026-08-22 13:50（白天队列收口: B4 三段核查 + 侧车楔死根因定论报拍板 + L1 runbook 就位 + NF 参数化补丁 + 减 step 菜单 + eval 08-22）

## 模式
守护模式。**等用户拍板（最高优先）: opencode 侧车楔死处置 ①重启侧车进程 ②重建 opencode.db ③维持现状**（证据链见 docs/experiments/2026-08-22_b4_agent_route_diagnosis.md, THREADS 条目在案）。
等拍板: ① 甲方首轮反馈（B4 时钟 08-12 启动）② 用户专利终审 + 导师时间表（专利件冻结, 用户亲发）③ kiosk A1 方案窗口 ④ L1 矩阵窗口（08-23 晚, runbook 已就位）
已关闭: L1 基线口径（拍板=a）/ L3 路径选择（拍板=A）/ D3 k=5 随 DSpark 退出作废 / cron 24h 条目已删

## Git
- HEAD: 本收口 commit; 三方对齐 GB10=GitHub=本机
- 本轮资产: B4 诊断报告 + 三段核查 / 减 step 菜单 / L1 runbook / NF+矩阵脚本参数化 / INDEX 登记 3 条 + CRLF 归一 / THREADS 侧车条目 / pytest_latest 全量修复

## B4 核查点（2026-08-22 白天, 数据说话）
- 回滚点 3295 起 128 尝试 / **0 完成**, 三段回落率均 100%: kiosk 94 / eval 窗(12:58-13:27) 30 / 手工 4（含 2 手工验证行）
- 判定: "kiosk 题难度分层"假设**证伪**（eval 16 确定性题 + 手工轻量题同样 0 完成）→ 升级系统诊断
- **根因定论 = opencode 侧车交付链楔死**（非模型栈/step 数/超时值; 故障起点 08-20 22:46 早于 DSpark v3 切换; 侧车进程 08-17 起未重启）; 处置三选项报用户拍板, 未擅自变更
- 口径注记: 全量 "83.4%" 是回落率（完成率=323/2027=15.9%）, 两列口径汇报统一写全名（#B4-NAMING）

## 服务
- :5050 UP（route=on, timeout=45, embeddings=137, 不重启）; :8004 A3B UP（M1 热路径锁定）; :8006 非 DSpark 生产 UP（GMEM 0.30, 观察期配置不动）; :8008 UP; :8007 空闲; :8005 DOWN（退位断言）; :15432 PG UP
- Loop B 30min 周期: agent_watchdog ALARM = **设计内信号**（侧车楔死期间预期持续, 记台账不当事故）
- kiosk 播放中（每条 QA 46-50s 超时回落, 演示观感待侧车修复）

## 质量基线
- eval 08-22（经 :5050 生产端点）: M1 PASS / 确定性 16/16（全部 direct 回落 ~46-50s）/ NF 0/9 / judge 四维 5.0
- pytest: 379 passed / 13 skipped（08-22 13:46 全量, 168.7s, logs/graph/pytest_latest.txt 已修复为全量工件）
- docs_lint: GB10 为准

## 下一步
1. **用户拍板侧车处置**（①重启侧车 ②重建 opencode.db ③维持现状）——准路恢复的前置, 减 step 菜单收益的前置
2. 08-23 晚窗口（另批）: **L1 thinking 档位裁定矩阵** medium/xhigh 两腿, runbook = docs/experiments/2026-08-22_l1_matrix_runbook.md（还原第一项=生产配置未动验证; P3 注入冒烟为窗口第 0 步）
3. 矩阵解读框架 = L2 定论（step 数主导）+ 本日三段核查（数据引用不重复复述）
4. L3: 盯 timothystewart6 新 tag; **08-29 checkpoint** 无 tag → 路径 B 再评估报告
5. 杠杆序（记账, 侧车修复+矩阵后实施）: 减 step（M4 组合 34s→19s −44%）+ 孤儿终结 > context 瘦身 > thinking 档位（质量维度）
6. 缓办: 甲方反馈 → B4 分布分析; kiosk A1 窗口; 专利终审用户亲发; C4 VL-8B; K3 批跑; NLPCC 核实
