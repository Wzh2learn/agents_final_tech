"""Synthetic CPU controls only: fake legacy admission/world/model sockets, no research results."""
import copy
from contextlib import contextmanager
import hashlib
import importlib.util
import io
import json
from pathlib import Path
from types import SimpleNamespace
from unittest import mock
import pytest
from test_alfworld_context_study import r

PATH=Path(__file__).resolve().parents[1]/'research/agent_frontier_portfolio_20261029/alfworld_native_actor.py'
spec=importlib.util.spec_from_file_location('cpu_native_actor',PATH)
a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
core=r.recovery().actor()
PROFILE=dict(model_id='CPU_TEACHER',host='CPU_NO_ENDPOINT',port=1,context=32768,output=8192)


def ref(path,value=None):
    if value is not None:
        path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value))
    return dict(path=str(path),sha256=hashlib.sha256(path.read_bytes()).hexdigest())


def state(count=39,commands=None,won=False):
    return dict(observation='CPU_PUBLIC_CURRENT',score=float(won),done=won,won=won,action_count=count,
                admissible_commands=commands or ['look','inventory'])


def sse(action='look',finish='tool_calls',usage=True,calls=None):
    delta=dict(role='assistant')
    if finish=='tool_calls':
        delta['tool_calls']=calls if calls is not None else [dict(index=0,id='call_CPU1',type='function',
            function=dict(name='environment_step',arguments=json.dumps(dict(action=action))))]
    else:delta['content']='CPU ordinary stop'
    items=[dict(choices=[dict(index=0,delta=delta,finish_reason=None)]),
           dict(choices=[dict(index=0,delta={},finish_reason=finish)])]
    if usage:items.append(dict(choices=[],usage=dict(prompt_tokens=5,completion_tokens=2,total_tokens=7)))
    return b''.join(b'data: '+json.dumps(x).encode()+b'\n\n' for x in items)+b'data: [DONE]\n\n'


class FakeSocket:
    def __init__(self,body=None,status=200,partial_send=False):
        body=sse() if body is None else body
        self.raw=b'HTTP/1.1 '+str(status).encode()+b' CPU\r\nContent-Type: text/event-stream\r\nContent-Length: '+str(len(body)).encode()+b'\r\n\r\n'+body
        self.closed=False;self.sent=[];self.timeouts=[];self.partial_send=partial_send
    def settimeout(self,value):self.timeouts.append(value)
    def sendall(self,value):
        self.sent.append(value)
        if self.partial_send:raise TimeoutError('CPU partial send')
    def makefile(self,*args,**kwargs):return io.BytesIO(self.raw)
    def close(self):self.closed=True


def qualify(payload):
    return dict(template_input_tokens=10,reserved_output_tokens=8192,context=32768,request_payload_sha256=a.sha(json.dumps(payload,separators=(',',':')).encode()))


def bundle():
    return dict(core=core,profile=PROFILE,qualify=qualify,prompt='CPU_PUBLIC_GOAL_AND_FULL_HISTORY')


@pytest.mark.parametrize('change',['illegal','multiple','wrong_name','extra_argument','nonstring','duplicate_argument','length','missing_done'])
def test_strict_reply_never_repairs_or_executes_bad_calls(change):
    calls=[dict(index=0,id='call1',type='function',function=dict(name='environment_step',arguments='{"action":"look"}'))]
    if change=='illegal':calls[0]['function']['arguments']='{"action":"go somewhere unknown"}'
    elif change=='multiple':calls.append(dict(index=1,id='call2',type='function',function=dict(name='environment_step',arguments='{"action":"inventory"}')))
    elif change=='wrong_name':calls[0]['function']['name']='bash'
    elif change=='extra_argument':calls[0]['function']['arguments']='{"action":"look","hidden":true}'
    elif change=='nonstring':calls[0]['function']['arguments']='{"action":7}'
    elif change=='duplicate_argument':calls[0]['function']['arguments']='{"action":"look","action":"inventory"}'
    body=sse(calls=calls,finish='length' if change=='length' else 'tool_calls')
    if change=='missing_done':body=body.replace(b'data: [DONE]\n\n',b'')
    with pytest.raises(ValueError):a.reply_from_sse(body,state())


