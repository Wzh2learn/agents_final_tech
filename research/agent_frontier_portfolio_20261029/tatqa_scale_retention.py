"""Prepare and score source retention on the frozen, exposed FinQA DEV64."""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path


ARM = "tatqa_scale_adapter"
REFERENCE_ARM = "paired_state_branch"
PINNED = "TATQA_SCALE_ADAPTER_PINNED"
RETURNED = "TATQA_SCALE_FINQA_DEV64_RETURNED"
ADAPTER_FILES = ("adapter_config.json", "adapter_model.safetensors")
REPLAY_FIELDS = ("input_ids", "labels", "prompt_token_count", "supervised_tokens", "sequence_length")


def runtime():
    import finqa_state_learning as state
    import run_finqa_learning_native as native

    return state.PAIRED_STATES, native


def private_path(path, native):
    root = native.study.PRIVATE.resolve()
    resolved = path.resolve()
    if not resolved.is_relative_to(root) or any("confirmation" in part.lower() for part in resolved.parts):
        raise ValueError("use an unsealed path under the private research evidence root")
    return resolved


def prepare_replay(out):
    paired, native = runtime()
    out = private_path(out, native)
    source = paired.parent / "teacher_expansion_clean_v3"
    plan = native.read(source / "PLAN.json")
    data_path = source / "DATA.json"
    if native.sha(data_path) != plan["data_sha256"]:
        raise ValueError("FinQA TRAIN replay data changed")
    rows = native.read(data_path)["rows"]
    indices = plan["paired_rows"]
    if len(indices) != 121 or sorted(i for group in indices for i in group) != list(range(195)) or len(rows) != 195:
        raise ValueError("expected 121 frozen FinQA TRAIN groups and 195 targets")
    groups = [[{key: rows[i][key] for key in REPLAY_FIELDS} for i in group] for group in indices]
    for group in groups:
        if len(group) not in (1, 2):
            raise ValueError("unexpected replay group shape")
        for row in group:
            if not (len(row["input_ids"]) == len(row["labels"]) == row["sequence_length"]
                    and sum(token != -100 for token in row["labels"]) == row["supervised_tokens"] > 0):
                raise ValueError("invalid replay target mask")
    native.study.new(out, dict(groups=groups, group_count=121, targets=195,
                               source_plan_sha256=native.sha(source / "PLAN.json"),
                               source_data_sha256=plan["data_sha256"],
                               scope="Existing FinQA TRAIN replay only"))
    print(f"{out}  121 TRAIN groups / 195 targets")


def episode_map(items):
    rows = {(item["index"], item["id"]): item for item in items}
    if len(items) != 64 or len(rows) != 64 or {index for index, _ in rows} != set(range(64)):
        raise ValueError("expected all 64 frozen FinQA DEV episodes")
    return rows


def frozen_components(plan, native):
    project = Path(__file__).resolve().parents[2]
    runtime_project = Path(native.__file__).resolve().parents[2]
    components = {}
    for name, digest in plan["components"].items():
        path = Path(name)
        if path.is_relative_to(project):
            path = runtime_project / path.relative_to(project)
        if native.sha(path) != digest:
            raise ValueError(f"DEV64 runtime component changed: {path}. Use --frozen-code.")
        components[str(path)] = digest
    return components


