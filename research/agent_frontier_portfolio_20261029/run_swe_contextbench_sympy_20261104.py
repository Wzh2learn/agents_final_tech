#!/usr/bin/env python3
"""Run isolated OpenCode/Qwen on two qualified historical SymPy issues.

The runtime sees only the selected issue and its base checkout. Hidden tests are
applied to a separate evaluator copy after the agent exits. No published
historical trajectory, reference patch, host Git history, or network is mounted.
"""
from __future__ import annotations

import argparse
from collections import Counter
import difflib
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import sys
import tarfile
import time
import urllib.request

_REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
if str(_REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPOSITORY_ROOT))
from scripts.graph.research_auto_record import recorded_episode

import pyarrow.parquet as pq
import qualify_swe_contextbench_sympy_20261104 as qual

ROOT = qual.ROOT / 'swe_contextbench_sympy_agent_20261104'
BASE = Path('/home/testuser/wzh/research_evidence/agent_skill_method_20261029/run_skill_episode_output8192.py')
BASE_SHA = '4111a0be97845740769722e2e596871d51c7693d14d2372d7f6931b4d06e7afb'
QUAL_SHA = '035a76785f4a9429a26071ba02c0f8bb1e59bfc33b78ea5ad5065ba6e2be83c4'
SEED = 7201
TEMPERATURE = 0.2
MAX_HTTP_REQUESTS = 48
MAX_BYTES = 6000000
MAX_SECONDS = 1800
SHIM = 'import _distutils_hack\n_distutils_hack.add_shim()\n'

CAPTURE = r'''
def capture_sampling(first,length,recv,temperature,seed):
 header,body=first.split(b'\r\n\r\n',1)
 if length is None or length<0 or len(body)>length:raise ValueError('invalid length')
 while len(body)<length:
  chunk=recv(min(65536,length-len(body)))
  if not chunk:raise EOFError('short body')
  body+=chunk
 payload=json.loads(body.decode('utf-8'))
 if not isinstance(payload,dict):raise ValueError('non-object')
 before_temperature,before_seed=payload.get('temperature'),payload.get('seed')
 payload['temperature'],payload['seed']=temperature,seed
 body=json.dumps(payload,ensure_ascii=False,separators=(',',':')).encode('utf-8')
 lines=header.split(b'\r\n')
 matches=[i for i,line in enumerate(lines) if line.lower().startswith(b'content-length:')]
 if len(matches)!=1:raise ValueError('ambiguous length')
 lines[matches[0]]=b'Content-Length: '+str(len(body)).encode('ascii')
 metadata={k:payload.get(k) for k in ('model','temperature','seed','top_p','max_tokens','max_completion_tokens')}
 metadata.update({'temperature_before':before_temperature,'seed_before':before_seed,
                  'original_length':length,'forwarded_length':len(body)})
 return b'\r\n'.join(lines)+b'\r\n\r\n'+body,metadata,len(body)
'''


def replace_once(text: str, old: str, new: str, count: int = 1) -> str:
    if text.count(old) != count:
        raise ValueError(f'unexpected base harness fragment: {old[:80]!r}')
    return text.replace(old, new, count)


def verify_clean_base(label: str) -> None:
    spec = qual.CASES[label]
    base, archive = qual.OUT / label / 'clean_base', qual.ROOT / spec['archive']
    if qual.sha(archive) != spec['archive_sha'] or (base / '.git').exists():
        raise ValueError('archive identity or history boundary changed')
    expected = set()
    with tarfile.open(archive, 'r:gz') as stream:
        for member in stream:
            p = PurePosixPath(member.name)
            if (p.is_absolute() or '..' in p.parts or not p.parts or p.parts[0] != 'sympy-' + spec['rev']
                    or not (member.isfile() or member.isdir())):
                raise ValueError('unsafe source archive')
            if not member.isfile():
                continue
            path = base.joinpath(*p.parts[1:])
            if path.is_symlink() or not path.is_file():
                raise ValueError('clean source tree changed')
            item = stream.extractfile(member)
            if item is None:
                raise ValueError('archive member missing')
            with item:
                if hashlib.sha256(item.read()).hexdigest() != qual.sha(path):
                    raise ValueError('clean source content changed')
            expected.add(path.relative_to(base).as_posix())
    actual = {p.relative_to(base).as_posix() for p in base.rglob('*') if p.is_file()}
    if actual != expected or any(p.is_symlink() for p in base.rglob('*')):
        raise ValueError('clean source tree contains unexpected files')


