#!/usr/bin/env python3
"""Collect one frozen, source-only ContextBench episode; prepare is CPU-only."""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import difflib
import hashlib
import importlib
import json
import os
from pathlib import Path
import re
import shutil
import signal
import socket
import socketserver
import subprocess
import sys
import tempfile
import threading
import time
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
PRIVATE = Path('/home/testuser/wzh/research_evidence/agent_learning_20261030')
LOCK = PRIVATE / 'alfworld_text_qualification_20261106/context_study_v1/model_resource.lock'
REGISTRY_SHA = 'de086acea81dcfae7bdc6e3276a05e7c8ff02e0c6ce38a989bb9f1560a39838f'
RESULT_SHA = '576dec0cc19d342d50c8ebfd65b90dde8c123ba7e1fd199545dde209ad638ab2'
PROFILE_SHA = '9cbb51bb6dc64583cb376f81e8f8c1c28400cb494fce2793f1fa2ce60e39a279'
CAPS = dict(posts=48, seconds=1200, combined_wire_bytes=64 * 1024**2)
SOURCES = {
    'django__django-12453': ('django/django', 'b330b918e979ea39a21d47b61172d112caf432c3', 'django__django-31051', 5,
        'd4e3a8f860acf71c69b63bbe2b553599807d1bf25ab0ae3c79c7b236bc6efd87'),
    'sympy__sympy-21055': ('sympy/sympy', '748ce73479ee2cd5c861431091001cc18943c735', 'sympy__sympy-9384', 13,
        '3637be1d94932dfff7ad9af88c2d5a6ebef42a51a6464e2f56717abd04cda703'),
}

# Explicit code-task guest. No generated runner, inherited world tool or host shell.
GUEST = r'''import json,os,pathlib,select,socket,subprocess,sys,threading
assert sys.version_info[:2]==(3,8) and os.getuid()==int(sys.argv[2]) and os.getuid()!=0
assert os.environ['HOME']=='/home/agent' and os.access('/workspace',os.W_OK)
assert not pathlib.Path('/home/testuser/wzh/research_evidence').exists()
def proxy(client):
 upstream=socket.socket(socket.AF_UNIX)
 try:
  upstream.connect('/model/s')
  while True:
   ready,_,_=select.select([client,upstream],[],[],1200)
   if not ready:return
   for stream in ready:
    data=stream.recv(65536)
    if not data:return
    (upstream if stream is client else client).sendall(data)
 finally:client.close();upstream.close()
listener=socket.socket();listener.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
listener.bind(('127.0.0.1',18004));listener.listen(8)
def serve():
 while True:
  client,_=listener.accept();threading.Thread(target=proxy,args=(client,),daemon=True).start()
threading.Thread(target=serve,daemon=True).start()
prompt=pathlib.Path('/inputs/task.txt').read_bytes().decode('utf8')
result=subprocess.run(['/opt/opencode','run','--pure','--format','json','-m',sys.argv[1],
 '--title','contextbench-source',prompt],stdin=subprocess.DEVNULL)
raise SystemExit(result.returncode)
'''


def helpers():
    for path in (HERE, REPO):
        if str(path) not in sys.path: sys.path.insert(0, str(path))
    h = SimpleNamespace(actor=importlib.import_module('run_alfworld_actor_20261106'),
        agg=importlib.import_module('run_django_aggregation_agent_20261106'),
        pool=importlib.import_module('qualify_contextbench_pool'),
        deps=importlib.import_module('scripts.graph.research_actor_dependencies'),
        teacher=importlib.import_module('scripts.graph.research_teacher_backend'),
        tools=importlib.import_module('scripts.graph.research_tool_runtime'))
    h.pool.helpers()  # Freeze scorer dependencies before preparing either mode.
    return h


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda: f.read(1024**2), b''): digest.update(chunk)
    return digest.hexdigest()


def safe(path):
    path = Path(path)
    if not path.is_absolute() or path != path.resolve() or any(c in str(path) for c in ',\r\n'):
        raise ValueError('unsafe absolute path')
    for p in (path, *path.parents):
        if p.is_symlink() or (p.is_file() and p.stat().st_nlink != 1): raise ValueError('linked input')
    return path


def tree(path):
    path = safe(path)
    if not path.is_dir(): raise ValueError('missing tree')
    result = {}
    for p in sorted(path.rglob('*')):
        safe(p)
        if '.git' in p.relative_to(path).parts: raise ValueError('Git history exposed')
        if p.is_file(): result[p.relative_to(path).as_posix()] = sha(p)
        elif not p.is_dir(): raise ValueError('special input')
    return result


