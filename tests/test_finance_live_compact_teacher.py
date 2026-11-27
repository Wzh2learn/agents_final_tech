import json
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest


@pytest.fixture
def live(monkeypatch):
    source = Path(__file__).resolve().parents[1] / 'research' / 'finance_frontier_pilot'
    monkeypatch.syspath_prepend(str(source))
    import live_compact_teacher

    return live_compact_teacher


@pytest.mark.parametrize('enabled, expected', [(False, 'add(1, 2)'), (True, 'add(2, 2)')])
def test_standalone_rerank_changes_only_local_selection(live, monkeypatch, tmp_path, enabled, expected):
    row = {'id': 'trial', 'dataset': 'finqa', 'report': 'report', 'question': 'What is the total?',
           'pre_text': [], 'post_text': [], 'table': [['Label', '2024'], ['Sales', '2']]}
    samples = [
        {'index': i, 'status': 'executed', 'stage': 'original', 'min_token_logprob': confidence,
         'submission': live.parse_dsl(f'Final program: {program}')}
        for i, confidence, program in [(0, -0.9, 'add(1, 2)'), (1, -0.1, 'add(2, 2)')]
    ]
    local = {'id': row['id'], 'n': 2, 'decision': {'selected_index': 0, 'vote_share': 0.5,
             'vote_support': 1, 'executed_n': 2, 'selected_min_token_logprob': -0.9, 'samples': samples},
             'usage': None, 'model_wall_seconds': 1.0}
    monkeypatch.setattr(live, 'local_call', lambda *a: local)
    policy = {'schema': live.SCHEMA, 'arms': {'n2': {'pooled_cutoffs': {'0.2': {'risk_cutoff': None}}}}}
    args = SimpleNamespace(seed=17, rate=0.2, confidence_rerank=enabled)

    def unexpected_teacher(*args):
        raise AssertionError('A local rerank must not change the frozen teacher gate')

    item, answer, _ = live.timed_arm(
        args, policy, {'model': 'compact'}, row, 'compact-teacher', tmp_path,
        0, 'trial-salt', unexpected_teacher, lambda: True,
    )
    assert answer['submission']['program'] == expected
    assert item['risk'] == (1, 0.5, -0.9)
    assert not item['teacher_requested']


def cli(live, tmp_path, *switches):
    paths = ('panel', 'benchmark', 'output', 'gate', 'serving-profile', 'api-profile', 'metric-dir', 'opencode')
    digests = ('gate', 'serving-profile', 'api-profile')
    return (['live_compact_teacher.py', '--n', '4', '--rate', '0.2', '--datasets', 'finqa',
             '--max-posts', '1', '--token-cap', str(live.school.campus.REQUEST_TOKEN_CEILING),
             '--prior-charged-tokens', str(live.school.RECORDED_PRIOR_CHARGE)]
            + [arg for name in paths for arg in (f'--{name}', str(tmp_path / name))]
            + [arg for name in digests for arg in (f'--{name}-sha256', 'digest')]
            + list(switches))


@pytest.mark.parametrize('matched', [False, True])
def test_rerank_rejects_selected_only_paths_before_setup(live, monkeypatch, tmp_path, capsys, matched):
    flags = ['--confidence-rerank', '--selected-local', str(tmp_path / 'cached')]
    if matched:
        flags.extend(['--matched-risk', str(tmp_path / 'teacher-pool')])
    monkeypatch.setattr(sys, 'argv', cli(live, tmp_path, *flags))
    with pytest.raises(SystemExit) as error:
        live.main()
    assert error.value.code == 2
    assert '--confidence-rerank is only available for live timing' in capsys.readouterr().err


@pytest.mark.parametrize('enabled', [False, True])
def test_live_run_metadata_marks_only_opted_in_selection(live, monkeypatch, tmp_path, enabled):
    (tmp_path / 'opencode').touch()
    budget_root = tmp_path / 'budget'
    budget_root.mkdir()
    budget = SimpleNamespace(root=budget_root, rows=[], close=lambda: None)
    monkeypatch.setattr(live, 'PRIVATE', tmp_path)
    monkeypatch.setattr(live, 'sys', SimpleNamespace(platform='linux'))
    monkeypatch.setattr(sys, 'argv', cli(live, tmp_path, *(['--confidence-rerank'] if enabled else [])))
    monkeypatch.setenv('BUPT_API_KEY', 'fixture')
    monkeypatch.setattr(live, 'checked_json', lambda *args: {})
    monkeypatch.setattr(live, 'gate_profile', lambda *args: {})
    monkeypatch.setattr(live.school, 'read_profile', lambda *args: ({}, {'model_id': live.TEACHER}))
    monkeypatch.setattr(live, 'read_panel', lambda *args: ([], {}, {}))
    monkeypatch.setattr(live, 'official_cases', lambda *args: ([], {}))
    monkeypatch.setattr(live.school.campus, 'BatchBudget', lambda *args: budget)
    monkeypatch.setattr(live.school, 'has_gateway_capacity', lambda *args: True)
    monkeypatch.setattr(live, 'collect', lambda args, *a, **kw: None)

    live.main()
    run = json.loads((tmp_path / 'output/run.json').read_text(encoding='utf-8'))
    if enabled:
        assert run['local_selection'] == 'confidence-rerank-v1'
    else:
        assert 'local_selection' not in run
