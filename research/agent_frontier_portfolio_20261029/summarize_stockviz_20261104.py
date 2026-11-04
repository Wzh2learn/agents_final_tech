#!/usr/bin/env python3
"""Recompute the private stock-format development panel from recorded receipts."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re

ROOT = Path('/home/testuser/wzh/research_evidence/agent_learning_20261030/stock_format_agent_20261104')
ARMS = ('no_history', 'raw_history', 'generated_skill', 'readable_tail', 'readable_diagnostic')


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def episode(root: Path, task: int, arm: str) -> dict:
    paths = list(root.glob(f'stock-data-visualization-{task}__{arm}__*'))
    if not paths:
        return {'task': task, 'arm': arm, 'status': 'NOT_FOUND'}
    if len(paths) != 1:
        raise ValueError(f'duplicate episode directories: {task} {arm}')
    path = paths[0]
    if not (path / 'receipt.json').exists():
        return {'task': task, 'arm': arm, 'status': 'NOT_FINISHED', 'case': path.name}
    receipt = json.loads((path / 'receipt.json').read_text(encoding='utf-8'))
    raw = path / 'raw.jsonl'
    if receipt['raw_sha256'] != sha(raw) or receipt['task'] != f'stock-data-visualization-{task}' or receipt['arm'] != arm:
        raise ValueError(f'episode receipt mismatch: {path.name}')
    verifier = path / 'verifier.txt'
    text = verifier.read_text(encoding='utf-8', errors='replace')
    # Parse only the final pytest terminal summary, never a failure traceback.
    terminal = [line for line in text.splitlines() if re.search(r'\b\d+ passed\b', line)]
    if not terminal:
        raise ValueError(f'no pytest terminal summary: {path.name}')
    summary = terminal[-1]
    count = lambda word: int(m.group(1)) if (m := re.search(rf'\b(\d+) {word}\b', summary)) else 0
    reads, errors = [], []
    intervention = json.loads((path / 'intervention.json').read_text(encoding='utf-8'))
    for line in raw.read_text(encoding='utf-8', errors='replace').splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            errors.append('UNPARSEABLE_RAW_LINE')
            continue
        part = event.get('part', {})
        state = part.get('state', {})
        inputs = state.get('input', {})
        if event.get('type') == 'error':
            errors.append(str(event.get('error', {}).get('name', 'UNKNOWN')))
        if event.get('type') == 'tool_use' and part.get('tool') == 'read':
            source_path = str(inputs.get('filePath', ''))
            if source_path in ('/root/source_history.json', '/root/source_history_readable.txt', '/root/source_skill.md'):
                output = str(state.get('output', ''))
                shown = [m.groups() for line in output.splitlines()
                         if (m := re.match(r'^(\d+): ?(.*)$', line))]
                if source_path.endswith('source_history_readable.txt'):
                    mounted = root / 'posthoc_readable_controls_20261104' / arm / 'source_history_readable.txt'
                else:
                    mounted = root / 'source_experience' / Path(source_path).name
                    if source_path.endswith('source_skill.md'):
                        mounted = root / 'source_experience/skill.md'
                if intervention['source_experience_sha256'].get(source_path) != sha(mounted):
                    raise ValueError(f'mounted source history changed: {path.name}')
                expected_lines = mounted.read_text(encoding='utf-8').splitlines()
                visible_exactly = (len(shown) == len(expected_lines)
                                   and all(int(number) == i and content == expected_lines[i - 1]
                                           for i, (number, content) in enumerate(shown, 1)))
                truncated = sum(1 for number, content in shown
                                if 1 <= int(number) <= len(expected_lines)
                                and content != expected_lines[int(number) - 1]
                                and content.endswith('... (line truncated to 2000 chars)'))
                reads.append({'path': source_path, 'status': state.get('status'),
                              'output_chars': len(output),
                              'truncated_lines': truncated,
                              'has_end_of_file_marker': 'End of file' in output,
                              'visible_lines_exactly_match_mounted_file': visible_exactly})
    usage = receipt['step_finish_tokens']
    requests = receipt['model_http_requests']
    return {'task': task, 'arm': arm, 'status': 'RECORDED', 'case': path.name,
            'tests': {'passed': count('passed'), 'failed': count('failed'), 'errors': count('errors'),
                      'summary': summary, 'verifier_sha256': sha(verifier)},
            'agent_exit': receipt['agent_exit'], 'verifier_exit': receipt['verifier_exit'],
            'http_post': sum(x.startswith('POST ') for x in requests),
            'denials': [x for x in requests if x.startswith('DENIED')],
            'recorded_step_finish_events': len(usage),
            'reported_total_tokens': sum(x.get('total', 0) for x in usage),
            'reported_cache_read_tokens_included': sum(x.get('cache', {}).get('read', 0) for x in usage),
            'elapsed_seconds': receipt['elapsed_seconds'], 'history_reads': reads, 'errors': errors,
            'raw_sha256': sha(raw), 'receipt_sha256': sha(path / 'receipt.json')}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--require-complete', action='store_true')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    keys = [(1, 'no_history')] + [(task, arm) for task in (2, 3) for arm in ARMS]
    cases = [episode(args.root, task, arm) for task, arm in keys]
    if args.require_complete and any(case['status'] != 'RECORDED' for case in cases):
        raise ValueError('expected episodes are not all recorded')
    ledger = json.loads((args.root / 'source_experience/ledger.json').read_text(encoding='utf-8'))
    if ledger['status'] != 'RECEIVED' or ledger['skill_sha256'] != sha(args.root / 'source_experience/skill.md'):
        raise ValueError('source skill ledger mismatch')
    recorded = [case for case in cases if case['status'] == 'RECORDED']
    result = {'scope': 'POST_HOC_SINGLE_SAME_SOURCE_DEVELOPMENT_FAMILY', 'cases': cases,
              'source_skill_generation': {'http_post_attempts': 1, 'usage': ledger['usage'],
                                          'ledger_sha256': sha(args.root / 'source_experience/ledger.json')},
              'recorded_episode_post': sum(x['http_post'] for x in recorded),
              'recorded_episode_total_tokens': sum(x['reported_total_tokens'] for x in recorded),
              'recorded_episode_cache_read_tokens_included': sum(x['reported_cache_read_tokens_included'] for x in recorded),
              'note': 'Counts exclude source skill generation; reported totals already include reported cached tokens. '
                      'Denied/failed requests and usage not reported by the backend may have unknown token cost.'}
    output = json.dumps(result, ensure_ascii=False, indent=2) + '\n'
    if args.output:
        if args.output.exists():
            raise ValueError('refusing to overwrite an existing receipt')
        args.output.write_text(output, encoding='utf-8')
        print(json.dumps({'output': str(args.output), 'sha256': sha(args.output)}))
    else:
        print(output)


if __name__ == '__main__':
    main()
