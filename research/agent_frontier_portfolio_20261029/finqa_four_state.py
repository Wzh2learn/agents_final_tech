"""Matched four-state utility and execution-feedback visibility on FinQA."""
import argparse
from collections import Counter
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback

import finqa_acquisition_learning as value
import finqa_patch_learning as patch


m = value.m
LEGACY = value.ROOT
RUN = LEGACY.parent / "acquisition_four_state_v1"
ARMS = ("full", "static")
LABELS = {(False, False): "N", (False, True): "B",
          (True, False): "A", (True, True): "D"}
CLASS_NAMES = {"N": "both_fail", "B": "recover", "A": "damage", "D": "keep_ok"}


def encode(tokenizer, request, label):
    return m.tokens.encode_completion(
        request, dict(role="assistant", content=json.dumps(dict(outcome=label))),
        tokenizer, 16384, completion_kind="text"
    )


def request_for(arm, public, initial, current):
    if arm == "static":
        initial = {key: field for key, field in initial.items() if key != "execution_feedback"}
        current = {key: field for key, field in current.items() if key != "execution_feedback"}
    request = value.request(public, initial, current)
    system = request["messages"][0]["content"].split("B means", 1)[0]
    request["messages"][0]["content"] = system + (
        "Judge correctness of the local program and the result after the controller. "
        "B means the local answer is wrong and the result after the controller is correct. "
        "A means the local answer is correct and the result after the controller is wrong. "
        "D means both answers are correct. N means both answers are wrong. "
        "Execution values are observed computations, not correctness labels. "
        "Return exactly one JSON object with the single key outcome and one letter A, B, D or N."
    )
    return request


def prepare():
    prior_plan = m.read(LEGACY / "PLAN.json")
    prior_data = m.read(LEGACY / "DATA.json")
    old_views = m.read(LEGACY / "TRAIN_VIEWS.json")["views"]
    labels = m.read(patch.step1 / "TRAIN_LABELS_PRIVATE.json")
    sources = {row["index"]: row for row in m.read(value.router.RELATIVE_ROOT / "CHEAP_PLAN.json")["episodes"]}
    teacher_study = m.read(value.TEACHER / "RESULT.json")
    assert teacher_study["status"] == "RETURNED"
    assert len(teacher_study["episodes"]) == 96
    assert len(old_views) == 252 and len(prior_data["anchor_groups"]) == 121
    assert len(prior_plan["schedule"]) == 434
    tokenizer = m.tokens.load_tokenizer(m.learning.MODEL)
    groups = {arm: [] for arm in ARMS}
    census = Counter()
    source_census = Counter()
    legacy_census = Counter()
    for teacher, old_group in zip(teacher_study["episodes"], prior_data["patch_groups"], strict=True):
        index = teacher["index"]
        source = Path(sources[index]["source_folder"])
        public = m.read(source / "inputs/public.json")
        initial = m.state_from_folder(source)
        assert public["id"] == teacher["id"] == labels[index]["id"]
        completed = m.read(Path(teacher["folder"]) / "RESULT.json")["agent_completed"]
        expected = [row for row in old_views if row["index"] == index]
        assert len(expected) == len(old_group)
        encoded = {arm: [] for arm in ARMS}
        seen = set()
        for view, reference in zip(expected, old_group, strict=True):
            assert view["id"] == public["id"]
            assert reference["source_index"] == index and reference["view_kind"] == view["kind"]
            program = view["program"]
            selected, kept = value.guarded_program(program, teacher["program"], public, completed)
            gold = labels[index]["exe_ans"]
            before = m.task.grade(program, public, gold)["execution_correct"]
            after = m.task.grade(selected, public, gold)["execution_correct"]
            utility = int(after) - int(before)
            collapsed = {-1: "A", 0: "N", 1: "B"}[utility]
            assert utility == view["utility"] and kept == view["guard_keep"]
            assert collapsed == view["target"]
            label = LABELS[before, after]
            name = CLASS_NAMES[label]
            census[name] += 1
            legacy_census[collapsed] += 1
            seen.add(name)
            current = dict(current_program=program, execution_feedback=m.task.execute_public(program, public))
            for arm in ARMS:
                row = encode(tokenizer, request_for(arm, public, initial, current), label)
                row.update(source_index=index, view_kind=view["kind"])
                encoded[arm].append(row)
        source_census.update(seen)
        for arm in ARMS:
            groups[arm].append(encoded[arm])
    assert dict(legacy_census) == prior_plan["target_counts"]
    assert census["keep_ok"] + census["both_fail"] == legacy_census["N"]
    assert sum(census.values()) == 252
    receipt = dict(sources=96, views=252, replay=121, optimizer_updates=434,
                   training_forwards=sum(len((prior_data["anchor_groups"] if item["kind"] == "replay"
                                              else prior_data["patch_groups"])[item["index"]])
                                         for item in prior_plan["schedule"]),
                   target_counts=dict(census), source_groups_by_target=dict(source_census),
                   legacy_target_counts=dict(legacy_census), http_posts=0)
    for arm in ARMS:
        root = RUN / arm
        root.mkdir(parents=True)
        plan = dict(prior_plan, arm=arm, target_counts=dict(census))
        m.study.new(root / "PLAN.json", plan)
        m.study.new(root / "DATA.json", dict(anchor_groups=prior_data["anchor_groups"], patch_groups=groups[arm]))
    m.study.new(RUN / "LABEL_CENSUS.json", receipt)
    print(json.dumps(receipt), flush=True)


