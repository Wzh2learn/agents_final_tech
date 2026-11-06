"""Source-evidence contracts, exercised only with synthetic files."""
import importlib.util
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'research/agent_frontier_portfolio_20261029')]
spec = importlib.util.spec_from_file_location('django_experience_test', ROOT / 'research/agent_frontier_portfolio_20261029/prepare_django_aggregation_experience_20261106.py')
exp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(exp)


class ExperienceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name); self.source=self.root/'attempts'/'attempt1'; self.source.mkdir(parents=True)
        self.base=self.root/'base'; self.base.mkdir()
        (self.base/'module.py').write_text('old\n')
        self.case=self.source/'source__none__seed7201'; (self.case/'work').mkdir(parents=True)
        (self.case/'work'/'module.py').write_text('new\n'+'x'*4000+'\n')
        (self.case/'raw.jsonl').write_text(json.dumps({'type':'tool_use','part':{'tool':'bash','state':{'input':{'command':'ls'},'output':'ok','status':'completed'}}})+'\n')
        self.ev=self.case/'post_run_evaluation_restored_tests'; self.ev.mkdir()
        for name in ('focus','regression','issue_probe'): (self.ev/(name+'.log')).write_text(name)
        self.eid='source__none__seed7201'; self.components=self.source/(self.eid+'.components'); self.components.mkdir()
        component_sha={}
        for name in ('outer_runner.py','core.py','requests_runner.py','research_actor_dependencies.py','research_auto_record.py','base_harness.py'):
            path=self.components/name;path.write_text(name);component_sha[name]=exp.sha(path)
        self.started=self.source/(self.eid+'.started.json')
        (self.source/(self.eid+'.task.txt')).write_text('Fix the source aggregation issue.\n')
        self.started.write_text(json.dumps({'task':'source','condition':'none','seed':7201,'model_profile_sha256':'a'*64,
             'projection_sha256':'b'*64,'task_sha256':exp.sha(self.source/(self.eid+'.task.txt')),
             'component_sha256':component_sha,'runner_sha256':component_sha['outer_runner.py']}))
        self.receipt=self.case/'receipt.json';self.receipt.write_text(json.dumps({'raw_sha256':exp.sha(self.case/'raw.jsonl'), 'model_http_requests':['POST /v1/chat/completions']}))
        feedback={'status':'EVALUATED'}
        for name in ('focus','regression','issue_probe'):
            feedback[name]={'exit':1 if name=='focus' else 0,'nodes_requested':1,'log_sha256':exp.sha(self.ev/(name+'.log'))}
        feedback['issue_probe']['observed']={'exception':{'type':'OperationalError'}}
        self.completed=self.source/(self.eid+'.completed.json')
        self.record={'status':'COMPLETED','agent_exit':1,'posts':1,'raw_sha256':exp.sha(self.case/'raw.jsonl'),
             'started_sha256':exp.sha(self.started),'post_run_evaluation':feedback}
        self.completed.write_text(json.dumps(self.record))
        self.output=self.source/'source_experience_v1'
        self.qual=lambda baseline: {'baseline_sha256':'c'*64}

    def draft(self): return exp.build_draft(self.source,self.base,self.output,verify_baseline=self.qual)

    def actions(self, *states):
        raw=self.case/'raw.jsonl'
        raw.write_text(''.join(json.dumps({'type':'tool_use','part':{'tool':'bash','state':state}})+'\n'
                               for state in states),encoding='utf8')
        self.record['raw_sha256']=exp.sha(raw)
        self.completed.write_text(json.dumps(self.record))
        receipt=json.loads(self.receipt.read_text());receipt['raw_sha256']=exp.sha(raw)
        self.receipt.write_text(json.dumps(receipt))

    def skill(self):
        request=self.output/'skill_generation_request.json';request.write_text(json.dumps({'model':'qwen3-8b-qual',
            'temperature':0.2,'seed':7201,'max_tokens':2500,'messages':[{'role':'user','content':(self.output/'source_history.md').read_text()}]}))
        response=self.output/'skill_generation_response.json';response.write_text(json.dumps({'choices':[{'finish_reason':'stop','message':{'content':'skill text'}}],'usage':{'total_tokens':12}}))
        skill=self.output/'generated_skill.md';skill.write_text('skill text\n')
        (self.output/'skill_generation_ledger.json').write_text(json.dumps({'status':'RECEIVED','physical_http_attempts':1,
            'source_history_sha256':exp.sha(self.output/'source_history.md'), 'request_sha256':exp.sha(request),
            'response_sha256':exp.sha(response),'skill_sha256':exp.sha(skill),'finish_reason':'stop',
            'model_profile_sha256':'a'*64}))

    def test_real_failed_episode_allowed_and_long_diff_complete(self):
        result=self.draft();self.assertEqual(result['status'],'DRAFT')
        text=(self.output/'feedback_card.md').read_text()
        self.assertIn('source outcome',text.lower())
        self.assertIn(b'x'*4000,exp.decode_patch(text))
        self.assertLess(max(map(len,text.splitlines())),1801)

    def test_failed_tool_error_keeps_status_and_separate_output_error_evidence(self):
        error='discarded prefix: '+'x'*900+'\nPermissionDenied: 源文件 is read-only'
        self.actions({'input':{'command':'write file'},'status':'error','error':error},
                     {'input':{'command':'run checks'},'status':'error','output':'partial stdout',
                      'error':'Process exited with code 1'},
                     {'input':{'command':'ls'},'status':'completed','output':'ok'})
        draft=self.draft()
        text=(self.output/'source_history.md').read_text(encoding='utf8')
        actions=json.loads(exp.decode_field(text,'ACTION_JSON'))
        self.assertEqual(actions[0]['status'],'error')
        self.assertEqual(actions[0]['output_tail'],'')
        self.assertEqual(actions[0]['error_tail'],error[-800:])
        self.assertEqual(actions[0]['error_chars'],len(error))
        self.assertEqual(actions[0]['error_sha256'],hashlib.sha256(error.encode()).hexdigest())
        self.assertEqual(actions[1]['output_tail'],'partial stdout')
        self.assertEqual(actions[1]['output_chars'],len('partial stdout'))
        self.assertEqual(actions[1]['output_sha256'],hashlib.sha256(b'partial stdout').hexdigest())
        self.assertEqual(actions[1]['error_tail'],'Process exited with code 1')
        self.assertEqual(actions[2]['status'],'completed')
        self.assertEqual(actions[2]['error_tail'],'')
        self.assertEqual(actions[2]['error_chars'],0)
        self.assertEqual(actions[2]['error_sha256'],hashlib.sha256(b'').hexdigest())
        self.assertEqual(draft['history_rendering_version'],2)
        self.assertIn('error tail 800 characters',text)
        self.assertLess(max(map(len,text.splitlines())),1801)
        self.assertEqual(exp.validate_draft(self.source,self.base,self.output,verify_baseline=self.qual),draft)

    def test_legacy_draft_and_frozen_history_validate_without_rewriting_bytes(self):
        self.actions({'input':{'command':'write file'},'status':'error','output':'partial stdout',
                      'error':'PermissionDenied: source file is read-only'})
        draft=self.draft();draft.pop('history_rendering_version',None)
        ev=exp.source_evidence(self.source,self.base,verify_baseline=self.qual)
        inp=json.dumps({'command':'write file'},ensure_ascii=False);out='partial stdout'
        # Independently spell the pre-version action schema and document layout.
        # Using the new legacy renderer to generate its expected bytes would hide drift.
        legacy_actions=[{'tool':'bash','status':'error','input_prefix':inp,'input_chars':len(inp),
                         'input_sha256':hashlib.sha256(inp.encode()).hexdigest(),'output_tail':out,
                         'output_chars':len(out),'output_sha256':hashlib.sha256(out.encode()).hexdigest()}]
        legacy='Source-only ordinary history.\nSource outcome:\n'+json.dumps(ev['outcome'],ensure_ascii=True,indent=2)+'\n'
        legacy+='Changed paths:\n'+json.dumps(ev['changed_paths'],ensure_ascii=True,indent=2)+'\n'
        legacy+='Source task (ordered JSON parts):\n'+exp.render_field('SOURCE_TASK',ev['task'])
        legacy+='Tool actions (input prefix 600 characters, output tail 800 characters; hashes retain identity):\n'
        legacy+=exp.render_field('ACTION_JSON',json.dumps(legacy_actions,ensure_ascii=True,indent=2).encode())
        legacy+='Complete observed source unified diff; concatenate ordered JSON part text exactly:\n'
        legacy+=exp.render_field('COMPLETE_SOURCE_DIFF',ev['diff'])
        (self.output/'source_history.md').write_bytes(legacy.encode())
        draft['artifacts']['source_history.md']=exp.sha(self.output/'source_history.md')
        (self.output/'draft_manifest.json').write_text(json.dumps(draft,indent=2)+'\n')
        self.skill()
        names=('source_history.md','feedback_card.md','generated_skill.md','skill_generation_request.json',
               'skill_generation_response.json','skill_generation_ledger.json','draft_manifest.json')
        frozen={'status':'FROZEN_BEFORE_TARGET','source':draft['source'],
                'artifacts':{name:exp.sha(self.output/name) for name in names},
                'scope':'development only; no target episode was visible in the source attempt family at freeze'}
        manifest=self.output/'input_profile_manifest.json'
        manifest.write_text(json.dumps(frozen,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
        before={path.name:path.read_bytes() for path in self.output.iterdir()}
        self.assertEqual(exp.validate_draft(self.source,self.base,self.output,verify_baseline=self.qual),draft)
        self.assertEqual(exp.validate_frozen(self.source,self.base,self.output,exp.sha(manifest),
                                           verify_baseline=self.qual),frozen)
        self.assertEqual({path.name:path.read_bytes() for path in self.output.iterdir()},before)
        self.assertNotIn(b'PermissionDenied',exp.decode_field(legacy,'ACTION_JSON'))

    def test_history_rendering_contract_cannot_be_downgraded_or_unknown(self):
        self.draft();path=self.output/'draft_manifest.json';draft=json.loads(path.read_text())
        for version in (None,True,0,3,'2'):
            with self.subTest(version=version):
                changed=dict(draft)
                if version is None:changed.pop('history_rendering_version',None)
                else:changed['history_rendering_version']=version
                path.write_text(json.dumps(changed))
                with self.assertRaises(ValueError):
                    exp.validate_draft(self.source,self.base,self.output,verify_baseline=self.qual)

    def test_zero_posts_and_raw_tamper_rejected(self):
        self.record['posts']=0;self.completed.write_text(json.dumps(self.record))
        with self.assertRaises(ValueError): self.draft()
        self.record['posts']=1;self.completed.write_text(json.dumps(self.record));(self.case/'raw.jsonl').write_text('{}\n')
        with self.assertRaises(ValueError): self.draft()

    def test_known_failed_execution_integrity_cannot_become_source_experience(self):
        # Historical records predate the transport integrity field.
        exp.source_evidence(self.source,self.base,verify_baseline=self.qual)
        self.record['execution_integrity']={'passed':True}
        self.completed.write_text(json.dumps(self.record))
        exp.source_evidence(self.source,self.base,verify_baseline=self.qual)
        self.record['execution_integrity']={'passed':False,'reason':'unmetered keep-alive requests'}
        self.completed.write_text(json.dumps(self.record))
        with self.assertRaisesRegex(ValueError,'execution integrity'):
            exp.source_evidence(self.source,self.base,verify_baseline=self.qual)
        with self.assertRaisesRegex(ValueError,'execution integrity'):self.draft()
        self.assertFalse(self.output.exists())
        self.record.pop('execution_integrity')
        self.record['usage_step_count_matches_posts']=False
        self.completed.write_text(json.dumps(self.record))
        with self.assertRaisesRegex(ValueError,'execution integrity'):
            exp.source_evidence(self.source,self.base,verify_baseline=self.qual)

    def test_feedback_skill_tamper_and_target_started_rejected(self):
        self.draft(); self.skill()
        (self.output/'feedback_card.md').write_text('tampered')
        with self.assertRaises(ValueError): exp.freeze(self.source,self.base,self.output,verify_baseline=self.qual)
        self.output.rename(self.output.with_name('corrupt'));self.draft();self.skill()
        (self.output/'generated_skill.md').write_text('tampered')
        with self.assertRaises(ValueError): exp.freeze(self.source,self.base,self.output,verify_baseline=self.qual)
        self.output.rename(self.output.with_name('corrupt2'));self.draft();self.skill()
        (self.source/'target__none__seed7202.started.json').write_text('{}')
        with self.assertRaises(ValueError): exp.freeze(self.source,self.base,self.output,verify_baseline=self.qual)

    def test_frozen_manifest_validates_historical_source_and_detects_snapshot_change(self):
        self.draft();self.skill()
        frozen=exp.freeze(self.source,self.base,self.output,verify_baseline=self.qual)
        self.assertEqual(frozen['history_rendering_version'],2)
        path=self.output/'input_profile_manifest.json';original=path.read_bytes();digest=exp.sha(path)
        self.assertEqual(exp.validate_frozen(self.source,self.base,self.output,digest,verify_baseline=self.qual)['status'],'FROZEN_BEFORE_TARGET')
        frozen['history_rendering_version']=1;path.write_text(json.dumps(frozen))
        with self.assertRaises(ValueError):
            exp.validate_frozen(self.source,self.base,self.output,exp.sha(path),verify_baseline=self.qual)
        path.write_bytes(original)
        (self.components/'outer_runner.py').write_text('changed')
        with self.assertRaises(ValueError): exp.validate_frozen(self.source,self.base,self.output,digest,verify_baseline=self.qual)

    def test_teacher_request_is_source_bound_and_never_uses_student_endpoint(self):
        from scripts.graph import research_teacher_backend as teacher
        started=json.loads(self.started.read_text());started['backend_kind']='teacher35b'
        snap=self.components/'research_teacher_backend.py';snap.write_bytes(Path(teacher.__file__).read_bytes())
        started['component_sha256']['research_teacher_backend.py']=exp.sha(snap)
        self.started.write_text(json.dumps(started));self.record['started_sha256']=exp.sha(self.started)
        self.completed.write_text(json.dumps(self.record));self.draft()
        profile={'model_id':teacher.MODEL_ID,'host':'127.0.0.1','port':8004}
        response={'choices':[{'finish_reason':'stop','message':{'content':'teacher instructions'}}],
                  'usage':{'total_tokens':11}}
        mocked=mock.MagicMock();mocked.__enter__.return_value.read.return_value=json.dumps(response).encode()
        with mock.patch.object(exp,'validate_draft',return_value=json.loads((self.output/'draft_manifest.json').read_text())), \
             mock.patch.object(teacher,'validate_model_profile',return_value=profile), \
             mock.patch.object(teacher,'verify_live_backend',return_value={'pid':2642808}), \
             mock.patch.object(exp.urllib.request,'urlopen',return_value=mocked) as http:
            ledger=exp.generate_skill(self.source,self.base,self.output,self.root/'profile.json','a'*64)
        self.assertEqual(http.call_count,1)
        request=http.call_args.args[0]
        self.assertEqual(request.full_url,'http://127.0.0.1:8004/v1/chat/completions')
        payload=json.loads(request.data);self.assertEqual(payload['model'],teacher.MODEL_ID)
        self.assertEqual(payload['max_tokens'],2500);self.assertEqual(ledger['backend_kind'],'teacher35b')
        self.assertEqual(ledger['model_id'],teacher.MODEL_ID)
        self.assertEqual(len(ledger['backend_helper_sha256']),64)
        draft=json.loads((self.output/'draft_manifest.json').read_text());exp.validate_skill(self.output,draft)
        payload['model']='qwen3-8b-qual'
        (self.output/'skill_generation_request.json').write_text(json.dumps(payload))
        with self.assertRaises(ValueError):exp.validate_skill(self.output,draft)
        ledger['request_sha256']=exp.sha(self.output/'skill_generation_request.json')
        (self.output/'skill_generation_ledger.json').write_text(json.dumps(ledger))
        with self.assertRaises(ValueError):exp.validate_skill(self.output,draft)

    def test_27b_compiler_uses_hf_backend_and_keeps_source_feedback(self):
        from scripts.graph import research_teacher_backend as teacher
        started=json.loads(self.started.read_text());started['backend_kind']='teacher27b'
        snap=self.components/'research_teacher_backend.py';snap.write_bytes(Path(teacher.__file__).read_bytes())
        started['component_sha256']['research_teacher_backend.py']=exp.sha(snap)
        self.started.write_text(json.dumps(started));self.record['started_sha256']=exp.sha(self.started)
        log=self.ev/'broader_regression.log';log.write_text('Ran 219 tests\nFAILED (failures=1, skipped=1)\n')
        self.record['post_run_evaluation']['broader_regression']={'exit':1,'tests_observed':219,'log_sha256':exp.sha(log)}
        self.record['post_run_evaluation']['source_artifact_qualification']={'passed':False,'failed_checks':['broader_regression']}
        self.completed.write_text(json.dumps(self.record));self.draft()
        self.assertIn('broader_regression',(self.output/'source_history.md').read_text())
        response={'choices':[{'finish_reason':'stop','message':{'content':'Retain regression checks; source repair is unqualified.'}}],
                  'usage':{'total_tokens':13}}
        http_response=mock.MagicMock();http_response.__enter__.return_value.read.return_value=json.dumps(response).encode()
        profile={'host':'127.0.0.1','port':8006,'model_id':'qwen38-27b-fp8'}
        with mock.patch.object(exp,'validate_draft',return_value=json.loads((self.output/'draft_manifest.json').read_text())), \
             mock.patch.object(teacher,'validate_vllm_model_profile',return_value=profile), \
             mock.patch.object(teacher,'verify_vllm_backend',return_value={'container_id':'fixed'}), \
             mock.patch.object(exp.urllib.request,'urlopen',return_value=http_response) as http:
            ledger=exp.generate_skill(self.source,self.base,self.output,self.root/'profile.json','a'*64)
        self.assertEqual(http.call_args.args[0].full_url,'http://127.0.0.1:8006/v1/chat/completions')
        self.assertEqual(http.call_args.kwargs['timeout'],900)
        self.assertEqual(ledger['backend_kind'],'teacher27b')
        self.assertEqual(json.loads(http.call_args.args[0].data)['chat_template_kwargs'],{'enable_thinking':False})
        exp.validate_skill(self.output,json.loads((self.output/'draft_manifest.json').read_text()))
        log.write_text('tampered')
        with self.assertRaises(ValueError):exp.validate_draft(self.source,self.base,self.output,verify_baseline=self.qual)

    def test_teacher_source_without_backend_snapshot_is_rejected(self):
        started=json.loads(self.started.read_text());started['backend_kind']='teacher35b'
        self.started.write_text(json.dumps(started));self.record['started_sha256']=exp.sha(self.started)
        self.completed.write_text(json.dumps(self.record))
        with self.assertRaises(ValueError):self.draft()

    def test_teacher_response_target_marker_is_retained_but_not_promoted(self):
        from scripts.graph import research_teacher_backend as teacher
        started=json.loads(self.started.read_text());started['backend_kind']='teacher35b'
        snap=self.components/'research_teacher_backend.py';snap.write_bytes(Path(teacher.__file__).read_bytes())
        started['component_sha256']['research_teacher_backend.py']=exp.sha(snap)
        self.started.write_text(json.dumps(started));self.record['started_sha256']=exp.sha(self.started)
        self.completed.write_text(json.dumps(self.record));self.draft()
        profile={'model_id':teacher.MODEL_ID,'host':'127.0.0.1','port':8004}
        response={'choices':[{'finish_reason':'stop','message':{'content':'Try ticket #34176'}}],
                  'usage':{'total_tokens':42}}
        raw=json.dumps(response).encode();mocked=mock.MagicMock();mocked.__enter__.return_value.read.return_value=raw
        with mock.patch.object(exp,'validate_draft',return_value=json.loads((self.output/'draft_manifest.json').read_text())), \
             mock.patch.object(teacher,'validate_model_profile',return_value=profile), \
             mock.patch.object(teacher,'verify_live_backend',return_value={'pid':2642808}), \
             mock.patch.object(exp.urllib.request,'urlopen',return_value=mocked) as http:
            with self.assertRaises(ValueError):exp.generate_skill(self.source,self.base,self.output,self.root/'profile.json','a'*64)
        self.assertEqual(http.call_count,1)
        self.assertEqual((self.output/'skill_generation_response.json').read_bytes(),raw)
        ledger=json.loads((self.output/'skill_generation_ledger.json').read_text())
        self.assertEqual(ledger['status'],'FAILED_RECORDED_RESPONSE')
        self.assertEqual(ledger['usage'],{'total_tokens':42})
        self.assertEqual(ledger['response_sha256'],exp.sha(self.output/'skill_generation_response.json'))
        self.assertFalse((self.output/'generated_skill.md').exists())
        self.assertFalse((self.output/'input_profile_manifest.json').exists())
        with self.assertRaises(ValueError):exp.freeze(self.source,self.base,self.output,verify_baseline=self.qual)

    def test_self_consistent_skill_with_target_marker_is_rejected(self):
        self.draft();self.skill()
        response_path=self.output/'skill_generation_response.json';response=json.loads(response_path.read_text())
        response['choices'][0]['message']['content']='See #34176'
        response_path.write_text(json.dumps(response));(self.output/'generated_skill.md').write_text('See #34176\n')
        ledger_path=self.output/'skill_generation_ledger.json';ledger=json.loads(ledger_path.read_text())
        ledger['response_sha256']=exp.sha(response_path);ledger['skill_sha256']=exp.sha(self.output/'generated_skill.md')
        ledger_path.write_text(json.dumps(ledger))
        with self.assertRaises(ValueError):exp.validate_skill(self.output,json.loads((self.output/'draft_manifest.json').read_text()))

if __name__=='__main__':unittest.main()
