"""A small pre-call recovery/damage predictor, learned from TRAIN executions."""
from pathlib import Path
import argparse,collections,json,os,re,shutil,time,traceback
import numpy as np
import finqa_patch_learning as c

m=c.m
ROOT=c.root.parent/'correction_router_v1'
SOURCE=c.root.parent/'correction_value_27b_v1'
RELATIVE_ROOT=ROOT.parent/'expert_relative_value_v1'


def public_features(public,state):
    """No expected answer, success flag, teacher rationale, or proposed repair."""
    m.task.check_public(public)
    question=public['question'];program=state['current_program'] or ''
    execution=state.get('execution_feedback') or {}
    basic=json.dumps(dict(question=question,program=program,
        execution=execution),ensure_ascii=False)
    words=set(re.findall(r'[a-z]+|\d{4}',question.lower()))
    lines=[' | '.join(map(str,row)) for row in public['table']]
    lines+=public.get('pre_text',[])+public.get('post_text',[])
    ranked=sorted(enumerate(lines),key=lambda pair:
        (-len(words & set(re.findall(r'[a-z]+|\d{4}',str(pair[1]).lower()))),pair[0]))
    evidence=question+'\n'+ '\n'.join(str(text) for _,text in ranked[:8])
    evidence+='\n'+json.dumps(c.literal_matches(public,state)[:8],ensure_ascii=False)
    numeric=[float(execution.get('status')=='executed'),min(len(execution.get('steps',[])),20)/20]
    for term in ['percent','ratio','average','change','increase','decrease','million','billion','thousand','tax','total','difference']:
        numeric.append(float(term in question.lower()))
    for op in ['add','subtract','multiply','divide','exp','greater','table_']:
        numeric.append(min(program.count(op+'('),8)/8)
    numeric.append(min(len(re.findall(r'\b(?:19|20)\d{2}\b',question)),5)/5)
    return basic,evidence,np.array(numeric,dtype=np.float32)


def encode(encoder,episodes):
    texts=[];numeric=[]
    for ep in episodes:
        folder=Path(ep.get('source_folder',ep['folder']))
        public=m.read(folder/'inputs/public.json');state=m.state_from_folder(folder)
        basic,evidence,values=public_features(public,state)
        texts.extend([basic,evidence]);numeric.append(values)
    vectors=encoder.encode(texts,batch_size=16,show_progress_bar=False,normalize_embeddings=True)
    a,b=np.asarray(vectors[::2]),np.asarray(vectors[1::2])
    return np.concatenate([a,b,a*b,np.abs(a-b),np.asarray(numeric)],axis=1)


def prepare():
    import torch
    from sentence_transformers import SentenceTransformer
    torch.set_num_threads(4);ROOT.mkdir()
    plan=m.read(SOURCE/'PLAN.json')
    dev=m.read(c.replay/'native_v1/PLAN.json')['source_episodes'];assert len(dev)==64
    cache=Path('/home/testuser/.cache/huggingface/hub/models--BAAI--bge-small-en-v1.5')
    revision=(cache/'refs/main').read_text().strip();weights=cache/'snapshots'/revision
    encoder=SentenceTransformer(str(weights),device='cpu',local_files_only=True)
    encoder.max_seq_length=384;calls=[0]
    original=encoder[0].auto_model.forward
    def counted_forward(*args,**kwargs):
        calls[0]+=1;return original(*args,**kwargs)
    encoder[0].auto_model.forward=counted_forward
    parts={};stats={}
    for name,episodes in [('train',plan['episodes']),('dev',dev)]:
        started=time.monotonic();previous=calls[0];parts[name]=encode(encoder,episodes)
        stats[name]=dict(seconds=time.monotonic()-started,encoder_forward_calls=calls[0]-previous,
            episodes=len(episodes),http_posts=0,device='cpu')
    encoder[0].auto_model.forward=original;np.savez(ROOT/'FEATURES.npz',**parts)
    m.study.new(ROOT/'FEATURE_PLAN.json',dict(train=plan['episodes'],dev=dev,
        encoder=str(weights),max_sequence_tokens=384,stats=stats,
        scope='Only public before-state inputs; all DEV routing decisions are frozen before scoring.'))
    print(json.dumps(stats),flush=True)


def fit_once(x,y,seed):
    import torch
    torch.manual_seed(seed)
    mean=x.mean(0);scale=np.maximum(x.std(0),.01)
    inputs=torch.tensor((x-mean)/scale,dtype=torch.float32);labels=torch.tensor(y)
    model=torch.nn.Sequential(torch.nn.Linear(x.shape[1],32),torch.nn.ReLU(),
        torch.nn.Dropout(.1),torch.nn.Linear(32,3))
    optimizer=torch.optim.AdamW(model.parameters(),lr=.003,weight_decay=.01)
    for _ in range(200):
        optimizer.zero_grad();loss=torch.nn.functional.cross_entropy(model(inputs),labels)
        loss.backward();optimizer.step()
    model.eval()
    return dict(weights=model.state_dict(),mean=mean,scale=scale,input_size=x.shape[1]),model


def probability(saved,model,x):
    import torch
    with torch.inference_mode():
        value=torch.tensor((x-saved['mean'])/saved['scale'],dtype=torch.float32)
        return model(value).softmax(-1).numpy()


def frozen_probability(x):
    """Reload this project's own frozen checkpoint, without optimizer updates."""
    import torch
    saved=torch.load(ROOT/'POLICY.pt',map_location='cpu',weights_only=False)
    model=torch.nn.Sequential(torch.nn.Linear(saved['input_size'],32),torch.nn.ReLU(),
        torch.nn.Dropout(.1),torch.nn.Linear(32,3))
    model.load_state_dict(saved['weights'],strict=True);model.eval()
    return probability(saved,model,x)


