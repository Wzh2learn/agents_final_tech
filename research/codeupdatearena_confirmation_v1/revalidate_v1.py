"""Zero-request re-execution of CodeUpdateArena V1 generated code."""

from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from research.codeupdatearena_adapter_v2.run_adapter import (
    FINAL_REPORT_PATH,
    FINAL_RESULT_PATH,
    MODEL_LEDGER_PATH,
    V1_ROOT,
    FrozenTask,
    execute_solution_v2,
    file_hash,
    verify_docker_image,
    write_json,
    write_text,
)


def code_from_response(path: Path) -> str:
    body = json.loads(path.read_text(encoding="utf-8"))
    content = body["choices"][0]["message"]["content"]
    payload = json.loads(content)
    if set(payload) != {"code"} or not isinstance(payload["code"], str):
        raise ValueError("response_code_contract")
    return payload["code"]


def summarize(records: list[dict]) -> dict:
    arms = {}
    for arm in ("base", "update_info"):
        rows = [row for row in records if row["arm"] == arm]
        counts = Counter(row["execution"]["failure_kind"] or "all_tests_pass" for row in rows)
        arms[arm] = {
            "attempts": len(rows),
            "all_tests_pass_families": sum(row["execution"]["all_tests_pass"] for row in rows),
            "hidden_tests_passed": sum(row["execution"]["tests_passed"] for row in rows),
            "hidden_tests_total": sum(row["execution"]["test_total"] for row in rows),
            "failure_counts": dict(sorted(counts.items())),
        }
    by_id = {}
    for row in records:
        by_id.setdefault(row["prog_syn_id"], {})[row["arm"]] = row
    pairs = []
    for prog_syn_id, arm_rows in sorted(by_id.items()):
        base = arm_rows["base"]
        update = arm_rows["update_info"]
        pairs.append(
            {
                "prog_syn_id": prog_syn_id,
                "base_all_tests_pass": base["execution"]["all_tests_pass"],
                "update_info_all_tests_pass": update["execution"]["all_tests_pass"],
                "paired_all_tests_pass_difference": int(update["execution"]["all_tests_pass"])
                - int(base["execution"]["all_tests_pass"]),
                "base_passed_total_tests": [
                    base["execution"]["tests_passed"],
                    base["execution"]["test_total"],
                ],
                "update_info_passed_total_tests": [
                    update["execution"]["tests_passed"],
                    update["execution"]["test_total"],
                ],
            }
        )
    return {
        "arms": arms,
        "family_pairs": pairs,
        "paired_all_tests_pass_difference": sum(
            pair["paired_all_tests_pass_difference"] for pair in pairs
        ),
    }


def render_report(result: dict) -> str:
    metrics = result["metrics"]
    arms = metrics["arms"]
    return "\n".join(
        [
            "# CodeUpdateArena V2 Post-Hoc Execution Revalidation",
            "",
            f"- Status: `{result['status']}`",
            f"- Evidence identity: `{result['evidence_identity']}`",
            "- Model calls: `0`; this re-executes only frozen V1 generated code.",
            f"- Docker image ID: `{result['docker_identity']['id']}`",
            f"- Paired all-tests-pass difference: `{metrics['paired_all_tests_pass_difference']}`",
            f"- Base: `{arms['base']['all_tests_pass_families']}/8`, "
            f"`{arms['base']['hidden_tests_passed']}/{arms['base']['hidden_tests_total']}` tests.",
            f"- Update-info: `{arms['update_info']['all_tests_pass_families']}/8`, "
            f"`{arms['update_info']['hidden_tests_passed']}/{arms['update_info']['hidden_tests_total']}` tests.",
            "",
            "Candidate code is AST-restricted against marker forging and early exits.",
            "Each hidden test emits trusted nonce-bound start/pass/completion markers.",
            "Assertion failures are classified as test failures; pre-test failures are runtime failures.",
            "",
            "This is public synthetic execution for development, not natural production drift",
            "or a general model-capability claim.",
        ]
    ) + "\n"


def main() -> int:
    snapshot = json.loads((V1_ROOT / "TASK_SNAPSHOT.json").read_text(encoding="utf-8"))
    ledger = json.loads((V1_ROOT / "MODEL_LEDGER.json").read_text(encoding="utf-8"))
    docker_identity = verify_docker_image()
    if docker_identity["id"] != snapshot["docker_identity"]["id"]:
        raise RuntimeError("docker_image_identity_changed")
    tasks = [
        FrozenTask(index=index, row=row)
        for index, row in enumerate(snapshot["selected_rows"])
    ]
    by_prog = {task.prog_syn_id: task for task in tasks}
    records = []
    oracle = {}
    for task in tasks:
        oracle[task.prog_syn_id] = execute_solution_v2(
            task,
            str(task.row["ref_solution"]),
            "reference",
            V1_ROOT / "evidence" / "v2_oracle" / task.slug,
            docker_identity["id"],
        )
        if not oracle[task.prog_syn_id]["all_tests_pass"]:
            raise RuntimeError(f"oracle_failed:{task.prog_syn_id}")
    for index, row in enumerate(ledger["records"], start=1):
        task = by_prog[row["prog_syn_id"]]
        response_path = V1_ROOT / row["raw_response"]
        code = code_from_response(response_path)
        execution = execute_solution_v2(
            task,
            code,
            "candidate",
            V1_ROOT / "evidence" / "v2_revalidation" / f"attempt_{index:02d}_{row['arm']}",
            docker_identity["id"],
        )
        records.append(
            {
                "attempt_index": index,
                "arm": row["arm"],
                "prog_syn_id": row["prog_syn_id"],
                "code_sha256": hashlib.sha256(code.encode("utf-8")).hexdigest(),
                "source_response_sha256": file_hash(response_path),
                "execution": execution,
            }
        )
    metrics = summarize(records)
    decision = (
        "BOUNDED_NEGATIVE_STOP"
        if metrics["paired_all_tests_pass_difference"] < 2
        else "PROCEED_TO_CROSS_MODEL"
    )
    result = {
        "schema": "codeupdatearena_adapter_posthoc_revalidation_v2",
        "evidence_identity": "POST_HOC_EXECUTION_REVALIDATION_PUBLIC_SYNTHETIC",
        "model_calls": 0,
        "v1_model_calls_reused": 16,
        "source": {
            "v1_result_sha256": file_hash(V1_ROOT.parent / "research_portfolio_v2" / "CODEUPDATEARENA_ADAPTER_RESULT.json"),
            "v1_snapshot_sha256": file_hash(V1_ROOT / "TASK_SNAPSHOT.json"),
            "v1_ledger_sha256": file_hash(V1_ROOT / "MODEL_LEDGER.json"),
        },
        "docker_identity": docker_identity,
        "oracle": oracle,
        "records": records,
        "metrics": metrics,
        "decision": decision,
        "status": "COMPLETE_ZERO_REQUEST_REVALIDATION",
    }
    write_json(MODEL_LEDGER_PATH, {
        "schema": "codeupdatearena_adapter_revalidation_ledger_v2",
        "model_calls": 0,
        "reused_generation_records": len(records),
        "docker_image_id": docker_identity["id"],
        "records": records,
    })
    write_json(FINAL_RESULT_PATH, result)
    write_text(FINAL_REPORT_PATH, render_report(result))
    print(json.dumps({
        "status": result["status"],
        "decision": decision,
        "paired_difference": metrics["paired_all_tests_pass_difference"],
        "base_pass": metrics["arms"]["base"]["all_tests_pass_families"],
        "update_pass": metrics["arms"]["update_info"]["all_tests_pass_families"],
        "model_calls": 0,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