def read_ref(ref):
    if set(ref) != {'path', 'sha256'} or not re.fullmatch('[0-9a-f]{64}', ref['sha256']):
        raise ValueError('invalid reference')
    p = safe(ref['path'])
    if sha(p) != ref['sha256']: raise ValueError('input hash changed')
    return json.loads(p.read_text())


def new(path, value):
    with Path(path).open('x') as f: json.dump(value, f, indent=2); f.write('\n')


def components():
    paths = {Path(__file__).resolve()}
    for module in list(sys.modules.values()):
        name = getattr(module, '__file__', None)
        if name:
            p = Path(name).resolve()
            if p.suffix == '.py' and (p.is_relative_to(HERE) or p.is_relative_to(REPO / 'scripts/graph')):
                paths.add(p)
    return {str(p): sha(safe(p)) for p in sorted(paths)}


def profile_input(path, digest, h):
    if digest != PROFILE_SHA: raise ValueError('unapproved profile')
    profile = read_ref(dict(path=str(path), sha256=digest))
    h.teacher._vllm_profile_fields(profile)  # Fields only: no weights, container or endpoint in prepare.
    if (profile['context'], profile['output'], profile['model_id']) != (32768, 8192, 'qwen38-27b-fp8'):
        raise ValueError('wrong model limits')
    return profile


def projection_input(path, digest, source, h):
    repo, _, _, _, expected = SOURCES[source]
    if digest != expected: raise ValueError('unapproved dependency projection')
    actor = h.deps.verify_projection(safe(path), digest)
    manifest = read_ref(dict(path=str(Path(path) / 'manifest.json'), sha256=digest))
    kind = repo.split('/')[0]
    site = PRIVATE / ('swe_contextbench_django_env_20261104' if kind == 'django' else 'swe_contextbench_sympy_python38_env_20261104') / 'site'
    if (manifest['python'], manifest['blocked_packages'], manifest['source_site_paths']) != ('3.8', [kind], {'default': str(site)}):
        raise ValueError('projection differs from qualified dependency source')
    if set(actor['sites']) != {'default'}: raise ValueError('extra dependency surface')
    tree(Path(path))
    return actor


def source_input(registry, digest, source):
    if source not in SOURCES or digest != REGISTRY_SHA: raise ValueError('unapproved source/registry')
    reg = read_ref(dict(path=str(registry), sha256=digest))
    if reg['schema'] != 'qualified_source_target_pairs_v1' or reg['source_result']['sha256'] != RESULT_SHA:
        raise ValueError('wrong source qualification')
    result = read_ref(reg['source_result'])
    if result['status'] != 'QUALIFIED' or result['model_calls'] != 0 or set(result['cases']) != set(SOURCES):
        raise ValueError('incomplete source qualification')
    rows = [r for r in reg['rows'] if r['source'] == source]
    if len(rows) != 1: raise ValueError('duplicate/missing source')
    row = rows[0]; case = result['cases'][source]; spec = case['spec']; repo, base, target, ptp, _ = SOURCES[source]
    if (spec['instance_id'], spec['repo'], spec['base_commit'], spec['role'], spec['related_target_id'], row['target']) != (source, repo, base, 'source', target, target):
        raise ValueError('source identity differs')
    if case['qualification']['qualified'] is not True or set(case['labels']) != {'f2p', 'ptp'} or (len(case['labels']['f2p']), len(case['labels']['ptp'])) != (1, ptp):
        raise ValueError('source controls/labels incomplete')
    clean = safe(row['clean_base']); parent = safe(reg['source_result']['path']).parent / source
    if clean != parent / 'clean_base' or tree(clean) != case['clean_base_sha256']:
        raise ValueError('source clean tree differs from qualification')
    for name in ('task.txt', 'test.patch'):
        if sha(safe(parent / name)) != case['input_sha256'][name]: raise ValueError('source task/tests changed')
    text = (parent / 'task.txt').read_text()
    number = target.rsplit('-', 1)[1]
    if any(m in text for m in (target, '/pull/' + number, '/issues/' + number, '#' + number)):
        raise ValueError('target identity in source task')
    return reg, case, parent



def scoring_dependencies(registry, h):
    result = read_ref(registry['source_result'])
    contracts = [(p, digest) for p, digest in result['input_sha256'].items() if Path(p).name == 'SOURCE_CONTRACT_V1.json']
    if len(contracts) != 1: raise ValueError('qualified source contract missing')
    contract = read_ref(dict(path=contracts[0][0], sha256=contracts[0][1])); bindings = {}
    limits = {kind: h.pool.dependencies(kind, contract['runtime'][kind + '_dependency_manifest'], bindings) for kind in ('django', 'sympy')}
    if contract['runtime']['image'] != h.pool.IMAGE: raise ValueError('scorer image differs from qualification')
    return dict(bindings=bindings, limits=limits)


