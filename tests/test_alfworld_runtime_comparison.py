"""CPU-only controller contracts; every process, model and world boundary is fake."""
from contextlib import contextmanager
import copy
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT/'research/agent_frontier_portfolio_20261029/run_alfworld_runtime_comparison.py'
spec = importlib.util.spec_from_file_location('alfworld_runtime_comparison_contract',SCRIPT)
r = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = r
spec.loader.exec_module(r)
study_spec = importlib.util.spec_from_file_location('runtime_comparison_actual_study',SCRIPT.with_name('alfworld_context_study.py'))
actual_study = importlib.util.module_from_spec(study_spec)
study_spec.loader.exec_module(actual_study)

CASES = ['fake_case_%02d'%i for i in range(16)]
CAPS = {'posts':128,'seconds':1800,'world_actions':100,'model_payload_bytes_combined':64000000}


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path,value):
    path = Path(path)
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value),encoding='utf8')
    return {'path':str(path),'sha256':digest(path)}


def process(pid=101):
    return {'pid':pid,'start_ticks':'1234','exe':'/OWNED_FAKE/llama-server',
            'argv':['/OWNED_FAKE/llama-server','-m','/OWNED_FAKE/original.gguf','--port','18104'],
            'cwd':'/OWNED_FAKE'}


def student_result():
    return {'status':'ALL_FIVE_ARMS_RETURNED','completed_receipts':80,
            'carried_receipts':16,'new_receipts':64,'restored_healthy':True,
            'shared35_unchanged':True,'shared27_unchanged':True,
            'restored_process':process(),'evaluation_unknown_usage_posts':0,
            'total_policy_model_calls':80,
            'cases':[{'case':case,'arm':arm,'status':'RECORDED','receipt_sha256':'a'*64}
                     for arm in ('frozen','ordinary','recovery','history_all7','history_top1')
                     for case in CASES]}


def teacher_result():
    return {'status':'ALL16_DIRECT_TEACHER_RETURNED','completed_receipts':16,
            'error':None,'cleanup_error':None,'unclosed_attempts':[],'unrun':[],
            'training':0,'judges':0,'service_start_stop_actions':0,'EVAL_ONLY':True,
            'unknown_usage_posts':0,
            'results':[{'case':case,'root':'/OWNED_FAKE/'+case,'receipt_sha256':'a'*64,
                        'won':False,'scientific_cap':False,
                        'provider_usage':{'prompt_tokens':8,'completion_tokens':2,'total_tokens':10}}
                       for case in CASES]}


def django_result():
    return {'status':'GENERATION_RECORDED','task_count':1,'actual_forwarded_posts':1,
            'generation':{'agent_exit':1,'accounting':{'actual_forwarded_posts':1,
                          'integrity':{'passed':True}}},
            'scoring':{'semantics':{'fixed':False},'focus':{'exit':1},
                       'regression':{'exit':1},'public_probe':{'exit':1}}}


@contextmanager
def contract_fixture():
    """Small fake manifests and source text; there are deliberately no model files."""
    with tempfile.TemporaryDirectory(prefix='comparison-fake-') as tmp:
        base=Path(tmp).resolve();st=base/'context_study_v1'
        selected=[]
        for case in CASES:
            text=base/'contexts'/(case+'.txt');text.parent.mkdir(exist_ok=True)
            text.write_text('OWNED_FAKE_PUBLIC_ALL7_HISTORY '+case,encoding='utf8')
            selected.append({'case':case,'all7':{'path':str(text),'sha256':digest(text)},
                             'public_reset_sha256':hashlib.sha256(case.encode()).hexdigest()})
        selection=write(base/'CONTEXT_SELECTIONS.json',{'selections':selected})
        common={'schema':'HF8B_NATIVE_TERMINAL_CONTEXT_CONTROL_DEVELOPMENT_V2',
                'case_ids':CASES,'world_seed':17,'model_seeds':[17],'recent_steps':3,
                'ordinary_continuations':1,'context_margin_tokens':512,'total_caps':CAPS,
                'collection_caps':dict(CAPS,posts=32,seconds=600),
                'intended_stage':'ordinary_reset','intended_backend':'student8b',
                'context_selection':selection,'pool_path':str(base/'POOL.json'),'pool_sha256':'a'*64,
                'parent_gguf':{'path':str(base/'FAKE_PARENT.gguf'),'sha256':'b'*64},
                'HF_parent_binding':{'path':str(base/'HF_BINDING.json'),'sha256':'c'*64},
                'adapters':{variant:{'path':str(base/(variant+'.gguf')),'sha256':'d'*64}
                            for variant in ('ordinary','recovery')}}
        protocols={}
        for context in ('full','last3'):
            value=dict(common,runtime_controls={'native_terminal_stop':True,
                       'recent_tool_rounds':3 if context=='last3' else None})
            protocols[context]=write(base/('PROTOCOL_'+context+'.json'),value)
        descriptions=[('frozen_last3','frozen','none','last3'),
                      ('ordinary_last3','ordinary','none','last3'),
                      ('ordinary_full','ordinary','none','full'),
                      ('recovery_full','recovery','none','full'),
                      ('recovery_last3','recovery','none','last3'),
                      ('history_all7_last3','frozen','all7','last3')]
        arms=[dict(id=name,variant=variant,reference=reference,context=context,attempt=index+8,
                   protocol=protocols[context])
              for index,(name,variant,reference,context) in enumerate(descriptions)]
        plan={'schema':'ALFWORLD_RUNTIME_CONTEXT_BASELINE_PLAN_V2','case_ids':CASES,'arms':arms,
              'planned_episodes':96,'carried_episodes':0,'maximum_planned_model_posts':12288,
              'maximum_per_episode_caps':CAPS}
        plan_ref=write(base/'PLAN.json',plan)
        student_ref=write(base/'student/RESULT.json',student_result())
        teacher_ref=write(base/'teacher/RESULT.json',teacher_result())
        write(base/'teacher/ADMISSION.json',{'closed_student_result':student_ref})
        django_ref=write(base/'django/result.json',django_result())
        window=write(base/'window/ADMISSION.json',{'owned_process':dict(process(),state='S'),
                      'protected35':{'pid':500},'protected27':'OWNED_FAKE_CONTAINER_ID'})
        old_profile=write(base/'OLD_PROFILE.json',{'host':'127.0.0.1','port':18104,
                           'model_id':'qwen3-8b-qual','context':32768,'output':8192,
                           'server_executable_sha256':'e'*64})
        helper=base/'FAKE_HELPER.py';helper.write_text('raise AssertionError("never imported in check")\n')
        study=SimpleNamespace(runtime_controls=actual_study.runtime_controls,
                              components=mock.Mock(return_value={'FAKE_COMPONENT':'f'*64}))
        refs=[plan_ref,student_ref,teacher_ref,django_ref]
        with mock.patch.object(r,'ROOT',base),mock.patch.object(r,'ST',st), \
                mock.patch.object(r,'WINDOW',Path(window['path'])),mock.patch.object(r,'WINDOW_SHA',window['sha256']), \
                mock.patch.object(r,'OLD_PROFILE',Path(old_profile['path'])),mock.patch.object(r,'OLD_PROFILE_SHA',old_profile['sha256']), \
                mock.patch.object(r,'HELPER',helper),mock.patch.object(r,'HELPER_SHA',digest(helper)):
            yield SimpleNamespace(base=base,st=st,plan=plan,refs=refs,protocols=protocols,study=study,
                                  output=base/'FRESH_OUTPUT',old_profile=old_profile)


def check_fixture(f):
    return r.check_plan(*f.refs,f.output,study=f.study)


def full_baseline_fixture(f):
    """Post-hoc controls refer to a complete96; none of its episodes are carried."""
    origin_plan=copy.deepcopy(f.plan)
    origin_ref=write(f.base/'origin96/PLAN.json',origin_plan)
    rows=[]
    for arm in origin_plan['arms']:
        for case in CASES:
            root=f.st/'cases'/case/'ordinary_reset/student8b'/('attempt_v'+str(arm['attempt']))
            receipt=write(root/'receipt.json',dict(case_id=case,backend='student8b',stage='ordinary_reset',
                                                  won=False,fake_arm=arm['id']))
            rows.append(dict(arm=arm['id'],case=case,status='CLOSED_AUDITED',won=False,
                             root=str(root),receipt_sha256=receipt['sha256']))
    closure=dict(status='ALL96_RUNTIME_CONTEXT_RETURNED',cases=rows,completed_receipts=96,
                 carried_episodes=0,training=0,judges=0,restored_healthy=True,
                 shared35_unchanged=True,shared27_unchanged=True,restored_process=process(202),
                 unknown_usage_model_posts=0,unrun=[],unclosed_attempts=[],aggregation_errors=[])
    closure_ref=write(f.base/'origin96/RESULT.json',closure)
    plan=dict(schema='ALFWORLD_FULL_BASELINE_EXTENSION_PLAN_V1',case_ids=list(CASES),
              arms=[dict(id=name,variant='frozen',reference=reference,context='full',attempt=attempt,
                         protocol=f.protocols['full'])
                    for name,reference,attempt in [('frozen_full','none',30),('history_all7_full','all7',31)]],
              planned_episodes=32,carried_episodes=0,maximum_planned_model_posts=4096,
              maximum_per_episode_caps=CAPS,origin_context_plan=origin_ref,origin_context_result=closure_ref)
    f.plan=plan;f.refs[0]=write(Path(f.refs[0]['path']),plan)
    return closure_ref


