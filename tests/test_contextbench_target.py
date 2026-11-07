"""CPU engineering controls with synthetic assets, not target model results."""
import copy
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
    (src/'reference.patch').write_text(patch)
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
    mounts=[v for v in cmd if 'type=bind' in v]
    assert any('/deps/target' in v and 'dst=/deps,readonly' in v for v in mounts)
    assert not any(str(f.receipt.parent) in v or '/deps/source' in v or 'scoring' in v or 'evidence' in v for v in mounts)
    assert '--network' in cmd and cmd[cmd.index('--network')+1]=='none'


def test_rebinding_manifest_hash_does_not_allow_prompt_or_cap_rewrite(target_inputs):
    f=target_inputs;out=prepare(f);path=f.root/'manifest.json';m=json.loads(path.read_text())
    (f.root/'inputs/task.txt').write_text('tampered target instructions')
    m['inputs']=s.tree(f.root/'inputs');m['wrapped_prompt_sha256']=s.sha(f.root/'inputs/task.txt')
    with pytest.raises(ValueError,match='input differs'):t.verify(f.root,write_json(path,m))


def test_existing_root_and_linked_work_refused(target_inputs):
    f=target_inputs;out=prepare(f)
    with pytest.raises(ValueError,match='fresh'):prepare(f)
    dest=f.root/'work/link';dest.symlink_to(f.private)
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
    monkeypatch.setattr(s.socketserver,'ThreadingUnixStreamServer',Server)
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
