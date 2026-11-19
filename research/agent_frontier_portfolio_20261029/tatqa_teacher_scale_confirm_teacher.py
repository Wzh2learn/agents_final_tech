"""Run the frozen K9 teacher pool and the scale readout on its saved programs."""
from __future__ import annotations

import argparse
import getpass
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import tatqa_action_routing as routing
import tatqa_scale_study as study
import tatqa_teacher_scale as replay
import tatqa_transfer as transfer


ROOT = transfer.BASE / "teacher_scale_confirmation_v1"
PANEL = ROOT / "dev32"
POOL = ROOT / "teacher_pool"
FREEZE = ROOT / "TEACHER_FREEZE.json"
CAP = 450_000
MAIN_K, POOL_K = 6, 9


def inputs():
    return (PANEL / "PLAN.json", PANEL / "LOCAL_RESULT.json", PANEL / "LABELS_PRIVATE.json",
            ROOT / "RISK_ORDER.json", ROOT / "LOCAL_SCALE_PREDICTIONS.json")


def prepare():
    plan, local, labels, order, _ = (study.read(p) for p in inputs())
    ranking = order["order"]
    if len(ranking) != 32 or any(type(i) is not int for i in ranking) or set(ranking) != set(range(32)):
        raise ValueError("risk ranking must be a permutation of the new panel")
    sources = routing.indexed(plan["episodes"])
    paired = routing.indexed(local["arms"]["paired"])
    firstpass = routing.indexed(local["arms"]["firstpass"])
    gold = routing.indexed(labels)
    if not plan.get("prospective_complete") or local["status"] != "RETURNED":
        raise ValueError("the full prospective local phase must return first")
    for i, source in sources.items():
        if any(source["id"] != r["id"] for r in (paired[i], firstpass[i], gold[i])):
            raise ValueError("local candidate identity mismatch")

    selected = ranking[:POOL_K]
    POOL.mkdir(mode=0o700)
    for i in selected:
        a = transfer.packet_at(PANEL, "firstpass", i)
        b = transfer.packet_at(POOL, "firstpass", i)
        for name in ("inputs", "work", "dependencies"):
            shutil.copytree(a / name, b / name)
    shutil.copyfile(PANEL / "LABELS_PRIVATE.json", POOL / "LABELS_PRIVATE.json")
    study.write_json(POOL / "PLAN.json", {**plan, "episodes": [sources[i] for i in selected]})
    study.write_json(POOL / "POLICIES.json", dict(orders=dict(risk=selected), budgets=[MAIN_K, POOL_K]))
    study.write_json(POOL / "RUN_RESULT.json", dict(status="RETURNED", phase="AWAITING_T0"))
    study.write_json(FREEZE, dict(
        K6=selected[:MAIN_K], K9=selected, token_cap=CAP, source="original first-pass snapshots",
        primary="K6 paired scale versus K9 raw; Risk order frozen before teacher outcomes",
        sha256={str(p.relative_to(ROOT)): replay.sha(p) for p in
                (*inputs(), POOL / "PLAN.json", POOL / "POLICIES.json", POOL / "LABELS_PRIVATE.json")},
    ))
    print("Frozen9 teacher episodes for nested K6 and K9.", flush=True)


def frozen():
    value = study.read(FREEZE)
    for path, digest in value["sha256"].items():
        if replay.sha(ROOT / path) != digest:
            raise ValueError("a frozen input changed after planning")
    if value["token_cap"] != CAP or value["K6"] != value["K9"][:MAIN_K] or len(value["K9"]) != POOL_K:
        raise ValueError("teacher budget or selection differs from the protocol")
    return value


def teacher():
    frozen()
    if any((POOL / name).exists() for name in ("TEACHER_ATTEMPT.json", "TEACHER_LIVE.json", "TEACHER_RESULT.json")):
        raise FileExistsError("a teacher attempt already exists")
    key = os.environ.get("BUPT_API_KEY") or getpass.getpass("Campus credential (hidden): ")
    if not key:
        raise ValueError("campus credential is missing")
    study.write_json(POOL / "TEACHER_ATTEMPT.json", dict(freeze_sha256=replay.sha(FREEZE)))
    transfer.ROOT = POOL
    transfer.teacher(key, token_cap=CAP)


def prefill():
    fixed = frozen()
    native = study.read(POOL / "TEACHER_RESULT.json")
    teachers = native["episodes"]
    if native["status"] != "RETURNED" or [r["index"] for r in teachers] != fixed["K9"]:
        raise ValueError("expected the complete frozen teacher attempts")
    if native["token_cap"] != CAP or native["known_tokens"] + native["unknown_reserve"] > CAP:
        raise ValueError("teacher ledger exceeded the preselected token limit")
    model = study.read(replay.ROOT / "FREEZE.json")
    for filename, digest in (("adapter_model.safetensors", model["adapter_sha256"]),
                             ("adapter_config.json", model["adapter_config_sha256"])):
        if replay.sha(replay.ADAPTER / filename) != digest:
            raise ValueError("teacher scale readout requires the original frozen Pair128 adapter")
    data = []
    for row in teachers:
        if not row["valid"] or not row["normal"] or row["submission"] is None:
            continue
        i = row["index"]
        public = study.read(transfer.packet_at(PANEL, "firstpass", i) / "inputs/public.json")
        if public["id"] != row["id"]:
            raise ValueError("teacher output and original public input disagree")
        data.append(study.example({**row, "public": public}, f"confirmation32:{i}", row["submission"]["scale"]))
    source = ROOT / "TEACHER_SCALE_INPUTS.jsonl"
    destination = ROOT / "TEACHER_SCALE_PREDICTIONS.json"
    study.write_rows(source, data)
    if not data:
        study.write_json(destination, dict(rows=[], counts=dict(
            forward_calls=0, input_tokens=0, generated_tokens=0, http_posts=0, input_rows=0, neural_rows=0,
        )))
        return
    unloaded = transfer.c.stop27()
    try:
        subprocess.run([sys.executable, "-u", "-B", "-m",
                        "research.agent_frontier_portfolio_20261029.tatqa_scale_training",
                        "predict", "--data", str(source), "--arm", f"{replay.ARM}={replay.ADAPTER}",
                        "--out", str(destination)], cwd=Path(__file__).resolve().parents[2], check=True)
    finally:
        if unloaded:
            restore = transfer.c.restore27()
            summary = {"pid": restore.get("pid"), "folder": restore.get("folder")}
            study.write_json(ROOT / "TEACHER_SCALE_RESTORATION.json", summary)
            print(json.dumps({"restoration": summary}), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("prepare", "teacher", "prefill"))
    args = parser.parse_args()
    {"prepare": prepare, "teacher": teacher, "prefill": prefill}[args.command]()
