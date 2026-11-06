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
import subprocess
import sys
import time

QUAL = Path('/home/testuser/wzh/research_evidence/agent_learning_20261030/alfworld_text_qualification_20261106')
HERE = Path(__file__).resolve().parent
RECOVERY_SHA = 'cad06ec2b6f9e144fea29c17061b9527d07b7df13ecbf5784fb0870d9a0ce8ca'
RECENT_STEPS = 3
STAGES = ('collect', 'keep_full', 'keep_recent', 'drop_full', 'drop_recent')
PUBLIC_KEYS = ('observation', 'score', 'done', 'won', 'action_count', 'admissible_commands')
CONTINUE = 'Continue the unfinished task.'
_REC = None


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


def prepare(root, protocol_path, protocol_sha, *, source_root=None, model_seed=17):
    root = check_root(root)
    root.mkdir(parents=True, exist_ok=True)
    if any(root.iterdir()):
        raise FileExistsError('fresh empty attempt required')
    case_id, stage, backend, _ = root.parts[-4:]
    study = protocol(protocol_path, protocol_sha)
    core = recovery().actor()
    profile = core.load_profile(backend)
    game, pool, assignment, experience = read_case(study, case_id)
    prefix = load_prefix(source_root, case_id) if source_root else None
    if (stage == 'collect') != (prefix is None):
        raise ValueError('only collection has no source prefix')
    cohort = cohort_binding(root,prefix,protocol_sha) if prefix else None
    caps = study['collection_caps'] if prefix is None else remaining_caps(study['total_caps'], prefix['receipt'])
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
    prompt = (core.condition_prompt(reset, assignment['carrier'], experience) if stage == 'collect' else
              render_prompt(reset, prefix['steps'], current, experience, stage.startswith('keep_'), stage.split('_')[1]))
    (root / 'task.txt').write_bytes(prompt.encode())
    core.write_new(root / 'opencode_config.json', core.config(profile, model_seed))
    core.write_new(root / 'initial_reset.json', reset)
    core.write_new(root / 'handoff_public.json', current)
    token_binding, _ = recovery().token_qualifier(backend, profile)
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
            'profile_sha256': core.PROFILE_PINS[backend][1], 'components': components(),
            'uid': os.getuid(), 'gid': os.getgid(), 'image_id': image,
            'inputs_sha256': {name: sha(root/name) for name in ['task.txt','opencode_config.json','initial_reset.json','handoff_public.json']},
            'development_only': True, 'ordinary_continuations': 1, 'recent_steps': RECENT_STEPS}
    core.write_new(root / 'manifest.json', manifest)
    return manifest


def verify(root, digest):
    root = check_root(root)
    if sha(root / 'manifest.json') != digest:
        raise ValueError('manifest changed')
    m = json.loads((root / 'manifest.json').read_text())
    if tuple(root.parts[-4:-1]) != (m['case_id'], m['stage'], m['backend']) or m['components'] != components():
        raise ValueError('namespace or components changed')
    study = protocol(m['protocol_path'], m['protocol_sha256'])
    game, pool, assignment, experience = read_case(study, m['case_id'])
    prefix = load_prefix(m['source_root'], m['case_id']) if m['source_root'] else None
    if prefix and m['cohort_binding'] != cohort_binding(root,prefix,m['protocol_sha256']):
        raise ValueError('shared recovery cohort changed')
    caps = study['collection_caps'] if prefix is None else remaining_caps(study['total_caps'], prefix['receipt'])
    core = recovery().actor()
    p = core.load_profile(m['backend'])
    if (m['game'] != game or m['pool_binding'] != pool or m['caps'] != caps or
            m['experience_assignment'] != assignment or m['profile_sha256'] != core.PROFILE_PINS[m['backend']][1] or
            m['source_binding'] != (prefix['binding'] if prefix else None) or
            m['sampling'] != core.model_payload({}, m['backend'], p, m['model_seed'], False if m['backend']=='student8b' else None) or
            m['model_id'] != p['model_id'] or (m['uid'],m['gid']) != (os.getuid(),os.getgid())):
        raise ValueError('frozen study inputs changed')
    for name, h in m['inputs_sha256'].items():
        if sha(root/name) != h:
            raise ValueError('frozen actor input changed')
    reset = json.loads((root/'initial_reset.json').read_text())
    current = json.loads((root/'handoff_public.json').read_text())
    expected = (core.condition_prompt(reset, assignment['carrier'], experience) if prefix is None else
                render_prompt(reset,prefix['steps'],current,experience,m['stage'].startswith('keep_'),m['stage'].split('_')[1]))
    if (root/'task.txt').read_bytes() != expected.encode() or hashlib.sha256(experience.encode()).hexdigest() != m['experience_text_sha256']:
        raise ValueError('prompt or source carrier changed')
    binding, qualify = recovery().token_qualifier(m['backend'],p)
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
    core.write_new(root/'reservation.json',{'manifest_sha256':digest,'mode':'OWNED_FAKE' if fake_endpoint else 'REAL_DEVELOPMENT'})
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
        status = 'COLLECTION_TIMEOUT' if m['stage']=='collect' else 'EPISODE_TIMEOUT'
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
    a = p.parse_args(argv)
    if a.execute:
        if not a.manifest_sha or a.protocol or a.protocol_sha or a.source_root:
            p.error('execute only accepts the frozen manifest SHA and root')
        r = run_episode(a.run_root,a.manifest_sha)
    else:
        if not a.protocol or not a.protocol_sha or not 0<=a.model_seed<2**32:
            p.error('preflight requires frozen protocol and uint32 model seed')
        r = prepare(a.run_root,a.protocol,a.protocol_sha,source_root=a.source_root,model_seed=a.model_seed)
    print(json.dumps(r))


if __name__=='__main__':
    main()
