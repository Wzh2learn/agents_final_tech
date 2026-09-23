#!/usr/bin/env python3
"""Deterministic seven-arm rule-gate replay for the Phase 2 software contract.

The runner is deliberately corpus-agnostic and offline.  It consumes a compact
table/alias contract, re-evaluates every candidate against each arm's own rule
state, and emits aggregate events only.  A report is never a training permit or
paper result; an independently reviewed GB10 run must accept it separately.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


CONTRACT_VERSION = "phase2-rule-gate-replay-v2"
REPORT_VERSION = "phase2-rule-gate-report-v2"
ARMS = (
    "no_gate",
    "gain_only",
    "collateral_only",
    "confidence_only",
    "fixed_dual_gate",
    "independent_gate_validation",
    "rollback_versioning",
)
ALLOWED_LAYERS = {"proposal_train", "gate_validation"}
CONFIDENCE_VALUES = {"high", "medium", "low", None}
DECISIONS = {"accept", "reject", "unmeasurable"}


def _stable_bytes(value: object) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            allow_nan=False,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _finite(value: object, *, minimum: float, maximum: float) -> bool:
    return (
        type(value) in (int, float)
        and math.isfinite(float(value))
        and minimum <= float(value) <= maximum
    )


def _exact_keys(value: dict[str, object], expected: set[str], source: str) -> None:
    unknown = sorted(set(value) - expected)
    missing = sorted(expected - set(value))
    if unknown:
        raise ValueError(f"unknown {source} fields: {unknown}")
    if missing:
        raise ValueError(f"missing {source} fields: {missing}")


def _norm(value: str) -> str:
    return "".join(char for char in value.casefold() if char.isalnum())


@dataclass(frozen=True)
class Observation:
    observed: str
    gold_target: str


@dataclass(frozen=True)
class TableCase:
    uid: str
    family: str
    layer: str
    observations: tuple[Observation, ...]


@dataclass(frozen=True)
class Candidate:
    candidate_id: str
    source_uid: str
    synonym: str
    target: str
    confidence: str | None


@dataclass(frozen=True)
class Score:
    correct: int
    harmful: int
    covered: int
    total: int

    @property
    def utility(self) -> float:
        return (self.correct - self.harmful) / self.total if self.total else 0.0

    @property
    def accuracy(self) -> float | None:
        return self.correct / self.covered if self.covered else None

    @property
    def coverage(self) -> float:
        return self.covered / self.total if self.total else 0.0


Rules = dict[str, list[str]]


def _validate_dataset(value: object) -> tuple[list[TableCase], list[Candidate], Rules]:
    if not isinstance(value, dict):
        raise ValueError("dataset must be a JSON object")
    _exact_keys(
        value,
        {"contract_version", "dataset_id", "tables", "candidates", "initial_rules"},
        "dataset",
    )
    if value["contract_version"] != CONTRACT_VERSION:
        raise ValueError("unsupported Phase 2 dataset contract_version")
    if not isinstance(value["dataset_id"], str) or not value["dataset_id"]:
        raise ValueError("dataset_id must be a non-empty string")

    raw_tables = value["tables"]
    if not isinstance(raw_tables, list) or not raw_tables:
        raise ValueError("tables must be a non-empty list")
    tables: list[TableCase] = []
    seen_uids: set[str] = set()
    for index, raw in enumerate(raw_tables):
        if not isinstance(raw, dict):
            raise ValueError(f"table {index} must be an object")
        _exact_keys(raw, {"uid", "family", "layer", "observations"}, f"table {index}")
        uid, family, layer = raw["uid"], raw["family"], raw["layer"]
        if not all(isinstance(item, str) and item for item in (uid, family, layer)):
            raise ValueError(f"table {index} identifiers must be non-empty strings")
        if uid in seen_uids:
            raise ValueError(f"duplicate table uid: {uid}")
        if layer not in ALLOWED_LAYERS:
            raise ValueError(f"forbidden or unknown data layer: {layer}")
        raw_observations = raw["observations"]
        if not isinstance(raw_observations, list) or not raw_observations:
            raise ValueError(f"table {uid} observations must be non-empty")
        observations: list[Observation] = []
        for obs_index, observation in enumerate(raw_observations):
            if not isinstance(observation, dict):
                raise ValueError(f"table {uid} observation {obs_index} must be an object")
            _exact_keys(observation, {"observed", "gold_target"}, "observation")
            if not all(
                isinstance(observation[field], str) and observation[field]
                for field in ("observed", "gold_target")
            ):
                raise ValueError("observed and gold_target must be non-empty strings")
            observations.append(Observation(observation["observed"], observation["gold_target"]))
        tables.append(TableCase(uid, family, layer, tuple(observations)))
        seen_uids.add(uid)

    raw_candidates = value["candidates"]
    if not isinstance(raw_candidates, list) or not raw_candidates:
        raise ValueError("candidates must be a non-empty ordered list")
    candidates: list[Candidate] = []
    seen_candidate_ids: set[str] = set()
    proposal_uids = {table.uid for table in tables if table.layer == "proposal_train"}
    for index, raw in enumerate(raw_candidates):
        if not isinstance(raw, dict):
            raise ValueError(f"candidate {index} must be an object")
        _exact_keys(
            raw,
            {"candidate_id", "source_uid", "synonym", "target", "confidence"},
            f"candidate {index}",
        )
        candidate_id, source_uid = raw["candidate_id"], raw["source_uid"]
        synonym, target, confidence = raw["synonym"], raw["target"], raw["confidence"]
        if not all(
            isinstance(item, str) and item
            for item in (candidate_id, source_uid, synonym, target)
        ):
            raise ValueError(f"candidate {index} identifiers and rule fields must be non-empty")
        if candidate_id in seen_candidate_ids:
            raise ValueError(f"duplicate candidate_id: {candidate_id}")
        if source_uid not in proposal_uids:
            raise ValueError("candidate source_uid must belong to proposal_train")
        if confidence not in CONFIDENCE_VALUES:
            raise ValueError("confidence must be high, medium, low, or null")
        candidates.append(Candidate(candidate_id, source_uid, synonym, target, confidence))
        seen_candidate_ids.add(candidate_id)

    raw_rules = value["initial_rules"]
    if not isinstance(raw_rules, dict):
        raise ValueError("initial_rules must be an object")
    rules: Rules = {}
    for target, synonyms in sorted(raw_rules.items()):
        if not isinstance(target, str) or not target:
            raise ValueError("initial rule targets must be non-empty strings")
        if not isinstance(synonyms, list) or any(
            not isinstance(synonym, str) or not synonym for synonym in synonyms
        ):
            raise ValueError("initial rule synonyms must be non-empty string lists")
        rules[target] = sorted(set(synonyms), key=lambda item: (_norm(item), item))
    return tables, candidates, rules


def _validate_config(value: object) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError("config must be a JSON object")
    _exact_keys(
        value,
        {
            "contract_version",
            "min_source_gain",
            "max_collateral_loss",
            "max_gate_loss",
            "rollback_budget",
            "significance_level",
            "confidence_policy",
            "cost_proxy",
        },
        "config",
    )
    if value["contract_version"] != CONTRACT_VERSION:
        raise ValueError("unsupported Phase 2 config contract_version")
    for field in (
        "min_source_gain",
        "max_collateral_loss",
        "max_gate_loss",
        "rollback_budget",
    ):
        if not _finite(value[field], minimum=0.0, maximum=2.0):
            raise ValueError(f"{field} must be finite and within [0, 2]")
    if not _finite(value["significance_level"], minimum=1e-9, maximum=0.5):
        raise ValueError("significance_level must be finite and within [1e-9, 0.5]")
    confidence = value["confidence_policy"]
    if not isinstance(confidence, dict):
        raise ValueError("confidence_policy must be an object")
    _exact_keys(confidence, {"high", "medium", "low", "missing"}, "confidence_policy")
    if any(decision not in DECISIONS for decision in confidence.values()):
        raise ValueError("confidence_policy values must be accept, reject, or unmeasurable")
    if confidence["missing"] != "unmeasurable":
        raise ValueError("missing confidence must remain unmeasurable")
    cost = value["cost_proxy"]
    if not isinstance(cost, dict):
        raise ValueError("cost_proxy must be an object")
    _exact_keys(cost, {"source", "collateral", "gate", "snapshot"}, "cost_proxy")
    for name, weight in cost.items():
        if not _finite(weight, minimum=0.0, maximum=1_000_000.0):
            raise ValueError(f"cost_proxy.{name} must be finite and non-negative")
    return value


def _predict(observed: str, gold_target: str, rules: Rules) -> str | None:
    observed_key = _norm(observed)
    if observed_key == _norm(gold_target):
        return gold_target
    targets = {
        target
        for target, synonyms in rules.items()
        if any(observed_key == _norm(synonym) for synonym in synonyms)
    }
    return next(iter(targets)) if len(targets) == 1 else None


def _score_table(table: TableCase, rules: Rules) -> Score:
    correct = harmful = covered = 0
    for observation in table.observations:
        predicted = _predict(observation.observed, observation.gold_target, rules)
        if predicted is not None:
            covered += 1
            if _norm(predicted) == _norm(observation.gold_target):
                correct += 1
            else:
                harmful += 1
    return Score(correct, harmful, covered, len(table.observations))


def _pool_score(tables: Iterable[TableCase], rules: Rules) -> Score:
    scores = [_score_table(table, rules) for table in tables]
    return Score(
        sum(score.correct for score in scores),
        sum(score.harmful for score in scores),
        sum(score.covered for score in scores),
        sum(score.total for score in scores),
    )


def _add_rule(rules: Rules, candidate: Candidate) -> Rules:
    updated = copy.deepcopy(rules)
    synonyms = updated.setdefault(candidate.target, [])
    if all(_norm(existing) != _norm(candidate.synonym) for existing in synonyms):
        synonyms.append(candidate.synonym)
        synonyms.sort(key=lambda item: (_norm(item), item))
    return updated


def _delta(tables: Iterable[TableCase], before: Rules, after: Rules) -> float:
    selected = tuple(tables)
    return _pool_score(selected, after).utility - _pool_score(selected, before).utility


def _candidate_is_valid(candidate: Candidate, tables: Iterable[TableCase]) -> bool:
    matching_targets = {
        _norm(observation.gold_target)
        for table in tables
        for observation in table.observations
        if _norm(observation.observed) == _norm(candidate.synonym)
    }
    return bool(matching_targets) and matching_targets == {_norm(candidate.target)}


def _arm_decision(
    arm: str,
    candidate: Candidate,
    source_gain: float,
    collateral: float,
    gate_delta: float,
    config: dict[str, object],
) -> str:
    min_gain = float(config["min_source_gain"])
    max_collateral = float(config["max_collateral_loss"])
    max_gate = float(config["max_gate_loss"])
    confidence_policy = config["confidence_policy"]
    assert isinstance(confidence_policy, dict)
    if arm == "no_gate":
        return "accept"
    if arm == "gain_only":
        return "accept" if source_gain >= min_gain else "reject"
    if arm == "collateral_only":
        return "accept" if collateral >= -max_collateral else "reject"
    if arm == "confidence_only":
        return str(confidence_policy[candidate.confidence or "missing"])
    fixed = source_gain >= min_gain and collateral >= -max_collateral
    if arm == "fixed_dual_gate":
        return "accept" if fixed else "reject"
    if arm in {"independent_gate_validation", "rollback_versioning"}:
        return "accept" if fixed and gate_delta >= -max_gate else "reject"
    raise ValueError(f"unknown arm: {arm}")


def _final_metrics(
    tables: list[TableCase],
    rules: Rules,
    accepted: set[str],
    retained: set[str],
    candidates: list[Candidate],
    significance_level: float,
) -> dict[str, object]:
    gate_tables = [table for table in tables if table.layer == "gate_validation"]
    overall = _pool_score(gate_tables, rules)
    families: dict[str, list[TableCase]] = {}
    for table in gate_tables:
        families.setdefault(table.family, []).append(table)
    family_rows = {
        family: {
            "utility": round(_pool_score(rows, rules).utility, 8),
            "accuracy": _round_optional(_pool_score(rows, rules).accuracy),
            "coverage": round(_pool_score(rows, rules).coverage, 8),
            "tables": len(rows),
        }
        for family, rows in sorted(families.items())
    }
    valid = {
        candidate.candidate_id
        for candidate in candidates
        if _candidate_is_valid(candidate, tables)
    }
    harmful_retained = retained - valid
    harmful_accepted = accepted - valid
    candidate_by_id = {candidate.candidate_id: candidate for candidate in candidates}
    evaluated_uids = {candidate.source_uid for candidate in candidates}
    harmful_uids = {
        candidate_by_id[candidate_id].source_uid for candidate_id in harmful_accepted
    }
    return {
        "gate_utility": round(overall.utility, 8),
        "gate_accuracy": _round_optional(overall.accuracy),
        "gate_coverage": round(overall.coverage, 8),
        "valid_rule_retention": round(len(retained & valid) / len(valid), 8) if valid else None,
        "rule_level_harmful_accept_rate": (
            round(len(harmful_accepted) / len(accepted), 8) if accepted else None
        ),
        "rule_level_harmful_retained_rate": (
            round(len(harmful_retained) / len(retained), 8) if retained else None
        ),
        "uid_any_harm_rate": (
            round(len(harmful_uids) / len(evaluated_uids), 8) if evaluated_uids else None
        ),
        "uid_any_harm_cp_upper": _clopper_pearson_upper(
            len(harmful_uids), len(evaluated_uids), significance_level
        ),
        "uid_any_harm_significance_level": significance_level,
        "uid_any_harm_counts": {
            "harmful_uids": len(harmful_uids),
            "evaluated_uids": len(evaluated_uids),
        },
        "retained_rules": len(retained),
        "valid_candidates": len(valid),
        "worst_family": min(
            family_rows,
            key=lambda name: (family_rows[name]["utility"], name),
        ) if family_rows else None,
        "families": family_rows,
    }


def _round_optional(value: float | None) -> float | None:
    return round(value, 8) if value is not None else None


def _binomial_cdf(k: int, n: int, probability: float) -> float:
    return sum(
        math.comb(n, index)
        * probability ** index
        * (1.0 - probability) ** (n - index)
        for index in range(k + 1)
    )


def _clopper_pearson_upper(k: int, n: int, significance_level: float) -> float | None:
    """One-sided exact upper bound for a binomial proportion."""

    if n <= 0:
        return None
    if k >= n:
        return 1.0
    lower, upper = 0.0, 1.0
    for _ in range(80):
        midpoint = (lower + upper) / 2.0
        if _binomial_cdf(k, n, midpoint) > significance_level:
            lower = midpoint
        else:
            upper = midpoint
    return round(upper, 8)


def _cost_for_arm(arm: str, n_proposal_other: int, n_gate: int, config: dict[str, object]) -> float:
    cost = config["cost_proxy"]
    assert isinstance(cost, dict)
    source = 2.0 * float(cost["source"])
    collateral = 2.0 * n_proposal_other * float(cost["collateral"])
    gate = 2.0 * n_gate * float(cost["gate"])
    if arm == "no_gate" or arm == "confidence_only":
        return 0.0
    if arm == "gain_only":
        return source
    if arm == "collateral_only":
        return collateral
    if arm == "fixed_dual_gate":
        return source + collateral
    return source + collateral + gate


def _run_arm(
    arm: str,
    tables: list[TableCase],
    candidates: list[Candidate],
    initial_rules: Rules,
    config: dict[str, object],
) -> dict[str, object]:
    proposal = [table for table in tables if table.layer == "proposal_train"]
    gate = [table for table in tables if table.layer == "gate_validation"]
    by_uid = {table.uid: table for table in tables}
    rules = copy.deepcopy(initial_rules)
    accepted_ids: set[str] = set()
    retained: set[str] = set()
    events: list[dict[str, object]] = []
    validations = rollbacks = 0
    cumulative_cost = 0.0
    best_gate_score = _pool_score(gate, rules).utility
    best_snapshot = (copy.deepcopy(rules), set(retained), best_gate_score)
    valid_ids = {
        candidate.candidate_id
        for candidate in candidates
        if _candidate_is_valid(candidate, tables)
    }

    for step, candidate in enumerate(candidates, start=1):
        proposed_rules = _add_rule(rules, candidate)
        source = by_uid[candidate.source_uid]
        collateral_tables = [table for table in proposal if table.uid != source.uid]
        source_gain = _delta([source], rules, proposed_rules)
        collateral = _delta(collateral_tables, rules, proposed_rules)
        gate_delta = _delta(gate, rules, proposed_rules)
        decision = _arm_decision(
            arm, candidate, source_gain, collateral, gate_delta, config
        )
        accepted = decision == "accept"
        rolled_back = False
        if accepted:
            accepted_ids.add(candidate.candidate_id)
            rules = proposed_rules
            retained.add(candidate.candidate_id)

        n_other = len(collateral_tables)
        step_cost = _cost_for_arm(arm, n_other, len(gate), config)
        if arm in {"independent_gate_validation", "rollback_versioning"}:
            validations += 1
        if arm == "rollback_versioning" and accepted:
            step_cost += len(gate) * float(config["cost_proxy"]["snapshot"])
            current_gate_score = _pool_score(gate, rules).utility
            if current_gate_score >= best_gate_score:
                best_gate_score = current_gate_score
                best_snapshot = (copy.deepcopy(rules), set(retained), best_gate_score)
            elif current_gate_score < best_gate_score - float(config["rollback_budget"]):
                rules, retained, best_gate_score = copy.deepcopy(best_snapshot)
                rollbacks += 1
                rolled_back = True
        cumulative_cost += step_cost
        events.append({
            "step": step,
            "decision": decision,
            "accepted": accepted,
            "retained_after_step": candidate.candidate_id in retained,
            "rolled_back": rolled_back,
            "source_gain": round(source_gain, 8),
            "collateral": round(collateral, 8),
            "gate_delta": round(gate_delta, 8),
            "retained_rules": len(retained),
            "retained_valid_rules": len(retained & valid_ids),
            "retained_harmful_rules": len(retained - valid_ids),
            "cumulative_rollbacks": rollbacks,
            "cumulative_cost_proxy": round(cumulative_cost, 8),
        })

    return {
        "events": events,
        "metrics": {
            **_final_metrics(
                tables,
                rules,
                accepted_ids,
                retained,
                candidates,
                float(config["significance_level"]),
            ),
            "validation_queries": validations,
            "rollbacks": rollbacks,
            "cumulative_cost_proxy": round(cumulative_cost, 8),
        },
        "final_state_sha256": _sha256_bytes(_stable_bytes(rules)),
        "processed_order_sha256": _sha256_bytes(
            _stable_bytes([candidate.candidate_id for candidate in candidates])
        ),
    }


def run_replay(dataset: object, config: object) -> dict[str, object]:
    """Validate inputs and replay all seven arms without network or row-level output."""
    tables, candidates, initial_rules = _validate_dataset(dataset)
    validated_config = _validate_config(config)
    if not any(table.layer == "proposal_train" for table in tables):
        raise ValueError("proposal_train tables are required")
    if not any(table.layer == "gate_validation" for table in tables):
        raise ValueError("independent gate_validation tables are required")
    order = [candidate.candidate_id for candidate in candidates]
    report = {
        "meta": {
            "contract_version": REPORT_VERSION,
            "evidence_level": "SOFTWARE_CONTRACT_ONLY",
            "paper_result": False,
            "training_authorized": False,
            "endpoint_calls": 0,
            "socket_attempts": 0,
            "arms": list(ARMS),
        },
        "hashes": {
            "dataset_sha256": _sha256_bytes(_stable_bytes(dataset)),
            "config_sha256": _sha256_bytes(_stable_bytes(config)),
            "candidate_order_sha256": _sha256_bytes(_stable_bytes(order)),
            "implementation_sha256": _sha256_bytes(Path(__file__).read_bytes()),
        },
        "support": {
            "proposal_tables": sum(table.layer == "proposal_train" for table in tables),
            "gate_validation_tables": sum(table.layer == "gate_validation" for table in tables),
            "candidates": len(candidates),
        },
        "arms": {
            arm: _run_arm(arm, tables, candidates, initial_rules, validated_config)
            for arm in ARMS
        },
    }
    expected_order = report["hashes"]["candidate_order_sha256"]
    if any(
        arm_report["processed_order_sha256"] != expected_order
        for arm_report in report["arms"].values()
    ):
        raise AssertionError("an arm did not consume the shared candidate order")
    return report


def _read_json(path: Path, source: str) -> object:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read strict JSON {source}") from exc


def _write_new(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("xb") as handle:
            handle.write(_stable_bytes(value))
    except FileExistsError as exc:
        raise ValueError("refusing to overwrite an existing Phase 2 report") from exc


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", required=True, type=Path)
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    report = run_replay(
        _read_json(args.dataset, "dataset"),
        _read_json(args.config, "config"),
    )
    _write_new(args.output, report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
