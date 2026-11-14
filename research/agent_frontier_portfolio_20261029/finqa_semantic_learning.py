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
    parser=argparse.ArgumentParser();parser.add_argument('mode',choices=['prepare','train','prepare-firstpass','firstpass','prepare-review','review','prepare-positive-fusion','positive-fusion','prepare-sources','sources']);parser.add_argument('--plan-sha');args=parser.parse_args()
    if args.mode=='prepare':prepare()
    elif args.mode=='train':learning.train(args.plan_sha,ROOT)
    elif args.mode=='prepare-firstpass':prepare_firstpass()
    elif args.mode=='prepare-review':prepare_review()
    elif args.mode=='prepare-positive-fusion':prepare_positive_fusion()
    elif args.mode=='prepare-sources':prepare_firstpass(True)
    else:native.run(args.plan_sha,ROOT/({'firstpass':'firstpass_v1','positive-fusion':'fusion_positive_v1/native_v1','sources':'formation_student_v1'}.get(args.mode,'native_v1')))