class FullBaselineExtensionTests(unittest.TestCase):
    def test_exact_two_full_controls_are_bound_to_closed96_and_fresh(self):
        with contract_fixture() as f:
            previous=full_baseline_fixture(f)
            with mock.patch.object(r.subprocess,'Popen',side_effect=AssertionError('CPU check only')):
                c=r.check_plan(*f.refs,f.output,study=f.study,restoration_ref=previous)
            self.assertEqual(len(c['rows']),32)
            self.assertEqual([a['id'] for a in c['plan']['arms']],['frozen_full','history_all7_full'])
            self.assertTrue(all(a['context']=='full' and a['variant']=='frozen' for a in c['plan']['arms']))
            self.assertEqual(c['owned_process'],process(202))
            self.assertEqual(c['bindings'][previous['path']],previous['sha256'])
            self.assertFalse(f.output.exists())
            self.assertTrue(all(not Path(row['root']).exists() for row in c['rows']))

    def test_partial_or_changed_origin_and_reused_attempt_are_rejected(self):
        for mode in ('missing_restore','missing_origin','status','missing_case','duplicate_case','unaudited',
                     'bad_receipt','unknown_cost','changed_cases','reused_attempt','different_full_protocol',
                     'missing_receipt_file','tampered_receipt_file','wrong_receipt_case'):
            with self.subTest(mode=mode),contract_fixture() as f:
                previous=full_baseline_fixture(f)
                plan=copy.deepcopy(f.plan)
                closure=json.loads(Path(previous['path']).read_text())
                if mode=='missing_origin':plan.pop('origin_context_plan')
                elif mode=='status':closure['status']='STARTED'
                elif mode=='missing_case':closure['cases'].pop()
                elif mode=='duplicate_case':closure['cases'][-1]=copy.deepcopy(closure['cases'][0])
                elif mode=='unaudited':closure['cases'][0]['status']='CLOSED_UNAUDITED'
                elif mode=='bad_receipt':closure['cases'][0]['receipt_sha256']='invalid'
                elif mode=='unknown_cost':closure['unknown_usage_model_posts']=1
                elif mode=='changed_cases':plan['case_ids']=list(reversed(CASES))
                elif mode=='reused_attempt':plan['arms'][0]['attempt']=8
                elif mode=='different_full_protocol':
                    value=json.loads(Path(f.protocols['full']['path']).read_text())
                    value['HF_parent_binding']['sha256']='e'*64
                    other=write(f.base/'different_full.json',value)
                    for arm in plan['arms']:arm['protocol']=other
                elif mode in ('missing_receipt_file','tampered_receipt_file','wrong_receipt_case'):
                    path=Path(closure['cases'][0]['root'])/'receipt.json'
                    if mode=='missing_receipt_file':path.unlink()
                    elif mode=='tampered_receipt_file':path.write_text('changed')
                    else:
                        value=json.loads(path.read_text());value['case_id']='different_case'
                        new=write(path,value);closure['cases'][0]['receipt_sha256']=new['sha256']
                previous=write(Path(previous['path']),closure)
                plan['origin_context_result']=previous
                f.refs[0]=write(Path(f.refs[0]['path']),plan)
                with self.assertRaises((ValueError,KeyError,RuntimeError)):
                    r.check_plan(*f.refs,f.output,study=f.study,
                                 restoration_ref=None if mode=='missing_restore' else previous)

    def test_only_the_fixed32_full_design_is_accepted(self):
        for mode in ('last3','extra_arm','missing_arm','budget','count','carried','variant','reference',
                     'float_count','float_budget','bool_carried'):
            with self.subTest(mode=mode),contract_fixture() as f:
                previous=full_baseline_fixture(f);plan=copy.deepcopy(f.plan)
                if mode=='last3':plan['arms'][0]['context']='last3'
                elif mode=='extra_arm':plan['arms'].append(copy.deepcopy(plan['arms'][0]))
                elif mode=='missing_arm':plan['arms'].pop()
                elif mode=='budget':plan['maximum_planned_model_posts']=4097
                elif mode=='count':plan['planned_episodes']=96
                elif mode=='carried':plan['carried_episodes']=1
                elif mode=='variant':plan['arms'][0]['variant']='recovery'
                elif mode=='float_count':plan['planned_episodes']=32.0
                elif mode=='float_budget':plan['maximum_planned_model_posts']=4096.0
                elif mode=='bool_carried':plan['carried_episodes']=False
                else:plan['arms'][1]['reference']='none'
                f.refs[0]=write(Path(f.refs[0]['path']),plan)
                with self.assertRaises(ValueError):
                    r.check_plan(*f.refs,f.output,study=f.study,restoration_ref=previous)

    def test_analysis_reference_is_frozen_without_reading_any_models(self):
        with contract_fixture() as f:
            previous=full_baseline_fixture(f)
            analysis=write(f.base/'ANALYSIS.json',{'scope':'OWNED_FAKE_FIXED_ANALYSIS'})
            f.plan['analysis_contract']=analysis;f.refs[0]=write(Path(f.refs[0]['path']),f.plan)
            c=r.check_plan(*f.refs,f.output,study=f.study,restoration_ref=previous)
            self.assertEqual(c['bindings'][analysis['path']],analysis['sha256'])
            previous_data=json.loads(Path(previous['path']).read_text())
            old_receipt=Path(previous_data['cases'][0]['root'])/'receipt.json'
            self.assertEqual(c['bindings'][str(old_receipt)],digest(old_receipt))
            Path(analysis['path']).write_text('changed')
            with self.assertRaisesRegex(RuntimeError,'frozen'):
                r.frozen(c,c['study'].components())

    def test_large_closed_json_has_a_separate_finite_limit_not_a_weight_exception(self):
        with contract_fixture() as f:
            previous=full_baseline_fixture(f)
            closure=json.loads(Path(previous['path']).read_text());closure['fake_metadata_padding']='x'*10_000_001
            previous=write(Path(previous['path']),closure);f.plan['origin_context_result']=previous
            f.refs[0]=write(Path(f.refs[0]['path']),f.plan)
            c=r.check_plan(*f.refs,f.output,study=f.study,restoration_ref=previous)
            self.assertEqual(len(c['rows']),32)
            closure['fake_metadata_padding']='x'*17_000_000
            previous=write(Path(previous['path']),closure);f.plan['origin_context_result']=previous
            f.refs[0]=write(Path(f.refs[0]['path']),f.plan)
            with self.assertRaises(ValueError):
                r.check_plan(*f.refs,f.output,study=f.study,restoration_ref=previous)

    def test_final_status_never_labels32_as96_or_an_incomplete32_as_closed(self):
        with contract_fixture() as f:
            full_baseline_fixture(f)
            complete=dict(status='ALL32_FULL_BASELINES_RETURNED',completed_receipts=32,restored_healthy=True,
                          unclosed_attempts=[],aggregation_errors=[],unrun=[])
            self.assertEqual(r.final_status(f.plan,complete),'ALL32_FULL_BASELINES_RETURNED')
            for key,value in [('completed_receipts',31),('unrun',['missing']),('aggregation_errors',['bad']),
                              ('episode_cleanup_error','pending'),('shared_identity_error','changed')]:
                with self.subTest(key=key):
                    self.assertEqual(r.final_status(f.plan,dict(complete,**{key:value})),
                                     'INCOMPLETE_OR_CLEANUP_FAILURE')
            self.assertEqual(r.final_status(f.plan,dict(complete,restored_healthy=False)),
                             'RESTORATION_NOT_VERIFIED')


