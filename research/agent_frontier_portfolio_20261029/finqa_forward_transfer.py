"""Frozen-cohort evaluation using the existing native actors and value readouts."""
from pathlib import Path
import argparse,json,os,random,shutil,subprocess,time,traceback
import finqa_patch_learning as c
import finqa_correction_router as router
import finqa_acquisition_learning as av

m=c.m
ROOT=c.root.parent/'forward_sources57_v1'
COHORT='forward'
POLICIES=dict(value='acquisition_value_v1',risk='acquisition_risk_control_v1',single='acquisition_single_state_v1')


def prepare():
    if COHORT=='confirmation':prepare_confirmation();return
    original=m.read(c.step1/'TRAIN_PLAN.json');prior=m.read(c.step1/'PLAN.json')
    used={r['index'] for r in m.read_lines(c.step1/'source_events.jsonl')}
    remaining=[r for r in original['episodes'] if r['index'] not in used]
    selection={r['index']:r for r in m.read(c.step1/'TRAIN_SELECTION.json')}
    reservation=m.read(c.step1.parents[2]/'filing_confirmation_reservation_v2/RESERVATION.json')
    protected={r['group'] for r in reservation['tasks']}|set(reservation['excluded_groups'])
    groups={selection[r['index']]['group'] for r in remaining}
    assert len(remaining)==len(groups)==57 and len(used)==96 and not groups&protected
    assert not groups&{selection[i]['group'] for i in used}
    assert all(not (Path(r['folder'])/'RESULT.json').exists() for r in remaining)
    labels=m.read(c.step1/'TRAIN_LABELS_PRIVATE.json');episodes=[];new_labels=[]
    ROOT.mkdir()
    for i,source in enumerate(remaining):
        folder=ROOT/'firstpass'/f'{i:03d}';shutil.copytree(source['folder'],folder)
        public=m.read(folder/'inputs/public.json');m.task.check_public(public)
        assert public['id']==source['id']==labels[source['index']]['id']
        ep=dict(index=i,id=source['id'],report=source['report'],group=selection[source['index']]['group'],
            original_index=source['index'],folder=str(folder))
        episodes.append(ep);label=dict(labels[source['index']]);label['index']=i;new_labels.append(label)
    adapters=dict(firstpass=prior['sampler_adapter'],
        ordinary=str(Path(prior['old37_adapter']).parent.parent/'aligned_sft/adapter.gguf'),cheap37=prior['old37_adapter'])
    assert all(Path(p).is_file() for p in adapters.values())
    template=m.read(router.RELATIVE_ROOT/'CHEAP_PLAN.json')['reference_template']
    m.study.new(ROOT/'LABELS_PRIVATE.json',new_labels)
    m.study.new(ROOT/'PLAN.json',dict(episodes=episodes,adapters=adapters,runtime=prior['runtime'],
        caps=original['caps'],review_caps=prior['caps'],reference_template=template,wall_seconds=7200,
        teacher_task_budget=16,secondary_task_budgets=[7,10,16],random_seed=20261117,
        frozen_policies=['value','risk','single'],
        scope='57 remaining eligible TRAIN company/year sources, disjoint from96 formation sources and reserved64. '
            'Forward development before any training on this batch; not final confirmation. '
            'All sources run without outcome selection; policies and budgets fixed before teacher responses.'))
    print(json.dumps(dict(prepared=57,unique_groups=len(groups),reserved_overlap=0,prior_result_files=0)),flush=True)


def prepare_confirmation():
    reservation_path=c.step1.parents[2]/'filing_confirmation_reservation_v2/RESERVATION.json'
    reservation=m.read(reservation_path);assert reservation['status']=='RESERVED_NOT_EXECUTED'
    tasks=reservation['tasks'];training={r['group'] for r in m.read(c.step1/'TRAIN_SELECTION.json')}
    assert len(tasks)==len({r['group'] for r in tasks})==64
    assert not {r['group'] for r in tasks}&(training|set(reservation['excluded_groups']))
    prior=m.read(c.step1/'PLAN.json');source_plan=m.read(c.step1/'TRAIN_PLAN.json')
    adapters=dict(firstpass=prior['sampler_adapter'],ordinary=str(Path(prior['old37_adapter']).parent.parent/'aligned_sft/adapter.gguf'),
        cheap37=prior['old37_adapter']);assert all(Path(path).is_file() for path in adapters.values())
    checkpoints={}
    for name,folder in POLICIES.items():
        path=ROOT.parent/folder;train=m.read(path/'TRAIN_RESULT.json');plan=m.read(path/'PLAN.json')
        assert train['status']=='TRAINED' and train['optimizer_updates']==434 and plan['value_source_groups']==96
        checkpoints[name]=dict(folder=str(path/'value_policy'),train_result=str(path/'TRAIN_RESULT.json'),updates=434)
    revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=c.repo,text=True).strip()
    ROOT.mkdir()
    protocol=dict(status='FROZEN_BEFORE_HELDOUT_PAYLOAD',cohort='confirmation',tasks=tasks,checkpoints=checkpoints,
        code_revision=revision,adapters=adapters,runtime=prior['runtime'],caps=source_plan['caps'],review_caps=prior['caps'],
        teacher_task_budget=18,secondary_task_budgets=[8,12,18],random_seed=20261117,
        reservation=str(reservation_path),source='/home/testuser/wzh/phase1a_staging_20260925/finqa/train.json',
        scope='One fixed-method confirmation on64 reserved company/year groups from official TRAIN, not official test. '
            'Old96-source value/risk/single models chosen before payload access; expanded153 variant stopped on DEV. '
            'Keep all64 tasks; no reroll, outcome filtering, further tuning or training on this cohort. '
            'Main18 and secondary8/12 teacher tasks; all policies share one actual teacher realization per original state.')
    m.study.new(ROOT/'PROTOCOL.json',protocol)
    records={r['id']:r for r in m.read(protocol['source'])};episodes=[];labels=[]
    template=Path(source_plan['episodes'][96]['folder'])/'inputs'
    for i,selected in enumerate(tasks):
        record=records[selected['id']];assert record['filename']==selected['report'] and '/'.join(record['filename'].split('/')[:2])==selected['group']
        public=m.task.public_record(record);folder=ROOT/'firstpass'/f'{i:03d}';inputs=folder/'inputs';inputs.mkdir(parents=True)
        (folder/'work').mkdir();(folder/'dependencies').mkdir()
        for name in ['finqa_tool.py','executor.py','guest.py']:shutil.copyfile(template/name,inputs/name)
        (inputs/'public.json').write_text(json.dumps(public,ensure_ascii=False))
        (inputs/'task.txt').write_text(m.study.prompt(public,terminal_program=True))
        episodes.append(dict(index=i,id=record['id'],report=record['filename'],group=selected['group'],folder=str(folder)))
        labels.append(dict(index=i,id=record['id'],report=record['filename'],exe_ans=record['qa']['exe_ans'],program=record['qa']['program']))
    m.study.new(ROOT/'LABELS_PRIVATE.json',labels)
    plan=dict(protocol,episodes=episodes,reference_template=m.read(router.RELATIVE_ROOT/'CHEAP_PLAN.json')['reference_template'],wall_seconds=7200)
    m.study.new(ROOT/'PLAN.json',plan)
    reservation.update(status='CONFIRMATION_PREPARED_NOT_EXECUTED',confirmation_root=str(ROOT),frozen_code_revision=revision)
    m.study.publish(reservation_path,reservation)
    print(json.dumps(dict(prepared=64,unique_groups=64,training_overlap=0,protocol_frozen_before_payload=True)),flush=True)


