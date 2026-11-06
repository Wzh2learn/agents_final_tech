"""CPU-only boundary tests; no model, service, database or Docker invocation."""
from contextlib import nullcontext
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import threading
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
            (root / 'execution_manifest.json').write_text('frozen')
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


def subprocess_error():
    import subprocess
    return subprocess.TimeoutExpired(['owned harness'], 1320, output=b'partial', stderr=b'error')


if __name__ == '__main__':
    unittest.main()
