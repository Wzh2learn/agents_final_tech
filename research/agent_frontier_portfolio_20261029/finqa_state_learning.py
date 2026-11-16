"""Matched corrective learning on witnessed public program states.

Keep the existing retention/repair targets. Ordinary SFT and executed-error
branch contrast share one state view; a frozen retention adapter is a prompt
control. No hidden correctness flag enters the public state or deployment.
"""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
import random
import re
import shutil

import finqa_learning_controls as controls
import run_finqa_learning_native as native

learning=controls.learning
study=controls.study
task=controls.task
tokens=controls.tokens
read=controls.read
sha=controls.sha
ROOT=controls.ROOT/'controls_v1/state_view_v2'
EXPANDED=controls.ROOT/'state_learning_expanded_v1'
PAIRED_STATES=EXPANDED/'completion_head_v1/paired_state_negatives_v1'


def call_binding(call):
    args=call['function']['arguments']
    return call['id'],call['function']['name'],json.loads(args) if isinstance(args,str) else args


def verified_teacher_pair(records,program,witnesses,prior_count):
    """Select a witnessed correct action and its real later closing request.

    An earlier unsuccessful or inspection request is not silently treated as
    the recovery target. Retention and repair both keep their actual tool IDs.
    """
    if not any(w.get('program')==program and w.get('execution',{}).get('status')=='executed'
               for w in witnesses[prior_count:]):raise ValueError('no newly executed final program')
    last=len(records)-1;final=records[last]['assistant']
    if final.get('tool_calls') or not final.get('content','').strip():raise ValueError('no final text response')
    candidates=[]
    for index,row in enumerate(records[:last]):
        try:matches=controls.program_of(row['assistant'])==program
        except (KeyError,ValueError,IndexError):continue
        if matches:candidates.append(index)
    if not candidates:raise ValueError('no actual final-program tool call')
    index=candidates[-1];call=records[index]['assistant']['tool_calls'][0];messages=records[last]['request']['messages']
    if not any(call_binding(c)==call_binding(call) for m in messages for c in m.get('tool_calls') or []):
        raise ValueError('closing request lost the actual successful call')
    if not any(m.get('role')=='tool' and m.get('tool_call_id')==call['id'] for m in messages):
        raise ValueError('closing request lacks its returned feedback')
    return index,last


def clean_success_request(request,private_text,public_text,action):
    """A fresh success trajectory contains the verified call and its feedback."""
    fresh=fresh_request(request,private_text,public_text);call=action['tool_calls'][0]
    messages=request['messages'];matched=[]
    for i,message in enumerate(messages):
        if any(call_binding(c)==call_binding(call) for c in message.get('tool_calls') or []):matched.append(i)
    if len(matched)!=1:raise ValueError('successful call history is not unique')
    returned=[m for m in messages[matched[0]+1:] if m.get('role')=='tool' and m.get('tool_call_id')==call['id']]
    if len(returned)!=1:raise ValueError('successful call feedback is not unique')
    fresh['messages']+=copy.deepcopy([messages[matched[0]],returned[0]])
    if any(k in json.dumps(fresh['messages']) for k in ('training_reference_program','training_reference_execution_answer')):
        raise ValueError('privileged labels in success conditioning')
    return fresh


def public_execution_state(program,execution,witnesses,actions):
    """A public execution value is not the benchmark's expected answer.

    A missing submission has no executed value: retain actual stderr instead
    of presenting a host re-grading error as an observed tool response.
    """
    if any(key in json.dumps(execution) for key in
           ('execution_correct','native_success','source_correct','training_reference','exe_ans')):
        raise ValueError('private correctness field in execution feedback')
    if program is None:
        return dict(current_program=None,execution_feedback=None,
                    last_tool_feedback=actions[-1].get('output') if actions else None)
    if not any(w.get('program')==program and w.get('execution')==execution for w in witnesses):
        raise ValueError('submitted program lacks matching actual execution')
    return dict(current_program=program,execution_feedback=copy.deepcopy(execution))


def state_from_folder(folder):
    folder=Path(folder);result=read(folder/'RESULT.json');path=folder/'work/executions.jsonl'
    witnesses=[json.loads(x) for x in path.read_text().splitlines()] if path.exists() else []
    return public_execution_state(result['submitted_program'],result['public_execution'],
                                  witnesses,study.recent_actions(folder))


def review_prompt(public,state, *, terminal_program=False):
    decision = ('Retain the current program by declaring it unchanged, or declare a corrected replacement before finishing. '
                if terminal_program else
                'Retain the current program if appropriate and finish, or correct and execute it before finishing. ')
    initial = study.prompt(public,terminal_program=True) if terminal_program else study.prompt(public)
    return (initial+'\n\nReview the existing submitted program using the public state snapshot below. '
            'The execution feedback is the observed result of that program, not an answer-correctness label. '
            'Check its quantities, periods, operands and references against the question and report. '
            +decision+
            'No reference answer is available.\n'+json.dumps(state,ensure_ascii=False))


