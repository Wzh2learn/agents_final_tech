"""Finite exposed-development six-arm x 16-reset comparison.

Check mode reads frozen small artifacts only. Execute explicitly owns one18104
window; model failure is an outcome, interface/accounting failure stops the queue.
"""
from pathlib import Path
import argparse
import fcntl
import hashlib
import importlib.util
import json
import os
import re
import signal
import subprocess
import time

ROOT = Path('/home/testuser/wzh/research_evidence/agent_learning_20261030')
ST = ROOT/'alfworld_text_qualification_20261106/context_study_v1'
BASE = ST/'learning_comparison_v1'
HERE = Path(__file__).resolve().parent
HELPER = BASE/'hf_evaluation_v1/run_evaluation_v3.py'
HELPER_SHA = '4bd44ba612dc7f0645f6cb3925da4e70180104c20332f2c3825bcd8d1b52d472'
WINDOW = BASE/'owned_window_v3/ADMISSION.json'
WINDOW_SHA = '94268732575e251a51613dbba8c8c4864ba175cd9b3ebdad53ca4b88f91026e9'
OLD_PROFILE = ROOT/'django_aggregation_agent_20261106/model_profile.json'
OLD_PROFILE_SHA = 'acce24743e43c205b605b8bceddd4f5eb756d93fdba5f58e28bc32ba772ab6d0'
CAPS = dict(posts=128,seconds=1800,world_actions=100,model_payload_bytes_combined=64000000)
TOKENS = ('prompt_tokens','completion_tokens','total_tokens')
CAP_ERRORS = {'native template estimate plus output/margin exceeds context','episode model budget closed'}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def private(path):
    path = Path(path)
    if (not path.is_absolute() or path != path.resolve() or ROOT not in path.parents or
            any(p.is_symlink() for p in [path,*path.parents])):
        raise ValueError('unsafe private reference: '+str(path))
    return path


def checked(ref):
    if type(ref) is not dict or set(ref) != {'path','sha256'} or not re.fullmatch('[a-f0-9]{64}',ref['sha256']):
        raise ValueError('reference requires exact path and SHA')
    path = private(ref['path'])
    if path.stat().st_size > 10_000_000 or sha(path) != ref['sha256']:
        raise ValueError('frozen small artifact changed: '+str(path))
    return json.loads(path.read_text())


def load(path,name):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def helper():
    if sha(private(HELPER)) != HELPER_SHA:raise ValueError('lifecycle helper changed')
    return load(HELPER,'runtime_comparison_lifecycle')


def prerequisite(kind,value,cases):
    if kind == 'student':
        entries=value.get('cases',[])
        expected={(arm,case) for arm in ('frozen','ordinary','recovery','history_all7','history_top1') for case in cases}
        valid = (value.get('status') == 'ALL_FIVE_ARMS_RETURNED' and value.get('completed_receipts') == 80 and
                 all(value.get(k) is True for k in ('restored_healthy','shared35_unchanged','shared27_unchanged')) and
                 value.get('evaluation_unknown_usage_posts') == 0 and
                 set(value.get('restored_process',{})) == {'pid','start_ticks','exe','argv','cwd'} and
                 len(entries)==80 and {(r.get('arm'),r.get('case')) for r in entries}==expected and
                 all(r.get('status')=='RECORDED' and re.fullmatch('[a-f0-9]{64}',r.get('receipt_sha256','')) for r in entries) and
                 not any(value.get(k) for k in ('unrun','unclosed_attempts','error','episode_cleanup_error','server_cleanup_error',
                         'restoration_error','shared_identity_error','aggregation_error')))
    elif kind == 'teacher':
        valid = (value.get('status') == 'ALL16_DIRECT_TEACHER_RETURNED' and value.get('completed_receipts') == 16 and
                 not any(value.get(k) for k in ('error','cleanup_error','unclosed_attempts','unrun')) and
                 all(value.get(k) == 0 for k in ('training','judges','service_start_stop_actions','unknown_usage_posts')) and
                 value.get('EVAL_ONLY') is True and [r['case'] for r in value.get('results',[])] == cases and
                 all(type(r.get('won')) is bool and re.fullmatch('[a-f0-9]{64}',r.get('receipt_sha256',''))
                     for r in value.get('results',[])))
    elif kind == 'django':
        accounting=(value.get('generation') or {}).get('accounting',{})
        scoring=value.get('scoring') or {}
        valid = (value.get('status') == 'GENERATION_RECORDED' and value.get('task_count') == 1 and
                 type(value.get('actual_forwarded_posts')) is int and value['actual_forwarded_posts'] >= 1 and
                 value['actual_forwarded_posts'] == accounting.get('actual_forwarded_posts') and
                 (accounting.get('integrity') or {}).get('passed') is True and
                 type((scoring.get('semantics') or {}).get('fixed')) is bool and
                 all(k in scoring for k in ('focus','regression','public_probe')))
    else:raise ValueError('unknown prerequisite')
    if not valid:raise ValueError('incomplete or invalid '+kind+' prerequisite')
    return value


