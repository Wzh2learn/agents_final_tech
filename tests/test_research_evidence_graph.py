"""Offline graph validates only structure and explicit file bindings."""
import hashlib
import json
from pathlib import Path

import pytest

from scripts.graph.research_evidence_graph import main, validate


def fixture(root):
    (root / "raw.json").write_text('{"result": "failed"}', encoding="utf-8")
    sha = hashlib.sha256((root / "raw.json").read_bytes()).hexdigest()
    return {
        "version": 1,
        "candidates": [
            {"id": "a", "parent": None, "hypothesis": "h", "baseline": "b", "source": "s", "conclusion": "unknown"},
            {"id": "b", "parent": "a", "hypothesis": "h2", "baseline": "b", "source": "s", "conclusion": "continue"},
        ],
        "evidence": [{"id": "raw", "path": "raw.json", "sha256": sha}],
        "trials": [
            {"id": "t1", "candidate": "a", "phase": "subset", "outcome": "truncated", "status": "engineering_failure", "evidence": ["raw"], "cost": None, "cost_unit": "tokens"},
            {"id": "t2", "candidate": "b", "phase": "full", "outcome": "not run", "status": "unknown", "evidence": [], "cost": 0, "cost_unit": "tokens"},
        ],
        "reviews": [{"id": "r", "candidate": "a", "reviewer": "AI", "conclusion": "needs work", "evidence": ["raw"]}],
    }


