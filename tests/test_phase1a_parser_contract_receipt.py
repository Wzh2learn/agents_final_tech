"""Tests for the phase1a parser_contract_receipt runner.

Fixtures are synthetic and self-declared; they exercise the frozen drop-rule
caliber, fail-closed rejections, determinism and the zero-connect guard.
"""
from __future__ import annotations

import json
import socket
import sys
from pathlib import Path

import pytest

from research.phase1a_parser_contract_receipt import (
    ReceiptError,
    compute,
    install_network_guard,
)

COMMIT = "0" * 40


@pytest.fixture()
def source_tables() -> dict:
    return {
        "tables": [
            {"uid": "u1", "table": [["asset total", "report date"], ["x", "y"]]},
            {"uid": "u2", "table": [["asset total", "report date"], ["p", "q"]]},
        ]
    }


@pytest.fixture()
def injection_map() -> dict:
    return {
        "mapping": [
            {
                "uid": "u1",
                "col": 0,
                "original": "asset total",
                "injected": "total assets",
                "type": "alias_variant",
            }
        ]
    }


def test_positive_compute(source_tables: dict, injection_map: dict) -> None:
    receipt = compute(source_tables, injection_map, None)
    assert receipt["status"] == "PASS"
    assert receipt["checker"] == "research/phase1a_parser_contract_receipt.py"
    assert receipt["drop_threshold"] == 2.0
    assert receipt["observed_ports"] == []
    assert [t["uid"] for t in receipt["tables"]] == ["u1", "u2"]
    fam = receipt["by_family"]["alias_variant"]
    assert fam["n"] == 1 and fam["visible"] + fam["absorbed"] == 1
    inj = receipt["injections"][0]
    assert set(inj) >= {"uid", "col", "type", "original", "injected", "canonical",
                        "h_orig", "h_single", "dH", "drop10",
                        "absorbed_full_injection", "visible_frozen"}
    assert inj["visible_frozen"] is (not inj["absorbed_full_injection"])


def test_determinism(source_tables: dict, injection_map: dict) -> None:
    a = json.dumps(compute(source_tables, injection_map, None), sort_keys=True)
    b = json.dumps(compute(source_tables, injection_map, None), sort_keys=True)
    assert a == b


def test_reference_mismatch_fails(source_tables: dict, injection_map: dict) -> None:
    ref = {"g3_detail": {"tables_discriminated_recomputed": 999, "by_type_recomputed": {}}}
    receipt = compute(source_tables, injection_map, ref)
    assert receipt["status"] == "FAIL"
    assert "reconciliation_tables_discriminated_mismatch" in receipt["reasons"]


def test_invalid_injection_entry(source_tables: dict) -> None:
    with pytest.raises(ReceiptError) as exc:
        compute(source_tables, {"mapping": [{"col": 0}]}, None)
    assert exc.value.code == "invalid_injection_entry"


def test_invalid_col_index(source_tables: dict) -> None:
    bad = {"mapping": [{"uid": "u1", "col": 77, "original": "a", "injected": "b"}]}
    with pytest.raises(ReceiptError) as exc:
        compute(source_tables, bad, None)
    assert exc.value.code == "invalid_injection_entry"


def test_zero_connect_guard() -> None:
    original_connect = socket.socket.connect
    original_cc = socket.create_connection
    try:
        install_network_guard()
        with pytest.raises(ReceiptError):
            socket.create_connection(("127.0.0.1", 8004), timeout=1)
    finally:
        socket.socket.connect = original_connect
        socket.create_connection = original_cc


def test_commit_validation(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from research import phase1a_parser_contract_receipt as runner

    src = tmp_path / "s.json"
    src.write_text(json.dumps({"tables": []}), encoding="utf-8")
    sch = tmp_path / "sch.json"
    sch.write_text("{}", encoding="utf-8")
    im = tmp_path / "im.json"
    im.write_text(json.dumps({"mapping": []}), encoding="utf-8")
    out = tmp_path / "receipt.json"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "runner",
            "--source-tables", str(src),
            "--schema", str(sch),
            "--injection-map", str(im),
            "--commit", "nothex",
            "--out", str(out),
        ],
    )
    with pytest.raises(ReceiptError) as exc:
        runner.main()
    assert exc.value.code == "invalid_parser_commit"