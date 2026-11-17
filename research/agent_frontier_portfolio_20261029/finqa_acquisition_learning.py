"""Learn correction acquisition value from shared teacher outcomes and executed states."""
from pathlib import Path
import argparse,collections,json,os,random,shutil,subprocess,time,traceback
import finqa_patch_learning as c
import finqa_correction_router as router
from finqa_minimal_patches import apply_patches

m=c.m
ROOT=c.root.parent/'acquisition_value_v1'
TEACHER=router.RELATIVE_ROOT/'full_teacher_train'
VARIANT='value'


def percent_scale_only(first,second):
    """A small rule baseline: unchanged core, only a terminal factor100 differs."""
    def core(program):
        try:steps=m.task.executor().parse_program(program)
        except Exception:return None,0
        power=0;hundred={'100','100.0','const_100'}
        while len(steps)>=2:
            step=steps[-1];ref='#'+str(len(steps)-2)
            if step.op=='multiply' and ((step.arg1==ref and step.arg2 in hundred) or (step.arg2==ref and step.arg1 in hundred)):power+=1
            elif step.op=='divide' and step.arg1==ref and step.arg2 in hundred:power-=1
            else:break
            steps=steps[:-1]
        return [(step.op,step.arg1,step.arg2) for step in steps],power
    a,ap=core(first);b,bp=core(second)
    return a is not None and a==b and abs(ap-bp)==1


def guarded_program(local,teacher,public,completed=True):
    execution=m.task.execute_public(teacher,public)
    keep=not completed or execution['status']!='executed' or percent_scale_only(local,teacher)
    return (local if keep else teacher),keep


def request(public,initial,current):
    """Only public states: no future teacher proposal or correctness labels."""
    system=('You estimate the outcome of acquiring another financial program correction. '
        'The local agent has already submitted its current program. A fixed teacher, if requested, '
        'starts from the original program snapshot independently of the current local program. '
        'Afterwards a controller keeps the local program if the teacher fails or if both calculations '
        'have the same core with only a trailing factor100 conversion difference; otherwise it uses the teacher program. '
        'Predict the resulting correctness change relative to keeping the local program. '
        'B means the teacher/controller repairs a wrong local answer; A means it damages a correct local answer; '
        'N means unchanged correctness, including both wrong. Execution values are observed computations, not correctness labels. '
        'Return exactly one JSON object with the single key outcome and one letter A, B or N.')
    if VARIANT=='risk':
        system=('You estimate whether the local financial agent has submitted an incorrect program. '
            'Compare the current program with the question and public report. '
            'B means the current program gives an incorrect answer; N means it gives a correct answer. '
            'Execution values are observed computations, not correctness labels. '
            'Return exactly one JSON object with the single key outcome and one letter B or N.')
    return dict(messages=[dict(role='system',content=system),dict(role='user',content=json.dumps(
        dict(public_task=public,initial_state=initial,local_state=current),ensure_ascii=False))])


