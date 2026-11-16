"""Learn to choose coherent role-bound patches on real OpenCode program states."""
from pathlib import Path
import argparse,collections,itertools,json,math,os,re,time,traceback
import numpy as np
import finqa_patch_learning as c
from finqa_minimal_patches import apply_patches,same_operand

m=c.m
ROOT=c.root.parent/'role_repair_v3'
STOP=set('what was were the in of to for from between a an and is it how much percentage percent change increase decrease growth rate year years'.split())


def words(text):
    return {word.rstrip('s') for word in re.findall('[a-z]+',str(text).lower()) if word not in STOP}


def years(text):
    return list(dict.fromkeys(int(x) for x in re.findall(r'\b(?:19|20)\d{2}\b',str(text))))


def number(text):
    found=re.search(r'(?<![A-Za-z0-9])[-+]?\d[\d,]*(?:\.\d+)?%?',str(text))
    if not found:return None
    token=found[0].replace(',','')
    try:value=float(m.task.executor().parse_numeric_argument(token))
    except Exception:return None
    if not math.isfinite(value):return None
    return dict(token=token,value=value)


def chunks(public):
    """Coherent rows, columns, or text sentences; never a reference answer."""
    table=public['table'];out=[]
    for i,row in enumerate(table):
        items=[]
        for j,cell in enumerate(row[1:],1):
            value=number(cell)
            if value:
                header=str(table[0][j]) if table and j<len(table[0]) else ''
                items.append(dict(value,header=header,years=years(header) or years(row[0]),cell=[i,j]))
        if items:out.append(dict(kind='row',text=' | '.join(map(str,row)),items=items[:8]))
    width=max(map(len,table),default=0)
    for j in range(1,width):
        items=[]
        for i,row in enumerate(table[1:],1):
            if j>=len(row):continue
            value=number(row[j])
            if value:items.append(dict(value,header=str(row[0]),years=(years(table[0][j]) if j<len(table[0]) else []) or years(row[0]),cell=[i,j]))
        if items:out.append(dict(kind='column',text='; '.join(str(table[item['cell'][0]][0])+': '+item['token'] for item in items),items=items[:8]))
    for name in ['pre_text','post_text']:
        for i,text in enumerate(public.get(name,[])):
            items=[]
            for match in re.finditer(r'(?<![A-Za-z0-9])[-+]?\d[\d,]*(?:\.\d+)?%?',str(text)):
                value=number(match[0])
                if value:items.append(dict(value,header=str(text),years=years(text),cell=[i,match.start()]))
            if items:out.append(dict(kind='text',text=str(text),items=items[:8]))
    out.append(dict(kind='constant',text='Numeric neutral elements and small counts',items=[
        dict(token=str(n),value=float(n),header='',years=[],cell=[]) for n in [0,1,2,3,4,100]]))
    q=words(public['question'])
    for item in out:item['lex']=len(q & words(item['text']))/max(1,len(q))
    return out


def bindings(steps,frame,values):
    patches=list(frame['scales'])
    for positions,value in zip(frame['numeric_roles'],values,strict=True):
        old_tokens=collections.defaultdict(list)
        for step,slot in positions:
            old=steps[step].arg1 if slot==1 else steps[step].arg2
            if not same_operand(old,value['token'],m.task.executor()):old_tokens[old].append([step,slot])
        for old,scope in old_tokens.items():
            patches.append(dict(op='rebind_operand',**{'from':old,'to':value['token'],'positions':scope}))
    for ref in frame['reference_bindings']:
        i,slot=ref['position'];old=steps[i].arg1 if slot==1 else steps[i].arg2
        if old!=ref['to']:patches.append(dict(op='rebind_operand',**{'from':old,'to':ref['to'],'positions':[[i,slot]]}))
    return patches


