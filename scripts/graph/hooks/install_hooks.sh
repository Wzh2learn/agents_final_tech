#!/bin/bash
# 安装 pre-commit hook 链 (在仓库根执行; 本地与 GB10 通用)
# 重要: 仓库已有冻结节点守卫 = scripts/graph/hooks/pre-commit (L5 frozen-node guard),
#       本安装器生成的链先跑该守卫, 再跑 *.precommit.sh 新守卫, 绝不覆盖冻结守卫。
set -euo pipefail
ROOT=$(git rev-parse --show-toplevel)
cat > "$ROOT/.git/hooks/pre-commit" <<'EOF'
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
chmod +x "$ROOT/.git/hooks/pre-commit"
echo "pre-commit hook 链已安装: $ROOT/.git/hooks/pre-commit (冻结守卫保留在链首)"
echo "必做: 正反例测试 (HOOK_AUTHORING_GUIDE §Debugging Hooks):"
echo "  正例: staged 一个含 U+FFFD 的 .md → 应拦截"
echo "  反例: 正常 .md → 应放行"
