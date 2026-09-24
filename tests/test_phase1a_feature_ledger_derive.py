"""Tests for the phase1a feature-ledger derivation runner.

Fixtures are synthetic and self-declared as such; they exercise the runner's
validation and assembly logic only. Package-level gate verification happens at
assembly time against real roles.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from research.phase1a_feature_ledger_derive import (
    FEATURE_LEDGER_VERSION,
    LedgerDerivationError,
    derive,
)


def _write(tmp_path: Path, name: str, payload: object) -> Path:
    p = tmp_path / name
    p.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return p


@pytest.fixture()
def roles(tmp_path: Path) -> dict[str, Path]:
    return {
        "source_tables": _write(tmp_path, "source_tables.json", {"tables": [{"id": "t1"}]}),
        "schema": _write(tmp_path, "schema.json", {"fields": ["a", "b"]}),
        "confidence_manifest": _write(
            tmp_path,
            "confidence_manifest.json",
            {"field": "none_native", "missing_policy": "unmeasurable"},
        ),
    }


@pytest.fixture()
def layer_manifest() -> dict:
    return {
        "layers": {
            "proposal_train.train": [
                {"sample_id": "s1", "uid": "u1"},
                {"sample_id": "s2", "uid": "u2"},
            ],
            "proposal_train.dev": [{"sample_id": "s3", "uid": "u3"}],
            "gate_validation": [{"sample_id": "g1", "uid": "ug"}],
        }
    }


def _row(sample_id: str, uid: str, **over: object) -> dict:
    row = {
        "sample_id": sample_id,
        "uid": uid,
        "observed_header": "h|" + sample_id,
        "canonical_fields": ["a", "b"],
        "candidate_target": "a",
        "confidence": None,
        "family": "unperturbed",
    }
    row.update(over)
    return row


def _inputs(*rows: dict) -> dict:
    return {"rows": list(rows)}


def test_positive_derivation(tmp_path: Path, roles: dict[str, Path], layer_manifest: dict) -> None:
    ledger = derive(
        _inputs(_row("s1", "u1"), _row("s2", "u2"), _row("s3", "u3", family="alias_variant")),
        layer_manifest,
        roles,
    )
    assert set(ledger) == {
        "contract_version",
        "source_tables_sha256",
        "schema_sha256",
        "confidence_manifest_sha256",
        "rows",
    }
    assert ledger["contract_version"] == FEATURE_LEDGER_VERSION
    assert [r["sample_id"] for r in ledger["rows"]] == ["s1", "s2", "s3"]
    assert all(r["confidence"] is None for r in ledger["rows"])
    first = json.dumps(ledger, sort_keys=True)
    again = derive(
        _inputs(_row("s3", "u3", family="alias_variant"), _row("s1", "u1"), _row("s2", "u2")),
        layer_manifest,
        roles,
    )
    assert json.dumps(again, sort_keys=True) == first  # order-independent determinism


def test_gate_sample_rejected(tmp_path: Path, roles: dict[str, Path], layer_manifest: dict) -> None:
    with pytest.raises(LedgerDerivationError) as exc:
        derive(_inputs(_row("s1", "u1"), _row("s2", "u2"), _row("g1", "ug")), layer_manifest, roles)
    assert exc.value.code == "feature_ledger_identity_mismatch"


def test_coverage_mismatch(tmp_path: Path, roles: dict[str, Path], layer_manifest: dict) -> None:
    with pytest.raises(LedgerDerivationError) as exc:
        derive(_inputs(_row("s1", "u1"), _row("s2", "u2")), layer_manifest, roles)
    assert exc.value.code == "feature_ledger_proposal_coverage_mismatch"
    assert exc.value.detail["missing"] == ["s3"]


def test_uid_mismatch(tmp_path: Path, roles: dict[str, Path], layer_manifest: dict) -> None:
    with pytest.raises(LedgerDerivationError) as exc:
        derive(
            _inputs(_row("s1", "u-wrong"), _row("s2", "u2"), _row("s3", "u3")),
            layer_manifest,
            roles,
        )
    assert exc.value.code == "feature_ledger_identity_mismatch"


def test_candidate_outside_canonical(tmp_path: Path, roles: dict[str, Path], layer_manifest: dict) -> None:
    with pytest.raises(LedgerDerivationError) as exc:
        derive(
            _inputs(
                _row("s1", "u1", candidate_target="zzz"),
                _row("s2", "u2"),
                _row("s3", "u3"),
            ),
            layer_manifest,
            roles,
        )
    assert exc.value.code == "invalid_feature_ledger_row"
    assert exc.value.detail["why"] == "candidate_target"


def test_confidence_vocabulary(tmp_path: Path, roles: dict[str, Path], layer_manifest: dict) -> None:
    with pytest.raises(LedgerDerivationError) as exc:
        derive(
            _inputs(_row("s1", "u1", confidence="bogus"), _row("s2", "u2"), _row("s3", "u3")),
            layer_manifest,
            roles,
        )
    assert exc.value.detail["why"] == "confidence"


def test_duplicate_canonical_fields(tmp_path: Path, roles: dict[str, Path], layer_manifest: dict) -> None:
    with pytest.raises(LedgerDerivationError) as exc:
        derive(
            _inputs(
                _row("s1", "u1", canonical_fields=["a", "a"]),
                _row("s2", "u2"),
                _row("s3", "u3"),
            ),
            layer_manifest,
            roles,
        )
    assert exc.value.detail["why"] == "canonical_fields"


def test_empty_rows_rejected(tmp_path: Path, roles: dict[str, Path], layer_manifest: dict) -> None:
    with pytest.raises(LedgerDerivationError) as exc:
        derive(_inputs(), layer_manifest, roles)
    assert exc.value.code == "invalid_feature_ledger_rows"