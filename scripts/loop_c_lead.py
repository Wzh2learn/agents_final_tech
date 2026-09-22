#!/usr/bin/env python3
"""Dependency-free Loop C Lead control plane; QUEUE.yaml is JSON-compatible YAML."""
from __future__ import annotations
import argparse, json, os, sys, tempfile
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
try:
    import fcntl
except ImportError:
    fcntl = None
ROOT = Path(os.environ.get("JINRONG_LOOP_C_HOME", "~/.jinrong-loop-c")).expanduser()
QUEUE, ACTIVE, CHECKPOINT, STOP, LOCK = (ROOT / n for n in ("QUEUE.yaml","ACTIVE.json","CHECKPOINT.md","STOP",".control.lock"))
DEFAULT_WORKTREE = Path.home() / "wzh/projects/agents_final_tech_loop_c"
def now(): return datetime.now(timezone.utc).replace(microsecond=0).isoformat()
def atomic_write(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=f".{path.name}.", dir=str(path.parent)); tmp = Path(name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as h:
            h.write(content); h.flush(); os.fsync(h.fileno())
        os.replace(tmp, path)
    finally:
        if tmp.exists(): tmp.unlink()
@contextmanager
def locked():
    ROOT.mkdir(parents=True, exist_ok=True)
    if fcntl is None: raise RuntimeError("fcntl is required on GB10")
    with LOCK.open("a+") as h:
        fcntl.flock(h.fileno(), fcntl.LOCK_EX)
        try: yield
        finally: fcntl.flock(h.fileno(), fcntl.LOCK_UN)
def load_queue():
    if not QUEUE.exists(): raise RuntimeError(f"missing {QUEUE}")
    try: data = json.loads(QUEUE.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as e: raise RuntimeError(f"QUEUE.yaml must be JSON-compatible YAML: {e}") from e
    if not isinstance(data, dict) or not isinstance(data.get("tasks"), list): raise RuntimeError("QUEUE.yaml requires tasks")
    ids, valid = set(), {"READY","ACTIVE","DONE","BLOCKED","FAILED"}
    for t in data["tasks"]:
        if not isinstance(t, dict) or not isinstance(t.get("id"), str): raise RuntimeError("task id missing")
        if t["id"] in ids: raise RuntimeError(f"duplicate task id {t['id']}")
        ids.add(t["id"])
        if t.get("status") not in valid: raise RuntimeError(f"invalid status {t['id']}")
        for key in ("owned_paths","forbidden_paths","depends_on","outputs","stop_conditions"):
            if not isinstance(t.get(key, []), list): raise RuntimeError(f"{key} must be list: {t['id']}")
    return data
def save_queue(data):
    data["updated_at"] = now(); atomic_write(QUEUE, json.dumps(data, ensure_ascii=False, indent=2) + "\n")
def active():
    if not ACTIVE.exists(): return {}
    try: data = json.loads(ACTIVE.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as e: raise RuntimeError(f"ACTIVE.json invalid: {e}") from e
    if not isinstance(data, dict): raise RuntimeError("ACTIVE.json must be object")
    return data
def select_ready(data):
    by_id = {t["id"]: t for t in data["tasks"]}
    for t in data["tasks"]:
        if t.get("status") == "READY" and all(by_id.get(d, {}).get("status") == "DONE" for d in t.get("depends_on", [])): return t
    raise RuntimeError("no dependency-satisfied READY task")
def cmd_check():
    with locked():
        q, a = load_queue(), active()
        print(json.dumps({"control_root": str(ROOT), "queue_tasks": len(q["tasks"]), "active": a, "stop_exists": STOP.exists(), "checkpoint_exists": CHECKPOINT.exists()}, ensure_ascii=False, indent=2))
    return 0
def cmd_status():
    with locked():
        q, a = load_queue(), active(); counts = {}
        for t in q["tasks"]: counts[t["status"]] = counts.get(t["status"], 0) + 1
        print(json.dumps({"control_root": str(ROOT), "queue_counts": counts, "active": a, "stop_exists": STOP.exists(), "checkpoint": str(CHECKPOINT)}, ensure_ascii=False, indent=2))
    return 0
def cmd_start():
    with locked():
        if STOP.exists(): raise RuntimeError(f"STOP exists: {STOP}")
        a = active()
        if a.get("state") in {"RUNNING","AUDITING"}: raise RuntimeError(f"active task: {a.get('task_id')}")
        q = load_queue(); t = select_ready(q); t["status"] = "ACTIVE"
        payload = {"task_id": t["id"], "mode": t.get("mode"), "worktree": t.get("worktree", str(DEFAULT_WORKTREE)), "branch": t.get("branch", "gb10/loop-c-lead-20260923"), "owned_paths": t.get("owned_paths", []), "pid": os.getpid(), "session": os.environ.get("LOOP_C_SESSION_ID", "manual"), "started_at": now(), "state": "RUNNING"}
        atomic_write(ACTIVE, json.dumps(payload, ensure_ascii=False, indent=2) + "\n"); save_queue(q); print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0
def cmd_complete(task_id, result, report):
    if result not in {"PASS","SCOPED_PASS","DATA_NO_GO","BLOCKED","FAILED"}: raise RuntimeError("invalid result")
    with locked():
        a = active()
        if a.get("task_id") != task_id: raise RuntimeError("task id mismatch; refusing blind completion")
        q, found = load_queue(), False
        for t in q["tasks"]:
            if t["id"] == task_id:
                t.update({"status": "DONE" if result not in {"BLOCKED","FAILED"} else result, "last_result": result, "completed_at": now(), "report": report}); found = True; break
        if not found: raise RuntimeError("ACTIVE task absent from queue")
        cp = (f"# Loop C Lead checkpoint\n\n- updated_at: {now()}\n- task: {task_id}\n- result: {result}\n- report: {report}\n- worktree: {a.get('worktree')}\n- owned_paths: {json.dumps(a.get('owned_paths', []), ensure_ascii=False)}\n- next action: reload GOAL/QUEUE/CHECKPOINT; do not rerun an ACTIVE or terminal task.\n")
        save_queue(q); atomic_write(CHECKPOINT, cp); atomic_write(ACTIVE, "{}\n"); print(cp, end="")
    return 0
def cmd_pause(reason):
    with locked(): atomic_write(STOP, f"requested_at: {now()}\nreason: {reason}\n"); print(f"STOP created: {STOP}")
    return 0
def cmd_resume():
    with locked():
        if STOP.exists(): STOP.unlink()
        print(f"STOP removed: {STOP}")
    return 0
def main():
    p = argparse.ArgumentParser(); s = p.add_subparsers(dest="cmd", required=True)
    for n in ("check","status","start","resume"): s.add_parser(n)
    c = s.add_parser("complete"); c.add_argument("task_id"); c.add_argument("result"); c.add_argument("--report", required=True)
    for n in ("pause","stop"):
        x = s.add_parser(n); x.add_argument("reason", nargs="?", default="explicit stop")
    a = p.parse_args()
    if a.cmd == "check": return cmd_check()
    if a.cmd == "status": return cmd_status()
    if a.cmd == "start": return cmd_start()
    if a.cmd == "complete": return cmd_complete(a.task_id, a.result, a.report)
    if a.cmd in {"pause","stop"}: return cmd_pause(a.reason)
    if a.cmd == "resume": return cmd_resume()
    return 2
if __name__ == "__main__":
    try: raise SystemExit(main())
    except (RuntimeError, OSError) as e:
        print(f"loop-c-lead: ERROR: {e}", file=sys.stderr); raise SystemExit(2)
