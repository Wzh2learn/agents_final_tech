#!/usr/bin/env python3
"""Run a source/target skill pilot on a fixed public aiohttp checkout."""
from __future__ import annotations

import argparse
import ast
from collections import Counter
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
import urllib.request

from qualify_swe_aiohttp_20261104 import AIO, AIO_REV, BENCH, BENCH_REV, DEPS, OUT as QUAL, ROOT, sha
from run_evoclaw_config_20261104 import BASE, BASE_SHA, replace_once

IMAGE = 'sha256:648a1999badfe683239ec49e05b2a508e37f762213478122c58fa713f6c00f58'
QUAL_SHA = '54d45a4ee7b117ec8c889a63b585b4481577187a3daf6440dab063ce63d33aca'
RUNS = ROOT / 'swe_aiohttp_agent_20261104_v2'
PUB_SKILL = BENCH / 'skills/asyncio-patterns/SKILL.md'
TASKS = {'source': 1, 'target': 2}


def validate() -> dict:
    if sha(BASE) != BASE_SHA or sha(QUAL / 'receipt.json') != QUAL_SHA:
        raise ValueError('base harness or qualification changed')
    qual = json.loads((QUAL / 'receipt.json').read_text(encoding='utf-8'))
    if qual['benchmark_revision'] != BENCH_REV or qual['repository_revision'] != AIO_REV or qual['image_id'] != IMAGE:
        raise ValueError('qualification identity mismatch')
    if any(qual['cases'][f'batch{i}_{kind}']['exit'] != wanted
           for i in (1, 2) for kind, wanted in (('empty', 1), ('positive', 0))):
        raise ValueError('qualification controls are not ready')
    for path, rev in ((AIO, AIO_REV), (BENCH, BENCH_REV)):
        actual = subprocess.check_output(['git', '-C', str(path), 'rev-parse', 'HEAD'], text=True).strip()
        if actual != rev:
            raise ValueError('upstream checkout changed')
        if subprocess.check_output(['git', '-C', str(path), 'status', '--porcelain'], text=True).strip():
            raise ValueError('upstream checkout is not clean')
    for batch in (1, 2):
        task = BENCH / f'tasks/batch{batch}/asyncio-patterns.md'
        hidden = BENCH / f'tests/batch{batch}/test_asyncio_patterns.py'
        checked = qual['cases'][f'batch{batch}_positive']
        if sha(task) != checked['task_sha256'] or sha(hidden) != checked['benchmark_test_sha256']:
            raise ValueError('task or benchmark test changed since qualification')
    return qual


def derived_harness(task: str, condition: str, experience: Path | None) -> str:
    code = BASE.read_text(encoding='utf-8')
    marker = '# A completely separate non-agent container mounts verifier after the episode;'
    if code.count(marker) != 1 or code.count("receipt={'task':task") != 1:
        raise ValueError('cannot isolate base post-run verification')
    code = code.split(marker, 1)[0] + "\nvrc=None\nreceipt={'task':task" + code.split("receipt={'task':task", 1)[1]
    batch = TASKS[task]
    source_code = (
        "src=UP/task\n"
        f"shutil.copytree(Path({str(AIO)!r}),work,dirs_exist_ok=True,"
        "ignore=shutil.ignore_patterns('.git','__pycache__','.pytest_cache'))\n"
        "work.chmod(0o777)\n"
        "(work/'aiohttp').chmod(0o777); (work/'tests').chmod(0o777); "
        "(work/'aiohttp/helpers.py').chmod(0o666)\n"
        + ("(work/'source_experience.md').touch(mode=0o444)\n" if experience else '')
    )
    edits = [
        ("ROOT=Path('/home/testuser/wzh/research_evidence/agent_skill_method_20261029')", f'ROOT=Path({str(RUNS)!r})', 1),
        ("UP=Path('/home/testuser/wzh/research_evidence/agent_frontier_20261029/skillsbench_v1_1/tasks')", f'UP=Path({str(BENCH / "tasks")!r})', 1),
        ("if task not in ('llm-prefix-cache-replay','dialogue-parser','tictoc-unnecessary-abort-detection') or arm not in ('no_skill','all_skill','select_skill'): raise SystemExit('unsupported')",
         f"if task not in {tuple(TASKS)!r} or arm != 'no_skill': raise SystemExit('unsupported')", 1),
        ("case=ROOT/(task+'__'+arm+'__'+str(os.getpid()))",
         f"case=ROOT/(task+'__{condition}__'+str(os.getpid()))", 1),
        ('src=UP/task', source_code, 1),
        ("body=(src/'task.md').read_text(encoding='utf8').split('---',2)[2].strip()",
         f"body=(UP/'batch{batch}'/'asyncio-patterns.md').read_text(encoding='utf8').strip()", 1),
        ("Never read an entire large trace into the conversation; inspect only the first two lines using shell head, then write code that processes the complete unmodified file.",
         'Use the repository in the current working directory and follow the current task.', 1),
        ("len(calls)>=8", "len(calls)>=32", 1),
        ("sum(payload_bytes)+length>450000", "sum(payload_bytes)+length>4000000", 1),
        ("calls.append('DENIED_OR_LIMIT');self.request.sendall",
         "reason=('method' if line not in allowed else 'request_cap' if len(calls)>=32 "
         "else 'missing_length' if length is None else 'post_byte_cap')\n"
         "   calls.append('DENIED:'+reason);self.request.sendall", 1),
        ("'timeout':120000", "'timeout':300000", 1),
        ("[],[],120)", "[],[],300)", 2),
        ("stderr=subprocess.PIPE,timeout=300)", "stderr=subprocess.PIPE,timeout=1500)", 1),
        ("'--cpus','1','--cap-drop'", "'--cpus','2','--cap-drop'", 1),
        ("'--memory','2g'", "'--memory','3g'", 1),
        ("sockpath.unlink(missing_ok=True)", "sockpath.unlink(missing_ok=True);bridge.rmdir()", 1),
        ("'python:3.12-slim'", repr(IMAGE), 1),
    ]
    for old, new, count in edits:
        code = replace_once(code, old, new, count)
    if experience:
        code = replace_once(code, 'Use available tools to implement and execute your solution.',
                            'Before solving, read /root/source_experience.md, assess what applies, '
                            'and follow the current task. Use available tools to implement and execute your solution.')
    mounts = (f"['--mount','type=bind,src={DEPS},dst=/deps,readonly',"
              "'-e','PYTHONDONTWRITEBYTECODE=1','-e','PYTEST_DISABLE_PLUGIN_AUTOLOAD=1',"
              "'-e','PYTEST_ADDOPTS=-p pytest_asyncio.plugin -p pytest_timeout']")
    if experience:
        mounts += f"+['--mount','type=bind,src={experience},dst=/root/source_experience.md,readonly']"
    code = replace_once(code, 'server=Server(str(sockpath),Handler);',
                        f"_at=cmd.index({IMAGE!r}); cmd[_at:_at]={mounts}; server=Server(str(sockpath),Handler);")
    compile(code, str(BASE), 'exec')
    return code


