# memory/STATE.md
更新: 2026-08-21 23:25（B4 24h 终判完成→等用户拍板; 专利终审补遗 001d04b）

## 模式
守护模式。本轮两大块: ① 专利 P4 完整修订版完成（待用户终审发导师）+ N0-N3
科研队列; ② D1-D4 DSpark 实效诊断——接受率分段定论（全段均匀低）, k=5 方案
就绪等窗口, DFlash 探针臂 NO-GO。
等: ① 甲方首轮反馈（B4 时钟 08-12 启动）② 用户专利终审 + 导师时间表
③ B4 24h 终判已出（尝试 190/完成 0/回落 100%, 菜单 a/b/c 待拍板）④ D3 k=5 重启窗口批复

## Git
- HEAD: 本收口 commit; 三方对齐 GB10=GitHub=本机
- 本轮资产: P4 专利修订版 / N1 B4 checkpoint 报告 + b4_checkpoint.py / N2 PSO
  原型 (research/pso/) / N3 C3 报告 / D2 分段报告 + d2_segments.py / D3 k5 方案 /
  D4 决策备忘 / B4 日志隔离修复 (m2.py env + conftest) / drafter ledger 双注 /
  INDEX/THREADS/dispatch/STATE

## 本轮战绩
- P4 专利: 权 1-6 保留 + 权 7-12 新增（权 10 锚定"确定性规则工件+回归验证门"）;
  实施例五 + PSO 实测回填（分离度 1.2560→1.4326, +14.06%）; 匿名化 0 命中
- N1: B4 污染修复（生产零改动）; 真实 agent 完成维持 0; 接受率观察入 D 队列
- N2: PSO 落点①v0 首批实测（专利实施例三供数激活）
- N3: C3 4B NO-GO + 4B 思考负增益/q08 反转洞察
- **D1 判定=观察档**: 切换点后真实流量 9/9 全 45-50s 超时回落（归因明确=预算<
  轨迹长度, 非归因不明）, agent 完成 0, content=null 0; **24h 终判完成: 尝试 190/完成 0/回落率 100%, 等用户拍板**
- **D2 核心定论**: 接受率全段均匀低——生产 agent 路 1.09-1.29 / XML-xhigh 1.517 /
  freeform 1.76, 无 >2.5 段; 探针 3.31 是 thinking-off 短答离群值不作生产预期;
  sidecar 真实轨迹（长上下文+skill 元数据+45s 截断）是接受率洼地
- **D3**: k=7→5 方案就绪——末两位贡献 4.2%/2.6%, 净估计 +3-8%, 推荐度中低
  （主矛盾是接受率非草稿长度）, 需 :8006 窗口, 未批不执行
- **D4**: DFlash 探针臂 NO-GO——判据后半不成立 + rwmacy drafter 需 rmacy/vllm
  fork（stock 下接受率崩 24%, README 自证）+ B70 调优; DFlash2 PR#52816 open
  （08-20 更新）+ 权重盯梢入 ledger

## 服务
- :5050 UP（route=on, timeout=45, embeddings=137）; :8004 A3B UP（M1 热路径锁定）;
  :8006 = DSpark 生产（GMEM 0.34 / KV 6.0G / k=7, 观察期配置不动）; :8008 UP;
  :8007 空闲（D 队列未开臂）; :8005 DOWN; :8100 UP; :15432 PG UP
- Loop B 常态; 本机 kiosk 播放中
- B4: 切换点 3092; 24h 终判完成（尝试 190/完成 0/回落率 100%, 全超时型, content=null=0）; cron 条目已删; 等用户拍板

## 质量基线
- eval: 确定性 16/16 + NF 0/9 + judge 四维 5.0
- pytest: 379 passed / 13 skipped（01:00 前后全量复测）
- docs_lint: GB10 为准

## 本轮追记（08-21 晚）
- B4 口径修复（辅助线审计）: route 记最终路径 → b4_checkpoint.py 两列口径
  （尝试=完成+≥45s 超时回落）; 冒烟 n=191: 尝试 186/完成 0/回落率 100%;
  23:50 cron 用修正口径终判; 口径注记入 THREADS
- kiosk 决策 A 方案已出（per-request route 参数, 待批; 需一次 :5050 重启窗口）:
  docs/experiments/2026-08-21_kiosk_agent_route_proposal.md
- B4 24h 终判（23:22 提前, 用户批准）: 尝试 190/完成 0/回落率 100%（全超时型）, content=null=0;
  归因明确（对照切换前 45s era 完成率 ~20%→0%, DSpark 对 agent 路净效应为负）→ 报用户拍板;
  菜单: a 回滚非 DSpark（SOP ~31s）/ b 超时抬 60s / c 保留+kiosk A1; cron 已删
- 专利终审补遗落地（附录 A 15/16 行 + 呈递说明 + §5.3.3 口径澄清, 001d04b）

## 下一步
1. B4 24h 终判已出 → 等用户拍板（a 回滚非 DSpark / b 超时抬 60s / c 保留+kiosk A1）
2. 用户专利终审（补遗 001d04b 已入）→ 导师; D3 k=5 窗口批复 → 执行
3. 优化方向记账（不动手）: drafter v2 盯梢 / sidecar 上下文瘦身（skill 元数据）/
  思考档位路由维度 / DFlash2+权重盯梢
4. 缓办: 甲方反馈 → B4 分布分析; C4 VL-8B 探针; K3 门控闭环批跑; NLPCC 核实