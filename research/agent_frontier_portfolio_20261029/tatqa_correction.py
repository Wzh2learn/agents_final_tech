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
import re
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


def prompt(public, *, terminal_program=False):
    arithmetic.check_public(public)
    delivery = ('You may execute a candidate with the bash tool: ' if terminal_program else
                'Submit a program with the bash tool: ')
    closing = (
        'Repair execution errors. Finish with exactly one plain-text line beginning Final program: '
        'followed by the complete expression, without wrappers, quotes or code fences. '
        'You may add one Final scale: line with none, thousand, million, billion or percent. '
        'An omitted final scale retains your last submitted scale, or none when there is no prior submission. '
        'The execution layer submits the declaration after normal completion. '
        'Keep explanations outside the declaration lines. '
        if terminal_program else 'Repair execution errors and then finish with a short explanation. ')
    return (
        'Solve this numeric question from the supplied TAT-QA table and paragraphs. '
        + delivery + '/extra/bin/python /inputs/finqa_tool.py '
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
        'correctness. ' + closing +
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


def submit_program(program, scale, public, work, module=None, *, origin=None):
    """Persist each actual submission; units are predictions, never gold metadata."""
    arithmetic.check_public(public)
    work = Path(work).resolve()
    candidate = dict(program=program, scale=scale)
    (work / 'candidate.json').write_text(json.dumps(candidate, ensure_ascii=False) + '\n')
    execution = execute_public(program, public, scale, module)
    record = {**candidate, 'execution': execution}
    if origin is not None:
        record['origin'] = origin
    with (work / 'executions.jsonl').open('a') as stream:
        stream.write(json.dumps(record, ensure_ascii=False) + '\n')
    return execution


def submit_terminal_response(events, public, work, module=None):
    """Submit an explicit latest-message program and optional predicted scale."""
    arithmetic.check_public(public)
    events = list(events)
    proposal = arithmetic.terminal_proposal(events)
    if proposal['status'] != 'proposal':
        return dict(status='not_submitted', reason=proposal['status'], origin='terminal_declaration')
    latest, parts = None, {}
    for event in events:
        part = event.get('part')
        if not isinstance(part, dict) or 'messageID' not in part:
            continue
        if part['messageID'] != latest:
            latest, parts = part['messageID'], {}
        if event.get('type') == 'text' and part.get('type') == 'text':
            parts[part['id']] = part['text']
    scales = re.findall(r'^Final scale:[ \t]*([^\r\n]*)$', '\n'.join(parts.values()), re.M)
    if len(scales) > 1:
        return dict(status='not_submitted', reason='ambiguous_scale', origin='terminal_declaration')
    previous = None
    candidate = Path(work) / 'candidate.json'
    if candidate.exists():
        try:
            value = json.loads(candidate.read_text())
        except json.JSONDecodeError:
            value = None
        if isinstance(value, dict) and set(value) == {'program', 'scale'} and isinstance(value['scale'], str):
            previous = value
    scale = scales[0].strip() if scales else previous['scale'] if previous else ''
    if scale == 'none':
        scale = ''
    program = proposal['program']
    execution = submit_program(program, scale, public, work, module, origin='terminal_declaration')
    return dict(status='submitted', origin='terminal_declaration', program=program, scale=scale,
                changed=previous != dict(program=program, scale=scale), execution=execution)


def main():
    parser = argparse.ArgumentParser()
    delivery = parser.add_mutually_exclusive_group(required=True)
    delivery.add_argument('--program')
    delivery.add_argument('--final-jsonl', type=Path)
    parser.add_argument('--scale', choices=SCALES, default='')
    parser.add_argument('--public', type=Path, default=Path('/inputs/public.json'))
    parser.add_argument('--work', type=Path, default=Path('/workspace'))
    parser.add_argument('--executor', type=Path, default=Path('/inputs/executor.py'))
    args = parser.parse_args()
    public = json.loads(args.public.read_text())
    arithmetic.check_public(public)
    module = arithmetic.executor(args.executor)
    if args.final_jsonl is not None:
        if args.scale:
            parser.error('--scale belongs to --program; final output declares its own scale')
        if args.final_jsonl.stat().st_size > 16 * 1024**2:
            raise ValueError('actor output exceeds the terminal submission bound')
        with args.final_jsonl.open() as stream:
            events = (json.loads(line) for line in stream if line.strip())
            result = submit_terminal_response(events, public, args.work, module)
    else:
        result = submit_program(args.program, args.scale, public, args.work, module)
    print(json.dumps(result, ensure_ascii=False, allow_nan=False))


if __name__ == '__main__':
    main()
