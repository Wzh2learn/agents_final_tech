#!/usr/bin/env python3
"""One Django34570 no-experience development task; prepare never calls a model.

Reuse the frozen OpenCode transport and native SQLite evaluator.  References,
benchmark tests and receipts stay outside the actor's explicit bind mounts.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
PRIVATE = Path('/home/testuser/wzh/research_evidence/agent_learning_20261030')
TASK = PRIVATE / 'django34570_development_v1'
STUDY = PRIVATE / 'alfworld_text_qualification_20261106/context_study_v1'
WINDOW = STUDY / 'learning_comparison_v1/owned_window_v3'
EVAL = STUDY / 'learning_comparison_v1/hf_evaluation_v1'
MANUAL_RESTORE_SHA = '131747165d1ce410612065bd7d619fc17382a9c8ddde941902e6cc750fa9d251'
PROFILE = PRIVATE / 'django_aggregation_agent_20261106/model_profile.json'
PROFILE_SHA = 'acce24743e43c205b605b8bceddd4f5eb756d93fdba5f58e28bc32ba772ab6d0'
DEPS = PRIVATE / 'swe_contextbench_django_env_20261104/site'
DEPS_MANIFEST = PRIVATE / 'swe_contextbench_django_qualification_20261104/dependency_manifest.json'
IMAGE = 'sha256:648a1999badfe683239ec49e05b2a508e37f762213478122c58fa713f6c00f58'
BASE = '0ec60661e61b153e6bcec64649b1b7f524eb3e18'
CAPS = {'posts': 48, 'seconds': 1200, 'model_wire_bytes_combined': 64000000}
PINNED = {
    'record.json': '5b2b332d1e9025bc9b13e04a0f4eda0badc69f74f5d669f0cb11c3ce9acef6c9',
    'source_manifest.json': 'a0b766cd96bc828b7cb4622c43160e75e87dc303e6043ecb40357efd92cbc95b',
    'actor/task.txt': 'f7b282c1813d1e6f0c48d2ac8ee1e67253de379d7264237524f4c7aa27811b58',
    'actor/public_feedback.json': '2e2b0623bc1ff9a67488a652d0ddd174fabf3b2c0e56da4068fd9df12085a1cb',
    'scoring/public_issue_probe.py': '956143351eca993c639f2e08d74f140b7355c13a035675aef2f0af7c65ace28e',
    'scoring/test.patch': 'daa30af155d6856d4a0a40d4617f3ea06dfc1dee07cfa290da8898faed60ed50',
}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def regular(path):
    path = Path(path)
    if not path.is_absolute() or any(p.is_symlink() for p in [path, *path.parents]):
        raise ValueError('absolute, non-symlink path required')
    if any(c in str(path) for c in (',', '\n', '\r')):
        raise ValueError('unsafe mount path')
    return path


def socket_directory(root):
    """A deterministic short mount path, frozen equally by prepare and execute."""
    root=regular(root)
    uid=os.getuid() if hasattr(os,'getuid') else 0
    path=Path('/tmp')/('d34570-'+str(uid)+'-'+hashlib.sha256(os.fsencode(root)).hexdigest()[:24])
    if len(os.fsencode(path/'model.sock'))>103:raise ValueError('UDS path exceeds portable byte budget')
    return path


def owned_socket_directory(path):
    path=regular(path)
    uid=os.getuid() if hasattr(os,'getuid') else 0
    if path.parent!=Path('/tmp') or not re.fullmatch('d34570-'+str(uid)+'-[a-f0-9]{24}',path.name):
        raise ValueError('not a task-owned short socket directory')
    return path


def create_socket_directory(path):
    path=owned_socket_directory(path)
    path.mkdir(mode=0o755,exist_ok=False)
    path.chmod(0o755)  # The readonly container bind must remain traversable.
    value=path.stat()
    return (value.st_dev,value.st_ino)


def cleanup_socket_directory(path,identity):
    """Remove only this invocation's directory and its actual model socket."""
    path=owned_socket_directory(path)
    if not path.exists():return False
    value=path.lstat()
    if not stat.S_ISDIR(value.st_mode) or value.st_uid!=os.getuid() or (value.st_dev,value.st_ino)!=tuple(identity):
        raise ValueError('socket directory ownership/inode changed')
    entries=list(path.iterdir())
    if any(p.name!='model.sock' for p in entries):raise ValueError('unexpected socket-directory entry; preserve it')
    for entry in entries:
        item=entry.lstat()
        if not stat.S_ISSOCK(item.st_mode) or item.st_uid!=os.getuid():raise ValueError('not an owned socket; preserve it')
        entry.unlink()
    path.rmdir()
    return True


def tree(path):
    path = regular(path)
    result = {}
    for p in sorted(path.rglob('*')):
        if p.is_symlink() or '.git' in p.relative_to(path).parts:
            raise ValueError('links or Git history in readable tree')
        if p.is_file():
            if p.stat().st_nlink != 1:
                raise ValueError('hard-linked file in readable tree')
            result[p.relative_to(path).as_posix()] = sha(p)
        elif not p.is_dir():
            raise ValueError('non-regular readable entry')
    if not path.is_dir() or not result:
        raise ValueError('missing readable tree')
    return result


def read_checked(path, digest):
    path = regular(path)
    if not re.fullmatch('[a-f0-9]{64}', digest or '') or sha(path) != digest:
        raise ValueError('file hash changed: ' + str(path))
    return json.loads(path.read_text(encoding='utf8'))


def write_new(path, value):
    with Path(path).open('x', encoding='utf8') as out:
        json.dump(value, out, indent=2, ensure_ascii=False)
        out.write('\n')