def derive(task: str, condition: str = 'none', experience: Path | None = None) -> str:
    if task not in ('source', 'target') or condition not in ('none', 'source_history', 'generated_skill',
                                                            'feedback_first_history'):
        raise ValueError('unsupported task or experience condition')
    if (task == 'source' and condition != 'none') or ((condition == 'none') != (experience is None)):
        raise ValueError('inconsistent task/experience selection')
    case = ROOT / f'{task}__{condition}__seed{SEED}'
    src = qual.OUT / task
    code = BASE.read_text(encoding='utf-8')
    marker = '# A completely separate non-agent container mounts verifier after the episode;'
    if code.count(marker) != 1 or code.count("receipt={'task':task") != 1:
        raise ValueError('cannot isolate post-run verifier')
    code = code.split(marker, 1)[0] + "\nvrc=None\nreceipt={'task':task" + code.split("receipt={'task':task", 1)[1]
    source = (
        f"src=Path({str(src)!r})\n"
        "shutil.copytree(src/'clean_base',work,dirs_exist_ok=True)\n"
        "for dp,dirs,files in os.walk(work):\n"
        " os.chmod(dp,0o777)\n"
        " for fn in files:\n"
        "  p=Path(dp)/fn\n"
        "  if p.is_symlink():raise ValueError('unexpected source link')\n"
        "  os.chmod(p,0o777 if p.stat().st_mode & 0o111 else 0o666)\n"
    )
    edits = [
        ("ROOT=Path('/home/testuser/wzh/research_evidence/agent_skill_method_20261029')", f'ROOT=Path({str(ROOT)!r})', 1),
        ("if task not in ('llm-prefix-cache-replay','dialogue-parser','tictoc-unnecessary-abort-detection') or arm not in ('no_skill','all_skill','select_skill'): raise SystemExit('unsupported')",
         "if task not in ('source','target') or arm != 'no_skill': raise SystemExit('unsupported')", 1),
        ("case=ROOT/(task+'__'+arm+'__'+str(os.getpid()))", f'case=Path({str(case)!r})', 1),
        ('src=UP/task', source, 1),
        ("body=(src/'task.md').read_text(encoding='utf8').split('---',2)[2].strip()",
         "body=(src/'task.txt').read_text(encoding='utf8').strip()", 1),
        ('Generate the required output files.', 'Implement the requested repository change and relevant tests.', 1),
        ('Never read an entire large trace into the conversation; inspect only the first two lines using shell head, then write code that processes the complete unmodified file.',
         'Use the checked-out repository and local Python dependencies; network access is unavailable.', 1),
        ("len(calls)>=8", f"len(calls)>={MAX_HTTP_REQUESTS}", 1),
        ("sum(payload_bytes)+length>450000", f"sum(payload_bytes)+length>{MAX_BYTES}", 1),
        ("'timeout':120000", "'timeout':300000", 1),
        ("[],[],120)", "[],[],300)", 2),
        ("stderr=subprocess.PIPE,timeout=300)", f"stderr=subprocess.PIPE,timeout={MAX_SECONDS})", 1),
        ("'--cpus','1','--cap-drop'", "'--cpus','2','--cap-drop'", 1),
        ("'--memory','2g'", "'--memory','3g'", 1),
        ("sockpath.unlink(missing_ok=True)", "sockpath.unlink(missing_ok=True);bridge.rmdir()", 1),
        ("'python:3.12-slim'", repr(qual.IMAGE), 1),
        ('calls=[]; payload_bytes=[];', 'calls=[]; payload_bytes=[]; sampling=[];', 1),
        ('class Handler(socketserver.BaseRequestHandler):', CAPTURE + '\nclass Handler(socketserver.BaseRequestHandler):', 1),
        ("receipt={'task':task", "receipt={'sampling_metadata':sampling,'task':task", 1),
    ]
    for old, new, count in edits:
        code = replace_once(code, old, new, count)
    if experience:
        code = replace_once(code, "(work/'instructions.txt').write_text(body,encoding='utf8')",
                            "(work/'instructions.txt').write_text(body,encoding='utf8')\n"
                            "(work/'source_experience.md').touch(mode=0o444)")
        code = replace_once(code, 'Use available tools to implement and execute your solution.',
                            'Before solving, read /root/source_experience.md from an earlier related task. '
                            'Decide what applies and follow the current task. '
                            'Use available tools to implement and execute your solution.')
    mounts = (f"['--mount','type=bind,src={qual.DEPS},dst=/deps,readonly',"
              f"'--mount','type=bind,src={qual.OVERLAY / 'site'},dst=/extra,readonly',"
              f"'--mount','type=bind,src={ROOT / 'runtime'},dst=/runtime,readonly',"
              "'-e','PYTHONPATH=/runtime:/extra:/deps','-e','PYTHONDONTWRITEBYTECODE=1',"
              "'-e','PYTEST_DISABLE_PLUGIN_AUTOLOAD=1','-e','HYPOTHESIS_STORAGE_DIRECTORY=/tmp/hypothesis']")
    if experience:
        mounts += f"+['--mount','type=bind,src={experience},dst=/root/source_experience.md,readonly']"
    code = replace_once(code, 'server=Server(str(sockpath),Handler);',
                        f"_at=cmd.index({qual.IMAGE!r}); cmd[_at:_at]={mounts}; server=Server(str(sockpath),Handler);")
    old = "  if line.startswith(b'POST'):payload_bytes.append(length)"
    new = ("  if line.startswith(b'POST'):\n"
           "   payload_bytes.append(length)\n"
           f"   try:first,meta,forwarded=capture_sampling(first,length,self.request.recv,{TEMPERATURE},{SEED})\n"
           "   except (ValueError,EOFError,UnicodeDecodeError):\n"
           "    calls.append('DENIED:invalid_metadata');self.request.sendall("
           "b'HTTP/1.1 400 Bad Request\\r\\nContent-Length: 0\\r\\nConnection: close\\r\\n\\r\\n');return\n"
           "   payload_bytes[-1]=forwarded\n"
           f"   if sum(payload_bytes)>{MAX_BYTES}:\n"
           "    calls.append('DENIED:post_byte_cap_after_override');self.request.sendall("
           "b'HTTP/1.1 403 Forbidden\\r\\nContent-Length: 0\\r\\nConnection: close\\r\\n\\r\\n');return\n"
           "   sampling.append(meta)\n"
           "   with (case/'sampling_metadata.jsonl').open('a',encoding='utf-8') as log:\n"
           "    log.write(json.dumps(meta,separators=(',',':'))+'\\n');log.flush()")
    code = replace_once(code, old, new)
    code = replace_once(code, "(work/'opencode.json').write_text(json.dumps(cfg),encoding='utf8')",
                        f"cfg['agent']={{'build':{{'temperature':{TEMPERATURE},'seed':{SEED}}}}}\n"
                        "(work/'opencode.json').write_text(json.dumps(cfg),encoding='utf8')")
    compile(code, '<contextbench-derived-harness>', 'exec')
    return code


