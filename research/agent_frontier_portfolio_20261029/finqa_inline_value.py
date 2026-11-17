"""One-pass correction and teacher-value readout; reuse the existing native actor."""
from pathlib import Path
from types import SimpleNamespace
import argparse, collections, copy, hashlib, http.client, json, math, os, re, shutil, subprocess, time, traceback

import finqa_acquisition_learning as acquisition

c=acquisition.c
m=c.m
BASE=acquisition.ROOT.parent
ROOT=BASE/'inline_acquisition_v2'
MARKER='Escalation outcome: '


def prompt(public,initial):
    return (m.review_prompt(public,initial,terminal_program=True)+
        '\nAfter the Final program line, add exactly one line: Escalation outcome: A or B or N. '
        'Judge the value of asking a fixed teacher to review the ORIGINAL snapshot, relative to your final program. '
        'The controller keeps your program if the teacher fails, or if only a trailing factor100 conversion differs; '
        'otherwise it uses the teacher program. B means repair of your wrong answer; A means damage to your correct answer; '
        'N means unchanged correctness, including both wrong. The observed execution value is not a correctness label. '
        'Do not call another model to make this judgment.')


def encode_value(request,program,label,tokenizer):
    # Wrong intermediate programs are context, never positive generation targets.
    program=program if isinstance(program,str) else 'NONE'
    assistant=dict(role='assistant',content='Final program: '+program+'\n'+MARKER+label)
    row=m.tokens.encode_completion(request,assistant,tokenizer,16384,completion_kind='text')
    rendered=tokenizer.apply_chat_template(request['messages']+[assistant],tools=request.get('tools'),
        enable_thinking=False,tokenize=False,add_generation_prompt=False)
    mapped=tokenizer(rendered,add_special_tokens=False,return_offsets_mapping=True)
    assert mapped['input_ids']==row['input_ids']
    boundary=rendered.rindex(MARKER+label)
    for i,(_,end) in enumerate(mapped['offset_mapping']):
        if end<=boundary and i!=row['assistant_end_index']:row['labels'][i]=-100
    active=[i for i,x in enumerate(row['labels']) if x!=-100]
    assert active and min(active)>=row['prompt_token_count']
    assert MARKER.strip() in tokenizer.decode([row['input_ids'][i] for i in active])
    row['native_generation_prompt_tokens']=row['prompt_token_count']
    row['native_generation_prefix_sha256']=row.pop('rendered_prefix_sha256')
    row['prompt_token_count']=min(active)  # The masked program is prefix context.
    row['supervised_tokens']=len(active)
    row['loss_scope']='Only inline outcome suffix and EOS; declared program tokens masked'
    m.learning.completion_logit_window(row)
    return row


def prepare():
    if ROOT.exists():raise RuntimeError('inspect existing inline attempt before resuming')
    prior=m.read(acquisition.ROOT/'PLAN.json');data=m.read(acquisition.ROOT/'DATA.json')
    views=m.read(acquisition.ROOT/'TRAIN_VIEWS.json')['views']
    sources={r['index']:r for r in m.read(acquisition.router.RELATIVE_ROOT/'CHEAP_PLAN.json')['episodes']}
    tokenizer=m.tokens.load_tokenizer(m.learning.MODEL)
    template=m.read(c.step1/'formation/000/wire/00001.request.json')
    before=(c.step1/'formation/000/inputs/task.txt').read_text()
    groups=collections.defaultdict(list)
    for view in views:
        index=view['index'];source=Path(sources[index]['source_folder'])
        public=m.read(source/'inputs/public.json');assert public['id']==view['id']
        request=m.fresh_request(template,before,prompt(public,m.state_from_folder(source)))
        row=encode_value(request,view['program'],view['target'],tokenizer)
        row.update(source_index=index,view_kind=view['kind']);groups[index].append(row)
    assert sorted(groups)==list(range(96)) and len(views)==252 and len(data['anchor_groups'])==121
    prior.update(adapter_folder='inline_policy',runtime=m.read(c.step1/'PLAN.json')['runtime'],
        caps=m.read(c.replay/'native_v1/PLAN.json')['caps'],
        hypothesis='Emit correction and acquisition-value suffix in one native response, eliminating the separate full-context classifier forward.',
        target_scope='Same96 teacher sources/252 executed program views,121 replay groups195 targets. No153 expansion, DEV or reserved64 targets.',
        information='Value suffix sees original real feedback and generated program, not a newly executed final-program value unless actor used a tool.',
        teacher_budgets=[8,12,18],primary_teacher_budget=18,
        readout='A/B/N top20 token probabilities at final suffix, renormalized over observed classes; absent class mass zero and coverage reported. Missing suffix score=-infinity.',
        stop='One candidate only. Retain if native quality/cost supports further work; no loss/threshold sweep.',
        literature='GenGate supplies action-token gating precedent; use relative teacher utility, not a claim of inventing generation-time gating.')
    ROOT.mkdir();m.study.new(ROOT/'DATA.json',dict(anchor_groups=data['anchor_groups'],patch_groups=[groups[i] for i in range(96)]))
    m.study.new(ROOT/'PLAN.json',prior)
    print(json.dumps(dict(prepared=True,sources=96,views=len(views),updates=len(prior['schedule']),
        program_tokens_supervised_in_value_rows=0,replay_groups=121)),flush=True)


