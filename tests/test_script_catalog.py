"""Contracts for the scripts production/operations/experiments/archive catalog."""

from __future__ import annotations

import subprocess
import tomllib
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
CATALOG = REPO_ROOT / "scripts" / "catalog.toml"
CATEGORIES = {"production", "operations", "experiments", "archive"}


def test_every_tracked_script_has_exactly_one_category() -> None:
    data = tomllib.loads(CATALOG.read_text(encoding="utf-8"))
    assert set(data) == {"catalog", *CATEGORIES}

    tracked = set(
        subprocess.check_output(
            ["git", "ls-files", "scripts"], cwd=REPO_ROOT, text=True
        ).splitlines()
    )
    tracked -= {"scripts/README.md", "scripts/catalog.toml"}

    assignments: dict[str, list[str]] = {}
    for category in CATEGORIES:
        for relative_path in data[category].get("files", []):
            assignments.setdefault(f"scripts/{relative_path}", []).append(category)
        for root in data[category].get("roots", []):
            prefix = f"scripts/{root.rstrip('/')}/"
            for path in tracked:
                if path.startswith(prefix):
                    assignments.setdefault(path, []).append(category)

    assert sorted(tracked - assignments.keys()) == []
    assert sorted(assignments.keys() - tracked) == []
    assert {path: owners for path, owners in assignments.items() if len(owners) != 1} == {}
