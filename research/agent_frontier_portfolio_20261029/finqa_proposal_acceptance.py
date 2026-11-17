"""Learn repair proposals separately from native-feedback accept/KEEP utility."""
from pathlib import Path
import argparse,collections,copy,json,os,random,shutil,subprocess,sys,time,traceback
import numpy as np
import finqa_patch_learning as c
import finqa_correction_router as router
from finqa_minimal_patches import apply_patches,same_operand
from finqa_patch_proposals import proposal_relay,format_proposal_request

m=c.m
ROOT=c.root.parent/'proposal_acceptance_v1'
ORIGINAL_ROOT=c.root


def proposal_prompt(public,state):
    text=c.prompt(public,state)
    text=text.replace('Retain consistent calculations; a patch is not mandatory. ',
        'Mode PROPOSE: produce a concrete repair candidate. An independent acceptance module may retain the original. '
        'Do not decide KEEP here; use the three edit operators below. ')
    text=text.replace('{"op":"KEEP"} alone preserves the original; ','')
    text=text.replace('diagnosis (brief), evidence (short list of report anchors)',
        'diagnosis (at most 180 characters), evidence (at most three short report anchors)')
    text=text.replace('If useful, validate with /extra/bin/python /inputs/finqa_tool.py --patches followed by one quoted JSON list. ',
        'Return your final JSON directly; this proposal request does not call tools. ')
    return text


def final_proposal(folder):
    latest=None;parts={}
    for event in m.read_lines(folder/'raw.jsonl'):
        part=event.get('part',{})
        if not isinstance(part,dict) or not isinstance(part.get('messageID'),str):continue
        if part['messageID']!=latest:latest=part['messageID'];parts={}
        if event.get('type')=='text' and part.get('type')=='text':parts[part['id']]=part.get('text','')
    return json.loads('\n'.join(parts.values()).strip())


def description(patches):
    pieces=[]
    for patch in patches:
        if patch['op']=='rebind_operand':pieces.append('Bind '+patch['from']+' to '+patch['to']+' at '+str(patch.get('positions','matching uses')))
        elif patch['op']=='scale_output':pieces.append('Scale output: '+patch['mode']+' by '+str(patch['factor']))
        else:pieces.append('Prepend '+patch['step'])
    return '; '.join(pieces)[:180]


def residual(original,selected,full):
    """Scope remaining bindings to their original slots, avoiding alias cascades."""
    if any(p['op']=='prepend_step' for p in full):return None
    counts=collections.Counter(json.dumps(p,sort_keys=True) for p in selected if p['op']!='KEEP')
    steps=m.task.executor().parse_program(original);result=[]
    for patch in full:
        key=json.dumps(patch,sort_keys=True)
        if counts[key]:counts[key]-=1;continue
        patch=copy.deepcopy(patch)
        if patch['op']=='rebind_operand' and 'positions' not in patch:
            patch['positions']=[[i,slot] for i,step in enumerate(steps) for slot,token in enumerate((step.arg1,step.arg2),1)
                if same_operand(token,patch['from'],m.task.executor())]
        result.append(patch)
    return result or None


