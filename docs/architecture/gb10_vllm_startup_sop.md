状态: 活跃 | 更新: 2026-08-16 | 取代/被取代: 无

# GB10 vLLM 启动 SOP（模型升级专项 S1 沉淀）

> vLLM 在 GB10 (121GB 统一内存) 上的启动流程, 由 P1 探针三次启动失败换来。
> 下次启动以本文为唯一依据, 不靠记忆。配套脚本: scripts/vllm_probe_serve.sh +
> scripts/gb10_reclaim_page_cache.sh。相关: docs/32 §2.1/§2.2 (模型卡与思考控制
> 实证)、DECISIONS.md 08-16 模型卡 (思考档位口径与回滚 SOP)。

## 0. 一键启动（已验证路径）

```bash
cd ~/wzh/projects/agents_final_tech
bash scripts/gb10_reclaim_page_cache.sh 35                # 第一步: 回收 page cache (必做)
# 第一步半: 预检闸 (08-20 新增, FM8): 量 CUDA free, ≥60 GiB 才许启动, 不达标当晚放弃:
#   ./venv/bin/python -c "import torch; f,_=torch.cuda.mem_get_info(); print('%.1f GiB' % (f/2**30))"
PORT=8006 GMEM=0.30 bash scripts/vllm_probe_serve.sh      # 第二步: 启动探针
```

冷启动 ~7min, 热启动 (有编译缓存) ~5min。READY 判据: curl :PORT/health 返回 200,
/v1/models 能列出 served-name。

## 1. 失败模式 → 对策 → 验证

### FM1 CUDA free 虚低 / page cache 争抢（三次启动失败主因）
- 症状: 模型+镜像下载后 CUDA free 仅 15.6GB; vLLM init 报 cudaErrorMemoryAllocation;
  或 KV 预算算成负值, GMEM=0.27 三连败 (差 0.44GiB)。
- 根因: CUDA mem_get_info 不计可回收 page cache; 权重读盘又把 cache 灌满, 挤掉 KV 预算。
- 对策: 启动前跑 `bash scripts/gb10_reclaim_page_cache.sh 35` — CPU 分配压力法回收
  干净缓存, 无 sudo, 生产栈实测无感 (:5050 healthy / :8004 200)。
- 验证: free -g 可用上升 (实测 15.6→38GB); vLLM 启动日志 KV cache size 为正。

### FM2 GMEM 超额分配
- 对策: GMEM=0.30 为生产 llama.cpp 常驻条件下的实测可用值; **只许调低不许调高**
  (0.27 差 0.44GiB 失败; 0.35 为理论上限无余量, 勿用)。
- 验证: 容器启动日志无 OOM; 权重 100% 后 READY。

### FM3 混合架构 Mamba 状态块约束并发槽位
- 根因: qwen3_5 混合 linear+full attention, Mamba 状态块按序列常驻。
- 对策: --max-num-seqs ≤78 (探针默认 32)。
- 验证: 启动日志无 Mamba 状态块分配错误。

### FM4 torch.compile 冷启动慢
- 对策: 挂持久编译缓存 `-v ~/wzh/vllm_cache:/root/.cache/vllm` (已内置于
  vllm_probe_serve.sh)。
- 验证: 二次启动时长 ~7min → ~5min。

## 2. 基建通道台账（2026-08-15/16 实测）

| 通道 | 状态 | 对策 |
|---|---|---|
| hub.docker.com | 不通 | 镜像名改 dockerproxy.net/<同路径>（实测通: vllm-gb10 22.1GB / pgvector） |
| daocloud 镜像站 | 白名单拒绝 | 不用 |
| 1ms.run 镜像站 | 大层卡死 | 不用 |
| HF 直连 | 000×3 不稳 | HF_ENDPOINT=https://hf-mirror.com（307→200 实测通） |
| ModelScope | 200 可用 | 备用下载通道 |
| 下载环境 | socks 代理变量干扰致报错 | 独立 dl_venv, 下载前剔除代理变量 |

