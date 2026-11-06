"""Offline, explicitly authorized bridge from closed frozen sources to replay.

Does not run a world, rewrite old records, or calculate old remaining POSTs.
"""
from __future__ import annotations
import hashlib
import json
import math
from pathlib import Path
import re
import sys

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))
from scripts.graph import research_alfworld_bridge as bridge

ROOT = Path('/home/testuser/wzh/research_evidence/agent_learning_20261030')
SOURCE_PROTOCOL_SHA = 'fc19b701ff61ad00e4884d8bd891c2e68d36ae5b582a0a6113a89c2647fa1bde'
SOURCE_COHORT_SHA = '6188e2ea570a1dadea6109bd2b65ecda7310966e9ca658a1907b00797b49bbcd'
POOL_SHA = '5f1eb3820881d797867c8348e71559a57d339a753bb88ef5b7bf70530095be00'
PARENT_SHA = '505618debb4e6ff112a8724f22853f09d4a6dd7ba0e32123d404fe9a4da8f5e3'
BRIDGE_SHA = '37ea21a558c73068b84958ba3862c01f31c8c719f61cb011399004c0ce8bbce5'
ADDITIONAL_CAPS = dict(posts=32, seconds=600, model_payload_bytes_combined=64000000)
PUBLIC_KEYS = ('observation', 'score', 'done', 'won', 'action_count', 'admissible_commands')


def sha(path):
    result = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            result.update(chunk)
    return result.hexdigest()


def checked(path, digest):
    path = Path(path)
    if (not path.is_absolute() or path != path.resolve() or ROOT not in path.parents or
            any(p.is_symlink() for p in [path, *path.parents]) or
            not re.fullmatch('[a-f0-9]{64}', digest or '') or sha(path) != digest):
        raise ValueError('unsafe or changed recovery source file')
    return path


def document(ref):
    return json.loads(checked(ref['path'], ref['sha256']).read_text(encoding='utf8'))


def public(value):
    result = {key: value[key] for key in PUBLIC_KEYS}
    bridge.validate_response(result)
    return result


