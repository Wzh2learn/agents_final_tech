#!/usr/bin/env python3
"""Focused deterministic recomputation for the completed TQ-5 run.

This is a Loop D verification artifact, not an independent-review claim.
It reads saved run bytes only and performs no HTTP or model calls.
"""

from __future__ import annotations

import copy
import hashlib
import json
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUN_ID = "20261017T072340Z_5d8942bd"
RUN = ROOT / "runs" / RUN_ID
RECOVERY = ROOT / "execution_v1" / "recovery_v1"
OUTPUT = ROOT / "reviews" / "TQ5_POST_RUN_RECOMPUTE_v1.json"
MASTER = ROOT.parent / "tq4_calibration_v1" / "runs" / "_chain" / "chain_master_ledger.jsonl"
AUTHORIZATION = ROOT.parent / "tq4_calibration_v1" / "run_card_v2" / "OWNER_DELEGATED_AUTHORIZATION_20261016_v1.md"

sys.path.insert(0, str(RECOVERY))
import tq4_scoring_entry_v21 as V21  # noqa: E402


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sha256_json(value) -> str:
    payload = json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def load_jsonl(path: Path) -> list[dict]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def display_decision(row: dict) -> str | None:
    if row.get("skipped"):
        return "skipped"
    if row.get("parse_error") or (row.get("decision") is None and row.get("ledger_state") == "done"):
        return "invalid"
    return row.get("decision") or row.get("ledger_state")


def verify_manifest() -> dict:
    manifest = load(RUN / "RUN_MANIFEST.json")
    expected = {item["path"]: item for item in manifest["files"]}
    actual_paths = {
        path.relative_to(RUN).as_posix()
        for path in RUN.rglob("*")
        if path.is_file() and path.name != "RUN_MANIFEST.json"
    }
    mismatches = []
    for rel, item in expected.items():
        path = RUN / rel
        if not path.is_file():
            mismatches.append({"path": rel, "error": "missing"})
            continue
        actual_hash = sha256_file(path)
        actual_bytes = path.stat().st_size
        if actual_hash != item["sha256"] or actual_bytes != item["bytes"]:
            mismatches.append({
                "path": rel,
                "expected_sha256": item["sha256"],
                "actual_sha256": actual_hash,
                "expected_bytes": item["bytes"],
                "actual_bytes": actual_bytes,
            })
    unexpected = sorted(actual_paths - set(expected))
    missing = sorted(set(expected) - actual_paths)

    snapshot = manifest["execution_snapshot"]
    snapshot_manifest_path = ROOT / snapshot["manifest_path"]
    snapshot_manifest = load(snapshot_manifest_path)
    snapshot_mismatches = []
    for item in snapshot_manifest["files"]:
        path = RECOVERY / item["path"]
        if not path.is_file():
            snapshot_mismatches.append({"path": item["path"], "error": "missing"})
            continue
        actual_hash = sha256_file(path)
        if actual_hash != item["sha256"]:
            snapshot_mismatches.append({
                "path": item["path"],
                "expected_sha256": item["sha256"],
                "actual_sha256": actual_hash,
            })
    snapshot_manifest_hash_ok = sha256_file(snapshot_manifest_path) == snapshot["manifest_sha256"]
    return {
        "run_manifest_sha256": sha256_file(RUN / "RUN_MANIFEST.json"),
        "listed_files": len(expected),
        "actual_files_excluding_manifest": len(actual_paths),
        "file_mismatches": mismatches,
        "unexpected_files": unexpected,
        "missing_files": missing,
        "snapshot_manifest_sha256": snapshot["manifest_sha256"],
        "snapshot_manifest_hash_ok": snapshot_manifest_hash_ok,
        "snapshot_files": len(snapshot["files"]),
        "snapshot_mismatches": snapshot_mismatches,
    }


def verify_run_meta() -> dict:
    meta = load(RUN / "RUN_META.json")
    expected = {
        "config_sha256": sha256_file(RECOVERY / "chain_config_tq5_frozen.json"),
        "runner_sha256": sha256_file(RECOVERY / "chain_runner.py"),
        "templates_md_sha256": sha256_file(RECOVERY / "prompt_templates_v2.md"),
        "authorization_sha256": sha256_file(AUTHORIZATION),
    }
    actual = {key: meta.get(key) for key in expected}
    return {
        "expected": expected,
        "actual": actual,
        "all_match": actual == expected,
        "resumed": meta.get("resumed"),
        "steps_total": meta.get("steps_total"),
    }


