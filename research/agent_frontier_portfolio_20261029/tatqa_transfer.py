"""Zero-training transfer of the frozen FinQA correction/acquisition pipeline."""
from pathlib import Path
from types import SimpleNamespace
import argparse,copy,getpass,hashlib,json,os,shutil,subprocess,sys,time,traceback
import finqa_patch_learning as c
import finqa_acquisition_learning as av
import tatqa_correction as task

m=c.m
BASE=m.study.PRIVATE/'tatqa_correction_v1'
OLD=BASE/'native_related_v1'
ORIGINAL=BASE/'flat_dsl_transfer_v1'
ROOT=ORIGINAL


def prepare_forward():
    """Freeze unchanged settings and unseen table contexts before model execution."""
    if ROOT.exists():raise RuntimeError('forward attempt exists; inspect rather than restart')
    prior=m.read(ORIGINAL/'PLAN.json');prep=m.read(BASE/'related_dev_v1/PREPARATION.json')
    original=prior['episodes'][0];old_public=m.read(packet_at(ORIGINAL,'firstpass',original['index'])/'inputs/public.json')
    assert task.prompt(old_public,terminal_program=True)==(packet_at(ORIGINAL,'firstpass',original['index'])/'inputs/task.txt').read_text()
    excluded=set()
    for path in BASE.rglob('public.json'):
        public=m.read(path)
        if str(public.get('report','')).startswith('TAT-QA/'):excluded.add(public['report'].split('/',1)[1])
    candidates=[]
    for record in m.read(prep['source_path']):
        uid=record['table']['uid']
        if uid in excluded:continue
        for question in record['questions']:
            if question['answer_type']=='arithmetic':
                key=hashlib.sha256(('tatqa-forward-frozen-v1|'+question['uid']).encode()).hexdigest()
                candidates.append((key,uid,record,question))
    chosen=[];seen=set()
    for item in sorted(candidates,key=lambda item:item[0]):
        if item[1] in seen:continue
        seen.add(item[1]);chosen.append(item)
        if len(chosen)==32:break
    assert len(chosen)==32 and not seen&excluded
    ROOT.mkdir();episodes=[];labels=[]
    template=packet_at(ORIGINAL,'firstpass',original['index'])/'inputs'
    for index,(_,uid,record,question) in enumerate(chosen):
        public=task.public_record(record,question);folder=packet('firstpass',index);inputs=folder/'inputs'
        inputs.mkdir(parents=True);(folder/'work').mkdir();(folder/'dependencies').mkdir()
        (inputs/'public.json').write_text(json.dumps(public,ensure_ascii=False))
        (inputs/'task.txt').write_text(task.prompt(public,terminal_program=True))
        for name in ['finqa_tool.py','finqa_correction.py','executor.py','guest.py']:shutil.copyfile(template/name,inputs/name)
        episodes.append(dict(index=index,id=public['id'],report=public['report'],table_uid=uid))
        # Reference annotations are extracted only after selection and remain host-only.
        labels.append(dict(index=index,id=public['id'],report=public['report'],exe_ans=copy.deepcopy(question)))
    plan=copy.deepcopy(prior)
    plan.update(episodes=episodes,selection='Fixed public-UID hash order, arithmetic type, one question per previously unused table context; no answer/scale/value/outcome filtering.',
        excluded_previous_tables=sorted(excluded),source_path=prep['source_path'],source_split='official dev, new Agent-evaluation contexts',
        frozen_from=str(ORIGINAL),code_revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=c.repo,text=True).strip(),
        prospective_complete=True,stop='Complete all32 regardless of interim accuracy/format counts; infrastructure, memory and wall caps still apply.',
        scope='Prospective frozen-setting32-context transfer check. All original prompts, checkpoints, controller, caps and K9/secondary budgets unchanged. No training or heldout FinQA64 access.')
    m.study.new(ROOT/'LABELS_PRIVATE.json',labels);m.study.new(ROOT/'PLAN.json',plan)
    print(json.dumps(dict(prepared=32,excluded_tables=len(excluded),unique_new_tables=32,primary_K=9,training=0)),flush=True)


