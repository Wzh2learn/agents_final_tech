"""Recover executable certificates from already-delivered finance free answers."""

import argparse
import ast
from collections import Counter
import json
from pathlib import Path
import re

from benchmark_actions import action_cost, deliver, read_panel
from diagnose import read_paired_run, read_replay_call
from grounding import ground
from run_pilot import paired_prompt, write_json
from scoring import _canonical, _reply_text, parse_free, public_execution, score


OPERATIONS = {ast.Add: 'add', ast.Sub: 'subtract', ast.Mult: 'multiply', ast.Div: 'divide'}
CONSTANTS = {1: 'const_1', 2: 'const_2', 100: 'const_100'}
ARITHMETIC = re.compile(r'(?<![\w.])[0-9.()+\-*/ \t]+(?![\w.])')
THOUSANDS = re.compile(r'(?<=\d),(?=\d{3}(?:\D|$))')
CURRENCY = re.compile(r'[$€£](?=[ -]?\d)')
MATH_SIGNS = str.maketrans({'×': '*', '÷': '/', '−': '-', '–': '-'})


def expressions(text):
    candidates = set()
    for line in text.splitlines():
        if '=' not in line and '≈' not in line:
            continue
        normalized = line.replace(r'\times', '*').replace(r'\div', '/').translate(MATH_SIGNS)
        normalized = CURRENCY.sub('', THOUSANDS.sub('', normalized))
        for match in ARITHMETIC.finditer(normalized):
            candidate = match[0].strip().rstrip('.')
            if 3 <= len(candidate) <= 160 and any(op in candidate for op in '+-*/'):
                candidates.add(candidate)
    return sorted(candidates)


def lower(expression, *, declared_constants):
    node = ast.parse(expression, mode='eval').body
    steps = []

    def visit(term):
        if isinstance(term, ast.BinOp) and type(term.op) in OPERATIONS:
            left, right = visit(term.left), visit(term.right)
            steps.append(f'{OPERATIONS[type(term.op)]}({left}, {right})')
            return f'#{len(steps) - 1}'
        sign = -1 if isinstance(term, ast.UnaryOp) and isinstance(term.op, ast.USub) else 1
        atom = term.operand if sign < 0 else term
        if isinstance(atom, ast.Constant) and type(atom.value) in (int, float):
            value = sign * atom.value
            return CONSTANTS[value] if declared_constants and value in CONSTANTS else repr(value)
        raise ValueError('Unsupported arithmetic operand')

    visit(node)
    if not 1 <= len(steps) <= 8:
        raise ValueError('No bounded arithmetic program')
    return ', '.join(steps)


def recover_formula(row, reply):
    """Accept exactly one grounded program that reproduces the reported number and scale."""
    free = parse_free(reply)
    accepted, coverage = recover_from_text(row, free, _reply_text(reply))
    return free, accepted, coverage


def recover_from_text(row, free, text):
    """Recover a formula while holding the delivered answer and scale fixed."""
    declared = free['answer']
    candidates = expressions(text)
    matching, grounded = set(), {}
    if type(declared) in (int, float):
        dataset, scale = row['dataset'], free['scale']
        # TAT-QA scores the rendered prediction and its scale, including for zero.
        # Exact text equality preserves the input to every official normalization path.
        def value_key(answer):
            return str(answer) if dataset == 'tatqa' else _canonical(dataset, answer, scale)

        value = value_key(declared)
        for expr in candidates:
            for declared_constants in (False, True):
                try:
                    program = lower(expr, declared_constants=declared_constants)
                except (SyntaxError, ValueError):
                    continue
                candidate = {**free, 'arm': 'dsl', 'program': program, 'answer': None,
                             'parse_mode': 'visible_formula'}
                native = public_execution(row, candidate)
                if (native['status'] != 'executed'
                        or value_key(native['terminal_execution_answer']) != value):
                    continue
                matching.add(program)
                bindings = ground(row, program)
                if bindings and all((source := binding['selected']) and not source.get('label_cell')
                                    and not binding['explicit_conflicts'] for binding in bindings):
                    grounded[program] = candidate
    accepted = next(iter(grounded.values())) if len(grounded) == 1 else None
    return accepted, {'equations': len(candidates), 'equal_programs': len(matching),
                      'grounded_equal_programs': len(grounded)}


