#!/usr/bin/env bash
# routeb-watch v2: Qwen3.8-35B-A3B 权重发布监视 + 自动下载 (纯下载, 无推理)
# 探测口径: HF 侧用 hf CLI (权威, 404=不存在); ModelScope 侧用 resolve 端点。
LOG=$HOME/wzh/routeb_watch.log
DLV=$HOME/wzh/models/dl_venv/bin/hf
MS=$HOME/wzh/projects/agents_final_tech/venv/bin/modelscope
DEST_HF=$HOME/wzh/models/hf
DEST_GGUF=$HOME/wzh/models/gguf/qwen3.8-35b-a3b
cenv() { env -u all_proxy -u ALL_PROXY -u http_proxy -u HTTP_PROXY -u https_proxy -u HTTPS_PROXY "$@"; }
hf_probe() { cenv HF_ENDPOINT=https://hf-mirror.com "$DLV" download "$1" --include "$2" --local-dir /tmp/_rb_probe >/dev/null 2>&1; }
ms_code() { curl -s -o /dev/null -w "%{http_code}" -L --max-time 30 "https://modelscope.cn/models/$1/resolve/master/$2"; }
ts() { date "+%F %T"; }
echo "$(ts) routeb-watch v2 started (pid $$, hf CLI probe)" >> "$LOG"
while true; do
  # --- 1) 官方 FP8: hf 优先, ms 备援 ---
  if [ ! -f "$DEST_HF/Qwen3.8-35B-A3B-FP8/config.json" ]; then
    if hf_probe Qwen/Qwen3.8-35B-A3B-FP8 config.json; then
      echo "$(ts) FOUND hf Qwen/Qwen3.8-35B-A3B-FP8 -> download start" >> "$LOG"
      cenv HF_ENDPOINT=https://hf-mirror.com "$DLV" download Qwen/Qwen3.8-35B-A3B-FP8 \
        --local-dir "$DEST_HF/Qwen3.8-35B-A3B-FP8" >> "$LOG" 2>&1 \
        && echo "$(ts) DONE hf FP8" >> "$LOG" || echo "$(ts) FAIL hf FP8, retry next loop" >> "$LOG"
    else
      c=$(ms_code Qwen/Qwen3.8-35B-A3B-FP8 config.json)
      if [ "$c" = "200" ]; then
        echo "$(ts) FOUND modelscope Qwen/Qwen3.8-35B-A3B-FP8 -> download start" >> "$LOG"
        cenv "$MS" download --model Qwen/Qwen3.8-35B-A3B-FP8 \
          --local_dir "$DEST_HF/Qwen3.8-35B-A3B-FP8" >> "$LOG" 2>&1 \
          && echo "$(ts) DONE ms FP8" >> "$LOG" || echo "$(ts) FAIL ms FP8, retry next loop" >> "$LOG"
      else
        echo "$(ts) FP8 未发布 (hf not-found / ms $c)" >> "$LOG"
      fi
    fi
  fi
  # --- 2) GGUF Q4_K_M 社区版 (llama.cpp 路线) ---
  if [ ! -d "$DEST_GGUF" ] || [ -z "$(ls -A "$DEST_GGUF" 2>/dev/null | grep -i q4_k_m)" ]; then
    for r in unsloth/Qwen3.8-35B-A3B-GGUF ggml-org/Qwen3.8-35B-A3B-GGUF lmstudio-community/Qwen3.8-35B-A3B-GGUF bartowski/Qwen3.8-35B-A3B-GGUF; do
      if hf_probe "$r" README.md; then
        echo "$(ts) FOUND hf $r -> download Q4_K_M start" >> "$LOG"
        mkdir -p "$DEST_GGUF"
        cenv HF_ENDPOINT=https://hf-mirror.com "$DLV" download "$r" --include "*Q4_K_M*" \
          --local-dir "$DEST_GGUF" >> "$LOG" 2>&1 \
          && echo "$(ts) DONE gguf $r" >> "$LOG" || echo "$(ts) FAIL gguf $r, retry next loop" >> "$LOG"
        break
      fi
    done
  fi
  # --- 3) 官方 base BF16 只报警不自动拉 (~70GB, 待拍板) ---
  if hf_probe Qwen/Qwen3.8-35B-A3B config.json; then
    echo "$(ts) ALERT hf Qwen/Qwen3.8-35B-A3B base 已发布(未自动下载, 待拍板)" >> "$LOG"
  fi
  sleep 600
done
