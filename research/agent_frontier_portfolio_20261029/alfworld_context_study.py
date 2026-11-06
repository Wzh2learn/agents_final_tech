"""Versioned multi-task context study, using the existing ALFWorld harness.

Collection and four fresh-session context conditions share one bounded ordinary
continuation rule. This module does not manage model services or expose experts.
"""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import stat
import struct
import subprocess
import sys
import threading
import time

QUAL = Path('/home/testuser/wzh/research_evidence/agent_learning_20261030/alfworld_text_qualification_20261106')
HERE = Path(__file__).resolve().parent
RECOVERY_SHA = 'cad06ec2b6f9e144fea29c17061b9527d07b7df13ecbf5784fb0870d9a0ce8ca'
RECENT_STEPS = 3
STAGES = ('collect', 'collect_none', 'keep_full', 'keep_recent', 'drop_full', 'drop_recent', 'goal_recent', 'ordinary_reset')
PUBLIC_KEYS = ('observation', 'score', 'done', 'won', 'action_count', 'admissible_commands')
CONTINUE = 'Continue the unfinished task.'
_REC = None
HF8B = Path('/home/testuser/wzh/models/hf/Qwen3-8B')
OWNED8B_EXE = Path('/home/testuser/.lmstudio/extensions/backends/llama.cpp-linux-arm64-nvidia-cuda13-2.16.0/llama-server')
_GGUF_DIGEST_CACHE = set()
_GGUF_DIGEST_LOCK = threading.Lock()
_GGUF_DIGEST_PID = os.getpid()
_GGUF_IDENTITY_FIELDS = ('dev','ino','size','mtime_ns','ctime_ns','mode','nlink')


def runtime_path(path, digest, *, private=True):
    path = Path(path)
    if (not path.is_absolute() or path != path.resolve() or path.is_symlink() or
            any(p.is_symlink() for p in path.parents) or not path.is_file() or
            (private and QUAL.parent not in path.parents) or
            not re.fullmatch('[0-9a-f]{64}', digest or '')):
        raise ValueError('unsafe runtime reference')
    return path


def runtime_file(path, digest, *, private=True):
    """Profiles, JSON references, adapters and executables are never cached."""
    path = runtime_path(path, digest, private=private)
    if runtime_digest(path) != digest:
        raise ValueError('runtime reference hash changed')
    return path


def gguf_identity(path):
    observed = path.stat(follow_symlinks=False)
    if not stat.S_ISREG(observed.st_mode):
        raise ValueError('GGUF must remain a regular file')
    return {key:getattr(observed,'st_' + key) for key in _GGUF_IDENTITY_FIELDS}


def verified_gguf(path, digest):
    """Only a POSIX read-only, single-link private GGUF can reuse this process's hash."""
    global _GGUF_DIGEST_PID, _GGUF_DIGEST_LOCK
    if _GGUF_DIGEST_PID != os.getpid():
        # A fork must not inherit either another process's proof or its held lock.
        _GGUF_DIGEST_CACHE.clear()
        _GGUF_DIGEST_LOCK = threading.Lock()
        _GGUF_DIGEST_PID = os.getpid()
    with _GGUF_DIGEST_LOCK:
        path = runtime_path(path, digest)
        before = gguf_identity(path)
        # Windows ctime is creation time, so it cannot guard restored-mtime writes.
        reusable = os.name == 'posix' and before['nlink'] == 1 and not before['mode'] & 0o222
        key = (str(path), digest, *(before[name] for name in _GGUF_IDENTITY_FIELDS))
        if not reusable or key not in _GGUF_DIGEST_CACHE:
            actual = runtime_digest(path)
            runtime_path(path, digest)
            if gguf_identity(path) != before:
                raise ValueError('GGUF identity changed during full hash')
            if actual != digest:
                raise ValueError('runtime reference hash changed')
            if reusable:
                _GGUF_DIGEST_CACHE.add(key)
        runtime_path(path, digest)
        if gguf_identity(path) != before:
            raise ValueError('GGUF identity changed during verification')
        proof = {'path':str(path), 'sha256':digest, 'file_identity':before,
                 'scope':('stream_sha256_or_same_process_posix_readonly_identity'
                          if reusable else 'stream_sha256_every_load')}
        return path, proof


def runtime_digest(path):
    result = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            result.update(chunk)
    return result.hexdigest()


def runtime_reference(ref):
    if not isinstance(ref, dict) or set(ref) != {'path', 'sha256'}:
        raise ValueError('runtime reference requires path and SHA')
    return runtime_file(ref['path'], ref['sha256'])


def load_reference_context(stage, backend, path=None, digest=None):
    if (path is None) != (digest is None):
        raise ValueError('reference context path and SHA must be provided together')
    if path is None:
        return None, None
    if stage != 'ordinary_reset' or backend != 'student8b':
        raise ValueError('reference context is ordinary_reset/student8b only')
    path = runtime_file(path, digest)
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != digest:
        raise ValueError('reference context changed during read')
    text = raw.decode('utf8')
    if not text.strip():
        raise ValueError('reference context must be nonempty UTF8')
    return {'path':str(path),'sha256':digest,'text_sha256':hashlib.sha256(text.encode('utf8')).hexdigest()}, text


