from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

from research.valentine_process_checkpoint_adapter import AdapterError, build
from research.valentine_q3_review_package import APPROVED_PAIRS

REVISION = "5d5163f04da304985bd51a476ccf7653de3979c3"
INVALID_PAIR = "City_Government__DSNY_Districts_With_Disposal_Vendor_Assignments"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _call(source: str, target: str, name: str = "record_match", call_id: str = "call-1") -> dict:
    return {
        "id": call_id,
        "name": name,
        "args": {
            "source_column": source,
            "target_column": target,
            "confidence": 0.75,
            "reasoning": "candidate evidence",
            "transformation_code": "identity",
        },
    }


def _state(call: dict) -> dict:
    return {"content": "", "reasoning_content": "", "tool_calls": [call]}


def _audit_row(turn: int, call: dict, *, rewritten: bool = False) -> dict:
    state = _state(call)
    return {
        "turn": turn,
        "agent_a_raw": state,
        "agent_b_verdict": {
            "reason": "",
            "severity": "critical" if rewritten else "fine",
            "suggested_alternative": None,
            "verdict": "REJECT" if rewritten else "ACCEPT",
        },
        "agent_c_revised": state if rewritten else None,
        "agent_d_reviews": [],
        "final": state,
        "was_rewritten": rewritten,
    }


def _rewrite_manifest(staging: Path, path: Path) -> None:
    manifest = staging / "sha256_manifest.txt"
    rows = manifest.read_text().splitlines()
    relpath = path.relative_to(staging).as_posix()
    rows = [(_sha256(path) + "  " + relpath if line.endswith(relpath) else line) for line in rows]
    manifest.write_text("\n".join(rows) + "\n", encoding="utf-8", newline="\n")


def _make_staging(root: Path) -> Path:
    staging = root / "staging"
    data_root = staging / "valentine" / "experiments" / "data"
    data_root.mkdir(parents=True)
    manifest_rows: list[str] = []
    for index, pair in enumerate(APPROVED_PAIRS):
        pair_dir = data_root / pair
        pair_dir.mkdir()
        source = pair_dir / "source_table.csv"
        target = pair_dir / "target_table.csv"
        gold = pair_dir / "ground_truth.json"
        full = pair_dir / f"{pair}_full.json"
        result = pair_dir / f"{pair}_result.json"
        trajectory = pair_dir / f"{pair}_trajectory.json"
        source.write_text(f"src_{index},other_{index}\nrow,row\n", encoding="utf-8", newline="\n")
        target.write_text("target_a,target_b\nrow,row\n", encoding="utf-8", newline="\n")
        gold.write_text("{\"matches\": []}\n", encoding="utf-8", newline="\n")
        if pair == INVALID_PAIR:
            audit = [
                _audit_row(1, _call(f"src_{index}", "target_a", call_id="call-valid")),
                _audit_row(12, _call("mgp_curb_pri_boro", "target_a", "record_match", "call_c4f11200e31c4c269217b8dc"), rewritten=True),
                _audit_row(13, _call("mgp_curb_pri_boro", "target_a", "revoke_match", "call_59ac6c3556084cfea42c037f"), rewritten=True),
                _audit_row(31, _call("mgp_curb_pri_boro", "target_a", "batch_record_match", "call_5e32f59bddca46e18a95c413"), rewritten=True),
            ]
        else:
            audit = [_audit_row(1, _call(f"src_{index}", "target_a"))]
        full.write_text(json.dumps({
            "audit_trail": audit,
            "ground_truth": {"matches": [{"secret": "must-not-leak"}]},
            "final_evaluation": {"f1_score": 1.0},
        }), encoding="utf-8", newline="\n")
        result.write_text("{\"status\": \"posthoc\"}\n", encoding="utf-8", newline="\n")
        trajectory.write_text(json.dumps({
            "metadata": {"trajectory_log": [{"accepted": True, "tool_calls": [], "turn": row["turn"]} for row in audit]},
            "trajectory": [{"role": "assistant", "content": ""}],
        }), encoding="utf-8", newline="\n")
        for path in (source, target, gold, full, result, trajectory):
            manifest_rows.append(f"{_sha256(path)}  valentine/experiments/data/{pair}/{path.name}")
    (staging / "sha256_manifest.txt").write_text("\n".join(manifest_rows) + "\n", encoding="utf-8", newline="\n")
    return staging


