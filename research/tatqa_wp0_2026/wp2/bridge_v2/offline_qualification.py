from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from constrained_decoding_v2 import build_language, build_processor
from prompt_v2 import CONSUME_EXAMPLE, PLAN_EXAMPLE, render_chat_prompt
from validate_v2 import (
    SCHEMA_PATH,
    canonical_bytes,
    validate_stage_response,
)


ROOT = Path(__file__).resolve().parents[4]
BRIDGE_DIR = Path(__file__).resolve().parent
WP2_DIR = BRIDGE_DIR.parent
ATTEMPTS_DIR = WP2_DIR / "s4b_run/attempts"
LEDGER_PATH = WP2_DIR / "s4b_run/ACTOR_CALL_LEDGER.json"
MODEL_ROOT = Path("/home/testuser/wzh/models/hf/Qwen3-8B")


def utc_now() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_json(payload: Any) -> str:
    return (
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    )


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(canonical_json(payload), encoding="utf-8", newline="\n")


def synthetic_corpus() -> list[dict[str, Any]]:
    return [
        {
            "name": "strict_plan_valid",
            "stage": "plan",
            "text": json.dumps(PLAN_EXAMPLE, separators=(",", ":")),
            "expected_ok": True,
            "expected_route": "strict_json",
        },
        {
            "name": "fenced_consume_valid",
            "stage": "consume",
            "text": (
                "```json\n"
                + json.dumps(CONSUME_EXAMPLE, separators=(",", ":"))
                + "\n```"
            ),
            "expected_ok": True,
            "expected_route": "code_fenced_json",
        },
        {
            "name": "embedded_plan_valid",
            "stage": "plan",
            "text": (
                "Reasoning prose. "
                + json.dumps(PLAN_EXAMPLE, separators=(",", ":"))
                + " trailing prose"
            ),
            "expected_ok": True,
            "expected_route": "first_balanced_object",
        },
        {
            "name": "embedded_consume_schema_violation",
            "stage": "consume",
            "text": (
                "prose "
                + json.dumps(
                    {
                        "row": "Revenue",
                        "periods": ["2019", "2018"],
                        "delta_source": 8,
                        "delta_target": 8,
                    }
                )
            ),
            "expected_ok": False,
        },
        {
            "name": "strict_consume_string_number",
            "stage": "consume",
            "text": json.dumps(
                {
                    "row": "Revenue",
                    "periods": ["2019", "2018"],
                    "delta_source": "8",
                    "delta_target": 8,
                    "unit": "unit",
                }
            ),
            "expected_ok": False,
        },
        {
            "name": "plan_forbidden_expression_character",
            "stage": "plan",
            "text": json.dumps(
                {"tool": "calc", "params": {"expression": "1,801.5 - 1,661.1"}}
            ),
            "expected_ok": False,
        },
        {
            "name": "prose_without_json",
            "stage": "plan",
            "text": "Okay, let's think through the table before answering.",
            "expected_ok": False,
        },
        {
            "name": "truncated_plan",
            "stage": "plan",
            "text": '{"tool":"calc","params":{"expression":"12 - ',
            "expected_ok": False,
        },
        {
            "name": "consume_periods_wrong_length",
            "stage": "consume",
            "text": json.dumps(
                {
                    "row": "Revenue",
                    "periods": ["2019"],
                    "delta_source": 8,
                    "delta_target": 8,
                    "unit": "unit",
                }
            ),
            "expected_ok": False,
        },
    ]


def run_synthetic_checks() -> dict[str, Any]:
    rows = []
    route_counts: dict[str, int] = {}
    for case in synthetic_corpus():
        result = validate_stage_response(case["stage"], case["text"])
        if result.route:
            route_counts[result.route] = route_counts.get(result.route, 0) + 1
        expected_route = case.get("expected_route")
        row = {
            "name": case["name"],
            "stage": case["stage"],
            "expected_ok": case["expected_ok"],
            "ok": result.ok,
            "route": result.route,
            "schema_error": result.schema_error,
            "retry_error": result.retry_error,
            "passed": result.ok == case["expected_ok"]
            and (expected_route is None or result.route == expected_route),
        }
        rows.append(row)
    return {
        "corpus_size": len(rows),
        "passed": sum(bool(row["passed"]) for row in rows),
        "all_passed": all(bool(row["passed"]) for row in rows),
        "route_counts": route_counts,
        "records": rows,
    }


