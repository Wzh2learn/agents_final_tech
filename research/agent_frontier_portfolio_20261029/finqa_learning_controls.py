"""Matched training controls compiled from the same actual FinQA teacher targets.

Preparation is CPU-only. Step-DPO refers to the step preference objective
(https://arxiv.org/html/2406.18629v1#S3.SS1), not a reproduction of its data
collection pipeline. No new model requests or adapter training occur here.
"""
from __future__ import annotations

import argparse
import copy
import json
import math
from pathlib import Path
import random
import shlex
import shutil

import finqa_learning as learning

study=learning.study
task=learning.task
tokens=learning.tokens
read=learning.read
sha=learning.sha
ROOT=learning.ROOT/'semantic_correction_v1/expanded_v1'

REVIEW_ONLY_INSTRUCTION=(
    '\n\nThis is a review of an already executed candidate, not a fresh task. '
    'Check the question, evidence, current program and its saved execution feedback. '
    'If you retain the program, finish directly using that feedback; do not rerun an '
    'unchanged program merely to submit it again. If you change the program, execute '
    'the changed program before finishing. Executability alone does not establish '
    'that the program answers the question. No reference answer is available.')


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


def preference_weight(beta,edit_weight,mean_initial_slope):
    """Match the TRAIN initial first-divergence derivative, not parameter norms."""
    if not math.isfinite(beta) or beta<=0 or edit_weight<=0 or not 0<mean_initial_slope<=1:
        raise ValueError('finite positive preference calibration required')
    return 2*edit_weight*mean_initial_slope/beta


class StepPreference:
    """A fixed warm reference and sequential branches for bounded GPU memory."""
    def __init__(self,model,rows,plan,root,state):
        import torch
        self.root=root;self.state=state;self.config=plan['step_preference'];self.beta=self.config['beta'];self.references={}
        if any(isinstance(x,torch.nn.Dropout) and x.p for x in model.modules()) or getattr(model.config,'attention_dropout',0):
            raise ValueError('split-gradient control requires deterministic zero-dropout forwards')
        model.eval()
        with torch.no_grad():
            for row in rows:
                prefs=row.get('step_preferences',[])
                if not prefs:continue
                logits=self.forward(model,row,'reference');chosen={}
                for pref in prefs:
                    value=selected_logprob(logits,row['input_ids'],pref['chosen_positions'])
                    at=pref['shared_prefix_tokens'];good=row['input_ids'][at];bad=pref['rejected']['input_ids'][at]
                    slope=torch.sigmoid(self.config['edit_margin']+logits[0,at-1,bad].float()-logits[0,at-1,good].float())
                    chosen[pref['uid']]=(float(value),float(slope))
                del logits,value,slope
                for pref in prefs:
                    rejected=pref['rejected'];logits=self.forward(model,rejected,'reference')
                    value=selected_logprob(logits,rejected['input_ids'],pref['rejected_positions'])
                    positive,slope=chosen[pref['uid']]
                    self.references[pref['uid']]=dict(gap=positive-float(value),chosen=positive,rejected=float(value),initial_slope=slope)
                    del logits,value
        slopes=[]
        for group in plan['schedule']:
            for index in plan['paired_rows'][group]:
                prefs=rows[index].get('step_preferences',[])
                if prefs:slopes.append(sum(self.references[p['uid']]['initial_slope'] for p in prefs)/len(prefs))
        self.weight=preference_weight(self.beta,self.config['edit_weight'],sum(slopes)/len(slopes))
        learning.new(root/'REFERENCE.json',dict(references=self.references,beta=self.beta,weight=self.weight,
                     mean_initial_slope=sum(slopes)/len(slopes),scope='TRAIN-only fixed warm model; schedule-weighted initial local slope, not a match of full parameter-gradient norms.'))
        state['step_preference_weight']=self.weight;state['reference_sha256']=sha(root/'REFERENCE.json')

    def forward(self,model,row,phase):
        import torch
        self.state['preference_attempted_forwards']=self.state.get('preference_attempted_forwards',0)+1
        learning.study.publish(self.root/'LIVE.json',self.state)
        logits=model(input_ids=torch.tensor([row['input_ids']],device='cuda'),use_cache=False).logits
        self.state['forward_calls']+=1
        key=phase+'_forward_calls';self.state[key]=self.state.get(key,0)+1
        key='reference_sequence_tokens' if phase=='reference' else 'training_sequence_tokens'
        self.state[key]=self.state.get(key,0)+len(row['input_ids'])
        return logits

    def before_row(self,model,row,arm):
        import torch
        work=[]
        if arm!=self.config['arm']:return work
        with torch.no_grad():
            for pref in row.get('step_preferences',[]):
                logits=self.forward(model,pref['rejected'],'preference_nograd')
                value=selected_logprob(logits,pref['rejected']['input_ids'],pref['rejected_positions'])
                work.append(dict(pref=pref,rejected=float(value)))
                del logits,value
        return work

    def positive(self,logits,row,work):
        import torch
        terms=[]
        for item in work:
            pref=item['pref'];chosen=selected_logprob(logits,row['input_ids'],pref['chosen_positions'])
            gap=self.references[pref['uid']]['gap'];rejected=torch.as_tensor(item['rejected'],device=chosen.device)
            terms.append(step_dpo_loss(chosen,rejected,gap,self.beta))
            item['negative_scale']=self.weight/len(work)*self.beta*float(torch.sigmoid(-self.beta*(chosen.detach()-rejected-gap)))
        return self.weight*torch.stack(terms).mean()

    def backward_rejected(self,model,work):
        for item in work:
            pref=item['pref'];row=pref['rejected'];logits=self.forward(model,row,'preference_grad')
            value=selected_logprob(logits,row['input_ids'],pref['rejected_positions'])
            # The coefficient is detached at the same pre-update policy. This
            # is the rejected branch of the joint DPO gradient, counted once.
            (item['negative_scale']*value).backward()
            self.state['preference_chosen_tokens']=self.state.get('preference_chosen_tokens',0)+len(pref['chosen_positions'])
            self.state['preference_rejected_tokens']=self.state.get('preference_rejected_tokens',0)+len(pref['rejected_positions'])
            del logits,value


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


