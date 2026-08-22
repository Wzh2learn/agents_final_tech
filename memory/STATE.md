# memory/STATE.md
更新: 2026-08-22 15:00（侧车修复专项收口: 选项 1 重启 + 选项 2 db 重建执行完毕 / 楔死解除但验收①未达成=延迟预算问题, 拍板三选项待裁 + 专利三件收口 + L1 runbook 补丁）

## 模式
守护模式。**等用户拍板（最高优先）: 侧车修后判定三选项 a) OPENCODE_ASK_TIMEOUT 45→60-75s（需 :5050 重启窗口）b) 准路根治杠杆（减 step 等）c) 维持现状**（证据与归因见 dispatch #SIDECAR-VERDICT）。
等拍板: ① 甲方首轮反馈（B4 时钟 08-12 启动）② 专利件用户终审 + 亲发导师（三件已冻结收口）③ kiosk A1 方案窗口 ④ L1 矩阵窗口（08-23 晚, runbook 已补丁就位）
已关闭: 侧车楔死诊断与修复（08-22 完成, 归因重记入账）/ L1 基线口径（a）/ L3 路径（A）/ D3 k=5 作废 / cron 24h 条目已删 / "content=null 首要怀疑" CLOSED

## Git
- HEAD: 本收口 commit; 三方对齐 GB10=GitHub=本机
- 本轮资产: 侧车修复四项存档 + db 重建备份与恢复 SOP / dispatch 三条（#SIDECAR-RESTART / -DB-REBUILD / -VERDICT）/ 专利三件收口（md + docx v2 入库 + 邮件草稿, 三 hash 台账, v1 不入库）/ L1 runbook 补丁（P6/P7 前提 + 还原第 6 步侧车状态行）/ INDEX 登记

## 侧车修复专项（2026-08-22, 拍板圈 1 → 预授权升级选项 2）
- 存档四项: logs/graph/eval/sidecar_restart_archive_0822.txt（旧 PID 1483419 = 08-17 22:49 起 / db 表行数 / json+jsonc sha256 / env 快照 ~/.sidecar_env.bin chmod 600）+ 日志尾 200 行
- 重启（新侧车 PID 1189803, 14:37:35 起）→ 预热 1 完成 50s, "exiting loop" 14:32:34 重现 = 验收②✓; 生产 2 发 46.1/46.7s 超时 → 按预授权进选项 2
- db 重建: ~/.local/share/opencode/backup_20260822/（db/shm/wal 三 sha256 + 恢复 SOP 在 dispatch #SIDECAR-DB-REBUILD）; 重建后零争用仍 0 完成: step 节奏恢复健康时代（5/12/12/12s）但需 5-6 步 ≈46-60s > 45s 预算
- **判定: 楔死解除✓, 验收①（B4 route=agent 完成）未达成 = 延迟预算问题, 非侧车故障**; 三选项已报拍板, 未擅自抬超时/重启 :5050
- 归因重记: DSpark era 190/0 与"准路不可用"结论保留, 归因更正为侧车楔死（起点 08-20 22:46 早于切换）, DSpark 切换/回滚不背 agent 路失败

## B4（回滚点 3295 分段）
- 回滚点段 128 尝试 / 0 完成（三段核查: kiosk 94 / eval 窗 30 / 手工 4）→ 难度分层假设证伪 → 系统诊断 → 侧车楔死根因
- 侧车修后: kiosk 尝试仍超时回落（46-50s）, 与判定一致; 待 a/b/c 拍板后分段观察
- 口径注记: 两列口径（尝试/完成）汇报统一写全名, "83.4%" 类单数字必须注明是回落率还是完成率（#B4-NAMING）

## 服务
- :5050 UP（route=on, timeout=45, embeddings=137, 不重启）; :8004 A3B UP（M1 热路径锁定）; :8006 非 DSpark 生产 UP（GMEM 0.30, 观察期配置不动）; :8008 UP; :8007 空闲; :8005 DOWN（退位断言）; :15432 PG UP
- opencode 侧车 PID 1189803 UP（14:37:35 起, --port 4096, db 已重建）
- Loop B 30min 周期: agent_watchdog ALARM = **设计内信号**（准路 0 完成期间预期持续, 记台账不当事故; 拍板后应自解）
- kiosk 播放中（每条 QA 46-50s 超时回落, 观感待拍板）

## 质量基线
- eval 08-22（经 :5050 生产端点）: M1 PASS / 确定性 16/16（全部 direct 回落）/ NF 0/9 / judge 四维 5.0
- pytest: 379 passed / 13 skipped（08-22 全量 168.7s, logs/graph/pytest_latest.txt 全量工件）
- docs_lint: GB10 为准

## 专利三件（08-22 收口, 用户终审后亲发导师, 主线程不碰）
- md 737 行（§1-§8 + 附录 A/B）hash F8A4B0…61F931635A6
- docx v2 hash 48FF2A…45DC01BC（入 git; 呈递说明已移出正文, "老师好/呈递说明/请您定夺"零命中）; v1 hash 7954BB… 留本地不入库
- 邮件草稿（呈递说明独立件）hash 7E39CF…E84E109A6, INDEX 已登记
- 侧线临时件已清理（10 项, 含额外发现的 _tmp_patent_full.txt）

## 下一步
1. **用户拍板侧车修后 a/b/c** —— 准路恢复的前置, 减 step 菜单收益的前置
2. 08-23 晚窗口（另批）: **L1 thinking 档位裁定矩阵** medium/xhigh 两腿, runbook = docs/experiments/2026-08-22_l1_matrix_runbook.md（已补丁: 腿直连 :8006 时侧车非硬前置, 经 :5050 路则是; 还原清单第 6 步记窗口起点侧车状态）
3. 矩阵解读框架 = L2 定论（step 数主导）+ 08-22 三段核查（数据引用不重复复述）
4. L3: 盯 timothystewart6 新 tag; **08-29 checkpoint** 无 tag → 路径 B 再评估报告
5. 杠杆序（记账, 拍板后实施）: 减 step（M4 组合 34s→19s −44%）+ 孤儿终结 > context 瘦身 > thinking 档位（质量维度）
6. 缓办: 甲方反馈 → B4 分布分析; kiosk A1 窗口; C4 VL-8B; K3 批跑; NLPCC 核实
