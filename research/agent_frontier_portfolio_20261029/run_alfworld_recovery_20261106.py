"""Fresh-session continuation from one hash-frozen public ALF failure prefix.

Preflight replays only world steps. Execute is D-only, SHA-bound and exclusive.
This development correction source and its layout must be excluded from future
confirmation. No original OpenCode conversation or expert state is restored.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import http.server
import importlib.metadata
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import struct
import subprocess
import threading
import time

REPO = Path(__file__).resolve().parents[2]
QUAL = Path("/home/testuser/wzh/research_evidence/agent_learning_20261030/alfworld_text_qualification_20261106")
ACTOR_PATH = Path(__file__).with_name("run_alfworld_actor_20261106.py")
ACTOR_SHA = "a192e6d2e3c7f8c4fbccc20d9528ad08dddf94bf2701b5e077f2d32d438d157c"
SOURCE_REGISTRY = {
    "clean2_history_v2": {"relative_root": "experience_transfer_pilot_v1/target_attempts/clean_2/student8b/ordinary_public_history/attempt_v2", "game_id": "clean_2", "pins": {
        "manifest.json": "c3e42e4fb5bff4f4163c07168df8782e47ed5d08fe44ac4a7b4d944ba762ae2f",
        "receipt.json": "33a0dc0f78263b60ee4f41663d161646382abf08a48f5e1856708fd98c5776b7",
        "execute_world.jsonl": "ed8d8c7fedd3be258a0386ea308f565aedffa6ea97c80207a5e517717934b734"}},
    "heat2_history_v1": {"relative_root": "experience_transfer_pilot_v1/target_attempts/heat_2/student8b/ordinary_public_history/attempt_v1", "game_id": "heat_2", "pins": {
        "manifest.json": "b5d2423227a835a29a5e98c7e98367e14b91e1307ab922f6c7c460d5b2379c99",
        "receipt.json": "dd93a8586a719f160cad32925f95c40f3a18206cf022411532ba921cc900044d",
        "execute_world.jsonl": "701cf4c590b066bae60ed58828d6c66d3454459cbbe78f43cc353eed59f63230"}},
}
PUBLIC_KEYS = ("observation", "score", "done", "won", "action_count", "admissible_commands")
PROJECTION = "accepted step events only; retain action and full observation/score/done/won/count; omit intermediate commands; full original reset observation and full current public state"
BACKENDS = ("student8b", "teacher27b")
PROMPT_MODES = ("neutral", "terminal_guard")
TERMINAL_GUARD = "Judge completion by the actual environment response, not the previous attempt's final text; the restored state is not done. Continue until the real goal succeeds or the budget ends."
BRANCH_RULE = {"first": "student8b/neutral", "second": "teacher27b/neutral",
               "student8b/terminal_guard": "D runs only if completed student8b neutral is not won; no automatic branch"}
_ACTOR = None
_BRIDGE = None


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def encoded(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def actor():
    global _ACTOR
    if sha(ACTOR_PATH) != ACTOR_SHA or ACTOR_PATH.is_symlink():
        raise ValueError("frozen CBC actor changed")
    if _ACTOR is None:
        _ACTOR = load_module(ACTOR_PATH, "alf_recovery_cbc")
    return _ACTOR


def bridge():
    global _BRIDGE
    core = actor()
    if sha(core.BRIDGE) != core.BRIDGE_SHA:
        raise ValueError("frozen bridge changed")
    if _BRIDGE is None:
        _BRIDGE = load_module(core.BRIDGE, "alf_recovery_bridge")
    return _BRIDGE


def public_state(state):
    result = {key: state[key] for key in PUBLIC_KEYS}
    bridge().validate_response(result)
    return result


def remaining_caps(manifest, receipt):
    caps = actor().episode_caps(manifest["caps"])
    elapsed = receipt["elapsed_seconds"]
    if type(elapsed) not in (int, float) or not math.isfinite(elapsed) or elapsed < 0:
        raise ValueError("invalid source wall cost")
    used = {"posts": receipt["model_posts"], "world_actions": receipt["world_actions"],
            "model_payload_bytes_combined": receipt["model_request_payload_bytes"] + receipt["model_response_wire_bytes"]}
    if any(type(value) is not int or value < 0 for value in used.values()):
        raise ValueError("invalid source physical costs")
    result = {key: caps[key] - used[key] for key in used}
    result["seconds"] = math.floor(caps["seconds"] - elapsed)
    return actor().episode_caps(result)


def source(source_id="clean2_history_v2"):
    if source_id not in SOURCE_REGISTRY:
        raise ValueError("unapproved failure source")
    approved = SOURCE_REGISTRY[source_id]
    source_root, pins = QUAL / approved["relative_root"], approved["pins"]
    for name, digest in pins.items():
        path = source_root / name
        if path.is_symlink() or sha(path) != digest:
            raise ValueError("frozen failure source changed")
    manifest = json.loads((source_root / "manifest.json").read_text())
    receipt = json.loads((source_root / "receipt.json").read_text())
    events = [json.loads(line) for line in (source_root / "execute_world.jsonl").read_text().splitlines()]
    resets = [public_state(row["state"]) for row in events if row.get("event") == "reset"]
    steps = [{"action": bridge().validate_request({"action": row["action"]}),
              "state": public_state(row["state"])} for row in events if row.get("event") == "step"]
    if (manifest["game_id"] != approved["game_id"] or manifest["seed"] != 17 or
            manifest["backend"] != "student8b" or manifest.get("student_enable_thinking") is not False or
            receipt["manifest_sha256"] != pins["manifest.json"] or receipt["status"] != "RETURNED" or
            receipt["won"] is not False or len(resets) != 1 or not steps or resets[0]["action_count"] != 0 or
            [row["state"]["action_count"] for row in steps] != list(range(1, len(steps) + 1)) or
            any(row["state"]["done"] or row["state"]["won"] for row in steps) or
            receipt["world_actions"] != len(steps) or public_state(receipt["final_world_state"]) != steps[-1]["state"]):
        raise ValueError("source is not the designated complete nonterminal failure prefix")
    game, pool = actor().select_game(manifest["game_id"], manifest["pool_binding"]["path"], manifest["pool_binding"]["sha256"])
    if pool != manifest["pool_binding"] or game["sha256_game"] != manifest["game_sha256"]:
        raise ValueError("source world binding changed")
    first_request = source_root / "requests/00001.json"
    binding = {"root": str(source_root), "sha256": dict(pins), "first_request_sha256": sha(first_request),
               "game_id": manifest["game_id"], "game_sha256": game["sha256_game"], "seed": manifest["seed"],
               "pool_binding": pool, "prefix_actions": len(steps), "remaining_caps": remaining_caps(manifest, receipt),
               "projection": PROJECTION, "public_prefix_sha256": hashlib.sha256(encoded([resets[0], steps])).hexdigest()}
    layout = next(row["layout"] for row in json.loads(Path(pool["path"]).read_text())["games"] if row["id"] == manifest["game_id"])
    binding["layout"] = layout
    return {"source_id": source_id, "root": source_root, "manifest": manifest, "receipt": receipt, "binding": binding, "reset": resets[0], "steps": steps}


def check_root(root, backend, source_id="clean2_history_v2"):
    if source_id not in SOURCE_REGISTRY:
        raise ValueError("unapproved failure source")
    if backend not in BACKENDS:
        raise ValueError("unsupported recovery backend")
    root = Path(root)
    expected = QUAL / "failure_recovery_v1" / source_id / backend
    if root.parent.resolve() != expected.resolve() or not re.fullmatch(r"attempt_v[1-9][0-9]*", root.name):
        raise ValueError("recovery requires canonical failure_recovery_v1/source_id/backend/attempt_vN")
    current = QUAL
    for part in expected.relative_to(QUAL).parts:
        current = current / part
        if current.is_symlink():
            raise ValueError("recovery namespace symlink")


def recovery_prompt(data, current, prompt_mode="neutral"):
    if prompt_mode not in PROMPT_MODES:
        raise ValueError("unsupported recovery prompt mode")
    history = [{"action": row["action"], **{key: row["state"][key] for key in PUBLIC_KEYS[:-1]}}
               for row in data["steps"]]
    result = (
        "Continue this unfinished household task in a fresh session. The environment has actually replayed "
        "the public actions below and verified the same state. This does not restore an earlier conversation.\n"
        "Original public goal/reset observation:\n" + data["reset"]["observation"] +
        "\nPrior accepted actions and complete returned observations (historical):\n" + json.dumps(history, ensure_ascii=False) +
        "\nCurrent real public handoff state:\n" + json.dumps(current, ensure_ascii=False) +
        "\nUse only Bash, one environment action per tool call:\n"
        "/runtime/bin/python -B /world/client.py step --socket /world/s --action '<one exact action>'\n"
        "Use current admissible_commands. Read every returned observation. Every accepted action, including look, "
        "consumes a real step. The reset snapshot file and prior observations are cached history after actions. "
        "Continue autonomously without asking permission. Stop when done is true. Claim success only after an "
        "actual response has won=true. There is no reset, game selection or administrative operation.\n")
    return result + ("\n" + TERMINAL_GUARD + "\n" if prompt_mode == "terminal_guard" else "")


def replay(data, initial, step, log_path):
    start = time.monotonic()
    with Path(log_path).open("x", encoding="utf8") as log:
        current = public_state(initial)
        log.write(json.dumps({"event": "reset_comparison", "equal": current == data["reset"], "actual": current}) + "\n")
        log.flush()
        if current != data["reset"]:
            raise ValueError("native reset differs from frozen source")
        for row in data["steps"]:
            current = public_state(step(row["action"]))
            equal = current == row["state"]
            log.write(json.dumps({"event": "replay_step", "action": row["action"], "equal": equal, "actual": current}) + "\n")
            log.flush()
            if not equal:
                raise ValueError("native replay state differs from frozen source")
    if current["done"] or current["won"]:
        raise ValueError("handoff must remain nonterminal and not won")
    return current, {"control_world_actions": len(data["steps"]), "wall_seconds": time.monotonic() - start,
                     "all_public_states_equal": True, "public_prefix_sha256": data["binding"]["public_prefix_sha256"]}


def gguf_metadata(path):
    """Read metadata only; never tensor payload or model weights."""
    with Path(path).open("rb") as stream:
        if stream.read(4) != b"GGUF":
            raise ValueError("expected local GGUF")
        version, _, count = struct.unpack("<IQQ", stream.read(20))
        if version != 3:
            raise ValueError("unsupported GGUF metadata")
        def value(kind):
            formats = {0: "B", 1: "b", 2: "H", 3: "h", 4: "I", 5: "i", 6: "f", 7: "?", 10: "Q", 11: "q", 12: "d"}
            if kind in formats:
                fmt = formats[kind]
                return struct.unpack("<" + fmt, stream.read(struct.calcsize(fmt)))[0]
            if kind == 8:
                length, = struct.unpack("<Q", stream.read(8))
                return stream.read(length).decode("utf8")
            if kind == 9:
                subtype, length = struct.unpack("<IQ", stream.read(12))
                return [value(subtype) for _ in range(length)]
            raise ValueError("unsupported GGUF value type")
        selected = {}
        for _ in range(count):
            key = value(8)
            kind, = struct.unpack("<I", stream.read(4))
            item = value(kind)
            if key in {"tokenizer.ggml.tokens", "tokenizer.ggml.merges", "tokenizer.ggml.pre", "tokenizer.chat_template"}:
                selected[key] = item
        return selected


def template_messages(payload, backend):
    messages = copy.deepcopy(payload["messages"])
    # Actual frozen vLLM chat_utils.py _postprocess_messages, lines 1911-1951:
    # SHA150f40b0a0ba87548b0feb86f002fea7d246f5a4d5f7bc2cecd3c3824098c851.
    # This projection is only for local template qualification, never forwarded.
    if backend == "teacher27b":
        for message in messages:
            if message.get("role") != "assistant" or not isinstance(message.get("tool_calls"), list):
                continue
            if not message["tool_calls"]:
                message.pop("tool_calls")
                continue
            for call in message["tool_calls"]:
                function = call["function"]
                value = function.get("arguments")
                if not value:
                    function["arguments"] = {}
                elif not isinstance(value, (dict, list)):
                    parsed = json.loads(value)
                    function["arguments"] = parsed if parsed is not None else {}
    return messages


def input_ids(value):
    # Transformers 5 may return a BatchEncoding with two keys, not a token list.
    if hasattr(value, "keys"):
        value = value["input_ids"]
    if isinstance(value, list) and value and isinstance(value[0], list):
        if len(value) != 1:
            raise ValueError("unexpected batched chat qualification")
        value = value[0]
    if not isinstance(value, list) or any(type(token) is not int for token in value):
        raise ValueError("unexpected template token representation")
    return value


def token_qualifier(backend, profile):
    """Local tokenizer + actual serving template, no weights/API/inference."""
    from transformers import AutoTokenizer
    model_dir = Path("/home/testuser/wzh/models/hf") / ("Qwen3-8B" if backend == "student8b" else "Qwen3.8-27B-FP8")
    files = {name: sha(model_dir / name) for name in ("tokenizer.json", "tokenizer_config.json")}
    if backend == "student8b":
        metadata = gguf_metadata(profile["gguf_path"])
        template = metadata["tokenizer.chat_template"]
        raw = json.loads((model_dir / "tokenizer.json").read_text())
        vocab = {**raw["model"]["vocab"], **{row["content"]: row["id"] for row in raw["added_tokens"]}}
        native = metadata["tokenizer.ggml.tokens"]
        if any(index >= len(native) or native[index] != text for text, index in vocab.items()):
            raise ValueError("HF/native GGUF token IDs differ")
        merges = [" ".join(row) if isinstance(row, list) else row for row in raw["model"]["merges"]]
        if merges != metadata["tokenizer.ggml.merges"]:
            raise ValueError("HF/native GGUF BPE merges differ")
        native_binding = {"template_origin": "actual_GGUF_metadata",
                          "native_pre_tokenizer": metadata["tokenizer.ggml.pre"], "BPE_merges_all_equal": True, "matched_vocab_entries": len(vocab),
                          "native_vocab_entries": len(native), "vocab_mapping_all_equal": True}
    else:
        template = Path(profile["template_path"]).read_bytes().decode("utf8")
        if hashlib.sha256(template.encode()).hexdigest() != profile["template_sha256"]:
            raise ValueError("teacher serving template changed")
        native_binding = {"template_origin": "frozen_vLLM_serving_template",
                          "local_chat_utils_sha256": "150f40b0a0ba87548b0feb86f002fea7d246f5a4d5f7bc2cecd3c3824098c851",
                          "offline_tool_arguments_projection": "actual_vLLM_postprocess_messages"}
    tokenizer = AutoTokenizer.from_pretrained(model_dir, local_files_only=True, trust_remote_code=False, use_fast=True)
    binding = {"model_dir": str(model_dir), "files_sha256": files,
               "template_sha256": hashlib.sha256(template.encode()).hexdigest(), **native_binding,
               "transformers_version": importlib.metadata.version("transformers"),
               "tokenizers_version": importlib.metadata.version("tokenizers")}
    def qualify(payload):
        tokens = tokenizer.apply_chat_template(template_messages(payload, backend), tools=payload.get("tools") or None,
                    chat_template=template, tokenize=True, return_dict=False, add_generation_prompt=True, enable_thinking=False)
        count = len(input_ids(tokens))
        result = {"template_input_tokens": count, "reserved_output_tokens": profile["output"],
                  "context": profile["context"], "fits": count + profile["output"] <= profile["context"],
                  "request_payload_sha256": hashlib.sha256(json.dumps(payload, separators=(",", ":")).encode()).hexdigest()}
        return result
    return binding, qualify


def components():
    return {**actor().components(), str(Path(__file__).resolve()): sha(__file__)}


def prepare(root, backend, source_id="clean2_history_v2", prompt_mode="neutral"):
    if prompt_mode not in PROMPT_MODES or prompt_mode == "terminal_guard" and backend != "student8b":
        raise ValueError("terminal guard is an explicit student8b development baseline")
    root = Path(root).resolve()
    check_root(root, backend, source_id)
    root.mkdir(parents=True, exist_ok=True)
    if any(root.iterdir()):
        raise FileExistsError("fresh empty recovery root required")
    core, data = actor(), source(source_id)
    profile = core.load_profile(backend)
    native_false = False if backend == "student8b" else None
    sampling = core.model_payload({}, backend, profile, data["manifest"]["seed"], native_false)
    core.dependencies.verify_projection(core.RUNTIME_ROOT, core.RUNTIME_SHA)
    if sha(core.BINARY) != core.BINARY_SHA:
        raise ValueError("OpenCode binary changed")
    image = subprocess.check_output(["docker", "image", "inspect", core.IMAGE, "--format", "{{.Id}}"], text=True).strip()
    world = None
    try:
        m = data["manifest"]
        world, initial, _ = core.start_world(root, m["game_id"], m["seed"], "preflight", m["caps"],
                                           m["pool_binding"]["path"], m["pool_binding"]["sha256"])
        current, replay_cost = replay(data, initial, lambda action: bridge().client_step(world[1] / "s", action), root / "preflight_replay.jsonl")
    finally:
        if world:
            core.stop_world(world)
    prompt = recovery_prompt(data, current, prompt_mode)
    (root / "task.txt").write_bytes(prompt.encode())
    core.write_new(root / "handoff_public.json", current)
    core.write_new(root / "opencode_config.json", core.config(profile, m["seed"]))
    token_binding, qualify = token_qualifier(backend, profile)
    # Preflight estimate uses a REAL prior SDK system/tool envelope, not guessed tool definitions.
    envelope = json.loads((data["root"] / "requests/00001.json").read_text())["incoming"]
    users = [row for row in envelope["messages"] if row.get("role") == "user"]
    if len(users) != 1 or any(t.get("function", {}).get("name") != "bash" for t in envelope.get("tools", [])):
        raise ValueError("unexpected source SDK envelope")
    users[0]["content"] = '"' + prompt.replace('"', chr(92) + '"') + '"'
    projected = core.model_payload(envelope, backend, profile, m["seed"], native_false)
    qualification = qualify(projected)
    if not qualification["fits"]:
        raise ValueError("projected actual-template context budget exceeded")
    core.write_new(root / "preflight_template_tokens.json", {"method": "prior_real_SDK_envelope_new_user_projection_not_new_actual_request", **qualification})
    manifest = {"version": 1, "label": "DEVELOPMENT_FAILURE_RECOVERY_SOURCE", "backend": backend,
                "arm": "N_fresh_session_neutral_continuation" if backend == "student8b" else "T_fresh_session_teacher_takeover",
                "prompt_mode": prompt_mode, "planned_branch_rule": BRANCH_RULE,
                "failure_source_id": source_id, "source_binding": data["binding"],
                "source_physical_cost_charge_once_id": data["binding"]["sha256"]["receipt.json"],
                "exclude_from_future_confirmation": {"game_id": m["game_id"], "layout": data["binding"]["layout"]},
                "caps": data["binding"]["remaining_caps"], "total_world_step_cap": m["caps"]["world_actions"],
                "replay_control_cost": replay_cost, "sampling": sampling, "model_id": profile["model_id"],
                "profile_sha256": core.PROFILE_PINS[backend][1], "student_enable_thinking": native_false,
                "tokenizer_binding": token_binding, "preflight_template_qualification": qualification,
                "components": components(), "uid": os.getuid(), "gid": os.getgid(), "image_id": image,
                "prompt_sha256": sha(root / "task.txt"), "handoff_sha256": sha(root / "handoff_public.json"),
                "config_sha256": sha(root / "opencode_config.json"), "real_model_calls": 0}
    core.write_new(root / "manifest.json", manifest)
    return manifest


def verify(root, digest):
    root = Path(root).resolve()
    if sha(root / "manifest.json") != digest:
        raise ValueError("recovery manifest SHA mismatch")
    manifest = json.loads((root / "manifest.json").read_text())
    check_root(root, manifest["backend"], manifest["failure_source_id"])
    if (manifest["planned_branch_rule"] != BRANCH_RULE or manifest["prompt_mode"] not in PROMPT_MODES or
            manifest["prompt_mode"] == "terminal_guard" and manifest["backend"] != "student8b"):
        raise ValueError("recovery prompt mode/branch binding changed")
    core, data = actor(), source(manifest["failure_source_id"])
    if (manifest["components"] != components() or manifest["source_binding"] != data["binding"] or
            manifest["caps"] != data["binding"]["remaining_caps"] or
            (manifest["uid"], manifest["gid"]) != (os.getuid(), os.getgid())):
        raise ValueError("recovery components/source/caps/owner changed")
    for name, key in (("task.txt", "prompt_sha256"), ("handoff_public.json", "handoff_sha256"), ("opencode_config.json", "config_sha256")):
        if sha(root / name) != manifest[key]:
            raise ValueError("frozen recovery input changed")
    if (root / "task.txt").read_bytes() != recovery_prompt(data, data["steps"][-1]["state"], manifest["prompt_mode"]).encode():
        raise ValueError("public recovery projection changed")
    profile = core.load_profile(manifest["backend"])
    if (manifest["profile_sha256"] != core.PROFILE_PINS[manifest["backend"]][1] or
            manifest["model_id"] != profile["model_id"] or
            manifest["sampling"] != core.model_payload({}, manifest["backend"], profile, data["manifest"]["seed"], manifest["student_enable_thinking"])):
        raise ValueError("recovery backend/native sampling mismatch")
    binding, qualify = token_qualifier(manifest["backend"], profile)
    if binding != manifest["tokenizer_binding"]:
        raise ValueError("actual serving template/tokenizer changed")
    core.dependencies.verify_projection(core.RUNTIME_ROOT, core.RUNTIME_SHA)
    return manifest, data, profile, qualify


def run(root, digest, *, fake_endpoint=None):
    root = Path(root).resolve()
    manifest, data, profile, qualify = verify(root, digest)
    core = actor()
    core.write_new(root / "reservation.json", {"manifest_sha256": digest, "mode": "OWNED_FAKE_RECOVERY_CONTROL" if fake_endpoint else "REAL_RECOVERY_EPISODE"})
    world = relay = model_dir = None
    replay_cost = None
    errors, status, docker_exit = [], "FAILED", None
    started = time.monotonic()
    name = "alf-recovery-owned-" + str(os.getpid()) + "-" + str(time.monotonic_ns())
    class QualifiedRelay(core.ModelRelay):
        def forward(self, upstream, packet, payload=None, post_index=None):
            proof = qualify(payload)
            core.write_new(root / "actual_template_tokens" / (str(post_index).zfill(5) + ".json"), proof)
            if not proof["fits"]:
                raise ValueError("actual serving-template context budget exceeded")
            return super().forward(upstream, packet, payload, post_index)
    try:
        m = data["manifest"]
        world, initial, _ = core.start_world(root, m["game_id"], m["seed"], "execute", m["caps"],
                                           m["pool_binding"]["path"], m["pool_binding"]["sha256"])
        current, replay_cost = replay(data, initial, lambda action: bridge().client_step(world[1] / "s", action), root / "execute_replay.jsonl")
        if current != json.loads((root / "handoff_public.json").read_text()):
            raise ValueError("execution handoff differs from preflight")
        work = root / "workspace"
        work.mkdir()
        for original, copied in (("task.txt", "task.txt"), ("opencode_config.json", "opencode.json")):
            (work / copied).write_bytes((root / original).read_bytes())
        (work / "guest.py").write_text(core.GUEST)
        model_dir = core.socket_directory("m")
        relay = QualifiedRelay(root, model_dir, manifest["backend"], profile, m["seed"],
                    fake_endpoint or (profile["host"], profile["port"]), manifest["caps"], manifest["sampling"],
                    student_enable_thinking=manifest["student_enable_thinking"])
        argv = core.docker_command(work, world[1], model_dir, manifest, name)
        core.write_new(root / "docker_command.json", {"argv": argv})
        actor_started = time.monotonic()
        with (root / "raw.jsonl").open("xb") as out, (root / "docker.stderr").open("xb") as err:
            result = subprocess.run(argv, stdout=out, stderr=err, timeout=manifest["caps"]["seconds"])
        docker_exit, status = result.returncode, "RETURNED"
    except subprocess.TimeoutExpired:
        status = "EPISODE_TIMEOUT"
    except Exception as exc:
        errors.append({"type": type(exc).__name__, "error": str(exc)})
    finally:
        if relay:
            relay.begin_close()
        try:
            subprocess.run(["docker", "rm", "-f", name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=15)
        except Exception as exc:
            errors.append({"cleanup": "owned_container", "error": str(exc)})
        for label, cleanup in (("relay", relay.close if relay else (lambda: core.cleanup_directory(model_dir)) if model_dir else None),
                               ("world", (lambda: core.stop_world(world)) if world else None)):
            if cleanup:
                try:
                    cleanup()
                except Exception as exc:
                    errors.append({"cleanup": label, "error": str(exc)})
        if relay:
            core.write_new(root / "actual_tool_definitions.json", relay.tools)
            core.write_new(root / "relay_errors.json", relay.errors)
        events = [json.loads(line) for line in (root / "execute_world.jsonl").read_text().splitlines()] if (root / "execute_world.jsonl").exists() else []
        states = [row["state"] for row in events if row.get("event") in {"reset", "step"}]
        final = public_state(states[-1]) if states else None
        responses = [json.loads(p.read_text()) for p in sorted((root / "responses").glob("*.receipt.json"))]
        tokens, token_error = None, None
        try:
            tokens = core.records._raw_step_tokens(root / "raw.jsonl") if (root / "raw.jsonl").exists() else []
        except Exception as exc:
            token_error = str(exc)
        receipt = {"label": "OWNED_FAKE_RECOVERY_NOT_POLICY" if fake_endpoint else "DEVELOPMENT_FAILURE_RECOVERY_SOURCE",
            "status": status, "errors": errors, "model_relay_errors": relay.errors if relay else [], "manifest_sha256": digest, "source_binding": data["binding"],
            "source_formation_cost_reference_only_charge_once": data["binding"]["sha256"]["receipt.json"],
            "backend": manifest["backend"], "model_id": manifest["model_id"], "arm": manifest["arm"],
            "prompt_mode": manifest["prompt_mode"], "planned_branch_rule": manifest["planned_branch_rule"],
            "elapsed_seconds": time.monotonic() - started, "actor_wall_seconds": time.monotonic() - actor_started if 'actor_started' in locals() else None,
            "replay_control_cost": replay_cost, "caps": manifest["caps"], "sampling": manifest["sampling"],
            "docker_exit": docker_exit, "model_posts": relay.budget.posts if relay else 0,
            "forwarded_model_posts": relay.forwarded if relay else 0,
            "real_model_calls": 0 if fake_endpoint else relay.forwarded if relay else 0,
            "fake_posts": relay.forwarded if fake_endpoint and relay else 0,
            "model_request_payload_bytes": relay.budget.request_bytes if relay else 0,
            "model_response_wire_bytes": relay.budget.response_bytes if relay else 0,
            "response_receipts": responses, "raw_step_tokens_separate_not_added": tokens, "raw_token_parse_error": token_error,
            "unknown_usage_model_posts": max(0, (relay.forwarded if relay else 0) - sum(bool(r.get("complete") and r.get("usage")) for r in responses)),
            "final_world_state": final, "won": bool(final and final["won"]),
            "actor_world_actions": max(0, final["action_count"] - len(data["steps"])) if final else 0,
            "handoff_delivery": relay.delivery if relay else None,
            "qualified_real_correction": bool(not fake_endpoint and status == "RETURNED" and not errors and relay and not relay.errors and final and final["won"] and final["done"] and replay_cost),
            "fresh_session_not_original_conversation": True, "future_confirmation_exclusion": manifest["exclude_from_future_confirmation"]}
        core.write_new(root / "receipt.json", receipt)
    return receipt


def mock_control(root, backend, source_id="clean2_history_v2", prompt_mode="neutral"):
    prepare(root, backend, source_id, prompt_mode)
    posts = []
    class Fake(http.server.BaseHTTPRequestHandler):
        def do_POST(self):
            payload = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            posts.append(payload)
            if len(posts) == 1:
                delta = {"tool_calls": [{"index": 0, "id": "mock_recovery_look", "type": "function", "function": {
                    "name": "bash", "arguments": json.dumps({"command": "/runtime/bin/python -B /world/client.py step --socket /world/s --action look", "description": "MOCK recovered-state socket control", "timeout": 20000})}}]}
                finish = "tool_calls"
            else:
                delta, finish = {"content": "MOCK control complete; no correction qualification."}, "stop"
            chunk = {"id": "owned_recovery_fake", "object": "chat.completion.chunk", "model": payload["model"],
                     "choices": [{"index": 0, "delta": delta, "finish_reason": finish}],
                     "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}}
            body = ("data: " + json.dumps(chunk) + "\n\ndata: [DONE]\n\n").encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        def log_message(self, *_):
            pass
    with http.server.ThreadingHTTPServer(("127.0.0.1", 0), Fake) as fake:
        if fake.server_port in {18104, 8006, 8004}:
            raise ValueError("owned fake collided with model port")
        worker = threading.Thread(target=fake.serve_forever, daemon=True)
        worker.start()
        try:
            receipt = run(root, sha(Path(root) / "manifest.json"), fake_endpoint=fake.server_address)
        finally:
            fake.shutdown()
            worker.join(timeout=3)
    if receipt["fake_posts"] != 2 or receipt["actor_world_actions"] != 1 or receipt["qualified_real_correction"]:
        raise ValueError("MOCK recovery plumbing failed")
    actor().write_new(Path(root) / "mock_control_verified.json", {"fake_posts": len(posts), "real_model_calls": 0,
                          "all_native_false": all(p.get("chat_template_kwargs") == {"enable_thinking": False} for p in posts)})
    return receipt


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--preflight-only", action="store_true")
    mode.add_argument("--mock-control", action="store_true")
    mode.add_argument("--execute", action="store_true", help="D only; real endpoint requires frozen SHA and one fresh reservation")
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--backend", choices=BACKENDS)
    parser.add_argument("--failure-source", choices=SOURCE_REGISTRY)
    parser.add_argument("--prompt-mode", choices=PROMPT_MODES)
    parser.add_argument("--manifest-sha")
    args = parser.parse_args(argv)
    if args.execute:
        if not args.manifest_sha:
            parser.error("--execute requires --manifest-sha")
        frozen = json.loads((args.run_root / "manifest.json").read_text())
        for value, key in ((args.backend, "backend"), (args.failure_source, "failure_source_id"), (args.prompt_mode, "prompt_mode")):
            if value is not None and value != frozen[key]:
                parser.error("execute override differs from frozen recovery manifest")
        result = run(args.run_root, args.manifest_sha)
    else:
        result = (mock_control if args.mock_control else prepare)(args.run_root, args.backend or "student8b", args.failure_source or "clean2_history_v2", args.prompt_mode or "neutral")
    print(json.dumps({"run_root": str(args.run_root), "result": result}))


if __name__ == "__main__":
    main()