def prepare():
    ROOT.mkdir()
    previous=m.read(OLD/'PLAN.json');first=m.read(OLD/'firstpass/PLAN.json')['episodes']
    finqa=m.read(c.step1/'PLAN.json');runtime=finqa['runtime']
    adapters=dict(firstpass=finqa['sampler_adapter'],ordinary=str(Path(finqa['old37_adapter']).parent.parent/'aligned_sft/adapter.gguf'),
        paired=finqa['old37_adapter'])
    assert len(first)==32 and all(Path(p).is_file() for p in adapters.values())
    m.study.new(ROOT/'LABELS_PRIVATE.json',m.read(OLD/'LABELS_PRIVATE.json'))
    episodes=[]
    for ep in first:
        public=m.read(Path(ep['folder'])/'inputs/public.json');task.arithmetic.check_public(public)
        episodes.append(dict(index=ep['index'],id=ep['id'],report=ep['report'],old_folder=ep['folder']))
        folder=ROOT/'firstpass'/f"{ep['index']:03d}";inputs=folder/'inputs';inputs.mkdir(parents=True)
        (folder/'work').mkdir();(folder/'dependencies').mkdir()
        (inputs/'public.json').write_text(json.dumps(public,ensure_ascii=False))
        (inputs/'task.txt').write_text(task.prompt(public,terminal_program=True))
        for name,source in [('finqa_tool.py',Path(task.__file__)),('finqa_correction.py',Path(task.arithmetic.__file__)),
                ('executor.py',Path(ep['folder'])/'inputs/executor.py'),('guest.py',Path(ep['folder'])/'inputs/guest.py')]:
            shutil.copyfile(source,inputs/name)
    m.study.new(ROOT/'PLAN.json',dict(episodes=episodes,adapters=adapters,runtime=runtime,
        metric_dir=previous['official_metric_dir'],caps=previous['runtime']['caps'],primary_K=9,budgets=[0,4,8,9,12,16,32],
        scope='Same32 original TAT-QA DEV arithmetic contexts. Common flat functional DSL prompt, existing frozen FinQA checkpoints; no training, no gold/teacher output in Agent inputs. Original0/32 records remain intact.',
        guard='Keep local if teacher incomplete/invalid, or only a terminal factor100 differs while predicted scale is identical. Otherwise use teacher program and its predicted scale.',
        stop='Stop early if first4 firstpass outputs are all invalid. No rerun/selection by correctness. Local wall cap3600s.',
        changed='Add generic DSL grammar/examples; unchanged question, table, paragraphs, executor and official metric.'))
    print(json.dumps(dict(prepared=32,training=0,primary_K=9)),flush=True)


def packet(arm,index):return ROOT/arm/f'{index:03d}'


def packet_at(root,arm,index):return Path(root)/arm/f'{index:03d}'


def prepare_reviews(arm):
    for ep in m.read(ROOT/'PLAN.json')['episodes']:
        source=packet('firstpass',ep['index']);folder=packet(arm,ep['index'])
        for name in ['inputs','work','dependencies']:shutil.copytree(source/name,folder/name)
        public=m.read(source/'inputs/public.json')
        (folder/'inputs/task.txt').write_text(task.review_prompt(public,task.saved_state(public,source/'work')))


