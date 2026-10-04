"""Validate Stage D training readiness without loading a model.

This is a dry-run contract checker. It validates configuration shape, safety
gates, dependency readiness, and planning-estimate labels. It never imports or
loads model weights and never authorizes training.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

REQUIRED_ARMS = {"A0", "A1", "A2", "A3"}
REQUIRED_SEEDS = [42, 43, 44]
REQUIRED_DEPENDENCIES = {"torch", "accelerate", "transformers", "peft", "trl", "deepspeed"}
FORBIDDEN_A2_FILTER_INPUTS = {"ground_truth", "source_gold", "final_correctness", "gain", "collateral", "gate_decision", "model_prediction"}


class ReadinessError(ValueError):
    def __init__(self, code: str, **detail: object) -> None:
        self.code = code
        self.detail = detail
        super().__init__(f"{code}: {detail}")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _require(condition: bool, code: str, **detail: object) -> None:
    if not condition:
        raise ReadinessError(code, **detail)


def validate(config_path: Path) -> dict[str, object]:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    _require(isinstance(config, dict), "invalid_config_type")
    _require(config.get("training_execution_authorized") is False, "training_must_remain_unauthorized")
    _require(config.get("training_results_present") is False, "training_results_must_be_absent")
    _require(config.get("paper_result") is False, "paper_result_must_be_false")
    _require(config.get("data_go") is False, "data_go_must_be_false")
    _require(config.get("rq2_status") == "NOT_IDENTIFIED", "rq2_boundary_changed")
    _require(config.get("stage_d_necessity") == "NOT_ESTABLISHED", "necessity_boundary_changed")

    arms = config.get("arms")
    _require(isinstance(arms, dict), "missing_arms")
    _require(set(arms) == REQUIRED_ARMS, "arm_set_mismatch", actual=sorted(arms))
    for arm in REQUIRED_ARMS:
        arm_config = arms[arm]
        _require(isinstance(arm_config, dict), "invalid_arm_config", arm=arm)
        _require(arm_config.get("status") in {"PREPARED_NOT_RUN", "CONDITIONAL_NOT_RUN"}, "arm_must_not_be_run", arm=arm)
    for arm in ("A1", "A2", "A3"):
        _require(arms[arm].get("seed_list") == REQUIRED_SEEDS, "seed_list_mismatch", arm=arm)
    _require(arms["A0"].get("train") is False, "a0_must_not_train")
    _require(arms["A2"].get("inherit_from") == "A1", "a2_must_match_a1")
    _require(arms["A3"].get("status") == "CONDITIONAL_NOT_RUN", "a3_must_be_conditional")

    template = config.get("template")
    _require(isinstance(template, dict), "missing_template")
    _require(template.get("decision_order") == ["map_to", "hold", "skip"], "decision_order_mismatch")
    _require(template.get("gold_leakage_forbidden") is True, "gold_leakage_must_be_forbidden")

    a2_filter = arms["A2"].get("filter_rule")
    _require(isinstance(a2_filter, dict), "missing_a2_filter")
    forbidden = set(arms["A2"].get("filter_forbidden_inputs", []))
    _require(forbidden == FORBIDDEN_A2_FILTER_INPUTS, "a2_filter_forbidden_set_mismatch", actual=sorted(forbidden))
    _require(arms["A2"].get("filter_inputs"), "a2_filter_inputs_missing")

    outputs = config.get("outputs")
    _require(isinstance(outputs, dict), "missing_outputs")
    _require(str(outputs.get("root", "")).startswith("/home/testuser/wzh/stage_d_runs"), "output_root_outside_isolated_area")
    _require(outputs.get("per_run_output_limit_bytes", 0) <= 5 * 1024**3, "output_limit_too_large")
    _require(outputs.get("per_run_log_limit_bytes", 0) <= 500 * 1024**2, "log_limit_too_large")
    _require(outputs.get("overwrite_existing") is False, "overwrite_must_be_false")

    resources = config.get("resources")
    _require(isinstance(resources, dict), "missing_resources")
    start = resources["start_gates"]
    stop = resources["stop_gates"]
    _require(start["disk_free_gb_min"] >= 50 and start["disk_free_percent_min"] >= 20, "start_disk_gate_too_weak")
    _require(stop["disk_free_gb_min"] >= 30 and stop["disk_free_percent_min"] >= 15, "stop_disk_gate_too_weak")
    _require(start["available_memory_gb_min_8b"] >= 45, "start_memory_gate_too_weak_for_8b")
    _require(stop["available_memory_gb_min"] >= 10, "stop_memory_gate_too_weak")
    _require(start["gpu_utilization_percent_max"] <= 80 and stop["gpu_utilization_percent_max"] <= 90, "gpu_gate_mismatch")
    _require(resources["monitor"]["background"] is True, "long_task_requires_background_monitor")
    _require(resources["monitor"]["heartbeat_interval_seconds"] <= 300, "heartbeat_interval_too_long")
    _require(resources["monitor"]["process_reconciliation"] is True, "process_reconciliation_required")

    estimates = config.get("planning_estimates")
    _require(isinstance(estimates, dict), "missing_estimates")
    _require(estimates.get("measurement_status") == "ESTIMATE_NOT_MEASURED", "estimate_must_be_unmeasured")
    _require(estimates.get("external_api_calls") == 0, "external_api_calls_must_be_zero")
    _require(estimates.get("external_api_cost") == 0, "external_api_cost_must_be_zero")

    packages = resources["current_snapshot"].get("packages", {})
    _require(set(packages) == REQUIRED_DEPENDENCIES, "dependency_inventory_mismatch", actual=sorted(packages))
    missing = sorted(name for name, present in packages.items() if not present)
    model_revision = config["model_family"]["model_revision"]
    revision_ready = isinstance(model_revision, str) and len(model_revision) == 64 and model_revision != "PENDING_MODEL_GO_SHA256"
    return {
        "record_type": "stage_d_training_readiness_validation",
        "record_version": "stage-d-training-readiness-validation-v1",
        "status": "PASS_DRY_RUN_ONLY",
        "training_execution_status": "BLOCKED_PENDING_MODEL_GO_DEPENDENCIES_AND_DATA_GATES",
        "training_execution_authorized": False,
        "model_revision_ready": revision_ready,
        "missing_dependencies": missing,
        "launch_conditions": config["launch_conditions"],
        "planning_estimates": estimates,
        "config_sha256": _sha256(config_path),
        "paper_result": False,
        "data_go": False,
        "phase2_status": "NOT_RUN",
        "training_status": "NOT_RUN",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Stage D training readiness without model loading")
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = validate(args.config)
    args.output.write_text(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
