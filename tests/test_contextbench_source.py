"""CPU engineering controls only: synthetic sources and fake socket pairs, no model evidence."""
import hashlib
import copy
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import threading
import time
from types import SimpleNamespace

import pytest

HERE = Path(__file__).resolve().parents[1] / 'research/agent_frontier_portfolio_20261029'
sys.path.insert(0, str(HERE))
import run_contextbench_source as m
import qualify_contextbench_pool as pool
import run_alfworld_actor_20261106 as actor
import run_django_aggregation_agent_20261106 as agg
from scripts.graph import research_actor_dependencies as deps


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True); path.write_text(json.dumps(value))
    return m.sha(path)


@pytest.fixture
def prepared_inputs(tmp_path, monkeypatch):
    """Synthetic metadata/projection; real tree/hash and projection verification."""
    private = tmp_path / 'private'; private.mkdir(); monkeypatch.setattr(m, 'PRIVATE', private)
    result_root = private / 'qualification'; result_root.mkdir(); cases = {}; rows = []; sources = dict(m.SOURCES)
    projection = private / 'projection'; (projection / 'runtime/bin').mkdir(parents=True)
    (projection / 'runtime/bin/python').write_text('synthetic CPU control, not executable')
    (projection / 'deps/default').mkdir(parents=True)
    (projection / 'deps/default/asgiref.py').write_text('synthetic third party')
    dep_manifest = dict(version=1, python='3.8', blocked_packages=['django'], site_names=['default'],
        source_site_paths={'default': str(private / 'swe_contextbench_django_env_20261104/site')}, files={name: dict(sha256=digest, bytes=(projection/name).stat().st_size) for name, digest in m.tree(projection).items()})
    dep_sha = write_json(projection / 'manifest.json', dep_manifest)
    sources['django__django-12453'] = (*sources['django__django-12453'][:-1], dep_sha); monkeypatch.setattr(m, 'SOURCES', sources)
    for source, (repo, base, target, count, _) in sources.items():
        root = result_root / source; clean = root / 'clean_base'; (clean / 'tests').mkdir(parents=True)
        (clean / 'module.py').write_text('value = 0\n'); (clean / 'tests/test_public.py').write_text('assert True\n')
        task = root / 'task.txt'; task.write_text('Public author suggestion diff is allowed.\n')
        patch = root / 'test.patch'; patch.write_text('synthetic evaluator-only tests')
        cases[source] = dict(spec=dict(instance_id=source, repo=repo, base_commit=base, role='source', related_target_id=target),
            qualification=dict(qualified=True), labels=dict(f2p=['test.fail'], ptp=['test.pass' + str(i) for i in range(count)]),
            clean_base_sha256=m.tree(clean), input_sha256={'task.txt': m.sha(task), 'test.patch': m.sha(patch)})
        rows.append(dict(source=source, target=target, clean_base=str(clean)))
    receipt = result_root / 'receipt.json'; digest = write_json(receipt, dict(status='QUALIFIED', model_calls=0, cases=cases))
    monkeypatch.setattr(m, 'RESULT_SHA', digest)
    registry = private / 'registry.json'; registry_sha = write_json(registry, dict(schema='qualified_source_target_pairs_v1', source_result=dict(path=str(receipt), sha256=digest), rows=rows))
    monkeypatch.setattr(m, 'REGISTRY_SHA', registry_sha)
    profile = private / 'profile.json'; profile_sha = write_json(profile, dict(model_id='qwen38-27b-fp8', context=32768, output=8192, host='127.0.0.1', port=1))
    monkeypatch.setattr(m, 'PROFILE_SHA', profile_sha)
    binaries = private / 'bin'; binaries.mkdir()
    for name in ('opencode', 'rg'): (binaries / name).write_text('synthetic tool')
    def forbidden(*_, **__): raise AssertionError('prepare must not execute or inspect a backend')
    h = SimpleNamespace(actor=actor, agg=agg, deps=deps, pool=pool,
        teacher=SimpleNamespace(_vllm_profile_fields=lambda _: None, validate_vllm_model_profile=forbidden, verify_vllm_backend=forbidden),
        tools=SimpleNamespace(OPENCODE=binaries / 'opencode', RG=binaries / 'rg', ripgrep_binding=lambda: []))
    monkeypatch.setattr(m, 'helpers', lambda: h)
    monkeypatch.setattr(m, 'scoring_dependencies', lambda *_: dict(bindings={}, limits='synthetic CPU dependency control'))
    return SimpleNamespace(private=private, root=private / 'attempt', registry=registry, registry_sha=registry_sha,
        source='django__django-12453', projection=projection, projection_sha=dep_sha, profile=profile, profile_sha=profile_sha, h=h,
        receipt=receipt, cases=cases)


def prepare(f):
    return m.prepare(f.registry, f.registry_sha, f.source, f.root, f.projection, f.projection_sha, f.profile, f.profile_sha)


@pytest.fixture
def matplotlib_inputs(prepared_inputs, monkeypatch):
    """Synthetic native-result records, never benchmark gold or an actual actor."""
    f = prepared_inputs
    source, target = 'matplotlib__matplotlib-25332', 'matplotlib__matplotlib-25352'
    result_root = f.private / 'mpl_qualification'; result_root.mkdir()
    cases = {}
    for identity, base, role, count in [
        (source, '66ba515e671638971bd11a34cff12c107a437e0b', 'source', 181),
        (target, '3742e7e8385e70072fb2521a411a25dd69d22dbf', 'target', 60),
    ]:
        root = result_root / identity; clean = root / 'clean_base'
        (clean / 'lib/matplotlib/tests').mkdir(parents=True)
        (clean / 'lib/matplotlib/cbook.py').write_text('CPU_PUBLIC_BASE = 1\n')
        (clean / 'lib/matplotlib/_native.so').write_bytes(b'CPU_NOT_AN_ELF_LIBRARY')
        (root / 'task.txt').write_bytes(b'Public source task only.\r\n' if role == 'source' else b'Private future task')
        (root / 'test.patch').write_text('CPU_EVALUATOR_ONLY_PATCH')
        labels = dict(f2p=['lib/matplotlib/tests/test_cpu.py::test_f2p'],
                      ptp=['lib/matplotlib/tests/test_cpu.py::test_ptp_' + str(i) for i in range(count)])
        arms = {}
        for arm, fail in [('base_with_tests', True), ('gold_with_tests', False)]:
            tests = {n: 'passed' for n in labels['f2p'] + labels['ptp']}
            if fail: tests[labels['f2p'][0]] = 'failed'
            payload = dict(tests=tests, fatal=[])
            log = root / (arm + '.log'); log.write_text(pool.MARKER + json.dumps(payload) + '\n')
            arms[arm] = dict(group=dict(exit=int(fail), result=payload, log_sha256=m.sha(log)))
        cases[identity] = dict(spec=dict(instance_id=identity, repo='matplotlib/matplotlib', base_commit=base, role=role),
            labels=labels, arms=arms, qualification=pool.matplotlib_qualification(
                arms['base_with_tests']['group'], arms['gold_with_tests']['group'], labels),
            clean_base_sha256=m.tree(clean), input_sha256={name:m.sha(root/name) for name in ['task.txt','test.patch']},
            native_overlay={'_native.so':m.sha(clean/'lib/matplotlib/_native.so')})
    contract = f.private / 'mpl_contract.json'
    contract_sha = write_json(contract, dict(runtime={'CPU_RUNTIME':True}))
    receipt = result_root / 'receipt.json'
    digest = write_json(receipt, dict(status='QUALIFIED', model_calls=0, training=0,
        cases=cases, input_sha256={str(contract):contract_sha}, unrun_groups=[]))
    projection = f.private / 'mpl_projection'; (projection / 'runtime/bin').mkdir(parents=True)
    (projection / 'runtime/bin/python').write_text('CPU_NON_EXECUTABLE')
    for slot in ['source','target']:
        (projection / 'deps' / slot).mkdir(parents=True)
        (projection / 'deps' / slot / 'numpy.py').write_text('CPU_NOT_A_PACKAGE')
    value = dict(version=1, python='3.10', blocked_packages=['matplotlib','mpl_toolkits'], site_names=['source','target'],
        source_site_paths={'source':'/CPU/source','target':'/CPU/target'},
        files={name:dict(sha256=digest,bytes=(projection/name).stat().st_size) for name,digest in m.tree(projection).items()})
    projection_sha = write_json(projection/'manifest.json',value)
    registry = f.private / 'mpl_registry.json'
    reg = dict(schema='qualified_matplotlib_source_v1', source_result=dict(path=str(receipt),sha256=digest),
        qualification_contract=dict(path=str(contract),sha256=contract_sha),
        actor_projection=dict(path=str(projection),sha256=projection_sha),
        rows=[dict(source=source,target=target,clean_base=str(result_root/source/'clean_base'))])
    f.source=source;f.registry=registry;f.registry_sha=write_json(registry,reg)
    f.projection=projection;f.projection_sha=projection_sha;f.receipt=receipt;f.cases=cases;f.reg=reg
    monkeypatch.setattr(m,'scoring_dependencies',lambda *_:dict(bindings={},limits='CPU Matplotlib',matplotlib_runtime={'CPU_RUNTIME':True}))
    return f


