#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import random
import socket
import subprocess
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


RUN_DIR = Path(__file__).resolve().parent
ROOT = next(path for path in Path(__file__).resolve().parents if (path / "src").is_dir())
PREREG = ROOT / "research/positive_repair_20261011/preregs/PR-EXP-01_prereg_v2.md"
CONTRACT = RUN_DIR / "implementation_contract.md"
CONTRACT_HASH = RUN_DIR / "implementation_contract.sha256"
PREREG_SHA256 = "41c6c3cd14b5d0dd1e00abef9bd15953ba9bf1cb1d8463910270f67b94af0cd3"
ALPHA = 0.05
CALIBRATION_FOLDS = (0, 1, 2)
HELDOUT_FOLDS = (3, 4)
N_BOOT = 2000
BOOT_SEED = 20260830
HARMFUL_EXPECTED_SHA256 = "3318ac178a0c3317ce18d69663b942e289c2668f4b604082606a549172f2ab10"
HARMFUL_LATE_HASHES = {
    "data/research/drift_v0/output/injected_tables.json": "827092cf6af2212ae334a9ad5f7b9ea12122d90ff9117353baf79bb1936e4fa9",
    "logs/graph/eval/d1_mutant_validity_audit.json": "ef1d46ed9ca1ae3832f35d2796b3a51be34c912897d68b40d73c9413d8651a2b",
    "logs/graph/eval/d2_cross_matcher_det.json": "7bb268e5da19590c9f58e71e293c3b66e4e5071f53932b41792ec8fb0ea1f146",
    "logs/graph/eval/d2_cross_matcher_embed.json": "ed3d3905e42c41ab71d4dfacc64a3609de2dd12d5e20cf9b5b363a90d29d4bbf",
    "logs/graph/eval/_w2_e16_section.json": "d02057eda97618fd57e9051babf45bf0faab3e5ba923c68cb39cafa07d6e2757",
    "logs/graph/eval/d3_matched_fpr_stage_a.json": HARMFUL_EXPECTED_SHA256,
}
RULES = (
    "edge_space_prefix",
    "edge_space_suffix",
    "internal_single_space_removed",
    "case_swap",
)

RAW_INPUT_HASHES = {
    "research/positive_repair_20261011/preregs/PR-EXP-01_prereg_v2.md": PREREG_SHA256,
    "research/positive_repair_20261011/prereg_freeze_manifest_v2.json": "b543953952c3af87b9db98f360b7d5b57d02a6dfe399cab8621c822b2b0dda5f",
    "research/positive_repair_20261011/contracts/shared_surface_freeze_v1.json": "d084e7f66cbc3f6f841683c57e97286d9a049a611d787fcb245dbea453f811a4",
    "research/positive_repair_20261011/contracts/SOURCE_LOCAL_RESPONSE_v1.md": "4c3d6f06ff49e4aa3bfd7f575c3e03d8d4c675909074d4275745c219b9240290",
    "research/positive_repair_20261011/loop_a_cards/residual_notes_v1.md": "a87758a125f9ea0625f1c3b891fa465f55929e2e01d19bc6c9f2ef7479bbb569",
    "research/positive_repair_20261011/loop_a_cards/loop_a_PR-EXP-01.md": "424bc01707bdd9aa075196725b0f35b8aa1193f923e68bc07cebfbd0b4aa71e8",
    "research/positive_repair_20261011/round_receipt_v4_hashfix.json": "7c942208c92c49fa4e54a066e7ce479b8d23a130d2dd5fadf80a6eb4fd87aa26",
    "research/positive_repair_20261011/loop_c_prereg_audit_recheck_result_raw.log": "a437792b4ff5997e18a5f2600b9778752b037173de616263431fdec6c0f7399d",
    "research/stage_e_method_revision_20261009/stage_e_matched_fpr_reanalysis.py": "f926c63d602db9ecbd2c64a8cdb0fff5850875a16ea88d386e905cc8bcb24489",
    "research/paper_d3_matched_fpr_stage_a.py": "56f0c8519236f4420a63835bf95ea6c6853bb838d94527486519a3e9482d8f9f",
    "research/paper_t1_eval_baselines.py": "01772e84efb3f579a1146c7c0b0e76f42b1e77625eee1124f901ab03b4c29f79",
    "src/biz/m1_statement_parser.py": "d4f9ed86c8d0fa466462c8132308a31bf51e7e4439042c4d147da9f99550d8a8",
    "config/eval_checkpoint_trees.json": "0931d952e40e80a930a335a3ac7180f35812000248c4f23a5f71e5a9b316bf25",
    "data/research/drift_v0/input/tatqa_tables.json": "3e7e056889c5207f6ab9ff0541e980393c658f044cce3dc5a22fedb976e64302",
    "data/research/drift_v0/output/injection_map.json": "d761240586b1597cbc02d823aa5c785a6fb6d47f112c36b705951717f64ac66e",
}

