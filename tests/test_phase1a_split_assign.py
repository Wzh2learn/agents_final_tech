"""Tests for the phase1a deterministic split assigner.

Fixtures are synthetic and self-declared. Two properties are enforced mechanically
rather than promised in prose:

* label-blindness -- `ground_truth.json` and `target_table.csv` exist on disk but are
  deliberately absent from the sha256 manifest, so reading one would fail closed with
  `input_not_in_sha256_manifest`;
* governance -- a namespace whose registry `role_fit` lacks gate/sealed cannot emit
  those partitions without an explicit ruling id.
"""
from __future__ import annotations

import hashlib
import json
import socket
import sys
from pathlib import Path

import pytest

from research import phase1a_split_assign as runner
from research.phase1a_data_contract import _digest_object, lineage_uid
from research.phase1a_split_assign import SplitError, compute, install_network_guard, load_registry_entry

COMMIT = "0" * 40
FINQA_HEAD = "0f16e2867befa6840783e58be38c9efb9229d742"
VALENTINE_HEAD = "5d5163f04da304985bd51a476ccf7653de3979c3"


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8", newline="\n")


def _registry(tmp_path: Path, valentine_role_fit: list[str] | None = None) -> Path:
    path = tmp_path / "registry.json"
    _write_json(
        path,
        {
            "sources": [
                {
                    "dataset_id": "finqa",
                    "checked_default_head": FINQA_HEAD,
                    "independence_cluster_namespace": "finqa_financial_reports",
                    "role_fit": ["process_supervision", "external_evaluate", "proposal_train"],
                },
                {
                    "dataset_id": "valentine_nyc",
                    "checked_default_head": VALENTINE_HEAD,
                    "independence_cluster_namespace": "valentine_nyc_schema_matching",
                    "role_fit": valentine_role_fit
                    or ["schema_action_pilot", "simple_baselines", "proposal_train"],
                },
            ]
        },
    )
    return path


def _make_valentine(root: Path, pairs: int, cols: int) -> None:
    for i in range(pairs):
        pair = f"PAIR_{i:02d}"
        d = root / "valentine" / "experiments" / "data" / pair
        d.mkdir(parents=True, exist_ok=True)
        header = ",".join(f"col_{j}" for j in range(cols))
        (d / "source_table.csv").write_text(
            header + "\n" + ",".join(["v"] * cols) + "\n", encoding="utf-8", newline="\n"
        )
        # Present on disk, absent from the manifest: touching either must fail closed.
        (d / "target_table.csv").write_text(header + "\n", encoding="utf-8", newline="\n")
        _write_json(d / "ground_truth.json", {"matches": [{"source_column": "col_0"}]})


def _make_finqa(root: Path, train_ids: list[str], dev_ids: list[str]) -> None:
    _write_json(
        root / "finqa" / "train.json", [{"id": i, "table": [["h"], ["1"]]} for i in train_ids]
    )
    _write_json(root / "finqa" / "dev.json", [{"id": i, "table": [["h"], ["1"]]} for i in dev_ids])


def _manifest(root: Path, exclude_suffixes: tuple[str, ...] = ()) -> Path:
    lines = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.name == "sha256_manifest.txt":
            continue
        rel = path.relative_to(root).as_posix()
        if rel.endswith(exclude_suffixes):
            continue
        lines.append(hashlib.sha256(path.read_bytes()).hexdigest() + "  " + rel)
    out = root / "sha256_manifest.txt"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    return out


@pytest.fixture()
def valentine_env(tmp_path: Path) -> dict[str, object]:
    root = tmp_path / "staging"
    _make_valentine(root, pairs=40, cols=3)
    return {
        "root": root,
        "manifest": _manifest(root, ("ground_truth.json", "target_table.csv")),
        "registry": _registry(tmp_path),
    }


@pytest.fixture()
def finqa_env(tmp_path: Path) -> dict[str, object]:
    root = tmp_path / "staging"
    _make_finqa(
        root,
        ["AAA/2009/page_1.pdf-1", "AAA/2009/page_1.pdf-2", "AAA/2009/page_2.pdf-1", "BBB/2010/page_5.pdf-1"],
        ["AAA/2009/page_3.pdf-1", "CCC/2011/page_9.pdf-1"],
    )
    return {"root": root, "manifest": _manifest(root), "registry": _registry(tmp_path)}


def _compute(env: dict[str, object], namespace: str, m_universe: int = 1, ruling: str | None = None) -> dict:
    entry = load_registry_entry(Path(str(env["registry"])), namespace)
    return compute(
        namespace=namespace,
        root=Path(str(env["root"])),
        manifest=runner.load_sha256_manifest(Path(str(env["manifest"]))),
        registry_entry=entry,
        m_universe=m_universe,
        pilot_override_ruling=ruling,
    )


