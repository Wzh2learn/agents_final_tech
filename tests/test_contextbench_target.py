"""CPU engineering controls with synthetic assets, not target model results."""
import copy
import hashlib
import json
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'research/agent_frontier_portfolio_20261029'))
import run_contextbench_target as t
import run_contextbench_source as s
from test_contextbench_source import prepared_inputs, matplotlib_inputs, write_json


@pytest.fixture
def target_inputs(matplotlib_inputs, monkeypatch):
    f = matplotlib_inputs
    contract = Path(f.reg['qualification_contract']['path'])
    contract_sha = write_json(contract, {'runtime': {'projection': {'path': str(f.projection/'manifest.json'), 'sha256': f.projection_sha}}})
    result = json.loads(f.receipt.read_text())
    result['input_sha256'] = {str(contract): contract_sha}
    src = f.receipt.parent / s.MPL_SOURCE_ID
    patch = 'diff --git a/lib/matplotlib/cbook.py b/lib/matplotlib/cbook.py\n--- a/lib/matplotlib/cbook.py\n+++ b/lib/matplotlib/cbook.py\n@@ -1 +1 @@\n-old\n+new\n'
    (src/'reference.patch').write_bytes(patch.encode())
    result['cases'][s.MPL_SOURCE_ID]['input_sha256']['reference.patch'] = s.sha(src/'reference.patch')
    result_sha = write_json(f.receipt, result)
    evidence = f.private / 'source_evidence.json'
    ev = dict(schema='reference_assisted_source_evidence_v1', source_id=s.MPL_SOURCE_ID,
        source_repo='matplotlib/matplotlib', source_base_commit='66ba515e671638971bd11a34cff12c107a437e0b',
        source_task=(src/'task.txt').read_bytes().decode(), source_reference_patch=patch,
        teacher_kind='Synthetic reference-assisted CPU fixture', observed_source_error='CPU_SOURCE_ERROR',
        native_control=dict(base_f2p_failed=1, base_ptp_passed=181, reference_f2p_passed=1, reference_ptp_passed=181),
        natural_model_attempt={}, evidence_scope='CPU engineering fixture, no actor outcome')
    evidence_sha = write_json(evidence, ev)
    monkeypatch.setattr(t, 'QUALIFICATION_SHA', result_sha)
    monkeypatch.setattr(t, 'CONTRACT_SHA', contract_sha)
    monkeypatch.setattr(t, 'EVIDENCE_SHA', evidence_sha)
    monkeypatch.setattr(t, 'scorer_input', lambda *_: dict(bindings={}, limits='Synthetic CPU scorer', matplotlib_runtime={'CPU_RUNTIME': True}))
    protocol = f.private / 'target_protocol.json'
    value = dict(schema='contextbench_target_comparison_v1', target=s.MPL_TARGET_ID,
        arms=['none', 'source_file_locator', 'full_verified_source_evidence'],
        qualification=dict(path=str(f.receipt), sha256=result_sha),
        qualification_contract=dict(path=str(contract), sha256=contract_sha),
        source_evidence=dict(path=str(evidence), sha256=evidence_sha),
        projection=dict(path=str(f.projection), sha256=f.projection_sha),
        profile=dict(path=str(f.profile), sha256=f.profile_sha), caps=dict(posts=4, seconds=120, combined_wire_bytes=2*1024**2),
        sampling=dict(seed=17, temperature=0.2, native_thinking=False, context=32768, output=8192))
    f.protocol = protocol; f.protocol_value = value; f.protocol_sha = write_json(protocol, value)
    f.evidence = evidence; f.evidence_value = ev; f.result = result
    return f


def prepare(f, arm='none', root=None):
    return t.prepare(f.protocol, f.protocol_sha, arm, root or f.root)


