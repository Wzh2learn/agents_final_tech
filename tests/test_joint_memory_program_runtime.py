"""CPU-only contracts for the Django continuation; no actor or scorer runs."""
import hashlib
import contextlib
import io
import json
import os
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / 'research/agent_frontier_portfolio_20261029'))
sys.path.insert(0, str(REPO))
import joint_memory_program as joint
import joint_memory_program_runtime as m
import run_contextbench_source as source
from scripts.graph import research_actor_dependencies as deps


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def put_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding='utf-8')
    return sha(path)


class RuntimeContracts(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.private = Path(self.temp.name).resolve() / 'private'
        self.private.mkdir()
        self.patches = []

        def patch(obj, key, value):
            p = mock.patch.object(obj, key, value); p.start(); self.patches.append(p)

        self.addCleanup(lambda: [p.stop() for p in reversed(self.patches)])
        patch(source, 'PRIVATE', self.private)

        self.pilot = self.private / 'public_pilot'; self.pilot.mkdir()
        self.snapshot = self.pilot / 'snapshot'
        (self.snapshot / 'django/db/models').mkdir(parents=True)
        (self.snapshot / 'django/db/models/expressions.py').write_text('candidate repair\n')
        (self.snapshot / 'tests').mkdir(); (self.snapshot / 'tests/public.py').write_text('public test\n')
        fp, _ = m.snapshot_fingerprint(self.snapshot)
        patch(m, 'SNAPSHOT_SHA', fp['tree_sha256']); patch(m, 'SNAPSHOT_FILES', fp['files'])
        patch(m, 'SNAPSHOT_BYTES', fp['bytes'])

        public = self.pilot / 'public'; public.mkdir()
        (public / 'source_task.txt').write_text('Public source issue.\n')
        (public / 'public_regression_failure.txt').write_text('Public regression failed.\n')
        patch(m, 'TASK_SHA', sha(public / 'source_task.txt'))
        patch(m, 'FAILURE_SHA', sha(public / 'public_regression_failure.txt'))
        query_dir = self.pilot / 'query_payloads'; query_dir.mkdir()
        test_text = query_dir / 'test.txt'; test_text.write_text('Public function.\n')
        prod_text = query_dir / 'production.txt'; prod_text.write_text('Production function.\n')
        query_hashes = {'read_public_test_function': sha(test_text),
                        'read_edited_production_function': sha(prod_text)}
        patch(m, 'QUERY_HASHES', query_hashes)
        self.input_manifest = self.pilot / 'input.json'
        input_sha = put_json(self.input_manifest, {'public_payloads': {
            'public/source_task.txt': {'sha256': m.TASK_SHA},
            'public/public_regression_failure.txt': {'sha256': m.FAILURE_SHA}}})
        patch(m, 'INPUT_MANIFEST_SHA', input_sha)
        self.query_dir = self.pilot / 'runs'; self.query_dir.mkdir()
        slots = [dict(slot=i, cidfile=str(self.query_dir / ('test_%02d.cid' % i)),
                      stdout=str(self.query_dir / ('test_%02d.stdout.log' % i)),
                      stderr=str(self.query_dir / ('test_%02d.stderr.log' % i)),
                      argv_sha256=('%064x' % i)) for i in range(1, 5)]
        self.binding = self.pilot / 'binding.json'
        binding = {'input_manifest_sha256': input_sha, 'snapshot': str(self.snapshot),
                   'snapshot_tree': {'sha256': m.SNAPSHOT_SHA}, 'queries': [
                       {'id': 'read_public_test_function', 'path': str(test_text),
                        'sha256': query_hashes['read_public_test_function'], 'executor': 'read exact bytes'},
                       {'id': 'read_edited_production_function', 'path': str(prod_text),
                        'sha256': query_hashes['read_edited_production_function'], 'executor': 'read exact bytes'},
                       {'id': m.TEST_QUERY, 'slots': slots}]}
        binding_sha = put_json(self.binding, binding); patch(m, 'QUERY_BINDING_SHA', binding_sha)

        self.projection = self.private / 'projection'
        (self.projection / 'runtime/bin').mkdir(parents=True)
        (self.projection / 'runtime/bin/python').write_text('CPU fake binary')
        for name in ('default', 'pgdriver'):
            (self.projection / 'deps' / name).mkdir(parents=True)
            (self.projection / 'deps' / name / 'dependency.py').write_text('CPU fake')
        files = source.tree(self.projection)
        projection_manifest = dict(version=1, python='3.8', blocked_packages=['django'],
            site_names=['default', 'pgdriver'], files={name: dict(sha256=digest,
                bytes=(self.projection / name).stat().st_size) for name, digest in files.items()})
        projection_sha = put_json(self.projection / 'manifest.json', projection_manifest)
        patch(m, 'PROJECTION_SHA', projection_sha)
        self.profile = self.private / 'profile.json'
        profile_sha = put_json(self.profile, dict(model_id='qwen38-27b-fp8', context=32768, output=8192))
        patch(m, 'PROFILE_SHA', profile_sha); patch(source, 'PROFILE_SHA', profile_sha)
        bin_dir = self.private / 'bin'; bin_dir.mkdir()
        for name in ('opencode', 'rg'): (bin_dir / name).write_text('CPU fake binary')
        def forbidden(*args, **kwargs): raise AssertionError('CPU prepare touched a backend or process')
        h = SimpleNamespace(deps=deps,
            teacher=SimpleNamespace(_vllm_profile_fields=lambda _: None,
                validate_vllm_model_profile=forbidden, verify_vllm_backend=forbidden),
            actor=SimpleNamespace(config=lambda profile, seed: {'model': profile['model_id'], 'seed': seed}),
            tools=SimpleNamespace(OPENCODE=bin_dir / 'opencode', RG=bin_dir / 'rg', ripgrep_binding=lambda: None))
        patch(source, 'helpers', lambda: h)

        score_dir = self.private / 'score_asset'; score_dir.mkdir()
        qual = score_dir / 'qualification.json'
        qual_sha = put_json(qual, {'cases': {'source': {'id': m.SOURCE_ID, 'base': m.BASE,
            'focus_labels': ['focus'], 'regression_labels': ['test' + str(i) for i in range(65)]}}})
        patch(m, 'QUALIFICATION_SHA', qual_sha)
        self.score_asset = score_dir / 'asset.json'
        score_sha = put_json(self.score_asset, {'source_instance': m.SOURCE_ID, 'source_base_commit': m.BASE,
            'evaluator_reproduction': {'command_65_labels_ref': str(qual)}})
        patch(m, 'SCORE_ASSET_SHA', score_sha)
        replay = score_dir / 'CURRENT_REPLAY_V1'; replay.mkdir()
        replay_sha = put_json(replay / 'RESULT_V1.json', {'CPU': True}); patch(m, 'REPLAY_RESULT_SHA', replay_sha)
        argv_sha = put_json(replay / 'ARGV_219.json', ['CPU', 'aggregation', 'expressions'])
        patch(m, 'ARGV_219_SHA', argv_sha)
        self.protocol = self.private / 'protocol.json'
        self.value = dict(schema=m.SCHEMA,
            input_manifest=dict(path=str(self.input_manifest), sha256=input_sha),
            query_binding=dict(path=str(self.binding), sha256=binding_sha),
            snapshot=dict(path=str(self.snapshot), tree_sha256=m.SNAPSHOT_SHA),
            score_asset=dict(path=str(self.score_asset), sha256=score_sha),
            projection=dict(path=str(self.projection), sha256=projection_sha),
            profile=dict(path=str(self.profile), sha256=profile_sha),
            program=dict(memory=[], queries=[]), query_results=[])
        self.root = self.private / 'episode'

    def prepare(self):
        digest = put_json(self.protocol, self.value)
        with mock.patch.object(source.subprocess, 'run', side_effect=AssertionError('CPU subprocess')), \
             mock.patch.object(source.subprocess, 'Popen', side_effect=AssertionError('CPU process')):
            return m.prepare(self.protocol, digest, self.root), digest

    def test_prepare_and_verify_preserve_candidate_and_hide_unselected_queries(self):
        out, protocol_sha = self.prepare(); manifest, _, actor, _ = m.verify(self.root, out['manifest_sha256'])
        self.assertEqual(manifest['caps'], m.CAPS)
        self.assertEqual(manifest['caps'], dict(posts=12, seconds=300, combined_wire_bytes=16 * 1024**2))
        self.assertEqual(manifest['baseline'], manifest['work'])
        self.assertEqual(set(actor['sites']), {'default'})
        self.assertEqual(set(x.name for x in (self.root / 'inputs').iterdir()),
                         {'task.txt', 'public_task.txt', 'public_failure.txt', 'guest.py', 'opencode.json'})
        prompt = (self.root / 'inputs/task.txt').read_text()
        self.assertIn('Public source issue.', prompt); self.assertIn('Public regression failed.', prompt)
        self.assertNotIn('Public function.', prompt); self.assertFalse(any((self.root / 'scoring').iterdir()))
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(m.main(['--verify', '--protocol', str(self.protocol), '--protocol-sha', protocol_sha,
                                     '--root', str(self.root), '--manifest-sha', out['manifest_sha256']]), 0)

    def test_selected_query_and_memory_are_the_only_added_text(self):
        self.value['program'] = dict(memory=['Keep the original fix.'], queries=['read_public_test_function'])
        self.value['query_results'] = [dict(id='read_public_test_function')]
        out, _ = self.prepare(); manifest, _, _, _ = m.verify(self.root, out['manifest_sha256'])
        prompt = (self.root / 'inputs/task.txt').read_text()
        self.assertIn('Keep the original fix.', prompt); self.assertIn('Public function.', prompt)
        self.assertNotIn('Production function.', prompt); self.assertEqual(len(manifest['query_inputs']), 1)

    def test_missing_result_and_target_leak_refused_before_prepare(self):
        self.value['program']['queries'] = ['read_public_test_function']
        with self.assertRaisesRegex(ValueError, 'one explicit result'): self.prepare()
        self.assertFalse(self.root.exists())
        self.value['program'] = dict(memory=['future target 34176'], queries=[])
        with self.assertRaisesRegex(ValueError, 'private marker'): self.prepare()
        self.assertFalse(self.root.exists())

    def test_snapshot_patch_or_git_and_wrong_profile_fail_closed(self):
        (self.snapshot / 'test.patch').write_text('private')
        with self.assertRaisesRegex(ValueError, 'snapshot bytes'): self.prepare()
        self.assertFalse(self.root.exists()); (self.snapshot / 'test.patch').unlink()
        (self.snapshot / '.git').mkdir()
        with self.assertRaises(ValueError): self.prepare()
        self.assertFalse(self.root.exists()); (self.snapshot / '.git').rmdir()
        self.value['profile']['sha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'profile'): self.prepare()
        self.assertFalse(self.root.exists())

    def test_work_can_change_but_baseline_or_prompt_cannot_be_rebound(self):
        out, _ = self.prepare(); digest = out['manifest_sha256']
        (self.root / 'work/django/db/models/expressions.py').write_text('continued repair\n')
        m.verify(self.root, digest, initial=False)
        with self.assertRaises(ValueError): m.verify(self.root, digest, initial=True)
        (self.root / 'inputs/task.txt').write_text('tampered\n')
        manifest_path = self.root / 'manifest.json'; value = json.loads(manifest_path.read_text())
        value['inputs'] = source.tree(self.root / 'inputs')
        value['wrapped_prompt_sha256'] = sha(self.root / 'inputs/task.txt')
        with self.assertRaises(ValueError): m.verify(self.root, put_json(manifest_path, value), initial=False)

    def test_selected_test_requires_bound_actual_receipt(self):
        self.value['program']['queries'] = [m.TEST_QUERY]
        receipt = self.query_dir / 'test_01.receipt.json'
        self.value['query_results'] = [dict(id=m.TEST_QUERY, slot=1,
                                           receipt=dict(path=str(receipt), sha256='0' * 64))]
        with self.assertRaises((ValueError, FileNotFoundError)): self.prepare()
        self.assertFalse(self.root.exists())

    def test_scoring_callback_cannot_claim_success(self):
        out, protocol_sha = self.prepare(); prepared = m.verify(self.root, out['manifest_sha256'])
        calls = []
        def fake_execute(root, digest, data, verify, **kwargs):
            calls.append(kwargs); pending = kwargs['score_prepared'](root, data[0], data[1])
            self.assertEqual(pending['status'], 'PENDING_EXTERNAL'); self.assertIs(pending['passed'], False)
            self.assertFalse(source.successful({'status': 'ACTOR_RETURNED', 'actor_exit': 0,
                'accounting': {'integrity_passed': True, 'actual_forwarded_posts': 1}, 'scoring': pending}))
            return {'status': 'CPU_FAKE', 'recovery_success': False}
        with mock.patch.object(source, 'execute_prepared', side_effect=fake_execute):
            result = m.execute(self.root, out['manifest_sha256'], self.protocol, protocol_sha)
        self.assertFalse(result['recovery_success']); self.assertEqual(len(calls), 1)


if __name__ == '__main__':
    unittest.main()


class CheckpointContracts(unittest.TestCase):
    """Synthetic filesystem/native-event controls, never model evidence."""
    def setUp(self):
        RuntimeContracts.setUp(self)
        def patch(obj, key, value):
            p = mock.patch.object(obj, key, value); p.start(); self.patches.append(p)
        self.parent = self.private / 'closed_source'; self.parent.mkdir()
        self.capture = self.parent / 'production_prefix_checkpoint'; self.capture.mkdir()
        self.work = self.capture / 'work'; self.work.mkdir()
        self.rel = 'lib/mpl_toolkits/axes_grid1/axes_grid.py'
        file = self.work / self.rel; file.parent.mkdir(parents=True); file.write_text('line one\nline two\n')
        (self.parent / 'inputs').mkdir(); (self.parent / 'wire').mkdir()
        (self.parent / 'inputs/source_task.txt').write_text('Public Matplotlib change.\n')
        (self.parent / 'inputs/task.txt').write_text('Original wrapper\n')
        self.qual = self.private / 'qualified'; self.qual.mkdir()
        shutil = __import__('shutil'); shutil.copytree(self.work, self.qual / 'clean_base')
        (self.qual / 'task.txt').write_text('Public Matplotlib change.\n')
        (self.qual / 'test.patch').write_text('private scoring overlay')
        self.registry = self.private / 'registry.json'; reg_sha = put_json(self.registry, {'CPU': 'qualified source stub'})
        self.body = {'messages':[{'role':'user','content':'Public Matplotlib change.'},
                                {'role':'tool','content':'UNRETAINED RECORD'}], 'seed':17,
                     'chat_template_kwargs':{'enable_thinking':True,'reasoning_effort':'low'}}
        put_json(self.capture / 'request.body', self.body)
        put_json(self.parent / 'wire/00006.incoming.json', self.body)
        source_manifest = dict(source='matplotlib__matplotlib-26020', registry={'path':str(self.registry),'sha256':reg_sha},
            profile={'path':str(self.profile),'sha256':m.PROFILE_SHA},
            projection={'path':str(self.projection),'sha256':m.PROJECTION_SHA},
            public_task_sha256=sha(self.parent/'inputs/source_task.txt'),
            wrapped_prompt_sha256=sha(self.parent/'inputs/task.txt'))
        source_sha = put_json(self.parent / 'manifest.json', source_manifest)
        parent_sha = put_json(self.parent / 'receipt.json', dict(manifest_sha256=source_sha, source='matplotlib__matplotlib-26020'))
        patch(m, 'CHECKPOINT_PARENT_RECEIPT_SHA', parent_sha)
        files = source.tree(self.work)
        map_sha = put_json(self.capture / 'files_sha256.json', dict(before=files, after=files, copied=files))
        capture_sha = put_json(self.capture / 'receipt.json', dict(status='READY', request=6,
            boundary='REQUEST_RECEIVED_BEFORE_FORWARD', copy_complete=True, manifest_sha256=source_sha,
            body_sha256=sha(self.capture/'request.body'), files_sha256=map_sha,
            incoming_request_sha256=sha(self.parent/'wire/00006.incoming.json')))
        patch(m, 'CHECKPOINT_SHA', capture_sha)
        self.catalog = self.private / 'catalog.json'
        catalog_sha = put_json(self.catalog, dict(schema='matplotlib26020_deferred_queries_v1',
            entries=[dict(id='q0', path=self.rel, start=1, end=1)]))
        self.value = dict(schema='matplotlib26020_checkpoint_resume_v1',
            checkpoint=dict(path=str(self.capture/'receipt.json'),sha256=capture_sha),
            registry=dict(path=str(self.registry),sha256=reg_sha), projection=source_manifest['projection'],
            profile=source_manifest['profile'],catalog=dict(path=str(self.catalog),sha256=catalog_sha),
            context='records',program=dict(memory=['Selected progress record.'],queries=['q0']))
        self.case = dict(spec=dict(repo='matplotlib/matplotlib',base_commit='a'*40),
            labels=dict(f2p=['focus'],ptp=['regression']),native_overlay={})
        self.reg = dict(actor_projection=self.value['projection'],source_result={'CPU':'qualification'})
        patch(source, 'source_input', lambda *args: (self.reg,self.case,self.qual))
        patch(source, 'scoring_dependencies', lambda *args: {'CPU':'frozen dependencies'})
        patch(source, 'projection_input', lambda *args: dict(runtime=self.projection/'runtime',sites={'default':self.projection/'deps/default'}))

    def prepare(self):
        digest = put_json(self.protocol, self.value)
        return m.prepare(self.protocol,digest,self.root), digest

    def test_prepare_deferred_shared_query_and_record_boundary(self):
        out,_=self.prepare(); manifest,_,_,_=m.verify(self.root,out['manifest_sha256'])
        text=(self.root/'inputs/task.txt').read_text()
        self.assertIn('Selected progress record.',text); self.assertNotIn('UNRETAINED RECORD',text)
        self.assertNotIn('line one',text); self.assertIn('/inputs/recover.py q0',text)
        self.assertEqual(manifest['caps'],dict(posts=6,seconds=180,combined_wire_bytes=8*1024**2))
        self.assertFalse(manifest['sampling']['native_thinking'])
        self.assertEqual(json.loads((self.root/'inputs/opencode.json').read_text())['compaction'],{'auto':False,'prune':False})
        self.assertEqual(source.tree(self.root/'work'),source.tree(self.work))
        self.assertNotIn('test.patch',source.tree(self.root/'inputs'))

    def test_full_history_is_distinct_and_program_cannot_smuggle_memory(self):
        self.value.update(context='full_history',program=dict(memory=[],queries=[]))
        out,_=self.prepare(); text=(self.root/'inputs/task.txt').read_text()
        self.assertIn('UNRETAINED RECORD',text); self.assertNotIn('Selected progress record.',text)
        self.assertIn('/inputs/recover.py q0',text)
        (self.root/'inputs/recover.py').write_text('tampered')
        with self.assertRaises(ValueError): m.verify(self.root,out['manifest_sha256'])

    def test_changed_capture_or_bad_catalog_rejected_before_root(self):
        (self.work/self.rel).write_text('tampered')
        with self.assertRaises(ValueError): self.prepare()
        self.assertFalse(self.root.exists())

    def test_fresh_root_cannot_be_inside_immutable_source_parent(self):
        self.root=self.capture/'unapproved_branch'
        with self.assertRaisesRegex(ValueError,'disjoint'): self.prepare()
        self.assertFalse(self.root.exists())
        (self.work/self.rel).write_text('line one\nline two\n')
        value=json.loads(self.catalog.read_text());value['entries'][0]['path']='../test.patch'
        self.value['catalog']['sha256']=put_json(self.catalog,value)
        with self.assertRaises(ValueError): self.prepare()
        self.assertFalse(self.root.exists())

    def test_execute_uses_distinct_callback_not_source_identity(self):
        out,p_sha=self.prepare()
        def fake(root,digest,prepared,verify,**kw):
            self.assertEqual(kw['mode'],'JOINT_CHECKPOINT_RECOVERY')
            self.assertIs(kw['score_prepared'],m.checkpoint_score)
            self.assertNotIn('request_policy',prepared[0])
            return {'status':'CPU_FAKE'}
        with mock.patch.object(source,'execute_prepared',side_effect=fake):
            self.assertEqual(m.execute(self.root,out['manifest_sha256'],self.protocol,p_sha)['status'],'CPU_FAKE')

    def test_client_reads_only_when_called_and_native_events_measure_cost(self):
        catalog={'q0':dict(id='q0',path=self.rel,start=1,end=1)}
        script=self.private/'recover.py'; script.write_bytes(m.recover_script(catalog,self.work).encode())
        # Writing the client performs no query; a later workspace change is observed.
        (self.work/self.rel).write_bytes(b'freshly acquired\nline two\n')
        import subprocess
        completed=subprocess.run([sys.executable,'-I',str(script),'q0'],capture_output=True,text=True)
        self.assertEqual(completed.returncode,0,completed.stderr)
        output=completed.stdout; value=json.loads(output)
        self.assertEqual(value['text'],'freshly acquired\n')
        event=dict(type='tool_use',part=dict(tool='bash',callID='native-q0',state=dict(status='completed',
            input=dict(command='/extra/bin/python -I /inputs/recover.py q0'),output=output,
            metadata=dict(exit=0,truncated=False,output=output),time=dict(start=1000,end=1011))))
        raw=self.private/'raw.jsonl'; raw.write_text(json.dumps(event)+'\n')
        usage=m.checkpoint_query_usage(raw,catalog)
        self.assertEqual((usage['status'],usage['invocations'],usage['bytes']),('MEASURED',1,len('freshly acquired\n')))
        self.assertEqual(usage['seconds'],.011)
        event['part']['state']['input']['command']+='; echo forged'
        raw.write_text(json.dumps(event)+'\n')
        self.assertEqual(m.checkpoint_query_usage(raw,catalog)['status'],'UNKNOWN')
        self.assertIsNone(m.checkpoint_query_usage(raw,catalog)['bytes'])
        for qid in ('../test.patch','q9'):
            self.assertNotEqual(subprocess.run([sys.executable,'-I',str(script),qid],capture_output=True).returncode,0)

    def test_rehashed_manifest_and_scoring_never_change_admission(self):
        out,_=self.prepare(); path=self.root/'manifest.json'; value=json.loads(path.read_text())
        value['sampling']['native_thinking']=True
        with self.assertRaises(ValueError): m.verify(self.root,put_json(path,value))
        self.assertFalse((self.root/'scoring/candidate').exists())
