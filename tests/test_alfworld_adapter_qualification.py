"""Matched adapter harness contracts; CPU mocks, no endpoint or containers."""
import copy
from contextlib import contextmanager, ExitStack
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "research/agent_frontier_portfolio_20261029"


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


r = load("adapter_qualification_contract", "run_alfworld_adapter_qualification_20261106.py")
REC = load("adapter_frozen_recovery_contract", "run_alfworld_recovery_20261106.py")
CORE = REC.actor()
TOKENIZER_QUALIFIER = r.tokenizer_qualifier


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


def state(count, observation="public observation"):
    return {"observation": observation, "score": 0.0, "done": False, "won": False,
            "action_count": count, "admissible_commands": ["look", "inventory"]}


@contextmanager
def fixture():
    """All private paths, lifecycle calls and transport are replaced here."""
    with tempfile.TemporaryDirectory() as tmp, ExitStack() as stack:
        qual = Path(tmp).resolve()
        adapter = qual / "learning_qualification_v1/attempt_v1/adapter"
        adapter.mkdir(parents=True)
        for name in ("adapter_config.json", "adapter_model.safetensors"):
            (adapter / name).write_bytes(("fixture " + name).encode())
        hashes = {p.name: r.sha(p) for p in adapter.iterdir()}
        training = adapter.parent / "receipt.json"
        write(training, {"adapter_files": hashes})
        training_sha = r.sha(training)
        base_binding = qual / "learning_qualification_v1/HF4B_MODEL_BINDING_V1.json"
        write(base_binding, {"base": "mock-pinned-bf16-model"})
        base_binding_sha = r.sha(base_binding)
        profile_path = qual / "serving_profile.json"
        profile = {"host": "127.0.0.1", "port": 18106, "context": 16384, "output": 4096,
                   "dtype": "bfloat16", "lora_dtype": "bfloat16", "tool_parser": "hermes",
                   "native_thinking": False, "model_ids": copy.deepcopy(r.MODEL_IDS),
                   "base_binding_sha256": base_binding_sha, "training_receipt_sha256": training_sha,
                   "adapter_files": hashes, "container_name": "alf4b-adapter-owned-fixture",
                   "container_id": "owned-container-id", "image_id": "sha256:owned-image"}
        write(profile_path, profile)
        reset = state(0, "Your task is to: heat some egg and put it in diningtable.")
        steps = [{"event": "step", "action": "look", "state": state(1)},
                 {"event": "step", "action": "inventory", "state": state(2, "Inventory is empty.")}]
        caps = {"posts": 119, "seconds": 1754, "world_actions": 92,
                "model_payload_bytes_combined": 62951673}
        binding = {"sha256": {"receipt.json": "source-receipt"}, "remaining_caps": caps,
                   "game_id": "heat_2", "layout": 4, "prefix_actions": 2}
        data = {"manifest": {"game_id": "heat_2", "seed": 17, "caps": dict(CORE.CAP_LIMITS),
                             "pool_binding": {"path": "mock-private-pool", "sha256": "pool-sha"}},
                "binding": binding, "reset": reset, "steps": steps}
        instances = []

        class Relay:
            def __init__(self, *args, **kwargs):
                self.args, self.kwargs = args, kwargs
                self.budget = SimpleNamespace(posts=0)
                self.forwarded, self.errors, self.delivery = 0, [], None
                self.forward_calls, self.closed, self.closing = [], False, False
                instances.append(self)

            def forward(self, upstream, packet, payload=None, post_index=None):
                self.forward_calls.append((upstream, packet, payload, post_index))
                self.forwarded += 1
                self.budget.posts += 1
                return "FORWARDED_WITHOUT_NETWORK"

            def begin_close(self):
                self.closing = True

            def close(self):
                self.closed = True

        def start_world(root, game_id, seed, phase, *_):
            events = [{"event": "reset", "state": reset}, *steps]
            (root / (phase + "_world.jsonl")).write_text(
                "".join(json.dumps(event) + "\n" for event in events), encoding="utf-8")
            return (object(), qual / "mock-world-socket-dir"), reset, {}

        core = SimpleNamespace(config=CORE.config, model_payload=CORE.model_payload, write_new=CORE.write_new,
            start_world=mock.Mock(side_effect=start_world), stop_world=mock.Mock(), IMAGE="mock-actor-image",
            ModelRelay=Relay, GUEST="# mock guest", socket_directory=mock.Mock(return_value=qual / "mock-model-dir"),
            cleanup_directory=mock.Mock(), docker_command=mock.Mock(return_value=["mock-owned-actor"]))
        rec = SimpleNamespace(actor=lambda: core, source=mock.Mock(return_value=data),
            components=lambda: {"frozen-recovery": "fixture-component-sha"},
            replay=mock.Mock(return_value=(steps[-1]["state"], {"actions": 2, "model_posts": 0})),
            recovery_prompt=REC.recovery_prompt, bridge=lambda: SimpleNamespace(client_step=mock.Mock()),
            template_messages=REC.template_messages, input_ids=REC.input_ids)

        def qualify(payload):
            count = payload.get("token_count", 100)
            return {"input_tokens": count, "reserved_output": 4096, "context": 16384,
                    "fits": count + 4096 <= 16384, "payload_sha256": "payload-sha"}

        def inspect(argv, **_):
            if argv[:2] == ["docker", "inspect"]:
                return "owned-container-id sha256:owned-image true\n"
            if argv[:3] == ["docker", "image", "inspect"]:
                return "sha256:actor-image\n"
            raise AssertionError("unexpected process: " + repr(argv))

        stack.enter_context(mock.patch.multiple(r, QUAL=qual, TRAIN_RECEIPT_SHA=training_sha,
                                                BASE_BINDING_SHA=base_binding_sha))
        stack.enter_context(mock.patch.object(r, "recovery", return_value=rec))
        stack.enter_context(mock.patch.object(r, "components", return_value={"runner": "frozen-code"}))
        stack.enter_context(mock.patch.object(r, "tokenizer_qualifier", return_value=({"tokenizer": "pinned"}, qualify)))
        stack.enter_context(mock.patch.object(r.os, "getuid", return_value=1001, create=True))
        stack.enter_context(mock.patch.object(r.os, "getgid", return_value=1001, create=True))
        inspect_mock = stack.enter_context(mock.patch.object(r.subprocess, "check_output", side_effect=inspect))
        process = stack.enter_context(mock.patch.object(r.subprocess, "run",
            return_value=subprocess.CompletedProcess([], 0)))
        stack.enter_context(mock.patch("socket.create_connection", side_effect=AssertionError("no network in unit tests")))
        yield SimpleNamespace(qual=qual, adapter=adapter, training=training, base_binding=base_binding,
            profile_path=profile_path,
            profile=profile, core=core, rec=rec, data=data, instances=instances, process=process,
            inspect=inspect_mock, qualifier=qualify,
            root=lambda arm="base", n=1: qual / "adapter_qualification_v1/episodes" / arm / ("attempt_v" + str(n)))