def test_matplotlib_source_prepares_python310_without_exposing_target_or_gold(matplotlib_inputs):
    f=matplotlib_inputs;result=prepare(f);manifest,h,actor,_=m.verify(f.root,result['manifest_sha256'])
    assert manifest['source_runtime']['python']=='3.10'
    assert (f.root/'inputs/source_task.txt').read_bytes()==(f.receipt.parent/f.source/'task.txt').read_bytes()
    prompt=(f.root/'inputs/task.txt').read_text()
    assert 'Python 3.10' in prompt and '25352' not in prompt and 'Private future task' not in prompt
    assert not any('reference.patch' in str(p) for p in (f.root/'inputs').rglob('*'))
    bridge=f.private/'bridge';bridge.mkdir()
    cmd=m.docker_command(f.root,actor,bridge,json.loads(f.profile.read_text()),h,'CPU_MPL',source_runtime=manifest['source_runtime'])
    assert 'PYTHONPATH=/workspace/lib:/deps' in cmd and 'MPLBACKEND=Agg' in cmd and cmd[-1]=='3.10'
    assert any('dst=/deps,readonly' in v and '/deps/source' in v for v in cmd)
    assert not any(str(f.receipt.parent) in v for v in cmd if 'type=bind' in v)


@pytest.mark.parametrize('change',['target_unqualified','skip','missing','wrong_projection','native_change','target_in_source'])
def test_matplotlib_source_rejects_incomplete_or_mixed_evidence(matplotlib_inputs,change):
    f=matplotlib_inputs
    if change=='wrong_projection': f.projection_sha='0'*64
    elif change=='native_change':
        (f.receipt.parent/f.source/'clean_base/lib/matplotlib/_native.so').write_bytes(b'changed')
    elif change=='target_in_source':
        p=f.receipt.parent/f.source/'task.txt';p.write_text('Future target #25352');x=json.loads(f.receipt.read_text())
        x['cases'][f.source]['input_sha256']['task.txt']=m.sha(p)
        f.reg['source_result']['sha256']=write_json(f.receipt,x);f.registry_sha=write_json(f.registry,f.reg)
    else:
        x=json.loads(f.receipt.read_text());target=x['cases']['matplotlib__matplotlib-25352']
        if change=='target_unqualified':target['qualification']['qualified']=False
        else:
            group=target['arms']['gold_with_tests']['group'];node=target['labels']['ptp'][0]
            if change=='skip':group['result']['tests'][node]='skipped'
            else:group['result']['tests'].pop(node)
        f.reg['source_result']['sha256']=write_json(f.receipt,x);f.registry_sha=write_json(f.registry,f.reg)
    with pytest.raises(ValueError):prepare(f)
    assert not f.root.exists()


def test_matplotlib_native_overlay_stays_frozen_during_actor_edits(matplotlib_inputs):
    f=matplotlib_inputs;digest=prepare(f)['manifest_sha256']
    (f.root/'work/lib/matplotlib/_native.so').write_bytes(b'actor cannot replace native dependency')
    with pytest.raises(ValueError,match='native'):m.verify(f.root,digest,initial=False)


def test_matplotlib_candidate_scorer_uses_only_qualified_source_dependencies(tmp_path,monkeypatch):
    labels=['lib/matplotlib/tests/test_cpu.py::test_f2p'];calls=[]
    assets=dict(runtime='/CPU/python310',sites=dict(source='/CPU/source',target='/CPU/future'))
    def command(work,nodes,runner,name,cid,given,slot):
        assert given is assets and slot=='source' and nodes==labels
        calls.append(slot);return ['CPU_ONLY_COMMAND']
    def owned(cmd,name,cid,stdout,stderr,timeout):
        assert cmd==['CPU_ONLY_COMMAND'];stdout.write_text(pool.MARKER+json.dumps(dict(tests={labels[0]:'passed'},fatal=[]))+'\n');stderr.write_bytes(b'')
        return dict(exit=0,cleanup=dict(status='CPU_NO_CONTAINER'))
    monkeypatch.setattr(m,'run_owned',owned)
    h=SimpleNamespace(pool=SimpleNamespace(mem_available=lambda:8*1024**3,matplotlib_command=command,
        MARKER=pool.MARKER,classify=pool.classify,parse_machine_result=pool.parse_machine_result))
    record=m.scored_test(tmp_path,'matplotlib/matplotlib',labels,tmp_path/'runner.py',tmp_path,'f2p',h,matplotlib_assets=assets)
    assert record['coverage']['complete'] is True and calls==['source']
    with pytest.raises(ValueError,match='assets'):m.scored_test(tmp_path,'matplotlib/matplotlib',labels,tmp_path/'runner.py',tmp_path,'other',h)


def test_matplotlib_rejects_edited_native_result_even_if_qualification_boolean_is_true(matplotlib_inputs):
    f=matplotlib_inputs;case=f.cases[f.source];log=f.receipt.parent/f.source/'gold_with_tests.log'
    log.write_text(pool.MARKER+json.dumps(dict(tests={},fatal=[]))+'\n')
    with pytest.raises(ValueError,match='log'):prepare(f)
    assert not f.root.exists()


@pytest.fixture
def development_inputs(matplotlib_inputs):
    """Synthetic single-source qualification; no real task or native execution."""
    f=matplotlib_inputs;old=f.source;source='matplotlib__matplotlib-90001'
    (f.receipt.parent/old).rename(f.receipt.parent/source)
    case=copy.deepcopy(f.cases[old]);spec=case['spec'];f.source=source
    spec.update(instance_id=source,role='DEVELOPMENT_SOURCE',dataset_file='CPU_SOURCE.parquet',
        problem_sha256=case['input_sha256']['task.txt'],archive={'path':'CPU_ARCHIVE','sha256':'a'*64},
        dependency_slot='source',label_map={k:[dict(published=n,node=n) for n in nodes] for k,nodes in case['labels'].items()})
    contract=Path(f.reg['qualification_contract']['path'])
    value=dict(schema='contextbench_pool_qualification_matplotlib_source_v1',dataset_manifest={'CPU':'fixed'},
        cases=[spec],runtime={'CPU_RUNTIME':True})
    f.reg['qualification_contract']['sha256']=write_json(contract,value)
    f.cases={source:case}
    result=dict(schema='matplotlib_source_qualification_result_v1',status='QUALIFIED',model_calls=0,training=0,
        cases=f.cases,input_sha256={str(contract):m.sha(contract)},unrun_groups=[])
    f.reg.update(schema='qualified_matplotlib_development_source_v1',
        rows=[dict(source=source,clean_base=str(f.receipt.parent/source/'clean_base'))])
    f.reg['source_result']['sha256']=write_json(f.receipt,result);f.registry_sha=write_json(f.registry,f.reg)
    return f


def test_development_source_dynamic_identity_and_exact_coverage_without_target(development_inputs):
    f=development_inputs;result=prepare(f);manifest,h,actor,_=m.verify(f.root,result['manifest_sha256'])
    assert manifest['source']==f.source and manifest['source_role']=='DEVELOPMENT_SOURCE'
    assert manifest['labels']==f.cases[f.source]['labels']
    assert set(p.name for p in (f.root/'inputs').iterdir())=={'source_task.txt','task.txt','guest.py','opencode.json'}
    assert not any(x in (f.root/'inputs/task.txt').read_text() for x in ('25352','CPU_EVALUATOR_ONLY_PATCH','CPU_ARCHIVE'))
    assert manifest['sampling']['native_thinking'] is False
    assert 'request_policy' not in manifest and 'production_prefix_capture' not in manifest


def test_development_source_opt_in_policy_and_capture_are_manifest_bound(development_inputs):
    f=development_inputs
    result=m.prepare(f.registry,f.registry_sha,f.source,f.root,f.projection,f.projection_sha,f.profile,f.profile_sha,
        request_policy='teacher27b_thinking_low_v1',capture_production_prefix=True)
    manifest,_,_,_=m.verify(f.root,result['manifest_sha256'])
    assert manifest['request_policy']['chat_template_kwargs']==dict(enable_thinking=True,reasoning_effort='low')
    assert manifest['sampling']==dict(seed=17,temperature=.2,native_thinking=True,reasoning_effort='low',context=32768,output=8192)
    assert json.loads((f.root/'inputs/opencode.json').read_text())['compaction']=={'auto':False,'prune':False}
    for key,value in [('source_role','target'),('caps',dict(m.CAPS,posts=49)),
            ('request_policy',{'version':'unapproved'}),('production_prefix_capture',{}),
            ('sampling',dict(manifest['sampling'],seed=18)),('opencode_compaction',{'auto':True,'prune':False})]:
        changed=copy.deepcopy(manifest);changed[key]=value;digest=write_json(f.root/'manifest.json',changed)
        with pytest.raises(ValueError):m.verify(f.root,digest)


