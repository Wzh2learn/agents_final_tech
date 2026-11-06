"""Deterministic data integrity/masking contracts; no model weights or endpoints."""
from contextlib import contextmanager
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "research/agent_frontier_portfolio_20261029/alfworld_correction_data_20261106.py"
spec = importlib.util.spec_from_file_location("correction_data_contract", SCRIPT)
d = importlib.util.module_from_spec(spec)
spec.loader.exec_module(d)


class Tokenizer:
    eos_token_id = 2
    chat_template = "unit HF-like template"
    mismatch = False
    empty = False

    def apply_chat_template(self, messages, *, add_generation_prompt, **kwargs):
        assert kwargs["enable_thinking"] is False and kwargs["truncation"] is False
        assert kwargs["return_dict"] is False
        context = messages if add_generation_prompt else messages[:-1]
        prefix = [3] + [100 + b for b in d.packed([context, kwargs["tools"]])] + [4]
        if add_generation_prompt:
            ids = prefix
        else:
            target = [] if self.empty else [100 + b for b in d.packed(messages[-1])]
            ids = prefix + target + [self.eos_token_id, 8]
            if self.mismatch:
                ids[0] = 9
        # Also exercise Transformers5 BatchEncoding output, not len(dict).
        return {"input_ids": ids, "attention_mask": [1] * len(ids)}

    def decode(self, ids):
        return "\n" if ids == [8] else "" if not ids else "NON_WHITESPACE"


def sse(content=None, arguments=None, reasoning=None):
    deltas = [{"role": "assistant"}]
    if reasoning is not None:
        deltas.append({"reasoning_content": reasoning})
    if arguments is not None:
        deltas += [{"tool_calls": [{"index": 0, "id": "native_call_1", "type": "function", "function": {"name": "ba", "arguments": arguments[:4]}}]},
                   {"tool_calls": [{"index": 0, "function": {"name": "sh", "arguments": arguments[4:]}}]}]
    if content is not None:
        middle = len(content) // 2
        deltas += [{"content": content[:middle]}, {"content": content[middle:]}]
    chunks = [{"choices": [{"index": 0, "delta": delta, "finish_reason": None}]} for delta in deltas]
    chunks += [{"choices": [{"index": 0, "delta": {}, "finish_reason": "tool_calls" if arguments is not None else "stop"}],
                "usage": {"prompt_tokens": 1, "completion_tokens": 2, "total_tokens": 3}}]
    return b"".join(b"data: " + d.packed(row) + b"\n\n" for row in chunks) + b"data: [DONE]\n\n"


@contextmanager
def fixture():
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        frozen_dir = base / "frozen"
        frozen_dir.mkdir()
        model = base / "local_hf"
        model.mkdir()
        (model / "config.json").write_text(json.dumps({"model_type": "qwen3", "architectures": ["Qwen3ForCausalLM"]}))
        for name in ["tokenizer.json", "tokenizer_config.json"]:
            (model / name).write_text('{}')
        messages = [{"role": "system", "content": "actual SDK system"}, {"role": "user", "content": 'current "goal"'},
                    {"role": "assistant", "content": "", "tool_calls": [{"id": "previous_call", "type": "function", "function": {"name": "bash", "arguments": '{"command":"inventory"}'}}]},
                    {"role": "tool", "tool_call_id": "previous_call", "content": "Inventory: egg 1. Real public output."}]
        request = {"messages": messages, "tools": [{"type": "function", "function": {"name": "bash", "parameters": {"type": "object"}}}],
                   "chat_template_kwargs": {"enable_thinking": False}}
        cases = []
        for backend, kind in [("teacher27b", "teacher_recovery"), ("student8b", "student_self_recovery")]:
            root = base / "cases" / backend
            (root / "requests").mkdir(parents=True)
            (root / "responses").mkdir()
            model_id = "teacher-model" if backend == "teacher27b" else "student-model"
            manifest = {"model_id": model_id}
            (root / "manifest.json").write_bytes(d.packed(manifest))
            bodies = [sse(arguments='{"command": "look"}'), sse(content="Real response won=true.")] if kind == "teacher_recovery" else [sse(content="Student recovery complete.")]
            receipts = []
            for index, body in enumerate(bodies, 1):
                (root / f"responses/{index:05}.body").write_bytes(body)
                response = {"status": 200, "complete": True, "body_bytes": len(body), "body_sha256": d.sha(root / f"responses/{index:05}.body"),
                            "usage": {"prompt_tokens": 1, "completion_tokens": 2, "total_tokens": 3}}
                (root / f"responses/{index:05}.body.receipt.json").write_bytes(d.packed(response))
                receipts.append(response)
                (root / f"requests/{index:05}.json").write_bytes(d.packed({"incoming": request, "forwarded": {**request, "model": model_id}}))
            receipt = {"qualified_real_correction": True, "status": "RETURNED", "errors": [], "model_relay_errors": [],
                       "won": True, "final_world_state": {"done": True}, "docker_exit": 0, "unknown_usage_model_posts": 0,
                       "fake_posts": 0, "model_posts": len(bodies), "forwarded_model_posts": len(bodies), "real_model_calls": len(bodies),
                       "manifest_sha256": d.sha(root / "manifest.json"), "future_confirmation_exclusion": {"game_id": "heat_2", "layout": 4},
                       "response_receipts": receipts}
            (root / "receipt.json").write_bytes(d.packed(receipt))
            (root / "raw.jsonl").write_bytes(b"frozen actual raw fixture\n")
            hashes = {name: d.sha(root / name) for name in ["manifest.json", "receipt.json", "raw.jsonl"]}
            cases.append({"backend": backend, "kind": kind, "root": str(root), "hashes": hashes,
                          "source_group": "SAME_EXPOSED_TASK_GROUP", "qualified_world_correction": True,
                          "provider_posts": len(bodies), "provider_tokens": 3 * len(bodies),
                          "future_confirmation_exclusion": {"game_id": "heat_2", "layout": 4}})
        frozen = frozen_dir / "FROZEN_MANIFEST.json"
        frozen.write_bytes(d.packed({"schema": "actual_failure_state_correction_asset_v1", "source_groups": 1,
                                    "cases": cases, "no_hidden_reference_used": True}))
        provider = base / "provider_manifest.json"
        members = [{"relative_path": p.relative_to(base).as_posix(), "bytes": p.stat().st_size, "sha256": d.sha(p)}
                   for p in sorted((base / "cases").rglob('*')) if p.is_file()]
        provider.write_bytes(d.packed({"members": members, "archive_sha256": "a" * 64}))
        tokenizer = Tokenizer()
        with mock.patch.object(d, "load_tokenizer", return_value=tokenizer):
            yield {"base": base, "frozen": frozen, "provider": provider, "model": model,
                   "cases": cases, "request": request, "tokenizer": tokenizer}


