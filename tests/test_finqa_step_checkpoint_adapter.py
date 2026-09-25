"""Tests for the FinQA step-level checkpoint corpus builder.

Fixtures are synthetic and self-declared. The layers artifact fed to the adapter is produced
by the real split assigner, so the `layers_manifest_sha256` recomputation is exercised for
real rather than mocked. Two properties are enforced mechanically: the corpus publishes no
detection or localization metric (no scorer is pre-registered yet), and `arg_swap` is never
applied to a commutative op family (where it would be an undetectable non-fault).
"""
from __future__ import annotations

import hashlib
import json
import socket
import sys
from pathlib import Path

import pytest

from research import phase1a_split_assign as split
from research.finqa_step_checkpoint_adapter import (
    COMMUTATIVE_FAMILIES,
    MEASUREMENT_STATUS,
    AdapterError,
    apply_fault,
    build,
    install_network_guard,
    op_family,
    scale_res,
)
from research.phase1a_split_assign import SplitError

COMMIT = "0" * 40
FINQA_HEAD = "0f16e2867befa6840783e58be38c9efb9229d742"


def _step(op: str, arg1: str, arg2: str, res: str) -> dict:
    return {"op": op, "arg1": arg1, "arg2": arg2, "res": res}


# One filing per example so the split assigner spreads them over partitions.
EXAMPLES = {
    "train": [
        # multi-step, numeric res -> res_scale admissible
        ("AA/2009/page_1.pdf-1", [_step("divide1-1", "100", "100", "1%"),
                                   _step("divide1-2", "3.8", "#0", "380")]),
        # multi-step, non-numeric res, non-commutative op -> arg_swap admissible
        ("BB/2010/page_2.pdf-1", [_step("compare_larger-1", "5", "9", "yes"),
                                   _step("minus1-2", "#0", "1", "no")]),
        # multi-step, non-numeric res, commutative op only -> no admissible fault
        ("CC/2011/page_3.pdf-1", [_step("add1-1", "2", "3", "yes"),
                                   _step("multiply1-2", "#0", "4", "no")]),
        # single step -> counted, never injected
        ("DD/2012/page_4.pdf-1", [_step("divide1-1", "10", "2", "5")]),
        # three steps, numeric
        ("EE/2013/page_5.pdf-1", [_step("minus1-1", "10", "4", "6"),
                                  _step("add1-2", "#0", "2", "8"),
                                  _step("divide1-3", "#1", "2", "4")]),
    ],
    "dev": [
        ("FF/2014/page_6.pdf-1", [_step("average1-1", "4", "6", "5"),
                                  _step("sum2-2", "#0", "1", "6")]),
    ],
}


def _write_staging(root: Path) -> Path:
    for split_name, rows in EXAMPLES.items():
        path = root / "finqa" / (split_name + ".json")
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = [{"id": eid, "qa": {"steps": steps}} for eid, steps in rows]
        path.write_text(json.dumps(payload), encoding="utf-8", newline="\n")
    lines = []
    for path in sorted(root.rglob("*")):
        if path.is_file():
            rel = path.relative_to(root).as_posix()
            lines.append(hashlib.sha256(path.read_bytes()).hexdigest() + "  " + rel)
    manifest = root / "sha256_manifest.txt"
    manifest.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    return manifest


def _registry(tmp_path: Path) -> Path:
    path = tmp_path / "registry.json"
    path.write_text(json.dumps({"sources": [{
        "dataset_id": "finqa",
        "checked_default_head": FINQA_HEAD,
        "independence_cluster_namespace": "finqa_financial_reports",
        "role_fit": ["process_supervision", "external_evaluate", "proposal_train"],
    }]}), encoding="utf-8", newline="\n")
    return path


@pytest.fixture()
def env(tmp_path: Path) -> dict:
    root = tmp_path / "staging"
    manifest = _write_staging(root)
    entry = split.load_registry_entry(_registry(tmp_path), "finqa")
    artifact = split.compute(
        namespace="finqa",
        root=root,
        manifest=split.load_sha256_manifest(manifest),
        registry_entry=entry,
        m_universe=1,
        pilot_override_ruling="RULING-TEST",
    )
    layers = tmp_path / "layers.json"
    layers.write_text(json.dumps(artifact, sort_keys=True), encoding="utf-8", newline="\n")
    return {"root": root, "manifest": manifest, "layers": layers, "split": artifact, "tmp": tmp_path}


