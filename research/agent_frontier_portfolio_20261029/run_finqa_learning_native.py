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
from scripts.graph.research_gpu_guard import acquire_gpu_lease

OUT=learning.ROOT/'native_v1'
REVIEW=learning.REFINEMENT/'native_v1'
PAIRED_REVIEW=learning.PAIRED/'native_v1'
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


def convert(plan,arm,output_root=None):
    if arm=='frozen':return None
    training=Path(plan.get('training_root',str(learning.ROOT)))
    source=training/arm
    receipt=read(training/'RESULT.json')['arms'][arm]
    for name,digest in receipt['adapter_files'].items():
        if sha(source/name)!=digest:raise ValueError('adapter changed')
    output=OUT if output_root is None else Path(output_root)
    target=output/arm/'adapter.gguf'
    env=dict(os.environ,CUDA_VISIBLE_DEVICES='',HF_HUB_OFFLINE='1',PYTHONDONTWRITEBYTECODE='1',
             PYTHONPATH=str(CONVERTER.parent/'gguf-py')+':'+str(CONVERTER.parent))
    argv=[str(study.REPO/'venv/bin/python'),'-B',str(CONVERTER),'--outtype','f32','--base',plan['base_config'],
          '--outfile',str(target),str(source)]
    started=time.monotonic()
    result=subprocess.run(argv,capture_output=True,timeout=180,env=env)
    (output/arm/'conversion.stdout').write_bytes(result.stdout);(output/arm/'conversion.stderr').write_bytes(result.stderr)
    study.new(output/arm/'CONVERSION.json',dict(argv=argv,exit=result.returncode,seconds=time.monotonic()-started,
                  output_sha256=sha(target) if target.exists() else None))
    if result.returncode:raise RuntimeError('adapter conversion failed: '+arm)
    return target


def start_server(plan,arm,lora,output_root=None):
    allocation=acquire_gpu_lease()
    try:return _start_server_with_lease(plan,arm,lora,output_root,allocation)
    except BaseException:
        allocation.close();raise


def _start_server_with_lease(plan,arm,lora,output_root,allocation):
    output=OUT if output_root is None else Path(output_root)
    with socket.socket() as sock:
        sock.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1);sock.bind(('127.0.0.1',18104))
    log=(output/arm/'server.log').open('xb')
    argv=[plan['server'],'-m',plan['parent'],'--host','127.0.0.1','--port','18104','--alias','qwen3-8b-qual',
          '-c','32768','-n','8192','-np','1','--no-context-shift','--jinja','-ngl','999','--no-mmap']
    if 'server_seed' in plan:argv+=['--seed',str(plan['server_seed'])]
    if lora is not None:argv+=['--lora',str(lora)]
    process=subprocess.Popen(argv,stdout=log,stderr=subprocess.STDOUT)
    process.gpu_weights_lease=allocation
    proof=dict(pid=process.pid,start_ticks=Path(f'/proc/{process.pid}/stat').read_text().split()[21],argv=argv,health_gets=0)
    try:
        for _ in range(120):
            if process.poll() is not None:raise RuntimeError('owned native server exited')
            try:
                conn=http.client.HTTPConnection('127.0.0.1',18104,timeout=2)
                proof['health_gets']+=1;conn.request('GET','/health');r=conn.getresponse();r.read();conn.close()
                if r.status==200:
                    study.new(output/arm/'SERVER.json',proof);return process,log
            except OSError:pass
            time.sleep(1)
        raise TimeoutError('owned native server startup cap')
    except BaseException:
        study.new(output/arm/'SERVER_START_FAILURE.json',proof)
        stop_server(process,log);raise


def stop_server(process,log):
    if process.poll() is None:
        process.terminate()
        try:process.wait(timeout=20)
        except subprocess.TimeoutExpired:process.kill();process.wait()
    log.close()
    allocation=getattr(process,'gpu_weights_lease',None)
    if allocation is not None:allocation.close()


def expected_episode_deadline(accounting):
    failures=accounting.get('failures',[])
    return (accounting.get('uncertain_partial_sends')==0 and bool(failures)
            and all(f.get('type')=='TimeoutError' and f.get('message')=='episode deadline' for f in failures))


def run(digest,out=None):
    output=OUT if out is None else Path(out)
    if sha(output/'PLAN.json')!=digest or (output/'LIVE.json').exists():raise ValueError('native plan/attempt')
    plan=read(output/'PLAN.json');training=Path(plan.get('training_root',str(learning.ROOT)))
    if 'protocol_path' in plan:assert sha(plan['protocol_path'])==plan['protocol_sha256']
    if 'training_result_sha256' in plan:assert sha(training/'RESULT.json')==plan['training_result_sha256']
    if 'training_plan_sha256' in plan:assert sha(training/'PLAN.json')==plan['training_plan_sha256']
    if 'required_training_status' in plan:assert read(training/'RESULT.json')['status']==plan['required_training_status']
    if 'private_labels_sha256' in plan:assert sha(output/'LABELS_PRIVATE.json')==plan['private_labels_sha256']
    for source in plan.get('source_episodes',[]):
        folder=Path(source['folder'])
        assert sha(folder/'RESULT.json')==source['result_sha256']
        assert study.core.tree(folder/'work')==source['work_tree']
    assert sha(plan['converter'])==plan['converter_sha256']
    assert sha(plan['server'])==plan['server_sha256']
    assert sha(plan['parent'])==plan['parent_sha256']
    for name,value in plan['components'].items():
        if sha(name)!=value:raise ValueError('native component changed: '+name)
    state=dict(status='RUNNING',pid=os.getpid(),episodes=[],plan_sha256=digest,owned_model_stopped=True,
               training_result_sha256=sha(training/'RESULT.json'))
    started=time.monotonic();study.publish(output/'LIVE.json',state)
    try:
        with study.core.resource_lock():
            h=study.core.helpers();runtime=h.deps.verify_projection(h.actor.RUNTIME_ROOT,h.actor.RUNTIME_SHA)
            for arm in plan['arm_order']:
                lora=convert(plan,arm,output);process=None;log=None
                try:
                    process,log=start_server(plan,arm,lora,output);state['owned_model_stopped']=False
                    for ep in plan['episodes']:
                        if ep['arm']!=arm:continue
                        folder=Path(ep['folder'])
                        assert sha(folder/'inputs/public.json')==ep['public_sha256']
                        assert sha(folder/'inputs/task.txt')==ep['task_sha256']
                        result=study.episode(ep,h,runtime,study.MODEL,private_labels=output/'LABELS_PRIVATE.json')
                        result['arm']=arm;state['episodes'].append(result)
                        study.publish(output/'LIVE.json',state)
                        print(json.dumps(dict(arm=arm,index=ep['index'],correct=result['execution_correct'],
                                              posts=result['accounting']['actual_forwarded_posts'])),flush=True)
                        if not result['accounting']['integrity_passed']:
                            if plan.get('episode_deadline_is_bounded_failure') and expected_episode_deadline(result['accounting']):
                                result['bounded_episode_deadline']=True;study.publish(output/'LIVE.json',state)
                            else:raise RuntimeError('native interface integrity')
                finally:
                    if process is not None:stop_server(process,log)
                    state['owned_model_stopped']=True;study.publish(output/'LIVE.json',state)
            state['status']=plan.get('terminal_status','NATIVE_DEVELOPMENT_BATCH_RETURNED')
    except BaseException:
        state.update(status='FAILED',error=traceback.format_exc());raise
    finally:
        state['seconds']=time.monotonic()-started
        study.publish(output/'LIVE.json',state);study.new(output/'RESULT.json',state)


