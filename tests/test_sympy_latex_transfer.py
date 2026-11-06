"""Transfer contracts; all HTTP is synthetic and no actor is launched."""
import ast
import importlib.util
import json
from pathlib import Path
import shutil
import sys
import tarfile
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'research/agent_frontier_portfolio_20261029')]
spec=importlib.util.spec_from_file_location('sympy_transfer_test',ROOT/'research/agent_frontier_portfolio_20261029/run_sympy_latex_transfer_20261106.py')
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)


class TransferTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
        for name,value in [('EXPERIENCE',self.root/'source_experience_v1'),('TARGETS',self.root/'targets')]:
            patch=mock.patch.object(r,name,value);patch.start();self.addCleanup(patch.stop)
        self.actor={'runtime':str(self.root/'projection/runtime'),'sites':{'default':str(self.root/'projection/deps/default')},
                    'manifest_sha256':'a'*64}
        self.profile={'host':'127.0.0.1','port':18104,'model_id':'qwen3-8b-qual','context':32768,'output':8192}

    def prepared(self):
        ev={'provenance':{'completion_sha256':'b'*64},'outcome':{'physical_posts':1,'focus':{'passed':True}},
            'changed_paths':['module.py'],'diff':b'--- source-base/module.py\n+++ source-agent/module.py\n+fixed\n',
            'task':b'old source issue only','actions':[{'tool':'edit','status':'error','output_tail':'',
                       'error_tail':'PermissionDenied','error_chars':16,'error_sha256':'c'*64}],
            'history_rendering_version':2}
        patch=mock.patch.object(r,'source_evidence',return_value=ev);patch.start();self.addCleanup(patch.stop)
        r.prepare_source();return ev

    def generated(self,finish='stop',content='Reuse source checks carefully.',reasoning='',expect_failure=False):
        raw=json.dumps({'choices':[{'finish_reason':finish,'message':{'content':content,'reasoning':reasoning}}],
                        'usage':{'total_tokens':23}}).encode()
        blocks=iter([raw,b''])
        connection=mock.Mock();connection.getresponse.return_value=SimpleNamespace(status=200,read=lambda n:next(blocks))
        with mock.patch.object(r.source.teacher,'validate_vllm_model_profile',return_value={'host':'127.0.0.1','port':8006}), \
             mock.patch.object(r.source.teacher,'verify_vllm_backend',return_value={}), \
             mock.patch.object(r.http.client,'HTTPConnection',return_value=connection):
            if finish=='stop' and not expect_failure:r.generate_skill()
            else:
                with self.assertRaises(ValueError):r.generate_skill()
        return connection,raw

    def test_real_source_uses_archived_snapshots_and_retains_both_observed_edits(self):
        if not r.SOURCE.exists():self.skipTest('authoritative source is on GB10')
        with mock.patch.object(r.source,'components',side_effect=AssertionError('must not compare current components')):
            ev=r.source_evidence()
        self.assertEqual(ev['changed_paths'],['sympy/printing/latex.py','sympy/printing/tests/test_latex.py'])
        self.assertEqual(ev['outcome']['provider_usage']['reported_tokens_known'],148213)
        self.assertTrue(all('error_tail' in action and 'status' in action for action in ev['actions']))
        self.assertIn(b'source-agent/sympy/printing/tests/test_latex.py',ev['diff'])

    def test_clipped_history_retains_error_and_full_diff_and_cannot_overwrite(self):
        ev=self.prepared();text=(r.EXPERIENCE/'source_history.md').read_text()
        actions=json.loads(r.rendering.decode_field(text,'ACTION_JSON'))
        self.assertEqual(actions[0]['status'],'error');self.assertEqual(actions[0]['error_tail'],'PermissionDenied')
        self.assertEqual(r.rendering.decode_patch(text),ev['diff'])
        with self.assertRaises(FileExistsError):r.prepare_source()
        (r.EXPERIENCE/'feedback_card.md').write_text('changed')
        with self.assertRaises(ValueError):r.validate_draft()

    def test_skill_generation_sends_exactly_one_source_only_request(self):
        self.prepared();connection,_=self.generated()
        self.assertEqual(connection.request.call_count,1)
        args=connection.request.call_args;self.assertEqual(args.args,('POST','/v1/chat/completions'))
        payload=json.loads(args.kwargs['body']);self.assertEqual(payload,r.skill_payload())
        self.assertEqual(payload['max_tokens'],2500);self.assertEqual(payload['model'],'qwen38-27b-fp8')
        self.assertEqual(r.validate_skill()['provider_usage'],{'total_tokens':23})
        with self.assertRaises(FileExistsError):r.generate_skill()

    def test_failed_skill_generation_retains_raw_usage_and_never_retries(self):
        self.prepared();connection,raw=self.generated(finish='length',content='unfinished')
        self.assertEqual(connection.request.call_count,1)
        self.assertEqual((r.EXPERIENCE/'skill_generation_response.json').read_bytes(),raw)
        ledger=r.read(r.EXPERIENCE/'skill_generation_ledger.json')
        self.assertEqual(ledger['provider_usage']['total_tokens'],23)
        self.assertFalse((r.EXPERIENCE/'generated_skill.md').exists())
        with self.assertRaises(FileExistsError):r.generate_skill()
        broken=SimpleNamespace(read=mock.Mock(side_effect=[b'first',r.http.client.IncompleteRead(b'partial',99)]))
        path=self.root/'partial-response'
        with self.assertRaises(r.http.client.IncompleteRead):r.retain_response(broken,path)
        self.assertEqual(path.read_bytes(),b'firstpartial')

    def test_freeze_requires_all_three_artifacts_and_precedes_every_target(self):
        self.prepared();self.generated()
        r.TARGETS.mkdir();(r.TARGETS/'prepared-target').mkdir()
        with self.assertRaisesRegex(ValueError,'target preparation'):r.freeze_source()
        (r.TARGETS/'prepared-target').rmdir();frozen=r.freeze_source();digest=r.sha(r.EXPERIENCE/'frozen_manifest.json')
        self.assertEqual(set(frozen['artifacts']),r.EXPERIENCE_NAMES)
        self.assertEqual(r.frozen_source(digest),frozen)
        (r.EXPERIENCE/'generated_skill.md').write_text('changed')
        with self.assertRaises(ValueError):r.frozen_source(digest)

    def test_skill_request_cannot_smuggle_additional_future_context(self):
        self.prepared();self.generated()
        path=r.EXPERIENCE/'skill_generation_request.json';request=r.read(path)
        request['messages'].insert(1,{'role':'user','content':'future target answer'})
        path.write_text(json.dumps(request));ledger=r.read(r.EXPERIENCE/'skill_generation_ledger.json')
        ledger['request_sha256']=r.sha(path);(r.EXPERIENCE/'skill_generation_ledger.json').write_text(json.dumps(ledger))
        with self.assertRaises(ValueError):r.validate_skill()

    def test_experience_identifiers_are_contained_and_reject_symlinks(self):
        with mock.patch.object(r,'PARENT',self.root):
            self.assertEqual(r.experience_directory('source_experience_v2'),self.root/'source_experience_v2')
            for identifier in ('../source_experience_v2','/tmp/source_experience_v2',r'..\source_experience_v2',
                               'source_experience_v0','source_experience_v02','source_experience_v2/child'):
                with self.subTest(identifier=identifier),self.assertRaises(ValueError):r.experience_directory(identifier)
            if sys.platform!='win32':
                (self.root/'source_experience_v3').symlink_to(self.root,target_is_directory=True)
                with self.assertRaises(ValueError):r.experience_directory('source_experience_v3')

    def test_v2_disables_thinking_and_preserves_failed_v1_and_identical_history(self):
        self.prepared();self.generated(content='',reasoning='- literal skill bullets in reasoning',expect_failure=True)
        self.assertFalse((r.EXPERIENCE/'generated_skill.md').exists())
        for name in ('draft_manifest.json','skill_generation_ledger.json'):
            path=r.EXPERIENCE/name;record=r.read(path);record.pop('experience_config');path.write_text(json.dumps(record))
        r.validate_draft()  # Legacy v1 metadata is readable without rewriting it.
        before={path.name:path.read_bytes() for path in r.EXPERIENCE.iterdir()}
        legacy_payload=r.skill_payload();self.assertNotIn('chat_template_kwargs',legacy_payload)
        with mock.patch.object(r,'EXPERIENCE',self.root/'source_experience_v2'):
            r.prepare_source();payload=r.skill_payload()
            self.assertIs(payload['chat_template_kwargs']['enable_thinking'],False)
            self.assertEqual({k:v for k,v in payload.items() if k!='chat_template_kwargs'},legacy_payload)
            for name in ('source_history.md','feedback_card.md'):
                self.assertEqual((r.EXPERIENCE/name).read_bytes(),before[name])
            self.assertNotIn(r.TARGET_ENVIRONMENT_NOTE,payload['messages'][-1]['content'])
            self.generated();self.assertEqual(r.validate_skill()['experience_config'],r.experience_config())
            request=r.EXPERIENCE/'skill_generation_request.json';request.write_text(json.dumps(legacy_payload))
            ledger_path=r.EXPERIENCE/'skill_generation_ledger.json';ledger=r.read(ledger_path)
            ledger['request_sha256']=r.sha(request);ledger_path.write_text(json.dumps(ledger))
            with self.assertRaises(ValueError):r.validate_skill()
            draft=r.read(r.EXPERIENCE/'draft_manifest.json');draft.pop('experience_config')
            (r.EXPERIENCE/'draft_manifest.json').write_text(json.dumps(draft))
            with self.assertRaises(ValueError):r.validate_draft()
        self.assertEqual({path.name:path.read_bytes() for path in r.EXPERIENCE.iterdir()},before)

    def test_wrong_target_experience_id_never_falls_back_to_another_source(self):
        root=r.TARGETS/'wrong';root.mkdir(parents=True)
        manifest={'experience_id':'source_experience_v2'};(root/'inputs_manifest.json').write_text(json.dumps(manifest))
        with mock.patch.object(r,'frozen_source',side_effect=AssertionError('wrong source must never be read')):
            with self.assertRaisesRegex(ValueError,'experience-id'):r.execute_target('wrong','d'*64,'e'*64)
            with self.assertRaisesRegex(ValueError,'experience-id'):r.verify_target_inputs(root,manifest)

    def test_actual_target_harness_binds_student_seed_and_none_has_no_experience(self):
        if not r.source.core.BASE.exists():self.skipTest('authoritative harness is on GB10')
        before=(r.source.EID,r.source.requests_runner,r.source.primitives)
        for condition in r.CONDITIONS:
            with self.subTest(condition=condition):
                root=self.root/condition;inputs=root/'inputs/target';inputs.mkdir(parents=True)
                (inputs/'clean_base').mkdir();(inputs/'clean_base/module.py').write_text('baseline')
                problem='target task only\r\nsecond line\n'
                (inputs/'task.txt').write_bytes(r.target_task(problem).encode());r.source.primitives.prepare_actor_runtime(root)
                experience=None
                if condition!='none':experience=root/'source_experience.md';experience.write_text('source evidence')
                with mock.patch.object(r.source,'ripgrep_binding',return_value=[]):
                    code=r.derive_target(root,condition,self.actor,self.profile,experience)
                prefix=[]
                for statement in ast.parse(code).body:
                    if isinstance(statement,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='server' for t in statement.targets):break
                    prefix.append(statement)
                with mock.patch.object(sys,'argv',['harness','target','no_skill']):
                    ns={};exec(compile(ast.Module(body=prefix,type_ignores=[]),'<target-setup>','exec'),ns)
                self.addCleanup(shutil.rmtree,ns['bridge'],True)
                cmd=ns['cmd'];mounts=[cmd[i+1] for i,x in enumerate(cmd) if x=='--mount']
                self.assertEqual(any('dst=/root/source_experience.md' in m for m in mounts),condition!='none')
                self.assertFalse(any(any(x in m for x in ('qualification','row.json','gold','probe_target','frozen_manifest')) for m in mounts))
                self.assertIn('/extra/bin/python',cmd);self.assertEqual(ns['case'],root/r.target_id(condition))
                body=json.dumps({'model':'wrong','temperature':1,'seed':1,'messages':[]}).encode()
                first=b'POST /v1/chat/completions HTTP/1.1\r\nContent-Length: '+str(len(body)).encode()+b'\r\n\r\n'+body
                forwarded,_,_=ns['capture_sampling'](first,len(body),lambda n:b'',.2,7202)
                payload=json.loads(forwarded.split(b'\r\n\r\n',1)[1])
                self.assertEqual((payload['model'],payload['temperature'],payload['seed']),('qwen3-8b-qual',.2,7202))
                self.assertIn("'timeout':300000",code);self.assertNotIn("'timeout':900000",code)
                self.assertIn('target task only',(root/r.target_id(condition)/'work/instructions.txt').read_text())
                actor_task=(root/r.target_id(condition)/'work/instructions.txt').read_bytes()
                self.assertTrue(actor_task.startswith(problem.encode()))
                self.assertEqual(actor_task.count(r.TARGET_ENVIRONMENT_NOTE.encode()),1)
                shutil.rmtree(ns['bridge'])
        self.assertEqual((r.source.EID,r.source.requests_runner,r.source.primitives),before)

    def test_target_evaluator_restores_configs_and_uses_142_without_changing_source(self):
        clean=self.root/'clean';tests=clean/'sympy/printing/tests';tests.mkdir(parents=True)
        (tests/'test_latex.py').write_text('def test_latex_functions():\n    assert True\n')
        (clean/'pytest.ini').write_text('[pytest]\n');work=self.root/'work';shutil.copytree(clean,work)
        (work/'pytest.ini').write_text('disable all tests');(work/'conftest.py').write_text('malicious config')
        row={'test_patch':''};nodes=[f'node{i}' for i in range(142)]
        actual_run=r.source.subprocess.run
        def process(cmd,**kwargs):
            if cmd[0]!='docker':return actual_run(cmd,**kwargs)
            bind=next(x for x in cmd if ',dst=/workspace,' in x);candidate=Path(bind.split('src=',1)[1].split(',dst=',1)[0])
            self.assertEqual((candidate/'pytest.ini').read_text(),'[pytest]\n');self.assertFalse((candidate/'conftest.py').exists())
            self.assertTrue(any('probe_target.py,dst=/probe.py' in x for x in cmd))
            out=b'RESULT {"module":"/workspace/sympy/__init__.py","pass":true}\n' if cmd[-1]=='/probe.py' else (b'142 passed\n' if cmd[-1]=='node141' else b'1 passed\n')
            return r.source.subprocess.CompletedProcess(cmd,0,out,b'')
        original=inspect_source(r.source.evaluate)
        with mock.patch.object(r,'target_row',return_value=(row,nodes)), \
             mock.patch.object(r.source,'apply_patch'),mock.patch.object(r.source.subprocess,'run',side_effect=process):
            result=r.target_evaluator()(work,self.root/'evaluation',self.actor,row,clean)
        self.assertTrue(result['passed']);self.assertEqual(result['regression']['expected_count'],142)
        self.assertEqual(inspect_source(r.source.evaluate),original);self.assertIn('114',original)
        self.assertEqual((work/'pytest.ini').read_text(),'disable all tests')

    def test_execute_adapter_uses_reserved_target_role_and_records_source_binding(self):
        root=r.TARGETS/'arm';(root/'inputs/target').mkdir(parents=True)
        (root/'inputs/target/task.txt').write_text('task');(root/'frozen_source_harness.py').write_text('no execution')
        (root/'preflight').mkdir();(root/'preflight/receipt.json').write_text('{"status":"PREFLIGHT_PASS"}')
        manifest={'condition':'none','experience_id':r.EXPERIENCE.name,'source_manifest_sha256':'d'*64,'projection_sha256':'a'*64,
                  'component_sha256':{'outer_runner.py':'b'*64},'task_sha256':r.sha(root/'inputs/target/task.txt'),
                  'harness_sha256':r.sha(root/'frozen_source_harness.py')}
        (root/'inputs_manifest.json').write_text(json.dumps(manifest));digest=r.sha(root/'inputs_manifest.json')
        with mock.patch.object(r,'verify_target_inputs'),mock.patch.object(r,'target_row',return_value=({},[])), \
             mock.patch.object(r,'target_evaluator'),mock.patch.object(r.source,'prepare_projection',return_value=self.actor), \
             mock.patch.object(r.source.primitives,'validate_model_profile',return_value=self.profile), \
             mock.patch.object(r.source.primitives,'verify_live_backend',return_value={}), \
             mock.patch.object(r.source.subprocess,'run',return_value=r.source.subprocess.CompletedProcess([],1,b'',b'')) as launch:
            result=r.execute_target('arm','d'*64,digest)
        self.assertEqual(launch.call_count,1)
        self.assertEqual((result['task'],result['condition'],result['seed'],result['backend_kind']),('target','none',7202,'student8b'))
        self.assertEqual(result['source_manifest_sha256'],'d'*64);self.assertIsNone(result['experience_read'])

    def test_prepared_none_and_history_bind_identical_source_and_target_inputs(self):
        if not r.source.core.BASE.exists():self.skipTest('authoritative harness is on GB10')
        q=self.root/'qualification';clean=q/'target/clean';clean.mkdir(parents=True);(clean/'module.py').write_text('old\n')
        with tarfile.open(q/'target.tar.gz','w:gz') as stream:stream.add(clean,arcname='sympy-'+r.TARGET_BASE)
        profile=self.root/'student.json';profile.write_text(json.dumps(self.profile))
        selected=self.root/'source_experience_v2'
        selected.mkdir()
        for condition in r.CONDITIONS[1:]:(selected/(condition+'.md')).write_text('source evidence')
        row={'problem_statement':'qualified target task\r\nverbatim second line\n','patch':''}
        def evaluate(work,*args):
            gold=work.name=='gold_input'
            return {'passed':gold,'focus':{'passed':gold,'observed':int(gold),'exit':0 if gold else 1},
                    'regression':{'passed':True,'observed':142,'exit':0},'issue_probe':{'passed':gold,'exit':0 if gold else 1}}
        with mock.patch.object(r,'EXPERIENCE',selected),mock.patch.object(r,'frozen_source',return_value={}),mock.patch.object(r,'target_row',return_value=(row,[])), \
             mock.patch.object(r,'target_evaluator',return_value=evaluate),mock.patch.object(r.source,'QUAL',q), \
             mock.patch.object(r,'STUDENT_PROFILE',profile),mock.patch.object(r,'STUDENT_SHA',r.sha(profile)), \
             mock.patch.object(r.source,'prepare_projection',return_value=self.actor), \
             mock.patch.object(r.source.dependencies,'verify_projection',return_value=self.actor), \
             mock.patch.object(r.source.primitives,'validate_model_profile',return_value=self.profile), \
             mock.patch.object(r.source,'apply_patch'),mock.patch.object(r.source,'ripgrep_binding',return_value=[]):
            results=[r.prepare_target(condition,condition,'d'*64) for condition in r.CONDITIONS]
        manifests=[r.read(Path(result['root'])/'inputs_manifest.json') for result in results]
        self.assertEqual([m['source_manifest_sha256'] for m in manifests],['d'*64]*4)
        self.assertEqual([m['experience_id'] for m in manifests],['source_experience_v2']*4)
        self.assertTrue(all(m['experience_config']['skill_chat_template_kwargs']['enable_thinking'] is False for m in manifests))
        self.assertEqual(manifests[0]['task_sha256'],manifests[1]['task_sha256'])
        self.assertEqual(manifests[0]['baseline_tree'],manifests[1]['baseline_tree'])
        self.assertFalse((Path(results[0]['root'])/'source_experience.md').exists())
        self.assertTrue((Path(results[1]['root'])/'source_experience.md').exists())
        tasks=[(Path(result['root'])/'inputs/target/task.txt').read_bytes() for result in results]
        self.assertTrue(all(task==tasks[0] and task.startswith(row['problem_statement'].encode()) for task in tasks))
        self.assertIn(b'test_issue_13559',tasks[0]);self.assertIn(b'test_issue_8470',tasks[0])


def inspect_source(function):
    import inspect
    return inspect.getsource(function)


if __name__=='__main__':unittest.main()
