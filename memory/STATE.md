# memory/STATE.md
更新: 2026-08-20 夜（opencode context 分布测量定论 → MAXLEN 退路作废; DSpark 08-21 重试窗口前置收口）

## 模式
守护模式。队列: 等 08-21 晚 DSpark 干净窗口重试（用户给窗; 两道闸已载入 SOP:
纯窗口禁大 I/O + 预检 CUDA free ≥60G 不达标当晚放弃）。等: ① 甲方首轮反馈
（B4 时钟 08-12 启动, asks ≥100, 天数累计中）② 导师专利时间表对齐（P3 进行中:
权 10 锚定注记已落 P2; 实施例三供数等 K7）③ NLPCC 2026 workshop 窗口用户人工核实。

## Git
- HEAD: 本收口 commit; 三方对齐 GB10=GitHub=本机（前点 84f54f9）
- 本轮: SOP FM9 + THREADS + dispatch_log（context 测量定论作废方案 2）+ STATE 覆写
- 冻结工件未动（甲方 docx bc3785cb / 导师 docx 冻结 hash 见台账）

## 本轮战绩（context 测量定论, 批复②）
- 生产 :8006 回滚后 21.2h n=1920 真实请求: ≤1k 30.3%（=title 调用, 与
  opencode.log 580 次 1:1）/ 10k–20k 63.2%（m2-qa 多轮）/ >20k 6.6%; 平均
  prompt 11,719; 累计秩法 p95/p99 均 >20k
- 历史佐证: 07-28 evidence-verifier 26,090 vs 16,384 硬失败; 07-16 build
  8,675 vs 8,192 硬失败（16k 上限杀自家负载有真实先例）
- 判定: 批复规则触发 → **方案 2 (MAXLEN=16384) 正式作废**（决策不修, SOP FM9）;
  重试 KV 防线 = 预检闸 ≥60G 唯一防线, 不达标或启动再败即当晚放弃（k=5 为延迟优化项非 KV 救援, 切换成功后跑）
- 附带观察（记账不行动）: message=failed 556/586 会话 ≈ fallback kill 模式;
  adapter ask 后删会话, DB 不留 27B 时代样本, 分布以 metrics 直方图为准

## 服务
- :5050 UP（route=on, timeout=45, embeddings=137, health/full 全绿）; :8004 A3B UP;
  :8006 27B UP（vllm-probe Up 21h = 回滚后原配置, maxlen 32768 / GMEM 0.30）;
  :8008 proxy UP; :8007 空闲; :8005 DOWN（退位断言生效）; :8100 UP; :15432 PG UP
- Loop B: 21:08 周期 overall=PASS（STEP 8 双模型断言 / STEP 9 agent watchdog /
  STEP 4 dirty_files=1 whitelisted=1 白名单正常）
- 本机: kiosk 播放中（建议计数 326, 08-20 入账）

## 质量基线
- eval: 确定性 16/16 + NF 0/9 + judge 四维 5.0（08-19 v1 冻版基线）
- pytest: 379 passed / 13 skipped（GB10 口径; 本收口复验见 dispatch_log）
- docs_lint: GB10 为准 0/0（本机 check[4] = CRLF 已知误报）

## 下一步
1. 08-21 晚 DSpark 干净窗口重试（等用户给窗）: 纯窗口 + 预检闸 ≥60G; 六步验证
   + 两项追加（/metrics spec 计数器随请求增长 + 生产负载接受率对照探针 3.31）;
   回滚 = 原参数重起（/tmp/rollback_launch.sh 与启动脚本在位）
2. 切换成功后: B4 分段统计 + medium 16 题矩阵 + k=5 A/B（2-3 天后）; K7 PSO
   实现（实施例三供数 + 论文 B 章 4 前置, 切换后第一周）
3. Route S: HF 双权重 DONE; sglang 镜像 pull 三连败, 缓至将来合并窗口
4. 台账 pending: NLPCC 2026 workshop 窗口人工核实; 专利发明人/时间表待导师确认