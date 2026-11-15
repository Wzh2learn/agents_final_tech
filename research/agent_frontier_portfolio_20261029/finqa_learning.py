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
PAIRED=ROOT/'closed_recovery_v1'
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


def completion_logit_window(row):
    """Skip only masked-prefix vocabulary projections, keeping all input tokens.

    The token immediately before the completion predicts its first token, so
    its logit must remain. Labels and auxiliary positions use the same offset.
    """
    labels=row['labels'];prompt=row['prompt_token_count']
    if (type(prompt) is not int or not 1<=prompt<len(labels)
            or len(row['input_ids'])!=len(labels)
            or any(value!=-100 for value in labels[:prompt]) or labels[prompt]<0):
        raise ValueError('a masked prefix and supervised first completion token are required')
    offset=prompt-1
    return offset,len(labels)-offset


def pair_coefficients(repair_tokens,closure_tokens,objective):
    if any(type(n) is not int or n<=0 for n in [repair_tokens,closure_tokens]):raise ValueError('positive target lengths required')
    if objective=='token_mean':
        total=repair_tokens+closure_tokens;return [repair_tokens/total,closure_tokens/total]
    if objective in ('decision_mean','paired_mode'):return [.5,.5]
    raise ValueError('unknown paired objective')


def group_coefficients(lengths,objective):
    """A retained state can have just a terminal target, not a fake repair."""
    if len(lengths)==2:return pair_coefficients(*lengths,objective)
    if (len(lengths)==1 and type(lengths[0]) is int and lengths[0]>0
            and objective in ('token_mean','decision_mean')):return [1.]
    raise ValueError('one terminal or two repair/closure targets required')


def conditioning_row(row,arm,*,allow_repair=False):
    """Preserve target tokens; moving repair context requires explicit opt-in."""
    alternate=row.get('conditioning_by_arm',{}).get(arm)
    if alternate is None:return row
    allowed={'input_ids','attention_mask','labels','prompt_token_count','sequence_length','supervised_tokens',
             'assistant_end_index','prefix_token_alignment_verified','rendered_prefix_sha256',
             'rendered_full_sha256','template_adaptations','loss_scope'}
    if ((row.get('boundary_role')!='closure' and not (allow_repair and row.get('boundary_role')=='repair')) or any(row.get('edit_contrasts',{}).values())
            or not set(alternate)<=allowed):raise ValueError('only terminal conditioning may move')
    if ([v for v in row['labels'] if v!=-100]!=[v for v in alternate['labels'] if v!=-100]
            or row['supervised_tokens']!=alternate['supervised_tokens']):
        raise ValueError('conditioning control changed supervised targets')
    return {**row,**alternate}


def initial_decision_coefficient(rows,groups,schedule):
    """Equalize initial-decision coefficients, preserving their scheduled sum.

    The existing token-mean objective gives the first token coefficient 1/N,
    where N counts ALL targets in that group, including the later closure.
    No correctness labels or evaluation outcomes enter this normalization.
    """
    if not schedule:raise ValueError('nonempty fixed schedule required')
    original=[]
    for index in schedule:
        lengths=[rows[i]['supervised_tokens'] for i in groups[index]]
        group_coefficients(lengths,'token_mean')
        original.append(1/sum(lengths))
    return sum(original)/len(original)


def initial_decision_adjustment(logits,labels,prompt_count,existing_coefficient,target_coefficient):
    """Replace one CE coefficient without renormalizing the other targets.

    This adjustment may be negative; the resulting coefficient remains positive.
    It uses the already computed causal logits, with no extra model forward.
    """
    import torch.nn.functional as F
    if (not 1<=prompt_count<labels.shape[1] or int(labels[0,prompt_count])<0
            or not all(math.isfinite(x) and x>0 for x in [existing_coefficient,target_coefficient])):
        raise ValueError('positive coefficients and supervised initial decision required')
    first=F.cross_entropy(logits[:,prompt_count-1].float(),labels[:,prompt_count])
    return (target_coefficient-existing_coefficient)*first


