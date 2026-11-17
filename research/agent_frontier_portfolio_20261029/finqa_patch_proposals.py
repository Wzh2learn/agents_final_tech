"""Collect native before/after patch utility on existing TRAIN sources only."""
from pathlib import Path
import argparse,json,os,shutil,sys,time,traceback
import finqa_patch_learning as c

m=c.m


def neutral_schema(allow_keep=True):
    operations=['rebind_operand','scale_output','prepend_step']
    if allow_keep:operations.insert(0,'KEEP')
    return dict(type='object',properties=dict(
        diagnosis=dict(type='string',enum=['']),
        evidence=dict(type='array',items=dict(type='string'),maxItems=0),
        patches=dict(type='array',minItems=1,maxItems=8,items=dict(type='object',
            properties=dict(op=dict(enum=operations),
                **{'from':dict(type='string'),'to':dict(type='string'),
                   'positions':dict(type='array',items=dict(type='array',items=dict(type='integer'),minItems=2,maxItems=2)),
                   'step':dict(type='string'),'mode':dict(enum=['multiply','divide']),'factor':dict(type='number')}),
            required=['op'],additionalProperties=False))),
        required=['diagnosis','evidence','patches'],additionalProperties=False)


def format_proposal_request(value,profile,force_repair=False,rationale=False):
    """Shared training/inference shape: final JSON, no advertised tool schema."""
    value=dict(value);schema=neutral_schema(allow_keep=not force_repair)
    if profile['model_id']=='qwen38-27b-fp8' or rationale:
        schema['properties']['diagnosis']=dict(type='string',maxLength=180)
        schema['properties']['evidence']=dict(type='array',items=dict(type='string'),maxItems=3)
        value['response_format']=(dict(type='json_schema',json_schema=dict(name='bounded_patch',schema=schema))
            if profile['model_id']=='qwen38-27b-fp8' else dict(type='json_object',schema=schema))
        value['max_tokens']=1024
    else:value['response_format']=dict(type='json_object',schema=schema)
    value.pop('tools',None);value.pop('tool_choice',None)
    return value


def proposal_relay(folder,profile,helpers,force_repair=False,rationale=False,**kwargs):
    class ActorProxy:
        def __getattr__(self,name):return getattr(helpers.actor,name)
        def model_payload(self,*args,**options):
            value=helpers.actor.model_payload(*args,**options)
            # This installed server accepts json_object+schema. Its legacy
            # json_schema+schema form silently left the rationale unconstrained.
            return format_proposal_request(value,profile,force_repair,rationale)
    class HelpersProxy:
        actor=ActorProxy()
        def __getattr__(self,name):return getattr(helpers,name)
    return m.study.core.Relay(folder,profile,HelpersProxy(),**kwargs)


def prepare(root,backend,force_repair=False):
    events=m.read_lines(c.step1/'source_events.jsonl');prior=m.read(c.root/'PLAN.json')
    caps=dict(prior['caps'])
    if backend=='campus':caps['posts']=1
    episodes=[]
    for event in events:
        index=event['index'];source=Path(event['folder']);folder=root/'train'/f'{index:03d}'
        inputs=folder/'inputs';inputs.mkdir(parents=True,exist_ok=True)
        for name in ['work','dependencies']:shutil.copytree(source/name,folder/name,dirs_exist_ok=True)
        public=m.read(source/'inputs/public.json');snapshot=m.state_from_folder(source)
        for name,value in [('public.json',public),('initial_state.json',snapshot)]:
            (inputs/name).write_text(json.dumps(value,ensure_ascii=False))
        (inputs/'task.txt').write_text(c.prompt(public,snapshot))
        for name,text in [('finqa_correction.py',Path(m.task.__file__).read_text()),
                ('executor.py',Path(m.task.executor().__file__).read_text()),
                ('finqa_minimal_patches.py',Path(__file__).with_name('finqa_minimal_patches.py').read_text()),
                ('finqa_tool.py',c.TOOL),('guest.py',m.study.guest_source(terminal_program=True))]:
            (inputs/name).write_text(text)
        episodes.append(dict(index=index,id=public['id'],report=public['report'],
            folder=str(folder),source_folder=str(source)))
    m.study.new(root/'PLAN.json',dict(episodes=episodes,backend=backend,caps=caps,force_repair=force_repair,
        scope='Same fixed TRAIN sources, first32 then96 only if any recovery; no DEV or reserved64, no optimizer updates.'))
    return episodes,prior


