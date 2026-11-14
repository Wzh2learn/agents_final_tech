"""Matched training controls compiled from the same actual FinQA teacher targets.

Preparation is CPU-only. Step-DPO refers to the step preference objective
(https://arxiv.org/html/2406.18629v1#S3.SS1), not a reproduction of its data
collection pipeline. No new model requests or adapter training occur here.
"""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
import shlex

import finqa_learning as learning

study=learning.study
task=learning.task
tokens=learning.tokens
read=learning.read
sha=learning.sha
ROOT=learning.ROOT/'semantic_correction_v1/expanded_v1'


def program_of(assistant):
    call=assistant['tool_calls'][0]
    if len(assistant['tool_calls'])!=1 or call['function']['name']!='bash':
        raise ValueError('one native program call required')
    arguments=call['function']['arguments']
    command=json.loads(arguments)['command'] if isinstance(arguments,str) else arguments['command']
    argv=shlex.split(command)
    return argv[argv.index('--program')+1]


def source_requests(repair,closure):
    closing=Path(closure['source_request'])
    if repair.get('source_request'):
        return Path(repair['source_request']),closing
    matches=[]
    for response in closing.parent.glob('*.request.response'):
        if int(response.name.split('.')[0])>=int(closing.name.split('.')[0]):continue
        if learning.sse_assistant(response.read_bytes())==repair['assistant']:
            matches.append(response.with_suffix('.json'))
    if len(matches)!=1:raise ValueError('original repair response is not uniquely bound')
    return matches[0],closing


def recovery_text(row,folder,public):
    """Recover the historical public projection, then verify its encoded preimage."""
    if row.get('phase')=='replay':
        source=study.ROOT/'student'/f"{row['source_index']:03d}"
        return (study.prompt(public)+'\n\nContinue the existing student workspace. Use the public task and actual '
                'failed operations below to repair its latest program with the same execution tool. '
                'No reference answer is available.\n'+json.dumps({'student_actions':study.recent_actions(source)},ensure_ascii=False))
    ep=next(e for e in read(folder.parent/'PLAN.json')['episodes'] if e['index']==row['source_index'])
    return study.recovery_prompt(public,study.recent_actions(Path(ep['source_folder'])))


def step_positions(tokenizer,row,program,index,first_divergence):
    rendered=tokenizer.decode(row['input_ids'],skip_special_tokens=False,clean_up_tokenization_spaces=False)
    encoded=tokenizer(rendered,add_special_tokens=False,return_offsets_mapping=True)
    if encoded['input_ids']!=row['input_ids']:raise ValueError('step offset tokenization changed')
    prefix=tokenizer.decode(row['input_ids'][:row['prompt_token_count']],skip_special_tokens=False,clean_up_tokenization_spaces=False)
    if rendered[len(prefix):].count(program)!=1:raise ValueError('step program is not unique')
    steps=task.executor().parse_program(program)
    if not 0<=index<len(steps):raise ValueError('no rejected operation for this step')
    chunks=[f'{s.op}({s.arg1}, {s.arg2})' for s in steps]
    if ', '.join(chunks)!=program:raise ValueError('noncanonical operation spans')
    begin=rendered.index(program,len(prefix))+sum(len(x)+2 for x in chunks[:index])
    end=begin+len(chunks[index])
    selected=[i for i,(a,b) in enumerate(encoded['offset_mapping'])
              if i>=first_divergence and row['labels'][i]!=-100 and a<end and b>begin]
    if not selected or selected[0]!=first_divergence:
        raise ValueError('step preference does not start at its shared-prefix divergence')
    return selected


def selected_logprob(logits,input_ids,positions):
    """Autoregressive positions refer to target tokens, not their own logits."""
    import torch
    if not positions or min(positions)<1 or max(positions)>=logits.shape[1]:
        raise ValueError('invalid preference positions')
    at=torch.tensor(positions,device=logits.device)
    target=torch.tensor([input_ids[i] for i in positions],device=logits.device)
    return logits[0,at-1].float().log_softmax(-1).gather(-1,target[:,None]).sum()


def step_dpo_loss(chosen,rejected,reference_gap,beta):
    import torch
    import torch.nn.functional as F
    if beta<=0:raise ValueError('positive DPO beta required')
    reference=torch.as_tensor(reference_gap,device=chosen.device,dtype=chosen.dtype).detach()
    return F.softplus(-beta*(chosen-rejected-reference))