def test_limited_qualification_metadata_and_native_recompute_are_bound(development_inputs,monkeypatch):
    """Runtime seam control; qualifier suite tests the real origin/log verifier."""
    f=development_inputs;case=f.cases[f.source];node=case['labels']['ptp'][0]
    origin=f.private/'CPU_ORIGIN.json';origin_sha=write_json(origin,{'CPU_ONLY':'qualification origin'})
    declared=dict(nodes=[node],origin_receipt=dict(path=str(origin),sha256=origin_sha),reason='CPU declared PDF skip')
    contract=Path(f.reg['qualification_contract']['path']);value=json.loads(contract.read_text());value['expected_skips']=declared
    f.reg['qualification_contract']['sha256']=write_json(contract,value)
    calls=[]
    def validated(c,labels,bindings):
        calls.append(c['expected_skips']);assert labels==case['labels'];m.read_ref(c['expected_skips']['origin_receipt'])
        return list(c['expected_skips']['nodes'])
    monkeypatch.setattr(pool,'matplotlib_source_expected_skips',validated)
    for arm in ('base_with_tests','gold_with_tests'):
        group=case['arms'][arm]['group'];group['result']['tests'][node]='skipped'
        log=f.receipt.parent/f.source/(arm+'.log');log.write_text(pool.MARKER+json.dumps(group['result'])+'\n');group['log_sha256']=m.sha(log)
    case['qualification']=pool.matplotlib_qualification(case['arms']['base_with_tests']['group'],case['arms']['gold_with_tests']['group'],case['labels'],expected_skips=[node])
    result=json.loads(f.receipt.read_text());result.update(cases=f.cases,expected_skips=declared,qualification_scope='LIMITED_RUNTIME_SCOPE',input_sha256={str(contract):m.sha(contract)})
    f.reg['source_result']['sha256']=write_json(f.receipt,result);f.registry_sha=write_json(f.registry,f.reg)
    digest=prepare(f)['manifest_sha256'];manifest,_,_,_=m.verify(f.root,digest)
    assert calls and manifest['expected_skips']==declared and manifest['qualification_scope']=='LIMITED_RUNTIME_SCOPE'
    assert case['qualification']['base_all_ptp_pass'] is False and case['qualification']['gold_all_ptp_pass'] is False
    assert 'CPU declared PDF skip' not in (f.root/'inputs/task.txt').read_text()
    for field in ('expected_skips','qualification_scope'):
        changed=copy.deepcopy(manifest);changed.pop(field)
        with pytest.raises(ValueError):m.verify(f.root,write_json(f.root/'manifest.json',changed))
    write_json(f.root/'manifest.json',manifest)
    origin.write_text('tampered origin')
    with pytest.raises(ValueError,match='hash'):m.verify(f.root,digest)


@pytest.mark.parametrize('role,slot',[('source','source'),('target','target'),('DEVELOPMENT_SOURCE','target')])
def test_declared_skip_cannot_enter_legacy_or_target_scoring(tmp_path,role,slot):
    manifest=dict(repo='matplotlib/matplotlib',source_role=role,source=m.MPL_SOURCE_ID,
        expected_skips={'nodes':['ptp']},qualification_scope='LIMITED_RUNTIME_SCOPE')
    with pytest.raises(ValueError,match='development source only'):m.score(tmp_path,manifest,None,matplotlib_slot=slot)
    assert not (tmp_path/'scoring').exists()


@pytest.mark.parametrize('change',['role','base','labels','task','extra_case','row_target','log','skip','projection'])
def test_development_source_rejects_rebound_or_mixed_qualification(development_inputs,change):
    f=development_inputs;result=json.loads(f.receipt.read_text());case=result['cases'][f.source]
    if change=='role':case['spec']['role']='target'
    elif change=='base':case['spec']['base_commit']='b'*40
    elif change=='labels':case['labels']['ptp']=case['labels']['ptp'][:-1]
    elif change=='task':case['spec']['problem_sha256']='0'*64
    elif change=='extra_case':result['cases'][m.MPL_TARGET_ID]=copy.deepcopy(case)
    elif change=='row_target':f.reg['rows'][0]['target']=m.MPL_TARGET_ID
    elif change=='log':(f.receipt.parent/f.source/'gold_with_tests.log').write_text('changed native log')
    elif change=='projection':f.projection_sha='0'*64
    else:case['arms']['gold_with_tests']['group']['result']['tests'][case['labels']['ptp'][0]]='skipped'
    f.reg['source_result']['sha256']=write_json(f.receipt,result);f.registry_sha=write_json(f.registry,f.reg)
    with pytest.raises(ValueError):prepare(f)
    assert not f.root.exists()


def test_development_config_cannot_reenable_compaction_after_rehash(development_inputs):
    f=development_inputs;result=prepare(f);path=f.root/'manifest.json';manifest=json.loads(path.read_text())
    config=json.loads((f.root/'inputs/opencode.json').read_text());config['compaction']['auto']=True
    write_json(f.root/'inputs/opencode.json',config);manifest['inputs']=m.tree(f.root/'inputs')
    with pytest.raises(ValueError,match='config'):m.verify(f.root,write_json(path,manifest))


def test_development_node_collection_uses_read_only_qualification_validator(development_inputs,monkeypatch):
    f=development_inputs;collection=f.private/'CPU_COLLECTION.json';collection_sha=write_json(collection,{'CPU_ENGINEERING_ONLY':True})
    contract=Path(f.reg['qualification_contract']['path']);value=json.loads(contract.read_text())
    value['node_collection']=dict(path=str(collection),sha256=collection_sha)
    f.reg['qualification_contract']['sha256']=write_json(contract,value)
    result=json.loads(f.receipt.read_text());result['input_sha256']={str(contract):m.sha(contract)}
    f.reg['source_result']['sha256']=write_json(f.receipt,result);f.registry_sha=write_json(f.registry,f.reg)
    calls=[]
    def validate(c,bindings,output,ref):
        assert ref==f.reg['qualification_contract'] and output==f.receipt.parent
        m.read_ref(c['node_collection']);calls.append(c['node_collection'])
        return {'cases':[{'labels':f.cases[f.source]['labels']}]}
    monkeypatch.setattr(pool,'load_matplotlib_source',validate)
    prepared=prepare(f);m.verify(f.root,prepared['manifest_sha256'])
    assert len(calls)==2 and str(collection) not in (f.root/'inputs/task.txt').read_text()
    collection.write_text('changed actual collection receipt')
    with pytest.raises(ValueError,match='hash'):m.verify(f.root,prepared['manifest_sha256'])


@pytest.mark.parametrize('module',['lib/mpl_toolkits/axes_grid1/tests/test_cpu.py',
    'lib/mpl_toolkits/../tests/test_cpu.py','lib/mpl_toolkits/axes_grid1/private/test_cpu.py',
    'lib/mpl_toolkits/axes_grid1/tests/not_a_test.py'])
def test_development_toolkit_nodes_are_source_only_and_path_restricted(development_inputs,module):
    f=development_inputs;case=f.cases[f.source]
    change=lambda n:module+'::'+n.split('::',1)[1]
    case['labels']={k:[change(n) for n in nodes] for k,nodes in case['labels'].items()}
    case['spec']['label_map']={k:[dict(published=n,node=n) for n in nodes] for k,nodes in case['labels'].items()}
    for arm in ('base_with_tests','gold_with_tests'):
        group=case['arms'][arm]['group'];group['result']['tests']={change(n):state for n,state in group['result']['tests'].items()}
        log=f.receipt.parent/f.source/(arm+'.log');log.write_text(pool.MARKER+json.dumps(group['result'])+'\n');group['log_sha256']=m.sha(log)
    case['qualification']=pool.matplotlib_qualification(case['arms']['base_with_tests']['group'],case['arms']['gold_with_tests']['group'],case['labels'])
    contract=Path(f.reg['qualification_contract']['path']);value=json.loads(contract.read_text());value['cases']=[case['spec']]
    f.reg['qualification_contract']['sha256']=write_json(contract,value)
    result=json.loads(f.receipt.read_text());result.update(cases={f.source:case},input_sha256={str(contract):m.sha(contract)})
    f.reg['source_result']['sha256']=write_json(f.receipt,result);f.registry_sha=write_json(f.registry,f.reg)
    if '/axes_grid1/tests/test_cpu.py' in module:
        prepared=prepare(f);m.verify(f.root,prepared['manifest_sha256'])
    else:
        with pytest.raises(ValueError,match='label'):prepare(f)
        assert not f.root.exists()


@pytest.mark.parametrize('kwargs',[dict(request_policy='teacher27b_thinking_low_v1'),dict(capture_production_prefix=True)])
def test_legacy_sources_cannot_enable_new_cohort_options(prepared_inputs,kwargs):
    f=prepared_inputs
    with pytest.raises(ValueError):m.prepare(f.registry,f.registry_sha,f.source,f.root,f.projection,f.projection_sha,f.profile,f.profile_sha,**kwargs)
    assert not f.root.exists()


def test_default_source_keeps_original_sampling_and_config(prepared_inputs):
    f=prepared_inputs;result=prepare(f);manifest,_,_,profile=m.verify(f.root,result['manifest_sha256'])
    assert manifest['sampling']==dict(seed=17,temperature=.2,native_thinking=False,context=32768,output=8192)
    assert json.loads((f.root/'inputs/opencode.json').read_text())==actor.config(profile,17)
    assert not {'request_policy','production_prefix_capture','source_role','opencode_compaction'} & manifest.keys()


def test_target_lifecycle_cannot_inject_development_source_options(tmp_path,monkeypatch):
    called=[];monkeypatch.setattr(m,'resource_lock',lambda:called.append('FORBIDDEN_LOCK'))
    manifest=dict(caps=m.CAPS,source='matplotlib__matplotlib-90001',source_role='DEVELOPMENT_SOURCE',request_policy=m.THINKING_LOW_POLICY)
    with pytest.raises(ValueError,match='another actor cohort'):
        m.execute_prepared(tmp_path,'0'*64,(manifest,None,None,None),None,
            identity=dict(target=m.MPL_TARGET_ID),success_key='target_success',mode='REAL_TARGET_EPISODE')
    assert not called


