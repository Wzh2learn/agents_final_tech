"""Direct function-tool ALFWorld capability control; no learning-effect claim."""
from __future__ import annotations
import argparse
import copy
from contextlib import contextmanager
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import signal
import socket
import time

HERE=Path(__file__).resolve().parent
ST=Path('/home/testuser/wzh/research_evidence/agent_learning_20261030/alfworld_text_qualification_20261106/context_study_v1')
STUDY=HERE/'alfworld_context_study.py'
PROFILE=dict(path=str(ST.parent.parent/'django_aggregation_agent_20261106/qwen38_27b_model_profile_v1.json'),
             sha256='9cbb51bb6dc64583cb376f81e8f8c1c28400cb494fce2793f1fa2ce60e39a279')
CAPS=dict(posts=48,seconds=900,world_actions=100,model_payload_bytes_combined=32000000)
SAMPLING=dict(seed=17,temperature=0.2,enable_thinking=False,context=32768,output=8192)
SYSTEM='Control the household environment using only environment_step. Choose one exact current admissible action. Treat tool results as current public evidence. Stop when the native environment is done; success requires native won=true.'
CONTINUE='Continue the unfinished task.'
BASH_BLOCK="\nUse only Bash, one environment action per tool call:\n/runtime/bin/python -B /world/client.py step --socket /world/s --action '<one exact action>'\n"
NATIVE_BLOCK='\nUse only environment_step, one exact action per tool call.\nChoose action from the current public admissible_commands returned by the environment.\n'


def sha(value):
    return hashlib.sha256(value).hexdigest()


def unique(pairs):
    value={}
    for k,v in pairs:
        if k in value:raise ValueError('duplicate JSON key')
        value[k]=v
    return value


def decode(raw):
    return json.loads(raw,object_pairs_hook=unique)