def collect(*, arms=('firstpass','ordinary','paired')):
    plan=m.read(ROOT/'PLAN.json');runtime=plan['runtime'];rows={};started=time.monotonic()
    state=dict(status='RUNNING',pid=os.getpid(),phase='LOCAL',arms=rows)
    m.study.publish(ROOT/'LOCAL_LIVE.json',state)
    def grade(candidate,public,label):return task.grade(candidate,public,label['exe_ans'],metric_dir=plan['metric_dir'])
    with m.study.core.resource_lock():
        h=m.study.core.helpers();checked=h.deps.verify_projection(h.actor.RUNTIME_ROOT,h.actor.RUNTIME_SHA)
        m.study.CAPS.clear();m.study.CAPS.update(plan['caps'])
        for arm in arms:
            if arm!='firstpass':prepare_reviews(arm)
            rows[arm]=[];process=log=None
            try:
                process,log=c.native.start_server(runtime,arm,Path(plan['adapters'][arm]),ROOT)
                for source in plan['episodes']:
                    if time.monotonic()-started>3600:raise TimeoutError('finite local TAT-QA budget')
                    ep=dict(source,folder=str(packet(arm,source['index'])))
                    raw=m.study.episode(ep,h,checked,m.study.MODEL,private_labels=ROOT/'LABELS_PRIVATE.json',submission_grader=grade)
                    rows[arm].append(dict(index=ep['index'],id=ep['id'],success=raw['native_success'],
                        valid=raw['program_valid'],scale_exact=raw['scale_exact'],normal=raw['agent_completed'],
                        submission=m.read(Path(ep['folder'])/'work/candidate.json') if (Path(ep['folder'])/'work/candidate.json').exists() else None,
                        posts=raw['accounting']['actual_forwarded_posts'],tokens=raw['accounting']['provider_total_tokens_known'],
                        unknown=len(raw['accounting']['unknown_usage_requests']),seconds=raw['actor']['seconds']))
                    m.study.publish(ROOT/'LOCAL_LIVE.json',state)
                    print(json.dumps(dict(arm=arm,done=len(rows[arm]),success=sum(r['success'] for r in rows[arm]),valid=sum(r['valid'] for r in rows[arm]))),flush=True)
                    if not raw['accounting']['integrity_passed']:raise RuntimeError('transport failure retained')
                    if not plan.get('prospective_complete',False) and arm=='firstpass' and len(rows[arm])==4 and not any(r['valid'] for r in rows[arm]):raise RuntimeError('all first4 programs invalid; stop rather than repeat32 failures')
            finally:
                if process is not None:c.native.stop_server(process,log)
    state.update(status='RETURNED',phase='CLOSED',seconds=time.monotonic()-started)
    m.study.new(ROOT/'LOCAL_RESULT.json',state)


def predict(*, strong_budget=9, freeze=True):
    plan=m.read(ROOT/'PLAN.json');av.m=SimpleNamespace(**vars(m))
    av.m.state_from_folder=lambda folder:task.saved_state(m.read(Path(folder)/'inputs/public.json'),Path(folder)/'work')
    sources=[dict(ep,folder=str(packet('firstpass',ep['index']))) for ep in plan['episodes']]
    cheap={ep['index']:dict(ep,folder=str(packet('paired',ep['index']))) for ep in plan['episodes']}
    try:
        for variant,folder in [('value','acquisition_value_v1'),('risk','acquisition_risk_control_v1')]:
            av.VARIANT=variant;av.ROOT=c.root.parent/folder
            av.predict(sources=sources,cheap=cheap,output=ROOT/(variant+'_PREDICTIONS.json'),strong_budget=strong_budget,fixed_threshold=-1.01)
        if freeze:freeze_policies()
    finally:
        av.m=m
        import gc,torch
        gc.collect();torch.cuda.empty_cache()


def freeze_policies():
    import random
    plan=m.read(ROOT/'PLAN.json')
    orders={name:[r['index'] for r in sorted(m.read(ROOT/(name+'_PREDICTIONS.json'))['decisions'],
        key=lambda r:(-r['score'],r['index']))] for name in ['value','risk']}
    assert all(sorted(order)==list(range(32)) for order in orders.values())
    orders['random_fixed']=random.Random(20261117).sample(range(32),32)
    m.study.new(ROOT/'POLICIES.json',dict(orders=orders,primary_K=9,budgets=plan['budgets'],random_seed=20261117,
        scope='Frozen before new teacher responses; TAT-QA is zero-training transfer, not a new training source.'))


