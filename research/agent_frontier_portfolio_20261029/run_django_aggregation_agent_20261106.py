#!/usr/bin/env python3
"""Private Django aggregation development episodes on a frozen 8B profile.

No network/model/DB operation occurs on import.  The source/target actor sees
only its frozen baseline, problem statement, isolated dependencies, model
bridge, and (source only) a separately owned PostgreSQL Unix socket.
"""
from __future__ import annotations

import argparse
import ast
from collections import Counter
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import subprocess
import sys
import tarfile
import time
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts.graph.research_auto_record import recorded_episode
from scripts.graph import research_actor_dependencies
from scripts.graph.research_tool_runtime import ripgrep_binding
import qualify_swe_contextbench_sympy_20261104 as shared
import run_swe_contextbench_sympy_20261104 as core
import run_swe_contextbench_requests_20261105 as requests_runner
from run_swe_contextbench_sphinx_20261105 import inspect_experience_reads

PRIVATE_ROOT = Path('/home/testuser/wzh/research_evidence/agent_learning_20261030')
QUAL = PRIVATE_ROOT / 'django_aggregation_qualification_20261106'
PARENT = PRIVATE_ROOT / 'django_aggregation_agent_20261106'
DATA = PRIVATE_ROOT / 'swe_contextbench_data_20261104'
QUAL_SHA = '46f67e61c87e2e3d118189fbce9ce45a9cbf105eb8440ff2eee6d43d67dd16cc'
SOURCE_IMAGE = 'sha256:648a1999badfe683239ec49e05b2a508e37f762213478122c58fa713f6c00f58'
CASES = {
    'source': ('django__django-12589', 'SWEContextBench_Lite_Experience.parquet',
               '895f28f9cbed817c00ab68770433170d83132d90', '3.8', 7201),
    'target': ('django__django-34176', 'SWEContextBench_Related_Lite.parquet',
               '016bead6a23989adec5c7ee6948db7ce2fc5e89b', '3.10', 7202),
}
PROJECTIONS = {
    'source': ('actor_source_v2', 'f76dc69ba650e61c49a81611392dabf15b65c5d67b7c8fc0ae03bac10c10c16c'),
    'target': ('actor_target', '196a1cfb4cb2d98fddb66ac56bed81ee90868b8e608fc15055b0e051f8a33efc'),
}
MAX_POSTS, MAX_SECONDS, MAX_BYTES = 48, 1200, 6_000_000
TEACHER_REPAIR_CONDITIONS = ('teacher_feedback_repair', 'teacher_joint_feedback_repair')
REPAIR_CONDITIONS = ('candidate_neutral_retry', 'candidate_feedback_retry', *TEACHER_REPAIR_CONDITIONS)
REPAIR_SOURCE = 'runtime_ready_8b_20261106'
REPAIR_DRAFT_SHA = 'cd2691418f8b5714539f4470d6e8126f21ca6da4f9007320bde09b18191abefd'
TEACHER_REPAIR_SOURCE = 'teacher_source_35b_20261106'
TEACHER_REPAIR_DRAFT_SHA = 'f009780d6105c1baff0f42cbfde8ef9b8148752595ea56113fe5faf2b7b24eee'
TEACHER_PROFILE_SHA = '2b0d9ed7d9bc4b763a697bfbb52e69c208217567d3089af7eb2f7ce5544e7294'
TEACHER_BROAD_RECEIPT_SHA = '2e58244265854ac2dacca9e4c0bca9850d93dcd7109e467717ea380737a8ebcc'
TEACHER_BROAD_LOG_SHA = 'ed69458dd7aa3629ae5f298338f1dcb7352490f7833ad6c8af2f092f2ed6e9da'


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def private_directory(path: Path, root: Path) -> Path:
    path, root = Path(path), Path(root)
    if not path.is_absolute() or not root.is_absolute() or path.is_symlink():
        raise ValueError('private path must be absolute and not a symlink')
    resolved = path.resolve()
    if not resolved.is_relative_to(root.resolve()) or not resolved.is_dir():
        raise ValueError('path is outside the declared private directory')
    return resolved


def attempt_root(parent: Path, attempt_id: str) -> Path:
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,63}', attempt_id):
        raise ValueError('invalid attempt identifier')
    return Path(parent) / 'attempts' / attempt_id


def prepare_actor_runtime(root: Path) -> Path:
    """The inherited harness mounts this empty, task-owned compatibility path."""
    runtime = root / 'runtime'
    if runtime.is_symlink() or (runtime.exists() and (not runtime.is_dir() or any(runtime.iterdir()))):
        raise ValueError('unexpected content in the empty actor runtime mount')
    runtime.mkdir(parents=True, exist_ok=True)
    return runtime


def validate_model_profile(path: Path, digest: str) -> dict:
    if path.is_symlink() or sha(path) != digest:
        raise ValueError('model profile missing or hash mismatch')
    p = json.loads(path.read_text(encoding='utf8'))
    keys = {'version', 'host', 'port', 'model_id', 'gguf_path', 'gguf_sha256',
            'context', 'output', 'pid', 'server_executable_sha256', 'thinking', 'ownership'}
    if set(p) != keys or (p['version'], p['host'], p['port'], p['model_id'], p['context'], p['output']) != (
            1, '127.0.0.1', 18104, 'qwen3-8b-qual', 32768, 8192):
        raise ValueError('unexpected model endpoint/profile')
    if p['ownership'] != 'research_django_aggregation_20261106' or p['thinking'] != 'default_template':
        raise ValueError('unrecognized research server ownership/thinking')
    if not isinstance(p['pid'], int) or p['pid'] <= 0 or not re.fullmatch(r'[0-9a-f]{64}', p['server_executable_sha256']):
        raise ValueError('invalid server identity')
    model = Path(p['gguf_path'])
    if not model.is_absolute() or model.is_symlink() or not model.is_file() or sha(model) != p['gguf_sha256']:
        raise ValueError('model weights changed')
    return p


def verify_server_argv(argv: list, profile: dict) -> None:
    expected = {'-m': profile['gguf_path'], '--host': profile['host'], '--port': str(profile['port']),
                '--alias': profile['model_id'], '-c': str(profile['context']), '-n': str(profile['output']), '-np': '1'}
    for flag, value in expected.items():
        if argv.count(flag) != 1 or argv.index(flag) + 1 >= len(argv) or argv[argv.index(flag)+1] != value:
            raise ValueError('live server command disagrees with profile: ' + flag)
    if argv.count('--no-context-shift') != 1: raise ValueError('live server permits context shifting')


