"""Actor-to-world role and turn boundaries; no tau2 dependency or model access."""
import importlib.util
import json
from pathlib import Path
from enum import Enum

import pytest
from types import SimpleNamespace


PATH = Path(__file__).resolve().parents[1] / 'research/agent_frontier_portfolio_20261029/tau2_execution.py'
SPEC = importlib.util.spec_from_file_location('tau2_execution_boundary', PATH)
ADAPTER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ADAPTER)
TOOLS = [{'function': {'name': 'get_customer_by_phone'}}]
CURRENT = {'turn': 4, 'done': False}


@pytest.mark.parametrize('reward', [0, 1])
def test_interrupted_world_preserves_native_prefix_and_scores_actual_progress(tmp_path, reward):
    class Reasons(Enum):
        TIMEOUT = 'timeout'
        UNEXPECTED_ERROR = 'unexpected_error'
    class Dump:
        def __init__(self, **values): self.values = values
        def model_dump(self, mode):
            return {k: v.value if isinstance(v, Enum) else v for k,v in self.values.items()}
    messages = [{'role': 'user', 'content': 'pending request'},
                {'role': 'tool', 'requestor': 'user', 'content': 'actual private device action'}]
    world = SimpleNamespace(get_messages=lambda:messages, simulation_id='fixed-world')
    env = SimpleNamespace(get_db_hash=lambda:'account-hash', get_user_db_hash=lambda:'device-hash')
    task = SimpleNamespace(id='t', evaluation_criteria=SimpleNamespace(nl_assertions=[]))
    calls = []
    def grade(sim, original, *args):
        assert (tmp_path/'simulation.json').exists()
        assert sim.values['messages'] == messages and original is task
        calls.append('deterministic-native-grade')
        return Dump(reward=reward)
    api = dict(SimulationRun=Dump, TerminationReason=Reasons,
               evaluate_simulation=grade, EvaluationType=SimpleNamespace(ALL='all'))
    ADAPTER.persist_interrupted_world(api, world, task, env, tmp_path,
        TimeoutError('actor stopped'), start_time='start', duration=3)
    assert json.loads((tmp_path/'simulation.json').read_text())['termination_reason'] == 'timeout'
    assert json.loads((tmp_path/'native_reward.json').read_text())['reward'] == reward
    assert json.loads((tmp_path/'interrupted.json').read_text())['interrupted'] is True
    assert calls == ['deterministic-native-grade']


def test_interruption_snapshot_never_triggers_a_generation_based_judge(tmp_path):
    class Dump:
        def __init__(self, **values): self.values = values
        def model_dump(self, mode): return self.values
    task = SimpleNamespace(id='t', evaluation_criteria=SimpleNamespace(nl_assertions=['needs judge']))
    api = dict(SimulationRun=Dump, TerminationReason=SimpleNamespace(TIMEOUT='timeout'),
               evaluate_simulation=lambda *a:pytest.fail('no model-based grading on interruption'))
    world = SimpleNamespace(get_messages=lambda:[], simulation_id='world')
    env = SimpleNamespace(get_db_hash=lambda:'a',get_user_db_hash=lambda:'u')
    ADAPTER.persist_interrupted_world(api, world, task, env, tmp_path,
        TimeoutError('actor stopped'), start_time='start', duration=1)
    assert (tmp_path/'simulation.json').exists()
    assert not (tmp_path/'native_reward.json').exists()
    assert json.loads((tmp_path/'interrupted.json').read_text())['score_status'] == 'generation_based_criteria_skipped'


def action(**changes):
    cmd = dict(op='act', turn=4, name='say', arguments={'message': 'Please check your network.'})
    return dict(cmd, **changes)


@pytest.mark.parametrize('cmd', [
    action(name='toggle_airplane_mode'),  # User-only device control.
    action(op='reset'),
    action(op='score'),
    action(turn=3),
    action(turn=True),
    action(name=['get_customer_by_phone']),
    action(arguments={'message': float('nan')}),
])
def test_rejects_wrong_role_admin_stale_and_malformed_actions(cmd):
    with pytest.raises(ValueError):
        ADAPTER.validate_action(cmd, CURRENT, TOOLS)


