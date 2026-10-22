from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SCRIPT = (
    ROOT
    / "research/publication_thesis_goals_v1/revision_v2/"
    "third_contribution_scope_reuse_probe.py"
)
FIXTURE_RESULTS = (
    ROOT
    / "research/publication_thesis_goals_v1/revision_v2/"
    "G3_REAL_ACTION_RESULTS_V2_COMPACT.json"
)
SHORT_RESULTS = (
    ROOT
    / "research/publication_thesis_goals_v1/revision_v2/"
    "G3_REAL_ACTION_RESULTS_V2_SHORT_INPUT_BEHAVIOR.json"
)


def test_same_candidate_dependency_fixed_input_regime_change(tmp_path: Path) -> None:
    output = tmp_path / "probe.json"
    subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--fixture-results",
            str(FIXTURE_RESULTS),
            "--short-input-results",
            str(SHORT_RESULTS),
            "--output",
            str(output),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(output.read_text(encoding="utf-8"))
    dependency = next(
        row for row in payload["policies"] if row["policy"] == "dependency_change_only"
    )
    scope = next(
        row
        for row in payload["policies"]
        if row["policy"] == "scope_fingerprint_dependency_and_input_regime"
    )
    assert all(
        row["dependency_changed_since_fixture_evidence"] is False
        for row in payload["rows"]
    )
    assert dependency["false_transfer_or_error"] >= 2
    assert scope["false_transfer_or_error"] == 0
    assert payload["scope_increment_identified"] is True
    assert payload["qualification"] == "QUALIFIED_FOR_BOUNDED_DEVELOPMENT"