def prepare_dev(sources=None,use_inline=True):
    if sources is None:
        sources=m.read(c.replay/'native_v1/PLAN.json')['source_episodes'];assert len(sources)==64
    labels=m.read(Path(sources[0]['folder']).parent.parent/'LABELS_PRIVATE.json')
    m.study.new(ROOT/'DEV_LABELS_PRIVATE.json',labels)
    template=Path(m.read(acquisition.router.RELATIVE_ROOT/'CHEAP_PLAN.json')['reference_template'])
    episodes=[]
    for ep in sources:
        source=Path(ep['folder']);folder=ROOT/'dev'/f"{ep['index']:03d}";inputs=folder/'inputs';inputs.mkdir(parents=True)
        for name in ['work','dependencies']:shutil.copytree(source/name,folder/name)
        for name in ['finqa_tool.py','executor.py']:shutil.copyfile(template/name,inputs/name)
        public=m.read(source/'inputs/public.json')
        (inputs/'public.json').write_text(json.dumps(public,ensure_ascii=False))
        initial=m.state_from_folder(source)
        (inputs/'task.txt').write_text(prompt(public,initial) if use_inline else m.review_prompt(public,initial,terminal_program=True))
        (inputs/'guest.py').write_text(m.study.guest_source(terminal_program=True))
        episodes.append(dict(index=ep['index'],id=ep['id'],report=ep['report'],folder=str(folder)))
    m.study.new(ROOT/'DEV_PLAN.json',dict(episodes=episodes,source='Same original64 development firstpass workspaces, no confirmation64'))


def gate_score(folder,submitted):
    found=None
    for path in sorted((Path(folder)/'wire').glob('*.response')):
        parts=[]
        for line in path.read_bytes().splitlines():
            if not line.startswith(b'data:'):continue
            try:item=json.loads(line[5:].strip())
            except (ValueError,UnicodeError):continue
            for choice in item.get('choices',[]):
                parts.extend((choice.get('logprobs') or {}).get('content') or [])
        text=''.join(part.get('token','') for part in parts)
        matches=list(re.finditer(r'(?:^|\n)Escalation outcome:\s*([ABN])(?:\s|$)',text))
        declarations=re.findall(r'(?:^|\n)Final program:\s*([^\n]+)',text)
        if not matches or not declarations or declarations[-1].strip()!=submitted:continue
        position=matches[-1].start(1);offset=0
        for part in parts:
            end=offset+len(part.get('token',''))
            if offset<=position<end:
                probability={label:0. for label in 'ABN'}
                for option in part.get('top_logprobs') or []:
                    token=option['token'].strip()
                    if token in probability:probability[token]+=math.exp(option['logprob'])
                mass=sum(probability.values())
                if mass:
                    found=dict(score=(probability['B']-probability['A'])/mass,probabilities={k:v/mass for k,v in probability.items()},
                        observed_classes=sum(v>0 for v in probability.values()),declared=matches[-1][1],wire=path.name)
                break
            offset=end
    return found or dict(score=None,observed_classes=0,declared=None,reason='missing aligned native outcome probabilities')


