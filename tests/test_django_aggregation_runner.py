"""Boundary tests for the private Django research runner; no services/models."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'research/agent_frontier_portfolio_20261029')]
SCRIPT = ROOT / 'research/agent_frontier_portfolio_20261029/run_django_aggregation_agent_20261106.py'
spec = importlib.util.spec_from_file_location('django_research_runner_test', SCRIPT)
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


class DjangoResearchRunnerTests(unittest.TestCase):
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


if __name__ == '__main__': unittest.main()
