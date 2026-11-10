"""Offline controls for the paired recovery pilot; no model or environment calls."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import pytest

MODULE = Path(__file__).resolve().parents[1] / 'research/agent_frontier_portfolio_20261029/feedback_recovery.py'
spec = importlib.util.spec_from_file_location('feedback_recovery', MODULE)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def payload(output='task and shared feedback', name='read', args=None, call='r1'):
    args = args or {'filePath': '/root/instructions.txt'}
    return {'model': 'fixed', 'messages': [
        {'role': 'user', 'content': 'read instructions'},
        {'role': 'assistant', 'tool_calls': [{'id': call, 'type': 'function',
          'function': {'name': name, 'arguments': json.dumps(args)}}]},
        {'role': 'tool', 'tool_call_id': call, 'content': output},
    ], 'tools': [{'type': 'function', 'function': {'name': 'bash', 'parameters': {}}}], 'seed': 7201}


def controller(tmp_path, method='fcdr'):
    case = tmp_path / method
    work = case / 'work/astropy'
    work.mkdir(parents=True)
    (work / 'module.py').write_text('value = None\n')
    seed = {'input': {'command': 'python astropy/module.py'},
            'output': 'File "/root/astropy/module.py", line 1\nAttributeError: NoneType has no attribute unit'}
    return m.RecoveryController(method, case, seed)


@pytest.mark.parametrize('text,expected', [
    ('AttributeError: NoneType has no attribute unit', 'implementation_precondition'),
    ("E       AttributeError: 'NDDataRef' object has no attribute 'collapse'", 'api_precondition'),
    ("NameError: name 'thing' is not defined", 'api_precondition'),
    ('3 failed, 1 passed in 0.2s', 'test_or_implementation'),
    ('DeprecationWarning: old dependency', 'execution_setup'),
    ('4 passed in 0.2s', None),
])
def test_failure_categories(text, expected):
    assert m.failure_kind(text) == expected


@pytest.mark.parametrize('method', m.METHODS)
def test_shared_history_and_permissions_preserved_after_feedback_visible(tmp_path, method):
    c = controller(tmp_path, method)
    original = payload()
    unchanged = copy.deepcopy(original)
    out, index = c.augment(original)
    assert original == unchanged
    assert out['messages'][:-1] == original['messages'] and len(out['messages']) == 4
    assert out['tools'] == original['tools'] and out['seed'] == 7201
    assert json.loads((c.wire / f'request-{index:03d}-forwarded.json').read_text()) == out


def test_no_seed_feedback_leaked_before_common_read_or_into_compaction(tmp_path):
    c = controller(tmp_path)
    original = {'model': 'fixed', 'messages': [{'role': 'user', 'content': 'start'}], 'tools': [{}]}
    assert c.augment(original)[0] == original
    c.augment(payload())
    compact = {'messages': [{'role': 'user', 'content': 'summarize'}]}
    assert c.augment(compact)[0] == compact


def test_new_file_version_requires_revalidation_not_old_failure_reuse(tmp_path):
    c = controller(tmp_path)
    assert 'RETEST_AFTER_RELEVANT_EDIT' not in c.advice()
    (c.work / 'astropy/module.py').write_text('value = object()\n')
    assert 'RETEST_AFTER_RELEVANT_EDIT' in c.advice()


def test_read_output_is_not_an_executed_failure(tmp_path):
    c = controller(tmp_path)
    before = copy.deepcopy(c.pending)
    assert not c.observe('source-read', 'read', {'filePath': '/root/astropy/module.py'}, 'NameError: from a doctest')
    assert c.pending == before


def test_new_failures_deduplicated_and_same_command_pass_clears(tmp_path):
    c = controller(tmp_path)
    args = {'command': 'python astropy/module.py'}
    assert c.observe('fresh', 'bash', args, 'AssertionError: mismatch')
    assert not c.observe('fresh', 'bash', args, 'AssertionError: mismatch')
    assert c.observe('pass', 'bash', args, '4 passed in 0.1s') and not c.pending


def test_two_quiet_rounds_choose_probe_or_pivot(tmp_path):
    c = controller(tmp_path)
    c.augment(payload())
    out, _ = c.augment(payload())
    assert 'PIVOT:' in out['messages'][-1]['content']


def test_tool_history_resolves_exact_call_id_and_typed_content():
    p = payload([{'type': 'text', 'text': 'actual result'}], name='functions.bash', args={'command': 'python x.py'})
    assert list(m.tool_results(p['messages'])) == [('r1', 'bash', {'command': 'python x.py'}, 'actual result')]


def test_partial_send_is_unknown_not_zero(tmp_path):
    c = controller(tmp_path)
    class Broken:
        def sendall(self, data):
            raise OSError('partial send')
    with pytest.raises(OSError):
        c.send(Broken(), b'payload', 1)
    assert json.loads((c.wire / 'send-001.json').read_text())['status'] == 'UNCERTAIN_PARTIAL_SEND'


def test_snapshot_rejects_mutated_input(tmp_path):
    snap, work = tmp_path / 'snapshot', tmp_path / 'work'
    (snap / 'files/astropy').mkdir(parents=True)
    (work / 'astropy').mkdir(parents=True)
    (work / 'astropy/module.py').write_text('old')
    (snap / 'files/astropy/module.py').write_text('new')
    record = {'files': {'astropy/module.py': {'before': m.sha(work / 'astropy/module.py'),
                                            'after': m.sha(snap / 'files/astropy/module.py')}}}
    m.new_json(snap / 'snapshot.json', record)
    digest = m.sha(snap / 'snapshot.json')
    m.install_snapshot(snap, work, digest)
    assert (work / 'astropy/module.py').read_text() == 'new'
    with pytest.raises(ValueError, match='baseline'):
        m.install_snapshot(snap, work, digest)


def test_static_baseline_also_receives_discriminating_probe_rule(tmp_path):
    assert 'distinguishing a faulty test from a faulty implementation' in controller(tmp_path, 'simple').advice()


def test_wire_validation_rejects_missing_delivery_and_response(tmp_path):
    c = controller(tmp_path)
    m.new_json(c.case / 'recovery_start.json', {'snapshot_sha256': 'frozen'})
    class Socket:
        def sendall(self, data):
            pass
    c.augment({'messages': [], 'tools': [{}]})
    c.send(Socket(), b'body', 1)
    faults = m.wire_summary(c.case, 'frozen')['faults']
    assert 'NO_DELIVERED_POLICY' in faults and 'MISSING_UPSTREAM_RESPONSE' in faults


@pytest.mark.skipif(not (m.PRIVATE / 'astropy_qualification_20261105').is_dir(),
                    reason='requires existing GB10 Astropy dependency projection, no model calls')
def test_actual_native_harness_integration_compiles_without_execution(tmp_path):
    sys.path.insert(0, str(MODULE.parent))
    astro = m.astropy_runtime()
    snap = tmp_path / 'snapshot'
    snap.mkdir()
    (tmp_path / 'runtime').mkdir()
    m.new_json(snap / 'snapshot.json', {'files': {}})
    m.new_json(snap / 'feedback.json', {'input': {'command': 'pytest'}, 'output': '1 failed'})
    (snap / 'common_instructions.txt').write_text('shared public feedback')
    original = astro.derive(tmp_path, 'target', 'none', None, seed=m.SEED,
                            max_posts=8, max_seconds=300, context_limit=65536, output_limit=8192)
    for method in m.METHODS:
        integrated = m.instrument(original, tmp_path, snap, method, astro.core.replace_once)
        compile(integrated, '<real-native-harness>', 'exec')