def test_prepare_three_arms_have_same_clean_target_and_only_frozen_evidence_difference(target_inputs, monkeypatch):
    f = target_inputs
    def forbidden(*_, **__): raise AssertionError('CPU prepare executed a process or endpoint')
    monkeypatch.setattr(s.subprocess, 'run', forbidden)
    monkeypatch.setattr(s.subprocess, 'Popen', forbidden)
    prompts = {}; manifests = {}
    for arm in f.protocol_value['arms']:
        root = f.private / arm
        out = prepare(f, arm, root); m, _, actor, _ = t.verify(root, out['manifest_sha256'])
        manifests[arm] = m; prompts[arm] = (root/'inputs/task.txt').read_bytes().decode()
        assert m['target'] == s.MPL_TARGET_ID and 'source' not in m
        assert actor['sites'] == {'default': str(f.projection/'deps/target')}
        assert (root/'inputs/public_task.txt').read_bytes() == (f.receipt.parent/s.MPL_TARGET_ID/'task.txt').read_bytes()
        assert not any('patch' in p.name or 'evidence' in p.name for p in (root/'inputs').iterdir())
        assert m['models_called'] == m['container_runs'] == 0
    assert all(m['baseline'] == manifests['none']['baseline'] and m['caps'] == manifests['none']['caps'] for m in manifests.values())
    assert 'CPU_SOURCE_ERROR' not in prompts['none'] and 'cbook.py' not in prompts['none']
    assert 'lib/matplotlib/cbook.py' in prompts['source_file_locator'] and 'CPU_SOURCE_ERROR' not in prompts['source_file_locator']
    assert f.evidence.read_bytes().decode() in prompts['full_verified_source_evidence']
    assert all(p.startswith(prompts['none']) for p in prompts.values())


@pytest.mark.parametrize('change', ['unknown_arm', 'caps', 'cap_overflow', 'sampling', 'sampling_type', 'unknown_key', 'wrong_sha', 'role', 'skip', 'source_evidence'])
def test_malformed_protocol_or_qualification_refused_before_root(target_inputs, monkeypatch, change):
    f = target_inputs; v = copy.deepcopy(f.protocol_value); arm = 'none'
    if change == 'unknown_arm': arm = 'skill'
    elif change == 'caps': v['caps']['posts'] = True
    elif change == 'cap_overflow': v['caps']['posts'] = 49
    elif change == 'sampling': v['sampling']['seed'] = 18
    elif change == 'sampling_type': v['sampling']['native_thinking'] = 0
    elif change == 'unknown_key': v['target_gold'] = 'not permitted'
    elif change == 'wrong_sha': v['qualification']['sha256'] = '0'*64
    elif change in ('role','skip'):
        if change == 'role': f.result['cases'][s.MPL_TARGET_ID]['spec']['role'] = 'source'
        else: f.result['cases'][s.MPL_TARGET_ID]['arms']['gold_with_tests']['group']['result']['tests'][f.cases[s.MPL_TARGET_ID]['labels']['ptp'][0]] = 'skipped'
        digest=write_json(f.receipt, f.result)
        monkeypatch.setattr(t,'QUALIFICATION_SHA',digest);v['qualification']['sha256']=digest
    else: f.evidence.write_text(f.evidence.read_text().replace('CPU_SOURCE_ERROR','target secret'))
    f.protocol_sha = write_json(f.protocol, v)
    with pytest.raises(ValueError): prepare(f, arm)
    assert not f.root.exists()


@pytest.mark.parametrize('patch', ['diff --git a/tests/test_x.py b/tests/test_x.py\n', 'diff --git a/../gold.py b/../gold.py\n', 'diff --git a/lib/a.py b/lib/b.py\n', 'no patch'])
def test_locator_rejects_test_paths_escape_renames_and_missing_headers(patch):
    with pytest.raises(ValueError): t.source_locator({'source_reference_patch': patch})


@pytest.mark.parametrize('change', ['prompt', 'public', 'native', 'baseline', 'manifest_caps', 'arm'])
def test_verify_reconstructs_identity_prompt_and_frozen_native(target_inputs, change):
    f = target_inputs; out = prepare(f); digest = out['manifest_sha256']
    if change in ('manifest_caps','arm'):
        p=f.root/'manifest.json';v=json.loads(p.read_text())
        if change=='manifest_caps': v['caps']['posts']+=1
        else: v['arm']='source_file_locator'
        digest=write_json(p,v)
    else:
        p={'prompt':'inputs/task.txt','public':'inputs/public_task.txt','native':'work/lib/matplotlib/_native.so','baseline':'baseline/lib/matplotlib/cbook.py'}[change]
        (f.root/p).write_text('tampered')
    with pytest.raises(ValueError): t.verify(f.root,digest,initial=False)