def prepare():
    ROOT.mkdir();started=time.monotonic()
    events=m.read_lines(c.step1/'source_events.jsonl');labels=m.read(c.step1/'TRAIN_LABELS_PRIVATE.json')
    sources={row['index']:row for row in events};repairs=collections.defaultdict(list)
    for row in m.read_lines(c.step1/'formation_v2/COMBINED_PATCH_SAMPLES.jsonl'):
        if row['phase']=='repair':repairs[row['source_index']].append(row)
    for name in ['correction_value_27b_v1','correction_value_campus_v2']:
        study=m.read(ROOT.parent/name/'RESULT.json');assert study['status']=='RETURNED'
        for row in study['episodes']:
            if row['utility']<=0:continue
            index=row['index'];folder=Path(sources[index]['folder']);public=m.read(folder/'inputs/public.json')
            state=m.state_from_folder(folder);target=final_proposal(ROOT.parent/name/'train'/f'{index:03d}')
            repairs[index].append(dict(id=row['id'],source_index=index,public=public,state=state,target=target,phase='blind_repair'))
    counterfactual={row['index']:row for row in m.read_lines(c.step1/'formation_v2/bundle_credit_autopsy/ROWS.jsonl')}
    examples=[];skipped=collections.Counter()
    for index,items in sorted(repairs.items()):
        base=items[0];public=base['public'];label=labels[index]
        assert public['id']==label['id']==base['id']
        candidates=list(items)
        if index in counterfactual and not counterfactual[index]['prefix_operations']:
            full=counterfactual[index]['full_patch'];wrong=[o for o in counterfactual[index]['outcomes'] if o['valid'] and not o['success']]
            wrong.sort(key=lambda o:(o['selected_mutable'],o['program']))
            for outcome in wrong:
                patch=residual(base['state']['current_program'],outcome['patches'],full)
                if not patch:continue
                state=dict(current_program=outcome['program'],execution_feedback=outcome['execution'])
                candidates.append(dict(base,state=state,target=dict(diagnosis=description(patch),evidence=[],patches=patch),phase='residual_repair'))
        retained={}
        for item in candidates:
            state=item['state'];target=item['target'];patch=target['patches']
            if any(p['op']=='KEEP' for p in patch):continue
            try:
                program=apply_patches(state['current_program'],patch)
                before=m.task.grade(state['current_program'],public,label['exe_ans'])
                after=m.task.grade(program,public,label['exe_ans'])
                if before['execution_correct'] or not after['execution_correct']:
                    skipped['not_actual_recovery']+=1;continue
            except Exception:skipped['invalid_residual']+=1;continue
            key=state['current_program']
            if key in retained:continue
            target=dict(diagnosis=str(target.get('diagnosis') or description(patch))[:180],
                evidence=[str(x)[:160] for x in (target.get('evidence') or [])[:3]],patches=patch)
            retained[key]=dict(item,target=target,native_before=False,native_after=True)
        # Preserve one actual failure and spread the remaining views over partial progress.
        views=list(retained.values());chosen=views[:1]
        remaining=views[1:]
        if remaining:
            positions=np.linspace(0,len(remaining)-1,min(3,len(remaining)),dtype=int)
            chosen += [remaining[int(i)] for i in positions]
        examples.extend(chosen)
    replay=m.read(c.replay/'DATA.json');prior=m.read(c.replay/'PLAN.json')
    tokenizer=m.tokens.load_tokenizer(m.learning.MODEL)
    template=m.read(c.step1/'formation/000/wire/00001.request.json')
    original=(c.step1/'formation/000/inputs/task.txt').read_text();grouped=collections.defaultdict(list)
    for example in examples:
        request=m.fresh_request(template,original,proposal_prompt(example['public'],example['state']))
        request=format_proposal_request(request,m.study.MODEL,force_repair=True,rationale=True)
        assert 'tools' not in request and 'tool_choice' not in request
        row=m.tokens.encode_completion(request,dict(role='assistant',content=json.dumps(example['target'],ensure_ascii=False)),
            tokenizer,16384,completion_kind='text')
        row.update(source_index=example['source_index'],phase=example['phase'])
        grouped[example['source_index']].append(row)
    anchors=[[replay['rows'][i] for i in group] for group in prior['paired_rows']]
    groups=list(grouped.values());schedule=[dict(kind='replay',index=i) for i in range(len(anchors))]
    schedule += [dict(kind='patch',index=i) for i in range(len(groups))]
    random.Random(17).shuffle(schedule);schedule*=3
    m.study.new(ROOT/'DATA.json',dict(anchor_groups=anchors,patch_groups=groups))
    with (ROOT/'PROPOSAL_EXAMPLES_TRAIN.jsonl').open('x') as file:
        for row in examples:file.write(json.dumps(row,ensure_ascii=False)+'\n')
    m.study.new(ROOT/'PLAN.json',dict(model=prior['model_path'],warm_start=str(c.replay/'aligned_sft'),seed=17,
        learning_rate=2e-4,epochs=3,schedule=schedule,wall_seconds=14400,
        replay_groups=len(anchors),patch_groups=len(groups),patch_targets=len(examples),
        phase_counts=dict(collections.Counter(row['phase'] for row in examples)),skipped=dict(skipped),
        runtime=m.read(c.step1/'PLAN.json')['runtime'],caps=dict(m.read(c.replay/'native_v1/PLAN.json')['caps'],posts=1),
        scope='TRAIN-only recovery proposals; no KEEP targets in proposal mode. Original Actor and 121 replay groups retained.',
        preparation_seconds=time.monotonic()-started))
    print(json.dumps(dict(groups=len(groups),targets=len(examples),updates=len(schedule))),flush=True)


