#!/usr/bin/env python3

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from diagnostic_runner import b0_decision, render_diagnostic_prompt, run_task
from execution_core import ExecutionBudget, ImmutableRawStore, parse_numeric
from collection_runner import RequestWindow


ROOT = Path(__file__).resolve().parents[1]


class StubAdapter:
    def __init__(self) -> None:
        self.calls = 0

    @staticmethod
    def response(content: dict) -> dict:
        return {
            "status_code": 200,
            "content_type": "application/json",
            "elapsed_s": 0,
            "body_text": json.dumps({
                "choices": [{"message": {"role": "assistant", "content": json.dumps(content)}}],
                "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
            }),
        }

    def complete(self, payload: dict) -> dict:
        self.calls += 1
        user = payload["messages"][-1]["content"]
        if "TOOL_RESULT_JSON=" not in user:
            task = json.loads(user.splitlines()[0].removeprefix("TASK_JSON="))
            header, row = task["evidence"]["table_projection"]
            early = parse_numeric(row[header.index(task["task"]["period_early"])])
            late = parse_numeric(row[header.index(task["task"]["period_late"])])
            return self.response({"tool": "calc", "params": {"expression": f"{late} - {early}"}})
        tool = json.loads(
            next(line for line in user.splitlines() if line.startswith("TOOL_RESULT_JSON="))
            .removeprefix("TOOL_RESULT_JSON=")
        )
        task = json.loads(user.splitlines()[0].removeprefix("TASK_JSON="))
        return self.response({
            "status": "ANSWER",
            "delta_target": tool["returned_value"],
            "unit": task["task"]["target_unit"],
        })


class DiagnosticRunnerTests(unittest.TestCase):
    def test_b0_branch_gates(self) -> None:
        success = [{"trajectory_complete": True, "outcome": "SUCCESS", "source_cluster_id": f"c{i}"} for i in range(16)]
        self.assertEqual(b0_decision(success)[0], "CEILING_ON_THIS_PANEL")
        limited = success[:15] + [{"trajectory_complete": True, "outcome": "WRONG_ANSWER", "source_cluster_id": "c15"}]
        self.assertEqual(b0_decision(limited)[0], "LIMITED_HEADROOM")
        headroom = success[:13] + [
            {"trajectory_complete": True, "outcome": "WRONG_ANSWER", "source_cluster_id": "c13"},
            {"trajectory_complete": True, "outcome": "UNKNOWN", "source_cluster_id": "c14"},
            {"trajectory_complete": True, "outcome": "REFUSED", "source_cluster_id": "c15"},
        ]
        self.assertEqual(b0_decision(headroom)[0], "CONTINUE_STAGE_THREE")
        incomplete = success[:15] + [{"trajectory_complete": False, "outcome": "INCOMPLETE_RECORD", "source_cluster_id": "c15"}]
        self.assertEqual(b0_decision(incomplete)[0], "TECHNICAL_INVALID_STOP")

    def test_b0_message_has_no_extra_context_and_run_is_traceable(self) -> None:
        plan_prompt = json.loads((ROOT / "reuse_opportunity_v1" / "DIAGNOSTIC_PLAN_PROMPT.json").read_text())
        consume_prompt = json.loads((ROOT / "reuse_opportunity_v1" / "DIAGNOSTIC_CONSUME_PROMPT.json").read_text())
        schemas = json.loads((ROOT / "OUTPUT_SCHEMAS.json").read_text())
        messages = render_diagnostic_prompt(plan_prompt, {"task": {}}, None, None, None, schemas)
        self.assertIn("EXTRA_CONTEXT_JSON=null", messages[1]["content"])
        self.assertNotIn("experience_id", messages[1]["content"])

        manifest = json.loads((ROOT / "reuse_opportunity_v1" / "REUSE_DIAGNOSTIC_PROTOCOL.json").read_text())
        task = json.loads((ROOT / "pilot_prep_v1" / "PILOT_TASK_REFERENCE_MANIFEST_V2.json").read_text())["tasks"][0]
        runtime = json.loads((ROOT / "RUNTIME_IDENTITY_SNAPSHOT.json").read_text())
        with tempfile.TemporaryDirectory() as tmp:
            budget = ExecutionBudget(128, 1700000, 12288)
            clock = {"now": __import__("datetime").datetime(2026, 10, 19, 12, 0, tzinfo=__import__("datetime").timezone.utc)}
            request_window = RequestWindow(
                __import__("datetime").datetime(2026, 10, 19, 11, 0, tzinfo=__import__("datetime").timezone.utc),
                __import__("datetime").datetime(2026, 10, 19, 14, 0, tzinfo=__import__("datetime").timezone.utc),
                120,
                lambda: clock["now"],
            )
            result = run_task(
                task, "B0", None, manifest, runtime, plan_prompt, consume_prompt, schemas,
                StubAdapter(), budget, ImmutableRawStore(Path(tmp)), request_window,
            )
            self.assertEqual(result["outcome"], "SUCCESS")
            self.assertEqual(result["arm"], "B0")
            self.assertEqual(result["source_cluster_id"], task["hidden"]["source_cluster_id"])
            self.assertEqual(budget.snapshot()["requests"], 2)


if __name__ == "__main__":
    unittest.main()
