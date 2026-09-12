#!/bin/bash
# pre-commit: cjk-byte-check
# 移植自 skills-loop-engineering@7ffbe44 hooks/cjk-byte-check.sh (Claude Code PreToolUse → git pre-commit 形态)
# 规则: staged 变更的 .md 文件做 U+FFFD 替换符扫描 (edit 工具链 CJK 编码副作用; 源仓库三次实证)
# 降级原则: python3 不可用或解析失败时警告放行, 不无声 fail-open
# 注意: U+FFFD 必须用 chr(0xFFFD) 显式构造——直接输入该字符会被传输链吞掉导致空串误报
# RW-5 修复 (2026-09-12, 决策 36; 侧线复验批 #3 时发现, HIGH): 解释器必须**实跑探测**, 不能只 command -v。
# 缺陷链 (Windows, 侧线实测): `command -v python3` **rc=0** 且指向
#   /c/Users/<非 ASCII 用户名>/AppData/Local/Microsoft/WindowsApps/python3 = **Microsoft Store 存根**
# => 旧的 `if ! command -v python3` 降级分支**不触发**; 但 `python3 -c "import sys"` **rc=49、
# stdout 空、stderr 空**(存根静默失败), 而真解释器是 `python`(3.9, rc=0)。
# => 于是 BAD=$(echo "$MD_FILES" | python3 -c ...) 得到**空串** => [ -n "$BAD" ] 为假 => exit 0
#    且**零输出** = 无声 fail-open, 恰好违反本钩子 :5 自述的「不无声 fail-open」。
# 直接证据: 构造 ASCII 名、内容确含 U+FFFD (文件字节 EF BF BD 已核在位) 的 .md 并 staged,
#   直接跑本钩子 => rc=0 / stdout 空 / stderr 空; 把 python3 换成 python => 正常检出。
# ⇒ 该守卫在 Windows 上对 ASCII 与 CJK 文件名**一律失效**, 与 quotepath 无关 (批 #3 对 :11 的
#   quotepath 修复本身是对的且已生效 —— 同一实验里 MD_FILES 枚举正确 —— 只是**下游消费者是死的**)。
# 影响面: 本守卫的职责正是「staged .md 的 U+FFFD 乱码扫描 (edit 工具链 CJK 编码副作用)」, 而
#   **Windows + 中文用户名 + CJK 文档正是最可能产生 U+FFFD 的环境** ⇒ 它恰好在唯一需要它的平台上是死的;
#   GB10 侧 python3 为真解释器故正常 ⇒ 平台不对称与 RW-2 同型 (Loop A 在 GB10 受保护, Loop D 在本机不受保护)。
# 本族第三个独立根因: RW-1 = git 路径转义口径; RW-2 = python 文本重编码撞 locale;
#   **RW-5 = 解释器解析 (硬编码 python3 + Store 存根静默 rc=49)**; 三者同属「Windows 上假设 POSIX 行为」,
#   但修法互不覆盖, 只修前两个仍留 RW-5。
# 范式取自同目录 summary-recompute-guard.precommit.sh:15-24 (其 :18 注释已逐字预言本故障)。
PY=""
for cand in python3 python py; do
  command -v "$cand" >/dev/null 2>&1 || continue
  # WindowsApps store 存根会静默失败: 必须实跑探测才算可用
  if "$cand" -c "import sys" >/dev/null 2>&1; then PY="$cand"; break; fi
done
if [ -z "$PY" ]; then
  echo "[pre-commit:cjk-byte-check] WARN: 无可用 python 解释器 (python3/python/py 均缺失或为静默失败的存根), U+FFFD 扫描本项未复核 (跳过不等于通过)" >&2
  exit 0
fi
MD_FILES=$(git -c core.quotepath=false diff --cached --name-only --diff-filter=ACM 2>/dev/null | grep -E '\.md$')
[ -z "$MD_FILES" ] && exit 0
BAD=$(echo "$MD_FILES" | "$PY" -c "
import sys
REPL = chr(0xFFFD)
bad = []
for line in sys.stdin:
    f = line.strip()
    if not f:
        continue
    try:
        s = open(f, encoding='utf-8').read()
    except Exception:
        continue
    n = s.count(REPL)
    if n:
        bad.append(f'{f}（{n} 处）')
print('\n'.join(bad))
")
py_rc=$?
# RW-5 fail-loud 不变量 (2026-09-12, 决策 36): 子进程失败绝不等于「没有乱码」。
# 旧实现只看 BAD 是否为空, 于是解释器静默失败 (WindowsApps 存根 rc=49, stdout 与 stderr 皆空)
# 与「扫描完成且零命中」在结果上完全同形 => 无声 fail-open, 违反本钩子 :5 自述的原则。
if [ "$py_rc" -ne 0 ]; then
  echo "[pre-commit:cjk-byte-check] WARN: U+FFFD 扫描子进程 rc=$py_rc (解释器=$PY), 本项未复核 (跳过不等于通过; 解析失败不等于没有乱码)" >&2
  exit 0
fi
if [ -n "$BAD" ]; then
  echo "[pre-commit:cjk-byte-check] 拦截: staged Markdown 含 U+FFFD 替换符:" >&2
  echo "$BAD" | sed 's/^/  - /' >&2
  echo "请修复乱码后再提交。" >&2
  exit 1
fi
exit 0
