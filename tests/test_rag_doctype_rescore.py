"""Unit tests for doc_type tagging + OCR-provenance rescore (2026-08-05).

Covers:
- biz.m1_rag_ingest.compute_doc_type  (doc_type 规则单一信源)
- biz.rag_service.RAGService._apply_doc_type_rescore  (OCR 溯源查询重排)

纯函数测试，不依赖 PGVector / embedding / LLM。
背景: email 正文"特别提示"样板 chunk 含表名字面量，纯向量检索下压过 OCR 证据
chunk；修复 = chunk doc_type 标记 + smart_retrieve 侧过滤召回与重排。
"""
from __future__ import annotations

import os
import sys

from langchain_core.documents import Document

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import biz.rag_service as rag_service  # noqa: E402
import m1_rag_ingest as ing  # noqa: E402

RAGService = rag_service.RAGService
OCR_QUERY = "哪个样本通过OCR解析了交易对账单？"


def _doc(combined: float, doc_type: str | None = None, schema: str = "",
         content: str = "x") -> Document:
    metadata: dict = {"combined_score": combined}
    if doc_type is not None:
        metadata["doc_type"] = doc_type
    if schema:
        metadata["matched_schema"] = schema
    return Document(page_content=content, metadata=metadata)


# ---------------------------------------------------------------------------
# compute_doc_type
# ---------------------------------------------------------------------------

class TestComputeDocType:
    def test_ocr_table_prefix(self):
        assert ing.compute_doc_type("sample_x.pdf", "ocr_table_1", "") == "ocr_table"

    def test_parse_meta(self):
        assert ing.compute_doc_type("sample_x.pdf", "解析元数据", "") == "parse_meta"

    def test_reconcile(self):
        assert ing.compute_doc_type("sample_x.pdf", "勾稽校验", "") == "reconcile"

    def test_header_meta(self):
        assert ing.compute_doc_type("sample_x.pdf", "表头信息", "") == "header_meta"

    def test_email_notice_markers(self):
        doc = "样本: email_x.html\n表: html_table_8 (交易对账单)\n字段: 特别提示=5.本公司对本账单内容拥有最终解释权。"
        assert ing.compute_doc_type("email_x.html", "html_table_8", doc) == "email_notice"

    def test_email_statement_data_not_notice(self):
        doc = "样本: email_x.html\n表: html_table_1 (证券持仓明细)\n字段: 申请日期=2026-03-12, 产品名称=某某基金C"
        assert ing.compute_doc_type("email_x.html", "html_table_1", doc) == "statement"

    def test_non_email_with_marker_word_is_statement(self):
        # 非 email_ 样本即使正文含标记词也不判为 email_notice
        doc = "字段: 备注=最终解释权归甲方"
        assert ing.compute_doc_type("sample_x.pdf", "p0_table_1", doc) == "statement"

    def test_plain_table_is_statement(self):
        assert ing.compute_doc_type("sample_x.pdf", "p0_table_2", "") == "statement"


# ---------------------------------------------------------------------------
# _apply_doc_type_rescore
# ---------------------------------------------------------------------------

class TestApplyDocTypeRescore:
    def test_non_ocr_query_untouched(self):
        docs = [
            _doc(0.44, "email_notice"),
            _doc(0.42, "ocr_table", schema="交易对账单"),
            _doc(0.40),  # 无 doc_type
        ]
        RAGService._apply_doc_type_rescore("嘉兴民安有哪些证券持仓？", docs)
        assert docs[0].metadata["combined_score"] == 0.44
        assert docs[1].metadata["combined_score"] == 0.42
        assert docs[2].metadata["combined_score"] == 0.40
        assert all("doc_type_rescore_factor" not in d.metadata for d in docs)

    def test_ocr_query_penalizes_email_notice(self):
        doc = _doc(0.44, "email_notice")
        RAGService._apply_doc_type_rescore(OCR_QUERY, [doc])
        assert doc.metadata["combined_score"] < 0.44
        assert doc.metadata["doc_type_rescore_factor"] == rag_service._DOCTYPE_FACTOR_EMAIL_NOTICE

    def test_ocr_query_boosts_schema_matching_ocr_table(self):
        doc = _doc(0.42, "ocr_table", schema="交易对账单")
        RAGService._apply_doc_type_rescore(OCR_QUERY, [doc])
        assert doc.metadata["combined_score"] > 0.42
        assert doc.metadata["doc_type_rescore_factor"] == rag_service._DOCTYPE_FACTOR_OCR_TABLE_SCHEMA_MATCH

    def test_ocr_query_boosts_other_ocr_table_less(self):
        match = _doc(0.42, "ocr_table", schema="交易对账单")
        other = _doc(0.42, "ocr_table", schema="证券持仓明细")
        RAGService._apply_doc_type_rescore(OCR_QUERY, [match, other])
        assert other.metadata["combined_score"] > 0.42
        assert match.metadata["combined_score"] > other.metadata["combined_score"]
        assert other.metadata["doc_type_rescore_factor"] == rag_service._DOCTYPE_FACTOR_OCR_TABLE

    def test_ocr_query_leaves_untagged_and_statement_chunks(self):
        untagged = _doc(0.41)
        statement = _doc(0.41, "statement")
        RAGService._apply_doc_type_rescore(OCR_QUERY, [untagged, statement])
        assert untagged.metadata["combined_score"] == 0.41
        assert statement.metadata["combined_score"] == 0.41

    def test_trigger_is_case_insensitive(self):
        doc = _doc(0.42, "ocr_table", schema="交易对账单")
        RAGService._apply_doc_type_rescore("which sample used ocr?", [doc])
        assert doc.metadata["combined_score"] > 0.42

    def test_schema_match_beats_raw_notice_dominance(self):
        # 端到端排序语义: 样板 chunk 原始分更高, 重排后 OCR 证据 chunk 胜出
        notice = _doc(0.4385, "email_notice")
        target = _doc(0.4161, "ocr_table", schema="交易对账单")
        RAGService._apply_doc_type_rescore(OCR_QUERY, [notice, target])
        assert target.metadata["combined_score"] > notice.metadata["combined_score"]