def postcheck(batch: int, case: Path, label: str = 'benchmark') -> dict:
    hidden = BENCH / f'tests/batch{batch}/test_asyncio_patterns.py'
    work, log = case / 'work', case / f'{label}_pytest.log'
    if log.exists():
        raise FileExistsError('refusing to overwrite evaluator log')
    if not (work.stat().st_mode & 0o002):
        raise ValueError('evaluator workspace is not writable in the capability-dropped container')
    names = (('aiohttp/helpers.py', 'tests/test_map_concurrent.py') if batch == 1
             else ('aiohttp/task_pool.py', 'tests/test_task_pool.py'))
    def artifact_hashes() -> dict:
        return {name: sha(work / name) if (work / name).is_file() and not (work / name).is_symlink() else None
                for name in names}
    before = artifact_hashes()
    name = f'swe-aiohttp-eval-{os.getpid()}'
    cmd = ['docker', 'run', '--name', name, '--rm', '--pull', 'never', '--network', 'none', '--read-only',
           '--cpus', '2', '--memory', '3g', '--pids-limit', '256', '--cap-drop', 'ALL',
           '--security-opt', 'no-new-privileges', '--tmpfs', '/tmp:rw,nosuid,size=128m',
           '-e', 'PYTHONPATH=/workspace/aiohttp', '-e', 'PYTHONDONTWRITEBYTECODE=1',
           '-e', 'PYTEST_DISABLE_PLUGIN_AUTOLOAD=1', '-e', 'PYTEST_ADDOPTS=-p pytest_asyncio.plugin -p pytest_timeout',
           '--mount', f'type=bind,src={work},dst=/workspace/aiohttp',
           '--mount', f'type=bind,src={hidden},dst=/checks/test_asyncio_patterns.py,readonly',
           '--mount', f'type=bind,src={DEPS},dst=/deps,readonly', '--workdir', '/workspace/aiohttp',
           '--entrypoint', 'python3', IMAGE, '-m', 'pytest', '-q', '-p', 'no:cacheprovider',
           '/checks/test_asyncio_patterns.py']
    start = time.monotonic()
    try:
        proc = subprocess.run(cmd, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT, timeout=300, check=False)
        exit_code, data = proc.returncode, proc.stdout
    except subprocess.TimeoutExpired as exc:
        exit_code, data = 124, exc.stdout or b''
        subprocess.run(['docker', 'kill', name], stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL, timeout=10, check=False)
    log.write_bytes(data)
    text = data.decode('utf-8', errors='replace')
    summary = next((line.strip() for line in reversed(text.splitlines())
                    if re.search(r'\d+ (?:passed|failed|error)', line)), '')
    failed_names = [line.split(' - ', 1)[0] for line in text.splitlines() if line.startswith('FAILED ')]
    after = artifact_hashes()
    return {'exit': exit_code, 'summary': summary, 'failed_names': failed_names,
            'candidate_artifact_sha256_before': before, 'candidate_artifact_sha256_after': after,
            'candidate_unchanged': before == after,
            'seconds': round(time.monotonic() - start, 3), 'benchmark_test_sha256': sha(hidden),
            'log_sha256': sha(log), 'evaluator_image': IMAGE}