def verify_budget() -> dict:
    receipt = load(RUN / "RECEIPT.json")
    ledger = load_jsonl(RUN / "request_ledger.jsonl")
    master_all = load_jsonl(MASTER)
    master = [
        row for row in master_all
        if row.get("run_id") == RUN_ID and row.get("panel") == "TQ-5"
    ]
    reserves = [row for row in ledger if row.get("op") == "reserve"]
    settles = [row for row in ledger if row.get("op") == "settle"]
    retries = [row for row in reserves if row.get("retry")]
    settled_tokens = sum(int(row.get("settled", 0)) for row in settles)
    raw = [load(path) for path in sorted((RUN / "raw").glob("*.json"))]
    raw_tokens = sum(int(row.get("usage", {}).get("total_tokens", 0)) for row in raw)
    raw_times = [datetime.fromisoformat(row["utc"].replace("Z", "+00:00")) for row in raw]
    first_request = datetime.fromisoformat(receipt["first_request_utc"].replace("Z", "+00:00"))
    first_raw = min(raw_times).isoformat().replace("+00:00", "Z")
    last_raw = max(raw_times).isoformat().replace("+00:00", "Z")
    duration_s = int((max(raw_times) - first_request).total_seconds())
    aux = load_jsonl(RUN / "aux_ledger.jsonl")
    aux_sends = sum(1 for row in aux if row.get("op") == "aux_send")
    expected_params = {
        "temperature": 0,
        "top_p": 1,
        "seed": 20261016,
        "max_tokens": 2048,
        "stream": False,
        "response_format": {"type": "json_object"},
        "chat_template_kwargs": {"enable_thinking": False},
    }
    param_mismatches = []
    http_mismatches = []
    for row in raw:
        if row.get("request", {}).get("params") != expected_params:
            param_mismatches.append(row["item_key"])
        if not row.get("http", {}).get("ok") or row.get("http", {}).get("status") != 200 or row.get("retry"):
            http_mismatches.append(row["item_key"])

    chain_reserves = sum(1 for row in master_all if row.get("op") == "reserve")
    chain_settles = sum(1 for row in master_all if row.get("op") == "settle")
    chain_tokens = sum(int(row.get("settled", 0)) for row in master_all if row.get("op") == "settle")
    return {
        "receipt": receipt,
        "request_ledger_lines": len(ledger),
        "reserve_count": len(reserves),
        "settle_count": len(settles),
        "retry_count": len(retries),
        "settled_tokens_recomputed": settled_tokens,
        "raw_tokens_recomputed": raw_tokens,
        "master_entries_for_run": len(master),
        "master_reserve_count": sum(1 for row in master if row.get("op") == "reserve"),
        "master_settle_count": sum(1 for row in master if row.get("op") == "settle"),
        "master_matches_run": [
            {key: value for key, value in row.items() if key not in {"panel", "run_id"}}
            for row in master
        ] == [
            {key: value for key, value in row.items() if key != "utc"}
            for row in ledger
        ],
        "master_comparison_note": "DualLedger mirror adds panel/run_id and omits per-entry utc; comparison normalizes those fields.",
        "first_request_utc_receipt": receipt.get("first_request_utc"),
        "first_response_utc_recomputed": first_raw,
        "last_response_utc_recomputed": last_raw,
        "duration_s_from_first_request": duration_s,
        "aux_send_count": aux_sends,
        "parameter_mismatches": param_mismatches,
        "http_mismatches": http_mismatches,
        "chain_totals": {
            "reserve_count": chain_reserves,
            "settle_count": chain_settles,
            "settled_tokens": chain_tokens,
        },
        "within_caps": (
            len(reserves) <= 40
            and len(retries) <= 4
            and settled_tokens <= 400000
            and chain_reserves <= 80
            and chain_tokens <= 800000
            and duration_s <= 90 * 60
        ),
    }


