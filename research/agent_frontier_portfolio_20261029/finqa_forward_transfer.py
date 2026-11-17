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


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('mode',choices=['prepare','collect','predict','predict-all','teacher','compare','progress-control','run'])
    parser.add_argument('--variant',choices=list(POLICIES),default='value');parser.add_argument('--cohort',choices=['forward','confirmation'],default='forward');args=parser.parse_args()
    COHORT=args.cohort
    if COHORT=='confirmation':ROOT=c.root.parent/'confirmation64_v1'
    if args.mode=='prepare':prepare()
    elif args.mode=='collect':collect()
    elif args.mode=='predict':predict(args.variant)
    elif args.mode=='predict-all':predict_all()
    elif args.mode=='teacher':launch_teacher()
    elif args.mode=='progress-control':progress_control()
    elif args.mode=='run':launch_run()
    else:compare()