def helpers():
    if str(HERE) not in sys.path:
        sys.path.insert(0, str(HERE))
    import run_django_aggregation_agent_20261106 as agg
    import qualify_swe_contextbench_django_20261104 as native
    return agg, native


def check_assets():
    for rel, digest in PINNED.items():
        if sha(regular(TASK / rel)) != digest:
            raise ValueError('Django34570 frozen input changed: ' + rel)
    record = json.loads((TASK / 'record.json').read_text())
    if record['instance_id'] != 'django__django-34570' or record['base_commit'] != BASE:
        raise ValueError('wrong task/base')
    if tree(TASK / 'actor/clean_base') != json.loads((TASK / 'source_manifest.json').read_text()):
        raise ValueError('base source changed')
    deps = read_checked(DEPS_MANIFEST, 'fece7e6e6a8ec7e87b8218a49e52407f4496a76c38faeabec382c7e0754e5d8e')
    if tree(DEPS) != deps['site_files'] or (DEPS / 'django').exists():
        raise ValueError('isolated dependencies changed')
    if len(record['focus_labels']) != 1 or len(record['regression_labels']) != 13:
        raise ValueError('native test selection changed')
    scoring = read_checked(TASK / 'scoring/base_with_tests_files.json',
                           record['arms']['base_with_tests']['source_files_manifest_sha256'])
    if tree(TASK / 'scoring/base_with_tests') != scoring:
        raise ValueError('qualified scoring tests/config/source changed')
    return record


def audit_command(cmd, mounts):
    """Exact bind allowlist; a parent bind is rejected even when read-only."""
    actual = {}
    if cmd[:2] != ['docker', 'run'] or cmd.count(IMAGE) != 1:
        raise ValueError('wrong isolated runtime')
    required = {'--network': 'none', '--pull': 'never', '--workdir': '/root',
                '--entrypoint': '/extra/bin/python', '--cap-drop': 'ALL',
                '--security-opt': 'no-new-privileges'}
    for key, value in required.items():
        if cmd.count(key) != 1 or cmd[cmd.index(key) + 1] != value:
            raise ValueError('unsafe container flag: ' + key)
    if cmd.count('--read-only') != 1 or any(x in cmd for x in ('-v', '--volume', '--privileged', '--device', '--pid', '--userns')):
        raise ValueError('unexpected container access')
    for index, value in enumerate(cmd):
        if value == '--mount':
            parts = cmd[index + 1].split(',')
            fields = dict(p.split('=', 1) for p in parts if '=' in p)
            if set(fields) != {'type', 'src', 'dst'} or fields['type'] != 'bind':
                raise ValueError('unexpected mount syntax')
            regular(fields['src'])
            dst = fields['dst']
            if dst in actual or any(p not in ('readonly',) and '=' not in p for p in parts):
                raise ValueError('ambiguous mount')
            actual[dst] = {'source': fields['src'], 'readonly': 'readonly' in parts}
    if actual != mounts:
        raise ValueError('actor readable surface differs from frozen allowlist')
    if [cmd[i + 1] for i, x in enumerate(cmd) if x == '--tmpfs'] != [
            '/tmp:rw,nosuid,size=128m', '/home/agent:rw,nosuid,size=256m']:
        raise ValueError('missing isolated HOME/tmpfs')
    env = [cmd[i + 1] for i, x in enumerate(cmd) if x in ('-e', '--env')]
    if set(env) != {'HOME=/home/agent', 'OPENCODE_DISABLE_MODELS_FETCH=1', 'PYTHONPATH=/deps',
                    'PATH=/extra/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin',
                    'PYTHONDONTWRITEBYTECODE=1', 'PYTEST_DISABLE_PLUGIN_AUTOLOAD=1',
                    'HYPOTHESIS_STORAGE_DIRECTORY=/tmp/hypothesis'} or len(env) != 7:
        raise ValueError('unexpected environment or PostgreSQL path')


def relay_capped(client, upstream, path, relay, lock, payload_bytes, response_bytes, limit, deadline=None):
    """Use the existing body/usage relay, with a combined wire-byte ceiling."""
    class Meter:
        def sendall(self, data):
            with lock:
                if deadline is not None and time.monotonic() >= deadline:
                    raise RuntimeError('model episode deadline')
                if sum(payload_bytes) + response_bytes[0] + len(data) > limit:
                    raise RuntimeError('combined model wire-byte cap')
                response_bytes[0] += len(data)
            client.sendall(data)
    return relay(Meter(), upstream, path)


def check_http_frame(first):
    """No GET-body or conflicting framing may smuggle an uncounted POST."""
    head, body = first.split(b'\r\n\r\n', 1)
    lines = head.split(b'\r\n')
    fields = [line.split(b':', 1) for line in lines[1:]]
    if any(len(p) != 2 or p[0] != p[0].strip() for p in fields):
        raise ValueError('ambiguous HTTP header')
    lengths = [v.strip() for k, v in fields if k.lower() == b'content-length']
    if any(k.lower() in (b'transfer-encoding', b'expect') for k, v in fields) or len(lengths) > 1:
        raise ValueError('ambiguous HTTP framing')
    if lines[0] == b'GET /v1/models HTTP/1.1':
        if body or lengths not in ([], [b'0']):
            raise ValueError('GET body forbidden')
    elif lines[0] == b'POST /v1/chat/completions HTTP/1.1':
        if len(lengths) != 1 or not lengths[0].isdigit() or len(body) > int(lengths[0]):
            raise ValueError('invalid POST length')
    else:
        raise ValueError('unsupported model HTTP request')