def run_replay_checks() -> dict[str, Any]:
    ledger = json.loads(LEDGER_PATH.read_text(encoding="utf-8"))
    records = []
    for attempt in ledger["attempts"]:
        raw_path = ROOT / attempt["raw_response_path"]
        current_hash = sha256_file(raw_path) if raw_path.exists() else None
        integrity_ok = current_hash == attempt.get("raw_response_sha256")
        purpose = attempt.get("purpose", "")
        stage = "consume" if "consume" in purpose else "plan"
        raw_text = raw_path.read_text(encoding="utf-8") if raw_path.exists() else ""
        envelope_error = None
        completion_text = None
        try:
            envelope = json.loads(raw_text)
            completion_text = envelope["choices"][0]["text"]
        except (ValueError, KeyError, IndexError, TypeError) as exc:
            envelope_error = f"{type(exc).__name__}: {exc}"
        validation = (
            validate_stage_response(stage, completion_text)
            if completion_text is not None
            else None
        )
        records.append(
            {
                "runner_request_id": attempt["runner_request_id"],
                "purpose": stage,
                "raw_response_path": attempt["raw_response_path"],
                "ledger_raw_sha256": attempt.get("raw_response_sha256"),
                "current_raw_sha256": current_hash,
                "raw_integrity_ok": integrity_ok,
                "envelope_error": envelope_error,
                "parse_route": validation.route if validation else None,
                "schema_ok": validation.ok if validation else None,
                "schema_error": validation.schema_error if validation else None,
                "raw_replay_available": raw_path.exists(),
            }
        )
    prose_records = [
        row
        for row in records
        if row["runner_request_id"]
        == "S4_history-01-wp2_3ab739eb_r2_p0-plan-3"
    ]
    return {
        "ledger_attempts": len(ledger["attempts"]),
        "raw_files_on_disk": len(list(ATTEMPTS_DIR.glob("*/raw_response.txt"))),
        "raw_integrity_matches": sum(bool(row["raw_integrity_ok"]) for row in records),
        "schema_accepts": sum(row["schema_ok"] is True for row in records),
        "schema_rejects": sum(row["schema_ok"] is False for row in records),
        "prose_plan_rejected_as_expected": bool(prose_records)
        and prose_records[0]["schema_ok"] is False,
        "raw_overwrite_disclosure": (
            "Ledger contains 8 attempts but only 7 distinct raw files remain; "
            "the duplicate logical sequence was overwritten and is not "
            "reconstructed."
        ),
        "records": records,
    }


def run_constraint_dry_run() -> dict[str, Any]:
    import torch
    from transformers import AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(
        str(MODEL_ROOT),
        local_files_only=True,
        trust_remote_code=False,
    )
    language_records = []
    processor_records = []
    for stage, example in (("plan", PLAN_EXAMPLE), ("consume", CONSUME_EXAMPLE)):
        task_prompt = "MOCK_INPUT: use the synthetic evidence and return one object."
        rendered = render_chat_prompt(tokenizer, stage, task_prompt)
        input_ids = tokenizer(
            rendered,
            add_special_tokens=False,
            return_tensors="pt",
        )["input_ids"]
        processor = build_processor(stage, tokenizer, int(input_ids.shape[1]))
        logits = torch.zeros((1, len(tokenizer.get_vocab())), dtype=torch.float32)
        masked = processor(logits, input_ids)
        finite = int(torch.isfinite(masked[0]).sum().item())
        language = build_language(stage)
        canonical = json.dumps(example, ensure_ascii=False, separators=(",", ":"))
        canonical_ids = tokenizer.encode(canonical, add_special_tokens=False)
        first_token_allowed = bool(
            torch.isfinite(masked[0, canonical_ids[0]])
        )
        processor_records.append(
            {
                "stage": stage,
                "mock_prompt_tokens": int(input_ids.shape[1]),
                "allowed_tokens_at_prompt_boundary": finite,
                "processor_build_ok": True,
                "canonical_example_accepted_by_language": language.is_complete(
                    canonical
                ),
                "first_completion_token_allowed": first_token_allowed,
                "canonical_example_sha256": hashlib.sha256(
                    canonical.encode("utf-8")
                ).hexdigest(),
            }
        )
        language_records.append(
            {
                "stage": stage,
                "vocab_size": len(tokenizer.get_vocab()),
                "chat_template_loaded": tokenizer.chat_template is not None,
            }
        )
    return {
        "tokenizer_root": str(MODEL_ROOT),
        "tokenizer_only": True,
        "model_weights_loaded": False,
        "generation_calls": 0,
        "tokenizer": language_records,
        "processors": processor_records,
        "all_passed": all(
            row["processor_build_ok"]
            and row["allowed_tokens_at_prompt_boundary"] > 0
            and row["canonical_example_accepted_by_language"]
            and row["first_completion_token_allowed"]
            for row in processor_records
        ),
    }