def train():
    import torch
    from sklearn.model_selection import GroupKFold
    if (ROOT/'POLICY.pt').exists() or (ROOT/'PREDICTIONS.json').exists():
        raise RuntimeError('policy is already frozen; do not retrain in this output directory')
    torch.set_num_threads(4)
    result=m.read(SOURCE/'RESULT.json');assert result['status']=='RETURNED'
    rows=result['episodes'];assert len(rows)>=32 and any(row['utility']>0 for row in rows)
    plan=m.read(ROOT/'FEATURE_PLAN.json');features=np.load(ROOT/'FEATURES.npz')
    indexes=np.array([row['index'] for row in rows]);x=features['train'][indexes]
    utility=np.array([row['utility'] for row in rows]);y=np.where(utility==1,1,np.where(utility==-1,2,0))
    groups=['/'.join(plan['train'][i]['report'].split('/')[:2]) for i in indexes]
    oof=np.zeros((len(rows),3),dtype=np.float32);started=time.monotonic()
    for fold,(a,b) in enumerate(GroupKFold(4).split(x,y,groups)):
        saved,model=fit_once(x[a],y[a],17+fold);oof[b]=probability(saved,model,x[b])
    gains=oof[:,1]-oof[:,2]
    choices=[]
    for threshold in [0,.01,.02,.05,.1,.15,.2,.3,.5,1.01]:
        active=gains>threshold
        choices.append(dict(threshold=threshold,calls=int(active.sum()),
            utility=int(utility[active].sum()),objective=float(utility[active].sum()-.02*active.sum())))
    best=max(choices,key=lambda row:(row['objective'],-row['calls'],row['threshold']))
    saved,model=fit_once(x,y,21);torch.save(saved,ROOT/'POLICY.pt')
    predicted=probability(saved,model,features['dev']);gain=predicted[:,1]-predicted[:,2]
    decisions=[dict(index=ep['index'],id=ep['id'],score=float(score),
        decision='ESCALATE' if score>best['threshold'] else 'KEEP')
        for ep,score in zip(plan['dev'],gain,strict=True)]
    m.study.new(ROOT/'TRAIN_RESULT.json',dict(train_rows=len(rows),utility_counts=dict(collections.Counter(map(int,utility))),
        group_folds=4,optimizer_updates=1000,head_forward_calls=1000,
        threshold_search=choices,selected=best,seconds=time.monotonic()-started,
        scope='TRAIN-only group cross-fit threshold; no DEV labels, no actor updates.'))
    m.study.new(ROOT/'PREDICTIONS.json',dict(threshold=best['threshold'],decisions=decisions,
        classes=['neutral','recovered','damaged'],score='p(recovered)-p(damaged)',
        selection='TRAIN utility minus 0.02 per escalation; ties prefer fewer calls'))
    print(json.dumps(dict(training=best,dev_escalations=sum(row['decision']=='ESCALATE' for row in decisions))),flush=True)


def evaluate():
    """KEEP executes the saved program; selected cases use real OpenCode/27B."""
    from finqa_patch_proposals import proposal_relay
    if (ROOT/'DEV_LIVE.json').exists():raise RuntimeError('native DEV already started; inspect its receipt')
    decisions=m.read(ROOT/'PREDICTIONS.json')['decisions']
    features=m.read(ROOT/'FEATURE_PLAN.json');sources=features['dev']
    # Expected answers are opened only after the TRAIN-only decisions are saved.
    labels_path=Path(sources[0]['folder']).parent.parent/'LABELS_PRIVATE.json'
    labels=m.read(labels_path)
    prior=m.read(c.root/'PLAN.json');profile=dict(host='127.0.0.1',port=8006,
        model_id='qwen38-27b-fp8',context=32768,output=8192)
    state=dict(status='RUNNING',episodes=[]);m.study.publish(ROOT/'DEV_LIVE.json',state)
    started=time.monotonic()
    try:
        with m.study.core.resource_lock():
            h=m.study.core.helpers();checked=h.deps.verify_projection(h.actor.RUNTIME_ROOT,h.actor.RUNTIME_SHA)
            m.study.CAPS.clear();m.study.CAPS.update(prior['caps'])
            for source_ep,decision in zip(sources,decisions,strict=True):
                assert (source_ep['index'],source_ep['id'])==(decision['index'],decision['id'])
                source=Path(source_ep['folder']);folder=ROOT/'dev'/f"{source_ep['index']:03d}"
                public=m.read(source/'inputs/public.json');snapshot=m.state_from_folder(source)
                before=m.read(source/'RESULT.json')['native_success']
                folder.mkdir(parents=True)
                for name in ['work','dependencies']:shutil.copytree(source/name,folder/name)
                if decision['decision']=='KEEP':
                    program=snapshot['current_program']
                    m.task.submit_program(program,public,folder/'work',origin='learned_router_KEEP')
                    grade=m.task.grade(program,public,labels[source_ep['index']]['exe_ans'])
                    result=dict(native_success=grade['execution_correct'],submitted_program=program,
                        actor=dict(seconds=0),accounting=dict(actual_forwarded_posts=0,
                        provider_total_tokens_known=0,unknown_usage_requests=[]),
                        controller='KEEP: deterministic execution, no new OpenCode/model call')
                    m.study.new(folder/'RESULT.json',result)
                else:
                    inputs=folder/'inputs';inputs.mkdir()
                    for name,value in [('public.json',public),('initial_state.json',snapshot)]:
                        (inputs/name).write_text(json.dumps(value,ensure_ascii=False))
                    (inputs/'task.txt').write_text(c.prompt(public,snapshot))
                    for name,text in [('finqa_correction.py',Path(m.task.__file__).read_text()),
                            ('executor.py',Path(m.task.executor().__file__).read_text()),
                            ('finqa_minimal_patches.py',Path(__file__).with_name('finqa_minimal_patches.py').read_text()),
                            ('finqa_tool.py',c.TOOL),('guest.py',m.study.guest_source(terminal_program=True))]:
                        (inputs/name).write_text(text)
                    ep=dict(index=source_ep['index'],id=source_ep['id'],report=source_ep['report'],folder=str(folder))
                    result=m.study.episode(ep,h,checked,profile,private_labels=labels_path,relay_factory=proposal_relay)
                row=dict(index=source_ep['index'],id=source_ep['id'],decision=decision['decision'],
                    score=decision['score'],before_success=before,success=result['native_success'],
                    utility=int(result['native_success'])-int(before),program=result['submitted_program'],
                    posts=result['accounting']['actual_forwarded_posts'],tokens=result['accounting']['provider_total_tokens_known'],
                    unknown=len(result['accounting']['unknown_usage_requests']),seconds=result['actor']['seconds'])
                state['episodes'].append(row);m.study.publish(ROOT/'DEV_LIVE.json',state)
                print(json.dumps(row),flush=True)
        rows=state['episodes'];before=sum(row['before_success'] for row in rows)
        state.update(status='RETURNED',summary=dict(tasks=len(rows),before_success=before,
            success=sum(row['success'] for row in rows),kept=sum(row['before_success'] and row['success'] for row in rows),
            recovered=sum(row['utility']>0 for row in rows),damaged=sum(row['utility']<0 for row in rows),
            native_opencode_escalations=sum(row['decision']=='ESCALATE' for row in rows),
            posts=sum(row['posts'] for row in rows),tokens=sum(row['tokens'] for row in rows),
            unknown=sum(row['unknown'] for row in rows),actor_seconds=sum(row['seconds'] for row in rows),
            cpu_routing=features['stats']['dev'],cached_firstpass_posts=129,cached_firstpass_tokens=494754))
    except BaseException:state.update(status='FAILED',error=traceback.format_exc())
    finally:
        state['seconds']=time.monotonic()-started
        m.study.publish(ROOT/'DEV_LIVE.json',state);m.study.new(ROOT/'DEV_RESULT.json',state)
        print(json.dumps({k:v for k,v in state.items() if k!='episodes'}),flush=True)


