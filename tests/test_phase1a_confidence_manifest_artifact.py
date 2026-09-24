"""Contract-condition checks for the landed confidence_manifest artifact (current corpus)."""
from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
ARTIFACT = REPO / "docs" / "datasets" / "phase1a_confidence_manifest_current_corpus_v1.json"


def test_confidence_manifest_artifact_satisfies_contract_conditions() -> None:
    doc = json.loads(ARTIFACT.read_text(encoding="utf-8"))
    assert isinstance(doc["field"], str) and doc["field"]
    assert isinstance(doc["source"], str) and doc["source"]
    assert doc["missing_policy"] == "unmeasurable"
    assert doc["gain_collateral_substitution"] is False
    assert set(doc["allowed_values"]) == {"low", "medium", "high"}
    assert doc["provenance"]["measured_at"] == "2026-09-24"