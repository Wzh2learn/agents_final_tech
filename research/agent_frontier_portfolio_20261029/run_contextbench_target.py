#!/usr/bin/env python3
"""Frozen code target comparisons; preparation never starts an actor."""
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
SYMPY_TARGET = 'sympy__sympy-9384'
SYMPY_SOURCE = 'sympy__sympy-21055'
SYMPY_BASE = '70cd4ffd093ac224fc0226c1be58f9163e2c800a'
SYMPY_SOURCE_BASE = '748ce73479ee2cd5c861431091001cc18943c735'
SYMPY_ARMS = ['none', 'source_repair_record']
SYMPY_QUALIFICATION_SHA = 'a3c7eef5d3b803dba02992d553d9858bf3e8385ace1d4c33435c750221044aa0'
SYMPY_CONTRACT_SHA = '8b9d0977494184c8e61eeafde308143fdc4dc293bf401b8b8b9c541f1b3c6017'
SYMPY_ANCESTRY_SHA = 'c8412bc8d709509fa9336520dd4d19572c65f67dea571f8fa5a4ce6700143603'
SYMPY_PAIR_REGISTRY_SHA = 'de086acea81dcfae7bdc6e3276a05e7c8ff02e0c6ce38a989bb9f1560a39838f'
SYMPY_SOURCE_MANIFEST_SHA = 'c1cbc8bcca58d6a5d32ac9322b777773bb4d8bc476676a508ebbf304bbaf71ba'
SYMPY_TEACHER_PROTOCOL_SHA = '77d9a417e23cef5d7a6e3d23c9766ac172057d1d11cf447e073fc5bd190e928c'
SYMPY_TEACHER_MANIFEST_SHA = '44af743dab01224bcb7085de6848dc65c9bd60596a6b9391d724908e877e062d'
SYMPY_TEACHER_RECEIPT_SHA = '519023796011a76195055f7b32dbe655ca01f7dee71233d80bb096d202773bed'
SYMPY_RECOUNT_SHA = 'abcfd72d6cdce158bcdcd0c6ac2819721cc9ca20263d37fd36943c21d2fe802c'
SYMPY_CLOSURE_SHA = 'e2ea0e06cf6d77dc40ee87756be218a3d5dc600cda1eb273cacdd88dba6de9b4'
SYMPY_SOURCE_TASK_SHA = '5fd224c389e80da161fb130b1b25f5c0b02b9f1741ea95a46feb60978e94f08b'
SYMPY_REPAIR_PATCH_SHA = '170d9794a56030a40e9dc8653c5f0c5e9ea765b883da26cf974b9d67761de6ba'
SYMPY_RECORD_FIELDS = {'schema', 'source_id', 'repo', 'source_base_commit', 'pair_registry', 'source_manifest',
    'teacher_protocol', 'teacher_manifest', 'teacher_receipt', 'recount_result', 'closure', 'source_task', 'repair_patch'}


def protocol_input(path, digest):
    p = source.read_ref(dict(path=str(path), sha256=digest))
    keys = {'schema', 'target', 'arms', 'qualification', 'qualification_contract', 'source_evidence', 'projection', 'profile', 'caps', 'sampling'}
    if not isinstance(p, dict) or set(p) != keys:
        raise ValueError('target protocol policy differs')
    sympy = p['schema'] == 'contextbench_sympy_target_comparison_v1'
    expected_schema = 'contextbench_sympy_target_comparison_v1' if sympy else 'contextbench_target_comparison_v1'
    if (p['schema'] != expected_schema or p['target'] != (SYMPY_TARGET if sympy else TARGET)
            or p['arms'] != (SYMPY_ARMS if sympy else ARMS) or p['sampling'] != SAMPLING
            or any(type(p['sampling'][k]) is not type(v) for k, v in SAMPLING.items())):
        raise ValueError('target protocol policy differs')
    if (not isinstance(p['caps'], dict) or set(p['caps']) != set(source.CAPS) or any(type(p['caps'][k]) is not int or not 0 < p['caps'][k] <= v for k, v in source.CAPS.items())):
        raise ValueError('target caps exceed approved limits')
    for key in ('qualification', 'qualification_contract', 'source_evidence', 'projection', 'profile'):
        ref = p[key]
        if (not isinstance(ref, dict) or set(ref) != {'path', 'sha256'} or not isinstance(ref['path'], str)
                or not isinstance(ref['sha256'], str) or not re.fullmatch('[0-9a-f]{64}', ref['sha256'])):
            raise ValueError('invalid target reference')
    pins = [('qualification', SYMPY_QUALIFICATION_SHA), ('qualification_contract', SYMPY_CONTRACT_SHA)] if sympy else [
        ('qualification', QUALIFICATION_SHA), ('qualification_contract', CONTRACT_SHA), ('source_evidence', EVIDENCE_SHA)]
    for key, expected in pins:
        if p[key].get('sha256') != expected: raise ValueError('unapproved ' + key)
        source.read_ref(p[key])
    if sympy:
        for key in ('qualification', 'qualification_contract', 'source_evidence', 'projection', 'profile'):
            if source.PRIVATE not in source.safe(p[key]['path']).parents:
                raise ValueError('SymPy input must be private')
        source.read_ref(p['source_evidence'])
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