def test_rejects_action_after_terminal_public_turn():
    with pytest.raises(ValueError):
        ADAPTER.validate_action(action(), dict(CURRENT, done=True), TOOLS)


def test_accepts_public_tool_and_customer_message_without_mutation():
    commands = [action(), action(name='get_customer_by_phone', arguments={'phone_number': '555-0100'})]
    for cmd in commands:
        before = repr(cmd)
        assert ADAPTER.validate_action(cmd, CURRENT, TOOLS) is cmd
        assert repr(cmd) == before


def test_public_projection_excludes_clock_metadata_and_private_user_tools():
    public=SimpleNamespace(role='user',content='The speed is still poor.',tool_calls=None,timestamp='irrelevant')
    assert ADAPTER.project_message(public)=={'role':'user','content':'The speed is still poor.'}
    private=SimpleNamespace(role='tool',requestor='user',content='private device state')
    with pytest.raises(ValueError):ADAPTER.project_message(private)


def test_shared_role_pacer_waits_before_the_next_request(monkeypatch):
    provider=ADAPTER.Provider.__new__(ADAPTER.Provider)
    provider.deadline=200;provider.next_send=103;provider.request_interval=3
    now=[100.0];waits=[]
    monkeypatch.setattr(ADAPTER.time,'monotonic',lambda:now[0])
    def sleep(seconds):
        waits.append(seconds);now[0]+=seconds
    monkeypatch.setattr(ADAPTER.time,'sleep',sleep)
    provider.wait_request_slot()
    provider.wait_request_slot()
    assert waits==[3,3] and provider.next_send==109


def test_pacing_cannot_send_after_the_episode_deadline(monkeypatch):
    provider=ADAPTER.Provider.__new__(ADAPTER.Provider)
    provider.deadline=102;provider.next_send=103;provider.request_interval=3
    monkeypatch.setattr(ADAPTER.time,'monotonic',lambda:100)
    monkeypatch.setattr(ADAPTER.time,'sleep',lambda _:pytest.fail('deadline must refuse without sleeping'))
    with pytest.raises(TimeoutError):provider.wait_request_slot()


def test_provider_failure_refuses_both_roles_without_another_post(monkeypatch):
    provider=ADAPTER.Provider.__new__(ADAPTER.Provider)
    provider.lock=ADAPTER.threading.Lock();provider.failed_status=429
    monkeypatch.setattr(ADAPTER.time,'monotonic',lambda:100)
    for role in ['actor','user']:
        with pytest.raises(RuntimeError,match='paused after HTTP 429'):
            provider.call({},role)


def test_exact_receipt_guard_returns_public_feedback_without_advancing_world():
    previous=dict(name='refuel_data',arguments={'line_id':'L1','gb_amount':2},receipt='Successfully added 2 GB')
    cmd=action(name='refuel_data',arguments=dict(previous['arguments']))
    before=repr((cmd,CURRENT,previous))
    result=ADAPTER.committed_operation_result(cmd,CURRENT,[previous])
    assert result['error']=='previously_committed_operation'
    assert result['turn']==CURRENT['turn'] and not result['done']
    assert result['confirmed_receipt']==previous['receipt']
    assert repr((cmd,CURRENT,previous))==before


def test_exact_receipt_guard_allows_other_bindings_and_is_disabled_by_default():
    previous=dict(name='refuel_data',arguments={'line_id':'L1','gb_amount':2},receipt='Successfully added 2 GB')
    for cmd in [action(),action(name='refuel_data',arguments={'line_id':'L2','gb_amount':2}),
                action(name='refuel_data',arguments={'line_id':'L1','gb_amount':1})]:
        assert ADAPTER.committed_operation_result(cmd,CURRENT,[previous]) is None
    assert ADAPTER.committed_operation_result(action(),CURRENT,[]) is None
