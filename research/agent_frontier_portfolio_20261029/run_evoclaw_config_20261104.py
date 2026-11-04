#!/usr/bin/env python3
"""Run source/target EvoClaw config tasks with isolated, post-run checks."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time

from qualify_evoclaw_config_20261104 import (
    BENCH, EVIDENCE, FILES, IMAGE, OUT as QUAL, REVISION, TASK, digest, independent_errors,
)

BASE = Path('/home/testuser/wzh/research_evidence/agent_skill_method_20261029/run_skill_episode_output8192.py')
BASE_SHA = '4111a0be97845740769722e2e596871d51c7693d14d2372d7f6931b4d06e7afb'
QUAL_SHA = '927d12958f2eae6b6fb9019165d4254460af1d221f1a34da5186849c59cc0119'
PACK = EVIDENCE / 'evoclaw_config_adapted_20261104'
RUNS = EVIDENCE / 'evoclaw_config_agent_20261104'
GROUPS = {'config-source': ('webapp',), 'config-target': ('worker', 'gateway', 'scheduler', 'mailer')}


def replace_once(text: str, old: str, new: str, count: int = 1) -> str:
    if text.count(old) != count:
        raise ValueError(f'unexpected harness fragment: {old[:80]!r}')
    return text.replace(old, new, count)


def prepare() -> None:
    if PACK.exists():
        raise FileExistsError('refusing to overwrite adapted task inputs')
    if digest(QUAL / 'receipt.json') != QUAL_SHA or digest(BASE) != BASE_SHA:
        raise ValueError('qualification or base harness changed')
    original = TASK.read_text(encoding='utf-8')
    match = re.search(r'## Prompt\s*\n(.*?)\n---\s*\n\s*## Expected Behavior', original, re.DOTALL)
    if not match:
        raise ValueError('cannot isolate the public task prompt')
    text = match.group(1).strip()
    marker = '**Files to migrate:**'
    if text.count(marker) != 1 or text.count('You have 5 application configuration files') != 1:
        raise ValueError('task prompt changed')
    preamble = text.split(marker, 1)[0]
    PACK.mkdir(parents=True)
    manifest = {'upstream_revision': REVISION, 'task_sha256': digest(TASK),
                'qualification_sha256': QUAL_SHA, 'base_sha256': BASE_SHA,
                'adaptation': 'public prompt split into source and target files; not an official benchmark run',
                'groups': {}}
    for group, names in GROUPS.items():
        root = PACK / group
        assets = root / 'assets/config_migration'
        assets.mkdir(parents=True)
        body = preamble.replace('You have 5 application configuration files',
                                f'You have {len(names)} application configuration file' + ('s' if len(names) != 1 else ''))
        body += marker + '\n' + ''.join(
            f'{i}. `assets/config_migration/{name}_v1.json` → `outputs/{name}_v2.json`\n'
            for i, name in enumerate(names, 1))
        (root / 'task.md').write_text(body, encoding='utf-8')
        hashes = {}
        for name in names:
            source = BENCH / f'assets/config_migration/{name}_v1.json'
            shutil.copyfile(source, assets / source.name)
            hashes[source.name] = digest(source)
        manifest['groups'][group] = {'files': list(names), 'input_sha256': hashes,
                                     'instruction_sha256': digest(root / 'task.md')}
    (PACK / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'manifest': str(PACK / 'manifest.json'), 'sha256': digest(PACK / 'manifest.json')}))


def verify_inputs(group: str) -> dict:
    manifest = json.loads((PACK / 'manifest.json').read_text(encoding='utf-8'))
    if manifest['upstream_revision'] != REVISION or manifest['qualification_sha256'] != QUAL_SHA:
        raise ValueError('adaptation provenance changed')
    if digest(QUAL / 'receipt.json') != QUAL_SHA or digest(BASE) != BASE_SHA:
        raise ValueError('qualification or harness changed')
    item, root = manifest['groups'][group], PACK / group
    if item['files'] != list(GROUPS[group]) or digest(root / 'task.md') != item['instruction_sha256']:
        raise ValueError('adapted task changed')
    for filename, wanted in item['input_sha256'].items():
        if digest(root / 'assets/config_migration' / filename) != wanted:
            raise ValueError('adapted input changed')
    return item


def derived_harness(group: str, history: Path | None) -> str:
    code = BASE.read_text(encoding='utf-8')
    edits = [
        ("ROOT=Path('/home/testuser/wzh/research_evidence/agent_skill_method_20261029')", f'ROOT=Path({str(RUNS)!r})', 1),
        ("UP=Path('/home/testuser/wzh/research_evidence/agent_frontier_20261029/skillsbench_v1_1/tasks')", f'UP=Path({str(PACK)!r})', 1),
        ("if task not in ('llm-prefix-cache-replay','dialogue-parser','tictoc-unnecessary-abort-detection') or arm not in ('no_skill','all_skill','select_skill'): raise SystemExit('unsupported')",
         f"if task not in {tuple(GROUPS)!r} or arm != 'no_skill': raise SystemExit('unsupported')", 1),
        ("body=(src/'task.md').read_text(encoding='utf8').split('---',2)[2].strip()",
         "body=(src/'task.md').read_text(encoding='utf8').strip()", 1),
        ("(work/'instructions.txt').write_text(body,encoding='utf8')",
         "(work/'instructions.txt').write_text(body,encoding='utf8')\n"
         "(work/'assets').mkdir()\n" + ("(work/'source_history.txt').touch(mode=0o444)" if history else 'pass'), 1),
        ("Never read an entire large trace into the conversation; inspect only the first two lines using shell head, then write code that processes the complete unmodified file.",
         'Treat the mounted input files as read-only. Follow the current task instructions.', 1),
        ("len(calls)>=8", "len(calls)>=24", 1),
        ("sum(payload_bytes)+length>450000", "sum(payload_bytes)+length>1500000", 1),
        ("calls.append('DENIED_OR_LIMIT');self.request.sendall",
         "reason=('method' if line not in allowed else 'request_cap' if len(calls)>=24 "
         "else 'missing_length' if length is None else 'post_byte_cap')\n"
         "   calls.append('DENIED:'+reason);self.request.sendall", 1),
        ("'timeout':120000", "'timeout':300000", 1),
        ("[],[],120)", "[],[],300)", 2),
        ("stderr=subprocess.PIPE,timeout=300)", "stderr=subprocess.PIPE,timeout=1200)", 1),
        ("'--cpus','1','--cap-drop'", "'--cpus','2','--cap-drop'", 1),
        ("'--memory','2g'", "'--memory','3g'", 1),
        ("sockpath.unlink(missing_ok=True)", "sockpath.unlink(missing_ok=True);bridge.rmdir()", 1),
        ("case=ROOT/(task+'__'+arm+'__'+str(os.getpid()))",
         f"case=ROOT/(task+'__{'source_history' if history else 'no_history'}__'+str(os.getpid()))", 1),
    ]
    for old, new, count in edits:
        code = replace_once(code, old, new, count)
    mounts = "['--mount',f'type=bind,src={src / \"assets\"},dst=/root/assets,readonly']"
    if history:
        mounts += f"+['--mount',f'type=bind,src={str(history)},dst=/root/source_history.txt,readonly']"
        code = replace_once(code, 'Use available tools to implement and execute your solution.',
                            'Before solving, read /root/source_history.txt from a prior related task; '
                            'decide what applies and follow the current task. '
                            'Use available tools to implement and execute your solution.')
    code = replace_once(code, 'server=Server(str(sockpath),Handler);',
                        f"_at=cmd.index('python:3.12-slim'); cmd[_at:_at]={mounts}; "
                        "server=Server(str(sockpath),Handler);")
    marker = '# A completely separate non-agent container mounts verifier after the episode;'
    if code.count(marker) != 1 or code.count("receipt={'task':task") != 1:
        raise ValueError('cannot isolate base post-run verification')
    head = code.split(marker, 1)[0]
    tail = "receipt={'task':task" + code.split("receipt={'task':task", 1)[1]
    code = head + '\nvrc=None\n' + tail
    compile(code, str(BASE), 'exec')
    return code


def postcheck(group: str, case: Path) -> dict:
    src, work = PACK / group, case / 'work'
    cmd = ['docker', 'run', '--rm', '--pull', 'never', '--network', 'none', '--read-only',
           '--cpus', '2', '--memory', '2g', '--pids-limit', '128', '--cap-drop', 'ALL',
           '--security-opt', 'no-new-privileges', '-e', 'PYTHONDONTWRITEBYTECODE=1',
           '--mount', f'type=bind,src={work},dst=/work,readonly',
           '--mount', f'type=bind,src={src / "assets"},dst=/work/assets,readonly',
           '--mount', f'type=bind,src={QUAL},dst=/checks,readonly',
           IMAGE, 'python3', '/checks/evaluate.py', '/work']
    started = time.monotonic()
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=120, check=True)
    scores, details = json.loads(proc.stdout), {}
    for name in GROUPS[group]:
        path = work / f'outputs/{name}_v2.json'
        keys = [key for key in scores if key.startswith(f'sub_{FILES.index(name) + 1}_')]
        row = {'upstream_scores': {key: scores[key] for key in keys}, 'candidate_status': 'MISSING'}
        if path.is_file() and not path.is_symlink():
            row['candidate_sha256'] = digest(path)
            try:
                candidate = json.loads(path.read_text(encoding='utf-8'))
                source = json.loads((src / f'assets/config_migration/{name}_v1.json').read_text(encoding='utf-8'))
                row['independent_errors'] = independent_errors(source, candidate)
                row['candidate_status'] = 'CHECKED'
            except (ValueError, OSError) as exc:
                row['candidate_status'] = 'INVALID_JSON_OR_IO'
                row['error_type'] = type(exc).__name__
        details[name] = row
    return {'scope': 'ADAPTED_TASK_ONLY', 'upstream_grader_sha256': digest(QUAL / 'upstream_grader.py'),
            'cases': details, 'check_seconds': round(time.monotonic() - started, 3)}


def build_history(case: Path) -> None:
    case = case.resolve(strict=True)
    if RUNS.resolve() not in case.parents or not case.name.startswith('config-source__no_history__'):
        raise ValueError('history must use a recorded source-only episode')
    raw, receipt_path, check_path = case / 'raw.jsonl', case / 'receipt.json', case / 'independent_receipt.json'
    receipt = json.loads(receipt_path.read_text(encoding='utf-8'))
    check = json.loads(check_path.read_text(encoding='utf-8'))
    if receipt['task'] != 'config-source' or receipt['raw_sha256'] != digest(raw):
        raise ValueError('source trace changed')
    actions = []
    for line in raw.read_text(encoding='utf-8').splitlines():
        event = json.loads(line)
        if event.get('type') != 'tool_use':
            continue
        part = event.get('part', {})
        state = part.get('state', {})
        actions.append({'tool': part.get('tool'), 'status': state.get('status'),
                        'input': state.get('input', {}), 'output_tail': str(state.get('output', ''))[-2000:]})
    if not actions:
        raise ValueError('source contains no tool actions')
    output = case / 'work/outputs/webapp_v2.json'
    if not output.is_file() or output.is_symlink():
        raise ValueError('source output unavailable')
    content = {'source_instruction': (case / 'work/instructions.txt').read_text(encoding='utf-8'),
               'source_actions': actions, 'source_output': json.loads(output.read_text(encoding='utf-8')),
               'source_upstream_feedback': check['cases']['webapp']['upstream_scores'],
               'scope': 'all source tool actions, each output tail clipped to 2000 characters; source-only feedback'}
    encoded = json.dumps(content, ensure_ascii=False, separators=(',', ':'))
    pieces = [encoded[i:i + 700] for i in range(0, len(encoded), 700)]
    readable = ('Prior source task. The current task can differ. Concatenate the content after | on '
                'consecutive numbered lines to reconstruct the source-only JSON.\n'
                + ''.join(f'{i:04d}|{piece}\n' for i, piece in enumerate(pieces)))
    if ''.join(line.split('|', 1)[1] for line in readable.splitlines()[1:]) != encoded:
        raise ValueError('history wrapping is not lossless')
    history, meta = case / 'source_history.txt', case / 'source_history_metadata.json'
    if history.exists() or meta.exists():
        raise FileExistsError('refusing to overwrite source history')
    history.write_text(readable, encoding='utf-8')
    meta.write_text(json.dumps({'source_trace_sha256': digest(raw), 'source_receipt_sha256': digest(receipt_path),
                                'source_check_sha256': digest(check_path), 'source_output_sha256': digest(output),
                                'history_sha256': digest(history), 'action_count': len(actions),
                                'scope': content['scope']}, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'history': str(history), 'sha256': digest(history), 'actions': len(actions)}))


def summarize(output: Path) -> None:
    if output.exists():
        raise FileExistsError('refusing to overwrite a summary')
    cases = sorted(path for path in RUNS.iterdir() if path.is_dir())
    expected = {('config-source', 'no_history'), ('config-target', 'no_history'),
                ('config-target', 'source_history')}
    rows = {}
    for case in cases:
        match = re.fullmatch(r'(config-source|config-target)__(no_history|source_history)__\d+', case.name)
        if not match:
            raise ValueError(f'unexpected episode directory: {case.name}')
        key = match.groups()
        if key in rows:
            raise ValueError(f'duplicate episode: {key}')
        receipt = json.loads((case / 'receipt.json').read_text(encoding='utf-8'))
        check = json.loads((case / 'independent_receipt.json').read_text(encoding='utf-8'))
        if receipt['task'] != key[0] or receipt['raw_sha256'] != digest(case / 'raw.jsonl'):
            raise ValueError(f'episode receipt changed: {case.name}')
        file_status = {}
        for name, result in check['cases'].items():
            candidate = case / f'work/outputs/{name}_v2.json'
            if result['candidate_status'] == 'CHECKED' and digest(candidate) != result['candidate_sha256']:
                raise ValueError(f'candidate changed: {case.name}/{name}')
            file_status[name] = {'status': result['candidate_status'],
                                 'upstream_all_one': all(value == 1 for value in result['upstream_scores'].values()),
                                 'independent_error_count': len(result['independent_errors'])
                                 if result['candidate_status'] == 'CHECKED' else None}
        reads = []
        for line in (case / 'raw.jsonl').read_text(encoding='utf-8').splitlines():
            event = json.loads(line)
            part, state = event.get('part', {}), event.get('part', {}).get('state', {})
            if (event.get('type') == 'tool_use' and part.get('tool') == 'read'
                    and state.get('input', {}).get('filePath') == '/root/source_history.txt'):
                source = next(path for path in cases if path.name.startswith('config-source__no_history__'))
                expected_lines = (source / 'source_history.txt').read_text(encoding='utf-8').splitlines()
                shown = [m.groups() for row in str(state.get('output', '')).splitlines()
                         if (m := re.match(r'^(\d+): ?(.*)$', row))]
                exact = (len(shown) == len(expected_lines) and
                         all(int(number) == i and content == expected_lines[i - 1]
                             for i, (number, content) in enumerate(shown, 1)))
                reads.append({'status': state.get('status'), 'lines_match_source_history': exact})
        tokens = receipt['step_finish_tokens']
        calls = receipt['model_http_requests']
        rows[key] = {'episode': case.name, 'task': key[0], 'condition': key[1],
                     'agent_exit': receipt['agent_exit'], 'files': file_status,
                     'http_post': sum(call.startswith('POST ') for call in calls),
                     'denied': [call for call in calls if call.startswith('DENIED')],
                     'reported_tokens': sum(step.get('total', 0) for step in tokens),
                     'cache_read_included': sum(step.get('cache', {}).get('read', 0) for step in tokens),
                     'elapsed_seconds': receipt['elapsed_seconds'], 'history_reads': reads,
                     'raw_sha256': digest(case / 'raw.jsonl'),
                     'check_sha256': digest(case / 'independent_receipt.json')}
    if set(rows) != expected:
        raise ValueError(f'missing/unexpected episodes: {set(rows) ^ expected}')
    ordered = [rows[key] for key in sorted(rows)]
    result = {'scope': 'SOURCE_EXPOSED_SYNTHETIC_DEVELOPMENT_ONE_FAMILY_NOT_OFFICIAL_HARNESS',
              'manifest_sha256': digest(PACK / 'manifest.json'), 'cases': ordered,
              'total_http_post': sum(row['http_post'] for row in ordered),
              'total_reported_tokens': sum(row['reported_tokens'] for row in ordered),
              'total_cache_read_included': sum(row['cache_read_included'] for row in ordered),
              'note': 'Source execution included; cache reads already included in reported totals. '
                      'Reservations for the first three episodes retained final hashes but overwrote their STARTED metadata.'}
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'summary': str(output), 'sha256': digest(output),
                      'total_http_post': result['total_http_post'],
                      'total_reported_tokens': result['total_reported_tokens'],
                      'total_cache_read_included': result['total_cache_read_included']}))


def run(group: str, history: Path | None) -> None:
    item = verify_inputs(group)
    if history:
        history = history.resolve(strict=True)
        meta_path = history.parent / 'source_history_metadata.json'
        if group != 'config-target' or RUNS.resolve() not in history.parents or not meta_path.is_file():
            raise ValueError('history must originate inside the source episode output root')
        meta = json.loads(meta_path.read_text(encoding='utf-8'))
        if meta['history_sha256'] != digest(history) or meta['source_trace_sha256'] != digest(history.parent / 'raw.jsonl'):
            raise ValueError('source history provenance changed')
    code = derived_harness(group, history)
    RUNS.mkdir(parents=True, exist_ok=True)
    condition = 'source_history' if history else 'no_history'
    pending = RUNS / f'{group}__{condition}__{os.getpid()}.pending.json'
    if pending.exists():
        raise FileExistsError('episode reservation exists')
    reservation = {'group': group, 'condition': condition, 'inputs': item,
                   'adaptation_sha256': digest(PACK / 'manifest.json'),
                   'derived_sha256': hashlib.sha256(code.encode()).hexdigest(),
                   'history_sha256': digest(history) if history else None,
                   'status': 'STARTED'}
    pending.write_text(json.dumps(reservation, indent=2) + '\n', encoding='utf-8')
    old_argv = sys.argv
    namespace = {'__name__': '__main__'}
    try:
        sys.argv = [str(BASE), group, 'no_skill']
        exec(compile(code, str(BASE), 'exec'), namespace)
    finally:
        sys.argv = old_argv
    case = namespace['case']
    result = postcheck(group, case)
    (case / 'independent_receipt.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    reservation.update({'status': 'COMPLETED', 'case': str(case),
                        'case_receipt_sha256': digest(case / 'receipt.json'),
                        'independent_sha256': digest(case / 'independent_receipt.json')})
    pending.write_text(json.dumps(reservation, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'case': str(case), 'independent': result}, ensure_ascii=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--prepare', action='store_true')
    parser.add_argument('--preflight', action='store_true')
    parser.add_argument('--build-history', type=Path)
    parser.add_argument('--summarize', type=Path)
    parser.add_argument('--group', choices=GROUPS)
    parser.add_argument('--history', type=Path)
    args = parser.parse_args()
    if args.prepare:
        if args.group or args.history or args.preflight or args.build_history or args.summarize:
            parser.error('--prepare cannot be combined with an episode')
        prepare()
    elif args.build_history:
        if args.group or args.history or args.preflight or args.summarize:
            parser.error('--build-history cannot be combined with an episode')
        build_history(args.build_history)
    elif args.summarize:
        if args.group or args.history or args.preflight:
            parser.error('--summarize cannot be combined with an episode')
        summarize(args.summarize)
    elif args.preflight:
        if not args.group or args.history:
            parser.error('--preflight requires --group and no history')
        item = verify_inputs(args.group)
        code = derived_harness(args.group, None)
        print(json.dumps({'group': args.group, 'files': item['files'],
                          'derived_sha256': hashlib.sha256(code.encode()).hexdigest(),
                          'status': 'READY_NO_MODEL_CALL'}))
    elif args.group:
        run(args.group, args.history)
    else:
        parser.error('choose --prepare or --group')