def prepare_regression(out, adapter):
    paired, native = runtime()
    out, adapter = (private_path(path, native) for path in (out, adapter))
    source = paired / "native_v1"
    plan = native.read(source / "PLAN.json")
    reference = native.read(source / "RESULT.json")
    if reference["plan_sha256"] != native.sha(source / "PLAN.json") or reference["status"] != plan["terminal_status"]:
        raise ValueError("frozen FinQA DEV64 reference did not close under its plan")
    originals = episode_map(plan["source_episodes"])
    templates = episode_map([row for row in plan["episodes"] if row["arm"] == REFERENCE_ARM])
    outcomes = episode_map([row for row in reference["episodes"] if row["arm"] == REFERENCE_ARM])
    if originals.keys() != templates.keys() or originals.keys() != outcomes.keys():
        raise ValueError("DEV64 reference episodes differ")
    if sum(row["native_success"] for row in outcomes.values()) != 37:
        raise ValueError("DEV64 reference is not the frozen Pair37 result")
    components = frozen_components(plan, native)

    config = native.read(adapter / "adapter_config.json")
    pair_config = native.read(paired / REFERENCE_ARM / "adapter_config.json")
    for key in ("base_model_name_or_path", "r", "lora_alpha", "peft_type", "task_type"):
        if config[key] != pair_config[key]:
            raise ValueError(f"candidate adapter differs from the frozen base in {key}")
    if set(config["target_modules"]) != set(pair_config["target_modules"]):
        raise ValueError("candidate adapter target modules differ from frozen Pair37")
    adapter_hashes = {name: native.sha(adapter / name) for name in ADAPTER_FILES}

    labels = source / "LABELS_PRIVATE.json"
    if native.sha(labels) != plan["private_labels_sha256"]:
        raise ValueError("frozen DEV64 scorer labels changed")
    for key, current in originals.items():
        initial = Path(current["folder"])
        prior = Path(templates[key]["folder"])
        if (native.sha(initial / "inputs/public.json") != templates[key]["public_sha256"]
                or native.sha(prior / "inputs/task.txt") != templates[key]["task_sha256"]):
            raise ValueError(f"frozen DEV64 public input changed at index {key[0]}")

    out.mkdir(mode=0o700)
    training = out / "checkpoint"
    pinned = training / ARM
    pinned.mkdir(parents=True, mode=0o700)
    for name, digest in adapter_hashes.items():
        shutil.copyfile(adapter / name, pinned / name)
        if native.sha(pinned / name) != digest:
            raise ValueError("candidate adapter changed during pinning")
    native.study.new(training / "RESULT.json", dict(status=PINNED, adapter=str(adapter),
                                                    arms={ARM: dict(adapter_files=adapter_hashes)}))

    episodes = []
    for key, current in originals.items():
        template = templates[key]
        initial, prior = Path(current["folder"]), Path(template["folder"])
        packet = out / ARM / f"{key[0]:03d}"
        packet.mkdir(parents=True)
        shutil.copytree(initial / "inputs", packet / "inputs")
        shutil.copytree(initial / "work", packet / "work")
        shutil.copyfile(prior / "inputs/task.txt", packet / "inputs/task.txt")
        (packet / "dependencies").mkdir()
        episodes.append(dict(template, arm=ARM, folder=str(packet)))

    shutil.copyfile(labels, out / "LABELS_PRIVATE.json")
    for key in ("training_plan_sha256", "protocol_path", "protocol_sha256"):
        plan.pop(key, None)
    plan.update(episodes=episodes, arms=[ARM], arm_order=[ARM], components=components, training_root=str(training),
                training_result_sha256=native.sha(training / "RESULT.json"), required_training_status=PINNED,
                terminal_status=RETURNED, max_posts=64 * plan["caps"]["posts"], scope="Exposed FinQA DEV64",
                baseline=str(source / "RESULT.json"), baseline_sha256=native.sha(source / "RESULT.json"),
                baseline_plan_sha256=native.sha(source / "PLAN.json"))
    native.study.new(out / "PLAN.json", plan)
    print(f"{out}  FinQA DEV64 frozen against Pair37")


