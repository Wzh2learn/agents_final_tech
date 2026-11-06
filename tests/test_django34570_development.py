"""CPU-only boundary tests; no model, service, database or Docker invocation."""
from contextlib import nullcontext
import ast
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import threading
import socket
import socketserver
import stat
from types import SimpleNamespace
import unittest
from unittest.mock import patch

MODULE = Path(__file__).resolve().parents[1] / 'research/agent_frontier_portfolio_20261029/run_django34570_development.py'
spec = importlib.util.spec_from_file_location('django34570_development_tests', MODULE)
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


class Django34570Tests(unittest.TestCase):
    def test_readable_tree_rejects_git_links_and_nonabsolute_paths(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / 'ordinary.py').write_text('public base')
            self.assertEqual(set(runner.tree(root)), {'ordinary.py'})
            (root / '.git').mkdir()
            (root / '.git/objects').write_text('private history')
            with self.assertRaises(ValueError):
                runner.tree(root)
            with self.assertRaises(ValueError):
                runner.regular(Path('../parent'))
            if sys.platform != 'win32':
                (root / 'escape').symlink_to(root.parent)
                with self.assertRaises(ValueError):
                    runner.tree(root)

    def command(self, root):
        mounts = {'/root': {'source': str(root / 'work'), 'readonly': False},
                  '/deps': {'source': str(root / 'deps'), 'readonly': True}}
        cmd = ['docker', 'run', '--network', 'none', '--pull', 'never', '--read-only',
               '--workdir', '/root', '--entrypoint', '/extra/bin/python', '--cap-drop', 'ALL',
               '--security-opt', 'no-new-privileges', '--tmpfs', '/tmp:rw,nosuid,size=128m',
               '--tmpfs', '/home/agent:rw,nosuid,size=256m']
        for env in ('HOME=/home/agent', 'OPENCODE_DISABLE_MODELS_FETCH=1', 'PYTHONPATH=/deps',
                    'PATH=/extra/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin',
                    'PYTHONDONTWRITEBYTECODE=1', 'PYTEST_DISABLE_PLUGIN_AUTOLOAD=1',
                    'HYPOTHESIS_STORAGE_DIRECTORY=/tmp/hypothesis'):
            cmd += ['-e', env]
        for dst, mount in mounts.items():
            cmd += ['--mount', f'type=bind,src={mount["source"]},dst={dst}' + (',readonly' if mount['readonly'] else '')]
        return cmd + [runner.IMAGE, '-c', 'public entry'], mounts

    @unittest.skipUnless(os.name=='posix' and hasattr(socket,'AF_UNIX'),'native Unix socket qualification')
    def test_long_native_path_fails_but_frozen_short_path_really_binds(self):
        with tempfile.TemporaryDirectory(prefix='d34570-path-') as temp:
            root=Path(temp)/('deep_attempt_'+'x'*110);old=root/'bridge/model.sock';old.parent.mkdir(parents=True)
            with socket.socket(socket.AF_UNIX) as peer:
                with self.assertRaisesRegex(OSError,'path too long'):peer.bind(str(old))
            directory=runner.socket_directory(root);self.assertLessEqual(len(os.fsencode(directory/'model.sock')),103);self.assertEqual(directory,runner.socket_directory(root));identity=runner.create_socket_directory(directory)
            try:
                self.assertEqual(stat.S_IMODE(directory.stat().st_mode),0o755)
                with socketserver.UnixStreamServer(str(directory/'model.sock'),socketserver.BaseRequestHandler):self.assertTrue(stat.S_ISSOCK((directory/'model.sock').stat().st_mode))
            finally:runner.cleanup_socket_directory(directory,identity)
            self.assertFalse(directory.exists())
    @unittest.skipUnless(os.name=='posix','inode/UID owned socket cleanup')
    def test_socket_cleanup_preserves_foreign_content_and_wrong_inode(self):
        with tempfile.TemporaryDirectory() as temp:
            directory=runner.socket_directory(Path(temp));identity=runner.create_socket_directory(directory)
            try:
                with self.assertRaisesRegex(ValueError,'ownership/inode'):runner.cleanup_socket_directory(directory,(identity[0],identity[1]+1))
                foreign=directory/'model.sock';foreign.write_text('not a socket')
                with self.assertRaisesRegex(ValueError,'not an owned socket'):runner.cleanup_socket_directory(directory,identity)
                self.assertEqual(foreign.read_text(),'not a socket');foreign.unlink();extra=directory/'do_not_delete';extra.write_text('foreign')
                with self.assertRaisesRegex(ValueError,'unexpected'):runner.cleanup_socket_directory(directory,identity)
                self.assertTrue(extra.exists());extra.unlink()
            finally:runner.cleanup_socket_directory(directory,identity)
    @unittest.skipUnless(os.name=='posix','short path collision refusal')
    def test_existing_short_directory_never_reused_or_removed(self):
        with tempfile.TemporaryDirectory() as temp:
            directory=runner.socket_directory(Path(temp));identity=runner.create_socket_directory(directory)
            try:
                with self.assertRaises(FileExistsError):runner.create_socket_directory(directory)
                self.assertTrue(directory.exists())
            finally:runner.cleanup_socket_directory(directory,identity)
    def test_probe_handoff_is_readable_copy_without_mutating_frozen_source(self):
        with tempfile.TemporaryDirectory() as temp:
            task=Path(temp);source=task/'scoring/public_issue_probe.py';source.parent.mkdir();source.write_bytes(b'print("public")\n');source.chmod(0o600);out=task/'out';out.mkdir();before=runner.sha(source)
            with patch.object(runner,'TASK',task),patch.object(runner,'PINNED',{'scoring/public_issue_probe.py':before}):copy=runner.scoring_probe(out)
            self.assertEqual(runner.sha(copy),before);self.assertEqual(runner.sha(source),before)
            if os.name=='posix':self.assertEqual(stat.S_IMODE(source.stat().st_mode),0o600);self.assertEqual(stat.S_IMODE(copy.stat().st_mode),0o444)
            self.assertNotEqual(source,copy)
    def test_public_scoring_mounts_readable_handoff_not_private_source(self):
        with tempfile.TemporaryDirectory() as temp:
            task=Path(temp);root=task/'attempt';root.mkdir();source=task/'scoring/public_issue_probe.py';source.parent.mkdir();source.write_bytes(b'# public probe\n');source.chmod(0o600);commands=[]
            def restore(work,clean,candidate):candidate.mkdir();(candidate/'candidate.py').write_text('actual candidate')
            agg=SimpleNamespace(restore_candidate=restore);native=SimpleNamespace(__file__=str(MODULE),test=lambda *a:{'exit':1,'summary':[]})
            probe={'public_problem_results':{n:{'status':'RETURNED','row_count':0} for n in ('ManyToManyField','GenericForeignKey')}}
            def run(cmd,**kwargs):
                commands.append(cmd);return SimpleNamespace(returncode=0,stdout=json.dumps(probe).encode(),stderr=b'')
            with patch.object(runner,'TASK',task),patch.object(runner,'PINNED',{'scoring/public_issue_probe.py':runner.sha(source)}),patch.object(runner,'helpers',return_value=(agg,native)),patch.object(runner.subprocess,'run',side_effect=run):result=runner.evaluate(root,{'focus_labels':['one'],'regression_labels':['more']})
            mount=next(x for x in commands[0] if 'dst=/public_issue_probe.py' in x);self.assertIn(str(root/'scoring/public_issue_probe.py'),mount);self.assertTrue(mount.endswith(',readonly'));self.assertNotIn('src='+str(source)+',',mount);self.assertEqual(result['public_probe']['probe_copy_sha256'],runner.sha(source));self.assertFalse(result['semantics']['fixed']);self.assertEqual(result['model_calls'],0)

    def test_parent_mount_and_postgres_are_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            cmd, mounts = self.command(Path(temp))
            runner.audit_command(cmd, mounts)
            for wrong in [cmd[:-3] + ['--mount', f'type=bind,src={temp},dst=/private,readonly'] + cmd[-3:],
                          cmd[:-3] + ['-e', 'PGHOST=/research-pg'] + cmd[-3:],
                          [s.replace('dst=/deps,readonly', 'dst=/deps') for s in cmd],
                          [s.replace('--read-only', '--privileged') for s in cmd]]:
                with self.subTest(wrong=wrong):
                    with self.assertRaises(ValueError):
                        runner.audit_command(wrong, mounts)

    def test_combined_byte_cap_stops_response_without_alternative_transport(self):
        sent = []
        relay_calls = []
        def relay(client, upstream, path):
            relay_calls.append((upstream, path))
            client.sendall(b'1234')
            client.sendall(b'5678')
        count = [0]
        with self.assertRaises(RuntimeError):
            runner.relay_capped(SimpleNamespace(sendall=sent.append), 'original', 'raw', relay,
                                threading.Lock(), [3], count, 10)
        self.assertEqual(sent, [b'1234'])
        self.assertEqual(count, [4])
        self.assertEqual(relay_calls, [('original', 'raw')])
        with patch.object(runner.time, 'monotonic', return_value=11):
            with self.assertRaisesRegex(RuntimeError, 'episode deadline'):
                runner.relay_capped(SimpleNamespace(sendall=sent.append), 'original', 'raw', relay,
                                    threading.Lock(), [], [0], 100, deadline=10)
        self.assertEqual(sent, [b'1234'])

    def test_get_pipelining_and_conflicting_framing_cannot_bypass_post_meter(self):
        runner.check_http_frame(b'GET /v1/models HTTP/1.1\r\nHost: local\r\n\r\n')
        runner.check_http_frame(b'POST /v1/chat/completions HTTP/1.1\r\nContent-Length: 2\r\n\r\n{}')
        for request in (b'GET /v1/models HTTP/1.1\r\n\r\nPOST /v1/chat/completions HTTP/1.1\r\n\r\n',
                        b'POST /v1/chat/completions HTTP/1.1\r\nContent-Length: 2\r\nTransfer-Encoding: chunked\r\n\r\n{}',
                        b'POST /v1/chat/completions HTTP/1.1\r\nContent-Length: 2\r\nContent-Length: 2\r\n\r\n{}'):
            with self.subTest(request=request):
                with self.assertRaises(ValueError):
                    runner.check_http_frame(request)

    def test_exit_zero_is_insufficient_for_native_or_public_success(self):
        good1 = {'exit': 0, 'summary': ['Ran 1 test in 0.1s', 'OK']}
        good13 = {'exit': 0, 'summary': ['Ran 13 tests in 0.1s', 'OK']}
        returned = {'public_problem_results': {n: {'status': 'RETURNED', 'row_count': 0}
                    for n in ('ManyToManyField', 'GenericForeignKey')}}
        self.assertTrue(runner.score_semantics(good1, good13, 0, returned)['fixed'])
        raised = {'public_problem_results': {'ManyToManyField': {'status': 'RAISED', 'type': 'AttributeError'}}}
        self.assertFalse(runner.score_semantics(good1, good13, 0, raised)['fixed'])
        self.assertFalse(runner.score_semantics({'exit': 0, 'summary': ['OK']}, good13, 0, returned)['fixed'])
        self.assertFalse(runner.score_semantics(good1, {'exit': 1, 'summary': ['Ran 13 tests in 0.1s', 'FAILED']}, 0, returned)['fixed'])

    def test_frozen_manifest_and_work_mutation_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            task = Path(temp)
            root = task / 'attempts/one'
            root.mkdir(parents=True)
            file = root / 'bound.py'
            file.write_text('frozen')
            manifest = {'root': str(root), 'bindings': {str(file): runner.sha(file)}}
            runner.write_new(root / 'manifest.json', manifest)
            digest = runner.sha(root / 'manifest.json')
            file.write_text('changed')
            with patch.object(runner, 'TASK', task):
                with self.assertRaisesRegex(ValueError, 'bound input'):
                    runner.verify_prepared(root, digest)
            (root / 'manifest.json').write_text('{}')
            with self.assertRaisesRegex(ValueError, 'hash changed'):
                runner.read_checked(root / 'manifest.json', digest)

    def test_derived_harness_requires_reserved_parent_and_explicit_manifest(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / 'execution_manifest.json').write_text('{}')
            digest = runner.sha(root / 'execution_manifest.json')
            runner.write_new(root / 'reservation.json', {'outer_pid': os.getppid(),
                'execution_manifest_sha256': digest, 'mode': 'REAL_8B_NO_EXPERIENCE_DEVELOPMENT'})
            with patch.dict(os.environ, {'DJANGO34570_EXECUTION_MANIFEST_SHA': digest}):
                runner.guard_execution(root)
                (root / 'execution_manifest.json').write_text('changed')
                with self.assertRaises(ValueError):
                    runner.guard_execution(root)
            with patch.dict(os.environ, {'DJANGO34570_EXECUTION_MANIFEST_SHA': ''}):
                with self.assertRaises(ValueError):
                    runner.guard_execution(root)

    def test_stale_profile_pid_does_not_authorize_different_restoration(self):
        profile = {'pid': 1, 'server_executable_sha256': 'binary'}
        identity = {'pid': 99, 'argv': ['server', 'fixed'], 'cwd': '/fixed', 'executable_sha256': 'binary'}
        admission = {'owned_process': {'pid': 1, 'argv': identity['argv'], 'cwd': '/fixed'}}
        result = dict.fromkeys(('owned8b_restored_healthy', 'restored_exact_argv', 'shared35_unchanged', 'shared27_unchanged'), True)
        result['restored_8b_pid'] = 99
        agg = SimpleNamespace(verify_server_argv=lambda argv, profile: None)
        with patch.object(runner, 'helpers', return_value=(agg, None)):
            runner.verify_restoration(profile, admission, result, identity)
            for wrong in ({**identity, 'cwd': '/other'}, {**identity, 'pid': 1}, {**identity, 'argv': ['another']}):
                with self.assertRaises(ValueError):
                    runner.verify_restoration(profile, admission, result, wrong)

    def test_fake_forwarded_receipt_rejected_and_unknown_usage_is_not_zero(self):
        with tempfile.TemporaryDirectory() as temp:
            case = Path(temp)
            (case / 'raw.jsonl').write_text('actual raw')
            entry = {'request_body_file': '00001.json', 'request_body_sha256': 'bodyhash', 'temperature': 0.2,
                     'seed': 17, 'model': 'qwen3-8b-qual', 'max_tokens': 8192,
                     'chat_template_kwargs': {'enable_thinking': False}}
            receipt = {'raw_sha256': runner.sha(case / 'raw.jsonl'), 'sampling_metadata': [entry],
                       'post_content_lengths': [100], 'response_wire_bytes': 0}
            agg = SimpleNamespace(execution_integrity=lambda c, r: {'passed': True, 'counted_posts': 1},
                provider_usage=lambda c, r: {'reported_tokens_known': 0, 'unknown_usage_requests': ['00001.json'],
                                            'response_bindings': []})
            ledger = case / 'forward_ledger.jsonl'
            (case / 'sampling_metadata.jsonl').write_text(json.dumps(entry) + '\n')
            (case / 'model_request_bodies').mkdir()
            (case / 'model_request_bodies/00001.json').write_text(json.dumps(entry))
            ledger.write_text(json.dumps({'request': '00001.json', 'event': 'forwarded', 'request_sha256': 'FAKE'}) + '\n')
            with patch.object(runner, 'helpers', return_value=(agg, None)):
                with self.assertRaisesRegex(ValueError, 'fake/unbound'):
                    runner.generation_accounting(case, receipt)
                ledger.write_text(json.dumps({'request': '00001.json', 'event': 'attempt'}) + '\n' +
                                  json.dumps({'request': '00001.json', 'event': 'forwarded', 'request_sha256': 'bodyhash'}) + '\n')
                result = runner.generation_accounting(case, receipt)
                self.assertIsNone(result['reported_provider_tokens_known'])
                self.assertIsNone(result['monetary_cost'])
                self.assertFalse(result.get('fixed', False))
                (case / 'model_request_bodies/00001.json').write_text(json.dumps({**entry, 'seed': 18}))
                with self.assertRaisesRegex(ValueError, 'actual request body'):
                    runner.generation_accounting(case, receipt)

    def test_scoring_error_does_not_become_fixed_or_erase_generation_failure(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / 'execution_manifest.json').write_text('{}')
            agg = SimpleNamespace(validate_model_profile=lambda *a: {}, verify_live_backend=lambda *a: None)
            frozen = {'manifest_sha256': 'manifest', 'admission_sha256': 'admission', 'result_sha256': 'result',
                      'identity': {'pid': 7}}
            def checked(path, digest):
                return frozen if Path(path).name == 'execution_manifest.json' else {}
            with patch.object(runner, 'queue_lock', return_value=nullcontext()), \
                 patch.object(runner, 'read_checked', side_effect=checked), \
                 patch.object(runner, 'verify_prepared', return_value={}), \
                 patch.object(runner, 'helpers', return_value=(agg, None)), \
                 patch.object(runner, 'process_identity', return_value={'pid': 7}), \
                 patch.object(runner, 'verify_restoration'), \
                 patch.object(runner.subprocess, 'run', side_effect=subprocess_error()), \
                 patch.object(runner, 'evaluate', side_effect=ValueError('failed scorer')):
                result = runner.execute(root, 'explicit')
            self.assertEqual(result['status'], 'GENERATION_FAILED')
            self.assertIsNone(result['actual_forwarded_posts'])
            self.assertIsNone(result['scoring'])
            self.assertIn('scoring_error', result)
            self.assertTrue((root / 'reservation.json').is_file())
            self.assertTrue((root / 'result.json').is_file())

    @unittest.skipUnless(Path('/home/testuser/wzh/research_evidence/agent_skill_method_20261029/run_skill_episode_output8192.py').is_file(), 'GB10 frozen derive asset only')
    def test_real_derive_compiles_and_has_no_old_source_or_pg(self):
        # Pure derivation only; deliberately never executes the resulting harness.
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            profile = {'host': '127.0.0.1', 'port': 18104, 'model_id': 'qwen3-8b-qual', 'context': 32768, 'output': 8192}
            code = runner.derive(root, profile)
            compile(code, '<test-bound-harness>', 'exec')
            self.assertNotIn('django_aggregation_qualification', code)
            self.assertNotIn('research-pg', code)
            self.assertNotIn('7201', code)
            self.assertIn("{'enable_thinking':False}", code)
            self.assertIn('timeout=1200)', code)
            self.assertIn('post_count[0]>=48', code)
            self.assertIn("raise SystemExit(0)\nif json.loads(command_path", code)
            self.assertIn('episode_deadline[0]=time.monotonic()+1200', code)

    @unittest.skipUnless(os.name=='posix' and Path('/home/testuser/wzh/research_evidence/agent_skill_method_20261029/run_skill_episode_output8192.py').is_file(),'GB10 derived startup CPU control')
    def test_actual_derived_bind_failure_cleans_only_its_socket(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);profile={'host':'127.0.0.1','port':18104,'model_id':'qwen3-8b-qual','context':32768,'output':8192};code=runner.derive(root,profile);directory=runner.socket_directory(root);self.assertIn('bridge=Path('+repr(str(directory))+')',code);self.assertNotIn(str(root/'bridge'),code)
            nodes=[n for n in ast.parse(code).body if isinstance(n,ast.Try) and n.body and isinstance(n.body[0],ast.Assign) and any(isinstance(t,ast.Name) and t.id=='bridge_identity' for t in n.body[0].targets)];self.assertEqual(len(nodes),1)
            def failing_server(path,handler):
                with socket.socket(socket.AF_UNIX) as peer:peer.bind(path)
                raise OSError('MOCK failure after native socket bind; no model/Docker')
            namespace={'server':None,'server_started':False,'bridge_identity':None,'bridge':directory,'sockpath':directory/'model.sock','Server':failing_server,'Handler':object,'create_socket_directory':runner.create_socket_directory,'cleanup_socket_directory':runner.cleanup_socket_directory}
            with self.assertRaisesRegex(OSError,'MOCK failure'):exec(compile(ast.Module(body=nodes,type_ignores=[]),'<actual-derived-bind-finally>','exec'),namespace)
            self.assertFalse(directory.exists())

    @unittest.skipUnless((runner.EVAL/'manual_restore_v1/RESULT.json').is_file(),'GB10 closed manual receipt schema only')
    def test_real_manual_receipt_schema_parses_without_any_live_identity_probe(self):
        with patch.object(runner,'process_identity',side_effect=AssertionError('no live probe')),patch.object(runner,'process_identity_full',side_effect=AssertionError('no live probe')):
            reference,process=runner.latest_restore_reference(runner.EVAL/'manual_restore_v1/RESULT.json',runner.MANUAL_RESTORE_SHA)
        self.assertEqual(reference['schema'],'manual_restore_v1_known_sha_status_health_contract');self.assertEqual(set(process),{'pid','start_ticks','argv','cwd','exe'})

    @unittest.skipUnless(Path('/home/testuser/wzh/research_evidence/agent_skill_method_20261029/run_skill_episode_output8192.py').is_file(), 'GB10 stable restore function only')
    def test_independent_restore_discards_actor_test_and_config_edits(self):
        agg, _ = runner.helpers()
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            work, clean, out = root / 'work', root / 'frozen', root / 'score'
            for path in (work, clean):
                (path / 'tests').mkdir(parents=True)
                (path / 'tests/test_target.py').write_text('frozen tests' if path == clean else 'fake pass')
                (path / 'setup.cfg').write_text('fixed config' if path == clean else 'skip everything')
                (path / 'django').mkdir()
            (work / 'django/repair.py').write_text('actual candidate')
            (work / 'conftest.py').write_text('skip scoring')
            agg.restore_candidate(work, clean, out)
            self.assertEqual((out / 'tests/test_target.py').read_text(), 'frozen tests')
            self.assertEqual((out / 'setup.cfg').read_text(), 'fixed config')
            self.assertEqual((out / 'django/repair.py').read_text(), 'actual candidate')
            self.assertFalse((out / 'conftest.py').exists())
            self.assertEqual((work / 'tests/test_target.py').read_text(), 'fake pass')


class LatestRestorationTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.private=Path(self.temp.name).resolve();self.window=self.private/'window';self.window.mkdir();self.eval=self.private/'eval';(self.eval/'RUN_v2').mkdir(parents=True);self.root=self.private/'attempt';self.root.mkdir()
        self.profile={'pid':1,'server_executable_sha256':'1'*64,'model_id':'qwen3-8b-qual','host':'127.0.0.1','port':18104,'context':32768,'output':8192,'gguf_path':'/home/testuser/wzh/models/gguf/qwen3-8b/Qwen3-8B-Q4_K_M.gguf','gguf_sha256':'d98cdcbd03e17ce47681435b5150e34c1417f50b5c0019dd560e4882c5745785'}
        argv=['/original/server','-m',self.profile['gguf_path'],'--host','127.0.0.1','--port','18104','--alias','qwen3-8b-qual','-c','32768','-n','8192','-np','1','--no-context-shift','--jinja','-ngl','999'];self.original={'pid':1,'start_ticks':'10','argv':argv,'cwd':'/fixed','exe':argv[0]};self.admission={'owned_process':self.original};self.legacy={key:True for key in ('owned8b_restored_healthy','restored_exact_argv','shared35_unchanged','shared27_unchanged')};self.legacy.update(restored_8b_pid=2,status='TRAINING_CHILDREN_RETURNED')
        self.restored={**self.original,'pid':99,'start_ticks':'999'};self.identity={**self.restored,'argv_sha256':'a'*64,'executable_sha256':'1'*64};self.latest={'status':'ALL_FIVE_ARMS_RETURNED','restored_healthy':True,'shared35_unchanged':True,'shared27_unchanged':True,'restored_process':self.restored,'window_wall_seconds':100.};self.latest_path=self.eval/'RUN_v2/RESULT.json';self.save(self.latest_path,self.latest)
        self.profile_path=self.private/'profile.json';self.save(self.profile_path,self.profile);self.save(self.window/'ADMISSION.json',self.admission);self.save(self.window/'RESULT.json',self.legacy)
        for name,value in [('PRIVATE',self.private),('EVAL',self.eval),('WINDOW',self.window),('PROFILE',self.profile_path),('PROFILE_SHA',runner.sha(self.profile_path))]:
            mock=patch.object(runner,name,value);mock.start();self.addCleanup(mock.stop)
        self.agg=SimpleNamespace(verify_server_argv=lambda *a:None,validate_model_profile=lambda *a:self.profile,verify_live_backend=lambda p:{'pid':p['pid']})
        self.helper=patch.object(runner,'helpers',return_value=(self.agg,None));self.helper.start();self.addCleanup(self.helper.stop)
    def save(self,path,value):path.write_text(json.dumps(value),encoding='utf8')
    def refs(self):return runner.sha(self.window/'ADMISSION.json'),runner.sha(self.window/'RESULT.json')
    def bind(self,latest=True):
        a,r=self.refs()
        with patch.object(runner,'queue_lock',return_value=nullcontext()),patch.object(runner,'verify_prepared',return_value={}),patch.object(runner,'process_identity_full',return_value=self.identity),patch.object(runner,'process_identity',return_value={**self.identity,'pid':2}):
            return runner.bind_runtime(self.root,'prepared',a,r,**({'latest_restore_path':self.latest_path,'latest_restore_sha':runner.sha(self.latest_path)} if latest else {}))
    def test_legacy_default_execution_manifest_fields_and_PID_unchanged(self):
        result=self.bind(False);self.assertEqual(set(result),{'execution_manifest_sha256','manifest_sha256','admission_sha256','result_sha256','identity','live_backend','status'});self.assertEqual(result['identity']['pid'],2);self.assertNotIn('latest_restore',runner.read_checked(self.root/'execution_manifest.json',result['execution_manifest_sha256']))
    def test_full_process_adapter_adds_executable_path_without_changing_legacy_shape(self):
        legacy={k:v for k,v in self.identity.items() if k!='exe'}
        with patch.object(runner,'process_identity',return_value=legacy),patch.object(runner.os,'readlink',return_value=self.restored['exe']) as link:value=runner.process_identity_full(99)
        self.assertEqual(value,self.identity);self.assertNotIn('exe',legacy);link.assert_called_once_with(Path('/proc/99/exe'))
    def test_qualified_latest_binds_exact_closed_source_and_complete_identity(self):
        result=self.bind();self.assertEqual(result['identity'],self.identity);self.assertEqual(result['latest_restore'],{'path':str(self.latest_path),'sha256':runner.sha(self.latest_path),'schema':'hf_evaluation_closed_restored_healthy_v1'});self.assertEqual(result['live_backend'],{'pid':99})
    def test_RUN_v3_reuses_the_same_closed_restored_contract(self):
        directory=self.eval/'RUN_v3';directory.mkdir();path=directory/'RESULT.json';self.save(path,self.latest);reference,process=runner.latest_restore_reference(path,runner.sha(path));self.assertEqual(reference['schema'],'hf_evaluation_closed_restored_healthy_v1');self.assertEqual(process,self.restored)
    def test_numbered_window_path_closed_status_and_health_are_required(self):
        for name in ['RUN_v0','RUN_v03','RUN_v3_other','other']:
            directory=self.eval/name;directory.mkdir();path=directory/'RESULT.json';self.save(path,self.latest)
            with self.subTest(path=name),self.assertRaisesRegex(ValueError,'schema/path'):runner.latest_restore_reference(path,runner.sha(path))
        directory=self.eval/'RUN_v4';directory.mkdir();path=directory/'RESULT.json'
        for changes in [{'status':'STARTED'},{'restored_healthy':False},{'restored_healthy':None}]:
            self.save(path,{**self.latest,**changes})
            with self.subTest(changes=changes),self.assertRaisesRegex(ValueError,'not closed and healthy'):runner.latest_restore_reference(path,runner.sha(path))
        missing={k:v for k,v in self.latest.items() if k!='restored_healthy'};self.save(path,missing)
        with self.assertRaisesRegex(ValueError,'not closed and healthy'):runner.latest_restore_reference(path,runner.sha(path))
    def test_latest_PID_start_time_argv_exe_cwd_and_binary_must_match(self):
        for wrong in [{**self.identity,'pid':100},{**self.identity,'start_ticks':'1000'},{**self.identity,'cwd':'/other'},{**self.identity,'exe':'/other/server'},{**self.identity,'argv':['different']},{**self.identity,'executable_sha256':'0'*64}]:
            with self.subTest(wrong=wrong),self.assertRaisesRegex(ValueError,'actual process'):runner.verify_latest_restoration(self.profile,self.admission,self.legacy,self.restored,wrong)
    def test_BF16_or_adapter_original_admission_is_rejected(self):
        for argv in [[*self.original['argv'],'--lora','/adapter.gguf'],[s.replace(self.profile['gguf_path'],'/HF-BOUND-BF16.gguf') for s in self.original['argv']]]:
            admission={'owned_process':{**self.original,'argv':argv}}
            with self.subTest(argv=argv),self.assertRaisesRegex(ValueError,'unadapted owned Q4'):runner.verify_latest_restoration(self.profile,admission,self.legacy,self.restored,self.identity)
    def test_BF16_latest_restored_process_rejected(self):
        bad={**self.restored,'argv':self.restored['argv']+['--lora','adapter']}
        with self.assertRaisesRegex(ValueError,'differs from original'):runner.verify_latest_restoration(self.profile,self.admission,self.legacy,bad,{**self.identity,'argv':bad['argv']})
    def test_source_sha_health_false_shared_false_and_started_rejected(self):
        with self.assertRaisesRegex(ValueError,'hash changed'):runner.latest_restore_reference(self.latest_path,'0'*64)
        for changes in [{'restored_healthy':False},{'shared35_unchanged':False},{'shared27_unchanged':False},{'status':'STARTED'},{'restoration_error':{'message':'failed'}}]:
            self.save(self.latest_path,{**self.latest,**changes})
            with self.subTest(changes=changes),self.assertRaises(ValueError):runner.latest_restore_reference(self.latest_path,runner.sha(self.latest_path))
    def test_source_path_outside_private_or_alias_is_rejected(self):
        wrong=self.private/'unknown.json';self.save(wrong,self.latest)
        with self.assertRaisesRegex(ValueError,'schema/path'):runner.latest_restore_reference(wrong,runner.sha(wrong))
        alias=self.latest_path.parent/'..'/'RUN_v2/RESULT.json'
        with self.assertRaisesRegex(ValueError,'canonical'):runner.latest_restore_reference(alias,runner.sha(self.latest_path))
        if os.name=='posix':
            link=self.eval/'link';link.symlink_to(self.eval/'RUN_v2',target_is_directory=True)
            with self.assertRaisesRegex(ValueError,'non-symlink'):runner.latest_restore_reference(link/'RESULT.json',runner.sha(self.latest_path))
    def test_harness_guard_rechecks_latest_source_and_full_runtime(self):
        result=self.bind();digest=result['execution_manifest_sha256'];runner.write_new(self.root/'reservation.json',{'outer_pid':os.getppid(),'execution_manifest_sha256':digest,'mode':'REAL_8B_NO_EXPERIENCE_DEVELOPMENT'})
        with patch.dict(os.environ,{'DJANGO34570_EXECUTION_MANIFEST_SHA':digest}),patch.object(runner,'process_identity_full',return_value=self.identity):runner.guard_execution(self.root)
        with patch.dict(os.environ,{'DJANGO34570_EXECUTION_MANIFEST_SHA':digest}),patch.object(runner,'process_identity_full',return_value={**self.identity,'start_ticks':'1000'}),self.assertRaisesRegex(ValueError,'actual process'):runner.guard_execution(self.root)
        self.save(self.latest_path,{**self.latest,'restored_healthy':False})
        with patch.dict(os.environ,{'DJANGO34570_EXECUTION_MANIFEST_SHA':digest}),patch.object(runner,'process_identity_full',return_value=self.identity),self.assertRaisesRegex(ValueError,'hash changed'):runner.guard_execution(self.root)
    def test_outer_execute_rechecks_frozen_reference_before_any_subprocess(self):
        result=self.bind();self.save(self.latest_path,{**self.latest,'restored_healthy':False})
        with patch.object(runner,'queue_lock',return_value=nullcontext()),patch.object(runner,'verify_prepared',return_value={}),patch.object(runner,'process_identity_full',return_value=self.identity),patch.object(runner.subprocess,'run') as run,self.assertRaisesRegex(ValueError,'hash changed'):runner.execute(self.root,result['execution_manifest_sha256'])
        run.assert_not_called();self.assertFalse((self.root/'reservation.json').exists())
    def test_path_SHA_pair_only_bind_runtime_CLI(self):
        import contextlib,io
        for args in [['bind-runtime','--root',str(self.root),'--manifest-sha','m','--admission-sha','a','--result-sha','r','--latest-restore-result',str(self.latest_path)],['execute','--root',str(self.root),'--manifest-sha','m','--latest-restore-result',str(self.latest_path),'--latest-restore-sha','s']]:
            with self.subTest(args=args),contextlib.redirect_stderr(io.StringIO()),self.assertRaises(SystemExit):runner.main(args)
        with patch.object(runner,'bind_runtime',return_value={}) as bind,contextlib.redirect_stdout(io.StringIO()):runner.main(['bind-runtime','--root',str(self.root),'--manifest-sha','m','--admission-sha','a','--result-sha','r','--latest-restore-result',str(self.latest_path),'--latest-restore-sha','s'])
        self.assertEqual(bind.call_args.kwargs,{'latest_restore_path':self.latest_path,'latest_restore_sha':'s'})
        with patch.object(runner,'bind_runtime',return_value={}) as legacy,contextlib.redirect_stdout(io.StringIO()):runner.main(['bind-runtime','--root',str(self.root),'--manifest-sha','m','--admission-sha','a','--result-sha','r'])
        legacy.assert_called_once_with(self.root,'m','a','r')
        with self.assertRaisesRegex(ValueError,'together'):runner.bind_runtime(self.root,'m','a','r',latest_restore_path=self.latest_path)
    def test_known_manual_schema_has_exact_SHA_status_contract_not_fake_bool(self):
        manual=self.eval/'manual_restore_v1';manual.mkdir();path=manual/'RESULT.json';value={'status':'ORIGINAL_Q4_RESTORED_AFTER_PREGENERATION_IDENTITY_RACE','health_gets':4,'model_generation_posts':0,'shared35_unchanged':True,'shared27_unchanged':True,'restored_process':self.restored};self.save(path,value);digest=runner.sha(path)
        with patch.object(runner,'MANUAL_RESTORE_SHA',digest):reference,process=runner.latest_restore_reference(path,digest)
        self.assertEqual(reference['schema'],'manual_restore_v1_known_sha_status_health_contract');self.assertEqual(process,self.restored);self.assertNotIn('restored_healthy',value)
        with self.assertRaisesRegex(ValueError,'contract differs'):runner.latest_restore_reference(path,digest)


def subprocess_error():
    import subprocess
    return subprocess.TimeoutExpired(['owned harness'], 1320, output=b'partial', stderr=b'error')


if __name__ == '__main__':
    unittest.main()
