from __future__ import annotations

from g2_contract_verifier_v2 import (
    evaluate_case,
    load_ntrip_candidates,
    summarize,
    synthetic_controls,
)


def test_adversarial_fallback_is_rejected_and_cache_is_unresolved() -> None:
    rows = {row["id"]: evaluate_case(row) for row in synthetic_controls()}
    assert rows["partridge_real_parent"]["judgments"]["hybrid"] is False
    assert rows["partridge_real_gold"]["judgments"]["hybrid"] is True
    assert rows["partridge_call_then_hardcoded_utf8"]["judgments"]["runtime_consumption"] is False
    assert rows["partridge_call_then_hardcoded_utf8"]["judgments"]["hybrid"] is False
    assert rows["partridge_target_call_then_source_fallback"]["judgments"]["runtime_consumption"] is False
    assert rows["partridge_target_call_then_source_fallback"]["judgments"]["hybrid"] is False
    assert rows["partridge_cached_equivalent_unresolved"]["reference"] == "UNRESOLVED"
    assert rows["partridge_cached_equivalent_unresolved"]["runtime"]["target_result_consumed"] is None


def test_alias_and_dynamic_target_result_consumption_are_allowed() -> None:
    rows = {row["id"]: evaluate_case(row) for row in synthetic_controls()}
    assert rows["partridge_alias_valid"]["judgments"]["hybrid"] is True
    assert rows["partridge_dynamic_valid"]["judgments"]["hybrid"] is True


def test_summary_separates_unresolved_from_errors() -> None:
    rows = [evaluate_case(row) for row in load_ntrip_candidates() + synthetic_controls()]
    summary = summarize(rows)
    assert summary["basic_behavior"]["unresolved"] == 1
    assert summary["runtime_consumption"]["unresolved"] == 1
    assert summary["hybrid"]["unresolved"] == 1
    assert summary["hybrid"]["false_accept"] == 0
