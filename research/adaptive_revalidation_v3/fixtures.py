"""Frozen development fixtures and evaluator-only opaque identity mapping."""
from __future__ import annotations

from dataclasses import dataclass, replace
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Sequence, Tuple

from .actor import ActorInput, ChangeSummary, OutputId
from .model import ExecutionGraph, NodeDefinition, Operation, Value


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


def _opaque_id(prefix: str, ordinal: int) -> str:
    digest = hashlib.sha256(
        f"adaptive-revalidation-v3:{prefix}:{ordinal}".encode("ascii")
    ).hexdigest()
    return f"{prefix}{digest[:12]}"


@dataclass(frozen=True)
class ActorIdentityMap:
    """Evaluator-only deterministic mapping between semantic and actor IDs."""

    actor_scenario_id: str
    semantic_nodes: Tuple[str, ...]
    actor_nodes: Tuple[str, ...]
    semantic_outputs: Tuple[OutputId, ...]
    actor_outputs: Tuple[OutputId, ...]
    semantic_changes: Tuple[str, ...]
    actor_changes: Tuple[str, ...]
    change_nodes: Tuple[str, ...]

    def __post_init__(self) -> None:
        if len(set(self.actor_nodes)) != len(self.actor_nodes):
            raise ValueError("DUPLICATE_ACTOR_NODE_ID")
        if len(set(self.actor_outputs)) != len(self.actor_outputs):
            raise ValueError("DUPLICATE_ACTOR_OUTPUT_ID")
        if len(set(self.actor_changes)) != len(self.actor_changes):
            raise ValueError("DUPLICATE_ACTOR_CHANGE_ID")
        if len(self.semantic_nodes) != len(self.actor_nodes):
            raise ValueError("NODE_ID_MAP_SIZE_MISMATCH")
        if len(self.semantic_outputs) != len(self.actor_outputs):
            raise ValueError("OUTPUT_ID_MAP_SIZE_MISMATCH")
        if len(self.semantic_changes) != len(self.actor_changes):
            raise ValueError("CHANGE_ID_MAP_SIZE_MISMATCH")
        if len(self.semantic_changes) != len(self.change_nodes):
            raise ValueError("CHANGE_NODE_MAP_SIZE_MISMATCH")

    @property
    def semantic_to_actor_node(self) -> Mapping[str, str]:
        """Return a copied semantic-to-actor node mapping."""
        return dict(zip(self.semantic_nodes, self.actor_nodes))

    @property
    def actor_to_semantic_node(self) -> Mapping[str, str]:
        """Return a copied actor-to-semantic node mapping."""
        return dict(zip(self.actor_nodes, self.semantic_nodes))

    @property
    def semantic_to_actor_output(self) -> Mapping[OutputId, OutputId]:
        """Return a copied semantic-to-actor output mapping."""
        return dict(zip(self.semantic_outputs, self.actor_outputs))

    @property
    def actor_to_semantic_output(self) -> Mapping[OutputId, OutputId]:
        """Return a copied actor-to-semantic output mapping."""
        return dict(zip(self.actor_outputs, self.semantic_outputs))

    @property
    def actor_to_semantic_change(self) -> Mapping[str, str]:
        """Return a copied actor-to-semantic change mapping."""
        return dict(zip(self.actor_changes, self.semantic_changes))

    @property
    def actor_to_change_node(self) -> Mapping[str, str]:
        """Return a copied actor-change-to-semantic-source mapping."""
        return dict(zip(self.actor_changes, self.change_nodes))

    def actor_node(self, semantic_node: str) -> str:
        """Map one semantic node to its opaque actor identifier."""
        return self.semantic_to_actor_node[semantic_node]

    def semantic_node(self, actor_node: str) -> str:
        """Map one opaque actor node back to its semantic identifier."""
        return self.actor_to_semantic_node[actor_node]

    def actor_output(self, semantic_output: OutputId) -> OutputId:
        """Map one semantic output to its opaque actor identifier."""
        return self.semantic_to_actor_output[semantic_output]

    def semantic_output(self, actor_output: OutputId) -> OutputId:
        """Map one opaque actor output back to its semantic identifier."""
        return self.actor_to_semantic_output[actor_output]

    def semantic_change_node(self, actor_change: str) -> str:
        """Map one opaque actor change to its semantic source node."""
        return self.actor_to_change_node[actor_change]

    def actor_input(self, query_budget: int) -> ActorInput:
        """Construct value-free actor input from opaque identifiers only."""
        return ActorInput(
            scenario_id=self.actor_scenario_id,
            node_ids=self.actor_nodes,
            output_ids=self.actor_outputs,
            changes=tuple(
                ChangeSummary(
                    change_id=change_id,
                    node_id=self.actor_node(change_node),
                    change_kind="source_value",
                )
                for change_id, change_node in zip(self.actor_changes, self.change_nodes)
            ),
            query_budget=query_budget,
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
    actor_ordinal: int = 0

    def changed_source_nodes(self, graph: ExecutionGraph = CHECKER_GRAPH) -> Tuple[str, ...]:
        """Return changed source nodes in graph order, never semantic-label order."""
        source_order = tuple(
            node_id
            for node_id in graph.node_ids
            if graph.definitions[node_id].operation is Operation.SOURCE
        )
        return tuple(
            node_id
            for node_id in source_order
            if self.before_source_values[node_id] != self.post_source_values[node_id]
        )

    def identity_map(self, graph: ExecutionGraph = CHECKER_GRAPH) -> ActorIdentityMap:
        """Build a stable index-derived actor map without using semantic labels."""
        changed_nodes = self.changed_source_nodes(graph)
        return ActorIdentityMap(
            actor_scenario_id=_opaque_id("S", self.actor_ordinal),
            semantic_nodes=tuple(graph.node_ids),
            actor_nodes=tuple(
                _opaque_id("N", index) for index in range(len(graph.node_ids))
            ),
            semantic_outputs=tuple(graph.output_ids),
            actor_outputs=tuple(
                _opaque_id("O", index) for index in range(len(graph.output_ids))
            ),
            semantic_changes=changed_nodes,
            actor_changes=tuple(
                _opaque_id("C", self.actor_ordinal * 100 + index)
                for index in range(len(changed_nodes))
            ),
            change_nodes=changed_nodes,
        )

    def actor_input(
        self,
        graph: ExecutionGraph = CHECKER_GRAPH,
        query_budget: Optional[int] = None,
    ) -> ActorInput:
        """Construct the value-free actor input from stable opaque IDs."""
        identity = self.identity_map(graph)
        budget = self.query_budget if query_budget is None else query_budget
        return identity.actor_input(budget)

    def actor_visible_dependencies(
        self,
        graph: ExecutionGraph = CHECKER_GRAPH,
    ) -> Mapping[str, Tuple[str, ...]]:
        """Return authored visible dependencies using actor-only identifiers."""
        identity = self.identity_map(graph)
        return {
            identity.actor_node(node_id): tuple(
                identity.actor_node(target) for target in targets
            )
            for node_id, targets in self.visible_dependencies.items()
        }

    def validate(self, graph: ExecutionGraph = CHECKER_GRAPH) -> None:
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
        if not self.changed_source_nodes(graph):
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
        identity = self.identity_map(graph)
        identity.actor_input(self.query_budget)


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
    scenarios = tuple(
        replace(_scenario_from_dict(item), actor_ordinal=index)
        for index, item in enumerate(raw["scenarios"])
    )
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
