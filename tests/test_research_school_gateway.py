"""Transport budget and credential boundaries; no model or network access."""
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

_path = Path(__file__).resolve().parents[1] / "scripts/graph/research_school_gateway.py"
_spec = importlib.util.spec_from_file_location("school_gateway", _path)
gateway = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gateway)


def response(tokens=10):
    return json.dumps(dict(usage=dict(prompt_tokens=tokens - 2, completion_tokens=2, total_tokens=tokens))).encode()


class GatewayTest(unittest.TestCase):
    def test_declared_program_generation_profile_can_use_8192_output_tokens(self):
        backend = gateway.SchoolBackend('dummy', object(), object())
        for output in (4096, 8192):
            with self.subTest(output=output):
                profile = dict(provider='bupt_chat_v1', base_url=gateway.BASE_URL,
                               model_id=gateway.MODEL, context=262144, output=output)
                result = backend.verify(profile)
                self.assertEqual(result['output_limit'], output)
                self.assertEqual(result['context_limit'], 262144)

    def test_profile_admission_still_rejects_undeclared_caps_or_model(self):
        backend = gateway.SchoolBackend('dummy', object(), object())
        valid = dict(provider='bupt_chat_v1', base_url=gateway.BASE_URL,
                     model_id=gateway.MODEL, context=262144, output=4096)
        for change in (dict(output=8193), dict(output=8192.0), dict(context=131072),
                       dict(model_id='other'), dict(thinking=False)):
            with self.subTest(change=change):
                with self.assertRaises(ValueError):
                    backend.verify({**valid, **change})

    def test_external_backend_cannot_enter_existing_target_cohort(self):
        here = _path.parents[2] / 'research/agent_frontier_portfolio_20261029'
        sys.path.insert(0, str(here))
        import run_contextbench_source as core
        with self.assertRaisesRegex(ValueError, 'external backend is restricted'):
            core.execute_prepared('/not/created', 'unused', ({'caps': {}}, None, None, {}), None,
                identity={'target': 'example'}, success_key='target_success', mode='NATIVE27_CAPABILITY_BASELINE',
                backend=object())

    def test_usage_subsets_are_not_added(self):
        value = dict(prompt_tokens=10, completion_tokens=5, total_tokens=15,
                     prompt_tokens_details=dict(cached_tokens=9), completion_tokens_details=dict(reasoning_tokens=3))
        body = b'data: {"choices":[]}\n\ndata: ' + json.dumps(dict(usage=value)).encode() + b'\n\ndata: [DONE]\n'
        self.assertEqual(gateway.usage_from_body(body), value)
        self.assertIsNone(gateway.usage_from_body(b'{"usage":{"total_tokens":15}}'))

    def test_unknown_send_blocks_unsafe_next_request(self):
        with tempfile.TemporaryDirectory() as root:
            b = gateway.BatchBudget(root)
            try:
                b.reserve(b'{}')
                b.sending()
                b.finish(body=response(240_000), status=200)
                with self.assertRaisesRegex(RuntimeError, "hard cap"):
                    b.reserve(b'{}')
            finally:
                b.close()
        with tempfile.TemporaryDirectory() as root:
            b = gateway.BatchBudget(root)
            try:
                b.reserve(b'{}')
                b.sending()
                b.finish()
                with self.assertRaisesRegex(RuntimeError, "hard cap"):
                    b.reserve(b'{}')
            finally:
                b.close()

    def test_complete_usage_releases_reservation_and_not_sent_does_not_spend(self):
        with tempfile.TemporaryDirectory() as root:
            b = gateway.BatchBudget(root, posts=1)
            try:
                b.reserve(b'{}')
                b.finish(sent=False)
                b.reserve(b'{}')
                b.sending()
                b.finish(body=response(), status=200)
                with self.assertRaisesRegex(RuntimeError, "hard cap"):
                    b.reserve(b'{}')
                self.assertEqual([r["state"] for r in b.rows], ["not_sent", "complete"])
            finally:
                b.close()

    def test_concurrent_owner_and_unreconciled_crash_are_rejected(self):
        with tempfile.TemporaryDirectory() as root:
            b = gateway.BatchBudget(root)
            with self.assertRaises(FileExistsError):
                gateway.BatchBudget(root)
            b.reserve(b'{}')
            b.close()
            with self.assertRaisesRegex(RuntimeError, "unresolved"):
                gateway.BatchBudget(root)
            self.assertFalse((Path(root) / "gateway_owner.lock").exists())

    def test_secret_stays_out_of_ledger_and_unsupported_options_never_send(self):
        class FakeSocket:
            def sendall(self, packet):
                self.packet = packet
            def close(self):
                pass
        fake = FakeSocket()
        class Context:
            def wrap_socket(self, raw, **kwargs):
                return fake
        with tempfile.TemporaryDirectory() as root:
            b = gateway.BatchBudget(root)
            g = gateway.SchoolGateway("unit-test-credential", b)
            payload = dict(model=gateway.MODEL, max_tokens=512)
            try:
                with self.assertRaisesRegex(ValueError, "unsupported"):
                    g.open(json.dumps(dict(payload, reasoning_effort="low")).encode())
                self.assertEqual(b.rows, [])
                with patch.object(gateway.socket, "create_connection", return_value=fake), patch.object(
                        gateway.ssl, "create_default_context", return_value=Context()):
                    g.open(json.dumps(payload).encode())
                self.assertIn(b"Authorization: Bearer unit-test-credential\r\n", fake.packet)
                b.finish(body=response(), status=200)
                self.assertNotIn("unit-test-credential", b.path.read_text())
                with patch.object(gateway.socket, "create_connection", return_value=fake), patch.object(
                        gateway.ssl, "create_default_context", return_value=Context()):
                    def refuse(_):
                        raise TimeoutError('episode closed')
                    with self.assertRaisesRegex(TimeoutError, 'episode closed'):
                        g.open(json.dumps(payload).encode(), admit=refuse)
                self.assertEqual(b.rows[-1]['state'], 'not_sent')
            finally:
                b.close()


if __name__ == "__main__":
    unittest.main()