def _build(env: dict, seed: int = 42):
    return build(root=env["root"], manifest_path=env["manifest"], layers_path=env["layers"], seed=seed)


def _corpus(env: dict, seed: int = 42) -> list[dict]:
    text = _build(env, seed)[1]
    return [json.loads(line) for line in text.splitlines() if line.strip()]


def test_scale_res_is_exact_and_format_preserving() -> None:
    assert scale_res("1%") == "1.1%"
    assert scale_res("3.8") == "4.18"
    assert scale_res("100") == "110.0"
    assert scale_res("-2.5") == "-2.75"
    assert scale_res(".4") == "0.44"
    # Zero and non-numeric results are not faults under a multiplicative shift.
    assert scale_res("0") is None
    assert scale_res("yes") is None
    assert scale_res("") is None


def test_op_family_parsing() -> None:
    assert op_family("divide1-2") == "divide"
    assert op_family("minus2-1") == "minus"
    assert op_family("compare_larger-1") == "compare_larger"
    assert op_family("table_average-3") == "table_average"
    assert op_family("divide1") == "divide"


def test_corpus_counts_match_the_synthetic_universe(env: dict) -> None:
    summary, _ = _build(env)
    counts = summary["counts"]
    assert counts["layer_rows"] == 6
    assert counts["injected"] == 4          # AA, BB, EE, FF
    assert counts["single_step_excluded"] == 1   # DD
    assert counts["no_admissible_fault"] == 1    # CC (commutative ops, non-numeric res)
    assert counts["injected"] + counts["single_step_excluded"] + counts["no_admissible_fault"] == 6
    assert counts["corpus_records"] == 4
    strat = summary["stratifications"]
    assert sum(v["injected"] for v in strat["by_partition"].values()) == 4
    assert sum(strat["by_step_count"].values()) == 4
    assert sum(strat["by_fault_family"].values()) == 4
    assert set(strat["by_fault_family"]) <= {"res_scale", "arg_swap"}
    assert summary["measurement_status"] == MEASUREMENT_STATUS
    assert summary["fault_spec"]["scorer"] == "NOT_PREREGISTERED"


def test_no_detection_or_localization_metric_is_published(env: dict) -> None:
    summary, _ = _build(env)
    banned = ("detection", "localization", "accuracy", "f1", "tpr", "precision", "recall")

    def keys(node, prefix=""):
        if isinstance(node, dict):
            for k, v in node.items():
                yield prefix + str(k)
                yield from keys(v, prefix + str(k) + ".")

    for key in keys(summary):
        assert not any(word in key.lower() for word in banned), key


def test_every_mutant_differs_in_exactly_one_declared_field(env: dict) -> None:
    for record in _corpus(env):
        clean = record["steps_clean"]
        fault = record["fault"]
        mutant = apply_fault(clean, fault)
        assert mutant != clean
        changed = [i for i, (a, b) in enumerate(zip(clean, mutant)) if a != b]
        assert changed == [fault["step_index"]]
        if fault["family"] == "res_scale":
            assert clean[fault["step_index"]]["res"] == fault["before"]
            assert mutant[fault["step_index"]]["res"] == fault["after"]
        else:
            before, after = fault["before"], fault["after"]
            assert [before[1], before[0]] == after
            assert mutant[fault["step_index"]]["arg1"] == before[1]


def test_arg_swap_never_targets_a_commutative_family(env: dict) -> None:
    for record in _corpus(env):
        fault = record["fault"]
        if fault["family"] == "arg_swap":
            assert fault["op_family"] not in COMMUTATIVE_FAMILIES
        for family in record["op_families"]:
            assert family


def test_single_step_examples_are_never_injected(env: dict) -> None:
    records = _corpus(env)
    assert all(record["n_steps"] >= 2 for record in records)
    assert all(len(record["steps_clean"]) == record["n_steps"] for record in records)


def test_corpus_is_confined_to_assigned_layer_rows(env: dict) -> None:
    layers = env["split"]["layers"]
    assigned = {r["sample_id"] for part in ("train", "dev") for r in layers["proposal_train"][part]}
    assigned |= {r["sample_id"] for r in layers["gate_validation"]}
    assigned |= {r["sample_id"] for r in layers["sealed_test"]}
    records = _corpus(env)
    assert {r["sample_id"] for r in records} <= assigned
    assert len({r["sample_id"] for r in records}) == len(records)
    # clean and mutant share lineage root and role layer by construction
    for record in records:
        assert record["role_layer"] == (
            "proposal_train" if record["partition"].startswith("proposal_train.") else record["partition"]
        )


