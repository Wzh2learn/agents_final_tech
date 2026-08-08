#!/usr/bin/env python3
"""HTML 邮件对账单 schema 匹配（P1.2 沉淀, 2026-08-09 重建）。

背景：scenario1 的 3 封邮件正文为 HTML（国金/南华/财通），08-01 曾以临时脚本
完成「HTML 提取 → 表格」并产出 html_extracted/*_tables.json，但匹配脚本未入库。
本脚本从提取产物出发做确定性 schema 匹配（复用 parser 的 map_headers 逻辑），
让 HTML 邮件链路的命中率可复现、可进回归门禁。

用法：
  python scripts/m1_html_email_parse.py --extracted-dir ~/wzh/m1_samples/scenario1/html_extracted \
      [--schema ~/wzh/m1_samples/m1_table_schema.json] [--json OUT]
"""

from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from m1_statement_parser import (  # noqa: E402
    Schema, ParsedTable, best_schema_match, normalize_rows,
    desensitize_record, resolve_schema_path,
)


def parse_extracted(path: str, schema: Schema) -> dict:
    with open(path, encoding="utf-8") as fh:
        raw_tables = json.load(fh)
    reports = []
    for i, t in enumerate(raw_tables):
        headers = [str(h) for h in t.get("headers", [])]
        records = t.get("records", [])
        rows = [[str(r.get(h, "")) for h in headers] for r in records]
        pt = ParsedTable(name=t.get("table", f"html_table_{i + 1}"),
                         headers=headers, rows=rows)
        match = best_schema_match(headers, schema)
        std_rows = normalize_rows(rows, match.mapping, headers)
        hit_rate = (match.hits / len(headers) * 100) if headers else 0.0
        reports.append({
            "table": pt.name,
            "rows": len(rows),
            "cols": len(headers),
            "matched_schema": match.schema_table,
            "mapping": match.mapping,
            "unmapped": match.unmapped,
            "hits": match.hits,
            "hit_rate": round(hit_rate, 1),
            "sample_record": desensitize_record(std_rows[0]) if std_rows else {},
        })
    name = os.path.basename(path).replace("_tables.json", "")
    return {"email": name, "file": os.path.basename(path), "ok": True,
            "table_count": len(reports), "tables": reports}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--extracted-dir", required=True)
    ap.add_argument("--schema", default=resolve_schema_path())
    ap.add_argument("--json", default="")
    args = ap.parse_args(argv)

    schema = Schema.load(args.schema)
    files = sorted(
        os.path.join(args.extracted_dir, f)
        for f in os.listdir(args.extracted_dir)
        if f.endswith("_tables.json"))
    results = [parse_extracted(p, schema) for p in files]

    print(f'{"邮件":10s} {"表格":>4s}   表/命中')
    for r in results:
        hits = ";".join(f'{t["hits"]}/{t["cols"]}' for t in r["tables"])
        print(f'{r["email"]:10s} {r["table_count"]:>4d}   {hits}')
    if args.json:
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump(results, fh, ensure_ascii=False, indent=2)
        print(f"\n[json] {args.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