def program_confidence(folder,program):
    """Read probabilities on the declared program, excluding prose and gate tokens."""
    found=None
    atoms=re.compile(r'(?P<operator>[A-Za-z_]\w*)\s*\(|(?P<reference>#\d+)|'
        r'(?P<operand>const_[A-Za-z0-9_.]+|(?<![\w.])[+-]?(?:\d+(?:\.\d+)?|\.\d+))')
    for path in sorted((Path(folder)/'wire').glob('*.response')):
        parts=[]
        for line in path.read_bytes().splitlines():
            if not line.startswith(b'data:'):continue
            try:item=json.loads(line[5:].strip())
            except (ValueError,UnicodeError):continue
            for choice in item.get('choices',[]):
                parts.extend((choice.get('logprobs') or {}).get('content') or [])
        text=''.join(part.get('token','') for part in parts)
        for match in re.finditer(r'(?:^|\n)Final program:[ \t]*([^\n]+)',text):
            declared=match[1].strip()
            if declared!=program:continue
            start=match.start(1)+len(match[1])-len(match[1].lstrip())
            spans=[];offset=0
            for part in parts:
                token=part.get('token','');end=offset+len(token)
                if end>offset and part.get('logprob') is not None:
                    spans.append((offset,end,-float(part['logprob'])))
                offset=end
            def surprise(a,b):
                total=weight=0.
                for left,right,nll in spans:
                    overlap=max(0,min(b,right)-max(a,left))/(right-left)
                    total+=overlap*nll;weight+=overlap
                return total/weight if weight else None
            values=[]
            for atom in atoms.finditer(program):
                category=atom.lastgroup
                # Do not include the opening parenthesis in an operator's score.
                a,b=atom.span(category);value=surprise(start+a,start+b)
                if value is not None:values.append(dict(kind=category,text=atom[category],nll=value))
            found=dict(program_mean=surprise(start,start+len(program)),
                semantic_max=max((row['nll'] for row in values),default=None),atoms=values,
                wire=path.name,scope='Actual declared-program tokens only; no labels or gate probabilities')
    return found or dict(program_mean=None,semantic_max=None,atoms=[],reason='No aligned program probabilities')


