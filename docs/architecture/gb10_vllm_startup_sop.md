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