def prepare_paired_review():
    """Reuse all four actual first-pass states, without regenerating or filtering."""
    target=PAIRED_REVIEW
    if target.exists():raise ValueError('paired review attempt already exists')
    parent=learning.ROOT/'refinement_v2/native_v1'
    original=read(parent/'PLAN.json');source=read(parent/'RESULT.json')['source']
    if len(source)!=4:raise ValueError('complete common first-pass source required')
    arms=list(read(learning.PAIRED/'PLAN.json')['arms']);random.Random(17).shuffle(arms)
    target.mkdir(mode=0o700);shutil.copyfile(parent/'LABELS_PRIVATE.json',target/'LABELS_PRIVATE.json')
    episodes=[];sources=[]
    for ep in original['source_episodes']:
        folder=Path(ep['folder']);study.core.tree(folder/'work')
        text=study.recovery_prompt(read(folder/'inputs/public.json'),study.recent_actions(folder))
        if text!=(parent/'ordinary_review'/f"{ep['index']:03d}"/'inputs/task.txt').read_text():
            raise ValueError('the fixed public review packet changed')
        sources.append(dict(ep,result_sha256=sha(folder/'RESULT.json'),work_tree=study.core.tree(folder/'work')))
        for arm in arms:
            output=target/arm/f"{ep['index']:03d}";output.mkdir(parents=True)
            shutil.copytree(folder/'inputs',output/'inputs');shutil.copytree(folder/'work',output/'work')
            (output/'dependencies').mkdir();(output/'inputs/task.txt').write_text(text)
            episodes.append(dict(ep,arm=arm,folder=str(output),task_sha256=sha(output/'inputs/task.txt'),
                                 source_result_sha256=sha(folder/'RESULT.json')))
    plan=dict(schema='finqa_paired_decision_native_review_v1',episodes=episodes,arm_order=arms,arms=arms,
              training_root=str(learning.PAIRED),training_plan_sha256=sha(learning.PAIRED/'PLAN.json'),
              required_training_status='TRAINED_PAIRED_DECISION_ARMS',terminal_status='FINQA_PAIRED_REVIEW_RETURNED',
              parent_review_plan_sha256=sha(parent/'PLAN.json'),source_episodes=sources,
              private_labels_sha256=sha(target/'LABELS_PRIVATE.json'),caps=study.CAPS,max_posts=4*len(arms)*study.CAPS['posts'],
              converter=str(CONVERTER),converter_sha256=sha(CONVERTER),base_config=str(CONFIG),
              parent=str(study.PARENT),parent_sha256=original['parent_sha256'],server=str(study.SERVER),server_sha256=sha(study.SERVER),
              components={str(p):sha(p) for p in [Path(__file__),Path(study.__file__),Path(task.__file__),Path(study.core.__file__)]},
              episode_deadline_is_bounded_failure=True,local_unknown_usage_reserve_per_request=32768,
              scope='Post-hoc development regression on the same four exposed reports; no independent confirmation claim',
              comparison='Same real first-pass workspaces, public review requests, actor, model, caps and private scoring labels; adapter training objective differs',
              accounting='Charge the previously executed common first pass when reporting whole-agent cost; do not bill it twice as a new physical run')
    new=study.new;new(target/'PLAN.json',plan)
    snapshot=target/'executed_sources';snapshot.mkdir()
    for path in plan['components']:(snapshot/Path(path).name).write_bytes(Path(path).read_bytes())
    print(json.dumps(dict(plan_sha256=sha(target/'PLAN.json'),episodes=len(episodes),arm_order=arms,max_posts=plan['max_posts'])))


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