def test_target_slot_is_explicit_and_source_default_unchanged(tmp_path, monkeypatch):
    seen=[]; work=tmp_path/'work';work.mkdir(); runner=tmp_path/'runner.py';runner.write_text('CPU')
    def command(*args): seen.append(args[-1]);return ['CPU_ONLY']
    pool=SimpleNamespace(mem_available=lambda:5*1024**3, matplotlib_command=command, MARKER='RESULT=', classify=lambda *_: {})
    h=SimpleNamespace(pool=pool)
    def run(cmd,name,cid,stdout,stderr,timeout):
        stdout.write_text('RESULT={"tests":{},"fatal":[]}\n');stderr.write_text('');return dict(exit=0)
    monkeypatch.setattr(s,'run_owned',run)
    for slot in ['source','target','default']:
        kwargs={} if slot=='default' else dict(matplotlib_slot=slot)
        s.scored_test(work,'matplotlib/matplotlib',[],runner,tmp_path,slot,h,matplotlib_assets={},**kwargs)
    assert seen==['source','target','source']
    with pytest.raises(ValueError):s.scored_test(work,'matplotlib/matplotlib',[],runner,tmp_path,'bad',h,matplotlib_assets={},matplotlib_slot='gold')


def test_execute_dispatch_keeps_target_identity_and_explicit_score_slot(target_inputs, monkeypatch):
    f=target_inputs;out=prepare(f);calls=[]
    def execute(root,digest,prepared,verify_prepared,**kwargs):
        calls.append(kwargs); assert prepared[0]['target']==s.MPL_TARGET_ID
        assert verify_prepared is t.verify
        return dict(status='CPU_FAKE',target_success=False)
    monkeypatch.setattr(s,'execute_prepared',execute)
    assert t.execute(f.root,out['manifest_sha256'],f.protocol,f.protocol_sha,'none')['target_success'] is False
    assert calls[0]['identity']==dict(target=s.MPL_TARGET_ID,arm='none')
    assert calls[0]['mode']=='REAL_TARGET_EPISODE' and calls[0]['success_key']=='target_success'
    monkeypatch.setattr(s,'score',lambda root,m,h,**kw:kw)
    assert calls[0]['score_prepared'](None,None,None)=={'matplotlib_slot':'target'}


def test_target_mounts_no_qualification_parent_source_or_gold(target_inputs):
    f=target_inputs;out=prepare(f);_,h,actor,p=t.verify(f.root,out['manifest_sha256']);bridge=f.private/'bridge';bridge.mkdir()
    cmd=s.docker_command(f.root,actor,bridge,p,h,'CPU_TARGET',source_runtime=s.MPL_SOURCE_RUNTIME)
    mounts=[v.replace('\\', '/') for v in cmd if 'type=bind' in v]
    assert any('/deps/target' in v and 'dst=/deps,readonly' in v for v in mounts)
    assert not any(f.receipt.parent.as_posix() in v or '/deps/source' in v or 'scoring' in v or 'evidence' in v for v in mounts)
    assert '--network' in cmd and cmd[cmd.index('--network')+1]=='none'


def test_rebinding_manifest_hash_does_not_allow_prompt_or_cap_rewrite(target_inputs):
    f=target_inputs;out=prepare(f);path=f.root/'manifest.json';m=json.loads(path.read_text())
    (f.root/'inputs/task.txt').write_text('tampered target instructions')
    m['inputs']=s.tree(f.root/'inputs');m['wrapped_prompt_sha256']=s.sha(f.root/'inputs/task.txt')
    with pytest.raises(ValueError,match='input differs'):t.verify(f.root,write_json(path,m))


def test_existing_root_and_linked_work_refused(target_inputs):
    f=target_inputs;out=prepare(f)
    with pytest.raises(ValueError,match='fresh'):prepare(f)
    dest=f.root/'work/link'
    try: dest.symlink_to(f.private)
    except OSError:
        # Windows may forbid symlinks; the same admission boundary rejects hardlinks.
        import os
        os.link(f.root/'work/lib/matplotlib/cbook.py', dest)
    with pytest.raises(ValueError):t.verify(f.root,out['manifest_sha256'],initial=False)