def gguf_architecture(path):
    """Metadata only: reject a different Qwen size even if its vocabulary matches."""
    wanted = {'general.architecture', 'qwen3.block_count', 'qwen3.embedding_length',
              'qwen3.feed_forward_length', 'qwen3.attention.head_count', 'qwen3.attention.head_count_kv'}
    with Path(path).open('rb') as stream:
        def take(size):
            value = stream.read(size)
            if len(value) != size:
                raise ValueError('truncated GGUF metadata')
            return value
        def value(kind, keep=True):
            formats = {0:'B', 1:'b', 2:'H', 3:'h', 4:'I', 5:'i', 6:'f', 7:'?', 10:'Q', 11:'q', 12:'d'}
            if kind in formats:
                fmt = '<' + formats[kind]
                return struct.unpack(fmt, take(struct.calcsize(fmt)))[0]
            if kind == 8:
                size, = struct.unpack('<Q', take(8))
                data = take(size)
                return data.decode('utf8') if keep else None
            if kind == 9:
                subtype, size = struct.unpack('<IQ', take(12))
                for _ in range(size):
                    value(subtype, False)
                return None
            raise ValueError('unsupported GGUF metadata type')
        if take(4) != b'GGUF':
            raise ValueError('expected actual GGUF metadata')
        version, _, count = struct.unpack('<IQQ', take(20))
        if version != 3:
            raise ValueError('unsupported GGUF metadata version')
        result = {}
        for _ in range(count):
            key = value(8)
            kind, = struct.unpack('<I', take(4))
            item = value(kind, key in wanted)
            if key in wanted:
                if key in result:
                    raise ValueError('duplicate GGUF architecture metadata')
                result[key] = item
    return result


def runtime_argv(profile, admission):
    process = admission['process']
    if (set(process) != {'pid', 'start_ticks', 'argv', 'cwd', 'exe'} or
            type(process['pid']) is not int or process['pid'] <= 0 or
            not re.fullmatch('[1-9][0-9]*', str(process['start_ticks'])) or
            not Path(process['cwd']).is_absolute() or process['exe'] != str(OWNED8B_EXE)):
        raise ValueError('invalid explicit runtime process identity')
    argv = process['argv']
    if not isinstance(argv, list) or not argv or argv[0] != str(OWNED8B_EXE) or any(type(a) is not str for a in argv):
        raise ValueError('invalid owned server argv')
    expected = {'-m': profile['gguf_path'], '--host':'127.0.0.1', '--port':'18104',
                '--alias':profile['model_id'], '-c':'32768', '-n':'8192', '-np':'1'}
    for flag, expected_value in expected.items():
        if argv.count(flag) != 1 or argv.index(flag)+1 >= len(argv) or argv[argv.index(flag)+1] != expected_value:
            raise ValueError('runtime argv/profile mismatch: ' + flag)
    alternate = {'--lora-scaled', '--lora-init-without-apply', '--model', '--ctx-size', '--n-predict', '--parallel'}
    if (argv.count('--no-context-shift') != 1 or any(a in argv for a in alternate) or
            any('=' in a and a.split('=',1)[0] in set(expected) | alternate | {'--lora'} for a in argv)):
        raise ValueError('ambiguous runtime model/context/adapter flags')
    active = admission['active_lora']
    if profile['variant'] == 'frozen':
        if active is not None or '--lora' in argv:
            raise ValueError('frozen variant must have no active adapter')
    else:
        if (not isinstance(active, dict) or set(active) != {'path','sha256','scale'} or
                type(active['scale']) not in (int,float) or active['scale'] != 1):
            raise ValueError('variant requires one explicit scale1 adapter binding')
        runtime_file(active['path'], active['sha256'])
        if argv.count('--lora') != 1 or argv.index('--lora')+1 >= len(argv) or argv[argv.index('--lora')+1] != active['path']:
            raise ValueError('admission adapter differs from actual startup argv')


def load_study_profile(backend, path=None, digest=None):
    """Explicit study epoch only; frozen actor/recovery pins remain unchanged."""
    if (path is None) != (digest is None):
        raise ValueError('runtime profile path and SHA must be provided together')
    core = recovery().actor()
    if path is None:
        return core.load_profile(backend), None
    if backend != 'student8b':
        raise ValueError('runtime profile override is student8b only')
    path = runtime_file(path, digest)
    profile = json.loads(path.read_text(encoding='utf8'))
    keys = {'schema','variant','host','port','model_id','context','output','enable_thinking',
            'gguf_path','gguf_sha256','server_executable','server_executable_sha256',
            'parent_hf_binding','runtime_admission'}
    if (set(profile) != keys or profile['schema'] != 'alfworld_owned_8b_runtime_profile_v1' or
            profile['variant'] not in {'frozen','ordinary','recovery'} or
            (profile['host'],profile['port'],profile['model_id'],profile['context'],profile['output']) !=
            ('127.0.0.1',18104,'qwen3-8b-qual',32768,8192) or profile['enable_thinking'] is not False):
        raise ValueError('unexpected owned8B runtime profile')
    trusted = core.load_profile('student8b')
    if (profile['server_executable'] != str(OWNED8B_EXE) or
            profile['server_executable_sha256'] != trusted['server_executable_sha256']):
        raise ValueError('untrusted owned server executable')
    runtime_file(OWNED8B_EXE, profile['server_executable_sha256'], private=False)
    gguf, gguf_proof = verified_gguf(profile['gguf_path'], profile['gguf_sha256'])
    parent_path = runtime_reference(profile['parent_hf_binding'])
    parent = json.loads(parent_path.read_text(encoding='utf8'))
    if parent['model_dir'] != str(HF8B):
        raise ValueError('runtime parent is not the fixed HF Qwen3-8B')
    rows = parent['files']
    if (not isinstance(rows, list) or not rows or len({row['path'] for row in rows}) != len(rows) or
            any(Path(row['path']).parent != HF8B or not re.fullmatch('[a-f0-9]{64}', row.get('sha256',''))
                or type(row.get('bytes')) is not int or row['bytes'] < 0 for row in rows)):
        raise ValueError('invalid parent HF file binding')
    files = {Path(row['path']).name:row for row in rows}
    for name in ('config.json','tokenizer.json','tokenizer_config.json','model.safetensors.index.json'):
        row = files[name]
        if Path(row['path']) != HF8B / name:
            raise ValueError('parent HF tokenizer/config path changed')
        runtime_file(row['path'], row['sha256'], private=False)
    index = json.loads((HF8B/'model.safetensors.index.json').read_text(encoding='utf8'))
    shards = set(index['weight_map'].values())
    if not shards or not shards <= files.keys() or any(Path(n).name != n or not n.endswith('.safetensors') for n in shards):
        raise ValueError('parent HF binding lacks its indexed weight shards')
    config = json.loads((HF8B/'config.json').read_text(encoding='utf8'))
    arch = gguf_architecture(gguf)
    mapping = {'qwen3.block_count':'num_hidden_layers', 'qwen3.embedding_length':'hidden_size',
               'qwen3.feed_forward_length':'intermediate_size', 'qwen3.attention.head_count':'num_attention_heads',
               'qwen3.attention.head_count_kv':'num_key_value_heads'}
    if (config.get('architectures') != ['Qwen3ForCausalLM'] or config.get('model_type') != 'qwen3' or
            arch.get('general.architecture') != 'qwen3' or
            any(type(config.get(v)) is not int or config[v] <= 0 or type(arch.get(k)) is not int or arch[k] != config[v]
                for k,v in mapping.items())):
        raise ValueError('actual GGUF architecture differs from bound HF8B config')
    admission_path = runtime_reference(profile['runtime_admission'])
    admission = json.loads(admission_path.read_text(encoding='utf8'))
    if (admission.get('schema') != 'owned_8b_runtime_admission_v1' or admission.get('status') != 'OWNED_RESEARCH_RUNTIME_READY' or
            admission.get('gguf') != {'path':str(gguf),'sha256':profile['gguf_sha256']} or
            admission.get('model_alias') != profile['model_id'] or admission.get('parent_hf_binding') != profile['parent_hf_binding']):
        raise ValueError('runtime admission does not bind this parent/model')
    runtime_argv(profile, admission)
    binding = {'path':str(path),'sha256':digest,'profile':profile,'parent_hf_binding':parent,
               'runtime_admission':admission,'gguf_architecture':arch,'gguf_verification':gguf_proof,
               'parent_weights_rehashed_here':False}
    return profile, binding


