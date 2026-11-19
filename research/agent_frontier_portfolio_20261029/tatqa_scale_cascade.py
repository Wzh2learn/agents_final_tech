"""Gate and replay a single K18 TAT-QA cascade on the C3 confirmation cohort."""

from __future__ import annotations

import argparse
import getpass
import math
import os
from pathlib import Path
import shutil
import time


SIZE = 64
K = 18
DOSES = ("032", "064", "096")
EXTENSION_DOSES = ("128", "160")
EXTENSION = "adaptive_extension_v1"
EXTENSION_CAP = 500_000
EXTENSION_MIN_SUCCESS = 23
POLICIES = ("value", "risk")
GATE_MARGIN = 3
CASCADE = "cascade_k18_v1"


def complete_rows(rows, size=SIZE):
    by_index = {row["index"]: row for row in rows}
    if len(rows) != size or sorted(by_index) != list(range(size)):
        raise ValueError(f"expected exactly {size} consecutive original indices")
    return by_index


def checked_scores(score):
    rows = complete_rows(score["rows"])
    successes = {}
    for method in ("raw", "paired", "joint", "ordinary"):
        values = [row["correct"][method] for row in rows.values()]
        if any(type(value) is not bool for value in values):
            raise ValueError(f"{method} does not have binary official outcomes")
        successes[method] = sum(values)
        reported = score["scores"][method]
        if (reported["n"], reported["success"]) != (SIZE, successes[method]):
            raise ValueError(f"{method} score summary disagrees with case outputs")
    margins = {method: successes["paired"] - successes[method] for method in ("joint", "ordinary")}
    return rows, successes, margins


def read_extension_gate(root, transfer):
    m = transfer.m
    manifest_path = root / "EXTENSION_PLAN.json"
    manifest = m.read(manifest_path)
    confirmation_plan = root.parent / "confirmation" / "PLAN.json"
    if (manifest["K"], manifest["min_margin"], manifest["min_pair_success"], manifest["teacher_token_cap"]) != (
            K, GATE_MARGIN, EXTENSION_MIN_SUCCESS, EXTENSION_CAP):
        raise ValueError("unexpected extension teacher gate")
    if manifest["confirmation_plan_sha256"] != m.sha(confirmation_plan):
        raise ValueError("locked TAT-QA confirmation plan differs")
    candidates, reports = {}, {}
    for dose in EXTENSION_DOSES:
        path = root / f"ALL_{dose}.json"
        rows, successes, margins = checked_scores(m.read(path)["confirmation64"])
        eligible = successes["paired"] >= EXTENSION_MIN_SUCCESS and min(margins.values()) >= GATE_MARGIN
        candidates[dose] = rows
        reports[dose] = dict(successes=successes, margins=margins, eligible=eligible, score_sha256=m.sha(path))
    eligible = [dose for dose in EXTENSION_DOSES if reports[dose]["eligible"]]
    selected = max(eligible, key=lambda dose: (reports[dose]["successes"]["paired"], -int(dose))) if eligible else None
    gate = dict(status="OPEN" if selected else "CLOSED", selected=selected, K=K, dose_results=reports,
                teacher_token_cap=EXTENSION_CAP, freeze_sha256=m.sha(manifest_path),
                scope="Adaptive follow-up on the previously scored locked TAT-QA cohort")
    return gate, candidates[selected] if selected else {}


def read_gate(root, transfer):
    if root.name == EXTENSION:
        return read_extension_gate(root, transfer)
    m = transfer.m
    freeze_path = root / "TRAINING_FREEZE.json"
    freeze = m.read(freeze_path)
    dose = freeze["selected"]
    if dose not in DOSES or (freeze["K"], freeze["gate"]) != (K, GATE_MARGIN):
        raise ValueError("unexpected C3 training freeze")
    score_path = root / f"ALL_{dose}.json"
    score = m.read(score_path)["confirmation64"]
    rows, successes, margins = checked_scores(score)
    open_gate = score["stage_b_gate"] is True and min(margins.values()) >= GATE_MARGIN
    gate = dict(status="OPEN" if open_gate else "CLOSED", selected=dose, K=K, successes=successes,
                paired_margins=margins, stored_gate=score["stage_b_gate"],
                freeze_sha256=m.sha(freeze_path), score_sha256=m.sha(score_path))
    return gate, rows


