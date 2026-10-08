"""Contracts that keep project entry-point documents usable as indexes."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import re


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


def test_audit_cycle_governance_references_resolve() -> None:
    text = (REPO_ROOT / "skills" / "audit-cycle" / "SKILL.md").read_text(encoding="utf-8")
    for relative in (
        "docs/governance/reference/APPEND_ONLY_LEDGER_PATTERN.md",
        "docs/governance/reference/FOUR_CONCEPT_SEPARATION_PATTERN.md",
        "docs/governance/reference/GOVERNANCE_INVENTORY_PATTERN.md",
    ):
        assert relative in text, relative
        assert (REPO_ROOT / relative).is_file(), relative


def test_review_governance_patterns_resolve() -> None:
    reference = REPO_ROOT / "docs" / "governance" / "reference"
    names = (
        "ACTION_FORMAT_SPEC.md",
        "EXPERT_REVIEW_REQUEST_PATTERN.md",
        "TRIPLE_AUDIT_PATTERN.md",
        "TIERED_EVAL_PATTERN.md",
        "RUNTIME_REDACTION_PATTERN.md",
        "UNTRUSTED_CHANNEL_DEFENSE_PATTERN.md",
        "SPEND_BUDGET_PATTERN.md",
        "EXTERNAL_CALL_RELIABILITY_PATTERN.md",
    )
    for name in names:
        assert (reference / name).is_file(), name

    task_card = (REPO_ROOT / "templates" / "task_card_template.md").read_text(encoding="utf-8")
    for name in names:
        assert name in task_card, name

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


def test_advisor_materials_link_to_the_current_execution_plan() -> None:
    plan = "docs/handoff/2026-09-22-paper-research-next-phase.md"
    for relative in (
        "paper/teacher_review_note_v2.md",
        "paper/teacher_review_readiness_v2.md",
        "paper/thesis_manuscript_scaffold_v1.md",
    ):
        text = (REPO_ROOT / relative).read_text(encoding="utf-8")
        assert plan in text, relative
        assert "先等待老师确认" not in text, relative
        assert "蒸馏结果闭合后，用同一候选流" not in text, relative


def test_active_loop_prompts_use_current_authorities() -> None:
    for relative in (
        "scripts/graph/loop_a_exec_constraints.md",
        "scripts/graph/loop_c_audit_prompt.md",
    ):
        text = (REPO_ROOT / relative).read_text(encoding="utf-8")
        for authority in (
            "AGENTS.md",
            "memory/STATE.md",
            "docs/research/README.md",
            "docs/governance/2026-09-07_execution_plane_boundary.md",
        ):
            assert authority in text, (relative, authority)
        assert "FastAPI 在 :5000" not in text
        assert "HANDOFF.md (项目交接状态)" not in text


def test_research_plan_binds_execution_to_existing_governance() -> None:
    plan = REPO_ROOT / "docs/handoff/2026-09-22-paper-research-next-phase.md"
    text = plan.read_text(encoding="utf-8")
    for reference in (
        "docs/29_graph_engineering_roadmap.md",
        "docs/17_Graph_Engineering_多层Loop设计.md",
        "docs/governance/2026-09-07_execution_plane_boundary.md",
        "templates/task_card_template.md",
    ):
        assert reference in text, reference


def test_orchestrator_messages_do_not_claim_automatic_dispatch() -> None:
    text = (REPO_ROOT / "scripts/graph/graph_orchestrator.sh").read_text(encoding="utf-8")
    assert "All loops started." not in text
    assert "codex exec --profile" not in text
    assert "docs/17 §8" not in text
    assert "scripts/graph/loop_a_exec_constraints.md" in text
    assert "scripts/graph/loop_c_audit_prompt.md" in text
    assert "templates/task_card_template.md" in text
    assert "docs/governance/2026-09-07_execution_plane_boundary.md" in text


def test_code_map_separates_assets_from_live_health() -> None:
    text = (REPO_ROOT / "docs/architecture/codebase_map.md").read_text(encoding="utf-8")
    for reference in (
        "research/vgmc_exp1.py",
        "research/dpo_pairs_v0.py",
        "paper/research_asset_map_v2.md",
        "memory/CORE.md",
    ):
        assert reference in text, reference
    assert "| healthy |" not in text
    paths = re.findall(r"`((?:src|scripts|research|tests|docs|memory|paper)/[^`*]+)`", text)
    assert paths
    for relative in paths:
        assert (REPO_ROOT / relative).exists(), relative