def paired_difference(first,second,draws=20000,seed=17):
    """Resample paired independent filing groups, not their individual requests."""
    if not first or len(first)!=len(second) or draws<2:raise ValueError('complete matched outcomes required')
    values=[int(a)-int(b) for a,b in zip(first,second)];rng=random.Random(seed);n=len(values)
    sampled=sorted(sum(rng.choice(values) for _ in range(n))/n for _ in range(draws))
    def quantile(q):
        x=q*(draws-1);i=int(x)
        return sampled[i]+(sampled[min(i+1,draws-1)]-sampled[i])*(x-i)
    return dict(n=n,mean_difference=sum(values)/n,ci95=[quantile(.025),quantile(.975)],
                first_only=values.count(1),second_only=values.count(-1),ties=values.count(0),draws=draws,seed=seed)


def syntax_gated_replay(source,review):
    """Offline public-validity policy; neither correctness label selects an arm."""
    before={r['index']:r for r in source};after={r['index']:r for r in review}
    if len(before)!=len(source) or len(after)!=len(review) or before.keys()!=after.keys():
        raise ValueError('complete unique paired states required')
    decisions={i:after[i] if not row['valid'] else row for i,row in before.items()}
    invoked=[i for i,row in before.items() if not row['valid']]
    return dict(native_success=sum(r['native_success'] for r in decisions.values()),
                selected_review_indices=invoked,
                posts=sum(r['posts'] for r in source)+sum(after[i]['posts'] for i in invoked),
                known_tokens=sum(r['known_tokens'] for r in source)+sum(after[i]['known_tokens'] for i in invoked),
                scope='Deterministic offline policy replay on actual paired continuations; not an additional online run or the physical research bill.')