class FrozenPlanTests(unittest.TestCase):
    def test_explicit_closed_restoration_updates_only_owned_process_and_is_bound(self):
        with contract_fixture() as f:
            previous={'status':'STOPPED_RESTORE_REQUIRED','restored_healthy':True,
                      'shared35_unchanged':True,'shared27_unchanged':True,
                      'restored_process':process(202),
                      'error':{'type':'KeyboardInterrupt','message':'CANCEL_REQUESTED'}}
            ref=write(f.base/'prior_window/RESULT.json',previous)
            c=r.check_plan(*f.refs,f.output,study=f.study,restoration_ref=ref)
            self.assertEqual(c['owned_process'],process(202))
            self.assertEqual(c['student']['restored_process'],process(101))
            self.assertEqual(c['bindings'][ref['path']],ref['sha256'])
            self.assertFalse(f.output.exists())

    def test_restoration_override_requires_terminal_healthy_unchanged_cleanup(self):
        for mode in ('live','unhealthy','shared','cleanup','wrong_argv','bad_pid','bad_ticks'):
            with self.subTest(mode=mode),contract_fixture() as f:
                v={'status':'STOPPED_RESTORE_REQUIRED','restored_healthy':True,
                   'shared35_unchanged':True,'shared27_unchanged':True,'restored_process':process(202)}
                if mode=='live':v['status']='STARTED'
                elif mode=='unhealthy':v['restored_healthy']=False
                elif mode=='shared':v['shared27_unchanged']=False
                elif mode=='cleanup':v['episode_cleanup_error']='OWNED_FAKE pending child'
                elif mode=='wrong_argv':v['restored_process']['argv']=['OWNED_FAKE different model']
                elif mode=='bad_pid':v['restored_process']['pid']=True
                else:v['restored_process']['start_ticks']='not-a-birth-ticket'
                ref=write(f.base/'prior_window/RESULT.json',v)
                with self.assertRaises(ValueError):
                    r.check_plan(*f.refs,f.output,study=f.study,restoration_ref=ref)

    def test_check_accepts_only_the_exact_fresh_six_arm_cases_without_external_actions(self):
        with contract_fixture() as f:
            real_sha=r.sha
            def small_sha(path):
                self.assertFalse(str(path).endswith('.gguf'),'check may not hash a model/adapter')
                return real_sha(path)
            with mock.patch.object(r,'sha',side_effect=small_sha), \
                    mock.patch.object(r,'helper',side_effect=AssertionError('no lifecycle import in check')), \
                    mock.patch.object(r.subprocess,'run',side_effect=AssertionError('no process/Docker/help in check')), \
                    mock.patch.object(r.subprocess,'Popen',side_effect=AssertionError('no service in check')):
                checked=check_fixture(f)
            self.assertEqual(len(checked['rows']),96)
            self.assertEqual(len({row['root'] for row in checked['rows']}),96)
            self.assertEqual([arm['id'] for arm in checked['plan']['arms']],
                ['frozen_last3','ordinary_last3','ordinary_full','recovery_full','recovery_last3','history_all7_last3'])
            self.assertTrue(all(row['status']=='UNRUN' for row in checked['rows']))
            self.assertFalse(f.output.exists())
            self.assertFalse((f.st/'cases').exists())

    def test_duplicate_case_root_arm_or_unknown_schema_is_rejected(self):
        for mode in ('case','root','arm_id','schema','old128'):
            with self.subTest(mode=mode),contract_fixture() as f:
                plan=copy.deepcopy(f.plan)
                if mode=='case':plan['case_ids'][-1]=plan['case_ids'][0]
                elif mode=='root':plan['arms'][1]['attempt']=plan['arms'][0]['attempt']
                elif mode=='arm_id':plan['arms'][1]['id']=plan['arms'][0]['id']
                elif mode=='schema':plan['schema']='UNREVIEWED_FUTURE_SCHEMA'
                else:plan.update(planned_episodes=128,maximum_planned_model_posts=16384)
                f.refs[0]=write(Path(f.refs[0]['path']),plan)
                with self.assertRaises((ValueError,RuntimeError)):check_fixture(f)

    def test_unknown_runtime_control_or_caps_and_asymmetric_protocols_are_rejected(self):
        for mode in ('unknown_control','integer_stop','bad_rounds','caps','protocol_schema','asymmetry'):
            with self.subTest(mode=mode),contract_fixture() as f:
                ref=f.protocols['last3'];value=json.loads(Path(ref['path']).read_text())
                if mode=='unknown_control':value['runtime_controls']['hidden_summary']=True
                elif mode=='integer_stop':value['runtime_controls']['native_terminal_stop']=1
                elif mode=='bad_rounds':value['runtime_controls']['recent_tool_rounds']=True
                elif mode=='caps':value['total_caps']=dict(CAPS,posts=129)
                elif mode=='protocol_schema':value['schema']='UNKNOWN_CHILD_PROTOCOL'
                else:value['context_margin_tokens']=513
                changed=write(Path(ref['path']),value)
                plan=copy.deepcopy(f.plan)
                for arm in plan['arms']:
                    if arm['context']=='last3':arm['protocol']=changed
                f.refs[0]=write(Path(f.refs[0]['path']),plan)
                with self.assertRaises((ValueError,RuntimeError)):check_fixture(f)

    def test_changed_hashes_existing_episode_and_output_are_preserved(self):
        for mode in ('hash','episode','output'):
            with self.subTest(mode=mode),contract_fixture() as f:
                if mode=='hash':Path(f.refs[0]['path']).write_text('{}')
                elif mode=='episode':
                    root=f.st/'cases'/CASES[0]/'ordinary_reset/student8b/attempt_v8'
                    root.mkdir(parents=True);(root/'unique.txt').write_text('PRESERVE_ME')
                else:f.output.mkdir()
                with self.assertRaises((ValueError,RuntimeError,FileExistsError)):check_fixture(f)
                if mode=='episode':self.assertEqual((root/'unique.txt').read_text(),'PRESERVE_ME')

    def test_original_profile_context_and_port_are_fixed(self):
        for change in ({'context':65536},{'port':18105},{'output':16384}):
            with self.subTest(change=change),contract_fixture() as f:
                value=json.loads(Path(f.old_profile['path']).read_text());value.update(change)
                ref=write(Path(f.old_profile['path']),value)
                with mock.patch.object(r,'OLD_PROFILE_SHA',ref['sha256']),self.assertRaises((ValueError,RuntimeError)):
                    check_fixture(f)

    def test_cli_check_never_calls_lifecycle_or_episode_boundaries(self):
        with contract_fixture() as f:
            forbidden=lambda *args,**kwargs:(_ for _ in ()).throw(AssertionError('check crossed execution boundary'))
            names=('proc','exact','listener','protected','idle','stop_owned','owned_child_ticket','stable_child',
                   'stop_child','ready','get','adapters','server_argv','cleanup_episode','offline_help')
            lifecycle=SimpleNamespace(**{name:mock.Mock(side_effect=forbidden) for name in names})
            for name in ('verified_gguf','runtime_file','prepare','run_episode'):
                setattr(f.study,name,mock.Mock(side_effect=forbidden))
            argv=['--check','--output',str(f.output)]
            for name,ref in zip(('plan','student-result','teacher-result','django-result'),f.refs):
                argv += ['--'+name,ref['path'],'--'+name+'-sha',ref['sha256']]
            with mock.patch.object(r,'load',return_value=f.study),mock.patch.object(r,'helper',return_value=lifecycle), \
                    mock.patch.object(r.subprocess,'run',side_effect=forbidden), \
                    mock.patch.object(r.subprocess,'Popen',side_effect=forbidden), \
                    mock.patch('sys.stdout',new_callable=io.StringIO) as stdout:
                self.assertEqual(r.main(argv),0)
            summary=json.loads(stdout.getvalue())
            self.assertEqual(summary['status'],'CPU_CHECK_ONLY_NOT_EXECUTED')
            self.assertEqual(summary['planned_episodes'],96)
            self.assertLess(len(stdout.getvalue()),1000)
            for name in names:getattr(lifecycle,name).assert_not_called()
            for name in ('verified_gguf','runtime_file','prepare','run_episode'):getattr(f.study,name).assert_not_called()
            self.assertFalse(f.output.exists())


@contextmanager
def receipt_fixture(*,won=False,terminal=True):
    """Actual small body/hash receipts, with only the native validator replaced."""
    with tempfile.TemporaryDirectory(prefix='receipt-fake-') as tmp:
        root=Path(tmp).resolve()
        controls={'native_terminal_stop':True,'recent_tool_rounds':3}
        manifest={'case_id':'fake_case','runtime_controls':controls}
        write(root/'manifest.json',manifest)
        state={'observation':'OWNED_FAKE_NATIVE_OBSERVATION','score':1.0 if won else 0.0,
               'done':terminal,'won':won,'action_count':1,'admissible_commands':['look']}
        (root/'execute_world.jsonl').write_text('OWNED_FAKE_NATIVE_LOG\n',encoding='utf8')
        (root/'raw_1.jsonl').write_text('{"OWNED_FAKE":true}\n')
        if terminal:
            (root/'raw_1.jsonl').write_text(json.dumps({'type':'error','error':{'name':'APIError',
                'data':{'statusCode':400,'message':'Bad Request'}}})+'\n')
        payload={'model':'OWNED_FAKE','messages':[{'role':'user','content':'PUBLIC_GOAL_ANCHOR'}]}
        write(root/'requests/00001.json',{'incoming':payload,'forwarded':payload})
        request_body=json.dumps(payload,separators=(',',':')).encode()
        (root/'requests/00001.body').write_bytes(request_body)
        usage={'prompt_tokens':8,'completion_tokens':2,'total_tokens':10,
               'prompt_tokens_details':{'cached_tokens':5}}
        response_body=b'data: '+json.dumps({'usage':usage}).encode()+b'\n\n'
        response_path=root/'responses/00001.body';response_path.parent.mkdir()
        response_path.write_bytes(response_body)
        response={'status':200,'complete':True,'body_bytes':len(response_body),
                  'body_sha256':digest(response_path),'usage':usage}
        write(root/'responses/00001.body.receipt.json',response)
        witness={'path':str(root/'execute_world.jsonl'),'sha256':digest(root/'execute_world.jsonl'),
                 'bytes':(root/'execute_world.jsonl').stat().st_size,'row':3,'state':state,
                 'episode_sha256':'a'*64}
        reason='native_won' if won else 'native_done_unwon'
        stop=dict(witness,reason=reason,forwarded_posts_at_stop=1) if terminal else None
        if terminal:write(root/'controller_stop.json',stop)
        receipt={'status':'NATIVE_TERMINAL_STOP' if terminal else 'RETURNED',
                 'label':'MULTITASK_CONTEXT_DEVELOPMENT','errors':[],'model_relay_errors':[],
                 'model_posts':1,'forwarded_model_posts':1,'real_model_calls':1,
                 'manifest_sha256':digest(root/'manifest.json'),'runtime_controls':controls,
                 'final_world_state':state,'won':won,'controller_stop':stop,
                 'controller_stops':[{'type':'ControllerStop','reason':reason}] if terminal else [],
                 'rounds':[{'round':1,'exit':1 if terminal else 0,'raw_sha256':digest(root/'raw_1.jsonl')}],
                 'model_request_payload_bytes':len(request_body),'model_response_wire_bytes':len(response_body)+40,
                 'response_receipts':[response],
                 'provider_usage':{k:usage[k] for k in ('prompt_tokens','completion_tokens','total_tokens')},
                 'unknown_usage_model_posts':0,'provider_cached_input_tokens':5}
        write(root/'receipt.json',receipt)
        study=SimpleNamespace(public=actual_study.public,native_world_witness=mock.Mock(return_value=witness))
        yield SimpleNamespace(root=root,manifest=manifest,receipt=receipt,study=study,
                              witness=witness,response=response,response_path=response_path)


def save_receipt(f):
    write(f.root/'receipt.json',f.receipt)


def write_raw_refusal(f,status,*,extra=None,message=None,name='APIError'):
    rows=list(extra or [])+[{'type':'error','error':{'name':name,'data':{'statusCode':status,
        'message':message or {403:'Forbidden',400:'Bad Request'}.get(status,'OWNED_FAKE_OTHER_ERROR')}}}]
    path=f.root/'raw_1.jsonl';path.write_text(''.join(json.dumps(row)+'\n' for row in rows))
    f.receipt['rounds'][0]['raw_sha256']=digest(path)