def test_actual_fake_wire_body_hash_billing_and_raw_receipt(tmp_path):
    budget=core.Budget(max_posts=48,max_bytes=32000000,seconds=900);attempts=[];upstream=FakeSocket()
    messages=[dict(role='user',content='CPU_GOAL')];original=copy.deepcopy(messages)
    payload=a.payload_for(core,PROFILE,messages,state())
    with mock.patch.object(a.socket,'create_connection',return_value=upstream) as connect:
        body=a.exchange(core,tmp_path,payload,budget,qualify,('CPU_FAKE',1),attempts)
    packet=upstream.sent[0];actual=packet.split(b'\r\n\r\n',1)[1]
    assert actual==(tmp_path/'requests/00001.body').read_bytes()
    assert hashlib.sha256(actual).hexdigest()==attempts[0]['request_body_sha256']
    assert budget.request_bytes==len(actual) and budget.response_bytes==len(upstream.raw)
    assert (tmp_path/'responses/00001.http').read_bytes()==upstream.raw
    assert body==(tmp_path/'responses/00001.sse').read_bytes()==sse()
    assert attempts[0]['response_receipt']['usage']['total_tokens']==7 and upstream.closed
    assert json.loads(actual)['tools'][0]['function']['parameters']['properties']['action']['enum']==['look','inventory']
    assert json.loads(actual)['tool_choice']['function']['name']=='environment_step'
    assert json.loads(actual)['parallel_tool_calls'] is False and messages==original and connect.call_count==1


@pytest.mark.parametrize('failure',['connect','partial','HTTP400','unknown_usage'])
def test_failures_keep_reserved_attempts_raw_unknown_and_no_retry(tmp_path,failure):
    attempts=[];budget=core.Budget(max_posts=48,max_bytes=32000000,seconds=900)
    upstream=FakeSocket(body=b'{"error":"CPU unsupported named tool choice"}' if failure=='HTTP400' else sse(usage=failure!='unknown_usage'),status=400 if failure=='HTTP400' else 200,partial_send=failure=='partial')
    effect=OSError('CPU connect failure') if failure=='connect' else None
    with mock.patch.object(a.socket,'create_connection',return_value=upstream,side_effect=effect) as connect:
        if failure=='unknown_usage':
            a.exchange(core,tmp_path,a.payload_for(core,PROFILE,[],state()),budget,qualify,('CPU_FAKE',1),attempts)
        else:
            with pytest.raises((OSError,RuntimeError)):
                a.exchange(core,tmp_path,a.payload_for(core,PROFILE,[],state()),budget,qualify,('CPU_FAKE',1),attempts)
    bill=a.accounting(attempts,budget)
    assert bill['reserved_posts']==1 and bill['unknown_usage_attempts']==1
    assert bill['provider_usage']['total_tokens'] is None and not bill['integrity_passed']
    assert connect.call_count==1 and (tmp_path/'ledger/00001.json').exists()
    if failure=='partial':assert bill['actual_forwarded_posts'] is None and bill['possible_additional_forwarded_posts']==1
    if failure=='HTTP400':assert bill['known_forwarded_posts']==1 and (tmp_path/'responses/00001.sse').exists()


def test_post_and_body_caps_refuse_before_another_connect(tmp_path):
    attempts=[];budget=core.Budget(max_posts=1,max_bytes=32000000,seconds=900);upstream=FakeSocket();payload=a.payload_for(core,PROFILE,[],state())
    with mock.patch.object(a.socket,'create_connection',return_value=upstream) as connect:
        a.exchange(core,tmp_path,payload,budget,qualify,('CPU_FAKE',1),attempts)
        with pytest.raises(a.CapClosed):a.exchange(core,tmp_path,payload,budget,qualify,('CPU_FAKE',1),attempts)
        assert connect.call_count==1 and len(attempts)==2 and not attempts[1]['reserved']
    other=tmp_path/'byte_cap';budget=core.Budget(max_posts=48,max_bytes=1,seconds=900);attempts=[]
    with mock.patch.object(a.socket,'create_connection',side_effect=AssertionError('CPU no endpoint')):
        with pytest.raises(a.CapClosed):a.exchange(core,other,payload,budget,qualify,('CPU_FAKE',1),attempts)
    assert budget.posts==0 and not attempts[0]['reserved']


