"""Tests for the step-level checkpoint scorer, mapped to pre-registration clauses R2-R7.

Synthetic and self-declared. The percent-chain case reproduces the measured FinQA example that
is the sole documented basis for the R4 convention, so a change to that convention shows up here.
"""
from __future__ import annotations

import hashlib
import json
import socket
import sys
from decimal import Decimal
from pathlib import Path

import pytest

from research.finqa_step_checkpoint_adapter import op_family, scale_res
from research.finqa_step_checkpoint_scorer import (
    ScorerError,
    aggregate,
    compute,
    install_network_guard,
    READING_DIRECT,
    READING_SCALED,
    res_form,
    resolve_arg,
    run_steps,
    score_record,
    step_verdict,
    verify_bindings,
)
from research.phase1a_data_contract import _digest_object

COMMIT = "0" * 40


def _step(op: str, arg1: str, arg2: str, res: str) -> dict:
    return {"op": op, "arg1": arg1, "arg2": arg2, "res": res}


def _record(steps, fault, partition="proposal_train.train", sample_id="s1"):
    return {
        "sample_id": sample_id,
        "uid": "uid-" + sample_id,
        "lineage_root_id": "root",
        "independence_cluster": "cluster",
        "partition": partition,
        "role_layer": "proposal_train",
        "example_id": "EX/2009/page_1.pdf-1",
        "source_split": "train",
        "n_steps": len(steps),
        "op_families": [op_family(s["op"]) for s in steps],
        "steps_clean": steps,
        "fault": fault,
    }


def _res_fault(index, steps):
    return {"family": "res_scale", "step_index": index, "field": "res",
            "op_family": op_family(steps[index]["op"]), "before": steps[index]["res"],
            "after": scale_res(steps[index]["res"])}


def _swap_fault(index, steps):
    return {"family": "arg_swap", "step_index": index, "field": "arg1+arg2",
            "op_family": op_family(steps[index]["op"]),
            "before": [steps[index]["arg1"], steps[index]["arg2"]],
            "after": [steps[index]["arg2"], steps[index]["arg1"]]}


def test_resolve_arg_grammar_r2():
    steps = [_step("divide1-1", "100", "100", "1%"), _step("divide1-2", "3.8", "#0", "380")]
    cache = {}
    assert resolve_arg("100", steps, cache) == Decimal("100")
    assert resolve_arg(".4", steps, cache) == Decimal(".4")
    assert resolve_arg("12%", steps, cache) == Decimal("0.12")
    assert resolve_arg("const_100", steps, cache) == Decimal("100")
    assert resolve_arg("const_m1", steps, cache) == Decimal("-1")
    assert resolve_arg("#0", steps, cache) == Decimal("0.01")
    assert resolve_arg("#7", steps, cache) is None
    assert resolve_arg("none", steps, cache) is None
    assert resolve_arg("net sales", steps, cache) is None


def test_compute_semantics_r3():
    two, three = Decimal(2), Decimal(3)
    assert compute("add", two, three) == Decimal(5)
    assert compute("sum", two, three) == Decimal(5)
    assert compute("minus", two, three) == Decimal(-1)
    assert compute("multiply", two, three) == Decimal(6)
    assert compute("divide", Decimal(6), three) == Decimal(2)
    assert compute("average", two, three) == Decimal("2.5")
    assert compute("max", two, three) == Decimal(3)
    assert compute("min", two, three) == Decimal(2)
    assert compute("exp", two, three) == Decimal(8)
    assert compute("compare_larger", three, two) == "yes"
    assert compute("compare_larger", two, three) == "no"
    assert compute("divide", two, Decimal(0)) is None
    assert compute("compare_larger", two, two) is None
    assert compute("mystery_op", two, three) is None


@pytest.mark.parametrize("steps", [
    [_step("add1-1", "none", "3", "5")],
    [_step("divide1-1", "6", "0", "5")],
    [_step("compare_larger-1", "2", "2", "yes")],
    [_step("mystery1-1", "2", "3", "5")],
    [_step("add1-1", "2", "3", "")],
    [_step("add1-1", "2", "3", "( 0.60 )")],
    [_step("add1-1", "2", "3", "2.3:1")],
])
def test_unevaluable_is_explicit_and_never_guessed(steps):
    state, _detail = step_verdict(steps, 0, READING_DIRECT)
    assert state == "unevaluable"


def test_percent_chain_from_the_measured_example_r4():
    steps = [_step("divide1-1", "100", "100", "1%"), _step("divide1-2", "3.8", "#0", "380")]
    run = run_steps(steps, READING_DIRECT)
    assert run["flagged"] == [] and run["unevaluable"] == []
    assert [state for state, _ in run["verdicts"]] == ["match", "match"]


def test_clean_faithful_and_no_false_flag_r7():
    steps = [_step("divide1-1", "100", "100", "1"), _step("divide1-2", "3.8", "#0", "3.8")]
    row = score_record(_record(steps, _res_fault(1, steps)), READING_DIRECT)
    assert row["clean_faithful"] is True
    assert row["clean_flagged"] is False
    assert row["steps_unevaluable"] == 0