def test_quarantine_primary_is_gold_free_and_exact(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    staging = _make_staging(tmp_path)
    opened: list[str] = []
    original_open = Path.open

    def tracking_open(self: Path, *args, **kwargs):
        if self.name == "ground_truth.json":
            opened.append(self.name)
            raise AssertionError("ground_truth.json must not be opened")
        return original_open(self, *args, **kwargs)

    monkeypatch.setattr(Path, "open", tracking_open)
    summary = build(staging, REVISION, tmp_path / "out")

    assert opened == []
    assert summary["analysis_variant"] == "quarantine-primary"
    assert summary["pair_count"] == 10
    assert summary["analysis_pair_count"] == 10
    assert summary["event_count"] == 10
    assert summary["invalid_action_reference_count"] == 3
    assert summary["analysis_source_header_count"] == 20
    assert summary["correctness_status"] == "NOT_RUN"
    assert summary["ground_truth_read"] is False
    assert summary["embedded_gold_exposed"] is False

    quarantine = [json.loads(line) for line in (tmp_path / "out" / "quarantine_events.jsonl").read_text().splitlines()]
    assert len(quarantine) == 3
    assert {(row["turn"], row["tool_name"]) for row in quarantine} == {
        (12, "record_match"),
        (13, "revoke_match"),
        (31, "batch_record_match"),
    }
    assert all(row["invalid_source_reference"] == "mgp_curb_pri_boro" for row in quarantine)
    assert "must-not-leak" not in (tmp_path / "out" / "checkpoint_summary.json").read_text()


def test_pair_invalid_sensitivity_excludes_whole_pair(tmp_path: Path) -> None:
    staging = _make_staging(tmp_path)
    summary = build(staging, REVISION, tmp_path / "out", "pair-invalid-sensitivity")

    assert summary["analysis_variant"] == "pair-invalid-sensitivity"
    assert summary["analysis_pair_count"] == 9
    assert summary["analysis_source_header_count"] == 18
    assert summary["event_count"] == 9
    assert summary["invalid_action_reference_count"] == 3
    assert summary["invalid_action_reference_pairs"] == [INVALID_PAIR]
    excluded = [row for row in summary["pairs"] if row["pair_id"] == INVALID_PAIR]
    assert len(excluded) == 1
    assert excluded[0]["analysis_included"] is False


def test_double_build_is_byte_identical(tmp_path: Path) -> None:
    staging = _make_staging(tmp_path)
    build(staging, REVISION, tmp_path / "out1")
    build(staging, REVISION, tmp_path / "out2")
    for name in ("checkpoint_events.jsonl", "quarantine_events.jsonl", "checkpoint_summary.json", "manifest.json"):
        assert (tmp_path / "out1" / name).read_bytes() == (tmp_path / "out2" / name).read_bytes(), name


def test_duplicate_header_fails_closed(tmp_path: Path) -> None:
    staging = _make_staging(tmp_path)
    source = staging / "valentine" / "experiments" / "data" / APPROVED_PAIRS[0] / "source_table.csv"
    source.write_text("same,same\nrow,row\n", encoding="utf-8", newline="\n")
    _rewrite_manifest(staging, source)
    with pytest.raises(AdapterError) as exc:
        build(staging, REVISION, tmp_path / "out")
    assert exc.value.code == "duplicate_source_header"


def test_extra_pair_file_fails_closed(tmp_path: Path) -> None:
    staging = _make_staging(tmp_path)
    extra = staging / "valentine" / "experiments" / "data" / APPROVED_PAIRS[0] / "extra.json"
    extra.write_text("{}\n", encoding="utf-8", newline="\n")
    with pytest.raises(AdapterError) as exc:
        build(staging, REVISION, tmp_path / "out")
    assert exc.value.code == "pair_file_allowlist_mismatch"


def test_invalid_tool_call_fails_closed(tmp_path: Path) -> None:
    staging = _make_staging(tmp_path)
    full = staging / "valentine" / "experiments" / "data" / APPROVED_PAIRS[0] / f"{APPROVED_PAIRS[0]}_full.json"
    obj = json.loads(full.read_text())
    obj["audit_trail"][0]["final"]["tool_calls"] = [{"name": "record_match", "args": {}}]
    full.write_text(json.dumps(obj), encoding="utf-8", newline="\n")
    _rewrite_manifest(staging, full)
    with pytest.raises(AdapterError) as exc:
        build(staging, REVISION, tmp_path / "out")
    assert exc.value.code == "invalid_tool_call_shape"


def test_unexpected_invalid_action_reference_fails_closed(tmp_path: Path) -> None:
    staging = _make_staging(tmp_path)
    full = staging / "valentine" / "experiments" / "data" / APPROVED_PAIRS[0] / f"{APPROVED_PAIRS[0]}_full.json"
    obj = json.loads(full.read_text())
    obj["audit_trail"][0]["final"]["tool_calls"][0]["args"]["source_column"] = "not_a_source_header"
    full.write_text(json.dumps(obj), encoding="utf-8", newline="\n")
    _rewrite_manifest(staging, full)
    with pytest.raises(AdapterError) as exc:
        build(staging, REVISION, tmp_path / "out")
    assert exc.value.code == "unexpected_invalid_action_reference"


def test_read_hash_mismatch_fails_closed(tmp_path: Path) -> None:
    staging = _make_staging(tmp_path)
    manifest = staging / "sha256_manifest.txt"
    manifest.write_text(manifest.read_text().replace("0", "1", 1), encoding="utf-8", newline="\n")
    with pytest.raises(AdapterError) as exc:
        build(staging, REVISION, tmp_path / "out")
    assert exc.value.code == "sha256_manifest_mismatch"


def test_output_dir_must_be_empty(tmp_path: Path) -> None:
    staging = _make_staging(tmp_path)
    out = tmp_path / "out"
    out.mkdir()
    (out / "sentinel.txt").write_text("keep", encoding="utf-8")
    with pytest.raises(AdapterError) as exc:
        build(staging, REVISION, out)
    assert exc.value.code == "output_dir_not_empty"
    assert (out / "sentinel.txt").read_text() == "keep"


def test_direct_script_help_does_not_need_pythonpath() -> None:
    repo = Path(__file__).resolve().parents[1]
    env = {"PATH": str(repo / "venv" / "bin") + ":" + "/usr/bin:/bin"}
    proc = subprocess.run([
        sys.executable,
        str(repo / "research" / "valentine_process_checkpoint_adapter.py"),
        "--help",
    ], cwd=repo, env=env, capture_output=True, text=True)
    assert proc.returncode == 0, proc.stderr
    assert "--analysis-variant" in proc.stdout