def write_new(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x',encoding='utf8') as out:json.dump(value,out,ensure_ascii=False,indent=2);out.write('\n')


def read_ref(ref,*,binary=False,private=True):
    if type(ref) is not dict or set(ref)!={'path','sha256'}:raise ValueError('exact path/SHA reference required')
    path=Path(ref['path'])
    if (not path.is_absolute() or path!=path.resolve() or path.is_symlink() or any(p.is_symlink() for p in path.parents)
            or not path.is_file() or path.stat().st_nlink!=1 or private and ST not in path.parents):
        raise ValueError('unsafe frozen input')
    raw=path.read_bytes()
    if sha(raw)!=ref['sha256']:raise ValueError('frozen input SHA changed')
    return raw if binary else decode(raw)


def prompt_from_request(task,forwarded):
    users=[x.get('content') for x in forwarded.get('messages',[]) if x.get('role')=='user']
    quoted='"'+task.replace('"','\\"')+'"'
    if len(users)!=1 or users[0] not in (task,quoted) or task.count(BASH_BLOCK)!=1:
        raise ValueError('prior full public prompt/known quote layer is not exact')
    if [x.get('function',{}).get('name') for x in forwarded.get('tools',[])]!=['bash']:
        raise ValueError('prior tool wrapper is not the measured Bash interface')
    prompt=task.replace(BASH_BLOCK,NATIVE_BLOCK)
    proof=dict(original_user_sha256=sha(users[0].encode()),normalized_public_task_sha256=sha(task.encode()),
        new_user_sha256=sha(prompt.encode()),old_messages_sha256=sha(json.dumps(forwarded['messages'],sort_keys=True).encode()),
        old_tools_sha256=sha(json.dumps(forwarded['tools'],sort_keys=True).encode()),new_system_sha256=sha(SYSTEM.encode()),
        changes=['Known lossless OpenCode argv quote layer removed','OpenCode system replaced by native actor system',
                 'Exact Bash dispatch block replaced','Dynamic native function schema and assistant/tool history used'],
        interpretation='Interface/controller combination diagnostic; not a single-factor or learning comparison.')
    return prompt,proof


def load_inputs(protocol_path,protocol_sha):
    ref=dict(path=str(Path(protocol_path)),sha256=protocol_sha);p=read_ref(ref)
    keys={'schema','prior','prior_first_request','prior_first_request_body','profile','output_root','caps','sampling'}
    if (set(p)!=keys or p['schema']!='ALFWORLD_NATIVE_ACTOR_PROTOCOL_V1' or p['caps']!=CAPS or
            any(type(v) is not int for v in p['caps'].values()) or p['sampling']!=SAMPLING or
            p['sampling']['enable_thinking'] is not False or p['profile']!=PROFILE or
            set(p['prior'])!={'root','manifest_sha256','study_source'}):
        raise ValueError('unsupported direct native actor contract')
    prior=p['prior'];root=Path(prior['root']);output=Path(p['output_root'])
    if (not output.is_absolute() or output!=output.resolve() or ST/'learning_comparison_v1' not in output.parents or
            any(x.is_symlink() for x in [output,*output.parents]) or output==root or root in output.parents or output in root.parents):
        raise ValueError('new independent private output root required')
    if output.exists():raise FileExistsError('never reuse an output root')
    m=read_ref(dict(path=str(root/'manifest.json'),sha256=prior['manifest_sha256']))
    if prior['study_source']['path']!=str(STUDY) or m['components'].get(str(STUDY))!=prior['study_source']['sha256']:
        raise ValueError('prior study source is not explicitly bound')
    for path,digest in m['components'].items():read_ref(dict(path=path,sha256=digest),binary=True,private=False)
    read_ref(prior['study_source'],binary=True,private=False)
    spec=importlib.util.spec_from_file_location('direct_native_prior_study',STUDY)
    study=importlib.util.module_from_spec(spec);spec.loader.exec_module(study)
    verified,old_protocol,profile,prefix,qualify=study.verify(root,prior['manifest_sha256'])
    if (verified!=m or prefix is None or m['stage']!='drop_full' or m['backend']!='teacher27b' or
            m.get('experience_mode')!='none' or m['experience_assignment']!={} or m['model_seed']!=17 or
            m['world_seed']!=17 or m['profile_sha256']!=PROFILE['sha256'] or m.get('reference_context') is not None or
            m.get('runtime_controls')!={'native_terminal_stop':True,'recent_tool_rounds':None}):
        raise ValueError('prior must be the frozen full public none/teacher condition')
    read_ref(p['profile'],private=False)  # Only the fixed sibling profile escapes ST.
    for name,key in [('00001.json','prior_first_request'),('00001.body','prior_first_request_body')]:
        if Path(p[key]['path'])!=root/'requests'/name:raise ValueError('first request must belong to prior root')
    first=read_ref(p['prior_first_request']);body=read_ref(p['prior_first_request_body'],binary=True)
    if decode(body)!=first['forwarded'] or body!=json.dumps(first['forwarded'],separators=(',',':')).encode():
        raise ValueError('prior actual request body differs')
    core=study.recovery().actor()
    if any(first['forwarded'].get(k)!=v for k,v in core.model_payload({},'teacher27b',profile,17).items()):
        raise ValueError('prior sampling differs from native actor baseline')
    prompt,proof=prompt_from_request((root/'task.txt').read_text(),first['forwarded'])
    return dict(p=p,protocol_ref=ref,prior=m,study=study,profile=profile,prefix=prefix,qualify=qualify,
                prompt=prompt,prompt_proof=proof,core=core)


def check_release(path,digest,bundle):
    ref=dict(path=str(Path(path)),sha256=digest);release=read_ref(ref);p=bundle['p']
    if (set(release)!={'schema','status','protocol','actor_source','prior_manifest_sha256','output_root'} or
            release['schema']!='ALFWORLD_NATIVE_ACTOR_RELEASE_V1' or release['status']!='RELEASED' or
            release['protocol']!=bundle['protocol_ref'] or release['output_root']!=p['output_root'] or
            release['prior_manifest_sha256']!=p['prior']['manifest_sha256'] or
            release['actor_source']!={'path':str(Path(__file__).resolve()),'sha256':sha(Path(__file__).read_bytes())}):
        raise ValueError('explicit D release does not bind this execution')
    return ref


@contextmanager
def resource_lock():
    import fcntl
    path=ST/'model_resource.lock'
    if path.is_symlink() or not path.is_file():raise ValueError('existing shared resource lock required')
    before=path.stat()
    with path.open('r+') as lock:
        actual=os.fstat(lock.fileno())
        if (before.st_dev,before.st_ino)!=(actual.st_dev,actual.st_ino):raise ValueError('resource lock inode changed')
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        try:
            after=path.stat()
            if (after.st_dev,after.st_ino)!=(actual.st_dev,actual.st_ino):raise ValueError('resource lock replaced')
            yield
        finally:fcntl.flock(lock,fcntl.LOCK_UN)


def tool_for(state):
    commands=state['admissible_commands']
    if not commands or any(type(x) is not str or not x for x in commands) or len(commands)!=len(set(commands)):
        raise ValueError('current native action enum malformed')
    return dict(type='function',function=dict(name='environment_step',description='Execute one exact current public admissible environment action.',
        strict=True,parameters=dict(type='object',properties=dict(action=dict(type='string',enum=list(commands))),
                                    required=['action'],additionalProperties=False)))


def payload_for(core,profile,messages,state):
    return core.model_payload(dict(messages=copy.deepcopy(messages),tools=[tool_for(state)],
        tool_choice=dict(type='function',function=dict(name='environment_step')),parallel_tool_calls=False),'teacher27b',profile,17)


class ModelContractError(ValueError):pass
class CapClosed(ValueError):pass


def reply_from_sse(raw,state):
    content='';calls={};finish=None;done=False
    for line in raw.splitlines():
        if not line.startswith(b'data:'):continue
        data=line[5:].strip()
        if data==b'[DONE]':done=True;continue
        if done:raise ModelContractError('SSE data after DONE')
        item=decode(data)
        for choice in item.get('choices',[]):
            if choice.get('index')!=0:raise ModelContractError('multiple model choices')
            delta=choice.get('delta',{})
            if delta.get('role','assistant')!='assistant' or delta.get('function_call') is not None:
                raise ModelContractError('unexpected assistant interface')
            part=delta.get('content')
            if part is not None:
                if type(part) is not str:raise ModelContractError('nontext assistant content')
                content+=part
            for piece in delta.get('tool_calls',[]):
                if piece.get('index')!=0 or set(piece)-{'index','id','type','function'}:
                    raise ModelContractError('parallel/unknown tool call')
                call=calls.setdefault(0,dict(id='',type='function',function=dict(name='',arguments='')))
                if piece.get('type','function')!='function':raise ModelContractError('tool type changed')
                if piece.get('id'):
                    if call['id'] and call['id']!=piece['id']:raise ModelContractError('tool ID changed')
                    call['id']=piece['id']
                function=piece.get('function',{})
                if set(function)-{'name','arguments'}:raise ModelContractError('unknown function fields')
                for key in ('name','arguments'):
                    if key in function:
                        if type(function[key]) is not str:raise ModelContractError('function fields must be strings')
                        call['function'][key]+=function[key]
            if choice.get('finish_reason') is not None:
                if finish is not None:raise ModelContractError('duplicate finish')
                finish=choice['finish_reason']
    if not done:raise ModelContractError('incomplete SSE')
    assistant=dict(role='assistant',content=content or None)
    if not calls:
        if finish!='stop':raise ModelContractError('nonordinary model stop:'+str(finish))
        return assistant,None
    call=calls[0]
    if finish!='tool_calls' or type(call['id']) is not str or not call['id'] or call['function']['name']!='environment_step':
        raise ModelContractError('exact single named tool call required')
    args=decode(call['function']['arguments'])
    if type(args) is not dict or set(args)!={'action'} or type(args['action']) is not str or args['action'] not in state['admissible_commands']:
        raise ModelContractError('action is not one exact current native command')
    assistant['tool_calls']=[call]
    return assistant,args['action']


def valid_usage(value):
    return (isinstance(value,dict) and all(type(value.get(k)) is int and value[k]>=0 for k in
        ('prompt_tokens','completion_tokens','total_tokens')) and value['total_tokens']==value['prompt_tokens']+value['completion_tokens'])


def exchange(core,root,payload,budget,qualify,endpoint,attempts):
    number=len(attempts)+1;tag=str(number).zfill(5);body=json.dumps(payload,separators=(',',':')).encode()
    record=dict(attempt=number,reserved=False,send_started=False,forwarded=False,response_wire_observed_bytes=0,
                tool_contract_sha256=sha(json.dumps({k:payload[k] for k in ('tools','tool_choice','parallel_tool_calls')},separators=(',',':')).encode()),
                request_body_bytes=len(body),request_body_sha256=sha(body),error=None)
    attempts.append(record);socket_owned=None;wire=None
    try:
        write_new(root/'requests'/(tag+'.json'),payload)
        path=root/'requests'/(tag+'.body')
        with path.open('xb') as out:out.write(body)
        proof=qualify(payload);proof['safety_margin_tokens']=512
        proof['fits_with_margin']=proof['template_input_tokens']+proof['reserved_output_tokens']+512<=proof['context']
        write_new(root/'template_checks'/(tag+'.json'),proof)
        if not proof['fits_with_margin']:raise CapClosed('CONTEXT_CAP')
        try:record['reserved_post']=budget.reserve(len(body));record['reserved']=True
        except ValueError as exc:
            if budget.failed:raise RuntimeError('model budget poisoned') from exc
            raise CapClosed('POST_CAP' if budget.posts>=budget.max_posts else 'TIME_CAP' if time.monotonic()>=budget.deadline else 'BYTE_CAP') from exc
        def remaining():
            value=budget.deadline-time.monotonic()
            if value<=0:raise TimeoutError('episode deadline reached')
            return value
        wirepath=root/'responses'/(tag+'.http');wirepath.parent.mkdir(parents=True,exist_ok=True);wire=wirepath.open('xb')
        socket_owned=socket.create_connection(endpoint,timeout=min(20,remaining()))
        socket_owned.settimeout(min(5,remaining()))
        packet=b'POST /v1/chat/completions HTTP/1.1\r\nHost: local\r\nContent-Type: application/json\r\nConnection: close\r\nContent-Length: '+str(len(body)).encode()+b'\r\n\r\n'+body
        record['send_started']=True;socket_owned.sendall(packet);record['forwarded']=True
        class BoundedSocket:
            def settimeout(self,seconds):socket_owned.settimeout(min(seconds,remaining()))
            def makefile(self,*a,**k):
                stream=socket_owned.makefile(*a,**k)
                class TimedFile:
                    def __getattr__(self,name):
                        method=getattr(stream,name)
                        if name not in ('read','read1','readline'):return method
                        def read(*args,**kwargs):
                            socket_owned.settimeout(remaining());data=method(*args,**kwargs)
                            wire.write(data);record['response_wire_observed_bytes']+=len(data);budget.response(len(data))
                            return data
                        return read
                return TimedFile()
        class Sink:
            def sendall(self,data):pass
        result=core.load_relay()(Sink(),BoundedSocket(),root/'responses'/(tag+'.sse'))
        if result['status']!=200:raise RuntimeError('model HTTP status '+str(result['status'])+'; no interface fallback')
        raw=(root/'responses'/(tag+'.sse')).read_bytes()
        return raw
    except BaseException as exc:
        record['error']=dict(type=type(exc).__name__,detail=str(exc))
        raise
    finally:
        if socket_owned:socket_owned.close()
        if wire:wire.close()
        receipt=root/'responses'/(tag+'.sse.receipt.json')
        if receipt.exists():record['response_receipt']=decode(receipt.read_bytes())
        record['possible_partial_send']=record['send_started'] and not record['forwarded']
        write_new(root/'ledger'/(tag+'.json'),record)


def accounting(attempts,budget):
    paid=[x for x in attempts if x['reserved']];known=[];cache=[]
    for item in paid:
        receipt=item.get('response_receipt',{});usage=receipt.get('usage')
        if receipt.get('complete') and valid_usage(usage):
            known.append(usage);details=usage.get('prompt_tokens_details')
            value=details.get('cached_tokens') if isinstance(details,dict) else None
            cache.append(value if type(value) is int and 0<=value<=usage['prompt_tokens'] else None)
    totals={k:sum(u[k] for u in known) for k in ('prompt_tokens','completion_tokens','total_tokens')}
    unknown=len(paid)-len(known);partial=sum(x['possible_partial_send'] for x in paid)
    cached=sum(cache) if cache and all(x is not None for x in cache) and not unknown else None
    forwarded=sum(x['forwarded'] for x in paid)
    return dict(attempts=len(attempts),reserved_posts=budget.posts,known_forwarded_posts=forwarded,
        actual_forwarded_posts=None if partial else forwarded,possible_additional_forwarded_posts=partial,
        unknown_usage_attempts=unknown,known_usage_subtotal=totals,provider_usage={k:None for k in totals} if unknown else totals,
        cached_input_tokens=cached,noncached_input_tokens=totals['prompt_tokens']-cached if cached is not None else None,
        request_body_bytes_reserved=budget.request_bytes,response_wire_bytes_charged=budget.response_bytes,
        response_wire_bytes_observed=sum(x['response_wire_observed_bytes'] for x in paid),
        integrity_passed=not unknown and not partial and all(x['forwarded'] and x.get('response_receipt',{}).get('status')==200 for x in paid),
        byte_scope='Compact actual request body plus original HTTP response wire consumed; cache is an input subset. Differs from old downstream normalized HTTP relay headers.')


def run_session(bundle,root,budget,state_fn,step,attempts):
    core=bundle['core'];messages=[dict(role='system',content=SYSTEM),dict(role='user',content=bundle['prompt'])]
    neutral=0
    while True:
        state=state_fn()
        if state['done'] or state['won']:return ('NATIVE_WON' if state['won'] else 'NATIVE_DONE_UNWON'),neutral
        if budget.posts>=budget.max_posts:return 'POST_CAP',neutral
        if time.monotonic()>=budget.deadline:return 'TIME_CAP',neutral
        payload=payload_for(core,bundle['profile'],messages,state)
        try:raw=exchange(core,root,payload,budget,bundle['qualify'],(bundle['profile']['host'],bundle['profile']['port']),attempts)
        except CapClosed as exc:return str(exc),neutral
        receipt=attempts[-1].get('response_receipt',{})
        if not receipt.get('complete') or not valid_usage(receipt.get('usage')):raise RuntimeError('unknown provider usage; no retry')
        assistant,action=reply_from_sse(raw,state);messages.append(assistant)
        if action is None:
            if neutral:return 'MODEL_STOP_UNWON',neutral
            messages.append(dict(role='user',content=CONTINUE));neutral+=1
        else:
            current=step(action)
            messages.append(dict(role='tool',tool_call_id=assistant['tool_calls'][0]['id'],content=json.dumps(current,ensure_ascii=False)))


def execute(protocol_path,protocol_sha,release_path,release_sha):
    bundle=load_inputs(protocol_path,protocol_sha);release=check_release(release_path,release_sha,bundle)
    p=bundle['p'];root=Path(p['output_root']);core=bundle['core'];study=bundle['study'];prior=bundle['prior']
    with resource_lock():
        if root.exists():raise FileExistsError('never reuse an output root')
        root.mkdir(parents=True)
        budget=core.Budget(max_posts=48,max_bytes=32000000,seconds=900);attempts=[];world=None;state=None;errors=[];neutral=0
        started=time.monotonic();status='RUNTIME_FAULT';witness=None;replay=None
        native_binding=dict(case_id=prior['case_id'],world_seed=17,caps=CAPS,game=prior['game'],pool_binding=prior['pool_binding'])
        write_new(root/'manifest.json',dict(schema='ALFWORLD_NATIVE_ACTOR_EXECUTION_V1',protocol=bundle['protocol_ref'],release=release,
            actor_source_sha256=sha(Path(__file__).read_bytes()),prior=p['prior'],prompt_wrapper=bundle['prompt_proof'],
            replay_action_count=len(bundle['prefix']['steps']),visible_count=len(bundle['prefix']['visible_steps']),caps=CAPS,native_binding=native_binding))
        (root/'task.txt').write_text(bundle['prompt'],encoding='utf8')
        def interrupt(*_):raise InterruptedError('owned native actor interrupted')
        old={s:signal.signal(s,interrupt) for s in (signal.SIGTERM,signal.SIGINT)}
        try:
            world,reset,_=study.task_pool().start_world(root,prior['case_id'],17,'execute',CAPS,bundle['study'].protocol(
                prior['protocol_path'],prior['protocol_sha256'])['pool_path'],prior['pool_binding']['sha256'])
            reset=study.public(reset)
            write_new(root/'initial_reset.json',reset)
            def step(action):
                if time.monotonic()>=budget.deadline:raise TimeoutError('episode deadline reached')
                return study.public(study.recovery().bridge().client_step(world[1]/'s',action))
            state,replay=study.replay_prefix(bundle['prefix'],study.public(reset),step,root/'source_replay.jsonl')
            def current():
                nonlocal witness,state
                witness=study.native_world_witness(root,native_binding);state=witness['state']
                return state
            if current()!=bundle['prefix']['current']:raise ValueError('new native handoff differs from frozen prior')
            status,neutral=run_session(bundle,root,budget,current,step,attempts)
        except BaseException as exc:
            errors.append(dict(type=type(exc).__name__,detail=str(exc)))
        finally:
            if world:
                try:core.stop_world(world)
                except BaseException as exc:errors.append(dict(cleanup='owned_world',type=type(exc).__name__,detail=str(exc)))
            if world:
                try:
                    witness=study.native_world_witness(root,native_binding);state=witness['state']
                except BaseException as exc:
                    state=None;errors.append(dict(cleanup='native_witness',type=type(exc).__name__,detail=str(exc)))
            for sig,handler in old.items():signal.signal(sig,handler)
            bill=accounting(attempts,budget)
            if errors or not bill['integrity_passed']:status='RUNTIME_FAULT'
            receipt=dict(schema='ALFWORLD_NATIVE_ACTOR_RECEIPT_V1',protocol=bundle['protocol_ref'],release=release,
                manifest_sha256=sha((root/'manifest.json').read_bytes()),actor_source_sha256=sha(Path(__file__).read_bytes()),
                prior_manifest_sha256=p['prior']['manifest_sha256'],caps=CAPS,
                status=status,task_won=state['won'] if state is not None else None,
                final_public_state=state,native_witness=witness,accounting=bill,attempts=attempts,errors=errors,
                ordinary_continuation_intents=neutral,source_replay_cost=replay,source_formation_charged_again=False,
                replay_action_count=len(bundle['prefix']['steps']),agent_world_actions=max(0,state['action_count']-len(bundle['prefix']['steps'])) if state else None,
                elapsed_seconds=time.monotonic()-started,not_learning_evidence=True,not_single_factor_comparison=True)
            write_new(root/'receipt.json',receipt)
    return receipt


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--protocol',type=Path,required=True);parser.add_argument('--protocol-sha',required=True)
    mode=parser.add_mutually_exclusive_group();mode.add_argument('--check-only',action='store_true');mode.add_argument('--execute',action='store_true')
    parser.add_argument('--release',type=Path);parser.add_argument('--release-sha')
    args=parser.parse_args(argv)
    if not args.execute:
        checked=load_inputs(args.protocol,args.protocol_sha)
        print(json.dumps(dict(status='CPU_INPUTS_BOUND_NO_EXECUTION',output_root=checked['p']['output_root'],prompt=checked['prompt_proof'])))
        return 0
    if not args.release or not args.release_sha:parser.error('execute requires an explicit frozen D release')
    result=execute(args.protocol,args.protocol_sha,args.release,args.release_sha)
    print(json.dumps(dict(status=result['status'],task_won=result['task_won'],accounting=result['accounting'])))
    return 0 if result['status']!='RUNTIME_FAULT' else 1


if __name__=='__main__':
    raise SystemExit(main())