def test_terminal_never_posts_and_stop_gets_one_neutral_continue(tmp_path):
    budget=core.Budget(max_posts=48,max_bytes=32000000,seconds=900);attempts=[]
    with mock.patch.object(a.socket,'create_connection',side_effect=AssertionError('CPU no endpoint')):
        assert a.run_session(bundle(),tmp_path,budget,lambda:state(won=True),mock.Mock(),attempts)==('NATIVE_WON',0)
    sockets=[FakeSocket(sse(finish='stop')),FakeSocket(sse(finish='stop'))]
    with mock.patch.object(a.socket,'create_connection',side_effect=sockets):
        status,neutral=a.run_session(bundle(),tmp_path,budget,lambda:state(),mock.Mock(side_effect=AssertionError('no native step')),attempts)
    assert (status,neutral)==('MODEL_STOP_UNWON',1) and budget.posts==2
    second=json.loads((tmp_path/'requests/00002.body').read_bytes())
    assert second['messages'][-1]==dict(role='user',content=a.CONTINUE)


def test_native_history_and_current_enum_are_retained_and_won_stops(tmp_path):
    current=[state()];attempts=[];budget=core.Budget(max_posts=48,max_bytes=32000000,seconds=900)
    def step(action):
        current[0]=state(40,['inventory']) if action=='look' else state(41,['look'],True)
        return current[0]
    sockets=[FakeSocket(sse('look')),FakeSocket(sse('inventory'))]
    with mock.patch.object(a.socket,'create_connection',side_effect=sockets) as connect:
        result=a.run_session(bundle(),tmp_path,budget,lambda:current[0],step,attempts)
    assert result==('NATIVE_WON',0) and connect.call_count==2
    p=json.loads((tmp_path/'requests/00002.body').read_bytes())
    assert p['tools'][0]['function']['parameters']['properties']['action']['enum']==['inventory']
    assert [x['role'] for x in p['messages']]==['system','user','assistant','tool']
    assert json.loads(p['messages'][-1]['content'])['action_count']==40