def verify_runtime_identity(binding):
    """Read /proc only; no HTTP, service management or adapter activation."""
    profile, process = binding['profile'], binding['runtime_admission']['process']
    proc = Path('/proc') / str(process['pid'])
    raw = (proc/'cmdline').read_bytes()
    actual = {'pid':process['pid'], 'start_ticks':(proc/'stat').read_text().rsplit(')',1)[1].split()[19],
              'argv':raw.rstrip(b'\0').decode('utf8').split('\0'), 'cwd':os.readlink(proc/'cwd'), 'exe':os.readlink(proc/'exe')}
    expected = {**process, 'start_ticks':str(process['start_ticks'])}
    if actual != expected:
        raise ValueError('actual owned runtime process changed')
    if runtime_digest(proc/'exe') != profile['server_executable_sha256']:
        raise ValueError('actual running executable hash changed')
    runtime_file(OWNED8B_EXE, profile['server_executable_sha256'], private=False)
    sockets = set()
    for fd in (proc/'fd').iterdir():
        try:
            match = re.fullmatch(r'socket:\[([0-9]+)\]', os.readlink(fd))
            if match:
                sockets.add(match.group(1))
        except FileNotFoundError:
            pass
    rows = [line.split() for line in (proc/'net/tcp').read_text().splitlines()[1:]]
    if not any(row[1] == '0100007F:' + format(18104,'04X') and row[3] == '0A' and row[9] in sockets for row in rows):
        raise ValueError('admitted process does not own 127.0.0.1:18104')
    return {**actual, 'argv_sha256':hashlib.sha256(raw).hexdigest(), 'owns_loopback_listener':True}


def study_token_qualifier(backend, profile, override):
    binding, qualify = recovery().token_qualifier(backend, profile)
    if override is not None:
        files = {Path(row['path']).name:row['sha256'] for row in override['parent_hf_binding']['files']}
        if (binding['model_dir'] != override['parent_hf_binding']['model_dir'] or
                any(files.get(name) != digest for name,digest in binding['files_sha256'].items()) or
                binding.get('template_origin') != 'actual_GGUF_metadata' or
                binding.get('vocab_mapping_all_equal') is not True or binding.get('BPE_merges_all_equal') is not True):
            raise ValueError('runtime tokenizer is not the bound HF/native GGUF pair')
        binding = {**binding, 'runtime_gguf_path':profile['gguf_path'], 'runtime_gguf_sha256':profile['gguf_sha256'],
                   'parent_hf_binding_sha256':profile['parent_hf_binding']['sha256']}
    return binding, qualify


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def recovery():
    global _REC
    p = HERE / 'run_alfworld_recovery_20261106.py'
    if p.is_symlink() or sha(p) != RECOVERY_SHA:
        raise ValueError('frozen recovery primitives changed')
    if _REC is None:
        _REC = module(p, 'context_study_recovery')
    return _REC


def task_pool():
    return module(HERE / 'alfworld_task_pool.py', 'context_study_pool')


def components():
    paths = [Path(__file__).resolve(),HERE/'alfworld_task_pool.py',
             HERE/'prepare_alfworld_experience_20261106.py',HERE/'prepare_django_aggregation_experience_20261106.py']
    return {**recovery().components(), **{str(p):sha(p) for p in paths}}


def public(value):
    result = {key: value[key] for key in PUBLIC_KEYS}
    recovery().bridge().validate_response(result)
    return result


