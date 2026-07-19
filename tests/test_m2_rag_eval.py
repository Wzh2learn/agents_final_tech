from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts.run_m2_rag_eval import aggregate, load_approved_id_map, score_case, source_id, tool_payload, validate_cases


def dataset() -> dict:
    return json.loads(Path("tests/fixtures/m2_eval_cases_v1.json").read_text(encoding="utf-8"))


def test_m2_dataset_has_twenty_balanced_synthetic_cases():
    cases = validate_cases(dataset())
    assert len(cases) == 20
    assert {case["category"] for case in cases} == {"answerable", "unanswerable", "boundary", "conflicting"}
    assert all("expected_document_labels" in case for case in cases)


def test_source_id_matches_rag_service_schema():
    assert source_id({"source": "stable-source", "metadata": {"source": "other"}}) == "stable-source"
    assert source_id({"metadata": {"source": "stable-source"}}) == "stable-source"
    assert source_id({"content": "private evidence"}) == ""


def test_tool_payload_supports_structured_and_json_content():
    assert tool_payload(SimpleNamespace(structuredContent={"status": "success"})) == {"status": "success"}
    assert tool_payload(SimpleNamespace(structuredContent=None, content=[SimpleNamespace(text='{"status":"success"}')])) == {"status": "success"}


def test_approved_id_map_must_match_all_synthetic_labels(tmp_path):
    cases = validate_cases(dataset())
    path = tmp_path / "map.json"
    path.write_text('{"approved": true, "document_ids": {}}', encoding="utf-8")
    with pytest.raises(ValueError, match="exactly"):
        load_approved_id_map(path, cases)


def test_score_case_and_metrics():
    answerable = {"category": "answerable", "required_keywords": ["70"]}
    scored = score_case(answerable, {"DOC-1"}, ["DOC-1"], "上限为70%。[source: DOC-1]")
    assert scored == {"retrieval_hit": True, "source_hit": True, "refusal": False, "answer_adherent": True}

    unanswerable = {"category": "unanswerable", "required_keywords": []}
    refused = score_case(unanswerable, set(), [], "现有证据不足，无法回答。")
    metrics = aggregate([
        {"answerable": True, "latency_sec": 1.0, **scored},
        {"answerable": False, "latency_sec": 2.0, **refused},
    ])
    assert metrics["recall_at_5"] == 1.0
    assert metrics["source_hit_rate"] == 1.0
    assert metrics["refusal_rate"] == 1.0
    assert metrics["answer_adherence_rate"] == 1.0
