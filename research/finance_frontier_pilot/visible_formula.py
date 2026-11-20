"""Recover executable certificates from already-delivered FinQA free answers."""

import argparse
import ast
from collections import Counter
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
    if row['dataset'] != 'finqa':
        raise ValueError('Visible equation recovery is defined here for FinQA')
    free = parse_free(reply)
    declared = free['answer']
    candidates = expressions(_reply_text(reply))
    matching, grounded = set(), {}
    if type(declared) in (int, float):
        value = _canonical('finqa', declared, free['scale'])
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
                        or _canonical('finqa', native['terminal_execution_answer'], free['scale']) != value):
                    continue
                matching.add(program)
                bindings = ground(row, program)
                if bindings and all((source := binding['selected']) and not source.get('label_cell')
                                    and not binding['explicit_conflicts'] for binding in bindings):
                    grounded[program] = candidate
    accepted = next(iter(grounded.values())) if len(grounded) == 1 else None
    return free, accepted, {'equations': len(candidates), 'equal_programs': len(matching),
                            'grounded_equal_programs': len(grounded)}


def replay(panel, run):
    public, references, panel_digest = read_panel(panel, 'finqa')
    reports = {row['id']: row['report'] for row in public}
    _, entries, provenance = read_paired_run(run, panel_digest, reports, 'finqa', 'compiled_fallback')
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
        gold = references['finqa', ident]
        correct = score(row, free, gold=gold)['strict']
        if free != baseline['submission'] or correct != baseline['strict']:
            raise ValueError(f'{ident}: numeric fallback differs from its frozen receipt')
        if candidate:
            grade = score(row, candidate, gold=gold)
            if not grade['executable'] or grade['strict'] != correct:
                raise ValueError(f'{ident}: formula did not preserve strict numeric scoring')
        counts.update(fallbacks=1, correct_fallbacks=correct,
                      fallback_with_equation=coverage['equations'] > 0,
                      fallback_with_equal_formula=coverage['equal_programs'] > 0,
                      fallback_with_certificate=candidate is not None,
                      correct_fallback_with_certificate=correct and candidate is not None)
        fallback_cases.append({'id': ident, 'strict': correct, 'certificate': candidate is not None, **coverage})
    counts['joint_after'] = counts['joint_before'] + counts['correct_fallback_with_certificate']
    return {'dataset': 'finqa', 'panel': panel_digest, 'source': provenance,
            'additional_model_calls': 0, 'unchanged_model_cost': action_cost(selected_receipts),
            'counts': dict(counts), 'fallback_cases': fallback_cases}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--panel', type=Path, required=True)
    parser.add_argument('--run', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error('Use a new results file')
    write_json(args.output, replay(args.panel, args.run))


if __name__ == '__main__':
    main()