def prepare_reviews(arm,plan):
    episodes=[];template=Path(plan['reference_template'])
    for first in plan['episodes']:
        source=Path(first['folder']);folder=ROOT/arm/f"{first['index']:03d}";inputs=folder/'inputs';inputs.mkdir(parents=True)
        for name in ['work','dependencies']:shutil.copytree(source/name,folder/name)
        for name in ['finqa_tool.py','executor.py','guest.py']:shutil.copyfile(template/name,inputs/name)
        public=m.read(source/'inputs/public.json');initial=m.state_from_folder(source)
        (inputs/'public.json').write_text(json.dumps(public,ensure_ascii=False))
        (inputs/'task.txt').write_text(m.review_prompt(public,initial,terminal_program=True))
        episodes.append(dict(first,folder=str(folder),source_folder=str(source)))
    return episodes


def collect():
    if not (ROOT/'PLAN.json').exists():prepare()
    if (ROOT/'LOCAL_LIVE.json').exists():raise RuntimeError('inspect the existing local attempt')
    plan=m.read(ROOT/'PLAN.json');started=time.monotonic();process=log=None;unloaded=False
    if COHORT=='confirmation':
        reservation=m.read(plan['reservation']);assert reservation['status']=='CONFIRMATION_PREPARED_NOT_EXECUTED'
        reservation['status']='CONFIRMATION_IN_PROGRESS';m.study.publish(Path(plan['reservation']),reservation)
    state=dict(status='RUNNING',phase='START',pid=os.getpid(),start_ticks=Path('/proc/self/stat').read_text().split()[21],arms={})
    m.study.new(ROOT/'LOCAL_LIVE.json',state)
    try:
        unloaded=c.stop27()
        with m.study.core.resource_lock():
            h=m.study.core.helpers();checked=h.deps.verify_projection(h.actor.RUNTIME_ROOT,h.actor.RUNTIME_SHA)
            for arm in ['firstpass','ordinary','cheap37']:
                episodes=plan['episodes'] if arm=='firstpass' else prepare_reviews(arm,plan)
                state['phase']=arm;state['arms'][arm]=[];m.study.publish(ROOT/'LOCAL_LIVE.json',state)
                m.study.CAPS.clear();m.study.CAPS.update(plan['caps'] if arm=='firstpass' else plan['review_caps'])
                process,log=c.native.start_server(plan['runtime'],arm,Path(plan['adapters'][arm]),ROOT)
                try:
                    for ep in episodes:
                        if time.monotonic()-started>plan['wall_seconds']:raise TimeoutError('forward local wall cap')
                        raw=m.study.episode(ep,h,checked,m.study.MODEL,private_labels=ROOT/'LABELS_PRIVATE.json')
                        row=dict(index=ep['index'],id=ep['id'],group=ep['group'],folder=ep['folder'],
                            native_success=raw['native_success'],execution_correct=raw['execution_correct'],
                            program=raw['submitted_program'],normal=raw['agent_completed'],
                            posts=raw['accounting']['actual_forwarded_posts'],tokens=raw['accounting']['provider_total_tokens_known'],
                            unknown=len(raw['accounting']['unknown_usage_requests']),actor_seconds=raw['actor']['seconds'])
                        state['arms'][arm].append(row);state['seconds']=time.monotonic()-started
                        m.study.publish(ROOT/'LOCAL_LIVE.json',state)
                        print(json.dumps(dict(arm=arm,index=ep['index'],success=row['native_success'],posts=row['posts'],tokens=row['tokens'])),flush=True)
                        if not raw['accounting']['integrity_passed']:
                            raise RuntimeError('native transport failure retained; inspect this same attempt')
                finally:c.native.stop_server(process,log);process=log=None
            state.update(status='RETURNED',phase='LOCAL_DONE',summary={arm:dict(tasks=len(rows),success=sum(r['native_success'] for r in rows),
                posts=sum(r['posts'] for r in rows),tokens=sum(r['tokens'] for r in rows),unknown=sum(r['unknown'] for r in rows))
                for arm,rows in state['arms'].items()})
    except BaseException:state.update(status='FAILED',error=traceback.format_exc())
    finally:
        if process is not None:c.native.stop_server(process,log)
        if unloaded:state['restoration']=c.restore27()
        state['seconds']=time.monotonic()-started
        m.study.publish(ROOT/'LOCAL_LIVE.json',state);m.study.new(ROOT/'LOCAL_RESULT.json',state)
        print(json.dumps({k:v for k,v in state.items() if k!='arms'}),flush=True)


