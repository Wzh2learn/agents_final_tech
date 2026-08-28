#!/usr/bin/env python3
"""治理漂移扫描（制度化 08-29: 收口清单固定步骤 + 夜间 cron 轻扫）。

扫荡面: INDEX 状态词（待批/待执行/待发送/待勾选）+ 活文档头部更新日期超期（>16 天）。
命中 = 漂移候选: 报告落 logs/graph/governance_drift_latest.md, 新候选幂等登记
docs/29 backlog 的"漂移扫描待核"节（已登记项按指纹去重不重复）。零 LLM 纯文本。
用法: governance_drift_scan.py [--cron]（--cron 仅报告不登记, 供夜间轻扫）
"""
import datetime
import hashlib
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
INDEX = REPO / "docs" / "INDEX.md"
BACKLOG = REPO / "docs" / "29_graph_engineering_roadmap.md"
REPORT = REPO / "logs" / "graph" / "governance_drift_latest.md"
WORDS = ("待批", "待执行", "待发送", "待勾选")
AGE_DAYS = 16


def scan_index():
    hits = []
    for i, line in enumerate(INDEX.read_text(encoding="utf-8").splitlines(), 1):
        if not line.startswith("|"):
            continue
        for w in WORDS:
            if w in line:
                name = line.split("`")[1] if "`" in line else line[:40]
                hits.append({"kind": f"INDEX 状态词[{w}]", "file": name, "line": i,
                             "fp": hashlib.sha1(f"{name}:{w}".encode()).hexdigest()[:10]})
                break
    return hits


def scan_doc_dates():
    hits, today = [], datetime.date.today()
    for md in list((REPO / "docs").glob("*.md")):
        head = md.read_text(encoding="utf-8", errors="replace")[:600]
        m = re.search(r"状态:\s*活跃.*?更新:\s*(\d{4}-\d{2}-\d{2})", head)
        if not m:
            continue
        try:
            d = datetime.date.fromisoformat(m.group(1))
        except ValueError:
            continue
        age = (today - d).days
        if age > AGE_DAYS:
            hits.append({"kind": f"日期超期[{age}天]", "file": md.name, "line": 1,
                         "fp": hashlib.sha1(f"{md.name}:age".encode()).hexdigest()[:10]})
    return hits


SECTION = "### 五、漂移扫描待核（governance_drift_scan 自动登记, 只核不改）\n"
OFFREPO_INV = REPO / "docs" / "experiments" / "2026-08-29_offrepo_assets_inventory.md"
OFFREPO_DIRS = [Path.home() / "wzh" / d for d in
                ("models/hf", "models/gguf", "research", "datasets")]
# 用户暂缓区白名单（未来扫描跳过, 防误报; 08-29 用户卡 §四）
SCAN_SKIP_WHITELIST = ("/home/testuser/datasets", "mym", ".openclaw", "6g_v2x")


def register(hits):
    text = BACKLOG.read_text(encoding="utf-8")
    if SECTION not in text:
        text += ("\n" + SECTION +
                 "\n| 指纹 | 类型 | 对象 | 首见 | 状态 |\n|---|---|---|---|---|\n")
    added = 0
    for h in hits:
        if h["fp"] in text:
            continue
        text += (f"| {h['fp']} | {h['kind']} | {h['file']} | "
                 f"{datetime.date.today().isoformat()} | 待核 |\n")
        added += 1
    BACKLOG.write_text(text, encoding="utf-8")
    return added


def scan_offrepo_assets():
    """仓外大件登记核查: ~/wzh 资产目录 vs 台账文本（下载即登记规则, 08-29）。"""
    hits = []
    if not OFFREPO_INV.exists():
        return [{"kind": "仓外台账缺失", "file": str(OFFREPO_INV), "line": 0,
                 "fp": "offrepo-inv-missing"}]
    inv = OFFREPO_INV.read_text(encoding="utf-8", errors="replace")
    for base in OFFREPO_DIRS:
        if not base.is_dir() or str(base).startswith(SCAN_SKIP_WHITELIST):
            continue
        for child in sorted(base.iterdir()):
            if not child.is_dir() or child.name.startswith(SCAN_SKIP_WHITELIST):
                continue
            if child.name not in inv:
                hits.append({"kind": "仓外资产未登记", "file": str(child), "line": 0,
                             "fp": hashlib.sha1(f"offrepo:{child}".encode()).hexdigest()[:10]})
    return hits


def main():
    cron = "--cron" in sys.argv
    hits = scan_index() + scan_doc_dates() + scan_offrepo_assets()
    lines = [f"# 治理漂移扫描报告 {datetime.datetime.now():%Y-%m-%d %H:%M}",
             "", f"命中 {len(hits)} 项（模式: {'cron 轻扫' if cron else '收口登记'}）", ""]
    for h in hits:
        lines.append(f"- [{h['kind']}] {h['file']} (L{h['line']}, fp={h['fp']})")
    added = 0 if cron else register(hits)
    lines += ["", f"新登记 backlog: {added} 项" if not cron else "（cron 模式不登记）"]
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"drift scan: {len(hits)} hits, registered {added}")


if __name__ == "__main__":
    main()