def guard_execution(root):
    """Private derived harness is callable only by the reserving entry process."""
    reservation = json.loads((root / 'reservation.json').read_text(encoding='utf8'))
    digest = os.environ.get('DJANGO34570_EXECUTION_MANIFEST_SHA')
    if (reservation.get('outer_pid') != os.getppid() or reservation.get('execution_manifest_sha256') != digest
            or reservation.get('mode') != 'REAL_8B_NO_EXPERIENCE_DEVELOPMENT'
            or sha(root / 'execution_manifest.json') != digest):
        raise ValueError('derived harness requires explicit reserved execution')
    frozen=read_checked(root/'execution_manifest.json',digest)
    if 'latest_restore' in frozen:verify_frozen_latest_restore(frozen)


def derive(root, profile):
    agg, _ = helpers()
    actor = {'sites': {'default': str(DEPS)}, 'runtime': str(root / 'runtime')}
    code = agg.derive(root, 'source', 'none', None, actor, profile,
                      root / 'public_task.txt', None, candidate=TASK / 'actor/clean_base')
    replace = agg.core.replace_once
    changes = [
        ("UP=Path('/home/testuser/wzh/research_evidence/agent_frontier_20261029/skillsbench_v1_1/tasks')", f'UP=Path({str(TASK / "actor")!r})', 1),
        (f'src=Path({str(agg.QUAL / "source")!r})', f'src=Path({str(TASK / "actor")!r})', 1),
        ('source__none__seed7201', 'episode', 1),
        ("if task not in ('source','target') or arm != 'no_skill': raise SystemExit('unsupported')",
         "if task != 'django__django-34570' or arm != 'no_skill': raise SystemExit('unsupported')", 1),
        (",0.2,7201)", ',0.2,17)', 1), ("'seed':7201", "'seed':17", 1),
        ('6000000', str(CAPS['model_wire_bytes_combined']), 4),
        ("case.mkdir(parents=True, exist_ok=False)", "preparing=sys.argv[3:]==['prepare']\nif sys.argv[3:] not in ([],['prepare']):raise ValueError('invalid stage')\nif not preparing:guard_execution(ROOT)\ncase.mkdir(parents=True, exist_ok=not preparing)", 1),
        ("work=case/'work'; work.mkdir(); work.chmod(0o777); bridge=Path('/tmp')/('skill_bridge_'+str(os.getpid())); bridge.mkdir(exist_ok=False)", f"work=case/'work'; work.mkdir(exist_ok=not preparing); work.chmod(0o777); bridge=Path({str(socket_directory(root))!r})", 1),
        (" payload['temperature'],payload['seed']=temperature,seed", " payload['chat_template_kwargs']={'enable_thinking':False}\n payload['max_tokens']=8192\n payload.pop('max_completion_tokens',None)\n payload['temperature'],payload['seed']=temperature,seed", 1),
        ("post_count=[0];", "post_count=[0]; response_bytes=[0]; episode_deadline=[None];", 1),
        ('upstream.settimeout(900)', 'upstream.settimeout(max(0.001,episode_deadline[0]-time.monotonic()))', 1),
        ('sum(payload_bytes)', '(sum(payload_bytes)+response_bytes[0])', 4),
        ("(work/'instructions.txt').write_text(body,encoding='utf8')", f"(work/'instructions.txt').write_text(body,encoding='utf8')\nshutil.copyfile(Path({str(root / 'public_feedback.json')!r}),work/'public_feedback.json')", 1),
        ("name='agent-skill-'+str(os.getpid())", f"name={'django34570-' + root.name!r}", 1),
        ("receipt={'sampling_metadata':sampling", "receipt={'response_wire_bytes':response_bytes[0],'sampling_metadata':sampling", 1),
    ]
    for old, new, count in changes:
        code = replace(code, old, new, count)
    # Freeze once at prepare. Actual execution cannot silently recopy a later base.
    copy_block = (f"shutil.copytree(Path({str(TASK / 'actor/clean_base')!r}),work,dirs_exist_ok=True)\n"
        "for dp,dirs,files in os.walk(work):\n os.chmod(dp,0o777)\n for fn in files:\n  p=Path(dp)/fn\n"
        "  if p.is_symlink():raise ValueError('unexpected source link')\n"
        "  os.chmod(p,0o777 if p.stat().st_mode & 0o111 else 0o666)\n")
    code = replace(code, copy_block, 'if preparing:\n' + ''.join(' ' + line + '\n' for line in copy_block.splitlines()))
    # Preserve real attempt/forward/error distinctions even if a socket fails.
    old = "  calls.append(line.decode()); upstream=socket.create_connection(('127.0.0.1',18104),timeout=30)\n  try:upstream.sendall(first);relay_one_model_response(self.request,upstream,case/'model_response_bodies'/(request_path.stem+'.body') if line.startswith(b'POST') else None)\n  finally:upstream.close()"
    new = """  calls.append(line.decode()); upstream=None
  def event(kind,**extra):
   if line.startswith(b'POST'):
    with post_lock:
     with (case/'forward_ledger.jsonl').open('a') as log:log.write(json.dumps({'request':request_path.name,'event':kind,**extra})+'\\n');log.flush()
  event('attempt')
  try:
   upstream=socket.create_connection(('127.0.0.1',18104),timeout=30)
   if time.monotonic()>=episode_deadline[0]:raise RuntimeError('model episode deadline')
   upstream.sendall(first);event('forwarded',request_sha256=meta['request_body_sha256'])
   relay_capped(self.request,upstream,case/'model_response_bodies'/(request_path.stem+'.body') if line.startswith(b'POST') else None,relay_one_model_response,post_lock,payload_bytes,response_bytes,64000000,episode_deadline[0])
   event('response_completed')
  except Exception as exc:event('error',error_type=type(exc).__name__,message=str(exc));raise
  finally:
   if upstream is not None:upstream.close()"""
    code = replace(code, old, new)
    mounts = []
    for name in ('instructions.txt', 'public_feedback.json', 'opencode.json'):
        mounts += ['--mount', f'type=bind,src={root / "episode/work" / name},dst=/root/{name},readonly']
    code = replace(code, 'cmd[_at:_at]=[', 'cmd[_at:_at]=' + repr(mounts) + '+[')
    import_line = f"sys.path.insert(0,{str(HERE)!r})\nfrom run_django34570_development import audit_command,relay_capped,check_http_frame,guard_execution,create_socket_directory,cleanup_socket_directory\n"
    code = replace(code, 'from pathlib import Path\n\nROOT=', 'from pathlib import Path\n' + import_line + '\nROOT=')
    code = replace(code, "  line=first.split(b'\\r\\n',1)[0].rsplit(b' ',1)[0]",
        "  try:check_http_frame(first)\n  except ValueError:\n   calls.append('DENIED:invalid_http_frame');return\n  line=first.split(b'\\r\\n',1)[0].rsplit(b' ',1)[0]")
    gate = f"\naudit_command(cmd,json.loads(Path({str(root / 'surface.json')!r}).read_text()))\ncommand_path=Path({str(root / 'actor_command.json')!r})\nif preparing:\n with command_path.open('x') as log:json.dump(cmd,log,indent=2)\n raise SystemExit(0)\nif json.loads(command_path.read_text())!=cmd:raise ValueError('frozen actor command changed')\n"
    code = replace(code, '; server=Server(str(sockpath),Handler);', gate + 'episode_deadline[0]=time.monotonic()+1200\nserver=Server(str(sockpath),Handler);')
    # Own the short UDS only while running; a bind/startup error must clean it too.
    code=replace(code, "server=Server(str(sockpath),Handler);os.chmod(sockpath,0o666);threading.Thread(target=server.serve_forever,daemon=True).start();start=time.time()\ntry:\n try:",
        "server=None;server_started=False;bridge_identity=None\ntry:\n bridge_identity=create_socket_directory(bridge)\n server=Server(str(sockpath),Handler);os.chmod(sockpath,0o666);threading.Thread(target=server.serve_forever,daemon=True).start();server_started=True;start=time.time()\n try:")
    code=replace(code, " server.shutdown();server.server_close();sockpath.unlink(missing_ok=True);bridge.rmdir()",
        " if server is not None:\n  if server_started:server.shutdown()\n  server.server_close()\n if bridge_identity is not None:cleanup_socket_directory(bridge,bridge_identity)")
    if str(agg.QUAL) in code or 'research-pg' in code or 'pgdriver' in code:
        raise ValueError('old source/PG binding survived derivation')
    compile(code, '<django34570-bound-harness>', 'exec')
    return code