def prepare_recovery():
    """Collect labelled TRAIN recoveries of the syntax-capable student's residuals."""
    target=OUT/'recovery_training_v1'
    if target.exists():raise ValueError('residual recovery attempt already exists')
    source=read(OUT/'RESULT.json');original=read(OUT/'PLAN.json')
    assert source['status']=='NATIVE_DEVELOPMENT_BATCH_RETURNED' and source['owned_model_stopped']
    records={r['id']:r for r in read(study.DATA)}
    target.mkdir(mode=0o700);episodes=[];labels=[]
    for result in source['episodes']:
        if result['arm']!='uniform_recovery':continue
        index=result['index'];ep=next(e for e in original['episodes'] if e['arm']=='uniform_recovery' and e['index']==index)
        parent=Path(ep['folder']);study.core.tree(parent/'work')
        folder=target/f'{index:03d}';folder.mkdir()
        shutil.copytree(parent/'inputs',folder/'inputs');shutil.copytree(parent/'work',folder/'work')
        (folder/'dependencies').mkdir()
        public=read(parent/'inputs/public.json');record=records[result['id']]
        labels.append(dict(index=index,id=record['id'],report=record['filename'],exe_ans=record['qa']['exe_ans']))
        reference=dict(training_reference_program=record['qa']['program'],training_reference_execution_answer=record['qa']['exe_ans'])
        text=(study.recovery_prompt(public,study.recent_actions(parent))+
              '\nTRAIN teacher formation only: use these provided labels to produce and execute a correct recovery. '
              'They will be removed from student conditioning.\n'+json.dumps(reference))
        (folder/'inputs/task.txt').write_text(text)
        episodes.append(dict(index=index,id=ep['id'],report=ep['report'],folder=str(folder),
                             source_folder=str(parent),source_result_sha256=sha(parent/'RESULT.json'),
                             public_sha256=sha(folder/'inputs/public.json'),task_sha256=sha(folder/'inputs/task.txt')))
    assert len(episodes)==4
    study.new(target/'LABELS_PRIVATE.json',labels)
    profile=dict(host='127.0.0.1',port=8006,model_id='qwen38-27b-fp8',context=32768,output=8192)
    plan=dict(model=profile,episodes=episodes,caps=original['caps'],max_posts=len(episodes)*original['caps']['posts'],
              parent_plan_sha256=sha(OUT/'PLAN.json'),private_labels_sha256=sha(target/'LABELS_PRIVATE.json'),
              private_labels_path=str(target/'LABELS_PRIVATE.json'),terminal_status='PRIVILEGED_RECOVERY_RETURNED',
              scope='TRAIN residual recovery formation on all four fixed source tasks, with reference labels; not blind capability or learned benefit',
              components={str(p):sha(p) for p in [Path(__file__),Path(study.__file__),Path(task.__file__),Path(study.core.__file__)]})
    snapshot=target/'executed_sources';snapshot.mkdir()
    for path in plan['components']:(snapshot/Path(path).name).write_bytes(Path(path).read_bytes())
    study.new(target/'PLAN.json',plan)
    print(json.dumps(dict(plan_sha256=sha(target/'PLAN.json'),episodes=len(episodes),max_posts=plan['max_posts'])))


def run_strong(digest, name='teacher27b_blind_v1', output_root=None):
    base=OUT if output_root is None else Path(output_root)
    target=base/name
    if sha(target/'PLAN.json')!=digest or (target/'LIVE.json').exists():raise ValueError('strong plan/attempt')
    plan=read(target/'PLAN.json')
    assert sha(base/'PLAN.json')==plan['parent_plan_sha256']
    if 'source_result_sha256' in plan:assert sha(base/'RESULT.json')==plan['source_result_sha256']
    for source in plan.get('source_episodes',[]):
        folder=Path(source['folder'])
        assert sha(folder/'RESULT.json')==source['result_sha256'] and study.core.tree(folder/'work')==source['work_tree']
    label_path=Path(plan.get('private_labels_path',str(base/'LABELS_PRIVATE.json')))
    assert sha(label_path)==plan['private_labels_sha256']
    for name,value in plan['components'].items():
        if sha(name)!=value:raise ValueError('strong component changed')
    conn=http.client.HTTPConnection('127.0.0.1',8006,timeout=5)
    conn.request('GET','/v1/models');response=conn.getresponse();catalog=json.loads(response.read());conn.close()
    if response.status!=200 or plan['model']['model_id'] not in {m['id'] for m in catalog['data']}:
        raise ValueError('ready model identity differs')
    state=dict(status='RUNNING',pid=os.getpid(),episodes=[],plan_sha256=digest,service_borrowed=True,
               role=plan.get('role','blind_strong_model'))
    started=time.monotonic();study.publish(target/'LIVE.json',state)
    try:
        with study.core.resource_lock():
            h=study.core.helpers();runtime=h.deps.verify_projection(h.actor.RUNTIME_ROOT,h.actor.RUNTIME_SHA)
            for ep in plan['episodes']:
                folder=Path(ep['folder'])
                assert sha(folder/'inputs/public.json')==ep['public_sha256']
                assert sha(folder/'inputs/task.txt')==ep['task_sha256']
                value=study.episode(ep,h,runtime,plan['model'],private_labels=label_path)
                state['episodes'].append(value);study.publish(target/'LIVE.json',state)
                print(json.dumps(dict(index=ep['index'],correct=value['execution_correct'],
                                      posts=value['accounting']['actual_forwarded_posts'])),flush=True)
                if not value['accounting']['integrity_passed']:
                    if plan.get('episode_deadline_is_bounded_failure') and expected_episode_deadline(value['accounting']):
                        value['bounded_episode_deadline']=True;study.publish(target/'LIVE.json',state)
                    else:raise RuntimeError('strong interface integrity')
            state['status']=plan.get('terminal_status','BLIND_STRONG_MODEL_RETURNED')
    except BaseException:
        state.update(status='FAILED',error=traceback.format_exc());raise
    finally:
        state['seconds']=time.monotonic()-started
        study.publish(target/'LIVE.json',state);study.new(target/'RESULT.json',state)