def preflight() -> None:
    if qual.sha(BASE) != BASE_SHA or qual.sha(qual.OUT / 'receipt.json') != QUAL_SHA:
        raise ValueError('base harness or controls changed')
    qual.checked_dataset()
    qual.checked_overlay()
    controls = json.loads((qual.OUT / 'receipt.json').read_text(encoding='utf-8'))
    ROOT.mkdir(parents=True, exist_ok=True)
    runtime = ROOT / 'runtime'
    runtime.mkdir(exist_ok=True)
    shim = runtime / 'sitecustomize.py'
    if shim.exists() and shim.read_text(encoding='utf-8') != SHIM:
        raise ValueError('runtime shim changed')
    if not shim.exists():
        shim.write_text(SHIM, encoding='utf-8')
    for task, spec in qual.CASES.items():
        row = controls['cases'][task]
        if (row['base_commit'] != spec['rev'] or row['arms']['base_with_tests']['focus']['exit'] != 1 or
                row['arms']['gold_with_tests']['focus']['exit'] != 0 or
                any(arm['regression']['exit'] != 0 for arm in row['arms'].values()) or
                qual.sha(qual.OUT / task / 'task.txt') != row['problem_sha256']):
            raise ValueError('control outcome or task identity mismatch')
        verify_clean_base(task)
        derive(task)
        cmd = ['docker', 'run', '--rm', '--pull', 'never', '--network', 'none', '--read-only',
               '--cap-drop', 'ALL', '--security-opt', 'no-new-privileges',
               '--mount', f'type=bind,src={qual.OUT / task / "clean_base"},dst=/workspace,readonly',
               '--mount', f'type=bind,src={qual.DEPS},dst=/deps,readonly',
               '--mount', f'type=bind,src={qual.OVERLAY / "site"},dst=/extra,readonly',
               '--mount', f'type=bind,src={runtime},dst=/runtime,readonly',
               '-e', 'PYTHONPATH=/runtime:/extra:/deps', '-e', 'PYTHONDONTWRITEBYTECODE=1',
               '--workdir', '/workspace', '--entrypoint', 'python3', qual.IMAGE,
               '-c', 'import distutils.version, pytest, sympy; print(pytest.__version__, sympy.__version__)']
        subprocess.run(cmd, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                       timeout=30, check=True)
    for condition in ('source_history', 'generated_skill', 'feedback_first_history'):
        derive('target', condition, Path('/tmp/preflight-source-experience.md'))
    ns = {'json': json}
    exec(CAPTURE, ns)
    body = json.dumps({'model': 'test', 'message': '数学'}).encode('utf-8')
    first = b'POST /v1/chat/completions HTTP/1.1\r\nContent-Length: ' + str(len(body)).encode() + b'\r\n\r\n' + body[:4]
    tail = [body[4:]]
    forwarded, meta, length = ns['capture_sampling'](first, len(body), lambda n: tail.pop(0), TEMPERATURE, SEED)
    if json.loads(forwarded.split(b'\r\n\r\n', 1)[1])['seed'] != SEED or meta['temperature'] != TEMPERATURE or length <= 0:
        raise ValueError('sampling proxy preflight failed')
    try:
        ns['capture_sampling'](first, len(body), lambda n: b'', TEMPERATURE, SEED)
    except EOFError:
        pass
    else:
        raise ValueError('short proxy request accepted')
    print(json.dumps({'status': 'PREFLIGHT_PASS', 'scientific_model_calls': 0, 'qualified_cases': list(qual.CASES)}))


