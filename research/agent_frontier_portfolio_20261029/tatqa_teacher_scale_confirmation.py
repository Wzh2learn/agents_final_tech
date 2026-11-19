"""Freeze a new TAT-QA panel, collect local programs and rank teacher calls."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import tatqa_action_routing as routing
import tatqa_scale_acceptance as acceptance
import tatqa_scale_cohorts as cohorts
import tatqa_scale_study as study
import tatqa_teacher_scale as replay
import tatqa_transfer as transfer


ROOT = transfer.BASE / "teacher_scale_confirmation_v1"
PANEL = ROOT / "dev32"
FREEZE = ROOT / "PANEL_FREEZE.json"
RISK = transfer.c.root.parent / "acquisition_risk_control_v1"


def adapter_digests():
    return {name: replay.sha(replay.ADAPTER / name)
            for name in ("adapter_model.safetensors", "adapter_config.json")}


def prepare():
    base = cohorts.ROOT
    dev_path = Path(study.read(base / "confirmation/PLAN.json")["source_path"])
    train_path = Path(study.read(base / "train/PLAN.json")["source_path"])
    dev, train = study.read(dev_path), study.read(train_path)
    acceptance.ROOT = ROOT
    excluded_ids, excluded_signatures, prior_plans = acceptance.exclusions(train, dev)
    old = study.read(transfer.BASE / "scale_acceptance_v1/dev32/PLAN.json")["episodes"]
    if any(x["table_uid"] not in excluded_ids or x["table_signature"] not in excluded_signatures for x in old):
        raise ValueError("the previous prospective 32 must be excluded")
    chosen = cohorts.select(dev, "dev", 32, excluded_ids, excluded_signatures)
    if (len({row[0] for row in chosen}) != 32 or len({row[1] for row in chosen}) != 32
            or any(row[0] in excluded_ids or row[1] in excluded_signatures for row in chosen)):
        raise ValueError("new tables must be separately locked by UID and normalized table content")
    prior = study.read(transfer.ORIGINAL / "PLAN.json")
    template = transfer.packet_at(transfer.ORIGINAL, "firstpass", prior["episodes"][0]["index"]) / "inputs"
    ROOT.mkdir(mode=0o700)
    cohorts.write_panel(PANEL, chosen, dev_path, prior, template, excluded_ids, "dev")
    record = dict(n=32, prior_plans=prior_plans, excluded_ids=len(excluded_ids),
                  excluded_content=len(excluded_signatures), plan_sha256=replay.sha(PANEL / "PLAN.json"),
                  labels_sha256=replay.sha(PANEL / "LABELS_PRIVATE.json"), adapter_digests=adapter_digests(),
                  budgets=[6, 9], teacher_cap=450_000,
                  risk_state="original pre-scale Pair program", teacher_state="first-pass snapshot",
                  primary="K6 Pair128 teacher scale versus K9 raw teacher",
                  contrasts=["K6 raw", "K6 joint", "K6 same-program scale inheritance", "K9 Pair128 teacher scale"])
    study.write_json(FREEZE, record)
    print(json.dumps(record), flush=True)


def predict_risk(plan):
    av = transfer.av
    original = av.m, av.VARIANT, av.ROOT
    av.m = SimpleNamespace(**vars(transfer.m))
    av.m.state_from_folder = lambda folder: transfer.task.saved_state(
        study.read(Path(folder) / "inputs/public.json"), Path(folder) / "work"
    )
    av.VARIANT, av.ROOT = "risk", RISK
    episodes = plan["episodes"]
    sources = [dict(row, folder=str(transfer.packet_at(PANEL, "firstpass", row["index"]))) for row in episodes]
    paired = {row["index"]: dict(row, folder=str(transfer.packet_at(PANEL, "paired", row["index"])))
              for row in episodes}
    path = ROOT / "RISK_PREDICTIONS.json"
    try:
        av.predict(sources=sources, cheap=paired, output=path, strong_budget=9, fixed_threshold=-1.01)
    finally:
        av.m, av.VARIANT, av.ROOT = original
    predictions = study.read(path)
    rows = routing.indexed(predictions["decisions"])
    sources = routing.indexed(episodes)
    if any(row["id"] != sources[i]["id"] for i, row in rows.items()):
        raise ValueError("risk prediction source mismatch")
    order = sorted(rows, key=lambda i: (-rows[i]["score"], i))
    cost = {key: predictions[key] for key in
            ("forward_calls", "input_tokens_processed", "forward_seconds", "seconds", "http_posts")}
    study.write_json(ROOT / "RISK_ORDER.json", dict(order=order, selected=dict(K6=order[:6], K9=order[:9]),
                                                   cost=cost, state="unadapted native paired candidate"))


def predict_local_scale():
    rows = [
        study.example(row, f"confirmation32:{row['index']}", row["submission"]["scale"])
        for row in study.cases(PANEL)
        if row["valid"] and row["normal"] and row["submission"]
    ]
    source = ROOT / "LOCAL_SCALE_INPUTS.jsonl"
    output = ROOT / "LOCAL_SCALE_PREDICTIONS.json"
    if source.exists():
        frozen = [json.loads(line) for line in source.read_text(encoding="utf-8").splitlines()]
        if frozen != rows:
            raise ValueError("saved readout inputs differ from the native receipts")
    else:
        study.write_rows(source, rows)
    if rows:
        subprocess.run([sys.executable, "-u", "-B", "-m",
                        "research.agent_frontier_portfolio_20261029.tatqa_scale_training",
                        "predict", "--data", str(source), "--arm", f"{replay.ARM}={replay.ADAPTER}",
                        "--out", str(output)], cwd=Path(__file__).resolve().parents[2], check=True)
    else:
        study.write_json(output, dict(rows=[], counts=dict(
            forward_calls=0, input_tokens=0, generated_tokens=0, http_posts=0, input_rows=0, neural_rows=0,
        )))


def run(*, resume_readouts=False):
    lock = study.read(FREEZE)
    if (replay.sha(PANEL / "PLAN.json") != lock["plan_sha256"]
            or replay.sha(PANEL / "LABELS_PRIVATE.json") != lock["labels_sha256"]
            or adapter_digests() != lock["adapter_digests"]):
        raise ValueError("the panel or local adapter changed after the freeze")
    live = ROOT / ("READOUT_RETRY.json" if resume_readouts else "LIVE.json")
    if resume_readouts:
        original = study.read(ROOT / "LIVE.json")
        native = study.read(PANEL / "LOCAL_RESULT.json")
        if (original["status"] != "FAILED" or original["phase"] != "LOCAL_SCALE"
                or native["status"] != "RETURNED" or (ROOT / "LOCAL_SCALE_PREDICTIONS.json").exists()):
            raise ValueError("retry requires completed native episodes and an interrupted scale readout")
    state = dict(status="RUNNING", phase="LOCAL_SCALE" if resume_readouts else "NATIVE",
                 pid=os.getpid(), campus_posts=0)
    study.write_json(live, state)
    transfer.ROOT = PANEL
    unloaded = False
    try:
        unloaded = transfer.c.stop27()
        if not resume_readouts:
            transfer.collect(arms=("firstpass", "paired"))
        state["phase"] = "LOCAL_SCALE"
        transfer.m.study.publish(live, state)
        predict_local_scale()
        state["phase"] = "RISK"
        transfer.m.study.publish(live, state)
        predict_risk(study.read(PANEL / "PLAN.json"))
        state.update(status="RETURNED", phase="FROZEN_RISK_AND_LOCAL_SCALE")
    except BaseException as exc:
        state.update(status="FAILED", error=f"{type(exc).__name__}: {exc}")
        raise
    finally:
        if unloaded:
            state["restoration"] = transfer.c.restore27()
        transfer.m.study.publish(live, state)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("prepare", "run", "resume-readouts"))
    args = parser.parse_args()
    if args.command == "prepare":
        prepare()
    else:
        run(resume_readouts=args.command == "resume-readouts")
