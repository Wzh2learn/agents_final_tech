#!/usr/bin/env python3
"""产品别名表构建器 (Q2, 2026-08-12)。

甲方映射表 (信息映射表 xlsx, 674 行) 是甲方口径 ground truth。本脚本确定性
(无 LLM) 提取三类资产写入 config/product_aliases.json:
- products:   基金名称 (组合产品) + NFKC 归一化别名 + 持仓证券数
- securities: 证券代码 -> {name, issuer, market} (代码/名称确定对)
- issuers:    发行公司名变体清单 (机构名变体, 供未来实体消歧)

用法:
  venv/bin/python scripts/build_product_aliases.py [--xlsx PATH] [--out PATH]
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import unicodedata
from datetime import date

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_XLSX = os.path.expanduser(
    "~/wzh/m1_samples/scenario1/信息映射表_20260715_160204_副本新综合信息查询_组合证券.xlsx")
DEFAULT_OUT = os.path.join(REPO_ROOT, "config", "product_aliases.json")


def normalize(name: str) -> str:
    """NFKC + 去空白: 全角/半角与空格差异不影响匹配。"""
    s = unicodedata.normalize("NFKC", str(name or "")).strip()
    return re.sub(r"\s+", "", s)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--xlsx", default=DEFAULT_XLSX)
    ap.add_argument("--out", default=DEFAULT_OUT)
    args = ap.parse_args()
    if not os.path.isfile(args.xlsx):
        print(f"ERROR: xlsx 不存在: {args.xlsx}", file=sys.stderr)
        return 2
    try:
        import openpyxl
    except ImportError:
        print("ERROR: 需要 openpyxl (venv)", file=sys.stderr)
        return 2

    wb = openpyxl.load_workbook(args.xlsx, read_only=True)
    ws = wb.worksheets[0]
    rows = [r for r in ws.iter_rows(values_only=True) if any(c is not None for c in r)]
    if not rows:
        print("ERROR: 空表", file=sys.stderr)
        return 2
    header = [str(c).strip() if c else "" for c in rows[0]]
    idx = {name: i for i, name in enumerate(header)}
    for col in ("基金名称", "证券代码", "证券名称"):
        if col not in idx:
            print(f"ERROR: 缺列 {col}; 实际表头={header}", file=sys.stderr)
            return 2
    i_fund, i_code, i_name = idx["基金名称"], idx["证券代码"], idx["证券名称"]
    i_market = idx.get("交易市场")
    i_issuer = idx.get("发行公司")

    products: dict[str, dict] = {}
    securities: dict[str, dict] = {}
    issuers: set[str] = set()
    for r in rows[1:]:
        fund = str(r[i_fund]).strip() if r[i_fund] else ""
        code = str(r[i_code]).strip() if r[i_code] else ""
        sname = str(r[i_name]).strip() if r[i_name] else ""
        market = str(r[i_market]).strip() if i_market is not None and r[i_market] else ""
        issuer = str(r[i_issuer]).strip() if i_issuer is not None and r[i_issuer] else ""
        if fund:
            key = normalize(fund)
            entry = products.setdefault(key, {
                "canonical": fund, "aliases": [], "position_count": 0,
                "security_codes": []})
            if fund not in entry["aliases"]:
                entry["aliases"].append(fund)
            entry["position_count"] += 1
            if code and code not in entry["security_codes"]:
                entry["security_codes"].append(code)
        if code and sname:
            sec = securities.setdefault(code, {"name": sname, "holders": set()})
            sec["name"] = sname
            if market:
                sec["market"] = market
            if issuer:
                sec["issuer"] = issuer
            if fund:
                sec["holders"].add(normalize(fund))
        if issuer:
            issuers.add(issuer)

    securities_out = {
        code: {"name": v["name"], **({"issuer": v["issuer"]} if v.get("issuer") else {}),
               **({"market": v["market"]} if v.get("market") else {}),
               "holder_count": len(v["holders"])}
        for code, v in sorted(securities.items())}
    products_out = {k: {**v, "security_codes": sorted(v["security_codes"])}
                    for k, v in sorted(products.items())}
    out = {
        "_comment": "甲方映射表 ground truth 确定性别名表; 由 scripts/build_product_aliases.py 生成, 勿手改。",
        "source_file": os.path.basename(args.xlsx),
        "built_at": date.today().isoformat(),
        "row_count": len(rows) - 1,
        "products": products_out,
        "securities": securities_out,
        "issuers": sorted(issuers),
    }
    tmp = args.out + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1)
    os.replace(tmp, args.out)
    print(f"[aliases] products={len(products_out)} securities={len(securities_out)} "
          f"issuers={len(issuers)} rows={len(rows) - 1} -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