def predict(variant):
    plan=m.read(ROOT/'PLAN.json');local=m.read(ROOT/'LOCAL_RESULT.json')
    assert local['status']=='RETURNED' and all(len(rows)==len(plan['episodes']) for rows in local['arms'].values())
    assert not (ROOT/'TEACHER_LIVE.json').exists()
    av.VARIANT=variant;av.ROOT=ROOT.parent/POLICIES[variant]
    cheap={row['index']:row for row in local['arms']['cheap37']}
    av.predict(sources=plan['episodes'],cheap=cheap,output=ROOT/(variant+'_PREDICTIONS.json'),
        strong_budget=plan['teacher_task_budget'],fixed_threshold=-1.01)


def predict_all():
    plan=m.read(ROOT/'PLAN.json');local=m.read(ROOT/'LOCAL_RESULT.json');assert local['status']=='RETURNED'
    state=dict(status='RUNNING',phase='PREDICT',pid=os.getpid(),start_ticks=Path('/proc/self/stat').read_text().split()[21])
    m.study.new(ROOT/'PREDICT_LIVE.json',state);unloaded=False;child=None
    try:
        restored=local.get('restoration')
        if restored:
            deadline=time.monotonic()+90
            while True:
                owner=m.read(m.study.PRIVATE/'research_services/gpu_guard_current.json')
                stat=Path('/proc',str(restored['pid']),'stat')
                if owner['pid']==restored['pid'] or not stat.exists() or stat.read_text().split()[2] in ['Z','X']:break
                if time.monotonic()>deadline:raise TimeoutError('restored GPU owner has not registered; refusing a second model')
                time.sleep(1)
        unloaded=c.stop27()
        for variant in POLICIES:
            with (ROOT/(variant+'_predict.log')).open('xb') as log:
                child=subprocess.Popen([str(c.repo/'venv/bin/python'),'-u','-B',__file__,'predict','--variant',variant,'--cohort',COHORT],
                    cwd=c.repo,stdout=log,stderr=subprocess.STDOUT)
                state.update(variant=variant,child_pid=child.pid);m.study.publish(ROOT/'PREDICT_LIVE.json',state)
                code=child.wait(timeout=1800)
            if code:raise RuntimeError(variant+' prediction failed; retain the same attempt')
        freeze_policies()
        state.update(status='RETURNED',phase='READY_FOR_TEACHER')
    except BaseException:state.update(status='FAILED',error=traceback.format_exc())
    finally:
        if child is not None and child.poll() is None:
            child.terminate()
            try:child.wait(timeout=30)
            except subprocess.TimeoutExpired:child.kill();child.wait()
        if unloaded:state['restoration']=c.restore27()
        m.study.publish(ROOT/'PREDICT_LIVE.json',state);m.study.new(ROOT/'PREDICT_RESULT.json',state)
        print(json.dumps(state),flush=True)


def freeze_policies():
    plan=m.read(ROOT/'PLAN.json');predictions={name:m.read(ROOT/(name+'_PREDICTIONS.json')) for name in POLICIES}
    for pred in predictions.values():
        assert len(pred['decisions'])==len(plan['episodes']) and all(row['id']==source['id'] and row['index']==source['index']
            for row,source in zip(pred['decisions'],plan['episodes'],strict=True))
    assert not (ROOT/'TEACHER_LIVE.json').exists()
    orders={name:[r['index'] for r in sorted(pred['decisions'],key=lambda row:(-row['score'],row['index']))]
        for name,pred in predictions.items()}
    order=list(range(len(plan['episodes'])));random.Random(plan['random_seed']).shuffle(order);orders['random_fixed']=order
    m.study.new(ROOT/'POLICIES.json',dict(orders=orders,budget=plan['teacher_task_budget'],
        secondary_budgets=plan['secondary_task_budgets'],classifiers={name:{k:pred[k] for k in
            ['forward_calls','input_tokens_processed','forward_seconds','seconds']} for name,pred in predictions.items()},
        teacher_pool='All original first-pass snapshots, one shared realization, no outcome-based selection',
        scope=plan['scope']))