def prepare(root):
    if sys.version_info[:2] != (3, 12):
        raise ValueError('prepare/run requires the qualified Python3.12 chain')
    root = regular(root)
    if root.parent != TASK / 'attempts' or not re.fullmatch('[a-zA-Z0-9][a-zA-Z0-9_-]{0,47}', root.name):
        raise ValueError('new task-private attempt root required')
    record = check_assets()
    profile = read_checked(PROFILE, PROFILE_SHA)
    if (profile['model_id'], profile['context'], profile['output'], profile['host'], profile['port']) != ('qwen3-8b-qual', 32768, 8192, '127.0.0.1', 18104):
        raise ValueError('wrong frozen 8B profile')
    agg, native = helpers()
    if sha(agg.core.BASE) != agg.core.BASE_SHA or native.shared.IMAGE != IMAGE or native.ENV / 'site' != DEPS:
        raise ValueError('qualified harness/image/dependencies changed')
    if sha(native.__file__) != record['qualifier_sha256'] or sha(native.shared.__file__) != record['shared_qualifier_sha256']:
        raise ValueError('qualified native test interface changed')
    root.parent.mkdir(exist_ok=True)
    root.mkdir(mode=0o700)
    (root / 'runtime/bin').mkdir(parents=True)
    alias = root / 'runtime/bin/python'
    alias.write_text('#!/bin/sh\nexec /usr/local/bin/python3 "$@"\n')
    alias.chmod(0o755)
    feedback = (TASK / 'actor/public_feedback.json').read_text()
    (root / 'public_feedback.json').write_text(feedback)
    (root / 'public_task.txt').write_text((TASK / 'actor/task.txt').read_text().strip() +
        '\n\nPublic reproduction on the unmodified base (shared task input, NOT an actor failure or prior experience):\n' + feedback)
    work = root / 'episode/work'
    mounts = {'/root': {'source': str(work), 'readonly': False},
              '/bridge': {'source': str(socket_directory(root)), 'readonly': True},
              '/opt/opencode': {'source': '/home/testuser/.opencode/bin/opencode', 'readonly': True},
              '/usr/local/bin/rg': {'source': '/home/testuser/.cache/opencode/bin/rg', 'readonly': True},
              '/deps': {'source': str(DEPS), 'readonly': True},
              '/extra': {'source': str(root / 'runtime'), 'readonly': True},
              '/runtime': {'source': str(root / 'runtime'), 'readonly': True}}
    mounts.update({'/root/' + n: {'source': str(work / n), 'readonly': True}
                   for n in ('instructions.txt', 'public_feedback.json', 'opencode.json')})
    write_new(root / 'surface.json', mounts)
    (root / 'harness.py').write_text(derive(root, profile))
    # Execute only setup and command auditing; the guard exits before UDS/model/Docker.
    proc = subprocess.run([sys.executable, str(root / 'harness.py'), 'django__django-34570', 'no_skill', 'prepare'],
                          capture_output=True, timeout=120)
    (root / 'prepare.stdout').write_bytes(proc.stdout)
    (root / 'prepare.stderr').write_bytes(proc.stderr)
    if proc.returncode:
        raise RuntimeError('CPU preparation failed; retain prepare.stderr')
    audit_command(json.loads((root / 'actor_command.json').read_text()), mounts)
    components = [Path(__file__), Path(agg.__file__), Path(agg.core.__file__), Path(agg.requests_runner.__file__),
                  Path(native.__file__), Path(native.shared.__file__), agg.core.BASE,
                  Path(sys.modules['scripts.graph.research_tool_runtime'].__file__)]
    bindings = {str(p): sha(p) for p in components + [PROFILE, DEPS_MANIFEST, TASK / 'scoring/base_with_tests_files.json'] +
                [TASK / rel for rel in PINNED] + [root / n for n in
                ('harness.py', 'surface.json', 'actor_command.json', 'public_task.txt', 'public_feedback.json')]}
    bindings.update({m['source']: sha(m['source']) for dst, m in mounts.items() if dst in ('/opt/opencode', '/usr/local/bin/rg')})
    manifest = {'schema': 'django34570_development_v1', 'root': str(root), 'task_id': 'django__django-34570',
                'base': BASE, 'condition': 'none', 'seed': 17, 'context': 32768, 'output': 8192,
                'native_thinking': False, 'caps': CAPS, 'image': IMAGE, 'bindings': bindings,
                'work_files': tree(work), 'runtime_files': tree(root / 'runtime'), 'deps_files': tree(DEPS),
                'scoring_files': tree(TASK / 'scoring/base_with_tests'), 'focus_labels': record['focus_labels'],
                'regression_labels': record['regression_labels'], 'models_called': 0,
                'shared_public_feedback_is_not_actor_failure': True, 'unit': 'one development task',
                'status': 'CPU_PREPARED_NOT_EXECUTABLE'}
    write_new(root / 'manifest.json', manifest)
    return {'status': manifest['status'], 'manifest_sha256': sha(root / 'manifest.json'), 'root': str(root)}