@contextmanager
def admitted_fixture(tmp_path):
    st=tmp_path/'qualification/context_study_v1';prior=st/'cases/cpu/drop_full/teacher27b/attempt_v1';prior.mkdir(parents=True)
    output=st/'learning_comparison_v1/native_actor/attempt_v1'
    source=tmp_path/'repo/alfworld_context_study.py';source.parent.mkdir();source.write_text('CPU_VERIFIED_OLD_SOURCE')
    # Real layout: profile is a sibling of qualification, not a descendant of ST.
    profile_path=tmp_path/'django_aggregation_agent_20261106/profile.json';profile_ref=ref(profile_path,PROFILE)
    task='CPU_PUBLIC_GOAL\nCPU_FULL_ACCEPTED_HISTORY'+a.BASH_BLOCK+'Historical observations are cached, not fresh evidence.\n'
    (prior/'task.txt').write_text(task)
    m=dict(case_id='cpu',stage='drop_full',backend='teacher27b',experience_mode='none',experience_assignment={},model_seed=17,world_seed=17,
        profile_sha256=profile_ref['sha256'],runtime_controls=dict(native_terminal_stop=True,recent_tool_rounds=None),
        components={str(source):hashlib.sha256(source.read_bytes()).hexdigest()},game={},pool_binding=dict(sha256='CPU_POOL'),
        protocol_path='CPU_PRIOR_PROTOCOL',protocol_sha256='CPU_PRIOR_PROTOCOL_SHA')
    manifest=ref(prior/'manifest.json',m)
    forwarded=core.model_payload(dict(messages=[dict(role='system',content='CPU_OLD_OPENCODE_SYSTEM'),dict(role='user',content='"'+task.replace('"','\\"')+'"')],
        tools=[dict(type='function',function=dict(name='bash',parameters={}))]),'teacher27b',PROFILE,17)
    first=ref(prior/'requests/00001.json',dict(incoming=forwarded,forwarded=forwarded))
    body=prior/'requests/00001.body';body.write_bytes(json.dumps(forwarded,separators=(',',':')).encode())
    protocol=dict(schema='ALFWORLD_NATIVE_ACTOR_PROTOCOL_V1',prior=dict(root=str(prior),manifest_sha256=manifest['sha256'],study_source=ref(source)),
        prior_first_request=first,prior_first_request_body=ref(body),profile=profile_ref,output_root=str(output),caps=copy.deepcopy(a.CAPS),sampling=copy.deepcopy(a.SAMPLING))
    p=ref(st/'CPU_NATIVE_PROTOCOL.json',protocol);prefix=dict(steps=[{}]*39,visible_steps=[{}]*39,current=state())
    fake=SimpleNamespace(verify=mock.Mock(return_value=(m,{},PROFILE,prefix,qualify)),recovery=lambda:SimpleNamespace(actor=lambda:core))
    spec=SimpleNamespace(loader=SimpleNamespace(exec_module=lambda module:None))
    with mock.patch.object(a,'ST',st),mock.patch.object(a,'STUDY',source),mock.patch.object(a,'PROFILE',profile_ref),\
         mock.patch.object(a.importlib.util,'spec_from_file_location',return_value=spec),mock.patch.object(a.importlib.util,'module_from_spec',return_value=fake):
        yield SimpleNamespace(ref=p,protocol=protocol,prior=prior,output=output,source=source,study=fake,manifest=m)


def test_cpu_check_only_real_sibling_profile_layout_and_readonly_hashes(tmp_path,capsys):
    with admitted_fixture(tmp_path) as f:
        before={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in f.prior.rglob('*') if p.is_file()}
        with mock.patch.object(a,'execute',side_effect=AssertionError('CPU no execute')),mock.patch.object(a.socket,'create_connection',side_effect=AssertionError('CPU no endpoint')):
            assert a.main(['--protocol',f.ref['path'],'--protocol-sha',f.ref['sha256']])==0
        assert not f.output.exists() and 'CPU_INPUTS_BOUND_NO_EXECUTION' in capsys.readouterr().out
        assert before=={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in f.prior.rglob('*') if p.is_file()}
        Path(f.ref['path']).write_text('{}')
        with pytest.raises(ValueError):a.load_inputs(f.ref['path'],f.ref['sha256'])


def test_never_reuse_root_and_profile_exception_does_not_relax_private_inputs(tmp_path):
    with admitted_fixture(tmp_path) as f:
        f.output.mkdir(parents=True)
        with pytest.raises(FileExistsError):a.load_inputs(f.ref['path'],f.ref['sha256'])
        outside=tmp_path/'outside.json';outside.write_text('{}')
        with pytest.raises(ValueError):a.read_ref(ref(outside))


def test_prompt_changes_only_exact_dispatch_and_rejects_opaque_wrapper():
    task='PUBLIC_GOAL_AND_HISTORY'+a.BASH_BLOCK+'PUBLIC_CURRENT'
    payload=dict(messages=[dict(role='user',content=task)],tools=[dict(function=dict(name='bash'))])
    prompt,proof=a.prompt_from_request(task,payload)
    assert prompt.replace(a.NATIVE_BLOCK,a.BASH_BLOCK)==task and proof['interpretation'].startswith('Interface/controller')
    payload['messages'][0]['content']='OPAQUE_SUMMARY'
    with pytest.raises(ValueError):a.prompt_from_request(task,payload)