def verify_live_backend(profile: dict) -> dict:
    proc = Path('/proc') / str(profile['pid'])
    argv = (proc / 'cmdline').read_bytes().decode('utf8').rstrip('\0').split('\0')
    verify_server_argv(argv, profile)
    binary_hash = sha(proc / 'exe')
    if binary_hash != profile['server_executable_sha256']: raise ValueError('live server executable changed')
    sockets = set()
    for fd in (proc / 'fd').iterdir():
        try:
            m = re.fullmatch(r'socket:\[([0-9]+)\]', os.readlink(fd))
            if m: sockets.add(m.group(1))
        except FileNotFoundError: pass
    port = f"{profile['port']:04X}"
    listeners = [line.split() for line in (proc / 'net/tcp').read_text().splitlines()[1:]]
    if not any(row[1] == '0100007F:' + port and row[3] == '0A' and row[9] in sockets for row in listeners):
        raise ValueError('profile process does not own expected loopback listener')
    return {'pid': profile['pid'], 'executable_sha256': binary_hash,
            'cmdline_sha256': hashlib.sha256((proc / 'cmdline').read_bytes()).hexdigest(),
            'owns_loopback_listener': True}


def verify_live_postgres(pg: dict) -> dict:
    proc = subprocess.run(['docker', 'inspect', pg['container_id']], capture_output=True, check=True, timeout=30)
    identity = json.loads(proc.stdout)[0]; host = identity['HostConfig']; cfg = identity['Config']
    matches = [m for m in identity['Mounts'] if m.get('Destination') == '/var/run/postgresql']
    if (identity['Id'] != pg['container_id'] or identity['Image'] != pg['image_id']
            or identity['Name'].lstrip('/') != pg['container_name'] or host['NetworkMode'] != 'none'
            or host.get('PortBindings') or host.get('PublishAllPorts') or not identity['State']['Running']
            or (cfg.get('Labels') or {}).get('jinrong.research.owner') != 'django_aggregation_20261106'
            or len(matches) != 1 or matches[0].get('Source') != pg['host_socket_dir']):
        raise ValueError('private postgres container identity/mount changed')
    return {'container_id': identity['Id'], 'image_id': identity['Image'], 'network': 'none',
            'host_ports': False, 'socket_mount_source': matches[0]['Source']}


def require_socket_manifest(path: Path, digest: str, parent: Path) -> dict:
    path = Path(path)
    if path.is_symlink() or not path.is_file() or sha(path) != digest:
        raise ValueError('socket manifest missing or changed')
    p = json.loads(path.read_text(encoding='utf8'))
    keys = {'version', 'container_name', 'container_id', 'image_id', 'host_socket_dir',
            'actor_socket_dir', 'database', 'user', 'network', 'host_ports'}
    if not keys.issubset(p) or p['version'] != 1 or p['network'] != 'none' or p['host_ports'] is not False:
        raise ValueError('invalid private postgres socket manifest')
    if (p['actor_socket_dir'], p['database'], p['user']) != ('/research-pg', 'research_probe', 'research_probe'):
        raise ValueError('unexpected private database identity')
    if not p['container_name'].startswith('research-django-aggregation-agent-20261106-') or p.get('owner') != 'django_aggregation_20261106':
        raise ValueError('postgres service is not task-owned')
    if not re.fullmatch(r'[a-f0-9]{12,64}', p['container_id']) or not re.fullmatch(r'sha256:[a-f0-9]{64}', p['image_id']):
        raise ValueError('invalid container identity')
    directory = private_directory(Path(p['host_socket_dir']), parent)
    if not re.fullmatch(r'pg_socket(?:_v[0-9]+)?', directory.name) or directory.parent != Path(parent).resolve():
        raise ValueError('socket must be in the task-specific socket directory')
    for item in directory.iterdir():
        if item.is_symlink() or item.name not in {'.s.PGSQL.5432', '.s.PGSQL.5432.lock'}:
            raise ValueError('unexpected socket directory content')
    socket = directory / '.s.PGSQL.5432'
    if not socket.exists() or not stat.S_ISSOCK(socket.stat().st_mode):
        raise ValueError('private postgres socket unavailable')
    return p


def actor_projection(path: Path, digest: str, task: str) -> dict:
    name, expected = PROJECTIONS[task]
    if path.is_symlink() or path.resolve() != (PARENT / name).resolve() or digest != expected:
        raise ValueError('unexpected actor projection')
    result = research_actor_dependencies.verify_projection(path, digest)
    manifest = json.loads((path / 'manifest.json').read_text())
    if manifest.get('python') != CASES[task][3] or 'django' not in manifest.get('blocked_packages', []):
        raise ValueError('projection Python or blocked package mismatch')
    expected_sites = {'default', 'pgdriver'} if task == 'source' else {'default'}
    if set(result['sites']) != expected_sites:
        raise ValueError('unexpected actor site set')
    return result


def rebind_model(code: str, profile: dict) -> str:
    old = "socket.create_connection(('127.0.0.1',8004),timeout=30)"
    code = core.replace_once(code, old, f"socket.create_connection(({profile['host']!r},{profile['port']}),timeout=30)")
    if code.count('qwen3.6-35b-a3b') < 2 or 'Qwen3.6-35B-A3B' not in code:
        raise ValueError('model alias fragments missing')
    return code.replace('Qwen3.6-35B-A3B', profile['model_id']).replace('qwen3.6-35b-a3b', profile['model_id'])


def validate_backend_choice(backend: str, task: str, condition: str) -> None:
    if backend not in ('student8b', 'teacher35b'):
        raise ValueError('unknown model backend')
    if backend == 'teacher35b' and (task != 'source' or condition not in ('none',*TEACHER_REPAIR_CONDITIONS)):
        raise ValueError('teacher profile permitted only for source and its approved feedback repair')
    if backend == 'student8b' and condition in TEACHER_REPAIR_CONDITIONS:
        raise ValueError('teacher feedback repair requires teacher backend')


