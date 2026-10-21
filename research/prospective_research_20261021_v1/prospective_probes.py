"""Executable DEV_ONLY qualification fixtures. No network, model calls, or production I/O."""

import argparse
from collections import deque
from copy import deepcopy
import hashlib
import json
from pathlib import Path


ORDER = ["gross", "converted", "report", "side"]
DEPS = {
    "gross": ["a", "b"],
    "converted": ["gross", "rate", "use_rate"],
    "report": ["converted"],
    "side": ["b"],
}
OWNERS = {"a": "A", "b": "B", "gross": "B", "converted": "C", "report": "D", "side": "A"}


def evaluate_node(name, values):
    if name == "gross":
        return values["a"] + values["b"]
    if name == "converted":
        return values["gross"] * values["rate"] if values["use_rate"] else values["gross"]
    if name == "report":
        return values["converted"]
    if name == "side":
        return values["b"] * 2
    raise ValueError(name)


def execute(inputs):
    values = dict(inputs)
    for node in ORDER:
        values[node] = evaluate_node(node, values)
    return values


def reachable(changed, dependencies):
    affected, queue = set(), deque(changed)
    while queue:
        parent = queue.popleft()
        for node, parents in dependencies.items():
            if parent in parents and node not in affected:
                affected.add(node)
                queue.append(node)
    return affected


def repair(cache, updates, dependencies):
    result = {**cache, **updates}
    dirty = reachable(updates, dependencies)
    for node in ORDER:
        if node in dirty:
            result[node] = evaluate_node(node, result)
    return result, dirty


def guard(context):
    expected = {"currency": "USD", "period": "quarter", "schema": "v2"}
    if any(key in context and context[key] != value for key, value in expected.items()):
        return "invalid"
    if any(key not in context for key in expected):
        return "unknown"
    return "valid"


def actor_view(record):
    return {key: deepcopy(record[key]) for key in ("case_id", "change_notice", "cached_outputs", "available_tools")}