def test_target_busy_lock_refuses_before_reservation_or_backend(target_inputs,monkeypatch):
    from contextlib import contextmanager
    f=target_inputs;out=prepare(f)
    @contextmanager
    def busy():raise BlockingIOError('CPU existing owner');yield
    monkeypatch.setattr(s,'resource_lock',busy)
    with pytest.raises(BlockingIOError):t.execute(f.root,out['manifest_sha256'],f.protocol,f.protocol_sha,'none')
    assert not (f.root/'reservation.json').exists() and not (f.root/'receipt.json').exists()


@pytest.mark.parametrize('error', [None, {'name':'UnknownError'}, {'name':'APIError','data':{'statusCode':403}}])
def test_fake_target_lifecycle_uses_frozen_caps_and_cannot_launder_errors(target_inputs,monkeypatch,error):
    """All backend/server/container/scorer operations below are CPU fakes."""
    from contextlib import contextmanager
    f=target_inputs;out=prepare(f);seen={}
    @contextmanager
    def lock():yield
    monkeypatch.setattr(s,'resource_lock',lock)
    f.h.teacher.validate_vllm_model_profile=lambda *a,**kw:None
    f.h.teacher.verify_vllm_backend=lambda _:dict(CPU_FAKE=True)
    class Server:
        def __init__(self,path,handler):Path(path).write_text('CPU fake owned UDS artifact')
        def serve_forever(self):pass
        def server_close(self):pass
        def shutdown(self):pass
    class Relay:
        def __init__(self,root,profile,h,*,deadline,caps):
            seen['caps']=caps;seen['remaining']=deadline-s.time.monotonic()
        def close(self):seen['closed']=True
        def accounting(self):return dict(integrity_passed=True,actual_forwarded_posts=1)
    monkeypatch.setattr(s.socketserver,'ThreadingUnixStreamServer',Server,raising=False)
    original_mkdtemp=s.tempfile.mkdtemp
    monkeypatch.setattr(s.tempfile,'mkdtemp',lambda prefix,dir:original_mkdtemp(prefix=prefix,dir=f.private))
    monkeypatch.setattr(s,'Relay',Relay)
    def collected(cmd,name,cid,stdout,stderr,timeout):
        seen['timeout']=timeout
        stdout.write_text((json.dumps(dict(type='error',error=error))+'\n') if error else '')
        stderr.write_text('');return dict(exit=0,cleanup=dict(CPU_FAKE=True))
    monkeypatch.setattr(s,'run_owned',collected)
    monkeypatch.setattr(s,'score',lambda r,m,h,**kw:dict(status='EVALUATED',passed=True,slot=kw['matplotlib_slot']))
    result=t.execute(f.root,out['manifest_sha256'],f.protocol,f.protocol_sha,'none')
    assert result['target_success'] is (error is None)
    assert result['status']==('ACTOR_RETURNED' if error is None else 'GENERATION_FAULT')
    assert seen['caps']==f.protocol_value['caps'] and seen['timeout']==120 and 119<seen['remaining']<=120 and seen['closed']
    assert result['scoring']['slot']=='target' and 'source_success' not in result