def set_model_limits(code: str, profile: dict, backend: str) -> str:
    old="'limit':{'context':32768,'output':8192}"
    if backend == 'student8b':
        if (profile['context'],profile['output']) != (32768,8192):raise ValueError('student limits changed')
        return code
    if (profile['context'],profile['output']) != (65536,16384):raise ValueError('teacher limits changed')
    code=core.replace_once(code,old,"'limit':{'context':65536,'output':16384}")
    return core.replace_once(code,"'timeout':300000","'timeout':900000")


def clean_root(task: str) -> Path:
    return QUAL / ('sqlite_' + task) / 'clean'


def verify_clean_archive(task: str, case: dict) -> None:
    root = clean_root(task); archive = QUAL / (task + '.tar.gz')
    if root.is_symlink() or not root.is_dir() or sha(archive) != case['archive_sha256']:
        raise ValueError('frozen baseline unavailable')
    expected, skipped = {}, []
    with tarfile.open(archive, 'r:gz') as tf:
        for item in tf:
            p = PurePosixPath(item.name)
            if not p.parts or p.parts[0] != 'django-' + case['base'] or p.is_absolute() or '..' in p.parts:
                raise ValueError('unsafe source archive')
            if item.issym():
                skipped.append(item.name); continue
            if item.isdir(): continue
            if not item.isfile(): raise ValueError('unexpected archive entry')
            with tf.extractfile(item) as stream:
                expected[PurePosixPath(*p.parts[1:]).as_posix()] = hashlib.sha256(stream.read()).hexdigest()
    actual = {p.relative_to(root).as_posix(): sha(p) for p in root.rglob('*') if p.is_file()}
    if actual != expected or sorted(skipped) != sorted(case['omitted_symlinks']) or (root / '.git').exists():
        raise ValueError('baseline differs from qualified archive')
    if any(p.is_symlink() for p in root.rglob('*')):
        raise ValueError('baseline has a symlink')


def row_for(task: str, *, include_reference: bool = False) -> dict:
    import pyarrow.parquet as pq
    identity, file, rev, _, _ = CASES[task]
    cols = ['instance_id', 'base_commit', 'problem_statement']
    if include_reference: cols += ['test_patch']
    rows = [r for r in pq.read_table(DATA / file, columns=cols).to_pylist() if r['instance_id'] == identity]
    if len(rows) != 1 or rows[0]['base_commit'] != rev:
        raise ValueError('dataset instance/revision mismatch')
    return rows[0]


def qualification(task: str) -> dict:
    shared.checked_dataset()
    path = QUAL / 'sqlite_receipt.json'
    if sha(path) != QUAL_SHA: raise ValueError('qualification receipt changed')
    c = json.loads(path.read_text())['cases'][task]
    if (c['id'], c['base']) != CASES[task][:1] + CASES[task][2:3]:
        raise ValueError('qualification identity changed')
    for arm in ('base', 'gold'):
        a = c['arms'][arm]
        if a['focus']['exit'] != (1 if arm == 'base' else 0) or a['regression']['exit'] != 0:
            raise ValueError('qualification controls failed')
        for metric in ('focus', 'regression'):
            if sha(QUAL / ('sqlite_' + task) / (arm + '_' + metric + '.log')) != a[metric]['sha256']:
                raise ValueError('qualification log changed')
    verify_clean_archive(task, c)
    return c


def restore_candidate(work: Path, clean: Path, output: Path) -> None:
    if output.exists() or output.is_symlink(): raise FileExistsError('preserve prior evaluation')
    if any(p.is_symlink() for p in work.rglob('*')): raise ValueError('candidate symlink requires review')
    shutil.copytree(work, output, ignore=shutil.ignore_patterns('.git', '__pycache__', '.pytest_cache',
                    'instructions.txt', 'opencode.json', 'source_experience.md'))
    if (output / 'tests').exists(): shutil.rmtree(output / 'tests')
    shutil.copytree(clean / 'tests', output / 'tests')
    for p in output.rglob('conftest.py'):
        if not (clean / p.relative_to(output)).is_file(): p.unlink()
    for p in clean.rglob('conftest.py'):
        target = output / p.relative_to(clean)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p, target)
    for rel in ('conftest.py', 'pytest.ini', 'pyproject.toml', 'setup.cfg', 'tox.ini'):
        old, dest = clean / rel, output / rel
        if old.is_file(): shutil.copy2(old, dest)
        elif dest.exists(): dest.unlink()


def repair_tree(root: Path) -> dict:
    if root.is_symlink() or not root.is_dir(): raise ValueError('candidate directory invalid')
    result = {}
    for p in root.rglob('*'):
        if p.is_symlink(): raise ValueError('candidate symlink rejected')
        if not p.is_file(): continue
        rel = p.relative_to(root)
        if any(part in ('.git', '__pycache__', '.pytest_cache') for part in rel.parts): continue
        if len(rel.parts) == 1 and rel.name in ('instructions.txt', 'opencode.json', 'source_experience.md'): continue
        result[rel.as_posix()] = sha(p)
    return result


def freeze_repair_candidate(work: Path, snapshot: Path, manifest: Path, draft_sha: str) -> dict:
    expected = repair_tree(work)
    if snapshot.exists() != manifest.exists(): raise ValueError('incomplete frozen candidate; do not overwrite')
    if not snapshot.exists():
        def ignore(path, names):
            blocked = {'.git', '__pycache__', '.pytest_cache'} & set(names)
            if Path(path) == work: blocked |= {'instructions.txt', 'opencode.json', 'source_experience.md'} & set(names)
            return blocked
        shutil.copytree(work, snapshot, ignore=ignore)
        data = {'source_draft_sha256': draft_sha, 'files': expected,
                'scope': 'source candidate only; no post-run evaluator copy or hidden test patch'}
        if repair_tree(snapshot) != expected: raise ValueError('candidate snapshot changed during copy')
        with manifest.open('x', encoding='utf8') as f:json.dump(data, f, indent=2);f.write('\n')
    data = json.loads(manifest.read_text(encoding='utf8'))
    if data.get('source_draft_sha256') != draft_sha or data.get('files') != expected or repair_tree(snapshot) != expected:
        raise ValueError('frozen candidate or source work changed')
    return data


def error_summary(log: str) -> list:
    matched=[]
    for line in log.splitlines():
        if (re.fullmatch(r'[A-Za-z_][A-Za-z0-9_.]*(?:Error|Exception): .{0,240}', line)
                or re.fullmatch(r'FAILED \([^\n]{1,120}\)', line)
                or re.fullmatch(r'Ran [0-9]+ tests? in .+', line)) and line not in matched:
            matched.append(line)
    return matched[-6:]


