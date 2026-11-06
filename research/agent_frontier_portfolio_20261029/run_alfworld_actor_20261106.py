"""Fresh single-episode ALFWorld actor. Preflight/mock never contact a model.

Execute requires a frozen manifest SHA and an exclusive reservation. This is a
PDDL-only compatibility adapter with native admissible commands exposed equally
in all future arms. No actor history is mounted or reused.
"""
from __future__ import annotations
import argparse
import ast
import hashlib
import http.server
import json
import os
from pathlib import Path
import signal
import socket
import socketserver
import subprocess
import sys
import threading
import time

REPO = Path(__file__).resolve().parents[2]
QUAL = Path("/home/testuser/wzh/research_evidence/agent_learning_20261030/alfworld_text_qualification_20261106")
PROFILE_ROOT = QUAL.parent / "django_aggregation_agent_20261106"
PROFILE_PINS = {
    "student8b": ("model_profile.json", "acce24743e43c205b605b8bceddd4f5eb756d93fdba5f58e28bc32ba772ab6d0"),
    "teacher27b": ("qwen38_27b_model_profile_v1.json", "9cbb51bb6dc64583cb376f81e8f8c1c28400cb494fce2793f1fa2ce60e39a279"),
}
RUNTIME_ROOT = PROFILE_ROOT / "actor_source_v2"
RUNTIME_SHA = "f76dc69ba650e61c49a81611392dabf15b65c5d67b7c8fc0ae03bac10c10c16c"
BINARY = Path("/home/testuser/.opencode/bin/opencode")
BINARY_SHA = "915ca1cd9eb5a7b3e15bd89dc71c38cf0caa9a02d13c5371422675b4b370bffb"
BRIDGE = REPO / "scripts/graph/research_alfworld_bridge.py"
BRIDGE_SHA = "37ea21a558c73068b84958ba3862c01f31c8c719f61cb011399004c0ce8bbce5"
PRIMITIVES = REPO / "research/agent_frontier_portfolio_20261029/run_django_aggregation_agent_20261106.py"
MAX_POSTS, MAX_SECONDS, MAX_BYTES, MAX_ACTIONS = 48, 1200, 6_000_000, 100
IMAGE = "python:3.12-slim"
GAME_IDS = ("clean_apple_diningtable19", "heat_apple_countertop2")
sys.path.insert(0, str(REPO))
from scripts.graph import research_auto_record as records
from scripts.graph import research_actor_dependencies as dependencies
from scripts.graph import research_teacher_backend as teacher


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_new(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    records._write_new(path, value)


def load_relay():
    """Reuse the standalone stdlib response relay without importing its harness."""
    tree = ast.parse(PRIMITIVES.read_text())
    node = next(n for n in tree.body if isinstance(n, ast.FunctionDef)
                and n.name == "relay_one_model_response")
    namespace = {}
    exec(compile(ast.Module(body=[node], type_ignores=[]), str(PRIMITIVES), "exec"), namespace)
    return namespace[node.name]


def load_profile(backend):
    filename, digest = PROFILE_PINS[backend]
    path = PROFILE_ROOT / filename
    if path.is_symlink() or sha(path) != digest:
        raise ValueError("model profile changed")
    profile = json.loads(path.read_text())
    if backend == "teacher27b":
        teacher.validate_vllm_model_profile(path, digest, full=False)
    if (profile["host"], profile["context"], profile["output"]) != ("127.0.0.1", 32768, 8192):
        raise ValueError("unexpected model profile")
    return profile


def model_payload(value, backend, profile, seed):
    value = dict(value)
    value.update(model=profile["model_id"], seed=seed, temperature=0.2,
                 max_tokens=profile["output"], stream=True,
                 stream_options={"include_usage": True})
    if backend == "teacher27b":
        value["chat_template_kwargs"] = {"enable_thinking": False}
    else:
        value.pop("chat_template_kwargs", None)
    return value


def config(profile, seed):
    tools = {"*": False, "bash": True}
    permission = {"*": "deny", "bash": "allow"}
    alias = profile["model_id"]
    return {
        "autoupdate": False, "model": "gb10/" + alias,
        "provider": {"gb10": {
            "npm": "@ai-sdk/openai-compatible", "name": "local",
            "options": {"baseURL": "http://127.0.0.1:18004/v1",
                        "timeout": 900000, "maxRetries": 0},
            "models": {alias: {"name": alias, "limit": {
                "context": profile["context"], "output": profile["output"]}}}}},
        "tools": tools, "permission": permission,
        "agent": {"build": {"temperature": 0.2, "seed": seed,
                            "tools": tools, "permission": permission}}}


def task_prompt(initial):
    return (
        "Complete this single household task by interacting with the environment.\n"
        "Initial public reset observation and goal:\n" + initial["observation"] + "\n\n"
        "Use only Bash and this client, with one environment action per tool call:\n"
        "/runtime/bin/python -B /world/client.py step --socket /world/s --action '<one exact action>'\n"
        "Read each returned observation before choosing the next action. Native "
        "admissible_commands are an additional public sensor; use them. Every "
        "accepted action, including look, consumes one real environment step. "
        "The initial snapshot is cached, never fresh evidence after an action. "
        "Continue autonomously without asking for permission. Stop when done is true. "
        "Report success only when an actual response has won=true. Use this episode "
        "only; there is no history, reset or game-selection operation.\n"
        "Initial public state:\n" + json.dumps(initial, ensure_ascii=True)
    )


GUEST = r'''import json,os,pathlib,select,socket,subprocess,sys,threading
assert os.getuid()==int(sys.argv[2]) and os.environ["HOME"]=="/workspace"
assert os.access("/workspace",os.W_OK) and not pathlib.Path("/home/testuser/wzh/research_evidence").exists()
print(json.dumps({"type":"runner_environment","uid":os.getuid(),"home":os.environ["HOME"],
 "workspace_writable":True,"private_evidence_mounted":False,"python":sys.version.split()[0]}),flush=True)
def proxy(client):
 upstream=socket.socket(socket.AF_UNIX);upstream.connect("/model/s")
 try:
  while True:
   ready,_,_=select.select([client,upstream],[],[],900)
   if not ready:return
   for stream in ready:
    data=stream.recv(65536)
    if not data:return
    (upstream if stream is client else client).sendall(data)
 finally:client.close();upstream.close()
listener=socket.socket();listener.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
listener.bind(("127.0.0.1",18004));listener.listen(8)
def serve():
 while True:
  client,_=listener.accept();threading.Thread(target=proxy,args=(client,),daemon=True).start()
threading.Thread(target=serve,daemon=True).start()
prompt=pathlib.Path("/workspace/task.txt").read_text()
result=subprocess.run(["/opt/opencode","run","--pure","--format","json","-m",sys.argv[1],
 "--title","alfworld-no-history",prompt],stdin=subprocess.DEVNULL)
raise SystemExit(result.returncode)
'''


def docker_command(work, world, model, manifest, name):
    return [
        "docker", "run", "--name", name, "--rm", "--pull", "never",
        "--network", "none", "--read-only", "--cpus", "1", "--memory", "2g",
        "--pids-limit", "128", "--cap-drop", "ALL", "--security-opt", "no-new-privileges",
        "--user", str(manifest["uid"]) + ":" + str(manifest["gid"]),
        "--tmpfs", "/tmp:rw,nosuid,nodev,size=128m",
        "--mount", "type=bind,src=" + str(work) + ",dst=/workspace",
        "--mount", "type=bind,src=" + str(world) + ",dst=/world,readonly",
        "--mount", "type=bind,src=" + str(model) + ",dst=/model,readonly",
        "--mount", "type=bind,src=" + str(RUNTIME_ROOT / "runtime") + ",dst=/runtime,readonly",
        "--mount", "type=bind,src=" + str(BINARY) + ",dst=/opt/opencode,readonly",
        "--workdir", "/workspace", "--env", "HOME=/workspace",
        "--env", "XDG_CONFIG_HOME=/workspace/.config",
        "--env", "XDG_DATA_HOME=/workspace/.local/share",
        "--env", "XDG_CACHE_HOME=/workspace/.cache",
        "--env", "LD_LIBRARY_PATH=/runtime/lib", "--env", "PYTHONDONTWRITEBYTECODE=1",
        "--env", "OPENCODE_DISABLE_MODELS_FETCH=1",
        "--entrypoint", "/runtime/bin/python", manifest["image_id"],
        "-B", "/workspace/guest.py", "gb10/" + manifest["model_id"], str(manifest["uid"])]


def socket_directory(prefix):
    for character in "0123456789abcdefghijklmnopqrstuvwxyz":
        path = QUAL / (prefix + character)
        try:
            path.mkdir()
            if len(os.fsencode(str(path / "s"))) > 103:
                raise ValueError("UDS pathname exceeds 103 bytes")
            return path
        except FileExistsError:
            continue
    raise RuntimeError("no free short socket slot")


def cleanup_directory(path):
    if Path(path).parent.resolve() != QUAL.resolve():
        raise ValueError("socket cleanup outside qualification root")
    for child in Path(path).iterdir():
        if child.name not in {"s", "client.py", "initial_reset_snapshot.json"}:
            raise ValueError("unexpected socket directory artifact")
        child.unlink()
    Path(path).rmdir()


def start_world(root, game_id, seed, label):
    rows = json.loads((QUAL / "assets/dev_game_manifest.json").read_text())
    game = rows[GAME_IDS.index(game_id)]
    if sha(game["game_path"]) != game["sha256_game"] or sha(BRIDGE) != BRIDGE_SHA:
        raise ValueError("world asset or bridge changed")
    public = socket_directory("w")
    (public / "client.py").write_bytes(BRIDGE.read_bytes())
    log = root / (label + "_world.jsonl")
    argv = [str(QUAL / "venv/bin/python"), "-B", str(BRIDGE), "serve",
            "--socket", str(public / "s"), "--trajectory", str(log),
            "--game-id", game_id, "--game-file", game["game_path"], "--seed", str(seed),
            "--step-cap", str(MAX_ACTIONS), "--admissible-commands"]
    output = (root / (label + "_world.stdout")).open("xb")
    errors = (root / (label + "_world.stderr")).open("xb")
    process = subprocess.Popen(argv, stdout=output, stderr=errors,
                               env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
    until = time.monotonic() + 20
    while not (public / "s").exists() and process.poll() is None and time.monotonic() < until:
        time.sleep(0.02)
    if not (public / "s").exists():
        stop_world((process, public, output, errors))
        raise RuntimeError("owned world bridge did not start")
    write_new(root / (label + "_world_command.json"), {"argv": argv, "pid": process.pid})
    initial = json.loads((public / "initial_reset_snapshot.json").read_text())
    return (process, public, output, errors), initial, game


def stop_world(handle):
    process, public, output, errors = handle
    try:
        if process.poll() is None:
            process.send_signal(signal.SIGTERM)
        process.wait(timeout=8)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)
    finally:
        output.close()
        errors.close()
        cleanup_directory(public)


def components():
    paths = [Path(__file__), BRIDGE, PRIMITIVES,
             REPO / "scripts/graph/research_auto_record.py",
             REPO / "scripts/graph/research_evidence_graph.py",
             REPO / "scripts/graph/research_actor_dependencies.py",
             REPO / "scripts/graph/research_teacher_backend.py"]
    return {str(path): sha(path) for path in paths}


def preflight(root, backend, game_id, seed):
    root = Path(root).resolve()
    if QUAL.resolve() not in root.parents or root == QUAL:
        raise ValueError("run root must be inside private qualification root")
    root.mkdir(parents=True, exist_ok=True)
    if any(root.iterdir()):
        raise FileExistsError("preflight requires a fresh empty run root")
    profile = load_profile(backend)
    dependencies.verify_projection(RUNTIME_ROOT, RUNTIME_SHA)
    if sha(BINARY) != BINARY_SHA:
        raise ValueError("OpenCode binary changed")
    image = subprocess.check_output(["docker", "image", "inspect", IMAGE, "--format", "{{.Id}}"],
                                    text=True).strip()
    world = None
    try:
        world, initial, game = start_world(root, game_id, seed, "preflight")
        write_new(root / "initial_reset.json", initial)
    finally:
        if world:
            stop_world(world)
    write_new(root / "opencode_config.json", config(profile, seed))
    (root / "task.txt").write_text(task_prompt(initial), encoding="utf-8")
    manifest = {
        "version": 1, "label": "NO_HISTORY_DEV_PDDL_ONLY",
        "backend": backend, "model_id": profile["model_id"],
        "profile_path": str(PROFILE_ROOT / PROFILE_PINS[backend][0]),
        "profile_sha256": PROFILE_PINS[backend][1], "game_id": game_id,
        "game_path": game["game_path"], "game_sha256": game["sha256_game"],
        "seed": seed, "domain_randomization": "DEV_train_name_randomization",
        "admissible_commands_sensor": True, "original_paper_replication": False,
        "uid": os.getuid(), "gid": os.getgid(), "image_id": image,
        "runtime_manifest_sha256": RUNTIME_SHA, "opencode_binary_sha256": BINARY_SHA,
        "components": components(), "config_sha256": sha(root / "opencode_config.json"),
        "prompt_sha256": sha(root / "task.txt"), "initial_sha256": sha(root / "initial_reset.json"),
        "caps": {"posts": MAX_POSTS, "seconds": MAX_SECONDS, "world_actions": MAX_ACTIONS,
                 "model_payload_bytes_combined": MAX_BYTES},
        "thinking": "explicit_false" if backend == "teacher27b" else "existing_template_default",
        "model_calls": 0, "live_endpoint_probed": False,
    }
    write_new(root / "manifest.json", manifest)
    return manifest


class Budget:
    """Atomic per-episode POST and combined payload reservations."""
    def __init__(self, max_posts=MAX_POSTS, max_bytes=MAX_BYTES, seconds=MAX_SECONDS):
        self.lock = threading.Lock()
        self.deadline = time.monotonic() + seconds
        self.max_posts, self.max_bytes = max_posts, max_bytes
        self.posts, self.request_bytes, self.response_bytes = 0, 0, 0
        self.failed = False

    def reserve(self, size):
        with self.lock:
            if (self.failed or time.monotonic() >= self.deadline or
                    self.posts >= self.max_posts or
                    self.request_bytes + self.response_bytes + size > self.max_bytes):
                raise ValueError("episode model budget closed")
            self.posts += 1
            self.request_bytes += size
            return self.posts

    def response(self, size):
        with self.lock:
            if (self.failed or time.monotonic() >= self.deadline or
                    self.request_bytes + self.response_bytes + size > self.max_bytes):
                self.failed = True
                raise OSError("episode response budget closed")
            self.response_bytes += size

    def poison(self):
        with self.lock:
            self.failed = True


def receive_http(connection):
    data = bytearray()
    while b"\r\n\r\n" not in data:
        part = connection.recv(4096)
        if not part or len(data) + len(part) > 65536:
            raise ValueError("invalid HTTP header")
        data.extend(part)
    head, body = bytes(data).split(b"\r\n\r\n", 1)
    lines = head.split(b"\r\n")
    if lines[0] != b"POST /v1/chat/completions HTTP/1.1":
        raise ValueError("only chat-completions POST is allowed")
    headers = {}
    for line in lines[1:]:
        key, value = line.split(b":", 1)
        key = key.lower()
        if key in headers:
            raise ValueError("duplicate HTTP header")
        headers[key] = value.strip()
    if b"transfer-encoding" in headers:
        raise ValueError("chunked requests are not accepted")
    length = int(headers[b"content-length"])
    if not 0 < length <= MAX_BYTES:
        raise ValueError("request length outside budget")
    while len(body) < length:
        part = connection.recv(min(65536, length - len(body)))
        if not part:
            raise ValueError("incomplete model request")
        body += part
    if len(body) != length:
        raise ValueError("pipelined model request")
    return json.loads(body)


class ModelRelay:
    def __init__(self, root, directory, backend, profile, seed, endpoint):
        self.root, self.directory = Path(root), Path(directory)
        self.budget = Budget()
        self.relay = load_relay()
        self.owned = set()
        self.lock = threading.Lock()
        self.tools = []
        self.errors = []
        self.forwarded = 0
        self.closing = False
        owner = self

        class Handler(socketserver.BaseRequestHandler):
            def handle(self):
                self.request.settimeout(20)
                upstream = None
                try:
                    incoming = receive_http(self.request)
                    with owner.lock:
                        observed = len(owner.tools)
                        owner.tools.append({"post": None, "definitions": incoming.get("tools", [])})
                    write_new(owner.root / "observed_requests" / (str(observed + 1).zfill(5) + ".json"), incoming)
                    names = [t["function"]["name"] for t in incoming.get("tools", [])]
                    if any(name != "bash" for name in names):
                        raise ValueError("unexpected exposed tool")
                    payload = model_payload(incoming, backend, profile, seed)
                    body = json.dumps(payload, separators=(",", ":")).encode()
                    index = owner.budget.reserve(len(body))
                    write_new(owner.root / "requests" / (str(index).zfill(5) + ".json"),
                              {"incoming": incoming, "forwarded": payload})
                    with owner.lock:
                        owner.tools[observed]["post"] = index
                    upstream = socket.create_connection(endpoint, timeout=20)
                    packet = (b"POST /v1/chat/completions HTTP/1.1\r\nHost: local\r\n"
                              b"Content-Type: application/json\r\nConnection: close\r\nContent-Length: "
                              + str(len(body)).encode() + b"\r\n\r\n" + body)
                    owner.forward(upstream, packet)

                    class CountedClient:
                        def sendall(self, data):
                            owner.budget.response(len(data))
                            self_socket.sendall(data)

                    self_socket = self.request
                    result = owner.relay(CountedClient(), upstream,
                                         owner.root / "responses" / (str(index).zfill(5) + ".body"))
                    if result["status"] >= 400:
                        owner.budget.poison()
                except Exception as exc:
                    with owner.lock:
                        owner.errors.append({"type": type(exc).__name__, "detail": str(exc)})
                    owner.budget.poison()
                    try:
                        self.request.sendall(b"HTTP/1.1 403 Forbidden\r\nContent-Length: 0\r\n"
                                             b"Connection: close\r\n\r\n")
                    except OSError:
                        pass
                finally:
                    if upstream:
                        with owner.lock:
                            owner.owned.discard(upstream)
                        upstream.close()

        class Server(socketserver.ThreadingUnixStreamServer):
            daemon_threads = False

        self.server = Server(str(self.directory / "s"), Handler)
        os.chmod(self.directory / "s", 0o600)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def forward(self, upstream, packet):
        # A socket connected after shutdown began must never escape the close snapshot.
        with self.lock:
            with self.budget.lock:
                if self.closing or self.budget.failed or time.monotonic() >= self.budget.deadline:
                    raise OSError("model relay closing")
                self.owned.add(upstream)
                upstream.sendall(packet)
                self.forwarded += 1

    def begin_close(self):
        with self.lock:
            self.closing = True
            self.budget.poison()

    def close(self):
        self.begin_close()
        self.server.shutdown()
        with self.lock:
            owned = list(self.owned)
        for connection in owned:
            try:
                connection.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            connection.close()
        # Non-daemon handlers finish response receipts before the final cost snapshot.
        self.server.server_close()
        self.thread.join(timeout=3)
        cleanup_directory(self.directory)


def verify_manifest(root, digest):
    root = Path(root).resolve()
    if QUAL.resolve() not in root.parents or sha(root / "manifest.json") != digest:
        raise ValueError("frozen manifest mismatch")
    manifest = json.loads((root / "manifest.json").read_text())
    if manifest["components"] != components():
        raise ValueError("runner or shared component changed")
    for filename, key in (("opencode_config.json", "config_sha256"), ("task.txt", "prompt_sha256"),
                          ("initial_reset.json", "initial_sha256")):
        if sha(root / filename) != manifest[key]:
            raise ValueError("frozen input changed")
    if sha(manifest["game_path"]) != manifest["game_sha256"] or sha(BINARY) != BINARY_SHA:
        raise ValueError("world asset or OpenCode changed")
    if (os.getuid(), os.getgid()) != (manifest["uid"], manifest["gid"]):
        raise ValueError("run owner changed")
    dependencies.verify_projection(RUNTIME_ROOT, RUNTIME_SHA)
    return manifest


def execute(root, digest, *, mock_endpoint=None):
    """Only explicit CLI execute reaches a real endpoint; mocks use an owned port."""
    root = Path(root).resolve()
    manifest = verify_manifest(root, digest)
    write_new(root / "reservation.json", {"manifest_sha256": digest,
              "mode": "MOCK_ORACLE_CONTROL" if mock_endpoint else "REAL_NO_HISTORY_EPISODE"})
    profile = load_profile(manifest["backend"])
    world = relay = None
    model_dir = None
    start = time.monotonic()
    name = "alfworld-owned-" + str(os.getpid()) + "-" + str(time.monotonic_ns())
    status, docker_exit = "FAILED", None
    try:
        world, initial, _ = start_world(root, manifest["game_id"], manifest["seed"], "execute")
        if initial != json.loads((root / "initial_reset.json").read_text()):
            raise ValueError("reset differs from frozen initial state")
        work = root / "workspace"
        work.mkdir()
        (work / "opencode.json").write_bytes((root / "opencode_config.json").read_bytes())
        (work / "task.txt").write_bytes((root / "task.txt").read_bytes())
        (work / "guest.py").write_text(GUEST)
        model_dir = socket_directory("m")
        endpoint = mock_endpoint or (profile["host"], profile["port"])
        relay = ModelRelay(root, model_dir, manifest["backend"], profile, manifest["seed"], endpoint)
        argv = docker_command(work, world[1], model_dir, manifest, name)
        write_new(root / "docker_command.json", {"argv": argv})
        with (root / "raw.jsonl").open("xb") as raw, (root / "docker.stderr").open("xb") as errors:
            result = subprocess.run(argv, stdout=raw, stderr=errors,
                                    timeout=max(1, MAX_SECONDS - (time.monotonic() - start)))
            docker_exit = result.returncode
        status = "RETURNED"
    except subprocess.TimeoutExpired:
        status = "EPISODE_TIMEOUT"
    finally:
        # Exact owned resources only; attempt every cleanup even if one fails.
        cleanup_errors = []
        if relay:
            relay.begin_close()
        try:
            subprocess.run(["docker", "rm", "-f", name], stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL, timeout=15)
        except Exception as exc:
            cleanup_errors.append({"resource": "owned_container", "error": repr(exc)})
        for resource, close in (("model_relay", relay.close if relay else
                                (lambda: cleanup_directory(model_dir)) if model_dir else None),
                                ("world_bridge", (lambda: stop_world(world)) if world else None)):
            if close:
                try:
                    close()
                except Exception as exc:
                    cleanup_errors.append({"resource": resource, "error": repr(exc)})
        if relay:
            write_new(root / "actual_tool_definitions.json", relay.tools)
            write_new(root / "relay_errors.json", relay.errors)
        events = [json.loads(line) for line in (root / "execute_world.jsonl").read_text().splitlines()] if (root / "execute_world.jsonl").exists() else []
        states = [event["state"] for event in events if event.get("event") in {"reset", "step"}]
        final = states[-1] if states else None
        responses = [json.loads(path.read_text()) for path in sorted((root / "responses").glob("*.receipt.json"))]
        token_parse_error = None
        try:
            tokens = records._raw_step_tokens(root / "raw.jsonl") if (root / "raw.jsonl").exists() else []
        except (ValueError, OSError) as exc:
            tokens = None
            token_parse_error = {"type": type(exc).__name__, "error": str(exc)}
        receipt = {
            "label": "MOCK_ORACLE_CONTROL" if mock_endpoint else "NO_HISTORY_DEV_PDDL_ONLY",
            "status": "CLEANUP_INCOMPLETE" if cleanup_errors else status,
            "cleanup_errors": cleanup_errors, "docker_exit": docker_exit, "manifest_sha256": digest,
            "elapsed_seconds": time.monotonic() - start,
            "model_posts": relay.budget.posts if relay else 0,
            "model_request_payload_bytes": relay.budget.request_bytes if relay else 0,
            "model_response_wire_bytes": relay.budget.response_bytes if relay else 0,
            "forwarded_model_posts": relay.forwarded if relay else 0,
            "real_model_calls": 0 if mock_endpoint else (relay.forwarded if relay else 0),
            "response_receipts": responses, "raw_step_tokens_separate_not_added": tokens,
            "raw_token_parse_error": token_parse_error,
            "unknown_usage_responses": sum(not row.get("usage") for row in responses),
            "unknown_usage_model_posts": max(0, (relay.forwarded if relay else 0) -
                sum(bool(row.get("complete") and row.get("usage")) for row in responses)),
            "final_world_state": final, "won": bool(final and final["won"]),
            "world_actions": final["action_count"] if final else 0,
            "public_sensor": "native_admissible_commands_same_all_future_arms",
            "original_paper_replication": False,
        }
        write_new(root / "receipt.json", receipt)
    return receipt


def mock_control(root, backend, game_id, seed):
    """Owned fake HTTP tests tool plumbing, never genuine policy or experience."""
    manifest = preflight(root, backend, game_id, seed)
    lock = threading.Lock()
    issued = [False]

    class Mock(http.server.BaseHTTPRequestHandler):
        def do_POST(self):
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            with lock:
                tool = bool(body.get("tools")) and not issued[0]
                if tool:
                    issued[0] = True
            if tool:
                delta = {"tool_calls": [{"index": 0, "id": "owned_mock_look",
                         "type": "function", "function": {"name": "bash", "arguments": json.dumps({
                         "command": "/runtime/bin/python -B /world/client.py step --socket /world/s --action look",
                         "description": "MOCK oracle socket control", "timeout": 20000})}}]}
                reason = "tool_calls"
            else:
                delta, reason = {"content": "MOCK control complete; no policy result."}, "stop"
            chunk = {"id": "owned_mock", "object": "chat.completion.chunk", "model": body["model"],
                     "choices": [{"index": 0, "delta": delta, "finish_reason": reason}],
                     "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}}
            data = ("data: " + json.dumps(chunk) + "\n\ndata: [DONE]\n\n").encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Connection", "close")
            self.end_headers()
            self.wfile.write(data)

        def log_message(self, *_):
            pass

    with http.server.ThreadingHTTPServer(("127.0.0.1", 0), Mock) as server:
        endpoint = server.server_address
        assert endpoint[1] not in {18104, 8006, 8004}
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            receipt = execute(root, sha(Path(root) / "manifest.json"), mock_endpoint=endpoint)
        finally:
            server.shutdown()
            thread.join(timeout=3)
    definitions = json.loads((Path(root) / "actual_tool_definitions.json").read_text())
    names = {t["function"]["name"] for row in definitions for t in row["definitions"]}
    raw = [json.loads(line) for line in (Path(root) / "raw.jsonl").read_text().splitlines()]
    environment = next(row for row in raw if row.get("type") == "runner_environment")
    if (names != {"bash"} or not issued[0] or receipt["world_actions"] != 1 or
            environment["uid"] != manifest["uid"] or not environment["workspace_writable"]):
        raise ValueError("MOCK tool/UID/socket control failed")
    write_new(Path(root) / "mock_control_verified.json", {
        "label": "MOCK_ORACLE_NOT_POLICY", "tools": sorted(names), "world_actions": 1,
        "real_model_calls": 0, "environment": environment})
    return receipt


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--preflight-only", action="store_true")
    mode.add_argument("--execute", action="store_true", help="D only; one fresh reserved episode")
    mode.add_argument("--mock-control", action="store_true", help="owned fake HTTP; zero model")
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--backend", choices=PROFILE_PINS, default="student8b")
    parser.add_argument("--game-id", choices=GAME_IDS, default=GAME_IDS[0])
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--manifest-sha")
    args = parser.parse_args(argv)
    if not 0 <= args.seed < 2**32:
        parser.error("seed outside uint32 range")
    if args.execute:
        if not args.manifest_sha:
            parser.error("--execute requires frozen --manifest-sha")
        result = execute(args.run_root, args.manifest_sha)
    elif args.mock_control:
        result = mock_control(args.run_root, args.backend, args.game_id, args.seed)
    else:
        result = preflight(args.run_root, args.backend, args.game_id, args.seed)
    print(json.dumps({"run_root": str(args.run_root), "result": result}, ensure_ascii=True))


if __name__ == "__main__":
    main()
