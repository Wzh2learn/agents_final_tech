"""Evaluate FinQA recovery LoRAs with the existing native OpenCode episode path."""
from __future__ import annotations

import argparse
import hashlib
import http.client
import json
import os
from pathlib import Path
import random
import shutil
import socket
import subprocess
import sys
import time
import traceback

HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(HERE),str(HERE.parents[1])]
import finqa_learning as learning
import finqa_correction as task
import run_finqa_correction as study

OUT=learning.ROOT/'native_v1'
CONVERTER=study.PRIVATE/'tools/llama_cpp/954de248ac6907dd05dc19f0f511ab18f2807a54/convert_lora_to_gguf.py'
CONFIG=study.PRIVATE/'alfworld_text_qualification_20261106/context_study_v1/learning_comparison_v1/gguf_conversion_v1/recovery_v4/BASE_CONFIG_ONLY'
ARMS=['frozen','uniform_recovery','operand_repair']


def read(path):return json.loads(Path(path).read_text())
def sha(path):return study.sha(path)


def prepare(count):
    if OUT.exists() or not 1<=count<=12:raise ValueError('finite new native attempt required')
    if read(learning.ROOT/'RESULT.json')['status']!='TRAINED_TWO_DEVELOPMENT_ARMS':
        raise ValueError('both trained adapters required')
    assert sha(study.DATA)=='49f237eb9779b569473b26b08048867d04635a7cc39ad6a7a5664c55bb428db6'
    excluded={x['report'] for x in read(study.ROOT/'LABELS_PRIVATE.json')}
    candidates=[r for r in read(study.DATA) if r['filename'] not in excluded
                and len(task.executor().parse_program(r['qa']['program']))>=2]
    candidates.sort(key=lambda r:hashlib.sha256(('finqa-native-v1|'+r['filename']+'|'+r['id']).encode()).hexdigest())
    selected=[]
    for record in candidates:
        if record['filename'] in excluded:continue
        selected.append(record);excluded.add(record['filename'])
        if len(selected)==count:break
    if len(selected)!=count:raise ValueError('insufficient distinct new reports')
    OUT.mkdir(mode=0o700)
    labels=[dict(index=i,id=r['id'],report=r['filename'],exe_ans=r['qa']['exe_ans']) for i,r in enumerate(selected)]
    study.new(OUT/'LABELS_PRIVATE.json',labels)
    arm_order=list(ARMS);random.Random(17).shuffle(arm_order);episodes=[]
    for arm in arm_order:
        for index,record in enumerate(selected):
            folder=OUT/arm/f'{index:03d}';inputs=folder/'inputs';inputs.mkdir(parents=True)
            (folder/'work').mkdir(mode=0o755);(folder/'dependencies').mkdir()
            public=task.public_record(record)
            (inputs/'public.json').write_text(json.dumps(public,ensure_ascii=False)+'\n')
            (inputs/'task.txt').write_text(study.prompt(public))
            (inputs/'finqa_tool.py').write_bytes(Path(task.__file__).read_bytes())
            (inputs/'executor.py').write_bytes(Path(task.executor().__file__).read_bytes())
            (inputs/'guest.py').write_text(study.core.GUEST)
            episodes.append(dict(arm=arm,index=index,id=record['id'],report=record['filename'],folder=str(folder),
                                 public_sha256=sha(inputs/'public.json'),task_sha256=sha(inputs/'task.txt')))
    plan=dict(schema='finqa_native_lora_development_v1',episodes=episodes,arm_order=arm_order,
              scope='New reports relative to this pilot, TRAIN-only development; not independent benchmark confirmation',
              selection='Fixed hash order before outcomes, >=2 reference steps, one task per report, excludes all eight formation reports',
              source_sha256=sha(study.DATA),training_result_sha256=sha(learning.ROOT/'RESULT.json'),
              arms=ARMS,seed=17,caps=study.CAPS,max_posts=count*len(ARMS)*study.CAPS['posts'],
              sampling=dict(temperature=.2,context=32768,output=8192),
              converter=str(CONVERTER),converter_sha256=sha(CONVERTER),base_config=str(CONFIG),
              parent=str(study.PARENT),parent_sha256='505618debb4e6ff112a8724f22853f09d4a6dd7ba0e32123d404fe9a4da8f5e3',
              server=str(study.SERVER),server_sha256=sha(study.SERVER),
              components={str(p):sha(p) for p in [Path(__file__),Path(study.__file__),Path(task.__file__),Path(study.core.__file__)]},
              comparison='Same public tasks, native harness, budgets, student base, sampling; only trained adapter differs',
              interpretation='Whole-agent execution accuracy and cost; valid-program accuracy separates format from arithmetic progress. No gold-based deployment trigger.')
    snapshot=OUT/'executed_sources';snapshot.mkdir()
    for name in plan['components']: (snapshot/Path(name).name).write_bytes(Path(name).read_bytes())
    study.new(OUT/'PLAN.json',plan)
    print(json.dumps(dict(plan_sha256=sha(OUT/'PLAN.json'),tasks=count,episodes=len(episodes),max_posts=plan['max_posts'])))


