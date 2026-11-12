"""Actor-to-world role and turn boundaries; no tau2 dependency or model access."""
import importlib.util
from pathlib import Path

import pytest
from types import SimpleNamespace


PATH = Path(__file__).resolve().parents[1] / 'research/agent_frontier_portfolio_20261029/tau2_execution.py'
SPEC = importlib.util.spec_from_file_location('tau2_execution_boundary', PATH)
ADAPTER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ADAPTER)
TOOLS = [{'function': {'name': 'get_customer_by_phone'}}]
CURRENT = {'turn': 4, 'done': False}


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
