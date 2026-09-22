"""Contracts for routing only to installable top-level repository skills."""

from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_primary_routing_entries_are_installable_top_level_skills() -> None:
    available = {
        path.parent.name for path in (REPO_ROOT / "skills").glob("*/SKILL.md")
    }
    text = (REPO_ROOT / "docs" / "SKILL_ROUTING.md").read_text(encoding="utf-8")
    section = text.split("## 1 ", 1)[1].split("## 2 ", 1)[0]
    routed: set[str] = set()
    for line in section.splitlines():
        if not line.startswith("|") or "---" in line or "主装" in line:
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        for cell in cells[1:3]:
            routed.update(part.strip() for part in cell.split("/") if part.strip())

    assert sorted(routed - available) == []
