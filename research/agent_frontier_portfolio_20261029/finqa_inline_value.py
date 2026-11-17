"""One-pass correction and teacher-value readout; reuse the existing native actor."""
from pathlib import Path
from types import SimpleNamespace
import argparse, collections, copy, json, math, os, re, shutil, subprocess, time, traceback

import finqa_acquisition_learning as acquisition

c=acquisition.c
m=c.m
ROOT=acquisition.ROOT.parent/'inline_acquisition_v2'
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


def prepare_dev():
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
        (inputs/'task.txt').write_text(prompt(public,m.state_from_folder(source)))
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


def evaluate():
    plan=m.read(ROOT/'PLAN.json');runtime=plan['runtime'];output=ROOT/'inline_policy';target=output/'adapter.gguf'
    env=dict(os.environ,CUDA_VISIBLE_DEVICES='',HF_HUB_OFFLINE='1',PYTHONDONTWRITEBYTECODE='1',
        PYTHONPATH=str(Path(runtime['converter']).parent/'gguf-py')+':'+str(Path(runtime['converter']).parent))
    conversion=subprocess.run([str(c.repo/'venv/bin/python'),'-B',runtime['converter'],'--outtype','f32',
        '--base',runtime['base_config'],'--outfile',str(target),str(output)],capture_output=True,timeout=180,env=env)
    (output/'conversion.stdout').write_bytes(conversion.stdout);(output/'conversion.stderr').write_bytes(conversion.stderr)
    if conversion.returncode:raise RuntimeError('inline adapter conversion failed')
    dev=m.read(ROOT/'DEV_PLAN.json');state=dict(status='RUNNING',pid=os.getpid(),phase='DEV',
        start_ticks=Path('/proc/self/stat').read_text().split()[21],episodes=[])
    m.study.publish(ROOT/'DEV_LIVE.json',state);process=log=None;started=time.monotonic()
    try:
        with m.study.core.resource_lock():
            h=m.study.core.helpers();wrapped=copy.copy(h);wrapped.actor=SimpleNamespace(**vars(h.actor))
            def payload(*args,**kwargs):
                value=h.actor.model_payload(*args,**kwargs);value.update(logprobs=True,top_logprobs=20);return value
            wrapped.actor.model_payload=payload
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
        state['status']='RETURNED'
    except BaseException:state.update(status='FAILED',error=traceback.format_exc());raise
    finally:
        if process is not None:c.native.stop_server(process,log)
        state['seconds']=time.monotonic()-started;m.study.publish(ROOT/'DEV_LIVE.json',state);m.study.new(ROOT/'DEV_RESULT.json',state)


def compare():
    # Freeze inline choices before loading teacher outcomes or private labels here.
    dev=m.read(ROOT/'DEV_RESULT.json');assert dev['status']=='RETURNED' and len(dev['episodes'])==64
    rows=dev['episodes'];ranked=sorted(rows,key=lambda x:(-(x['gate']['score'] if x['gate']['score'] is not None else -math.inf),x['index']))
    orders=[r['index'] for r in ranked if r['gate']['score'] is not None]
    m.study.new(ROOT/'POLICIES.json',dict(order=orders,budgets=[8,12,18],teacher_pool='Same-input shared_union from frozen earlier DEV controls, no new teacher calls'))
    legacy=m.read(ROOT.parent/'deepseek_development_reference_v1/RESULT.json')['episodes']
    labels=m.read(ROOT/'DEV_LABELS_PRIVATE.json');sources=m.read(ROOT/'DEV_PLAN.json')['episodes'];outcomes=[]
    for row,source,label in zip(rows,sources,labels,strict=True):
        i=row['index'];teacher=legacy[i]
        for name in ['acquisition_value_v1','acquisition_risk_control_v1','acquisition_single_state_v1']:
            f=ROOT.parent/name/'teacher_dev'/f'{i:03d}'/'RESULT.json'
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
        new_campus_posts=0,extra_classifier_forwards=0,scope='One native correction arm, inline token readout. Fixed actual teacher replay, not new teacher-policy episodes.')
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


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('mode',choices=['prepare','train','run','compare']);args=parser.parse_args()
    if args.mode=='train':c.root=ROOT;c.train()
    else:globals()[args.mode]()