@pytest.fixture
def sympy_target_inputs(prepared_inputs, monkeypatch):
    """Synthetic qualification and teacher repair; no benchmark or model execution."""
    f = prepared_inputs
    target = 'sympy__sympy-9384'; source_id = 'sympy__sympy-21055'
    target_root = f.private / 'target_qualification' / target
    clean = target_root / 'clean_base'; (clean / 'sympy').mkdir(parents=True)
    (clean / 'sympy/refine.py').write_text('PUBLIC_TARGET_BASE = True\n')
    (target_root / 'task.txt').write_text('PUBLIC_TARGET_TASK')
    (target_root / 'test.patch').write_text('SECRET_EVALUATOR_PATCH')
    (target_root / 'reference.patch').write_text('SECRET_TARGET_GOLD')
    labels = {'f2p': ['sympy/tests/test_cpu.py::test_fix_' + str(i) for i in range(2)],
              'ptp': ['sympy/tests/test_cpu.py::test_reg_' + str(i) for i in range(320)]}

    def result(names, state):
        record = dict(exit=int(state == 'failed'), result=dict(tests={n: state for n in names}, fatal=[]))
        record['coverage'] = f.h.pool.classify(names, record)
        return record

    arms = {'base_with_tests': {'f2p': result(labels['f2p'], 'failed'), 'ptp': result(labels['ptp'], 'passed')},
            'gold_with_tests': {'f2p': result(labels['f2p'], 'passed'), 'ptp': result(labels['ptp'], 'passed')}}
    qualified = f.h.pool.qualification(arms['base_with_tests']['f2p'], arms['gold_with_tests']['f2p'],
                                       arms['base_with_tests']['ptp'], arms['gold_with_tests']['ptp'])
    spec = dict(instance_id=target, repo='sympy/sympy', base_commit='70cd4ffd093ac224fc0226c1be58f9163e2c800a',
                dataset_file='SWEContextBench_Related_Lite.parquet')
    case = dict(spec=spec, labels=labels, arms=arms, qualification=qualified, clean_base_sha256=s.tree(clean),
                input_sha256={k: s.sha(target_root / k) for k in ('task.txt', 'test.patch')})
    dep = {'path': str(f.private / 'sympy_environment.json'), 'sha256': 'a' * 64}
    ancestry = f.private / 'ancestry.json'; ancestry_sha = write_json(ancestry, {'fixture': 'source-before-target'})
    monkeypatch.setattr(t, 'SYMPY_ANCESTRY_SHA', ancestry_sha, raising=False)
    contract = f.private / 'target_contract.json'
    contract_sha = write_json(contract, {'cases': [spec], 'ancestry': {'path': str(ancestry), 'sha256': ancestry_sha},
        'runtime': {'image': f.h.pool.IMAGE, 'sympy_dependency_manifest': dep}})
    receipt = target_root.parent / 'receipt.json'
    receipt_sha = write_json(receipt, {'status': 'NOT_QUALIFIED', 'model_calls': 0, 'cases': {target: case},
                                       'input_sha256': {str(contract): contract_sha, str(ancestry): ancestry_sha}})
    monkeypatch.setattr(t, 'SYMPY_QUALIFICATION_SHA', receipt_sha, raising=False)
    monkeypatch.setattr(t, 'SYMPY_CONTRACT_SHA', contract_sha, raising=False)
    monkeypatch.setattr(f.h.pool, 'dependencies', lambda kind, ref, bindings: 'CPU_SYMPY_DEPENDENCIES')

    projection = json.loads((f.projection / 'manifest.json').read_text())
    projection.update(blocked_packages=['sympy'], source_site_paths={'default': str(f.private / 'swe_contextbench_sympy_python38_env_20261104/site')})
    f.projection_sha = write_json(f.projection / 'manifest.json', projection)
    sources = dict(s.SOURCES); sources[source_id] = (*sources[source_id][:-1], f.projection_sha)
    monkeypatch.setattr(s, 'SOURCES', sources)

    source_dir = f.private / 'source_repair'; attempt = source_dir / 'attempt_v1'; (attempt / 'inputs').mkdir(parents=True)
    task = attempt / 'inputs/source_task.txt'; task.write_text('PUBLIC_SOURCE_TASK')
    teacher = source_dir / 'teacher_patch_v2'; (teacher / 'false').mkdir(parents=True)
    diff = teacher / 'false/adapted.diff'; diff.write_text('SYNTHETIC_GENERATED_SOURCE_DIFF')
    pair = source_dir / 'pairs.json'; pair_sha = write_json(pair, {'schema': 'qualified_source_target_pairs_v1',
        'source_result': {'path': str(f.receipt), 'sha256': s.RESULT_SHA}, 'rows': [{'source': source_id, 'target': target}]})
    ref = lambda path, digest: {'path': str(path), 'sha256': digest}
    attempt_manifest = attempt / 'manifest.json'
    attempt_sha = write_json(attempt_manifest, dict(schema='contextbench_source_v2', root=str(attempt), source=source_id,
        repo='sympy/sympy', base='748ce73479ee2cd5c861431091001cc18943c735', public_task_sha256=s.sha(task),
        registry=ref(pair, pair_sha), source_result={'path': str(f.receipt), 'sha256': s.RESULT_SHA}))
    teacher_protocol = source_dir / 'teacher_protocol.json'
    teacher_protocol_sha = write_json(teacher_protocol, {'schema': 'CONTEXTBENCH_TEACHER_PATCH_V1',
        'source_manifest': ref(attempt_manifest, attempt_sha), 'output_root': str(teacher)})
    teacher_manifest = teacher / 'manifest.json'
    teacher_manifest_sha = write_json(teacher_manifest, dict(schema='CONTEXTBENCH_TEACHER_PATCH_PREPARED_V1', root=str(teacher),
        source=source_id, source_public_task_sha256=s.sha(task), protocol=ref(teacher_protocol, teacher_protocol_sha)))
    teacher_receipt = teacher / 'false/receipt.json'
    teacher_receipt_sha = write_json(teacher_receipt, dict(status='GENERATION_FAULT', source=source_id, arm='false', source_success=False,
        prepared_manifest_sha256=teacher_manifest_sha, protocol=ref(teacher_protocol, teacher_protocol_sha),
        response={'finish_reason': 'stop'}, patch={'check_exit': 128, 'apply_exit': None}))
    def source_score(count):
        return {'exit': 0, 'result': {'fatal': []}, 'coverage': {'complete': True, 'reported_tests': count,
                'labels': {'fixture_' + str(i): 'passed' for i in range(count)}}}
    recount = teacher / 'recount_evaluation_v1/D_RESULT_V1.json'
    recount_value = {'schema': 'D_POSTHOC_RECOUNT_RESULT_V1', 'new_model_POST': 0, 'training': 0, 'results': [dict(
        arm='false', primary_receipt_sha256=teacher_receipt_sha, patch_sha256=s.sha(diff), generated_program_text_changed=False,
        commands=[{'args': ['git', 'apply', '--recount', '--check', 'fixture.diff'], 'exit': 0},
                  {'args': ['git', 'apply', '--recount', 'fixture.diff'], 'exit': 0}],
        status='EVALUATED_AFTER_GIT_RECOUNT', source_success=True,
        scoring={'passed': True, 'suites': {'f2p': source_score(1), 'ptp': source_score(13)}})]}
    recount_sha = write_json(recount, recount_value)
    closure = teacher / 'D_CLOSURE_V1.json'
    closure_value = dict(schema='D_TEACHER_CORRECTION_CLOSURE_V1', status='ONE_ENGINEERING_ASSISTED_SOURCE_CORRECTION_QUALIFIED',
        source=source_id, records=[dict(version='teacher_patch_v2', arm='false', receipt_sha256=teacher_receipt_sha)],
        secondary=dict(path=str(recount), sha256=recount_sha, posthoc=True, false_f2p='1/1', false_ptp='13/13'))
    closure_sha = write_json(closure, closure_value)
    record = {'schema': 'contextbench_source_repair_record_v1', 'source_id': source_id, 'repo': 'sympy/sympy',
        'source_base_commit': '748ce73479ee2cd5c861431091001cc18943c735', 'pair_registry': ref(pair, pair_sha),
        'source_manifest': ref(attempt_manifest, attempt_sha), 'teacher_protocol': ref(teacher_protocol, teacher_protocol_sha),
        'teacher_manifest': ref(teacher_manifest, teacher_manifest_sha), 'teacher_receipt': ref(teacher_receipt, teacher_receipt_sha),
        'recount_result': ref(recount, recount_sha), 'closure': ref(closure, closure_sha),
        'source_task': ref(task, s.sha(task)), 'repair_patch': ref(diff, s.sha(diff))}
    for name, value in {'SYMPY_PAIR_REGISTRY_SHA':pair_sha, 'SYMPY_SOURCE_MANIFEST_SHA':attempt_sha,
        'SYMPY_TEACHER_PROTOCOL_SHA':teacher_protocol_sha, 'SYMPY_TEACHER_MANIFEST_SHA':teacher_manifest_sha,
        'SYMPY_TEACHER_RECEIPT_SHA':teacher_receipt_sha, 'SYMPY_RECOUNT_SHA':recount_sha,
        'SYMPY_CLOSURE_SHA':closure_sha, 'SYMPY_SOURCE_TASK_SHA':s.sha(task), 'SYMPY_REPAIR_PATCH_SHA':s.sha(diff)}.items():
        monkeypatch.setattr(t, name, value, raising=False)
    evidence = source_dir / 'source_repair_record.json'; evidence_sha = write_json(evidence, record)
    protocol = f.private / 'sympy_target_protocol.json'
    value = dict(schema='contextbench_sympy_target_comparison_v1', target=target, arms=['none', 'source_repair_record'],
        qualification=ref(receipt, receipt_sha), qualification_contract=ref(contract, contract_sha),
        source_evidence=ref(evidence, evidence_sha), projection=ref(f.projection, f.projection_sha),
        profile=ref(f.profile, f.profile_sha), caps=dict(posts=4, seconds=120, combined_wire_bytes=2*1024**2),
        sampling=dict(seed=17, temperature=0.2, native_thinking=False, context=32768, output=8192))
    f.protocol=protocol; f.protocol_value=value; f.protocol_sha=write_json(protocol,value)
    f.record=record; f.evidence=evidence; f.recount=recount; f.recount_value=recount_value
    f.closure=closure; f.closure_value=closure_value; f.diff=diff; f.target_root=target_root
    f.target_receipt=receipt; f.target_result=json.loads(receipt.read_text())
    return f