def sympy_qualification_input(p, h):
    """Accept the qualified 9384 case, even though its larger pool was not qualified."""
    result = source.read_ref(p['qualification']); contract = source.read_ref(p['qualification_contract'])
    if (result.get('status') not in {'QUALIFIED', 'NOT_QUALIFIED'} or type(result.get('model_calls')) is not int
            or result['model_calls'] != 0 or result.get('input_sha256', {}).get(p['qualification_contract']['path']) != p['qualification_contract']['sha256']):
        raise ValueError('target qualification receipt differs')
    ancestry = contract.get('ancestry')
    if (not isinstance(ancestry, dict) or set(ancestry) != {'path', 'sha256'} or ancestry['sha256'] != SYMPY_ANCESTRY_SHA
            or source.PRIVATE not in source.safe(ancestry['path']).parents
            or result['input_sha256'].get(ancestry['path']) != SYMPY_ANCESTRY_SHA):
        raise ValueError('source/target ancestry binding differs')
    source.read_ref(ancestry)
    cases = result.get('cases')
    if not isinstance(cases, dict) or SYMPY_TARGET not in cases: raise ValueError('target case missing')
    case = cases[SYMPY_TARGET]; spec = case['spec']; labels = case['labels']
    identity = (SYMPY_TARGET, 'sympy/sympy', SYMPY_BASE, 'SWEContextBench_Related_Lite.parquet')
    if tuple(spec.get(k) for k in ('instance_id', 'repo', 'base_commit', 'dataset_file')) != identity:
        raise ValueError('target identity differs')
    matches = [row for row in contract.get('cases', []) if row.get('instance_id') == SYMPY_TARGET]
    if len(matches) != 1 or any(matches[0].get(k) != spec.get(k) for k in ('instance_id', 'repo', 'base_commit', 'dataset_file')):
        raise ValueError('target contract identity differs')
    if (set(labels) != {'f2p', 'ptp'} or len(labels['f2p']) != 2 or len(labels['ptp']) != 320
            or len(set(labels['f2p'] + labels['ptp'])) != 322):
        raise ValueError('target qualification labels differ')
    h.pool.mapped_labels('sympy/sympy', labels['f2p'] + labels['ptp'])
    base = case['arms']['base_with_tests']; gold = case['arms']['gold_with_tests']
    for arm in (base, gold):
        for suite in ('f2p', 'ptp'):
            if h.pool.classify(labels[suite], arm[suite]) != arm[suite].get('coverage'):
                raise ValueError('target qualification coverage differs')
    qualified = h.pool.qualification(base['f2p'], gold['f2p'], base['ptp'], gold['ptp'])
    if qualified != case['qualification'] or qualified.get('qualified') is not True:
        raise ValueError('target qualification incomplete')
    parent = source.safe(p['qualification']['path']).parent / SYMPY_TARGET
    if source.tree(parent / 'clean_base') != case['clean_base_sha256']:
        raise ValueError('qualified clean target changed')
    for name in ('task.txt', 'test.patch'):
        if source.sha(source.safe(parent / name)) != case['input_sha256'][name]:
            raise ValueError('target public task or evaluator patch changed')
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