def run_regression(out):
    paired, native = runtime()
    out = private_path(out, native)
    plan = native.read(out / "PLAN.json")
    if (plan["scope"], plan["arms"], plan["required_training_status"]) != ("Exposed FinQA DEV64", [ARM], PINNED):
        raise ValueError("expected the prepared DEV64 source-retention plan")
    source = paired / "native_v1/PLAN.json"
    reference = native.read(source)
    if (plan["baseline_plan_sha256"] != native.sha(source)
            or plan["source_episodes"] != reference["source_episodes"]
            or plan["components"] != frozen_components(reference, native)
            or Path(plan["training_root"]) != out / "checkpoint"):
        raise ValueError("DEV64 source or frozen runtime binding changed")
    native.study.CAPS.clear()
    native.study.CAPS.update(plan["caps"])
    native.run(native.sha(out / "PLAN.json"), out)


def score_regression(out):
    paired, native = runtime()
    out = private_path(out, native)
    plan = native.read(out / "PLAN.json")
    baseline = paired / "native_v1/RESULT.json"
    if Path(plan["baseline"]) != baseline or native.sha(baseline) != plan["baseline_sha256"]:
        raise ValueError("frozen FinQA DEV64 reference changed")
    result = native.read(out / "RESULT.json")
    if result["status"] != RETURNED or result["plan_sha256"] != native.sha(out / "PLAN.json"):
        raise ValueError("DEV64 native batch did not close under the prepared plan")
    reference = episode_map([row for row in native.read(baseline)["episodes"] if row["arm"] == REFERENCE_ARM])
    outcomes = episode_map([row for row in result["episodes"] if row["arm"] == ARM])
    if reference.keys() != outcomes.keys():
        raise ValueError("DEV64 paired episode identity mismatch")
    recovered, damaged, retained = [], [], []
    for key, row in outcomes.items():
        old, new = reference[key]["native_success"], row["native_success"]
        if old and new:
            retained.append(key[0])
        elif new:
            recovered.append(key[0])
        elif old:
            damaged.append(key[0])
    report = dict(reference_success=sum(row["native_success"] for row in reference.values()),
                  candidate_success=sum(row["native_success"] for row in outcomes.values()), total=64,
                  retained=len(retained), recovered=len(recovered), damaged=len(damaged),
                  recovered_indices=recovered, damaged_indices=damaged,
                  posts=sum(row["accounting"]["actual_forwarded_posts"] for row in outcomes.values()),
                  known_tokens=sum(row["accounting"]["provider_total_tokens_known"] for row in outcomes.values()),
                  unknown_requests=sum(len(row["accounting"]["unknown_usage_requests"]) for row in outcomes.values()),
                  candidate_adapter_sha256=native.sha(out / "checkpoint" / ARM / "adapter_model.safetensors"),
                  reference_sha256=plan["baseline_sha256"], result_sha256=native.sha(out / "RESULT.json"))
    native.study.new(out / "RETENTION.json", report)
    print(f"FinQA DEV64 {report['reference_success']} -> {report['candidate_success']}/64 "
          f"R/H {report['recovered']}/{report['damaged']}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    subcommands = parser.add_subparsers(dest="command", required=True)
    for command in ("prepare-replay", "prepare-regression", "run-regression", "score-regression"):
        subparser = subcommands.add_parser(command)
        subparser.add_argument("--out", type=Path, required=True)
        if command in ("prepare-regression", "run-regression"):
            subparser.add_argument("--frozen-code", type=Path, required=True)
        if command == "prepare-regression":
            subparser.add_argument("--adapter", type=Path, required=True)
    args = parser.parse_args()
    if getattr(args, "frozen_code", None) is not None:
        frozen = args.frozen_code.resolve(strict=True)
        module_root = frozen / "research/agent_frontier_portfolio_20261029"
        if not (module_root / "run_finqa_learning_native.py").is_file():
            raise ValueError("expected the existing frozen FinQA code checkout")
        sys.path[:0] = [str(module_root), str(frozen)]
    if args.command == "prepare-regression":
        prepare_regression(args.out, args.adapter)
    else:
        commands = {"prepare-replay": prepare_replay, "run-regression": run_regression, "score-regression": score_regression}
        commands[args.command](args.out)


if __name__ == "__main__":
    main()