def inputs(folder,source):
    public=m.read(source/'inputs/public.json');state=m.state_from_folder(source)
    target=folder/'inputs';target.mkdir(parents=True)
    for name in ['work','dependencies']:shutil.copytree(source/name,folder/name)
    for name,value in [('public.json',public),('initial_state.json',state)]:
        (target/name).write_text(json.dumps(value,ensure_ascii=False))
    (target/'task.txt').write_text(proposal_prompt(public,state))
    for name,text in [('finqa_correction.py',Path(m.task.__file__).read_text()),
        ('executor.py',Path(m.task.executor().__file__).read_text()),
        ('finqa_minimal_patches.py',Path(__file__).with_name('finqa_minimal_patches.py').read_text()),
        ('finqa_tool.py',c.TOOL),('guest.py',m.study.guest_source(terminal_program=True))]:
        (target/name).write_text(text)
    return public,state


def collect(phase,h,checked):
    sources=(m.read_lines(c.step1/'source_events.jsonl') if phase=='train'
        else m.read(c.replay/'native_v1/PLAN.json')['source_episodes'])
    labels_path=(c.step1/'TRAIN_LABELS_PRIVATE.json' if phase=='train'
        else Path(sources[0]['folder']).parent.parent/'LABELS_PRIVATE.json')
    rows=[]
    for source_ep in sources:
        source=Path(source_ep['folder']);folder=ROOT/phase/f"{source_ep['index']:03d}"
        public,state=inputs(folder,source)
        ep=dict(index=source_ep['index'],id=source_ep['id'],report=public['report'],folder=str(folder))
        def relay(folder,profile,helpers,**kwargs):
            return proposal_relay(folder,profile,helpers,force_repair=True,rationale=True,**kwargs)
        result=m.study.episode(ep,h,checked,m.study.MODEL,private_labels=labels_path,relay_factory=relay)
        before=m.read(source/'RESULT.json')['native_success']
        try:proposal=final_proposal(folder)
        except (ValueError,IndexError):proposal=None
        row=dict(index=ep['index'],id=ep['id'],report=ep['report'],folder=str(folder),source_folder=str(source),
            before_success=before,success=result['native_success'],utility=int(result['native_success'])-int(before),
            before_program=state['current_program'],program=result['submitted_program'],proposal=proposal,
            posts=result['accounting']['actual_forwarded_posts'],tokens=result['accounting']['provider_total_tokens_known'],
            unknown=len(result['accounting']['unknown_usage_requests']),seconds=result['actor']['seconds'])
        rows.append(row);m.study.publish(ROOT/('PROPOSAL_'+phase.upper()+'_LIVE.json'),dict(status='RUNNING',episodes=rows))
        print(json.dumps(dict(phase=phase,index=ep['index'],utility=row['utility'],tokens=row['tokens'])),flush=True)
    summary=dict(tasks=len(rows),before=sum(r['before_success'] for r in rows),success=sum(r['success'] for r in rows),
        recovered=sum(r['utility']>0 for r in rows),damaged=sum(r['utility']<0 for r in rows),
        posts=sum(r['posts'] for r in rows),tokens=sum(r['tokens'] for r in rows),unknown=sum(r['unknown'] for r in rows))
    m.study.new(ROOT/('PROPOSAL_'+phase.upper()+'_RESULT.json'),dict(status='RETURNED',summary=summary,episodes=rows))
    return rows


def case(public,before,after,report,utility,kind,index):
    return dict(public=public,before_program=before,program=after,report=report,
        utility=int(utility),kind=kind,index=index)


