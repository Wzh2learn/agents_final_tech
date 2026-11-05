#!/usr/bin/env python3
"""Bounded requests development episodes using the existing OpenCode harness.

Each explicit attempt has an isolated output root. References and hidden tests
are mounted only after execution; a reservation never triggers an auto retry.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tarfile
import time
import urllib.request

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts.graph.research_auto_record import recorded_episode
import pyarrow.parquet as pq
import qualify_swe_contextbench_requests_20261105 as qual
import qualify_swe_contextbench_sympy_20261104 as shared
import run_swe_contextbench_sympy_20261104 as core
from run_swe_contextbench_sphinx_20261105 import inspect_experience_reads

PARENT = qual.ROOT / 'requests_agent_20261105'
MAX_SECONDS = 900
MAX_POSTS = 24
QUAL_SHA = '54ea5ffc639201ff5b19ff87e7066eef7f86cdc8f35ce8354393aadfb03eda0e'


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def row_for(task: str) -> dict:
    identity, dataset, rev, _ = qual.CASES[task]
    rows = [r for r in pq.read_table(qual.DATA / dataset,
        columns=['instance_id', 'base_commit', 'problem_statement', 'test_patch', 'FAIL_TO_PASS']).to_pylist()
        if r['instance_id'] == identity]
    if len(rows) != 1 or rows[0]['base_commit'] != rev:
        raise ValueError('task identity changed')
    return rows[0]


def check_source(task: str) -> None:
    _, _, rev, archive_sha = qual.CASES[task]
    archive, clean = qual.OUT / (task + '.tar.gz'), qual.OUT / task / 'clean_base'
    if sha(archive) != archive_sha or any(p.is_symlink() for p in clean.rglob('*')):
        raise ValueError('source identity or link changed')
    expected = {}
    with tarfile.open(archive, 'r:gz') as stream:
        for item in stream:
            parts = Path(item.name).parts
            if not parts or parts[0] != 'requests-' + rev or '..' in parts or item.name.startswith('/'):
                raise ValueError('unsafe archive')
            if item.isfile():
                with stream.extractfile(item) as f:
                    expected[Path(*parts[1:]).as_posix()] = hashlib.sha256(f.read()).hexdigest()
            elif not item.isdir():
                raise ValueError('unexpected archive entry')
    actual = {p.relative_to(clean).as_posix(): sha(p) for p in clean.rglob('*') if p.is_file()}
    if actual != expected or (clean / '.git').exists():
        raise ValueError('source content or history changed')


def preflight(task: str) -> dict:
    shared.checked_dataset()
    if sha(core.BASE) != core.BASE_SHA or sha(qual.OUT / 'receipt.json') != QUAL_SHA:
        raise ValueError('base harness or qualification changed')
    check_source(task)
    result = json.loads((qual.OUT / 'receipt.json').read_text(encoding='utf8'))
    c = result['cases'][task]
    if c['arms']['base']['focus']['exit'] != 1 or c['arms']['gold']['focus']['exit'] != 0:
        raise ValueError('focus controls do not qualify')
    if not c.get('qualified_regression_nodes'):
        raise ValueError('missing frozen executable regression subset')
    if any(c['arms'][arm]['qualified_regression']['exit'] != 0 for arm in ('base', 'gold')):
        raise ValueError('regression subset does not qualify')
    nodes = c['qualified_regression_nodes']
    node_file = qual.OUT / task / 'qualified_regression_nodes.json'
    if sha(node_file) != nodes['sha256'] or len(json.loads(node_file.read_text())) != nodes['count']:
        raise ValueError('frozen regression nodes changed')
    row = row_for(task)
    text = row['problem_statement'].replace('\r\n', '\n').rstrip() + '\n'
    task_file = qual.OUT / task / 'task.txt'
    if task_file.read_bytes() != text.encode('utf8') or sha(task_file) != c['task_sha256']:
        raise ValueError('problem_statement-only task changed')
    if hashlib.sha256(row['test_patch'].encode('utf8')).hexdigest() != c['arms']['base']['test_patch']['sha256']:
        raise ValueError('test patch changed')
    return c


def derive(root: Path, task: str, condition: str, experience: Path | None) -> str:
    base_condition = 'none' if condition == 'none' else 'generated_skill'
    code = core.derive(task, base_condition, experience)
    for old, new in ((str(core.ROOT), str(root)), (str(shared.OUT), str(qual.OUT)),
                     (str(shared.DEPS), str(qual.SITE)), (str(shared.OVERLAY / 'site'), str(qual.LEGACY))):
        if old not in code:
            raise ValueError('missing harness binding: ' + old)
        code = code.replace(old, new)
    if condition != base_condition:
        code = core.replace_once(code, str(root / f'{task}__{base_condition}__seed{core.SEED}'),
                                 str(root / f'{task}__{condition}__seed{core.SEED}'))
    edits = [
        ("'-e','PYTHONPATH=/runtime:/extra:/deps'", "'-e','PYTHONPATH=/deps','-e','PATH=/extra/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin'"),
        (f'len(calls)>={core.MAX_HTTP_REQUESTS}', f'len(calls)>={MAX_POSTS}'),
        (f'timeout={core.MAX_SECONDS})', f'timeout={MAX_SECONDS})'),
        ("(work/'instructions.txt').write_text(body,encoding='utf8')",
         "(work/'instructions.txt').write_text(body,encoding='utf8')\n(case/'frozen_instructions.txt').write_bytes((work/'instructions.txt').read_bytes())")]
    for old, new in edits:
        code = core.replace_once(code, old, new)
    compile(code, '<requests-agent-harness>', 'exec')
    return code


def evaluate(task: str, case: Path, control: dict) -> dict:
    work = case / 'work'
    if any(p.is_symlink() for p in work.rglob('*')):
        return {'status': 'UNRESOLVED_SYMLINK'}
    out = case / 'post_run_evaluation_restored_tests'
    out.mkdir()
    copy = out / 'candidate'
    standard = shutil.ignore_patterns('.git', '__pycache__', '.pytest_cache', 'instructions.txt', 'opencode.json')
    def ignore(path, names):
        excluded = set(standard(path, names))
        if Path(path) == work:
            excluded.update(set(names) & {'tests', 'source_experience.md'})
        return excluded
    shutil.copytree(work, copy, ignore=ignore)
    check_source(task)
    shutil.copytree(qual.OUT / task / 'clean_base/tests', copy / 'tests')
    patch = qual.patch(copy, row_for(task)['test_patch'], out / 'test.patch')
    result = {'status': 'TEST_PATCH_CONFLICT', 'test_source': 'FROZEN_BASE', 'test_patch': patch,
              'regression_scope': 'qualified executable subset; full controls and exclusions in qualification receipt'}
    if len(patch['steps']) == 2 and all(x['exit'] == 0 for x in patch['steps']):
        result.update({'status': 'EVALUATED',
            'focus': qual.run(copy, json.loads(row_for(task)['FAIL_TO_PASS']), out / 'focus.log', task + 'agentfocus'),
            'regression': qual.run(copy, json.loads((qual.OUT / task / 'qualified_regression_nodes.json').read_text()), out / 'regression.log', task + 'agentregression')})
    return result


def build_experience(root: Path) -> None:
    """Freeze source-only clipped history and a transparent feedback digest."""
    completed = root / f'source__none__seed{core.SEED}.completed.json'
    record = json.loads(completed.read_text(encoding='utf8'))
    case = root / f'source__none__seed{core.SEED}'
    raw = case / 'raw.jsonl'
    feedback = record['post_run_evaluation']
    if record['status'] != 'COMPLETED' or sha(raw) != record['raw_sha256'] or feedback['status'] != 'EVALUATED':
        raise ValueError('source evidence incomplete')
    actions = []
    for line in raw.read_text(encoding='utf8').splitlines():
        event = json.loads(line)
        if event.get('type') == 'tool_use':
            part = event['part']
            state = part.get('state', {})
            inp = json.dumps(state.get('input', {}), ensure_ascii=False)
            output = str(state.get('output', ''))
            actions.append({'tool': part.get('tool'), 'status': state.get('status'),
                'input_prefix': inp[:600], 'input_chars': len(inp),
                'input_sha256': hashlib.sha256(inp.encode('utf8')).hexdigest(),
                'output_tail': output[-800:], 'output_chars': len(output),
                'output_sha256': hashlib.sha256(output.encode('utf8')).hexdigest()})
    if not actions:
        raise ValueError('no source tool actions')
    for key in ('focus', 'regression'):
        if sha(case / 'post_run_evaluation_restored_tests' / (key + '.log')) != feedback[key]['log_sha256']:
            raise ValueError('source feedback log changed')
    def tree(path):
        return {p.relative_to(path).as_posix(): sha(p) for p in path.rglob('*') if p.is_file()
                and not any(x in ('.git', '__pycache__', '.pytest_cache') for x in p.parts)
                and p.name not in ('instructions.txt', 'opencode.json')}
    before, after = tree(qual.OUT / 'source/clean_base'), tree(case / 'work')
    changed = sorted(k for k in before.keys() | after.keys() if before.get(k) != after.get(k))
    source = {'source_task': (qual.OUT / 'source/task.txt').read_text(encoding='utf8'),
        'source_result': {'agent_exit': record['agent_exit'], 'posts': record['posts'],
            'request_limit_reached': record['posts'] >= MAX_POSTS,
            'focus_exit': feedback['focus']['exit'], 'focus_count': feedback['focus']['nodes_requested'],
            'regression_exit': feedback['regression']['exit'], 'regression_count': feedback['regression']['nodes_requested'],
            'regression_scope': feedback['regression_scope']}, 'changed_paths': changed}
    digest = json.dumps(source, ensure_ascii=False, indent=2)
    history = json.dumps({**source, 'source_actions': actions}, ensure_ascii=False, indent=2)
    if any(marker.casefold() in (history + raw.read_text(encoding='utf8')).casefold()
           for marker in ('psf__requests-3481', 'pull/3481', 'issues/3481', '#3481')):
        raise ValueError('literal target marker in source experience')
    out = root / 'source_experience'
    out.mkdir()
    (out / 'source_history.md').write_text('Source-only clipped history; feedback is stated first.\n' + history + '\n', encoding='utf8')
    (out / 'feedback_card.md').write_text('Transparent source-only result digest; no inferred repair instructions.\n' + digest + '\n', encoding='utf8')
    meta = {'source_raw_sha256': sha(raw), 'source_completion_sha256': sha(completed), 'actions': len(actions),
            'input_prefix_cap': 600, 'output_tail_cap': 800, 'changed_paths': changed,
            'clipped_inputs': sum(a['input_chars'] > 600 for a in actions),
            'clipped_outputs': sum(a['output_chars'] > 800 for a in actions),
            'scope': 'source-only; literal target screen is not proof of semantic or pretraining isolation',
            'artifacts': {p.name: sha(p) for p in out.iterdir() if p.is_file()}}
    (out / 'metadata.json').write_text(json.dumps(meta, indent=2) + '\n', encoding='utf8')
    print(json.dumps(meta))


def generate_skill(root: Path) -> None:
    """Ordinary source-only skill baseline, using the existing extraction prompt."""
    out = root / 'source_experience'
    meta = json.loads((out / 'metadata.json').read_text())
    history = out / 'source_history.md'
    if sha(history) != meta['artifacts']['source_history.md']:
        raise ValueError('source history changed')
    ledger = out / 'skill_generation_ledger.json'
    request_path = out / 'skill_generation_request.json'
    if any(p.exists() for p in (ledger, request_path, out / 'generated_skill.md', out / 'skill_generation_response.json')):
        raise FileExistsError('skill generation already attempted')
    payload = {'model': 'Qwen3.6-35B-A3B-Q4_K_M.gguf', 'temperature': core.TEMPERATURE, 'seed': core.SEED,
        'max_tokens': 2500, 'chat_template_kwargs': {'enable_thinking': False},
        'messages': [{'role': 'system', 'content': 'Create concise reusable instructions from a past '
            'tool-using agent episode and its feedback. Separate general steps from task-specific '
            'choices; include observed failures and unresolved assumptions. Do not invent results '
            'or copy the old answer as a future answer. Return only the skill text.'},
            {'role': 'user', 'content': history.read_text(encoding='utf8')}]}
    body = json.dumps(payload, ensure_ascii=False, separators=(',', ':')).encode('utf8')
    request_path.write_bytes(body)
    result = {'status': 'ATTEMPT_STARTED', 'physical_http_attempts': 1, 'usage': None,
              'source_history_sha256': sha(history), 'request_sha256': sha(request_path)}
    ledger.write_text(json.dumps(result, indent=2) + '\n')
    start = time.monotonic()
    try:
        request = urllib.request.Request('http://127.0.0.1:8004/v1/chat/completions', data=body,
                    headers={'Content-Type': 'application/json'}, method='POST')
        with urllib.request.urlopen(request, timeout=300) as response:
            raw = response.read()
        response_path = out / 'skill_generation_response.json'
        response_path.write_bytes(raw)
        parsed = json.loads(raw)
        text = parsed['choices'][0]['message']['content']
        if not isinstance(text, str) or not text.strip():
            raise ValueError('empty skill')
        result.update({'status': 'RECEIVED', 'usage': parsed.get('usage'),
            'finish_reason': parsed['choices'][0].get('finish_reason'), 'response_sha256': sha(response_path)})
        skill = out / 'generated_skill.md'
        skill.write_text(text.strip() + '\n', encoding='utf8')
        result['skill_sha256'] = sha(skill)
    except Exception as exc:
        result.update({'status': 'FAILED_UNKNOWN_USAGE', 'error_type': type(exc).__name__})
        raise
    finally:
        result['seconds'] = round(time.monotonic() - start, 3)
        ledger.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--attempt-id', required=True)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument('--task', choices=('source', 'target'))
    action.add_argument('--build-experience', action='store_true')
    action.add_argument('--generate-skill', action='store_true')
    parser.add_argument('--condition', choices=('none', 'source_history', 'generated_skill', 'feedback_card'), default='none')
    parser.add_argument('--experience', type=Path)
    parser.add_argument('--experience-sha256')
    parser.add_argument('--preflight-only', action='store_true')
    args = parser.parse_args()
    if not re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9_-]{0,63}', args.attempt_id):
        parser.error('invalid attempt identifier')
    root = PARENT / 'attempts' / args.attempt_id
    if args.build_experience or args.generate_skill:
        if args.condition != 'none' or args.experience or args.experience_sha256 or args.preflight_only:
            parser.error('build-experience accepts only an attempt identifier')
        preflight('source')
        (build_experience if args.build_experience else generate_skill)(root)
        return
    if (args.condition == 'none') != (args.experience is None) or ((args.experience is None) != (args.experience_sha256 is None)):
        parser.error('experience and its frozen hash required only for experience conditions')
    if args.task == 'source' and args.condition != 'none':
        parser.error('source episode must have no history')
    if args.experience and (args.experience.is_symlink() or sha(args.experience) != args.experience_sha256):
        raise ValueError('experience changed')
    control = preflight(args.task)
    target_freeze = None
    if args.task == 'target':
        directory = root / 'source_experience'
        frozen_path = directory / 'target_input_freeze.json'
        files = ('source_history.md', 'feedback_card.md', 'generated_skill.md')
        if not frozen_path.exists():
            ledger = json.loads((directory / 'skill_generation_ledger.json').read_text())
            if ledger['status'] != 'RECEIVED' or ledger['finish_reason'] != 'stop':
                raise ValueError('ordinary skill baseline incomplete')
            frozen = {'source_receipt_sha256': sha(root / f'source__none__seed{core.SEED}.completed.json'),
                      'skill_generation_ledger_sha256': sha(directory / 'skill_generation_ledger.json'),
                      'artifacts': {name: sha(directory / name) for name in files},
                      'scope': 'frozen before the first target model call; researcher has seen task references'}
            with frozen_path.open('x', encoding='utf8') as f:
                json.dump(frozen, f, indent=2)
        frozen = json.loads(frozen_path.read_text())
        if (frozen['source_receipt_sha256'] != sha(root / f'source__none__seed{core.SEED}.completed.json') or
                frozen['skill_generation_ledger_sha256'] != sha(directory / 'skill_generation_ledger.json') or
                any(sha(directory / name) != value for name, value in frozen['artifacts'].items())):
            raise ValueError('frozen source inputs changed')
        if args.experience and (args.experience.resolve().parent != directory.resolve() or
                frozen['artifacts'].get(args.experience.name) != args.experience_sha256 or
                args.experience.name != {'source_history': 'source_history.md',
                    'generated_skill': 'generated_skill.md', 'feedback_card': 'feedback_card.md'}[args.condition]):
            raise ValueError('experience is outside the frozen source-only baseline set')
        target_freeze = sha(frozen_path)
    code = derive(root, args.task, args.condition, args.experience)
    if args.preflight_only:
        print(json.dumps({'status': 'PREFLIGHT_PASS_NO_MODEL', 'task': args.task, 'attempt': args.attempt_id,
                          'qualification_sha256': sha(qual.OUT / 'receipt.json'),
                          'harness_sha256': hashlib.sha256(code.encode('utf8')).hexdigest()}))
        return
    (root / 'runtime').mkdir(parents=True, exist_ok=True)
    @recorded_episode(root, core.SEED)
    def run(task, condition):
        eid = f'{task}__{condition}__seed{core.SEED}'
        case = root / eid
        harness = root / (eid + '.harness.py')
        harness.write_text(code, encoding='utf8')
        plan = {'status': 'STARTED', 'task': task, 'condition': condition, 'attempt_id': args.attempt_id,
            'seed': core.SEED, 'temperature': core.TEMPERATURE, 'max_posts': MAX_POSTS,
            'task_identity': control['identity'], 'base_commit': control['base'],
            'harness_sha256': sha(harness), 'qualification_sha256': sha(qual.OUT / 'receipt.json'),
            'task_text_sha256': control['task_sha256'], 'experience_sha256': args.experience_sha256,
            'runner_sha256': sha(Path(__file__)),
            'target_input_freeze_sha256': target_freeze,
            'candidate_reference_hidden': True, 'attempt_policy': 'explicit isolated output root; never auto-retry'}
        start = root / (eid + '.started.json')
        start.write_text(json.dumps(plan, indent=2) + '\n', encoding='utf8')
        proc = subprocess.run([sys.executable, str(harness), task, 'no_skill'], stdin=subprocess.DEVNULL,
                              capture_output=True, timeout=MAX_SECONDS + 120)
        (root / (eid + '.runner.stdout')).write_bytes(proc.stdout)
        (root / (eid + '.runner.stderr')).write_bytes(proc.stderr)
        plan.update({'runner_exit': proc.returncode, 'started_sha256': sha(start)})
        if proc.returncode == 0 and (case / 'receipt.json').is_file():
            receipt = json.loads((case / 'receipt.json').read_text(encoding='utf8'))
            if sha(case / 'raw.jsonl') != receipt['raw_sha256']:
                raise ValueError('raw receipt changed')
            sampling_file = case / 'sampling_metadata.jsonl'
            metadata = [json.loads(s) for s in sampling_file.read_text().splitlines()] if sampling_file.is_file() else []
            if Counter(json.dumps(x, sort_keys=True) for x in metadata) != Counter(json.dumps(x, sort_keys=True) for x in receipt['sampling_metadata']):
                raise ValueError('sampling metadata changed')
            if (case / 'frozen_instructions.txt').read_bytes() != (qual.OUT / task / 'task.txt').read_text(encoding='utf8').strip().encode('utf8'):
                raise ValueError('actual task differs from frozen problem')
            if args.experience and sha(args.experience) != args.experience_sha256:
                raise ValueError('experience changed during run')
            plan.update({'status': 'COMPLETED', 'agent_exit': receipt['agent_exit'], 'raw_sha256': receipt['raw_sha256'],
                'posts': sum(s.startswith('POST ') for s in receipt['model_http_requests']),
                'denied': [s for s in receipt['model_http_requests'] if s.startswith('DENIED')],
                'reported_tokens': sum(t.get('total', 0) for t in receipt['step_finish_tokens']),
                'cache_read_included': sum(t.get('cache', {}).get('read', 0) for t in receipt['step_finish_tokens']),
                'seed_and_temperature_forwarded': bool(metadata) and all(
                    x['seed'] == core.SEED and x['temperature'] == core.TEMPERATURE for x in metadata),
                'experience_read': inspect_experience_reads(case / 'raw.jsonl', args.experience) if args.experience else None,
                'post_run_evaluation': evaluate(task, case, control)})
        else:
            plan['status'] = 'RUNNER_ERROR_REVIEW_RAW_AND_PROXY_LOG'
        completed = root / (eid + '.completed.json')
        completed.write_text(json.dumps(plan, indent=2) + '\n', encoding='utf8')
        print(json.dumps({'receipt': str(completed), 'sha256': sha(completed), 'result': plan}))
    run(args.task, args.condition)


if __name__ == '__main__':
    main()