def application_frames(log: str) -> list:
    lines=log.splitlines(); frames=[]
    for i,line in enumerate(lines):
        if re.fullmatch(r'\s*File "/workspace/django/[A-Za-z0-9_./-]+\.py", line [0-9]+, in [^\n]{1,120}', line):
            code=lines[i+1].strip()[:240] if i+1<len(lines) and lines[i+1].startswith('    ') else ''
            frame=line.strip()+(('\n    '+code) if code else '')
            if frame not in frames:frames.append(frame)
    return frames[-2:]


def repair_feedback(record: dict, case: Path) -> str:
    feedback=record['post_run_evaluation']; items=[]
    for name in ('focus','regression','issue_probe'):
        metric=feedback[name]; log=(case/'post_run_evaluation_restored_tests'/(name+'.log')).read_text(encoding='utf8',errors='replace')
        items.append({'check':name,'exit':metric['exit'],'requested':metric['nodes_requested'],
                      'observed':error_summary(log),'application_frames':application_frames(log)})
    text='Independent source evaluation feedback (observed results only):\n'+json.dumps(items,ensure_ascii=True,indent=2)
    if any(s in text.lower() for s in ('django__django-34176','/pull/34176','/issues/34176','#34176')):
        raise ValueError('feedback contains target identity')
    return text


def teacher_public_feedback(receipt: Path, log: Path, clean: Path,
                            receipt_sha: str = TEACHER_BROAD_RECEIPT_SHA,
                            log_sha: str = TEACHER_BROAD_LOG_SHA) -> tuple[str, dict]:
    """Copy only the failure of an independently verified existing public test."""
    if sha(receipt) != receipt_sha or sha(log) != log_sha: raise ValueError('broader regression receipt or log changed')
    data=json.loads(receipt.read_text(encoding='utf8')); teacher=data['results']['teacher']
    if teacher['exit'] != 1 or teacher['log_sha256'] != log_sha:raise ValueError('broader regression does not bind teacher failure')
    test_file=clean/'tests/aggregation/tests.py';source=test_file.read_text(encoding='utf8')
    module=ast.parse(source)
    classes=[n for n in module.body if isinstance(n,ast.ClassDef) and n.name=='AggregateTestCase']
    methods=[n for n in classes[0].body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))
             and n.name=='test_aggregation_subquery_annotation'] if len(classes)==1 else []
    if len(methods)!=1:raise ValueError('reported test is absent from clean public source')
    method=ast.get_source_segment(source,methods[0])
    if "self.assertEqual(ctx[0]['sql'].count('SELECT'), 2)" not in method:
        raise ValueError('clean public test lacks the observed SELECT-count assertion')
    text=log.read_text(encoding='utf8')
    marker='FAIL: test_aggregation_subquery_annotation (aggregation.tests.AggregateTestCase)'
    end='AssertionError: 3 != 2'
    if text.count(marker)!=1 or text.count(end)!=1 or text.count('\nFAIL:')>1 or 'FAILED (failures=1, skipped=1)' not in text:
        raise ValueError('broader regression failure does not match expected public test')
    start=text.index(marker); stop=text.index(end,start)+len(end)
    failure=text[start:stop]
    if any(s in failure.lower() for s in ('django__django-34176','/pull/34176','/issues/34176','#34176')):
        raise ValueError('feedback contains target identity')
    feedback=('Independent regression feedback for a test already present in the public source checkout; '
              '219 tests ran, one failed and one was skipped.\n'+failure)
    binding={'broader_receipt_sha256':receipt_sha,'teacher_log_sha256':log_sha,
             'public_test_file_sha256':sha(test_file),
             'public_test_method_sha256':hashlib.sha256(method.encode('utf8')).hexdigest(),
             'test':'aggregation.tests.AggregateTestCase.test_aggregation_subquery_annotation'}
    return feedback,binding


def joint_source_validation_feedback(record: dict) -> str:
    checks=record['post_run_evaluation']; issue=checks['issue_probe'].get('observed',{})
    if (checks['focus']['exit'] != 0 or checks['regression']['exit'] != 0
            or issue.get('exception') is not None or issue.get('expected_data') is not True):
        raise ValueError('parent did not pass the source checks being preserved')
    observed={'focus':checks['focus']['summary'],'regression':checks['regression']['summary'],
              'original_issue':{'exception':None,'expected_data':True}}
    return ('Joint validation requirement: preserve the original issue repair AND the existing regression behavior. '
            'Fixing only the reported regression while reintroducing the original issue is not a completed repair. '
            'The parent implementation passed these independently observed source checks:\n'
            +json.dumps(observed,ensure_ascii=True,indent=2))


def repair_prompt(task: str, condition: str, feedback: str) -> str:
    if condition not in REPAIR_CONDITIONS: raise ValueError('not a source repair condition')
    common=task.rstrip()+'\n\nContinue from the current implementation. Inspect and run relevant local tests yourself; '
    common+='complete the repair without asking for permission. Do not assume the current implementation is correct.'
    common+=' The file /root/instructions.txt is a read-only issue specification, not executable project source; do not edit it or change its permissions.'
    common+=' Writable Django project source is under /root/django/. Inspect and modify the relevant project files; a permission error on the specification does not mean the source is read-only.'
    common+=' Evaluation paths beginning /workspace/ refer to the same repository-relative paths under /root/ in this actor. Apply this path mapping when inspecting diagnostic frames.'
    return common + ('\n\n'+feedback if condition in ('candidate_feedback_retry',*TEACHER_REPAIR_CONDITIONS) else '')


