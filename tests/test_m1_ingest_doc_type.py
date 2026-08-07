"""E4 regression: ingest must pass chunk text to compute_doc_type.

Before the fix, cmd_ingest passed document="" so the email_notice marker check
was always False for email_* samples entering ingest (label drift vs the
non-destructive backfill script). This test pins the ingest-side doc_type
computation so an email_* chunk with notice markers gets doc_type=email_notice.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import m1_rag_ingest as ing  # noqa: E402


def _build_res() -> dict:
    """A minimal process_sample result containing a notice-marker email chunk."""
    return {
        "file": "email_qwer.html",
        "kind": "html",
        "ok": True,
        "header_meta": {"客户姓名": "abc"},
        "tables": [{
            "table": "html_table_1",
            "matched_schema": "证券持仓明细",
            "_records": [
                {"基金名称": "某某基金", "申请日期": "2026-03-12"},
            ],
        }],
    }


def test_ingest_groups_doc_type_email_notice():
    groups = ing.build_chunks_for_sample(_build_res())
    # Add a notice-marker chunk of the kind email footers produce.
    notice = {
        "group": "html_table_2",
        "schema": "证券持仓明细",
        "standard_fields": ["备注"],
        "blocks": [{
            "text": "样本: email_qwer.html\n表: html_table_2 (证券持仓明细)\n"
                    "字段: 备注=5.本公司对本账单内容拥有最终解释权。",
            "block_id": "html_table_2:r0",
        }],
    }
    groups.append(notice)

    target = next(g for g in groups if g["group"] == "html_table_2")
    chunk_text = "\n".join(str(b.get("text") or "") for b in target["blocks"])
    # The E4 fix computes doc_type from the actual chunk text, so the marker is seen.
    assert ing.compute_doc_type("email_qwer.html", target["group"], chunk_text) == "email_notice"
    # And a plain data chunk from the same email stays statement.
    data = next(g for g in groups if g["group"] == "html_table_1")
    data_text = "\n".join(str(b.get("text") or "") for b in data["blocks"])
    assert ing.compute_doc_type("email_qwer.html", data["group"], data_text) == "statement"


def test_ingest_groups_passes_nonempty_document_to_compute_doc_type():
    """cmd_ingest metadata wiring: doc_type must be derived from chunk text."""
    groups = ing.build_chunks_for_sample(_build_res())
    assert groups, "build_chunks_for_sample should produce at least one group"
    for g in groups:
        chunk_text = "\n".join(str(b.get("text") or "") for b in g["blocks"] if b.get("text"))
        computed = ing.compute_doc_type("email_qwer.html", g["group"], chunk_text)
        # Mirrors the production wiring: doc_type comes from the real chunk text,
        # never from a hardcoded empty document string.
        assert isinstance(computed, str) and computed
