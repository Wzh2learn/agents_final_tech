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


def train():
    import torch
    from sklearn.model_selection import GroupKFold
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


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('mode',choices=['prepare','train','evaluate']);args=parser.parse_args()
    {'prepare':prepare,'train':train,'evaluate':evaluate}[args.mode]()