class RuntimeAuditTests(unittest.TestCase):
    def test_permanent_terminal_http_requires_witness_and_rejects_old_retryable_409(self):
        for terminal,status,message in ((False,400,'Bad Request'),(True,409,'Conflict')):
            with self.subTest(terminal=terminal,status=status),receipt_fixture(won=terminal,terminal=terminal) as f:
                write_raw_refusal(f,status,message=message)
                save_receipt(f)
                with self.assertRaisesRegex(ValueError,'actor failure'):
                    r.audit(f.study,f.root,f.receipt,f.manifest)
        with receipt_fixture(won=False,terminal=True) as f:
            result=r.audit(f.study,f.root,f.receipt,f.manifest)
            self.assertFalse(result['won'])
            self.assertTrue(result['done_unwon'])

    def test_zero_exit_unknown_top_level_errors_stop_and_keep_native_state_and_costs(self):
        for won in (False,True):
            for earlier in (False,True):
                with self.subTest(won=won,earlier=earlier),receipt_fixture(won=won,terminal=won) as f:
                    f.receipt['rounds'][0]['exit']=0
                    write_raw_refusal(f,400,name='OWNED_FAKE_UnknownError',message='OWNED_FAKE opaque failure')
                    if earlier:
                        path=f.root/'raw_1.jsonl';path.write_text(path.read_text()+'{"type":"step_finish"}\n')
                        f.receipt['rounds'][0]['raw_sha256']=digest(path)
                    save_receipt(f);before=(f.root/'receipt.json').read_bytes()
                    with self.assertRaisesRegex(ValueError,'actor failure'):
                        r.audit(f.study,f.root,f.receipt,f.manifest)
                    totals=r.aggregate([{'root':str(f.root),'status':'CLOSED_UNAUDITED'}])
                    self.assertEqual(totals['known_actual_model_calls'],1)
                    self.assertEqual(totals['provider_usage_known_subtotals'],{'prompt_tokens':8,'completion_tokens':2,'total_tokens':10})
                    self.assertIsNone(totals['total_actual_model_calls'])
                    self.assertEqual((f.root/'receipt.json').read_bytes(),before)
                    self.assertEqual(json.loads(before)['final_world_state'],f.witness['state'])

    def test_zero_exit_normal_tool_feedback_and_qualified_relay_errors_remain_valid(self):
        for mode in ('tool_feedback','cap403','stop400'):
            with self.subTest(mode=mode),receipt_fixture(won=mode=='stop400',terminal=mode=='stop400') as f:
                f.receipt['rounds'][0]['exit']=0
                if mode=='tool_feedback':
                    path=f.root/'raw_1.jsonl';path.write_text(json.dumps({'type':'tool_use','state':{
                        'status':'error','error':'OWNED_FAKE ordinary tool feedback'}})+'\n')
                    f.receipt['rounds'][0]['raw_sha256']=digest(path)
                elif mode=='cap403':
                    f.receipt['model_relay_errors']=[{'type':'ValueError','detail':'episode model budget closed'}]
                    write_raw_refusal(f,403)
                save_receipt(f)
                self.assertEqual(r.audit(f.study,f.root,f.receipt,f.manifest)['scientific_cap'],mode=='cap403')

    def test_cap_or_terminal_witness_does_not_mask_killed_actor_and_preserves_bills(self):
        for kind,code in (('cap',137),('won',137),('done_unwon',-9)):
            with self.subTest(kind=kind),receipt_fixture(won=kind=='won',terminal=kind!='cap') as f:
                f.receipt['rounds'][0]['exit']=code
                if kind=='cap':
                    f.receipt['model_relay_errors']=[{'type':'ValueError',
                        'detail':'native template estimate plus output/margin exceeds context'}]
                    write_raw_refusal(f,403)
                save_receipt(f);before=(f.root/'receipt.json').read_bytes()
                with self.assertRaisesRegex(ValueError,'actor failure'):
                    r.audit(f.study,f.root,f.receipt,f.manifest)
                rows=[{'root':str(f.root),'status':'CLOSED_UNAUDITED'}]
                totals=r.aggregate(rows)
                self.assertEqual((totals['known_actual_model_calls'],totals['known_budget_model_posts']),(1,1))
                self.assertEqual(totals['provider_usage_known_subtotals'],{'prompt_tokens':8,'completion_tokens':2,'total_tokens':10})
                self.assertIsNone(totals['total_actual_model_calls']);self.assertIsNone(totals['unknown_usage_model_posts'])
                self.assertNotIn('scientific_cap',rows[0])
                self.assertEqual((f.root/'receipt.json').read_bytes(),before)
                self.assertEqual(json.loads(before)['final_world_state'],f.witness['state'])

    def test_only_normal_zero_and_qualified_guard_one_exits_are_accepted(self):
        for terminal,won,code,cap in ((False,False,0,False),(False,False,1,True),
                                     (True,True,1,False),(True,False,1,False)):
            with self.subTest(terminal=terminal,won=won,code=code,cap=cap),receipt_fixture(won=won,terminal=terminal) as f:
                f.receipt['rounds'][0]['exit']=code
                if cap:
                    f.receipt['model_relay_errors']=[{'type':'ValueError','detail':'episode model budget closed'}]
                    write_raw_refusal(f,403)
                save_receipt(f)
                self.assertEqual(r.audit(f.study,f.root,f.receipt,f.manifest)['scientific_cap'],cap)

    def test_guard_exit_requires_bound_terminal_api_error_without_other_opaque_errors(self):
        for mode in ('raw_sha','not_terminal','no_error','wrong_status','wrong_message','wrong_name','earlier_opaque','wrong_round'):
            with self.subTest(mode=mode),receipt_fixture(won=True) as f:
                if mode=='raw_sha':f.receipt['rounds'][0]['raw_sha256']='0'*64
                elif mode=='not_terminal':
                    path=f.root/'raw_1.jsonl';path.write_text(path.read_text()+'{"type":"step_finish"}\n')
                    f.receipt['rounds'][0]['raw_sha256']=digest(path)
                elif mode=='no_error':
                    path=f.root/'raw_1.jsonl';path.write_text('{"type":"step_finish"}\n')
                    f.receipt['rounds'][0]['raw_sha256']=digest(path)
                elif mode=='wrong_status':write_raw_refusal(f,403)
                elif mode=='wrong_message':write_raw_refusal(f,400,message='OWNED_FAKE different failure')
                elif mode=='wrong_name':write_raw_refusal(f,400,name='OWNED_FAKE_OtherError')
                elif mode=='earlier_opaque':write_raw_refusal(f,400,extra=[{'type':'error','error':{
                    'name':'UnknownError','data':{'message':'OWNED_FAKE unrelated crash'}}}])
                else:f.receipt['rounds'][0]['round']=0
                save_receipt(f)
                with self.assertRaises(ValueError):r.audit(f.study,f.root,f.receipt,f.manifest)

    def test_ordinary_returned_receipt_cannot_replace_the_fresh_native_outcome(self):
        with receipt_fixture(terminal=False) as f:
            f.study.native_world_witness.return_value=dict(f.witness,
                state=dict(f.witness['state'],action_count=2,observation='NEWER_OWNED_FAKE_NATIVE_STATE'))
            with self.assertRaises((ValueError,RuntimeError)):
                r.audit(f.study,f.root,f.receipt,f.manifest)
            f.study.native_world_witness.assert_called_once_with(f.root,f.manifest)

    def test_verified_native_win_and_done_unwon_remain_distinct_despite_actor_error_exit(self):
        for won in (False,True):
            with self.subTest(won=won),receipt_fixture(won=won) as f:
                result=r.audit(f.study,f.root,f.receipt,f.manifest)
                self.assertEqual(result['won'],won)
                self.assertEqual(result['done_unwon'],not won)
                self.assertEqual(result['controller_reason'],'native_won' if won else 'native_done_unwon')
                self.assertEqual((result['actual_model_calls'],result['budget_model_posts']),(1,1))
                self.assertEqual(result['provider_usage'],{'prompt_tokens':8,'completion_tokens':2,'total_tokens':10})
                self.assertEqual(result['cached_input_tokens'],5)
                self.assertIn(str(f.root/'requests/00001.body'),result['raw_bindings'])
                f.study.native_world_witness.assert_called_once_with(f.root,f.manifest)

    def test_forged_or_stale_terminal_reason_state_count_or_signal_is_rejected(self):
        for mode in ('missing','reason','state','count','stale','state_not_terminal','signal','witness_file'):
            with self.subTest(mode=mode),receipt_fixture(won=True) as f:
                if mode=='missing':f.receipt['controller_stop']=None
                elif mode=='reason':f.receipt['controller_stop']['reason']='native_done_unwon'
                elif mode=='state':f.receipt['final_world_state']=dict(f.receipt['final_world_state'],action_count=2)
                elif mode=='count':f.receipt['controller_stop']['forwarded_posts_at_stop']=0
                elif mode=='stale':f.study.native_world_witness.return_value=dict(f.witness,sha256='b'*64)
                elif mode=='state_not_terminal':f.study.native_world_witness.return_value=dict(f.witness,state=dict(f.witness['state'],done=False))
                elif mode=='signal':f.receipt['controller_stops']=[{'type':'ValueError','reason':'native_won'}]
                else:write(f.root/'controller_stop.json',dict(f.receipt['controller_stop'],reason='forged'))
                save_receipt(f)
                with self.assertRaises((ValueError,RuntimeError)):r.audit(f.study,f.root,f.receipt,f.manifest)

    def test_generic_relay_or_episode_failures_are_never_laundered_as_terminal_success(self):
        for key,value in (
            ('errors',[{'type':'RuntimeError','error':'OWNED_FAKE cleanup failed'}]),
            ('model_relay_errors',[{'type':'ValueError','detail':'unexpected exposed tool'}]),
            ('model_relay_errors',[{'type':'OSError','detail':'episode model budget closed'}]),
            ('status','UNKNOWN_INTERFACE_SUCCESS'),
        ):
            with self.subTest(key=key,value=value),receipt_fixture(won=True) as f:
                f.receipt[key]=value;save_receipt(f)
                with self.assertRaises((ValueError,RuntimeError)):r.audit(f.study,f.root,f.receipt,f.manifest)

    def test_wire_body_byte_bill_and_cache_subset_are_checked(self):
        for mode in ('body','bytes','cache','provider_total','unknown_count','unqualified_exit'):
            with self.subTest(mode=mode),receipt_fixture(terminal=False) as f:
                if mode=='body':(f.root/'requests/00001.body').write_bytes(b'FORGED_BODY')
                elif mode=='bytes':f.receipt['model_request_payload_bytes']+=1
                elif mode=='cache':
                    f.response['usage']['prompt_tokens_details']['cached_tokens']=9
                    write(f.root/'responses/00001.body.receipt.json',f.response)
                    f.receipt['provider_cached_input_tokens']=9
                elif mode=='provider_total':f.receipt['provider_usage']['total_tokens']=11
                elif mode=='unknown_count':f.receipt['unknown_usage_model_posts']=1
                else:f.receipt['rounds'][0]['exit']=1
                save_receipt(f)
                with self.assertRaises((ValueError,RuntimeError)):r.audit(f.study,f.root,f.receipt,f.manifest)

    def test_missing_provider_usage_stops_audit_but_keeps_original_call_costs(self):
        with receipt_fixture(terminal=False) as f:
            f.response['usage']=None;write(f.root/'responses/00001.body.receipt.json',f.response)
            f.receipt.update(provider_usage={'prompt_tokens':0,'completion_tokens':0,'total_tokens':0},
                             unknown_usage_model_posts=1,provider_cached_input_tokens=None)
            save_receipt(f)
            before=(f.root/'receipt.json').read_bytes()
            with self.assertRaisesRegex(ValueError,'unknown usage'):
                r.audit(f.study,f.root,f.receipt,f.manifest)
            totals=r.aggregate([{'root':str(f.root),'status':'CLOSED_UNAUDITED'}])
            self.assertEqual(totals['known_actual_model_calls'],1)
            self.assertEqual(totals['known_budget_model_posts'],1)
            self.assertEqual(totals['unknown_usage_model_posts_known_subtotal'],1)
            self.assertIsNone(totals['total_actual_model_calls'])
            self.assertIsNone(totals['unknown_usage_model_posts'])
            self.assertEqual((f.root/'receipt.json').read_bytes(),before)

    def test_missing_cache_is_reported_without_adding_it_to_input_or_imputing_zero(self):
        with receipt_fixture(terminal=False) as f:
            f.response['usage'].pop('prompt_tokens_details')
            write(f.root/'responses/00001.body.receipt.json',f.response)
            f.receipt['provider_cached_input_tokens']=None;save_receipt(f)
            result=r.audit(f.study,f.root,f.receipt,f.manifest)
            self.assertIsNone(result['cached_input_tokens'])
            self.assertEqual(result['provider_usage']['prompt_tokens'],8)