def test_layers_digest_tamper_fails_closed(env: dict) -> None:
    artifact = json.loads(env["layers"].read_text(encoding="utf-8"))
    # Any edit to `layers` must break the recomputed digest, even one that adds a row.
    artifact["layers"]["future_replay"] = [{"sample_id": "tampered"}]
    env["layers"].write_text(json.dumps(artifact, sort_keys=True), encoding="utf-8", newline="\n")
    with pytest.raises(AdapterError) as exc:
        _build(env)
    assert exc.value.code == "layers_manifest_sha256_mismatch"


def test_source_hash_tamper_fails_closed(env: dict) -> None:
    victim = env["root"] / "finqa" / "train.json"
    victim.write_text(victim.read_text(encoding="utf-8") + " ", encoding="utf-8", newline="\n")
    with pytest.raises(SplitError) as exc:
        _build(env)
    assert exc.value.code == "input_sha256_mismatch"


def test_layer_sample_missing_from_source_fails_closed(env: dict) -> None:
    path = env["root"] / "finqa" / "train.json"
    rows = json.loads(path.read_text(encoding="utf-8"))
    path.write_text(json.dumps(rows[1:]), encoding="utf-8", newline="\n")
    lines = []
    for p in sorted(env["root"].rglob("*")):
        if p.is_file():
            rel = p.relative_to(env["root"]).as_posix()
            lines.append(hashlib.sha256(p.read_bytes()).hexdigest() + "  " + rel)
    env["manifest"].write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    with pytest.raises(AdapterError) as exc:
        _build(env)
    assert exc.value.code == "layer_sample_not_in_source"


def test_build_is_deterministic_and_seed_is_an_input(env: dict) -> None:
    first, corpus_a = _build(env, seed=42)
    second, corpus_b = _build(env, seed=42)
    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)
    assert corpus_a == corpus_b
    other, corpus_c = _build(env, seed=43)
    assert other["counts"]["injected"] == first["counts"]["injected"]
    assert other["seed"] == 43
    assert len([json.loads(x) for x in corpus_c.splitlines() if x.strip()]) == 4


def test_cli_writes_byte_identical_artifacts(env: dict, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from research import finqa_step_checkpoint_adapter as runner

    outputs = []
    for name in ("a", "b"):
        out, corpus = tmp_path / (name + ".json"), tmp_path / (name + ".jsonl")
        monkeypatch.setattr(sys, "argv", [
            "runner",
            "--staging-root", str(env["root"]),
            "--sha256-manifest", str(env["manifest"]),
            "--layers", str(env["layers"]),
            "--seed", "42",
            "--commit", COMMIT,
            "--out", str(out),
            "--out-corpus", str(corpus),
        ])
        assert runner.main() == 0
        outputs.append((out.read_bytes(), corpus.read_bytes()))
    assert outputs[0] == outputs[1]
    payload = json.loads(outputs[0][0])
    assert payload["commit"] == COMMIT
    assert "executed_at" not in payload


def test_invalid_commit_fails_closed(env: dict, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from research import finqa_step_checkpoint_adapter as runner

    monkeypatch.setattr(sys, "argv", [
        "runner",
        "--staging-root", str(env["root"]),
        "--sha256-manifest", str(env["manifest"]),
        "--layers", str(env["layers"]),
        "--seed", "42",
        "--commit", "abc",
        "--out", str(tmp_path / "o.json"),
        "--out-corpus", str(tmp_path / "o.jsonl"),
    ])
    with pytest.raises(AdapterError) as exc:
        runner.main()
    assert exc.value.code == "invalid_adapter_commit"
    assert not (tmp_path / "o.json").exists()


def test_zero_connect_guard() -> None:
    original_connect = socket.socket.connect
    original_cc = socket.create_connection
    try:
        install_network_guard()
        with pytest.raises(AdapterError):
            socket.create_connection(("127.0.0.1", 8004), timeout=1)
    finally:
        socket.socket.connect = original_connect
        socket.create_connection = original_cc