def collection_prompt(reset, stage, assignment, experience):
    """The no-experience control uses the identical frozen task/controller."""
    core = recovery().actor()
    if stage == 'collect_none':
        return core.condition_prompt(reset, 'none')
    if stage != 'collect':
        raise ValueError('not a collection condition')
    return core.condition_prompt(reset, assignment['carrier'], experience)


def render_prompt(reset, steps, current, experience, keep, window):
    if type(keep) is not bool or window not in {'full', 'recent'} or not isinstance(experience, str):
        raise ValueError('invalid context condition')
    history = steps if window == 'full' else steps[-RECENT_STEPS:]
    history = [{'action': row['action'], 'state': {k: public(row['state'])[k] for k in PUBLIC_KEYS[:-1]}}
               for row in history]
    return (
        'Complete this unfinished household task using the actual environment.\n'
        'Original public goal and reset observation (historical):\n' + public(reset)['observation'] +
        '\nPrior experience, historical and not the current state:\n<prior_experience>\n' +
        (experience if keep else '') + '\n</prior_experience>\n'
        'Accepted target actions and public observations (historical):\n' + json.dumps(history, ensure_ascii=False) +
        '\nCurrent public observation and admissible actions:\n' + json.dumps(public(current), ensure_ascii=False) +
        '\nUse only Bash, one environment action per tool call:\n'
        "/runtime/bin/python -B /world/client.py step --socket /world/s --action '<one exact action>'\n"
        'Read every returned observation and use current admissible_commands. Historical observations are cached, '
        'not fresh evidence. Follow the current goal rather than an old object or procedure. Every accepted action '
        'including look consumes a real step. Continue autonomously. Stop when done is true, and claim success only '
        'after an actual response has won=true. There is no reset, game selection or administrative operation.\n')


def recovery_prompt(reset, steps, current, experience, stage):
    if stage not in {'keep_full', 'keep_recent', 'drop_full', 'drop_recent', 'goal_recent'}:
        raise ValueError('not a recovery condition')
    text = render_prompt(reset, steps, current, experience, stage.startswith('keep_'), stage.split('_')[1])
    if stage == 'goal_recent':
        # Repetition of an already supplied public goal, never a reference plan.
        observation = public(reset)['observation']
        marker = 'Your task is to:'
        if observation.count(marker) != 1:
            raise ValueError('public goal must be unambiguous for restatement')
        goal = observation.split(marker, 1)[1].strip()
        if not goal or '\n' in goal:
            raise ValueError('public goal must be a single visible instruction')
        text += '\nCurrent task to finish (restated from the public reset): ' + goal + '\n'
    return text


def initial_prompt(reset: dict, stage: str, assignment: dict, experience: str) -> str:
    """Start an ordinary episode without inventing a failed source trajectory."""
    if stage == 'ordinary_reset':
        return render_prompt(reset, [], reset, '', False, 'recent')
    return collection_prompt(reset, stage, assignment, experience)


def stage_caps(stage: str, study: dict, prefix: dict | None) -> dict:
    """Validate source presence and preserve each stage's original budget."""
    if stage not in STAGES:
        raise ValueError('unsupported episode stage')
    from_reset = stage in {'collect', 'collect_none', 'ordinary_reset'}
    if from_reset != (prefix is None):
        raise ValueError('only recovery stages require a source prefix')
    if stage == 'ordinary_reset':
        return study['total_caps']
    return study['collection_caps'] if prefix is None else remaining_caps(study['total_caps'], prefix['receipt'])


def remaining_caps(total, receipt):
    for key in ('model_request_payload_bytes','model_response_wire_bytes'):
        if type(receipt[key]) is not int or receipt[key] < 0:
            raise ValueError('invalid individual physical byte cost')
    used = {'posts': receipt['model_posts'], 'world_actions': receipt['world_actions'],
            'model_payload_bytes_combined': receipt['model_request_payload_bytes'] + receipt['model_response_wire_bytes']}
    if any(type(v) is not int or v < 0 for v in used.values()):
        raise ValueError('invalid physical source cost')
    elapsed = receipt['elapsed_seconds']
    if type(elapsed) not in (float, int) or not math.isfinite(elapsed) or elapsed < 0:
        raise ValueError('invalid elapsed source cost')
    result = {k: total[k] - used[k] for k in used}
    result['seconds'] = math.floor(total['seconds'] - elapsed)
    if any(type(v) is not int or v <= 0 for v in result.values()):
        raise ValueError('source exhausted the common total budget')
    return result


def one_continue_eligible(first_exit, final, posts, max_posts, elapsed, max_seconds, relay_errors):
    if (type(first_exit) is not int or type(posts) is not int or posts < 0 or
            type(max_posts) is not int or max_posts <= 0 or type(elapsed) not in (int,float) or
            not math.isfinite(elapsed) or elapsed < 0 or type(max_seconds) not in (int,float) or
            not math.isfinite(max_seconds) or max_seconds <= 0 or not isinstance(final,dict) or
            type(final.get('won')) is not bool or type(final.get('done')) is not bool):
        return False
    return bool(first_exit == 0 and final and not final['won'] and not final['done'] and
                posts < max_posts and elapsed + 5 < max_seconds and not relay_errors)


def check_root(root):
    root = Path(root).absolute()
    if root != root.resolve():
        raise ValueError('episode root cannot traverse aliases or symlinks')
    try:
        parts = root.relative_to(QUAL / 'context_study_v1/cases').parts
    except ValueError as exc:
        raise ValueError('outside canonical study namespace') from exc
    if (len(parts) != 4 or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]*', parts[0]) or
            parts[1] not in STAGES or parts[2] not in {'student8b', 'teacher27b'} or
            not re.fullmatch(r'attempt_v[1-9][0-9]*', parts[3])):
        raise ValueError('use cases/case_id/stage/backend/attempt_vN')
    return root