def test_const_m1_participates_r7():
    steps = [_step("multiply1-1", "5", "const_m1", "-5"), _step("add1-2", "#0", "2", "-3")]
    row = score_record(_record(steps, _res_fault(1, steps)), READING_DIRECT)
    assert row["clean_faithful"] is True


def test_res_scale_fault_is_detected_and_exactly_localized_r7():
    steps = [_step("divide1-1", "100", "100", "1"), _step("divide1-2", "3.8", "#0", "3.8")]
    row = score_record(_record(steps, _res_fault(1, steps)), READING_DIRECT)
    assert row["clean_faithful"] is True
    assert row["detected"] is True
    assert row["exact_localization"] is True
    assert row["inclusive_localization"] is True


def test_arg_swap_on_non_commutative_is_detected_r7():
    steps = [_step("minus1-1", "10", "4", "6"), _step("add1-2", "#0", "2", "8")]
    row = score_record(_record(steps, _swap_fault(0, steps)), READING_DIRECT)
    assert row["clean_faithful"] is True
    assert row["detected"] is True
    assert row["exact_localization"] is True


def test_arg_swap_on_commutative_would_be_undetectable():
    # Documents why the adapter forbids arg_swap on commutative families: the mutant is
    # arithmetically identical, so no detector can flag it and any rate would be inflated.
    steps = [_step("add1-1", "2", "3", "5"), _step("multiply1-2", "#0", "4", "20")]
    row = score_record(_record(steps, _swap_fault(0, steps)), READING_DIRECT)
    assert row["clean_faithful"] is True
    assert row["detected"] is False


def test_unfaithful_examples_leave_the_detection_denominator_r5():
    good = [_step("divide1-1", "100", "100", "1"), _step("divide1-2", "3.8", "#0", "3.8")]
    bad = [_step("add1-1", "none", "3", "5"), _step("add1-2", "1", "2", "3")]
    rows = [score_record(_record(good, _res_fault(1, good), sample_id="a"), READING_DIRECT),
            score_record(_record(bad, _res_fault(1, bad), sample_id="b"), READING_DIRECT)]
    out = aggregate(rows)
    assert out["totals"]["clean_faithful"] == 1
    assert out["totals"]["clean_unfaithful"] == 1
    assert out["metric_denominators"]["fault_detection_rate"] == 1
    assert out["metric_denominators"]["interpretation_fidelity"] == 2
    assert out["metrics"]["interpretation_fidelity"] == 0.5
    assert out["metrics"]["fault_detection_rate"] == 1.0
    assert out["metrics"]["clean_false_flag_rate"] == 0.0
    assert out["metrics"]["exact_localization_rate"] == 1.0
    assert out["metrics"]["inclusive_localization_rate"] == 1.0


def test_strata_dimensions_are_complete_r6():
    steps = [_step("minus1-1", "10", "4", "6"), _step("divide2-2", "#0", "2", "3")]
    out = aggregate([score_record(_record(steps, _swap_fault(0, steps)), READING_DIRECT)])
    assert set(out["step_strata"]) == {"op_family", "res_form", "variant"}
    assert set(out["example_strata"]) == {
        "fault_family", "injected_op_family", "injected_variant", "n_steps", "partition"}
    assert set(out["step_strata"]["op_family"]) == {"divide", "minus"}
    assert set(out["step_strata"]["variant"]) == {"1", "2"}
    assert out["step_strata"]["op_family"]["minus"]["steps"] == 1


def test_aggregate_is_deterministic():
    steps = [_step("divide1-1", "100", "100", "1"), _step("divide1-2", "3.8", "#0", "3.8")]
    rows = [score_record(_record(steps, _res_fault(1, steps)), READING_DIRECT)]
    assert json.dumps(aggregate(rows), sort_keys=True) == json.dumps(aggregate(rows), sort_keys=True)


def test_res_form_classification():
    assert res_form("3.8") == "num"
    assert res_form("1%") == "pct"
    assert res_form("yes") == "bool"
    assert res_form("( 0.60 )") == "other"
    assert res_form("") == "other"


def _bindings_fixture():
    layers = {"layers": {"proposal_train": {"train": [
        {"sample_id": "a", "uid": "u", "dataset_id": "finqa", "dataset_revision": "r",
         "source_split": "train", "independence_cluster": "c", "lineage_root_id": "root",
         "transformation_parent_id": None}], "dev": []},
        "gate_validation": [], "sealed_test": [], "future_replay": []}}
    digest = _digest_object(layers["layers"])
    raw = (json.dumps({"sample_id": "a"}) + "\n").encode("utf-8")
    summary = {"counts": {"corpus_sha256": hashlib.sha256(raw).hexdigest(), "corpus_records": 1},
               "inputs": {"layers_manifest_sha256": digest, "layers_m_universe": 1}}
    return raw, hashlib.sha256(raw).hexdigest(), summary, layers


