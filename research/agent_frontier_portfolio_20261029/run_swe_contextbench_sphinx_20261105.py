#!/usr/bin/env python3
"""Isolated no-history Sphinx agent episodes with post-run restored-test scoring."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import re
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import sys
import tarfile

import pyarrow.parquet as pq
import qualify_swe_contextbench_sphinx_20261105 as qual
import qualify_swe_contextbench_sympy_20261104 as shared
import run_swe_contextbench_sympy_20261104 as core
import build_source_status_control_20261105 as status_control

ROOT = qual.ROOT / 'swe_contextbench_sphinx_agent_20261105'
CONTROL_SHA = 'b2ad10dcce9c8656e465d174aed570a015344538fb8f213bfec21c5e95ca4ab6'
RECHECK_SHA = '65bc205313e0f2aa60f58e2c4903eec164cb127ae6ed366a1352f4c67e323f7a'
SITE_SHA = 'd49caee193deb2158dbe8796be7e40fd72c3fa9abdd3db749719b9336d66e52b'


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def row_for(task: str) -> dict:
    ident, dataset, rev, _ = qual.CASES[task]
    columns = ['instance_id', 'base_commit', 'problem_statement', 'test_patch', 'FAIL_TO_PASS', 'PASS_TO_PASS']
    rows = [row for row in pq.read_table(qual.DATA / dataset, columns=columns).to_pylist()
            if row['instance_id'] == ident]
    if len(rows) != 1 or rows[0]['base_commit'] != rev:
        raise ValueError('dataset task or revision changed')
    return rows[0]


def verify_clean(task: str) -> None:
    _, _, rev, archive_sha = qual.CASES[task]
    base = qual.OUT / task / 'clean_base'
    archive = qual.SOURCE / f'{task}.tar.gz'
    if sha(archive) != archive_sha or (base / '.git').exists():
        raise ValueError('archive or history boundary changed')
    expected = {}
    with tarfile.open(archive, 'r:gz') as stream:
        for member in stream:
            p = PurePosixPath(member.name)
            if (not p.parts or p.parts[0] != 'sphinx-' + rev or p.is_absolute() or '..' in p.parts
                    or not (member.isfile() or member.isdir())):
                raise ValueError('unsafe archive member')
            if member.isfile():
                with stream.extractfile(member) as data:
                    expected[PurePosixPath(*p.parts[1:]).as_posix()] = hashlib.sha256(data.read()).hexdigest()
    actual = {p.relative_to(base).as_posix(): sha(p) for p in base.rglob('*') if p.is_file()}
    if actual != expected or any(p.is_symlink() for p in base.rglob('*')):
        raise ValueError('clean base differs from frozen archive')


def derive(task: str, condition: str = 'none', experience: Path | None = None) -> str:
    underlying = 'generated_skill' if condition in ('source_status', 'length_control') else condition
    code = core.derive(task, underlying, experience)
    substitutions = ((str(core.ROOT), str(ROOT)), (str(shared.OUT), str(qual.OUT)),
                     (str(shared.DEPS), str(qual.SITE)), (str(shared.OVERLAY / 'site'), str(qual.LEGACY)))
    for old, new in substitutions:
        if old not in code:
            raise ValueError('missing expected harness fragment')
        code = code.replace(old, new)
    if underlying != condition:
        code = core.replace_once(code, str(ROOT / f'{task}__generated_skill__seed{core.SEED}'),
                                 str(ROOT / f'{task}__{condition}__seed{core.SEED}'))
    code = core.replace_once(code, "(src/'task.txt').read_text(encoding='utf8').strip()",
                             f"Path({str(ROOT / 'task_inputs' / (task + '.txt'))!r}).read_text(encoding='utf8').strip()")
    code = core.replace_once(code, "'-e','PYTHONPATH=/runtime:/extra:/deps'",
                             "'-e','PYTHONPATH=/deps','-e','PATH=/extra/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin'")
    code = core.replace_once(code, "(work/'instructions.txt').write_text(body,encoding='utf8')",
                             "(work/'instructions.txt').write_text(body,encoding='utf8')\n"
                             "(case/'frozen_instructions.txt').write_bytes((work/'instructions.txt').read_bytes())")
    compile(code, '<sphinx-agent-harness>', 'exec')
    return code


def preflight() -> None:
    if (sha(core.BASE) != core.BASE_SHA or sha(qual.OUT / 'receipt.json') != CONTROL_SHA or
            sha(qual.OUT / 'target/regression_recheck_v1/receipt.json') != RECHECK_SHA or
            sha(qual.SOURCE / 'site_manifest_20261105.json') != SITE_SHA):
        raise ValueError('harness, qualification or environment manifest changed')
    shared.checked_dataset()
    manifest = json.loads((qual.SOURCE / 'site_manifest_20261105.json').read_text(encoding='utf8'))
    actual = {p.relative_to(qual.SITE).as_posix(): sha(p) for p in sorted(qual.SITE.rglob('*')) if p.is_file()}
    if actual != manifest['files'] or sha(qual.LEGACY / 'bin/python3.8') != manifest['python_sha256']:
        raise ValueError('Python environment changed')
    control = json.loads((qual.OUT / 'receipt.json').read_text(encoding='utf8'))
    target_recheck = json.loads((qual.OUT / 'target/regression_recheck_v1/receipt.json').read_text(encoding='utf8'))
    source = control['cases']['source']['arms']
    target = control['cases']['target']['arms']
    if (source['base']['focus']['exit'] != 1 or source['gold']['focus']['exit'] != 0 or
            any(source[x]['regression']['exit'] != 0 for x in ('base', 'gold')) or
            target['base']['focus']['exit'] != 4 or target['gold']['focus']['exit'] != 0 or
            len(target_recheck['mapped']) != 18 or any(target_recheck['arms'][x]['exit'] != 0 for x in ('base', 'gold'))):
        raise ValueError('test controls do not qualify')
    ROOT.mkdir(parents=True, exist_ok=True)
    (ROOT / 'runtime').mkdir(exist_ok=True)
    shim = ROOT / 'runtime/sitecustomize.py'
    if shim.exists() and shim.read_text(encoding='utf8') != core.SHIM:
        raise ValueError('shim changed')
    if not shim.exists():
        shim.write_text(core.SHIM, encoding='utf8')
    inputs = ROOT / 'task_inputs'
    inputs.mkdir(exist_ok=True)
    for task in ('source', 'target'):
        verify_clean(task)
        text = row_for(task)['problem_statement']
        path = inputs / f'{task}.txt'
        if path.exists() and path.read_bytes() != text.encode('utf8'):
            raise ValueError('task text changed')
        if not path.exists():
            path.write_bytes(text.encode('utf8'))
        derive(task)
        cmd = ['docker', 'run', '--rm', '--pull', 'never', '--network', 'none', '--read-only',
               '--cap-drop', 'ALL', '--security-opt', 'no-new-privileges',
               '--mount', f'type=bind,src={qual.OUT / task / "clean_base"},dst=/workspace,readonly',
               '--mount', f'type=bind,src={qual.LEGACY},dst=/extra,readonly',
               '--mount', f'type=bind,src={qual.SITE},dst=/deps,readonly',
               '-e', 'PYTHONPATH=/workspace:/deps', '--workdir', '/workspace',
               '--entrypoint', '/extra/bin/python', qual.IMAGE,
               '-c', 'import sphinx,pytest,docutils; print(sphinx.__version__,pytest.__version__)']
        subprocess.run(cmd, stdin=subprocess.DEVNULL, capture_output=True, timeout=30, check=True)
    print(json.dumps({'status': 'PREFLIGHT_PASS', 'scientific_model_calls': 0}))


def evaluate(task: str, case: Path) -> dict:
    work = case / 'work'
    if any(p.is_symlink() for p in work.rglob('*')):
        return {'status': 'UNRESOLVED_SYMLINK'}
    out = case / 'post_run_evaluation_restored_tests'
    out.mkdir()
    copy = out / 'candidate'
    standard = shutil.ignore_patterns('.git', '__pycache__', '.pytest_cache', 'instructions.txt', 'opencode.json')
    def ignore(path, names):
        excluded = set(standard(path, names))
        if Path(path) == work and 'tests' in names:
            excluded.add('tests')
        return excluded
    shutil.copytree(work, copy, ignore=ignore)
    verify_clean(task)
    shutil.copytree(qual.OUT / task / 'clean_base/tests', copy / 'tests')
    row = row_for(task)
    control = json.loads((qual.OUT / 'receipt.json').read_text(encoding='utf8'))['cases'][task]['arms']['base']
    patch = row['test_patch']
    if hashlib.sha256(patch.encode('utf8')).hexdigest() != control['test_patch']['sha256']:
        raise ValueError('hidden test patch changed')
    applied = qual.apply_patch(copy, patch, out / 'test.patch')
    result = {'status': 'TEST_PATCH_CONFLICT', 'test_source': 'FROZEN_BASE', 'test_patch': applied}
    if len(applied['steps']) == 2 and all(x['exit'] == 0 for x in applied['steps']):
        labels = json.loads(row['PASS_TO_PASS'])
        if task == 'target':
            checked = json.loads((qual.OUT / 'target/regression_recheck_v1/receipt.json').read_text(encoding='utf8'))
            if labels != checked['original']:
                raise ValueError('regression labels changed')
            labels = checked['mapped']
        result.update({'status': 'EVALUATED',
                       'focus': qual.run_test(copy, json.loads(row['FAIL_TO_PASS']), out / 'focus.log', task + 'agentfocus'),
                       'regression': qual.run_test(copy, labels, out / 'regression.log', task + 'agentregression')})
    return result


def experience_file(condition: str) -> Path:
    directory = ROOT / 'source_experience'
    meta = json.loads((directory / 'metadata.json').read_text(encoding='utf8'))
    if condition in ('source_status', 'length_control'):
        control = json.loads((directory / 'status_control/receipt.json').read_text(encoding='utf8'))
        path = directory / 'status_control' / (condition + '.md')
        if (control['input_history_sha256'] != meta['history_sha256'] or
                control['input_skill_sha256'] != meta['skill_sha256'] or
                sha(directory / 'source_history.md') != meta['history_sha256'] or
                sha(directory / 'generated_skill.md') != meta['skill_sha256'] or
                sha(path) != control['artifacts'][condition]['sha256']):
            raise ValueError('source status control changed')
        expected = status_control.build((directory / 'source_history.md').read_bytes(),
                                        (directory / 'generated_skill.md').read_bytes(),
                                        meta['history_sha256'], meta['skill_sha256'])
        if path.read_bytes() != expected['outputs'][condition].encode('utf8'):
            raise ValueError('status text differs from deterministic source-only control')
    else:
        name, key = {'source_history': ('source_history.md', 'history_sha256'),
                     'generated_skill': ('generated_skill.md', 'skill_sha256')}[condition]
        path = directory / name
        if sha(path) != meta.get(key):
            raise ValueError('source experience changed')
    if condition != 'source_history':
        ledger = json.loads((directory / 'skill_generation_ledger.json').read_text(encoding='utf8'))
        if (ledger['status'] != 'RECEIVED' or ledger['http_attempts'] != 1 or
                ledger['source_history_sha256'] != meta['history_sha256'] or
                ledger['skill_sha256'] != meta['skill_sha256'] or
                sha(directory / 'skill_generation_request.json') != ledger['request_sha256'] or
                sha(directory / 'skill_generation_response.json') != ledger['response_sha256']):
            raise ValueError('skill generation provenance changed')
    if (sha(ROOT / f'source__none__seed{core.SEED}.completed.json') !=
            meta['source_completion_sha256'] or sha(ROOT / f'source__none__seed{core.SEED}/raw.jsonl') !=
            meta['source_raw_sha256'] or
            sha(ROOT / f'source__none__seed{core.SEED}/post_run_evaluation_restored_tests/focus.log') !=
            meta['source_focus_log_sha256'] or
            sha(ROOT / f'source__none__seed{core.SEED}/post_run_evaluation_restored_tests/regression.log') !=
            meta['source_regression_log_sha256']):
        raise ValueError('source experience or source episode changed')
    if target_marker_hits(path.read_text(encoding='utf8')):
        raise ValueError('experience contains a literal target marker')
    return path


def target_marker_hits(text: str) -> list[str]:
    # Literal screening reduces accidental leakage; it cannot rule out semantic leakage.
    return [marker for marker in ('sphinx-doc__sphinx-8588', '#8588', 'test_TypeAliasNamespace')
            if marker.casefold() in text.casefold()]


def forbid_target_exposure() -> None:
    if list(ROOT.glob('target__*.started.json')):
        raise ValueError('cannot create or modify source experience after target has started')


def build_experience() -> None:
    """Create a clipped history from source actions and independent source-only scores."""
    preflight()
    forbid_target_exposure()
    case = ROOT / f'source__none__seed{core.SEED}'
    completed = ROOT / f'source__none__seed{core.SEED}.completed.json'
    plan = json.loads(completed.read_text(encoding='utf8'))
    raw = case / 'raw.jsonl'
    feedback = plan['post_run_evaluation']
    if (plan['status'] != 'COMPLETED' or sha(raw) != plan['raw_sha256'] or
            feedback['status'] != 'EVALUATED' or not feedback.get('focus') or not feedback.get('regression')):
        raise ValueError('source episode or independent feedback incomplete')
    raw_text = raw.read_text(encoding='utf8')
    if target_marker_hits(raw_text):
        raise ValueError('source raw contains a literal target marker')
    actions = []
    for line in raw_text.splitlines():
        event = json.loads(line)
        if event.get('type') != 'tool_use':
            continue
        part = event.get('part', {})
        state = part.get('state', {})
        inp = json.dumps(state.get('input', {}), ensure_ascii=False, separators=(',', ':'))
        output = str(state.get('output', ''))
        actions.append({'tool': part.get('tool'), 'status': state.get('status'),
                        'input_prefix': inp[:600], 'input_chars': len(inp),
                        'input_sha256': hashlib.sha256(inp.encode('utf8')).hexdigest(),
                        'output_tail': output[-800:], 'output_chars': len(output),
                        'output_sha256': hashlib.sha256(output.encode('utf8')).hexdigest()})
    if not actions:
        raise ValueError('source episode has no tool actions')
    def files(root: Path) -> dict:
        return {p.relative_to(root).as_posix(): sha(p) for p in root.rglob('*')
                if p.is_file() and not p.is_symlink() and p.name not in ('instructions.txt', 'opencode.json')
                and not any(part in ('.git', '__pycache__', '.pytest_cache') for part in p.parts)}
    before, after = files(qual.OUT / 'source/clean_base'), files(case / 'work')
    changed = sorted(k for k in before.keys() | after.keys() if before.get(k) != after.get(k))
    feedback_dir = case / 'post_run_evaluation_restored_tests'
    if (sha(feedback_dir / 'focus.log') != feedback['focus']['log_sha256'] or
            sha(feedback_dir / 'regression.log') != feedback['regression']['log_sha256'] or
            feedback.get('test_source') != 'FROZEN_BASE'):
        raise ValueError('independent source-only feedback logs changed')
    log = (feedback_dir / 'focus.log').read_text(encoding='utf8', errors='replace')
    content = {'source_task': (ROOT / 'task_inputs/source.txt').read_text(encoding='utf8'),
               'source_actions': actions, 'source_changed_paths': changed,
               'source_feedback': {'agent_exit': plan['agent_exit'],
                                   'request_limit_reached': (True if plan['posts'] >= core.MAX_HTTP_REQUESTS else
                                                             None if plan['denied'] else False),
                                   'focus_exit': feedback['focus']['exit'],
                                   'focus_log_tail': log[-2000:],
                                   'regression_exit': feedback['regression']['exit'],
                                   'regression_log_tail': feedback['regression']['log_tail'][-8:]},
               'scope': 'clipped source actions, source file changes, independent source-only feedback; '
                        'no target task or target tests'}
    encoded = json.dumps(content, ensure_ascii=False, separators=(',', ':'))
    if target_marker_hits(encoded):
        raise ValueError('source history contains a literal target marker')
    pieces = [encoded[i:i + 700] for i in range(0, len(encoded), 700)]
    readable = ('Source-only task history. The current task may differ. Concatenate text after | '
                'on numbered lines to reconstruct the JSON.\n' +
                ''.join(f'{i:04d}|{piece}\n' for i, piece in enumerate(pieces)))
    if ''.join(line.split('|', 1)[1] for line in readable.splitlines()[1:]) != encoded:
        raise ValueError('history wrapping changed source content')
    out = ROOT / 'source_experience'
    out.mkdir(exist_ok=False)
    history = out / 'source_history.md'
    history.write_text(readable, encoding='utf8')
    metadata = {'source_raw_sha256': sha(raw), 'source_completion_sha256': sha(completed),
                'history_sha256': sha(history), 'source_focus_log_sha256': sha(feedback_dir / 'focus.log'),
                'source_regression_log_sha256': sha(feedback_dir / 'regression.log'),
                'actions': len(actions), 'history_chars': len(readable), 'changed_paths': changed,
                'clipped_inputs': sum(x['input_chars'] > 600 for x in actions),
                'clipped_outputs': sum(x['output_chars'] > 800 for x in actions),
                'target_marker_screen': 'NO_LITERAL_MATCH; semantic leakage and model pretraining exposure remain unknown',
                'scope': content['scope']}
    (out / 'metadata.json').write_text(json.dumps(metadata, indent=2) + '\n', encoding='utf8')
    print(json.dumps({'history': str(history), 'metadata': metadata}, ensure_ascii=False))


def generate_skill() -> None:
    """Use the previously audited generator; its request/response and usage are retained."""
    forbid_target_exposure()
    experience_file('source_history')
    old_root, old_preflight = core.ROOT, core.preflight
    try:
        core.ROOT, core.preflight = ROOT, preflight
        core.generate_skill()
    finally:
        core.ROOT, core.preflight = old_root, old_preflight


def build_status_control() -> None:
    """Attach verified source-only status to the unchanged generated skill."""
    preflight()
    forbid_target_exposure()
    history = experience_file('source_history')
    skill = experience_file('generated_skill')
    result = status_control.build(history.read_bytes(), skill.read_bytes(), sha(history), sha(skill))
    out = history.parent / 'status_control'
    out.mkdir(exist_ok=False)
    artifacts = {}
    for name, text in result.pop('outputs').items():
        path = out / (name + '.md')
        path.write_bytes(text.encode('utf8'))
        artifacts[name] = {'sha256': sha(path), 'characters': len(text)}
    result['artifacts'] = artifacts
    result['scientific_model_calls'] = 0
    receipt = out / 'receipt.json'
    receipt.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
    print(json.dumps({'receipt': str(receipt), 'sha256': sha(receipt), 'artifacts': artifacts}))


def inspect_experience_reads(raw: Path, experience: Path, read_path: str = '/root/source_experience.md') -> dict:
    expected = experience.read_text(encoding='utf8').splitlines()
    seen, reads, other_path_mentions = {}, 0, 0
    for line in raw.read_text(encoding='utf8').splitlines():
        event = json.loads(line)
        part = event.get('part', {})
        state = part.get('state', {})
        if event.get('type') != 'tool_use':
            continue
        inp = state.get('input', {})
        if part.get('tool') != 'read' or inp.get('filePath') != read_path:
            other_path_mentions += int(Path(read_path).name in json.dumps(inp, ensure_ascii=False))
            continue
        reads += 1
        for entry in str(state.get('output', '')).splitlines():
            match = re.match(r'^(\d+): ?(.*)$', entry)
            if match:
                index = int(match.group(1))
                if index in seen and seen[index] != match.group(2):
                    raise ValueError('inconsistent experience read')
                seen[index] = match.group(2)
    return {'scope': 'read tool only; other path mentions need raw inspection', 'read_calls': reads,
            'other_path_mentions': other_path_mentions, 'lines_seen': len(seen), 'lines_total': len(expected),
            'complete_exact_read': len(seen) == len(expected) and all(
                seen.get(i) == expected[i - 1] for i in range(1, len(expected) + 1))}


def run(task: str, condition: str = 'none') -> None:
    preflight()
    if task == 'source' and condition != 'none':
        raise ValueError('source only supports no history')
    frozen = None
    if task == 'target':
        # Freeze all compared artifacts before *any* target outcome is observed.
        frozen = {arm: sha(experience_file(arm)) for arm in
                  ('source_history', 'generated_skill', 'source_status', 'length_control')}
        frozen['status_control_receipt'] = sha(ROOT / 'source_experience/status_control/receipt.json')
        frozen['skill_generation_ledger'] = sha(ROOT / 'source_experience/skill_generation_ledger.json')
        frozen['source_completion'] = sha(ROOT / f'source__none__seed{core.SEED}.completed.json')
        for previous in ROOT.glob('target__*.started.json'):
            if json.loads(previous.read_text(encoding='utf8')).get('frozen_experience') != frozen:
                raise ValueError('target arm must use the same frozen source and experience artifacts')
    experience = None if condition == 'none' else experience_file(condition)
    case = ROOT / f'{task}__{condition}__seed{core.SEED}'
    started = ROOT / f'{task}__{condition}__seed{core.SEED}.started.json'
    complete = ROOT / f'{task}__{condition}__seed{core.SEED}.completed.json'
    harness = ROOT / f'{task}__{condition}__seed{core.SEED}.harness.py'
    if any(p.exists() for p in (case, started, complete, harness)):
        raise FileExistsError('episode already attempted')
    harness.write_text(derive(task, condition, experience), encoding='utf8')
    plan = {'status': 'STARTED', 'task': task, 'condition': condition, 'seed': core.SEED, 'temperature': core.TEMPERATURE,
            'max_http_requests': core.MAX_HTTP_REQUESTS, 'max_bytes': core.MAX_BYTES,
            'max_seconds': core.MAX_SECONDS, 'harness_sha256': sha(harness),
            'task_text_sha256': sha(ROOT / 'task_inputs' / f'{task}.txt'), 'experience_sha256': sha(experience) if experience else None,
            'qualification_sha256': CONTROL_SHA, 'environment_manifest_sha256': SITE_SHA,
            'status_control_receipt_sha256': sha(ROOT / 'source_experience/status_control/receipt.json') if task == 'target' else None,
            'frozen_experience': frozen,
            'runtime_scope': 'Python 3.8 interpreter and site mounted read-only; shared conda libraries not fully frozen'}
    started.write_text(json.dumps(plan, indent=2) + '\n', encoding='utf8')
    proc = subprocess.run([sys.executable, str(harness), task, 'no_skill'], stdin=subprocess.DEVNULL,
                          capture_output=True, timeout=core.MAX_SECONDS + 120)
    (ROOT / f'{task}__{condition}__seed{core.SEED}.runner.stdout').write_bytes(proc.stdout)
    (ROOT / f'{task}__{condition}__seed{core.SEED}.runner.stderr').write_bytes(proc.stderr)
    plan.update({'runner_exit': proc.returncode, 'started_sha256': sha(started)})
    if proc.returncode == 0 and (case / 'receipt.json').is_file():
        receipt = json.loads((case / 'receipt.json').read_text(encoding='utf8'))
        log = case / 'sampling_metadata.jsonl'
        metadata = [json.loads(line) for line in log.read_text(encoding='utf8').splitlines()] if log.is_file() else []
        if (Counter(json.dumps(x, sort_keys=True) for x in metadata) != Counter(
                json.dumps(x, sort_keys=True) for x in receipt['sampling_metadata']) or
                sha(case / 'raw.jsonl') != receipt['raw_sha256']):
            raise ValueError('agent receipt changed')
        instructions = case / 'frozen_instructions.txt'
        expected_instruction = (ROOT / 'task_inputs' / f'{task}.txt').read_text(encoding='utf8').strip().encode('utf8')
        if instructions.read_bytes() != expected_instruction:
            raise ValueError('actual initial instructions differ from normalized task input')
        instruction_read = inspect_experience_reads(case / 'raw.jsonl', instructions, '/root/instructions.txt')
        read_info = None
        if experience:
            if sha(experience) != plan['experience_sha256']:
                raise ValueError('experience changed during execution')
            read_info = inspect_experience_reads(case / 'raw.jsonl', experience)
        plan.update({'status': 'COMPLETED', 'agent_exit': receipt['agent_exit'],
                     'posts': sum(x.startswith('POST ') for x in receipt['model_http_requests']),
                     'denied': [x for x in receipt['model_http_requests'] if x.startswith('DENIED')],
                     'reported_tokens': sum(x.get('total', 0) for x in receipt['step_finish_tokens']),
                     'cache_read_included': sum(x.get('cache', {}).get('read', 0) for x in receipt['step_finish_tokens']),
                     'seed_and_temperature_forwarded': bool(metadata) and all(
                         x['seed'] == core.SEED and x['temperature'] == core.TEMPERATURE for x in metadata),
                     'raw_sha256': receipt['raw_sha256'], 'initial_instructions_sha256': sha(instructions),
                     'initial_instructions_read': instruction_read, 'experience_read': read_info,
                     'post_run_evaluation': evaluate(task, case)})
    else:
        plan['status'] = 'RUNNER_ERROR_REVIEW_RAW_AND_PROXY_LOG'
    complete.write_text(json.dumps(plan, indent=2) + '\n', encoding='utf8')
    print(json.dumps({'receipt': str(complete), 'sha256': sha(complete), 'result': plan}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--preflight', action='store_true')
    parser.add_argument('--build-experience', action='store_true')
    parser.add_argument('--generate-skill', action='store_true')
    parser.add_argument('--build-status-control', action='store_true')
    parser.add_argument('--task', choices=('source', 'target'))
    parser.add_argument('--condition', choices=('none', 'source_history', 'generated_skill',
                                                 'source_status', 'length_control'), default='none')
    args = parser.parse_args()
    if args.preflight:
        preflight()
    elif args.build_experience:
        build_experience()
    elif args.generate_skill:
        generate_skill()
    elif args.build_status_control:
        build_status_control()
    elif args.task:
        run(args.task, args.condition)
    else:
        parser.error('choose --preflight or --task')
