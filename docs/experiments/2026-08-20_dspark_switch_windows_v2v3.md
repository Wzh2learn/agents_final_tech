# DSpark :8006 切换窗口 v2/v3 全程记录 (2026-08-20 夜)

状态: v2 失败 (KV 缺口) → v3 成功 (GMEM 0.34 + kv-cache-memory 6.0G 钉死); DSpark 已在生产
关联: docs/architecture/gb10_vllm_startup_sop.md FM8/FM10 / 2026-08-19_dspark_drafter_ledger.md

## 1. 背景
- DSpark GO 判定 (08-19 探针): off 2.9x / xhigh 3.5x, 接受率 3.31, eval 零回归 (det 16/16 + NF 0/9 + judge 5.0)
- 08-20 夜窗口 v1: 预检闸 52.08<60G, 当晚放弃 (THREADS [08-20 22:35])
- 根因诊断 (辅助线): vllm#48140 (closed not_planned) — GB10 mem_get_info 读 MemFree 不读
  MemAvailable, page cache 计为已用; 官方 workaround = load 前 drop_caches
- sudo 预授权: /etc/sudoers.d/drop-caches, 窄口径 NOPASSWD 仅 `tee /proc/sys/vm/drop_caches`
  (sudo -ln 窗口前验证生效)
- 误判更正 (用户确认): ① PID 2104425/2104426 = :5050 uvicorn workers (父 2104416), 永不杀;
  ② zhikuncode 常驻仅 220MiB, 非内存嫌疑

## 2. 窗口 v2 (~22:5x): 闸过, 启动败, 回滚亦败
- 窗前: worktree 干净 / 无下载 / kiosk 停 (PID 159568/159996) / B4 前置标记 3077 行 /
  before-archive (0 处 speculative)
- 停消费者: firefox snap 3400916 (RSS 351M, 32 天) + mcp_server.server 1483806 (RSS 1.22G, 3 天)
- drop_caches: buff/cache 24→2G, free 15→76G; **CUDA free 76.05 GiB ≥ 60G 闸通过**
  (比探针成功窗 69.46G 更干净)
- DSpark 启动失败: `ValueError` KV 需 4.6 GiB vs 可用 3.08 GiB (estimated maxlen 16640);
  日志伴 "Add 4 padding layers, may waste at most 25.00% KV cache memory"
- 回滚 (原参数) 连败两次: 2.13 / 2.47 GiB vs 需 2.3 GiB (25% padding 浪费后更不足) —
  两次权重加载把 MemFree 压到 36.49G 预算之下, vLLM 预算被截断 (#48140 机制再现)
- 教训: **drop_caches 必须在每次启动 (含回滚) 前重做**, 不能一劳永逸

## 3. 窗口 v3 (23:2x-23:5x): 参数变更批准 + 成功
- 配置变更 (用户批准, 仅两项): GMEM 0.30→**0.34** (上限 41.35G; 探针峰值实测 37.07G, 余量 4.2G)
  + **--kv-cache-memory=6442450944** (6.0G 显式钉死 ≥4.6G 硬门槛; 探针成功值 5.24G 留余量)
- vllm_probe_serve.sh: KV_CACHE_MEMORY 透传 + GMEM 注释覆写记录 (commit 入仓库)
- **首启失败 = 脚本编辑失误**: exec 块行续反斜杠丢失 → docker run 截断,
  speculative_config=None / kv-cache-memory 未生效 / trust_remote_code=False,
  容器以 GMEM 0.34 原配置静默运行。暴露手段 = /metrics spec_decode 计数器为 0 (追加验证①抓住)
- 修复重起 23:41:20 → READY 23:48:08; 引擎配置行核验:
  `SpeculativeConfig(method='dspark', model='/models/drafter', num_spec_tokens=7)` +
  `trust_remote_code=True`
- 仪表五行摘录 (批复要求):
  - `torch.compile took 1.45 s / 0.06 s` (编译缓存全热)
  - `Initial free memory 79.01 GiB, reserved 6.0 GiB memory for KV Cache as specified by
    kv_cache_memory_bytes config and skipped memory profiling` ← 钉死跳过 profiling,
    结构性消除 MemFree 口径噪声 (2.88G 漂移之谜的机制解答)
  - `GPU KV cache size: 42,711 tokens` (≥32768 单请求硬门槛)
  - 无 consumed/peak/graph 摘要行 = profiling 被跳过的直接体现
  - 对照 v3 首启 (未钉死, profiling 路径): `Free memory on device (76.36/121.63 GiB),
    desired (0.34, 41.35 GiB), consumed 32.43, peak activation 2.54, CUDAGraph 0.19, KV 6.38`
- 启动前后 free -g: 前 121/39/78 (buff/cache 1) MemFree 82.8G → 后 121/84/11 (buff/cache 27)
  MemFree 10.0G / MemAvailable 41.6G (权重灌 cache 属预期)

## 4. 验证组 (六步 + 两项追加)
- health/full: healthy, embeddings=137, provider=local, llm_8004 ok, m2_rag ok ✓
- /v1/models: qwen38-27b-fp8, max_model_len 32768 ✓
- parse 冒烟 (fuxi txt): success 65ms, 确定性路径 llm_used=false ✓
- QA 2 题 canary (adv_ocr_meta + q06_minan_cash_balance): PASS 2/2 (均 45s 超时回落 direct,
  答案与出处正确)
- compare/positions "嘉兴民安" 20231031: position_count=2, 模糊匹配 ✓
- route=on / OPENCODE_ASK_TIMEOUT=45 进程 env ✓
- 追加① spec_decode 计数器: 0 → 20 项指标, num_drafts 112→117 随请求增长 ✓ 投机解码真激活
- 追加② **生产负载接受率: 147 accepted / 117 rounds = 1.26 tokens/round**
  (逐位 51/34/19/10/7/3/2%) vs 探针 3.31 — 生产流量 (xhigh reasoning + 工具 XML)
  接受率显著低于探针基准集, 探针高估了生产收益
- **agent 路完成: 切换点以来 0 次** (B4 权威: 全部 fell_back=true)。eval 中间行曾现
  route=agent 标签 (35850/38677ms), 但 B4 与报告 JSON 均为 direct — 以 B4 为准, 异常记账
- 观察项 (与本切换无关): ask 自然语言日期对比把"嘉兴民安"解析成复熙混合25号 (规则路径)

## 5. B4 分段与 kiosk
- 窗口开始标记 3081 行 → **切换点标记 3092 行** (23:48 READY); B4 统计按 3092 分段
- kiosk: 窗口两次暂停 → v3b 后恢复 (PID 23036 controller / 151364 loop_demo)
- Loop B: 窗口内周期只记台账不处置; 切换后周期验证恢复态

## 6. 结论与开放问题
1. 确定性参数有效: kv-cache-memory 钉死跳过 profiling, 结构性消除 #48140 族噪声轮盘;
   GMEM 0.34 补足 DSpark 的 KV 结构缺口 (4.6G 需求 vs 0.30 预算仅 ~3G)
2. 生产接受率 1.26 vs 探针 3.31 — agent 路 45s 内完成率是否实质改善, 以 B4 数日观察为准,
   不以探针数据外推
3. 待审: ask 日期对比产品解析错配; eval 中间行 route 标签异常
4. vLLM 版本升级评估长期台账: #46932 / #49760 / #48140 (今晚不动版本)
5. 存档: before (0821v2, 0 spec) / after-dspark (0821v3, 4 处 spec) inspect 配对,
   logs/graph/eval/ (GB10 本地); 启动日志 /tmp/dspark_switch_0821v3*.log