def protocol(path, digest):
    path = Path(path)
    if path.is_symlink() or sha(path) != digest:
        raise ValueError('frozen study protocol changed')
    value = json.loads(path.read_text())
    core = recovery().actor()
    core.episode_caps(value['total_caps'])
    core.episode_caps(value['collection_caps'])
    if (value['recent_steps'] != RECENT_STEPS or value['ordinary_continuations'] != 1 or
            value['context_margin_tokens'] != 512 or value['world_seed'] != 17 or
            value['total_caps']['world_actions'] != 100 or value['collection_caps']['world_actions'] != 100 or
            value['collection_caps']['posts'] >= value['total_caps']['posts'] or
            value['collection_caps']['seconds'] >= value['total_caps']['seconds']):
        raise ValueError('unqualified common controller/budget contract')
    return value


def read_case(study, case_id):
    if case_id not in study['case_ids']:
        raise ValueError('case not in frozen study')
    game, binding = task_pool().select_game(study['pool_path'], study['pool_sha256'], case_id)
    pool = json.loads(Path(study['pool_path']).read_text())
    row = next(row for row in pool['games'] if row['id'] == case_id)
    a = row['experience_assignment']
    if a['carrier'] not in {'ordinary_public_history', 'ordinary_generated_skill'}:
        raise ValueError('unsupported frozen carrier')
    # The frozen compiler uses a sibling import as when invoked by its CLI.
    # Scope this loader path to validation; do not change any frozen module global.
    inserted = str(HERE) not in sys.path
    if inserted:
        sys.path.insert(0,str(HERE))
    try:
        value = recovery().actor().experience_validator()(Path(a['manifest_path']), a['manifest_sha256'])
    finally:
        if inserted:
            sys.path.remove(str(HERE))
    if value['manifest']['source_game_id'] != a['source_id']:
        raise ValueError('experience source assignment changed')
    return game, binding, a, value['texts'][a['carrier']]