def run(task: str, condition: str) -> None:
    validate()
    if task == 'source' and condition != 'none':
        raise ValueError('source runs without experience')
    if condition == 'published_skill':
        experience = PUB_SKILL
    elif condition in ('neutral_plan', 'conditioned_plan'):
        source_cases = sorted(path for path in RUNS.iterdir() if path.is_dir() and path.name.startswith('source__none__'))
        if len(source_cases) != 1:
            raise ValueError('expected a single recorded source episode')
        plan_dir = source_cases[0] / 'target_plans' / condition
        ledger = json.loads((plan_dir / 'ledger.json').read_text(encoding='utf-8'))
        experience = plan_dir / 'plan.md'
        if ledger['status'] != 'RECEIVED' or ledger['plan_sha256'] != sha(experience):
            raise ValueError('target plan changed or is not ready')
    elif condition in ('source_history', 'generated_skill'):
        source_cases = sorted(path for path in RUNS.iterdir() if path.is_dir() and path.name.startswith('source__none__'))
        if len(source_cases) != 1:
            raise ValueError('expected a single recorded source episode')
        source = source_cases[0]
        meta = json.loads((source / 'experience_metadata.json').read_text(encoding='utf-8'))
        experience = source / ('source_history.txt' if condition == 'source_history' else 'generated_skill.md')
        expected = meta['history_sha256'] if condition == 'source_history' else meta.get('skill_sha256')
        if not expected or not experience.is_file() or sha(experience) != expected:
            raise ValueError('source experience changed or missing')
    else:
        experience = None
    code = derived_harness(task, condition, experience)
    RUNS.mkdir(parents=True, exist_ok=True)
    reservation = RUNS / f'{task}__{condition}__{os.getpid()}.reservation.json'
    if reservation.exists():
        raise FileExistsError('episode reservation exists')
    task_file = BENCH / f'tasks/batch{TASKS[task]}/asyncio-patterns.md'
    info = {'status': 'STARTED', 'task': task, 'condition': condition, 'task_sha256': sha(task_file),
            'repository_revision': AIO_REV, 'benchmark_revision': BENCH_REV, 'qualification_sha256': QUAL_SHA,
            'derived_sha256': hashlib.sha256(code.encode()).hexdigest(),
            'experience_sha256': sha(experience) if experience else None,
            'max_http': 32, 'max_request_bytes': 4000000, 'max_wall_seconds': 1500,
            'started_utc': datetime.datetime.now(datetime.timezone.utc).isoformat()}
    reservation.write_text(json.dumps(info, indent=2) + '\n', encoding='utf-8')
    old_argv = sys.argv
    namespace = {'__name__': '__main__'}
    try:
        sys.argv = [str(BASE), task, 'no_skill']
        exec(compile(code, str(BASE), 'exec'), namespace)
    finally:
        sys.argv = old_argv
    case = namespace['case']
    result = postcheck(TASKS[task], case)
    (case / 'benchmark_receipt.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    info.update({'status': 'COMPLETED', 'case': str(case), 'raw_receipt_sha256': sha(case / 'receipt.json'),
                 'benchmark_receipt_sha256': sha(case / 'benchmark_receipt.json')})
    reservation.write_text(json.dumps(info, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'case': str(case), 'benchmark': result}, ensure_ascii=False))


def build_experience(case: Path) -> None:
    case = case.resolve(strict=True)
    if RUNS.resolve() not in case.parents or not case.name.startswith('source__none__'):
        raise ValueError('source episode is not eligible')
    receipt = json.loads((case / 'receipt.json').read_text(encoding='utf-8'))
    feedback_path = case / 'benchmark_recheck_receipt.json'
    if not feedback_path.is_file():
        feedback_path = case / 'benchmark_receipt.json'
    feedback = json.loads(feedback_path.read_text(encoding='utf-8'))
    if not feedback.get('candidate_unchanged'):
        raise ValueError('source feedback has not been bound to unchanged artifacts')
    raw = case / 'raw.jsonl'
    if receipt['raw_sha256'] != sha(raw):
        raise ValueError('source raw changed')
    actions = []
    for line in raw.read_text(encoding='utf-8').splitlines():
        event = json.loads(line)
        if event.get('type') == 'tool_use':
            part = event.get('part', {})
            state = part.get('state', {})
            input_text = json.dumps(state.get('input', {}), ensure_ascii=False, separators=(',', ':'))
            output_text = str(state.get('output', ''))
            actions.append({'tool': part.get('tool'), 'status': state.get('status'),
                            'input_prefix': input_text[:1600], 'input_chars': len(input_text),
                            'input_sha256': hashlib.sha256(input_text.encode()).hexdigest(),
                            'output_tail': output_text[-1600:], 'output_chars': len(output_text)})
    if not actions:
        raise ValueError('no source tool actions recorded')
    helper = case / 'work/aiohttp/helpers.py'
    source_text = helper.read_text(encoding='utf-8')
    tree = ast.parse(source_text)
    functions = [node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                 and node.name == 'map_concurrent']
    generated_function = ast.get_source_segment(source_text, functions[-1]) if functions else None
    content = {'source_instruction': (case / 'work/instructions.txt').read_text(encoding='utf-8'),
               'source_actions': actions, 'source_function': generated_function,
               'source_feedback': {'exit': feedback['exit'], 'summary': feedback['summary'],
                                   'failed_test_names': feedback['failed_names']},
               'scope': 'all source tool actions, each input prefix and output tail clipped to 1600 characters; '
                        'source-only feedback, source function separately included'}
    encoded = json.dumps(content, ensure_ascii=False, separators=(',', ':'))
    pieces = [encoded[i:i + 700] for i in range(0, len(encoded), 700)]
    readable = ('Source-only task history. The current task may differ. Concatenate text after | '
                'on numbered lines to reconstruct the JSON.\n'
                + ''.join(f'{i:04d}|{piece}\n' for i, piece in enumerate(pieces)))
    if ''.join(line.split('|', 1)[1] for line in readable.splitlines()[1:]) != encoded:
        raise ValueError('history wrapping is not lossless')
    history, meta = case / 'source_history.txt', case / 'experience_metadata.json'
    if history.exists() or meta.exists():
        raise FileExistsError('experience already exists')
    history.write_text(readable, encoding='utf-8')
    metadata = {'source_raw_sha256': sha(raw), 'source_receipt_sha256': sha(case / 'receipt.json'),
                'source_feedback_sha256': sha(feedback_path), 'history_sha256': sha(history),
                'history_action_count': len(actions), 'source_function_present': bool(functions),
                'scope': content['scope']}
    meta.write_text(json.dumps(metadata, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'history': str(history), 'sha256': sha(history), 'actions': len(actions),
                      'source_function_present': bool(functions)}))