def program_declaration(program):
    """Render a derived TRAIN action using the unchanged deployment grammar.

    This checks representation only; callers must bind the program to its
    actual successful execution before using it as a supervision target.
    """
    if (not isinstance(program,str) or not program.strip() or len(program)>8192
            or '\n' in program or '\r' in program or program!=program.strip()
            or program.startswith(('"',"'",'`'))):
        raise ValueError('one unwrapped program expression required')
    module=task.executor()
    try:module.parse_program(program)
    except module.ExecutorContractError as exc:
        raise ValueError('invalid declaration program') from exc
    target=dict(role='assistant',content='Final program: '+program,tool_calls=[])
    event=dict(type='text',part=dict(type='text',messageID='derived-target',
                                   id='program',text=target['content']))
    if task.terminal_proposal([event])!=dict(status='proposal',program=program):
        raise ValueError('derived target differs from deployment declaration')
    return target


def declaration_target(assistant,program):
    """Align transport while preserving the complete original explanation."""
    declaration=program_declaration(program)
    content=assistant.get('content')
    if assistant.get('role')!='assistant' or not isinstance(content,str):
        raise ValueError('actual assistant content required')
    event=dict(type='text',part=dict(type='text',messageID='aligned',id='text',text=content))
    existing=task.terminal_proposal([event])
    if existing['status']=='absent':
        content=content+('\n\n' if content else '')+declaration['content']
    elif existing!=dict(status='proposal',program=program):
        raise ValueError('original declaration conflicts with verified execution')
    return dict(role='assistant',content=content,tool_calls=[])


def declaration_counterfactual(positive,good_program,bad_program):
    """Change only the submitted expression, retaining its causal text prefix."""
    program_declaration(bad_program)
    if declaration_target(positive,good_program)!=positive:
        raise ValueError('positive must already declare its verified program')
    matches=list(re.finditer(r'^Final program:[ \t]*([^\r\n]+)$',positive['content'],re.M))
    if len(matches)!=1 or matches[0].group(1).strip()!=good_program or good_program==bad_program:
        raise ValueError('one distinct counterfactual program required')
    begin,end=matches[0].span(1)
    negative=copy.deepcopy(positive)
    negative['content']=positive['content'][:begin]+bad_program+positive['content'][end:]
    return negative


def action_conditioning(request,original_task,public,state):
    """Replace the task exactly, preserving native system/tools and quoting."""
    task.check_public(public)
    if not isinstance(state,dict) or set(state)-{
            'current_program','execution_feedback','last_tool_feedback'}:
        raise ValueError('only public execution state fields are allowed')
    if any(k in json.dumps(state) for k in (
            'execution_correct','native_success','source_correct','training_reference','exe_ans')):
        raise ValueError('private correctness field in action conditioning')
    return fresh_request(request,original_task,review_prompt(public,state,terminal_program=True))


def rebind_state_contrasts(points,before,after):
    """Shift only prefix-relative positions; keep the supervised token stream."""
    if [x for x in before['labels'] if x!=-100]!=[x for x in after['labels'] if x!=-100]:
        raise ValueError('state view changed positive targets')
    delta=after['prompt_token_count']-before['prompt_token_count'];result=[]
    for point in points:
        old=point['target_position'];new=old+delta;good=point['good_token']
        if (not before['prompt_token_count']<=old<len(before['labels']) or
                before['labels'][old]!=good or before['input_ids'][old]!=good or
                not after['prompt_token_count']<=new<len(after['labels']) or
                after['labels'][new]!=good or after['input_ids'][new]!=good or good==point['bad_token']):
            raise ValueError('execution-negative token binding changed')
        result.append(dict(point,target_position=new))
    return result


def fresh_request(request,before_text,after_text):
    fresh=learning.project_request(request,before_text,after_text)
    wrapped='"'+after_text.replace('"',chr(92)+'"')+'"'
    users=[m for m in fresh['messages'] if m.get('role')=='user' and m.get('content') in (after_text,wrapped)]
    if len(users)!=1:raise ValueError('public state user turn is not unique')
    fresh['messages']=[m for m in fresh['messages'] if m.get('role')=='system']+users
    return fresh


def source_folder(repair,teacher):
    if repair['phase']=='replay':return study.ROOT/'student'/f"{repair['source_index']:03d}"
    return Path(next(e for e in read(teacher.parent/'PLAN.json')['episodes']
                     if e['index']==repair['source_index'])['source_folder'])


