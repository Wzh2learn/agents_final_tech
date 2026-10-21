"""Frozen development fixtures and their fail-closed loader."""
from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Dict, Mapping, Sequence, Tuple

from .model import (
    ActorInput,
    ChangeSummary,
    ExecutionGraph,
    NodeDefinition,
    Operation,
    OutputId,
    Value,
)


DEV_ONLY_STATUS = "DEV_ONLY_AUTHORED_MECHANISM_FIXTURES"
PUBLIC_TOOL_NAMES = (
    "inspect_dependency",
    "inspect_change",
    "run_target_test",
)


CHECKER_GRAPH = ExecutionGraph(
    definitions=(
        NodeDefinition("price", Operation.SOURCE, ()),
        NodeDefinition("rate", Operation.SOURCE, ()),
        NodeDefinition("fee", Operation.SOURCE, ()),
        NodeDefinition("branch_flag", Operation.SOURCE, ()),
        NodeDefinition("bonus", Operation.SOURCE, ()),
        NodeDefinition("unused", Operation.SOURCE, ()),
        NodeDefinition("base", Operation.ADD, ("price", "fee")),
        NodeDefinition("scaled", Operation.MULTIPLY, ("base", "rate")),
        NodeDefinition("taxed", Operation.COPY, ("base",)),
        NodeDefinition("total", Operation.ADD, ("scaled", "taxed")),
        NodeDefinition("margin", Operation.SUBTRACT, ("scaled", "taxed")),
        NodeDefinition("audit", Operation.SELECT, ("branch_flag", "bonus", "scaled")),
    ),
    output_ids=("total", "margin", "audit"),
)


@dataclass(frozen=True)
class ScenarioFixture:
    """One frozen before-success and post-change development scenario."""

    scenario_id: str
    family: str
    description: str
    before_source_values: Mapping[str, Value]
    post_source_values: Mapping[str, Value]
    before_success_snapshot: Mapping[OutputId, Value]
    visible_dependencies: Mapping[str, Tuple[str, ...]]
    query_budget: int

    def changed_source_nodes(self) -> Tuple[str, ...]:
        """Return changed source nodes in stable lexical order."""
        return tuple(
            node_id
            for node_id in sorted(self.before_source_values)
            if self.before_source_values[node_id] != self.post_source_values[node_id]
        )

    def actor_input(self, graph: ExecutionGraph) -> ActorInput:
        """Construct the value-free actor input from frozen public fields."""
        changes = tuple(
            ChangeSummary(
                change_id=f"chg_{self.scenario_id}_{node_id}",
                node_id=node_id,
                change_kind="source_value",
            )
            for node_id in self.changed_source_nodes()
        )
        return ActorInput(
            scenario_id=self.scenario_id,
            node_ids=graph.node_ids,
            output_ids=graph.output_ids,
            changes=changes,
            query_budget=self.query_budget,
        )

    def validate(self, graph: ExecutionGraph) -> None:
        """Validate frozen invariants without exposing evaluator state to actors."""
        source_ids = {
            node_id
            for node_id, definition in graph.definitions.items()
            if definition.operation is Operation.SOURCE
        }
        if set(self.before_source_values) != source_ids:
            raise ValueError("FIXTURE_BEFORE_SOURCE_KEYS_MISMATCH", self.scenario_id)
        if set(self.post_source_values) != source_ids:
            raise ValueError("FIXTURE_POST_SOURCE_KEYS_MISMATCH", self.scenario_id)
        if not self.changed_source_nodes():
            raise ValueError("FIXTURE_HAS_NO_CHANGE", self.scenario_id)
        if set(self.visible_dependencies) != set(graph.node_ids):
            raise ValueError("FIXTURE_VISIBLE_NODE_KEYS_MISMATCH", self.scenario_id)
        unknown_targets = sorted(
            {
                target
                for dependencies in self.visible_dependencies.values()
                for target in dependencies
                if target not in graph.node_ids
            }
        )
        if unknown_targets:
            raise ValueError("FIXTURE_VISIBLE_TARGET_UNKNOWN", self.scenario_id, unknown_targets)
        if not 0 <= self.query_budget <= 24:
            raise ValueError("FIXTURE_QUERY_BUDGET_OUT_OF_BOUNDS", self.scenario_id)

        trace = graph.full_trace(self.before_source_values, self.post_source_values)
        before_values = trace.before.value_map()
        for output_id, expected in self.before_success_snapshot.items():
            if output_id not in graph.output_ids:
                raise ValueError("FIXTURE_SNAPSHOT_OUTPUT_UNKNOWN", self.scenario_id)
            if abs(float(expected) - before_values[output_id]) > 1e-12:
                raise ValueError("FIXTURE_BEFORE_SNAPSHOT_MISMATCH", self.scenario_id, output_id)
        if set(self.before_success_snapshot) != set(graph.output_ids):
            raise ValueError("FIXTURE_SNAPSHOT_OUTPUT_SET_MISMATCH", self.scenario_id)