def evaluate(task: str, case: Path) -> dict:
    """Use a post-run copy; never attach hidden tests to the agent workspace."""
    work = case / 'work'
    links = [p.relative_to(work).as_posix() for p in work.rglob('*') if p.is_symlink()]
    if links:
        return {'status': 'UNRESOLVED_SYMLINK', 'links': links[:20]}
    out = case / 'post_run_evaluation'
    out.mkdir()
    copy = out / 'candidate'
    shutil.copytree(work, copy, ignore=shutil.ignore_patterns('.git', '__pycache__', '.pytest_cache',
                                                            'instructions.txt', 'opencode.json'))
    spec = qual.CASES[task]
    rows = pq.read_table(qual.DATA / spec['data'], columns=['instance_id', 'test_patch']).to_pylist()
    row = next(item for item in rows if item['instance_id'] == spec['id'])
    controls = json.loads((qual.OUT / 'receipt.json').read_text(encoding='utf-8'))['cases'][task]
    if qual.sha_bytes(row['test_patch'].encode('utf-8')) != controls['test_patch_sha256']:
        raise ValueError('hidden test patch changed')
    patch = qual.apply_patch(copy, row['test_patch'])
    result = {'status': 'TEST_PATCH_CONFLICT' if patch['apply_exit'] != 0 else 'EVALUATED', 'test_patch': patch}
    if patch['apply_exit'] == 0:
        result['focus'] = qual.test(copy, spec['focus'], out / 'focus.log', task + '-agent-focus')
        result['regression'] = qual.test(copy, spec['regression'], out / 'regression.log', task + '-agent-regression')
    return result


def recheck_test_conflict(task: str, condition: str) -> None:
    """Post-hoc sensitivity: restore only benchmark-touched test files in a copy."""
    preflight()
    case = ROOT / f'{task}__{condition}__seed{SEED}'
    completed = ROOT / f'{task}__{condition}__seed{SEED}.completed.json'
    plan = json.loads(completed.read_text(encoding='utf-8'))
    if (plan.get('post_run_evaluation', {}).get('status') != 'TEST_PATCH_CONFLICT' or
            qual.sha(case / 'raw.jsonl') != plan.get('raw_sha256')):
        raise ValueError('no matching recorded test-patch conflict')
    work = case / 'work'
    if any(p.is_symlink() for p in work.rglob('*')):
        raise ValueError('candidate contains symbolic links')
    out = case / 'post_run_recheck_test_files_restored'
    if out.exists():
        raise FileExistsError('recheck already exists')
    out.mkdir()
    copy = out / 'candidate'
    shutil.copytree(work, copy, ignore=shutil.ignore_patterns('.git', '__pycache__', '.pytest_cache',
                                                            'instructions.txt', 'opencode.json'))
    spec = qual.CASES[task]
    rows = pq.read_table(qual.DATA / spec['data'], columns=['instance_id', 'test_patch']).to_pylist()
    row = next(item for item in rows if item['instance_id'] == spec['id'])
    frozen = json.loads((qual.OUT / 'receipt.json').read_text(encoding='utf-8'))['cases'][task]
    if qual.sha_bytes(row['test_patch'].encode('utf-8')) != frozen['test_patch_sha256']:
        raise ValueError('benchmark test patch changed')
    paths = sorted(set(re.findall(r'^\+\+\+ b/(.+)$', row['test_patch'], flags=re.MULTILINE)))
    if not paths:
        raise ValueError('no test paths in patch')
    restored = []
    for name in paths:
        relative = PurePosixPath(name)
        if relative.is_absolute() or '..' in relative.parts or 'tests' not in relative.parts:
            raise ValueError('test patch unexpectedly touches a non-test path')
        base, current = qual.OUT / task / 'clean_base' / name, copy / name
        if base.is_symlink() or current.is_symlink() or not base.is_file() or not current.is_file():
            raise ValueError('test file cannot be restored without an assumption')
        before = qual.sha(current)
        shutil.copyfile(base, current)
        restored.append({'path': name, 'candidate_sha256': before, 'restored_base_sha256': qual.sha(current),
                         'candidate_had_modified_file': before != qual.sha(current)})
    def non_test_hashes() -> dict:
        return {p.relative_to(copy).as_posix(): qual.sha(p) for p in copy.rglob('*')
                if p.is_file() and p.relative_to(copy).as_posix() not in paths}
    before = non_test_hashes()
    applied = qual.apply_patch(copy, row['test_patch'])
    result = {'scope': 'POST_HOC_TEST_FILE_RESTORATION_SENSITIVITY',
              'original_conflict_receipt_sha256': qual.sha(completed), 'raw_sha256': plan['raw_sha256'],
              'restored_test_files': restored, 'test_patch': applied}
    if applied['apply_exit'] == 0:
        result['focus'] = qual.test(copy, spec['focus'], out / 'focus.log', task + '-restored-focus')
        result['regression'] = qual.test(copy, spec['regression'], out / 'regression.log',
                                         task + '-restored-regression')
    result['other_files_unchanged'] = before == non_test_hashes()
    receipt = out / 'receipt.json'
    receipt.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'receipt': str(receipt), 'sha256': qual.sha(receipt), 'result': result}))