def test_prepare_has_zero_process_endpoint_and_verbatim_public_input(prepared_inputs, monkeypatch):
    f = prepared_inputs
    def forbidden(*_, **__): raise AssertionError('CPU prepare crossed execution boundary')
    monkeypatch.setattr(subprocess, 'Popen', forbidden); monkeypatch.setattr(socket, 'create_connection', forbidden)
    result = prepare(f); manifest, _, _, _ = m.verify(f.root, result['manifest_sha256'])
    assert result['status'] == 'CPU_PREPARED'
    assert manifest['models_called'] == manifest['container_runs'] == 0
    original = f.receipt.parent / f.source / 'task.txt'
    assert (f.root / 'inputs/source_task.txt').read_bytes() == original.read_bytes()
    assert (f.root / 'inputs/task.txt').read_text().endswith(original.read_text())
    assert manifest['public_task_sha256'] == m.sha(original)
    assert manifest['wrapped_prompt_sha256'] != manifest['public_task_sha256']
    assert not (f.root / 'work/test.patch').exists() and not (f.root / 'inputs/reference.patch').exists()
    assert set(manifest['components']) and manifest['baseline'] == manifest['work']
    assert not (f.root / 'reservation.json').exists()


@pytest.mark.parametrize('change', ['target', 'hash', 'hardlink', 'symlink'])
def test_reject_wrong_identity_and_linked_clean_before_root(prepared_inputs, change):
    f = prepared_inputs
    if change == 'target': f.source = 'django__django-31051'
    elif change == 'hash': f.registry_sha = '0' * 64
    else:
        clean = f.receipt.parent / f.source / 'clean_base'
        if change == 'hardlink': os.link(clean / 'module.py', clean / 'alias.py')
        else: (clean / 'alias.py').symlink_to(clean / 'module.py')
    with pytest.raises(ValueError): prepare(f)
    assert not f.root.exists()


def test_wrong_profile_and_target_injection_rejected(prepared_inputs):
    f = prepared_inputs; f.profile_sha = '0' * 64
    with pytest.raises(ValueError, match='profile'): prepare(f)
    f.profile_sha = m.PROFILE_SHA; result = prepare(f)
    (f.root / 'inputs/task.txt').write_text('django__django-31051 target must not be introduced')
    with pytest.raises(ValueError, match='inputs'): m.verify(f.root, result['manifest_sha256'])


def test_projection_must_match_qualified_source_site(prepared_inputs, monkeypatch):
    f = prepared_inputs; manifest_path = f.projection / 'manifest.json'; v = json.loads(manifest_path.read_text())
    v['source_site_paths']['default'] = str(f.private / 'other-site'); f.projection_sha = write_json(manifest_path, v)
    sources = dict(m.SOURCES); sources[f.source] = (*sources[f.source][:-1], f.projection_sha); monkeypatch.setattr(m, 'SOURCES', sources)
    with pytest.raises(ValueError, match='qualified dependency'): prepare(f)
    assert not f.root.exists()


def test_actor_mounts_exact_source_surface_and_reject_ancestor(prepared_inputs):
    f = prepared_inputs; result = prepare(f); manifest, h, projection, profile = m.verify(f.root, result['manifest_sha256'])
    bridge = f.private / 'bridge'; bridge.mkdir()
    command = m.docker_command(f.root, projection, bridge, profile, h, 'fake-control')
    mounts = [command[i+1] for i, word in enumerate(command) if word == '--mount']
    assert len(mounts) == 7
    assert {v.split('dst=')[1].split(',')[0] for v in mounts} == {'/workspace', '/inputs', '/extra', '/deps', '/model', '/opt/opencode', '/usr/local/bin/rg'}
    assert command[command.index('--network')+1] == 'none' and '--read-only' in command
    assert str(f.receipt.parent) not in ' '.join(mounts) and '--privileged' not in command
    assert command[command.index('--user')+1] != '0:0'
    projection['runtime'] = str(f.root)
    with pytest.raises(ValueError, match='ancestor'): m.docker_command(f.root, projection, bridge, profile, h, 'fake')


def wire_payload(client, payload):
    body = json.dumps(payload).encode()
    client.sendall(b'POST /v1/chat/completions HTTP/1.1\r\nContent-Length: ' + str(len(body)).encode() + b'\r\n\r\n' + body)


def synthetic_payload(**extra):
    """Engineering fixture reproducing the actual bash-only description conflict."""
    return dict(messages=[{'role': 'user', 'content': 'synthetic CPU control'}],
        tools=[dict(type='function', function=dict(name='bash',
            description='DO NOT use it for file operations (reading, writing, editing, searching, finding files) - use the specialized tools for this instead.',
            parameters=dict(type='object', properties=dict(command=dict(type='string'),
                workdir=dict(type='string')), required=['command'])))], **extra)


def test_source_tool_contract_only_changes_description_without_mutating_input():
    payload = synthetic_payload(temperature=.2, seed=17, stream=True,
        chat_template_kwargs={'enable_thinking': False})
    before = copy.deepcopy(payload)
    forwarded, proof = m.prepare_tool_contract(payload)
    assert payload == before and forwarded is not payload
    description = forwarded['tools'][0]['function'].pop('description')
    expected = copy.deepcopy(before); expected['tools'][0]['function'].pop('description')
    assert forwarded == expected
    assert '/workspace' in description and all(word in description.lower() for word in ('read', 'edit', 'test'))
    assert 'specialized tools' not in description and 'DO NOT use it for file operations' not in description
    assert proof['version'] == m.TOOL_CONTRACT_VERSION
    assert proof['incoming_tools_sha256'] != proof['forwarded_tools_sha256']
    assert proof['incoming_tools_sha256'] == hashlib.sha256(json.dumps(before['tools'], ensure_ascii=False, allow_nan=False, separators=(',', ':')).encode()).hexdigest()
    forwarded['messages'][0]['content'] = 'only the copy changes'
    assert payload == before


def test_actual_fake_wire_replaces_legacy_bash_description(tmp_path, monkeypatch):
    """Fails on the old wire behavior, independent of the new pure helper."""
    bodies, workers = fake_upstream(monkeypatch); relay = relay_at(tmp_path)
    assert exchange(relay, synthetic_payload()).startswith(b'HTTP/1.1 200')
    for worker in workers: worker.join(3)
    actual = json.loads(bodies[0])['tools'][0]['function']['description']
    assert 'DO NOT use it for file operations' not in actual
    assert '/workspace' in actual and all(word in actual.lower() for word in ('read', 'edit', 'test'))


@pytest.mark.parametrize('tools', [None, [], 'bash',
    [{'type': 'function', 'function': {'name': 'edit', 'description': 'edit', 'parameters': {}}}],
    synthetic_payload()['tools'] * 2,
    synthetic_payload()['tools'] + [{'type': 'function', 'function': {'name': 'read'}}],
    [{'type': 'custom', 'function': {'name': 'bash', 'description': 'bash', 'parameters': {}}}],
    [{'type': 'function', 'function': {'name': 'bash', 'description': 'bash', 'parameters': []}}],
])
def test_invalid_source_tool_contract_never_reserves_or_connects(tmp_path, monkeypatch, tools):
    connected = []
    def forbidden(*_, **__): connected.append(True); raise AssertionError('invalid tools reached connect')
    monkeypatch.setattr(socket, 'create_connection', forbidden)
    payload = synthetic_payload(); payload['tools'] = tools
    relay = relay_at(tmp_path)
    assert exchange(relay, payload).startswith(b'HTTP/1.1 502')
    bill = relay.accounting()
    assert connected == [] and bill['actual_forwarded_posts'] == 0
    assert bill['budget_reserved_combined_wire_bytes'] == 0
    assert not list((tmp_path / 'wire').glob('*.request.json'))


def test_missing_source_tool_contract_never_connects(tmp_path, monkeypatch):
    connected = []
    def forbidden(*_, **__): connected.append(True); raise AssertionError('missing tools reached connect')
    monkeypatch.setattr(socket, 'create_connection', forbidden)
    relay = relay_at(tmp_path)
    assert exchange(relay, {'messages': []}).startswith(b'HTTP/1.1 502')
    assert connected == [] and relay.accounting()['budget_reserved_combined_wire_bytes'] == 0


def test_tool_contract_actual_fake_wire_precedes_byte_cap_and_hash(tmp_path, monkeypatch):
    payload = synthetic_payload(); before = copy.deepcopy(payload)
    projected, proof = m.prepare_tool_contract(payload)
    projected = actor.model_payload(projected, 'teacher27b', relay_at_profile(), 17)
    expected = json.dumps(projected, ensure_ascii=False, allow_nan=False, separators=(',', ':')).encode()
    bodies, workers = fake_upstream(monkeypatch); relay = relay_at(tmp_path)
    assert exchange(relay, payload).startswith(b'HTTP/1.1 200')
    for worker in workers: worker.join(3)
    assert bodies == [expected] and payload == before
    assert (tmp_path / 'wire/00001.request.json').read_bytes() == expected
    ledger = [json.loads(x) for x in (tmp_path / 'forward_ledger.jsonl').read_text().splitlines()]
    contract = next(x for x in ledger if x['event'] == 'tool_contract_prepared')
    assert all(contract[k] == v for k, v in proof.items())
    assert contract['body_sha256'] == hashlib.sha256(expected).hexdigest()
    assert contract['body_bytes'] == relay.accounting()['actual_forwarded_body_bytes'] == len(expected)
    incoming = actor.model_payload(copy.deepcopy(payload), 'teacher27b', relay_at_profile(), 17)
    assert len(json.dumps(incoming, ensure_ascii=False, separators=(',', ':')).encode()) < len(expected)
    denied = tmp_path / 'denied'; denied.mkdir(); connected = []
    def forbidden(*_, **__): connected.append(True); raise AssertionError('projected body exceeded cap')
    monkeypatch.setattr(socket, 'create_connection', forbidden)
    capped = relay_at(denied, dict(posts=1, seconds=10, combined_wire_bytes=len(expected)-1))
    assert exchange(capped, payload).startswith(b'HTTP/1.1 403')
    assert connected == [] and capped.accounting()['budget_reserved_combined_wire_bytes'] == 0
    assert (denied / 'wire/00001.request.json').read_bytes() == expected