def panels():
    dev = m.read(value.router.ROOT / "FEATURE_PLAN.json")["dev"]
    dev_plan = m.read(LEGACY.parent / "paired_state_negatives_v1/native_v1/PLAN.json")
    dev_local = {row["index"]: row for row in dev_plan["episodes"] if row["arm"] == "paired_state_branch"}
    forward_root = LEGACY.parent / "forward_sources57_v1"
    forward = m.read(forward_root / "PLAN.json")["episodes"]
    forward_rows = m.read(forward_root / "LOCAL_RESULT.json")["arms"]["cheap37"]
    forward_local = {row["index"]: row for row in forward_rows}
    assert len(dev) == len(dev_local) == 64
    assert len(forward) == len(forward_local) == 57
    return (("DEV64", dev, dev_local), ("FORWARD57", forward, forward_local))


def tatqa_panel(root, name):
    from tatqa_correction import saved_state
    from tatqa_transfer import packet_at

    episodes = m.read(root / "PLAN.json")["episodes"]
    sources = [dict(row, folder=str(packet_at(root, "firstpass", row["index"]))) for row in episodes]
    local = {row["index"]: dict(row, folder=str(packet_at(root, "paired", row["index"]))) for row in episodes}

    def state(folder):
        return saved_state(m.read(folder / "inputs/public.json"), folder / "work")

    return name, sources, local, state


def predict_panel(arm, spec, tokenizer, model, root):
    import torch

    name, sources, local, state = spec
    ordered = list(CLASS_NAMES)
    started = time.monotonic()
    rows = []
    for source in sources:
        folder = Path(source["folder"])
        current_folder = Path(local[source["index"]]["folder"])
        public = m.read(folder / "inputs/public.json")
        assert public["id"] == source["id"] == local[source["index"]]["id"]
        request = request_for(arm, public, state(folder), state(current_folder))
        encoded = [encode(tokenizer, request, label)["input_ids"] for label in ordered]
        at = next(i for i, row in enumerate(zip(*encoded)) if len(set(row)) > 1)
        assert all(row[at + 1:] == encoded[0][at + 1:] for row in encoded)
        classes = [row[at] for row in encoded]
        assert len(set(classes)) == len(ordered)
        free_gib = next(int(x.split()[1]) / 1024**2 for x in Path("/proc/meminfo").read_text().splitlines()
                        if x.startswith("MemAvailable:"))
        if free_gib < 32:
            raise RuntimeError("32GiB memory reserve")
        batch = torch.tensor([encoded[0][:at]], device="cuda")
        with torch.inference_mode():
            logits = model(input_ids=batch, use_cache=False, logits_to_keep=1).logits[0, -1, classes].float()
            probabilities = logits.softmax(-1).cpu().tolist()
            recoverability = logits[[0, 1]].softmax(-1).cpu().tolist()[1]
            damage_given_correct = logits[[2, 3]].softmax(-1).cpu().tolist()[0]
        p = dict(zip(CLASS_NAMES.values(), probabilities, strict=True))
        rows.append(dict(index=source["index"], id=source["id"], probabilities=p,
                         score=p["recover"] - p["damage"], risk=p["both_fail"] + p["recover"],
                         recoverability=recoverability, damage_given_correct=damage_given_correct,
                         input_tokens=at))
        del batch, logits
    m.study.new(root / (name + "_PREDICTIONS.json"),
                dict(decisions=rows, forward_calls=len(rows), generated_tokens=0, http_posts=0,
                     input_tokens=sum(row["input_tokens"] for row in rows),
                     seconds=time.monotonic() - started))
    print(json.dumps(dict(arm=arm, panel=name, predictions=len(rows))), flush=True)