def verify_prepared(root, digest):
    root = regular(root)
    manifest = read_checked(root / 'manifest.json', digest)
    if manifest['root'] != str(root) or root.parent != TASK / 'attempts':
        raise ValueError('manifest root mismatch')
    for path, binding in manifest['bindings'].items():
        if sha(regular(path)) != binding:
            raise ValueError('bound input/component changed: ' + path)
    for path, key in ((root / 'episode/work', 'work_files'), (root / 'runtime', 'runtime_files'),
                      (DEPS, 'deps_files'), (TASK / 'scoring/base_with_tests', 'scoring_files')):
        if tree(path) != manifest[key]:
            raise ValueError('frozen tree changed: ' + key)
    audit_command(json.loads((root / 'actor_command.json').read_text()), json.loads((root / 'surface.json').read_text()))
    return manifest


@contextmanager
def queue_lock():
    import fcntl
    with regular(STUDY / 'model_resource.lock').open('r+') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        try:
            yield
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)


def process_identity(pid):
    if type(pid) is not int or pid <= 0:
        raise ValueError('invalid restored PID')
    proc = Path('/proc') / str(pid)
    raw = (proc / 'cmdline').read_bytes()
    return {'pid': pid, 'argv': raw.rstrip(b'\0').decode().split('\0'),
            'argv_sha256': hashlib.sha256(raw).hexdigest(), 'cwd': os.readlink(proc / 'cwd'),
            'start_ticks': (proc / 'stat').read_text().rsplit(')', 1)[1].split()[19],
            'executable_sha256': sha(proc / 'exe')}


def verify_restoration(profile, admission, result, identity):
    if any(result.get(k) is not True for k in ('owned8b_restored_healthy', 'restored_exact_argv', 'shared35_unchanged', 'shared27_unchanged')):
        raise ValueError('owned restoration not complete')
    old = admission['owned_process']
    if result.get('restored_8b_pid') != identity['pid'] or old['argv'] != identity['argv'] or old['cwd'] != identity['cwd']:
        raise ValueError('restored process differs from original argv/cwd')
    agg, _ = helpers()
    agg.verify_server_argv(identity['argv'], profile)
    if identity['executable_sha256'] != profile['server_executable_sha256']:
        raise ValueError('restored executable changed')


def latest_restore_reference(path,digest):
    """Only two explicit closed receipt schemas; no caller-supplied free PID."""
    path=regular(path)
    if path.resolve()!=path or PRIVATE not in path.parents:raise ValueError('latest restoration must be canonical inside private ROOT')
    value=read_checked(path,digest)
    if path==EVAL/'manual_restore_v1/RESULT.json':
        # This historical schema encodes healthy in the exact D-qualified status,
        # not a nonexistent restored_healthy field. Its known content SHA is fixed.
        if (digest!=MANUAL_RESTORE_SHA or value.get('status')!='ORIGINAL_Q4_RESTORED_AFTER_PREGENERATION_IDENTITY_RACE' or type(value.get('health_gets')) is not int or value['health_gets']<=0 or type(value.get('model_generation_posts')) is not int or value['model_generation_posts']!=0):raise ValueError('manual restoration health/status contract differs')
        schema='manual_restore_v1_known_sha_status_health_contract'
    elif path.parent.parent==EVAL and path.name=='RESULT.json' and re.fullmatch(r'RUN_v[1-9][0-9]*',path.parent.name):
        if (value.get('status') not in {'ALL_FIVE_ARMS_RETURNED','STOPPED_RESTORE_REQUIRED'} or value.get('restored_healthy') is not True or type(value.get('window_wall_seconds')) not in (int,float) or value['window_wall_seconds']<0 or value.get('restoration_error') or value.get('shared_identity_error')):raise ValueError('evaluation restoration is not closed and healthy')
        schema='hf_evaluation_closed_restored_healthy_v1'
    else:raise ValueError('unsupported latest restoration source schema/path')
    if any(value.get(key) is not True for key in ('shared35_unchanged','shared27_unchanged')):raise ValueError('latest restoration changed shared services')
    process=value.get('restored_process')
    if (type(process) is not dict or set(process)!={'pid','start_ticks','argv','cwd','exe'} or type(process['pid']) is not int or process['pid']<=0 or type(process['start_ticks']) is not str or not process['start_ticks'].isdigit() or not int(process['start_ticks']) or type(process['argv']) is not list or not process['argv'] or any(type(x) is not str or not x or '\0' in x for x in process['argv']) or any(type(process[k]) is not str or not process[k] for k in ('cwd','exe'))):raise ValueError('latest restoration lacks a complete process identity')
    return {'path':str(path),'sha256':digest,'schema':schema},process


