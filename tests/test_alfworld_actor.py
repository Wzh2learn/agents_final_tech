"""ALFWorld actor boundary contracts; tests never contact a model endpoint."""
import importlib.util
import io
import os
import json
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "research/agent_frontier_portfolio_20261029/run_alfworld_actor_20261106.py"
sys.path[:0] = [str(ROOT), str(SCRIPT.parent)]
spec = importlib.util.spec_from_file_location("alfworld_actor_contract", SCRIPT)
actor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(actor)


def profile(model="qwen3-8b-qual"):
    return {"host": "127.0.0.1", "port": 18104, "model_id": model,
            "context": 32768, "output": 8192}


class FragmentedSocket:
    """Use a real socketpair while forcing the parser to handle short reads."""
    def __init__(self, connection):
        self.connection = connection

    def recv(self, size, *args):
        return self.connection.recv(min(size, 3), *args)

    def __getattr__(self, name):
        return getattr(self.connection, name)


class ActorContractTests(unittest.TestCase):
    def test_config_is_bash_only_and_disables_sdk_retries(self):
        cfg = actor.config(profile(), 17)
        self.assertEqual(cfg["model"], "gb10/qwen3-8b-qual")
        self.assertIs(cfg["autoupdate"], False)
        for scope in (cfg, cfg["agent"]["build"]):
            self.assertEqual(scope["tools"], {"*": False, "bash": True})
            self.assertEqual(scope["permission"], {"*": "deny", "bash": "allow"})
        provider = cfg["provider"]["gb10"]
        self.assertEqual(provider["options"]["baseURL"], "http://127.0.0.1:18004/v1")
        self.assertEqual(provider["options"]["maxRetries"], 0)
        self.assertEqual(provider["models"]["qwen3-8b-qual"]["limit"],
                         {"context": 32768, "output": 8192})
        self.assertEqual(cfg["agent"]["build"]["seed"], 17)

    def test_teacher_and_student_payloads_pin_sampling_without_thinking_leak(self):
        incoming = {"model": "untrusted", "seed": 999, "temperature": 1.5,
                    "max_tokens": 999999, "stream": False,
                    "messages": [{"role": "user", "content": "public task"}],
                    "tools": [{"type": "function", "function": {"name": "bash"}}],
                    "chat_template_kwargs": {"enable_thinking": True}}
        for backend, model in (("student8b", "qwen3-8b-qual"),
                               ("teacher27b", "qwen38-27b-fp8")):
            with self.subTest(backend=backend):
                value = actor.model_payload(incoming, backend, profile(model), 17)
                self.assertEqual((value["model"], value["seed"], value["temperature"]),
                                 (model, 17, 0.2))
                self.assertEqual(value["max_tokens"], 8192)
                self.assertIs(value["stream"], True)
                self.assertIs(value["stream_options"]["include_usage"], True)
                self.assertEqual(value["messages"], incoming["messages"])
                self.assertEqual(value["tools"], incoming["tools"])
                if backend == "teacher27b":
                    self.assertEqual(value["chat_template_kwargs"], {"enable_thinking": False})
                else:
                    self.assertNotIn("chat_template_kwargs", value)

    def test_prompt_contains_current_public_task_and_explicit_step_semantics(self):
        initial = {"observation": "Your task is to clean an apple and put it on the table.",
                   "score": 0.0, "done": False, "won": False, "action_count": 0,
                   "admissible_commands": ["look"]}
        prompt = actor.task_prompt(initial)
        self.assertIn(initial["observation"], prompt)
        self.assertIn("/world/client.py step --socket /world/s", prompt)
        self.assertIn("one environment action per tool call", prompt)
        self.assertIn("cached", prompt)
        self.assertIn("including look", prompt)
        self.assertIn("won=true", prompt)
        self.assertNotIn("source_experience.md", prompt)
        self.assertNotIn("expert_plan", prompt)
        self.assertNotIn("game.tw-pddl", prompt)
        self.assertNotIn("/home/testuser/", prompt)

    def test_docker_mounts_only_public_episode_dirs_and_readonly_runtime(self):
        work, world, model = map(Path, ("/episode/work", "/episode/world", "/episode/model"))
        manifest = {"uid": 1000, "gid": 1000,
                    "image_id": "sha256:" + "a" * 64, "model_id": "qwen3-8b-qual"}
        with mock.patch.object(actor, "RUNTIME_ROOT", Path("/readonly-python")), \
                mock.patch.object(actor, "BINARY", Path("/readonly-opencode")):
            cmd = actor.docker_command(work, world, model, manifest, "alfworld-contract")
        self.assertEqual(cmd[cmd.index("--user") + 1], "1000:1000")
        self.assertEqual(cmd[cmd.index("--network") + 1], "none")
        self.assertIn("--read-only", cmd)
        self.assertEqual(cmd[cmd.index("--pull") + 1], "never")
        self.assertEqual(cmd[cmd.index("--workdir") + 1], "/workspace")
        self.assertIn("HOME=/workspace", cmd)
        self.assertIn("OPENCODE_DISABLE_MODELS_FETCH=1", cmd)
        mounts = [cmd[i + 1] for i, item in enumerate(cmd) if item == "--mount"]
        self.assertEqual(set(mounts), {
            "type=bind,src=/episode/work,dst=/workspace",
            "type=bind,src=/episode/world,dst=/world,readonly",
            "type=bind,src=/episode/model,dst=/model,readonly",
            "type=bind,src=/readonly-python/runtime,dst=/runtime,readonly",
            "type=bind,src=/readonly-opencode,dst=/opt/opencode,readonly"})
        self.assertEqual(len(mounts), 5)
        joined = " ".join(cmd)
        for forbidden in ("game.tw-pddl", "alfworld_text_qualification", "docker.sock",
                          "--privileged", "--network host", "--pid host"):
            self.assertNotIn(forbidden, joined)
        self.assertIn(manifest["image_id"], cmd)

    def test_concurrent_reservations_are_unique_and_obey_explicit_post_cap(self):
        budget = actor.Budget(max_posts=3, max_bytes=1000, seconds=30)
        gate = threading.Barrier(9)
        accepted, denied, unexpected = [], [], []

        def reserve():
            gate.wait()
            try:
                accepted.append(budget.reserve(2))
            except ValueError:
                denied.append(True)
            except Exception as exc:
                unexpected.append(type(exc).__name__)

        threads = [threading.Thread(target=reserve) for _ in range(8)]
        for thread in threads:
            thread.start()
        gate.wait()
        for thread in threads:
            thread.join(timeout=2)
        self.assertTrue(all(not t.is_alive() for t in threads))
        self.assertEqual(unexpected, [])
        self.assertEqual(len(accepted), 3)
        self.assertEqual(len(set(accepted)), 3)
        self.assertEqual(len(denied), 5)
        self.assertEqual((budget.posts, budget.request_bytes, budget.response_bytes), (3, 6, 0))
        # The controller's explicit default cap, independent of any conversation Goal.
        default = actor.Budget()
        for _ in range(48):
            default.reserve(1)
        with self.assertRaises(ValueError):
            default.reserve(1)
        self.assertEqual(default.posts, 48)

    def test_combined_request_and_response_bytes_enforce_one_budget(self):
        budget = actor.Budget(max_posts=9, max_bytes=10, seconds=30)
        budget.reserve(4)
        budget.response(5)
        self.assertEqual((budget.request_bytes, budget.response_bytes), (4, 5))
        with self.assertRaises(ValueError):
            budget.reserve(2)  # request-only accounting would wrongly admit this.
        other = actor.Budget(max_posts=9, max_bytes=10, seconds=30)
        other.reserve(4)
        other.response(6)  # exact combined boundary is allowed.
        with self.assertRaises(OSError):
            other.response(1)

    def test_closing_relay_rejects_reserved_connect_without_sending(self):
        relay = actor.ModelRelay.__new__(actor.ModelRelay)
        relay.lock = threading.Lock()
        relay.budget = actor.Budget(max_posts=3, max_bytes=100, seconds=30)
        relay.owned = set()
        relay.forwarded = 0
        relay.closing = False
        relay.budget.reserve(4)  # A handler reserved before its connect completed.

        class FakeUpstream:
            def __init__(self):
                self.sent = []

            def sendall(self, packet):
                self.sent.append(packet)

        upstream = FakeUpstream()
        relay.begin_close()
        with self.assertRaises((OSError, ValueError)):
            relay.forward(upstream, b"body")
        self.assertEqual(upstream.sent, [])
        self.assertEqual(relay.owned, set())
        self.assertEqual(relay.forwarded, 0)

    def test_deadline_and_poison_block_new_requests_without_retry(self):
        clock = [100.0]
        with mock.patch.object(actor.time, "monotonic", side_effect=lambda: clock[0]):
            expired = actor.Budget(max_posts=3, max_bytes=100, seconds=2)
            clock[0] = 103.0
            with self.assertRaises(ValueError):
                expired.reserve(1)
        budget = actor.Budget(max_posts=3, max_bytes=100, seconds=30)
        budget.reserve(4)
        budget.poison()
        for _ in range(2):
            with self.assertRaises(ValueError):
                budget.reserve(1)
        self.assertEqual((budget.posts, budget.request_bytes), (1, 4))

    def http_value(self, wire, fragmented=False):
        sender, receiver = socket.socketpair()
        try:
            sender.settimeout(1)
            receiver.settimeout(1)
            sender.sendall(wire)
            sender.shutdown(socket.SHUT_WR)
            return actor.receive_http(FragmentedSocket(receiver) if fragmented else receiver)
        finally:
            sender.close()
            receiver.close()

    def test_http_parser_accepts_one_real_fragmented_post(self):
        value = {"messages": [{"role": "user", "content": "public task"}], "stream": True}
        body = json.dumps(value).encode()
        wire = (b"POST /v1/chat/completions HTTP/1.1\r\nHost: local\r\n"
                b"Content-Type: application/json\r\nContent-Length: " +
                str(len(body)).encode() + b"\r\n\r\n" + body)
        self.assertEqual(self.http_value(wire, fragmented=True), value)

    def test_http_parser_rejects_ambiguous_frames_before_forwarding(self):
        prefix = b"POST /v1/chat/completions HTTP/1.1\r\n"
        normal = prefix + b"Content-Length: 2\r\n\r\n{}"
        wires = [
            prefix + b"Content-Length: 2\r\ncontent-length: 2\r\n\r\n{}",
            prefix + b"Host: one\r\nhost: two\r\nContent-Length: 2\r\n\r\n{}",
            prefix + b"Transfer-Encoding: chunked\r\n\r\n2\r\n{}\r\n0\r\n\r\n",
            prefix + b"Content-Length: -1\r\n\r\n{}",
            prefix + b"Content-Length: nope\r\n\r\n{}",
            prefix + b"BrokenHeader\r\nContent-Length: 2\r\n\r\n{}",
            prefix + b"Content-Type: application/json\r\n\r\n{}",
            prefix + b"Content-Length: 9\r\n\r\n{}",
            prefix + b"Content-Length: 1\r\n\r\n{",
            normal + normal,
            normal.replace(b"POST /v1/chat/completions", b"GET /v1/chat/completions", 1),
            normal.replace(b"/v1/chat/completions", b"/admin", 1),
        ]
        for wire in wires:
            with self.subTest(wire=wire), self.assertRaises((ValueError, KeyError)):
                self.http_value(wire)

    def test_execute_cli_requires_manifest_before_any_execution(self):
        with mock.patch.object(actor, "execute") as execute, \
                mock.patch.object(actor, "load_profile") as load_profile, \
                mock.patch.object(actor, "start_world") as start_world, \
                mock.patch.object(actor.socket, "create_connection") as connect, \
                mock.patch("sys.stderr", new_callable=io.StringIO) as stderr:
            with self.assertRaises(SystemExit) as raised:
                actor.main(["--execute", "--run-root", "/unused-alfworld-run"])
            self.assertEqual(raised.exception.code, 2)
            self.assertIn("--manifest-sha", stderr.getvalue())
            execute.assert_not_called()
            load_profile.assert_not_called()
            start_world.assert_not_called()
            connect.assert_not_called()

    def test_existing_reservation_blocks_rerun_before_profile_world_or_connection(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            with mock.patch.object(actor, "verify_manifest", return_value={"backend": "student8b"}) as verify, \
                    mock.patch.object(actor, "write_new", side_effect=FileExistsError("reserved")) as reserve, \
                    mock.patch.object(actor, "load_profile") as load_profile, \
                    mock.patch.object(actor, "start_world") as start_world, \
                    mock.patch.object(actor.socket, "create_connection") as connect:
                with self.assertRaises(FileExistsError):
                    actor.execute(root, "a" * 64)
                verify.assert_called_once_with(root, "a" * 64)
                reserve.assert_called_once()
                self.assertEqual(reserve.call_args.args[0], root / "reservation.json")
                load_profile.assert_not_called()
                start_world.assert_not_called()
                connect.assert_not_called()
            self.assertEqual(list(root.iterdir()), [])

    def test_manifest_rejects_changed_frozen_inputs_components_and_digest(self):
        with tempfile.TemporaryDirectory() as tmp:
            qual = Path(tmp) / "qualification"
            root = qual / "episode"
            root.mkdir(parents=True)
            binary = qual / "opencode"
            binary.write_bytes(b"fake pinned binary")
            game = qual / "game.tw-pddl"
            game.write_bytes(b"private fake asset, never mounted")
            files = {"opencode_config.json": b"{}", "task.txt": b"public current goal",
                     "initial_reset.json": b'{"observation":"public reset"}'}
            for name, content in files.items():
                (root / name).write_bytes(content)
            component_hashes = {"runner.py": "a" * 64}
            manifest = {
                "components": component_hashes,
                "config_sha256": actor.sha(root / "opencode_config.json"),
                "prompt_sha256": actor.sha(root / "task.txt"),
                "initial_sha256": actor.sha(root / "initial_reset.json"),
                "game_path": str(game), "game_sha256": actor.sha(game),
                "uid": os.getuid(), "gid": os.getgid()}
            frozen = root / "manifest.json"
            frozen.write_text(json.dumps(manifest))
            digest = actor.sha(frozen)
            with mock.patch.object(actor, "QUAL", qual), \
                    mock.patch.object(actor, "BINARY", binary), \
                    mock.patch.object(actor, "BINARY_SHA", actor.sha(binary)), \
                    mock.patch.object(actor, "components", return_value=component_hashes) as components, \
                    mock.patch.object(actor.dependencies, "verify_projection") as projection:
                # A passing control ensures tamper failures are not a broken fixture.
                self.assertEqual(actor.verify_manifest(root, digest), manifest)
                for name, content in files.items():
                    with self.subTest(changed=name):
                        projection.reset_mock()
                        (root / name).write_bytes(content + b" tampered")
                        with self.assertRaises(ValueError):
                            actor.verify_manifest(root, digest)
                        projection.assert_not_called()
                        (root / name).write_bytes(content)
                components.return_value = {"runner.py": "b" * 64}
                projection.reset_mock()
                with self.assertRaises(ValueError):
                    actor.verify_manifest(root, digest)
                projection.assert_not_called()
                components.return_value = component_hashes
                frozen.write_bytes(frozen.read_bytes() + b"\n")
                with self.assertRaises(ValueError):
                    actor.verify_manifest(root, digest)

    def test_import_is_lazy_and_never_imports_native_or_django_runner(self):
        probe = ("import importlib.util,sys; "
                 "sys.path[:0]=[sys.argv[2],sys.argv[3]];"
                 "s=importlib.util.spec_from_file_location('isolated_actor',sys.argv[1]);"
                 "m=importlib.util.module_from_spec(s);s.loader.exec_module(m);"
                 "assert not ({'alfworld','textworld','pyarrow',"
                 "'run_django_aggregation_agent_20261106'} & set(sys.modules))")
        with tempfile.TemporaryDirectory() as tmp:
            result = subprocess.run([sys.executable, "-B", "-c", probe, str(SCRIPT),
                                     str(ROOT), str(SCRIPT.parent)], cwd=tmp,
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(list(Path(tmp).iterdir()), [])


    def pool_fixture(self, temporary):
        qual = Path(temporary) / "qual"
        base = qual / "source_expansion_v1"
        base.mkdir(parents=True)
        assets = qual / "assets"
        assets.mkdir()
        archives = {}
        for name in ("json_2.1.1_json.zip", "json_2.1.2_tw-pddl.zip"):
            path = assets / name
            path.write_bytes(("unit archive " + name).encode())
            archives[name] = {"path": str(path), "sha256": actor.sha(path)}
        receipt = base / "RECEIPT.json"
        receipt.write_text(json.dumps({"archives": archives}))
        rows = []
        for category in ("clean", "heat", "cool", "plain_place"):
            for index in (1, 2):
                identifier = category + "_" + str(index)
                game = base / "private_game_assets" / identifier / "game.tw-pddl"
                game.parent.mkdir(parents=True)
                game.write_bytes(("private game " + identifier).encode())
                trajectory = game.with_name("traj_data.json")
                trajectory.write_bytes(("private trajectory " + identifier).encode())
                rows.append({"id": identifier, "category": category, "layout": index,
                             "private_game_path": str(game), "game_sha256": actor.sha(game),
                             "traj_sha256": actor.sha(trajectory), "game_member": identifier + "/game.tw-pddl",
                             "traj_member": identifier + "/traj_data.json",
                             "private_expert_path": "/NEVER_READ/private_expert/" + identifier})
        pool = base / "FUTURE_POOL.json"
        pool.write_text(json.dumps({"receipt_sha256": actor.sha(receipt), "games": rows}))
        return qual, pool, receipt, rows

    def test_default_caps_stay_legacy_and_new_caps_are_explicit_and_bounded(self):
        self.assertEqual(actor.episode_caps(), {"posts": 48, "seconds": 1200, "world_actions": 100,
                                               "model_payload_bytes_combined": 6_000_000})
        expanded = {"posts": 128, "seconds": 1800, "world_actions": 100,
                    "model_payload_bytes_combined": 64_000_000}
        self.assertEqual(actor.episode_caps(expanded), expanded)
        for changes in ({"posts": 129}, {"posts": True}, {"seconds": 1801},
                        {"world_actions": 101}, {"model_payload_bytes_combined": 64_000_001},
                        {"posts": 0}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                actor.episode_caps({**expanded, **changes})

    @unittest.skipUnless(hasattr(socket, "AF_UNIX"), "Unix sockets required")
    def test_relay_receives_manifest_caps_instead_of_budget_defaults(self):
        with tempfile.TemporaryDirectory() as temporary:
            qual = Path(temporary)
            model = qual / "m0"
            model.mkdir()
            root = qual / "episode"
            root.mkdir()
            caps = {"posts": 128, "seconds": 1800, "world_actions": 100,
                    "model_payload_bytes_combined": 64_000_000}
            with mock.patch.object(actor, "QUAL", qual), \
                    mock.patch.object(actor, "load_relay", return_value=lambda *args: None), \
                    mock.patch.object(actor.socket, "create_connection", side_effect=AssertionError("model probe")):
                relay = actor.ModelRelay(root, model, "student8b", profile(), 17, ("127.0.0.1", 1),
                                         caps, actor.model_payload({}, "student8b", profile(), 17))
                try:
                    self.assertEqual(relay.budget.max_posts, 128)
                    self.assertEqual(relay.budget.max_bytes, 64_000_000)
                    import time
                    self.assertGreater(relay.budget.deadline - time.monotonic(), 1795)
                    for _ in range(128):
                        relay.budget.reserve(1)
                    with self.assertRaises(ValueError):
                        relay.budget.reserve(1)
                finally:
                    relay.close()

    def test_pool_binds_exact_ids_archive_and_selected_asset_hashes_without_oracle(self):
        with tempfile.TemporaryDirectory() as temporary:
            qual, pool, receipt, rows = self.pool_fixture(temporary)
            digest = actor.sha(pool)
            with mock.patch.multiple(actor, QUAL=qual, POOL_SHA=digest,
                                     POOL_RECEIPT_SHA=actor.sha(receipt)):
                game, binding = actor.select_game("clean_1", pool, digest)
                self.assertEqual(actor.sha(game["game_path"]), rows[0]["game_sha256"])
                self.assertEqual(binding["sha256"], digest)
                self.assertEqual(set(binding["archives"]),
                                 {"json_2.1.1_json.zip", "json_2.1.2_tw-pddl.zip"})
                self.assertNotIn("private_expert", json.dumps([game, binding]))
                for identifier, path, sha in (("../../secret", pool, digest),
                                               ("clean_1", pool, "0" * 64),
                                               ("clean_1", None, digest),
                                               ("clean_1", pool, None)):
                    with self.subTest(identifier=identifier, path=path, sha=sha), self.assertRaises(ValueError):
                        actor.select_game(identifier, path, sha)
                with self.assertRaises(ValueError):
                    actor.select_game("clean_1")  # No arbitrary pool id in legacy mode.
                for asset in [qual / "assets/json_2.1.2_tw-pddl.zip",
                              Path(rows[0]["private_game_path"]),
                              Path(rows[0]["private_game_path"]).with_name("traj_data.json")]:
                    before = asset.read_bytes()
                    asset.write_bytes(before + b"changed")
                    with self.subTest(asset=asset), self.assertRaises(ValueError):
                        actor.select_game("clean_1", pool, digest)
                    asset.write_bytes(before)
                original = json.loads(pool.read_text())
                changed = json.loads(pool.read_text())
                changed["games"][0]["private_game_path"] = "/NEVER_READ/private_expert/plan"
                pool.write_text(json.dumps(changed))
                with mock.patch.object(actor, "POOL_SHA", actor.sha(pool)), self.assertRaises(ValueError):
                    actor.select_game("clean_1", pool, actor.sha(pool))
                pool.write_text(json.dumps(original))

    def test_pool_world_launch_uses_private_library_mode_and_explicit_caps(self):
        with tempfile.TemporaryDirectory() as temporary:
            qual = Path(temporary)
            root = qual / "episode"
            root.mkdir()
            public = qual / "w0"
            public.mkdir()
            game = qual / "private_game.tw-pddl"
            game.write_bytes(b"unit asset")
            caps = {"posts": 128, "seconds": 1800, "world_actions": 100,
                    "model_payload_bytes_combined": 64_000_000}
            selected = {"game_path": str(game), "sha256_game": actor.sha(game)}
            pool = {"sha256": "a" * 64}
            process = mock.Mock()
            process.pid = 1234
            process.poll.return_value = 0
            process.wait.return_value = 0

            def started(argv, **kwargs):
                (public / "s").touch()
                (public / "initial_reset_snapshot.json").write_text('{"observation":"public"}')
                return process

            with mock.patch.object(actor, "QUAL", qual), \
                    mock.patch.object(actor, "select_game", return_value=(selected, pool)), \
                    mock.patch.object(actor, "socket_directory", return_value=public), \
                    mock.patch.object(actor.subprocess, "Popen", side_effect=started) as launch:
                handle, initial, _ = actor.start_world(root, "clean_1", 17, "preflight", caps,
                                                       qual / "FUTURE_POOL.json", "a" * 64)
                argv = launch.call_args.args[0]
                self.assertIn("--serve-pool-world", argv)
                self.assertNotIn("--game-file", argv)
                for flag, value in (("--max-posts", "128"), ("--max-seconds", "1800"),
                                    ("--max-actions", "100"), ("--max-bytes", "64000000")):
                    self.assertEqual(argv[argv.index(flag) + 1], value)
                self.assertEqual(initial, {"observation": "public"})
                self.assertEqual({p.name for p in public.iterdir()},
                                 {"s", "client.py", "initial_reset_snapshot.json"})
                actor.stop_world(handle)

    def test_pool_manifest_caps_sampling_and_snapshot_tampering_are_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            qual, pool, receipt, _ = self.pool_fixture(temporary)
            digest = actor.sha(pool)
            root = qual / "episode"
            root.mkdir()
            binary = qual / "binary"
            binary.write_bytes(b"unit binary")
            with mock.patch.multiple(actor, QUAL=qual, POOL_SHA=digest,
                                     POOL_RECEIPT_SHA=actor.sha(receipt), BINARY=binary,
                                     BINARY_SHA=actor.sha(binary)), \
                    mock.patch.object(actor, "components", return_value={"runner": "a" * 64}), \
                    mock.patch.object(actor, "load_profile", return_value=profile("qwen38-27b-fp8")), \
                    mock.patch.object(actor.dependencies, "verify_projection"):
                game, binding = actor.select_game("clean_1", pool, digest)
                files = {"opencode_config.json": b"{}", "task.txt": b"public",
                         "initial_reset.json": b"{}", "pool_manifest.json": pool.read_bytes()}
                for name, content in files.items():
                    (root / name).write_bytes(content)
                value = {"components": {"runner": "a" * 64}, "backend": "teacher27b", "seed": 17,
                         "game_id": "clean_1", "game_path": game["game_path"],
                         "game_sha256": game["sha256_game"], "uid": os.getuid(), "gid": os.getgid(),
                         "config_sha256": actor.sha(root / "opencode_config.json"),
                         "prompt_sha256": actor.sha(root / "task.txt"),
                         "initial_sha256": actor.sha(root / "initial_reset.json"),
                         "caps": actor.episode_caps(),
                         "sampling": actor.model_payload({}, "teacher27b", profile("qwen38-27b-fp8"), 17),
                         "pool_binding": binding}
                frozen = root / "manifest.json"
                frozen.write_text(json.dumps(value))
                self.assertEqual(actor.verify_manifest(root, actor.sha(frozen)), value)
                for change in ({"caps": {**value["caps"], "posts": 129}},
                               {"sampling": {**value["sampling"], "chat_template_kwargs": {"enable_thinking": 0}}},
                               {"pool_binding": {**binding, "game_sha256": "0" * 64}}):
                    frozen.write_text(json.dumps({**value, **change}))
                    with self.subTest(change=change), self.assertRaises(ValueError):
                        actor.verify_manifest(root, actor.sha(frozen))
                frozen.write_text(json.dumps(value))
                (root / "pool_manifest.json").write_bytes(b"changed pool snapshot")
                with self.assertRaises(ValueError):
                    actor.verify_manifest(root, actor.sha(frozen))

    def test_cli_freezes_explicit_caps_and_rejects_execute_overrides(self):
        caps = {"posts": 128, "seconds": 1800, "world_actions": 100,
                "model_payload_bytes_combined": 64_000_000}
        with mock.patch.object(actor, "preflight", return_value={}) as prepare, \
                mock.patch("sys.stdout", new_callable=io.StringIO):
            actor.main(["--preflight-only", "--run-root", "/private/new", "--backend", "teacher27b",
                        "--pool-manifest", "/private/pool.json", "--pool-manifest-sha", "a" * 64,
                        "--game-id", "clean_1", "--max-posts", "128", "--max-seconds", "1800",
                        "--max-actions", "100", "--max-bytes", "64000000"])
            self.assertEqual(prepare.call_args.kwargs["caps"], caps)
            self.assertEqual(prepare.call_args.args[2], "clean_1")
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "manifest.json").write_text(json.dumps({"caps": caps}))
            with mock.patch.object(actor, "execute") as execute, \
                    mock.patch("sys.stderr", new_callable=io.StringIO):
                with self.assertRaises(SystemExit):
                    actor.main(["--execute", "--run-root", str(root), "--manifest-sha", "a" * 64,
                                "--max-posts", "48"])
                execute.assert_not_called()



if __name__ == "__main__":
    unittest.main()