def acceptance_cases():
    """Actual on-policy examples plus executed, source-grouped counterfactuals."""
    onpolicy=m.read(ROOT/'PROPOSAL_TRAIN_RESULT.json')['episodes'];cases=[]
    for row in onpolicy:
        public=m.read(Path(row['folder'])/'inputs/public.json')
        cases.append(case(public,row['before_program'],row['program'],row['report'],row['utility'],'onpolicy',row['index']))
    examples={row['source_index']:row for row in m.read_lines(c.step1/'formation_v2/COMBINED_PATCH_SAMPLES.jsonl') if row['phase']=='repair'}
    for row in m.read_lines(c.step1/'formation_v2/bundle_credit_autopsy/ROWS.jsonl'):
        sample=examples[row['index']];public=sample['public'];old=sample['state']['current_program']
        correct=apply_patches(old,row['full_patch'])
        for outcome in row['outcomes']:
            if not outcome['valid']:continue
            cases.append(case(public,old,outcome['program'],public['report'],int(outcome['success']),'subset',row['index']))
            if not outcome['success']:
                cases.append(case(public,outcome['program'],correct,public['report'],1,'remaining_repair',row['index']))
                cases.append(case(public,correct,outcome['program'],public['report'],-1,'harmful_reversal',row['index']))
    return cases,len(onpolicy)


def encode_cases(encoder,cases):
    """Projection ignores native labels and source kind; public paired programs only."""
    texts=[];numeric=[]
    for row in cases:
        public=row['public'];states=[dict(current_program=row[key],execution_feedback=m.task.execute_public(row[key],public))
            for key in ['before_program','program']]
        features=[router.public_features(public,state) for state in states]
        texts.extend([features[0][0],features[1][0],features[0][1],features[1][1]])
        a,b=features[0][2],features[1][2]
        numeric.append(np.concatenate([a,b-a,[len(row['program'] or '')/1000-len(row['before_program'] or '')/1000]]))
    vectors=encoder.encode(texts,batch_size=16,show_progress_bar=False,normalize_embeddings=True).reshape(len(cases),4,-1)
    b,a,be,ae=[vectors[:,i] for i in range(4)]
    return np.concatenate([b,a,a-b,b*a,be,ae-be,np.asarray(numeric)],axis=1).astype(np.float32)


def fit_critic(x,y,groups,seed):
    import torch
    torch.manual_seed(seed);mean=x.mean(0);scale=np.maximum(x.std(0),.01)
    inputs=torch.tensor((x-mean)/scale,dtype=torch.float32);labels=torch.tensor(y)
    counts=collections.Counter(groups);weights=torch.tensor([1/counts[g] for g in groups],dtype=torch.float32)
    model=torch.nn.Sequential(torch.nn.Linear(x.shape[1],32),torch.nn.ReLU(),torch.nn.Dropout(.1),torch.nn.Linear(32,3))
    optimizer=torch.optim.AdamW(model.parameters(),lr=.003,weight_decay=.01)
    for _ in range(200):
        optimizer.zero_grad();loss=torch.nn.functional.cross_entropy(model(inputs),labels,reduction='none')
        value=(loss*weights).sum()/weights.sum();value.backward();optimizer.step()
    model.eval();return dict(weights=model.state_dict(),mean=mean,scale=scale,input_size=x.shape[1]),model


def load_encoder():
    from sentence_transformers import SentenceTransformer
    plan=m.read(ROOT.parent/'correction_router_v1/FEATURE_PLAN.json')
    model=SentenceTransformer(plan['encoder'],device='cpu',local_files_only=True);model.max_seq_length=384
    return model


