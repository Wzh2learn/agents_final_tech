from __future__ import annotations

from g2_contract_verifier import CONTROLS, evaluate_case, load_natural_candidates, summarize


def test_natural_candidates_keep_behavior_and_contract_boundary() -> None:
    rows = [evaluate_case(case) for case in load_natural_candidates()]
    by_id = {row["id"]: row for row in rows}
    assert by_id["natural_base"]["reference"] == "INVALID"
    assert by_id["natural_base"]["judgments"]["basic_behavior"] is True
    assert by_id["natural_base"]["judgments"]["hybrid"] is False
    assert by_id["natural_prose_change_facts"]["judgments"]["hybrid"] is True
    assert by_id["natural_structured_change_facts"]["judgments"]["hybrid"] is True


def test_controls_separate_alias_dynamic_adapter_and_bad_consumption() -> None:
    rows = {row["id"]: evaluate_case(row) for row in CONTROLS}
    assert rows["valid_alias"]["judgments"]["hybrid"] is True
    assert rows["valid_wrapper"]["judgments"]["hybrid"] is True
    assert rows["valid_dynamic_import"]["judgments"]["hybrid"] is True
    assert rows["valid_equivalent_adapter"]["judgments"]["hybrid"] is True
    assert rows["invalid_dead_target_call"]["judgments"]["hybrid"] is False
    assert rows["invalid_unused_target_result"]["judgments"]["hybrid"] is False
    assert rows["invalid_swallowed_old_fallback"]["judgments"]["hybrid"] is False


def test_summary_exposes_false_accepts_of_basic_and_static_views() -> None:
    rows = [evaluate_case(case) for case in load_natural_candidates() + CONTROLS]
    summary = summarize(rows)
    assert summary["basic_behavior"]["false_accept"] == 4
    assert summary["static_contract"]["false_accept"] == 2
    assert summary["runtime_consumption"]["false_accept"] == 0
    assert summary["hybrid"] == {
        "correct": 10,
        "false_accept": 0,
        "false_reject": 0,
        "n": 10,
    }
