#!/bin/bash
# 安装 pre-commit hook 链 (在仓库根执行; 本地与 GB10 通用)
# 重要: 仓库已有冻结节点守卫 = scripts/graph/hooks/pre-commit (L5 frozen-node guard),
#       本安装器生成的链先跑该守卫, 再跑 *.precommit.sh 新守卫, 绝不覆盖冻结守卫。
#
# 原子性 (2026-09-10, TASK-20260910-A4A5A4W §2.1 ②, 承 A19「暂存校验后交换」姿势):
#   改前 `cat > .git/hooks/pre-commit` 直写目标 —— 写一半被中断 = 钩子半装
#   (半装的链可能只跑部分守卫, 比不装更危险, 因为它看起来是装好的)。
#   现在: 写临时文件 -> bash -n 校验 -> 备份现有钩子 -> mv -f 原子交换 -> 装后自检。
set -euo pipefail
ROOT=$(git rev-parse --show-toplevel)
HOOK="$ROOT/.git/hooks/pre-commit"
TMP="${HOOK}.new.$$"
cleanup() { rm -f "$TMP" 2>/dev/null || true; }
trap cleanup EXIT

cat > "$TMP" <<'EOF'
#!/bin/bash
# hook 链 (2026-08-25 起):
#   1) scripts/graph/hooks/pre-commit          — L5 冻结节点守卫 (2026-08-06 既有, 必须先跑)
#   2) scripts/graph/hooks/*.precommit.sh      — 新增守卫 (源: skills-loop-engineering@7ffbe44)
ROOT=$(git rev-parse --show-toplevel)
rc=0
bash "$ROOT/scripts/graph/hooks/pre-commit" || rc=1
for h in "$ROOT"/scripts/graph/hooks/*.precommit.sh; do
  [ -e "$h" ] || continue
  [ -x "$h" ] || chmod +x "$h"
  bash "$h" || rc=1
done
exit $rc
EOF

# 校验: 临时文件必须是语法合法的 bash, 且链首守卫与各 Fragment 自身也必须语法合法
bash -n "$TMP"
[ -f "$ROOT/scripts/graph/hooks/pre-commit" ] || { echo "REFUSE: 缺 L5 守卫 scripts/graph/hooks/pre-commit"; exit 1; }
bash -n "$ROOT/scripts/graph/hooks/pre-commit"
for h in "$ROOT"/scripts/graph/hooks/*.precommit.sh; do
  [ -e "$h" ] || continue
  bash -n "$h" || { echo "REFUSE: 守卫 fragment 语法不合法: $h"; exit 1; }
done
chmod 755 "$TMP"

if [ -f "$HOOK" ]; then
  BK="${HOOK}.bak.$(date +%Y%m%d%H%M%S)"
  cp -p "$HOOK" "$BK"
  echo "已备份现有钩子: $BK"
fi
mv -f "$TMP" "$HOOK"          # 同目录原子交换
trap - EXIT

# 装后自检: 落地的钩子存在、可执行、语法合法、且确实把 L5 守卫排在链首
[ -x "$HOOK" ] || { echo "FAIL: 安装后 $HOOK 不可执行"; exit 1; }
bash -n "$HOOK"
grep -q 'scripts/graph/hooks/pre-commit' "$HOOK" || { echo "FAIL: 链首冻结守卫缺失"; exit 1; }
[ "$(grep -n 'scripts/graph/hooks/pre-commit' "$HOOK" | head -1 | cut -d: -f1)" -lt \
    "$(grep -n 'precommit.sh' "$HOOK" | head -1 | cut -d: -f1)" ] \
  || { echo "FAIL: L5 守卫未排在 fragment 之前"; exit 1; }

echo "pre-commit hook 链已安装: $HOOK (冻结守卫保留在链首; 原子安装 + 装后自检通过)"
echo "必做: 正反例测试 (HOOK_AUTHORING_GUIDE §Debugging Hooks):"
echo "  正例: staged 一个含 U+FFFD 的 .md → 应拦截"
echo "  反例: 正常 .md → 应放行"