def prepare(registry, registry_sha, source, root, projection, projection_sha, profile, profile_sha):
    h = helpers(); reg, case, parent = source_input(registry, registry_sha, source)
    scorer = scoring_dependencies(reg, h)
    p = profile_input(profile, profile_sha, h); actor = projection_input(projection, projection_sha, source, h)
    root = safe(root)
    if PRIVATE not in root.parents or root.exists() or any(root == x or root in x.parents or x in root.parents for x in (parent, Path(projection))):
        raise ValueError('fresh disjoint private root required')
    h.tools.ripgrep_binding(); binaries = {str(safe(h.tools.OPENCODE)): sha(h.tools.OPENCODE), str(safe(h.tools.RG)): sha(h.tools.RG)}
    root.mkdir(mode=0o700, parents=True)
    shutil.copytree(parent / 'clean_base', root / 'baseline')
    shutil.copytree(root / 'baseline', root / 'work')
    for f in (root / 'work').rglob('*'):
        if f.is_file(): f.chmod(f.stat().st_mode | 0o200)
    inputs = root / 'inputs'; inputs.mkdir(); (root / 'scoring').mkdir()
    shutil.copyfile(parent / 'task.txt', inputs / 'source_task.txt')
    public = (inputs / 'source_task.txt').read_bytes().decode('utf8')
    (inputs / 'task.txt').write_text('Implement the requested source change in /workspace and run relevant tests. Python 3.8 and dependencies are offline. Do not ask for permission to continue. The task below is reproduced verbatim.\n\n' + public)
    shutil.copyfile(parent / 'test.patch', root / 'scoring/test.patch')
    (inputs / 'guest.py').write_text(GUEST)
    new(inputs / 'opencode.json', h.actor.config(p, 17))
    manifest = dict(schema='contextbench_source_v1', root=str(root), source=source,
        registry=dict(path=str(registry), sha256=registry_sha), source_result=reg['source_result'],
        repo=case['spec']['repo'], base=case['spec']['base_commit'], labels=case['labels'],
        scorer_dependencies=scorer, projection=dict(path=str(projection), sha256=projection_sha), profile=dict(path=str(profile), sha256=profile_sha),
        baseline=tree(root / 'baseline'), work=tree(root / 'work'), inputs=tree(inputs),
        public_task_sha256=sha(inputs / 'source_task.txt'), wrapped_prompt_sha256=sha(inputs / 'task.txt'),
        test_patch_sha256=sha(root / 'scoring/test.patch'), components=components(), binaries=binaries,
        caps=CAPS, sampling=dict(seed=17, temperature=0.2, native_thinking=False, context=32768, output=8192),
        boundary='source clean/task only; scorer/test_patch/registry/targets/gold never actor mounts',
        dependency_limit='qualification used legacy conda libraries not wholly frozen; actor projection bytes frozen separately',
        status='CPU_PREPARED', models_called=0, container_runs=0)
    new(root / 'manifest.json', manifest)
    return dict(status='CPU_PREPARED', root=str(root), manifest_sha256=sha(root / 'manifest.json'))


def verify(root, digest, *, initial=True):
    root = safe(root); m = read_ref(dict(path=str(root / 'manifest.json'), sha256=digest)); h = helpers()
    if m['schema'] != 'contextbench_source_v1' or m['root'] != str(root) or m['caps'] != CAPS or m['sampling'] != dict(seed=17, temperature=0.2, native_thinking=False, context=32768, output=8192):
        raise ValueError('manifest policy differs')
    reg, case, _ = source_input(m['registry']['path'], m['registry']['sha256'], m['source'])
    if m['source_result'] != reg['source_result'] or (m['repo'], m['base'], m['labels']) != (case['spec']['repo'], case['spec']['base_commit'], case['labels']):
        raise ValueError('manifest source differs')
    if scoring_dependencies(reg, h) != m['scorer_dependencies']: raise ValueError('scorer dependencies changed')
    actor = projection_input(m['projection']['path'], m['projection']['sha256'], m['source'], h)
    p = profile_input(m['profile']['path'], m['profile']['sha256'], h)
    for name in (('baseline', 'work', 'inputs') if initial else ('baseline', 'inputs')):
        if tree(root / name) != m[name]: raise ValueError('prepared ' + name + ' changed')
    if (sha(safe(root / 'scoring/test.patch')) != m['test_patch_sha256'] or m['test_patch_sha256'] != case['input_sha256']['test.patch']
            or m['public_task_sha256'] != case['input_sha256']['task.txt'] or sha(root / 'inputs/source_task.txt') != m['public_task_sha256']
            or sha(root / 'inputs/task.txt') != m['wrapped_prompt_sha256'] or m['work'] != m['baseline'] or m['baseline'] != case['clean_base_sha256']):
        raise ValueError('prepared baseline/tests differ')
    if components() != m['components'] or any(sha(safe(path)) != digest for path, digest in m['binaries'].items()):
        raise ValueError('loaded source/tool changed')
    return m, h, actor, p