IMPLEMENTATION_HASHES = {
    "generate_null_panel.py": None,
    "check_null_panel.py": None,
    "run_pr_exp_01.py": None,
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, str(path))
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def raw_header(row: list) -> list[str]:
    return [str(value) if value is not None else "" for value in row]


def reconstruct(header: list[str], index: int, rule: str) -> list[str]:
    edited = list(header)
    value = edited[index]
    if rule == RULES[0]:
        replacement = " " + value
    elif rule == RULES[1]:
        replacement = value + " "
    elif rule == RULES[2]:
        if " " not in value:
            raise ValueError("frozen rule not applicable to record")
        replacement = value.replace(" ", "", 1)
    elif rule == RULES[3]:
        replacement = value.swapcase()
    else:
        raise ValueError(rule)
    if replacement == value:
        raise ValueError("frozen rule produced identity")
    edited[index] = replacement
    return edited


def percentile(values: list[float], p: float) -> float:
    if not values:
        raise ValueError("empty distribution")
    ordered = sorted(values)
    if len(ordered) == 1:
        return float(ordered[0])
    position = (len(ordered) - 1) * (p / 100.0)
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = position - lower
    return float(ordered[lower] * (1.0 - fraction) + ordered[upper] * fraction)


def distribution(values: list[float]) -> dict:
    if not values:
        return {"n": 0, "support": [], "positive_count": 0, "mean": None, "min": None, "max": None}
    return {
        "n": len(values),
        "support": sorted(set(values)),
        "support_size": len(set(values)),
        "positive_count": sum(value > 0 for value in values),
        "mean": round(sum(values) / len(values), 12),
        "min": min(values),
        "max": max(values),
    }


def threshold_from_scores(scores: list[float]) -> float | None:
    if not scores:
        return None
    candidates = sorted(set(scores))
    valid = [
        candidate
        for candidate in candidates
        if sum(score > candidate for score in scores) / len(scores) <= ALPHA
    ]
    return min(valid) if valid else None


def run_process(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=False)


def install_network_guard() -> None:
    real_socket = socket.socket

    class BlockedSocket(real_socket):
        def connect(self, *args, **kwargs):
            raise RuntimeError("ZERO_ENDPOINT: outbound socket attempt blocked")

        def connect_ex(self, *args, **kwargs):
            raise RuntimeError("ZERO_ENDPOINT: outbound socket attempt blocked")

    socket.socket = BlockedSocket
    socket.create_connection = lambda *args, **kwargs: (_ for _ in ()).throw(
        RuntimeError("ZERO_ENDPOINT: outbound socket attempt blocked")
    )


