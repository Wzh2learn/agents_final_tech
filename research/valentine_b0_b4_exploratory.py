"""Run the frozen exploratory Valentine B0-B4 probe without model calls.

This runner consumes the sealed corrected Q3 label ledger, the original Q3
input package, and a gold-free process/checkpoint view. It performs only
deterministic or CPU-only baselines. Results are development exploratory
evidence and never authorize Stage D, DATA_GO, training, Phase 2, or paper use.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import statistics
import sys
import tempfile
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from research.phase1a_learnability_baselines import (  # noqa: E402
    _SoftmaxClassifier,
    _confidence_only,
    _deterministic_matcher,
    _features,
    _lexical_fuzzy,
)

ACTIONS = ("map_to", "skip", "hold")
BASELINES = ("B0", "B1", "B2", "B3", "B4")
BASELINE_NAMES = {
    "B0": "always_skip",
    "B1": "deterministic_matcher",
    "B2": "lexical_fuzzy",
    "B3": "confidence_only",
    "B4": "simple_classifier",
}


class ProbeError(ValueError):
    """Fail-closed exploratory probe error."""


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _stable_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_labels(path: Path) -> dict[str, dict[str, object]]:
    labels: dict[str, dict[str, object]] = {}
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        fields = [field.strip() for field in line.split("|")]
        if len(fields) < 3:
            raise ProbeError("invalid_label_row", line=line_no)
        sample_id, action, target = fields[:3]
        if action not in ACTIONS:
            raise ProbeError("invalid_label_action", line=line_no, action=action)
        if sample_id in labels:
            raise ProbeError("duplicate_label_sample", sample_id=sample_id)
        labels[sample_id] = {
            "gold_action": action,
            "gold_target": None if target in {"null", ""} else target,
        }
    if not labels:
        raise ProbeError("empty_label_ledger")
    return labels


def _load_samples(path: Path) -> dict[str, dict[str, object]]:
    samples: dict[str, dict[str, object]] = {}
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        row = json.loads(line)
        sample_id = row.get("sample_id")
        if not isinstance(sample_id, str) or sample_id in samples:
            raise ProbeError("invalid_sample_id", line=line_no)
        for key in ("lineage_root_id", "source_header", "target_headers", "uid", "col"):
            if key not in row:
                raise ProbeError("missing_sample_field", line=line_no, field=key)
        samples[sample_id] = row
    return samples


def _load_process_features(events_path: Path) -> dict[str, dict[str, object]]:
    grouped: dict[str, list[dict[str, object]]] = defaultdict(list)
    for line in events_path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            row = json.loads(line)
            grouped[str(row["sample_id"])].append(row)
    features: dict[str, dict[str, object]] = {}
    for sample_id, rows in grouped.items():
        rows.sort(key=lambda row: (int(row["turn"]), int(row["event_index"]), str(row["event_id"])))
        candidate_target: str | None = None
        confidence: float | None = None
        seen_record = False
        seen_revoke = False
        for row in rows:
            kind = row.get("event_kind")
            if kind == "record_candidate":
                target = row.get("target_header")
                if isinstance(target, str):
                    candidate_target = target
                    value = row.get("confidence")
                    confidence = float(value) if isinstance(value, (int, float)) else None
                    seen_record = True
            elif kind == "revoke_candidate":
                candidate_target = None
                confidence = None
                seen_revoke = True
        features[sample_id] = {
            "candidate_target": candidate_target,
            "confidence": confidence,
            "seen_record": seen_record,
            "seen_revoke": seen_revoke,
            "event_count": len(rows),
        }
    return features


def _confidence_category(value: object) -> str:
    if value is None:
        return "missing"
    number = float(value)
    if not math.isfinite(number):
        raise ProbeError("invalid_confidence", value=value)
    if number >= 0.8:
        return "high"
    if number >= 0.6:
        return "medium"
    return "low"


def _make_rows(
    labels: dict[str, dict[str, object]],
    samples: dict[str, dict[str, object]],
    process_features: dict[str, dict[str, object]],
    included_pairs: set[str],
) -> list[dict[str, object]]:
    if set(labels) != set(samples):
        raise ProbeError(
            "label_sample_set_mismatch",
            missing_labels=sorted(set(samples) - set(labels)),
            extra_labels=sorted(set(labels) - set(samples)),
        )
    rows: list[dict[str, object]] = []
    for sample_id in sorted(samples):
        sample = samples[sample_id]
        pair = str(sample["lineage_root_id"])
        if pair not in included_pairs:
            continue
        feature = process_features.get(sample_id, {})
        confidence_value = feature.get("confidence")
        target_headers = list(sample["target_headers"])
        candidate_target = feature.get("candidate_target")
        if candidate_target is not None and candidate_target not in target_headers:
            raise ProbeError("candidate_target_not_canonical", sample_id=sample_id)
        row = {
            "sample_id": sample_id,
            "uid": sample["uid"],
            "observed_header": sample["source_header"],
            "canonical_fields": target_headers,
            "candidate_target": candidate_target,
            "confidence": _confidence_category(confidence_value),
            "gold_action": labels[sample_id]["gold_action"],
            "gold_target": labels[sample_id]["gold_target"],
            "quality_grade": "Q3",
            "family": pair,
            "pair_id": pair,
            "confidence_numeric": confidence_value,
            "process_event_count": feature.get("event_count", 0),
        }
        rows.append(row)
    if not rows:
        raise ProbeError("empty_analysis_rows")
    return rows


def _predict_nonlearned(row: dict[str, object], baseline: str, threshold: float) -> tuple[str, str | None] | None:
    if baseline == "B0":
        return ("skip", None)
    if baseline == "B1":
        return _deterministic_matcher(row)
    if baseline == "B2":
        return _lexical_fuzzy(row, threshold)
    if baseline == "B3":
        return _confidence_only(row)
    raise ProbeError("unknown_nonlearned_baseline", baseline=baseline)


def _predict_all(
    rows: list[dict[str, object]],
    config: dict[str, object],
    split: str,
    salted_assignment: dict[str, str] | None = None,
) -> dict[str, list[tuple[str, str | None] | None]]:
    predictions: dict[str, list[tuple[str, str | None] | None]] = {name: [] for name in BASELINES}
    threshold = float(config["lexical_threshold"])
    for row in rows:
        for baseline in ("B0", "B1", "B2", "B3"):
            predictions[baseline].append(_predict_nonlearned(row, baseline, threshold))

    if split == "leave_one_pair_out":
        pairs = sorted({str(row["pair_id"]) for row in rows})
        for held_out in pairs:
            train = [row for row in rows if row["pair_id"] != held_out]
            test_indices = [index for index, row in enumerate(rows) if row["pair_id"] == held_out]
            if not train or not test_indices:
                raise ProbeError("empty_loo_fold", pair=held_out)
            classifier = _SoftmaxClassifier(
                epochs=int(config["classifier"]["epochs"]),
                learning_rate=float(config["classifier"]["learning_rate"]),
                l2=float(config["classifier"]["l2"]),
            )
            classifier.fit(train)
            for index in test_indices:
                predictions["B4"].append((index, classifier.predict(rows[index])))  # type: ignore[arg-type]
    elif split == "salted_group_split":
        if salted_assignment is None:
            raise ProbeError("missing_salted_assignment")
        train_pairs = {pair for pair, layer in salted_assignment.items() if layer == "train"}
        test_pairs = {pair for pair, layer in salted_assignment.items() if layer == "test"}
        train = [row for row in rows if row["pair_id"] in train_pairs]
        test_indices = [index for index, row in enumerate(rows) if row["pair_id"] in test_pairs]
        if not train or not test_indices:
            raise ProbeError("empty_salted_layer", train=sorted(train_pairs), test=sorted(test_pairs))
        classifier = _SoftmaxClassifier(
            epochs=int(config["classifier"]["epochs"]),
            learning_rate=float(config["classifier"]["learning_rate"]),
            l2=float(config["classifier"]["l2"]),
        )
        classifier.fit(train)
        for index in test_indices:
            predictions["B4"].append((index, classifier.predict(rows[index])))  # type: ignore[arg-type]
    else:
        raise ProbeError("invalid_split", split=split)

    if split == "salted_group_split":
        test_pairs = {pair for pair, layer in salted_assignment.items() if layer == "test"}
        test_indices = [index for index, row in enumerate(rows) if row["pair_id"] in test_pairs]
        for baseline in ("B0", "B1", "B2", "B3"):
            predictions[baseline] = [predictions[baseline][index] for index in test_indices]
    else:
        for baseline in ("B0", "B1", "B2", "B3"):
            predictions[baseline] = list(predictions[baseline])
    return predictions


def _align_rows_and_predictions(
    rows: list[dict[str, object]],
    raw_predictions: list[object],
    split: str,
    salted_assignment: dict[str, str] | None,
) -> tuple[list[dict[str, object]], list[tuple[str, str | None] | None]]:
    if split == "salted_group_split":
        test_pairs = {pair for pair, layer in salted_assignment.items() if layer == "test"}
        selected = [row for row in rows if row["pair_id"] in test_pairs]
    else:
        selected = list(rows)
    if split == "leave_one_pair_out":
        by_index = {int(item[0]): item[1] for item in raw_predictions if isinstance(item, tuple)}
        aligned = [by_index.get(index) for index in range(len(rows))]
        return rows, aligned
    return selected, list(raw_predictions)  # type: ignore[arg-type]


def _percentile(values: list[float], q: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    position = (len(ordered) - 1) * q
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


def _metric_core(
    rows: list[dict[str, object]],
    predictions: list[tuple[str, str | None] | None],
) -> dict[str, object]:
    if len(rows) != len(predictions):
        raise ProbeError("prediction_length_mismatch")
    scored = [(row, pred) for row, pred in zip(rows, predictions, strict=True) if pred is not None]
    abstained = len(rows) - len(scored)
    confusion: dict[str, Counter] = {action: Counter() for action in ACTIONS}
    for row, pred in scored:
        action, _target = pred
        confusion[str(row["gold_action"])][action] += 1
    f1: dict[str, float | None] = {}
    for action in ACTIONS:
        tp = confusion[action][action]
        fp = sum(confusion[other][action] for other in ACTIONS if other != action)
        fn = sum(confusion[action][other] for other in ACTIONS if other != action)
        denominator = 2 * tp + fp + fn
        f1[action] = (2 * tp / denominator) if denominator else None
    macro = statistics.fmean(value for value in f1.values() if value is not None) if any(value is not None for value in f1.values()) else None
    incorrect_map = sum(
        1 for row, pred in scored
        if pred[0] == "map_to" and (row["gold_action"] != "map_to" or pred[1] != row["gold_target"])
    )
    correct_map = sum(
        1 for row, pred in scored
        if pred[0] == "map_to" and row["gold_action"] == "map_to" and pred[1] == row["gold_target"]
    )
    predicted_map = sum(1 for _row, pred in scored if pred[0] == "map_to")
    gold_map_rows = [row for row in rows if row["gold_action"] == "map_to"]
    gold_map_correct = sum(
        1 for row, pred in zip(rows, predictions, strict=True)
        if row["gold_action"] == "map_to" and pred is not None and pred[0] == "map_to" and pred[1] == row["gold_target"]
    )
    pair_rows: dict[str, list[bool]] = defaultdict(list)
    for row, pred in zip(rows, predictions, strict=True):
        pair_rows[str(row["pair_id"])].append(
            pred is not None and pred[0] == row["gold_action"]
        )
    return {
        "row_count": len(rows),
        "scored_row_count": len(scored),
        "abstained_row_count": abstained,
        "abstention_rate": abstained / len(rows),
        "action_macro_f1": macro,
        "action_f1_by_class": f1,
        "action_accuracy": sum(1 for row, pred in scored if pred[0] == row["gold_action"]) / len(scored) if scored else None,
        "harmful_map_rate": incorrect_map / len(scored) if scored else None,
        "map_to_risk": incorrect_map / predicted_map if predicted_map else None,
        "correct_map_coverage_all_rows": correct_map / len(rows),
        "target_exact_gold_map_to": gold_map_correct / len(gold_map_rows) if gold_map_rows else None,
        "target_exact_predicted_map_to": sum(
            1 for row, pred in scored if pred[0] == "map_to" and pred[1] == row["gold_target"]
        ) / predicted_map if predicted_map else None,
        "per_pair_action_accuracy": {
            pair: sum(values) / len(values) for pair, values in sorted(pair_rows.items())
        },
    }


def _bootstrap(
    rows: list[dict[str, object]],
    predictions: list[tuple[str, str | None] | None],
    config: dict[str, object],
) -> dict[str, object]:
    by_pair: dict[str, list[int]] = defaultdict(list)
    for index, row in enumerate(rows):
        by_pair[str(row["pair_id"])].append(index)
    pairs = sorted(by_pair)
    metric_names = (
        "action_macro_f1",
        "harmful_map_rate",
        "correct_map_coverage_all_rows",
        "target_exact_gold_map_to",
    )
    samples_n = int(config["bootstrap"]["samples"])
    per_seed: dict[str, dict[str, list[float]]] = {}
    for seed in config["bootstrap"]["seeds"]:
        rng = random.Random(int(seed))
        values: dict[str, list[float]] = {name: [] for name in metric_names}
        for _ in range(samples_n):
            sampled_pairs = [pairs[rng.randrange(len(pairs))] for _ in pairs]
            sampled_indices = [index for pair in sampled_pairs for index in by_pair[pair]]
            metrics = _metric_core(
                [rows[index] for index in sampled_indices],
                [predictions[index] for index in sampled_indices],
            )
            for name in metric_names:
                value = metrics[name]
                if isinstance(value, (int, float)):
                    values[name].append(float(value))
        per_seed[str(seed)] = values
    pooled = {
        name: [value for seed_values in per_seed.values() for value in seed_values[name]]
        for name in metric_names
    }
    return {
        "samples_per_seed": samples_n,
        "seeds": list(config["bootstrap"]["seeds"]),
        "cluster_unit": config["bootstrap"]["cluster_unit"],
        "interval": {
            name: {
                "low": _percentile(values, 0.025),
                "high": _percentile(values, 0.975),
            }
            for name, values in pooled.items()
        },
        "seed_dispersion": {
            seed: {
                name: {
                    "mean": statistics.fmean(values) if values else None,
                    "stdev": statistics.pstdev(values) if len(values) > 1 else 0.0,
                }
                for name, values in seed_values.items()
            }
            for seed, seed_values in per_seed.items()
        },
        "power_claim_allowed": False,
    }


def _salted_assignment(pairs: list[str], config: dict[str, object]) -> dict[str, str]:
    salt = str(config["salted_split"]["salt"]).encode("utf-8")
    modulus = int(config["salted_split"]["modulus"])
    assignment: dict[str, str] = {}
    for pair in pairs:
        bucket = int(hashlib.sha256(salt + b"\n" + pair.encode("utf-8")).hexdigest(), 16) % modulus
        if bucket < int(config["salted_split"]["train_buckets"][1]):
            assignment[pair] = "train"
        elif bucket < int(config["salted_split"]["dev_buckets"][1]):
            assignment[pair] = "dev"
        else:
            assignment[pair] = "test"
    if any(layer not in {"train", "dev", "test"} for layer in assignment.values()):
        raise ProbeError("invalid_salted_layer")
    if not [pair for pair, layer in assignment.items() if layer == "train"] or not [pair for pair, layer in assignment.items() if layer == "test"]:
        raise ProbeError("empty_salted_layer", assignment=assignment)
    return assignment


def _run_variant(
    labels_path: Path,
    samples_path: Path,
    canonical_path: Path,
    process_summary_path: Path,
    process_events_path: Path,
    config: dict[str, object],
    analysis_variant: str,
    split: str,
) -> tuple[dict[str, object], list[dict[str, object]]]:
    labels = _load_labels(labels_path)
    samples = _load_samples(samples_path)
    canonical = _load_json(canonical_path)
    if not isinstance(canonical, dict):
        raise ProbeError("invalid_canonical_reference")
    for pair, fields in canonical.items():
        if not isinstance(fields, list):
            raise ProbeError("invalid_canonical_pair", pair=pair)
    process_summary = _load_json(process_summary_path)
    if not isinstance(process_summary, dict):
        raise ProbeError("invalid_process_summary")
    included_pairs = {
        str(row["pair_id"]) for row in process_summary.get("pairs", [])
        if row.get("analysis_included") is True
    }
    process_features = _load_process_features(process_events_path)
    rows = _make_rows(labels, samples, process_features, included_pairs)
    for row in rows:
        expected = set(canonical.get(str(row["pair_id"]), []))
        if set(row["canonical_fields"]) != expected:
            raise ProbeError("canonical_reference_mismatch", pair=row["pair_id"])

    salted_assignment = None
    if split == "salted_group_split":
        salted_assignment = _salted_assignment(sorted({str(row["pair_id"]) for row in rows}), config)
    raw_predictions = _predict_all(rows, config, split, salted_assignment)
    report_rows: list[dict[str, object]] = []
    baseline_reports: dict[str, object] = {}
    for baseline in BASELINES:
        selected_rows, aligned = _align_rows_and_predictions(rows, raw_predictions[baseline], split, salted_assignment)
        baseline_reports[baseline] = {
            "runner_name": BASELINE_NAMES[baseline],
            "metrics": _metric_core(selected_rows, aligned),
            "cluster_bootstrap": _bootstrap(selected_rows, aligned, config),
        }
        for row, prediction in zip(selected_rows, aligned, strict=True):
            report_rows.append({
                "analysis_variant": analysis_variant,
                "split": split,
                "baseline": baseline,
                "sample_id": row["sample_id"],
                "pair_id": row["pair_id"],
                "gold_action": row["gold_action"],
                "gold_target": row["gold_target"],
                "predicted_action": prediction[0] if prediction is not None else None,
                "predicted_target": prediction[1] if prediction is not None else None,
                "abstained": prediction is None,
                "paper_result": False,
            })
    return {
        "analysis_variant": analysis_variant,
        "split": split,
        "row_count": len(rows),
        "pair_count": len({str(row["pair_id"]) for row in rows}),
        "salted_assignment": salted_assignment,
        "baselines": baseline_reports,
        "decision_status": "EXPLORATORY_ONLY_NOT_A_GO_NO_GO_GATE",
        "data_go": False,
        "rq2_status": "NOT_IDENTIFIED",
        "paper_result": False,
    }, report_rows


def build(
    *,
    labels_path: Path,
    samples_path: Path,
    canonical_reference_path: Path,
    process_summary_path: Path,
    process_events_path: Path,
    config_path: Path,
    out_dir: Path,
    analysis_variant: str,
    split: str,
) -> dict[str, object]:
    config = _load_json(config_path)
    if not isinstance(config, dict):
        raise ProbeError("invalid_config")
    if config.get("same_data_tuning_allowed") is not False:
        raise ProbeError("same_data_tuning_not_prohibited")
    if config.get("paper_result") is not False:
        raise ProbeError("config_must_be_paper_result_false")
    if out_dir.exists() and any(out_dir.iterdir()):
        raise ProbeError("output_dir_not_empty")
    out_dir.mkdir(parents=True, exist_ok=True)
    report, prediction_rows = _run_variant(
        labels_path,
        samples_path,
        canonical_reference_path,
        process_summary_path,
        process_events_path,
        config,
        analysis_variant,
        split,
    )
    report["hashes"] = {
        "labels_sha256": _sha256(labels_path),
        "samples_sha256": _sha256(samples_path),
        "canonical_reference_sha256": _sha256(canonical_reference_path),
        "process_summary_sha256": _sha256(process_summary_path),
        "process_events_sha256": _sha256(process_events_path),
        "config_sha256": _sha256(config_path),
    }
    predictions_path = out_dir / "predictions.jsonl"
    predictions_path.write_text("".join(_stable_json(row) + "\n" for row in prediction_rows), encoding="utf-8", newline="\n")
    report["prediction_count"] = len(prediction_rows)
    report_path = out_dir / "report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8", newline="\n")
    manifest = {
        "contract_version": config["contract_version"],
        "analysis_variant": analysis_variant,
        "split": split,
        "files": {
            "report.json": {"bytes": report_path.stat().st_size, "sha256": _sha256(report_path)},
            "predictions.jsonl": {"bytes": predictions_path.stat().st_size, "sha256": _sha256(predictions_path)},
        },
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8", newline="\n")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Run frozen exploratory Valentine B0-B4 baselines")
    parser.add_argument("--labels", type=Path, required=True)
    parser.add_argument("--samples", type=Path, required=True)
    parser.add_argument("--canonical-reference", type=Path, required=True)
    parser.add_argument("--process-summary", type=Path, required=True)
    parser.add_argument("--process-events", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--analysis-variant", choices=("quarantine-primary", "pair-invalid-sensitivity"), required=True)
    parser.add_argument("--split", choices=("leave_one_pair_out", "salted_group_split"), required=True)
    args = parser.parse_args()
    report = build(
        labels_path=args.labels,
        samples_path=args.samples,
        canonical_reference_path=args.canonical_reference,
        process_summary_path=args.process_summary,
        process_events_path=args.process_events,
        config_path=args.config,
        out_dir=args.out_dir,
        analysis_variant=args.analysis_variant,
        split=args.split,
    )
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
