"""Form witnessed scale actions on TRAIN and score fixed-program comparisons."""
from __future__ import annotations

import argparse
from functools import lru_cache
import importlib.util
import json
from pathlib import Path
import re

import tatqa_correction as task

KEEP = "KEEP"
SCALES = task.SCALES
COHORTS = {"development32": "flat_dsl_transfer_v1",
           "forward32": "flat_dsl_forward_v1",
           "disclosure48": "disclosure_paired48_v1"}
MAGNITUDE = re.compile(r"\b(?:in\s+)?(?:us\s*dollars?\s+|usd\s+|eur\s+|gbp\s+|[$€£]\s*)?"
                       r"(thousand|million|billion)s?\b", re.I)
HEADER_MAGNITUDE = re.compile(r"\bin\s+(?:(?:us\s+dollars?|usd|eur|gbp|[$€£])\s+)?"
                              r"(thousand|million|billion)s?\b", re.I)
ADDITIVE = {"add", "subtract", "table_sum", "table_average", "table_min", "table_max"}


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path, value):
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def write_rows(path, rows):
    with path.open("x", encoding="utf-8") as stream:
        for row in rows:
            stream.write(json.dumps(row, ensure_ascii=False) + "\n")


@lru_cache(maxsize=1)
def percent_rule(base):
    script = base / "TATQA_MANUSCRIPT_FOLLOWUP.py"
    spec = importlib.util.spec_from_file_location("_c3_percent_rule", script)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load the fixed percent control from {script}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.predicted_scale


def joint_rule(case, base):
    candidate = case["submission"]
    if not case["normal"] or not case["valid"] or not candidate or candidate["scale"]:
        return candidate
    public = case["public"]
    proposed = percent_rule(base)(candidate, public["question"], "structured")
    if proposed["scale"]:
        return proposed
    table_scales = {
        match.group(1).lower()
        for row in public["table"]
        for cell in row
        for match in HEADER_MAGNITUDE.finditer(str(cell))
    }
    question_scales = {match.group(1).lower() for match in MAGNITUDE.finditer(public["question"])}
    if len(table_scales) != 1 or (question_scales and question_scales != table_scales):
        return candidate
    steps = task.arithmetic.executor().parse_program(candidate["program"])
    if not all(step.op in ADDITIVE for step in steps):
        return candidate
    return {**candidate, "scale": next(iter(table_scales))}


def cases(panel, receipt=None):
    plan = read(panel / "PLAN.json")
    labels = {row["index"]: row for row in read(panel / "LABELS_PRIVATE.json")}
    rows = read((receipt or panel) / "LOCAL_RESULT.json")["arms"]["paired"]
    if len({row["index"] for row in rows}) != len(rows):
        raise ValueError("duplicate paired receipts")
    for row in sorted(rows, key=lambda item: item["index"]):
        index = row["index"]
        label = labels[index]
        folder = panel / "firstpass" / f"{index:03d}" / "inputs"
        public = read(folder / "public.json")
        if row["id"] != public["id"] or row["id"] != label["id"]:
            raise ValueError("outcome, public input and private label differ")
        yield {**row, "public": public, "gold": label["exe_ans"], "metric_dir": plan["metric_dir"]}


def grade(case, candidate):
    if not case["normal"]:
        return False
    return bool(task.grade(candidate, case["public"], case["gold"],
                           metric_dir=case["metric_dir"])["execution_correct"])


def example(case, source, scale):
    public = case["public"]
    program = case["submission"]["program"]
    execution = task.execute_public(program, public, scale)
    # The actor sees reported quantities and scale, never the official label.
    evidence = {
        "question": public["question"],
        "program": program,
        "execution": execution,
        "table": public["table"],
        "paragraphs": public["pre_text"],
    }
    return {"source": source, "scale": scale, "text": json.dumps(evidence, ensure_ascii=False)}


def training_pair(case):
    """Contrast a passing and failing public state holding the program fixed."""
    candidate = case["submission"]
    if not case["normal"] or not case["valid"] or not candidate:
        return [], "no_valid_submission"
    actual = candidate["scale"]
    passed = [scale for scale in SCALES if grade(case, {**candidate, "scale": scale})]
    failed = [scale for scale in SCALES if scale not in passed]
    if not passed or not failed:
        return [], "no_scale_contrast"
    gold = case["gold"]["scale"]
    good = actual if actual in passed else gold if gold in passed else passed[0]
    if actual in failed:
        bad = actual
    elif actual == "" and "percent" in failed:
        bad = "percent"
    else:
        bad = failed[0]
    source = case["public"]["report"].split("/", 1)[1]
    preserve = example(case, source, good)
    preserve.update(ordinary=gold, paired=KEEP, negative=bad)
    repair = example(case, source, bad)
    repair.update(ordinary=gold, paired=good, negative=bad)
    return [preserve, repair], "actual_pass" if actual in passed else "actual_failure"


