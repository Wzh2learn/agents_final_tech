#!/usr/bin/env python3
"""docs 治理 lint (Q3, 2026-08-12) — 把踩过的漂移变成机器检查。

四项检查:
  [1] INDEX 覆盖率 + 死链: docs/ 所有被跟踪 md (archive 除外) 必须在 INDEX.md
      登记 (按 basename); INDEX.md 内所有相对链接必须可解析。
  [2] 存活文档状态头: docs/ 顶层活文档须有 "状态:" 头行; 状态=活跃 但 更新
      日期超 14 天 -> WARN (时效过期)。
  [3] 台账防漂移 (08-11 漂移案沉淀): docs/ 非 experiments/archive 文档中出现
      gap/遗留 关键词复述 (而非引用 THREADS) -> flag。治理规则: gap/遗留项台账
      唯一存放于 memory/THREADS.md, 其他文档只引用不复述。
  [4] skill 注册表 vs 两端安装 diff: 调 scripts/graph/sync_skills.sh --check。

用法: venv/bin/python scripts/docs_lint.py [--json PATH]
退出码: 0 = 无 FAIL (WARN 允许) / 1 = 有 FAIL / 2 = 环境错误
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import subprocess
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS = os.path.join(REPO_ROOT, "docs")
INDEX = os.path.join(DOCS, "INDEX.md")
STALE_DAYS = 14

# --- check 3 关键词与豁免 -----------------------------------------------
GAP_KEYWORDS = re.compile(r"known[_ ]gap|遗留|挂起|待修|未解决", re.I)
GAP_EXEMPT = re.compile(
    r"THREADS|RESOLVED|CLOSED|已修|已解决|已闭环|已入账|见 |参见|台账|~~|登记|"
    r"不修|无需修|不再|防漂移|关键词", re.I)


def iter_docs(include_experiments: bool = False):
    for root, dirs, files in os.walk(DOCS):
        rel_root = os.path.relpath(root, DOCS)
        if rel_root.startswith("archive"):
            continue
        if rel_root.startswith("experiments") and not include_experiments:
            continue
        for f in files:
            if f.endswith(".md"):
                yield os.path.join(root, f)


def check_index() -> tuple[list, list]:
    fails, warns = [], []
    if not os.path.isfile(INDEX):
        return ["INDEX.md 不存在"], []
    index_text = open(INDEX, encoding="utf-8").read()
    # coverage: tracked md basename must appear in INDEX
    try:
        tracked = subprocess.run(
            ["git", "ls-files", "docs"], capture_output=True, text=True,
            cwd=REPO_ROOT).stdout.splitlines()
    except Exception as e:
        return [f"git ls-files 失败: {e}"], []
    for path in tracked:
        if not path.endswith(".md") or path.startswith("docs/archive/"):
            continue
        if path == "docs/INDEX.md":
            continue
        base = os.path.basename(path)
        if base not in index_text:
            warns.append(f"[1] INDEX 未登记: {path}")
    # dead links inside INDEX.md
    for m in re.finditer(r"\[[^\]]*\]\(([^)\s]+)\)", index_text):
        target = m.group(1)
        if re.match(r"^(https?://|mailto:|#)", target):
            continue
        target = target.split("#")[0]
        if not target:
            continue
        resolved = os.path.normpath(os.path.join(DOCS, target))
        if not os.path.exists(resolved):
            fails.append(f"[1] INDEX 死链: {target}")
    return fails, warns


def check_status_headers() -> tuple[list, list]:
    fails, warns = [], []
    today = dt.date.today()
    for path in sorted(iter_docs()):
        if os.path.dirname(path) != DOCS:
            continue  # 仅顶层活文档要求状态头
        name = os.path.basename(path)
        if name in ("INDEX.md", "README.md"):
            continue
        # 交付件 (甲方发送版源文) 不带内部状态头, 状态由 INDEX 管理
        if name.startswith("23_"):
            continue
        head = open(path, encoding="utf-8").read(2000)
        m = re.search(r"状态[:：]\s*(\S+)", head)
        if not m:
            warns.append(f"[2] 缺状态头: docs/{name}")
            continue
        status = m.group(1)
        dm = re.search(r"更新[:：]\s*(\d{4}-\d{2}-\d{2})", head)
        if "活跃" in status and dm:
            try:
                updated = dt.date.fromisoformat(dm.group(1))
                age = (today - updated).days
                if age > STALE_DAYS:
                    warns.append(f"[2] 活跃但 {age} 天未更新: docs/{name} (更新: {dm.group(1)})")
            except ValueError:
                pass
    return fails, warns


def _doc_status(path: str) -> str:
    try:
        head = open(path, encoding="utf-8").read(2000)
    except OSError:
        return ""
    m = re.search(r"状态[:：]\s*(\S+)", head)
    return m.group(1) if m else ""


def check_gap_restating() -> tuple[list, list]:
    fails, warns = [], []
    for path in sorted(iter_docs(include_experiments=False)):
        # 历史/归档/完成态文档允许提及旧 gap (只约束活跃文档不复述台账)
        status = _doc_status(path)
        if any(k in status for k in ("历史", "归档", "完成")):
            continue
        rel = os.path.relpath(path, REPO_ROOT)
        for i, line in enumerate(open(path, encoding="utf-8"), 1):
            if GAP_KEYWORDS.search(line) and not GAP_EXEMPT.search(line):
                warns.append(f"[3] 疑似 gap 复述 (应只引用 THREADS): {rel}:{i}: {line.strip()[:80]}")
    return fails, warns


def check_skill_sync() -> tuple[list, list]:
    fails, warns = [], []
    script = os.path.join(REPO_ROOT, "scripts", "graph", "sync_skills.sh")
    try:
        r = subprocess.run(["bash", script, "--check"], capture_output=True,
                           text=True, timeout=60)
        if r.returncode != 0:
            fails.append("[4] skill 安装漂移 (sync_skills.sh --check): "
                         + "; ".join(l for l in r.stdout.splitlines() if "DRIFT" in l)[:300])
    except Exception as e:
        fails.append(f"[4] sync_skills --check 执行失败: {e}")
    return fails, warns


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--json", default=os.path.join(
        REPO_ROOT, "logs", "graph", "docs_lint_report.json"))
    args = ap.parse_args()

    all_fails, all_warns = [], []
    for fn in (check_index, check_status_headers, check_gap_restating, check_skill_sync):
        f, w = fn()
        all_fails.extend(f)
        all_warns.extend(w)

    report = {"date": dt.datetime.now().isoformat(timespec="seconds"),
              "fails": all_fails, "warns": all_warns,
              "overall": "FAIL" if all_fails else "PASS"}
    os.makedirs(os.path.dirname(args.json), exist_ok=True)
    with open(args.json, "w", encoding="utf-8") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=1)

    print(f"== docs_lint: {report['overall']} ({len(all_fails)} fail / {len(all_warns)} warn)")
    for x in all_fails:
        print("FAIL", x)
    for x in all_warns[:40]:
        print("WARN", x)
    if len(all_warns) > 40:
        print(f"... 及另外 {len(all_warns) - 40} 条 warn (见报告)")
    print(f"[report] {args.json}")
    return 1 if all_fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
