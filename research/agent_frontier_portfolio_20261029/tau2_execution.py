"""GB10 development adapter: OpenCode decisions, official tau2 world/user/grader.

No hidden task, user-tool access or reward is mounted in the actor container.
This is an execution carrier; no learned-method effectiveness is implied.
Requires isolated tau2 v1.0.1, commit fc0055dc, and the existing owned actor runtime.
FCCL_TAU2_ROOT selects the private data/evidence root; credentials enter via stdin.
The original executed snapshot is preserved in its evidence package.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import http.client
import http.server
import importlib.util
import json
import os
from pathlib import Path
import queue
import socket
import socketserver
import subprocess
import sys
import threading
import time

REPO = Path(os.environ.get('FCCL_RESEARCH_REPO', str(Path(__file__).resolve().parents[2])))
ROOT = Path(os.environ.get('FCCL_TAU2_ROOT', '/home/testuser/wzh/research_evidence/agent_learning_20261030/fccl_tau2_v1'))
os.environ['TAU2_DATA_DIR'] = str(ROOT / 'upstream/data')
os.environ['LITELLM_LOCAL_MODEL_COST_MAP'] = 'True'
sys.path.insert(0, str(REPO))
from scripts.graph.research_school_gateway import BatchBudget, SchoolGateway, MODEL, usage_from_body


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8') as f:
        f.write(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def tau():
    from loguru import logger
    logger.remove()
    from tau2.domains.telecom.environment import get_environment
    from tau2.data_model.tasks import Task
    from tau2.data_model.message import AssistantMessage, UserMessage, ToolCall, MultiToolMessage
    from tau2.data_model.simulation import SimulationRun, TerminationReason
    from tau2.evaluator.evaluator import evaluate_simulation, EvaluationType
    from tau2.evaluator.evaluator_env import EnvironmentEvaluator
    from tau2.orchestrator.orchestrator import Orchestrator
    from tau2.agent.llm_agent import LLMAgent
    from tau2.user.user_simulator import UserSimulator
    from tau2.utils.llm_utils import to_litellm_messages
    return locals()


def prepare():
    """Select by IDs alone, before opening the selected scenarios/solutions."""
    data = ROOT / 'upstream/data/tau2/domains/telecom'
    split = json.loads((data / 'split_tasks.json').read_text())
    rank = lambda s: hashlib.sha256(('fccl-telecom-v1:' + str(s)).encode()).digest()
    plan = dict(upstream_commit='fc0055dc4e0a316c3f83133267fbd6faaa770992',
                dev=sorted(split['train'], key=rank)[:3],
                unseen=sorted(split['test'], key=rank)[:1],
                input_policy='workflow for every actor; native private user kept on host',
                model=MODEL, output_cap=8192, actor_post_cap=24, total_post_cap=72,
                token_cap=2_000_000, seconds=900, native_steps=160,
                purpose='development carrier and residual discovery; not method evidence',
                sampling='campus gateway has no supported seed control; do not claim seeded replication',
                task_file_sha256=sha(data/'tasks.json'), split_sha256=sha(data/'split_tasks.json'))
    write(ROOT/'PLAN.json', plan)
    print(json.dumps({'prepared':True,'plan_sha256':sha(ROOT/'PLAN.json'), 'dev':plan['dev'], 'unseen':plan['unseen']}))


def task_at(index):
    api = tau(); plan = json.loads((ROOT/'PLAN.json').read_text())
    data = ROOT/'upstream/data/tau2/domains/telecom/tasks.json'
    assert sha(data) == plan['task_file_sha256']
    selected = plan['dev'][index]
    tasks = json.loads(data.read_text())
    if isinstance(tasks, dict): tasks = tasks['tasks']
    return api, plan, api['Task'].model_validate(next(t for t in tasks if t['id']==selected))


def qualify(index, *, prepared=None, root_override=None):
    api, plan, task = prepared if prepared is not None else task_at(index)
    out = Path(root_override) if root_override is not None else ROOT / f'dev{index}' / 'qualification'
    out.mkdir(parents=True, exist_ok=False)
    assert not task.evaluation_criteria.nl_assertions
    now = '2026-11-12T00:00:00'
    initial = task.initial_state
    hist = copy.deepcopy(initial.message_history or []) if initial else []
    env = api['get_environment'](policy_type='workflow')
    env.set_state(initialization_data=initial.initialization_data if initial else None,
                  initialization_actions=initial.initialization_actions if initial else None,
                  message_history=hist)
    trajectory = copy.deepcopy(hist)
    def grade(messages, label):
        sim = api['SimulationRun'](id='qualification-'+label,task_id=task.id,start_time=now,end_time=now,
                                  duration=0,termination_reason=api['TerminationReason'].USER_STOP,messages=messages)
        return api['evaluate_simulation'](sim,task,api['EvaluationType'].ALL,False,'telecom-workflow').model_dump(mode='json')
    base = grade(trajectory, 'base')
    for i, action in enumerate(task.evaluation_criteria.actions or []):
        tc = api['ToolCall'](id=f'gold-{i}',name=action.name,arguments=action.arguments,requestor=action.requestor)
        cls = api['UserMessage'] if action.requestor=='user' else api['AssistantMessage']
        trajectory += [cls(role=action.requestor,content=None,tool_calls=[tc]), env.get_response(tc)]
    gold = grade(trajectory, 'reference')
    write(out/'RESULT.json',dict(task_id=task.id,base=base,reference=gold,models=0,
                               purpose='host-only native task integrity, not actor training or success'))
    print(json.dumps(dict(task_id=task.id,base=base['reward'],reference=gold['reward'],models=0)))


class Provider:
    def __init__(self, key, root, plan):
        interval=plan.get('request_interval_seconds',0)
        cooldown=plan.get('initial_cooldown_seconds',0)
        if any(type(x) not in (int,float) or not 0<=x<=120 for x in (interval,cooldown)):
            raise ValueError('invalid declared request pacing')
        self.budget = BatchBudget(root/'budget',posts=plan['total_post_cap'],tokens=plan['token_cap'])
        self.gateway = SchoolGateway(key,self.budget)
        self.root, self.lock, self.counts = root, threading.Lock(), {'actor':0,'user':0}
        self.deadline = time.monotonic()+plan['seconds']
        self.actor_cap = plan['actor_post_cap']
        self.request_interval=interval;self.next_send=time.monotonic()+cooldown
        self.failed_status=None

    def wait_request_slot(self):
        # Called under the shared actor/user lock, before budget reservation.
        pause=max(0,self.next_send-time.monotonic())
        if time.monotonic()+pause>=self.deadline:
            raise TimeoutError('episode deadline before paced request')
        if pause:time.sleep(pause)
        if time.monotonic()>=self.deadline:raise TimeoutError('episode deadline')
        self.next_send=time.monotonic()+self.request_interval

    def call(self, payload, role):
        with self.lock:
            if self.failed_status is not None:
                raise RuntimeError('provider paused after HTTP '+str(self.failed_status))
            if time.monotonic()>=self.deadline: raise TimeoutError('episode deadline')
            if role=='actor' and self.counts[role]>=self.actor_cap: raise RuntimeError('actor post cap')
            self.wait_request_slot()
            assert payload['model']==MODEL
            for k in ('seed','thinking','reasoning_effort','chat_template_kwargs','max_completion_tokens'):
                payload.pop(k,None)
            payload['max_tokens']=8192
            body=json.dumps(payload,ensure_ascii=False,separators=(',',':')).encode()
            ordinal=sum(self.counts.values())+1
            wire=self.root/'wire'; wire.mkdir(exist_ok=True)
            req=wire/f'{ordinal:05d}.{role}.request.json'
            with req.open('xb') as f:f.write(body)
            conn=None
            try:
                idx,conn=self.gateway.open(body,timeout=min(60,max(.01,self.deadline-time.monotonic())))
                self.counts[role]+=1
                response=http.client.HTTPResponse(conn);response.begin()
                raw=response.read(8*1024**2+1)
                with req.with_suffix('.response').open('xb') as f:f.write(raw)
                self.budget.finish(status=response.status,body=raw)
                write(req.with_suffix('.receipt.json'),dict(index=idx,role=role,status=response.status,usage=usage_from_body(raw)))
                if len(raw)>8*1024**2:raise RuntimeError('response byte cap')
                if response.status!=200:
                    self.failed_status=response.status
                    raise RuntimeError('provider HTTP '+str(response.status))
                return raw,response.getheader('Content-Type','application/json')
            except BaseException:
                if self.budget.pending is not None:self.budget.finish()
                raise
            finally:
                if conn is not None:conn.close()


def project_message(message):
    """Stable public projection; native metadata/private user tools stay on host."""
    role=message.role
    calls=getattr(message,'tool_calls',None)
    if (role=='tool' and message.requestor!='assistant') or (role=='user' and calls):
        raise ValueError('private user tool history cannot enter actor context')
    value={'role':role}
    if message.content is not None:value['content']=message.content
    if calls:value['tool_calls']=[dict(id=c.id,name=c.name,arguments=c.arguments) for c in calls]
    if role=='tool':value.update(id=message.id,requestor='assistant',error=message.error)
    return value


def make_world(api, task, provider, root, plan, evaluation_task=None):
    LLMAgent=api['LLMAgent']; AM=api['AssistantMessage']; MT=api['MultiToolMessage']; TC=api['ToolCall']
    class QueueAgent(LLMAgent):
        def __init__(self, **kwargs):
            super().__init__(llm=MODEL,**kwargs)
            self.actions=queue.Queue();self.observations=queue.Queue();self.turn=0
        def _generate_next_message(self,message,state):
            new=message.tool_messages if isinstance(message,MT) else [message]
            state.messages.extend(new);self.turn+=1
            observation=dict(done=False,turn=self.turn,messages=[project_message(m) for m in (state.messages if self.turn==1 else new)])
            # QueueAgent receives only the official agent-visible projection.
            assert all(not (m.role=='tool' and m.requestor=='user') for m in state.messages)
            self.observations.put(observation)
            command=self.actions.get(timeout=max(.01,provider.deadline-time.monotonic()))
            if command is None:raise TimeoutError('actor stopped before native user termination')
            if command['name']=='say':return AM(role='assistant',content=command['arguments']['message'])
            return AM(role='assistant',content=None,tool_calls=[TC(id=f'actor-{self.turn}',name=command['name'],arguments=command['arguments'])])
    env=api['get_environment'](policy_type='workflow')
    agent=QueueAgent(tools=env.get_tools(),domain_policy=env.get_policy())
    user=api['UserSimulator'](llm=MODEL,instructions=str(task.user_scenario),tools=env.get_user_tools(),llm_args={})
    def generate_user(*,model,messages,tools=None,**kwargs):
        payload=dict(model=MODEL,messages=api['to_litellm_messages'](messages),max_tokens=8192,temperature=0,stream=False)
        if tools:payload.update(tools=[t.openai_schema for t in tools],tool_choice='auto')
        raw,_=provider.call(payload,'user'); value=json.loads(raw)
        choice=value['choices'][0]
        if choice['finish_reason']=='length':raise RuntimeError('user output truncated')
        m=choice['message']; calls=[TC(id=x['id'],name=x['function']['name'],arguments=json.loads(x['function']['arguments'])) for x in m.get('tool_calls') or []]
        return AM(role='assistant',content=m.get('content'),tool_calls=calls or None)
    import tau2.user.user_simulator as user_module
    user_module.generate=generate_user
    world=api['Orchestrator'](domain='telecom-workflow',agent=agent,user=user,environment=env,task=task,
                              max_steps=plan['native_steps'],max_errors=10,timeout=plan['seconds'])
    def run():
        try:
            sim=world.run();write(root/'simulation.json',sim.model_dump(mode='json'))
            reward=api['evaluate_simulation'](sim,evaluation_task or task,api['EvaluationType'].ALL,False,'telecom-workflow')
            write(root/'native_reward.json',reward.model_dump(mode='json'))
            write(root/'world_final.json',dict(termination=str(sim.termination_reason),agent_db=env.get_db_hash(),user_db=env.get_user_db_hash()))
            agent.observations.put(dict(done=True,termination=sim.termination_reason.value))
        except BaseException as exc:
            write(root/'world_failure.json',dict(type=type(exc).__name__,message=str(exc)))
            agent.observations.put(dict(done=True,error='world_failure'))
    thread=threading.Thread(target=run,daemon=True);thread.start()
    return env,agent,world,thread


CLIENT = r'''import json,socket,sys
request=json.loads(sys.argv[1]); s=socket.socket(socket.AF_UNIX);s.settimeout(850);s.connect('/world/s')
s.sendall(json.dumps(request,separators=(',',':')).encode()+b'\n');parts=[]
while True:
 b=s.recv(65536)
 if not b:break
 parts.append(b)
 if b'\n' in b:break
s.close();print(b''.join(parts).decode().strip())
'''


def validate_action(cmd, current, public_tools):
    if type(cmd) is not dict or set(cmd)!={'op','turn','name','arguments'} or cmd['op']!='act':
        raise ValueError('invalid operation')
    if current.get('done') or type(cmd['turn']) is not int or cmd['turn']!=current['turn']:
        raise ValueError('stale or ended turn')
    names={t['function']['name'] for t in public_tools}
    if type(cmd['name']) is not str or cmd['name'] not in names|{'say'} or type(cmd['arguments']) is not dict:
        raise ValueError('not an actor tool')
    try:
        json.dumps(cmd,allow_nan=False)
    except (TypeError,ValueError):
        raise ValueError('non-JSON action') from None
    if cmd['name']=='say' and (set(cmd['arguments'])!={'message'} or type(cmd['arguments']['message']) is not str):
        raise ValueError('invalid message')
    return cmd


def smoke(index):
    api,plan,task=task_at(index)
    root=ROOT/f'dev{index}'/'mock_queue_smoke';root.mkdir(parents=True,exist_ok=False)
    class Fake:
        deadline=time.monotonic()+30
        calls=0
        def call(self,payload,role):
            assert role=='user';self.calls+=1
            # This scripted customer is solely a zero-model transport check.
            content='Hello, I need help with my phone.' if self.calls==1 else '###STOP###'
            return json.dumps(dict(choices=[dict(finish_reason='stop',message=dict(content=content))])).encode(),'application/json'
    fake=Fake();env,agent,world,thread=make_world(api,task,fake,root,plan)
    obs=agent.observations.get(timeout=10);assert obs['turn']==1 and not obs['done']
    public_tools=[t.openai_schema for t in env.get_tools()]
    user_only={t.name for t in env.get_user_tools()}-{t['function']['name'] for t in public_tools}
    assert user_only
    bads=[dict(op='act',turn=1,name=sorted(user_only)[0],arguments={}),
          dict(op='act',turn=0,name='say',arguments={'message':'x'}),
          dict(op='reset',turn=1,name='say',arguments={'message':'x'})]
    for bad in bads:
        try:validate_action(bad,obs,public_tools)
        except ValueError:pass
        else:raise AssertionError('forbidden operation accepted')
    cmd=validate_action(dict(op='act',turn=1,name='say',arguments={'message':'Thank you.'}),obs,public_tools)
    agent.actions.put(cmd);final=agent.observations.get(timeout=10);thread.join(timeout=5)
    assert final['done'] and final['termination']=='user_stop' and not thread.is_alive()
    native=json.loads((root/'native_reward.json').read_text());assert native['reward']==0
    assert all(m.get('requestor')!='user' for m in obs['messages'])
    result=dict(label='MOCK_ORACLE',model_calls=0,forbidden_operations_rejected=len(bads),
                native_reward=native['reward'],terminal=final['termination'],fake_user_responses=fake.calls)
    write(root/'SMOKE.json',result);print(json.dumps(result))


def run_one(index, *, prepared=None, root_override=None, plan_path=None,
            extra_files=None, extra_instruction='', condition='ordinary_workflow',
            evaluation_task=None, checkpoint=None):
    api,plan,task=prepared if prepared is not None else task_at(index)
    root=Path(root_override) if root_override is not None else ROOT/f'dev{index}'/'ordinary_workflow_v2'
    root.mkdir(parents=True,exist_ok=False)
    allowed={'experience.txt','program.py','continuation_program.py','continuation_client.py','program_memory.json'}
    if extra_files is not None and (type(extra_files) is not dict or not set(extra_files)<=allowed
            or any(type(v) is not bytes for v in extra_files.values())):
        raise ValueError('only explicit public experience/program payloads may enter the actor')
    write(root/'reservation.json',dict(plan_sha256=sha(plan_path or ROOT/'PLAN.json'),
        code_sha256=sha(__file__),task_id=task.id,kind='development '+condition))
    key=sys.stdin.readline().rstrip('\r\n')
    if not key:raise ValueError('missing stdin credential')
    # Reuse the existing owned Docker/OpenCode guest and read-only runtime.
    path=REPO/'research/agent_frontier_portfolio_20261029/run_alfworld_actor_20261106.py'
    spec=importlib.util.spec_from_file_location('owned_actor',path);actor=importlib.util.module_from_spec(spec);spec.loader.exec_module(actor)
    work=root/'work';work.mkdir();world_dir=actor.socket_directory('e');model_dir=actor.socket_directory('m')
    image=subprocess.check_output(['docker','image','inspect',actor.IMAGE,'--format','{{.Id}}'],text=True).strip()
    assert sha(actor.BINARY)==actor.BINARY_SHA
    # Validate all inherited path/runtime assets before the first user request.
    manifest=dict(uid=os.getuid(),gid=os.getgid(),model_id=MODEL,image_id=image)
    probe=actor.docker_command(work,world_dir,model_dir,manifest,'fccl-tau2-preflight-'+str(os.getpid()))
    probe=probe[:-4]+['-c',"import os,socket,pathlib,sys; assert os.getuid()!=0 and os.access('/workspace',os.W_OK) and not pathlib.Path('/home/testuser/wzh/research_evidence').exists();print(sys.version)"]
    preflight=subprocess.run(probe,capture_output=True,text=True,timeout=30)
    write(root/'zero_model_runtime.json',dict(argv=probe,exit=preflight.returncode,stdout=preflight.stdout,stderr=preflight.stderr,model_calls=0))
    preflight.check_returncode()
    provider=Provider(key,root,plan);del key
    env,agent,world,thread=make_world(api,task,provider,root,plan,evaluation_task=evaluation_task)
    (world_dir/'client.py').write_text(CLIENT)
    public_tools=[t.openai_schema for t in env.get_tools()]
    (work/'tools.json').write_text(json.dumps(public_tools,ensure_ascii=False,indent=2))
    (work/'policy.txt').write_text(env.get_policy())
    guest=actor.GUEST.replace('alfworld-no-history','telecom-workflow-development')
    if plan.get('continue_unfinished_once'):
        continuation=r'''
if result.returncode==0:
 try:
  s=socket.socket(socket.AF_UNIX);s.settimeout(10);s.connect('/world/s');s.sendall(b'{"op":"observe"}\n');buf=b''
  while b'\n' not in buf:
   part=s.recv(65536)
   if not part:break
   buf+=part
  s.close();current=json.loads(buf)
 except Exception:current=None
 if current is not None and not current.get('done') and not current.get('error'):
  print(json.dumps({'type':'shared_continuation','count':1}),flush=True)
  reminder='Continue the same task from the current public observation using the actual world client. A final prose reply does not send a message to the customer. Preserve existing progress. Current public observation:\n'+json.dumps(current)
  result=subprocess.run(['/opt/opencode','run','--pure','--format','json','-m',sys.argv[1],'--continue',reminder],stdin=subprocess.DEVNULL)
raise SystemExit(result.returncode)
'''
        guest=guest.replace('raise SystemExit(result.returncode)',continuation)
    (work/'guest.py').write_text(guest)
    for name,raw in (extra_files or {}).items():
        with (work/name).open('xb') as f:f.write(raw)
    profile=dict(model_id=MODEL,context=262144,output=8192)
    cfg=actor.config(profile,0);cfg['agent']['build'].pop('seed',None)
    (work/'opencode.json').write_text(json.dumps(cfg))
    current={'value':agent.observations.get(timeout=120),'pending':True}
    if checkpoint is not None:
        observed=dict(agent_db=env.get_db_hash(),user_db=env.get_user_db_hash(),
            public_sha256=hashlib.sha256(json.dumps(current['value']['messages'],ensure_ascii=False,separators=(',',':')).encode()).hexdigest())
        if observed!=checkpoint:
            raise ValueError('reconstructed world or public prefix differs from the frozen checkpoint')
        write(root/'checkpoint_verified.json',observed)
    class WorldHandler(socketserver.StreamRequestHandler):
        def handle(self):
            try:
                raw=self.rfile.readline(65537)
                if len(raw)>65536 or not raw.endswith(b'\n'):raise ValueError('invalid request')
                cmd=json.loads(raw)
                if cmd=={'op':'observe'}:result=current['value']
                else:
                    validate_action(cmd,current['value'],public_tools)
                    agent.actions.put(cmd); result=agent.observations.get(timeout=max(.01,provider.deadline-time.monotonic()))
                    current['value']=result
                self.wfile.write(json.dumps(result,ensure_ascii=False).encode()+b'\n')
            except BaseException:
                self.wfile.write(b'{"error":"invalid_or_failed_operation"}\n')
    class RelayHandler(http.server.BaseHTTPRequestHandler):
        def log_message(self,*args):pass
        def do_POST(self):
            try:
                size=int(self.headers.get('Content-Length',0))
                if not 0<size<=8*1024**2:raise ValueError('request size')
                value=json.loads(self.rfile.read(size))
                tools=value.get('tools',[])
                if len(tools)!=1 or tools[0].get('function',{}).get('name')!='bash':raise ValueError('unexpected actor tools')
                tools[0]['function']['description']='Execute a shell command in the isolated task workspace. Use the supplied world client for real interactions.'
                value['model']=MODEL;value['stream_options']={'include_usage':True}
                raw,ctype=provider.call(value,'actor')
                self.send_response(200);self.send_header('Content-Type',ctype);self.send_header('Content-Length',str(len(raw)));self.send_header('Connection','close');self.end_headers();self.wfile.write(raw)
            except BaseException as exc:
                with (root/'relay_errors.jsonl').open('a') as f:f.write(json.dumps(dict(type=type(exc).__name__,message=str(exc)))+'\n')
                self.send_error(403,'episode or request limit')
    world_server=socketserver.UnixStreamServer(str(world_dir/'s'),WorldHandler)
    model_server=socketserver.UnixStreamServer(str(model_dir/'s'),RelayHandler)
    for server in (world_server,model_server):threading.Thread(target=server.serve_forever,daemon=True).start()
    prompt=('Complete the telecom support interaction using the actual world. The full official policy is in /workspace/policy.txt and legal assistant tool schemas in /workspace/tools.json; read both. '
            'Use Bash to invoke /runtime/bin/python -B /world/client.py with one JSON argument. First {"op":"observe"}; then one {"op":"act","turn":CURRENT_TURN,"name":TOOL_NAME,"arguments":OBJECT} per returned observation. '
            'To speak to the customer, use name="say", arguments={"message":"your words"}. The customer simulator performs its own actions; you cannot call customer-only tools. '
            'Read actual responses, retain reported progress, and follow the workflow at the appropriate current step. Continue until done=true, then give a short final response. No other environment, reset or status API exists. '
            'A normal final answer alone does not interact with the customer.\nInitial public observation:\n'+json.dumps(current['value'],ensure_ascii=False))
    if extra_instruction:prompt+='\n'+extra_instruction
    (work/'task.txt').write_text(prompt)
    name='fccl-tau2-dev'+str(index)+'-'+str(os.getpid())
    argv=actor.docker_command(work,world_dir,model_dir,manifest,name)
    write(root/'actor_manifest.json',dict(argv=argv,image=image,opencode_sha256=sha(actor.BINARY),prompt_sha256=sha(work/'task.txt'),policy_sha256=sha(work/'policy.txt'),tools_sha256=sha(work/'tools.json'),
        extra_sha256={n:hashlib.sha256(v).hexdigest() for n,v in (extra_files or {}).items()},private_task_mounted=False))
    try:
        with (root/'actor.raw.jsonl').open('xb') as out,(root/'actor.stderr').open('xb') as err:
            run=subprocess.run(argv,stdout=out,stderr=err,timeout=max(1,provider.deadline-time.monotonic()+5))
        code=run.returncode
    except subprocess.TimeoutExpired:code='TIMEOUT'
    finally:
        subprocess.run(['docker','rm','-f',name],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        if thread.is_alive():agent.actions.put(None)
        thread.join(timeout=65)
        for server in (world_server,model_server):server.shutdown();server.server_close()
        provider.budget.close()
        actor.cleanup_directory(world_dir);actor.cleanup_directory(model_dir)
    rows=provider.budget.rows;charged=[r for r in rows if r['state']!='not_sent']
    result=dict(task_id=task.id,actor_exit=code,counts=provider.counts,physical_posts=len(charged),
                known_tokens=sum(r.get('usage',{}).get('total_tokens',0) for r in charged),
                unknown=sum('usage' not in r for r in charged),world_thread_alive=thread.is_alive(),
                phase='development '+condition)
    write(root/'RESULT.json',result);print(json.dumps(result))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['prepare','qualify','smoke','run']);p.add_argument('--index',type=int,default=0)
    args=p.parse_args()
    if args.mode=='prepare':prepare()
    elif args.mode=='qualify':qualify(args.index)
    elif args.mode=='smoke':smoke(args.index)
    else:run_one(args.index)
