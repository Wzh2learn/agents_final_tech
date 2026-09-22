"""Positive/negative controls for docs_lint [5] registry<->distribution reconcile.

Decision 51 (i) / batch #9-B: [5] must skip registry rows whose purpose column marks
DEPRECATED (they are retained on purpose by governance rule 4 and are therefore absent
from the distribution lists), and it must emit an info line so those rows do not go
invisible. The controls below pin both halves of that contract.

Both controls run the check inside an isolated tmp copy of the two inputs, so the live
repo files are never modified by the test.
"""
import importlib.util
import os
import sys

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _load_lint():
    path = os.path.join(REPO, "scripts", "docs_lint.py")
    if not os.path.isfile(path):
        pytest.skip("scripts/docs_lint.py not available")
    spec = importlib.util.spec_from_file_location("docs_lint_under_test", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["docs_lint_under_test"] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture()
def lint(tmp_path, monkeypatch):
    """docs_lint bound to a throwaway registry + sync_skills.sh + skills/."""
    mod = _load_lint()
    import shutil
    monkeypatch.setattr(mod, "REPO_ROOT", str(tmp_path), raising=True)
    # minimal skills/ tree: one dir per name we reference
    (tmp_path / "skills").mkdir()
    (tmp_path / "docs" / "governance").mkdir(parents=True)
    monkeypatch.setattr(
        mod,
        "SKILL_REGISTRY",
        str(tmp_path / "docs" / "governance" / "SKILL_REGISTRY.md"),
        raising=True,
    )
    (tmp_path / "scripts" / "graph").mkdir(parents=True)
    shutil.copy(os.path.join(REPO, "scripts", "graph", "sync_skills.sh"),
                tmp_path / "scripts" / "graph" / "sync_skills.sh")
    return mod


def _write_sync(mod, a_names, c_names):
    p = os.path.join(mod.REPO_ROOT, "scripts", "graph", "sync_skills.sh")
    body = "A_SKILLS=(%s)\nC_SKILLS=(%s)\n" % (" ".join(a_names), " ".join(c_names))
    with open(p, "w", encoding="utf-8") as fh:
        fh.write(body)


def _write_registry(mod, rows):
    """rows: list of (loop, skill, purpose)."""
    head = ("# test\n\n**\u914d\u5c5e\u6ce8\u518c\u8868**:\n\n"
            "| Loop | Harness | skill | \u7528\u9014 |\n|---|---|---|---|\n")
    body = "".join("| %s | Codex CLI | %s | %s |\n" % r for r in rows)
    with open(mod.SKILL_REGISTRY, "w", encoding="utf-8") as fh:
        fh.write(head + body)


LIVE = "verify-before-done"


def test_positive_deprecated_row_may_be_absent_from_distribution(lint):
    """Removing a DEPRECATED-destined skill from the list must keep [5] PASS."""
    _write_registry(lint, [("A", LIVE, "active"),
                           ("A", "verification-before-completion",
                            "DEPRECATED 2026-08-25: superseded")])
    _write_sync(lint, [LIVE], [])
    fails, _warns, info = lint.check_registry_distribution()
    assert fails == [], "a DEPRECATED registry row must not fail [5]: %r" % (fails,)
    assert any("DEPRECATED" in i for i in info), \
        "the skipped row must still be reported via an info line: %r" % (info,)


def test_negative_non_deprecated_row_absent_from_distribution_fails(lint):
    """Negative control: a NON-deprecated registered skill missing from the list fails."""
    _write_registry(lint, [("A", LIVE, "active"),
                           ("A", "some-live-skill", "active, not deprecated")])
    _write_sync(lint, [LIVE], [])
    fails, _warns, _info = lint.check_registry_distribution()
    assert any("some-live-skill" in f for f in fails), \
        "a non-DEPRECATED registered skill missing from A_SKILLS must fail [5]: %r" % (fails,)
