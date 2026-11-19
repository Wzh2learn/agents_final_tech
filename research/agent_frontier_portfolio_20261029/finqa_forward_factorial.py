"""Cross two real local correction arms with two frozen teacher selectors."""
from __future__ import annotations

import argparse
import gc
import getpass
import json
import os
from pathlib import Path
import time
import traceback

import numpy as np

import finqa_forward_transfer as forward


STATES = ("ordinary", "cheap37")
SELECTORS = ("risk", "value")
BUDGETS = (7, 16)
m = forward.m
av = forward.av
SOURCE = forward.ROOT
ROOT = SOURCE.parent / "forward57_factorial_v1"
FRESH_ROOT = SOURCE.parent / "forward64_factorial_fresh_v1"
FRESH = False


def freeze():
    plan = m.read(SOURCE / "PLAN.json")
    native = m.read(SOURCE / "LOCAL_RESULT.json")
    n = 64 if FRESH else 57
    assert native["status"] == "RETURNED" and len(plan["episodes"]) == n
    assert len({r["group"] for r in plan["episodes"]}) == n
    for name in ("firstpass", *STATES):
        assert [(r["index"], r["id"]) for r in native["arms"][name]] == [
            (r["index"], r["id"]) for r in plan["episodes"]
        ]
    if not FRESH:
        ROOT.mkdir(mode=0o700)
        m.study.new(ROOT / "PLAN.json", dict(
            n=n, source=str(SOURCE), local_states=STATES, selectors=SELECTORS, budgets=BUDGETS,
            primary="cheap37 + value minus ordinary + risk at K16",
            scope="Exposed forward development batch; fixed T0 from each first-pass snapshot.",
            adoption="Original FinQA guard applied anew to each executed local program.",
            cost="Match K and report actual selected teacher usage and local cost separately.",
        ))
    return plan, native


def await_restoration(native):
    show = native.get("restoration")
    if not show:
        return
    target = Path("/proc", str(show["pid"]), "stat")
    registry = m.study.PRIVATE / "research_services/gpu_guard_current.json"
    deadline = time.monotonic() + 120
    while target.exists() and target.read_text().split()[2] not in ("Z", "X"):
        if registry.exists() and m.read(registry)["pid"] == show["pid"]:
            return
        if time.monotonic() >= deadline:
            raise TimeoutError("the previous local owner has not registered")
        time.sleep(1)


def infer():
    import torch

    plan, native = freeze()
    live = ROOT / "LIVE.json"
    state = dict(status="RUNNING", phase="START", pid=os.getpid(), new_teacher_posts=0)
    m.study.new(live, state)
    unloaded = False
    original = av.VARIANT, av.ROOT
    try:
        await_restoration(native)
        unloaded = forward.c.stop27()
        for name in STATES if FRESH else ("ordinary",):
            cheap = {row["index"]: row for row in native["arms"][name]}
            for variant in SELECTORS:
                state["phase"] = f"{name}_{variant}"
                m.study.publish(live, state)
                av.VARIANT, av.ROOT = variant, SOURCE.parent / forward.POLICIES[variant]
                av.predict(sources=plan["episodes"], cheap=cheap,
                           output=ROOT / f"{name}_{variant}_PREDICTIONS.json",
                           strong_budget=max(BUDGETS), fixed_threshold=-1.01)
                gc.collect()
                torch.cuda.empty_cache()
        if FRESH:
            freeze_fresh_policies(plan["episodes"])
        state.update(status="RETURNED", phase="READOUTS_READY")
    except BaseException:
        state.update(status="FAILED", error=traceback.format_exc())
        raise
    finally:
        av.VARIANT, av.ROOT = original
        if unloaded:
            state["restoration"] = forward.c.restore27()
        m.study.publish(live, state)


