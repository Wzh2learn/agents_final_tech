"""Compile real FinQA recoveries without privileged conditioning; train two LoRAs.

Reuses the verified native Qwen completion encoder. No generation occurs here.
"""
from __future__ import annotations

import argparse
import copy
import gc
import hashlib
import json
import math
from pathlib import Path
import shlex
import sys
import time
import traceback

HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(HERE),str(HERE.parents[1])]
import finqa_correction as task
import run_finqa_correction as study
import alfworld_supervision_tokens as tokens

ROOT=study.ROOT/'learning_v1'
REFINEMENT=ROOT/'refinement_v1'
MODEL=Path('/home/testuser/wzh/models/hf/Qwen3-8B')


def read(path):return json.loads(Path(path).read_text())
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def new(path,value):study.new(path,value)


def sse_assistant(raw):
    text=[];calls={}
    for line in raw.splitlines():
        if not line.startswith(b'data:'):continue
        body=line[5:].strip()
        if body==b'[DONE]':continue
        value=json.loads(body)
        for choice in value.get('choices',[]):
            delta=choice.get('delta',{})
            if delta.get('content'):text.append(delta['content'])
            for entry in delta.get('tool_calls') or []:
                call=calls.setdefault(entry['index'],dict(id='',type='function',function=dict(name='',arguments='')))
                if entry.get('id'):call['id']=entry['id']
                for key in ['name','arguments']:
                    if entry.get('function',{}).get(key):call['function'][key]+=entry['function'][key]
    return dict(role='assistant',content=''.join(text),tool_calls=[calls[k] for k in sorted(calls)])


def project_request(request, teacher_text, public_text):
    """Rebuild only the controlled user task; retain actual public history/tools."""
    request=copy.deepcopy(request);count=0
    for message in request['messages']:
        if message.get('role')!='user' or not isinstance(message.get('content'),str):continue
        # Native OpenCode quotes CLI task text and escapes its literal quotes.
        # This is the same exact delivery representation checked by the actor;
        # do not JSON-decode arbitrary history or remove labels by fuzzy matching.
        wrapped='"'+teacher_text.replace('"',chr(92)+'"')+'"'
        if message['content']==wrapped:
            message['content']='"'+public_text.replace('"',chr(92)+'"')+'"'
            count+=1
        elif message['content']==teacher_text:
            message['content']=public_text
            count+=1
    if count!=1:raise ValueError('teacher task not uniquely identified in conditioning')
    encoded=json.dumps(request['messages'],ensure_ascii=False)
    if 'training_reference_program' in encoded or 'training_reference_execution_answer' in encoded:
        raise ValueError('a later message re-exposed privileged teacher labels')
    return dict(messages=request['messages'],tools=request['tools'])


def field_annotation(tokenizer,request,assistant,row,program,selected,*,return_fields=False):
    opts=dict(tools=request['tools'],enable_thinking=False,truncation=False,return_dict=False)
    prefix=tokenizer.apply_chat_template(request['messages'],tokenize=False,add_generation_prompt=True,**opts)
    full=tokenizer.apply_chat_template(request['messages']+[assistant],tokenize=False,add_generation_prompt=False,**opts)
    encoded=tokenizer(full,add_special_tokens=False,return_offsets_mapping=True)
    if encoded['input_ids']!=row['input_ids']:raise ValueError('offset tokenizer differs from verified completion')
    if full[len(prefix):].count(program)!=1:raise ValueError('program is not unique in actual completion')
    start=full.index(program,len(prefix));spans=[];cursor=0
    for step in task.executor().parse_program(program):
        rendered=f'{step.op}({step.arg1}, {step.arg2})'
        if not program[cursor:].startswith(rendered):raise ValueError('noncanonical program span')
        a=start+cursor
        for name,offset,size in [('op',0,len(step.op)),('arg1',len(step.op)+1,len(step.arg1)),
                                 ('arg2',len(step.op)+len(step.arg1)+3,len(step.arg2))]:
            spans.append((a+offset,a+offset+size,f'{step.index}:{name}'))
        cursor+=len(rendered)+2
    field_ids=[];supervised=[label!=-100 for label in row['labels']]
    for keep,(a,b) in zip(supervised,encoded['offset_mapping']):
        matches={name for c,d,name in spans if a<d and b>c} if keep else set()
        if len(matches)>1:raise ValueError('one token crosses two annotated fields')
        field_ids.append(next(iter(matches)) if matches else None)
    weights=task.field_token_weights(field_ids,selected,supervised)
    if selected and not any(keep and field in selected for keep,field in zip(supervised,field_ids)):
        raise ValueError('selected fields have no supervised tokens')
    if abs(sum(weights)-sum(supervised))>1e-6:raise ValueError('supervised weight mass changed')
    return (weights,field_ids) if return_fields else weights


