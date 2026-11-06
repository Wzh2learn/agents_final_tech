"""Resume one frozen research OpenCode session at its replayed failed world.

Default preflight is model-free. Only explicit SHA-bound execute can forward a
real model request. Original SQLite files are read as bytes, never opened by
SQLite; recovery/checkpointing occurs only in new private copies.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import http.server
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import sqlite3
import subprocess
import threading
import time

REPO = Path(__file__).resolve().parents[2]
QUAL = Path("/home/testuser/wzh/research_evidence/agent_learning_20261030/alfworld_text_qualification_20261106")
RECOVERY_PATH = Path(__file__).with_name("run_alfworld_recovery_20261106.py")
RECOVERY_SHA = "cad06ec2b6f9e144fea29c17061b9527d07b7df13ecbf5784fb0870d9a0ce8ca"
ASSET_PATH = QUAL / "failure_context_v1/SESSION_RESUME_ASSET_V1.json"
ASSET_SHA = "22dc7b634c2d52fed2917582ecc337311267ace967006b93258f7d91174d5bc0"
MODES = ("neutral", "resume_current_state")
NEUTRAL = "Continue the unfinished task."
BRANCH = "neutral first; if neutral won, skip resume_current_state; otherwise D freezes a new state-mode attempt"
DB_NAMES = ("opencode.db", "opencode.db-wal", "opencode.db-shm")
_RECOVERY = None


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def recovery():
    global _RECOVERY
    if RECOVERY_PATH.is_symlink() or sha(RECOVERY_PATH) != RECOVERY_SHA:
        raise ValueError("frozen recovery component changed")
    if _RECOVERY is None:
        spec = importlib.util.spec_from_file_location("context_recovery_primitives", RECOVERY_PATH)
        _RECOVERY = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(_RECOVERY)
    return _RECOVERY


def asset():
    if ASSET_PATH.is_symlink() or sha(ASSET_PATH) != ASSET_SHA:
        raise ValueError("session asset manifest changed")
    value = json.loads(ASSET_PATH.read_text())
    data = recovery().source("heat2_history_v1")
    source = Path(data["binding"]["root"])
    if (value["source_root"] != str(source) or value["source_receipt_sha256"] != data["binding"]["sha256"]["receipt.json"] or
            sha(source / "raw.jsonl") != value["raw_sha256"] or not re.fullmatch(r"ses_[A-Za-z0-9]+", value["session_id"])):
        raise ValueError("session asset/source binding mismatch")
    paths = {Path(row["path"]).name: row for row in value["database_files"]}
    if set(paths) != set(DB_NAMES) or len(value["database_files"]) != 3:
        raise ValueError("only the research DB/WAL/SHM may be copied")
    expected = source / "workspace/.local/share/opencode"
    for name, row in paths.items():
        path = Path(row["path"])
        if path.is_symlink() or path.resolve() != expected / name or path.stat().st_size != row["bytes"] or sha(path) != row["sha256"]:
            raise ValueError("frozen research SQLite file changed")
    return value, data


def check_root(root, mode):
    if mode not in MODES:
        raise ValueError("unsupported context-recovery mode")
    root = Path(root)
    expected = QUAL / "failure_context_v1/heat2_history_v1/student8b" / mode
    if root.parent.resolve() != expected.resolve() or not re.fullmatch(r"attempt_v[1-9][0-9]*", root.name):
        raise ValueError("context recovery requires source/student8b/mode/attempt_vN canonical root")
    current = QUAL
    for part in expected.relative_to(QUAL).parts:
        current = current / part
        if current.is_symlink():
            raise ValueError("context-recovery namespace symlink")


def snapshot_session(value, snapshot):
    snapshot = Path(snapshot)
    snapshot.mkdir()
    for row in value["database_files"]:
        original = Path(row["path"])
        raw = original.read_bytes()
        if len(raw) != row["bytes"] or hashlib.sha256(raw).hexdigest() != row["sha256"]:
            raise ValueError("SQLite source changed during snapshot")
        with (snapshot / original.name).open("xb") as out:
            out.write(raw)
    if any(sha(row["path"]) != row["sha256"] for row in value["database_files"]):
        raise ValueError("SQLite source changed after snapshot")
    return {name: sha(snapshot / name) for name in DB_NAMES}


def derive_seed(snapshot, seed):
    snapshot, seed = Path(snapshot).resolve(), Path(seed).absolute()
    if seed == snapshot or snapshot in seed.parents or seed in snapshot.parents or seed.is_symlink():
        raise ValueError("checkpoint destination must be a separate new copy")
    seed.mkdir()
    for name in DB_NAMES:
        shutil.copyfile(snapshot / name, seed / name)
    # The frozen SHM remains in the D snapshot. Never reuse its stale reader locks.
    (seed / "opencode.db-shm").unlink()
    database = seed / "opencode.db"
    with sqlite3.connect(database) as conn:
        checkpoint = conn.execute("PRAGMA wal_checkpoint(TRUNCATE)").fetchone()
        if checkpoint[0] != 0:
            raise ValueError("copied WAL checkpoint busy")
        mode = conn.execute("PRAGMA journal_mode=DELETE").fetchone()[0]
        if mode != "delete":
            raise ValueError("copied seed journal conversion failed")
    return {"seed_sha256": sha(database), "sqlite_version": sqlite3.sqlite_version,
            "actions": ["copy frozen triplet", "remove copied SHM only", "checkpoint copied WAL TRUNCATE", "copied seed journal_mode DELETE"],
            "checkpoint": list(checkpoint), "copied_lock_directories": False, "original_DB_opened_by_SQLite": False}


def session_reference(database, value, data):
    """Read checkpointed seed only; return public context, not host credentials."""
    sid = value["session_id"]
    with sqlite3.connect(Path(database).resolve().as_uri() + "?mode=ro&immutable=1", uri=True) as conn:
        sessions = conn.execute("SELECT id,project_id,directory,model,agent,time_compacting FROM session").fetchall()
        if len(sessions) != 1 or sessions[0][:3] != (sid, "global", "/workspace") or sessions[0][4:] != ("build", None):
            raise ValueError("seed must contain only the original uncompacted research session")
        model = json.loads(sessions[0][3])
        if model.get("id") != "qwen3-8b-qual" or model.get("providerID") != "gb10":
            raise ValueError("stored session model mismatch")
        messages = [(mid, json.loads(raw)) for mid, raw in conn.execute(
            "SELECT id,data FROM message WHERE session_id=? ORDER BY time_created,id", (sid,))]
        parts = [(mid, json.loads(raw)) for mid, raw in conn.execute(
            "SELECT message_id,data FROM part WHERE session_id=? ORDER BY time_created,id", (sid,))]
    user_ids = {mid for mid, message in messages if message.get("role") == "user"}
    users = [part["text"] for mid, part in parts if mid in user_ids and part.get("type") == "text"]
    tools = [{"call_id": part["callID"], "arguments": part["state"]["input"], "output": part["state"]["output"]}
             for _, part in parts if part.get("type") == "tool" and part.get("tool") == "bash" and part["state"].get("status") == "completed"]
    assistants = [(mid, item) for mid, item in messages if item.get("role") == "assistant"]
    if not assistants or assistants[-1][1].get("finish") != "stop":
        raise ValueError("copied WAL did not restore the completed source conversation")
    final_id = assistants[-1][0]
    final = "".join(part["text"] for mid, part in parts if mid == final_id and part.get("type") == "text")
    raw = [json.loads(line) for line in (Path(value["source_root"]) / "raw.jsonl").read_text().splitlines()]
    raw_tools = [{"call_id": row["part"]["callID"], "arguments": row["part"]["state"]["input"], "output": row["part"]["state"]["output"]}
                 for row in raw if row.get("type") == "tool_use"]
    raw_final = "".join(row["part"]["text"] for row in raw if row.get("type") == "text")
    delivery = data["receipt"]["experience_delivery"]
    if (len(users) != 1 or hashlib.sha256(users[0].encode()).hexdigest() != delivery["first_forwarded_user_sha256"] or
            "<source-experience>" not in users[0] or tools != raw_tools or len(tools) != len(data["steps"]) or not final or final != raw_final):
        raise ValueError("checkpointed session does not match frozen source user/tools/final text")
    return {"session_id": sid, "users": users, "tools": tools, "final_assistant_text": final,
            "message_count": len(messages), "part_count": len(parts), "source_carrier_in_original_user": True}


def reference_metadata(reference):
    return {"session_id": reference["session_id"], "message_count": reference["message_count"], "part_count": reference["part_count"],
            "user_sha256": [hashlib.sha256(text.encode()).hexdigest() for text in reference["users"]],
            "tool_feedback_sha256": [{"call_id": item["call_id"], "output_sha256": hashlib.sha256(item["output"].encode()).hexdigest(),
                                       "arguments_sha256": digest(item["arguments"])} for item in reference["tools"]],
            "final_assistant_sha256": hashlib.sha256(reference["final_assistant_text"].encode()).hexdigest(),
            "source_carrier_in_original_user": reference["source_carrier_in_original_user"]}


def retry_prompt(mode, current):
    if mode not in MODES:
        raise ValueError("unsupported retry mode")
    return NEUTRAL if mode == "neutral" else NEUTRAL + "\nCurrent restored public environment state:\n" + json.dumps(current, ensure_ascii=False)


def session_guest(session_id):
    if not re.fullmatch(r"ses_[A-Za-z0-9]+", session_id):
        raise ValueError("invalid session id")
    guest = recovery().actor().GUEST
    old = '"--title","alfworld-no-history",prompt]'
    if guest.count(old) != 1:
        raise ValueError("unexpected frozen guest invocation")
    return guest.replace(old, '"--session",' + json.dumps(session_id) + ',prompt]')


def retention_proof(payload, reference, prompt):
    messages = payload["messages"]
    user_texts = [row.get("content") for row in messages if row.get("role") == "user"]
    results = [all(text in user_texts for text in reference["users"])]
    details = []
    for item in reference["tools"]:
        outputs = [row for row in messages if row.get("role") == "tool" and row.get("tool_call_id") == item["call_id"]]
        calls = [call for row in messages if row.get("role") == "assistant" for call in row.get("tool_calls", []) if call.get("id") == item["call_id"]]
        output_ok = any(row.get("content") == item["output"] for row in outputs)
        args_ok = any(call.get("function", {}).get("name") == "bash" and
                      (json.loads(call["function"]["arguments"]) if isinstance(call["function"].get("arguments"), str) else call["function"].get("arguments")) == item["arguments"] for call in calls)
        details.append({"call_id": item["call_id"], "feedback_equal": output_ok, "arguments_equal": args_ok})
        results.extend([output_ok, args_ok])
    final_ok = any(row.get("role") == "assistant" and row.get("content") == reference["final_assistant_text"] for row in messages)
    quoted = '"' + prompt.replace('"', chr(92) + '"') + '"'
    prompt_ok = bool(user_texts) and user_texts[-1] in (prompt, quoted)
    results.extend([final_ok, prompt_ok])
    return {"verified": all(results), "old_user_complete": results[0], "source_carrier_retained": results[0] and "<source-experience>" in reference["users"][0],
            "original_tool_feedback_count": len(details), "tool_checks": details, "original_final_assistant_retained": final_ok,
            "new_neutral_or_state_prompt_equal": prompt_ok, "source_reference_sha256": digest(reference_metadata(reference)),
            "actual_request_sha256": hashlib.sha256(json.dumps(payload, separators=(",", ":")).encode()).hexdigest(),
            "retention_proves_understanding": False, "restoration": "actual SQLite session, not text replay"}


def components():
    return {**recovery().components(), str(Path(__file__).resolve()): sha(__file__)}


def prepare(root, mode="neutral"):
    root = Path(root).resolve()
    check_root(root, mode)
    root.mkdir(parents=True, exist_ok=True)
    if any(root.iterdir()):
        raise FileExistsError("fresh context-recovery root required")
    rec = recovery();core = rec.actor();value, data = asset();profile = core.load_profile("student8b")
    snapshot_hashes = snapshot_session(value, root / "source_session_snapshot")
    derivation = derive_seed(root / "source_session_snapshot", root / "session_seed")
    reference = session_reference(root / "session_seed/opencode.db", value, data)
    world = None
    try:
        m = data["manifest"]
        world, initial, _ = core.start_world(root, m["game_id"], m["seed"], "preflight", m["caps"], m["pool_binding"]["path"], m["pool_binding"]["sha256"])
        current, replay_cost = rec.replay(data, initial, lambda action: rec.bridge().client_step(world[1] / "s", action), root / "preflight_replay.jsonl")
    finally:
        if world:
            core.stop_world(world)
    prompt = retry_prompt(mode, current)
    (root / "task.txt").write_bytes(prompt.encode())
    core.write_new(root / "handoff_public.json", current)
    core.write_new(root / "session_reference_metadata.json", reference_metadata(reference))
    original_config = Path(value["source_root"]) / "opencode_config.json"
    if sha(original_config) != data["manifest"]["config_sha256"] or sha(core.BINARY) != core.BINARY_SHA:
        raise ValueError("original actor config or binary changed")
    (root / "opencode_config.json").write_bytes(original_config.read_bytes())
    core.dependencies.verify_projection(core.RUNTIME_ROOT, core.RUNTIME_SHA)
    token_binding, qualify = rec.token_qualifier("student8b", profile)
    envelope_path = Path(value["source_root"]) / "requests" / (str(data["receipt"]["model_posts"]).zfill(5) + ".json")
    envelope = json.loads(envelope_path.read_text())["incoming"]
    envelope["messages"].extend([{"role": "assistant", "content": reference["final_assistant_text"]},
                                 {"role": "user", "content": '"' + prompt.replace('"', chr(92) + '"') + '"'}])
    sampling = core.model_payload({}, "student8b", profile, m["seed"], False)
    qualification = qualify(core.model_payload(envelope, "student8b", profile, m["seed"], False))
    if not qualification["fits"]:
        raise ValueError("projected resumed template exceeds context budget")
    image = subprocess.check_output(["docker", "image", "inspect", core.IMAGE, "--format", "{{.Id}}"], text=True).strip()
    manifest = {"version": 1, "label": "DEVELOPMENT_RETAINED_SESSION_RETRY", "mode": mode, "planned_branch": BRANCH,
        "source_binding": data["binding"], "session_asset_sha256": ASSET_SHA, "session_id": value["session_id"],
        "source_snapshot_sha256": snapshot_hashes, "seed_derivation": derivation, "reference_metadata_sha256": sha(root / "session_reference_metadata.json"),
        "source_envelope_path": str(envelope_path), "source_envelope_sha256": sha(envelope_path),
        "source_config_sha256": sha(original_config), "config_sha256": sha(root / "opencode_config.json"),
        "prompt_sha256": sha(root / "task.txt"), "handoff_sha256": sha(root / "handoff_public.json"),
        "guest_sha256": hashlib.sha256(session_guest(value["session_id"]).encode()).hexdigest(),
        "caps": data["binding"]["remaining_caps"], "total_world_step_cap": m["caps"]["world_actions"], "replay_control_cost": replay_cost,
        "backend": "student8b", "model_id": profile["model_id"], "profile_sha256": core.PROFILE_PINS["student8b"][1], "sampling": sampling,
        "tokenizer_binding": token_binding, "preflight_template_qualification": {"method": "source-last-request plus stored final assistant plus new prompt; projected, not actual new SDK request", **qualification},
        "components": components(), "uid": os.getuid(), "gid": os.getgid(), "image_id": image, "real_model_calls": 0,
        "future_confirmation_exclusion": {"game_id": m["game_id"], "layout": data["binding"]["layout"]}}
    core.write_new(root / "manifest.json", manifest)
    return manifest


def verify(root, expected_sha):
    root = Path(root).resolve()
    if sha(root / "manifest.json") != expected_sha:
        raise ValueError("context-recovery manifest changed")
    m = json.loads((root / "manifest.json").read_text());check_root(root, m["mode"])
    rec = recovery();core = rec.actor();value, data = asset();profile = core.load_profile("student8b")
    if (m["components"] != components() or m["session_asset_sha256"] != ASSET_SHA or m["source_binding"] != data["binding"] or
            m["session_id"] != value["session_id"] or m["caps"] != data["binding"]["remaining_caps"] or
            m["planned_branch"] != BRANCH or (m["uid"], m["gid"]) != (os.getuid(), os.getgid()) or
            m["sampling"] != core.model_payload({}, "student8b", profile, data["manifest"]["seed"], False) or
            m["profile_sha256"] != core.PROFILE_PINS["student8b"][1]):
        raise ValueError("frozen source/session/model/caps changed")
    for filename, key in (("task.txt", "prompt_sha256"), ("opencode_config.json", "config_sha256"), ("handoff_public.json", "handoff_sha256"), ("session_reference_metadata.json", "reference_metadata_sha256")):
        if sha(root / filename) != m[key]:
            raise ValueError("context-recovery frozen input changed")
    for name, digest_value in m["source_snapshot_sha256"].items():
        if sha(root / "source_session_snapshot" / name) != digest_value:
            raise ValueError("D session snapshot changed")
    if sha(root / "session_seed/opencode.db") != m["seed_derivation"]["seed_sha256"] or sha(m["source_envelope_path"]) != m["source_envelope_sha256"]:
        raise ValueError("derived seed or projected envelope changed")
    reference = session_reference(root / "session_seed/opencode.db", value, data)
    if json.loads((root / "session_reference_metadata.json").read_text()) != reference_metadata(reference):
        raise ValueError("checkpointed session reference changed")
    if (root / "task.txt").read_bytes() != retry_prompt(m["mode"], data["steps"][-1]["state"]).encode():
        raise ValueError("neutral/state retry instruction changed")
    if hashlib.sha256(session_guest(value["session_id"]).encode()).hexdigest() != m["guest_sha256"] or sha(core.BINARY) != core.BINARY_SHA:
        raise ValueError("session guest/binary changed")
    binding, qualify = rec.token_qualifier("student8b", profile)
    if binding != m["tokenizer_binding"]:
        raise ValueError("actual template assets changed")
    core.dependencies.verify_projection(core.RUNTIME_ROOT, core.RUNTIME_SHA)
    return m, data, profile, reference, qualify


def run(root, expected_sha, *, fake_endpoint=None):
    root = Path(root).resolve();m,data,profile,reference,qualify = verify(root, expected_sha)
    rec = recovery();core = rec.actor();core.write_new(root / "reservation.json", {"manifest_sha256": expected_sha, "mode": "OWNED_FAKE_RETAINED_SESSION" if fake_endpoint else "REAL_RETAINED_SESSION_RETRY"})
    world = relay = model_dir = None;replay_cost = None;retention = None;errors = [];status = "FAILED";docker_exit = None
    started = time.monotonic();name = "alf-context-owned-" + str(os.getpid()) + "-" + str(time.monotonic_ns())
    class ContextRelay(core.ModelRelay):
        def forward(self, upstream, packet, payload=None, post_index=None):
            nonlocal retention
            proof = qualify(payload)
            core.write_new(root / "actual_template_tokens" / (str(post_index).zfill(5) + ".json"), proof)
            if not proof["fits"]:
                raise ValueError("actual resumed template exceeds context budget")
            if retention is None:
                retention = retention_proof(payload, reference, (root / "task.txt").read_bytes().decode())
                core.write_new(root / "actual_session_retention.json", retention)
                if not retention["verified"]:
                    raise ValueError("actual first resumed request lost frozen session context")
            return super().forward(upstream, packet, payload, post_index)
    try:
        src = data["manifest"]
        world,initial,_ = core.start_world(root, src["game_id"], src["seed"], "execute", src["caps"], src["pool_binding"]["path"], src["pool_binding"]["sha256"])
        current,replay_cost = rec.replay(data, initial, lambda action: rec.bridge().client_step(world[1] / "s", action), root / "execute_replay.jsonl")
        if current != json.loads((root / "handoff_public.json").read_text()):
            raise ValueError("restored world differs from preflight")
        work = root / "workspace";work.mkdir();db_dir = work / ".local/share/opencode";db_dir.mkdir(parents=True)
        shutil.copyfile(root / "session_seed/opencode.db", db_dir / "opencode.db")
        for original,copied in (("task.txt","task.txt"),("opencode_config.json","opencode.json")):
            (work / copied).write_bytes((root / original).read_bytes())
        (work / "guest.py").write_text(session_guest(m["session_id"]))
        model_dir = core.socket_directory("m")
        relay = ContextRelay(root, model_dir, "student8b", profile, src["seed"], fake_endpoint or (profile["host"],profile["port"]), m["caps"],m["sampling"],student_enable_thinking=False)
        argv = core.docker_command(work,world[1],model_dir,m,name);core.write_new(root / "docker_command.json",{"argv":argv})
        actor_started = time.monotonic()
        with (root / "raw.jsonl").open("xb") as out,(root / "docker.stderr").open("xb") as err:
            result = subprocess.run(argv,stdout=out,stderr=err,timeout=m["caps"]["seconds"])
        docker_exit,status = result.returncode,"RETURNED"
    except subprocess.TimeoutExpired:
        status = "EPISODE_TIMEOUT"
    except Exception as exc:
        errors.append({"type":type(exc).__name__,"error":str(exc)})
    finally:
        if relay:relay.begin_close()
        try:subprocess.run(["docker","rm","-f",name],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=15)
        except Exception as exc:errors.append({"cleanup":"owned_container","error":str(exc)})
        for label,cleanup in (("relay",relay.close if relay else (lambda:core.cleanup_directory(model_dir)) if model_dir else None),("world",(lambda:core.stop_world(world)) if world else None)):
            if cleanup:
                try:cleanup()
                except Exception as exc:errors.append({"cleanup":label,"error":str(exc)})
        if relay:
            core.write_new(root / "relay_errors.json",relay.errors);core.write_new(root / "actual_tool_definitions.json",relay.tools)
        events=[json.loads(line) for line in (root / "execute_world.jsonl").read_text().splitlines()] if (root / "execute_world.jsonl").exists() else []
        states=[row["state"] for row in events if row.get("event") in {"reset","step"}];final=rec.public_state(states[-1]) if states else None
        responses=[json.loads(p.read_text()) for p in sorted((root / "responses").glob("*.receipt.json"))]
        tokens,token_error=None,None
        try:tokens=core.records._raw_step_tokens(root / "raw.jsonl") if (root / "raw.jsonl").exists() else []
        except Exception as exc:token_error=str(exc)
        work_db=root / "workspace/.local/share/opencode"
        receipt={"label":"OWNED_FAKE_RETAINED_SESSION_NOT_POLICY" if fake_endpoint else "DEVELOPMENT_RETAINED_SESSION_RETRY","mode":m["mode"],"status":status,"errors":errors,"model_relay_errors":relay.errors if relay else [],
            "manifest_sha256":expected_sha,"source_binding":data["binding"],"session_asset_sha256":ASSET_SHA,"session_id":m["session_id"],"source_formation_cost_reference_only_charge_once":data["binding"]["sha256"]["receipt.json"],
            "elapsed_seconds":time.monotonic()-started,"actor_wall_seconds":time.monotonic()-actor_started if 'actor_started' in locals() else None,"replay_control_cost":replay_cost,"caps":m["caps"],"sampling":m["sampling"],"docker_exit":docker_exit,
            "model_posts":relay.budget.posts if relay else 0,"forwarded_model_posts":relay.forwarded if relay else 0,"real_model_calls":0 if fake_endpoint else relay.forwarded if relay else 0,"fake_posts":relay.forwarded if fake_endpoint and relay else 0,
            "model_request_payload_bytes":relay.budget.request_bytes if relay else 0,"model_response_wire_bytes":relay.budget.response_bytes if relay else 0,"response_receipts":responses,"raw_step_tokens_separate_not_added":tokens,"raw_token_parse_error":token_error,
            "unknown_usage_model_posts":max(0,(relay.forwarded if relay else 0)-sum(bool(x.get('complete') and x.get('usage')) for x in responses)),
            "actual_session_retention":retention,"final_world_state":final,"won":bool(final and final['won']),"actor_world_actions":max(0,final['action_count']-len(data['steps'])) if final else 0,
            "session_files_after_sha256":{p.name:sha(p) for p in work_db.glob('opencode.db*')} if work_db.exists() else {},
            "qualified_real_correction":bool(not fake_endpoint and status=='RETURNED' and not errors and relay and not relay.errors and retention and retention['verified'] and final and final['won'] and final['done']),
            "future_confirmation_exclusion":m['future_confirmation_exclusion'],"original_session_restored_not_text_replay":True}
        core.write_new(root / "receipt.json",receipt)
    return receipt


def mock_control(root,mode="neutral"):
    prepare(root,mode);posts=[]
    class Fake(http.server.BaseHTTPRequestHandler):
        def do_POST(self):
            payload=json.loads(self.rfile.read(int(self.headers['Content-Length'])));posts.append(payload)
            if len(posts)==1:
                delta={"tool_calls":[{"index":0,"id":"context_fake_look","type":"function","function":{"name":"bash","arguments":json.dumps({"command":"/runtime/bin/python -B /world/client.py step --socket /world/s --action look","description":"MOCK retained-session world control","timeout":20000})}}]};finish='tool_calls'
            else:delta,finish={"content":"MOCK session plumbing complete; no policy result."},'stop'
            chunk={"id":"owned_context_fake","object":"chat.completion.chunk","model":payload['model'],"choices":[{"index":0,"delta":delta,"finish_reason":finish}],"usage":{"prompt_tokens":0,"completion_tokens":0,"total_tokens":0}}
            body=('data: '+json.dumps(chunk)+'\n\ndata: [DONE]\n\n').encode();self.send_response(200);self.send_header('Content-Type','text/event-stream');self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
        def log_message(self,*_):pass
    with http.server.ThreadingHTTPServer(('127.0.0.1',0),Fake) as fake:
        if fake.server_port in {18104,8006,8004}:raise ValueError('fake collided with a model port')
        worker=threading.Thread(target=fake.serve_forever,daemon=True);worker.start()
        try:receipt=run(root,sha(Path(root)/'manifest.json'),fake_endpoint=fake.server_address)
        finally:fake.shutdown();worker.join(timeout=3)
    if receipt['fake_posts']!=2 or receipt['actor_world_actions']!=1 or not receipt['actual_session_retention'] or not receipt['actual_session_retention']['verified']:
        raise ValueError('owned retained-session control failed')
    recovery().actor().write_new(Path(root)/'mock_control_verified.json',{'fake_posts':len(posts),'real_model_calls':0,'original_tool_feedback_retained':receipt['actual_session_retention']['original_tool_feedback_count'],'native_false':all(p.get('chat_template_kwargs')=={'enable_thinking':False} for p in posts)})
    return receipt


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__);group=parser.add_mutually_exclusive_group();group.add_argument('--preflight-only',action='store_true');group.add_argument('--mock-control',action='store_true');group.add_argument('--execute',action='store_true')
    parser.add_argument('--run-root',type=Path,required=True);parser.add_argument('--mode',choices=MODES);parser.add_argument('--manifest-sha');args=parser.parse_args(argv)
    if args.execute:
        if not args.manifest_sha:parser.error('--execute requires frozen --manifest-sha')
        if args.mode is not None and args.mode!=json.loads((args.run_root/'manifest.json').read_text())['mode']:parser.error('execute mode differs from frozen manifest')
        result=run(args.run_root,args.manifest_sha)
    else:result=(mock_control if args.mock_control else prepare)(args.run_root,args.mode or 'neutral')
    print(json.dumps({'run_root':str(args.run_root),'result':result}))


if __name__=='__main__':main()
