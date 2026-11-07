#!/usr/bin/env python3
"""Frozen Matplotlib target comparison; preparation never starts an actor."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import shutil

import run_contextbench_source as source

QUALIFICATION_SHA = '490dc51749892229d689312f56ef178f3bb0078c45f24b870addc3b85dd53cfe'
CONTRACT_SHA = '6723d734d33fad028a2324092ec01f84b1b7361abd71b7a6b046b51cfb38d2ce'
EVIDENCE_SHA = '1dae2bf35ea1c72a124a3ea236e1c00dd62e1ad1db734e11629ec74a3fe4c413'
TARGET = source.MPL_TARGET_ID
BASE = '3742e7e8385e70072fb2521a411a25dd69d22dbf'
ARMS = ['none', 'source_file_locator', 'full_verified_source_evidence']
SAMPLING = dict(seed=17, temperature=0.2, native_thinking=False, context=32768, output=8192)


def protocol_input(path, digest):
    p = source.read_ref(dict(path=str(path), sha256=digest))
    keys = {'schema', 'target', 'arms', 'qualification', 'qualification_contract', 'source_evidence', 'projection', 'profile', 'caps', 'sampling'}
    if (not isinstance(p, dict) or set(p) != keys or p['schema'] != 'contextbench_target_comparison_v1'
            or p['target'] != TARGET or p['arms'] != ARMS or p['sampling'] != SAMPLING
            or any(type(p['sampling'][k]) is not type(v) for k, v in SAMPLING.items())):
        raise ValueError('target protocol policy differs')
    if (not isinstance(p['caps'], dict) or set(p['caps']) != set(source.CAPS) or any(type(p['caps'][k]) is not int or not 0 < p['caps'][k] <= v for k, v in source.CAPS.items())):
        raise ValueError('target caps exceed approved limits')
    for key in ('qualification', 'qualification_contract', 'source_evidence', 'projection', 'profile'):
        ref = p[key]
        if (not isinstance(ref, dict) or set(ref) != {'path', 'sha256'} or not isinstance(ref['path'], str)
                or not isinstance(ref['sha256'], str) or not re.fullmatch('[0-9a-f]{64}', ref['sha256'])):
            raise ValueError('invalid target reference')
    for key, expected in [('qualification', QUALIFICATION_SHA), ('qualification_contract', CONTRACT_SHA), ('source_evidence', EVIDENCE_SHA)]:
        if p[key].get('sha256') != expected: raise ValueError('unapproved ' + key)
        source.read_ref(p[key])
    return p


def qualification_input(p, h):
    result = source.read_ref(p['qualification']); contract = source.read_ref(p['qualification_contract'])
    if (result.get('status') != 'QUALIFIED' or result.get('model_calls') != 0 or result.get('training') != 0
            or result.get('unrun_groups') or result.get('unrun_cases')
            or set(result.get('cases', {})) != {source.MPL_SOURCE_ID, TARGET}
            or result.get('input_sha256', {}).get(p['qualification_contract']['path']) != p['qualification_contract']['sha256']):
        raise ValueError('incomplete target qualification')
    for identity, base, role, count in [(source.MPL_SOURCE_ID, '66ba515e671638971bd11a34cff12c107a437e0b', 'source', 181), (TARGET, BASE, 'target', 60)]:
        case = result['cases'][identity]; spec = case['spec']; labels = case['labels']
        if (spec['instance_id'], spec['repo'], spec['base_commit'], spec['role']) != (identity, 'matplotlib/matplotlib', base, role):
            raise ValueError('qualified case identity differs')
        if set(labels) != {'f2p', 'ptp'} or (len(labels['f2p']), len(labels['ptp'])) != (1, count):
            raise ValueError('qualified case labels differ')
        flat = labels['f2p'] + labels['ptp']
        if len(set(flat)) != len(flat) or any(not n.startswith('lib/matplotlib/tests/') for n in flat):
            raise ValueError('duplicate or foreign evaluation nodes')
        groups = [case['arms'][a]['group'] for a in ('base_with_tests', 'gold_with_tests')]
        computed = h.pool.matplotlib_qualification(*groups, labels)
        if computed != case['qualification'] or computed['qualified'] is not True:
            raise ValueError('native qualification incomplete')
        parent = source.safe(p['qualification']['path']).parent / identity
        for arm, group in zip(('base_with_tests', 'gold_with_tests'), groups):
            log = source.safe(parent / (arm + '.log'))
            markers = [z[len(h.pool.MARKER):] for z in log.read_text().splitlines() if z.startswith(h.pool.MARKER)]
            if source.sha(log) != group['log_sha256'] or len(markers) != 1 or json.loads(markers[0]) != group['result']:
                raise ValueError('native qualification log differs')
    case = result['cases'][TARGET]; parent = source.safe(p['qualification']['path']).parent / TARGET
    if source.tree(parent / 'clean_base') != case['clean_base_sha256']:
        raise ValueError('qualified clean target changed')
    for name in ('task.txt', 'test.patch'):
        if source.sha(source.safe(parent / name)) != case['input_sha256'][name]: raise ValueError('target public input changed')
    if p['projection'] != dict(path=str(Path(contract['runtime']['projection']['path']).parent), sha256=contract['runtime']['projection']['sha256']):
        raise ValueError('target projection differs from qualification')
    return result, case, parent


def source_locator(evidence):
    """Derive only production file paths from the source patch's exact headers."""
    patch = evidence['source_reference_patch']; paths = []
    for left, right in re.findall(r'^diff --git a/(\S+) b/(\S+)$', patch, re.MULTILINE):
        p = PurePosixPath(right)
        if (left != right or p.is_absolute() or '..' in p.parts or '\\' in right
                or not right.startswith('lib/matplotlib/') or p.suffix != '.py'
                or any(z in ('tests', 'testing') for z in p.parts)
                or not re.search(r'^--- a/' + re.escape(left) + r'\n\+\+\+ b/' + re.escape(right) + r'\n', patch, re.MULTILINE)):
            raise ValueError('source locator requires exact production paths')
        paths.append(right)
    if not paths or len(paths) != len(set(paths)): raise ValueError('missing/duplicate source production paths')
    return paths