def predictions(name, selector, sources):
    folder = ROOT if FRESH or name == "ordinary" else SOURCE
    prefix = f"{name}_" if FRESH or name == "ordinary" else ""
    outcome = m.read(folder / f"{prefix}{selector}_PREDICTIONS.json")
    rows = outcome["decisions"]
    assert outcome["variant"] == selector and not outcome["http_posts"] and not outcome["generated_tokens"]
    assert [(r["index"], r["id"]) for r in rows] == [(r["index"], r["id"]) for r in sources]
    ranked = [r["index"] for r in sorted(rows, key=lambda r: (-r["score"], r["index"]))]
    cost = {key: outcome[key] for key in ("forward_calls", "input_tokens_processed", "forward_seconds")}
    return ranked, cost


def freeze_fresh_policies(sources):
    assert not (ROOT / "TEACHER_LIVE.json").exists()
    order = {f"{n}_{s}": predictions(n, s, sources)[0] for n in STATES for s in SELECTORS}
    # Interleave the policies by rank, making all primary selections precede the secondary-only selections.
    union = list(dict.fromkeys(i for rank in zip(*order.values(), strict=True) for i in rank))[:len(sources)]
    chosen = {i for ranking in order.values() for i in ranking[:max(BUDGETS)]}
    m.study.new(ROOT / "POLICIES.json", dict(
        orders={**order, "value": order["cheap37_value"]}, teacher_sequence=[i for i in union if i in chosen],
        budgets=BUDGETS, source="One teacher execution per selected task from its unchanged first-pass snapshot.",
    ))
    m.study.new(ROOT / "PREDICT_RESULT.json", dict(status="RETURNED"))


def fresh_teacher(key=None):
    assert FRESH and m.read(ROOT / "LIVE.json")["status"] == "RETURNED"
    if (ROOT / "TEACHER_LIVE.json").exists():
        raise FileExistsError("preserve the first frozen teacher attempt")
    order = m.read(ROOT / "POLICIES.json")
    selected = order["teacher_sequence"]
    assert set(selected) == {i for n in STATES for s in SELECTORS
                             for i in order["orders"][f"{n}_{s}"][:max(BUDGETS)]}
    key = key or os.environ.get("BUPT_API_KEY") or getpass.getpass("Campus credential (hidden): ")
    if not key:
        raise ValueError("missing campus credential")
    forward.teacher(key, indices=selected, token_cap=1_200_000)


def observed(source, local, teacher, label):
    assert source["index"] == local["index"] == label["index"]
    assert source["id"] == local["id"] == label["id"]
    if teacher is None:
        before = bool(local["native_success"])
        return before, before, True
    assert source["index"] == teacher["index"] and source["id"] == teacher["id"]
    public = m.read(Path(source["folder"]) / "inputs/public.json")
    program, keep = av.guarded_program(local["program"], teacher["program"], public, teacher["normal"])
    correct = m.task.grade(program, public, label["exe_ans"])["execution_correct"]
    return bool(local["native_success"]), bool(correct), keep


def paired(before, after):
    return dict(success=sum(after), recovered=sum(not a and b for a, b in zip(before, after, strict=True)),
                harmed=sum(a and not b for a, b in zip(before, after, strict=True)))


def compare(arms, draws):
    sr, sv, pr, pv = [np.asarray(arms[key], dtype=int) for key in
                      ("ordinary_risk", "ordinary_value", "cheap37_risk", "cheap37_value")]
    contrasts = {"complete_vs_simple": pv - sr, "correction_given_risk": pr - sr,
                 "routing_given_ordinary": sv - sr, "routing_given_pair": pv - pr,
                 "interaction": (pv - pr) - (sv - sr)}
    result = {}
    for key, difference in contrasts.items():
        values = difference[draws].mean(axis=1) * 100
        result[key] = dict(net=int(difference.sum()), wins=int((difference > 0).sum()),
                           losses=int((difference < 0).sum()),
                           interval_pp=np.quantile(values, (0.025, 0.975)).tolist())
    return result