def confidence_probe():
    """Zero-model comparison on existing DEV outputs; never read confirmation64."""
    native=ROOT/'native_nonstream_v1';target=ROOT/'confidence_probe_v1';target.mkdir()
    dev=m.read(native/'DEV_RESULT.json');sources=m.read(native/'DEV_PLAN.json')['episodes']
    assert dev['status']=='RETURNED' and len(dev['episodes'])==len(sources)==64
    features=[]
    for row,source in zip(dev['episodes'],sources,strict=True):
        assert row['id']==source['id']
        public=m.read(Path(source['folder'])/'inputs/public.json')
        execution=m.task.execute_public(row['program'],public)
        features.append(dict(index=row['index'],id=row['id'],
            valid=execution['status']=='executed',**program_confidence(source['folder'],row['program'])))
    # Primary and baseline rules are fixed before any teacher outcomes or labels.
    orders={key:[r['index'] for r in sorted(features,key=lambda r:
        (r['valid'],r[key] is not None,-r[key] if r[key] is not None else 0,r['index']))]
        for key in ['semantic_max','program_mean']}
    m.study.new(target/'POLICIES.json',dict(primary='semantic_max',baseline='program_mean',
        orders=orders,budgets=[8,12,18],features=features,
        definition='Higher mean token surprisal indicates risk. Primary uses the worst numeric/operator/reference atom. Invalid programs and missing probabilities are selected first; ties use input index.',
        scope='Post-hoc DEV diagnostic, fixed actor outputs and fixed teacher pool. No new model requests or tuning on confirmation64.'))
    labels=m.read(native/'DEV_LABELS_PRIVATE.json')
    legacy=m.read(BASE/'deepseek_development_reference_v1/RESULT.json')['episodes'];outcomes=[]
    for row,source,label in zip(dev['episodes'],sources,labels,strict=True):
        i=row['index'];teacher=legacy[i]
        for name in ['acquisition_value_v1','acquisition_risk_control_v1','acquisition_single_state_v1']:
            path=BASE/name/'teacher_dev'/f'{i:03d}'/'RESULT.json'
            if path.exists():teacher=m.read(path);break
        assert row['id']==source['id']==label['id']==teacher['id']
        public=m.read(Path(source['folder'])/'inputs/public.json')
        program,keep=acquisition.guarded_program(row['program'],teacher['submitted_program'],public,teacher['agent_completed'])
        normal=row['normal'] if keep else teacher['agent_completed']
        correct=bool(m.task.grade(program,public,label['exe_ans'])['execution_correct'] and normal)
        outcomes.append(dict(index=i,program=program,success=correct,utility=int(correct)-int(row['success']),
            posts=teacher['accounting']['actual_forwarded_posts'],tokens=teacher['accounting']['provider_total_tokens_known']))
    table={}
    for key,order in orders.items():
        table[key]={}
        for k in [8,12,18]:
            chosen=set(order[:k]);selected=[row for row in outcomes if row['index'] in chosen]
            final=[outcome['success'] if row['index'] in chosen else row['success']
                for row,outcome in zip(dev['episodes'],outcomes,strict=True)]
            table[key][str(k)]=dict(success=sum(final),recovered=sum(r['utility']>0 for r in selected),
                damaged=sum(r['utility']<0 for r in selected),selected=order[:k],
                teacher_posts=sum(r['posts'] for r in selected),teacher_tokens=sum(r['tokens'] for r in selected))
    result=dict(status='RETURNED',native_baseline=sum(r['success'] for r in dev['episodes']),
        tasks=64,coverage=sum(r['program_mean'] is not None for r in features),
        primary='semantic_max',budgets=table,new_model_posts=0,new_training_updates=0,
        cpu_teacher_outcomes=outcomes,
        scope='Offline policy replay on actual fixed native programs and teacher completions, not new OpenCode episodes. Existing generation and teacher costs remain charged at their original executions.')
    m.study.new(target/'RESULT.json',result)
    print(json.dumps({k:v for k,v in result.items() if k!='cpu_teacher_outcomes'}),flush=True)


def nonstream_response(client,upstream,response_path):
    """Retain actual JSON/usage, and expose the same message as SSE to OpenCode."""
    upstream.settimeout(900)  # The caller bounds this by the episode deadline.
    response=http.client.HTTPResponse(upstream);response.begin()
    try:raw=response.read(32*1024**2+1);status=response.status
    finally:response.close()
    path=Path(response_path);path.with_name(path.name+'.upstream.json').write_bytes(raw)
    if len(raw)>32*1024**2:raise RuntimeError('nonstream response exceeds native wire bound')
    obj=json.loads(raw);usage=obj.get('usage');events=[]
    if status==200:
        for choice in obj['choices']:
            delta=dict(choice['message'])
            if delta.get('tool_calls'):
                delta['tool_calls']=[dict(call,index=i) for i,call in enumerate(delta['tool_calls'])]
            events.append(dict(id=obj.get('id'),object='chat.completion.chunk',model=obj.get('model'),
                choices=[dict(index=choice.get('index',0),delta=delta,logprobs=choice.get('logprobs'),finish_reason=None)]))
            events.append(dict(id=obj.get('id'),object='chat.completion.chunk',model=obj.get('model'),
                choices=[dict(index=choice.get('index',0),delta={},finish_reason=choice['finish_reason'])]))
        events.append(dict(choices=[],usage=usage))
        body=b''.join(b'data: '+json.dumps(event,ensure_ascii=False).encode()+b'\n\n' for event in events)+b'data: [DONE]\n\n'
        content_type='text/event-stream'
    else:body=raw;content_type='application/json'
    path.write_bytes(body)
    receipt=dict(status=status,complete=True,body_bytes=len(body),body_sha256=hashlib.sha256(body).hexdigest(),usage=usage,
        transport='Actual nonstream JSON converted to SSE; no additional generation',upstream_body_path=path.name+'.upstream.json',upstream_body_bytes=len(raw))
    path.with_name(path.name+'.receipt.json').write_text(json.dumps(receipt,indent=2))
    header=f'HTTP/1.1 {status} response\r\nContent-Type: {content_type}\r\nContent-Length: {len(body)}\r\nConnection: close\r\n\r\n'.encode()
    client.sendall(header);client.sendall(body)
    return dict(status=status,body_bytes=len(body),complete=True)


