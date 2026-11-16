"""A small pre-call recovery/damage predictor, learned from TRAIN executions."""
from pathlib import Path
import argparse,collections,json,re,shutil,time,traceback
import numpy as np
import finqa_patch_learning as c

m=c.m
ROOT=c.root.parent/'correction_router_v1'
SOURCE=c.root.parent/'correction_value_27b_v1'


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


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('mode',choices=['prepare','train','evaluate','expert-reference','reference-check']);args=parser.parse_args()
    {'prepare':prepare,'train':train,'evaluate':evaluate,'expert-reference':expert_reference,'reference-check':reference_check}[args.mode]()