def verify_contract_and_inputs() -> list[str]:
    problems = []
    if not CONTRACT.is_file() or not CONTRACT_HASH.is_file():
        problems.append("INPUT_MISSING: implementation contract or hash sidecar")
        return problems
    recorded = CONTRACT_HASH.read_text(encoding="utf-8").strip().split()[0]
    if recorded != sha256(CONTRACT):
        problems.append("HASH_MISMATCH: implementation contract")
    if sha256(PREREG) != PREREG_SHA256:
        problems.append("PREREG_MISMATCH")
    for relative, expected in RAW_INPUT_HASHES.items():
        path = ROOT / relative
        if not path.is_file():
            problems.append(f"INPUT_MISSING: {relative}")
        elif sha256(path) != expected:
            problems.append(f"HASH_MISMATCH: {relative}")
    canonical = ROOT / "scripts/m1_statement_parser.py"
    rev = subprocess.run(["git", "rev-parse", "HEAD:scripts/m1_statement_parser.py"], cwd=ROOT, text=True, capture_output=True, check=False).stdout.strip()
    blob = subprocess.run(["git", "hash-object", str(canonical)], cwd=ROOT, text=True, capture_output=True, check=False).stdout.strip()
    if rev != "def5161dd17fc14345d340879174ed01e0277626" or blob != "def5161dd17fc14345d340879174ed01e0277626":
        problems.append("HASH_MISMATCH: canonicalizer git_blob identity")
    return problems


def verify_harmful_late_hashes() -> list[str]:
    problems = []
    for relative, expected in HARMFUL_LATE_HASHES.items():
        path = ROOT / relative
        if not path.is_file():
            problems.append(f"INPUT_MISSING: {relative}")
        elif sha256(path) != expected:
            problems.append(f"HASH_MISMATCH: {relative}")
    return problems


def input_hash_report(*, harmful_read: bool) -> dict:
    report = {relative: sha256(ROOT / relative) for relative in RAW_INPUT_HASHES}
    report["scripts/m1_statement_parser.py:git_blob"] = subprocess.run(
        ["git", "hash-object", str(ROOT / "scripts/m1_statement_parser.py")],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    ).stdout.strip()
    if harmful_read:
        report["logs/graph/eval/d3_matched_fpr_stage_a.json"] = sha256(
            ROOT / "logs/graph/eval/d3_matched_fpr_stage_a.json"
        )
        for relative, _expected in HARMFUL_LATE_HASHES.items():
            report[relative] = sha256(ROOT / relative)
    return report


def implementation_hash_report() -> dict:
    return {name: sha256(RUN_DIR / name) for name in IMPLEMENTATION_HASHES}


def output_hash_report(paths: list[Path]) -> dict:
    return {str(path.relative_to(RUN_DIR)): sha256(path) for path in paths if path.is_file()}


def finalize(
    *,
    start_utc: str,
    status: str,
    label: str,
    result: dict,
    metrics: dict,
    outputs: list[Path],
    unverified: list[str],
    deviations: list[str],
    phase: str,
    wall_seconds: float,
    threshold_frozen_utc: str | None = None,
    harmful_read_utc: str | None = None,
) -> Path:
    end_utc = utc_now()
    result_path = RUN_DIR / "result.json"
    write_json(result_path, result)
    outputs_to_hash = list(outputs)
    if result_path not in outputs_to_hash:
        outputs_to_hash.append(result_path)
    receipt = {
        "experiment_id": "PR-EXP-01",
        "status": status,
        "phase_reached": phase,
        "outcome_label": label,
        "claim_object": "SYNTHETIC_NULL_SUPPORT_REPAIR",
        "prereg_sha256": PREREG_SHA256,
        "implementation_contract_sha256": sha256(CONTRACT),
        "start_utc": start_utc,
        "end_utc": end_utc,
        "threshold_frozen_utc": threshold_frozen_utc,
        "harmful_semantic_read_utc": harmful_read_utc,
        "threshold_frozen_before_harmful_semantic_read": (
            threshold_frozen_utc is not None
            and harmful_read_utc is not None
            and threshold_frozen_utc <= harmful_read_utc
        ),
        "input_hashes": input_hash_report(harmful_read=harmful_read_utc is not None),
        "implementation_hashes": implementation_hash_report(),
        "output_hashes": output_hash_report(outputs_to_hash),
        "raw_metrics": metrics,
        "cost": {
            "model_calls": 0,
            "judge_calls": 0,
            "training_runs": 0,
            "service_calls": 0,
            "database_calls": 0,
            "network_calls": 0,
            "wall_seconds": round(wall_seconds, 6),
        },
        "unverified_items": unverified,
        "deviations": deviations,
    }
    receipt_path = RUN_DIR / "receipt.json"
    write_json(receipt_path, receipt)
    (RUN_DIR / "receipt.sha256").write_text(sha256(receipt_path) + "  receipt.json\n", encoding="utf-8")
    return receipt_path