def teacher(key):
    from scripts.graph.research_school_gateway import BatchBudget,SchoolBackend,BASE_URL,MODEL,REQUEST_TOKEN_CEILING
    plan=m.read(ROOT/'PLAN.json');policies=m.read(ROOT/'POLICIES.json')
    assert m.read(ROOT/'PREDICT_RESULT.json')['status']=='RETURNED' and len(policies['orders']['value'])==len(plan['episodes'])
    reference=m.read(av.TEACHER/'PLAN.json');profile=reference['model'];assert profile['model_id']==MODEL
    budget=BatchBudget(ROOT/'teacher_budget',posts=6*len(plan['episodes']),tokens=2_000_000);backend=SchoolBackend(key,budget,m.study.core)
    backend.verify(profile);episodes=prepare_reviews('teacher',plan)
    started=time.monotonic();state=dict(status='RUNNING',pid=os.getpid(),start_ticks=Path('/proc/self/stat').read_text().split()[21],episodes=[])
    def persist():
        state.update(posts=sum(row['state']!='not_sent' for row in budget.rows),
            known_tokens=sum(row.get('usage',{}).get('total_tokens',0) for row in budget.rows),
            unknown=sum(row['state']=='unknown' for row in budget.rows),seconds=time.monotonic()-started)
        state['unknown_reserved_tokens']=state['unknown']*REQUEST_TOKEN_CEILING
        m.study.publish(ROOT/'TEACHER_LIVE.json',state)
    persist()
    try:
        with m.study.core.resource_lock():
            h=m.study.core.helpers();checked=h.deps.verify_projection(h.actor.RUNTIME_ROOT,h.actor.RUNTIME_SHA)
            m.study.CAPS.clear();m.study.CAPS.update(reference['caps'])
            for ep in episodes:
                raw=m.study.episode(ep,h,checked,profile,private_labels=ROOT/'LABELS_PRIVATE.json',relay_factory=backend.make_relay)
                state['episodes'].append(dict(index=ep['index'],id=ep['id'],folder=ep['folder'],native_success=raw['native_success'],
                    program=raw['submitted_program'],normal=raw['agent_completed'],posts=raw['accounting']['actual_forwarded_posts'],
                    tokens=raw['accounting']['provider_total_tokens_known'],unknown=len(raw['accounting']['unknown_usage_requests']),
                    actor_seconds=raw['actor']['seconds']))
                persist();print(json.dumps(dict(index=ep['index'],success=raw['native_success'])),flush=True)
                if not raw['accounting']['integrity_passed']:raise RuntimeError('native transport failure retained; no automatic retry')
        state.update(status='RETURNED')
    except BaseException:state.update(status='FAILED',error=traceback.format_exc())
    finally:
        if budget.pending is not None:budget.finish()
        persist();budget.close();m.study.new(ROOT/'TEACHER_RESULT.json',state)
        print(json.dumps({k:v for k,v in state.items() if k!='episodes'}),flush=True)


def launch_teacher():
    import getpass
    assert m.read(ROOT/'PREDICT_RESULT.json')['status']=='RETURNED'
    if (ROOT/'TEACHER_LIVE.json').exists():raise RuntimeError('inspect the existing teacher attempt')
    print('CREDENTIAL_INPUT_READY',flush=True)
    key=os.environ.get('BUPT_API_KEY') or getpass.getpass('Campus credential (hidden): ')
    output=(ROOT/'teacher.log').open('xb');pid=os.fork()
    if pid:output.close();print('CAMPUS_WORKER_PID='+str(pid),flush=True);return
    os.setsid();os.dup2(output.fileno(),1);os.dup2(output.fileno(),2)
    null=os.open(os.devnull,os.O_RDONLY);os.dup2(null,0);os.close(null)
    try:
        teacher(key)
        if m.read(ROOT/'TEACHER_RESULT.json')['status']=='RETURNED':compare()
    except BaseException:traceback.print_exc()
    finally:os._exit(0)


def progress_control():
    """Hold selected tasks/teacher fixed; vary only the retained local program."""
    plan=m.read(ROOT/'PLAN.json');local=m.read(ROOT/'LOCAL_RESULT.json');teacher_rows=m.read(ROOT/'TEACHER_RESULT.json')['episodes']
    assert m.read(ROOT/'COMPARISON.json')['status']=='RETURNED'
    labels=m.read(ROOT/'LABELS_PRIVATE.json');order=m.read(ROOT/'POLICIES.json')['orders']['value'];results={}
    for arm,programs in local['arms'].items():
        outcomes=[]
        for source,current,teacher_row,label in zip(plan['episodes'],programs,teacher_rows,labels,strict=True):
            assert source['id']==current['id']==teacher_row['id']==label['id']
            public=m.read(Path(source['folder'])/'inputs/public.json')
            program,keep=av.guarded_program(current['program'],teacher_row['program'],public,teacher_row['normal'])
            correct=m.task.grade(program,public,label['exe_ans'])['execution_correct']
            outcomes.append(dict(index=source['index'],before=current['native_success'],after=correct,guard_keep=keep))
        results[arm]={}
        for k in [7,10,16,57]:
            selected=set(order[:k]);results[arm][str(k)]=sum(row['after'] if row['index'] in selected else row['before'] for row in outcomes)
    result=dict(status='RETURNED',tables=results,new_http_posts=0,new_model_forwards=0,
        scope='CPU execution/replay of existing actual programs. Value choices were frozen on cheap37 states and remain fixed here. '
            'This isolates retained-program contribution at identical selected teacher tasks, not a newly scored selector on firstpass/ordinary inputs. '
            'At57 all tasks use the teacher/controller. Firstpass is common; ordinary or cheap37 stages cost extra.')
    m.study.new(ROOT/'STAGE_PROGRESS_CONTROL.json',result);print(json.dumps(result),flush=True)