@contextmanager
def resource_lock():
    import fcntl
    path = safe(LOCK); before = path.stat()
    with path.open('r+') as f:
        if (before.st_dev, before.st_ino) != (os.fstat(f.fileno()).st_dev, os.fstat(f.fileno()).st_ino): raise ValueError('resource lock replaced')
        fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if (path.stat().st_dev, path.stat().st_ino) != (before.st_dev, before.st_ino): raise ValueError('resource lock path replaced')
        try: yield
        finally: fcntl.flock(f, fcntl.LOCK_UN)


class Relay:
    """One real HTTP POST per connection; engineering tests use fake socket pairs."""
    def __init__(self, root, profile, h, *, deadline, caps=None):
        self.root, self.profile, self.h, self.deadline = Path(root), profile, h, deadline
        self.caps = CAPS if caps is None else caps
        self.lock = threading.RLock(); self.posts = self.inflight = self.unknown = self.used = self.response_bytes = 0
        self.attempts = 0; self.failures = []; self.active = set()
        (self.root / 'wire').mkdir()

    def event(self, index, kind, **extra):
        with self.lock:
            with (self.root / 'forward_ledger.jsonl').open('a') as f:
                f.write(json.dumps(dict(request=index, event=kind, monotonic_seconds=time.monotonic(), **extra)) + '\n'); f.flush()

    def handle(self, client):
        upstream = None; reserved = sent = sending = False; size = 0
        with self.lock: self.attempts += 1; index = self.attempts; self.active.add(client)
        self.event(index, 'attempt')
        try:
            client.settimeout(max(0.001, self.deadline - time.monotonic()))
            value = self.h.actor.receive_http(client, self.caps['combined_wire_bytes'])
            if not isinstance(value, dict): raise ValueError('model payload must be an object')
            value = self.h.actor.model_payload(value, 'teacher27b', self.profile, 17)
            value.pop('max_completion_tokens', None)
            body = json.dumps(value, ensure_ascii=False, allow_nan=False, separators=(',', ':')).encode()
            size = len(body); path = self.root / 'wire' / f'{index:05d}.request.json'; path.write_bytes(body)
            with self.lock:
                if time.monotonic() >= self.deadline: raise TimeoutError('episode deadline')
                if self.posts + self.inflight + self.unknown >= self.caps['posts'] or self.used + size > self.caps['combined_wire_bytes']:
                    self.event(index, 'refused', reason='HARD_CAP'); client.sendall(b'HTTP/1.1 403 Forbidden\r\nContent-Length: 0\r\nConnection: close\r\n\r\n'); return
                self.inflight += 1; self.used += size; reserved = True
            self.event(index, 'prepared', body_bytes=size, body_sha256=sha(path))
            upstream = socket.create_connection((self.profile['host'], self.profile['port']), timeout=max(0.001, min(30, self.deadline - time.monotonic())))
            with self.lock: self.active.add(upstream)
            packet = (f'POST /v1/chat/completions HTTP/1.1\r\nHost: {self.profile["host"]}:{self.profile["port"]}\r\nContent-Type: application/json\r\nContent-Length: {size}\r\nConnection: close\r\n\r\n').encode() + body
            with self.lock:
                if time.monotonic() >= self.deadline: raise TimeoutError('episode deadline before POST')
                upstream.settimeout(max(0.001, self.deadline - time.monotonic()))
                sending = True; self.event(index, 'send_started')
            upstream.sendall(packet); sent = True
            with self.lock: self.posts += 1; self.inflight -= 1; reserved = False
            self.event(index, 'forwarded', body_bytes=size, body_sha256=sha(path))
            relay = self
            class ClientMeter:
                def sendall(self, data):
                    with relay.lock:
                        if time.monotonic() >= relay.deadline: raise TimeoutError('episode deadline')
                        if relay.used + len(data) > relay.caps['combined_wire_bytes']: raise RuntimeError('response wire cap')
                        relay.used += len(data); relay.response_bytes += len(data)
                    client.sendall(data)
            class DeadlineSocket:
                def settimeout(self, seconds): upstream.settimeout(max(0.001, min(seconds, relay.deadline - time.monotonic())))
                def makefile(self, *args, **kwargs): return upstream.makefile(*args, **kwargs)
            response = self.h.agg.relay_one_model_response(ClientMeter(), DeadlineSocket(), path.with_suffix('.response'))
            self.event(index, 'response_completed', **response)
            if response['status'] != 200: raise RuntimeError('upstream HTTP ' + str(response['status']))
        except Exception as exc:
            with self.lock:
                self.failures.append(dict(request=index, type=type(exc).__name__, message=str(exc)))
                if reserved:
                    self.inflight -= 1
                    if sending: self.unknown += 1
                    else: self.used -= size
            self.event(index, 'failed', error_type=type(exc).__name__, message=str(exc), forward_state='forwarded' if sent else 'UNKNOWN_PARTIAL_SEND' if sending else 'not_forwarded')
            if not sent:
                try: client.sendall(b'HTTP/1.1 502 Bad Gateway\r\nContent-Length: 0\r\nConnection: close\r\n\r\n')
                except OSError: pass
        finally:
            for connection in (upstream, client):
                if connection is not None:
                    with self.lock: self.active.discard(connection)
                    connection.close()

    def close(self):
        with self.lock:
            for connection in tuple(self.active):
                try: connection.shutdown(socket.SHUT_RDWR)
                except OSError: pass

    def accounting(self):
        requests = []; known = 0; unknown_usage = []
        ledger = self.root / 'forward_ledger.jsonl'
        events = [json.loads(line) for line in ledger.read_text().splitlines()] if ledger.exists() else []
        for e in events:
            if e['event'] != 'forwarded': continue
            path = self.root / 'wire' / f'{e["request"]:05d}.request.response'; record = path.with_suffix('.response.receipt.json')
            request = self.root / 'wire' / f'{e["request"]:05d}.request.json'
            if sha(request) != e['body_sha256'] or request.stat().st_size != e['body_bytes']: raise ValueError('request binding changed')
            receipt = json.loads(record.read_text()) if record.exists() else None
            if receipt and sha(path) != receipt['body_sha256']: raise ValueError('response binding changed')
            usage = receipt.get('usage') if receipt else None
            if receipt and receipt['complete'] and isinstance(usage, dict) and type(usage.get('total_tokens')) is int: known += usage['total_tokens']
            else: unknown_usage.append(e['request'])
            requests.append(dict(request=e['request'], request_sha256=e['body_sha256'], body_bytes=e['body_bytes'], response=receipt))
        return dict(actual_forwarded_posts=self.posts, attempted_posts=self.attempts, uncertain_partial_sends=self.unknown,
            actual_forwarded_body_bytes=sum(r['body_bytes'] for r in requests), response_wire_bytes=self.response_bytes,
            budget_reserved_combined_wire_bytes=self.used, provider_total_tokens_known=known, unknown_usage_requests=unknown_usage,
            requests=requests, failures=self.failures, integrity_passed=not self.failures and self.unknown == 0,
            byte_scope='budget: serialized request bodies plus downstream response HTTP headers and dechunked bodies; raw provider bodies preserved separately')


