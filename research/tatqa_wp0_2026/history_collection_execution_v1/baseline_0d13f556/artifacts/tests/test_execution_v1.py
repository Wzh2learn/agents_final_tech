#!/usr/bin/env python3

from __future__ import annotations

import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from collection_runner import (
    CollectionRunner,
    parse_chat_response,
    render_prompt,
    validate_authorization,
)
from execution_core import (
    ExecutionBudget,
    ImmutableRawStore,
    evaluate_expression,
    parse_numeric,
    strict_json_object,
    synthetic_fixture_tasks,
    validate_consume_response,
    validate_plan_response,
)


ROOT = Path(__file__).resolve().parents[1]


def load_json(name: str) -> dict[str, Any]:
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


class FixtureAdapter:
    def __init__(self) -> None:
        self.calls = 0

    @staticmethod
    def _body(content: dict[str, Any]) -> dict[str, Any]:
        return {
            "status_code": 200,
            "content_type": "application/json",
            "elapsed_s": 0.0,
            "body_text": json.dumps({
                "id": "fixture",
                "object": "chat.completion",
                "created": 0,
                "model": "fixture",
                "choices": [{
                    "index": 0,
                    "finish_reason": "stop",
                    "message": {
                        "role": "assistant",
                        "content": json.dumps(content, separators=(",", ":")),
                    },
                }],
                "usage": {
                    "prompt_tokens": 10,
                    "completion_tokens": 5,
                    "total_tokens": 15,
                },
            }),
        }

    def complete(self, request_payload: dict[str, Any]) -> dict[str, Any]:
        self.calls += 1
        user = request_payload["messages"][-1]["content"]
        task_json = user.splitlines()[0].removeprefix("TASK_JSON=")
        task = json.loads(task_json)
        if "PLAN_OUTPUT_SCHEMA" in user:
            header, row = task["evidence"]["table_projection"]
            early_col = header.index(task["task"]["period_early"])
            late_col = header.index(task["task"]["period_late"])
            early = parse_numeric(row[early_col])
            late = parse_numeric(row[late_col])
            return self._body({
                "tool": "calc",
                "params": {"expression": f"{late} - {early}"},
            })
        tool_line = next(
            line for line in user.splitlines()
            if line.startswith("TOOL_RESULT_JSON=")
        )
        tool = json.loads(tool_line.removeprefix("TOOL_RESULT_JSON="))
        if tool["status"] != "OK":
            return self._body({
                "status": "UNKNOWN", "delta_target": None, "unit": None
            })
        return self._body({
            "status": "ANSWER",
            "delta_target": tool["returned_value"],
            "unit": task["task"]["target_unit"],
        })


class DivideZeroAdapter(FixtureAdapter):
    def complete(self, request_payload: dict[str, Any]) -> dict[str, Any]:
        self.calls += 1
        user = request_payload["messages"][-1]["content"]
        if "PLAN_OUTPUT_SCHEMA" in user:
            return self._body({
                "tool": "calc", "params": {"expression": "1/0"}
            })
        return self._body({
            "status": "UNKNOWN", "delta_target": None, "unit": None
        })