def relay_at_profile():
    return dict(host='127.0.0.1', port=1, model_id='qwen38-27b-fp8', output=8192)


@pytest.mark.parametrize('mutation', ['legacy', 'changed_contract'])
def test_new_prepare_binds_tool_contract_and_rejects_old_policy(prepared_inputs, mutation):
    f = prepared_inputs; prepare(f); path = f.root / 'manifest.json'; manifest = json.loads(path.read_text())
    assert manifest['schema'] == 'contextbench_source_v2'
    assert manifest['tool_contract']['version'] == m.TOOL_CONTRACT_VERSION
    if mutation == 'legacy': manifest['schema'] = 'contextbench_source_v1'; manifest.pop('tool_contract')
    else: manifest['tool_contract']['version'] = 'unapproved'
    digest = write_json(path, manifest)
    with pytest.raises(ValueError, match='policy'): m.verify(f.root, digest)


def fake_upstream(monkeypatch):
    """Socket pairs only, no listening endpoint; capture the actual serialized POST."""
    bodies = []; workers = []
    def connect(*_, **__):
        sender, receiver = socket.socketpair()
        def respond():
            data = b''
            while b'\r\n\r\n' not in data: data += receiver.recv(65536)
            head, body = data.split(b'\r\n\r\n', 1)
            size = int(next(l.split(b':', 1)[1] for l in head.split(b'\r\n') if l.startswith(b'Content-Length:')))
            while len(body) < size: body += receiver.recv(size-len(body))
            bodies.append(body)
            response = b'data: {"usage":{"total_tokens":7}}\n\ndata: [DONE]\n\n'
            receiver.sendall(b'HTTP/1.1 200 OK\r\nContent-Length: ' + str(len(response)).encode() + b'\r\n\r\n' + response); receiver.close()
        worker = threading.Thread(target=respond); worker.start(); workers.append(worker); return sender
    monkeypatch.setattr(socket, 'create_connection', connect)
    return bodies, workers


def exchange(relay, payload=None):
    client, receiver = socket.socketpair(); client.settimeout(5)
    worker = threading.Thread(target=relay.handle, args=(receiver,)); worker.start()
    wire_payload(client, synthetic_payload() if payload is None else payload)
    data = b''
    while True:
        piece = client.recv(65536)
        if not piece: break
        data += piece
    client.close(); worker.join(5); assert not worker.is_alive(); return data


def relay_at(tmp_path, caps=None):
    return m.Relay(tmp_path, dict(host='127.0.0.1', port=1, model_id='qwen38-27b-fp8', output=8192),
        SimpleNamespace(actor=actor, agg=agg), deadline=time.monotonic()+10, caps=caps)


def test_thinking_low_all_real_fake_wire_requests_use_frozen_nested_policy(tmp_path,monkeypatch):
    bodies,workers=fake_upstream(monkeypatch)
    relay=m.Relay(tmp_path,relay_at_profile(),SimpleNamespace(actor=actor,agg=agg),deadline=time.monotonic()+10,
        request_policy=copy.deepcopy(m.THINKING_LOW_POLICY))
    for seed in (123,456):
        payload=synthetic_payload(seed=seed,reasoning_effort='high',chat_template_kwargs={'enable_thinking':False,'reasoning_effort':'high'})
        assert exchange(relay,payload).startswith(b'HTTP/1.1 200')
    for worker in workers:worker.join(5);assert not worker.is_alive()
    for index,body in enumerate(bodies,1):
        value=json.loads(body);incoming=json.loads((tmp_path/'wire'/f'{index:05d}.incoming.json').read_text())
        assert value['chat_template_kwargs']=={'enable_thinking':True,'reasoning_effort':'low'}
        assert 'reasoning_effort' not in value and (value['seed'],value['temperature'],value['max_tokens'])==(17,.2,8192)
        assert incoming['chat_template_kwargs']['enable_thinking'] is False and incoming['seed'] in (123,456)
        assert body==(tmp_path/'wire'/f'{index:05d}.request.json').read_bytes()
    events=[json.loads(line) for line in (tmp_path/'forward_ledger.jsonl').read_text().splitlines()]
    assert len([e for e in events if e['event']=='request_policy_prepared'])==2
    assert relay.accounting()['actual_forwarded_body_bytes']==sum(map(len,bodies))
    relay.close()


@pytest.mark.parametrize('policy',[{},dict(m.THINKING_LOW_POLICY,version='wrong'),
    dict(m.THINKING_LOW_POLICY,chat_template_kwargs={'enable_thinking':1,'reasoning_effort':'low'})])
def test_unknown_request_policy_never_opens_wire_directory(tmp_path,policy):
    with pytest.raises(ValueError):m.Relay(tmp_path,relay_at_profile(),SimpleNamespace(),deadline=time.monotonic()+10,request_policy=policy)
    assert not (tmp_path/'wire').exists()


def test_policy_sampling_fault_rejected_before_reservation_or_connect(tmp_path,monkeypatch):
    def wrong(*args):return dict(actor.model_payload(*args),seed=18)
    h=SimpleNamespace(actor=SimpleNamespace(receive_http=actor.receive_http,model_payload=wrong),agg=agg)
    relay=m.Relay(tmp_path,relay_at_profile(),h,deadline=time.monotonic()+10,request_policy=m.THINKING_LOW_POLICY)
    connected=[];monkeypatch.setattr(socket,'create_connection',lambda *a,**k:connected.append(True))
    assert exchange(relay).startswith(b'HTTP/1.1 502')
    assert not connected and relay.posts==relay.inflight==relay.used==0
    relay.close()


def capture_relay(tmp_path):
    for name in ('baseline','work'):
        for path in ('lib/matplotlib/cbook.py','lib/mpl_toolkits/axes_grid1/tool.py','lib/matplotlib/tests/test_cpu.py'):
            p=tmp_path/name/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_text('CPU_PUBLIC_INITIAL = True\n')
    write_json(tmp_path/'manifest.json',{'CPU_ENGINEERING_ONLY':True})
    return m.Relay(tmp_path,relay_at_profile(),SimpleNamespace(actor=actor,agg=agg),deadline=time.monotonic()+30,
        capture_production_prefix=copy.deepcopy(m.PREFIX_CAPTURE))


@pytest.mark.parametrize('production',['lib/matplotlib/cbook.py','lib/mpl_toolkits/axes_grid1/tool.py'])
def test_first_production_prefix_has_actual_body_and_exact_public_snapshot_once(tmp_path,monkeypatch,production):
    bodies,workers=fake_upstream(monkeypatch);relay=capture_relay(tmp_path);folder=tmp_path/'production_prefix_checkpoint'
    exchange(relay);assert not folder.exists()
    (tmp_path/'work/lib/matplotlib/tests/test_cpu.py').write_text('ONLY_TEST_EDIT = True\n')
    exchange(relay);assert not folder.exists()
    (tmp_path/'work'/production).write_text('ACTUAL_PRODUCTION_EDIT = True\n')
    assert exchange(relay).startswith(b'HTTP/1.1 200')
    record=json.loads((folder/'receipt.json').read_text());frozen=(folder/'receipt.json').read_bytes()
    assert record['status']=='READY' and record['request']==3 and record['changed_production_files']==[production]
    assert (folder/'request.body').read_bytes()==bodies[2]
    assert record['body_sha256']==hashlib.sha256(bodies[2]).hexdigest()
    assert record['manifest_sha256']==m.sha(tmp_path/'manifest.json')
    assert record['incoming_request_sha256']==m.sha(tmp_path/'wire/00003.incoming.json')
    files=json.loads((folder/'files_sha256.json').read_text())
    assert files['before']==files['after']==files['copied']==m.tree(folder/'work')
    assert record['elapsed_seconds']>=0 and record['cpu_seconds']>=0
    (tmp_path/'work'/production).write_text('LATER_EDIT = True\n');exchange(relay)
    assert (folder/'receipt.json').read_bytes()==frozen
    for worker in workers:worker.join(5);assert not worker.is_alive()
    assert relay.accounting()['actual_forwarded_posts']==4
    relay.close()


def test_unstable_prefix_is_unknown_preserves_copy_and_never_retries(tmp_path,monkeypatch):
    bodies,workers=fake_upstream(monkeypatch);relay=capture_relay(tmp_path)
    source=tmp_path/'work/lib/matplotlib/cbook.py';source.write_text('FIRST_EDIT = True\n')
    real_copy=m.shutil.copytree
    def changing(*args,**kwargs):
        result=real_copy(*args,**kwargs)
        if Path(args[0])==tmp_path/'work':source.write_text('CONCURRENT_EDIT = True\n')
        return result
    monkeypatch.setattr(m.shutil,'copytree',changing)
    exchange(relay);folder=tmp_path/'production_prefix_checkpoint'
    record=json.loads((folder/'receipt.json').read_text())
    assert record['status']=='UNKNOWN' and record['error']=='work changed during snapshot'
    frozen=(folder/'receipt.json').read_bytes();exchange(relay);assert (folder/'receipt.json').read_bytes()==frozen
    assert (folder/'work/lib/matplotlib/cbook.py').read_text()=='FIRST_EDIT = True\n'
    for worker in workers:worker.join(5);assert not worker.is_alive()
    relay.close()