def active_gate(root, transfer):
    gate, rows = read_gate(root, transfer)
    recorded = transfer.m.read(root / CASCADE / "GATE.json")
    if gate != recorded or gate["status"] != "OPEN":
        raise ValueError("stage B gate is closed or its inputs have changed")
    return rows


def copy_packet(source, target):
    for name in ("inputs", "work", "dependencies"):
        shutil.copytree(source / name, target / name)


def prepare(root, transfer):
    m, task = transfer.m, transfer.task
    gate, scored = read_gate(root, transfer)
    output = root / CASCADE
    output.mkdir(mode=0o700)
    m.study.new(output / "GATE.json", gate)
    print(gate, flush=True)
    if gate["status"] == "CLOSED":
        return

    panel = (root.parent if root.name == EXTENSION else root) / "confirmation"
    plan = m.read(panel / "PLAN.json")
    local = m.read(panel / "LOCAL_RESULT.json")
    if plan["primary_K"] != K or not plan["prospective_complete"] or local["status"] != "RETURNED":
        raise ValueError("expected the full frozen TAT-QA C3 confirmation batch")
    sources = complete_rows(plan["episodes"])
    paired = complete_rows(local["arms"]["paired"])
    firstpass = complete_rows(local["arms"]["firstpass"])
    patched = []
    for index, source in sources.items():
        raw = paired[index]
        candidate = scored[index]["submissions"]["paired"]
        old = raw["submission"]
        if source["id"] != raw["id"] or source["id"] != firstpass[index]["id"]:
            raise ValueError("C3 confirmation source identifiers disagree")
        if old != scored[index]["submissions"]["raw"] or raw["success"] != scored[index]["correct"]["raw"]:
            raise ValueError("C3 raw submission and score do not match the frozen result")
        for arm in ("firstpass", "paired"):
            copy_packet(transfer.packet_at(panel, arm, index), transfer.packet_at(output, arm, index))
        if candidate != old:
            if not raw["normal"] or not raw["valid"] or not old or not candidate or old["program"] != candidate["program"]:
                raise ValueError("only the scale of a valid original program may be adapted")
            folder = transfer.packet_at(output, "paired", index)
            public = m.read(folder / "inputs/public.json")
            execution = task.submit_program(candidate["program"], candidate["scale"], public, folder / "work",
                                            origin="c3_scale_adapter_replay")
            if execution["status"] != "executed":
                raise ValueError("adapted fixed program failed public execution")
        patched.append(dict(raw, submission=candidate, success=scored[index]["correct"]["paired"]))

    shutil.copyfile(panel / "LABELS_PRIVATE.json", output / "LABELS_PRIVATE.json")
    m.study.new(output / "PLAN.json", plan)
    m.study.new(output / "LOCAL_RESULT.json", dict(status="RETURNED", arms={"firstpass": list(firstpass.values()),
                "paired": patched}, scope="Immutable C3 local receipts with scale-only host replay in a separate work tree"))
    print(f"Prepared all {SIZE} patched local states and original T0 first-pass snapshots.", flush=True)


def cost_fields(predictions):
    return {key: predictions[key] for key in ("forward_calls", "input_tokens_processed", "forward_seconds", "seconds")
            if key in predictions}


def rank(root, transfer):
    active_gate(root, transfer)
    output = root / CASCADE
    m = transfer.m
    if m.read(output / "LOCAL_RESULT.json")["status"] != "RETURNED":
        raise ValueError("prepare the complete local clone before running native readouts")
    m.study.new(output / "RANK_ATTEMPT.json", dict(K=K, status="STARTED"))
    transfer.ROOT = output
    unloaded = False
    try:
        unloaded = transfer.c.stop27()
        transfer.predict(strong_budget=K, freeze=False)
    finally:
        if unloaded:
            transfer.c.restore27()


