from __future__ import annotations

import hashlib
import json
import math
import random
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable, Sequence


EVIDENCE_CLASS = "ENGINEERING / DEV_ONLY"
RECEIPT_LABEL = "ALGORITHM_SMOKE_DEV_ONLY"
SPLIT_LABEL = "DEV_ONLY_PSEUDO_FOLD"
TERMINAL_STATUS = "NOT_AVAILABLE"
EXPECTED_ROWS = 216
EXPECTED_RESPONSE_FIELDS = 12
EXPECTED_CHECKPOINTS = 12
RANDOM_SEED = 20261011
SPLIT_SEED = 20261011
TEST_FRACTION = 0.2
SMOKE_BUDGETS = ((4, 0), (8, 2))
TIE_EPSILON = 1e-12

EXPECTED_INPUT_HASHES = {
    "research/causal_checkpoint_selection_mvp_20261011/METHOD_DESIGN_QUALIFICATION_V1.md": "bcd83b665b19465e7757164cbac071a40c43afd28c1b541fa6f2eb0f6fd301a3",
    "config/eval_checkpoint_trees.json": "0931d952e40e80a930a335a3ac7180f35812000248c4f23a5f71e5a9b316bf25",
    "research/stage_e_multileaf_20261010/results/multileaf_prediction_rows.jsonl": "37bb360133e4c85129a13f9d56db04d57ec2202ad0409491c20f79bd892afa06",
    "research/stage_e_multileaf_20261010/results/multileaf_paired_artifacts.jsonl": "39c3a2c5c37949928b1250ec41ddf04059524853032dff2173cebec36265e53f",
}

DIRECT_TARGETS = {
    "M": "parse.field.hit_rate",
    "R": "qa.retrieval.source_required",
    "N": "parse.reconcile.equations",
}

POTENTIAL_DOWNSTREAM = {
    "M": ("parse.table.regression",),
    "R": ("qa.numeric.number_grounding", "qa.faithfulness.judge"),
    "N": ("qa.numeric.exact", "qa.numeric.number_grounding"),
}

MANUAL_PRIORITY = (
    "parse.field.hit_rate",
    "qa.retrieval.source_required",
    "parse.reconcile.equations",
    "parse.table.regression",
    "qa.numeric.number_grounding",
    "qa.faithfulness.judge",
    "qa.numeric.exact",
    "qa.numeric.number_grounding",
)

METRIC_FIELDS = (
    "failure_coverage",
    "source_local_coverage",
    "downstream_causal_coverage",
    "source_local_only_coverage",
    "stage_macro_f1",
    "family_macro_f1",
    "diagnosability_macro_f1",
)

BASELINE_IDS = (
    "all-checkpoints",
    "random-K",
    "manual/default stage-aligned",
    "coverage-only greedy",
    "ours",
    "terminal-only",
)

REQUIRED_RESULT_FIELDS = (
    "schema_version",
    "evidence_class",
    "receipt_label",
    "scientific_claim",
    "formal_experiment",
    "input_shape",
    "mechanism_holdout",
    "split",
    "checkpoint_inventory",
    "budget_results",
    "required_fields_present",
)

REQUIRED_SELECTION_FIELDS = (
    "baseline_id",
    "status",
    "availability",
    "reason",
    "selected_ids",
    "selected_checkpoint_count",
    "budget_usage",
    "response_counts",
    "metrics",
)


class BudgetExceededError(ValueError):
    pass


@dataclass(frozen=True)
class Checkpoint:
    checkpoint_id: str
    family: str
    check_count: int
    model_or_judge_calls: int
    measured_runtime_ms: float | None


@dataclass(frozen=True)
class Budget:
    check_budget: int
    call_budget: int


@dataclass(frozen=True)
class Selection:
    status: str
    selected_ids: tuple[str, ...]
    reason: str = ""


