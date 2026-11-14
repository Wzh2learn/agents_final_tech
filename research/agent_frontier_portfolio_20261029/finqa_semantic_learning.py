"""Train on executed correction edits; evaluate with the existing native Agent.

Execution labels below are TRAIN-only. Deployment never reads them or selects
a reviewer using hidden correctness. Historical runners and outputs stay intact.
"""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
import random
import shlex
import shutil

import finqa_learning as learning
import run_finqa_learning_native as native

study=learning.study
task=learning.task
tokens=learning.tokens
ROOT=learning.ROOT/'semantic_correction_v1'
read=learning.read
sha=learning.sha
new=learning.new


def prepare():
    if (ROOT/'PLAN.json').exists():raise ValueError('semantic attempt already prepared')
    parent=learning.PAIRED
    data=read(parent/'DATA.json');rows=copy.deepcopy(data['rows'])
    sources=dict(data['sources'])
    repair_data=learning.ROOT/'refinement_v2/DATA.json'
    if sha(repair_data)!=data['parent_data_sha256']:raise ValueError('repair source binding changed')
    requests=[Path(p) for p in read(repair_data)['sources'] if p.endswith('.request.json')]
    sources[str(repair_data)]=sha(repair_data)
    records={r['id']:r for r in read(study.DATA)}
    if sha(study.DATA)!='49f237eb9779b569473b26b08048867d04635a7cc39ad6a7a5664c55bb428db6':
        raise ValueError('TRAIN source changed')
    tokenizer=tokens.load_tokenizer(learning.MODEL);diagnostics=[]
    for row in rows:
        if row['boundary_role']!='repair':continue
        name=row['teacher_attempt'] if row['phase']=='replay' else 'recovery_training_v1'
        candidates=[p for p in requests if p.parent.parent.name==f"{row['source_index']:03d}" and p.parents[2].name==name]
        if len(candidates)!=1:raise ValueError('repair request binding differs')
        request_path=candidates[0];episode=request_path.parent.parent
        public=read(episode/'inputs/public.json');record=records[public['id']]
        if task.public_record(record)!=public:raise ValueError('training record differs')
        if row['phase']=='replay':
            source=study.ROOT/'student'/f"{row['source_index']:03d}"
            public_text=(study.prompt(public)+'\n\nContinue the existing student workspace. Use the public task and actual '
                         'failed operations below to repair its latest program with the same execution tool. '
                         'No reference answer is available.\n'+json.dumps({'student_actions':study.recent_actions(source)},ensure_ascii=False))
        else:
            ep=next(x for x in read(episode.parent/'PLAN.json')['episodes'] if x['index']==row['source_index'])
            source=Path(ep['source_folder'])
            public_text=study.recovery_prompt(public,study.recent_actions(source))
        candidate=source/'work/candidate.json'
        before=read(candidate)['program'] if candidate.exists() else None
        teacher_text=(episode/'inputs/task.txt').read_text()
        projected=learning.project_request(read(request_path),teacher_text,public_text)
        assistant=row['assistant'];arguments=assistant['tool_calls'][0]['function']['arguments']
        command=json.loads(arguments)['command'];argv=shlex.split(command)
        program=argv[argv.index('--program')+1]
        positive=tokens.encode_completion(projected,assistant,tokenizer,16384)
        if any(positive[k]!=row[k] for k in ('input_ids','labels')):
            raise ValueError('positive recovery changed')
        escaped=json.dumps(program,ensure_ascii=False)[1:-1]
        if arguments.count(escaped)!=1:raise ValueError('program is not unique in native tool arguments')
        row['edit_contrasts']={'edit_positive':[],'edit_contrast':[]}
        edits=task.execution_backslides(before,program,public,record['qa']['exe_ans'])
        for edit in edits:
            if not edit['program_valid']:continue
            negative=copy.deepcopy(assistant)
            negative['tool_calls'][0]['function']['arguments']=arguments.replace(escaped,json.dumps(edit['program'],ensure_ascii=False)[1:-1],1)
            encoded=tokens.encode_completion(projected,negative,tokenizer,16384)
            decision=learning.first_edit_decision(row,encoded)
            if edit['semantic_negative']:
                row['edit_contrasts']['edit_positive'].append(decision)
                row['edit_contrasts']['edit_contrast'].append(decision)
            edit['decision']=decision
        diagnostics.append(dict(pair_id=row['pair_id'],report=row['report'],before=before,repair=program,edits=edits))
        provenance=candidate if candidate.exists() else source/'RESULT.json'
        sources[str(provenance)]=sha(provenance)
    new(ROOT/'DATA.json',dict(rows=rows,sources=sources,tokenizer=data['tokenizer'],diagnostics=diagnostics,
                             parent_data_sha256=sha(parent/'DATA.json'),train_source_sha256=sha(study.DATA)))
    old=read(parent/'PLAN.json');result=read(parent/'RESULT.json');baseline=copy.deepcopy(result['arms']['token_mean'])
    target=ROOT/'token_mean';target.mkdir()
    for name,digest in baseline['adapter_files'].items():
        if sha(parent/'token_mean'/name)!=digest:raise ValueError('reused baseline changed')
        shutil.copy2(parent/'token_mean'/name,target/name)
    baseline['inherited_from']=str(parent/'RESULT.json')
    baseline['inherited_result_sha256']=sha(parent/'RESULT.json')
    components=[Path(__file__),Path(learning.__file__),Path(task.__file__),Path(tokens.__file__),Path(study.__file__),
                study.REPO/'scripts/graph/research_gpu_guard.py']
    plan=dict(schema='finqa_execution_validated_edit_contrast_v1',model_path=str(learning.MODEL),
              data_sha256=sha(ROOT/'DATA.json'),seed=old['seed'],arms=['edit_positive','edit_contrast'],
              inherited_arms={'token_mean':baseline},updates_per_arm=32,expected_forward_calls=128,
              paired_rows=old['paired_rows'],schedule=old['schedule'],pair_objective='token_mean',
              learning_rate=old['learning_rate'],rank=old['rank'],alpha=old['alpha'],wall_seconds=2700,
              warm_start=old['warm_start'],warm_files=old['warm_files'],resource_lock=old['resource_lock'],
              tool_token_id=old['tool_token_id'],edit_margin=1.,edit_weight=.1,
              terminal_status='TRAINED_SEMANTIC_CONTRAST_ARMS',components={str(p):sha(p) for p in components},
              parent_training_plan_sha256=sha(parent/'PLAN.json'),selection_sha256=sha(ROOT/'SELECTION.json'),
              comparison='Same 22 positive rows, warm start, 32 pair updates, 64 forwards and validated edit positions per arm. Token-mean baseline reused unchanged. Positive-only edit CE versus explicit bad/good token margin at the same shared prefix.',
              scope='11 already exposed TRAIN recovery sources. Eight preselected filing-disjoint TRAIN evaluation reports; official dev untouched.',
              deployment='Ordinary native first pass followed by one fixed public review for every task, with no gold-based trigger.',
              prediction='Explicit bad/good contrasts should improve at least one paired target beyond closed SFT and positive-only edit emphasis without merely changing termination. No increment means no evidence for the added negative direction.')
    new(ROOT/'PLAN.json',plan);snapshot=ROOT/'training_sources';snapshot.mkdir()
    for path in components:(snapshot/path.name).write_bytes(path.read_bytes())
    print(json.dumps(dict(plan_sha256=sha(ROOT/'PLAN.json'),rows=len(rows),new_updates=64,new_forwards=128,
                          edits=sum(len(x['edits']) for x in diagnostics),
                          negatives=sum(e['semantic_negative'] for x in diagnostics for e in x['edits']))))