def convert(plan,arm):
    if arm=='frozen':return None
    source=learning.ROOT/arm
    receipt=read(learning.ROOT/'RESULT.json')['arms'][arm]
    for name,digest in receipt['adapter_files'].items():
        if sha(source/name)!=digest:raise ValueError('adapter changed')
    target=OUT/arm/'adapter.gguf'
    env=dict(os.environ,CUDA_VISIBLE_DEVICES='',HF_HUB_OFFLINE='1',PYTHONDONTWRITEBYTECODE='1',
             PYTHONPATH=str(CONVERTER.parent/'gguf-py')+':'+str(CONVERTER.parent))
    argv=[str(study.REPO/'venv/bin/python'),'-B',str(CONVERTER),'--outtype','f32','--base',plan['base_config'],
          '--outfile',str(target),str(source)]
    started=time.monotonic()
    result=subprocess.run(argv,capture_output=True,timeout=180,env=env)
    (OUT/arm/'conversion.stdout').write_bytes(result.stdout);(OUT/arm/'conversion.stderr').write_bytes(result.stderr)
    study.new(OUT/arm/'CONVERSION.json',dict(argv=argv,exit=result.returncode,seconds=time.monotonic()-started,
                  output_sha256=sha(target) if target.exists() else None))
    if result.returncode:raise RuntimeError('adapter conversion failed: '+arm)
    return target


def start_server(plan,arm,lora):
    with socket.socket() as sock:
        sock.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1);sock.bind(('127.0.0.1',18104))
    log=(OUT/arm/'server.log').open('xb')
    argv=[plan['server'],'-m',plan['parent'],'--host','127.0.0.1','--port','18104','--alias','qwen3-8b-qual',
          '-c','32768','-n','8192','-np','1','--no-context-shift','--jinja','-ngl','999','--no-mmap']
    if lora is not None:argv+=['--lora',str(lora)]
    process=subprocess.Popen(argv,stdout=log,stderr=subprocess.STDOUT)
    proof=dict(pid=process.pid,start_ticks=Path(f'/proc/{process.pid}/stat').read_text().split()[21],argv=argv,health_gets=0)
    try:
        for _ in range(120):
            if process.poll() is not None:raise RuntimeError('owned native server exited')
            try:
                conn=http.client.HTTPConnection('127.0.0.1',18104,timeout=2)
                proof['health_gets']+=1;conn.request('GET','/health');r=conn.getresponse();r.read();conn.close()
                if r.status==200:
                    study.new(OUT/arm/'SERVER.json',proof);return process,log
            except OSError:pass
            time.sleep(1)
        raise TimeoutError('owned native server startup cap')
    except BaseException:
        study.new(OUT/arm/'SERVER_START_FAILURE.json',proof)
        stop_server(process,log);raise


def stop_server(process,log):
    if process.poll() is None:
        process.terminate()
        try:process.wait(timeout=20)
        except subprocess.TimeoutExpired:process.kill();process.wait()
    log.close()


def run(digest):
    if sha(OUT/'PLAN.json')!=digest or (OUT/'LIVE.json').exists():raise ValueError('native plan/attempt')
    plan=read(OUT/'PLAN.json')
    assert sha(learning.ROOT/'RESULT.json')==plan['training_result_sha256']
    assert sha(plan['converter'])==plan['converter_sha256']
    assert sha(plan['server'])==plan['server_sha256']
    assert sha(plan['parent'])==plan['parent_sha256']
    for name,value in plan['components'].items():
        if sha(name)!=value:raise ValueError('native component changed: '+name)
    state=dict(status='RUNNING',pid=os.getpid(),episodes=[],plan_sha256=digest,owned_model_stopped=True)
    started=time.monotonic();study.publish(OUT/'LIVE.json',state)
    try:
        with study.core.resource_lock():
            h=study.core.helpers();runtime=h.deps.verify_projection(h.actor.RUNTIME_ROOT,h.actor.RUNTIME_SHA)
            for arm in plan['arm_order']:
                lora=convert(plan,arm);process=None;log=None
                try:
                    process,log=start_server(plan,arm,lora);state['owned_model_stopped']=False
                    for ep in plan['episodes']:
                        if ep['arm']!=arm:continue
                        folder=Path(ep['folder'])
                        assert sha(folder/'inputs/public.json')==ep['public_sha256']
                        assert sha(folder/'inputs/task.txt')==ep['task_sha256']
                        result=study.episode(ep,h,runtime,study.MODEL,private_labels=OUT/'LABELS_PRIVATE.json')
                        result['arm']=arm;state['episodes'].append(result)
                        study.publish(OUT/'LIVE.json',state)
                        print(json.dumps(dict(arm=arm,index=ep['index'],correct=result['execution_correct'],
                                              posts=result['accounting']['actual_forwarded_posts'])),flush=True)
                        if not result['accounting']['integrity_passed']:raise RuntimeError('native interface integrity')
                finally:
                    if process is not None:stop_server(process,log)
                    state['owned_model_stopped']=True;study.publish(OUT/'LIVE.json',state)
            state['status']='NATIVE_DEVELOPMENT_BATCH_RETURNED'
    except BaseException:
        state.update(status='FAILED',error=traceback.format_exc());raise
    finally:
        state['seconds']=time.monotonic()-started
        study.publish(OUT/'LIVE.json',state);study.new(OUT/'RESULT.json',state)


