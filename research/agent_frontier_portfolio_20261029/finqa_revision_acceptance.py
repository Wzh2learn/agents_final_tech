"""Test local correction evidence using existing, actually executed proposals.

Preparation and scoring never read hidden answers. This is an offline policy
experiment, not a fresh Agent rollout. The two adapters share their positive
targets and warm start; only one received execution-filtered negative edits.
"""
from __future__ import annotations

import argparse
import gc
import json
import math
from pathlib import Path
import shlex
import time
import traceback

import finqa_learning_controls as controls

learning=controls.learning
task=controls.task
read=learning.read
sha=learning.sha
ROOT=controls.ROOT/'controls_v1/local_acceptance_v1'
METHODS=('negative_first','sft_first','relative_first','relative_sequence_sum','relative_sequence_mean')


def public_gate(original,candidate):
    if any(x.get('status') not in ('executed','error') for x in (original,candidate)):
        raise ValueError('public execution status required')
    if candidate['status']!='executed':return 'retain'
    if original['status']!='executed':return 'accept'
    if task.canonical_answer(original['terminal_execution_answer'])==task.canonical_answer(candidate['terminal_execution_answer']):return 'retain'
    return 'score'


def advantages(negative,reference):
    return dict(negative_first=negative['first_margin'],sft_first=reference['first_margin'],
                relative_first=negative['first_margin']-reference['first_margin'],
                relative_sequence_sum=(negative['new_sum']-negative['old_sum'])-(reference['new_sum']-reference['old_sum']),
                relative_sequence_mean=(negative['new_mean']-negative['old_mean'])-(reference['new_mean']-reference['old_mean']))


def accept(gate,score):
    if gate in ('accept','retain'):return gate=='accept'
    if gate!='score' or score is None or not math.isfinite(score):raise ValueError('finite declared acceptance score required')
    return score>0.  # Fixed before the first scoring forward; ties retain.


def tool_target(program):
    command='/extra/bin/python /inputs/finqa_tool.py --program '+shlex.quote(program)
    return dict(role='assistant',content='',tool_calls=[dict(id='public-candidate',type='function',
                function=dict(name='bash',arguments=json.dumps(dict(command=command),ensure_ascii=False)))])


def canonical_program(program,public):
    steps=task.executor().parse_program(program)
    value=', '.join(f'{s.op}({s.arg1}, {s.arg2})' for s in steps)
    if task.execute_public(value,public)!=task.execute_public(program,public):raise ValueError('canonical program changed execution')
    return value


def prepare():
    if ROOT.exists():raise ValueError('local-acceptance study already prepared')
    expanded=controls.ROOT;source_plan=read(expanded/'dev_firstpass_v1/PLAN.json')
    original={e['index']:e for e in source_plan['episodes']}
    proposed=[e for e in read(expanded/'dev_review_v1/PLAN.json')['episodes'] if e['arm']=='edit_all_negative']
    if len(original)!=32 or {e['index'] for e in proposed}!=set(original):raise ValueError('fixed complete cohort required')
    tokenizer=learning.tokens.load_tokenizer(learning.MODEL);rows=[];binding={}
    for ep in sorted(proposed,key=lambda e:e['index']):
        prior=Path(original[ep['index']]['folder']);after=Path(ep['folder'])
        before=read(prior/'RESULT.json');now=read(after/'RESULT.json');public=read(prior/'inputs/public.json')
        for folder in (prior,after):
            for rel in ('RESULT.json','inputs/public.json'):binding[str(folder/rel)]=sha(folder/rel)
        if sha(prior/'inputs/public.json')!=sha(after/'inputs/public.json'):raise ValueError('public task differs')
        old=task.execute_public(before['submitted_program'],public);new=task.execute_public(now['submitted_program'],public)
        if old!=before['public_execution'] or new!=now['public_execution']:raise ValueError('public execution changed')
        row=dict(index=ep['index'],id=ep['id'],gate=public_gate(old,new),original_folder=str(prior),proposal_folder=str(after),
                 original_program=before['submitted_program'],candidate_program=now['submitted_program'])
        if row['gate']=='score':
            request=after/'wire/00001.request.json';binding[str(request)]=sha(request)
            if binding[str(request)]!=now['accounting']['requests'][0]['request_sha256']:raise ValueError('public request changed')
            raw=read(request)
            public_text=(after/'inputs/task.txt').read_text()
            projected=learning.project_request(raw,public_text,public_text)
            old_target=tool_target(canonical_program(row['original_program'],public))
            new_target=tool_target(canonical_program(row['candidate_program'],public))
            a,b=[learning.tokens.encode_completion(projected,x,tokenizer,16384) for x in (old_target,new_target)]
            point=learning.first_edit_decision(b,a)
            row.update(old=a,new=b,decision=point)
        rows.append(row)
    trained=read(expanded/'RESULT.json');models={}
    for name,arm in [('sft','closed_sft'),('negative','edit_all_negative')]:
        folder=expanded/arm;files=trained['arms'][arm]['adapter_files']
        if any(sha(folder/n)!=v for n,v in files.items()):raise ValueError('adapter differs from training receipt')
        models[name]=dict(folder=str(folder),files=files)
    scored=[x for x in rows if x['gate']=='score']
    if len(scored)!=16:raise ValueError('public-outcome cohort changed')
    ROOT.mkdir(mode=0o700)
    learning.new(ROOT/'DATA.json',dict(rows=rows,source_hashes=binding,model_requests=0,scope='Public-only same-state candidate pairs; hidden answers are not read by compilation or scoring.'))
    plan=dict(schema='finqa_local_acceptance_v1',data_sha256=sha(ROOT/'DATA.json'),adapters=models,model_path=str(learning.MODEL),
              tokenizer=learning.tokens.tokenizer_binding(learning.MODEL,tokenizer),threshold=0.,methods=METHODS,
              max_forwards=len(scored)*6,max_sequence_tokens=sum(2*(len(x['old']['input_ids'])+len(x['new']['input_ids'])+x['decision']['target_position']) for x in scored),
              wall_seconds=1800,local_http_posts=0,campus_posts=0,training_updates=0,
              source_training_result_sha256=sha(expanded/'RESULT.json'),private_labels_path=str(expanded/'dev_firstpass_v1/LABELS_PRIVATE.json'),private_labels_sha256=source_plan['private_labels_sha256'],
              components={str(p):sha(p) for p in [Path(__file__),Path(learning.__file__),Path(task.__file__),Path(learning.tokens.__file__),Path(controls.__file__)]},
              scope='All 32 already-exposed dev tasks; score 16 valid unequal-outcome pairs. Three forwards per adapter/pair compare shared-prefix local evidence with full-sequence controls. This does not add online Agent successes.')
    learning.new(ROOT/'PLAN.json',plan);snapshot=ROOT/'executed_sources';snapshot.mkdir()
    for p in plan['components']:(snapshot/Path(p).name).write_bytes(Path(p).read_bytes())
    print(json.dumps(dict(plan_sha256=sha(ROOT/'PLAN.json'),tasks=len(rows),scored_pairs=len(scored),max_forwards=plan['max_forwards'],max_sequence_tokens=plan['max_sequence_tokens'])))