def verify_outputs() -> dict:
    raw_by_key = {}
    for path in sorted((RUN / "raw").glob("*.json")):
        row = load(path)
        raw_by_key[row["item_key"]] = row
    stored = load(RUN / "part1_results.json")
    stored_by_task = {row["task_id"]: row for row in stored["rows"]}
    score_mismatches = []
    legality_mismatches = []
    decision_rows = []
    parse_failures = []
    actor_valid = 0
    for key, row in sorted(raw_by_key.items()):
        arm = row["arm"]
        parse = row["parse"]
        item = {"key": key, "valid": parse["valid"], "parse_error": parse.get("error")}
        if not parse["valid"]:
            parse_failures.append(copy.deepcopy(item))
            item["display_decision"] = "invalid"
            decision_rows.append(item)
            continue
        result = parse["result"]
        if arm == "actor":
            actor_valid += 1
            task_id = row["case"]
            material = load(ROOT / "panel" / "scoring" / f"{task_id}.json")
            input_data = load(ROOT / "panel" / "inputs" / f"{task_id}.json")
            scoring = V21.score(task_id, result, material)
            legality = V21.check_evidence_legality(input_data["table"], input_data["paragraphs"], result["evidence"])
            if scoring != stored_by_task[task_id]["scoring_v21"]:
                score_mismatches.append({"task_id": task_id, "expected": scoring, "stored": stored_by_task[task_id]["scoring_v21"]})
            if legality != stored_by_task[task_id]["legality_v21"]:
                legality_mismatches.append({"task_id": task_id, "expected": legality, "stored": stored_by_task[task_id]["legality_v21"]})
            item["answer"] = result["answer"]
            item["scoring_status"] = scoring["status"]
        else:
            item["decision"] = result["decision"]
            item["display_decision"] = result["decision"]
            item["contradiction_points"] = result.get("contradiction_points", [])
        decision_rows.append(item)
    score_counts = Counter(row.get("scoring_status") for row in decision_rows if row.get("scoring_status"))
    b_counts = Counter(row["display_decision"] for row in decision_rows if row["key"].startswith("b|"))
    c_counts = Counter(row["display_decision"] for row in decision_rows if row["key"].startswith("c|"))
    return {
        "raw_files": len(raw_by_key),
        "actor_valid": actor_valid,
        "score_counts": dict(sorted(score_counts.items())),
        "score_mismatches": score_mismatches,
        "legality_mismatches": legality_mismatches,
        "b_decision_counts": dict(sorted(b_counts.items())),
        "c_decision_counts": dict(sorted(c_counts.items())),
        "parse_failures": parse_failures,
        "rows": decision_rows,
    }


def verify_prompts() -> dict:
    raw_by_key = {}
    for path in sorted((RUN / "raw").glob("*.json")):
        row = load(path)
        raw_by_key[row["item_key"]] = row
    forbidden = [
        "answer_kind",
        "evidence_legality",
        "candidate_id",
        "frozen_design_target",
        "support_target",
        "injection",
        "v4_label",
        "checker_verdict",
        "correct+",
        "incorrect+",
        "perturbed",
    ]
    hash_mismatches = []
    marker_mismatches = []
    forbidden_hits = []
    c_exposure_hits = []
    prompts = sorted((RUN / "prompts").glob("*.json"))
    for path in prompts:
        row = load(path)
        messages = row["messages"]
        if sha256_json(messages) != row["messages_sha256"]:
            hash_mismatches.append(row["item_key"])
        text = json.dumps(messages, ensure_ascii=False)
        hits = [marker for marker in forbidden if marker in text]
        if hits:
            forbidden_hits.append({"item_key": row["item_key"], "markers": hits})
        arm = row["item_key"].split("|", 1)[0]
        if arm == "b" and "Candidate answer (from another system):" not in text:
            marker_mismatches.append({"item_key": row["item_key"], "missing": "b_candidate_marker"})
        if arm == "c" and "Candidate final answer:" not in text:
            marker_mismatches.append({"item_key": row["item_key"], "missing": "c_candidate_marker"})
        if arm == "actor" and ("Candidate answer (from another system):" in text or "Candidate final answer:" in text):
            marker_mismatches.append({"item_key": row["item_key"], "unexpected": "candidate_marker"})
        if arm == "c":
            actor = raw_by_key["actor|" + row["item_key"].split("|", 1)[1]]["parse"]["result"]
            exposed = []
            if json.dumps(actor["evidence"], ensure_ascii=False) in text:
                exposed.append("evidence_json")
            if actor.get("notes") and actor["notes"] in text:
                exposed.append("actor_notes")
            if exposed:
                c_exposure_hits.append({"item_key": row["item_key"], "exposed": exposed})
    return {
        "prompt_files": len(prompts),
        "message_hash_mismatches": hash_mismatches,
        "marker_mismatches": marker_mismatches,
        "forbidden_hits": forbidden_hits,
        "c_exposure_hits": c_exposure_hits,
    }