def local_run(*, strong_budget=9, freeze=True):
    if not (ROOT/'PLAN.json').exists():prepare()
    state=dict(status='RUNNING',pid=os.getpid(),start_ticks=Path('/proc/self/stat').read_text().split()[21],phase='LOCAL')
    m.study.new(ROOT/'RUN_LIVE.json',state);unloaded=False
    try:
        unloaded=c.stop27();collect();state['phase']='PREDICT';m.study.publish(ROOT/'RUN_LIVE.json',state)
        predict(strong_budget=strong_budget,freeze=freeze)
        state.update(status='RETURNED',phase='READY_FOR_TEACHER' if freeze else 'AWAITING_POLICY_FREEZE')
    except BaseException:state.update(status='FAILED',error=traceback.format_exc());traceback.print_exc()
    finally:
        if unloaded:state['restoration']=c.restore27()
        m.study.publish(ROOT/'RUN_LIVE.json',state);m.study.new(ROOT/'RUN_RESULT.json',state)


def teacher(key):
    from scripts.graph.research_school_gateway import BatchBudget,SchoolBackend,BASE_URL,MODEL,REQUEST_TOKEN_CEILING
    assert m.read(ROOT/'RUN_RESULT.json')['status']=='RETURNED' and (ROOT/'POLICIES.json').exists()
    plan=m.read(ROOT/'PLAN.json');prepare_reviews('teacher')
    budget=BatchBudget(ROOT/'teacher_budget',posts=384,tokens=3_000_000)
    backend=SchoolBackend(key,budget,m.study.core)
    profile=dict(provider='bupt_chat_v1',base_url=BASE_URL,model_id=MODEL,context=262144,output=8192)
    backend.verify(profile);started=time.monotonic()
    state=dict(status='RUNNING',pid=os.getpid(),episodes=[])
    def persist():
        state.update(posts=sum(r['state']!='not_sent' for r in budget.rows),
            known_tokens=sum(r.get('usage',{}).get('total_tokens',0) for r in budget.rows),
            unknown=sum(r['state']=='unknown' for r in budget.rows),seconds=time.monotonic()-started)
        state['unknown_reserve']=state['unknown']*REQUEST_TOKEN_CEILING
        m.study.publish(ROOT/'TEACHER_LIVE.json',state)
    def grade(candidate,public,label):return task.grade(candidate,public,label['exe_ans'],metric_dir=plan['metric_dir'])
    try:
        with m.study.core.resource_lock():
            h=m.study.core.helpers();checked=h.deps.verify_projection(h.actor.RUNTIME_ROOT,h.actor.RUNTIME_SHA)
            m.study.CAPS.clear();m.study.CAPS.update(plan['caps'])
            for source in plan['episodes']:
                ep=dict(source,folder=str(packet('teacher',source['index'])))
                raw=m.study.episode(ep,h,checked,profile,private_labels=ROOT/'LABELS_PRIVATE.json',
                    relay_factory=backend.make_relay,submission_grader=grade)
                candidate=Path(ep['folder'])/'work/candidate.json'
                state['episodes'].append(dict(index=ep['index'],id=ep['id'],success=raw['native_success'],
                    valid=raw['program_valid'],normal=raw['agent_completed'],
                    submission=m.read(candidate) if candidate.exists() else None,
                    posts=raw['accounting']['actual_forwarded_posts'],tokens=raw['accounting']['provider_total_tokens_known'],
                    seconds=raw['actor']['seconds']))
                persist();print(json.dumps(dict(teacher_done=len(state['episodes']),success=sum(r['success'] for r in state['episodes']))),flush=True)
                if not raw['accounting']['integrity_passed']:raise RuntimeError('teacher transport failure retained')
        state['status']='RETURNED'
    except BaseException:state.update(status='FAILED',error=traceback.format_exc());raise
    finally:
        if budget.pending is not None:budget.finish()
        persist();budget.close();m.study.new(ROOT/'TEACHER_RESULT.json',state)