def test_sympy_prepare_isolated_two_arms_without_starting_process(sympy_target_inputs, monkeypatch):
    f = sympy_target_inputs
    def forbidden(*_, **__): raise AssertionError('CPU prepare must not execute processes')
    monkeypatch.setattr(s.subprocess, 'run', forbidden); monkeypatch.setattr(s.subprocess, 'Popen', forbidden)
    outputs = {}
    for arm in f.protocol_value['arms']:
        root = f.private / ('sympy_' + arm)
        out = t.prepare(f.protocol, f.protocol_sha, arm, root); m, _, actor, _ = t.verify(root, out['manifest_sha256'])
        outputs[arm] = (root, m, (root / 'inputs/task.txt').read_text())
        assert m['target'] == 'sympy__sympy-9384' and m['repo'] == 'sympy/sympy'
        assert m['models_called'] == m['container_runs'] == 0
        assert m['baseline'] == m['work'] and actor['sites'] == {'default': str(f.projection / 'deps/default')}
        assert (root / 'scoring/test.patch').read_text() == 'SECRET_EVALUATOR_PATCH'
        assert not any('patch' in p.name or 'evidence' in p.name for p in (root / 'inputs').iterdir())
        assert all('SECRET_' not in p.read_text(errors='ignore') for p in (root / 'inputs').iterdir() if p.is_file())
    assert 'PUBLIC_SOURCE_TASK' not in outputs['none'][2]
    assert 'SYNTHETIC_GENERATED_SOURCE_DIFF' in outputs['source_repair_record'][2]
    assert 'teacher-assisted' in outputs['source_repair_record'][2].lower()
    assert outputs['source_repair_record'][2].startswith(outputs['none'][2])