def repository_root(start: Path | None = None) -> Path:
    current = (start or Path(__file__)).resolve()
    if current.is_file():
        current = current.parent
    for candidate in (current, *current.parents):
        if (candidate / "config" / "eval_checkpoint_trees.json").is_file():
            return candidate
    raise FileNotFoundError("repository root containing config/eval_checkpoint_trees.json not found")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def load_config(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def checkpoint_inventory(config: dict[str, Any]) -> list[Checkpoint]:
    checkpoints: list[Checkpoint] = []

    def visit(node: dict[str, Any]) -> None:
        children = node.get("children") or []
        if not children:
            checkpoint_id = str(node["id"])
            checkpoints.append(
                Checkpoint(
                    checkpoint_id=checkpoint_id,
                    family=checkpoint_id.split(".", 1)[0],
                    check_count=1,
                    model_or_judge_calls=1 if checkpoint_id.endswith(".judge") else 0,
                    measured_runtime_ms=None,
                )
            )
            return
        for child in children:
            visit(child)

    for tree in config["trees"]:
        visit(tree)
    return checkpoints


def validate_inputs(
    rows: Sequence[dict[str, Any]],
    paired_rows: Sequence[dict[str, Any]],
    inventory: Sequence[Checkpoint],
) -> dict[str, Any]:
    if len(rows) != EXPECTED_ROWS or len(paired_rows) != EXPECTED_ROWS:
        raise ValueError(
            f"old matrix shape mismatch: rows={len(rows)}, paired_rows={len(paired_rows)}"
        )
    if len({row["sample_id"] for row in rows}) != EXPECTED_ROWS:
        raise ValueError("sample_id values are not unique")
    response_fields = tuple(sorted(rows[0]["response_vector"]))
    inventory_ids = tuple(sorted(item.checkpoint_id for item in inventory))
    if len(response_fields) != EXPECTED_RESPONSE_FIELDS:
        raise ValueError(f"response field count mismatch: {len(response_fields)}")
    if response_fields != inventory_ids:
        raise ValueError("response fields do not exactly match checkpoint inventory")
    for row, paired in zip(rows, paired_rows, strict=True):
        if row["sample_id"] != paired["sample_id"]:
            raise ValueError("prediction/paired sample order mismatch")
        if row["cluster_id"] != paired["cluster_id"]:
            raise ValueError("prediction/paired cluster mismatch")
        if row["response_vector"] != paired["response_vector"]:
            raise ValueError("prediction/paired response mismatch")
        if row["true_stage"] != paired["stage"]:
            raise ValueError("prediction/paired stage mismatch")
        if sorted(row["response_vector"]) != list(response_fields):
            raise ValueError("response schema drift within matrix")
    return {
        "rows": len(rows),
        "response_fields": len(response_fields),
        "response_field_ids": list(response_fields),
        "checkpoint_count": len(inventory),
        "shape_status": "PASS_216_X_12",
    }


def authoritative_paths(root: Path | None = None) -> dict[str, Path]:
    base = root or repository_root()
    return {
        "research/causal_checkpoint_selection_mvp_20261011/METHOD_DESIGN_QUALIFICATION_V1.md": base
        / "research/causal_checkpoint_selection_mvp_20261011/METHOD_DESIGN_QUALIFICATION_V1.md",
        "config/eval_checkpoint_trees.json": base / "config/eval_checkpoint_trees.json",
        "research/stage_e_multileaf_20261010/results/multileaf_prediction_rows.jsonl": base
        / "research/stage_e_multileaf_20261010/results/multileaf_prediction_rows.jsonl",
        "research/stage_e_multileaf_20261010/results/multileaf_paired_artifacts.jsonl": base
        / "research/stage_e_multileaf_20261010/results/multileaf_paired_artifacts.jsonl",
    }


def validate_input_hashes(root: Path | None = None) -> dict[str, str]:
    observed = {
        relative: sha256_file(path)
        for relative, path in authoritative_paths(root).items()
    }
    if observed != EXPECTED_INPUT_HASHES:
        raise ValueError("frozen input hash mismatch")
    return observed


def load_authoritative_inputs(root: Path | None = None) -> tuple[
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[Checkpoint],
    dict[str, str],
    dict[str, Any],
]:
    base = root or repository_root()
    hashes = validate_input_hashes(base)
    paths = authoritative_paths(base)
    config = load_config(paths["config/eval_checkpoint_trees.json"])
    inventory = checkpoint_inventory(config)
    if len(inventory) != EXPECTED_CHECKPOINTS:
        raise ValueError(f"checkpoint inventory mismatch: {len(inventory)}")
    rows = load_jsonl(
        paths["research/stage_e_multileaf_20261010/results/multileaf_prediction_rows.jsonl"]
    )
    paired_rows = load_jsonl(
        paths[
            "research/stage_e_multileaf_20261010/results/multileaf_paired_artifacts.jsonl"
        ]
    )
    shape = validate_inputs(rows, paired_rows, inventory)
    return rows, paired_rows, inventory, hashes, shape


def build_dev_only_overlay(row: dict[str, Any]) -> dict[str, Any]:
    stage = str(row["true_stage"])
    if stage not in DIRECT_TARGETS:
        raise ValueError(f"unsupported stage in DEV_ONLY overlay: {stage}")
    responses = {key: int(value) for key, value in row["response_vector"].items()}
    direct = DIRECT_TARGETS[stage]
    downstream = POTENTIAL_DOWNSTREAM[stage]
    if direct not in responses or any(leaf not in responses for leaf in downstream):
        raise ValueError("overlay target absent from response schema")
    source_local = responses[direct] > 0
    downstream_causal = any(responses[leaf] > 0 for leaf in downstream)
    candidate_leaves = {direct, *downstream}
    roles: dict[str, str] = {}
    ripr_flags: dict[str, dict[str, int]] = {}
    for leaf, response in responses.items():
        if leaf == direct and response > 0:
            role = "SOURCE_LOCAL_RESPONSE"
        elif leaf in downstream and response > 0:
            role = "DOWNSTREAM_CAUSAL_RESPONSE"
        elif response > 0:
            role = "UNCLASSIFIED_DEV_ONLY_RESPONSE"
        else:
            role = "NO_RESPONSE"
        roles[leaf] = role
        ripr_flags[leaf] = {
            "REACHED": int(leaf in candidate_leaves),
            "INFECTED": int(leaf == direct and source_local),
            "PROPAGATED": int(leaf in downstream and downstream_causal),
            "REVEALED": int(response > 0),
        }
    return {
        "overlay_label": "DEV_ONLY_RESPONSE_ROLE_AND_RIPR_PLUMBING_OVERLAY",
        "SOURCE_LOCAL_RESPONSE": source_local,
        "DOWNSTREAM_CAUSAL_RESPONSE": downstream_causal,
        "source_local_response": source_local,
        "downstream_causal_response": downstream_causal,
        "direct_target_leaf": direct,
        "potential_downstream_leaves": list(downstream),
        "checkpoint_roles": roles,
        "ripr_flags": ripr_flags,
        "raw_state_pre_hash": "NOT_IDENTIFIABLE",
        "raw_state_post_hash": "NOT_IDENTIFIABLE",
        "dependency_path_status": "DEV_ONLY_DESIGN_PATH_PRESENT_NO_RAW_STATE_PROOF",
        "family_label": direct.split(".", 1)[0],
        "family_label_definition": "DEV_ONLY_DIRECT_TARGET_CONFIG_TOP_TREE_FAMILY",
    }


def apply_dev_only_overlay(rows: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    augmented: list[dict[str, Any]] = []
    for row in rows:
        copied = dict(row)
        copied["dev_only_overlay"] = build_dev_only_overlay(row)
        copied["stage_label"] = str(row["true_stage"])
        copied["family_label"] = copied["dev_only_overlay"]["family_label"]
        augmented.append(copied)
    return augmented


def hard_budget_enforced(
    selected_ids: Iterable[str],
    budget: Budget,
    inventory: Sequence[Checkpoint],
) -> bool:
    costs = {item.checkpoint_id: item for item in inventory}
    selected = list(selected_ids)
    if len(selected) != len(set(selected)):
        raise BudgetExceededError("duplicate checkpoint selection")
    try:
        check_count = sum(costs[item].check_count for item in selected)
        calls = sum(costs[item].model_or_judge_calls for item in selected)
    except KeyError as exc:
        raise BudgetExceededError(f"unknown checkpoint in selection: {exc.args[0]}") from exc
    return check_count <= budget.check_budget and calls <= budget.call_budget


def assert_hard_budget(
    selected_ids: Iterable[str],
    budget: Budget,
    inventory: Sequence[Checkpoint],
) -> dict[str, int | bool]:
    costs = {item.checkpoint_id: item for item in inventory}
    selected = list(selected_ids)
    if len(selected) != len(set(selected)):
        raise BudgetExceededError("duplicate checkpoint selection")
    try:
        check_count = sum(costs[item].check_count for item in selected)
        calls = sum(costs[item].model_or_judge_calls for item in selected)
    except KeyError as exc:
        raise BudgetExceededError(f"unknown checkpoint in selection: {exc.args[0]}") from exc
    within = check_count <= budget.check_budget and calls <= budget.call_budget
    if not within:
        raise BudgetExceededError(
            f"hard budget exceeded: check={check_count}/{budget.check_budget}, "
            f"calls={calls}/{budget.call_budget}"
        )
    return {
        "check_count": check_count,
        "B_check": budget.check_budget,
        "check_headroom": budget.check_budget - check_count,
        "model_or_judge_calls": calls,
        "B_call": budget.call_budget,
        "call_headroom": budget.call_budget - calls,
        "within_hard_budgets": within,
    }


def make_selection(
    status: str,
    selected_ids: Sequence[str],
    budget: Budget,
    inventory: Sequence[Checkpoint],
    reason: str = "",
) -> Selection:
    if status != TERMINAL_STATUS:
        assert_hard_budget(selected_ids, budget, inventory)
    return Selection(status=status, selected_ids=tuple(selected_ids), reason=reason)


def all_checkpoints(
    inventory: Sequence[Checkpoint],
    budget: Budget,
) -> Selection:
    selected = [item.checkpoint_id for item in inventory]
    if not hard_budget_enforced(selected, budget, inventory):
        required = assert_hard_budget(
            [],
            Budget(
                check_budget=sum(item.check_count for item in inventory),
                call_budget=sum(item.model_or_judge_calls for item in inventory),
            ),
            inventory,
        )
        return make_selection(
            TERMINAL_STATUS,
            (),
            budget,
            inventory,
            reason=(
                "ALL_CHECKPOINTS_BUDGET_INFEASIBLE: "
                f"required_check={required['check_count']}, "
                f"required_calls={required['model_or_judge_calls']}"
            ),
        )
    return make_selection("AVAILABLE", selected, budget, inventory)


def random_k_select(
    inventory: Sequence[Checkpoint],
    budget: Budget,
    k: int,
    seed: int = RANDOM_SEED,
) -> Selection:
    if k < 0:
        raise ValueError("k must be non-negative")
    rng = random.Random(seed)
    ordered = list(inventory)
    rng.shuffle(ordered)
    remaining = Budget(budget.check_budget, budget.call_budget)
    selected: list[str] = []
    for item in ordered:
        if len(selected) >= k:
            break
        trial = selected + [item.checkpoint_id]
        if hard_budget_enforced(trial, remaining, inventory):
            selected.append(item.checkpoint_id)
    if len(selected) < k:
        return make_selection(
            "NOT_AVAILABLE",
            selected,
            budget,
            inventory,
            reason=f"RANDOM_K_INFEASIBLE_REQUESTED={k}",
        )
    return make_selection("AVAILABLE", selected, budget, inventory)


def manual_default_stage_aligned(
    inventory: Sequence[Checkpoint],
    budget: Budget,
) -> Selection:
    inventory_ids = {item.checkpoint_id for item in inventory}
    unknown = [item for item in MANUAL_PRIORITY if item not in inventory_ids]
    if unknown:
        raise ValueError(f"manual priority absent from inventory: {unknown}")
    selected: list[str] = []
    for checkpoint_id in MANUAL_PRIORITY:
        if checkpoint_id in selected:
            continue
        trial = selected + [checkpoint_id]
        if hard_budget_enforced(trial, budget, inventory):
            selected.append(checkpoint_id)
    return make_selection("AVAILABLE", selected, budget, inventory)


def terminal_only_baseline(
    inventory: Sequence[Checkpoint],
    budget: Budget,
) -> Selection:
    return make_selection(
        TERMINAL_STATUS,
        (),
        budget,
        inventory,
        reason="NO_COMPARABLE_FINAL_OUTPUT_MONITOR_IN_AUTHORITATIVE_ARTIFACTS",
    )


def feature_vector(row: dict[str, Any], selected_ids: Sequence[str]) -> tuple[float, ...]:
    overlay = row.get("dev_only_overlay")
    if overlay is None:
        raise ValueError("DEV_ONLY overlay required before diagnosability")
    values: list[float] = []
    for checkpoint_id in selected_ids:
        if checkpoint_id not in row["response_vector"]:
            raise ValueError(f"selected checkpoint absent from row: {checkpoint_id}")
        values.append(float(row["response_vector"][checkpoint_id]))
        flags = overlay["ripr_flags"][checkpoint_id]
        for flag_name in ("REACHED", "INFECTED", "PROPAGATED", "REVEALED"):
            values.append(float(flags[flag_name]))
    return tuple(values)


def fit_nearest_centroids(
    train_rows: Sequence[dict[str, Any]],
    selected_ids: Sequence[str],
    label_key: str,
) -> dict[str, tuple[float, ...]]:
    grouped: dict[str, list[tuple[float, ...]]] = defaultdict(list)
    for row in train_rows:
        grouped[str(row[label_key])].append(feature_vector(row, selected_ids))
    centroids: dict[str, tuple[float, ...]] = {}
    dimension = len(selected_ids) * 5
    for label, vectors in grouped.items():
        if not vectors:
            continue
        centroids[label] = tuple(
            sum(vector[index] for vector in vectors) / len(vectors)
            for index in range(dimension)
        )
    return centroids


def nearest_centroid_predict(
    train_rows: Sequence[dict[str, Any]],
    test_rows: Sequence[dict[str, Any]],
    selected_ids: Sequence[str],
    label_key: str,
    tie_failure: bool = True,
) -> list[str]:
    if not selected_ids:
        return ["__TIE_FAILURE__" if tie_failure else "__NO_FEATURES__" for _ in test_rows]
    centroids = fit_nearest_centroids(train_rows, selected_ids, label_key)
    if not centroids:
        raise ValueError(f"no training centroids for {label_key}")
    predictions: list[str] = []
    for row in test_rows:
        vector = feature_vector(row, selected_ids)
        distances = {
            label: sum((value - centroid[index]) ** 2 for index, value in enumerate(vector))
            for label, centroid in centroids.items()
        }
        minimum = min(distances.values())
        tied = sorted(
            label
            for label, distance in distances.items()
            if abs(distance - minimum) <= TIE_EPSILON
        )
        if len(tied) > 1 and tie_failure:
            predictions.append("__TIE_FAILURE__")
        else:
            predictions.append(tied[0])
    return predictions


def macro_f1(
    y_true: Sequence[str],
    y_pred: Sequence[str],
    labels: Sequence[str],
) -> float:
    if len(y_true) != len(y_pred):
        raise ValueError("y_true/y_pred length mismatch")
    if not labels:
        return 0.0
    scores: list[float] = []
    for label in labels:
        true_positive = sum(
            truth == label and prediction == label
            for truth, prediction in zip(y_true, y_pred, strict=True)
        )
        false_positive = sum(
            truth != label and prediction == label
            for truth, prediction in zip(y_true, y_pred, strict=True)
        )
        false_negative = sum(
            truth == label and prediction != label
            for truth, prediction in zip(y_true, y_pred, strict=True)
        )
        precision_denominator = true_positive + false_positive
        recall_denominator = true_positive + false_negative
        if precision_denominator == 0 or recall_denominator == 0:
            scores.append(0.0)
            continue
        precision = true_positive / precision_denominator
        recall = true_positive / recall_denominator
        scores.append(2 * precision * recall / (precision + recall))
    return sum(scores) / len(scores)


def diagnosability_macro_f1(
    train_rows: Sequence[dict[str, Any]],
    test_rows: Sequence[dict[str, Any]],
    selected_ids: Sequence[str],
    label_key: str,
) -> float:
    labels = sorted({str(row[label_key]) for row in test_rows})
    predictions = nearest_centroid_predict(
        train_rows, test_rows, selected_ids, label_key, tie_failure=True
    )
    return macro_f1([str(row[label_key]) for row in test_rows], predictions, labels)


def tie_order(checkpoint: Checkpoint) -> tuple[int, int, float, str]:
    runtime = (
        checkpoint.measured_runtime_ms
        if checkpoint.measured_runtime_ms is not None
        else math.inf
    )
    return (
        checkpoint.model_or_judge_calls,
        checkpoint.check_count,
        runtime,
        checkpoint.checkpoint_id,
    )


def downstream_coverage(
    rows: Sequence[dict[str, Any]],
    selected_ids: Sequence[str],
) -> float:
    if not rows:
        return 0.0
    covered = 0
    for row in rows:
        roles = row["dev_only_overlay"]["checkpoint_roles"]
        if any(
            checkpoint_id in selected_ids
            and roles[checkpoint_id] == "DOWNSTREAM_CAUSAL_RESPONSE"
            for checkpoint_id in selected_ids
        ):
            covered += 1
    return covered / len(rows)


def causal_or_diagnostic_gain(
    rows: Sequence[dict[str, Any]],
    selected_ids: Sequence[str],
    mode: str,
) -> float:
    if mode == "coverage-only":
        return downstream_coverage(rows, selected_ids)
    if mode != "causal-diagnostic":
        raise ValueError(f"unknown greedy mode: {mode}")
    coverage = downstream_coverage(rows, selected_ids)
    if not selected_ids:
        return coverage
    stage_f1 = diagnosability_macro_f1(rows, rows, selected_ids, "stage_label")
    family_f1 = diagnosability_macro_f1(rows, rows, selected_ids, "family_label")
    return coverage + stage_f1 + family_f1


def greedy_select(
    inventory: Sequence[Checkpoint],
    budget: Budget,
    rows: Sequence[dict[str, Any]],
    mode: str,
) -> Selection:
    selected: list[str] = []
    remaining_ids = {item.checkpoint_id for item in inventory}
    while True:
        feasible: list[Checkpoint] = []
        for item in inventory:
            if item.checkpoint_id not in remaining_ids:
                continue
            if hard_budget_enforced(selected + [item.checkpoint_id], budget, inventory):
                feasible.append(item)
        if not feasible:
            break
        current_gain = causal_or_diagnostic_gain(rows, selected, mode)
        ranked: list[tuple[float, tuple[int, int, float, str], str]] = []
        for item in feasible:
            trial = selected + [item.checkpoint_id]
            gain = causal_or_diagnostic_gain(rows, trial, mode)
            ranked.append((gain, tie_order(item), item.checkpoint_id))
        max_gain = max(item[0] for item in ranked)
        best = min(
            (item for item in ranked if abs(item[0] - max_gain) <= TIE_EPSILON),
            key=lambda item: item[1],
        )
        if best[0] + TIE_EPSILON < current_gain:
            raise RuntimeError("greedy marginal gain decreased")
        selected.append(best[2])
        remaining_ids.remove(best[2])
    return make_selection("AVAILABLE", selected, budget, inventory)


def coverage_only_greedy(
    inventory: Sequence[Checkpoint],
    budget: Budget,
    rows: Sequence[dict[str, Any]],
) -> Selection:
    return greedy_select(inventory, budget, rows, "coverage-only")


def causal_diagnostic_greedy(
    inventory: Sequence[Checkpoint],
    budget: Budget,
    rows: Sequence[dict[str, Any]],
) -> Selection:
    return greedy_select(inventory, budget, rows, "causal-diagnostic")


def group_disjoint_split(
    rows: Sequence[dict[str, Any]],
    seed: int = SPLIT_SEED,
    test_fraction: float = TEST_FRACTION,
) -> dict[str, Any]:
    if not 0 < test_fraction < 1:
        raise ValueError("test_fraction must be between zero and one")
    groups_by_stage: dict[str, set[str]] = defaultdict(set)
    for row in rows:
        groups_by_stage[str(row["true_stage"])].add(str(row["cluster_id"]))
    train_groups: set[str] = set()
    test_groups: set[str] = set()
    per_stage: dict[str, dict[str, int]] = {}
    for stage in sorted(groups_by_stage):
        groups = sorted(groups_by_stage[stage])
        ranked = sorted(
            groups,
            key=lambda group: hashlib.sha256(
                f"{seed}|{stage}|{group}".encode("utf-8")
            ).hexdigest(),
        )
        test_count = max(1, math.ceil(len(ranked) * test_fraction))
        stage_test = set(ranked[:test_count])
        stage_train = set(ranked[test_count:])
        test_groups.update(stage_test)
        train_groups.update(stage_train)
        per_stage[stage] = {
            "train_groups": len(stage_train),
            "test_groups": len(stage_test),
        }
    if train_groups & test_groups:
        raise RuntimeError("group-disjoint split leaked a cluster")
    train_rows = [row for row in rows if row["cluster_id"] in train_groups]
    test_rows = [row for row in rows if row["cluster_id"] in test_groups]
    if any(row["cluster_id"] in test_groups for row in train_rows):
        raise RuntimeError("group-disjoint split row leak")
    return {
        "label": SPLIT_LABEL,
        "strategy": "STAGE_STRATIFIED_GROUP_DISJOINT",
        "group_key": "cluster_id",
        "seed": seed,
        "test_fraction": test_fraction,
        "mechanism_holdout": TERMINAL_STATUS,
        "mechanism_holdout_reason": "OLD_MATRIX_HAS_ONE_MECHANISM_PER_STAGE",
        "train_group_ids": sorted(train_groups),
        "test_group_ids": sorted(test_groups),
        "train_group_count": len(train_groups),
        "test_group_count": len(test_groups),
        "train_row_count": len(train_rows),
        "test_row_count": len(test_rows),
        "per_stage_group_counts": per_stage,
        "group_overlap": [],
    }


def split_rows(
    rows: Sequence[dict[str, Any]],
    split: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    train_groups = set(split["train_group_ids"])
    test_groups = set(split["test_group_ids"])
    train_rows = [row for row in rows if row["cluster_id"] in train_groups]
    test_rows = [row for row in rows if row["cluster_id"] in test_groups]
    if set(row["cluster_id"] for row in train_rows) & set(
        row["cluster_id"] for row in test_rows
    ):
        raise RuntimeError("group overlap after split_rows")
    return train_rows, test_rows


def overlay_counts(rows: Sequence[dict[str, Any]]) -> dict[str, int]:
    overlays = [row["dev_only_overlay"] for row in rows]
    return {
        "rows": len(rows),
        "source_local_positive_rows": sum(
            overlay["SOURCE_LOCAL_RESPONSE"] for overlay in overlays
        ),
        "downstream_causal_positive_rows": sum(
            overlay["DOWNSTREAM_CAUSAL_RESPONSE"] for overlay in overlays
        ),
        "source_local_positive_cells": sum(
            role == "SOURCE_LOCAL_RESPONSE"
            for overlay in overlays
            for role in overlay["checkpoint_roles"].values()
        ),
        "downstream_causal_positive_cells": sum(
            role == "DOWNSTREAM_CAUSAL_RESPONSE"
            for overlay in overlays
            for role in overlay["checkpoint_roles"].values()
        ),
    }


def evaluate_selection(
    selection: Selection,
    budget: Budget,
    inventory: Sequence[Checkpoint],
    train_rows: Sequence[dict[str, Any]],
    test_rows: Sequence[dict[str, Any]],
) -> tuple[dict[str, Any], dict[str, Any]]:
    budget_usage = assert_hard_budget(selection.selected_ids, budget, inventory)
    response_counts = {
        "source_local_positive_rows": overlay_counts(test_rows)[
            "source_local_positive_rows"
        ],
        "downstream_causal_positive_rows": overlay_counts(test_rows)[
            "downstream_causal_positive_rows"
        ],
        "selected_source_local_positive_cells": 0,
        "selected_downstream_causal_positive_cells": 0,
        "selected_positive_cells": 0,
    }
    for row in test_rows:
        roles = row["dev_only_overlay"]["checkpoint_roles"]
        for checkpoint_id in selection.selected_ids:
            role = roles[checkpoint_id]
            if row["response_vector"][checkpoint_id] > 0:
                response_counts["selected_positive_cells"] += 1
            if role == "SOURCE_LOCAL_RESPONSE":
                response_counts["selected_source_local_positive_cells"] += 1
            elif role == "DOWNSTREAM_CAUSAL_RESPONSE":
                response_counts["selected_downstream_causal_positive_cells"] += 1
    metrics: dict[str, float | None] = {field: None for field in METRIC_FIELDS}
    if selection.status == "AVAILABLE" and test_rows:
        selected = list(selection.selected_ids)
        metrics["downstream_causal_coverage"] = downstream_coverage(test_rows, selected)
        metrics["source_local_coverage"] = sum(
            any(
                checkpoint_id in selected
                and row["dev_only_overlay"]["checkpoint_roles"][checkpoint_id]
                == "SOURCE_LOCAL_RESPONSE"
                for checkpoint_id in selected
            )
            for row in test_rows
        ) / len(test_rows)
        metrics["failure_coverage"] = sum(
            any(
                checkpoint_id in selected
                and row["response_vector"][checkpoint_id] > 0
                for checkpoint_id in selected
            )
            for row in test_rows
        ) / len(test_rows)
        metrics["source_local_only_coverage"] = sum(
            any(
                checkpoint_id in selected
                and row["dev_only_overlay"]["checkpoint_roles"][checkpoint_id]
                == "SOURCE_LOCAL_RESPONSE"
                for checkpoint_id in selected
            )
            and not any(
                checkpoint_id in selected
                and row["dev_only_overlay"]["checkpoint_roles"][checkpoint_id]
                == "DOWNSTREAM_CAUSAL_RESPONSE"
                for checkpoint_id in selected
            )
            for row in test_rows
        ) / len(test_rows)
        metrics["stage_macro_f1"] = diagnosability_macro_f1(
            train_rows, test_rows, selected, "stage_label"
        )
        metrics["family_macro_f1"] = diagnosability_macro_f1(
            train_rows, test_rows, selected, "family_label"
        )
        metrics["diagnosability_macro_f1"] = (
            float(metrics["stage_macro_f1"]) + float(metrics["family_macro_f1"])
        ) / 2
    return budget_usage, {**response_counts, **{f"metrics_{key}": value for key, value in metrics.items()}}


def selection_result(
    baseline_id: str,
    selection: Selection,
    budget: Budget,
    inventory: Sequence[Checkpoint],
    train_rows: Sequence[dict[str, Any]],
    test_rows: Sequence[dict[str, Any]],
) -> dict[str, Any]:
    budget_usage, counts_and_metrics = evaluate_selection(
        selection, budget, inventory, train_rows, test_rows
    )
    response_counts = {
        key: value
        for key, value in counts_and_metrics.items()
        if not key.startswith("metrics_")
    }
    metrics = {
        key.removeprefix("metrics_"): counts_and_metrics[key]
        for key in counts_and_metrics
        if key.startswith("metrics_")
    }
    return {
        "baseline_id": baseline_id,
        "status": selection.status,
        "availability": selection.status == "AVAILABLE",
        "reason": selection.reason,
        "selected_ids": list(selection.selected_ids),
        "selected_checkpoint_count": len(selection.selected_ids),
        "budget_usage": budget_usage,
        "response_counts": response_counts,
        "metrics": metrics,
    }


def build_result(
    rows: Sequence[dict[str, Any]],
    paired_rows: Sequence[dict[str, Any]],
    inventory: Sequence[Checkpoint],
    hashes: dict[str, str],
    shape: dict[str, Any],
) -> dict[str, Any]:
    augmented = apply_dev_only_overlay(rows)
    split = group_disjoint_split(augmented)
    train_rows, test_rows = split_rows(augmented, split)
    budget_results: list[dict[str, Any]] = []
    for check_budget, call_budget in SMOKE_BUDGETS:
        budget = Budget(check_budget, call_budget)
        selections = {
            "all-checkpoints": all_checkpoints(inventory, budget),
            "random-K": random_k_select(inventory, budget, check_budget, RANDOM_SEED),
            "manual/default stage-aligned": manual_default_stage_aligned(
                inventory, budget
            ),
            "coverage-only greedy": coverage_only_greedy(
                inventory, budget, train_rows
            ),
            "ours": causal_diagnostic_greedy(inventory, budget, train_rows),
            "terminal-only": terminal_only_baseline(inventory, budget),
        }
        budget_results.append(
            {
                "budget_id": f"B_check={check_budget},B_call={call_budget}",
                "B_check": check_budget,
                "B_call": call_budget,
                "budget_scope": "SMOKE_CONSTRAINT_ONLY",
                "baselines": {
                    baseline_id: selection_result(
                        baseline_id,
                        selections[baseline_id],
                        budget,
                        inventory,
                        train_rows,
                        test_rows,
                    )
                    for baseline_id in BASELINE_IDS
                },
            }
        )
    baseline_schema_ok = all(
        set(result) == set(REQUIRED_SELECTION_FIELDS)
        for budget_result in budget_results
        for result in budget_result["baselines"].values()
    )
    result = {
        "schema_version": "causal_checkpoint_selection_dev_smoke_v1",
        "evidence_class": EVIDENCE_CLASS,
        "receipt_label": RECEIPT_LABEL,
        "scientific_claim": "ZERO",
        "formal_experiment": "ZERO",
        "endpoint_calls": 0,
        "formal_scientific_outputs_created": 0,
        "input_hashes": hashes,
        "input_shape": shape,
        "mechanism_holdout": TERMINAL_STATUS,
        "mechanism_holdout_reason": "OLD_MATRIX_HAS_ONE_MECHANISM_PER_STAGE",
        "split": split,
        "checkpoint_inventory": [asdict(item) for item in inventory],
        "overlay_definition": {
            "label": "DEV_ONLY_RESPONSE_ROLE_AND_RIPR_PLUMBING_OVERLAY",
            "source_local_target": DIRECT_TARGETS,
            "potential_downstream_targets": {
                stage: list(leaves) for stage, leaves in POTENTIAL_DOWNSTREAM.items()
            },
            "family_label_definition": "DEV_ONLY_DIRECT_TARGET_CONFIG_TOP_TREE_FAMILY",
            "raw_state_evidence": "NOT_IDENTIFIABLE",
        },
        "cost_definition": {
            "check_count": 1,
            "model_or_judge_calls": "1 for checkpoint IDs ending in .judge; otherwise 0",
            "human_cost_weights": 0,
        },
        "tie_rule": [
            "fewer_model_or_judge_calls",
            "lower_check_count",
            "lower_measured_runtime_when_available",
            "fixed_checkpoint_id",
        ],
        "random_seed": RANDOM_SEED,
        "metric_fields": list(METRIC_FIELDS),
        "budget_results": budget_results,
        "overlay_counts": overlay_counts(augmented),
        "deterministic_replay_required": True,
    }
    result["required_fields_present"] = all(
        field in result for field in REQUIRED_RESULT_FIELDS
        if field != "required_fields_present"
    ) and baseline_schema_ok
    return result


def input_manifest(
    hashes: dict[str, str],
    shape: dict[str, Any],
    inventory: Sequence[Checkpoint],
) -> dict[str, Any]:
    return {
        "schema_version": "causal_checkpoint_selection_dev_smoke_input_manifest_v1",
        "evidence_class": EVIDENCE_CLASS,
        "receipt_label": RECEIPT_LABEL,
        "input_hashes": hashes,
        "input_shape": shape,
        "checkpoint_inventory": [asdict(item) for item in inventory],
        "checkpoint_count": len(inventory),
        "smoke_budgets": [
            {"B_check": check, "B_call": calls} for check, calls in SMOKE_BUDGETS
        ],
        "mechanism_holdout": TERMINAL_STATUS,
        "split_label": SPLIT_LABEL,
        "random_seed": RANDOM_SEED,
        "split_seed": SPLIT_SEED,
        "formal_scientific_dataset_created": False,
        "endpoint_calls": 0,
    }


def receipt(
    hashes: dict[str, str],
    result: dict[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": "causal_checkpoint_selection_dev_smoke_receipt_v1",
        "receipt_label": RECEIPT_LABEL,
        "evidence_class": EVIDENCE_CLASS,
        "statement": (
            "ALGORITHM_SMOKE_DEV_ONLY; zero scientific claim; "
            "zero formal experiment."
        ),
        "scientific_claim": "ZERO",
        "formal_experiment": "ZERO",
        "scientific_claim_count": 0,
        "formal_experiment_count": 0,
        "endpoint_calls": 0,
        "model_training_runs": 0,
        "new_scientific_dataset_rows": 0,
        "input_hashes": hashes,
        "design_contract_changed": False,
        "frozen_multi_leaf_artifacts_changed": False,
        "shape_status": result["input_shape"]["shape_status"],
        "required_fields_present": result["required_fields_present"],
        "mechanism_holdout": TERMINAL_STATUS,
        "success_exit": "METHOD_DATASET_READY_PENDING_INDEPENDENT_LOOP_C_AUDIT",
        "unverified_scope": [
            "GB10_RUNTIME",
            "FORMAL_SCIENTIFIC_VALIDITY",
            "INDEPENDENT_LOOP_C_AUDIT",
        ],
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True, ensure_ascii=False)
        handle.write("\n")


def generate_smoke_artifacts(root: Path | None = None) -> dict[str, Path]:
    base = root or repository_root()
    rows, paired_rows, inventory, hashes, shape = load_authoritative_inputs(base)
    result = build_result(rows, paired_rows, inventory, hashes, shape)
    manifest = input_manifest(hashes, shape, inventory)
    output_dir = (
        base
        / "research/causal_checkpoint_selection_mvp_20261011/smoke"
    )
    paths = {
        "manifest": output_dir / "dev_smoke_input_manifest.json",
        "result": output_dir / "dev_smoke_result.json",
        "receipt": output_dir / "dev_smoke_receipt.json",
    }
    write_json(paths["manifest"], manifest)
    write_json(paths["result"], result)
    write_json(paths["receipt"], receipt(hashes, result))
    return paths


def main() -> int:
    paths = generate_smoke_artifacts()
    print(json.dumps({key: str(value) for key, value in paths.items()}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
