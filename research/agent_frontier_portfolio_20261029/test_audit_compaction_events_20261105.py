import json

from research.agent_frontier_portfolio_20261029 import audit_compaction_events_20261105 as audit


def test_continue_marker_and_permission_phrase_are_counted(tmp_path):
    raw = tmp_path / 'raw.jsonl'
    events = [
        {'type': 'text', 'part': {'synthetic': True, 'metadata': {'compaction_continue': True}}},
        {'type': 'step_start', 'part': {}},
        {'type': 'text', 'part': {'text': 'Want me to continue investigating?'}},
        {'type': 'step_finish', 'part': {'reason': 'stop'}},
    ]
    raw.write_text('\n'.join(json.dumps(e) for e in events), encoding='utf8')
    result = audit.analyze(raw)
    assert result['final_text_asks_exact_pattern'] is True
    assert result['compaction_transitions'][0]['next_text_asks_exact_pattern'] is True
    assert result['compaction_transitions'][0]['next_step_tools'] == []


def test_tool_continuation_does_not_count_as_question(tmp_path):
    raw = tmp_path / 'raw.jsonl'
    events = [
        {'type': 'text', 'part': {'synthetic': True, 'metadata': {'compaction_continue': True}}},
        {'type': 'tool_use', 'part': {'tool': 'read'}},
        {'type': 'step_finish', 'part': {'reason': 'tool-calls'}},
    ]
    raw.write_text('\n'.join(json.dumps(e) for e in events), encoding='utf8')
    result = audit.analyze(raw)
    assert result['final_text_asks_exact_pattern'] is False
    assert result['compaction_transitions'][0]['next_step_tools'] == ['read']
    assert result['compaction_transitions'][0]['next_text_asks_exact_pattern'] is False
