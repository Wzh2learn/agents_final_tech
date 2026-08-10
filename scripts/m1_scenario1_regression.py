#!/usr/bin/env python3
"""scenario1 回归门禁 (P1.2 沉淀, 2026-08-09)。

固化甲方真实样本 scenario1 全部 15 源的解析命中率；schema/parser/OCR prompt
任何改动后必跑。口径与 :5050 生产一致 (resolve_schema_path, config/ 优先)。

判定策略：
- 确定性样本 (嘉合×8 / NCAMC / HTML×3): table_count 与逐表命中率精确一致
- OCR 样本 (华泰紫金/TraFax/WaveFax): vision 输出非确定性, 逐表命中率容差
  ±tolerance.ocr_hit_rate_pp (默认 10pp), 表数容差 ±ocr_table_count_delta;
  容差内表数差异记 WARN 不判 FAIL, 命中率下降超差判 FAIL;
  命中率上升超差记 WARN(改善, 建议 --rebuild 重建基线), 非 OCR 样本同理。

用法:
  python scripts/m1_scenario1_regression.py            # 全量 (~2-4min, 含 OCR)
  python scripts/m1_scenario1_regression.py --quick    # 跳 OCR 样本 (~5s)
  python scripts/m1_scenario1_regression.py --rebuild  # 重跑并覆写基线 (慎用)

Loop B 挂载 (可选, Loop B 本体不改): scripts/m1_scenario1_regression.py --quick
退出码: 0=PASS 1=FAIL 2=环境/文件缺失
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
import time

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASELINE_PATH = os.path.join(REPO_ROOT, "tests", "baselines",
                             "scenario1_baseline.json")
PARSER = os.path.join(REPO_ROOT, "scripts", "m1_statement_parser.py")
HTML_TOOL = os.path.join(REPO_ROOT, "scripts", "m1_html_email_parse.py")
REPORT_DEFAULT = os.path.join(REPO_ROOT, "logs", "graph",
                              "scenario1_regression_report.json")


def _expand(p: str) -> str:
    return os.path.expanduser(p)


def _run(cmd: list[str], timeout: int) -> None:
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if proc.returncode != 0:
        raise RuntimeError(
            f"command failed rc={proc.returncode}: {' '.join(cmd[:4])}...\n"
            f"{proc.stderr[-800:]}")


def run_pdf_cases(attach_dir: str, files: list[str], tmpdir: str) -> dict:
    out = os.path.join(tmpdir, "pdf_results.json")
    _run([sys.executable, PARSER, "--samples-dir", attach_dir, "--no-llm",
          "--files", *files, "--json", out], timeout=1800)
    with open(out, encoding="utf-8") as fh:
        return {r["file"]: r for r in json.load(fh)}


def run_html_cases(html_dir: str, tmpdir: str) -> dict:
    out = os.path.join(tmpdir, "html_results.json")
    _run([sys.executable, HTML_TOOL, "--extracted-dir", html_dir,
          "--json", out], timeout=300)
    with open(out, encoding="utf-8") as fh:
        return {f'html_extracted/{h["email"]}_tables.json': h
                for h in json.load(fh)}


def compare_case(case: dict, hit_rates: list[float], table_count: int,
                 tol: dict) -> tuple[str, list[str]]:
    """返回 (PASS|WARN|FAIL, 差异说明列表)。"""
    diffs: list[str] = []
    exp_hits, exp_tc = case["hit_rates"], case["table_count"]
    status = "PASS"
    if case["ocr_expected"]:
        pp = float(tol.get("ocr_hit_rate_pp", 10.0))
        dtc = int(tol.get("ocr_table_count_delta", 1))
        if abs(table_count - exp_tc) > dtc:
            diffs.append(f"表数 {exp_tc} -> {table_count} 超出容差 ±{dtc}")
            status = "FAIL"
        elif table_count != exp_tc:
            diffs.append(f"表数 {exp_tc} -> {table_count} (容差内, WARN)")
            status = "WARN"
        for i in range(min(len(exp_hits), len(hit_rates))):
            d = hit_rates[i] - exp_hits[i]
            if d < -pp:
                diffs.append(f"表{i + 1} 命中率 {exp_hits[i]}% -> {hit_rates[i]}% "
                             f"(下降 {round(-d, 1)}pp > {pp}pp)")
                status = "FAIL"
            elif d > pp:
                diffs.append(f"表{i + 1} 命中率 {exp_hits[i]}% -> {hit_rates[i]}% "
                             f"(提升 {round(d, 1)}pp, 建议 --rebuild 更新基线)")
                if status != "FAIL":
                    status = "WARN"
            elif d != 0:
                diffs.append(f"表{i + 1} 命中率 {exp_hits[i]}% -> {hit_rates[i]}% (容差内)")
    else:
        if table_count != exp_tc:
            diffs.append(f"表数 {exp_tc} -> {table_count}")
            status = "FAIL"
        if hit_rates != exp_hits:
            dropped = any(a < e for e, a in zip(exp_hits, hit_rates))
            diffs.append(f"命中率 {exp_hits} -> {hit_rates}"
                         + (" (下降)" if dropped else " (提升, 建议 --rebuild 更新基线)"))
            status = "FAIL" if dropped else "WARN"
    return status, diffs


def collect_actual(cases: list[dict], baseline: dict, tmpdir: str,
                   quick: bool) -> list[dict]:
    attach_dir = _expand(baseline["attachments_dir"])
    html_dir = _expand(baseline["html_extracted_dir"])
    pdf_cases = [c for c in cases if c["kind"] == "pdf"
                 and not (quick and c["ocr_expected"])]
    html_cases = [c for c in cases if c["kind"] == "html"]

    pdf_results = {}
    if pdf_cases:
        missing = [c["file"] for c in pdf_cases
                   if not os.path.isfile(os.path.join(attach_dir, c["file"]))]
        if missing:
            raise FileNotFoundError(f"附件缺失: {missing[:3]} ...")
        pdf_results = run_pdf_cases(
            attach_dir, [os.path.join(attach_dir, c["file"]) for c in pdf_cases],
            tmpdir)
    html_results = run_html_cases(html_dir, tmpdir) if html_cases else {}

    rows = []
    for c in cases:
        if quick and c["ocr_expected"]:
            rows.append({"label": c["label"], "status": "SKIP(quick)",
                         "diffs": [], "expected": c["hit_rates"], "actual": []})
            continue
        res = (pdf_results.get(c["file"]) if c["kind"] == "pdf"
               else html_results.get(c["file"]))
        if res is None:
            rows.append({"label": c["label"], "status": "FAIL",
                         "diffs": ["无解析结果"], "expected": c["hit_rates"],
                         "actual": []})
            continue
        hits = [t["hit_rate"] for t in res.get("tables", [])]
        status, diffs = compare_case(c, hits, res.get("table_count", 0),
                                     baseline.get("tolerance", {}))
        rows.append({"label": c["label"], "kind": c["kind"],
                     "ocr_expected": c["ocr_expected"], "status": status,
                     "diffs": diffs, "expected": c["hit_rates"], "actual": hits})
    return rows



def do_rebuild(args) -> int:
    """重跑全部 15 源, 以实跑结果覆写基线 (OCR 漂移确认后使用)。"""
    try:
        with open(args.baseline, encoding="utf-8") as fh:
            baseline = json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"[env] 基线文件不可读: {exc}", file=sys.stderr)
        return 2  # F11: 环境缺失与真 FAIL 分开（契约: 0=PASS 1=FAIL 2=env）
    attach_dir = _expand(baseline["attachments_dir"])
    html_dir = _expand(baseline["html_extracted_dir"])
    with tempfile.TemporaryDirectory(prefix="scenario1_rebuild_") as tmpdir:
        pdf_files = [os.path.join(attach_dir, c["file"])
                     for c in baseline["cases"] if c["kind"] == "pdf"]
        pdf_results = run_pdf_cases(attach_dir, pdf_files, tmpdir)
        html_results = run_html_cases(html_dir, tmpdir)
    cases = []
    for c in baseline["cases"]:
        res = (pdf_results.get(c["file"]) if c["kind"] == "pdf"
               else html_results.get(c["file"]))
        if res is None:
            print(f"[rebuild][warn] 无结果, 保留旧条目: {c['label']}",
                  file=sys.stderr)
            cases.append(c)
            continue
        nc = dict(c)
        nc["table_count"] = res.get("table_count", 0)
        nc["hit_rates"] = [t["hit_rate"] for t in res.get("tables", [])]
        cases.append(nc)
        print(f"  {c['label']:16s} tables={nc['table_count']} hits={nc['hit_rates']}")
    baseline["cases"] = cases
    baseline["created"] = time.strftime("%Y-%m-%d")
    with open(args.baseline, "w", encoding="utf-8") as fh:
        json.dump(baseline, fh, ensure_ascii=False, indent=2)
    print(f"[rebuild] 基线已覆写: {args.baseline}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--baseline", default=BASELINE_PATH)
    ap.add_argument("--quick", action="store_true",
                    help="跳过 OCR 样本（快速门禁, 约 5s）")
    ap.add_argument("--rebuild", action="store_true",
                    help="重跑全部样本并覆写基线（基线漂移确认后使用）")
    ap.add_argument("--report", default=REPORT_DEFAULT)
    args = ap.parse_args(argv)

    if args.rebuild:
        return do_rebuild(args)

    try:
        with open(args.baseline, encoding="utf-8") as fh:
            baseline = json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"[env] 基线文件不可读: {exc}", file=sys.stderr)
        return 2  # F11: 契约 0=PASS 1=FAIL 2=env
    cases = baseline["cases"]
    t0 = time.time()

    with tempfile.TemporaryDirectory(prefix="scenario1_reg_") as tmpdir:
        rows = collect_actual(cases, baseline, tmpdir, args.quick)

    n_fail = sum(1 for r in rows if r["status"] == "FAIL")
    n_warn = sum(1 for r in rows if r["status"] == "WARN")
    n_pass = sum(1 for r in rows if r["status"] == "PASS")
    n_skip = sum(1 for r in rows if r["status"].startswith("SKIP"))

    print(f'{"样本":16s} {"状态":10s} 差异')
    for r in rows:
        diff_txt = "; ".join(r["diffs"]) if r["diffs"] else "-"
        print(f'{r["label"]:16s} {r["status"]:10s} {diff_txt[:110]}')
    overall = "FAIL" if n_fail else "PASS"
    print(f"\n[scenario1-regression] {overall}: {n_pass} pass / {n_warn} warn / "
          f"{n_fail} fail / {n_skip} skip, 耗时 {time.time() - t0:.1f}s")

    os.makedirs(os.path.dirname(args.report), exist_ok=True)
    with open(args.report, "w", encoding="utf-8") as fh:
        json.dump({"timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                   "overall": overall, "quick": args.quick,
                   "baseline": os.path.basename(args.baseline),
                   "rows": rows}, fh, ensure_ascii=False, indent=2)
    print(f"[report] {args.report}")
    return 1 if n_fail else 0


if __name__ == "__main__":
    raise SystemExit(main())
