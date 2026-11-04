#!/usr/bin/env python3
"""Run isolated no-history agents on two qualified historical Django issues."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import sys
import tarfile

import pyarrow.parquet as pq
import qualify_swe_contextbench_django_20261104 as django
import qualify_swe_contextbench_sympy_20261104 as shared
import run_swe_contextbench_sympy_20261104 as core

ROOT = shared.ROOT / 'swe_contextbench_django_agent_20261104'
QUAL_SHA = '3c0e97a962c1607fb6aca351438a79c48b1b1528ae7e3f971bec099095094ff4'
REGRESSION_SHA = 'd18485d97cd01aa52150657fa48664eeb7efe8b1cb605e0144730d6bb7031e74'


def verify_base(task: str) -> None:
    spec = django.CASES[task]
    base, archive = django.OUT / task / 'clean_base', shared.ROOT / spec['archive']
    if shared.sha(archive) != spec['archive_sha'] or (base / '.git').exists():
        raise ValueError('Django source archive or history changed')
    expected, omitted = set(), []
    with tarfile.open(archive, 'r:gz') as stream:
        for member in stream:
            path = PurePosixPath(member.name)
            if path.is_absolute() or '..' in path.parts or not path.parts or path.parts[0] != 'django-' + spec['rev']:
                raise ValueError('unsafe archive path')
            if member.issym():
                if (not member.name.startswith('django-' + spec['rev'] + '/docs/_theme/djangodocs-epub/static/') or
                        not member.linkname.startswith('../../djangodocs/static/')):
                    raise ValueError('unexpected symbolic link')
                omitted.append(member.name)
                continue
            if not (member.isfile() or member.isdir()):
                raise ValueError('unexpected archive member')
            if member.isdir():
                continue
            output = base.joinpath(*path.parts[1:])
            if output.is_symlink() or not output.is_file():
                raise ValueError('Django clean tree changed')
            item = stream.extractfile(member)
            if item is None:
                raise ValueError('archive file missing')
            with item:
                if hashlib.sha256(item.read()).hexdigest() != shared.sha(output):
                    raise ValueError('Django clean source content changed')
            expected.add(output.relative_to(base).as_posix())
    actual = {p.relative_to(base).as_posix() for p in base.rglob('*') if p.is_file()}
    if actual != expected or len(omitted) != 4 or any(p.is_symlink() for p in base.rglob('*')):
        raise ValueError('Django clean source has unexpected files')


def derive(task: str, condition: str = 'none', experience: Path | None = None) -> str:
    code = core.derive(task, condition, experience)
    substitutions = ((str(core.ROOT), str(ROOT)), (str(shared.OUT), str(django.OUT)),
                     (str(shared.OVERLAY / 'site'), str(django.ENV / 'site')))
    for old, new in substitutions:
        if old not in code:
            raise ValueError('missing expected SymPy harness fragment')
        code = code.replace(old, new)
    compile(code, '<django-contextbench-harness>', 'exec')
    return code


def preflight() -> None:
    if (shared.sha(core.BASE) != core.BASE_SHA or shared.sha(django.OUT / 'receipt.json') != QUAL_SHA or
            shared.sha(django.OUT / 'full_regression_v2/receipt.json') != REGRESSION_SHA):
        raise ValueError('base harness or Django controls changed')
    shared.checked_dataset()
    control = json.loads((django.OUT / 'receipt.json').read_text(encoding='utf-8'))
    regression = json.loads((django.OUT / 'full_regression_v2/receipt.json').read_text(encoding='utf-8'))
    manifest_path = django.OUT / 'dependency_manifest.json'
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    site, wheels = django.ENV / 'site', django.ENV / 'wheelhouse'
    site_files = {p.relative_to(site).as_posix(): shared.sha(p) for p in sorted(site.rglob('*'))
                  if p.is_file() and not p.is_symlink()}
    if (shared.sha(manifest_path) != control['dependency_manifest_sha256'] or not control['dependencies_unchanged'] or
            site_files != manifest['site_files'] or
            {p.name: shared.sha(p) for p in sorted(wheels.glob('*.whl'))} != manifest['wheels']):
        raise ValueError('Django dependency overlay changed')
    ROOT.mkdir(parents=True, exist_ok=True)
    runtime = ROOT / 'runtime'
    runtime.mkdir(exist_ok=True)
    shim = runtime / 'sitecustomize.py'
    if shim.exists() and shim.read_text(encoding='utf-8') != core.SHIM:
        raise ValueError('runtime shim changed')
    if not shim.exists():
        shim.write_text(core.SHIM, encoding='utf-8')
    for task, spec in django.CASES.items():
        row, full = control['cases'][task], regression['cases'][task]
        if (row['base_commit'] != spec['rev'] or row['arms']['base_with_tests']['focus']['exit'] != 1 or
                row['arms']['gold_with_tests']['focus']['exit'] != 0 or
                any(arm['regression']['exit'] != 0 for arm in row['arms'].values()) or
                any(arm['exit'] != 0 for arm in full['arms'].values()) or
                shared.sha(django.OUT / task / 'task.txt') != row['problem_sha256']):
            raise ValueError('Django controls or issue identity mismatch')
        verify_base(task)
        derive(task)
        cmd = ['docker', 'run', '--rm', '--pull', 'never', '--network', 'none', '--read-only',
               '--cap-drop', 'ALL', '--security-opt', 'no-new-privileges',
               '--mount', f'type=bind,src={django.OUT / task / "clean_base"},dst=/workspace,readonly',
               '--mount', f'type=bind,src={site},dst=/extra,readonly',
               '-e', 'PYTHONPATH=/workspace:/extra', '-e', 'PYTHONDONTWRITEBYTECODE=1',
               '--workdir', '/workspace', '--entrypoint', 'python3', shared.IMAGE,
               '-c', 'import django, asgiref, sqlparse; print(django.get_version())']
        subprocess.run(cmd, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                       timeout=30, check=True)
    for condition in ('source_history', 'generated_skill'):
        derive('target', condition, Path('/tmp/preflight-django-experience.md'))
    print(json.dumps({'status': 'PREFLIGHT_PASS', 'scientific_model_calls': 0, 'qualified_cases': list(django.CASES)}))


def evaluate(task: str, case: Path) -> dict:
    work = case / 'work'
    links = [p.relative_to(work).as_posix() for p in work.rglob('*') if p.is_symlink()]
    if links:
        return {'status': 'UNRESOLVED_SYMLINK', 'links': links[:20]}
    out = case / 'post_run_evaluation'
    out.mkdir()
    copy = out / 'candidate'
    shutil.copytree(work, copy, ignore=shutil.ignore_patterns('.git', '__pycache__', '.pytest_cache',
                                                            'instructions.txt', 'opencode.json'))
    spec = django.CASES[task]
    rows = pq.read_table(shared.DATA / spec['data'], columns=['instance_id', 'test_patch']).to_pylist()
    row = next(item for item in rows if item['instance_id'] == spec['id'])
    frozen = json.loads((django.OUT / 'receipt.json').read_text(encoding='utf-8'))['cases'][task]
    if shared.sha_bytes(row['test_patch'].encode('utf-8')) != frozen['test_patch_sha256']:
        raise ValueError('Django hidden test patch changed')
    applied = shared.apply_patch(copy, row['test_patch'])
    result = {'status': 'TEST_PATCH_CONFLICT' if applied['apply_exit'] != 0 else 'EVALUATED',
              'test_patch': applied}
    if applied['apply_exit'] == 0:
        labels, unresolved = django.regression_labels(spec)
        result.update({'focus': django.test(copy, spec['focus'], out / 'focus.log', task + '-agent-focus'),
                       'regression': django.test(copy, labels, out / 'regression.log', task + '-agent-regression'),
                       'unresolved_regression_labels': unresolved})
    return result


def experience_file(condition: str) -> Path:
    directory = ROOT / 'source_experience'
    meta = json.loads((directory / 'metadata.json').read_text(encoding='utf-8'))
    name = {'source_history': 'source_history.md', 'generated_skill': 'generated_skill.md'}[condition]
    path = directory / name
    key = 'history_sha256' if condition == 'source_history' else 'skill_sha256'
    if shared.sha(path) != meta.get(key):
        raise ValueError('Django source experience changed or missing')
    return path


def build_experience() -> None:
    """Construct source-only clipped action history plus actual source feedback."""
    preflight()
    case = ROOT / f'source__none__seed{core.SEED}'
    completed = ROOT / f'source__none__seed{core.SEED}.completed.json'
    plan = json.loads(completed.read_text(encoding='utf-8'))
    raw = case / 'raw.jsonl'
    feedback = plan['post_run_evaluation']
    if (shared.sha(raw) != plan['raw_sha256'] or feedback['status'] != 'EVALUATED' or
            not feedback.get('focus') or not feedback.get('regression')):
        raise ValueError('Django source episode or feedback is incomplete')
    actions = []
    for line in raw.read_text(encoding='utf-8').splitlines():
        event = json.loads(line)
        if event.get('type') != 'tool_use':
            continue
        part, state = event.get('part', {}), event.get('part', {}).get('state', {})
        inp = json.dumps(state.get('input', {}), ensure_ascii=False, separators=(',', ':'))
        output = str(state.get('output', ''))
        actions.append({'tool': part.get('tool'), 'status': state.get('status'),
                        'input_prefix': inp[:600], 'input_chars': len(inp),
                        'input_sha256': shared.sha_bytes(inp.encode('utf-8')),
                        'output_tail': output[-800:], 'output_chars': len(output),
                        'output_sha256': shared.sha_bytes(output.encode('utf-8'))})
    if not actions:
        raise ValueError('Django source episode has no tool actions')
    base, work = django.OUT / 'source/clean_base', case / 'work'
    def files(root: Path) -> dict:
        return {p.relative_to(root).as_posix(): shared.sha(p) for p in root.rglob('*')
                if p.is_file() and not p.is_symlink() and p.name not in ('instructions.txt', 'opencode.json')
                and not any(part in ('.git', '__pycache__', '.pytest_cache') for part in p.parts)}
    before, after = files(base), files(work)
    changed = sorted(k for k in before.keys() | after.keys() if before.get(k) != after.get(k))
    log = (case / 'post_run_evaluation/focus.log').read_text(encoding='utf-8', errors='replace')
    content = {'source_task': (django.OUT / 'source/task.txt').read_text(encoding='utf-8'),
               'source_actions': actions, 'source_changed_paths': changed,
               'source_feedback': {'agent_exit': plan['agent_exit'], 'request_limit_reached': bool(plan['denied']),
                                   'focus_exit': feedback['focus']['exit'],
                                   'focus_summary': feedback['focus']['summary'],
                                   'regression_exit': feedback['regression']['exit'],
                                   'regression_summary': feedback['regression']['summary'],
                                   'unresolved_regression_count': len(feedback['unresolved_regression_labels']),
                                   'focus_log_tail': log[-2000:]},
               'scope': 'all recorded source tool actions with clipped fields, changed paths, '
                        'source-only post-run feedback; no target issue or target tests'}
    encoded = json.dumps(content, ensure_ascii=False, separators=(',', ':'))
    if '35356' in encoded or 'recursive relationships in select_related() and only()' in encoded.lower():
        raise ValueError('Django source history contains a literal target marker')
    pieces = [encoded[i:i + 700] for i in range(0, len(encoded), 700)]
    readable = ('Source-only task history. The current task may differ. Concatenate text after | '
                'on numbered lines to reconstruct the JSON.\n' +
                ''.join(f'{i:04d}|{piece}\n' for i, piece in enumerate(pieces)))
    if ''.join(line.split('|', 1)[1] for line in readable.splitlines()[1:]) != encoded:
        raise ValueError('Django history wrapping changed content')
    out = ROOT / 'source_experience'
    out.mkdir(exist_ok=False)
    history = out / 'source_history.md'
    history.write_text(readable, encoding='utf-8')
    metadata = {'source_raw_sha256': shared.sha(raw), 'source_completion_sha256': shared.sha(completed),
                'history_sha256': shared.sha(history), 'actions': len(actions), 'history_chars': len(readable),
                'changed_paths': changed, 'clipped_inputs': sum(x['input_chars'] > 600 for x in actions),
                'clipped_outputs': sum(x['output_chars'] > 800 for x in actions),
                'target_marker_screen': 'NO_LITERAL_MATCH; semantic or model pretraining leakage remains unknown',
                'scope': content['scope']}
    (out / 'metadata.json').write_text(json.dumps(metadata, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'history': str(history), 'metadata': metadata}, ensure_ascii=False))


def generate_skill() -> None:
    """Reuse the same source-only local-model skill generator and ledger."""
    old_root, old_preflight = core.ROOT, core.preflight
    try:
        core.ROOT, core.preflight = ROOT, preflight
        core.generate_skill()
    finally:
        core.ROOT, core.preflight = old_root, old_preflight


def run(task: str, condition: str) -> None:
    preflight()
    experience = None if condition == 'none' else experience_file(condition)
    case = ROOT / f'{task}__{condition}__seed{core.SEED}'
    started = ROOT / f'{task}__{condition}__seed{core.SEED}.started.json'
    complete = ROOT / f'{task}__{condition}__seed{core.SEED}.completed.json'
    harness = ROOT / f'{task}__{condition}__seed{core.SEED}.harness.py'
    if any(path.exists() for path in (case, started, complete, harness)):
        raise FileExistsError('Django task already attempted')
    harness.write_text(derive(task, condition, experience), encoding='utf-8')
    plan = {'task': task, 'condition': condition, 'seed': core.SEED, 'temperature': core.TEMPERATURE,
            'base_sha256': core.BASE_SHA, 'qualification_sha256': QUAL_SHA, 'regression_sha256': REGRESSION_SHA,
            'harness_sha256': shared.sha(harness), 'shim_sha256': shared.sha(ROOT / 'runtime/sitecustomize.py'),
            'max_http_requests': core.MAX_HTTP_REQUESTS, 'max_bytes': core.MAX_BYTES,
            'max_seconds': core.MAX_SECONDS, 'experience_sha256': shared.sha(experience) if experience else None,
            'status': 'STARTED'}
    started.write_text(json.dumps(plan, indent=2) + '\n', encoding='utf-8')
    proc = subprocess.run([sys.executable, str(harness), task, 'no_skill'], stdin=subprocess.DEVNULL,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=core.MAX_SECONDS + 120)
    (ROOT / f'{task}__{condition}__seed{core.SEED}.runner.stdout').write_bytes(proc.stdout)
    (ROOT / f'{task}__{condition}__seed{core.SEED}.runner.stderr').write_bytes(proc.stderr)
    plan.update({'runner_exit': proc.returncode, 'started_sha256': shared.sha(started)})
    if proc.returncode == 0 and (case / 'receipt.json').is_file():
        receipt = json.loads((case / 'receipt.json').read_text(encoding='utf-8'))
        log = case / 'sampling_metadata.jsonl'
        metadata = [json.loads(line) for line in log.read_text(encoding='utf-8').splitlines()] if log.is_file() else []
        same = Counter(json.dumps(x, sort_keys=True) for x in metadata) == Counter(
            json.dumps(x, sort_keys=True) for x in receipt['sampling_metadata'])
        if not same or shared.sha(case / 'raw.jsonl') != receipt['raw_sha256']:
            raise ValueError('Django agent receipt changed')
        read_info = None
        if experience:
            if shared.sha(experience) != plan['experience_sha256']:
                raise ValueError('Django source experience changed during execution')
            expected_lines = experience.read_text(encoding='utf-8').splitlines()
            seen, reads = {}, 0
            for line in (case / 'raw.jsonl').read_text(encoding='utf-8').splitlines():
                event = json.loads(line)
                part, state = event.get('part', {}), event.get('part', {}).get('state', {})
                if (event.get('type') == 'tool_use' and part.get('tool') == 'read' and
                        state.get('input', {}).get('filePath') == '/root/source_experience.md'):
                    reads += 1
                    for entry in str(state.get('output', '')).splitlines():
                        match = re.match(r'^(\d+): ?(.*)$', entry)
                        if match:
                            index = int(match.group(1))
                            if index in seen and seen[index] != match.group(2):
                                raise ValueError('inconsistent Django experience read')
                            seen[index] = match.group(2)
            read_info = {'read_calls': reads, 'lines_seen': len(seen), 'lines_total': len(expected_lines),
                         'complete_exact_read': len(seen) == len(expected_lines) and all(
                             seen.get(i) == expected_lines[i - 1] for i in range(1, len(expected_lines) + 1))}
        plan.update({'status': 'COMPLETED', 'agent_exit': receipt['agent_exit'],
                     'posts': sum(x.startswith('POST ') for x in receipt['model_http_requests']),
                     'denied': [x for x in receipt['model_http_requests'] if x.startswith('DENIED')],
                     'reported_tokens': sum(x.get('total', 0) for x in receipt['step_finish_tokens']),
                     'cache_read_included': sum(x.get('cache', {}).get('read', 0)
                                                for x in receipt['step_finish_tokens']),
                     'seed_and_temperature_forwarded': bool(metadata) and all(
                         x['seed'] == core.SEED and x['temperature'] == core.TEMPERATURE for x in metadata),
                     'raw_sha256': receipt['raw_sha256'], 'experience_read': read_info,
                     'post_run_evaluation': evaluate(task, case)})
    else:
        plan['status'] = 'RUNNER_ERROR_REVIEW_RAW_AND_PROXY_LOG'
    complete.write_text(json.dumps(plan, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'receipt': str(complete), 'sha256': shared.sha(complete), 'result': plan}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--preflight', action='store_true')
    parser.add_argument('--build-experience', action='store_true')
    parser.add_argument('--generate-skill', action='store_true')
    parser.add_argument('--task', choices=('source', 'target'))
    parser.add_argument('--condition', choices=('none', 'source_history', 'generated_skill'), default='none')
    args = parser.parse_args()
    if args.preflight:
        preflight()
    elif args.build_experience:
        build_experience()
    elif args.generate_skill:
        generate_skill()
    elif args.task:
        run(args.task, args.condition)
    else:
        parser.error('choose --preflight or --task')