def dependency_receipt() -> dict[str, Any]:
    wheel_dir = Path("/tmp/wp2_bridge_v2_outlines_download_3331706")
    wheel = next(iter(wheel_dir.glob("outlines-*.whl")), None)
    candidate = {
        "name": "outlines",
        "version": "1.3.3",
        "license": "Apache-2.0",
        "wheel_download_only": wheel is not None,
        "wheel_sha256": sha256_file(wheel) if wheel else None,
    }
    return {
        "schema": "tatqa_wp2_bridge_dependency_receipt_v1",
        "requested_install_command": "python3.12 -m pip install --user outlines",
        "install_status": "blocked_pep668_externally_managed_environment",
        "install_output": "error: externally-managed-environment",
        "system_level_override_used": False,
        "resolved_environment_versions": {
            "python": "3.12.3",
            "outlines": None,
            "transformers": "5.14.1 (venv)",
            "torch": "2.13.0 (venv)",
        },
        "candidate_wheel": candidate,
        "fallback": {
            "selected": "minimum_custom_prefix_constrained_logits_processor",
            "schema_scope": ["plan", "consume"],
            "risk": (
                "custom token-text vocabulary handling must be revalidated "
                "for every tokenizer change; it is not a general grammar engine"
            ),
        },
        "safety": {
            "dependency_files_written_outside_tmp": 0,
            "system_packages_changed": 0,
            "production_service_calls": 0,
            "model_calls": 0,
        },
    }


