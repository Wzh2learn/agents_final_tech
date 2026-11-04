#!/usr/bin/env python3
"""Run the fixed source/target skill protocol on a public SymPy checkout."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
import zipfile

import run_swe_aiohttp_20261104 as common
from qualify_swe_sympy_20261104 import OUT as QUAL, SYMPY, SYMPY_REV

QUAL_SHA = 'e725bd55c4a5583340196bc8a08b3aff48d985d5a3157035e366653271ea8b20'
RUNS = common.ROOT / 'swe_sympy_agent_20261104'
PROBE_ROOT = common.ROOT / 'swe_sympy_independent_probe_20261104'
GENERAL_ROOT = common.ROOT / 'swe_sympy_general_extension_20261104'
NATIVE_ROOT = common.ROOT / 'swe_sympy_native_probe_20261104'
HYPOTHESIS_ROOT = common.ROOT / 'sympy_hypothesis_env_20261104'
HYPOTHESIS_MANIFEST_SHA = '535659f88bae86059cac418c39634ff14d140eb555828fb7753584225c06d459'
STEM = 'sympy-symbolic-math'
IMAGE = common.IMAGE
TASKS = {'source': 1, 'target': 2}
common.AIO, common.AIO_REV, common.QUAL, common.QUAL_SHA = SYMPY, SYMPY_REV, QUAL, QUAL_SHA
common.RUNS, common.TASK_FILE_STEM = RUNS, STEM
common.PUB_SKILL = common.BENCH / f'skills/{STEM}/SKILL.md'


def validate() -> dict:
    if common.sha(common.BASE) != common.BASE_SHA or common.sha(QUAL / 'receipt.json') != QUAL_SHA:
        raise ValueError('base harness or SymPy qualification changed')
    qual = json.loads((QUAL / 'receipt.json').read_text(encoding='utf-8'))
    if (qual['benchmark_revision'] != common.BENCH_REV or qual['repository_revision'] != SYMPY_REV
            or qual['image_id'] != IMAGE):
        raise ValueError('qualification identity mismatch')
    for path, rev in ((SYMPY, SYMPY_REV), (common.BENCH, common.BENCH_REV)):
        actual = subprocess.check_output(['git', '-C', str(path), 'rev-parse', 'HEAD'], text=True).strip()
        if actual != rev or subprocess.check_output(['git', '-C', str(path), 'status', '--porcelain'], text=True).strip():
            raise ValueError('upstream checkout changed or is not clean')
    for batch in (1, 2):
        positive, empty = (qual['cases'][f'batch{batch}_{condition}'] for condition in ('positive', 'empty'))
        task = common.BENCH / f'tasks/batch{batch}/{STEM}.md'
        hidden = common.BENCH / f'tests/batch{batch}/test_sympy_symbolic_math.py'
        if (positive['exit'] != 0 or empty['exit'] != 1 or common.sha(task) != positive['task_sha256']
                or common.sha(hidden) != positive['benchmark_test_sha256']):
            raise ValueError('qualification controls or task hashes changed')
    return qual


def derive(task: str, condition: str, experience: Path | None) -> str:
    code = common.BASE.read_text(encoding='utf-8')
    marker = '# A completely separate non-agent container mounts verifier after the episode;'
    if code.count(marker) != 1 or code.count("receipt={'task':task") != 1:
        raise ValueError('cannot isolate base post-run verification')
    code = code.split(marker, 1)[0] + "\nvrc=None\nreceipt={'task':task" + code.split("receipt={'task':task", 1)[1]
    batch = TASKS[task]
    source_code = (
        "src=UP/task\n"
        f"shutil.copytree(Path({str(SYMPY)!r}),work,dirs_exist_ok=True,"
        "ignore=shutil.ignore_patterns('.git','__pycache__','.pytest_cache'))\n"
        "work.chmod(0o777)\n"
        "for p in ('sympy/calculus','sympy/calculus/tests','sympy/matrices','sympy/matrices/tests'): "
        "(work/p).chmod(0o777)\n"
        "for p in ('sympy/calculus/__init__.py','sympy/matrices/__init__.py'): (work/p).chmod(0o666)\n"
        + ("(work/'source_experience.md').touch(mode=0o444)\n" if experience else '')
    )
    edits = [
        ("ROOT=Path('/home/testuser/wzh/research_evidence/agent_skill_method_20261029')", f'ROOT=Path({str(common.RUNS)!r})', 1),
        ("UP=Path('/home/testuser/wzh/research_evidence/agent_frontier_20261029/skillsbench_v1_1/tasks')", f'UP=Path({str(common.BENCH / "tasks")!r})', 1),
        ("if task not in ('llm-prefix-cache-replay','dialogue-parser','tictoc-unnecessary-abort-detection') or arm not in ('no_skill','all_skill','select_skill'): raise SystemExit('unsupported')",
         f"if task not in {tuple(TASKS)!r} or arm != 'no_skill': raise SystemExit('unsupported')", 1),
        ("case=ROOT/(task+'__'+arm+'__'+str(os.getpid()))",
         f"case=ROOT/(task+'__{condition}__'+str(os.getpid()))", 1),
        ('src=UP/task', source_code, 1),
        ("body=(src/'task.md').read_text(encoding='utf8').split('---',2)[2].strip()",
         f"body=(UP/'batch{batch}'/'{STEM}.md').read_text(encoding='utf8').strip()", 1),
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
        code = common.replace_once(code, old, new, count)
    if experience:
        code = common.replace_once(code, 'Use available tools to implement and execute your solution.',
                                   'Before solving, read /root/source_experience.md, assess what applies, '
                                   'and follow the current task. Use available tools to implement and execute your solution.')
    mounts = (f"['--mount','type=bind,src={common.DEPS},dst=/deps,readonly',"
              "'-e','PYTHONDONTWRITEBYTECODE=1','-e','PYTEST_DISABLE_PLUGIN_AUTOLOAD=1']")
    if experience:
        mounts += f"+['--mount','type=bind,src={experience},dst=/root/source_experience.md,readonly']"
    code = common.replace_once(code, 'server=Server(str(sockpath),Handler);',
                               f"_at=cmd.index({IMAGE!r}); cmd[_at:_at]={mounts}; server=Server(str(sockpath),Handler);")
    compile(code, str(common.BASE), 'exec')
    return code


def postcheck(batch: int, case: Path) -> dict:
    hidden = common.BENCH / f'tests/batch{batch}/test_sympy_symbolic_math.py'
    work, log = case / 'work', case / 'benchmark_pytest.log'
    if log.exists() or not (work.stat().st_mode & 0o002):
        raise ValueError('invalid evaluation workspace or existing log')
    names = (('sympy/calculus/taylor.py', 'sympy/calculus/__init__.py', 'sympy/calculus/tests/test_taylor.py')
             if batch == 1 else ('sympy/matrices/charutil.py', 'sympy/matrices/__init__.py',
                                 'sympy/matrices/tests/test_charutil.py'))
    def hashes() -> dict:
        return {name: common.sha(work / name) if (work / name).is_file() and not (work / name).is_symlink()
                else None for name in names}
    before = hashes()
    name = f'swe-sympy-eval-{os.getpid()}'
    cmd = ['docker', 'run', '--name', name, '--rm', '--pull', 'never', '--network', 'none', '--read-only',
           '--cpus', '2', '--memory', '3g', '--pids-limit', '256', '--cap-drop', 'ALL',
           '--security-opt', 'no-new-privileges', '--tmpfs', '/tmp:rw,nosuid,size=128m',
           '-e', 'PYTHONPATH=/workspace/sympy', '-e', 'PYTHONDONTWRITEBYTECODE=1',
           '-e', 'PYTEST_DISABLE_PLUGIN_AUTOLOAD=1',
           '--mount', f'type=bind,src={work},dst=/workspace/sympy',
           '--mount', f'type=bind,src={hidden},dst=/checks/test_sympy_symbolic_math.py,readonly',
           '--mount', f'type=bind,src={common.DEPS},dst=/deps,readonly', '--workdir', '/workspace/sympy',
           '--entrypoint', 'python3', IMAGE, '-m', 'pytest', '-q', '-p', 'no:cacheprovider',
           '/checks/test_sympy_symbolic_math.py']
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
    failed = [line.split(' - ', 1)[0] for line in text.splitlines() if line.startswith('FAILED ')]
    after = hashes()
    return {'exit': exit_code, 'summary': summary, 'failed_names': failed,
            'candidate_artifact_sha256_before': before, 'candidate_artifact_sha256_after': after,
            'candidate_unchanged': before == after, 'seconds': round(time.monotonic() - start, 3),
            'benchmark_test_sha256': common.sha(hidden), 'log_sha256': common.sha(log), 'evaluator_image': IMAGE}


def build_experience(case: Path) -> None:
    case = case.resolve(strict=True)
    if RUNS.resolve() not in case.parents or not case.name.startswith('source__none__'):
        raise ValueError('source episode is not eligible')
    receipt = json.loads((case / 'receipt.json').read_text(encoding='utf-8'))
    feedback_path = case / 'benchmark_receipt.json'
    feedback = json.loads(feedback_path.read_text(encoding='utf-8'))
    raw = case / 'raw.jsonl'
    if receipt['raw_sha256'] != common.sha(raw) or not feedback.get('candidate_unchanged'):
        raise ValueError('source feedback or raw is not bound to unchanged artifacts')
    actions = []
    for line in raw.read_text(encoding='utf-8').splitlines():
        event = json.loads(line)
        if event.get('type') == 'tool_use':
            part, state = event.get('part', {}), event.get('part', {}).get('state', {})
            input_text = json.dumps(state.get('input', {}), ensure_ascii=False, separators=(',', ':'))
            output_text = str(state.get('output', ''))
            actions.append({'tool': part.get('tool'), 'status': state.get('status'),
                            'input_prefix': input_text[:1600], 'input_chars': len(input_text),
                            'input_sha256': hashlib.sha256(input_text.encode()).hexdigest(),
                            'output_tail': output_text[-1600:], 'output_chars': len(output_text)})
    if not actions:
        raise ValueError('no source actions')
    output = case / 'work/sympy/calculus/taylor.py'
    source_code = output.read_text(encoding='utf-8')[:16000] if output.is_file() and not output.is_symlink() else None
    content = {'source_instruction': (case / 'work/instructions.txt').read_text(encoding='utf-8'),
               'source_actions': actions, 'source_code_prefix': source_code,
               'source_feedback': {'exit': feedback['exit'], 'summary': feedback['summary'],
                                   'failed_test_names': feedback['failed_names']},
               'scope': 'all source actions with input prefix and output tail clipped to 1600 chars; '
                        'source code prefix limited to 16000 chars; source-only feedback'}
    encoded = json.dumps(content, ensure_ascii=False, separators=(',', ':'))
    pieces = [encoded[i:i + 700] for i in range(0, len(encoded), 700)]
    readable = ('Source-only task history. The current task may differ. Concatenate text after | '
                'on numbered lines to reconstruct the JSON.\n'
                + ''.join(f'{i:04d}|{piece}\n' for i, piece in enumerate(pieces)))
    if ''.join(line.split('|', 1)[1] for line in readable.splitlines()[1:]) != encoded:
        raise ValueError('history wrapping is not lossless')
    history, meta = case / 'source_history.txt', case / 'experience_metadata.json'
    if history.exists() or meta.exists():
        raise FileExistsError('source experience exists')
    history.write_text(readable, encoding='utf-8')
    metadata = {'source_raw_sha256': common.sha(raw), 'source_receipt_sha256': common.sha(case / 'receipt.json'),
                'source_feedback_sha256': common.sha(feedback_path), 'history_sha256': common.sha(history),
                'history_action_count': len(actions), 'source_code_present': source_code is not None,
                'scope': content['scope']}
    meta.write_text(json.dumps(metadata, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'history': str(history), 'sha256': common.sha(history), 'actions': len(actions),
                      'source_code_present': source_code is not None}))


PROBE = r'''
import json
try:
    from sympy import Matrix, Symbol, diag, expand, simplify, Float
    from sympy.matrices import characteristic_data
    from sympy.matrices.exceptions import NonSquareMatrixError
except Exception as exc:
    print(json.dumps({'import_error': type(exc).__name__}))
    raise SystemExit(0)

result = {}
lam = Symbol('lambda')
for label, matrix in [('one_by_one', Matrix([[2]])), ('three_by_three', diag(1, 2, 3))]:
    try:
        value = characteristic_data(matrix, lam)
        expected = expand((matrix - lam*Matrix.eye(matrix.rows)).det())
        result[label] = {'pass': simplify(value['char_poly'] - expected) == 0}
    except Exception as exc:
        result[label] = {'pass': False, 'error': type(exc).__name__}
try:
    value = characteristic_data(Matrix([[2, 0], [0, 3]]), lam)
    result['exact'] = {'pass': value['determinant'] == 6 and not value['determinant'].has(Float)
                       and value['trace'] == 5 and value['eigenvalues'] == {2: 1, 3: 1}}
except Exception as exc:
    result['exact'] = {'pass': False, 'error': type(exc).__name__}
try:
    characteristic_data(Matrix([[1, 2, 3], [4, 5, 6]]), lam)
    result['non_square'] = {'pass': False, 'error': 'no_error'}
except NonSquareMatrixError:
    result['non_square'] = {'pass': True}
except Exception as exc:
    result['non_square'] = {'pass': False, 'error': type(exc).__name__}
print(json.dumps(result, sort_keys=True))
'''


def execute_probe(work: Path, script: Path, label: str, output: Path) -> dict:
    name = f'independent-sympy-{os.getpid()}-{label}'
    cmd = ['docker', 'run', '--name', name, '--rm', '--pull', 'never', '--network', 'none', '--read-only',
           '--cpus', '2', '--memory', '3g', '--pids-limit', '256', '--cap-drop', 'ALL',
           '--security-opt', 'no-new-privileges', '--tmpfs', '/tmp:rw,nosuid,size=64m',
           '-e', 'PYTHONPATH=/workspace/sympy', '-e', 'PYTHONDONTWRITEBYTECODE=1',
           '--mount', f'type=bind,src={work},dst=/workspace/sympy,readonly',
           '--mount', f'type=bind,src={script},dst=/check/probe.py,readonly',
           '--mount', f'type=bind,src={common.DEPS},dst=/deps,readonly',
           '--entrypoint', 'python3', IMAGE, '/check/probe.py']
    start = time.monotonic()
    try:
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30, check=False)
        exit_code, stdout, stderr = proc.returncode, proc.stdout, proc.stderr
    except subprocess.TimeoutExpired as exc:
        exit_code, stdout, stderr = 124, exc.stdout or b'', exc.stderr or b''
        subprocess.run(['docker', 'kill', name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                       timeout=10, check=False)
    log, err = output / f'{label}.stdout', output / f'{label}.stderr'
    log.write_bytes(stdout)
    err.write_bytes(stderr)
    parsed = None
    if exit_code == 0:
        try:
            parsed = json.loads(stdout.decode('utf-8').splitlines()[-1])
        except (ValueError, IndexError, UnicodeDecodeError):
            pass
    return {'label': label, 'exit': exit_code, 'seconds': round(time.monotonic() - start, 3),
            'stdout_sha256': common.sha(log), 'stderr_sha256': common.sha(err), 'result': parsed}


def prepare_probe() -> None:
    validate()
    if PROBE_ROOT.exists():
        raise FileExistsError('probe already exists')
    PROBE_ROOT.mkdir()
    script = PROBE_ROOT / 'probe.py'
    script.write_text(PROBE, encoding='utf-8')
    positive = execute_probe(QUAL / 'batch2_positive/sympy', script, 'control_positive', PROBE_ROOT)
    empty = execute_probe(QUAL / 'batch2_empty/sympy', script, 'control_empty', PROBE_ROOT)
    receipt = PROBE_ROOT / 'pre_run_controls.json'
    receipt.write_text(json.dumps({'scope': 'PRE_AGENT_DEVELOPMENT_CONTROLS', 'probe_sha256': common.sha(script),
                                   'positive': positive, 'empty': empty}, indent=2) + '\n', encoding='utf-8')
    if (positive['exit'] != 0 or not isinstance(positive['result'], dict)
            or not all(positive['result'].get(key, {}).get('pass')
                       for key in ('one_by_one', 'three_by_three', 'exact', 'non_square'))
            or empty['exit'] != 0 or not (empty['result'] or {}).get('import_error')):
        raise ValueError(f'probe controls failed; evidence preserved in {receipt}')
    print(json.dumps({'receipt': str(receipt), 'sha256': common.sha(receipt), 'probe_sha256': common.sha(script)}))


def probe_targets() -> None:
    validate()
    controls = json.loads((PROBE_ROOT / 'pre_run_controls.json').read_text(encoding='utf-8'))
    script = PROBE_ROOT / 'probe.py'
    if controls['probe_sha256'] != common.sha(script):
        raise ValueError('frozen probe changed')
    targets = sorted(p for p in RUNS.iterdir() if p.is_dir() and p.name.startswith('target__'))
    if len(targets) != 6:
        raise ValueError('expected six target candidates')
    out = PROBE_ROOT / 'target_results'
    out.mkdir(exist_ok=False)
    rows = []
    for index, case in enumerate(targets):
        result = json.loads((case / 'benchmark_receipt.json').read_text(encoding='utf-8'))
        work = case / 'work'
        path = work / 'sympy/matrices/charutil.py'
        before = common.sha(path) if path.is_file() and not path.is_symlink() else None
        if before != result['candidate_artifact_sha256_after']['sympy/matrices/charutil.py']:
            raise ValueError('candidate changed before independent probe')
        row = execute_probe(work, script, f'candidate_{index}', out)
        after = common.sha(path) if path.is_file() and not path.is_symlink() else None
        row.update({'case': case.name, 'candidate_sha256': before, 'candidate_unchanged': before == after})
        rows.append(row)
    receipt = out / 'receipt.json'
    receipt.write_text(json.dumps({'scope': 'PREDECLARED_SOURCE_EXPOSED_DEVELOPMENT_PROBE',
                                   'probe_sha256': common.sha(script), 'cases': rows}, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'receipt': str(receipt), 'sha256': common.sha(receipt), 'cases': rows}))


def extract_general(text: str) -> str:
    """Keep one named section intact, including any task-specific examples within it."""
    sections = re.findall(r'(?ms)^## General Steps[^\n]*\n(.*?)(?=^## |\Z)', text)
    if len(sections) != 1 or not sections[0].strip():
        raise ValueError('expected one nonempty general section')
    return '# Source experience: general section only\n\n## General Steps\n\n' + sections[0].strip() + '\n'


def prepare_general() -> None:
    """Freeze the existing general section after observing two development arms."""
    validate()
    sources = sorted(p for p in RUNS.iterdir() if p.is_dir() and p.name.startswith('source__none__'))
    if len(sources) != 1 or GENERAL_ROOT.exists():
        raise ValueError('expected one source and a new extension directory')
    source = sources[0]
    meta = json.loads((source / 'experience_metadata.json').read_text(encoding='utf-8'))
    skill = source / 'generated_skill.md'
    if common.sha(skill) != meta['skill_sha256']:
        raise ValueError('source skill changed')
    content = extract_general(skill.read_text(encoding='utf-8'))
    GENERAL_ROOT.mkdir()
    general = GENERAL_ROOT / 'general_only.md'
    general.write_text(content, encoding='utf-8')
    receipt = GENERAL_ROOT / 'pre_run_receipt.json'
    receipt.write_text(json.dumps({
        'scope': 'POST_HOC_SOURCE_SECTION_DEVELOPMENT', 'source_case': str(source),
        'source_skill_sha256': common.sha(skill), 'general_sha256': common.sha(general),
        'selection': 'one existing General Steps section; examples within that section are retained',
        'observed_before_selection': ['target none 13/15', 'target source history 14/15'],
        'limitations': 'content and length change together; not a single-factor causal estimate',
    }, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'general': str(general), 'sha256': common.sha(general),
                      'receipt_sha256': common.sha(receipt)}))


def run_general() -> None:
    """Reuse the normal agent runner with an explicitly labeled general-only input."""
    receipt = json.loads((GENERAL_ROOT / 'pre_run_receipt.json').read_text(encoding='utf-8'))
    general = GENERAL_ROOT / 'general_only.md'
    if common.sha(general) != receipt['general_sha256']:
        raise ValueError('general-only input changed')
    common.RUNS, common.PUB_SKILL = GENERAL_ROOT, general
    common.run('target', 'general_only')


def probe_general() -> None:
    validate()
    controls = json.loads((PROBE_ROOT / 'pre_run_controls.json').read_text(encoding='utf-8'))
    script = PROBE_ROOT / 'probe.py'
    pre = json.loads((GENERAL_ROOT / 'pre_run_receipt.json').read_text(encoding='utf-8'))
    general = GENERAL_ROOT / 'general_only.md'
    if common.sha(script) != controls['probe_sha256'] or common.sha(general) != pre['general_sha256']:
        raise ValueError('probe or general input changed')
    cases = sorted(p for p in GENERAL_ROOT.iterdir()
                   if p.is_dir() and re.fullmatch(r'target__general_only__\d+', p.name))
    if len(cases) != 1:
        raise ValueError('expected one general-only candidate')
    case = cases[0]
    reservation = json.loads((GENERAL_ROOT / (case.name + '.reservation.json')).read_text(encoding='utf-8'))
    receipt = json.loads((case / 'receipt.json').read_text(encoding='utf-8'))
    result = json.loads((case / 'benchmark_receipt.json').read_text(encoding='utf-8'))
    if (reservation['status'] != 'COMPLETED' or reservation['experience_sha256'] != common.sha(general)
            or reservation['raw_receipt_sha256'] != common.sha(case / 'receipt.json')
            or reservation['benchmark_receipt_sha256'] != common.sha(case / 'benchmark_receipt.json')
            or receipt['raw_sha256'] != common.sha(case / 'raw.jsonl') or not result['candidate_unchanged']):
        raise ValueError('general-only case evidence changed')
    for name, expected in result['candidate_artifact_sha256_after'].items():
        artifact = case / 'work' / name
        actual = common.sha(artifact) if artifact.is_file() and not artifact.is_symlink() else None
        if actual != expected:
            raise ValueError('candidate changed before probe')
    out = GENERAL_ROOT / 'probe_result'
    out.mkdir(exist_ok=False)
    probe = execute_probe(case / 'work', script, 'candidate', out)
    lines = general.read_text(encoding='utf-8').splitlines()
    seen, reads = {}, 0
    for line in (case / 'raw.jsonl').read_text(encoding='utf-8').splitlines():
        event = json.loads(line)
        part, state = event.get('part', {}), event.get('part', {}).get('state', {})
        if (event.get('type') == 'tool_use' and part.get('tool') == 'read'
                and state.get('input', {}).get('filePath') == '/root/source_experience.md'):
            reads += 1
            for entry in str(state.get('output', '')).splitlines():
                found = re.match(r'^(\d+): ?(.*)$', entry)
                if found:
                    seen[int(found.group(1))] = found.group(2)
    usage, calls = receipt['step_finish_tokens'], receipt['model_http_requests']
    summary = {'scope': 'POST_HOC_SOURCE_SECTION_DEVELOPMENT', 'case': case.name,
               'agent_exit': receipt['agent_exit'], 'benchmark_exit': result['exit'],
               'benchmark_summary': result['summary'], 'failed_names': result['failed_names'],
               'http_post': sum(x.startswith('POST ') for x in calls),
               'denied': [x for x in calls if x.startswith('DENIED')],
               'reported_tokens': sum(x.get('total', 0) for x in usage),
               'cache_read_included': sum(x.get('cache', {}).get('read', 0) for x in usage),
               'elapsed_seconds': receipt['elapsed_seconds'], 'experience_reads': reads,
               'experience_lines_seen': len(seen), 'experience_lines_total': len(lines),
               'experience_read_exact': len(seen) == len(lines) and all(
                   seen.get(i) == lines[i - 1] for i in range(1, len(lines) + 1)),
               'general_sha256': common.sha(general), 'raw_sha256': common.sha(case / 'raw.jsonl'),
               'benchmark_receipt_sha256': common.sha(case / 'benchmark_receipt.json'),
               'probe_sha256': common.sha(script), 'probe': probe}
    target = out / 'summary.json'
    target.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'summary': str(target), 'sha256': common.sha(target), 'result': summary}))


def validate_hypothesis_overlay() -> dict:
    """Check pinned PyPI wheel bytes and every extracted file before use."""
    manifest = HYPOTHESIS_ROOT / 'manifest.json'
    if common.sha(manifest) != HYPOTHESIS_MANIFEST_SHA:
        raise ValueError('hypothesis overlay manifest changed')
    data = json.loads(manifest.read_text(encoding='utf-8'))
    site = HYPOTHESIS_ROOT / 'site'
    expected_files = set()
    for package in data['packages']:
        wheel = HYPOTHESIS_ROOT / package['filename']
        if common.sha(wheel) != package['sha256']:
            raise ValueError('wheel changed')
        with zipfile.ZipFile(wheel) as archive:
            for member in archive.infolist():
                if member.is_dir():
                    continue
                path = (site / member.filename).resolve()
                if not path.is_relative_to(site.resolve()) or not path.is_file():
                    raise ValueError('unsafe or missing extracted wheel member')
                if hashlib.sha256(archive.read(member)).hexdigest() != common.sha(path):
                    raise ValueError('extracted wheel member changed')
                expected_files.add(path)
    actual = {p.resolve() for p in site.rglob('*') if p.is_file()}
    if actual != expected_files:
        raise ValueError('unexpected files in hypothesis overlay')
    return data


def run_native_test(work: Path, label: str, overlay: bool, output: Path) -> dict:
    """Run the task's own pytest file in an isolated post-hoc environment."""
    name = f'native-sympy-{os.getpid()}-{label}'
    pythonpath = '/workspace/sympy:/extra:/deps' if overlay else '/workspace/sympy:/deps'
    cmd = ['docker', 'run', '--name', name, '--rm', '--pull', 'never', '--network', 'none', '--read-only',
           '--cpus', '2', '--memory', '3g', '--pids-limit', '256', '--cap-drop', 'ALL',
           '--security-opt', 'no-new-privileges', '--tmpfs', '/tmp:rw,nosuid,size=128m',
           '-e', f'PYTHONPATH={pythonpath}', '-e', 'PYTHONDONTWRITEBYTECODE=1',
           '-e', 'PYTEST_DISABLE_PLUGIN_AUTOLOAD=1', '-e', 'HYPOTHESIS_STORAGE_DIRECTORY=/tmp/hypothesis',
           '--mount', f'type=bind,src={work},dst=/workspace/sympy,readonly',
           '--mount', f'type=bind,src={common.DEPS},dst=/deps,readonly']
    if overlay:
        cmd += ['--mount', f'type=bind,src={HYPOTHESIS_ROOT / "site"},dst=/extra,readonly']
    cmd += ['--workdir', '/workspace/sympy', '--entrypoint', 'python3', IMAGE, '-m', 'pytest',
            'sympy/matrices/tests/test_charutil.py', '-q', '-p', 'no:cacheprovider']
    started = time.monotonic()
    try:
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=180, check=False)
        code, data = proc.returncode, proc.stdout
    except subprocess.TimeoutExpired as exc:
        code, data = 124, exc.stdout or b''
        subprocess.run(['docker', 'kill', name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                       timeout=10, check=False)
    log = output / f'{label}.log'
    log.write_bytes(data)
    text = data.decode('utf-8', errors='replace')
    result_line = next((line.strip() for line in reversed(text.splitlines())
                        if re.search(r'\d+ (?:passed|failed|error)', line)), '')
    return {'label': label, 'overlay': overlay, 'exit': code, 'summary': result_line,
            'hypothesis_missing': 'hypothesis is a required dependency' in text.lower(),
            'seconds': round(time.monotonic() - started, 3), 'log_sha256': common.sha(log)}


def native_probe() -> None:
    """Contrast the original and repaired test environments on frozen artifacts."""
    validate()
    packages = validate_hypothesis_overlay()
    if NATIVE_ROOT.exists():
        raise FileExistsError('native probe directory already exists')
    NATIVE_ROOT.mkdir()
    positive = QUAL / 'batch2_positive/sympy'
    controls = [run_native_test(positive, 'positive_original', False, NATIVE_ROOT),
                run_native_test(positive, 'positive_overlay', True, NATIVE_ROOT)]
    controls_path = NATIVE_ROOT / 'controls.json'
    controls_path.write_text(json.dumps(controls, indent=2) + '\n', encoding='utf-8')
    if (controls[0]['exit'] == 0 or not controls[0]['hypothesis_missing'] or controls[1]['exit'] != 0):
        raise ValueError('native environment controls failed; logs preserved')
    cases = sorted(p for p in RUNS.iterdir() if p.is_dir() and p.name.startswith('target__'))
    cases += sorted(p for p in GENERAL_ROOT.iterdir() if p.is_dir() and p.name.startswith('target__general_only__'))
    if len(cases) != 7:
        raise ValueError('expected six primary and one post-hoc target candidates')
    results = []
    for index, case in enumerate(cases):
        score = json.loads((case / 'benchmark_receipt.json').read_text(encoding='utf-8'))
        for name, expected in score['candidate_artifact_sha256_after'].items():
            artifact = case / 'work' / name
            actual = common.sha(artifact) if artifact.is_file() and not artifact.is_symlink() else None
            if actual != expected:
                raise ValueError('candidate changed before native probe')
        trial = run_native_test(case / 'work', f'candidate_{index}', True, NATIVE_ROOT)
        trial.update({'case': case.name, 'benchmark_receipt_sha256': common.sha(case / 'benchmark_receipt.json')})
        results.append(trial)
    summary = {'scope': 'POST_HOC_NATIVE_TEST_WITH_PINNED_PRIVATE_OVERLAY',
               'limitations': 'Artifacts were produced in the original environment; overlay is not evidence '
                              'that agents ran or passed tests during their own episodes.',
               'overlay_manifest_sha256': HYPOTHESIS_MANIFEST_SHA, 'packages': packages['packages'],
               'controls': controls, 'cases': results}
    path = NATIVE_ROOT / 'summary.json'
    path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'summary': str(path), 'sha256': common.sha(path), 'results': results}))