def propose(public,state,templates):
    original=state['current_program'];before=state.get('execution_feedback') or {}
    try:steps=m.task.executor().parse_program(original)
    except Exception:return [],[]
    evidence=chunks(public);candidates={};qyears=years(public['question']);before_value=before.get('terminal_execution_answer')
    def add(patches,origin,values,template,priority):
        if not patches:return
        try:
            program=apply_patches(original,patches)
            result=m.task.execute_public(program,public)
            if result['status']!='executed':return
            if before.get('status')=='executed' and m.task.canonical_answer(result['terminal_execution_answer'])==m.task.canonical_answer(before_value):return
        except Exception:return
        row=dict(program=program,patches=patches,execution=result,chunk=origin,values=values,template=template,priority=priority,
            role_positions=templates[template]['frame']['numeric_roles'] if template>=0 else [])
        if program not in candidates or candidates[program]['priority']<priority:candidates[program]=row
    for mode in ['multiply','divide']:
        for power in [1,2,3,6,9]:
            add([dict(op='scale_output',mode=mode,factor=10**power)],None,[],-1,-1)
    for ti,entry in enumerate(templates):
        frame=entry['frame']
        if frame['operators']!=[step.op for step in steps] or len(frame['numeric_roles'])>2:continue
        if not frame['numeric_roles']:
            add(bindings(steps,frame,[]),None,[],ti,-.5);continue
        for ei,origin in enumerate(evidence):
            for values in itertools.product(origin['items'],repeat=len(frame['numeric_roles'])):
                alignment=0.
                for positions,value in zip(frame['numeric_roles'],values):
                    if not qyears or not value['years']:continue
                    expected=qyears[0]
                    if [0,1] in positions and steps[0].op=='subtract':expected=qyears[-1]
                    alignment+=float(expected in value['years'])
                patch=bindings(steps,frame,values)
                add(patch,ei,list(values),ti,10*origin['lex']+alignment-.02*len(patch))
    ranked=sorted(candidates.values(),key=lambda row:(-row['priority'],row['program']))
    units=[row for row in ranked if row['chunk'] is None][:10]
    tied=[row for row in ranked if row['chunk'] is not None][:40]
    whole=set(row['program'] for row in units+tied)
    for row in tied[:8]:
        if len(row['patches'])<2:continue
        for i in range(len(row['patches'])):
            add(row['patches'][:i]+row['patches'][i+1:],row['chunk'],row['values'],row['template'],row['priority']-.01)
    partial=sorted([row for program,row in candidates.items() if program not in whole],
        key=lambda row:(-row['priority'],row['program']))[:14]
    return units+tied+partial,evidence


def signed_log(value):
    if not isinstance(value,(int,float)) or not math.isfinite(value):return 0.
    return math.copysign(math.log10(1+abs(value)),value)/12


def descriptors(public,state,row,evidence,qvector,evectors):
    """Features are derived from public values/anchors, never correctness."""
    qyears=years(public['question']);origin=evidence[row['chunk']] if row['chunk'] is not None else None
    cosine=float(qvector@evectors[row['chunk']]) if origin else 0.
    lexical=origin['lex'] if origin else 0.;old_best=0.;old_lex=0.
    steps=m.task.executor().parse_program(state['current_program'])
    from_values=[]
    for patch in row['patches']:
        if patch['op']=='rebind_operand':
            try:from_values.append(float(m.task.executor().parse_numeric_argument(patch['from'])))
            except Exception:pass
    for ei,chunk in enumerate(evidence):
        if any(math.isclose(item['value'],old,rel_tol=1e-9,abs_tol=1e-9) for item in chunk['items'] for old in from_values):
            old_best=max(old_best,float(qvector@evectors[ei]));old_lex=max(old_lex,chunk['lex'])
    before=(state.get('execution_feedback') or {}).get('terminal_execution_answer');after=row['execution']['terminal_execution_answer']
    partial_values=[]
    for patch in row['patches']:
        try:
            one=m.task.execute_public(apply_patches(state['current_program'],[patch]),public)
            if one['status']=='executed':partial_values.append(one['terminal_execution_answer'])
        except Exception:pass
    numeric_pair=isinstance(before,(int,float)) and isinstance(after,(int,float))
    interaction=(after-before-sum(value-before for value in partial_values if isinstance(value,(int,float)))) if numeric_pair else 0
    x=[cosine,lexical,old_best,old_lex,cosine-old_best,lexical-old_lex,signed_log(before),signed_log(after),
        signed_log(interaction),float(before==0),float(after==0),float(numeric_pair and before*after<0),len(row['patches'])/8,len(steps)/24]
    for kind in ['row','column','text','constant']:x.append(float(origin is not None and origin['kind']==kind))
    for kind in ['rebind_operand','scale_output','prepend_step']:x.append(sum(p['op']==kind for p in row['patches'])/8)
    for op in ['add','subtract','multiply','divide','exp','greater','table_sum']:
        x.append(sum(step.op==op for step in steps)/8)
    scales=[(1 if p.get('mode')=='multiply' else -1)*math.log10(p['factor']) for p in row['patches'] if p['op']=='scale_output']
    x.append(sum(scales)/9)
    for vi in range(2):
        if vi<len(row['values']):
            value=row['values'][vi];ys=value['years'];expected=(qyears[-1] if vi==0 else qyears[0]) if qyears else 0
            x.extend([signed_log(value['value']),float(bool(ys)),float(expected in ys),
                min([abs(y-expected) for y in ys],default=50)/50,float(bool(set(ys)&set(qyears)))])
        else:x.extend([0.]*5)
    for i in range(6):
        for slot in [1,2]:x.append(float(any([i,slot] in p.get('positions',[]) for p in row['patches'])))
    x.extend([float('percent' in public['question']),float('million' in public['question']),
        float('average' in public['question']),float(len(from_values)!=len(set(from_values)))])
    return enrich(x,public,state,row,evidence)