def collect(backend,force_repair=False):
    if force_repair and backend!='8b':raise ValueError('forced proposal probe is declared only for the frozen 8B patch model')
    name='correction_value_forced_v1' if force_repair else ('correction_value_v1' if backend=='8b' else 'correction_value_27b_v1')
    root=c.root.parent/name
    root.mkdir(exist_ok=True)
    if any((root/'train').glob('*/STARTED.json')):
        raise RuntimeError('this collection already has actual episode attempts; do not duplicate it')
    episodes,prior=prepare(root,backend,force_repair)
    state=dict(status='RUNNING',pid=os.getpid(),start_ticks=Path('/proc/self/stat').read_text().split()[21],
        backend=backend,episodes=[],training_updates=0)
    m.study.publish(root/'LIVE.json',state);unloaded=False;process=log=None;started=time.monotonic()
    try:
        if backend=='8b':unloaded=c.stop27()
        with m.study.core.resource_lock():
            h=m.study.core.helpers();checked=h.deps.verify_projection(h.actor.RUNTIME_ROOT,h.actor.RUNTIME_SHA)
            m.study.CAPS.clear();m.study.CAPS.update(prior['caps'])
            if backend=='8b':
                (root/'model').mkdir()
                process,log=c.native.start_server(prior['runtime'],'model',c.root/'patch_policy/adapter.gguf',root)
                profile=m.study.MODEL
                def relay(folder,profile,helpers,**options):
                    return proposal_relay(folder,profile,helpers,force_repair=force_repair,**options)
            else:
                # Reuse the already-owned 27B service; do not start a second GPU model.
                import http.client
                profile=dict(host='127.0.0.1',port=8006,model_id='qwen38-27b-fp8',context=32768,output=8192)
                deadline=time.monotonic()+600
                while True:
                    try:
                        conn=http.client.HTTPConnection(profile['host'],profile['port'],timeout=3)
                        conn.request('GET','/health');response=conn.getresponse();response.read();conn.close()
                        if response.status==200:break
                    except OSError:pass
                    if time.monotonic()>deadline:raise RuntimeError('local27 service is not ready')
                    time.sleep(2)
                relay=proposal_relay
            for ep in episodes:
                value=m.study.episode(ep,h,checked,profile,
                    private_labels=c.step1/'TRAIN_LABELS_PRIVATE.json',relay_factory=relay)
                raw=m.read_lines(Path(ep['folder'])/'raw.jsonl')
                texts=[x['part'].get('text','') for x in raw if x.get('type')=='text' and x.get('part',{}).get('type')=='text']
                try:proposal=json.loads(texts[-1]) if texts else None
                except ValueError:proposal=None
                if backend=='8b' and not state['episodes'] and (not proposal or proposal.get('diagnosis')!='' or proposal.get('evidence')!=[]):
                    raise RuntimeError('neutral decoding did not reach the actual native episode')
                before=m.read(Path(ep['source_folder'])/'RESULT.json')
                row=dict(index=ep['index'],id=ep['id'],before_success=before['native_success'],
                    after_success=value['native_success'],utility=int(value['native_success'])-int(before['native_success']),
                    before_program=before['submitted_program'],after_program=value['submitted_program'],proposal=proposal,
                    posts=value['accounting']['actual_forwarded_posts'],tokens=value['accounting']['provider_total_tokens_known'],
                    unknown=len(value['accounting']['unknown_usage_requests']),seconds=value['actor']['seconds'])
                state['episodes'].append(row);m.study.publish(root/'LIVE.json',state)
                print(json.dumps({k:row[k] for k in ['index','before_success','after_success','utility','posts','tokens']}),flush=True)
                if len(state['episodes'])==32 and not any(x['utility']>0 for x in state['episodes']):
                    state['decision']='No recovery in TRAIN32; stop this proposer';break
            state['status']='RETURNED'
    except BaseException:state.update(status='FAILED',error=traceback.format_exc())
    finally:
        if process is not None:c.native.stop_server(process,log)
        if unloaded:state['restoration']=c.restore27()
        state['seconds']=time.monotonic()-started
        m.study.publish(root/'LIVE.json',state);m.study.new(root/'RESULT.json',state)
        print(json.dumps({k:v for k,v in state.items() if k!='episodes'}),flush=True)