def summarize(path: Path) -> None:
    if path.exists():
        raise FileExistsError('summary already exists')
    cases = sorted(p for p in RUNS.iterdir() if p.is_dir())
    sources = [p for p in cases if p.name.startswith('source__none__')]
    if len(sources) != 1:
        raise ValueError('expected one source episode')
    source = sources[0]
    metadata = json.loads((source / 'experience_metadata.json').read_text(encoding='utf-8'))
    skill = json.loads((source / 'skill_generation_ledger.json').read_text(encoding='utf-8'))
    if (common.sha(source / 'raw.jsonl') != metadata['source_raw_sha256']
            or common.sha(source / 'benchmark_receipt.json') != metadata['source_feedback_sha256']
            or common.sha(source / 'source_history.txt') != metadata['history_sha256']
            or common.sha(source / 'generated_skill.md') != metadata['skill_sha256']
            or skill['status'] != 'RECEIVED' or skill['skill_sha256'] != metadata['skill_sha256']):
        raise ValueError('source experience changed')
    expected = {('source', 'none')} | {('target', condition) for condition in
        ('none', 'source_history', 'generated_skill', 'published_skill', 'neutral_plan', 'conditioned_plan')}
    rows = {}
    for case in cases:
        match = re.fullmatch(r'(source|target)__(none|source_history|generated_skill|published_skill|neutral_plan|conditioned_plan)__(\d+)', case.name)
        if not match or (match[1], match[2]) in rows:
            raise ValueError(f'unexpected or duplicate episode: {case.name}')
        task, condition, pid = match.groups()
        reservation = json.loads((RUNS / f'{task}__{condition}__{pid}.reservation.json').read_text(encoding='utf-8'))
        receipt = json.loads((case / 'receipt.json').read_text(encoding='utf-8'))
        result_path = case / 'benchmark_receipt.json'
        result = json.loads(result_path.read_text(encoding='utf-8'))
        if (reservation['status'] != 'COMPLETED' or receipt['raw_sha256'] != common.sha(case / 'raw.jsonl')
                or reservation['raw_receipt_sha256'] != common.sha(case / 'receipt.json')
                or reservation['benchmark_receipt_sha256'] != common.sha(result_path)
                or not result.get('candidate_unchanged')):
            raise ValueError(f'episode evidence changed: {case.name}')
        for name, expected_hash in result['candidate_artifact_sha256_after'].items():
            artifact = case / 'work' / name
            actual = common.sha(artifact) if artifact.is_file() and not artifact.is_symlink() else None
            if actual != expected_hash:
                raise ValueError(f'candidate changed after scoring: {case.name}/{name}')
        evidence = {'source_history': source / 'source_history.txt', 'generated_skill': source / 'generated_skill.md',
                    'published_skill': common.PUB_SKILL,
                    'neutral_plan': source / 'target_plans/neutral_plan/plan.md',
                    'conditioned_plan': source / 'target_plans/conditioned_plan/plan.md'}.get(condition)
        if evidence and reservation['experience_sha256'] != common.sha(evidence):
            raise ValueError(f'experience changed: {case.name}')
        expected_lines = evidence.read_text(encoding='utf-8').splitlines() if evidence else []
        seen, reads, reasons = {}, 0, Counter()
        for line in (case / 'raw.jsonl').read_text(encoding='utf-8').splitlines():
            event = json.loads(line)
            part, state = event.get('part', {}), event.get('part', {}).get('state', {})
            if event.get('type') == 'step_finish':
                reasons[str(part.get('reason'))] += 1
            if (evidence and event.get('type') == 'tool_use' and part.get('tool') == 'read'
                    and state.get('input', {}).get('filePath') == '/root/source_experience.md'):
                reads += 1
                for entry in str(state.get('output', '')).splitlines():
                    found = re.match(r'^(\d+): ?(.*)$', entry)
                    if found:
                        index = int(found.group(1))
                        if index in seen and seen[index] != found.group(2):
                            raise ValueError('inconsistent repeated experience read')
                        seen[index] = found.group(2)
        exact = bool(evidence and len(seen) == len(expected_lines) and all(
            seen.get(i) == expected_lines[i - 1] for i in range(1, len(expected_lines) + 1)))
        usage, calls = receipt['step_finish_tokens'], receipt['model_http_requests']
        rows[(task, condition)] = {'episode': case.name, 'task': task, 'condition': condition,
            'agent_exit': receipt['agent_exit'], 'benchmark_exit': result['exit'], 'benchmark_summary': result['summary'],
            'failed_names': result['failed_names'], 'http_post': sum(x.startswith('POST ') for x in calls),
            'denied': [x for x in calls if x.startswith('DENIED')],
            'reported_tokens': sum(x.get('total', 0) for x in usage),
            'cache_read_included': sum(x.get('cache', {}).get('read', 0) for x in usage),
            'elapsed_seconds': receipt['elapsed_seconds'], 'finish_reasons': dict(reasons),
            'experience_reads': reads, 'experience_lines_seen': len(seen),
            'experience_lines_total': len(expected_lines), 'experience_read_exact': exact,
            'raw_sha256': common.sha(case / 'raw.jsonl'), 'benchmark_receipt_sha256': common.sha(result_path)}
    if set(rows) != expected:
        raise ValueError(f'missing or unexpected episodes: {set(rows) ^ expected}')
    plans = {}
    for condition in ('neutral_plan', 'conditioned_plan'):
        directory = source / 'target_plans' / condition
        ledger = json.loads((directory / 'ledger.json').read_text(encoding='utf-8'))
        if (ledger['status'] != 'RECEIVED' or common.sha(directory / 'request.json') != ledger['request_sha256']
                or common.sha(directory / 'response.json') != ledger['response_sha256']
                or common.sha(directory / 'plan.md') != ledger['plan_sha256']):
            raise ValueError('target plan ledger changed')
        plans[condition] = {'http_post': ledger['http_attempts'], 'usage': ledger['usage'],
                            'finish_reason': json.loads((directory / 'response.json').read_text(encoding='utf-8'))
                                             ['choices'][0].get('finish_reason')}
    ordered = [rows[key] for key in sorted(rows)]
    result = {'scope': 'SOURCE_EXPOSED_FIXED_SYMPY_SYNTHETIC_REQUIREMENTS_DEVELOPMENT', 'cases': ordered,
              'agent_http_post': sum(row['http_post'] for row in ordered),
              'agent_reported_tokens': sum(row['reported_tokens'] for row in ordered),
              'cache_read_included': sum(row['cache_read_included'] for row in ordered),
              'skill_generation_http_post': skill['http_attempts'], 'skill_generation_usage': skill['usage'],
              'target_plans': plans}
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'summary': str(path), 'sha256': common.sha(path), 'agent_http_post': result['agent_http_post'],
                      'agent_reported_tokens': result['agent_reported_tokens']}))


