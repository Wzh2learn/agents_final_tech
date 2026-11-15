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


def review_prompt(public,state):
    return (study.prompt(public)+'\n\nReview the existing submitted program using the public state snapshot below. '
            'The execution feedback is the observed result of that program, not an answer-correctness label. '
            'Check its quantities, periods, operands and references against the question and report. '
            'Retain the current program if appropriate and finish, or correct and execute it before finishing. '
            'No reference answer is available.\n'+json.dumps(state,ensure_ascii=False))


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


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('mode',choices=['prepare','train','native']);parser.add_argument('--plan-sha');args=parser.parse_args()
    if args.mode=='prepare':prepare()
    elif args.mode=='train':learning.train(args.plan_sha,ROOT)
    else:native.run(args.plan_sha,ROOT/'native_v1')
