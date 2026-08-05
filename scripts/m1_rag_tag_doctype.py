#!/usr/bin/env python3
"""给 m1_parsed_statements 集合的 chunks 非破坏性地标记 doc_type metadata。

背景（2026-08-05, Loop A OCR meta-query 修复任务）:
- email 正文解析出的"特别提示/风险提示"类 chunk（样板免责文本）含表名字面量
  （如"交易对账单"），纯向量检索下会压过真正的 OCR 解析证据 chunk。
- RAGService.smart_retrieve 对 OCR 溯源类查询按 doc_type 重排
  （见 src/biz/rag_service.py 的 _apply_doc_type_rescore），本脚本负责把
  doc_type 写进 PGVector 的 cmetadata。

安全性:
- 只 UPDATE cmetadata（jsonb 合并 ||），不碰 document/embedding，不删不灌；
  幂等：重复运行 0 变更。
- 只作用于 m1_parsed_statements 集合。

doc_type 规则:
- ocr_table     : table_name 以 "ocr_" 开头（OCR 提取的表，OCR 解析的直接证据）
- parse_meta    : table_name == "解析元数据"
- reconcile     : table_name == "勾稽校验"
- header_meta   : table_name == "表头信息"
- email_notice  : sample_id 以 "email_" 开头且正文含提示/免责样板标记词
- statement     : 其余（正常业务表数据）

用法:
    ./venv/bin/python scripts/m1_rag_tag_doctype.py            # 应用
    ./venv/bin/python scripts/m1_rag_tag_doctype.py --dry-run  # 只报告
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

# 复用入库脚本的环境变量设置与 COLLECTION 常量（不重复配置）
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

import m1_rag_ingest as ing  # noqa: E402  (sets PGDATABASE_URL etc.)

from sqlalchemy import create_engine, text  # noqa: E402

COLLECTION = ing.COLLECTION

# 规则单一信源在 m1_rag_ingest.compute_doc_type（ingest 与本脚本共用，避免漂移）
compute_doc_type = ing.compute_doc_type


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="非破坏性标记 m1_parsed_statements chunks 的 doc_type")
    ap.add_argument("--dry-run", action="store_true", help="只报告将发生的变更，不写库")
    args = ap.parse_args(argv)

    eng = create_engine(ing.os.environ["PGDATABASE_URL"])
    with eng.begin() as conn:
        cid = conn.execute(
            text("SELECT uuid FROM langchain_pg_collection WHERE name=:n"),
            {"n": COLLECTION},
        ).scalar()
        if cid is None:
            print(f"[tag-doctype] ERROR collection {COLLECTION} not found")
            return 2
        rows = conn.execute(
            text(
                "SELECT id, document, cmetadata FROM langchain_pg_embedding "
                "WHERE collection_id=:c"
            ),
            {"c": cid},
        ).fetchall()

        plan = []  # (id, old_doc_type, new_doc_type, sample_id, table_name)
        dist_new: Counter = Counter()
        for row_id, document, cmetadata in rows:
            md = cmetadata or {}
            new_type = compute_doc_type(
                md.get("sample_id", ""), md.get("table_name", ""), document
            )
            dist_new[new_type] += 1
            if md.get("doc_type") != new_type:
                plan.append((row_id, md.get("doc_type"), new_type,
                             md.get("sample_id", ""), md.get("table_name", "")))

        print(f"[tag-doctype] collection={COLLECTION} chunks={len(rows)}")
        print("[tag-doctype] target distribution: "
              + ", ".join(f"{k}={v}" for k, v in sorted(dist_new.items())))
        print(f"[tag-doctype] changes to apply: {len(plan)}")
        for row_id, old, new, sid, tn in plan:
            print(f"  {str(old) or '-':>12s} -> {new:12s} | {str(sid)[:48]:48s} | {tn}")

        if args.dry_run:
            print("[tag-doctype] DRY-RUN: no writes performed")
            return 0

        for row_id, _old, new, _sid, _tn in plan:
            conn.execute(
                text(
                    "UPDATE langchain_pg_embedding "
                    "SET cmetadata = COALESCE(cmetadata, '{}'::jsonb) || CAST(:tag AS jsonb) "
                    "WHERE id=:id AND collection_id=:c"
                ),
                {"tag": json.dumps({"doc_type": new}, ensure_ascii=False),
                 "id": row_id, "c": cid},
            )

        # 复核
        check = conn.execute(
            text(
                "SELECT cmetadata->>'doc_type', count(*) FROM langchain_pg_embedding "
                "WHERE collection_id=:c GROUP BY 1 ORDER BY 2 DESC"
            ),
            {"c": cid},
        ).fetchall()
        print("[tag-doctype] applied. doc_type now in DB: "
              + ", ".join(f"{k}={v}" for k, v in check))
    return 0


if __name__ == "__main__":
    sys.exit(main())