def docker_command(root, actor, bridge, profile, h, name):
    root, bridge = safe(root), safe(bridge)
    mounts = [(root / 'work', '/workspace', False), (root / 'inputs', '/inputs', True),
        (Path(actor['runtime']), '/extra', True), (Path(actor['sites']['default']), '/deps', True),
        (bridge, '/model', True), (h.tools.OPENCODE, '/opt/opencode', True), (h.tools.RG, '/usr/local/bin/rg', True)]
    paths = [safe(src) for src, _, _ in mounts]
    if any(a == b or a in b.parents or b in a.parents for i, a in enumerate(paths) for b in paths[i+1:]):
        raise ValueError('ancestor/overlapping actor mounts')
    if os.getuid() == 0: raise ValueError('nonroot actor owner required')
    cmd = ['docker', 'run', '--rm', '--pull', 'never', '--name', name, '--cidfile', str(root / 'container.cid'),
        '--network', 'none', '--read-only', '--user', str(os.getuid()) + ':' + str(os.getgid()), '--cpus', '1', '--memory', '1g',
        '--pids-limit', '256', '--cap-drop', 'ALL', '--security-opt', 'no-new-privileges', '--workdir', '/workspace',
        '--tmpfs', '/tmp:rw,nosuid,size=128m', '--tmpfs', '/home/agent:rw,nosuid,size=256m']
    env = dict(HOME='/home/agent', OPENCODE_CONFIG='/inputs/opencode.json', OPENCODE_DISABLE_MODELS_FETCH='1',
        PYTHONPATH='/deps', PATH='/extra/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin',
        PYTHONDONTWRITEBYTECODE='1', PYTEST_DISABLE_PLUGIN_AUTOLOAD='1', HYPOTHESIS_STORAGE_DIRECTORY='/tmp/hypothesis')
    for key, value in env.items(): cmd += ['-e', key + '=' + value]
    for (src, dst, readonly), path in zip(mounts, paths): cmd += ['--mount', f'type=bind,src={path},dst={dst}' + (',readonly' if readonly else '')]
    return cmd + ['--entrypoint', '/extra/bin/python', h.pool.IMAGE, '/inputs/guest.py', 'gb10/' + profile['model_id'], str(os.getuid())]