def make_training(root, count):
    panel = root / "train"
    plan = read(panel / "PLAN.json")
    if plan["source_split"] != "train" or count not in plan["prefixes"]:
        raise ValueError("formation requires an official TRAIN prefix")
    frozen = plan["episodes"][:count]
    rows, outcomes, eligible = [], {}, []
    actual_indices = set()
    for end in plan["prefixes"]:
        if end > count:
            break
        for case in cases(panel, panel / f"through_{end:03d}"):
            index = case["index"]
            if index in actual_indices or case["id"] != frozen[index]["id"]:
                raise ValueError("unexpected source in a TRAIN receipt")
            actual_indices.add(index)
            pair, kind = training_pair(case)
            rows.extend(pair)
            outcomes[kind] = outcomes.get(kind, 0) + 1
            if pair:
                eligible.append(index)
    if actual_indices != set(range(count)):
        raise ValueError("missing TRAIN executions")
    tag = f"{count:03d}"
    write_rows(root / f"TRAIN_{tag}.jsonl", rows)
    # Record the entire attempted denominator, including irreparable programs.
    summary = {"attempted_tables": count, "eligible_tables": len(eligible),
               "states": len(rows), "outcomes": outcomes,
               "alternate_correct_keep": sum(row["paired"] == KEEP and row["scale"] != row["ordinary"] for row in rows),
               "campus_posts": 0}
    write_json(root / f"FORMATION_{tag}.json", summary)
    print(json.dumps(summary), flush=True)


def all_panels(root, include_confirmation):
    panels = {key: root.parent / value for key, value in COHORTS.items()}
    if include_confirmation:
        panels["confirmation64"] = root / "confirmation"
    return panels


def make_inference(root, include_confirmation):
    rows = []
    for name, panel in all_panels(root, include_confirmation).items():
        for case in cases(panel):
            if case["valid"] and case["normal"] and case["submission"]:
                rows.append(example(case, f"{name}:{case['index']}", case["submission"]["scale"]))
    path = root / ("INFERENCE_ALL.jsonl" if include_confirmation else "INFERENCE_OLD.jsonl")
    write_rows(path, rows)
    print(json.dumps({"prediction_rows": len(rows), "path": str(path)}), flush=True)


def apply_action(candidate, action):
    if action == KEEP:
        return candidate
    if not candidate or action not in SCALES:
        raise ValueError(f"invalid scale adaptation action {action!r}")
    return {**candidate, "scale": action}


def delta(before, after):
    if len(before) != len(after):
        raise ValueError("misaligned panels")
    aligned = list(zip(before, after, strict=True))
    return {"n": len(aligned), "success": sum(after),
            "recovered": sum(not a and b for a, b in aligned),
            "harmed": sum(a and not b for a, b in aligned)}


def score(root, predictions, output, include_confirmation, prefix):
    data = read(predictions)
    decisions = {row["source"]: row["actions"] for row in data["rows"]}
    if len(decisions) != len(data["rows"]):
        raise ValueError("duplicate prediction sources")
    results = {}
    for name, panel in all_panels(root, include_confirmation).items():
        rows = list(cases(panel))
        if not rows:
            raise ValueError(f"empty panel {name}")
        baseline = [row["success"] for row in rows]
        outputs = []
        for case in rows:
            candidate = case["submission"]
            methods = {"raw": candidate, "joint": joint_rule(case, root.parent)}
            arms = ["ordinary", "paired"]
            if "replay" in next(iter(decisions.values())):
                arms.append("replay")
            for arm in arms:
                action = KEEP
                if case["valid"] and case["normal"]:
                    key = f"{arm}-{prefix}" if prefix and arm != "replay" else arm
                    action = decisions[f"{name}:{case['index']}"][key]["action"]
                methods[arm] = apply_action(candidate, action)
            correct = {arm: grade(case, submission) for arm, submission in methods.items()}
            if correct["raw"] != case["success"]:
                raise ValueError(f"saved original score differs in {name} {case['index']}")
            outputs.append({"index": case["index"], "submissions": methods, "correct": correct})
        vectors = {arm: [row["correct"][arm] for row in outputs] for arm in outputs[0]["correct"]}
        means = {arm: delta(baseline, vector) for arm, vector in vectors.items()}
        versus = {arm: delta(vectors[arm], vectors["paired"]) for arm in ("joint", "ordinary")}
        gate = min(means["paired"]["success"] - means[arm]["success"] for arm in versus) >= 3
        results[name] = {"scores": means, "paired_versus": versus,
                         "stage_b_gate": gate and name == "confirmation64", "rows": outputs}
    write_json(output, results)
    print(json.dumps({name: {k: v for k, v in result.items() if k != "rows"}
                      for name, result in results.items()}), flush=True)


def confirm_rule(root):
    for name, panel in all_panels(root, False).items():
        rows = list(cases(panel))
        result = delta([row["success"] for row in rows], [grade(row, joint_rule(row, root.parent)) for row in rows])
        print(json.dumps({"panel": name, **result}), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path)
    commands = parser.add_subparsers(dest="mode", required=True)
    commands.add_parser("rule")
    train = commands.add_parser("prepare-train")
    train.add_argument("--count", required=True, type=int, choices=(32, 64, 96))
    inputs = commands.add_parser("prepare-inference")
    inputs.add_argument("--include-confirmation", action="store_true")
    scoring = commands.add_parser("score")
    scoring.add_argument("--predictions", type=Path, required=True)
    scoring.add_argument("--out", type=Path, required=True)
    scoring.add_argument("--include-confirmation", action="store_true")
    scoring.add_argument("--prefix", choices=("032", "064", "096"))
    args = parser.parse_args()
    if args.mode == "rule":
        confirm_rule(args.root)
    elif args.mode == "prepare-train":
        make_training(args.root, args.count)
    elif args.mode == "prepare-inference":
        make_inference(args.root, args.include_confirmation)
    else:
        score(args.root, args.predictions, args.out, args.include_confirmation, args.prefix)


if __name__ == "__main__":
    main()