def prepare_prompt_review():
    """Strong simple prompt control, on all 32 fixed public first-pass states."""
    import run_finqa_learning_native as native
    out=ROOT/'controls_v1/review_prompt_v1'
    if out.exists():raise ValueError('prompt-control attempt already exists')
    original=read(ROOT/'dev_review_v1/PLAN.json')
    if read(ROOT/'dev_review_v1/RESULT.json')['status']!='FINQA_EXPANDED_DEV_REVIEW_RETURNED':
        raise ValueError('original comparison must be terminal')
    out.mkdir();episodes=[];arms=['closed_sft','edit_all_negative']
    order=list(arms);random.Random(17).shuffle(order)
    for ep in read(ROOT/'dev_firstpass_v1/PLAN.json')['episodes']:
        source=Path(ep['folder'])
        public=read(source/'inputs/public.json')
        text=study.recovery_prompt(public,study.recent_actions(source))+REVIEW_ONLY_INSTRUCTION
        for arm in arms:
            target=out/arm/f"{ep['index']:03d}";target.mkdir(parents=True)
            shutil.copytree(source/'inputs',target/'inputs');shutil.copytree(source/'work',target/'work')
            (target/'dependencies').mkdir();(target/'inputs/task.txt').write_text(text)
            episodes.append(dict(ep,arm=arm,folder=str(target),task_sha256=sha(target/'inputs/task.txt')))
    shutil.copyfile(ROOT/'dev_firstpass_v1/LABELS_PRIVATE.json',out/'LABELS_PRIVATE.json')
    plan=dict(original)
    plan.update(schema='finqa_review_instruction_control_v1',episodes=episodes,arms=arms,arm_order=order,
                terminal_status='FINQA_CLEAR_REVIEW_RETURNED',max_posts=len(episodes)*study.CAPS['posts'],
                components={**native.expanded_runtime()['components'],str(Path(__file__)):sha(__file__)},
                comparison='Same 32 source states, weights and original recovery prompt plus one shared review-only clarification; two unchanged trained adapters. Review all states without a hidden-answer trigger.',
                prediction='Clarifying that an unchanged, already executed program may terminate can reduce repeated execution and wrong edits. Any improvement here is a prompt baseline, not a new training mechanism.')
    learning.new(out/'PLAN.json',plan);snapshot=out/'executed_sources';snapshot.mkdir()
    for path in plan['components']:(snapshot/Path(path).name).write_bytes(Path(path).read_bytes())
    print(json.dumps(dict(plan_sha256=sha(out/'PLAN.json'),episodes=len(episodes),max_posts=plan['max_posts'])))