def predict(arm):
    import torch
    from peft import PeftModel
    from transformers import AutoModelForCausalLM
    from scripts.graph.research_gpu_guard import gpu_lease

    root = RUN / arm
    plan = m.read(root / "PLAN.json")
    tokenizer = m.tokens.load_tokenizer(m.learning.MODEL)
    with m.study.core.resource_lock(), gpu_lease():
        base = AutoModelForCausalLM.from_pretrained(
            plan["model"], dtype=torch.bfloat16, device_map={"": 0},
            attn_implementation="sdpa", local_files_only=True, trust_remote_code=False
        )
        model = PeftModel.from_pretrained(base, str(root / "value_policy"))
        model.eval()
        for name, sources, local in panels():
            predict_panel(arm, (name, sources, local, m.state_from_folder), tokenizer, model, root)
        if arm == "full":
            try:
                from tatqa_transfer import ORIGINAL

                predict_panel(arm, tatqa_panel(ORIGINAL, "TATQA_DEV32"), tokenizer, model, root)
            except Exception:
                m.study.new(root / "TATQA_DEV32_ERROR.json", dict(error=traceback.format_exc()))


def order_by_score(rows):
    return [row["index"] for row in sorted(rows, key=lambda row: (-row["score"], row["index"]))]


def compare_pair(first, second, seed):
    """Resample paired task correctness differences on the fixed panel."""
    import numpy as np

    differences = np.asarray(first, dtype=int) - np.asarray(second, dtype=int)
    samples = np.random.default_rng(seed).integers(len(differences), size=(20000, len(differences)))
    interval = np.quantile(differences[samples].mean(axis=1), [0.025, 0.975]).tolist()
    return dict(net=int(differences.sum()), gains=int((differences > 0).sum()),
                losses=int((differences < 0).sum()), rate_interval=interval)


def outcome_curve(rows, order):
    baseline = sum(row["before"] for row in rows.values())
    selected = []
    points = []
    for k in range(len(rows) + 1):
        if k:
            selected.append(rows[order[k - 1]])
        points.append(dict(K=k, success=baseline + sum(row["utility"] for row in selected),
                           recovered=sum(row["utility"] > 0 for row in selected),
                           damaged=sum(row["utility"] < 0 for row in selected),
                           semantic_recovered=sum(row["utility"] > 0 and row["semantic"] for row in selected),
                           teacher_posts=sum(row["posts"] for row in selected),
                           teacher_tokens=sum(row["tokens"] for row in selected),
                           teacher_seconds=sum(row.get("seconds", row.get("actor_seconds", 0.0)) for row in selected)))
    return points


def recovery_auc(rows, scores):
    positives = [scores[i] for i, row in rows.items() if not row["before"] and row["utility"] == 1]
    negatives = [scores[i] for i, row in rows.items() if not row["before"] and row["utility"] == 0]
    assert positives and negatives
    return sum((p > n) + 0.5 * (p == n) for p in positives for n in negatives) / (len(positives) * len(negatives))


