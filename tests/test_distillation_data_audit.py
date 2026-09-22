import copy
import json
from pathlib import Path
import socket

import pytest

from research import dpo_pairs_v0 as audit


ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def corpus(tmp_path):
    def write(name, value):
        (tmp_path / name).write_text(json.dumps(value), encoding="utf-8")

    event = {"uid": "fix", "col": 0, "round": 0, "injected": "alias",
             "type": "alias_variant", "target": "Revenue", "gain": 0.2,
             "collateral": 0.0, "accepted": True, "reason": "gated_pass"}
    write("vgmc_demo_checkpoint.json", {
        "arm_gated": {"sugg_log": [event], "rules": {"Revenue": ["alias"]}}})
    write("vgmc_demo_results.json", {"meta": {"prereg": {
        "fix_uids": ["fix"], "meas_uids": ["meas"]}},
        "arm_gated": {"rules": {"Revenue": ["alias"]}}})
    write("checkpoint_discrimination_tables_v2.json", {"tables": [
        {"uid": "fix", "n_cols": 1, "injections": [
            {"col": 0, "injected": "alias", "canonical": "Revenue", "type": "alias_variant"}]},
        {"uid": "meas", "n_cols": 1, "injections": []}]})
    write("dpo_pairs_v0.json", {"meta": {"sources": ["demo (vgmc_demo_checkpoint.json)"]},
        "pairs": [{"uid": "fix", "col": 0, "chosen": {"action": "skip"},
                   "rejected": {"action": "map_to", "target": "Revenue"},
                   "sources": ["demo/gated/r0"], "types": ["A", "C"], "gate_fooled": True}]})
    return tmp_path


