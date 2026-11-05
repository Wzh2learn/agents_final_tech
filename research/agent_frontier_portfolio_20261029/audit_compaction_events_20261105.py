#!/usr/bin/env python3
"""Describe recorded compaction-continuation events without invoking a model."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re

ASK_PATTERN = re.compile(
    r'(?i)\b(would you like me to|do you want me to|want me to (?:continue|proceed)|should i continue)\b'
)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def analyze(path: Path) -> dict:
    if path.is_symlink() or not path.is_file():
        raise ValueError(f'raw file is missing or is a symlink: {path}')
    events = [json.loads(line) for line in path.read_text(encoding='utf8').splitlines() if line]
    transitions = []
    for i, event in enumerate(events):
        part = event.get('part', {})
        if part.get('metadata', {}).get('compaction_continue') is not True:
            continue
        following = []
        finish = None
        for later in events[i + 1:]:
            if later.get('type') == 'step_finish':
                finish = later.get('part', {}).get('reason')
                break
            following.append(later)
        tools = [later.get('part', {}).get('tool') for later in following if later.get('type') == 'tool_use']
        texts = [str(later.get('part', {}).get('text', '')) for later in following
                 if later.get('type') == 'text' and not later.get('part', {}).get('synthetic')]
        transitions.append({'raw_event_index_zero_based': i, 'synthetic': part.get('synthetic') is True,
                            'next_step_finish_reason': finish, 'next_step_tools': tools,
                            'next_text_asks_exact_pattern': any(ASK_PATTERN.search(x) for x in texts)})
    text_events = [e for e in events if e.get('type') == 'text' and not e.get('part', {}).get('synthetic')]
    last = str(text_events[-1].get('part', {}).get('text', '')) if text_events else ''
    return {'raw_path': str(path), 'raw_sha256': sha(path), 'events': len(events),
            'compaction_transitions': transitions,
            'final_text_asks_exact_pattern': bool(ASK_PATTERN.search(last))}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--raw', type=Path, action='append', required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    paths = [p.resolve(strict=True) for p in args.raw]
    if len(set(paths)) != len(paths):
        raise ValueError('duplicate input paths')
    receipt = {'selection': 'explicit raw paths; not a random or independent sample',
               'limits': 'An exact English pattern is not a general request-for-permission classifier; '
                         'events do not establish causality or reconstruct the model prompt.',
               'scientific_model_calls': 0, 'script_sha256': sha(Path(__file__)),
               'runs': [analyze(path) for path in paths]}
    encoded = (json.dumps(receipt, ensure_ascii=False, indent=2) + '\n').encode('utf8')
    with args.out.open('xb') as output:
        output.write(encoded)
    print(json.dumps({'receipt': str(args.out), 'sha256': sha(args.out), 'runs': len(paths),
                      'compactions': sum(len(r['compaction_transitions']) for r in receipt['runs'])}))


if __name__ == '__main__':
    main()
