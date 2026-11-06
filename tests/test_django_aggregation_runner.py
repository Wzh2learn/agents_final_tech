"""Boundary tests for the private Django research runner; no services/models."""
import hashlib
import importlib.util
import json
import http.client
import socket
import socketserver
import threading
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'research/agent_frontier_portfolio_20261029')]
SCRIPT = ROOT / 'research/agent_frontier_portfolio_20261029/run_django_aggregation_agent_20261106.py'
spec = importlib.util.spec_from_file_location('django_research_runner_test', SCRIPT)
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


class DjangoResearchRunnerTests(unittest.TestCase):
    def test_transport_binding_preserves_generated_handler_indentation(self):
        code = ('class Handler(socketserver.BaseRequestHandler):\n'
                ' def handle(self):\n'
                "  if line.startswith(b'POST'):\n"
                '   sampling.append(meta)\n'
                '  try:upstream.sendall(first);relay(self.request,upstream)\n'
                '  finally:upstream.close()\n')
        bound=runner.bind_per_request_transport(code)
        compile(bound,'<bound-handler>','exec')
        self.assertIn('relay_one_model_response(self.request,upstream)',bound)
        self.assertIn("request_path.open('xb')",bound)
        self.assertNotIn('relay(self.request,upstream)',bound)

    def test_unmetered_or_unbound_source_cannot_be_qualified(self):
        with tempfile.TemporaryDirectory() as td:
            case=Path(td)
            receipt={'model_http_requests':['POST /v1/chat/completions'],
                     'sampling_metadata':[], 'step_finish_tokens':[{},{}]}
            invalid=runner.execution_integrity(case,receipt)
            self.assertFalse(invalid['passed'])
            self.assertIn('model_usage_steps_disagree_with_counted_posts',invalid['failures'])
            request=case/'model_request_bodies/00001.json'
            request.parent.mkdir();request.write_bytes(b'{}')
            receipt['step_finish_tokens']=[{}]
            receipt['sampling_metadata']=[{'request_body_file':request.name,
                                           'request_body_sha256':runner.sha(request)}]
            self.assertTrue(runner.execution_integrity(case,receipt)['passed'])
            request.write_bytes(b'{"changed":true}')
            self.assertFalse(runner.execution_integrity(case,receipt)['passed'])

    def test_keepalive_cannot_forward_a_second_uncounted_request(self):
        """A persistent client must reconnect through the request budget gate."""
        from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
        upstream_calls = []
        counted = []

        class Model(BaseHTTPRequestHandler):
            protocol_version = 'HTTP/1.1'
            def do_POST(self):
                upstream_calls.append(self.rfile.read(int(self.headers['Content-Length'])))
                self.send_response(200)
                self.send_header('Content-Length', '2')
                self.end_headers()
                self.wfile.write(b'{}')
                self.wfile.flush()
            def log_message(self, *args): pass

        model = ThreadingHTTPServer(('127.0.0.1', 0), Model)
        class Bridge(socketserver.BaseRequestHandler):
            def handle(self):
                first = b''
                while b'\r\n\r\n' not in first:
                    first += self.request.recv(4096)
                headers, body = first.split(b'\r\n\r\n', 1)
                length = int(next(x.split(b':',1)[1] for x in headers.split(b'\r\n')
                                  if x.lower().startswith(b'content-length:')))
                while len(body) < length:
                    body += self.request.recv(length-len(body))
                counted.append(body)
                if len(counted) > 2:
                    self.request.sendall(b'HTTP/1.1 403 Forbidden\r\nConnection: close\r\nContent-Length: 0\r\n\r\n')
                    return
                with socket.create_connection(model.server_address, timeout=2) as upstream:
                    upstream.sendall(headers+b'\r\n\r\n'+body)
                    runner.relay_one_model_response(self.request, upstream)

        bridge = socketserver.ThreadingTCPServer(('127.0.0.1',0), Bridge)
        for server in (model, bridge):
            threading.Thread(target=server.serve_forever, daemon=True).start()
        client = http.client.HTTPConnection(*bridge.server_address, timeout=2)
        try:
            responses = []
            for body in ('first','second','third'):
                client.request('POST','/v1/chat/completions',body=body)
                response = client.getresponse()
                responses.append((response.status, response.getheader('Connection'), response.read()))
            self.assertEqual([r[0] for r in responses], [200,200,403])
            self.assertEqual([r[1] for r in responses], ['close']*3)
            self.assertEqual(counted, [b'first',b'second',b'third'])
            self.assertEqual(upstream_calls, [b'first',b'second'])
        finally:
            client.close()
            for server in (bridge, model):
                server.shutdown(); server.server_close()

    def test_chunked_sse_is_forwarded_without_chunk_frames(self):
        client, bridge = socket.socketpair()
        upstream, model = socket.socketpair()
        received = []
        failures = []
        def relay():
            try:
                received.append(runner.relay_one_model_response(bridge, upstream))
            except Exception as exc:
                failures.append(exc)
            finally:
                bridge.close(); upstream.close()
        thread = threading.Thread(target=relay, daemon=True)
        thread.start()
        try:
            model.sendall(b'HTTP/1.1 200 OK\r\nContent-Type: text/event-stream\r\n'
                          b'Transfer-Encoding: chunked\r\n\r\n'
                          b'9\r\ndata: 1\n\n\r\nE\r\ndata: [DONE]\n\n\r\n0\r\n\r\n')
            response = http.client.HTTPResponse(client)
            response.begin()
            self.assertEqual(response.getheader('Connection'), 'close')
            self.assertIsNone(response.getheader('Transfer-Encoding'))
            self.assertEqual(response.read(), b'data: 1\n\ndata: [DONE]\n\n')
            thread.join(timeout=2)
            self.assertFalse(thread.is_alive())
            self.assertEqual(failures, [])
            self.assertEqual(received, [{'status':200,'body_bytes':23,'complete':True}])
        finally:
            client.close(); model.close()

    def test_actual_actor_runtime_mount_is_created_and_cannot_hide_files(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / 'fresh_attempt'
            runtime = runner.prepare_actor_runtime(root)
            self.assertTrue(runtime.is_dir())
            self.assertEqual(list(runtime.iterdir()), [])
            self.assertEqual(runner.prepare_actor_runtime(root), runtime)
            (runtime / 'future.py').write_text('not a permitted dependency')
            with self.assertRaises(ValueError): runner.prepare_actor_runtime(root)

    def test_model_profile_is_bound_and_rejects_other_endpoint(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); model = root / 'weights.gguf'; model.write_bytes(b'weights')
            profile = {'version': 1, 'host': '127.0.0.1', 'port': 18104,
                       'model_id': 'qwen3-8b-qual', 'gguf_path': str(model),
                       'gguf_sha256': hashlib.sha256(b'weights').hexdigest(),
                       'context': 32768, 'output': 8192, 'pid': 42,
                       'server_executable_sha256': 'a' * 64,
                       'thinking': 'default_template', 'ownership': 'research_django_aggregation_20261106'}
            path = root / 'profile.json'; path.write_text(json.dumps(profile), encoding='utf8')
            digest = runner.sha(path)
            self.assertEqual(runner.validate_model_profile(path, digest), profile)
            with self.assertRaises(ValueError): runner.validate_model_profile(path, '0' * 64)
            profile['port'] = 8004; path.write_text(json.dumps(profile), encoding='utf8')
            with self.assertRaises(ValueError): runner.validate_model_profile(path, runner.sha(path))

    def test_harness_rebinds_upstream_alias_and_not_bridge(self):
        code = ("upstream=socket.create_connection(('127.0.0.1',8004),timeout=30)\n"
                "'model':'gb10/qwen3.6-35b-a3b'\n'qwen3.6-35b-a3b':{'name':'Qwen3.6-35B-A3B'}\n"
                "baseURL='http://127.0.0.1:18004/v1'\n")
        out = runner.rebind_model(code, {'host': '127.0.0.1', 'port': 18104,
                                        'model_id': 'qwen3-8b-qual'})
        self.assertIn("('127.0.0.1',18104)", out)
        self.assertIn('gb10/qwen3-8b-qual', out)
        self.assertIn('http://127.0.0.1:18004/v1', out)
        self.assertNotIn('qwen3.6-35b-a3b', out)
        with self.assertRaises(ValueError): runner.rebind_model('incomplete', {'host':'127.0.0.1','port':18104,'model_id':'qwen3-8b-qual'})
        teacher=dict(host='127.0.0.1',port=8004,model_id='Qwen3.6-35B-A3B-Q4_K_M.gguf')
        upgraded=runner.rebind_model(code,teacher)
        self.assertIn('gb10/Qwen3.6-35B-A3B-Q4_K_M.gguf',upgraded)
        self.assertNotIn('Q4_K_M.gguf-Q4_K_M.gguf',upgraded)

    def test_teacher_is_source_approved_conditions_only_and_limits_are_profiled(self):
        runner.validate_backend_choice('teacher35b','source','none')
        runner.validate_backend_choice('teacher35b','source','teacher_feedback_repair')
        runner.validate_backend_choice('teacher35b','source','teacher_joint_feedback_repair')
        runner.validate_backend_choice('teacher27b','source','none')
        for task,condition in [('target','none'),('source','candidate_neutral_retry'),('source','feedback_card')]:
            with self.assertRaises(ValueError):runner.validate_backend_choice('teacher35b',task,condition)
        with self.assertRaises(ValueError):runner.validate_backend_choice('student8b','source','teacher_feedback_repair')
        with self.assertRaises(ValueError):runner.validate_backend_choice('student8b','source','teacher_joint_feedback_repair')
        with self.assertRaises(ValueError):runner.validate_backend_choice('teacher27b','target','none')
        with self.assertRaises(ValueError):runner.validate_backend_choice('teacher27b','source','teacher_feedback_repair')
        profile={'context':65536,'output':16384}
        original="cfg={'options':{'timeout':300000},'limit':{'context':32768,'output':8192}}"
        upgraded=runner.set_model_limits(original,profile,'teacher35b')
        self.assertIn("'context':65536,'output':16384",upgraded)
        self.assertIn("'timeout':900000",upgraded)
        self.assertEqual(runner.set_model_limits(original,{'context':32768,'output':8192},'student8b'),original)
        q27=runner.set_model_limits(original,{'context':32768,'output':8192},'teacher27b')
        self.assertEqual(q27,original.replace("'timeout':300000","'timeout':900000"))
        with self.assertRaises(ValueError):runner.set_model_limits(original,profile,'teacher27b')
        self.assertEqual(runner.episode_limits('teacher27b'),(96,2400,12_000_000))
        self.assertEqual(runner.episode_limits('student8b'),(48,1200,6_000_000))
        self.assertEqual(runner.episode_limits('teacher35b'),(48,1200,6_000_000))

    def test_live_server_arguments_must_match_the_frozen_profile(self):
        profile = {'gguf_path':'/research/model.gguf', 'host':'127.0.0.1', 'port':18104,
                   'model_id':'qwen3-8b-qual','context':32768,'output':8192}
        argv=['server','-m','/research/model.gguf','--host','127.0.0.1','--port','18104',
              '--alias','qwen3-8b-qual','-c','32768','-n','8192','-np','1','--no-context-shift']
        runner.verify_server_argv(argv,profile)
        with self.assertRaises(ValueError): runner.verify_server_argv(argv[:-1],profile)
        with self.assertRaises(ValueError): runner.verify_server_argv(argv+['-np','2'],profile)

    def test_restore_replaces_candidate_tests_and_conftest(self):
        with tempfile.TemporaryDirectory() as td:
            r = Path(td); clean = r/'clean'; candidate = r/'candidate'; out = r/'out'
            (clean/'tests').mkdir(parents=True); (candidate/'tests').mkdir(parents=True)
            (clean/'tests/test_a.py').write_text('trusted')
            (candidate/'tests/test_a.py').write_text('fake gold')
            (candidate/'tests/conftest.py').write_text('malicious')
            (clean/'conftest.py').write_text('trusted config')
            (candidate/'conftest.py').write_text('malicious')
            (candidate/'solution.py').write_text('candidate')
            runner.restore_candidate(candidate, clean, out)
            self.assertEqual((out/'tests/test_a.py').read_text(), 'trusted')
            self.assertFalse((out/'tests/conftest.py').exists())
            self.assertEqual((out/'conftest.py').read_text(), 'trusted config')
            self.assertEqual((out/'solution.py').read_text(), 'candidate')
            with self.assertRaises(FileExistsError): runner.restore_candidate(candidate, clean, out)

    def test_attempt_and_mount_paths_cannot_escape(self):
        with tempfile.TemporaryDirectory() as td:
            base=Path(td); (base/'attempts').mkdir()
            self.assertEqual(runner.attempt_root(base,'good_1'),base/'attempts'/'good_1')
            with self.assertRaises(ValueError): runner.attempt_root(base,'../escape')
            outside=base/'outside'; outside.mkdir()
            with self.assertRaises(ValueError): runner.private_directory(outside,base/'attempts')
            with self.assertRaises(ValueError): runner.require_socket_manifest(base/'missing.json','0'*64,base)

    def test_source_probe_adapts_only_connection_not_query_or_expected(self):
        data = ('password=pathlib.Path("/run/research_secret").read_text().strip()\n'
                'settings={"HOST":"research-django-aggregation-20261106-db", "NAME":"research_probe"}\n'
                'query=A.objects.filter(Q(pk=a.pk)|Q(ab_a__b=b.pk))\n'
                'expected_data=values==[{"status":7,"total_count":1}]\n')
        adapted = runner.adapt_source_probe(data, 'research_eval_0123456789abcdef')
        self.assertIn('query=A.objects.filter(Q(pk=a.pk)|Q(ab_a__b=b.pk))', adapted)
        self.assertIn('expected_data=values==[{"status":7,"total_count":1}]', adapted)
        self.assertIn('"HOST":"/research-pg"', adapted)
        self.assertNotIn('/run/research_secret', adapted)
        with self.assertRaises(ValueError): runner.adapt_source_probe(data, 'postgres')
        with self.assertRaises(ValueError): runner.adapt_source_probe(data.replace('"NAME":"research_probe"', ''), 'research_eval_0123456789abcdef')

    def test_repair_arms_share_frozen_candidate_and_only_feedback_differs(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); work=root/'work';work.mkdir();(work/'module.py').write_text('candidate')
            (work/'instructions.txt').write_text('old prompt');(work/'opencode.json').write_text('old config')
            case=root/'case';case.mkdir();ev=case/'post_run_evaluation_restored_tests';ev.mkdir()
            for name in ('focus','regression','issue_probe'):
                (ev/(name+'.log')).write_text('TypeError: example failure\nRan 65 tests\nFAILED (errors=42)\n')
            record={'post_run_evaluation':{'focus':{'exit':1,'nodes_requested':1},
                   'regression':{'exit':1,'nodes_requested':65},'issue_probe':{'exit':1,'nodes_requested':1}}}
            feedback=runner.repair_feedback(record,case)
            self.assertIn('errors=42',feedback)
            neutral=runner.repair_prompt('SOURCE TASK\n','candidate_neutral_retry',feedback)
            informed=runner.repair_prompt('SOURCE TASK\n','candidate_feedback_retry',feedback)
            self.assertTrue(informed.startswith(neutral));self.assertEqual(informed[len(neutral):],'\n\n'+feedback)
            self.assertIn('/root/instructions.txt is a read-only issue specification',neutral)
            self.assertIn('Writable Django project source is under /root/django/',neutral)
            self.assertIn('Evaluation paths beginning /workspace/',neutral)
            self.assertNotIn('compiler.py',neutral)
            snapshot=root/'snapshot'; manifest=root/'candidate.json'
            first=runner.freeze_repair_candidate(work,snapshot,manifest,'a'*64)
            second=runner.freeze_repair_candidate(work,snapshot,manifest,'a'*64)
            self.assertEqual(first,second)
            self.assertEqual((snapshot/'module.py').read_text(),'candidate')
            self.assertFalse((snapshot/'instructions.txt').exists())
            (snapshot/'module.py').write_text('tampered')
            with self.assertRaises(ValueError): runner.freeze_repair_candidate(work,snapshot,manifest,'a'*64)

    def test_feedback_excludes_test_lines_and_unknown_exceptions(self):
        self.assertEqual(runner.error_summary('line\nTypeError: broken\nFAILED (errors=42)\n'),
                         ['TypeError: broken', 'FAILED (errors=42)'])
        self.assertEqual(runner.error_summary('some secret hidden test content'),[])
        log=('  File "/workspace/tests/hidden.py", line 3, in test_gold\n'
             '    assert secret_gold == expected\n'
             '  File "/workspace/django/db/models/sql/compiler.py", line 573, in as_sql\n'
             '    result.append(candidate_format)\nTypeError: broken\n')
        frames=runner.application_frames(log)
        self.assertEqual(len(frames),1)
        self.assertIn('compiler.py',frames[0]);self.assertIn('result.append(candidate_format)',frames[0])
        self.assertNotIn('hidden',str(frames));self.assertNotIn('secret_gold',str(frames))

    def test_joint_feedback_does_not_confuse_probe_exit_with_semantic_success(self):
        checks={'focus':{'exit':0,'summary':['Ran 1 test','OK']},
                'regression':{'exit':0,'summary':['Ran 65 tests','OK']},
                'issue_probe':{'exit':0,'observed':{'exception':None,'expected_data':True}}}
        record={'post_run_evaluation':checks}
        self.assertIn('original issue repair AND',runner.joint_source_validation_feedback(record))
        checks['issue_probe']['observed']={'exception':{'type':'ProgrammingError'}}
        with self.assertRaises(ValueError):runner.joint_source_validation_feedback(record)
        checks['issue_probe']['observed']={'exception':None,'expected_data':False}
        with self.assertRaises(ValueError):runner.joint_source_validation_feedback(record)

    def test_source_qualification_rejects_zero_tests_skips_and_caught_probe_exception(self):
        checks={k:{'exit':0,'tests_observed':n,'skipped_observed':s}
                for k,n,s in [('focus',1,0),('regression',65,0),('broader_regression',219,1)]}
        checks['issue_probe']={'exit':0,'observed':{'exception':None,'expected_data':True}}
        self.assertTrue(runner.source_artifact_qualification(checks)['passed'])
        checks['broader_regression']['exit']=1
        self.assertEqual(runner.source_artifact_qualification(checks)['failed_checks'],['broader_regression'])
        checks['broader_regression']['exit']=0;checks['focus']['tests_observed']=0
        self.assertFalse(runner.source_artifact_qualification(checks)['passed'])
        checks['focus']['tests_observed']=1;checks['broader_regression']['skipped_observed']=219
        self.assertFalse(runner.source_artifact_qualification(checks)['passed'])
        checks['broader_regression']['skipped_observed']=1
        checks['issue_probe']['observed']={'exception':{'type':'ProgrammingError'}}
        self.assertEqual(runner.source_artifact_qualification(checks)['failed_checks'],['original_issue_semantics'])

    def test_target_arms_bind_same_freeze_without_leaking_memory_to_none(self):
        import prepare_django_aggregation_experience_20261106 as helper
        with tempfile.TemporaryDirectory() as td:
            parent=Path(td)/'private';source=parent/'attempts/source';output=source/'experience';output.mkdir(parents=True)
            root=parent/'attempts/cohort';root.mkdir()
            history=output/'source_history.md';history.write_text('frozen history')
            manifest=output/'input_profile_manifest.json'
            frozen={'source':{'source_attempt':str(source.resolve()),'completion_sha256':'c'*64},
                    'artifacts':{'source_history.md':runner.sha(history)}}
            manifest.write_text(json.dumps(frozen));digest=runner.sha(manifest)
            with mock.patch.object(runner,'PARENT',parent),mock.patch.object(helper,'validate_frozen',return_value=frozen):
                no_history=runner.validate_target_experience(root,'none',manifest,digest,None,None)
                self.assertFalse(no_history['applied_to_actor']);self.assertIsNone(no_history['artifact_sha256'])
                bound=runner.validate_target_experience(root,'source_history',manifest,digest,history,runner.sha(history))
                self.assertTrue(bound['applied_to_actor'])
                with self.assertRaises(ValueError):runner.validate_target_experience(root,'source_history',manifest,digest,history,'0'*64)
                with self.assertRaises(ValueError):runner.validate_target_experience(root,'none',manifest,digest,history,runner.sha(history))
                (root/'target__none__seed7202.started.json').write_text(json.dumps({'source_experience':{'manifest_sha256':'0'*64}}))
                with self.assertRaises(ValueError):runner.validate_target_experience(root,'source_history',manifest,digest,history,runner.sha(history))

    def test_teacher_public_feedback_rejects_changed_receipt_or_log(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);clean=root/'clean';test=clean/'tests/aggregation/tests.py';test.parent.mkdir(parents=True)
            test.write_text("class AggregateTestCase:\n    def test_aggregation_subquery_annotation(self):\n        self.assertEqual(ctx[0]['sql'].count('SELECT'), 2)\n")
            log=root/'teacher.log';log.write_text('FAIL: test_aggregation_subquery_annotation (aggregation.tests.AggregateTestCase)\n'
                'Traceback (most recent call last):\n  File "/workspace/tests/aggregation/tests.py", line 1141\n'
                "    self.assertEqual(ctx[0]['sql'].count('SELECT'), 2)\nAssertionError: 3 != 2\n"
                'Ran 219 tests in 0.1s\nFAILED (failures=1, skipped=1)\n')
            receipt=root/'receipt.json';receipt.write_text(json.dumps({'results':{'teacher':{'exit':1,'log_sha256':runner.sha(log)}}}))
            receipt_sha,log_sha=runner.sha(receipt),runner.sha(log)
            feedback,binding=runner.teacher_public_feedback(receipt,log,clean,receipt_sha,log_sha)
            self.assertIn('AssertionError: 3 != 2',feedback)
            self.assertIn('test_aggregation_subquery_annotation',feedback)
            self.assertEqual(binding['teacher_log_sha256'],log_sha)
            log.write_text('tampered')
            with self.assertRaises(ValueError):runner.teacher_public_feedback(receipt,log,clean,receipt_sha,log_sha)
            log.write_text('clean again');receipt.write_text('{}')
            with self.assertRaises(ValueError):runner.teacher_public_feedback(receipt,log,clean,receipt_sha,log_sha)


if __name__ == '__main__': unittest.main()