def compare():
    plan=m.read(ROOT/'PLAN.json');local=m.read(ROOT/'LOCAL_RESULT.json');native=m.read(ROOT/'TEACHER_RESULT.json')
    policies=m.read(ROOT/'POLICIES.json');labels=m.read(ROOT/'LABELS_PRIVATE.json')
    assert local['status']==native['status']=='RETURNED' and len(native['episodes'])==len(plan['episodes'])
    rows=[]
    for source,cheap,teacher_row,label in zip(plan['episodes'],local['arms']['cheap37'],native['episodes'],labels,strict=True):
        i=source['index'];assert i==cheap['index']==teacher_row['index']==label['index']
        assert source['id']==cheap['id']==teacher_row['id']==label['id']
        public=m.read(Path(source['folder'])/'inputs/public.json')
        program,keep=av.guarded_program(cheap['program'],teacher_row['program'],public,teacher_row['normal'])
        final=ROOT/'final'/f'{i:03d}';final.mkdir(parents=True)
        m.task.submit_program(program,public,final,origin='frozen_forward_teacher_with_scale_guard')
        after=m.task.grade(program,public,label['exe_ans'])['execution_correct']
        original_program,_=av.guarded_program(local['arms']['firstpass'][i]['program'],teacher_row['program'],public,teacher_row['normal'])
        original_after=m.task.grade(original_program,public,label['exe_ans'])['execution_correct']
        if COHORT=='confirmation':
            original_final=ROOT/'original_guard_final'/f'{i:03d}';original_final.mkdir(parents=True)
            m.task.submit_program(original_program,public,original_final,origin='full_teacher_guarding_original_program')
        rows.append(dict(index=i,before=cheap['native_success'],after=after,utility=int(after)-int(cheap['native_success']),
            teacher=teacher_row['native_success'],guard_keep=keep,semantic=m.task.execute_public(cheap['program'],public)['status']=='executed',
            guarded_program=program,original_guard_after=original_after,
            posts=teacher_row['posts'],tokens=teacher_row['tokens'],actor_seconds=teacher_row['actor_seconds']))
    base=sum(r['before'] for r in rows);tables={}
    for k in policies['secondary_budgets']:
        table={}
        for name,order in policies['orders'].items():
            chosen={*order[:k]};rr=[r for r in rows if r['index'] in chosen]
            table[name]=dict(success=base+sum(r['utility'] for r in rr),recovered=sum(r['utility']>0 for r in rr),
                damaged=sum(r['utility']<0 for r in rr),semantic_recovered=sum(r['utility']>0 and r['semantic'] for r in rr),
                acquisitions=k,teacher_posts=sum(r['posts'] for r in rr),teacher_tokens=sum(r['tokens'] for r in rr),
                teacher_actor_seconds=sum(r['actor_seconds'] for r in rr))
        tables[str(k)]=table
    costs={arm:dict(posts=sum(r['posts'] for r in rr),tokens=sum(r['tokens'] for r in rr),
        actor_seconds=sum(r['actor_seconds'] for r in rr),unknown=sum(r['unknown'] for r in rr))
        for arm,rr in local['arms'].items()}
    costs['teacher_full']=dict(posts=native['posts'],tokens=native['known_tokens'],
        actor_seconds=sum(r['actor_seconds'] for r in native['episodes']),unknown=native['unknown'])
    if COHORT=='confirmation':
        for name,order in policies['orders'].items():
            selected=set(order[:policies['budget']]);successes=0
            for source,row,label in zip(plan['episodes'],rows,labels,strict=True):
                i=source['index'];program=row['guarded_program'] if i in selected else local['arms']['cheap37'][i]['program']
                public=m.read(Path(source['folder'])/'inputs/public.json');final=ROOT/'policy_final'/name/f'{i:03d}';final.mkdir(parents=True)
                m.task.submit_program(program,public,final,origin='frozen_confirmation_'+name)
                successes+=m.task.grade(program,public,label['exe_ans'])['execution_correct']
            assert successes==tables[str(policies['budget'])][name]['success']
    result=dict(status='RETURNED',tasks=len(plan['episodes']),local=local['summary'],teacher_native=sum(r['teacher'] for r in rows),
        all_teacher_guard=sum(r['after'] for r in rows),tables=tables,outcomes=rows,classifiers=policies['classifiers'],
        teacher_guard_original=sum(r['original_guard_after'] for r in rows),
        stage_costs=costs,cost_rule='Firstpass is common; selective policies add cheap37, their own classifier and selected teacher. '
            'Raw direct teacher and teacher_guard_original add only teacher_full to firstpass; all_teacher_guard also adds cheap37. '
            'Actor seconds are not end-to-end wall time; HF inputs are separate from provider tokens.',
        physical_new_campus=dict(posts=native['posts'],tokens=native['known_tokens'],unknown=native['unknown'],seconds=native['seconds']),
        scope=plan['scope']+' All common teacher trajectories ran through OpenCode. '
            'Selected-policy totals replay common native candidates. All guarded finals submitted through the task executor. '
            'Teacher and local formation costs charged physically once.')
    m.study.new(ROOT/'COMPARISON.json',result)
    if COHORT=='confirmation':
        reservation=m.read(plan['reservation']);reservation['status']='CONFIRMATION_EXECUTED_FROZEN_V1'
        m.study.publish(Path(plan['reservation']),reservation)
    print(json.dumps({k:v for k,v in result.items() if k!='outcomes'}),flush=True)


