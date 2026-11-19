"""Score the prospective K6/K9 comparison from the completed private receipts."""
from __future__ import annotations

import json

import tatqa_scale_study as study
import tatqa_scale_training as training
import tatqa_teacher_scale as replay
import tatqa_teacher_scale_confirm_teacher as trial


def readout(path):
    payload = study.read(path)
    rows = {row["source"]: row for row in payload["rows"]}
    if len(rows) != len(payload["rows"]):
        raise ValueError("duplicate predictions")
    return rows, payload["counts"]


def candidate(row, data):
    submission = row["submission"]
    if not row["valid"] or not row["normal"] or not submission:
        return submission
    prediction = data[f"confirmation32:{row['index']}"]
    if prediction["scale"] != submission["scale"]:
        raise ValueError("readout was computed from a different candidate scale")
    return study.apply_action(submission, prediction["actions"][replay.ARM]["action"])


def collect(teachers, local_readouts, teacher_readouts):
    records = []
    for case in study.cases(trial.PANEL):
        local = candidate(case, local_readouts)
        if study.grade(case, case["submission"]) != case["success"]:
            raise ValueError("local receipt grading changed")
        local_correct = study.grade(case, local)
        row = dict(index=case["index"], local_correct=local_correct, local=local)
        teacher = teachers.get(case["index"])
        if teacher is None:
            records.append(row)
            continue
        if teacher["id"] != case["id"]:
            raise ValueError("teacher candidate source mismatch")
        actor = {**case, **teacher}
        if study.grade(actor, actor["submission"]) != teacher["success"]:
            raise ValueError("teacher receipt grading changed")
        row["teacher"] = actor
        proposed = candidate(actor, teacher_readouts)
        action = study.KEEP if proposed is None else proposed["scale"]
        variants = replay.teacher_candidates(row, action)
        results = {arm: replay.guard(row, response) for arm, response in variants.items()}
        results["oracle"] = replay.diagnostic_oracle(row, results["raw"], guard_first=True)
        records.append(dict(row, outcomes=results))
    if len(records) != 32:
        raise ValueError("report requires all 32 local tasks")
    return records


def lengths():
    inputs = trial.ROOT / "TEACHER_SCALE_INPUTS.jsonl"
    with inputs.open(encoding="utf-8") as file:
        rows = [json.loads(line) for line in file]
    if not rows:
        return {}
    tokenizer = training.load_tokenizer(training.DEFAULT_MODEL)
    return {row["source"]: len(training.encode(row, tokenizer, 6144)) for row in rows}


def score():
    fixed = trial.frozen()
    attempt = study.read(trial.POOL / "TEACHER_ATTEMPT.json")
    if attempt["freeze_sha256"] != replay.sha(trial.FREEZE):
        raise ValueError("teacher selection was not frozen before attempts")
    teacher_run = study.read(trial.POOL / "TEACHER_RESULT.json")
    if teacher_run["status"] != "RETURNED" or [r["index"] for r in teacher_run["episodes"]] != fixed["K9"]:
        raise ValueError("report requires the full frozen teacher run")
    teachers = {row["index"]: row for row in teacher_run["episodes"]}
    ledger = [row for row in study.read(trial.POOL / "teacher_budget/gateway_ledger.json")
              if row["state"] != "not_sent"]
    if (any(row["state"] != "complete" for row in ledger) or len(ledger) != teacher_run["posts"]
            or sum(row["usage"]["total_tokens"] for row in ledger) != teacher_run["known_tokens"]
            or sum(row["tokens"] for row in teachers.values()) != teacher_run["known_tokens"]
            or sum(row["posts"] for row in teachers.values()) != teacher_run["posts"]
            or teacher_run["known_tokens"] > fixed["token_cap"]):
        raise ValueError("physical teacher cost does not reconcile")
    lp, lc = readout(trial.ROOT / "LOCAL_SCALE_PREDICTIONS.json")
    tp, tc = readout(trial.ROOT / "TEACHER_SCALE_PREDICTIONS.json")
    input_lengths = lengths()
    if set(input_lengths) != set(tp) or sum(input_lengths.values()) != tc["input_tokens"]:
        raise ValueError("teacher prefill accounting does not reconcile")
    rows = collect(teachers, lp, tp)
    local = [row["local_correct"] for row in rows]
    budget_scores, metrics, costs = {}, {}, {}
    for name in ("K6", "K9"):
        group = fixed[name]
        budget_scores[name] = {arm: [row["outcomes"][arm] if row["index"] in group else row["local_correct"]
                                     for row in rows] for arm in replay.METHODS}
        outcomes = budget_scores[name]
        raw = outcomes["raw"]
        metrics[name] = {arm: dict(vs_local=study.delta(local, data), vs_same_k_raw=study.delta(raw, data))
                         for arm, data in outcomes.items()}
        prompts = [input_lengths.get(f"confirmation32:{i}", 0) for i in group]
        costs[name] = dict(tasks=len(group), teacher_posts=sum(teachers[i]["posts"] for i in group),
                           teacher_tokens=sum(teachers[i]["tokens"] for i in group),
                           teacher_native_success=sum(teachers[i]["success"] for i in group),
                           teacher_valid=sum(bool(teachers[i]["normal"] and teachers[i]["valid"]) for i in group),
                           scale_inputs=sum(bool(length) for length in prompts), scale_input_tokens=sum(prompts))
    local_run = study.read(trial.PANEL / "LOCAL_RESULT.json")
    primary = study.delta(budget_scores["K9"]["raw"], budget_scores["K6"]["pair128"])
    result = dict(primary_vs_k9_raw=primary, n=len(local), local_pair128=sum(local), budgets=metrics, costs=costs,
                  local_native={arm: {key: sum(row[key] for row in arm_rows)
                                      for key in ("posts", "tokens", "unknown", "seconds", "success", "valid")}
                                for arm, arm_rows in local_run["arms"].items()},
                  local_scale=lc, teacher_scale_physical=tc,
                  risk=study.read(trial.ROOT / "RISK_ORDER.json")["cost"],
                  teacher_physical={key: teacher_run[key] for key in ("posts", "known_tokens", "unknown", "seconds")},
                  frozen_sha256=replay.sha(trial.FREEZE))
    study.write_json(trial.ROOT / "RESULT.json", result)
    print(json.dumps(result), flush=True)


if __name__ == "__main__":
    score()