@pytest.mark.skipif(__import__('os').name!='posix',reason='POSIX flock engineering control')
def test_resource_lock_existing_same_inode_busy_and_unchanged(tmp_path):
    st=tmp_path/'CPU_ST';st.mkdir();path=st/'model_resource.lock';path.write_bytes(b'CPU_LOCK_BYTES')
    inode=path.stat().st_ino
    with mock.patch.object(a,'ST',st):
        with a.resource_lock():
            with pytest.raises(BlockingIOError):
                with a.resource_lock():pass
        with a.resource_lock():pass
    assert path.read_bytes()==b'CPU_LOCK_BYTES' and path.stat().st_ino==inode


def test_owned_world_and_lock_cleaned_on_replay_timeout_without_model(tmp_path):
    with admitted_fixture(tmp_path) as f:
        f.study.task_pool=lambda:SimpleNamespace(start_world=mock.Mock(return_value=((object(),tmp_path/'CPU_WORLD'),state(0),{})))
        f.study.protocol=lambda *args:dict(pool_path='CPU_POOL')
        f.study.public=lambda x:x
        f.study.replay_prefix=mock.Mock(side_effect=TimeoutError('CPU_NATIVE_REPLAY_TIMEOUT'))
        f.study.native_world_witness=mock.Mock(return_value=dict(state=state(),path='CPU_NATIVE_TRACE',sha256='CPU_NATIVE_HASH'))
        events=[]
        @contextmanager
        def lock():
            events.append('enter')
            try:yield
            finally:events.append('exit')
        with mock.patch.object(a,'resource_lock',lock),mock.patch.object(a,'check_release',return_value=dict(path='CPU_RELEASE',sha256='CPU_SHA')),\
             mock.patch.object(core,'stop_world') as stop,mock.patch.object(a.socket,'create_connection',side_effect=AssertionError('CPU no endpoint')):
            result=a.execute(f.ref['path'],f.ref['sha256'],'CPU_RELEASE','CPU_SHA')
        assert result['status']=='RUNTIME_FAULT' and result['task_won'] is False
        assert events==['enter','exit'] and stop.call_count==1 and result['accounting']['reserved_posts']==0
        assert any(x['type']=='TimeoutError' for x in result['errors'])
        assert (f.output/'receipt.json').exists() and (f.output/'manifest.json').exists()
        assert result['manifest_sha256']==hashlib.sha256((f.output/'manifest.json').read_bytes()).hexdigest()
        assert result['protocol']==f.ref and result['prior_manifest_sha256']==f.protocol['prior']['manifest_sha256']
        with pytest.raises(FileExistsError):a.load_inputs(f.ref['path'],f.ref['sha256'])


def test_execute_requires_release_before_any_new_world(tmp_path):
    with admitted_fixture(tmp_path) as f,mock.patch.object(a,'execute',side_effect=AssertionError('CPU no execute')):
        with pytest.raises(SystemExit):a.main(['--execute','--protocol',f.ref['path'],'--protocol-sha',f.ref['sha256']])
        assert not f.output.exists()


def test_poisoned_budget_is_fault_not_an_explained_cap(tmp_path):
    budget=core.Budget(max_posts=48,max_bytes=32000000,seconds=900);budget.poison();attempts=[]
    with mock.patch.object(a.socket,'create_connection',side_effect=AssertionError('CPU no endpoint')):
        with pytest.raises(RuntimeError,match='poisoned'):
            a.exchange(core,tmp_path,a.payload_for(core,PROFILE,[],state()),budget,qualify,('CPU_FAKE',1),attempts)
    assert not attempts[0]['reserved']