def test_capture_close_during_copy_does_not_block_send_close_lock(tmp_path,monkeypatch):
    relay=capture_relay(tmp_path);(tmp_path/'work/lib/matplotlib/cbook.py').write_text('EDIT = True\n')
    entered,release=threading.Event(),threading.Event();real_copy=m.shutil.copytree
    def paused(*args,**kwargs):
        if Path(args[0])==tmp_path/'work':entered.set();assert release.wait(3)
        return real_copy(*args,**kwargs)
    monkeypatch.setattr(m.shutil,'copytree',paused)
    connected=[];monkeypatch.setattr(socket,'create_connection',lambda *a,**k:connected.append(True))
    worker=threading.Thread(target=lambda:exchange(relay));worker.start();assert entered.wait(3)
    closed=threading.Event();closer=threading.Thread(target=lambda:(relay.close(),closed.set()));closer.start()
    try:assert closed.wait(1)
    finally:release.set();worker.join(5);closer.join(5)
    assert not worker.is_alive() and not closer.is_alive() and not connected
    record=json.loads((tmp_path/'production_prefix_checkpoint/receipt.json').read_text())
    assert record['status']=='UNKNOWN' and record['error']=='relay closed during snapshot'


def test_linked_capture_is_unknown_without_copying_external_bytes(tmp_path,monkeypatch):
    relay=capture_relay(tmp_path);secret=tmp_path/'OUTSIDE';secret.write_text('NEVER_COPY_THIS')
    link=tmp_path/'work/lib/matplotlib/linked.py'
    try:os.link(secret,link)
    except OSError:pytest.skip('hardlinks unavailable')
    new_payload=synthetic_payload();write_json(tmp_path/'wire/00001.incoming.json',new_payload)
    relay.capture_prefix(1,json.dumps(new_payload).encode())
    folder=tmp_path/'production_prefix_checkpoint';record=json.loads((folder/'receipt.json').read_text())
    assert record['status']=='UNKNOWN' and record['error']['type']=='ValueError'
    assert not (folder/'work').exists()
    relay.close()


def test_capture_byte_cap_preflight_precedes_hashing_and_copy(tmp_path,monkeypatch):
    relay=capture_relay(tmp_path)
    large=tmp_path/'work/lib/matplotlib/oversized.py'
    with large.open('wb') as out:out.truncate(256*1024**2+1)  # Real sparse file/stat, no large allocation.
    actual_sha=m.sha;actual_open=Path.open;copied=[]
    def checked_open(path,*args,**kwargs):
        assert not Path(path).is_relative_to(tmp_path/'work'), 'capacity must precede work reads'
        assert not Path(path).is_relative_to(tmp_path/'baseline'), 'capacity must precede baseline reads'
        return actual_open(path,*args,**kwargs)
    def checked_sha(path):
        assert not Path(path).is_relative_to(tmp_path/'work'), 'oversized work must not be hashed'
        assert not Path(path).is_relative_to(tmp_path/'baseline'), 'capacity must precede all tree hashing'
        return actual_sha(path)
    monkeypatch.setattr(m,'sha',checked_sha)
    monkeypatch.setattr(Path,'open',checked_open)
    monkeypatch.setattr(m.shutil,'copytree',lambda *a,**k:copied.append(a))
    relay.capture_prefix(1,b'CPU_ONLY_REQUEST')
    folder=tmp_path/'production_prefix_checkpoint';record=json.loads((folder/'receipt.json').read_text())
    assert record['status']=='UNKNOWN' and record['error']['type']=='ValueError'
    assert 'capture capacity' in record['error']['message'] and record['policy']['max_bytes']==256*1024**2
    assert record['policy']['max_files']==30000 and record['policy']['max_seconds']==30
    assert not copied and not (folder/'work').exists() and record['copied_bytes']==0 and record['copy_complete'] is False
    assert record['elapsed_seconds']>=0 and record['cpu_seconds']>=0
    frozen=(folder/'receipt.json').read_bytes();relay.capture_prefix(2,b'NO_RETRY');assert (folder/'receipt.json').read_bytes()==frozen
    relay.close()


def test_fake_wire_exact_payload_and_concurrent_actual_post_cap(tmp_path, monkeypatch):
    bodies, upstreams = fake_upstream(monkeypatch); relay = relay_at(tmp_path, dict(posts=2, seconds=10, combined_wire_bytes=100000))
    responses = []; workers = [threading.Thread(target=lambda: responses.append(exchange(relay))) for _ in range(5)]
    for w in workers: w.start()
    for w in workers: w.join(5); assert not w.is_alive()
    for w in upstreams: w.join(5)
    bill = relay.accounting(); assert len(bodies) == bill['actual_forwarded_posts'] == 2
    assert sum(r.startswith(b'HTTP/1.1 403') for r in responses) == 3
    events = [json.loads(l) for l in (tmp_path / 'forward_ledger.jsonl').read_text().splitlines()]
    stored = [(tmp_path / 'wire' / f'{e["request"]:05d}.request.json').read_bytes() for e in events if e['event'] == 'forwarded']
    assert sorted(stored) == sorted(bodies)
    assert bill['actual_forwarded_body_bytes'] == sum(map(len, bodies)) and bill['provider_total_tokens_known'] == 14
    value = json.loads(bodies[0]); assert (value['seed'], value['temperature'], value['max_tokens'], value['chat_template_kwargs']) == (17, .2, 8192, {'enable_thinking': False})


def test_connection_failure_is_not_forwarded_or_billed_then_retry_can_send(tmp_path, monkeypatch):
    relay = relay_at(tmp_path, dict(posts=1, seconds=10, combined_wire_bytes=100000))
    def refused(*_, **__): raise ConnectionRefusedError('fake endpoint')
    monkeypatch.setattr(socket, 'create_connection', refused); assert exchange(relay).startswith(b'HTTP/1.1 502')
    bill = relay.accounting(); assert bill['actual_forwarded_posts'] == bill['actual_forwarded_body_bytes'] == bill['budget_reserved_combined_wire_bytes'] == 0
    bodies, workers = fake_upstream(monkeypatch); assert exchange(relay).startswith(b'HTTP/1.1 200')
    for w in workers: w.join(5)
    assert len(bodies) == relay.accounting()['actual_forwarded_posts'] == 1
    assert relay.accounting()['integrity_passed'] is False


@pytest.mark.parametrize('payload', [[], {'temperature': float('nan')}])
def test_malformed_projection_payload_fails_before_send(tmp_path, monkeypatch, payload):
    def forbidden(*_, **__): raise AssertionError('must fail before send')
    monkeypatch.setattr(socket, 'create_connection', forbidden)
    # model_payload overwrites temperature; put NaN in an untouched field.
    if isinstance(payload, dict): payload = {'messages': [float('nan')]}
    relay = relay_at(tmp_path); assert exchange(relay, payload).startswith(b'HTTP/1.1 502')
    assert relay.accounting()['actual_forwarded_posts'] == 0


def test_uncertain_partial_send_is_preserved_and_consumes_cap(tmp_path, monkeypatch):
    class Broken:
        def settimeout(self, _): pass
        def sendall(self, _): raise OSError('fake partial send; extent unknown')
        def close(self): pass
    monkeypatch.setattr(socket, 'create_connection', lambda *_, **__: Broken())
    relay = relay_at(tmp_path, dict(posts=1, seconds=10, combined_wire_bytes=100000))
    assert exchange(relay).startswith(b'HTTP/1.1 502')
    assert exchange(relay).startswith(b'HTTP/1.1 403')
    bill = relay.accounting(); assert bill['uncertain_partial_sends'] == 1 and bill['actual_forwarded_posts'] == 0
    assert bill['budget_reserved_combined_wire_bytes'] > 0 and bill['actual_forwarded_body_bytes'] == 0


def test_stop_owned_rejects_unknown_identity_without_rm(tmp_path, monkeypatch):
    cid = tmp_path / 'cid'; cid.write_text('a'*64); calls = []
    def run(cmd, **_): calls.append(cmd); return SimpleNamespace(returncode=0, stdout=b'"/someone-else"', stderr=b'')
    monkeypatch.setattr(subprocess, 'run', run)
    with pytest.raises(ValueError, match='ownership'): m.stop_owned(cid, 'ours')
    assert len(calls) == 1 and calls[0][:2] == ['docker', 'inspect']


@pytest.mark.parametrize('fault', [None, subprocess.TimeoutExpired('fake-owned-docker', 1), KeyboardInterrupt(), InterruptedError('fake SIGTERM')])
def test_owned_run_preserves_raw_and_cleans_exact_cid_on_all_exits(tmp_path, monkeypatch, fault):
    calls = []; cid = tmp_path / 'cid'; cid.write_text('a'*64)
    class Process:
        returncode = 0
        def __init__(self, cmd, **kwargs): kwargs['stdout'].write(b'{"type":"text"}\n'); self.waits = 0
        def wait(self, **_):
            self.waits += 1
            if fault is not None and self.waits == 1: self.returncode = None; raise fault
            self.returncode = 0; return 0
        def poll(self): return self.returncode
        def kill(self): raise AssertionError('fake process already collected')
    def cleanup(path, name): calls.append((path, name)); return {'cid': 'a'*64, 'name': name}
    monkeypatch.setattr(subprocess, 'Popen', Process); monkeypatch.setattr(m, 'stop_owned', cleanup)
    stdout, stderr = tmp_path / 'raw', tmp_path / 'stderr'
    record = m.run_owned(['fake-owned-docker'], 'ours', cid, stdout, stderr, 1)
    assert calls == [(cid, 'ours')] and stdout.read_bytes() == b'{"type":"text"}\n'
    assert bool(record.get('error')) == (fault is not None)
    assert record['stdout_sha256'] == m.sha(stdout)


