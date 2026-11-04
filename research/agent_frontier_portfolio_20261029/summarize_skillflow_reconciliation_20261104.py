#!/usr/bin/env python3
"""Recompute one exposed SkillFlow agent panel without copying private task data."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re

from qualify_skillflow_reconciliation_20261104 import QUAL, ROOT, TASKS

EPISODES = ROOT / 'skillflow_reconciliation_agent_20261104'
EXPERIENCE = QUAL / 'source_experience_20261104'


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def summarize(root: Path = EPISODES, experience: Path = EXPERIENCE) -> dict:
    config = json.loads((experience / 'config.json').read_text(encoding='utf-8'))
    ledger = json.loads((experience / 'ledger.json').read_text(encoding='utf-8'))
    if (config['history_sha256'] != sha(experience / 'source_history.json')
            or config['readable_history_sha256'] != sha(experience / 'readable_history.txt')
            or ledger['status'] != 'RECEIVED' or ledger['skill_sha256'] != sha(experience / 'skill.md')):
        raise ValueError('source experience or ledger changed')
    cases = {}
    for path in sorted(p for p in root.iterdir() if p.is_dir()):
        receipt_path, intervention_path, independent_path = (path / name for name in
            ('receipt.json', 'intervention.json', 'independent_receipt.json'))
        if not all(p.is_file() for p in (receipt_path, intervention_path, independent_path)):
            raise ValueError(f'episode incomplete: {path.name}')
        receipt = json.loads(receipt_path.read_text(encoding='utf-8'))
        meta = json.loads(intervention_path.read_text(encoding='utf-8'))
        independent = json.loads(independent_path.read_text(encoding='utf-8'))
        if receipt['raw_sha256'] != sha(path / 'raw.jsonl') or meta['task'] != receipt['task']:
            raise ValueError(f'raw or task mismatch: {path.name}')
        condition = meta.get('condition', 'no_history')
        key = (meta['task'], meta['variant'], condition)
        if key in cases:
            raise ValueError(f'duplicate episode: {key}')
        if independent['status'] == 'RECORDED':
            output_file = path / 'work' / ('cloud_service_portfolio_diff.json' if meta['task'] == TASKS[0]
                                          else 'hospital_capacity_diff_report.json')
            if not output_file.is_file() or sha(output_file) != independent['candidate_sha256']:
                raise ValueError(f'candidate changed: {path.name}')
        reads, errors, mentioned_inputs = [], [], set()
        for line in (path / 'raw.jsonl').read_text(encoding='utf-8', errors='replace').splitlines():
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                errors.append('UNPARSEABLE_RAW_LINE')
                continue
            part, state = event.get('part', {}), event.get('part', {}).get('state', {})
            inputs = state.get('input', {})
            if event.get('type') == 'error':
                errors.append(str(event.get('error', {}).get('name', 'UNKNOWN')))
            if event.get('type') != 'tool_use':
                continue
            for name in meta['input_hashes']:
                if name in json.dumps(inputs, ensure_ascii=False):
                    mentioned_inputs.add(name)
            file_path = inputs.get('filePath')
            if part.get('tool') == 'read' and file_path in ('/root/source_history_readable.txt', '/root/source_skill.md'):
                local = experience / ('readable_history.txt' if file_path.endswith('readable.txt') else 'skill.md')
                if meta['source_experience_sha256'].get(file_path) != sha(local):
                    raise ValueError(f'mounted experience changed: {path.name}')
                text = str(state.get('output', ''))
                shown = [m.groups() for line in text.splitlines() if (m := re.match(r'^(\d+): ?(.*)$', line))]
                expected = local.read_text(encoding='utf-8').splitlines()
                exact = (len(shown) == len(expected) and
                         all(int(number) == i and content == expected[i - 1]
                             for i, (number, content) in enumerate(shown, 1)))
                reads.append({'path': file_path, 'status': state.get('status'), 'lines_match_mounted_file': exact})
        usage = receipt['step_finish_tokens']
        calls = receipt['model_http_requests']
        cases[key] = {'task': meta['task'], 'variant': meta['variant'], 'condition': condition, 'case': path.name,
                      'agent_exit': receipt['agent_exit'], 'upstream_verifier_exit': receipt['verifier_exit'],
                      'upstream_scope': meta['upstream_verifier_interpretation'],
                      'independent_status': independent['status'], 'independent_result': independent.get('result'),
                      'independent_seconds': independent.get('check', {}).get('seconds'),
                      'http_post': sum(x.startswith('POST ') for x in calls),
                      'denials': [x for x in calls if x.startswith('DENIED')],
                      'reported_total_tokens': sum(x.get('total', 0) for x in usage),
                      'reported_cache_read_tokens_included': sum(x.get('cache', {}).get('read', 0) for x in usage),
                      'elapsed_seconds': receipt['elapsed_seconds'], 'experience_reads': reads,
                      'tool_inputs_mention': sorted(mentioned_inputs), 'errors': errors,
                      'raw_sha256': sha(path / 'raw.jsonl'), 'receipt_sha256': sha(receipt_path),
                      'independent_receipt_sha256': sha(independent_path)}
    expected = {(TASKS[0], 'normal', 'no_history')} | {(TASKS[1], variant, condition)
        for variant in ('normal', 'stale_example') for condition in ('no_history', 'source_history', 'generated_skill')}
    if set(cases) != expected:
        raise ValueError(f'missing/unexpected cases: {set(cases) ^ expected}')
    ordered = [cases[key] for key in sorted(cases)]
    return {'scope': 'EXPOSED_SYNTHETIC_ONE_FAMILY_DEVELOPMENT', 'cases': ordered,
            'source_skill_generation': {'http_post_attempts': 1, 'usage': ledger['usage'],
                                        'ledger_sha256': sha(experience / 'ledger.json')},
            'agent_http_post': sum(x['http_post'] for x in ordered),
            'agent_reported_tokens': sum(x['reported_total_tokens'] for x in ordered),
            'agent_cache_read_included': sum(x['reported_cache_read_tokens_included'] for x in ordered),
            'note': 'Generation is listed separately; cached tokens are already included in reported totals. '
                    'Input filename mentions in a tool call do not prove actual use of their contents.'}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    result = json.dumps(summarize(), ensure_ascii=False, indent=2) + '\n'
    if args.output:
        if args.output.exists():
            raise ValueError('refusing to overwrite receipt')
        args.output.write_text(result, encoding='utf-8')
        print(json.dumps({'output': str(args.output), 'sha256': sha(args.output)}))
    else:
        print(result)


if __name__ == '__main__':
    main()