@pytest.mark.parametrize('failure',['read_timeout','unknown_usage'])
def test_response_fault_never_executes_even_an_apparently_valid_tool(tmp_path,failure):
    class TimeoutSocket(FakeSocket):
        def makefile(self,*args,**kwargs):
            class TimedBody(io.BytesIO):
                reads=0
                def read1(self,size=-1):
                    self.reads+=1
                    if self.reads>1:raise TimeoutError('CPU response read timeout')
                    return super().read1(40)
            return TimedBody(self.raw)
    upstream=TimeoutSocket() if failure=='read_timeout' else FakeSocket(sse(usage=False))
    attempts=[];budget=core.Budget(max_posts=48,max_bytes=32000000,seconds=900);step=mock.Mock()
    with mock.patch.object(a.socket,'create_connection',return_value=upstream) as connect:
        with pytest.raises((TimeoutError,RuntimeError)):
            a.run_session(bundle(),tmp_path,budget,lambda:state(),step,attempts)
    step.assert_not_called();assert upstream.closed and connect.call_count==1
    bill=a.accounting(attempts,budget)
    assert bill['reserved_posts']==1 and bill['known_forwarded_posts']==1 and bill['unknown_usage_attempts']==1
    assert bill['provider_usage']['total_tokens'] is None and not bill['integrity_passed']
    assert (tmp_path/'responses/00001.http').stat().st_size>0
    assert (tmp_path/'responses/00001.sse').exists()


def test_cache_is_input_subset_and_missing_cache_is_not_unknown_total_usage(tmp_path):
    raw=sse().replace(b'"total_tokens": 7',b'"total_tokens": 7, "prompt_tokens_details": {"cached_tokens": 2}')
    attempts=[];budget=core.Budget(max_posts=48,max_bytes=32000000,seconds=900)
    with mock.patch.object(a.socket,'create_connection',return_value=FakeSocket(raw)):
        a.exchange(core,tmp_path,a.payload_for(core,PROFILE,[],state()),budget,qualify,('CPU_FAKE',1),attempts)
    bill=a.accounting(attempts,budget)
    assert bill['provider_usage']==dict(prompt_tokens=5,completion_tokens=2,total_tokens=7)
    assert bill['cached_input_tokens']==2 and bill['noncached_input_tokens']==3 and bill['integrity_passed']
    attempts[0]['response_receipt']['usage'].pop('prompt_tokens_details')
    bill=a.accounting(attempts,budget)
    assert bill['provider_usage']['total_tokens']==7 and bill['cached_input_tokens'] is None and bill['integrity_passed']


def test_release_binds_new_protocol_and_actor_not_old_slot_authorization(tmp_path):
    with admitted_fixture(tmp_path) as f:
        checked=a.load_inputs(f.ref['path'],f.ref['sha256'])
        release=dict(schema='ALFWORLD_NATIVE_ACTOR_RELEASE_V1',status='RELEASED',protocol=copy.deepcopy(checked['protocol_ref']),
            actor_source=dict(path=str(PATH),sha256=hashlib.sha256(PATH.read_bytes()).hexdigest()),
            prior_manifest_sha256=f.protocol['prior']['manifest_sha256'],output_root=f.protocol['output_root'])
        path=Path(f.ref['path']).parent/'CPU_RELEASE.json';binding=ref(path,release)
        assert a.check_release(binding['path'],binding['sha256'],checked)==binding
        release['protocol']['sha256']='0'*64;binding=ref(path,release)
        with pytest.raises(ValueError):a.check_release(binding['path'],binding['sha256'],checked)
        assert not f.output.exists()


def test_http_error_with_reported_usage_keeps_known_costs(tmp_path):
    budget=core.Budget(max_posts=48,max_bytes=32000000,seconds=900);attempts=[]
    with mock.patch.object(a.socket,'create_connection',return_value=FakeSocket(sse(),status=400)):
        with pytest.raises(RuntimeError):a.exchange(core,tmp_path,a.payload_for(core,PROFILE,[],state()),budget,qualify,('CPU_FAKE',1),attempts)
    bill=a.accounting(attempts,budget)
    assert bill['provider_usage']['total_tokens']==7 and bill['known_usage_subtotal']['total_tokens']==7
    assert bill['unknown_usage_attempts']==0 and not bill['integrity_passed']