def test_existing_lock_is_nonblocking_and_missing_lock_not_created(tmp_path, monkeypatch):
    lock = tmp_path / 'model_resource.lock'; monkeypatch.setattr(m, 'LOCK', lock)
    with pytest.raises(FileNotFoundError):
        with m.resource_lock(): pass
    assert not lock.exists(); lock.write_text('existing owner record')
    with m.resource_lock():
        with pytest.raises(BlockingIOError):
            with m.resource_lock(): pass
    assert lock.read_text() == 'existing owner record'


@pytest.mark.parametrize('state', ['passed', 'failed', 'xfailed', 'xpassed', 'skipped', 'missing'])
def test_candidate_scoring_never_accepts_nonpass_or_missing(tmp_path, monkeypatch, state):
    (tmp_path / 'baseline/tests').mkdir(parents=True); (tmp_path / 'baseline/tests/test_a.py').write_text('public tests')
    (tmp_path / 'work/tests').mkdir(parents=True); (tmp_path / 'work/tests/test_a.py').write_text('actor modified tests')
    (tmp_path / 'scoring').mkdir(); (tmp_path / 'scoring/test.patch').write_text('frozen source test patch')
    def tests(candidate, repo, labels, runner, output, suite, h):
        assert (candidate / 'tests/test_a.py').read_text() == 'public tests'
        record = dict(exit=0 if state=='passed' else 1, result=dict(tests={} if state=='missing' else {n: state for n in labels}, fatal=[]))
        record['coverage'] = pool.classify(labels, record); return record
    monkeypatch.setattr(m, 'scored_test', tests)
    h = SimpleNamespace(pool=SimpleNamespace(helpers=lambda: (SimpleNamespace(apply_patch=lambda *_: dict(check_exit=0, apply_exit=0)), None), RUNNER='synthetic test runner'))
    result = m.score(tmp_path, dict(repo='django/django', labels=dict(f2p=['a'], ptp=['b'])), h)
    assert result['passed'] is (state == 'passed')


@pytest.mark.parametrize('fault',[None,'skip_passed','extra_skip','f2p_skip','regression','skip_error','missing','extra_node'])
def test_development_scoring_keeps_all_91_ptp_and_only_declared_skip(tmp_path,monkeypatch,fault):
    for name in ('baseline','work'):
        (tmp_path/name/'tests').mkdir(parents=True);(tmp_path/name/'tests/test_public.py').write_text('PUBLIC_REPOSITORY_TESTS')
    (tmp_path/'scoring').mkdir();(tmp_path/'scoring/test.patch').write_text('SCORER_ONLY')
    labels=dict(f2p=['test_f2p1','test_f2p2'],ptp=['test_ptp'+str(i) for i in range(91)])
    declared=dict(nodes=[labels['ptp'][0]],origin_receipt=dict(path=str(tmp_path/'origin.json'),sha256='a'*64),reason='CPU observed PDF skip')
    contract=tmp_path/'contract.json';contract_sha=write_json(contract,dict(expected_skips=declared))
    registry=tmp_path/'registry.json';registry_sha=write_json(registry,dict(schema=m.DEVELOPMENT_REGISTRY,qualification_contract=dict(path=str(contract),sha256=contract_sha)))
    manifest=dict(repo='matplotlib/matplotlib',source='matplotlib__matplotlib-22711',source_role='DEVELOPMENT_SOURCE',
        labels=labels,expected_skips=declared,qualification_scope='LIMITED_RUNTIME_SCOPE',
        registry=dict(path=str(registry),sha256=registry_sha),scorer_dependencies=dict(matplotlib_runtime={}))
    calls=[]
    def tests(candidate,repo,nodes,runner,output,suite,h,**kwargs):
        calls.append((suite,list(nodes)));states={n:'passed' for n in nodes}
        if suite=='ptp':
            states[declared['nodes'][0]]='skipped'
            if fault=='skip_passed':states[declared['nodes'][0]]='passed'
            elif fault=='extra_skip':states[nodes[1]]='skipped'
            elif fault=='regression':states[nodes[1]]='failed'
            elif fault=='skip_error':states[nodes[0]]='error'
            elif fault=='missing':states.pop(nodes[-1])
            elif fault=='extra_node':states['UNDECLARED']='passed'
        elif fault=='f2p_skip':states[nodes[0]]='skipped'
        record=dict(exit=0,result=dict(tests=states,fatal=[]));record['coverage']=pool.classify(nodes,record)
        return record
    monkeypatch.setattr(m,'scored_test',tests)
    def expected(contract,given,bindings):
        assert contract['expected_skips']==declared and given==labels
        return list(declared['nodes'])  # Qualification helper itself is tested in qualifier suite.
    h=SimpleNamespace(pool=SimpleNamespace(helpers=lambda:(SimpleNamespace(apply_patch=lambda *_:dict(check_exit=0,apply_exit=0)),None),
        RUNNER='CPU_RUNNER',matplotlib_assets=lambda *_:{},exact_coverage=pool.exact_coverage,matplotlib_source_expected_skips=expected))
    result=m.score(tmp_path,manifest,h)
    assert calls==[('f2p',labels['f2p']),('ptp',labels['ptp'])]
    assert result['passed'] is (fault is None)
    assert result['qualification_scope']=='LIMITED_RUNTIME_SCOPE'
    if fault is None:
        assert result['ptp_counts']==dict(total=91,passed=90,skipped=1,other=0)
        assert result['suites']['ptp']['coverage']['complete'] is False
        assert result['suites']['ptp']['limited_scope_coverage']['labels'][declared['nodes'][0]]=='skipped'


@pytest.mark.parametrize('error', [None, {'name':'UnknownError'}, {'name':'APIError', 'data':{'statusCode':409}}])
def test_zero_exit_stop_or_opaque_error_never_becomes_success(tmp_path, error):
    raw = tmp_path / 'raw'
    raw.write_text(json.dumps({'type':'tool_use','part':{'state':{'error':'ordinary tool feedback'}}})+'\n'+
        (json.dumps({'type':'error','error':error})+'\n' if error else ''))
    result = dict(status='ACTOR_RETURNED', actor_exit=0, raw_errors=m.raw_errors(raw), actor={},
        accounting=dict(integrity_passed=True, actual_forwarded_posts=1), scoring=dict(passed=True))
    assert m.successful(result) is (error is None)
    result['actor_exit'] = 137; assert m.successful(result) is False

def test_deadline_rechecked_after_connect_before_any_wire_post(tmp_path, monkeypatch):
    relay = relay_at(tmp_path); sent = []
    class Delayed:
        def sendall(self, data): sent.append(data)
        def settimeout(self, _): pass
        def makefile(self, *_): raise OSError('must never reach response parsing')
        def close(self): pass
    def connect(*_, **__): relay.deadline = time.monotonic() - 1; return Delayed()
    monkeypatch.setattr(socket, 'create_connection', connect)
    exchange(relay)
    assert sent == [] and relay.accounting()['actual_forwarded_posts'] == 0


def test_response_wire_cap_keeps_known_request_and_unknown_response_usage(tmp_path, monkeypatch):
    bodies, workers = fake_upstream(monkeypatch)
    # Request fits, but the received response cannot be forwarded within the ceiling.
    value, _ = m.prepare_tool_contract(synthetic_payload())
    value = actor.model_payload(value, 'teacher27b', relay_at_profile(), 17)
    size = len(json.dumps(value, ensure_ascii=False, separators=(',', ':')).encode())
    relay = relay_at(tmp_path, dict(posts=1, seconds=10, combined_wire_bytes=size+1))
    exchange(relay)
    for w in workers: w.join(5)
    bill = relay.accounting()
    assert bill['actual_forwarded_posts'] == 1 and bill['actual_forwarded_body_bytes'] == len(bodies[0])
    assert bill['unknown_usage_requests'] == [1] and bill['provider_total_tokens_known'] == 0
    assert bill['budget_reserved_combined_wire_bytes'] <= size+1 and bill['integrity_passed'] is False


def test_changed_component_binding_fails_verification(prepared_inputs):
    f = prepared_inputs; prepare(f); path = f.root / 'manifest.json'; manifest = json.loads(path.read_text())
    manifest['components'][str(Path(m.__file__).resolve())] = '0' * 64
    digest = write_json(path, manifest)
    with pytest.raises(ValueError, match='source/tool'): m.verify(f.root, digest)

