#!/usr/bin/env python3
"""批量应用 LLM 自学习同义词建议并复验（P1.1 沉淀, 2026-08-08）。

流程（安全优先）：
1. 读 config/schema_suggestions.json（--min-confidence 过滤，默认 medium 及以上）
2. 把 raw_column 合并进目标 schema 对应 table.field 的 synonyms（先到临时文件）
3. 用 --no-llm 确定性口径对受影响样本跑 before(现 schema)/after(合并后 schema)
4. 无回归（命中率不降 且 unmapped 不增）才在 --apply 时写回目标 schema

目标 schema 默认 = 仓库内 config/m1_table_schema.json（非冻结，可热加载种子）。
冻结运行时 schema（~/wzh/m1_samples/m1_table_schema.json，frozen_hashes.txt 在册）
默认拒写；确需更新时 --allow-frozen 显式指定，且事后必须由 Loop D 刷新
scripts/graph/frozen_hashes.txt（否则 commit 钩子/Loop B 拦截）。

用法：
  python scripts/m1_apply_schema_suggestions.py                 # dry-run 报告
  python scripts/m1_apply_schema_suggestions.py --apply         # 无回归才写回
  python scripts/m1_apply_schema_suggestions.py --min-confidence high --apply
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PARSER = os.path.join(REPO_ROOT, "scripts", "m1_statement_parser.py")
DEFAULT_SUGGESTIONS = os.path.join(REPO_ROOT, "config", "schema_suggestions.json")
DEFAULT_TARGET = os.path.join(REPO_ROOT, "config", "m1_table_schema.json")
FROZEN_RUNTIME_SCHEMA = os.path.expanduser("~/wzh/m1_samples/m1_table_schema.json")
CONF_RANK = {"high": 3, "medium": 2, "low": 1}


def load_suggestions(path: str, min_conf: str) -> list[dict]:
    if not os.path.isfile(path):
        print(f"[warn] 建议文件不存在: {path}", file=sys.stderr)
        return []
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    items = data.get("suggestions", []) if isinstance(data, dict) else data
    floor = CONF_RANK.get(min_conf, 2)
    return [s for s in items
            if CONF_RANK.get(s.get("confidence", ""), 0) >= floor]


def merge_into_schema(schema_path: str, suggestions: list[dict],
                      out_path: str) -> tuple[int, list[str]]:
    """把建议合并进 schema，写到 out_path。返回 (新增 synonym 数, 跳过原因列表)。"""
    with open(schema_path, encoding="utf-8") as fh:
        schema = json.load(fh)
    tables = {t["table_name"]: t for t in schema.get("tables", [])}
    added, skips = 0, []
    for sg in suggestions:
        t = tables.get(sg.get("table", ""))
        if t is None:
            skips.append(f"表不存在: {sg.get('table')} ({sg.get('raw_column')})")
            continue
        field = next((f for f in t.get("fields", [])
                      if f.get("standard") == sg.get("standard_field")), None)
        if field is None:
            skips.append(f"字段不存在: {sg.get('table')}.{sg.get('standard_field')} "
                         f"({sg.get('raw_column')})")
            continue
        syns = field.setdefault("synonyms", [])
        raw = sg["raw_column"]
        if raw in syns:
            skips.append(f"已存在: {sg.get('table')}.{sg.get('standard_field')} <- {raw}")
            continue
        syns.append(raw)
        added += 1
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(schema, fh, ensure_ascii=False, indent=2)
    return added, skips


def run_parser(samples_dir: str, files: list[str], schema_path: str,
               out_json: str) -> list[dict]:
    cmd = [sys.executable, PARSER, "--samples-dir", samples_dir, "--no-llm",
           "--schema", schema_path, "--files", *files, "--json", out_json]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    if proc.returncode != 0:
        raise RuntimeError(f"parser failed rc={proc.returncode}: {proc.stderr[-500:]}")
    with open(out_json, encoding="utf-8") as fh:
        return json.load(fh)


def summarize(results: list[dict]) -> dict[str, dict]:
    """每样本: unmapped 总数 / 命中数 / 列数 / 命中率。"""
    out = {}
    for r in results:
        unmapped = sum(len(tr.get("unmapped", [])) for tr in r.get("tables", []))
        hits = sum(tr.get("hits", 0) for tr in r.get("tables", []))
        cols = sum(tr.get("cols", 0) for tr in r.get("tables", []))
        rate = round(hits / cols * 100, 1) if cols else 0.0
        out[r["file"]] = {"unmapped": unmapped, "hits": hits, "cols": cols,
                          "hit_rate": rate}
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--suggestions", default=DEFAULT_SUGGESTIONS)
    ap.add_argument("--target", default=DEFAULT_TARGET,
                    help="目标 schema（默认仓库内非冻结 config/m1_table_schema.json）")
    ap.add_argument("--min-confidence", default="medium",
                    choices=["high", "medium", "low"])
    ap.add_argument("--samples-dir",
                    default=os.path.expanduser("~/wzh/m1_samples"))
    ap.add_argument("--apply", action="store_true",
                    help="无回归时写回目标 schema（默认 dry-run）")
    ap.add_argument("--force", action="store_true",
                    help="即使检测到回归也写回（慎用）")
    ap.add_argument("--allow-frozen", action="store_true",
                    help="允许以冻结运行时 schema 为目标（需 Loop D 事后刷新 manifest）")
    ap.add_argument("--report", default="", help="额外写 JSON 报告到该路径")
    args = ap.parse_args(argv)

    target = os.path.abspath(args.target)
    if target == os.path.abspath(FROZEN_RUNTIME_SCHEMA) and not args.allow_frozen:
        print("[blocked] 目标为冻结运行时 schema。确需更新请加 --allow-frozen，"
              "且写后必须由 Loop D 刷新 scripts/graph/frozen_hashes.txt。",
              file=sys.stderr)
        return 3

    suggestions = load_suggestions(args.suggestions, args.min_confidence)
    if not suggestions:
        print(f"无满足置信度 >= {args.min_confidence} 的建议，退出。")
        return 0

    # 受影响样本（建议来源），只保留样本目录里真实存在的
    wanted = sorted({s.get("sample", "") for s in suggestions if s.get("sample")})
    files, missing = [], []
    for name in wanted:
        p = os.path.join(args.samples_dir, name)
        (files if os.path.isfile(p) else missing).append(p if os.path.isfile(p) else name)
    for name in missing:
        print(f"[warn] 样本不存在, 跳过复验: {name}", file=sys.stderr)

    tmpdir = tempfile.mkdtemp(prefix="m1_apply_")
    merged = os.path.join(tmpdir, "merged_schema.json")
    added, skips = merge_into_schema(target, suggestions, merged)
    print(f"建议 {len(suggestions)} 条 → 新增 synonyms {added} 个；跳过 {len(skips)} 条")
    for sk in skips[:10]:
        print(f"  - {sk}")
    if added == 0:
        print("无新增 synonym（可能全部已存在），退出。")
        return 0

    report = {"suggestions": len(suggestions), "synonyms_added": added,
              "skips": skips, "samples": {}}
    if not files:
        if args.apply and not args.force:
            print("[blocked] 无可复验样本时 --apply 需显式 --force（F10 门禁盲区防护）。",
                  file=sys.stderr)
            return 4
        print("[warn] 无可复验样本，仅合并 schema（不验证）。")
        if args.apply:
            shutil.copyfile(merged, target)
            print(f"[apply] 已写回 {target}")
        return 0

    before = summarize(run_parser(args.samples_dir, files, target,
                                  os.path.join(tmpdir, "before.json")))
    after = summarize(run_parser(args.samples_dir, files, merged,
                                 os.path.join(tmpdir, "after.json")))

    regression = []
    print(f"\n{'样本':40s} {'unmapped':>9s} {'命中率':>14s}")
    for f in files:
        name = os.path.basename(f)
        b, a = before.get(name, {}), after.get(name, {})
        if not b or not a:
            print(f"{name:40s} {'缺结果':>9s}")
            continue
        um = f"{b['unmapped']} -> {a['unmapped']}"
        hr = f"{b['hit_rate']}% -> {a['hit_rate']}%"
        print(f"{name:40s} {um:>9s} {hr:>14s}")
        report["samples"][name] = {"before": b, "after": a}
        if a["hit_rate"] < b["hit_rate"] or a["unmapped"] > b["unmapped"]:
            regression.append(name)

    if regression and not args.force:
        print(f"\n[blocked] 检测到回归, 不写回: {regression}")
        return 2
    if args.apply:
        shutil.copyfile(merged, target)
        print(f"\n[apply] 无回归, 已写回 {target}")
    else:
        print("\n[dry-run] 未写回（加 --apply 生效）")
    if args.report:
        with open(args.report, "w", encoding="utf-8") as fh:
            json.dump(report, fh, ensure_ascii=False, indent=2)
        print(f"[report] {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
