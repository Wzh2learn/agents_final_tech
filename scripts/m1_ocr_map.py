#!/usr/bin/env python3
"""M1 OCR 兜底 · Phase 2/3：把 OCR 文本/表格送进同一套近义词映射，记录命中率。

读 ocr_results.json（30s 预算）与可选 ocr_probe.json（仅测量用、放宽超时），
对 probe 覆盖的 unit 以 probe 文本为准。复用 m1_statement_parser 的
Schema / best_schema_match / normalize_rows / extract_header_meta / desensitize_*。
OCR 文本先解析为表格（markdown 管道表 + 分隔线表 + 近义词表头启发式），再映射。
与同源 TXT 对比字符重叠（若存在；本批纯图样本无同源 TXT -> n/a）。
全部输出脱敏，写 /tmp，不入库。

用法（项目 venv）:
  ./venv/bin/python scripts/m1_ocr_map.py \
      --ocr /tmp/m1_ocr/ocr_results.json --probe /tmp/m1_ocr/ocr_probe.json \
      --samples-dir ~/wzh/m1_samples --out /tmp/m1_ocr/mapping_results.json
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import m1_statement_parser as P  # noqa: E402

_MD_SEP = re.compile(r"^:?-{2,}:?$")
_WS2 = re.compile(r"\s{2,}")


def _pipe_cells(line: str) -> list[str]:
    s = line.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|"):
        s = s[:-1]
    return [c.strip() for c in s.split("|")]


def _is_md_table_line(line: str) -> bool:
    s = line.strip()
    return s.count("|") >= 2 and (s.startswith("|") or s.endswith("|"))


def _parse_markdown_tables(text: str) -> list[P.ParsedTable]:
    """解析 markdown 管道表（含 |---| 分隔行）。"""
    tables: list[P.ParsedTable] = []
    lines = text.splitlines()
    n = len(lines)
    i = 0
    tidx = 0
    while i < n:
        if _is_md_table_line(lines[i]):
            block: list[list[str]] = []
            j = i
            while j < n and _is_md_table_line(lines[j]):
                block.append(_pipe_cells(lines[j]))
                j += 1
            # 找分隔行
            sep_idx = next((k for k, row in enumerate(block)
                            if row and all(_MD_SEP.match(c) for c in row if c)), -1)
            if sep_idx == 1 and len(block) >= 2:
                headers = block[0]
                rows = [r for r in block[2:] if any(c for c in r)]
            elif sep_idx == 0:
                headers = block[1] if len(block) > 1 else []
                rows = [r for r in block[2:] if any(c for c in r)]
            elif len(block) >= 2:
                headers = block[0]
                rows = [r for r in block[1:] if any(c for c in r)
                        and not all(_MD_SEP.match(c) for c in r if c)]
            else:
                i = j
                continue
            if len(headers) >= 2:
                tidx += 1
                tables.append(P.ParsedTable(f"md_table_{tidx}", headers, rows))
            i = j
            continue
        i += 1
    return tables


def _parse_sep_tables(text: str) -> list[P.ParsedTable]:
    """复用 parse_txt 的分隔线逻辑（表头行后跟 ---/=== 线）。"""
    lines = text.splitlines()
    n = len(lines)
    tables: list[P.ParsedTable] = []
    i = 0
    tidx = 0
    while i < n:
        line = lines[i]
        if line.strip() and i + 1 < n and P._SEP_RE.match(lines[i + 1]):
            headers = P._split_cells(line)
            j = i + 2
            rows: list[list[str]] = []
            while j < n and not P._SEP_RE.match(lines[j]) and lines[j].strip():
                rows.append(P._split_cells(lines[j]))
                j += 1
            if len(headers) >= 2:
                tidx += 1
                tables.append(P.ParsedTable(f"sep_table_{tidx}", headers, rows))
            i = j + 1 if j < n else j
            continue
        i += 1
    return tables


def _synonym_header_tables(text: str, schema: P.Schema) -> list[P.ParsedTable]:
    """启发式：某行 >=2 个单元格命中 schema 近义词 -> 视为表头，后续等列行视为数据。"""
    syns = {P.normalize_header(s) for t in schema.tables for f in t.fields for s in f.synonyms}
    syns = {s for s in syns if s}

    def hit(cell: str) -> bool:
        cn = P.normalize_header(cell)
        if not cn:
            return False
        for s in syns:
            if s == cn or (len(s) >= 2 and (s in cn or cn in s)):
                return True
        return False

    lines = [ln for ln in text.splitlines() if ln.strip()]
    tables: list[P.ParsedTable] = []
    tidx = 0
    used = set()
    for i, line in enumerate(lines):
        if i in used:
            continue
        cells = _WS2.split(line.strip()) or P._split_cells(line)
        if len(cells) < 2:
            continue
        if sum(1 for c in cells if hit(c)) < 2:
            continue
        headers = cells
        rows: list[list[str]] = []
        j = i + 1
        while j < len(lines):
            rc = _WS2.split(lines[j].strip()) or P._split_cells(lines[j])
            if abs(len(rc) - len(headers)) > 1 or not any(rc):
                break
            rows.append(rc)
            j += 1
        tidx += 1
        tables.append(P.ParsedTable(f"heur_table_{tidx}", headers, rows))
        for k in range(i, j):
            used.add(k)
    return tables


def parse_ocr_tables(text: str, schema: P.Schema) -> tuple[list[P.ParsedTable], list[str]]:
    """按优先级解析 OCR 文本为表格，返回 (tables, methods)。"""
    methods: list[str] = []
    tables = _parse_markdown_tables(text)
    if tables:
        methods.append("markdown")
    if not tables:
        tables = _parse_sep_tables(text)
        if tables:
            methods.append("separator")
    if not tables:
        tables = _synonym_header_tables(text, schema)
        if tables:
            methods.append("heuristic")
    return tables, methods


def char_overlap(a: str, b: str) -> float:
    """字符多重集重叠率（min-count / max-count），用于与同源 TXT 对比。"""
    if not a or not b:
        return 0.0
    from collections import Counter
    ca, cb = Counter(a), Counter(b)
    inter = sum((ca & cb).values())
    union = max(sum(ca.values()), sum(cb.values()))
    return round(inter / union, 3) if union else 0.0


def same_source_txt(sample_stem: str, samples_dir: Path) -> str | None:
    """查找同源 TXT（同 stem 去 sample_ 前缀的 .txt）；无则 None。"""
    base = sample_stem
    for prefix in ("sample_",):
        if base.startswith(prefix):
            base = base[len(prefix):]
    cand = samples_dir / f"{base}.txt"
    if cand.is_file():
        return cand.read_text(encoding="utf-8", errors="replace")
    # 也试 stem 直接
    cand2 = samples_dir / f"{sample_stem}.txt"
    if cand2.is_file():
        return cand2.read_text(encoding="utf-8", errors="replace")
    return None


def suspicious(table_reports: list[dict], methods: list[str], status: str, text_len: int) -> list[str]:
    flags: list[str] = []
    if status != "ok":
        flags.append(f"status={status}")
    if text_len == 0:
        flags.append("empty_ocr")
    if "heuristic" in methods:
        flags.append("heuristic_header")
    for t in table_reports:
        if t["rows"] == 0 and t["hits"] > 0:
            flags.append("header_only_no_rows")
        if t["hit_rate"] > 0 and t["hit_rate"] < 34:
            flags.append("low_hit_rate")
    return flags


def process_unit(unit: dict, schema: P.Schema, samples_dir: Path) -> dict:
    text = unit.get("text", "") or ""
    status = unit.get("status", "?")
    tables, methods = parse_ocr_tables(text, schema) if text else ([], [])
    table_reports: list[dict] = []
    best_hits = 0
    best_cols = 0
    for t in tables:
        match = P.best_schema_match(t.headers, schema)
        std_rows = P.normalize_rows(t.rows, match.mapping, t.headers)
        hit_rate = (match.hits / len(t.headers) * 100) if t.headers else 0.0
        best_hits = max(best_hits, match.hits)
        best_cols = max(best_cols, len(t.headers))
        table_reports.append({
            "table": t.name,
            "matched_schema": match.schema_table,
            "rows": len(t.rows),
            "cols": len(t.headers),
            "hits": match.hits,
            "hit_rate": round(hit_rate, 1),
            "mapping": P.desensitize_record(match.mapping),
            "unmapped": match.unmapped,
            "sample_record": P.desensitize_record(std_rows[0]) if std_rows else {},
        })
    meta = P.extract_header_meta(text, schema) if text else {}
    meta = P.desensitize_record(meta)
    txt = same_source_txt(unit["sample"], samples_dir)
    overlap = char_overlap(text, txt) if (text and txt) else None
    flags = suspicious(table_reports, methods, status, len(text))
    return {
        "sample": unit["sample"],
        "unit": unit["unit"],
        "png_basename": unit.get("png_basename", ""),
        "ocr_status": status,
        "ocr_text_len": len(text),
        "elapsed_sec": unit.get("elapsed_sec", 0.0),
        "parse_methods": methods,
        "n_tables": len(tables),
        "best_hits": best_hits,
        "best_cols": best_cols,
        "best_hit_rate": round(best_hits / best_cols * 100, 1) if best_cols else 0.0,
        "header_meta_count": len(meta),
        "header_meta": meta,
        "same_source_txt_overlap": overlap,
        "flags": flags,
        "tables": table_reports,
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="OCR 文本 -> 近义词映射 + 命中率记录")
    ap.add_argument("--ocr", default="/tmp/m1_ocr/ocr_results.json")
    ap.add_argument("--probe", default="/tmp/m1_ocr/ocr_probe.json")
    ap.add_argument("--samples-dir", default=os.path.expanduser("~/wzh/m1_samples"))
    ap.add_argument("--schema", default=os.path.expanduser("~/wzh/m1_samples/m1_table_schema.json"))
    ap.add_argument("--out", default="/tmp/m1_ocr/mapping_results.json")
    args = ap.parse_args(argv)

    schema = P.Schema.load(args.schema)
    ocr = json.load(open(args.ocr, encoding="utf-8"))
    units = { (r["sample"], r["unit"]): dict(r) for r in ocr["results"] }
    probe_note = ""
    if args.probe and Path(args.probe).is_file():
        probe = json.load(open(args.probe, encoding="utf-8"))
        for r in probe["results"]:
            key = (r["sample"], r["unit"])
            if r.get("status") == "ok" and r.get("text"):
                merged = dict(units.get(key, {}))
                merged.update(text=r["text"], text_len=r["text_len"],
                              elapsed_sec=r["elapsed_sec"], status="ok(probe)",
                              peak_cuda_memory_gib=r.get("peak_cuda_memory_gib"))
                units[key] = merged
        probe_note = f"probe merged: model={probe.get('model')} cold_start={probe.get('cold_start_sec')}"

    samples_dir = Path(args.samples_dir)
    mapped = [process_unit(u, schema, samples_dir) for u in units.values()]
    # 保持 manifest 顺序
    order = [(r["sample"], r["unit"]) for r in ocr["results"]]
    mapped.sort(key=lambda x: order.index((x["sample"], x["unit"])) if (x["sample"], x["unit"]) in order else 999)

    payload = {
        "schema_tables": [t.table_name for t in schema.tables],
        "ocr_model": ocr.get("model"),
        "ocr_cold_start_sec": ocr.get("cold_start_sec"),
        "ocr_timeout_sec": ocr.get("timeout_sec"),
        "probe_note": probe_note,
        "units": mapped,
    }
    Path(args.out).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"schema tables: {payload['schema_tables']}")
    print(f"ocr model={payload['ocr_model']} cold_start={payload['ocr_cold_start_sec']} "
          f"timeout={payload['ocr_timeout_sec']}s")
    if probe_note:
        print(probe_note)
    print(f"\n{'unit':34} {'status':12} {'len':>5} {'tbl':>3} {'best':>8} {'meta':>4} flags")
    for u in mapped:
        print(f"{u['png_basename'][:34]:34} {u['ocr_status'][:12]:12} {u['ocr_text_len']:>5} "
              f"{u['n_tables']:>3} {u['best_hits']}/{u['best_cols']}={u['best_hit_rate']:>4}% "
              f"{u['header_meta_count']:>4} {','.join(u['flags']) or '-'}")
    print(f"\n[out] {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