def phase0_not_evaluable(start_utc: str, checker_payload: dict | None, summary: dict | None, wall_start: float) -> Path:
    result = {
        "experiment_id": "PR-EXP-01",
        "claim_object": "SYNTHETIC_NULL_SUPPORT_REPAIR",
        "outcome_label": "NOT_EVALUABLE",
        "phase0": checker_payload,
        "scoring_performed": False,
        "harmful_side_read": False,
        "reason": "Phase 0 qualification failed: empty admission or unverifiable identity",
        "original_clean_identifiability": {
            "population": "2,382 empirical clean rows",
            "support": [0],
            "status": "NOT_IDENTIFIABLE",
            "reported_separately": True,
        },
    }
    outputs = [path for path in (RUN_DIR / "generator_summary.json", RUN_DIR / "phase0_qualification.json", RUN_DIR / "panel.jsonl") if path.is_file()]
    metrics = {
        "phase0": checker_payload,
        "generator_summary": summary,
        "calibration": "not applicable: Phase 0 stopped before scoring",
        "heldout_null": "not applicable: Phase 0 stopped before scoring",
        "harmful": "not read",
        "bridge": "not applicable: no frozen threshold",
    }
    return finalize(
        start_utc=start_utc,
        status="NOT_EVALUABLE",
        label="NOT_EVALUABLE",
        result=result,
        metrics=metrics,
        outputs=outputs,
        unverified=["No scoring or harmful-side claim is made because Phase 0 failed."],
        deviations=[],
        phase="PHASE_0_STOP",
        wall_seconds=time.monotonic() - wall_start,
    )