def recovery_auc_difference(rows, first, second):
    """Paired bootstrap on wrong tasks, resampling recoverable/unrecoverable strata."""
    import numpy as np

    positives = [i for i, row in rows.items() if not row["before"] and row["utility"] == 1]
    negatives = [i for i, row in rows.items() if not row["before"] and row["utility"] == 0]

    def wins(scores):
        p = np.asarray([scores[i] for i in positives])
        n = np.asarray([scores[i] for i in negatives])
        return (p[:, None] > n).astype(float) + 0.5 * (p[:, None] == n)

    difference = wins(first) - wins(second)
    rng = np.random.default_rng(171118)
    p = rng.integers(len(positives), size=(20000, len(positives)))
    n = rng.integers(len(negatives), size=(20000, len(negatives)))
    samples = difference[p[:, :, None], n[:, None, :]].mean(axis=(1, 2))
    return dict(delta=float(difference.mean()), interval=np.quantile(samples, [0.025, 0.975]).tolist())


def report(arms):
    """Compare frozen predictions with cached teacher/controller outcomes only after inference."""
    base = LEGACY.parent
    forward = base / "forward_sources57_v1"
    source_panels = (
        ("DEV64", (8, 18), m.read(base / "acquisition_single_state_v1/MATCHED_COMPARISON.json")["pools"]["shared_union"]["outcomes"],
         {name: m.read(base / folder / "PREDICTIONS.json")["decisions"] for name, folder in
          (("legacy_value", "acquisition_value_v1"), ("risk", "acquisition_risk_control_v1"), ("single", "acquisition_single_state_v1"))}),
        ("FORWARD57", (7, 16), m.read(forward / "COMPARISON.json")["outcomes"],
         {name: m.read(forward / (variant + "_PREDICTIONS.json"))["decisions"] for name, variant in
          (("legacy_value", "value"), ("risk", "risk"), ("single", "single"))}),
    )
    panels_report = {}
    for panel, budgets, outcomes, old in source_panels:
        rows = {row["index"]: row for row in outcomes}
        assert len(rows) in (64, 57)
        assert [row["index"] for row in outcomes] == list(range(len(rows)))
        predictions = {arm: m.read(RUN / arm / (panel + "_PREDICTIONS.json")) for arm in arms}
        for run in predictions.values():
            assert set(row["index"] for row in run["decisions"]) == set(rows)
            assert len(run["decisions"]) == run["forward_calls"] == len(rows)
            assert run["http_posts"] == run["generated_tokens"] == 0
            assert [row["id"] for row in run["decisions"]] == [row["id"] for row in old["legacy_value"]]
        orders = {name: order_by_score(data) for name, data in old.items()}
        for arm, run in predictions.items():
            orders[arm] = order_by_score(run["decisions"])
            orders[arm + "_risk_only"] = [
                r["index"] for r in sorted(run["decisions"], key=lambda row: (-row["risk"], row["index"]))
            ]
        curves = {name: outcome_curve(rows, order) for name, order in orders.items()}
        local = sum(row["before"] for row in rows.values())
        net = sum(row["utility"] for row in rows.values())
        curves["random_expectation"] = [dict(K=k, success=local + k * net / len(rows))
                                        for k in range(len(rows) + 1)]
        score_fields = {
            "legacy_value_P_B": {r["index"]: r["probabilities"]["B"] for r in old["legacy_value"]},
            "legacy_value_P_B_minus_P_A": {r["index"]: r["score"] for r in old["legacy_value"]},
            "risk": {r["index"]: r["score"] for r in old["risk"]},
        }
        for arm, run in predictions.items():
            for field in ("score", "risk", "recoverability"):
                score_fields[arm + "_" + field] = {r["index"]: r[field] for r in run["decisions"]}
            score_fields[arm + "_P_B"] = {r["index"]: r["probabilities"]["recover"] for r in run["decisions"]}
        auc = {name: recovery_auc(rows, scores) for name, scores in score_fields.items()}
        auc_pairs = [(arm + "_recoverability", "legacy_value_P_B_minus_P_A") for arm in arms]
        if set(arms) == set(ARMS):
            auc_pairs.append(("full_recoverability", "static_recoverability"))
        auc_comparisons = {first + "_minus_" + second: recovery_auc_difference(rows, score_fields[first], score_fields[second])
                           for first, second in auc_pairs}
        comparisons = {}
        for k in budgets:
            fixed = {}
            for name, order in orders.items():
                choices = set(order[:k])
                fixed[name] = [int(row["before"]) + (row["utility"] if i in choices else 0)
                               for i, row in rows.items()]
                assert sum(fixed[name]) == curves[name][k]["success"]
            pairs = [(arm, reference) for arm in arms for reference in ("legacy_value", "risk", arm + "_risk_only")]
            if set(arms) == set(ARMS):
                pairs.append(("full", "static"))
            comparisons[str(k)] = {arm + "_minus_" + reference: compare_pair(fixed[arm], fixed[reference], 171118)
                                    for arm, reference in pairs}
        panels_report[panel] = dict(
            budgets=budgets, local_success=local, oracle_rescues=sum(r["utility"] == 1 for r in rows.values()),
            local_wrong=sum(not r["before"] for r in rows.values()), recovery_auc=auc, paired_auc=auc_comparisons,
            curves=curves, paired_comparisons=comparisons,
            classifier_cost={arm: {key: run[key] for key in ("forward_calls", "input_tokens", "seconds")}
                             for arm, run in predictions.items()}
        )
    suffix = "_".join(arms)
    m.study.new(RUN / ("MATCHED_" + suffix.upper() + ".json"),
                dict(status="RETURNED", panels=panels_report, new_http_posts=0,
                     paired_accuracy_interval_scope="Task resampling with realized fixed-budget selections held fixed."))
    brief = {panel: dict(auc=details["recovery_auc"], local_wrong=details["local_wrong"],
                         oracle_rescues=details["oracle_rescues"],
                         success={str(k): {name: points[k]["success"] for name, points in details["curves"].items()}
                                  for k in details["budgets"]})
             for panel, details in panels_report.items()}
    print(json.dumps(brief), flush=True)