def evidence_input(p, result):
    e = source.read_ref(p['source_evidence']); case = result['cases'][source.MPL_SOURCE_ID]
    if (e.get('schema'), e.get('source_id'), e.get('source_repo'), e.get('source_base_commit')) != (
            'reference_assisted_source_evidence_v1', source.MPL_SOURCE_ID, 'matplotlib/matplotlib', case['spec']['base_commit']):
        raise ValueError('source evidence identity differs')
    for key, name in [('source_task', 'task.txt'), ('source_reference_patch', 'reference.patch')]:
        if not isinstance(e.get(key), str) or hashlib.sha256(e[key].encode()).hexdigest() != case['input_sha256'][name]:
            raise ValueError('source evidence bytes differ from qualified source')
    if e.get('native_control') != dict(base_f2p_failed=1, base_ptp_passed=181, reference_f2p_passed=1, reference_ptp_passed=181):
        raise ValueError('source evidence controls differ')
    source_locator(e)
    return e


def render_prompt(public, evidence, evidence_bytes, arm):
    if arm not in ARMS: raise ValueError('unknown target arm')
    prompt = ('Implement the requested target change in /workspace and run relevant tests. Python 3.10 '
        'and dependencies are offline. Do not ask for permission to continue. The task below is reproduced verbatim.\n\n' + public)
    if arm == 'source_file_locator':
        prompt += '\n\nSource production file paths:\n' + '\n'.join(source_locator(evidence))
    elif arm == 'full_verified_source_evidence':
        prompt += '\n\nVerified source-only reference-assisted evidence:\n' + evidence_bytes
    return prompt


def projection_input(p, h):
    actor = h.deps.verify_projection(source.safe(p['projection']['path']), p['projection']['sha256'])
    m = source.read_ref(dict(path=str(Path(p['projection']['path']) / 'manifest.json'), sha256=p['projection']['sha256']))
    if (m['python'], m['blocked_packages'], m['site_names'], set(actor['sites'])) != ('3.10', ['matplotlib', 'mpl_toolkits'], ['source', 'target'], {'source', 'target'}):
        raise ValueError('target dependency surface differs')
    return {**actor, 'sites': {'default': actor['sites']['target']}}