def legacy_evaluate(task: str, condition: str) -> None:
    """Re-evaluate a frozen candidate on the independently qualified Python 3.8 stack."""
    preflight()
    env = qual.ROOT / 'swe_contextbench_sympy_python38_env_20261104'
    controls_path, manifest_path = env / 'controls/receipt.json', env / 'controls/environment_manifest.json'
    if qual.sha(controls_path) != '1c6ebb9f156a60076a30ef3a17aa0373bd41ae58abfa6b4e510d8daf00dce9a6':
        raise ValueError('legacy controls changed')
    controls = json.loads(controls_path.read_text(encoding='utf-8'))
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    if (qual.sha(manifest_path) != controls['environment_manifest_sha256'] or
            not controls['environment_unchanged'] or
            qual.sha(Path('/home/testuser/miniconda3/envs/haiguan/bin/python')) != manifest['python_binary_sha256']):
        raise ValueError('legacy environment identity changed')
    site = env / 'site'
    actual = {p.relative_to(site).as_posix(): qual.sha(p) for p in sorted(site.rglob('*'))
              if p.is_file() and not p.is_symlink()}
    if (actual != manifest['site_files'] or
            {p.name: qual.sha(p) for p in sorted((env / 'wheelhouse').glob('*.whl'))} != manifest['wheels']):
        raise ValueError('legacy dependency overlay changed')
    expected = controls['cases'][task]
    if (expected['base_with_tests']['focus']['exit'] != 1 or expected['gold_with_tests']['focus']['exit'] != 0 or
            any(arm['regression']['exit'] != 0 for arm in expected.values())):
        raise ValueError('legacy controls do not qualify this task')
    case = ROOT / f'{task}__{condition}__seed{SEED}'
    completed = ROOT / f'{task}__{condition}__seed{SEED}.completed.json'
    plan = json.loads(completed.read_text(encoding='utf-8'))
    if qual.sha(case / 'raw.jsonl') != plan.get('raw_sha256'):
        raise ValueError('raw episode changed')
    if plan['post_run_evaluation']['status'] == 'EVALUATED':
        candidate = case / 'post_run_evaluation/candidate'
        scoring_source = 'ORIGINAL_POST_RUN_EVALUATION'
    elif plan['post_run_evaluation']['status'] == 'TEST_PATCH_CONFLICT':
        recheck = case / 'post_run_recheck_test_files_restored/receipt.json'
        check = json.loads(recheck.read_text(encoding='utf-8'))
        if not check['other_files_unchanged'] or check['test_patch']['apply_exit'] != 0:
            raise ValueError('test-restored sensitivity is not qualified')
        candidate = recheck.parent / 'candidate'
        scoring_source = 'POST_HOC_TEST_FILE_RESTORATION_SENSITIVITY'
    else:
        raise ValueError('agent candidate did not receive a test patch')
    spec = qual.CASES[task]
    row = qual.dataset_row(spec)
    paths = set(re.findall(r'^\+\+\+ b/(.+)$', row['test_patch'], flags=re.MULTILINE))
    if not paths or any('tests' not in PurePosixPath(p).parts or '..' in PurePosixPath(p).parts for p in paths):
        raise ValueError('unexpected test patch paths')
    def code_files(root: Path) -> dict:
        result = {}
        for p in root.rglob('*'):
            if p.is_symlink():
                raise ValueError('candidate contains symbolic links')
            relative = p.relative_to(root).as_posix()
            if (p.is_file() and relative not in paths and p.name not in ('instructions.txt', 'opencode.json')
                    and not any(part in ('.git', '__pycache__', '.pytest_cache') for part in p.parts)):
                result[relative] = qual.sha(p)
        return result
    before = code_files(candidate)
    if before != code_files(case / 'work'):
        raise ValueError('evaluator copy differs from agent non-test artifacts')
    check = subprocess.run(['git', 'apply', '--reverse', '--check', '-'], cwd=candidate,
                           input=row['test_patch'].encode('utf-8'), stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT, timeout=30)
    if check.returncode:
        raise ValueError('expected test patch not present in evaluator copy')
    out = case / 'post_run_python38_evaluation'
    if out.exists():
        raise FileExistsError('legacy evaluation already exists')
    out.mkdir()
    reg = json.loads(row['PASS_TO_PASS']) if task == 'target' else spec['regression']
    result = {'scope': 'POST_HOC_CROSS_ENVIRONMENT_AGENT_EVALUATION', 'scoring_source': scoring_source,
              'original_receipt_sha256': qual.sha(completed), 'legacy_controls_sha256': qual.sha(controls_path),
              'agent_environment': 'Python 3.12; evaluator is Python 3.8', 'agent_or_model_calls': 0,
              'focus': qual.test_legacy(candidate, spec['focus'], out / 'focus.log', task + '-candidate-focus'),
              'regression': qual.test_legacy(candidate, reg, out / 'regression.log', task + '-candidate-regression')}
    result['candidate_other_files_unchanged'] = before == code_files(candidate)
    receipt = out / 'receipt.json'
    receipt.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'receipt': str(receipt), 'sha256': qual.sha(receipt), 'result': result}))