def fit_acceptance():
    import torch
    from sklearn.model_selection import GroupKFold
    torch.set_num_threads(4);started=time.monotonic();cases,n=acceptance_cases();encoder=load_encoder()
    forwards=[0];original=encoder[0].auto_model.forward
    def counted(*args,**kwargs):forwards[0]+=1;return original(*args,**kwargs)
    encoder[0].auto_model.forward=counted;x=encode_cases(encoder,cases);encoder[0].auto_model.forward=original
    utility=np.asarray([row['utility'] for row in cases]);y=np.where(utility==1,1,np.where(utility==-1,2,0))
    groups=np.asarray(['/'.join(row['report'].split('/')[:2]) for row in cases]);oof=np.zeros((n,3),dtype=np.float32)
    # All views of one filing stay on one side; threshold uses ACTUAL proposer
    # outcomes only, not the augmentation distribution's artificial label mix.
    for fold,(a,b) in enumerate(GroupKFold(4).split(x,y,groups)):
        saved,model=fit_critic(x[a],y[a],groups[a],17+fold);validation=b[b<n]
        if len(validation):oof[validation]=router.probability(saved,model,x[validation])
    gains=oof[:,1]-oof[:,2];choices=[]
    for threshold in [-1.01,0,.01,.05,.1,.2,.3,.5,1.01]:
        use=gains>threshold;choices.append(dict(threshold=threshold,accepted=int(use.sum()),utility=int(utility[:n][use].sum())))
    selected=max(choices,key=lambda row:(row['utility'],-row['accepted'],row['threshold']))
    saved,model=fit_critic(x,y,groups,21);torch.save(saved,ROOT/'ACCEPTANCE.pt')
    m.study.new(ROOT/'ACCEPTANCE_TRAIN.json',dict(cases=len(cases),actual_proposals=n,source_groups=len(set(groups)),
        kinds=dict(collections.Counter(row['kind'] for row in cases)),thresholds=choices,selected=selected,
        optimizer_updates=1000,encoder_forwards=forwards[0],seconds=time.monotonic()-started,
        scope='Source-grouped native counterfactual utility, calibration only on held-out on-policy TRAIN proposals.'))
    print(json.dumps(dict(acceptance=selected,cases=len(cases))),flush=True)


def calibrate_with_fixed_baselines():
    """TRAIN-only correction for an older running controller's omitted option."""
    result=m.read(ROOT/'ACCEPTANCE_TRAIN.json')
    if any(row['threshold']==-1.01 for row in result['thresholds']):return
    proposals=m.read(ROOT/'PROPOSAL_TRAIN_RESULT.json')['episodes']
    baseline=dict(threshold=-1.01,accepted=len(proposals),utility=sum(row['utility'] for row in proposals))
    result['initial_selected_without_accept_all']=result['selected']
    result['thresholds'].insert(0,baseline)
    result['selected']=max(result['thresholds'],key=lambda row:(row['utility'],-row['accepted'],row['threshold']))
    result['fixed_baseline_calibration']='Added always-accept using TRAIN outcomes only; no policy weights or DEV outcomes used.'
    m.study.publish(ROOT/'ACCEPTANCE_TRAIN.json',result)
    print(json.dumps(dict(calibrated=result['selected'])),flush=True)


def evaluate_acceptance(rows):
    import torch
    started=time.monotonic();saved=torch.load(ROOT/'ACCEPTANCE.pt',map_location='cpu',weights_only=False)
    model=torch.nn.Sequential(torch.nn.Linear(saved['input_size'],32),torch.nn.ReLU(),torch.nn.Dropout(.1),torch.nn.Linear(32,3))
    model.load_state_dict(saved['weights']);model.eval();threshold=m.read(ROOT/'ACCEPTANCE_TRAIN.json')['selected']['threshold']
    public_cases=[dict(public=m.read(Path(row['folder'])/'inputs/public.json'),before_program=row['before_program'],program=row['program']) for row in rows]
    encoder=load_encoder();x=encode_cases(encoder,public_cases);p=router.probability(saved,model,x);gain=p[:,1]-p[:,2]
    decisions=[dict(index=row['index'],id=row['id'],score=float(score),accept=bool(score>threshold)) for row,score in zip(rows,gain,strict=True)]
    m.study.new(ROOT/'ACCEPTANCE_PREDICTIONS.json',dict(threshold=threshold,decisions=decisions))
    sources=m.read(c.replay/'native_v1/PLAN.json')['source_episodes'];labels=m.read(Path(sources[0]['folder']).parent.parent/'LABELS_PRIVATE.json')
    final=[]
    for row,decision,public in zip(rows,decisions,public_cases,strict=True):
        program=row['program'] if decision['accept'] else row['before_program'];folder=ROOT/'final'/f"{row['index']:03d}";folder.mkdir(parents=True)
        m.task.submit_program(program,public['public'],folder,origin='learned_proposal_acceptance')
        success=m.task.grade(program,public['public'],labels[row['index']]['exe_ans'])['execution_correct']
        final.append(dict(index=row['index'],id=row['id'],before_success=row['before_success'],success=success,
            utility=int(success)-int(row['before_success']),accept=decision['accept'],score=decision['score'],program=program))
    summary=dict(tasks=len(final),before=sum(r['before_success'] for r in final),success=sum(r['success'] for r in final),
        recovered=sum(r['utility']>0 for r in final),damaged=sum(r['utility']<0 for r in final),
        accepted=sum(r['accept'] for r in final),posts=sum(r['posts'] for r in rows),tokens=sum(r['tokens'] for r in rows),
        unknown=sum(r['unknown'] for r in rows),actor_seconds=sum(r['seconds'] for r in rows),acceptance_seconds=time.monotonic()-started)
    m.study.new(ROOT/'DEV_FINAL_RESULT.json',dict(status='RETURNED',summary=summary,episodes=final));print(json.dumps(summary),flush=True)