common.validate, common.derived_harness, common.postcheck = validate, derive, postcheck


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--preflight', action='store_true')
    parser.add_argument('--task', choices=TASKS)
    parser.add_argument('--condition', choices=('none', 'source_history', 'generated_skill', 'published_skill',
                                                'neutral_plan', 'conditioned_plan'), default='none')
    parser.add_argument('--build-experience', type=Path)
    parser.add_argument('--generate-skill', type=Path)
    parser.add_argument('--make-target-plan', choices=('neutral_plan', 'conditioned_plan'))
    parser.add_argument('--summarize', type=Path)
    parser.add_argument('--prepare-probe', action='store_true')
    parser.add_argument('--probe-targets', action='store_true')
    parser.add_argument('--prepare-general', action='store_true')
    parser.add_argument('--run-general', action='store_true')
    parser.add_argument('--probe-general', action='store_true')
    parser.add_argument('--native-probe', action='store_true')
    args = parser.parse_args()
    if args.preflight:
        validate()
        for task in TASKS:
            derive(task, 'none', None)
        print(json.dumps({'status': 'READY_NO_MODEL_CALL', 'qualification_sha256': QUAL_SHA}))
    elif args.build_experience:
        build_experience(args.build_experience)
    elif args.generate_skill:
        common.generate_skill(args.generate_skill)
    elif args.make_target_plan:
        common.make_target_plan(args.make_target_plan)
    elif args.summarize:
        summarize(args.summarize)
    elif args.prepare_probe:
        prepare_probe()
    elif args.probe_targets:
        probe_targets()
    elif args.prepare_general:
        prepare_general()
    elif args.run_general:
        run_general()
    elif args.probe_general:
        probe_general()
    elif args.native_probe:
        native_probe()
    elif args.task:
        common.run(args.task, args.condition)
    else:
        parser.error('select a task or an experience action')