def evaluate(trained_root=None,adapter_path=None):
    plan=m.read(ROOT/'PLAN.json');runtime=plan['runtime'];output=ROOT/'inline_policy';output.mkdir(exist_ok=True)
    target=Path(adapter_path) if adapter_path is not None else (ROOT if trained_root is None else trained_root)/'inline_policy/adapter.gguf'
    env=dict(os.environ,CUDA_VISIBLE_DEVICES='',HF_HUB_OFFLINE='1',PYTHONDONTWRITEBYTECODE='1',
        PYTHONPATH=str(Path(runtime['converter']).parent/'gguf-py')+':'+str(Path(runtime['converter']).parent))
    if trained_root is None:
        conversion=subprocess.run([str(c.repo/'venv/bin/python'),'-B',runtime['converter'],'--outtype','f32',
            '--base',runtime['base_config'],'--outfile',str(target),str(output)],capture_output=True,timeout=180,env=env)
        (output/'conversion.stdout').write_bytes(conversion.stdout);(output/'conversion.stderr').write_bytes(conversion.stderr)
        if conversion.returncode:raise RuntimeError('inline adapter conversion failed')
    else:assert target.is_file(), 'reuse the completed candidate, never retrain for a transport repair'
    dev=m.read(ROOT/'DEV_PLAN.json');state=dict(status='RUNNING',pid=os.getpid(),phase='DEV',
        start_ticks=Path('/proc/self/stat').read_text().split()[21],episodes=[])
    m.study.publish(ROOT/'DEV_LIVE.json',state);process=log=None;started=time.monotonic()
    try:
        with m.study.core.resource_lock():
            h=m.study.core.helpers();wrapped=copy.copy(h);wrapped.actor=SimpleNamespace(**vars(h.actor))
            def payload(*args,**kwargs):
                value=h.actor.model_payload(*args,**kwargs);value.update(logprobs=True,top_logprobs=20)
                if trained_root is not None:value.update(stream=False);value.pop('stream_options',None)
                return value
            wrapped.actor.model_payload=payload
            if trained_root is not None:
                wrapped.agg=SimpleNamespace(**vars(h.agg));wrapped.agg.relay_one_model_response=nonstream_response
            checked=h.deps.verify_projection(h.actor.RUNTIME_ROOT,h.actor.RUNTIME_SHA)
            m.study.CAPS.clear();m.study.CAPS.update(plan['caps'])
            process,log=c.native.start_server(runtime,'inline_policy',target,ROOT)
            for ep in dev['episodes']:
                result=m.study.episode(ep,wrapped,checked,m.study.MODEL,private_labels=ROOT/'DEV_LABELS_PRIVATE.json')
                row=dict(index=ep['index'],id=ep['id'],program=result['submitted_program'],success=result['native_success'],normal=result['agent_completed'],
                    posts=result['accounting']['actual_forwarded_posts'],tokens=result['accounting']['provider_total_tokens_known'],
                    unknown=len(result['accounting']['unknown_usage_requests']),seconds=result['actor']['seconds'],
                    gate=gate_score(ep['folder'],result['submitted_program']))
                state['episodes'].append(row);m.study.publish(ROOT/'DEV_LIVE.json',state)
                print(json.dumps(dict(index=row['index'],success=row['success'],score=row['gate']['score'],posts=row['posts'],tokens=row['tokens'])),flush=True)
                receipts=[m.read(p) for p in (Path(ep['folder'])/'wire').glob('*.receipt.json')]
                if any(item['status']!=200 for item in receipts):raise RuntimeError('native service rejected the request; stop before repeating an interface failure')
        state['status']='RETURNED'
    except BaseException:state.update(status='FAILED',error=traceback.format_exc());raise
    finally:
        if process is not None:c.native.stop_server(process,log)
        state['seconds']=time.monotonic()-started;m.study.publish(ROOT/'DEV_LIVE.json',state);m.study.new(ROOT/'DEV_RESULT.json',state)


