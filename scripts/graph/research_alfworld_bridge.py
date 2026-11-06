"""One fixed ALFWorld DEV episode over a bounded Unix socket.

The actor protocol has only {"action": "..."}; there is no observe/reset/admin RPC.
initial_reset_snapshot.json is a cached reset snapshot, never fresh step evidence.
Every accepted action, including 'look', advances the native environment once.
'done' includes the D-selected step cap. Transport failures are never retried:
an action may already have committed; only D may inspect the private trajectory.
ALFWorld imports happen only in serve mode. The stdlib client supports Python 3.8.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import math
import os
from pathlib import Path
import signal
import socket
import socketserver
import sys
import threading
from typing import Any

MAX_ACTION_BYTES = 256
MAX_REQUEST_BYTES = 2048
MAX_RESPONSE_BYTES = 524288
MAX_OBSERVATION_BYTES = 65536
ERRORS = frozenset({
    "invalid_request", "invalid_action", "episode_done", "budget_exhausted",
    "environment_failure", "trajectory_failure", "transport_error",
    "invalid_response", "startup_error",
})
DEV_GAMES = {
    "clean_apple_diningtable19": "353f22a6fc8a6116a5ae97da5eefb25722091a6767f94ad6e32418e419b23acc",
    "heat_apple_countertop2": "0a7ff3f112f426f3a1ba5d68cbfa39f1ce1e2a7045dfff7a9be603ae32a1f721",
}
STATE_KEYS = frozenset({"observation", "score", "done", "won", "action_count",
                        "admissible_commands"})


class BridgeError(Exception):
    """A fixed public error code, without native exception details."""

    def __init__(self, code: str):
        if code not in ERRORS:
            raise ValueError("unknown public error")
        self.code = code
        super().__init__(code)


def validate_request(value: Any) -> str:
    if type(value) is not dict or set(value) != {"action"}:
        raise BridgeError("invalid_request")
    action = value["action"]
    if type(action) is not str or not action or action.strip() != action:
        raise BridgeError("invalid_request")
    try:
        valid = len(action.encode("utf-8")) <= MAX_ACTION_BYTES
    except UnicodeError:
        valid = False
    if not valid or any(ord(c) < 32 or ord(c) == 127 for c in action):
        raise BridgeError("invalid_request")
    return action


def _json_object(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise BridgeError("invalid_request")
        value[key] = item
    return value


def _decode(data: bytes):
    try:
        return json.loads(data.decode("utf-8"), object_pairs_hook=_json_object,
                          parse_constant=lambda _: (_ for _ in ()).throw(ValueError()))
    except (ValueError, UnicodeError, RecursionError):
        raise BridgeError("invalid_request") from None


def _line(conn, limit: int) -> bytes:
    data = bytearray()
    while True:
        part = conn.recv(min(4096, limit + 1 - len(data)))
        if not part:
            raise BridgeError("invalid_request")
        data.extend(part)
        if len(data) > limit:
            raise BridgeError("invalid_request")
        if b"\n" in data:
            if not data.endswith(b"\n") or data.count(b"\n") != 1:
                raise BridgeError("invalid_request")
            return bytes(data[:-1])


def _encoded(value) -> bytes:
    return (json.dumps(value, ensure_ascii=True, allow_nan=False,
                       separators=(",", ":")) + "\n").encode("utf-8")


class PublicTrajectory:
    """Exclusive creation, then append only; caller supplies public metadata."""

    def __init__(self, path: Path, metadata: dict):
        self.path = Path(path).resolve()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.fd = os.open(str(self.path), os.O_WRONLY | os.O_CREAT | os.O_EXCL |
                          os.O_APPEND, 0o600)
        self.append({"event": "episode", **metadata})

    def append(self, value: dict):
        if self.fd is None:
            raise OSError("trajectory is closed")
        data = _encoded(value)
        while data:
            written = os.write(self.fd, data)
            if written <= 0:
                raise OSError("trajectory write failed")
            data = data[written:]
        os.fsync(self.fd)

    def close(self):
        if self.fd is not None:
            os.close(self.fd)
            self.fd = None


class Episode:
    """Own exactly one backend. Native mutation and receipt are serialized."""

    def __init__(self, backend, step_cap: int, trajectory: PublicTrajectory,
                 show_admissible: bool = False):
        if type(step_cap) is not int or not 1 <= step_cap <= 500:
            raise ValueError("step cap must be 1..500")
        self.backend = backend
        self.step_cap = step_cap
        self.trajectory = trajectory
        self.show_admissible = show_admissible
        self.lock = threading.Lock()
        self.action_count = 0
        self.stop_reason = None
        observation, infos = backend.reset()
        self._accept_state(observation, 0.0, False, infos)
        self.trajectory.append({"event": "reset", "state": self.snapshot()})

    def _accept_state(self, observation, score, done, infos):
        if (type(observation) is not str or
                len(observation.encode("utf-8")) > MAX_OBSERVATION_BYTES or
                not isinstance(score, (int, float)) or not math.isfinite(score)):
            raise BridgeError("environment_failure")
        commands = infos.get("admissible_commands")
        if (type(commands) is not list or len(commands) > 1024 or
                any(type(c) is not str or not c or
                    len(c.encode("utf-8")) > MAX_ACTION_BYTES for c in commands)):
            raise BridgeError("environment_failure")
        self.observation = observation
        self.score = float(score)
        self.won = bool(infos.get("won", False))
        self.commands = list(commands)
        if done or self.won:
            self.stop_reason = "episode_done"
        elif self.action_count >= self.step_cap:
            self.stop_reason = "budget_exhausted"

    def snapshot(self) -> dict:
        state = {"observation": self.observation, "score": self.score,
                 "done": self.stop_reason is not None, "won": self.won,
                 "action_count": self.action_count}
        if self.show_admissible:
            state["admissible_commands"] = list(self.commands)
        return state

    def apply(self, request: Any) -> dict:
        action = validate_request(request)
        with self.lock:
            if self.stop_reason:
                raise BridgeError(self.stop_reason)
            if action not in self.commands:
                raise BridgeError("invalid_action")
            self.action_count += 1
            try:
                observation, score, done, infos = self.backend.step(action)
                self._accept_state(observation, score, done, infos)
            except Exception:
                self.stop_reason = "environment_failure"
                try:
                    self.trajectory.append({"event": "error",
                                            "error": self.stop_reason,
                                            "action_count": self.action_count})
                except OSError:
                    self.stop_reason = "trajectory_failure"
                raise BridgeError(self.stop_reason) from None
            state = self.snapshot()
            try:
                self.trajectory.append({"event": "step", "action": action,
                                        "state": state})
            except OSError:
                self.stop_reason = "trajectory_failure"
                raise BridgeError(self.stop_reason) from None
            return state

    def close(self):
        try:
            self.backend.close()
        finally:
            self.trajectory.close()


class NativeBackend:
    """Official PDDL backend and ALFWorld demangler; no expert/facts wrapper."""

    def __init__(self, game: Path, seed: int):
        import random
        import numpy as np
        import textworld
        from textworld.envs.pddl import PddlEnv
        from alfworld.agents.environment.alfred_tw_env import AlfredDemangler

        # This server process owns its RNG. Match DEV train-mode name shuffling.
        random.seed(seed)
        np.random.seed(seed)
        infos = textworld.EnvInfos(won=True, admissible_commands=True)
        self.env = AlfredDemangler(PddlEnv(infos), shuffle=True)
        self.env.load(str(game))

    @staticmethod
    def _public_native_infos(state):
        return {"won": bool(state.won),
                "admissible_commands": list(state.admissible_commands)}

    def reset(self):
        state = self.env.reset()
        return state.feedback, self._public_native_infos(state)

    def step(self, action):
        state, score, done = self.env.step(action)
        return state.feedback, score, done, self._public_native_infos(state)

    def close(self):
        self.env.close()


def serve(socket_path: Path, episode: Episode, stop: threading.Event,
          ready: threading.Event | None = None):
    """D owns startup/shutdown. The socket accepts one bounded request/connection."""
    socket_path = Path(socket_path)
    directory = socket_path.parent.resolve()
    if (len(os.fsencode(str(socket_path))) > 103 or
            episode.trajectory.path == directory or
            directory in episode.trajectory.path.parents):
        raise BridgeError("startup_error")
    directory.mkdir(parents=True, exist_ok=True)
    if any(child.name != "client.py" or child.is_symlink() or not child.is_file()
           for child in directory.iterdir()):
        raise BridgeError("startup_error")
    # This directory contains only the socket, cached public initial snapshot,
    # and (if D copies it here) this stdlib client. Never place assets/logs here.
    initial = directory / "initial_reset_snapshot.json"
    with initial.open("x", encoding="utf-8") as stream:
        json.dump(episode.snapshot(), stream, ensure_ascii=True, allow_nan=False)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())

    class Handler(socketserver.BaseRequestHandler):
        def handle(self):
            self.request.settimeout(5.0)
            try:
                value = _decode(_line(self.request, MAX_REQUEST_BYTES))
                response = episode.apply(value)
            except BridgeError as exc:
                response = {"error": exc.code}
            except (OSError, ValueError):
                response = {"error": "invalid_request"}
            try:
                self.request.sendall(_encoded(response))
            except OSError:
                pass  # Never retry a native action after an ambiguous response.

    with socketserver.UnixStreamServer(str(socket_path), Handler) as server:
        os.chmod(socket_path, 0o600)
        inode = socket_path.stat().st_ino
        server.timeout = 0.1
        if ready:
            ready.set()
        try:
            while not stop.is_set():
                server.handle_request()
        finally:
            if socket_path.exists() and socket_path.stat().st_ino == inode:
                socket_path.unlink()


def validate_response(value: Any) -> dict:
    if type(value) is not dict:
        raise BridgeError("invalid_response")
    if set(value) == {"error"}:
        if type(value["error"]) is not str or value["error"] not in ERRORS:
            raise BridgeError("invalid_response")
        return value
    required = STATE_KEYS - {"admissible_commands"}
    if not required <= set(value) or not set(value) <= STATE_KEYS:
        raise BridgeError("invalid_response")
    if (type(value["observation"]) is not str or
            len(value["observation"].encode("utf-8")) > MAX_OBSERVATION_BYTES or
            type(value["done"]) is not bool or type(value["won"]) is not bool or
            type(value["action_count"]) is not int or value["action_count"] < 0 or
            type(value["score"]) not in (int, float) or
            abs(value["score"]) > 1e100 or
            not math.isfinite(value["score"])):
        raise BridgeError("invalid_response")
    if "admissible_commands" in value and (
            type(value["admissible_commands"]) is not list or
            any(type(c) is not str for c in value["admissible_commands"])):
        raise BridgeError("invalid_response")
    return value


def client_step(socket_path: Path, action: str, timeout: float = 10.0) -> dict:
    validate_request({"action": action})
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as conn:
            conn.settimeout(timeout)
            conn.connect(str(socket_path))
            conn.sendall(_encoded({"action": action}))
            return validate_response(_decode(_line(conn, MAX_RESPONSE_BYTES)))
    except (OSError, BridgeError) as exc:
        if isinstance(exc, BridgeError):
            raise
        raise BridgeError("transport_error") from None


def validate_private_paths(game: Path, socket_path: Path, trajectory: Path):
    directory = Path(socket_path).parent.resolve()
    for private in (Path(game).resolve(), Path(trajectory).resolve()):
        if private == directory or directory in private.parents:
            raise BridgeError("startup_error")


def _serve_cli(args):
    game = Path(args.game_file).resolve()
    validate_private_paths(game, Path(args.socket), Path(args.trajectory))
    asset_sha = hashlib.sha256(game.read_bytes()).hexdigest()
    if asset_sha != DEV_GAMES[args.game_id]:
        raise BridgeError("startup_error")
    bridge_sha = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    metadata = {"game_id": args.game_id, "asset_sha256": asset_sha,
                "seed": args.seed, "step_cap": args.step_cap,
                "mode": "DEV_train_name_randomization",
                "bridge_sha256": bridge_sha, "python_version": sys.version.split()[0],
                "versions": {name: importlib.metadata.version(name) for name in
                             ("alfworld", "textworld", "fast-downward-textworld")},
                "compatibility": "PDDL-only build adapter; Inform7 unused"}
    metadata["episode_sha256"] = hashlib.sha256(
        _encoded(metadata)).hexdigest()
    socket_path = Path(args.socket)
    log_path = Path(args.trajectory).resolve()
    if socket_path.parent.resolve() in log_path.parents:
        raise BridgeError("startup_error")
    backend = NativeBackend(game, args.seed)
    trajectory = PublicTrajectory(log_path, metadata)
    episode = Episode(backend, args.step_cap, trajectory, args.admissible_commands)
    stop = threading.Event()
    for sig in (signal.SIGINT, signal.SIGTERM):
        signal.signal(sig, lambda *_: stop.set())
    try:
        serve(socket_path, episode, stop)
    finally:
        episode.close()


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="mode", required=True)
    server = sub.add_parser("serve", help="D-only: one fixed DEV game and seed")
    server.add_argument("--socket", required=True)
    server.add_argument("--trajectory", required=True)
    server.add_argument("--game-id", choices=sorted(DEV_GAMES), required=True)
    server.add_argument("--game-file", required=True)
    server.add_argument("--seed", type=int, required=True)
    server.add_argument("--step-cap", type=int, required=True)
    server.add_argument("--admissible-commands", action="store_true")
    client = sub.add_parser("step", help="Actor: one native step; no automatic retry")
    client.add_argument("--socket", required=True)
    client.add_argument("--action", required=True)
    args = parser.parse_args(argv)
    try:
        if args.mode == "serve":
            if not 0 <= args.seed < 2**32 or not 1 <= args.step_cap <= 500:
                raise BridgeError("startup_error")
            _serve_cli(args)
            return 0
        response = client_step(Path(args.socket), args.action)
        print(json.dumps(response, ensure_ascii=True, allow_nan=False))
        return 2 if "error" in response else 0
    except BridgeError as exc:
        print(json.dumps({"error": exc.code}))
        return 2
    except (OSError, ValueError):
        print(json.dumps({"error": "startup_error"}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