def score(digest):
    import torch
    import torch.nn.functional as functional
    from transformers import AutoModelForCausalLM
    from peft import PeftModel
    from scripts.graph.research_gpu_guard import gpu_lease,available_gib
    if sha(ROOT/'PLAN.json')!=digest or (ROOT/'LIVE.json').exists():raise ValueError('fresh bound scoring attempt required')
    plan=read(ROOT/'PLAN.json');assert sha(ROOT/'DATA.json')==plan['data_sha256']
    for path,value in plan['components'].items():
        if sha(path)!=value:raise ValueError('scoring source changed')
    for item in plan['adapters'].values():
        for name,value in item['files'].items():
            if sha(Path(item['folder'])/name)!=value:raise ValueError('adapter changed')
    data=read(ROOT/'DATA.json');started=time.monotonic();model=None
    state=dict(status='RUNNING',plan_sha256=digest,forward_calls=0,attempted_forwards=0,sequence_tokens=0,scores={},http_model_requests=0,training_updates=0)
    def publish():learning.study.publish(ROOT/'LIVE.json',state)
    def forward(ids):
        if time.monotonic()-started>plan['wall_seconds'] or available_gib()<32:raise RuntimeError('wall or memory limit')
        if state['attempted_forwards']>=plan['max_forwards']:raise RuntimeError('forward cap')
        state['attempted_forwards']+=1;state['sequence_tokens']+=len(ids);publish()
        result=model(input_ids=torch.tensor([ids],device='cuda'),use_cache=False).logits
        state['forward_calls']+=1
        return result
    try:
        publish()
        with gpu_lease():
            try:
                model=AutoModelForCausalLM.from_pretrained(plan['model_path'],dtype=torch.bfloat16,device_map={'':0},attn_implementation='sdpa',local_files_only=True,trust_remote_code=False)
                model=PeftModel.from_pretrained(model,plan['adapters']['sft']['folder'],adapter_name='sft',is_trainable=False)
                model.load_adapter(plan['adapters']['negative']['folder'],adapter_name='negative',is_trainable=False)
                model.eval()
                with torch.inference_mode():
                    for row in data['rows']:
                        if row['gate']!='score':continue
                        point=row['decision'];at=point['target_position'];pair={}
                        for role in ('sft','negative'):
                            model.set_adapter(role);model.eval()
                            logits=forward(row['old']['input_ids'][:at]);z=logits[0,-1].float()
                            item=dict(first_margin=float(z[point['good_token']]-z[point['bad_token']]))
                            del z,logits
                            for branch in ('old','new'):
                                batch=row[branch];logits=forward(batch['input_ids'])
                                positions=torch.tensor([i for i,t in enumerate(batch['labels']) if t!=-100],device='cuda')
                                target=torch.tensor([batch['input_ids'][i] for i in positions.tolist()],device='cuda')
                                lp=-functional.cross_entropy(logits[0,positions-1].float(),target,reduction='none')
                                item[branch+'_sum']=float(lp.sum());item[branch+'_mean']=float(lp.mean())
                                del logits,lp,positions,target
                            pair[role]=item
                        state['scores'][str(row['index'])]=dict(models=pair,advantages=advantages(pair['negative'],pair['sft']));publish()
                if state['sequence_tokens']!=plan['max_sequence_tokens']:raise ValueError('sequence accounting differs')
                if state['forward_calls']!=plan['max_forwards']:raise ValueError('incomplete scoring')
                state['status']='LOCAL_ACCEPTANCE_SCORED'
            finally:
                if model is not None:del model
                gc.collect();torch.cuda.empty_cache();torch.cuda.synchronize()
    except BaseException:
        state.update(status='FAILED',error=traceback.format_exc());raise
    finally:
        state['seconds']=time.monotonic()-started;publish();learning.new(ROOT/'RESULT.json',state)
    print(json.dumps({k:v for k,v in state.items() if k!='scores'}))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mode',choices=('prepare','score'));p.add_argument('--plan-sha');args=p.parse_args()
    if args.mode=='prepare':prepare()
    else:score(args.plan_sha)