def freeze(root, transfer):
    active_gate(root, transfer)
    m = transfer.m
    output = root / CASCADE
    plan = m.read(output / "PLAN.json")
    sources = complete_rows(plan["episodes"])
    orders, classifiers = {}, {}
    for policy in POLICIES:
        predictions = m.read(output / f"{policy}_PREDICTIONS.json")
        decisions = complete_rows(predictions["decisions"])
        if (predictions["variant"] != policy or predictions["strong_budget"] != K
                or predictions["forward_calls"] != SIZE or predictions["http_posts"] != 0):
            raise ValueError("unexpected frozen classifier prediction contract")
        if any(row["id"] != sources[index]["id"] or not math.isfinite(row["score"])
               for index, row in decisions.items()):
            raise ValueError("classifier row identity or score is invalid")
        orders[policy] = sorted(decisions, key=lambda index: (-decisions[index]["score"], index))[:K]
        classifiers[policy] = cost_fields(predictions)

    selected = sorted(set(orders["value"]) | set(orders["risk"]))
    pool = output / "teacher_pool"
    pool.mkdir(mode=0o700)
    for index in selected:
        copy_packet(transfer.packet_at(output, "firstpass", index), transfer.packet_at(pool, "firstpass", index))
    shutil.copyfile(output / "LABELS_PRIVATE.json", pool / "LABELS_PRIVATE.json")
    teacher_pool = dict(plan, episodes=[sources[index] for index in selected])
    if root.name == EXTENSION:
        teacher_pool["teacher_token_cap"] = EXTENSION_CAP
    m.study.new(pool / "PLAN.json", teacher_pool)
    m.study.new(pool / "POLICIES.json", dict(orders=orders, primary_K=K, union=selected, classifiers=classifiers,
                    pool_plan_sha256=m.sha(pool / "PLAN.json"), gate_sha256=m.sha(output / "GATE.json")))
    m.study.new(pool / "RUN_RESULT.json", dict(status="RETURNED", phase="AWAITING_T0",
                scope="Original first-pass snapshots, one fresh teacher episode for every selected union task"))
    print(f"Frozen K={K}: union {len(selected)}, overlap {2 * K - len(selected)}.", flush=True)


def frozen_pool(root, transfer):
    active_gate(root, transfer)
    m = transfer.m
    output = root / CASCADE
    pool = output / "teacher_pool"
    policy = m.read(pool / "POLICIES.json")
    orders = policy["orders"]
    union = sorted(set(orders["value"]) | set(orders["risk"]))
    if (policy["primary_K"] != K or set(orders) != set(POLICIES)
            or any(len(order) != K or len(set(order)) != K or not set(order) <= set(range(SIZE))
                                       for order in orders.values())
            or policy["union"] != union or policy["pool_plan_sha256"] != m.sha(pool / "PLAN.json")
            or policy["gate_sha256"] != m.sha(output / "GATE.json")):
        raise ValueError("frozen K18 policies or teacher plan changed")
    return output, pool, policy


def teacher(root, transfer):
    _, pool, _ = frozen_pool(root, transfer)
    if (pool / "TEACHER_ATTEMPT.json").exists() or (pool / "TEACHER_RESULT.json").exists():
        raise ValueError("the frozen teacher pool has already been attempted")
    key = os.environ.get("BUPT_API_KEY") or getpass.getpass("Campus credential (hidden): ")
    if not key:
        raise ValueError("a campus credential is required")
    m = transfer.m
    m.study.new(pool / "TEACHER_ATTEMPT.json", dict(status="STARTED", started_at=time.time(),
                policy_sha256=m.sha(pool / "POLICIES.json")))
    transfer.ROOT = pool
    if root.name == EXTENSION:
        token_cap = m.read(pool / "PLAN.json")["teacher_token_cap"]
        if token_cap != EXTENSION_CAP:
            raise ValueError("extension teacher budget differs")
        transfer.teacher(key, token_cap=token_cap)
    else:
        transfer.teacher(key)


def cost(rows):
    return dict(posts=sum(row["posts"] for row in rows), known_tokens=sum(row["tokens"] for row in rows),
                actor_seconds=sum(row["seconds"] for row in rows),
                unknown_requests=sum(row.get("unknown", 0) for row in rows))