def sympy_evidence_input(p):
    """Bind the actual teacher repair and post-hoc recount, never a gold patch."""
    evidence = source.read_ref(p['source_evidence'])
    if (not isinstance(evidence, dict) or set(evidence) != SYMPY_RECORD_FIELDS
            or (evidence['schema'], evidence['source_id'], evidence['repo'], evidence['source_base_commit']) !=
               ('contextbench_source_repair_record_v1', SYMPY_SOURCE, 'sympy/sympy', SYMPY_SOURCE_BASE)):
        raise ValueError('source repair record identity differs')
    pins = {'pair_registry': SYMPY_PAIR_REGISTRY_SHA, 'source_manifest': SYMPY_SOURCE_MANIFEST_SHA,
        'teacher_protocol': SYMPY_TEACHER_PROTOCOL_SHA, 'teacher_manifest': SYMPY_TEACHER_MANIFEST_SHA,
        'teacher_receipt': SYMPY_TEACHER_RECEIPT_SHA, 'recount_result': SYMPY_RECOUNT_SHA,
        'closure': SYMPY_CLOSURE_SHA, 'source_task': SYMPY_SOURCE_TASK_SHA, 'repair_patch': SYMPY_REPAIR_PATCH_SHA}
    values = {}
    for key, digest in pins.items():
        ref = evidence[key]
        if not isinstance(ref, dict) or set(ref) != {'path', 'sha256'} or ref['sha256'] != digest:
            raise ValueError('missing or unapproved source repair binding: ' + key)
        path = source.safe(ref['path'])
        if source.PRIVATE not in path.parents: raise ValueError('source repair binding must be private')
        if key in {'source_task', 'repair_patch'}:
            raw = path.read_bytes()
            if hashlib.sha256(raw).hexdigest() != digest: raise ValueError('source repair bytes changed')
            values[key] = raw.decode('utf8')
        else:
            values[key] = source.read_ref(ref)
    pair, original = values['pair_registry'], values['source_manifest']
    teacher, prepared, receipt = values['teacher_protocol'], values['teacher_manifest'], values['teacher_receipt']
    recount, closure = values['recount_result'], values['closure']
    rows = [row for row in pair.get('rows', []) if row.get('source') == SYMPY_SOURCE and row.get('target') == SYMPY_TARGET]
    if (pair.get('schema') != 'qualified_source_target_pairs_v1' or len(rows) != 1
            or pair.get('source_result', {}).get('sha256') != source.RESULT_SHA
            or original.get('schema') != 'contextbench_source_v2'
            or (original.get('source'), original.get('repo'), original.get('base')) != (SYMPY_SOURCE, 'sympy/sympy', SYMPY_SOURCE_BASE)
            or original.get('registry') != evidence['pair_registry'] or original.get('source_result') != pair['source_result']
            or original.get('public_task_sha256') != SYMPY_SOURCE_TASK_SHA
            or Path(evidence['source_task']['path']) != Path(original['root']) / 'inputs/source_task.txt'):
        raise ValueError('source qualification or task differs')
    if (teacher.get('schema') != 'CONTEXTBENCH_TEACHER_PATCH_V1' or teacher.get('source_manifest') != evidence['source_manifest']
            or teacher.get('output_root') != prepared.get('root')
            or prepared.get('schema') != 'CONTEXTBENCH_TEACHER_PATCH_PREPARED_V1' or prepared.get('source') != SYMPY_SOURCE
            or prepared.get('source_public_task_sha256') != SYMPY_SOURCE_TASK_SHA or prepared.get('protocol') != evidence['teacher_protocol']
            or Path(evidence['teacher_manifest']['path']) != Path(prepared['root']) / 'manifest.json'
            or Path(evidence['teacher_receipt']['path']) != Path(prepared['root']) / 'false/receipt.json'
            or Path(evidence['repair_patch']['path']) != Path(prepared['root']) / 'false/adapted.diff'):
        raise ValueError('teacher preparation identity differs')
    if (receipt.get('source') != SYMPY_SOURCE or receipt.get('arm') != 'false' or receipt.get('status') != 'GENERATION_FAULT'
            or receipt.get('source_success') is not False or receipt.get('prepared_manifest_sha256') != SYMPY_TEACHER_MANIFEST_SHA
            or receipt.get('protocol') != evidence['teacher_protocol'] or receipt.get('response', {}).get('finish_reason') != 'stop'
            or type(receipt.get('patch', {}).get('check_exit')) is not int or receipt['patch']['check_exit'] == 0
            or receipt['patch'].get('apply_exit') is not None):
        raise ValueError('teacher primary repair receipt differs')
    rows = [row for row in recount.get('results', []) if row.get('arm') == 'false']
    if (recount.get('schema') != 'D_POSTHOC_RECOUNT_RESULT_V1' or recount.get('new_model_POST') != 0 or recount.get('training') != 0
            or len(rows) != 1 or rows[0].get('primary_receipt_sha256') != SYMPY_TEACHER_RECEIPT_SHA
            or rows[0].get('patch_sha256') != SYMPY_REPAIR_PATCH_SHA or rows[0].get('generated_program_text_changed') is not False
            or rows[0].get('status') != 'EVALUATED_AFTER_GIT_RECOUNT' or rows[0].get('source_success') is not True):
        raise ValueError('post-hoc source recount differs')
    commands = rows[0].get('commands', [])
    if (len(commands) != 2 or any(type(c.get('exit')) is not int or c['exit'] != 0 or c.get('args', [])[:2] != ['git', 'apply']
            or '--recount' not in c['args'] for c in commands) or '--check' not in commands[0]['args']
            or '--check' in commands[1]['args']):
        raise ValueError('source recount commands differ')
    scoring = rows[0].get('scoring', {}); suites = scoring.get('suites', {})
    if scoring.get('passed') is not True or set(suites) != {'f2p', 'ptp'}:
        raise ValueError('source recount scoring incomplete')
    for name, count in (('f2p', 1), ('ptp', 13)):
        suite = suites[name]; coverage = suite.get('coverage', {}); labels = coverage.get('labels', {})
        if (type(suite.get('exit')) is not int or suite['exit'] != 0 or suite.get('result', {}).get('fatal') != []
                or coverage.get('complete') is not True or type(coverage.get('reported_tests')) is not int
                or coverage['reported_tests'] != count or len(labels) != count or any(value != 'passed' for value in labels.values())):
            raise ValueError('source recount suite incomplete')
    sec = closure.get('secondary', {})
    if (closure.get('schema') != 'D_TEACHER_CORRECTION_CLOSURE_V1' or closure.get('source') != SYMPY_SOURCE
            or closure.get('status') != 'ONE_ENGINEERING_ASSISTED_SOURCE_CORRECTION_QUALIFIED'
            or not any(row.get('version') == 'teacher_patch_v2' and row.get('arm') == 'false'
                       and row.get('receipt_sha256') == SYMPY_TEACHER_RECEIPT_SHA for row in closure.get('records', []))
            or sec.get('path') != evidence['recount_result']['path'] or sec.get('sha256') != SYMPY_RECOUNT_SHA
            or sec.get('posthoc') is not True or sec.get('false_f2p') != '1/1' or sec.get('false_ptp') != '13/13'):
        raise ValueError('source repair closure differs')
    return values['source_task'], values['repair_patch']