def prepare_review(count):
    """Freeze new reports and an unconditional, information-matched review loop."""
    if REVIEW.exists() or not 1<=count<=12:raise ValueError('new finite review attempt required')
    training=read(learning.REFINEMENT/'PLAN.json')
    excluded={r['report'] for r in read(study.ROOT/'LABELS_PRIVATE.json')}
    excluded.update(r['report'] for r in read(OUT/'LABELS_PRIVATE.json'))
    candidates=[r for r in read(study.DATA) if r['filename'] not in excluded
                and len(task.executor().parse_program(r['qa']['program']))>=2]
    candidates.sort(key=lambda r:hashlib.sha256(('finqa-review-v1|'+r['filename']+'|'+r['id']).encode()).hexdigest())
    selected=[]
    for record in candidates:
        if record['filename'] in excluded:continue
        selected.append(record);excluded.add(record['filename'])
        if len(selected)==count:break
    if len(selected)!=count:raise ValueError('insufficient distinct reports')
    REVIEW.mkdir(mode=0o700);episodes=[]
    labels=[dict(index=i,id=r['id'],report=r['filename'],exe_ans=r['qa']['exe_ans']) for i,r in enumerate(selected)]
    study.new(REVIEW/'LABELS_PRIVATE.json',labels)
    for index,record in enumerate(selected):
        folder=REVIEW/'source'/f'{index:03d}';inputs=folder/'inputs';inputs.mkdir(parents=True)
        (folder/'work').mkdir(mode=0o755);(folder/'dependencies').mkdir()
        public=task.public_record(record)
        (inputs/'public.json').write_text(json.dumps(public,ensure_ascii=False)+'\n')
        (inputs/'task.txt').write_text(study.prompt(public))
        (inputs/'finqa_tool.py').write_bytes(Path(task.__file__).read_bytes())
        (inputs/'executor.py').write_bytes(Path(task.executor().__file__).read_bytes())
        (inputs/'guest.py').write_text(study.core.GUEST)
        episodes.append(dict(index=index,id=record['id'],report=record['filename'],folder=str(folder),
                             public_sha256=sha(inputs/'public.json'),task_sha256=sha(inputs/'task.txt')))
    arms=['ordinary_review','uniform_recovery','all_operands','localized_fields']
    random.Random(17).shuffle(arms)
    warm=OUT/'uniform_recovery/adapter.gguf'
    assert sha(warm)==read(OUT/'uniform_recovery/CONVERSION.json')['output_sha256']
    plan=dict(schema='finqa_fixed_review_learning_development_v1',source_episodes=episodes,review_arms=arms,
              training_root=str(learning.REFINEMENT),training_plan_sha256=sha(learning.REFINEMENT/'PLAN.json'),
              caps=study.CAPS,max_posts=count*(1+len(arms))*study.CAPS['posts'],
              warm_gguf=str(warm),warm_gguf_sha256=sha(warm),
              converter=str(CONVERTER),converter_sha256=sha(CONVERTER),base_config=str(CONFIG),
              parent=str(study.PARENT),parent_sha256='505618debb4e6ff112a8724f22853f09d4a6dd7ba0e32123d404fe9a4da8f5e3',
              server=str(study.SERVER),server_sha256=sha(study.SERVER),seed=17,
              components={str(p):sha(p) for p in [Path(__file__),Path(study.__file__),Path(task.__file__),Path(study.core.__file__)]},
              selection='Fixed hash order before model outcomes; one TRAIN task per report, excludes all 12 earlier reports',
              scope='Report-disjoint development, not official held-out confirmation',
              deployment='One common first pass with saved syntax-capable uniform-v1 adapter, followed by exactly one review for ALL tasks, including correct ones',
              comparison='Ordinary review reuses the unchanged warm adapter; the three trained reviewers differ only in residual-field supervision',
              accounting='Report shared first-pass plus review cost per policy, conditional recovery and correct-source regression separately; count shared formation once')
    snapshot=REVIEW/'executed_sources';snapshot.mkdir()
    for path in plan['components']:(snapshot/Path(path).name).write_bytes(Path(path).read_bytes())
    study.new(REVIEW/'PLAN.json',plan)
    print(json.dumps(dict(plan_sha256=sha(REVIEW/'PLAN.json'),tasks=count,review_arms=arms,max_posts=plan['max_posts'])))


def select_report_disjoint(records,excluded,count,salt):
    """A page from an exposed company/year is not a new independent report."""
    if not 1<=count<=64:raise ValueError('finite report batch required')
    used=set(excluded);selected=[]
    ordered=sorted(records,key=lambda r:hashlib.sha256((salt+'|'+r['filename']+'|'+r['id']).encode()).hexdigest())
    for record in ordered:
        group=tuple(record['filename'].split('/')[:2])
        if group in used or len(task.executor().parse_program(record['qa']['program']))<2:continue
        selected.append(record);used.add(group)
        if len(selected)==count:return selected
    raise ValueError('insufficient distinct filing groups')


def expanded_runtime():
    return dict(converter=str(CONVERTER),converter_sha256=sha(CONVERTER),base_config=str(CONFIG),
                parent=str(study.PARENT),parent_sha256='505618debb4e6ff112a8724f22853f09d4a6dd7ba0e32123d404fe9a4da8f5e3',
                server=str(study.SERVER),server_sha256=sha(study.SERVER),server_seed=17,
                components={str(p):sha(p) for p in [Path(__file__),Path(study.__file__),Path(task.__file__),Path(study.core.__file__)]},
                caps=study.CAPS,sampling=dict(temperature=.2,context=32768,output=8192,server_seed=17),
                episode_deadline_is_bounded_failure=True,local_unknown_usage_reserve_per_request=32768)


