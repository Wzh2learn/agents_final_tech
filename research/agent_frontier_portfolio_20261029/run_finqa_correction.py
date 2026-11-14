"""Finite FinQA development episodes using the existing isolated OpenCode runner.

Prepare selects train reports without model outcomes. Run owns its local model;
gold labels stay outside all student mounts. Existing histories are untouched.
"""
from __future__ import annotations

import argparse
import hashlib
import http.client
import json
import os
from pathlib import Path
import shutil
import socket
import socketserver
import subprocess
import sys
import tempfile
import threading
import time
import traceback

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path[:0] = [str(HERE), str(REPO)]
import finqa_correction as task
import run_contextbench_source as core

PRIVATE = Path('/home/testuser/wzh/research_evidence/agent_learning_20261030')
ROOT = PRIVATE / 'finqa_correction_v1'
DATA = Path('/home/testuser/wzh/phase1a_staging_20260925/finqa/train.json')
PARENT = PRIVATE / 'alfworld_text_qualification_20261106/context_study_v1/learning_comparison_v1/gguf_conversion_v1/hf_parent_bf16_v1/Qwen3-8B-HF-BOUND-BF16.gguf'
SERVER = Path('/home/testuser/.lmstudio/extensions/backends/llama.cpp-linux-arm64-nvidia-cuda13-2.16.0/llama-server')
MODEL = dict(host='127.0.0.1', port=18104, model_id='qwen3-8b-qual', context=32768, output=8192)
CAPS = dict(posts=12, seconds=300, combined_wire_bytes=16*1024**2)


def sha(path):
    return core.sha(Path(path))


def new(path, value):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    core.new(Path(path), value)


def publish(path, value):
    temp = Path(path).with_suffix('.tmp')
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n')
    temp.replace(path)


def prompt(public):
    return ('Solve this financial question from its supplied report. Submit a FinQA program using the only bash tool. '
            'Run /extra/bin/python /inputs/finqa_tool.py --program followed by one quoted program string. '
            'This executes the program and saves the latest submission; repair it if the returned execution indicates an error. '
            'Then finish with a short explanation. Do not edit files in /inputs. The tool never reports answer correctness. '
            'Allowed operators: add, subtract, multiply, divide, exp, greater, table_sum, table_average, table_max, table_min. '
            'Steps have two arguments and are separated by commas; #0 references step zero. Numbers may use commas/percent signs; '
            'const_100 denotes 100 and const_m1 denotes -1. For table operations use the exact row label and none as the second argument. '
            'Example tool command: /extra/bin/python /inputs/finqa_tool.py --program "add(10, 5), divide(#0, const_100)". '
            'Use the program execution value as the answer; do not invent an independent answer field.\n\n'
            + json.dumps(public, ensure_ascii=False))


