"""Replay surface-only decoding on the recorded TAT-QA pilot responses."""

import argparse
from collections import Counter
import json
from pathlib import Path
import re
from time import process_time

from run_pilot import load_lines
from scoring import (
    OPERATION, PROGRAM_LABEL, SCALE_LABEL, SCALE_PREFIX, _plain, _reply_text, _scale,
    parse_dsl, parse_free, score,
)


INLINE_LABEL = re.compile(
    r'"[^"\n]*"|(?:,\s*|(?<=\))[ \t]+)(?=(?:final\s+)?(?:program|scale)\s*:)', re.I
)
ATOM = r'"[^"\r\n]*"|[^(),"\r\n]+'
STEP = re.compile(rf'({OPERATION})\(\s*({ATOM})\s*,\s*({ATOM})\s*\)')
NEXT_STEP = re.compile(r'\s*,\s*')


def canonical_program(text):
    """Read native flat calls without splitting a quoted atom at its commas."""
    steps, cursor = [], 0
    while match := STEP.match(text, cursor):
        op, *tokens = match.groups()
        args = [token[1:-1] if token.startswith('"') else token.strip() for token in tokens]
        if any(not arg or ', ' in arg or '(' in arg or ')' in arg for arg in args):
            return None
        if op.startswith('table_') and args[1] != 'none':
            return None
        steps.append(f'{op}({args[0]}, {args[1]})')
        if match.end() == len(text):
            return ', '.join(steps)
        separator = NEXT_STEP.match(text, match.end())
        if not separator:
            return None
        cursor = separator.end()
    return None


def decode_surface(reply):
    """Accept one complete declared scale and one unambiguous native program."""
    text = _reply_text(reply)
    if re.search(r'</?answer\b', text, re.I):
        return None
    text = INLINE_LABEL.sub(lambda match: match[0] if match[0].startswith('"') else '\n', text)
    programs, scales = set(), set()
    for raw in text.splitlines():
        line = _plain(raw.strip().rstrip(','))
        if SCALE_PREFIX.match(line):
            match = SCALE_LABEL.fullmatch(line)
            if not match:
                return None
            scales.add(_scale(match[1]))
            continue
        label = PROGRAM_LABEL.match(line)
        program = canonical_program(line[label.end():] if label else line)
        if label and program is None:
            return None
        if program is not None:
            programs.add(program)
    if len(programs) != 1 or len(scales) != 1:
        return None
    return {'arm': 'dsl', 'answer': None, 'scale': scales.pop(),
            'program': programs.pop(), 'parse_mode': 'surface_replay'}


def replay(root, metric_dir):
    public = load_lines(root / 'panel/public.jsonl')
    jobs = [(index, row) for index, row in enumerate(public) if row['dataset'] == 'tatqa']
    references = [row for row in load_lines(root / 'panel/references.jsonl') if row['dataset'] == 'tatqa']
    gold = {row['id']: row['gold'] for row in references}
    if len(jobs) != 200 or len(references) != 200 or len(gold) != 200 or {row['id'] for _, row in jobs} != gold.keys():
        raise ValueError('expected all 200 distinct TAT-QA pilot receipts and matching references')

    counts, cases = Counter(), []
    fallback = {'frozen': Counter(), 'surface': Counter()}
    start = process_time()
    for index, row in jobs:
        path = root / 'calls/tatqa' / f'{index:03d}'
        receipt = json.loads((path / 'dsl/call.json').read_text(encoding='utf-8'))
        reply = receipt['text']
        observed = score(row, parse_dsl(reply), metric_dir=metric_dir, gold=gold[row['id']])
        stopped = receipt['finish'] == ['stop'] and not receipt['exit_code'] and not receipt['errors'] and bool(reply.strip())
        eligible = not observed['executable'] and stopped
        candidate = decode_surface(reply) if eligible else None
        proposed = score(row, candidate, metric_dir=metric_dir, gold=gold[row['id']]) if candidate else None
        selected = proposed if proposed is not None and proposed['executable'] else observed
        if not observed['executable']:
            free_receipt = json.loads((path / 'free/call.json').read_text(encoding='utf-8'))
            free = score(row, parse_free(free_receipt['text']), metric_dir=metric_dir, gold=gold[row['id']])
        fallback_correct = {}
        for name, result in (('frozen', observed), ('surface', selected)):
            needs_free = not result['executable']
            fallback_correct[name] = (free if needs_free else result)['strict']
            costs = [receipt['usage'], free_receipt['usage']] if needs_free else [receipt['usage']]
            fallback[name].update({
                'official_correct': fallback_correct[name], 'extra_calls': needs_free,
                'total_calls': len(costs), 'unknown_usage_receipts': sum(usage is None for usage in costs),
                'recorded_model_tokens': sum(usage['total'] for usage in costs if usage is not None),
            })
        counts.update({
            'n': 1, 'eligible': eligible, 'decoded': candidate is not None,
            'original_executable': observed['executable'], 'selected_executable': selected['executable'],
            'original_official_correct': observed['strict'], 'selected_official_correct': selected['strict'],
            'gains': selected['strict'] and not observed['strict'], 'losses': observed['strict'] and not selected['strict'],
            'fallback_gains': fallback_correct['surface'] and not fallback_correct['frozen'],
            'fallback_losses': fallback_correct['frozen'] and not fallback_correct['surface'],
            'recorded_model_tokens': (receipt['usage'] or {}).get('total', 0),
            'unknown_usage_receipts': receipt['usage'] is None,
        })
        cases.append({
            'case_index': index, 'id': row['id'], 'original_error': observed['execution'].get('code'),
            'original_executable': observed['executable'], 'original_official_correct': observed['strict'],
            'eligible': eligible, 'surface_candidate': candidate,
            'candidate_error': proposed['execution'].get('code') if proposed else None,
            'selected_executable': selected['executable'], 'selected_official_correct': selected['strict'],
            'fallback_official_correct': fallback_correct,
        })
    return {'scope': 'Post-hoc paired replay on the 200 development receipts, with original official scoring.',
            'counts': dict(counts), 'fallback_from_receipts': fallback, 'new_model_calls': 0, 'new_provider_tokens': 0,
            'cpu_seconds': process_time() - start, 'cases': cases}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--metric-dir', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    report = replay(args.root, args.metric_dir)
    with args.output.open('x', encoding='utf-8') as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(json.dumps({key: value for key, value in report.items() if key != 'cases'}))


if __name__ == '__main__':
    main()