def compare(extra_classifier_forwards=0):
    # Freeze inline choices before loading teacher outcomes or private labels here.
    dev=m.read(ROOT/'DEV_RESULT.json');assert dev['status']=='RETURNED' and len(dev['episodes'])==64
    rows=dev['episodes'];ranked=sorted(rows,key=lambda x:(-(x['gate']['score'] if x['gate']['score'] is not None else -math.inf),x['index']))
    orders=[r['index'] for r in ranked if r['gate']['score'] is not None]
    m.study.new(ROOT/'POLICIES.json',dict(order=orders,budgets=[8,12,18],teacher_pool='Same-input shared_union from frozen earlier DEV controls, no new teacher calls'))
    legacy=m.read(BASE/'deepseek_development_reference_v1/RESULT.json')['episodes']
    labels=m.read(ROOT/'DEV_LABELS_PRIVATE.json');sources=m.read(ROOT/'DEV_PLAN.json')['episodes'];outcomes=[]
    for row,source,label in zip(rows,sources,labels,strict=True):
        i=row['index'];teacher=legacy[i]
        for name in ['acquisition_value_v1','acquisition_risk_control_v1','acquisition_single_state_v1']:
            f=BASE/name/'teacher_dev'/f'{i:03d}'/'RESULT.json'
            if f.exists():teacher=m.read(f);break
        assert row['id']==teacher['id']==label['id']==source['id']
        public=m.read(Path(source['folder'])/'inputs/public.json')
        program,keep=acquisition.guarded_program(row['program'],teacher['submitted_program'],public,teacher['agent_completed'])
        normal=row['normal'] if keep else teacher['agent_completed']
        graded=m.task.grade(program,public,label['exe_ans'])['execution_correct'] and normal
        outcomes.append(dict(index=i,program=program,success=bool(graded),utility=int(graded)-int(row['success']),
            normal=normal,posts=teacher['accounting']['actual_forwarded_posts'],tokens=teacher['accounting']['provider_total_tokens_known'],guard_keep=keep))
    table={};baseline=sum(r['success'] for r in rows)
    for k in [8,12,18]:
        chosen=set(orders[:k]);final=[]
        for row,source,label,teacher in zip(rows,sources,labels,outcomes,strict=True):
            i=row['index'];program=teacher['program'] if i in chosen else row['program']
            public=m.read(Path(source['folder'])/'inputs/public.json');folder=ROOT/f'final{k}'/f'{i:03d}';folder.mkdir(parents=True)
            m.task.submit_program(program,public,folder,origin='inline_value_frozen_candidate_replay')
            normal=teacher['normal'] if i in chosen else row['normal']
            final.append(m.task.grade(program,public,label['exe_ans'])['execution_correct'] and normal)
        selected=[r for r in outcomes if r['index'] in chosen]
        table[str(k)]=dict(success=sum(final),recovered=sum(r['utility']>0 for r in selected),damaged=sum(r['utility']<0 for r in selected),
            teacher_tasks=len(selected),teacher_posts=sum(r['posts'] for r in selected),teacher_tokens=sum(r['tokens'] for r in selected))
    result=dict(status='RETURNED',cheap_success=baseline,tasks=64,inline_coverage=len(orders),
        all_three_class_coverage=sum(r['gate']['observed_classes']==3 for r in rows),budgets=table,
        actual_new_local=dict(posts=sum(r['posts'] for r in rows),tokens=sum(r['tokens'] for r in rows),unknown=sum(r['unknown'] for r in rows)),
        new_campus_posts=0,extra_classifier_forwards=extra_classifier_forwards,scope='Native correction with inline readout, optionally public missing-tag followups. Fixed actual teacher replay, not new teacher-policy episodes; extra followups are explicitly counted.')
    m.study.new(ROOT/'COMPARISON.json',result);print(json.dumps(result),flush=True)


