"""CPU-only contracts: injected transport/world, no endpoint or native game."""
import hashlib
from contextlib import contextmanager
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest import mock


SCRIPT = Path(__file__).resolve().parents[1] / 'research/agent_frontier_portfolio_20261029/alfworld_direct_policy.py'
spec = importlib.util.spec_from_file_location('alfworld_direct_policy_contract', SCRIPT)
d = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = d
spec.loader.exec_module(d)


def state(count=0, *, won=False, done=False, commands=None):
    return dict(observation='Public goal: complete the household task. State ' + str(count),
                score=float(won), won=won, done=done, action_count=count,
                admissible_commands=['look'] if commands is None else commands)


def envelope(content, *, usage=True, finish='stop'):
    result = {'model': 'owned-fake-8b', 'choices': [{'message': {'content': content}, 'finish_reason': finish}]}
    if usage:
        result['usage'] = dict(prompt_tokens=3, completion_tokens=1, total_tokens=4,
                               prompt_tokens_details={'cached_tokens': 1})
    return json.dumps(result).encode()


class DirectPolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        study = d.dependencies()
        cls.core = study.recovery().actor()
        cls.validator = staticmethod(study.recovery().bridge().validate_response)

    def run_fake(self, replies, states=(), *, caps=None, reset=None, http_status=200,
                 usage=True, failure=None, world_failure=None, clock=None, finish='stop', proof_tokens=20):
        requests, calls = [], []
        replies, states = iter(replies), iter(states)
        clock = clock or SimpleNamespace(value=0.)
        def transport(body, deadline, allowance, emit):
            requests.append(json.loads(body))
            emit('sent', True)
            emit('headers', dict(status=http_status, reason='owned fake', headers=[['Content-Type', 'application/json']]))
            if failure:
                emit('body', b'{')
                raise failure
            answer = next(replies)
            raw = envelope(json.dumps(answer) if isinstance(answer, dict) else answer, usage=usage, finish=finish)
            emit('body', raw)
            if hasattr(clock, 'after_response'):
                clock.value = clock.after_response
        def step(action, timeout):
            calls.append((action, timeout))
            if world_failure:
                raise world_failure
            return next(states)
        profile = dict(model_id='owned-fake-8b', context=32768, output=8192, host='not-contacted', port=1)
        qualify = lambda payload: dict(template_input_tokens=proof_tokens, reserved_output_tokens=8192, context=32768,
                                       request_payload_sha256=hashlib.sha256(json.dumps(payload, separators=(',', ':')).encode()).hexdigest())
        with tempfile.TemporaryDirectory() as tmp, \
                mock.patch('socket.create_connection', side_effect=AssertionError('no network allowed')):
            root = Path(tmp) / 'episode'
            receipt = d.run_policy(root, state() if reset is None else reset, step, transport,
                                   self.core, profile, qualify, self.validator, caps=caps,
                                   now=lambda: clock.value)
            files = {p.name: p.read_bytes() for p in root.iterdir() if p.is_file()}
            with self.assertRaises(FileExistsError):
                d.run_policy(root, state(), step, transport, self.core, profile, qualify, self.validator)
        return receipt, requests, calls, files

    def test_native_won_only_and_no_terminal_post_or_replay(self):
        receipt, requests, calls, files = self.run_fake([{'action': 'look'}], [state(1, won=True, done=True)])
        self.assertEqual(receipt['status'], 'WON')
        self.assertTrue(receipt['won'])
        self.assertEqual((len(requests), calls[0][0], receipt['world_actions'], receipt['replayed_actions']), (1, 'look', 1, 0))
        self.assertEqual(receipt['real_model_calls'], 0)
        self.assertEqual((receipt['provider_cached_input_tokens'], receipt['provider_uncached_input_tokens']), (1, 2))
        self.assertEqual(receipt['label'], 'OWNED_FAKE_NOT_SCIENTIFIC')
        exchange = json.loads(files['00001.exchange.json'])
        self.assertEqual(exchange['request_sha256'], hashlib.sha256(files['00001.request.json']).hexdigest())
        self.assertEqual(exchange['response_sha256'], hashlib.sha256(files['00001.response.body']).hexdigest())
        receipt, requests, calls, _ = self.run_fake([], reset=state(done=True))
        self.assertEqual(receipt['status'], 'DONE_UNWON')
        self.assertFalse(receipt['won'])
        self.assertEqual((requests, calls), ([], []))

    def test_full_public_history_current_enum_and_frozen_configuration(self):
        initial = dict(state(), expert_plan='NEVER_PRIVATE_SOURCE_OR_EXPERT')
        initial['observation'] += ' Public UTF-8: 中文'
        later = dict(state(1, commands=['take object']), hidden_facts='NEVER_PRIVATE_SOURCE_OR_EXPERT')
        receipt, requests, calls, files = self.run_fake([{'action': 'look'}, {'action': 'take object'}],
                                                   [later, state(2, won=True, done=True)], reset=initial)
        self.assertEqual(receipt['status'], 'WON')
        self.assertEqual(json.loads(files['00001.template.json'])['request_payload_sha256'],
                         hashlib.sha256(files['00001.request.json']).hexdigest())
        self.assertEqual([x[0] for x in calls], ['look', 'take object'])
        for request in requests:
            self.assertEqual((request['seed'], request['temperature'], request['max_tokens'], request['stream']), (17, .2, 8192, False))
            self.assertEqual(request['chat_template_kwargs'], {'enable_thinking': False})
            self.assertEqual(request['response_format']['type'], 'json_object')
            self.assertNotIn('stream_options', request)
            self.assertNotIn('tools', request)
            self.assertNotIn('NEVER_PRIVATE', json.dumps(request))
        self.assertEqual(requests[0]['response_format']['schema']['oneOf'][0]['properties']['action']['enum'], ['look'])
        self.assertEqual(requests[1]['response_format']['schema']['oneOf'][0]['properties']['action']['enum'], ['take object'])
        self.assertEqual(requests[1]['messages'][:2], requests[0]['messages'])
        self.assertEqual(requests[1]['messages'][2], {'role': 'assistant', 'content': '{"action": "look"}'})
        self.assertIn('Actual environment response', requests[1]['messages'][3]['content'])
        self.assertIn(later['observation'], requests[1]['messages'][3]['content'])

    def test_strict_json_never_substitutes_an_illegal_model_choice(self):
        bad = ['{"action":"take object"}', '{"action":"look","stop":true}', '{"stop":false}',
               '{"stop":1}', '{"action":"look","action":"look"}', '```json\n{"action":"look"}\n```',
               '{"action":"look"} trailing', '{"action":"look","won":true}', '{"action":NaN}', 'null']
        for answer in bad:
            with self.subTest(answer=answer):
                receipt, requests, calls, _ = self.run_fake([answer])
                self.assertEqual(receipt['status'], 'MODEL_CONTRACT_ERROR')
                self.assertEqual(len(requests), 1)
                self.assertEqual(calls, [])
        self.assertEqual(d.parse_decision('{"stop":true}', []), {'stop': True})
        self.assertEqual(len(d.decision_schema([])['oneOf']), 1)

    def test_ordinary_stop_has_one_neutral_continue_and_shared_budgets(self):
        receipt, requests, calls, _ = self.run_fake([{'stop': True}, {'action': 'look'}], [state(1, won=True, done=True)])
        self.assertEqual((receipt['ordinary_continuations'], len(requests), len(calls)), (1, 2, 1))
        self.assertEqual(requests[1]['messages'][-1], {'role': 'user', 'content': d.CONTINUE})
        receipt, requests, calls, _ = self.run_fake([{'stop': True}, {'stop': True}, {'action': 'look'}])
        self.assertEqual((receipt['status'], receipt['ordinary_continuations'], len(requests), calls), ('MODEL_STOP', 1, 2, []))
        receipt, requests, _, _ = self.run_fake([{'stop': True}], caps=dict(d.CAPS, posts=1))
        self.assertEqual((receipt['ordinary_continuations'], len(requests)), (0, 1))

    def test_post_world_context_and_request_byte_caps_close_without_extra_calls(self):
        receipt, requests, calls, _ = self.run_fake([{'action': 'look'}], [state(1)], caps=dict(d.CAPS, posts=1))
        self.assertEqual((receipt['status'], len(requests), len(calls)), ('POST_LIMIT', 1, 1))
        receipt, requests, calls, _ = self.run_fake([{'action': 'look'}], [state(1)], caps=dict(d.CAPS, world_actions=1))
        self.assertEqual((receipt['status'], len(requests), len(calls)), ('WORLD_LIMIT', 1, 1))
        for options, status in ((dict(caps=dict(d.CAPS, model_payload_bytes_combined=1)), 'BYTE_LIMIT'),
                                (dict(proof_tokens=32768), 'CONTEXT_LIMIT')):
            with self.subTest(status=status):
                receipt, requests, calls, _ = self.run_fake([], **options)
                self.assertEqual((receipt['status'], requests, calls, receipt['model_posts']), (status, [], [], 0))
        clock = SimpleNamespace(value=0., after_response=1801.)
        receipt, requests, calls, _ = self.run_fake([{'action': 'look'}], clock=clock)
        self.assertEqual((receipt['status'], len(requests), calls), ('EPISODE_TIMEOUT', 1, []))

    def test_timeout_partial_raw_and_absent_usage_are_never_retried_or_zero_filled(self):
        receipt, requests, calls, files = self.run_fake([], failure=TimeoutError('owned timeout'))
        self.assertEqual((receipt['status'], receipt['model_posts'], len(requests), calls), ('TRANSPORT_TIMEOUT', 1, 1, []))
        self.assertEqual(receipt['unknown_usage_model_posts'], 1)
        self.assertIsNone(receipt['provider_usage'])
        self.assertIsNone(receipt['provider_cached_input_tokens'])
        self.assertEqual(files['00001.response.body'], b'{')
        self.assertFalse(json.loads(files['00001.exchange.json'])['complete'])
        receipt, _, _, _ = self.run_fake([{'action': 'look'}], [state(1, won=True, done=True)], usage=False)
        self.assertTrue(receipt['won'])
        self.assertEqual(receipt['unknown_usage_model_posts'], 1)
        self.assertIsNone(receipt['provider_usage'])

    def test_native_timeout_keeps_world_terminal_unknown(self):
        receipt, requests, calls, _ = self.run_fake([{'action': 'look'}], world_failure=TimeoutError('owned world timeout'))
        self.assertEqual((receipt['status'], len(requests), len(calls)), ('NATIVE_TIMEOUT', 1, 1))
        self.assertFalse(receipt['world_state_known'])
        self.assertEqual(receipt['unknown_usage_model_posts'], 0)

    def test_http_schema_rejection_and_length_finish_have_no_fallback(self):
        receipt, requests, calls, _ = self.run_fake([{'action': 'look'}], http_status=400)
        self.assertEqual((receipt['status'], len(requests), calls), ('INTERFACE_BLOCKED', 1, []))
        receipt, requests, calls, _ = self.run_fake([{'action': 'look'}], finish='length')
        self.assertEqual((receipt['status'], len(requests), calls), ('MODEL_OUTPUT_LIMIT', 1, []))

    def test_actual_native_error_is_public_feedback_without_an_invented_action(self):
        receipt, requests, calls, _ = self.run_fake([{'action': 'look'}, {'stop': True}, {'stop': True}], [{'error': 'invalid_action'}])
        self.assertEqual([x[0] for x in calls], ['look'])
        self.assertEqual(receipt['world_actions'], 0)
        self.assertEqual(len(receipt['native_errors']), 1)
        self.assertIn('invalid_action', requests[1]['messages'][-1]['content'])