def run_series():
    assert (RUN / "LABEL_CENSUS.json").is_file()
    state = dict(status="RUNNING", pid=os.getpid(), phase="RELEASE_MODEL_SERVICE")
    m.study.new(RUN / "SERIES_LIVE.json", state)
    unloaded = False
    child = None
    try:
        unloaded = patch.stop27()
        for arm in ARMS:
            for phase in ("train", "predict"):
                with (RUN / arm / (phase + ".log")).open("xb") as log:
                    child = subprocess.Popen(
                        [sys.executable, "-u", "-B", __file__, phase, "--arm", arm],
                        cwd=patch.repo, stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT
                    )
                    state.update(arm=arm, phase=phase, child_pid=child.pid)
                    m.study.publish(RUN / "SERIES_LIVE.json", state)
                    print(json.dumps(state), flush=True)
                    code = child.wait(timeout=7800 if phase == "train" else 1800)
                if code:
                    raise RuntimeError(f"{arm} {phase} failed with exit {code}")
        state.update(status="RETURNED", phase="COMPLETE")
    except BaseException:
        state.update(status="FAILED", error=traceback.format_exc())
        raise
    finally:
        if child is not None and child.poll() is None:
            child.terminate()
            try:
                child.wait(timeout=30)
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait()
        if unloaded:
            try:
                state["restoration"] = patch.restore27()
            except Exception:
                state["restoration_error"] = traceback.format_exc()
        m.study.publish(RUN / "SERIES_LIVE.json", state)
        m.study.new(RUN / "SERIES_RESULT.json", state)
        print(json.dumps(state), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=("prepare", "series", "train", "predict", "report"))
    parser.add_argument("--arm", choices=ARMS)
    args = parser.parse_args()
    if args.phase == "prepare":
        prepare()
    elif args.phase == "series":
        run_series()
    elif args.phase == "report":
        report((args.arm,) if args.arm else ARMS)
    elif args.arm is None:
        parser.error("--arm is required for train or predict")
    elif args.phase == "train":
        patch.root = RUN / args.arm
        patch.train()
    else:
        predict(args.arm)