def run():
    if not (ROOT/'PLAN.json').exists():prepare()
    if (ROOT/'RUN_LIVE.json').exists():raise RuntimeError('inspect the existing attempt instead of restarting')
    state=dict(status='RUNNING',phase='TRAIN',pid=os.getpid(),start_ticks=Path('/proc/self/stat').read_text().split()[21])
    m.study.publish(ROOT/'RUN_LIVE.json',state);unloaded=c.stop27();process=log=trained=None
    try:
        with (ROOT/'training.log').open('x') as output:
            trained=subprocess.Popen([str(c.repo/'venv/bin/python'),'-u','-B',__file__,'train'],cwd=c.repo,stdout=output,stderr=subprocess.STDOUT)
            state['training_pid']=trained.pid;m.study.publish(ROOT/'RUN_LIVE.json',state)
            returncode=trained.wait(timeout=15000)
        if returncode:raise RuntimeError('proposal training failed; inspect TRAIN_RESULT and training.log')
        plan=m.read(ROOT/'PLAN.json');runtime=plan['runtime'];target=ROOT/'patch_policy/adapter.gguf'
        env=dict(os.environ,CUDA_VISIBLE_DEVICES='',HF_HUB_OFFLINE='1',PYTHONDONTWRITEBYTECODE='1',
            PYTHONPATH=str(Path(runtime['converter']).parent/'gguf-py')+':'+str(Path(runtime['converter']).parent))
        converted=subprocess.run([str(c.repo/'venv/bin/python'),'-B',runtime['converter'],'--outtype','f32',
            '--base',runtime['base_config'],'--outfile',str(target),str(ROOT/'patch_policy')],capture_output=True,env=env,timeout=180)
        (ROOT/'conversion.stdout').write_bytes(converted.stdout);(ROOT/'conversion.stderr').write_bytes(converted.stderr)
        if converted.returncode:raise RuntimeError('adapter conversion failed')
        with m.study.core.resource_lock():
            h=m.study.core.helpers();checked=h.deps.verify_projection(h.actor.RUNTIME_ROOT,h.actor.RUNTIME_SHA)
            m.study.CAPS.clear();m.study.CAPS.update(plan['caps'])
            (ROOT/'proposal_model').mkdir(exist_ok=True)
            process,log=c.native.start_server(runtime,'proposal_model',target,ROOT)
            state['phase']='PROPOSE_TRAIN';m.study.publish(ROOT/'RUN_LIVE.json',state)
            collect('train',h,checked)
            state['phase']='ACCEPTANCE_AND_DEV';m.study.publish(ROOT/'RUN_LIVE.json',state)
            fit_acceptance()
            dev=collect('dev',h,checked);evaluate_acceptance(dev)
        state.update(status='RETURNED',phase='FINISHED')
    except BaseException:state.update(status='FAILED',error=traceback.format_exc())
    finally:
        if trained is not None and trained.poll() is None:
            trained.terminate()
            try:trained.wait(timeout=30)
            except subprocess.TimeoutExpired:trained.kill();trained.wait()
        if process is not None:c.native.stop_server(process,log)
        if unloaded:state['restoration']=c.restore27()
        m.study.publish(ROOT/'RUN_LIVE.json',state);m.study.new(ROOT/'RUN_RESULT.json',state)
        print(json.dumps(state),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('mode',choices=['prepare','train','run','calibrate']);args=parser.parse_args()
    if args.mode=='prepare':prepare()
    elif args.mode=='train':c.root=ROOT;c.train()
    elif args.mode=='calibrate':calibrate_with_fixed_baselines()
    else:run()