def test_valid_graph_and_cli_do_not_modify_inputs(tmp_path, capsys):
    snapshot = fixture(tmp_path)
    path = tmp_path / "snapshot.json"
    path.write_text(json.dumps(snapshot), encoding="utf-8")
    before = path.read_bytes()
    assert main(["--root", str(tmp_path), "snapshot.json"]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["valid"] and result["evidence_hashes_checked"] == 1
    assert "no claim" in result["scope"]
    assert path.read_bytes() == before
    assert snapshot["trials"][0]["cost"] is None and snapshot["trials"][1]["cost"] == 0


def test_detects_tamper_missing_and_dangling_references(tmp_path):
    snapshot = fixture(tmp_path)
    (tmp_path / "raw.json").write_text("altered", encoding="utf-8")
    snapshot["trials"][0]["evidence"] = ["absent"]
    report = validate(tmp_path, snapshot)
    assert any("hash mismatch" in error for error in report["errors"])
    assert any("invalid evidence" in error for error in report["errors"])
    (tmp_path / "raw.json").unlink()
    assert any("missing" in error for error in validate(tmp_path, snapshot)["errors"])


def test_rejects_duplicate_ids_cycles_and_bad_cost(tmp_path):
    snapshot = fixture(tmp_path)
    snapshot["candidates"][0]["parent"] = "b"
    snapshot["reviews"][0]["id"] = "t1"
    snapshot["trials"][1]["cost"] = True
    errors = validate(tmp_path, snapshot)["errors"]
    assert any("cycle" in error for error in errors)
    assert any("duplicate id" in error for error in errors)
    assert any("cost" in error for error in errors)


@pytest.mark.parametrize("name", ["../other", "/absolute", "../raw.json"])
def test_rejects_untrusted_paths(tmp_path, name):
    snapshot = fixture(tmp_path)
    snapshot["evidence"][0]["path"] = name
    assert not validate(tmp_path, snapshot)["valid"]


def test_rejects_symlink_escape(tmp_path):
    snapshot = fixture(tmp_path)
    outside = tmp_path.parent / (tmp_path.name + "-outside")
    outside.write_text("not in root", encoding="utf-8")
    try:
        (tmp_path / "escape").symlink_to(outside)
    except OSError:
        pytest.skip("symlinks unavailable")
    snapshot["evidence"][0]["path"] = "escape"
    assert not validate(tmp_path, snapshot)["valid"]


def test_malformed_missing_fields_and_schema_never_approve(tmp_path, capsys):
    snapshot = fixture(tmp_path)
    del snapshot["trials"][0]["cost"]
    snapshot["trials"][1]["status"] = "accepted_for_publication"
    assert not validate(tmp_path, snapshot)["valid"]
    assert not validate(tmp_path, {"version": 1})["valid"]
    (tmp_path / "bad.json").write_text("{", encoding="utf-8")
    assert main(["--root", str(tmp_path), "bad.json"]) == 1
    assert not json.loads(capsys.readouterr().out)["valid"]


@pytest.mark.parametrize("status", ["success", "failure", "engineering_failure"])
def test_completed_outcomes_require_referenced_evidence(tmp_path, status):
    snapshot = fixture(tmp_path)
    snapshot["trials"][0]["status"] = status
    snapshot["trials"][0]["evidence"] = []
    assert any("requires evidence" in e for e in validate(tmp_path, snapshot)["errors"])


def test_unobserved_draft_has_explicit_no_evidence_status(tmp_path):
    snapshot = fixture(tmp_path)
    snapshot["evidence"] = []
    snapshot["reviews"] = []
    snapshot["trials"] = [snapshot["trials"][1]]
    report = validate(tmp_path, snapshot)
    assert report["valid"]
    assert report["evidence_hashes_checked"] == 0
    assert report["evidence_binding_status"] == "no_evidence_supplied"


@pytest.mark.parametrize("raw", [
    '{"version":1,"version":1}',
    '{"version":1,"trials":[{"status":"unknown","status":"success"}]}',
    '{"version":1,"evidence":[{"sha256":"a","sha256":"b"}]}',
])
def test_cli_rejects_duplicate_keys_at_any_depth(tmp_path, capsys, raw):
    (tmp_path / "duplicate.json").write_text(raw, encoding="utf-8")
    assert main(["--root", str(tmp_path), "duplicate.json"]) == 1
    result = json.loads(capsys.readouterr().out)
    assert not result["valid"] and "duplicate JSON key" in result["errors"][0]


def test_invalid_nested_types_are_reported_without_crash(tmp_path, capsys):
    snapshot = fixture(tmp_path)
    snapshot["candidates"][0]["parent"] = []
    snapshot["trials"][0]["status"] = {"bogus": "value"}
    snapshot["trials"][0]["evidence"] = [{}]
    snapshot["trials"][0]["cost"] = []
    snapshot["evidence"][0]["path"] = {}
    (tmp_path / "types.json").write_text(json.dumps(snapshot), encoding="utf-8")
    assert main(["--root", str(tmp_path), "types.json"]) == 1
    assert len(json.loads(capsys.readouterr().out)["errors"]) >= 4


@pytest.mark.parametrize("location", ["root", "snapshot", "evidence"])
def test_cli_reports_resolve_runtime_error_as_json(tmp_path, capsys, monkeypatch, location):
    snapshot = fixture(tmp_path)
    if location == "evidence":
        snapshot["evidence"][0]["path"] = "loop"
    (tmp_path / "snapshot.json").write_text(json.dumps(snapshot), encoding="utf-8")
    target = tmp_path if location == "root" else tmp_path / ("loop" if location == "evidence" else "snapshot.json")
    original = Path.resolve

    def fail_target(self, *args, **kwargs):
        if self == target:
            raise RuntimeError("Symlink loop")
        return original(self, *args, **kwargs)

    monkeypatch.setattr(Path, "resolve", fail_target)
    assert main(["--root", str(tmp_path), "snapshot.json"]) == 1
    report = json.loads(capsys.readouterr().out)
    assert report["valid"] is False and report["errors"]


@pytest.mark.parametrize("location", ["root", "snapshot", "evidence"])
def test_cli_handles_real_symlink_loop(tmp_path, capsys, location):
    snapshot = fixture(tmp_path)
    if location == "evidence":
        snapshot["evidence"][0]["path"] = "loop"
    (tmp_path / "snapshot.json").write_text(json.dumps(snapshot), encoding="utf-8")
    try:
        (tmp_path / "loop").symlink_to("loop")
    except OSError:
        pytest.skip("symlinks unavailable")
    root = tmp_path / "loop" if location == "root" else tmp_path
    snapshot_path = "loop" if location == "snapshot" else "snapshot.json"
    assert main(["--root", str(root), snapshot_path]) == 1
    report = json.loads(capsys.readouterr().out)
    assert report["valid"] is False and report["errors"]
