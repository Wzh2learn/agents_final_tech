"""Contracts for keeping production M1 code inside the ``src`` package."""

from __future__ import annotations

import ast
import importlib
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_parser_and_ingest_have_canonical_biz_modules() -> None:
    parser = importlib.import_module("biz.m1_statement_parser")
    ingest = importlib.import_module("biz.m1_rag_ingest")

    assert parser.__file__ and "/src/biz/" in parser.__file__.replace("\\", "/")
    assert ingest.__file__ and "/src/biz/" in ingest.__file__.replace("\\", "/")


def test_legacy_script_imports_alias_canonical_modules(monkeypatch) -> None:
    monkeypatch.syspath_prepend(str(REPO_ROOT / "scripts"))
    for legacy_name, canonical_name in (
        ("m1_statement_parser", "biz.m1_statement_parser"),
        ("m1_rag_ingest", "biz.m1_rag_ingest"),
    ):
        sys.modules.pop(legacy_name, None)
        legacy = importlib.import_module(legacy_name)
        canonical = importlib.import_module(canonical_name)
        assert legacy is canonical


def test_production_callers_do_not_load_modules_from_scripts() -> None:
    def function_source(relative_path: str, function_name: str) -> str:
        text = (REPO_ROOT / relative_path).read_text(encoding="utf-8")
        tree = ast.parse(text)
        node = next(
            item
            for item in tree.body
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))
            and item.name == function_name
        )
        return ast.get_source_segment(text, node) or ""

    parser_loader = function_source("src/web/routers/m1.py", "_get_parser")
    rag_loader = function_source("src/biz/m2_service.py", "_load_rag")
    assert "scripts" not in parser_loader
    assert "scripts" not in rag_loader
    assert "from biz import m1_statement_parser" in parser_loader
    assert "from biz import m1_rag_ingest" in rag_loader
