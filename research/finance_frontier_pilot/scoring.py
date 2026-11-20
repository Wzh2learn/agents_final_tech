"""Evaluate the pilot's two formats without exposing references to public rules."""

from __future__ import annotations

from functools import lru_cache
import json
import math
from pathlib import Path
import re
import sys

LEGACY = Path(__file__).resolve().parents[1] / "agent_frontier_portfolio_20261029"
if str(LEGACY) not in sys.path:
    sys.path.append(str(LEGACY))

import finqa_correction as finqa
import tatqa_correction as tatqa
import tatqa_scale_study as scale_study


SCALE_FACTORS = {"": 1, "percent": 0.01, "thousand": 1000, "million": 10**6, "billion": 10**9}
NORMALIZATION_FACTORS = (0.01, 100, 0.001, 1000)
SCALE_TERMS = r"none|percent(?:age)?|per\s+cent|thousands?|millions?|billions?|%"
NUMBER = r"[+-]?(?:(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?|\.\d+)(?:[eE][+-]?\d+)?"
TERMINAL_ANSWER = re.compile(
    rf"(?:US\$|[\$€£]|(?:USD|EUR|GBP)\s+)?\s*({NUMBER}|yes|no)"
    rf"(?:\s*({SCALE_TERMS}))?(?:\s+(?:USD|EUR|GBP))?\s*[.!]?",
    re.I,
)
ANSWER_LABEL = re.compile(r"^(?:final\s+)?answer(?:\s+is\b|\s*:)\s*", re.I)
PROGRAM_LABEL = re.compile(r"^(?:final\s+)?program\s*:\s*", re.I)
SCALE_LABEL = re.compile(rf"^(?:final\s+)?scale\s*:\s*({SCALE_TERMS})\s*\.?$", re.I)
SCALE_PREFIX = re.compile(r"^(?:final\s+)?scale\s*:", re.I)
OPERATION = r"add|subtract|multiply|divide|exp|greater|table_sum|table_average|table_max|table_min"
FLAT_PROGRAM = re.compile(rf"(?:{OPERATION})\([^()]+\)(?:\s*,\s*(?:{OPERATION})\([^()]+\))*")


def _scale(raw):
    if raw is None:
        return ""
    if not isinstance(raw, str):
        return None
    name = raw.lower().strip()
    if name == "none":
        return ""
    if name in {"%", "percentage", "per cent"}:
        return "percent"
    if name in {"thousands", "millions", "billions"}:
        return name[:-1]
    return name if name in SCALE_FACTORS else None


def _reply_text(reply):
    if isinstance(reply, dict):
        reply = reply.get("content")
    if not isinstance(reply, str):
        return ""
    # Some checkpoints render their internal trace inside the content stream.
    # Only the delivered assistant text is a final answer candidate.
    text = re.sub(r"<think>.*?(?:</think>|\Z)", "", reply, flags=re.I | re.S).strip()
    answer = re.fullmatch(r"<answer>\s*(.*?)\s*</answer>", text, re.I | re.S)
    return answer[1] if answer else text


def _plain(text):
    text = text.replace("−", "-").replace("\\%", "%").replace("\\$", "$")
    text = re.sub(r"\\(?:text|mathrm|mathbf)\{([^{}]*)\}", r"\1", text)
    text = re.sub(r"\\[,;!]|\\quad\b", " ", text)
    text = text.replace("**", "").replace("`", "").strip()
    return re.sub(r"^(?:[-*]\s+|#{1,6}\s+)", "", text)


def _unbox(text):
    # Peel explicit LaTeX answer framing without searching for a number in prose.
    text = text.strip().strip("$").strip()
    match = re.fullmatch(r"\\(?:boxed|fbox)\s*\{(.*)\}\s*[.!]?", text)
    return match.group(1) if match else text


def _number(text):
    # Keep a single leading currency sign distinct from math delimiters.
    text = _plain(_unbox(text)).strip()
    text = re.sub(rf"\s*\[\s*({SCALE_TERMS})\s*\]\s*([.!]?)$", r" \1\2", text, flags=re.I)
    match = TERMINAL_ANSWER.fullmatch(text)
    if not match:
        return None, ""
    raw, scale = match.groups()
    if raw.lower() in {"yes", "no"}:
        return (raw.lower(), "") if not scale else (None, "")
    value = float(raw.replace(",", ""))
    return (value, _scale(scale)) if math.isfinite(value) else (None, "")