def prepared(f, arm="base", n=1):
    root = f.root(arm, n)
    manifest = r.prepare(root, arm, f.profile_path, r.sha(f.profile_path))
    return root, manifest, r.sha(root / "manifest.json")


class AdapterQualificationTests(unittest.TestCase):
    def test_real_client_configs_match_but_upstream_dispatch_and_sampling_are_bound(self):
        with fixture() as f:
            base, bm, _ = prepared(f)
            trained, tm, _ = prepared(f, "trained")
            self.assertEqual((base / "opencode_config.json").read_bytes(),
                             (trained / "opencode_config.json").read_bytes())
            self.assertEqual((base / "task.txt").read_bytes(), (trained / "task.txt").read_bytes())
            cfg = json.loads((base / "opencode_config.json").read_text())
            self.assertEqual(cfg["model"], "gb10/" + r.CLIENT_ID)
            self.assertEqual(cfg["provider"]["gb10"]["models"][r.CLIENT_ID]["limit"],
                             {"context": 16384, "output": 4096})
            for m, arm in ((bm, "base"), (tm, "trained")):
                self.assertEqual(m["model_id"], r.CLIENT_ID)
                self.assertEqual(m["sampling"]["model"], r.MODEL_IDS[arm])
                self.assertEqual(m["sampling"]["chat_template_kwargs"], {"enable_thinking": False})
                self.assertEqual([m["sampling"][k] for k in ("seed", "temperature", "max_tokens")], [17, .2, 4096])
                incoming = {"model": r.CLIENT_ID, "max_tokens": 99999,
                            "chat_template_kwargs": {"enable_thinking": True}}
                forwarded = CORE.model_payload(incoming, "student8b", m["serving"], 17, False)
                self.assertEqual(forwarded, {**incoming, **m["sampling"]})
                self.assertEqual(forwarded["model"], r.MODEL_IDS[arm])
                self.assertEqual(incoming["model"], r.CLIENT_ID)
                self.assertIs(incoming["chat_template_kwargs"]["enable_thinking"], True)
            self.assertNotEqual(bm["serving"]["model_id"], tm["serving"]["model_id"])
            with self.assertRaises(ValueError):
                r.serving(f.profile, "zero")

    def test_profile_semantic_drift_is_rejected_even_when_caller_rehashes(self):
        changes = {"host": "0.0.0.0", "port": 18104, "context": 32768, "output": 8192,
                   "dtype": "float16", "lora_dtype": "float16", "native_thinking": True,
                   "tool_parser": "qwen3_coder", "base_binding_sha256": "wrong-base",
                   "training_receipt_sha256": "wrong-training", "container_name": "shared-model",
                   "model_ids": {"base": "wrong", "trained": "wrong", "zero": "wrong"}}
        with fixture() as f:
            for key, value in changes.items():
                with self.subTest(field=key):
                    changed = dict(f.profile, **{key: value})
                    write(f.profile_path, changed)
                    with self.assertRaises(ValueError):
                        r.profile(f.profile_path, r.sha(f.profile_path), verify_container=False)
            self.assertEqual(f.inspect.call_count, 0)

    def test_profile_hash_checkpoint_and_training_receipt_reject_tampering(self):
        with fixture() as f:
            digest = r.sha(f.profile_path)
            f.profile_path.write_bytes(f.profile_path.read_bytes() + b" ")
            with self.assertRaisesRegex(ValueError, "profile changed"):
                r.profile(f.profile_path, digest)
            write(f.profile_path, f.profile)
            for target in [*f.adapter.iterdir(), f.training, f.base_binding]:
                with self.subTest(target=target.name):
                    old = target.read_bytes()
                    target.write_bytes(old + b"tampered")
                    with self.assertRaisesRegex(ValueError, "bytes changed|receipt changed|base binding changed"):
                        r.profile(f.profile_path, r.sha(f.profile_path), verify_container=False)
                    target.write_bytes(old)
            changed = copy.deepcopy(f.profile)
            changed["adapter_files"]["adapter_config.json"] = "relabelled-checkpoint"
            write(f.profile_path, changed)
            with self.assertRaisesRegex(ValueError, "qualified checkpoint"):
                r.profile(f.profile_path, r.sha(f.profile_path), verify_container=False)

    def test_serving_identity_requires_the_owned_running_container_and_image(self):
        with fixture() as f:
            self.assertEqual(r.profile(f.profile_path, r.sha(f.profile_path)), f.profile)
            self.assertEqual(f.inspect.call_args.args[0][:2], ["docker", "inspect"])
            for actual in ("other-id sha256:owned-image true", "owned-container-id other-image true",
                           "owned-container-id sha256:owned-image false"):
                with self.subTest(actual=actual), mock.patch.object(r.subprocess, "check_output", return_value=actual):
                    with self.assertRaisesRegex(ValueError, "container identity"):
                        r.profile(f.profile_path, r.sha(f.profile_path))

    def test_canonical_namespace_and_fresh_root_precede_any_world_start(self):
        with fixture() as f:
            for path, arm in ((f.qual / "elsewhere/attempt_v1", "base"),
                              (f.root("trained"), "base"), (f.root(n=0), "base"),
                              (f.root().with_name("attempt_v01"), "base"), (f.root(), "zero")):
                with self.subTest(path=str(path), arm=arm), self.assertRaises(ValueError):
                    r.prepare(path, arm, f.profile_path, r.sha(f.profile_path))
            f.core.start_world.assert_not_called()
            root = f.root()
            root.mkdir(parents=True)
            (root / "keep.raw").write_bytes(b"retained")
            with self.assertRaises(FileExistsError):
                r.prepare(root, "base", f.profile_path, r.sha(f.profile_path))
            self.assertEqual((root / "keep.raw").read_bytes(), b"retained")
            f.core.start_world.assert_not_called()

    def test_symlink_alias_cannot_disguise_a_noncanonical_episode_path(self):
        with fixture() as f:
            root, _, digest = prepared(f)
            alias = f.qual / "outside-alias"
            parent_alias = f.qual / "aliased-parent"
            try:
                alias.symlink_to(root, target_is_directory=True)
                parent_alias.symlink_to(root.parent, target_is_directory=True)
            except OSError as exc:
                self.skipTest("symlinks unavailable: " + str(exc))
            f.core.start_world.reset_mock()
            for path in (alias, parent_alias / root.name):
                for operation in (lambda: r.check_root(path, "base"),
                                  lambda: r.verify(path, digest),
                                  lambda: r.execute(path, digest, fake_endpoint=("mock-endpoint", 1))):
                    with self.subTest(path=str(path), operation=operation), self.assertRaises(ValueError):
                        operation()
            self.assertFalse((root / "reservation.json").exists())
            f.core.start_world.assert_not_called()
            f.process.assert_not_called()

    def test_frozen_inputs_and_semantic_manifest_bindings_fail_before_reservation(self):
        mutations = ["task.txt", "handoff_public.json", "opencode_config.json", "manifest.json",
                     "components", "source_binding", "caps", "serving", "model_id",
                     "tokenizer_files_sha256", "sampling", "uid"]
        with fixture() as f:
            for n, name in enumerate(mutations, 1):
                with self.subTest(field=name):
                    root, manifest, digest = prepared(f, n=n)
                    if name.endswith(".json") or name == "task.txt":
                        path = root / name
                        path.write_bytes(path.read_bytes() + b"tampered")
                    else:
                        manifest[name] = {} if isinstance(manifest[name], dict) else "changed"
                        write(root / "manifest.json", manifest)
                        digest = r.sha(root / "manifest.json")
                    f.core.start_world.reset_mock()
                    with self.assertRaises(ValueError):
                        r.execute(root, digest)
                    self.assertFalse((root / "reservation.json").exists())
                    f.core.start_world.assert_not_called()
            f.process.assert_not_called()

    def test_exclusive_reservation_prevents_a_second_episode_before_world_or_actor(self):
        with fixture() as f:
            root, _, digest = prepared(f)
            receipt = r.execute(root, digest, fake_endpoint=("mock-endpoint", 1))
            self.assertFalse(receipt["qualifies_learning_gain"])
            reservation = (root / "reservation.json").read_bytes()
            f.core.start_world.reset_mock()
            f.process.reset_mock()
            with self.assertRaises(FileExistsError):
                r.execute(root, digest, fake_endpoint=("mock-endpoint", 1))
            self.assertEqual((root / "reservation.json").read_bytes(), reservation)
            f.core.start_world.assert_not_called()
            f.process.assert_not_called()

    def test_actual_relay_checks_template_budget_before_forwarding_any_packet(self):
        for count, fits in ((12288, True), (12289, False)):
            with self.subTest(input_tokens=count), fixture() as f:
                root, manifest, digest = prepared(f, "trained")
                payload = {"token_count": count, "model": r.MODEL_IDS["trained"]}

                def process(argv, **_):
                    if argv == ["mock-owned-actor"]:
                        f.instances[-1].forward("mock-upstream", b"packet", payload, 1)
                    return subprocess.CompletedProcess(argv, 0)

                f.process.side_effect = process
                receipt = r.execute(root, digest, fake_endpoint=("mock-endpoint", 1))
                relay = f.instances[-1]
                proof = json.loads((root / "actual_template_tokens/00001.json").read_text())
                self.assertEqual(proof["input_tokens"], count)
                self.assertIs(proof["fits"], fits)
                self.assertEqual(len(relay.forward_calls), int(fits))
                self.assertEqual(relay.args[3], manifest["serving"])
                self.assertIs(relay.kwargs["student_enable_thinking"], False)
                self.assertTrue(relay.closed)
                if not fits:
                    self.assertEqual(receipt["status"], "FAILED")
                    self.assertIn("actual native template exceeds context", receipt["errors"][0]["error"])

    def test_template_qualifier_counts_actual_projected_ids_with_reserved_output(self):
        tokenizer = SimpleNamespace()
        calls = []

        def apply(messages, **kwargs):
            calls.append((copy.deepcopy(messages), kwargs))
            return {"input_ids": [[0] * len(messages[0]["content"])], "attention_mask": []}

        tokenizer.apply_chat_template = apply
        loader = mock.Mock(return_value=tokenizer)
        with fixture(), mock.patch.dict(sys.modules, {"transformers": SimpleNamespace(
                AutoTokenizer=SimpleNamespace(from_pretrained=loader))}), mock.patch.object(r, "sha", return_value="tokenizer-sha"):
            binding, qualify = TOKENIZER_QUALIFIER()
            self.assertEqual(set(binding), {"tokenizer.json", "tokenizer_config.json"})
            self.assertEqual(loader.call_args.kwargs, {"local_files_only": True, "trust_remote_code": False})
            for count in (12288, 12289):
                payload = {"messages": [{"role": "user", "content": "x" * count},
                    {"role": "assistant", "tool_calls": [{"function": {
                        "name": "bash", "arguments": '{"command":"look"}'}}]}], "tools": [{"type": "function"}]}
                before = copy.deepcopy(payload)
                proof = qualify(payload)
                self.assertEqual(proof["input_tokens"], count)
                self.assertEqual(proof["fits"], count <= 12288)
                self.assertEqual(payload, before)
                messages, kwargs = calls[-1]
                self.assertEqual(messages[1]["tool_calls"][0]["function"]["arguments"], {"command": "look"})
                self.assertIs(kwargs["enable_thinking"], False)
                self.assertTrue(kwargs["add_generation_prompt"])
                self.assertEqual(kwargs["tools"], payload["tools"])

    def test_cleanup_failure_still_retains_terminal_receipt(self):
        with fixture() as f:
            root, _, digest = prepared(f)

            def process(argv, **_):
                if argv[:3] == ["docker", "rm", "-f"]:
                    raise subprocess.TimeoutExpired(argv, 15)
                return subprocess.CompletedProcess(argv, 0)

            f.process.side_effect = process
            receipt = r.execute(root, digest, fake_endpoint=("mock-endpoint", 1))
            self.assertEqual(receipt["status"], "RETURNED")
            self.assertTrue((root / "receipt.json").exists())
            self.assertEqual(receipt["errors"][0]["cleanup"], "actor_container")
            self.assertTrue(f.instances[-1].closed)
            f.core.stop_world.assert_called()

    def test_execute_cli_only_accepts_frozen_manifest_and_no_arm_or_profile_override(self):
        for extra in (["--arm", "base"], ["--profile", "changed.json"], ["--profile-sha", "changed"]):
            with self.subTest(extra=extra), mock.patch.object(r, "execute") as execute, \
                    mock.patch("sys.stderr", new_callable=io.StringIO), self.assertRaises(SystemExit):
                r.main(["--execute", "--run-root", "mock-root", "--manifest-sha", "frozen", *extra])
            execute.assert_not_called()


if __name__ == "__main__":
    unittest.main()