def check_plan(plan_ref,student_ref,teacher_ref,django_ref,output,study=None):
    study=study or load(HERE/'alfworld_context_study.py','runtime_comparison_study')
    p=checked(plan_ref);cases=p['case_ids'];arms=p['arms'];output=private(output)
    if (p.get('schema') not in {'ALFWORLD_RUNTIME_CONTEXT_BASELINE_PLAN_V2'} or
            len(cases)!=16 or len(set(cases))!=16 or any(not re.fullmatch('[A-Za-z0-9][A-Za-z0-9_-]*',c) for c in cases) or
            p.get('planned_episodes')!=96 or p.get('carried_episodes')!=0 or
            p.get('maximum_planned_model_posts')!=12288 or p.get('maximum_per_episode_caps')!=CAPS or len(arms)!=6):
        raise ValueError('unknown schema or non-finite comparison contract')
    if any(type(v) is not int for v in p['maximum_per_episode_caps'].values()):raise ValueError('caps must be integers')
    expected=[('frozen_last3','frozen','none','last3'),('ordinary_last3','ordinary','none','last3'),
              ('ordinary_full','ordinary','none','full'),('recovery_full','recovery','none','full'),
              ('recovery_last3','recovery','none','last3'),('history_all7_last3','frozen','all7','last3')]
    if [(a['id'],a['variant'],a['reference'],a['context']) for a in arms]!=expected:
        raise ValueError('not the exact six-arm V2 design/order')
    bindings={ref['path']:ref['sha256'] for ref in (plan_ref,student_ref,teacher_ref,django_ref)}
    protocols={};selections=None;common=None;combinations=set();rows=[]
    for arm in arms:
        if (set(arm)!={'id','variant','reference','context','attempt','protocol'} or
                not re.fullmatch('[a-z][a-z0-9_]*',arm['id']) or type(arm['attempt']) is not int or arm['attempt']<7 or
                arm['context'] not in {'full','last3'} or
                (arm['variant'],arm['reference']) not in {('frozen','none'),('ordinary','none'),('recovery','none'),('frozen','all7')}):
            raise ValueError('invalid fixed comparison arm')
        combination=(arm['variant'],arm['reference'],arm['context'])
        if combination in combinations:raise ValueError('duplicate comparison arm')
        combinations.add(combination);ref=arm['protocol'];q=checked(ref);bindings[ref['path']]=ref['sha256']
        if (q.get('schema') not in {'HF8B_NATIVE_TERMINAL_CONTEXT_CONTROL_DEVELOPMENT_V1','HF8B_NATIVE_TERMINAL_CONTEXT_CONTROL_DEVELOPMENT_V2'} or
                q.get('case_ids')!=cases or q.get('total_caps')!=CAPS or q.get('world_seed')!=17 or q.get('model_seeds')!=[17] or
                q.get('intended_stage')!='ordinary_reset' or q.get('intended_backend')!='student8b' or
                q.get('context_margin_tokens')!=512 or q.get('ordinary_continuations')!=1 or q.get('recent_steps')!=3 or
                study.runtime_controls(q)!={'native_terminal_stop':True,'recent_tool_rounds':3 if arm['context']=='last3' else None}):
            raise ValueError('child protocol/controller/caps changed')
        collection=q.get('collection_caps',{})
        if (any(type(v) is not int for v in q['total_caps'].values()) or set(collection)!=set(CAPS) or
                any(type(v) is not int or v<=0 for v in collection.values()) or collection['world_actions']!=100 or
                collection['posts']>=128 or collection['seconds']>=1800):raise ValueError('invalid child collection/total caps')
        shared={k:v for k,v in q.items() if k!='runtime_controls'}
        if common is not None and shared!=common:raise ValueError('full/last3 changed more than runtime controls')
        common=shared;protocols[arm['context']]=q
        for case in cases:
            root=ST/'cases'/case/'ordinary_reset/student8b'/('attempt_v'+str(arm['attempt']))
            if root.exists():raise FileExistsError('preserve existing episode: '+str(root))
            rows.append(dict(arm=arm['id'],case=case,root=str(root),status='UNRUN'))
    if len({r['root'] for r in rows})!=96 or len({a['id'] for a in arms})!=6:
        raise ValueError('duplicate case/root/arm identity')
    if output.exists():raise FileExistsError('fresh output required')
    selection=common['context_selection'];selected=checked(selection);bindings[selection['path']]=selection['sha256']
    if [r['case'] for r in selected['selections']]!=cases:raise ValueError('selection case/order changed')
    selections={r['case']:r for r in selected['selections']}
    for row in selections.values():
        ref=row['all7'];path=private(ref['path'])
        if not re.fullmatch('[a-f0-9]{64}',row['public_reset_sha256']) or sha(path)!=ref['sha256']:
            raise ValueError('public reset/context binding changed')
        bindings[str(path)]=ref['sha256']
    student=prerequisite('student',checked(student_ref),cases)
    prerequisite('teacher',checked(teacher_ref),cases);prerequisite('django',checked(django_ref),cases)
    teacher_admission=Path(teacher_ref['path']).with_name('ADMISSION.json')
    admission=checked(dict(path=str(teacher_admission),sha256=sha(teacher_admission)))
    if admission['closed_student_result']!=student_ref:raise ValueError('teacher used another student closure')
    bindings[str(teacher_admission)]=sha(teacher_admission)
    window=checked(dict(path=str(WINDOW),sha256=WINDOW_SHA));old_profile=checked(dict(path=str(OLD_PROFILE),sha256=OLD_PROFILE_SHA))
    if tuple(old_profile.get(k) for k in ('host','port','model_id','context','output'))!=('127.0.0.1',18104,'qwen3-8b-qual',32768,8192):
        raise ValueError('original Q4 profile/context changed')
    bindings.update({str(WINDOW):WINDOW_SHA,str(OLD_PROFILE):OLD_PROFILE_SHA,str(HELPER):HELPER_SHA})
    if any(student['restored_process'][k]!=window['owned_process'][k] for k in ('argv','cwd','exe')):
        raise ValueError('original Q4 restoration contract changed')
    # Parent/adapter file hashes are intentionally deferred to explicit execution.
    if set(common['adapters'])!={'ordinary','recovery'}:raise ValueError('unexpected adapter variants')
    for ref in [common['parent_gguf'],common['HF_parent_binding'],*common['adapters'].values()]:
        private(ref['path'])
        if not re.fullmatch('[a-f0-9]{64}',ref['sha256']):raise ValueError('model binding SHA missing')
    return dict(plan=p,protocols=protocols,selections=selections,rows=rows,bindings=bindings,
                student=student,window=window,old_profile=old_profile,study=study,output=output)