def prepare_expanded_eval(count):
    """Freeze official-dev inputs before running any expanded-adapter outcome."""
    training=learning.ROOT/'semantic_correction_v1/expanded_v1';target=training/'dev_firstpass_v1'
    if target.exists():raise ValueError('expanded evaluation already frozen')
    selection=read(training.parent/'SELECTION.json');excluded=set()
    for path,digest in selection['exposure_files'].items():
        if sha(path)!=digest:raise ValueError('earlier exposure manifest changed')
        excluded.update(tuple(r['report'].split('/')[:2]) for r in read(path))
    for key in ('train','evaluation'):
        excluded.update(tuple(r['report'].split('/')[:2]) for r in selection[key])
    data=study.DATA.with_name('dev.json')
    if sha(data)!='a847fb7e0d61a3125a1e2909852df6b89f1ee64d2c5ff1bf689e332214deee51':
        raise ValueError('official dev source changed')
    records=select_report_disjoint(read(data),excluded,count,'finqa-expanded-dev-v1')
    for record in records:
        if not task.grade(record['qa']['program'],task.public_record(record),record['qa']['exe_ans'])['execution_correct']:
            raise ValueError('selected reference does not satisfy the declared executor')
    target.mkdir(mode=0o700);episodes=[]
    labels=[dict(index=i,id=r['id'],report=r['filename'],exe_ans=r['qa']['exe_ans']) for i,r in enumerate(records)]
    study.new(target/'LABELS_PRIVATE.json',labels)
    for i,record in enumerate(records):
        folder=target/'closed_sft'/f'{i:03d}';inputs=folder/'inputs';inputs.mkdir(parents=True)
        (folder/'work').mkdir(mode=0o755);(folder/'dependencies').mkdir()
        public=task.public_record(record)
        (inputs/'public.json').write_text(json.dumps(public,ensure_ascii=False)+'\n')
        (inputs/'task.txt').write_text(study.prompt(public))
        for name,path in [('finqa_tool.py',Path(task.__file__)),('executor.py',Path(task.executor().__file__))]:
            (inputs/name).write_bytes(path.read_bytes())
        (inputs/'guest.py').write_text(study.core.GUEST)
        episodes.append(dict(index=i,id=record['id'],report=record['filename'],arm='closed_sft',folder=str(folder),
                             public_sha256=sha(inputs/'public.json'),task_sha256=sha(inputs/'task.txt')))
    plan=dict(schema='finqa_expanded_official_dev_firstpass_v1',episodes=episodes,arm_order=['closed_sft'],
              training_root=str(training),training_plan_sha256=sha(training/'PLAN.json'),
              required_training_status='TRAINED_EXPANDED_SEMANTIC_ARMS',terminal_status='FINQA_EXPANDED_DEV_FIRSTPASS_RETURNED',
              private_labels_sha256=sha(target/'LABELS_PRIVATE.json'),source_split='dev',source_sha256=sha(data),
              selection_sha256=sha(training.parent/'SELECTION.json'),excluded_filing_groups=sorted('/'.join(g) for g in excluded),
              selection='Fixed hash order, >=2 reference operations, one task per company/year, excludes all 44 previously exposed filing groups; selected reference execution checked before model outcomes',
              scope='Model-unseen report-disjoint official-dev subset; historical CPU reference checks are not model exposure. This is a method-development comparison, not a final full-benchmark claim.',
              deployment='One common ordinary closed-SFT Agent first pass; subsequently review every state in all four arms without a hidden-answer trigger.',
              max_posts=count*study.CAPS['posts'],**expanded_runtime())
    study.new(target/'PLAN.json',plan);snapshot=target/'executed_sources';snapshot.mkdir()
    for path in plan['components']:(snapshot/Path(path).name).write_bytes(Path(path).read_bytes())
    print(json.dumps(dict(plan_sha256=sha(target/'PLAN.json'),tasks=count,excluded_groups=len(excluded),max_posts=plan['max_posts'])))


def prepare_expanded_review():
    """All trained reviewers continue the same public workspaces, including successes."""
    training=learning.ROOT/'semantic_correction_v1/expanded_v1';parent=training/'dev_firstpass_v1';target=training/'dev_review_v1'
    if target.exists():raise ValueError('expanded review already frozen')
    original=read(parent/'PLAN.json');first=read(parent/'RESULT.json')
    if first['status']!='FINQA_EXPANDED_DEV_FIRSTPASS_RETURNED' or len(first['episodes'])!=len(original['episodes']):
        raise ValueError('complete common first pass required')
    arms=list(read(training/'PLAN.json')['arms']);random.Random(17).shuffle(arms)
    target.mkdir(mode=0o700);shutil.copyfile(parent/'LABELS_PRIVATE.json',target/'LABELS_PRIVATE.json');episodes=[];sources=[]
    for ep in original['episodes']:
        folder=Path(ep['folder']);text=study.recovery_prompt(read(folder/'inputs/public.json'),study.recent_actions(folder))
        sources.append(dict(ep,result_sha256=sha(folder/'RESULT.json'),work_tree=study.core.tree(folder/'work')))
        for arm in arms:
            output=target/arm/f"{ep['index']:03d}";output.mkdir(parents=True)
            shutil.copytree(folder/'inputs',output/'inputs');shutil.copytree(folder/'work',output/'work')
            (output/'dependencies').mkdir();(output/'inputs/task.txt').write_text(text)
            episodes.append(dict(ep,arm=arm,folder=str(output),task_sha256=sha(output/'inputs/task.txt'),source_result_sha256=sha(folder/'RESULT.json')))
    plan=dict(schema='finqa_expanded_official_dev_review_v1',episodes=episodes,arm_order=arms,arms=arms,
              training_root=str(training),training_plan_sha256=sha(training/'PLAN.json'),training_result_sha256=sha(training/'RESULT.json'),
              required_training_status='TRAINED_EXPANDED_SEMANTIC_ARMS',terminal_status='FINQA_EXPANDED_DEV_REVIEW_RETURNED',
              source_episodes=sources,parent_plan_sha256=sha(parent/'PLAN.json'),private_labels_sha256=sha(target/'LABELS_PRIVATE.json'),
              max_posts=len(original['episodes'])*len(arms)*study.CAPS['posts'],
              scope=original['scope'],comparison='Identical real first-pass states, public feedback, actor, model, information and budgets; only the matched training rule differs.',
              accounting='Count the common first pass once physically and include it in each whole-policy cost. Report recovery, retention and native success separately.',**expanded_runtime())
    study.new(target/'PLAN.json',plan);snapshot=target/'executed_sources';snapshot.mkdir()
    for path in plan['components']:(snapshot/Path(path).name).write_bytes(Path(path).read_bytes())
    print(json.dumps(dict(plan_sha256=sha(target/'PLAN.json'),episodes=len(episodes),arm_order=arms,max_posts=plan['max_posts'])))


def reserved_confirmation_records(records,reservation,count=64):
    """Use the preselected order; never replace a filing after seeing outcomes."""
    if not 1<=count<=64 or reservation.get('status')!='RESERVED_NOT_EXECUTED':
        raise ValueError('inactive or unbounded confirmation reservation')
    tasks=reservation['tasks'];excluded=set(reservation['excluded_groups'])
    if len(tasks)!=count:raise ValueError('reserved task count differs')
    selected=[];ids=set();groups=set()
    for item in tasks:
        matches=[r for r in records if r['id']==item['id']]
        if len(matches)!=1 or matches[0]['filename']!=item['report']:
            raise ValueError('reserved task is missing, ambiguous or changed')
        record=matches[0];group='/'.join(record['filename'].split('/')[:2])
        if item['id'] in ids or group in groups or group in excluded:
            raise ValueError('duplicate or exposed confirmation filing')
        if len(task.executor().parse_program(record['qa']['program']))<2:
            raise ValueError('reserved task no longer satisfies the multi-step scope')
        selected.append(record);ids.add(item['id']);groups.add(group)
    return selected


