"""Recovery contracts: fake/local only, never a model endpoint."""
import copy
from contextlib import contextmanager
import importlib.util
import io
import json
import os
from pathlib import Path
import socket
import struct
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "research/agent_frontier_portfolio_20261029/run_alfworld_recovery_20261106.py"
spec = importlib.util.spec_from_file_location("recovery_contract", SCRIPT)
r = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r)
CORE, BRIDGE = r.actor(), r.bridge()


def state(count, observation="public observation"):
    return {"observation": observation, "score": 0.0, "done": False, "won": False,
            "action_count": count, "admissible_commands": ["look", "inventory"]}


@contextmanager
def fixture(source_id="clean2_history_v2"):
    with tempfile.TemporaryDirectory() as tmp:
        qual = Path(tmp)
        source_root = qual / "frozen_source"
        source_root.mkdir()
        game_id = "heat_2" if source_id == "heat2_history_v1" else "clean_2"
        pool = qual / "pool.json"
        pool.write_text(json.dumps({"games": [{"id": game_id, "layout": 7}]}))
        pool_binding = {"path": str(pool), "sha256": r.sha(pool)}
        game = qual / "private_game.tw-pddl"
        game.write_bytes(b"unit private asset")
        selected = {"game_path": str(game), "sha256_game": r.sha(game)}
        caps = dict(CORE.CAP_LIMITS)
        reset = state(0, "Your task is to: clean a kettle. Public reset.")
        steps = [{"event": "step", "action": "look", "state": state(1, "You hold a mug.")},
                 {"event": "step", "action": "inventory", "state": state(2, "Inventory: mug 1.")}]
        m = {"game_id": game_id, "seed": 17, "backend": "student8b", "student_enable_thinking": False,
             "caps": caps, "pool_binding": pool_binding, "game_sha256": r.sha(game)}
        (source_root / "manifest.json").write_text(json.dumps(m))
        receipt = {"manifest_sha256": r.sha(source_root / "manifest.json"), "status": "RETURNED", "won": False,
                   "world_actions": 2, "model_posts": 4, "model_request_payload_bytes": 100,
                   "model_response_wire_bytes": 200, "elapsed_seconds": 2.6, "final_world_state": steps[-1]["state"]}
        (source_root / "receipt.json").write_text(json.dumps(receipt))
        events = [{"event": "episode", "hidden_facts": "NEVER_EXPORT"}, {"event": "reset", "state": reset},
                  steps[0], {"event": "rejected_tool", "action": "INVALID", "error": "invalid_request"}, steps[1]]
        (source_root / "execute_world.jsonl").write_text("\n".join(json.dumps(x) for x in events) + "\n")
        request = source_root / "requests/00001.json"
        request.parent.mkdir()
        request.write_text(json.dumps({"incoming": {"messages": [{"role": "system", "content": "SDK fixture"},
                 {"role": "user", "content": "old task"}], "tools": [{"function": {"name": "bash"}}]}}))
        pins = {name: r.sha(source_root / name) for name in ("manifest.json", "receipt.json", "execute_world.jsonl")}
        registry = {source_id: {"relative_root": "frozen_source", "game_id": game_id, "pins": pins}}
        binary = qual / "opencode"
        binary.write_bytes(b"fake pinned binary")
        profiles = {name: {"model_id": "qwen3-8b-qual" if name == "student8b" else "qwen38-27b-fp8",
                           "context": 32768, "output": 8192, "host": "127.0.0.1", "port": 1} for name in r.BACKENDS}
        core = SimpleNamespace(episode_caps=CORE.episode_caps, model_payload=CORE.model_payload,
            select_game=mock.Mock(return_value=(selected, pool_binding)), load_profile=mock.Mock(side_effect=lambda name: profiles[name]),
            write_new=CORE.write_new, config=CORE.config, components=mock.Mock(return_value={"cbc": "a" * 64}),
            dependencies=SimpleNamespace(verify_projection=mock.Mock()), RUNTIME_ROOT=qual / "runtime", RUNTIME_SHA="b" * 64,
            BINARY=binary, BINARY_SHA=r.sha(binary), PROFILE_PINS={name: ("profile.json", "c" * 64) for name in r.BACKENDS},
            IMAGE="owned-fixture-image", start_world=mock.Mock(return_value=((None, qual / "public"), reset, selected)),
            stop_world=mock.Mock(), records=CORE.records)
        qualifier = lambda payload: {"template_input_tokens": 100, "reserved_output_tokens": 8192,
                                    "context": 32768, "fits": True, "request_payload_sha256": "e" * 64}
        with mock.patch.multiple(r, QUAL=qual, SOURCE_REGISTRY=registry), mock.patch.object(r, "actor", return_value=core), \
                mock.patch.object(r, "bridge", return_value=BRIDGE), \
                mock.patch.object(r, "token_qualifier", return_value=({"actual_template": "d" * 64}, qualifier)):
            yield SimpleNamespace(qual=qual, source_root=source_root, pins=pins, source_id=source_id,
                                  m=m, receipt=receipt, reset=reset, steps=steps, core=core, qualifier=qualifier)