def expert_reference():
    """Complete the fixed 27B reference, reusing the 18 actual routed calls."""
    from finqa_patch_proposals import proposal_relay
    routed=m.read(ROOT/'DEV_RESULT.json');assert routed['status']=='RETURNED'
    assert routed['summary']['success']>=36
    target=ROOT/'expert_reference';target.mkdir()
    sources=m.read(ROOT/'FEATURE_PLAN.json')['dev']
    labels_path=Path(sources[0]['folder']).parent.parent/'LABELS_PRIVATE.json'
    old={row['index']:row for row in routed['episodes']}
    prior=m.read(c.root/'PLAN.json');profile=dict(host='127.0.0.1',port=8006,
        model_id='qwen38-27b-fp8',context=32768,output=8192)
    state=dict(status='RUNNING',episodes=[],reused_calls=18,new_posts=0,new_tokens=0)
    m.study.publish(target/'LIVE.json',state);started=time.monotonic()
    try:
        with m.study.core.resource_lock():
            h=m.study.core.helpers();checked=h.deps.verify_projection(h.actor.RUNTIME_ROOT,h.actor.RUNTIME_SHA)
            m.study.CAPS.clear();m.study.CAPS.update(prior['caps'])
            for source_ep in sources:
                index=source_ep['index']
                if old[index]['decision']=='ESCALATE':
                    row=dict(old[index],reused=True,evidence_folder=str(ROOT/'dev'/f'{index:03d}'))
                else:
                    source=Path(source_ep['folder']);folder=target/'dev'/f'{index:03d}';inputs=folder/'inputs'
                    inputs.mkdir(parents=True)
                    for name in ['work','dependencies']:shutil.copytree(source/name,folder/name)
                    public=m.read(source/'inputs/public.json');snapshot=m.state_from_folder(source)
                    for name,value in [('public.json',public),('initial_state.json',snapshot)]:
                        (inputs/name).write_text(json.dumps(value,ensure_ascii=False))
                    (inputs/'task.txt').write_text(c.prompt(public,snapshot))
                    for name,text in [('finqa_correction.py',Path(m.task.__file__).read_text()),
                            ('executor.py',Path(m.task.executor().__file__).read_text()),
                            ('finqa_minimal_patches.py',Path(__file__).with_name('finqa_minimal_patches.py').read_text()),
                            ('finqa_tool.py',c.TOOL),('guest.py',m.study.guest_source(terminal_program=True))]:
                        (inputs/name).write_text(text)
                    ep=dict(index=index,id=source_ep['id'],report=source_ep['report'],folder=str(folder))
                    value=m.study.episode(ep,h,checked,profile,private_labels=labels_path,relay_factory=proposal_relay)
                    row=dict(index=index,id=source_ep['id'],before_success=old[index]['before_success'],
                        success=value['native_success'],utility=int(value['native_success'])-int(old[index]['before_success']),
                        program=value['submitted_program'],posts=value['accounting']['actual_forwarded_posts'],
                        tokens=value['accounting']['provider_total_tokens_known'],unknown=len(value['accounting']['unknown_usage_requests']),
                        seconds=value['actor']['seconds'],reused=False,evidence_folder=str(folder))
                    state['new_posts']+=row['posts'];state['new_tokens']+=row['tokens']
                state['episodes'].append(row);m.study.publish(target/'LIVE.json',state)
                print(json.dumps(row),flush=True)
        rows=state['episodes'];state.update(status='RETURNED',summary=dict(tasks=len(rows),
            success=sum(row['success'] for row in rows),recovered=sum(row['utility']>0 for row in rows),
            damaged=sum(row['utility']<0 for row in rows),policy_posts=sum(row['posts'] for row in rows),
            policy_tokens=sum(row['tokens'] for row in rows),actor_seconds=sum(row['seconds'] for row in rows),
            reused=sum(row['reused'] for row in rows),new_posts=state['new_posts'],new_tokens=state['new_tokens']))
    except BaseException:state.update(status='FAILED',error=traceback.format_exc())
    finally:
        state['seconds']=time.monotonic()-started
        m.study.publish(target/'LIVE.json',state);m.study.new(target/'RESULT.json',state)
        print(json.dumps({k:v for k,v in state.items() if k!='episodes'}),flush=True)


def routing_controls():
    """Freeze budget-matched controls from TRAIN, before reference completion."""
    import torch
    from sentence_transformers import SentenceTransformer
    target=ROOT/'routing_controls';target.mkdir();torch.set_num_threads(4);started=time.monotonic()
    plan=m.read(ROOT/'FEATURE_PLAN.json');training=m.read(SOURCE/'RESULT.json')['episodes']
    indexes=np.array([row['index'] for row in training]);utility=np.array([row['utility'] for row in training])
    y=np.where(utility==1,1,np.where(utility==-1,2,0))
    difficulty=np.array([int(not row['before_success']) for row in training])
    features=np.load(ROOT/'FEATURES.npz');budget=sum(row['decision']=='ESCALATE'
        for row in m.read(ROOT/'PREDICTIONS.json')['decisions'])
    encoder=SentenceTransformer(plan['encoder'],device='cpu',local_files_only=True);encoder.max_seq_length=384
    texts=[m.read(Path(ep.get('source_folder',ep['folder']))/'inputs/public.json')['question']
        for ep in plan['train']+plan['dev']]
    vectors=np.asarray(encoder.encode(texts,batch_size=16,show_progress_bar=False,normalize_embeddings=True))
    question_train=vectors[:len(plan['train'])][indexes];question_dev=vectors[len(plan['train']):]
    predictions={}
    for name,x,labels,test in [('question_only',question_train,y,question_dev),
            ('error_risk',features['train'][indexes],difficulty,features['dev'])]:
        saved,model=fit_once(x,labels,21);prob=probability(saved,model,test)
        scores=prob[:,1]-prob[:,2] if name=='question_only' else prob[:,1]
        chosen=set(sorted(range(64),key=lambda i:(-float(scores[i]),i))[:budget])
        predictions[name]=[dict(index=ep['index'],score=float(score),selected=i in chosen)
            for i,(ep,score) in enumerate(zip(plan['dev'],scores,strict=True))]
    rng=np.random.default_rng(20261117);chosen=set(map(int,rng.choice(64,budget,replace=False)))
    predictions['random_fixed']=[dict(index=ep['index'],selected=i in chosen) for i,ep in enumerate(plan['dev'])]
    predictions['execution_error_only']=[dict(index=ep['index'],selected=
        (m.state_from_folder(ep['folder']).get('execution_feedback') or {}).get('status')!='executed') for ep in plan['dev']]
    m.study.new(target/'PREDICTIONS.json',dict(budget=budget,predictions=predictions,
        model_seed=21,random_seed=20261117,optimizer_updates=400,head_training_forwards=400,
        seconds=time.monotonic()-started,scope='Same TRAIN/public features and model architecture; top18 matches the frozen primary call count. No DEV labels used.'))
    print('Routing control decisions frozen',flush=True)


