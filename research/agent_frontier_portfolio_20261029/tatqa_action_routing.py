"""Estimate local and teacher action utility from matched TAT-QA receipts."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import numpy as np

import tatqa_scale_study as study
import tatqa_transfer as transfer


COHORTS = ("development32", "forward32")
QUOTAS = (4, 9)
YEAR = re.compile(r"\b(?:19|20)\d{2}\b")


def indexed(rows):
    result = {row["index"]: row for row in rows}
    if set(result) != set(range(32)) or len(rows) != 32:
        raise ValueError("expected a complete 32-table development cohort")
    return result


def teacher_adopted(local, teacher):
    proposal = teacher["submission"]
    if not teacher["normal"] or not teacher["valid"] or not proposal:
        return False
    return not (
        local
        and local["scale"] == proposal["scale"]
        and transfer.av.percent_scale_only(local["program"], proposal["program"])
    )


def action_outcomes(raw, adapted, labels, teacher):
    return (
        labels["raw"], labels["paired"],
        teacher["success"] if teacher_adopted(raw, teacher) else labels["raw"],
        teacher["success"] if teacher_adopted(adapted, teacher) else labels["paired"],
    )


def repeated_t0(base, original, plan, i):
    """Load a second realized outcome for the unchanged T0 request setup."""
    root = base / "state_aware_teacher_v1"
    packet = transfer.packet_at(root, "T0", i)
    first = transfer.packet_at(original, "teacher", i)
    for name in ("task.txt", "public.json", "opencode.json"):
        if (packet / "inputs" / name).read_bytes() != (first / "inputs" / name).read_bytes():
            raise ValueError("historical repeated teacher inputs differ")
    result = study.read(packet / "RESULT.json")
    if result["id"] != plan["id"] or not result["accounting"]["integrity_passed"]:
        raise ValueError("historical repeat lacks a matched native result")
    candidate = packet / "work/candidate.json"
    return dict(success=result["native_success"], valid=result["program_valid"],
                normal=result["agent_completed"], submission=study.read(candidate) if candidate.exists() else None,
                tokens=result["accounting"]["provider_total_tokens_known"])


def features(public, local, proposal, logits, risk, value):
    question = public["question"]
    has_change = local != proposal
    margin = 0.0
    if has_change and local and proposal and logits is not None:
        margin = logits[proposal["scale"]] - max(logits[study.KEEP], logits[local["scale"]])
    return (
        risk,
        value,
        float(bool(local)),
        float(has_change),
        np.clip(margin, -8.0, 8.0),
        float(bool(study.MAGNITUDE.search(question))),
        float(bool(re.search(r"percent|percentage|%", question, flags=re.I))),
        float(len(set(YEAR.findall(question)))),
    )


def load_cohort(base, scale, predictions, name):
    folder = base / study.COHORTS[name]
    plan = indexed(study.read(folder / "PLAN.json")["episodes"])
    locals_ = indexed(study.read(folder / "LOCAL_RESULT.json")["arms"]["paired"])
    teacher_result = study.read(folder / "TEACHER_RESULT.json")
    if teacher_result["status"] != "RETURNED" or teacher_result["unknown"]:
        raise ValueError("complete teacher candidates with measured costs are required")
    teachers = indexed(teacher_result["episodes"])
    risk = indexed(study.read(folder / "risk_PREDICTIONS.json")["decisions"])
    value = indexed(study.read(folder / "value_PREDICTIONS.json")["decisions"])
    scores = indexed(scale[name]["rows"])
    rows = []
    for i, record in plan.items():
        public = study.read(transfer.packet_at(folder, "firstpass", i) / "inputs/public.json")
        if any(record["id"] != row["id"] for row in
               (public, locals_[i], teachers[i], risk[i], value[i])):
            raise ValueError("public and native source identities disagree")
        score = scores[i]
        before, proposed = (score["submissions"][arm] for arm in ("raw", "paired"))
        for arm in ("raw", "paired", "joint"):
            if type(score["correct"][arm]) is not bool:
                raise ValueError("counterfactual action requires an official boolean grade")
        labels = score["correct"]
        teacher = teachers[i]
        if labels["raw"] != locals_[i]["success"] or before != locals_[i]["submission"]:
            raise ValueError("raw Pair participant mismatch")
        arms = action_outcomes(before, proposed, labels, teacher)
        logits = predictions.get(f"{name}:{i}")
        rows.append(dict(
            index=i, features=features(public, before, proposed, logits, risk[i]["score"], value[i]["score"]),
            outcomes=arms, risk=risk[i]["score"], value=value[i]["score"], joint=labels["joint"],
            joint_guide=teacher["success"] if teacher_adopted(score["submissions"]["joint"], teacher)
            else labels["joint"],
            tokens=teacher["tokens"], posts=teacher["posts"],
        ))
        if name == "development32":
            repeated = repeated_t0(base, folder, record, i)
            rows[-1]["repeat_outcomes"] = action_outcomes(before, proposed, labels, repeated)
            rows[-1]["repeat_tokens"] = repeated["tokens"]
    return rows


def estimate(train, held, *, repeat=False):
    """Fit fixed ridge models using the other table cohort."""
    x = np.asarray([row["features"] for row in train])
    z = np.asarray([row["features"] for row in held])
    mu, sigma = x.mean(0), np.maximum(x.std(0), 0.1)
    x = np.c_[np.ones(len(x)), (x - mu) / sigma]
    z = np.c_[np.ones(len(z)), (z - mu) / sigma]
    y = np.asarray([row["outcomes"] for row in train], dtype=float)
    if repeat:
        repeated = np.asarray([row["repeat_outcomes"] for row in train], dtype=float)
        y = 0.5 * (y + repeated)
    # First fit three relative effects and leave intercepts unpenalized.
    effects = y[:, 1:] - y[:, :1]
    penalty = np.diag([0.0, *([8.0] * (x.shape[1] - 1))])
    return z @ np.linalg.solve(x.T @ x + penalty, x.T @ effects)


def report_delta(final, baseline, rows, picks=()):
    totals = study.delta(baseline, final)
    totals.update(teacher_tasks=len(picks), teacher_tokens=sum(rows[i]["tokens"] for i in picks),
                  teacher_posts=sum(rows[i]["posts"] for i in picks))
    return totals


def compare(rows, predicted):
    y = np.asarray([row["outcomes"] for row in rows], dtype=bool)
    raw, scale = y[:, 0], y[:, 1]
    learned_scale = predicted[:, 0] > 0
    local = np.where(learned_scale, scale, raw)
    net = np.where(learned_scale, predicted[:, 2] - predicted[:, 0], predicted[:, 1])
    learned_teacher = np.where(learned_scale, y[:, 3], y[:, 2])
    joint = np.asarray([row["joint"] for row in rows], dtype=bool)
    joint_teacher = np.asarray([row["joint_guide"] for row in rows], dtype=bool)
    report = {arm: report_delta(outcome.tolist(), raw.tolist(), rows) for arm, outcome in
              {"raw": raw, "pair128": scale, "joint": joint, "learned_local": local}.items()}
    report["actions"] = dict(
        scale_recovers=int((~raw & scale).sum()), scale_harms=int((raw & ~scale).sum()),
        teacher_recovers_after_scale=int((~scale & y[:, 3]).sum()),
        teacher_harms_after_scale=int((scale & ~y[:, 3]).sum()),
        teacher_after_scale_recovers_neither_local=int((~raw & ~scale & y[:, 3]).sum()),
        learned_scale_choices=int(learned_scale.sum()),
    )
    for k in QUOTAS:
        arms = {}
        for arm, local_y, teacher_y, rank in (
            ("pair128_risk", scale, y[:, 3], [row["risk"] for row in rows]),
            ("pair128_value", scale, y[:, 3], [row["value"] for row in rows]),
            ("joint_risk", joint, joint_teacher, [row["risk"] for row in rows]),
            ("learned", local, learned_teacher, net),
        ):
            picks = sorted(range(len(rows)), key=lambda i: (-rank[i], rows[i]["index"]))[:k]
            after = local_y.copy()
            after[picks] = teacher_y[picks]
            arms[arm] = report_delta(after.tolist(), raw.tolist(), rows, picks)
        report[f"K{k}"] = arms
    return report


def evidence_diagnostic(root, scale):
    """Summarize paired teacher modes before and after the cached scale action."""
    policy = study.read(root / "SELECTION.json")["episodes"]
    observed = study.read(root / "TEACHER_RESULT.json")
    if observed["status"] != "RETURNED" or len(observed["episodes"]) != 2 * len(policy):
        raise ValueError("evidence diagnostic requires complete matched teacher pairs")
    projection = {row["index"]: bool(row["locators"]) for row in study.read(root / "PROJECTION.json")}
    receipt = {(row["index"], row["arm"]): row for row in observed["episodes"]}
    rows = []
    for source in policy:
        name = {"development": "development32", "forward": "forward32"}[source["source"]]
        i = source["index"]
        row = indexed(scale[name]["rows"])[source["source_index"]]
        scores = row["correct"]
        current = row["submissions"]["paired"]
        teacher_scores = []
        for arm in ("T0", "T1"):
            before = receipt[i, arm]
            native = study.read(transfer.packet_at(root, arm, i) / "RESULT.json")
            if native["id"] != source["id"] or before["before"] != scores["raw"]:
                raise ValueError("evidence and prior local receipts disagree")
            teacher = dict(normal=native["agent_completed"], valid=native["program_valid"],
                           submission=before["proposal"], success=native["native_success"])
            teacher_scores.append(teacher["success"] if teacher_adopted(current, teacher) else scores["paired"])
        rows.append((projection[i], scores["paired"], *teacher_scores))

    def describe(cohort):
        baseline = [row[1] for row in cohort]
        t0 = [row[2] for row in cohort]
        card = [row[3] for row in cohort]
        return dict(Pair128=sum(baseline), T0=study.delta(baseline, t0),
                    evidence=study.delta(baseline, card), versus_T0=study.delta(t0, card))

    return dict(all=describe(rows), located=describe([row for row in rows if row[0]]),
                no_location=describe([row for row in rows if not row[0]]))


def run(base, output, evidence=None):
    extension = base / "scale_adaptation_c3_v1/adaptive_extension_v1"
    scale = study.read(extension / "ALL_128.json")
    predictions = {row["source"]: row["actions"]["paired-128"]["logits"]
                   for row in study.read(extension / "PREDICTIONS.json")["rows"]}
    data = {name: load_cohort(base, scale, predictions, name) for name in COHORTS}
    reports = {held: compare(data[held], estimate(data[train], data[held]))
               for train, held in (COHORTS, COHORTS[::-1])}
    train, held = data["development32"], data["forward32"]
    repeated = compare(held, estimate(train, held, repeat=True))
    variation = dict(
        n=len(train), after_scale_disagreements=sum(row["outcomes"][3] != row["repeat_outcomes"][3]
                                                  for row in train),
        raw_guard_disagreements=sum(row["outcomes"][2] != row["repeat_outcomes"][2] for row in train),
        first_tokens=sum(row["tokens"] for row in train),
        repeat_tokens=sum(row["repeat_tokens"] for row in train),
    )
    result = dict(scope="Cross-cohort reuse of exposed development panels; no new teacher calls.",
                  teacher_posts=0, reports=reports, historical_repeat=variation,
                  forward_with_repeat_supervision={f"K{k}": repeated[f"K{k}"]["learned"] for k in QUOTAS})
    if evidence is not None:
        result["evidence_after_scale"] = evidence_diagnostic(evidence, scale)
    study.write_json(output, result)
    print(json.dumps(result, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", type=Path, default=transfer.BASE)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--evidence", type=Path)
    args = parser.parse_args()
    run(args.base, args.out, args.evidence)
