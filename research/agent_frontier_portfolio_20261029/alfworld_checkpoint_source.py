"""Read-only checkpoint admission. Private replay and actor-visible history stay separate."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import re

STAGES = ('drop_full', 'checkpoint_current', 'drop_recent', 'goal_recent')
CAPS = dict(posts=48, seconds=900, world_actions=72, model_payload_bytes_combined=32000000)
REF_KEYS = ('checkpoint_reference', 'checkpoint_group_reference')
PUBLIC_KEYS = {'observation', 'score', 'done', 'won', 'action_count', 'admissible_commands'}
DESCRIPTOR_KEYS = {'schema','version','case_id','pool','world_seed','world_step_cap','world_replay',
    'visible_context','handoff_public','replay_action_count','visible_context_action_count','native_trace',
    'native_control_protocol','native_control_result','formation_refs','role','not_training_supervision'}
GROUP_KEYS = {'schema','version','case_id','pool','world_seed','world_step_cap','replay_action_count',
    'visible_context_action_count','handoff_public','visible_context','checkpoints','approved_runs',
    'actor_caps','scope','formation_charged_once'}


def reference(value):
    if (type(value) is not dict or set(value) != {'path','sha256'} or type(value['path']) is not str or type(value['sha256']) is not str or
            not re.fullmatch('[a-f0-9]{64}', value.get('sha256',''))):
        raise ValueError('checkpoint reference requires an exact path and SHA')
    return dict(value)


def references(study):
    present = [key in study for key in REF_KEYS]
    if not any(present):
        return None
    if not all(present) or study.get('experience_mode') != 'none':
        raise ValueError('checkpoint requires both explicit references and none experience mode')
    if any(key in study for key in ('reference_context','additional_recovery_source')):
        raise ValueError('checkpoint cannot acquire an external experience carrier')
    return {key:reference(study[key]) for key in REF_KEYS}


def metadata(prefix):
    if prefix is None or 'checkpoint_reference' not in prefix:
        return {}
    keys = (*REF_KEYS, 'replay_action_count', 'visible_count')
    if prefix.get('checkpoint_version') == 2:
        keys += ('checkpoint_version','checkpoint_source_kind')
    return {key:prefix[key] for key in keys}


def _load_v1(study, case_id, run_root, model_seed, *, validate_public, private_root):
    """No environment, model, or historical actor import; every input is re-read and hashed."""
    refs = references(study)
    if refs is None or run_root is None:
        raise ValueError('checkpoint requires its approved destination root')
    private_root = Path(private_root).resolve()
    binding = {}

    def read(ref, *, lines=False, opaque=False):
        ref = reference(ref)
        path = Path(ref['path'])
        if (not path.is_absolute() or path != path.resolve() or private_root not in path.parents or
                path.is_symlink() or any(p.is_symlink() for p in path.parents) or
                not path.is_file() or path.stat().st_nlink != 1):
            raise ValueError('unsafe checkpoint input path')
        raw = path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != ref['sha256']:
            raise ValueError('checkpoint input SHA changed')
        binding[str(path)] = ref['sha256']
        return None if opaque else [json.loads(line) for line in raw.splitlines()] if lines else json.loads(raw)

    def state(value, count):
        if (type(value) is not dict or set(value) != PUBLIC_KEYS or
                type(value['action_count']) is not int or value['action_count'] != count or
                value['done'] is not False or value['won'] is not False):
            raise ValueError('checkpoint public state must be counted and nonterminal')
        return validate_public(value)

    def trajectory(value, count):
        if type(value) is not dict or set(value) != {'reset','steps'} or len(value['steps']) != count:
            raise ValueError('checkpoint trajectory count changed')
        previous = state(value['reset'], 0)
        for index, row in enumerate(value['steps'], 1):
            if (type(row) is not dict or set(row) != {'action','state'} or
                    type(row['action']) is not str or row['action'] not in previous['admissible_commands']):
                raise ValueError('checkpoint replay must consist of legal public actions')
            previous = state(row['state'], index)
        return value

    group = read(refs['checkpoint_group_reference'])
    if (set(group) != GROUP_KEYS or group['schema'] != 'ALFWORLD_CHECKPOINT_COHORT_V1' or
            group['version'] != 1 or group['case_id'] != case_id or group['world_seed'] != 17 or
            group['world_step_cap'] != 100 or group['replay_action_count'] != 28 or
            group['visible_context_action_count'] != 21 or group['actor_caps'] != CAPS or
            any(type(v) is not int for v in group['actor_caps'].values()) or
            group['formation_charged_once'] is not True or set(group['checkpoints']) != {'a','b'}):
        raise ValueError('invalid frozen checkpoint group')
    if (study['case_ids'] != [case_id] or study['model_seeds'] != [17] or model_seed != 17 or
            study['world_seed'] != 17 or group['pool'] != {'path':study['pool_path'],'sha256':study['pool_sha256']} or
            study['collection_caps'] != dict(CAPS, world_actions=100) or study['total_caps'] != study['collection_caps']):
        raise ValueError('checkpoint study pool, seed or phase caps differ')
    pool = read(group['pool'])
    games = [row for row in pool['games'] if row['id'] == case_id]
    if len(games) != 1:
        raise ValueError('checkpoint pool case must be unique')
    game = games[0]
    read_game = reference(dict(path=game['private_game_path'],sha256=game['game_sha256']))
    # Game bytes are not JSON. Use the same strict path and hash rules without decoding.
    game_path = Path(read_game['path'])
    if (game_path != game_path.resolve() or private_root not in game_path.parents or game_path.is_symlink() or
            any(p.is_symlink() for p in game_path.parents) or not game_path.is_file() or game_path.stat().st_nlink != 1 or
            hashlib.sha256(game_path.read_bytes()).hexdigest() != read_game['sha256']):
        raise ValueError('checkpoint game changed')
    binding[str(game_path)] = read_game['sha256']
    visible = trajectory(read(group['visible_context']), 21)
    current = state(read(group['handoff_public']), 28)
    approved = group['approved_runs']
    if type(approved) is not list or len(approved) != 8:
        raise ValueError('checkpoint requires the eight fixed development slots')
    expected_roots = set()
    selected = None
    for slot in approved:
        if (set(slot) != {'id','case_id','stage','backend','model_seed','attempt','run_root','checkpoint_id','runtime_controls'} or
                slot['stage'] not in STAGES or slot['checkpoint_id'] not in ('a','b')):
            raise ValueError('invalid checkpoint slot')
        attempt = 1 if slot['checkpoint_id'] == 'a' else 2
        expected = private_root/'cases'/case_id/slot['stage']/'teacher27b'/('attempt_v'+str(attempt))
        controls = dict(native_terminal_stop=True, recent_tool_rounds=3 if slot['stage'] in ('drop_recent','goal_recent') else None)
        if (slot['id'] != slot['stage']+'_'+slot['checkpoint_id'] or slot['case_id'] != case_id or slot['backend'] != 'teacher27b' or slot['model_seed'] != 17 or
                slot['attempt'] != attempt or slot['run_root'] != str(expected) or slot['runtime_controls'] != controls or
                str(expected) in expected_roots):
            raise ValueError('checkpoint slot identity changed or repeated')
        expected_roots.add(str(expected))
        if str(run_root) == str(expected):
            selected = slot
    if (selected is None or study.get('runtime_controls') != selected['runtime_controls'] or
            refs['checkpoint_reference'] != group['checkpoints'][selected['checkpoint_id']]):
        raise ValueError('checkpoint reference does not match the approved slot')
    prefixes = {}
    for opaque, ref in group['checkpoints'].items():
        d = read(ref)
        if (set(d) != DESCRIPTOR_KEYS or d['schema'] != 'ALFWORLD_NATIVE_CHECKPOINT_V1' or d['version'] != 1 or
                any(d[key] != group[key] for key in ('case_id','pool','world_seed','world_step_cap',
                    'replay_action_count','visible_context_action_count','handoff_public','visible_context')) or
                d['role'] != 'D_CONSTRUCTED_EXPOSED_TRAIN_CONTROL_NOT_NATURAL_FAILURE' or d['not_training_supervision'] is not True):
            raise ValueError('checkpoint descriptor differs from group')
        world = trajectory(read(d['world_replay']), 28)
        if world['reset'] != visible['reset'] or world['steps'][:21] != visible['steps'] or world['steps'][-1]['state'] != current:
            raise ValueError('checkpoint visible prefix or handoff changed')
        control = read(d['native_control_protocol'])
        result = read(d['native_control_result'])
        if (control['case_id'] != case_id or control['pool_sha256'] != group['pool']['sha256'] or control['seed'] != 17 or
                result['status'] != 'DEVELOPMENT_CONTROL_PASS' or result['error'] is not None or
                result['protocol_sha256'] != d['native_control_protocol']['sha256'] or not result['checks'] or
                any(v is not True for v in result['checks'].values())):
            raise ValueError('checkpoint native control qualification changed')
        for name, key in (('manifest.json','source_manifest_sha256'),('receipt.json','source_receipt_sha256'),('execute_world.jsonl','source_trace_sha256')):
            source = Path(control['source_root'])/name
            # These formation bytes may be JSONL, and are deliberately not interpreted as a new model episode.
            source_ref = dict(path=str(source),sha256=control[key])
            read(source_ref, opaque=True)
        trace = read(d['native_trace'], lines=True)
        if (len(trace) < 30 or trace[0].get('event') != 'episode' or trace[0].get('case_id') != case_id or
                trace[0].get('role') != 'D_NATIVE_CONTROL_NO_AGENT' or trace[0].get('seed') != 17 or
                trace[0].get('game_sha256') != game['game_sha256'] or trace[0].get('step_cap') != 100 or
                trace[0].get('protocol_sha256') != d['native_control_protocol']['sha256'] or
                trace[1] != dict(event='reset',state=world['reset']) or
                trace[2:30] != [dict(event='step',**row) for row in world['steps']] or
                result['snapshots'].get(trace[0].get('condition','')+':after') != current):
            raise ValueError('checkpoint differs from native trace or matched handoff')
        if type(d['formation_refs']) is not list or not d['formation_refs']:
            raise ValueError('checkpoint formation references missing')
        for ref in d['formation_refs']:
            if set(ref) != {'role','path','sha256'} or ref['role'] != 'closed_source_batch':
                raise ValueError('invalid checkpoint formation role')
            read({k:ref[k] for k in ('path','sha256')})
        prefixes[opaque] = world
    world = prefixes[selected['checkpoint_id']]
    digest = hashlib.sha256(json.dumps([world['reset'],world['steps']],sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
    return dict(steps=world['steps'], reset=world['reset'], current=current, visible_steps=visible['steps'],
        binding=binding, public_prefix_sha256=digest, actor_caps=dict(CAPS), replay_action_count=28, visible_count=21, **refs)


# V2 is a separate admission contract. The V1 validator above is deliberately unchanged.
V2_STAGES = ('drop_full', 'goal_recent')
SOURCE_KINDS = ('D_CONSTRUCTED_MATCHED_CONTROL', 'REAL_CLOSED_ACTOR_FAILURE', 'REAL_CLOSED_STUDENT8B_FAILURE')
FAILURE_PROFILES = {
    'teacher27b':'9cbb51bb6dc64583cb376f81e8f8c1c28400cb494fce2793f1fa2ce60e39a279',
    'student8b':'acce24743e43c205b605b8bceddd4f5eb756d93fdba5f58e28bc32ba772ab6d0',
}
CLOSED_BATCH_SHA = 'c017c9dfb02a8d27a7d837e2544ca47aef03d641df0c56e011b5aa0c2016b86f'
CLOSED_REVIEW_SHA = 'cbedba3ee3260a1ca424d985a412427162008449a0ada3fa8d7b9209ada1fd44'
METADATA_KEYS = (*REF_KEYS, 'replay_action_count', 'visible_count', 'checkpoint_version', 'checkpoint_source_kind')
CONTROL_ROLES = {'matched_control_protocol','matched_control_result','native_trace','paired_native_trace','negative_native_trace'}
FAILURE_ROLES = {'source_manifest','source_receipt','source_reservation','source_native_trace',
                 'source_slot_closure','source_batch_closure','source_independent_review'}


def phase_caps(prefix):
    version = prefix.get('checkpoint_version', 1)
    if version == 1:
        expected = CAPS
    elif version == 2:
        count, visible = prefix['replay_action_count'], prefix['visible_count']
        if type(count) is not int or not 1 <= visible <= count <= 99:
            raise ValueError('invalid V2 checkpoint counts')
        expected = dict(CAPS, world_actions=100-count)
    else:
        raise ValueError('unknown checkpoint version')
    if prefix.get('actor_caps') != expected:
        raise ValueError('checkpoint phase caps changed')
    return dict(expected)


class _Reader:
    def __init__(self, private_root, validate_public):
        self.private = Path(private_root).resolve()
        self.validate = validate_public
        self.binding = {}

    def read(self, ref, form='json'):
        ref = reference(ref)
        path = Path(ref['path'])
        if (not path.is_absolute() or path != path.resolve() or self.private not in path.parents or
                path.is_symlink() or any(p.is_symlink() for p in path.parents) or
                not path.is_file() or path.stat().st_nlink != 1):
            raise ValueError('unsafe checkpoint input path')
        raw = path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != ref['sha256']:
            raise ValueError('checkpoint input SHA changed')
        self.binding[str(path)] = ref['sha256']
        if form == 'bytes':
            return raw
        def unique(pairs):
            value = {}
            for k,v in pairs:
                if k in value:
                    raise ValueError('duplicate checkpoint JSON key')
                value[k] = v
            return value
        return ([json.loads(line,object_pairs_hook=unique) for line in raw.splitlines()]
                if form == 'jsonl' else json.loads(raw,object_pairs_hook=unique))

    def state(self, value, count, nonterminal=True):
        if (type(value) is not dict or set(value) != PUBLIC_KEYS or
                type(value['action_count']) is not int or value['action_count'] != count or
                nonterminal and (value['done'] is not False or value['won'] is not False)):
            raise ValueError('checkpoint public state/count changed')
        return self.validate(value)

    def trajectory(self, value, count):
        if type(value) is not dict or set(value) != {'reset','steps'} or len(value['steps']) != count:
            raise ValueError('checkpoint trajectory count changed')
        previous = self.state(value['reset'], 0)
        for index,row in enumerate(value['steps'],1):
            if type(row) is not dict or set(row) != {'action','state'} or row['action'] not in previous['admissible_commands']:
                raise ValueError('checkpoint replay action was not public-admissible')
            previous = self.state(row['state'],index)
        return value

    def native(self, ref):
        rows = self.read(ref,'jsonl')
        if len(rows) < 3 or rows[0].get('event') != 'episode' or rows[1].get('event') != 'reset':
            raise ValueError('native source episode missing')
        reset = self.state(rows[1]['state'],0)
        steps = []
        previous = reset
        for count,row in enumerate(rows[2:],1):
            if (set(row) != {'event','action','state'} or row['event'] != 'step' or
                    previous['done'] or row['action'] not in previous['admissible_commands'] or count > 100):
                raise ValueError('native source is not a complete accepted action sequence')
            previous = self.state(row['state'],count,False)
            steps.append(dict(action=row['action'],state=previous))
        return rows[0],dict(reset=reset,steps=steps)


def _roles(descriptor, expected):
    values = descriptor['provenance']
    if (type(values) is not list or any(type(x) is not dict or set(x) != {'role','path','sha256'} for x in values) or
            len(values) != len(expected) or {x['role'] for x in values} != expected):
        raise ValueError('missing, duplicate or unknown checkpoint provenance role')
    return {x['role']:reference({k:x[k] for k in ('path','sha256')}) for x in values}


def _closed_failure(reader, refs, group, world, game, *, source_backend='teacher27b'):
    if source_backend not in FAILURE_PROFILES:
        raise ValueError('unsupported closed source backend')
    if refs['source_batch_closure']['sha256'] != CLOSED_BATCH_SHA or refs['source_independent_review']['sha256'] != CLOSED_REVIEW_SHA:
        raise ValueError('unapproved source closure/review')
    m,r,res,slot,batch,review = [reader.read(refs[k]) for k in (
        'source_manifest','source_receipt','source_reservation','source_slot_closure','source_batch_closure','source_independent_review')]
    root = Path(refs['source_manifest']['path']).parent
    case = group['case_id']
    for role,name in (('source_manifest','manifest.json'),('source_receipt','receipt.json'),
                      ('source_reservation','reservation.json'),('source_native_trace','execute_world.jsonl')):
        if Path(refs[role]['path']) != root/name:
            raise ValueError('source files must belong to one actual root')
    if (root.parts[-4:-1] != (case,'collect_none',source_backend) or
            any(x.get('case_id') != case or x.get('stage') != 'collect_none' or x.get('backend') != source_backend for x in (m,r)) or
            m.get('world_seed') != 17 or m.get('model_seed') != 17 or m.get('world_step_cap') != 100 or
            m.get('source_root') is not None or m.get('experience_mode') != 'none' or m.get('experience_assignment') != {} or
            m.get('experience_text_sha256') != hashlib.sha256(b'').hexdigest() or
            any(k in m for k in ('reference_context','additional_recovery_source','checkpoint_reference')) or
            r.get('experience_mode') != 'none' or r.get('label') != 'MULTITASK_CONTEXT_DEVELOPMENT' or
            res.get('mode') != 'REAL_DEVELOPMENT' or res.get('experience_mode') != 'none' or
            res.get('manifest_sha256') != refs['source_manifest']['sha256'] or r.get('manifest_sha256') != res['manifest_sha256'] or
            m['pool_binding']['path'] != group['pool']['path'] or m['pool_binding']['sha256'] != group['pool']['sha256'] or
            m['game']['sha256_game'] != game['game_sha256'] or
            m.get('profile_sha256') != FAILURE_PROFILES[source_backend]):
        raise ValueError('source is not this real none/teacher collection' if source_backend == 'teacher27b'
                         else 'source is not this real none/student8b collection')
    old_protocol = reader.read(dict(path=m['protocol_path'],sha256=m['protocol_sha256']))
    if (old_protocol.get('experience_mode') != 'none' or old_protocol['pool_path'] != group['pool']['path'] or
            old_protocol['pool_sha256'] != group['pool']['sha256'] or case not in old_protocol['case_ids'] or
            old_protocol['world_seed'] != 17 or old_protocol['collection_caps'] != m['caps']):
        raise ValueError('original source protocol differs')
    header,actual = reader.native(refs['source_native_trace'])
    frozen = dict(header);episode_sha = frozen.pop('episode_sha256',None);frozen.pop('event',None)
    if (hashlib.sha256(json.dumps(frozen,sort_keys=True).encode()).hexdigest() != episode_sha or
            header.get('game_id') != case or header.get('asset_sha256') != game['game_sha256'] or header.get('seed') != 17 or
            header.get('pool_manifest_sha256') != group['pool']['sha256'] or header.get('caps') != m['caps'] or header.get('step_cap') != 100 or
            actual != world or r.get('final_world_state') != world['steps'][-1]['state'] or r.get('won') is not False or
            r.get('world_actions') != len(world['steps']) or r.get('total_world_action_count') != len(world['steps']) or r.get('errors') != []):
        raise ValueError('source native state/count differs')
    if (batch.get('schema') != 'D_TRAIN12_SOURCE_COLLECTION_CLOSURE_V1' or batch.get('status') != 'ALL24_CLOSED_AND_RAW_RECHECKED' or
            batch.get('independent_result_review') != refs['source_independent_review'] or
            review.get('schema') != 'C_SOURCE_COLLECTION_RESULT_REVIEW_V1' or review.get('verdict') != 'PASS_WITH_ACCOUNTING_LIMITS' or
            review.get('blocking_findings') != [] or slot.get('can_continue') is not True or slot.get('task_won') is not False or
            slot.get('task_won_known') is not True or slot.get('reasons') != []):
        raise ValueError('source is not an independently closed failure')
    drows = [x for x in batch['rows'] if x['root'] == str(root)]
    crows = [x for x in review['per_slot_independent_results'] if x['root'] == str(root)]
    if len(drows) != 1 or len(crows) != 1:
        raise ValueError('source closure slot is missing or ambiguous')
    d,c = drows[0],crows[0]
    if (d['case_id'] != case or c['case'] != case or d['backend'] != source_backend or c['backend'] != source_backend or
            d['slot'] != c['slot'] or d['manifest_sha256'] != refs['source_manifest']['sha256'] or
            c['manifest_sha256'] != d['manifest_sha256'] or d['receipt_sha256'] != refs['source_receipt']['sha256'] or
            c['receipt_sha256'] != d['receipt_sha256'] or d['closure_sha256'] != refs['source_slot_closure']['sha256'] or
            c['closure_sha256'] != d['closure_sha256'] or c['native_sha256'] != refs['source_native_trace']['sha256'] or
            d['native_won'] is not False or c['won'] is not False or c['done'] is not False or
            d['native_actions'] != len(world['steps']) or c['actions'] != len(world['steps']) or
            d['classification'] != slot['classification'] or slot['native_witness']['state'] != r['final_world_state'] or
            slot['native_witness']['path'] != refs['source_native_trace']['path'] or
            slot['native_witness']['sha256'] != refs['source_native_trace']['sha256'] or slot['native_witness']['episode_sha256'] != episode_sha):
        raise ValueError('source slot/native hashes differ')
    ac = slot['accounting'];calls = r.get('real_model_calls')
    if (type(calls) is not int or calls <= 0 or r.get('unknown_usage_model_posts') != 0 or
            any(x != calls for x in (r['model_posts'],r['forwarded_model_posts'],ac['actual_forwarded_posts'],ac['reserved_posts'],
                ac['real_model_calls'],c['posts'],c['reserved_posts'])) or ac['unknown_usage_calls'] != 0 or c['unknown_usage_calls'] != 0 or
            ac['unexplained_reserved_not_forwarded'] != 0 or d['accounting'] != ac or
            calls > m['caps']['posts'] or r['elapsed_seconds'] > m['caps']['seconds'] or
            r['model_request_payload_bytes'] + r['model_response_wire_bytes'] > m['caps']['model_payload_bytes_combined']):
        raise ValueError('source has unknown or inconsistent total costs')
    usage = dict(prompt_tokens=0,completion_tokens=0,total_tokens=0)
    if len(r['response_receipts']) != calls:
        raise ValueError('source response coverage incomplete')
    for response in r['response_receipts']:
        u = response.get('usage',{})
        if (response.get('complete') is not True or any(type(u.get(k)) is not int or u[k] < 0 for k in usage) or
                u['total_tokens'] != u['prompt_tokens'] + u['completion_tokens']):
            raise ValueError('source provider totals unknown')
        for k in usage:usage[k] += u[k]
    if (usage != r['provider_usage'] or usage != ac['provider_usage_known'] or usage != c['provider_usage_known'] or
            r['model_request_payload_bytes'] != ac['request_payload_bytes'] or c['request_bytes'] != ac['request_payload_bytes'] or
            r['model_response_wire_bytes'] != ac['response_wire_bytes'] or c['response_wire_bytes'] != ac['response_wire_bytes']):
        raise ValueError('source closed physical accounting differs')
    cap_error = [{'type':'ValueError','detail':'episode model budget closed'}]
    for item in r['rounds']:
        raw_ref = dict(path=str(root/('raw_'+str(item['round'])+'.jsonl')),sha256=item['raw_sha256'])
        errors = [x for x in reader.read(raw_ref,'jsonl') if x.get('type') == 'error']
        if item['exit'] not in (0,1) or item['exit'] == 1 and not errors:
            raise ValueError('source round was an unqualified runtime fault')
        for error in errors:
            e = error.get('error',{})
            if (e.get('name') != 'APIError' or e.get('data',{}).get('statusCode') != 403 or
                    r['model_relay_errors'] != cap_error or calls != m['caps']['posts'] or slot['classification'] != 'POST_CAP_CLOSED'):
                raise ValueError('source has an opaque raw error')
    if r['model_relay_errors'] not in ([],cap_error):
        raise ValueError('source has an unexplained relay error')
    # These historical files are bound by the original gate, not by today's source code.
    for path,digest in slot['bindings'].items():
        if root not in Path(path).parents:
            raise ValueError('source gate binding escapes its original root')
        reader.read(dict(path=path,sha256=digest),'bytes')
    for role in ('source_manifest','source_receipt','source_reservation'):
        if slot['bindings'].get(refs[role]['path']) != refs[role]['sha256']:
            raise ValueError('source gate does not bind original files')


def _matched_control(reader, refs, group, world, visible, game):
    p = reader.read(refs['matched_control_protocol']);result = reader.read(refs['matched_control_result'])
    if (p.get('schema') != 'NEXTDEV_LOOK01_NATIVE_MATCHED_V1' or p['case_id'] != group['case_id'] or p['seed'] != 17 or
            p['pool'] != group['pool'] or p['game'] != dict(path=game['private_game_path'],sha256=game['game_sha256']) or
            p['visible_count'] != len(visible['steps']) or p['handoff_action_count'] != len(world['steps']) or
            p['maximum_worlds'] != 3 or p['maximum_actions_per_world'] != 100 or
            result.get('status') != 'NATIVE_MATCHED_CONTROL_PASS' or result.get('error') is not None or
            result.get('unstarted') != [] or result['protocol_sha256'] != refs['matched_control_protocol']['sha256'] or
            result['code_sha256'] != p['code']['sha256'] or result['actual_worlds_started'] != 3 or
            any(result.get(k) != 0 or p.get(k) != 0 for k in ('models','HTTP','Docker','training'))):
        raise ValueError('unqualified constructed matched-control provenance')
    reader.read(p['code'],'bytes')
    teacher = reader.read(p['source_receipt']);source_header,old = reader.native(p['source_trace'])
    source_root = Path(p['source_receipt']['path']).parent
    original_manifest = reader.read(dict(path=str(source_root/'manifest.json'),sha256=teacher['manifest_sha256']))
    if (source_root.parts[-4:-1] != (group['case_id'],'collect_none','teacher27b') or
            original_manifest.get('case_id') != group['case_id'] or original_manifest.get('backend') != 'teacher27b' or
            original_manifest.get('stage') != 'collect_none' or original_manifest.get('experience_mode') != 'none' or
            original_manifest.get('world_seed') != 17 or original_manifest.get('model_seed') != 17 or
            original_manifest['pool_binding']['path'] != group['pool']['path'] or original_manifest['pool_binding']['sha256'] != group['pool']['sha256'] or
            source_header.get('game_id') != group['case_id'] or source_header.get('asset_sha256') != game['game_sha256'] or
            source_header.get('pool_manifest_sha256') != group['pool']['sha256'] or source_header.get('seed') != 17):
        raise ValueError('constructed control teacher case, pool or seed differs')
    if (teacher.get('case_id') != group['case_id'] or teacher.get('backend') != 'teacher27b' or
            teacher.get('stage') != 'collect_none' or teacher.get('won') is not True or
            teacher.get('unknown_usage_model_posts') != 0 or type(teacher.get('real_model_calls')) is not int or teacher['real_model_calls'] <= 0 or
            teacher.get('real_model_calls') != teacher.get('forwarded_model_posts') or
            teacher['final_world_state'] != old['steps'][-1]['state'] or
            hashlib.sha256(json.dumps([old['reset'],old['steps'][:4]],sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest() != p['source_prefix_sha256'] or
            p['source_prefix_actions'] != [x['action'] for x in old['steps'][:4]]):
        raise ValueError('constructed control is not bound to the real teacher prefix')
    screen = reader.read(p['source_screen'])
    found = [x for x in screen['rows'] if x['case_id'] == group['case_id']]
    if len(found) != 1 or any(found[0][k] != p[k] for k in ('source_receipt','source_trace')):
        raise ValueError('constructed teacher source screen differs')
    if len(p['conditions']) != 3 or len(result['conditions']) != 3:
        raise ValueError('matched control must bind all three native branches')
    controls = {}
    positives = []
    for condition,record in zip(p['conditions'],result['conditions']):
        if (type(condition['lamp_on']) is not bool or type(condition['expected_won']) is not bool or
                record['id'] != condition['id'] or record.get('error') is not None or record.get('cleanup_error') is not None):
            raise ValueError('matched native branch failed')
        header,trace = reader.native(record['trace'])
        replay = len(world['steps']);vcount = len(visible['steps'])
        prefix = list(p['source_prefix_actions'])
        if not condition['lamp_on']:prefix[2] = 'look'
        witness = [x.replace('<actual_paper_location>',condition['actual_paper_location']) for x in p['witness_template']]
        expected = prefix + p['common_visible_extension'] + condition['intervention'] + witness
        if (header.get('case_id') != group['case_id'] or header.get('seed') != 17 or header.get('game_sha256') != game['game_sha256'] or
                header.get('protocol_sha256') != refs['matched_control_protocol']['sha256'] or header.get('condition') != condition['id'] or
                [x['action'] for x in trace['steps']] != expected or len(trace['steps']) != record['accepted_actions'] or
                trace['reset'] != old['reset'] or record['before_intervention'] != trace['steps'][vcount-1]['state'] or
                record['handoff'] != trace['steps'][replay-1]['state'] or record['final'] != trace['steps'][-1]['state'] or
                record['final']['won'] is not condition['expected_won'] or condition['expected_won'] is not condition['lamp_on'] or
                any(x['state']['done'] or x['state']['won'] for x in trace['steps'][:-1])):
            raise ValueError('matched protocol, public trace or native witness differs')
        if condition['lamp_on']:
            if trace['steps'][:4] != old['steps'][:4]:
                raise ValueError('positive visible prefix differs from original teacher')
            positives.append(record['trace'])
        controls[record['trace']['path']] = trace
    if (len(positives) != 2 or refs['native_trace'] not in positives or refs['paired_native_trace'] not in positives or
            refs['native_trace'] == refs['paired_native_trace'] or refs['negative_native_trace'] in positives or
            refs['negative_native_trace'] not in [x['trace'] for x in result['conditions']]):
        raise ValueError('checkpoint must select a genuine positive paired branch')
    selected,paired = controls[refs['native_trace']['path']],controls[refs['paired_native_trace']['path']]
    count = len(world['steps'])
    if (world != dict(reset=selected['reset'],steps=selected['steps'][:count]) or
            visible != dict(reset=selected['reset'],steps=selected['steps'][:len(visible['steps'])]) or
            selected['steps'][:len(visible['steps'])] != paired['steps'][:len(visible['steps'])] or
            selected['steps'][count-1]['state'] != paired['steps'][count-1]['state']):
        raise ValueError('constructed replay, visible prefix or matched handoff differs')


def load_checkpoint(study, case_id, run_root, model_seed, *, validate_public, private_root):
    refs = references(study)
    if refs is None or run_root is None:
        raise ValueError('checkpoint requires approved references/root')
    reader = _Reader(private_root,validate_public)
    group = reader.read(refs['checkpoint_group_reference'])
    if group.get('schema') == 'ALFWORLD_CHECKPOINT_COHORT_V1':
        return _load_v1(study,case_id,run_root,model_seed,validate_public=validate_public,private_root=private_root)
    if (set(group) != GROUP_KEYS | {'source_kind'} or group['schema'] != 'ALFWORLD_CHECKPOINT_COHORT_V2' or
            type(group['version']) is not int or group['version'] != 2 or group['case_id'] != case_id or
            group['source_kind'] not in SOURCE_KINDS or group['world_seed'] != 17 or group['world_step_cap'] != 100 or
            type(group['replay_action_count']) is not int or type(group['visible_context_action_count']) is not int or
            not 1 <= group['visible_context_action_count'] <= group['replay_action_count'] <= 99 or
            set(group['checkpoints']) not in ({'a'},{'a','b'}) or group['formation_charged_once'] is not True):
        raise ValueError('invalid explicit V2 checkpoint cohort')
    count,visible_count = group['replay_action_count'],group['visible_context_action_count']
    caps = dict(CAPS,world_actions=100-count)
    if (group['actor_caps'] != caps or any(type(v) is not int for v in group['actor_caps'].values()) or
            study['case_ids'] != [case_id] or study['world_seed'] != 17 or study['model_seeds'] != [17] or model_seed != 17 or
            group['pool'] != dict(path=study['pool_path'],sha256=study['pool_sha256']) or
            study['collection_caps'] != dict(caps,world_actions=100) or study['total_caps'] != study['collection_caps']):
        raise ValueError('V2 pool, seed or independent phase caps differ')
    pool = reader.read(group['pool']);games = [x for x in pool['games'] if x['id'] == case_id]
    if len(games) != 1:raise ValueError('V2 pool case is ambiguous')
    game = games[0];reader.read(dict(path=game['private_game_path'],sha256=game['game_sha256']),'bytes')
    visible = reader.trajectory(reader.read(group['visible_context']),visible_count)
    current = reader.state(reader.read(group['handoff_public']),count)
    approved = group['approved_runs'];expected = set();chosen = None
    if type(approved) is not list or len(approved) != 2*len(group['checkpoints']):
        raise ValueError('V2 slots must enumerate the two policies for every checkpoint')
    for slot in approved:
        if (set(slot) != {'id','case_id','stage','backend','model_seed','attempt','run_root','checkpoint_id','runtime_controls'} or
                slot['stage'] not in V2_STAGES or slot['checkpoint_id'] not in group['checkpoints']):
            raise ValueError('unknown V2 slot')
        opaque = slot['checkpoint_id'];attempt = 1 if opaque == 'a' else 2
        root = Path(private_root)/'cases'/case_id/slot['stage']/'teacher27b'/('attempt_v'+str(attempt))
        controls = dict(native_terminal_stop=True,recent_tool_rounds=3 if slot['stage']=='goal_recent' else None)
        key = slot['stage'],opaque
        if (key in expected or slot['id'] != slot['stage']+'_'+opaque or slot['run_root'] != str(root) or
                slot['case_id'] != case_id or slot['backend'] != 'teacher27b' or slot['model_seed'] != 17 or
                type(slot['attempt']) is not int or slot['attempt'] != attempt or slot['runtime_controls'] != controls or
                slot['runtime_controls'].get('native_terminal_stop') is not True or
                (slot['stage'] == 'goal_recent' and type(slot['runtime_controls'].get('recent_tool_rounds')) is not int)):
            raise ValueError('V2 slot identity, pairing or runtime controls differ')
        expected.add(key)
        if str(root) == str(run_root):chosen = slot
    if (expected != {(s,c) for s in V2_STAGES for c in group['checkpoints']} or chosen is None or
            study['runtime_controls'] != chosen['runtime_controls'] or refs['checkpoint_reference'] != group['checkpoints'][chosen['checkpoint_id']]):
        raise ValueError('V2 destination is not the approved paired slot')
    prefixes = {};common_provenance = None;native_refs = []
    descriptor_keys = (DESCRIPTOR_KEYS - {'native_trace','native_control_protocol','native_control_result','formation_refs','role'}) | {'source_kind','provenance'}
    for opaque,ref in group['checkpoints'].items():
        d = reader.read(ref)
        if (set(d) != descriptor_keys or d['schema'] != 'ALFWORLD_NATIVE_CHECKPOINT_V2' or type(d['version']) is not int or d['version'] != 2 or
                d['source_kind'] != group['source_kind'] or d['not_training_supervision'] is not True or
                any(d[k] != group[k] for k in ('case_id','pool','world_seed','world_step_cap','replay_action_count',
                    'visible_context_action_count','handoff_public','visible_context'))):
            raise ValueError('V2 descriptor is not this cohort')
        world = reader.trajectory(reader.read(d['world_replay']),count)
        if world['reset'] != visible['reset'] or world['steps'][:visible_count] != visible['steps'] or world['steps'][-1]['state'] != current:
            raise ValueError('V2 visible history or current state differs')
        if d['source_kind'] in ('REAL_CLOSED_ACTOR_FAILURE','REAL_CLOSED_STUDENT8B_FAILURE'):
            provenance = _roles(d,FAILURE_ROLES)
            if count != visible_count or world != visible:
                raise ValueError('real failure must retain all actual accepted source history')
            if d['source_kind'] == 'REAL_CLOSED_STUDENT8B_FAILURE':
                _closed_failure(reader,provenance,group,world,game,source_backend='student8b')
            else:
                _closed_failure(reader,provenance,group,world,game)
            common = provenance
        else:
            provenance = _roles(d,CONTROL_ROLES)
            _matched_control(reader,provenance,group,world,visible,game)
            common = {k:v for k,v in provenance.items() if k not in {'native_trace','paired_native_trace'}}
            native_refs.append(provenance['native_trace']['path'])
        if common_provenance is not None and common_provenance != common:
            raise ValueError('V2 checkpoints swapped their common source provenance')
        common_provenance = common;prefixes[opaque] = world
    if len(native_refs) != len(set(native_refs)):
        raise ValueError('V2 matched checkpoints cannot duplicate the same branch')
    world = prefixes[chosen['checkpoint_id']]
    digest = hashlib.sha256(json.dumps([world['reset'],world['steps']],sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
    return dict(steps=world['steps'],reset=world['reset'],current=current,visible_steps=visible['steps'],
        binding=reader.binding,public_prefix_sha256=digest,actor_caps=caps,replay_action_count=count,visible_count=visible_count,
        checkpoint_version=2,checkpoint_source_kind=group['source_kind'],**refs)