def _last_object(text):
    lines = [line for line in text.splitlines() if line.strip()]
    for line in [text, *lines[-1:]]:
        try:
            value = json.loads(line)
        except (TypeError, ValueError):
            continue
        if isinstance(value, dict):
            return value
    return None


def _standalone_scale(lines):
    declarations = [line for line in lines if SCALE_PREFIX.match(line)]
    if not declarations:
        return ""
    if len(declarations) != 1 or not (match := SCALE_LABEL.fullmatch(declarations[0])):
        return None
    return _scale(match.group(1))


def parse_free(reply):
    """Extract a final value. Strict framing and terminal fallbacks are marked."""
    text = _reply_text(reply)
    lines = list(filter(None, map(_plain, text.splitlines())))
    answer, scale, mode = None, "", "missing"
    inline = [(i, match) for i, line in enumerate(lines) if (match := ANSWER_LABEL.match(line))]
    if inline:
        index, label = inline[-1]
        answer, scale = _number(lines[index][label.end():])
        mode = "declared" if lines[index].lower().startswith("final ") else "answer_label"
    elif (obj := _last_object(text)) and type(obj.get("answer")) in (int, float, str):
        answer, scale = _number(str(obj["answer"]))
        explicit = _scale(obj.get("scale"))
        if explicit is None or (scale and "scale" in obj and scale != explicit):
            answer = None
        scale = explicit or scale
        mode = "json"
    else:
        body = [line for line in lines if not SCALE_PREFIX.match(line)]
        if body:
            answer, scale = _number(body[-1])
            mode = "boxed" if re.search(r"\\(?:boxed|fbox)\b", body[-1]) else "numeric_terminal"
    explicit = _standalone_scale(lines)
    if explicit is None or (scale and any(SCALE_PREFIX.match(line) for line in lines) and scale != explicit):
        answer = None
    return {"arm": "free", "answer": answer, "scale": explicit or scale, "program": None,
            "parse_mode": mode if answer is not None else "missing"}


def parse_dsl(reply):
    """Extract a flat declaration and preserve native executor syntax checks."""
    text = _reply_text(reply)
    lines = list(filter(None, map(_plain, text.splitlines())))
    declarations = [line[match.end():].strip() for line in lines if (match := PROGRAM_LABEL.match(line))]
    scale = _standalone_scale(lines)
    program, mode = None, "missing"
    if len(declarations) == 1:
        program, mode = declarations[0], "declared"
    elif not declarations and (obj := _last_object(text)) and isinstance(obj.get("program"), str):
        program, mode = obj["program"].strip(), "json"
        scale = _scale(obj.get("scale", scale)) if scale is not None else None
    elif not declarations:
        body = [line for line in lines if not SCALE_PREFIX.match(line)]
        if body and FLAT_PROGRAM.fullmatch(body[-1]):
            program, mode = body[-1], "program_terminal"
    if scale is None:
        mode = "invalid_scale"
    return {"arm": "dsl", "answer": None, "scale": scale, "program": program or None,
            "parse_mode": mode}


def public_execution(row, parsed):
    """Use the existing native program evaluator on a question-only projection."""
    if parsed["arm"] != "dsl":
        return None
    public = {key: row[key] for key in finqa.PUBLIC_KEYS}
    if row["dataset"] == "tatqa":
        return tatqa.execute_public(parsed["program"], public, parsed["scale"])
    if row["dataset"] == "finqa":
        return finqa.execute_public(parsed["program"], public)
    raise ValueError(f"unknown dataset {row['dataset']}")


