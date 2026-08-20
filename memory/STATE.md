# memory/STATE.md
更新: 2026-08-21 00:00（DSpark 切换窗口 v3 成功 — :8006 生产已切 DSpark 投机解码）

## 模式
守护模式。本轮: 窗口 v2 闸过启动败 (KV 结构缺口) → 窗口 v3 批准参数变更
(GMEM 0.34 + kv-cache-memory 6.0G 钉死) 成功, DSpark 在生产。等: ① 甲方首轮
反馈（B4 时钟 08-12 启动）② 导师专利时间表对齐 ③ B4 数日观察 agent 路完成率
(DSpark 收益以生产数据为准, 不以探针外推)。

## Git
- HEAD: 本收口 commit; 三方对齐 GB10=GitHub=本机
- 本轮: 实验文档 (窗口 v2/v3 全程) + SOP FM8 对策③ (sudo drop_caches) + FM10
  (GMEM 0.34 + KV 钉死 + 行续反斜杠教训) + vllm_probe_serve.sh KV_CACHE_MEMORY
  透传 + THREADS + dispatch + STATE
- 冻结工件未动（甲方 docx bc3785cb / 导师 docx 冻结 hash 见台账）

## 本轮战绩（DSpark 窗口 v3）
- v2 教训: 闸过 (drop_caches 后 76.05G) 但 GMEM 0.30 预算结构性不足 (KV 3.08 vs
  需 4.6 GiB); 回滚两败 = 权重加载吃 MemFree + #48140 机制 → drop_caches 每次
  启动前必须重做
- v3 成功: GMEM 0.34 (用户授权覆写, 上限 41.35G) + --kv-cache-memory=6442450944
  (6.0G 钉死, 跳过 profiling 结构性消除噪声); READY 23:48, SpeculativeConfig
  (dspark k=7) + KV 42,711 tokens + spec 计数器随请求增长 (drafts 117)
- 验证组全过: health/full (137/local) / parse 65ms / QA 2/2 / compare 嘉兴民安
  2 持仓 / route=on / spec 激活
- **如实数据**: 生产接受率 1.26 tokens/round vs 探针 3.31 (探针高估); agent 路
  切换点以来完成 0 次 (B4 全 fell_back) — 收益待 B4 数日观察
- 事故: 首启因脚本行续反斜杠丢失静默失败 (speculative_config=None), spec 计数
  器为 0 暴露; 教训入 SOP FM10

## 服务
- :5050 UP (route=on, timeout=45, embeddings=137); :8004 A3B UP (M1 热路径锁定);
  **:8006 = DSpark 生产** (GMEM 0.34 / KV 6.0G 钉死 / k=7 probabilistic /
  maxlen 32768, 23:48 READY); :8008 proxy UP; :8007 空闲; :8005 DOWN (退位);
  :8100 UP; :15432 PG UP
- Loop B: 窗口内周期只记台账; 切换后周期验证恢复态 (STEP 8 模型 ID 断言不受
  DSpark 影响, served-name 不变)
- 本机: kiosk 播放中 (PID 23036 controller / 151364 loop_demo)
- B4: 切换点 **3092 行** (窗口开始 3081); 统计按 3092 分段, DSpark 收益观察窗口开启

## 质量基线
- eval: 确定性 16/16 + NF 0/9 + judge 四维 5.0 (08-19 v1 冻版基线)
- pytest: 379 passed / 13 skipped (GB10 口径)
- docs_lint: GB10 为准 0/0 (本机 check[4] = CRLF 已知误报)

## 下一步
1. B4 观察 (≥2-3 天): agent 路完成率 / 回落率 / 接受率趋势; watchdog 守护,
   异常即按回滚预案 (原参数重起, /tmp/rollback_launch.sh + drop_caches)
2. 切换稳定后: k=5 A/B + medium 16 题矩阵 (延迟优化项, 非 KV 救援)
3. 待审项: ask 日期对比产品解析错配; eval 中间行 route 标签异常
4. 长期台账: vLLM 版本升级评估 (#46932/#49760/#48140, 不动版本)
5. 缓办: 甲方反馈 → B4 分布分析; K7 PSO (专利实施例三供数); NLPCC workshop 核实