def prepare():
    if ROOT.exists():raise ValueError('state-view experiment already prepared')
    parent=controls.ROOT/'controls_v1/identity_fold_v1';old=read(parent/'DATA.json');plan=read(parent/'PLAN.json')
    if sha(parent/'DATA.json')!='01af4ad54f1a65c4491071a2c7e976b27d4f20f7c3e0029e7e4818d9272a3960':
        raise ValueError('original target source changed')
    if 'initial_decision_coefficient' in plan:raise ValueError('preserve original token-mean coefficients')
    original=read(controls.ROOT/'DATA.json');tokenizer=tokens.load_tokenizer(learning.MODEL)
    arms=['state_sft','state_branch'];rows=[];groups=[];proofs=[];sources=dict(old['sources'])
    for path,digest in sources.items():
        if sha(path)!=digest:raise ValueError('frozen teacher source changed')
    for old_group,(a,b) in zip(old['paired_rows'],original['paired_rows'],strict=True):
        repair,closure=original['rows'][a],original['rows'][b]
        first,last=controls.source_requests(repair,closure);teacher=last.parent.parent
        source=source_folder(repair,teacher);public=read(teacher/'inputs/public.json')
        before_text=controls.recovery_text(repair,teacher,public);group=[]
        for index in old_group:
            base=copy.deepcopy(learning.conditioning_row(old['rows'][index],'terminal_identity_fold'))
            is_repair=base['boundary_role']=='repair'
            req=first if is_repair or repair['source_correct'] else last
            target=base.get('assistant') or learning.sse_assistant(Path(closure['source_response']).read_bytes())
            request=learning.project_request(read(req),(teacher/'inputs/task.txt').read_text(),before_text)
            kind='action' if is_repair else 'text'
            check=tokens.encode_completion(request,target,tokenizer,16384,completion_kind=kind)
            if any(check[k]!=base[k] for k in ('input_ids','labels')):raise ValueError('old target conditioning differs')
            state_folder=source if is_repair or repair['source_correct'] else teacher
            state=state_from_folder(state_folder)
            encoded=tokens.encode_completion(fresh_request(request,before_text,review_prompt(public,state)),
                                               target,tokenizer,16384,completion_kind=kind)
            points=rebind_state_contrasts(base.get('edit_contrasts',{}).get('terminal_identity_fold',[]),base,encoded)
            row=dict(base,**encoded);row.pop('conditioning_by_arm',None);row.pop('semantic_field_mask',None)
            row.update(assistant=target,source_correct=repair['source_correct'],
                       edit_contrasts={'state_sft':[],'state_branch':points},
                       projection='One public current-program state; old target tokens and coefficients preserved')
            row['weights_by_arm']={arm:[float(x!=-100) for x in row['labels']] for arm in arms}
            group.append(len(rows));rows.append(row)
            proofs.append(dict(pair_id=repair['pair_id'],role=row['boundary_role'],state_folder=str(state_folder),
                               state=state,target_tokens=row['supervised_tokens'],negative_points=len(points),
                               old_prompt_tokens=base['prompt_token_count'],new_prompt_tokens=row['prompt_token_count']))
            for path in [req,state_folder/'RESULT.json',state_folder/'raw.jsonl',state_folder/'work/executions.jsonl']:
                if path.exists():sources[str(path)]=sha(path)
        groups.append(group)
    if (len(rows),len(groups),sum(x['supervised_tokens'] for x in rows),sum(x['negative_points'] for x in proofs))!=(51,30,4362,40):
        raise ValueError('original supervision or negative dose changed')
    ROOT.mkdir();study.new(ROOT/'DATA.json',dict(schema='finqa_preserved_target_state_pairs_v2',rows=rows,paired_rows=groups,
        sources=sources,tokenizer=old['tokenizer'],state_proofs=proofs,parent_data_sha256=sha(parent/'DATA.json')))
    reference=copy.deepcopy(read(parent/'RESULT.json')['arms']['terminal_identity_fold'])
    reference.update(source_training_result_sha256=sha(parent/'RESULT.json'),source_arm='terminal_identity_fold',fresh_training_updates=0)
    target=ROOT/'retention_reference';target.mkdir()
    for name,digest in reference['adapter_files'].items():
        path=parent/'terminal_identity_fold'/name
        if sha(path)!=digest:raise ValueError('retention reference changed')
        shutil.copyfile(path,target/name)
    for key in ('parent_training_result_sha256','teacher_result_sha256'):plan.pop(key,None)
    components=[Path(__file__),Path(learning.__file__),Path(controls.__file__),Path(tokens.__file__),Path(study.__file__),
                Path(task.__file__),Path(native.__file__),Path(study.core.__file__),study.REPO/'scripts/graph/research_gpu_guard.py']
    plan.update(schema='finqa_preserved_target_state_learning_v2',arms=arms,paired_rows=groups,
        inherited_arms={'retention_reference':reference},positive_only_arms=[],data_sha256=sha(ROOT/'DATA.json'),
        expected_forward_calls=2*sum(len(groups[i]) for i in plan['schedule']),terminal_status='TRAINED_STATE_VIEW_ARMS',
        components={str(p):sha(p) for p in components},
        comparison='Same original 51 targets, coefficients, warm start, 96 updates and 13633 supervised tokens per fresh arm. Ordinary state SFT versus executed-error branch contrast; a frozen retention adapter is reused only as a common-prompt reference.',
        prediction='On the same public state view, branch supervision should recover more semantic errors than ordinary state SFT without cancelling the gain through incorrect revisions.',
        scope='Thirty existing TRAIN groups and 32 already-exposed development reports; no new teacher calls or confirmation claim.')
    study.new(ROOT/'PLAN.json',plan);snapshot=ROOT/'compilation_sources';snapshot.mkdir()
    for p in components:(snapshot/p.name).write_bytes(p.read_bytes())
    prepare_native(arms+['retention_reference'])
    print(json.dumps(dict(plan_sha256=sha(ROOT/'PLAN.json'),data_sha256=sha(ROOT/'DATA.json'),groups=30,targets=51,
        supervised_tokens_per_arm=13633,expected_forwards=322,reference_training_updates=0,native_episodes=96,model_requests=0)))


