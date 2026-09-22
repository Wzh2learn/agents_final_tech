"""Contracts that keep project entry-point documents usable as indexes."""

from __future__ import annotations

import importlib.util
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def _load_docs_lint():
    path = REPO_ROOT / "scripts" / "docs_lint.py"
    spec = importlib.util.spec_from_file_location("docs_lint_for_governance", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_agent_rules_are_a_thin_entry_point() -> None:
    text = (REPO_ROOT / "AGENTS.md").read_text(encoding="utf-8")

    assert len(text.splitlines()) <= 150
    for required in (
        "**Precedence:**",
        "memory/CORE.md",
        "memory/STATE.md",
        "memory/THREADS.md",
        "docs/INDEX.md",
        "docs/SKILL_ROUTING.md",
        "## Boundaries",
        "## Scoped AGENTS.md",
    ):
        assert required in text


def test_current_state_and_docs_index_are_navigational() -> None:
    state = (REPO_ROOT / "memory" / "STATE.md").read_text(encoding="utf-8")
    index = (REPO_ROOT / "docs" / "INDEX.md").read_text(encoding="utf-8")

    assert len(state.splitlines()) <= 100
    assert "STATE_2026-09-22_pre_governance.md" in state
    assert len(index.splitlines()) <= 180
    assert "experiments/" in index
    assert "archive/" in index


def test_docs_lint_registers_collections_by_directory() -> None:
    lint = _load_docs_lint()

    assert lint.index_registration_key("docs/experiments/a/report.md") == "experiments/"
    assert lint.index_registration_key("docs/governance/audit/run/report.md") == "governance/audit/"
    assert lint.index_registration_key("docs/architecture/codebase_map.md") == "codebase_map.md"