def _flat(artifact: dict) -> list[tuple[str, dict]]:
    layers = artifact["layers"]
    out = []
    for name, rows in (("proposal_train.train", layers["proposal_train"]["train"]),
                       ("proposal_train.dev", layers["proposal_train"]["dev"]),
                       ("gate_validation", layers["gate_validation"]),
                       ("sealed_test", layers["sealed_test"]),
                       ("future_replay", layers["future_replay"])):
        out.extend((name, row) for row in rows)
    return out


def _argv(env: dict[str, object], namespace: str, out: Path, m_universe: int = 1,
          commit: str = COMMIT, ruling: str | None = None) -> list[str]:
    argv = [
        "runner",
        "--namespace", namespace,
        "--staging-root", str(env["root"]),
        "--sha256-manifest", str(env["manifest"]),
        "--registry", str(env["registry"]),
        "--m-universe", str(m_universe),
        "--commit", commit,
        "--out", str(out),
    ]
    if ruling is not None:
        argv += ["--pilot-override-ruling", ruling]
    return argv


def test_pilot_namespace_withholds_gate_and_sealed(valentine_env: dict) -> None:
    art = _compute(valentine_env, "valentine_nyc")
    assert art["status"] == "INCOMPLETE"
    assert any(r.startswith("LAYER_CAPACITY_BLOCKED_PILOT_ONLY") for r in art["reasons"])
    assert art["layers"]["gate_validation"] == []
    assert art["layers"]["sealed_test"] == []
    assert art["layers"]["proposal_train"]["train"]
    assert art["layers"]["proposal_train"]["dev"]
    intended = {p["intended_partition"] for p in art["pending_ruling_rows"]}
    assert intended <= {"gate_validation", "sealed_test"}
    assert art["pending_ruling_rows"]
    # Nothing is silently dropped: assigned + withheld == full universe.
    assert len(_flat(art)) + len(art["pending_ruling_rows"]) == art["counts"]["units_total"] == 120
    assert art["counts"]["clusters_total"] == 40


def test_override_ruling_fills_all_four_layers(valentine_env: dict) -> None:
    art = _compute(valentine_env, "valentine_nyc", ruling="RULING-TEST-1")
    assert art["reasons"] == []
    assert art["status"] == "READY"
    assert art["pending_ruling_rows"] == []
    assert art["pilot_override_ruling"] == "RULING-TEST-1"
    counts = art["counts"]["partitions"]
    for partition in ("proposal_train.train", "proposal_train.dev", "gate_validation", "sealed_test"):
        assert counts[partition]["samples"] > 0, partition
    assert len(_flat(art)) == 120


def test_rows_satisfy_contract_invariants(valentine_env: dict) -> None:
    art = _compute(valentine_env, "valentine_nyc", ruling="RULING-TEST-1")
    rows = [row for _, row in _flat(art)]
    assert rows
    for row in rows:
        assert set(row) == runner.MANIFEST_ROW_FIELDS
        assert row["uid"] == lineage_uid(row["dataset_id"], row["dataset_revision"], row["lineage_root_id"])
        assert row["independence_cluster"].startswith("valentine_nyc_schema_matching:PAIR_")
        assert row["transformation_parent_id"] is None
        assert row["dataset_revision"] == VALENTINE_HEAD
    assert len({row["sample_id"] for row in rows}) == len(rows)


def test_ground_truth_and_target_table_are_never_read(valentine_env: dict) -> None:
    art = _compute(valentine_env, "valentine_nyc")
    read = sorted(art["input_sha256"])
    assert len(read) == 40
    assert all(rel.endswith("/source_table.csv") for rel in read)
    assert not any("ground_truth" in rel or "target_table" in rel for rel in read)


def test_layers_manifest_digest_matches_contract_caliber(valentine_env: dict) -> None:
    art = _compute(valentine_env, "valentine_nyc", ruling="RULING-TEST-1")
    assert art["layers_manifest_sha256"] == _digest_object(art["layers"])


def test_compute_is_deterministic(valentine_env: dict) -> None:
    first = _compute(valentine_env, "valentine_nyc", ruling="RULING-TEST-1")
    second = _compute(valentine_env, "valentine_nyc", ruling="RULING-TEST-1")
    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)