def budget_curves():
    """Descriptive full-K replay of frozen rankings, never a new model evaluation."""
    import csv
    base=c.root.parent;target=base/'FROZEN_BUDGET_CURVES.json'
    if target.exists():raise RuntimeError('curves already exist; inspect rather than regenerate')
    dev=m.read(base/'acquisition_single_state_v1/MATCHED_COMPARISON.json')
    pool=dev['pools']['shared_union']
    specifications=[('DEV64',pool['outcomes'],
        {name:[r['index'] for r in sorted(m.read(base/POLICIES[name]/'PREDICTIONS.json')['decisions'],
            key=lambda r:(-r['score'],r['index']))] for name in POLICIES},
        dev['classifiers'],dev['cheap_common'],dict(native=None,guarded=pool['policies']['all_teacher']['success']))]
    for name,folder in [('FORWARD57','forward_sources57_v1'),('CONFIRM64','confirmation64_v1')]:
        result=m.read(base/folder/'COMPARISON.json');policies=m.read(base/folder/'POLICIES.json')
        specifications.append((name,result['outcomes'],policies['orders'],result['classifiers'],
            result['stage_costs']['cheap37'],dict(native=result['teacher_native'],guarded=result['all_teacher_guard'])))
    panels={};flat=[]
    for name,rows,orders,classifiers,local_cost,reference in specifications:
        n=len(rows);assert sorted(r['index'] for r in rows)==list(range(n))
        baseline=sum(r['before'] for r in rows);by_index={r['index']:r for r in rows};curves={}
        for policy,order in orders.items():
            assert sorted(order)==list(range(n))
            points=[];success=baseline;recovered=damaged=posts=tokens=0;seconds=0.
            for k in range(n+1):
                if k:
                    r=by_index[order[k-1]];success+=r['utility'];recovered+=r['utility']>0;damaged+=r['utility']<0
                    posts+=r['posts'];tokens+=r['tokens'];seconds+=r.get('actor_seconds',r.get('seconds',0.))
                point=dict(panel=name,policy=policy,K=k,success=success,rate=success/n,
                    recovered=int(recovered),damaged=int(damaged),teacher_posts=posts,teacher_tokens=tokens,
                    teacher_actor_seconds=seconds,classifier_forward_seconds=classifiers.get(policy,{}).get('forward_seconds',0.),
                    classifier_input_tokens=classifiers.get(policy,{}).get('input_tokens_processed',0))
                points.append(point);flat.append(point)
            assert points[-1]['success']==reference['guarded'];curves[policy]=points
        curves['random_expectation']=[dict(K=k,success=baseline+k/n*sum(r['utility'] for r in rows),
            teacher_tokens=k/n*sum(r['tokens'] for r in rows),teacher_actor_seconds=k/n*sum(r.get('actor_seconds',r.get('seconds',0.)) for r in rows)) for k in range(n+1)]
        differences=[curves['value'][k]['success']-curves['risk'][k]['success'] for k in range(n+1)]
        def runs(sign):
            selected=[k for k,d in enumerate(differences) if (d>0 if sign>0 else d<0)];groups=[]
            for k in selected:
                if groups and groups[-1][1]+1==k:groups[-1][1]=k
                else:groups.append([k,k])
            return groups
        panels[name]=dict(tasks=n,baseline=baseline,teacher_reference=reference,local_stage=local_cost,
            classifiers=classifiers,curves=curves,value_minus_risk=differences,
            value_better_K_ranges=runs(1),risk_better_K_ranges=runs(-1),
            equal_K=[k for k,d in enumerate(differences) if d==0])
    result=dict(status='RETURNED',panels=panels,new_model_posts=0,new_training_updates=0,
        scope='Post-hoc descriptive analysis of every K using frozen rankings and common actual native teacher candidates. No new confirmation evaluation, no policy/model change, no selection of a new operating budget.',
        cost_rule='Report local generation, classifier forwards/seconds, and teacher tokens/actor-seconds separately. No equal-cost token summation; actor work is not end-to-end wall time. Confirmation classifier timings retain the previously disclosed residency overlap.',
        random_rule='Uniform-random expected utility at every K. Forward/confirmation also retain their original complete fixed random order; DEV original random control exists only at its frozen primary budget.')
    m.study.new(target,result)
    with target.with_suffix('.csv').open('x',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(flat[0]));writer.writeheader();writer.writerows(flat)
    for name,panel in panels.items():
        ks=sorted({k for k in [0,4,7,8,10,12,16,18,24,panel['tasks']] if k<=panel['tasks']})
        print(json.dumps(dict(panel=name,value_better=panel['value_better_K_ranges'],risk_better=panel['risk_better_K_ranges'],
            selected=[dict(K=k,**{policy:panel['curves'][policy][k]['success'] for policy in POLICIES},
                value_teacher_tokens=panel['curves']['value'][k]['teacher_tokens']) for k in ks])),flush=True)


def budget_difference_cases():
    """Explain curve crossings by exclusive selections, without changing policies."""
    base=c.root.parent;output=base/'FROZEN_BUDGET_CASES.json'
    if output.exists():raise RuntimeError('case analysis already exists')
    cases={}
    for name,folder in [('DEV64',None),('FORWARD57','forward_sources57_v1'),('CONFIRM64','confirmation64_v1')]:
        if folder is None:
            rows=m.read(base/'acquisition_single_state_v1/MATCHED_COMPARISON.json')['pools']['shared_union']['outcomes']
            orders={p:[r['index'] for r in sorted(m.read(base/POLICIES[p]/'PREDICTIONS.json')['decisions'],
                key=lambda r:(-r['score'],r['index']))] for p in ['value','risk']}
        else:
            rows=m.read(base/folder/'COMPARISON.json')['outcomes'];orders=m.read(base/folder/'POLICIES.json')['orders']
        by={r['index']:r for r in rows};cases[name]={}
        for k in [4,8,12,16,18,24]:
            a,b=set(orders['value'][:k]),set(orders['risk'][:k]);parts={}
            for label,selected in [('common',a&b),('value_only',a-b),('risk_only',b-a)]:
                detail=[dict(index=i,local_correct=by[i]['before'],after_guard=bool(by[i].get('after',by[i].get('success'))),
                    utility=by[i]['utility'],teacher_tokens=by[i]['tokens'],teacher_native_correct=by[i].get('teacher')) for i in sorted(selected)]
                parts[label]=dict(recovered=sum(r['utility']>0 for r in detail),damaged=sum(r['utility']<0 for r in detail),
                    still_wrong=sum(not r['local_correct'] and not r['after_guard'] for r in detail),details=detail)
            parts['value_minus_risk']=sum(by[i]['utility'] for i in a)-sum(by[i]['utility'] for i in b)
            cases[name][str(k)]=parts
    m.study.new(output,dict(status='RETURNED',cases=cases,new_model_posts=0,
        scope='Descriptive matched-pool attribution. Exclusive selection outcomes explain observed differences, not unobserved teacher sampling or a universally optimal K.'))
    print(json.dumps({name:{k:{label:{a:b for a,b in d.items() if a!='details'} if isinstance(d,dict) else d
        for label,d in case.items()} for k,case in rr.items() if k in ['8','18']} for name,rr in cases.items()}),flush=True)