def prepare(count=8):
    if not 1 <= count <= 24:
        raise ValueError('finite development sample required')
    if ROOT.exists():
        raise ValueError('existing development batch; inspect it instead of overwriting')
    if sha(DATA) != '49f237eb9779b569473b26b08048867d04635a7cc39ad6a7a5664c55bb428db6':
        raise ValueError('FinQA train source changed')
    records = json.loads(DATA.read_text())
    # Multi-step training questions expose correction dependencies; no model-result filtering.
    eligible = [r for r in records if len(task.executor().parse_program(r['qa']['program'])) >= 2]
    eligible.sort(key=lambda r: hashlib.sha256(('finqa-correction-v1|'+r['filename']+'|'+r['id']).encode()).hexdigest())
    chosen, reports = [], set()
    for record in eligible:
        if record['filename'] in reports:
            continue
        chosen.append(record); reports.add(record['filename'])
        if len(chosen) == count:
            break
    if len(chosen) != count:
        raise ValueError('not enough distinct reports')
    ROOT.mkdir(mode=0o700)
    labels, episodes = [], []
    for index, record in enumerate(chosen):
        public = task.public_record(record)
        folder = ROOT / 'student' / f'{index:03d}'
        (folder/'inputs').mkdir(parents=True)
        (folder/'work').mkdir(mode=0o755)
        (folder/'inputs/public.json').write_text(json.dumps(public, ensure_ascii=False)+'\n')
        (folder/'inputs/task.txt').write_text(prompt(public))
        (folder/'inputs/finqa_tool.py').write_bytes(Path(task.__file__).read_bytes())
        (folder/'inputs/executor.py').write_bytes(Path(task.executor().__file__).read_bytes())
        (folder/'inputs/guest.py').write_text(core.GUEST)
        # No application deps are required; reuse the verified stdlib runtime only.
        (folder/'dependencies').mkdir()
        labels.append(dict(index=index, id=record['id'], report=record['filename'],
                           gold_program=record['qa']['program'], exe_ans=record['qa']['exe_ans']))
        episodes.append(dict(index=index, id=record['id'], report=record['filename'], folder=str(folder),
                             public_sha256=sha(folder/'inputs/public.json')))
    new(ROOT/'LABELS_PRIVATE.json', labels)
    plan = dict(schema='finqa_corrective_learning_development_v1', status='PREPARED',
                source={'path':str(DATA), 'sha256':sha(DATA), 'split':'train'},
                selection='sha256 order, >=2 gold program steps, one task per report; no result selection',
                episodes=episodes, model=MODEL, caps=CAPS, seed=17, temperature=.2,
                total_local_post_cap=count*CAPS['posts'], teacher_post_cap=count*CAPS['posts'],
                teacher_campus_token_cap=4_000_000,
                parent={'path':str(PARENT),'precision':'BF16','bytes':PARENT.stat().st_size},
                server={'path':str(SERVER),'sha256':sha(SERVER)},
                components={str(p):sha(p) for p in [Path(__file__),Path(task.__file__),Path(core.__file__),Path(task.executor().__file__)]},
                mechanism='Teacher recovery differences define changed steps and their #reference descendants; '
                          'compare token-mass-normalized extra weight versus uniform corrective SFT on identical trajectories.',
                baselines=['base Agent','ordinary success SFT','uniform recovery SFT','partial-mask adaptation',
                           'legality/loop rule','all-program weighting or shuffled-region ablation'],
                scope='Exposed TRAIN development, not held-out confirmation; select one concrete rule before expanding.',
                feedback='Public execution/errors only; answer correctness and teacher labels outside student mounts.')
    new(ROOT/'PLAN.json', plan)
    print(json.dumps({'status':'PREPARED','episodes':len(episodes),'plan_sha256':sha(ROOT/'PLAN.json')}))


def start_model():
    with socket.socket() as test:
        test.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        test.bind(('127.0.0.1', MODEL['port']))
    log = (ROOT/'model.log').open('xb')
    argv=[str(SERVER),'-m',str(PARENT),'--host','127.0.0.1','--port',str(MODEL['port']),
          '--alias',MODEL['model_id'],'-c','32768','-n','8192','-np','1','--no-context-shift',
          '--jinja','-ngl','999','--no-mmap']
    process=subprocess.Popen(argv,stdout=log,stderr=subprocess.STDOUT)
    proof=dict(pid=process.pid,argv=argv,health_gets=0)
    try:
        for _ in range(120):
            if process.poll() is not None:
                raise RuntimeError('owned research model exited')
            try:
                c=http.client.HTTPConnection('127.0.0.1',MODEL['port'],timeout=2)
                proof['health_gets']+=1;c.request('GET','/health');response=c.getresponse();response.read();c.close()
                if response.status==200:
                    new(ROOT/'MODEL_STARTED.json',proof)
                    return process,log
            except OSError:
                pass
            time.sleep(1)
        raise TimeoutError('owned model startup cap')
    except BaseException:
        process.terminate();process.wait(timeout=20);log.close()
        new(ROOT/'MODEL_START_FAILURE.json',proof)
        raise