## 3. 多实例并存的内存算术（08-16 口径）

- 机器: MemTotal 121GB 统一内存 (CUDA 可见口径 130.6GB)
- 生产常驻: llama.cpp :8004 (A3B+mmproj, -c 65536) + :8005 (14B) ≈ 30GB+
- 探针 :8006 (Qwen3.8-27B-FP8, GMEM=0.30) ≈ 39GB
- 新增实例前先算: 121 − 生产常驻 − 已有探针 − 系统余量(≥10GB); 权重 > 可分配预算时
  换更小量化 (GGUF Q4) 或先停旧探针再上 (停探针不影响生产)。

### FM5 reasoning parser 按请求级显式 enable_thinking 键控（S4 发现, 2026-08-16）
- 症状: 改造模板把服务器默认改为 thinking off (jinja2 本地渲染逐字节一致) 后,
  不携带 chat_template_kwargs 的请求仍被整体归入 reasoning 字段 (content=null);
  显式传 enable_thinking=false 则正常。空 kwargs {} 同样失败。
- 根因: vLLM 0.27 (vllm-gb10) reasoning-parser 按请求级 chat_template_kwargs
  enable_thinking 的**显式值**决定是否启用 reasoning 抽取; 服务器级模板默认
  不能替代请求级显式值。
- 对策: scripts/thinking_inject_proxy.py (:8008, tmux thinking-proxy) 对未携带
  显式值的 /v1/chat/completions 注入 enable_thinking=false; 显式值原样透传
  (judge 的 false / 未来 thinking-on 实验不受影响)。opencode gb10v provider
  baseURL 指 :8008/v1; judge 直连 :8006 (自带显式 false)。
  注意: 脚本内自清 socks 代理环境变量 + trust_env=False (SOP §2 同款陷阱,
  tmux 环境 ALL_PROXY 会致 httpx 启动崩溃)。
- 验证: 代理三态测试 (注入 off / 显式 true 透传思考 / 显式 false 透传) 全过;
  opencode m2-qa 会话 modelID=qwen38-27b-fp8 坐实。
- 模板改造告诫: jinja 替换必须逐字节保留原缩进与块结构; 排障时先用 jinja2
  本地渲染 diff 隔离"模板渲染差异 vs 服务端行为差异", 再下结论。

### FM6 Qwen3.8 工具调用为 XML 标签格式, hermes parser 不识别 (2026-08-17)
- 症状: m2-qa 走 27B 时答案恒空: finish_reason=stop, tool_calls=null;
  模型把工具调用以 XML 标签 (tool_call/function/parameter) 写进 content,
  opencode 收到空答案 → 每 ask 触发 compaction/回落。
- 根因: Qwen3.8 工具调用输出格式是 XML 标签而非 hermes 风格; vLLM 0.27
  (vllm-gb10) 自带 qwen3_engine_tool_parser.py, 注册名 qwen3_xml
  (别名 mimo/qwen3_coder)。
- 对策: vllm_probe_serve.sh 增 TOOL_PARSER env (默认 qwen3_xml),
  --tool-call-parser "$TOOL_PARSER"。
- 验证: 带 tools 直连 :8008 → finish_reason=tool_calls + 结构化 tool_calls;
  m2-qa 全链路答案带 sources。

### FM7 本构建 APC 默认关闭, 必须显式 --enable-prefix-caching (2026-08-17)
- 症状: agent 链 warm ask 45-85s; 逐轮 prefill 14.8k/15.9k/18.7k 全量重算,
  45s 预算完成率趋零 (00:13 曾实测 30s 完成, 重启后不复现)。
- 根因: vllm-gb10 v0.27.1 构建 prefix_cache_queries_total=0 — APC 从未开启,
  vLLM 每轮全量 prefill。
- 对策: vllm_probe_serve.sh 加 --enable-prefix-caching。
- 验证: 重启后 prefix_cache queries/hits >0 (实测命中率 ~78%); warm ask
  47s→30-34s; :5050 真实承载 agent 完成 30.2s/33.7s (route=agent,
  fell_back=false)。