def render_prompt(public, evidence, evidence_bytes, arm):
    if arm not in ARMS: raise ValueError('unknown target arm')
    prompt = ('Implement the requested target change in /workspace and run relevant tests. Python 3.10 '
        'and dependencies are offline. Do not ask for permission to continue. The task below is reproduced verbatim.\n\n' + public)
    if arm == 'source_file_locator':
        prompt += '\n\nSource production file paths:\n' + '\n'.join(source_locator(evidence))
    elif arm == 'full_verified_source_evidence':
        prompt += '\n\nVerified source-only reference-assisted evidence:\n' + evidence_bytes
    return prompt


def sympy_prompt(public, repair, arm):
    if arm not in SYMPY_ARMS: raise ValueError('unknown SymPy target arm')
    prompt = ('Implement the requested target change in /workspace and run relevant tests. Python 3.8 '
        'and dependencies are offline. Do not ask for permission to continue. The task below is reproduced verbatim.\n\n' + public)
    if arm == 'source_repair_record':
        task, patch = repair
        prompt += ('\n\nHistorical teacher-assisted source repair record; this is not a complete successful agent trajectory. '
            'The source differs from the current target. Strict application of the generated diff initially failed; '
            'a post-hoc git apply --recount preserved generated program text and passed the source original test '
            'and 13 source regression tests. Use current target evidence to judge relevance.\n\n'
            'Public source task:\n' + task + '\n\nTeacher-generated source diff:\n' + patch)
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
    p = protocol_input(protocol_path, protocol_sha); h = source.helpers()
    if arm not in p['arms']: raise ValueError('unknown target arm')
    if p['target'] == SYMPY_TARGET:
        result, case, parent = sympy_qualification_input(p, h)
        repair = sympy_evidence_input(p)
        actor = source.projection_input(p['projection']['path'], p['projection']['sha256'], SYMPY_SOURCE, h)
        profile = source.profile_input(p['profile']['path'], p['profile']['sha256'], h)
        contract = source.read_ref(p['qualification_contract']); bindings = {}
        if contract['runtime']['image'] != h.pool.IMAGE: raise ValueError('SymPy scorer image differs')
        limits = h.pool.dependencies('sympy', contract['runtime']['sympy_dependency_manifest'], bindings)
        scorer = dict(bindings=bindings, limits=limits)
        public = (parent / 'task.txt').read_bytes().decode('utf8')
        return p, h, case, parent, actor, profile, scorer, sympy_prompt(public, repair, arm)
    result, case, parent = qualification_input(p, h); evidence = evidence_input(p, result)
    actor = projection_input(p, h); profile = source.profile_input(p['profile']['path'], p['profile']['sha256'], h)
    scorer = scorer_input(p, h)
    public = (parent / 'task.txt').read_bytes().decode('utf8')
    prompt = render_prompt(public, evidence, Path(p['source_evidence']['path']).read_bytes().decode('utf8'), arm)
    return p, h, case, parent, actor, profile, scorer, prompt