def process_identity_full(pid):
    identity=process_identity(pid)
    return {**identity,'exe':os.readlink(Path('/proc')/str(pid)/'exe')}


def verify_latest_restoration(profile,admission,legacy_result,restored,identity):
    """Preserve the original owned-Q4 contract; only PID/start time may renew."""
    expected=('qwen3-8b-qual','127.0.0.1',18104,32768,8192,
              '/home/testuser/wzh/models/gguf/qwen3-8b/Qwen3-8B-Q4_K_M.gguf',
              'd98cdcbd03e17ce47681435b5150e34c1417f50b5c0019dd560e4882c5745785')
    if tuple(profile.get(k) for k in ('model_id','host','port','context','output','gguf_path','gguf_sha256'))!=expected:raise ValueError('latest restoration requires the pinned original Q4 profile')
    if any(legacy_result.get(k) is not True for k in ('owned8b_restored_healthy','restored_exact_argv','shared35_unchanged','shared27_unchanged')):raise ValueError('original window restoration proof failed')
    old=admission['owned_process'];argv=old['argv']
    flags={'-m':profile['gguf_path'],'--host':profile['host'],'--port':str(profile['port']),'--alias':profile['model_id'],'-c':str(profile['context']),'-n':str(profile['output']),'-np':'1'}
    if (not argv or any(type(a) is not str or a.startswith(('--lora','--adapter')) for a in argv) or argv.count('--no-context-shift')!=1 or any(argv.count(k)!=1 or argv.index(k)+1>=len(argv) or argv[argv.index(k)+1]!=v for k,v in flags.items()) or old.get('exe')!=argv[0]):raise ValueError('original admission is not unadapted owned Q4')
    if any(restored[k]!=old[k] for k in ('argv','cwd','exe')):raise ValueError('latest restoration argv/cwd/exe differs from original Q4')
    if any(identity.get(k)!=restored[k] for k in ('pid','start_ticks','argv','cwd','exe')) or identity.get('executable_sha256')!=profile['server_executable_sha256']:raise ValueError('actual process differs from latest restoration identity')


def verify_frozen_latest_restore(frozen):
    ref=frozen['latest_restore'];actual,restored=latest_restore_reference(Path(ref['path']),ref['sha256'])
    if actual!=ref:raise ValueError('frozen latest restoration schema/reference changed')
    profile=read_checked(PROFILE,PROFILE_SHA);admission=read_checked(WINDOW/'ADMISSION.json',frozen['admission_sha256']);legacy=read_checked(WINDOW/'RESULT.json',frozen['result_sha256']);identity=process_identity_full(restored['pid'])
    verify_latest_restoration(profile,admission,legacy,restored,identity)
    if identity!=frozen['identity']:raise ValueError('runtime changed since latest restoration binding')
    return identity


def bind_runtime(root, digest, admission_sha, result_sha, *, latest_restore_path=None, latest_restore_sha=None):
    if (latest_restore_path is None)!=(latest_restore_sha is None):raise ValueError('latest restoration path and SHA must be supplied together')
    with queue_lock():
        verify_prepared(root, digest)
        admission = read_checked(WINDOW / 'ADMISSION.json', admission_sha)
        result = read_checked(WINDOW / 'RESULT.json', result_sha)
        profile = read_checked(PROFILE, PROFILE_SHA)
        latest_ref=None
        if latest_restore_path is None:
            identity=process_identity(result['restored_8b_pid'])
            verify_restoration(profile,admission,result,identity)
        else:
            latest_ref,restored=latest_restore_reference(latest_restore_path,latest_restore_sha)
            identity=process_identity_full(restored['pid'])
            verify_latest_restoration(profile,admission,result,restored,identity)
        agg, _ = helpers()
        # The profile's original PID is deliberately not used for runtime identity.
        profile = agg.validate_model_profile(PROFILE, PROFILE_SHA)
        live = agg.verify_live_backend({**profile, 'pid': identity['pid']})
        frozen = {'manifest_sha256': digest, 'admission_sha256': admission_sha, 'result_sha256': result_sha,
                  'identity': identity, 'live_backend': live, 'status': 'BOUND_RESTORED_8B_NO_MODEL_CALL'}
        if latest_ref is not None:frozen['latest_restore']=latest_ref
        write_new(root / 'execution_manifest.json', frozen)
        return {'execution_manifest_sha256': sha(root / 'execution_manifest.json'), **frozen}