@pytest.mark.parametrize('change', ['target_base', 'target_unqualified', 'target_skip', 'target_tree', 'target_test_patch',
                                   'unapproved_profile', 'missing_recount', 'extra_record_field', 'changed_patch'])
def test_sympy_rejects_unqualified_or_unbound_inputs_before_copy(sympy_target_inputs, monkeypatch, change):
    f = sympy_target_inputs
    if change in ('target_base', 'target_unqualified', 'target_skip'):
        case = f.target_result['cases']['sympy__sympy-9384']
        if change == 'target_base': case['spec']['base_commit'] = '0' * 40
        elif change == 'target_unqualified': case['qualification']['qualified'] = False
        else: case['arms']['gold_with_tests']['ptp']['result']['tests'][case['labels']['ptp'][0]] = 'skipped'
        digest = write_json(f.target_receipt, f.target_result)
        monkeypatch.setattr(t, 'SYMPY_QUALIFICATION_SHA', digest, raising=False)
        f.protocol_value['qualification']['sha256'] = digest
    elif change == 'target_tree':
        (f.target_root / 'clean_base/sympy/refine.py').write_text('CHANGED_TARGET_BASE')
    elif change == 'target_test_patch':
        (f.target_root / 'test.patch').write_text('CHANGED_EVALUATOR_PATCH')
    elif change == 'unapproved_profile':
        f.protocol_value['profile']['sha256'] = '0' * 64
    elif change == 'missing_recount':
        f.record.pop('recount_result')
    elif change == 'extra_record_field':
        f.record['target_gold'] = 'SHOULD_NEVER_BE_VISIBLE'
    else:
        f.diff.write_text('MODIFIED_SOURCE_DIFF')
        f.record['repair_patch']['sha256'] = s.sha(f.diff)
    if change in ('missing_recount', 'extra_record_field', 'changed_patch'):
        f.protocol_value['source_evidence']['sha256'] = write_json(f.evidence, f.record)
    f.protocol_sha = write_json(f.protocol, f.protocol_value)
    with pytest.raises((ValueError, KeyError)): t.prepare(f.protocol, f.protocol_sha, 'source_repair_record', f.root)
    assert not f.root.exists()