def episode(ep, h, runtime, profile):
    folder=Path(ep['folder'])
    new(folder/'STARTED.json',{'pid':os.getpid(),'unix':time.time()})
    (folder/'inputs/opencode.json').write_text(json.dumps(h.actor.config(profile,17)))
    inputs=core.tree(folder/'inputs')
    bridge=Path(tempfile.mkdtemp(prefix='finqa-',dir='/tmp'));bridge.chmod(0o700)
    relay=core.Relay(folder,profile,h,deadline=time.monotonic()+CAPS['seconds'],caps=CAPS)
    class Server(socketserver.ThreadingUnixStreamServer):
        daemon_threads=False
        block_on_close=True
    class Handler(socketserver.BaseRequestHandler):
        def handle(self): relay.handle(self.request)
    server=Server(str(bridge/'s'),Handler);os.chmod(bridge/'s',0o600)
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    name='finqa-agent-'+str(os.getpid())+'-'+str(time.monotonic_ns())
    actor={'runtime':runtime['runtime'],'sites':{'default':str(folder/'dependencies')}}
    command=core.docker_command(folder,actor,bridge,profile,h,name)
    new(folder/'ACTOR_COMMAND.json',command)
    try:
        returned=core.run_owned(command,name,folder/'container.cid',folder/'raw.jsonl',folder/'actor.stderr',CAPS['seconds'])
    finally:
        relay.close();server.shutdown();server.server_close()
        (bridge/'s').unlink();bridge.rmdir()
    accounting=relay.accounting()
    if core.tree(folder/'inputs')!=inputs:
        raise RuntimeError('read-only inputs changed')
    program=None
    candidate=folder/'work/candidate.json'
    if candidate.exists():
        value=json.loads(candidate.read_text())
        if isinstance(value,dict) and set(value)=={'program'}:program=value['program']
    gold=json.loads((ROOT/'LABELS_PRIVATE.json').read_text())[ep['index']]
    result=task.grade(program,json.loads((folder/'inputs/public.json').read_text()),gold['exe_ans'])
    result.update(index=ep['index'],id=ep['id'],actor=returned,accounting=accounting,
                  agent_completed=returned.get('exit')==0,
                  submitted_program=program,inputs=inputs)
    result['native_success']=result['execution_correct'] and result['agent_completed']
    new(folder/'RESULT.json',result)
    return result


def run(digest):
    if sha(ROOT/'PLAN.json')!=digest or (ROOT/'LIVE.json').exists():
        raise ValueError('wrong plan or already started batch')
    plan=json.loads((ROOT/'PLAN.json').read_text())
    for path,value in plan['components'].items():
        if sha(path)!=value:raise ValueError('component changed: '+path)
    h=core.helpers();runtime=h.deps.verify_projection(h.actor.RUNTIME_ROOT,h.actor.RUNTIME_SHA)
    if not (Path(runtime['runtime'])/'bin/python').exists():raise ValueError('actor runtime missing')
    state=dict(status='RUNNING',pid=os.getpid(),plan_sha256=digest,episodes=[],training=0,campus_posts=0)
    process=log=None
    publish(ROOT/'LIVE.json',state)
    try:
        with core.resource_lock():
            process,log=start_model()
            for ep in plan['episodes']:
                result=episode(ep,h,runtime,MODEL)
                state['episodes'].append(result);publish(ROOT/'LIVE.json',state)
                print(json.dumps({'index':ep['index'],'correct':result['execution_correct'],
                                  'completed':result['agent_completed'],
                                  'posts':result['accounting']['actual_forwarded_posts'],
                                  'tokens':result['accounting']['provider_total_tokens_known']}),flush=True)
                if not result['accounting']['integrity_passed']:
                    state['status']='STOPPED_INTERFACE';break
            else:
                state['status']='STUDENT_BATCH_RETURNED'
    except BaseException:
        state.update(status='FAILED',error=traceback.format_exc())
        raise
    finally:
        if process is not None:
            process.terminate()
            try:process.wait(timeout=20)
            except subprocess.TimeoutExpired:process.kill();process.wait()
            log.close()
        state['owned_model_stopped']=process is None or process.poll() is not None
        publish(ROOT/'LIVE.json',state);new(ROOT/'RESULT.json',state)


