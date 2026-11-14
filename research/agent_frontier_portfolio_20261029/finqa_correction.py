"""Public FinQA execution tool, private grading and one correction-weight rule.

The public tool receives question/context/table only. Gold execution answers and
teacher programs are never needed by its execution or error feedback.
"""
from __future__ import annotations

import argparse
from difflib import SequenceMatcher
import importlib.util
import json
import math
from pathlib import Path
import re
import sys


PUBLIC_KEYS = {"id", "report", "question", "pre_text", "post_text", "table"}


def executor(path=None):
    path = Path(path) if path else Path(__file__).resolve().parents[1] / "finqa_causal_exposure_20261010/executor_contract_v1/finqa_executor_contract_v1.py"
    name = "finqa_correction_executor"
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
    return sys.modules[name]


def public_record(record):
    value = {"id": record["id"], "report": record["filename"],
             "question": record["qa"]["question"], "pre_text": record["pre_text"],
             "post_text": record["post_text"], "table": record["table"]}
    check_public(value)
    return value


def check_public(value):
    if not isinstance(value, dict) or set(value) != PUBLIC_KEYS:
        raise ValueError("public record fields differ; labels/retrieval annotations are forbidden")
    if not isinstance(value["question"], str) or not isinstance(value["table"], list):
        raise ValueError("invalid public question or table")


def execute_public(program, public, module=None):
    check_public(public)
    if not isinstance(program, str) or not program.strip() or len(program) > 8192:
        return {"status": "error", "code": "PROGRAM_REQUIRED_OR_TOO_LONG"}
    module = module or executor()
    try:
        result = module.execute_program(program, public["table"])
        return {"status": "executed", **result.as_dict()}
    except module.ExecutorContractError as exc:
        return {"status": "error", "code": exc.code, "detail": exc.detail}


def canonical_answer(value):
    if isinstance(value, str) and value.lower() in ("yes", "no"):
        return value.lower()
    if isinstance(value, bool):
        raise ValueError("boolean is not a numeric execution answer")
    value = float(value)
    if not math.isfinite(value):
        raise ValueError("non-finite answer")
    return round(value, 5)


def grade(program, public, gold_execution_answer, module=None):
    execution = execute_public(program, public, module)
    valid = execution["status"] == "executed"
    correct = valid and canonical_answer(execution["terminal_execution_answer"]) == canonical_answer(gold_execution_answer)
    return {"execution_correct": correct, "program_valid": valid, "public_execution": execution}


def correction_region(before, after, module=None):
    """Edited teacher steps plus their downstream #reference consumers.

    Invalid input programs make all teacher steps repair targets. This is an
    explicit fallback, recorded separately rather than a semantic localization.
    """
    module = module or executor()
    target = module.parse_program(after)
    try:
        original = module.parse_program(before)
    except module.ExecutorContractError:
        return {"changed": list(range(len(target))), "affected": list(range(len(target))),
                "fallback": "unparseable_student_program"}
    key = lambda step: (step.op, step.arg1, step.arg2)
    edited = set()
    for tag, _a, _b, c, d in SequenceMatcher(a=list(map(key, original)), b=list(map(key, target)), autojunk=False).get_opcodes():
        if tag != "equal":
            edited.update(range(c, d))
    # In a pure deletion, at least the first following teacher step is a target.
    if not edited and list(map(key, original)) != list(map(key, target)):
        edited.update(range(len(target)))
    affected = set(edited)
    for step in target:
        refs = {int(arg[1:]) for arg in (step.arg1, step.arg2) if re.fullmatch(r"#\d+", arg)}
        if refs & affected:
            affected.add(step.index)
    return {"changed": sorted(edited), "affected": sorted(affected), "fallback": None}


def normalized_step_weights(region, step_count, strength=2.0):
    """Step-level diagnostic; actual training normalizes over supervised tokens."""
    if step_count < 1 or strength < 0:
        raise ValueError("positive step count and nonnegative strength required")
    affected = set(region["affected"])
    if any(type(i) is not int or not 0 <= i < step_count for i in affected):
        raise ValueError("step index outside teacher program")
    weights = [1.0 + strength * int(i in affected) for i in range(step_count)]
    mean = sum(weights) / step_count
    return [value / mean for value in weights]