def load_prefix(root, case_id):
    root = check_root(root)
    if root.parts[-3:-1] != ('collect', 'student8b') or root.parts[-4] != case_id:
        raise ValueError('recovery requires this case student collection')
    m = json.loads((root / 'manifest.json').read_text())
    r = json.loads((root / 'receipt.json').read_text())
    reservation = json.loads((root / 'reservation.json').read_text())
    if (m.get('case_id'), m.get('stage'), m.get('backend')) != (case_id, 'collect', 'student8b'):
        raise ValueError('source manifest must identify this case student collection')
    if (r.get('label') != 'MULTITASK_CONTEXT_DEVELOPMENT' or
            reservation.get('mode') != 'REAL_DEVELOPMENT' or
            reservation.get('manifest_sha256') != sha(root/'manifest.json') or
            type(r.get('real_model_calls')) is not int or r['real_model_calls'] <= 0 or
            r['real_model_calls'] != r.get('forwarded_model_posts')):
        raise ValueError('only an actual model collection can seed real recovery')
    if r['manifest_sha256'] != sha(root / 'manifest.json') or r['won'] or r['unknown_usage_model_posts']:
        raise ValueError('source must be a complete-accounted nonterminal unfinished attempt')
    events = [json.loads(line) for line in (root / 'execute_world.jsonl').read_text().splitlines()]
    resets = [public(row['state']) for row in events if row.get('event') == 'reset']
    steps = [{'action': row['action'], 'state': public(row['state'])} for row in events if row.get('event') == 'step']
    if (len(resets) != 1 or not steps or steps[-1]['state']['done'] or
            [row['state']['action_count'] for row in steps] != list(range(1, len(steps)+1)) or
            public(r['final_world_state']) != steps[-1]['state'] or r['world_actions'] != len(steps)):
        raise ValueError('incomplete or terminal public source trajectory')
    binding = {str(root / name): sha(root / name) for name in ('manifest.json', 'receipt.json', 'execute_world.jsonl')}
    return {'root': root, 'manifest': m, 'receipt': r, 'reset': resets[0], 'steps': steps,
            'binding': binding, 'public_prefix_sha256':hashlib.sha256(
                json.dumps([resets[0],steps],sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()}


def replay_prefix(prefix, reset, step, log):
    # Frozen recovery's replay expects this metadata key, not the file-hash map
    # used by this study's immutable cross-arm cohort. Keep both contracts intact.
    projected = dict(prefix,binding={'public_prefix_sha256':prefix['public_prefix_sha256']})
    return recovery().replay(projected,reset,step,log)


def cohort_binding(root, prefix, protocol_sha):
    """One immutable prefix per case; arms cannot cherry-pick other attempts."""
    path = check_root(root).parents[2] / 'RECOVERY_COHORT.json'
    expected = {'protocol_sha256':protocol_sha, 'source_root':str(prefix['root']),
                'source_binding':prefix['binding']}
    if prefix['manifest']['protocol_sha256'] != protocol_sha:
        raise ValueError('source belongs to a different frozen study')
    try:
        recovery().actor().write_new(path,expected)
    except FileExistsError:
        pass
    if path.is_symlink() or json.loads(path.read_text()) != expected:
        raise ValueError('all arms must use the same frozen collector')
    return {'path':str(path),'sha256':sha(path)}


def prepare(root, protocol_path, protocol_sha, *, source_root=None, model_seed=17,
            runtime_profile=None, runtime_profile_sha=None, reference_context=None, reference_context_sha=None):
    if (runtime_profile is None) != (runtime_profile_sha is None):
        raise ValueError('runtime profile path and SHA must be provided together')
    if (reference_context is None) != (reference_context_sha is None):
        raise ValueError('reference context path and SHA must be provided together')
    root = check_root(root)
    root.mkdir(parents=True, exist_ok=True)
    if any(root.iterdir()):
        raise FileExistsError('fresh empty attempt required')
    case_id, stage, backend, _ = root.parts[-4:]
    reference, reference_text = load_reference_context(stage, backend, reference_context, reference_context_sha)
    study = protocol(protocol_path, protocol_sha)
    core = recovery().actor()
    profile, override = load_study_profile(backend, runtime_profile, runtime_profile_sha)
    game, pool, assignment, experience = read_case(study, case_id)
    prefix = load_prefix(source_root, case_id) if source_root is not None else None
    caps = stage_caps(stage, study, prefix)
    cohort = cohort_binding(root,prefix,protocol_sha) if prefix else None
    world = None
    try:
        # World budget is total100 even when collection's request/time budget is shorter.
        world, reset, _ = task_pool().start_world(root, case_id, study['world_seed'], 'preflight',
                dict(caps, world_actions=100), study['pool_path'], study['pool_sha256'])
        reset = public(reset)
        current = reset
        if prefix:
            current, _ = replay_prefix(prefix, reset, lambda a: recovery().bridge().client_step(world[1]/'s', a), root/'preflight_replay.jsonl')
    finally:
        if world:
            core.stop_world(world)
    prompt = (render_prompt(reset, [], reset, reference_text, True, 'recent') if reference is not None else
              initial_prompt(reset, stage, assignment, experience) if prefix is None else
              recovery_prompt(reset, prefix['steps'], current, experience, stage))
    (root / 'task.txt').write_bytes(prompt.encode())
    core.write_new(root / 'opencode_config.json', core.config(profile, model_seed))
    core.write_new(root / 'initial_reset.json', reset)
    core.write_new(root / 'handoff_public.json', current)
    token_binding, _ = study_token_qualifier(backend, profile, override)
    core.dependencies.verify_projection(core.RUNTIME_ROOT, core.RUNTIME_SHA)
    if sha(core.BINARY) != core.BINARY_SHA:
        raise ValueError('OpenCode binary changed')
    image = subprocess.check_output(['docker', 'image', 'inspect', core.IMAGE, '--format', '{{.Id}}'], text=True).strip()
    manifest = {'version': 1, 'case_id': case_id, 'stage': stage, 'backend': backend,
            'model_id': profile['model_id'], 'model_seed': model_seed, 'world_seed': study['world_seed'],
            'protocol_path': str(Path(protocol_path).resolve()), 'protocol_sha256': protocol_sha,
            'pool_binding': pool, 'game': game, 'experience_assignment': assignment,
            'experience_text_sha256': hashlib.sha256(experience.encode()).hexdigest(),
            'source_root': str(prefix['root']) if prefix else None, 'source_binding': prefix['binding'] if prefix else None,
            'cohort_binding':cohort,
            'caps': caps, 'world_step_cap': 100, 'tokenizer_binding': token_binding,
            'sampling': core.model_payload({}, backend, profile, model_seed, False if backend == 'student8b' else None),
            'profile_sha256': override['sha256'] if override else core.PROFILE_PINS[backend][1], 'components': components(),
            'uid': os.getuid(), 'gid': os.getgid(), 'image_id': image,
            'inputs_sha256': {name: sha(root/name) for name in ['task.txt','opencode_config.json','initial_reset.json','handoff_public.json']},
            'development_only': True, 'ordinary_continuations': 1, 'recent_steps': RECENT_STEPS}
    if override is not None:
        manifest['runtime_profile_override'] = override
    if reference is not None:
        manifest['reference_context'] = reference
    core.write_new(root / 'manifest.json', manifest)
    return manifest


def verify(root, digest):
    root = check_root(root)
    if sha(root / 'manifest.json') != digest:
        raise ValueError('manifest changed')
    m = json.loads((root / 'manifest.json').read_text())
    if tuple(root.parts[-4:-1]) != (m['case_id'], m['stage'], m['backend']) or m['components'] != components():
        raise ValueError('namespace or components changed')
    bound_reference = m.get('reference_context')
    reference, reference_text = load_reference_context(m['stage'], m['backend'],
            bound_reference['path'] if bound_reference else None, bound_reference['sha256'] if bound_reference else None)
    if reference != bound_reference:
        raise ValueError('frozen reference context metadata changed')
    study = protocol(m['protocol_path'], m['protocol_sha256'])
    game, pool, assignment, experience = read_case(study, m['case_id'])
    prefix = load_prefix(m['source_root'], m['case_id']) if m['source_root'] is not None else None
    caps = stage_caps(m['stage'], study, prefix)
    expected_cohort = cohort_binding(root,prefix,m['protocol_sha256']) if prefix else None
    if m['cohort_binding'] != expected_cohort:
        raise ValueError('shared recovery cohort changed')
    core = recovery().actor()
    bound = m.get('runtime_profile_override')
    p, override = load_study_profile(m['backend'], bound['path'] if bound else None, bound['sha256'] if bound else None)
    if bound != override:
        raise ValueError('frozen runtime profile metadata changed')
    profile_sha = override['sha256'] if override else core.PROFILE_PINS[m['backend']][1]
    if (m['game'] != game or m['pool_binding'] != pool or m['caps'] != caps or
            m['experience_assignment'] != assignment or m['profile_sha256'] != profile_sha or
            m['source_binding'] != (prefix['binding'] if prefix else None) or
            m['sampling'] != core.model_payload({}, m['backend'], p, m['model_seed'], False if m['backend']=='student8b' else None) or
            m['model_id'] != p['model_id'] or (m['uid'],m['gid']) != (os.getuid(),os.getgid())):
        raise ValueError('frozen study inputs changed')
    for name, h in m['inputs_sha256'].items():
        if sha(root/name) != h:
            raise ValueError('frozen actor input changed')
    reset = json.loads((root/'initial_reset.json').read_text())
    current = json.loads((root/'handoff_public.json').read_text())
    if prefix is None and current != reset:
        raise ValueError('from-reset stage cannot contain recovery progress')
    expected = (render_prompt(reset, [], reset, reference_text, True, 'recent') if reference is not None else
                initial_prompt(reset, m['stage'], assignment, experience) if prefix is None else
                recovery_prompt(reset,prefix['steps'],current,experience,m['stage']))
    if (root/'task.txt').read_bytes() != expected.encode() or hashlib.sha256(experience.encode()).hexdigest() != m['experience_text_sha256']:
        raise ValueError('prompt or source carrier changed')
    binding, qualify = study_token_qualifier(m['backend'],p,override)
    if binding != m['tokenizer_binding']:
        raise ValueError('native template binding changed')
    return m,study,p,prefix,qualify


def final_state(root):
    path = Path(root) / 'execute_world.jsonl'
    rows = [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []
    states = [public(row['state']) for row in rows if row.get('event') in {'reset','step'}]
    return states[-1] if states else None


def session_id(raw):
    values = set()
    def visit(x):
        if isinstance(x,dict):
            for key,value in x.items():
                if key in {'sessionID','session_id'} and isinstance(value,str) and re.fullmatch(r'ses_[A-Za-z0-9]+',value):
                    values.add(value)
                else:
                    visit(value)
        elif isinstance(x,list):
            for value in x:
                visit(value)
    for line in Path(raw).read_text().splitlines():
        visit(json.loads(line))
    if len(values) != 1:
        raise ValueError('ordinary continuation requires one actual persisted session')
    return values.pop()


def retry_guest(sid):
    if not re.fullmatch(r'ses_[A-Za-z0-9]+',sid):
        raise ValueError('invalid owned session')
    guest = recovery().actor().GUEST
    needle = '"--title","alfworld-no-history",prompt]'
    if guest.count(needle) != 1:
        raise ValueError('frozen guest changed')
    return guest.replace(needle, '"--session",'+json.dumps(sid)+',prompt]')


def run_episode(root, digest, *, fake_endpoint=None):
    root = check_root(root)
    m,study,p,prefix,qualify = verify(root,digest)
    core = recovery().actor()
    reservation = {'manifest_sha256':digest,'mode':'OWNED_FAKE' if fake_endpoint else 'REAL_DEVELOPMENT'}
    if m.get('runtime_profile_override') is not None:
        reservation['runtime_identity'] = (verify_runtime_identity(m['runtime_profile_override']) if fake_endpoint is None
                                           else {'mode':'OWNED_FAKE_NO_RUNTIME_IDENTITY_CLAIM'})
    core.write_new(root/'reservation.json',reservation)
    world = relay = model_dir = None
    started = time.monotonic()
    errors,rounds = [],[]
    replay_cost = None
    status = 'FAILED'
    class Relay(core.ModelRelay):
        def forward(self,upstream,packet,payload=None,post_index=None):
            if self.forwarded == 0:
                delivery = core.delivery_evidence(payload,expected_task=self.expected_task)
                core.write_new(root/'actual_task_delivery.json',dict(delivery,stage=m['stage']))
                if not (delivery['whole_task_raw_equal'] or delivery['whole_task_lossless_quoted_equal']):
                    raise ValueError('actual first model request lost the frozen context condition')
            proof = qualify(payload)
            proof['safety_margin_tokens'] = study['context_margin_tokens']
            proof['fits_with_margin'] = proof['template_input_tokens'] + proof['reserved_output_tokens'] + study['context_margin_tokens'] <= proof['context']
            core.write_new(root/'template_checks'/(str(post_index).zfill(5)+'.json'),proof)
            if not proof['fits_with_margin']:
                raise ValueError('native template estimate plus output/margin exceeds context')
            return super().forward(upstream,packet,payload,post_index)
    name = None
    try:
        world,reset,_ = task_pool().start_world(root,m['case_id'],m['world_seed'],'execute',
                         dict(m['caps'],world_actions=100),study['pool_path'],study['pool_sha256'])
        reset = public(reset)
        if reset != json.loads((root/'initial_reset.json').read_text()):
            raise ValueError('native reset differs from frozen preflight')
        current = reset
        if prefix:
            current,replay_cost = replay_prefix(prefix,reset,lambda a: recovery().bridge().client_step(world[1]/'s',a),root/'execute_replay.jsonl')
        if current != json.loads((root/'handoff_public.json').read_text()):
            raise ValueError('handoff differs from frozen public state')
        work = root/'workspace'
        work.mkdir()
        (work/'task.txt').write_bytes((root/'task.txt').read_bytes())
        (work/'opencode.json').write_bytes((root/'opencode_config.json').read_bytes())
        (work/'guest.py').write_text(core.GUEST)
        model_dir = core.socket_directory('m')
        relay = Relay(root,model_dir,m['backend'],p,m['model_seed'],fake_endpoint or (p['host'],p['port']),
                      m['caps'],m['sampling'],student_enable_thinking=False if m['backend']=='student8b' else None)
        actor_started = time.monotonic()
        for round_index in (1,2):
            name = 'alf-study-owned-'+str(os.getpid())+'-'+str(time.monotonic_ns())
            cmd = core.docker_command(work,world[1],model_dir,m,name)
            core.write_new(root/('docker_command_'+str(round_index)+'.json'),{'argv':cmd})
            timeout = max(1,m['caps']['seconds']-(time.monotonic()-actor_started))
            raw = root/('raw_'+str(round_index)+'.jsonl')
            with raw.open('xb') as out,(root/('actor_'+str(round_index)+'.stderr')).open('xb') as err:
                done = subprocess.run(cmd,stdout=out,stderr=err,timeout=timeout)
            state = final_state(root)
            rounds.append({'round':round_index,'exit':done.returncode,'raw_sha256':sha(raw),'state':state,
                           'model_posts_cumulative':relay.budget.posts,'actor_elapsed':time.monotonic()-actor_started})
            if round_index==2 or not one_continue_eligible(done.returncode,state,relay.budget.posts,m['caps']['posts'],
                            time.monotonic()-actor_started,m['caps']['seconds'],relay.errors):
                break
            sid = session_id(raw)
            (work/'guest.py').write_text(retry_guest(sid))
            (work/'task.txt').write_bytes(CONTINUE.encode())
            core.write_new(root/'ordinary_continuation.json',{'session_id':sid,'prompt':CONTINUE,'after_round':1,
                           'world_state_before':state,'world_reset':False,'new_method':False})
        status = 'RETURNED'
    except subprocess.TimeoutExpired:
        status = 'COLLECTION_TIMEOUT' if m['stage'] in {'collect', 'collect_none'} else 'EPISODE_TIMEOUT'
    except Exception as exc:
        errors.append({'type':type(exc).__name__,'error':str(exc)})
    finally:
        if relay:
            relay.begin_close()
        if name:
            try:
                subprocess.run(['docker','rm','-f',name],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=15)
            except Exception as exc:
                errors.append({'cleanup':'actor','error':str(exc)})
        if relay:
            try:
                relay.close()
            except Exception as exc:
                errors.append({'cleanup':'relay','error':str(exc)})
        elif model_dir:
            core.cleanup_directory(model_dir)
        if world:
            try:
                core.stop_world(world)
            except Exception as exc:
                errors.append({'cleanup':'world','error':str(exc)})
        state = final_state(root)
        responses = [json.loads(x.read_text()) for x in sorted((root/'responses').glob('*.receipt.json'))]
        usages = [x['usage'] for x in responses if x.get('complete') and x.get('usage')]
        counts = {k:sum(u.get(k,0) for u in usages) for k in ['prompt_tokens','completion_tokens','total_tokens']}
        cache_values = [u.get('prompt_tokens_details',{}).get('cached_tokens')
                        if isinstance(u.get('prompt_tokens_details'),dict) else None for u in usages]
        cache_known = len(cache_values)>0 and all(type(x) is int and x>=0 for x in cache_values)
        used_prefix = len(prefix['steps']) if prefix else 0
        receipt = {'label':'OWNED_FAKE_NOT_SCIENTIFIC' if fake_endpoint else 'MULTITASK_CONTEXT_DEVELOPMENT',
            'status':status,'case_id':m['case_id'],'stage':m['stage'],'backend':m['backend'],'manifest_sha256':digest,
            'elapsed_seconds':time.monotonic()-started,'errors':errors,'model_relay_errors':relay.errors if relay else [],
            'model_posts':relay.budget.posts if relay else 0,'forwarded_model_posts':relay.forwarded if relay else 0,
            'real_model_calls':0 if fake_endpoint else relay.forwarded if relay else 0,
            'model_request_payload_bytes':relay.budget.request_bytes if relay else 0,
            'model_response_wire_bytes':relay.budget.response_bytes if relay else 0,
            'response_receipts':responses,'provider_usage':counts,
            'provider_cached_input_tokens':sum(cache_values) if cache_known else None,
            'unknown_usage_model_posts':max(0,(relay.forwarded if relay else 0)-len(usages)),
            'rounds':rounds,'ordinary_continuations':max(0,len(rounds)-1),
            'first_stop_won':bool(rounds and rounds[0]['state'] and rounds[0]['state']['won']),
            'final_world_state':state,'won':bool(state and state['won']),
            'world_actions':max(0,state['action_count']-used_prefix) if state else 0,
            'total_world_action_count':state['action_count'] if state else None,
            'replay_control_cost':replay_cost,'experience_delivery':relay.delivery if relay else None,
            'source_binding_charge_once':m['source_binding'],'development_only':True,
            'not_independent_confirmation':True,'cached_tokens_are_input_subset':True}
        core.write_new(root/'receipt.json',receipt)
    return receipt


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    modes = p.add_mutually_exclusive_group(required=True)
    modes.add_argument('--preflight-only',action='store_true')
    modes.add_argument('--execute',action='store_true')
    p.add_argument('--run-root',required=True,type=Path)
    p.add_argument('--protocol',type=Path)
    p.add_argument('--protocol-sha')
    p.add_argument('--source-root',type=Path)
    p.add_argument('--model-seed',type=int,default=17)
    p.add_argument('--manifest-sha')
    p.add_argument('--runtime-profile',type=Path)
    p.add_argument('--runtime-profile-sha')
    p.add_argument('--reference-context',type=Path)
    p.add_argument('--reference-context-sha')
    a = p.parse_args(argv)
    if (a.runtime_profile is None) != (a.runtime_profile_sha is None):
        p.error('runtime profile path and SHA must be provided together')
    if (a.reference_context is None) != (a.reference_context_sha is None):
        p.error('reference context path and SHA must be provided together')
    if a.execute:
        if not a.manifest_sha or a.protocol or a.protocol_sha or a.source_root or a.runtime_profile or a.reference_context:
            p.error('execute only accepts the frozen manifest SHA and root')
        r = run_episode(a.run_root,a.manifest_sha)
    else:
        if not a.protocol or not a.protocol_sha or not 0<=a.model_seed<2**32:
            p.error('preflight requires frozen protocol and uint32 model seed')
        r = prepare(a.run_root,a.protocol,a.protocol_sha,source_root=a.source_root,model_seed=a.model_seed,
                    runtime_profile=a.runtime_profile,runtime_profile_sha=a.runtime_profile_sha,
                    reference_context=a.reference_context,reference_context_sha=a.reference_context_sha)
    print(json.dumps(r))


if __name__=='__main__':
    main()