def scorer_input(p, h):
    contract = source.read_ref(p['qualification_contract']); bindings = {}
    h.pool.matplotlib_assets(contract['runtime'], bindings)
    return dict(bindings=bindings, limits='Exact qualified Python3.10 target projection and native overlay', matplotlib_runtime=contract['runtime'])


def admitted(protocol_path, protocol_sha, arm):
    if arm not in ARMS: raise ValueError('unknown target arm')
    p = protocol_input(protocol_path, protocol_sha); h = source.helpers()
    result, case, parent = qualification_input(p, h); evidence = evidence_input(p, result)
    actor = projection_input(p, h); profile = source.profile_input(p['profile']['path'], p['profile']['sha256'], h)
    scorer = scorer_input(p, h)
    public = (parent / 'task.txt').read_bytes().decode('utf8')
    prompt = render_prompt(public, evidence, Path(p['source_evidence']['path']).read_bytes().decode('utf8'), arm)
    return p, h, case, parent, actor, profile, scorer, prompt


def metadata(protocol_path, protocol_sha, arm, root, p, case, scorer):
    return dict(schema='contextbench_target_v1', tool_contract=source.tool_contract_policy(), root=str(root), target=TARGET, arm=arm,
        protocol=dict(path=str(protocol_path), sha256=protocol_sha), qualification=p['qualification'], qualification_contract=p['qualification_contract'],
        source_evidence=p['source_evidence'], repo=case['spec']['repo'], base=case['spec']['base_commit'], labels=case['labels'],
        scorer_dependencies=scorer, projection=p['projection'], profile=p['profile'], caps=p['caps'], sampling=p['sampling'],
        source_runtime=source.MPL_SOURCE_RUNTIME, scoring_slot='target', native_overlay=case['native_overlay'],
        public_task_sha256=case['input_sha256']['task.txt'], test_patch_sha256=case['input_sha256']['test.patch'],
        boundary='target clean/public task and explicit source evidence only; qualification/test patches/target reference never actor mounts',
        status='CPU_PREPARED', models_called=0, container_runs=0)


def prepare(protocol_path, protocol_sha, arm, root):
    p, h, case, parent, actor, profile, scorer, prompt = admitted(protocol_path, protocol_sha, arm)
    root = source.safe(root)
    refs = [Path(p['qualification']['path']).parent, Path(p['projection']['path']), Path(p['source_evidence']['path']), Path(protocol_path)]
    if (source.PRIVATE not in root.parents or root.exists()
            or any(root == x or root in x.parents or x in root.parents for x in refs)):
        raise ValueError('fresh disjoint private target root required')
    h.tools.ripgrep_binding(); binaries = {str(source.safe(x)): source.sha(x) for x in (h.tools.OPENCODE, h.tools.RG)}
    root.mkdir(mode=0o700, parents=True)
    shutil.copytree(parent / 'clean_base', root / 'baseline'); shutil.copytree(root / 'baseline', root / 'work')
    for f in (root / 'work').rglob('*'):
        if f.is_file(): f.chmod(f.stat().st_mode | 0o200)
    inputs = root / 'inputs'; inputs.mkdir(); (root / 'scoring').mkdir()
    shutil.copyfile(parent / 'task.txt', inputs / 'public_task.txt')
    (inputs / 'task.txt').write_bytes(prompt.encode()); (inputs / 'guest.py').write_bytes(source.GUEST.encode())
    source.new(inputs / 'opencode.json', h.actor.config(profile, 17))
    shutil.copyfile(parent / 'test.patch', root / 'scoring/test.patch')
    m = metadata(protocol_path, protocol_sha, arm, root, p, case, scorer)
    m.update(baseline=source.tree(root / 'baseline'), work=source.tree(root / 'work'), inputs=source.tree(inputs),
        wrapped_prompt_sha256=source.sha(inputs / 'task.txt'), components=source.components(), binaries=binaries)
    source.new(root / 'manifest.json', m)
    return dict(status='CPU_PREPARED', root=str(root), target=TARGET, arm=arm, manifest_sha256=source.sha(root / 'manifest.json'))