def derive(root: Path, task: str, condition: str, experience: Path | None,
           actor: dict, profile: dict, task_file: Path, pg: dict | None, candidate: Path | None = None,
           backend: str = 'student8b') -> str:
    validate_backend_choice(backend, task, condition)
    protocol = SimpleNamespace(OUT=QUAL, SITE=Path(actor['sites']['default']), LEGACY=Path(actor['runtime']))
    base_condition = 'none' if condition in REPAIR_CONDITIONS else condition
    code = requests_runner.derive(root, task, base_condition, experience, protocol=protocol, seed=CASES[task][4])
    if condition in REPAIR_CONDITIONS:
        if task != 'source' or candidate is None or experience is not None: raise ValueError('invalid repair inputs')
        old = str(root / f'{task}__none__seed{CASES[task][4]}')
        new = str(root / f'{task}__{condition}__seed{CASES[task][4]}')
        code = core.replace_once(code, old, new)
    code = rebind_model(code, profile)
    code = set_model_limits(code, profile, backend)
    code = core.replace_once(code, "before_temperature,before_seed=payload.get('temperature'),payload.get('seed')",
        "before_temperature,before_seed=payload.get('temperature'),payload.get('seed')\n payload['model']=" + repr(profile['model_id']))
    code = core.replace_once(code, "shutil.copytree(src/'clean_base',work,dirs_exist_ok=True)",
        f"shutil.copytree(Path({str(candidate if candidate else clean_root(task))!r}),work,dirs_exist_ok=True)")
    code = core.replace_once(code, "(src/'task.txt').read_text(encoding='utf8').strip()",
        f"Path({str(task_file)!r}).read_text(encoding='utf8').strip()")
    code = core.replace_once(code, "'--entrypoint','python3'", "'--entrypoint','/extra/bin/python'")
    code = core.replace_once(code, 'Use the checked-out repository and local Python dependencies; network access is unavailable.',
        'Use the checked-out repository and isolated Python dependencies; network access is unavailable.' +
        (' PostgreSQL is available only via PGHOST=/research-pg, PGUSER=research_probe, PGDATABASE=research_probe.' if pg else ''))
    code = core.replace_once(code, 'calls=[]; payload_bytes=[]; sampling=[];',
        'calls=[]; payload_bytes=[]; sampling=[]; post_lock=threading.Lock(); post_count=[0];')
    line = "  line=first.split(b'\\r\\n',1)[0].rsplit(b' ',1)[0]"
    guard = line + "\n  if line.startswith(b'POST'):\n   with post_lock:\n    if post_count[0]>=48:\n     calls.append('DENIED_POST_LIMIT');self.request.sendall(b'HTTP/1.1 403 Forbidden\\r\\nContent-Length: 0\\r\\nConnection: close\\r\\n\\r\\n');return\n    post_count[0]+=1"
    code = core.replace_once(code, line, guard)
    code = core.replace_once(code, 'line not in allowed or len(calls)>=24 or ', 'line not in allowed or ')
    code = core.replace_once(code, 'timeout=900)', f'timeout={MAX_SECONDS})')
    extra = ripgrep_binding()
    if backend == 'teacher35b':
        instruction_file = root / f'{task}__{condition}__seed{CASES[task][4]}' / 'work/instructions.txt'
        extra += ['--mount', f'type=bind,src={instruction_file},dst=/root/instructions.txt,readonly']
    if pg:
        extra += ['--mount', f"type=bind,src={pg['host_socket_dir']},dst=/research-pg,readonly",
                  '--mount', f"type=bind,src={actor['sites']['pgdriver']},dst=/pgdriver,readonly",
                  '-e', 'PGHOST=/research-pg', '-e', 'PGUSER=research_probe', '-e', 'PGDATABASE=research_probe']
        code = core.replace_once(code, "'-e','PYTHONPATH=/deps'", "'-e','PYTHONPATH=/deps:/pgdriver'")
    code = core.replace_once(code, 'cmd[_at:_at]=[', 'cmd[_at:_at]=' + repr(extra) + '+[')
    compile(code, '<django-aggregation-harness>', 'exec')
    return code


def adapt_source_probe(data: str, eval_db: str) -> str:
    """Keep the original issue's SQL/expected values byte-identical."""
    if not re.fullmatch(r'research_eval_[0-9a-f]{16}', eval_db): raise ValueError('invalid evaluation DB')
    adapted = core.replace_once(data, 'password=pathlib.Path("/run/research_secret").read_text().strip()', 'password=""')
    adapted = core.replace_once(adapted, '"HOST":"research-django-aggregation-20261106-db"', '"HOST":"/research-pg"')
    adapted = core.replace_once(adapted, '"NAME":"research_probe"', '"NAME":' + repr(eval_db))
    restored = adapted.replace('password=""', 'password=pathlib.Path("/run/research_secret").read_text().strip()', 1)
    restored = restored.replace('"HOST":"/research-pg"', '"HOST":"research-django-aggregation-20261106-db"', 1)
    restored = restored.replace('"NAME":' + repr(eval_db), '"NAME":"research_probe"', 1)
    if restored != data: raise ValueError('probe changed beyond isolation adaptation')
    return adapted


