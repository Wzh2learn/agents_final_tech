"""Calibrate a fixed scale-acceptance gate and evaluate on disjoint TAT-QA tables."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time

import tatqa_scale_cohorts as cohorts
import tatqa_scale_study as study


TRANSFER = cohorts.transfer
BASE = TRANSFER.BASE
ORIGINAL = cohorts.ROOT
EXTENSION = ORIGINAL / "adaptive_extension_v1"
ROOT = BASE / "scale_acceptance_v1"
GRID = (0.0, 0.25, 0.5, 1.0, 2.0, 4.0)
MODELS = ("paired-128", "paired-160")
PRIMARY = "paired-160"
N = 32
KEEP = study.KEEP
READOUT = Path(__file__).with_name("tatqa_scale_training.py")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def model_files():
    return {
        name: {
            part: digest(EXTENSION / f"fit_{name.split('-')[1]}" / "paired" / part)
            for part in ("adapter_config.json", "adapter_model.safetensors")
        }
        for name in MODELS
    }


def action_set(current, prediction):
    logits = prediction["logits"]
    action = prediction["action"]
    if (action not in (KEEP, *study.SCALES) or logits is None
            or set(logits) != {KEEP, *study.SCALES}
            or any(not math.isfinite(v) for v in logits.values())):
        raise ValueError("Bad fixed-action readout")
    if action in (KEEP, current):
        return KEEP, None
    margin = logits[action] - max(logits[KEEP], logits[current])
    if margin < 0:
        raise ValueError("A frozen native proposal is outside its saved maximum")
    return action, round(margin, 8)


def predictions_at(path):
    rows = study.read(path)["rows"]
    indexed = {row["source"]: row for row in rows}
    if len(indexed) != len(rows):
        raise ValueError("Repeated readout source")
    return indexed


def evaluation_rows(panel, name, indexed):
    observed = list(study.cases(panel))
    if not observed or [row["index"] for row in observed] != list(range(len(observed))):
        raise ValueError("Panel does not contain one native result per planned case")
    for case in observed:
        native = case["submission"]
        raw = study.grade(case, native)
        if raw != case["success"]:
            raise ValueError("Private re-score disagrees with frozen native outcome")
        joint = study.joint_rule(case, BASE)
        scales = {}
        row = dict(raw=raw, joint=study.grade(case, joint), joint_edit=joint != native,
                   valid=bool(case["normal"] and case["valid"] and native), model={})
        if row["valid"]:
            readout = indexed[f"{name}:{case['index']}"]
            current = native["scale"]
            if readout["scale"] != current:
                raise ValueError("Prediction scale disagrees with frozen candidate")
            for arm in MODELS:
                action, margin = action_set(current, readout["actions"][arm])
                if action == KEEP:
                    correct = raw
                else:
                    if action not in scales:
                        scales[action] = study.grade(case, study.apply_action(native, action))
                    correct = scales[action]
                row["model"][arm] = dict(changed=action != KEEP, margin=margin, correct=correct)
        else:
            if f"{name}:{case['index']}" in indexed:
                raise ValueError("Invalid submission reached a model readout")
            row["model"] = {arm: dict(changed=False, margin=None, correct=raw) for arm in MODELS}
        yield row


def aggregate(rows, arm, threshold=None):
    baseline = [row["raw"] for row in rows]
    if arm == "raw":
        after = baseline
        changes = 0
    elif arm == "joint":
        after = [row["joint"] for row in rows]
        changes = sum(row["joint_edit"] for row in rows)
    else:
        scores = [row["model"][arm] for row in rows]
        edits = [row["changed"] and (threshold is None or row["margin"] > threshold) for row in scores]
        changes = sum(edits)
        after = [score["correct"] if edit else orig
                 for score, edit, orig in zip(scores, edits, baseline, strict=True)]
    result = study.delta(baseline, after)
    assert result["success"] == sum(baseline) + result["recovered"] - result["harmed"]
    result.update(changed=changes, valid=sum(row["valid"] for row in rows),
                  coverage=changes / len(rows))
    return result


def compare_gate(rows, model, threshold):
    fixed = aggregate(rows, model)
    gated = aggregate(rows, model, threshold)
    lost_recoveries = fixed["recovered"] - gated["recovered"]
    averted_harms = fixed["harmed"] - gated["harmed"]
    if min(lost_recoveries, averted_harms) < 0 or gated["changed"] > fixed["changed"]:
        raise ValueError("An acceptance gate changed its frozen proposal")
    assert gated["success"] - fixed["success"] == averted_harms - lost_recoveries
    return dict(gated, lost_recoveries=lost_recoveries, averted_harms=averted_harms,
                net_vs_fixed=gated["success"] - fixed["success"])


def pooled(groups):
    return [row for rows in groups.values() for row in rows]


def select_threshold(rows):
    scored = [(limit, compare_gate(rows, PRIMARY, limit)) for limit in GRID]
    defensible = [(limit, row) for limit, row in scored
                  if row["averted_harms"] and row["net_vs_fixed"] >= 0]
    if not defensible:
        return 0.0, "No grid point reduced harms without a net loss; use the strict zero-margin baseline."
    limit, _ = max(defensible, key=lambda p: (p[1]["net_vs_fixed"], p[1]["averted_harms"], -p[0]))
    return limit, "Maximize net successes among rules averting harms without net loss; tie on harms then lower threshold."


def report_cohort(rows):
    fixed = {arm: aggregate(rows, arm) for arm in ("raw", "joint", *MODELS)}
    grid = {arm: {str(t): compare_gate(rows, arm, t) for t in GRID} for arm in MODELS}
    return dict(fixed=fixed, thresholds=grid)


def calibrate():
    if ROOT.exists():
        raise FileExistsError(ROOT)
    predictions = EXTENSION / "PREDICTIONS.json"
    indexed = predictions_at(predictions)
    groups = {label: list(evaluation_rows(BASE / folder, label, indexed))
              for label, folder in study.COHORTS.items()}
    all_rows = pooled(groups)
    totals = report_cohort(all_rows)
    observed = {arm: row["success"] for arm, row in totals["fixed"].items()}
    if observed != {"raw": 25, "joint": 40, "paired-128": 54, "paired-160": 50}:
        raise ValueError(f"Old cache control scores differ: {observed}")
    folds = {}
    for holdout, rows in groups.items():
        train = pooled({name: material for name, material in groups.items() if name != holdout})
        limit, choice = select_threshold(train)
        folds[holdout] = dict(threshold=limit, choice=choice, score=compare_gate(rows, PRIMARY, limit))
    threshold, choice = select_threshold(all_rows)
    report = dict(scope="Previously exposed 112 tables; scores are descriptive, with three panel-held-out calibration folds.",
                  pooled=totals, per_panel={name: report_cohort(rows) for name, rows in groups.items()},
                  grouped_cv=folds, choice=choice, selected_model=PRIMARY, selected_threshold=threshold,
                  model_posts=0, generated_tokens=0)
    ROOT.mkdir(mode=0o700)
    study.write_json(ROOT / "CALIBRATION.json", report)
    freeze = dict(threshold=threshold, model=PRIMARY, grid=GRID, choice=choice, models=model_files(),
                  calibration_sha256=digest(ROOT / "CALIBRATION.json"), prediction_sha256=digest(predictions),
                  scope="Freeze precedes panel selection and every new native result.",
                  rule="Predicted action differs from the original scale and candidate logit exceeds both KEEP "
                       "and the original scale logit by strictly more than the frozen threshold.")
    study.write_json(ROOT / "GATE_FREEZE.json", freeze)
    print(json.dumps(report), flush=True)


def exclusions(train, dev):
    uids, signatures = cohorts.prior_tables()
    plans = 0
    for path in sorted(BASE.rglob("PLAN.json")):
        if ROOT in path.parents:
            continue
        plans += 1
        for episode in study.read(path).get("episodes", []):
            report = str(episode.get("report", ""))
            uid = episode.get("table_uid")
            if report.startswith("TAT-QA/"):
                uids.add(report.split("/", 1)[1])
            if uid:
                uids.add(uid)
            if episode.get("table_signature"):
                signatures.add(episode["table_signature"])
    for record in (*train, *dev):
        if record["table"]["uid"] in uids:
            signatures.add(cohorts.table_signature(record["table"]["table"]))
    # Avoid duplicated official train content, including tables outside model formation.
    uids.update(item["table"]["uid"] for item in train)
    signatures.update(cohorts.table_signature(item["table"]["table"]) for item in train)
    return uids, signatures, plans


def prepare():
    prior = study.read(TRANSFER.ORIGINAL / "PLAN.json")
    source = Path(study.read(ORIGINAL / "confirmation/PLAN.json")["source_path"])
    train_source = Path(study.read(ORIGINAL / "train/PLAN.json")["source_path"])
    freeze = ROOT / "GATE_FREEZE.json"
    if not freeze.is_file():
        raise ValueError("Calibrate the gate before freezing the new panel")
    if (ROOT / "PANEL_FREEZE.json").exists():
        raise FileExistsError("New set already frozen")
    train, dev = study.read(train_source), study.read(source)
    uids, signatures, plans = exclusions(train, dev)
    candidate = cohorts.select(dev, "dev", N, uids, signatures)
    selected_uids = {item[0] for item in candidate}
    selected_signatures = {item[1] for item in candidate}
    if len(selected_uids) != N or len(selected_signatures) != N or uids & selected_uids or signatures & selected_signatures:
        raise ValueError("New official-dev tables must be disjoint by UID and signature")
    template = TRANSFER.packet_at(TRANSFER.ORIGINAL, "firstpass", prior["episodes"][0]["index"]) / "inputs"
    panel = ROOT / "dev32"
    cohorts.write_panel(panel, candidate, source, prior, template, uids, "dev")
    payload = dict(n=N, prior_plans=plans, excluded_uids=len(uids), excluded_signatures=len(signatures),
                   train_source_sha256=digest(train_source), dev_source_sha256=digest(source),
                   plan_sha256=digest(panel / "PLAN.json"), labels_sha256=digest(panel / "LABELS_PRIVATE.json"),
                   gate_sha256=digest(freeze), native_actor_arms=["firstpass", "paired"],
                   model_posts=0, teacher_posts=0)
    study.write_json(ROOT / "PANEL_FREEZE.json", payload)
    print(json.dumps(payload), flush=True)


def native_cost(rows):
    return dict(cases=len(rows), posts=sum(r["posts"] for r in rows),
                provider_tokens=sum(r["tokens"] for r in rows),
                unknown_usage_requests=sum(r["unknown"] for r in rows),
                actor_seconds=sum(r["seconds"] for r in rows))


def run():
    panel = ROOT / "dev32"
    plan = study.read(panel / "PLAN.json")
    freeze = study.read(ROOT / "GATE_FREEZE.json")
    panel_freeze = study.read(ROOT / "PANEL_FREEZE.json")
    if (panel_freeze["gate_sha256"] != digest(ROOT / "GATE_FREEZE.json")
            or panel_freeze["plan_sha256"] != digest(panel / "PLAN.json")
            or panel_freeze["labels_sha256"] != digest(panel / "LABELS_PRIVATE.json")
            or freeze["models"] != model_files() or len(plan["episodes"]) != N):
        raise ValueError("Frozen evaluation input or adapter changed")
    if (panel / "LOCAL_LIVE.json").exists():
        raise FileExistsError("Native panel was already attempted")
    state = dict(status="RUNNING", phase="NATIVE", pid=os.getpid(), campus_posts=0)
    live = ROOT / "LIVE.json"
    study.write_json(live, state)
    before = time.monotonic()
    unloaded = False
    try:
        unloaded = TRANSFER.c.stop27()
        TRANSFER.ROOT = panel
        TRANSFER.collect(arms=("firstpass", "paired"))
        native = study.read(panel / "LOCAL_RESULT.json")
        if native["status"] != "RETURNED" or any(len(rows) != N for rows in native["arms"].values()):
            raise ValueError("Collect all 32 native rows for both arms")
        state.update(phase="FROZEN_SCALE_READOUT")
        cohorts.m.study.publish(live, state)
        inference = ROOT / "INFERENCE.jsonl"
        study.write_rows(inference, (
            study.example(case, f"new32:{case['index']}", case["submission"]["scale"])
            for case in study.cases(panel)
            if case["valid"] and case["normal"] and case["submission"]
        ))
        output = ROOT / "PREDICTIONS.json"
        args = [sys.executable, "-u", "-B", str(READOUT),
                "predict", "--data", str(inference), "--out", str(output)]
        for arm in MODELS:
            args.extend(("--arm", str(arm) + "=" + str(EXTENSION / f"fit_{arm.split('-')[1]}" / "paired")))
        subprocess.run(args, check=True)
        rows = list(evaluation_rows(panel, "new32", predictions_at(output)))
        if len(rows) != N:
            raise ValueError("Native denominator changed")
        selected = float(freeze["threshold"])
        result = dict(n=N, frozen_threshold=selected, primary=PRIMARY,
                      scores={method: aggregate(rows, method) for method in ("raw", "joint", *MODELS)},
                      guarded_primary=compare_gate(rows, PRIMARY, selected),
                      native={arm: native_cost(arm_rows) for arm, arm_rows in native["arms"].items()},
                      neural_readout=study.read(output)["counts"],
                      inference_sha256=digest(inference), predictions_sha256=digest(output),
                      panel_sha256=digest(panel / "PLAN.json"), gate_sha256=digest(ROOT / "GATE_FREEZE.json"),
                      campus_posts=0, scope="New official DEV32, fixed proposals and pre-frozen threshold.")
        result["total_seconds"] = time.monotonic() - before
        study.write_json(ROOT / "RESULT.json", result)
        print(json.dumps(result), flush=True)
        state.update(status="RETURNED", phase="COMPLETE")
    except BaseException as error:
        state.update(status="FAILED", error=f"{type(error).__name__}: {error}")
        raise
    finally:
        if unloaded:
            state["restoration"] = TRANSFER.c.restore27()
        cohorts.m.study.publish(live, state)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("calibrate", "prepare", "run"))
    {"calibrate": calibrate, "prepare": prepare, "run": run}[parser.parse_args().stage]()
