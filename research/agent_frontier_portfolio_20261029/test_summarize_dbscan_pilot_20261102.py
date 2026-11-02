import json

import pytest

from run_dbscan_reference_20261101 import sha
from summarize_dbscan_pilot_20261102 import episode


def test_summary_preserves_cache_and_rejects_tampered_raw(tmp_path):
    case = tmp_path / "case"
    (case / "work").mkdir(parents=True)
    raw = case / "raw.jsonl"
    raw.write_text(json.dumps({"type": "tool_use", "part": {"tool": "read", "state": {"input": {"filePath": "/root/prior_solution.py"}}}}) + "\n", encoding="utf-8")
    (case / "intervention.json").write_text("{}", encoding="utf-8")
    (case / "receipt.json").write_text(json.dumps({"raw_sha256": sha(raw), "model_http_requests": ["POST /v1/chat/completions"],
                                                     "step_finish_tokens": [{"input": 10, "output": 2, "total": 17,
                                                                             "cache": {"read": 5}}]}), encoding="utf-8")
    reference = tmp_path / "reference.csv"
    reference.write_text("F1,delta,min_samples,epsilon,shape_weight\n0.7,15,3,10,1.8\n", encoding="utf-8")
    result = episode(case, reference)
    assert result["post_requests"] == 1 and result["reported_total_tokens"] == 17
    assert result["reported_cached_read_tokens"] == 5 and result["reported_output_tokens"] == 2
    assert result["explicit_read_tool_calls_for_history"]["prior_solution.py"] == 1
    assert result["output_audit"]["classification"] == "NO_OUTPUT"
    raw.write_text("changed\n", encoding="utf-8")
    with pytest.raises(ValueError, match="raw Agent event hash differs"):
        episode(case, reference)