def finqa_ratio_rule(row, parsed, execution, *, preserve_literal_ratio=False):
    """Propose the same public percentage-contract edit tested on pilot receipts."""
    if row['dataset'] != 'finqa' or not execution or execution['status'] != 'executed':
        return None
    if not re.search(r'\bpercent(?:age)?\b|%', row['question'], re.I):
        return None
    executor = finqa.executor()
    steps = executor.parse_program(parsed['program'])
    if len(steps) < 2 or (steps[-2].op, steps[-1].op) != ('divide', 'multiply'):
        return None
    arguments = {steps[-1].arg1, steps[-1].arg2}
    if f'#{len(steps) - 2}' not in arguments or not arguments & {'100', '100.0', 'const_100'}:
        return None
    if preserve_literal_ratio and len(steps) == 2:
        from grounding import _value

        operands = [_value(token) for token in (steps[0].arg1, steps[0].arg2)]
        if all(value is not None and not value[1] for value in operands):
            return None
    return {**parsed, 'program': executor.render_program(steps[:-1])}


@lru_cache(maxsize=1)
def _metric_type(metric_dir):
    return tatqa.official_metric_type(metric_dir)


def _official(dataset, answer, scale, gold, metric_dir):
    if answer is None or scale not in SCALE_FACTORS:
        return False
    if isinstance(answer, (float, int)) and not math.isfinite(answer * SCALE_FACTORS[scale]):
        return False
    if dataset == "finqa":
        # The official executor rounds its numeric output before equality to exe_ans.
        value = answer * SCALE_FACTORS["percent"] if scale == "percent" and not isinstance(answer, str) else answer
        return finqa.canonical_answer(value) == gold["exe_ans"]
    if dataset == "tatqa":
        if gold.get("answer_type") != "arithmetic" or gold.get("scale") not in tatqa.SCALES:
            raise ValueError("outside the arithmetic scoring scope")
        if metric_dir is None:
            raise ValueError("official TAT-QA metric_dir is required")
        metric = _metric_type(Path(metric_dir))()
        metric(gold, str(answer), pred_scale=scale)
        return metric.get_overall_metric()[0] == 1
    raise ValueError(f"unknown dataset {dataset}")


def _canonical(dataset, answer, scale):
    """Comparable prediction-only value, independent of scale or answer labels."""
    if answer is None or isinstance(answer, str) or scale not in SCALE_FACTORS:
        return answer
    if dataset == "finqa":
        return finqa.canonical_answer(answer * SCALE_FACTORS["percent"] if scale == "percent" else answer)
    if not scale:
        return round(answer, 4)
    scaled = round(answer, 2) * SCALE_FACTORS[scale]
    return round(scaled, 4) if math.isfinite(scaled) else None


def score(row, parsed, *, metric_dir=None, rule_dir=None, gold=None):
    """Score same official answers, bounded factor hits, and deployable rule outputs."""
    gold = row["gold"] if gold is None else gold
    if "gold" in gold:
        gold = gold["gold"]
    dataset, scale = row["dataset"], parsed["scale"]
    execution = public_execution(row, parsed)
    executable = execution["status"] == "executed" if execution is not None else None
    answer = execution["terminal_execution_answer"] if executable else parsed["answer"]
    strict = _official(dataset, answer, scale, gold, metric_dir)
    matched_factor = None
    if not strict and type(answer) in (int, float) and answer != 0:
        matched_factor = next((
            factor for factor in NORMALIZATION_FACTORS
            if _official(dataset, answer * factor, scale, gold, metric_dir)
        ), None)
    rule_scale = scale
    rule_id = "identity"
    if dataset == "tatqa" and executable and rule_dir is not None:
        public = {key: row[key] for key in finqa.PUBLIC_KEYS}
        case = {"submission": {"program": parsed["program"], "scale": scale},
                "valid": True, "normal": True, "public": public}
        rule_scale = scale_study.joint_rule(case, Path(rule_dir))["scale"]
        rule_id = "public_tatqa_joint_scale"
    rule = strict if rule_scale == scale else _official(dataset, answer, rule_scale, gold, metric_dir)
    return {
        **parsed,
        "strict": strict,
        "norm": strict or matched_factor is not None,
        "rule": rule,
        "rule_id": rule_id,
        "rule_scale": rule_scale,
        "gold_assisted_factor": matched_factor,
        "strict_answer": answer,
        "normalized_answer": _canonical(dataset, answer, scale),
        "executable": executable,
        "execution": execution,
        "scale_exact": answer is not None and scale == gold["scale"] if dataset == "tatqa" else None,
    }