def prepare_teacher(backend='fp8', attempt=1):
    """Continue actual student workspaces; references are privileged train labels."""
    source=json.loads((ROOT/'RESULT.json').read_text())
    if source['status']!='STUDENT_BATCH_RETURNED' or not source['owned_model_stopped']:
        raise ValueError('student collector must be terminal and its model stopped')
    if backend not in ('fp8','gguf') or attempt<1:raise ValueError('teacher backend/attempt')
    target=ROOT/f'teacher_v{attempt}';target.mkdir()
    labels=json.loads((ROOT/'LABELS_PRIVATE.json').read_text())
    original=json.loads((ROOT/'PLAN.json').read_text())
    episodes=[]
    profile=dict(host='127.0.0.1',port=18105,model_id='qwen38-27b-fp8',context=32768,output=8192)
    if backend=='gguf':profile['model_id']='qwen36-35b-q4'
    for result in source['episodes']:
        if result['native_success']:continue
        index=result['index'];label=labels[index];old=Path(original['episodes'][index]['folder'])
        core.tree(old/'work')  # Reject links/special files before copying an actor output.
        folder=target/f'{index:03d}';folder.mkdir()
        shutil.copytree(old/'work',folder/'work')
        shutil.copytree(old/'dependencies',folder/'dependencies')
        shutil.copytree(old/'inputs',folder/'inputs')
        events=[json.loads(l) for l in (old/'raw.jsonl').read_text().splitlines() if l.startswith('{')]
        actions=[]
        for event in events:
            part=event.get('part',{})
            if part.get('type')=='tool':
                state=part.get('state',{})
                actions.append(dict(input=state.get('input'),output=state.get('output')))
        public=json.loads((folder/'inputs/public.json').read_text())
        text=(prompt(public)+'\n\nContinue the existing student workspace; the saved candidate, if any, is its real last submission. '
              'The following are actual failed student operations (last six) and their returned feedback. '
              'Fix the program and execute it with the same tool; finish after checking the execution. '
              'This is TRAIN-only teacher recovery. The reference below is training supervision, not online feedback. '
              'Programs use a flat sequence of two-argument steps, not nested function calls. '
              'Use shell single quotes around the program when row labels include punctuation.\n'
              +json.dumps({'student_actions':actions[-6:], 'training_reference_program':label['gold_program'],
                           'training_reference_execution_answer':label['exe_ans']},ensure_ascii=False))
        (folder/'inputs/task.txt').write_text(text)
        episodes.append(dict(index=index,id=label['id'],folder=str(folder),student_result_sha256=sha(old/'RESULT.json')))
    plan=dict(schema='finqa_train_teacher_recovery_v1',episodes=episodes,model=profile,caps=CAPS,backend=backend,
              parent_student_result_sha256=sha(ROOT/'RESULT.json'),max_posts=len(episodes)*CAPS['posts'],
              teacher='Local teacher recovery with train labels; exact backend below, new owned server only',
              model_root='/home/testuser/wzh/models/hf/Qwen3.8-27B-FP8',
              gguf='/home/testuser/.lmstudio/models/lmstudio-community/Qwen3.6-35B-A3B-GGUF/Qwen3.6-35B-A3B-Q4_K_M.gguf',
              image='sha256:734134467dc5b567845fdfc1cbe5b16e9761e3b6a059b35dc8de6d8147ac997f',
              template='/home/testuser/wzh/vllm_cache/qwen38_think_off_default.jinja',
              launcher=str(REPO/'scripts/vllm_probe_serve.sh'),
              components={str(p):sha(p) for p in [Path(__file__),Path(task.__file__),REPO/'scripts/vllm_probe_serve.sh']},
              budget='local teacher formation, separate from campus API and from deployment cost',
              scope='Privileged-label training recovery, not a blind strong-model task baseline or learned-method gain')
    new(target/'PLAN.json',plan)
    print(json.dumps({'teacher_episodes':len(episodes),'plan_sha256':sha(target/'PLAN.json')}))