def metadata(protocol_path, protocol_sha, arm, root, p, case, scorer):
    if p['target'] == SYMPY_TARGET:
        return dict(schema='contextbench_sympy_target_v1', tool_contract=source.tool_contract_policy(), root=str(root),
            target=SYMPY_TARGET, target_role='DEVELOPMENT_EVAL_ONLY', arm=arm,
            source_record_kind='TEACHER_ASSISTED_REPAIR_POSTHOC_RECOUNT_NOT_COMPLETE_TRAJECTORY',
            protocol=dict(path=str(protocol_path), sha256=protocol_sha), qualification=p['qualification'],
            qualification_contract=p['qualification_contract'], source_evidence=p['source_evidence'],
            repo=case['spec']['repo'], base=case['spec']['base_commit'], labels=case['labels'],
            scorer_dependencies=scorer, projection=p['projection'], profile=p['profile'], caps=p['caps'], sampling=p['sampling'],
            source_runtime=None, scoring_slot='sympy', public_task_sha256=case['input_sha256']['task.txt'],
            test_patch_sha256=case['input_sha256']['test.patch'],
            boundary='target clean/public task and source repair only; qualification/test patches/target gold never actor mounts',
            status='CPU_PREPARED', models_called=0, container_runs=0)
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
    if p['target'] == SYMPY_TARGET:
        record = source.read_ref(p['source_evidence'])
        refs.extend(Path(record[key]['path']).parent for key in SYMPY_RECORD_FIELDS - {'schema', 'source_id', 'repo', 'source_base_commit'})
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
    return dict(status='CPU_PREPARED', root=str(root), target=p['target'], arm=arm, manifest_sha256=source.sha(root / 'manifest.json'))


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
    if m['target'] != SYMPY_TARGET:
        for rel, sha in m['native_overlay'].items():
            if source.sha(source.safe(root / 'work/lib/matplotlib' / rel)) != sha: raise ValueError('target native dependency changed')
    if source.components() != m['components'] or m['binaries'] != {str(source.safe(x)): source.sha(x) for x in (h.tools.OPENCODE, h.tools.RG)}:
        raise ValueError('target source or tool changed')
    return m, h, actor, profile


def execute(root, digest, protocol_path, protocol_sha, arm):
    prepared = verify(root, digest); m = prepared[0]
    if (m['protocol'], m['arm']) != (dict(path=str(protocol_path), sha256=protocol_sha), arm): raise ValueError('CLI target input differs')
    if m['target'] == SYMPY_TARGET:
        return source.execute_prepared(root, digest, prepared, verify, identity=dict(target=SYMPY_TARGET, arm=arm),
            success_key='target_success', mode='REAL_TARGET_EPISODE', score_prepared=source.score)
    return source.execute_prepared(root, digest, prepared, verify, identity=dict(target=TARGET, arm=arm),
        success_key='target_success', mode='REAL_TARGET_EPISODE',
        score_prepared=lambda r, m, h: source.score(r, m, h, matplotlib_slot='target'))


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__); mode = p.add_mutually_exclusive_group(required=True)
    mode.add_argument('--prepare', action='store_true'); mode.add_argument('--execute', action='store_true')
    p.add_argument('--protocol', type=Path, required=True); p.add_argument('--protocol-sha', required=True)
    p.add_argument('--arm', choices=list(dict.fromkeys(ARMS + SYMPY_ARMS)), required=True); p.add_argument('--root', type=Path, required=True); p.add_argument('--manifest-sha')
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