def compare():
    plan=m.read(ROOT/'PLAN.json');local=m.read(ROOT/'LOCAL_RESULT.json');native=m.read(ROOT/'TEACHER_RESULT.json')
    policies=m.read(ROOT/'POLICIES.json');labels=m.read(ROOT/'LABELS_PRIVATE.json');rows=[]
    assert local['status']==native['status']=='RETURNED' and len(native['episodes'])==32
    for source,cheap,teacher_row,label in zip(plan['episodes'],local['arms']['paired'],native['episodes'],labels,strict=True):
        assert source['id']==cheap['id']==teacher_row['id']==label['id']
        public=m.read(packet('firstpass',source['index'])/'inputs/public.json')
        a,b=cheap['submission'],teacher_row['submission'];keep=not teacher_row['normal'] or not teacher_row['valid']
        if isinstance(a,dict) and isinstance(b,dict) and a['scale']==b['scale']:
            keep=keep or av.percent_scale_only(a['program'],b['program'])
        selected=a if keep else b
        normal=cheap['normal'] if keep else teacher_row['normal']
        graded=task.grade(selected,public,label['exe_ans'],metric_dir=plan['metric_dir'])
        correct=bool(graded['execution_correct'] and normal)
        rows.append(dict(index=source['index'],before=cheap['success'],after=correct,
            utility=int(correct)-int(cheap['success']),guard_keep=keep,submission=selected,
            teacher_posts=teacher_row['posts'],teacher_tokens=teacher_row['tokens'],teacher_seconds=teacher_row['seconds']))
    baseline=sum(r['before'] for r in rows);tables={}
    for k in plan['budgets']:
        tables[str(k)]={}
        for name,order in policies['orders'].items():
            chosen={*order[:k]};selected=[r for r in rows if r['index'] in chosen]
            tables[str(k)][name]=dict(success=baseline+sum(r['utility'] for r in selected),
                recovered=sum(r['utility']>0 for r in selected),damaged=sum(r['utility']<0 for r in selected),
                teacher_tasks=k,teacher_posts=sum(r['teacher_posts'] for r in selected),
                teacher_tokens=sum(r['teacher_tokens'] for r in selected),teacher_actor_seconds=sum(r['teacher_seconds'] for r in selected))
    result=dict(status='RETURNED',tasks=32,local={name:dict(success=sum(r['success'] for r in rr),
        valid=sum(r['valid'] for r in rr),posts=sum(r['posts'] for r in rr),tokens=sum(r['tokens'] for r in rr),
        unknown=sum(r['unknown'] for r in rr),actor_seconds=sum(r['seconds'] for r in rr)) for name,rr in local['arms'].items()},
        teacher_native=sum(r['success'] for r in native['episodes']),all_teacher_guard=sum(r['after'] for r in rows),
        primary_K=9,tables=tables,outcomes=rows,
        classifiers={name:{k:v for k,v in m.read(ROOT/(name+'_PREDICTIONS.json')).items() if k in ['forward_calls','input_tokens_processed','forward_seconds','seconds']} for name in ['value','risk']},
        physical_campus={k:native[k] for k in ['posts','known_tokens','unknown','unknown_reserve','seconds']},
        scope='Frozen FinQA checkpoints transferred without TAT-QA training. Local and teacher episodes actually run OpenCode; selective policies replay the fixed common teacher candidates. Official arithmetic EM/F1 remains host-only; primary budget fixed before teacher responses.')
    m.study.new(ROOT/'COMPARISON.json',result);print(json.dumps({k:v for k,v in result.items() if k!='outcomes'}),flush=True)