def main() -> int:
    wall_start = time.monotonic()
    start_utc = utc_now()
    install_network_guard()
    preflight_problems = verify_contract_and_inputs()
    if preflight_problems:
        result = {
            "experiment_id": "PR-EXP-01",
            "outcome_label": "INVALID",
            "status": "HASH_MISMATCH" if any(item.startswith("HASH_MISMATCH") for item in preflight_problems) else "INPUT_MISSING",
            "problems": preflight_problems,
            "scoring_performed": False,
            "harmful_side_read": False,
        }
        receipt = finalize(
            start_utc=start_utc,
            status=result["status"],
            label="INVALID",
            result=result,
            metrics={"stop": preflight_problems},
            outputs=[],
            unverified=["Run stopped before scientific execution."],
            deviations=[],
            phase="PREFLIGHT_STOP",
            wall_seconds=time.monotonic() - wall_start,
        )
        print(receipt)
        return 2

    generator = RUN_DIR / "generate_null_panel.py"
    checker = RUN_DIR / "check_null_panel.py"
    panel = RUN_DIR / "panel.jsonl"
    generator_summary_path = RUN_DIR / "generator_summary.json"
    phase0_path = RUN_DIR / "phase0_qualification.json"
    generator_run = run_process([sys.executable, str(generator), "--out", str(panel), "--summary", str(generator_summary_path)])
    if generator_run.returncode != 0:
        payload = {"status": "FAIL", "stage": "generator", "stdout": generator_run.stdout, "stderr": generator_run.stderr}
        write_json(phase0_path, payload)
        return phase0_not_evaluable(start_utc, payload, None, wall_start)
    summary = json.loads(generator_summary_path.read_text(encoding="utf-8"))
    checker_run = run_process([sys.executable, str(checker), "--panel", str(panel), "--generator", str(generator), "--out", str(phase0_path)])
    checker_payload = json.loads(phase0_path.read_text(encoding="utf-8")) if phase0_path.is_file() else {"status": "FAIL", "stderr": checker_run.stderr}
    if checker_run.returncode != 0 or checker_payload.get("status") != "PASS" or checker_payload.get("empty_admission"):
        return phase0_not_evaluable(start_utc, checker_payload, summary, wall_start)

    sys.path.insert(0, str(ROOT / "src"))
    import biz.m1_statement_parser as mp

    d3 = load_module("pr01_runner_d3", ROOT / "research/paper_d3_matched_fpr_stage_a.py")
    tb = load_module("pr01_runner_tree", ROOT / "research/paper_t1_eval_baselines.py")
    tables = json.loads((ROOT / "data/research/drift_v0/input/tatqa_tables.json").read_text(encoding="utf-8"))
    by_uid = {row["uid"]: row for row in tables}
    records = [json.loads(line) for line in panel.read_text(encoding="utf-8").splitlines() if line.strip()]
    null_rows = []
    for record in records:
        source_header = raw_header(by_uid[record["uid"]]["table"][0])
        edited_header = reconstruct(source_header, record["cell_index"], record["rule"])
        canonical = d3.unique_canonical(source_header, mp)
        if not canonical:
            raise RuntimeError("canonicalization disappeared after Phase 0")
        h_original, _ = d3.hit_rate(source_header, canonical, mp)
        h_edited, _ = d3.hit_rate(edited_header, canonical, mp)
        flat = round((h_original - h_edited) * 10.0, 6)
        layered = round(d3.root_of(tb, h_original) - d3.root_of(tb, h_edited), 6)
        null_rows.append({**record, "flat": flat, "layered": layered})

    null_scores_path = RUN_DIR / "null_scores.jsonl"
    with null_scores_path.open("w", encoding="utf-8") as handle:
        for row in sorted(null_rows, key=lambda item: item["candidate_id"]):
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n")
    calibration_rows = [row for row in null_rows if row["fold"] in CALIBRATION_FOLDS]
    heldout_rows = [row for row in null_rows if row["fold"] in HELDOUT_FOLDS]
    if not calibration_rows or not heldout_rows:
        payload = {
            "status": "FAIL",
            "reason": "empty calibration or held-out partition after non-empty admission",
            "calibration_count": len(calibration_rows),
            "heldout_count": len(heldout_rows),
        }
        return phase0_not_evaluable(start_utc, payload, summary, wall_start)

    calibration_flat = [row["flat"] for row in calibration_rows]
    calibration_layered = [row["layered"] for row in calibration_rows]
    threshold_flat = threshold_from_scores(calibration_flat)
    threshold_layered = threshold_from_scores(calibration_layered)
    if threshold_flat is None or threshold_layered is None:
        payload = {"status": "FAIL", "reason": "threshold rule has no candidate on calibration support"}
        return phase0_not_evaluable(start_utc, payload, summary, wall_start)

    threshold_path = RUN_DIR / "threshold_freeze.json"
    threshold_payload = {
        "namespace": "PR-EXP-01_threshold_freeze_v1",
        "frozen_utc": utc_now(),
        "alpha": ALPHA,
        "comparison": "strict greater-than",
        "candidate_support": "calibration-null score support only",
        "rule": "smallest t in calibration support such that fraction(calibration score > t) <= 0.05",
        "calibration_folds": list(CALIBRATION_FOLDS),
        "heldout_folds": list(HELDOUT_FOLDS),
        "threshold_flat": threshold_flat,
        "threshold_layered": threshold_layered,
        "calibration_flat": distribution(calibration_flat),
        "calibration_layered": distribution(calibration_layered),
        "null_scores_sha256": sha256(null_scores_path),
        "panel_sha256": sha256(panel),
        "harmful_rows_parsed_before_freeze": False,
        "harmful_source_expected_sha256": HARMFUL_EXPECTED_SHA256,
    }
    write_json(threshold_path, threshold_payload)
    threshold_sha = sha256(threshold_path)
    (RUN_DIR / "threshold_freeze.sha256").write_text(threshold_sha + "  threshold_freeze.json\n", encoding="utf-8")
    os.chmod(threshold_path, 0o444)
    threshold_frozen_utc = threshold_payload["frozen_utc"]

    heldout_flat = [row["flat"] for row in heldout_rows]
    heldout_layered = [row["layered"] for row in heldout_rows]
    heldout_flat_fp = sum(score > threshold_flat for score in heldout_flat)
    heldout_layered_fp = sum(score > threshold_layered for score in heldout_layered)
    null_evaluation_path = RUN_DIR / "null_evaluation.json"
    null_evaluation = {
        "namespace": "PR-EXP-01_null_evaluation_v1",
        "threshold_freeze_sha256": threshold_sha,
        "calibration": {
            "flat": distribution(calibration_flat),
            "layered": distribution(calibration_layered),
            "support_greater_than_single_point": len(set(calibration_flat)) > 1 and len(set(calibration_layered)) > 1,
            "flat_fp_numerator": sum(score > threshold_flat for score in calibration_flat),
            "flat_denominator": len(calibration_flat),
            "layered_fp_numerator": sum(score > threshold_layered for score in calibration_layered),
            "layered_denominator": len(calibration_layered),
        },
        "heldout": {
            "flat": distribution(heldout_flat),
            "layered": distribution(heldout_layered),
            "flat_fp_numerator": heldout_flat_fp,
            "flat_denominator": len(heldout_flat),
            "flat_fpr": heldout_flat_fp / len(heldout_flat),
            "flat_exact_ci95": d3.clopper_pearson(heldout_flat_fp, len(heldout_flat), 0.95),
            "layered_fp_numerator": heldout_layered_fp,
            "layered_denominator": len(heldout_layered),
            "layered_fpr": heldout_layered_fp / len(heldout_layered),
            "layered_exact_ci95": d3.clopper_pearson(heldout_layered_fp, len(heldout_layered), 0.95),
            "fpr_contract_satisfied": (
                heldout_flat_fp / len(heldout_flat) <= ALPHA
                and heldout_layered_fp / len(heldout_layered) <= ALPHA
            ),
        },
    }
    write_json(null_evaluation_path, null_evaluation)

    injection_uids_for_bridge = {
        item["uid"]
        for item in json.loads((ROOT / "data/research/drift_v0/output/injection_map.json").read_text(encoding="utf-8"))["mapping"]
    }
    source_clean = [
        row for row in tables
        if row["uid"] not in injection_uids_for_bridge
    ]
    empirical_rows = []
    for table in source_clean:
        header = raw_header(table["table"][0])
        canonical = d3.unique_canonical(header, mp)
        if not canonical:
            continue
        h, _ = d3.hit_rate(header, canonical, mp)
        h_repeat = d3.hit_rate(header, canonical, mp)[0]
        empirical_rows.append(
            {
                "flat": round((h - h_repeat) * 10.0, 6),
                "layered": round(d3.root_of(tb, h) - d3.root_of(tb, h_repeat), 6),
            }
        )
    empirical_flat = [row["flat"] for row in empirical_rows]
    empirical_layered = [row["layered"] for row in empirical_rows]
    empirical_flat_fp = sum(score > threshold_flat for score in empirical_flat)
    empirical_layered_fp = sum(score > threshold_layered for score in empirical_layered)
    bridge_path = RUN_DIR / "bridge_report.json"
    bridge = {
        "namespace": "PR-EXP-01_bridge_report_v1",
        "noncomparability": "Explicitly non-comparable empirical-vs-synthetic read; the 2,382-row empirical clean population is not replaced.",
        "threshold_freeze_sha256": threshold_sha,
        "empirical_clean": {
            "flat_distribution": distribution(empirical_flat),
            "layered_distribution": distribution(empirical_layered),
            "flat_fp_numerator": empirical_flat_fp,
            "flat_denominator": len(empirical_flat),
            "flat_fpr": empirical_flat_fp / len(empirical_flat),
            "flat_exact_ci95": d3.clopper_pearson(empirical_flat_fp, len(empirical_flat), 0.95),
            "layered_fp_numerator": empirical_layered_fp,
            "layered_denominator": len(empirical_layered),
            "layered_fpr": empirical_layered_fp / len(empirical_layered),
            "layered_exact_ci95": d3.clopper_pearson(empirical_layered_fp, len(empirical_layered), 0.95),
        },
        "synthetic_threshold": {"flat": threshold_flat, "layered": threshold_layered},
    }
    write_json(bridge_path, bridge)

    harmful_read_utc = utc_now()
    late_hash_problems = verify_harmful_late_hashes()
    if late_hash_problems:
        raise RuntimeError("; ".join(late_hash_problems))
    harmful_corpus = d3.load_corpus()
    harmful_g1 = d3.g1_reproduce(harmful_corpus, mp, tb)
    if not harmful_g1.get("all_pass"):
        raise RuntimeError("INVALID: frozen harmful-side reproduction checks failed")
    harmful_rows = [row for row in harmful_g1["per_inj"] if row.get("class") in {"H", "HI"}]
    if len(harmful_rows) != 111:
        raise RuntimeError(f"INPUT_MISSING: expected 111 harmful pairs, found {len(harmful_rows)}")
    flat_scores = [float(row["dH10"]) for row in harmful_rows]
    layered_scores = [float(row["layer_drop"]) for row in harmful_rows]
    flat_detected = sum(score > threshold_flat for score in flat_scores)
    layered_detected = sum(score > threshold_layered for score in layered_scores)
    clusters = defaultdict(list)
    for row in harmful_rows:
        clusters[row["uid"]].append(row)
    cluster_ids = sorted(clusters)
    rng = random.Random(BOOT_SEED)
    flat_bootstrap = []
    layered_bootstrap = []
    difference_bootstrap = []
    for _ in range(N_BOOT):
        sampled_ids = [cluster_ids[rng.randrange(len(cluster_ids))] for _ in cluster_ids]
        sampled_rows = [row for uid in sampled_ids for row in clusters[uid]]
        flat_tpr = sum(float(row["dH10"]) > threshold_flat for row in sampled_rows) / len(sampled_rows)
        layered_tpr = sum(float(row["layer_drop"]) > threshold_layered for row in sampled_rows) / len(sampled_rows)
        flat_bootstrap.append(flat_tpr)
        layered_bootstrap.append(layered_tpr)
        difference_bootstrap.append(flat_tpr - layered_tpr)
    harmful_result_path = RUN_DIR / "harmful_results.json"
    harmful_result = {
        "namespace": "PR-EXP-01_harmful_results_v1",
        "threshold_freeze_sha256": threshold_sha,
        "threshold_frozen_utc": threshold_frozen_utc,
        "harmful_semantic_read_utc": harmful_read_utc,
        "source_hashes": {relative: sha256(ROOT / relative) for relative in HARMFUL_LATE_HASHES},
        "flat": {
            "numerator": flat_detected,
            "denominator": len(flat_scores),
            "tpr": flat_detected / len(flat_scores),
            "paired_cluster_bootstrap_ci95": [round(percentile(flat_bootstrap, 2.5), 6), round(percentile(flat_bootstrap, 97.5), 6)],
        },
        "layered": {
            "numerator": layered_detected,
            "denominator": len(layered_scores),
            "tpr": layered_detected / len(layered_scores),
            "paired_cluster_bootstrap_ci95": [round(percentile(layered_bootstrap, 2.5), 6), round(percentile(layered_bootstrap, 97.5), 6)],
        },
        "paired_tpr_difference": {
            "estimate": flat_detected / len(flat_scores) - layered_detected / len(layered_scores),
            "paired_cluster_bootstrap_ci95": [round(percentile(difference_bootstrap, 2.5), 6), round(percentile(difference_bootstrap, 97.5), 6)],
        },
        "bootstrap": {"replicates": N_BOOT, "seed": BOOT_SEED, "cluster_unit": "table uid", "cluster_count": len(cluster_ids)},
    }
    write_json(harmful_result_path, harmful_result)

    support_pass = null_evaluation["calibration"]["support_greater_than_single_point"]
    fpr_pass = null_evaluation["heldout"]["fpr_contract_satisfied"]
    operating_point_identifiable = support_pass and threshold_flat is not None and threshold_layered is not None
    label = "POSITIVE" if operating_point_identifiable and fpr_pass else "NULL"
    result = {
        "experiment_id": "PR-EXP-01",
        "claim_object": "SYNTHETIC_NULL_SUPPORT_REPAIR",
        "outcome_label": label,
        "phase0": checker_payload,
        "threshold_rule": {
            "alpha": ALPHA,
            "comparison": "strict greater-than",
            "calibration_folds": list(CALIBRATION_FOLDS),
            "heldout_folds": list(HELDOUT_FOLDS),
            "threshold_flat": threshold_flat,
            "threshold_layered": threshold_layered,
            "threshold_freeze_sha256": threshold_sha,
        },
        "qualification": {
            "calibration_support_greater_than_single_point": support_pass,
            "heldout_fpr_contract_satisfied": fpr_pass,
            "operating_point_identifiable": operating_point_identifiable,
            "positive_rule_satisfied": operating_point_identifiable and fpr_pass,
        },
        "calibration_nulls": null_evaluation["calibration"],
        "heldout_nulls": null_evaluation["heldout"],
        "harmful": harmful_result,
        "bridge_report": bridge,
        "original_identifiability": {
            "population": "2,382 empirical clean rows",
            "support": [0],
            "status": "NOT_IDENTIFIABLE",
            "reported_separately": True,
            "replacement_claim": None,
        },
        "scoring_performed": True,
        "harmful_side_read": True,
        "deviations": [],
    }
    post_problems = verify_contract_and_inputs() + verify_harmful_late_hashes()
    if post_problems:
        result["outcome_label"] = "INVALID"
        result["post_run_verification_failures"] = post_problems
    metrics = {
        "phase0_admitted_n": checker_payload["admitted_count_observed"],
        "calibration": null_evaluation["calibration"],
        "heldout": null_evaluation["heldout"],
        "harmful": harmful_result,
        "bridge": bridge["empirical_clean"],
        "original_clean_identifiability": result["original_identifiability"],
    }
    outputs = [
        generator_summary_path,
        phase0_path,
        panel,
        null_scores_path,
        threshold_path,
        null_evaluation_path,
        bridge_path,
        harmful_result_path,
    ]
    receipt = finalize(
        start_utc=start_utc,
        status="COMPLETED" if not post_problems else "INVALID",
        label=result["outcome_label"],
        result=result,
        metrics=metrics,
        outputs=outputs,
        unverified=["Loop C post-result independent audit is outside this Loop A execution."],
        deviations=[],
        phase="PHASE_1_COMPLETE",
        wall_seconds=time.monotonic() - wall_start,
        threshold_frozen_utc=threshold_frozen_utc,
        harmful_read_utc=harmful_read_utc,
    )
    print(json.dumps({"status": "COMPLETED" if not post_problems else "INVALID", "label": label, "receipt": str(receipt)}, sort_keys=True))
    return 0 if not post_problems else 2


if __name__ == "__main__":
    raise SystemExit(main())