def prepare_confirmation():
    """Freeze all four checkpoint comparisons before any of the 64 outcomes."""
    training=learning.ROOT/'semantic_correction_v1/expanded_v1';root=training/'confirmation_v1'
    if root.exists():raise ValueError('confirmation already prepared')
    reservation=training/'CONFIRMATION_RESERVATION_V1.json'
    if sha(reservation)!='2d6ae0670332732af53204a8e8713cfae4e76e4718cd0ecd3d36438663dac442':
        raise ValueError('pre-outcome reservation changed')
    reserved=read(reservation);data=study.DATA.with_name('dev.json')
    if sha(data)!=reserved['dev_source_sha256']:raise ValueError('dev source changed')
    records=reserved_confirmation_records(read(data),reserved)
    for record in records:
        if not task.grade(record['qa']['program'],task.public_record(record),record['qa']['exe_ans'])['execution_correct']:
            raise ValueError('reserved reference does not meet the executor contract; do not replace the task')
    bindings={}
    for name,folder,arms,status in [
        ('original',training,['closed_sft','edit_all_negative'],'TRAINED_EXPANDED_SEMANTIC_ARMS'),
        ('controls',training/'controls_v1/matched_training_v1',['success_context_sft','step_dpo'],'TRAINED_MATCHED_CONTROL_ARMS')]:
        receipt=read(folder/'RESULT.json')
        if receipt['status']!=status:raise ValueError('training incomplete')
        for arm in arms:
            for filename,digest in receipt['arms'][arm]['adapter_files'].items():
                if sha(folder/arm/filename)!=digest:raise ValueError('trained checkpoint changed')
        bindings[name]=dict(training_root=str(folder),training_plan_sha256=sha(folder/'PLAN.json'),
                            training_result_sha256=sha(folder/'RESULT.json'),required_training_status=status,arms=arms)
    jobs=[dict(name=name,arms=list(value['arms'])) for name,value in bindings.items()]
    rng=random.Random(17);rng.shuffle(jobs)
    for job in jobs:rng.shuffle(job['arms'])
    runtime=expanded_runtime();root.mkdir(mode=0o700)
    protocol=dict(schema='finqa_reserved_filing_validation_v1',reservation_path=str(reservation),reservation_sha256=sha(reservation),
                  source_sha256=sha(data),tasks=reserved['tasks'],excluded_groups=reserved['excluded_groups'],bindings=bindings,
                  review_jobs=jobs,primary='edit_all_negative minus closed_sft native success, paired by filing',
                  secondary='Success-context SFT, step-preference adaptation, source retention, valid-wrong recovery and complete costs; no selection on target labels.',
                  scope='64 new project-training/development-unseen company/year groups; fixed checkpoints and one inference seed. Not full-benchmark or pretraining-independence evidence.',
                  inference='One common closed-SFT first pass; all four reviewers receive all identical public states, including successes. Same native OpenCode runtime and budgets.',
                  simple_baseline='Prespecified offline replay: retain every executable source program; otherwise use its closed-SFT review. No hidden labels in this trigger; count only selected requests as policy cost.',
                  statistics=dict(primary='paired filing bootstrap difference, 20000 draws, seed 17, percentile 95% interval',
                                  secondary='Report paired point differences and intervals descriptively, without treating non-significance as equality.'),
                  decision='Retain all outcomes. Do not tune the rule, prompt, gate or threshold on these filings; changes require new development designation and a fresh evaluation source.',
                  max_local_posts=64*5*study.CAPS['posts'],campus_posts=0,**runtime)
    study.new(root/'PROTOCOL.json',protocol)
    target=root/'firstpass_v1';target.mkdir();episodes=[]
    study.new(target/'LABELS_PRIVATE.json',[dict(index=i,id=r['id'],report=r['filename'],exe_ans=r['qa']['exe_ans']) for i,r in enumerate(records)])
    for i,record in enumerate(records):
        folder=target/'closed_sft'/f'{i:03d}';inputs=folder/'inputs';inputs.mkdir(parents=True)
        (folder/'work').mkdir(mode=0o755);(folder/'dependencies').mkdir()
        public=task.public_record(record)
        (inputs/'public.json').write_text(json.dumps(public,ensure_ascii=False)+'\n')
        (inputs/'task.txt').write_text(study.prompt(public))
        for filename,path in [('finqa_tool.py',Path(task.__file__)),('executor.py',Path(task.executor().__file__))]:
            (inputs/filename).write_bytes(path.read_bytes())
        (inputs/'guest.py').write_text(study.core.GUEST)
        episodes.append(dict(index=i,id=record['id'],report=record['filename'],arm='closed_sft',folder=str(folder),
                             public_sha256=sha(inputs/'public.json'),task_sha256=sha(inputs/'task.txt')))
    plan=dict(schema='finqa_reserved_confirmation_firstpass_v1',episodes=episodes,arms=['closed_sft'],arm_order=['closed_sft'],
              **{k:v for k,v in bindings['original'].items() if k!='arms'},
              protocol_path=str(root/'PROTOCOL.json'),protocol_sha256=sha(root/'PROTOCOL.json'),
              private_labels_sha256=sha(target/'LABELS_PRIVATE.json'),terminal_status='FINQA_CONFIRMATION_FIRSTPASS_RETURNED',
              source_split='dev',scope=protocol['scope'],max_posts=64*study.CAPS['posts'],**runtime)
    study.new(target/'PLAN.json',plan);snapshot=root/'executed_sources';snapshot.mkdir()
    for path in runtime['components']:(snapshot/Path(path).name).write_bytes(Path(path).read_bytes())
    print(json.dumps(dict(protocol_sha256=sha(root/'PROTOCOL.json'),plan_sha256=sha(target/'PLAN.json'),tasks=64,max_posts=protocol['max_local_posts'])))