def test_verify_bindings_rejects_each_tamper_r1():
    raw, sha, summary, layers = _bindings_fixture()
    assert verify_bindings(raw, sha, summary, layers) == {"a"}
    with pytest.raises(ScorerError) as exc:
        verify_bindings(raw, "0" * 64, summary, layers)
    assert exc.value.code == "corpus_sha256_mismatch"
    broken_summary = dict(summary, counts=dict(summary["counts"], corpus_sha256="f" * 64))
    with pytest.raises(ScorerError) as exc:
        verify_bindings(raw, sha, broken_summary, layers)
    assert exc.value.code == "summary_corpus_sha_mismatch"
    broken_layers = dict(layers, layers=dict(layers["layers"], future_replay=[{"sample_id": "x"}]))
    with pytest.raises(ScorerError) as exc:
        verify_bindings(raw, sha, summary, broken_layers)
    assert exc.value.code == "layers_manifest_sha256_mismatch"


def test_invalid_commit_fails_closed(tmp_path, monkeypatch):
    from research import finqa_step_checkpoint_scorer as runner

    monkeypatch.setattr(sys, "argv", [
        "runner", "--corpus", str(tmp_path / "c.jsonl"), "--corpus-sha256", "0" * 64,
        "--summary", str(tmp_path / "s.json"), "--layers", str(tmp_path / "l.json"),
        "--prereg", str(tmp_path / "p.md"),
        "--v1-results-doc", str(tmp_path / "v1.md"), "--v1-score", str(tmp_path / "v1.json"),
        "--commit", "abc", "--out", str(tmp_path / "o.json")])
    with pytest.raises(ScorerError) as exc:
        runner.main()
    assert exc.value.code == "invalid_scorer_commit"
    assert not (tmp_path / "o.json").exists()


def test_zero_connect_guard():
    original_connect = socket.socket.connect
    original_cc = socket.create_connection
    try:
        install_network_guard()
        with pytest.raises(ScorerError):
            socket.create_connection(("127.0.0.1", 8004), timeout=1)
    finally:
        socket.socket.connect = original_connect
        socket.create_connection = original_cc

def test_two_percent_readings_disagree_where_v1_measured_divergence():
    # divide(3.8, 100) = 0.038 with gold res "3.8%":
    #   mantissa_direct compares 0.038 against 3.8 -> mismatch (the reading v1 falsified)
    #   mantissa_scaled compares 3.8   against 3.8 -> match
    # If these two ever agree, the parallel computation required by V2-1 is not really happening.
    steps = [_step("divide1-1", "3.8", "100", "3.8%"), _step("add1-2", "1", "2", "3")]
    assert step_verdict(steps, 0, READING_DIRECT)[0] == "mismatch"
    assert step_verdict(steps, 0, READING_SCALED)[0] == "match"


def test_num_form_verdicts_are_reading_independent():
    steps = [_step("divide1-1", "100", "100", "1"), _step("divide1-2", "3.8", "#0", "3.8")]
    for index in range(2):
        assert step_verdict(steps, index, READING_DIRECT) == step_verdict(steps, index, READING_SCALED)


def test_unknown_percent_reading_is_rejected():
    steps = [_step("divide1-1", "3.8", "100", "3.8%")]
    with pytest.raises(ScorerError) as exc:
        step_verdict(steps, 0, "mantissa_whatever")
    assert exc.value.code == "unknown_percent_reading"


def test_root_cause_hits_cascade_where_exact_does_not():
    # res_scale on step 1 mutates a res that step 2 consumes through #1, so step 2 mismatches
    # too. exact therefore fails while root_cause (earliest flagged == injected) holds.
    steps = [_step("divide1-1", "100", "100", "1"),
             _step("divide1-2", "3.8", "#0", "3.8"),
             _step("multiply1-3", "#1", "2", "7.6")]
    row = score_record(_record(steps, _res_fault(1, steps)), READING_DIRECT)
    assert row["clean_faithful"] is True
    assert row["detected"] is True
    assert row["exact_localization"] is False
    assert row["inclusive_localization"] is True
    assert row["root_cause_localization"] is True


def test_all_three_localization_metrics_are_reported_together():
    steps = [_step("divide1-1", "100", "100", "1"), _step("divide1-2", "3.8", "#0", "3.8")]
    out = aggregate([score_record(_record(steps, _res_fault(1, steps)), READING_DIRECT)])
    for name in ("exact_localization_rate", "inclusive_localization_rate",
                 "root_cause_localization_rate"):
        assert name in out["metrics"], name
        assert name in out["metric_denominators"], name
    assert out["totals"]["root_cause_localization"] == 1
    assert out["metrics"]["root_cause_localization_rate"] == 1.0


def test_arg_swap_localizes_exactly_under_both_readings():
    steps = [_step("minus1-1", "10", "4", "6"), _step("add1-2", "#0", "2", "8")]
    for reading in (READING_DIRECT, READING_SCALED):
        row = score_record(_record(steps, _swap_fault(0, steps)), reading)
        assert row["clean_faithful"] is True, reading
        assert row["exact_localization"] is True, reading
        assert row["root_cause_localization"] is True, reading
