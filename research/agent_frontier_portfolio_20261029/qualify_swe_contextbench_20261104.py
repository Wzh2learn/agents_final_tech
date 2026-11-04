#!/usr/bin/env python3
"""Inspect linked issue metadata and commit ancestry without reading gold patches."""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import re
import subprocess
import urllib.error
import urllib.request

import pyarrow.parquet as pq

ROOT = Path('/home/testuser/wzh/research_evidence/agent_learning_20261030')
DATA = ROOT / 'swe_contextbench_data_20261104'
SOURCE = ROOT / 'swe_contextbench_source_20261104'
DATASET_REV = '12c65bd15e2559bc808065565e941ee7bbbd008f'
SOURCE_REV = '12ad6ab14e18e9378e1e293c9edbc3f7ce43d27b'
MANIFEST_SHA = 'bfa76e90221cc82e2c33d24588ff3060756c57679d687f68b29e9e662d68b10c'
PAIRS = (
    ('astropy__astropy-14995', 'astropy__astropy-15082'),
    ('django__django-16910', 'django__django-35356'),
    ('matplotlib__matplotlib-26020', 'matplotlib__matplotlib-26331'),
    ('psf__requests-3362', 'psf__requests-3359'),
    ('sphinx-doc__sphinx-8627', 'sphinx-doc__sphinx-8588'),
    ('sympy__sympy-19487', 'sympy__sympy-19484'),
)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def api(url: str) -> dict:
    request = urllib.request.Request(url, headers={'User-Agent': 'JinRongAgents-research-source-qualification',
                                                  'Accept': 'application/vnd.github+json'})
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return {'http_status': response.status, 'data': json.load(response)}
    except (urllib.error.URLError, TimeoutError, ValueError) as exc:
        return {'http_status': getattr(exc, 'code', None), 'error_type': type(exc).__name__, 'data': {}}


def load() -> tuple[list, list, list]:
    manifest = DATA / 'manifest.json'
    if sha(manifest) != MANIFEST_SHA:
        raise ValueError('dataset manifest changed')
    m = json.loads(manifest.read_text(encoding='utf-8'))
    if m['revision'] != DATASET_REV:
        raise ValueError('dataset revision changed')
    for f in m['files']:
        if sha(DATA / f['name']) != f['sha256']:
            raise ValueError('dataset file changed')
    head = subprocess.check_output(['git', '-C', str(SOURCE), 'rev-parse', 'HEAD'], text=True).strip()
    dirty = subprocess.check_output(['git', '-C', str(SOURCE), 'status', '--porcelain'], text=True).strip()
    if head != SOURCE_REV or dirty:
        raise ValueError('source revision changed or dirty')
    cols = ['repo', 'instance_id', 'base_commit', 'created_at', 'problem_statement', 'FAIL_TO_PASS']
    exp = pq.read_table(DATA / 'SWEContextBench_Lite_Experience.parquet', columns=cols).to_pylist()
    rel = pq.read_table(DATA / 'SWEContextBench_Related_Lite.parquet', columns=cols).to_pylist()
    links = pq.read_table(DATA / 'SWEContextBench_Relationship.parquet', columns=[
        'related_instance_id', 'experience_instance_id', 'related_pr_url', 'related_issue_url',
        'experience_pr_url']).to_pylist()
    return exp, rel, links


def trace_evidence(path: Path, issue_url: str | None) -> list[dict]:
    """Bind target-issue mentions to tool calls without retaining prompt or trace text."""
    number = issue_url.rstrip('/').split('/')[-1] if isinstance(issue_url, str) else ''
    if not number.isdigit():
        return []
    marker = '#' + number
    tool_calls = {}
    matches = []
    with path.open(encoding='utf-8') as handle:
        for line_number, line in enumerate(handle, 1):
            event = json.loads(line)
            message = event.get('message', {})
            content = message.get('content', []) if isinstance(message, dict) else []
            for block in content if isinstance(content, list) else []:
                if not isinstance(block, dict):
                    continue
                if block.get('type') == 'tool_use' and block.get('id'):
                    tool_calls[block['id']] = {'line': line_number, 'name': block.get('name'),
                                               'input': block.get('input', {})}
                elif block.get('type') == 'tool_result' and marker in str(block.get('content', '')):
                    call = tool_calls.get(block.get('tool_use_id'), {})
                    command = call.get('input', {}).get('command', '') if isinstance(call.get('input'), dict) else ''
                    result = str(block.get('content', ''))
                    match = re.search(r'\b([0-9a-f]{7,40})\s+Fixed\s+' + re.escape(marker) + r'\b',
                                      result, flags=re.IGNORECASE)
                    matches.append({'tool_result_line': line_number, 'tool_use_line': call.get('line'),
                                    'tool_name': call.get('name'),
                                    'command_sha256': hashlib.sha256(command.encode('utf-8')).hexdigest(),
                                    'command_is_git_log_all': bool(re.search(r'\bgit\s+log\b[^\n]*--all\b', command)),
                                    'fix_commit_prefix': match.group(1) if match else None})
    return matches