def compare_routing():
    expert=m.read(ROOT/'expert_reference/RESULT.json');assert expert['status']=='RETURNED'
    rows=sorted(expert['episodes'],key=lambda row:row['index']);assert len(rows)==64
    controls=m.read(ROOT/'routing_controls/PREDICTIONS.json')
    routed=m.read(ROOT/'PREDICTIONS.json')['decisions'];before=sum(row['before_success'] for row in rows)
    policies={'keep_all':[False]*64,'always_27b':[True]*64,
        'learned_value':[row['decision']=='ESCALATE' for row in routed]}
    policies.update({name:[row['selected'] for row in choices] for name,choices in controls['predictions'].items()})
    table={}
    for name,selection in policies.items():
        chosen=[row for row,active in zip(rows,selection,strict=True) if active]
        table[name]=dict(success=before+sum(row['utility'] for row in chosen),
            recovered=sum(row['utility']>0 for row in chosen),damaged=sum(row['utility']<0 for row in chosen),
            calls=len(chosen),posts=sum(row['posts'] for row in chosen),tokens=sum(row['tokens'] for row in chosen),
            actor_seconds=sum(row['seconds'] for row in chosen))
    assert table['learned_value']['success']==m.read(ROOT/'DEV_RESULT.json')['summary']['success']
    rng=np.random.default_rng(20261117);samples=[]
    for _ in range(2000):
        chosen=rng.choice(64,controls['budget'],replace=False)
        samples.append(before+sum(rows[int(i)]['utility'] for i in chosen))
    result=dict(status='RETURNED',policies=table,random_allocation=dict(draws=2000,seed=20261117,
        mean_success=float(np.mean(samples)),p05=float(np.quantile(samples,.05)),p95=float(np.quantile(samples,.95))),
        scope='Routing controls replay one actual fixed OpenCode/27B response per state; not new independent actor runs. Reused18 calls are not charged twice.')
    m.study.new(ROOT/'routing_controls/COMPARISON.json',result);print(json.dumps(result),flush=True)


def reference_check():
    import os
    live=ROOT/'REFERENCE_CHECK_LIVE.json'
    state=dict(status='RUNNING',pid=os.getpid(),start_ticks=Path('/proc/self/stat').read_text().split()[21],phase='CONTROL_TRAIN')
    m.study.publish(live,state)
    try:
        routing_controls();state['phase']='WAIT_REFERENCE';m.study.publish(live,state);started=time.monotonic()
        while not (ROOT/'expert_reference/RESULT.json').exists():
            if time.monotonic()-started>3600:raise TimeoutError('reference wait cap')
            time.sleep(10)
        compare_routing();state.update(status='RETURNED',phase='FINISHED')
    except BaseException:state.update(status='FAILED',error=traceback.format_exc())
    finally:m.study.publish(live,state)


def collect_reference_student():
    """Collect old37 on the same TRAIN states, with its unchanged native policy."""
    root=RELATIVE_ROOT;root.mkdir()
    previous=m.read(c.step1/'PLAN.json');runtime=previous['runtime']
    cached=m.read(root.parent/'paired_state_negatives_v1/native_v1/PLAN.json')
    reference=next(ep for ep in cached['episodes'] if ep['arm']=='paired_state_branch')
    template=Path(reference['folder'])/'inputs'
    source0=Path(cached['source_episodes'][0]['folder'])
    assert (template/'task.txt').read_text()==m.review_prompt(
        m.read(source0/'inputs/public.json'),m.state_from_folder(source0),terminal_program=True)
    teacher={row['index']:row for row in m.read(SOURCE/'RESULT.json')['episodes']}
    episodes=[]
    for event in m.read_lines(c.step1/'source_events.jsonl'):
        source=Path(event['folder']);folder=root/'train'/f"{event['index']:03d}"
        public=m.read(source/'inputs/public.json');snapshot=m.state_from_folder(source)
        assert public['id']==teacher[event['index']]['id']
        target=folder/'inputs';target.mkdir(parents=True)
        for name in ['work','dependencies']:shutil.copytree(source/name,folder/name)
        for name in ['finqa_tool.py','executor.py','guest.py']:shutil.copyfile(template/name,target/name)
        (target/'public.json').write_text(json.dumps(public,ensure_ascii=False))
        (target/'task.txt').write_text(m.review_prompt(public,snapshot,terminal_program=True))
        episodes.append(dict(index=event['index'],id=public['id'],report=public['report'],
            folder=str(folder),source_folder=str(source)))
    assert len(episodes)==96
    plan=dict(episodes=episodes,runtime=runtime,caps=cached['caps'],adapter=previous['old37_adapter'],
        wall_seconds=3600,reference_template=str(template),
        scope='Same TRAIN first-pass states as the27B/DeepSeek collections; unchanged old37 native policy. No DEV or reserved64.')
    m.study.new(root/'CHEAP_PLAN.json',plan)
    state=dict(status='RUNNING',phase='OLD37_TRAIN',pid=os.getpid(),
        start_ticks=Path('/proc/self/stat').read_text().split()[21],episodes=[])
    m.study.publish(root/'CHEAP_LIVE.json',state);process=log=None;unloaded=False;started=time.monotonic()
    try:
        unloaded=c.stop27()
        with m.study.core.resource_lock():
            h=m.study.core.helpers();checked=h.deps.verify_projection(h.actor.RUNTIME_ROOT,h.actor.RUNTIME_SHA)
            m.study.CAPS.clear();m.study.CAPS.update(plan['caps'])
            (root/'cheap37').mkdir();process,log=c.native.start_server(runtime,'cheap37',Path(plan['adapter']),root)
            for ep in episodes:
                if time.monotonic()-started>plan['wall_seconds']:raise TimeoutError('TRAIN collection wall cap')
                result=m.study.episode(ep,h,checked,m.study.MODEL,private_labels=c.step1/'TRAIN_LABELS_PRIVATE.json')
                before=m.read(Path(ep['source_folder'])/'RESULT.json')['native_success']
                row=dict(index=ep['index'],id=ep['id'],report=ep['report'],folder=ep['folder'],
                    before_success=before,success=result['native_success'],program=result['submitted_program'],
                    utility=int(result['native_success'])-int(before),
                    posts=result['accounting']['actual_forwarded_posts'],tokens=result['accounting']['provider_total_tokens_known'],
                    unknown=len(result['accounting']['unknown_usage_requests']),seconds=result['actor']['seconds'])
                state['episodes'].append(row);m.study.publish(root/'CHEAP_LIVE.json',state)
                print(json.dumps({k:row[k] for k in ['index','utility','posts','tokens','unknown']}),flush=True)
                if (result['actor'].get('error') or {}).get('type')=='KeyboardInterrupt':raise KeyboardInterrupt()
                if row['unknown']:raise RuntimeError('unknown usage; inspect this native attempt instead of retrying')
        rows=state['episodes'];state.update(status='RETURNED',summary=dict(tasks=len(rows),
            before=sum(x['before_success'] for x in rows),success=sum(x['success'] for x in rows),
            recovered=sum(x['utility']>0 for x in rows),damaged=sum(x['utility']<0 for x in rows),
            posts=sum(x['posts'] for x in rows),tokens=sum(x['tokens'] for x in rows),unknown=sum(x['unknown'] for x in rows)))
    except BaseException:state.update(status='FAILED',error=traceback.format_exc())
    finally:
        if process is not None:c.native.stop_server(process,log)
        if unloaded:state['restoration']=c.restore27()
        state['seconds']=time.monotonic()-started
        m.study.publish(root/'CHEAP_LIVE.json',state);m.study.new(root/'CHEAP_RESULT.json',state)
        print(json.dumps({k:v for k,v in state.items() if k!='episodes'}),flush=True)