def score():
    assert m.read(ROOT / "LIVE.json")["status"] == "RETURNED"
    plan, native, pool = [m.read(SOURCE / name) for name in ("PLAN.json", "LOCAL_RESULT.json", "TEACHER_RESULT.json")]
    labels = m.read(SOURCE / "LABELS_PRIVATE.json")
    assert pool["status"] == "RETURNED" and pool["unknown"] == 0
    teacher = {r["index"]: r for r in pool["episodes"]}
    sources = plan["episodes"]
    if FRESH:
        sequence = m.read(ROOT / "POLICIES.json")["teacher_sequence"]
        assert list(teacher) == sequence and pool["known_tokens"] <= 1_200_000
    else:
        assert len(teacher) == 57 and pool["posts"] == 107
    assert len(sources) == len(labels) == (64 if FRESH else 57)
    assert sum(row["posts"] for row in teacher.values()) == pool["posts"]
    assert sum(row["tokens"] for row in teacher.values()) == pool["known_tokens"]
    draws = np.random.default_rng(20261119).integers(0, len(sources), size=(20000, len(sources)))
    observations = [teacher.get(row["index"]) for row in sources]
    outcomes = {name: [observed(*args) for args in zip(sources, native["arms"][name], observations, labels, strict=True)]
                for name in STATES}
    policy = {(name, selector): predictions(name, selector, sources) for name in STATES for selector in SELECTORS}
    budgets = {}
    for k in BUDGETS:
        cells, arms = {}, {}
        for (name, selector), (ranked, cost) in policy.items():
            chosen = set(ranked[:k])
            assert chosen <= teacher.keys()
            before = [a for a, _, _ in outcomes[name]]
            after = [b if i in chosen else a for i, (a, b, _) in enumerate(outcomes[name])]
            key = f"{name}_{selector}"
            arms[key] = after
            cells[key] = dict(**paired(before, after), local_success=sum(before), classifier=cost,
                              chosen=ranked[:k], guarded_keep=sum(outcomes[name][i][2] for i in chosen),
                              teacher_posts=sum(teacher[i]["posts"] for i in chosen),
                              teacher_tokens=sum(teacher[i]["tokens"] for i in chosen))
        budgets[str(k)] = dict(cells=cells, contrasts=compare(arms, draws),
                               paired_outcomes={str(r["index"]): [arms[key][r["index"]] for key in arms]
                                                for r in sources}, cell_order=list(arms))
    if not FRESH:
        old = m.read(SOURCE / "COMPARISON.json")
        for k in BUDGETS:
            for selector in SELECTORS:
                saved = old["tables"][str(k)][selector]
                measured = budgets[str(k)]["cells"][f"cheap37_{selector}"]
                assert all(measured[key] == saved[key] for key in ("success", "teacher_tokens"))
    result = dict(n=len(sources), budgets=budgets, local=native["summary"], new_teacher_posts=pool["posts"] if FRESH else 0,
                  new_opencode_generation=sum(x["posts"] for x in native["summary"].values()) if FRESH else 0,
                  new_training_updates=0, teacher_pool_tokens=pool["known_tokens"], teacher_pool_tasks=len(teacher))
    m.study.new(ROOT / "RESULT.json", result)
    print(json.dumps({**result, "budgets": {k: {n: a[n] for n in ("cells", "contrasts")}
                                          for k, a in budgets.items()}}), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("local", "infer", "teacher", "score"))
    parser.add_argument("--fresh", action="store_true")
    args = parser.parse_args()
    FRESH = args.fresh
    if FRESH:
        SOURCE = ROOT = forward.ROOT = FRESH_ROOT
        BUDGETS = (8, 18)
    if args.command in ("local", "teacher") and not FRESH:
        parser.error("new executions require --fresh")
    {"local": forward.collect, "infer": infer, "teacher": fresh_teacher, "score": score}[args.command]()
