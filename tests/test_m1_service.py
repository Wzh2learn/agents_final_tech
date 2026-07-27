"""Focused tests for the M1 deterministic extraction baseline."""

import sys
import os

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from biz.m1_service import (
    M1ExtractionRequest,
    M1ReviewRequest,
    M1Service,
    ExtractedRule,
    SAMPLE_DOCUMENT,
)


@pytest.fixture
def service():
    return M1Service()


class TestSampleDocument:
    def test_returns_text_and_name(self, service):
        sample = service.sample_document()
        assert "text" in sample
        assert "document_name" in sample
        assert len(sample["text"]) > 100

    def test_sample_contains_rules(self, service):
        sample = service.sample_document()
        assert "规则一" in sample["text"]
        assert "规则二" in sample["text"]
        assert "规则三" in sample["text"]


class TestExtraction:
    def test_basic_extraction(self, service):
        req = M1ExtractionRequest(text=SAMPLE_DOCUMENT)
        res = service.extract(req)
        assert res.status in ("success", "needs_review")
        assert res.run_mode == "local-rule-baseline"
        assert res.document_id.startswith("doc_")
        assert len(res.rules) == 3
        assert len(res.stages) == 5

    def test_preamble_not_emitted_as_rule(self, service):
        """The document title/preamble before the first rule heading must not become a rule."""
        req = M1ExtractionRequest(text=SAMPLE_DOCUMENT)
        res = service.extract(req)
        rule_names = [r.rule_name for r in res.rules]
        # Preamble contains "文件名称" - should not appear as a rule name
        for name in rule_names:
            assert "文件名称" not in name
            assert "金融业务规则样例" not in name

    def test_rule_schema_valid(self, service):
        req = M1ExtractionRequest(text=SAMPLE_DOCUMENT)
        res = service.extract(req)
        for rule in res.rules:
            assert rule.rule_id.startswith("M1-")
            assert len(rule.rule_id) == 11  # M1- + 8 hex
            assert 0 <= rule.confidence <= 1
            assert rule.source.page_no >= 1
            assert rule.source.paragraph_no >= 1
            assert len(rule.source.quote) >= 6

    def test_rule_fields_populated(self, service):
        req = M1ExtractionRequest(text=SAMPLE_DOCUMENT)
        res = service.extract(req)
        first = res.rules[0]
        assert "企业客户开户资料核验" in first.rule_name
        assert first.scenario
        assert first.trigger_condition
        assert first.action
        assert len(first.parameters) > 0

    def test_validation_summary(self, service):
        req = M1ExtractionRequest(text=SAMPLE_DOCUMENT)
        res = service.extract(req)
        assert res.validation.passed == len(res.rules)
        assert res.validation.failed == 0

    def test_m2_payload_structure(self, service):
        req = M1ExtractionRequest(text=SAMPLE_DOCUMENT)
        res = service.extract(req)
        payload = res.m2_payload
        assert payload.document_id == res.document_id
        assert len(payload.chunks) == len(res.rules)
        assert len(payload.records) == len(res.rules)
        for chunk in payload.chunks:
            assert "chunk_id" in chunk
            assert "text" in chunk
            assert "metadata" in chunk

    def test_metrics_present(self, service):
        req = M1ExtractionRequest(text=SAMPLE_DOCUMENT)
        res = service.extract(req)
        m = res.metrics
        assert m["rules"] == 3
        assert m["chars"] > 0
        assert m["paragraphs"] > 0
        assert 0 <= m["schema_pass_rate"] <= 1
        assert 0 <= m["source_coverage_rate"] <= 1

    def test_deterministic_ids(self, service):
        """Same input produces same document_id and rule_ids."""
        req = M1ExtractionRequest(text=SAMPLE_DOCUMENT)
        res1 = service.extract(req)
        res2 = service.extract(req)
        assert res1.document_id == res2.document_id
        assert [r.rule_id for r in res1.rules] == [r.rule_id for r in res2.rules]

    def test_short_text_rejected(self, service):
        with pytest.raises(Exception):
            M1ExtractionRequest(text="too short")

    def test_custom_document_name(self, service):
        req = M1ExtractionRequest(document_name="my-test.txt", text=SAMPLE_DOCUMENT)
        res = service.extract(req)
        assert res.document_name == "my-test.txt"

    def test_no_rules_text(self, service):
        """Text without rule headings produces zero rules, not a crash."""
        text = "This is a plain document.\n\nIt has no rule headings at all.\n\nJust paragraphs."
        req = M1ExtractionRequest(text=text)
        res = service.extract(req)
        assert len(res.rules) == 0
        assert res.validation.passed == 0


class TestReview:
    def test_approve_review(self, service):
        req = M1ExtractionRequest(text=SAMPLE_DOCUMENT)
        res = service.extract(req)
        rule = res.rules[0]
        review_req = M1ReviewRequest(rule=rule, decision="approved")
        review_res = service.review(review_req)
        assert review_res.status == "success"
        assert review_res.persisted is False
        assert review_res.rule.need_human_review is False

    def test_flag_review(self, service):
        req = M1ExtractionRequest(text=SAMPLE_DOCUMENT)
        res = service.extract(req)
        rule = res.rules[0]
        review_req = M1ReviewRequest(rule=rule, decision="needs_review", reviewer_note="unclear trigger")
        review_res = service.review(review_req)
        assert review_res.rule.need_human_review is True
        assert review_res.review["reviewer_note"] == "unclear trigger"


class TestEdgeCases:
    def test_single_rule(self, service):
        text = "规则一：测试规则\n触发条件：当某个业务事件发生且满足预设条件时触发\n执行动作：系统自动执行相应的业务操作并记录日志"
        req = M1ExtractionRequest(text=text)
        res = service.extract(req)
        assert len(res.rules) == 1
        assert "测试规则" in res.rules[0].rule_name

    def test_english_rule_heading(self, service):
        text = "Rule 1: Test Rule\nTrigger: when something happens\nAction: system does something"
        req = M1ExtractionRequest(text=text)
        res = service.extract(req)
        # Should recognize English rule heading
        assert len(res.rules) >= 1

    def test_stages_all_have_duration(self, service):
        req = M1ExtractionRequest(text=SAMPLE_DOCUMENT)
        res = service.extract(req)
        for stage in res.stages:
            assert stage.duration_ms >= 1
            assert stage.status in ("passed", "warning", "failed")
