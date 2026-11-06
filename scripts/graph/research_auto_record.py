"""Record ContextBench episode evidence without launching an agent itself.

Decorate a runner's run(task, condition) using recorded_episode(root, seed).
Per-episode reservation is local to that root; abandoned reservations require
inspection, never an automatic rerun. recover_episode writes missing sidecars
from existing artifacts only. Cost and scientific outcomes are not inferred.
"""
from __future__ import annotations

from functools import wraps
import hashlib
import json
import math
import os
from pathlib import Path
import re
import sys
import tempfile
import time
from scripts.graph.research_evidence_graph import validate, _unique_object


_ID = re.compile(r"^[A-Za-z0-9_-]+__[-A-Za-z0-9_]+__seed[0-9]+$")


class RecordingPendingError(RuntimeError):
    """The episode may have run; inspect its reservation and recover, never rerun."""

    def __init__(self, episode_id: str):
        self.episode_id = episode_id
        super().__init__(f"Recording pending for {episode_id}; the episode may have executed. "
                         "Inspect its reservation and recover; do not rerun automatically.")


def _paths(root: Path, episode_id: str) -> dict:
    if not _ID.fullmatch(episode_id):
        raise ValueError("invalid episode identifier")
    return {"reservation": root / (episode_id + ".auto_reservation.json"),
            "terminal": root / (episode_id + ".auto_terminal.json"),
            "started": root / (episode_id + ".started.json"),
            "completed": root / (episode_id + ".completed.json"),
            "harness": root / (episode_id + ".harness.py"),
            "stdout": root / (episode_id + ".runner.stdout"),
            "stderr": root / (episode_id + ".runner.stderr"),
            "case": root / episode_id,
            "sidecar": root / (episode_id + ".auto_record.json"),
            "graph": root / (episode_id + ".evidence_graph.json"),
            "check": root / (episode_id + ".evidence_check.json")}


def _write_new(path: Path, obj: dict) -> None:
    # Publish a complete, fsynced file without ever replacing an existing file.
    fd, temp = tempfile.mkstemp(prefix="." + path.name + ".", suffix=".partial", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            json.dump(obj, f, ensure_ascii=False, indent=2, allow_nan=False)
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())
        os.link(temp, path)
    finally:
        os.unlink(temp)


def _hash(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(1024 * 1024), b""):
            h.update(b)
    return h.hexdigest()


def _guard_paths(root: Path, paths: dict) -> None:
    """Reject symlinks and any nested artifact resolving beyond the root."""
    candidates = list(paths.values()) + [paths["case"] / "raw.jsonl", paths["case"] / "receipt.json"]
    for p in candidates:
        try:
            if p.is_symlink() or any(parent.is_symlink() for parent in p.parents if parent != root and root in parent.parents):
                raise ValueError("symlink artifact rejected: " + p.name)
            p.resolve().relative_to(root)
        except (RuntimeError, OSError, ValueError) as exc:
            raise ValueError("unsafe episode artifact: " + p.name) from exc


