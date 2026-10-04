from __future__ import annotations

import json
from pathlib import Path

import pytest

from research.valentine_b0_b4_exploratory import ProbeError, _salted_assignment, build


def _write_fixture(root: Path) -> dict[str, Path]:
    labels = root / "labels.txt"
    samples = root / "samples.jsonl"
    canonical = root / "canonical.json"
    summary = root / "process_summary.json"
    events = root / "events.jsonl"
    config = root / "config.json"
    labels.write_text(
        "\n".join([
            "p1_src0 | map_to | t0",
            "p1_src1 | skip | null",
            "p2_src0 | hold | null",
            "p2_src1 | map_to | t1",
            "p3_src0 | skip | null",
            "p3_src1 | map_to | t0",
        ]) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    rows = []
    event_rows = []
    for pair, source, target, action, gold_target, confidence in [
        ("p1", "src0", "t0", "map_to", "t0", 0.9),
        ("p1", "src1", "t1", "skip", None, 0.2),
        ("p2", "src0", "t0", "hold", None, 0.7),
        ("p2", "src1", "t1", "map_to", "t1", 1.0),
        ("p3", "src0", "t0", "skip", None, None),
        ("p3", "src1", "t1", "map_to", "t0", 0.8),
    ]:
        sample_id = f"{pair}_{source}"
        rows.append({
            "sample_id": sample_id,
            "lineage_root_id": pair,
            "uid": f"uid-{pair}",
            "col": len(rows),
            "source_header": source,
            "target_headers": ["t0", "t1"],
        })
        event_rows.append({
            "sample_id": sample_id,
            "turn": 1,
            "event_index": 0,
            "event_id": f"e-{sample_id}",
            "event_kind": "record_candidate",
            "target_header": target,
            "confidence": confidence,
        })
    samples.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8", newline="\n")
    events.write_text("".join(json.dumps(row) + "\n" for row in event_rows), encoding="utf-8", newline="\n")
    canonical.write_text(json.dumps({"p1": ["t0", "t1"], "p2": ["t0", "t1"], "p3": ["t0", "t1"]}), encoding="utf-8", newline="\n")
    summary.write_text(json.dumps({"pairs": [{"pair_id": pair, "analysis_included": True} for pair in ("p1", "p2", "p3")]}), encoding="utf-8", newline="\n")
    config.write_text(json.dumps({
        "contract_version": "valentine-b0-b4-exploratory-v1",
        "lexical_threshold": 0.8,
        "confidence_policy": {"mapping": {"high": {}, "medium": {}, "low": {}, "missing": {}}},
        "classifier": {"epochs": 2, "learning_rate": 0.2, "l2": 0.01},
        "bootstrap": {"samples": 2, "seeds": [42], "cluster_unit": "table_pair_lineage_uid"},
        "salted_split": {"salt": "b0b4-explore-v1:layer", "modulus": 100, "train_buckets": [0, 60], "dev_buckets": [60, 80], "test_buckets": [80, 100]},
        "same_data_tuning_allowed": False,
        "paper_result": False,
    }), encoding="utf-8", newline="\n")
    return {
        "labels": labels,
        "samples": samples,
        "canonical": canonical,
        "summary": summary,
        "events": events,
        "config": config,
    }


def test_salted_assignment_is_deterministic() -> None:
    config = {"salted_split": {"salt": "b0b4-explore-v1:layer", "modulus": 100, "train_buckets": [0, 60], "dev_buckets": [60, 80], "test_buckets": [80, 100]}}
    first = _salted_assignment(["p1", "p2", "p3"], config)
    second = _salted_assignment(["p3", "p2", "p1"], config)
    assert first == second


def test_build_reports_exploratory_and_uses_corrected_labels(tmp_path: Path) -> None:
    fixture = _write_fixture(tmp_path)
    report = build(
        labels_path=fixture["labels"],
        samples_path=fixture["samples"],
        canonical_reference_path=fixture["canonical"],
        process_summary_path=fixture["summary"],
        process_events_path=fixture["events"],
        config_path=fixture["config"],
        out_dir=tmp_path / "out",
        analysis_variant="quarantine-primary",
        split="leave_one_pair_out",
    )
    assert report["paper_result"] is False
    assert report["data_go"] is False
    assert report["rq2_status"] == "NOT_IDENTIFIED"
    assert report["decision_status"] == "EXPLORATORY_ONLY_NOT_A_GO_NO_GO_GATE"
    assert report["prediction_count"] == 30


def test_same_data_tuning_is_rejected(tmp_path: Path) -> None:
    fixture = _write_fixture(tmp_path)
    config = json.loads(fixture["config"].read_text())
    config["same_data_tuning_allowed"] = True
    fixture["config"].write_text(json.dumps(config), encoding="utf-8", newline="\n")
    with pytest.raises(ProbeError) as exc:
        build(
            labels_path=fixture["labels"],
            samples_path=fixture["samples"],
            canonical_reference_path=fixture["canonical"],
            process_summary_path=fixture["summary"],
            process_events_path=fixture["events"],
            config_path=fixture["config"],
            out_dir=tmp_path / "out",
            analysis_variant="quarantine-primary",
            split="leave_one_pair_out",
        )
    assert exc.value.code == "same_data_tuning_not_prohibited"