def experience_file(condition: str) -> Path:
    directory = ROOT / 'source_experience'
    meta = json.loads((directory / 'metadata.json').read_text(encoding='utf-8'))
    name = {'source_history': 'source_history.md', 'generated_skill': 'generated_skill.md',
            'feedback_first_history': 'feedback_first_history.md'}[condition]
    path = directory / name
    key = {'source_history': 'history_sha256', 'generated_skill': 'skill_sha256',
           'feedback_first_history': 'feedback_first_history_sha256'}[condition]
    if qual.sha(path) != meta.get(key):
        raise ValueError('source experience changed or not generated')
    return path


def build_experience() -> None:
    """Create a clipped source-only history, preserving source failure feedback."""
    preflight()
    case = ROOT / f'source__none__seed{SEED}'
    completed = ROOT / f'source__none__seed{SEED}.completed.json'
    plan = json.loads(completed.read_text(encoding='utf-8'))
    raw = case / 'raw.jsonl'
    feedback_path = case / 'post_run_recheck_test_files_restored/receipt.json'
    feedback = json.loads(feedback_path.read_text(encoding='utf-8'))
    if (qual.sha(raw) != plan['raw_sha256'] or not feedback['other_files_unchanged'] or
            feedback['original_conflict_receipt_sha256'] != qual.sha(completed)):
        raise ValueError('source episode or feedback changed')
    actions = []
    for line in raw.read_text(encoding='utf-8').splitlines():
        event = json.loads(line)
        if event.get('type') != 'tool_use':
            continue
        part, state = event.get('part', {}), event.get('part', {}).get('state', {})
        input_text = json.dumps(state.get('input', {}), ensure_ascii=False, separators=(',', ':'))
        output_text = str(state.get('output', ''))
        actions.append({'tool': part.get('tool'), 'status': state.get('status'),
                        'input_prefix': input_text[:600], 'input_chars': len(input_text),
                        'input_sha256': qual.sha_bytes(input_text.encode('utf-8')),
                        'output_tail': output_text[-800:], 'output_chars': len(output_text),
                        'output_sha256': qual.sha_bytes(output_text.encode('utf-8'))})
    if not actions:
        raise ValueError('source episode has no recorded actions')
    source_code = 'sympy/functions/elementary/complexes.py'
    old = (qual.OUT / 'source/clean_base' / source_code).read_text(encoding='utf-8').splitlines(True)
    new = (case / 'work' / source_code).read_text(encoding='utf-8').splitlines(True)
    diff = ''.join(difflib.unified_diff(old, new, fromfile='source-base/' + source_code,
                                       tofile='source-agent/' + source_code))
    focus_log = (feedback_path.parent / 'focus.log').read_text(encoding='utf-8', errors='replace')
    content = {'source_task': (qual.OUT / 'source/task.txt').read_text(encoding='utf-8'),
               'source_actions': actions, 'source_code_diff_prefix': diff[:10000],
               'source_code_diff_chars': len(diff),
               'source_feedback': {'agent_exit': plan['agent_exit'], 'request_limit_reached': bool(plan['denied']),
                                   'focus_exit': feedback['focus']['exit'],
                                   'regression_exit': feedback['regression']['exit'],
                                   'focus_log_tail': focus_log[-2000:]},
               'scope': 'all recorded source tool actions; each input prefix and output tail clipped; '
                        'code diff capped; source-only post-run feedback; no target issue or tests'}
    encoded = json.dumps(content, ensure_ascii=False, separators=(',', ':'))
    if '19484' in encoded or 'cannot simplify sign(x) * abs(x)' in encoded.lower():
        raise ValueError('source history contains a literal target marker')
    pieces = [encoded[i:i + 700] for i in range(0, len(encoded), 700)]
    readable = ('Source-only task history. The current task may differ. Concatenate text after | '
                'on numbered lines to reconstruct the JSON.\n' +
                ''.join(f'{i:04d}|{piece}\n' for i, piece in enumerate(pieces)))
    if ''.join(line.split('|', 1)[1] for line in readable.splitlines()[1:]) != encoded:
        raise ValueError('history wrapping changed content')
    out = ROOT / 'source_experience'
    out.mkdir(exist_ok=False)
    history = out / 'source_history.md'
    history.write_text(readable, encoding='utf-8')
    meta = {'source_raw_sha256': qual.sha(raw), 'source_completion_sha256': qual.sha(completed),
            'source_feedback_sha256': qual.sha(feedback_path), 'history_sha256': qual.sha(history),
            'actions': len(actions), 'history_chars': len(readable), 'source_diff_chars': len(diff),
            'clipped_inputs': sum(x['input_chars'] > 600 for x in actions),
            'clipped_outputs': sum(x['output_chars'] > 800 for x in actions),
            'target_marker_screen': 'NO_LITERAL_MATCH; semantic or model pretraining leakage remains unknown',
            'scope': content['scope']}
    (out / 'metadata.json').write_text(json.dumps(meta, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'history': str(history), 'metadata': meta}, ensure_ascii=False))