def prepare_native(arms):
    source=controls.ROOT/'dev_firstpass_v1';out=ROOT/'native_v1';out.mkdir();episodes=[];bindings=[]
    order=list(arms);random.Random(17).shuffle(order)
    for ep in read(source/'PLAN.json')['episodes']:
        folder=Path(ep['folder']);public=read(folder/'inputs/public.json');text=review_prompt(public,state_from_folder(folder))
        bindings.append(dict(ep,result_sha256=sha(folder/'RESULT.json'),work_tree=study.core.tree(folder/'work')))
        for arm in order:
            target=out/arm/f"{ep['index']:03d}";target.mkdir(parents=True)
            shutil.copytree(folder/'inputs',target/'inputs');shutil.copytree(folder/'work',target/'work');(target/'dependencies').mkdir()
            (target/'inputs/task.txt').write_text(text)
            episodes.append(dict(ep,arm=arm,folder=str(target),task_sha256=sha(target/'inputs/task.txt')))
    shutil.copyfile(source/'LABELS_PRIVATE.json',out/'LABELS_PRIVATE.json')
    plan=dict(schema='finqa_common_public_state_native_v2',episodes=episodes,arms=order,arm_order=order,
        training_root=str(ROOT),training_plan_sha256=sha(ROOT/'PLAN.json'),required_training_status='TRAINED_STATE_VIEW_ARMS',
        terminal_status='FINQA_STATE_VIEW_REVIEW_RETURNED',source_episodes=bindings,parent_plan_sha256=sha(source/'PLAN.json'),
        private_labels_sha256=sha(out/'LABELS_PRIVATE.json'),max_posts=len(episodes)*study.CAPS['posts'],
        comparison='All three adapters get identical witnessed public states and saved workspaces. Primary: branch minus ordinary state SFT. Secondary: branch minus frozen retention reference; no extra oracle trigger.',
        scope='Already-exposed development reports; original-prompt legacy scores are not the matched common-prompt reference.',**native.expanded_runtime())
    study.new(out/'PLAN.json',plan);snapshot=out/'executed_sources';snapshot.mkdir()
    for p in plan['components']:(snapshot/Path(p).name).write_bytes(Path(p).read_bytes())