def plot_budget_curves(source,destination):
    """Export full frozen curves with teacher cost separate from local compute."""
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    result=m.read(source);destination=Path(destination);destination.parent.mkdir(parents=True,exist_ok=True)
    fig,axes=plt.subplots(2,3,figsize=(12.2,7.1),layout='constrained')
    styles=dict(value=('#0072B2','-'),risk=('#D55E00','--'),single=('#009E73','-.'),random_fixed=('#999999',':'),random_expectation=('#333333',':'))
    names=dict(value='Multi-state value',risk='Error risk',single='Single-state value',random_fixed='Fixed random',random_expectation='Random expectation')
    for column,(name,panel) in enumerate(result['panels'].items()):
        primary=16 if name=='FORWARD57' else 18
        for policy,points in panel['curves'].items():
            color,style=styles[policy]
            for row in range(2):
                x=[p['K'] if not row else p['teacher_tokens']/1000 for p in points]
                axes[row,column].plot(x,[p['success'] for p in points],color=color,linestyle=style,
                    linewidth=1.7 if policy in ['value','risk'] else 1.1,label=names[policy])
                if policy in POLICIES:
                    p=points[primary];axes[row,column].scatter(p['K'] if not row else p['teacher_tokens']/1000,
                        p['success'],s=24,color=color,zorder=4)
        for row in range(2):
            axes[row,column].grid(alpha=.2);axes[row,column].set_xlabel('Teacher task budget K' if not row else 'Teacher tokens (thousands)')
            axes[row,column].set_ylabel('Successful tasks');axes[row,column].set_title(name+' (n='+str(panel['tasks'])+')')
            axes[row,column].tick_params(labelsize=8)
        axes[0,column].axvline(primary,color='#777777',alpha=.4,linewidth=.8)
    handles,labels=axes[0,1].get_legend_handles_labels()
    fig.legend(handles,labels,loc='outside lower center',ncol=5,fontsize=8,frameon=False)
    fig.suptitle('Frozen FinQA rankings: full-budget replay; dots mark original primary budgets',fontsize=11)
    for extension in ['png','pdf']:fig.savefig(destination.with_suffix('.'+extension),dpi=180)
    plt.close(fig)


def launch_run():
    import getpass
    assert (ROOT/'PROTOCOL.json').exists() and not (ROOT/'LOCAL_LIVE.json').exists()
    print('CREDENTIAL_INPUT_READY',flush=True)
    key=os.environ.get('BUPT_API_KEY') or getpass.getpass('Campus credential (hidden): ')
    output=(ROOT/'driver.log').open('xb');pid=os.fork()
    if pid:output.close();print('COHORT_WORKER_PID='+str(pid),flush=True);return
    os.setsid();os.dup2(output.fileno(),1);os.dup2(output.fileno(),2)
    null=os.open(os.devnull,os.O_RDONLY);os.dup2(null,0);os.close(null)
    state=dict(status='RUNNING',pid=os.getpid(),start_ticks=Path('/proc/self/stat').read_text().split()[21],phase='LOCAL')
    try:
        collect();assert m.read(ROOT/'LOCAL_RESULT.json')['status']=='RETURNED'
        state['phase']='PREDICT'
        predict_all();assert m.read(ROOT/'PREDICT_RESULT.json')['status']=='RETURNED'
        state['phase']='TEACHER'
        teacher(key);assert m.read(ROOT/'TEACHER_RESULT.json')['status']=='RETURNED'
        state['phase']='COMPARE';compare();state.update(status='RETURNED',phase='CLOSED')
    except BaseException:state.update(status='FAILED',error=traceback.format_exc());traceback.print_exc()
    finally:m.study.new(ROOT/'RUN_RESULT.json',state);os._exit(0)