def generate_skill() -> None:
    """Use only the frozen source history; persist attempt and usage separately."""
    preflight()
    history = experience_file('source_history')
    directory = history.parent
    meta_path = directory / 'metadata.json'
    metadata = json.loads(meta_path.read_text(encoding='utf-8'))
    ledger, request_path, skill = (directory / name for name in
                                   ('skill_generation_ledger.json', 'skill_generation_request.json', 'generated_skill.md'))
    if any(path.exists() for path in (ledger, request_path, skill)):
        raise FileExistsError('skill generation already attempted')
    payload = {'model': 'Qwen3.6-35B-A3B-Q4_K_M.gguf', 'temperature': TEMPERATURE, 'seed': SEED,
               'max_tokens': 2500, 'chat_template_kwargs': {'enable_thinking': False},
               'messages': [{'role': 'system', 'content': 'Create concise reusable instructions from a past '
                             'tool-using agent episode and its feedback. Separate general steps from task-specific '
                             'choices; include observed failures and unresolved assumptions. Do not invent results '
                             'or copy the old answer as a future answer. Return only the skill text.'},
                            {'role': 'user', 'content': history.read_text(encoding='utf-8')}]}
    request = json.dumps(payload, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
    request_path.write_bytes(request)
    accounting = {'status': 'ATTEMPT_STARTED', 'http_attempts': 1, 'usage': None,
                  'request_sha256': qual.sha(request_path), 'source_history_sha256': qual.sha(history)}
    ledger.write_text(json.dumps(accounting, indent=2) + '\n', encoding='utf-8')
    started = time.monotonic()
    try:
        req = urllib.request.Request('http://127.0.0.1:8004/v1/chat/completions', data=request,
                                     headers={'Content-Type': 'application/json'}, method='POST')
        with urllib.request.urlopen(req, timeout=300) as response:
            raw = response.read()
        response_path = directory / 'skill_generation_response.json'
        response_path.write_bytes(raw)
        parsed = json.loads(raw)
        text = parsed['choices'][0]['message']['content']
        if not isinstance(text, str) or not text.strip():
            raise ValueError('empty generated skill')
        skill.write_text(text.strip() + '\n', encoding='utf-8')
        accounting.update({'status': 'RECEIVED', 'response_sha256': qual.sha(response_path),
                           'skill_sha256': qual.sha(skill), 'usage': parsed.get('usage')})
        metadata['skill_sha256'] = qual.sha(skill)
        meta_path.write_text(json.dumps(metadata, indent=2) + '\n', encoding='utf-8')
    except Exception as exc:
        accounting.update({'status': 'FAILED_UNKNOWN_USAGE', 'error_type': type(exc).__name__})
        raise
    finally:
        accounting['seconds'] = round(time.monotonic() - started, 3)
        ledger.write_text(json.dumps(accounting, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(accounting, ensure_ascii=False))


@recorded_episode(ROOT, SEED)
def run(task: str, condition: str) -> None:
    preflight()
    runtime = ROOT / 'runtime'
    shim = runtime / 'sitecustomize.py'
    experience = None if condition == 'none' else experience_file(condition)
    case = ROOT / f'{task}__{condition}__seed{SEED}'
    started = ROOT / f'{task}__{condition}__seed{SEED}.started.json'
    complete = ROOT / f'{task}__{condition}__seed{SEED}.completed.json'
    if case.exists() or started.exists() or complete.exists():
        raise FileExistsError('task already attempted; inspect receipts before retry')
    code = derive(task, condition, experience)
    harness = ROOT / f'{task}__{condition}__seed{SEED}.harness.py'
    harness.write_text(code, encoding='utf-8')
    plan = {'task': task, 'condition': condition, 'seed': SEED, 'temperature': TEMPERATURE,
            'base_sha256': BASE_SHA, 'qualification_sha256': QUAL_SHA, 'harness_sha256': qual.sha(harness),
            'shim_sha256': qual.sha(shim), 'max_http_requests': MAX_HTTP_REQUESTS, 'max_bytes': MAX_BYTES,
            'max_seconds': MAX_SECONDS, 'experience_sha256': qual.sha(experience) if experience else None,
            'status': 'STARTED'}
    started.write_text(json.dumps(plan, indent=2) + '\n', encoding='utf-8')
    proc = subprocess.run([sys.executable, str(harness), task, 'no_skill'], stdin=subprocess.DEVNULL,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=MAX_SECONDS + 120)
    (ROOT / f'{task}__{condition}__seed{SEED}.runner.stdout').write_bytes(proc.stdout)
    (ROOT / f'{task}__{condition}__seed{SEED}.runner.stderr').write_bytes(proc.stderr)
    plan.update({'runner_exit': proc.returncode, 'started_sha256': qual.sha(started)})
    if proc.returncode == 0 and (case / 'receipt.json').is_file():
        receipt = json.loads((case / 'receipt.json').read_text(encoding='utf-8'))
        log = case / 'sampling_metadata.jsonl'
        metadata = [json.loads(line) for line in log.read_text(encoding='utf-8').splitlines()] if log.is_file() else []
        same = Counter(json.dumps(x, sort_keys=True) for x in metadata) == Counter(
            json.dumps(x, sort_keys=True) for x in receipt['sampling_metadata'])
        if not same or qual.sha(case / 'raw.jsonl') != receipt['raw_sha256']:
            raise ValueError('model receipt or sampling log mismatch')
        read_info = None
        if experience:
            if qual.sha(experience) != plan['experience_sha256']:
                raise ValueError('source experience changed during episode')
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
                                raise ValueError('inconsistent experience read')
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
                         x['seed'] == SEED and x['temperature'] == TEMPERATURE for x in metadata),
                     'raw_sha256': receipt['raw_sha256'], 'experience_read': read_info,
                     'post_run_evaluation': evaluate(task, case)})
    else:
        plan['status'] = 'RUNNER_ERROR_REVIEW_RAW_AND_PROXY_LOG'
    complete.write_text(json.dumps(plan, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'receipt': str(complete), 'sha256': qual.sha(complete), 'result': plan}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--preflight', action='store_true')
    parser.add_argument('--recheck-test-conflict', action='store_true')
    parser.add_argument('--legacy-evaluate', action='store_true')
    parser.add_argument('--build-experience', action='store_true')
    parser.add_argument('--generate-skill', action='store_true')
    parser.add_argument('--task', choices=('source', 'target'))
    parser.add_argument('--condition', choices=('none', 'source_history', 'generated_skill',
                                                 'feedback_first_history'), default='none')
    args = parser.parse_args()
    if args.preflight:
        preflight()
    elif args.build_experience:
        build_experience()
    elif args.generate_skill:
        generate_skill()
    elif args.recheck_test_conflict and args.task:
        recheck_test_conflict(args.task, args.condition)
    elif args.legacy_evaluate and args.task:
        legacy_evaluate(args.task, args.condition)
    elif args.task:
        run(args.task, args.condition)
    else:
        parser.error('choose --preflight or --task')