def tool_log_odds(logits,prompt_tokens,tool_token_id):
    import torch
    scores=logits[0,prompt_tokens-1,:].float()
    others=torch.cat((scores[:tool_token_id],scores[tool_token_id+1:]))
    return scores[tool_token_id]-torch.logsumexp(others,dim=0)


def paired_mode_loss(before,after,margin):
    """One-sided calibration: the pre-update repair state's odds are detached.

    Sequential backward passes need no second retained activation graph.
    This is an asymmetric auxiliary objective, not a symmetric contrast loss.
    """
    import torch.nn.functional as F
    return F.softplus(margin+after-before.detach())


def first_edit_decision(positive,negative):
    """Return a contrast only where both completions share the causal prefix."""
    a,b=positive['input_ids'],negative['input_ids'];start=positive['prompt_token_count']
    if start!=negative['prompt_token_count'] or a[:start]!=b[:start]:
        raise ValueError('counterfactual prompt differs')
    for at,(good,bad) in enumerate(zip(a,b)):
        if good==bad:continue
        if at<start or positive['labels'][at]!=good or negative['labels'][at]!=bad:
            raise ValueError('edit is outside verified supervised completion')
        return dict(target_position=at,good_token=good,bad_token=bad)
    raise ValueError('no contrasted supervised decision')


def edit_contrast_loss(logits,decisions,margin,positive_only=False,logit_offset=0):
    """Pairwise token margin at verified shared prefixes; no negative forward."""
    import torch
    import torch.nn.functional as F
    if type(logit_offset) is not int or logit_offset<0:raise ValueError('invalid logit offset')
    points=sorted({(d['target_position']-logit_offset,d['good_token'],d['bad_token']) for d in decisions})
    if not points:return logits[0,0,0]*0
    losses=[]
    for position,good,bad in points:
        if not 1<=position<logits.shape[1] or not 0<=good<logits.shape[-1] or not 0<=bad<logits.shape[-1] or good==bad:
            raise ValueError('invalid edit contrast')
        scores=logits[0,position-1].float()
        losses.append(-F.log_softmax(scores,dim=-1)[good] if positive_only else F.softplus(margin+scores[bad]-scores[good]))
    return torch.stack(losses).mean()


def mean_adapter_parameters(first,second):
    """Mean matching LoRA parameters, not effective BA weight matrices."""
    if first.keys()!=second.keys() or any(first[k].shape!=second[k].shape for k in first):
        raise ValueError('adapter parameters differ')
    return {k:((first[k].float()+second[k].float())*.5).to(first[k].dtype) for k in first}


def semantic_field_mask(tokenizer,row,program):
    """Locate operator/operand tokens in the exact previously encoded target."""
    rendered=tokenizer.decode(row['input_ids'],skip_special_tokens=False,clean_up_tokenization_spaces=False)
    if hashlib.sha256(rendered.encode()).hexdigest()!=row['rendered_full_sha256']:
        raise ValueError('native rendered target cannot be recovered exactly')
    prefix=tokenizer.decode(row['input_ids'][:row['prompt_token_count']],skip_special_tokens=False,clean_up_tokenization_spaces=False)
    if rendered[len(prefix):].count(program)!=1:raise ValueError('program target not unique')
    encoded=tokenizer(rendered,add_special_tokens=False,return_offsets_mapping=True)
    if encoded['input_ids']!=row['input_ids']:raise ValueError('offset tokenization changed')
    start=rendered.index(program,len(prefix));cursor=0;spans=[]
    for step in task.executor().parse_program(program):
        value=f'{step.op}({step.arg1}, {step.arg2})'
        if not program[cursor:].startswith(value):raise ValueError('noncanonical program fields')
        at=start+cursor
        spans.extend([(at,at+len(step.op)),(at+len(step.op)+1,at+len(step.op)+1+len(step.arg1)),
                      (at+len(step.op)+len(step.arg1)+3,at+len(step.op)+len(step.arg1)+3+len(step.arg2))])
        cursor+=len(value)+2
    return [label!=-100 and any(a<end and b>begin for begin,end in spans)
            for label,(a,b) in zip(row['labels'],encoded['offset_mapping'])]