def frozen(contract,epoch):
    if contract['study'].components()!=epoch or any(sha(path)!=digest for path,digest in contract['bindings'].items()):
        raise RuntimeError('frozen helper/protocol/source/components changed')


def audit(study,root,receipt,manifest):
    root=Path(root);gates=receipt['model_relay_errors'];cap=bool(gates)
    if receipt['errors'] or any(e.get('type')!='ValueError' or e.get('detail') not in CAP_ERRORS for e in gates):
        raise ValueError('generic episode/transport/cleanup failure')
    if receipt['status'] not in {'RETURNED','EPISODE_TIMEOUT','NATIVE_TERMINAL_STOP'} or receipt['label']!='MULTITASK_CONTEXT_DEVELOPMENT':
        raise ValueError('unknown episode status/label')
    posts,actual=receipt['model_posts'],receipt['forwarded_model_posts']
    if any(type(n) is not int for n in (posts,actual,receipt['real_model_calls'])) or not 0<=actual<=posts<=128 or receipt['real_model_calls']!=actual:
        raise ValueError('actual/budget calls differ')
    if receipt['manifest_sha256']!=sha(root/'manifest.json') or receipt['runtime_controls']!=manifest['runtime_controls']:
        raise ValueError('receipt manifest/control binding changed')
    state=receipt['final_world_state'];study.public(state)
    if type(receipt['won']) is not bool or receipt['won']!=state['won']:raise ValueError('native outcome differs')
    witness=study.native_world_witness(root,manifest)
    if state!=witness['state']:raise ValueError('final receipt differs from fresh native state')
    stop=receipt.get('controller_stop')
    if stop is not None:
        reason='native_won' if witness['state']['won'] else 'native_done_unwon'
        if (not witness['state']['done'] or state!=witness['state'] or
                stop!=dict(witness,reason=reason,forwarded_posts_at_stop=actual) or
                json.loads((root/'controller_stop.json').read_text())!=stop or not receipt['controller_stops'] or
                any(s!={'type':'ControllerStop','reason':reason} for s in receipt['controller_stops'])):
            raise ValueError('native terminal witness/reason/count differs')
    elif receipt['status']=='NATIVE_TERMINAL_STOP' or receipt.get('controller_stops'):
        raise ValueError('terminal status has no verified witness')
    if any(r['exit']!=0 for r in receipt['rounds']) and not (cap or stop):raise ValueError('unqualified actor failure')
    requests=sorted((root/'requests').glob('*.json'));request_bytes=0
    if len(requests)!=posts:raise ValueError('budget request records missing')
    for path in requests:
        payload=json.loads(path.read_text())['forwarded'];body=path.with_suffix('.body').read_bytes()
        if 'lora' in payload or body!=json.dumps(payload,separators=(',',':')).encode():raise ValueError('actual body changed')
        request_bytes+=len(body)
    if request_bytes!=receipt['model_request_payload_bytes']:raise ValueError('request byte accounting differs')
    if (any(type(receipt.get(k)) is not int or receipt[k]<0 for k in ('model_request_payload_bytes','model_response_wire_bytes')) or
            request_bytes+receipt['model_response_wire_bytes']>CAPS['model_payload_bytes_combined']):
        raise ValueError('combined physical byte accounting invalid')
    records=sorted((root/'responses').glob('*.receipt.json'));totals=dict.fromkeys(TOKENS,0);cached=[];known=0
    if len(records)!=len(receipt['response_receipts']) or len(records)>actual:raise ValueError('response counts differ')
    for path,embedded in zip(records,receipt['response_receipts']):
        row=json.loads(path.read_text());body=Path(str(path)[:-len('.receipt.json')])
        if (row!=embedded or sha(body)!=row['body_sha256'] or row['complete'] is not True or row['status']!=200 or
                row['body_bytes']!=body.stat().st_size):
            raise ValueError('response integrity failed')
        usage=row.get('usage')
        if usage is None:continue
        if any(type(usage.get(k)) is not int or usage[k]<0 for k in TOKENS) or usage['total_tokens']!=usage['prompt_tokens']+usage['completion_tokens']:
            raise ValueError('provider usage invalid')
        known+=1
        for key in TOKENS:totals[key]+=usage[key]
        cache=(usage.get('prompt_tokens_details') or {}).get('cached_tokens')
        if cache is not None and (type(cache) is not int or not 0<=cache<=usage['prompt_tokens']):raise ValueError('cache is not input subset')
        cached.append(cache)
    expected_cache=sum(cached) if cached and all(x is not None for x in cached) else None
    if (totals!=receipt['provider_usage'] or actual-known!=receipt['unknown_usage_model_posts'] or
            expected_cache!=receipt['provider_cached_input_tokens']):raise ValueError('provider cost accounting differs')
    if actual-known:raise ValueError('unknown usage retained; stop on accounting failure')
    if not actual and not (cap or stop):raise ValueError('no actual model call or native controller stop')
    paths=[p for p in root.rglob('*') if p.is_file() and p.parent.name in
           {'requests','responses','observed_requests','projections','template_checks'}]
    paths += [p for p in root.glob('raw_*.jsonl')]+[root/'manifest.json',root/'receipt.json',root/'execute_world.jsonl']
    if stop:paths.append(root/'controller_stop.json')
    return dict(won=state['won'],done_unwon=state['done'] and not state['won'],
                controller_reason=stop['reason'] if stop else None,scientific_cap=cap or receipt['status']=='EPISODE_TIMEOUT',
                actual_model_calls=actual,budget_model_posts=posts,provider_usage=totals,
                cached_input_tokens=expected_cache,raw_bindings={str(p):sha(p) for p in paths})