def prepare():
    out=ROOT/'controls_v1'
    if out.exists():raise ValueError('control data already prepared')
    data=read(ROOT/'DATA.json');tokenizer=tokens.load_tokenizer(learning.MODEL)
    old=read(ROOT.parent/'DATA.json')
    if sha(ROOT.parent/'DATA.json')!=data['parent_data_sha256']:raise ValueError('original contrast sources changed')
    old_edits={x['pair_id']:x['edits'] for x in old['diagnostics']}
    new_edits={'expanded_teacher27b/'+str(x['index']):x['edits'] for x in data['diagnostics']}
    edits={**old_edits,**new_edits};success=[];preferences=[];sources={};skipped=[]
    for a,b in data['paired_rows']:
        repair,closure=data['rows'][a],data['rows'][b]
        requests=source_requests(repair,closure);folder=requests[0].parent.parent
        public=read(folder/'inputs/public.json');private=(folder/'inputs/task.txt').read_text()
        original_text=recovery_text(repair,folder,public)
        projected=None
        for row,q in zip((repair,closure),requests):
            response=q.with_suffix('.response')
            for path in (q,response):
                if data['sources'].get(str(path))!=sha(path):raise ValueError('actual teacher source changed: '+str(path))
                sources[str(path)]=sha(path)
            assistant=learning.sse_assistant(response.read_bytes())
            kind='closure' if row['boundary_role']=='closure' else 'action'
            # Verify the historical projection before constructing the matched clean context.
            original=learning.project_request(read(q),private,original_text)
            encoded=tokens.encode_completion(original,assistant,tokenizer,16384,completion_kind=kind)
            if any(encoded[k]!=row[k] for k in ('input_ids','labels')):
                raise ValueError('historical public conditioning changed')
            if row['boundary_role']=='repair':projected=original
            clean=tokens.encode_completion(learning.project_request(read(q),private,study.prompt(public)),
                                           assistant,tokenizer,16384,completion_kind=kind)
            if [x for x in clean['labels'] if x!=-100]!=[x for x in row['labels'] if x!=-100]:
                raise ValueError('success-context control changed the positive supervised targets')
            clean.update(pair_id=row['pair_id'],boundary_role=row['boundary_role'],report=row['report'],
                         source_request=str(q),source_response=str(response),source_correct=repair['source_correct'])
            success.append(clean)
        program=program_of(repair['assistant'])
        for edit in edits[repair['pair_id']]:
            if not edit['semantic_negative']:continue
            if edit['kind']!='field':
                skipped.append(dict(pair_id=repair['pair_id'],kind=edit['kind'],reason='no existing rejected operation; retain all-pair SFT separately'))
                continue
            negative=copy.deepcopy(repair['assistant']);args=negative['tool_calls'][0]['function']['arguments']
            escaped=json.dumps(program,ensure_ascii=False)[1:-1]
            if args.count(escaped)!=1:raise ValueError('counterfactual program not unique')
            negative['tool_calls'][0]['function']['arguments']=args.replace(escaped,json.dumps(edit['program'],ensure_ascii=False)[1:-1],1)
            rejected=tokens.encode_completion(projected,negative,tokenizer,16384)
            point=learning.first_edit_decision(repair,rejected)
            if point!=edit['decision']:raise ValueError('existing preference decision changed')
            step=int(edit['field'].split(':')[0]);i=point['target_position']
            positions=step_positions(tokenizer,repair,program,step,i)
            rejected_positions=step_positions(tokenizer,rejected,edit['program'],step,i)
            preferences.append(dict(row_index=a,pair_id=repair['pair_id'],field=edit['field'],step=step,
                                    rejected=rejected,chosen_positions=positions,rejected_positions=rejected_positions,
                                    shared_prefix_tokens=i,reference_gap=None))
    out.mkdir(mode=0o700)
    meta=dict(source_data_sha256=sha(ROOT/'DATA.json'),formation_model_requests=0,pairs=len(data['paired_rows']),
              actual_positive_targets_identical=True,scope='TRAIN-only same-target clean-context SFT and matched field-step DPO data. No adapters trained or original-method scores reproduced.')
    learning.new(out/'SUCCESS_CONTEXT_DATA.json',dict(rows=success,paired_rows=data['paired_rows'],sources=sources,**meta))
    learning.new(out/'STEP_PREFERENCE_DATA.json',dict(preferences=preferences,skipped_boundaries=skipped,**meta))
    snapshot=out/'compilation_sources';snapshot.mkdir()
    for path in [Path(__file__),Path(learning.__file__),Path(tokens.__file__),Path(task.__file__)]:
        (snapshot/path.name).write_bytes(path.read_bytes())
    print(json.dumps(dict(pairs=meta['pairs'],rows=len(success),step_pairs=len(preferences),skipped_boundaries=len(skipped),
                          success_data_sha256=sha(out/'SUCCESS_CONTEXT_DATA.json'),step_data_sha256=sha(out/'STEP_PREFERENCE_DATA.json'),
                          model_requests=0,supervised_tokens=sum(r['supervised_tokens'] for r in success))))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['prepare']);p.parse_args();prepare()