def enrich(features,public,state,row,evidence):
    """Compare each changed role with its OLD evidence/period binding."""
    x=list(features[:55]);extra=[];qyears=years(public['question'])
    steps=m.task.executor().parse_program(state['current_program'])
    origin=evidence[row['chunk']] if row['chunk'] is not None else None
    for vi in range(2):
        if vi>=len(row['values']):
            extra.extend([0.]*8);continue
        value=row['values'][vi];scope=row.get('role_positions',[[],[]])[vi]
        active=[]
        for patch in row['patches']:
            if patch['op']=='rebind_operand' and same_operand(patch['to'],value['token'],m.task.executor()):
                active.extend(position for position in patch.get('positions',[]) if position in scope)
        expected=(qyears[-1] if [0,1] in scope and steps[0].op=='subtract' else qyears[0]) if qyears else 0
        old_values=[]
        for i,slot in active:
            token=steps[i].arg1 if slot==1 else steps[i].arg2
            try:old_values.append(float(m.task.executor().parse_numeric_argument(token)))
            except Exception:pass
        matches=[item for item in origin['items'] if any(math.isclose(item['value'],old,rel_tol=1e-9,abs_tol=1e-9) for old in old_values)] if origin else []
        old_year=float(any(expected in item['years'] for item in matches)) if expected else 0.
        new_year=float(expected in value['years']) if expected else 0.
        offset=29+5*vi
        x[offset+2]=new_year
        x[offset+3]=min([abs(year-expected) for year in value['years']],default=50)/50 if expected else 1.
        old=old_values[0] if old_values else 0.
        ratio=math.log10(abs(value['value']/old)) if old and value['value'] else 0.
        extra.extend([float(bool(active)),float(bool(matches)),old_year,new_year-old_year,
            signed_log(old),max(-9,min(9,ratio))/9,len(active)/8,float(bool(qyears))])
    return np.asarray(x+extra,dtype=np.float32)


def prepare():
    import torch
    from sentence_transformers import SentenceTransformer
    torch.set_num_threads(4);ROOT.mkdir()
    source=m.read(c.root.parent/'correction_router_v1/FEATURE_PLAN.json')
    templates=m.read(c.step1/'formation_v2/ROLE_BINDING_TEMPLATES.json')['templates']
    encoder=SentenceTransformer(source['encoder'],device='cpu',local_files_only=True);encoder.max_seq_length=256
    labels=m.read(c.step1/'TRAIN_LABELS_PRIVATE.json')
    dataset={};started=time.monotonic();stats={}
    for phase in ['train','dev']:
        tasks=[];phase_started=time.monotonic()
        for ep in source[phase]:
            folder=Path(ep.get('source_folder',ep['folder']));public=m.read(folder/'inputs/public.json');state=m.state_from_folder(folder)
            candidates,evidence=propose(public,state,templates)
            vectors=encoder.encode([public['question']]+[item['text'] for item in evidence],batch_size=16,
                show_progress_bar=False,normalize_embeddings=True) if evidence else None
            for row in candidates:row['features']=descriptors(public,state,row,evidence,vectors[0],vectors[1:]).tolist()
            task=dict(index=ep['index'],id=ep['id'],report=ep['report'],folder=str(folder),candidates=candidates)
            if phase=='train':
                assert labels[ep['index']]['id']==ep['id']
                task['before_success']=m.read(folder/'RESULT.json')['native_success']
                for row in candidates:row['success']=m.task.grade(row['program'],public,labels[ep['index']]['exe_ans'])['execution_correct']
            tasks.append(task)
            m.study.publish(ROOT/'PREPARE_LIVE.json',dict(status='RUNNING',phase=phase,completed=len(tasks),model_http_posts=0))
        dataset[phase]=tasks;stats[phase]=dict(tasks=len(tasks),candidates=sum(len(t['candidates']) for t in tasks),seconds=time.monotonic()-phase_started)
    train=dataset['train'];stats['coverage']=dict(before=sum(t['before_success'] for t in train),
        recoverable=sum(not t['before_success'] and any(row['success'] for row in t['candidates']) for t in train))
    m.study.new(ROOT/'DATA.json',dataset);m.study.new(ROOT/'PLAN.json',dict(stats=stats,templates=templates,
        encoder=source['encoder'],scope='Public role-bound candidates; only TRAIN has correctness labels. DEV scoring after policy freeze.',seconds=time.monotonic()-started))
    m.study.publish(ROOT/'PREPARE_LIVE.json',dict(status='RETURNED',**stats));print(json.dumps(stats),flush=True)