def aggregate(rows):
    costs=[];missing=[];errors=[]
    if len({r['root'] for r in rows})!=len(rows):raise ValueError('duplicate accounting root')
    for entry in rows:
        path=Path(entry['root'])/'receipt.json'
        if not path.exists():
            if Path(entry['root']).exists():missing.append(entry['root'])
            continue
        try:
            if entry['status']=='UNRUN':raise ValueError('unowned receipt appeared on an unrun root')
            digest=sha(path)
            if entry.get('receipt_sha256',digest)!=digest:raise ValueError('receipt SHA changed')
            receipt=json.loads(path.read_text())
            if type(receipt) is not dict:raise ValueError('receipt must be an object')
            costs.append(receipt);entry['receipt_sha256']=digest
            for key in ('real_model_calls','model_posts','unknown_usage_model_posts'):
                if type(receipt.get(key)) is not int or receipt[key]<0:errors.append(dict(root=entry['root'],field=key))
            usage=receipt.get('provider_usage')
            if type(usage) is not dict or any(type(usage.get(k)) is not int or usage[k]<0 for k in TOKENS):
                errors.append(dict(root=entry['root'],field='provider_usage'))
            if entry['status']!='CLOSED_AUDITED':entry['status']='CLOSED_UNAUDITED'
        except (ValueError,OSError) as exc:errors.append(dict(root=entry['root'],error=str(exc)))
    known=lambda key:sum(r[key] for r in costs if type(r.get(key)) is int and r[key]>=0)
    unknown_known=all(type(r.get('unknown_usage_model_posts')) is int for r in costs)
    complete=bool(rows) and len(costs)==len(rows) and not missing and not errors and all(r['status']=='CLOSED_AUDITED' for r in rows)
    return dict(completed_receipts=len(costs),unclosed_attempts=missing,aggregation_errors=errors,
        unrun=[r['root'] for r in rows if not Path(r['root']).exists()],known_actual_model_calls=known('real_model_calls'),
        known_budget_model_posts=known('model_posts'),total_actual_model_calls=known('real_model_calls') if complete else None,
        provider_usage_known_subtotals={k:sum(r['provider_usage'][k] for r in costs if type(r.get('provider_usage')) is dict and
                type(r['provider_usage'].get(k)) is int and r['provider_usage'][k]>=0) for k in TOKENS},
        unknown_usage_model_posts=known('unknown_usage_model_posts') if unknown_known and complete else None,
        unknown_usage_model_posts_known_subtotal=known('unknown_usage_model_posts'),
        cached_input_tokens_known_subtotal=known('provider_cached_input_tokens'),
        cached_input_missing_receipts=sum(r.get('provider_cached_input_tokens') is None for r in costs),
        scope='New unique roots only; formation, training and historical bills remain separate')