def main() -> int:
    manifest_check = verify_manifest()
    meta_check = verify_run_meta()
    budget_check = verify_budget()
    output_check = verify_outputs()
    prompt_check = verify_prompts()
    results = load(RUN / "RESULTS.json")
    corrected = load(ROOT / "reviews" / "TQ5_RESULTS_CORRECTED_v1.json")
    label = results.get("part1", {}).get("summary", {}).get("label", "")
    corrected_label = corrected.get("part1", {}).get("summary", {}).get("label", "")
    original_without_corrections = copy.deepcopy(results)
    corrected_without_corrections = copy.deepcopy(corrected)
    corrected_without_corrections["part1"]["summary"]["label"] = original_without_corrections["part1"]["summary"]["label"]
    corrected_without_corrections.pop("analysis_corrections", None)
    corrected_without_corrections.pop("source_results_sha256", None)
    result_values_unchanged = original_without_corrections == corrected_without_corrections
    original_label_expected = "旧池新增任务的受控扰动部分（非自然失败分布；无原始版对照）"
    checks = {
        "run_manifest": (
            not manifest_check["file_mismatches"]
            and not manifest_check["unexpected_files"]
            and not manifest_check["missing_files"]
        ),
        "execution_snapshot": manifest_check["snapshot_manifest_hash_ok"] and not manifest_check["snapshot_mismatches"],
        "run_meta": meta_check["all_match"] and meta_check["resumed"] is False,
        "budget_and_ledger": (
            budget_check["request_ledger_lines"] == 72
            and budget_check["reserve_count"] == 36
            and budget_check["settle_count"] == 36
            and budget_check["retry_count"] == 0
            and budget_check["settled_tokens_recomputed"] == 44867
            and budget_check["raw_tokens_recomputed"] == 44867
            and budget_check["master_entries_for_run"] == 72
            and budget_check["master_matches_run"]
            and not budget_check["parameter_mismatches"]
            and not budget_check["http_mismatches"]
            and budget_check["within_caps"]
        ),
        "outputs": (
            output_check["raw_files"] == 36
            and output_check["actor_valid"] == 12
            and not output_check["score_mismatches"]
            and not output_check["legality_mismatches"]
        ),
        "prompt_isolation": (
            prompt_check["prompt_files"] == 36
            and not prompt_check["message_hash_mismatches"]
            and not prompt_check["marker_mismatches"]
            and not prompt_check["forbidden_hits"]
            and not prompt_check["c_exposure_hits"]
        ),
        "original_analysis_label_preserved": label == original_label_expected,
        "analysis_correction": (
            "TQ-5 table-disjoint" in corrected_label
            and "not TQ-4" in corrected_label
            and corrected.get("source_results_sha256") == sha256_file(RUN / "RESULTS.json")
            and result_values_unchanged
        ),
    }
    payload = {
        "schema": "tq5_post_run_recompute_v1",
        "identity": "Loop D focused deterministic recomputation; not an independent-review claim",
        "run_id": RUN_ID,
        "checks": checks,
        "manifest": manifest_check,
        "run_meta": meta_check,
        "budget": budget_check,
        "outputs": output_check,
        "prompts": prompt_check,
        "analysis_label_observed": label,
        "analysis_label_corrected": corrected_label,
        "analysis_label_expected": "TQ-5 table-disjoint developmental source-separation panel; not TQ-4 and not pooled with TQ-4",
        "analysis_result_values_unchanged": result_values_unchanged,
        "boundaries": [
            "No model calls, HTTP, or frozen-file modification.",
            "Reference field equality and arithmetic recomputation do not establish human semantic gold.",
            "Machine NO_MATCH, semantic adjudication, and checker decisions remain separate.",
        ],
    }
    OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(OUTPUT), "checks": checks}, ensure_ascii=True))
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