def test_raw_snapshot_recount_and_no_training_release(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("legacy corpus/model loader must not run")
    monkeypatch.setattr(audit, "load_module", forbidden)
    result = audit.audit_data(ROOT / "logs/graph/eval")
    assert result["counts"]["checkpoint_files"] == 16
    assert result["counts"]["raw_gated_events"] == 625
    assert result["counts"]["scored_events"] == 494
    assert result["counts"]["scored_uids"] == 48
    assert result["counts"]["scored_uid_cols"] == 94
    assert result["counts"]["scored_uid_col_targets"] == 139
    assert result["counts"]["accepted"] == 292
    assert result["counts"]["rejected"] == 202
    assert result["counts"]["conflicting_groups"] == 16
    assert result["counts"]["multi_target_columns"] == 41
    assert result["counts"]["excluded_reasons"] == {"no_map": 126, "target_not_canonical": 5}
    assert result["counts"]["raw_actions"] == {"map_to": 499, "parse_fail": 5, "skip": 121}
    assert result["families"]["ocr_similar"] == {"events": 0, "scored": 0, "uids": 0}
    assert result["counts"]["reference_matches"] == 368
    assert result["counts"]["accepted_reference_mismatches"] == 17
    assert result["counts"]["exact_duplicate_observations"] == 17
    assert result["dpo"]["pairs"] == 60
    assert result["dpo"]["uids"] == 36
    assert result["dpo"]["directions"] == {"skip>map_to": 60}
    assert result["dpo"]["by_type"] == {"A": 50, "C": 51}
    assert result["dpo"]["gate_fooled"] == 9
    assert result["hashes"]["checkpoint_manifest"] == "9b4bc0e63b4a5964d66648337e7d0f23d40d5fa2f4df597d8b60eae4f6cbd6c6"
    assert result["hashes"]["dpo"] == "20b09efd154862580cdaf1c9ef55311ec9fab4c8bb0373d0438965e0a116ae37"
    assert result["meta"]["endpoint_calls"] == result["meta"]["socket_attempts"] == 0
    assert not any(view["training_export"] for view in result["views"].values())
    assert result["manifest"]["sealed_test"]["uids"] == []
    assert result["manifest"]["future_replay"]["uids"] == []


def test_deterministic_audit_and_separation_of_gate_and_truth(corpus):
    first = audit.audit_data(corpus)
    assert first == audit.audit_data(corpus)
    assert first["events"][0]["recorded_target_match"] is True
    assert first["events"][0]["independent_correctness"] is None
    assert first["events"][0]["action_inferred"] is True
    assert first["dpo"]["rejected_reference_matches"] == 1
    assert first["manifest"]["proposal_train"]["status"] == "HISTORICAL_ONLY"
    assert all(first["views"][name]["training_export"] == [] for name in first["views"])


def test_conflicts_are_retained_not_majority_voted(corpus):
    path = corpus / "vgmc_demo_checkpoint.json"
    data = json.loads(path.read_text())
    rejected = copy.deepcopy(data["arm_gated"]["sugg_log"][0])
    rejected.update(accepted=False, reason="gated_fail", gain=0.0, round=1)
    data["arm_gated"]["sugg_log"].extend([rejected, copy.deepcopy(rejected)])
    path.write_text(json.dumps(data))
    result = audit.audit_data(corpus)
    assert result["counts"]["conflicting_groups"] == 1
    assert len(result["conflicts"][0]["event_ids"]) == 3
    assert result["counts"]["exact_duplicate_observations"] == 1
    assert result["conflicts"][0]["resolution"] == "QUARANTINED"


def test_parse_failure_and_missing_reference_are_not_positive_labels(corpus):
    path = corpus / "vgmc_demo_checkpoint.json"
    data = json.loads(path.read_text())
    data["arm_gated"]["sugg_log"].append({"uid": "fix", "col": 1, "round": 0,
        "injected": "unknown", "type": None, "action": "parse_fail",
        "accepted": False, "reason": "no_map"})
    path.write_text(json.dumps(data))
    result = audit.audit_data(corpus)
    event = result["events"][-1]
    assert event["recorded_target_match"] is None
    assert event["independent_correctness"] is None
    assert event["action"] == "parse_fail"


@pytest.mark.parametrize("change", ["split_overlap", "missing_result", "wrong_header", "wrong_final_rules", "orphan_pair"])
def test_missing_or_conflicting_provenance_is_reported(corpus, change):
    if change == "missing_result":
        (corpus / "vgmc_demo_results.json").unlink()
    else:
        name = "dpo_pairs_v0.json" if change == "orphan_pair" else (
            "vgmc_demo_results.json" if change == "split_overlap" else "vgmc_demo_checkpoint.json")
        path = corpus / name
        data = json.loads(path.read_text())
        if change == "split_overlap":
            data["meta"]["prereg"]["meas_uids"] = ["fix"]
        elif change == "wrong_header":
            data["arm_gated"]["sugg_log"][0]["injected"] = "different"
        elif change == "wrong_final_rules":
            data["arm_gated"]["rules"] = {}
        else:
            data["pairs"][0]["sources"] = ["demo/gated/r99"]
        path.write_text(json.dumps(data))
    result = audit.audit_data(corpus)
    assert result["issues"]
    assert all(view["verdict"] != "DATA_GO" for view in result["views"].values())
    if change == "orphan_pair":
        assert result["views"]["dpo"]["verdict"] == "DATA_NO_GO"


def test_bad_inputs_fail_instead_of_being_silently_skipped(corpus):
    (corpus / "vgmc_demo_checkpoint.json").write_text('{"arm_gated": NaN}')
    with pytest.raises(ValueError):
        audit.audit_data(corpus)


def test_cli_is_explicit_and_never_overwrites(corpus, monkeypatch):
    import sys
    output = corpus.parent / (corpus.name + "-audit.json")
    monkeypatch.setattr(sys, "argv", ["dpo_pairs_v0.py", "--audit", "--eval-dir", str(corpus),
                                      "--output", str(output)])
    assert audit.audit_cli() == 0
    saved = output.read_bytes()
    with pytest.raises(SystemExit):
        audit.audit_cli()
    assert output.read_bytes() == saved
    for path in (corpus / "new.json", ROOT / "paper/forbidden-audit.json"):
        monkeypatch.setattr(sys, "argv", ["dpo_pairs_v0.py", "--audit", "--eval-dir", str(corpus),
                                          "--output", str(path)])
        with pytest.raises(SystemExit):
            audit.audit_cli()
        assert not path.exists()


def test_rule_context_is_part_of_deduplication(corpus):
    path = corpus / "vgmc_demo_checkpoint.json"
    data = json.loads(path.read_text())
    data["arm_gated"]["sugg_log"].append(copy.deepcopy(data["arm_gated"]["sugg_log"][0]))
    path.write_text(json.dumps(data))
    result = audit.audit_data(corpus)
    assert result["counts"]["exact_duplicate_observations"] == 0
    assert len({e["rule_state_before_sha256"] for e in result["events"]}) == 2


@pytest.mark.parametrize("change", ["no_sources", "empty_target", "same_action", "boolean_score"])
def test_invalid_training_candidates_never_become_exportable(corpus, change):
    path = corpus / ("vgmc_demo_checkpoint.json" if change == "boolean_score" else "dpo_pairs_v0.json")
    data = json.loads(path.read_text())
    if change == "boolean_score":
        data["arm_gated"]["sugg_log"][0]["gain"] = True
    elif change == "no_sources":
        data["pairs"][0]["sources"] = []
    elif change == "empty_target":
        data["pairs"][0]["rejected"]["target"] = ""
    else:
        data["pairs"][0]["rejected"] = data["pairs"][0]["chosen"]
    path.write_text(json.dumps(data))
    if change == "no_sources":
        assert audit.audit_data(corpus)["views"]["dpo"]["verdict"] == "DATA_NO_GO"
    else:
        with pytest.raises(ValueError):
            audit.audit_data(corpus)


def test_offline_guard_blocks_and_restores_sockets():
    original = socket.create_connection
    with audit.offline_guard() as attempts:
        with pytest.raises(RuntimeError, match="network"):
            socket.create_connection(("invalid.example", 443))
        assert attempts == [1]
    assert socket.create_connection is original