def generation_accounting(case, receipt):
    agg, _ = helpers()
    if sha(case / 'raw.jsonl') != receipt['raw_sha256']:
        raise ValueError('generation raw changed')
    integrity = agg.execution_integrity(case, receipt)
    if not integrity['passed']:
        raise ValueError('unbound model request accounting')
    disk = [json.loads(s) for s in (case / 'sampling_metadata.jsonl').read_text(encoding='utf8').splitlines()]
    canonical = lambda rows: sorted(json.dumps(e, sort_keys=True) for e in rows)
    if canonical(disk) != canonical(receipt['sampling_metadata']):
        raise ValueError('sampling log/receipt disagree')
    events = [json.loads(s) for s in (case / 'forward_ledger.jsonl').read_text().splitlines()] if (case / 'forward_ledger.jsonl').exists() else []
    metadata = {e['request_body_file']: e for e in receipt['sampling_metadata']}
    if len(metadata) != len(receipt['sampling_metadata']):
        raise ValueError('duplicate model request binding')
    forwarded = [e for e in events if e['event'] == 'forwarded']
    if not forwarded or len({e['request'] for e in forwarded}) != len(forwarded):
        raise ValueError('no unique actual forwarded requests')
    for event in forwarded:
        if event['request'] not in metadata or event['request_sha256'] != metadata[event['request']]['request_body_sha256']:
            raise ValueError('fake/unbound forwarded request')
    for entry in metadata.values():
        body = json.loads((case / 'model_request_bodies' / entry['request_body_file']).read_text(encoding='utf8'))
        if any(body.get(k) != entry.get(k) for k in ('model', 'seed', 'temperature', 'max_tokens', 'chat_template_kwargs')):
            raise ValueError('actual request body differs from metadata')
        if (entry['seed'], entry['model'], entry['max_tokens'], entry.get('chat_template_kwargs')) != (17, 'qwen3-8b-qual', 8192, {'enable_thinking': False}):
            raise ValueError('actual model payload differs')
    for name in metadata:
        sequence = [e['event'] for e in events if e['request'] == name]
        if not sequence or sequence[0] != 'attempt' or sequence.count('attempt') != 1 or sequence.count('forwarded') > 1:
            raise ValueError('invalid request lifecycle')
    combined = sum(receipt['post_content_lengths']) + receipt['response_wire_bytes']
    if integrity['counted_posts'] > CAPS['posts'] or not 0 <= combined <= CAPS['model_wire_bytes_combined']:
        raise ValueError('actual model budget exceeded')
    usage = agg.provider_usage(case, receipt)
    known_responses = len({e['request'] for e in usage['response_bindings']} - set(usage['unknown_usage_requests']))
    if not known_responses:
        usage['reported_tokens_known'] = None
    return {'actual_forwarded_posts': len(forwarded), 'request_attempts': integrity['counted_posts'],
            'reserved_request_body_bytes': sum(receipt['post_content_lengths']),
            'response_wire_bytes': receipt['response_wire_bytes'], 'provider_usage': usage,
            'reported_provider_tokens_known': usage['reported_tokens_known'] if known_responses else None,
            'monetary_cost': None, 'monetary_cost_status': 'UNKNOWN_NOT_PRICED',
            'request_errors': [e for e in events if e['event'] == 'error'],
            'forward_status_unknown': sorted(set(metadata) - {e['request'] for e in forwarded}), 'integrity': integrity}


def score_semantics(focus, regression, probe_exit, probe):
    def passed(record, count):
        return (record['exit'] == 0 and 'OK' in record['summary'] and
                any(re.fullmatch(r'Ran ' + str(count) + r' tests? in .+', s) for s in record['summary']))
    expected = {n: {'status': 'RETURNED', 'row_count': 0} for n in ('ManyToManyField', 'GenericForeignKey')}
    public_pass = probe_exit == 0 and probe.get('public_problem_results') == expected
    return {'f2p_passed': passed(focus, 1), 'ptp_passed': passed(regression, 13),
            'public_m2m_gfk_passed': public_pass,
            'fixed': passed(focus, 1) and passed(regression, 13) and public_pass}


def scoring_probe(out):
    source=regular(TASK/'scoring/public_issue_probe.py')
    expected=PINNED['scoring/public_issue_probe.py']
    if sha(source)!=expected:raise ValueError('frozen public probe changed')
    target=out/'public_issue_probe.py'
    with target.open('xb') as dest:dest.write(source.read_bytes())
    target.chmod(0o444)
    if sha(target)!=expected:raise ValueError('scoring probe copy changed')
    return target


def evaluate(root, manifest):
    agg, native = helpers()
    out = root / 'scoring'
    out.mkdir()
    candidate = out / 'candidate'
    agg.restore_candidate(root / 'episode/work', TASK / 'scoring/base_with_tests', candidate)
    started = time.monotonic()
    result = {}
    for name, key in (('focus', 'focus_labels'), ('regression', 'regression_labels')):
        write_new(out / (name + '_interface.json'), {'function': 'qualify_swe_contextbench_django_20261104.test',
            'module_sha256': sha(native.__file__), 'work': str(candidate), 'labels': manifest[key],
            'log': str(out / (name + '.log')), 'name': '34570-' + name, 'image': IMAGE, 'dependencies': str(DEPS)})
        result[name] = native.test(candidate, manifest[key], out / (name + '.log'), '34570-' + name)
    probe_path=scoring_probe(out)
    name = 'django34570-public-' + str(os.getpid())
    cmd = ['docker', 'run', '--name', name, '--rm', '--pull', 'never', '--network', 'none', '--read-only',
           '--cpus', '2', '--memory', '3g', '--pids-limit', '256', '--cap-drop', 'ALL', '--security-opt', 'no-new-privileges',
           '--tmpfs', '/tmp:rw,nosuid,size=128m', '-e', 'PYTHONPATH=/workspace:/extra', '-e', 'PYTHONDONTWRITEBYTECODE=1',
           '--mount', f'type=bind,src={candidate},dst=/workspace,readonly',
           '--mount', f'type=bind,src={DEPS},dst=/extra,readonly',
           '--mount', f'type=bind,src={probe_path},dst=/public_issue_probe.py,readonly',
           '--workdir', '/workspace', '--entrypoint', 'python3', IMAGE, '/public_issue_probe.py']
    write_new(out / 'public_probe_command.json', cmd)
    try:
        proc = subprocess.run(cmd, stdin=subprocess.DEVNULL, capture_output=True, timeout=240)
        code, stdout, stderr = proc.returncode, proc.stdout, proc.stderr
    except subprocess.TimeoutExpired as exc:
        subprocess.run(['docker', 'kill', name], capture_output=True, timeout=10)
        code, stdout, stderr = 124, exc.stdout or b'', exc.stderr or b''
    (out / 'public.stdout').write_bytes(stdout)
    (out / 'public.stderr').write_bytes(stderr)
    try:
        probe = json.loads(stdout)
    except (ValueError, UnicodeDecodeError):
        probe = {}
    result.update({'public_probe': {'exit': code, 'result': probe, 'stdout_sha256': sha(out / 'public.stdout'),
                                  'stderr_sha256': sha(out / 'public.stderr'),'probe_copy_sha256':sha(probe_path),'probe_copy_mode':oct(probe_path.stat().st_mode&0o777)},
                   'semantics': score_semantics(result['focus'], result['regression'], code, probe),
                   'wall_seconds': time.monotonic() - started, 'model_calls': 0,
                   'statistical_unit': 'one task, not fourteen independent samples',
                   'candidate_files': tree(candidate)})
    write_new(out / 'receipt.json', result)
    return result


