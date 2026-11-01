import sys

import pytest

import run_dbscan_reference_20261101 as runner


@pytest.mark.parametrize("verifier_valid", [False, True])
def test_verifier_hash_is_checked_before_any_container_run(tmp_path, monkeypatch, verifier_valid):
    def fake_sha(path):
        if path.name == "solve.py":
            return runner.SOURCES[1]
        if path.name == "expected_frontier.csv":
            return runner.EXPECTED[1]
        if path.name == "test_outputs.py":
            return runner.TEST_HASH if verifier_valid else "wrong-verifier"
        return runner.DATA[path.name]

    monkeypatch.setattr(runner, "sha", fake_sha)
    monkeypatch.setattr(runner.subprocess, "check_output", lambda *args, **kwargs: "wrong-image\n")
    monkeypatch.setattr(sys, "argv", ["runner", "1", "--checkout", str(tmp_path),
                                     "--dependencies", str(tmp_path), "--output", str(tmp_path / "out")])
    expected = "container image changed" if verifier_valid else "released verifier changed"
    with pytest.raises(ValueError, match=expected):
        runner.main()
    assert not (tmp_path / "out").exists()