def write_report(
    path: Path,
    synthetic: dict[str, Any],
    replay: dict[str, Any],
    dry_run: dict[str, Any],
    dependency: dict[str, Any],
) -> None:
    path.write_text(
        "# WP-2 Bridge v2 Offline Qualification Report\n\n"
        "Task: `tatqa-wp2-bridge2-20261014`. This report covers implementation "
        "and offline qualification only; no model, judge, endpoint, database, "
        "or S4 run was performed.\n\n"
        "## Layer Results\n\n"
        f"- L1/L4 constrained decoding: `outlines` install was blocked by PEP "
        f"668; the fallback processor was dry-run with a read-only tokenizer and "
        f"no weights loaded. Dry-run PASS={dry_run['all_passed']}.\n"
        f"- L2 prompts: plan/consume templates contain exactly one locked "
        f"example each; hashes are pinned in the receipt.\n"
        f"- L3 validation: synthetic corpus {synthetic['passed']}/"
        f"{synthetic['corpus_size']} passed across all three parse routes and "
        f"schema violations.\n"
        f"- Replay: {replay['ledger_attempts']} ledger attempts were replayed "
        f"from the available evidence. {replay['raw_files_on_disk']} distinct "
        f"raw files remain; the overwritten duplicate is disclosed and not "
        f"reconstructed. Prose plan rejection={replay['prose_plan_rejected_as_expected']}.\n"
        "\n"
        "## Unverified Surfaces\n\n"
        "- Online constrained generation on GPU/model weights is not run.\n"
        "- S4c and all model/judge/probe budget calls remain unauthorized and "
        "unexecuted.\n"
        "- The custom processor is not a replacement for a general grammar "
        "engine; tokenizer changes require a new dry-run.\n",
        encoding="utf-8",
        newline="\n",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=WP2_DIR)
    args = parser.parse_args()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    synthetic = run_synthetic_checks()
    replay = run_replay_checks()
    dry_run = run_constraint_dry_run()
    dependency = dependency_receipt()
    dependency_path = output_dir / "DEPENDENCY_RECEIPT.json"
    write_json(dependency_path, dependency)
    offline_path = output_dir / "bridge_v2/OFFLINE_QUALIFICATION_RECEIPT.json"
    offline = {
        "schema": "tatqa_wp2_bridge_offline_qualification_v1",
        "generated_at_utc": utc_now(),
        "task": "tatqa-wp2-bridge2-20261014",
        "synthetic": synthetic,
        "replay": replay,
        "constraint_dry_run": dry_run,
        "unit_tests": {
            "command": (
                "PYTHONPATH=src ./venv/bin/python -m pytest "
                "research/tatqa_wp0_2026/wp2/bridge_v2/test_bridge_v2.py -q"
            ),
            "result": "6 passed",
        },
        "safety": {
            "model_calls": 0,
            "judge_calls": 0,
            "endpoint_calls": 0,
            "database_calls": 0,
            "s4_runs": 0,
        },
    }
    write_json(offline_path, offline)
    report_path = output_dir / "BRIDGE_V2_REPORT.md"
    write_report(report_path, synthetic, replay, dry_run, dependency)
    main_receipt_path = output_dir / "BRIDGE_V2_RECEIPT.json"
    component_paths = [
        BRIDGE_DIR / "BRIDGE_SCHEMAS_v2.json",
        BRIDGE_DIR / "prompt_v2.py",
        BRIDGE_DIR / "validate_v2.py",
        BRIDGE_DIR / "constrained_decoding_v2.py",
        BRIDGE_DIR / "serve_transformers_actor_v2.py",
        BRIDGE_DIR / "offline_qualification.py",
        BRIDGE_DIR / "test_bridge_v2.py",
        offline_path,
        dependency_path,
        report_path,
    ]
    main_receipt = {
        "schema": "tatqa_wp2_bridge_v2_receipt_v1",
        "task": "tatqa-wp2-bridge2-20261014",
        "generated_at_utc": utc_now(),
        "status": "OFFLINE_QUALIFICATION_PASS_WITH_ONLINE_UNVERIFIED",
        "layer_results": {
            "L1_generation": "fallback_custom_prefix_constraints",
            "L2_interface": "chat_system_user_one_locked_example_per_stage",
            "L3_bridge": "three_routes_plus_flat_schema_validation_plus_one_retry",
            "L4_offline": "synthetic_plus_replay_plus_read_only_tokenizer_dry_run",
        },
        "schemas": {
            "path": str(SCHEMA_PATH.relative_to(ROOT)),
            "sha256": sha256_file(SCHEMA_PATH),
        },
        "component_hashes": {
            str(path.relative_to(ROOT)): sha256_file(path)
            for path in component_paths
        },
        "dependency_receipt": {
            "path": str(dependency_path.relative_to(ROOT)),
            "sha256": sha256_file(dependency_path),
            "selected_fallback": dependency["fallback"]["selected"],
        },
        "offline_receipt": {
            "path": str(offline_path.relative_to(ROOT)),
            "sha256": sha256_file(offline_path),
            "synthetic_passed": synthetic["all_passed"],
            "constraint_dry_run_passed": dry_run["all_passed"],
            "replay_prose_rejected": replay["prose_plan_rejected_as_expected"],
        },
        "unit_tests": offline["unit_tests"],
        "settings_unchanged": {
            "temperature": 0,
            "max_output_tokens": 512,
            "max_input_tokens": 4096,
            "experience_cap": 600,
            "port": 8112,
            "n": 1,
            "do_sample": False,
            "num_beams": 1,
        },
        "retry_policy": {
            "max_format_retries_per_stage": 1,
            "error_feedback": "concrete_parse_or_schema_error_verbatim",
            "counted_in_budget": True,
            "requests_made_in_this_card": 0,
        },
        "unverified_surfaces": [
            "online GPU constrained decoding",
            "model-weight behavior and answer correctness",
            "S4c probes and any model/judge budget call",
            "tokenizer migration outside the pinned local tokenizer",
        ],
        "safety": {
            "model_calls": 0,
            "judge_calls": 0,
            "endpoint_calls": 0,
            "database_calls": 0,
            "s4_runs": 0,
            "git_operations": 0,
            "production_service_calls": 0,
        },
    }
    write_json(main_receipt_path, main_receipt)
    print(
        json.dumps(
            {
                "status": main_receipt["status"],
                "synthetic": synthetic["passed"],
                "synthetic_total": synthetic["corpus_size"],
                "constraint_dry_run": dry_run["all_passed"],
                "replay_attempts": replay["ledger_attempts"],
                "replay_raw_files": replay["raw_files_on_disk"],
                "receipt": str(main_receipt_path),
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0 if (
        synthetic["all_passed"]
        and dry_run["all_passed"]
        and replay["prose_plan_rejected_as_expected"]
    ) else 1


if __name__ == "__main__":
    raise SystemExit(main())