def manuscript_evidence():
    """Summarize frozen native outcomes; no inference, regrading or policy selection."""
    import numpy as np
    base=c.root.parent;target=base/'PAPER_DRAFT_EVIDENCE_V1.json'
    if target.exists():raise RuntimeError('manuscript evidence exists; inspect rather than overwrite')
    comparisons=[];rng=np.random.default_rng(171118);draws=20000
    def paired(panel,name,first,second):
        assert len(first)==len(second) and len(first)>0
        d=np.asarray(first,dtype=np.int8)-np.asarray(second,dtype=np.int8)
        boot=rng.choice(d,size=(draws,len(d)),replace=True).mean(axis=1)
        comparisons.append(dict(panel=panel,comparison=name,n=len(d),first_success=sum(first),
            second_success=sum(second),first_only=int((d==1).sum()),second_only=int((d==-1).sum()),
            difference=float(d.mean()),ci95=np.quantile(boot,[.025,.975]).tolist()))
    native=m.read(base/'paired_state_negatives_v1/native_v1/PLAN.json')
    arms={}
    for name in ['aligned_sft','paired_state_branch']:
        episodes=sorted([e for e in native['episodes'] if e['arm']==name],key=lambda e:e['index'])
        assert [e['index'] for e in episodes]==list(range(64))
        arms[name]=[m.read(Path(e['folder'])/'RESULT.json')['native_success'] for e in episodes]
    paired('FinQA DEV64','paired - ordinary',arms['paired_state_branch'],arms['aligned_sft'])
    d=m.read(base/'acquisition_single_state_v1/MATCHED_COMPARISON.json')['pools']['shared_union']
    before=[r['before'] for r in d['outcomes']]
    def outcomes(rows,selection):
        selected=set(selection)
        return [bool(r.get('after',r.get('success'))) if r['index'] in selected else bool(r['before']) for r in rows]
    chosen={name:[r['index'] for r in m.read(base/POLICIES[name]/'PREDICTIONS.json')['decisions'] if r['decision']=='TEACHER'] for name in POLICIES}
    finals={name:outcomes(d['outcomes'],indices) for name,indices in chosen.items()}
    for name in ['risk','single']:paired('FinQA DEV64','value - '+name,finals['value'],finals[name])
    paired('FinQA DEV64','value - ordinary',finals['value'],arms['aligned_sft'])
    for panel,folder,k in [('FinQA FORWARD57','forward_sources57_v1',16),('FinQA CONFIRM64','confirmation64_v1',18),
                           ('TAT-QA DEV32','flat_dsl_transfer_v1',9),('TAT-QA FORWARD32','flat_dsl_forward_v1',9)]:
        root=base/folder if folder.startswith(('forward','confirmation')) else m.study.PRIVATE/'tatqa_correction_v1'/folder
        d=m.read(root/'COMPARISON.json');local=m.read(root/'LOCAL_RESULT.json')['arms'];pol=m.read(root/'POLICIES.json')['orders']
        key='cheap37' if 'cheap37' in local else 'paired'
        def success(row):return bool(row['native_success'] if 'native_success' in row else row['success'])
        a=[success(x) for x in local[key]];b=[success(x) for x in local['ordinary']]
        paired(panel,'paired - ordinary',a,b)
        final={name:outcomes(d['outcomes'],order[:k]) for name,order in pol.items()}
        for name,result in final.items():assert sum(result)==d['tables'][str(k)][name]['success']
        for name in ['risk','single']:
            if name in final:paired(panel,'value - '+name,final['value'],final[name])
        paired(panel,'value - ordinary',final['value'],b)
    early=m.read(base/'confirmation53_v1/ANALYSIS.json')['paired_comparisons']['primary_paired_minus_sft']
    comparisons.append(dict(panel='FinQA EARLY53',comparison='paired - ordinary',n=early['n'],
        first_success=30,second_success=30,first_only=early['first_only'],second_only=early['second_only'],
        difference=early['mean_difference'],ci95=early['ci95'],source='Existing frozen 20,000-draw source bootstrap, seed17053; not recomputed.'))
    root=m.study.PRIVATE/'tatqa_correction_v1';d=m.read(root/'state_aware_teacher_v1/RESULT.json')
    initial=[r['success'] for r in m.read(root/'flat_dsl_transfer_v1/LOCAL_RESULT.json')['arms']['paired']]
    plan=m.read(root/'state_aware_teacher_v1/PLAN.json')
    for scope,selection in [('primary9',set(plan['primary_selected'])),('all32',set(range(32)))]:
        final={}
        for name in ['T0','T1']:
            rr={r['index']:r for r in d['episodes'] if r['arm']==name}
            final[name]=[bool(rr[i]['after']) if i in selection else bool(initial[i]) for i in range(32)]
            assert sum(final[name])==d['tables'][scope][name]['success']
        paired('TAT-QA TEACHER32 '+scope,'T1 - T0',final['T1'],final['T0'])
    result=dict(status='RETURNED',comparisons=comparisons,draws=draws,seed=171118,
        method='Paired percentile bootstrap of one frozen binary outcome difference per source; 95% intervals are conditional on the fixed training fit and realized teacher pool, unadjusted across comparisons.',
        scope='Descriptive manuscript analysis of existing outputs only. Confirmation models, policies, budgets, scores and reservations unchanged; no new grading, training, inference or HTTP.',
        new_model_posts=0,new_neural_forwards=0,new_training_updates=0)
    m.study.new(target,result)
    print(json.dumps(result),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('mode',choices=['prepare','collect','predict','predict-all','teacher','compare','progress-control','manuscript-evidence','run'])
    parser.add_argument('--variant',choices=list(POLICIES),default='value');parser.add_argument('--cohort',choices=['forward','confirmation'],default='forward');args=parser.parse_args()
    COHORT=args.cohort
    if COHORT=='confirmation':ROOT=c.root.parent/'confirmation64_v1'
    if args.mode=='prepare':prepare()
    elif args.mode=='collect':collect()
    elif args.mode=='predict':predict(args.variant)
    elif args.mode=='predict-all':predict_all()
    elif args.mode=='teacher':launch_teacher()
    elif args.mode=='progress-control':progress_control()
    elif args.mode=='manuscript-evidence':manuscript_evidence()
    elif args.mode=='run':launch_run()
    else:compare()