def restore(h,original,child,ticket,output,window,stop_requested):
    """Collect only birth-ticket children; never signal or overlay an unknown PID."""
    result=dict(restored_healthy=False);restored_child=restore_ticket=None
    try:
        if child is not None:
            h.stop_child(child,ticket);child.wait(timeout=15)
        if original is None:return result
        prior=h.proc(original['pid'])
        h.protected(window)
        if prior is not None:
            if prior!=original:raise RuntimeError('original PID replaced; refuse overlay or signal')
            h.listener(original);health,_=h.get('/health',output/'retained_q4_health',1)
            if health['status']!=200:raise RuntimeError('retained Q4 health failed')
            result.update(restored_healthy=True,restored_process=original,original_not_released=True)
        else:
            if not stop_requested:raise RuntimeError('original disappeared without owned release')
            h.idle()
            with (output/'restore_q4.log').open('xb') as log:
                restored_child=subprocess.Popen(original['argv'],cwd=original['cwd'],stdin=subprocess.DEVNULL,
                    stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
                restore_ticket=h.owned_child_ticket(restored_child)
                h.new(output/'RESTORE_SPAWN_TICKET.json',restore_ticket)
                expected={k:original[k] for k in ('argv','cwd','exe')}
                actual=h.stable_child(restored_child,expected,output/'restore_identity.jsonl',restore_ticket)
                h.ready(restored_child,actual,output/'restoration');h.listener(actual)
                result.update(restored_healthy=True,restored_process=actual)
    except BaseException as exc:
        result.update(restoration_error=dict(type=type(exc).__name__,message=str(exc)))
        if restored_child is not None and not result['restored_healthy']:
            try:h.stop_child(restored_child,restore_ticket);restored_child.wait(timeout=15)
            except BaseException as cleanup:result['restore_child_cleanup_error']=str(cleanup)
    if result['restored_healthy']:
        try:h.protected(window);result.update(shared35_unchanged=True,shared27_unchanged=True)
        except BaseException as exc:result['shared_identity_error']=str(exc)
    return result


def execute(c):
    h=helper();study=c['study'];out=c['output'];p=c['plan'];rows=c['rows'];window=c['window']
    epoch=study.components();c['bindings'][str(Path(__file__).resolve())]=sha(__file__)
    # The nonblocking shared lock rejects a still-active teacher or another owner.
    with (ST/'model_resource.lock').open('r+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);out.mkdir()
        result=dict(status='STARTED',cases=rows,development_only=True,carried_episodes=0,training=0,judges=0,
                    historical_formation_and_training_costs=None,restored_healthy=False)
        original=child=ticket=active=None;released=False;started=time.monotonic()
        def event(kind,**data):
            with (out/'events.jsonl').open('a') as log:
                log.write(json.dumps(dict(event=kind,utc=time.time(),**data))+'\n');log.flush();os.fsync(log.fileno())
        cancelled=False
        def cancel(*_):
            nonlocal cancelled
            if not cancelled:cancelled=True;raise KeyboardInterrupt('CANCEL_REQUESTED')
        previous={s:signal.signal(s,cancel) for s in (signal.SIGTERM,signal.SIGINT)}
        try:
            frozen(c,epoch);original=c['student']['restored_process']
            if h.proc(original['pid'])!=original:raise RuntimeError('current Q4 differs from complete restoration identity')
            h.listener(original);h.protected(window);h.idle()
            common=c['protocols']['full'];_,parent=study.verified_gguf(common['parent_gguf']['path'],common['parent_gguf']['sha256'])
            if sha(original['exe'])!=c['old_profile']['server_executable_sha256']:raise ValueError('server executable changed')
            h.new(out/'ADMISSION.json',dict(owner_pid=os.getpid(),bindings=c['bindings'],components=epoch,
                  owned_process=original,parent_verification=parent,protected35=window['protected35'],protected27=window['protected27']))
            # No model success qualification: the first scheduled actor is counted.
            released=True;h.stop_owned(original,escalate=False);event('original_stopped',process=original)
            for arm in p['arms']:
                frozen(c,epoch);h.protected(window);h.idle();directory=out/arm['id'];directory.mkdir()
                q=c['protocols'][arm['context']];adapter=q['adapters'].get(arm['variant'])
                if adapter:study.runtime_file(adapter['path'],adapter['sha256'])
                argv=h.server_argv(original['argv'],q['parent_gguf']['path'],adapter)
                with (directory/'server.log').open('xb') as log:
                    child=subprocess.Popen(argv,cwd=original['cwd'],stdin=subprocess.DEVNULL,stdout=log,
                                           stderr=subprocess.STDOUT,start_new_session=True)
                    ticket=h.owned_child_ticket(child);h.new(directory/'SPAWN_TICKET.json',ticket)
                    current=h.stable_child(child,dict(argv=argv,cwd=original['cwd'],exe=original['exe']),directory/'startup_identity.jsonl',ticket)
                    h.ready(child,current,directory);loaded,body=h.get('/lora-adapters',directory/'loaded_adapters',1)
                    if loaded['status']!=200:raise RuntimeError('loaded adapters HTTP failed')
                    h.adapters(body,adapter)
                    admission=dict(schema='owned_8b_runtime_admission_v1',status='OWNED_RESEARCH_RUNTIME_READY',process=current,
                        gguf={k:q['parent_gguf'][k] for k in ('path','sha256')},model_alias='qwen3-8b-qual',
                        active_lora=dict(adapter,scale=1) if adapter else None,parent_hf_binding=q['HF_parent_binding'],
                        loaded_adapter_receipt=loaded,protocol_sha256=arm['protocol']['sha256'])
                    h.new(directory/'ADMISSION.json',admission)
                    profile=dict(schema='alfworld_owned_8b_runtime_profile_v1',variant=arm['variant'],host='127.0.0.1',port=18104,
                        model_id='qwen3-8b-qual',context=32768,output=8192,enable_thinking=False,gguf_path=q['parent_gguf']['path'],
                        gguf_sha256=q['parent_gguf']['sha256'],server_executable=original['exe'],
                        server_executable_sha256=c['old_profile']['server_executable_sha256'],parent_hf_binding=q['HF_parent_binding'],
                        runtime_admission=dict(path=str(directory/'ADMISSION.json'),sha256=sha(directory/'ADMISSION.json')))
                    profile_path=directory/'PROFILE.json';h.new(profile_path,profile);profile_sha=sha(profile_path)
                    for entry in [r for r in rows if r['arm']==arm['id']]:
                        active=Path(entry['root']);frozen(c,epoch);h.listener(current);h.protected(window)
                        if active.exists():raise FileExistsError('attempt appeared after admission')
                        entry['status']='PREPARING';event('case_start',**entry)
                        ref=c['selections'][entry['case']]['all7'] if arm['reference']=='all7' else None
                        m=study.prepare(active,Path(arm['protocol']['path']),arm['protocol']['sha256'],model_seed=17,
                            runtime_profile=profile_path,runtime_profile_sha=profile_sha,
                            reference_context=Path(ref['path']) if ref else None,reference_context_sha=ref['sha256'] if ref else None)
                        if (m['source_root'] is not None or m['caps']!=CAPS or m['runtime_controls']!=q['runtime_controls'] or
                                sha(active/'initial_reset.json')!=c['selections'][entry['case']]['public_reset_sha256'] or
                                m['runtime_profile_override']['gguf_verification']!=parent):raise ValueError('reset/input/parent differs')
                        frozen(c,epoch);entry['status']='EXECUTING';receipt=study.run_episode(active,sha(active/'manifest.json'))
                        entry.update(status='CLOSED_UNAUDITED',receipt_sha256=sha(active/'receipt.json'))
                        entry.update(audit(study,active,receipt,m));entry['status']='CLOSED_AUDITED';event('case_audited',**entry)
                        frozen(c,epoch);h.protected(window);active=None
                    h.stop_child(child,ticket);child.wait(timeout=15);child=ticket=None
            result['status']='ALL96_RUNTIME_CONTEXT_RETURNED'
        except BaseException as exc:
            result.update(status='STOPPED_RESTORE_REQUIRED',error=dict(type=type(exc).__name__,message=str(exc)))
            event('queue_stopped',error=result['error'],active_root=str(active) if active else None)
        finally:
            for sig in previous:signal.signal(sig,signal.SIG_IGN)
            try:
                if active is not None:h.cleanup_episode(active)
            except BaseException as exc:result['episode_cleanup_error']=str(exc)
            result.update(restore(h,original,child,ticket,out,window,released))
            try:result.update(aggregate(rows))
            except BaseException as exc:result.update(aggregation_error=str(exc),total_actual_model_calls=None,unknown_usage_model_posts=None)
            result['window_wall_seconds']=time.monotonic()-started
            if not result['restored_healthy']:result['status']='RESTORATION_NOT_VERIFIED'
            if result['status']=='ALL96_RUNTIME_CONTEXT_RETURNED' and (result.get('completed_receipts')!=96 or
                    result.get('unclosed_attempts') or result.get('aggregation_errors') or result.get('unrun') or
                    result.get('episode_cleanup_error') or result.get('shared_identity_error')):
                result['status']='INCOMPLETE_OR_CLEANUP_FAILURE'
            try:h.new(out/'RESULT.json',result);event('window_closed',status=result['status'],result_sha256=sha(out/'RESULT.json'))
            finally:
                for sig,handler in previous.items():signal.signal(sig,handler)
                fcntl.flock(lock,fcntl.LOCK_UN)
    return result


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__);mode=parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--check',action='store_true');mode.add_argument('--execute',action='store_true')
    for name in ('plan','student-result','teacher-result','django-result'):
        parser.add_argument('--'+name,type=Path,required=True);parser.add_argument('--'+name+'-sha',required=True)
    parser.add_argument('--output',type=Path,required=True);args=parser.parse_args(argv)
    refs=[dict(path=str(getattr(args,k)),sha256=getattr(args,k+'_sha')) for k in ('plan','student_result','teacher_result','django_result')]
    c=check_plan(*refs,args.output);helper() # Checked import only; never call the old execute/main.
    if args.check:
        frozen(c,c['study'].components())
        result=dict(status='CPU_CHECK_ONLY_NOT_EXECUTED',planned_episodes=96,model_calls=0,service_actions=0,
                    native_world_runs=0,parent_weight_hash_not_run=True)
    else:result=execute(c)
    print(json.dumps({k:result.get(k) for k in ('status','planned_episodes','completed_receipts','known_actual_model_calls',
        'total_actual_model_calls','unknown_usage_model_posts','restored_healthy') if k in result}))
    return 0 if args.check or result['status']=='ALL96_RUNTIME_CONTEXT_RETURNED' else 1


if __name__=='__main__':
    raise SystemExit(main())