def test_sympy_actor_mounts_exclude_qualification_and_scorer(sympy_target_inputs, monkeypatch):
    f=sympy_target_inputs; out=t.prepare(f.protocol, f.protocol_sha, 'source_repair_record', f.root)
    _,h,actor,profile=t.verify(f.root,out['manifest_sha256']); bridge=f.private/'bridge';bridge.mkdir()
    monkeypatch.setattr(s.os,'getuid',lambda:1000,raising=False);monkeypatch.setattr(s.os,'getgid',lambda:1000,raising=False)
    cmd=s.docker_command(f.root,actor,bridge,profile,h,'CPU_SYMPY')
    mounts=[x for x in cmd if 'type=bind' in x]
    assert not any(str(f.target_root.parent) in x or 'scoring' in x or str(f.evidence.parent) in x for x in mounts)
    assert cmd[-1]=='3.8' and cmd[cmd.index('--network')+1]=='none'


def test_sympy_rejects_rehashed_unverified_recount(sympy_target_inputs, monkeypatch):
    f = sympy_target_inputs
    f.recount_value['results'][0]['generated_program_text_changed'] = True
    recount_sha = write_json(f.recount, f.recount_value)
    monkeypatch.setattr(t, 'SYMPY_RECOUNT_SHA', recount_sha, raising=False)
    f.record['recount_result']['sha256'] = recount_sha
    f.closure_value['secondary']['sha256'] = recount_sha
    closure_sha = write_json(f.closure, f.closure_value)
    monkeypatch.setattr(t, 'SYMPY_CLOSURE_SHA', closure_sha, raising=False)
    f.record['closure']['sha256'] = closure_sha
    f.protocol_value['source_evidence']['sha256'] = write_json(f.evidence, f.record)
    f.protocol_sha = write_json(f.protocol, f.protocol_value)
    with pytest.raises(ValueError, match='recount'):
        t.prepare(f.protocol, f.protocol_sha, 'source_repair_record', f.root)
    assert not f.root.exists()


def test_sympy_preparation_rejects_qualification_parent_as_output(sympy_target_inputs):
    f = sympy_target_inputs; root = f.target_root / 'nested_actor'
    with pytest.raises(ValueError, match='fresh disjoint'):
        t.prepare(f.protocol, f.protocol_sha, 'none', root)
    assert not root.exists()


def test_sympy_execute_dispatch_uses_existing_scorer_without_running_it(sympy_target_inputs, monkeypatch):
    f=sympy_target_inputs; out=t.prepare(f.protocol,f.protocol_sha,'none',f.root); calls=[]
    def fake_execute(root,digest,prepared,verify_prepared,**kwargs):
        calls.append(kwargs); return {'status':'CPU_FAKE','target_success':False}
    monkeypatch.setattr(s,'execute_prepared',fake_execute)
    result=t.execute(f.root,out['manifest_sha256'],f.protocol,f.protocol_sha,'none')
    assert result['target_success'] is False and calls[0]['identity']=={'target':'sympy__sympy-9384','arm':'none'}
    assert calls[0]['score_prepared'] is s.score


def test_sympy_cli_prepares_only_the_explicit_arm(sympy_target_inputs, capsys):
    f = sympy_target_inputs
    exit_code = t.main(['--prepare', '--protocol', str(f.protocol), '--protocol-sha', f.protocol_sha,
                        '--arm', 'source_repair_record', '--root', str(f.root)])
    output = json.loads(capsys.readouterr().out)
    assert exit_code == 0 and output['status'] == 'CPU_PREPARED'
    assert output['target'] == 'sympy__sympy-9384' and output['arm'] == 'source_repair_record'