def autopsy():
    local=m.read(ROOT/'LOCAL_RESULT.json')['arms'];teachers=m.read(ROOT/'TEACHER_RESULT.json')['episodes']
    result=dict(status='RETURNED',new_model_posts=0,comparisons={},scale_guard_changes=[])
    for name,a,b in [('paired_vs_ordinary',local['ordinary'],local['paired']),('paired_vs_firstpass',local['firstpass'],local['paired'])]:
        repair=[dict(index=x['index'],before=x['submission'],after=y['submission'],before_valid=x['valid'])
            for x,y in zip(a,b,strict=True) if not x['success'] and y['success']]
        harm=[x['index'] for x,y in zip(a,b,strict=True) if x['success'] and not y['success']]
        result['comparisons'][name]=dict(recovered=len(repair),damaged=len(harm),semantic_recovered=sum(x['before_valid'] for x in repair),repairs=repair,harms=harm)
    for a,b in zip(local['paired'],teachers,strict=True):
        x,y=a['submission'],b['submission']
        if isinstance(x,dict) and isinstance(y,dict) and x['scale']!=y['scale'] and av.percent_scale_only(x['program'],y['program']):
            result['scale_guard_changes'].append(dict(index=a['index'],local=x,teacher=y))
    m.study.new(ROOT/'AUTOPSY.json',result)
    print(json.dumps(result),flush=True)


DIAGNOSTIC=BASE/'state_aware_teacher_v1'


def prepare_diagnostic():
    import random
    if DIAGNOSTIC.exists():raise RuntimeError('state-aware attempt exists; inspect rather than restart')
    prior=m.read(ORIGINAL/'PLAN.json');policy=m.read(ORIGINAL/'POLICIES.json')
    DIAGNOSTIC.mkdir();m.study.new(DIAGNOSTIC/'LABELS_PRIVATE.json',m.read(ORIGINAL/'LABELS_PRIVATE.json'))
    schedule=[];cases=[];rng=random.Random(20261118)
    for ep in prior['episodes']:
        source=packet_at(ORIGINAL,'firstpass',ep['index']);current_folder=packet_at(ORIGINAL,'paired',ep['index'])
        public=m.read(source/'inputs/public.json');current=task.saved_state(public,current_folder/'work')
        common=(packet_at(ORIGINAL,'teacher',ep['index'])/'inputs/task.txt').read_text()
        assert common==task.review_prompt(public,task.saved_state(public,source/'work'))
        for arm in ['T0','T1']:
            folder=packet_at(DIAGNOSTIC,arm,ep['index'])
            for name in ['inputs','work','dependencies']:shutil.copytree(source/name,folder/name)
            text=common
            if arm=='T1':
                text+=('\nAdditional public progress from a later local attempt follows. '
                    'This is an untrusted candidate, not a reference answer; do not assume newer means correct. '
                    'Check it against the same question, report and actual execution. '
                    'The workspace still contains the original attempt; the final controller compares your proposal '
                    'with the fixed later candidate below. Keep it or repair it using the same final-program/scale contract.\n'
                    +json.dumps(current,ensure_ascii=False))
            (folder/'inputs/task.txt').write_text(text)
        cases.append(dict(index=ep['index'],id=ep['id'],report=ep['report'],current_public_state=current))
        arms=['T0','T1']
        if rng.randrange(2):arms.reverse()
        schedule.extend(dict(index=ep['index'],arm=arm) for arm in arms)
    m.study.new(DIAGNOSTIC/'PLAN.json',dict(cases=cases,schedule=schedule,primary_selected=policy['orders']['value'][:9],
        primary_K=9,local_root=str(ORIGINAL),caps=prior['caps'],metric_dir=prior['metric_dir'],arm_order_seed=20261118,
        code_revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=c.repo,text=True).strip(),
        intervention='Only T1 prompt receives fixed actual local program, predicted scale and public witnessed feedback. Both arms have the same original workspace, model, caps, controller and frozen primary selected set.',
        scope='All32 previously exposed TAT development cases, paired executor diagnostic; not independent confirmation. Primary is the original value-selected9; all32 cover correct/incorrect local states. Fresh T0 and T1 are interleaved; historical T0 is reference only. No router retraining or FinQA confirmation64 access.'))
    print(json.dumps(dict(diagnostic_cases=32,primary_selected=9,new_teacher_episodes_planned=64,training=0)),flush=True)