def load_source(protocol_path, protocol_sha, case_id):
    """Return study.replay_prefix-compatible data, plus a separate new-phase cap."""
    q = document(dict(path=str(protocol_path), sha256=protocol_sha))
    if (q.get('schema') != 'ALFWORLD_ADDITIONAL_RECOVERY_V1' or
            q.get('allow_frozen_ordinary_reset_sources') is not True or
            q.get('additional_caps') != ADDITIONAL_CAPS or q.get('world_step_cap') != 100):
        raise ValueError('new protocol must explicitly authorize this source and additional budget')
    if q['source_protocol']['sha256'] != SOURCE_PROTOCOL_SHA or q['source_cohort']['sha256'] != SOURCE_COHORT_SHA:
        raise ValueError('unapproved historical protocol/cohort')
    old, cohort = document(q['source_protocol']), document(q['source_cohort'])
    if (len(old['case_ids']) != 16 or len(set(old['case_ids'])) != 16 or case_id not in old['case_ids'] or
            old['pool_sha256'] != POOL_SHA or [r['case'] for r in cohort['cases']] != old['case_ids'] or
            any(r['arm'] != 'frozen' or r['status'] != 'RECORDED' for r in cohort['cases'])):
        raise ValueError('not the closed common-HF frozen16 cohort')
    row = next(r for r in cohort['cases'] if r['case'] == case_id)
    source = q['source_bindings'][case_id]
    root = Path(source['root'])
    if str(root) != row['root'] or tuple(root.parts[-4:]) != (case_id, 'ordinary_reset', 'student8b', 'attempt_v2'):
        raise ValueError('source root/stage differs from the explicitly approved frozen attempt')
    if row['won'] is not False or source['receipt_sha256'] != row['receipt_sha256']:
        raise ValueError('source is not an approved frozen failure')
    names = ('manifest.json', 'receipt.json', 'execute_world.jsonl', 'reservation.json')
    keys = ('manifest_sha256', 'receipt_sha256', 'execute_world_sha256', 'reservation_sha256')
    paths = {name: checked(root/name, source[key]) for name, key in zip(names, keys)}
    m, r, reservation = [json.loads(paths[n].read_text(encoding='utf8')) for n in (names[0], names[1], names[3])]
    profile = m['runtime_profile_override']['profile']
    runtime = m['runtime_profile_override']['runtime_admission']
    if ((m['case_id'], m['stage'], m['backend'], m['model_seed'], m['world_seed']) !=
            (case_id, 'ordinary_reset', 'student8b', 17, 17) or m['protocol_sha256'] != SOURCE_PROTOCOL_SHA or
            m['protocol_path'] != q['source_protocol']['path'] or m['caps'] != old['total_caps'] or
            m.get('source_root') is not None or m.get('reference_context') is not None or
            m['pool_binding']['sha256'] != POOL_SHA or m['world_step_cap'] != 100 or
            profile['variant'] != 'frozen' or profile['gguf_sha256'] != PARENT_SHA or runtime['active_lora'] is not None):
        raise ValueError('source model/pool/stage is not the frozen no-experience policy')
    if (r.get('status') not in {'RETURNED', 'EPISODE_TIMEOUT'} or
            r['label'] != 'MULTITASK_CONTEXT_DEVELOPMENT' or reservation['mode'] != 'REAL_DEVELOPMENT' or
            reservation['manifest_sha256'] != source['manifest_sha256'] or r['manifest_sha256'] != source['manifest_sha256'] or
            type(r['real_model_calls']) is not int or type(r['forwarded_model_posts']) is not int or
            not 0 < r['real_model_calls'] == r['forwarded_model_posts'] or
            r['unknown_usage_model_posts'] != 0 or r['won'] is not False or r['errors']):
        raise ValueError('fake, incomplete-accounted or successful source')
    if any(reservation['runtime_identity'].get(k) != v for k, v in runtime['process'].items()):
        raise ValueError('source reservation/runtime identity differs')
    for key in ('model_posts', 'model_request_payload_bytes', 'model_response_wire_bytes'):
        if type(r[key]) is not int or r[key] < 0:
            raise ValueError('invalid historical formation cost')
    if (not r['real_model_calls'] <= r['model_posts'] <= m['caps']['posts'] or
            r['model_request_payload_bytes'] + r['model_response_wire_bytes'] > m['caps']['model_payload_bytes_combined'] or
            type(r['elapsed_seconds']) not in (int, float) or
            not math.isfinite(r['elapsed_seconds']) or r['elapsed_seconds'] < 0):
        raise ValueError('invalid historical formation cost')
    events = [json.loads(line) for line in paths['execute_world.jsonl'].read_text(encoding='utf8').splitlines()]
    meta = events[0]
    if (meta['event'] != 'episode' or meta['game_id'] != case_id or meta['seed'] != 17 or meta['step_cap'] != 100 or
            meta['asset_sha256'] != m['game']['sha256_game'] or meta['pool_manifest_sha256'] != POOL_SHA or
            meta['bridge_sha256'] != BRIDGE_SHA or sha(bridge.__file__) != BRIDGE_SHA):
        raise ValueError('world/game/bridge source binding differs')
    resets, steps = [], []
    for event in events[1:]:
        if event['event'] == 'reset':
            if resets or steps:
                raise ValueError('duplicate or late reset')
            resets.append(public(event['state']))
        elif event['event'] == 'step':
            if len(resets) != 1:
                raise ValueError('action before the unique reset')
            state = public(event['state'])
            if state['done'] or state['won'] or state['action_count'] != len(steps)+1:
                raise ValueError('terminal, duplicate or out-of-order step')
            steps.append(dict(action=bridge.validate_request({'action': event['action']}), state=state))
    if (len(resets) != 1 or resets[0]['action_count'] != 0 or resets[0]['done'] or resets[0]['won'] or
            not 0 < len(steps) < 100 or public(r['final_world_state']) != steps[-1]['state'] or
            r['world_actions'] != len(steps) or r['total_world_action_count'] != len(steps)):
        raise ValueError('not a complete nonterminal prefix with real progress')
    reset_path = checked(root/'initial_reset.json', m['inputs_sha256']['initial_reset.json'])
    if public(json.loads(reset_path.read_text(encoding='utf8'))) != resets[0]:
        raise ValueError('public reset differs from frozen actor input')
    binding = {str(path): source[key] for (name, path), key in zip(paths.items(), keys)}
    binding.update({str(protocol_path): protocol_sha, q['source_protocol']['path']: SOURCE_PROTOCOL_SHA,
                    q['source_cohort']['path']: SOURCE_COHORT_SHA})
    prefix_sha = hashlib.sha256(json.dumps([resets[0], steps], sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()).hexdigest()
    return dict(root=root, manifest=m, receipt=r, reset=resets[0], steps=steps, binding=binding,
                public_prefix_sha256=prefix_sha, additional_caps=dict(ADDITIONAL_CAPS, world_actions=100-len(steps)),
                world_step_cap=100, budget_semantics='ADDITIONAL_PHASE_NOT_OLD_REMAINING_POSTS',
                historical_formation=dict(receipt_sha256=source['receipt_sha256'], charge_once=True,
                    ledger_scope='reuse historical formation ledger; do not charge it per recovery arm'))
