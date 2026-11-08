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
    return {key:prefix[key] for key in (*REF_KEYS, 'replay_action_count', 'visible_count')}


def load_checkpoint(study, case_id, run_root, model_seed, *, validate_public, private_root):
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