class RecoveryTests(unittest.TestCase):
    def test_two_approved_sources_exclude_rejected_tools_and_hidden_fields(self):
        for identifier in ("clean2_history_v2", "heat2_history_v1"):
            with self.subTest(identifier=identifier), fixture(identifier) as f:
                data = r.source(identifier)
                self.assertEqual(len(data["steps"]), 2)
                self.assertEqual(data["binding"]["prefix_actions"], 2)
                self.assertEqual(data["binding"]["sha256"], f.pins)
                self.assertEqual(data["binding"]["remaining_caps"], {"posts": 124, "seconds": 1797,
                                 "world_actions": 98, "model_payload_bytes_combined": 63_999_700})
                text = r.recovery_prompt(data, data["steps"][-1]["state"])
                self.assertNotIn("NEVER_EXPORT", text)
                self.assertNotIn("INVALID", text)
                self.assertEqual(text.count('"admissible_commands"'), 1)
                self.assertIn("Inventory: mug 1.", text)
                self.assertIn(f.reset["observation"], text)
                for private in (str(f.qual), "game.tw-pddl", "expert_plan", "source_experience"):
                    self.assertNotIn(private, text)

    def test_source_hash_or_nonterminal_prefix_corruption_is_rejected(self):
        with fixture() as f:
            r.source()
            for filename in f.pins:
                p = f.source_root / filename
                before = p.read_bytes()
                p.write_bytes(before + b" ")
                with self.subTest(filename=filename), self.assertRaises(ValueError):
                    r.source()
                p.write_bytes(before)
            changed = copy.deepcopy(f.receipt)
            changed["won"] = True
            p = f.source_root / "receipt.json"
            p.write_text(json.dumps(changed))
            f.pins["receipt.json"] = r.sha(p)
            with self.assertRaises(ValueError):
                r.source()
            with self.assertRaises(ValueError):
                r.source("arbitrary_private_root")

    def test_native_replay_compares_every_public_state_without_retry(self):
        with fixture() as f:
            data = r.source()
            step = mock.Mock(side_effect=[row["state"] for row in f.steps])
            current, cost = r.replay(data, f.reset, step, f.qual / "replay.jsonl")
            self.assertEqual(current, f.steps[-1]["state"])
            self.assertEqual(step.call_args_list, [mock.call("look"), mock.call("inventory")])
            self.assertEqual(cost["control_world_actions"], 2)
            lines = [json.loads(x) for x in (f.qual / "replay.jsonl").read_text().splitlines()]
            self.assertTrue(all(row["equal"] for row in lines))
            wrong = {**f.steps[0]["state"], "observation": "different state"}
            step = mock.Mock(return_value=wrong)
            with self.assertRaises(ValueError):
                r.replay(data, f.reset, step, f.qual / "mismatch.jsonl")
            self.assertEqual(step.call_count, 1)
            step.reset_mock()
            with self.assertRaises(ValueError):
                r.replay(data, {**f.reset, "action_count": 1}, step, f.qual / "badreset.jsonl")
            step.assert_not_called()

    def test_public_whitelist_and_terminal_guard_preserve_same_information(self):
        with fixture() as f:
            data = r.source()
            hidden = {**f.steps[-1]["state"], "facts": "NEVER", "expert_plan": ["SECRET"]}
            current = r.public_state(hidden)
            self.assertEqual(set(current), set(r.PUBLIC_KEYS))
            neutral = r.recovery_prompt(data, current)
            guard = r.recovery_prompt(data, current, "terminal_guard")
            self.assertEqual(guard, neutral + "\n" + r.TERMINAL_GUARD + "\n")
            self.assertIn("fresh session", neutral)
            self.assertIn("does not restore an earlier conversation", neutral)
            self.assertNotIn("SECRET", neutral)
            with self.assertRaises(ValueError):
                r.recovery_prompt(data, current, "invented_method")

    def test_remaining_caps_reject_exhaustion_bad_types_and_wall_cost(self):
        with fixture() as f:
            for change in ({"model_posts": 128}, {"world_actions": 100}, {"elapsed_seconds": 1800},
                           {"elapsed_seconds": float("nan")}, {"elapsed_seconds": -1},
                           {"model_request_payload_bytes": 64_000_000}):
                with self.subTest(change=change), self.assertRaises(ValueError):
                    r.remaining_caps(f.m, {**f.receipt, **change})

    def test_namespace_keeps_source_backend_and_attempts_separate(self):
        with fixture() as f:
            root = f.qual / "failure_recovery_v1" / f.source_id / "student8b/attempt_v1"
            r.check_root(root, "student8b", f.source_id)
            for path in (f.qual / "elsewhere", root.with_name("attempt_v0"), root.parent / "teacher27b/attempt_v1"):
                with self.subTest(path=path), self.assertRaises(ValueError):
                    r.check_root(path, "student8b", f.source_id)
            with self.assertRaises(ValueError):
                r.check_root(root, "teacher27b", f.source_id)

    def test_preflight_arms_replay_same_state_caps_prompt_and_freeze_native_templates(self):
        with fixture() as f, mock.patch.object(r.subprocess, "check_output", return_value="sha256:owned-image"), \
                mock.patch.object(BRIDGE, "client_step") as step, \
                mock.patch.object(socket, "create_connection", side_effect=AssertionError("no model probe")):
            prompts, caps = [], []
            for backend in r.BACKENDS:
                step.side_effect = [row["state"] for row in f.steps]
                root = f.qual / "failure_recovery_v1" / f.source_id / backend / "attempt_v1"
                manifest = r.prepare(root, backend)
                self.assertEqual(manifest["total_world_step_cap"], 100)
                self.assertEqual(manifest["caps"]["world_actions"], 98)
                self.assertEqual(f.core.start_world.call_args.args[4]["world_actions"], 100)
                self.assertEqual(manifest["planned_branch_rule"], r.BRANCH_RULE)
                self.assertEqual(manifest["prompt_mode"], "neutral")
                self.assertEqual(manifest["sampling"]["chat_template_kwargs"], {"enable_thinking": False})
                self.assertEqual(manifest["real_model_calls"], 0)
                self.assertEqual(r.verify(root, r.sha(root / "manifest.json"))[0], manifest)
                prompts.append((root / "task.txt").read_bytes())
                caps.append(manifest["caps"])
                with self.assertRaises(FileExistsError):
                    r.prepare(root, backend)
                original = (root / "manifest.json").read_bytes()
                changed = copy.deepcopy(manifest)
                changed["caps"]["posts"] -= 1
                (root / "manifest.json").write_text(json.dumps(changed))
                with self.assertRaises(ValueError):
                    r.verify(root, r.sha(root / "manifest.json"))
                (root / "manifest.json").write_bytes(original)
                (root / "task.txt").write_bytes(prompts[-1] + b"tampered")
                with self.assertRaises(ValueError):
                    r.verify(root, r.sha(root / "manifest.json"))
            self.assertEqual(prompts[0], prompts[1])
            self.assertEqual(caps[0], caps[1])
            self.assertEqual(f.core.stop_world.call_count, 2)

    def test_guard_mode_is_frozen_and_teacher_guard_rejected_before_environment(self):
        with fixture() as f, mock.patch.object(r.subprocess, "check_output", return_value="sha256:owned-image"), \
                mock.patch.object(BRIDGE, "client_step", side_effect=[row["state"] for row in f.steps]):
            root = f.qual / "failure_recovery_v1" / f.source_id / "student8b/attempt_v2"
            manifest = r.prepare(root, "student8b", prompt_mode="terminal_guard")
            self.assertEqual(manifest["prompt_mode"], "terminal_guard")
            self.assertTrue((root / "task.txt").read_text().endswith(r.TERMINAL_GUARD + "\n"))
            self.assertEqual(r.verify(root, r.sha(root / "manifest.json"))[0], manifest)
            changed = {**manifest, "prompt_mode": "neutral"}
            (root / "manifest.json").write_text(json.dumps(changed))
            with self.assertRaises(ValueError):
                r.verify(root, r.sha(root / "manifest.json"))
            f.core.start_world.reset_mock()
            with self.assertRaises(ValueError):
                r.prepare(f.qual / "unused", "teacher27b", prompt_mode="terminal_guard")
            f.core.start_world.assert_not_called()

    def test_existing_reservation_blocks_before_world_or_model(self):
        with fixture() as f:
            root = f.qual / "fresh"
            root.mkdir()
            CORE.write_new(root / "reservation.json", {"reserved": True})
            with mock.patch.object(r, "verify", return_value=({}, {}, {}, None)), \
                    mock.patch.object(socket, "create_connection") as connect:
                with self.assertRaises(FileExistsError):
                    r.run(root, "a" * 64)
                f.core.start_world.assert_not_called()
                connect.assert_not_called()

    def test_cli_execute_sha_and_overrides_are_checked_before_run(self):
        with mock.patch.object(r, "run") as run, mock.patch("sys.stderr", new_callable=io.StringIO):
            with self.assertRaises(SystemExit):
                r.main(["--execute", "--run-root", "/unused"])
            run.assert_not_called()
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            (p / "manifest.json").write_text(json.dumps({"backend": "teacher27b", "failure_source_id": "heat2_history_v1", "prompt_mode": "neutral"}))
            for flag, value in (("--backend", "student8b"), ("--failure-source", "clean2_history_v2"), ("--prompt-mode", "terminal_guard")):
                with self.subTest(flag=flag), mock.patch.object(r, "run") as run, mock.patch("sys.stderr", new_callable=io.StringIO):
                    with self.assertRaises(SystemExit):
                        r.main(["--execute", "--run-root", str(p), "--manifest-sha", "a" * 64, flag, value])
                    run.assert_not_called()

    def test_actual_token_list_not_batchencoding_key_count_and_vllm_projection_is_copy_only(self):
        self.assertEqual(len(r.input_ids({"input_ids": list(range(23)), "attention_mask": [1] * 23})), 23)
        self.assertEqual(r.input_ids([[1, 2, 3]]), [1, 2, 3])
        for invalid in ([[1], [2]], {"input_ids": "wrong"}, [True]):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                r.input_ids(invalid)
        payload = {"messages": [{"role": "assistant", "tool_calls": [{"type": "function", "function": {
            "name": "bash", "arguments": '{"command":"look"}'}}]}, {"role": "assistant", "tool_calls": []}]}
        before = copy.deepcopy(payload)
        normalized = r.template_messages(payload, "teacher27b")
        self.assertEqual(normalized[0]["tool_calls"][0]["function"]["arguments"], {"command": "look"})
        self.assertNotIn("tool_calls", normalized[1])
        self.assertEqual(payload, before)
        self.assertEqual(r.template_messages(payload, "student8b"), payload["messages"])

    def test_gguf_reader_reads_metadata_not_tensor_payload(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "fake.gguf"
            def string(value):
                raw = value.encode()
                return struct.pack("<Q", len(raw)) + raw
            p.write_bytes(b"GGUF" + struct.pack("<IQQ", 3, 999, 2) +
                          string("tokenizer.chat_template") + struct.pack("<I", 8) + string("{{ messages }}") +
                          string("tokenizer.ggml.pre") + struct.pack("<I", 8) + string("qwen2") + b"NOT A VALID TENSOR PAYLOAD")
            self.assertEqual(r.gguf_metadata(p), {"tokenizer.chat_template": "{{ messages }}", "tokenizer.ggml.pre": "qwen2"})

    def test_import_is_lazy_without_models_native_environment_or_endpoints(self):
        script = ("import importlib.util,sys; s=importlib.util.spec_from_file_location('fresh',sys.argv[1]);"
                  "m=importlib.util.module_from_spec(s);s.loader.exec_module(m);"
                  "assert not ({'torch','transformers','tokenizers','alfworld','textworld'} & set(sys.modules));"
                  "assert m._ACTOR is None and m._BRIDGE is None")
        result = subprocess.run([sys.executable, "-B", "-c", script, str(SCRIPT)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