def test_execute_saves_actual_reset_for_real_witness_and_real_replay(tmp_path):
    """Fake native/socket I/O; production replay, trace witness and actor loop are real."""
    rec=r.recovery();bridge=rec.bridge()
    with admitted_fixture(tmp_path) as f,mock.patch.object(rec,'actor',return_value=core),mock.patch.object(rec,'bridge',return_value=bridge),mock.patch.object(bridge,'client_step') as client_step:
        f.manifest['game']=dict(sha256_game='a'*64)
        f.manifest['pool_binding']=dict(sha256='b'*64)
        f.protocol['prior']['manifest_sha256']=ref(f.prior/'manifest.json',f.manifest)['sha256']
        f.ref=ref(Path(f.ref['path']),f.protocol)
        reset=state(0);source_steps=[dict(action='look',state=state(1)),dict(action='inventory',state=state(2))]
        prefix=dict(reset=reset,steps=source_steps,visible_steps=source_steps,current=source_steps[-1]['state'],binding={})
        prefix['public_prefix_sha256']=hashlib.sha256(json.dumps([reset,source_steps],sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
        f.study.verify.return_value=(f.manifest,{},PROFILE,prefix,qualify)
        active={}
        def start(root,case,seed,label,caps,pool_path,pool_sha):
            active.update(root=root,index=0)
            header=dict(game_id=case,seed=seed,step_cap=100,bridge_sha256=core.BRIDGE_SHA,
                asset_sha256='a'*64,pool_manifest_sha256=pool_sha,caps=dict(caps,world_actions=100))
            header['episode_sha256']=hashlib.sha256(json.dumps(header,sort_keys=True).encode()).hexdigest()
            path=root/'execute_world.jsonl'
            with path.open('x') as out:
                out.write(json.dumps(dict(event='episode',**header))+'\n')
                out.write(json.dumps(dict(event='reset',state=reset))+'\n')
            return (object(),tmp_path/'CPU_NATIVE_SOCKET'),reset,{}
        def native_step(socket_path,action):
            row=source_steps[active['index']];assert row['action']==action;active['index']+=1
            with (active['root']/'execute_world.jsonl').open('a') as out:
                out.write(json.dumps(dict(event='step',**row))+'\n')
            return row['state']
        f.study.task_pool=lambda:SimpleNamespace(start_world=start)
        f.study.protocol=lambda *args:dict(pool_path='CPU_POOL')
        f.study.public=r.public
        f.study.replay_prefix=r.replay_prefix
        f.study.native_world_witness=r.native_world_witness
        f.study.recovery=lambda:rec
        client_step.side_effect=native_step
        @contextmanager
        def lock():yield
        with mock.patch.object(a,'resource_lock',lock),mock.patch.object(a,'check_release',return_value=dict(path='CPU_RELEASE',sha256='CPU_SHA')),\
             mock.patch.object(core,'stop_world') as stop,\
             mock.patch.object(a.socket,'create_connection',side_effect=[FakeSocket(sse(finish='stop')),FakeSocket(sse(finish='stop'))]) as connect:
            result=a.execute(f.ref['path'],f.ref['sha256'],'CPU_RELEASE','CPU_SHA')
        assert result['status']=='MODEL_STOP_UNWON',result['errors']
        assert result['errors']==[] and result['task_won'] is False
        assert json.loads((f.output/'initial_reset.json').read_text())==reset
        assert result['native_witness']['state']==source_steps[-1]['state']
        assert result['native_witness']['sha256']==hashlib.sha256((f.output/'execute_world.jsonl').read_bytes()).hexdigest()
        assert result['source_replay_cost']['control_world_actions']==2 and result['agent_world_actions']==0
        assert active['index']==2 and connect.call_count==2 and stop.call_count==1
        binding=json.loads((f.output/'manifest.json').read_text())['native_binding']
        assert r.native_world_witness(f.output,binding)['state']['action_count']==2
        saved=(f.output/'initial_reset.json').read_bytes();(f.output/'initial_reset.json').write_text(json.dumps(state(0,['look'])))
        with pytest.raises(ValueError,match='reset differs'):r.native_world_witness(f.output,binding)
        (f.output/'initial_reset.json').write_bytes(saved)