def prepare_expanded():
    """Compile the additional real TRAIN recoveries for matched learning.

    The ordinary state and contrast arms have identical targets. A separate
    success-distillation dataset restores the real submission actions needed
    in an empty workspace; its additional action dose is reported explicitly.
    """
    import finqa_semantic_learning as semantic
    if EXPANDED.exists():raise ValueError('expanded state study already prepared')
    parent=read(ROOT/'DATA.json');original=read(controls.ROOT/'DATA.json')
    formed=controls.ROOT/'formation_sources_v2';teacher=formed/'teacher_v1'
    result=read(teacher/'RESULT.json');teacher_plan=read(teacher/'PLAN.json')
    if result['status']!='TEACHER_EXPANSION_RETURNED' or result.get('analysis_error'):
        raise ValueError('bound completed teacher formation required')
    analysis=read(teacher/'ANALYSIS.json')
    if sha(teacher/'ANALYSIS.json')!=result['analysis_sha256'] or analysis['summary']['native_success']!=40:
        raise ValueError('teacher formation receipt changed')
    source_plan=read(formed/'PLAN.json');source_result=read(formed/'RESULT.json')
    source_rows={r['index']:r for r in source_result['episodes']}
    source_episodes={r['index']:r for r in source_plan['episodes']}
    labels=read(formed/'LABELS_PRIVATE.json');sources=dict(parent['sources'])
    for path,digest in sources.items():
        if sha(path)!=digest:raise ValueError('parent teacher evidence changed')
    quarantine={
        'JPM/2003/page_44.pdf-1':'Teacher explicitly reports reference/question conflict; raw qa.answer=157.85% while exe_ans=20452.85 and the selected reference uses earnings rather than the revenue question.',
        'MMM/2007/page_66.pdf-2':'Teacher explicitly reports period conflict; question asks January 1 while the reference adds January 1 and December 31 interest/penalties.'}
    rows=copy.deepcopy(parent['rows']);groups=copy.deepcopy(parent['paired_rows'])
    clean_rows=[];clean_groups=[];proofs=[];excluded=[]
    tokenizer=tokens.load_tokenizer(learning.MODEL)
    def remember(*paths):
        for path in paths:
            path=Path(path)
            if path.exists():sources[str(path)]=sha(path)
    def load_records(folder,item):
        result=[]
        for q in item['accounting']['requests']:
            request=folder/'wire'/f"{q['request']:05d}.request.json";response=request.with_suffix('.response')
            if sha(request)!=q['request_sha256'] or sha(response)!=q['response']['body_sha256']:
                raise ValueError('formation wire binding changed')
            result.append(dict(request=read(request),assistant=learning.sse_assistant(response.read_bytes()),
                               source_request=str(request),source_response=str(response)))
            remember(request,response)
        return result
    def encoded(request,target,kind,pair_id,report,role,source_record):
        row=tokens.encode_completion(request,target,tokenizer,16384,completion_kind=kind)
        row.update(boundary_role=role,pair_id=pair_id,report=report,assistant=copy.deepcopy(target),
                   source_request=source_record['source_request'],source_response=source_record['source_response'],
                   edit_contrasts={'state_sft':[],'state_branch':[]},phase='additional_train')
        return row
    def success_pair(action_request,closure_request,private_text,public,action,closure,pair_id,report,first,last):
        a=encoded(fresh_request(action_request,private_text,study.prompt(public)),action,'action',pair_id,report,'repair',first)
        b=encoded(clean_success_request(closure_request,private_text,study.prompt(public),action),closure,'closure',pair_id,report,'closure',last)
        clean_groups.append([len(clean_rows),len(clean_rows)+1]);clean_rows.extend([a,b])
    # The old 30 groups keep their proven targets. Success distillation also
    # receives the nine real identity submissions removed by the state recipe.
    for group,(a,b) in zip(groups,original['paired_rows'],strict=True):
        repair,closing=original['rows'][a],original['rows'][b]
        first,last=controls.source_requests(repair,closing);folder=last.parent.parent
        public=read(folder/'inputs/public.json');private_text=(folder/'inputs/task.txt').read_text()
        target=next(rows[i]['assistant'] for i in group if rows[i]['boundary_role']=='closure')
        success_pair(read(first),read(last),private_text,public,repair['assistant'],target,repair['pair_id'],repair['report'],
                     dict(source_request=str(first),source_response=str(first.with_suffix('.response'))),
                     dict(source_request=str(last),source_response=str(last.with_suffix('.response'))))
        remember(first,first.with_suffix('.response'),last,last.with_suffix('.response'))
    actual_teachers={r['index']:r for r in result['episodes']}
    keep_manifest={r['index']:r for r in read(teacher/'KEEP_SOURCES.json')}
    for index,source_item in sorted(source_rows.items()):
        ep=source_episodes[index];source=Path(ep['folder']);public=read(source/'inputs/public.json')
        task.check_public(public)
        if public['id']!=labels[index]['id']:raise ValueError('source/label identity differs')
        is_keep=source_item['native_success'];item=source_item if is_keep else actual_teachers[index]
        if not item['native_success']:
            excluded.append(dict(index=index,id=ep['id'],reason='teacher_native_incomplete'));continue
        if ep['id'] in quarantine:
            excluded.append(dict(index=index,id=ep['id'],reason='conflicting_training_supervision',evidence=quarantine[ep['id']]));continue
        folder=source if is_keep else Path(next(e['folder'] for e in teacher_plan['episodes'] if e['index']==index))
        if is_keep and study.core.tree(source/'work')!=keep_manifest[index]['source_work_tree']:
            raise ValueError('successful source workspace changed')
        if not task.grade(item['submitted_program'],public,labels[index]['exe_ans'])['execution_correct']:
            raise ValueError('positive program no longer matches TRAIN target')
        records=load_records(folder,item);before_log=source/'work/executions.jsonl'
        prior=read_lines(before_log) if before_log.exists() else []
        witnesses=read_lines(folder/'work/executions.jsonl')
        if not is_keep and witnesses[:len(prior)]!=prior:raise ValueError('source execution prefix changed')
        action_at,closure_at=verified_teacher_pair(records,item['submitted_program'],witnesses,0 if is_keep else len(prior))
        first,last=records[action_at],records[closure_at];action=first['assistant']
        private_text=(folder/'inputs/task.txt').read_text();before=state_from_folder(source);after=state_from_folder(folder)
        closure=semantic.identity_execution(source_item,item['submitted_program'],item['public_execution'],witnesses) if is_keep else last['assistant']
        pair_id='additional_train/'+str(index);group=[]
        if not is_keep:
            request=fresh_request(first['request'],private_text,review_prompt(public,before))
            row=encoded(request,action,'action',pair_id,ep['report'],'repair',first);points=[]
            edits=task.execution_backslides(source_item['submitted_program'],item['submitted_program'],public,labels[index]['exe_ans'])
            args=action['tool_calls'][0]['function']['arguments'];escaped=json.dumps(item['submitted_program'],ensure_ascii=False)[1:-1]
            if args.count(escaped)!=1:raise ValueError('positive program not unique in real call')
            for edit in edits:
                if not edit['semantic_negative']:continue
                negative=copy.deepcopy(action)
                negative['tool_calls'][0]['function']['arguments']=args.replace(escaped,json.dumps(edit['program'],ensure_ascii=False)[1:-1],1)
                alt=tokens.encode_completion(request,negative,tokenizer,16384)
                points.append(learning.first_edit_decision(row,alt))
            unique={tuple(p[k] for k in ('target_position','good_token','bad_token')):p for p in points}
            row['edit_contrasts']['state_branch']=list(unique.values())
            row['source_correct']=False;group.append(len(rows));rows.append(row)
        row=encoded(fresh_request(last['request'],private_text,review_prompt(public,after)),closure,'text',pair_id,ep['report'],'closure',last)
        row['source_correct']=is_keep;group.append(len(rows));rows.append(row);groups.append(group)
        success_pair(first['request'],last['request'],private_text,public,action,closure,pair_id,ep['report'],first,last)
        proofs.append(dict(index=index,id=ep['id'],report=ep['report'],kind='keep' if is_keep else 'repair',
                           actual_requests=len(records),action_request=action_at,closure_request=closure_at,
                           source_folder=str(source),teacher_folder=str(folder),before=before,after=after))
        for endpoint in {source,folder}:remember(endpoint/'RESULT.json',endpoint/'raw.jsonl',endpoint/'inputs/public.json',
                                               endpoint/'inputs/task.txt',endpoint/'work/executions.jsonl')
    if (len(groups),len(rows),len(clean_groups),len(clean_rows),len(proofs))!=(88,147,88,176,58):
        raise ValueError('unexpected accepted formation scope')
    filings=[tuple(rows[g[0]]['report'].split('/')[:2]) for g in groups]
    if len(set(filings))!=88:raise ValueError('training source filings overlap')
    for path in [ROOT/'DATA.json',teacher/'RESULT.json',teacher/'PLAN.json',teacher/'ANALYSIS.json',
                 teacher/'KEEP_SOURCES.json',formed/'RESULT.json',formed/'PLAN.json',formed/'LABELS_PRIVATE.json']:
        remember(path)
    components=[Path(__file__),Path(semantic.__file__),Path(learning.__file__),Path(controls.__file__),Path(tokens.__file__),
                Path(study.__file__),Path(task.__file__),Path(native.__file__),Path(study.core.__file__),
                study.REPO/'scripts/graph/research_gpu_guard.py']
    EXPANDED.mkdir();success_root=EXPANDED/'clean_success';success_root.mkdir()
    def freeze(root,data_rows,paired,arms,status):
        study.new(root/'DATA.json',dict(schema='finqa_expanded_witnessed_state_training_v1',rows=data_rows,paired_rows=paired,
            sources=sources,tokenizer=parent['tokenizer'],formation_proofs=proofs,excluded_teachers=excluded,
            quarantine=quarantine,parent_data_sha256=sha(ROOT/'DATA.json'),scope='TRAIN only. Forty native teacher successes remain in receipts; two conflicting references are held out from every training arm.'))
        order=list(range(len(paired)));random.Random(17).shuffle(order);plan=copy.deepcopy(read(ROOT/'PLAN.json'))
        for key in ['inherited_arms','same_target_context_arms','initial_decision_coefficient','parent_training_result_sha256','teacher_result_sha256']:plan.pop(key,None)
        plan.update(schema='finqa_expanded_state_learning_plan_v1',arms=arms,paired_rows=paired,schedule=order*3,
            updates_per_arm=3*len(paired),wall_seconds=14400,data_sha256=sha(root/'DATA.json'),
            expected_forward_calls=len(arms)*3*len(data_rows),positive_only_arms=[],terminal_status=status,
            components={str(p):sha(p) for p in components},
            comparison='Same 88 verified source filings, warm adapter and three group-balanced passes. State SFT versus branch share every target token. Clean success additionally learns 29 necessary submission actions for fresh workspaces; report its extra target/forward dose.',
            scope='Thirty old TRAIN groups plus 38 referenced native recoveries and 20 native successes. Two explicit reference conflicts and four unresolved teachers are excluded uniformly; no dev inputs or answers are training targets.')
        study.new(root/'PLAN.json',plan);snapshot=root/'compilation_sources';snapshot.mkdir()
        for p in components:(snapshot/p.name).write_bytes(p.read_bytes())
        return dict(root=str(root),groups=len(paired),targets=len(data_rows),arms=arms,updates_per_arm=plan['updates_per_arm'],
                    forwards=plan['expected_forward_calls'],supervised_tokens_per_arm=3*sum(r['supervised_tokens'] for r in data_rows),plan_sha256=sha(root/'PLAN.json'))
    main=freeze(EXPANDED,rows,groups,['state_sft','state_branch'],'TRAINED_EXPANDED_STATE_ARMS')
    success=freeze(success_root,clean_rows,clean_groups,['success_sft'],'TRAINED_EXPANDED_SUCCESS_ARM')
    study.new(EXPANDED/'PREPARATION.json',dict(status='CPU_PREPARED_NOT_TRAINED',main=main,clean_success=success,
        old_negative_points=40,new_negative_points=sum(len(r['edit_contrasts']['state_branch']) for r in rows[51:]),
        excluded=excluded,model_requests=0,neural_forwards=0,training_updates=0))
    print(json.dumps(dict(main=main,success=success,excluded=excluded,model_requests=0)))