def stop_owned(cidfile, name):
    cid = safe(cidfile).read_text().strip()
    if not re.fullmatch('[0-9a-f]{64}', cid): raise ValueError('unverifiable container ID')
    inspected = subprocess.run(['docker', 'inspect', '--format', '{{json .Name}}', cid], capture_output=True, timeout=15)
    if inspected.returncode:
        if b'No such object' in inspected.stderr or b'No such container' in inspected.stderr: return dict(cid=cid, name=name, status='ALREADY_REMOVED')
        raise ValueError('container ownership not proven; no stop')
    if json.loads(inspected.stdout) != '/' + name: raise ValueError('container ownership not proven; no stop')
    result = subprocess.run(['docker', 'rm', '-f', cid], capture_output=True, timeout=15)
    if result.returncode: raise RuntimeError('owned container cleanup failed')
    return dict(cid=cid, name=name, exit=result.returncode)



def run_owned(cmd, name, cidfile, stdout, stderr, timeout):
    """Only this Popen and this exact CID may be collected, including interrupts."""
    result = {}; proc = None; started = time.monotonic()
    with stdout.open('xb') as out, stderr.open('xb') as err:
        try:
            proc = subprocess.Popen(cmd, stdin=subprocess.DEVNULL, stdout=out, stderr=err)
            result['exit'] = proc.wait(timeout=timeout)
        except BaseException as exc:
            result.update(exit=None, error=dict(type=type(exc).__name__, message=str(exc)))
        finally:
            if proc is not None:
                try: result['cleanup'] = stop_owned(cidfile, name)
                except BaseException as exc: result['cleanup_error'] = dict(type=type(exc).__name__, message=str(exc))
                if proc.poll() is None:
                    try: proc.wait(timeout=15)
                    except subprocess.TimeoutExpired: proc.kill(); proc.wait(timeout=15)  # Owned Docker CLI only.
    result.update(stdout_sha256=sha(stdout), stderr_sha256=sha(stderr), seconds=time.monotonic() - started)
    return result


def scored_test(work, repo, labels, runner, output, suite, h):
    available = h.pool.mem_available()
    if available < 4 * 1024**3: return dict(status='DEFERRED', MemAvailable=available)
    name = 'cb-source-score-' + str(os.getpid()) + '-' + str(time.monotonic_ns())
    cid = output / (suite + '.cid'); cmd = h.pool.command(work, repo, labels, runner, name)
    cmd[2:2] = ['--cidfile', str(cid)]
    new(output / (suite + '.command.json'), dict(argv=cmd, name=name, timeout_seconds=240))
    log, errors = output / (suite + '.log'), output / (suite + '.stderr')
    started = time.monotonic(); record = run_owned(cmd, name, cid, log, errors, 240)
    lines = (log.read_bytes() + errors.read_bytes()).decode('utf8', errors='replace').splitlines()
    markers = [s[len(h.pool.MARKER):] for s in lines if s.startswith(h.pool.MARKER)]
    try: payload = json.loads(markers[0]) if len(markers) == 1 else {'fatal': ['missing/duplicate machine result']}
    except ValueError: payload = {'fatal': ['invalid machine result']}
    record.update(result=payload, seconds=time.monotonic() - started, MemAvailable=available)
    record['coverage'] = h.pool.classify(labels, record)
    return record


