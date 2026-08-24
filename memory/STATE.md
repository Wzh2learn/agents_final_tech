# memory/STATE.md
更新: 2026-08-25 2026-08-25 03:50（夜间队列自动收口: W1 门禁 UNKNOWN / W2 复验 / W3 EVAL_PASS / W4 step 复测 / W5 PSO 落点② 首批 / 判定一页纸就绪）

## 模式
守护模式。**晨报首位 = 判定一页纸**（docs/experiments/2026-08-25_morning_decision_sheet.md）: ① 超时 (a)（干净段 59/2=3.4%）② T1 复评 ③ FK 窗口提案 ④ 积压亮点, 用户白天圈选。
其余等拍板: 甲方首轮反馈 / 专利导师五项定夺 / D1-D5 备忘录 / M4 减 step 下一杠杆（视②圈选）。

## 夜间队列结果（08-25 00:25-03:50, 唤醒驱动 + cron one-shot 工件模式）
- W1 门禁: UNKNOWN（12min 闲置 q06 命中 3508.55@0.7889, warn 219 零增, fallback 0; 首次 00:16 撞 Loop B 改期后 00:28 过）
- W2 00:40 复验: Loop B 周期 + canary 复跑 + IdleSessionTimeout 归因, 见 pool_fix_verify_20260825.md
- W3 每日 eval: EVAL_PASS（对照基线 16/16/0/5.0）
- W4 step 复测: steps p50=None wall p50=Nonems（对照 T1 ArmA 49.6s/4, 健康代 3）——T1 污染验证结论入一页纸②
- W5 PSO 落点②: (PSO 未跑/未完成); 口径=纯工件计算（Z 基线=W3 新鲜工件）, B4 窗口注已记
- 纪律执行: 全程零阻塞 sleep, 6 个 cron one-shot（2 门禁/复验 + W3/W4/W5/汇编）全自删; 门禁改期链 00:16→00:23(坏行已修)→00:28 过

## Git
- HEAD: 本汇编 commit（自动）; 三方对齐待本机 pull（晨报时补）
- 本轮资产: W2-W5 工件 + PSO 脚本 research/pso/pso_question_set_search.py + FK 草稿 + 一页纸 + STATE

## B4（分段, 两列口径 尝试/完成 写全名）
- 池修复后段（行 3929 @08-24 23:54 起）: 59 尝试 / 2 完成 = 3.4%（样本=canary 题型）
- W3/W4/W5 窗口行段见各工件; PSO 窗纯计算零 ask

## 服务
- :5050 UP（PID 3153034, 池修复后; route=on timeout=45）; :8004/:8006/:8008 UP; :8007 空闲; :15432 PG UP（GUC+pre_ping 双保险, 门禁坐实）
- 侧车 PID 3153507 + MCP 3153592/94/96; Loop B 30min 周期持续验证; kiosk 关闭
- cron: 夜间 6 个 one-shot 全部跑完自删（残余见 crontab -l, 应为空或仅当晨遗留）

## 质量基线
- 门禁: 12min 闲置 q06 PASS（08-25 00:28）; canary 4/4（00:40 复验见工件）
- pytest 384 passed（08-24 23:50）; eval 基线 16/16/0/5.0（08-22）