def test_cli_artifact_is_byte_identical_without_wall_clock(
    valentine_env: dict, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    out_a, out_b = tmp_path / "a.json", tmp_path / "b.json"
    for out in (out_a, out_b):
        monkeypatch.setattr(sys, "argv", _argv(valentine_env, "valentine_nyc", out, ruling="RULING-TEST-1"))
        assert runner.main() == 0
    assert out_a.read_bytes() == out_b.read_bytes()
    payload = json.loads(out_a.read_text(encoding="utf-8"))
    assert payload["commit"] == COMMIT
    assert "executed_at" not in payload


def test_input_sha256_mismatch_fails_closed(valentine_env: dict) -> None:
    victim = Path(str(valentine_env["root"])) / "valentine/experiments/data/PAIR_00/source_table.csv"
    victim.write_text(victim.read_text(encoding="utf-8") + "tampered\n", encoding="utf-8", newline="\n")
    with pytest.raises(SplitError) as exc:
        _compute(valentine_env, "valentine_nyc")
    assert exc.value.code == "input_sha256_mismatch"


def test_input_absent_from_manifest_fails_closed(finqa_env: dict, tmp_path: Path) -> None:
    root = Path(str(finqa_env["root"]))
    finqa_env["manifest"] = _manifest(root, ("dev.json",))
    with pytest.raises(SplitError) as exc:
        _compute(finqa_env, "finqa")
    assert exc.value.code == "input_not_in_sha256_manifest"


def test_finqa_lineage_root_cluster_and_source_split(finqa_env: dict) -> None:
    art = _compute(finqa_env, "finqa", ruling="RULING-TEST-1")
    rows = [row for _, row in _flat(art)]
    assert len(rows) == 6
    roots = {row["lineage_root_id"] for row in rows}
    assert "AAA/2009/page_1.pdf" in roots and "CCC/2011/page_9.pdf" in roots
    page1 = [row for row in rows if row["lineage_root_id"] == "AAA/2009/page_1.pdf"]
    assert len(page1) == 2 and page1[0]["uid"] == page1[1]["uid"]
    assert page1[0]["source_split"] == "train"
    assert [r for r in rows if r["lineage_root_id"] == "AAA/2009/page_3.pdf"][0]["source_split"] == "dev"
    # One filing spans the official train and dev files, yet must land in a single layer.
    aaa = [(name, row) for name, row in _flat(art)
           if row["independence_cluster"] == "finqa_financial_reports:AAA/2009"]
    assert len(aaa) == 4
    assert len({name for name, _ in aaa}) == 1
    assert art["dataset_revision"] == FINQA_HEAD


def test_unparsable_finqa_id_fails_closed(tmp_path: Path) -> None:
    root = tmp_path / "staging"
    _make_finqa(root, ["not-a-finqa-id"], [])
    env = {"root": root, "manifest": _manifest(root), "registry": _registry(tmp_path)}
    with pytest.raises(SplitError) as exc:
        _compute(env, "finqa")
    assert exc.value.code == "unparsable_example_id"


def test_universe_rule_is_hash_bound_and_bounded(valentine_env: dict) -> None:
    full = _compute(valentine_env, "valentine_nyc", m_universe=1)
    assert full["counts"]["clusters_in_universe"] == 40
    assert full["counts"]["excluded_by_universe_rule"] == 0
    bounded = _compute(valentine_env, "valentine_nyc", m_universe=3)
    assert 0 < bounded["counts"]["clusters_in_universe"] < 40
    clusters = {row["independence_cluster"] for _, row in _flat(bounded)}
    clusters |= {p["row"]["independence_cluster"] for p in bounded["pending_ruling_rows"]}
    for cluster in clusters:
        key = cluster.split(":", 1)[1]
        assert runner.bucket(runner.UNIVERSE_SALT, key, 3) == 0


def test_namespace_must_exist_in_registry(tmp_path: Path) -> None:
    root = tmp_path / "staging"
    _make_valentine(root, pairs=2, cols=2)
    registry = tmp_path / "registry.json"
    _write_json(registry, {"sources": [{"dataset_id": "finqa", "checked_default_head": FINQA_HEAD,
                                       "independence_cluster_namespace": "finqa_financial_reports",
                                       "role_fit": ["proposal_train"]}]})
    env = {"root": root, "manifest": _manifest(root, ("ground_truth.json", "target_table.csv")),
           "registry": registry}
    with pytest.raises(SplitError) as exc:
        _compute(env, "valentine_nyc")
    assert exc.value.code == "namespace_not_in_registry"


def test_invalid_commit_and_m_universe_fail_closed(
    valentine_env: dict, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(sys, "argv", _argv(valentine_env, "valentine_nyc", tmp_path / "o.json", commit="abc"))
    with pytest.raises(SplitError) as exc:
        runner.main()
    assert exc.value.code == "invalid_split_commit"
    monkeypatch.setattr(sys, "argv", _argv(valentine_env, "valentine_nyc", tmp_path / "o.json", m_universe=0))
    with pytest.raises(SplitError) as exc:
        runner.main()
    assert exc.value.code == "invalid_m_universe"
    assert not (tmp_path / "o.json").exists()


def test_zero_connect_guard() -> None:
    original_connect = socket.socket.connect
    original_cc = socket.create_connection
    try:
        install_network_guard()
        with pytest.raises(SplitError):
            socket.create_connection(("127.0.0.1", 8004), timeout=1)
    finally:
        socket.socket.connect = original_connect
        socket.create_connection = original_cc