def run():
    if not (ROOT/'PLAN.json').exists():prepare()
    state=dict(status='RUNNING',pid=os.getpid(),start_ticks=Path('/proc/self/stat').read_text().split()[21],phase='TRAIN')
    m.study.new(ROOT/'RUN_LIVE.json',state);unloaded=False;child=None
    try:
        unloaded=c.stop27()
        with (ROOT/'training.log').open('xb') as log:
            child=subprocess.Popen([str(c.repo/'venv/bin/python'),'-u','-B',__file__,'train'],cwd=c.repo,stdout=log,stderr=subprocess.STDOUT)
            state['child_pid']=child.pid;m.study.publish(ROOT/'RUN_LIVE.json',state)
            if child.wait(timeout=7800):raise RuntimeError('inline training failed; inspect retained TRAIN_RESULT')
        state['phase']='DEV';m.study.publish(ROOT/'RUN_LIVE.json',state);prepare_dev();evaluate();compare();state.update(status='RETURNED',phase='CLOSED')
    except BaseException:state.update(status='FAILED',error=traceback.format_exc());raise
    finally:
        if child is not None and child.poll() is None:child.terminate();child.wait(timeout=30)
        if unloaded:state['restoration']=c.restore27()
        m.study.publish(ROOT/'RUN_LIVE.json',state);m.study.new(ROOT/'RUN_RESULT.json',state)


def native_retry():
    global ROOT
    trained=ROOT;assert m.read(trained/'TRAIN_RESULT.json')['status']=='TRAINED'
    assert m.read(trained/'RUN_RESULT.json')['status'] in ['RETURNED','FAILED']
    ROOT=trained/'native_nonstream_v1';ROOT.mkdir()
    plan=m.read(trained/'PLAN.json');plan.update(training_source=str(trained),
        transport='Nonstream upstream with tools/logprobs; actual raw JSON and usage retained, SSE conversion for unchanged OpenCode.')
    m.study.new(ROOT/'PLAN.json',plan)
    state=dict(status='RUNNING',phase='DEV',pid=os.getpid(),start_ticks=Path('/proc/self/stat').read_text().split()[21])
    m.study.new(ROOT/'RUN_LIVE.json',state);unloaded=False
    try:
        unloaded=c.stop27();prepare_dev();evaluate(trained_root=trained);compare();state.update(status='RETURNED',phase='CLOSED')
    except BaseException:state.update(status='FAILED',error=traceback.format_exc());raise
    finally:
        if unloaded:state['restoration']=c.restore27()
        m.study.publish(ROOT/'RUN_LIVE.json',state);m.study.new(ROOT/'RUN_RESULT.json',state)


def prompt_probe():
    """Post-hoc three-case diagnosis; never a new generalization estimate."""
    global ROOT
    trained=ROOT;top=trained/'prompt_probe_v1';top.mkdir()
    sources=[e for e in m.read(c.replay/'native_v1/PLAN.json')['source_episodes'] if e['index'] in [8,10,39]]
    old=Path(m.read(acquisition.router.RELATIVE_ROOT/'CHEAP_PLAN.json')['adapter']);assert old.is_file()
    candidate=trained/'inline_policy/adapter.gguf';assert candidate.is_file()
    arms=[('new_oldprompt',candidate,False),('old_oldprompt',old,False),('old_inlineprompt',old,True)]
    state=dict(status='RUNNING',pid=os.getpid(),start_ticks=Path('/proc/self/stat').read_text().split()[21],arms={})
    m.study.new(top/'RUN_LIVE.json',state);unloaded=False
    try:
        unloaded=c.stop27()
        for name,adapter,inline in arms:
            ROOT=top/name;ROOT.mkdir();m.study.new(ROOT/'PLAN.json',m.read(trained/'PLAN.json'))
            state['phase']=name;m.study.publish(top/'RUN_LIVE.json',state)
            prepare_dev(sources=sources,use_inline=inline);evaluate(trained_root=trained,adapter_path=adapter)
            rows=m.read(ROOT/'DEV_RESULT.json')['episodes']
            state['arms'][name]=dict(success=sum(r['success'] for r in rows),episodes=rows,
                posts=sum(r['posts'] for r in rows),tokens=sum(r['tokens'] for r in rows),unknown=sum(r['unknown'] for r in rows))
            m.study.publish(top/'RUN_LIVE.json',state)
        state.update(status='RETURNED',phase='CLOSED',scope='Three post-hoc DEV losses, fixed original starting workspaces; parameters x prompt diagnosis. New-inline cell is cached from the completed64. Not nine independent tasks.')
    except BaseException:state.update(status='FAILED',error=traceback.format_exc());raise
    finally:
        if unloaded:state['restoration']=c.restore27()
        m.study.publish(top/'RUN_LIVE.json',state);m.study.new(top/'RUN_RESULT.json',state)