def run_evaluator(task: str, case: Path, control: dict, actor: dict, pg: dict | None) -> dict:
    """Apply the frozen test patch only after actor exit, to a restored copy."""
    work, out = case / 'work', case / 'post_run_evaluation_restored_tests'
    out.mkdir()
    copy = out / 'candidate'
    restore_candidate(work, clean_root(task), copy)
    reference = row_for(task, include_reference=True)['test_patch'].encode('utf8')
    if hashlib.sha256(reference).hexdigest() != control['arms']['base']['patches'][0]['sha256']:
        raise ValueError('frozen test patch mismatch')
    patch = out / 'test.patch'; patch.write_bytes(reference)
    steps = []
    for arguments in (['git', 'apply', '--check', str(patch)], ['git', 'apply', str(patch)]):
        proc = subprocess.run(arguments, cwd=copy, capture_output=True, timeout=30)
        steps.append({'exit': proc.returncode, 'stderr': proc.stderr.decode(errors='replace')[-2000:]})
        if proc.returncode: break
    result = {'status': 'TEST_PATCH_CONFLICT', 'patch_sha256': sha(patch), 'patch_steps': steps,
              'regression_scope': 'qualification-mapped SQLite subset; see qualification receipt'}
    if len(steps) != 2 or any(s['exit'] for s in steps): return result
    base = ['docker', 'run', '--rm', '--pull', 'never', '--network', 'none', '--read-only',
            '--cpus', '2', '--memory', '3g', '--pids-limit', '256', '--cap-drop', 'ALL',
            '--security-opt', 'no-new-privileges', '--tmpfs', '/tmp:rw,nosuid,size=256m',
            '-e', 'HOME=/tmp', '-e', 'PYTHONDONTWRITEBYTECODE=1',
            '--mount', f'type=bind,src={copy},dst=/workspace,readonly',
            '--mount', f"type=bind,src={actor['runtime']},dst=/extra,readonly",
            '--mount', f"type=bind,src={actor['sites']['default']},dst=/deps,readonly",
            '--workdir', '/workspace', '--entrypoint', '/extra/bin/python']
    def execute(name: str, command: list, nodes: int) -> dict:
        start = time.monotonic()
        try:
            p = subprocess.run(command, capture_output=True, timeout=300)
            exit_code, data = p.returncode, p.stdout + p.stderr
        except subprocess.TimeoutExpired as exc:
            exit_code, data = 124, (exc.stdout or b'') + (exc.stderr or b'')
        log = out / (name + '.log'); log.write_bytes(data)
        lines = data.decode(errors='replace').splitlines()
        return {'exit': exit_code, 'nodes_requested': nodes, 'log_sha256': sha(log),
                'seconds': round(time.monotonic()-start, 3),
                'summary': [s for s in lines if s.startswith(('Ran ', 'FAILED', 'OK'))][-4:]}
    for metric in ('focus', 'regression'):
        labels = control[metric + '_labels']
        cmd = base + ['-e', 'PYTHONPATH=/workspace:/deps', SOURCE_IMAGE,
                      'tests/runtests.py', '--settings=test_sqlite', '--parallel=1', '--verbosity=1', *labels]
        result[metric] = execute(metric, cmd, len(labels))
    # Probe scripts are D-side data, mounted only here, never to the actor.
    probe_root = QUAL / 'issue_probe'
    name = 'source_issue_probe.py' if task == 'source' else 'target_issue_probe.py'
    original = probe_root / name
    expected = ('bad04113610b05e9946274a967aeb2b6fb7487ac45dfd96e7683c8d3284d209d'
                if task == 'source' else '01725a6a639f6e818aac7aca7fc33ef51ac250013a96df674a09f5b72b7984ea')
    if sha(original) != expected: raise ValueError('original issue probe changed')
    model_path = probe_root / ('probeapp' if task == 'source' else 'targetprobe') / 'models.py'
    model_hash = ('f9381e2204cf9b2ea2f6c909d023f0acc6db7795d94ee2b7ff2c1cbcec1d9f61'
                  if task == 'source' else '427bf4116859d22903e823c2abe251250fa21dc6da2ca35f1bda94e3334a63e4')
    if sha(model_path) != model_hash: raise ValueError('original probe models changed')
    data = original.read_text(encoding='utf8')
    eval_db = None
    if task == 'source':
        eval_db = 'research_eval_' + hashlib.sha256(str(case).encode()).hexdigest()[:16]
        data = adapt_source_probe(data, eval_db)
    probe = out / 'issue_probe.py'; probe.write_text(data, encoding='utf8')
    cmd = base + ['--mount', f'type=bind,src={probe_root},dst=/probe,readonly',
                  '--mount', f'type=bind,src={probe},dst=/issue_probe.py,readonly']
    pythonpath = '/workspace:/probe:/deps'
    if pg:
        cmd += ['--mount', f"type=bind,src={pg['host_socket_dir']},dst=/research-pg,readonly",
                '--mount', f"type=bind,src={actor['sites']['pgdriver']},dst=/pgdriver,readonly"]
        pythonpath += ':/pgdriver'
    cmd += ['-e', 'PYTHONPATH=' + pythonpath, SOURCE_IMAGE, '/issue_probe.py']
    if pg:
        verify_live_postgres(pg)
        psql = ['docker', 'exec', pg['container_id'], 'psql', '-X', '-v', 'ON_ERROR_STOP=1', '-U', 'research_probe', '-d', 'postgres', '-c']
        create = subprocess.run(psql + [f'CREATE DATABASE {eval_db}'], capture_output=True, timeout=30)
        if create.returncode: raise RuntimeError('private evaluation database creation failed')
        try:
            result['issue_probe'] = execute('issue_probe', cmd, 1)
        finally:
            drop = subprocess.run(psql + [f'DROP DATABASE {eval_db} WITH (FORCE)'], capture_output=True, timeout=30)
            (out / 'database_lifecycle.json').write_text(json.dumps({'database': eval_db, 'created_after_actor': True,
                    'container_id': pg['container_id'], 'create_exit': create.returncode, 'drop_exit': drop.returncode}) + '\n')
            if drop.returncode: raise RuntimeError('private evaluation database cleanup failed')
        result['issue_probe']['database_lifecycle_sha256'] = sha(out / 'database_lifecycle.json')
    else:
        result['issue_probe'] = execute('issue_probe', cmd, 1)
    lines = (out / 'issue_probe.log').read_text(encoding='utf8', errors='replace').splitlines()
    observed = []
    for line in lines:
        try: observed.append(json.loads(line))
        except ValueError: pass
    result['issue_probe']['observed'] = observed[-1] if observed else None
    result['issue_probe']['original_sha256'] = expected
    result['issue_probe']['original_models_sha256'] = model_hash
    result['issue_probe']['adapted_sha256'] = sha(probe)
    result['status'] = 'EVALUATED'
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--attempt-id', required=True)
    parser.add_argument('--task', choices=('source', 'target'), required=True)
    parser.add_argument('--condition', choices=('none', 'source_history', 'generated_skill', 'feedback_card', *REPAIR_CONDITIONS), default='none')
    parser.add_argument('--experience', type=Path)
    parser.add_argument('--experience-sha256')
    parser.add_argument('--repair-source-attempt-id')
    parser.add_argument('--repair-draft-dir', type=Path)
    parser.add_argument('--repair-draft-sha256')
    parser.add_argument('--backend', choices=('student8b','teacher35b'), default='student8b')
    parser.add_argument('--model-profile', type=Path, required=True)
    parser.add_argument('--model-profile-sha256', required=True)
    parser.add_argument('--actor-projection', type=Path, required=True)
    parser.add_argument('--actor-manifest-sha256', required=True)
    parser.add_argument('--pg-socket-manifest', type=Path)
    parser.add_argument('--pg-socket-sha256')
    parser.add_argument('--preflight-only', action='store_true')
    args = parser.parse_args()
    root = attempt_root(PARENT, args.attempt_id)
    validate_backend_choice(args.backend, args.task, args.condition)
    is_repair = args.condition in REPAIR_CONDITIONS
    if args.task != 'source' and is_repair: parser.error('repair conditions are source-only')
    if args.task == 'source' and args.condition not in ('none', *REPAIR_CONDITIONS): parser.error('unsupported source condition')
    if (args.condition in ('none', *REPAIR_CONDITIONS)) != (args.experience is None) or ((args.experience is None) != (args.experience_sha256 is None)):
        parser.error('experience and hash must both be supplied for experience arms')
    if args.condition != 'none' and not is_repair:
        # No ad-hoc experience or unbound skill: the freeze/build interface is intentionally gated.
        raise ValueError('source experience freeze interface not yet implemented; no experience arms released')
    repair_args = (args.repair_source_attempt_id, args.repair_draft_dir, args.repair_draft_sha256)
    if is_repair and any(x is None for x in repair_args): parser.error('repair source, draft directory and hash required')
    if not is_repair and any(x is not None for x in repair_args): parser.error('repair arguments require a repair condition')
    if (args.pg_socket_manifest is None) != (args.pg_socket_sha256 is None): parser.error('socket manifest and hash required together')
    if args.task == 'source' and args.pg_socket_manifest is None: parser.error('source requires private PostgreSQL socket')
    if args.task == 'target' and args.pg_socket_manifest is not None: parser.error('target must not receive PostgreSQL socket')
    if args.backend == 'teacher35b':
        from scripts.graph import research_teacher_backend as teacher_backend
        profile = teacher_backend.validate_model_profile(args.model_profile, args.model_profile_sha256)
        backend = teacher_backend.verify_live_backend(profile)
    else:
        profile = validate_model_profile(args.model_profile, args.model_profile_sha256)
        backend = verify_live_backend(profile)
    actor = actor_projection(args.actor_projection, args.actor_manifest_sha256, args.task)
    pg = require_socket_manifest(args.pg_socket_manifest, args.pg_socket_sha256, PARENT) if args.pg_socket_manifest else None
    live_pg = verify_live_postgres(pg) if pg else None
    if sha(core.BASE) != core.BASE_SHA: raise ValueError('base harness changed')
    control = qualification(args.task)
    row = row_for(args.task)
    task_text = row['problem_statement'].replace('\r\n', '\n').rstrip() + '\n'
    if args.backend == 'teacher35b':
        task_text = task_text.rstrip() + ('\n\nEnvironment: The instructions at /root/instructions.txt are read-only; '
            'repository code under /root/django is writable. You may inspect files and run relevant local tests '
            'without asking the user for permission.\n')
    candidate = None; repair = None
    if is_repair:
        is_teacher_repair = args.condition in TEACHER_REPAIR_CONDITIONS
        repair_source_id = TEACHER_REPAIR_SOURCE if is_teacher_repair else REPAIR_SOURCE
        repair_draft_digest = TEACHER_REPAIR_DRAFT_SHA if is_teacher_repair else REPAIR_DRAFT_SHA
        if args.repair_source_attempt_id != repair_source_id or args.repair_draft_sha256 != repair_draft_digest:
            raise ValueError('unrecognized repair source or draft')
        if is_teacher_repair and args.model_profile_sha256 != TEACHER_PROFILE_SHA:
            raise ValueError('teacher repair must use the source teacher profile')
        source = attempt_root(PARENT, args.repair_source_attempt_id)
        draft_dir = source / ('source_experience_teacher_v1' if is_teacher_repair else 'source_experience_draft_v1')
        if args.repair_draft_dir.is_symlink() or args.repair_draft_dir.resolve() != draft_dir.resolve():
            raise ValueError('draft directory differs from source-bound draft')
        if sha(draft_dir / 'draft_manifest.json') != repair_draft_digest: raise ValueError('repair draft hash changed')
        import prepare_django_aggregation_experience_20261106 as experience_helper
        draft = experience_helper.validate_draft(source, clean_root('source'), draft_dir)
        started = json.loads((source/'source__none__seed7201.started.json').read_text(encoding='utf8'))
        if (draft['source']['model_profile_sha256'] != args.model_profile_sha256
                or draft['source']['projection_sha256'] != args.actor_manifest_sha256
                or started.get('backend_kind','student8b') != args.backend
                or sha(source/'source__none__seed7201.task.txt') != hashlib.sha256(task_text.encode()).hexdigest()):
            raise ValueError('repair model/projection/task differs from source')
        old_case=source/'source__none__seed7201';record=json.loads((source/'source__none__seed7201.completed.json').read_text())
        if is_teacher_repair:
            broad=PARENT/'teacher_broader_regression_20261106_v1'
            feedback,broad_binding=teacher_public_feedback(broad/'receipt.json',broad/'teacher.log',clean_root('source'))
            source_diff=experience_helper.decode_patch((draft_dir/'feedback_card.md').read_text(encoding='utf8'))
            broad_binding['observed_source_diff_sha256']=hashlib.sha256(source_diff).hexdigest()
            feedback=('Observed parent-agent edits against the source baseline, not a reference repair:\n'
                      +source_diff.decode('utf8',errors='replace')+'\n'+feedback)
            if args.condition == 'teacher_joint_feedback_repair':
                feedback+='\n\n'+joint_source_validation_feedback(record)
            broad_binding['joint_validation']=args.condition == 'teacher_joint_feedback_repair'
            candidate=source/'teacher_repair_candidate_frozen_v1'; manifest=source/'teacher_repair_candidate_frozen_v1.json'
        else:
            feedback=repair_feedback(record,old_case);broad_binding=None
            candidate=source/'repair_candidate_frozen_v1'; manifest=source/'repair_candidate_frozen_v1.json'
        freeze_repair_candidate(old_case/'work',candidate,manifest,repair_draft_digest)
        task_text=repair_prompt(task_text,args.condition,feedback)+'\n'
        repair={'source_completion_sha256':draft['source']['completion_sha256'],'draft_sha256':repair_draft_digest,
                'candidate_manifest_sha256':sha(manifest),'feedback_sha256':hashlib.sha256(feedback.encode()).hexdigest()
                    if args.condition in ('candidate_feedback_retry',*TEACHER_REPAIR_CONDITIONS) else None,
                'public_regression':broad_binding,
                'scope':'source candidate continuation; not target confirmation',
                'database_reset':'operator must reset only the manifest-bound private research_probe before each arm'}
    eid = f'{args.task}__{args.condition}__seed{CASES[args.task][4]}'
    case = root / eid
    task_file = root / (eid + '.task.txt')
    harness = root / (eid + '.harness.py')
    if any(p.exists() or p.is_symlink() for p in (case, task_file, harness, root / (eid + '.started.json'),
            root / (eid + '.completed.json'), root / (eid + '.auto_reservation.json'))):
        raise FileExistsError('episode already exists; never overwrite or auto-retry')
    # derive compiles without launching the model; the actor receives only task_text and frozen baseline.
    code = derive(root, args.task, args.condition, args.experience, actor, profile, task_file, pg, candidate, args.backend)
    if args.preflight_only:
        print(json.dumps({'status': 'PREFLIGHT_ONLY', 'episode': eid, 'task_sha256': hashlib.sha256(task_text.encode()).hexdigest(),
                          'harness_sha256': hashlib.sha256(code.encode()).hexdigest(),
                          'model_profile_sha256': args.model_profile_sha256, 'projection_sha256': args.actor_manifest_sha256,
                          'socket_sha256': args.pg_socket_sha256, 'backend': backend, 'postgres': live_pg,
                          'backend_kind': args.backend,
                          'repair': repair, 'model_calls': 0}))
        return
    prepare_actor_runtime(root)
    @recorded_episode(root, CASES[args.task][4])
    def run(task: str, condition: str) -> None:
        task_file.write_text(task_text, encoding='utf8')
        harness.write_text(code, encoding='utf8')
        components = {'outer_runner.py': Path(__file__), 'core.py': Path(core.__file__),
                      'requests_runner.py': Path(requests_runner.__file__),
                      'research_actor_dependencies.py': Path(research_actor_dependencies.__file__),
                      'research_auto_record.py': Path(sys.modules['scripts.graph.research_auto_record'].__file__),
                      'research_tool_runtime.py': Path(sys.modules['scripts.graph.research_tool_runtime'].__file__),
                      'base_harness.py': core.BASE}
        if args.backend == 'teacher35b': components['research_teacher_backend.py'] = Path(teacher_backend.__file__)
        if is_repair:
            components['experience_helper.py'] = Path(experience_helper.__file__)
        snapshot = root / (eid + '.components'); snapshot.mkdir()
        for name, path in components.items(): shutil.copyfile(path, snapshot / name)
        component_hashes = {name: sha(snapshot / name) for name in components}
        if any(sha(path) != component_hashes[name] for name, path in components.items()):
            raise ValueError('components changed during snapshot')
        plan = {'task': task, 'condition': condition, 'seed': CASES[task][4], 'max_posts': MAX_POSTS,
                'backend_kind': args.backend, 'profile_context': profile['context'], 'profile_output': profile['output'],
                'request_timeout_ms': 900000 if args.backend == 'teacher35b' else 300000,
                'max_seconds': MAX_SECONDS, 'model_profile_sha256': args.model_profile_sha256,
                'projection_sha256': args.actor_manifest_sha256, 'pg_socket_manifest_sha256': args.pg_socket_sha256,
                'live_backend': backend, 'live_postgres': live_pg,
                'repair': repair,
                'task_sha256': sha(task_file), 'harness_sha256': sha(harness), 'runner_sha256': component_hashes['outer_runner.py'],
                'component_sha256': component_hashes,
                'status': 'STARTED', 'reference_boundary': 'D-side reference visible only in post-run evaluator'}
        start = root / (eid + '.started.json'); start.write_text(json.dumps(plan, indent=2) + '\n')
        proc = subprocess.run([sys.executable, str(harness), task, 'no_skill'], stdin=subprocess.DEVNULL,
                              capture_output=True, timeout=MAX_SECONDS + 120)
        (root / (eid + '.runner.stdout')).write_bytes(proc.stdout)
        (root / (eid + '.runner.stderr')).write_bytes(proc.stderr)
        if candidate is not None:
            freeze_repair_candidate(old_case/'work', candidate, manifest, repair_draft_digest)
            if sha(manifest) != repair['candidate_manifest_sha256']:
                raise ValueError('frozen repair candidate changed during episode')
        plan.update({'runner_exit': proc.returncode, 'started_sha256': sha(start)})
        if proc.returncode == 0 and (case / 'receipt.json').is_file():
            receipt = json.loads((case / 'receipt.json').read_text(encoding='utf8'))
            if sha(case / 'raw.jsonl') != receipt['raw_sha256']: raise ValueError('raw receipt changed')
            sampling_file = case / 'sampling_metadata.jsonl'
            metadata = [json.loads(s) for s in sampling_file.read_text().splitlines()] if sampling_file.is_file() else []
            if Counter(json.dumps(x, sort_keys=True) for x in metadata) != Counter(json.dumps(x, sort_keys=True) for x in receipt['sampling_metadata']):
                raise ValueError('sampling metadata changed')
            if (case / 'frozen_instructions.txt').read_bytes() != task_text.strip().encode('utf8'):
                raise ValueError('actor problem changed')
            forwarded = bool(metadata) and all(x['seed'] == CASES[task][4] and x['temperature'] == core.TEMPERATURE
                                                and x['model'] == profile['model_id'] for x in metadata)
            plan.update({'status': 'COMPLETED', 'agent_exit': receipt['agent_exit'], 'raw_sha256': receipt['raw_sha256'],
                         'posts': sum(s.startswith('POST ') for s in receipt['model_http_requests']),
                         'denied': [s for s in receipt['model_http_requests'] if s.startswith('DENIED')],
                         'reported_tokens': sum(t.get('total', 0) for t in receipt['step_finish_tokens']),
                         'reported_usage_steps': len(receipt['step_finish_tokens']),
                         'usage_step_count_matches_posts': len(receipt['step_finish_tokens']) == sum(
                             s.startswith('POST ') for s in receipt['model_http_requests']),
                         'cache_read_included': sum(t.get('cache', {}).get('read', 0) for t in receipt['step_finish_tokens']),
                         'seed_temperature_model_forwarded': forwarded,
                         'post_run_evaluation': run_evaluator(task, case, control, actor, pg)})
        else: plan['status'] = 'RUNNER_ERROR_REVIEW_RAW_AND_PROXY_LOG'
        if any(sha(path) != component_hashes[name] or sha(snapshot / name) != component_hashes[name]
               for name, path in components.items()):
            raise ValueError('runner component changed during episode; review raw and reservation')
        completed = root / (eid + '.completed.json'); completed.write_text(json.dumps(plan, indent=2) + '\n')
        print(json.dumps({'receipt': str(completed), 'sha256': sha(completed), 'status': plan['status']}))
    run(args.task, args.condition)


if __name__ == '__main__':
    main()