def prepare_training_controls():
    """Same positive targets and warm start; clean context vs step preferences."""
    import run_finqa_learning_native as native
    out=ROOT/'controls_v1/matched_training_v1'
    if out.exists():raise ValueError('matched controls already prepared')
    old=read(ROOT/'PLAN.json');data=read(ROOT/'DATA.json')
    clean_path=out.parent/'SUCCESS_CONTEXT_DATA.json';pref_path=out.parent/'STEP_PREFERENCE_DATA.json'
    clean=read(clean_path);preferences=read(pref_path)
    if sha(ROOT/'DATA.json')!=old['data_sha256'] or clean['source_data_sha256']!=sha(ROOT/'DATA.json') or preferences['source_data_sha256']!=sha(ROOT/'DATA.json'):
        raise ValueError('compiled control sources changed')
    if len(clean['rows'])!=len(data['rows']) or len(preferences['preferences'])!=35:raise ValueError('matched control counts differ')
    fields={'input_ids','attention_mask','labels','prompt_token_count','sequence_length','supervised_tokens','assistant_end_index',
            'prefix_token_alignment_verified','rendered_prefix_sha256','rendered_full_sha256','template_adaptations','loss_scope'}
    for row,target in zip(data['rows'],clean['rows']):
        row['edit_contrasts']={};row['conditioning_by_arm']={'success_context_sft':{k:v for k,v in target.items() if k in fields}}
        learning.conditioning_row(row,'success_context_sft',allow_repair=True)
    for index,pref in enumerate(preferences['preferences']):
        if pref['reference_gap'] is not None:raise ValueError('unexpected precomputed reference')
        data['rows'][pref['row_index']].setdefault('step_preferences',[]).append(dict(pref,uid=f'p{index:04d}'))
    refs=len({p['row_index'] for p in preferences['preferences']})+len(preferences['preferences'])
    repeated=sum(sum(len(data['rows'][i].get('step_preferences',[])) for i in old['paired_rows'][g]) for g in old['schedule'])
    data.update(scope='Same 60 teacher targets; clean public context only for success_context_sft; original recovery prefix plus 35 step preferences for step_dpo. No new formation calls.')
    out.mkdir(mode=0o700);learning.new(out/'DATA.json',data)
    components=[Path(__file__),Path(learning.__file__),Path(learning.tokens.__file__),Path(task.__file__),Path(study.__file__),study.REPO/'scripts/graph/research_gpu_guard.py']
    plan=dict(old, schema='finqa_matched_training_controls_v1',arms=['success_context_sft','step_dpo'],data_sha256=sha(out/'DATA.json'),
              same_target_context_arms=['success_context_sft'],expected_forward_calls=384+2*repeated+refs,wall_seconds=10800,
              step_preference=dict(arm='step_dpo',beta=.4,edit_weight=old['edit_weight'],edit_margin=old['edit_margin'],
                                   weight_rule='2 * edit_weight * TRAIN schedule-mean initial sigmoid(edit_margin - local_good_minus_bad) / beta',
                                   backward='Sequential exact first derivatives with a rejected no-grad prepass; extra forwards are implementation cost, not intrinsic Step-DPO cost.'),
              source_control_data_sha256={str(p):sha(p) for p in (clean_path,pref_path)},
              terminal_status='TRAINED_MATCHED_CONTROL_ARMS',components={str(p):sha(p) for p in components},
              comparison='Two controls, each with the same 30 groups, 60 positive targets, warm adapter and 96-update schedule as original recovery/negative training. Success-context SFT changes conditioning. Step-DPO core is adapted with the shared positive-CE anchor, fixed warm reference and beta .4; not the original paper data pipeline.',
              scope='TRAIN-only, one predetermined recipe; positive supervised targets match, step negatives and reference compute are reported separately.',
              next='Freeze the execution-negative primary candidate and necessary controls before enabling reserved confirmation filings.')
    learning.new(out/'PLAN.json',plan);snapshot=out/'training_sources';snapshot.mkdir()
    for p in components:(snapshot/p.name).write_bytes(p.read_bytes())
    parent=ROOT/'dev_firstpass_v1';target=out/'native_v1';target.mkdir()
    source=read(parent/'PLAN.json');template=read(ROOT/'dev_review_v1/PLAN.json');episodes=[];sources=[]
    for ep in source['episodes']:
        original=Path(ep['folder']);text=study.recovery_prompt(read(original/'inputs/public.json'),study.recent_actions(original))
        sources.append(dict(ep,result_sha256=sha(original/'RESULT.json'),work_tree=study.core.tree(original/'work')))
        for arm in plan['arms']:
            folder=target/arm/f"{ep['index']:03d}";folder.mkdir(parents=True)
            shutil.copytree(original/'inputs',folder/'inputs');shutil.copytree(original/'work',folder/'work');(folder/'dependencies').mkdir()
            (folder/'inputs/task.txt').write_text(text);episodes.append(dict(ep,arm=arm,folder=str(folder),task_sha256=sha(folder/'inputs/task.txt')))
    shutil.copyfile(parent/'LABELS_PRIVATE.json',target/'LABELS_PRIVATE.json');order=list(plan['arms']);random.Random(17).shuffle(order)
    template.update(schema='finqa_matched_controls_native_v1',episodes=episodes,arms=plan['arms'],arm_order=order,source_episodes=sources,
                    training_root=str(out),training_plan_sha256=sha(out/'PLAN.json'),required_training_status=plan['terminal_status'],
                    terminal_status='FINQA_MATCHED_CONTROLS_RETURNED',max_posts=len(episodes)*study.CAPS['posts'],
                    components={**native.expanded_runtime()['components'],str(Path(learning.__file__)):sha(learning.__file__)})
    learning.new(target/'PLAN.json',template)
    print(json.dumps(dict(plan_sha256=sha(out/'PLAN.json'),data_sha256=sha(out/'DATA.json'),updates=192,forwards=plan['expected_forward_calls'],reference_forwards=refs,rejected_prepass_and_backward=2*repeated,positive_supervised_tokens=33710,review_plan_sha256=sha(target/'PLAN.json'),review_episodes=len(episodes),max_posts=template['max_posts'])))


def planned_result_key(result,expected):
    """The older strong-model runner omits arm; bind its unique frozen role."""
    if 'arm' in result:return result['arm'],result['index']
    matches=[key for key in expected if key[1]==result['index']]
    if len(matches)!=1:raise ValueError('missing result role is ambiguous in PLAN')
    return matches[0]