def prepare_firstpass(formation=False):
    output=ROOT/('formation_student_v1' if formation else 'firstpass_v1')
    if output.exists():raise ValueError('first-pass attempt already exists')
    selection=read(ROOT/'SELECTION.json')
    if sha(ROOT/'SELECTION.json')!=read(ROOT/'PLAN.json')['selection_sha256']:raise ValueError('selection changed')
    records={r['id']:r for r in read(study.DATA)};episodes=[];labels=[]
    arm='token_mean' if formation else 'uniform_recovery'
    for index,item in enumerate(selection['train' if formation else 'evaluation']):
        record=records[item['id']];public=task.public_record(record)
        if not task.grade(record['qa']['program'],public,record['qa']['exe_ans'])['execution_correct']:
            raise ValueError('selected task reference does not satisfy the executor contract')
        folder=output/arm/f'{index:03d}';inputs=folder/'inputs';inputs.mkdir(parents=True)
        (folder/'work').mkdir();(folder/'dependencies').mkdir()
        (inputs/'public.json').write_text(json.dumps(public,ensure_ascii=False)+'\n')
        (inputs/'task.txt').write_text(study.prompt(public))
        (inputs/'finqa_tool.py').write_bytes(Path(task.__file__).read_bytes())
        (inputs/'executor.py').write_bytes(Path(task.executor().__file__).read_bytes())
        (inputs/'guest.py').write_text(study.core.GUEST)
        episodes.append(dict(arm=arm,index=index,id=record['id'],report=record['filename'],folder=str(folder),public_sha256=sha(inputs/'public.json'),task_sha256=sha(inputs/'task.txt')))
        labels.append(dict(index=index,id=record['id'],report=record['filename'],exe_ans=record['qa']['exe_ans']))
    new(output/'LABELS_PRIVATE.json',labels)
    template=read(learning.PAIRED/'native_v1/PLAN.json')
    for key in ('source_episodes','parent_review_plan_sha256','training_plan_sha256'):template.pop(key,None)
    training=learning.PAIRED if formation else learning.ROOT
    template.update(schema='finqa_formation_sources_v1' if formation else 'finqa_semantic_common_firstpass_v1',episodes=episodes,arm_order=[arm],arms=[arm],
                    training_root=str(training),training_result_sha256=sha(training/'RESULT.json'),
                    required_training_status='TRAINED_PAIRED_DECISION_ARMS' if formation else 'TRAINED_TWO_DEVELOPMENT_ARMS',
                    terminal_status='FORMATION_STUDENT_RETURNED' if formation else 'SEMANTIC_COMMON_FIRSTPASS_RETURNED',
                    private_labels_sha256=sha(output/'LABELS_PRIVATE.json'),max_posts=len(episodes)*study.CAPS['posts'],
                    selection_sha256=sha(ROOT/'SELECTION.json'),components={str(p):sha(p) for p in [Path(__file__),Path(native.__file__),Path(study.__file__),Path(task.__file__)]},
                    scope='Twenty preselected filing-disjoint TRAIN formation sources, ordinary closed-SFT student; retain all outcomes.' if formation else 'Eight preselected report-disjoint TRAIN development tasks, common first pass before every reviewer.')
    new(output/'PLAN.json',template)
    print(json.dumps(dict(plan_sha256=sha(output/'PLAN.json'),episodes=len(episodes),max_posts=template['max_posts'])))