def main():
    checks = []

    def passed(name, facts):
        checks.append({"name": name, "status": "PASS", "observation": facts})

    base = {"a": 2, "b": 3, "rate": 2, "use_rate": True}
    cache = execute(base)
    edges = reachable({"a"}, DEPS)
    membership = {node for node in ORDER if OWNERS[node] == OWNERS["a"]}
    assert edges == {"gross", "converted", "report"}
    assert membership == {"side"}
    passed("resource_membership_is_not_edge_propagation", {"resource_selected": sorted(membership), "edge_reachable": sorted(edges)})

    repaired, dirty = repair(cache, {"a": 5}, DEPS)
    assert repaired == execute({**base, "a": 5})
    assert len(dirty) == 3 < len(ORDER)
    passed("local_repair_equals_fresh_execution", {"recomputed_nodes": sorted(dirty), "fixture_full_compute_nodes": len(ORDER)})

    broken = deepcopy(DEPS)
    broken["converted"] = ["rate", "use_rate"]
    wrong, _ = repair(cache, {"a": 5}, broken)
    assert wrong["report"] != repaired["report"]
    passed("missing_edge_negative_control_detects_stale_output", {"missing_edge_result": wrong["report"], "fresh_execution_result": repaired["report"]})

    inactive = {**base, "use_rate": False}
    inactive_cache = execute(inactive)
    inactive_after, inactive_dirty = repair(inactive_cache, {"rate": 7}, DEPS)
    assert inactive_after == execute({**inactive, "rate": 7})
    actual_output_changes = {node for node in ORDER if inactive_after[node] != inactive_cache[node]}
    assert inactive_dirty == {"converted", "report"} and actual_output_changes == set()
    passed("potential_dependency_is_not_value_change", {"potentially_dirty": sorted(inactive_dirty), "changed_computed_values": sorted(actual_output_changes)})

    cancellation_after = execute({**base, "a": 3, "b": 2})
    assert cancellation_after["report"] == cache["report"]
    assert {"a", "b"} != set()
    passed("output_invariance_does_not_prove_source_invariance", {"output_before": cache["report"], "output_after": cancellation_after["report"], "changed_source_fields": ["a", "b"], "note": "Value correctness and provenance validity require separate contracts."})

    assert guard({"currency": "USD", "period": "quarter", "schema": "v2"}) == "valid"
    assert guard({"currency": "USD", "schema": "v2"}) == "unknown"
    assert guard({"currency": "EUR"}) == "invalid"
    assert guard({"currency": "USD", "period": "annual", "schema": "v2"}) == "invalid"
    passed("three_state_guard_does_not_treat_missing_as_valid", {"all_matched": "valid", "missing_period": "unknown", "known_contradiction": "invalid"})

    context = {"schema": "v2"}
    after_one = {**context, "currency": "USD"}
    after_two = {**after_one, "period": "quarter"}
    assert guard(context) == guard(after_one) == "unknown" and guard(after_two) == "valid"
    passed("complementary_checks_can_be_expressed", {"zero_checks": "unknown", "one_check": "unknown", "two_checks": "valid", "warning": "Constructed fixture only; not evidence of natural query complementarity or superiority over greedy."})

    old_world, new_world = {**base, "rate": 2}, {**base, "rate": 3}
    visible = {"case_id": "fixture_1", "change_notice": "conversion configuration changed", "cached_outputs": {"report": cache["report"]}, "available_tools": ["inspect_config", "run_target_test"]}
    one = {**visible, "hidden_world": old_world, "labels": {"report": execute(old_world)["report"]}}
    two = {**visible, "hidden_world": new_world, "labels": {"report": execute(new_world)["report"]}}
    assert actor_view(one) == actor_view(two)
    assert one["labels"] != two["labels"]
    assert execute(one["hidden_world"])["report"] != execute(two["hidden_world"])["report"]
    passed("identical_visible_inputs_can_require_a_query", {"actor_view_equal": True, "independent_execution_targets_equal": False, "warning": "This proves a property of the authored fixture, not of MA-CERD or real-world tasks."})

    mutated = deepcopy(one)
    mutated["labels"] = {"report": -999}
    mutated["gold_trace"] = ["private_expected_action"]
    assert actor_view(one) == actor_view(mutated)
    assert all(key not in actor_view(mutated) for key in ("labels", "gold_trace", "hidden_world"))
    passed("actor_serialization_noninterference", {"label_mutation_changes_actor_payload": False, "hidden_trace_exposed": False})

    new_attempts, new_tokens = 2048, 10000000
    assert 747 + new_attempts == 2795
    assert 1564176 + new_tokens == 11564176
    passed("proposed_budget_is_an_increment_not_old_balance", {"new_attempt_cap": new_attempts, "new_token_cap": new_tokens, "historical_747_plus_new_attempt_cap": 2795, "historical_tokens_plus_new_cap": 11564176, "execution_authorized_by_script": False})

    result = {
        "schema": "prospective_qualification_fixtures_v1",
        "evidence_identity": "DEV_ONLY_AUTHORED_MECHANISM_FIXTURES",
        "date": "2026-10-21",
        "status": "PASS",
        "checks": checks,
        "check_groups": len(checks),
        "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "model_calls": 0,
        "network_calls": 0,
        "nonclaims": ["No model or learned guard was evaluated.", "No external benchmark or natural task distribution was validated.", "Hand-authored graph and guard are fixtures, not novel methods.", "Fixture repair savings are not scientific performance evidence.", "No governance merge, cleanup, model service change or budget activation occurred."],
    }
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    text = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.write_text(text, encoding="utf-8")
        print(json.dumps({"status": result["status"], "check_groups": len(checks), "output": str(args.output), "model_calls": 0}))
    else:
        print(text, end="")


if __name__ == "__main__":
    main()
