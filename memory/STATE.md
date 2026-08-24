# memory/STATE.md
更新: 2026-08-25 00:05（池×GUC 修复窗执行: F1+F2 生效 / sanity 0.7889 / canary 4/4 / 门禁转 cron 工件; 执行节奏治理入账）

## 模式
守护模式。**明早第一单 = 《判定一页纸》**（新规则: 收集/判定分离——夜间只跑确定性执行, 判定移白天）: 池修复验证工件（pool_fix_verify_20260825.md）+ B4 池修复后段数据 → 超时 (a) 是否还需要 + T1 结论复测安排（T1 跑在池病活跃期, 疑似污染）, 用户白天圈选。
其余等拍板: ① 甲方首轮反馈（B4 时钟 08-12 启动）② 专利件导师五项定夺反馈（三件已发 08-22 晚）③ D1-D5 用户决策备忘录圈选（2026-08-23_user_decision_memos.md）④ M4 减 step 下一杠杆（菜单剩 M3 终答瘦身 / M1 playbook 预注入 / 结构性 3→2）
本轮已关闭: 池×GUC 修复窗（批准卡 08-24 + 节奏修正: 收集与判定分离 / sleep 链作废改工件模式）

## 池×GUC 修复窗（08-24 23:46-23:55 执行, 判定挂起）
- 根因（归因报告 2026-08-24_segment_d_q06_attribution.md）: 实例缓存长驻池 × GUC idle_session_timeout 10min × 无 pre_ping × smart_retrieve 吞异常 × 兜底冒充检索
- 窗前存档: logs/graph/eval/pool_fix_window_archive_20260824.txt（旧 PID 2300096 / env 45/on / db [51,368,907] / warn 基线 218）
- 补丁 2 文件: src/tools/vector_store.py（engine_args pre_ping=True + recycle=300）+ src/biz/rag_service.py（WARNING→ERROR + dispose 重试一次 + fallback_reason 显式 + 兜底冒充曝光日志）
- pytest 384 passed/13 skipped（195.99s）→ :5050 重启新 PID 3153034（env 45/on 不变; /api/health/full healthy: pgvector ok / embeddings 137 / retrieval_working）→ 侧车重启 pid 3153507 + MCP 三进程重生 3153592/94/96（新池载修复）
- sanity q06 = 3508.55 命中 **score 0.7889**（与归因复现暖池值逐字一致）; canary 4/4（对照病灶期 23:19 周期 3/4 FAIL）
- warn 218→219: 增量 23:47:08 = 重启前旧代码病灶残留（时间戳坐实）; 重启后零新警告, recovered=0（无需 dispose 救援 = pre_ping 已前置拦下）
- B4 池修复后段起点 **行 3929 @23:54**; 窗前 checkpoint 原始数据: 段 3429 累计 491 尝试/53 完成/回落率 89.2%（判定挂起, 污染段定性见归因报告）
- 门禁（12min 闲置后 q06 直问）= cron one-shot 00:16（闲置未达自动改期+7min, 至多 5 次后挂起; FAIL 自动回滚原参数重起）; Loop B 复验 = cron 00:40（canary 复跑 + 周期状态）; 工件均落 logs/graph/eval/pool_fix_verify_20260825.md, cron 跑完自删条目并自动提交工件
- 纪律（批复）: 除恢复每日 eval 外不排变更留干净段; Loop B 翻转应停, 不停先疑修复未生效
- 教训入账（任务卡模板 §8）: 多修复同窗必加"交互假设检查"（本案 = GUC 兜底 × 实例缓存化学反应, 单项验证全绿无一捕获）

## 治理新增（2026-08-25, templates/task_card_template.md §8 + AGENTS.md 同文）
- 主线程禁用 >5min 阻塞 sleep; 里程碑等待 = GB10 cron one-shot + 文件工件 + 结 turn; watcher/sleep 链模式作废（本窗已全杀, 进度零损失）
- 收集与判定分离: 收集保留夜间 cron（机器时间, 流量干净）; 判定移白天——每日上午《判定一页纸》（分段数据+选项+推荐+红线核对）; 任务卡不得把人类决策排在 22:00 后; 夜间窗口只执行已批准的确定性动作
- cron one-shot 三件套: 跑完自删条目 + abort/rollback 分支写死脚本 + 工件路径显式声明

## Git
- HEAD: 本收口 commit（窗口执行 commit e03326c 已推）; 三方对齐 GB10=GitHub=本机
- 本轮资产: src 2 文件补丁 / 窗前存档 / checkpoint 原始数据 / canary 工件 / 门禁+复验 cron 脚本（/tmp, 工件落 md）/ 治理规则两处 / STATE 覆写

## B4（分段, 两列口径 尝试/完成 写全名）
- 段 3429（侧车修复后, 08-22 14:38 → 3929）: 491 尝试 / 53 完成 / 回落率 89.2%（含池病污染段; 今日 218/4=1.8% 为塌方值）
- **池修复后段（行 3929 @08-24 23:54 起）= 干净段起点**, 明早判定一页纸主数据源
- 基线注: 45s era 完成率 ~19-20%（侧车修复后 58 尝试/11 完成）; 今日完成 4 条全为 OCR 类（00:21/02:03/16:34/20:28）

## 服务
- :5050 UP（PID 3153034, 08-24 23:50:27 池修复窗重启; route=on, timeout=45, embeddings=137）; :8004 A3B UP（M1 热路径锁定）; :8006 非 DSpark 生产 UP（观察期配置不动）; :8008 UP; :8007 空闲; :8005 DOWN（退位断言）; :15432 PG UP（GUC 10min + 池 pre_ping/recycle300 双保险）
- opencode 侧车 PID 3153507 UP（池修复窗重启）; MCP 三子进程 3153592/94/96 重生（新池载修复, 旧 49 条错误进程已替换）
- Loop B 30min 周期持续验证中（翻转应停）; kiosk 正式关闭（08-22）
- cron 在排: 00:16 pool_gate.sh / 00:40 pool_loopb_check.sh（均 one-shot 自删）

## 质量基线
- eval 08-22: M1 PASS / 确定性 16/16 / NF 0/9 / judge 5.0
- pytest 384 passed / 13 skipped（08-24 23:50, 补丁后全量）
- canary 4/4（08-24 23:54, 修复后首轮; 对照修复前 23:19 周期 3/4）

## 待办（白天队列）
- 明早第一单: 《判定一页纸》（池修复工件 + B4 分段 → 超时 (a) + T1 复测安排）
- 每日 eval 恢复（今日缺位已记账; 今晚不排, 留干净段）
- T1 结论疑似带污染: 引用前先复测 step 基线（#T1-POLLUTION-NOTE）
- :5050 代码窗积压: FK cleanup 水位闸边角（08:14 新增 1 条）/ 泄漏真源根治（engine-per-request 已修, 观察）——观察期后再排