def recheck(case: Path) -> None:
    case = case.resolve(strict=True)
    if RUNS.resolve() not in case.parents:
        raise ValueError('recheck requires an episode in the current run root')
    receipt_path = case / 'benchmark_recheck_receipt.json'
    if receipt_path.exists():
        raise FileExistsError('recheck receipt already exists')
    if case.name.startswith('source__'):
        batch = 1
    elif case.name.startswith('target__'):
        batch = 2
    else:
        raise ValueError('unknown episode')
    validate()
    result = postcheck(batch, case, 'benchmark_recheck')
    receipt_path.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'receipt': str(receipt_path), 'sha256': sha(receipt_path), 'result': result}))


def skill_request(history: Path) -> bytes:
    payload = {'model': 'Qwen3.6-35B-A3B-Q4_K_M.gguf', 'temperature': 0, 'max_tokens': 2500,
               'chat_template_kwargs': {'enable_thinking': False},
               'messages': [{'role': 'system', 'content': 'Create concise reusable instructions from a past '
                             'tool-using agent episode and its feedback. Separate general steps from task-specific '
                             'choices; include observed failures and unresolved assumptions. Do not invent results '
                             'or copy the old answer as a future answer. Return only the skill text.'},
                            {'role': 'user', 'content': history.read_text(encoding='utf-8')}]}
    return json.dumps(payload, ensure_ascii=False, separators=(',', ':')).encode()