class AggregateTests(unittest.TestCase):
    def test_partial_closed_unfinished_and_unrun_roots_keep_totals_unknown(self):
        with receipt_fixture(terminal=False) as f:
            unfinished=f.root/'unfinished';unfinished.mkdir()
            unrun=f.root/'unrun'
            rows=[{'root':str(f.root),'status':'CLOSED_AUDITED'},
                  {'root':str(unfinished),'status':'EXECUTING'},
                  {'root':str(unrun),'status':'UNRUN'}]
            result=r.aggregate(rows)
            self.assertEqual(result['completed_receipts'],1)
            self.assertEqual(result['known_actual_model_calls'],1)
            self.assertEqual(result['known_budget_model_posts'],1)
            self.assertEqual(result['provider_usage_known_subtotals']['total_tokens'],10)
            self.assertEqual(result['unclosed_attempts'],[str(unfinished)])
            self.assertEqual(result['unrun'],[str(unrun)])
            self.assertIsNone(result['total_actual_model_calls'])
            self.assertIsNone(result['unknown_usage_model_posts'])

    def test_entirely_unrun_cohort_never_claims_zero_unknown_total(self):
        with tempfile.TemporaryDirectory() as tmp:
            rows=[{'root':str(Path(tmp)/case),'status':'UNRUN'} for case in CASES]
            result=r.aggregate(rows)
            self.assertEqual(result['completed_receipts'],0)
            self.assertEqual(result['known_actual_model_calls'],0)
            self.assertIsNone(result['total_actual_model_calls'])
            self.assertIsNone(result['unknown_usage_model_posts'])
            self.assertEqual(len(result['unrun']),16)

    def test_changed_receipt_sha_stops_aggregation_without_replacing_original(self):
        with receipt_fixture() as f:
            before=(f.root/'receipt.json').read_bytes()
            result=r.aggregate([{'root':str(f.root),'status':'CLOSED_AUDITED','receipt_sha256':'f'*64}])
            self.assertTrue(result['aggregation_errors'])
            self.assertIsNone(result['total_actual_model_calls'])
            self.assertEqual((f.root/'receipt.json').read_bytes(),before)

    def test_malformed_cost_fields_keep_valid_subtotals_and_unknown_full_totals(self):
        for change in ({'provider_usage':None},{'provider_usage':{'prompt_tokens':'unknown','completion_tokens':2,'total_tokens':10}},
                       {'real_model_calls':None},{'unknown_usage_model_posts':None}):
            with self.subTest(change=change),receipt_fixture() as f:
                f.receipt.update(change);save_receipt(f)
                result=r.aggregate([{'root':str(f.root),'status':'CLOSED_AUDITED'}])
                self.assertTrue(result['aggregation_errors'])
                self.assertIsNone(result['total_actual_model_calls'])
                self.assertIsNone(result['unknown_usage_model_posts'])
                self.assertEqual(result['known_budget_model_posts'],1)

    def test_duplicate_accounting_roots_and_unowned_receipts_are_rejected(self):
        with receipt_fixture() as f:
            row={'root':str(f.root),'status':'CLOSED_AUDITED'}
            with self.assertRaisesRegex(ValueError,'duplicate'):
                r.aggregate([dict(row),dict(row)])
            result=r.aggregate([dict(row,status='UNRUN')])
            self.assertTrue(result['aggregation_errors'])
            self.assertEqual(result['completed_receipts'],0)
            self.assertIsNone(result['total_actual_model_calls'])


def fake_lifecycle(original):
    """Mocks only: invoking these helpers never touches a process or endpoint."""
    ticket={'pid':202,'start_ticks':'5678','ppid':303,'pgid':202}
    return SimpleNamespace(
        stop_child=mock.Mock(),proc=mock.Mock(return_value=original),protected=mock.Mock(),
        listener=mock.Mock(),get=mock.Mock(return_value=({'status':200},b'OWNED_FAKE_HEALTH')),
        idle=mock.Mock(),owned_child_ticket=mock.Mock(return_value=ticket),
        new=mock.Mock(side_effect=lambda path,value:write(path,value)),
        stable_child=mock.Mock(return_value=dict(original,pid=202,start_ticks='5678')),
        ready=mock.Mock(),stop_owned=mock.Mock())


class OwnedPortGuardTests(unittest.TestCase):
    def test_unknown_ipv4_or_ipv6_listener_blocks_without_any_socket_probe(self):
        header='sl local_address rem_address st\n'
        for family in ('tcp','tcp6'):
            with self.subTest(family=family),tempfile.TemporaryDirectory() as tmp:
                tables=Path(tmp)
                for name in ('tcp','tcp6'):(tables/name).write_text(header)
                r.require_free_owned_port(tables)
                (tables/family).write_text(header+'0: 00000000:46B8 00000000:0000 0A\n')
                with self.assertRaisesRegex(RuntimeError,'unknown listener'):r.require_free_owned_port(tables)