def execute(root, digest):
    with queue_lock():
        frozen = read_checked(root / 'execution_manifest.json', digest)
        manifest = verify_prepared(root, frozen['manifest_sha256'])
        admission = read_checked(WINDOW / 'ADMISSION.json', frozen['admission_sha256'])
        result = read_checked(WINDOW / 'RESULT.json', frozen['result_sha256'])
        agg, _ = helpers()
        profile = agg.validate_model_profile(PROFILE, PROFILE_SHA)
        if 'latest_restore' in frozen:identity=verify_frozen_latest_restore(frozen)
        else:
            identity=process_identity(frozen['identity']['pid'])
            verify_restoration(profile,admission,result,identity)
        if identity != frozen['identity']:
            raise ValueError('runtime changed since manifest binding')
        agg.verify_live_backend({**profile, 'pid': identity['pid']})
        write_new(root / 'reservation.json', {'execution_manifest_sha256': digest, 'identity': identity,
                                             'caps': CAPS, 'mode': 'REAL_8B_NO_EXPERIENCE_DEVELOPMENT', 'outer_pid': os.getpid()})
        report = {'status': 'GENERATION_FAILED', 'generation': None, 'scoring': None,
                  'actual_forwarded_posts': None, 'tokens': None, 'monetary_cost': None, 'task_count': 1}
        started = time.monotonic()
        try:
            proc = subprocess.run([sys.executable, str(root / 'harness.py'), 'django__django-34570', 'no_skill'],
                                  stdin=subprocess.DEVNULL, capture_output=True, timeout=1320,
                                  env={**os.environ, 'DJANGO34570_EXECUTION_MANIFEST_SHA': digest})
            (root / 'runner.stdout').write_bytes(proc.stdout)
            (root / 'runner.stderr').write_bytes(proc.stderr)
            report['runner_exit'] = proc.returncode
            case = root / 'episode'
            if (case / 'receipt.json').is_file():
                receipt = json.loads((case / 'receipt.json').read_text())
                report['generation'] = {'agent_exit': receipt['agent_exit'], 'accounting': generation_accounting(case, receipt)}
                report['actual_forwarded_posts'] = report['generation']['accounting']['actual_forwarded_posts']
                report['tokens'] = report['generation']['accounting']['reported_provider_tokens_known']
                report['status'] = 'GENERATION_RECORDED'
        except Exception as exc:
            if isinstance(exc, subprocess.TimeoutExpired):
                (root / 'runner.stdout').write_bytes(exc.stdout or b'')
                (root / 'runner.stderr').write_bytes(exc.stderr or b'')
            report['generation_error'] = {'type': type(exc).__name__, 'message': str(exc)}
        finally:
            report['generation_wall_seconds'] = time.monotonic() - started
            # This separate CPU phase has no model transport and cannot make generation successful.
            try:
                report['scoring'] = evaluate(root, manifest)
            except Exception as exc:
                report['scoring_error'] = {'type': type(exc).__name__, 'message': str(exc)}
            write_new(root / 'result.json', report)
        return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage', choices=('prepare', 'bind-runtime', 'execute'))
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--manifest-sha')
    parser.add_argument('--admission-sha')
    parser.add_argument('--result-sha')
    parser.add_argument('--latest-restore-result',type=Path)
    parser.add_argument('--latest-restore-sha')
    args = parser.parse_args(argv)
    if (args.latest_restore_result is None)!=(args.latest_restore_sha is None):parser.error('latest restoration path and SHA are a pair')
    if args.stage!='bind-runtime' and args.latest_restore_result is not None:parser.error('latest restoration parameters are bind-runtime only')
    if args.stage != 'prepare' and not args.manifest_sha:
        parser.error('explicit manifest SHA required')
    if args.stage == 'prepare':
        result = prepare(args.root)
    elif args.stage == 'bind-runtime':
        if not args.admission_sha or not args.result_sha:
            parser.error('bind-runtime requires completed restoration receipt hashes')
        if args.latest_restore_result is None:result=bind_runtime(args.root,args.manifest_sha,args.admission_sha,args.result_sha)
        else:result=bind_runtime(args.root,args.manifest_sha,args.admission_sha,args.result_sha,latest_restore_path=args.latest_restore_result,latest_restore_sha=args.latest_restore_sha)
    else:
        result = execute(args.root, args.manifest_sha)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