@pytest.mark.parametrize('fault_type', ['KeyboardInterrupt', 'InterruptedError', 'TimeoutExpired'])
def test_execute_fault_closes_without_starting_new_scorer(prepared_inputs, monkeypatch, fault_type):
    """Engineering lifecycle simulation; no server, Docker, backend or source outcome."""
    from contextlib import contextmanager
    f = prepared_inputs; digest = prepare(f)['manifest_sha256']; order = []
    @contextmanager
    def locked(): order.append('lock'); yield
    monkeypatch.setattr(m, 'resource_lock', locked)
    def validate(*_, **kwargs):
        assert order == ['lock'] and kwargs == {'full': True}; order.append('weights')
    f.h.teacher.validate_vllm_model_profile = validate
    f.h.teacher.verify_vllm_backend = lambda _: dict(fake_engineering_backend=True)
    class FakeServer:
        def __init__(self, path, handler): Path(path).write_text('fake owned socket artifact')
        def serve_forever(self): pass
        def server_close(self): pass
        def shutdown(self): pass
    monkeypatch.setattr(m.socketserver, 'ThreadingUnixStreamServer', FakeServer)
    def collected(cmd, name, cid, stdout, stderr, timeout):
        stdout.write_text('{"type":"text"}\n'); stderr.write_text('')
        return dict(exit=None, error=dict(type=fault_type, message='fake engineering interruption'), cleanup=dict(fake=True))
    monkeypatch.setattr(m, 'run_owned', collected)
    def no_scoring(*_): raise AssertionError('a stopped actor must not launch a scorer')
    monkeypatch.setattr(m, 'score', no_scoring)
    result = m.execute(f.root, digest, f.registry, f.registry_sha, f.source)
    assert result['status'] == ('RUNTIME_ERROR' if fault_type == 'TimeoutExpired' else 'INTERRUPTED')
    assert result['source_success'] is False and 'scoring' not in result
    assert 'finalization_error' not in result and (f.root / 'receipt.json').is_file()
    assert result['accounting']['actual_forwarded_posts'] == 0


def test_busy_resource_refuses_before_reservation_or_live_validation(prepared_inputs, monkeypatch):
    from contextlib import contextmanager
    f = prepared_inputs; digest = prepare(f)['manifest_sha256']
    @contextmanager
    def busy(): raise BlockingIOError('synthetic existing model owner'); yield
    monkeypatch.setattr(m, 'resource_lock', busy)
    with pytest.raises(BlockingIOError): m.execute(f.root, digest, f.registry, f.registry_sha, f.source)
    assert not (f.root / 'reservation.json').exists() and not (f.root / 'receipt.json').exists()


def test_close_rejects_connection_that_returns_after_shutdown(tmp_path, monkeypatch):
    """Fake delayed connect: close must prohibit its later first POST."""
    relay = relay_at(tmp_path); connecting = threading.Event(); release = threading.Event(); frames = []
    class LateSocket:
        closed = False
        def settimeout(self, _): pass
        def sendall(self, data): frames.append(data); raise OSError('fake attempted send after close')
        def shutdown(self, _): self.closed = True
        def close(self): self.closed = True
    upstream = LateSocket()
    def connect(*_, **__):
        connecting.set(); assert release.wait(3); return upstream
    monkeypatch.setattr(socket, 'create_connection', connect)
    client, receiver = socket.socketpair(); worker = threading.Thread(target=relay.handle, args=(receiver,))
    worker.start(); wire_payload(client, synthetic_payload())
    try:
        assert connecting.wait(3); relay.close(); release.set(); worker.join(3)
        assert not worker.is_alive() and upstream.closed and frames == []
        bill = relay.accounting()
        assert bill['actual_forwarded_posts'] == bill['uncertain_partial_sends'] == bill['budget_reserved_combined_wire_bytes'] == 0
        assert bill['integrity_passed'] is False
    finally: release.set(); client.close(); worker.join(3)


def test_close_cannot_cross_check_and_actual_send_boundary(tmp_path, monkeypatch):
    """Fake attribute gate pauses between guard evaluation and calling sendall."""
    relay = relay_at(tmp_path); ready = threading.Event(); decision = threading.Event(); close_done = threading.Event()
    frame_after_close = []; probe = []
    class GatedSocket:
        closed = False
        def settimeout(self, _): pass
        @property
        def sendall(self):
            ready.set(); assert decision.wait(3); return self.write_fragment
        def write_fragment(self, packet):
            frame_after_close.append(self.closed)
            raise OSError('fake partial send; bill extent remains unknown')
        def shutdown(self, _): self.closed = True
        def close(self): self.closed = True
    upstream = GatedSocket(); monkeypatch.setattr(socket, 'create_connection', lambda *_, **__: upstream)
    def closer():
        assert ready.wait(3)
        acquired = relay.lock.acquire(blocking=False); probe.append(acquired)
        if acquired:
            try: relay.close()
            finally: relay.lock.release()
            decision.set()
        else:
            decision.set(); relay.close()
        close_done.set()
    close_worker = threading.Thread(target=closer); close_worker.start()
    client, receiver = socket.socketpair(); worker = threading.Thread(target=relay.handle, args=(receiver,))
    worker.start(); wire_payload(client, synthetic_payload())
    try:
        worker.join(3); close_worker.join(3)
        assert not worker.is_alive() and not close_worker.is_alive() and close_done.is_set()
        assert frame_after_close == [False] and probe == [False]
        bill = relay.accounting()
        assert bill['actual_forwarded_posts'] == 0 and bill['uncertain_partial_sends'] == 1
        assert bill['budget_reserved_combined_wire_bytes'] > 0 and bill['integrity_passed'] is False
    finally: decision.set(); client.close(); worker.join(3); close_worker.join(3)


def test_close_is_bounded_when_locked_fake_send_honors_timeout(tmp_path, monkeypatch):
    """Engineering timing control: scale the production bound down, not the episode."""
    monkeypatch.setattr(m, 'SEND_TIMEOUT', 0.05, raising=False)
    relay = relay_at(tmp_path); sending = threading.Event(); release = threading.Event(); configured = []
    class BlockingSocket:
        timeout = None
        def settimeout(self, seconds): self.timeout = seconds; configured.append(seconds)
        def sendall(self, packet):
            sending.set(); release.wait(self.timeout)
            raise socket.timeout('fake partial write reached its configured timeout')
        def shutdown(self, _): pass
        def close(self): pass
    monkeypatch.setattr(socket, 'create_connection', lambda *_, **__: BlockingSocket())
    client, receiver = socket.socketpair(); worker = threading.Thread(target=relay.handle, args=(receiver,))
    worker.start(); wire_payload(client, synthetic_payload())
    closer = threading.Thread(target=relay.close)
    try:
        assert sending.wait(3); closer.start(); closer.join(1)
        assert not closer.is_alive(), 'close waited for the episode timeout instead of the short send bound'
        worker.join(1); assert not worker.is_alive()
        assert 0 < configured[0] <= .05
        bill = relay.accounting()
        assert bill['actual_forwarded_posts'] == 0 and bill['uncertain_partial_sends'] == 1
        assert bill['actual_forwarded_body_bytes'] == 0 and bill['budget_reserved_combined_wire_bytes'] > 0
        assert bill['integrity_passed'] is False
    finally:
        release.set(); client.close(); worker.join(3)
        if closer.ident is not None: closer.join(3)


def test_successful_fake_send_restores_response_deadline_timeout(tmp_path, monkeypatch):
    assert m.SEND_TIMEOUT == 5.0
    bodies, workers = fake_upstream(monkeypatch); connect = socket.create_connection; trace = []
    class SocketView:
        def __init__(self, sock): self.sock = sock; self.timeout = None
        def settimeout(self, seconds): self.timeout = seconds; trace.append(('timeout', seconds)); self.sock.settimeout(seconds)
        def sendall(self, packet): trace.append(('send', self.timeout)); self.sock.sendall(packet)
        def makefile(self, *args, **kwargs): return self.sock.makefile(*args, **kwargs)
        def shutdown(self, how): return self.sock.shutdown(how)
        def close(self): self.sock.close()
    monkeypatch.setattr(socket, 'create_connection', lambda *a, **kw: SocketView(connect(*a, **kw)))
    relay = relay_at(tmp_path); assert exchange(relay).startswith(b'HTTP/1.1 200')
    for worker in workers: worker.join(3)
    assert trace[0] == ('timeout', 5.0) and trace[1] == ('send', 5.0)
    assert trace[-1][0] == 'timeout' and 5.0 < trace[-1][1] <= 10
    bill = relay.accounting()
    assert bill['actual_forwarded_posts'] == 1 and bill['provider_total_tokens_known'] == 7 and bill['integrity_passed'] is True


@pytest.mark.parametrize('stderr,missing', [
    (b'error: no such object: ', True),
    (b'Error response from daemon: No such container: ', True),
    (b'permission denied while trying to connect to the Docker daemon socket: ', False),
    (b'Cannot connect to the Docker daemon at unix:///var/run/docker.sock: ', False),
])
def test_missing_cid_case_normalization_does_not_accept_operational_errors(tmp_path, monkeypatch, stderr, missing):
    cid = tmp_path / 'cid'; cid.write_text('a' * 64); calls = []
    def inspect(cmd, **_):
        calls.append(cmd)
        return SimpleNamespace(returncode=1, stdout=b'', stderr=stderr + b'a' * 64 + b'\n')
    monkeypatch.setattr(subprocess, 'run', inspect)
    if missing:
        result = m.stop_owned(cid, 'ours')
        assert result == dict(cid='a' * 64, name='ours', status='ALREADY_REMOVED')
    else:
        with pytest.raises(ValueError, match='ownership not proven'): m.stop_owned(cid, 'ours')
    assert len(calls) == 1 and calls[0] == ['docker', 'inspect', '--format', '{{json .Name}}', 'a' * 64]