def normalized_problem(row: dict) -> str:
    """Compare problem statements without logging their contents or labels."""
    return ' '.join((row.get('problem_statement') or '').split()).casefold()


def inspect(out: Path, use_api: bool) -> None:
    if out.exists():
        raise FileExistsError('qualification receipt exists')
    exp, rel, links = load()
    sources = {x['instance_id']: x for x in exp}
    targets = {x['instance_id']: x for x in rel}
    joined = [x for x in links if x['experience_instance_id'] in sources and x['related_instance_id'] in targets]
    counts = Counter()
    for link in joined:
        source = sources[link['experience_instance_id']]
        target = targets[link['related_instance_id']]
        left, right = normalized_problem(source), normalized_problem(target)
        if left and right and left == right:
            counts['problem_text_equal_normalized'] += 1
        if source['repo'] != target['repo']:
            counts['cross_repository'] += 1
        a, b = source.get('created_at'), target.get('created_at')
        if not a or not b:
            counts['created_at_unknown'] += 1
        elif a < b:
            counts['source_created_before_target'] += 1
        elif a > b:
            counts['source_created_after_target'] += 1
        else:
            counts['same_created_at'] += 1
    cases = SOURCE / 'cases/SWEContextBench Lite'
    case_ids = {x.stem for x in cases.glob('*.json')}
    trace_dir = SOURCE / 'cases/SWEContextBench Lite Past Experience'
    traces: dict[str, list[dict]] = {}
    trace_unmatched = 0
    for path in sorted(trace_dir.glob('*.jsonl')):
        first_user = None
        with path.open(encoding='utf-8') as handle:
            for line in handle:
                event = json.loads(line)
                message = event.get('message', {})
                if (event.get('type') == 'user' and isinstance(message, dict)
                        and isinstance(message.get('content'), str)):
                    first_user = event
                    break
        if first_user is None:
            trace_unmatched += 1
            continue
        prompt = first_user['message']['content']
        matches = [identity for identity in sources if identity in prompt]
        if len(matches) != 1:
            trace_unmatched += 1
            continue
        traces.setdefault(matches[0], []).append({'path': path, 'first_timestamp': first_user.get('timestamp')})
    candidates = []
    for source_id, target_id in PAIRS:
        source, target = sources[source_id], targets[target_id]
        matching = [x for x in joined if x['experience_instance_id'] == source_id
                    and x['related_instance_id'] == target_id]
        if len(matching) != 1 or source['repo'] != target['repo'] or target_id not in case_ids:
            raise ValueError('candidate linkage not unique')
        link = matching[0]
        row = {'repo': source['repo'], 'source': source_id, 'target': target_id,
               'source_created_at': source['created_at'], 'target_created_at': target['created_at'],
               'source_base_commit': source['base_commit'], 'target_base_commit': target['base_commit'],
               'problem_text_equal_normalized': bool(normalized_problem(source) and
                                                     normalized_problem(source) == normalized_problem(target)),
               'source_pr_url': link['experience_pr_url'], 'target_pr_url': link['related_pr_url'],
               'target_issue_url': link['related_issue_url'],
               'target_prompt_chars': len(target.get('problem_statement') or ''),
               'target_fail_to_pass_count': len(json.loads(target.get('FAIL_TO_PASS') or '[]')),
               'source_merge_ancestor_of_target_base': 'NOT_CHECKED'}
        source_traces = traces.get(source_id, [])
        if len(source_traces) == 1:
            trace = source_traces[0]
            text = trace['path'].read_text(encoding='utf-8')
            markers = {'target_instance_id': target_id, 'target_pr_url': row['target_pr_url'],
                       'target_issue_url': row['target_issue_url']}
            for kind, url in [('target_pr_reference', row['target_pr_url']),
                              ('target_issue_reference', row['target_issue_url'])]:
                number = url.rstrip('/').split('/')[-1] if isinstance(url, str) else ''
                markers[kind] = '#' + number if number.isdigit() else ''
            row['source_trace'] = {'file': trace['path'].name, 'sha256': sha(trace['path']),
                                   'bytes': trace['path'].stat().st_size,
                                   'first_timestamp': trace['first_timestamp'],
                                   'explicit_target_markers_found':
                                       {kind: bool(marker and marker in text) for kind, marker in markers.items()},
                                   'target_issue_tool_results': trace_evidence(trace['path'], row['target_issue_url'])}
        else:
            row['source_trace'] = {'mapping_count': len(source_traces)}
        if use_api:
            number = row['source_pr_url'].rstrip('/').split('/')[-1]
            pull = api(f"https://api.github.com/repos/{source['repo']}/pulls/{number}")
            pr = pull['data']
            row.update({'pull_api_status': pull['http_status'], 'pull_api_error': pull.get('error_type'),
                        'source_merged_at': pr.get('merged_at'), 'source_merge_sha': pr.get('merge_commit_sha')})
            if pr.get('merged_at') and pr.get('merge_commit_sha'):
                comparison = api(f"https://api.github.com/repos/{source['repo']}/compare/"
                                 f"{pr['merge_commit_sha']}...{target['base_commit']}")
                detail = comparison['data']
                status = detail.get('status')
                row.update({'compare_api_status': comparison['http_status'],
                            'compare_api_error': comparison.get('error_type'), 'compare_status': status,
                            'source_merge_ancestor_of_target_base':
                                ('YES' if status in ('ahead', 'identical') else
                                 'NO' if status in ('behind', 'diverged') else 'UNKNOWN')})
            elif pull['http_status'] == 200:
                row['source_merge_ancestor_of_target_base'] = 'NO_MERGED_PR'
            else:
                row['source_merge_ancestor_of_target_base'] = 'UNKNOWN'
            for event in row['source_trace'].get('target_issue_tool_results', []):
                if event.get('fix_commit_prefix'):
                    future = api(f"https://api.github.com/repos/{source['repo']}/compare/"
                                 f"{event['fix_commit_prefix']}...{target['base_commit']}")
                    event.update({'fix_compare_api_status': future['http_status'],
                                  'fix_compare_status': future['data'].get('status'),
                                  'fix_compare_error': future.get('error_type')})
        candidates.append(row)
    receipt = {'scope': 'METADATA_ONLY_DEVELOPMENT_SOURCE_SCREEN',
               'inspected_utc': datetime.now(timezone.utc).isoformat(),
               'dataset_revision': DATASET_REV, 'dataset_manifest_sha256': MANIFEST_SHA,
               'qualification_script_sha256': sha(Path(__file__)), 'host_architecture': platform.machine(),
               'source_git_revision': SOURCE_REV, 'source_repository_license': 'NOT_FOUND_AT_ROOT',
               'dataset_card_license': 'MIT; underlying project licenses must be checked individually',
               'experience_rows': len(exp), 'related_rows': len(rel), 'relationship_rows': len(links),
               'lite_links': len(joined), 'lite_related_covered': len({x['related_instance_id'] for x in joined}),
               'metadata_counts': dict(counts), 'case_files': len(case_ids),
               'case_dataset_id_agreement': case_ids == set(targets),
               'experience_trace_files': len(list(trace_dir.glob('*.jsonl'))),
               'experience_ids_with_unique_trace': sum(len(v) == 1 for v in traces.values()),
               'experience_trace_unmatched': trace_unmatched,
               'official_build_script_platform': 'linux/amd64 as documented in source; images not executed here',
               'selection': 'six development examples across repositories with earlier source created_at; '
                            'not random and no gold patch or target test content was read by this script',
               'limits': 'created_at ordering alone does not show a source fix was available in target base; '
                         'GitHub ancestry and literal target-marker checks do not prove task executability, '
                         'absence of semantic leakage, trace correctness or model non-exposure',
               'candidates': candidates}
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'receipt': str(out), 'sha256': sha(out), 'counts': dict(counts),
                      'candidates': [{k: v for k, v in x.items() if k in
                                      ('repo', 'source', 'target', 'source_merge_ancestor_of_target_base',
                                       'compare_status', 'pull_api_status', 'compare_api_status')}
                                     for x in candidates]}, ensure_ascii=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', required=True, type=Path)
    parser.add_argument('--github-api', action='store_true')
    args = parser.parse_args()
    inspect(args.out, args.github_api)
