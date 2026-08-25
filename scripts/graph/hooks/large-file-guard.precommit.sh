#!/bin/bash
# pre-commit: large-file-guard
# 移植自 skills-loop-engineering@7ffbe44 hooks/large-file-guard.sh (命令拦截 → staged 文件口径)
# 规则: >5MB 文件与权重/视频/数据类型禁入库 (对应既有纪律 "视频文件不入 git";
#       demo_v3.mp4 录制当晚即为第一个受益者)
# 降级原则: stat 不可用时跳过体积检查, 类型检查仍生效
STAGED=$(git diff --cached --name-only --diff-filter=ACM 2>/dev/null)
[ -z "$STAGED" ] && exit 0
BAD=""
for f in $STAGED; do
  [ -f "$f" ] || continue
  case "$f" in
    *.mp4|*.mov|*.webm|*.pt|*.ckpt|*.npy|*.npz|*.safetensors|*.gguf|checkpoints/*|datasets/*|weights/*)
      BAD="$BAD
  - $f (禁入类型/目录)"; continue ;;
  esac
  SZ=$(stat -c%s "$f" 2>/dev/null || stat -f%z "$f" 2>/dev/null || echo 0)
  if [ "$SZ" -gt 5242880 ]; then
    BAD="$BAD
  - $f ($((SZ/1048576))MB > 5MB)"
  fi
done
if [ -n "$BAD" ]; then
  echo "[pre-commit:large-file-guard] 拦截: 大文件/禁入类型:" >&2
  echo "$BAD" >&2
  echo "视频/权重/数据一律不入库; 确有特例请人工在终端操作。" >&2
  exit 1
fi
exit 0