def prepare_paired_states():
    """Reuse frozen TRAIN witnesses; align transport and split one contrast budget.

    The native request is a system/tool template only. Its dev user task is
    replaced exactly before encoding any TRAIN example. All original assistant
    explanations survive verbatim; no new teacher or model generation is used.
    """
    parent=PAIRED_STATES.parent
    if PAIRED_STATES.exists():raise ValueError('paired-state attempt already exists')
    if sha(parent/'DATA.json')!='cf187ad67f555f18c604c694da4b3a55957c1cea3bd224bd1524331b3355285a':
        raise ValueError('frozen TRAIN source changed')
    original=read(parent/'DATA.json');old=read(controls.ROOT/'DATA.json')
    groups=original['paired_rows'];sources=dict(original['sources'])
    for path,digest in sources.items():
        if sha(path)!=digest:raise ValueError('original TRAIN witness changed: '+path)
    template_folder=parent/'test_execution_v1/state_reviews/state_sft/000'
    template_path=template_folder/'wire/00001.request.json'
    template=read(template_path);original_task=(template_folder/'inputs/task.txt').read_text()
    tokenizer=tokens.load_tokenizer(learning.MODEL)
    binding=tokens.tokenizer_binding(learning.MODEL,tokenizer)
    if binding['files_sha256']!=original['tokenizer']['files_sha256']:
        raise ValueError('TRAIN tokenizer files changed')
    proofs={p['index']:p for p in original['formation_proofs']}
    arms=['aligned_sft','aligned_one_sided','paired_state_branch'];rows=[];bindings=[]
    def remember(*paths):
        for path in paths:sources[str(path)]=sha(path)
    remember(parent/'DATA.json',parent/'PLAN.json',controls.ROOT/'DATA.json',
             template_path,template_folder/'inputs/task.txt')
    for number,group in enumerate(groups):
        base=[original['rows'][i] for i in group]
        closing=next(r for r in base if r['boundary_role']=='closure')
        if number<30:
            a,b=old['paired_rows'][number];repair=old['rows'][a]
            _,last=controls.source_requests(repair,old['rows'][b]);teacher=last.parent.parent
            source=source_folder(repair,teacher)
        else:
            proof=proofs[int(closing['pair_id'].split('/')[-1])]
            source,teacher=Path(proof['source_folder']),Path(proof['teacher_folder'])
        public=read(teacher/'inputs/public.json');task.check_public(public)
        if public['report']!=closing['report']:raise ValueError('TRAIN report binding changed')
        before,after=state_from_folder(source),state_from_folder(teacher)
        actual=read(teacher/'RESULT.json');program=after['current_program']
        if not actual['native_success'] or not actual['execution_correct']:
            raise ValueError('a real successful TRAIN teacher is required')
        if program!=actual['submitted_program'] or after['execution_feedback']!=actual['public_execution']:
            raise ValueError('after-state differs from successful execution')
        edits=(task.execution_backslides(before['current_program'],program,public,
                                       after['execution_feedback']['terminal_execution_answer'])
               if len(group)==2 else [])
        negatives=[e for e in edits if e['semantic_negative']]
        diagnostics=[]
        for old_index,base_row in zip(group,base,strict=True):
            role=base_row['boundary_role'];snapshot=before if role=='repair' else after
            request=action_conditioning(template,original_task,public,snapshot)
            target=declaration_target(base_row['assistant'],program)
            encoded=tokens.encode_completion(request,target,tokenizer,16384,completion_kind='text')
            points=[]
            for edit in negatives:
                alternate=declaration_counterfactual(target,program,edit['program'])
                other=tokens.encode_completion(request,alternate,tokenizer,16384,completion_kind='text')
                points.append(learning.first_edit_decision(encoded,other))
            unique={tuple(p[k] for k in ('target_position','good_token','bad_token')):p for p in points}
            contrasts={'aligned_sft':[],
                       'aligned_one_sided':list(unique.values()) if role=='repair' else [],
                       'paired_state_branch':list(unique.values())}
            encoded.update(boundary_role=role,pair_id=base_row['pair_id'],report=base_row['report'],
                           assistant=target,edit_contrasts=contrasts,parent_row=old_index,
                           source_correct=base_row['source_correct'],phase='paired_state_train',
                           original_content_sha256=tokens.text_sha(base_row['assistant']['content']),
                           public_state=snapshot,negative_programs=[e['program'] for e in negatives])
            rows.append(encoded)
            diagnostics.append(dict(role=role,supervised_tokens=encoded['supervised_tokens'],
                                    contrast_points=len(unique),original_content_preserved=True,
                                    rendered_prefix_sha256=encoded['rendered_prefix_sha256']))
        if [r['parent_row'] for r in rows[-len(group):]]!=group:
            raise ValueError('group order changed')
        bindings.append(dict(group=number,pair_id=closing['pair_id'],report=closing['report'],
                             source_folder=str(source),teacher_folder=str(teacher),
                             before=before,after=after,negative_executions=edits,rows=diagnostics,
                             absent_execution_logs=[]))
        for folder in {source,teacher}:
            remember(folder/'RESULT.json',folder/'inputs/public.json')
            execution_log=folder/'work/executions.jsonl'
            if execution_log.exists():remember(execution_log)
            elif read(folder/'RESULT.json')['submitted_program'] is None:
                bindings[-1]['absent_execution_logs'].append(str(execution_log))
            else:raise ValueError('submitted program lost its execution witness')
    if len(rows)!=147 or len(groups)!=88:raise ValueError('paired-state source scope changed')
    old_negative_groups=sum(any(original['rows'][i]['edit_contrasts']['state_branch'] for i in g) for g in groups)
    new_negative_groups=sum(bool(rows[g[0]]['negative_programs']) for g in groups)
    if old_negative_groups!=new_negative_groups or old_negative_groups!=54:
        raise ValueError('executed-negative source coverage changed')
    plan=copy.deepcopy(read(parent/'PLAN.json'))
    for key in ['parent_interrupted_attempt','parent_plan_sha256','retention_projection_arms',
                'edit_weight_by_arm','inherited_arms','initial_decision_coefficient']:
        plan.pop(key,None)
    components={str(Path(p)):sha(p) for p in plan['components']}
    coefficients={role:0. for role in ['repair','closure']}
    for group in groups:
        for i,weight in zip(group,learning.group_coefficients([rows[j]['supervised_tokens'] for j in group],'token_mean'),strict=True):
            coefficients[rows[i]['boundary_role']]+=weight
    preparation=dict(status='CPU_PREPARED_NOT_TRAINED',source_groups=88,positive_targets=147,
        negative_source_groups=new_negative_groups,supervised_tokens_per_arm=3*sum(r['supervised_tokens'] for r in rows),
        sequence_tokens_per_arm=3*sum(r['sequence_length'] for r in rows),ce_role_coefficients=coefficients,
        old_points=sum(len(r['edit_contrasts']['state_branch']) for r in original['rows']),
        paired_points_by_role={role:sum(len(r['edit_contrasts']['paired_state_branch']) for r in rows if r['boundary_role']==role)
                               for role in ['repair','closure']},
        model_requests=0,neural_forwards=0,training_updates=0,
        transform='Preserve original assistant content verbatim; normalize only program delivery; reuse native system/tools and replace its complete task before encoding TRAIN.',
        template_scope='The exposed dev task is used only as an exact replacement preimage, never as a TRAIN question or target.')
    PAIRED_STATES.mkdir(mode=0o700)
    study.new(PAIRED_STATES/'DATA.json',dict(schema='finqa_paired_execution_states_v1',rows=rows,
        paired_rows=groups,sources=sources,tokenizer=binding,bindings=bindings,
        parent_data_sha256=sha(parent/'DATA.json'),scope='The same 88 TRAIN filings; no dev labels or new teacher targets.'))
    plan.update(schema='finqa_paired_execution_states_plan_v1',arms=arms,data_sha256=sha(PAIRED_STATES/'DATA.json'),
        components=components,expected_forward_calls=3*3*len(rows),wall_seconds=21600,
        edit_weight=.1,edit_state_fraction_by_arm={'paired_state_branch':{'repair':.5,'closure':.5}},
        terminal_status='TRAINED_PAIRED_EXECUTION_STATE_ARMS',
        comparison='Identical positive content, token masks, native public-state conditioning, schedule, warm start and updates. Single-state versus paired-state execution negatives share total auxiliary weight 0.1 per eligible source.',
        prediction='Paired-state negatives should reduce harmful revisions while retaining useful repairs, improving net native success over both aligned references.',
        next='Reuse all 64 fixed development states; if gains survive, add half-weight and coverage controls before untouched confirmation.')
    study.new(PAIRED_STATES/'PLAN.json',plan)
    preparation['plan_sha256']=sha(PAIRED_STATES/'PLAN.json')
    study.new(PAIRED_STATES/'PREPARATION.json',preparation)
    snapshot=PAIRED_STATES/'compilation_sources';snapshot.mkdir()
    for p in components:(snapshot/Path(p).name).write_bytes(Path(p).read_bytes())
    print(json.dumps(preparation))


def read_lines(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('mode',choices=['prepare','train','native','expand','expand-train','success-train','paired-states-prepare','paired-states-train']);parser.add_argument('--plan-sha');args=parser.parse_args()
    if args.mode=='prepare':prepare()
    elif args.mode=='expand':prepare_expanded()
    elif args.mode=='expand-train':learning.train(args.plan_sha,EXPANDED)
    elif args.mode=='success-train':learning.train(args.plan_sha,EXPANDED/'clean_success')
    elif args.mode=='paired-states-prepare':prepare_paired_states()
    elif args.mode=='paired-states-train':learning.train(args.plan_sha,PAIRED_STATES)
    elif args.mode=='train':learning.train(args.plan_sha,ROOT)
    else:native.run(args.plan_sha,ROOT/'native_v1')