def collect_campus(key):
    """Same-state, blind TRAIN utility; then one learned native DEV policy."""
    from scripts.graph.research_school_gateway import BatchBudget,SchoolBackend,BASE_URL,MODEL,REQUEST_TOKEN_CEILING
    import finqa_correction_router as router
    if not key:raise ValueError('campus credential required through stdin or environment')
    root=c.root.parent/'correction_value_campus_v2';root.mkdir()
    episodes,prior=prepare(root,'campus')
    profile=dict(provider='bupt_chat_v1',base_url=BASE_URL,model_id=MODEL,context=262144,output=8192)
    # One proposal per state. No correctness-triggered retry and no TRAIN answer
    # enters the model prompt. Existing OpenCode and native final patch execution.
    caps=dict(prior['caps'],posts=1)
    budget=BatchBudget(root/'budget',posts=160,tokens=4_000_000)
    class ProposalCore:
        def __getattr__(self,name):return getattr(m.study.core,name)
        def prepare_tool_contract(self,value):
            # Validate the installed OpenCode's source tool before removing it
            # from this deliberately final-only provider request.
            value,contract=m.study.core.prepare_tool_contract(value)
            value=dict(value);value.pop('tools',None);value.pop('tool_choice',None)
            value['response_format']=dict(type='json_object')
            contract=dict(contract,provider_tools_removed_for_final_only=True)
            return value,contract
    backend=SchoolBackend(key,budget,ProposalCore());backend.verify(profile)
    state=dict(status='RUNNING',phase='TRAIN',pid=os.getpid(),
        start_ticks=Path('/proc/self/stat').read_text().split()[21],episodes=[])
    m.study.publish(root/'LIVE.json',state);started=time.monotonic()
    def run_one(ep,h,checked,labels):
        value=m.study.episode(ep,h,checked,profile,private_labels=labels,relay_factory=backend.make_relay)
        before=m.read(Path(ep['source_folder'])/'RESULT.json')
        row=dict(index=ep['index'],id=ep['id'],before_success=before['native_success'],
            after_success=value['native_success'],success=value['native_success'],
            utility=int(value['native_success'])-int(before['native_success']),
            before_program=before['submitted_program'],after_program=value['submitted_program'],
            program=value['submitted_program'],posts=value['accounting']['actual_forwarded_posts'],
            tokens=value['accounting']['provider_total_tokens_known'],
            unknown=len(value['accounting']['unknown_usage_requests']),seconds=value['actor']['seconds'])
        print(json.dumps(dict(phase=state['phase'],**{k:row[k] for k in ['index','utility','posts','tokens','unknown']})),flush=True)
        return row
    def persist():
        state['physical_posts']=sum(row['state']!='not_sent' for row in budget.rows)
        state['known_tokens']=sum(row.get('usage',{}).get('total_tokens',0) for row in budget.rows)
        state['unknown_requests']=sum(row['state']=='unknown' for row in budget.rows)
        state['unknown_reserved_tokens']=state['unknown_requests']*REQUEST_TOKEN_CEILING
        state['seconds']=time.monotonic()-started;m.study.publish(root/'LIVE.json',state)
    try:
        with m.study.core.resource_lock():
            h=m.study.core.helpers();checked=h.deps.verify_projection(h.actor.RUNTIME_ROOT,h.actor.RUNTIME_SHA)
            m.study.CAPS.clear();m.study.CAPS.update(caps)
            for ep in episodes:
                row=run_one(ep,h,checked,c.step1/'TRAIN_LABELS_PRIVATE.json')
                state['episodes'].append(row);persist()
                if row['unknown'] or not row['posts']:
                    raise RuntimeError('stop the batch on unknown transport or absent request, inspect the raw receipt')
                if len(state['episodes'])==32 and not any(x['utility']>0 for x in state['episodes']):break
        state['status']='RETURNED';persist();m.study.new(root/'RESULT.json',dict(state))
        if not any(x['utility']>0 for x in state['episodes']):return
        # Fixed before-state features, reused without new encoder calls. Only
        # new TRAIN counterfactual outcomes supervise the new utility head.
        state.update(status='RUNNING',phase='TRAIN_ROUTER');persist()
        router.SOURCE=root;router.ROOT=root.parent/'correction_router_campus_v2';router.ROOT.mkdir()
        for name in ['FEATURES.npz','FEATURE_PLAN.json']:
            shutil.copyfile(root.parent/'correction_router_v1'/name,router.ROOT/name)
        router.train();decisions=m.read(router.ROOT/'PREDICTIONS.json')['decisions']
        sources=m.read(router.ROOT/'FEATURE_PLAN.json')['dev']
        labels_path=Path(sources[0]['folder']).parent.parent/'LABELS_PRIVATE.json';labels=m.read(labels_path)
        dev=[];state['phase']='DEV';state['dev_episodes']=dev;persist()
        with m.study.core.resource_lock():
            for source,decision in zip(sources,decisions,strict=True):
                assert (source['index'],source['id'])==(decision['index'],decision['id'])
                old=Path(source['folder']);folder=router.ROOT/'dev'/f"{source['index']:03d}"
                public=m.read(old/'inputs/public.json');snapshot=m.state_from_folder(old)
                before=m.read(old/'RESULT.json')['native_success']
                folder.mkdir(parents=True)
                if decision['decision']=='KEEP':
                    program=snapshot['current_program'];m.task.submit_program(program,public,folder,origin='campus_utility_KEEP')
                    success=m.task.grade(program,public,labels[source['index']]['exe_ans'])['execution_correct']
                    row=dict(index=source['index'],id=source['id'],before_success=before,success=success,
                        utility=int(success)-int(before),program=program,posts=0,tokens=0,unknown=0,seconds=0)
                else:
                    for name in ['work','dependencies']:shutil.copytree(old/name,folder/name)
                    inputs=folder/'inputs';inputs.mkdir()
                    for name,value in [('public.json',public),('initial_state.json',snapshot)]:
                        (inputs/name).write_text(json.dumps(value,ensure_ascii=False))
                    (inputs/'task.txt').write_text(c.prompt(public,snapshot))
                    for name,text in [('finqa_correction.py',Path(m.task.__file__).read_text()),
                        ('executor.py',Path(m.task.executor().__file__).read_text()),
                        ('finqa_minimal_patches.py',Path(__file__).with_name('finqa_minimal_patches.py').read_text()),
                        ('finqa_tool.py',c.TOOL),('guest.py',m.study.guest_source(terminal_program=True))]:
                        (inputs/name).write_text(text)
                    ep=dict(source,folder=str(folder),source_folder=str(old))
                    row=run_one(ep,h,checked,labels_path)
                row.update(decision=decision['decision'],score=decision['score']);dev.append(row);persist()
                if row['unknown']:raise RuntimeError('unknown DEV transport; do not retry silently')
        summary=dict(tasks=len(dev),before=sum(row['before_success'] for row in dev),success=sum(row['success'] for row in dev),
            recovered=sum(row['utility']>0 for row in dev),damaged=sum(row['utility']<0 for row in dev),
            posts=sum(row['posts'] for row in dev),tokens=sum(row['tokens'] for row in dev),
            unknown=sum(row['unknown'] for row in dev),actor_seconds=sum(row['seconds'] for row in dev),
            encoder_calls=0,encoder_reused=True,scope='Frozen TRAIN-only utility policy; same actual OpenCode first-pass states.')
        m.study.new(router.ROOT/'DEV_RESULT.json',dict(status='RETURNED',summary=summary,episodes=dev))
        state.update(status='RETURNED',phase='FINISHED',dev_summary=summary)
    except BaseException:state.update(status='FAILED',error=traceback.format_exc())
    finally:
        if budget.pending is not None:budget.finish()
        persist();budget.close();m.study.new(root/'PIPELINE_RESULT.json',state)
        print(json.dumps({k:v for k,v in state.items() if k not in ['episodes','dev_episodes']}),flush=True)


