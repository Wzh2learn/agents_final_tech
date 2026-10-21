"""Fixed repairer that consumes policy evidence without evaluator state."""
from __future__ import annotations

from typing import Dict, Sequence, Set

from .actor import (
    ChangeEvidence,
    DependencyEvidence,
    EvidenceBundle,
    FinalAction,
    OutputAction,
    OutputId,
    RepairDecision,
    TargetTestEvidence,
)


class FixedRepairer:
    """Replay a deterministic output action from evidence bundles alone.

    The constructor intentionally accepts no scenario, graph, Gold set, trace,
    or evaluator handle. Every decision below is derived from ``EvidenceBundle``.
    """

    def repair(self, bundle: EvidenceBundle) -> FinalAction:
        """Return keep/recompute/abstain decisions for all actor-visible outputs."""
        actor_input = bundle.actor_input
        changes = actor_input.changes
        change_evidence: Dict[str, ChangeEvidence] = {}
        dependency_evidence: Dict[str, DependencyEvidence] = {}
        tests: Dict[OutputId, TargetTestEvidence] = {}

        for record in bundle.records:
            if isinstance(record, ChangeEvidence):
                change_evidence[record.change_id] = record
            elif isinstance(record, DependencyEvidence):
                dependency_evidence[record.node_id] = record
            elif isinstance(record, TargetTestEvidence):
                tests[record.output_id] = record

        inspected_changes = {
            change.change_id for change in changes if change.change_id in change_evidence
        }
        all_changes_inspected = len(inspected_changes) == len(changes)
        all_changes_zero = all_changes_inspected and all(
            change_evidence[change.change_id].result_key == "no_delta"
            for change in changes
        )

        actions = []
        for output_id in actor_input.output_ids:
            test = tests.get(output_id)
            if test is not None and not test.passed:
                decision = RepairDecision.RECOMPUTE
            elif test is not None and test.passed:
                decision = RepairDecision.KEEP
            elif all_changes_zero:
                decision = RepairDecision.KEEP
            else:
                supporting_changes: Set[str] = set()
                complete_negative_evidence = True
                positive_change_seen = False
                for change in changes:
                    inspected = change_evidence.get(change.change_id)
                    if inspected is not None and inspected.result_key == "delta":
                        positive_change_seen = True
                    dependency = dependency_evidence.get(change.node_id)
                    if dependency is None:
                        complete_negative_evidence = False
                        continue
                    if output_id in dependency.reachable_outputs:
                        supporting_changes.add(change.change_id)
                if supporting_changes:
                    decision = RepairDecision.RECOMPUTE
                elif complete_negative_evidence and (
                    positive_change_seen or all_changes_inspected
                ):
                    decision = RepairDecision.KEEP
                else:
                    decision = RepairDecision.ABSTAIN
            actions.append(OutputAction(output_id=output_id, decision=decision))
        return FinalAction(tuple(actions))


def decisions_from_mapping(
    output_ids: Sequence[OutputId],
    decisions: Dict[OutputId, RepairDecision],
) -> FinalAction:
    """Build a complete action from a mapping while preserving output order."""
    if set(decisions) != set(output_ids):
        raise ValueError("ACTION_OUTPUT_SET_MISMATCH")
    return FinalAction(
        tuple(OutputAction(output_id, decisions[output_id]) for output_id in output_ids)
    )