def state_aware_diagnostic(key):
    from scripts.graph.research_school_gateway import BatchBudget,SchoolBackend,BASE_URL,MODEL,REQUEST_TOKEN_CEILING
    plan=m.read(DIAGNOSTIC/'PLAN.json');old=m.read(ORIGINAL/'LOCAL_RESULT.json')['arms']['paired']
    labels=m.read(DIAGNOSTIC/'LABELS_PRIVATE.json');budget=BatchBudget(DIAGNOSTIC/'budget',posts=768,tokens=6_000_000)
    backend=SchoolBackend(key,budget,m.study.core)
    profile=dict(provider='bupt_chat_v1',base_url=BASE_URL,model_id=MODEL,context=262144,output=8192)
    backend.verify(profile);started=time.monotonic();state=dict(status='RUNNING',pid=os.getpid(),episodes=[])
    def persist():
        state.update(posts=sum(r['state']!='not_sent' for r in budget.rows),
            known_tokens=sum(r.get('usage',{}).get('total_tokens',0) for r in budget.rows),
            unknown=sum(r['state']=='unknown' for r in budget.rows),seconds=time.monotonic()-started)
        state['unknown_reserve']=state['unknown']*REQUEST_TOKEN_CEILING;m.study.publish(DIAGNOSTIC/'LIVE.json',state)
    def grade(candidate,public,label):return task.grade(candidate,public,label['exe_ans'],metric_dir=plan['metric_dir'])
    try:
        with m.study.core.resource_lock():
            h=m.study.core.helpers();checked=h.deps.verify_projection(h.actor.RUNTIME_ROOT,h.actor.RUNTIME_SHA)
            m.study.CAPS.clear();m.study.CAPS.update(plan['caps'])
            for item in plan['schedule']:
                if time.monotonic()-started>5400:raise TimeoutError('finite paired teacher diagnostic')
                i=item['index'];case=plan['cases'][i];arm=item['arm'];folder=packet_at(DIAGNOSTIC,arm,i)
                ep=dict(index=i,id=case['id'],report=case['report'],folder=str(folder))
                raw=m.study.episode(ep,h,checked,profile,private_labels=DIAGNOSTIC/'LABELS_PRIVATE.json',
                    relay_factory=backend.make_relay,submission_grader=grade)
                candidate=folder/'work/candidate.json';proposal=m.read(candidate) if candidate.exists() else None
                local=old[i];a=local['submission'];keep=not raw['agent_completed'] or not raw['program_valid']
                if isinstance(a,dict) and isinstance(proposal,dict) and a['scale']==proposal['scale']:
                    keep=keep or av.percent_scale_only(a['program'],proposal['program'])
                selected=a if keep else proposal;normal=local['normal'] if keep else raw['agent_completed']
                public=m.read(folder/'inputs/public.json');after=bool(task.grade(selected,public,labels[i]['exe_ans'],
                    metric_dir=plan['metric_dir'])['execution_correct'] and normal)
                state['episodes'].append(dict(index=i,id=case['id'],arm=arm,before=local['success'],after=after,
                    utility=int(after)-int(local['success']),teacher_success=raw['native_success'],guard_keep=keep,
                    proposal=proposal,selected=selected,posts=raw['accounting']['actual_forwarded_posts'],
                    tokens=raw['accounting']['provider_total_tokens_known'],actor_seconds=raw['actor']['seconds']))
                persist();print(json.dumps(dict(diagnostic_done=len(state['episodes']),index=i,arm=arm,after=after)),flush=True)
                if not raw['accounting']['integrity_passed']:raise RuntimeError('paired teacher transport failure retained')
        table={};baseline=sum(r['success'] for r in old)
        for scope,selection in [('primary9',set(plan['primary_selected'])),('all32',set(range(32)))]:
            table[scope]={}
            for arm in ['T0','T1']:
                rr=[r for r in state['episodes'] if r['arm']==arm and r['index'] in selection]
                assert len(rr)==len(selection)
                table[scope][arm]=dict(success=baseline+sum(r['utility'] for r in rr),
                    recovered=sum(r['utility']>0 for r in rr),damaged=sum(r['utility']<0 for r in rr),
                    initially_wrong=sum(not r['before'] for r in rr),initially_correct=sum(r['before'] for r in rr),
                    teacher_tasks=len(rr),teacher_posts=sum(r['posts'] for r in rr),teacher_tokens=sum(r['tokens'] for r in rr),
                    teacher_actor_seconds=sum(r['actor_seconds'] for r in rr))
            a={r['index']:r for r in state['episodes'] if r['arm']=='T0'}
            b={r['index']:r for r in state['episodes'] if r['arm']=='T1'}
            table[scope]['paired']=dict(T1_wins=sum(b[i]['after'] and not a[i]['after'] for i in selection),
                T1_losses=sum(a[i]['after'] and not b[i]['after'] for i in selection))
        state.update(status='RETURNED',baseline=baseline,tables=table,
            historical_T0_reference=m.read(ORIGINAL/'COMPARISON.json')['teacher_native'],
            scope=plan['scope']+' Both teacher policies newly executed; no historical output substitution.')
    except BaseException:state.update(status='FAILED',error=traceback.format_exc());raise
    finally:
        if budget.pending is not None:budget.finish()
        persist();budget.close();m.study.new(DIAGNOSTIC/'RESULT.json',state)
    print(json.dumps({k:v for k,v in state.items() if k!='episodes'}),flush=True)