- 告诫: --enable-prefix-caching 改变 torch.compile 图 → 首次启动冷重编译
  (本次 ~4min 额外), 后续启动命中编译缓存。

### FM8 大 I/O page cache 污染: 切换窗 = 纯窗口 (DSpark 四连败教训, 2026-08-19→20, 用户批复立闸)
- 症状: Route S 下载 (docker pull 39GB 镜像 ×3 尝试 + HF 24GB 权重) 之后, :8006 DSpark
  投机切换启动 4 连败, KV 可用逐次恶化 2.57→3.09→1.86→0.56 GiB (maxlen 32768 需 4.6 GiB);
  reclaim×5 上限 ~50 GiB CUDA free, 达不到探针成功窗口的 69.46 GiB 干净 free。
- 根因: 大 I/O (镜像拉取/权重下载) 持续灌 page cache; CUDA mem_get_info 不计 page cache
  为可用 (FM1 同机制, 但规模更大且边下载边回填); reclaim CPU 压力法追不上"下载中持续灌入"
  与残留脏层; DSpark drafter 2.53G + spec 增量 ~3.4G 把 KV 挤过红线。
- 对策 (两道闸, 08-20 用户批复):
  ① **纯窗口**: 切换窗内禁止任何 download/pull — 任何大 I/O 必须提前完成或推后。
     此前"下载与切换同窗"的批复已由用户更正为失误, 此后切换窗 = 纯窗口。
  ② **预检闸**: reclaim 后量 CUDA free, **≥60 GiB 才许启动**; 不达标当晚放弃,
     杜绝连败 (不恋战)。测量: venv python torch.cuda.mem_get_info 一行 (见 §0)。
- 验证: 切换窗内无活跃 pull/下载进程; 启动前 CUDA free ≥60 GiB; 启动日志 KV 可用
  ≥ 需求 + 1 GiB 余量 (DSpark 全规格需求 ≈4.6 GiB @maxlen 32768)。

### FM9 MAXLEN 缩减退路作废: context 分布实测 p99>20k (2026-08-20, 批复②测量定论)
- 背景: DSpark 重试菜单方案 2 (MAXLEN 32768→16384, KV 需 ~2.3 GiB) 以"先量 opencode
  实际 context 分布"为前提; 批复规则: p99>16k 则放弃该退路。
- 测量 (生产 :8006, 08-20 00:12 回滚重启起 21.2h, n=1920 真实请求, vLLM /metrics 直方图):
  ≤1k 581 (30.3%, = title agent 调用, 与 opencode.log 同窗 580 次 title stream 1:1) /
  10k–20k 1213 (63.2%, m2-qa agent 路多轮) / >20k 126 (6.6%, m2-qa 后段轮次);
  平均 prompt 11,719 tokens; 累计秩计算 p95/p99 均落入 >20k 区间 (≤20k 累计 1794 < 秩 1824/1901)。
  同窗 opencode.log: m2-qa stream 1757 次 / 586 会话; 417 次调用未达 vLLM (超时早杀)。
  历史佐证: 07-28 evidence-verifier 26,090 token 请求 vs 16,384 上限 → 硬失败;
  07-16 build 8,675 vs 8,192 → 硬失败 (均 opencode.log error 行)。
  DB 残留旧时代样本 (thinking off): build 子 agent max 19.1k。
- 结论: p99 > 16k (实为 p99 > 20k) → **方案 2 作废** (批复规则触发, 决策不修)。
  即使 24576 仍会切掉 20-26k 尾部。MAXLEN 不是重试窗可用的 KV 节省杠杆。
- 剩余 KV 余量杠杆 (优先序): ① 预检闸 (FM8②, ≥60 GiB, 不达标当晚放弃)
  ② num_speculative_tokens 7→5 A/B (台账项, k=7 第 6/7 位接受率 14.3%/5.7% 近乎白算)
  ③ 当晚放弃。GMEM 抬升为 SOP 红线所禁, 不在菜单。