def inspect_batch(folder,status):
    """Re-grade saved programs and reconcile actual request/response evidence."""
    from scripts.graph.research_school_gateway import usage_from_body
    folder=Path(folder);plan=read(folder/'PLAN.json');result=read(folder/'RESULT.json')
    if result['status']!=status or result['plan_sha256']!=sha(folder/'PLAN.json'):
        raise ValueError('complete bound native result required')
    label_path=Path(plan.get('private_labels_path',folder/'LABELS_PRIVATE.json'))
    if sha(label_path)!=plan['private_labels_sha256']:raise ValueError('labels changed')
    labels=read(label_path)
    expected={(e['arm'],e['index']):e for e in plan['episodes']};seen=set();rows=[];inferred_roles=0
    if len(expected)!=len(plan['episodes']):raise ValueError('duplicate planned task')
    for r in result['episodes']:
        key=planned_result_key(r,expected);inferred_roles+='arm' not in r
        if key in seen or key not in expected:raise ValueError('duplicate/unplanned result')
        seen.add(key);ep=expected[key];case=Path(ep['folder']);label=labels[r['index']]
        if label['id']!=r['id'] or sha(case/'inputs/public.json')!=ep['public_sha256']:
            raise ValueError('case identity changed')
        graded=task.grade(r['submitted_program'],read(case/'inputs/public.json'),label['exe_ans'])
        if any(graded[k]!=r[k] for k in ('execution_correct','program_valid')):
            raise ValueError('saved program grade changed')
        if r['native_success']!=(graded['execution_correct'] and r['agent_completed']):
            raise ValueError('native completion predicate changed')
        ac=r['accounting'];total=known=unknown=prompt=completion=cached=cache_unknown=0
        for request in ac['requests']:
            prefix=case/'wire'/f"{request['request']:05d}.request"
            q=prefix.with_suffix('.request.json');response=prefix.with_suffix('.request.response')
            if sha(q)!=request['request_sha256'] or sha(response)!=request['response']['body_sha256']:
                raise ValueError('wire evidence changed')
            usage=usage_from_body(response.read_bytes());total+=1
            if usage is None:unknown+=1
            else:
                if usage!=request['response']['usage']:raise ValueError('usage disagrees with raw response')
                known+=usage['total_tokens'];prompt+=usage['prompt_tokens'];completion+=usage['completion_tokens']
                details=usage.get('prompt_tokens_details') or {}
                cache=details.get('cached_tokens',usage.get('prompt_cache_hit_tokens'))
                if type(cache) is int and 0<=cache<=usage['prompt_tokens']:cached+=cache
                else:cache_unknown+=1
        prior_unknown=ac['unknown_usage_requests']
        if (total!=ac['actual_forwarded_posts'] or known!=ac['provider_total_tokens_known']
                or unknown!=(len(prior_unknown) if isinstance(prior_unknown,list) else prior_unknown)):
            raise ValueError('request accounting does not reconcile')
        witness=case/'work/executions.jsonl'
        executions=[json.loads(x) for x in witness.read_text().splitlines()] if witness.exists() else []
        observed=any(x['program']==r['submitted_program'] and x['execution']['status']=='executed' for x in executions)
        rows.append(dict(arm=key[0],index=key[1],id=r['id'],report=ep['report'],answer_correct=r['execution_correct'],
                         native_success=r['native_success'],normal_exit=r['agent_completed'],valid=r['program_valid'],
                         execution_witness=observed,posts=total,known_tokens=known,unknown_requests=unknown,
                         prompt_tokens_known=prompt,completion_tokens_known=completion,cached_input_known=cached,
                         cache_unknown_requests=cache_unknown+unknown,
                         noncached_input_tokens=prompt-cached if not cache_unknown and not unknown else None,
                         actor_seconds=r['actor']['seconds'],wire_hashes=total*2))
    if seen!=set(expected):raise ValueError('unexecuted planned cases must not disappear from final analysis')
    output=dict(plan_sha256=sha(folder/'PLAN.json'),result_sha256=sha(folder/'RESULT.json'),rows=rows)
    if inferred_roles:output['roles_from_unique_plan']=inferred_roles
    return output


