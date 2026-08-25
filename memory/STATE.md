# memory/STATE.md
更新: 2026-08-25 22:55（晚间队列 E1-E6 收口: 三缺陷修复 + E2/E4 补跑 + 规则评估回填; 一页纸 v2 待圈选）

## 模式
守护模式。**晨报首位 = 判定一页纸 v2**（docs/experiments/2026-08-25_morning_decision_sheet_v2.md）: 门禁更正 PASS + 规则 0/A/B/C/D/E 逐条评估, 用户白天圈选。
关键裁定已入账: 规则 A 超时 (a) CLOSED（不抬超时, 诊断=E3）; 规则 B T1 结论维持（steps p50=4 干净环境复现）; 规则 D PSO blocked（judge 工件根因, 修复候选待明日窗口）。
其余等拍板: 甲方首轮反馈 / 专利导师五项定夺 / D1-D5 备忘录 / FK 水位线单件窗（规则 C, 等用户另行批, 不催）/ M4 减 step（须与 context 瘦身组合, E3 菜单）。

## 晚间队列 E1-E6（08-25 22:25-22:55）
- E1 三修: a) cron_gate_helper.sh 入库（闸失败=改期, 禁 SKIP; 回归修 grep -vF 清表 bug） b) 门禁解析三层修（半字符截断根因; 回归 GATE_PASS runs=3 → 今晚门禁更正为 PASS） c) pending 卡必须 cron one-shot 交接（入 template §8 + AGENTS.md）
- E2 step 复测补跑: 13/13 PASS, wall p50=49.09s / steps p50=4 mean=4.67（对照 T1 Arm A 49.6s/4 复现, 健康代 p50=3 未复现）→ T1 未被池病污染
- E3 逐步耗时诊断: 45s 截断时 step1 在途 44%, 每 step 位 p50=30-34s（prefill/context 27k 膨胀 3-4 倍）→ 减 step 必须与 context 瘦身组合; 报告+菜单入 experiments/
- E4 PSO 落点② 补跑 = ABORT（根因坐实）: 启动闸全过, 判别力套件崩溃 = W3 judge 工件四维 avg=None（judge 全 16 条 TimeoutError）× aggregate L67 无 None 防护; 修复候选 ① None 安全化 ② judge 腿重跑 ③ 超时排查
- E5 Loop B 归因: 18:44 FAIL = STEP 9 agent_watchdog, canary 抖动类（08-23 23:51 先例）, 20:24 翻回, 22:05 九项全绿; 只分类不动手
- E6 一页纸 v2 回填 + 规则逐条入 THREADS; W3 "judge 5.0 零漂移"口径更正（确定性+NF 属实, judge 腿无数据）

## Git
- HEAD: E1-E6 收口 commit; 三方对齐（本机 pull --ff-only）
- 本轮资产: cron_gate_helper.sh / assemble_morning.py（升仓库）/ e3 报告 / 一页纸 v2 / template+AGENTS 规则（含字节截断字符安全）/ THREADS+INDEX+dispatch 入账 / pool_fix_verify+e2 工件（-f 入库）

## B4（分段, 两列口径 尝试/完成 写全名）
- 池修复后段（行 3929 @08-24 23:54 起）: 规则评估注册窗 3929→3988 = 59 尝试 / 2 完成 = 3.4%（样本=canary 题型, 代表性注记在一页纸 §2）; 滚动累计至 22:54 = 210 尝试 / 5 完成 = 2.4%（含 canary 续流 + E2 窗口 13 题, E2 窗注记在案）
- E2 窗口行 4122→4139（13 题 + canary 混入 4 行已注）; E4 窗纯工件计算零 ask

## 服务
- :5050 UP（PID 3153034, 池修复后; route=on timeout=45 未动）; :8004/:8006/:8008 UP; :8007 空闲; :15432 PG UP（GUC 10min + pre_ping/recycle 300 双保险, 门禁坐实）
- 侧车 + MCP 三进程载修复在跑; Loop B 30min 周期持续验证（22:05 九项全绿）; kiosk 关闭
- cron: 应为空（夜间 one-shot 全自删; E2/E4 用 nohup 非 cron）

## 质量基线
- 门禁: 12min 闲置 q06 PASS（08-25 00:28, 3 次运行）——一页纸 v1 UNKNOWN 为误报, 根因已修
- eval: 确定性 16/16 + NF 0/9（W3 01:51）; judge 腿全超时无数据（口径更正已入账, 重跑候选）
- E2 step 基线（干净段）: wall p50=49.09s / steps p50=4——T1 对照新基线