def score(root, manifest, h):
    output = root / 'scoring'; candidate = output / 'candidate'; work = root / 'work'; clean = root / 'baseline'
    tree(work)  # Reject links, including hardlinks, before candidate copying.
    shutil.copytree(work, candidate, ignore=shutil.ignore_patterns('__pycache__', '.pytest_cache'))
    # Restore every original test subtree and test configuration before the frozen patch.
    tests = sorted((p for p in clean.rglob('tests') if p.is_dir()), key=lambda p: len(p.parts))
    restored = []
    for path in tests:
        if any(parent in path.parents for parent in restored): continue
        dest = candidate / path.relative_to(clean)
        if dest.exists(): shutil.rmtree(dest) if dest.is_dir() else dest.unlink()
        shutil.copytree(path, dest); restored.append(path)
    for path in candidate.rglob('conftest.py'):
        if not (clean / path.relative_to(candidate)).exists(): path.unlink()
    for path in clean.rglob('conftest.py'): shutil.copyfile(path, candidate / path.relative_to(clean))
    for rel in ('pytest.ini', 'pyproject.toml', 'setup.cfg', 'tox.ini'):
        src, dest = clean / rel, candidate / rel
        if src.is_file(): shutil.copyfile(src, dest)
        elif dest.exists(): dest.unlink()
    patch = output / 'test.patch'; helper, _ = h.pool.helpers()
    applied = helper.apply_patch(candidate, patch.read_text()); new(output / 'patch_receipt.json', applied)
    if applied['apply_exit'] != 0: return dict(passed=False, status='TEST_PATCH_FAILED', patch=applied)
    runner = output / 'qualifier.py'; runner.write_text(h.pool.RUNNER)
    result = dict(status='EVALUATED', runner_sha256=sha(runner), suites={})
    for suite in ('f2p', 'ptp'):
        r = scored_test(candidate, manifest['repo'], manifest['labels'][suite], runner, output, suite, h)
        result['suites'][suite] = r
        if r.get('status') == 'DEFERRED' or r.get('error') or r.get('cleanup_error'): break
    result['passed'] = len(result['suites']) == 2 and all(not r.get('error') and not r.get('cleanup_error') and r.get('exit') == 0 and r.get('coverage', {}).get('complete') is True and all(s == 'passed' for s in r['coverage']['labels'].values()) for r in result['suites'].values())
    if len(result['suites']) != 2 or any(r.get('error') or r.get('cleanup_error') or r.get('status') == 'DEFERRED' for r in result['suites'].values()): result['status'] = 'UNFINISHED'
    new(output / 'receipt.json', result); return result


def candidate_diff(root):
    before, after = tree(root / 'baseline'), tree(root / 'work'); changes = []; pieces = []
    for name in sorted(before.keys() | after.keys()):
        if before.get(name) == after.get(name): continue
        changes.append(dict(path=name, before=before.get(name), after=after.get(name)))
        a, b = root / 'baseline' / name, root / 'work' / name
        if all(not p.exists() or p.stat().st_size <= 1024**2 for p in (a, b)):
            left = a.read_text(errors='replace').splitlines(True) if a.is_file() else []
            right = b.read_text(errors='replace').splitlines(True) if b.is_file() else []
            pieces.extend(difflib.unified_diff(left, right, fromfile='base/' + name, tofile='candidate/' + name))
    (root / 'candidate.diff').write_text(''.join(pieces)); return changes


def raw_errors(raw):
    errors = []
    for line in raw.read_text().splitlines():
        event = json.loads(line)
        if event.get('type') == 'error': errors.append(event.get('error'))
    return errors


def successful(result):
    return (result.get('status') == 'ACTOR_RETURNED' and result.get('actor_exit') == 0
        and not result.get('raw_errors') and not result.get('socket_cleanup_error')
        and not result.get('actor', {}).get('error') and not result.get('actor', {}).get('cleanup_error')
        and result.get('accounting', {}).get('integrity_passed') is True
        and result['accounting']['actual_forwarded_posts'] > 0 and result.get('scoring', {}).get('passed') is True)