def prepare_positive_fusion():
    """Matched alpha=.5 retention control; no grid or additional training."""
    from safetensors.torch import load_file,save_file
    root=ROOT/'fusion_positive_v1'
    if root.exists():raise ValueError('fusion control already prepared')
    arm='mean_positive';target=root/arm;target.mkdir(parents=True)
    donors=[ROOT/'token_mean',ROOT/'edit_positive']
    configs=[read(p/'adapter_config.json') for p in donors]
    if configs[0]!=configs[1]:raise ValueError('adapter configurations differ')
    weights=[load_file(p/'adapter_model.safetensors',device='cpu') for p in donors]
    save_file(learning.mean_adapter_parameters(*weights),str(target/'adapter_model.safetensors'))
    shutil.copy2(donors[0]/'adapter_config.json',target/'adapter_config.json')
    new(root/'PLAN.json',dict(schema='finqa_positive_adapter_parameter_mean_v1',alpha=.5,
                            operation='Mean matching LoRA A/B parameters, unchanged rank/scaling; not effective BA matrix averaging',
                            donors={str(p/'adapter_model.safetensors'):sha(p/'adapter_model.safetensors') for p in donors},
                            comparison='Matched control for the same alpha=.5 closed-SFT plus edit-contrast parameter mean',optimizer_updates=0))
    new(root/'RESULT.json',dict(status='ADAPTER_PARAMETERS_AVERAGED',optimizer_updates=0,forward_calls=0,
                              arms={arm:dict(adapter_files={p.name:sha(p) for p in target.iterdir() if p.is_file()})}))
    template=read(ROOT/'native_v1/PLAN.json');output=root/'native_v1';episodes=[]
    for ep in template['episodes']:
        if ep['arm']!='token_mean':continue
        folder=output/arm/f"{ep['index']:03d}";folder.mkdir(parents=True)
        shutil.copytree(Path(ep['folder'])/'inputs',folder/'inputs');(folder/'dependencies').mkdir()
        shutil.copytree(ROOT/'firstpass_v1/uniform_recovery'/f"{ep['index']:03d}"/'work',folder/'work')
        episodes.append(dict(ep,arm=arm,folder=str(folder)))
    shutil.copy2(ROOT/'native_v1/LABELS_PRIVATE.json',output/'LABELS_PRIVATE.json')
    template.update(schema='finqa_positive_fusion_native_v1',episodes=episodes,arms=[arm],arm_order=[arm],
                    training_root=str(root),training_plan_sha256=sha(root/'PLAN.json'),required_training_status='ADAPTER_PARAMETERS_AVERAGED',
                    terminal_status='POSITIVE_FUSION_REVIEW_RETURNED',private_labels_sha256=sha(output/'LABELS_PRIVATE.json'),max_posts=96,
                    components={str(p):sha(p) for p in [Path(__file__),Path(native.__file__),Path(study.__file__),Path(task.__file__)]},
                    scope='One post-hoc alpha=.5 positive-only retention control on the same eight exposed development tasks')
    new(output/'PLAN.json',template)
    print(json.dumps(dict(plan_sha256=sha(output/'PLAN.json'),episodes=8,max_posts=96)))