def generate_skill(case: Path) -> None:
    case = case.resolve(strict=True)
    if RUNS.resolve() not in case.parents or not case.name.startswith('source__none__'):
        raise ValueError('source episode is not eligible')
    meta_path, history = case / 'experience_metadata.json', case / 'source_history.txt'
    meta = json.loads(meta_path.read_text(encoding='utf-8'))
    if sha(history) != meta['history_sha256'] or sha(case / 'raw.jsonl') != meta['source_raw_sha256']:
        raise ValueError('source evidence changed')
    ledger_path, skill = case / 'skill_generation_ledger.json', case / 'generated_skill.md'
    request_path = case / 'skill_generation_request.json'
    if ledger_path.exists() or skill.exists() or request_path.exists():
        raise FileExistsError('skill generation already attempted')
    request = skill_request(history)
    request_path.write_bytes(request)
    ledger = {'status': 'ATTEMPT_STARTED', 'request_sha256': hashlib.sha256(request).hexdigest(),
              'source_history_sha256': sha(history), 'http_attempts': 1, 'usage': None}
    ledger_path.write_text(json.dumps(ledger, indent=2) + '\n', encoding='utf-8')
    started = time.monotonic()
    try:
        req = urllib.request.Request('http://127.0.0.1:8004/v1/chat/completions', data=request,
                                     headers={'Content-Type': 'application/json'}, method='POST')
        with urllib.request.urlopen(req, timeout=300) as response:
            raw = response.read()
        (case / 'skill_generation_response.json').write_bytes(raw)
        parsed = json.loads(raw)
        text = parsed['choices'][0]['message']['content']
        if not isinstance(text, str) or not text.strip():
            raise ValueError('empty skill response')
        skill.write_text(text.strip() + '\n', encoding='utf-8')
        ledger.update({'status': 'RECEIVED', 'response_sha256': sha(case / 'skill_generation_response.json'),
                       'skill_sha256': sha(skill), 'usage': parsed.get('usage')})
        meta['skill_sha256'] = sha(skill)
        meta_path.write_text(json.dumps(meta, indent=2) + '\n', encoding='utf-8')
    except Exception as exc:
        ledger.update({'status': 'FAILED_UNKNOWN_USAGE', 'error_type': type(exc).__name__})
        raise
    finally:
        ledger['seconds'] = round(time.monotonic() - started, 3)
        ledger_path.write_text(json.dumps(ledger, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(ledger, ensure_ascii=False))


def reconstruct_skill_request(case: Path) -> None:
    case = case.resolve(strict=True)
    if RUNS.resolve() not in case.parents or not case.name.startswith('source__none__'):
        raise ValueError('source episode is not eligible')
    ledger = json.loads((case / 'skill_generation_ledger.json').read_text(encoding='utf-8'))
    history = case / 'source_history.txt'
    if sha(history) != ledger['source_history_sha256']:
        raise ValueError('source history changed')
    request = skill_request(history)
    if hashlib.sha256(request).hexdigest() != ledger['request_sha256']:
        raise ValueError('reconstructed request differs from recorded request')
    path = case / 'skill_generation_request_reconstructed.json'
    if path.exists():
        raise FileExistsError('reconstructed request already exists')
    path.write_bytes(request)
    print(json.dumps({'request': str(path), 'sha256': sha(path), 'status': 'RECONSTRUCTED_POSTHOC_HASH_MATCH'}))


def make_target_plan(condition: str) -> None:
    validate()
    if condition not in ('neutral_plan', 'conditioned_plan'):
        raise ValueError('unsupported plan condition')
    source_cases = sorted(p for p in RUNS.iterdir() if p.is_dir() and p.name.startswith('source__none__'))
    if len(source_cases) != 1:
        raise ValueError('expected a single source episode')
    source = source_cases[0]
    meta = json.loads((source / 'experience_metadata.json').read_text(encoding='utf-8'))
    skill = source / 'generated_skill.md'
    if sha(skill) != meta['skill_sha256']:
        raise ValueError('source skill changed')
    task_file = BENCH / 'tasks/batch2/asyncio-patterns.md'
    target = task_file.read_text(encoding='utf-8')
    material = {'current_task': target}
    if condition == 'conditioned_plan':
        material['prior_source_skill'] = skill.read_text(encoding='utf-8')
    prompt = ('Create a concise implementation plan for the current task. Use only the supplied material; '
              'do not assume hidden tests or invent results. Focus on required files, API, concurrency, '
              'exception handling, and tests. The current task always takes priority over any prior experience. '
              'Output the plan only.')
    payload = {'model': 'Qwen3.6-35B-A3B-Q4_K_M.gguf', 'temperature': 0, 'max_tokens': 1600,
               'chat_template_kwargs': {'enable_thinking': False},
               'messages': [{'role': 'system', 'content': prompt},
                            {'role': 'user', 'content': json.dumps(material, ensure_ascii=False, separators=(',', ':'))}]}
    request = json.dumps(payload, ensure_ascii=False, separators=(',', ':')).encode()
    directory = source / 'target_plans' / condition
    directory.mkdir(parents=True, exist_ok=False)
    (directory / 'request.json').write_bytes(request)
    ledger_path = directory / 'ledger.json'
    ledger = {'status': 'ATTEMPT_STARTED', 'condition': condition, 'task_sha256': sha(task_file),
              'source_skill_sha256': sha(skill) if condition == 'conditioned_plan' else None,
              'request_sha256': sha(directory / 'request.json'), 'http_attempts': 1, 'usage': None,
              'scope': 'post-hoc target planning from public task and optional source-only skill; no target tests'}
    ledger_path.write_text(json.dumps(ledger, indent=2) + '\n', encoding='utf-8')
    start = time.monotonic()
    try:
        req = urllib.request.Request('http://127.0.0.1:8004/v1/chat/completions', data=request,
                                     headers={'Content-Type': 'application/json'}, method='POST')
        with urllib.request.urlopen(req, timeout=300) as response:
            raw = response.read()
        (directory / 'response.json').write_bytes(raw)
        parsed = json.loads(raw)
        text = parsed['choices'][0]['message']['content']
        if not isinstance(text, str) or not text.strip():
            raise ValueError('empty plan')
        (directory / 'plan.md').write_text(text.strip() + '\n', encoding='utf-8')
        ledger.update({'status': 'RECEIVED', 'plan_sha256': sha(directory / 'plan.md'),
                       'response_sha256': sha(directory / 'response.json'), 'usage': parsed.get('usage')})
    except Exception as exc:
        ledger.update({'status': 'FAILED_UNKNOWN_USAGE', 'error_type': type(exc).__name__})
        raise
    finally:
        ledger['seconds'] = round(time.monotonic() - start, 3)
        ledger_path.write_text(json.dumps(ledger, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(ledger, ensure_ascii=False))


def workspace_changes(work: Path) -> dict:
    def inventory(root: Path) -> dict:
        found = {}
        for current, dirs, files in os.walk(root, followlinks=False):
            dirs[:] = [name for name in dirs if name not in ('.git', '__pycache__', '.pytest_cache')]
            for name in list(dirs):
                directory = Path(current) / name
                if directory.is_symlink():
                    if root == AIO:
                        raise ValueError('source contains a directory symlink: copy semantics need review')
                    found[directory.relative_to(root).as_posix()] = 'symlink:' + os.readlink(directory)
                    dirs.remove(name)
            for name in files:
                file = Path(current) / name
                rel = file.relative_to(root).as_posix()
                if rel in ('instructions.txt', 'opencode.json', 'source_experience.md'):
                    continue
                if file.is_symlink():
                    if root == AIO:
                        resolved = file.resolve(strict=True)
                        if AIO.resolve() not in resolved.parents or not resolved.is_file():
                            raise ValueError('source file symlink leaves the repository')
                        found[rel] = sha(resolved)  # copytree dereferences source file symlinks
                    else:
                        found[rel] = 'symlink:' + os.readlink(file)
                elif file.is_file():
                    found[rel] = sha(file)
        return found
    original, current = inventory(AIO), inventory(work)
    return {'added': sorted(set(current) - set(original)), 'deleted': sorted(set(original) - set(current)),
            'modified': sorted(name for name in set(original) & set(current) if original[name] != current[name])}


PROBE = r'''
import asyncio, json

class Marker(Exception):
    pass

try:
    from aiohttp.task_pool import TaskPool
except Exception as exc:
    print(json.dumps({'import_error': type(exc).__name__}))
    raise SystemExit(0)

async def normal_drain():
    completed = []
    async def job(i):
        await asyncio.sleep(0.02)
        completed.append(i)
    async with TaskPool(2) as pool:
        pool.submit(job(0))
        pool.submit(job(1))
    return {'completed': sorted(completed), 'pass': sorted(completed) == [0, 1]}

async def body_error():
    completed, cancelled = [], []
    async def job(i):
        try:
            await asyncio.sleep(1)
            completed.append(i)
        except asyncio.CancelledError:
            cancelled.append(i)
            raise
    caught = None
    try:
        async with TaskPool(2) as pool:
            pool.submit(job(0))
            pool.submit(job(1))
            await asyncio.sleep(0.05)
            raise Marker('body')
    except Exception as exc:
        caught = type(exc).__name__
    await asyncio.sleep(0.05)
    return {'caught': caught, 'completed': sorted(completed), 'cancelled': sorted(cancelled),
            'pass': caught == 'Marker' and not completed and sorted(cancelled) == [0, 1]}

async def handled_job_error():
    caught = None
    async def bad():
        await asyncio.sleep(0)
        raise Marker('job')
    try:
        async with TaskPool(1) as pool:
            handle = pool.submit(bad())
            try:
                await handle
            except Marker:
                caught = 'inner'
    except Exception as exc:
        return {'caught': caught, 'outer': type(exc).__name__, 'pass': False}
    return {'caught': caught, 'outer': None, 'pass': caught == 'inner'}

async def main():
    output = {}
    for name, func in [('normal_drain', normal_drain), ('body_error', body_error),
                       ('handled_job_error', handled_job_error)]:
        try:
            output[name] = await asyncio.wait_for(func(), timeout=4)
        except Exception as exc:
            output[name] = {'error': type(exc).__name__, 'pass': False}
    print(json.dumps(output, sort_keys=True))

asyncio.run(main())
'''


def independent_probe() -> None:
    validate()
    out = RUNS / 'independent_probe_20261104'
    if out.exists():
        raise FileExistsError('independent probe already exists')
    candidates = sorted(p for p in RUNS.iterdir() if p.is_dir() and p.name.startswith('target__'))
    if len(candidates) != 6:
        raise ValueError('expected six target candidates')
    out.mkdir()
    script = out / 'probe.py'
    script.write_text(PROBE, encoding='utf-8')
    rows = []
    cases = [('control_positive', QUAL / 'batch2_positive/aiohttp', None),
             ('control_empty', QUAL / 'batch2_empty/aiohttp', None)]
    for case in candidates:
        result = json.loads((case / 'benchmark_receipt.json').read_text(encoding='utf-8'))
        cases.append((case.name, case / 'work', result['candidate_artifact_sha256_after']['aiohttp/task_pool.py']))
    for index, (label, work, expected_hash) in enumerate(cases):
        path = work / 'aiohttp/task_pool.py'
        before = sha(path) if path.is_file() and not path.is_symlink() else None
        if label.startswith('target__') and before != expected_hash:
            raise ValueError('candidate changed before independent probe')
        name = f'independent-aiohttp-{os.getpid()}-{index}'
        cmd = ['docker', 'run', '--name', name, '--rm', '--pull', 'never', '--network', 'none', '--read-only',
               '--cpus', '2', '--memory', '3g', '--pids-limit', '256', '--cap-drop', 'ALL',
               '--security-opt', 'no-new-privileges', '--tmpfs', '/tmp:rw,nosuid,size=64m',
               '-e', 'PYTHONPATH=/workspace/aiohttp', '-e', 'PYTHONDONTWRITEBYTECODE=1',
               '--mount', f'type=bind,src={work},dst=/workspace/aiohttp,readonly',
               '--mount', f'type=bind,src={script},dst=/check/probe.py,readonly',
               '--mount', f'type=bind,src={DEPS},dst=/deps,readonly', '--entrypoint', 'python3', IMAGE, '/check/probe.py']
        start = time.monotonic()
        try:
            proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30, check=False)
            exit_code, stdout, stderr = proc.returncode, proc.stdout, proc.stderr
        except subprocess.TimeoutExpired as exc:
            exit_code, stdout, stderr = 124, exc.stdout or b'', exc.stderr or b''
            subprocess.run(['docker', 'kill', name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                           timeout=10, check=False)
        log = out / f'{label}.stdout'
        err = out / f'{label}.stderr'
        log.write_bytes(stdout)
        err.write_bytes(stderr)
        parsed = None
        if exit_code == 0:
            try:
                parsed = json.loads(stdout.decode('utf-8').splitlines()[-1])
            except (ValueError, IndexError, UnicodeDecodeError):
                pass
        after = sha(path) if path.is_file() and not path.is_symlink() else None
        rows.append({'case': label, 'exit': exit_code, 'seconds': round(time.monotonic() - start, 3),
                     'candidate_sha256': before, 'candidate_unchanged': before == after,
                     'stdout_sha256': sha(log), 'stderr_sha256': sha(err), 'result': parsed})
    receipt = out / 'receipt.json'
    receipt.write_text(json.dumps({'scope': 'POSTHOC_DEVELOPMENT_BEHAVIOR_PROBE', 'probe_sha256': sha(script),
                                   'cases': rows}, indent=2) + '\n', encoding='utf-8')
    positive, empty = rows[:2]
    if (positive['exit'] != 0 or not isinstance(positive['result'], dict)
            or not all(positive['result'].get(name, {}).get('pass')
                       for name in ('normal_drain', 'body_error', 'handled_job_error'))
            or empty['exit'] != 0 or not (empty['result'] or {}).get('import_error')):
        raise ValueError(f'probe controls failed; evidence saved in {receipt}')
    print(json.dumps({'receipt': str(receipt), 'sha256': sha(receipt), 'cases': rows}))


def summarize(path: Path) -> None:
    if path.exists():
        raise FileExistsError('refusing to overwrite a summary')
    cases = sorted(p for p in RUNS.iterdir() if p.is_dir())
    expected = {('source', 'none')} | {('target', condition) for condition in
        ('none', 'source_history', 'generated_skill', 'published_skill', 'neutral_plan', 'conditioned_plan')}
    source_cases = [p for p in cases if p.name.startswith('source__none__')]
    if len(source_cases) != 1:
        raise ValueError('expected one qualified source episode')
    source = source_cases[0]
    metadata = json.loads((source / 'experience_metadata.json').read_text(encoding='utf-8'))
    skill_ledger = json.loads((source / 'skill_generation_ledger.json').read_text(encoding='utf-8'))
    if (sha(source / 'raw.jsonl') != metadata['source_raw_sha256']
            or sha(source / 'receipt.json') != metadata['source_receipt_sha256']
            or sha(source / 'benchmark_recheck_receipt.json') != metadata['source_feedback_sha256']
            or sha(source / 'source_history.txt') != metadata['history_sha256']
            or sha(source / 'generated_skill.md') != metadata['skill_sha256']
            or skill_ledger['status'] != 'RECEIVED' or skill_ledger['skill_sha256'] != metadata['skill_sha256']
            or sha(source / 'skill_generation_request_reconstructed.json') != skill_ledger['request_sha256']):
        raise ValueError('source experience or skill ledger changed')
    rows = {}
    for case in cases:
        match = re.fullmatch(r'(source|target)__(none|source_history|generated_skill|published_skill|neutral_plan|conditioned_plan)__(\d+)', case.name)
        if not match or (match[1], match[2]) in rows:
            raise ValueError(f'unexpected or duplicated episode: {case.name}')
        task, condition, pid = match.groups()
        reservation = json.loads((RUNS / f'{task}__{condition}__{pid}.reservation.json').read_text(encoding='utf-8'))
        receipt = json.loads((case / 'receipt.json').read_text(encoding='utf-8'))
        result_path = case / ('benchmark_recheck_receipt.json' if task == 'source' else 'benchmark_receipt.json')
        result = json.loads(result_path.read_text(encoding='utf-8'))
        if (reservation['status'] != 'COMPLETED' or receipt['raw_sha256'] != sha(case / 'raw.jsonl')
                or reservation['raw_receipt_sha256'] != sha(case / 'receipt.json')
                or (task == 'target' and reservation['benchmark_receipt_sha256'] != sha(result_path))
                or not result.get('candidate_unchanged')):
            raise ValueError(f'episode evidence incomplete or changed: {case.name}')
        for name, expected_hash in result['candidate_artifact_sha256_after'].items():
            artifact = case / 'work' / name
            actual = sha(artifact) if artifact.is_file() and not artifact.is_symlink() else None
            if actual != expected_hash:
                raise ValueError(f'candidate changed after scoring: {case.name}/{name}')
        evidence = {'source_history': source / 'source_history.txt', 'generated_skill': source / 'generated_skill.md',
                    'published_skill': PUB_SKILL,
                    'neutral_plan': source / 'target_plans/neutral_plan/plan.md',
                    'conditioned_plan': source / 'target_plans/conditioned_plan/plan.md'}.get(condition)
        if evidence and reservation['experience_sha256'] != sha(evidence):
            raise ValueError(f'experience changed: {case.name}')
        expected_lines = evidence.read_text(encoding='utf-8').splitlines() if evidence else []
        seen_lines, read_calls, reasons = {}, 0, Counter()
        for line in (case / 'raw.jsonl').read_text(encoding='utf-8').splitlines():
            event = json.loads(line)
            part, state = event.get('part', {}), event.get('part', {}).get('state', {})
            if event.get('type') == 'step_finish':
                reasons[str(part.get('reason'))] += 1
            if (evidence and event.get('type') == 'tool_use' and part.get('tool') == 'read'
                    and state.get('input', {}).get('filePath') == '/root/source_experience.md'):
                read_calls += 1
                for entry in str(state.get('output', '')).splitlines():
                    found = re.match(r'^(\d+): ?(.*)$', entry)
                    if found:
                        index = int(found.group(1))
                        if index in seen_lines and seen_lines[index] != found.group(2):
                            raise ValueError(f'inconsistent repeated read: {case.name}')
                        seen_lines[index] = found.group(2)
        exact_read = bool(evidence and len(seen_lines) == len(expected_lines) and all(
            seen_lines.get(i) == expected_lines[i - 1] for i in range(1, len(expected_lines) + 1)))
        usage, calls = receipt['step_finish_tokens'], receipt['model_http_requests']
        rows[(task, condition)] = {'episode': case.name, 'task': task, 'condition': condition,
            'agent_exit': receipt['agent_exit'], 'benchmark_exit': result['exit'], 'benchmark_summary': result['summary'],
            'failed_names': result['failed_names'], 'postcheck_seconds': result['seconds'],
            'http_post': sum(call.startswith('POST ') for call in calls),
            'denied': [call for call in calls if call.startswith('DENIED')],
            'reported_tokens': sum(item.get('total', 0) for item in usage),
            'cache_read_included': sum(item.get('cache', {}).get('read', 0) for item in usage),
            'elapsed_seconds': receipt['elapsed_seconds'], 'finish_reasons': dict(reasons),
            'workspace_changes': workspace_changes(case / 'work'),
            'experience_read_calls': read_calls, 'experience_lines_seen': len(seen_lines),
            'experience_lines_total': len(expected_lines), 'experience_read_exact': exact_read,
            'raw_sha256': sha(case / 'raw.jsonl'), 'benchmark_receipt_sha256': sha(result_path)}
    if set(rows) != expected:
        raise ValueError(f'missing/unexpected episodes: {set(rows) ^ expected}')
    ordered = [rows[key] for key in sorted(rows)]
    usage = skill_ledger['usage'] or {}
    plans = {}
    for condition in ('neutral_plan', 'conditioned_plan'):
        directory = source / 'target_plans' / condition
        ledger = json.loads((directory / 'ledger.json').read_text(encoding='utf-8'))
        if (ledger['status'] != 'RECEIVED' or sha(directory / 'request.json') != ledger['request_sha256']
                or sha(directory / 'plan.md') != ledger['plan_sha256']
                or sha(directory / 'response.json') != ledger['response_sha256']):
            raise ValueError(f'plan ledger changed: {condition}')
        plans[condition] = {'http_post': ledger['http_attempts'], 'usage': ledger['usage'],
                            'plan_sha256': ledger['plan_sha256'],
                            'finish_reason': json.loads((directory / 'response.json').read_text(encoding='utf-8'))
                                             ['choices'][0].get('finish_reason')}
    summary = {'scope': 'SOURCE_EXPOSED_FIXED_REAL_REPO_SYNTHETIC_REQUIREMENTS_DEVELOPMENT', 'cases': ordered,
        'agent_http_post': sum(row['http_post'] for row in ordered),
        'agent_reported_tokens': sum(row['reported_tokens'] for row in ordered),
        'cache_read_included': sum(row['cache_read_included'] for row in ordered),
        'skill_generation_http_post': skill_ledger['http_attempts'], 'skill_generation_usage': usage,
        'skill_generation_finish_reason': json.loads((source / 'skill_generation_response.json')
                                                      .read_text(encoding='utf-8'))['choices'][0].get('finish_reason'),
        'posthoc_target_plans': plans,
        'skill_generation_request_reconstructed_sha256': sha(source / 'skill_generation_request_reconstructed.json'),
        'notes': 'Source and target have the same repository; cache reads are included in reported totals. '
                 'The skill request was reconstructed after the call and matched the previously recorded hash.'}
    path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'summary': str(path), 'sha256': sha(path), 'agent_http_post': summary['agent_http_post'],
                      'agent_reported_tokens': summary['agent_reported_tokens'],
                      'skill_generation_tokens': usage.get('total_tokens')}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--preflight', action='store_true')
    parser.add_argument('--task', choices=TASKS)
    parser.add_argument('--condition', choices=('none', 'source_history', 'generated_skill', 'published_skill',
                                                'neutral_plan', 'conditioned_plan'), default='none')
    parser.add_argument('--build-experience', type=Path)
    parser.add_argument('--generate-skill', type=Path)
    parser.add_argument('--reconstruct-skill-request', type=Path)
    parser.add_argument('--recheck', type=Path)
    parser.add_argument('--summarize', type=Path)
    parser.add_argument('--make-target-plan', choices=('neutral_plan', 'conditioned_plan'))
    parser.add_argument('--independent-probe', action='store_true')
    args = parser.parse_args()
    if args.preflight:
        validate()
        for name in TASKS:
            derived_harness(name, 'none', None)
        print(json.dumps({'status': 'READY_NO_MODEL_CALL', 'qualification_sha256': QUAL_SHA}))
    elif args.build_experience:
        build_experience(args.build_experience)
    elif args.recheck:
        recheck(args.recheck)
    elif args.generate_skill:
        generate_skill(args.generate_skill)
    elif args.reconstruct_skill_request:
        reconstruct_skill_request(args.reconstruct_skill_request)
    elif args.summarize:
        summarize(args.summarize)
    elif args.make_target_plan:
        make_target_plan(args.make_target_plan)
    elif args.independent_probe:
        independent_probe()
    elif args.task:
        run(args.task, args.condition)
    else:
        parser.error('select a task, experience action, or preflight')