def prepare():
    if ROOT.exists():raise ValueError('learning attempt already exists')
    labels=read(study.ROOT/'LABELS_PRIVATE.json');student=read(study.ROOT/'RESULT.json')
    successes={}
    for attempt in [2,3]:
        folder=study.ROOT/f'teacher_v{attempt}'
        for entry in read(folder/'RESULT.json')['episodes']:
            if entry['native_success']:successes.setdefault(entry['index'],(folder,entry))
    tok=tokens.load_tokenizer(MODEL);rows=[];sources={}
    for index,(folder,entry) in sorted(successes.items()):
        episode=folder/f'{index:03d}';public=read(episode/'inputs/public.json')
        original=study.ROOT/'student'/f'{index:03d}'
        actions=[]
        for line in (original/'raw.jsonl').read_text().splitlines():
            event=json.loads(line);part=event.get('part',{})
            if part.get('type')=='tool':
                state=part.get('state',{});actions.append(dict(input=state.get('input'),output=state.get('output')))
        public_text=(study.prompt(public)+'\n\nContinue the existing student workspace. Use the public task and actual '
                     'failed operations below to repair its latest program with the same execution tool. '
                     'No reference answer is available.\n'+json.dumps({'student_actions':actions[-6:]},ensure_ascii=False))
        teacher_text=(episode/'inputs/task.txt').read_text()
        for record in entry['accounting']['requests']:
            prefix=episode/'wire'/f"{record['request']:05d}.request"
            request_path=prefix.with_suffix('.request.json');response_path=prefix.with_suffix('.request.response')
            assert sha(request_path)==record['request_sha256']
            assert sha(response_path)==record['response']['body_sha256']
            assistant=sse_assistant(response_path.read_bytes())
            calls=assistant.get('tool_calls') or []
            if len(calls)!=1 or calls[0]['function']['name']!='bash':continue
            arguments=json.loads(calls[0]['function']['arguments'])
            argv=shlex.split(arguments['command'])
            if '--program' not in argv:continue
            program=argv[argv.index('--program')+1]
            if not task.grade(program,public,labels[index]['exe_ans'])['execution_correct']:continue
            projected=project_request(read(request_path),teacher_text,public_text)
            if program in json.dumps(projected['messages'],ensure_ascii=False):
                raise ValueError('correct target program is already present in conditioning')
            encoded=tokens.encode_completion(projected,assistant,tok,16384)
            region=task.correction_fields(student['episodes'][index]['submitted_program'],program)
            weights=field_annotation(tok,projected,assistant,encoded,program,region['fields'])
            rows.append(dict(**encoded,weights=weights,source_index=index,report=labels[index]['report'],
                             teacher_attempt=folder.name,region=region,assistant=assistant,
                             projection='privileged teacher user task replaced with public recovery task; actual later history retained'))
            sources[str(request_path)]=sha(request_path);sources[str(response_path)]=sha(response_path)
            break
        else:raise ValueError('no actual correct tool action for source '+str(index))
    if len(rows)!=7 or len({r['report'] for r in rows})!=7:raise ValueError('expected seven report-distinct real recoveries')
    ROOT.mkdir()
    data=dict(rows=rows,tokenizer=tokens.tokenizer_binding(MODEL,tok),sources=sources,
              scope='TRAIN-only native teacher actions, privileged labels removed from student conditioning')
    new(ROOT/'DATA.json',data)
    plan=dict(model_path=str(MODEL),data_sha256=sha(ROOT/'DATA.json'),seed=17,
              arms=['uniform_recovery','operand_repair'],updates_per_arm=24,learning_rate=2e-4,
              rank=8,alpha=16,wall_seconds=2400,resource_lock=str(study.core.LOCK),
              components={str(p):sha(p) for p in [Path(__file__),Path(task.__file__),Path(tokens.__file__)]},
              interpretation='On this cohort localized fields equal a conditional all-operand rule; reuse that same arm, no independent localization claim',
              next='Save/reload LoRAs, convert with existing converter and evaluate native OpenCode on new report-disjoint development tasks')
    new(ROOT/'PLAN.json',plan)
    print(json.dumps({'rows':len(rows),'active_weight_rows':sum(any(abs(w-1)>1e-6 for w,label in zip(r['weights'],r['labels']) if label!=-100) for r in rows),
                      'sequence_tokens':[r['sequence_length'] for r in rows],'supervised_tokens':sum(r['supervised_tokens'] for r in rows),
                      'plan_sha256':sha(ROOT/'PLAN.json')}))