class ExecutionTests(unittest.TestCase):
    def test_manifest_and_execution_plan_are_qualified(self) -> None:
        manifest = load_json("TASK_REFERENCE_MANIFEST.json")
        plan = load_json("EXECUTION_PLAN.json")
        self.assertEqual(manifest["counts"], {
            "history": 12,
            "future_test": 16,
            "development": 4,
            "qualification_fixtures": 3,
        })
        self.assertEqual(len(manifest["tasks"]), 32)
        self.assertEqual(len(plan["request_slots"]), 54)
        self.assertEqual(len({row["request_key"] for row in plan["request_slots"]}), 54)
        self.assertTrue(all(
            row["hidden"]["reference"]["status"] == "REFERENCE_RECOMPUTED"
            for row in manifest["tasks"]
        ))
        self.assertTrue(all(
            row["qualification"]["candidate_gold_agreement"] is True
            for row in manifest["tasks"]
        ))

    def test_actor_task_has_no_hidden_identity_or_reference(self) -> None:
        manifest = load_json("TASK_REFERENCE_MANIFEST.json")
        hidden_names = (
            "source_uid", "source_cluster_id", "source_item_id",
            "selection_rank", "reference", "gold_delta_source_unit",
        )
        for row in manifest["tasks"]:
            actor_json = json.dumps(row["actor_task"], ensure_ascii=False)
            self.assertTrue(row["actor_task"]["item_id"] == row["task_id"])
            for name in hidden_names:
                self.assertNotIn(name, actor_json)
                value = row["hidden"].get(name)
                if isinstance(value, str):
                    self.assertNotIn(value, actor_json)

    def test_actor_projection_has_only_row_label_and_two_target_periods(self) -> None:
        manifest = load_json("TASK_REFERENCE_MANIFEST.json")
        for row in manifest["tasks"] + manifest["qualification_fixtures"]:
            projection = row["actor_task"]["evidence"]["table_projection"]
            self.assertEqual(len(projection), 2)
            self.assertEqual(len(projection[0]), 3)
            self.assertEqual(projection[0][0], "row")
            self.assertEqual(projection[0][1], row["actor_task"]["task"]["period_early"])
            self.assertEqual(projection[0][2], row["actor_task"]["task"]["period_late"])
            self.assertEqual(len(projection[1]), 3)
            self.assertNotIn("change", projection[0][1].lower())
            self.assertNotIn("change", projection[0][2].lower())

    def test_unit_inference_handles_header_scale_and_inherited_currency(self) -> None:
        from execution_core import infer_unit

        cases = [
            (
                {"source_unit": None, "period_early": {"col": 2, "label": "2018"},
                 "period_late": {"col": 1, "label": "2019"},
                 "table": [["£m", "2019", "2018"], ["row", "1", "2"]]},
                "currency_million",
            ),
            (
                {"source_unit": None, "period_early": {"col": 2, "label": "2018"},
                 "period_late": {"col": 1, "label": "2019"},
                 "table": [["USDm", "2019", "2018"], ["row", "1", "2"]]},
                "currency_million",
            ),
            (
                {"source_unit": None, "period_early": {"col": 2, "label": "2018"},
                 "period_late": {"col": 1, "label": "2019"},
                 "table": [["", "2019", "2018", "%Change"],
                           ["North", "$6,024,305", "$5,362,981", "12%"],
                           ["EMEA", "1,526,644", "1,530,241", "—"]]},
                "currency",
            ),
        ]
        for item, expected in cases:
            self.assertEqual(infer_unit(item)[0], expected)

    def test_safe_calculator_and_strict_schemas_reject_unsafe_or_unknown(self) -> None:
        for expression in ("True", "1 if True else 2", "__import__('os')", "1 +"):
            with self.assertRaises(ValueError):
                evaluate_expression(expression)
        with self.assertRaises(ValueError):
            evaluate_expression("1/0")
        with self.assertRaises(ValueError):
            validate_plan_response({"tool": "calc", "params": {"expression": "1-1"}, "x": 1})
        self.assertEqual(
            validate_plan_response({"tool": "calc", "params": {"expression": "1-1"}}),
            {"tool": "calc", "params": {"expression": "1-1"}},
        )
        with self.assertRaises(ValueError):
            validate_consume_response({
                "status": "UNKNOWN", "delta_target": 1, "unit": None
            })
        with self.assertRaises(ValueError):
            strict_json_object('{"a":1}\nprose')

    def test_chat_response_contract_rejects_unknown_and_usage_mismatch(self) -> None:
        good = FixtureAdapter._body({"status": "ANSWER", "delta_target": 1, "unit": "%"})
        self.assertEqual(parse_chat_response(good)["usage"]["total_tokens"], 15)
        bad = json.loads(good["body_text"])
        bad["unexpected"] = 1
        good["body_text"] = json.dumps(bad)
        with self.assertRaises(ValueError):
            parse_chat_response(good)
        bad = json.loads(FixtureAdapter._body({})["body_text"])
        bad["usage"]["total_tokens"] = 99
        raw = FixtureAdapter._body({})
        raw["body_text"] = json.dumps(bad)
        with self.assertRaises(ValueError):
            parse_chat_response(raw)

    def test_raw_store_is_immutable_and_crash_terminal(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = ImmutableRawStore(Path(tmp))
            request_id = store.begin_request("plan|H01|a1", {"x": 1})
            store.persist_response(request_id, {"x": 2})
            with self.assertRaises(FileExistsError):
                store.persist_response(request_id, {"x": 3})
            crash_id = store.begin_request("plan|H01|a2", {"x": 1})
            store.mark_crash(crash_id, "fixture crash")
            with self.assertRaises(RuntimeError):
                store.persist_response(crash_id, {"x": 2})

    def test_budget_worst_case_and_caps(self) -> None:
        budget = ExecutionBudget(54, 600000, 10240)
        for _ in range(54):
            reservation = budget.reserve()
            budget.settle(reservation, 15)
        with self.assertRaises(RuntimeError):
            budget.reserve()
        self.assertEqual(budget.snapshot()["requests"], 54)
        self.assertEqual(budget.snapshot()["actual_tokens"], 810)
        with self.assertRaises(ValueError):
            ExecutionBudget(55, 500000, 10240)

    def test_authorization_gate_precedes_adapter_and_binds_bundle_window(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bundle = Path(tmp) / "bundle.json"
            bundle.write_text('{"x":1}\n', encoding="utf-8")
            valid = {
                "schema": "collection_execution_authorization_v1",
                "authorization_id": "auth-test",
                "mode": "SINGLE_COLLECTION_RUN",
                "bundle_sha256": __import__("hashlib").sha256(bundle.read_bytes()).hexdigest(),
                "window_start_utc": "2026-10-19T12:00:00Z",
                "window_end_utc": "2026-10-19T13:30:00Z",
                "timezone": "Asia/Shanghai",
                "request_cap": 54,
                "token_cap": 600000,
                "retry_cap": 0,
                "concurrency": 1,
                "allow_model_requests": True,
                "owner_decision_reference": "owner-test",
            }
            now = datetime(2026, 10, 19, 12, 30, tzinfo=timezone.utc)
            self.assertEqual(
                validate_authorization(valid, bundle, now)["authorization_id"],
                "auth-test",
            )
            invalid = dict(valid, allow_model_requests=False)
            with self.assertRaises(PermissionError):
                validate_authorization(invalid, bundle, now)
            outside = datetime(2026, 10, 19, 14, 0, tzinfo=timezone.utc)
            with self.assertRaises(PermissionError):
                validate_authorization(valid, bundle, outside)

    def test_runner_integrates_budget_raw_plan_tool_consume_without_external_calls(self) -> None:
        manifest = load_json("TASK_REFERENCE_MANIFEST.json")
        execution_plan = load_json("EXECUTION_PLAN.json")
        runtime_identity = load_json("RUNTIME_IDENTITY_SNAPSHOT.json")
        plan_prompt = load_json("PROMPT_PLAN.json")
        consume_prompt = load_json("PROMPT_CONSUME.json")
        adapter = FixtureAdapter()
        with tempfile.TemporaryDirectory() as tmp:
            runner = CollectionRunner(
                root=ROOT,
                manifest=manifest,
                execution_plan=execution_plan,
                runtime_identity=runtime_identity,
                plan_prompt=plan_prompt,
                consume_prompt=consume_prompt,
                adapter=adapter,
                raw_root=Path(tmp),
            )
            result = runner.run()
            self.assertEqual(adapter.calls, 54)
            self.assertEqual(result["budget"]["requests"], 54)
            self.assertEqual(result["budget"]["actual_tokens"], 810)
            self.assertEqual(len(result["results"]), 27)
            self.assertTrue(all(
                row["feedback_category"] == "SUCCESS" for row in result["results"]
            ))
            raw_dirs = [path for path in Path(tmp).iterdir() if path.is_dir()]
            self.assertEqual(len(raw_dirs), 54)
            source_uids = {
                row["hidden"]["source_uid"] for row in manifest["tasks"]
                if row["bucket"] == "history"
            }
            for raw_dir in raw_dirs:
                request_payload = json.loads(
                    (raw_dir / "request.json").read_text(encoding="utf-8")
                )["request"]
                request_json = json.dumps(request_payload, ensure_ascii=False)
                self.assertNotIn("hidden_reference", request_json)
                self.assertNotIn("source_cluster_id", request_json)
                for uid in source_uids:
                    self.assertNotIn(uid, request_json)
            followup_payloads = [
                json.loads((path / "request.json").read_text(encoding="utf-8"))
                for path in raw_dirs
                if "a2" in path.name
            ]
            self.assertTrue(any(
                "SUCCESS_EXECUTION_RECHECK" in json.dumps(row["request"])
                for row in followup_payloads
            ))

    def test_runner_contains_divide_by_zero_and_completes_all_slots(self) -> None:
        manifest = load_json("TASK_REFERENCE_MANIFEST.json")
        execution_plan = load_json("EXECUTION_PLAN.json")
        runtime_identity = load_json("RUNTIME_IDENTITY_SNAPSHOT.json")
        adapter = DivideZeroAdapter()
        with tempfile.TemporaryDirectory() as tmp:
            runner = CollectionRunner(
                root=ROOT,
                manifest=manifest,
                execution_plan=execution_plan,
                runtime_identity=runtime_identity,
                plan_prompt=load_json("PROMPT_PLAN.json"),
                consume_prompt=load_json("PROMPT_CONSUME.json"),
                adapter=adapter,
                raw_root=Path(tmp),
            )
            result = runner.run()
            self.assertEqual(adapter.calls, 54)
            self.assertEqual(result["budget"]["requests"], 54)
            self.assertEqual(len(result["results"]), 27)
            self.assertTrue(all(
                row["tool_result"]["status"] == "TOOL_ERROR" and
                row["tool_result"]["error"] == "INVALID_PLAN"
                for row in result["results"]
            ))
            self.assertEqual(len([path for path in Path(tmp).iterdir() if path.is_dir()]), 54)

    def test_prompt_rendering_is_bounded_and_rejects_unresolved_placeholders(self) -> None:
        prompt = load_json("PROMPT_PLAN.json")
        messages = render_prompt(prompt, {
            "ACTOR_TASK_JSON": '{"item_id":"X01"}',
            "CORRECTION_CONTEXT_JSON": '{"mode":"INITIAL_ATTEMPT"}',
        })
        self.assertEqual(len(messages), 2)
        self.assertNotIn("{{", messages[1]["content"])
        with self.assertRaises(ValueError):
            render_prompt(prompt, {"ACTOR_TASK_JSON": "{}"})

    def test_synthetic_fixtures_have_independent_recomputed_references(self) -> None:
        fixtures = synthetic_fixture_tasks()
        self.assertEqual(len(fixtures), 3)
        self.assertEqual(
            [row["hidden"]["reference"]["status"] for row in fixtures],
            ["REFERENCE_RECOMPUTED"] * 3,
        )


if __name__ == "__main__":
    unittest.main()