def normalized_token_weights(step_ids, affected, supervised, strength=2.0):
    """Token CE weights: edited/affected steps gain weight, total mass is fixed.

    None identifies protocol/EOS tokens, which keep a positive base weight.
    Prompt/tool observations have supervised=False and always receive zero.
    """
    if len(step_ids) != len(supervised) or strength < 0:
        raise ValueError("unaligned token annotations or negative strength")
    if not any(supervised):
        raise ValueError("no supervised completion tokens")
    affected = set(affected)
    if any(type(i) is not int or i < 0 for i in affected):
        raise ValueError("invalid affected step")
    weights = [float(1 + strength * int(step in affected)) if keep else 0.0
               for step, keep in zip(step_ids, supervised)]
    mean = sum(weights) / sum(bool(keep) for keep in supervised)
    return [value / mean for value in weights]


def correction_fields(before, after, module=None):
    """Localize teacher edits and reference consumers at operand/operator level.

    Alignment uses the operator sequence. It is a training-label heuristic,
    not a proof that each changed field was necessary. Unparseable sources
    receive ordinary recovery supervision instead of invented localization.
    """
    module = module or executor()
    target = module.parse_program(after)
    try:
        original = module.parse_program(before)
    except module.ExecutorContractError:
        return {"fields": [], "fallback": "uniform_unparseable_source"}
    mapping = {}
    for tag, a, b, c, d in SequenceMatcher(a=[s.op for s in original], b=[s.op for s in target], autojunk=False).get_opcodes():
        if tag in ("equal", "replace"):
            mapping.update({new: old for old, new in zip(range(a, b), range(c, d))})
    fields, affected = set(), set()
    for step in target:
        old = original[mapping[step.index]] if step.index in mapping else None
        for field in ("op", "arg1", "arg2"):
            new_value = getattr(step, field)
            changed = old is None or new_value != getattr(old, field)
            if field != "op" and re.fullmatch(r"#\d+", new_value):
                parent = int(new_value[1:])
                prior = getattr(old, field) if old is not None else ""
                rebound = (not re.fullmatch(r"#\d+", prior) or mapping.get(parent) != int(prior[1:]))
                changed = changed or rebound or parent in affected
            if changed:
                fields.add(f"{step.index}:{field}")
                affected.add(step.index)
    return {"fields": sorted(fields), "fallback": None}


def field_token_weights(field_ids, selected, supervised, strength=2.0):
    """Preserve protocol/EOS weights exactly; redistribute only program fields."""
    if len(field_ids) != len(supervised) or strength < 0 or not any(supervised):
        raise ValueError("invalid supervised field alignment")
    selected = set(selected)
    if any(not isinstance(f, str) or not re.fullmatch(r"\d+:(op|arg1|arg2)", f) for f in selected):
        raise ValueError("invalid selected field")
    positions = [i for i, keep in enumerate(supervised) if keep and field_ids[i] is not None]
    weights = [float(bool(keep)) for keep in supervised]
    if positions:
        raw = [1.0 + strength * int(field_ids[i] in selected) for i in positions]
        mean = sum(raw) / len(raw)
        for i, value in zip(positions, raw):
            weights[i] = value / mean
    return weights


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--program", required=True)
    parser.add_argument("--public", type=Path, default=Path("/inputs/public.json"))
    parser.add_argument("--work", type=Path, default=Path("/workspace"))
    parser.add_argument("--executor", type=Path, default=Path("/inputs/executor.py"))
    args = parser.parse_args()
    public = json.loads(args.public.read_text())
    check_public(public)
    work = args.work.resolve()
    candidate = {"program": args.program}
    # Every submission is retained, including invalid programs and later repairs.
    path = work / "candidate.json"
    path.write_text(json.dumps(candidate, ensure_ascii=False) + "\n")
    result = execute_public(args.program, public, executor(args.executor))
    with (work / "executions.jsonl").open("a") as stream:
        stream.write(json.dumps({"program": args.program, "execution": result}, ensure_ascii=False) + "\n")
    print(json.dumps(result, ensure_ascii=False, allow_nan=False))


if __name__ == "__main__":
    main()
