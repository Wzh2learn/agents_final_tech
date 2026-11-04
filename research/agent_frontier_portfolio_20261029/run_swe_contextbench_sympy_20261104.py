#!/usr/bin/env python3
"""Run isolated OpenCode/Qwen on two qualified historical SymPy issues.

The runtime sees only the selected issue and its base checkout. Hidden tests are
applied to a separate evaluator copy after the agent exits. No published
historical trajectory, reference patch, host Git history, or network is mounted.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import sys
import tarfile

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


def derive(task: str) -> str:
    case = ROOT / f'{task}__none__seed{SEED}'
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
    mounts = (f"['--mount','type=bind,src={qual.DEPS},dst=/deps,readonly',"
              f"'--mount','type=bind,src={qual.OVERLAY / 'site'},dst=/extra,readonly',"
              f"'--mount','type=bind,src={ROOT / 'runtime'},dst=/runtime,readonly',"
              "'-e','PYTHONPATH=/runtime:/extra:/deps','-e','PYTHONDONTWRITEBYTECODE=1',"
              "'-e','PYTEST_DISABLE_PLUGIN_AUTOLOAD=1','-e','HYPOTHESIS_STORAGE_DIRECTORY=/tmp/hypothesis']")
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


def run(task: str) -> None:
    preflight()
    runtime = ROOT / 'runtime'
    shim = runtime / 'sitecustomize.py'
    case = ROOT / f'{task}__none__seed{SEED}'
    started = ROOT / f'{task}__none__seed{SEED}.started.json'
    complete = ROOT / f'{task}__none__seed{SEED}.completed.json'
    if case.exists() or started.exists() or complete.exists():
        raise FileExistsError('task already attempted; inspect receipts before retry')
    code = derive(task)
    harness = ROOT / f'{task}__none__seed{SEED}.harness.py'
    harness.write_text(code, encoding='utf-8')
    plan = {'task': task, 'condition': 'none', 'seed': SEED, 'temperature': TEMPERATURE,
            'base_sha256': BASE_SHA, 'qualification_sha256': QUAL_SHA, 'harness_sha256': qual.sha(harness),
            'shim_sha256': qual.sha(shim), 'max_http_requests': MAX_HTTP_REQUESTS, 'max_bytes': MAX_BYTES,
            'max_seconds': MAX_SECONDS, 'status': 'STARTED'}
    started.write_text(json.dumps(plan, indent=2) + '\n', encoding='utf-8')
    proc = subprocess.run([sys.executable, str(harness), task, 'no_skill'], stdin=subprocess.DEVNULL,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=MAX_SECONDS + 120)
    (ROOT / f'{task}__none__seed{SEED}.runner.stdout').write_bytes(proc.stdout)
    (ROOT / f'{task}__none__seed{SEED}.runner.stderr').write_bytes(proc.stderr)
    plan.update({'runner_exit': proc.returncode, 'started_sha256': qual.sha(started)})
    if proc.returncode == 0 and (case / 'receipt.json').is_file():
        receipt = json.loads((case / 'receipt.json').read_text(encoding='utf-8'))
        log = case / 'sampling_metadata.jsonl'
        metadata = [json.loads(line) for line in log.read_text(encoding='utf-8').splitlines()] if log.is_file() else []
        same = Counter(json.dumps(x, sort_keys=True) for x in metadata) == Counter(
            json.dumps(x, sort_keys=True) for x in receipt['sampling_metadata'])
        if not same or qual.sha(case / 'raw.jsonl') != receipt['raw_sha256']:
            raise ValueError('model receipt or sampling log mismatch')
        plan.update({'status': 'COMPLETED', 'agent_exit': receipt['agent_exit'],
                     'posts': sum(x.startswith('POST ') for x in receipt['model_http_requests']),
                     'denied': [x for x in receipt['model_http_requests'] if x.startswith('DENIED')],
                     'reported_tokens': sum(x.get('total', 0) for x in receipt['step_finish_tokens']),
                     'cache_read_included': sum(x.get('cache', {}).get('read', 0)
                                                for x in receipt['step_finish_tokens']),
                     'seed_and_temperature_forwarded': bool(metadata) and all(
                         x['seed'] == SEED and x['temperature'] == TEMPERATURE for x in metadata),
                     'raw_sha256': receipt['raw_sha256'], 'post_run_evaluation': evaluate(task, case)})
    else:
        plan['status'] = 'RUNNER_ERROR_REVIEW_RAW_AND_PROXY_LOG'
    complete.write_text(json.dumps(plan, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'receipt': str(complete), 'sha256': qual.sha(complete), 'result': plan}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--preflight', action='store_true')
    parser.add_argument('--task', choices=('source', 'target'))
    args = parser.parse_args()
    if args.preflight:
        preflight()
    elif args.task:
        run(args.task)
    else:
        parser.error('choose --preflight or --task')