def build(f, **kwargs):
    return d.build_rows(f["frozen"], d.sha(f["frozen"]), f["model"], provider_manifest=f["provider"],
                        provider_manifest_sha=d.sha(f["provider"]), asset_root=f["base"], **kwargs)


class CorrectionDataTests(unittest.TestCase):
    def test_teacher_rows_full_context_and_only_current_completion_eos_supervised(self):
        with fixture() as f:
            bundle = build(f)
            self.assertEqual(len(bundle["rows"]), 2)
            self.assertEqual(bundle["manifest"]["source_group_count"], 1)
            for row in bundle["rows"]:
                self.assertEqual(row["source_role"], "teacher")
                self.assertEqual(row["request_messages"], f["request"]["messages"])
                self.assertEqual(row["request_tools"], f["request"]["tools"])
                self.assertTrue(all(x == -100 for x in row["labels"][:row["prompt_token_count"]]))
                d.validate_labels(row)
                self.assertEqual(row["labels"][row["assistant_end_index"]], Tokenizer.eos_token_id)
                self.assertEqual(row["labels"][-1], -100)
                self.assertEqual(row["input_ids"][-1], 8)
                self.assertTrue(row["template_adaptations"])
            self.assertIsInstance(f["request"]["messages"][2]["tool_calls"][0]["function"]["arguments"], str)

    def test_student_is_explicit_role_same_group_never_independent_family(self):
        with fixture() as f:
            combined = build(f, roles=("teacher", "student"))
            self.assertEqual(len(combined["rows"]), 3)
            self.assertEqual({row["source_role"] for row in combined["rows"]}, {"teacher", "student"})
            self.assertEqual(len({row["row_id"] for row in combined["rows"]}), 3)
            self.assertEqual(combined["manifest"]["source_group_count"], 1)
            self.assertEqual(len(build(f, roles=("student",))["rows"]), 1)

    def test_streamed_tool_arguments_join_as_valid_native_json(self):
        assistant, metadata = d.native_assistant(sse(arguments='{"command":"echo \\"quoted\\""}'))
        self.assertEqual(assistant["tool_calls"][0]["function"]["name"], "bash")
        self.assertEqual(json.loads(assistant["tool_calls"][0]["function"]["arguments"]), {"command": 'echo "quoted"'})
        self.assertEqual(metadata["finish_reason"], "tool_calls")

    def test_reasoning_is_never_a_target_and_empty_reasoning_only_is_rejected(self):
        assistant, metadata = d.native_assistant(sse(content="visible answer", reasoning="PRIVATE REASONING"))
        self.assertEqual(assistant, {"role": "assistant", "content": "visible answer"})
        self.assertEqual(metadata["ignored_reasoning_utf8_bytes"], len("PRIVATE REASONING"))
        for body in [sse(reasoning="PRIVATE REASONING"), sse(content="<think>hidden</think>answer"), sse(content=" ")]:
            with self.subTest(body=body), self.assertRaises(ValueError):
                d.native_assistant(body)

    def test_bad_args_duplicates_truncated_sse_and_missing_end_are_rejected(self):
        for body in [sse(arguments='{"command":'), sse(arguments='[]'), sse(arguments='{"x":1,"x":2}'),
                     sse(content="answer").replace(b"data: [DONE]\n\n", b""),
                     sse(content="answer").replace(b'"finish_reason":"stop"', b'"finish_reason":"length"')]:
            with self.subTest(body=body), self.assertRaises(ValueError):
                d.native_assistant(body)

    def test_token_prefix_boundary_truncation_and_zero_target_fail_closed(self):
        with fixture() as f:
            good = build(f)
            with self.assertRaises(ValueError):
                build(f, max_length=good["manifest"]["max_sequence_tokens"] - 1)
            f["tokenizer"].mismatch = True
            with self.assertRaisesRegex(ValueError, "prefix boundary"):
                build(f)
            f["tokenizer"].mismatch = False
            f["tokenizer"].empty = True
            with self.assertRaisesRegex(ValueError, "zero-target"):
                build(f)

    def test_frozen_provider_request_response_or_top_level_tampering_rejected(self):
        with fixture() as f:
            build(f)
            paths = [f["frozen"], Path(f["cases"][0]["root"]) / "requests/00001.json",
                     Path(f["cases"][0]["root"]) / "responses/00001.body"]
            frozen_sha = d.sha(f["frozen"])
            for p in paths:
                original = p.read_bytes()
                p.write_bytes(original + b" ")
                with self.subTest(path=p), self.assertRaises(ValueError):
                    d.build_rows(f["frozen"], frozen_sha, f["model"], provider_manifest=f["provider"],
                                 provider_manifest_sha=d.sha(f["provider"]), asset_root=f["base"])
                p.write_bytes(original)

    def test_semantic_case_and_complete_usage_gate_even_when_fixture_hashes_refrozen(self):
        for bad in ("errors", "usage"):
            with self.subTest(bad=bad), fixture() as f:
                case = f["cases"][0]
                root = Path(case["root"])
                receipt = json.loads((root / "receipt.json").read_text())
                if bad == "errors":
                    receipt["errors"] = [{"error": "native failure"}]
                else:
                    receipt["response_receipts"][0]["complete"] = False
                    (root / "responses/00001.body.receipt.json").write_bytes(d.packed(receipt["response_receipts"][0]))
                (root / "receipt.json").write_bytes(d.packed(receipt))
                frozen = json.loads(f["frozen"].read_text())
                frozen["cases"][0]["hashes"]["receipt.json"] = d.sha(root / "receipt.json")
                f["frozen"].write_bytes(d.packed(frozen))
                provider = json.loads(f["provider"].read_text())
                for entry in provider["members"]:
                    path = f["base"] / entry["relative_path"]
                    entry.update(bytes=path.stat().st_size, sha256=d.sha(path))
                f["provider"].write_bytes(d.packed(provider))
                with self.assertRaises(ValueError):
                    build(f)

    def test_declared_source_count_cannot_turn_same_group_into_two_sources(self):
        with fixture() as f:
            frozen = json.loads(f["frozen"].read_text())
            frozen["source_groups"] = 2
            f["frozen"].write_bytes(d.packed(frozen))
            with self.assertRaises(ValueError):
                build(f)

    def test_export_is_deterministic_never_overwrites_and_rechecks_labels(self):
        with fixture() as f:
            bundle = build(f)
            out = f["base"] / "exports/one"
            first = d.export_rows(bundle, out)
            self.assertEqual(first["rows_sha256"], d.sha(out / "rows.jsonl"))
            second = d.export_rows(bundle, f["base"] / "exports/two")
            self.assertEqual(first["rows_sha256"], second["rows_sha256"])
            self.assertEqual(first["data_manifest_sha256"], second["data_manifest_sha256"])
            with self.assertRaises(FileExistsError):
                d.export_rows(bundle, out)
            with self.assertRaises(ValueError):
                d.export_rows(bundle, Path(f["cases"][0]["root"]) / "new_data")
            corrupted = copy.deepcopy(bundle)
            corrupted["rows"][0]["labels"][0] = 123
            with self.assertRaises(ValueError):
                d.export_rows(corrupted, f["base"] / "exports/corrupted")
            self.assertFalse((f["base"] / "exports/corrupted").exists())

    def test_import_has_no_transformers_torch_or_side_effects(self):
        code = ("import importlib.util,sys; s=importlib.util.spec_from_file_location('isolated',sys.argv[1]);"
                "m=importlib.util.module_from_spec(s);s.loader.exec_module(m);"
                "assert not ({'torch','transformers','tokenizers'} & set(sys.modules))")
        with tempfile.TemporaryDirectory() as tmp:
            result = subprocess.run([sys.executable, "-B", "-c", code, str(SCRIPT)], cwd=tmp, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(list(Path(tmp).iterdir()), [])


if __name__ == "__main__":
    unittest.main()