def prepare_strong():
    """Blind capability baseline on every preselected task, using the ready service."""
    target=OUT/'teacher27b_blind_v1'
    if target.exists():raise ValueError('strong-model attempt already exists')
    assert read(OUT/'RESULT.json')['status']=='NATIVE_DEVELOPMENT_BATCH_RETURNED'
    original=read(OUT/'PLAN.json');profile=dict(host='127.0.0.1',port=8006,model_id='qwen38-27b-fp8',context=32768,output=8192)
    target.mkdir(mode=0o700);episodes=[]
    for ep in original['episodes']:
        if ep['arm']!='frozen':continue
        folder=target/f"{ep['index']:03d}";folder.mkdir()
        shutil.copytree(Path(ep['folder'])/'inputs',folder/'inputs')
        (folder/'work').mkdir(mode=0o755);(folder/'dependencies').mkdir()
        episodes.append(dict(ep,arm='teacher27b_blind',folder=str(folder)))
    plan=dict(model=profile,episodes=episodes,caps=original['caps'],max_posts=len(episodes)*original['caps']['posts'],
              parent_plan_sha256=sha(OUT/'PLAN.json'),private_labels_sha256=sha(OUT/'LABELS_PRIVATE.json'),
              service='Existing research service; borrow it without restart or stop',
              scope='Post-hoc blind capability baseline, all four fixed development tasks; no reference programs or answers in inputs',
              components={str(p):sha(p) for p in [Path(__file__),Path(study.__file__),Path(task.__file__),Path(study.core.__file__)]})
    snapshot=target/'executed_sources';snapshot.mkdir()
    for path in plan['components']:(snapshot/Path(path).name).write_bytes(Path(path).read_bytes())
    study.new(target/'PLAN.json',plan)
    print(json.dumps(dict(plan_sha256=sha(target/'PLAN.json'),episodes=len(episodes),max_posts=plan['max_posts'])))


def run_strong(digest):
    target=OUT/'teacher27b_blind_v1'
    if sha(target/'PLAN.json')!=digest or (target/'LIVE.json').exists():raise ValueError('strong plan/attempt')
    plan=read(target/'PLAN.json')
    assert sha(OUT/'PLAN.json')==plan['parent_plan_sha256']
    assert sha(OUT/'LABELS_PRIVATE.json')==plan['private_labels_sha256']
    for name,value in plan['components'].items():
        if sha(name)!=value:raise ValueError('strong component changed')
    conn=http.client.HTTPConnection('127.0.0.1',8006,timeout=5)
    conn.request('GET','/v1/models');response=conn.getresponse();catalog=json.loads(response.read());conn.close()
    if response.status!=200 or plan['model']['model_id'] not in {m['id'] for m in catalog['data']}:
        raise ValueError('ready model identity differs')
    state=dict(status='RUNNING',pid=os.getpid(),episodes=[],plan_sha256=digest,service_borrowed=True)
    started=time.monotonic();study.publish(target/'LIVE.json',state)
    try:
        with study.core.resource_lock():
            h=study.core.helpers();runtime=h.deps.verify_projection(h.actor.RUNTIME_ROOT,h.actor.RUNTIME_SHA)
            for ep in plan['episodes']:
                folder=Path(ep['folder'])
                assert sha(folder/'inputs/public.json')==ep['public_sha256']
                assert sha(folder/'inputs/task.txt')==ep['task_sha256']
                value=study.episode(ep,h,runtime,plan['model'],private_labels=OUT/'LABELS_PRIVATE.json')
                state['episodes'].append(value);study.publish(target/'LIVE.json',state)
                print(json.dumps(dict(index=ep['index'],correct=value['execution_correct'],
                                      posts=value['accounting']['actual_forwarded_posts'])),flush=True)
                if not value['accounting']['integrity_passed']:raise RuntimeError('strong interface integrity')
            state['status']='BLIND_STRONG_MODEL_RETURNED'
    except BaseException:
        state.update(status='FAILED',error=traceback.format_exc());raise
    finally:
        state['seconds']=time.monotonic()-started
        study.publish(target/'LIVE.json',state);study.new(target/'RESULT.json',state)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['prepare','run','prepare-strong','strong']);p.add_argument('--count',type=int,default=4)
    p.add_argument('--plan-sha');a=p.parse_args()
    if a.mode=='prepare':prepare(a.count)
    elif a.mode=='prepare-strong':prepare_strong()
    elif a.mode=='strong':run_strong(a.plan_sha)
    else:run(a.plan_sha)