def weighted_loss(logits,labels,weights):
    import torch.nn.functional as F
    scores=logits[:,:-1,:].float();target=labels[:,1:];mass=weights[:,1:]
    losses=F.cross_entropy(scores.reshape(-1,scores.shape[-1]),target.reshape(-1),ignore_index=-100,reduction='none')
    return (losses.reshape_as(target)*mass).sum()/mass.sum()


def prepare_refinement():
    if REFINEMENT.exists():raise ValueError('refinement attempt already exists')
    folder=ROOT/'native_v1/recovery_training_v1'
    state=read(folder/'RESULT.json');teacher_plan=read(folder/'PLAN.json')
    assert state['status']=='PRIVILEGED_RECOVERY_RETURNED'
    arms=['uniform_recovery','all_operands','localized_fields']
    original=read(ROOT/'DATA.json');rows=[];sources=dict(original['sources'])
    # Identical replay preserves the already learned execution protocol.
    # Only the new on-policy residuals carry alternative field supervision.
    for row in original['rows']:
        row=copy.deepcopy(row);uniform=[float(t!=-100) for t in row['labels']]
        row['weights_by_arm']={arm:list(uniform) for arm in arms};row['phase']='replay'
        rows.append(row)
    tok=tokens.load_tokenizer(MODEL);diagnostics=[]
    for entry in state['episodes']:
        ep=next(e for e in teacher_plan['episodes'] if e['index']==entry['index'])
        parent=Path(ep['source_folder']);source=read(parent/'RESULT.json')
        if sha(parent/'RESULT.json')!=ep['source_result_sha256']:raise ValueError('residual source changed')
        if not entry['native_success']:raise ValueError('all four teacher recoveries required before compiling')
        episode=Path(ep['folder']);public=read(episode/'inputs/public.json')
        label=read(folder/'LABELS_PRIVATE.json')[entry['index']]
        public_text=study.recovery_prompt(public,study.recent_actions(parent))
        teacher_text=(episode/'inputs/task.txt').read_text()
        for rec in entry['accounting']['requests']:
            request_path=episode/'wire'/f"{rec['request']:05d}.request.json"
            response_path=request_path.with_suffix('.response')
            assert sha(request_path)==rec['request_sha256']
            assert sha(response_path)==rec['response']['body_sha256']
            assistant=sse_assistant(response_path.read_bytes());calls=assistant.get('tool_calls') or []
            if len(calls)!=1 or calls[0]['function']['name']!='bash':continue
            argv=shlex.split(json.loads(calls[0]['function']['arguments'])['command'])
            if '--program' not in argv:continue
            program=argv[argv.index('--program')+1]
            if not task.grade(program,public,label['exe_ans'])['execution_correct']:continue
            projected=project_request(read(request_path),teacher_text,public_text)
            if program in json.dumps(projected['messages'],ensure_ascii=False):
                raise ValueError('correct target already present in recovery conditioning')
            encoded=tokens.encode_completion(projected,assistant,tok,16384)
            region=task.correction_fields(source['submitted_program'],program)
            local,fields=field_annotation(tok,projected,assistant,encoded,program,region['fields'],return_fields=True)
            uniform=[float(t!=-100) for t in encoded['labels']]
            operands={field for field in fields if field is not None and not field.endswith(':op')}
            all_operands=task.field_token_weights(fields,operands,[t!=-100 for t in encoded['labels']])
            weights=dict(uniform_recovery=uniform,all_operands=all_operands,localized_fields=local)
            row=dict(**encoded,source_index=entry['index'],report=ep['report'],phase='residual',region=region,
                     assistant=assistant,weights_by_arm=weights,teacher_attempt='on_policy_27b_train_recovery',
                     projection='privileged teacher task replaced with the same public fixed-review prompt used for deployment')
            rows.append(row);sources[str(request_path)]=sha(request_path);sources[str(response_path)]=sha(response_path)
            diagnostics.append(dict(index=entry['index'],fields=region['fields'],fallback=region['fallback'],
                                    differs_from_all_operands=any(abs(a-b)>1e-6 for a,b in zip(local,all_operands)),
                                    supervised_tokens=encoded['supervised_tokens']))
            break
        else:raise ValueError('no correct native teacher tool action for residual '+str(entry['index']))
    assert len(rows)==11 and len({r['report'] for r in rows})==11
    assert any(d['differs_from_all_operands'] for d in diagnostics),'need an actual supervision contrast'
    REFINEMENT.mkdir()
    new(REFINEMENT/'DATA.json',dict(rows=rows,sources=sources,tokenizer=tokens.tokenizer_binding(MODEL,tok),diagnostics=diagnostics))
    warm=ROOT/'uniform_recovery'
    warm_files=read(ROOT/'RESULT.json')['arms']['uniform_recovery']['adapter_files']
    for name,digest in warm_files.items():assert sha(warm/name)==digest
    schedule=[(i//2)%7 if i%2==0 else 7+(i//2)%4 for i in range(32)]
    plan=dict(model_path=str(MODEL),data_sha256=sha(REFINEMENT/'DATA.json'),seed=17,arms=arms,
              updates_per_arm=32,schedule=schedule,learning_rate=2e-4,rank=8,alpha=16,wall_seconds=3600,
              resource_lock=str(study.core.LOCK),warm_start=str(warm),warm_files=warm_files,
              parent_training_result_sha256=sha(ROOT/'RESULT.json'),teacher_result_sha256=sha(folder/'RESULT.json'),
              components={str(p):sha(p) for p in [Path(__file__),Path(task.__file__),Path(tokens.__file__),Path(study.__file__)]},
              scope='TRAIN-only development. Four former development reports now join training; exclude all 12 formation/exposed reports from the next task set.',
              comparison='Same warm adapter, replay, new recoveries, schedule and token mass; only residual-field weights differ',
              deployment='Common first-pass Agent, then one fixed public review for every task; no hidden-answer trigger',
              next='Native report-disjoint review comparison against ordinary fixed review; include common first-pass and formation/training costs')
    snapshot=REFINEMENT/'executed_sources';snapshot.mkdir()
    for path in plan['components']:(snapshot/Path(path).name).write_bytes(Path(path).read_bytes())
    new(REFINEMENT/'PLAN.json',plan)
    print(json.dumps(dict(plan_sha256=sha(REFINEMENT/'PLAN.json'),rows=len(rows),diagnostics=diagnostics)))


def train(digest, root=None):
    import fcntl
    import torch
    from transformers import AutoModelForCausalLM
    from peft import LoraConfig,get_peft_model,PeftModel
    root=ROOT if root is None else Path(root)
    if sha(root/'PLAN.json')!=digest or (root/'LIVE.json').exists():raise ValueError('training plan/attempt')
    plan=read(root/'PLAN.json');assert sha(root/'DATA.json')==plan['data_sha256']
    for path,value in plan['components'].items():
        if sha(path)!=value:raise ValueError('training component changed')
    rows=read(root/'DATA.json')['rows'];started=time.monotonic()
    state=dict(status='RUNNING',pid=__import__('os').getpid(),optimizer_updates=0,forward_calls=0,
               training_sequence_tokens=0,supervised_tokens=0,arms={},http_model_requests=0)
    model=None
    try:
        with Path(plan['resource_lock']).open('r+') as lease:
            fcntl.flock(lease,fcntl.LOCK_EX|fcntl.LOCK_NB)
            torch.manual_seed(plan['seed'])
            study.publish(root/'LIVE.json',state)
            model=AutoModelForCausalLM.from_pretrained(plan['model_path'],dtype=torch.bfloat16,
                device_map={'':0},attn_implementation='sdpa',local_files_only=True,trust_remote_code=False)
            if plan.get('warm_start'):
                for name,value in plan['warm_files'].items():
                    if sha(Path(plan['warm_start'])/name)!=value:raise ValueError('warm adapter changed')
                model=PeftModel.from_pretrained(model,plan['warm_start'],is_trainable=True)
            else:
                model=get_peft_model(model,LoraConfig(r=8,lora_alpha=16,lora_dropout=0.,target_modules=['q_proj','v_proj'],task_type='CAUSAL_LM',bias='none'))
            initial={n:p.detach().clone() for n,p in model.named_parameters() if p.requires_grad}
            state['trainable_parameters']=sum(p.numel() for p in initial.values())
            state['initial_adapter_sha256']=hashlib.sha256(b''.join(
                name.encode()+value.detach().cpu().contiguous().view(torch.uint8).numpy().tobytes()
                for name,value in sorted(initial.items()))).hexdigest()
            model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={'use_reentrant':False});model.enable_input_require_grads()
            for arm in plan['arms']:
                with torch.no_grad():
                    for name,param in model.named_parameters():
                        if name in initial:param.copy_(initial[name])
                optimizer=torch.optim.AdamW([p for p in model.parameters() if p.requires_grad],lr=plan['learning_rate'])
                model.train();losses=[];arm_start=time.monotonic()
                for update in range(plan['updates_per_arm']):
                    if time.monotonic()-started>plan['wall_seconds']:raise TimeoutError('finite training wall cap')
                    row=rows[plan['schedule'][update] if 'schedule' in plan else update%len(rows)]
                    x=torch.tensor([row['input_ids']],device='cuda');y=torch.tensor([row['labels']],device='cuda')
                    weights=(row['weights_by_arm'][arm] if 'weights_by_arm' in row else
                             row['weights'] if arm=='operand_repair' else [float(t!=-100) for t in row['labels']])
                    w=torch.tensor([weights],device='cuda')
                    optimizer.zero_grad(set_to_none=True)
                    value=weighted_loss(model(input_ids=x,use_cache=False).logits,y,w)
                    if not torch.isfinite(value):raise ValueError('nonfinite loss')
                    value.backward();torch.nn.utils.clip_grad_norm_([p for p in model.parameters() if p.requires_grad],1.)
                    optimizer.step();losses.append(float(value.detach()))
                    state['optimizer_updates']+=1;state['forward_calls']+=1
                    state['training_sequence_tokens']+=row['sequence_length'];state['supervised_tokens']+=row['supervised_tokens']
                    study.publish(root/'LIVE.json',state)
                    del x,y,w,value
                output=root/arm;model.save_pretrained(output)
                state['arms'][arm]=dict(updates=len(losses),losses=losses,seconds=time.monotonic()-arm_start,
                                       adapter_files={p.name:sha(p) for p in output.iterdir() if p.is_file()})
                del optimizer;gc.collect();torch.cuda.empty_cache()
                study.publish(root/'LIVE.json',state)
            state['status']='TRAINED_REFINEMENT_ARMS' if plan.get('warm_start') else 'TRAINED_TWO_DEVELOPMENT_ARMS'
    except BaseException:
        state.update(status='FAILED',error=traceback.format_exc());raise
    finally:
        state['seconds']=time.monotonic()-started
        study.publish(root/'LIVE.json',state);new(root/'RESULT.json',state)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['prepare','train','prepare-refinement','train-refinement']);p.add_argument('--plan-sha');args=p.parse_args()
    if args.mode=='prepare':prepare()
    elif args.mode=='prepare-refinement':prepare_refinement()
    else:train(args.plan_sha,REFINEMENT if args.mode=='train-refinement' else ROOT)
