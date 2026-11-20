"""Replay exact public table coordinates on remaining TAT-QA pilot failures."""

import argparse
from collections import Counter
from datetime import datetime
import json
from math import isfinite
from pathlib import Path
import re
from time import process_time

from run_pilot import load_lines
from scoring import (
    OPERATION, PROGRAM_LABEL, SCALE_LABEL, SCALE_PREFIX, _plain, _reply_text, _scale,
    finqa, score,
)
from surface_replay import INLINE_LABEL, replay as replay_surface


CALL = re.compile(r'([A-Za-z_][A-Za-z_0-9]*)\((.*)\)')
OPERATIONS = set(OPERATION.split('|'))
YEAR = re.compile(r'(?:19|20)\d{2}')
PERIOD_HEADING = re.compile(r'\b(?:year|years|fiscal|period|ended|december|january|september)\b', re.I)


def split_items(text):
    """Read comma-delimited items, respecting quotes and nested calls."""
    result = []
    quoted = False
    depth = start = 0
    for index, char in enumerate(text):
        if char == '"':
            quoted = not quoted
        elif not quoted:
            if char in '()':
                depth += 1 if char == '(' else -1
                if depth < 0:
                    raise ValueError('unbalanced_call')
            elif char == ',' and depth == 0:
                result.append(text[start:index].strip())
                start = index + 1
    result.append(text[start:].strip())
    if depth or quoted or not all(result):
        raise ValueError('incomplete_call')
    return result


def parse_call(text):
    match = CALL.fullmatch(text)
    if not match:
        raise ValueError('not_a_call')
    op, inner = match.groups()
    if op not in OPERATIONS and op != 'table_value':
        raise ValueError('unsupported_operator')
    args = []
    for atom in split_items(inner):
        if re.fullmatch(r'"[^"]*"', atom):
            args.append(atom[1:-1])
        elif '(' in atom:
            args.append(parse_call(atom))
        elif '"' in atom or ')' in atom:
            raise ValueError('malformed_atom')
        else:
            args.append(atom)
    return op, tuple(args)


def decode(reply):
    text = _reply_text(reply)
    if re.search(r'</?answer\b', text, re.I):
        raise ValueError('incomplete_answer')
    text = INLINE_LABEL.sub(lambda match: match[0] if match[0].startswith('"') else '\n', text)
    plans, scales = set(), set()
    for raw in text.splitlines():
        line = _plain(raw.strip().rstrip(','))
        if SCALE_PREFIX.match(line):
            label = SCALE_LABEL.fullmatch(line)
            if not label:
                raise ValueError('invalid_scale')
            scales.add(_scale(label[1]))
            continue
        label = PROGRAM_LABEL.match(line)
        source = line[label.end():] if label else line
        if label or re.match(r'[A-Za-z_][A-Za-z_0-9]*\(', source):
            plans.add(tuple(parse_call(item) for item in split_items(source)))
    if len(plans) != 1 or len(scales) != 1:
        raise ValueError('missing_or_conflicting_declaration')
    return plans.pop(), scales.pop()


def resolve_row(table, label):
    matches = [index for index, row in enumerate(table[1:], 1)
               if row and str(row[0]).strip() == label.strip()]
    if not label.strip() or len(matches) != 1:
        raise ValueError('nonunique_row')
    return matches[0]


def projected_columns(table, row, requested):
    # The top row is the ordinary header. A second period header must supply
    # at least two explicit years and have a blank label or a period heading above it.
    headers = [0]
    if row > 1 and sum(bool(YEAR.fullmatch(str(cell).strip())) for cell in table[1][1:]) >= 2:
        if not str(table[1][0]).strip() or any(PERIOD_HEADING.search(str(cell)) for cell in table[0]):
            headers.append(1)
    catalog = {}
    for header in headers:
        for column, label in enumerate(table[header][1:], 1):
            key = str(label).strip()
            if key:
                catalog.setdefault(key, {}).setdefault(column, header)

    selected = []
    for label in requested:
        label = label.strip()
        interpretations = [[label]] if label in catalog else []
        if ',' in label:
            parts = [part.strip() for part in label.split(',')]
            if all(part in catalog for part in parts):
                interpretations.append(parts)
        if len(interpretations) != 1:
            raise ValueError('unresolved_or_ambiguous_column_scope')
        for part in interpretations[0]:
            matches = catalog[part]
            if len(matches) != 1:
                raise ValueError('nonunique_column')
            column, header = next(iter(matches.items()))
            selected.append((column, header))
    if len({column for column, _ in selected}) != len(selected):
        raise ValueError('repeated_column')
    return selected


