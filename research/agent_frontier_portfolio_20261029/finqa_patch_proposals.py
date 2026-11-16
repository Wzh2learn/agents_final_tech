"""Collect native before/after patch utility on existing TRAIN sources only."""
from pathlib import Path
import argparse,json,os,shutil,time,traceback
import finqa_patch_learning as c

m=c.m


def neutral_schema():
    return dict(type='object',properties=dict(
        diagnosis=dict(type='string',enum=['']),
        evidence=dict(type='array',items=dict(type='string'),maxItems=0),
        patches=dict(type='array',minItems=1,maxItems=8,items=dict(type='object',
            properties=dict(op=dict(enum=['KEEP','rebind_operand','scale_output','prepend_step']),
                **{'from':dict(type='string'),'to':dict(type='string'),
                   'positions':dict(type='array',items=dict(type='array',items=dict(type='integer'),minItems=2,maxItems=2)),
                   'step':dict(type='string'),'mode':dict(enum=['multiply','divide']),'factor':dict(type='number')}),
            required=['op'],additionalProperties=False))),
        required=['diagnosis','evidence','patches'],additionalProperties=False)


def proposal_relay(folder,profile,helpers,**kwargs):
    class ActorProxy:
        def __getattr__(self,name):return getattr(helpers.actor,name)
        def model_payload(self,*args,**options):
            value=helpers.actor.model_payload(*args,**options)
            # This installed server accepts json_object+schema. Its legacy
            # json_schema+schema form silently left the rationale unconstrained.
            schema=neutral_schema()
            if profile['model_id']=='qwen38-27b-fp8':
                schema['properties']['diagnosis']=dict(type='string',maxLength=180)
                schema['properties']['evidence']=dict(type='array',items=dict(type='string'),maxItems=3)
                value['response_format']=dict(type='json_schema',json_schema=dict(name='bounded_patch',schema=schema))
                value['max_tokens']=1024
            else:value['response_format']=dict(type='json_object',schema=schema)
            value.pop('tools',None);value.pop('tool_choice',None)
            return value
    class HelpersProxy:
        actor=ActorProxy()
        def __getattr__(self,name):return getattr(helpers,name)
    return m.study.core.Relay(folder,profile,HelpersProxy(),**kwargs)


def prepare(root,backend):
    events=m.read_lines(c.step1/'source_events.jsonl');prior=m.read(c.root/'PLAN.json')
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
    m.study.new(root/'PLAN.json',dict(episodes=episodes,backend=backend,caps=prior['caps'],
        scope='Same fixed TRAIN sources, first32 then96 only if any recovery; no DEV or reserved64, no optimizer updates.'))
    return episodes,prior


def collect(backend):
    root=c.root.parent/('correction_value_v1' if backend=='8b' else 'correction_value_27b_v1')
    root.mkdir(exist_ok=True)
    if any((root/'train').glob('*/STARTED.json')):
        raise RuntimeError('this collection already has actual episode attempts; do not duplicate it')
    episodes,prior=prepare(root,backend)
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
                profile=m.study.MODEL;relay=proposal_relay
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


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--backend',choices=['8b','27b'],required=True)
    collect(parser.parse_args().backend)