def prepare_teacher():
    source=ROOT/'formation_student_v1';output=source/'teacher27b_v1'
    if output.exists():raise ValueError('formation teacher attempt already exists')
    result=read(source/'RESULT.json')
    if result['status']!='FORMATION_STUDENT_RETURNED' or len(result['episodes'])!=20:
        raise ValueError('complete twenty-source student batch required')
    records={r['id']:r for r in read(study.DATA)};episodes=[];sources=[]
    for row in sorted(result['episodes'],key=lambda r:r['index']):
        original=source/'token_mean'/f"{row['index']:03d}";public=read(original/'inputs/public.json')
        record=records[public['id']];folder=output/f"{row['index']:03d}";inputs=folder/'inputs';inputs.mkdir(parents=True)
        for name in ['public.json','finqa_tool.py','executor.py','guest.py']:shutil.copy2(original/'inputs'/name,inputs/name)
        public_text=study.recovery_prompt(public,study.recent_actions(original))
        reference=dict(training_reference_program=record['qa']['program'],training_reference_execution_answer=record['qa']['exe_ans'],
                       training_source_program_correct=bool(row['execution_correct']))
        text=(public_text+'\n\nTRAIN formation only: the reference below is permitted for this teacher. '
              'If the existing source program is correct, keep its exact program rather than changing its scale or rewriting it. '
              'Otherwise repair the failed program using the public evidence and the reference. '
              'Always execute the final program once with the FinQA tool, then finish with a concise result. '
              'Do not write candidate files directly or alter the executor.\n'+json.dumps(reference,ensure_ascii=False))
        (inputs/'task.txt').write_text(text);shutil.copytree(original/'work',folder/'work');(folder/'dependencies').mkdir()
        episodes.append(dict(index=row['index'],id=row['id'],report=public['report'],folder=str(folder),source_folder=str(original),
                             source_correct=bool(row['execution_correct']),public_sha256=sha(inputs/'public.json'),task_sha256=sha(inputs/'task.txt')))
        sources.append(dict(folder=str(original),result_sha256=sha(original/'RESULT.json'),work_tree=study.core.tree(original/'work')))
    shutil.copy2(source/'LABELS_PRIVATE.json',output/'LABELS_PRIVATE.json')
    plan=dict(schema='finqa_train_teacher_recovery_retention_v1',role='TRAIN-referenced teacher recovery and retention; not blind model evaluation',
              episodes=episodes,source_episodes=sources,parent_plan_sha256=sha(source/'PLAN.json'),source_result_sha256=sha(source/'RESULT.json'),
              private_labels_path=str(output/'LABELS_PRIVATE.json'),private_labels_sha256=sha(output/'LABELS_PRIVATE.json'),
              model=dict(host='127.0.0.1',port=8006,model_id='qwen38-27b-fp8',context=32768,output=8192),
              caps=study.CAPS,max_posts=240,episode_deadline_is_bounded_failure=True,
              terminal_status='TRAIN_TEACHER_RECOVERY_RETENTION_RETURNED',
              components={str(p):sha(p) for p in [Path(__file__),Path(native.__file__),Path(study.__file__),Path(task.__file__)]},
              scope='Twenty preselected TRAIN sources: eleven original errors and nine correct sources. All outcomes and formation costs retained.',
              projection='Before student learning replace the entire privileged teacher user packet with the saved public recovery prompt; never expose reference labels to deployment.',
              interpretation='Actual local 27B tool execution with TRAIN references. This does not measure blind 27B capability or prove student learning.')
    new(output/'PLAN.json',plan);snapshot=output/'executed_sources';snapshot.mkdir()
    for path in plan['components']:(snapshot/Path(path).name).write_bytes(Path(path).read_bytes())
    print(json.dumps(dict(plan_sha256=sha(output/'PLAN.json'),episodes=20,source_errors=11,source_correct=9,max_posts=240,
                          max_task_characters=max(len((Path(e['folder'])/'inputs/task.txt').read_text()) for e in episodes))))