def launch_teacher(then_diagnostic=False):
    print('CREDENTIAL_INPUT_READY',flush=True)
    key=os.environ.get('BUPT_API_KEY') or getpass.getpass('Campus credential (hidden): ')
    with (ROOT/'teacher_driver.log').open('xb') as log:
        pid=os.fork()
        if pid:print('TEACHER_WORKER_PID='+str(pid),flush=True);return
        os.setsid();os.dup2(log.fileno(),1);os.dup2(log.fileno(),2)
        null=os.open(os.devnull,os.O_RDONLY);os.dup2(null,0);os.close(null)
    state=dict(status='WAITING_LOCAL',pid=os.getpid(),start_ticks=Path('/proc/self/stat').read_text().split()[21])
    m.study.new(ROOT/'TEACHER_DRIVER_LIVE.json',state);started=time.monotonic()
    try:
        while not (ROOT/'RUN_RESULT.json').exists():
            if time.monotonic()-started>3900:raise TimeoutError('bounded wait for local transfer')
            time.sleep(2)
        assert m.read(ROOT/'RUN_RESULT.json')['status']=='RETURNED','local failure must be inspected before teacher calls'
        if not (ROOT/'POLICIES.json').exists():freeze_policies()
        state['status']='RUNNING';m.study.publish(ROOT/'TEACHER_DRIVER_LIVE.json',state)
        teacher(key);compare()
        if then_diagnostic:
            state['phase']='STATE_AWARE_DIAGNOSTIC';m.study.publish(ROOT/'TEACHER_DRIVER_LIVE.json',state)
            state_aware_diagnostic(key)
        state['status']='RETURNED'
    except BaseException:state.update(status='FAILED',error=traceback.format_exc());traceback.print_exc()
    finally:
        m.study.publish(ROOT/'TEACHER_DRIVER_LIVE.json',state);m.study.new(ROOT/'TEACHER_DRIVER_RESULT.json',state);os._exit(0)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('mode',choices=['prepare','local','teacher','compare','autopsy'])
    parser.add_argument('--cohort',choices=['original','forward'],default='original')
    parser.add_argument('--then-diagnostic',action='store_true');args=parser.parse_args()
    if args.cohort=='forward':ROOT=BASE/'flat_dsl_forward_v1'
    if args.mode=='teacher':launch_teacher(args.then_diagnostic)
    else:{'prepare':prepare_forward if args.cohort=='forward' else prepare,'local':local_run,'compare':compare,'autopsy':autopsy}[args.mode]()
