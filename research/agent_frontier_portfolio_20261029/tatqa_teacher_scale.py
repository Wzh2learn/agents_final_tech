"""Replay scale-only revisions on saved teacher programs under the original guard."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

import tatqa_action_routing as routing
import tatqa_scale_study as study
import tatqa_transfer as transfer
from tatqa_correction import arithmetic


BASE = transfer.BASE
ROOT = BASE / "teacher_scale_replay_v1"
EXT = BASE / "scale_adaptation_c3_v1" / "adaptive_extension_v1"
ADAPTER = EXT / "fit_128" / "paired"
ARM = "paired-128"
PANELS = ("development32", "forward32", "repeated_development32")
METHODS = ("raw", "joint", "same_program_keep_scale", "pair128", "oracle")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_records():
    readouts = {r["source"]: r for r in study.read(EXT / "PREDICTIONS.json")["rows"]
                if r["source"].split(":", 1)[0] in PANELS[:2]}
    material = {}
    for name in PANELS:
        repeat = name == "repeated_development32"
        original = "development32" if repeat else name
        panel = BASE / study.COHORTS[original]
        plan = routing.indexed(study.read(panel / "PLAN.json")["episodes"])
        result = study.read(panel / "TEACHER_RESULT.json")
        if result["status"] != "RETURNED" or result["unknown"] != 0:
            raise ValueError("Old teacher pool must be complete with known usage")
        teachers = routing.indexed(result["episodes"])
        rank = study.read(panel / "POLICIES.json")["orders"]["risk"]
        if len(rank) != 32 or set(rank) != set(range(32)):
            raise ValueError("Unexpected saved Risk ordering")
        selected = set(rank[:9])
        records = []
        for case in study.cases(panel):
            i = case["index"]
            teacher = teachers[i]
            if case["id"] != teacher["id"] or case["id"] != plan[i]["id"]:
                raise ValueError("Teacher and local receipt identifiers differ")
            if repeat:
                teacher = routing.repeated_t0(BASE, panel, plan[i], i)
                packet = transfer.packet_at(BASE / "state_aware_teacher_v1", "T0", i)
                ledger = study.read(packet / "RESULT.json")["accounting"]
                if ledger["unknown_usage_requests"]:
                    raise ValueError("Repeated teacher usage is incomplete")
                teacher["posts"] = ledger["actual_forwarded_posts"]
            before = case["submission"]
            if case["normal"] and case["valid"]:
                stored = readouts[f"{original}:{i}"]
                if stored["scale"] != before["scale"]:
                    raise ValueError("Saved Pair128 readout does not match the original scale")
                local = study.apply_action(before, stored["actions"][ARM]["action"])
            else:
                local = before
            teacher_case = {**case, **teacher}
            raw_correct = study.grade(teacher_case, teacher["submission"])
            if raw_correct != teacher["success"] or study.grade(case, before) != case["success"]:
                raise ValueError("Original submission does not match the official host receipt")
            records.append(dict(index=i, selected=i in selected, local=local,
                                local_correct=study.grade(case, local), case=case, teacher=teacher_case))
        if len(records) != 32:
            raise ValueError("A saved teacher pool must contain all 32 tasks")
        material[name] = records
    return material


def guard(row, teacher_proposal):
    teacher = {**row["teacher"], "submission": teacher_proposal}
    if not routing.teacher_adopted(row["local"], teacher):
        return row["local_correct"]
    return study.grade(teacher, teacher_proposal)


def inherit_scale(row):
    local, native = row["local"], row["teacher"]["submission"]
    if not local or not native:
        return native
    executor = arithmetic.executor()
    try:
        local_steps = executor.parse_program(local["program"])
        native_steps = executor.parse_program(native["program"])
    except executor.ExecutorContractError:
        return native
    if local_steps == native_steps:
        return {**native, "scale": local["scale"]}
    return native


def teacher_candidates(row, proposed_action=None):
    case = row["teacher"]
    current = case["submission"]
    valid = bool(current and case["normal"] and case["valid"])
    if not valid:
        return {method: current for method in METHODS[:-1]}
    return dict(raw=current, joint=study.joint_rule(case, BASE),
                same_program_keep_scale=inherit_scale(row),
                pair128=study.apply_action(current, study.KEEP if proposed_action is None else proposed_action))


def diagnostic_oracle(row, baseline, *, guard_first):
    case = row["teacher"]
    candidate = case["submission"]
    if baseline or not candidate or not case["normal"] or not case["valid"]:
        return baseline
    grader = (lambda proposal: guard(row, proposal)) if guard_first else (lambda proposal: study.grade(case, proposal))
    return any(grader({**candidate, "scale": s}) for s in study.SCALES)


def summarize(rows, predicted, name, choose, *, prefill_controls):
    before = []
    outcomes = {method: [] for method in METHODS}
    action_edits = {method: 0 for method in METHODS[:-1]}
    local = []
    cost = dict(teacher_tasks=0, historical_posts=0, historical_tokens=0)
    standalone = dict(raw=0, oracle=0)
    for row in rows:
        t = row["teacher"]
        native = t["submission"]
        raw_correct = guard(row, native)
        local.append(row["local_correct"])
        if choose == "risk_K9" and not row["selected"]:
            before.append(row["local_correct"])
            for observations in outcomes.values():
                observations.append(row["local_correct"])
            continue
        before.append(raw_correct)
        cost["teacher_tasks"] += 1
        cost["historical_posts"] += t["posts"]
        cost["historical_tokens"] += t["tokens"]
        standalone["raw"] += t["success"]
        standalone["oracle"] += diagnostic_oracle(row, t["success"], guard_first=False)
        eligible = bool(native and t["valid"] and t["normal"])
        action = study.KEEP
        if eligible and prefill_controls:
            readout = predicted[f"{name}:{row['index']}"]
            if readout["scale"] != native["scale"]:
                raise ValueError("Teacher scale changed after the frozen readout")
            action = readout["actions"][ARM]["action"]
        edits = teacher_candidates(row, action)
        for name_, proposal in edits.items():
            action_edits[name_] += int(proposal != native)
            outcomes[name_].append(guard(row, proposal))
        outcomes["oracle"].append(diagnostic_oracle(row, raw_correct, guard_first=True))
    stats = {name_: study.delta(before, result) for name_, result in outcomes.items()}
    for method, count in action_edits.items():
        stats[method]["scale_edits"] = count
    return dict(local=sum(local), profiled=choose, results=stats, shared_teacher_cost=cost,
                standalone_selected=standalone)


def scores(groups, predictions, run_prefill):
    return {name: {
        scope: summarize(rows, predictions, name, scope, prefill_controls=run_prefill)
        for scope in ("risk_K9", "full_pool")
    } for name, rows in groups.items()}


def combined(results):
    out = {}
    for quota in ("risk_K9", "full_pool"):
        rows = [results[name][quota] for name in PANELS[:2]]
        out[quota] = dict(
            local=sum(row["local"] for row in rows),
            results={method: {k: sum(row["results"][method][k] for row in rows)
                              for k in rows[0]["results"][method]}
                     for method in METHODS},
            shared_teacher_cost={k: sum(row["shared_teacher_cost"][k] for row in rows)
                                 for k in rows[0]["shared_teacher_cost"]},
            standalone_selected={k: sum(row["standalone_selected"][k] for row in rows)
                                 for k in rows[0]["standalone_selected"]},
        )
    return out


def main():
    if ROOT.exists():
        raise FileExistsError(ROOT)
    groups = source_records()
    before = scores(groups, {}, False)
    baseline = combined(before)
    if baseline["risk_K9"]["results"]["raw"]["success"] != 40:
        raise ValueError("Frozen raw K9 cascade must reproduce 40 on both old panels combined")
    ROOT.mkdir(mode=0o700)
    study.write_json(ROOT / "CPU_BASELINE.json", dict(per_panel=before, combined=baseline,
                                                     pair128_available=False, model_posts=0, campus_posts=0))
    print(json.dumps({"phase": "CPU_BASELINE", "risk_K9": baseline["risk_K9"]}), flush=True)
    public = ROOT / "INFERENCE.jsonl"
    study.write_rows(public, (
        study.example(row["teacher"], f"{name}:{row['index']}", row["teacher"]["submission"]["scale"])
        for name, rows in groups.items() for row in rows
        if row["teacher"]["valid"] and row["teacher"]["normal"] and row["teacher"]["submission"]
    ))
    study.write_json(ROOT / "FREEZE.json",
                     dict(panels=PANELS, original_proposals=True, K=9, policy="saved Risk",
                          adapter=ARM, adapter_sha256=sha(ADAPTER / "adapter_model.safetensors"),
                          adapter_config_sha256=sha(ADAPTER / "adapter_config.json"), inference_sha256=sha(public)))
    prediction = ROOT / "PREDICTIONS.json"
    started = time.monotonic()
    live = ROOT / "LIVE.json"
    state = dict(status="RUNNING", phase="FROZEN_TEACHER_SCALE_READOUT", pid=os.getpid(),
                 campus_posts=0, open_code_posts=0)
    study.write_json(live, state)
    unloaded = False
    try:
        unloaded = transfer.c.stop27()
        script = Path(__file__).with_name("tatqa_scale_training.py")
        subprocess.run([sys.executable, "-u", "-B", str(script), "predict", "--data", str(public),
                        "--arm", f"{ARM}={ADAPTER}", "--out", str(prediction)], check=True)
        receipt = study.read(prediction)
        indexed = {row["source"]: row for row in receipt["rows"]}
        if len(indexed) != len(receipt["rows"]):
            raise ValueError("Duplicate teacher inputs")
        after = scores(groups, indexed, True)
        actual = combined(after)
        for quota in ("risk_K9", "full_pool"):
            for method in ("raw", "joint", "same_program_keep_scale", "oracle"):
                if actual[quota]["results"][method] != baseline[quota]["results"][method]:
                    raise ValueError("GPU evaluation moved a fixed CPU comparator")
            if actual[quota]["shared_teacher_cost"] != baseline[quota]["shared_teacher_cost"]:
                raise ValueError("Scale adaptation moved the fixed teacher cost")
        result = dict(per_panel=after, primary_combined=actual, campus_posts=0, open_code_posts=0,
                      prefill=receipt["counts"], seconds=time.monotonic()-started,
                      scope="Old saved teacher proposals, old Risk selection; repeated T0 remains descriptive.")
        study.write_json(ROOT / "RESULT.json", result)
        print(json.dumps(result), flush=True)
        state.update(status="RETURNED", phase="COMPLETE")
    except BaseException as error:
        state.update(status="FAILED", error=f"{type(error).__name__}: {error}")
        raise
    finally:
        if unloaded:
            state["restoration"] = transfer.c.restore27()
        transfer.m.study.publish(live, state)


if __name__ == "__main__":
    main()