def bundle_credit(output=None):
    """Native TRAIN subset rewards, keeping prefix numbering unchanged."""
    import itertools
    from finqa_minimal_patches import apply_patches
    source=c.step1/'formation_v2';out=Path(output) if output else source/'bundle_credit_autopsy'
    out.mkdir();started=time.monotonic();labels=m.read(c.step1/'TRAIN_LABELS_PRIVATE.json')
    repairs=[row for row in m.read_lines(source/'COMBINED_PATCH_SAMPLES.jsonl') if row['phase']=='repair']
    rows=[];examples=[]
    for sample in repairs:
        public=sample['public'];state=sample['state'];label=labels[sample['source_index']]
        assert public['id']==label['id']
        patches=sample['target']['patches'];prefix=[i for i,p in enumerate(patches) if p['op']=='prepend_step']
        mutable=[i for i,p in enumerate(patches) if p['op']!='prepend_step']
        assert m.task.grade(apply_patches(state['current_program'],patches),public,label['exe_ans'])['execution_correct']
        before=m.task.grade(state['current_program'],public,label['exe_ans']);assert not before['execution_correct']
        outcomes=[]
        for flags in itertools.product([False,True],repeat=len(mutable)):
            chosen=set(prefix+[i for i,flag in zip(mutable,flags) if flag])
            subset=[patch for i,patch in enumerate(patches) if i in chosen] or [dict(op='KEEP')]
            try:
                program=apply_patches(state['current_program'],subset);grade=m.task.grade(program,public,label['exe_ans'])
                value=dict(selected_mutable=sum(flags),valid=grade['program_valid'],success=grade['execution_correct'],
                    patches=subset,program=program,execution=grade['public_execution'])
            except Exception as error:
                value=dict(selected_mutable=sum(flags),valid=False,success=False,patches=subset,error=str(error))
            outcomes.append(value)
            examples.append(dict(id=public['id'],source_index=sample['source_index'],public=public,state=state,
                proposal_patches=subset,proposed_program=value.get('program'),public_execution=value.get('execution'),
                native_utility=int(value['success']),valid=value['valid']))
        minimum=min(row['selected_mutable'] for row in outcomes if row['success'])
        rows.append(dict(index=sample['source_index'],id=public['id'],original_valid=before['program_valid'],
            prefix_operations=len(prefix),mutable_operations=len(mutable),minimum_mutable_for_success=minimum,
            counterfactuals=len(outcomes),executed_wrong=sum(row['valid'] and not row['success'] for row in outcomes),
            invalid=sum(not row['valid'] for row in outcomes),full_patch=patches,outcomes=outcomes))
    summary=dict(status='RETURNED',repairs=len(rows),original_valid=sum(row['original_valid'] for row in rows),
        counterfactuals=len(examples),pure_no_prefix=sum(row['prefix_operations']==0 for row in rows),
        joint_nonprefix_needed=sum(row['original_valid'] and row['minimum_mutable_for_success']>=2 for row in rows),
        pure_joint_needed=sum(row['original_valid'] and not row['prefix_operations'] and row['minimum_mutable_for_success']>=2 for row in rows),
        executed_wrong=sum(row['executed_wrong'] for row in rows),invalid=sum(row['invalid'] for row in rows),
        seconds=time.monotonic()-started,model_calls=0,
        scope='TRAIN subset outcomes; prefix steps remain together to avoid reference-index artifacts. Utility labels are not deployment inputs.')
    m.study.new(out/'RESULT.json',summary)
    for name,items in [('ROWS.jsonl',rows),('CREDIT_EXAMPLES_TRAIN.jsonl',examples)]:
        with (out/name).open('x') as file:
            for row in items:file.write(json.dumps(row,ensure_ascii=False)+'\n')
    print(json.dumps(summary),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();mode=parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--backend',choices=['8b','27b','campus']);mode.add_argument('--bundle-credit',action='store_true')
    parser.add_argument('--credit-output',type=Path);parser.add_argument('--force-repair',action='store_true');args=parser.parse_args()
    if args.force_repair and args.backend!='8b':parser.error('--force-repair requires --backend 8b')
    if args.bundle_credit:bundle_credit(args.credit_output)
    elif args.credit_output:parser.error('--credit-output requires --bundle-credit')
    elif args.backend=='campus':
        print('CREDENTIAL_INPUT_READY',flush=True)
        key=os.environ.get('BUPT_API_KEY')
        if not key:
            if sys.stdin.isatty():
                import getpass
                key=getpass.getpass('Campus credential (hidden): ')
            else:key=sys.stdin.readline().rstrip('\r\n')
        collect_campus(key)
    else:collect(args.backend,args.force_repair)