def analyze():
    source=inspect_batch(ROOT/'dev_firstpass_v1','FINQA_EXPANDED_DEV_FIRSTPASS_RETURNED')
    review=inspect_batch(ROOT/'dev_review_v1','FINQA_EXPANDED_DEV_REVIEW_RETURNED')
    before={r['index']:r for r in source['rows']}
    if len({tuple(r['report'].split('/')[:2]) for r in before.values()})!=len(before):
        raise ValueError('bootstrap units must be independent filing groups')
    names=read(ROOT/'PLAN.json')['arms'];groups={name:sorted([r for r in review['rows'] if r['arm']==name],key=lambda r:r['index']) for name in names}
    result={};vectors={};indices=sorted(before)
    for name,rows in groups.items():
        if [r['index'] for r in rows]!=indices:raise ValueError('review cohorts differ')
        correct=[before[r['index']]['answer_correct'] for r in rows]
        native=[before[r['index']]['native_success'] for r in rows]
        n=len(rows);vectors[name]=[r['native_success'] for r in rows]
        result[name]=dict(n=n,answer_correct=sum(r['answer_correct'] for r in rows),native_success=sum(vectors[name]),
                          normal_exit=sum(r['normal_exit'] for r in rows),valid=sum(r['valid'] for r in rows),
                          native_with_execution_witness=sum(r['native_success'] and r['execution_witness'] for r in rows),
                          source_correct=sum(correct),correct_retained=sum(c and r['answer_correct'] for c,r in zip(correct,rows)),
                          original_wrong_recovered=sum(not c and r['answer_correct'] for c,r in zip(correct,rows)),
                          source_native=sum(native),native_recovered=sum(not c and r['native_success'] for c,r in zip(native,rows)),
                          posts=sum(r['posts'] for r in rows),known_tokens=sum(r['known_tokens'] for r in rows),
                          unknown_requests=sum(r['unknown_requests'] for r in rows),actor_seconds=sum(r['actor_seconds'] for r in rows),
                          prompt_tokens_known=sum(r['prompt_tokens_known'] for r in rows),completion_tokens_known=sum(r['completion_tokens_known'] for r in rows),
                          cached_input_known=sum(r['cached_input_known'] for r in rows),cache_unknown_requests=sum(r['cache_unknown_requests'] for r in rows))
        result[name]['whole_policy_posts']=result[name]['posts']+sum(r['posts'] for r in before.values())
        result[name]['whole_policy_known_tokens']=result[name]['known_tokens']+sum(r['known_tokens'] for r in before.values())
    contrasts={name+' minus closed_sft':paired_difference(vectors[name],vectors['closed_sft']) for name in names if name!='closed_sft'}
    for name in ('edit_field_positive','edit_all_negative'):
        contrasts['edit_field_negative minus '+name]=paired_difference(vectors['edit_field_negative'],vectors[name])
    physical=source['rows']+review['rows']
    output=dict(schema='finqa_expanded_native_comparison_v1',source=source,review=review,arms=result,paired_native_differences=contrasts,
                physical=dict(episodes=len(physical),posts=sum(r['posts'] for r in physical),known_tokens=sum(r['known_tokens'] for r in physical),
                              unknown_requests=sum(r['unknown_requests'] for r in physical),wire_hashes=sum(r['wire_hashes'] for r in physical)),
                scope='Exploratory fixed 32-filing cohort, one sampling seed; intervals resample filing groups and do not measure repeated-model-seed variability. No multiplicity-adjusted significance claim. Common first pass billed once physically.')
    path=ROOT/'ANALYSIS.json'
    if path.exists():
        if read(path)!=output:raise ValueError('existing analysis differs; preserve it and name an amendment')
    else:learning.new(path,output)
    print(json.dumps(dict(arms=result,paired_native_differences=contrasts,physical=output['physical'],analysis_sha256=sha(path))))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['prepare','analyze','prepare-prompt-review','prepare-training-controls','train-controls']);p.add_argument('--plan-sha');args=p.parse_args()
    if args.mode=='prepare':prepare()
    elif args.mode=='prepare-prompt-review':prepare_prompt_review()
    elif args.mode=='prepare-training-controls':prepare_training_controls()
    elif args.mode=='train-controls':learning.train(args.plan_sha,ROOT/'controls_v1/matched_training_v1')
    else:analyze()