def run_teacher(digest, attempt=1):
    target=ROOT/f'teacher_v{attempt}'
    if sha(target/'PLAN.json')!=digest or (target/'LIVE.json').exists():
        raise ValueError('wrong or already used teacher plan')
    plan=json.loads((target/'PLAN.json').read_text())
    for path,value in plan['components'].items():
        if sha(path)!=value:raise ValueError('teacher component changed')
    profile=plan['model'];h=core.helpers()
    runtime=h.deps.verify_projection(h.actor.RUNTIME_ROOT,h.actor.RUNTIME_SHA)
    state=dict(status='RUNNING',pid=os.getpid(),episodes=[],plan_sha256=digest,campus_posts=0,training=0)
    proc=log=None;name='finqa-teacher-'+str(os.getpid())
    try:
        with core.resource_lock():
            with socket.socket() as check:check.bind(('127.0.0.1',profile['port']))
            env=dict(os.environ,PORT='127.0.0.1:'+str(profile['port']),CONTAINER_NAME=name,
                     GMEM='0.30',MAXSEQS='1',MAXLEN=str(profile['context']),
                     KV_CACHE_MEMORY='4294967296',CHAT_TEMPLATE=plan['template'],
                     MODEL_DIR=plan['model_root'],VLLM_IMAGE=plan['image'])
            log=(target/'model.log').open('xb')
            if plan.get('backend','fp8')=='gguf':
                argv=[str(SERVER),'-m',plan['gguf'],'--host','127.0.0.1','--port',str(profile['port']),
                      '--alias',profile['model_id'],'-c','32768','-n','8192','-np','1',
                      '--no-context-shift','--jinja','-ngl','999','--no-mmap']
            else:argv=['bash',plan['launcher']]
            proc=subprocess.Popen(argv,cwd=REPO,env=env,stdout=log,stderr=subprocess.STDOUT)
            new(target/'MODEL_STARTED.json',dict(pid=proc.pid,argv=argv,backend=plan.get('backend','fp8'),
                container_name=name if plan.get('backend','fp8')=='fp8' else None,profile=profile,
                settings=({k:env[k] for k in ['PORT','GMEM','MAXSEQS','MAXLEN','KV_CACHE_MEMORY','MODEL_DIR','VLLM_IMAGE']}
                          if plan.get('backend','fp8')=='fp8' else {'gguf':plan['gguf']}),health_gets=0))
            publish(target/'LIVE.json',state)
            ready=False
            state['health_gets']=0
            for _ in range(480):
                if proc.poll() is not None:raise RuntimeError('owned teacher startup failed')
                try:
                    c=http.client.HTTPConnection('127.0.0.1',profile['port'],timeout=2)
                    state['health_gets']+=1
                    c.request('GET','/health');response=c.getresponse();response.read();c.close()
                    if response.status==200:ready=True;break
                except OSError:pass
                time.sleep(1)
            if not ready:raise TimeoutError('teacher startup timebox')
            for ep in plan['episodes']:
                result=episode(ep,h,runtime,profile);state['episodes'].append(result)
                publish(target/'LIVE.json',state)
                print(json.dumps({'index':ep['index'],'correct':result['execution_correct'],
                                  'posts':result['accounting']['actual_forwarded_posts'],
                                  'tokens':result['accounting']['provider_total_tokens_known']}),flush=True)
                if not result['accounting']['integrity_passed']:
                    state['status']='STOPPED_INTERFACE';break
            else:state['status']='TEACHER_RECOVERIES_RETURNED'
    except BaseException:
        state.update(status='FAILED',error=traceback.format_exc());raise
    finally:
        if proc is not None:
            # Exact owned name/image proof before any removal; no historic model is touched.
            inspected=subprocess.run(['docker','inspect','--format','{{.Id}} {{.Name}} {{.Image}}',name],capture_output=True,text=True)
            if inspected.returncode==0:
                cid,actual_name,image=inspected.stdout.strip().split()
                if actual_name!='/'+name or image!=plan['image']:
                    raise RuntimeError('teacher container ownership differs')
                (target/'container.cid').write_text(cid+'\n')
                state['model_cleanup']=core.stop_owned(target/'container.cid',name)
            if plan.get('backend')=='gguf' and proc.poll() is None:proc.terminate()
            try:proc.wait(timeout=20)
            except subprocess.TimeoutExpired:proc.terminate();proc.wait(timeout=20)
            log.close()
        state['owned_teacher_stopped']=proc is None or proc.poll() is not None
        publish(target/'LIVE.json',state);new(target/'RESULT.json',state)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('mode',choices=['prepare','run','prepare-teacher','teacher'])
    parser.add_argument('--count',type=int,default=8);parser.add_argument('--plan-sha')
    parser.add_argument('--teacher-backend',choices=['fp8','gguf'],default='fp8')
    parser.add_argument('--teacher-attempt',type=int,default=1)
    args=parser.parse_args()
    if args.mode=='prepare':prepare(args.count)
    elif args.mode=='run':run(args.plan_sha)
    elif args.mode=='prepare-teacher':prepare_teacher(args.teacher_backend,args.teacher_attempt)
    else:run_teacher(args.plan_sha,args.teacher_attempt)