def verify(root, digest, *, initial=True):
    root = source.safe(root); m = source.read_ref(dict(path=str(root / 'manifest.json'), sha256=digest))
    p, h, case, parent, actor, profile, scorer, prompt = admitted(m['protocol']['path'], m['protocol']['sha256'], m['arm'])
    expected = metadata(m['protocol']['path'], m['protocol']['sha256'], m['arm'], root, p, case, scorer)
    extra = {'baseline', 'work', 'inputs', 'wrapped_prompt_sha256', 'components', 'binaries'}
    if set(m) != set(expected) | extra or any(m[k] != v for k, v in expected.items()): raise ValueError('target manifest policy differs')
    if not initial: source.tree(root / 'work')  # Editable bytes may change; linked surfaces may not.
    for name in (('baseline', 'work', 'inputs') if initial else ('baseline', 'inputs')):
        if source.tree(root / name) != m[name]: raise ValueError('prepared target ' + name + ' changed')
    if (m['baseline'] != case['clean_base_sha256'] or m['work'] != m['baseline']
            or (root / 'inputs/task.txt').read_bytes() != prompt.encode()
            or source.sha(root / 'inputs/task.txt') != m['wrapped_prompt_sha256']
            or source.sha(root / 'inputs/public_task.txt') != expected['public_task_sha256']
            or source.sha(source.safe(root / 'scoring/test.patch')) != expected['test_patch_sha256']
            or (root / 'inputs/guest.py').read_bytes() != source.GUEST.encode()
            or json.loads((root / 'inputs/opencode.json').read_text()) != h.actor.config(profile, 17)):
        raise ValueError('prepared target input differs')
    for rel, sha in m['native_overlay'].items():
        if source.sha(source.safe(root / 'work/lib/matplotlib' / rel)) != sha: raise ValueError('target native dependency changed')
    if source.components() != m['components'] or m['binaries'] != {str(source.safe(x)): source.sha(x) for x in (h.tools.OPENCODE, h.tools.RG)}:
        raise ValueError('target source or tool changed')
    return m, h, actor, profile


def execute(root, digest, protocol_path, protocol_sha, arm):
    prepared = verify(root, digest); m = prepared[0]
    if (m['protocol'], m['arm']) != (dict(path=str(protocol_path), sha256=protocol_sha), arm): raise ValueError('CLI target input differs')
    return source.execute_prepared(root, digest, prepared, verify, identity=dict(target=TARGET, arm=arm),
        success_key='target_success', mode='REAL_TARGET_EPISODE',
        score_prepared=lambda r, m, h: source.score(r, m, h, matplotlib_slot='target'))


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__); mode = p.add_mutually_exclusive_group(required=True)
    mode.add_argument('--prepare', action='store_true'); mode.add_argument('--execute', action='store_true')
    p.add_argument('--protocol', type=Path, required=True); p.add_argument('--protocol-sha', required=True)
    p.add_argument('--arm', choices=ARMS, required=True); p.add_argument('--root', type=Path, required=True); p.add_argument('--manifest-sha')
    args = p.parse_args(argv)
    if args.prepare:
        if args.manifest_sha: p.error('prepare does not accept manifest-sha')
        r = prepare(args.protocol, args.protocol_sha, args.arm, args.root)
    else:
        if not args.manifest_sha: p.error('execute requires manifest-sha')
        r = execute(args.root, args.manifest_sha, args.protocol, args.protocol_sha, args.arm)
    print(json.dumps({k: r[k] for k in ('status', 'target', 'arm', 'root', 'manifest_sha256', 'target_success') if k in r}))
    return 0 if r['status'] in ('CPU_PREPARED', 'ACTOR_RETURNED') and not any(k in r for k in ('error', 'finalization_error', 'socket_cleanup_error', 'accounting_error')) else 1


if __name__ == '__main__': raise SystemExit(main())
