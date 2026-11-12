"""Actor-to-world role and turn boundaries; no tau2 dependency or model access."""
import importlib.util
from pathlib import Path

import pytest


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