class RestoreOwnershipTests(unittest.TestCase):
    def setUp(self):
        patcher=mock.patch.object(r,'require_free_owned_port',create=True)
        self.port_guard=patcher.start();self.addCleanup(patcher.stop)

    def test_preexisting_shared_mismatch_still_restores_safely_and_keeps_the_failure(self):
        for persists in (False,True):
            with self.subTest(persists=persists),tempfile.TemporaryDirectory() as tmp:
                original=process();h=fake_lifecycle(original);h.proc.return_value=None
                child=mock.Mock(name='OWNED_FAKE_OLD_CHILD');ticket={'OWNED_FAKE_TICKET':True}
                restored=mock.Mock(name='OWNED_FAKE_RESTORED_CHILD')
                failure=RuntimeError('OWNED_FAKE preexisting shared mismatch')
                h.protected.side_effect=[failure,failure if persists else None]
                with mock.patch.object(r.subprocess,'Popen',return_value=restored) as popen:
                    result=r.restore(h,original,child,ticket,Path(tmp),{},True)
                self.assertTrue(result['restored_healthy'])
                self.assertIn('preexisting shared mismatch',result['shared_identity_error'])
                self.assertNotIn('shared35_unchanged',result)
                self.assertNotIn('restoration_error',result)
                h.stop_child.assert_called_once_with(child,ticket);child.wait.assert_called_once_with(timeout=15)
                h.idle.assert_called_once();self.port_guard.assert_called();popen.assert_called_once()
                self.assertEqual(popen.call_args.args[0],original['argv'])
                self.assertEqual(popen.call_args.kwargs['cwd'],original['cwd'])
                h.protected.assert_called();restored.wait.assert_not_called()

    def test_preexisting_shared_mismatch_retains_exact_original_without_duplicate_restart(self):
        original=process();h=fake_lifecycle(original)
        h.protected.side_effect=RuntimeError('OWNED_FAKE persistent shared mismatch')
        with tempfile.TemporaryDirectory() as tmp,mock.patch.object(r.subprocess,'Popen') as popen:
            result=r.restore(h,original,None,None,Path(tmp),{},False)
        self.assertTrue(result['restored_healthy']);self.assertTrue(result['original_not_released'])
        self.assertIn('persistent shared mismatch',result['shared_identity_error'])
        self.assertNotIn('shared35_unchanged',result)
        h.listener.assert_called_once_with(original);h.get.assert_called_once()
        h.stop_child.assert_not_called();h.stop_owned.assert_not_called();popen.assert_not_called()
        self.port_guard.assert_not_called()

    def test_unknown_owned_port_listener_blocks_restore_even_with_shared_mismatch(self):
        original=process();h=fake_lifecycle(original);h.proc.return_value=None
        h.protected.side_effect=RuntimeError('OWNED_FAKE shared mismatch')
        self.port_guard.side_effect=RuntimeError('unknown listener on18104')
        with tempfile.TemporaryDirectory() as tmp,mock.patch.object(r.subprocess,'Popen') as popen:
            result=r.restore(h,original,None,None,Path(tmp),{},True)
        self.assertFalse(result['restored_healthy'])
        self.assertIn('shared mismatch',result['shared_identity_error'])
        self.assertIn('unknown listener',result['restoration_error']['message'])
        h.stop_owned.assert_not_called();h.stop_child.assert_not_called();popen.assert_not_called()

    def test_exact_retained_original_is_checked_without_start_or_stop(self):
        original=process();h=fake_lifecycle(original)
        with tempfile.TemporaryDirectory() as tmp,mock.patch.object(r.subprocess,'Popen') as popen:
            result=r.restore(h,original,None,None,Path(tmp),{'OWNED_FAKE_WINDOW':True},False)
        self.assertTrue(result['restored_healthy'])
        self.assertTrue(result['original_not_released'])
        self.assertEqual(result['restored_process'],original)
        h.listener.assert_called_once_with(original)
        self.assertEqual(h.get.call_args.args[0],'/health')
        h.stop_child.assert_not_called();h.stop_owned.assert_not_called();popen.assert_not_called()

    def test_replaced_original_pid_is_never_signalled_or_overlaid(self):
        for field,value in (('start_ticks','DIFFERENT_BIRTH'),('exe','/UNKNOWN/exe'),
                            ('argv',['UNKNOWN_ARGV']),('cwd','/UNKNOWN/cwd')):
            with self.subTest(field=field),tempfile.TemporaryDirectory() as tmp:
                original=process();h=fake_lifecycle(original);h.proc.return_value=dict(original,**{field:value})
                with mock.patch.object(r.subprocess,'Popen') as popen:
                    result=r.restore(h,original,None,None,Path(tmp),{},True)
                self.assertFalse(result['restored_healthy'])
                self.assertIn('PID replaced',result['restoration_error']['message'])
                h.stop_owned.assert_not_called();h.stop_child.assert_not_called()
                h.get.assert_not_called();popen.assert_not_called()

    def test_unknown_replacement_birth_ticket_blocks_restoration(self):
        original=process();h=fake_lifecycle(original);h.proc.return_value=None
        child=mock.Mock(name='OWNED_FAKE_REPLACEMENT_CHILD');ticket={'UNKNOWN_TICKET':True}
        h.stop_child.side_effect=RuntimeError('unknown birth ticket; do not signal')
        with tempfile.TemporaryDirectory() as tmp,mock.patch.object(r.subprocess,'Popen') as popen:
            result=r.restore(h,original,child,ticket,Path(tmp),{},True)
        self.assertFalse(result['restored_healthy'])
        self.assertIn('unknown birth ticket',result['restoration_error']['message'])
        h.stop_child.assert_called_once_with(child,ticket)
        h.proc.assert_not_called();popen.assert_not_called()

    def test_missing_original_without_owned_release_is_not_restarted(self):
        original=process();h=fake_lifecycle(original);h.proc.return_value=None
        with tempfile.TemporaryDirectory() as tmp,mock.patch.object(r.subprocess,'Popen') as popen:
            result=r.restore(h,original,None,None,Path(tmp),{},False)
        self.assertFalse(result['restored_healthy'])
        self.assertIn('without owned release',result['restoration_error']['message'])
        popen.assert_not_called()

    def test_owned_child_is_collected_before_exact_argv_cwd_restoration(self):
        original=process();h=fake_lifecycle(original);h.proc.return_value=None
        child=mock.Mock(name='OWNED_FAKE_PRIOR_CHILD');old_ticket={'pid':150,'start_ticks':'450'}
        restored=mock.Mock(name='OWNED_FAKE_RESTORED_CHILD');events=[]
        h.stop_child.side_effect=lambda *args:events.append('collect_old')
        h.idle.side_effect=lambda:events.append('idle')
        def launch(*args,**kwargs):events.append('launch_restore');return restored
        with tempfile.TemporaryDirectory() as tmp,mock.patch.object(r.subprocess,'Popen',side_effect=launch) as popen:
            result=r.restore(h,original,child,old_ticket,Path(tmp),{},True)
            self.assertTrue((Path(tmp)/'RESTORE_SPAWN_TICKET.json').exists())
        self.assertTrue(result['restored_healthy'])
        self.assertEqual(events,['collect_old','idle','launch_restore'])
        h.stop_child.assert_called_once_with(child,old_ticket);child.wait.assert_called_once_with(timeout=15)
        self.assertEqual(popen.call_args.args[0],original['argv'])
        self.assertEqual(popen.call_args.kwargs['cwd'],original['cwd'])
        self.assertTrue(popen.call_args.kwargs['start_new_session'])
        h.owned_child_ticket.assert_called_once_with(restored)
        expected=h.stable_child.call_args.args[1]
        self.assertEqual(expected,{k:original[k] for k in ('argv','cwd','exe')})
        h.ready.assert_called_once()
        self.assertEqual(result['restored_process']['pid'],202)

    def test_failed_or_interrupted_restoration_collects_its_own_spawn_without_retry(self):
        for failure in (RuntimeError('OWNED_FAKE load failed'),KeyboardInterrupt('OWNED_FAKE interrupt')):
            with self.subTest(failure=type(failure).__name__),tempfile.TemporaryDirectory() as tmp:
                original=process();h=fake_lifecycle(original);h.proc.return_value=None
                restored=mock.Mock(name='OWNED_FAKE_FAILED_RESTORE');h.ready.side_effect=failure
                with mock.patch.object(r.subprocess,'Popen',return_value=restored) as popen:
                    result=r.restore(h,original,None,None,Path(tmp),{},True)
                self.assertFalse(result['restored_healthy'])
                self.assertEqual(result['restoration_error']['type'],type(failure).__name__)
                popen.assert_called_once()
                h.stop_child.assert_called_once_with(restored,h.owned_child_ticket.return_value)
                restored.wait.assert_called_once_with(timeout=15)

    def test_protected_identity_change_after_verified_restore_does_not_kill_restored_q4(self):
        original=process();h=fake_lifecycle(original);h.proc.return_value=None
        restored=mock.Mock(name='OWNED_FAKE_HEALTHY_RESTORED_CHILD')
        h.protected.side_effect=[None,RuntimeError('OWNED_FAKE shared identity changed')]
        with tempfile.TemporaryDirectory() as tmp,mock.patch.object(r.subprocess,'Popen',return_value=restored):
            result=r.restore(h,original,None,None,Path(tmp),{},True)
        self.assertTrue(result['restored_healthy'])
        self.assertIn('shared identity changed',result['shared_identity_error'])
        self.assertNotIn('shared35_unchanged',result)
        self.assertEqual(result['restored_process']['pid'],202)
        h.stop_child.assert_not_called();restored.wait.assert_not_called()


class PrerequisiteTests(unittest.TestCase):
    def test_closed_failed_baseline_is_valid_without_requiring_model_success(self):
        before = django_result()
        r.prerequisite('django',before,CASES)
        self.assertEqual(before,django_result())
        r.prerequisite('student',student_result(),CASES)
        r.prerequisite('teacher',teacher_result(),CASES)

    def test_live_incomplete_or_unaccounted_prerequisites_are_rejected(self):
        changes = {
            'student':[{'status':'STARTED'},{'completed_receipts':79},{'restored_healthy':False},
                       {'shared35_unchanged':False},{'shared27_unchanged':False},
                       {'evaluation_unknown_usage_posts':1}],
            'teacher':[{'status':'STARTED'},{'completed_receipts':15},{'unrun':['fake_case_15']},
                       {'unclosed_attempts':['/OWNED_FAKE/live']},{'cleanup_error':{'message':'failure'}},
                       {'error':{'message':'failure'}},{'training':1},{'EVAL_ONLY':False}],
            'django':[{'status':'GENERATION_FAILED'},{'task_count':2},{'actual_forwarded_posts':0},
                      {'actual_forwarded_posts':True},{'scoring':None}]
        }
        fixtures = {'student':student_result,'teacher':teacher_result,'django':django_result}
        for kind,variants in changes.items():
            for change in variants:
                with self.subTest(kind=kind,change=change),self.assertRaises((ValueError,RuntimeError)):
                    r.prerequisite(kind,dict(fixtures[kind](),**change),CASES)

    def test_django_requires_matching_integrity_and_boolean_scored_semantics(self):
        for mutate in (
            lambda value:value['generation']['accounting'].update(actual_forwarded_posts=2),
            lambda value:value['generation']['accounting']['integrity'].update(passed=False),
            lambda value:value['scoring']['semantics'].update(fixed=None),
            lambda value:value['scoring'].pop('regression'),
        ):
            value = django_result();mutate(value)
            with self.subTest(value=value),self.assertRaises((ValueError,RuntimeError)):
                r.prerequisite('django',value,CASES)


if __name__ == '__main__':
    unittest.main()



def preserved_fixture(f):
    cases=CASES[:8]
    old=write(f.base/'preserved/old_protocol.json',dict(case_ids=CASES))
    src=write(f.base/'preserved/source_contract.json',dict(schema='ALFWORLD_ADDITIONAL_RECOVERY_V1',
        source_protocol=old,source_bindings={case:dict(root=str(f.st/'cases'/case/'ordinary_reset/student8b/attempt_v2')) for case in cases}))
    prefixes={}
    native=[]
    for case in cases:
        file=write(f.base/'preserved'/case/'source.json',dict(case=case,won=False))
        prefix=dict(root=Path(json.loads(Path(src['path']).read_text())['source_bindings'][case]['root']),
            steps=[dict(action='look')]*2,public_prefix_sha256=hashlib.sha256(case.encode()).hexdigest(),
            binding={file['path']:file['sha256']},additional_caps=dict(CAPS,posts=32,seconds=600,world_actions=98),
            budget_semantics='ADDITIONAL_PHASE_NOT_OLD_REMAINING_POSTS',world_step_cap=100,
            receipt=dict(real_model_calls=128),manifest=dict(protocol_sha256=old['sha256']))
        prefixes[case]=prefix
        native.append(dict(case=case,status='PUBLIC_REPLAY_EQUAL',source_actions=2,remaining_world_actions=98,
            public_prefix_sha256=prefix['public_prefix_sha256'],owned_world_stopped=True,
            final_state=dict(won=False,done=False,action_count=2)))
    replay=write(f.base/'preserved/native.json',dict(schema='additional_failure_prefix_native_replay_v1',
        status='QUALIFIED_PUBLIC_REPLAY',source_protocol=src,rows=native,model_calls=0,training=0,replayed_actions=16,
        pool=dict(path=str(f.base/'POOL.json'),sha256='a'*64)))
    q=json.loads(Path(f.protocols['full']['path']).read_text())
    selection=json.loads(Path(q['context_selection']['path']).read_text())
    selection['selections']=[x for x in selection['selections'] if x['case'] in cases]
    q['context_selection']=write(f.base/'preserved/contexts.json',selection)
    q.update(schema='HF8B_PRESERVED_FAILURE_CONTEXT_DEVELOPMENT_V1',intended_stage='preserved_recovery',
        case_ids=cases,additional_recovery_source=src)
    proto=write(f.base/'preserved/PROTOCOL.json',q)
    plan=dict(schema='ALFWORLD_PRESERVED_RECOVERY_COMPARISON_PLAN_V1',case_ids=cases,
        arms=[dict(id=name,variant=variant,reference=reference,context='full',attempt=40+i,protocol=proto)
              for i,(name,variant,reference) in enumerate([
                ('frozen_full','frozen','none'),('ordinary_full','ordinary','none'),
                ('recovery_full','recovery','none'),('history_all7_full','frozen','all7')])],
        additional_recovery_source=src,source_native_replay=replay,
        planned_episodes=32,carried_episodes=0,maximum_planned_model_posts=1024,
        maximum_per_episode_caps=dict(CAPS,posts=32,seconds=600))
    f.plan=plan;f.refs[0]=write(Path(f.refs[0]['path']),plan)
    f.study.load_source_prefix=mock.Mock(side_effect=lambda study,case,root:copy.deepcopy(prefixes[case]))
    restoration=write(f.base/'preserved/restoration.json',dict(status='ALL32_FULL_BASELINES_RETURNED',
        restored_healthy=True,shared35_unchanged=True,shared27_unchanged=True,restored_process=process(202)))
    return SimpleNamespace(cases=cases,prefixes=prefixes,source=src,replay=replay,protocol=proto,restoration=restoration)