def score(root, transfer):
    output, pool, policy = frozen_pool(root, transfer)
    m, task = transfer.m, transfer.task
    attempt = m.read(pool / "TEACHER_ATTEMPT.json")
    if attempt["policy_sha256"] != m.sha(pool / "POLICIES.json"):
        raise ValueError("K18 selection changed after the teacher attempt started")
    plan = m.read(output / "PLAN.json")
    sources = complete_rows(plan["episodes"])
    labels = complete_rows(m.read(output / "LABELS_PRIVATE.json"))
    local = m.read(output / "LOCAL_RESULT.json")["arms"]
    paired = complete_rows(local["paired"])
    teacher_result = m.read(pool / "TEACHER_RESULT.json")
    if root.name == EXTENSION and (teacher_result["token_cap"] != EXTENSION_CAP
                                  or teacher_result["known_tokens"] + teacher_result["unknown_reserve"] > EXTENSION_CAP):
        raise ValueError("extension teacher ledger exceeded its frozen token cap")
    teachers = {row["index"]: row for row in teacher_result["episodes"]}
    if (teacher_result["status"] != "RETURNED" or sorted(teachers) != policy["union"]
            or len(teachers) != len(teacher_result["episodes"])):
        raise ValueError("native teacher pool did not return every frozen union task exactly once")

    outcomes = {}
    for index, row in teachers.items():
        candidate, teacher_candidate = paired[index]["submission"], row["submission"]
        if sources[index]["id"] != paired[index]["id"] or row["id"] != sources[index]["id"] or row["id"] != labels[index]["id"]:
            raise ValueError("native T0, local and scorer IDs disagree")
        public = m.read(transfer.packet_at(output, "firstpass", index) / "inputs/public.json")
        keep = not row["normal"] or not row["valid"]
        if isinstance(candidate, dict) and isinstance(teacher_candidate, dict) and candidate["scale"] == teacher_candidate["scale"]:
            keep = keep or transfer.av.percent_scale_only(candidate["program"], teacher_candidate["program"])
        final = candidate if keep else teacher_candidate
        normal = paired[index]["normal"] if keep else row["normal"]
        graded = task.grade(final, public, labels[index]["exe_ans"], metric_dir=plan["metric_dir"])
        after = bool(normal and graded["execution_correct"])
        outcomes[index] = dict(index=index, before=paired[index]["success"], after=after, guard_keep=keep)
        if teacher_result["unknown"]:
            raw = m.read(transfer.packet_at(pool, "teacher", index) / "RESULT.json")
            row["unknown"] = len(raw["accounting"]["unknown_usage_requests"])

    baseline = sum(row["success"] for row in paired.values())
    arms = {}
    for name, indices in policy["orders"].items():
        chosen = [outcomes[index] for index in indices]
        recovered = sum(not row["before"] and row["after"] for row in chosen)
        damaged = sum(row["before"] and not row["after"] for row in chosen)
        arms[name] = dict(success=baseline + recovered - damaged, recovered=recovered, damaged=damaged,
                          teacher_tasks=K, selected=indices, teacher=cost([teachers[index] for index in indices]),
                          classifier=policy["classifiers"][name])

    report = dict(status="RETURNED", tasks=SIZE, K=K, local_success=baseline, arms=arms,
                  common_local={name: cost(rows) for name, rows in local.items()},
                  scale_adapter=dict(valid_states=sum(row["valid"] and row["normal"] for row in paired.values()),
                      shared_experiment_predictions=str(root / (
                          "PREDICTIONS.json" if root.name == EXTENSION else "ALL_PREDICTIONS.json")),
                      scope="Aggregate counters span old/new panels and candidate adapters; per-arm timing unavailable."),
                  physical_union={key: teacher_result[key] for key in ("posts", "known_tokens", "unknown", "unknown_reserve", "seconds")},
                  union_tasks=len(teachers), shared_tasks=2 * K - len(teachers),
                  gate=m.read(output / "GATE.json"), outcomes=list(outcomes.values()),
                  scope="A new K18 lookup on C3 confirmation states. T0 receives the original first-pass snapshot.")
    m.study.new(output / "COMPARISON.json", report)
    print({key: value for key, value in report.items() if key != "outcomes"}, flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("prepare", "rank", "freeze", "teacher", "score"))
    parser.add_argument("--extension", action="store_true", help="use the frozen 128/160-table follow-up")
    args = parser.parse_args()
    import tatqa_transfer as transfer

    root = transfer.BASE / "scale_adaptation_c3_v1"
    if args.extension:
        root = root / EXTENSION
    command = {"prepare": prepare, "rank": rank, "freeze": freeze, "teacher": teacher, "score": score}
    command[args.mode](root, transfer)


if __name__ == "__main__":
    main()