def _number(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return value if value >= 0 and (isinstance(value, int) or math.isfinite(value)) else None


def _strict_json(path):
    def invalid_constant(value):
        raise ValueError('nonfinite JSON constant: ' + value)
    value = json.loads(path.read_text(encoding='utf-8'), object_pairs_hook=_unique_object,
                       parse_constant=invalid_constant)
    if not isinstance(value, dict):
        raise ValueError('expected JSON object')
    return value


def _raw_step_tokens(path):
    def invalid_constant(value):
        raise ValueError('nonfinite JSON constant: ' + value)
    tokens = []
    with path.open(encoding='utf-8') as stream:
        for line in stream:
            event = json.loads(line, object_pairs_hook=_unique_object, parse_constant=invalid_constant)
            if not isinstance(event, dict):
                raise ValueError('raw event is not an object')
            if event.get('type') == 'step_finish':
                part = event.get('part')
                if not isinstance(part, dict) or not isinstance(part.get('tokens'), dict):
                    raise ValueError('raw step tokens missing')
                tokens.append(part['tokens'])
    return tokens


def _costs(paths, elapsed_seconds):
    errors = []
    costs = {k: None for k in ('posts', 'reported_tokens', 'cache_read_included',
                                'input_tokens', 'output_tokens', 'reasoning_tokens')}
    costs['elapsed_seconds'] = _number(elapsed_seconds)
    receipt = {}
    if paths['completed'].is_file():
        try:
            receipt = _strict_json(paths['completed'])
        except (ValueError, OSError, UnicodeError) as exc:
            errors.append('completed receipt invalid: ' + type(exc).__name__)
    for key in ('posts', 'reported_tokens', 'cache_read_included'):
        value = receipt.get(key)
        if value is not None:
            if type(value) is int and value >= 0:
                costs[key] = value
            else:
                errors.append(key + ' must be a nonnegative integer')
    if (costs['reported_tokens'] is not None and costs['cache_read_included'] is not None
            and costs['cache_read_included'] > costs['reported_tokens']):
        errors.append('cache_read_included exceeds reported_tokens')
        costs['reported_tokens'] = costs['cache_read_included'] = None

    source = 'UNKNOWN_NO_BOUND_STEP_RECEIPT'
    posts_source = 'UNKNOWN_NO_REQUEST_LIST'
    detailed = paths['case'] / 'receipt.json'
    raw = paths['case'] / 'raw.jsonl'
    if detailed.is_file() and raw.is_file() and receipt:
        try:
            detail = _strict_json(detailed)
            raw_hash = _hash(raw)
            if receipt.get('raw_sha256') != raw_hash or detail.get('raw_sha256') != raw_hash:
                raise ValueError('raw hash binding mismatch')
            requests = detail.get('model_http_requests')
            if requests is not None:
                if not isinstance(requests, list) or any(not isinstance(v, str) for v in requests):
                    errors.append('model_http_requests is not a string list')
                    costs['posts'] = None
                elif costs['posts'] is not None:
                    if sum(v.startswith('POST ') for v in requests) != costs['posts']:
                        errors.append('posts differs from case request list')
                        costs['posts'] = None
                    else:
                        posts_source = 'MATCHED_CASE_REQUEST_LIST_NOT_PROXY'
            steps = detail.get('step_finish_tokens')
            if not isinstance(steps, list) or not steps or any(not isinstance(s, dict) for s in steps):
                raise ValueError('step token events missing')
            raw_steps = _raw_step_tokens(raw)
            if json.dumps(raw_steps, sort_keys=True) != json.dumps(steps, sort_keys=True):
                raise ValueError('step token events differ from raw')
            if costs['posts'] is not None and len(raw_steps)>costs['posts']:
                errors.append('more completed model steps than counted posts; request accounting is incomplete')
                costs['posts']=None
                posts_source='INCOMPLETE_REQUEST_ACCOUNTING'
            totals = [s.get('total') for s in steps]
            caches = [s.get('cache', {}).get('read') if isinstance(s.get('cache'), dict) else None for s in steps]
            if (any(type(v) is not int or v < 0 for v in totals + caches)
                    or costs['reported_tokens'] is None or costs['cache_read_included'] is None
                    or sum(totals) != costs['reported_tokens'] or sum(caches) != costs['cache_read_included']):
                raise ValueError('step totals or cache mismatch')
            for field, target in [('input', 'input_tokens'), ('output', 'output_tokens'),
                                  ('reasoning', 'reasoning_tokens')]:
                values = [s.get(field) for s in steps]
                if all(type(v) is int and v >= 0 for v in values):
                    costs[target] = sum(values)
            source = 'BOUND_RAW_AND_STEP_RECEIPT'
        except (ValueError, OSError, UnicodeError) as exc:
            errors.append('step receipt invalid or unbound: ' + str(exc))
            costs['reported_tokens'] = costs['cache_read_included'] = None
    has_cost = any(costs[k] is not None for k in ('posts', 'reported_tokens', 'cache_read_included'))
    state = ('INVALID' if errors else 'UNKNOWN' if not has_cost else
             'FORMAT_VALID_BOUND' if source == 'BOUND_RAW_AND_STEP_RECEIPT'
             and (costs['posts'] is None or posts_source == 'MATCHED_CASE_REQUEST_LIST_NOT_PROXY')
             else 'FORMAT_VALID_UNBOUND')
    return receipt, costs, state, errors, source, posts_source


def recover_episode(root: Path, episode_id: str, elapsed_seconds=None, *, abandoned=False) -> dict:
    """Create missing sidecars only; abandoned requires an operator to verify it is not live."""
    root = Path(root).resolve(strict=True)
    paths = _paths(root, episode_id)
    _guard_paths(root, paths)
    if not paths["reservation"].is_file():
        raise ValueError("episode reservation missing")
    if not paths["terminal"].is_file() and not abandoned:
        raise ValueError("episode may still be running; no terminal marker")
    if elapsed_seconds is None and paths["terminal"].is_file():
        try:
            terminal = _strict_json(paths["terminal"])
            if terminal.get("episode_id") == episode_id:
                elapsed_seconds = _number(terminal.get("elapsed_seconds"))
        except (ValueError, OSError, UnicodeError):
            pass  # Legacy or malformed terminal: duration remains unknown.
    if not paths["sidecar"].exists():
        receipt, costs, contract, cost_errors, token_source, posts_source = _costs(paths, elapsed_seconds)
        artifacts = []
        for p in (paths["reservation"], paths["terminal"], paths["started"], paths["completed"],
                  paths["harness"], paths["stdout"], paths["stderr"],
                  paths["case"] / "raw.jsonl", paths["case"] / "receipt.json"):
            if p.is_file() and p.resolve().is_relative_to(root):
                artifacts.append({"path": p.relative_to(root).as_posix(), "sha256": _hash(p)})
        sidecar = {"version": 1, "episode_id": episode_id,
                   "receipt_status": receipt.get("status", "UNKNOWN"),
                   "scientific_outcome": "UNKNOWN_NOT_INFERRED",
                   "costs": costs, "cost_contract": contract, "cost_errors": cost_errors,
                   "token_breakdown_source": token_source, "posts_source": posts_source,
                   "usage_completeness": "UNKNOWN_NOT_INFERRED_FROM_RECEIPT",
                   "cost_scope": "reported tokens already include cache; missing usage is unknown",
                   "artifacts": artifacts,
                   "boundary": "local episode evidence; no cross-host lock, budget enforcement, or semantic verdict"}
        _write_new(paths["sidecar"], sidecar)
    if not paths["graph"].exists():
        # Bind both the sidecar and each captured raw artifact in the graph.
        side_id = episode_id + "-sidecar"
        side = json.loads(paths["sidecar"].read_text(encoding="utf-8"))
        artifacts = side["artifacts"]
        refs = [{"id": side_id, "path": paths["sidecar"].relative_to(root).as_posix(),
                 "sha256": _hash(paths["sidecar"])}]
        refs.extend({"id": episode_id + "-artifact-" + str(i), "path": a["path"],
                     "sha256": a["sha256"]} for i, a in enumerate(artifacts))
        graph = {"version": 1,
                 "candidates": [{"id": episode_id, "parent": None,
                     "hypothesis": "not supplied by runner", "baseline": "not inferred",
                     "source": "ContextBench runner episode", "conclusion": "unknown pending scientific evaluation"}],
                 "evidence": refs,
                 "trials": [{"id": episode_id + "-trial", "candidate": episode_id,
                    "phase": "runner", "outcome": "see sidecar and original artifacts", "status": "unknown",
                    "evidence": [e["id"] for e in refs], "cost": None, "cost_unit": "multi-dimensional; see sidecar"}],
                 "reviews": []}
        _write_new(paths["graph"], graph)
    if not paths["check"].exists():
        graph = json.loads(paths["graph"].read_text(encoding="utf-8"))
        check = validate(root, graph)
        check["graph_sha256"] = _hash(paths["graph"])
        _write_new(paths["check"], check)
        if not check["valid"]:
            raise ValueError("evidence graph check failed; see immutable evidence_check")
    else:
        check = json.loads(paths["check"].read_text(encoding="utf-8"))
        current = validate(root, json.loads(paths["graph"].read_text(encoding="utf-8")))
        if not check.get("valid") or check.get("graph_sha256") != _hash(paths["graph"]) or not current["valid"]:
            raise ValueError("existing evidence check invalid or stale")
    return {"sidecar": str(paths["sidecar"]), "graph": str(paths["graph"]), "check": str(paths["check"])}


def recorded_episode(root: Path, seed: int):
    """Reserve and capture each run(task, condition); does not change prompts."""
    def decorate(func):
        @wraps(func)
        def wrapped(task, condition="none"):
            Path(root).mkdir(parents=True, exist_ok=True)
            base = Path(root).resolve(strict=True)
            episode_id = f"{task}__{condition}__seed{seed}"
            p = _paths(base, episode_id)
            _guard_paths(base, p)
            if any(p[k].exists() for k in ("started", "completed", "case", "harness", "stdout", "stderr", "terminal", "sidecar", "graph", "check")):
                raise FileExistsError("episode already attempted or recorded")
            _write_new(p["reservation"], {"version": 1, "episode_id": episode_id})
            start = time.monotonic()
            execution_returned = False
            try:
                result = func(task, condition)
                execution_returned = True
                return result
            finally:
                elapsed_seconds = time.monotonic() - start
                try:
                    _write_new(p["terminal"], {"version": 1, "episode_id": episode_id,
                               "execution_returned": execution_returned,
                               "elapsed_seconds": elapsed_seconds})
                    recover_episode(base, episode_id, elapsed_seconds)
                except Exception as exc:
                    # Reservation remains; a successful episode must not look fully recorded.
                    print(f"research-auto-record: sidecar pending: {exc}", file=sys.stderr)
                    if execution_returned:
                        raise RecordingPendingError(episode_id) from exc
        return wrapped
    return decorate