class PreservedRecoveryControllerTests(unittest.TestCase):
    def check(self,f,g):return r.check_plan(*f.refs,f.output,study=f.study,restoration_ref=g.restoration)

    def test_exact_four_arms_same_eight_sources_and_new_budget(self):
        with contract_fixture() as f:
            g=preserved_fixture(f);c=self.check(f,g)
            self.assertEqual(len(c['rows']),32);self.assertEqual(set(c['prefixes']),set(g.cases))
            self.assertEqual(c['owned_process'],process(202))
            self.assertEqual({Path(x['root']).parts[-3] for x in c['rows']},{'drop_full','keep_full'})
            for prefix in g.prefixes.values():
                for path,h in prefix['binding'].items():self.assertEqual(c['bindings'][path],h)
            self.assertEqual(c['plan']['maximum_planned_model_posts'],1024)
            self.assertEqual(r.completed_status(c['plan']),'ALL32_PRESERVED_RECOVERY_RETURNED')
            self.assertEqual(c['student']['completed_receipts'],80)

    def test_missing_provenance_or_wrong_finite_design_rejected(self):
        for mode in ('missing_source','missing_replay','wrong_cases','wrong_posts','wrong_arms','wrong_child','no_restore'):
            with self.subTest(mode=mode),contract_fixture() as f:
                g=preserved_fixture(f)
                if mode=='missing_source':del f.plan['additional_recovery_source']
                elif mode=='missing_replay':del f.plan['source_native_replay']
                elif mode=='wrong_cases':f.plan['case_ids'][-1]=CASES[9]
                elif mode=='wrong_posts':f.plan['maximum_planned_model_posts']=4096
                elif mode=='wrong_arms':f.plan['arms'][0]['context']='last3'
                elif mode=='wrong_child':
                    q=json.loads(Path(g.protocol['path']).read_text());q.pop('additional_recovery_source');new=write(g.protocol['path'],q)
                    for a in f.plan['arms']:a['protocol']=new
                f.refs[0]=write(f.refs[0]['path'],f.plan)
                with self.assertRaises((ValueError,KeyError)):
                    r.check_plan(*f.refs,f.output,study=f.study,restoration_ref=None if mode=='no_restore' else g.restoration)

    def test_native_replay_and_prefix_cannot_be_swapped(self):
        for mode in ('not_closed','won','wrong_prefix','wrong_actions','wrong_source','zero_actions','changed_root'):
            with self.subTest(mode=mode),contract_fixture() as f:
                g=preserved_fixture(f);v=json.loads(Path(g.replay['path']).read_text())
                if mode=='not_closed':v['rows'][0]['owned_world_stopped']=False
                elif mode=='won':v['rows'][0]['final_state']['won']=True
                elif mode=='wrong_prefix':v['rows'][0]['public_prefix_sha256']='f'*64
                elif mode=='wrong_actions':v['rows'][0]['remaining_world_actions']=99
                elif mode=='wrong_source':v['source_protocol']['sha256']='f'*64
                elif mode=='zero_actions':g.prefixes[g.cases[0]]['steps']=[]
                elif mode=='changed_root':g.prefixes[g.cases[0]]['root']=g.prefixes[g.cases[1]]['root']
                f.plan['source_native_replay']=write(g.replay['path'],v);f.refs[0]=write(f.refs[0]['path'],f.plan)
                with self.assertRaises(ValueError):self.check(f,g)

    def test_old_source_change_after_admission_invalidates_epoch(self):
        with contract_fixture() as f:
            g=preserved_fixture(f);c=self.check(f,g);epoch=f.study.components()
            path=next(iter(g.prefixes[g.cases[0]]['binding']));Path(path).write_text('CHANGED')
            with self.assertRaises(RuntimeError):r.frozen(c,epoch)

    def test_recovery_admission_uses_eight_not_legacy_sixteen_rows(self):
        with contract_fixture() as f:
            g=preserved_fixture(f);f.plan['case_ids']=CASES;f.refs[0]=write(f.refs[0]['path'],f.plan)
            with self.assertRaises(ValueError):self.check(f,g)

    def test_preparation_carries_the_actual_prefix_and_only_all7_adds_reference(self):
        with contract_fixture() as f:
            g=preserved_fixture(f);c=self.check(f,g);parent={'OWNED_FAKE_PARENT':True}
            seen=[]
            def prepare(root,protocol,protocol_sha,**kwargs):
                root.mkdir(parents=True);case=root.parts[-4];(root/'initial_reset.json').write_bytes(case.encode())
                prefix=g.prefixes[case];seen.append((root,kwargs.copy()))
                return dict(source_root=str(kwargs['source_root']),source_binding=prefix['binding'],
                    additional_recovery_source=g.source,caps=prefix['additional_caps'],
                    runtime_controls={'native_terminal_stop':True,'recent_tool_rounds':None},
                    runtime_profile_override={'gguf_verification':parent})
            f.study.prepare=mock.Mock(side_effect=prepare)
            for arm in f.plan['arms']:
                entry=next(x for x in c['rows'] if x['arm']==arm['id'])
                m,caps=r.prepare_episode(c,entry,arm,Path('/OWNED_FAKE_PROFILE'),'a'*64,parent)
                root,kwargs=seen[-1];self.assertEqual(kwargs['source_root'],g.prefixes[entry['case']]['root'])
                self.assertEqual(caps,dict(CAPS,posts=32,seconds=600,world_actions=98))
                self.assertEqual(root.parts[-3],'keep_full' if arm['reference']=='all7' else 'drop_full')
                expected=Path(c['selections'][entry['case']]['all7']['path']) if arm['reference']=='all7' else None
                self.assertEqual(kwargs['reference_context'],expected)
                self.assertEqual(kwargs['model_seed'],17)

    def test_source_outcome_counts_only_new_actions_and_requires_same_prefix(self):
        with contract_fixture() as f:
            g=preserved_fixture(f);c=self.check(f,g);entry=c['rows'][0];prefix=g.prefixes[entry['case']]
            receipt=dict(world_actions=3,total_world_action_count=5,final_world_state=dict(action_count=5),
                source_binding_charge_once=prefix['binding'])
            r.validate_preserved_outcome(c,entry,receipt)
            for change in (dict(world_actions=5),dict(total_world_action_count=3),
                           dict(world_actions=99,total_world_action_count=101,final_world_state=dict(action_count=101)),
                           dict(source_binding_charge_once={})):
                with self.subTest(change=change),self.assertRaises(ValueError):
                    r.validate_preserved_outcome(c,entry,dict(receipt,**change))

    def test_audit_respects_the_explicit_new_post_cap(self):
        with receipt_fixture() as f:
            f.receipt.update(model_posts=33,forwarded_model_posts=33,real_model_calls=33)
            with self.assertRaisesRegex(ValueError,'actual/budget calls differ'):
                r.audit(f.study,f.root,f.receipt,f.manifest,caps=dict(CAPS,posts=32,seconds=600))


