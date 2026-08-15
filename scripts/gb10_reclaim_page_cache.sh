#!/usr/bin/env bash
# 统一内存回收探针 (GB10 模型升级专项沉淀, 2026-08-16)。
# 背景: GB10 统一内存上, page cache (模型下载/镜像拉取灌入) 不被 CUDA
#   mem_get_info 计为可用, vLLM 启动时即使 OS available 充足也会
#   cudaErrorMemoryAllocation。无 sudo 时无法 drop_caches,
#   用 CPU 分配压力迫使内核回收干净 page cache (实测 15.6GB -> 38GB CUDA free)。
# 安全性: 只回收 page cache, 不动进程匿名页; 生产 llama.cpp/:5050 实测无感。
# 用法: bash scripts/gb10_reclaim_page_cache.sh [GB, 默认 35]
set -euo pipefail
GB="${1:-35}"
N=$((GB / 5))
echo "[reclaim] 施加 ${GB}GB CPU 分配压力迫使 page cache 回收..."
python3 - "$N" <<'PY'
import sys, time
blocks = []
n = int(sys.argv[1])
try:
    for i in range(n):
        b = bytearray(5*1024**3)
        step = 4*1024*1024
        for j in range(0, len(b), step):
            b[j] = 1
        blocks.append(b)
    time.sleep(3)
finally:
    del blocks
print("[reclaim] 分配-释放完成")
PY
free -g | head -2
echo "[reclaim] done"