def semantic_edit_decisions(mask,decisions):
    """Drop structural first divergences; never compare after prefixes differ."""
    return [d for d in decisions if mask[d['target_position']]]


def prepare_paired():
    if (PAIRED/'PLAN.json').exists():raise ValueError('paired attempt already frozen')
    data=read(PAIRED/'DATA.json');rows=data['rows'];pairs=[]
    for i in range(0,len(rows),2):
        repair,closure=rows[i:i+2]
        if repair['boundary_role']!='repair' or closure['boundary_role']!='closure' or repair['pair_id']!=closure['pair_id']:
            raise ValueError('actual repair/closure pairing differs')
        pairs.append([i,i+1])
    if len(pairs)!=11 or len({r['report'] for r in rows})!=11:raise ValueError('eleven source pairs required')
    tok=tokens.load_tokenizer(MODEL);tool_id=tok.encode('<tool_call>',add_special_tokens=False)
    if len(tool_id)!=1:raise ValueError('native tool branch is not a single token')
    tool_id=tool_id[0]
    for a,b in pairs:
        if next(t for t in rows[a]['labels'] if t!=-100)!=tool_id or next(t for t in rows[b]['labels'] if t!=-100)==tool_id:
            raise ValueError('native branch targets differ from the paired roles')
    parent=read(ROOT/'refinement_v2/PLAN.json');warm=Path(parent['warm_start'])
    for name,digest in parent['warm_files'].items():
        if sha(warm/name)!=digest:raise ValueError('shared warm start changed')
    plan=dict(schema='finqa_paired_decision_learning_v1',model_path=str(MODEL),data_sha256=sha(PAIRED/'DATA.json'),
              seed=17,arms=['token_mean','decision_mean','paired_mode'],updates_per_arm=32,
              paired_rows=pairs,schedule=parent['schedule'],learning_rate=2e-4,rank=8,alpha=16,wall_seconds=3600,
              warm_start=str(warm),warm_files=parent['warm_files'],resource_lock=str(study.core.LOCK),
              tool_token_id=tool_id,mode_margin=1.,mode_weight=.1,expected_forward_calls=192,
              components={str(p):sha(p) for p in [Path(__file__),Path(task.__file__),Path(tokens.__file__),Path(study.__file__),HERE.parents[1]/'scripts/graph/research_gpu_guard.py']},
              comparison='Identical 22 rows, pair schedule, warm start, 32 updates and 64 sequential forwards per arm; only loss changes. Paired-mode adds asymmetric post-execution branch calibration to decision-mean CE.',
              scope='Eleven TRAIN sources, 0 new formation. Previous four review reports remain development regression only.',
              deployment='Unchanged native OpenCode reviewer, no branch threshold or hidden-answer trigger at deployment')
    new(PAIRED/'PLAN.json',plan)
    snapshot=PAIRED/'training_sources';snapshot.mkdir()
    for name in plan['components']:(snapshot/Path(name).name).write_bytes(Path(name).read_bytes())
    print(json.dumps(dict(plan_sha256=sha(PAIRED/'PLAN.json'),pairs=len(pairs),arms=plan['arms'],updates=96,forwards=192)))


