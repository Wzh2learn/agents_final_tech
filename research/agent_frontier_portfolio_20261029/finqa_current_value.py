"""One CPU value-head trial on executed states; the native corrector stays fixed."""
from pathlib import Path
import collections,json,os,time,traceback
import numpy as np
import finqa_inline_value as prior

m=prior.m
ROOT=prior.BASE/'current_value_cpu_v1'


def features(encoder,examples):
    texts=[];numeric=[]
    for public,program in examples:
        state=dict(current_program=program,execution_feedback=m.task.execute_public(program,public))
        basic,evidence,values=prior.acquisition.router.public_features(public,state)
        texts.extend([basic,evidence]);numeric.append(values)
    vectors=np.asarray(encoder.encode(texts,batch_size=16,show_progress_bar=False,normalize_embeddings=True))
    a,b=vectors[::2],vectors[1::2]
    return np.concatenate([a,b,a*b,np.abs(a-b),np.asarray(numeric)],axis=1)


def run():
    import torch
    from sentence_transformers import SentenceTransformer
    from sklearn.linear_model import LogisticRegression
    torch.set_num_threads(4);ROOT.mkdir();started=time.monotonic()
    state=dict(status='RUNNING',phase='ENCODE',pid=os.getpid(),
        start_ticks=Path('/proc/self/stat').read_text().split()[21],encoder_forwards=0,
        encoder_active_tokens=0,encoder_padded_positions=0,device='cpu',new_model_posts=0)
    m.study.new(ROOT/'PLAN.json',dict(actor='Frozen old37 native outputs; no Actor updates',
        sources=153,views=323,primary_budget=18,secondary_budgets=[8,12],
        features='Existing BGE-small384 encoder and numeric features, now using each actual current program and public execution feedback instead of the original before-state.',
        learner='Single source-weighted multinomial LogisticRegression C=1,max_iter=300,seed21; no feature/threshold/hyperparameter search.',
        stop='One candidate against cached41 and fixed random. No reruns, Actor training or new teacher sampling; confirmation64 excluded.'))
    encoder=None
    def persist():
        state['seconds']=time.monotonic()-started;m.study.publish(ROOT/'LIVE.json',state)
    persist()
    try:
        views=m.read(prior.BASE/'acquisition_value_expanded_v1/TRAIN_VIEWS.json')['views']
        sources={r['index']:Path(r['source_folder']) for r in m.read(prior.acquisition.router.RELATIVE_ROOT/'CHEAP_PLAN.json')['episodes']}
        sources.update({96+r['index']:Path(r['folder']) for r in m.read(prior.BASE/'forward_sources57_v1/PLAN.json')['episodes']})
        dev_sources=m.read(prior.c.replay/'native_v1/PLAN.json')['source_episodes']
        native=m.read(prior.BASE/'paired_state_negatives_v1/native_v1/PLAN.json')['episodes']
        old={r['index']:r for r in native if r['arm']=='paired_state_branch'}
        assert len(views)==323 and len(sources)==153 and len(dev_sources)==len(old)==64
        publics={i:m.read(p/'inputs/public.json') for i,p in sources.items()}
        assert {p['id'] for p in publics.values()}.isdisjoint(r['id'] for r in dev_sources)
        train=[]
        for view in views:
            public=publics[view['index']];assert public['id']==view['id']
            train.append((public,view['program']))
        dev=[]
        for row in dev_sources:
            i=row['index'];folder=Path(old[i]['folder'])
            public=m.read(Path(row['folder'])/'inputs/public.json');snapshot=m.state_from_folder(folder)
            assert row['id']==old[i]['id']==public['id']
            dev.append((public,snapshot['current_program']))
        feature_plan=m.read(prior.acquisition.router.ROOT/'FEATURE_PLAN.json')
        encoder=SentenceTransformer(feature_plan['encoder'],device='cpu',local_files_only=True)
        encoder.max_seq_length=384
        def count(module,args,kwargs):
            state['encoder_forwards']+=1
            ids=kwargs.get('input_ids');mask=kwargs.get('attention_mask')
            if ids is not None:state['encoder_padded_positions']+=ids.numel()
            if mask is not None:state['encoder_active_tokens']+=int(mask.sum())
        hook=encoder[0].auto_model.register_forward_pre_hook(count,with_kwargs=True)
        before=time.monotonic();x=features(encoder,train)
        state['train_encoding_seconds']=time.monotonic()-before
        state['train_encoder_forwards']=state['encoder_forwards'];persist()
        before=time.monotonic();test=features(encoder,dev)
        state['dev_encoding_seconds']=time.monotonic()-before
        state['dev_encoder_forwards']=state['encoder_forwards']-state['train_encoder_forwards']
        hook.remove();del encoder;encoder=None
        if not state['encoder_forwards']:
            state['encoder_hook_observed']=0
            for name in ['encoder_forwards','encoder_active_tokens','encoder_padded_positions',
                    'train_encoder_forwards','dev_encoder_forwards']:state[name]=None
            state['encoder_accounting']='Forward hook did not fire; neural count/tokens unknown, not zero. CPU wall times retained.'
        counts=collections.Counter(v['index'] for v in views)
        weights=np.asarray([1/counts[v['index']] for v in views])
        assert abs(weights.sum()-153)<1e-8
        mean=np.average(x,axis=0,weights=weights)
        scale=np.maximum(np.sqrt(np.average((x-mean)**2,axis=0,weights=weights)),.01)
        x=(x-mean)/scale;test=(test-mean)/scale
        labels=np.asarray([v['target'] for v in views]);state['phase']='FIT';persist()
        model=LogisticRegression(C=1,max_iter=300,random_state=21)
        model.fit(x,labels,sample_weight=weights)
        assert set(model.classes_)=={'A','B','N'}
        probabilities=model.predict_proba(test)
        scores=probabilities[:,list(model.classes_).index('B')]-probabilities[:,list(model.classes_).index('A')]
        order=sorted(range(64),key=lambda i:(-float(scores[i]),i))
        # Policy freezes before DEV grades or teacher responses are read.
        m.study.new(ROOT/'POLICIES.json',dict(order=order,scores=scores.tolist(),classes=model.classes_.tolist(),
            probabilities=probabilities.tolist(),budgets=[8,12,18],scope='TRAIN-only fit; no DEV labels, no confirmation64'))
        np.savez(ROOT/'POLICY.npz',mean=mean,scale=scale,coef=model.coef_,intercept=model.intercept_,classes=model.classes_)
        state.update(phase='REPLAY',optimizer_iterations=model.n_iter_.tolist(),feature_dimension=x.shape[1]);persist()
        private=m.read(prior.ROOT/'native_nonstream_v1/DEV_LABELS_PRIVATE.json')
        legacy=m.read(prior.BASE/'deepseek_development_reference_v1/RESULT.json')['episodes'];outcomes=[]
        for row,(public,program),label in zip(dev_sources,dev,private,strict=True):
            i=row['index'];local=m.read(Path(old[i]['folder'])/'RESULT.json');teacher=legacy[i]
            for name in ['acquisition_value_v1','acquisition_risk_control_v1','acquisition_single_state_v1']:
                path=prior.BASE/name/'teacher_dev'/f'{i:03d}'/'RESULT.json'
                if path.exists():teacher=m.read(path);break
            assert row['id']==label['id']==local['id']==teacher['id']
            selected,keep=prior.acquisition.guarded_program(program,teacher['submitted_program'],public,teacher['agent_completed'])
            a=bool(m.task.grade(program,public,label['exe_ans'])['execution_correct'] and local['agent_completed'])
            b=bool(m.task.grade(selected,public,label['exe_ans'])['execution_correct'] and (local['agent_completed'] if keep else teacher['agent_completed']))
            outcomes.append(dict(index=i,before=a,after=b,utility=int(b)-int(a),program=selected,
                teacher_posts=teacher['accounting']['actual_forwarded_posts'],teacher_tokens=teacher['accounting']['provider_total_tokens_known']))
        baseline=sum(r['before'] for r in outcomes);assert baseline==37
        table={}
        for k in [8,12,18]:
            chosen=set(order[:k]);selected=[r for r in outcomes if r['index'] in chosen]
            table[str(k)]=dict(success=baseline+sum(r['utility'] for r in selected),
                recovered=sum(r['utility']>0 for r in selected),damaged=sum(r['utility']<0 for r in selected),
                teacher_posts=sum(r['teacher_posts'] for r in selected),teacher_tokens=sum(r['teacher_tokens'] for r in selected))
        state.update(status='RETURNED',phase='CLOSED',native_baseline=baseline,budgets=table,
            train_target_counts=dict(collections.Counter(labels)),outcomes=outcomes,
            scope='CPU-trained selector, actual fixed old37 programs and actual fixed teacher replay. No new OpenCode episodes or model HTTP; CPU encoding time and counter coverage are reported separately.')
    except BaseException:state.update(status='FAILED',error=traceback.format_exc());raise
    finally:
        persist();m.study.new(ROOT/'RESULT.json',state)
    print(json.dumps({k:v for k,v in state.items() if k!='outcomes'}),flush=True)


if __name__=='__main__':run()