def value_followup():
    """One bounded retry for each publicly missing tag; all programs stay fixed."""
    global ROOT
    trained=ROOT;native=trained/'native_nonstream_v1';top=trained/'value_followup_v1';top.mkdir()
    base=m.read(native/'DEV_RESULT.json');missing={r['index'] for r in base['episodes'] if r['gate']['score'] is None}
    original={r['index']:r for r in base['episodes']}
    sources=[e for e in m.read(c.replay/'native_v1/PLAN.json')['source_episodes'] if e['index'] in missing]
    state=dict(status='RUNNING',phase='FOLLOWUP',pid=os.getpid(),start_ticks=Path('/proc/self/stat').read_text().split()[21])
    m.study.new(top/'RUN_LIVE.json',state);unloaded=False
    try:
        unloaded=c.stop27();ROOT=top/'native';ROOT.mkdir();m.study.new(ROOT/'PLAN.json',m.read(trained/'PLAN.json'));prepare_dev(sources=sources)
        for ep in m.read(ROOT/'DEV_PLAN.json')['episodes']:
            f=Path(ep['folder']);public=m.read(f/'inputs/public.json');program=original[ep['index']]['program']
            execution=m.task.submit_program(program,public,f/'work',origin='freeze_actual_native_program_for_value_only_followup')
            with (f/'inputs/task.txt').open('a') as out:
                out.write('\nThis is a value-only followup. Your already submitted program is FROZEN. Copy it unchanged on the Final program line and add the missing Escalation outcome line. Do not repair or replace it. The fixed teacher still starts from the ORIGINAL snapshot above. Current frozen program and its real execution: '+json.dumps(dict(program=program,execution=execution),ensure_ascii=False))
        evaluate(trained_root=trained);follow=m.read(ROOT/'DEV_RESULT.json');by_index={r['index']:r for r in follow['episodes']}
        ROOT=top;m.study.new(ROOT/'PLAN.json',dict(m.read(trained/'PLAN.json'),scope='Exploratory missing-tag retry, no training. Original64 correction programs fixed; only gate scores may change.'))
        combined=copy.deepcopy(base)
        for row in combined['episodes']:
            if row['index'] not in by_index:continue
            extra=by_index[row['index']];valid=extra['normal'] and extra['program']==row['program']
            if valid and extra['gate']['score'] is not None:row['gate']=extra['gate']
            for key in ['posts','tokens','unknown','seconds']:row[key]+=extra[key]
        added=dict(posts=sum(r['posts'] for r in follow['episodes']),tokens=sum(r['tokens'] for r in follow['episodes']),unknown=sum(r['unknown'] for r in follow['episodes']))
        combined.update(scope='Composed real64 correction episodes plus publicly triggered value-only followups. No new64 runs; no program replacements.',physical_new_followup=added)
        m.study.new(ROOT/'DEV_RESULT.json',combined);m.study.new(ROOT/'DEV_PLAN.json',m.read(native/'DEV_PLAN.json'));m.study.new(ROOT/'DEV_LABELS_PRIVATE.json',m.read(native/'DEV_LABELS_PRIVATE.json'))
        compare(extra_classifier_forwards=added['posts']);state.update(status='RETURNED',phase='CLOSED',physical_new_followup=added)
    except BaseException:state.update(status='FAILED',error=traceback.format_exc());raise
    finally:
        if unloaded:state['restoration']=c.restore27()
        m.study.publish(top/'RUN_LIVE.json',state);m.study.new(top/'RUN_RESULT.json',state)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('mode',choices=['prepare','train','run','compare','native_retry','prompt_probe','value_followup','confidence_probe']);args=parser.parse_args()
    if args.mode=='train':c.root=ROOT;c.train()
    else:globals()[args.mode]()