def prepare_closed():
    """Reuse actual post-execution teacher completions, paired with each repair.

    The action row is reconstructed exactly before adding closure supervision;
    no fresh generation, new reports, or privileged student conditioning.
    """
    source=ROOT/'refinement_v2';target=ROOT/'closed_recovery_v1'
    if target.exists():raise ValueError('closed-recovery candidate already exists')
    original=read(source/'DATA.json');tok=tokens.load_tokenizer(MODEL)
    requests=[Path(p) for p in original['sources'] if p.endswith('.request.json')]
    rows=[];bindings=dict(original['sources']);diagnostics=[]
    def call_binding(call):
        function=call['function'];arguments=function['arguments']
        return (call['id'],function['name'],json.loads(arguments) if isinstance(arguments,str) else arguments)
    for row in original['rows']:
        name=row['teacher_attempt'] if row['phase']=='replay' else 'recovery_training_v1'
        candidates=[p for p in requests if p.parent.parent.name==f"{row['source_index']:03d}" and p.parents[2].name==name]
        if len(candidates)!=1:raise ValueError('repair request not uniquely bound')
        action_request=candidates[0];episode=action_request.parent.parent
        public=read(episode/'inputs/public.json');teacher_text=(episode/'inputs/task.txt').read_text()
        if row['phase']=='replay':
            public_text=(study.prompt(public)+'\n\nContinue the existing student workspace. Use the public task and actual '
                         'failed operations below to repair its latest program with the same execution tool. '
                         'No reference answer is available.\n'+json.dumps({'student_actions':study.recent_actions(study.ROOT/'student'/f"{row['source_index']:03d}")},ensure_ascii=False))
        else:
            ep=next(x for x in read(episode.parent/'PLAN.json')['episodes'] if x['index']==row['source_index'])
            public_text=study.recovery_prompt(public,study.recent_actions(Path(ep['source_folder'])))
        projected=project_request(read(action_request),teacher_text,public_text)
        reconstructed=tokens.encode_completion(projected,row['assistant'],tok,16384)
        if any(reconstructed[k]!=row[k] for k in ['input_ids','labels']):
            raise ValueError('reconstructed repair differs from the executed training row')
        pair_id=name+'/'+str(row['source_index'])
        repair=copy.deepcopy(row);repair.update(boundary_role='repair',pair_id=pair_id)
        teacher_result=read(episode/'RESULT.json')
        if not teacher_result['native_success']:raise ValueError('teacher did not complete the recovery')
        receipts={r['request']:r for r in teacher_result['accounting']['requests']}
        current=int(action_request.name.split('.')[0])
        for request in sorted(action_request.parent.glob('*.request.json')):
            index=int(request.name.split('.')[0])
            if index<=current:continue
            response=request.with_suffix('.response');receipt=receipts[index]
            if sha(request)!=receipt['request_sha256'] or sha(response)!=receipt['response']['body_sha256']:
                raise ValueError('closure wire binding changed')
            if not receipt['response']['complete']:continue
            stopped=any(c.get('finish_reason')=='stop'
                        for line in response.read_bytes().splitlines()
                        if line.startswith(b'data:') and line[5:].strip()!=b'[DONE]'
                        for c in json.loads(line[5:]).get('choices',[]))
            if not stopped:continue
            assistant=sse_assistant(response.read_bytes())
            if assistant['tool_calls'] or not assistant['content']:continue
            final=project_request(read(request),teacher_text,public_text)
            # OpenCode may merge calls and reserialize JSON arguments; the
            # actual ID, function and argument object must still agree.
            if not any(call_binding(call)==call_binding(row['assistant']['tool_calls'][0])
                       for m in final['messages'] if m.get('role')=='assistant'
                       for call in m.get('tool_calls') or []):
                raise ValueError('closure does not follow the actual supervised repair: '+pair_id)
            if not any(m.get('role')=='tool' for m in final['messages']):raise ValueError('closure has no execution feedback')
            encoded=tokens.encode_completion(final,assistant,tok,16384,completion_kind='closure')
            uniform=[float(t!=-100) for t in encoded['labels']]
            closure=dict(**encoded,weights_by_arm={arm:list(uniform) for arm in row['weights_by_arm']},
                         phase='closure',source_phase=row['phase'],boundary_role='closure',pair_id=pair_id,
                         report=row['report'],source_index=row['source_index'],assistant=assistant,
                         source_request=str(request),source_response=str(response),
                         projection='actual post-repair teacher completion; privileged user task replaced, public execution retained')
            rows.extend([repair,closure]);bindings[str(request)]=sha(request);bindings[str(response)]=sha(response)
            diagnostics.append(dict(pair_id=pair_id,repair_tokens=row['supervised_tokens'],closure_tokens=encoded['supervised_tokens']))
            break
        else:raise ValueError('no linked actual teacher closure for '+pair_id)
    if len(rows)!=22:raise ValueError('expected eleven linked repair/closure pairs')
    target.mkdir(mode=0o700)
    data=dict(rows=rows,sources=bindings,tokenizer=original['tokenizer'],diagnostics=diagnostics,
              parent_data_sha256=sha(source/'DATA.json'),compiler_sha256=sha(Path(__file__)),
              components={str(p):sha(p) for p in [Path(__file__),Path(tokens.__file__),Path(study.__file__)]},
              scope='Same eleven TRAIN reports; closed-recovery candidate data, no training/effect claim; new evaluation reports excluded')
    new(target/'DATA.json',data)
    print(json.dumps(dict(rows=len(rows),pairs=len(diagnostics),diagnostics=diagnostics,data_sha256=sha(target/'DATA.json'))))


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
    from scripts.graph.research_gpu_guard import gpu_lease
    root=ROOT if root is None else Path(root)
    if sha(root/'PLAN.json')!=digest or (root/'LIVE.json').exists():raise ValueError('training plan/attempt')
    plan=read(root/'PLAN.json');assert sha(root/'DATA.json')==plan['data_sha256']
    if plan.get('completion_logits_only') and plan.get('step_preference'):
        raise ValueError('completion-only head is not implemented for rejected preference forwards')
    for path,value in plan['components'].items():
        if sha(path)!=value:raise ValueError('training component changed')
    rows=read(root/'DATA.json')['rows'];started=time.monotonic()
    inherited=copy.deepcopy(plan.get('inherited_arms',{}))
    if set(inherited)&set(plan['arms']):raise ValueError('inherited arm cannot be retrained')
    for arm,item in inherited.items():
        for name,value in item['adapter_files'].items():
            if sha(root/arm/name)!=value:raise ValueError('inherited adapter changed')
    state=dict(status='RUNNING',pid=__import__('os').getpid(),optimizer_updates=0,forward_calls=0,
               training_sequence_tokens=0,supervised_tokens=0,arms=inherited,http_model_requests=0,
               inherited_arm_names=list(inherited))
    if plan.get('completion_logits_only'):
        state.update(completion_logits_only=True,vocabulary_logit_positions=0)
    model=None
    try:
        with gpu_lease(), Path(plan['resource_lock']).open('r+') as lease:
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
            preference=None
            if plan.get('step_preference'):
                from finqa_learning_controls import StepPreference
                preference=StepPreference(model,rows,plan,root,state)
            for arm in plan['arms']:
                with torch.no_grad():
                    for name,param in model.named_parameters():
                        if name in initial:param.copy_(initial[name])
                optimizer=torch.optim.AdamW([p for p in model.parameters() if p.requires_grad],lr=plan['learning_rate'])
                model.train();losses=[];mode_diagnostics=[];edit_diagnostics=[];arm_start=time.monotonic()
                for update in range(plan['updates_per_arm']):
                    if time.monotonic()-started>plan['wall_seconds']:raise TimeoutError('finite training wall cap')
                    index=plan['schedule'][update] if 'schedule' in plan else update%len(rows)
                    batch=[rows[i] for i in plan['paired_rows'][index]] if plan.get('paired_rows') else [rows[index]]
                    batch=[conditioning_row(row,arm,allow_repair=arm in plan.get('same_target_context_arms',[])) for row in batch]
                    coefficients=group_coefficients([r['supervised_tokens'] for r in batch],plan.get('pair_objective',arm)) if plan.get('paired_rows') else [1.]
                    optimizer.zero_grad(set_to_none=True)
                    total=0.;odds_values=[];before=None;auxiliary=0.
                    for at,(row,coefficient) in enumerate(zip(batch,coefficients)):
                        work=preference.before_row(model,row,arm) if preference else []
                        offset,kept=completion_logit_window(row) if plan.get('completion_logits_only') else (0,row['sequence_length'])
                        x=torch.tensor([row['input_ids']],device='cuda');y=torch.tensor([row['labels'][offset:]],device='cuda')
                        weights=([float(t!=-100) for t in row['labels']] if plan.get('paired_rows') else
                                 row['weights_by_arm'][arm] if 'weights_by_arm' in row else
                                 row['weights'] if arm=='operand_repair' else [float(t!=-100) for t in row['labels']])
                        if offset and any(weight!=0 for weight in weights[:offset]):raise ValueError('unmasked prefix weights')
                        w=torch.tensor([weights[offset:]],device='cuda')
                        head={'logits_to_keep':kept} if plan.get('completion_logits_only') else {}
                        logits=model(input_ids=x,use_cache=False,**head).logits
                        prompt_count=row['prompt_token_count']-offset
                        value=coefficient*weighted_loss(logits,y,w)
                        if work:
                            term=preference.positive(logits,row,work)
                            edit_diagnostics.append(dict(update=update,decisions=len(work),loss=float(term.detach())))
                            value=value+term;del term
                        if at==0 and 'initial_decision_coefficient' in plan:
                            value=value+initial_decision_adjustment(logits,y,prompt_count,
                                coefficient/row['supervised_tokens'],plan['initial_decision_coefficient'])
                        decisions=row.get('edit_contrasts',{}).get(arm,[])
                        if decisions:
                            contrast=edit_contrast_loss(logits,decisions,plan['edit_margin'],
                                                       positive_only=arm in plan.get('positive_only_arms',['edit_positive']),logit_offset=offset)
                            edit_diagnostics.append(dict(update=update,decisions=len(decisions),loss=float(contrast.detach())))
                            value=value+plan['edit_weight']*contrast
                            del contrast
                        if plan.get('paired_rows') and len(batch)==2:
                            odds=tool_log_odds(logits,prompt_count,plan['tool_token_id'])
                            odds_values.append(float(odds.detach()))
                            if at==0:before=odds.detach()
                            elif arm=='paired_mode':
                                penalty=paired_mode_loss(before,odds,plan['mode_margin'])
                                auxiliary=float(penalty.detach());value=value+plan['mode_weight']*penalty
                            del odds
                        if not torch.isfinite(value):raise ValueError('nonfinite loss')
                        total+=float(value.detach());value.backward()
                        state['forward_calls']+=1;state['training_sequence_tokens']+=row['sequence_length'];state['supervised_tokens']+=row['supervised_tokens']
                        if plan.get('completion_logits_only'):state['vocabulary_logit_positions']+=logits.shape[1]
                        del x,y,w,value,logits
                        if work:preference.backward_rejected(model,work)
                        if at==1 and arm=='paired_mode':del penalty
                    torch.nn.utils.clip_grad_norm_([p for p in model.parameters() if p.requires_grad],1.)
                    optimizer.step();losses.append(total);state['optimizer_updates']+=1
                    if odds_values:mode_diagnostics.append(dict(before=odds_values[0],after=odds_values[1],auxiliary=auxiliary))
                    study.publish(root/'LIVE.json',state)
                output=root/arm;model.save_pretrained(output)
                state['arms'][arm]=dict(updates=len(losses),losses=losses,mode_diagnostics=mode_diagnostics,edit_diagnostics=edit_diagnostics,seconds=time.monotonic()-arm_start,
                                       adapter_files={p.name:sha(p) for p in output.iterdir() if p.is_file()})
                del optimizer;gc.collect();torch.cuda.empty_cache()
                study.publish(root/'LIVE.json',state)
            if plan.get('step_preference') and state['forward_calls']!=plan['expected_forward_calls']:
                raise ValueError('matched preference forward count differs')
            state['status']=plan.get('terminal_status') or ('TRAINED_PAIRED_DECISION_ARMS' if plan.get('paired_rows') else 'TRAINED_REFINEMENT_ARMS' if plan.get('warm_start') else 'TRAINED_TWO_DEVELOPMENT_ARMS')
    except BaseException:
        state.update(status='FAILED',error=traceback.format_exc());raise
    finally:
        state['seconds']=time.monotonic()-started
        study.publish(root/'LIVE.json',state);new(root/'RESULT.json',state)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['prepare','train','prepare-refinement','train-refinement','prepare-closed','prepare-paired','train-paired']);p.add_argument('--plan-sha');args=p.parse_args()
    if args.mode=='prepare':prepare()
    elif args.mode=='prepare-refinement':prepare_refinement()
    elif args.mode=='prepare-closed':prepare_closed()
    elif args.mode=='prepare-paired':prepare_paired()
    else:train(args.plan_sha,PAIRED if args.mode=='train-paired' else REFINEMENT if args.mode=='train-refinement' else ROOT)