def _scenario_from_dict(raw: Mapping[str, Any]) -> ScenarioFixture:
    visible = {
        str(node_id): tuple(str(target) for target in targets)
        for node_id, targets in raw["visible_dependencies"].items()
    }
    return ScenarioFixture(
        scenario_id=str(raw["scenario_id"]),
        family=str(raw["family"]),
        description=str(raw["description"]),
        before_source_values={
            str(key): float(value) for key, value in raw["before_source_values"].items()
        },
        post_source_values={
            str(key): float(value) for key, value in raw["post_source_values"].items()
        },
        before_success_snapshot={
            str(key): float(value) for key, value in raw["before_success_snapshot"].items()
        },
        visible_dependencies=visible,
        query_budget=int(raw["query_budget"]),
    )


def load_fixture_document(path: Path) -> Mapping[str, Any]:
    """Load and minimally validate a frozen fixture document."""
    with path.open("r", encoding="utf-8") as handle:
        raw = json.load(handle)
    if raw.get("schema_version") != "adaptive-revalidation-fixtures-v1":
        raise ValueError("FIXTURE_SCHEMA_VERSION_MISMATCH")
    if raw.get("status") != DEV_ONLY_STATUS:
        raise ValueError("FIXTURE_STATUS_MISMATCH")
    contract = raw.get("environment_contract", {})
    if tuple(contract.get("executable_node_ids", ())) != CHECKER_GRAPH.node_ids:
        raise ValueError("FIXTURE_NODE_CONTRACT_MISMATCH")
    if tuple(contract.get("output_ids", ())) != CHECKER_GRAPH.output_ids:
        raise ValueError("FIXTURE_OUTPUT_CONTRACT_MISMATCH")
    if tuple(contract.get("public_tools", ())) != PUBLIC_TOOL_NAMES:
        raise ValueError("FIXTURE_TOOL_CONTRACT_MISMATCH")
    if not isinstance(raw.get("scenarios"), list):
        raise ValueError("FIXTURE_SCENARIOS_NOT_LIST")
    return raw


def load_scenarios(path: Path) -> Tuple[ScenarioFixture, ...]:
    """Load and validate all frozen scenario families."""
    raw = load_fixture_document(path)
    scenarios = tuple(_scenario_from_dict(item) for item in raw["scenarios"])
    if not scenarios:
        raise ValueError("FIXTURE_SCENARIOS_EMPTY")
    ids = [scenario.scenario_id for scenario in scenarios]
    if len(set(ids)) != len(ids):
        raise ValueError("FIXTURE_SCENARIO_ID_DUPLICATE")
    families = [scenario.family for scenario in scenarios]
    required = {
        "breaking",
        "benign",
        "inactive_branch",
        "multiple_evidence",
        "value_cancellation",
        "near_additive",
        "partial_breaking",
        "missing_edge",
        "noisy_edge",
    }
    if not required <= set(families):
        raise ValueError("FIXTURE_REQUIRED_FAMILY_MISSING", sorted(required - set(families)))
    for scenario in scenarios:
        scenario.validate(CHECKER_GRAPH)
    return scenarios


def default_fixture_path() -> Path:
    """Return the package-local frozen fixture path."""
    return Path(__file__).resolve().parent / "fixtures" / "scenarios.json"


def load_frozen_scenarios() -> Tuple[ScenarioFixture, ...]:
    """Load the package-local frozen development scenarios."""
    return load_scenarios(default_fixture_path())
