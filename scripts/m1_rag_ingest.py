#!/usr/bin/env python3
"""M1 -> M2 闭环：把 M1 对账单解析结果写入 PGVector 并做 RAG QA 验证。

设计要点（遵守仓库数据安全边界）：
- 真实样本只在内存中解析，绝不把原始值落库/落盘；写入向量库前对每条标准化
  记录调用解析器自带的 desensitize_record 脱敏（字段名/表名保留，值打码）。
- 入库走 RAGService.ingest_parsed_blocks（不绕过 RAGService、不另建向量库）。
- 检索走 RAGService.smart_retrieve（向量 + BM25 混合），验证 M1 结果可被问答命中。

用法:
    ./venv/bin/python scripts/m1_rag_ingest.py ingest   # 解析+脱敏+入库
    ./venv/bin/python scripts/m1_rag_ingest.py verify   # 3 条 QA 检索验证
    ./venv/bin/python scripts/m1_rag_ingest.py all      # 先入库再验证
    ./venv/bin/python scripts/m1_rag_ingest.py ingest --append  # 不先清空集合
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Any

# ---- 路径与运行环境 -------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

# 本地 embedding（Qwen3-Embedding-0.6B）+ 本地 PGVector。
# 设备默认 cpu：GB10 aarch64 上 triton 的 CUDA JIT 编译失败，CPU 对少量 chunk 足够快。
os.environ.setdefault(
    "LOCAL_EMBEDDING_MODEL_PATH",
    str(Path.home() / "wzh" / "models" / "hf" / "qwen3-embedding-0.6b"),
)
os.environ.setdefault("LOCAL_EMBEDDING_DEVICE", "cpu")
os.environ.setdefault(
    "PGDATABASE_URL", "postgresql://postgres:postgres@127.0.0.1:15432/vector_db"
)

COLLECTION = "m1_parsed_statements"

# 解析器（scripts/m1_statement_parser.py）
import m1_statement_parser as m1p  # noqa: E402

# RAG 业务层
from biz.rag_service import RAGService  # noqa: E402


# 三条验证查询：(query, 期望样本前缀, 期望命中的字段/表关键词)
VERIFY_QUERIES: list[tuple[str, str, str]] = [
    ("复熙混合25号的资产总值是多少？", "sample_fuxi_hunhe25", "资产总值"),
    ("嘉兴民安有哪些证券持仓？", "sample_jiaxing_minan", "证券持仓"),
    ("博时传统产品的基金名称是什么？", "sample_boshi_chuantong", "基金名称"),
]


# --- Product metadata extraction (raw, non-desensitized) --------------------
# process_sample() desensitizes header_meta before returning, but metadata
# enrichment needs actual product names / dates for PGVector filtering.
_PRODUCT_NAME_KEYS = ["客户全称", "客户名称", "产品名称", "基金名称", "客户姓名"]
_STATEMENT_DATE_KEYS = ["开始日期", "对账日期", "统计日期", "结束日期", "打印时间"]
_FILENAME_DATE_RE = re.compile(r"(\d{8})")


def _extract_raw_header_meta(path: str, schema) -> dict[str, str]:
    """Re-parse file to get raw (non-desensitized) header_meta."""
    ext = os.path.splitext(path)[1].lower()
    parser = m1p.PARSERS.get(ext)
    if parser is None:
        return {}
    doc = parser(path)
    if not doc.ok:
        return {}
    meta = m1p.extract_header_meta(doc.text, schema)
    ua_kv = m1p.scan_unattributed_kv(doc.text, schema)
    for k, v in ua_kv.items():
        if k not in meta:
            meta[k] = v
    return meta


def extract_product_name(meta: dict[str, str]) -> str:
    """Extract product name from raw header_meta (first non-empty key hit)."""
    for key in _PRODUCT_NAME_KEYS:
        val = (meta.get(key) or "").strip()
        if val:
            return val
    return ""


def extract_statement_date(meta: dict[str, str]) -> str:
    """Extract statement date from raw header_meta.

    For date ranges like ``20231101 - 20231101``, takes the first date.
    """
    for key in _STATEMENT_DATE_KEYS:
        val = (meta.get(key) or "").strip()
        if val:
            for sep in (" - ", " ~ ", " 至 ", " — "):
                if sep in val:
                    val = val.split(sep)[0].strip()
                    break
            # Normalise Chinese date format: "2023年11月02日 ..." -> "20231102"
            m = re.match(r"(\d{4})年(\d{1,2})月(\d{1,2})日", val)
            if m:
                return f"{m.group(1)}{int(m.group(2)):02d}{int(m.group(3)):02d}"
            # Already YYYYMMDD?
            m2 = re.match(r"^(\d{8})", val)
            if m2:
                return m2.group(1)
            return val
    return ""


def extract_date_from_filename(filename: str) -> str:
    """Fallback: extract YYYYMMDD date from the sample filename."""
    m = _FILENAME_DATE_RE.search(filename)
    return m.group(1) if m else ""


def _list_sample_files(samples_dir: str) -> list[str]:
    """只取 sample_* 的 5 个甲方对账单（排除 mapping_* 参考表）。"""
    exts = set(m1p.PARSERS.keys())
    files = []
    for name in sorted(os.listdir(samples_dir)):
        if name.startswith("sample_") and os.path.splitext(name)[1].lower() in exts:
            files.append(os.path.join(samples_dir, name))
    return files


def _fmt_record(sample_id: str, table_name: str, schema_name: str, rec: dict[str, str]) -> str:
    """把一条标准化记录渲染成 chunk 文本（值已脱敏）。"""
    fields = ", ".join(f"{k}={v}" for k, v in rec.items() if v not in (None, ""))
    return (
        f"样本: {sample_id}\n"
        f"表: {table_name} ({schema_name})\n"
        f"字段: {fields}"
    )


def build_chunks_for_sample(res: dict[str, Any]) -> list[dict[str, Any]]:
    """把一个样本的解析结果转成若干入库分组。

    返回: [{group, schema, standard_fields, blocks:[{text, block_id}]}]
    每条记录单独一个 chunk；表头区 KV 汇总成一个 chunk。
    """
    sample_id = res["file"]
    groups: list[dict[str, Any]] = []

    # 表头区 KV（解析器已脱敏）
    meta = res.get("header_meta") or {}
    if meta:
        text = (
            f"样本: {sample_id}\n"
            f"表: 表头信息\n"
            f"字段: " + ", ".join(f"{k}={v}" for k, v in meta.items() if v not in (None, ""))
        )
        groups.append({
            "group": "表头信息",
            "schema": "表头信息",
            "standard_fields": list(meta.keys()),
            "blocks": [{"text": text, "block_id": "header_meta:0"}],
        })

    # 逐表标准化记录（_records 为原始值，这里逐条脱敏后再渲染）
    for t in res.get("tables", []):
        table_name = t.get("table", "")
        schema_name = t.get("matched_schema", "")
        records = t.get("_records") or []
        blocks = []
        fields_seen: list[str] = []
        for i, raw in enumerate(records):
            safe = m1p.desensitize_record(raw)
            if not any(v not in (None, "") for v in safe.values()):
                continue  # 跳过全空记录（如 xinhua 的 0 命中 OCR 表）
            if not fields_seen:
                fields_seen = list(safe.keys())
            blocks.append({
                "text": _fmt_record(sample_id, table_name, schema_name, safe),
                "block_id": f"{table_name}:r{i}",
            })
        if blocks:
            groups.append({
                "group": table_name,
                "schema": schema_name,
                "standard_fields": fields_seen,
                "blocks": blocks,
            })
    return groups



def build_meta_chunks(res: dict[str, Any], parse_ms: int) -> list[dict[str, Any]]:
    """Build reconcile summary + parse metadata chunks for a sample."""
    sample_id = res["file"]
    groups: list[dict[str, Any]] = []

    # --- Reconcile summary chunk ---
    checks = res.get("reconcile") or []
    if checks:
        total = len(checks)
        real_pass = sum(1 for c in checks if c.get("disposition") == "real_pass")
        skipped = sum(1 for c in checks if c.get("disposition") == "skipped")
        failed = sum(1 for c in checks if c.get("disposition") == "fail")
        if failed == 0 and skipped == 0:
            disposition = "全部通过"
        elif failed == 0:
            disposition = "通过(部分跳过)"
        else:
            disposition = "存在失败"
        details = "; ".join(
            f"{c['check']}={c.get('disposition', '?')}" for c in checks
        )
        text = (
            f"样本: {sample_id}\n"
            f"表: 勾稽校验\n"
            f"字段: 勾稽结论={disposition}, 通过={real_pass}/{total}, "
            f"跳过={skipped}, 失败={failed}, 明细=[{details}]"
        )
        groups.append({
            "group": "勾稽校验",
            "schema": "勾稽校验",
            "standard_fields": ["勾稽结论", "通过", "跳过", "失败", "明细"],
            "blocks": [{"text": text, "block_id": "reconcile:summary"}],
        })

    # --- Parse metadata chunk ---
    ocr_used = res.get("ocr_used", False)
    ocr_engine = res.get("ocr_engine", "")
    table_count = res.get("table_count", 0)
    engine_label = ocr_engine if ocr_used and ocr_engine else "规则解析"
    text = (
        f"样本: {sample_id}\n"
        f"表: 解析元数据\n"
        f"字段: 解析耗时={parse_ms}ms, 解析引擎={engine_label}, "
        f"表数={table_count}, 解析速度={parse_ms}ms"
    )
    groups.append({
        "group": "解析元数据",
        "schema": "解析元数据",
        "standard_fields": ["解析耗时", "OCR", "表数", "解析速度"],
        "blocks": [{"text": text, "block_id": "parse_meta:0"}],
    })

    return groups


def cmd_ingest(samples_dir: str, schema_path: str, append: bool) -> int:
    schema = m1p.Schema.load(schema_path)
    sample_files = _list_sample_files(samples_dir)
    print(f"[ingest] samples: {len(sample_files)} | collection: {COLLECTION}")

    rag = RAGService(collection_name=COLLECTION)

    if not append:
        try:
            from tools.vector_store import get_vector_store
            get_vector_store(collection_name=COLLECTION).delete_collection()
            print(f"[ingest] reset: dropped existing collection {COLLECTION}")
        except Exception as exc:  # 集合不存在等
            print(f"[ingest] reset: no existing collection to drop ({type(exc).__name__})")

    total_chunks = 0
    summary = []
    for path in sample_files:
        t0 = time.perf_counter()
        res = m1p.process_sample(path, schema, llm_fallback=False)
        parse_ms = int((time.perf_counter() - t0) * 1000)
        if not res.get("ok"):
            print(f"[ingest] SKIP {res.get('file')}: parse not ok ({res.get('error')})")
            continue
        # Extract raw (non-desensitized) product metadata for PGVector filtering
        raw_meta = _extract_raw_header_meta(path, schema)
        product_name = extract_product_name(raw_meta)
        statement_date = extract_statement_date(raw_meta)
        if not statement_date:
            statement_date = extract_date_from_filename(os.path.basename(path))
        groups = build_chunks_for_sample(res)
        groups.extend(build_meta_chunks(res, parse_ms))
        # Filter: skip samples with no financial structure (e.g. operational docs)
        if not groups and not res.get("header_meta"):
            print(f"[ingest] SKIP {res['file']}: no financial structure (0 tables, 0 header_meta)")
            summary.append({
                "sample_id": res["file"],
                "kind": res.get("kind"),
                "groups": 0,
                "chunks": 0,
                "needs_ocr": res.get("needs_ocr", False),
                "skipped": "no_financial_structure",
            })
            continue
        sample_chunks = 0
        for g in groups:
            metadata = {
                "sample_id": res["file"],
                "kind": res.get("kind", ""),
                "table_name": g["group"],
                "matched_schema": g["schema"],
                "standard_fields": ",".join(g["standard_fields"]),
                "source": res["file"],
                "product_name": product_name,
                "statement_date": statement_date,
            }
            out = rag.ingest_parsed_blocks(
                document_id=res["file"],
                blocks=g["blocks"],
                metadata=metadata,
                collection_name=COLLECTION,
            )
            sample_chunks += out["chunks"]
        total_chunks += sample_chunks
        summary.append({
            "sample_id": res["file"],
            "kind": res.get("kind"),
            "groups": len(groups),
            "chunks": sample_chunks,
            "needs_ocr": res.get("needs_ocr", False),
        })
        print(f"[ingest] {res['file']}: {len(groups)} groups, {sample_chunks} chunks")

    print(f"[ingest] DONE total_chunks={total_chunks}")
    print("[ingest] summary=" + json.dumps(summary, ensure_ascii=False))
    return 0


def cmd_verify(top_k: int) -> int:
    rag = RAGService(collection_name=COLLECTION)
    available = rag.get_collection_names()
    if COLLECTION not in available:
        print(f"[verify] ERROR collection {COLLECTION} not found; run ingest first")
        print(f"[verify] available collections: {available}")
        return 2
    print(f"[verify] collection {COLLECTION} present | top_k={top_k}")

    results = []
    relevant_count = 0
    for query, want_sample, want_key in VERIFY_QUERIES:
        try:
            docs = rag.smart_retrieve(
                query=query,
                top_k=top_k,
                collection_names=[COLLECTION],
                max_results=top_k,
                use_rerank=False,
            )
        except Exception as exc:
            print(f"[verify] QUERY FAIL: {query!r} -> {type(exc).__name__}: {exc}")
            results.append({"query": query, "relevant": False, "error": str(exc)})
            continue

        hit = False
        retrieved = []
        for d in docs:
            # smart_retrieve 返回 {"content", "metadata", "relevance_score"}
            md = d.get("metadata", {})
            content = d.get("content", "")
            sid = str(md.get("sample_id", ""))
            if want_sample in sid and want_key in content:
                hit = True
            retrieved.append({
                "sample_id": sid,
                "table_name": md.get("table_name", ""),
                "block_id": md.get("block_id", ""),
                "score": round(float(d.get("relevance_score") or 0.0), 4),
                "text": content.replace("\n", " ")[:160],
            })
        relevant_count += 1 if hit else 0
        results.append({"query": query, "want_sample": want_sample,
                        "want_key": want_key, "relevant": hit, "retrieved": retrieved})
        print(f"[verify] Q: {query}")
        print(f"        relevant={hit} (want sample~{want_sample}, key~{want_key})")
        for r in retrieved[:top_k]:
            print(f"        - [{r['sample_id']}|{r['table_name']}|{r['block_id']}] {r['text']}")

    print(f"[verify] RELEVANT {relevant_count}/{len(VERIFY_QUERIES)}")
    print("[verify] json=" + json.dumps(results, ensure_ascii=False))
    return 0 if relevant_count >= 2 else 1


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="M1->M2 RAG 闭环：入库 + QA 验证")
    ap.add_argument("mode", choices=["ingest", "verify", "all"])
    ap.add_argument("--samples-dir", default=m1p.DEFAULT_SAMPLES_DIR)
    ap.add_argument("--schema", default=m1p.resolve_schema_path())
    ap.add_argument("--append", action="store_true", help="ingest 前不清空集合")
    ap.add_argument("--top-k", type=int, default=5)
    args = ap.parse_args(argv)

    if args.mode in ("ingest", "all"):
        rc = cmd_ingest(args.samples_dir, args.schema, args.append)
        if rc != 0:
            return rc
    if args.mode in ("verify", "all"):
        return cmd_verify(args.top_k)
    return 0


if __name__ == "__main__":
    sys.exit(main())