def fit_policy(tasks,seed):
    import torch
    torch.manual_seed(seed)
    arrays=[np.asarray([row['features'] for row in task['candidates']],dtype=np.float32) for task in tasks]
    present=[array for array in arrays if len(array)]
    joined=np.concatenate(present);mean=joined.mean(0);scale=np.maximum(joined.std(0),.05)
    model=make_model(len(mean),bool(tasks[0].get('semantic_vectors')))
    optimizer=torch.optim.AdamW(model.parameters(),lr=.003,weight_decay=.01)
    batches=[]
    for task,array in zip(tasks,arrays,strict=True):
        if not len(array):continue
        target=[i+1 for i,row in enumerate(task['candidates']) if row['success']] if not task['before_success'] else []
        target=target or [0]
        semantic=torch.tensor(task['semantic_vectors'],dtype=torch.float32) if task.get('semantic_vectors') else None
        batches.append((torch.tensor((array-mean)/scale),torch.tensor(target,dtype=torch.long),semantic))
    rng=np.random.default_rng(seed);updates=0
    for epoch in range(12):
        for index in rng.permutation(len(batches)):
            values,target,semantic=batches[int(index)];optimizer.zero_grad()
            scores=torch.cat([torch.zeros(1),model(values,semantic).flatten() if semantic is not None else model(values).flatten()])
            loss=torch.logsumexp(scores,0)-torch.logsumexp(scores[target],0)
            loss.backward();optimizer.step();updates+=1
    model.eval()
    return dict(weights=model.state_dict(),mean=mean,scale=scale,input_size=len(mean),updates=updates,
        semantic=bool(tasks[0].get('semantic_vectors'))),model


