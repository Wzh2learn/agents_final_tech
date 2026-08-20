# memory/STATE.md
更新: 2026-08-21 01:45（夜间 loop: 专利 P4 完整修订版 + N0-N3 科研队列收口）

## 模式
守护模式。本轮: P4 专利完整修订版交底书完成（待用户终审后亲发导师）; B4 切换点
interim checkpoint + 24h cron 布防; PSO 落点① v0 首批实测数据回填专利。
等: ① 甲方首轮反馈（B4 时钟 08-12 启动）② 用户专利终审 + 导师时间表
③ B4 24h checkpoint（08-21 23:50 cron 一次性）

## Git
- HEAD: 本收口 commit; 三方对齐 GB10=GitHub=本机
- 本轮: P4 专利修订版（724 行, 权 7-12 新增, 权 10 双要素锚定）+ N1 B4 checkpoint
  报告 + scripts/graph/b4_checkpoint.py + B4 日志隔离修复（m2.py env 覆盖 +
  conftest）+ N2 PSO 原型（research/pso/, 独立 venv）+ INDEX/THREADS/dispatch/STATE
- 冻结工件未动（甲方 docx bc3785cb / 导师 docx 冻结 hash 见台账）

## 本轮战绩（夜间 loop P4+N0-N2）
- P4: docs/experiments/2026-08-21_patent_full_revised.md — 权 1-6 逐字保留 +
  权 7-12 新增（权 10 锚定"确定性规则工件 + 回归验证门", 附 Mem0/Letta 划界注记）;
  实施例五全抽象化 + 基线回填; §5.3.3 PSO 实测回填; 附录 A 对照 19 条 + 附录 B
  匿名化实跑 0 命中; DSpark/DFlash 术语口径入 drafter 台账
- N1: 切换点后真实流量 7 条全 45-50s 超时回落; "1 次 agent 完成"（行 3098）重分类
  为 pytest TestClient 污染 → 修复 M1_B4_LOG_PATH env 覆盖 + conftest 隔离
  （验证: 生产日志行数不变 + 20 passed）; 生产接受率 1.33（1141/856, vs 切换窗
  1.26）; 真实 agent 完成维持 0; 24h checkpoint cron 23:50 一次性布防
- N2: PSO 落点① v0 — 验证门 PASS（复现判别力报告根分）, 平均分离度
  1.2560→1.4326（+14.06%）, 5 轮收敛, 8/11 节点权重变更; 均值目标压缩低频缺陷
  分离的取舍如实入账（minimax 变体列跟进）; 数据回填专利 §5.3.3/§5.5.5
- N0: docs/33 §8 状态对齐（K2 v1 已交付 / C1C2 NO-GO / PSO 落点①v0）
- N3: C3 4B 探针 — off 14/16 / xhigh 13/16 → NO-GO（双档）; 4B 思考负增益
  + q08 掩码客户名题 4B 双档全过（14B/8B xhigh 反挂）洞察入账; :8007 用毕即停

## 服务
- :5050 UP（route=on, timeout=45, embeddings=137）; :8004 A3B UP（M1 热路径锁定）;
  :8006 = DSpark 生产（GMEM 0.34 / KV 6.0G 钉死 / k=7 probabilistic / maxlen 32768）;
  :8008 proxy UP; :8007 空闲; :8005 DOWN（退位）; :8100 UP; :15432 PG UP
- Loop B 常态; 本机 kiosk 播放中
- B4: 切换点 3092 行; interim n=12（5 条测试疑似行已标记）; 24h checkpoint cron
  一次性 08-21 23:50（跑完需人工删除条目）

## 质量基线
- eval: 确定性 16/16 + NF 0/9 + judge 四维 5.0（08-19 v1 冻版基线）
- pytest: 379 passed / 13 skipped（本收口全量复测, 169.58s, 零回归）
- docs_lint: GB10 为准（收口复跑）

## 下一步
1. B4 24h checkpoint（23:50 cron → logs/graph/b4_checkpoint_*.md）; 判定按批复③:
   回落率 >60% 第一怀疑 content=null, 查无解释报用户拍板
2. 用户专利终审 → 导师; PSO 落点② + minimax 变体列跟进
3. 切换稳定后: k=5 A/B + medium 矩阵（08-23+ 窗口）
4. 缓办: 甲方反馈 → B4 分布分析; NLPCC workshop 核实; K3 门控闭环批跑; C4 VL-8B 探针;
   eval route 标签差异（B4 为准, 观察期内不动）