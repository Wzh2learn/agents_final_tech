#!/usr/bin/env python3
"""Check the compact active research context without reading historical assets."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
from urllib.parse import unquote, urlsplit

ACTIVE = {
    'memory/STATE.md': 4096,
    'memory/THREADS.md': 5120,
    'docs/research/README.md': 4096,
    'docs/research/LOOP_D_RESEARCH_PROMPT.md': 6144,
    'research/agent_frontier_portfolio_20261029/STAGE2_AGENT_RESEARCH_PLAN_20261102.md': 10240,
    'research/agent_frontier_portfolio_20261029/AGENT_FRONTIER_RESEARCH_PORTFOLIO.md': 6144,
    'research/agent_frontier_portfolio_20261029/IJCNN_RELATED_WORK_REFRESH_20261030.md': 8192,
}
TOTAL_CAP = 32768
INLINE_LINK = re.compile(r'!?\[[^\]\n]*\]\(\s*(?:<([^>\n]+)>|([^\s)]+))(?:\s+["\'][^\n]*?["\'])?\s*\)')
REFERENCE_DEFINITION = re.compile(r'^\s{0,3}\[(?!\^)[^\]]+\]:\s*(?:<([^>]+)>|(\S+))')
INLINE_CODE = re.compile(r'(`+).*?\1')
FENCE = re.compile(r'^\s{0,3}(`{3,}|~{3,})')


def markdown_destinations(text: str):
    fence = None
    for line_number, line in enumerate(text.splitlines(), 1):
        found = FENCE.match(line)
        if found:
            marker = found.group(1)
            if fence is None:
                fence = marker
            elif marker[0] == fence[0] and len(marker) >= len(fence):
                fence = None
            continue
        if fence is not None:
            continue
        line = INLINE_CODE.sub('', line)
        for match in INLINE_LINK.finditer(line):
            yield line_number, match.group(1) or match.group(2)
        match = REFERENCE_DEFINITION.match(line)
        if match:
            yield line_number, match.group(1) or match.group(2)


def within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def audit(root: Path) -> dict:
    root = root.resolve()
    files, failures, total = [], [], 0
    for rel, cap in ACTIVE.items():
        path = root / rel
        item = {'path': rel, 'bytes': None, 'lines': None, 'cap': cap,
                'status': 'OK', 'broken_links': []}
        files.append(item)
        if not within(path.resolve(), root):
            item['status'] = 'OUTSIDE_ROOT'
            failures.append({'kind': 'outside_root', 'path': rel})
            continue
        try:
            raw = path.read_bytes()
        except FileNotFoundError:
            item['status'] = 'MISSING'
            failures.append({'kind': 'missing_file', 'path': rel})
            continue
        except OSError as exc:
            item['status'] = 'UNREADABLE'
            failures.append({'kind': 'unreadable_file', 'path': rel, 'error': type(exc).__name__})
            continue
        item['bytes'] = len(raw)
        total += len(raw)
        if len(raw) > cap:
            item['status'] = 'OVERSIZE'
            failures.append({'kind': 'file_cap', 'path': rel, 'bytes': len(raw), 'cap': cap})
        try:
            text = raw.decode('utf-8')
        except UnicodeDecodeError:
            item['status'] = 'INVALID_UTF8'
            failures.append({'kind': 'invalid_utf8', 'path': rel})
            continue
        item['lines'] = len(text.splitlines())
        for line_no, destination in markdown_destinations(text):
            if destination.startswith(('#', '/', '\\', '//')) or re.match(r'^[A-Za-z][A-Za-z0-9+.-]*:', destination):
                continue
            parts = urlsplit(destination)
            local_path = unquote(parts.path)
            if not local_path:
                continue
            target = (path.parent / local_path).resolve()
            if not within(target, root):
                continue
            if not target.exists():
                issue = {'line': line_no, 'target': destination}
                item['broken_links'].append(issue)
                failures.append({'kind': 'broken_link', 'path': rel, **issue})
                if item['status'] == 'OK':
                    item['status'] = 'BROKEN_LINK'
    if total > TOTAL_CAP:
        failures.append({'kind': 'total_cap', 'bytes': total, 'cap': TOTAL_CAP})
    return {'ok': not failures, 'total_bytes': total, 'total_cap': TOTAL_CAP,
            'files': files, 'failures': failures}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument('--json', type=Path, help='write result to a new JSON file outside the repository')
    args = parser.parse_args()
    root = args.root.resolve()
    if args.json is not None and within(args.json.resolve(), root):
        parser.error('--json destination must be outside the repository')
    result = audit(root)
    encoded = json.dumps(result, ensure_ascii=False, separators=(',', ':'))
    if args.json is not None:
        try:
            with args.json.open('x', encoding='utf-8', newline='\n') as stream:
                stream.write(encoded + '\n')
        except OSError as exc:
            parser.error(f'cannot create --json destination: {type(exc).__name__}')
    print(encoded)
    return 0 if result['ok'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