def prepare_confirmation_reviews():
    """Materialize every fixed reviewer from the same completed public states."""
    root=learning.ROOT/'semantic_correction_v1/expanded_v1/confirmation_v1';parent=root/'firstpass_v1'
    original=read(parent/'PLAN.json');first=read(parent/'RESULT.json');protocol=read(root/'PROTOCOL.json')
    if sha(root/'PROTOCOL.json')!=original['protocol_sha256']:raise ValueError('confirmation protocol changed')
    if first['status']!='FINQA_CONFIRMATION_FIRSTPASS_RETURNED' or len(first['episodes'])!=64:
        raise ValueError('complete common first pass required')
    if first['plan_sha256']!=sha(parent/'PLAN.json'):raise ValueError('first-pass binding changed')
    runtime={k:protocol[k] for k in expanded_runtime()}
    for path,digest in runtime['components'].items():
        if sha(path)!=digest:raise ValueError('frozen runtime changed')
    targets=[root/('review_'+job['name']) for job in protocol['review_jobs']]
    if any(p.exists() for p in targets):raise ValueError('review preparation already attempted')
    for job,target in zip(protocol['review_jobs'],targets):
        binding=protocol['bindings'][job['name']];training=Path(binding['training_root'])
        if sha(training/'RESULT.json')!=binding['training_result_sha256']:raise ValueError('training result changed')
        target.mkdir();shutil.copyfile(parent/'LABELS_PRIVATE.json',target/'LABELS_PRIVATE.json');episodes=[];sources=[]
        for ep in original['episodes']:
            source=Path(ep['folder']);text=study.recovery_prompt(read(source/'inputs/public.json'),study.recent_actions(source))
            sources.append(dict(ep,result_sha256=sha(source/'RESULT.json'),work_tree=study.core.tree(source/'work')))
            for arm in job['arms']:
                folder=target/arm/f"{ep['index']:03d}";folder.mkdir(parents=True)
                shutil.copytree(source/'inputs',folder/'inputs');shutil.copytree(source/'work',folder/'work');(folder/'dependencies').mkdir()
                (folder/'inputs/task.txt').write_text(text)
                episodes.append(dict(ep,arm=arm,folder=str(folder),task_sha256=sha(folder/'inputs/task.txt'),source_result_sha256=sha(source/'RESULT.json')))
        plan=dict(schema='finqa_reserved_confirmation_review_v1',**binding,arm_order=job['arms'],episodes=episodes,source_episodes=sources,
                  protocol_path=str(root/'PROTOCOL.json'),protocol_sha256=sha(root/'PROTOCOL.json'),parent_plan_sha256=sha(parent/'PLAN.json'),
                  private_labels_sha256=sha(target/'LABELS_PRIVATE.json'),max_posts=128*study.CAPS['posts'],
                  terminal_status='FINQA_CONFIRMATION_REVIEW_RETURNED',scope=protocol['scope'],**runtime)
        study.new(target/'PLAN.json',plan)
    print(json.dumps(dict(jobs=[dict(folder=str(p),plan_sha256=sha(p/'PLAN.json')) for p in targets])))


def prepare_identity_review():
    """Replay both terminal-placement learners on the existing dev states."""
    training=learning.ROOT/'semantic_correction_v1/expanded_v1/controls_v1/identity_fold_v1'
    parent=training.parents[1]/'dev_firstpass_v1';out=training/'native_v1'
    if out.exists():raise ValueError('identity review already prepared')
    source_plan=read(parent/'PLAN.json');first=read(parent/'RESULT.json');trained=read(training/'PLAN.json')
    if first['status']!='FINQA_EXPANDED_DEV_FIRSTPASS_RETURNED' or len(first['episodes'])!=32:
        raise ValueError('complete shared source states required')
    arms=list(trained['arms']);random.Random(17).shuffle(arms);episodes=[];sources=[];out.mkdir()
    for ep in source_plan['episodes']:
        source=Path(ep['folder']);public=read(source/'inputs/public.json')
        text=study.recovery_prompt(public,study.recent_actions(source))
        sources.append(dict(ep,result_sha256=sha(source/'RESULT.json'),work_tree=study.core.tree(source/'work')))
        for arm in arms:
            folder=out/arm/f"{ep['index']:03d}";folder.mkdir(parents=True)
            shutil.copytree(source/'inputs',folder/'inputs');shutil.copytree(source/'work',folder/'work')
            (folder/'dependencies').mkdir();(folder/'inputs/task.txt').write_text(text)
            episodes.append(dict(ep,arm=arm,folder=str(folder),task_sha256=sha(folder/'inputs/task.txt')))
    shutil.copyfile(parent/'LABELS_PRIVATE.json',out/'LABELS_PRIVATE.json')
    plan=dict(schema='finqa_identity_placement_native_review_v1',episodes=episodes,arm_order=arms,arms=arms,
              training_root=str(training),training_plan_sha256=sha(training/'PLAN.json'),
              required_training_status='TRAINED_IDENTITY_TERMINAL_ARMS',terminal_status='FINQA_IDENTITY_REVIEW_RETURNED',
              source_episodes=sources,parent_plan_sha256=sha(parent/'PLAN.json'),private_labels_sha256=sha(out/'LABELS_PRIVATE.json'),
              max_posts=len(episodes)*study.CAPS['posts'],
              comparison='Same existing 32 dev workspaces and original public review prompt, all reviewed regardless of answer. Only the matched terminal-target conditioning changes during training.',
              scope='Already exposed method-development cohort; not an independent confirmation set.',**expanded_runtime())
    study.new(out/'PLAN.json',plan);snapshot=out/'executed_sources';snapshot.mkdir()
    for path in plan['components']:(snapshot/Path(path).name).write_bytes(Path(path).read_bytes())
    print(json.dumps(dict(plan_sha256=sha(out/'PLAN.json'),episodes=len(episodes),max_posts=plan['max_posts'])))