class ReferenceComponentProbeTests(unittest.TestCase):
    """Synthetic CPU controls: no model, native world, container, or shared lease."""
    def plan(self):
        cases=['nexttrain_look_%02d'%i for i in range(1,7)]
        return dict(schema='ALFWORLD_REFERENCE_COMPONENT_PROBE_V1',planned_episodes=6,max_forwarded_posts=768,
            rows=[dict(case=case,root=str(r.ST/'cases'/case/'ordinary_reset/student8b/attempt_v6')) for case in cases])

    def ledger(self):
        rows=[dict(status='CLOSED_AUDITED') for _ in range(6)]
        result=dict(completed_receipts=6,aggregation_errors=[],unclosed_attempts=[],unrun=[],unknown_usage_model_posts=0,
            total_actual_model_calls=6,known_budget_model_posts=6,known_actual_model_calls=6,
            restored_healthy=True,shared35_unchanged=True,shared27_unchanged=True)
        return rows,result

    def test_fixed_six_fresh_slots_and_768_budget(self):
        p=self.plan();self.assertEqual(r._reference_probe_shape(p),[e['case'] for e in p['rows']])
        for key,value in [('planned_episodes',18),('max_forwarded_posts',2304)]:
            with self.subTest(key=key),self.assertRaises(ValueError):r._reference_probe_shape(dict(p,**{key:value}))
        for attempt in ('attempt_v1','attempt_v5','attempt_v06'):
            bad=copy.deepcopy(p);bad['rows'][0]['root']=str(Path(bad['rows'][0]['root']).with_name(attempt))
            with self.subTest(attempt=attempt),self.assertRaises(ValueError):r._reference_probe_shape(bad)

    def test_duplicate_or_mismatched_slot_rejected(self):
        p=self.plan();p['rows'][-1]=copy.deepcopy(p['rows'][0])
        with self.assertRaises(ValueError):r._reference_probe_shape(p)
        p=self.plan();p['rows'][1]['root']=str(Path(p['rows'][1]['root']).with_name('attempt_v7'))
        with self.assertRaises(ValueError):r._reference_probe_shape(p)

    def test_actual_plan_file_sha_checked_before_loading_helpers(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory).resolve();path=root/'plan.json';path.write_text(json.dumps(self.plan()))
            with mock.patch.object(r,'ROOT',root),mock.patch.object(r,'load') as load:
                with self.assertRaises(ValueError):r.check_reference_probe_plan(path,'0'*64)
            load.assert_not_called()

    def test_release_must_match_current_identity_and_six_budget(self):
        c=dict(plan_ref={'path':'/FAKE/plan','sha256':'a'*64},epoch={},execution_controls={'FAKE_GUARD':'SHA'},
            owned_process={'pid':123,'start_ticks':'456'},closed_refs={'F':'FAKE_F','H':'FAKE_H'},bindings={})
        release=dict(schema='ALFWORLD_REFERENCE_COMPONENT_RELEASE_V1',status='RELEASED',plan=c['plan_ref'],operator_sha256=r.sha(SCRIPT),
            components={},execution_controls=c['execution_controls'],restored_process=c['owned_process'],closed_results=c['closed_refs'],
            reference_B_sha256='69d22b795c361c52683a293b4eb0c772a0ca1526e4aca845724205dc72af91bd',
            episodes=6,maximum_forwarded_posts=768,input_bindings={},training=0,judges=0)
        for change in (dict(episodes=18),dict(maximum_forwarded_posts=2304),dict(restored_process={'pid':999}),dict(execution_controls={})):
            with self.subTest(change=change),mock.patch.object(r,'check_reference_probe_plan',return_value=c),mock.patch.object(r,'private',side_effect=Path),\
                    mock.patch.object(r,'checked',return_value=dict(release,**change)),mock.patch.object(r,'_execute_owned_reference_rows') as execute:
                with self.assertRaises(ValueError):r.execute_reference_probe('/FAKE/plan','a'*64,'/FAKE/release','b'*64)
                execute.assert_not_called()

    def test_shared_window_rejects_missing_release_before_any_resource_action(self):
        with mock.patch.object(r,'helper') as helper:
            with self.assertRaisesRegex(ValueError,'release'):r._execute_owned_reference_rows({})
        helper.assert_not_called()

    def test_only_experience_changes_normalize_including_quote_layer(self):
        prefix='Goal and \\n sensor <prior_experience>';suffix='</prior_experience> current shelf remains public'
        a={'messages':[{'content':'"'+prefix+'A \\"quoted\\"'+suffix+'"'}],'time':'2026-11-08','tools':[{'x':1}]}
        b=copy.deepcopy(a);b['messages'][0]['content']='"'+prefix+'B'+suffix+'"'
        self.assertEqual(r._reference_probe_frame(a),r._reference_probe_frame(b))
        b['time']='2026-11-09';self.assertNotEqual(r._reference_probe_frame(a),r._reference_probe_frame(b))
        with self.assertRaises(ValueError):r._reference_probe_frame('<prior_experience>unclosed')

    @contextmanager
    def frame_guard(self,base_returns_saved=False):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);case='nexttrain_look_01';reset={'observation':'FAKE public room','done':False,'won':False,'action_count':0}
            task=lambda body:'Goal\n<prior_experience>\n'+body+'\n</prior_experience>\ncurrent state unchanged'
            quote=lambda text:'"'+text.replace('"',chr(92)+'"')+'"'
            incoming=lambda body:{'messages':[{'role':'system','content':'Current date: 2026-11-08'},{'role':'user','content':quote(task(body))}],'tools':[{'function':{'name':'bash'}}]}
            source=incoming('A');observed=incoming('B');sampling={'seed':17,'temperature':.2}
            c=dict(execution_controls={'frame_guard':{'path':'FAKE_CONTROLLER','sha256':'c'*64}},frames={case:r._reference_probe_frame(dict(
                task=task('A'),reset=reset,handoff=reset,incoming=source,forwarded=dict(source,**sampling),observed=source))})
            c['relay_input_frames']={case:dict(c['frames'][case],incoming=r._reference_probe_frame(dict(source,**sampling)))}
            (root/'task.txt').write_text(task('B'));write(root/'initial_reset.json',reset);write(root/'handoff_public.json',reset)
            write(root/'observed_requests/00001.json',observed)
            visits=[]
            legitimate=copy.deepcopy(dict(observed,**sampling))
            class BaseRelay:
                def prepare_payload(self,payload,index):
                    visits.append('parent_whole_task_proof');return copy.deepcopy(legitimate) if base_returns_saved else payload
            factory=mock.Mock(return_value=BaseRelay);study=SimpleNamespace(study_relay=factory)
            r._install_reference_frame_guard(study,c)
            cls=study.study_relay(SimpleNamespace(write_new=write),{'case_id':case},{},None)
            relay=cls();relay.root=root;relay.forwarded=0
            yield SimpleNamespace(root=root,relay=relay,observed=observed,payload=dict(observed,**sampling),visits=visits,c=c,sampling=sampling)

    def test_real_guard_factory_keeps_payload_and_records_input_only(self):
        with self.frame_guard() as f:
            before=copy.deepcopy(f.payload);returned=f.relay.prepare_payload(f.payload,1)
            self.assertIs(returned,f.payload);self.assertEqual(returned,before);self.assertEqual(f.visits,['parent_whole_task_proof'])
            proof=json.loads((f.root/'reference_input_frame_checks/00001.json').read_text())
            self.assertTrue(proof['matched']);self.assertFalse(proof['actual_forward_or_native_outcome_claim'])

    def test_date_or_template_drift_blocks_before_any_post_reservation(self):
        with self.frame_guard() as f:
            f.payload['messages'][0]['content']='Current date: 2026-11-09';reserved=mock.Mock()
            with self.assertRaisesRegex(ValueError,'first input frame'):
                payload=f.relay.prepare_payload(f.payload,1);reserved(json.dumps(payload).encode())
            reserved.assert_not_called()
            self.assertFalse(json.loads((f.root/'reference_input_frame_checks/00001.json').read_text())['matched'])

    def test_real_hook_input_cannot_be_replaced_by_observed_or_base_output(self):
        for change in ('date','extra_field'):
            with self.subTest(change=change),self.frame_guard(base_returns_saved=True) as f:
                if change=='date':f.payload['messages'][0]['content']='Current date: 2026-11-09'
                else:f.payload['unknown_actual_input']={'unapproved':True}
                reserved=mock.Mock()
                with self.assertRaisesRegex(ValueError,'first input frame'):
                    forwarded=f.relay.prepare_payload(f.payload,1);reserved(json.dumps(forwarded).encode())
                reserved.assert_not_called();proof=json.loads((f.root/'reference_input_frame_checks/00001.json').read_text())
                self.assertFalse(proof['matched']);self.assertNotEqual(proof['incoming_payload_sha256'],proof['prepared_payload_sha256'])

    def test_missing_or_changed_controller_proofs_cannot_close_actual_wire(self):
        with self.frame_guard() as f:
            f.relay.prepare_payload(f.payload,1);f.c['plan_ref']={'path':'FAKE_PLAN','sha256':'a'*64}
            write(f.root/'requests/00001.json',{'incoming':f.observed,'forwarded':f.payload})
            (f.root/'requests/00001.body').write_bytes(json.dumps(f.payload,separators=(',',':')).encode())
            binding_path=f.root/'controller_execution_binding.json';binding={'plan':f.c['plan_ref'],'execution_controls':f.c['execution_controls']};write(binding_path,binding)
            manifest={'sampling':f.sampling};proof_path=f.root/'reference_input_frame_checks/00001.json';proof=json.loads(proof_path.read_text())
            refs=r._reference_probe_delivery_bindings(f.c,f.root,manifest)
            self.assertEqual(set(refs),{str(proof_path),str(binding_path)})
            for key,value in [('matched',False),('kind','NATIVE_SUCCESS'),('actual_forward_or_native_outcome_claim',True),
                              ('control',{}),('incoming_payload_sha256','0'*64),('prepared_payload_sha256','0'*64),('observed_request_sha256','0'*64)]:
                with self.subTest(field=key):
                    write(proof_path,dict(proof,**{key:value}));entry={'status':'CLOSED_UNAUDITED'}
                    with self.assertRaises(ValueError):
                        r._reference_probe_delivery_bindings(f.c,f.root,manifest);entry['status']='CLOSED_AUDITED'
                    self.assertEqual(entry['status'],'CLOSED_UNAUDITED')
            write(proof_path,proof);write(binding_path,dict(binding,plan={'path':'FORGED'}))
            with self.assertRaises(ValueError):r._reference_probe_delivery_bindings(f.c,f.root,manifest)
            write(binding_path,binding)
            for path in (proof_path,binding_path):
                raw=path.read_bytes();path.unlink()
                with self.subTest(missing=path.name),self.assertRaises(OSError):r._reference_probe_delivery_bindings(f.c,f.root,manifest)
                path.write_bytes(raw)

    def test_raw_accounting_unknown_or_partial_never_complete(self):
        rows,result=self.ledger();self.assertTrue(r._reference_rows_complete(result,rows))
        for change in (dict(unknown_usage_model_posts=1),dict(total_actual_model_calls=None),dict(known_budget_model_posts=769),
                       dict(aggregation_errors=['unknown']),dict(unrun=['slot']),dict(unclosed_attempts=['slot']),dict(known_actual_model_calls=5)):
            with self.subTest(change=change):self.assertFalse(r._reference_rows_complete(dict(result,**change),rows))
        self.assertFalse(r._reference_rows_complete(result,rows+[{'status':'CLOSED_AUDITED'}]))

    def test_restoration_failure_or_disk_failure_keeps_lease(self):
        class Held(BaseException):pass
        def hold(*args):raise Held()
        for failure in ('restoration_error','world_cleanup_error','shared_identity_error','disk'):
            with self.subTest(failure=failure):
                rows,result=self.ledger();old=SimpleNamespace(write=mock.Mock(),hold_for_d=mock.Mock(side_effect=hold))
                c=dict(old=old,rows=rows,output=Path('/FAKE/OWNED_OUTPUT'))
                if failure!='disk':result[failure]='FAKE_ERROR'
                persist=mock.Mock(side_effect=OSError('FAKE_DISK')) if failure=='disk' else mock.Mock()
                with mock.patch.object(r,'sha',return_value='FAKE_SHA'),self.assertRaises(Held):r._finish_reference_rows(c,result,persist,mock.Mock())
                self.assertEqual(result['status'],'NEEDS_D_RECOVERY');old.hold_for_d.assert_called_once()
