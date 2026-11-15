"""Original TAT-QA arithmetic tasks with public execution and private scoring.

Uses the existing FinQA DSL executor. The host scorer is the unmodified official
TAT-QA code at the pinned revision; it is never mounted into the Agent's inputs.
This module does not start a model or alter the active FinQA runner.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import finqa_correction as arithmetic

SCALES = ('', 'thousand', 'million', 'billion', 'percent')
OFFICIAL_COMMIT = '870accc41953dcde885aabeb963d94aabdc0fbc3'
OFFICIAL_FILES = {
    'tatqa_utils.py': 'a84bb2f960737cf0a53733637a674cc4b20ef030a2be6a4b21dc2c4356f415ec',
    'tatqa_metric.py': '2aeeac479f89f8c76300af1cc0e8d098eb86af84bc386b38b6ab4af484a6dea8',
}


def public_record(record, question):
    """Keep the original full table and paragraphs, without answer annotations."""
    value = dict(id=question['uid'], report='TAT-QA/' + record['table']['uid'],
                 question=question['question'], table=record['table']['table'],
                 pre_text=[p['text'] for p in record['paragraphs']], post_text=[])
    arithmetic.check_public(value)
    return value


def prompt(public):
    arithmetic.check_public(public)
    return (
        'Solve this numeric question from the supplied TAT-QA table and paragraphs. '
        'Submit a program with the bash tool: /extra/bin/python /inputs/finqa_tool.py '
        '--program followed by one quoted FinQA program string. You may also supply '
        '--scale with one of thousand, million, billion or percent; omitted scale means no scale. '
        'The numerical result and this predicted scale together represent your answer. '
        'For example, 22.12 with scale percent means 22.12 percent, and 0.2212 with no scale '
        'represents the same quantity. A percent sign on a program operand already divides it by 100. '
        'Allowed operators: add, subtract, multiply, divide, exp, greater, table_sum, table_average, '
        'table_max, table_min. Each step has two arguments; separate steps with commas and use '
        '#0 for the result of step zero. const_100 means 100; const_m1 means -1. '
        'For table operations use the exact row label and none as the second argument. '
        'The tool saves the latest program and scale, and reports execution feedback, never answer '
        'correctness. Repair execution errors and then finish with a short explanation. '
        'Do not edit /inputs or invent a separate answer field.\n\n'
        + json.dumps(public, ensure_ascii=False))


def execute_public(program, public, scale='', module=None):
    arithmetic.check_public(public)
    if type(scale) is not str or scale not in SCALES:
        return dict(status='error', code='UNSUPPORTED_PREDICTED_SCALE')
    result = arithmetic.execute_public(program, public, module)
    return {**result, 'predicted_scale': scale}


def official_metric_type(directory):
    """Load only the verified upstream files; never download during evaluation."""
    directory = Path(directory)
    for name, digest in OFFICIAL_FILES.items():
        if hashlib.sha256((directory / name).read_bytes()).hexdigest() != digest:
            raise ValueError('official TAT-QA source changed: ' + name)
    for name, filename in [('tatqa_utils', 'tatqa_utils.py'), ('_tatqa_official_870accc', 'tatqa_metric.py')]:
        existing = sys.modules.get(name)
        if existing is not None:
            if hashlib.sha256(Path(existing.__file__).read_bytes()).hexdigest() != OFFICIAL_FILES[filename]:
                raise ValueError('conflicting TAT-QA module already loaded')
        else:
            spec = importlib.util.spec_from_file_location(name, directory / filename)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            sys.modules[name] = module
    return sys.modules['_tatqa_official_870accc'].TaTQAEmAndF1


def grade(submission, public, gold, *, metric_dir):
    """Host-only official EM/F1; scale accuracy is reported separately."""
    if gold.get('answer_type') != 'arithmetic' or gold.get('scale') not in SCALES:
        raise ValueError('outside the declared arithmetic scoring scope')
    valid_submission = isinstance(submission, dict) and set(submission) == {'program', 'scale'}
    if not valid_submission:
        execution = dict(status='error', code='PROGRAM_AND_SCALE_REQUIRED')
    else:
        execution = execute_public(submission['program'], public, submission['scale'])
    valid = execution['status'] == 'executed'
    em = f1 = 0.0
    predicted_scale = submission['scale'] if valid_submission else None
    if valid:
        metric = official_metric_type(metric_dir)()
        # Official predictions are text. Passing the float zero would hit the
        # scorer's empty-prediction branch instead of evaluating a zero answer.
        metric(gold, str(execution['terminal_execution_answer']), pred_scale=predicted_scale)
        em, f1, _, _ = metric.get_overall_metric()
    return dict(execution_correct=valid and em == 1.0, program_valid=valid,
                public_execution=execution, official_em=float(em), official_f1=float(f1),
                scale_exact=predicted_scale == gold['scale'], predicted_scale=predicted_scale)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--program', required=True)
    parser.add_argument('--scale', choices=SCALES, default='')
    parser.add_argument('--public', type=Path, default=Path('/inputs/public.json'))
    parser.add_argument('--work', type=Path, default=Path('/workspace'))
    parser.add_argument('--executor', type=Path, default=Path('/inputs/executor.py'))
    args = parser.parse_args()
    public = json.loads(args.public.read_text())
    arithmetic.check_public(public)
    candidate = dict(program=args.program, scale=args.scale)
    work = args.work.resolve()
    (work / 'candidate.json').write_text(json.dumps(candidate, ensure_ascii=False) + '\n')
    result = execute_public(args.program, public, args.scale, arithmetic.executor(args.executor))
    with (work / 'executions.jsonl').open('a') as stream:
        stream.write(json.dumps({**candidate, 'execution': result}, ensure_ascii=False) + '\n')
    print(json.dumps(result, ensure_ascii=False, allow_nan=False))


if __name__ == '__main__':
    main()