def compile_expanded():
    """Reuse native successes, including identity recoveries, without oracle inputs."""
    output=ROOT/'expanded_v1'
    if output.exists():raise ValueError('expanded dataset already exists')
    teacher=ROOT/'formation_student_v1/teacher27b_v1';result=read(teacher/'RESULT.json');plan=read(teacher/'PLAN.json')
    if result['status']!='TRAIN_TEACHER_RECOVERY_RETENTION_RETURNED':raise ValueError('teacher not terminal')
    parent=read(ROOT/'DATA.json');rows=copy.deepcopy(parent['rows']);sources=dict(parent['sources'])
    tokenizer=tokens.load_tokenizer(learning.MODEL);diagnostics=[];excluded=[]
    def program_of(assistant):
        calls=assistant.get('tool_calls') or []
        if len(calls)!=1 or calls[0]['function']['name']!='bash':raise ValueError('one actual bash target required')
        argv=shlex.split(json.loads(calls[0]['function']['arguments'])['command'])
        if '--program' not in argv:raise ValueError('target did not execute the FinQA tool')
        return argv[argv.index('--program')+1]
    def call_binding(call):
        args=call['function']['arguments']
        return call['id'],call['function']['name'],json.loads(args) if isinstance(args,str) else args
    for row in rows:
        if row['boundary_role']!='repair':continue
        mask=learning.semantic_field_mask(tokenizer,row,program_of(row['assistant']))
        all_points=row['edit_contrasts']['edit_contrast'];fields=learning.semantic_edit_decisions(mask,all_points)
        row.update(semantic_field_mask=mask,source_correct=False,
                   edit_contrasts={'edit_all_negative':all_points,'edit_field_positive':fields,'edit_field_negative':fields})
    records={r['id']:r for r in read(study.DATA)}
    for item in result['episodes']:
        if not item['native_success']:
            excluded.append(dict(index=item['index'],reason='teacher_native_incomplete',answer_correct=item['execution_correct']))
            continue
        ep=next(e for e in plan['episodes'] if e['index']==item['index']);folder=Path(ep['folder']);source=Path(ep['source_folder'])
        public=read(folder/'inputs/public.json');record=records[public['id']]
        public_text=study.recovery_prompt(public,study.recent_actions(source));private_text=(folder/'inputs/task.txt').read_text()
        requests=item['accounting']['requests'];action=folder/'wire'/f"{requests[0]['request']:05d}.request.json"
        for entry in requests:
            prefix=folder/'wire'/f"{entry['request']:05d}.request"
            if sha(prefix.with_suffix('.request.json'))!=entry['request_sha256'] or sha(prefix.with_suffix('.request.response'))!=entry['response']['body_sha256']:
                raise ValueError('teacher wire evidence changed')
        action_response=action.with_suffix('.response');assistant=learning.sse_assistant(action_response.read_bytes())
        program=program_of(assistant)
        if not task.grade(program,public,record['qa']['exe_ans'])['execution_correct']:raise ValueError('teacher action not correct')
        prior_log=source/'work/executions.jsonl';prior_lines=prior_log.read_text().splitlines() if prior_log.exists() else []
        log=[json.loads(s) for s in (folder/'work/executions.jsonl').read_text().splitlines()]
        if not any(x['program']==program and x['execution']['status']=='executed' for x in log[len(prior_lines):]):
            raise ValueError('no newly executed program witness')
        projected=learning.project_request(read(action),private_text,public_text)
        repair=tokens.encode_completion(projected,assistant,tokenizer,16384)
        pair_id='expanded_teacher27b/'+str(item['index'])
        repair.update(boundary_role='repair',pair_id=pair_id,report=ep['report'],source_index=item['index'],
                      phase='retention' if ep['source_correct'] else 'expanded_recovery',source_correct=ep['source_correct'],
                      assistant=assistant,source_request=str(action),source_response=str(action_response))
        mask=learning.semantic_field_mask(tokenizer,repair,program);all_points=[];edits=[]
        before_path=source/'work/candidate.json';before=read(before_path)['program'] if before_path.exists() else None
        if not ep['source_correct']:
            edits=task.execution_backslides(before,program,public,record['qa']['exe_ans'])
            args=assistant['tool_calls'][0]['function']['arguments'];escaped=json.dumps(program,ensure_ascii=False)[1:-1]
            if args.count(escaped)!=1:raise ValueError('non-unique target program')
            for edit in edits:
                if not edit['semantic_negative']:continue
                negative=copy.deepcopy(assistant)
                negative['tool_calls'][0]['function']['arguments']=args.replace(escaped,json.dumps(edit['program'],ensure_ascii=False)[1:-1],1)
                encoded=tokens.encode_completion(projected,negative,tokenizer,16384)
                point=learning.first_edit_decision(repair,encoded);edit['decision']=point;all_points.append(point)
        fields=learning.semantic_edit_decisions(mask,all_points)
        repair.update(semantic_field_mask=mask,edit_contrasts={'edit_all_negative':all_points,'edit_field_positive':fields,'edit_field_negative':fields})
        if len(requests)!=2:raise ValueError('expected directly witnessed action/closure pair')
        closure_request=folder/'wire'/f"{requests[1]['request']:05d}.request.json"
        closure_response=closure_request.with_suffix('.response');request=read(closure_request)
        binding=call_binding(assistant['tool_calls'][0])
        if not any(call_binding(c)==binding for msg in request['messages'] for c in msg.get('tool_calls') or []):
            raise ValueError('closure does not condition on the actual executed call')
        final=learning.sse_assistant(closure_response.read_bytes())
        closure=tokens.encode_completion(learning.project_request(request,private_text,public_text),final,tokenizer,16384,completion_kind='closure')
        closure.update(boundary_role='closure',pair_id=pair_id,report=ep['report'],source_index=item['index'],
                       phase='closure',source_correct=ep['source_correct'],source_request=str(closure_request),source_response=str(closure_response))
        rows.extend([repair,closure]);diagnostics.append(dict(index=item['index'],report=ep['report'],source_correct=ep['source_correct'],
                                                            all_decisions=len(all_points),field_decisions=len(fields),edits=edits))
        for p in [action,action_response,closure_request,closure_response]:sources[str(p)]=sha(p)
    pairs=[[i,i+1] for i in range(0,len(rows),2)]
    for a,b in pairs:
        if rows[a]['pair_id']!=rows[b]['pair_id']:raise ValueError('pair ownership changed')
    groups={tuple(r['report'].split('/')[:2]) for r in rows}
    if len(groups)!=len(pairs):raise ValueError('formation filing groups overlap')
    output.mkdir()
    new(output/'DATA.json',dict(schema='finqa_expanded_semantic_boundary_data_v1',rows=rows,paired_rows=pairs,sources=sources,
                              tokenizer=parent['tokenizer'],diagnostics=diagnostics,excluded_teachers=excluded,
                              parent_data_sha256=sha(ROOT/'DATA.json'),teacher_result_sha256=sha(teacher/'RESULT.json'),
                              source_result_sha256=sha(ROOT/'formation_student_v1/RESULT.json'),
                              scope='TRAIN-only native repair/retention and actual post-execution closures; whole privileged user packet removed. No new model calls.'))
    snapshot=output/'compilation_sources';snapshot.mkdir()
    for p in [Path(__file__),Path(learning.__file__),Path(tokens.__file__),Path(task.__file__)]:
        (snapshot/p.name).write_bytes(p.read_bytes())
    print(json.dumps(dict(data_sha256=sha(output/'DATA.json'),pairs=len(pairs),rows=len(rows),new_pairs=len(diagnostics),
                          retention_pairs=sum(d['source_correct'] for d in diagnostics),excluded=excluded,
                          all_decisions=sum(len(r.get('edit_contrasts',{}).get('edit_all_negative',[])) for r in rows),
                          field_decisions=sum(len(r.get('edit_contrasts',{}).get('edit_field_negative',[])) for r in rows))))