class HTTPBoundaryTests(unittest.TestCase):
    def test_prepare_execute_freeze_inputs_and_hold_lock_through_native_terminal(self):
        real = d.dependencies()
        profile = dict(model_id='owned-fake-8b', context=32768, output=8192, host='not-contacted', port=1)
        phases = []
        with tempfile.TemporaryDirectory() as tmp:
            qual = Path(tmp).resolve()
            root = qual / 'context_study_v1/direct_policy_v1/heldout1_clean_01/student8b/attempt_v1'
            root.parent.mkdir(parents=True)
            terminal = state(1, won=True, done=True)
            def start_world(*args):
                phases.append('world')
                (root / 'execute_world.jsonl').write_text('OWNED_FAKE_NATIVE_LOG')
                return ((object(), qual / 'fake-socket-dir'), state(), {})
            def fake_run(output, *args, **kwargs):
                phases.append('policy')
                output.mkdir()
                (output / 'receipt.json').write_text('{"label":"OWNED_FAKE_NOT_SCIENTIFIC"}')
                return {'label': 'OWNED_FAKE_NOT_SCIENTIFIC', 'won': False}
            @contextmanager
            def owned_lock(path):
                self.assertEqual(path, qual / 'context_study_v1/model_resource.lock')
                phases.append('lock')
                try:
                    yield
                finally:
                    phases.append('unlock')
            core = SimpleNamespace(load_profile=lambda backend: profile,
                                   stop_world=lambda world: phases.append('stop'))
            pool = SimpleNamespace(private_path=lambda path: Path(path), select_game=lambda *args: ({}, {'pool': 'fixed'}),
                                   start_world=start_world)
            recovery = SimpleNamespace(actor=lambda: core, token_qualifier=lambda *args: ({'tokenizer': 'fixed'}, None),
                                       bridge=lambda: SimpleNamespace(client_step=mock.Mock(), validate_response=real.recovery().bridge().validate_response))
            study = SimpleNamespace(QUAL=qual, task_pool=lambda: pool, recovery=lambda: recovery,
                                    components=lambda: {'dependencies': 'fixed'}, final_state=lambda path: terminal)
            with mock.patch.object(d, 'dependencies', return_value=study), \
                    mock.patch.object(d, 'resource_lock', side_effect=owned_lock), \
                    mock.patch.object(d, 'run_policy', side_effect=fake_run), \
                    mock.patch('socket.create_connection', side_effect=AssertionError('no endpoint')):
                manifest = d.prepare(root, qual / 'mock-pool.json', 'a' * 64, 'heldout1_clean_01')
                digest = d.sha(root / 'manifest.json')
                result = d.execute(root, digest)
                self.assertEqual(phases, ['lock', 'world', 'policy', 'stop', 'unlock'])
                self.assertTrue(result['won'])
                self.assertEqual(result['final_world_state'], terminal)
                self.assertTrue((root / 'terminal_native.json').is_file())
                self.assertEqual(d.sha(root / 'manifest.json'), digest)
                with self.assertRaises(FileExistsError):
                    d.execute(root, digest)
                # Rehashing a changed budget cannot bypass the fixed controller contract.
                manifest['caps'] = dict(d.CAPS, posts=127)
                (root / 'manifest.json').write_text(json.dumps(manifest))
                before = list(phases)
                with self.assertRaisesRegex(ValueError, 'frozen direct-policy inputs'):
                    d.execute(root, d.sha(root / 'manifest.json'))
                self.assertEqual(phases, before)

    def test_truncated_http_body_keeps_partial_bytes_and_is_not_complete(self):
        response = SimpleNamespace(status=200, reason='OK', length=5, getheaders=lambda: [],
                                   isclosed=mock.Mock(side_effect=[False, True]), read=mock.Mock(return_value=b'ab'))
        conn = mock.Mock()
        conn.getresponse.return_value = response
        events = []
        with mock.patch.object(d.http.client, 'HTTPConnection', return_value=conn):
            with self.assertRaises(d.http.client.HTTPException):
                d.http_transport(dict(host='not-contacted', port=1))(b'{}', time.monotonic()+10, 20,
                                                                  lambda k,v: events.append((k,v)))
        self.assertEqual(events[-1], ('body', b'ab'))
        self.assertEqual(conn.request.call_count, 1)

    def test_http_body_limit_rejects_before_read_and_never_retries(self):
        response = SimpleNamespace(status=200, reason='OK', length=20, getheaders=lambda: [('Content-Length', '20')])
        conn = mock.Mock()
        conn.getresponse.return_value = response
        events = []
        with mock.patch.object(d.http.client, 'HTTPConnection', return_value=conn) as factory:
            with self.assertRaises(d.ByteLimit):
                d.http_transport(dict(host='not-contacted', port=1))(b'{}', time.monotonic()+10, 2,
                                                                  lambda k,v: events.append((k,v)))
        self.assertEqual(factory.call_count, 1)
        self.assertEqual([e[0] for e in events], ['sent', 'headers'])
        conn.close.assert_called_once()

    @unittest.skipIf(sys.platform == 'win32', 'fcntl is a Linux execution boundary')
    def test_study_resource_lock_is_nonblocking_and_released(self):
        with tempfile.TemporaryDirectory() as tmp:
            lock = Path(tmp) / 'owned.lock'
            with d.resource_lock(lock):
                with self.assertRaises(BlockingIOError):
                    with d.resource_lock(lock):
                        self.fail('second owner acquired active study lock')
            with d.resource_lock(lock):
                pass


if __name__ == '__main__':
    unittest.main()