def prepare():
    if VARIANT=='risk':prepare_risk();return
    study=m.read(TEACHER/'RESULT.json');assert study['status']=='RETURNED' and len(study['episodes'])==96
    labels=m.read(c.step1/'TRAIN_LABELS_PRIVATE.json')
    sources={row['index']:row for row in m.read(router.RELATIVE_ROOT/'CHEAP_PLAN.json')['episodes']}
    cheap={row['index']:row for row in m.read(router.RELATIVE_ROOT/'CHEAP_RESULT.json')['episodes']}
    proposals={row['index']:row for row in m.read(ROOT.parent/'proposal_acceptance_v1/PROPOSAL_TRAIN_RESULT.json')['episodes']}
    repairs={row['source_index']:row for row in m.read_lines(c.step1/'formation_v2/COMBINED_PATCH_SAMPLES.jsonl') if row['phase']=='repair'}
    subsets={row['index']:row for row in m.read_lines(c.step1/'formation_v2/bundle_credit_autopsy/ROWS.jsonl')}
    replay=m.read(c.replay/'DATA.json');prior=m.read(c.replay/'PLAN.json');tokenizer=m.tokens.load_tokenizer(m.learning.MODEL)
    anchor_groups=[[replay['rows'][i] for i in group] for group in prior['paired_rows']]
    groups=[];views=[];base_rows=[];contrasts=0
    for teacher in study['episodes']:
        index=teacher['index'];source=Path(sources[index]['source_folder'])
        public=m.read(source/'inputs/public.json');initial=m.state_from_folder(source)
        assert public['id']==teacher['id']==cheap[index]['id']==labels[index]['id']
        actual=m.read(Path(teacher['folder'])/'RESULT.json');completed=actual['agent_completed']
        candidates=[('cheap_actual',cheap[index]['program']),('original_actual',initial['current_program']),
            ('proposal_actual',proposals[index]['program'])]
        if index in repairs:
            item=repairs[index];candidates.append(('correct_execution_witness',apply_patches(item['state']['current_program'],item['target']['patches'])))
        if index in subsets:
            wrong=[row for row in subsets[index]['outcomes'] if row['valid'] and not row['success']]
            wrong.sort(key=lambda row:(row['selected_mutable'],row['program']))
            if wrong:
                for position in sorted(set([len(wrong)//2,len(wrong)-1])):
                    candidates.append(('executed_partial',wrong[position]['program']))
        retained={};encoded=[];outcomes=set()
        for kind,program in candidates:
            if program in retained:continue
            retained[program]=kind;current=dict(current_program=program,execution_feedback=m.task.execute_public(program,public))
            selected,kept=guarded_program(program,teacher['program'],public,completed)
            before=m.task.grade(program,public,labels[index]['exe_ans'])['execution_correct']
            after=m.task.grade(selected,public,labels[index]['exe_ans'])['execution_correct'];utility=int(after)-int(before)
            target='B' if utility>0 else ('A' if utility<0 else 'N');outcomes.add(target)
            row=m.tokens.encode_completion(request(public,initial,current),dict(role='assistant',content=json.dumps(dict(outcome=target))),
                tokenizer,16384,completion_kind='text')
            row.update(source_index=index,view_kind=kind);encoded.append(row)
            views.append(dict(index=index,id=teacher['id'],kind=kind,program=program,utility=utility,target=target,guard_keep=kept))
            if kind=='cheap_actual':base_rows.append(dict(index=index,before=before,after=after,utility=utility,guard_keep=kept))
        contrasts+=int(len(outcomes)>1);groups.append(encoded)
    schedule=[dict(kind='replay',index=i) for i in range(len(anchor_groups))]+[dict(kind='value',index=i) for i in range(len(groups))]
    random.Random(17).shuffle(schedule);schedule*=2
    ROOT.mkdir()
    m.study.new(ROOT/'DATA.json',dict(anchor_groups=anchor_groups,patch_groups=groups))
    m.study.new(ROOT/'TRAIN_VIEWS.json',dict(views=views,cheap_actual=base_rows))
    m.study.new(ROOT/'PLAN.json',dict(model=str(m.learning.MODEL),warm_start=str(ROOT.parent/'paired_state_negatives_v1/paired_state_branch'),
        adapter_folder='value_policy',seed=17,learning_rate=2e-4,epochs=2,schedule=schedule,wall_seconds=7200,
        replay_groups=len(anchor_groups),value_source_groups=len(groups),value_views=len(views),
        target_counts=dict(collections.Counter(row['target'] for row in views)),source_groups_with_changed_value=contrasts,
        strong_budget=18,fixed_threshold=0,teacher='Full native DeepSeek from original snapshot; no reuse as if it saw intervened local states.',
        scope='One actual teacher rollout per original TRAIN state supports multiple already-executed local states. Group weighting; DEV/reserved64 excluded.'))
    print(json.dumps(dict(sources=len(groups),views=len(views),changed_value_groups=contrasts,updates=len(schedule),
        targets=dict(collections.Counter(row['target'] for row in views)))),flush=True)


def prepare_risk():
    """Same sources, executed views, replay and schedule; only learn local error risk."""
    reference=ROOT.parent/'acquisition_value_v1';plan=m.read(reference/'PLAN.json')
    views=m.read(reference/'TRAIN_VIEWS.json')['views'];data=m.read(reference/'DATA.json')
    labels=m.read(c.step1/'TRAIN_LABELS_PRIVATE.json')
    sources={r['index']:r for r in m.read(router.RELATIVE_ROOT/'CHEAP_PLAN.json')['episodes']}
    tokenizer=m.tokens.load_tokenizer(m.learning.MODEL);grouped=collections.defaultdict(list);targets=collections.Counter()
    for view in views:
        index=view['index'];source=Path(sources[index]['source_folder']);public=m.read(source/'inputs/public.json')
        initial=m.state_from_folder(source);program=view['program']
        current=dict(current_program=program,execution_feedback=m.task.execute_public(program,public))
        correct=m.task.grade(program,public,labels[index]['exe_ans'])['execution_correct']
        target='N' if correct else 'B';targets[target]+=1
        row=m.tokens.encode_completion(request(public,initial,current),dict(role='assistant',content=json.dumps(dict(outcome=target))),
            tokenizer,16384,completion_kind='text')
        row.update(source_index=index,view_kind=view['kind']);grouped[index].append(row)
    assert len(grouped)==96 and len(views)==252
    groups=[grouped[i] for i in range(96)]
    assert [len(g) for g in groups]==[len(g) for g in data['patch_groups']]
    plan.pop('source_groups_with_changed_value',None)
    plan.update(target_counts=dict(targets),objective='Local execution error risk, not teacher acquisition value',
        scope='Matched old37 warm start,96 TRAIN sources/252 identical executed views,121 replay groups,434 updates. No new sources or DEV targets.')
    ROOT.mkdir();m.study.new(ROOT/'DATA.json',dict(anchor_groups=data['anchor_groups'],patch_groups=groups))
    m.study.new(ROOT/'PLAN.json',plan)
    print(json.dumps(dict(variant=VARIANT,sources=len(groups),views=len(views),targets=dict(targets),updates=len(plan['schedule']))),flush=True)


def predict():
    import torch
    from peft import PeftModel
    from transformers import AutoModelForCausalLM
    from scripts.graph.research_gpu_guard import gpu_lease
    plan=m.read(ROOT/'PLAN.json');features=m.read(router.ROOT/'FEATURE_PLAN.json')
    cached=m.read(ROOT.parent/'paired_state_negatives_v1/native_v1/PLAN.json')
    cheap={ep['index']:ep for ep in cached['episodes'] if ep['arm']=='paired_state_branch'}
    tokenizer=m.tokens.load_tokenizer(m.learning.MODEL);started=time.monotonic();rows=[];total_tokens=0;forward_seconds=0
    with gpu_lease():
        base=AutoModelForCausalLM.from_pretrained(plan['model'],dtype=torch.bfloat16,device_map={'':0},
            attn_implementation='sdpa',local_files_only=True,trust_remote_code=False)
        model=PeftModel.from_pretrained(base,str(ROOT/'value_policy'));model.eval()
        for source in features['dev']:
            public=m.read(Path(source['folder'])/'inputs/public.json');initial=m.state_from_folder(Path(source['folder']))
            current=m.state_from_folder(Path(cheap[source['index']]['folder']))
            encoded=[m.tokens.encode_completion(request(public,initial,current),dict(role='assistant',content=json.dumps(dict(outcome=label))),
                tokenizer,16384,completion_kind='text') for label in ['A','B','N']]
            ids=[row['input_ids'] for row in encoded]
            at=next(i for i,tokens in enumerate(zip(*ids)) if len(set(tokens))>1)
            assert all(seq[at+1:]==ids[0][at+1:] for seq in ids), 'class readout must differ in one token only'
            prefix=ids[0][:at];classes=[seq[at] for seq in ids];total_tokens+=len(prefix)
            free=next(int(x.split()[1])/1024**2 for x in Path('/proc/meminfo').read_text().splitlines() if x.startswith('MemAvailable:'))
            if free<32:raise RuntimeError('32GiB memory reserve')
            batch=torch.tensor([prefix],device='cuda');clock=time.monotonic()
            with torch.inference_mode():
                logits=model(input_ids=batch,use_cache=False,logits_to_keep=1).logits[0,-1,classes].float()
                probability=logits.softmax(-1).cpu().tolist()
                if VARIANT=='risk':
                    binary=logits[1:].softmax(-1).cpu().tolist();probability=[0.,*binary]
            forward_seconds+=time.monotonic()-clock
            rows.append(dict(index=source['index'],id=source['id'],probabilities=dict(zip(['A','B','N'],probability)),
                score=probability[1]-probability[0],input_tokens=len(prefix)))
            del batch,logits
    ranked=sorted(rows,key=lambda row:(-row['score'],row['index']))
    chosen={row['index'] for row in ranked[:plan['strong_budget']] if row['score']>plan['fixed_threshold']}
    for row in rows:row['decision']='TEACHER' if row['index'] in chosen else 'CHEAP'
    m.study.new(ROOT/'PREDICTIONS.json',dict(decisions=rows,strong_budget=plan['strong_budget'],
        variant=VARIANT,
        forward_calls=len(rows),input_tokens_processed=total_tokens,generated_tokens=0,http_posts=0,
        forward_seconds=forward_seconds,seconds=time.monotonic()-started,
        scope='Actual neural classifier forwards, not free compute or language generation. Predictions frozen before any DEV teacher result/label is read.'))
    print(json.dumps(dict(forwards=len(rows),selected=len(chosen),input_tokens=total_tokens)),flush=True)


def train_and_predict():
    if not (ROOT/'PLAN.json').exists():prepare()
    state=dict(status='RUNNING',phase='TRAIN',pid=os.getpid(),start_ticks=Path('/proc/self/stat').read_text().split()[21])
    m.study.new(ROOT/'PIPELINE_LIVE.json',state);unloaded=c.stop27();child=None
    try:
        for mode in ['train','predict']:
            state['phase']=mode
            with (ROOT/(mode+'.log')).open('xb') as log:
                child=subprocess.Popen([str(c.repo/'venv/bin/python'),'-u','-B',__file__,mode,'--variant',VARIANT],cwd=c.repo,stdout=log,stderr=subprocess.STDOUT)
                state['child_pid']=child.pid;m.study.publish(ROOT/'PIPELINE_LIVE.json',state)
                code=child.wait(timeout=7800 if mode=='train' else 1800)
            if code:raise RuntimeError(mode+' failed; inspect its unchanged log and receipt')
        state.update(status='RETURNED',phase='READY_FOR_NATIVE_TEACHER')
    except BaseException:state.update(status='FAILED',error=traceback.format_exc())
    finally:
        if child is not None and child.poll() is None:
            child.terminate()
            try:child.wait(timeout=30)
            except subprocess.TimeoutExpired:child.kill();child.wait()
        if unloaded:state['restoration']=c.restore27()
        m.study.publish(ROOT/'PIPELINE_LIVE.json',state);m.study.new(ROOT/'PIPELINE_RESULT.json',state)
        print(json.dumps(state),flush=True)


def evaluate(key=None):
    """Only selected acquisitions are new; all final programs execute natively."""
    from scripts.graph.research_school_gateway import BatchBudget,SchoolBackend,BASE_URL,MODEL,REQUEST_TOKEN_CEILING
    predictions=m.read(ROOT/'PREDICTIONS.json');decisions=predictions['decisions']
    features=m.read(router.ROOT/'FEATURE_PLAN.json');sources=features['dev']
    cached=m.read(ROOT.parent/'paired_state_negatives_v1/native_v1/PLAN.json')
    cheap={ep['index']:ep for ep in cached['episodes'] if ep['arm']=='paired_state_branch'}
    reference=m.read(TEACHER/'PLAN.json');template=Path(m.read(router.RELATIVE_ROOT/'CHEAP_PLAN.json')['reference_template'])
    profile=dict(provider='bupt_chat_v1',base_url=BASE_URL,model_id=MODEL,context=262144,output=8192)
    assert reference['model']==profile and len(decisions)==len(sources)==64
    if any(row['decision']=='TEACHER' for row in decisions) and not key:raise ValueError('campus credential required')
    budget=BatchBudget(ROOT/'eval_budget',posts=216,tokens=1_200_000)
    backend=SchoolBackend(key,budget,m.study.core) if key else None
    if backend:backend.verify(profile)
    state=dict(status='RUNNING',pid=os.getpid(),start_ticks=Path('/proc/self/stat').read_text().split()[21],episodes=[])
    started=time.monotonic()
    def persist():
        state.update(posts=sum(row['state']!='not_sent' for row in budget.rows),
            known_tokens=sum(row.get('usage',{}).get('total_tokens',0) for row in budget.rows),
            unknown=sum(row['state']=='unknown' for row in budget.rows),seconds=time.monotonic()-started)
        state['unknown_reserved_tokens']=state['unknown']*REQUEST_TOKEN_CEILING
        m.study.publish(ROOT/'DEV_LIVE.json',state)
    persist()
    try:
        with m.study.core.resource_lock():
            h=m.study.core.helpers();checked=h.deps.verify_projection(h.actor.RUNTIME_ROOT,h.actor.RUNTIME_SHA)
            m.study.CAPS.clear();m.study.CAPS.update(reference['caps'])
            for source,decision in zip(sources,decisions,strict=True):
                index=source['index'];assert source['id']==decision['id']==cheap[index]['id']
                original=Path(source['folder']);public=m.read(original/'inputs/public.json');initial=m.state_from_folder(original)
                cheap_folder=Path(cheap[index]['folder']);local=m.read(cheap_folder/'RESULT.json');current=m.state_from_folder(cheap_folder)
                assert (cheap_folder/'inputs/task.txt').read_text()==m.review_prompt(public,initial,terminal_program=True)
                guard_keep=False;teacher_program=None;teacher_success=None
                if decision['decision']=='TEACHER':
                    folder=ROOT/'teacher_dev'/f'{index:03d}';target=folder/'inputs';target.mkdir(parents=True)
                    for name in ['work','dependencies']:shutil.copytree(original/name,folder/name)
                    for name in ['finqa_tool.py','executor.py','guest.py']:shutil.copyfile(template/name,target/name)
                    (target/'public.json').write_text(json.dumps(public,ensure_ascii=False))
                    (target/'task.txt').write_text(m.review_prompt(public,initial,terminal_program=True))
                    ep=dict(index=index,id=source['id'],report=public['report'],folder=str(folder))
                    raw=m.study.episode(ep,h,checked,profile,private_labels=original.parent.parent/'LABELS_PRIVATE.json',relay_factory=backend.make_relay)
                    teacher_program=raw['submitted_program'];teacher_success=raw['native_success']
                    program,guard_keep=guarded_program(current['current_program'],teacher_program,public,raw['agent_completed'])
                    if not raw['accounting']['integrity_passed']:
                        persist();raise RuntimeError('native transport failure retained; no automatic retry')
                else:program=current['current_program']
                final=ROOT/'final'/f'{index:03d}';final.mkdir(parents=True)
                m.task.submit_program(program,public,final,origin='learned_acquisition_with_scale_guard')
                label=m.read(original.parent.parent/'LABELS_PRIVATE.json')[index]
                success=m.task.grade(program,public,label['exe_ans'])['execution_correct']
                before=m.read(original/'RESULT.json')['native_success']
                state['episodes'].append(dict(index=index,id=source['id'],decision=decision['decision'],score=decision['score'],
                    before=before,cheap=local['native_success'],success=success,
                    utility=int(success)-int(local['native_success']),program=program,guard_keep=guard_keep,
                    cheap_executed=current['execution_feedback']['status']=='executed',
                    teacher_program=teacher_program,teacher_success=teacher_success))
                persist();print(json.dumps(dict(index=index,decision=decision['decision'],success=success)),flush=True)
        rows=state['episodes'];state.update(status='RETURNED',summary=dict(tasks=len(rows),success=sum(row['success'] for row in rows),
            cheap_reference=sum(row['cheap'] for row in rows),relative_recovered=sum(row['utility']>0 for row in rows),
            relative_damaged=sum(row['utility']<0 for row in rows),before=sum(row['before'] for row in rows),
            semantic_recovered=sum(row['utility']>0 and row['cheap_executed'] for row in rows),
            recovered=sum(row['success'] and not row['before'] for row in rows),
            damaged=sum(row['before'] and not row['success'] for row in rows),
            acquisitions=sum(row['decision']=='TEACHER' for row in rows),guard_kept=sum(row['guard_keep'] for row in rows),
            classifier_forward_calls=predictions['forward_calls'],classifier_input_tokens=predictions['input_tokens_processed'],
            scope='Actual selected full native DeepSeek episodes plus native final execution. All64 cheap outputs cached; their deployment and formation costs remain separate.'))
    except BaseException:state.update(status='FAILED',error=traceback.format_exc())
    finally:
        if budget.pending is not None:budget.finish()
        persist();budget.close();m.study.new(ROOT/'DEV_RESULT.json',state)
        print(json.dumps({k:v for k,v in state.items() if k!='episodes'}),flush=True)


def launch_evaluation():
    import getpass
    predictions=m.read(ROOT/'PREDICTIONS.json')
    if (ROOT/'DEV_LIVE.json').exists():raise RuntimeError('inspect the existing native attempt')
    if not any(row['decision']=='TEACHER' for row in predictions['decisions']):evaluate();return
    print('CREDENTIAL_INPUT_READY',flush=True)
    key=os.environ.get('BUPT_API_KEY') or getpass.getpass('Campus credential (hidden): ')
    output=(ROOT/'evaluation.log').open('xb');pid=os.fork()
    if pid:output.close();print('CAMPUS_WORKER_PID='+str(pid),flush=True);return
    os.setsid();os.dup2(output.fileno(),1);os.dup2(output.fileno(),2)
    null=os.open(os.devnull,os.O_RDONLY);os.dup2(null,0);os.close(null)
    try:evaluate(key)
    except BaseException:traceback.print_exc()
    finally:os._exit(0)


def cached_controls():
    """Compare frozen selections on common native teacher responses; no new calls."""
    if (ROOT/'CONTROL_PREDICTIONS.json').exists():raise RuntimeError('control decisions already exist; inspect their saved comparison')
    import numpy as np
    import torch
    assert VARIANT=='value'
    torch.set_num_threads(4);started=time.monotonic()
    feature=m.read(router.ROOT/'FEATURE_PLAN.json');x=np.load(router.ROOT/'FEATURES.npz')
    train=m.read(router.RELATIVE_ROOT/'CHEAP_RESULT.json')['episodes']
    assert len(train)==96 and all(row['index']==i for i,row in enumerate(train))
    saved,model=router.fit_once(x['train'],np.asarray([int(not row['success']) for row in train]),21)
    risk=router.probability(saved,model,x['dev'])[:,1]
    budget=m.read(ROOT/'PLAN.json')['strong_budget']
    ranked=sorted(range(64),key=lambda i:(-float(risk[i]),i));selected=set(ranked[:budget])
    prior=m.read(router.ROOT/'routing_controls/PREDICTIONS.json')
    controls=dict(error_risk37=[dict(index=i,selected=i in selected,score=float(risk[i])) for i in range(64)],
        random_fixed=prior['predictions']['random_fixed'])
    assert prior['budget']==budget==18 and all(sum(row['selected'] for row in rows)==budget for rows in controls.values())
    m.study.new(ROOT/'CONTROL_PREDICTIONS.json',dict(controls=controls,head_updates=200,encoder_forwards=0,
        seconds=time.monotonic()-started,scope='Post-primary controls; TRAIN cheap37 error labels only. Prior random seed reused unchanged; no DEV outcome tuning. BGE inputs are original public states, not matched-capacity/full-current-state controls.'))
    # Teacher responses and DEV labels are read only after the control decisions.
    predictions=m.read(ROOT/'PREDICTIONS.json');actual=m.read(ROOT/'DEV_RESULT.json')
    legacy=m.read(ROOT.parent/'deepseek_development_reference_v1/RESULT.json')['episodes']
    assert len(legacy)==len(actual['episodes'])==64 and actual['status']=='RETURNED'
    cached=m.read(ROOT.parent/'paired_state_negatives_v1/native_v1/PLAN.json')
    cheap={row['index']:row for row in cached['episodes'] if row['arm']=='paired_state_branch'}
    labels=m.read(Path(feature['dev'][0]['folder']).parent.parent/'LABELS_PRIVATE.json')
    policy=dict(keep_all=set(),all_teacher=set(range(64)),
        learned_value={r['index'] for r in predictions['decisions'] if r['decision']=='TEACHER'})
    policy.update({name:{r['index'] for r in rows if r['selected']} for name,rows in controls.items()})
    pools={};rng=np.random.default_rng(prior['random_seed'])
    allocations=[rng.choice(64,budget,replace=False) for _ in range(2000)]
    for name in ['legacy_common','fresh_selected_common']:
        outcomes=[]
        for i,(source,teacher) in enumerate(zip(feature['dev'],legacy,strict=True)):
            if name=='fresh_selected_common' and actual['episodes'][i]['decision']=='TEACHER':
                teacher=m.read(ROOT/'teacher_dev'/f'{i:03d}'/'RESULT.json')
            public=m.read(Path(source['folder'])/'inputs/public.json');local=m.state_from_folder(Path(cheap[i]['folder']))
            assert source['id']==teacher['id']==cheap[i]['id']
            program,kept=guarded_program(local['current_program'],teacher['submitted_program'],public,teacher['agent_completed'])
            before=actual['episodes'][i]['cheap'];after=m.task.grade(program,public,labels[i]['exe_ans'])['execution_correct']
            outcomes.append(dict(index=i,before=before,after=after,utility=int(after)-int(before),guard_keep=kept,
                posts=teacher['accounting']['actual_forwarded_posts'],tokens=teacher['accounting']['provider_total_tokens_known']))
        table={};base=sum(row['before'] for row in outcomes)
        for pname,selection in policy.items():
            chosen=[r for r in outcomes if r['index'] in selection]
            table[pname]=dict(success=base+sum(r['utility'] for r in chosen),recovered=sum(r['utility']>0 for r in chosen),
                damaged=sum(r['utility']<0 for r in chosen),teacher_episodes=len(chosen),
                teacher_posts=sum(r['posts'] for r in chosen),teacher_tokens=sum(r['tokens'] for r in chosen))
        random_scores=[base+sum(outcomes[int(i)]['utility'] for i in chosen) for chosen in allocations]
        pools[name]=dict(policies=table,random_allocation=dict(draws=2000,mean=float(np.mean(random_scores)),
            p05=float(np.quantile(random_scores,.05)),p95=float(np.quantile(random_scores,.95))),outcomes=outcomes)
    assert pools['fresh_selected_common']['policies']['learned_value']['success']==actual['summary']['success']
    result=dict(status='RETURNED',pools=pools,new_http_posts=0,head_updates=200,encoder_forwards=0,
        scope='CPU replay of actual native teacher candidates, not fresh policy runs. Each pool shares identical per-source teacher responses across policies; fresh-selected pool mixes timepoints, so legacy common pool is also reported. Same18 episode cap, actual teacher POST/tokens vary. Cheap37 and classifier costs are additional.')
    m.study.new(ROOT/'CONTROL_COMPARISON.json',result)
    print(json.dumps({name:{k:v for k,v in pool.items() if k!='outcomes'} for name,pool in pools.items()}),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('mode',choices=['prepare','train','predict','run','evaluate','controls'])
    parser.add_argument('--variant',choices=['value','risk'],default='value');args=parser.parse_args()
    VARIANT=args.variant
    if VARIANT=='risk':ROOT=ROOT.parent/'acquisition_risk_control_v1'
    if args.mode=='prepare':prepare()
    elif args.mode=='train':c.root=ROOT;c.train()
    elif args.mode=='predict':predict()
    elif args.mode=='evaluate':launch_evaluation()
    elif args.mode=='controls':cached_controls()
    else:train_and_predict()