def run_review(digest):
    if sha(REVIEW/'PLAN.json')!=digest or (REVIEW/'LIVE.json').exists():raise ValueError('review plan/attempt')
    plan=read(REVIEW/'PLAN.json');training=Path(plan['training_root'])
    assert sha(training/'PLAN.json')==plan['training_plan_sha256']
    assert read(training/'RESULT.json')['status']=='TRAINED_REFINEMENT_ARMS'
    for name,value in plan['components'].items():
        if sha(name)!=value:raise ValueError('review component changed')
    for key in ['parent','server','converter','warm_gguf']:
        assert sha(plan[key])==plan[key+'_sha256']
    state=dict(status='RUNNING',pid=os.getpid(),source=[],reviews=[],plan_sha256=digest,
               training_result_sha256=sha(training/'RESULT.json'),owned_model_stopped=True)
    started=time.monotonic();study.publish(REVIEW/'LIVE.json',state)
    try:
        with study.core.resource_lock():
            h=study.core.helpers();runtime=h.deps.verify_projection(h.actor.RUNTIME_ROOT,h.actor.RUNTIME_SHA)
            for arm in ['source']+plan['review_arms']:
                if arm in ['source','ordinary_review']:lora=Path(plan['warm_gguf'])
                else:lora=convert(plan,arm,REVIEW)
                process=None;log=None
                try:
                    process,log=start_server(plan,arm,lora,REVIEW);state['owned_model_stopped']=False
                    study.publish(REVIEW/'LIVE.json',state)
                    episodes=plan['source_episodes'] if arm=='source' else read(REVIEW/'REVIEW_INPUTS.json')[arm]
                    for ep in episodes:
                        folder=Path(ep['folder'])
                        assert sha(folder/'inputs/public.json')==ep['public_sha256']
                        assert sha(folder/'inputs/task.txt')==ep['task_sha256']
                        value=study.episode(ep,h,runtime,study.MODEL,private_labels=REVIEW/'LABELS_PRIVATE.json')
                        value['arm']=arm;state['source' if arm=='source' else 'reviews'].append(value)
                        study.publish(REVIEW/'LIVE.json',state)
                        print(json.dumps(dict(arm=arm,index=ep['index'],correct=value['execution_correct'],
                                              posts=value['accounting']['actual_forwarded_posts'])),flush=True)
                        if not value['accounting']['integrity_passed']:raise RuntimeError('review interface integrity')
                finally:
                    if process is not None:stop_server(process,log)
                    state['owned_model_stopped']=True;study.publish(REVIEW/'LIVE.json',state)
                if arm=='source':
                    # No outcome-dependent filtering: every source state gets
                    # the exact same public review packet in every policy arm.
                    packets={a:[] for a in plan['review_arms']}
                    for ep in plan['source_episodes']:
                        parent=Path(ep['folder']);study.core.tree(parent/'work')
                        public=read(parent/'inputs/public.json')
                        text=study.recovery_prompt(public,study.recent_actions(parent))
                        for target in plan['review_arms']:
                            folder=REVIEW/target/f"{ep['index']:03d}";folder.mkdir(parents=True)
                            shutil.copytree(parent/'inputs',folder/'inputs');shutil.copytree(parent/'work',folder/'work')
                            (folder/'dependencies').mkdir();(folder/'inputs/task.txt').write_text(text)
                            packets[target].append(dict(ep,folder=str(folder),task_sha256=sha(folder/'inputs/task.txt'),
                                                        source_result_sha256=sha(parent/'RESULT.json')))
                    study.new(REVIEW/'REVIEW_INPUTS.json',packets)
            state['status']='FINQA_REVIEW_COMPARISON_RETURNED'
    except BaseException:
        state.update(status='FAILED',error=traceback.format_exc());raise
    finally:
        state['seconds']=time.monotonic()-started
        study.publish(REVIEW/'LIVE.json',state);study.new(REVIEW/'RESULT.json',state)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['prepare','run','prepare-strong','strong','prepare-recovery','recover','prepare-review','review','prepare-paired-review','paired-review','prepare-expanded-eval','expanded-firstpass','prepare-expanded-review','expanded-review','prepare-identity-review','identity-review','prepare-confirmation','confirmation-firstpass','prepare-confirmation-reviews']);p.add_argument('--count',type=int,default=4)
    p.add_argument('--plan-sha');a=p.parse_args()
    if a.mode=='prepare':prepare(a.count)
    elif a.mode=='prepare-strong':prepare_strong()
    elif a.mode=='prepare-recovery':prepare_recovery()
    elif a.mode=='strong':run_strong(a.plan_sha)
    elif a.mode=='recover':run_strong(a.plan_sha,'recovery_training_v1')
    elif a.mode=='prepare-review':prepare_review(a.count)
    elif a.mode=='review':run_review(a.plan_sha)
    elif a.mode=='prepare-paired-review':prepare_paired_review()
    elif a.mode=='paired-review':run(a.plan_sha,PAIRED_REVIEW)
    elif a.mode=='prepare-expanded-eval':prepare_expanded_eval(a.count)
    elif a.mode=='expanded-firstpass':run(a.plan_sha,learning.ROOT/'semantic_correction_v1/expanded_v1/dev_firstpass_v1')
    elif a.mode=='prepare-expanded-review':prepare_expanded_review()
    elif a.mode=='prepare-confirmation':prepare_confirmation()
    elif a.mode=='prepare-confirmation-reviews':prepare_confirmation_reviews()
    elif a.mode=='confirmation-firstpass':run(a.plan_sha,learning.ROOT/'semantic_correction_v1/expanded_v1/confirmation_v1/firstpass_v1')
    elif a.mode=='prepare-identity-review':prepare_identity_review()
    elif a.mode=='identity-review':run(a.plan_sha,learning.ROOT/'semantic_correction_v1/expanded_v1/controls_v1/identity_fold_v1/native_v1')
    elif a.mode=='expanded-review':run(a.plan_sha,learning.ROOT/'semantic_correction_v1/expanded_v1/dev_review_v1')
    else:run(a.plan_sha)
