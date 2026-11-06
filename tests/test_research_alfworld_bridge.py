"""Public protocol tests; fake hidden fields must never cross the actor boundary."""
import importlib.util
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import threading
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/graph/research_alfworld_bridge.py"
spec = importlib.util.spec_from_file_location("alfworld_bridge", SCRIPT)
bridge = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bridge)


class FakeBackend:
    def __init__(self, winning=False, fail=False):
        self.calls = []
        self.winning = winning
        self.fail = fail

    def infos(self):
        return {"won": False, "admissible_commands": ["look", "take apple 1"],
                "facts": ["SECRET_FACT"], "extra.expert_plan": ["SECRET_PLAN"],
                "extra.gamefile": "/SECRET_ASSET/game.tw-pddl"}

    def reset(self):
        return "public goal: take an apple", self.infos()

    def step(self, action):
        self.calls.append(action)
        if self.fail:
            raise RuntimeError("/SECRET_ASSET SECRET_FAILURE")
        infos = self.infos()
        infos["won"] = self.winning
        return "public step " + str(len(self.calls)), float(self.winning), self.winning, infos

    def close(self):
        pass


class EpisodeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def episode(self, backend=None, cap=4, show=True):
        backend = backend or FakeBackend()
        log = bridge.PublicTrajectory(self.root / "public.jsonl",
                                      {"asset_sha256": "a" * 64, "seed": 17})
        episode = bridge.Episode(backend, cap, log, show)
        self.addCleanup(episode.close)
        return episode, backend

    def test_public_whitelist_and_append_only_log_omit_hidden_infos(self):
        episode, backend = self.episode()
        initial = episode.snapshot()
        result = episode.apply({"action": "look"})
        self.assertEqual(backend.calls, ["look"])
        self.assertEqual(result["action_count"], 1)
        self.assertEqual(initial["action_count"], 0)
        self.assertNotEqual(initial["observation"], result["observation"])
        self.assertEqual(set(result), bridge.STATE_KEYS)
        lines = [json.loads(x) for x in (self.root / "public.jsonl").read_text().splitlines()]
        self.assertEqual([x["event"] for x in lines], ["episode", "reset", "step"])
        self.assertEqual(lines[1]["state"], initial)
        self.assertEqual(lines[2]["state"], result)
        serialized = json.dumps([result, lines])
        for hidden in ("SECRET_FACT", "SECRET_PLAN", "SECRET_ASSET", "extra.", "facts"):
            self.assertNotIn(hidden, serialized)

    def test_forbidden_fields_types_controls_and_unknown_actions_do_not_mutate(self):
        episode, backend = self.episode()
        values = [{}, {"reset": True}, {"action": "look", "game": "other"},
                  {"action": "look", "observe": True}, {"action": ["look"]},
                  {"action": ""}, {"action": " look"}, {"action": "look\n"},
                  {"action": "x" * 257}, {"action": "\ud800"}]
        for value in values:
            with self.subTest(value=repr(value)), self.assertRaises(bridge.BridgeError):
                episode.apply(value)
        with self.assertRaisesRegex(bridge.BridgeError, "invalid_action"):
            episode.apply({"action": "invented action"})
        self.assertEqual(backend.calls, [])
        self.assertEqual(episode.action_count, 0)

    def test_winning_terminal_and_budget_both_prevent_further_native_mutation(self):
        episode, backend = self.episode(FakeBackend(winning=True))
        state = episode.apply({"action": "take apple 1"})
        self.assertTrue(state["done"])
        self.assertTrue(state["won"])
        self.assertEqual(state["score"], 1.0)
        with self.assertRaisesRegex(bridge.BridgeError, "episode_done"):
            episode.apply({"action": "look"})
        self.assertEqual(len(backend.calls), 1)

    def test_concurrent_actions_obey_one_shared_cap_without_retries(self):
        episode, backend = self.episode(cap=2)
        results = []
        gate = threading.Barrier(9)

        def call():
            gate.wait()
            try:
                results.append(episode.apply({"action": "look"}))
            except bridge.BridgeError as exc:
                results.append({"error": exc.code})

        threads = [threading.Thread(target=call) for _ in range(8)]
        for t in threads:
            t.start()
        gate.wait()
        for t in threads:
            t.join(timeout=2)
        states = [r for r in results if "error" not in r]
        self.assertEqual(sorted(r["action_count"] for r in states), [1, 2])
        self.assertTrue(next(r for r in states if r["action_count"] == 2)["done"])
        self.assertEqual(sum(r == {"error": "budget_exhausted"} for r in results), 6)
        self.assertEqual(backend.calls, ["look", "look"])

    def test_native_exception_is_redacted_and_poisoned_without_retry(self):
        episode, backend = self.episode(FakeBackend(fail=True))
        for _ in range(2):
            with self.assertRaisesRegex(bridge.BridgeError, "^environment_failure$"):
                episode.apply({"action": "look"})
        self.assertEqual(backend.calls, ["look"])
        self.assertNotIn("SECRET", (self.root / "public.jsonl").read_text())

    def test_trajectory_write_failure_stops_episode_after_one_committed_action(self):
        episode, backend = self.episode()
        episode.trajectory.close()
        with self.assertRaises(bridge.BridgeError):
            episode.apply({"action": "look"})
        self.assertEqual(backend.calls, ["look"])
        with self.assertRaises(bridge.BridgeError):
            episode.apply({"action": "look"})
        self.assertEqual(len(backend.calls), 1)

    def test_admissible_list_is_optional_and_response_parser_rejects_hidden_fields(self):
        episode, _ = self.episode(show=False)
        state = episode.apply({"action": "look"})
        self.assertNotIn("admissible_commands", state)
        self.assertEqual(bridge.validate_response(state), state)
        with self.assertRaises(bridge.BridgeError):
            bridge.validate_response({**state, "facts": ["SECRET"]})

    def test_malformed_error_payload_and_huge_score_are_public_protocol_errors(self):
        for value in ({"error": []}, {"error": {}}, {"error": "SECRET"}):
            with self.subTest(value=value), self.assertRaisesRegex(
                    bridge.BridgeError, "invalid_response"):
                bridge.validate_response(value)
        episode, _ = self.episode()
        state = episode.snapshot()
        with self.assertRaisesRegex(bridge.BridgeError, "invalid_response"):
            bridge.validate_response({**state, "score": 10**1000})

    def test_private_asset_and_trajectory_cannot_be_under_actor_socket_mount(self):
        socket_path = self.root / "actor" / "s"
        for game, log in ((self.root / "actor" / "game.tw-pddl", self.root / "log"),
                          (self.root / "game.tw-pddl", self.root / "actor" / "log")):
            with self.assertRaisesRegex(bridge.BridgeError, "startup_error"):
                bridge.validate_private_paths(game, socket_path, log)
        bridge.validate_private_paths(self.root / "game.tw-pddl", socket_path,
                                      self.root / "log")

    def test_existing_trajectory_cannot_be_replaced(self):
        episode, _ = self.episode()
        before = (self.root / "public.jsonl").read_bytes()
        with self.assertRaises(FileExistsError):
            bridge.PublicTrajectory(self.root / "public.jsonl", {})
        self.assertEqual((self.root / "public.jsonl").read_bytes(), before)

    def test_module_import_has_no_alfworld_runtime_or_filesystem_side_effect(self):
        probe = ("import importlib.util,sys; "
                 "s=importlib.util.spec_from_file_location('probe',sys.argv[1]);"
                 "m=importlib.util.module_from_spec(s);s.loader.exec_module(m);"
                 "assert 'alfworld' not in sys.modules;"
                 "assert 'textworld' not in sys.modules")
        result = subprocess.run([sys.executable, "-B", "-c", probe, str(SCRIPT)],
                                cwd=self.root, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(list(self.root.iterdir()), [])


@unittest.skipUnless(hasattr(socket, "AF_UNIX"), "Unix socket required")
class SocketTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="aw-")
        self.root = Path(self.tmp.name)
        self.backend = FakeBackend()
        log = bridge.PublicTrajectory(self.root / "public.jsonl", {"seed": 17})
        self.episode = bridge.Episode(self.backend, 4, log)
        self.socket_dir = self.root / "actor"
        short_root = os.environ.get("ALFWORLD_BRIDGE_TEST_SOCKET_ROOT")
        if short_root:
            # AF_UNIX limits the supplied pathname, even on a spacious filesystem.
            for index in range(16):
                candidate = Path(short_root) / ("u" + format(index, "x"))
                try:
                    candidate.mkdir()
                    self.socket_dir = candidate
                    break
                except FileExistsError:
                    continue
            else:
                self.fail("no private short socket directory available")
        self.path = self.socket_dir / "s"
        self.stop = threading.Event()
        self.ready = threading.Event()
        self.thread = threading.Thread(target=bridge.serve,
                                       args=(self.path, self.episode, self.stop, self.ready))
        self.thread.start()
        self.assertTrue(self.ready.wait(2))

    def tearDown(self):
        self.stop.set()
        self.thread.join(timeout=2)
        self.episode.close()
        if self.socket_dir != self.root / "actor":
            (self.socket_dir / "initial_reset_snapshot.json").unlink()
            self.socket_dir.rmdir()
        self.tmp.cleanup()

    def raw(self, data):
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as conn:
            conn.settimeout(2)
            conn.connect(str(self.path))
            conn.sendall(data)
            return json.loads(conn.recv(65536))

    def test_same_client_path_advances_look_once_and_initial_file_remains_cached(self):
        cached = (self.path.parent / "initial_reset_snapshot.json").read_bytes()
        first = bridge.client_step(self.path, "look")
        second = bridge.client_step(self.path, "look")
        self.assertEqual([first["action_count"], second["action_count"]], [1, 2])
        self.assertEqual(self.backend.calls, ["look", "look"])
        self.assertEqual((self.path.parent / "initial_reset_snapshot.json").read_bytes(), cached)
        self.assertEqual(set(p.name for p in self.path.parent.iterdir()),
                         {"s", "initial_reset_snapshot.json"})

    def test_partial_frame_duplicate_key_extra_fields_and_large_input(self):
        self.assertEqual(self.raw(b'{"action":"look","reset":true}\n'),
                         {"error": "invalid_request"})
        self.assertEqual(self.raw(b'{"action":"look","action":"look"}\n'),
                         {"error": "invalid_request"})
        self.assertEqual(self.raw(b'{"action":"look"}\n{"action":"look"}\n'),
                         {"error": "invalid_request"})
        self.assertEqual(self.raw(b"x" * (bridge.MAX_REQUEST_BYTES + 1)),
                         {"error": "invalid_request"})
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as conn:
            conn.settimeout(2)
            conn.connect(str(self.path))
            conn.sendall(b'{"action":')
            conn.sendall(b'"look"}\n')
            self.assertEqual(json.loads(conn.recv(65536))["action_count"], 1)
        self.assertEqual(self.backend.calls, ["look"])

    def test_cli_returns_only_public_json(self):
        result = subprocess.run([sys.executable, "-B", str(SCRIPT), "step",
                                 "--socket", str(self.path), "--action", "look"],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(set(json.loads(result.stdout)),
                         bridge.STATE_KEYS - {"admissible_commands"})
        self.assertNotIn("SECRET", result.stdout)


if __name__ == "__main__":
    unittest.main()