def prepare_expanded_train():
    root=ROOT/'expanded_v1'
    if (root/'PLAN.json').exists():raise ValueError('expanded training already frozen')
    data=read(root/'DATA.json');pairs=data['paired_rows'];order=list(range(len(pairs)));random.Random(17).shuffle(order)
    warm=ROOT/'token_mean';baseline=read(ROOT/'RESULT.json')['arms']['token_mean']
    for name,digest in baseline['adapter_files'].items():
        if sha(warm/name)!=digest:raise ValueError('ordinary warm adapter changed')
    components=[Path(__file__),Path(learning.__file__),Path(task.__file__),Path(tokens.__file__),Path(study.__file__),
                study.REPO/'scripts/graph/research_gpu_guard.py']
    plan=dict(schema='finqa_expanded_semantic_boundary_learning_v1',model_path=str(learning.MODEL),data_sha256=sha(root/'DATA.json'),
              seed=17,arms=['closed_sft','edit_field_positive','edit_all_negative','edit_field_negative'],
              paired_rows=pairs,schedule=[order[i%len(order)] for i in range(96)],updates_per_arm=96,
              expected_forward_calls=768,learning_rate=2e-4,rank=8,alpha=16,wall_seconds=7200,
              warm_start=str(warm),warm_files=baseline['adapter_files'],resource_lock=str(study.core.LOCK),
              tool_token_id=read(learning.PAIRED/'PLAN.json')['tool_token_id'],pair_objective='token_mean',
              edit_margin=1.,edit_weight=.1,positive_only_arms=['edit_field_positive'],
              terminal_status='TRAINED_EXPANDED_SEMANTIC_ARMS',components={str(p):sha(p) for p in components},
              comparison='All arms share 30 actual repair/closure pairs, including nine retention cases, the ordinary closed-SFT warm start, pair order and update budget. Contrast only differs in direction and semantic boundary eligibility.',
              scope='TRAIN-only formation; 19 accepted real new teacher continuations plus 11 replay pairs. Failed teacher cost and trajectory retained.',
              prediction='Field-gated negative learning should improve true corrections without increasing structural overcorrection relative to all-first-divergence negatives; compare with same-position positive-only CE.',
              next='Freeze report-disjoint development evaluation before model outcomes, use one common Agent first pass and review every task. If boundary gating wins, test a dose-matched all-negative control before crediting position selection.')
    new(root/'PLAN.json',plan);snapshot=root/'training_sources';snapshot.mkdir()
    for p in components:(snapshot/p.name).write_bytes(p.read_bytes())
    print(json.dumps(dict(plan_sha256=sha(root/'PLAN.json'),pairs=len(pairs),arms=plan['arms'],updates=384,forwards=768)))