def compile_table_scope(public, reply):
    steps, scale = decode(reply)
    table = public['table']
    executor = finqa.executor()
    projected, program, provenance = [], [], []

    def values(op, args, step):
        if not args or not all(isinstance(arg, str) for arg in args):
            raise ValueError('table_coordinates_must_be_explicit_labels')
        row_index = resolve_row(table, args[0])
        row = table[row_index]
        if op == 'table_value' and len(args) != 2:
            raise ValueError('table_value_requires_one_column')
        if op != 'table_value' and args[1:] == ('none',):
            columns = [(column, None) for column in range(1, len(row))]
        else:
            columns = projected_columns(table, row_index, args[1:])
        if not columns or (op == 'table_value' and len(columns) != 1):
            raise ValueError('missing_or_nonunique_column_scope')
        if any(column >= len(row) for column, _ in columns):
            raise ValueError('column_outside_row')
        raw = [row[column] for column, _ in columns]
        try:
            numeric = executor.process_table_row(raw, step)
        except executor.ExecutorContractError as error:
            raise ValueError(error.code) from error
        if not all(isfinite(value) for value in numeric):
            raise ValueError('nonfinite_table_cell')
        provenance.extend({
            'step': step, 'operator': op, 'row': row_index, 'row_label': row[0],
            'column': column, 'header_row': header,
            'column_label': table[header][column] if header is not None else None,
            'cell': row[column],
        } for column, header in columns)
        return raw, numeric

    for step, (op, args) in enumerate(steps):
        if op.startswith('table_'):
            cells, numeric = values(op, args, step)
            if op == 'table_value':
                program.append(f'add({numeric[0]!r}, const_0)')
            else:
                # Native aggregates need a row label and all selected raw cells.
                label = f'typed_scope_step_{step}'
                projected.append([label, *cells])
                program.append(f'{op}({label}, none)')
            continue
        if len(args) != 2:
            raise ValueError('native_arithmetic_requires_two_operands')
        atoms = []
        for arg in args:
            if isinstance(arg, tuple):
                nested_op, nested_args = arg
                if nested_op != 'table_value':
                    raise ValueError('only_table_value_can_be_nested')
                _, numeric = values(nested_op, nested_args, step)
                arg = repr(numeric[0])
            if not arg or any(char in arg for char in ('(', ')', ', ')):
                raise ValueError('non_native_arithmetic_operand')
            atoms.append(arg)
        program.append(f'{op}({atoms[0]}, {atoms[1]})')
    if not provenance:
        raise ValueError('no_explicit_table_coordinates')
    return ({**public, 'table': projected},
            {'arm': 'dsl', 'answer': None, 'scale': scale, 'program': ', '.join(program),
             'parse_mode': 'exact_table_scope'}, provenance)


def replay(root, metric_dir):
    surface = replay_surface(root, metric_dir)
    started = process_time()
    public = load_lines(root / 'panel/public.jsonl')
    gold = {row['id']: row['gold'] for row in load_lines(root / 'panel/references.jsonl') if row['dataset'] == 'tatqa'}
    base = surface['counts']
    fallback = Counter(surface['fallback_from_receipts']['surface'])
    gains, typed_cases = Counter(), []
    for case in surface['cases']:
        if not case['eligible'] or case['selected_executable']:
            continue
        index = case['case_index']
        row = public[index]
        path = root / 'calls/tatqa' / f'{index:03d}'
        reply = json.loads((path / 'dsl/call.json').read_text(encoding='utf-8'))['text']
        result = {'case_index': index, 'id': case['id'], 'surface_error': case['candidate_error'] or case['original_error']}
        typed_cases.append(result)
        try:
            bound, candidate, provenance = compile_table_scope(row, reply)
        except ValueError as error:
            result['rejected'] = str(error)
            continue
        observed = score(bound, candidate, metric_dir=metric_dir, gold=gold[row['id']])
        result.update(candidate=candidate, source_cells=provenance, native_error=observed['execution'].get('code'),
                      executable=observed['executable'], strict=observed['strict'])
        if not observed['executable']:
            continue
        before = case['fallback_official_correct']['surface']
        correct = observed['strict']
        free = json.loads((path / 'free/call.json').read_text(encoding='utf-8'))['usage']
        fallback.subtract(total_calls=1, extra_calls=1, unknown_usage_receipts=int(free is None),
                          recorded_model_tokens=free['total'] if free else 0)
        fallback['official_correct'] += int(correct) - int(before)
        gains.update(executable=1, strict=int(correct), fallback_gains=int(correct and not before),
                     fallback_losses=int(before and not correct))
        result['fallback_before_correct'] = before
    return {
        'scope': 'Post-hoc exact table-scope replay on the 200 TAT-QA development receipts.',
        'n': base['n'], 'surface_executable': base['selected_executable'], 'surface_official_correct': base['selected_official_correct'],
        'typed_executable': base['selected_executable'] + gains['executable'],
        'typed_official_correct': base['selected_official_correct'] + gains['strict'],
        'typed_gains': gains['strict'], 'typed_losses': 0, 'typed_eligible': len(typed_cases),
        'fallback_gains': gains['fallback_gains'], 'fallback_losses': gains['fallback_losses'],
        'fallback_from_receipts': {**surface['fallback_from_receipts'], 'typed': fallback},
        'new_model_calls': 0, 'new_provider_tokens': 0, 'dsl_tokens': base['recorded_model_tokens'],
        'typed_cpu_seconds': process_time() - started, 'typed_cases': typed_cases,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--metric-dir', type=Path, required=True)
    args = parser.parse_args()
    report = replay(args.root, args.metric_dir)
    timestamp = datetime.now().astimezone().strftime('%Y%m%dT%H%M%S%z')
    output = args.root / f'tatqa_table_scope_replay_{timestamp}.json'
    with output.open('x', encoding='utf-8') as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(json.dumps({**{key: value for key, value in report.items() if key != 'typed_cases'}, 'output': str(output)}))


if __name__ == '__main__':
    main()