def fit_relative_value():
    """Predict strong-minus-cheap outcome, rather than original error risk."""
    import torch
    from sklearn.model_selection import GroupKFold
    root=RELATIVE_ROOT;cheap=m.read(root/'CHEAP_RESULT.json');expert=m.read(SOURCE/'RESULT.json')
    assert cheap['status']==expert['status']=='RETURNED' and len(cheap['episodes'])==len(expert['episodes'])==96
    plan=m.read(ROOT/'FEATURE_PLAN.json');features=np.load(ROOT/'FEATURES.npz')
    old={row['index']:row for row in cheap['episodes']};teacher={row['index']:row for row in expert['episodes']}
    collected={row['index']:row for row in m.read(root/'CHEAP_PLAN.json')['episodes']}
    utility=[]
    for index,source in enumerate(plan['train']):
        a,b=old[index],teacher[index]
        assert a['id']==b['id']==source['id'] and a['before_success']==b['before_success']
        assert m.state_from_folder(Path(collected[index]['source_folder']))['current_program']==b['before_program']
        assert not a['unknown'] and not b['unknown']
        utility.append(int(b.get('after_success',b.get('success')))-int(a['success']))
    x=features['train'];utility=np.asarray(utility);y=np.where(utility==1,1,np.where(utility==-1,2,0))
    groups=['/'.join(row['report'].split('/')[:2]) for row in plan['train']]
    # One fixed call budget and zero gain threshold, frozen before any DEV label.
    protocol=m.read(root/'RELATIVE_PROTOCOL.json');budget=protocol['strong_budget'];assert protocol['threshold']==0
    started=time.monotonic();torch.set_num_threads(4);oof=np.zeros((96,3),dtype=np.float32)
    for fold,(a,b) in enumerate(GroupKFold(4).split(x,y,groups)):
        saved,model=fit_once(x[a],y[a],17+fold);oof[b]=probability(saved,model,x[b])
    saved,model=fit_once(x,y,21);torch.save(saved,root/'RELATIVE_POLICY.pt')
    probs=probability(saved,model,features['dev']);gains=probs[:,1]-probs[:,2]
    ranked=sorted(range(len(gains)),key=lambda index:(-float(gains[index]),index))
    selected=set(index for index in ranked[:budget] if gains[index]>0)
    decisions=[dict(index=row['index'],id=row['id'],score=float(gains[i]),
        decision='EXPERT27' if i in selected else 'CHEAP37') for i,row in enumerate(plan['dev'])]
    calibration=oof[:,1]-oof[:,2];ranked_train=sorted(range(96),key=lambda i:(-float(calibration[i]),i))
    selected_train=[i for i in ranked_train[:budget*96//64] if calibration[i]>0]
    m.study.new(root/'RELATIVE_TRAIN_RESULT.json',dict(source_rows=96,utility_counts=dict(collections.Counter(map(int,utility))),
        objective='C(expert27)-C(cheap37), both from the same original public state',
        fixed_threshold=0,dev_strong_budget=budget,OOF_selected=len(selected_train),
        OOF_net_gain=int(utility[selected_train].sum()),optimizer_updates=1000,encoder_calls=0,
        encoder_cache_reused=True,seconds=time.monotonic()-started))
    m.study.new(root/'RELATIVE_PREDICTIONS.json',dict(decisions=decisions,strong_budget=budget,
        selection='Positive predicted relative gain, top18 maximum; no DEV outcomes or cheap proposals used as policy inputs.'))
    print(json.dumps(dict(TRAIN_utility_counts=dict(collections.Counter(map(int,utility))),
        OOF_net_gain=int(utility[selected_train].sum()),DEV_selected=len(selected))),flush=True)


def evaluate_relative_value():
    """Execute selected27B continuations; reuse unchanged cheap37 native cache."""
    import http.client
    from finqa_patch_proposals import proposal_relay
    root=RELATIVE_ROOT;predictions=m.read(root/'RELATIVE_PREDICTIONS.json')['decisions']
    feature=m.read(ROOT/'FEATURE_PLAN.json');sources=feature['dev']
    cached=m.read(root.parent/'paired_state_negatives_v1/native_v1/PLAN.json')
    cheap={ep['index']:ep for ep in cached['episodes'] if ep['arm']=='paired_state_branch'}
    assert len(predictions)==len(sources)==len(cheap)==64
    profile=dict(host='127.0.0.1',port=8006,model_id='qwen38-27b-fp8',context=32768,output=8192)
    state=dict(status='RUNNING',pid=os.getpid(),start_ticks=Path('/proc/self/stat').read_text().split()[21],episodes=[],health_gets=0)
    m.study.publish(root/'RELATIVE_DEV_LIVE.json',state);started=time.monotonic()
    try:
        if any(x['decision']=='EXPERT27' for x in predictions):
            deadline=time.monotonic()+180
            while True:
                state['health_gets']+=1
                try:
                    conn=http.client.HTTPConnection(profile['host'],profile['port'],timeout=3)
                    conn.request('GET','/health');response=conn.getresponse();response.read();conn.close()
                    if response.status==200:break
                except OSError:pass
                if time.monotonic()>deadline:raise TimeoutError('owned27 service not ready; do not launch a second model')
                time.sleep(2)
        with m.study.core.resource_lock():
            h=m.study.core.helpers();checked=h.deps.verify_projection(h.actor.RUNTIME_ROOT,h.actor.RUNTIME_SHA)
            m.study.CAPS.clear();m.study.CAPS.update(m.read(c.root/'PLAN.json')['caps'])
            for source,decision in zip(sources,predictions,strict=True):
                assert source['id']==decision['id']==cheap[source['index']]['id']
                folder=Path(source['folder']);public=m.read(folder/'inputs/public.json');snapshot=m.state_from_folder(folder)
                cached_folder=Path(cheap[source['index']]['folder']);old=m.read(cached_folder/'RESULT.json')
                assert (cached_folder/'inputs/task.txt').read_text()==m.review_prompt(public,snapshot,terminal_program=True)
                before=m.read(folder/'RESULT.json')['native_success'];target=root/'dev'/f"{source['index']:03d}"
                if decision['decision']=='EXPERT27':
                    from finqa_proposal_acceptance import inputs as proposal_inputs
                    # Public preparation is the original four-operator prompt, not PROPOSE mode.
                    proposal_inputs(target,folder)
                    (target/'inputs/task.txt').write_text(c.prompt(public,snapshot))
                    ep=dict(index=source['index'],id=source['id'],report=public['report'],folder=str(target))
                    result=m.study.episode(ep,h,checked,profile,
                        private_labels=Path(folder).parent.parent/'LABELS_PRIVATE.json',relay_factory=proposal_relay)
                    new_posts=result['accounting']['actual_forwarded_posts'];new_tokens=result['accounting']['provider_total_tokens_known']
                    unknown=len(result['accounting']['unknown_usage_requests'])
                else:result=old;new_posts=new_tokens=unknown=0
                final=root/'final'/f"{source['index']:03d}";final.mkdir(parents=True)
                m.task.submit_program(result['submitted_program'],public,final,origin=decision['decision'])
                labels=m.read(Path(folder).parent.parent/'LABELS_PRIVATE.json')
                verified=m.task.grade(result['submitted_program'],public,labels[source['index']]['exe_ans'])
                assert verified['execution_correct']==result['execution_correct']
                row=dict(index=source['index'],id=source['id'],decision=decision['decision'],
                    before_success=before,cheap_success=old['native_success'],success=result['native_success'],
                    utility=int(result['native_success'])-int(old['native_success']),program=result['submitted_program'],
                    actual_new_posts=new_posts,actual_new_tokens=new_tokens,actual_new_unknown=unknown,
                    policy_posts=result['accounting']['actual_forwarded_posts'],
                    policy_tokens=result['accounting']['provider_total_tokens_known'],policy_actor_seconds=result['actor']['seconds'])
                state['episodes'].append(row);m.study.publish(root/'RELATIVE_DEV_LIVE.json',state)
                print(json.dumps(dict(index=row['index'],decision=row['decision'],relative_gain=row['utility'])),flush=True)
                if unknown or (result['actor'].get('error') or {}).get('type')=='KeyboardInterrupt':
                    raise RuntimeError('interrupted native result retained; stop instead of retrying')
        rows=state['episodes'];state.update(status='RETURNED',summary=dict(tasks=len(rows),
            before=sum(x['before_success'] for x in rows),cheap_reference=sum(x['cheap_success'] for x in rows),
            success=sum(x['success'] for x in rows),relative_recovered=sum(x['utility']>0 for x in rows),
            relative_damaged=sum(x['utility']<0 for x in rows),
            recovered=sum(x['success'] and not x['before_success'] for x in rows),
            damaged=sum(x['before_success'] and not x['success'] for x in rows),
            strong_episodes=sum(x['decision']=='EXPERT27' for x in rows),
            actual_new_posts=sum(x['actual_new_posts'] for x in rows),actual_new_tokens=sum(x['actual_new_tokens'] for x in rows),
            policy_posts=sum(x['policy_posts'] for x in rows),policy_tokens=sum(x['policy_tokens'] for x in rows),
            policy_actor_seconds=sum(x['policy_actor_seconds'] for x in rows),
            scope='Cheap native outputs cached; selected expert continuations new and from the same original state. Actor sum excludes loading/swap time; shared firstpass not recharged.'))
    except BaseException:state.update(status='FAILED',error=traceback.format_exc())
    finally:
        state['seconds']=time.monotonic()-started;m.study.publish(root/'RELATIVE_DEV_LIVE.json',state)
        m.study.new(root/'RELATIVE_DEV_RESULT.json',state)
        print(json.dumps({k:v for k,v in state.items() if k!='episodes'}),flush=True)


CHOICE_TOOL='''from pathlib import Path
import argparse,json
import finqa_correction as task
task.executor(Path('/inputs/executor.py'))
p=argparse.ArgumentParser();p.add_argument('--program');p.add_argument('--final-jsonl');a=p.parse_args()
public=json.loads(Path('/inputs/public.json').read_text())
spec=json.loads(Path('/inputs/candidates.json').read_text())
if a.program is not None:
 print(json.dumps(task.execute_public(a.program,public)))
else:
 events=[json.loads(s) for s in Path(a.final_jsonl).read_text().splitlines() if s.strip()]
 value=task.terminal_proposal(events);declared=value.get('program')
 allowed={x['program'] for x in spec['candidates']};valid=isinstance(declared,str) and declared in allowed
 selected=declared if valid else spec['default_program']
 receipt=dict(in_menu=valid,fallback=not valid,declared=declared,program=selected)
 Path('/workspace/choice.json').write_text(json.dumps(receipt))
 receipt['execution']=task.submit_program(selected,public,Path('/workspace'),origin='candidate_choice')
 print(json.dumps(receipt))
'''


def candidate_choice_probe():
    """Use full candidate/trace information; no new head or actor training."""
    import random
    root=RELATIVE_ROOT/'candidate_choice_v1';root.mkdir();prior=m.read(c.step1/'PLAN.json')
    features=m.read(ROOT/'FEATURE_PLAN.json');train=m.read(RELATIVE_ROOT/'CHEAP_RESULT.json')['episodes']
    teachers={x['index']:x for x in m.read(SOURCE/'RESULT.json')['episodes']}
    original={x['index']:x for x in m.read(RELATIVE_ROOT/'CHEAP_PLAN.json')['episodes']}
    cached=m.read(root.parent.parent/'paired_state_negatives_v1/native_v1/PLAN.json')
    cheap_dev={x['index']:x for x in cached['episodes'] if x['arm']=='paired_state_branch'}
    # Full DeepSeek native outputs are DEV-only and never enter the TRAIN probe.
    def cases(phase):
        if phase=='train':
            rows=[]
            for a in train:
                b=teachers[a['index']];success=b.get('after_success',b.get('success'))
                if a['success']==success:continue
                rows.append(dict(index=a['index'],id=a['id'],source=original[a['index']]['source_folder'],
                    cheap_program=a['program'],expert_program=b['after_program'],cheap_success=a['success']))
            return rows,c.step1/'TRAIN_LABELS_PRIVATE.json'
        ds=m.read(root.parent.parent/'deepseek_development_reference_v1/RESULT.json');assert ds['status']=='RETURNED'
        reference={x['index']:x for x in ds['episodes']};rows=[]
        for source in features['dev']:
            a=m.read(Path(cheap_dev[source['index']]['folder'])/'RESULT.json');b=reference[source['index']]
            assert a['id']==b['id']==source['id']
            rows.append(dict(index=source['index'],id=source['id'],source=source['folder'],
                cheap_program=a['submitted_program'],expert_program=b['submitted_program'],cheap_success=a['native_success']))
        return rows,Path(features['dev'][0]['folder']).parent.parent/'LABELS_PRIVATE.json'
    caps=dict(posts=2,seconds=90,combined_wire_bytes=16777216)
    m.study.new(root/'PLAN.json',dict(caps=caps,TRAIN_pass_success=11,TRAIN_expected_cases=16,
        protocol='Anonymous A/B programs and actual public execution traces. Choose a supplied program via Final program. Off-menu defaults to cheap; equal executed values bypass the judge. Only after TRAIN>=11/16 evaluate DEV.',
        weights='unchanged old37; no optimizer updates',scope='DEV teacher programs remain DEV-only. This is a capability probe, not trained selector evidence.'))
    state=dict(status='RUNNING',pid=os.getpid(),start_ticks=Path('/proc/self/stat').read_text().split()[21],phases={})
    m.study.publish(root/'LIVE.json',state);process=log=None;unloaded=False;started=time.monotonic()
    try:
        unloaded=c.stop27()
        with m.study.core.resource_lock():
            h=m.study.core.helpers();checked=h.deps.verify_projection(h.actor.RUNTIME_ROOT,h.actor.RUNTIME_SHA)
            m.study.CAPS.clear();m.study.CAPS.update(caps)
            (root/'model37').mkdir();process,log=c.native.start_server(prior['runtime'],'model37',Path(prior['old37_adapter']),root)
            for phase in ['train','dev']:
                rows,labels_path=cases(phase)
                if phase=='train':assert len(rows)==16
                state['phase']=phase;state['phases'][phase]=[]
                for row in rows:
                    source=Path(row['source']);folder=root/phase/f"{row['index']:03d}";inputs=folder/'inputs';inputs.mkdir(parents=True)
                    public=m.read(source/'inputs/public.json');assert public['id']==row['id']
                    programs=[row['cheap_program'],row['expert_program']]
                    feedback=[m.task.execute_public(program,public) for program in programs]
                    same=(feedback[0]['status']==feedback[1]['status']=='executed' and
                        m.task.canonical_answer(feedback[0]['terminal_execution_answer'])==m.task.canonical_answer(feedback[1]['terminal_execution_answer']))
                    for name in ['work','dependencies']:shutil.copytree(source/name,folder/name)
                    m.task.submit_program(row['cheap_program'],public,folder/'work',origin='candidate_choice_initial')
                    if same:
                        success=m.task.grade(row['cheap_program'],public,m.read(labels_path)[row['index']]['exe_ans'])['execution_correct']
                        assert success==row['cheap_success'];posts=tokens=unknown=0;actor_seconds=0;in_menu=True;selected=row['cheap_program']
                    else:
                        order=[0,1];random.Random(17+row['index']).shuffle(order)
                        candidates=[dict(name=name,program=programs[i],execution_feedback=feedback[i]) for name,i in zip(['A','B'],order)]
                        spec=dict(default_program=row['cheap_program'],candidates=candidates)
                        text=(m.study.prompt(public,terminal_program=True)+'\n\nCompare the two anonymously supplied candidate programs below with the question and report. '
                            'The numeric executions are observed results, not correctness labels. One, both or neither candidate may be correct. '
                            'Check the quantities, years, formula and units. Choose only one supplied complete program; do not invent a third. '
                            'If evidence does not distinguish them, retain the initial workspace program. Finish with its exact Final program: declaration.\n'
                            +json.dumps(dict(candidates=candidates),ensure_ascii=False))
                        for name,value in [('public.json',public),('candidates.json',spec)]: (inputs/name).write_text(json.dumps(value,ensure_ascii=False))
                        (inputs/'task.txt').write_text(text);(inputs/'finqa_tool.py').write_text(CHOICE_TOOL)
                        (inputs/'finqa_correction.py').write_text(Path(m.task.__file__).read_text())
                        (inputs/'executor.py').write_text(Path(m.task.executor().__file__).read_text())
                        (inputs/'guest.py').write_text(m.study.guest_source(terminal_program=True))
                        ep=dict(index=row['index'],id=row['id'],folder=str(folder),report=public['report'])
                        result=m.study.episode(ep,h,checked,m.study.MODEL,private_labels=labels_path)
                        success=result['native_success'];selected=result['submitted_program'];actor_seconds=result['actor']['seconds']
                        posts=result['accounting']['actual_forwarded_posts'];tokens=result['accounting']['provider_total_tokens_known']
                        unknown=len(result['accounting']['unknown_usage_requests'])
                        receipt=folder/'work/choice.json';in_menu=m.read(receipt)['in_menu'] if receipt.exists() else False
                    value=dict(index=row['index'],id=row['id'],before=row['cheap_success'],success=success,
                        utility=int(success)-int(row['cheap_success']),program=selected,posts=posts,tokens=tokens,
                        unknown=unknown,seconds=actor_seconds,equal_value_skip=same,in_menu=in_menu)
                    state['phases'][phase].append(value);m.study.publish(root/'LIVE.json',state)
                    print(json.dumps(dict(phase=phase,index=row['index'],utility=value['utility'],posts=posts)),flush=True)
                    if unknown:raise RuntimeError('unknown native usage; stop this probe without retry')
                done=state['phases'][phase];summary=dict(tasks=len(done),before=sum(x['before'] for x in done),success=sum(x['success'] for x in done),
                    recovered=sum(x['utility']>0 for x in done),damaged=sum(x['utility']<0 for x in done),
                    posts=sum(x['posts'] for x in done),tokens=sum(x['tokens'] for x in done),
                    judge_cases=sum(not x['equal_value_skip'] for x in done),off_menu=sum(not x['in_menu'] for x in done))
                state[phase+'_summary']=summary;print(json.dumps(dict(phase=phase,summary=summary)),flush=True)
                if phase=='train' and summary['success']<11:
                    state['decision']='No >=2 improvement over fixed cheap on TRAIN16; stop before DEV';break
        state['status']='RETURNED'
    except BaseException:state.update(status='FAILED',error=traceback.format_exc())
    finally:
        if process is not None:c.native.stop_server(process,log)
        if unloaded:state['restoration']=c.restore27()
        state['seconds']=time.monotonic()-started;m.study.publish(root/'LIVE.json',state);m.study.new(root/'RESULT.json',state)
        print(json.dumps({k:v for k,v in state.items() if k!='phases'}),flush=True)


def collect_full_teacher(root,key):
    """Full native teacher policy, matching the saved38/64 reference."""
    from scripts.graph.research_school_gateway import BatchBudget,SchoolBackend,BASE_URL,MODEL,REQUEST_TOKEN_CEILING
    cached=m.read(RELATIVE_ROOT/'CHEAP_PLAN.json');template=Path(cached['reference_template'])
    cheap={x['index']:x for x in m.read(RELATIVE_ROOT/'CHEAP_RESULT.json')['episodes']}
    profile=dict(provider='bupt_chat_v1',base_url=BASE_URL,model_id=MODEL,context=262144,output=8192)
    # Configuration and caps match the full native DeepSeek DEV reference;
    # no final-only JSON restriction or removed tool interface is applied.
    reference=m.read(root.parent.parent/'deepseek_development_reference_v1/PLAN.json')
    assert reference['model']==profile
    caps=reference['caps'];budget=BatchBudget(root/'budget',posts=384,tokens=3_000_000)
    backend=SchoolBackend(key,budget,m.study.core);backend.verify(profile)
    plan=dict(model=profile,caps=caps,max_posts=384,token_cap=3_000_000,wall_seconds=3600,
        inputs='Same96 TRAIN original states as cheap37; full native tools/Finalprogram, no gold in actor inputs.',
        reference='deepseek_development_reference_v1,38/64',prediction='Teacher source data for guarded correction acquisition; no new DEV or reserved64.')
    m.study.new(root/'PLAN.json',plan);started=time.monotonic()
    state=dict(status='RUNNING',pid=os.getpid(),start_ticks=Path('/proc/self/stat').read_text().split()[21],episodes=[])
    def persist():
        state.update(posts=sum(x['state']!='not_sent' for x in budget.rows),
            known_tokens=sum(x.get('usage',{}).get('total_tokens',0) for x in budget.rows),
            unknown=sum(x['state']=='unknown' for x in budget.rows),seconds=time.monotonic()-started)
        state['unknown_reserved_tokens']=state['unknown']*REQUEST_TOKEN_CEILING
        m.study.publish(root/'LIVE.json',state)
    persist()
    try:
        with m.study.core.resource_lock():
            h=m.study.core.helpers();checked=h.deps.verify_projection(h.actor.RUNTIME_ROOT,h.actor.RUNTIME_SHA)
            m.study.CAPS.clear();m.study.CAPS.update(caps)
            for source_ep in cached['episodes']:
                if time.monotonic()-started>plan['wall_seconds']:raise TimeoutError('full teacher batch wall cap')
                source=Path(source_ep['source_folder']);folder=root/'train'/f"{source_ep['index']:03d}"
                public=m.read(source/'inputs/public.json');snapshot=m.state_from_folder(source)
                assert public['id']==source_ep['id']==cheap[source_ep['index']]['id']
                target=folder/'inputs';target.mkdir(parents=True)
                for name in ['work','dependencies']:shutil.copytree(source/name,folder/name)
                for name in ['finqa_tool.py','executor.py','guest.py']:shutil.copyfile(template/name,target/name)
                (target/'public.json').write_text(json.dumps(public,ensure_ascii=False))
                (target/'task.txt').write_text(m.review_prompt(public,snapshot,terminal_program=True))
                ep=dict(index=source_ep['index'],id=public['id'],report=public['report'],folder=str(folder))
                value=m.study.episode(ep,h,checked,profile,private_labels=c.step1/'TRAIN_LABELS_PRIVATE.json',relay_factory=backend.make_relay)
                row=dict(index=ep['index'],id=ep['id'],folder=str(folder),cheap_success=cheap[ep['index']]['success'],
                    success=value['native_success'],program=value['submitted_program'],cheap_program=cheap[ep['index']]['program'],
                    utility=int(value['native_success'])-int(cheap[ep['index']]['success']),
                    posts=value['accounting']['actual_forwarded_posts'],tokens=value['accounting']['provider_total_tokens_known'],
                    unknown=len(value['accounting']['unknown_usage_requests']),seconds=value['actor']['seconds'])
                state['episodes'].append(row);persist()
                print(json.dumps({k:row[k] for k in ['index','utility','posts','tokens','unknown']}),flush=True)
                if row['unknown'] or not value['accounting']['integrity_passed']:
                    raise RuntimeError('native transport issue retained; inspect rather than retry')
                if (value['actor'].get('error') or {}).get('type')=='KeyboardInterrupt':raise KeyboardInterrupt()
        state['status']='RETURNED'
    except BaseException:state.update(status='FAILED',error=traceback.format_exc())
    finally:
        if budget.pending is not None:budget.finish()
        persist();budget.close();m.study.new(root/'RESULT.json',state)
        print(json.dumps({k:v for k,v in state.items() if k!='episodes'}),flush=True)


def launch_full_teacher():
    """Detach after echo-hidden input; credentials live only in child memory."""
    import getpass
    print('CREDENTIAL_INPUT_READY',flush=True)
    key=os.environ.get('BUPT_API_KEY') or getpass.getpass('Campus credential (hidden): ')
    if not key:raise ValueError('no campus credential')
    root=RELATIVE_ROOT/'full_teacher_train';root.mkdir()
    output=(root/'supervisor.log').open('xb');pid=os.fork()
    if pid:
        output.close();print('CAMPUS_WORKER_PID='+str(pid),flush=True);return
    os.setsid();os.dup2(output.fileno(),1);os.dup2(output.fileno(),2)
    null=os.open(os.devnull,os.O_RDONLY);os.dup2(null,0);os.close(null)
    try:collect_full_teacher(root,key)
    except BaseException:traceback.print_exc()
    finally:os._exit(0)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('mode',choices=['prepare','train','evaluate','expert-reference','reference-check','relative-cheap','relative-fit','relative-evaluate','choice-probe','relative-campus']);args=parser.parse_args()
    {'prepare':prepare,'train':train,'evaluate':evaluate,'expert-reference':expert_reference,'reference-check':reference_check,
        'relative-cheap':collect_reference_student,'relative-fit':fit_relative_value,'relative-evaluate':evaluate_relative_value,
        'choice-probe':candidate_choice_probe,'relative-campus':launch_full_teacher}[args.mode]()
