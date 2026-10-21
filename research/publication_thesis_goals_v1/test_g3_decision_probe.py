from g3_decision_probe import build_results, cases, evaluate, run_strategy


def test_behavior_only_accepts_the_natural_fallback_false_positive() -> None:
    case = next(item for item in cases() if item.case_id == "ntrip_base_fallback")
    behavior = run_strategy(case, "behavior_only")
    contract = run_strategy(case, "contract_only")
    greedy = run_strategy(case, "risk_greedy")
    assert behavior["decision"] == "ACCEPT"
    assert contract["decision"] == "REJECT"
    assert greedy["decision"] == "REJECT"


def test_contract_only_accepts_dead_target_call() -> None:
    case = next(item for item in cases() if item.case_id == "control_dead_target_call")
    contract = run_strategy(case, "contract_only")
    greedy = run_strategy(case, "risk_greedy")
    assert contract["decision"] == "ACCEPT"
    assert greedy["decision"] == "REJECT"


def test_risk_greedy_resolves_alias_without_simple_contract_false_reject() -> None:
    case = next(item for item in cases() if item.case_id == "control_valid_alias")
    simple = run_strategy(case, "contract_only")
    greedy = run_strategy(case, "risk_greedy")
    assert simple["decision"] == "REJECT"
    assert greedy["decision"] == "ACCEPT"


def test_environment_failure_is_deferred_before_candidate_judgment() -> None:
    case = next(item for item in cases() if item.case_id == "datetimerange_environment")
    result = run_strategy(case, "risk_greedy")
    assert result["decision"] == "DEFER_ENVIRONMENT"
    assert result["actions"] == ["preflight"]


def test_headroom_result_is_not_a_learning_claim() -> None:
    result = build_results()
    assert result["headroom"]["behavior_only_false_accepts"] >= 1
    assert result["headroom"]["contract_only_false_accepts"] >= 1
    assert result["headroom"]["greedy_same_decisions_as_full"] is True
    assert result["headroom"]["greedy_cost_delta_vs_full"] < 0
    assert "learned policy" in result["nonclaims"][2]
    assert evaluate("risk_greedy", cases())["false_accept"] == 0