def make_model(input_size,semantic=False):
    import torch
    if not semantic:
        return torch.nn.Sequential(torch.nn.Linear(input_size,32),torch.nn.Tanh(),torch.nn.Linear(32,1,bias=False))
    class SemanticCritic(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.binding=torch.nn.Linear(384,24,bias=False)
            self.structured=torch.nn.Sequential(torch.nn.Linear(input_size,32),torch.nn.Tanh())
            self.score=torch.nn.Sequential(torch.nn.Linear(128,48),torch.nn.Tanh(),torch.nn.Linear(48,1,bias=False))

        def forward(self,values,vectors):
            q,new,old=self.binding(vectors).tanh().unbind(1)
            interaction=torch.cat([q,new-old,q*(new-old),new*old,self.structured(values)],dim=-1)
            return self.score(interaction)
    return SemanticCritic()


def rank(saved,model,task):
    import torch
    if not task['candidates']:return dict(candidate=None,score=-1e9)
    values=np.asarray([row['features'] for row in task['candidates']],dtype=np.float32)
    with torch.inference_mode():
        x=torch.tensor((values-saved['mean'])/saved['scale'])
        semantic=torch.tensor(task['semantic_vectors'],dtype=torch.float32) if saved.get('semantic') else None
        scores=(model(x,semantic) if semantic is not None else model(x)).flatten().numpy()
    index=int(scores.argmax());return dict(candidate=index,score=float(scores[index]))


def train():
    import torch
    from sklearn.model_selection import GroupKFold
    torch.set_num_threads(4)
    if (ROOT/'POLICY.pt').exists():raise RuntimeError('this policy is frozen')
    data=m.read(ROOT/'DATA.json');tasks=data['train'];started=time.monotonic()
    groups=['/'.join(task['report'].split('/')[:2]) for task in tasks]
    oof=[None]*len(tasks);updates=0
    for fold,(a,b) in enumerate(GroupKFold(4).split(tasks,groups=groups)):
        saved,model=fit_policy([tasks[i] for i in a],17+fold);updates+=saved['updates']
        for i in b:oof[i]=rank(saved,model,tasks[i])
    choices=[]
    for threshold in [-2,-1,-.5,0,.5,1,2,4,8,1e9]:
        utilities=[];changed=0
        for task,prediction in zip(tasks,oof,strict=True):
            use=prediction['candidate'] is not None and prediction['score']>threshold
            after=task['candidates'][prediction['candidate']]['success'] if use else task['before_success']
            utilities.append(int(after)-int(task['before_success']));changed+=int(use)
        choices.append(dict(threshold=threshold,utility=sum(utilities),changed=changed,objective=sum(utilities)-.002*changed))
    best=max(choices,key=lambda row:(row['objective'],-row['changed'],row['threshold']))
    saved,model=fit_policy(tasks,21);updates+=saved['updates'];torch.save(saved,ROOT/'POLICY.pt')
    decisions=[dict(index=task['index'],id=task['id'],**rank(saved,model,task)) for task in data['dev']]
    for row in decisions:row['decision']='PATCH' if row['candidate'] is not None and row['score']>best['threshold'] else 'KEEP'
    fitted=[]
    for task in tasks:
        prediction=rank(saved,model,task);use=prediction['candidate'] is not None and prediction['score']>0
        after=task['candidates'][prediction['candidate']]['success'] if use else task['before_success']
        fitted.append(dict(index=task['index'],before=task['before_success'],success=after,used=use,
            top_success=task['candidates'][prediction['candidate']]['success'] if prediction['candidate'] is not None else False))
    m.study.new(ROOT/'TRAIN_RESULT.json',dict(optimizer_updates=updates,folds=4,epochs=12,choices=choices,selected=best,
        fitted_at_zero=dict(recovered=sum(not row['before'] and row['success'] for row in fitted),
            damaged=sum(row['before'] and not row['success'] for row in fitted),changed=sum(row['used'] for row in fitted),
            repair_top1=sum(not row['before'] and row['top_success'] for row in fitted)),
        seconds=time.monotonic()-started,scope='Selector grouped CV conditional on TRAIN-mined template bank; this is calibration, not independent confirmation.'))
    m.study.new(ROOT/'PREDICTIONS.json',dict(threshold=best['threshold'],decisions=decisions))
    print(json.dumps(dict(training=best,dev_patches=sum(row['decision']=='PATCH' for row in decisions))),flush=True)


def evaluate():
    data=m.read(ROOT/'DATA.json');decisions=m.read(ROOT/'PREDICTIONS.json')['decisions']
    source=m.read(c.replay/'native_v1/PLAN.json')['source_episodes']
    labels=m.read(Path(source[0]['folder']).parent.parent/'LABELS_PRIVATE.json')
    rows=[];started=time.monotonic();(ROOT/'dev').mkdir()
    for task,decision,ep in zip(data['dev'],decisions,source,strict=True):
        assert task['id']==decision['id']==ep['id']
        folder=Path(ep['folder']);public=m.read(folder/'inputs/public.json');state=m.state_from_folder(folder)
        patches=task['candidates'][decision['candidate']]['patches'] if decision['decision']=='PATCH' else [dict(op='KEEP')]
        try:program=apply_patches(state['current_program'],patches)
        except Exception:program=state['current_program']
        work=ROOT/'dev'/f"{task['index']:03d}";work.mkdir()
        execution=m.task.submit_program(program,public,work,origin='neural_role_repair')
        grade=m.task.grade(program,public,labels[task['index']]['exe_ans'])
        before=m.read(folder/'RESULT.json')['native_success']
        rows.append(dict(index=task['index'],id=task['id'],before_success=before,success=grade['execution_correct'],
            utility=int(grade['execution_correct'])-int(before),decision=decision['decision'],score=decision['score'],
            patches=patches,program=program))
    summary=dict(tasks=len(rows),before=sum(row['before_success'] for row in rows),success=sum(row['success'] for row in rows),
        recovered=sum(row['utility']>0 for row in rows),damaged=sum(row['utility']<0 for row in rows),
        changed=sum(row['decision']=='PATCH' for row in rows),http_posts=0,seconds=time.monotonic()-started,
        scope='Real neural corrective-module inference and native execution on cached actual OpenCode first-pass states; not new LLM/OpenCode actor calls.')
    m.study.new(ROOT/'DEV_RESULT.json',dict(status='RETURNED',summary=summary,episodes=rows));print(json.dumps(summary),flush=True)


def upgrade():
    previous=ROOT.parent/'role_repair_v1';ROOT.mkdir();started=time.monotonic()
    data=m.read(previous/'DATA.json');plan=m.read(previous/'PLAN.json');templates=plan['templates']
    for phase in ['train','dev']:
        for task in data[phase]:
            folder=Path(task['folder']);public=m.read(folder/'inputs/public.json');state=m.state_from_folder(folder);evidence=chunks(public)
            for row in task['candidates']:
                row['role_positions']=templates[row['template']]['frame']['numeric_roles'] if row['template']>=0 else []
                row['features']=enrich(row['features'],public,state,row,evidence).tolist()
    plan.update(feature_version='old/new evidence and role-relative period alignment',reused_bge_features=True,
        upgrade_seconds=time.monotonic()-started)
    m.study.new(ROOT/'DATA.json',data);m.study.new(ROOT/'PLAN.json',plan)


def semantic_prepare():
    """Keep the bank fixed; learn financial binding from full frozen vectors."""
    import torch
    from sentence_transformers import SentenceTransformer
    torch.set_num_threads(4);ROOT.mkdir();started=time.monotonic()
    previous=ROOT.parent/'role_repair_v2';data=m.read(previous/'DATA.json');plan=m.read(previous/'PLAN.json')
    encoder=SentenceTransformer(plan['encoder'],device='cpu',local_files_only=True);encoder.max_seq_length=256
    forwards=[0]
    hook=encoder.register_forward_hook(lambda *args:forwards.__setitem__(0,forwards[0]+1))
    for phase in ['train','dev']:
        for done,task in enumerate(data[phase],1):
            public=m.read(Path(task['folder'])/'inputs/public.json');evidence=chunks(public)
            vectors=encoder.encode([public['question']]+[item['text'] for item in evidence],batch_size=16,
                show_progress_bar=False,normalize_embeddings=True)
            q=vectors[0];rows=vectors[1:];semantic=[]
            for candidate in task['candidates']:
                old_values=[]
                for patch in candidate['patches']:
                    if patch['op']=='rebind_operand':
                        try:old_values.append(float(m.task.executor().parse_numeric_argument(patch['from'])))
                        except Exception:pass
                old_indices=[i for i,chunk in enumerate(evidence) if any(math.isclose(item['value'],old,rel_tol=1e-9,abs_tol=1e-9)
                    for item in chunk['items'] for old in old_values)]
                old=rows[max(old_indices,key=lambda i:float(q@rows[i]))] if old_indices else np.zeros(384,dtype=np.float32)
                new=rows[candidate['chunk']] if candidate['chunk'] is not None else np.zeros(384,dtype=np.float32)
                semantic.append(np.stack([q,new,old]).tolist())
            task['semantic_vectors']=semantic
            m.study.publish(ROOT/'PREPARE_LIVE.json',dict(status='RUNNING',phase=phase,completed=done,http_posts=0))
    hook.remove();plan.update(feature_version='Full question/new/old evidence vectors plus 71 structural features',
        bank_reused_from=str(previous),encoder_forwards=forwards[0] if forwards[0] else None,
        encoder_forward_count_note='Unobserved hook count stays unknown, never recorded as zero compute.',
        preparation_seconds=time.monotonic()-started)
    m.study.new(ROOT/'DATA.json',data);m.study.new(ROOT/'PLAN.json',plan)
    print(json.dumps(dict(prepared=True,seconds=plan['preparation_seconds'],encoder_forwards=plan['encoder_forwards'])),flush=True)


def run(use_existing_features=False,semantic=False):
    live=ROOT.parent/(ROOT.name.upper()+'_LIVE.json')
    state=dict(status='RUNNING',phase='PREPARE',pid=os.getpid(),start_ticks=Path('/proc/self/stat').read_text().split()[21]);m.study.publish(live,state)
    try:
        semantic_prepare() if semantic else (upgrade() if use_existing_features else prepare())
        state['phase']='TRAIN';m.study.publish(live,state)
        train();state['phase']='EVALUATE';m.study.publish(live,state)
        evaluate();state.update(status='RETURNED',phase='FINISHED')
    except BaseException:state.update(status='FAILED',error=traceback.format_exc())
    finally:m.study.publish(live,state)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('mode',choices=['prepare','train','evaluate','run','upgrade','semantic']);args=parser.parse_args()
    if args.mode=='upgrade':run(True)
    elif args.mode=='semantic':run(semantic=True)
    else:{'prepare':prepare,'train':train,'evaluate':evaluate,'run':run}[args.mode]()