def execute(root, digest, registry, registry_sha, source):
    m, h, actor, profile = verify(root, digest); root = Path(root)
    if (m['registry'], m['source']) != (dict(path=str(registry), sha256=registry_sha), source): raise ValueError('CLI input differs from manifest')
    with resource_lock():
        new(root / 'reservation.json', dict(manifest_sha256=digest, mode='REAL_SOURCE_EPISODE'))
        result = dict(status='ERROR', source=source, manifest_sha256=digest, source_success=False)
        bridge = relay = server = thread = None
        name = 'cb-source-' + str(os.getpid()) + '-' + str(time.monotonic_ns())
        old_signal = signal.getsignal(signal.SIGTERM)
        def interrupted(*_): raise InterruptedError('SIGTERM')
        signal.signal(signal.SIGTERM, interrupted)
        try:
            h.teacher.validate_vllm_model_profile(m['profile']['path'], m['profile']['sha256'], full=True)
            result['backend'] = h.teacher.verify_vllm_backend(profile)
            bridge = Path(tempfile.mkdtemp(prefix='cb-src-', dir='/tmp')); bridge.chmod(0o700); identity = bridge.stat().st_ino
            relay = Relay(root, profile, h, deadline=time.monotonic() + CAPS['seconds'])
            class Server(socketserver.ThreadingUnixStreamServer): daemon_threads = False; block_on_close = True
            class Handler(socketserver.BaseRequestHandler):
                def handle(self): relay.handle(self.request)
            server = Server(str(bridge / 's'), Handler); os.chmod(bridge / 's', 0o600)
            thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
            cmd = docker_command(root, actor, bridge, profile, h, name); new(root / 'actor_command.json', cmd)
            result['actor'] = run_owned(cmd, name, root / 'container.cid', root / 'raw.jsonl', root / 'actor.stderr', CAPS['seconds'])
            fault = result['actor'].get('error')
            status = ('INTERRUPTED' if fault['type'] in ('KeyboardInterrupt', 'InterruptedError') else 'RUNTIME_ERROR') if fault else 'ACTOR_RETURNED'
            if result['actor'].get('cleanup_error'): status = 'CLEANUP_FAILED'
            result.update(status=status, actor_exit=result['actor'].get('exit'), raw_sha256=sha(root / 'raw.jsonl'), raw_errors=raw_errors(root / 'raw.jsonl'))
        except BaseException as exc:
            result.update(status='INTERRUPTED' if isinstance(exc, (KeyboardInterrupt, InterruptedError)) else 'ERROR', error=dict(type=type(exc).__name__, message=str(exc)))
        finally:
            if relay: relay.close()
            if server:
                if thread and thread.is_alive(): server.shutdown()
                server.server_close()
            if relay:
                try: result['accounting'] = relay.accounting()
                except Exception as exc: result['accounting_error'] = str(exc)
            if bridge:
                try:
                    if bridge.stat().st_ino != identity or set(p.name for p in bridge.iterdir()) != {'s'}: raise ValueError('UDS ownership changed')
                    (bridge / 's').unlink(); bridge.rmdir()
                except Exception as exc: result['socket_cleanup_error'] = str(exc)
        try:
            verify(root, digest, initial=False)
            result['changed_artifacts'] = candidate_diff(root)
            if result['status'] == 'ACTOR_RETURNED' and not result.get('actor', {}).get('cleanup_error'):
                result['scoring'] = score(root, m, h)
            verify(root, digest, initial=False)
            if result.get('scoring', {}).get('status') == 'UNFINISHED': result['status'] = 'UNFINISHED_SCORING'
            if result['status'] == 'ACTOR_RETURNED' and (result.get('raw_errors') or result.get('actor_exit') != 0 or result.get('accounting', {}).get('integrity_passed') is not True): result['status'] = 'GENERATION_FAULT'
            result['source_success'] = successful(result)
        except BaseException as exc:
            result['finalization_error'] = dict(type=type(exc).__name__, message=str(exc))
        finally:
            try: new(root / 'receipt.json', result)
            finally: signal.signal(signal.SIGTERM, old_signal)
        return result


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__); mode = p.add_mutually_exclusive_group(required=True)
    mode.add_argument('--prepare', action='store_true'); mode.add_argument('--execute', action='store_true')
    p.add_argument('--registry', type=Path, required=True); p.add_argument('--registry-sha', required=True)
    p.add_argument('--source', choices=SOURCES, required=True); p.add_argument('--root', type=Path, required=True)
    for key in ('projection', 'profile'): p.add_argument('--' + key, type=Path); p.add_argument('--' + key + '-sha')
    p.add_argument('--manifest-sha'); args = p.parse_args(argv)
    if args.prepare:
        if args.manifest_sha or any(getattr(args, k) is None for k in ('projection', 'projection_sha', 'profile', 'profile_sha')): p.error('prepare requires projection/profile path+sha; no manifest-sha')
        result = prepare(args.registry, args.registry_sha, args.source, args.root, args.projection, args.projection_sha, args.profile, args.profile_sha)
    else:
        if not args.manifest_sha or any(getattr(args, k) is not None for k in ('projection', 'projection_sha', 'profile', 'profile_sha')): p.error('execute requires manifest-sha and uses manifest projection/profile')
        result = execute(args.root, args.manifest_sha, args.registry, args.registry_sha, args.source)
    print(json.dumps({k: result[k] for k in ('status', 'source', 'root', 'manifest_sha256', 'source_success') if k in result}))
    return 0 if result['status'] in ('CPU_PREPARED', 'ACTOR_RETURNED') and not any(k in result for k in ('error', 'finalization_error', 'socket_cleanup_error', 'accounting_error')) else 1


if __name__ == '__main__': raise SystemExit(main())
