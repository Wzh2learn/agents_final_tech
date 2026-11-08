"""Finite exposed-development six-arm comparison or its two-full-control extension.

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
SIX_SCHEMA = 'ALFWORLD_RUNTIME_CONTEXT_BASELINE_PLAN_V2'
FULL_SCHEMA = 'ALFWORLD_FULL_BASELINE_EXTENSION_PLAN_V1'
RECOVERY_SCHEMA = 'ALFWORLD_PRESERVED_RECOVERY_COMPARISON_PLAN_V1'
RECOVERY_CAPS = dict(CAPS,posts=32,seconds=600)
SIX_ARMS = [('frozen_last3','frozen','none','last3'),('ordinary_last3','ordinary','none','last3'),
            ('ordinary_full','ordinary','none','full'),('recovery_full','recovery','none','full'),
            ('recovery_last3','recovery','none','last3'),('history_all7_last3','frozen','all7','last3')]
FULL_ARMS = [('frozen_full','frozen','none','full'),('history_all7_full','frozen','all7','full')]
RECOVERY_ARMS = [('frozen_full','frozen','none','full'),('ordinary_full','ordinary','none','full'),
                 ('recovery_full','recovery','none','full'),('history_all7_full','frozen','all7','full')]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def private(path):
    path = Path(path)
    if (not path.is_absolute() or path != path.resolve() or ROOT not in path.parents or
            any(p.is_symlink() for p in [path,*path.parents])):
        raise ValueError('unsafe private reference: '+str(path))
    return path


def checked(ref, *, max_bytes=10_000_000):
    if type(ref) is not dict or set(ref) != {'path','sha256'} or not re.fullmatch('[a-f0-9]{64}',ref['sha256']):
        raise ValueError('reference requires exact path and SHA')
    path = private(ref['path'])
    if path.stat().st_size > max_bytes or sha(path) != ref['sha256']:
        raise ValueError('frozen small artifact changed: '+str(path))
    return json.loads(path.read_text())


def full_baseline_origin(plan, cases, arms, bindings):
    """Bind the post-hoc controls to the complete original96, without carrying it."""
    if not all(k in plan for k in ('origin_context_plan','origin_context_result')):
        raise ValueError('full controls require the frozen original96 plan/result')
    origin_ref=plan['origin_context_plan'];result_ref=plan['origin_context_result']
    origin=checked(origin_ref)
    # The real closure embeds96 raw-binding maps and is10.7MB. Only this typed
    # result (and restoration metadata below) gets a bounded16MiB JSON allowance.
    previous=checked(result_ref,max_bytes=16*1024**2)
    if (origin.get('schema')!=SIX_SCHEMA or origin.get('planned_episodes')!=96 or
            origin.get('carried_episodes')!=0 or origin.get('case_ids')!=cases or
            origin.get('maximum_planned_model_posts')!=12288 or
            origin.get('maximum_per_episode_caps')!=CAPS or
            [(a['id'],a['variant'],a['reference'],a['context']) for a in origin.get('arms',[])]!=SIX_ARMS):
        raise ValueError('full controls changed the original96 design/tasks')
    previous_arms={a['id']:a for a in origin['arms']}
    expected=[(a['id'],case) for a in origin['arms'] for case in cases]
    rows=previous.get('cases',[])
    if (previous.get('status')!='ALL96_RUNTIME_CONTEXT_RETURNED' or
            previous.get('completed_receipts')!=96 or previous.get('carried_episodes')!=0 or
            any(previous.get(k) is not True for k in ('restored_healthy','shared35_unchanged','shared27_unchanged')) or
            any(type(previous.get(k)) is not int or previous[k]!=0 for k in ('training','judges','unknown_usage_model_posts')) or
            any(previous.get(k) for k in ('error','unrun','unclosed_attempts','aggregation_errors','aggregation_error',
                'episode_cleanup_error','server_cleanup_error','restoration_error','shared_identity_error')) or
            len(rows)!=96 or [(r.get('arm'),r.get('case')) for r in rows]!=expected):
        raise ValueError('full controls require all96 audited, restored and accounted')
    for row in rows:
        arm=previous_arms[row['arm']]
        root=ST/'cases'/row['case']/'ordinary_reset/student8b'/('attempt_v'+str(arm['attempt']))
        if (row.get('status')!='CLOSED_AUDITED' or type(row.get('won')) is not bool or
                row.get('root')!=str(root) or not re.fullmatch('[a-f0-9]{64}',row.get('receipt_sha256',''))):
            raise ValueError('original96 episode identity/closure differs')
        receipt_ref=dict(path=str(root/'receipt.json'),sha256=row['receipt_sha256'])
        if not (root/'receipt.json').is_file():raise ValueError('original96 receipt is missing')
        receipt=checked(receipt_ref)
        if ((receipt.get('case_id'),receipt.get('stage'),receipt.get('backend'))!=
                (row['case'],'ordinary_reset','student8b') or
                type(receipt.get('won')) is not bool or receipt['won']!=row['won']):
            raise ValueError('original96 receipt task/outcome differs')
        bindings[receipt_ref['path']]=receipt_ref['sha256']
    old_attempts={a['attempt'] for a in origin['arms']}
    if any(a['attempt'] in old_attempts or a['protocol']!=previous_arms['ordinary_full']['protocol'] for a in arms):
        raise ValueError('full controls require fresh attempts and the identical full protocol')
    for ref in (origin_ref,result_ref):bindings[ref['path']]=ref['sha256']


def preserved_sources(plan,cases,common,bindings,study):
    """Qualify the fixed eight nonterminal prefixes, not a fresh-source claim."""
    if not all(k in plan for k in ('additional_recovery_source','source_native_replay')):
        raise ValueError('preserved recovery requires source and native replay references')
    source_ref=plan['additional_recovery_source'];native_ref=plan['source_native_replay']
    source=checked(source_ref);native=checked(native_ref);old_ref=source['source_protocol'];old=checked(old_ref)
    if (source.get('schema')!='ALFWORLD_ADDITIONAL_RECOVERY_V1' or
            native.get('schema')!='additional_failure_prefix_native_replay_v1' or
            native.get('status')!='QUALIFIED_PUBLIC_REPLAY' or native.get('source_protocol')!=source_ref or
            native.get('model_calls')!=0 or native.get('training')!=0 or
            len(old.get('case_ids',[]))!=16 or len(set(old['case_ids']))!=16 or
            len(native.get('rows',[]))!=8 or [r.get('case') for r in native['rows']]!=cases or
            common.get('additional_recovery_source')!=source_ref or
            native.get('pool')!=dict(path=common['pool_path'],sha256=common['pool_sha256'])):
        raise ValueError('preserved source/native cohort or protocol differs')
    prefixes={};total_steps=0
    for case,row in zip(cases,native['rows']):
        if case not in old['case_ids'] or case not in source['source_bindings']:
            raise ValueError('preserved case not in the frozen source cohort')
        root=Path(source['source_bindings'][case]['root'])
        prefix=study.load_source_prefix(common,case,root);n=len(prefix['steps'])
        expected=dict(RECOVERY_CAPS,world_actions=100-n)
        if (prefix['root']!=root or not 0<n<100 or prefix.get('additional_caps')!=expected or
                prefix.get('world_step_cap')!=100 or
                prefix.get('budget_semantics')!='ADDITIONAL_PHASE_NOT_OLD_REMAINING_POSTS' or
                prefix['manifest']['protocol_sha256']!=old_ref['sha256'] or
                row.get('status')!='PUBLIC_REPLAY_EQUAL' or row.get('owned_world_stopped') is not True or
                row.get('public_prefix_sha256')!=prefix['public_prefix_sha256'] or
                row.get('source_actions')!=n or row.get('remaining_world_actions')!=100-n or
                row.get('final_state',{}).get('won') is not False or row['final_state'].get('done') is not False or
                row['final_state'].get('action_count')!=n):
            raise ValueError('preserved prefix/replay/new-phase budget differs')
        for path,digest in prefix['binding'].items():
            path=private(path)
            if sha(path)!=digest:raise ValueError('preserved source binding changed')
            bindings[str(path)]=digest
        prefixes[case]=prefix;total_steps+=n
    if native.get('replayed_actions')!=total_steps:raise ValueError('native replay action total differs')
    for ref in (source_ref,native_ref,old_ref):bindings[ref['path']]=ref['sha256']
    return prefixes,old['case_ids']


def completed_status(plan):
    if plan['schema']==SIX_SCHEMA:return 'ALL96_RUNTIME_CONTEXT_RETURNED'
    if plan['schema']==FULL_SCHEMA:return 'ALL32_FULL_BASELINES_RETURNED'
    if plan['schema']==RECOVERY_SCHEMA:return 'ALL32_PRESERVED_RECOVERY_RETURNED'
    raise ValueError('unknown completion design')


def final_status(plan, result):
    if not result.get('restored_healthy'):return 'RESTORATION_NOT_VERIFIED'
    if result['status']==completed_status(plan) and (result.get('completed_receipts')!=plan['planned_episodes'] or
            any(result.get(k) for k in ('unclosed_attempts','aggregation_errors','unrun',
                'episode_cleanup_error','shared_identity_error'))):
        return 'INCOMPLETE_OR_CLEANUP_FAILURE'
    return result['status']


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


def check_plan(plan_ref,student_ref,teacher_ref,django_ref,output,study=None,restoration_ref=None):
    study=study or load(HERE/'alfworld_context_study.py','runtime_comparison_study')
    p=checked(plan_ref);cases=p['case_ids'];arms=p['arms'];output=private(output)
    extension=p.get('schema')==FULL_SCHEMA;preserved=p.get('schema')==RECOVERY_SCHEMA
    count=32 if extension or preserved else 96
    expected=RECOVERY_ARMS if preserved else FULL_ARMS if extension else SIX_ARMS
    maximum=RECOVERY_CAPS if preserved else CAPS
    case_count=8 if preserved else 16
    if (p.get('schema') not in {SIX_SCHEMA,FULL_SCHEMA,RECOVERY_SCHEMA} or
            len(cases)!=case_count or len(set(cases))!=case_count or any(not re.fullmatch('[A-Za-z0-9][A-Za-z0-9_-]*',c) for c in cases) or
            p.get('planned_episodes')!=count or p.get('carried_episodes')!=0 or
            p.get('maximum_planned_model_posts')!=count*maximum['posts'] or p.get('maximum_per_episode_caps')!=maximum or
            len(arms)!=len(expected)):
        raise ValueError('unknown schema or non-finite comparison contract')
    if (any(type(v) is not int for v in p['maximum_per_episode_caps'].values()) or
            any(type(p[k]) is not int for k in ('planned_episodes','carried_episodes','maximum_planned_model_posts'))):
        raise ValueError('caps/counts must be integers')
    if [(a['id'],a['variant'],a['reference'],a['context']) for a in arms]!=expected:
        raise ValueError('not the exact fixed design/order')
    bindings={ref['path']:ref['sha256'] for ref in (plan_ref,student_ref,teacher_ref,django_ref)}
    if extension:
        if restoration_ref is None:raise ValueError('full controls require explicit current restoration')
        full_baseline_origin(p,cases,arms,bindings)
    if p.get('analysis_contract'):
        ref=p['analysis_contract'];checked(ref);bindings[ref['path']]=ref['sha256']
    if preserved and restoration_ref is None:raise ValueError('preserved recovery requires current restoration')
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
        allowed_schemas={'HF8B_PRESERVED_FAILURE_CONTEXT_DEVELOPMENT_V1'} if preserved else {'HF8B_NATIVE_TERMINAL_CONTEXT_CONTROL_DEVELOPMENT_V1','HF8B_NATIVE_TERMINAL_CONTEXT_CONTROL_DEVELOPMENT_V2'}
        if (q.get('schema') not in allowed_schemas or
                q.get('case_ids')!=cases or q.get('total_caps')!=CAPS or q.get('world_seed')!=17 or q.get('model_seeds')!=[17] or
                q.get('intended_stage')!=('preserved_recovery' if preserved else 'ordinary_reset') or
                ('additional_recovery_source' in q)!=preserved or q.get('intended_backend')!='student8b' or
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
            stage=('keep_full' if arm['reference']=='all7' else 'drop_full') if preserved else 'ordinary_reset'
            root=ST/'cases'/case/stage/'student8b'/('attempt_v'+str(arm['attempt']))
            if root.exists():raise FileExistsError('preserve existing episode: '+str(root))
            rows.append(dict(arm=arm['id'],case=case,root=str(root),status='UNRUN'))
    if len({r['root'] for r in rows})!=count or len({a['id'] for a in arms})!=len(expected):
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
    prefixes={};prerequisite_cases=cases
    if preserved:prefixes,prerequisite_cases=preserved_sources(p,cases,common,bindings,study)
    student=prerequisite('student',checked(student_ref),prerequisite_cases)
    prerequisite('teacher',checked(teacher_ref),prerequisite_cases);prerequisite('django',checked(django_ref),cases)
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
    owned=student['restored_process']
    if restoration_ref is not None:
        previous=checked(restoration_ref,max_bytes=16*1024**2);owned=previous.get('restored_process',{})
        if (previous.get('status') not in {'STOPPED_RESTORE_REQUIRED','ALL96_RUNTIME_CONTEXT_RETURNED',
                'ALL32_FULL_BASELINES_RETURNED','ALL32_PRESERVED_RECOVERY_RETURNED','INCOMPLETE_OR_CLEANUP_FAILURE'} or
                any(previous.get(k) is not True for k in ('restored_healthy','shared35_unchanged','shared27_unchanged')) or
                any(previous.get(k) for k in ('restoration_error','server_cleanup_error','episode_cleanup_error','shared_identity_error')) or
                set(owned)!={'pid','start_ticks','exe','argv','cwd'} or type(owned['pid']) is not int or owned['pid']<=0 or
                not isinstance(owned['start_ticks'],str) or not owned['start_ticks'].isdigit() or
                any(owned[k]!=window['owned_process'][k] for k in ('argv','cwd','exe'))):
            raise ValueError('previous window does not prove a healthy, unchanged owned restoration')
        bindings[restoration_ref['path']]=restoration_ref['sha256']
    # Parent/adapter file hashes are intentionally deferred to explicit execution.
    if set(common['adapters'])!={'ordinary','recovery'}:raise ValueError('unexpected adapter variants')
    for ref in [common['parent_gguf'],common['HF_parent_binding'],*common['adapters'].values()]:
        private(ref['path'])
        if not re.fullmatch('[a-f0-9]{64}',ref['sha256']):raise ValueError('model binding SHA missing')
    return dict(plan=p,protocols=protocols,selections=selections,rows=rows,bindings=bindings,
                student=student,owned_process=owned,window=window,old_profile=old_profile,study=study,output=output,
                prefixes=prefixes)


def frozen(contract,epoch):
    if contract['study'].components()!=epoch or any(sha(path)!=digest for path,digest in contract['bindings'].items()):
        raise RuntimeError('frozen helper/protocol/source/components changed')


def qualified_actor_rounds(root,rounds,cap,stop):
    """Validate raw guard errors even on exit0; reject unrelated failures."""
    expected={}
    if cap:expected[403]='Forbidden'
    if stop:expected[400]='Bad Request'
    for row in rounds:
        number=row.get('round');code=row.get('exit')
        if type(number) is not int or number<1:raise ValueError('actor round identity missing')
        raw=Path(root)/('raw_'+str(number)+'.jsonl')
        if sha(raw)!=row.get('raw_sha256'):raise ValueError('actor round raw SHA differs')
        if type(code) is not int or code not in (0,1) or code==1 and not expected:
            raise ValueError('unqualified actor failure')
        rows=[json.loads(line) for line in raw.read_text().splitlines()]
        errors=[r for r in rows if r.get('type')=='error']
        if not errors and code==0:continue
        if not errors or rows[-1].get('type')!='error':raise ValueError('actor failure has no terminal relay refusal')
        for record in errors:
            error=record.get('error') or {};data=error.get('data') or {};status=data.get('statusCode')
            if error.get('name')!='APIError' or type(status) is not int or status not in expected or data.get('message')!=expected[status]:
                raise ValueError('actor failure includes an unqualified raw error')


def audit(study,root,receipt,manifest,*,caps=None):
    caps=CAPS if caps is None else caps
    root=Path(root);gates=receipt['model_relay_errors'];cap=bool(gates)
    if receipt['errors'] or any(e.get('type')!='ValueError' or e.get('detail') not in CAP_ERRORS for e in gates):
        raise ValueError('generic episode/transport/cleanup failure')
    if receipt['status'] not in {'RETURNED','EPISODE_TIMEOUT','NATIVE_TERMINAL_STOP'} or receipt['label']!='MULTITASK_CONTEXT_DEVELOPMENT':
        raise ValueError('unknown episode status/label')
    posts,actual=receipt['model_posts'],receipt['forwarded_model_posts']
    if any(type(n) is not int for n in (posts,actual,receipt['real_model_calls'])) or not 0<=actual<=posts<=caps['posts'] or receipt['real_model_calls']!=actual:
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
    qualified_actor_rounds(root,receipt['rounds'],cap,stop)
    requests=sorted((root/'requests').glob('*.json'));request_bytes=0
    if len(requests)!=posts:raise ValueError('budget request records missing')
    for path in requests:
        payload=json.loads(path.read_text())['forwarded'];body=path.with_suffix('.body').read_bytes()
        if 'lora' in payload or body!=json.dumps(payload,separators=(',',':')).encode():raise ValueError('actual body changed')
        request_bytes+=len(body)
    if request_bytes!=receipt['model_request_payload_bytes']:raise ValueError('request byte accounting differs')
    if (any(type(receipt.get(k)) is not int or receipt[k]<0 for k in ('model_request_payload_bytes','model_response_wire_bytes')) or
            request_bytes+receipt['model_response_wire_bytes']>caps['model_payload_bytes_combined']):
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


def require_free_owned_port(tables=Path('/proc/net')):
    """Read local socket tables; no endpoint probe and no unknown listener overlay."""
    for name in ('tcp','tcp6'):
        for line in (tables/name).read_text().splitlines()[1:]:
            fields=line.split()
            if fields[3]=='0A' and fields[1].rsplit(':',1)[-1]=='46B8':
                raise RuntimeError('unknown listener on18104; refuse restoration overlay')


def restore(h,original,child,ticket,output,window,stop_requested):
    """Collect only birth-ticket children; never signal or overlay an unknown PID."""
    result=dict(restored_healthy=False);restored_child=restore_ticket=None
    def check_shared():
        try:h.protected(window)
        except Exception as exc:
            result.setdefault('shared_identity_error',str(exc))
            result.setdefault('shared_identity_errors',[]).append(str(exc))
    try:
        if child is not None:
            h.stop_child(child,ticket);child.wait(timeout=15)
        if original is None:return result
        prior=h.proc(original['pid'])
        check_shared() # Shared drift stops research, not independent safe Q4 restoration.
        if prior is not None:
            if prior!=original:raise RuntimeError('original PID replaced; refuse overlay or signal')
            h.listener(original);health,_=h.get('/health',output/'retained_q4_health',1)
            if health['status']!=200:raise RuntimeError('retained Q4 health failed')
            result.update(restored_healthy=True,restored_process=original,original_not_released=True)
        else:
            if not stop_requested:raise RuntimeError('original disappeared without owned release')
            h.idle();require_free_owned_port()
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
        check_shared()
        if 'shared_identity_error' not in result:
            result.update(shared35_unchanged=True,shared27_unchanged=True)
    return result


def validate_preserved_outcome(contract,entry,receipt):
    prefix=contract.get('prefixes',{}).get(entry['case'])
    if prefix is None:return
    new=receipt.get('world_actions');total=receipt.get('total_world_action_count')
    if (type(new) is not int or not 0<=new<=prefix['additional_caps']['world_actions'] or
            type(total) is not int or total!=len(prefix['steps'])+new or
            receipt.get('final_world_state',{}).get('action_count')!=total or
            receipt.get('source_binding_charge_once')!=prefix['binding']):
        raise ValueError('preserved source/new action or formation accounting differs')


def prepare_episode(contract,entry,arm,profile_path,profile_sha,parent):
    """One shared preparation path; only the explicit source branch replays state."""
    study=contract['study'];root=Path(entry['root']);q=contract['protocols'][arm['context']]
    prefix=contract.get('prefixes',{}).get(entry['case'])
    ref=contract['selections'][entry['case']]['all7'] if arm['reference']=='all7' else None
    kwargs=dict(model_seed=17,runtime_profile=profile_path,runtime_profile_sha=profile_sha,
        reference_context=Path(ref['path']) if ref else None,reference_context_sha=ref['sha256'] if ref else None)
    if prefix is not None:kwargs['source_root']=prefix['root']
    m=study.prepare(root,Path(arm['protocol']['path']),arm['protocol']['sha256'],**kwargs)
    caps=prefix['additional_caps'] if prefix is not None else CAPS
    expected_source=str(prefix['root']) if prefix is not None else None
    if (m['source_root']!=expected_source or m['caps']!=caps or m['runtime_controls']!=q['runtime_controls'] or
            sha(root/'initial_reset.json')!=contract['selections'][entry['case']]['public_reset_sha256'] or
            m['runtime_profile_override']['gguf_verification']!=parent):raise ValueError('episode input/source/parent differs')
    if prefix is not None and (m['source_binding']!=prefix['binding'] or
            m.get('additional_recovery_source')!=contract['plan']['additional_recovery_source']):
        raise ValueError('preserved episode source metadata differs')
    return m,caps


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
            frozen(c,epoch);original=c['owned_process']
            if h.proc(original['pid'])!=original:raise RuntimeError('current Q4 differs from complete restoration identity')
            h.listener(original);h.protected(window);h.idle()
            common=c['protocols']['full'];_,parent=study.verified_gguf(common['parent_gguf']['path'],common['parent_gguf']['sha256'])
            # SHA verification can populate page cache on this unified-memory host.
            # This is the same advisory release as the previously qualified driver.
            fd=os.open(common['parent_gguf']['path'],os.O_RDONLY|os.O_NOFOLLOW)
            try:os.posix_fadvise(fd,0,0,os.POSIX_FADV_DONTNEED)
            finally:os.close(fd)
            if sha(original['exe'])!=c['old_profile']['server_executable_sha256']:raise ValueError('server executable changed')
            h.new(out/'ADMISSION.json',dict(owner_pid=os.getpid(),bindings=c['bindings'],components=epoch,
                  owned_process=original,parent_verification=parent,parent_cache_advice='POSIX_FADV_DONTNEED accepted; eviction not guaranteed',
                  protected35=window['protected35'],protected27=window['protected27']))
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
                        m,caps=prepare_episode(c,entry,arm,profile_path,profile_sha,parent)
                        frozen(c,epoch);entry['status']='EXECUTING';receipt=study.run_episode(active,sha(active/'manifest.json'))
                        entry.update(status='CLOSED_UNAUDITED',receipt_sha256=sha(active/'receipt.json'))
                        validate_preserved_outcome(c,entry,receipt)
                        entry.update(audit(study,active,receipt,m,caps=caps));entry['status']='CLOSED_AUDITED';event('case_audited',**entry)
                        frozen(c,epoch);h.protected(window);active=None
                    h.stop_child(child,ticket);child.wait(timeout=15);child=ticket=None
            result['status']=completed_status(p)
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
            result['status']=final_status(p,result)
            try:h.new(out/'RESULT.json',result);event('window_closed',status=result['status'],result_sha256=sha(out/'RESULT.json'))
            finally:
                for sig,handler in previous.items():signal.signal(sig,handler)
                fcntl.flock(lock,fcntl.LOCK_UN)
    return result


def _reference_probe_frame(value):
    """Remove experience content only, including inside the measured SDK quote layer."""
    if isinstance(value,str):
        if value.count('<prior_experience>')!=value.count('</prior_experience>') or value.count('<prior_experience>')>1:
            raise ValueError('ambiguous experience boundaries')
        return re.sub(r'(<prior_experience>)[\s\S]*?(</prior_experience>)',r'\1\2',value)
    if isinstance(value,list):return [_reference_probe_frame(v) for v in value]
    if isinstance(value,dict):return {k:_reference_probe_frame(v) for k,v in value.items()}
    return value


def _reference_probe_shape(p):
    cases=['nexttrain_look_%02d'%i for i in range(1,7)];rows=p.get('rows',[])
    if (p.get('schema')!='ALFWORLD_REFERENCE_COMPONENT_PROBE_V1' or p.get('planned_episodes')!=6 or
            p.get('max_forwarded_posts')!=768 or len(rows)!=6 or [e.get('case') for e in rows]!=cases):
        raise ValueError('fixed look6/768 plan required')
    attempts=[]
    for e in rows:
        root=Path(e['root']);match=re.fullmatch('attempt_v([1-9][0-9]*)',root.name)
        if (set(e)!={'case','root'} or not match or int(match[1])<6 or
                root!=ST/'cases'/e['case']/'ordinary_reset/student8b'/root.name):raise ValueError('fresh canonical B slot required')
        attempts.append(root.name)
    if len(set(attempts))!=1 or len({e['root'] for e in rows})!=6:raise ValueError('duplicate or mismatched attempts')
    return cases


def _install_reference_frame_guard(study,c):
    import copy
    factory=study.study_relay
    def aligned_relay(core,manifest,protocol,qualify):
        base=factory(core,manifest,protocol,qualify)
        class Relay(base):
            def prepare_payload(self,payload,index):
                incoming=copy.deepcopy(payload)
                payload=super().prepare_payload(payload,index)  # Includes measured whole-task quote-layer proof.
                if self.forwarded==0:
                    observed=json.loads((self.root/'observed_requests'/('%05d.json'%index)).read_text())
                    frame=dict(task=(self.root/'task.txt').read_text(),reset=json.loads((self.root/'initial_reset.json').read_text()),
                        handoff=json.loads((self.root/'handoff_public.json').read_text()),incoming=incoming,forwarded=payload,observed=observed)
                    try:matched=_reference_probe_frame(frame)==c['relay_input_frames'][manifest['case_id']]
                    except ValueError:matched=False
                    core.write_new(self.root/'reference_input_frame_checks'/('%05d.json'%index),dict(kind='PRE_SEND_INPUT_ONLY',
                        control=c['execution_controls']['frame_guard'],observed_request_sha256=sha(self.root/'observed_requests'/('%05d.json'%index)),
                        incoming_payload_sha256=hashlib.sha256(json.dumps(incoming,separators=(',',':')).encode()).hexdigest(),
                        prepared_payload_sha256=hashlib.sha256(json.dumps(payload,separators=(',',':')).encode()).hexdigest(),
                        matched=matched,actual_forward_or_native_outcome_claim=False))
                    if not matched:raise ValueError('first input frame changed beyond B experience')
                return payload
        return Relay
    study.study_relay=aligned_relay  # This checked study import only; neither payload nor old helpers are rewritten.


def reference_probe_execution_controls():
    parent=BASE/'next_train_source_v1'
    return dict(frame_guard=dict(path=str(Path(__file__).resolve()),sha256=sha(__file__),function='_install_reference_frame_guard',
            incoming_capture='prepare_payload argument after CBC sampling, before super; source reconstruction from frozen incoming+sampling'),
        world_guard=dict(path=str(parent/'trained_baseline_transfer_v1/RUN_OPERATOR_V1.py'),sha256='83fa07e1af89197307b11c7b529b410af23cc23fc47d2a9caa05a06fe78b5b2f',function='owned_start_world'),
        receipt_audit=dict(path=str(parent/'ordinary_history_train12_inputs_v1/RUN_HISTORY_CANDIDATE_V2.py'),sha256='5ff7c35771f67d752c80506d138052dd73ae1566ab35a485b79ca238a63e0496',function='audited'))


def _reference_probe_delivery_bindings(c,root,manifest):
    check_path=root/'reference_input_frame_checks/00001.json';binding_path=root/'controller_execution_binding.json'
    precheck=json.loads(check_path.read_text());request=json.loads((root/'requests/00001.json').read_text())
    incoming=dict(request['incoming']);incoming.update(manifest['sampling'])
    if (precheck['kind']!='PRE_SEND_INPUT_ONLY' or precheck['actual_forward_or_native_outcome_claim'] is not False or
            precheck['matched'] is not True or precheck['control']!=c['execution_controls']['frame_guard'] or
            precheck['incoming_payload_sha256']!=hashlib.sha256(json.dumps(incoming,separators=(',',':')).encode()).hexdigest() or
            precheck['prepared_payload_sha256']!=sha(root/'requests/00001.body') or
            precheck['observed_request_sha256']!=sha(root/'observed_requests/00001.json') or
            json.loads(binding_path.read_text())!=dict(plan=c['plan_ref'],execution_controls=c['execution_controls'])):
        raise ValueError('pre-send input/controller proof differs from actual saved wire')
    return {str(path):sha(path) for path in (check_path,binding_path)}


def check_reference_probe_plan(plan_path,plan_sha):
    """CPU/file-only qualification. Never prepare, inspect services, or hash weights."""
    from types import SimpleNamespace
    ref=dict(path=str(private(plan_path)),sha256=plan_sha);p=checked(ref);cases=_reference_probe_shape(p)
    bindings={ref['path']:plan_sha,str(Path(__file__).resolve()):sha(__file__)}
    def read(r):
        value=checked(r);bindings[r['path']]=r['sha256'];return value
    spec=read(p['inputs'])
    if p['inputs']['sha256']!='208ab2a96a6255c96ebb0aff49dbc515b53ed2be4d0122dce2b2f2c7567e9534':raise ValueError('wrong component inputs')
    alignment=read(spec['alignment_evidence'])
    prediction=Path(spec['reference_B']['path']).with_name('D_MECHANISM_PREDICTION_V2.json')
    if p['mechanism_prediction']!=dict(path=str(prediction),sha256='4360c93e5bf66f99d3b1a543478ecbeaaf5ff7b6ffb0ed3bf524e1edb2e0792e'):raise ValueError('frozen development prediction ref required')
    read(p['mechanism_prediction'])  # Hypothesis provenance, never an execution permission.
    if (spec['cases']!=cases or spec['new_episodes']!=6 or spec['max_new_posts']!=768 or
            spec['alignment_evidence']['sha256']!='141b93d9b9332cb37fb2812a2841d320bb07217768a88be368002f167acfc181' or
            alignment['strictly_aligned'] is not True):raise ValueError('component cohort/alignment differs')
    parent=BASE/'next_train_source_v1/ordinary_history_train12_inputs_v1'
    kernel=parent/'RUN_HISTORY_CANDIDATE_V2.py';kernel_sha='5ff7c35771f67d752c80506d138052dd73ae1566ab35a485b79ca238a63e0496'
    if sha(private(kernel))!=kernel_sha:raise ValueError('frozen H18 pure helpers changed')
    hist=load(kernel,'reference_probe_h18_pure');old=hist.original();bindings[str(kernel)]=kernel_sha;bindings[str(hist.ORIGINAL)]=hist.ORIGINAL_SHA
    study_path=HERE/'alfworld_context_study.py'
    if sha(study_path)!='716c4dd09ad7e673f75bb52b36708713d58c8dde00275784df41571453d535c6':raise ValueError('actor study differs from aligned H18')
    study=load(study_path,'reference_probe_study');epoch=study.components()
    if p['operator_sha256']!=sha(__file__) or p['components']!=epoch:raise ValueError('new operator/component epoch required')
    bindings.update(epoch);q=study.protocol(Path(spec['protocol']['path']),spec['protocol']['sha256']);read(spec['protocol'])
    controls=reference_probe_execution_controls()
    if p['execution_controls']!=controls:raise ValueError('explicit actual controller code bindings required beyond study components')
    if (spec['protocol']['sha256']!='77c04adf4224f3c9c098c387385f482f369ab4ef95f713b85ecc914af9d8aa23' or
            q['case_ids']!=cases or q['total_caps']!=CAPS or q['runtime_controls']!={'native_terminal_stop':True,'recent_tool_rounds':None} or
            q['experience_mode']!='reference_only' or q['generation_settings']!={'seed':17,'temperature':.2,'enable_thinking':False,'context':32768,'max_tokens':8192}):
        raise ValueError('fixed reference-only full/BF16 decoding/caps required')
    data={}
    for name,r in (('A',alignment['source_A']),('AB',alignment['source_all7']),('B',spec['reference_B'])):
        path=private(r['path']);data[name]=path.read_bytes()
        if sha(path)!=r['sha256']:raise ValueError('reference bytes changed')
        bindings[str(path)]=r['sha256']
    if (q['reference_context']!=spec['reference_B'] or sha(private(spec['reference_B']['path']))!='69d22b795c361c52683a293b4eb0c772a0ca1526e4aca845724205dc72af91bd' or
            data['AB'].count(data['A'])!=1 or data['AB'][9881:10689]!=data['A'] or data['B']!=data['AB'][:9881]+data['AB'][10689:]):
        raise ValueError('B must be the exact A subtraction, without other edits')
    closed={name:read({k:r[k] for k in ('path','sha256')}) for name,r in alignment['closed_results'].items()}
    for name,n,status in (('F',36,'ALL36_TRANSFER_RETURNED'),('H',18,'ALL18_HISTORY_RETURNED')):
        value=closed[name]
        if (value['status']!=status or value['completed_receipts']!=n or value['unknown_usage_model_posts']!=0 or
                any(value.get(k) for k in ('error','aggregation_errors','unrun','unclosed_attempts')) or
                any(value.get(k) is not True for k in ('restored_healthy','shared35_unchanged','shared27_unchanged'))):raise ValueError('prior batch not closed')
    admission=read(p['H_admission']);expected_admission=str(Path(alignment['closed_results']['H']['path']).with_name('ADMISSION.json'))
    if p['H_admission']['path']!=expected_admission or p['restored_process']!=closed['H']['restored_process']:raise ValueError('H18 restoration identity required')
    window={k:admission[k] for k in ('protected35','protected27')};h=helper();old_profile=read(dict(path=str(OLD_PROFILE),sha256=OLD_PROFILE_SHA))
    for path,digest in ((HELPER,HELPER_SHA),(WINDOW,WINDOW_SHA)):
        if sha(private(path))!=digest:raise ValueError('frozen controller support bytes changed')
        bindings[str(path)]=digest
    c=dict(plan=p,study=study,epoch=epoch,bindings=bindings,old=old,hist=hist,h=h,old_profile=old_profile,owned_process=p['restored_process'],
        window=window,comparison=SimpleNamespace(audit=audit),protocols={'B':q},texts={'B':data['B'].decode()},frozen_cases={},frames={},relay_input_frames={},
        output=private(p['output_root']),plan_ref=ref,closed_refs=alignment['closed_results'],execution_controls=controls)
    for case in cases:
        frames=[];relay_frames=[]
        for cell,source,attempt in (('00',closed['F'],1),('10',closed['H'],5),('11',closed['H'],4)):
            row=next(e for e in source['cases'] if e['case']==case and Path(e['root']).name=='attempt_v'+str(attempt))
            root=private(row['root']);info=alignment['cases'][case][cell]
            if row['status']!='CLOSED_AUDITED' or str(root)!=info['root']:raise ValueError('aligned prior slot differs')
            manifest=read(dict(path=str(root/'manifest.json'),sha256=row['manifest_sha256']));read(dict(path=str(root/'receipt.json'),sha256=row['receipt_sha256']))
            hist.frozen_runtime(manifest,q)
            for name,digest in info['files_sha256'].items():
                path=root/name
                if sha(path)!=digest:raise ValueError('aligned source input changed')
                bindings[str(path)]=digest
            request=json.loads((root/'requests/00001.json').read_text());observed=json.loads((root/'observed_requests/00001.json').read_text())
            frames.append(_reference_probe_frame(dict(task=(root/'task.txt').read_text(),reset=json.loads((root/'initial_reset.json').read_text()),
                handoff=json.loads((root/'handoff_public.json').read_text()),incoming=request['incoming'],forwarded=request['forwarded'],observed=observed)))
            hook_input=dict(request['incoming']);hook_input.update(manifest['sampling'])  # Exact frozen CBC7759 Handler ABI, with no exclusions.
            if hook_input!=request['forwarded']:raise ValueError('prior full-history sampling reconstruction differs from actual wire')
            relay_frames.append(dict(frames[-1],incoming=_reference_probe_frame(hook_input)))
            tools=hashlib.sha256(json.dumps(request['forwarded']['tools'],sort_keys=True,separators=(',',':')).encode()).hexdigest();hist.seed_frozen_tools(c,tools)
            if cell=='00':c['frozen_cases'][case]=dict(row=row,manifest=manifest)
        if any(f!=frames[0] for f in frames[1:]) or any(f!=relay_frames[0] for f in relay_frames[1:]):raise ValueError('non-experience task/state/request frame differs')
        c['frames'][case]=frames[0];c['relay_input_frames'][case]=relay_frames[0]
    c['rows']=[dict(e,id='B__'+e['case'],arm='B',policy='B',protocol=spec['protocol'],reference=spec['reference_B'],status='UNRUN') for e in p['rows']]
    if c['output'].parent!=Path(spec['reference_B']['path']).parent or c['output'].exists() or any(Path(e['root']).exists() for e in c['rows']):raise FileExistsError('fresh probe output/slots required')
    return c


def _reference_rows_complete(result,rows):
    n=len(rows);actual=result.get('total_actual_model_calls');posts=result.get('known_budget_model_posts')
    return (0<n<=6 and all(r['status']=='CLOSED_AUDITED' for r in rows) and result.get('completed_receipts')==n and
        all(result.get(k)==[] for k in ('aggregation_errors','unrun','unclosed_attempts')) and result.get('unknown_usage_model_posts')==0 and
        type(actual) is int and type(posts) is int and n<=actual<=posts<=n*CAPS['posts'] and result.get('known_actual_model_calls')==actual and
        not result.get('error') and not result.get('aggregation_error'))


def _finish_reference_rows(c,result,persist,event):
    old=c['old'];out=c['output'];rows=c['rows']
    unsafe=('episode_cleanup_error','server_cleanup_error','restoration_error','restore_child_cleanup_error','shared_identity_error','shared_identity_errors','world_cleanup_error','durable_write_error')
    safe=all(result.get(k) is True for k in ('restored_healthy','shared35_unchanged','shared27_unchanged')) and not any(k in result for k in unsafe)
    result.update(status='ALL%d_REFERENCE_COMPONENT_RETURNED'%len(rows) if safe and _reference_rows_complete(result,rows) else 'STOPPED_RESTORED' if safe else 'NEEDS_D_RECOVERY',
        resource_lease='RELEASE_AFTER_DURABLE_RESULT' if safe else 'HELD_FOR_D_INTERNAL_TAKEOVER')
    try:persist();old.write(out/'RESULT.json',result);event('window_closed',status=result['status'],result_sha256=sha(out/'RESULT.json'))
    except BaseException as exc:
        safe=False;result.update(status='NEEDS_D_RECOVERY',resource_lease='HELD_FOR_D_INTERNAL_TAKEOVER',durable_write_error=str(exc))
        for path in (out/'STATE.json',out/'RESULT.json'):
            try:old.write(path,result,replace=path.exists())
            except BaseException:pass
    if not safe:old.hold_for_d(out,ST/'model_resource.lock');raise RuntimeError('D hold returned')


def _execute_owned_reference_rows(c):
    """Finite reference rows in one owned BF16 window; no callbacks or scheduler."""
    if not c.get('authorized_release'):raise ValueError('new explicit reference-row release required')
    old=c['old'];h=c['h'];study=c['study'];out=c['output'];rows=c['rows'];q=c['protocols']['B'];original=c['owned_process']
    result=dict(status='STARTED',cases=rows,restored_healthy=False,training=0,judges=0,development_only=True,historical_formation_and_training_costs=None,
        execution_controls=c['execution_controls'],scientific_scope='Development component completion, not independent method validation')
    lock_path=ST/'model_resource.lock'
    if lock_path.is_symlink() or not lock_path.is_file():raise ValueError('existing shared lock required')
    lock=lock_path.open('r+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    if os.fstat(lock.fileno()).st_ino!=lock_path.stat().st_ino:raise ValueError('lock inode changed')
    owned=[];child=ticket=active=None;released=owns_output=False;started=time.monotonic();cancelled=False
    pool=study.task_pool();pool.start_world=lambda *a,**k:old.owned_start_world(pool,owned,*a,**k);study.task_pool=lambda:pool
    _install_reference_frame_guard(study,c)
    def event(kind,**data):
        try:
            with (out/'events.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps(dict(event=kind,utc=time.time(),**data))+'\n');f.flush();os.fsync(f.fileno())
        except BaseException as exc:result['durable_write_error']=str(exc);raise
    h.event=event
    def persist():
        try:old.write(out/'STATE.json',result,replace=(out/'STATE.json').exists())
        except BaseException as exc:result['durable_write_error']=str(exc);raise
    def cancel(*_):
        nonlocal cancelled
        if not cancelled:cancelled=True;raise KeyboardInterrupt('CANCEL_REQUESTED')
    previous={s:signal.signal(s,cancel) for s in (signal.SIGTERM,signal.SIGINT)}
    try:
        out.mkdir();owns_output=True;frozen(c,c['epoch'])
        if h.proc(original['pid'])!=original:raise RuntimeError('complete current Q4 identity differs')
        h.listener(original);h.protected(c['window']);h.idle()
        if sha(original['exe'])!=c['old_profile']['server_executable_sha256']:raise ValueError('server executable changed')
        _,parent=study.verified_gguf(q['parent_gguf']['path'],q['parent_gguf']['sha256'])
        fd=os.open(q['parent_gguf']['path'],os.O_RDONLY|os.O_NOFOLLOW)
        try:os.posix_fadvise(fd,0,0,os.POSIX_FADV_DONTNEED)
        finally:os.close(fd)
        old.write(out/'ADMISSION.json',dict(owner_pid=os.getpid(),bindings=c['bindings'],components=c['epoch'],execution_controls=c['execution_controls'],owned_process=original,protected35=c['window']['protected35'],protected27=c['window']['protected27'],parent_verification=parent))
        persist();released=True;h.stop_owned(original,escalate=False);require_free_owned_port();argv=h.server_argv(original['argv'],q['parent_gguf']['path'],None)
        with (out/'server.log').open('xb') as log:
            pending=[];saved={}
            try:
                for sig in previous:saved[sig]=signal.signal(sig,lambda sig,frame:pending.append(sig))
                child=subprocess.Popen(argv,cwd=original['cwd'],stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
                ticket=h.owned_child_ticket(child)
            finally:
                for sig,handler in saved.items():signal.signal(sig,handler)
            if pending:cancel()
            old.write(out/'SPAWN_TICKET.json',ticket);current=h.stable_child(child,dict(argv=argv,cwd=original['cwd'],exe=original['exe']),out/'startup_identity.jsonl',ticket)
            h.ready(child,current,out);h.listener(current);h.protected(c['window']);loaded,body=h.get('/lora-adapters',out/'loaded_adapters',1)
            if loaded['status']!=200:raise RuntimeError('loaded adapter HTTP failure')
            h.adapters(body,None)
            old.write(out/'RUNTIME_ADMISSION.json',dict(schema='owned_8b_runtime_admission_v1',status='OWNED_RESEARCH_RUNTIME_READY',process=current,gguf={k:q['parent_gguf'][k] for k in ('path','sha256')},model_alias='qwen3-8b-qual',active_lora=None,parent_hf_binding=q['HF_parent_binding'],loaded_adapter_receipt=loaded))
            profile=dict(schema='alfworld_owned_8b_runtime_profile_v1',variant='frozen',host='127.0.0.1',port=18104,model_id='qwen3-8b-qual',context=32768,output=8192,enable_thinking=False,gguf_path=q['parent_gguf']['path'],gguf_sha256=q['parent_gguf']['sha256'],server_executable=original['exe'],server_executable_sha256=c['old_profile']['server_executable_sha256'],parent_hf_binding=q['HF_parent_binding'],runtime_admission=dict(path=str(out/'RUNTIME_ADMISSION.json'),sha256=sha(out/'RUNTIME_ADMISSION.json')))
            old.write(out/'PROFILE.json',profile);profile_sha=sha(out/'PROFILE.json')
            for entry in rows:
                frozen(c,c['epoch']);h.listener(current);h.protected(c['window']);active=Path(entry['root'])
                if active.exists():raise FileExistsError('preserve appeared slot')
                entry['status']='PREPARING';persist();event('case_start',slot=entry['id'])
                m=study.prepare(active,Path(entry['protocol']['path']),entry['protocol']['sha256'],model_seed=17,runtime_profile=out/'PROFILE.json',runtime_profile_sha=profile_sha,reference_context=Path(entry['reference']['path']),reference_context_sha=entry['reference']['sha256'])
                c['hist'].prepared(c,entry,m,profile,profile_sha,parent)
                old.write(active/'controller_execution_binding.json',dict(plan=c['plan_ref'],execution_controls=c['execution_controls']))
                entry.update(status='EXECUTING',manifest_sha256=sha(active/'manifest.json'));persist();frozen(c,c['epoch'])
                receipt=study.run_episode(active,entry['manifest_sha256'])
                if any(e.get('cleanup')=='world' for e in receipt.get('errors',[])):result['world_cleanup_error']=receipt['errors']
                entry.update(status='CLOSED_UNAUDITED',receipt_sha256=sha(active/'receipt.json'));persist()
                if any(e.get('detail')=='first input frame changed beyond B experience' for e in receipt.get('model_relay_errors',[])):
                    entry.update(input_admission='REJECTED',scientific_outcome_eligible=False)
                    raise ValueError('INPUT_ADMISSION_REJECTED: first input frame changed')
                proof=c['hist'].audited(c,entry,m,receipt)
                request=json.loads((active/'requests/00001.json').read_text());observed=json.loads((active/'observed_requests/00001.json').read_text())
                frame=_reference_probe_frame(dict(task=(active/'task.txt').read_text(),reset=json.loads((active/'initial_reset.json').read_text()),handoff=json.loads((active/'handoff_public.json').read_text()),incoming=request['incoming'],forwarded=request['forwarded'],observed=observed))
                if frame!=c['frames'][entry['case']]:
                    entry.update(input_admission='REJECTED',scientific_outcome_eligible=False)
                    raise ValueError('INPUT_ADMISSION_REJECTED: actual raw input frame changed')
                proof['raw_bindings'].update(_reference_probe_delivery_bindings(c,active,m))
                entry.update(proof,status='CLOSED_AUDITED');persist();event('case_audited',slot=entry['id']);active=None
            frozen(c,c['epoch']);h.protected(c['window'])
    except BaseException as exc:
        result['error']=dict(type=type(exc).__name__,message=str(exc))
        if owns_output:event('queue_stopped',error=result['error'])
    finally:
        for sig in previous:signal.signal(sig,signal.SIG_IGN)
        if not owns_output:old.hold_for_d(out,lock_path);raise RuntimeError('D hold returned')
        try:
            if active is not None:h.cleanup_episode(active)
        except BaseException as exc:result['episode_cleanup_error']=str(exc)
        result['owned_worlds']=[]
        for record in owned:
            try:old.close_owned_world(record)
            except BaseException as exc:result['world_cleanup_error']=str(exc)
            proc=record.get('process');result['owned_worlds'].append(dict(root=record['root'],label=record['label'],pid=proc.pid if proc else None,exit=proc.poll() if proc else None))
            if record.get('cleanup_error'):result['world_cleanup_error']=record['cleanup_error']
        try:result.update(restore(h,original,child,ticket,out,c['window'],released))
        except BaseException as exc:result.update(restored_healthy=False,restoration_error=str(exc))
        try:result.update(aggregate(rows))
        except BaseException as exc:result.update(aggregation_error=str(exc),total_actual_model_calls=None,unknown_usage_model_posts=None)
        result['window_wall_seconds']=time.monotonic()-started;_finish_reference_rows(c,result,persist,event)
        fcntl.flock(lock,fcntl.LOCK_UN);lock.close()
        for sig,handler in previous.items():signal.signal(sig,handler)
    return result


def execute_reference_probe(plan_path,plan_sha,release_path,release_sha):
    c=check_reference_probe_plan(plan_path,plan_sha);release_ref=dict(path=str(private(release_path)),sha256=release_sha);release=checked(release_ref)
    expected=dict(schema='ALFWORLD_REFERENCE_COMPONENT_RELEASE_V1',status='RELEASED',plan=c['plan_ref'],operator_sha256=sha(__file__),
        components=c['epoch'],execution_controls=c['execution_controls'],restored_process=c['owned_process'],closed_results=c['closed_refs'],reference_B_sha256='69d22b795c361c52683a293b4eb0c772a0ca1526e4aca845724205dc72af91bd',
        episodes=6,maximum_forwarded_posts=768,input_bindings=c['bindings'],training=0,judges=0)
    if release!=expected:raise ValueError('new exact6/768 release required; old releases never carry')
    c['bindings'][release_ref['path']]=release_sha;c['authorized_release']=release_ref
    return _execute_owned_reference_rows(c)


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__);mode=parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--check',action='store_true');mode.add_argument('--execute',action='store_true')
    for name in ('plan','student-result','teacher-result','django-result'):
        parser.add_argument('--'+name,type=Path,required=True);parser.add_argument('--'+name+'-sha',required=True)
    parser.add_argument('--restoration-result',type=Path);parser.add_argument('--restoration-result-sha')
    parser.add_argument('--output',type=Path,required=True);args=parser.parse_args(argv)
    if bool(args.restoration_result)!=bool(args.restoration_result_sha):parser.error('restoration result and SHA must be supplied together')
    refs=[dict(path=str(getattr(args,k)),sha256=getattr(args,k+'_sha')) for k in ('plan','student_result','teacher_result','django_result')]
    restoration_ref=(dict(path=str(args.restoration_result),sha256=args.restoration_result_sha) if args.restoration_result else None)
    c=check_plan(*refs,args.output,restoration_ref=restoration_ref);helper() # Checked import only; never call the old execute/main.
    if args.check:
        frozen(c,c['study'].components())
        result=dict(status='CPU_CHECK_ONLY_NOT_EXECUTED',planned_episodes=c['plan']['planned_episodes'],model_calls=0,service_actions=0,
                    native_world_runs=0,parent_weight_hash_not_run=True)
    else:result=execute(c)
    print(json.dumps({k:result.get(k) for k in ('status','planned_episodes','completed_receipts','known_actual_model_calls',
        'total_actual_model_calls','unknown_usage_model_posts','restored_healthy') if k in result}))
    return 0 if args.check or result['status']==completed_status(c['plan']) else 1


if __name__=='__main__':
    raise SystemExit(main())