def prepare_review():
    source=ROOT/'firstpass_v1';output=ROOT/'native_v1'
    if output.exists():raise ValueError('review attempt already exists')
    first=read(source/'RESULT.json')
    if first['status']!='SEMANTIC_COMMON_FIRSTPASS_RETURNED' or len(first['episodes'])!=8:
        raise ValueError('all eight common first-pass outcomes required')
    arms=['token_mean','edit_positive','edit_contrast'];order=list(arms);random.Random(17).shuffle(order)
    source_episodes=[];episodes=[]
    for row in sorted(first['episodes'],key=lambda r:r['index']):
        folder=source/'uniform_recovery'/f"{row['index']:03d}"
        public=read(folder/'inputs/public.json')
        prompt=study.recovery_prompt(public,study.recent_actions(folder))
        source_episodes.append(dict(folder=str(folder),result_sha256=sha(folder/'RESULT.json'),work_tree=study.core.tree(folder/'work')))
        for arm in arms:
            target=output/arm/f"{row['index']:03d}";inputs=target/'inputs';inputs.mkdir(parents=True)
            for name in ['public.json','finqa_tool.py','executor.py','guest.py']:shutil.copy2(folder/'inputs'/name,inputs/name)
            (inputs/'task.txt').write_text(prompt);(target/'dependencies').mkdir()
            shutil.copytree(folder/'work',target/'work')
            episodes.append(dict(arm=arm,index=row['index'],id=row['id'],report=public['report'],folder=str(target),
                                 public_sha256=sha(inputs/'public.json'),task_sha256=sha(inputs/'task.txt')))
    shutil.copy2(source/'LABELS_PRIVATE.json',output/'LABELS_PRIVATE.json')
    template=read(learning.PAIRED/'native_v1/PLAN.json')
    template.update(schema='finqa_semantic_native_review_v1',episodes=episodes,arm_order=order,arms=arms,
                    training_root=str(ROOT),training_plan_sha256=sha(ROOT/'PLAN.json'),
                    required_training_status='TRAINED_SEMANTIC_CONTRAST_ARMS',terminal_status='SEMANTIC_REVIEW_RETURNED',
                    parent_review_plan_sha256=sha(source/'PLAN.json'),source_episodes=source_episodes,
                    private_labels_sha256=sha(output/'LABELS_PRIVATE.json'),max_posts=len(episodes)*study.CAPS['posts'],
                    components={str(p):sha(p) for p in [Path(__file__),Path(native.__file__),Path(study.__file__),Path(task.__file__)]},
                    scope='Eight preselected filing-disjoint TRAIN development tasks. Review every task once, regardless of hidden correctness.',
                    comparison='Identical model, harness, public first-pass history, cloned workspaces and caps. Ordinary closed SFT versus positive-only edit emphasis versus explicit bad/good edit contrast.',
                    accounting='First-pass cost is shared physically and added to each complete Agent policy for per-policy totals; no new teacher calls.')
    template.pop('training_result_sha256',None)
    new(output/'PLAN.json',template)
    print(json.dumps(dict(plan_sha256=sha(output/'PLAN.json'),episodes=len(episodes),max_posts=template['max_posts'])))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('mode',choices=['prepare','train','prepare-firstpass','firstpass','prepare-review','review','prepare-positive-fusion','positive-fusion','prepare-sources','sources','prepare-teacher','teacher','compile-expanded','prepare-expanded-train','train-expanded']);parser.add_argument('--plan-sha');args=parser.parse_args()
    if args.mode=='prepare':prepare()
    elif args.mode=='train':learning.train(args.plan_sha,ROOT)
    elif args.mode=='prepare-firstpass':prepare_firstpass()
    elif args.mode=='prepare-review':prepare_review()
    elif args.mode=='prepare-positive-fusion':prepare_positive_fusion()
    elif args.mode=='prepare-sources':prepare_firstpass(True)
    elif args.mode=='prepare-teacher':prepare_teacher()
    elif args.mode=='teacher':native.run_strong(args.plan_sha,'teacher27b_v1',ROOT/'formation_student_v1')
    elif args.mode=='compile-expanded':compile_expanded()
    elif args.mode=='prepare-expanded-train':prepare_expanded_train()
    elif args.mode=='train-expanded':learning.train(args.plan_sha,ROOT/'expanded_v1')
    else:native.run(args.plan_sha,ROOT/({'firstpass':'firstpass_v1','positive-fusion':'fusion_positive_v1/native_v1','sources':'formation_student_v1'}.get(args.mode,'native_v1')))
