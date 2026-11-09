#!/usr/bin/env python3
"""Prepare one Django 12589 public-candidate continuation; no scorer is wired.

The actor lifecycle is the existing ContextBench source lifecycle.  Its scoring
record remains PENDING_EXTERNAL until D independently checks the frozen original
1+65 and the wider 219-test contract; actor faults retain their original status.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import stat

import joint_memory_program as joint
import run_contextbench_source as source


INPUT_MANIFEST_SHA = '19643a148a7d68887f61cffd935b93a15a13e836404fdb2216b02f128763878f'
QUERY_BINDING_SHA = '8efd9b814dced2faa3bb5ce9e4efe3d939ede8d54aa21c10169f3be910ad616d'
SNAPSHOT_SHA = 'b1fb79d5cd6082942f4e56881fb037b7b6a2cdfdc381e301151a22526548dd3c'
SNAPSHOT_FILES = 6192
SNAPSHOT_BYTES = 37001020
PROFILE_SHA = '9cbb51bb6dc64583cb376f81e8f8c1c28400cb494fce2793f1fa2ce60e39a279'
PROJECTION_SHA = 'f76dc69ba650e61c49a81611392dabf15b65c5d67b7c8fc0ae03bac10c10c16c'
SCORE_ASSET_SHA = 'dd8d1924e00965469e13b08051dc3019c0753f64f2b76a8f2d2a703a7871b969'
QUALIFICATION_SHA = '46f67e61c87e2e3d118189fbce9ce45a9cbf105eb8440ff2eee6d43d67dd16cc'
REPLAY_RESULT_SHA = 'e549bc3b3b05744f4570c907d10f027afa59d1145af7989d68ba295e291d2968'
ARGV_219_SHA = 'd870190022ff6c14ac96e652eaf326cdc86f91e98b8e87249ce685700a35e564'
TASK_SHA = 'a2f4fdd4ea9e05f3580f98d871ef19a9aacf1156f3a73bcc83b2e659a23c61a5'
FAILURE_SHA = 'baad22bf0baeaea15a9caf7e6fa9035dd49f5ce946910ba6c849bbe6705bed49'
QUERY_HASHES = {
    'read_public_test_function': 'fc38abc5b718ac3f06b36e86a0aa83223542aa537bdee5e21691183a3b226c10',
    'read_edited_production_function': '861825a9aaf479b03bb65b138390780a9e9d811f015273c35e6668dc7ecdea41',
}
TEST_QUERY = 'run_public_regression_single_test'
CAPS = dict(posts=12, seconds=300, combined_wire_bytes=16 * 1024**2)
SAMPLING = dict(seed=17, temperature=0.2, native_thinking=False, context=32768, output=8192)
SCHEMA = 'django12589_joint_memory_resume_v1'
SOURCE_ID = 'django__django-12589'
BASE = '895f28f9cbed817c00ab68770433170d83132d90'


def _unique(pairs):
    out = {}
    for key, value in pairs:
        if key in out:
            raise ValueError('duplicate JSON key')
        out[key] = value
    return out


def _read_json(path, digest):
    path = source.safe(path)
    if not re.fullmatch(r'[0-9a-f]{64}', digest) or source.sha(path) != digest:
        raise ValueError('JSON input hash differs')
    return json.loads(path.read_text(encoding='utf-8'), object_pairs_hook=_unique)


def _ref(value, expected=None):
    if not isinstance(value, dict) or set(value) != {'path', 'sha256'}:
        raise ValueError('exact path/hash reference required')
    if expected is not None and value['sha256'] != expected:
        raise ValueError('unapproved input hash')
    return _read_json(value['path'], value['sha256'])


def _public_text(path, digest, limit=65536):
    path = source.safe(path)
    if not path.is_file() or path.stat().st_size > limit or source.sha(path) != digest:
        raise ValueError('public text missing, changed or oversized')
    value = path.read_bytes().decode('utf-8')
    if '\x00' in value:
        raise ValueError('public text contains NUL')
    return value


def snapshot_fingerprint(root):
    """Match the frozen public snapshot algorithm, including executable modes."""
    root = source.safe(root)
    files = source.tree(root)  # Reject links, hard links, special files and .git.
    digest = hashlib.sha256()
    total = 0
    for rel, file_sha in sorted(files.items()):
        p = source.safe(root / rel)
        info = p.stat()
        parts = Path(rel).parts
        if any(x == '.git' or x == '.env' or x.startswith('.env.') for x in parts):
            raise ValueError('private snapshot path')
        total += info.st_size
        row = [rel, format(stat.S_IMODE(info.st_mode), '04o'), info.st_size, file_sha]
        digest.update((json.dumps(row, ensure_ascii=False, separators=(',', ':')) + '\n').encode('utf-8'))
    return dict(tree_sha256=digest.hexdigest(), files=len(files), bytes=total), files


def projection_input(ref, h):
    if ref.get('sha256') != PROJECTION_SHA or set(ref) != {'path', 'sha256'}:
        raise ValueError('unapproved Django projection')
    path = source.safe(ref['path'])
    manifest = _ref(dict(path=str(path / 'manifest.json'), sha256=PROJECTION_SHA))
    actor = h.deps.verify_projection(path, PROJECTION_SHA)
    if (manifest.get('python'), manifest.get('blocked_packages'), manifest.get('site_names')) != (
            '3.8', ['django'], ['default', 'pgdriver']):
        raise ValueError('Django projection surface differs')
    if set(actor['sites']) != {'default', 'pgdriver'}:
        raise ValueError('Django projection sites differ')
    # PG driver is not needed or mounted by this source continuation.
    return {**actor, 'sites': {'default': actor['sites']['default']}}


def _test_query_result(entry, binding, program_sha):
    """Accept only a D-recorded selected test slot and its fixed output files.

    The receipt binds logs and ownership claims; CPU prepare does not independently
    inspect Docker or prove a physical run.  Missing/incomplete receipts fail closed.
    """
    if set(entry) != {'id', 'slot', 'receipt'} or type(entry['slot']) is not int:
        raise ValueError('test query requires an explicit slot and receipt')
    q = next(x for x in binding['queries'] if x['id'] == TEST_QUERY)
    slot = next((x for x in q['slots'] if x['slot'] == entry['slot']), None)
    if slot is None:
        raise ValueError('unregistered test query slot')
    receipt_path = Path(slot['cidfile']).parent / ('test_%02d.receipt.json' % slot['slot'])
    if entry['receipt'].get('path') != str(receipt_path):
        raise ValueError('test query receipt path differs')
    receipt = _ref(entry['receipt'])
    keys = {'schema', 'status', 'query_binding_sha256', 'snapshot_tree_sha256',
            'program_sha256', 'slot', 'argv_sha256', 'exit', 'timed_out',
            'cleanup_verified', 'container_id', 'stdout_sha256', 'stderr_sha256'}
    if (set(receipt) != keys or receipt['schema'] != 'django12589_public_test_query_receipt_v1'
            or receipt['status'] != 'COMPLETED' or receipt['query_binding_sha256'] != QUERY_BINDING_SHA
            or receipt['snapshot_tree_sha256'] != SNAPSHOT_SHA or receipt['program_sha256'] != program_sha
            or receipt['slot'] != slot['slot'] or receipt['argv_sha256'] != slot['argv_sha256']
            or type(receipt['exit']) is not int or receipt['exit'] not in (0, 1)
            or receipt['timed_out'] is not False or receipt['cleanup_verified'] is not True
            or not isinstance(receipt['container_id'], str)
            or not re.fullmatch(r'[0-9a-f]{64}', receipt['container_id'])):
        raise ValueError('test query receipt is incomplete or differs')
    stdout = _public_text(slot['stdout'], receipt['stdout_sha256'], 32768)
    stderr = _public_text(slot['stderr'], receipt['stderr_sha256'], 32768)
    return ('Exit code: %d\nstdout:\n%s\nstderr:\n%s' % (receipt['exit'], stdout, stderr),
            dict(id=TEST_QUERY, slot=slot['slot'], receipt=entry['receipt'],
                 stdout_sha256=receipt['stdout_sha256'], stderr_sha256=receipt['stderr_sha256'],
                 verification='bound D receipt; no Docker inspection in prepare'))


def query_inputs(program, entries, binding):
    if type(entries) is not list or len(entries) != len(program.queries):
        raise ValueError('one explicit result required for every selected query')
    allowed = {x['id']: x for x in binding['queries']}
    if set(allowed) != set(QUERY_HASHES) | {TEST_QUERY}:
        raise ValueError('query catalog differs')
    program_sha = hashlib.sha256(joint.program_json(program).encode('utf-8')).hexdigest()
    values, refs, used_slots = [], [], set()
    for selected, entry in zip(program.queries, entries):
        if not isinstance(entry, dict) or entry.get('id') != selected:
            raise ValueError('query result order differs from selected program')
        if selected in QUERY_HASHES:
            if set(entry) != {'id'}:
                raise ValueError('public read query takes no arbitrary input')
            q = allowed[selected]
            if q.get('sha256') != QUERY_HASHES[selected] or q.get('executor') != 'read exact bytes':
                raise ValueError('public query binding differs')
            text = _public_text(q['path'], QUERY_HASHES[selected], 8192)
            values.append((selected, text))
            refs.append(dict(id=selected, sha256=QUERY_HASHES[selected], bytes=len(text.encode('utf-8')),
                             verification='selected bound public file read during prepare/verify'))
        elif selected == TEST_QUERY:
            if entry.get('slot') in used_slots:
                raise ValueError('one physical test slot cannot be reused')
            text, detail = _test_query_result(entry, binding, program_sha)
            used_slots.add(entry['slot']); values.append((selected, text)); refs.append(detail)
        else:
            raise ValueError('unknown selected query')
    return values, refs, program_sha


def render_prompt(task, failure, program, queries):
    prompt = ('Continue the existing edited Django workspace in /workspace. Preserve the original '
              'issue fix and repair the publicly observed regression. Python 3.8 and dependencies '
              'are offline. Inspect relevant public source and run appropriate tests.\n\n'
              'Public source issue:\n' + task + '\nPublic regression feedback:\n' + failure)
    if program.memory:
        prompt += '\n\nExplicit memory records:\n' + '\n'.join('- ' + x for x in program.memory)
    for name, text in queries:
        prompt += '\n\nSelected query result (' + name + '):\n' + text
    return prompt


def _no_private_markers(text):
    # Explicitly block known target/host locations; source-only semantic provenance
    # of a generated memory remains the caller's responsibility.
    low = text.casefold()
    if any(x in low for x in ('34176', '016bead6a23989adec5c7ee6948db7ce2fc5e89b',
                              '/home/testuser/wzh/research_evidence', '\x00')):
        raise ValueError('non-source or private marker in actor text')


def scoring_recipe(ref):
    asset = _ref(ref, SCORE_ASSET_SHA)
    if (asset.get('source_instance'), asset.get('source_base_commit')) != (SOURCE_ID, BASE):
        raise ValueError('scoring source identity differs')
    info = asset['evaluator_reproduction']
    qual_path = Path(info['command_65_labels_ref'])
    qual = _read_json(qual_path, QUALIFICATION_SHA)
    row = qual['cases']['source']
    if (row['id'], row['base'], len(row['focus_labels']), len(row['regression_labels'])) != (SOURCE_ID, BASE, 1, 65):
        raise ValueError('original scoring labels differ')
    replay = Path(ref['path']).parent / 'CURRENT_REPLAY_V1'
    _read_json(replay / 'RESULT_V1.json', REPLAY_RESULT_SHA)
    argv = _read_json(replay / 'ARGV_219.json', ARGV_219_SHA)
    if not isinstance(argv, list) or argv[-2:] != ['aggregation', 'expressions']:
        raise ValueError('wide scoring recipe differs')
    return dict(status='NOT_WIRED_EXTERNAL_D_SCORING_REQUIRED',
        qualification=dict(path=str(qual_path), sha256=QUALIFICATION_SHA),
        focus_pointer='/cases/source/focus_labels', regression_pointer='/cases/source/regression_labels',
        original_focus_count=1, original_regression_count=65,
        wider_argv=dict(path=str(replay / 'ARGV_219.json'), sha256=ARGV_219_SHA),
        wider_count=219, wider_allowed_skips=1,
        boundary='restore public tests/config and apply the private frozen test overlay only in a D-side scoring copy',
        replay_note='allocate a new owned container name and cidfile; the historical argv is an evidence template, not reusable as-is')


def admitted(protocol_path, protocol_sha):
    p = _read_json(protocol_path, protocol_sha)
    keys = {'schema', 'input_manifest', 'query_binding', 'snapshot', 'score_asset',
            'projection', 'profile', 'program', 'query_results'}
    if not isinstance(p, dict) or set(p) != keys or p['schema'] != SCHEMA:
        raise ValueError('exact continuation protocol required')
    public = _ref(p['input_manifest'], INPUT_MANIFEST_SHA)
    binding = _ref(p['query_binding'], QUERY_BINDING_SHA)
    if (binding.get('input_manifest_sha256') != INPUT_MANIFEST_SHA
            or binding.get('snapshot_tree', {}).get('sha256') != SNAPSHOT_SHA):
        raise ValueError('public input and query binding differ')
    if (not isinstance(p['snapshot'], dict) or set(p['snapshot']) != {'path', 'tree_sha256'}
            or p['snapshot']['tree_sha256'] != SNAPSHOT_SHA
            or binding.get('snapshot') != p['snapshot']['path']):
        raise ValueError('wrong public snapshot binding')
    fingerprint, files = snapshot_fingerprint(p['snapshot']['path'])
    if fingerprint != dict(tree_sha256=SNAPSHOT_SHA, files=SNAPSHOT_FILES, bytes=SNAPSHOT_BYTES):
        raise ValueError('public snapshot bytes or modes differ')
    base = Path(p['input_manifest']['path']).parent
    task = _public_text(base / 'public/source_task.txt', TASK_SHA)
    failure = _public_text(base / 'public/public_regression_failure.txt', FAILURE_SHA)
    expected = public['public_payloads']
    if (expected['public/source_task.txt']['sha256'] != TASK_SHA
            or expected['public/public_regression_failure.txt']['sha256'] != FAILURE_SHA):
        raise ValueError('public input hashes differ')
    program = joint.parse_program(json.dumps(p['program'], ensure_ascii=False), set(QUERY_HASHES) | {TEST_QUERY})
    queries, query_refs, program_sha = query_inputs(program, p['query_results'], binding)
    prompt = render_prompt(task, failure, program, queries)
    _no_private_markers(prompt)
    if len(prompt.encode('utf-8')) > 32768:
        raise ValueError('actor prompt exceeds bounded UTF-8 input')
    h = source.helpers()
    if p['profile'].get('sha256') != PROFILE_SHA or source.PROFILE_SHA != PROFILE_SHA:
        raise ValueError('unapproved 27B profile')
    profile = source.profile_input(p['profile']['path'], p['profile']['sha256'], h)
    actor = projection_input(p['projection'], h)
    score = scoring_recipe(p['score_asset'])
    return p, h, actor, profile, score, task, failure, prompt, query_refs, program_sha, files


def metadata(protocol_path, protocol_sha, root, p, score, task, failure, prompt, query_refs, program_sha):
    return dict(schema=SCHEMA, root=str(root), source=SOURCE_ID, base=BASE,
        protocol=dict(path=str(protocol_path), sha256=protocol_sha), snapshot=p['snapshot'],
        input_manifest=p['input_manifest'], query_binding=p['query_binding'], score_asset=p['score_asset'],
        projection=p['projection'], profile=p['profile'], tool_contract=source.tool_contract_policy(),
        caps=CAPS, sampling=SAMPLING, source_runtime=None, program_sha256=program_sha,
        query_inputs=query_refs, task_sha256=hashlib.sha256(task.encode()).hexdigest(),
        failure_sha256=hashlib.sha256(failure.encode()).hexdigest(),
        wrapped_prompt_sha256=hashlib.sha256(prompt.encode()).hexdigest(),
        scoring_recipe=score, status='CPU_PREPARED', models_called=0, container_runs=0,
        boundary='actor receives public candidate, source task, public failure and selected explicit memory/query text only')


def prepare(protocol_path, protocol_sha, root):
    data = admitted(protocol_path, protocol_sha)
    p, h, actor, profile, score, task, failure, prompt, query_refs, program_sha, files = data
    root = source.safe(root)
    refs = [Path(protocol_path), Path(p['input_manifest']['path']).parent,
            Path(p['query_binding']['path']), Path(p['snapshot']['path']),
            Path(p['projection']['path']), Path(p['profile']['path']), Path(p['score_asset']['path'])]
    if (source.PRIVATE not in root.parents or root.exists()
            or any(root == x or root in x.parents or x in root.parents for x in refs)):
        raise ValueError('fresh disjoint private root required')
    h.tools.ripgrep_binding()
    binaries = {str(source.safe(x)): source.sha(x) for x in (h.tools.OPENCODE, h.tools.RG)}
    root.mkdir(mode=0o700, parents=True)
    shutil.copytree(p['snapshot']['path'], root / 'baseline')
    shutil.copytree(root / 'baseline', root / 'work')
    for f in (root / 'work').rglob('*'):
        if f.is_file(): f.chmod(f.stat().st_mode | 0o200)
    inputs = root / 'inputs'; inputs.mkdir(); (root / 'scoring').mkdir()
    (inputs / 'public_task.txt').write_bytes(task.encode())
    (inputs / 'public_failure.txt').write_bytes(failure.encode())
    (inputs / 'task.txt').write_bytes(prompt.encode())
    (inputs / 'guest.py').write_bytes(source.GUEST.encode())
    source.new(inputs / 'opencode.json', h.actor.config(profile, 17))
    m = metadata(protocol_path, protocol_sha, root, p, score, task, failure, prompt, query_refs, program_sha)
    m.update(baseline=source.tree(root / 'baseline'), work=source.tree(root / 'work'),
             inputs=source.tree(inputs), components=source.components(), binaries=binaries)
    baseline_fingerprint, _ = snapshot_fingerprint(root / 'baseline')
    if (m['baseline'] != files or m['work'] != files
            or baseline_fingerprint != dict(tree_sha256=SNAPSHOT_SHA, files=SNAPSHOT_FILES, bytes=SNAPSHOT_BYTES)):
        raise ValueError('prepared workspace differs from public candidate')
    source.new(root / 'manifest.json', m)
    return dict(status='CPU_PREPARED', root=str(root), manifest_sha256=source.sha(root / 'manifest.json'))


def verify(root, digest, *, initial=True):
    root = source.safe(root)
    m = _read_json(root / 'manifest.json', digest)
    data = admitted(m['protocol']['path'], m['protocol']['sha256'])
    p, h, actor, profile, score, task, failure, prompt, query_refs, program_sha, files = data
    expected = metadata(m['protocol']['path'], m['protocol']['sha256'], root, p, score,
                        task, failure, prompt, query_refs, program_sha)
    extra = {'baseline', 'work', 'inputs', 'components', 'binaries'}
    if set(m) != set(expected) | extra or any(m[k] != v for k, v in expected.items()):
        raise ValueError('prepared manifest policy differs')
    for name in (('baseline', 'work', 'inputs') if initial else ('baseline', 'inputs')):
        if source.tree(root / name) != m[name]:
            raise ValueError('prepared ' + name + ' changed')
    fingerprint, _ = snapshot_fingerprint(root / 'baseline')
    if fingerprint != dict(tree_sha256=SNAPSHOT_SHA, files=SNAPSHOT_FILES, bytes=SNAPSHOT_BYTES):
        raise ValueError('prepared baseline modes differ')
    if not initial: source.tree(root / 'work')  # Editable, but never linked or .git.
    if (m['baseline'] != files or m['work'] != files
            or (root / 'inputs/task.txt').read_bytes() != prompt.encode()
            or (root / 'inputs/public_task.txt').read_bytes() != task.encode()
            or (root / 'inputs/public_failure.txt').read_bytes() != failure.encode()
            or (root / 'inputs/guest.py').read_bytes() != source.GUEST.encode()
            or json.loads((root / 'inputs/opencode.json').read_text()) != h.actor.config(profile, 17)):
        raise ValueError('prepared actor input differs')
    if source.components() != m['components'] or m['binaries'] != {
            str(source.safe(x)): source.sha(x) for x in (h.tools.OPENCODE, h.tools.RG)}:
        raise ValueError('source component or binary changed')
    return m, h, actor, profile


def score_pending(root, manifest, helpers):
    """Explicit callback contract: never claim success before independent scoring."""
    # ContextBench changes the outer status to UNFINISHED_SCORING before its
    # actor-fault check when status is UNFINISHED.  Keep that check reachable.
    return dict(status='PENDING_EXTERNAL', passed=False,
        reason='D must independently score original 1 F2P, 65 PTP and wide 219 on a restored test copy',
        recipe=manifest['scoring_recipe'])


def execute(root, digest, protocol_path, protocol_sha):
    prepared = verify(root, digest)
    if prepared[0]['protocol'] != dict(path=str(protocol_path), sha256=protocol_sha):
        raise ValueError('CLI protocol differs from prepared input')
    return source.execute_prepared(root, digest, prepared, verify,
        identity=dict(source=SOURCE_ID, stage='PUBLIC_REGRESSION_RECOVERY'),
        success_key='recovery_success', mode='DJANGO_PUBLIC_RECOVERY_EPISODE',
        score_prepared=score_pending)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    mode = p.add_mutually_exclusive_group(required=True)
    mode.add_argument('--prepare', action='store_true'); mode.add_argument('--verify', action='store_true')
    mode.add_argument('--execute', action='store_true')
    p.add_argument('--protocol', type=Path, required=True); p.add_argument('--protocol-sha', required=True)
    p.add_argument('--root', type=Path, required=True); p.add_argument('--manifest-sha')
    args = p.parse_args(argv)
    if args.prepare:
        if args.manifest_sha: p.error('prepare does not accept manifest-sha')
        result = prepare(args.protocol, args.protocol_sha, args.root)
    elif args.verify:
        if not args.manifest_sha: p.error('verify requires manifest-sha')
        prepared = verify(args.root, args.manifest_sha)
        if prepared[0]['protocol'] != dict(path=str(args.protocol), sha256=args.protocol_sha):
            raise ValueError('CLI protocol differs from prepared input')
        result = dict(status='CPU_VERIFIED', root=str(args.root), manifest_sha256=args.manifest_sha)
    else:
        if not args.manifest_sha: p.error('execute requires manifest-sha')
        result = execute(args.root, args.manifest_sha, args.protocol, args.protocol_sha)
    print(json.dumps({k: result[k] for k in ('status', 'root', 'manifest_sha256', 'recovery_success') if k in result}))
    if result['status'] in ('CPU_PREPARED', 'CPU_VERIFIED'): return 0
    if result['status'] == 'ACTOR_RETURNED' and result.get('scoring', {}).get('status') == 'PENDING_EXTERNAL':
        return 2  # Actor returned; the requested success gate is still unknown.
    return 1


if __name__ == '__main__':
    raise SystemExit(main())
