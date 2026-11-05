import json

import pytest

from research.agent_frontier_portfolio_20261029 import build_source_status_control_20261105 as control


def history(feedback):
    payload = json.dumps({'source_feedback': feedback}, separators=(',', ':'))
    return ('Source-only task history. test\n0000|' + payload[:20] + '\n0001|' + payload[20:] + '\n').encode()


def test_source_status_is_derived_and_control_preserves_skill():
    raw = history({'agent_exit': 1, 'request_limit_reached': True, 'focus_exit': 1, 'regression_exit': 0})
    skill = b'# Previous skill\n'
    result = control.build(raw, skill, control.sha(raw), control.sha(skill))
    assert 'Source focus-test exit: 1; source regression-test exit: 0.' in result['outputs']['source_status']
    assert result['outputs']['plain_skill'].encode() == skill
    assert len(result['outputs']['source_status']) == len(result['outputs']['length_control'])
    assert result['outputs']['source_status'].endswith(skill.decode())
    assert result['outputs']['length_control'].endswith(skill.decode())


def test_invalid_input_or_missing_status_does_not_turn_into_success():
    raw = history({'focus_exit': True})
    skill = b'skill'
    with pytest.raises(ValueError, match='hash mismatch'):
        control.build(raw, skill, '0' * 64, control.sha(skill))
    with pytest.raises(ValueError, match='missing, reordered, or malformed'):
        control.parse_history('Source-only task history. test\n0001|{}')
    assert 'Source focus-test exit: UNKNOWN' in control.status_header({'focus_exit': True})