def recorded_reasoning(path):
    """Read the model's reasoning events without copying the trace into results."""
    chunks = []
    for line in path.read_bytes().decode('utf-8', errors='replace').splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue  # Match extraction of JSON events in the native harness.
        if not isinstance(event, dict) or event.get('type') != 'reasoning':
            continue
        part = event.get('part')
        if isinstance(part, dict) and isinstance(part.get('text'), str):
            chunks.append(part['text'])
    return '\n'.join(chunks)


def replay(panel, run, *, dataset='finqa', metric_dir=None, include_recorded_trace=False):
    if dataset == 'tatqa' and metric_dir is None:
        raise ValueError('Official TAT-QA metric directory required')
    public, references, panel_digest = read_panel(panel, dataset)
    reports = {row['id']: row['report'] for row in public}
    _, entries, provenance = read_paired_run(run, panel_digest, reports, dataset, 'compiled_fallback')
    counts = Counter()
    fallback_cases = []
    selected_receipts = []
    for row in public:
        ident = row['id']
        entry = entries[ident]
        baseline = entry['actions']['compiled_fallback']
        receipts = [entry['calls'][name] for name in baseline['calls']]
        if action_cost(receipts) != baseline['cost']:
            raise ValueError(f'{ident}: fallback cost differs from the selected calls')
        selected_receipts.extend(receipts)
        counts.update(n=1, strict=baseline['strict'], joint_before=baseline['strict'] and baseline['executable'])
        if baseline['decision'] != 'free_on_nonexecution':
            continue
        if baseline['calls'] != ['low', 'free'] or baseline['executable']:
            raise ValueError(f'{ident}: expected the recorded numeric-only fallback')
        receipt = read_replay_call(run, row, 'free', 'solve', paired_prompt(row, 'free'), provenance['run.json'],
                                   entry['calls']['free'])
        free, candidate, coverage = recover_formula(row, deliver(receipt))
        gold = references[dataset, ident]
        correct = score(row, free, gold=gold, metric_dir=metric_dir)['strict']
        if free != baseline['submission'] or correct != baseline['strict']:
            raise ValueError(f'{ident}: numeric fallback differs from its frozen receipt')
        trace_fields = {}
        chosen = candidate
        if include_recorded_trace:
            raw = (run / entry['calls']['free']['path']).with_name('raw.jsonl')
            trace = recorded_reasoning(raw)
            trace_candidate, trace_coverage = recover_from_text(row, free, trace)
            trace_only = candidate is None and trace_candidate is not None
            chosen = trace_candidate if trace_only else candidate
            counts.update(fallbacks_with_recorded_trace=bool(trace),
                          correct_fallback_with_trace_only_certificate=correct and trace_only)
            trace_fields = {'trace_grounded_equal_programs': trace_coverage['grounded_equal_programs'],
                            'extra_certificate_from_trace': trace_only}
        if chosen:
            grade = score(row, chosen, gold=gold, metric_dir=metric_dir)
            if not grade['executable'] or grade['strict'] != correct:
                raise ValueError(f'{ident}: formula did not preserve strict numeric scoring')
        counts.update(fallbacks=1, correct_fallbacks=correct,
                      fallback_with_equation=coverage['equations'] > 0,
                      fallback_with_equal_formula=coverage['equal_programs'] > 0,
                      fallback_with_certificate=candidate is not None,
                      correct_fallback_with_certificate=correct and candidate is not None)
        fallback_cases.append({'id': ident, 'strict': correct, 'certificate': candidate is not None,
                               **coverage, **trace_fields})
    counts['joint_after'] = counts['joint_before'] + counts['correct_fallback_with_certificate']
    if include_recorded_trace:
        counts['joint_after_trace'] = counts['joint_after'] + counts['correct_fallback_with_trace_only_certificate']
    return {'dataset': dataset, 'panel': panel_digest, 'source': provenance,
            'additional_model_calls': 0, 'unchanged_model_cost': action_cost(selected_receipts),
            'counts': dict(counts), 'fallback_cases': fallback_cases}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--panel', type=Path, required=True)
    parser.add_argument('--run', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--dataset', choices=('finqa', 'tatqa'), default='finqa')
    parser.add_argument('--metric-dir', type=Path)
    parser.add_argument('--include-recorded-trace', action='store_true',
                        help='Try the native reasoning-event text after abstaining on the delivered reply')
    args = parser.parse_args()
    if args.output.exists():
        parser.error('Use a new results file')
    write_json(args.output, replay(args.panel, args.run, dataset=args.dataset, metric_dir=args.metric_dir,
                                   include_recorded_trace=args.include_recorded_trace))


if __name__ == '__main__':
    main()
